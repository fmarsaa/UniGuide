# Starts the UniGuide demo on this laptop: backend on port 8000 (v4 model) and the admin
# web portal on port 5000, both reachable from a phone on the same hotspot.
#
#     powershell -ExecutionPolicy Bypass -File start_demo.ps1
#
# Stop everything with stop_demo.ps1. Output goes to logs\demo_backend*.log and
# logs\demo_portal*.log.

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
$Backend = Join-Path $Root "backend"
$Portal = Join-Path $Root "flutter_app\build\web_demo"
$Logs = Join-Path $Root "logs"

if (-not (Test-Path (Join-Path $Backend "uniguide_xgb_v4.joblib"))) { throw "backend\uniguide_xgb_v4.joblib is missing." }
if (-not (Test-Path (Join-Path $Portal "index.html"))) { throw "The portal build is missing: $Portal" }

$env:OPENBLAS_NUM_THREADS = "1"
$env:OMP_NUM_THREADS = "1"
$env:MKL_NUM_THREADS = "1"
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUNBUFFERED = "1"

& (Join-Path $Root "stop_demo.ps1")

$ip = Get-NetIPConfiguration |
    Where-Object { $_.IPv4DefaultGateway -and $_.NetAdapter.Status -eq "Up" } |
    Sort-Object { if ($_.InterfaceAlias -like "*Wi*Fi*") { 0 } else { 1 } } |
    Select-Object -First 1 -ExpandProperty IPv4Address |
    Select-Object -First 1 -ExpandProperty IPAddress
if (-not $ip) { throw "No network connection found. Connect the laptop to the phone's hotspot first." }

$env:CORS_ORIGINS = "http://${ip}:5000"

Start-Process -FilePath "python" -WorkingDirectory $Backend -WindowStyle Hidden `
    -ArgumentList "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000" `
    -RedirectStandardOutput (Join-Path $Logs "demo_backend.log") `
    -RedirectStandardError (Join-Path $Logs "demo_backend_err.log")
Start-Process -FilePath "python" -WorkingDirectory $Root -WindowStyle Hidden `
    -ArgumentList "-m", "http.server", "5000", "--bind", "0.0.0.0", "--directory", $Portal `
    -RedirectStandardOutput (Join-Path $Logs "demo_portal.log") `
    -RedirectStandardError (Join-Path $Logs "demo_portal_err.log")

Write-Host "Waiting for the backend to load the model..."
$health = $null
for ($i = 0; $i -lt 45 -and -not $health; $i++) {
    Start-Sleep -Seconds 2
    try { $health = Invoke-RestMethod -Uri "http://${ip}:8000/api/health" -TimeoutSec 3 } catch { }
}

Write-Host ""
Write-Host "Laptop IP on this network : $ip"
Write-Host "Server address for the app: http://${ip}:8000"
Write-Host "Admin portal on the phone : http://${ip}:5000"
if ($health) {
    Write-Host "Health check              : status=$($health.status) model_loaded=$($health.model_loaded) model_version=$($health.model_version) firestore_configured=$($health.firestore_configured)"
} else {
    Write-Host "Health check              : NO ANSWER after 90 s - see logs\demo_backend_err.log"
}
