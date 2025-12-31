# Installation Guide

## Prerequisites

- Python 3.8 or higher
- 10GB+ free disk space
- Linux, macOS, or Windows (WSL or native)

## Quick Installation

### Linux / macOS

**One-command install:**
```bash
curl -sSL https://raw.githubusercontent.com/gaI-observe-online/SmartFileOrganizer/main/install.sh | bash
```

**Manual install:**
```bash
# Clone repository
git clone https://github.com/gaI-observe-online/SmartFileOrganizer.git
cd SmartFileOrganizer

# Run installer
chmod +x install.sh
./install.sh
```

### Windows

**PowerShell:**
```powershell
# Download and run installer
powershell -ExecutionPolicy Bypass -File install.ps1
```

**Manual install:**
```powershell
# Clone repository
git clone https://github.com/gaI-observe-online/SmartFileOrganizer.git
cd SmartFileOrganizer

# Install Python dependencies
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt

# Install Ollama
# Download from: https://ollama.com/download/windows

# Pull AI models
ollama pull llama3.3
ollama pull qwen2.5

# Create config
mkdir %USERPROFILE%\.organizer
copy config.example.json %USERPROFILE%\.organizer\config.json
```

## Docker Installation

```bash
# Clone repository
git clone https://github.com/gaI-observe-online/SmartFileOrganizer.git
cd SmartFileOrganizer

# Start services
docker-compose up -d

# Pull AI models
docker exec ollama ollama pull llama3.3
docker exec ollama ollama pull qwen2.5

# Use organizer
docker exec smartfile-organizer python organize.py scan /data/Downloads
```

## Verifying Installation

```bash
# Check version
python organize.py --version

# Run help
python organize.py --help

# Test scan (dry run)
python organize.py scan ~/Downloads --dry-run
```

## Troubleshooting

### Python Not Found

**Linux/Mac:**
```bash
# Install Python 3.8+
sudo apt-get install python3.8  # Debian/Ubuntu
brew install python@3.8         # macOS
```

**Windows:**
Download from [python.org](https://www.python.org/downloads/)

### Ollama Installation Issues

**Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**macOS:**
Download from [ollama.com/download](https://ollama.com/download)

**Windows:**
Download from [ollama.com/download/windows](https://ollama.com/download/windows)

### Dependency Installation Errors

```bash
# Upgrade pip first
pip install --upgrade pip

# Install with verbose output
pip install -r requirements.txt -v
```

### Tesseract OCR Not Found

**Linux:**
```bash
sudo apt-get install tesseract-ocr
```

**macOS:**
```bash
brew install tesseract
```

**Windows:**
Download from [tesseract-ocr](https://github.com/UB-Mannheim/tesseract/wiki)

## Post-Installation

### Configure AI Provider

```bash
# View current config
python organize.py config --show

# Edit config file
python organize.py config --edit
```

### First Run

```bash
# Scan a test folder
python organize.py scan ~/Downloads --dry-run

# View statistics
python organize.py stats --summary
```

## Updating

```bash
# Pull latest changes
git pull origin main

# Update dependencies
pip install -r requirements.txt --upgrade

# Pull latest AI models
ollama pull llama3.3
ollama pull qwen2.5
```

## Uninstallation

```bash
# Remove virtual environment
rm -rf venv/

# Remove config and data
rm -rf ~/.organizer/

# Remove system command (if created)
sudo rm /usr/local/bin/organize

# Remove repository
cd ..
rm -rf SmartFileOrganizer/
```
