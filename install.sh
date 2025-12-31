#!/bin/bash
# SmartFileOrganizer Enhanced Installation Script
# For Linux and macOS with comprehensive error handling and rollback

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# ============================================================================
# CONFIGURATION
# ============================================================================

SCRIPT_VERSION="2.0.0"
INSTALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="$HOME/.organizer"
LOG_FILE="$CONFIG_DIR/install.log"
STATE_FILE="$CONFIG_DIR/install.state"
VENV_DIR="$INSTALL_DIR/venv"
MIN_DISK_SPACE_GB=10
MIN_PYTHON_VERSION="3.8"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Installation state tracking
INSTALLED_STEPS=()

# ============================================================================
# LOGGING FUNCTIONS
# ============================================================================

setup_logging() {
    mkdir -p "$CONFIG_DIR"
    exec > >(tee -a "$LOG_FILE") 2>&1
    log_info "Installation started at $(date)"
    log_info "Script version: $SCRIPT_VERSION"
    log_info "Install directory: $INSTALL_DIR"
    log_info "System: $(uname -s) $(uname -r) $(uname -m)"
}

log_info() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] [INFO] $*" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] [ERROR] $*${NC}" | tee -a "$LOG_FILE"
}

log_warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] [WARN] $*${NC}" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] [SUCCESS] $*${NC}" | tee -a "$LOG_FILE"
}

# ============================================================================
# STATE MANAGEMENT
# ============================================================================

save_state() {
    local step="$1"
    echo "$step" >> "$STATE_FILE"
    INSTALLED_STEPS+=("$step")
    log_info "Saved state: $step"
}

load_state() {
    if [ -f "$STATE_FILE" ]; then
        mapfile -t INSTALLED_STEPS < "$STATE_FILE"
        log_info "Loaded previous installation state: ${#INSTALLED_STEPS[@]} steps completed"
    fi
}

clear_state() {
    rm -f "$STATE_FILE"
    INSTALLED_STEPS=()
    log_info "Cleared installation state"
}

# ============================================================================
# CLEANUP AND ROLLBACK
# ============================================================================

cleanup_on_failure() {
    log_error "Installation failed! Rolling back changes..."
    
    # Rollback in reverse order
    for ((i=${#INSTALLED_STEPS[@]}-1; i>=0; i--)); do
        local step="${INSTALLED_STEPS[$i]}"
        log_info "Rolling back: $step"
        
        case "$step" in
            "venv_created")
                rm -rf "$VENV_DIR"
                log_info "Removed virtual environment"
                ;;
            "dependencies_installed")
                # Dependencies are in venv, will be removed with venv
                ;;
            "ollama_models_pulled")
                # Models can stay, they're useful
                ;;
            "config_created")
                if [ -f "$CONFIG_DIR/config.json.backup" ]; then
                    mv "$CONFIG_DIR/config.json.backup" "$CONFIG_DIR/config.json"
                    log_info "Restored previous config"
                else
                    rm -f "$CONFIG_DIR/config.json"
                    log_info "Removed config file"
                fi
                ;;
            "symlink_created")
                sudo rm -f /usr/local/bin/organize 2>/dev/null || true
                log_info "Removed symlink"
                ;;
        esac
    done
    
    clear_state
    log_error "Rollback complete. Check $LOG_FILE for details."
    exit 1
}

# Set trap for cleanup on error
trap cleanup_on_failure ERR

# ============================================================================
# PRE-FLIGHT CHECKS
# ============================================================================

print_header() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║      SmartFileOrganizer - Installation Wizard v$SCRIPT_VERSION      ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
}

