"""
Tabular baselines for student risk prediction.

Improvements adopted from the OULAD reference pipeline (ElizabethSeidle/OULAD `modeling.py`):
  * Hyperparameter tuning with GridSearchCV (5-fold CV, scoring = ROC-AUC).
  * Global feature importance report (RF impurity importance) - plus model-agnostic
    permutation importance on the VALIDATION split (more reliable than impurity importance).
Fixes vs. the reference implementation:
  * AUC is computed on predicted probabilities (the reference used hard labels).
  * Grid search runs on the TRAIN split only (reference tuned on all data -> test leakage).
  * Best params are passed by name (reference read them by dict position, which is fragile).
  * Decision threshold is calibrated on the validation split, same protocol as the HGT model.
"""
import os
import json
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.inspection import permutation_importance
from sklearn.metrics import f1_score, roc_auc_score, recall_score, precision_score
from sklearn.model_selection import GridSearchCV, StratifiedKFold

PROCESSED_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "data", "processed"))

FEATURE_COLS = [
    "studied_credits_norm",
    "num_of_prev_attempts",
    "attendance_rate",
    "avg_score_norm",
    "submission_rate",
    "late_submission_rate",
    "total_clicks_norm",
    "active_days_norm"
]

FEATURE_LABELS_VI = {
    "studied_credits_norm": "Khối lượng tín chỉ đăng ký",
    "num_of_prev_attempts": "Số lần học lại trước đó",
    "attendance_rate": "Tỷ lệ điểm danh chuyên cần",
    "avg_score_norm": "Điểm trung bình bài kiểm tra",
    "submission_rate": "Tỷ lệ nộp bài tập",
    "late_submission_rate": "Tỷ lệ nộp bài trễ hạn",
    "total_clicks_norm": "Tổng lượt tương tác VLE (clicks)",
    "active_days_norm": "Số ngày hoạt động trên VLE",
}

PARAM_GRIDS = {
    "Logistic Regression": {"C": [0.1, 1.0, 10.0]},
    "Random Forest": {
        "n_estimators": [200, 400],
        "max_depth": [3, 5, 7],
        "min_samples_split": [2, 6, 10],
        "max_features": ["sqrt", "log2"],
    },
    "Gradient Boosting": {
        "n_estimators": [80, 150],
        "max_depth": [2, 3],
        "learning_rate": [0.05, 0.1],
    },
}


def _base_estimators(random_state: int = 42) -> dict:
    return {
        "Logistic Regression": LogisticRegression(class_weight="balanced", random_state=random_state, max_iter=1000),
        "Random Forest": RandomForestClassifier(class_weight="balanced", random_state=random_state, n_jobs=-1),
        "Gradient Boosting": GradientBoostingClassifier(random_state=random_state),
    }


def calibrate_threshold(y_true: np.ndarray, probs: np.ndarray, low: float = 0.30, high: float = 0.70) -> float:
    """Pick the threshold maximizing macro-F1 on the given (validation) split."""
    best_t, best_f1 = 0.50, -1.0
    for t in np.linspace(low, high, 41):
        f1_m = f1_score(y_true, (probs >= t).astype(int), average="macro", zero_division=0)
        if f1_m > best_f1 + 1e-9:
            best_f1, best_t = f1_m, float(t)
    return round(best_t, 2)


def compute_metrics(y_true: np.ndarray, probs: np.ndarray, threshold: float) -> dict:
    pred = (probs >= threshold).astype(int)
    return {
        "f1_macro": round(float(f1_score(y_true, pred, average="macro", zero_division=0)), 4),
        "f1_risk": round(float(f1_score(y_true, pred, pos_label=1, zero_division=0)), 4),
        "recall_risk": round(float(recall_score(y_true, pred, pos_label=1, zero_division=0)), 4),
        "precision_risk": round(float(precision_score(y_true, pred, pos_label=1, zero_division=0)), 4),
        "auc_roc": round(float(roc_auc_score(y_true, probs)), 4),
        "threshold": threshold,
    }


def _available_features(df: pd.DataFrame) -> list:
    return [c for c in FEATURE_COLS if c in df.columns]


