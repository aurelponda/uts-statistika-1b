from io import BytesIO

import pandas as pd

from src.exporters import csv_bytes, excel_bytes


def test_csv_and_excel_exports_preserve_numeric_values_and_modes():
    summary = pd.DataFrame(
        {
            "Statistik": ["Rata-rata", "Modus"],
            "Nilai": [2.5, [2.0, 3.0]],
        }
    )

    csv_text = csv_bytes(summary).decode("utf-8-sig")
    assert "2.5" in csv_text
    assert "2.0; 3.0" in csv_text

    workbook = pd.read_excel(BytesIO(excel_bytes(summary)), sheet_name="Ringkasan")
    assert workbook.loc[0, "Nilai"] == 2.5
    assert workbook.loc[1, "Nilai"] == "2.0; 3.0"
