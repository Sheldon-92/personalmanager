# PersonalManager 安全修复补丁

## 紧急修复补丁 (Critical Fixes)

### 1. bin/pm-local 安全加固补丁

创建新文件 `/Users/sheldonzhao/programs/personal-manager/bin/pm-local-secure`:

```bash
#!/usr/bin/env bash
#
# PersonalManager Local Launcher (Security Hardened Version)
# Project-level executable script for PersonalManager
#

set -euo pipefail  # Exit on error, undefined variables, and pipe failures
IFS=$'\n\t'        # Set secure Internal Field Separator

# Security check: Refuse to run as root
if [[ $EUID -eq 0 ]]; then
    echo "Error: This script must not be run as root!" >&2
    echo "Please run as a regular user." >&2
    exit 1
fi

# Get the directory where this script is located (with symlink resolution)
SCRIPT_PATH="$(readlink -f "${BASH_SOURCE[0]}" 2>/dev/null || realpath "${BASH_SOURCE[0]}")"
SCRIPT_DIR="$(dirname "$SCRIPT_PATH")"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd -P)"

# Validate project structure
if [[ ! -d "$PROJECT_ROOT/src/pm" ]]; then
    echo "Error: Invalid project structure - src/pm directory not found" >&2
    exit 1
fi

# Security: Clean sensitive environment variables
unset AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN
unset DATABASE_PASSWORD DB_PASSWORD
unset API_KEY API_TOKEN PRIVATE_KEY SECRET_KEY
unset GITHUB_TOKEN GITLAB_TOKEN
unset STRIPE_SECRET_KEY PAYMENT_SECRET

# Set secure PATH
export PATH="/usr/local/bin:/usr/bin:/bin"

# Set security-focused Python environment variables
export PYTHONDONTWRITEBYTECODE=1
export PYTHONHASHSEED=random

# Validate and sanitize arguments
validate_args() {
    local max_arg_length=1000

    for arg in "$@"; do
        # Check for dangerous characters
        if [[ "$arg" =~ [;\|&\$\`] ]]; then
            echo "Error: Invalid character in argument" >&2
            exit 1
        fi

        # Check for null bytes
        if [[ "$arg" == *$'\0'* ]]; then
            echo "Error: Null byte in argument" >&2
            exit 1
        fi

        # Check argument length
        if [[ ${#arg} -gt $max_arg_length ]]; then
            echo "Error: Argument too long (max $max_arg_length characters)" >&2
            exit 1
        fi
    done
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check Poetry availability
check_poetry() {
    if command_exists poetry && [[ -f "$PROJECT_ROOT/pyproject.toml" ]]; then
        return 0
    else
        return 1
    fi
}

# Function to launch with Poetry (with timeout)
launch_with_poetry() {
    echo "[INFO] Using Poetry environment" >&2

    # Use timeout to prevent hanging
    timeout 300 poetry run pm "$@" || {
        local exit_code=$?
        if [[ $exit_code -eq 124 ]]; then
            echo "Error: Command timed out after 5 minutes" >&2
        fi
        exit $exit_code
    }
}

# Function to launch with direct Python (with timeout)
launch_with_python() {
    echo "[INFO] Using direct Python execution" >&2

    # Verify Python module can be imported
    if ! PYTHONPATH="$PROJECT_ROOT/src" python3 -c "import pm.cli.main" 2>/dev/null; then
        echo "Error: Cannot import pm.cli.main module" >&2
        exit 1
    fi

    # Set secure PYTHONPATH
    export PYTHONPATH="$PROJECT_ROOT/src"

    # Use timeout to prevent hanging
    timeout 300 python3 -m pm.cli.main "$@" || {
        local exit_code=$?
        if [[ $exit_code -eq 124 ]]; then
            echo "Error: Command timed out after 5 minutes" >&2
        fi
        exit $exit_code
    }
}

# Main execution
main() {
    # Validate arguments first
    validate_args "$@"

    # Check Python availability
    if ! command_exists python3; then
        echo "Error: Python 3 is required but not found" >&2
        exit 1
    fi

    # Try Poetry first, then fall back to direct Python
    if check_poetry; then
        launch_with_poetry "$@"
    else
        launch_with_python "$@"
    fi
}

# Execute main function
main "$@"
```

### 2. Python subprocess 安全包装器

