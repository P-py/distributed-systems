#!/usr/bin/env bash
set -euo pipefail
# Roteiro de verificação: compila o lado Java e troca o mesmo objeto
# entre Java e Python, nos dois sentidos.
cd "$(dirname "$0")"

GSON_JAR="java/gson-2.13.1.jar"
GSON_URL="https://search.maven.org/remotecontent?filepath=com/google/code/gson/gson/2.13.1/gson-2.13.1.jar"

if [ ! -f "$GSON_JAR" ]; then
    echo "Baixando o Gson..."
    curl -sSL -o "$GSON_JAR" "$GSON_URL"
fi

# O -cp precisa do diretório das classes E do jar.
CP="java:$GSON_JAR"

javac -cp "$GSON_JAR" -d java java/*.java

echo "=== 1/4: Java gera o JSON ==="
JSON_JAVA=$(java -cp "$CP" MyApp)
echo "$JSON_JAVA"

echo
echo "=== 2/4: Python gera o JSON ==="
JSON_PYTHON=$(python3 python/MyApp.py)
echo "$JSON_PYTHON"

echo
echo "=== 3/4: JSON do Java lido pelo Python ==="
python3 python/MyApp.py "$JSON_JAVA"

echo
echo "=== 4/4: JSON do Python lido pelo Java ==="
java -cp "$CP" MyApp "$JSON_PYTHON"
