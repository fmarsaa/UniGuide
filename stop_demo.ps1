# Stops the UniGuide demo backend and portal started by start_demo.ps1. Only Python
# processes running the backend (uvicorn main:app) or the portal (http.server) are
# stopped; other Python programs are left alone.
#
#     powershell -ExecutionPolicy Bypass -File stop_demo.ps1

$targets = Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" |
    Where-Object { $_.CommandLine -match "uvicorn\s+main:app" -or $_.CommandLine -match "http\.server\s+5000" }
foreach ($p in $targets) {
    Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
    Write-Host "Stopped python process $($p.ProcessId): $($p.CommandLine)"
}
if (-not $targets) { Write-Host "No demo backend or portal was running." }
