"""
End-to-end training pipeline for GNN-EduGuard (inspired by OULAD `run_pipeline.py`).

Stages:
  1. Data generation / ETL + data quality profiling      -> data_quality_report.json
  2. Heterogeneous graph construction (+ train-only caps) -> graph.pt, student_features.csv
  3. Tabular baselines (GridSearchCV) + feature importance -> baseline_metrics.json, feature_importance.json
  4. Static HGT training                                   -> best_hgt_model.pt, benchmark_summary.json
  5. Causal Temporal HGT + LSTM (early warning)            -> best_temporal_hgt.pt, early_warning_metrics.json
  6. Ablation study                                        -> ablation_metrics.json

Usage (from ai-service/):  python run_pipeline.py [--epochs 120] [--temporal-epochs 100]
"""
import argparse
import logging
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

_LOG = logging.getLogger("pipeline")


def _stage(name, fn, *args, **kwargs):
    _LOG.info("▶ %s ...", name)
    t0 = time.perf_counter()
    out = fn(*args, **kwargs)
    _LOG.info("✔ %s done in %.1fs\n", name, time.perf_counter() - t0)
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description="GNN-EduGuard training pipeline")
    parser.add_argument("--epochs", type=int, default=120, help="Static HGT epochs")
    parser.add_argument("--temporal-epochs", type=int, default=100, help="Temporal HGT epochs")
    parser.add_argument("--generate-synthetic", action="store_true", help="Explicitly replace raw CSVs with synthetic sample data")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    from gnn.data_loader import OuladDataLoader
    from gnn.data_quality import run_data_quality
    from gnn.train import train_hgt_model
    from gnn.temporal_model import train_and_evaluate_temporal
    from gnn.ablation_study import run_ablation_study

    start = time.perf_counter()
    raw_dir = Path(__file__).resolve().parent / "gnn" / "data" / "raw"
    required = {"courses.csv", "vle.csv", "assessments.csv", "studentInfo.csv", "studentRegistration.csv", "studentAssessment.csv", "studentVle.csv", "studentAttendance.csv"}
    if args.generate_synthetic:
        _stage("1. Generate OULAD-schema data", OuladDataLoader().generate_synthetic_oulad_sample, 300, 4)
    else:
        missing = sorted(name for name in required if not (raw_dir / name).is_file())
        if missing:
            parser.error(f"Missing raw data: {', '.join(missing)}. Supply CSVs or use --generate-synthetic.")
        _LOG.info("Using existing raw CSVs in %s", raw_dir)
    _stage("2. Data quality profiling", run_data_quality)
    # train_hgt_model builds the graph (stage 2b) and runs tuned baselines (stage 3) before HGT training
    _stage("3-4. Graph build + baselines + static HGT", train_hgt_model, epochs=args.epochs)
    _stage("5. Causal Temporal HGT (early warning)", train_and_evaluate_temporal, epochs=args.temporal_epochs)
    _stage("6. Ablation study", run_ablation_study)
    _LOG.info("Pipeline complete in %.1fs", time.perf_counter() - start)


if __name__ == "__main__":
    main()
