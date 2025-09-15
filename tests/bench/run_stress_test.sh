#!/bin/bash
# Plugin Stress Test Runner Script
# Provides easy execution of plugin stress tests with various configurations

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ROUNDS=10
WORKERS=4
MODE="threading"
P95_TARGET=300
P99_TARGET=500
LEAK_TOLERANCE=2.0

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"

# Function to print colored output
print_color() {
    local color=$1
    shift
    echo -e "${color}$@${NC}"
}

# Function to display usage
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Plugin Stress Test Runner - Tests concurrent plugin loading/unloading

OPTIONS:
    -h, --help              Show this help message
    -r, --rounds NUM        Number of test rounds (default: 10)
    -w, --workers NUM       Number of concurrent workers (default: 4)
    -m, --mode MODE         Concurrency mode: threading or multiprocess (default: threading)
    -p95 --p95-target MS    P95 latency target in milliseconds (default: 300)
    -p99 --p99-target MS    P99 latency target in milliseconds (default: 500)
    -l, --leak-tolerance %  Resource leak tolerance percentage (default: 2.0)
    --quick                 Quick test (3 rounds, 2 workers)
    --full                  Full test (20 rounds, 8 workers)
    --stress                Stress test (50 rounds, 16 workers)

EXAMPLES:
    # Quick test with default settings
    $0 --quick

    # Full test with multiprocessing
    $0 --full --mode multiprocess

    # Custom configuration
    $0 --rounds 15 --workers 6 --p95-target 250

    # Maximum stress test
    $0 --stress --leak-tolerance 1.0

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            exit 0
            ;;
        -r|--rounds)
            ROUNDS="$2"
            shift 2
            ;;
        -w|--workers)
            WORKERS="$2"
            shift 2
            ;;
        -m|--mode)
            MODE="$2"
            if [[ "$MODE" != "threading" && "$MODE" != "multiprocess" ]]; then
                print_color $RED "Error: Mode must be 'threading' or 'multiprocess'"
                exit 1
            fi
            shift 2
            ;;
        -p95|--p95-target)
            P95_TARGET="$2"
            shift 2
            ;;
        -p99|--p99-target)
            P99_TARGET="$2"
            shift 2
            ;;
        -l|--leak-tolerance)
            LEAK_TOLERANCE="$2"
            shift 2
            ;;
        --quick)
            ROUNDS=3
            WORKERS=2
            shift
            ;;
        --full)
            ROUNDS=20
            WORKERS=8
            shift
            ;;
        --stress)
            ROUNDS=50
            WORKERS=16
            shift
            ;;
        *)
            print_color $RED "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Display test configuration
print_color $BLUE "============================================"
print_color $BLUE "Plugin Stress Test Configuration"
print_color $BLUE "============================================"
echo "Rounds:          $ROUNDS"
echo "Workers:         $WORKERS"
echo "Mode:            $MODE"
echo "P95 Target:      ${P95_TARGET}ms"
echo "P99 Target:      ${P99_TARGET}ms"
echo "Leak Tolerance:  ${LEAK_TOLERANCE}%"
print_color $BLUE "============================================"
echo

# Check Python installation
if ! command -v python3 &> /dev/null; then
    print_color $RED "Error: Python 3 is not installed"
    exit 1
fi

# Check required Python packages
print_color $YELLOW "Checking Python dependencies..."
python3 -c "import psutil" 2>/dev/null || {
    print_color $RED "Error: psutil package not installed"
    print_color $YELLOW "Install with: pip install psutil"
    exit 1
}

python3 -c "import numpy" 2>/dev/null || {
    print_color $RED "Error: numpy package not installed"
    print_color $YELLOW "Install with: pip install numpy"
    exit 1
}

# Create output directory
OUTPUT_DIR="/tmp/plugin_stress_test"
mkdir -p "$OUTPUT_DIR"
print_color $GREEN "Output directory: $OUTPUT_DIR"

# Build command
CMD="python3 $SCRIPT_DIR/test_plugin_stress.py"
CMD="$CMD --rounds $ROUNDS"
CMD="$CMD --workers $WORKERS"
CMD="$CMD --p95-target $P95_TARGET"
CMD="$CMD --p99-target $P99_TARGET"
CMD="$CMD --leak-tolerance $LEAK_TOLERANCE"

if [[ "$MODE" == "multiprocess" ]]; then
    CMD="$CMD --multiprocess"
fi

# Run the stress test
print_color $YELLOW "Starting stress test..."
echo "Command: $CMD"
echo

# Execute with timing
START_TIME=$(date +%s)

if $CMD; then
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))

    print_color $GREEN ""
    print_color $GREEN "============================================"
    print_color $GREEN "Stress Test Completed Successfully!"
    print_color $GREEN "Total Duration: ${DURATION} seconds"
    print_color $GREEN "============================================"

    # Show output files
    echo
    print_color $BLUE "Output Files:"
    ls -la "$OUTPUT_DIR"/*.json 2>/dev/null | tail -5 || echo "No output files generated"

    exit 0
else
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))

    print_color $RED ""
    print_color $RED "============================================"
    print_color $RED "Stress Test Failed!"
    print_color $RED "Duration: ${DURATION} seconds"
    print_color $RED "============================================"

    # Show recent errors from log
    echo
    print_color $YELLOW "Check output files in: $OUTPUT_DIR"

    exit 1
fi