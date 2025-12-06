import sys
import os
import time
import hashlib
import json
import threading
import socket
import csv
import logging
import random
from concurrent import futures

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import grpc
import protos.blockchain_pb2 as pb2
import protos.blockchain_pb2_grpc as pb2_grpc

# Configuration
DIFFICULTY = 4  # Number of leading zeros
LOG_FILE = "/logs/simulation_data.csv"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class InternalBlock:
    def __init__(self, index, previous_hash, timestamp, transactions, nonce=0, hash_val=""):
        self.index = index
        self.previous_hash = previous_hash
        self.timestamp = timestamp
        self.transactions = transactions
        self.nonce = nonce
        self.hash = hash_val or self.calculate_hash()

    def calculate_hash(self):
        tx_str = json.dumps([t.__str__() for t in self.transactions], sort_keys=True)
        block_string = f"{self.index}{self.previous_hash}{self.timestamp}{tx_str}{self.nonce}"
        return hashlib.sha256(block_string.encode()).hexdigest()

    def to_proto(self, miner_id):
        proto_txs = []
        for t in self.transactions:
            proto_txs.append(pb2.Transaction(
                id=t['id'], sender=t['sender'], receiver=t['receiver'], 
                amount=t['amount'], timestamp=t['timestamp']
            ))
        return pb2.Block(
            index=self.index, previous_hash=self.previous_hash, timestamp=self.timestamp,
            transactions=proto_txs, nonce=self.nonce, hash=self.hash, 
            miner_id=miner_id, difficulty=DIFFICULTY
        )

class BlockchainNode(pb2_grpc.BlockchainNodeServicer):
    def __init__(self, node_id, port, peers):
        self.node_id = node_id
        self.port = port
        self.peers = peers  # List of "host:port" strings
        self.chain = [self.create_genesis_block()]
        self.pending_transactions = []
        self.lock = threading.Lock()
        self.mining_event = threading.Event()
        self.stop_event = threading.Event()
        
        self.log_event("Node Started", f"Node {node_id} started on port {port}")

    def create_genesis_block(self):
        return InternalBlock(0, "0", time.time(), [], 0, "00000000000000000000000000000000")

    def log_event(self, event_type, details=""):
        try:
            with open(LOG_FILE, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([time.time(), self.node_id, event_type, details])
        except Exception as e:
            logging.error(f"Failed to log event: {e}")

    # --- gRPC Methods ---
    def SubmitTransaction(self, request, context):
        tx = {
            'id': request.id, 'sender': request.sender, 'receiver': request.receiver,
            'amount': request.amount, 'timestamp': request.timestamp
        }
        with self.lock:
            if tx not in self.pending_transactions:
                self.pending_transactions.append(tx)
                self.log_event("Transaction Received", f"Tx {tx['id']} from {tx['sender']}")
                # Broadcast to peers
                threading.Thread(target=self.broadcast_transaction, args=(request,)).start()
        return pb2.Ack(success=True, message="Transaction added to pool")

    def BroadcastBlock(self, request, context):
        block_hash = request.hash
        with self.lock:
            if block_hash == self.chain[-1].hash:
                return pb2.Ack(success=True, message="Block already exists")
            if request.index <= self.chain[-1].index:
                return pb2.Ack(success=False, message="Block index too low")
            
            # Simple validation (check hash difficulty)
            if not request.hash.startswith('0' * DIFFICULTY):
                 return pb2.Ack(success=False, message="Invalid PoW")

            # In a real blockchain, we'd validate transactions and previous hash heavily
            # Here we accept longest chain
            
            logging.info(f"Received block {request.index} from {request.miner_id}")
            self.log_event("Block Received", f"Block {request.index} Hash {request.hash[:8]}")

            # Reconstruct internal block
            txs = []
            for t in request.transactions:
                txs.append({'id': t.id, 'sender': t.sender, 'receiver': t.receiver,
                           'amount': t.amount, 'timestamp': t.timestamp})
            
            new_block = InternalBlock(
                request.index, request.previous_hash, request.timestamp,
                txs, request.nonce, request.hash
            )
            
            self.chain.append(new_block)
            
            # Remove confirmed txs from pending
            for tx in txs:
                self.pending_transactions = [p for p in self.pending_transactions if p['id'] != tx['id']]
            
            # Restart mining
            self.mining_event.set() 
            
        return pb2.Ack(success=True, message="Block accepted")

    def BroadcastTransaction(self, request, context):
        # Same as SubmitTransaction basically, but this is node-to-node
        return self.SubmitTransaction(request, context)

    # --- Networking ---
    def broadcast_transaction(self, tx_proto):
        for peer in self.peers:
            try:
                with grpc.insecure_channel(peer) as channel:
                    stub = pb2_grpc.BlockchainNodeStub(channel)
                    stub.BroadcastTransaction(tx_proto)
            except:
                pass # Peer might be down

    def broadcast_block(self, block_proto):
        for peer in self.peers:
            try:
                with grpc.insecure_channel(peer) as channel:
                    stub = pb2_grpc.BlockchainNodeStub(channel)
                    stub.BroadcastBlock(block_proto)
            except:
                pass


    # --- Mining Loop ---
    def mine(self):
        logging.info("Mining started...")
        while not self.stop_event.is_set():
            self.mining_event.clear()
            
            with self.lock:
                last_block = self.chain[-1]
                # Deep copy pending txs to mine
                txs_to_mine = list(self.pending_transactions)
            
            new_index = last_block.index + 1
            new_timestamp = time.time()
            new_nonce = 0
            
            # Mining (PoW)
            while not self.mining_event.is_set():
                # Check simple condition to stop wasteful compute if chain updated
                
                temp_block = InternalBlock(new_index, last_block.hash, new_timestamp, txs_to_mine, new_nonce)
                if temp_block.hash.startswith('0' * DIFFICULTY):
                    # Block Found!
                    with self.lock:
                        # Double check we haven't been beaten
                        if self.chain[-1].index >= new_index:
                            break 
                        
                        logging.info(f"Block {new_index} mined! Hash: {temp_block.hash}")
                        self.log_event("Block Mined", f"Block {new_index} Hash {temp_block.hash[:8]}")
                        self.chain.append(temp_block)
                        
                        # Remove mined txs
                        for tx in txs_to_mine:
                            self.pending_transactions = [p for p in self.pending_transactions if p['id'] != tx['id']]

                        # Broadcast
                        proto_block = temp_block.to_proto(self.node_id)
                        threading.Thread(target=self.broadcast_block, args=(proto_block,)).start()
                    
                    break # Restart loop for next block
                
                new_nonce += 1
                if new_nonce % 10000 == 0:
                     # Yield to allow thread switch or event check
                     time.sleep(0.001)

def serve():
    node_id = os.environ.get('NODE_ID', 'node_1')
    port = os.environ.get('PORT', '50051')
    peers_str = os.environ.get('PEERS', '') # Comma separated
    peers = [p for p in peers_str.split(',') if p]
    
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    node = BlockchainNode(node_id, port, peers)
    pb2_grpc.add_BlockchainNodeServicer_to_server(node, server)
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    
    # Start mining thread
    miner_thread = threading.Thread(target=node.mine)
    miner_thread.start()
    
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)
        node.stop_event.set()
        miner_thread.join()

if __name__ == '__main__':
    # Initialize logs file header if not exists (only by one node or setup script)
    # Ideally should be done by orchestrator, but we can check if empty
    if not os.path.exists(LOG_FILE):
         # This is racey in docker, but let's assume orchestrator handles or we append
         pass
         
    serve()