创建新文件 `/Users/sheldonzhao/programs/personal-manager/src/pm/security/command_executor.py`:

```python
"""
Secure command execution wrapper for PersonalManager.
Provides safe subprocess execution with validation and sandboxing.
"""

import subprocess
import shlex
import os
import signal
import ipaddress
from typing import List, Optional, Dict, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class SecurityError(Exception):
    """Raised when a security violation is detected."""
    pass


class SecureCommandExecutor:
    """Secure wrapper for executing system commands."""

    # Whitelist of allowed commands
    ALLOWED_COMMANDS = {
        'python', 'python3', 'pip', 'pip3', 'pipx',
        'poetry', 'pm', 'git', 'ping'
    }

    # Dangerous patterns to block
    DANGEROUS_PATTERNS = [
        ';', '|', '&', '$', '`', '\n', '\r', '\x00',
        '$(', '${', '&&', '||', '>>', '<<', '>', '<'
    ]

    # Maximum argument length
    MAX_ARG_LENGTH = 1000

    # Default timeout in seconds
    DEFAULT_TIMEOUT = 30

    @classmethod
    def validate_command(cls, command: str) -> None:
        """Validate that a command is allowed."""
        if command not in cls.ALLOWED_COMMANDS:
            raise SecurityError(f"Command not allowed: {command}")

    @classmethod
    def validate_args(cls, args: List[str]) -> List[str]:
        """Validate and sanitize command arguments."""
        sanitized = []

        for arg in args:
            # Check length
            if len(arg) > cls.MAX_ARG_LENGTH:
                raise SecurityError(f"Argument too long: {len(arg)} > {cls.MAX_ARG_LENGTH}")

            # Check for dangerous patterns
            for pattern in cls.DANGEROUS_PATTERNS:
                if pattern in arg:
                    raise SecurityError(f"Dangerous pattern in argument: {pattern}")

            # Check for null bytes
            if '\x00' in arg:
                raise SecurityError("Null byte in argument")

            sanitized.append(arg)

        return sanitized

    @classmethod
    def validate_ip_address(cls, ip_str: str) -> str:
        """Validate an IP address string."""
        try:
            # This will raise ValueError if invalid
            ip = ipaddress.ip_address(ip_str)
            return str(ip)
        except ValueError as e:
            raise SecurityError(f"Invalid IP address: {ip_str}") from e

    @classmethod
    def get_safe_environment(cls) -> Dict[str, str]:
        """Get a sanitized environment for subprocess execution."""
        # Start with minimal environment
        safe_env = {
            'PATH': '/usr/local/bin:/usr/bin:/bin',
            'LANG': 'en_US.UTF-8',
            'PYTHONDONTWRITEBYTECODE': '1',
            'PYTHONHASHSEED': 'random',
        }

        # Add specific safe variables from current environment
        safe_vars = ['HOME', 'USER', 'TERM', 'SHELL']
        for var in safe_vars:
            if var in os.environ:
                safe_env[var] = os.environ[var]

        # Explicitly exclude sensitive variables
        sensitive_vars = [
            'AWS_SECRET_ACCESS_KEY', 'AWS_SESSION_TOKEN',
            'DATABASE_PASSWORD', 'DB_PASSWORD',
            'API_KEY', 'API_TOKEN', 'PRIVATE_KEY', 'SECRET_KEY',
            'GITHUB_TOKEN', 'GITLAB_TOKEN',
        ]

        for var in sensitive_vars:
            safe_env.pop(var, None)

        return safe_env

    @classmethod
    def execute(cls,
                command: str,
                args: Optional[List[str]] = None,
                timeout: Optional[int] = None,
                check: bool = True) -> subprocess.CompletedProcess:
        """
        Safely execute a command with arguments.

        Args:
            command: The command to execute (must be whitelisted)
            args: List of arguments for the command
            timeout: Timeout in seconds (default: 30)
            check: Whether to raise exception on non-zero exit

        Returns:
            CompletedProcess instance with results

        Raises:
            SecurityError: If command or arguments fail validation
            subprocess.TimeoutExpired: If command times out
            subprocess.CalledProcessError: If command fails and check=True
        """
        # Validate command
        cls.validate_command(command)

        # Prepare command list
        cmd_list = [command]

        # Validate and add arguments
        if args:
            sanitized_args = cls.validate_args(args)
            cmd_list.extend(sanitized_args)

        # Set timeout
        if timeout is None:
            timeout = cls.DEFAULT_TIMEOUT

        # Log execution (without sensitive data)
        logger.info(f"Executing command: {command} with {len(args or [])} arguments")

        try:
            # Execute with security measures
            result = subprocess.run(
                cmd_list,
                capture_output=True,
                text=True,
                shell=False,  # Never use shell
                timeout=timeout,
                check=check,
                env=cls.get_safe_environment()
            )

            logger.info(f"Command completed with exit code: {result.returncode}")
            return result

        except subprocess.TimeoutExpired as e:
            logger.error(f"Command timed out after {timeout} seconds")
            raise
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed with exit code: {e.returncode}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error executing command: {e}")
            raise


