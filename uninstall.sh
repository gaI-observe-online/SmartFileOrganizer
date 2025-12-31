#!/bin/bash
# SmartFileOrganizer Uninstall Script
# Completely removes Smart FileOrganizer and all related files

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
INSTALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="$HOME/.organizer"
UNINSTALL_LOG="$CONFIG_DIR/uninstall.log"
VENV_DIR="$INSTALL_DIR/venv"
SYMLINK="/usr/local/bin/organize"

# Logging functions
log_info() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] [INFO] $*" | tee -a "$UNINSTALL_LOG"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] [ERROR] $*${NC}" | tee -a "$UNINSTALL_LOG"
}

log_warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] [WARN] $*${NC}" | tee -a "$UNINSTALL_LOG"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] [SUCCESS] $*${NC}" | tee -a "$UNINSTALL_LOG"
}

print_header() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║      SmartFileOrganizer - Uninstall                        ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
}

# Main uninstall function
main() {
    print_header
    
    # Create log directory if it doesn't exist
    mkdir -p "$CONFIG_DIR"
    log_info "Uninstall started"
    
    echo -e "${YELLOW}⚠  WARNING: This will completely remove SmartFileOrganizer${NC}"
    echo ""
    echo "The following will be removed:"
    echo "  • Virtual environment: $VENV_DIR"
    echo "  • Configuration directory: $CONFIG_DIR"
    echo "  • System symlink: $SYMLINK (if exists)"
    echo "  • All databases, logs, and audit trails"
    echo ""
    echo "The source code in $INSTALL_DIR will NOT be removed."
    echo ""
    read -p "Are you sure you want to continue? (yes/N): " -r
    echo
    
    if [[ ! $REPLY == "yes" ]]; then
        log_info "Uninstall cancelled by user"
        echo "Uninstall cancelled."
        exit 0
    fi
    
    echo ""
    echo "Uninstalling SmartFileOrganizer..."
    echo ""
    
    # Remove virtual environment
    if [ -d "$VENV_DIR" ]; then
        log_info "Removing virtual environment: $VENV_DIR"
        rm -rf "$VENV_DIR"
        log_success "✓ Virtual environment removed"
    else
        log_warn "Virtual environment not found, skipping"
    fi
    
    # Remove system symlink
    if [ -L "$SYMLINK" ]; then
        log_info "Removing system symlink: $SYMLINK"
        if sudo rm -f "$SYMLINK" 2>/dev/null; then
            log_success "✓ System symlink removed"
        else
            log_warn "⚠ Could not remove symlink (may need sudo)"
            echo "  You can manually remove it with: sudo rm $SYMLINK"
        fi
    else
        log_warn "System symlink not found, skipping"
    fi
    
    # Ask about config directory
    if [ -d "$CONFIG_DIR" ]; then
        echo ""
        echo "Configuration directory contains:"
        echo "  • config.json - Your settings"
        echo "  • *.db - File organization database"
        echo "  • *.jsonl - Audit logs"
        echo "  • install/uninstall logs"
        echo ""
        read -p "Remove configuration directory? (y/N): " -n 1 -r
        echo
        
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log_info "Removing configuration directory: $CONFIG_DIR"
            # Create a final log entry before removal
            log_success "Configuration directory removal approved by user"
            
            # Save the uninstall log before removing
            if [ -f "$UNINSTALL_LOG" ]; then
                TIMESTAMP=$(date +%Y%m%d-%H%M%S)
                cp "$UNINSTALL_LOG" "/tmp/smartfile-uninstall-$TIMESTAMP.log"
                echo "Uninstall log saved to: /tmp/smartfile-uninstall-$TIMESTAMP.log"
            fi
            
            rm -rf "$CONFIG_DIR"
            echo -e "${GREEN}✓ Configuration directory removed${NC}"
        else
            log_info "Configuration directory kept by user request"
            echo "Configuration directory kept at: $CONFIG_DIR"
        fi
    else
        log_warn "Configuration directory not found, skipping"
    fi
    
    # Remove __pycache__ directories
    if [ -d "$INSTALL_DIR/src" ]; then
        log_info "Removing Python cache files"
        find "$INSTALL_DIR/src" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
        find "$INSTALL_DIR/src" -type f -name "*.pyc" -delete 2>/dev/null || true
        log_success "✓ Cache files removed"
    fi
    
    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║          Uninstall Complete                                 ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
    echo "SmartFileOrganizer has been removed from your system."
    echo ""
    echo "Source code remains at: $INSTALL_DIR"
    echo "You can safely delete this directory if you no longer need it."
    echo ""
    echo "Thank you for using SmartFileOrganizer! 👋"
    echo ""
}

main "$@"
