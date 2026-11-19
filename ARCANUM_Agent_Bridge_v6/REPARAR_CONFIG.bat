@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
 echo [ERRO] Execute INSTALAR.bat primeiro.
 pause
 exit /b 1
)
".venv\Scripts\python.exe" "bootstrap.py"
if errorlevel 1 (echo [ERRO] Reparo nao concluido.) else (echo [OK] Configuracoes revisadas.)
pause
