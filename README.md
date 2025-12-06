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
    *(Catatan: Ini juga dilakukan secara otomatis di dalam container Docker)*

## Menjalankan Simulasi

1.  **Hasilkan Konfigurasi Jaringan:**
    Jalankan alat orkestrator untuk membuat jaringan dengan `N` node (contohnya: 3).
    ```bash
    python tools/generate_network.py 3
    ```

2.  **Mulai Jaringan:**
    Build dan jalankan container Docker.
    ```bash
    docker-compose up --build
    ```
    *Buka terminal baru untuk langkah selanjutnya.*

3.  **Inject Transaksi (Client):**
    Jalankan klien untuk mengirim transaksi ke node (default mengirim 10 tx).
    <!-- ```bash
    # Linux/Mac
    export TARGET_NODE=localhost:50051
    python src/client.py 
    
    # Windows (Powershell)
    $env:TARGET_NODE="localhost:50051"
    python src/client.py
    ```
    Anda dapat menjalankan ini beberapa kali atau terhadap port yang berbeda (dipetakan oleh docker-compose, tetapi kami menggunakan jaringan internal. **Penting**: Secara default, `docker-compose` mungkin tidak memetakan port ke host kecuali ditentukan. Skrip saya tidak memetakan port ke host untuk menghindari konflik, jadi klien perlu berjalan **di dalam** jaringan docker atau kita perlu memperbarui `generate_network.py` untuk memetakan port jika menjalankan klien secara lokal.
    
    *Koreksi*: `generate_network.py` saat ini TIDAK memetakan port ke host. Untuk menjalankan klien secara lokal, Anda perlu memetakan port atau menjalankan klien dalam container.
    
    **Opsi A: Jalankan Klien di Docker (Disarankan)**
    ```bash
    docker run --network blockchain-simulation-with-grpc_blockchain-net --env TARGET_NODE=node_1:50051 -v $(pwd):/app python:3.9-slim sh -c "pip install grpcio protobuf && python /app/src/client.py"
    ``` -->
    *Lebih Sederhana*: Cukup masuk (exec) ke dalam node (Gunakan ini jika tidak ingin membuat docker baru di terminal baru).
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
