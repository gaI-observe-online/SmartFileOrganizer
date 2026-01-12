#!/bin/bash
# SmartFileOrganizer Uninstall Script
# Completely removes SmartFileOrganizer and all related files

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

# CLI flags
DRY_RUN=false
PURGE_CONFIG=false

# Logging functions
log_info() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] [INFO] $*" | tee -a "$UNINSTALL_LOG" 2>/dev/null || echo "[$(date +'%Y-%m-%d %H:%M:%S')] [INFO] $*"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] [ERROR] $*${NC}" | tee -a "$UNINSTALL_LOG" 2>/dev/null || echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] [ERROR] $*${NC}"
}

log_warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] [WARN] $*${NC}" | tee -a "$UNINSTALL_LOG" 2>/dev/null || echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] [WARN] $*${NC}"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] [SUCCESS] $*${NC}" | tee -a "$UNINSTALL_LOG" 2>/dev/null || echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] [SUCCESS] $*${NC}"
}

print_header() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║      SmartFileOrganizer - Uninstall                        ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
}

show_help() {
    cat << 'EOF'
SmartFileOrganizer Uninstall Script

USAGE:
    ./uninstall.sh [OPTIONS]

OPTIONS:
    -h, --help          Show this help message
    --dry-run           Show what would be removed without making changes
    --purge-config      Remove configuration and data (default: preserve)

EXAMPLES:
    # Standard uninstall (preserves config)
    ./uninstall.sh
    
    # Preview what will be removed
    ./uninstall.sh --dry-run
    
    # Complete removal including config
    ./uninstall.sh --purge-config

EOF
    exit 0
}

# Safety check: ensure path is within allowed directories
safe_remove() {
    local path="$1"
    local description="$2"
    
    # Resolve to absolute path
    local abs_path=$(cd "$(dirname "$path")" 2>/dev/null && pwd)/$(basename "$path") || {
        log_warn "Cannot resolve path: $path"
        return 1
    }
    
    # Safety checks - never remove these
    local forbidden_paths=(
        "/"
        "$HOME"
        "$HOME/"
        "/usr"
        "/etc"
        "/var"
        "/bin"
        "/sbin"
    )
    
    for forbidden in "${forbidden_paths[@]}"; do
        if [ "$abs_path" = "$forbidden" ]; then
            log_error "SAFETY: Refusing to remove protected path: $abs_path"
            return 1
        fi
    done
    
    # Verify path starts with install root or config root
    if [[ ! "$abs_path" =~ ^$INSTALL_DIR ]] && [[ ! "$abs_path" =~ ^$CONFIG_DIR ]] && [[ ! "$abs_path" =~ ^/usr/local/bin ]]; then
        log_error "SAFETY: Path outside install boundaries: $abs_path"
        return 1
    fi
    
    # Verify path exists
    if [ ! -e "$abs_path" ]; then
        log_warn "$description not found, skipping: $abs_path"
        return 0
    fi
    
    if [ "$DRY_RUN" = true ]; then
        echo "[DRY RUN] Would remove: $description ($abs_path)"
    else
        log_info "Removing $description: $abs_path"
        rm -rf "$abs_path"
        log_success "✓ Removed $description"
    fi
}

parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --purge-config)
                PURGE_CONFIG=true
                shift
                ;;
            *)
                echo "Unknown option: $1"
                echo "Run './uninstall.sh --help' for usage information"
                exit 1
                ;;
        esac
    done
}

