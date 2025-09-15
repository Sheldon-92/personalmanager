#!/bin/bash

# PersonalManager Standalone Doctor Script
# Comprehensive system health check and diagnostics
# Can be used independently or alongside the main pm doctor command

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Colors and formatting
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Status icons
CHECK_PASS="✅"
CHECK_FAIL="❌"
CHECK_WARN="⚠️"
CHECK_SKIP="⏭️"
CHECK_INFO="ℹ️"

# Counters
CHECKS_TOTAL=0
CHECKS_PASSED=0
CHECKS_FAILED=0
CHECKS_WARNED=0
CHECKS_SKIPPED=0

# Configuration
VERBOSE=false
QUICK_MODE=false
FIX_MODE=false
EXPORT_FILE=""
CHECKS_LOG=""

# Logging functions
log_header() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE} $1 ${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

log_section() {
    echo -e "${CYAN}▶ $1${NC}"
}

log_pass() {
    echo -e "${CHECK_PASS} ${GREEN}PASS${NC} $1"
    ((CHECKS_PASSED++))
    log_to_file "PASS: $1"
}

log_fail() {
    echo -e "${CHECK_FAIL} ${RED}FAIL${NC} $1"
    ((CHECKS_FAILED++))
    log_to_file "FAIL: $1"
    if [[ -n "${2:-}" ]]; then
        echo -e "   ${YELLOW}Fix: $2${NC}"
        log_to_file "     Fix: $2"
    fi
}

log_warn() {
    echo -e "${CHECK_WARN} ${YELLOW}WARN${NC} $1"
    ((CHECKS_WARNED++))
    log_to_file "WARN: $1"
    if [[ -n "${2:-}" ]]; then
        echo -e "   ${YELLOW}Note: $2${NC}"
        log_to_file "     Note: $2"
    fi
}

log_skip() {
    echo -e "${CHECK_SKIP} ${PURPLE}SKIP${NC} $1"
    ((CHECKS_SKIPPED++))
    log_to_file "SKIP: $1"
}

log_info() {
    echo -e "${CHECK_INFO} ${BLUE}INFO${NC} $1"
    log_to_file "INFO: $1"
}

log_verbose() {
    if [[ "$VERBOSE" == "true" ]]; then
        echo -e "   ${CYAN}$1${NC}"
        log_to_file "     $1"
    fi
}

log_to_file() {
    if [[ -n "$CHECKS_LOG" ]]; then
        echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" >> "$CHECKS_LOG"
    fi
}

# Increment check counter
check_start() {
    ((CHECKS_TOTAL++))
}

# Usage information
usage() {
    cat << EOF
PersonalManager Standalone Doctor - System Health Diagnostics

USAGE:
    $0 [OPTIONS]

OPTIONS:
    --help              Show this help message
    --version           Show version information
    --verbose           Enable verbose output with detailed information
    --quick             Quick check mode (skip network and performance tests)
    --fix               Attempt to automatically fix detected issues
    --export FILE       Export detailed report to file (markdown format)
    --log FILE          Log all checks to file
    --silent            Suppress output (use with --export or --log)

EXAMPLES:
    $0                  # Run full diagnostic check
    $0 --quick          # Quick system check only
    $0 --verbose        # Detailed output with system information
    $0 --fix            # Run diagnostics and auto-fix issues
    $0 --export report.md --verbose  # Generate detailed report

EXIT CODES:
    0   All checks passed
    1   One or more critical checks failed
    2   Warnings detected (non-critical)
    64  Command line usage error
    130 Interrupted by user (Ctrl+C)

CATEGORIES:
    • System Environment    - Python, OS, architecture
    • Dependencies         - Python packages and system tools
    • PersonalManager      - Configuration, directories, permissions
    • Network & Security   - Connectivity and API access
    • Performance         - Memory, disk space, system resources
    • Integration         - External services and tools

For more comprehensive diagnostics, use: pm doctor
EOF
}

# Version information
show_version() {
    local version
    version=$(python3 -c "import toml; print(toml.load('$PROJECT_ROOT/pyproject.toml')['tool']['poetry']['version'])" 2>/dev/null || echo "unknown")

    cat << EOF
PersonalManager Standalone Doctor v${version}

System Information:
  OS: $(uname -s) $(uname -r)
  Architecture: $(uname -m)
  Python: $(python3 --version 2>/dev/null || echo "not found")
  Shell: ${SHELL:-unknown}
  User: $(whoami)
  Date: $(date)

Script Location: $0
Project Root: $PROJECT_ROOT
EOF
}

# Detect system information
detect_system() {
    local system_type=""
    case "$(uname -s)" in
        Darwin*)    system_type="macOS" ;;
        Linux*)
            if [[ -n "${WSL_DISTRO_NAME:-}" ]] || grep -qi microsoft /proc/version 2>/dev/null; then
                system_type="WSL"
            else
                system_type="Linux"
            fi
            ;;
        CYGWIN*|MINGW*|MSYS*) system_type="Windows" ;;
        *)          system_type="Unknown" ;;
    esac

    log_verbose "Detected system: $system_type $(uname -m)"
    echo "$system_type"
}

