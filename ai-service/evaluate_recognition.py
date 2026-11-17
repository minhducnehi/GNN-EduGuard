"""Evaluate saved models on the held-out synthetic test split; never retrains."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import brier_score_loss, precision_score, recall_score, roc_auc_score

from gnn.models.hgt_model import StudentRiskHGT
from gnn.temporal_model import TemporalHGTModel

ROOT = Path(__file__).resolve().parent / "gnn"


def metrics(y, p, threshold):
    pred = p >= threshold
    result = {
        "n": len(y), "positive_count": int(y.sum()),
        "precision": float(precision_score(y, pred, zero_division=0)),
        "recall": float(recall_score(y, pred, zero_division=0)),
        "brier": float(brier_score_loss(y, p)),
        "mean_predicted_risk": float(np.mean(p)),
        "observed_risk": float(np.mean(y)),
    }
    result["roc_auc"] = float(roc_auc_score(y, p)) if len(np.unique(y)) == 2 else None
    return result


def bootstrap_recall(y, p, threshold, repetitions=1000, seed=42):
    rng = np.random.default_rng(seed)
    estimates = []
    for _ in range(repetitions):
        sampled = rng.integers(0, len(y), len(y))
        if y[sampled].sum():
            estimates.append(recall_score(y[sampled], p[sampled] >= threshold, zero_division=0))
    return [float(v) for v in np.quantile(estimates, [0.025, 0.975])]


def main():
    processed = ROOT / "data" / "processed"
    graph = torch.load(processed / "graph.pt", map_location="cpu", weights_only=False)
    sequence = torch.load(processed / "weekly_sequences.pt", map_location="cpu", weights_only=False)
    frame = pd.read_csv(processed / "student_features.csv")
    outcomes = pd.read_csv(ROOT / "data" / "raw" / "studentInfo.csv")[["id_student", "final_result"]]
    frame = frame.merge(outcomes, on="id_student", how="left", validate="one_to_one", sort=False)
    if frame["final_result"].isna().any():
        raise ValueError("Missing final_result for evaluated students")
    mask = graph["student"].test_mask.numpy()
    assert len(frame) == len(mask)
    assert np.array_equal(frame["split"].eq("test").to_numpy(), mask)
    y = graph["student"].y.numpy()[mask]
    assert np.array_equal(frame.loc[mask, "is_at_risk"].to_numpy(), y)
    report = {"data_source": "repository synthetic OULAD-schema sample", "test_n": int(mask.sum()), "models": {}}

    static_ckpt = torch.load(ROOT / "models" / "best_hgt_model.pt", map_location="cpu", weights_only=False)
    static = StudentRiskHGT(static_ckpt["in_dims"], graph.metadata(), static_ckpt["hidden_channels"], static_ckpt["num_heads"], dropout=0.0)
    static.load_state_dict(static_ckpt["model_state_dict"])
    static.eval()
    temporal_ckpt = torch.load(ROOT / "models" / "best_temporal_hgt.pt", map_location="cpu", weights_only=False)
    temporal = TemporalHGTModel(temporal_ckpt["in_dims"], graph.metadata(), temporal_ckpt["seq_in_dim"], temporal_ckpt["hidden_channels"], temporal_ckpt["num_heads"], dropout=0.0)
    temporal.load_state_dict(temporal_ckpt["model_state_dict"])
    temporal.eval()

    with torch.no_grad():
        predictions = {"static": torch.softmax(static(graph.x_dict, graph.edge_index_dict), -1)[:, 1].numpy()[mask]}
        for week in (2, 4, 8, 12, 16):
            predictions[f"week_{week}"] = torch.softmax(temporal(graph.x_dict, graph.edge_index_dict, sequence, cutoff_week=week, graph_data=graph), -1)[:, 1].numpy()[mask]

    for name, p in predictions.items():
        threshold = float(static_ckpt["val_metrics"]["threshold"]) if name == "static" else 0.48
        result = metrics(y, p, threshold)
        result["threshold"] = threshold
        result["recall_95pct_bootstrap_ci"] = bootstrap_recall(y, p, threshold)
        result["subgroups"] = {}
        for column in ("gender_code", "code_module"):
            result["subgroups"][column] = {}
            for value in sorted(frame.loc[mask, column].dropna().unique()):
                group = frame.loc[mask, column].to_numpy() == value
                result["subgroups"][column][str(value)] = metrics(y[group], p[group], threshold)
        result["outcomes"] = {}
        for outcome in sorted(frame.loc[mask, "final_result"].unique()):
            group = frame.loc[mask, "final_result"].to_numpy() == outcome
            result["outcomes"][str(outcome)] = {
                "n": int(group.sum()),
                "flagged_count": int((p[group] >= threshold).sum()),
                "flagged_rate": float(np.mean(p[group] >= threshold)),
            }
        report["models"][name] = result

    output = Path(__file__).resolve().parent / "recognition_evaluation.json"
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