# Main uninstall function
main() {
    # Parse arguments first
    parse_arguments "$@"
    
    print_header
    
    # Create log directory if it doesn't exist (unless dry run)
    if [ "$DRY_RUN" = false ]; then
        mkdir -p "$CONFIG_DIR" 2>/dev/null || true
    fi
    log_info "Uninstall started"
    
    if [ "$DRY_RUN" = true ]; then
        echo -e "${YELLOW}DRY RUN MODE - No changes will be made${NC}"
        echo ""
    else
        echo -e "${YELLOW}⚠  WARNING: This will remove SmartFileOrganizer${NC}"
        echo ""
    fi
    
    echo "The following will be removed:"
    echo "  • Virtual environment: $VENV_DIR"
    if [ "$PURGE_CONFIG" = true ]; then
        echo "  • Configuration directory: $CONFIG_DIR (--purge-config)"
    else
        echo "  • Configuration directory: preserved (use --purge-config to remove)"
    fi
    echo "  • System symlink: $SYMLINK (if exists)"
    echo "  • Python cache files"
    echo ""
    echo "The source code in $INSTALL_DIR will NOT be removed."
    echo ""
    
    if [ "$DRY_RUN" = false ]; then
        read -p "Continue with uninstall? (yes/N): " -r
        echo
        
        if [[ ! $REPLY == "yes" ]]; then
            log_info "Uninstall cancelled by user"
            echo "Uninstall cancelled."
            exit 0
        fi
    fi
    
    echo ""
    echo "Uninstalling SmartFileOrganizer..."
    echo ""
    
    # Remove virtual environment
    safe_remove "$VENV_DIR" "virtual environment"
    
    # Remove system symlink
    if [ -L "$SYMLINK" ] || [ -f "$SYMLINK" ]; then
        if [ "$DRY_RUN" = true ]; then
            echo "[DRY RUN] Would remove: system symlink ($SYMLINK)"
        else
            log_info "Removing system symlink: $SYMLINK"
            sudo rm -f "$SYMLINK" 2>/dev/null || {
                log_warn "⚠ Could not remove symlink (may need sudo)"
                echo "  You can manually remove it with: sudo rm $SYMLINK"
            }
            log_success "✓ System symlink removed"
        fi
    else
        log_warn "System symlink not found, skipping"
    fi
    
    # Remove Python cache
    if [ -d "$INSTALL_DIR/src" ]; then
        if [ "$DRY_RUN" = true ]; then
            echo "[DRY RUN] Would remove: Python cache files"
        else
            log_info "Removing Python cache files"
            find "$INSTALL_DIR/src" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
            find "$INSTALL_DIR/src" -type f -name "*.pyc" -delete 2>/dev/null || true
            log_success "✓ Cache files removed"
        fi
    fi
    
    # Handle config directory
    if [ "$PURGE_CONFIG" = true ]; then
        if [ -d "$CONFIG_DIR" ]; then
            if [ "$DRY_RUN" = true ]; then
                echo "[DRY RUN] Would remove: configuration directory ($CONFIG_DIR)"
            else
                # Save uninstall log before removal
                TIMESTAMP=$(date +%Y%m%d-%H%M%S)
                if [ -f "$UNINSTALL_LOG" ]; then
                    cp "$UNINSTALL_LOG" "${TMPDIR:-/tmp}/smartfile-uninstall-$TIMESTAMP.log" 2>/dev/null || true
                    echo "Uninstall log saved to: ${TMPDIR:-/tmp}/smartfile-uninstall-$TIMESTAMP.log"
                fi
                
                safe_remove "$CONFIG_DIR" "configuration directory"
            fi
        else
            log_warn "Configuration directory not found, skipping"
        fi
    else
        log_info "Configuration directory preserved at: $CONFIG_DIR"
        echo "  To remove config later, run: rm -rf $CONFIG_DIR"
    fi
    
    echo ""
    if [ "$DRY_RUN" = true ]; then
        echo "╔════════════════════════════════════════════════════════════╗"
        echo "║          Dry Run Complete                                   ║"
        echo "╚════════════════════════════════════════════════════════════╝"
        echo ""
        echo "Run without --dry-run to perform actual uninstall."
    else
        echo "╔════════════════════════════════════════════════════════════╗"
        echo "║          Uninstall Complete                                 ║"
        echo "╚════════════════════════════════════════════════════════════╝"
        echo ""
        echo "SmartFileOrganizer has been removed from your system."
        if [ "$PURGE_CONFIG" = false ]; then
            echo "Configuration preserved at: $CONFIG_DIR"
        fi
        echo ""
        echo "Thank you for using SmartFileOrganizer! 👋"
    fi
    echo ""
}

main "$@"