# Check Python installation and version
check_python() {
    log_section "Python Environment"

    check_start
    if ! command -v python3 &> /dev/null; then
        log_fail "Python 3 not found" "Install Python 3.9+ from https://python.org"
        return 1
    fi

    local python_version
    python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')")

    check_start
    if python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)" 2>/dev/null; then
        log_pass "Python version: $python_version"
        log_verbose "Python executable: $(which python3)"
        log_verbose "Python path: $(python3 -c "import sys; print(':'.join(sys.path[:3]))")"
    else
        log_fail "Python version too old: $python_version" "Upgrade to Python 3.9 or newer"
        return 1
    fi

    # Check virtual environment
    check_start
    if [[ -n "${VIRTUAL_ENV:-}" ]]; then
        log_info "Running in virtual environment: $(basename "$VIRTUAL_ENV")"
    elif [[ -n "${CONDA_DEFAULT_ENV:-}" ]]; then
        log_info "Running in Conda environment: $CONDA_DEFAULT_ENV"
    else
        log_warn "Not running in virtual environment" "Consider using virtual environments for isolation"
    fi
}

# Check system dependencies and tools
check_system_dependencies() {
    log_section "System Dependencies"

    local system_type
    system_type=$(detect_system)

    # Essential commands
    local essential_commands=("git" "curl" "tar" "pip")
    for cmd in "${essential_commands[@]}"; do
        check_start
        if command -v "$cmd" &> /dev/null; then
            local version
            case "$cmd" in
                git) version=$(git --version | head -1) ;;
                curl) version=$(curl --version | head -1) ;;
                pip) version=$(pip --version 2>/dev/null || pip3 --version 2>/dev/null) ;;
                *) version="available" ;;
            esac
            log_pass "$cmd: $version"
            log_verbose "$cmd location: $(which "$cmd")"
        else
            local install_hint=""
            case "$system_type" in
                "macOS") install_hint="brew install $cmd" ;;
                "Linux"|"WSL") install_hint="sudo apt install $cmd" ;;
            esac
            log_fail "$cmd not found" "$install_hint"
        fi
    done

    # Package managers
    check_start
    local package_managers=()
    case "$system_type" in
        "macOS")
            if command -v brew &> /dev/null; then
                log_pass "Package manager: Homebrew $(brew --version | head -1 | cut -d' ' -f2)"
            else
                log_warn "Homebrew not found" "Install: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
            fi
            ;;
        "Linux"|"WSL")
            if command -v apt &> /dev/null; then
                log_pass "Package manager: APT"
            elif command -v yum &> /dev/null; then
                log_pass "Package manager: YUM"
            elif command -v dnf &> /dev/null; then
                log_pass "Package manager: DNF"
            else
                log_warn "No recognized package manager found"
            fi
            ;;
    esac
}

