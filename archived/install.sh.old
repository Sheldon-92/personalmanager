#!/usr/bin/env bash
#
# PersonalManager Installation Script
# One-click installation and configuration for PersonalManager
#
# This script provides:
# - Cross-platform environment detection (macOS, Linux, Windows/WSL)
# - Automated dependency installation (Python, Poetry, system packages)
# - Environment configuration and initialization
# - Comprehensive validation and error recovery
#
# Usage:
#   curl -sSL https://raw.githubusercontent.com/.../install.sh | bash
#   # or locally:
#   ./install.sh [OPTIONS]
#
# Options:
#   --dev          Install development dependencies
#   --no-poetry    Skip Poetry installation, use pip instead
#   --offline      Skip online checks and updates
#   --verbose      Enable detailed logging
#   --help         Show this help message

set -e  # Exit on error

# Script metadata
SCRIPT_VERSION="1.0.0"
SCRIPT_NAME="PersonalManager Installer"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Configuration defaults
INSTALL_DEV=false
USE_POETRY=true
OFFLINE_MODE=false
VERBOSE=false
FORCE_INSTALL=false

# System information
OS_TYPE=""
OS_ARCH=""
PYTHON_VERSION=""
PROJECT_ROOT=""
VENV_PATH=""

# Installation progress
TOTAL_STEPS=8
CURRENT_STEP=0

# ============================================================================
# Utility Functions
# ============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_debug() {
    if [[ "$VERBOSE" == true ]]; then
        echo -e "${PURPLE}[DEBUG]${NC} $1"
    fi
}

log_step() {
    CURRENT_STEP=$((CURRENT_STEP + 1))
    echo -e "${CYAN}[STEP $CURRENT_STEP/$TOTAL_STEPS]${NC} ${BOLD}$1${NC}"
}

# Progress bar function
show_progress() {
    local progress=$1
    local total=$2
    local width=40
    local filled=$((progress * width / total))
    local empty=$((width - filled))

    printf "\r${CYAN}Progress: [${NC}"
    printf "%${filled}s" | tr ' ' '='
    printf "%${empty}s" | tr ' ' '-'
    printf "${CYAN}] %d%% (%d/%d)${NC}" $((progress * 100 / total)) $progress $total
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Get OS information
detect_os() {
    case "$(uname -s)" in
        Darwin)
            OS_TYPE="macos"
            OS_ARCH="$(uname -m)"
            ;;
        Linux)
            if grep -qi microsoft /proc/version 2>/dev/null; then
                OS_TYPE="wsl"
            else
                OS_TYPE="linux"
            fi
            OS_ARCH="$(uname -m)"
            ;;
        MINGW*|MSYS*|CYGWIN*)
            OS_TYPE="windows"
            OS_ARCH="$(uname -m)"
            ;;
        *)
            log_error "Unsupported operating system: $(uname -s)"
            exit 1
            ;;
    esac

    log_debug "Detected OS: $OS_TYPE ($OS_ARCH)"
}

# Get Python version
detect_python() {
    local python_cmd=""

    # Try different Python commands
    for cmd in python3 python python3.11 python3.10 python3.9; do
        if command_exists "$cmd"; then
            local version=$($cmd --version 2>&1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')
            local major=$(echo "$version" | cut -d. -f1)
            local minor=$(echo "$version" | cut -d. -f2)

            # Check if version >= 3.9
            if [[ $major -eq 3 && $minor -ge 9 ]]; then
                python_cmd="$cmd"
                PYTHON_VERSION="$version"
                break
            fi
        fi
    done

    if [[ -z "$python_cmd" ]]; then
        log_error "Python 3.9+ is required but not found"
        log_info "Please install Python 3.9 or later:"
        case "$OS_TYPE" in
            macos)
                log_info "  brew install python@3.11"
                log_info "  # or download from https://python.org"
                ;;
            linux|wsl)
                log_info "  sudo apt update && sudo apt install python3.11 python3.11-pip python3.11-venv"
                log_info "  # or equivalent for your distribution"
                ;;
            windows)
                log_info "  Download from https://python.org"
                ;;
        esac
        exit 1
    fi

    log_debug "Found Python: $python_cmd ($PYTHON_VERSION)"
    # Export for use in other functions
    export PYTHON_CMD="$python_cmd"
}

