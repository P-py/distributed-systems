#!/usr/bin/env bash
set -euo pipefail
# Regenera o código do Person a partir da IDL, para Java e para Python.
cd "$(dirname "$0")"

mkdir -p java python

echo "=== 1/2: gerar o código Java ==="
echo "protoc --java_out=java MyApp.proto"
protoc --java_out=java MyApp.proto
ls java

echo
echo "=== 2/2: gerar o código Python ==="
echo "protoc --python_out=python MyApp.proto"
protoc --python_out=python MyApp.proto
ls python
