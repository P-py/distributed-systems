#!/usr/bin/env bash
set -euo pipefail
# Roteiro de verificação: o Python serializa o Person com o Protocol Buffers e
# o Java recupera o mesmo objeto a partir do base64.
cd "$(dirname "$0")"

PROTOBUF_JAR="java/protobuf-java-3.6.1.jar"
PROTOBUF_URL="https://search.maven.org/remotecontent?filepath=com/google/protobuf/protobuf-java/3.6.1/protobuf-java-3.6.1.jar"
VENV="../.venv"

if [ ! -f "$PROTOBUF_JAR" ]; then
    echo "Baixando o protobuf-java (mesma versão do protoc que gerou o código)..."
    curl -sSL -o "$PROTOBUF_JAR" "$PROTOBUF_URL"
fi

# O código gerado pelo protoc 3.6.1 monta os descritores em Python puro, forma
# que o protobuf 4.x recusa: daí a versão fixa no runtime também.
if [ ! -x "$VENV/bin/python" ]; then
    echo "Criando o venv do módulo..."
    python3 -m venv "$VENV"
fi
PY="$VENV/bin/python"
if ! "$PY" -c "import google.protobuf" 2>/dev/null; then
    echo "Instalando o protobuf no venv..."
    "$VENV/bin/pip" install -q "protobuf==3.20.3"
fi

# O -cp precisa do diretório das classes E do jar do protobuf.
CP="java:$PROTOBUF_JAR"

javac -cp "$PROTOBUF_JAR" -d java java/*.java

echo "=== 1/4: Python serializa e imprime o base64 ==="
B64_PYTHON=$("$PY" python/MyApp.py)
echo "$B64_PYTHON"

echo
echo "=== 2/4: Java lê o stream de amostra da constante ==="
java -cp "$CP" MyApp

echo
echo "=== 3/4: Java lê o base64 gerado agora pelo Python ==="
java -cp "$CP" MyApp "$B64_PYTHON"

echo
echo "=== 4/4: Python lê o mesmo base64 ==="
"$PY" python/MyApp.py "$B64_PYTHON"
