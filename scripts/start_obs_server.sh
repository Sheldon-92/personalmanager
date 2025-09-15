#!/bin/bash

# API Server Startup Wrapper for OBS
# Starts API server on port 8001 with metric collection enabled

set -euo pipefail

# Configuration
PROJECT_ROOT="/Users/sheldonzhao/programs/personal-manager"
API_PORT="${API_PORT:-8001}"
API_HOST="${API_HOST:-localhost}"
CONFIG_FILE="${CONFIG_FILE:-$PROJECT_ROOT/configs/observability/dual_write_config.yaml}"
LOG_DIR="${LOG_DIR:-$PROJECT_ROOT/logs}"
PID_FILE="${PID_FILE:-$LOG_DIR/obs_server.pid}"

# Python environment
PYTHON_CMD="${PYTHON_CMD:-python3}"
PYTHONPATH="$PROJECT_ROOT/src:${PYTHONPATH:-}"

# Create necessary directories
mkdir -p "$LOG_DIR"

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >&2
}

# Function to check if server is running
is_server_running() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            return 0
        else
            rm -f "$PID_FILE"
            return 1
        fi
    fi
    return 1
}

# Function to start the API server
start_server() {
    log "Starting OBS API server on $API_HOST:$API_PORT"

    # Check if server is already running
    if is_server_running; then
        log "Server is already running (PID: $(cat "$PID_FILE"))"
        return 1
    fi

    # Validate configuration file
    if [ ! -f "$CONFIG_FILE" ]; then
        log "ERROR: Configuration file not found: $CONFIG_FILE"
        return 1
    fi

    # Start the server in background
    PYTHONPATH="$PYTHONPATH" nohup "$PYTHON_CMD" -c "
import sys
import os
import json
import time
import signal
import logging
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('$LOG_DIR/obs_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('obs_server')

# Load configuration
with open('$CONFIG_FILE', 'r') as f:
    config = yaml.safe_load(f)

class ObsAPIHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.start_time = datetime.utcnow()
        self.request_count = 0
        super().__init__(*args, **kwargs)

    def log_message(self, format, *args):
        logger.info(format % args)

    def do_GET(self):
        self.request_count += 1
        parsed_path = urlparse(self.path)

        if parsed_path.path == '/health':
            self.handle_health_check()
        elif parsed_path.path == '/metrics/legacy':
            self.handle_legacy_metrics()
        elif parsed_path.path == '/metrics/standard':
            self.handle_standard_metrics()
        elif parsed_path.path == '/system/info':
            self.handle_system_info()
        else:
            self.send_error(404, 'Endpoint not found')

    def handle_health_check(self):
        response = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'uptime_seconds': (datetime.utcnow() - self.start_time).total_seconds(),
            'version': '1.0.0',
            'service': 'obs-api-server'
        }
        self.send_json_response(200, response)

    def handle_legacy_metrics(self):
        current_time = datetime.utcnow()
        metrics = [
            {
                'timestamp': current_time.isoformat() + 'Z',
                'metric_name': 'api.requests.total',
                'value': self.request_count,
                'tags': {'endpoint': 'legacy', 'method': 'GET'},
                'source': 'obs-api-server'
            },
            {
                'timestamp': current_time.isoformat() + 'Z',
                'metric_name': 'api.uptime.seconds',
                'value': (current_time - self.start_time).total_seconds(),
                'tags': {'service': 'obs-api'},
                'source': 'obs-api-server'
            },
            {
                'timestamp': current_time.isoformat() + 'Z',
                'metric_name': 'system.memory.usage',
                'value': 85.2,
                'tags': {'unit': 'percent', 'type': 'virtual'},
                'source': 'system-monitor'
            }
        ]
        self.send_json_response(200, {'metrics': metrics})

    def handle_standard_metrics(self):
        current_time = datetime.utcnow()
        timestamp_nano = int(current_time.timestamp() * 1_000_000_000)

        metrics = [
            {
                'timestamp': timestamp_nano,
                'metric_type': 'counter',
                'name': 'api_requests_total',
                'value': self.request_count,
                'unit': 'requests',
                'labels': {'endpoint': 'standard', 'method': 'GET', 'status': '200'},
                'metadata': {
                    'service_name': 'obs-api-server',
                    'service_version': '1.0.0',
                    'environment': 'development',
                    'node_id': 'node-001'
                }
            },
            {
                'timestamp': timestamp_nano,
                'metric_type': 'gauge',
                'name': 'api_uptime_seconds',
                'value': (current_time - self.start_time).total_seconds(),
                'unit': 'seconds',
                'labels': {'service': 'obs-api'},
                'metadata': {
                    'service_name': 'obs-api-server',
                    'service_version': '1.0.0',
                    'environment': 'development',
                    'node_id': 'node-001'
                }
            },
            {
                'timestamp': timestamp_nano,
                'metric_type': 'gauge',
                'name': 'system_memory_usage_percent',
                'value': 85.2,
                'unit': 'percent',
                'labels': {'type': 'virtual', 'component': 'system'},
                'metadata': {
                    'service_name': 'system-monitor',
                    'service_version': '1.0.0',
                    'environment': 'development',
                    'node_id': 'node-001'
                }
            }
        ]
        self.send_json_response(200, {'metrics': metrics})

    def handle_system_info(self):
        response = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'system': {
                'hostname': os.uname().nodename,
                'platform': os.uname().sysname,
                'version': os.uname().release,
                'architecture': os.uname().machine
            },
            'service': {
                'name': 'obs-api-server',
                'version': '1.0.0',
                'pid': os.getpid(),
                'python_version': sys.version.split()[0]
            },
            'metrics': {
                'total_requests': self.request_count,
                'uptime_seconds': (datetime.utcnow() - self.start_time).total_seconds()
            }
        }
        self.send_json_response(200, response)

    def send_json_response(self, status_code, data):
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())

