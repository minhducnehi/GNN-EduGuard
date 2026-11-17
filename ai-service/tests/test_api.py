"""API smoke tests (FastAPI TestClient, lifespan/watcher not started)."""
import pytest
from fastapi.testclient import TestClient

import main

client = TestClient(main.app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "online"


def test_feature_importance_endpoint():
    r = client.get("/api/models/feature-importance")
    assert r.status_code == 200
    body = r.json()
    assert "features" in body and len(body["features"]) == 8


def test_data_quality_endpoint():
    r = client.get("/api/data/quality")
    assert r.status_code == 200
    tables = {t["table"] for t in r.json()["tables_before_cleaning"]}
    assert {"studentInfo", "studentVle", "studentAssessment", "studentAttendance"} <= tables


def test_benchmark_endpoints():
    for path in ["/api/models/benchmark", "/api/models/early-warning", "/api/models/ablation"]:
        r = client.get(path)
        assert r.status_code == 200 and r.json(), path


@pytest.mark.parametrize("student_id", [1, 2, 150, 300])
def test_predict_risk_contract(student_id):
    r = client.get(f"/api/predict/risk/{student_id}?refresh=true")
    assert r.status_code == 200
    body = r.json()
    assert body["model_used"].startswith("StudentRiskHGT")
    assert 0.0 <= body["risk_score"] <= 1.0
    assert body["risk_level"] in {"High", "Medium", "Low"}
    assert "vle_active_days" in body
    keys = {a["feature_key"] for a in body["feature_attributions"]}
    assert "active_days_norm" in keys and len(keys) == 8
    assert [t["week"] for t in body["early_warning_trajectory"]] == [2, 4, 8, 12, 16]


def test_attendance_update_changes_risk():
    good = client.post("/api/predict/attendance/5", json={"attended_sessions": 9, "total_sessions": 9}).json()
    bad = client.post("/api/predict/attendance/5", json={"attended_sessions": 4, "total_sessions": 9}).json()
    assert bad["absent_sessions"] == 5
    assert bad["risk_score"] > good["risk_score"]


def test_attendance_validation():
    r = client.post("/api/predict/attendance/5", json={"attended_sessions": -1, "total_sessions": 9})
    assert r.status_code == 422


@pytest.mark.parametrize("path", ["/api/predict/risk/999999", "/api/explain/999999"])
def test_unknown_student_is_not_mapped_to_another_student(path):
    assert client.get(path).status_code == 404
