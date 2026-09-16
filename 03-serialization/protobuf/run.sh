#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

mkdir -p java python

echo "=== Teste 1: gerar o código Java ==="
echo "protoc --java_out=java MyApp.proto"
protoc --java_out=java MyApp.proto
ls java

echo
echo "=== Teste 2: gerar o código Python ==="
echo "protoc --python_out=python MyApp.proto"
protoc --python_out=python MyApp.proto
ls python
