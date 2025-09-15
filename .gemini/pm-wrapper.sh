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

set -euo pipefail  # Exit on error, undefined variables, and pipe failures

# Get the directory where this script is located
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Security: Command whitelist
readonly ALLOWED_COMMANDS=("today" "projects" "capture" "explain" "clarify" "tasks" "inbox" "next" "help" "--help" "--version" "ai")
# Allowlisted AI subcommands (must align with CLI: src/pm/cli/commands/ai.py)
readonly AI_SUBCOMMANDS=("route" "config" "status")

# Security: Parameter constraints
readonly MAX_ARG_LENGTH=1000
readonly SAFE_CHAR_PATTERN='^[a-zA-Z0-9._/-][a-zA-Z0-9._/ -]*$'

# Change to project root directory
cd "$PROJECT_ROOT"

# Color codes for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m' # No Color

# Security logging
readonly SECURITY_LOG="${PROJECT_ROOT}/.gemini/security.log"

# Function to print colored messages
print_info() {
    echo -e "${BLUE}[GEMINI-WRAPPER]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[GEMINI-WRAPPER]${NC} $1"
}

print_error() {
    echo -e "${RED}[GEMINI-WRAPPER]${NC} $1" >&2
    log_security_event "ERROR" "$1"
}

print_success() {
    echo -e "${GREEN}[GEMINI-WRAPPER]${NC} $1"
}

print_header() {
    echo -e "${CYAN}╔══════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║           PersonalManager via Gemini        ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════╝${NC}"
}

# Security: Log security events
log_security_event() {
    local level="$1"
    local message="$2"
    local timestamp="$(date '+%Y-%m-%d %H:%M:%S')"

    # Ensure log directory exists
    mkdir -p "$(dirname "$SECURITY_LOG")"

    # Log security events with proper formatting
    printf '[%s] %s: %s\n' "$timestamp" "$level" "$message" >> "$SECURITY_LOG" 2>/dev/null || true
}

# Security: Validate command against whitelist
validate_command() {
    local cmd="$1"
    local is_valid=false

    # Check against allowed commands
    for allowed in "${ALLOWED_COMMANDS[@]}"; do
        if [[ "$cmd" == "$allowed" ]]; then
            is_valid=true
            break
        fi
    done

    if [[ "$is_valid" != "true" ]]; then
        print_error "Security: Command '$cmd' not in whitelist"
        log_security_event "BLOCKED" "Invalid command attempted: $cmd"
        return 1
    fi

    return 0
}

# Security: Validate AI subcommand
validate_ai_subcommand() {
    local subcmd="$1"
    local is_valid=false

    # Check against allowed AI subcommands
    for allowed in "${AI_SUBCOMMANDS[@]}"; do
        if [[ "$subcmd" == "$allowed" ]]; then
            is_valid=true
            break
        fi
    done

    if [[ "$is_valid" != "true" ]]; then
        print_error "Security: AI subcommand '$subcmd' not allowed"
        log_security_event "BLOCKED" "Invalid AI subcommand attempted: $subcmd"
        return 1
    fi

    return 0
}

