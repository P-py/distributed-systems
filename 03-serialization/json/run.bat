@echo off
rem Os 4 testes do roteiro, versao Windows. Rode de dentro do json\: run.bat
setlocal enabledelayedexpansion
cd /d "%~dp0"

set "GSON_JAR=java\gson-2.13.1.jar"

if not exist "%GSON_JAR%" (
    echo Baixe o Gson 2.13.1 para %GSON_JAR%:
    echo   https://search.maven.org/remotecontent?filepath=com/google/code/gson/gson/2.13.1/gson-2.13.1.jar
    exit /b 1
)

rem O -cp precisa do diretorio das classes E do jar; no Windows o separador e ";".
set "CP=java;%GSON_JAR%"

javac -cp "%GSON_JAR%" -d java java\*.java || exit /b 1

echo === Teste 1: Java gera o JSON ===
for /f "delims=" %%i in ('java -cp "%CP%" MyApp') do set "JSON_JAVA=%%i"
echo !JSON_JAVA!

echo.
echo === Teste 2: Python gera o JSON ===
for /f "delims=" %%i in ('python python\MyApp.py') do set "JSON_PYTHON=%%i"
echo !JSON_PYTHON!

rem As aspas do JSON precisam ser escapadas com \" para atravessar o cmd inteiras.
set "ARG_JAVA=!JSON_JAVA:"=\"!"
set "ARG_PYTHON=!JSON_PYTHON:"=\"!"

echo.
echo === Teste 3: JSON do Java lido pelo Python ===
python python\MyApp.py "!ARG_JAVA!"

echo.
echo === Teste 4: JSON do Python lido pelo Java ===
java -cp "%CP%" MyApp "!ARG_PYTHON!"

endlocal
