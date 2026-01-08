#!/bin/bash
# SmartFileOrganizer Installation Script
# For Linux and macOS

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║      SmartFileOrganizer - Installation Wizard              ║"
echo "║              One-Click Setup with Web UI                   ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

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

# Create start script for easy server restart
echo ""
echo "→ Creating start script..."
cat > "$SCRIPT_DIR/start.sh" << 'EOF'
#!/bin/bash
# SmartFileOrganizer - Start Script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate virtual environment
source venv/bin/activate

# Start server
echo "Starting SmartFileOrganizer server..."
# Bind to localhost only for security (prevents external network access)
python -m uvicorn src.main:app --host 127.0.0.1 --port 8001 &
SERVER_PID=$!

echo "Server started with PID: $SERVER_PID"
echo "Web UI: http://localhost:8001"
echo ""
echo "To stop the server, run: kill $SERVER_PID"
echo "Or press Ctrl+C if running in foreground"

# Keep script running if executed directly
if [ "${BASH_SOURCE[0]}" -ef "$0" ]; then
    wait $SERVER_PID
fi
EOF

chmod +x "$SCRIPT_DIR/start.sh"
echo -e "${GREEN}✓ Start script created: start.sh${NC}"

# Start server automatically
echo ""
echo "→ Starting SmartFileOrganizer server..."
cd "$SCRIPT_DIR"
source venv/bin/activate

# Start server in background
# Bind to localhost only for security (prevents external network access)
python -m uvicorn src.main:app --host 127.0.0.1 --port 8001 > /dev/null 2>&1 &
SERVER_PID=$!
echo -e "${GREEN}✓ Server started (PID: $SERVER_PID)${NC}"

# Wait for server to be ready
echo ""
echo "→ Waiting for server to be ready..."
MAX_ATTEMPTS=30
ATTEMPT=0
SERVER_READY=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    if curl -s http://localhost:8001/health > /dev/null 2>&1; then
        SERVER_READY=1
        break
    fi
    sleep 1
    ATTEMPT=$((ATTEMPT + 1))
    echo -n "."
done

echo ""

if [ $SERVER_READY -eq 1 ]; then
    echo -e "${GREEN}✓ Server is ready!${NC}"
    
    # Open browser
    echo ""
    echo "→ Opening browser..."
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command -v xdg-open &> /dev/null; then
            xdg-open http://localhost:8001 &
        elif command -v sensible-browser &> /dev/null; then
            sensible-browser http://localhost:8001 &
        else
            echo -e "${YELLOW}⚠ Could not auto-open browser. Please visit: http://localhost:8001${NC}"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        open http://localhost:8001 &
    else
        echo -e "${YELLOW}⚠ Could not auto-open browser. Please visit: http://localhost:8001${NC}"
    fi
    
    # Success message
    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║          Installation Complete! 🎉                         ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
    echo -e "${BLUE}Web UI:${NC}      http://localhost:8001"
    echo -e "${BLUE}API Docs:${NC}    http://localhost:8001/docs"
    echo ""
    echo "Quick Start:"
    echo "  1. Click 'Auto-Scan' in the web UI"
    echo "  2. Review organization plans"
    echo "  3. Click 'Approve' and 'Execute'"
    echo ""
    echo "CLI Usage (Advanced):"
    echo "  • Activate venv:   source venv/bin/activate"
    echo "  • Scan folder:     python organize.py scan ~/Downloads"
    echo "  • Watch folder:    python organize.py watch ~/Downloads"
    echo ""
    echo "Server Management:"
    echo "  • Restart server:  ./start.sh"
    echo "  • Stop server:     kill $SERVER_PID"
    echo ""
    echo "Documentation:"
    echo "  • README.md         - Overview"
    echo "  • docs/USAGE.md     - Detailed guide"
    echo "  • docs/PRIVACY.md   - Privacy info"
    echo ""
    echo -e "${GREEN}🔒 All processing is 100% local. Your files never leave your computer.${NC}"
    echo ""
    echo -e "${GREEN}Happy organizing! 📂${NC}"
else
    echo -e "${RED}✗ Server failed to start within 30 seconds${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Check if port 8001 is already in use:"
    echo "     lsof -i :8001"
    echo ""
    echo "  2. Try starting manually:"
    echo "     ./start.sh"
    echo ""
    echo "  3. Check server logs for errors"
    exit 1
fi
