#!/bin/bash

# OBS-O2 Alert Replay Testing Script
# Replays historical incidents and generates synthetic failures to test alert accuracy
# Target: <5% false positive rate, 0% false negative rate

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TEST_RESULTS_DIR="$PROJECT_ROOT/docs/reports/phase_5"
LOGS_DIR="$PROJECT_ROOT/logs/alert_testing"
TIMESTAMP=$(date "+%Y%m%d_%H%M%S")

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOGS_DIR/alert_test_$TIMESTAMP.log"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "$LOGS_DIR/alert_test_$TIMESTAMP.log"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOGS_DIR/alert_test_$TIMESTAMP.log"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOGS_DIR/alert_test_$TIMESTAMP.log"
}

# Setup test environment
setup_test_environment() {
    log_info "Setting up alert testing environment..."

    # Create necessary directories
    mkdir -p "$TEST_RESULTS_DIR"
    mkdir -p "$LOGS_DIR"

    # Check dependencies
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 is required but not installed"
        exit 1
    fi

    # Check if PM is installed
    if ! python3 -c "import src.pm" 2>/dev/null; then
        log_error "PM module not found. Ensure PM is properly installed."
        exit 1
    fi

    log_success "Test environment setup complete"
}

# Historical incident patterns (synthetic data for testing)
generate_historical_incidents() {
    local incidents_file="$LOGS_DIR/historical_incidents_$TIMESTAMP.json"

    log_info "Generating historical incident patterns..."

    cat > "$incidents_file" << 'EOF'
{
  "incidents": [
    {
      "id": "INC-2024-001",
      "timestamp": "2024-08-15T14:30:00Z",
      "type": "network_failure",
      "duration_minutes": 45,
      "affected_metrics": ["api_response_time", "error_rate"],
      "severity": "critical",
      "root_cause": "Load balancer node failure",
      "pattern": {
        "error_rate_peak": 0.35,
        "latency_p99_peak": 2500,
        "requests_affected": 15000
      }
    },
    {
      "id": "INC-2024-002",
      "timestamp": "2024-08-22T09:15:00Z",
      "type": "database_performance",
      "duration_minutes": 25,
      "affected_metrics": ["api_response_time"],
      "severity": "high",
      "root_cause": "Database lock contention",
      "pattern": {
        "latency_p99_peak": 1800,
        "latency_p95_peak": 1200,
        "queries_affected": 8500
      }
    },
    {
      "id": "INC-2024-003",
      "timestamp": "2024-09-01T16:45:00Z",
      "type": "cache_failure",
      "duration_minutes": 15,
      "affected_metrics": ["cache_hit_rate", "api_response_time"],
      "severity": "medium",
      "root_cause": "Redis cluster split-brain",
      "pattern": {
        "cache_hit_rate_drop": 0.15,
        "latency_increase": 300,
        "cache_requests": 25000
      }
    },
    {
      "id": "INC-2024-004",
      "timestamp": "2024-09-05T11:20:00Z",
      "type": "resource_exhaustion",
      "duration_minutes": 120,
      "affected_metrics": ["memory_usage", "cpu_usage", "api_response_time"],
      "severity": "critical",
      "root_cause": "Memory leak in service",
      "pattern": {
        "memory_peak": 95,
        "cpu_peak": 88,
        "latency_degradation": 400
      }
    },
    {
      "id": "INC-2024-005",
      "timestamp": "2024-09-08T20:10:00Z",
      "type": "deployment_failure",
      "duration_minutes": 35,
      "affected_metrics": ["error_rate", "api_response_time"],
      "severity": "high",
      "root_cause": "Bad deployment with regression",
      "pattern": {
        "error_rate_spike": 0.28,
        "latency_spike": 800,
        "deployment_rollback": true
      }
    }
  ]
}
EOF

    log_success "Generated historical incidents data at $incidents_file"
    echo "$incidents_file"
}

# Run specific alert scenario
run_alert_scenario() {
    local scenario_name="$1"
    local output_file="$2"

    log_info "Running alert scenario: $scenario_name"

    cd "$PROJECT_ROOT"

    # Run the scenario using the alert testing module
    python3 -m tests.obs.alert_scenarios \
        --scenario "$scenario_name" \
        --output "$output_file" \
        2>&1 | tee -a "$LOGS_DIR/scenario_$scenario_name_$TIMESTAMP.log"

    if [ $? -eq 0 ]; then
        log_success "Scenario $scenario_name completed successfully"
        return 0
    else
        log_error "Scenario $scenario_name failed"
        return 1
    fi
}

