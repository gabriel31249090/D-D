$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location -LiteralPath (Join-Path $projectRoot 'frontend')
try {
    Write-Host "Inicializando o Frontend ARCANUM (Vite / React 19)..." -ForegroundColor Cyan
    Write-Host "URL: http://localhost:5173" -ForegroundColor Green
    npm run dev
} finally {
    Pop-Location
}
