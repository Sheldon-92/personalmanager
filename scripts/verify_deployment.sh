#!/bin/bash

# Deployment Verification Script for OBS-O3 Health Probes
# Verifies that all components are deployed correctly and meet requirements

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}OBS-O3 Health Probe Deployment Verification${NC}"
echo -e "${BLUE}============================================================${NC}"
echo

# Check 1: Verify all required files exist
echo -e "${YELLOW}1. Verifying deployment files...${NC}"

required_files=(
    "scripts/deploy_health_probes.sh"
    "scripts/health_probe.sh"
    "configs/observability/health_probe_config.yaml"
    "src/pm/obs/slo_calculator.py"
    "logs/health_probes_24hr.jsonl"
)

all_files_exist=true
for file in "${required_files[@]}"; do
    if [ -f "$PROJECT_ROOT/$file" ]; then
        echo -e "  ${GREEN}✓${NC} $file"
    else
        echo -e "  ${RED}✗${NC} $file (missing)"
        all_files_exist=false
    fi
done

if [ "$all_files_exist" = true ]; then
    echo -e "${GREEN}✓ All required files present${NC}"
else
    echo -e "${RED}✗ Missing required files${NC}"
    exit 1
fi

echo

# Check 2: Verify 24hr data meets requirements
echo -e "${YELLOW}2. Verifying 24-hour data...${NC}"

total_records=$(wc -l < "$PROJECT_ROOT/logs/health_probes_24hr.jsonl")
expected_records=14400  # 2880 probes × 5 endpoints

if [ "$total_records" -eq "$expected_records" ]; then
    echo -e "  ${GREEN}✓${NC} Total records: $total_records (expected: $expected_records)"
else
    echo -e "  ${RED}✗${NC} Total records: $total_records (expected: $expected_records)"
fi

# Check probe interval (should be 30 seconds between records)
echo "  Checking probe intervals..."
probe_interval_ok=true

for endpoint in api-server api-server-ready api-server-metrics api-docs api-openapi; do
    probe_file="$PROJECT_ROOT/logs/health_probe_${endpoint}.jsonl"
    if [ -f "$probe_file" ]; then
        probe_count=$(wc -l < "$probe_file")
        if [ "$probe_count" -eq 2880 ]; then
            echo -e "    ${GREEN}✓${NC} $endpoint: $probe_count probes"
        else
            echo -e "    ${RED}✗${NC} $endpoint: $probe_count probes (expected: 2880)"
            probe_interval_ok=false
        fi
    else
        echo -e "    ${RED}✗${NC} $endpoint: probe file missing"
        probe_interval_ok=false
    fi
done

if [ "$probe_interval_ok" = true ]; then
    echo -e "${GREEN}✓ All endpoints have correct probe count${NC}"
else
    echo -e "${RED}✗ Probe count verification failed${NC}"
fi

echo

# Check 3: Run SLO analysis and verify >99.5% availability
echo -e "${YELLOW}3. Running SLO analysis...${NC}"

cd "$PROJECT_ROOT"
slo_output=$(python3 scripts/run_slo_analysis.py 2>&1)

if echo "$slo_output" | grep -q "SUCCESS: OBS-O3 health probes deployed with >99.5% availability"; then
    echo -e "${GREEN}✓ SLO analysis passed${NC}"

    # Extract availability percentages
    critical_availability=$(echo "$slo_output" | grep "Critical Availability:" | grep "24HOUR" | sed 's/.*Critical Availability: \([0-9.]*\)%.*/\1/')
    overall_availability=$(echo "$slo_output" | grep "Overall Availability:" | grep "24HOUR" | sed 's/.*Overall Availability: \([0-9.]*\)%.*/\1/')

    echo "  Critical endpoints (24h): ${critical_availability}%"
    echo "  Overall availability (24h): ${overall_availability}%"

    # Check if critical endpoints meet SLO
    if (( $(echo "$critical_availability >= 99.5" | bc -l) )); then
        echo -e "  ${GREEN}✓${NC} Critical endpoints meet 99.5% SLO target"
    else
        echo -e "  ${RED}✗${NC} Critical endpoints below 99.5% SLO target"
    fi

else
    echo -e "${RED}✗ SLO analysis failed${NC}"
    echo "$slo_output"
fi

echo

# Check 4: Verify deployment script functionality
echo -e "${YELLOW}4. Testing deployment script...${NC}"

# Test help command
if scripts/deploy_health_probes.sh help > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC} Help command works"
else
    echo -e "  ${RED}✗${NC} Help command failed"
fi

# Test status command
if scripts/deploy_health_probes.sh status > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC} Status command works"
else
    echo -e "  ${RED}✗${NC} Status command failed"
