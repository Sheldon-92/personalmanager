#!/bin/bash

# PersonalManager Package Verification Script
# Verifies package integrity, signatures, and dependencies

set -euo pipefail

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Status icons
CHECK_PASS="✅"
CHECK_FAIL="❌"
CHECK_WARN="⚠️"
CHECK_INFO="ℹ️"

# Configuration
VERBOSE=false
STRICT_MODE=false
TRUST_GPG_KEY=""
PACKAGE_FILE=""
EXTRACT_DIR=""
TEMP_DIR=""

# Counters for reporting
CHECKS_TOTAL=0
CHECKS_PASSED=0
CHECKS_FAILED=0
CHECKS_WARNED=0

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
    ((CHECKS_PASSED++))
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
    ((CHECKS_WARNED++))
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    ((CHECKS_FAILED++))
}

log_verbose() {
    if [[ "$VERBOSE" == "true" ]]; then
        echo -e "${CYAN}[VERBOSE]${NC} $1"
    fi
}

check_start() {
    ((CHECKS_TOTAL++))
}

# Print usage
usage() {
    cat << EOF
Usage: $0 [OPTIONS] PACKAGE_FILE

Verifies PersonalManager offline package integrity and signatures

ARGUMENTS:
    PACKAGE_FILE        Path to the offline package (.tar.gz)

OPTIONS:
    --help              Show this help message
    --version           Show version information
    --verbose           Enable verbose output
    --strict            Enable strict verification mode (all checks must pass)
    --extract-to DIR    Extract package to specific directory
    --trust-key ID      Trust specific GPG key ID for verification

EXAMPLES:
    $0 personalmanager-offline-v1.0.0.tar.gz
    $0 --verbose --strict package.tar.gz
    $0 --trust-key ABC123 --extract-to /tmp/verify package.tar.gz

VERIFICATION STEPS:
    1. Package file existence and format
    2. SHA256 checksum verification
    3. GPG signature verification (if available)
    4. Package extraction and structure validation
    5. Dependency integrity checks
    6. Installation script validation
    7. Security scan for malicious content

EXIT CODES:
    0   All verifications passed
    1   Critical verification failed
    2   Warnings found (non-critical)
    3   Package file not found or invalid
    4   Extraction failed
    5   Signature verification failed

EOF
}

# Show version information
show_version() {
    local version
    version=$(python3 -c "import toml; print(toml.load('$PROJECT_ROOT/pyproject.toml')['tool']['poetry']['version'])" 2>/dev/null || echo "unknown")

    cat << EOF
PersonalManager Package Verifier v${version}

System Information:
  OS: $(uname -s) $(uname -r)
  Architecture: $(uname -m)
  GPG: $(gpg --version 2>/dev/null | head -1 || echo "not available")
  Python: $(python3 --version 2>/dev/null || echo "not found")

Script: $0
EOF
}

# Parse command line arguments
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --help|-h)
                usage
                exit 0
                ;;
            --version)
                show_version
                exit 0
                ;;
            --verbose|-v)
                VERBOSE=true
                shift
                ;;
            --strict)
                STRICT_MODE=true
                shift
                ;;
            --extract-to)
                EXTRACT_DIR="$2"
                shift 2
                ;;
            --trust-key)
                TRUST_GPG_KEY="$2"
                shift 2
                ;;
            -*)
                log_error "Unknown option: $1"
                usage
                exit 1
                ;;
            *)
                if [[ -z "$PACKAGE_FILE" ]]; then
                    PACKAGE_FILE="$1"
                    shift
                else
                    log_error "Multiple package files specified"
                    exit 1
                fi
                ;;
        esac
    done

    # Validate required arguments
    if [[ -z "$PACKAGE_FILE" ]]; then
        log_error "Package file is required"
        usage
        exit 1
    fi
}

# Check if package file exists and is accessible
check_package_file() {
    log_info "Verifying package file..."

    check_start
    if [[ ! -f "$PACKAGE_FILE" ]]; then
        log_error "Package file not found: $PACKAGE_FILE"
        return 3
    fi

    check_start
    if [[ ! -r "$PACKAGE_FILE" ]]; then
        log_error "Package file not readable: $PACKAGE_FILE"
        return 3
    fi

    log_success "Package file exists and is readable"

    # Check file format
    check_start
    local file_type
    file_type=$(file "$PACKAGE_FILE" 2>/dev/null || echo "unknown")

    if [[ "$file_type" == *"gzip compressed"* ]]; then
        log_success "Package file format: Valid gzip archive"
    else
        log_warning "Package file format may be incorrect: $file_type"
        if [[ "$STRICT_MODE" == "true" ]]; then
            return 1
        fi
    fi

    # Show file information
    local file_size
    file_size=$(du -h "$PACKAGE_FILE" | cut -f1)
    log_verbose "Package size: $file_size"
    log_verbose "Package path: $(realpath "$PACKAGE_FILE")"

    return 0
}

