"""CSV and Excel export helpers for the unrounded summary table."""

from __future__ import annotations

from io import BytesIO
from typing import Any

import pandas as pd


def _excel_safe(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (list, tuple)):
        return "; ".join(str(item) for item in value)
    return value


def export_frame(summary: pd.DataFrame) -> pd.DataFrame:
    """Convert mode lists to a portable text cell while preserving numeric cells."""
    return summary.map(_excel_safe)


def csv_bytes(summary: pd.DataFrame) -> bytes:
    return export_frame(summary).to_csv(index=False).encode("utf-8-sig")


def excel_bytes(summary: pd.DataFrame) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        export_frame(summary).to_excel(writer, index=False, sheet_name="Ringkasan")
        conventions = pd.DataFrame(
            {
                "Konvensi": [
                    "N menghitung observasi numerik valid.",
                    "Varians dan simpangan baku menggunakan rumus sampel (ddof=1).",
                    "Q1, Q2, dan Q3 menggunakan kuantil linear; Q2 sama dengan median.",
                    "Nilai kosong dan nilai tidak hingga dikecualikan dari perhitungan.",
                    "Sel angka menyimpan nilai penuh; pembulatan hanya diterapkan pada tampilan aplikasi.",
                ]
            }
        )
        conventions.to_excel(writer, index=False, sheet_name="Konvensi")
    return output.getvalue()