check_existing_installation() {
    log_info "Checking for existing installation..."
    
    local has_existing=false
    
    if [ -d "$VENV_DIR" ]; then
        log_warn "Found existing virtual environment at $VENV_DIR"
        has_existing=true
    fi
    
    if [ -f "$CONFIG_DIR/config.json" ]; then
        log_warn "Found existing configuration at $CONFIG_DIR/config.json"
        has_existing=true
    fi
    
    if [ -L "/usr/local/bin/organize" ]; then
        log_warn "Found existing symlink at /usr/local/bin/organize"
        has_existing=true
    fi
    
    if [ "$has_existing" = true ]; then
        echo ""
        echo -e "${YELLOW}⚠ Existing installation detected!${NC}"
        echo "This will upgrade/reinstall SmartFileOrganizer."
        echo ""
        read -p "Continue with reinstall? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Installation cancelled by user"
            exit 0
        fi
        
        # Backup existing config
        if [ -f "$CONFIG_DIR/config.json" ]; then
            cp "$CONFIG_DIR/config.json" "$CONFIG_DIR/config.json.backup"
            log_info "Backed up existing configuration"
        fi
    fi
}

check_os_compatibility() {
    log_info "Checking OS compatibility..."
    
    local os_type="$(uname -s)"
    case "$os_type" in
        Linux*)
            log_success "✓ Linux detected"
            
            # Try to detect distribution
            if [ -f /etc/os-release ]; then
                source /etc/os-release
                log_info "Distribution: $NAME $VERSION"
                
                # Warn if not tested distro
                case "$ID" in
                    ubuntu|debian|fedora|centos|rhel|arch|manjaro)
                        log_success "✓ Supported distribution: $ID"
                        ;;
                    *)
                        log_warn "Distribution '$ID' is not officially tested"
                        ;;
                esac
            fi
            ;;
        Darwin*)
            log_success "✓ macOS detected"
            log_info "macOS version: $(sw_vers -productVersion)"
            ;;
        *)
            log_error "Unsupported operating system: $os_type"
            log_error "Supported: Linux, macOS"
            exit 1
            ;;
    esac
}

check_system_dependencies() {
    log_info "Checking system dependencies..."
    
    local missing_deps=()
    
    # Check Python 3
    if ! command -v python3 &> /dev/null; then
        missing_deps+=("python3")
    else
        echo -ne "→ Python 3... "
        local python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        if [ "$(printf '%s\n' "$MIN_PYTHON_VERSION" "$python_version" | sort -V | head -n1)" != "$MIN_PYTHON_VERSION" ]; then
            log_error "✗ Python $python_version found, but Python $MIN_PYTHON_VERSION+ is required"
            exit 1
        fi
        log_success "✓ Python $python_version"
    fi
    
    # Check pip
    if ! command -v pip3 &> /dev/null && ! python3 -m pip --version &> /dev/null; then
        missing_deps+=("pip3")
    else
        log_success "✓ pip available"
    fi
    
    # Check venv module
    if ! python3 -m venv --help &> /dev/null; then
        missing_deps+=("python3-venv")
    else
        log_success "✓ venv module available"
    fi
    
    # Check curl
    if ! command -v curl &> /dev/null; then
        missing_deps+=("curl")
    else
        log_success "✓ curl available"
    fi
    
    # Check git (optional but recommended)
    if ! command -v git &> /dev/null; then
        log_warn "⚠ git not found (optional)"
    else
        log_success "✓ git available"
    fi
    
    if [ ${#missing_deps[@]} -gt 0 ]; then
        log_error "Missing required dependencies: ${missing_deps[*]}"
        echo ""
        echo "Please install missing dependencies:"
        echo ""
        
        case "$(uname -s)" in
            Linux*)
                if [ -f /etc/debian_version ]; then
                    echo "  sudo apt-get update"
                    echo "  sudo apt-get install -y ${missing_deps[*]}"
                elif [ -f /etc/fedora-release ]; then
                    echo "  sudo dnf install -y ${missing_deps[*]}"
                elif [ -f /etc/arch-release ]; then
                    echo "  sudo pacman -S ${missing_deps[*]}"
                fi
                ;;
            Darwin*)
                echo "  brew install ${missing_deps[*]}"
                ;;
        esac
        exit 1
    fi
}

