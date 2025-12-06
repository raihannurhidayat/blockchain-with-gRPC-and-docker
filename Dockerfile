FROM python:3.9-slim

WORKDIR /app

# Install system dependencies if any (none really needed for basic python)
# RUN apt-get update && apt-get install -y gcc

# Install python dependencies
RUN pip install grpcio grpcio-tools pandas matplotlib

# Copy project files
COPY . .

# Generate gRPC code inside image to be safe
RUN python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. protos/blockchain.proto

# Set python path
ENV PYTHONPATH=/app

CMD ["python", "src/node.py"]
