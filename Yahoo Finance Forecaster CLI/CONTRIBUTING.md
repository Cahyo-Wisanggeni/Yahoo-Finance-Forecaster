# Panduan Kontribusi - Yahoo Finance Forecaster CLI

Terima kasih atas ketertarikan Anda untuk berkontribusi pada **Yahoo Finance Forecaster CLI**!

## Pengaturan Lingkungan Pengembangan (*Development Setup*)

1. Fork dan kloning repositori:
   ```bash
   git clone https://github.com/Cahyo-Wisanggeni/Yahoo-Finance-Forecaster.git
   cd Yahoo-Finance-Forecaster/"Yahoo Finance Forecaster CLI"
   ```

2. Buat dan aktifkan virtual environment:
   ```bash
   python -m venv venv
   # Pada Windows:
   venv\Scripts\activate
   # Pada Linux / macOS:
   source venv/bin/activate
   ```

3. Pasang semua dependensi yang dibutuhkan:
   ```bash
   pip install -r requirements.txt
   ```

4. Uji coba menjalankan program CLI:
   ```bash
   python main.py
   ```

---

## Standar Kode

- Ikuti pedoman gaya kode **PEP 8**.
- Buat komentar kode yang ringkas, jelas, dan informatif (jelaskan *mengapa*, bukan sekadar *apa* yang sudah jelas dari kode).
- Pastikan penanganan kesalahan (*error handling*) mampu menangani gangguan jaringan atau kode ticker tidak valid dengan baik tanpa membuat program *crash*.
- Lakukan pengujian menggunakan ticker lokal BEI (misal: `BBCA.JK`) dan ticker bursa global (misal: `AAPL`).

---

## Alur Kerja Pull Request

1. Buat branch fitur baru:
   ```bash
   git checkout -b fitur/nama-fitur-anda
   ```
2. Lakukan commit perubahan Anda:
   ```bash
   git commit -m "feat: Menambahkan metrik evaluasi baru"
   ```
3. Push ke branch Anda dan buka Pull Request dengan deskripsi perubahan yang jelas dan terstruktur.
