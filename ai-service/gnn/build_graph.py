import os
import json
import torch
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from torch_geometric.data import HeteroData
from gnn.data_quality import clean_table, fit_outlier_caps

RAW_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "data", "raw"))
PROCESSED_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "data", "processed"))

CONCEPTS = [
    "Con trỏ & Quản lý bộ nhớ (Pointers & Memory)",
    "Đệ quy & Quy nạp (Recursion)",
    "Cấu trúc dữ liệu tuyến tính (Stack & Queue)",
    "Cây & Đồ thị (Trees & Graphs)"
]

# Student node feature order (index positions are relied upon by temporal_model, explainer & ablation)
STUDENT_FEATURE_COLS = [
    "studied_credits_norm",   # 0
    "num_of_prev_attempts",   # 1
    "attendance_rate",        # 2
    "avg_score_norm",         # 3
    "submission_rate",        # 4
    "late_submission_rate",   # 5
    "total_clicks_norm",      # 6
    "active_days_norm",       # 7 (distinct VLE active days, P98-capped on train)
]

def build_heterogeneous_graph(raw_dir: str = RAW_DIR, output_dir: str = PROCESSED_DIR, force_regen: bool = False) -> HeteroData:
    os.makedirs(output_dir, exist_ok=True)

    courses_file = os.path.join(raw_dir, "courses.csv")
    students_file = os.path.join(raw_dir, "studentInfo.csv")
    attendance_file = os.path.join(raw_dir, "studentAttendance.csv")
    required = ("courses.csv", "vle.csv", "assessments.csv", "studentInfo.csv",
                "studentRegistration.csv", "studentAssessment.csv", "studentVle.csv",
                "studentAttendance.csv")
    missing = [name for name in required if not os.path.isfile(os.path.join(raw_dir, name))]
    if missing:
        raise FileNotFoundError(f"Missing raw CSVs: {', '.join(missing)}")

    # Load tables
    courses_df = pd.read_csv(os.path.join(raw_dir, "courses.csv"))
    vle_df = pd.read_csv(os.path.join(raw_dir, "vle.csv"))
    assessments_df = pd.read_csv(os.path.join(raw_dir, "assessments.csv"))
    students_df = pd.read_csv(os.path.join(raw_dir, "studentInfo.csv"))
    student_assessments_df = pd.read_csv(os.path.join(raw_dir, "studentAssessment.csv"))
    student_vle_df = pd.read_csv(os.path.join(raw_dir, "studentVle.csv"))
    student_att_df = pd.read_csv(os.path.join(raw_dir, "studentAttendance.csv"))

    # Data quality: drop all-null columns, rows missing key IDs and exact duplicates (OULAD ETL step)
    courses_df = clean_table("courses", courses_df)
    vle_df = clean_table("vle", vle_df)
    assessments_df = clean_table("assessments", assessments_df)
    students_df = clean_table("studentInfo", students_df).drop_duplicates(subset=["id_student"]).reset_index(drop=True)
    student_assessments_df = clean_table("studentAssessment", student_assessments_df)
    student_vle_df = clean_table("studentVle", student_vle_df)
    student_att_df = clean_table("studentAttendance", student_att_df)
    if "score" in student_assessments_df.columns:
        student_assessments_df["score"] = student_assessments_df["score"].fillna(0.0)

    # Map IDs to continuous 0-based indices
    student_ids = sorted(students_df["id_student"].unique())
    student_id_map = {id_: idx for idx, id_ in enumerate(student_ids)}
    course_id_map = {id_: idx for idx, id_ in enumerate(courses_df["code_module"].unique())}
    lesson_id_map = {id_: idx for idx, id_ in enumerate(vle_df["id_site"].unique())}
    assessment_id_map = {id_: idx for idx, id_ in enumerate(assessments_df["id_assessment"].unique())}

    # Merge assessment deadlines to check late submissions
    sa_merged = student_assessments_df.merge(
        assessments_df[["id_assessment", "date", "weight", "concept_idx"]],
        on="id_assessment",
        how="left"
    )
    sa_merged["is_late"] = (sa_merged["date_submitted"] > sa_merged["date"]).astype(int)
    sa_merged["week"] = np.clip((sa_merged["date"] // 7).astype(int), 1, 16)
    student_vle_df["week"] = np.clip((student_vle_df["date"] // 7).astype(int) + 1, 1, 16)

    # Feature engineering per student (including Class Attendance)
    tabular_rows = []
    for s_id in student_ids:
        s_row = students_df[students_df["id_student"] == s_id].iloc[0]
        s_sa = sa_merged[sa_merged["id_student"] == s_id]
        s_vle = student_vle_df[student_vle_df["id_student"] == s_id]
        s_att = student_att_df[student_att_df["id_student"] == s_id]

        total_sessions = len(s_att) if len(s_att) > 0 else 9
        attended_sessions = int(s_att["attended"].sum()) if len(s_att) > 0 else 8
        absent_sessions = max(0, total_sessions - attended_sessions)
        attendance_rate = attended_sessions / float(max(1, total_sessions))

        total_course_assessments = len(assessments_df[assessments_df["code_module"] == s_row["code_module"]])
        sub_count = len(s_sa)
        submission_rate = sub_count / max(1, total_course_assessments)
        avg_score = float(s_sa["score"].mean()) if sub_count > 0 else 0.0
        late_rate = float(s_sa["is_late"].mean()) if sub_count > 0 else 1.0
        total_clicks = int(s_vle["sum_click"].sum()) if len(s_vle) > 0 else 0
        lessons_watched = len(s_vle["id_site"].unique())
        # Number of distinct days with VLE activity: the strongest predictor of negative outcomes
        # in the OULAD reference analysis (`total_n_days`, RF importance ~0.46)
        active_days = int(s_vle["date"].nunique()) if len(s_vle) > 0 else 0

        # Weakest concept detection based on assessment scores AND missed class attendance sessions
        weak_concepts = []
        for c_idx, c_name in enumerate(CONCEPTS):
            c_sa = s_sa[s_sa["concept_idx"] == c_idx]
            c_att = s_att[s_att["concept_idx"] == c_idx]
            missed_concept_classes = int((c_att["attended"] == 0).sum()) if len(c_att) > 0 else 0
            if len(c_sa) == 0 or c_sa["score"].mean() < 55.0 or missed_concept_classes >= 2:
                weak_concepts.append(c_name)

        is_at_risk = 1 if s_row["final_result"] in ["Fail", "Withdrawn"] else 0

        tabular_rows.append({
            "id_student": int(s_id),
            "node_idx": student_id_map[s_id],
            "code_module": s_row["code_module"],
            "gender_code": 1.0 if s_row["gender"] == "F" else 0.0,
            "studied_credits_norm": float(s_row["studied_credits"]) / 120.0,
            "num_of_prev_attempts": float(s_row["num_of_prev_attempts"]),
            "total_sessions": total_sessions,
            "attended_sessions": attended_sessions,
            "absent_sessions": absent_sessions,
            "attendance_rate": round(attendance_rate, 3),
            "avg_score_norm": avg_score / 100.0,
            "avg_score": round(avg_score, 1),
            "submission_rate": round(submission_rate, 3),
            "late_submission_rate": round(late_rate, 3),
            "total_clicks": total_clicks,
            "total_clicks_norm": min(1.0, total_clicks / 100.0),
            "lessons_watched": lessons_watched,
            "active_days": active_days,
            "weak_concepts": "|".join(weak_concepts[:2]) if weak_concepts else "",
            "is_at_risk": is_at_risk
        })

    tabular_df = pd.DataFrame(tabular_rows)

    # Stratified Train / Val / Test split (70% / 15% / 15%)
    indices = np.arange(len(tabular_df))
    labels = tabular_df["is_at_risk"].values
    train_idx, temp_idx, _, temp_y = train_test_split(
        indices, labels, test_size=0.30, stratify=labels, random_state=42
    )
    val_idx, test_idx = train_test_split(
        temp_idx, test_size=0.50, stratify=temp_y, random_state=42
    )

    train_mask = torch.zeros(len(tabular_df), dtype=torch.bool)
    val_mask = torch.zeros(len(tabular_df), dtype=torch.bool)
    test_mask = torch.zeros(len(tabular_df), dtype=torch.bool)
    train_mask[train_idx] = True
    val_mask[val_idx] = True
    test_mask[test_idx] = True

    tabular_df["split"] = "train"
    tabular_df.loc[val_idx, "split"] = "val"
    tabular_df.loc[test_idx, "split"] = "test"

    # Outlier capping at P98 fitted on TRAIN only (right-skewed count), then min-max to [0, 1]
    caps = fit_outlier_caps(tabular_df, ["active_days"], fit_mask=train_mask.numpy())
    active_days_cap = max(1.0, caps.get("active_days", 1.0))
    tabular_df["active_days_norm"] = (
        tabular_df["active_days"].clip(upper=active_days_cap) / active_days_cap
    ).round(4)
    with open(os.path.join(output_dir, "feature_scaling.json"), "w", encoding="utf-8") as f:
        json.dump({"active_days_cap": active_days_cap, "quantile": 0.98, "fitted_on": "train"}, f, indent=2)

    tabular_df.to_csv(os.path.join(output_dir, "student_features.csv"), index=False)

    # Build HeteroData
    data = HeteroData()

    # 1. Student Nodes [N_sv, 8] - Fair academic, attendance & behavioral features (no demographic gender)
    feature_cols = STUDENT_FEATURE_COLS
    data["student"].x = torch.tensor(tabular_df[feature_cols].values, dtype=torch.float)
    data["student"].y = torch.tensor(labels, dtype=torch.long)
    data["student"].train_mask = train_mask
    data["student"].val_mask = val_mask
    data["student"].test_mask = test_mask
    data["student"].num_nodes = len(tabular_df)

    # 2. Course Nodes [N_mh, 2] - Compute historical fail rate strictly on TRAIN split
    train_only_df = tabular_df.iloc[train_idx]
    course_feats = []
    for _, c_row in courses_df.iterrows():
        m = c_row["code_module"]
        m_students = train_only_df[train_only_df["code_module"] == m]
        hist_fail_rate = float(m_students["is_at_risk"].mean()) if len(m_students) > 0 else 0.3
        course_feats.append([float(c_row["module_presentation_length"]) / 260.0, hist_fail_rate])
    data["course"].x = torch.tensor(course_feats, dtype=torch.float)
    data["course"].num_nodes = len(course_id_map)

    # 3. Lesson Nodes (VLE) [N_bl, 2]
    act_types = {a: i / 5.0 for i, a in enumerate(vle_df["activity_type"].unique())}
    vle_feats = []
    for _, v_row in vle_df.iterrows():
        w_norm = float(v_row["week_from"]) / 16.0
        a_code = act_types.get(v_row["activity_type"], 0.0)
        vle_feats.append([w_norm, a_code])
    data["lesson"].x = torch.tensor(vle_feats, dtype=torch.float)
    data["lesson"].num_nodes = len(lesson_id_map)

    # 4. Assignment Nodes [N_bt, 3] - Compute avg score on TRAIN split students only
    train_student_ids = set(train_only_df["id_student"].tolist())
    sa_train_only = sa_merged[sa_merged["id_student"].isin(train_student_ids)]
    ass_feats = []
    for _, a_row in assessments_df.iterrows():
        a_id = a_row["id_assessment"]
        a_subs = sa_train_only[sa_train_only["id_assessment"] == a_id]
        avg_s = float(a_subs["score"].mean()) / 100.0 if len(a_subs) > 0 else 0.5
        ass_feats.append([float(a_row["weight"]) / 40.0, float(a_row["date"]) / 120.0, avg_s])
    data["assignment"].x = torch.tensor(ass_feats, dtype=torch.float)
    data["assignment"].num_nodes = len(assessment_id_map)

    # 5. Concept Nodes [N_kc, 4]
    data["concept"].x = torch.eye(len(CONCEPTS), dtype=torch.float)
    data["concept"].num_nodes = len(CONCEPTS)

    # === EDGES & REVERSE EDGES (with temporal edge_week for leakage-free Early Warning) ===
    def add_bi_edge(src_type, rel, dst_type, src_list, dst_list, edge_attr=None, edge_week=None):
        edge_index = torch.tensor([src_list, dst_list], dtype=torch.long)
        rev_edge_index = torch.tensor([dst_list, src_list], dtype=torch.long)
        data[src_type, rel, dst_type].edge_index = edge_index
        data[dst_type, f"rev_{rel}", src_type].edge_index = rev_edge_index
        if edge_attr is not None:
            data[src_type, rel, dst_type].edge_attr = edge_attr
            data[dst_type, f"rev_{rel}", src_type].edge_attr = edge_attr
        if edge_week is not None:
            w_tensor = torch.tensor(edge_week, dtype=torch.long)
            data[src_type, rel, dst_type].edge_week = w_tensor
            data[dst_type, f"rev_{rel}", src_type].edge_week = w_tensor

    # 1. student <-> enrolled <-> course
    enrolled_src = [student_id_map[s_id] for s_id in students_df["id_student"]]
    enrolled_dst = [course_id_map[c_id] for c_id in students_df["code_module"]]
    add_bi_edge("student", "enrolled", "course", enrolled_src, enrolled_dst)

    # 2. student <-> watched <-> lesson
    watched_src, watched_dst, watched_attr, watched_week = [], [], [], []
    for _, row in student_vle_df.iterrows():
        s_id, v_id = row["id_student"], row["id_site"]
        if s_id in student_id_map and v_id in lesson_id_map:
            watched_src.append(student_id_map[s_id])
            watched_dst.append(lesson_id_map[v_id])
            watched_attr.append([min(1.0, float(row["sum_click"]) / 20.0)])
            watched_week.append(int(row["week"]))
    add_bi_edge(
        "student", "watched", "lesson",
        watched_src, watched_dst,
        torch.tensor(watched_attr, dtype=torch.float),
        watched_week
    )

    # 3. student <-> submitted / failed <-> assignment
    submitted_src, submitted_dst, submitted_attr, submitted_week = [], [], [], []
    failed_src, failed_dst, failed_week = [], [], []
    passed_src, passed_dst, passed_week = [], [], []
    for _, row in sa_merged.iterrows():
        s_id, a_id = row["id_student"], row["id_assessment"]
        if s_id in student_id_map and a_id in assessment_id_map:
            s_idx = student_id_map[s_id]
            a_idx = assessment_id_map[a_id]
            w_val = int(row["week"])
            submitted_src.append(s_idx)
            submitted_dst.append(a_idx)
            submitted_attr.append([float(row["score"]) / 100.0, float(row["is_late"])])
            submitted_week.append(w_val)
            if float(row["score"]) < 55.0 or int(row["is_late"]) == 1:
                failed_src.append(s_idx)
                failed_dst.append(a_idx)
                failed_week.append(w_val)
            else:
                passed_src.append(s_idx)
                passed_dst.append(a_idx)
                passed_week.append(w_val)
    add_bi_edge(
        "student", "submitted", "assignment",
        submitted_src, submitted_dst,
        torch.tensor(submitted_attr, dtype=torch.float),
        submitted_week
    )
    if failed_src:
        add_bi_edge("student", "failed", "assignment", failed_src, failed_dst, edge_week=failed_week)
    if passed_src:
        add_bi_edge("student", "passed", "assignment", passed_src, passed_dst, edge_week=passed_week)

    # 4. assignment <-> tests <-> concept
    tests_src, tests_dst = [], []
    for i, row in assessments_df.iterrows():
        a_id = row["id_assessment"]
        c_idx = int(row.get("concept_idx", i % len(CONCEPTS)))
        tests_src.append(assessment_id_map[a_id])
        tests_dst.append(c_idx)
    add_bi_edge("assignment", "tests", "concept", tests_src, tests_dst)

    # 5. lesson <-> teaches <-> concept
    teaches_src, teaches_dst = [], []
    for i, row in vle_df.iterrows():
        v_id = row["id_site"]
        c_idx = int(row.get("concept_idx", (i // 3) % len(CONCEPTS)))
        teaches_src.append(lesson_id_map[v_id])
        teaches_dst.append(c_idx)
    add_bi_edge("lesson", "teaches", "concept", teaches_src, teaches_dst)

    out_file = os.path.join(output_dir, "graph.pt")
    torch.save(data, out_file)
    print(f"[OK] Bidirectional Fair Heterogeneous Graph (with Attendance) saved to: {out_file}")
    print(f"[INFO] Student features saved to: {os.path.join(output_dir, 'student_features.csv')}")
    return data

if __name__ == "__main__":
    build_heterogeneous_graph(force_regen=True)
