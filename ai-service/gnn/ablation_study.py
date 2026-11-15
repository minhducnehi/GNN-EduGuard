import os
import json
import torch
import numpy as np
from sklearn.metrics import f1_score, roc_auc_score, recall_score, precision_score
from gnn.models.hgt_model import StudentRiskHGT
from gnn.temporal_model import TemporalHGTModel

PROCESSED_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "data", "processed"))
MODELS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "models"))


@torch.no_grad()
def _eval_probs(probs: np.ndarray, y_true: np.ndarray, threshold: float = 0.50) -> dict:
    preds = (probs >= threshold).astype(int)
    return {
        "f1_macro": round(float(f1_score(y_true, preds, average="macro", zero_division=0)), 4),
        "f1_risk": round(float(f1_score(y_true, preds, pos_label=1, zero_division=0)), 4),
        "recall_risk": round(float(recall_score(y_true, preds, pos_label=1, zero_division=0)), 4),
        "precision_risk": round(float(precision_score(y_true, preds, pos_label=1, zero_division=0)), 4),
        "auc_roc": round(float(roc_auc_score(y_true, probs)), 4)
    }


@torch.no_grad()
def run_ablation_study() -> dict:
    graph_path = os.path.join(PROCESSED_DIR, "graph.pt")
    hgt_ckpt_path = os.path.join(MODELS_DIR, "best_hgt_model.pt")
    temp_ckpt_path = os.path.join(MODELS_DIR, "best_temporal_hgt.pt")
    seq_path = os.path.join(PROCESSED_DIR, "weekly_sequences.pt")

    data = torch.load(graph_path, weights_only=False)
    x_seq = torch.load(seq_path, weights_only=False)
    test_mask = data["student"].test_mask
    y_test = data["student"].y[test_mask].numpy()

    # Load Static HGT
    hgt_ckpt = torch.load(hgt_ckpt_path, weights_only=False)
    hgt_model = StudentRiskHGT(
        in_dims=hgt_ckpt["in_dims"],
        metadata=data.metadata(),
        hidden_channels=hgt_ckpt["hidden_channels"],
        num_heads=hgt_ckpt["num_heads"],
        num_layers=2,
        dropout=0.0
    )
    hgt_model.load_state_dict(hgt_ckpt["model_state_dict"])
    hgt_model.eval()

    # Load Temporal HGT + LSTM
    t_ckpt = torch.load(temp_ckpt_path, weights_only=False)
    temp_model = TemporalHGTModel(
        in_dims=t_ckpt["in_dims"],
        metadata=data.metadata(),
        seq_in_dim=t_ckpt.get("seq_in_dim", 5),
        hidden_channels=t_ckpt["hidden_channels"],
        num_heads=t_ckpt["num_heads"],
        dropout=0.0
    )
    temp_model.load_state_dict(t_ckpt["model_state_dict"])
    temp_model.eval()

    results = {}

    # 1. Full Model (HGT + LSTM + Attendance + All Heterogeneous Edges)
    logits_full = temp_model(data.x_dict, data.edge_index_dict, x_seq, cutoff_week=16, graph_data=data)
    probs_full = torch.softmax(logits_full[test_mask], dim=-1)[:, 1].numpy()
    val_mask = data["student"].val_mask
    y_val = data["student"].y[val_mask].numpy()
    val_probs = torch.softmax(logits_full[val_mask], dim=-1)[:, 1].numpy()
    best_th = 0.55
    best_vf1 = -1.0
    for th in np.linspace(0.40, 0.75, 36):
        vp = (val_probs >= th).astype(int)
        vf1 = float(f1_score(y_val, vp, average="macro", zero_division=0))
        if vf1 > best_vf1:
            best_vf1 = vf1
            best_th = float(th)
    results["1. Full Model (HGT + LSTM + Attendance)"] = _eval_probs(probs_full, y_test, threshold=best_th)

    # 2. w/o Temporal Sequence (Static HGT Only)
    logits_static = hgt_model(data.x_dict, data.edge_index_dict)
    probs_static = torch.softmax(logits_static[test_mask], dim=-1)[:, 1].numpy()
    results["2. w/o Temporal Dynamics (Static HGT)"] = _eval_probs(probs_static, y_test, threshold=0.57)

    # 3. w/o Class Attendance Features (Mask out attendance_rate column 2)
    x_no_att = {k: v.clone() for k, v in data.x_dict.items()}
    x_no_att["student"][:, 2] = 0.80  # mask attendance variation with neutral 80%
    logits_no_att = hgt_model(x_no_att, data.edge_index_dict)
    probs_no_att = torch.softmax(logits_no_att[test_mask], dim=-1)[:, 1].numpy()
    results["3. w/o Class Attendance Features"] = _eval_probs(probs_no_att, y_test, threshold=0.57)

    # 4. w/o Concept Nodes (Mask out concept features & concept-linked edges)
    x_no_concept = {k: v.clone() for k, v in data.x_dict.items()}
    x_no_concept["concept"] = torch.zeros_like(x_no_concept["concept"])
    edges_no_concept = {k: v.clone() for k, v in data.edge_index_dict.items()}
    for rel_key in list(edges_no_concept.keys()):
        if "concept" in rel_key:
            edges_no_concept[rel_key] = torch.empty((2, 0), dtype=torch.long)
    logits_no_concept = hgt_model(x_no_concept, edges_no_concept)
    probs_no_concept = torch.softmax(logits_no_concept[test_mask], dim=-1)[:, 1].numpy()
    results["4. w/o Concept Nodes & Links"] = _eval_probs(probs_no_concept, y_test, threshold=0.57)

    # 5. w/o Assignment Submission Edges (Remove submitted/passed/failed edges & score feature)
    x_no_sub = {k: v.clone() for k, v in data.x_dict.items()}
    x_no_sub["student"][:, 3:6] = 0.0  # mask avg_score, submission_rate, late_submission_rate
    edges_no_sub = {k: v.clone() for k, v in data.edge_index_dict.items()}
    for rel_key in list(edges_no_sub.keys()):
        if "assignment" in rel_key:
            edges_no_sub[rel_key] = torch.empty((2, 0), dtype=torch.long)
    logits_no_sub = hgt_model(x_no_sub, edges_no_sub)
    probs_no_sub = torch.softmax(logits_no_sub[test_mask], dim=-1)[:, 1].numpy()
    results["5. w/o Assignment Submission Edges"] = _eval_probs(probs_no_sub, y_test, threshold=0.50)

    # 6. w/o VLE Lesson Edges (Remove watched edges & click feature)
    x_no_vle = {k: v.clone() for k, v in data.x_dict.items()}
    x_no_vle["student"][:, 6] = 0.0  # mask total_clicks_norm
    if x_no_vle["student"].size(1) > 7:
        x_no_vle["student"][:, 7] = 0.0  # mask active_days_norm
    edges_no_vle = {k: v.clone() for k, v in data.edge_index_dict.items()}
    for rel_key in list(edges_no_vle.keys()):
        if "lesson" in rel_key:
            edges_no_vle[rel_key] = torch.empty((2, 0), dtype=torch.long)
    logits_no_vle = hgt_model(x_no_vle, edges_no_vle)
    probs_no_vle = torch.softmax(logits_no_vle[test_mask], dim=-1)[:, 1].numpy()
    results["6. w/o VLE Lesson Interaction Edges"] = _eval_probs(probs_no_vle, y_test, threshold=0.57)

    print("\n=== ABLATION STUDY RESULTS (TEST SET) ===")
    print(f"{'Configuration':<38} | {'F1 (Macro)':<10} | {'Recall (Risk)':<13} | {'AUC-ROC':<10}")
    print("-" * 78)
    for k, m in results.items():
        print(f"{k:<38} | {m['f1_macro']:<10.4f} | {m['recall_risk']:<13.4f} | {m['auc_roc']:<10.4f}")

    out_path = os.path.join(PROCESSED_DIR, "ablation_metrics.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"[OK] Saved ablation study results to: {out_path}")
    return results


if __name__ == "__main__":
    run_ablation_study()
