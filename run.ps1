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
$lavalink_running = $false
try {
    $response = Invoke-WebRequest -Uri "http://localhost:2333/version" -TimeoutSec 2 -ErrorAction Stop
    Write-Host "[OK] Lavalink is already running" -ForegroundColor Green
    $lavalink_running = $true
} catch {
    Write-Host "[INFO] Lavalink not detected, starting it now..." -ForegroundColor Yellow
    
    # Check if start_lavalink.ps1 exists
    if (Test-Path "start_lavalink.ps1") {
        try {
            # Start Lavalink in a new PowerShell window
            Write-Host "[INFO] Opening new terminal for Lavalink..." -ForegroundColor Cyan
            $lavalink_path = Join-Path $PSScriptRoot "start_lavalink.ps1"
            Start-Process powershell -ArgumentList "-NoExit", "-File", "`"$lavalink_path`""
            
            # Wait for Lavalink to start (up to 30 seconds)
            Write-Host "[INFO] Waiting for Lavalink to start (this may take 10-30 seconds)..." -ForegroundColor Cyan
            $max_wait = 30
            $waited = 0
            while ($waited -lt $max_wait) {
                Start-Sleep -Seconds 2
                $waited += 2
                try {
                    $test = Invoke-WebRequest -Uri "http://localhost:2333/version" -TimeoutSec 1 -ErrorAction Stop
                    Write-Host "[OK] Lavalink started successfully!" -ForegroundColor Green
                    $lavalink_running = $true
                    break
                } catch {
                    Write-Host "." -NoNewline -ForegroundColor Gray
                }
            }
            Write-Host ""
            
            if (-not $lavalink_running) {
                Write-Host "[WARN] Lavalink taking longer than expected to start" -ForegroundColor Yellow
                Write-Host "       Check the Lavalink terminal window for errors" -ForegroundColor Yellow
                Write-Host "       The bot will continue, but voice features may not work immediately" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "[ERROR] Failed to start Lavalink: $($_.Exception.Message)" -ForegroundColor Red
            Write-Host "       You can manually run: .\start_lavalink.ps1" -ForegroundColor Yellow
        }
    } else {
        Write-Host "[WARN] start_lavalink.ps1 not found" -ForegroundColor Yellow
        Write-Host "       Voice features will not work without Lavalink" -ForegroundColor Yellow
        Write-Host "       See LAVALINK_SETUP.md for manual setup" -ForegroundColor White
    }
}

Write-Host ""
Write-Host "Starting Athan Bot..." -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""
if ($lavalink_running) {
    Write-Host "✓ Lavalink: Running" -ForegroundColor Green
} else {
    Write-Host "✗ Lavalink: Not running (voice features disabled)" -ForegroundColor Yellow
}
Write-Host ""
Write-Host "Press Ctrl+C to stop the bot" -ForegroundColor Gray
Write-Host ""

# Run the bot
python -m athan.bot