# Security: Sanitize and validate parameters
sanitize_parameters() {
    local -a sanitized_params=()

    for param in "$@"; do
        # Check parameter length
        if [[ ${#param} -gt $MAX_ARG_LENGTH ]]; then
            print_error "Security: Parameter too long (max $MAX_ARG_LENGTH chars)"
            log_security_event "BLOCKED" "Parameter length violation: ${#param} chars"
            return 1
        fi

        # Check for dangerous patterns
        if [[ "$param" =~ ^/ ]] || [[ "$param" =~ \.\. ]] || [[ "$param" =~ [\|\&\;\`\$\(\)\<\>] ]] || [[ "$param" =~ [*?\[\]] ]]; then
            print_error "Security: Dangerous pattern detected in parameter"
            log_security_event "BLOCKED" "Dangerous pattern in parameter: $param"
            return 1
        fi

        # Basic character validation (allow common safe characters)
        if [[ ! "$param" =~ $SAFE_CHAR_PATTERN ]]; then
            print_error "Security: Invalid characters in parameter"
            log_security_event "BLOCKED" "Invalid characters in parameter: $param"
            return 1
        fi

        sanitized_params+=("$param")
    done

    # Output sanitized parameters
    printf '%s\n' "${sanitized_params[@]}"
    return 0
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
    echo "  clarify           GTD clarification process"
    echo "  tasks             Task management operations"
    echo "  inbox             Inbox management"
    echo "  next              Next actions processing"
    echo "  help              Show PersonalManager help information"
    echo "  ai [subcmd]       AI-powered features (route, query, suggest, analyze, plan)"
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
    # Security: Log execution attempt
    log_security_event "INFO" "Wrapper execution started with args: $*"

    # Handle no arguments or help flags
    if [[ $# -eq 0 || "$1" == "-h" || "$1" == "--help" || "$1" == "help" ]]; then
        if [[ "$1" == "help" ]]; then
            # Security: Validate help command
            if ! validate_command "help"; then
                exit 1
            fi
            check_pm_local
            execute_pm_command "help"
        else
            show_usage
        fi
        exit 0
    fi

    # Security: Validate first command
    if ! validate_command "$1"; then
        exit 1
    fi

    # Security: Special handling for AI commands
    if [[ "$1" == "ai" ]]; then
        if [[ $# -lt 2 ]]; then
            print_error "Security: AI command requires subcommand"
            log_security_event "BLOCKED" "AI command without subcommand"
            exit 1
        fi
        if ! validate_ai_subcommand "$2"; then
            exit 1
        fi
    fi

    # Security: Sanitize all parameters
    local -a sanitized_args
    local sanitized_output
    if ! sanitized_output="$(sanitize_parameters "$@")"; then
        exit 1
    fi

    # Convert output to array (compatible with older bash)
    IFS=$'\n' read -ra sanitized_args <<< "$sanitized_output"

    # Print header for all commands
    print_header
    echo

    # Check if pm-local exists and is executable
    check_pm_local
    
    # Security: Use sanitized arguments for command routing
    case "${sanitized_args[0]}" in
        "today")
            execute_pm_command "today"
            ;;
        "projects")
            # Pass remaining sanitized arguments
            if [[ ${#sanitized_args[@]} -gt 1 ]]; then
                execute_pm_command "projects" "${sanitized_args[@]:1}"
            else
                execute_pm_command "projects"
            fi
            ;;
        "capture")
            if [[ ${#sanitized_args[@]} -eq 1 ]]; then
                print_warn "No capture text provided. Starting interactive capture mode..."
                execute_pm_command "capture"
            else
                execute_pm_command "capture" "${sanitized_args[@]:1}"
            fi
            ;;
        "explain")
            execute_pm_command "explain"
            ;;
        "clarify")
            execute_pm_command "clarify"
            ;;
        "tasks")
            if [[ ${#sanitized_args[@]} -gt 1 ]]; then
                execute_pm_command "tasks" "${sanitized_args[@]:1}"
            else
                execute_pm_command "tasks"
            fi
            ;;
        "inbox")
            if [[ ${#sanitized_args[@]} -gt 1 ]]; then
                execute_pm_command "inbox" "${sanitized_args[@]:1}"
            else
                execute_pm_command "inbox"
            fi
            ;;
        "next")
            if [[ ${#sanitized_args[@]} -gt 1 ]]; then
                execute_pm_command "next" "${sanitized_args[@]:1}"
            else
                execute_pm_command "next"
            fi
            ;;
        "help"|"--help")
            execute_pm_command "help"
            ;;
        "--version")
            execute_pm_command "--version"
            ;;
        "ai")
            # AI command with validated subcommand
            if [[ ${#sanitized_args[@]} -gt 2 ]]; then
                execute_pm_command "ai" "${sanitized_args[1]}" "${sanitized_args[@]:2}"
            else
                execute_pm_command "ai" "${sanitized_args[1]}"
            fi
            ;;
        *)
            # Security: No fallback - all commands must be explicitly whitelisted
            print_error "Security: Command '${sanitized_args[0]}' not allowed"
            log_security_event "BLOCKED" "Attempted execution of non-whitelisted command: ${sanitized_args[0]}"
            exit 1
            ;;
    esac

    # Security: Log successful execution
    log_security_event "INFO" "Command executed successfully: ${sanitized_args[*]}"
}

# Error handling
trap 'print_error "Script interrupted"; exit 1' INT TERM

# Execute main function with all arguments
main "$@"
