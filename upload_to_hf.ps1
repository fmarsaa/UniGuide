# UniGuide HF Spaces Upload Script
# Run this from the repo root: powershell -File upload_to_hf.ps1

$HF_USERNAME = "fatmaom"
$MODEL_REPO  = "$HF_USERNAME/uniguide-model"
$SPACE_REPO  = "$HF_USERNAME/uniguide-backend"
$BACKEND_DIR = ".\backend"
$HF_DIR      = ".\hf_space"

Write-Host "=== Step 1: Upload model to HF Hub ===" -ForegroundColor Cyan
Write-Host "This uploads the 2.17 GB model file. It may take 10-20 minutes depending on your internet speed."
huggingface-cli upload $MODEL_REPO `
  "$BACKEND_DIR\rf_model_pipeline.pkl" `
  rf_model_pipeline.pkl `
  --repo-type model

Write-Host ""
Write-Host "=== Step 2: Clone and push Space ===" -ForegroundColor Cyan
$tmpDir = "$env:TEMP\uniguide-hf-space"
if (Test-Path $tmpDir) { Remove-Item -Recurse -Force $tmpDir }
git clone "https://huggingface.co/spaces/$SPACE_REPO" $tmpDir

# Copy Dockerfile and README
Copy-Item "$HF_DIR\Dockerfile" "$tmpDir\Dockerfile" -Force
Copy-Item "$HF_DIR\README.md"  "$tmpDir\README.md"  -Force

# Copy backend Python files + requirements
Copy-Item "$BACKEND_DIR\*.py"          "$tmpDir\" -Force
Copy-Item "$BACKEND_DIR\requirements.txt" "$tmpDir\" -Force

# Copy data directory if present (catalogue JSON etc.)
if (Test-Path "$BACKEND_DIR\data") {
    Copy-Item "$BACKEND_DIR\data" "$tmpDir\data" -Recurse -Force
}

Set-Location $tmpDir
git add .
git commit -m "Deploy UniGuide backend to HF Spaces"
git push

Write-Host ""
Write-Host "=== Done! ===" -ForegroundColor Green
Write-Host "Your Space is building at: https://huggingface.co/spaces/$SPACE_REPO"
Write-Host "API will be live at: https://$HF_USERNAME-uniguide-backend.hf.space/api/health"
Write-Host ""
Write-Host "MODEL SHA256 (copy this into HF Space Secrets as MODEL_SHA256):"
Write-Host "4dbc2ba52e7ee67376f200c5045e4ce47db02e33f59666a4b10ae9cb6867ecec" -ForegroundColor Yellow
Write-Host ""
Write-Host "MODEL_URL (copy into HF Space Secrets as MODEL_URL):"
Write-Host "https://huggingface.co/$MODEL_REPO/resolve/main/rf_model_pipeline.pkl" -ForegroundColor Yellow
