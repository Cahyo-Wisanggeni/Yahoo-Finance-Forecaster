# Panduan Kontribusi - Yahoo Finance Forecaster GUI

Terima kasih atas minat Anda untuk berkontribusi pada **Yahoo Finance Forecaster GUI**!

## 🛠️ Pengaturan Lingkungan Pengembangan (*Development Setup*)

1. Fork dan kloning repositori:
   ```bash
   git clone https://github.com/Cahyo-Wisanggeni/Yahoo-Finance-Forecaster.git
   cd Yahoo-Finance-Forecaster/"Yahoo Finance Forecaster GUI"
   ```

2. Buat dan aktifkan virtual environment:
   ```bash
   python -m venv venv
   # Pada Windows:
   venv\Scripts\activate
   # Pada Linux / macOS:
   source venv/bin/activate
   ```

3. Pasang seluruh dependensi pustaka:
   ```bash
   pip install -r requirements.txt
   ```

4. Jalankan aplikasi GUI:
   ```bash
   python app.py
   # atau di Windows:
   run_gui.bat
   ```

---

## 🎨 Pedoman Desain & Komponen GUI

- Aplikasi ini sengaja menggunakan pustaka bawaan `tkinter` dan `ttk` tanpa dependensi antarmuka eksternal yang berat (seperti Qt atau wxWidgets). Pertahankan komponen UI murni Tkinter + Matplotlib demi portabilitas lintas platform yang maksimal serta kemudahan instalasi.
- Seluruh tugas yang memakan waktu (pengambilan data Yahoo Finance, pelatihan model *Random Forest*, peramalan *multi-step*) **wajib dijalankan dalam background daemon thread** agar antarmuka Tkinter tidak membeku (*freeze*).
- Pertahankan konsistensi tema warna (`primary: #6B21A8`, `primary_dark: #4C1D95`, `accent: #06B6D4`, `bg: #F8FAFC`).

---

## 🚀 Alur Kerja Pull Request

1. Buat branch fitur baru:
   ```bash
   git checkout -b fitur/nama-fitur-anda
   ```
2. Lakukan commit perubahan Anda:
   ```bash
   git commit -m "feat: Menambahkan opsi ekspor grafik interaktif"
   ```
3. Push ke branch Anda dan buat Pull Request baru di repositori GitHub dengan penjelasan yang informatif.
