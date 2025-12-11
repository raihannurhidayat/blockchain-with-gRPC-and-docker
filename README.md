# Simulasi Blockchain PoW Terdistribusi

Proyek ini mensimulasikan jaringan blockchain Proof-of-Work terdistribusi menggunakan Python, gRPC, dan Docker. Ini dibuat untuk bisa menganalisis kinerja jaringan, skalabilitas, dan metrik konsensus.

## Prasyarat

- [Docker](https://www.docker.com/) dan Docker Compose
- Python 3.9+
- Disarankan: Buat virtual environment (`python -m venv venv` dan `source venv/bin/activate` atau `venv\Scripts\activate`)

## Pengaturan

1.  **Instal Dependensi:**

    ```bash
    pip install -r requirements.txt
    ```

2.  **Hasilkan Kode gRPC:**
    ```bash
    python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. protos/blockchain.proto
    ```
    _(Catatan: Ini juga dilakukan secara otomatis di dalam container Docker)_

## Menjalankan Simulasi

1.  **Hasilkan Konfigurasi Jaringan secara paralel:**
    Jalankan alat orkestrator untuk membuat jaringan dengan flag "--nodes" untuk menentukan jumlah node (contohnya: 3).

    ```bash
    python tools/generate_network.py parallel --nodes 3
    ```

    **Hasilkan Konfigurasi Jaringan secara sekuensial:**
    Jalankan alat orkestrator untuk membuat jaringan secara sekuensial.

    ```bash
    python tools/generate_network.py sequential
    ```

2.  **Mulai Jaringan:**
    Build dan jalankan container Docker.

    ```bash
    docker-compose up --build
    ```

    _Buka terminal baru untuk langkah selanjutnya._

3.  **Inject Transaksi (Client):**
    Jalankan klien untuk mengirim transaksi ke node (default mengirim 10 tx).
    _Lebih Sederhana_: Cukup masuk (exec) ke dalam node (Gunakan ini jika tidak ingin membuat docker baru di terminal baru).

    ```bash
    docker exec -it node_1 python src/client.py
    ```

4.  **Simulasikan Kegagalan Node:**
    Hentikan container tertentu untuk mensimulasikan crash.

    ```bash
    docker stop node_2
    ```

5.  **Hentikan Simulasi:**
    ```bash
    docker-compose down
    ```

## Menganalisis Hasil

Log simulasi disimpan di `logs/simulation_data.csv`.

1.  **Jalankan Analisis:**
    ```bash
    python tools/analyze_results.py
    ```
    Menghitung Speedup (Peningkatan Kecepatan), Throughput, Latency (Latensi), dan menyimpan plot ke `logs/growth_plot.png`.

## Struktur Proyek

- `src/node.py`: Logika node blockchain (Mining, Server/Klien gRPC).
- `src/client.py`: Generator transaksi.
- `protos/blockchain.proto`: Definisi protocol buffer.
- `tools/generate_network.py`: Membuat `docker-compose.yml`.
- `tools/analyze_results.py`: Perhitungan metrik.
