param([switch]$PrepareOnly)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonExecutable = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonExecutable)) { throw 'Configure o ambiente Python do projeto primeiro.' }
Push-Location -LiteralPath $projectRoot
try {
    $buildArguments = @('packaging/build_windows.py')
    if ($PrepareOnly) { $buildArguments += '--prepare-only' }
    & $pythonExecutable @buildArguments
    if ($LASTEXITCODE -ne 0) { throw 'A criação do instalador falhou.' }
} finally { Pop-Location }

