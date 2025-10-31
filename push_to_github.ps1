# ===================================================================
# Athan Bot - Safe GitHub Push Script
# ===================================================================
# This script safely pushes your code to GitHub without exposing secrets
# ===================================================================

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ATHAN BOT - GitHub Push Script" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Security Check
Write-Host "[STEP 1/5] Running security checks..." -ForegroundColor Cyan
Write-Host ""

$safe = $true

# Check if .env is gitignored
if (Test-Path ".env") {
    $gitStatus = git status --short .env 2>$null
    if ($gitStatus) {
        Write-Host "[ERROR] .env will be committed! Add it to .gitignore!" -ForegroundColor Red
        $safe = $false
    } else {
        Write-Host "[OK] .env is properly gitignored" -ForegroundColor Green
    }
}

# Check if DISCORD_TOKEN.txt is gitignored
if (Test-Path "DISCORD_TOKEN.txt") {
    $gitStatus = git status --short DISCORD_TOKEN.txt 2>$null
    if ($gitStatus) {
        Write-Host "[ERROR] DISCORD_TOKEN.txt will be committed! Add it to .gitignore!" -ForegroundColor Red
        $safe = $false
    } else {
        Write-Host "[OK] DISCORD_TOKEN.txt is properly gitignored" -ForegroundColor Green
    }
}

# Check if data/ is gitignored
if (Test-Path "data") {
    $gitStatus = git status --short data/ 2>$null
    if ($gitStatus) {
        Write-Host "[ERROR] data/ will be committed! Add it to .gitignore!" -ForegroundColor Red
        $safe = $false
    } else {
        Write-Host "[OK] data/ is properly gitignored" -ForegroundColor Green
    }
}

Write-Host ""

if (-not $safe) {
    Write-Host "========================================" -ForegroundColor Red
    Write-Host " UNSAFE TO PUSH - Fix errors above!" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    exit 1
}

# Update README for GitHub
Write-Host "[STEP 2/5] Preparing README for GitHub..." -ForegroundColor Cyan
if (Test-Path "SETUP_GITHUB.md") {
    Copy-Item "README.md" "README_LOCAL_BACKUP.md" -Force
    Copy-Item "SETUP_GITHUB.md" "README.md" -Force
    Write-Host "[OK] README.md updated for GitHub" -ForegroundColor Green
}
Write-Host ""

# Git status
Write-Host "[STEP 3/5] Checking git status..." -ForegroundColor Cyan
git status
Write-Host ""

# Confirm with user
Write-Host "[STEP 4/5] Review the files above." -ForegroundColor Yellow
Write-Host ""
$confirm = Read-Host "Do you want to push to GitHub? (yes/no)"
Write-Host ""

if ($confirm -ne "yes") {
    Write-Host "[CANCELLED] Push cancelled by user" -ForegroundColor Yellow
    exit 0
}

# Add and commit
Write-Host "[STEP 5/5] Pushing to GitHub..." -ForegroundColor Cyan
Write-Host ""

git add .
git commit -m "Update: Athan Discord bot"

# Check if remote exists
$remoteExists = git remote get-url origin 2>$null
if (-not $remoteExists) {
    Write-Host "[SETUP] Adding remote repository..." -ForegroundColor Cyan
    git remote add origin https://github.com/S8nm/Athan.git
}

# Push
git push -u origin main 2>&1 | Tee-Object -Variable pushOutput

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  SUCCESS! Bot pushed to GitHub!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "View at: https://github.com/S8nm/Athan" -ForegroundColor Cyan
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host " PUSH FAILED - Check errors above" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    
    # Try master branch
    Write-Host "Trying 'master' branch instead of 'main'..." -ForegroundColor Yellow
    git push -u origin master
}

Write-Host ""
Write-Host "[DONE] Script complete" -ForegroundColor Green
Write-Host ""