# Run category of scenarios
run_scenario_category() {
    local category="$1"
    local output_file="$2"

    log_info "Running alert scenarios for category: $category"

    cd "$PROJECT_ROOT"

    python3 -m tests.obs.alert_scenarios \
        --category "$category" \
        --output "$output_file" \
        2>&1 | tee -a "$LOGS_DIR/category_${category}_$TIMESTAMP.log"

    if [ $? -eq 0 ]; then
        log_success "Category $category scenarios completed successfully"
        return 0
    else
        log_error "Category $category scenarios failed"
        return 1
    fi
}

# Run comprehensive alert testing
run_comprehensive_testing() {
    local output_file="$TEST_RESULTS_DIR/alert_test_results.json"
    local temp_results_dir="$LOGS_DIR/temp_results_$TIMESTAMP"

    mkdir -p "$temp_results_dir"

    log_info "Starting comprehensive alert testing (N≥50 scenarios)..."

    cd "$PROJECT_ROOT"

    # Run all scenarios
    python3 -m tests.obs.alert_scenarios \
        --output "$output_file" \
        2>&1 | tee -a "$LOGS_DIR/comprehensive_test_$TIMESTAMP.log"

    local exit_code=$?

    if [ $exit_code -eq 0 ]; then
        log_success "Comprehensive testing completed successfully"

        # Validate results
        validate_test_results "$output_file"

        return 0
    else
        log_error "Comprehensive testing failed with exit code: $exit_code"
        return 1
    fi
}

# Validate test results against acceptance criteria
validate_test_results() {
    local results_file="$1"

    log_info "Validating test results against acceptance criteria..."

    if [ ! -f "$results_file" ]; then
        log_error "Results file not found: $results_file"
        return 1
    fi

    # Extract key metrics using Python
    local validation_script=$(cat << 'EOF'
import json
import sys

def validate_results(results_file):
    try:
        with open(results_file, 'r') as f:
            data = json.load(f)

        # Extract key metrics
        performance = data.get('performance_metrics', {})
        fp_rate = performance.get('overall_false_positive_rate', 1.0)
        fn_rate = performance.get('overall_false_negative_rate', 1.0)

        test_summary = data.get('test_summary', {})
        total_scenarios = test_summary.get('total_scenarios', 0)

        # Acceptance criteria
        fp_target = 0.05  # <5%
        fn_target = 0.0   # 0%
        min_scenarios = 50

        print(f"Results Summary:")
        print(f"- Total scenarios tested: {total_scenarios}")
        print(f"- False positive rate: {fp_rate:.2%}")
        print(f"- False negative rate: {fn_rate:.2%}")
        print(f"- FP target (<5%): {'PASS' if fp_rate < fp_target else 'FAIL'}")
        print(f"- FN target (0%): {'PASS' if fn_rate <= fn_target else 'FAIL'}")
        print(f"- Scenario count (≥50): {'PASS' if total_scenarios >= min_scenarios else 'FAIL'}")

        # Overall assessment
        passes_all = (
            fp_rate < fp_target and
            fn_rate <= fn_target and
            total_scenarios >= min_scenarios
        )

        print(f"\nOverall Result: {'PASS' if passes_all else 'FAIL'}")

        return 0 if passes_all else 1

    except Exception as e:
        print(f"Error validating results: {e}")
        return 1

if __name__ == "__main__":
    exit(validate_results(sys.argv[1]))
EOF
    )

    echo "$validation_script" | python3 - "$results_file"
    local validation_result=$?

    if [ $validation_result -eq 0 ]; then
        log_success "All acceptance criteria met!"
    else
        log_warn "Some acceptance criteria not met. Check results for details."
    fi

    return $validation_result
}