# Check Python dependencies
check_python_dependencies() {
    log_section "Python Dependencies"

    # Check if we're in project directory
    if [[ ! -f "$PROJECT_ROOT/pyproject.toml" ]]; then
        log_skip "Not in PersonalManager project directory"
        return 0
    fi

    # Key dependencies to check
    local key_modules=("typer" "rich" "pydantic" "structlog" "watchdog" "yaml")

    for module in "${key_modules[@]}"; do
        check_start
        if python3 -c "import $module" 2>/dev/null; then
            local version=""
            case "$module" in
                yaml) version=$(python3 -c "import yaml; print(getattr(yaml, '__version__', 'unknown'))") ;;
                *) version=$(python3 -c "import $module; print(getattr($module, '__version__', 'unknown'))") ;;
            esac
            log_pass "$module: $version"
        else
            log_fail "$module not available" "Run: pip install -e . or poetry install"
        fi
    done

    # Check if PersonalManager can be imported
    check_start
    if python3 -c "from pm.core.config import PMConfig" 2>/dev/null; then
        log_pass "PersonalManager modules importable"
    else
        log_fail "PersonalManager modules not importable" "Run: pip install -e . from project root"
    fi
}

# Check package installation integrity
check_installation_integrity() {
    log_section "Installation Integrity"

    # Check if installed from offline package
    check_start
    local install_marker="${HOME}/.personalmanager/.offline_install_info"
    if [[ -f "$install_marker" ]]; then
        log_pass "Offline installation detected"
        log_verbose "Install info: $(cat "$install_marker" | head -3)"

        # Verify installation matches expected structure
        check_start
        local install_dir
        install_dir=$(grep "INSTALL_DIR=" "$install_marker" 2>/dev/null | cut -d'=' -f2- | tr -d '"')
        if [[ -n "$install_dir" && -d "$install_dir" ]]; then
            log_pass "Installation directory exists: $install_dir"

            # Check key components
            check_start
            local required_components=("venv/bin/activate" "src" "bin/pm-local")
            local missing_components=()

            for component in "${required_components[@]}"; do
                if [[ ! -e "$install_dir/$component" ]]; then
                    missing_components+=("$component")
                fi
            done

            if [[ ${#missing_components[@]} -eq 0 ]]; then
                log_pass "All installation components present"
            else
                log_fail "Missing components: ${missing_components[*]}" "Reinstall PersonalManager"
            fi
        else
            log_fail "Installation directory missing or invalid" "Check installation path in $install_marker"
        fi
    else
        log_info "Standard installation (not offline package)"
    fi
}

# Check for installation rollback capability
check_rollback_capability() {
    log_section "Rollback Capability"

    check_start
    local backup_dir="${HOME}/.personalmanager/backups/installation"
    if [[ -d "$backup_dir" ]]; then
        local backup_count
        backup_count=$(find "$backup_dir" -name "backup_*" -type d | wc -l)
        if [[ $backup_count -gt 0 ]]; then
            log_pass "Installation backups available: $backup_count"
            log_verbose "Backup directory: $backup_dir"

            # Check latest backup
            local latest_backup
            latest_backup=$(find "$backup_dir" -name "backup_*" -type d | sort -r | head -1)
            if [[ -n "$latest_backup" ]]; then
                local backup_age
                backup_age=$(( ($(date +%s) - $(stat -c %Y "$latest_backup" 2>/dev/null || stat -f %m "$latest_backup" 2>/dev/null || echo 0)) / 86400 ))
                log_verbose "Latest backup age: ${backup_age} days"

                if [[ $backup_age -lt 30 ]]; then
                    log_pass "Recent backup available for rollback"
                else
                    log_warn "Latest backup is $backup_age days old" "Consider creating fresh backup"
                fi
            fi
        else
            log_warn "Backup directory exists but no backups found"
        fi
    else
        log_warn "No installation backup capability" "Enable backups for rollback support"
    fi
}

# Check PersonalManager configuration
check_personalmanager_config() {
    log_section "PersonalManager Configuration"

    # Check if we can import PMConfig
    check_start
    if ! python3 -c "from pm.core.config import PMConfig" 2>/dev/null; then
        log_skip "PersonalManager not installed"
        return 0
    fi

    # Check configuration initialization
    check_start
    local config_status
    config_status=$(python3 -c "
from pm.core.config import PMConfig
try:
    config = PMConfig()
    print('initialized' if config.is_initialized() else 'not_initialized')
    print(config.config_file)
    print(config.data_dir)
except Exception as e:
    print(f'error:{e}')
" 2>/dev/null)

    local status=$(echo "$config_status" | head -1)
    case "$status" in
        "initialized")
            local config_file=$(echo "$config_status" | sed -n '2p')
            local data_dir=$(echo "$config_status" | sed -n '3p')
            log_pass "Configuration initialized"
            log_verbose "Config file: $config_file"
            log_verbose "Data directory: $data_dir"

            # Check data directory structure
            check_start
            local required_dirs=("tasks" "habits" "projects" "logs" "backups" "tokens")
            local missing_dirs=()

            for dir in "${required_dirs[@]}"; do
                if [[ ! -d "$data_dir/$dir" ]]; then
                    missing_dirs+=("$dir")
                fi
            done

            if [[ ${#missing_dirs[@]} -eq 0 ]]; then
                log_pass "Data directory structure complete"
            else
                log_warn "Missing directories: ${missing_dirs[*]}" "Run: pm setup to create missing directories"
            fi
            ;;
        "not_initialized")
            log_fail "PersonalManager not initialized" "Run: pm setup"
            ;;
        error:*)
            log_fail "Configuration error: ${status#error:}"
            ;;
    esac
}

# Check launcher and scripts
check_launcher() {
    log_section "Launcher and Scripts"

    # Check main launcher
    check_start
    local launcher_path="$PROJECT_ROOT/bin/pm-local"
    if [[ -f "$launcher_path" ]]; then
        if [[ -x "$launcher_path" ]]; then
            log_pass "Launcher script executable: $launcher_path"
        else
            log_fail "Launcher script not executable" "Run: chmod +x $launcher_path"
        fi
    else
        log_fail "Launcher script missing: $launcher_path"
    fi

    # Test launcher functionality
    if [[ -x "$launcher_path" ]] && python3 -c "from pm.core.config import PMConfig" 2>/dev/null; then
        check_start
        if timeout 10s "$launcher_path" --launcher-debug &>/dev/null; then
            log_pass "Launcher functionality test passed"
        else
            log_fail "Launcher functionality test failed" "Check Python environment and dependencies"
        fi
    fi
}

# Check system resources
check_system_resources() {
    log_section "System Resources"

    # Check available memory
    check_start
    local mem_info=""
    case "$(uname -s)" in
        "Linux")
            if [[ -f /proc/meminfo ]]; then
                local mem_total mem_available
                mem_total=$(grep MemTotal /proc/meminfo | awk '{print $2}')
                mem_available=$(grep MemAvailable /proc/meminfo | awk '{print $2}' 2>/dev/null || echo "$mem_total")

                mem_total=$((mem_total / 1024))  # Convert to MB
                mem_available=$((mem_available / 1024))

                if [[ $mem_available -gt 500 ]]; then
                    log_pass "Memory: ${mem_available}MB available / ${mem_total}MB total"
                else
                    log_warn "Low memory: ${mem_available}MB available" "Close other applications to free memory"
                fi
            else
                log_skip "Memory information not available"
            fi
            ;;
        "Darwin")
            local mem_total
            mem_total=$(sysctl -n hw.memsize 2>/dev/null)
            if [[ -n "$mem_total" ]]; then
                mem_total=$((mem_total / 1024 / 1024))  # Convert to MB
                log_pass "Memory: ${mem_total}MB total (macOS)"
            else
                log_skip "Memory information not available"
            fi
            ;;
        *)
            log_skip "Memory check not supported on this platform"
            ;;
    esac

    # Check disk space
    check_start
    local data_dir="${HOME}/.personalmanager"
    if [[ -d "$data_dir" ]]; then
        local available_space
        available_space=$(df -m "$data_dir" 2>/dev/null | tail -1 | awk '{print $4}')
        if [[ -n "$available_space" && $available_space -gt 200 ]]; then
            log_pass "Disk space: ${available_space}MB available"
        else
            log_warn "Low disk space: ${available_space}MB available" "Free up disk space (need >200MB)"
        fi
    else
        # Check home directory space instead
        local available_space
        available_space=$(df -m "$HOME" 2>/dev/null | tail -1 | awk '{print $4}')
        if [[ -n "$available_space" && $available_space -gt 200 ]]; then
            log_pass "Disk space: ${available_space}MB available (home directory)"
        else
            log_warn "Low disk space: ${available_space}MB available" "Free up disk space"
        fi
    fi
}

# Check network connectivity
check_network() {
    if [[ "$QUICK_MODE" == "true" ]]; then
        log_skip "Network check skipped (quick mode)"
        return 0
    fi

    log_section "Network Connectivity"

    # Test basic connectivity
    check_start
    if timeout 5s ping -c 1 8.8.8.8 &>/dev/null; then
        log_pass "Basic network connectivity"
    else
        log_warn "No network connectivity" "Operating in offline mode"
        return 0
    fi

    # Test HTTPS connectivity
    check_start
    if timeout 10s curl -s https://www.google.com > /dev/null 2>&1; then
        log_pass "HTTPS connectivity"
    else
        log_warn "HTTPS connectivity issues" "Check firewall and proxy settings"
    fi

    # Test GitHub connectivity (for updates)
    check_start
    if timeout 10s curl -s https://github.com > /dev/null 2>&1; then
        log_pass "GitHub connectivity"
    else
        log_warn "GitHub not reachable" "Updates and git operations may fail"
    fi
}

# Check security and permissions
check_security() {
    log_section "Security and Permissions"

    # Check home directory permissions
    check_start
    if [[ -r "$HOME" && -w "$HOME" ]]; then
        log_pass "Home directory permissions"
    else
        log_fail "Home directory permission issues" "Check directory ownership and permissions"
    fi

    # Check PersonalManager data directory permissions
    check_start
    local data_dir="${HOME}/.personalmanager"
    if [[ -d "$data_dir" ]]; then
        if [[ -r "$data_dir" && -w "$data_dir" ]]; then
            log_pass "Data directory permissions"
        else
            log_fail "Data directory permission issues" "Run: chmod -R 755 $data_dir"
        fi

        # Check for sensitive files security
        check_start
        local tokens_dir="$data_dir/tokens"
        if [[ -d "$tokens_dir" ]]; then
            local perms
            perms=$(stat -c %a "$tokens_dir" 2>/dev/null || stat -f %A "$tokens_dir" 2>/dev/null)
            if [[ "$perms" == "700" || "$perms" == "755" ]]; then
                log_pass "Tokens directory security"
            else
                log_warn "Tokens directory permissions: $perms" "Run: chmod 700 $tokens_dir"
            fi
        fi
    else
        log_skip "Data directory not created yet"
    fi
}

# Attempt automatic fixes
attempt_fixes() {
    log_section "Auto-Fix Attempts"

    local fixes_applied=0

    # Fix launcher permissions
    local launcher_path="$PROJECT_ROOT/bin/pm-local"
    if [[ -f "$launcher_path" && ! -x "$launcher_path" ]]; then
        if chmod +x "$launcher_path" 2>/dev/null; then
            log_pass "Fixed launcher permissions"
            ((fixes_applied++))
        else
            log_fail "Could not fix launcher permissions"
        fi
    fi

    # Create missing data directories
    local data_dir="${HOME}/.personalmanager"
    if [[ -d "$data_dir" ]]; then
        local required_dirs=("tasks" "habits" "projects" "logs" "backups" "tokens")
        for dir in "${required_dirs[@]}"; do
            if [[ ! -d "$data_dir/$dir" ]]; then
                if mkdir -p "$data_dir/$dir" 2>/dev/null; then
                    log_pass "Created missing directory: $dir"
                    ((fixes_applied++))
                else
                    log_fail "Could not create directory: $dir"
                fi
            fi
        done
    fi

    if [[ $fixes_applied -gt 0 ]]; then
        log_info "Applied $fixes_applied automatic fixes"
    else
        log_info "No automatic fixes available"
    fi
}

# Generate summary report
generate_summary() {
    log_header "DIAGNOSTIC SUMMARY"

    local total_issues=$((CHECKS_FAILED + CHECKS_WARNED))
    local health_score=0

    if [[ $CHECKS_TOTAL -gt 0 ]]; then
        health_score=$(( (CHECKS_PASSED * 100) / CHECKS_TOTAL ))
    fi

    echo -e "${CYAN}System Health Score: ${NC}${health_score}%"
    echo
    echo -e "${CYAN}Check Results:${NC}"
    echo -e "  ${GREEN}Passed:  ${CHECKS_PASSED}${NC}"
    echo -e "  ${RED}Failed:  ${CHECKS_FAILED}${NC}"
    echo -e "  ${YELLOW}Warned:  ${CHECKS_WARNED}${NC}"
    echo -e "  ${PURPLE}Skipped: ${CHECKS_SKIPPED}${NC}"
    echo -e "  ${BLUE}Total:   ${CHECKS_TOTAL}${NC}"
    echo

    # Overall assessment
    if [[ $CHECKS_FAILED -eq 0 && $CHECKS_WARNED -eq 0 ]]; then
        echo -e "${GREEN}🎉 EXCELLENT: System is healthy and ready for use!${NC}"
    elif [[ $CHECKS_FAILED -eq 0 && $CHECKS_WARNED -lt 3 ]]; then
        echo -e "${YELLOW}✨ GOOD: System is mostly healthy with minor issues${NC}"
    elif [[ $CHECKS_FAILED -le 2 ]]; then
        echo -e "${YELLOW}⚠️  CAUTION: System has some issues that should be addressed${NC}"
    else
        echo -e "${RED}🚨 ATTENTION: System has critical issues that need fixing${NC}"
    fi

    echo
    echo -e "${CYAN}Next Steps:${NC}"
    if [[ $CHECKS_FAILED -gt 0 ]]; then
        echo -e "  • Address failed checks above"
        echo -e "  • Run: $0 --fix  (to attempt automatic repairs)"
    fi
    if [[ $CHECKS_WARNED -gt 0 ]]; then
        echo -e "  • Review warnings for optimization opportunities"
    fi
    echo -e "  • Run: pm setup  (if PersonalManager is not initialized)"
    echo -e "  • Run: pm doctor  (for comprehensive diagnostics)"
}

# Export report to markdown
export_report() {
    local output_file="$1"

    cat > "$output_file" << EOF
# PersonalManager System Diagnostic Report

**Generated**: $(date)
**System**: $(uname -s) $(uname -r) ($(uname -m))
**User**: $(whoami)
**Script**: $0

## Executive Summary

- **Health Score**: ${health_score:-0}%
- **Checks Passed**: $CHECKS_PASSED
- **Checks Failed**: $CHECKS_FAILED
- **Warnings**: $CHECKS_WARNED
- **Skipped**: $CHECKS_SKIPPED
- **Total Checks**: $CHECKS_TOTAL

## Detailed Results

EOF

    if [[ -n "$CHECKS_LOG" && -f "$CHECKS_LOG" ]]; then
        echo "### Check Log" >> "$output_file"
        echo '```' >> "$output_file"
        cat "$CHECKS_LOG" >> "$output_file"
        echo '```' >> "$output_file"
    fi

    cat >> "$output_file" << EOF

## System Information

- **OS**: $(uname -s) $(uname -r)
- **Architecture**: $(uname -m)
- **Python**: $(python3 --version 2>/dev/null || echo "Not found")
- **Shell**: ${SHELL:-Unknown}
- **Home Directory**: $HOME
- **Current Directory**: $(pwd)

## Recommendations

EOF

    if [[ $CHECKS_FAILED -gt 0 ]]; then
        echo "### Critical Issues" >> "$output_file"
        echo "- Address all failed checks before using PersonalManager" >> "$output_file"
        echo "- Run \`$0 --fix\` to attempt automatic repairs" >> "$output_file"
        echo >> "$output_file"
    fi

    if [[ $CHECKS_WARNED -gt 0 ]]; then
        echo "### Warnings" >> "$output_file"
        echo "- Review warnings for system optimization" >> "$output_file"
        echo "- Consider addressing warnings for best experience" >> "$output_file"
        echo >> "$output_file"
    fi

    echo "### Next Steps" >> "$output_file"
    echo "1. Run \`pm setup\` if PersonalManager is not initialized" >> "$output_file"
    echo "2. Run \`pm doctor\` for comprehensive diagnostics" >> "$output_file"
    echo "3. Test basic functionality with \`pm today\`" >> "$output_file"

    log_info "Report exported to: $output_file"
}

# Parse command line arguments
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --help|-h)
                usage
                exit 0
                ;;
            --version)
                show_version
                exit 0
                ;;
            --verbose|-v)
                VERBOSE=true
                shift
                ;;
            --quick|-q)
                QUICK_MODE=true
                shift
                ;;
            --fix)
                FIX_MODE=true
                shift
                ;;
            --export)
                EXPORT_FILE="$2"
                shift 2
                ;;
            --log)
                CHECKS_LOG="$2"
                shift 2
                ;;
            --silent)
                exec 1>/dev/null
                shift
                ;;
            *)
                echo "Error: Unknown option $1" >&2
                echo "Use --help for usage information" >&2
                exit 64
                ;;
        esac
    done
}