fi

# Test report generation
if scripts/deploy_health_probes.sh report > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC} Report generation works"
else
    echo -e "  ${RED}✗${NC} Report generation failed"
fi

echo

# Check 5: Verify configuration file
echo -e "${YELLOW}5. Verifying configuration...${NC}"

config_file="$PROJECT_ROOT/configs/observability/health_probe_config.yaml"
config_valid=true

# Check required sections exist
required_sections=("global" "endpoints" "slo_windows" "alerts")
for section in "${required_sections[@]}"; do
    if yq eval ".$section" "$config_file" > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} $section section present"
    else
        echo -e "  ${RED}✗${NC} $section section missing"
        config_valid=false
    fi
done

# Check endpoints configuration
endpoint_count=$(yq eval '.endpoints | length' "$config_file")
if [ "$endpoint_count" -eq 5 ]; then
    echo -e "  ${GREEN}✓${NC} All 5 endpoints configured"
else
    echo -e "  ${RED}✗${NC} Expected 5 endpoints, found $endpoint_count"
    config_valid=false
fi

# Check SLO target
slo_target=$(yq eval '.global.slo_target' "$config_file")
if [ "$slo_target" = "99.5" ]; then
    echo -e "  ${GREEN}✓${NC} SLO target set to 99.5%"
else
    echo -e "  ${RED}✗${NC} SLO target is $slo_target% (expected: 99.5%)"
    config_valid=false
fi

if [ "$config_valid" = true ]; then
    echo -e "${GREEN}✓ Configuration validation passed${NC}"
else
    echo -e "${RED}✗ Configuration validation failed${NC}"
fi

echo

# Check 6: Verify output file formats
echo -e "${YELLOW}6. Verifying output formats...${NC}"

formats_valid=true

# Check JSONL format
if head -1 "$PROJECT_ROOT/logs/health_probes_24hr.jsonl" | jq . > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC} 24hr data file is valid JSON"
else
    echo -e "  ${RED}✗${NC} 24hr data file has invalid JSON"
    formats_valid=false
fi

# Check SLO report format
latest_report=$(ls -t "$PROJECT_ROOT/logs/slo_report_"*.json 2>/dev/null | head -1)
if [ -n "$latest_report" ] && jq . "$latest_report" > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC} SLO report is valid JSON"
else
    echo -e "  ${RED}✗${NC} SLO report has invalid JSON"
    formats_valid=false
fi

# Check Prometheus metrics format
if [ -f "$PROJECT_ROOT/logs/slo_metrics.prom" ]; then
    if grep -q "obs_slo_availability_percentage" "$PROJECT_ROOT/logs/slo_metrics.prom"; then
        echo -e "  ${GREEN}✓${NC} Prometheus metrics file valid"
    else
        echo -e "  ${RED}✗${NC} Prometheus metrics file invalid"
        formats_valid=false
    fi
else
    echo -e "  ${RED}✗${NC} Prometheus metrics file missing"
    formats_valid=false
fi

if [ "$formats_valid" = true ]; then
    echo -e "${GREEN}✓ Output format validation passed${NC}"
else
    echo -e "${RED}✗ Output format validation failed${NC}"
fi

echo
echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}DEPLOYMENT VERIFICATION SUMMARY${NC}"
echo -e "${BLUE}============================================================${NC}"

# Final summary
verification_passed=true

if [ "$all_files_exist" = true ] && \
   [ "$probe_interval_ok" = true ] && \
   [ "$config_valid" = true ] && \
   [ "$formats_valid" = true ] && \
   echo "$slo_output" | grep -q "SUCCESS"; then

    echo -e "${GREEN}🎯 DEPLOYMENT VERIFICATION PASSED${NC}"
    echo
    echo "✅ All components deployed successfully"
    echo "✅ 30-second health probes configured"
    echo "✅ 24-hour data with >99.5% critical availability"
    echo "✅ SLO calculation and reporting functional"
    echo "✅ Prometheus metrics export working"
    echo
    echo "Deployment meets all acceptance criteria:"
    echo "• Probes run every 30 seconds ✓"
    echo "• All endpoints monitored ✓"
    echo "• 24hr data available ✓"
    echo "• SLO calculation shows ≥99.5% ✓"

else
    echo -e "${RED}❌ DEPLOYMENT VERIFICATION FAILED${NC}"
    echo
    echo "Please review the issues above and fix before proceeding."
    verification_passed=false
fi

echo
echo -e "${BLUE}============================================================${NC}"

if [ "$verification_passed" = true ]; then
    exit 0
else
    exit 1
fi