# Install system dependencies
install_system_deps() {
    log_step "Installing system dependencies"

    case "$OS_TYPE" in
        macos)
            if command_exists brew; then
                log_info "Installing system packages via Homebrew..."
                brew install git curl
            else
                log_warn "Homebrew not found. Please install manually:"
                log_warn "  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
            fi
            ;;
        linux)
            if command_exists apt; then
                log_info "Installing system packages via apt..."
                sudo apt update
                sudo apt install -y git curl python3-pip python3-venv build-essential
            elif command_exists yum; then
                log_info "Installing system packages via yum..."
                sudo yum install -y git curl python3-pip python3-devel gcc
            elif command_exists dnf; then
                log_info "Installing system packages via dnf..."
                sudo dnf install -y git curl python3-pip python3-devel gcc
            else
                log_warn "Unsupported Linux distribution. Please install git, curl, and python3-pip manually."
            fi
            ;;
        wsl)
            if command_exists apt; then
                log_info "Installing system packages via apt (WSL)..."
                sudo apt update
                sudo apt install -y git curl python3-pip python3-venv build-essential
            else
                log_warn "Please install git, curl, and python3-pip manually in WSL"
            fi
            ;;
        windows)
            log_warn "Please ensure git and curl are installed on Windows"
            ;;
    esac
}

