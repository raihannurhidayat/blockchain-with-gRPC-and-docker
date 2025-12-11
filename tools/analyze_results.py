import pandas as pd
import matplotlib.pyplot as plt
import sys
import os
import json  # <--- Tambahan untuk fitur history

LOG_FILE = "logs/simulation_data.csv"
HISTORY_FILE = "logs/benchmark_history.json" # <--- File database history

def analyze():
    # 1. Cek File
    if not os.path.exists(LOG_FILE):
        print(f"File log tidak ditemukan di: {LOG_FILE}")
        return

    try:
        df = pd.read_csv(LOG_FILE, names=["Timestamp", "NodeID", "Event", "Details"])
    except Exception as e:
        print(f"Error membaca CSV: {e}")
        return

    print(f"{'='*50}")
    print(f"   ANALISIS PERFORMA BLOCKCHAIN (METODE ACTIVE WINDOW)")
    print(f"{'='*50}")

    if df.empty:
        print("Data kosong.")
        return

    # Hitung Jumlah Node Aktif (Penting untuk Key Database)
    active_nodes = df["NodeID"].nunique()
    print(f"Jumlah Node Terdeteksi       : {active_nodes} Node")

    # --- BAGIAN 1: DATA MENTAH & MINING ---
    start_sim = df["Timestamp"].min()
    end_sim = df["Timestamp"].max()
    total_duration = end_sim - start_sim
    
    mined_blocks = df[df["Event"] == "Block Mined"]
    total_blocks = len(mined_blocks)
    
    # Block Throughput
    bps = total_blocks / total_duration if total_duration > 0 else 0

    print(f"Total Durasi Simulasi (Uptime) : {total_duration:.2f} detik")
    print(f"Total Blok Terbentuk           : {total_blocks}")
    print(f"Block Throughput               : {bps:.4f} blocks/sec")
    print(f"{'-'*50}")

    # --- BAGIAN 2: TRANSAKSI & TPS (LOGIKA BARU) ---
    tx_logs = df[df["Event"].str.contains("Transaction", case=False, na=False)]
    
    # Inisialisasi variabel default agar tidak error jika kosong
    real_tps = 0
    tx_duration = 0
    unique_tx_count = 0

    if not tx_logs.empty:
        # A. Hitung Jumlah Transaksi Unik
        unique_tx_count = tx_logs["Details"].nunique()
        
        # B. Tentukan 'Active Window'
        tx_start_time = tx_logs["Timestamp"].min()
        tx_end_time = tx_logs["Timestamp"].max()
        
        # Durasi pengerjaan transaksi saja
        tx_duration = tx_end_time - tx_start_time
        
        # Safety check
        if tx_duration <= 0.0001:
            tx_duration = 1.0 

        # C. Hitung TPS Sebenarnya
        real_tps = unique_tx_count / tx_duration

        print(f"Jendela Waktu Transaksi (Active) : {tx_duration:.4f} detik")
        print(f"Jumlah Transaksi Unik            : {unique_tx_count}")
        print(f"Transaction Throughput (TPS)     : {real_tps:.4f} TPS")
        print(f"(Dihitung dari {unique_tx_count} tx dibagi {tx_duration:.2f} detik)")
    else:
        print("Tidak ada data transaksi ditemukan (Pastikan client.py dijalankan!)")

    print(f"{'-'*50}")

    # --- BAGIAN 3: LATENCY (PROPAGASI) ---
    df["Hash"] = df["Details"].apply(lambda x: x.split("Hash ")[1] if isinstance(x, str) and "Hash " in x else None)
    mined_events = df[df["Event"] == "Block Mined"].dropna(subset=["Hash"])
    received_events = df[df["Event"] == "Block Received"].dropna(subset=["Hash"])
    
    latencies = []
    for _, mined in mined_events.iterrows():
        block_hash = mined["Hash"]
        mine_time = mined["Timestamp"]
        receptions = received_events[received_events["Hash"] == block_hash]
        for _, rx in receptions.iterrows():
            latency = rx["Timestamp"] - mine_time
            if latency > 0: latencies.append(latency)
                
    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    print(f"Rata-rata Latency Propagasi      : {avg_latency:.6f} detik")
    print(f"{'='*50}")

    # --- BAGIAN 4: SIMPAN KE DATABASE JSON (FITUR BARU) ---
    # Kita hanya menyimpan jika ada transaksi yang terjadi
    if unique_tx_count > 0:
        # 1. Load data lama
        data_history = {}
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r") as f:
                    data_history = json.load(f)
            except:
                data_history = {}

        # 2. Update data (Key = Jumlah Node)
        # Ini menjamin tidak ada duplikat data untuk jumlah node yang sama.
        node_key = str(active_nodes)
        
        data_history[node_key] = {
            "nodes": int(active_nodes),
            "duration": float(tx_duration),
            "throughput": float(real_tps),
            "latency": float(avg_latency),
            "tx_count": int(unique_tx_count)
        }

        # 3. Save kembali ke file
        with open(HISTORY_FILE, "w") as f:
            json.dump(data_history, f, indent=4)
            
        print(f"[AUTO-SAVE] Data untuk {active_nodes} Node berhasil disimpan ke history.")
        print(f"Database saat ini berisi data untuk node: {list(data_history.keys())}")
    else:
        print("[SKIP-SAVE] Tidak menyimpan ke history karena tidak ada transaksi.")

    # --- BAGIAN 5: PLOTTING ---
    if not mined_blocks.empty:
        plt.figure(figsize=(10, 6))
        mined_blocks = mined_blocks.sort_values("Timestamp")
        mined_blocks["Elapsed"] = mined_blocks["Timestamp"] - start_sim
        mined_blocks["BlockCount"] = range(1, len(mined_blocks) + 1)
        plt.plot(mined_blocks["Elapsed"], mined_blocks["BlockCount"])
        plt.xlabel("Waktu (s)")
        plt.ylabel("Jumlah Blok")
        plt.title("Pertumbuhan Blockchain")
        plt.grid(True)
        plt.savefig("logs/growth_plot.png")
        print("Grafik disimpan ke logs/growth_plot.png")

if __name__ == "__main__":
    analyze()