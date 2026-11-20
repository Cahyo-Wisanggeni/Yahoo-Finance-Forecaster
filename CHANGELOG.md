# Catatan Perubahan (Changelog)

Seluruh perubahan penting pada proyek **Yahoo Finance Forecaster** akan didokumentasikan dalam berkas ini.

Format berkas ini mengacu pada [Keep a Changelog](https://keepachangelog.com/id/1.0.0/) dan mematuhi prinsip [Semantic Versioning (SemVer)](https://semver.org/lang/id/).

---

## [Belum Dirilis] (Unreleased)

### Ditambahkan
- **Tab Analisis Variabel**: Visualisasi opsional **SHAP Feature Importance & Summary Impact** (`shap.TreeExplainer`) serta **Learning Curve** (`TimeSeriesSplit` cross-validation) beserta tombol pop-up HD.
- **Kotak Pengaturan Opsional**: Pilihan centang *SHAP analysis* dan *Learning Curve* pada panel Parameter Peramalan.
- **Tab Riwayat**: Penyimpanan otomatis riwayat peramalan ke `forecast_history.json` lengkap dengan fitur pencarian, muat ulang hasil, pakai ulang parameter, dan hapus riwayat.

### Diubah
- **Fokus Edisi Tunggal (GUI)**: Seluruh berkas aplikasi GUI (`app.py`, `requirements.txt`, `run_gui.bat`, `run_gui_debug.bat`, `CONTRIBUTING.md`) dipindahkan langsung ke direktori utama (root) repositori agar struktur lebih bersih tanpa duplikasi berkas.
- Pembaruan `README.md`, `CONTRIBUTING.md`, dan `.gitignore` mengikuti struktur baru berbasis GUI.

### Dihapus
- Menghapus direktori **Edisi Terminal (CLI)** (`Yahoo Finance Forecaster CLI/`) beserta tangkapan layar pratinjau CLI (`assets/cli_preview.png`, `assets/cli_preview_v2.png`).

---

## [1.0.0] - 2026-11-17

### Rilis Perdana Stabil (Initial Stable Release)
Rilis resmi perdana platform peramalan pergerakan harga pasar keuangan **Yahoo Finance Forecaster**, awalnya menghadirkan dua edisi: **Terminal CLI** dan **Desktop GUI**.

### Fitur Utama

#### Inti Machine Learning (Core Engine)
- **Strategi Peramalan**: Menggunakan `skforecast.direct.ForecasterDirect` untuk memproyeksikan pergerakan multi-langkah (*multi-step forecast*) secara langsung tanpa akumulasi galat (*error accumulation*).
- **Model Estimator**: Algoritma `RandomForestRegressor` (100 *decision trees*, `random_state=42`, `n_jobs=-1`) yang teroptimasi untuk stabilitas dan kecepatan eksekusi.
- **Rekayasa Fitur (Feature Engineering)**:
  - 10 variabel lag autoregresif (`lag_1` hingga `lag_10`).
  - 10 variabel rata-rata bergerak (*rolling window averages* `roll_mean_1` hingga `roll_mean_10`).
  - Total 20 fitur prediktor deret waktu.
- **Diferensiasi Ordo Pertama**: Transformasi data harga non-stasioner menjadi deret stasioner secara otomatis.
- **Validasi Evaluasi Internal**: Pemisahan data latih dan data uji (80% / 20%) untuk menghitung metrik evaluasi Mean Absolute Error (MAE) dan Mean Absolute Percentage Error (MAPE).

#### Edisi Desktop (GUI)
- Antarmuka grafis desktop modern berbasis Python `tkinter` dan `ttk` murni tanpa ketergantungan pustaka antarmuka eksternal yang berat.
- Arsitektur komputasi *multi-threading* asinkron pada latar belakang (*daemon thread*) sehingga antarmuka pengguna tidak membeku (*non-blocking / no freeze*).
- Konversi otomatis huruf kapital (*auto-uppercase*) pada input ticker serta deteksi langsung informasi Nama Perusahaan, Sektor, dan Industri.
- Tombol *preset* tanggal cepat (1 Tahun, 2 Tahun, 3 Tahun, 5 Tahun).
- Tab navigasi terstruktur:
  - **Grafik Prediksi**: Kanvas Matplotlib tersemat (sinkronisasi grafik evaluasi dan proyeksi masa depan) dengan toolbar interaktif dan tombol pop-up HD.
  - **Tabel Rincian Prediksi**: Tabel Treeview terperinci yang memuat tanggal proyeksi, estimasi harga, perubahan nominal, dan persentase perubahan harga.
  - **Ekspor CSV**: Fitur ekspor seluruh hasil proyeksi ke berkas spreadsheet CSV (`prediksi_<ticker>_<timestamp>.csv`).
  - **Log Komputasi**: Aliran log teknis berpenanda waktu (*timestamp*) secara *real-time*.
  - **Tutorial**: Panduan penggunaan terintegrasi langsung di dalam aplikasi.
- Tombol reset parameter dan pembersihan memori kanvas yang aman saat penutupan aplikasi.
- Skrip peluncuran Windows (`run_gui.bat` dan `run_gui_debug.bat`).

#### Edisi Terminal (CLI) *(Dihapus pasca-v1.0.0)*
- Antarmuka terminal interaktif dengan pewarnaan ANSI, logo ASCII, validasi input interaktif, tabel ringkasan ASCII, dan pop-up Matplotlib HD.
