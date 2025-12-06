import argparse
import sys

def generate_compose(num_nodes):
    services = ""
    node_ports = []
    
    # We use internal docker dns names: node_1, node_2...
    # All nodes listen on 50051 inside container
    
    peer_list = ",".join([f"node_{i}:50051" for i in range(1, num_nodes + 1)])
    
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
    
    print(f"Generated docker-compose.yml for {num_nodes} nodes.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python generate_network.py <num_nodes>")
        sys.exit(1)
    
    try:
        n = int(sys.argv[1])
        generate_compose(n)
    except ValueError:
        print("Error: Number of nodes must be an integer.")
