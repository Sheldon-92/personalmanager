#!/bin/bash

# PersonalManager Installation Rollback Script
# Provides quick rollback capability for failed installations

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Configuration
BACKUP_BASE_DIR="${HOME}/.personalmanager/backups/installation"
VERBOSE=false
DRY_RUN=false
FORCE=false

usage() {
    cat << EOF
Usage: $0 [OPTIONS] [BACKUP_ID]

Roll back PersonalManager installation to a previous state

OPTIONS:
    --help              Show this help message
    --list              List available backups
    --verbose           Enable verbose output
    --dry-run           Show what would be done without executing
    --force             Force rollback without confirmation
    --latest            Rollback to the most recent backup

ARGUMENTS:
    BACKUP_ID           Specific backup ID to restore (optional)

EXAMPLES:
    $0 --list                    # List all available backups
    $0 --latest                  # Rollback to most recent backup
    $0 backup_20240314_143022    # Rollback to specific backup
    $0 --dry-run --latest        # Preview latest rollback

ROLLBACK PROCESS:
    1. Verify backup integrity
    2. Stop PersonalManager processes
    3. Create pre-rollback backup
    4. Restore files from backup
    5. Update configuration
    6. Verify installation

TARGET ROLLBACK TIME: ≤5 minutes

EOF
}

# Parse command line arguments
parse_arguments() {
    local list_only=false
    local use_latest=false
    local backup_id=""

    while [[ $# -gt 0 ]]; do
        case $1 in
            --help|-h)
                usage
                exit 0
                ;;
            --list)
                list_only=true
                shift
                ;;
            --verbose|-v)
                VERBOSE=true
                shift
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --force)
                FORCE=true
                shift
                ;;
            --latest)
                use_latest=true
                shift
                ;;
            -*)
                log_error "Unknown option: $1"
                usage
                exit 1
                ;;
            *)
                if [[ -z "$backup_id" ]]; then
                    backup_id="$1"
                    shift
                else
                    log_error "Multiple backup IDs specified"
                    exit 1
                fi
                ;;
        esac
    done

    if [[ "$list_only" == "true" ]]; then
        list_backups
        exit 0
    fi

    if [[ "$use_latest" == "true" ]]; then
        backup_id=$(get_latest_backup)
        if [[ -z "$backup_id" ]]; then
            log_error "No backups available"
            exit 1
        fi
    fi

    if [[ -z "$backup_id" ]]; then
        log_error "Backup ID required. Use --list to see available backups or --latest for most recent"
        exit 1
    fi

    echo "$backup_id"
}

# List available backups
list_backups() {
    log_info "Available installation backups:"
    echo

    if [[ ! -d "$BACKUP_BASE_DIR" ]]; then
        log_warning "No backup directory found: $BACKUP_BASE_DIR"
        return 0
    fi

    local backups_found=false

    for backup_dir in "$BACKUP_BASE_DIR"/backup_*; do
        if [[ ! -d "$backup_dir" ]]; then
            continue
        fi

        backups_found=true
        local backup_id
        backup_id=$(basename "$backup_dir")

        local backup_date
        local backup_size
        local backup_version=""

        # Extract date from backup ID (format: backup_YYYYMMDD_HHMMSS)
        if [[ "$backup_id" =~ backup_([0-9]{8})_([0-9]{6}) ]]; then
            local date_part="${BASH_REMATCH[1]}"
            local time_part="${BASH_REMATCH[2]}"
            backup_date="${date_part:0:4}-${date_part:4:2}-${date_part:6:2} ${time_part:0:2}:${time_part:2:2}:${time_part:4:2}"
        else
            backup_date="unknown"
        fi

        backup_size=$(du -sh "$backup_dir" 2>/dev/null | cut -f1 || echo "unknown")

        # Try to read version info
        if [[ -f "$backup_dir/backup_info.json" ]]; then
            backup_version=$(grep -o '"version":"[^"]*"' "$backup_dir/backup_info.json" 2>/dev/null | cut -d'"' -f4 || echo "")
        fi

        printf "  %-25s  %s  %8s  %s\n" "$backup_id" "$backup_date" "$backup_size" "${backup_version:+v$backup_version}"
    done

    if [[ "$backups_found" == "false" ]]; then
        log_warning "No backups found in $BACKUP_BASE_DIR"
    else
        echo
        log_info "Use backup ID with this script to rollback"
    fi
}

