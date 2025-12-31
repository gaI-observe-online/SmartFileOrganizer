#!/bin/bash
# SmartFileOrganizer Diagnostics Tool
# Collect system information and diagnose common issues

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
INSTALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="$HOME/.organizer"
VENV_DIR="$INSTALL_DIR/venv"
DIAG_OUTPUT="/tmp/smartfile-diagnostics-$(date +%Y%m%d-%H%M%S).txt"

# Start diagnostic output
exec > >(tee "$DIAG_OUTPUT") 2>&1

print_header() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║      SmartFileOrganizer - Diagnostics Tool                 ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
    echo "Collecting system information and checking for issues..."
    echo "Output will be saved to: $DIAG_OUTPUT"
    echo ""
}

section() {
    echo ""
    echo "═══════════════════════════════════════════════════════════"
    echo "  $1"
    echo "═══════════════════════════════════════════════════════════"
    echo ""
}

check_mark() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
    fi
}

# System Information
collect_system_info() {
    section "SYSTEM INFORMATION"
    
    echo "Timestamp: $(date)"
    echo "Hostname: $(hostname)"
    echo "OS: $(uname -s)"
    echo "Kernel: $(uname -r)"
    echo "Architecture: $(uname -m)"
    
    if [ -f /etc/os-release ]; then
        echo ""
        echo "Distribution Info:"
        cat /etc/os-release
    fi
    
    if command -v sw_vers &> /dev/null; then
        echo ""
        echo "macOS Version:"
        sw_vers
    fi
}

# Python Environment
check_python() {
    section "PYTHON ENVIRONMENT"
    
    echo -n "Python 3: "
    if command -v python3 &> /dev/null; then
        echo -e "$(check_mark 0) $(python3 --version)"
        echo "Location: $(which python3)"
        
        echo ""
        echo -n "pip: "
        if python3 -m pip --version &> /dev/null; then
            echo -e "$(check_mark 0) $(python3 -m pip --version)"
        else
            echo -e "$(check_mark 1) Not available"
        fi
        
        echo ""
        echo -n "venv module: "
        if python3 -m venv --help &> /dev/null; then
            echo -e "$(check_mark 0) Available"
        else
            echo -e "$(check_mark 1) Not available"
        fi
    else
        echo -e "$(check_mark 1) Not found"
    fi
}

# Installation Status
check_installation() {
    section "INSTALLATION STATUS"
    
    echo -n "Install directory ($INSTALL_DIR): "
    if [ -d "$INSTALL_DIR" ]; then
        echo -e "$(check_mark 0) exists"
        echo "  Writable: $([ -w "$INSTALL_DIR" ] && echo "yes" || echo "no")"
    else
        echo -e "$(check_mark 1) not found"
    fi
    
    echo ""
    echo -n "Virtual environment ($VENV_DIR): "
    if [ -d "$VENV_DIR" ]; then
        echo -e "$(check_mark 0) exists"
        
        if [ -f "$VENV_DIR/bin/activate" ]; then
            echo "  Activate script: $(check_mark 0)"
            
            # Check installed packages
            if [ -f "$VENV_DIR/bin/python" ]; then
                echo ""
                echo "  Installed packages:"
                "$VENV_DIR/bin/python" -m pip list 2>/dev/null | head -20
            fi
        else
            echo "  Activate script: $(check_mark 1)"
        fi
    else
        echo -e "$(check_mark 1) not found"
    fi
    
    echo ""
    echo -n "Config directory ($CONFIG_DIR): "
    if [ -d "$CONFIG_DIR" ]; then
        echo -e "$(check_mark 0) exists"
        echo "  Writable: $([ -w "$CONFIG_DIR" ] && echo "yes" || echo "no")"
        
        if [ -f "$CONFIG_DIR/config.json" ]; then
            echo -n "  config.json: $(check_mark 0)"
            # Validate JSON
            if python3 -c "import json; json.load(open('$CONFIG_DIR/config.json'))" 2>/dev/null; then
                echo " (valid JSON)"
            else
                echo " ${RED}(invalid JSON)${NC}"
            fi
        else
            echo "  config.json: $(check_mark 1)"
        fi
        
        echo ""
        echo "  Directory contents:"
        ls -lh "$CONFIG_DIR" 2>/dev/null || echo "    Cannot list directory"
    else
        echo -e "$(check_mark 1) not found"
    fi
    
    echo ""
    echo -n "System symlink (/usr/local/bin/organize): "
    if [ -L "/usr/local/bin/organize" ]; then
        echo -e "$(check_mark 0) exists"
        echo "  Target: $(readlink /usr/local/bin/organize)"
    else
        echo -e "$(check_mark 1) not found"
    fi
    
    echo ""
    echo -n "organize.py: "
    if [ -f "$INSTALL_DIR/organize.py" ]; then
        echo -e "$(check_mark 0) exists"
        echo "  Executable: $([ -x "$INSTALL_DIR/organize.py" ] && echo "yes" || echo "no")"
    else
        echo -e "$(check_mark 1) not found"
    fi
}

