@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
 echo [ERRO] Execute INSTALAR.bat primeiro.
 pause
 exit /b 1
)
if not exist "project_path.txt" (
 echo [ERRO] Execute INSTALAR.bat primeiro.
 pause
 exit /b 1
)
echo === DIAGNOSTICO DO BRIDGE ===
".venv\Scripts\python.exe" "bridge.py" doctor --project-file "project_path.txt"
echo.
echo === TESTE MCP LOCAL (handshake real) ===
".venv\Scripts\python.exe" "bridge.py" test-mcp --project-file "project_path.txt"
echo.
echo OBS: este teste valida a biblioteca MCP, nao confirma que Codex/Antigravity abriram o servidor.
pause