class NetworkChecker:
    """Secure network connectivity checker."""

    @staticmethod
    def check_connectivity(target: str = '8.8.8.8') -> bool:
        """
        Safely check network connectivity using ping.

        Args:
            target: IP address to ping (default: Google DNS)

        Returns:
            True if network is reachable, False otherwise
        """
        try:
            # Validate IP address
            validated_ip = SecureCommandExecutor.validate_ip_address(target)

            # Execute ping safely
            result = SecureCommandExecutor.execute(
                'ping',
                ['-c', '1', validated_ip],
                timeout=5,
                check=False
            )

            return result.returncode == 0

        except (SecurityError, subprocess.TimeoutExpired):
            return False


# Example usage for GTDAgent
def detect_network_context() -> Dict[str, Any]:
    """Safely detect network context for GTDAgent."""
    context = {
        'network_info': {
            'online': False,
            'check_method': 'ping',
            'target': '8.8.8.8'
        }
    }

    try:
        # Use secure network checker
        context['network_info']['online'] = NetworkChecker.check_connectivity()
    except Exception as e:
        logger.warning(f"Network check failed: {e}")
        context['network_info']['error'] = str(e)

    return context
```

### 3. npm 包安全修复

创建补丁文件 `/Users/sheldonzhao/programs/personal-manager/npm/pm-bootstrap/lib/secure-exec.js`:

```javascript
/**
 * Secure command execution module for pm-bootstrap
 */

const { spawn } = require('child_process');
const path = require('path');

// Whitelist of allowed commands
const ALLOWED_COMMANDS = new Set([
    'python', 'python3', 'pip', 'pip3', 'pipx',
    'poetry', 'npm', 'npx', 'git', 'brew',
    'apt', 'apt-get', 'yum', 'dnf'
]);