# Replay historical incidents
replay_historical_incidents() {
    local incidents_file="$1"
    local output_file="$TEST_RESULTS_DIR/historical_replay_results_$TIMESTAMP.json"

    log_info "Replaying historical incidents from: $incidents_file"

    # Create replay script
    local replay_script=$(cat << 'EOF'
import json
import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.obs.alert_scenarios import AlertTestEngine, FailureScenario

async def replay_incidents(incidents_file, output_file):
    try:
        with open(incidents_file, 'r') as f:
            incidents_data = json.load(f)

        engine = AlertTestEngine()
        replay_scenarios = []

        # Convert historical incidents to test scenarios
        for incident in incidents_data['incidents']:
            scenario = FailureScenario(
                name=f"replay_{incident['id']}",
                category="historical_replay",
                description=f"Replay of {incident['id']}: {incident['root_cause']}",
                duration_seconds=min(incident['duration_minutes'] * 60, 300),  # Cap at 5 minutes
                expected_alerts=determine_expected_alerts(incident),
                false_positive_risk=0.1,  # Default for historical
                severity=incident['severity']
            )
            replay_scenarios.append(scenario)

        # Run replay scenarios
        engine.scenarios = replay_scenarios
        results = await engine.run_all_scenarios()

        # Save results
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"Historical replay completed. Results saved to: {output_file}")
        return 0

    except Exception as e:
        print(f"Error in historical replay: {e}")
        return 1

def determine_expected_alerts(incident):
    """Determine expected alerts based on incident type and metrics"""
    alerts = []

    if 'error_rate' in incident['affected_metrics']:
        alerts.append('High Error Rate')
    if 'api_response_time' in incident['affected_metrics']:
        alerts.append('High P99 Latency')
    if 'cache_hit_rate' in incident['affected_metrics']:
        alerts.append('Low Cache Hit Rate')
    if 'memory_usage' in incident['affected_metrics']:
        alerts.append('High Memory Usage')
    if 'cpu_usage' in incident['affected_metrics']:
        alerts.append('High CPU Usage')
    if 'disk_usage' in incident['affected_metrics']:
        alerts.append('High Disk Usage')

    return alerts

if __name__ == "__main__":
    asyncio.run(replay_incidents(sys.argv[1], sys.argv[2]))
EOF
    )

    echo "$replay_script" | python3 - "$incidents_file" "$output_file"

    if [ $? -eq 0 ]; then
        log_success "Historical incident replay completed"
        echo "$output_file"
    else
        log_error "Historical incident replay failed"
        return 1
    fi
}

# Generate synthetic failure patterns
generate_synthetic_failures() {
    local output_file="$TEST_RESULTS_DIR/synthetic_failures_$TIMESTAMP.json"

    log_info "Generating synthetic failure patterns..."

    local synthetic_script=$(cat << 'EOF'
import json
import sys
import asyncio
import random
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.obs.alert_scenarios import AlertTestEngine, FailureScenario

async def generate_synthetic_patterns(output_file):
    try:
        engine = AlertTestEngine()

        # Generate additional synthetic scenarios
        synthetic_scenarios = [
            FailureScenario(
                name="synthetic_ddos_attack",
                category="synthetic",
                description="Simulated DDoS attack causing service degradation",
                duration_seconds=90,
                expected_alerts=["High Error Rate", "High P99 Latency"],
                false_positive_risk=0.05,
                severity="critical"
            ),
            FailureScenario(
                name="synthetic_data_corruption",
                category="synthetic",
                description="Data corruption causing validation errors",
                duration_seconds=60,
                expected_alerts=["High Error Rate"],
                false_positive_risk=0.15,
                severity="high"
            ),
            FailureScenario(
                name="synthetic_third_party_timeout",
                category="synthetic",
                description="Third-party service timeout cascade",
                duration_seconds=45,
                expected_alerts=["High P99 Latency", "High Error Rate"],
                false_positive_risk=0.1,
                severity="high"
            ),
            FailureScenario(
                name="synthetic_config_error",
                category="synthetic",
                description="Configuration error causing startup failures",
                duration_seconds=30,
                expected_alerts=["High Error Rate"],
                false_positive_risk=0.05,
                severity="critical"
            ),
            FailureScenario(
                name="synthetic_token_expiry_storm",
                category="synthetic",
                description="Mass token expiry causing auth failures",
                duration_seconds=75,
                expected_alerts=["High Error Rate"],
                false_positive_risk=0.2,
                severity="medium"
            )
        ]

        # Run synthetic scenarios
        engine.scenarios = synthetic_scenarios
        results = await engine.run_all_scenarios()

        # Save results
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"Synthetic failure testing completed. Results saved to: {output_file}")
        return 0

    except Exception as e:
        print(f"Error in synthetic failure generation: {e}")
        return 1

if __name__ == "__main__":
    asyncio.run(generate_synthetic_patterns(sys.argv[1]))
EOF
    )

    echo "$synthetic_script" | python3 - "$output_file"

    if [ $? -eq 0 ]; then
        log_success "Synthetic failure testing completed"
        echo "$output_file"
    else
        log_error "Synthetic failure testing failed"
        return 1
    fi
}

