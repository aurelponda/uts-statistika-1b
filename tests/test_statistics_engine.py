import numpy as np
import pandas as pd
import pytest

from src.statistics_engine import build_summary_frame, describe_series, numeric_columns


def test_known_ordinary_values_and_linear_quartiles():
    stats = describe_series(pd.Series([10, 20, 30, 40, 50], dtype="int64"))

    assert stats["n"] == 5
    assert stats["minimum"] == 10
    assert stats["maximum"] == 50
    assert stats["mean"] == 30
    assert stats["median"] == 30
    assert stats["q1"] == 20
    assert stats["q2"] == stats["median"] == 30
    assert stats["q3"] == 40
    assert stats["variance"] == 250
    assert stats["std_dev"] == pytest.approx(np.sqrt(250))


def test_all_tied_modes_are_returned():
    stats = describe_series(pd.Series([1, 2, 2, 3, 3], dtype="int64"))
    assert stats["mode"] == [2.0, 3.0]


def test_missing_values_are_excluded_and_reported():
    stats = describe_series(pd.Series([10, 20, None, 40, 50], dtype="float64"))
    assert stats["n"] == 4
    assert stats["missing_count"] == 1
    assert stats["mean"] == 30
    assert stats["variance"] == pytest.approx(1000 / 3)
    assert stats["q1"] == 17.5
    assert stats["q2"] == 30
    assert stats["q3"] == 42.5


def test_non_finite_values_are_excluded_and_reported():
    stats = describe_series(pd.Series([1.0, 2.0, np.inf, -np.inf, np.nan]))
    assert stats["n"] == 2
    assert stats["missing_count"] == 1
    assert stats["non_finite_count"] == 2
    assert stats["mean"] == 1.5


def test_constant_values_and_one_observation():
    constant = describe_series(pd.Series([5, 5, 5, 5], dtype="int64"))
    assert constant["mean"] == constant["median"] == constant["mode"][0] == 5
    assert constant["variance"] == constant["std_dev"] == 0

    single = describe_series(pd.Series([5], dtype="int64"))
    assert single["n"] == 1
    assert single["variance"] is None
    assert single["std_dev"] is None


def test_multiple_variables_and_selection_order():
    frame = pd.DataFrame({"Nilai A": [10, 20, 30], "Nilai B": [2, 4, 8], "Catatan": ["a", "b", "c"]})
    assert numeric_columns(frame) == ["Nilai A", "Nilai B"]

    summary, diagnostics = build_summary_frame(frame, ["Nilai A", "Nilai B"], ["mean", "n"])
    assert summary.columns.tolist() == ["Statistik", "Nilai A", "Nilai B"]
    assert summary["Nilai A"].tolist() == [20.0, 3]
    assert summary["Nilai B"].tolist() == [14 / 3, 3]
    assert diagnostics["Nilai B"]["n"] == 3


def test_empty_valid_series_returns_empty_statistics():
    stats = describe_series(pd.Series([None, np.nan], dtype="float64"))
    assert stats["n"] == 0
    assert stats["mean"] is None
    assert stats["mode"] == []
