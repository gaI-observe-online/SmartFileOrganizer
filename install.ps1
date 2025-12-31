# SmartFileOrganizer Installation Script for Windows
# Run with: powershell -ExecutionPolicy Bypass -File install.ps1

Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║      SmartFileOrganizer - Installation Wizard              ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Check Python version
Write-Host "→ Checking Python version..." -ForegroundColor Yellow

try {
    $pythonVersion = & python --version 2>&1
    if ($pythonVersion -match "Python (\d+\.\d+)") {
        $version = [version]$matches[1]
        if ($version -lt [version]"3.8") {
            Write-Host "✗ Python $version found, but Python 3.8+ is required." -ForegroundColor Red
            exit 1
        }
        Write-Host "✓ Python $version found" -ForegroundColor Green
    }
} catch {
    Write-Host "✗ Python not found. Please install Python 3.8 or higher." -ForegroundColor Red
    Write-Host "  Download from: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

# Check disk space
Write-Host ""
Write-Host "→ Checking disk space..." -ForegroundColor Yellow

$drive = (Get-Location).Drive
$freeSpace = [math]::Round((Get-PSDrive $drive.Name).Free / 1GB, 2)

if ($freeSpace -lt 10) {
    Write-Host "⚠ Warning: Less than 10GB free disk space available ($freeSpace GB)" -ForegroundColor Yellow
    $continue = Read-Host "Continue anyway? (y/N)"
    if ($continue -ne "y" -and $continue -ne "Y") {
        exit 1
    }
} else {
    Write-Host "✓ $freeSpace GB available" -ForegroundColor Green
}

# Check for Ollama
Write-Host ""
Write-Host "→ Checking for Ollama..." -ForegroundColor Yellow

try {
    $null = & ollama --version 2>&1
    Write-Host "✓ Ollama found" -ForegroundColor Green
} catch {
    Write-Host "⚠ Ollama not found." -ForegroundColor Yellow
    Write-Host "  Please install Ollama from: https://ollama.com/download/windows" -ForegroundColor Yellow
    Write-Host "  After installation, run this script again." -ForegroundColor Yellow
    exit 1
}

# Pull Ollama models
Write-Host ""
Write-Host "→ Pulling AI models (this may take a few minutes)..." -ForegroundColor Yellow

Write-Host "  Downloading llama3.3..." -ForegroundColor Cyan
try {
    & ollama pull llama3.3
} catch {
    Write-Host "⚠ Failed to pull llama3.3" -ForegroundColor Yellow
}

Write-Host "  Downloading qwen2.5..." -ForegroundColor Cyan
try {
    & ollama pull qwen2.5
} catch {
    Write-Host "⚠ Failed to pull qwen2.5" -ForegroundColor Yellow
}

# Create virtual environment
Write-Host ""
Write-Host "→ Creating Python virtual environment..." -ForegroundColor Yellow

& python -m venv venv

# Activate virtual environment and install dependencies
Write-Host ""
Write-Host "→ Installing Python dependencies..." -ForegroundColor Yellow

& .\venv\Scripts\pip.exe install --upgrade pip
& .\venv\Scripts\pip.exe install -r requirements.txt

# Initialize database
Write-Host ""
Write-Host "→ Initializing database..." -ForegroundColor Yellow

$organizerDir = Join-Path $env:USERPROFILE ".organizer"
if (-not (Test-Path $organizerDir)) {
    New-Item -ItemType Directory -Path $organizerDir | Out-Null
}

# Create config file
Write-Host ""
Write-Host "→ Creating default configuration..." -ForegroundColor Yellow

$configPath = Join-Path $organizerDir "config.json"
if (-not (Test-Path $configPath)) {
    Copy-Item "config.example.json" $configPath
    Write-Host "✓ Configuration created at $configPath" -ForegroundColor Green
} else {
    Write-Host "⚠ Configuration already exists, skipping" -ForegroundColor Yellow
}

# Create wrapper script
Write-Host ""
Write-Host "→ Creating launcher script..." -ForegroundColor Yellow

$wrapperScript = @"
@echo off
"%~dp0venv\Scripts\python.exe" "%~dp0organize.py" %*
"@

$wrapperScript | Out-File -Encoding ASCII "organize.bat"

Write-Host "✓ Launcher script created (organize.bat)" -ForegroundColor Green

# Success message
Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║             Installation Complete! 🎉                      ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "Quick Start:" -ForegroundColor Yellow
Write-Host "  1. Scan a folder:    organize.bat scan C:\Downloads" -ForegroundColor White
Write-Host "  2. Watch a folder:   organize.bat watch C:\Downloads" -ForegroundColor White
Write-Host "  3. View help:        organize.bat --help" -ForegroundColor White
Write-Host ""
Write-Host "Documentation:" -ForegroundColor Yellow
Write-Host "  • README.md         - Quick overview" -ForegroundColor White
Write-Host "  • docs\USAGE.md     - Detailed usage guide" -ForegroundColor White
Write-Host "  • docs\PRIVACY.md   - Privacy information" -ForegroundColor White
Write-Host ""
Write-Host "Happy organizing! 📂" -ForegroundColor Green