# Get the latest backup ID
get_latest_backup() {
    if [[ ! -d "$BACKUP_BASE_DIR" ]]; then
        return
    fi

    find "$BACKUP_BASE_DIR" -name "backup_*" -type d | sort -r | head -1 | xargs basename
}

# Verify backup integrity
verify_backup() {
    local backup_id="$1"
    local backup_dir="$BACKUP_BASE_DIR/$backup_id"

    log_info "Verifying backup integrity: $backup_id"

    if [[ ! -d "$backup_dir" ]]; then
        log_error "Backup directory not found: $backup_dir"
        return 1
    fi

    # Check backup info file
    local backup_info="$backup_dir/backup_info.json"
    if [[ ! -f "$backup_info" ]]; then
        log_warning "No backup info file found"
    else
        local backup_date
        backup_date=$(grep -o '"timestamp":"[^"]*"' "$backup_info" | cut -d'"' -f4)
        log_info "Backup created: $backup_date"
    fi

    # Check essential directories
    local required_dirs=("installation" "config")
    local missing_dirs=()

    for dir in "${required_dirs[@]}"; do
        if [[ ! -d "$backup_dir/$dir" ]]; then
            missing_dirs+=("$dir")
        fi
    done

    if [[ ${#missing_dirs[@]} -gt 0 ]]; then
        log_error "Backup incomplete - missing directories: ${missing_dirs[*]}"
        return 1
    fi

    log_success "Backup verification passed"
    return 0
}

# Create pre-rollback backup
create_pre_rollback_backup() {
    log_info "Creating pre-rollback backup..."

    local current_time
    current_time=$(date +"%Y%m%d_%H%M%S")
    local pre_rollback_backup_dir="$BACKUP_BASE_DIR/pre_rollback_$current_time"

    mkdir -p "$pre_rollback_backup_dir"

    # Backup current installation if it exists
    local install_dir="${HOME}/.personalmanager"
    if [[ -d "$install_dir" ]]; then
        if [[ "$DRY_RUN" == "false" ]]; then
            cp -r "$install_dir" "$pre_rollback_backup_dir/config/"
        fi
        log_info "Current configuration backed up to: pre_rollback_$current_time"
    fi

    return 0
}

# Stop PersonalManager processes
stop_pm_processes() {
    log_info "Stopping PersonalManager processes..."

    # Kill any running pm processes
    local pm_pids
    pm_pids=$(pgrep -f "pm-local" 2>/dev/null || true)

    if [[ -n "$pm_pids" ]]; then
        if [[ "$DRY_RUN" == "false" ]]; then
            echo "$pm_pids" | xargs -r kill 2>/dev/null || true
            sleep 2
            # Force kill if still running
            echo "$pm_pids" | xargs -r kill -9 2>/dev/null || true
        fi
        log_info "Stopped PersonalManager processes"
    else
        log_info "No PersonalManager processes found"
    fi
}

# Restore from backup
restore_from_backup() {
    local backup_id="$1"
    local backup_dir="$BACKUP_BASE_DIR/$backup_id"

    log_info "Restoring from backup: $backup_id"

    # Restore installation directory
    if [[ -d "$backup_dir/installation" ]]; then
        local install_target
        if [[ -f "$backup_dir/backup_info.json" ]]; then
            install_target=$(grep -o '"install_dir":"[^"]*"' "$backup_dir/backup_info.json" | cut -d'"' -f4)
        fi

        if [[ -z "$install_target" ]]; then
            install_target="${HOME}/.local/personalmanager"
        fi

        log_info "Restoring installation to: $install_target"

        if [[ "$DRY_RUN" == "false" ]]; then
            # Remove current installation
            if [[ -d "$install_target" ]]; then
                rm -rf "$install_target"
            fi

            # Restore from backup
            mkdir -p "$(dirname "$install_target")"
            cp -r "$backup_dir/installation" "$install_target"
        fi
    fi

    # Restore configuration
    if [[ -d "$backup_dir/config" ]]; then
        local config_target="${HOME}/.personalmanager"
        log_info "Restoring configuration to: $config_target"

        if [[ "$DRY_RUN" == "false" ]]; then
            if [[ -d "$config_target" ]]; then
                rm -rf "$config_target"
            fi

            mkdir -p "$(dirname "$config_target")"
            cp -r "$backup_dir/config" "$config_target"
        fi
    fi

    log_success "Restore completed"
}

# Update system launcher
update_launcher() {
    log_info "Updating system launcher..."

    local launcher_path="$HOME/.local/bin/pm"

    if [[ -f "$launcher_path" ]]; then
        if [[ "$DRY_RUN" == "false" ]]; then
            # Recreate launcher to point to restored installation
            local install_dir="${HOME}/.local/personalmanager"

            cat > "$launcher_path" << LAUNCHER_EOF
#!/bin/bash
# PersonalManager System Launcher (Restored)
INSTALL_DIR="$install_dir"
source "\$INSTALL_DIR/venv/bin/activate"
"\$INSTALL_DIR/bin/pm-local" "\$@"
LAUNCHER_EOF

            chmod +x "$launcher_path"
        fi

        log_success "System launcher updated"
    else
        log_info "No system launcher found, skipping"
    fi
}

# Verify restored installation
verify_installation() {
    log_info "Verifying restored installation..."

    local launcher_path="$HOME/.local/bin/pm"

    if [[ -f "$launcher_path" ]]; then
        if [[ "$DRY_RUN" == "false" ]]; then
            # Test launcher
            if timeout 10s "$launcher_path" --version &>/dev/null; then
                log_success "Installation verification passed"
            else
                log_warning "Installation verification failed - manual intervention may be required"
                return 1
            fi
        else
            log_info "[DRY RUN] Would verify installation"
        fi
    else
        log_warning "No launcher found - installation may be incomplete"
        return 1
    fi

    return 0
}

# Main rollback function
perform_rollback() {
    local backup_id="$1"
    local start_time
    start_time=$(date +%s)

    log_info "Starting rollback to: $backup_id"
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "DRY RUN MODE - No changes will be made"
    fi

    # Verify backup exists and is valid
    verify_backup "$backup_id" || exit 1

    # Confirmation unless forced
    if [[ "$FORCE" == "false" && "$DRY_RUN" == "false" ]]; then
        echo
        log_warning "This will replace your current PersonalManager installation with backup: $backup_id"
        read -p "Continue? (y/N): " -r
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Rollback cancelled by user"
            exit 0
        fi
    fi

    # Execute rollback steps
    create_pre_rollback_backup || exit 1
    stop_pm_processes
    restore_from_backup "$backup_id" || exit 1
    update_launcher
    verify_installation || exit 1

    local end_time
    end_time=$(date +%s)
    local duration=$((end_time - start_time))

    echo
    log_success "Rollback completed successfully in ${duration} seconds"

    if [[ $duration -le 300 ]]; then
        log_success "✅ Rollback time within 5-minute target"
    else
        log_warning "⚠️ Rollback exceeded 5-minute target (${duration}s)"
    fi

    echo
    log_info "Next steps:"
    log_info "1. Test basic functionality: pm --version"
    log_info "2. Run diagnostics: pm doctor"
    log_info "3. Verify your data: pm status"

    return 0
}

# Main execution
main() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE} PersonalManager Installation Rollback ${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    local backup_id
    backup_id=$(parse_arguments "$@")

    perform_rollback "$backup_id"
}

# Run main if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi