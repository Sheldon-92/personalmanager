#!/bin/bash

# Enhanced Health Probe Deployment Script for OBS-O3
# Deploys multiple health probes with 30s intervals
# Monitors all critical endpoints with 24hr+ retention

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CONFIG_DIR="$PROJECT_ROOT/configs/observability"
LOGS_DIR="$PROJECT_ROOT/logs"
PID_DIR="$PROJECT_ROOT/logs/pids"

# Default values
PROBE_INTERVAL="${PROBE_INTERVAL:-30}"
LOG_RETENTION_HOURS="${LOG_RETENTION_HOURS:-48}"
CONFIG_FILE="${CONFIG_FILE:-$CONFIG_DIR/health_probe_config.yaml}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log_error() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] ${RED}ERROR${NC}: $1" >&2
}

log_success() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] ${GREEN}SUCCESS${NC}: $1"
}

log_warning() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] ${YELLOW}WARNING${NC}: $1"
}

# Function to check dependencies
check_dependencies() {
    local deps=("jq" "bc" "curl" "yq")
    local missing=()

    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            missing+=("$dep")
        fi
    done

    if [ ${#missing[@]} -ne 0 ]; then
        log_error "Missing dependencies: ${missing[*]}"
        log "Please install missing dependencies and try again"
        exit 1
    fi
}

# Function to create directories
setup_directories() {
    mkdir -p "$CONFIG_DIR" "$LOGS_DIR" "$PID_DIR"
    log "Created necessary directories"
}

# Function to parse YAML config
parse_config() {
    if [ ! -f "$CONFIG_FILE" ]; then
        log_error "Configuration file not found: $CONFIG_FILE"
        exit 1
    fi

    # Extract endpoints from config
    yq eval '.endpoints[].name' "$CONFIG_FILE" 2>/dev/null || {
        log_error "Failed to parse configuration file"
        exit 1
    }
}

# Function to start health probe for a specific endpoint
start_probe() {
    local endpoint_name="$1"
    local endpoint_url="$2"
    local health_path="$3"
    local timeout="$4"

    local output_file="$LOGS_DIR/health_probe_${endpoint_name}.jsonl"
    local metrics_file="$LOGS_DIR/health_metrics_${endpoint_name}.jsonl"
    local pid_file="$PID_DIR/health_probe_${endpoint_name}.pid"
    local log_file="$LOGS_DIR/health_probe_${endpoint_name}.log"

    # Check if probe is already running
    if [ -f "$pid_file" ] && kill -0 "$(cat "$pid_file")" 2>/dev/null; then
        log_warning "Probe for $endpoint_name is already running (PID: $(cat "$pid_file"))"
        return 0
    fi

    # Start the probe in background
    API_ENDPOINT="$endpoint_url" \
    HEALTH_PATH="$health_path" \
    PROBE_INTERVAL="$PROBE_INTERVAL" \
    OUTPUT_FILE="$output_file" \
    METRICS_FILE="$metrics_file" \
    nohup "$SCRIPT_DIR/health_probe.sh" > "$log_file" 2>&1 &

    local probe_pid=$!
    echo "$probe_pid" > "$pid_file"

    # Wait a moment to ensure probe started successfully
    sleep 2
    if kill -0 "$probe_pid" 2>/dev/null; then
        log_success "Started health probe for $endpoint_name (PID: $probe_pid)"
        log "  Endpoint: $endpoint_url$health_path"
        log "  Output: $output_file"
        log "  Logs: $log_file"
    else
        log_error "Failed to start health probe for $endpoint_name"
        rm -f "$pid_file"
        return 1
    fi
}

# Function to stop health probe for a specific endpoint
stop_probe() {
    local endpoint_name="$1"
    local pid_file="$PID_DIR/health_probe_${endpoint_name}.pid"

    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid"
            sleep 2
            if kill -0 "$pid" 2>/dev/null; then
                kill -9 "$pid" 2>/dev/null || true
            fi
            log_success "Stopped health probe for $endpoint_name (PID: $pid)"
        else
            log_warning "Probe for $endpoint_name was not running"
        fi
        rm -f "$pid_file"
    else
        log_warning "No PID file found for $endpoint_name"
    fi
}

# Function to stop all probes
stop_all_probes() {
    log "Stopping all health probes..."

    for pid_file in "$PID_DIR"/health_probe_*.pid; do
        if [ -f "$pid_file" ]; then
            local endpoint_name=$(basename "$pid_file" .pid | sed 's/health_probe_//')
            stop_probe "$endpoint_name"
        fi
    done
}

# Function to start all probes from config
start_all_probes() {
    log "Starting health probes from configuration..."

    local endpoints
    endpoints=$(yq eval '.endpoints[] | [.name, .url, .health_path, .timeout] | @tsv' "$CONFIG_FILE")

    while IFS=$'\t' read -r name url health_path timeout; do
        if [ -n "$name" ] && [ -n "$url" ]; then
            start_probe "$name" "$url" "${health_path:-/health}" "${timeout:-10}"
        fi
    done <<< "$endpoints"
}

# Function to show status of all probes
show_status() {
    log "Health Probe Status:"
    echo

    local running=0
    local total=0

    for pid_file in "$PID_DIR"/health_probe_*.pid; do
        if [ -f "$pid_file" ]; then
            local endpoint_name=$(basename "$pid_file" .pid | sed 's/health_probe_//')
            local pid=$(cat "$pid_file")
            total=$((total + 1))

            if kill -0 "$pid" 2>/dev/null; then
                echo -e "  ${GREEN}●${NC} $endpoint_name (PID: $pid) - RUNNING"
                running=$((running + 1))

                # Show recent statistics if available
                local metrics_file="$LOGS_DIR/health_metrics_${endpoint_name}.jsonl"
                if [ -f "$metrics_file" ] && [ -s "$metrics_file" ]; then
                    local latest_metrics=$(tail -n 1 "$metrics_file")
                    local uptime=$(echo "$latest_metrics" | jq -r '.uptime_percentage // "N/A"')
                    local total_probes=$(echo "$latest_metrics" | jq -r '.total_probes // "N/A"')
                    echo "    Uptime: ${uptime}% (${total_probes} probes)"
                fi
            else
                echo -e "  ${RED}●${NC} $endpoint_name (PID: $pid) - STOPPED"
                rm -f "$pid_file"
            fi
        fi
    done

    echo
    log "Summary: $running/$total probes running"
}

# Function to clean old logs
cleanup_logs() {
    log "Cleaning up logs older than $LOG_RETENTION_HOURS hours..."

    find "$LOGS_DIR" -name "health_probe_*.jsonl" -type f -mmin +$((LOG_RETENTION_HOURS * 60)) -delete
    find "$LOGS_DIR" -name "health_probe_*.log" -type f -mmin +$((LOG_RETENTION_HOURS * 60)) -delete
    find "$LOGS_DIR" -name "health_metrics_*.jsonl" -type f -mmin +$((LOG_RETENTION_HOURS * 60)) -delete

    log_success "Log cleanup completed"
}

# Function to generate consolidated report
generate_report() {
    local output_file="$LOGS_DIR/health_report_$(date +%Y%m%d_%H%M%S).json"
    log "Generating consolidated health report: $output_file"

    local report_data='{"timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ")'", "endpoints": []}'

    for metrics_file in "$LOGS_DIR"/health_metrics_*.jsonl; do
        if [ -f "$metrics_file" ] && [ -s "$metrics_file" ]; then
            local endpoint_name=$(basename "$metrics_file" .jsonl | sed 's/health_metrics_//')
            local latest_metrics=$(tail -n 1 "$metrics_file")

            # Add endpoint data to report
            report_data=$(echo "$report_data" | jq --arg name "$endpoint_name" --argjson metrics "$latest_metrics" '
                .endpoints += [{
                    "name": $name,
                    "uptime_percentage": $metrics.uptime_percentage,
                    "total_probes": $metrics.total_probes,
                    "successful_probes": $metrics.successful_probes,
                    "failed_probes": $metrics.failed_probes,
                    "runtime_seconds": $metrics.runtime_seconds
                }]
            ')
        fi
    done

    echo "$report_data" | jq '.' > "$output_file"
    log_success "Health report generated: $output_file"
}

# Function to show usage
show_usage() {
    cat << EOF
Usage: $0 [COMMAND] [OPTIONS]

Commands:
    start [endpoint]    Start health probes (all or specific endpoint)
    stop [endpoint]     Stop health probes (all or specific endpoint)
    restart [endpoint]  Restart health probes (all or specific endpoint)
    status              Show status of all probes
    cleanup             Clean old log files
    report              Generate consolidated health report
    help                Show this help message

Options:
    --config FILE       Use specific configuration file
    --interval SECONDS  Set probe interval (default: 30)
    --retention HOURS   Set log retention hours (default: 48)

Examples:
    $0 start                    # Start all probes from config
    $0 start api-server         # Start probe for api-server endpoint
    $0 stop                     # Stop all probes
    $0 status                   # Show status
    $0 cleanup                  # Clean old logs
    $0 report                   # Generate health report

Configuration file: $CONFIG_FILE
EOF
}

# Main function
main() {
    local command="${1:-help}"
    local endpoint="${2:-}"

    # Parse command line options
    while [[ $# -gt 0 ]]; do
        case $1 in
            --config)
                CONFIG_FILE="$2"
                shift 2
                ;;
            --interval)
                PROBE_INTERVAL="$2"
                shift 2
                ;;
            --retention)
                LOG_RETENTION_HOURS="$2"
                shift 2
                ;;
            *)
                if [ -z "$command" ] || [ "$command" = "help" ]; then
                    command="$1"
                elif [ -z "$endpoint" ]; then
                    endpoint="$1"
                fi
                shift
                ;;
        esac
    done

    # Initialize
    check_dependencies
    setup_directories

    case "$command" in
        start)
            if [ -n "$endpoint" ]; then
                # Parse specific endpoint from config
                local endpoint_data
                endpoint_data=$(yq eval ".endpoints[] | select(.name == \"$endpoint\") | [.name, .url, .health_path, .timeout] | @tsv" "$CONFIG_FILE")
                if [ -n "$endpoint_data" ]; then
                    IFS=$'\t' read -r name url health_path timeout <<< "$endpoint_data"
                    start_probe "$name" "$url" "${health_path:-/health}" "${timeout:-10}"
                else
                    log_error "Endpoint '$endpoint' not found in configuration"
                    exit 1
                fi
            else
                start_all_probes
            fi
            ;;
        stop)
            if [ -n "$endpoint" ]; then
                stop_probe "$endpoint"
            else
                stop_all_probes
            fi
            ;;
        restart)
            if [ -n "$endpoint" ]; then
                stop_probe "$endpoint"
                sleep 1
                local endpoint_data
                endpoint_data=$(yq eval ".endpoints[] | select(.name == \"$endpoint\") | [.name, .url, .health_path, .timeout] | @tsv" "$CONFIG_FILE")
                if [ -n "$endpoint_data" ]; then
                    IFS=$'\t' read -r name url health_path timeout <<< "$endpoint_data"
                    start_probe "$name" "$url" "${health_path:-/health}" "${timeout:-10}"
                fi
            else
                stop_all_probes
                sleep 2
                start_all_probes
            fi
            ;;
        status)
            show_status
            ;;
        cleanup)
            cleanup_logs
            ;;
        report)
            generate_report
            ;;
        help|--help|-h)
            show_usage
            ;;
        *)
            log_error "Unknown command: $command"
            show_usage
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"