import numpy as np
import pandas as pd
import pytest

from gnn.data_quality import (
    clean_table, profile_tables, fit_outlier_caps, apply_outlier_caps, run_data_quality,
)


def test_clean_table_drops_null_columns_missing_keys_and_duplicates():
    df = pd.DataFrame({
        "id_student": [1, 1, 2, None],
        "id_site": [10, 10, 11, 12],
        "date": [1, 1, 2, 3],
        "sum_click": [5, 5, 3, 1],
        "empty": [None, None, None, None],
    })
    out = clean_table("studentVle", df)
    assert "empty" not in out.columns          # all-null column dropped
    assert out["id_student"].notna().all()     # row with missing key dropped
    assert len(out) == 2                       # exact duplicate dropped


def test_clean_table_keeps_key_column_even_if_all_null():
    df = pd.DataFrame({"code_module": [None, None], "x": [1, 2]})
    out = clean_table("courses", df)
    assert "code_module" in out.columns
    assert len(out) == 0


def test_profile_tables_counts():
    df = pd.DataFrame({"a": [1, 1, None], "b": [2, 2, 3]})
    prof = profile_tables({"t": df})[0]
    assert prof["rows"] == 3 and prof["cols"] == 2
    assert prof["missing_rows"] == 1
    assert prof["duplicate_rows"] == 1


def test_outlier_caps_fitted_on_train_only():
    df = pd.DataFrame({"v": list(range(1, 101)) + [10_000]})
    train_mask = np.array([True] * 100 + [False])  # the extreme value is in test only
    caps = fit_outlier_caps(df, ["v"], fit_mask=train_mask, quantile=0.98)
    assert caps["v"] == pytest.approx(np.quantile(np.arange(1, 101), 0.98))
    capped = apply_outlier_caps(df, caps)
    assert capped["v"].max() == pytest.approx(caps["v"])
    assert df["v"].max() == 10_000  # original untouched


def test_run_data_quality_on_temp_dir(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    pd.DataFrame({"id_student": [1, 1], "code_module": ["A", "A"], "final_result": ["Pass", "Pass"]}) \
        .to_csv(raw / "studentInfo.csv", index=False)
    report = run_data_quality(str(raw), str(tmp_path / "out"), save=True)
    assert report["rows_removed"]["studentInfo"] == 1
    assert (tmp_path / "out" / "data_quality_report.json").exists()
