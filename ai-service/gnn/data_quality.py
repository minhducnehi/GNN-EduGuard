"""
Data Quality & ETL Profiling for OULAD-schema raw tables.

Inspired by the OULAD analysis pipeline (ElizabethSeidle/OULAD: `raw_data_eda` + `basic_clean`),
but adapted to be leakage-free for supervised GNN training:
  1. Profile every raw table (rows, cols, missing rows, duplicate rows, column names).
  2. Clean tables: drop all-null columns, drop exact duplicate rows, drop rows missing key IDs.
  3. Right-skewed count features are capped at the 98th percentile, where the percentile is
     FITTED ON THE TRAIN SPLIT ONLY and then applied to val/test (the reference repo fitted on
     the full dataset, which leaks test statistics).
"""
import os
import json
from typing import Dict, Iterable, Optional

import numpy as np
import pandas as pd

RAW_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "data", "raw"))
PROCESSED_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "data", "processed"))

# Columns that must never be null, per table (rows violating this are dropped)
KEY_COLUMNS = {
    "studentInfo": ["id_student", "code_module", "final_result"],
    "studentAssessment": ["id_assessment", "id_student"],
    "studentVle": ["id_student", "id_site", "date", "sum_click"],
    "studentAttendance": ["id_student", "session_no", "attended"],
    "assessments": ["id_assessment", "code_module"],
    "vle": ["id_site", "code_module"],
    "courses": ["code_module"],
}

OUTLIER_QUANTILE = 0.98


def read_raw_tables(raw_dir: str = RAW_DIR) -> Dict[str, pd.DataFrame]:
    """Read every *.csv file in raw_dir into a {table_name: DataFrame} dict."""
    tables = {}
    if not os.path.isdir(raw_dir):
        return tables
    for fname in sorted(os.listdir(raw_dir)):
        if fname.lower().endswith(".csv"):
            tables[os.path.splitext(fname)[0]] = pd.read_csv(os.path.join(raw_dir, fname))
    return tables


def profile_tables(tables: Dict[str, pd.DataFrame]) -> list:
    """Return a per-table summary (shape, missing rows, duplicate rows, column names)."""
    summary = []
    for name, df in tables.items():
        summary.append({
            "table": name,
            "rows": int(df.shape[0]),
            "cols": int(df.shape[1]),
            "missing_rows": int(df.isnull().any(axis=1).sum()),
            "missing_cells": int(df.isnull().sum().sum()),
            "duplicate_rows": int(df.duplicated().sum()),
            "all_null_columns": [c for c in df.columns if df[c].isnull().all()],
            "columns": list(map(str, df.columns)),
        })
    return summary


def clean_table(name: str, df: pd.DataFrame) -> pd.DataFrame:
    """Drop all-null columns, rows with missing key columns, and exact duplicate rows."""
    out = df.copy()
    all_null = [c for c in out.columns if out[c].isnull().all()]
    # Never drop key columns even if (unexpectedly) all-null; those rows get dropped below instead
    all_null = [c for c in all_null if c not in KEY_COLUMNS.get(name, [])]
    if all_null:
        out = out.drop(columns=all_null)
    keys = [k for k in KEY_COLUMNS.get(name, []) if k in out.columns]
    if keys:
        out = out.dropna(subset=keys)
    out = out.drop_duplicates().reset_index(drop=True)
    return out


def clean_tables(tables: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    return {name: clean_table(name, df) for name, df in tables.items()}


def fit_outlier_caps(df: pd.DataFrame, columns: Iterable[str], fit_mask: Optional[np.ndarray] = None,
                     quantile: float = OUTLIER_QUANTILE) -> Dict[str, float]:
    """Compute upper caps (quantile) for each column using only rows in fit_mask (e.g. train split)."""
    fit_df = df if fit_mask is None else df.loc[np.asarray(fit_mask, dtype=bool)]
    caps = {}
    for col in columns:
        if col in fit_df.columns and len(fit_df) > 0:
            cap = float(fit_df[col].quantile(quantile))
            caps[col] = cap if cap > 0 else float(max(1.0, fit_df[col].max()))
    return caps


def apply_outlier_caps(df: pd.DataFrame, caps: Dict[str, float]) -> pd.DataFrame:
    out = df.copy()
    for col, cap in caps.items():
        if col in out.columns:
            out[col] = out[col].clip(upper=cap)
    return out


def run_data_quality(raw_dir: str = RAW_DIR, output_dir: str = PROCESSED_DIR, save: bool = True) -> dict:
    """Profile raw tables before/after cleaning and persist a JSON report."""
    raw = read_raw_tables(raw_dir)
    cleaned = clean_tables(raw)
    before = profile_tables(raw)
    after = profile_tables(cleaned)
    report = {
        "raw_dir": raw_dir,
        "tables_before_cleaning": before,
        "tables_after_cleaning": after,
        "rows_removed": {
            b["table"]: b["rows"] - a["rows"] for b, a in zip(before, after)
        },
        "outlier_policy": f"Right-skewed count features capped at P{int(OUTLIER_QUANTILE * 100)} fitted on TRAIN split only",
    }
    if save:
        os.makedirs(output_dir, exist_ok=True)
        with open(os.path.join(output_dir, "data_quality_report.json"), "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"{'Table':<20} | {'Rows':>7} | {'Cols':>4} | {'Missing rows':>12} | {'Duplicates':>10}")
    print("-" * 66)
    for t in before:
        print(f"{t['table']:<20} | {t['rows']:>7} | {t['cols']:>4} | {t['missing_rows']:>12} | {t['duplicate_rows']:>10}")
    return report


if __name__ == "__main__":
    run_data_quality()