check_permissions() {
    log_info "Checking filesystem permissions..."
    
    # Check write permissions in install directory
    if [ ! -w "$INSTALL_DIR" ]; then
        log_error "No write permission in installation directory: $INSTALL_DIR"
        exit 1
    fi
    log_success "✓ Install directory writable"
    
    # Check/create config directory
    if [ ! -d "$CONFIG_DIR" ]; then
        mkdir -p "$CONFIG_DIR" || {
            log_error "Cannot create config directory: $CONFIG_DIR"
            exit 1
        }
    fi
    
    if [ ! -w "$CONFIG_DIR" ]; then
        log_error "No write permission in config directory: $CONFIG_DIR"
        exit 1
    fi
    log_success "✓ Config directory writable"
    
    # Check if we can create symlink (optional)
    if [ -w "/usr/local/bin" ] || sudo -n true 2>/dev/null; then
        log_success "✓ Can create system symlink (with sudo)"
    else
        log_warn "⚠ Cannot create system symlink (sudo required)"
    fi
}

check_disk_space() {
    log_info "Checking disk space..."
    
    # Get available space in GB
    if command -v df &> /dev/null; then
        local available_gb
        case "$(uname -s)" in
            Linux*)
                available_gb=$(df -BG "$INSTALL_DIR" | tail -1 | awk '{print $4}' | sed 's/G//')
                ;;
            Darwin*)
                available_gb=$(df -g "$INSTALL_DIR" | tail -1 | awk '{print $4}')
                ;;
        esac
        
        log_info "Available disk space: ${available_gb}GB"
        
        if [ "$available_gb" -lt "$MIN_DISK_SPACE_GB" ]; then
            log_warn "⚠ Warning: Less than ${MIN_DISK_SPACE_GB}GB free (${available_gb}GB available)"
            echo "   This may cause issues with AI models and file processing."
            read -p "   Continue anyway? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
        else
            log_success "✓ ${available_gb}GB available (>= ${MIN_DISK_SPACE_GB}GB required)"
        fi
    else
        log_warn "⚠ Cannot check disk space (df not available)"
    fi
}

check_network_connectivity() {
    log_info "Checking network connectivity..."
    
    # Check if we can reach PyPI
    if curl -s --max-time 5 -I https://pypi.org > /dev/null 2>&1; then
        log_success "✓ PyPI reachable"
    else
        log_warn "⚠ Cannot reach PyPI (pip install may fail)"
    fi
    
    # Check if we can reach Ollama
    if curl -s --max-time 5 -I https://ollama.com > /dev/null 2>&1; then
        log_success "✓ Ollama site reachable"
    else
        log_warn "⚠ Cannot reach ollama.com"
    fi
}

run_preflight_checks() {
    echo ""
    echo "═══════════════════════════════════════════════════════════"
    echo "  PRE-FLIGHT CHECKS"
    echo "═══════════════════════════════════════════════════════════"
    echo ""
    
    check_existing_installation
    check_os_compatibility
    check_system_dependencies
    check_permissions
    check_disk_space
    check_network_connectivity
    
    echo ""
    log_success "✓ All pre-flight checks passed"
    echo ""
}

# ============================================================================
# INSTALLATION STEPS
# ============================================================================

install_virtual_environment() {
    log_info "Creating Python virtual environment..."
    
    if [ -d "$VENV_DIR" ]; then
        log_warn "Virtual environment already exists, recreating..."
        rm -rf "$VENV_DIR"
    fi
    
    python3 -m venv "$VENV_DIR"
    save_state "venv_created"
    log_success "✓ Virtual environment created"
}

