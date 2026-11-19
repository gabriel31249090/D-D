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
".venv\Scripts\python.exe" "bridge.py" dashboard --project-file "project_path.txt" --port 8765
if errorlevel 1 (
 echo.
 echo [ERRO] O painel nao conseguiu iniciar. Veja a mensagem acima.
 pause
)
