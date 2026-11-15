import os
import sys
import torch
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from gnn.models.hgt_model import StudentRiskHGT
from gnn.temporal_model import TemporalHGTModel
from gnn.build_graph import CONCEPTS

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PROCESSED_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "data", "processed"))
MODELS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "models"))

# 7 Fair Pedagogical, Attendance & Behavioral Features (Demographic gender_code excluded)
FEATURE_METADATA = [
    ("studied_credits_norm", "Khối lượng tín chỉ đăng ký", True),
    ("num_of_prev_attempts", "Số lần học lại / thi lại trước đó", True),
    ("attendance_rate", "Tỷ lệ điểm danh chuyên cần trên lớp (Attendance)", False),
    ("avg_score_norm", "Điểm trung bình bài kiểm tra (Assessment Score)", False),
    ("submission_rate", "Tỷ lệ nộp bài tập đúng tiến độ", False),
    ("late_submission_rate", "Tỷ lệ nộp bài trễ hạn (Late Submission)", True),
    ("total_clicks_norm", "Mức độ tương tác học liệu VLE (Clicks)", False),
    ("active_days_norm", "Số ngày hoạt động trên VLE (Active Days)", False),
]


class StudentRiskExplainer:
    """
    Explainable AI (XAI) Engine for Heterogeneous Student Risk GNN:
    1. Gradient x Counterfactual Feature Attribution (including Class Attendance Rate)
    2. Relational Subgraph Edge Perturbation + Attendance Exam-Ban Regulation Check
    3. Causal Early Warning Weekly Trajectory Analysis (Week 2 -> Week 16)
    """
    def __init__(self):
        self.device = torch.device("cpu")
        self.hgt_model = None
        self.temporal_model = None
        self.graph_data = None
        self.weekly_seq = None
        self.student_df = None
        self.safe_mean = None
        self._xai_cache: Dict[int, Dict[str, Any]] = {}
        self._load_all()

    def _load_all(self):
        self._xai_cache.clear()
        graph_path = os.path.join(PROCESSED_DIR, "graph.pt")
        hgt_ckpt_path = os.path.join(MODELS_DIR, "best_hgt_model.pt")
        temp_ckpt_path = os.path.join(MODELS_DIR, "best_temporal_hgt.pt")
        seq_path = os.path.join(PROCESSED_DIR, "weekly_sequences.pt")
        csv_path = os.path.join(PROCESSED_DIR, "student_features.csv")

        if os.path.exists(csv_path):
            self.student_df = pd.read_csv(csv_path)

        if os.path.exists(graph_path):
            self.graph_data = torch.load(graph_path, map_location=self.device, weights_only=False)
            train_safe_mask = (self.graph_data["student"].y == 0) & self.graph_data["student"].train_mask
            if train_safe_mask.sum() == 0:
                train_safe_mask = (self.graph_data["student"].y == 0)
            self.safe_mean = self.graph_data["student"].x[train_safe_mask].mean(dim=0).detach()

        if self.graph_data is not None and os.path.exists(hgt_ckpt_path):
            ckpt = torch.load(hgt_ckpt_path, map_location=self.device, weights_only=False)
            self.hgt_model = StudentRiskHGT(
                in_dims=ckpt["in_dims"],
                metadata=self.graph_data.metadata(),
                hidden_channels=ckpt["hidden_channels"],
                num_heads=ckpt["num_heads"],
                num_layers=2,
                dropout=0.0
            ).to(self.device)
            self.hgt_model.load_state_dict(ckpt["model_state_dict"])
            self.hgt_model.eval()

        if os.path.exists(seq_path):
            self.weekly_seq = torch.load(seq_path, map_location=self.device, weights_only=False)

        if self.graph_data is not None and os.path.exists(temp_ckpt_path):
            t_ckpt = torch.load(temp_ckpt_path, map_location=self.device, weights_only=False)
            self.temporal_model = TemporalHGTModel(
                in_dims=t_ckpt["in_dims"],
                metadata=self.graph_data.metadata(),
                seq_in_dim=t_ckpt.get("seq_in_dim", 5),
                hidden_channels=t_ckpt["hidden_channels"],
                num_heads=t_ckpt["num_heads"],
                dropout=0.0
            ).to(self.device)
            self.temporal_model.load_state_dict(t_ckpt["model_state_dict"])
            self.temporal_model.eval()

    def invalidate_cache(self, student_id: Optional[int] = None):
        if student_id is None:
            self._xai_cache.clear()
        else:
            self._xai_cache.pop(student_id, None)

    def resolve_node_idx(self, student_id: int) -> int:
        if self.student_df is not None:
            exact = self.student_df[self.student_df["id_student"] == student_id]
            if len(exact) > 0:
                return int(exact.iloc[0]["node_idx"])
        num_nodes = self.graph_data["student"].num_nodes if self.graph_data is not None else 300
        return max(0, min(num_nodes - 1, student_id - 1))

    def update_attendance_in_memory(self, student_id: int, attended_sessions: int, total_sessions: int = 9):
        """
        Updates the live graph tensor, weekly sequence tensor, and dataframe for a student's class attendance,
        then invalidates their XAI cache so the next prediction reflects the new attendance immediately.
        """
        if self.graph_data is None or self.student_df is None:
            self._load_all()

        total_sessions = max(1, int(total_sessions))
        attended_sessions = max(0, min(total_sessions, int(attended_sessions)))
        absent_sessions = total_sessions - attended_sessions
        att_rate = round(attended_sessions / float(total_sessions), 3)

        node_idx = self.resolve_node_idx(student_id)
        self.student_df.loc[node_idx, "total_sessions"] = total_sessions
        self.student_df.loc[node_idx, "attended_sessions"] = attended_sessions
        self.student_df.loc[node_idx, "absent_sessions"] = absent_sessions
        self.student_df.loc[node_idx, "attendance_rate"] = att_rate

        # Column 2 of student.x is attendance_rate
        self.graph_data["student"].x[node_idx, 2] = float(att_rate)

        # Update weekly_seq dim 4 (cumulative attendance rate)
        if self.weekly_seq is not None and self.weekly_seq.size(-1) >= 5:
            self.weekly_seq[node_idx, :, 4] = float(att_rate)

        self.invalidate_cache(student_id)

    def explain_student(self, student_id: int, force_refresh: bool = False) -> Dict[str, Any]:
        if self.hgt_model is None or self.graph_data is None:
            self._load_all()

        if not force_refresh and student_id in self._xai_cache:
            return self._xai_cache[student_id]

        node_idx = self.resolve_node_idx(student_id)
        row = self.student_df.iloc[node_idx]

        # 1. Gradient x Counterfactual Feature Attributions
        with torch.enable_grad():
            x_dict = {nt: self.graph_data[nt].x.clone().detach() for nt in self.graph_data.node_types}
            x_dict["student"].requires_grad_(True)

            logits = self.hgt_model(x_dict, self.graph_data.edge_index_dict)
            probs = torch.softmax(logits[node_idx], dim=-1)
            base_hgt_prob = float(probs[1].item())

            target_margin = logits[node_idx, 1] - logits[node_idx, 0]
            self.hgt_model.zero_grad()
            target_margin.backward()

            grad = x_dict["student"].grad[node_idx].detach()
        diff_from_safe = (self.graph_data["student"].x[node_idx] - self.safe_mean).detach()
        raw_attr = (grad * diff_from_safe).numpy()

        # Adjust risk probability with explicit attendance impact (9 sessions per semester)
        att_rate = float(row.get("attendance_rate", 0.889))
        absent_sessions = int(row.get("absent_sessions", 1))
        total_sessions = int(row.get("total_sessions", 9))
        attended_sessions = int(row.get("attended_sessions", total_sessions - absent_sessions))

        # Combine GNN structural probability with attendance regulation modifier (absent >= 2/9 is < 80% exam ban)
        att_delta = (0.85 - att_rate) * 0.45 + (0.14 if absent_sessions >= 2 or att_rate < 0.80 else 0.0)
        risk_prob = float(np.clip(base_hgt_prob + att_delta, 0.02, 0.99))

        # Ensure attendance attribution reflects deficit vs safe mean
        safe_att = float(self.safe_mean[2].item())
        if abs(raw_attr[2]) < 0.05 and abs(att_rate - safe_att) > 0.02:
            raw_attr[2] = (safe_att - att_rate) * 1.5

        max_abs = max(1e-4, float(np.max(np.abs(raw_attr))))
        norm_attr = raw_attr / max_abs

        feature_attributions = []
        num_feats = min(len(FEATURE_METADATA), int(self.graph_data["student"].x.size(1)))
        for i, (col_name, label_vi, _) in enumerate(FEATURE_METADATA[:num_feats]):
            impact = float(norm_attr[i])
            val = float(self.graph_data["student"].x[node_idx, i].item())
            safe_val = float(self.safe_mean[i].item())

            if col_name == "attendance_rate":
                exam_ban_note = " - CẢNH BÁO CẤM THI (>20% vắng)" if att_rate < 0.80 else ""
                desc = (
                    f"Điểm danh: {attended_sessions}/{total_sessions} buổi ({att_rate*100:.0f}%, vắng {absent_sessions} buổi{exam_ban_note} | "
                    f"Chuẩn an toàn: {safe_val*100:.0f}%)"
                )
            elif col_name == "avg_score_norm":
                desc = f"Điểm TB bài tập: {row['avg_score']:.1f}/100 (Chuẩn nhóm an toàn: {safe_val*100:.1f}/100)"
            elif col_name == "submission_rate":
                desc = f"Tỷ lệ nộp bài: {row['submission_rate']*100:.0f}% (Chuẩn nhóm an toàn: {safe_val*100:.0f}%)"
            elif col_name == "late_submission_rate":
                desc = f"Tỷ lệ nộp trễ: {row['late_submission_rate']*100:.0f}% (Chuẩn nhóm an toàn: {safe_val*100:.0f}%)"
            elif col_name == "total_clicks_norm":
                desc = f"Tương tác học liệu VLE: {int(row['total_clicks'])} clicks (Chuẩn an toàn: ~{int(safe_val*100)} clicks)"
            elif col_name == "num_of_prev_attempts":
                desc = f"Số lần học lại trước đó: {int(row['num_of_prev_attempts'])} lần"
            elif col_name == "active_days_norm":
                act_days = int(row.get("active_days", 0))
                desc = f"Số ngày hoạt động trên VLE: {act_days} ngày (Chuẩn nhóm an toàn: {safe_val*100:.0f}% mức trần P98)"
            else:
                desc = f"Số tín chỉ đăng ký: {int(round(val*120))} tín chỉ"

            feature_attributions.append({
                "feature_key": col_name,
                "feature_name": label_vi,
                "description": desc,
                "impact_score": round(impact, 3),
                "is_negative_impact": bool(impact > 0.0)
            })

        feature_attributions.sort(key=lambda x: abs(x["impact_score"]), reverse=True)

        # 2. Subgraph Edge Perturbation (2-hop Student -> Assignment -> Concept + Attendance Rule)
        subgraph_edges = self._explain_subgraph_edges(node_idx, risk_prob, attended_sessions, total_sessions, absent_sessions)

        # 3. Causal Early Warning Weekly Trajectory (Week 2, 4, 8, 12, 16)
        trajectory = self._compute_weekly_trajectory(node_idx, att_delta)

        result = {
            "student_id": student_id,
            "graph_node_idx": int(node_idx),
            "risk_score": round(risk_prob, 4),
            "risk_level": "High" if risk_prob >= 0.70 else ("Medium" if risk_prob >= 0.40 else "Low"),
            "attendance_rate": round(att_rate, 3),
            "attended_sessions": attended_sessions,
            "total_sessions": total_sessions,
            "absent_sessions": absent_sessions,
            "feature_attributions": feature_attributions,
            "subgraph_explanations": subgraph_edges,
            "early_warning_trajectory": trajectory
        }
        self._xai_cache[student_id] = result
        return result

    @torch.no_grad()
    def _explain_subgraph_edges(
        self,
        node_idx: int,
        base_risk: float,
        attended_sessions: int,
        total_sessions: int,
        absent_sessions: int
    ) -> List[Dict[str, Any]]:
        explanations = []
        edge_dict = self.graph_data.edge_index_dict

        # Check Class Attendance Regulation (9 sessions: >= 2 absences -> < 80% attendance)
        att_rate = attended_sessions / float(max(1, total_sessions))
        if absent_sessions >= 2 or att_rate < 0.80:
            explanations.append({
                "edge_type": "student --[absent_class]--> course_regulation",
                "assignment_node": f"Vắng {absent_sessions}/{total_sessions} buổi ({att_rate*100:.0f}%)",
                "concept_node": "Quy chế Điểm danh (>= 80% | Tối thiểu 8/9 buổi)",
                "risk_contribution": round(max(0.16, (0.88 - att_rate) * 0.55), 4),
                "explanation": f"Sinh viên đã vắng {absent_sessions}/{total_sessions} buổi học trên lớp (chuyên cần đạt {att_rate*100:.0f}% < ngưỡng tối thiểu 80%), nguy cơ cao bị cấm thi kết thúc học phần"
            })
        elif absent_sessions == 1:
            explanations.append({
                "edge_type": "student --[early_absence]--> course_regulation",
                "assignment_node": f"Vắng 1/{total_sessions} buổi ({att_rate*100:.0f}%)",
                "concept_node": "Cảnh báo Chuyên cần Sớm",
                "risk_contribution": 0.08,
                "explanation": f"Sinh viên đã vắng 1/{total_sessions} buổi học; chỉ cần vắng thêm 1 buổi nữa sẽ vượt quá 20% giới hạn quy chế dự thi"
            })

        ass_to_concept = {}
        if ("assignment", "tests", "concept") in edge_dict:
            ei = edge_dict[("assignment", "tests", "concept")]
            for a_i, c_i in zip(ei[0].tolist(), ei[1].tolist()):
                ass_to_concept[a_i] = CONCEPTS[c_i % len(CONCEPTS)]

        if ("student", "failed", "assignment") in edge_dict:
            ei_fail = edge_dict[("student", "failed", "assignment")]
            mask_student = (ei_fail[0] == node_idx)
            failed_ass = ei_fail[1][mask_student].tolist()

            for a_idx in failed_ass:
                mod_edges = {k: v.clone() for k, v in edge_dict.items()}
                keep_f = ~((ei_fail[0] == node_idx) & (ei_fail[1] == a_idx))
                mod_edges[("student", "failed", "assignment")] = ei_fail[:, keep_f]

                ei_rev = edge_dict[("assignment", "rev_failed", "student")]
                keep_rev = ~((ei_rev[0] == a_idx) & (ei_rev[1] == node_idx))
                mod_edges[("assignment", "rev_failed", "student")] = ei_rev[:, keep_rev]

                cf_logits = self.hgt_model(self.graph_data.x_dict, mod_edges)
                cf_risk = float(torch.softmax(cf_logits[node_idx], dim=-1)[1].item())
                delta = max(0.01, base_risk - cf_risk)
                concept_name = ass_to_concept.get(a_idx, "Khái niệm cơ sở")

                explanations.append({
                    "edge_type": "student --[failed/late]--> assignment --[tests]--> concept",
                    "assignment_node": f"Assignment #{a_idx + 1}",
                    "concept_node": concept_name,
                    "risk_contribution": round(delta, 4),
                    "explanation": f"Cạnh tương tác lỗi/nộp trễ tại Bài tập #{a_idx + 1} (kiểm tra '{concept_name}') làm tăng nguy cơ rủi ro"
                })

        if ("student", "watched", "lesson") in edge_dict:
            ei_watch = edge_dict[("student", "watched", "lesson")]
            watched_count = int((ei_watch[0] == node_idx).sum().item())
            if watched_count < 8:
                explanations.append({
                    "edge_type": "student --[missing_views]--> lesson",
                    "assignment_node": f"Watched {watched_count}/18 Lessons",
                    "concept_node": "Chuỗi bài giảng VLE",
                    "risk_contribution": 0.12,
                    "explanation": f"Đồ thị ghi nhận sinh viên mới xem {watched_count}/18 bài giảng VLE của môn học (thiếu kết nối tới các bài học trọng tâm)"
                })

        explanations.sort(key=lambda x: x["risk_contribution"], reverse=True)
        return explanations[:4]

    @torch.no_grad()
    def _compute_weekly_trajectory(self, node_idx: int, att_delta: float = 0.0) -> List[Dict[str, Any]]:
        if self.temporal_model is None or self.weekly_seq is None:
            return []

        trajectory = []
        for w in [2, 4, 8, 12, 16]:
            logits = self.temporal_model(
                self.graph_data.x_dict,
                self.graph_data.edge_index_dict,
                self.weekly_seq,
                cutoff_week=w,
                graph_data=self.graph_data
            )
            base_prob = float(torch.softmax(logits[node_idx], dim=-1)[1].item())
            scale = float(w) / 16.0
            prob = float(np.clip(base_prob + att_delta * scale, 0.02, 0.99))
            trajectory.append({
                "week": w,
                "risk_score": round(prob, 4),
                "status": "High" if prob >= 0.70 else ("Medium" if prob >= 0.40 else "Low")
            })
        return trajectory


if __name__ == "__main__":
    explainer = StudentRiskExplainer()
    sample = explainer.explain_student(1)
    import json
    print(json.dumps(sample, indent=2, ensure_ascii=False))
