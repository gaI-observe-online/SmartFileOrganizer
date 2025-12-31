#!/bin/bash
# SmartFileOrganizer Installation Script
# For Linux and macOS

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║      SmartFileOrganizer - Installation Wizard              ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo "→ Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 not found. Please install Python 3.8 or higher.${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then 
    echo -e "${RED}✗ Python $PYTHON_VERSION found, but Python 3.8+ is required.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"

# Check disk space
echo ""
echo "→ Checking disk space..."
AVAILABLE_SPACE=$(df -BG . | tail -1 | awk '{print $4}' | sed 's/G//')

if [ "$AVAILABLE_SPACE" -lt 10 ]; then
    echo -e "${YELLOW}⚠ Warning: Less than 10GB free disk space available (${AVAILABLE_SPACE}GB)${NC}"
    echo "   This may cause issues with backups and model storage."
    read -p "   Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo -e "${GREEN}✓ ${AVAILABLE_SPACE}GB available${NC}"
fi

# Check if Ollama is installed
echo ""
echo "→ Checking for Ollama..."
if ! command -v ollama &> /dev/null; then
    echo -e "${YELLOW}⚠ Ollama not found. Installing...${NC}"
    
    # Detect OS
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        curl -fsSL https://ollama.com/install.sh | sh
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "Please install Ollama manually from https://ollama.com/download"
        echo "After installation, run this script again."
        exit 1
    else
        echo -e "${RED}✗ Unsupported OS for automatic Ollama installation${NC}"
        echo "Please install Ollama manually from https://ollama.com/download"
        exit 1
    fi
else
    echo -e "${GREEN}✓ Ollama found${NC}"
fi

# Pull Ollama models
echo ""
echo "→ Pulling AI models (this may take a few minutes)..."
echo "  Downloading llama3.3..."
ollama pull llama3.3 || echo -e "${YELLOW}⚠ Failed to pull llama3.3${NC}"

echo "  Downloading qwen2.5..."
ollama pull qwen2.5 || echo -e "${YELLOW}⚠ Failed to pull qwen2.5${NC}"

# Create virtual environment
echo ""
echo "→ Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo ""
echo "→ Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Initialize database
echo ""
echo "→ Initializing database..."
mkdir -p ~/.organizer

# Create config file
echo ""
echo "→ Creating default configuration..."
if [ ! -f ~/.organizer/config.json ]; then
    cp config.example.json ~/.organizer/config.json
    echo -e "${GREEN}✓ Configuration created at ~/.organizer/config.json${NC}"
else
    echo -e "${YELLOW}⚠ Configuration already exists, skipping${NC}"
fi

# Make organize.py executable
chmod +x organize.py

# Create symlink in /usr/local/bin (optional)
echo ""
read -p "→ Create system-wide command 'organize'? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    sudo ln -sf "$SCRIPT_DIR/organize.py" /usr/local/bin/organize
    echo -e "${GREEN}✓ Command 'organize' created${NC}"
fi

# Success message
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║             Installation Complete! 🎉                      ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Quick Start:"
echo "  1. Activate virtual environment:  source venv/bin/activate"
echo "  2. Scan a folder:                 python organize.py scan ~/Downloads"
echo "  3. Watch a folder:                python organize.py watch ~/Downloads"
echo ""
echo "Documentation:"
echo "  • README.md         - Quick overview"
echo "  • docs/USAGE.md     - Detailed usage guide"
echo "  • docs/PRIVACY.md   - Privacy information"
echo ""
echo -e "${GREEN}Happy organizing! 📂${NC}"
