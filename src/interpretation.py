"""Cautious, rule-based Indonesian descriptions of summary statistics."""

from __future__ import annotations

from typing import Any


def format_number(value: Any, decimals: int = 4) -> str:
    """Format numeric values for Indonesian display without rounding stored values."""
    if value is None:
        return "—"
    number = float(value)
    if number.is_integer():
        return f"{int(number):,}".replace(",", ".")
    rendered = f"{number:,.{decimals}f}".rstrip("0").rstrip(".")
    return rendered.replace(",", "\0").replace(".", ",").replace("\0", ".")


def format_result(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, (list, tuple)):
        return ", ".join(format_number(item) for item in value) if value else "—"
    return format_number(value)


def interpret_column(column_name: str, stats: dict[str, Any]) -> list[str]:
    """Explain center and spread without making causal or inferential claims."""
    if stats["n"] == 0:
        return [f"{column_name}: tidak ada observasi numerik valid untuk ditafsirkan."]

    mean = stats["mean"]
    median = stats["median"]
    lines = [
        f"{column_name}: rata-rata {format_number(mean)} dan median {format_number(median)} "
        "merangkum pusat data dengan dua cara yang berbeda."
    ]
    if mean > median:
        lines.append("Rata-rata yang lebih tinggi dapat mengindikasikan beberapa nilai tinggi; periksa histogram atau boxplot untuk konteks.")
    elif mean < median:
        lines.append("Rata-rata yang lebih rendah dapat mengindikasikan beberapa nilai rendah; periksa histogram atau boxplot untuk konteks.")
    else:
        lines.append("Rata-rata dan median sama pada ketelitian perhitungan, tetapi bentuk distribusi tetap perlu diperiksa melalui grafik.")

    if stats["std_dev"] is not None:
        lines.append(
            f"Simpangan baku sampel {format_number(stats['std_dev'])} menggambarkan sebaran data "
            "dalam satuan yang sama dengan variabel."
        )
    if stats["missing_count"] or stats["non_finite_count"]:
        details = []
        if stats["missing_count"]:
            details.append(f"{stats['missing_count']} nilai kosong")
        if stats["non_finite_count"]:
            details.append(f"{stats['non_finite_count']} nilai tidak hingga")
        lines.append("Perhitungan mengecualikan " + " dan ".join(details) + ".")
    return lines
