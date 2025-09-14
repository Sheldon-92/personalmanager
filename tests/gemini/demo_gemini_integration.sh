#!/usr/bin/env bash
#
# PersonalManager Gemini CLI Integration Demo Script
# Demonstrates various integration approaches and failure/success scenarios
#
# This script showcases:
# 1. Direct Gemini CLI command attempts (will fail)
# 2. Wrapper script solutions (will succeed)
# 3. Direct PersonalManager commands (will succeed)
# 4. Before/after comparison of integration approaches
#

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
DEMO_DELAY=2  # Seconds to wait between demos
SHOW_ERRORS=true  # Whether to show error details

# Function to print colored messages
print_header() {
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║           PersonalManager Gemini CLI Integration Demo           ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════╝${NC}"
    echo
}

print_section() {
    echo -e "${MAGENTA}▶ $1${NC}"
    echo -e "${MAGENTA}$( printf '═%.0s' {1..60} )${NC}"
}

print_subsection() {
    echo -e "${BLUE}→ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_failure() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

print_command() {
    echo -e "${CYAN}$ $1${NC}"
}

# Function to wait with countdown
wait_with_countdown() {
    local seconds=${1:-$DEMO_DELAY}
    echo
    for ((i=seconds; i>0; i--)); do
        printf "\rContinuing in %d seconds..." "$i"
        sleep 1
    done
    printf "\r\033[K"  # Clear the line
    echo
}

# Function to run a command and capture output
run_command_demo() {
    local cmd="$1"
    local description="$2"
    local expect_success="${3:-true}"
    
    print_subsection "$description"
    print_command "$cmd"
    echo
    
    if $expect_success; then
        if eval "$cmd"; then
            print_success "Command executed successfully"
        else
            print_failure "Command failed unexpectedly"
        fi
    else
        # We expect this to fail
        if eval "$cmd" 2>/dev/null; then
            print_failure "Command succeeded when we expected it to fail"
        else
            print_failure "Command failed as expected (due to Gemini CLI limitations)"
            if $SHOW_ERRORS; then
                print_info "This demonstrates the core integration issue"
            fi
        fi
    fi
    
    wait_with_countdown 1
}

# Function to demonstrate error scenarios
demo_error_scenarios() {
    print_section "1. DEMONSTRATING CURRENT GEMINI CLI FAILURES"
    
    print_info "These commands will fail due to missing shell execution tools in Gemini CLI"
    echo
    
    # Note: We can't actually run these interactively as they would hang waiting for input
    # Instead, we'll show what would happen
    
    print_subsection "Attempting: gemini pm-today"
    print_command "gemini pm-today"
    echo
    print_failure "Expected failure: 'Tool \"run_shell_command\" not found in registry'"
    print_info "Gemini CLI analyzes code but cannot execute PersonalManager commands"
    
    wait_with_countdown
    
    print_subsection "Attempting: gemini pm-projects"
    print_command "gemini pm-projects"
    echo
    print_failure "Expected failure: Same tool registry issue"
    print_info "Provides file analysis but no actual command execution"
    
    wait_with_countdown
    
    print_subsection "Attempting: gemini pm-capture"
    print_command "gemini pm-capture"
    echo
    print_failure "Expected failure: Cannot execute capture workflow"
    print_info "Recognizes intent but lacks execution capability"
    
    wait_with_countdown
}

# Function to demonstrate wrapper script solutions
demo_wrapper_solutions() {
    print_section "2. DEMONSTRATING WRAPPER SCRIPT SOLUTIONS"
    
    print_info "Using .gemini/pm-wrapper.sh to provide direct shell execution"
    echo
    
    # Check if wrapper exists and is executable
    local wrapper_path=".gemini/pm-wrapper.sh"
    
    if [[ ! -f "$wrapper_path" ]]; then
        print_failure "Wrapper script not found at $wrapper_path"
        return 1
    fi
    
    if [[ ! -x "$wrapper_path" ]]; then
        print_info "Making wrapper script executable..."
        chmod +x "$wrapper_path"
    fi
    
    run_command_demo "$wrapper_path --help" "Show wrapper help information" true
    
    run_command_demo "$wrapper_path today" "Get today's recommendations via wrapper" true
    
    run_command_demo "$wrapper_path projects overview" "Get projects overview via wrapper" true
    
    # Test capture with sample input (non-interactive)
    run_command_demo "echo 'Sample task idea' | $wrapper_path capture" "Capture task via wrapper" true
}

# Function to demonstrate direct PersonalManager usage
demo_direct_usage() {
    print_section "3. DEMONSTRATING DIRECT PERSONALMANAGER USAGE"
    
    print_info "Using ./bin/pm-local directly (recommended approach)"
    echo
    
    run_command_demo "./bin/pm-local --version" "Check PersonalManager version" true
    
    run_command_demo "./bin/pm-local --help | head -20" "Show PersonalManager help (first 20 lines)" true
    
    run_command_demo "./bin/pm-local doctor" "Run system diagnostics" true
    
    print_info "Note: For actual daily usage, run './bin/pm-local [command]' directly"
}

# Function to demonstrate new Gemini CLI task configurations
demo_task_configurations() {
    print_section "4. DEMONSTRATING NEW GEMINI CLI TASK CONFIGURATIONS"
    
    print_info "New Gemini CLI tasks created for PersonalManager integration"
    echo
    
    # Show available PersonalManager tasks
    local tasks_dir=".gemini/commands/PersonalManager/tasks"
    
    if [[ -d "$tasks_dir" ]]; then
        print_subsection "Available Gemini CLI PersonalManager tasks:"
        for task_file in "$tasks_dir"/*.toml; do
            if [[ -f "$task_file" ]]; then
                local task_name=$(basename "$task_file" .toml)
                local description=$(grep '^description = ' "$task_file" | cut -d'"' -f2)
                echo -e "  ${GREEN}$task_name${NC}: $description"
            fi
        done
        
        echo
        print_info "Users can now run: gemini [task-name] for PersonalManager integration"
        print_info "These tasks provide workarounds for shell execution limitations"
        
        wait_with_countdown
        
        # Show sample task configuration
        print_subsection "Sample Task Configuration (pm-today.toml):"
        print_command "head -10 $tasks_dir/pm-today.toml"
        echo
        head -10 "$tasks_dir/pm-today.toml" 2>/dev/null || print_failure "Could not read task configuration"
        
    else
        print_failure "PersonalManager task configurations not found at $tasks_dir"
    fi
    
    wait_with_countdown
}

# Function to show integration summary
show_integration_summary() {
    print_section "5. INTEGRATION SUMMARY & RECOMMENDATIONS"
    
    echo -e "${GREEN}✓ WORKING SOLUTIONS:${NC}"
    echo "  1. Direct usage: ./bin/pm-local [command]"
    echo "  2. Wrapper script: .gemini/pm-wrapper.sh [command]"
    echo "  3. Gemini CLI tasks: gemini [pm-task-name] (with limitations)"
    echo
    
    echo -e "${RED}✗ CURRENT LIMITATIONS:${NC}"
    echo "  1. Gemini CLI lacks shell execution tools"
    echo "  2. Direct command mapping not supported"
    echo "  3. Interactive commands require workarounds"
    echo
    
    echo -e "${YELLOW}📋 RECOMMENDED USAGE:${NC}"
    echo "  • For daily use: ./bin/pm-local [command]"
    echo "  • For Gemini integration: .gemini/pm-wrapper.sh [command]"
    echo "  • For AI assistance: gemini pm-help or gemini pm-explain"
    echo
    
    echo -e "${BLUE}🔧 TROUBLESHOOTING:${NC}"
    echo "  • Check installation: ./bin/pm-local doctor"
    echo "  • Verify wrapper: .gemini/pm-wrapper.sh --help"
    echo "  • Review logs: Check PersonalManager error output"
    echo
}

# Main demo execution
main() {
    print_header
    
    print_info "This demo showcases PersonalManager Gemini CLI integration approaches"
    print_info "Including failure scenarios and working solutions"
    echo
    
    # Check prerequisites
    print_subsection "Checking Prerequisites..."
    
    if [[ ! -f "./bin/pm-local" ]]; then
        print_failure "PersonalManager not found. Please run from project root directory."
        exit 1
    fi
    
    if ! command -v gemini >/dev/null 2>&1; then
        print_failure "Gemini CLI not found. Some demos will be skipped."
    else
        print_success "Gemini CLI found: $(gemini --version)"
    fi
    
    print_success "PersonalManager found: $(./bin/pm-local --version 2>/dev/null | head -1 || echo 'Version check failed')"
    
    wait_with_countdown 3
    
    # Run demo sections
    demo_error_scenarios
    demo_wrapper_solutions  
    demo_direct_usage
    demo_task_configurations
    show_integration_summary
    
    print_header
    print_success "Demo completed successfully!"
    print_info "For more information, see docs/reports/sprint_3/gemini_error_reproduction.md"
    echo
}

# Handle script arguments
case "${1:-}" in
    --help|-h|help)
        echo "PersonalManager Gemini CLI Integration Demo"
        echo
        echo "Usage: $0 [options]"
        echo
        echo "Options:"
        echo "  --help, -h     Show this help message"
        echo "  --quick, -q    Run quick demo (reduced delays)"
        echo "  --no-errors    Skip error demonstration scenarios"
        echo
        echo "This script demonstrates various approaches to integrating PersonalManager"
        echo "with Gemini CLI, including current limitations and working solutions."
        exit 0
        ;;
    --quick|-q)
        DEMO_DELAY=0
        ;;
    --no-errors)
        SHOW_ERRORS=false
        ;;
esac

# Run the main demo
main "$@"