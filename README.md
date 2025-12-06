# Distributed PoW Blockchain Simulation

This project simulates a distributed Proof-of-Work blockchain network using Python, gRPC, and Docker. It allows you to analyze network performance, scalability, and consensus metrics.

## Prerequisites

- [Docker](https://www.docker.com/) and Docker Compose
- Python 3.9+
- Recommended: Create a virtual environment (`python -m venv venv` and `source venv/bin/activate` or `venv\Scripts\activate`)

## Setup

1.  **Install Dependencies:**
    ```bash
    pip install grpcio grpcio-tools pandas matplotlib
    ```

2.  **Generate gRPC Code:**
    ```bash
    python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. protos/blockchain.proto
    ```
    *(Note: This is also done automatically inside the Docker containers)*

## Running the Simulation

1.  **Generate Network Configuration:**
    Run the orchestrator tool to create a network with `N` nodes (e.g., 3).
    ```bash
    python tools/generate_network.py 3
    ```

2.  **Start the Network:**
    Build and start the Docker containers.
    ```bash
    docker-compose up --build
    ```
    *Open a new terminal for the next steps.*

3.  **Inject Transactions (Client):**
    Run the client to send transactions to a node (default sends 10 txs).
    ```bash
    # Linux/Mac
    export TARGET_NODE=localhost:50051
    python src/client.py 
    
    # Windows (Powershell)
    $env:TARGET_NODE="localhost:50051"
    python src/client.py
    ```
    You can run this multiple times or against different ports (mapped by docker-compose, but we used internal networking. **Important**: By default, `docker-compose` might not map ports to host unless specified. My script didn't map ports to host to avoid conflicts, so the client needs to run **inside** the docker network or we need to update `generate_network.py` to map ports if running client locally.
    
    *Correction*: The current `generate_network.py` does NOT map ports to host. To run the client locally, you need to map ports or run the client in a container.
    
    **Option A: Run Client in Docker (Recommended)**
    ```bash
    docker run --network blockchain-simulation-with-grpc_blockchain-net --env TARGET_NODE=node_1:50051 -v $(pwd):/app python:3.9-slim sh -c "pip install grpcio protobuf && python /app/src/client.py"
    ```
    *Simpler*: Just exec into a node (Gunakan ini jika tidak ingin membuat docker baru di terminal baru).
    ```bash
    docker exec -it node_1 python src/client.py
    ```

4.  **Simulate Node Failure:**
    Stop a specific container to simulate a crash.
    ```bash
    docker stop node_2
    ```

5.  **Stop Simulation:**
    ```bash
    docker-compose down
    ```

## Analyzing Results

The simulation logs are saved to `logs/simulation_data.csv`.

1.  **Run Analysis:**
    ```bash
    python tools/analyze_results.py
    ```
    Calculates Speedup, Throughput, Latency, and saves a plot to `logs/growth_plot.png`.

## Project Structure

- `src/node.py`: Blockchain node logic (Mining, gRPC Server/Client).
- `src/client.py`: Transaction generator.
- `protos/blockchain.proto`: Protocol buffer definitions.
- `tools/generate_network.py`: Creates `docker-compose.yml`.
- `tools/analyze_results.py`: Metrics calculation.
