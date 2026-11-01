# Benchmark Software Proyek EKG Telehealth

Skrip untuk mengulang empat uji di bagian Minggu 4, 1.2 Software. Hasil asli ada di folder `hasil/`, grafiknya di `grafik/`.

Lingkungan uji asli: Linux, CPU 2 inti, RAM sekitar 7 GB, Python 3.13, PostgreSQL 16, TimescaleDB 2.29.2.
Angka di laptop lain akan berbeda. Yang dibandingkan adalah urutan dan selisih antarteknologi.

## Persiapan

```
pip install -r requirements.txt
python -m playwright install chromium
```

## 1. Front-end: waktu per frame (Canvas 2D, Chart.js, SVG)

```
cd frontend
npm install chart.js@4.4.4
python run_fe.py
```
Hasil: `fe_results.json`. Kolom yang dipakai di grafik adalah `frameMs`.

## 2. Back-end: jeda kirim data live (WebSocket, SSE, REST polling)

Terminal 1:
```
cd backend_transport
uvicorn server:app --port 8000 --log-level warning
```
Terminal 2 (format: `mode jumlah_klien durasi_detik`):
```
cd backend_transport
for m in polling sse ws; do for n in 1 10 50 100 200; do python client.py $m $n 15; done; done > be_results.jsonl
```
Di Windows, jalankan perintah `python client.py ...` satu per satu.

## 3. Back-end: waktu query riwayat (PostgreSQL vs TimescaleDB)

Butuh PostgreSQL 16 dengan ekstensi TimescaleDB. Paling mudah lewat Docker:
```
docker run -d --name tsdb -p 5432:5432 -e POSTGRES_PASSWORD=postgres timescale/timescaledb:latest-pg16
docker exec -it tsdb psql -U postgres -c "create database plain" -c "create database ts"
docker exec -it tsdb psql -U postgres -d ts -c "create extension if not exists timescaledb"
```
Lalu:
```
cd backend_database
set PGPASSWORD=postgres      (Windows)   atau   export PGPASSWORD=postgres   (Linux/Mac)
python setup.py     # mengisi 30 hari data sintetis, sekitar 1,7 GB per database
python query.py
```
Pengaturan PostgreSQL saat uji asli: shared_buffers=1GB, work_mem=64MB, jit=off.

## 4. Machine learning: waktu inferensi

```
cd ml
python ml_bench.py
```
Yang diukur hanya kecepatan. Model belum dilatih, jadi akurasi belum diuji.

## Menggambar ulang grafik

Salin file hasil ke folder `hasil/`, lalu dari folder utama:
```
python plot.py
```
Grafik memakai font Liberation Serif. Kalau tidak ada, matplotlib akan memakai font bawaan.
