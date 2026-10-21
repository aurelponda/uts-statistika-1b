"""STATWISE: an interactive descriptive-statistics app for UTS Statistika 1B."""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from src.data_loader import DataLoadError, get_excel_sheet_names, load_dataset
from src.exporters import csv_bytes, excel_bytes
from src.interpretation import format_result, interpret_column
from src.statistics_engine import (
    STATISTIC_KEYS,
    STATISTIC_LABELS,
    build_summary_frame,
    finite_numeric_values,
    numeric_columns,
)

MAX_UPLOAD_BYTES = 20 * 1024 * 1024
PREVIEW_ROWS = 100
DEFAULT_STATISTICS = list(STATISTIC_KEYS)


def _set_selection(key: str, values: list[str]) -> None:
    st.session_state[key] = list(values)


def _dataset_key(content: bytes, filename: str, sheet_name: str | None) -> str:
    digest = hashlib.sha256(content).hexdigest()[:12]
    return f"{digest}_{Path(filename).suffix.lower().lstrip('.')}_{sheet_name or 'csv'}"


def _frequency_frame(values: np.ndarray) -> pd.DataFrame:
    counts = pd.Series(values).value_counts(dropna=True).sort_index()
    total = int(counts.sum())
    return pd.DataFrame(
        {
            "Nilai": [format_result(value) for value in counts.index.tolist()],
            "Frekuensi": counts.to_numpy(dtype=int),
            "Persentase": [float(count / total * 100) for count in counts.to_numpy()],
        }
    )


def _show_visualization(frame: pd.DataFrame, selected_variables: list[str], dataset_id: str) -> None:
    st.subheader("Visualisasi")
    if not selected_variables:
        st.info("Pilih setidaknya satu variabel untuk melihat grafik.")
        return

    variable_key = f"chart_variable_{dataset_id}"
    chart_key = f"chart_type_{dataset_id}"
    if st.session_state.get(variable_key) not in selected_variables:
        st.session_state[variable_key] = selected_variables[0]
    variable = st.selectbox("Variabel grafik", selected_variables, key=variable_key)
    values = finite_numeric_values(frame[variable])
    if values.size == 0:
        st.info("Tidak ada observasi numerik valid untuk digambarkan.")
        return

    unique_count = int(np.unique(values).size)
    chart_options = ["Histogram", "Boxplot"]
    if unique_count <= 30:
        chart_options.append("Frekuensi (batang)")
    if unique_count <= 8:
        chart_options.append("Proporsi (lingkaran)")

    selected_chart = st.selectbox("Jenis grafik", chart_options, key=chart_key)
    if selected_chart == "Histogram":
        bins = st.slider("Jumlah kelompok", min_value=5, max_value=50, value=20, key=f"bins_{dataset_id}")
        figure = px.histogram(
            x=values,
            nbins=bins,
            labels={"x": variable, "y": "Frekuensi"},
            title=f"Distribusi {variable}",
            color_discrete_sequence=["#c49a2c"],
        )
        figure.update_layout(bargap=0.08)
    elif selected_chart == "Boxplot":
        figure = px.box(
            y=values,
            labels={"y": variable},
            title=f"Boxplot {variable}",
            color_discrete_sequence=["#c49a2c"],
        )
    else:
        frequencies = pd.Series(values).value_counts().sort_index().rename_axis("Nilai").reset_index(name="Frekuensi")
        frequencies["Label"] = frequencies["Nilai"].map(format_result)
        if selected_chart == "Frekuensi (batang)":
            figure = px.bar(
                frequencies,
                x="Label",
                y="Frekuensi",
                text="Frekuensi",
                title=f"Frekuensi {variable}",
                labels={"Label": variable},
                color_discrete_sequence=["#c49a2c"],
            )
            figure.update_traces(textposition="outside")
        else:
            figure = px.pie(
                frequencies,
                names="Label",
                values="Frekuensi",
                title=f"Proporsi {variable}",
                color_discrete_sequence=px.colors.sequential.YlOrBr,
            )
        st.caption("Grafik frekuensi ditampilkan karena jumlah nilai unik variabel relatif sedikit.")
        st.dataframe(_frequency_frame(values), hide_index=True, use_container_width=True)

    figure.update_layout(
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(l=12, r=12, t=52, b=12),
    )
    st.plotly_chart(figure, use_container_width=True)


