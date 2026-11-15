import os
import json
import torch
import numpy as np
from sklearn.metrics import f1_score, roc_auc_score, recall_score, precision_score
from sklearn.utils.class_weight import compute_class_weight

from gnn.build_graph import build_heterogeneous_graph
from gnn.baseline import run_baselines
from gnn.models.hgt_model import StudentRiskHGT, FocalLoss

PROCESSED_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "data", "processed"))
MODELS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "models"))

@torch.no_grad()
def evaluate_split(model, data, mask, threshold: float = None) -> dict:
    model.eval()
    logits = model(data.x_dict, data.edge_index_dict)
    probs = torch.softmax(logits[mask], dim=-1)[:, 1].cpu().numpy()
    y_true = data["student"].y[mask].cpu().numpy()

    if threshold is None:
        # Calibrate threshold on current split to maximize F1 while keeping Recall >= 0.80
        best_t = 0.50
        best_f1 = -1.0
        for t in np.linspace(0.30, 0.70, 41):
            p = (probs >= t).astype(int)
            rec = float(recall_score(y_true, p, pos_label=1, zero_division=0))
            f1_m = float(f1_score(y_true, p, average="macro", zero_division=0))
            score = f1_m + (0.15 if rec >= 0.80 else 0.0)
            if score > best_f1:
                best_f1 = score
                best_t = float(t)
        threshold = best_t

    preds = (probs >= threshold).astype(int)
    f1_macro = float(f1_score(y_true, preds, average="macro", zero_division=0))
    f1_risk = float(f1_score(y_true, preds, pos_label=1, zero_division=0))
    recall_risk = float(recall_score(y_true, preds, pos_label=1, zero_division=0))
    precision_risk = float(precision_score(y_true, preds, pos_label=1, zero_division=0))
    auc = float(roc_auc_score(y_true, probs))

    return {
        "f1_macro": round(f1_macro, 4),
        "f1_risk": round(f1_risk, 4),
        "recall_risk": round(recall_risk, 4),
        "precision_risk": round(precision_risk, 4),
        "auc_roc": round(auc, 4),
        "threshold": round(threshold, 2)
    }

def train_hgt_model(epochs: int = 120, lr: float = 0.003, hidden_channels: int = 64, num_heads: int = 4):
    torch.manual_seed(42)
    np.random.seed(42)
    os.makedirs(MODELS_DIR, exist_ok=True)

    # 1. Build/Load Graph & Run Baselines
    graph_path = os.path.join(PROCESSED_DIR, "graph.pt")
    data = build_heterogeneous_graph(force_regen=True)
    baseline_results = run_baselines(PROCESSED_DIR)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"\n[TRAIN] Training StudentRiskHGT on device: {device}")
    data = data.to(device)

    in_dims = {nt: data[nt].x.size(-1) for nt in data.node_types}
    model = StudentRiskHGT(
        in_dims=in_dims,
        metadata=data.metadata(),
        hidden_channels=hidden_channels,
        num_heads=num_heads,
        num_layers=2,
        dropout=0.25
    ).to(device)

    # 2. Compute class weights for FocalLoss
    y_train_np = data["student"].y[data["student"].train_mask].cpu().numpy()
    weights = compute_class_weight("balanced", classes=np.array([0, 1]), y=y_train_np)
    # Boost weight of at-risk class slightly to prioritize Recall >= 0.80
    weights[1] *= 1.15
    class_weights = torch.tensor(weights, dtype=torch.float, device=device)

    criterion = FocalLoss(weight=class_weights, alpha=0.65, gamma=2.0)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    best_score = -1.0
    best_test_metrics = None
    best_epoch = 0
    ckpt_path = os.path.join(MODELS_DIR, "best_hgt_model.pt")

    for epoch in range(1, epochs + 1):
        model.train()
        optimizer.zero_grad()
        out = model(data.x_dict, data.edge_index_dict)
        train_mask = data["student"].train_mask
        loss = criterion(out[train_mask], data["student"].y[train_mask])
        loss.backward()
        optimizer.step()
        scheduler.step()

        if epoch % 10 == 0 or epoch == epochs:
            val_metrics = evaluate_split(model, data, data["student"].val_mask)
            # Composite score favoring Recall (at-risk), F1, and AUC
            composite = 0.40 * val_metrics["recall_risk"] + 0.35 * val_metrics["f1_macro"] + 0.25 * val_metrics["auc_roc"]
            if composite > best_score:
                best_score = composite
                best_epoch = epoch
                torch.save({
                    "epoch": epoch,
                    "model_state_dict": model.state_dict(),
                    "in_dims": in_dims,
                    "hidden_channels": hidden_channels,
                    "num_heads": num_heads,
                    "val_metrics": val_metrics
                }, ckpt_path)
                best_test_metrics = evaluate_split(model, data, data["student"].test_mask, threshold=val_metrics["threshold"])

            if epoch % 20 == 0 or epoch == epochs:
                print(
                    f"Epoch {epoch:03d}/{epochs:03d} | Loss: {loss.item():.4f} | "
                    f"Val F1: {val_metrics['f1_macro']:.4f} | Val Recall(Risk): {val_metrics['recall_risk']:.4f} | "
                    f"Val AUC: {val_metrics['auc_roc']:.4f}"
                )

    print(f"\n[OK] Best HGT checkpoint saved at epoch {best_epoch} -> {ckpt_path}")
    print("\n=== FINAL SPRINT 2 BENCHMARK SUMMARY (TEST SET) ===")
    all_benchmarks = dict(baseline_results)
    all_benchmarks["HGT (HeteroGNN)"] = best_test_metrics

    print(f"{'Model':<22} | {'F1 (Macro)':<10} | {'F1 (Risk)':<10} | {'Recall (Risk)':<13} | {'AUC-ROC':<10}")
    print("-" * 78)
    for name, m in all_benchmarks.items():
        print(f"{name:<22} | {m['f1_macro']:<10.4f} | {m['f1_risk']:<10.4f} | {m['recall_risk']:<13.4f} | {m['auc_roc']:<10.4f}")

    summary_path = os.path.join(PROCESSED_DIR, "benchmark_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(all_benchmarks, f, indent=2, ensure_ascii=False)
    print(f"[OK] Saved full benchmark comparison to: {summary_path}")
    return all_benchmarks

if __name__ == "__main__":
    train_hgt_model()
