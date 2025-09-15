# PersonalManager Installation Guide

## Quick Start (5-10 minutes)

### One-Click Installation

```bash
# Clone the repository
git clone <repository-url>
cd personal-manager

# Run the one-click installer
./install.sh
```

### Manual Installation

```bash
# Install dependencies
poetry install
# or
pip install -e .

# Initialize configuration
./bin/pm-local setup

# Verify installation
./bin/pm-local doctor
```

## Installation Options

### Development Installation

```bash
./install.sh --dev --verbose
```

### Offline Installation

#### Method 1: Pre-built Offline Package (Recommended)

```bash
# Create offline package (requires internet initially)
bash scripts/package_offline.sh

# Transfer personalmanager-offline-v*.tar.gz to target system
# Extract and install (no internet required)
tar -xzf personalmanager-offline-v*.tar.gz
cd personalmanager-offline
./install_offline.sh

# Verify installation
pm doctor
```

#### Method 2: Online installer with offline mode

```bash
./install.sh --no-poetry --offline
```

### Custom Options

#### Online Installer Options
- `--dev`: Install development dependencies
- `--no-poetry`: Use pip instead of Poetry
- `--offline`: Skip online checks
- `--verbose`: Detailed output
- `--force`: Force reinstallation

#### Offline Packaging Options
```bash
# Create offline package with options
bash scripts/package_offline.sh [OPTIONS]

--help              Show help message
--output DIR        Output directory (default: ./dist)
--include-dev       Include development dependencies
--compress LEVEL    Compression level 1-9 (default: 6)
--platform          Target platform (auto-detect)
--verbose           Enable verbose output
--clean             Clean build directory before packaging
```

#### Offline Package Examples
```bash
# Basic offline package
bash scripts/package_offline.sh

# Include development dependencies
bash scripts/package_offline.sh --include-dev

# Custom output directory with maximum compression
bash scripts/package_offline.sh --output ~/packages --compress 9

# Clean build and verbose output
bash scripts/package_offline.sh --clean --verbose
```

## Offline Installation Deep Dive

### Creating Offline Packages

The offline packaging system creates self-contained installation packages that include all Python dependencies and can be installed on systems without internet connectivity.

#### Package Contents
- PersonalManager source code
- All Python dependencies (.whl and .tar.gz files)
- Self-contained installer script
- Documentation and configuration templates
- Version information and checksums

#### Package Creation Process
```bash
# Step 1: Create the offline package (requires internet)
cd personal-manager
bash scripts/package_offline.sh

# Output: dist/personalmanager-offline-v0.1.0.tar.gz
```

#### Transfer to Target System
```bash
# Copy to target system via USB, network share, etc.
scp dist/personalmanager-offline-v*.tar.gz user@target-system:/tmp/
```

### Offline Installation Process

#### Step 1: Extract Package
```bash
# On target system (no internet required)
cd /tmp
tar -xzf personalmanager-offline-v*.tar.gz
cd personalmanager-offline
```

#### Step 2: Run Installer
```bash
# Default installation to ~/.local/personalmanager
./install_offline.sh

# Custom installation directory
./install_offline.sh /opt/personalmanager
```

#### Step 3: Verify Installation
```bash
# Check installation health
pm doctor

# Quick system check
pm doctor --quick

# Test basic functionality
pm capture "Test task"
pm today
```

## System Diagnostics

### Basic Diagnostics

```bash
./bin/pm-local doctor
```

### Advanced Diagnostics

```bash
# Quick check (core components only)
./bin/pm-local doctor --quick

# Verbose output with system details
./bin/pm-local doctor --verbose

# Export detailed report
./bin/pm-local doctor --export diagnostic_report.md

# Auto-fix common issues
./bin/pm-local doctor --fix
```

### Diagnostic Commands

- `pm doctor` - Full system diagnostic
- `pm doctor check` - Alias for basic check
- `pm doctor fix` - Auto-repair system issues
- `pm doctor report` - Generate detailed report

## Installation Verification

### Automated Verification

```bash
./scripts/verify_installation.sh
```

### Verification Options

```bash
# Verbose output
./scripts/verify_installation.sh --verbose

# Show timing information
./scripts/verify_installation.sh --timing
```

## Platform Support

### macOS
- **Package Manager**: Homebrew (recommended)
- **Python**: System Python 3.9+ or Homebrew Python
- **Dependencies**: Xcode Command Line Tools

### Linux/Ubuntu
```bash
sudo apt update
sudo apt install python3.9+ python3-pip python3-venv git curl
```

### Windows (WSL)
```bash
# In WSL environment
sudo apt update
sudo apt install python3.9+ python3-pip python3-venv git curl
```

## Diagnostic Coverage

The enhanced `pm doctor` command checks:

### Core System
- ✅ Python version (3.9+)
- ✅ Required Python modules
- ✅ System commands (git, curl, package managers)
- ✅ Environment variables

### PersonalManager Specific
- ✅ Configuration initialization
- ✅ Data directories and permissions
- ✅ Launcher script functionality
- ✅ Required directory structure

### System Resources
- ✅ Disk space (>200MB)
- ✅ Memory availability (>500MB)
- ✅ Network connectivity
- ✅ File permissions

## Troubleshooting

### Common Issues

#### Permission Errors
```bash
chmod +x bin/pm-local
./bin/pm-local doctor --fix
```

#### Missing Dependencies
```bash
# For Poetry users
poetry install

# For pip users
pip install -e .
```

#### Network Issues
```bash
# Run in offline mode
./install.sh --offline
```

#### Python Version Issues
```bash
# Check Python version
python3 --version

# Install newer Python (macOS)
brew install python@3.11

# Install newer Python (Linux)
sudo apt install python3.11
```

### Getting Help

1. **Run diagnostics**: `./bin/pm-local doctor --verbose`
2. **Check logs**: Look in `~/.personalmanager/logs/`
3. **Generate report**: `./bin/pm-local doctor --export report.md`
4. **Verify installation**: `./scripts/verify_installation.sh --verbose`

## Performance Expectations

### Installation Time
- **Basic installation**: 2-5 minutes
- **Development installation**: 5-10 minutes
- **Full verification**: Under 1 minute

### System Requirements
- **Python**: 3.9 or later
- **Memory**: 500MB+ available
- **Disk**: 200MB+ free space
- **Network**: Optional (for full features)

## Post-Installation

### Complete Setup
```bash
./bin/pm-local setup
```

### Verify Everything Works
```bash
./bin/pm-local today
./bin/pm-local capture "My first task"
./bin/pm-local projects overview
```

### Enable Integrations (Optional)
```bash
# Google services
./bin/pm-local auth login

# Check privacy settings
./bin/pm-local privacy info
```

## Maintenance

### Regular Health Checks
```bash
# Weekly diagnostic
./bin/pm-local doctor

# Monthly full report
./bin/pm-local doctor --export monthly_report.md

# Clean up data
./bin/pm-local privacy cleanup
```

### Updates
```bash
git pull
poetry install  # or pip install -e .
./bin/pm-local doctor --fix
```

---

For more information, see:
- [User Guide](docs/user_guide.md)
- [README.md](README.md)
- [System Status](./bin/pm-local status)