"""Pure descriptive-statistics calculations used by the UI and tests."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np
import pandas as pd
from pandas.api.types import is_bool_dtype, is_numeric_dtype

STATISTIC_LABELS: dict[str, str] = {
    "n": "N valid",
    "minimum": "Minimum",
    "maximum": "Maksimum",
    "mean": "Rata-rata",
    "median": "Median",
    "mode": "Modus",
    "variance": "Varians sampel",
    "std_dev": "Simpangan baku sampel",
    "q1": "Q1 (25%)",
    "q2": "Q2 (50%)",
    "q3": "Q3 (75%)",
}
STATISTIC_KEYS: tuple[str, ...] = tuple(STATISTIC_LABELS)


def numeric_columns(frame: pd.DataFrame) -> list[str]:
    """Return numeric columns, excluding booleans and text-like columns."""
    return [
        str(column)
        for column in frame.columns
        if is_numeric_dtype(frame[column].dtype) and not is_bool_dtype(frame[column].dtype)
    ]


def finite_numeric_values(series: pd.Series) -> np.ndarray:
    """Return finite observations from a numeric series without coercing text."""
    if not is_numeric_dtype(series.dtype) or is_bool_dtype(series.dtype):
        raise TypeError("Kolom harus bertipe numerik.")
    values = series.dropna().to_numpy(dtype=np.float64, copy=True)
    return values[np.isfinite(values)]


def describe_series(series: pd.Series) -> dict[str, Any]:
    """Calculate descriptive statistics using the documented STATWISE conventions.

    Missing and non-finite observations are excluded. Variance and standard
    deviation use the sample convention (ddof=1). Quartiles use linear
    interpolation; Q2 is assigned from the median so the two values match.
    """
    if not is_numeric_dtype(series.dtype) or is_bool_dtype(series.dtype):
        raise TypeError("Kolom harus bertipe numerik.")

    not_missing = series.dropna().to_numpy(dtype=np.float64, copy=True)
    finite_mask = np.isfinite(not_missing)
    values = not_missing[finite_mask]
    n = int(values.size)
    missing_count = int(series.isna().sum())
    non_finite_count = int((~finite_mask).sum())

    result: dict[str, Any] = {
        "n": n,
        "minimum": None,
        "maximum": None,
        "mean": None,
        "median": None,
        "mode": [],
        "variance": None,
        "std_dev": None,
        "q1": None,
        "q2": None,
        "q3": None,
        "missing_count": missing_count,
        "non_finite_count": non_finite_count,
    }
    if n == 0:
        return result

    modes = pd.Series(values).mode(dropna=True).to_list()
    median = float(np.quantile(values, 0.5, method="linear"))
    q1, _q2, q3 = np.quantile(values, [0.25, 0.5, 0.75], method="linear")

    result.update(
        minimum=float(np.min(values)),
        maximum=float(np.max(values)),
        mean=float(np.mean(values)),
        median=median,
        mode=[float(value) for value in modes],
        variance=float(np.var(values, ddof=1)) if n >= 2 else None,
        std_dev=float(np.std(values, ddof=1)) if n >= 2 else None,
        q1=float(q1),
        q2=median,
        q3=float(q3),
    )
    return result


def build_summary_frame(
    frame: pd.DataFrame,
    columns: Sequence[str],
    selected_statistics: Sequence[str],
) -> tuple[pd.DataFrame, dict[str, dict[str, Any]]]:
    """Build an unrounded summary table and per-column diagnostics."""
    unknown_columns = [column for column in columns if column not in frame.columns]
    if unknown_columns:
        raise ValueError(f"Variabel tidak ditemukan: {', '.join(unknown_columns)}")

    unknown_statistics = [key for key in selected_statistics if key not in STATISTIC_LABELS]
    if unknown_statistics:
        raise ValueError(f"Statistik tidak dikenal: {', '.join(unknown_statistics)}")

    statistics_by_column = {column: describe_series(frame[column]) for column in columns}
    rows: list[dict[str, Any]] = []
    for key in selected_statistics:
        row: dict[str, Any] = {"Statistik": STATISTIC_LABELS[key]}
        for column in columns:
            row[column] = statistics_by_column[column][key]
        rows.append(row)
    return pd.DataFrame(rows, columns=["Statistik", *columns]), statistics_by_column
