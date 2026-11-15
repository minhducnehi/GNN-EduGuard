import os
import sys
import json
import torch
import torch.nn as nn
import torch.nn.functional as F
import pandas as pd
import numpy as np
from sklearn.metrics import f1_score, roc_auc_score, recall_score, precision_score
from sklearn.utils.class_weight import compute_class_weight
from torch_geometric.nn import HGTConv
from gnn.models.hgt_model import FocalLoss
from gnn.data_quality import clean_table

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

RAW_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "data", "raw"))
PROCESSED_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "data", "processed"))
MODELS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "models"))
SEQ_DIM = 6


def _load_active_days_cap(processed_dir: str) -> float:
    path = os.path.join(processed_dir, "feature_scaling.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return max(1.0, float(json.load(f).get("active_days_cap", 1.0)))
    return 16.0


def build_weekly_sequences(raw_dir: str = RAW_DIR, processed_dir: str = PROCESSED_DIR, max_weeks: int = 16) -> torch.Tensor:
    """
    Constructs a tensor of shape [N_students, max_weeks, 6] representing weekly student trajectories:
      dim 0: weekly_clicks_norm (VLE clicks in week t)
      dim 1: cumulative_clicks_norm (cumulative VLE clicks up to week t)
      dim 2: weekly_score_norm (assessment score in week t, or last known score)
      dim 3: cumulative_late_ratio (fraction of late/missing submissions up to week t)
      dim 4: cumulative_attendance_rate (class attendance rate up to week t)
      dim 5: cumulative_active_days_norm (distinct VLE active days up to week t / train P98 cap)
    """
    active_days_cap = _load_active_days_cap(processed_dir)
    students_df = clean_table("studentInfo", pd.read_csv(os.path.join(raw_dir, "studentInfo.csv"))).drop_duplicates(subset=["id_student"])
    assessments_df = clean_table("assessments", pd.read_csv(os.path.join(raw_dir, "assessments.csv")))
    student_assessments_df = clean_table("studentAssessment", pd.read_csv(os.path.join(raw_dir, "studentAssessment.csv")))
    student_vle_df = clean_table("studentVle", pd.read_csv(os.path.join(raw_dir, "studentVle.csv")))
    att_path = os.path.join(raw_dir, "studentAttendance.csv")
    student_att_df = clean_table("studentAttendance", pd.read_csv(att_path)) if os.path.exists(att_path) else pd.DataFrame()
    if "score" in student_assessments_df.columns:
        student_assessments_df["score"] = student_assessments_df["score"].fillna(0.0)

    sa_merged = student_assessments_df.merge(
        assessments_df[["id_assessment", "date", "weight"]],
        on="id_assessment",
        how="left"
    )
    sa_merged["week"] = np.clip((sa_merged["date"] // 7).astype(int), 1, max_weeks)
    sa_merged["is_late"] = (sa_merged["date_submitted"] > sa_merged["date"]).astype(float)

    student_vle_df["week"] = np.clip((student_vle_df["date"] // 7).astype(int) + 1, 1, max_weeks)

    student_ids = sorted(students_df["id_student"].unique())
    num_students = len(student_ids)
    seq_tensor = np.zeros((num_students, max_weeks, SEQ_DIM), dtype=np.float32)

    for idx, s_id in enumerate(student_ids):
        s_vle = student_vle_df[student_vle_df["id_student"] == s_id]
        s_sa = sa_merged[sa_merged["id_student"] == s_id]
        s_att = student_att_df[student_att_df["id_student"] == s_id] if len(student_att_df) > 0 else pd.DataFrame()

        cum_clicks = 0.0
        last_score = 0.55
        cum_subs = 0
        cum_late = 0
        cum_attended = 0
        cum_sessions = 0
        seen_days = set()

        for w in range(1, max_weeks + 1):
            w_vle = s_vle[s_vle["week"] == w] if len(s_vle) > 0 else s_vle
            w_clicks = float(w_vle["sum_click"].sum()) if len(w_vle) > 0 else 0.0
            cum_clicks += w_clicks
            if len(w_vle) > 0:
                seen_days.update(w_vle["date"].tolist())

            w_sa = s_sa[s_sa["week"] == w]
            if len(w_sa) > 0:
                last_score = float(w_sa["score"].mean()) / 100.0
                cum_subs += len(w_sa)
                cum_late += int(w_sa["is_late"].sum())

            if len(s_att) > 0:
                w_att = s_att[s_att["week"] == w]
                if len(w_att) > 0:
                    cum_sessions += len(w_att)
                    cum_attended += int(w_att["attended"].sum())
            else:
                if w <= 15:
                    cum_sessions += 1
                    cum_attended += 1

            cum_att_rate = cum_attended / float(max(1, cum_sessions))

            expected_subs = w // 4
            missing_subs = max(0, expected_subs - cum_subs)
            late_or_missing_ratio = (cum_late + missing_subs) / max(1, expected_subs) if expected_subs > 0 else 0.0

            seq_tensor[idx, w - 1, 0] = min(1.0, w_clicks / 25.0)
            seq_tensor[idx, w - 1, 1] = min(1.0, cum_clicks / (w * 8.0))
            seq_tensor[idx, w - 1, 2] = last_score
            seq_tensor[idx, w - 1, 3] = min(1.0, late_or_missing_ratio)
            seq_tensor[idx, w - 1, 4] = cum_att_rate
            seq_tensor[idx, w - 1, 5] = min(1.0, len(seen_days) / active_days_cap)

    out_t = torch.tensor(seq_tensor, dtype=torch.float)
    torch.save(out_t, os.path.join(processed_dir, "weekly_sequences.pt"))
    return out_t


def filter_edges_by_cutoff_week(graph_data, edge_index_dict: dict, cutoff_week: int) -> dict:
    if cutoff_week >= 16 or graph_data is None:
        return edge_index_dict

    filtered = {}
    for edge_type, ei in edge_index_dict.items():
        store = graph_data[edge_type] if edge_type in graph_data.edge_types else None
        if store is not None and hasattr(store, "edge_week") and store.edge_week is not None:
            mask = (store.edge_week <= cutoff_week)
            filtered[edge_type] = ei[:, mask]
        else:
            filtered[edge_type] = ei
    return filtered


class TemporalHGTModel(nn.Module):
    """
    Hybrid LSTM + Heterogeneous Graph Transformer (Temporal-HGT) for Early Warning Prediction.
    Incorporates weekly class attendance, VLE clicks, and assignment submissions up to cutoff_week.
    """
    def __init__(
        self,
        in_dims: dict,
        metadata: tuple,
        seq_in_dim: int = SEQ_DIM,
        hidden_channels: int = 64,
        num_heads: int = 4,
        dropout: float = 0.25
    ):
        super().__init__()
        self.hidden_channels = hidden_channels
        self.dropout = dropout
        node_types = metadata[0]

        self.lstm = nn.LSTM(
            input_size=seq_in_dim,
            hidden_size=hidden_channels,
            num_layers=1,
            batch_first=True
        )
        self.temporal_norm = nn.LayerNorm(hidden_channels)

        self.input_proj = nn.ModuleDict({
            nt: nn.Sequential(
                nn.Linear(in_dims[nt], hidden_channels),
                nn.LayerNorm(hidden_channels),
                nn.GELU()
            )
            for nt in node_types
        })

        self.conv1 = HGTConv(hidden_channels, hidden_channels, metadata, heads=num_heads)
        self.conv2 = HGTConv(hidden_channels, hidden_channels, metadata, heads=num_heads)
        self.norm1 = nn.ModuleDict({nt: nn.LayerNorm(hidden_channels) for nt in node_types})
        self.norm2 = nn.ModuleDict({nt: nn.LayerNorm(hidden_channels) for nt in node_types})

        self.classifier = nn.Sequential(
            nn.Linear(hidden_channels * 2, hidden_channels),
            nn.LayerNorm(hidden_channels),
            nn.GELU(),
            nn.Dropout(p=dropout),
            nn.Linear(hidden_channels, 2)
        )

    def _build_causal_student_features(self, x_student: torch.Tensor, seq_slice: torch.Tensor, cutoff_week: int) -> torch.Tensor:
        """
        Student feature columns (8 total):
          0: studied_credits_norm (start of semester)
          1: num_of_prev_attempts (start of semester)
          2: attendance_rate (causal up to cutoff_week)
          3: avg_score_norm (causal up to cutoff_week)
          4: submission_rate (causal up to cutoff_week)
          5: late_submission_rate (causal up to cutoff_week)
          6: total_clicks_norm (causal up to cutoff_week)
          7: active_days_norm (causal up to cutoff_week, if present in graph & sequence)
        """
        if cutoff_week >= 16:
            return x_student

        causal_x = x_student.clone()
        last_step = seq_slice[:, -1, :]  # [w_clicks, cum_clicks, last_score, cum_late_ratio, cum_att_rate, cum_active_days]
        cum_clicks_norm = last_step[:, 1]
        last_score_norm = last_step[:, 2]
        cum_late_ratio = last_step[:, 3]
        cum_att_rate = last_step[:, 4]
        est_sub_rate = torch.clamp(1.0 - 0.5 * cum_late_ratio, 0.0, 1.0)

        causal_x[:, 2] = cum_att_rate
        causal_x[:, 3] = last_score_norm
        causal_x[:, 4] = est_sub_rate
        causal_x[:, 5] = cum_late_ratio
        causal_x[:, 6] = cum_clicks_norm
        if causal_x.size(1) > 7 and last_step.size(1) > 5:
            causal_x[:, 7] = last_step[:, 5]
        return causal_x

    def forward(self, x_dict: dict, edge_index_dict: dict, x_seq: torch.Tensor, cutoff_week: int = 16, graph_data=None):
        seq_slice = x_seq[:, :cutoff_week, :]
        _, (h_n, _) = self.lstm(seq_slice)
        h_temporal = self.temporal_norm(h_n[-1])

        causal_x_dict = dict(x_dict)
        causal_x_dict["student"] = self._build_causal_student_features(x_dict["student"], seq_slice, cutoff_week)
        causal_edges = filter_edges_by_cutoff_week(graph_data, edge_index_dict, cutoff_week)

        h_dict = {nt: proj(causal_x_dict[nt]) for nt, proj in self.input_proj.items()}
        week_ratio = float(cutoff_week) / 16.0
        h_dict["student"] = (1.0 - 0.5 * week_ratio) * h_temporal + (0.5 * week_ratio) * h_dict["student"]

        out1 = self.conv1(h_dict, causal_edges)
        for nt in h_dict:
            if nt in out1 and out1[nt] is not None:
                h_dict[nt] = self.norm1[nt](h_dict[nt] + F.dropout(F.gelu(out1[nt]), p=self.dropout, training=self.training))

        out2 = self.conv2(h_dict, causal_edges)
        for nt in h_dict:
            if nt in out2 and out2[nt] is not None:
                h_dict[nt] = self.norm2[nt](h_dict[nt] + F.dropout(F.gelu(out2[nt]), p=self.dropout, training=self.training))

        combined = torch.cat([h_temporal, h_dict["student"]], dim=-1)
        return self.classifier(combined)


def train_and_evaluate_temporal(epochs: int = 100):
    torch.manual_seed(42)
    np.random.seed(42)
    os.makedirs(MODELS_DIR, exist_ok=True)

    graph_path = os.path.join(PROCESSED_DIR, "graph.pt")
    data = torch.load(graph_path, weights_only=False)
    x_seq = build_weekly_sequences(RAW_DIR, PROCESSED_DIR)

    in_dims = {nt: data[nt].x.size(-1) for nt in data.node_types}
    model = TemporalHGTModel(in_dims=in_dims, metadata=data.metadata(), seq_in_dim=x_seq.size(-1), hidden_channels=64, num_heads=4)

    y_train_np = data["student"].y[data["student"].train_mask].numpy()
    weights = compute_class_weight("balanced", classes=np.array([0, 1]), y=y_train_np)
    weights[1] *= 1.2
    criterion = FocalLoss(weight=torch.tensor(weights, dtype=torch.float), alpha=0.65, gamma=2.0)
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.003, weight_decay=1e-4)

    train_mask = data["student"].train_mask
    val_mask = data["student"].val_mask
    test_mask = data["student"].test_mask

    best_score = -1.0
    ckpt_path = os.path.join(MODELS_DIR, "best_temporal_hgt.pt")

    horizons = [2, 4, 8, 12, 16]
    for epoch in range(1, epochs + 1):
        model.train()
        optimizer.zero_grad()
        total_loss = 0.0
        for w in horizons:
            logits = model(data.x_dict, data.edge_index_dict, x_seq, cutoff_week=w, graph_data=data)
            total_loss = total_loss + criterion(logits[train_mask], data["student"].y[train_mask])
        total_loss = total_loss / len(horizons)
        total_loss.backward()
        optimizer.step()

        if epoch % 10 == 0 or epoch == epochs:
            model.eval()
            with torch.no_grad():
                logits_w8 = model(data.x_dict, data.edge_index_dict, x_seq, cutoff_week=8, graph_data=data)
                probs_w8 = torch.softmax(logits_w8[val_mask], dim=-1)[:, 1].numpy()
                preds_w8 = (probs_w8 >= 0.48).astype(int)
                y_val = data["student"].y[val_mask].numpy()
                rec = float(recall_score(y_val, preds_w8, pos_label=1, zero_division=0))
                f1_m = float(f1_score(y_val, preds_w8, average="macro", zero_division=0))
                score = 0.5 * rec + 0.5 * f1_m
                if score > best_score:
                    best_score = score
                    torch.save({
                        "model_state_dict": model.state_dict(),
                        "in_dims": in_dims,
                        "seq_in_dim": int(x_seq.size(-1)),
                        "hidden_channels": 64,
                        "num_heads": 4
                    }, ckpt_path)

    ckpt = torch.load(ckpt_path, weights_only=False)
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()

    early_warning_results = {}
    y_test = data["student"].y[test_mask].numpy()

    print("\n=== CAUSAL EARLY WARNING HORIZON ANALYSIS (WITH ATTENDANCE) ===")
    print(f"{'Prediction Cutoff':<22} | {'Recall (Risk)':<14} | {'F1 (Macro)':<12} | {'F1 (Risk)':<12} | {'AUC-ROC':<10}")
    print("-" * 78)

    with torch.no_grad():
        val_logits_16 = model(data.x_dict, data.edge_index_dict, x_seq, cutoff_week=16, graph_data=data)
        val_probs_16 = torch.softmax(val_logits_16[val_mask], dim=-1)[:, 1].numpy()
        y_val = data["student"].y[val_mask].numpy()
        best_th = 0.55
        best_val_f1 = -1.0
        for th in np.linspace(0.40, 0.75, 36):
            vp = (val_probs_16 >= th).astype(int)
            vf1 = float(f1_score(y_val, vp, average="macro", zero_division=0))
            vrec = float(recall_score(y_val, vp, pos_label=1, zero_division=0))
            if vrec >= 0.85 and vf1 > best_val_f1:
                best_val_f1 = vf1
                best_th = float(th)

        for w in [2, 4, 8, 12, 16]:
            logits = model(data.x_dict, data.edge_index_dict, x_seq, cutoff_week=w, graph_data=data)
            probs = torch.softmax(logits[test_mask], dim=-1)[:, 1].numpy()
            preds = (probs >= best_th).astype(int)

            rec = float(recall_score(y_test, preds, pos_label=1, zero_division=0))
            prec = float(precision_score(y_test, preds, pos_label=1, zero_division=0))
            f1_m = float(f1_score(y_test, preds, average="macro", zero_division=0))
            f1_r = float(f1_score(y_test, preds, pos_label=1, zero_division=0))
            auc = float(roc_auc_score(y_test, probs))

            key = f"Week_{w}"
            early_warning_results[key] = {
                "week": w,
                "label": f"Tuần {w} ({'Rất sớm' if w==2 else 'Sớm' if w==4 else 'Giữa kỳ' if w==8 else 'Cuối kỳ' if w==12 else 'Toàn kỳ'})",
                "recall_risk": round(rec, 4),
                "precision_risk": round(prec, 4),
                "f1_macro": round(f1_m, 4),
                "f1_risk": round(f1_r, 4),
                "auc_roc": round(auc, 4)
            }
            print(f"{early_warning_results[key]['label']:<22} | {rec:<14.4f} | {f1_m:<12.4f} | {f1_r:<12.4f} | {auc:<10.4f}")

    summary_path = os.path.join(PROCESSED_DIR, "benchmark_summary.json")
    if os.path.exists(summary_path):
        with open(summary_path, "r", encoding="utf-8") as f:
            bench = json.load(f)
        bench["HGT + LSTM (Temporal)"] = {
            "f1_macro": early_warning_results["Week_16"]["f1_macro"],
            "f1_risk": early_warning_results["Week_16"]["f1_risk"],
            "recall_risk": early_warning_results["Week_16"]["recall_risk"],
            "precision_risk": early_warning_results["Week_16"]["precision_risk"],
            "auc_roc": early_warning_results["Week_16"]["auc_roc"]
        }
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(bench, f, indent=2, ensure_ascii=False)

    ew_path = os.path.join(PROCESSED_DIR, "early_warning_metrics.json")
    with open(ew_path, "w", encoding="utf-8") as f:
        json.dump(early_warning_results, f, indent=2, ensure_ascii=False)
    print(f"[OK] Saved Early Warning horizon metrics to: {ew_path}")
    return early_warning_results


if __name__ == "__main__":
    train_and_evaluate_temporal()
