# STATWISE — Statistika Deskriptif

STATWISE adalah aplikasi Streamlit berbahasa Indonesia untuk mengeksplorasi data dan menghitung statistik deskriptif. Aplikasi menerima file Excel dan CSV, menampilkan pratinjau, membandingkan beberapa variabel numerik, membuat grafik, dan mengekspor ringkasan.

## Fitur

- Unggah `.xlsx`, `.xls`, dan `.csv` dengan batas 20 MB.
- Pilih lembar kerja untuk workbook Excel yang memiliki beberapa sheet.
- Lihat sampai 100 baris pratinjau dan ringkasan nilai kosong.
- Pilih satu atau beberapa kolom numerik dan statistik yang ingin ditampilkan.
- Lihat N valid, minimum, maksimum, rata-rata, median, semua modus, varians sampel, simpangan baku sampel, serta Q1, Q2, dan Q3.
- Tinjau histogram, boxplot, serta grafik frekuensi/proposi untuk variabel dengan sedikit nilai unik.
- Unduh ringkasan ke CSV atau Excel.
- Lihat interpretasi sederhana yang tidak membuat klaim sebab-akibat.

## Teknologi

Python, Streamlit, Pandas, NumPy, Plotly, OpenPyXL, dan xlrd.

## Instalasi lokal

Gunakan Python 3.10 atau lebih baru.

```bash
python -m venv .venv
```

Aktifkan lingkungan virtual:

```bash
# Windows PowerShell
.venv\Scripts\Activate.ps1

# macOS/Linux
source .venv/bin/activate
```

Pasang dependensi dan jalankan aplikasi:

```bash
pip install -r requirements.txt
streamlit run app.py
```

Buka alamat lokal yang ditampilkan Streamlit di terminal.

## Cara menggunakan

1. Unggah file Excel atau CSV.
2. Jika workbook memiliki beberapa sheet, pilih sheet yang ingin dianalisis.
3. Tinjau pratinjau dan jumlah nilai kosong.
4. Pilih satu atau beberapa variabel numerik dan statistik.
5. Tinjau tabel, grafik, dan interpretasi.
6. Unduh ringkasan CSV atau Excel.

Kolom teks yang tampak seperti angka tidak dikonversi otomatis. Simpan kolom tersebut sebagai angka di sumber data sebelum mengunggah.

## Konvensi statistik

- N adalah jumlah observasi numerik valid yang digunakan.
- Nilai kosong dan nilai tidak hingga seperti `inf` dikecualikan; jumlah keduanya dilaporkan terpisah.
- Varians dan simpangan baku memakai konvensi sampel (`ddof=1`). Untuk N kurang dari dua, kedua nilai itu tidak tersedia.
- Modus menampilkan semua nilai yang memiliki frekuensi tertinggi.
- Q1, Q2, dan Q3 adalah persentil 25, 50, dan 75 dengan interpolasi linear NumPy. Q2 dibuat sama dengan median.
- Perhitungan dan ekspor mempertahankan nilai penuh; aplikasi hanya membulatkan angka pada tampilan.

## Pengujian

Pasang dependensi pengembangan lalu jalankan tes:

```bash
pip install -r requirements-dev.txt
python -m pytest
```

Tes mencakup hasil yang diketahui, modus seri, nilai kosong/tidak hingga, nilai konstan, beberapa variabel, parsing CSV/Excel, validasi file, dan ekspor. Setelah tes, jalankan `streamlit run app.py` untuk smoke test halaman aplikasi.

## Deploy ke Streamlit Community Cloud

1. Push repository ke GitHub.
2. Buat aplikasi baru di Streamlit Community Cloud dan hubungkan repository ini.
3. Pilih branch `main` dan file utama `app.py`.
4. Deploy, lalu uji unggah, pemilihan sheet, perhitungan, grafik, dan unduhan melalui URL publik.

`requirements.txt` menyediakan dependensi runtime. Render dapat dipakai sebagai fallback apabila Streamlit Community Cloud tidak sesuai; gunakan perintah start berikut dan port yang disediakan platform:

```bash
streamlit run app.py --server.address 0.0.0.0 --server.port $PORT
```

## Privasi dan keamanan

Aplikasi tidak menulis dataset unggahan ke disk atau memasukkan isi dataset ke log. File diproses dalam sesi Streamlit. Jangan unggah data sensitif ke deployment publik. Batas ukuran file adalah 20 MB.
