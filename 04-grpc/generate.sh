#!/usr/bin/env bash
set -euo pipefail
# Gera as mensagens e os stubs do serviço com o protoc do grpcio-tools.
cd "$(dirname "$0")"

PY=".venv/bin/python"

echo "python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. contact_book.proto"
"$PY" -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. contact_book.proto
ls contact_book_pb2.py contact_book_pb2_grpc.py
