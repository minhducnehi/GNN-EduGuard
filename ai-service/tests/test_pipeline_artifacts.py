"""Integration tests on the trained artifacts produced by `python run_pipeline.py`."""
import json
import os

import numpy as np
import pandas as pd
import pytest
import torch

from gnn.baseline import calibrate_threshold, compute_metrics, FEATURE_COLS
from gnn.build_graph import STUDENT_FEATURE_COLS, PROCESSED_DIR
from gnn.temporal_model import TemporalHGTModel, SEQ_DIM

MODELS_DIR = os.path.abspath(os.path.join(PROCESSED_DIR, "..", "..", "models"))


def _need(*names):
    for n in names:
        p = os.path.join(PROCESSED_DIR, n) if not n.endswith("_model.pt") and not n.startswith("best_") else os.path.join(MODELS_DIR, n)
        if not os.path.exists(p):
            pytest.skip(f"Artifact {n} missing - run `python run_pipeline.py` first")


@pytest.fixture(scope="module")
def graph():
    _need("graph.pt")
    return torch.load(os.path.join(PROCESSED_DIR, "graph.pt"), weights_only=False)


@pytest.fixture(scope="module")
def features_df():
    _need("student_features.csv")
    return pd.read_csv(os.path.join(PROCESSED_DIR, "student_features.csv"))


@pytest.fixture(scope="module")
def weekly_seq():
    _need("weekly_sequences.pt")
    return torch.load(os.path.join(PROCESSED_DIR, "weekly_sequences.pt"), weights_only=False)


# ---------------- Feature engineering ----------------

def test_student_features_include_active_days(graph, features_df):
    assert graph["student"].x.size(1) == len(STUDENT_FEATURE_COLS) == 8
    assert STUDENT_FEATURE_COLS == FEATURE_COLS  # tabular baselines & GNN use identical features
    assert {"active_days", "active_days_norm"} <= set(features_df.columns)
    x7 = graph["student"].x[:, 7].numpy()
    assert np.allclose(x7, features_df["active_days_norm"].values, atol=1e-4)
    assert x7.min() >= 0.0 and x7.max() <= 1.0


def test_active_days_cap_fitted_on_train(features_df):
    with open(os.path.join(PROCESSED_DIR, "feature_scaling.json"), encoding="utf-8") as f:
        cap = json.load(f)["active_days_cap"]
    train = features_df[features_df["split"] == "train"]
    assert cap == pytest.approx(max(1.0, train["active_days"].quantile(0.98)))


def test_splits_are_disjoint_and_stratified(graph):
    s = graph["student"]
    assert not (s.train_mask & s.val_mask).any()
    assert not (s.train_mask & s.test_mask).any()
    assert not (s.val_mask & s.test_mask).any()
    assert int((s.train_mask | s.val_mask | s.test_mask).sum()) == s.num_nodes
    rates = [float(s.y[m].float().mean()) for m in (s.train_mask, s.val_mask, s.test_mask)]
    assert max(rates) - min(rates) < 0.08


# ---------------- Causal / leakage-free temporal sequence ----------------

def test_weekly_sequence_shape_and_monotonic_active_days(weekly_seq, graph):
    assert weekly_seq.shape == (graph["student"].num_nodes, 16, SEQ_DIM)
    cum_days = weekly_seq[:, :, 5]
    assert torch.all(cum_days[:, 1:] >= cum_days[:, :-1] - 1e-6), "cumulative active days must be non-decreasing"


def test_week16_sequence_matches_static_feature(weekly_seq, graph):
    # At the end of the semester the causal cumulative value must equal the static node feature
    assert torch.allclose(weekly_seq[:, -1, 5], graph["student"].x[:, 7], atol=1e-3)


def test_causal_features_do_not_leak_future(weekly_seq, graph):
    _need("best_temporal_hgt.pt")
    ckpt = torch.load(os.path.join(MODELS_DIR, "best_temporal_hgt.pt"), weights_only=False)
    model = TemporalHGTModel(ckpt["in_dims"], graph.metadata(), seq_in_dim=ckpt["seq_in_dim"],
                             hidden_channels=ckpt["hidden_channels"], num_heads=ckpt["num_heads"], dropout=0.0)
    x = graph["student"].x
    early = model._build_causal_student_features(x, weekly_seq[:, :4, :], cutoff_week=4)
    assert torch.allclose(early[:, 7], weekly_seq[:, 3, 5])
    assert float(early[:, 7].mean()) < float(x[:, 7].mean())  # less activity observed by week 4
    assert torch.equal(early[:, :2], x[:, :2])                 # start-of-semester features untouched


# ---------------- Baselines / metrics ----------------

def test_calibrate_threshold_and_auc_uses_probabilities():
    y = np.array([0, 0, 0, 1, 1, 1])
    p = np.array([0.1, 0.2, 0.45, 0.4, 0.8, 0.9])
    t = calibrate_threshold(y, p)
    assert 0.30 <= t <= 0.70
    m = compute_metrics(y, p, t)
    # AUC from probabilities (8/9), not from hard labels
    assert m["auc_roc"] == pytest.approx(8 / 9, abs=1e-4)


def test_benchmark_and_importance_artifacts():
    _need("benchmark_summary.json", "feature_importance.json", "baseline_best_params.json",
          "early_warning_metrics.json", "ablation_metrics.json", "data_quality_report.json")
    with open(os.path.join(PROCESSED_DIR, "benchmark_summary.json"), encoding="utf-8") as f:
        bench = json.load(f)
    for k in ["Logistic Regression", "Random Forest", "Gradient Boosting", "HGT (HeteroGNN)", "HGT + LSTM (Temporal)"]:
        assert k in bench
        for metric in ["f1_macro", "recall_risk", "auc_roc"]:
            assert 0.0 <= bench[k][metric] <= 1.0
    assert "cv_auc" in bench["Random Forest"]

    with open(os.path.join(PROCESSED_DIR, "feature_importance.json"), encoding="utf-8") as f:
        fi = json.load(f)
    keys = [it["feature_key"] for it in fi["features"]]
    assert sorted(keys) == sorted(FEATURE_COLS)
    perms = [it["permutation_importance"] for it in fi["features"]]
    assert perms == sorted(perms, reverse=True)

    with open(os.path.join(PROCESSED_DIR, "baseline_best_params.json"), encoding="utf-8") as f:
        params = json.load(f)
    assert {"n_estimators", "max_depth"} <= set(params["Random Forest"])
