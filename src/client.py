import sys
import os
import time
import uuid
import random
import grpc

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import protos.blockchain_pb2 as pb2
import protos.blockchain_pb2_grpc as pb2_grpc

def run():
    target_node = os.environ.get('TARGET_NODE', 'localhost:50051')
    num_tx = int(os.environ.get('NUM_TX', '10'))
    
    print(f"Client connecting to {target_node}, sending {num_tx} transactions...")
    
    with grpc.insecure_channel(target_node) as channel:
        stub = pb2_grpc.BlockchainNodeStub(channel)
        
        for i in range(num_tx):
            tx_id = str(uuid.uuid4())
            tx = pb2.Transaction(
                id=tx_id,
                sender=f"Client",
                receiver=f"Recipient_{random.randint(1,100)}",
                amount=random.uniform(1, 100),
                timestamp=time.time()
            )
            try:
                response = stub.SubmitTransaction(tx)
                print(f"Sent Tx {i+1}/{num_tx}: {response.message}")
            except grpc.RpcError as e:
                print(f"RPC failed: {e}")
            
            time.sleep(0.1) # Throttle slightly

if __name__ == '__main__':
    run()
