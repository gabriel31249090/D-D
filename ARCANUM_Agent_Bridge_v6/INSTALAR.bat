@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
chcp 65001 >nul 2>nul
color 0B
echo.
echo ============================================
echo    ARCANUM AGENT BRIDGE 6.0 - INSTALACAO
echo ============================================
echo.
if not exist ".venv\Scripts\python.exe" (
  echo [1/4] Criando ambiente Python...
  py -3.12 -m venv ".venv" >nul 2>nul
  if errorlevel 1 py -3 -m venv ".venv" >nul 2>nul
  if errorlevel 1 python -m venv ".venv" >nul 2>nul
)
if not exist ".venv\Scripts\python.exe" (
  echo [ERRO] Python 3.11+ ou Python Launcher nao encontrado.
  echo Teste no PowerShell: py -3.12 --version
  goto fail
)
echo [2/4] Verificando Python...
".venv\Scripts\python.exe" --version
if errorlevel 1 goto fail
echo [3/4] Instalando dependencias...
".venv\Scripts\python.exe" -m pip install -r "requirements.txt"
if errorlevel 1 goto fail
echo [4/4] Configurando servidores MCP com backup...
".venv\Scripts\python.exe" "bootstrap.py"
if errorlevel 1 goto fail
echo.
echo [OK] Instalacao finalizada.
echo Abra ABRIR_PAINEL.bat para iniciar o monitoramento.
echo.
pause
exit /b 0
:fail
echo.
echo Instalacao interrompida. Nada foi apagado.
pause
exit /b 1
