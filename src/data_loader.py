"""Upload parsing and basic validation for CSV and Excel files."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pandas as pd

ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}


class DataLoadError(ValueError):
    """An expected, user-correctable upload or parsing error."""


def _check_extension(filename: str) -> str:
    extension = Path(filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise DataLoadError("Format file tidak didukung. Gunakan .xlsx, .xls, atau .csv.")
    return extension


def _excel_file(content: bytes, extension: str) -> pd.ExcelFile:
    try:
        return pd.ExcelFile(BytesIO(content))
    except ImportError as exc:
        if extension == ".xls":
            raise DataLoadError("Untuk membaca file .xls, pastikan paket xlrd tersedia.") from exc
        raise DataLoadError("Paket pembaca Excel belum tersedia.") from exc
    except Exception as exc:
        raise DataLoadError("File Excel tidak dapat dibaca. Periksa file lalu coba lagi.") from exc


def get_excel_sheet_names(content: bytes, filename: str) -> list[str]:
    """Return worksheet names for a valid Excel upload."""
    extension = _check_extension(filename)
    if extension == ".csv":
        return []
    if not content:
        raise DataLoadError("File kosong. Pilih file yang berisi data.")
    with _excel_file(content, extension) as workbook:
        if not workbook.sheet_names:
            raise DataLoadError("Workbook tidak memiliki lembar kerja.")
        return list(workbook.sheet_names)


def _normalize_column_names(frame: pd.DataFrame) -> pd.DataFrame:
    """Strip labels, fill blank headers, and make duplicate headers unique."""
    normalized: list[str] = []
    used: set[str] = set()
    counts: dict[str, int] = {}

    for index, raw_name in enumerate(frame.columns, start=1):
        base = str(raw_name).strip() or f"Kolom {index}"
        candidate = base
        number = counts.get(base, 1)
        while candidate in used:
            number += 1
            candidate = f"{base} ({number})"
        counts[base] = number
        used.add(candidate)
        normalized.append(candidate)

    result = frame.copy()
    result.columns = normalized
    return result


def _read_csv(content: bytes) -> pd.DataFrame:
    last_decode_error: UnicodeDecodeError | None = None
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return pd.read_csv(BytesIO(content), encoding=encoding, engine="python", on_bad_lines="error")
        except UnicodeDecodeError as exc:
            last_decode_error = exc
        except pd.errors.EmptyDataError as exc:
            raise DataLoadError("CSV kosong atau tidak memiliki header.") from exc
        except (pd.errors.ParserError, ValueError) as exc:
            raise DataLoadError("CSV tidak dapat dibaca. Periksa pemisah dan isi file.") from exc
    raise DataLoadError("Encoding CSV tidak dikenali. Simpan file sebagai UTF-8 lalu coba lagi.") from last_decode_error


def load_dataset(content: bytes, filename: str, sheet_name: str | None = None) -> pd.DataFrame:
    """Load a CSV/XLSX/XLS byte payload into a normalized DataFrame."""
    extension = _check_extension(filename)
    if not content or not content.strip():
        raise DataLoadError("File kosong. Pilih file yang berisi data.")

    try:
        if extension == ".csv":
            frame = _read_csv(content)
        else:
            with _excel_file(content, extension) as workbook:
                selected_sheet = sheet_name or workbook.sheet_names[0]
                if selected_sheet not in workbook.sheet_names:
                    raise DataLoadError("Lembar kerja yang dipilih tidak ditemukan di file.")
                frame = workbook.parse(sheet_name=selected_sheet)
    except DataLoadError:
        raise
    except Exception as exc:
        raise DataLoadError("File tidak dapat dibaca. Periksa format dan isi file.") from exc

    if frame.shape[1] == 0:
        raise DataLoadError("File tidak memiliki kolom data.")
    if frame.empty:
        raise DataLoadError("File tidak memiliki baris data di luar header.")
    return _normalize_column_names(frame)