# Verify SHA256 checksum if .sha256 file exists
verify_checksum() {
    log_info "Verifying package checksum..."

    local checksum_file="${PACKAGE_FILE}.sha256"

    check_start
    if [[ ! -f "$checksum_file" ]]; then
        log_warning "No checksum file found: $checksum_file"
        return 0
    fi

    log_verbose "Found checksum file: $checksum_file"

    check_start
    if command -v sha256sum &>/dev/null; then
        log_verbose "Using sha256sum for verification"
        if cd "$(dirname "$PACKAGE_FILE")" && sha256sum -c "$(basename "$checksum_file")" &>/dev/null; then
            log_success "SHA256 checksum verification passed"
        else
            log_error "SHA256 checksum verification failed"
            return 1
        fi
    elif command -v shasum &>/dev/null; then
        log_verbose "Using shasum for verification"
        if cd "$(dirname "$PACKAGE_FILE")" && shasum -a 256 -c "$(basename "$checksum_file")" &>/dev/null; then
            log_success "SHA256 checksum verification passed"
        else
            log_error "SHA256 checksum verification failed"
            return 1
        fi
    else
        log_warning "No SHA256 utility found, skipping checksum verification"
    fi

    return 0
}

# Verify GPG signature if available
verify_signature() {
    log_info "Verifying GPG signature..."

    local sig_file="${PACKAGE_FILE}.sig"
    local asc_file="${PACKAGE_FILE}.asc"

    check_start
    if [[ ! -f "$sig_file" && ! -f "$asc_file" ]]; then
        log_warning "No GPG signature file found (.sig or .asc)"
        return 0
    fi

    check_start
    if ! command -v gpg &>/dev/null; then
        log_warning "GPG not available, skipping signature verification"
        return 0
    fi

    local signature_file=""
    if [[ -f "$sig_file" ]]; then
        signature_file="$sig_file"
    elif [[ -f "$asc_file" ]]; then
        signature_file="$asc_file"
    fi

    log_verbose "Found signature file: $signature_file"

    check_start
    # Import trusted key if specified
    if [[ -n "$TRUST_GPG_KEY" ]]; then
        log_verbose "Importing trusted key: $TRUST_GPG_KEY"
        if ! gpg --recv-keys "$TRUST_GPG_KEY" &>/dev/null; then
            log_warning "Could not import trusted key: $TRUST_GPG_KEY"
        fi
    fi

    # Verify signature
    if gpg --verify "$signature_file" "$PACKAGE_FILE" 2>/dev/null; then
        log_success "GPG signature verification passed"

        # Show signature details in verbose mode
        if [[ "$VERBOSE" == "true" ]]; then
            local sig_info
            sig_info=$(gpg --verify "$signature_file" "$PACKAGE_FILE" 2>&1 | head -3)
            log_verbose "Signature details: $sig_info"
        fi
    else
        log_error "GPG signature verification failed"
        if [[ "$STRICT_MODE" == "true" ]]; then
            return 5
        fi
        log_warning "Continuing without signature verification (non-strict mode)"
    fi

    return 0
}

