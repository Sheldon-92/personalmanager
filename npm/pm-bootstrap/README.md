# PersonalManager Bootstrap Installer

One-line installer for PersonalManager - AI-driven personal productivity system.

## Quick Start

```bash
# Install latest version
npx @personal-manager/pm-bootstrap

# Install specific version
npx @personal-manager/pm-bootstrap --version v0.1.0

# Verbose output
npx @personal-manager/pm-bootstrap --verbose
```

## What It Does

This installer automatically:

1. **Checks Environment**: Verifies Python 3.9+ is available
2. **Installs pipx**: Ensures isolated Python app installation (recommended)  
3. **Installs PersonalManager**: Downloads and installs from GitHub releases
4. **Verifies Installation**: Confirms `pm --version` and `pm --help` work
5. **Provides Next Steps**: Guides you through initial setup

## Installation Strategy

The installer uses a multi-tier approach for maximum compatibility:

### Tier 1: pipx + GitHub Release (Preferred)
- Uses `pipx` for isolated installation
- Downloads from GitHub release artifacts
- Clean, secure, and isolated

### Tier 2: pipx + Git Repository  
- Falls back to Git installation if release fails
- Still uses `pipx` for isolation
- Direct from source code

### Tier 3: pip + Git Repository
- Uses system `pip --user` if `pipx` unavailable
- Last resort for older systems
- Still functional but less isolated

### Manual Fallback
- Provides copy-pasteable commands if all automated methods fail
- Platform-specific instructions
- Link to documentation

## Platform Support

- ✅ **macOS**: Full automated support via Homebrew or pip
- ✅ **Linux**: Full automated support via apt/yum or pip
- ✅ **Windows**: Automated with manual PATH setup guidance
- ✅ **Unix-like**: Generic POSIX support

## Command Options

```bash
npx @personal-manager/pm-bootstrap [options]

Options:
  --version <version>    Install specific version (default: v0.1.0)
  --source <source>      Installation source: release, git (default: release)  
  --verbose, -v          Show detailed output
  --help, -h             Show help message
```

## Examples

```bash
# Basic installation
npx @personal-manager/pm-bootstrap

# Install specific version with verbose output
npx @personal-manager/pm-bootstrap --version v0.1.1 --verbose

# Force Git installation (bypass release artifacts)
npx @personal-manager/pm-bootstrap --source git

# Test mode (dry run without actual installation)
npx @personal-manager/pm-bootstrap --source test
```

## Prerequisites

- **Node.js 14+**: For running the installer itself
- **Python 3.9+**: Required for PersonalManager
- **Git**: Required for Git-based installation fallback
- **Internet Connection**: For downloading packages

## Troubleshooting

### Python Not Found
```bash
# macOS (Homebrew)
brew install python3

# Ubuntu/Debian  
sudo apt update && sudo apt install python3 python3-pip

# CentOS/RHEL
sudo yum install python3 python3-pip

# Windows
# Download from https://python.org
```

### pipx Installation Issues
```bash
# Manual pipx installation
python3 -m pip install --user pipx
python3 -m pipx ensurepath

# Restart terminal after installation
```

### Permission Issues
```bash
# Use --user flag for pip installations
python3 -m pip install --user "git+https://github.com/Sheldon-92/personalmanager.git@v0.1.0"
```

### Network/Firewall Issues
```bash
# Try direct Git clone + local installation
git clone https://github.com/Sheldon-92/personalmanager.git
cd personalmanager
git checkout v0.1.0
python3 -m pip install --user .
```

## Manual Installation

If the automated installer fails, you can install manually:

```bash
# 1. Verify Python
python3 --version  # Should be 3.9+

# 2. Install pipx (recommended)
python3 -m pip install --user pipx
python3 -m pipx ensurepath

# 3. Install PersonalManager
pipx install "git+https://github.com/Sheldon-92/personalmanager.git@v0.1.0"

# 4. Verify installation
pm --version
pm setup
```

## Security

- Downloads only from official GitHub repository
- Uses secure HTTPS connections
- Installs in user space (no admin privileges required)
- Source code is open and auditable

## Development

```bash
# Clone this repository
git clone https://github.com/Sheldon-92/personalmanager.git
cd personalmanager/npm/pm-bootstrap

# Test locally
node bin/pm-bootstrap.js --help

# Create package for testing
npm pack
npx personal-manager-pm-bootstrap-0.1.0.tgz
```

## Publishing

```bash
# Login to npm
npm login

# Publish to npm registry
npm publish --access public
```

## Support

- **Issues**: [GitHub Issues](https://github.com/Sheldon-92/personalmanager/issues)
- **Documentation**: [Project README](https://github.com/Sheldon-92/personalmanager)
- **Discussions**: [GitHub Discussions](https://github.com/Sheldon-92/personalmanager/discussions)

---

**Repository**: https://github.com/Sheldon-92/personalmanager  
**Package**: [@personal-manager/pm-bootstrap](https://www.npmjs.com/package/@personal-manager/pm-bootstrap)  
**License**: MIT