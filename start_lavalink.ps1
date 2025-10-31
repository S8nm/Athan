# ===================================================================
# Athan Bot - Lavalink Quick Start Script
# ===================================================================
# This script downloads and runs Lavalink for you automatically
# ===================================================================

$LAVALINK_VERSION = "4.0.4"
$LAVALINK_DIR = "lavalink"
$LAVALINK_JAR = "$LAVALINK_DIR/Lavalink.jar"
$LAVALINK_URL = "https://github.com/lavalink-devs/Lavalink/releases/download/$LAVALINK_VERSION/Lavalink.jar"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Athan Bot - Lavalink Starter" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Java is installed
Write-Host "[1/4] Checking for Java..." -ForegroundColor Cyan
try {
    $javaVersion = java -version 2>&1 | Select-Object -First 1
    Write-Host "[OK] Java found: $javaVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Java not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Java 17 or newer:" -ForegroundColor Yellow
    Write-Host "https://adoptium.net/" -ForegroundColor White
    Write-Host ""
    exit 1
}

# Create lavalink directory
Write-Host ""
Write-Host "[2/4] Setting up Lavalink directory..." -ForegroundColor Cyan
if (-not (Test-Path $LAVALINK_DIR)) {
    New-Item -ItemType Directory -Path $LAVALINK_DIR | Out-Null
    Write-Host "[OK] Created $LAVALINK_DIR directory" -ForegroundColor Green
} else {
    Write-Host "[OK] Directory exists" -ForegroundColor Green
}

# Download Lavalink if not present
Write-Host ""
Write-Host "[3/4] Checking for Lavalink JAR..." -ForegroundColor Cyan
if (-not (Test-Path $LAVALINK_JAR)) {
    Write-Host "[INFO] Downloading Lavalink $LAVALINK_VERSION..." -ForegroundColor Yellow
    Write-Host "       This may take a minute..." -ForegroundColor Gray
    try {
        Invoke-WebRequest -Uri $LAVALINK_URL -OutFile $LAVALINK_JAR
        Write-Host "[OK] Downloaded Lavalink.jar" -ForegroundColor Green
    } catch {
        Write-Host "[ERROR] Failed to download Lavalink!" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "[OK] Lavalink.jar exists" -ForegroundColor Green
}

# Copy config if needed
$LAVALINK_CONFIG = "$LAVALINK_DIR/application.yml"
if (-not (Test-Path $LAVALINK_CONFIG)) {
    if (Test-Path "lavalink-config.yml") {
        Copy-Item "lavalink-config.yml" $LAVALINK_CONFIG
        Write-Host "[OK] Copied configuration file" -ForegroundColor Green
    } else {
        Write-Host "[WARNING] No configuration file found, using defaults" -ForegroundColor Yellow
    }
}

# Start Lavalink
Write-Host ""
Write-Host "[4/4] Starting Lavalink server..." -ForegroundColor Cyan
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Lavalink is starting..." -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Keep this window OPEN while running the bot!" -ForegroundColor Yellow
Write-Host "Press Ctrl+C to stop Lavalink" -ForegroundColor Gray
Write-Host ""
Write-Host "----------------------------------------" -ForegroundColor Cyan

cd $LAVALINK_DIR
java -Xmx512M -jar Lavalink.jar