install_dependencies() {
    log_info "Installing Python dependencies..."
    
    source "$VENV_DIR/bin/activate"
    
    # Upgrade pip
    pip install --upgrade pip --quiet
    log_info "pip upgraded"
    
    # Install dependencies with locked versions
    if [ -f "$INSTALL_DIR/requirements.txt" ]; then
        pip install -r "$INSTALL_DIR/requirements.txt" --quiet
        save_state "dependencies_installed"
        log_success "✓ Dependencies installed"
    else
        log_error "requirements.txt not found"
        exit 1
    fi
}

install_ollama() {
    log_info "Checking for Ollama..."
    
    if command -v ollama &> /dev/null; then
        log_success "✓ Ollama already installed"
        
        # Check if Ollama is running
        if curl -s http://localhost:11434/api/version > /dev/null 2>&1; then
            log_success "✓ Ollama service running"
        else
            log_warn "⚠ Ollama installed but not running"
            echo "  Please start Ollama: 'ollama serve' or system service"
        fi
    else
        log_warn "⚠ Ollama not found"
        
        case "$(uname -s)" in
            Linux*)
                echo ""
                echo "Installing Ollama..."
                curl -fsSL https://ollama.com/install.sh | sh
                log_success "✓ Ollama installed"
                
                # Try to start Ollama service
                if systemctl is-active --quiet ollama 2>/dev/null; then
                    log_success "✓ Ollama service is running"
                else
                    log_warn "⚠ Start Ollama with: sudo systemctl start ollama"
                fi
                ;;
            Darwin*)
                log_warn "Please install Ollama manually:"
                echo "  1. Visit https://ollama.com/download"
                echo "  2. Download and install Ollama for macOS"
                echo "  3. Run this installer again"
                exit 1
                ;;
        esac
    fi
}

pull_ollama_models() {
    log_info "Pulling AI models..."
    
    if ! command -v ollama &> /dev/null; then
        log_warn "⚠ Skipping model download (Ollama not available)"
        return
    fi
    
    # Check if Ollama is responsive
    if ! curl -s http://localhost:11434/api/version > /dev/null 2>&1; then
        log_warn "⚠ Skipping model download (Ollama not running)"
        echo "  Start Ollama and run: ollama pull llama3.3 && ollama pull qwen2.5"
        return
    fi
    
    echo "  Downloading llama3.3 (this may take several minutes)..."
    if ollama pull llama3.3 >> "$LOG_FILE" 2>&1; then
        log_success "✓ llama3.3 downloaded"
    else
        log_warn "⚠ Failed to download llama3.3 (you can download it later)"
    fi
    
    echo "  Downloading qwen2.5..."
    if ollama pull qwen2.5 >> "$LOG_FILE" 2>&1; then
        log_success "✓ qwen2.5 downloaded"
    else
        log_warn "⚠ Failed to download qwen2.5 (you can download it later)"
    fi
    
    save_state "ollama_models_pulled"
}

create_configuration() {
    log_info "Creating configuration..."
    
    if [ -f "$CONFIG_DIR/config.json" ] && [ ! -f "$CONFIG_DIR/config.json.backup" ]; then
        log_warn "⚠ Configuration already exists, keeping existing"
        return
    fi
    
    if [ -f "$INSTALL_DIR/config.example.json" ]; then
        cp "$INSTALL_DIR/config.example.json" "$CONFIG_DIR/config.json"
        save_state "config_created"
        log_success "✓ Configuration created at $CONFIG_DIR/config.json"
    else
        log_error "config.example.json not found"
        exit 1
    fi
}

create_symlink() {
    log_info "Creating system command..."
    
    # Make organize.py executable
    chmod +x "$INSTALL_DIR/organize.py"
    
    echo ""
    read -p "→ Create system-wide 'organize' command? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if sudo ln -sf "$INSTALL_DIR/organize.py" /usr/local/bin/organize 2>/dev/null; then
            save_state "symlink_created"
            log_success "✓ Command 'organize' created"
        else
            log_warn "⚠ Could not create symlink (sudo required)"
            echo "  You can run: sudo ln -sf $INSTALL_DIR/organize.py /usr/local/bin/organize"
        fi
    else
        log_info "Skipped symlink creation"
    fi
}

