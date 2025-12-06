import pandas as pd
import matplotlib.pyplot as plt
import sys
import os

# LOG_FILE = "../logs/simulation_data.csv"
LOG_FILE = "logs/simulation_data.csv"

def analyze():
    if not os.path.exists(LOG_FILE):
        print(f"Log file {LOG_FILE} not found.")
        return

    # Check if file has header, if not, add names
    # Our node.py writes: timestamp, node_id, event_type, details
    try:
        df = pd.read_csv(LOG_FILE, names=["Timestamp", "NodeID", "Event", "Details"])
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    # 1. Total Duration
    start_time = df["Timestamp"].min()
    end_time = df["Timestamp"].max()
    duration = end_time - start_time
    print(f"Total Simulation Duration: {duration:.2f} seconds")

    # 2. Mining Performance (Blocks Mined)
    mined_blocks = df[df["Event"] == "Block Mined"]
    total_blocks = len(mined_blocks)
    print(f"Total Blocks Mined: {total_blocks}")
    
    # 3. Thoughput (TPS)
    # We count "Transaction Received" or "Block Mined"? 
    # Usually TPS is confirmed transactions.
    # We can infer tx count from details? Or just use block count * avg tx?
    # Our node.py logs "Block Mined" with hash. It doesn't explicitly log tx count in block summary.
    # We'll estimate or if we logged tx count. 
    # For now, let's use Block Throughput = Blocks / Second.
    bps = total_blocks / duration if duration > 0 else 0
    print(f"Block Throughput: {bps:.4f} blocks/sec")

    # 4. Latency (Propagation)
    # Match "Block Mined" with "Block Received" for same hash?
    # Details format: "Block {index} Hash {hash}"
    # We need to extract Hash.
    
    # Extract Hash
    df["Hash"] = df["Details"].apply(lambda x: x.split("Hash ")[1] if "HashVal" in x or "Hash " in x else None)
    
    mined_events = df[df["Event"] == "Block Mined"].dropna(subset=["Hash"])
    received_events = df[df["Event"] == "Block Received"].dropna(subset=["Hash"])
    
    latencies = []
    
    for _, mined in mined_events.iterrows():
        block_hash = mined["Hash"]
        mine_time = mined["Timestamp"]
        
        # Find reception of this block
        receptions = received_events[received_events["Hash"] == block_hash]
        for _, rx in receptions.iterrows():
            latency = rx["Timestamp"] - mine_time
            if latency > 0: # Clock skew might make it negative in real distrib, but here local docker
                latencies.append(latency)
                
    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    print(f"Average Block Propagation Latency: {avg_latency:.6f} seconds")

    # 5. Speedup and Efficiency (Requires Baseline)
    # We hardcode a baseline or ask user?
    # Let's assume baseline T_seq for X blocks ~ X * (Difficulty_Constant)
    # For reporting, we generate a plot with dummy comparison if only 1 run, 
    # or just report current performance.
    
    # Generate Plots
    plt.figure(figsize=(10, 6))
    
    # Plot 1: Blocks Mined over Time
    mined_blocks = mined_blocks.sort_values("Timestamp")
    mined_blocks["Elapsed"] = mined_blocks["Timestamp"] - start_time
    mined_blocks["BlockCount"] = range(1, len(mined_blocks) + 1)
    
    plt.plot(mined_blocks["Elapsed"], mined_blocks["BlockCount"], marker='o')
    plt.xlabel("Time (s)")
    plt.ylabel("Blocks Mined")
    plt.title("Blockchain Growth")
    plt.grid(True)
    plt.savefig("logs/growth_plot.png")
    print("Plot saved to logs/growth_plot.png")

if __name__ == "__main__":
    analyze()