# Main execution flow
main() {
    parse_arguments "$@"

    # Set up logging
    if [[ -n "$CHECKS_LOG" ]]; then
        mkdir -p "$(dirname "$CHECKS_LOG")"
        echo "PersonalManager Diagnostic Log - $(date)" > "$CHECKS_LOG"
    fi

    # Show header
    log_header "PersonalManager Standalone Doctor"

    if [[ "$QUICK_MODE" == "true" ]]; then
        log_info "Running in quick mode - skipping network and performance tests"
    fi

    if [[ "$VERBOSE" == "true" ]]; then
        log_info "Verbose mode enabled - showing detailed information"
    fi

    echo

    # Run diagnostic checks
    check_python
    check_system_dependencies
    check_python_dependencies
    check_personalmanager_config
    check_launcher
    check_system_resources
    check_network
    check_security

    # Attempt fixes if requested
    if [[ "$FIX_MODE" == "true" ]]; then
        echo
        attempt_fixes
    fi

    # Generate summary
    echo
    generate_summary

    # Export report if requested
    if [[ -n "$EXPORT_FILE" ]]; then
        export_report "$EXPORT_FILE"
    fi

    # Determine exit code
    local exit_code=0
    if [[ $CHECKS_FAILED -gt 0 ]]; then
        exit_code=1
    elif [[ $CHECKS_WARNED -gt 0 ]]; then
        exit_code=2
    fi

    echo
    log_info "Diagnostic completed with exit code: $exit_code"

    exit $exit_code
}

# Handle interrupts gracefully
trap 'echo -e "\n${YELLOW}Diagnostic interrupted by user${NC}"; exit 130' INT TERM

# Execute main function with all arguments
main "$@"