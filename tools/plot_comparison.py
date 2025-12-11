import json
import matplotlib.pyplot as plt
import os
import sys

HISTORY_FILE = "logs/benchmark_history.json"

def generate_graphs():
    if not os.path.exists(HISTORY_FILE):
        print(f"File {HISTORY_FILE} belum ada. Jalankan simulasi dulu!")
        return

    # 1. Load Data
    with open(HISTORY_FILE, "r") as f:
        data = json.load(f)

    # Konversi ke List dan Sort berdasarkan jumlah node (1, 2, 4, 8...)
    # Agar grafik garisnya urut
    sorted_nodes = sorted([int(k) for k in data.keys()])
    
    # Siapkan List untuk Sumbu X dan Y
    nodes_x = []
    throughput_y = []
    latency_y = []
    speedup_y = []
    efficiency_y = []

    # 2. Cari Baseline (Sequential / 1 Node)
    if "1" not in data:
        print("ERROR: Data untuk '1 Node' (Sequential) belum ada.")
        print("Harap jalankan simulasi 1 node dulu sebagai pembanding Speedup.")
        return
    
    t_sequential = data["1"]["duration"]

    print(f"{'='*40}")
    print(f"GENERATING COMPARISON GRAPHS")
    print(f"Baseline (1 Node) Duration: {t_sequential:.4f} s")
    print(f"{'='*40}")

    # 3. Hitung Rumus untuk setiap data node
    for n in sorted_nodes:
        record = data[str(n)]
        
        t_paralel = record["duration"]
        p = n # Jumlah prosesor/node
        
        # Rumus Speedup: S = T_seq / T_par
        s = t_sequential / t_paralel
        
        # Rumus Efficiency: E = S / P
        e = s / p
        
        nodes_x.append(n)
        throughput_y.append(record["throughput"])
        latency_y.append(record["latency"])
        speedup_y.append(s)
        efficiency_y.append(e)
        
        print(f"Node {n}: Speedup={s:.2f}x, Eff={e:.2f}")

    # 4. Membuat Plot (4 Grafik dalam 1 Gambar)
    fig, axs = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle('Analisis Skalabilitas Blockchain (Sequential vs Parallel)', fontsize=16)

    # Grafik A: Throughput
    axs[0, 0].plot(nodes_x, throughput_y, marker='o', color='b')
    axs[0, 0].set_title('Throughput (Transaction/Sec)')
    axs[0, 0].set_xlabel('Jumlah Node')
    axs[0, 0].set_ylabel('TPS')
    axs[0, 0].grid(True)

    # Grafik B: Latency
    axs[0, 1].plot(nodes_x, latency_y, marker='o', color='r')
    axs[0, 1].set_title('Latency (Block Propagation)')
    axs[0, 1].set_xlabel('Jumlah Node')
    axs[0, 1].set_ylabel('Detik')
    axs[0, 1].grid(True)

    # Grafik C: Speedup
    axs[1, 0].plot(nodes_x, speedup_y, marker='o', color='g')
    axs[1, 0].plot(nodes_x, nodes_x, linestyle='--', color='gray', alpha=0.5, label='Ideal Linear') # Garis ideal
    axs[1, 0].set_title('Speedup Ratio (S)')
    axs[1, 0].set_xlabel('Jumlah Node')
    axs[1, 0].set_ylabel('Ratio')
    axs[1, 0].legend()
    axs[1, 0].grid(True)

    # Grafik D: Efficiency
    axs[1, 1].plot(nodes_x, efficiency_y, marker='o', color='purple')
    axs[1, 1].set_title('Efficiency (E)')
    axs[1, 1].set_xlabel('Jumlah Node')
    axs[1, 1].set_ylabel('Ratio (0-1)')
    axs[1, 1].set_ylim(0, 1.1) # Batas y 0 sampai 1.1
    axs[1, 1].grid(True)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    
    output_file = "logs/final_comparison_analysis.png"
    plt.savefig(output_file)
    print(f"\n[DONE] Grafik perbandingan disimpan ke: {output_file}")
    # plt.show() # Uncomment jika ingin pop-up window

if __name__ == "__main__":
    generate_graphs()