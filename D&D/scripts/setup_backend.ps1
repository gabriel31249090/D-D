$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location -LiteralPath $projectRoot
try {
    $pythonExecutable = Join-Path $projectRoot '.venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $pythonExecutable)) {
        $installedPython = Join-Path $env:LOCALAPPDATA 'Programs\Python\Python312\python.exe'
        if (Test-Path -LiteralPath $installedPython) {
            & $installedPython -m venv .venv
        } else {
            & py -3.12 -m venv .venv
        }
        if ($LASTEXITCODE -ne 0) { throw 'Python 3.12 is required.' }
    }
    & $pythonExecutable -m pip install -e '.[dev]'
    if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
    & $pythonExecutable -m alembic upgrade head
    if ($LASTEXITCODE -ne 0) { throw 'Migration failed.' }
    & $pythonExecutable -m pytest
    if ($LASTEXITCODE -ne 0) { throw 'Tests failed.' }
    Write-Host 'Backend ready. Run scripts/run_api.ps1 to open http://127.0.0.1:8000/docs'
} finally {
    Pop-Location
}

