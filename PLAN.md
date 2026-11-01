# PLAN: Benchmark EKG v2

Status: menunggu persetujuan. Belum ada kode yang ditulis.

## 1. Temuan dari isi folder lama

Bias tambahan di luar daftar dosen, ditemukan saat membaca kode:

| Uji | Temuan | Perbaikan |
|---|---|---|
| Front-end | `frameMs` = waktu total / jumlah frame di Chromium headless dengan batas fps dimatikan. Itu bukan waktu per frame di layar. `workMs` hanya waktu JavaScript, tanpa raster. | Ukur selisih timestamp `requestAnimationFrame`, hitung frame > 16,7 ms. Headless dan headed. |
| Front-end | Canvas 2D polos tanpa sumbu, sedangkan Chart.js menggambar sumbu dan layout. Chart.js juga menyalin data tiap frame. | Samakan: semua tanpa sumbu (kerja inti menggambar garis), lalu satu varian dengan sumbu untuk uPlot dan Chart.js. |
| Transport | Server dan klien satu mesin, satu jam. Semua klien dalam satu proses `asyncio` (klien bisa jadi penyempit). Tidak ada p99, bandwidth, CPU. Polling mengukur umur data, bukan jeda kirim. | Klien dibagi ke beberapa proses, ukur CPU server (`psutil`), byte per klien, p99. Pisahkan metrik "umur data" untuk polling dan jelaskan. |
| Transport | Alur asli perangkat lewat MQTT, uji hanya mulai dari FastAPI. | Dicatat sebagai keterbatasan (MQTT di luar cakupan benchmark ini). |
| Database | Data diisi dengan `generate_series` di sisi server dari 1000 paket. Biaya insert nyata tidak terukur. Indeks dibuat setelah isi. Hanya 1 perangkat. | Ingest lewat `COPY` dan `INSERT` batch dengan indeks sudah ada, dari rekaman MIT-BIH. Beberapa pasien. |
| ML | Input acak, RF hanya 6 fitur acak tanpa ekstraksi, RF `n_jobs=1` sedangkan DL memakai semua inti. | Data nyata, ekstraksi fitur dihitung, jumlah thread dicatat dan disamakan. |

## 2. Lingkungan

- Mesin: Apple M2, 16 GB, Docker 29.1.3 tersedia. Satu mesin saja.
- Python: sistem 3.14 terlalu baru untuk TensorFlow/TFLite. Pakai `uv venv --python 3.11 .venv`. `requirements.txt` dikunci dengan `uv pip compile`.
- Keputusan yang perlu persetujuan: `ml_bench.py` memakai Keras + backend JAX, tetapi konversi TFLite int8 butuh TensorFlow. Usul: arsitektur tetap sama (disalin dari `ml_bench.py`), backend diganti TensorFlow untuk semua model DL supaya waktu inferensi sebanding dan model bisa dikonversi. Perbedaan ini dicatat di METODOLOGI.md.
- Notebook dijalankan dengan `jupyter nbconvert --execute`; kode pengukuran dalam modul kecil `bench/` (env, statistik, gaya grafik) agar notebook tidak berisi salinan kode.

## 3. Struktur

```
data/download_mitdb.py   data/raw/ (gitignore)   data/processed/
bench/                   env.py, stats.py, plotstyle.py (dari plot.py lama)
notebooks/               00..04
results/                 CSV mentah per uji
grafik/                  PNG/PDF dari CSV, hitam putih
app_reference/inference.py
models/                  .keras, .tflite, metadata.json
docker-compose.yml       PostgreSQL 16 + TimescaleDB
METODOLOGI.md  REFERENSI.md  RINGKASAN_HASIL.md  .gitignore
```

Folder lama (`frontend/`, `backend_*`, `ml/`, `hasil/`) dipertahankan sebagai versi 1 dan dipakai sebagai dasar. Tidak dihapus.

## 4. Urutan kerja dan perkiraan waktu (M2)

| # | Notebook | Isi inti | Waktu jalan penuh | Versi uji coba |
|---|---|---|---|---|
| 00 | data | unduh 48 rekaman (~100 MB), resample, filter 0,5 sampai 40 Hz, distribusi DS1/DS2 | ~5 menit | tidak perlu |
| 01 | ML | Pan-Tompkins, 5 model x 5 seed, tuning grup CV, TFLite int8, inferensi 1 sampai 200 pasien | ~2 sampai 4 jam (perkiraan kasar, ukur dulu di 1 model) | 2 seed, subset DS1, ~20 menit |
| 02 | database | 4 konfigurasi, 30 hari, ingest, refresh, kompresi | ~1 sampai 2 jam, disk ~10 GB | 3 hari data, ~10 menit |
| 03 | transport | 3 protokol x 5 jumlah klien x 5 ulangan x 30 detik | ~30 menit | 2 ulangan, ~8 menit |
| 04 | front-end | 4 library x 6 ukuran x 5 ulangan, headless dan headed | ~20 menit | 2 ulangan, ~5 menit |

Sebelum notebook 01 dan 02 saya ukur waktu satu unit kerja dulu, lalu beri tahu angka sebenarnya dan tawarkan versi kecil.

Cara pengulangan data di 02: tiap rekaman 30 menit menghasilkan ~1800 paket 1 detik. Paket diputar berurutan per pasien dengan offset rekaman berbeda, dan diulang sampai 30 hari. Konsekuensinya: data berulang sehingga kompresi TimescaleDB bisa tampak lebih baik dari data nyata. Ini dicatat sebagai keterbatasan, dan ukuran kompresi juga dilaporkan pada data tanpa pengulangan (satu rekaman utuh) sebagai pembanding.

## 5. Rujukan

- Sumber wajib dari daftar Anda masuk ke `REFERENSI.md`.
- Angka pembanding de Chazal 2004 diambil dari teks paper. Kalau paper tidak bisa saya akses lewat jaringan, ditulis "TODO: verifikasi sumber", bukan dari ingatan.
- Pilihan metode tanpa sumber yang bisa saya verifikasi (uPlot sebagai canvas library kuat, kebijakan refresh matview, dan sejenisnya) ditandai "TODO: verifikasi sumber".
- Lisensi MIT-BIH: dibaca dari halaman PhysioNet saat mengunduh, tidak dari ingatan.

## 6. Hal yang tidak dikerjakan

- MQTT dan ESP32 asli. Alur ini tidak diuji.
- Mesin kedua untuk transport, kecuali Anda punya. Tanpa itu jeda diukur di satu mesin dan satu jam, dan itu ditulis sebagai keterbatasan.
- Grafik berwarna. Semua abu-abu dengan marker dan jenis garis.

## 7. Yang perlu Anda putuskan

1. Backend TensorFlow menggantikan JAX (bagian 2). Setuju?
2. Skala database penuh: 1 pasien x 30 hari (~2,6 juta baris, ~2 GB per konfigurasi), ditambah uji multi-pasien kecil (10 pasien x 3 hari). Setuju, atau mau jumlah lain?
3. Ada mesin kedua untuk uji transport?
4. Jalankan versi uji coba dulu untuk 01 dan 02, baru penuh?
