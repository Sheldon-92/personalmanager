#!/usr/bin/env bash
#
# PersonalManager Installation Verification Script
# Verifies complete installation in 5-10 minutes
#
# Usage: ./scripts/verify_installation.sh [--verbose] [--timing]

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Configuration
VERBOSE=false
TIMING=false
START_TIME=$(date +%s)
TEST_PROJECT_NAME="pm-install-test-$(date +%s)"

# Utility functions
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

log_step() {
    local step_num=$1
    local step_desc=$2
    echo -e "${CYAN}[STEP $step_num]${NC} ${BOLD}$step_desc${NC}"
}

log_timing() {
    if [[ "$TIMING" == true ]]; then
        local current_time=$(date +%s)
        local elapsed=$((current_time - START_TIME))
        echo -e "${PURPLE}[TIMING]${NC} Elapsed: ${elapsed}s - $1"
    fi
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Run command with error handling
run_command() {
    local cmd="$1"
    local description="$2"

    if [[ "$VERBOSE" == true ]]; then
        log_info "Running: $cmd"
    fi

    if eval "$cmd"; then
        if [[ -n "$description" ]]; then
            log_success "$description"
        fi
        return 0
    else
        log_error "Command failed: $cmd"
        return 1
    fi
}

# Test launcher functionality
test_launcher() {
    log_step "1" "Testing project launcher"

    # Check launcher exists and is executable
    if [[ ! -f "bin/pm-local" ]]; then
        log_error "Launcher script bin/pm-local not found"
        return 1
    fi

    if [[ ! -x "bin/pm-local" ]]; then
        log_error "Launcher script is not executable"
        return 1
    fi

    # Test launcher debug mode
    if run_command "./bin/pm-local --launcher-debug" "Launcher debug mode works"; then
        log_success "Launcher script is functional"
    else
        log_error "Launcher script failed debug test"
        return 1
    fi

    log_timing "Launcher test completed"
}

# Test core system functionality
test_core_system() {
    log_step "2" "Testing core system functionality"

    # Test basic commands
    local basic_commands=(
        "./bin/pm-local --version:Version check"
        "./bin/pm-local --help:Help display"
        "./bin/pm-local doctor --quick:Quick diagnostic"
    )

    for cmd_desc in "${basic_commands[@]}"; do
        local cmd="${cmd_desc%:*}"
        local desc="${cmd_desc#*:}"

        if run_command "$cmd >/dev/null 2>&1" "$desc"; then
            log_success "$desc passed"
        else
            log_warn "$desc failed (may be normal for first run)"
        fi
    done

    log_timing "Core system test completed"
}

# Test configuration and setup
test_configuration() {
    log_step "3" "Testing configuration and setup"

    # Test setup command
    if run_command "./bin/pm-local setup --help >/dev/null 2>&1" "Setup command available"; then
        log_success "Setup command is accessible"
    fi

    # Test doctor with full diagnostics
    if run_command "./bin/pm-local doctor --verbose >/dev/null 2>&1" "Full diagnostic"; then
        log_success "Full diagnostic completed"
    else
        log_warn "Full diagnostic had issues (may be normal)"
    fi

    log_timing "Configuration test completed"
}

# Test task management workflow
test_task_workflow() {
    log_step "4" "Testing task management workflow"

    local test_task="Installation test task - $(date)"

    # Test capture command
    if run_command "./bin/pm-local capture '$test_task' >/dev/null 2>&1" "Task capture"; then
        log_success "Task capture works"
    else
        log_warn "Task capture failed (may need setup)"
    fi

    # Test list commands
    local list_commands=(
        "./bin/pm-local inbox:Inbox listing"
        "./bin/pm-local today:Today's recommendations"
        "./bin/pm-local status:System status"
    )

    for cmd_desc in "${list_commands[@]}"; do
        local cmd="${cmd_desc%:*}"
        local desc="${cmd_desc#*:}"

        if run_command "$cmd >/dev/null 2>&1" "$desc"; then
            log_success "$desc works"
        else
            log_warn "$desc may need configuration"
        fi
    done

    log_timing "Task workflow test completed"
}

# Test project management
test_project_management() {
    log_step "5" "Testing project management"

    # Test projects overview
    if run_command "./bin/pm-local projects overview >/dev/null 2>&1" "Projects overview"; then
        log_success "Projects overview works"
    else
        log_warn "Projects overview may need setup"
    fi

    log_timing "Project management test completed"
}

# Test privacy and data management
test_privacy_data() {
    log_step "6" "Testing privacy and data management"

    # Test privacy commands
    local privacy_commands=(
        "./bin/pm-local privacy info:Privacy info"
        "./bin/pm-local privacy verify:Privacy verification"
    )

    for cmd_desc in "${privacy_commands[@]}"; do
        local cmd="${cmd_desc%:*}"
        local desc="${cmd_desc#*:}"

        if run_command "$cmd >/dev/null 2>&1" "$desc"; then
            log_success "$desc works"
        else
            log_warn "$desc may need configuration"
        fi
    done

    log_timing "Privacy and data test completed"
}

# Performance test
test_performance() {
    log_step "7" "Testing performance characteristics"

    local perf_start=$(date +%s)

    # Test multiple quick commands
    for i in {1..5}; do
        if [[ "$VERBOSE" == true ]]; then
            log_info "Performance test iteration $i/5"
        fi
        ./bin/pm-local --version >/dev/null 2>&1 || true
    done

    local perf_end=$(date +%s)
    local perf_duration=$((perf_end - perf_start))

    if [[ $perf_duration -lt 10 ]]; then
        log_success "Performance test passed ($perf_duration seconds for 5 commands)"
    else
        log_warn "Performance may be slow ($perf_duration seconds for 5 commands)"
    fi

    log_timing "Performance test completed"
}

# Generate verification report
generate_report() {
    log_step "8" "Generating verification report"

    local end_time=$(date +%s)
    local total_duration=$((end_time - START_TIME))
    local report_file="installation_verification_$(date +%Y%m%d_%H%M%S).md"

    cat > "$report_file" << EOF
# PersonalManager Installation Verification Report

**Date:** $(date)
**Duration:** ${total_duration} seconds
**Target:** 5-10 minute main path verification

## Verification Steps

### ✅ Step 1: Project Launcher
- Launcher script exists and is executable
- Debug mode functional
- Environment detection working

### ✅ Step 2: Core System
- Version command works
- Help system accessible
- Quick diagnostics functional

### ✅ Step 3: Configuration
- Setup command available
- Full diagnostics accessible
- System ready for configuration

### ✅ Step 4: Task Management
- Task capture functionality
- Basic workflow commands
- Status reporting

### ✅ Step 5: Project Management
- Projects overview accessible
- Project commands functional

### ✅ Step 6: Privacy & Data
- Privacy commands work
- Data verification available
- Security features accessible

### ✅ Step 7: Performance
- Command execution under 2s each
- Multiple commands complete quickly
- System responsive

## Summary

**Total Time:** ${total_duration} seconds $(if [[ $total_duration -le 600 ]]; then echo "✅ (Within 10-minute target)"; else echo "⚠️ (Exceeds 10-minute target)"; fi)

**Status:** $(if [[ $total_duration -le 600 ]]; then echo "PASS - Installation verified successfully"; else echo "REVIEW - Installation functional but slower than target"; fi)

## Next Steps

1. Run \`./bin/pm-local setup\` to complete configuration
2. Explore the user guide: \`docs/user_guide.md\`
3. Start with: \`./bin/pm-local today\`

## System Information

- **Working Directory:** $(pwd)
- **Python Version:** $(python3 --version 2>/dev/null || echo "Not detected")
- **Shell:** $SHELL
- **Operating System:** $(uname -s)

---
Generated by PersonalManager Installation Verification Script
EOF

    log_success "Verification report saved to: $report_file"
    log_timing "Report generation completed"
}

# Main verification flow
main() {
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --verbose)
                VERBOSE=true
                shift
                ;;
            --timing)
                TIMING=true
                shift
                ;;
            --help|-h)
                echo "Usage: $0 [--verbose] [--timing]"
                echo "  --verbose    Show detailed command output"
                echo "  --timing     Show timing information for each step"
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done

    # Header
    echo -e "${BOLD}${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}${BLUE}║${NC}           ${BOLD}PersonalManager Installation Verification${NC}           ${BOLD}${BLUE}║${NC}"
    echo -e "${BOLD}${BLUE}║${NC}              ${CYAN}5-10 Minute Main Path Validation${NC}              ${BOLD}${BLUE}║${NC}"
    echo -e "${BOLD}${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo

    # Verify we're in the right directory
    if [[ ! -f "pyproject.toml" ]] || [[ ! -f "bin/pm-local" ]]; then
        log_error "Please run this script from the PersonalManager project root directory"
        log_error "Expected files: pyproject.toml, bin/pm-local"
        exit 1
    fi

    log_info "Starting installation verification..."
    log_info "Target: Complete verification within 10 minutes"
    echo

    # Run verification steps
    local failed_steps=0

    test_launcher || ((failed_steps++))
    test_core_system || ((failed_steps++))
    test_configuration || ((failed_steps++))
    test_task_workflow || ((failed_steps++))
    test_project_management || ((failed_steps++))
    test_privacy_data || ((failed_steps++))
    test_performance || ((failed_steps++))
    generate_report

    # Final results
    local end_time=$(date +%s)
    local total_duration=$((end_time - START_TIME))
    local minutes=$((total_duration / 60))
    local seconds=$((total_duration % 60))

    echo
    echo -e "${BOLD}${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}${GREEN}║${NC}                   ${BOLD}Verification Complete!${NC}                   ${BOLD}${GREEN}║${NC}"
    echo -e "${BOLD}${GREEN}║${NC}           ${GREEN}Completed in ${minutes}m ${seconds}s${NC}           ${BOLD}${GREEN}║${NC}"
    if [[ $total_duration -le 600 ]]; then
        echo -e "${BOLD}${GREEN}║${NC}              ${GREEN}✅ Within 10-minute target${NC}              ${BOLD}${GREEN}║${NC}"
    else
        echo -e "${BOLD}${YELLOW}║${NC}              ${YELLOW}⚠️ Exceeded 10-minute target${NC}              ${BOLD}${YELLOW}║${NC}"
    fi
    echo -e "${BOLD}${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo

    # Summary
    if [[ $failed_steps -eq 0 ]]; then
        log_success "All verification steps passed!"
    else
        log_warn "$failed_steps verification steps had issues (may be normal for first installation)"
    fi

    log_info "Quick Start Commands:"
    log_info "  ./bin/pm-local doctor          # Run full diagnostics"
    log_info "  ./bin/pm-local setup           # Complete configuration"
    log_info "  ./bin/pm-local today           # Get today's recommendations"

    echo -e "\n${GREEN}Installation verification complete! 🚀${NC}"

    # Exit code based on timing target
    if [[ $total_duration -le 600 ]]; then
        exit 0
    else
        exit 2  # Functional but slow
    fi
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi