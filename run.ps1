# One-command setup and run script for Athan bot
# Windows PowerShell version

Write-Host ""
Write-Host "Athan Bot - Startup Script" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check Python installation
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[OK] Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python not found. Please install Python 3.10+" -ForegroundColor Red
    exit 1
}

# Create venv if missing
if (-not (Test-Path "venv")) {
    Write-Host "[INFO] Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    Write-Host "[OK] Virtual environment created" -ForegroundColor Green
} else {
    Write-Host "[OK] Virtual environment exists" -ForegroundColor Green
}

# Activate venv
Write-Host "[INFO] Activating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

# Check if dependencies are installed
$pipList = pip list 2>&1
if ($pipList -notmatch "discord.py") {
    Write-Host "[INFO] Installing dependencies..." -ForegroundColor Yellow
    pip install -e .
    Write-Host "[OK] Dependencies installed" -ForegroundColor Green
} else {
    Write-Host "[OK] Dependencies already installed" -ForegroundColor Green
}

# Check for Discord token in multiple locations
Write-Host ""
Write-Host "[INFO] Checking for Discord token..." -ForegroundColor Yellow

$tokenFound = $false
$tokenLocations = @(
    "DISCORD_TOKEN.txt",
    ".env",
    $env:DISCORD_TOKEN
)

foreach ($location in $tokenLocations) {
    if ($location -and (Test-Path $location -PathType Leaf)) {
        $content = Get-Content $location -Raw
        if ($content -match "DISCORD_TOKEN\s*=\s*(.+)" -or $content.Trim().Length -gt 0) {
            Write-Host "[OK] Token found in: $location" -ForegroundColor Green
            $tokenFound = $true
            break
        }
    } elseif ($location -eq $env:DISCORD_TOKEN -and $env:DISCORD_TOKEN) {
        Write-Host "[OK] Token found in environment variable" -ForegroundColor Green
        $tokenFound = $true
        break
    }
}

if (-not $tokenFound) {
    Write-Host "[ERROR] Discord token not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please create one of these files:" -ForegroundColor Yellow
    Write-Host "  1. DISCORD_TOKEN.txt (just paste your token)" -ForegroundColor White
    Write-Host "  2. .env (add line: DISCORD_TOKEN=your_token)" -ForegroundColor White
    Write-Host ""
    Write-Host "Get your bot token from: https://discord.com/developers/applications" -ForegroundColor Cyan
    exit 1
}

# Check for adhan audio file
if (-not (Test-Path "assets\adhan.mp3")) {
    Write-Host "[WARN] assets\adhan.mp3 not found" -ForegroundColor Yellow
    Write-Host "       Voice Adhan will not work until you add the audio file" -ForegroundColor Yellow
    Write-Host "       See assets\README.md for details" -ForegroundColor White
} else {
    Write-Host "[OK] Adhan audio file found" -ForegroundColor Green
}

# Create data directory if missing
if (-not (Test-Path "data")) {
    New-Item -ItemType Directory -Path "data" | Out-Null
    Write-Host "[OK] Data directory created" -ForegroundColor Green
} else {
    Write-Host "[OK] Data directory exists" -ForegroundColor Green
}

# Check if Lavalink is running
Write-Host ""
Write-Host "Checking Lavalink server..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "http://localhost:2333/version" -TimeoutSec 2 -ErrorAction Stop
    Write-Host "[OK] Lavalink is running" -ForegroundColor Green
} catch {
    Write-Host "[WARN] Lavalink not detected" -ForegroundColor Yellow
    Write-Host "       Voice features require Lavalink server" -ForegroundColor Yellow
    Write-Host "       Run .\start_lavalink.ps1 in another terminal" -ForegroundColor White
    Write-Host "       Or see LAVALINK_SETUP.md for details" -ForegroundColor White
}

Write-Host ""
Write-Host "Starting Athan Bot..." -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the bot" -ForegroundColor Gray
Write-Host ""

# Run the bot
python -m athan.bot
