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

```bash
./install.sh --no-poetry --offline
```

### Custom Options

- `--dev`: Install development dependencies
- `--no-poetry`: Use pip instead of Poetry
- `--offline`: Skip online checks
- `--verbose`: Detailed output
- `--force`: Force reinstallation

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