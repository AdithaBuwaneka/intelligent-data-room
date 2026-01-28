# Hugging Face Deployment Script
# Usage: .\deploy_hf.ps1 YOUR_USERNAME

param(
    [Parameter(Mandatory=$true)]
    [string]$HFUsername
)

$SpaceName = "intelligent-data-room"
$HFRepo = "https://huggingface.co/spaces/$HFUsername/$SpaceName"

Write-Host "Deploying to Hugging Face Spaces" -ForegroundColor Cyan
Write-Host ""
Write-Host "Deploying to: $HFRepo" -ForegroundColor Yellow
Write-Host ""

# Check if git remote exists
$remoteExists = git remote get-url hf 2>$null
if ($remoteExists) {
    Write-Host "HF remote already exists" -ForegroundColor Green
} else {
    Write-Host "Adding HF remote..." -ForegroundColor Yellow
    git remote add hf $HFRepo
}

# Copy README for HF Space
Write-Host "Preparing README..." -ForegroundColor Yellow
Copy-Item README_HF_SPACE.md README.md -Force

# Check required files
Write-Host "Checking files..." -ForegroundColor Green
if (!(Test-Path "Dockerfile")) {
    Write-Host "Error: Dockerfile not found" -ForegroundColor Red
    exit 1
}

if (!(Test-Path "backend")) {
    Write-Host "Error: backend directory not found" -ForegroundColor Red
    exit 1
}

# Stage files
Write-Host "Staging files..." -ForegroundColor Yellow
git add Dockerfile .dockerignore backend/ README.md

# Commit
Write-Host "Committing..." -ForegroundColor Yellow
try {
    git commit -m "Deploy to Hugging Face Spaces"
} catch {
    Write-Host "No changes to commit" -ForegroundColor Gray
}

# Push
Write-Host "Pushing to Hugging Face..." -ForegroundColor Cyan
git push hf main

Write-Host ""
Write-Host "Deployment initiated!" -ForegroundColor Green
Write-Host ""
Write-Host "Your Space: https://huggingface.co/spaces/$HFUsername/$SpaceName" -ForegroundColor Cyan
Write-Host "Docs: https://$HFUsername-$SpaceName.hf.space/docs" -ForegroundColor Cyan
Write-Host "Health: https://$HFUsername-$SpaceName.hf.space/health" -ForegroundColor Cyan
Write-Host ""
Write-Host "Build will take 5-10 minutes" -ForegroundColor Yellow
Write-Host "Add secrets in Space Settings!" -ForegroundColor Yellow
Write-Host ""