# Ollama Status
check_ollama() {
    section "OLLAMA STATUS"
    
    echo -n "Ollama command: "
    if command -v ollama &> /dev/null; then
        echo -e "$(check_mark 0) $(ollama --version 2>&1 | head -1)"
        echo "Location: $(which ollama)"
        
        echo ""
        echo -n "Ollama service: "
        if curl -s --max-time 3 http://localhost:11434/api/version > /dev/null 2>&1; then
            echo -e "$(check_mark 0) running"
            
            version_info=$(curl -s http://localhost:11434/api/version 2>/dev/null)
            echo "  $version_info"
            
            echo ""
            echo "Installed models:"
            ollama list 2>/dev/null || echo "  Cannot list models"
        else
            echo -e "$(check_mark 1) not running"
            echo "  Try: ollama serve"
        fi
    else
        echo -e "$(check_mark 1) not found"
        echo "  Install from: https://ollama.com"
    fi
}

# Disk Space
check_disk_space() {
    section "DISK SPACE"
    
    if command -v df &> /dev/null; then
        echo "Install directory ($INSTALL_DIR):"
        df -h "$INSTALL_DIR" 2>/dev/null || echo "  Cannot check disk space"
        
        if [ -d "$CONFIG_DIR" ]; then
            echo ""
            echo "Config directory ($CONFIG_DIR):"
            df -h "$CONFIG_DIR" 2>/dev/null || echo "  Cannot check disk space"
        fi
    else
        echo "df command not available"
    fi
}

# Network Connectivity
check_network() {
    section "NETWORK CONNECTIVITY"
    
    echo -n "PyPI (pypi.org): "
    if curl -s --max-time 5 -I https://pypi.org > /dev/null 2>&1; then
        echo -e "$(check_mark 0) reachable"
    else
        echo -e "$(check_mark 1) unreachable"
    fi
    
    echo -n "Ollama (ollama.com): "
    if curl -s --max-time 5 -I https://ollama.com > /dev/null 2>&1; then
        echo -e "$(check_mark 0) reachable"
    else
        echo -e "$(check_mark 1) unreachable"
    fi
    
    echo -n "GitHub (github.com): "
    if curl -s --max-time 5 -I https://github.com > /dev/null 2>&1; then
        echo -e "$(check_mark 0) reachable"
    else
        echo -e "$(check_mark 1) unreachable"
    fi
}

# Check Logs
check_logs() {
    section "RECENT LOGS"
    
    if [ -f "$CONFIG_DIR/install.log" ]; then
        echo "Installation log (last 20 lines):"
        echo "---"
        tail -20 "$CONFIG_DIR/install.log"
        echo "---"
    else
        echo "No installation log found"
    fi
    
    if [ -f "$CONFIG_DIR/uninstall.log" ]; then
        echo ""
        echo "Uninstall log (last 20 lines):"
        echo "---"
        tail -20 "$CONFIG_DIR/uninstall.log"
        echo "---"
    fi
}

# Test CLI
test_cli() {
    section "CLI FUNCTIONALITY TEST"
    
    if [ -d "$VENV_DIR" ] && [ -f "$VENV_DIR/bin/activate" ]; then
        echo "Testing CLI import..."
        source "$VENV_DIR/bin/activate"
        
        if python3 -c "from smartfile.cli.main import cli; print('OK')" 2>/dev/null; then
            echo -e "$(check_mark 0) CLI module imports successfully"
        else
            echo -e "$(check_mark 1) CLI module import failed"
            echo ""
            echo "Error output:"
            python3 -c "from smartfile.cli.main import cli" 2>&1 || true
        fi
        
        deactivate 2>/dev/null || true
    else
        echo "Virtual environment not available, skipping CLI test"
    fi
}

# Common Issues
check_common_issues() {
    section "COMMON ISSUES"
    
    local issues_found=false
    
    # Check Python version
    if command -v python3 &> /dev/null; then
        py_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        if [ "$(printf '%s\n' "3.8" "$py_version" | sort -V | head -n1)" != "3.8" ]; then
            echo -e "${RED}✗ Python version too old: $py_version (need 3.8+)${NC}"
            issues_found=true
        fi
    fi
    
    # Check disk space
    if command -v df &> /dev/null; then
        case "$(uname -s)" in
            Linux*)
                available=$(df -BG "$INSTALL_DIR" | tail -1 | awk '{print $4}' | sed 's/G//')
                ;;
            Darwin*)
                available=$(df -g "$INSTALL_DIR" | tail -1 | awk '{print $4}')
                ;;
        esac
        
        if [ "$available" -lt 10 ]; then
            echo -e "${YELLOW}⚠ Low disk space: ${available}GB available (10GB+ recommended)${NC}"
            issues_found=true
        fi
    fi
    
    # Check if venv exists but is broken
    if [ -d "$VENV_DIR" ] && [ ! -f "$VENV_DIR/bin/activate" ]; then
        echo -e "${RED}✗ Virtual environment appears corrupted${NC}"
        echo "  Try: rm -rf venv && ./install.sh"
        issues_found=true
    fi
    
    # Check if config is invalid JSON
    if [ -f "$CONFIG_DIR/config.json" ]; then
        if ! python3 -c "import json; json.load(open('$CONFIG_DIR/config.json'))" 2>/dev/null; then
            echo -e "${RED}✗ config.json is invalid JSON${NC}"
            echo "  Try: cp config.example.json ~/.organizer/config.json"
            issues_found=true
        fi
    fi
    
    # Check if Ollama is installed but not running
    if command -v ollama &> /dev/null; then
        if ! curl -s --max-time 3 http://localhost:11434/api/version > /dev/null 2>&1; then
            echo -e "${YELLOW}⚠ Ollama is installed but not running${NC}"
            echo "  Try: ollama serve"
            issues_found=true
        fi
    fi
    
    if [ "$issues_found" = false ]; then
        echo -e "${GREEN}✓ No common issues detected${NC}"
    fi
}

# Main
main() {
    print_header
    
    collect_system_info
    check_python
    check_installation
    check_ollama
    check_disk_space
    check_network
    check_logs
    test_cli
    check_common_issues
    
    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║          Diagnostics Complete                               ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
    echo "Report saved to: $DIAG_OUTPUT"
    echo ""
    echo "If you need help, please share this report with the support team."
    echo ""
}

main "$@"
