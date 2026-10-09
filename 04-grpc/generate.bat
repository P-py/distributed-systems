@echo off
rem Versao Windows do generate.sh.
setlocal
cd /d "%~dp0"

set "PY=.venv\Scripts\python.exe"

echo python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. contact_book.proto
"%PY%" -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. contact_book.proto || exit /b 1
dir /b contact_book_pb2.py contact_book_pb2_grpc.py

endlocal
