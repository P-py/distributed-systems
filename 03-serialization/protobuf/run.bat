@echo off
rem Versao Windows do run.sh. Rode de dentro de 03-serialization\protobuf\: run.bat
setlocal enabledelayedexpansion
cd /d "%~dp0"

set "PROTOBUF_JAR=java\protobuf-java-3.6.1.jar"
set "VENV=..\.venv"

if not exist "%PROTOBUF_JAR%" (
    echo Baixe o protobuf-java 3.6.1 para %PROTOBUF_JAR%:
    echo   https://search.maven.org/remotecontent?filepath=com/google/protobuf/protobuf-java/3.6.1/protobuf-java-3.6.1.jar
    exit /b 1
)

rem O codigo gerado pelo protoc 3.6.1 monta os descritores em Python puro,
rem forma que o protobuf 4.x recusa: dai a versao fixa no runtime tambem.
set "PY=%VENV%\Scripts\python.exe"
if not exist "%PY%" (
    echo Criando o venv do modulo...
    python -m venv "%VENV%" || exit /b 1
)
"%PY%" -c "import google.protobuf" 2>nul || (
    echo Instalando o protobuf no venv...
    "%VENV%\Scripts\pip.exe" install -q "protobuf==3.20.3" || exit /b 1
)

rem O -cp precisa do diretorio das classes E do jar; no Windows o separador e ";".
set "CP=java;%PROTOBUF_JAR%"

javac -cp "%PROTOBUF_JAR%" -d java java\*.java || exit /b 1

echo === 1/4: Python serializa e imprime o base64 ===
for /f "delims=" %%i in ('"%PY%" python\MyApp.py') do set "B64_PYTHON=%%i"
echo !B64_PYTHON!

echo.
echo === 2/4: Java le o stream de amostra da constante ===
java -cp "%CP%" MyApp

echo.
echo === 3/4: Java le o base64 gerado agora pelo Python ===
java -cp "%CP%" MyApp "!B64_PYTHON!"

echo.
echo === 4/4: Python le o mesmo base64 ===
"%PY%" python\MyApp.py "!B64_PYTHON!"

endlocal
