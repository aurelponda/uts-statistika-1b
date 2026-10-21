from io import BytesIO

import pandas as pd
import pytest
import xlwt

from src.data_loader import DataLoadError, _normalize_column_names, get_excel_sheet_names, load_dataset
from src.statistics_engine import numeric_columns


def make_workbook() -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        pd.DataFrame({"Nilai": [10, 20]}).to_excel(writer, index=False, sheet_name="Kelas A")
        pd.DataFrame({"Nilai": [30, 40]}).to_excel(writer, index=False, sheet_name="Kelas B")
    return output.getvalue()


def make_legacy_xls() -> bytes:
    workbook = xlwt.Workbook()
    sheet = workbook.add_sheet("Data")
    sheet.write(0, 0, "Nilai")
    sheet.write(1, 0, 10)
    sheet.write(2, 0, 20)
    output = BytesIO()
    workbook.save(output)
    return output.getvalue()


def test_csv_load_and_column_normalization():
    frame = load_dataset(b" Nilai ,Catatan\n10,baik\n20,cukup\n", "nilai.csv")
    assert frame.columns.tolist() == ["Nilai", "Catatan"]
    assert frame["Nilai"].tolist() == [10, 20]

    duplicated = _normalize_column_names(pd.DataFrame([[1, 2, 3]], columns=["Nilai", "Nilai", "  "]))
    assert duplicated.columns.tolist() == ["Nilai", "Nilai (2)", "Kolom 3"]


def test_excel_sheet_selection():
    content = make_workbook()
    assert get_excel_sheet_names(content, "nilai.xlsx") == ["Kelas A", "Kelas B"]
    selected = load_dataset(content, "nilai.xlsx", "Kelas B")
    assert selected["Nilai"].tolist() == [30, 40]


def test_legacy_xls_loads_with_xlrd():
    frame = load_dataset(make_legacy_xls(), "nilai.xls")
    assert frame["Nilai"].tolist() == [10, 20]


@pytest.mark.parametrize(
    ("content", "filename", "message"),
    [
        (b"", "kosong.csv", "kosong"),
        (b"a,b\n1,\"belum selesai\n", "rusak.csv", "tidak dapat dibaca"),
        (b"x", "gambar.png", "tidak didukung"),
    ],
)
def test_expected_load_errors(content, filename, message):
    with pytest.raises(DataLoadError, match=message):
        load_dataset(content, filename)


def test_text_only_columns_are_not_treated_as_numeric():
    frame = load_dataset(b"nama,catatan\nA,hadir\n", "tanpa_angka.csv")
    assert numeric_columns(frame) == []


def test_invalid_sheet_is_reported():
    with pytest.raises(DataLoadError, match="tidak ditemukan"):
        load_dataset(make_workbook(), "nilai.xlsx", "Sheet yang tidak ada")