def run_baselines(processed_dir: str = PROCESSED_DIR, tune: bool = True, random_state: int = 42) -> dict:
    csv_path = os.path.join(processed_dir, "student_features.csv")
    if not os.path.exists(csv_path):
        from gnn.build_graph import build_heterogeneous_graph
        build_heterogeneous_graph()

    df = pd.read_csv(csv_path)
    feats = _available_features(df)
    train_df = df[df["split"] == "train"]
    val_df = df[df["split"] == "val"]
    test_df = df[df["split"] == "test"]

    X_train, y_train = train_df[feats].values, train_df["is_at_risk"].values
    X_val, y_val = val_df[feats].values, val_df["is_at_risk"].values
    X_test, y_test = test_df[feats].values, test_df["is_at_risk"].values

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=random_state)
    results, fitted, best_params = {}, {}, {}

    print("=== BASELINE BENCHMARK (GridSearchCV 5-fold on TRAIN, threshold calibrated on VAL, TEST metrics) ===")
    print(f"{'Model':<22} | {'F1 (Macro)':<10} | {'F1 (Risk)':<10} | {'Recall (Risk)':<13} | {'AUC-ROC':<10} | {'CV AUC':<7}")
    print("-" * 90)

    for name, est in _base_estimators(random_state).items():
        cv_auc = None
        if tune:
            gs = GridSearchCV(est, PARAM_GRIDS[name], cv=cv, scoring="roc_auc", n_jobs=-1, refit=True)
            gs.fit(X_train, y_train)
            clf = gs.best_estimator_
            best_params[name] = {k: (v if isinstance(v, (int, float, str)) else str(v)) for k, v in gs.best_params_.items()}
            cv_auc = round(float(gs.best_score_), 4)
        else:
            clf = est.fit(X_train, y_train)
        fitted[name] = clf

        threshold = calibrate_threshold(y_val, clf.predict_proba(X_val)[:, 1])
        metrics = compute_metrics(y_test, clf.predict_proba(X_test)[:, 1], threshold)
        if cv_auc is not None:
            metrics["cv_auc"] = cv_auc
        results[name] = metrics
        print(f"{name:<22} | {metrics['f1_macro']:<10.4f} | {metrics['f1_risk']:<10.4f} | "
              f"{metrics['recall_risk']:<13.4f} | {metrics['auc_roc']:<10.4f} | {cv_auc if cv_auc is not None else '-':<7}")

    # Feature importance (RF impurity + permutation importance on VAL split)
    rf = fitted["Random Forest"]
    perm = permutation_importance(rf, X_val, y_val, scoring="roc_auc", n_repeats=20, random_state=random_state, n_jobs=-1)
    importance = []
    for i, col in enumerate(feats):
        importance.append({
            "feature_key": col,
            "feature_name": FEATURE_LABELS_VI.get(col, col),
            "rf_impurity_importance": round(float(rf.feature_importances_[i]), 4),
            "permutation_importance": round(float(perm.importances_mean[i]), 4),
            "permutation_std": round(float(perm.importances_std[i]), 4),
        })
    importance.sort(key=lambda x: x["permutation_importance"], reverse=True)

    with open(os.path.join(processed_dir, "baseline_metrics.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    with open(os.path.join(processed_dir, "baseline_best_params.json"), "w", encoding="utf-8") as f:
        json.dump(best_params, f, indent=2, ensure_ascii=False)
    with open(os.path.join(processed_dir, "feature_importance.json"), "w", encoding="utf-8") as f:
        json.dump({
            "model": "Random Forest (GridSearchCV-tuned)",
            "method": "Permutation importance (ROC-AUC drop) on validation split; RF impurity importance for reference",
            "features": importance,
        }, f, indent=2, ensure_ascii=False)

    print("\n=== GLOBAL FEATURE IMPORTANCE (Random Forest, permutation on VAL) ===")
    for it in importance:
        print(f"  {it['feature_key']:<22} perm={it['permutation_importance']:+.4f}  impurity={it['rf_impurity_importance']:.4f}")
    print(f"[OK] Saved baseline metrics / best params / feature importance to: {processed_dir}")
    return results


if __name__ == "__main__":
    run_baselines()