# ============================================================================
# POST-INSTALL HEALTH CHECKS
# ============================================================================

health_check_python_env() {
    log_info "Verifying Python environment..."
    
    source "$VENV_DIR/bin/activate"
    
    # Check critical packages
    local packages=("click" "rich" "ollama" "watchdog")
    for pkg in "${packages[@]}"; do
        if python3 -c "import $pkg" 2>/dev/null; then
            log_success "✓ Package '$pkg' available"
        else
            log_error "✗ Package '$pkg' missing"
            return 1
        fi
    done
}

health_check_ollama() {
    log_info "Verifying Ollama connectivity..."
    
    if ! command -v ollama &> /dev/null; then
        log_warn "⚠ Ollama not installed"
        return 0  # Not fatal
    fi
    
    if curl -s http://localhost:11434/api/version > /dev/null 2>&1; then
        local version=$(curl -s http://localhost:11434/api/version | grep -o '"version":"[^"]*"' | cut -d'"' -f4)
        log_success "✓ Ollama running (version: ${version:-unknown})"
    else
        log_warn "⚠ Ollama not responding at localhost:11434"
        echo "  Start Ollama service to use AI features"
    fi
}

health_check_cli() {
    log_info "Verifying CLI functionality..."
    
    source "$VENV_DIR/bin/activate"
    
    # Test that the CLI can be imported
    if python3 -c "from smartfile.cli.main import cli; print('OK')" 2>/dev/null | grep -q "OK"; then
        log_success "✓ CLI module loads successfully"
    else
        log_error "✗ CLI module failed to load"
        return 1
    fi
    
    # Test organize.py
    if [ -x "$INSTALL_DIR/organize.py" ]; then
        log_success "✓ organize.py is executable"
    else
        log_error "✗ organize.py is not executable"
        return 1
    fi
}

health_check_config() {
    log_info "Verifying configuration..."
    
    if [ -f "$CONFIG_DIR/config.json" ]; then
        # Validate JSON
        if python3 -c "import json; json.load(open('$CONFIG_DIR/config.json'))" 2>/dev/null; then
            log_success "✓ Configuration file valid"
        else
            log_error "✗ Configuration file is invalid JSON"
            return 1
        fi
    else
        log_error "✗ Configuration file missing"
        return 1
    fi
}

run_health_checks() {
    echo ""
    echo "═══════════════════════════════════════════════════════════"
    echo "  POST-INSTALL HEALTH CHECKS"
    echo "═══════════════════════════════════════════════════════════"
    echo ""
    
    local failed=false
    
    health_check_python_env || failed=true
    health_check_ollama || failed=true
    health_check_cli || failed=true
    health_check_config || failed=true
    
    echo ""
    if [ "$failed" = true ]; then
        log_warn "⚠ Some health checks failed (see above)"
        log_warn "Installation may be incomplete. Check $LOG_FILE for details."
    else
        log_success "✓ All health checks passed"
    fi
    echo ""
}

# ============================================================================
# MAIN INSTALLATION FLOW
# ============================================================================

main() {
    # Initialize
    print_header
    setup_logging
    load_state
    
    # Pre-flight checks
    run_preflight_checks
    
    # Installation
    echo "═══════════════════════════════════════════════════════════"
    echo "  INSTALLATION"
    echo "═══════════════════════════════════════════════════════════"
    echo ""
    
    install_virtual_environment
    install_dependencies
    install_ollama
    pull_ollama_models
    create_configuration
    create_symlink
    
    # Post-install verification
    run_health_checks
    
    # Clear state on success
    clear_state
    
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
    echo "Installation log: $LOG_FILE"
    echo ""
    log_success "Happy organizing! 📂"
}

# Run main installation
main "$@"