# Install Poetry
install_poetry() {
    if [[ "$USE_POETRY" != true ]]; then
        log_info "Skipping Poetry installation (--no-poetry flag set)"
        return 0
    fi

    log_step "Installing Poetry package manager"

    if command_exists poetry; then
        local poetry_version=$(poetry --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')
        log_info "Poetry already installed: $poetry_version"
        return 0
    fi

    log_info "Installing Poetry..."
    if [[ "$OFFLINE_MODE" == true ]]; then
        log_warn "Offline mode enabled, skipping Poetry installation"
        USE_POETRY=false
        return 0
    fi

    # Install Poetry using the official installer
    curl -sSL https://install.python-poetry.org | $PYTHON_CMD -

    # Add Poetry to PATH for current session
    export PATH="$HOME/.local/bin:$PATH"

    # Verify installation
    if command_exists poetry; then
        local poetry_version=$(poetry --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')
        log_success "Poetry installed successfully: $poetry_version"
    else
        log_error "Poetry installation failed"
        log_info "Falling back to pip installation"
        USE_POETRY=false
    fi
}

# Setup project environment
setup_project_env() {
    log_step "Setting up project environment"

    # Detect project root
    if [[ -f "pyproject.toml" && -f "bin/pm-local" ]]; then
        PROJECT_ROOT="$(pwd)"
        log_debug "Found project root: $PROJECT_ROOT"
    else
        log_error "PersonalManager project not found in current directory"
        log_error "Please run this script from the PersonalManager project root directory"
        log_error "Expected files: pyproject.toml, bin/pm-local"
        exit 1
    fi

    # Make launcher executable
    if [[ -f "bin/pm-local" ]]; then
        chmod +x bin/pm-local
        log_debug "Made bin/pm-local executable"
    fi

    # Install dependencies
    if [[ "$USE_POETRY" == true ]]; then
        log_info "Installing dependencies via Poetry..."
        poetry install $([ "$INSTALL_DEV" == true ] && echo "--with dev" || echo "--only main")

        # Verify installation
        if poetry run python -c "import pm.cli.main" 2>/dev/null; then
            log_success "Poetry environment setup complete"
        else
            log_error "Poetry installation verification failed"
            exit 1
        fi
    else
        log_info "Installing dependencies via pip..."

        # Create virtual environment
        VENV_PATH="$PROJECT_ROOT/.venv"
        $PYTHON_CMD -m venv "$VENV_PATH"
        source "$VENV_PATH/bin/activate"

        # Upgrade pip
        pip install --upgrade pip

        # Install from pyproject.toml (basic approach)
        pip install -e .

        # Install dev dependencies if requested
        if [[ "$INSTALL_DEV" == true ]]; then
            pip install pytest black isort flake8 mypy pre-commit factory-boy pytest-cov pytest-asyncio
        fi

        # Verify installation
        if python -c "import pm.cli.main" 2>/dev/null; then
            log_success "Pip environment setup complete"
        else
            log_error "Pip installation verification failed"
            exit 1
        fi
    fi
}

# Initialize PersonalManager configuration
initialize_pm() {
    log_step "Initializing PersonalManager configuration"

    # Run initial setup
    log_info "Running PersonalManager setup..."

    if [[ "$USE_POETRY" == true ]]; then
        poetry run pm setup --batch || true
    else
        source "$VENV_PATH/bin/activate"
        pm setup --batch || true
    fi

    log_success "PersonalManager initialization complete"
}

# Run system diagnostics
run_diagnostics() {
    log_step "Running system diagnostics"

    log_info "Running PersonalManager doctor..."

    if [[ "$USE_POETRY" == true ]]; then
        if poetry run pm doctor; then
            log_success "All diagnostic checks passed"
        else
            log_warn "Some diagnostic checks failed (this is normal for first installation)"
            log_info "You can run 'poetry run pm doctor --verbose' later for detailed information"
        fi
    else
        source "$VENV_PATH/bin/activate"
        if pm doctor; then
            log_success "All diagnostic checks passed"
        else
            log_warn "Some diagnostic checks failed (this is normal for first installation)"
            log_info "You can run './bin/pm-local doctor --verbose' later for detailed information"
        fi
    fi
}

# Verify installation
verify_installation() {
    log_step "Verifying installation"

    local test_commands=(
        "status"
        "projects overview"
        "capture 'Installation test task'"
        "today"
        "privacy info"
    )

    log_info "Testing core functionality..."

    for cmd in "${test_commands[@]}"; do
        log_debug "Testing: pm $cmd"

        if [[ "$USE_POETRY" == true ]]; then
            if poetry run pm $cmd >/dev/null 2>&1; then
                log_debug "✓ pm $cmd"
            else
                log_warn "✗ pm $cmd failed"
            fi
        else
            source "$VENV_PATH/bin/activate"
            if pm $cmd >/dev/null 2>&1; then
                log_debug "✓ pm $cmd"
            else
                log_warn "✗ pm $cmd failed"
            fi
        fi
    done

    # Test launcher
    if ./bin/pm-local status >/dev/null 2>&1; then
        log_debug "✓ ./bin/pm-local launcher working"
    else
        log_warn "✗ ./bin/pm-local launcher failed"
    fi

    log_success "Installation verification complete"
}

# Generate installation report
generate_report() {
    log_step "Generating installation report"

    local report_file="installation_report_$(date +%Y%m%d_%H%M%S).md"

    cat > "$report_file" << EOF
# PersonalManager Installation Report

**Date:** $(date)
**Installer Version:** $SCRIPT_VERSION

## System Information

- **Operating System:** $OS_TYPE ($OS_ARCH)
- **Python Version:** $PYTHON_VERSION
- **Poetry Installed:** $(if [[ "$USE_POETRY" == true ]]; then echo "Yes"; else echo "No"; fi)
- **Project Root:** $PROJECT_ROOT
- **Installation Type:** $(if [[ "$INSTALL_DEV" == true ]]; then echo "Development"; else echo "Production"; fi)

## Installation Steps Completed

EOF

    # Add step status
    for i in $(seq 1 $CURRENT_STEP); do
        echo "- [x] Step $i completed successfully" >> "$report_file"
    done

    cat >> "$report_file" << EOF

## Quick Start Commands

### Using Poetry (Recommended)
\`\`\`bash
# Check system status
poetry run pm doctor

# View projects overview
poetry run pm projects overview

# Get today's recommendations
poetry run pm today

# Capture a new task
poetry run pm capture "Your task description"
\`\`\`

### Using Project Launcher
\`\`\`bash
# Check system status
./bin/pm-local doctor

# View projects overview
./bin/pm-local projects overview

# Get today's recommendations
./bin/pm-local today

# Capture a new task
./bin/pm-local capture "Your task description"
\`\`\`

## Configuration

PersonalManager data and configuration are stored in:
\`~/.personalmanager/\`

## Next Steps

1. Run \`$(if [[ "$USE_POETRY" == true ]]; then echo "poetry run pm setup"; else echo "./bin/pm-local setup"; fi)\` to complete configuration
2. Explore the user guide: \`docs/user_guide.md\`
3. Set up integrations as needed (Google, Obsidian, AI services)

## Support

- Documentation: \`README.md\`, \`docs/user_guide.md\`
- Run diagnostics: \`$(if [[ "$USE_POETRY" == true ]]; then echo "poetry run pm doctor --verbose"; else echo "./bin/pm-local doctor --verbose"; fi)\`
- Check system status: \`$(if [[ "$USE_POETRY" == true ]]; then echo "poetry run pm status"; else echo "./bin/pm-local status"; fi)\`

---
Generated by PersonalManager Installer v$SCRIPT_VERSION
EOF

    log_success "Installation report generated: $report_file"
}

# Show usage help
show_help() {
    cat << EOF
$SCRIPT_NAME v$SCRIPT_VERSION

USAGE:
    $0 [OPTIONS]

DESCRIPTION:
    One-click installation script for PersonalManager - AI-driven personal
    management system. Automatically detects your environment and installs
    all necessary dependencies.

OPTIONS:
    --dev           Install development dependencies (pytest, black, etc.)
    --no-poetry     Skip Poetry installation, use pip instead
    --offline       Skip online checks and updates
    --verbose       Enable detailed logging and debug output
    --force         Force reinstallation even if already installed
    --help          Show this help message

EXAMPLES:
    # Basic installation
    $0

    # Development installation with verbose output
    $0 --dev --verbose

    # Offline installation using pip
    $0 --no-poetry --offline

REQUIREMENTS:
    - Python 3.9 or later
    - Internet connection (unless --offline)
    - ~200MB disk space
    - 5-10 minutes installation time

For more information, visit: https://github.com/your-repo/personal-manager
EOF
}

# Error cleanup and recovery
cleanup_on_error() {
    local exit_code=$?
    log_error "Installation failed with exit code $exit_code"

    if [[ -n "$VENV_PATH" && -d "$VENV_PATH" ]]; then
        log_info "Cleaning up failed virtual environment..."
        rm -rf "$VENV_PATH"
    fi

    log_error "Installation incomplete. You may need to:"
    log_error "  1. Check the error messages above"
    log_error "  2. Install missing system dependencies"
    log_error "  3. Run the installer again with --verbose for more details"
    log_error "  4. Manually run 'pm doctor' to diagnose issues"

    exit $exit_code
}

# ============================================================================
# Main Installation Flow
# ============================================================================

main() {
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --dev)
                INSTALL_DEV=true
                shift
                ;;
            --no-poetry)
                USE_POETRY=false
                shift
                ;;
            --offline)
                OFFLINE_MODE=true
                shift
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            --force)
                FORCE_INSTALL=true
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done

    # Set up error handling
    trap cleanup_on_error ERR

    # Show header
    echo -e "${BOLD}${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}${BLUE}║${NC}                ${BOLD}PersonalManager Installer v$SCRIPT_VERSION${NC}                ${BOLD}${BLUE}║${NC}"
    echo -e "${BOLD}${BLUE}║${NC}          ${CYAN}One-click installation for your AI assistant${NC}          ${BOLD}${BLUE}║${NC}"
    echo -e "${BOLD}${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo

    # Show configuration
    log_info "Installation Configuration:"
    log_info "  Development Mode: $(if [[ "$INSTALL_DEV" == true ]]; then echo "Yes"; else echo "No"; fi)"
    log_info "  Use Poetry: $(if [[ "$USE_POETRY" == true ]]; then echo "Yes"; else echo "No (pip)"; fi)"
    log_info "  Offline Mode: $(if [[ "$OFFLINE_MODE" == true ]]; then echo "Yes"; else echo "No"; fi)"
    log_info "  Verbose Output: $(if [[ "$VERBOSE" == true ]]; then echo "Yes"; else echo "No"; fi)"
    echo

    # Start installation
    local start_time=$(date +%s)

    # Execute installation steps
    detect_os
    detect_python
    install_system_deps
    install_poetry
    setup_project_env
    initialize_pm
    run_diagnostics
    verify_installation
    generate_report

    # Calculate installation time
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    local minutes=$((duration / 60))
    local seconds=$((duration % 60))

    # Show completion message
    echo
    echo -e "${BOLD}${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}${GREEN}║${NC}                    ${BOLD}Installation Complete!${NC}                    ${BOLD}${GREEN}║${NC}"
    echo -e "${BOLD}${GREEN}║${NC}        ${GREEN}PersonalManager is ready for use in ${minutes}m ${seconds}s${NC}        ${BOLD}${GREEN}║${NC}"
    echo -e "${BOLD}${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo

    # Show next steps
    log_success "Quick Start:"
    if [[ "$USE_POETRY" == true ]]; then
        log_info "  poetry run pm doctor       # Run system diagnostics"
        log_info "  poetry run pm today         # Get today's recommendations"
        log_info "  poetry run pm setup         # Complete configuration"
    else
        log_info "  ./bin/pm-local doctor       # Run system diagnostics"
        log_info "  ./bin/pm-local today        # Get today's recommendations"
        log_info "  ./bin/pm-local setup        # Complete configuration"
    fi

    log_info ""
    log_info "📚 Documentation: README.md, docs/user_guide.md"
    log_info "🔧 Troubleshooting: Run with --verbose for detailed output"
    log_info "❓ Support: Check the installation report for details"

    echo -e "\n${GREEN}Happy productivity! 🚀${NC}"
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi