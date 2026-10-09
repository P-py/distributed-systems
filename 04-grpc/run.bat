@echo off
rem Versao Windows do run.sh: sobe o servidor em outra janela e roda o cliente.
setlocal
cd /d "%~dp0"

set "PY=.venv\Scripts\python.exe"

if not exist "%PY%" (
    echo Criando o venv do modulo e instalando o grpcio...
    python -m venv .venv || exit /b 1
    .venv\Scripts\pip.exe install -q grpcio grpcio-tools || exit /b 1
)

if not exist contact_book_pb2_grpc.py call generate.bat || exit /b 1

rem O cliente espera o servidor ficar pronto (grpc.channel_ready_future).
start "servidor gRPC" /min "%PY%" -u server.py
"%PY%" client.py
taskkill /FI "WINDOWTITLE eq servidor gRPC*" /T /F >nul 2>&1

endlocal
