#!/usr/bin/env bash
set -euo pipefail
# Sobe o servidor em segundo plano, roda o cliente e mostra o log do servidor.
cd "$(dirname "$0")"

PY=".venv/bin/python"

if [ ! -x "$PY" ]; then
    echo "Criando o venv do módulo e instalando o grpcio..."
    python3 -m venv .venv
    .venv/bin/pip install -q grpcio grpcio-tools
fi

if [ ! -f contact_book_pb2_grpc.py ]; then
    ./generate.sh
fi

"$PY" -u server.py > server.log 2>&1 &
SERVIDOR=$!
trap 'kill "$SERVIDOR" 2>/dev/null || true' EXIT

"$PY" client.py

echo
echo "=== log do servidor ==="
cat server.log
