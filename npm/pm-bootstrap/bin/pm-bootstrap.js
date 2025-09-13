#!/usr/bin/env node

/**
 * PersonalManager Bootstrap Installer
 * One-line installer for PersonalManager with pipx priority and fallback strategies
 */

const { execSync, spawn } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');

const GITHUB_REPO = 'https://github.com/Sheldon-92/personalmanager.git';
const DEFAULT_VERSION = 'v0.1.0';

class PMBootstrap {
  constructor() {
    this.platform = os.platform();
    this.isWindows = this.platform === 'win32';
    this.version = DEFAULT_VERSION;
    this.source = 'release'; // 'release', 'git', 'test'
    this.verbose = false;
  }

  log(message, level = 'info') {
    const prefix = level === 'error' ? '❌' : level === 'warn' ? '⚠️' : level === 'success' ? '✅' : 'ℹ️';
    console.log(`${prefix} ${message}`);
  }

  async execCommand(command, options = {}) {
    try {
      if (this.verbose) {
        this.log(`Executing: ${command}`, 'info');
      }
      const result = execSync(command, { 
        encoding: 'utf8', 
        stdio: this.verbose ? 'inherit' : 'pipe',
        ...options 
      });
      return { success: true, output: result };
    } catch (error) {
      return { success: false, error: error.message, output: error.stdout };
    }
  }

  async checkCommand(command) {
    const result = await this.execCommand(`${command} --version`);
    return result.success;
  }

  async checkPython() {
    // Check Python 3.9+
    const pythonCommands = ['python3', 'python'];
    
    for (const cmd of pythonCommands) {
      if (await this.checkCommand(cmd)) {
        const versionResult = await this.execCommand(`${cmd} --version`);
        if (versionResult.success && versionResult.output) {
          const version = versionResult.output.match(/Python (\d+)\.(\d+)/);
          if (version) {
            const major = parseInt(version[1]);
            const minor = parseInt(version[2]);
            if (major === 3 && minor >= 9) {
              return { available: true, command: cmd, version: `${major}.${minor}` };
            }
          }
        }
      }
    }
    
    return { available: false };
  }

  async checkPipx() {
    if (await this.checkCommand('pipx')) {
      return { available: true, command: 'pipx' };
    }
    return { available: false };
  }

  async installPipx() {
    this.log('Installing pipx...', 'info');
    
    if (this.isWindows) {
      const result = await this.execCommand('python -m pip install --user pipx');
      if (result.success) {
        await this.execCommand('python -m pipx ensurepath');
        this.log('pipx installed. Please restart your terminal or run: python -m pipx ensurepath', 'warn');
        return true;
      }
    } else {
      // Try package manager first, then pip
      const managers = [
        { cmd: 'brew install pipx', check: 'brew --version' },
        { cmd: 'apt update && apt install -y pipx', check: 'apt --version' },
        { cmd: 'yum install -y pipx', check: 'yum --version' },
        { cmd: 'python3 -m pip install --user pipx', check: 'python3 --version' }
      ];

      for (const manager of managers) {
        if (await this.checkCommand(manager.check.split(' ')[0])) {
          const result = await this.execCommand(manager.cmd);
          if (result.success) {
            if (manager.cmd.includes('pip install')) {
              await this.execCommand('python3 -m pipx ensurepath');
              this.log('pipx installed. You may need to restart your terminal.', 'warn');
            }
            return true;
          }
        }
      }
    }
    
    return false;
  }

  async installPersonalManager() {
    this.log(`Installing PersonalManager ${this.version}...`, 'info');

    // Strategy 1: pipx with GitHub release wheel (preferred)
    if (this.source === 'release' || this.source === 'test') {
      const pipxResult = await this.checkPipx();
      
      if (!pipxResult.available) {
        this.log('pipx not found. Attempting to install pipx...', 'warn');
        const pipxInstalled = await this.installPipx();
        if (!pipxInstalled) {
          this.log('Failed to install pipx. Falling back to git installation.', 'warn');
          return this.installFromGit();
        }
      }

      // Try installing from GitHub release
      const releaseUrl = `git+${GITHUB_REPO}@${this.version}`;
      const installResult = await this.execCommand(`pipx install "${releaseUrl}"`);
      
      if (installResult.success) {
        this.log('PersonalManager installed successfully via pipx!', 'success');
        return true;
      } else {
        this.log('GitHub installation failed. Trying alternative methods...', 'warn');
        return this.installFromGit();
      }
    }

    return this.installFromGit();
  }

