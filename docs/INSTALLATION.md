# Installation Guide

## Prerequisites

- Python 3.8 or higher
- 10GB+ free disk space
- Linux, macOS, or Windows (WSL or native)
- Internet connection for downloading dependencies

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

The enhanced installer will:
- ✅ Check for conflicts and existing installations
- ✅ Verify all system dependencies
- ✅ Check disk space and permissions
- ✅ Create isolated virtual environment
- ✅ Install all Python dependencies
- ✅ Install and configure Ollama (Linux only)
- ✅ Download AI models (llama3.3, qwen2.5)
- ✅ Create configuration files
- ✅ Run health checks
- ✅ Provide detailed logs
- ✅ Automatic rollback on failure

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

After installation, the installer runs automatic health checks. You can verify manually:

```bash
# Run diagnostics tool
./diagnose.sh

# Check version
python organize.py --version

# Run help
python organize.py --help

# Test scan (dry run)
python organize.py scan ~/Downloads --dry-run
```

### Installation Logs

All installation activity is logged to: `~/.organizer/install.log`

View logs:
```bash
cat ~/.organizer/install.log
tail -f ~/.organizer/install.log  # Follow in real-time
```

## Troubleshooting

### Run Diagnostics

If you encounter issues, run the diagnostics tool first:

```bash
./diagnose.sh
```

This will:
- Collect system information
- Check all dependencies
- Verify installation status
- Test Ollama connectivity
- Analyze logs
- Identify common issues
- Generate a report

### Common Issues

#### 1. Python Not Found

**Linux/Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install python3.8 python3-pip python3-venv
```

**Fedora/RHEL:**
```bash
sudo dnf install python3 python3-pip
```

**macOS:**
```bash
brew install python@3.8
```

**Windows:**
Download from [python.org](https://www.python.org/downloads/)

#### 2. Ollama Installation Issues

**Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
sudo systemctl start ollama  # Start service
```

**macOS:**
Download from [ollama.com/download](https://ollama.com/download)

**Windows:**
Download from [ollama.com/download/windows](https://ollama.com/download/windows)

#### 3. Ollama Not Running

```bash
# Check if Ollama is running
curl http://localhost:11434/api/version

# Start Ollama
ollama serve  # Run in background or
sudo systemctl start ollama  # Linux with systemd
```

#### 4. Dependency Installation Errors

```bash
# Upgrade pip first
python3 -m pip install --upgrade pip

# Install with verbose output
pip install -r requirements.txt -v

# If specific package fails
pip install <package-name> --verbose
```

#### 5. Permission Denied Errors

**Install directory not writable:**
```bash
# Check permissions
ls -la .

# Fix if needed
sudo chown -R $USER:$USER .
```

**Cannot create config directory:**
```bash
# Check home directory permissions
ls -la ~

# Create directory manually
mkdir -p ~/.organizer
chmod 755 ~/.organizer
```

**Cannot create symlink:**
```bash
# Create symlink manually
sudo ln -sf $(pwd)/organize.py /usr/local/bin/organize
```

#### 6. Disk Space Issues

```bash
# Check available space
df -h .

# Clean up if needed
docker system prune  # If using Docker
pip cache purge
ollama rm <unused-model>  # Remove unused models
```

#### 7. Network Connectivity Issues

```bash
# Test PyPI connection
curl -I https://pypi.org

# Test Ollama connection
curl -I https://ollama.com

# If behind proxy, set environment variables
export HTTP_PROXY=http://proxy:port
export HTTPS_PROXY=http://proxy:port
pip install -r requirements.txt
```

#### 8. Installation Failed Mid-Way

The installer has automatic rollback, but if you need to clean up manually:

```bash
# Remove partial installation
rm -rf venv/
rm -f ~/.organizer/install.state

# Run installer again
./install.sh
```

#### 9. Reinstalling Over Existing Installation

The installer detects existing installations and prompts for confirmation. To force reinstall:

```bash
# Uninstall first
./uninstall.sh

# Then reinstall
./install.sh
```

#### 10. Tesseract OCR Not Found

Tesseract is optional but required for OCR on images.

**Linux:**
```bash
sudo apt-get install tesseract-ocr  # Ubuntu/Debian
sudo dnf install tesseract            # Fedora
```

**macOS:**
```bash
brew install tesseract
```

**Windows:**
Download from [tesseract-ocr](https://github.com/UB-Mannheim/tesseract/wiki)

### Getting Help

If problems persist:

1. Run `./diagnose.sh` and save the output
2. Check installation log: `~/.organizer/install.log`
3. Search existing [GitHub Issues](https://github.com/gaI-observe-online/SmartFileOrganizer/issues)
4. Create a new issue with:
   - Diagnostic output
   - Installation log
   - System information (OS, Python version)
   - Error messages

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

SmartFileOrganizer provides a complete uninstall script:

```bash
./uninstall.sh
```

The uninstaller will:
- Remove the virtual environment
- Remove system symlink
- Optionally remove configuration and data
- Log all uninstall actions
- Leave no artifacts behind

**Manual uninstall (if needed):**
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

## Testing the Installation

Run the installation test suite:

```bash
# Run all tests
./tests/install/integration_tests.sh

# Run Python unit tests (requires pytest)
pytest tests/install/test_installation.py -v
```

## Web UI Installation

SmartFileOrganizer includes a modern web interface built with React. The web UI runs on **port 8001** by default.

### Prerequisites for Web UI

In addition to the base installation requirements:

- **Node.js 18+** and npm (for building the web UI)
- **Web dependencies** (automatically installed):
  - FastAPI
  - Uvicorn
  - WebSockets
  - psutil
  - requests

### Installing Web Dependencies

The web server dependencies are included in `requirements.txt`:

```bash
# Install all dependencies including web server
pip install -r requirements.txt
```

### Building the Web UI (Optional)

The web UI is pre-built, but if you want to customize it:

```bash
# Navigate to web directory
cd src/web

# Install Node dependencies
npm install

# Build for production
npm run build
```

The built files will be in `src/web/dist/` and automatically served by the backend.

### Starting the Web Server

```bash
# Start with default settings (port 8001)
smartfile serve

# Or with custom port
smartfile serve --port 8002

# Or using environment variable
SMARTFILE_PORT=8002 smartfile serve

# Don't auto-open browser
smartfile serve --no-browser
```

The web interface will be accessible at `http://localhost:8001`.

### Web UI Features

- 🎨 Modern, responsive interface with dark/light mode
- 📊 Dashboard with system health and recent scans
- 🔍 Interactive scanner with real-time progress
- 📋 Filterable results view
- ⚙️ Settings configuration
- 📱 Mobile-responsive design

See [Web UI Documentation](WEB_UI.md) for detailed usage instructions.

### Troubleshooting Web UI

#### Port Already in Use

If port 8001 is occupied:

```bash
# The CLI will auto-detect and suggest alternatives
smartfile serve
# > Error: Port 8001 is already in use
# > Suggested: Try port 8002

# Use custom port
smartfile serve --port 8002
```

#### Web UI Not Loading

If you see "Web UI not built":

```bash
cd src/web
npm install
npm run build
```

#### WebSocket Connection Issues

Check that:
1. Backend is running on the correct port
2. No firewall blocking WebSocket connections
3. Browser console for error messages

### Development Mode

For development with hot-reload:

```bash
# Terminal 1: Start backend
smartfile serve

# Terminal 2: Start frontend dev server
cd src/web
npm run dev
```

Frontend dev server runs on `http://localhost:3000` with API proxy to port 8001.
