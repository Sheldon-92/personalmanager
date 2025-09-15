#!/bin/bash

# Health Probe Script for OBS API Server
# Probes endpoint every 30s and writes results to JSONL
# Calculates uptime percentage

set -euo pipefail

# Configuration
API_ENDPOINT="${API_ENDPOINT:-http://localhost:8001}"
HEALTH_PATH="${HEALTH_PATH:-/health}"
PROBE_INTERVAL="${PROBE_INTERVAL:-30}"
OUTPUT_FILE="${OUTPUT_FILE:-/Users/sheldonzhao/programs/personal-manager/logs/health_probe.jsonl}"
METRICS_FILE="${METRICS_FILE:-/Users/sheldonzhao/programs/personal-manager/logs/health_metrics.jsonl}"

# Create logs directory if it doesn't exist
mkdir -p "$(dirname "$OUTPUT_FILE")"
mkdir -p "$(dirname "$METRICS_FILE")"

# Initialize counters
total_probes=0
successful_probes=0
start_time=$(date +%s)

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >&2
}

# Function to calculate uptime percentage
calculate_uptime() {
    if [ $total_probes -eq 0 ]; then
        echo "0"
    else
        echo "scale=2; $successful_probes * 100 / $total_probes" | bc -l
    fi
}

# Function to perform health check
perform_health_check() {
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ")
    local probe_start=$(date +%s.%3N)

    # Perform the health check
    local response_code
    local response_time
    local response_body=""
    local error_message=""

    if response=$(curl -s -w "%{http_code}" -m 10 "$API_ENDPOINT$HEALTH_PATH" 2>/dev/null); then
        response_code="${response: -3}"
        response_body="${response%???}"
        local probe_end=$(date +%s.%3N)
        response_time=$(echo "$probe_end - $probe_start" | bc -l)

        if [ "$response_code" = "200" ]; then
            successful_probes=$((successful_probes + 1))
            local status="healthy"
        else
            local status="unhealthy"
            error_message="HTTP $response_code"
        fi
    else
        local probe_end=$(date +%s.%3N)
        response_time=$(echo "$probe_end - $probe_start" | bc -l)
        response_code="000"
        local status="unhealthy"
        error_message="Connection failed"
    fi

    total_probes=$((total_probes + 1))
    local uptime_percentage=$(calculate_uptime)
    local runtime=$(($(date +%s) - start_time))

    # Create JSONL entry
    local jsonl_entry=$(cat <<EOF
{
  "timestamp": "$timestamp",
  "probe_id": "$total_probes",
  "endpoint": "$API_ENDPOINT$HEALTH_PATH",
  "status": "$status",
  "response_code": "$response_code",
  "response_time_ms": $(echo "$response_time * 1000" | bc -l | cut -d. -f1),
  "response_body": $(echo "$response_body" | jq -R . 2>/dev/null || echo "\"$response_body\""),
  "error_message": "$error_message",
  "uptime_percentage": $uptime_percentage,
  "total_probes": $total_probes,
  "successful_probes": $successful_probes,
  "runtime_seconds": $runtime
}
EOF
)

    # Write to output file
    echo "$jsonl_entry" >> "$OUTPUT_FILE"

    # Write metrics summary every 10 probes
    if [ $((total_probes % 10)) -eq 0 ]; then
        local metrics_entry=$(cat <<EOF
{
  "timestamp": "$timestamp",
  "metric_type": "health_summary",
  "total_probes": $total_probes,
  "successful_probes": $successful_probes,
  "failed_probes": $((total_probes - successful_probes)),
  "uptime_percentage": $uptime_percentage,
  "runtime_seconds": $runtime,
  "average_interval": $(echo "scale=2; $runtime / $total_probes" | bc -l)
}
EOF
)
        echo "$metrics_entry" >> "$METRICS_FILE"
    fi

    log "Probe #$total_probes: $status ($response_code) - ${response_time}s - Uptime: ${uptime_percentage}%"
}

# Signal handlers
cleanup() {
    log "Health probe shutting down..."
    local final_uptime=$(calculate_uptime)
    local final_runtime=$(($(date +%s) - start_time))

    log "Final stats: $successful_probes/$total_probes successful (${final_uptime}%) over ${final_runtime}s"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Main loop
log "Starting health probe for $API_ENDPOINT$HEALTH_PATH (interval: ${PROBE_INTERVAL}s)"
log "Output: $OUTPUT_FILE"
log "Metrics: $METRICS_FILE"

while true; do
    perform_health_check
    sleep "$PROBE_INTERVAL"
done