# Generate comprehensive test report
generate_final_report() {
    local comprehensive_results="$TEST_RESULTS_DIR/alert_test_results.json"
    local historical_results="$TEST_RESULTS_DIR/historical_replay_results_*.json"
    local synthetic_results="$TEST_RESULTS_DIR/synthetic_failures_*.json"
    local final_report="$TEST_RESULTS_DIR/phase_5_alert_testing_final_report.json"

    log_info "Generating final comprehensive report..."

    local report_script=$(cat << 'EOF'
import json
import sys
import glob
from pathlib import Path
from datetime import datetime

def merge_results(comprehensive_file, historical_pattern, synthetic_pattern, output_file):
    try:
        final_report = {
            "report_metadata": {
                "generation_timestamp": datetime.now().isoformat(),
                "report_type": "OBS-O2_Alert_Testing_Final_Report",
                "phase": "Phase 5 - Alert Tuning Testing"
            },
            "executive_summary": {},
            "comprehensive_testing": {},
            "historical_replay": {},
            "synthetic_testing": {},
            "recommendations": {},
            "acceptance_criteria_status": {}
        }

        # Load comprehensive results
        if Path(comprehensive_file).exists():
            with open(comprehensive_file, 'r') as f:
                comp_data = json.load(f)
            final_report["comprehensive_testing"] = comp_data

        # Load historical replay results
        historical_files = glob.glob(historical_pattern)
        if historical_files:
            with open(historical_files[-1], 'r') as f:  # Latest file
                hist_data = json.load(f)
            final_report["historical_replay"] = hist_data

        # Load synthetic results
        synthetic_files = glob.glob(synthetic_pattern)
        if synthetic_files:
            with open(synthetic_files[-1], 'r') as f:  # Latest file
                synth_data = json.load(f)
            final_report["synthetic_testing"] = synth_data

        # Calculate executive summary
        total_scenarios = 0
        total_fp_rate = 0
        total_fn_rate = 0

        for test_type in ["comprehensive_testing", "historical_replay", "synthetic_testing"]:
            test_data = final_report.get(test_type, {})
            if test_data:
                perf_metrics = test_data.get("performance_metrics", {})
                test_summary = test_data.get("test_summary", {})

                scenarios = test_summary.get("total_scenarios", 0)
                fp_rate = perf_metrics.get("overall_false_positive_rate", 0)
                fn_rate = perf_metrics.get("overall_false_negative_rate", 0)

                total_scenarios += scenarios
                total_fp_rate += fp_rate * scenarios  # Weighted average
                total_fn_rate += fn_rate * scenarios  # Weighted average

        if total_scenarios > 0:
            avg_fp_rate = total_fp_rate / total_scenarios
            avg_fn_rate = total_fn_rate / total_scenarios
        else:
            avg_fp_rate = 0
            avg_fn_rate = 0

        final_report["executive_summary"] = {
            "total_scenarios_tested": total_scenarios,
            "overall_false_positive_rate": avg_fp_rate,
            "overall_false_negative_rate": avg_fn_rate,
            "meets_fp_criteria": avg_fp_rate < 0.05,
            "meets_fn_criteria": avg_fn_rate == 0.0,
            "meets_scenario_count": total_scenarios >= 50
        }

        # Acceptance criteria status
        final_report["acceptance_criteria_status"] = {
            "false_positive_target": "< 5%",
            "false_negative_target": "0%",
            "minimum_scenarios": "≥ 50",
            "fp_result": f"{avg_fp_rate:.2%}",
            "fn_result": f"{avg_fn_rate:.2%}",
            "scenario_count": total_scenarios,
            "overall_status": "PASS" if (avg_fp_rate < 0.05 and avg_fn_rate == 0.0 and total_scenarios >= 50) else "FAIL"
        }

        # Generate recommendations
        final_report["recommendations"] = {
            "alert_tuning": [],
            "monitoring_improvements": [],
            "operational_procedures": []
        }

        if avg_fp_rate >= 0.05:
            final_report["recommendations"]["alert_tuning"].append({
                "issue": "High false positive rate",
                "recommendation": "Increase alert thresholds for metrics with high FP rates",
                "priority": "high"
            })

        if avg_fn_rate > 0.0:
            final_report["recommendations"]["alert_tuning"].append({
                "issue": "False negatives detected",
                "recommendation": "Decrease alert thresholds to catch missed incidents",
                "priority": "critical"
            })

        # Save final report
        with open(output_file, 'w') as f:
            json.dump(final_report, f, indent=2)

        print(f"Final report generated: {output_file}")
        print(f"Total scenarios tested: {total_scenarios}")
        print(f"Overall FP rate: {avg_fp_rate:.2%}")
        print(f"Overall FN rate: {avg_fn_rate:.2%}")
        print(f"Acceptance criteria: {final_report['acceptance_criteria_status']['overall_status']}")

        return 0

    except Exception as e:
        print(f"Error generating final report: {e}")
        return 1

if __name__ == "__main__":
    merge_results(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
EOF
    )

    echo "$report_script" | python3 - "$comprehensive_results" "$historical_results" "$synthetic_results" "$final_report"

    if [ $? -eq 0 ]; then
        log_success "Final report generated at: $final_report"
        echo "$final_report"
    else
        log_error "Failed to generate final report"
        return 1
    fi
}

# Quick test mode (subset of scenarios)
run_quick_test() {
    local output_file="$TEST_RESULTS_DIR/quick_test_results_$TIMESTAMP.json"

    log_info "Running quick test (subset of scenarios)..."

    cd "$PROJECT_ROOT"

    python3 -m tests.obs.alert_scenarios \
        --quick \
        --output "$output_file" \
        2>&1 | tee -a "$LOGS_DIR/quick_test_$TIMESTAMP.log"

    if [ $? -eq 0 ]; then
        log_success "Quick test completed successfully"
        validate_test_results "$output_file"
        echo "$output_file"
    else
        log_error "Quick test failed"
        return 1
    fi
}

# Main execution function
main() {
    local mode="${1:-comprehensive}"
    local scenario_name="${2:-}"
    local category="${3:-}"

    log_info "Starting OBS-O2 Alert Replay Testing..."
    log_info "Mode: $mode"

    # Setup environment
    setup_test_environment

    case "$mode" in
        "comprehensive")
            log_info "Running comprehensive alert testing..."
            run_comprehensive_testing
            ;;
        "quick")
            log_info "Running quick test..."
            run_quick_test
            ;;
        "scenario")
            if [ -z "$scenario_name" ]; then
                log_error "Scenario name required for scenario mode"
                echo "Usage: $0 scenario <scenario_name>"
                exit 1
            fi
            local output_file="$TEST_RESULTS_DIR/scenario_${scenario_name}_$TIMESTAMP.json"
            run_alert_scenario "$scenario_name" "$output_file"
            ;;
        "category")
            if [ -z "$category" ]; then
                log_error "Category name required for category mode"
                echo "Usage: $0 category <category_name>"
                exit 1
            fi
            local output_file="$TEST_RESULTS_DIR/category_${category}_$TIMESTAMP.json"
            run_scenario_category "$category" "$output_file"
            ;;
        "historical")
            log_info "Running historical incident replay..."
            incidents_file=$(generate_historical_incidents)
            replay_historical_incidents "$incidents_file"
            ;;
        "synthetic")
            log_info "Running synthetic failure testing..."
            generate_synthetic_failures
            ;;
        "full")
            log_info "Running full test suite..."

            # Run comprehensive testing
            run_comprehensive_testing

            # Generate and replay historical incidents
            incidents_file=$(generate_historical_incidents)
            replay_historical_incidents "$incidents_file"

            # Generate synthetic failures
            generate_synthetic_failures

            # Generate final report
            generate_final_report
            ;;
        "report")
            log_info "Generating final report from existing results..."
            generate_final_report
            ;;
        *)
            echo "Usage: $0 {comprehensive|quick|scenario|category|historical|synthetic|full|report} [scenario_name|category_name]"
            echo ""
            echo "Modes:"
            echo "  comprehensive - Run all N≥50 alert scenarios"
            echo "  quick        - Run subset of scenarios for quick validation"
            echo "  scenario     - Run specific scenario by name"
            echo "  category     - Run all scenarios in category (network|latency|errors|resources|cascade)"
            echo "  historical   - Replay historical incident patterns"
            echo "  synthetic    - Generate and test synthetic failure patterns"
            echo "  full         - Run complete test suite with all modes"
            echo "  report       - Generate final report from existing results"
            echo ""
            echo "Examples:"
            echo "  $0 comprehensive"
            echo "  $0 scenario network_timeout_cascade"
            echo "  $0 category network"
            echo "  $0 full"
            exit 1
            ;;
    esac

    local exit_code=$?

    if [ $exit_code -eq 0 ]; then
        log_success "OBS-O2 Alert Testing completed successfully!"
        log_info "Check logs in: $LOGS_DIR"
        log_info "Check results in: $TEST_RESULTS_DIR"
    else
        log_error "OBS-O2 Alert Testing failed!"
    fi

    exit $exit_code
}

# Handle script interruption
trap 'log_warn "Alert testing interrupted"; exit 130' INT TERM

# Execute main function with all arguments
main "$@"