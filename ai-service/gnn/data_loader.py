import os
import pandas as pd
import numpy as np

DATA_RAW_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "data", "raw"))

class OuladDataLoader:
    def __init__(self, raw_dir: str = DATA_RAW_DIR):
        self.raw_dir = raw_dir
        os.makedirs(self.raw_dir, exist_ok=True)

    def generate_synthetic_oulad_sample(self, num_students: int = 300, num_courses: int = 4, seed: int = 42):
        """
        Generates a realistic OULAD-schema dataset with weekly class attendance (15 sessions),
        latent concept mastery, noise, and class imbalance so both tabular baselines and
        Heterogeneous GNN models can be rigorously benchmarked.
        """
        np.random.seed(seed)
        print(f"[DATA] Generating OULAD + Class Attendance dataset ({num_students} students, {num_courses} courses)...")

        # 1. Courses
        courses_df = pd.DataFrame({
            "code_module": [f"CS{i+1}01" for i in range(num_courses)],
            "code_presentation": ["2026J"] * num_courses,
            "module_presentation_length": [240, 240, 210, 260][:num_courses]
        })
        courses_df.to_csv(os.path.join(self.raw_dir, "courses.csv"), index=False)

        # 2. VLE (Virtual Learning Environment resources / lessons)
        vle_records = []
        vle_id = 1000
        activities = ["homepage", "resource", "quiz", "forumng", "oucontent", "subpage"]
        for m in courses_df["code_module"]:
            for act in activities:
                for i in range(3):
                    vle_records.append({
                        "id_site": vle_id,
                        "code_module": m,
                        "code_presentation": "2026J",
                        "activity_type": act,
                        "week_from": i * 4 + 1,
                        "week_to": (i + 1) * 4,
                        "concept_idx": (vle_id % 4)
                    })
                    vle_id += 1
        vle_df = pd.DataFrame(vle_records)
        vle_df.to_csv(os.path.join(self.raw_dir, "vle.csv"), index=False)

        # 3. Assessments
        assessments_records = []
        assessment_id = 5000
        for m in courses_df["code_module"]:
            for idx_w, week in enumerate([4, 8, 12, 16]):
                assessments_records.append({
                    "id_assessment": assessment_id,
                    "code_module": m,
                    "code_presentation": "2026J",
                    "assessment_type": "TMA" if week < 16 else "Exam",
                    "date": week * 7,
                    "weight": 20.0 if week < 16 else 40.0,
                    "concept_idx": idx_w % 4
                })
                assessment_id += 1
        assessments_df = pd.DataFrame(assessments_records)
        assessments_df.to_csv(os.path.join(self.raw_dir, "assessments.csv"), index=False)

        # 4. Students info, Class Attendance (9 sessions per semester) & latent variables
        genders = ["M", "F"]
        regions = ["North", "South", "Central", "East"]
        students = []
        registrations = []
        student_assessments = []
        student_vle = []
        student_attendance = []
        total_sessions = 9
        session_weeks = [1, 2, 4, 6, 8, 10, 12, 14, 16]

        for s_id in range(1, num_students + 1):
            m = np.random.choice(courses_df["code_module"])
            prev_attempts = int(np.random.choice([0, 1, 2, 3], p=[0.65, 0.20, 0.10, 0.05]))
            credits = int(np.random.choice([60, 90, 120], p=[0.6, 0.25, 0.15]))
            gender = np.random.choice(genders)

            # Latent engagement & concept mastery (4 concepts)
            base_ability = np.random.normal(0.62 - 0.12 * prev_attempts, 0.22)
            concept_mastery = np.clip(base_ability + np.random.normal(0, 0.15, size=4), 0.05, 0.98)

            # Simulate 9 class attendance sessions across the semester
            attended_count = 0
            for s_idx, w in enumerate(session_weeks):
                c_idx = s_idx % 4
                attend_prob = np.clip(0.38 + 0.60 * concept_mastery[c_idx] + np.random.normal(0, 0.08), 0.15, 0.99)
                is_present = 1 if np.random.rand() < attend_prob else 0
                attended_count += is_present
                student_attendance.append({
                    "id_student": s_id,
                    "code_module": m,
                    "session_no": s_idx + 1,
                    "week": w,
                    "concept_idx": c_idx,
                    "attended": is_present
                })

            attendance_rate = attended_count / float(total_sessions)
            absent_sessions = total_sessions - attended_count

            # Simulate assessments for this student
            mod_assessments = assessments_df[assessments_df["code_module"] == m]
            scores_list = []
            late_count = 0
            submitted_count = 0

            for _, a in mod_assessments.iterrows():
                c_idx = int(a["concept_idx"])
                mastery = concept_mastery[c_idx]
                submit_prob = np.clip(mastery + 0.25 + np.random.normal(0, 0.15), 0.1, 0.99)

                if np.random.rand() < submit_prob:
                    submitted_count += 1
                    score = float(np.clip(mastery * 85 + np.random.normal(5, 14), 10, 100))
                    delay = int(np.random.normal((1.0 - mastery) * 5 - 1, 3))
                    if delay > 0:
                        late_count += 1
                    scores_list.append(score)
                    student_assessments.append({
                        "id_assessment": a["id_assessment"],
                        "id_student": s_id,
                        "date_submitted": int(a["date"]) + delay,
                        "is_banked": 0,
                        "score": round(score, 1)
                    })

            # Simulate VLE interactions
            mod_vle = vle_df[vle_df["code_module"] == m]
            total_clicks = 0
            for _, v in mod_vle.iterrows():
                c_idx = int(v["concept_idx"])
                watch_prob = np.clip(concept_mastery[c_idx] * 0.75 + np.random.normal(0, 0.15), 0.05, 0.95)
                if np.random.rand() < watch_prob:
                    clicks = int(max(1, np.random.poisson(lam=max(1.5, concept_mastery[c_idx] * 8))))
                    total_clicks += clicks
                    student_vle.append({
                        "code_module": m,
                        "code_presentation": "2026J",
                        "id_student": s_id,
                        "id_site": v["id_site"],
                        "date": int(v["week_from"]) * 7 + np.random.randint(0, 7),
                        "sum_click": clicks
                    })

            # True outcome probability: depends on concept mastery, assignments, VLE, and Class Attendance (9 sessions, >=2 absences = <80% exam ban risk)
            avg_score = np.mean(scores_list) if scores_list else 20.0
            sub_ratio = submitted_count / max(1, len(mod_assessments))
            gateway_deficit = max(0.0, 0.62 - 0.5 * (concept_mastery[0] + concept_mastery[1]))
            attendance_deficit = max(0.0, 0.85 - attendance_rate)
            exam_ban_penalty = 0.85 if absent_sessions >= 2 else 0.0
            course_difficulty = 0.25 if m in ["CS201", "CS401"] else -0.15

            risk_logit = (
                -1.05
                + 3.2 * gateway_deficit
                + 2.4 * attendance_deficit
                + exam_ban_penalty
                + 1.4 * (0.55 - np.mean(concept_mastery))
                + 1.3 * (0.65 - sub_ratio)
                + 1.1 * ((55.0 - avg_score) / 50.0)
                + course_difficulty
                + 0.35 * prev_attempts
                + 0.25 * late_count
                + np.random.normal(0, 0.32)
            )
            risk_prob = 1.0 / (1.0 + np.exp(-risk_logit))
            is_at_risk = 1 if risk_prob > 0.52 else 0

            final_result = (
                np.random.choice(["Fail", "Withdrawn"])
                if is_at_risk
                else np.random.choice(["Pass", "Distinction"], p=[0.75, 0.25])
            )

            students.append({
                "id_student": s_id,
                "code_module": m,
                "code_presentation": "2026J",
                "gender": gender,
                "region": np.random.choice(regions),
                "highest_education": "A Level",
                "imd_band": "20-30%",
                "age_band": "0-35",
                "num_of_prev_attempts": prev_attempts,
                "studied_credits": credits,
                "disability": "N",
                "final_result": final_result
            })

            registrations.append({
                "code_module": m,
                "code_presentation": "2026J",
                "id_student": s_id,
                "date_registration": -30,
                "date_unregistration": 70 if final_result == "Withdrawn" else np.nan
            })

        pd.DataFrame(students).to_csv(os.path.join(self.raw_dir, "studentInfo.csv"), index=False)
        pd.DataFrame(registrations).to_csv(os.path.join(self.raw_dir, "studentRegistration.csv"), index=False)
        pd.DataFrame(student_assessments).to_csv(os.path.join(self.raw_dir, "studentAssessment.csv"), index=False)
        pd.DataFrame(student_vle).to_csv(os.path.join(self.raw_dir, "studentVle.csv"), index=False)
        pd.DataFrame(student_attendance).to_csv(os.path.join(self.raw_dir, "studentAttendance.csv"), index=False)

        at_risk_cnt = sum(1 for s in students if s["final_result"] in ["Fail", "Withdrawn"])
        print(f"[OK] Generated {num_students} students ({at_risk_cnt} at-risk, {at_risk_cnt/num_students:.1%}) with 15-week attendance in {self.raw_dir}")
        return True

if __name__ == "__main__":
    loader = OuladDataLoader()
    loader.generate_synthetic_oulad_sample(300, 4)
