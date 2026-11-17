"""Guards against misleading results and accidental raw-data replacement."""
import pytest

from gnn.predictor import StudentRiskPredictor
import run_pipeline
from evaluate_recognition import metrics
import numpy as np
from gnn.build_graph import build_heterogeneous_graph


def test_missing_model_never_returns_a_fabricated_risk(monkeypatch):
    predictor = StudentRiskPredictor.__new__(StudentRiskPredictor)
    predictor.model = None
    predictor.graph_data = None
    predictor.student_df = None
    monkeypatch.setattr(predictor, "_load_artifacts", lambda: None)
    with pytest.raises(RuntimeError, match="artifacts are unavailable"):
        predictor.predict_risk(1)


def test_pipeline_help_documents_explicit_synthetic_generation(capsys):
    with pytest.raises(SystemExit) as result:
        run_pipeline.main(["--help"])
    assert result.value.code == 0
    assert "--generate-synthetic" in capsys.readouterr().out


def test_recognition_metrics_handle_single_class_subgroup():
    result = metrics(np.array([1, 1]), np.array([0.8, 0.2]), 0.5)
    assert result["recall"] == 0.5
    assert result["roc_auc"] is None


def test_graph_builder_does_not_generate_data_in_empty_directory(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    with pytest.raises(FileNotFoundError, match="Missing raw CSVs"):
        build_heterogeneous_graph(raw_dir=str(raw), output_dir=str(tmp_path / "processed"), force_regen=True)
    assert list(raw.iterdir()) == []