def main() -> None:
    st.set_page_config(
        page_title="STATWISE | Statistika Deskriptif",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    st.markdown(
        """
        <style>
        :root { --gold: #c49a2c; --ink: #302b22; --cream: #fffaf0; }
        [data-testid="stAppViewContainer"] { background: #fffdf8; color: var(--ink); }
        [data-testid="stHeader"] { background: rgba(255, 253, 248, 0.92); }
        [data-testid="stMetric"] { background: white; border: 1px solid #eee3c8; border-radius: 12px; padding: 0.8rem; }
        h1, h2, h3 { color: var(--ink); }
        .stButton > button, .stDownloadButton > button { border-color: var(--gold); }
        .stButton > button[kind="primary"] { background: var(--gold); border-color: var(--gold); color: white; }
        @media (max-width: 700px) { [data-testid="stMetric"] { padding: 0.55rem; } }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("STATWISE")
    st.caption("Analisis statistik deskriptif yang sederhana, jelas, dan interaktif.")
    st.markdown("Unggah data, pilih variabel numerik, lalu tinjau ringkasan, grafik, dan hasil yang dapat diunduh.")

    uploaded_file = st.file_uploader(
        "Pilih file data",
        type=["xlsx", "xls", "csv"],
        help="Format yang didukung: .xlsx, .xls, dan .csv. Ukuran maksimum 20 MB.",
    )
    if uploaded_file is None:
        st.info("Mulai dengan mengunggah file Excel atau CSV. Data yang diunggah tidak disimpan oleh aplikasi.")
        st.markdown(
            "**Alur analisis:** pratinjau data → pilih variabel → pilih statistik → tinjau grafik dan unduh ringkasan."
        )
        return

    content = uploaded_file.getvalue()
    if len(content) > MAX_UPLOAD_BYTES:
        st.error("Ukuran file melebihi batas 20 MB. Kecilkan file lalu unggah kembali.")
        return

    extension = Path(uploaded_file.name).suffix.lower()
    sheet_names: list[str] = []
    selected_sheet: str | None = None
    if extension in {".xlsx", ".xls"}:
        try:
            sheet_names = get_excel_sheet_names(content, uploaded_file.name)
        except DataLoadError as exc:
            st.error(str(exc))
            return
        if len(sheet_names) > 1:
            sheet_key = f"sheet_{hashlib.sha256(content).hexdigest()[:12]}"
            selected_sheet = st.selectbox("Pilih lembar kerja", sheet_names, key=sheet_key)
        elif sheet_names:
            selected_sheet = sheet_names[0]

    try:
        frame = load_dataset(content, uploaded_file.name, selected_sheet)
    except DataLoadError as exc:
        st.error(str(exc))
        return
    except Exception:
        st.error("File tidak dapat diproses. Periksa format dan isi file, lalu coba kembali.")
        return

    dataset_id = _dataset_key(content, uploaded_file.name, selected_sheet)
    variables = numeric_columns(frame)
    metric_columns = st.columns(3)
    metric_columns[0].metric("Baris", f"{len(frame):,}".replace(",", "."))
    metric_columns[1].metric("Kolom", f"{len(frame.columns):,}".replace(",", "."))
    metric_columns[2].metric("Variabel numerik", f"{len(variables):,}".replace(",", "."))
    st.caption(f"File: **{uploaded_file.name}**" + (f" · Lembar: **{selected_sheet}**" if selected_sheet else ""))

    st.subheader("Pratinjau data")
    st.dataframe(frame.head(PREVIEW_ROWS), use_container_width=True, height=320)
    if len(frame) > PREVIEW_ROWS:
        st.caption(f"Menampilkan {PREVIEW_ROWS} dari {len(frame):,} baris.")

    missing = frame.isna().sum()
    missing_frame = pd.DataFrame(
        {
            "Variabel": [str(column) for column in frame.columns],
            "Nilai terisi": [int(frame[column].notna().sum()) for column in frame.columns],
            "Nilai kosong": [int(missing[column]) for column in frame.columns],
        }
    )
    with st.expander("Ringkasan nilai kosong"):
        st.dataframe(missing_frame, hide_index=True, use_container_width=True)

    if not variables:
        st.warning("Tidak ada variabel numerik yang terdeteksi. Gunakan kolom angka bertipe numerik; teks angka tidak dikonversi otomatis.")
        return

    st.subheader("Pilih analisis")
    variable_key = f"variables_{dataset_id}"
    statistics_key = f"statistics_{dataset_id}"
    if variable_key not in st.session_state:
        st.session_state[variable_key] = variables[:1]
    if statistics_key not in st.session_state:
        st.session_state[statistics_key] = list(DEFAULT_STATISTICS)

    selected_variables = st.multiselect(
        "Variabel numerik",
        options=variables,
        key=variable_key,
        help="Pilih satu atau beberapa variabel untuk dibandingkan.",
    )
    button_columns = st.columns([1, 1, 4])
    button_columns[0].button(
        "Pilih semua",
        key=f"select_all_{dataset_id}",
        on_click=_set_selection,
        args=(statistics_key, list(DEFAULT_STATISTICS)),
    )
    button_columns[1].button(
        "Hapus pilihan",
        key=f"clear_all_{dataset_id}",
        on_click=_set_selection,
        args=(statistics_key, []),
    )
    selected_statistics = st.multiselect(
        "Statistik yang ditampilkan",
        options=list(STATISTIC_KEYS),
        format_func=lambda key: STATISTIC_LABELS[key],
        key=statistics_key,
    )

    if not selected_variables:
        st.warning("Pilih setidaknya satu variabel.")
        return
    if not selected_statistics:
        st.warning("Pilih setidaknya satu statistik.")
        return

    raw_summary, statistics_by_column = build_summary_frame(frame, selected_variables, selected_statistics)
    display_summary = raw_summary.copy()
    for column in selected_variables:
        display_summary[column] = display_summary[column].map(format_result)

    st.subheader("Ringkasan statistik")
    st.dataframe(display_summary, hide_index=True, use_container_width=True)
    diagnostics = pd.DataFrame(
        [
            {
                "Variabel": column,
                "N valid": statistics_by_column[column]["n"],
                "Nilai kosong": statistics_by_column[column]["missing_count"],
                "Nilai tidak hingga": statistics_by_column[column]["non_finite_count"],
            }
            for column in selected_variables
        ]
    )
    st.caption("N menghitung observasi valid yang digunakan. Nilai kosong dan nilai tidak hingga dikecualikan.")
    st.dataframe(diagnostics, hide_index=True, use_container_width=True)

    download_columns = st.columns(2)
    download_columns[0].download_button(
        "Unduh ringkasan CSV",
        data=csv_bytes(raw_summary),
        file_name="statwise_ringkasan.csv",
        mime="text/csv",
        use_container_width=True,
    )
    download_columns[1].download_button(
        "Unduh ringkasan Excel",
        data=excel_bytes(raw_summary),
        file_name="statwise_ringkasan.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

    _show_visualization(frame, selected_variables, dataset_id)

    st.subheader("Interpretasi sederhana")
    for column in selected_variables:
        for sentence in interpret_column(column, statistics_by_column[column]):
            st.markdown(f"- {sentence}")
    st.caption("Interpretasi ini bersifat deskriptif dan tidak menyatakan hubungan sebab-akibat.")


if __name__ == "__main__":
    main()