# Signal handler for graceful shutdown
def signal_handler(signum, frame):
    logger.info('Received signal %s, shutting down gracefully...', signum)
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

# Start the server
try:
    server = HTTPServer(('$API_HOST', $API_PORT), ObsAPIHandler)
    logger.info('OBS API Server started on http://$API_HOST:$API_PORT')
    logger.info('Available endpoints:')
    logger.info('  GET /health - Health check')
    logger.info('  GET /metrics/legacy - Legacy format metrics')
    logger.info('  GET /metrics/standard - Standard format metrics')
    logger.info('  GET /system/info - System information')

    server.serve_forever()
except Exception as e:
    logger.error('Failed to start server: %s', e)
    sys.exit(1)
" > "$LOG_DIR/obs_server.log" 2>&1 &

    # Save PID
    echo $! > "$PID_FILE"
    local pid=$!

    log "Server started with PID: $pid"
    log "Waiting for server to be ready..."

    # Wait for server to be ready
    local max_attempts=30
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if curl -s "http://$API_HOST:$API_PORT/health" > /dev/null 2>&1; then
            log "Server is ready and responding to health checks"
            return 0
        fi

        log "Attempt $attempt/$max_attempts: Server not ready yet..."
        sleep 2
        attempt=$((attempt + 1))
    done

    log "ERROR: Server failed to start within timeout"
    stop_server
    return 1
}

# Function to stop the API server
stop_server() {
    if is_server_running; then
        local pid=$(cat "$PID_FILE")
        log "Stopping OBS API server (PID: $pid)"

        kill "$pid"

        # Wait for graceful shutdown
        local attempts=0
        while [ $attempts -lt 10 ] && kill -0 "$pid" 2>/dev/null; do
            sleep 1
            attempts=$((attempts + 1))
        done

        # Force kill if still running
        if kill -0 "$pid" 2>/dev/null; then
            log "Force killing server..."
            kill -9 "$pid"
        fi

        rm -f "$PID_FILE"
        log "Server stopped"
    else
        log "Server is not running"
    fi
}

# Function to restart the server
restart_server() {
    log "Restarting OBS API server..."
    stop_server
    sleep 2
    start_server
}

# Function to show server status
status_server() {
    if is_server_running; then
        local pid=$(cat "$PID_FILE")
        log "Server is running (PID: $pid)"

        # Test health endpoint
        if curl -s "http://$API_HOST:$API_PORT/health" > /dev/null; then
            log "Health check: PASS"
        else
            log "Health check: FAIL"
        fi
        return 0
    else
        log "Server is not running"
        return 1
    fi
}

# Function to start dual-write collector
start_collector() {
    log "Starting dual-write metric collector..."

    PYTHONPATH="$PYTHONPATH" "$PYTHON_CMD" "$PROJECT_ROOT/src/pm/obs/dual_write_collector.py" \
        --config "$CONFIG_FILE" \
        --daemon > "$LOG_DIR/dual_write_collector.log" 2>&1 &

    echo $! > "$LOG_DIR/dual_write_collector.pid"
    log "Dual-write collector started with PID: $!"
}

# Function to start health probe
start_health_probe() {
    log "Starting health probe..."

    API_ENDPOINT="http://$API_HOST:$API_PORT" \
    OUTPUT_FILE="$LOG_DIR/health_probe.jsonl" \
    METRICS_FILE="$LOG_DIR/health_metrics.jsonl" \
    "$PROJECT_ROOT/scripts/health_probe.sh" > "$LOG_DIR/health_probe.log" 2>&1 &

    echo $! > "$LOG_DIR/health_probe.pid"
    log "Health probe started with PID: $!"
}

# Main script logic
case "${1:-start}" in
    start)
        start_server
        if [ $? -eq 0 ]; then
            start_collector
            start_health_probe
            log "All components started successfully"
            log "Server: http://$API_HOST:$API_PORT"
            log "Logs: $LOG_DIR/"
        fi
        ;;
    stop)
        stop_server
        # Stop collector and health probe
        for service in dual_write_collector health_probe; do
            pid_file="$LOG_DIR/${service}.pid"
            if [ -f "$pid_file" ]; then
                pid=$(cat "$pid_file")
                if kill -0 "$pid" 2>/dev/null; then
                    log "Stopping $service (PID: $pid)"
                    kill "$pid"
                fi
                rm -f "$pid_file"
            fi
        done
        ;;
    restart)
        restart_server
        ;;
    status)
        status_server
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac