@echo off
setlocal
cd /d "%~dp0"

if not exist java mkdir java
if not exist python mkdir python

echo === 1/2: gerar o codigo Java ===
echo protoc --java_out=java MyApp.proto
protoc --java_out=java MyApp.proto || exit /b 1
dir /b java

echo.
echo === 2/2: gerar o codigo Python ===
echo protoc --python_out=python MyApp.proto
protoc --python_out=python MyApp.proto || exit /b 1
dir /b python

endlocal
