import argparse
import sys

def generate_compose(num_nodes):
    services = ""
    if num_nodes < 1:
        print("Error: Jumlah node minimal 1.")
        sys.exit(1)

    print(f"[*] Menyiapkan konfigurasi untuk {num_nodes} node...")

    for i in range(1, num_nodes + 1):
        node_id = f"node_{i}"
        # Peers for this node: all others
        my_peers = ",".join([f"node_{j}:50051" for j in range(1, num_nodes + 1) if j != i])
        
        services += f"""
  {node_id}:
    build: .
    container_name: {node_id}
    environment:
      - NODE_ID={node_id}
      - PORT=50051
      - PEERS={my_peers}
      - PYTHONUNBUFFERED=1
    volumes:
      - ./logs:/logs
    networks:
      - blockchain-net
"""

    compose_content = f"""version: '3.8'

services:{services}

networks:
  blockchain-net:
    driver: bridge
"""
    
    with open("docker-compose.yml", "w") as f:
        f.write(compose_content)
    
    print(f"[SUCCESS] Berhasil membuat docker-compose.yml dengan {num_nodes} node.")
    print(f"          Mode: {'SEQUENTIAL' if num_nodes == 1 else 'PARALLEL'}")


def main():
    parser = argparse.ArgumentParser(description="Generator Network Blockchain untuk Simulasi")
    subparsers = parser.add_subparsers(dest='command', help='Pilih mode operasi', required=True)

    # Command: python tools/generate_network.py sequential
    parser_seq = subparsers.add_parser('sequential', help='Mode Sekuensial (Hanya 1 Node)')

    # Command: python tools/generate_network.py parallel --nodes 4
    parser_par = subparsers.add_parser('parallel', help='Mode Paralel (Multi Node)')
    parser_par.add_argument('--nodes', type=int, default=2, help='Jumlah node (default: 2)')

    args = parser.parse_args()

    if args.command == 'sequential':
        generate_compose(1)
    elif args.command == 'parallel':
        if args.nodes < 2:
            print("Warning: Mode parallel biasanya membutuhkan minimal 2 node.")
            confirm = input("Lanjut dengan 1 node? (y/n): ")
            if confirm.lower() != 'y':
                sys.exit(0)
        generate_compose(args.nodes)

if __name__ == "__main__":
    main()