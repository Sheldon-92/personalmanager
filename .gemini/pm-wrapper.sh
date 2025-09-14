#!/usr/bin/env bash
#
# PersonalManager Gemini CLI Wrapper Script
# Provides direct shell execution for PersonalManager commands when Gemini CLI lacks execution tools
#
# Usage: ./pm-wrapper.sh [command] [args...]
# Examples:
#   ./pm-wrapper.sh today
#   ./pm-wrapper.sh projects overview
#   ./pm-wrapper.sh capture "New task idea"
#

set -e  # Exit on error

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Change to project root directory
cd "$PROJECT_ROOT"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored messages
print_info() {
    echo -e "${BLUE}[GEMINI-WRAPPER]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[GEMINI-WRAPPER]${NC} $1"
}

print_error() {
    echo -e "${RED}[GEMINI-WRAPPER]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[GEMINI-WRAPPER]${NC} $1"
}

print_header() {
    echo -e "${CYAN}╔══════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║           PersonalManager via Gemini        ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════╝${NC}"
}

# Function to show usage help
show_usage() {
    print_header
    echo
    echo "Usage: $0 [command] [args...]"
    echo
    echo "Available Commands:"
    echo "  today              Get today's personalized task recommendations"
    echo "  projects [action]  Project management (overview, status, etc.)"
    echo "  capture [text]     Capture new tasks or ideas to inbox"
    echo "  explain           Explain recommendation logic and insights"
    echo "  help              Show PersonalManager help information"
    echo "  doctor            Run system diagnostics"
    echo "  habits            Habit tracking and management"
    echo "  review            Review and reflection tools"
    echo "  clarify           GTD clarification process"
    echo "  deepwork          Deep work session management"
    echo
    echo "Examples:"
    echo "  $0 today"
    echo "  $0 projects overview"
    echo "  $0 capture \"New project idea\""
    echo "  $0 explain"
    echo
    echo "Note: This wrapper provides direct shell execution for PersonalManager"
    echo "commands when called through Gemini CLI, bypassing tool execution limitations."
    echo
}

# Function to check if pm-local exists
check_pm_local() {
    if [ ! -f "$PROJECT_ROOT/bin/pm-local" ]; then
        print_error "PersonalManager launcher not found at $PROJECT_ROOT/bin/pm-local"
        print_error "Please ensure you're running this script from a valid PersonalManager project directory."
        exit 1
    fi
    
    if [ ! -x "$PROJECT_ROOT/bin/pm-local" ]; then
        print_error "PersonalManager launcher is not executable: $PROJECT_ROOT/bin/pm-local"
        print_error "Run: chmod +x $PROJECT_ROOT/bin/pm-local"
        exit 1
    fi
}

# Function to execute PersonalManager command with enhanced output
execute_pm_command() {
    local cmd_args=("$@")
    
    print_info "Executing: ./bin/pm-local ${cmd_args[*]}"
    print_info "Project Root: $PROJECT_ROOT"
    echo
    
    # Execute the command and capture both output and exit code
    if ./bin/pm-local "${cmd_args[@]}"; then
        echo
        print_success "Command completed successfully"
    else
        local exit_code=$?
        echo
        print_error "Command failed with exit code: $exit_code"
        exit $exit_code
    fi
}

# Main execution logic
main() {
    # Handle no arguments or help flags
    if [[ $# -eq 0 || "$1" == "-h" || "$1" == "--help" || "$1" == "help" ]]; then
        if [[ "$1" == "help" ]]; then
            # If user specifically asked for "help", also show PersonalManager help
            check_pm_local
            execute_pm_command "help"
        else
            show_usage
        fi
        exit 0
    fi
    
    # Print header for all commands
    print_header
    echo
    
    # Check if pm-local exists and is executable
    check_pm_local
    
    # Map some common Gemini CLI patterns to PersonalManager commands
    case "$1" in
        "pm-today"|"today")
            execute_pm_command "today"
            ;;
        "pm-projects"|"projects")
            shift  # Remove first argument
            execute_pm_command "projects" "$@"
            ;;
        "pm-capture"|"capture")
            shift  # Remove first argument
            if [[ $# -eq 0 ]]; then
                print_warn "No capture text provided. Starting interactive capture mode..."
                execute_pm_command "capture"
            else
                execute_pm_command "capture" "$@"
            fi
            ;;
        "pm-explain"|"explain")
            execute_pm_command "explain"
            ;;
        "pm-help"|"help")
            execute_pm_command "help"
            ;;
        "pm-doctor"|"doctor")
            shift
            if [[ $# -eq 0 ]]; then
                execute_pm_command "doctor" "main"
            else
                execute_pm_command "doctor" "$@"
            fi
            ;;
        "pm-habits"|"habits")
            shift
            execute_pm_command "habits" "$@"
            ;;
        "pm-review"|"review")
            shift
            execute_pm_command "review" "$@"
            ;;
        "pm-clarify"|"clarify")
            execute_pm_command "clarify"
            ;;
        "pm-deepwork"|"deepwork")
            shift
            execute_pm_command "deepwork" "$@"
            ;;
        *)
            # Pass through any unrecognized commands directly to pm-local
            print_info "Passing through unrecognized command: $*"
            execute_pm_command "$@"
            ;;
    esac
}

# Error handling
trap 'print_error "Script interrupted"; exit 1' INT TERM

# Execute main function with all arguments
main "$@"