  async installFromGit() {
    this.log('Installing from Git repository...', 'info');
    
    const pipxResult = await this.checkPipx();
    const installCmd = pipxResult.available ? 'pipx install' : 'pip install --user';
    
    const gitUrl = `git+${GITHUB_REPO}@${this.version}`;
    const result = await this.execCommand(`${installCmd} "${gitUrl}"`);
    
    if (result.success) {
      this.log('PersonalManager installed successfully from Git!', 'success');
      return true;
    } else {
      this.log('Git installation failed.', 'error');
      this.showManualInstructions();
      return false;
    }
  }

  showManualInstructions() {
    this.log('\\nManual installation instructions:', 'warn');
    console.log(`
📋 Manual Installation Steps:

1. Ensure Python 3.9+ is installed:
   python3 --version

2. Install pipx (recommended):
   ${this.isWindows ? 
     'python -m pip install --user pipx && python -m pipx ensurepath' : 
     'python3 -m pip install --user pipx && python3 -m pipx ensurepath'
   }

3. Install PersonalManager:
   pipx install "git+${GITHUB_REPO}@${this.version}"

4. Verify installation:
   pm --version

Alternative (without pipx):
   ${this.isWindows ? 'python' : 'python3'} -m pip install --user "git+${GITHUB_REPO}@${this.version}"

For more help, visit: ${GITHUB_REPO}
`);
  }

  async verifyInstallation() {
    this.log('Verifying installation...', 'info');
    
    const commands = ['pm --version', 'pm --help'];
    
    for (const cmd of commands) {
      const result = await this.execCommand(cmd);
      if (!result.success) {
        this.log(`Verification failed: ${cmd}`, 'error');
        return false;
      }
    }
    
    this.log('Installation verified successfully!', 'success');
    this.log('\\n🎉 PersonalManager is ready to use!', 'success');
    this.log('\\nNext steps:', 'info');
    console.log(`
• Run 'pm setup' to initialize your system
• Run 'pm today' to get daily recommendations
• Run 'pm --help' to see all available commands

Happy productivity! 🚀
`);
    
    return true;
  }

  parseArgs() {
    const args = process.argv.slice(2);
    
    for (let i = 0; i < args.length; i++) {
      const arg = args[i];
      
      switch (arg) {
        case '--version':
          this.version = args[++i] || DEFAULT_VERSION;
          break;
        case '--source':
          this.source = args[++i] || 'release';
          break;
        case '--verbose':
        case '-v':
          this.verbose = true;
          break;
        case '--help':
        case '-h':
          this.showHelp();
          process.exit(0);
        default:
          if (arg.startsWith('-')) {
            this.log(`Unknown option: ${arg}`, 'error');
            process.exit(1);
          }
      }
    }
  }

  showHelp() {
    console.log(`
PersonalManager Bootstrap Installer v0.1.0

Usage: npx @personal-manager/pm-bootstrap [options]

Options:
  --version <version>    Install specific version (default: ${DEFAULT_VERSION})
  --source <source>      Installation source: release, git (default: release)
  --verbose, -v          Show detailed output
  --help, -h             Show this help message

Examples:
  npx @personal-manager/pm-bootstrap
  npx @personal-manager/pm-bootstrap --version v0.1.0
  npx @personal-manager/pm-bootstrap --source git --verbose

Repository: ${GITHUB_REPO}
`);
  }

  async checkEnvironment() {
    this.log('Checking environment...', 'info');
    
    // Check Node.js
    if (this.verbose) {
      this.log(`Node.js version: ${process.version}`, 'info');
      this.log(`Platform: ${this.platform}`, 'info');
    }
    
    // Check Python
    const pythonCheck = await this.checkPython();
    if (!pythonCheck.available) {
      this.log('Python 3.9+ is required but not found.', 'error');
      this.log('Please install Python 3.9+ and try again.', 'error');
      return false;
    }
    
    if (this.verbose) {
      this.log(`Python found: ${pythonCheck.command} ${pythonCheck.version}`, 'info');
    }
    
    return true;
  }

  async run() {
    try {
      console.log('🚀 PersonalManager Bootstrap Installer\\n');
      
      this.parseArgs();
      
      if (this.source === 'test') {
        this.log('Test mode - skipping actual installation', 'info');
        return;
      }
      
      const envOk = await this.checkEnvironment();
      if (!envOk) {
        process.exit(1);
      }
      
      const installed = await this.installPersonalManager();
      if (!installed) {
        process.exit(1);
      }
      
      const verified = await this.verifyInstallation();
      if (!verified) {
        process.exit(1);
      }
      
    } catch (error) {
      this.log(`Installation failed: ${error.message}`, 'error');
      this.showManualInstructions();
      process.exit(1);
    }
  }
}

// Run if called directly
if (require.main === module) {
  const installer = new PMBootstrap();
  installer.run();
}

module.exports = PMBootstrap;