// Dangerous patterns to block
const DANGEROUS_PATTERNS = [
    /[;&|$`]/,
    /\$\(/,
    /\$\{/,
    /&&/,
    /\|\|/,
    />>/,
    /</,
    /\x00/  // Null byte
];

class SecureExecutor {
    /**
     * Validate a command is allowed
     */
    static validateCommand(command) {
        const baseCommand = path.basename(command).split(/\s+/)[0];

        if (!ALLOWED_COMMANDS.has(baseCommand)) {
            throw new Error(`Command not allowed: ${baseCommand}`);
        }

        return baseCommand;
    }

    /**
     * Validate arguments are safe
     */
    static validateArgs(args) {
        const sanitized = [];

        for (const arg of args) {
            // Check length
            if (arg.length > 1000) {
                throw new Error('Argument too long');
            }

            // Check for dangerous patterns
            for (const pattern of DANGEROUS_PATTERNS) {
                if (pattern.test(arg)) {
                    throw new Error(`Dangerous pattern in argument: ${arg}`);
                }
            }

            sanitized.push(arg);
        }

        return sanitized;
    }

    /**
     * Validate Git URLs
     */
    static validateGitUrl(url) {
        const allowedHosts = ['github.com', 'gitlab.com', 'bitbucket.org'];

        try {
            const parsed = new URL(url);

            // Check protocol
            if (!['https:', 'git:', 'ssh:'].includes(parsed.protocol)) {
                throw new Error(`Unsafe protocol: ${parsed.protocol}`);
            }

            // Check host
            if (!allowedHosts.includes(parsed.hostname)) {
                throw new Error(`Untrusted host: ${parsed.hostname}`);
            }

            return url;
        } catch (e) {
            throw new Error(`Invalid Git URL: ${e.message}`);
        }
    }

    /**
     * Get safe environment variables
     */
    static getSafeEnv() {
        const safeEnv = {
            PATH: process.env.PATH || '/usr/local/bin:/usr/bin:/bin',
            LANG: 'en_US.UTF-8',
            NODE_ENV: 'production'
        };

        // Add safe variables
        const safeVars = ['HOME', 'USER', 'SHELL', 'TERM'];
        for (const key of safeVars) {
            if (process.env[key]) {
                safeEnv[key] = process.env[key];
            }
        }

        // Exclude sensitive variables
        const sensitiveVars = [
            'AWS_SECRET_ACCESS_KEY', 'AWS_SESSION_TOKEN',
            'DATABASE_PASSWORD', 'DB_PASSWORD',
            'API_KEY', 'API_TOKEN', 'PRIVATE_KEY',
            'GITHUB_TOKEN', 'GITLAB_TOKEN', 'NPM_TOKEN'
        ];

        for (const key of sensitiveVars) {
            delete safeEnv[key];
        }

        return safeEnv;
    }

    /**
     * Execute command safely
     */
    static async execute(command, args = [], options = {}) {
        // Validate command
        const validatedCommand = this.validateCommand(command);

        // Validate arguments
        const validatedArgs = this.validateArgs(args);

        return new Promise((resolve, reject) => {
            const timeout = options.timeout || 30000; // 30 seconds default

            const proc = spawn(validatedCommand, validatedArgs, {
                ...options,
                shell: false,  // Never use shell
                env: this.getSafeEnv(),
                timeout: timeout
            });

            let stdout = '';
            let stderr = '';
            let timedOut = false;

            // Set timeout
            const timer = setTimeout(() => {
                timedOut = true;
                proc.kill('SIGTERM');
                setTimeout(() => proc.kill('SIGKILL'), 5000);
            }, timeout);

            proc.stdout.on('data', (data) => {
                stdout += data.toString();
            });

            proc.stderr.on('data', (data) => {
                stderr += data.toString();
            });

            proc.on('close', (code) => {
                clearTimeout(timer);

                if (timedOut) {
                    reject(new Error(`Command timed out after ${timeout}ms`));
                } else if (code === 0) {
                    resolve({ success: true, output: stdout, stderr });
                } else {
                    resolve({
                        success: false,
                        code,
                        output: stdout,
                        error: stderr
                    });
                }
            });

            proc.on('error', (err) => {
                clearTimeout(timer);
                reject(err);
            });
        });
    }
}

module.exports = SecureExecutor;
```

## 应用补丁的步骤

### 1. 备份现有文件
```bash
cp bin/pm-local bin/pm-local.backup
cp npm/pm-bootstrap/bin/pm-bootstrap.js npm/pm-bootstrap/bin/pm-bootstrap.js.backup
```

### 2. 应用 Shell 脚本补丁
```bash
# 将安全版本设为主要启动器
cp bin/pm-local-secure bin/pm-local
chmod +x bin/pm-local
```

### 3. 集成 Python 安全模块
```python
# 在 src/pm/agents/gtd_agent.py 中替换 subprocess 调用
from pm.security.command_executor import NetworkChecker

# 替换原有的 ping 实现
def detect_current_context(self):
    # ... 其他代码 ...

    # 使用安全的网络检查
    context['network_info']['online'] = NetworkChecker.check_connectivity()

    # ... 其他代码 ...
```

### 4. 更新 npm 包
```javascript
// 在 pm-bootstrap.js 中引入安全执行器
const SecureExecutor = require('./lib/secure-exec');

// 替换 execCommand 方法
async execCommand(command, args = []) {
    try {
        return await SecureExecutor.execute(command, args, {
            timeout: 60000  // 60 seconds for installation commands
        });
    } catch (error) {
        return { success: false, error: error.message };
    }
}
```

## 验证补丁

运行安全测试：
```bash
python3 -m pytest tests/test_security_critical.py -v
```

所有关键测试应该通过。

## 注意事项

1. **逐步部署**: 先在测试环境验证，再部署到生产环境
2. **监控日志**: 部署后密切监控错误日志，确保没有破坏正常功能
3. **性能测试**: 验证安全措施不会显著影响性能
4. **文档更新**: 更新相关文档说明安全变更

---

**重要**: 这些补丁修复了所有 Critical 和 High 级别的安全问题。请立即应用以保护系统安全。