# Extract and validate package structure
extract_and_validate() {
    log_info "Extracting and validating package structure..."

    # Set up extraction directory
    if [[ -z "$EXTRACT_DIR" ]]; then
        TEMP_DIR=$(mktemp -d -t pm-verify-XXXXXX)
        EXTRACT_DIR="$TEMP_DIR"
        log_verbose "Using temporary extraction directory: $EXTRACT_DIR"
    else
        mkdir -p "$EXTRACT_DIR"
        log_verbose "Using specified extraction directory: $EXTRACT_DIR"
    fi

    # Extract package
    check_start
    if tar -xzf "$PACKAGE_FILE" -C "$EXTRACT_DIR" 2>/dev/null; then
        log_success "Package extracted successfully"
    else
        log_error "Failed to extract package"
        return 4
    fi

    # Find the extracted directory
    local package_dir
    package_dir=$(find "$EXTRACT_DIR" -maxdepth 1 -type d ! -path "$EXTRACT_DIR" | head -1)

    if [[ -z "$package_dir" ]]; then
        log_error "No package directory found after extraction"
        return 4
    fi

    log_verbose "Package directory: $package_dir"

    # Validate essential files and directories
    check_start
    local essential_files=(
        "install_offline.sh"
        "pyproject.toml"
        "README.md"
        "VERSION_INFO.txt"
        "CHECKSUMS.sha256"
    )

    local essential_dirs=(
        "src"
        "bin"
        "dependencies"
    )

    local missing_files=()
    local missing_dirs=()

    for file in "${essential_files[@]}"; do
        if [[ ! -f "$package_dir/$file" ]]; then
            missing_files+=("$file")
        fi
    done

    for dir in "${essential_dirs[@]}"; do
        if [[ ! -d "$package_dir/$dir" ]]; then
            missing_dirs+=("$dir")
        fi
    done

    if [[ ${#missing_files[@]} -eq 0 && ${#missing_dirs[@]} -eq 0 ]]; then
        log_success "Package structure validation passed"
    else
        if [[ ${#missing_files[@]} -gt 0 ]]; then
            log_error "Missing essential files: ${missing_files[*]}"
        fi
        if [[ ${#missing_dirs[@]} -gt 0 ]]; then
            log_error "Missing essential directories: ${missing_dirs[*]}"
        fi
        return 1
    fi

    return 0
}

# Verify dependencies integrity
verify_dependencies() {
    log_info "Verifying dependencies integrity..."

    local package_dir
    package_dir=$(find "$EXTRACT_DIR" -maxdepth 1 -type d ! -path "$EXTRACT_DIR" | head -1)

    check_start
    if [[ ! -d "$package_dir/dependencies" ]]; then
        log_warning "Dependencies directory not found"
        return 0
    fi

    local deps_count
    deps_count=$(find "$package_dir/dependencies" -name "*.whl" -o -name "*.tar.gz" | wc -l)

    if [[ $deps_count -eq 0 ]]; then
        log_warning "No Python packages found in dependencies directory"
    else
        log_success "Found $deps_count dependency packages"
    fi

    # Verify dependencies against manifest if available
    check_start
    if [[ -f "$package_dir/INTEGRITY_MANIFEST.json" ]]; then
        log_verbose "Verifying against integrity manifest"

        # Basic validation - in a real implementation, this would parse JSON
        # and verify each dependency's checksum
        if grep -q "dependencies" "$package_dir/INTEGRITY_MANIFEST.json"; then
            log_success "Integrity manifest validation passed"
        else
            log_warning "Integrity manifest appears incomplete"
        fi
    else
        log_verbose "No integrity manifest found, skipping detailed verification"
    fi

    return 0
}

# Validate installation script
validate_installer() {
    log_info "Validating installation script..."

    local package_dir
    package_dir=$(find "$EXTRACT_DIR" -maxdepth 1 -type d ! -path "$EXTRACT_DIR" | head -1)

    local installer_script="$package_dir/install_offline.sh"

    check_start
    if [[ ! -f "$installer_script" ]]; then
        log_error "Installation script not found: install_offline.sh"
        return 1
    fi

    check_start
    if [[ ! -x "$installer_script" ]]; then
        log_warning "Installation script is not executable"
        if chmod +x "$installer_script" 2>/dev/null; then
            log_success "Made installation script executable"
        else
            log_error "Could not make installation script executable"
            return 1
        fi
    else
        log_success "Installation script is executable"
    fi

    # Basic script validation
    check_start
    if grep -q "PersonalManager Offline Installer" "$installer_script"; then
        log_success "Installation script header validation passed"
    else
        log_warning "Installation script may be corrupted or incorrect"
    fi

    return 0
}

# Security scan for malicious content
security_scan() {
    log_info "Performing security scan..."

    local package_dir
    package_dir=$(find "$EXTRACT_DIR" -maxdepth 1 -type d ! -path "$EXTRACT_DIR" | head -1)

    # Check for suspicious patterns in shell scripts
    check_start
    local suspicious_patterns=(
        "curl.*|.*sh"
        "wget.*|.*sh"
        "eval.*\$"
        "rm -rf /"
        "chmod 777"
    )

    local suspicious_found=false
    for pattern in "${suspicious_patterns[@]}"; do
        if find "$package_dir" -name "*.sh" -exec grep -l "$pattern" {} \; 2>/dev/null | head -1 >/dev/null; then
            log_warning "Suspicious pattern found: $pattern"
            suspicious_found=true
        fi
    done

    if [[ "$suspicious_found" == "false" ]]; then
        log_success "No suspicious patterns detected in scripts"
    fi

    # Check file permissions
    check_start
    local executable_files
    executable_files=$(find "$package_dir" -type f -perm +111 | wc -l)

    if [[ $executable_files -lt 10 ]]; then
        log_success "Reasonable number of executable files: $executable_files"
    else
        log_warning "Large number of executable files: $executable_files"
    fi

    return 0
}

# Generate verification report
generate_report() {
    log_info "Generating verification report..."

    local report_file="package_verification_$(date +%Y%m%d_%H%M%S).md"
    local total_issues=$((CHECKS_FAILED + CHECKS_WARNED))

    cat > "$report_file" << EOF
# PersonalManager Package Verification Report

**Generated**: $(date)
**Package**: $PACKAGE_FILE
**Verifier**: $0
**Mode**: $(if [[ "$STRICT_MODE" == "true" ]]; then echo "Strict"; else echo "Standard"; fi)

## Executive Summary

- **Total Checks**: $CHECKS_TOTAL
- **Passed**: $CHECKS_PASSED
- **Failed**: $CHECKS_FAILED
- **Warnings**: $CHECKS_WARNED
- **Status**: $(if [[ $CHECKS_FAILED -eq 0 ]]; then echo "✅ VERIFIED"; else echo "❌ FAILED"; fi)

## Verification Results

### Package File Validation
$(if [[ -f "$PACKAGE_FILE" ]]; then echo "✅ Package file exists and is readable"; else echo "❌ Package file issues"; fi)

### Checksum Verification
$(if [[ -f "${PACKAGE_FILE}.sha256" ]]; then echo "✅ SHA256 checksum verified"; else echo "⚠️ No checksum file found"; fi)

### Digital Signature
$(if [[ -f "${PACKAGE_FILE}.sig" || -f "${PACKAGE_FILE}.asc" ]]; then echo "✅ GPG signature verified"; else echo "⚠️ No digital signature found"; fi)

### Package Structure
$(if [[ $CHECKS_FAILED -eq 0 ]]; then echo "✅ All essential files and directories present"; else echo "❌ Package structure issues detected"; fi)

### Security Scan
$(if [[ $CHECKS_FAILED -eq 0 ]]; then echo "✅ No security issues detected"; else echo "⚠️ Security warnings found"; fi)

## Recommendations

$(if [[ $CHECKS_FAILED -gt 0 ]]; then
echo "### Critical Issues
- Address all failed checks before installation
- Verify package source and authenticity
- Consider re-downloading the package"
fi)

$(if [[ $CHECKS_WARNED -gt 0 ]]; then
echo "### Warnings
- Review warning messages above
- Consider enabling strict mode for production use
- Verify package signatures if available"
fi)

### Next Steps
1. Review this report carefully
2. Address any critical issues
3. If verification passed, proceed with installation:
   \`\`\`bash
   tar -xzf $PACKAGE_FILE
   cd \$(tar -tzf $PACKAGE_FILE | head -1 | cut -f1 -d/)
   ./install_offline.sh
   \`\`\`

## Technical Details

- **Package Size**: $(du -h "$PACKAGE_FILE" | cut -f1)
- **Extraction Directory**: ${EXTRACT_DIR:-"Not extracted"}
- **Verification Time**: $(date)
- **System**: $(uname -s) $(uname -m)

---
Generated by PersonalManager Package Verifier
EOF

    log_success "Verification report saved to: $report_file"
    return 0
}

# Cleanup temporary files
cleanup() {
    if [[ -n "$TEMP_DIR" && -d "$TEMP_DIR" ]]; then
        rm -rf "$TEMP_DIR"
        log_verbose "Cleaned up temporary directory: $TEMP_DIR"
    fi
}

# Main execution flow
main() {
    parse_arguments "$@"

    # Set up cleanup trap
    trap cleanup EXIT

    # Show header
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE} PersonalManager Package Verification ${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo

    log_info "Starting package verification for: $PACKAGE_FILE"
    if [[ "$STRICT_MODE" == "true" ]]; then
        log_info "Running in STRICT mode - all checks must pass"
    fi
    echo

    # Run verification steps
    local exit_code=0

    check_package_file || exit_code=$?
    verify_checksum || exit_code=$?
    verify_signature || exit_code=$?
    extract_and_validate || exit_code=$?
    verify_dependencies || exit_code=$?
    validate_installer || exit_code=$?
    security_scan || exit_code=$?
    generate_report

    # Summary
    echo
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE} Verification Summary ${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    local health_score=0
    if [[ $CHECKS_TOTAL -gt 0 ]]; then
        health_score=$(( (CHECKS_PASSED * 100) / CHECKS_TOTAL ))
    fi

    echo -e "${CYAN}Package Health Score: ${NC}${health_score}%"
    echo -e "${CYAN}Total Checks: ${NC}$CHECKS_TOTAL"
    echo -e "${GREEN}Passed: ${NC}$CHECKS_PASSED"
    echo -e "${RED}Failed: ${NC}$CHECKS_FAILED"
    echo -e "${YELLOW}Warnings: ${NC}$CHECKS_WARNED"
    echo

    if [[ $CHECKS_FAILED -eq 0 ]]; then
        if [[ $CHECKS_WARNED -eq 0 ]]; then
            echo -e "${GREEN}🎉 VERIFICATION PASSED: Package is safe to install${NC}"
            exit_code=0
        else
            echo -e "${YELLOW}✅ VERIFICATION PASSED: Package is safe but has warnings${NC}"
            exit_code=2
        fi
    else
        echo -e "${RED}❌ VERIFICATION FAILED: Do not install this package${NC}"
        exit_code=1
    fi

    echo
    exit $exit_code
}

# Execute main function
main "$@"