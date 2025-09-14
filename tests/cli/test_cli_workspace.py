"""测试工作空间和 Agent CLI 命令"""

import sys
import json
import subprocess
import tempfile
import shutil
from pathlib import Path
import pytest


class TestWorkspaceCLI:
    """测试 workspace CLI 命令"""

    def setup_method(self):
        """每个测试方法前创建临时目录"""
        self.temp_dir = tempfile.mkdtemp()
        self.root = Path(self.temp_dir)

    def teardown_method(self):
        """每个测试方法后清理临时目录"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def run_cli_command(self, args):
        """运行 CLI 命令并返回结果"""
        cmd = [sys.executable, '-m', 'pm.cli.main'] + args
        result = subprocess.run(
            cmd,
            cwd=self.root,
            capture_output=True,
            text=True,
            env={
                'PYTHONPATH': 'src',
                'HOME': str(self.root)  # 设置 HOME 避免沙箱环境 getpwuid 错误
            }
        )
        return result

    def test_workspace_init_help(self):
        """测试 workspace init 帮助信息"""
        result = self.run_cli_command(['workspace', 'init', '--help'])
        assert result.returncode == 0
        assert '初始化 AI 工作空间配置' in result.stdout
        assert '--force' in result.stdout
        assert '--root' in result.stdout

    def test_workspace_init_default(self):
        """测试默认初始化工作空间"""
        result = self.run_cli_command(['workspace', 'init'])
        assert result.returncode == 0
        assert '初始化成功' in result.stdout or '初始化完成' in result.stdout

        # 验证文件被创建
        workspace_dir = self.root / '.personalmanager'
        assert workspace_dir.exists()
        assert (workspace_dir / 'workspace-config.yaml').exists()
        assert (workspace_dir / 'ai-agent-definition.md').exists()
        assert (workspace_dir / 'interaction-patterns.json').exists()

    def test_workspace_init_idempotent(self):
        """测试幂等性：第二次运行不覆盖"""
        # 第一次初始化
        result1 = self.run_cli_command(['workspace', 'init'])
        assert result1.returncode == 0

        # 第二次初始化
        result2 = self.run_cli_command(['workspace', 'init'])
        assert result2.returncode == 0
        assert '跳过' in result2.stdout or '已存在' in result2.stdout

    def test_workspace_init_force(self):
        """测试强制覆盖模式"""
        # 第一次初始化
        result1 = self.run_cli_command(['workspace', 'init'])
        assert result1.returncode == 0

        # 修改一个文件
        config_file = self.root / '.personalmanager' / 'workspace-config.yaml'
        config_file.write_text('# Modified')

        # 强制覆盖
        result2 = self.run_cli_command(['workspace', 'init', '--force'])
        assert result2.returncode == 0
        assert '强制模式' in result2.stdout or '覆盖' in result2.stdout

        # 验证文件被覆盖
        content = config_file.read_text()
        assert '# Modified' not in content
        assert 'PersonalManager' in content

    def test_workspace_init_custom_root(self):
        """测试自定义根目录"""
        custom_dir = self.root / 'custom_project'
        custom_dir.mkdir()

        result = self.run_cli_command(['workspace', 'init', '--root', str(custom_dir)])
        assert result.returncode == 0

        # 验证文件在自定义目录中创建
        workspace_dir = custom_dir / '.personalmanager'
        assert workspace_dir.exists()
        assert (workspace_dir / 'workspace-config.yaml').exists()


class TestAgentStatusCLI:
    """测试 agent status CLI 命令"""

    def setup_method(self):
        """每个测试方法前创建临时目录"""
        self.temp_dir = tempfile.mkdtemp()
        self.root = Path(self.temp_dir)

    def teardown_method(self):
        """每个测试方法后清理临时目录"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def run_cli_command(self, args):
        """运行 CLI 命令并返回结果"""
        cmd = [sys.executable, '-m', 'pm.cli.main'] + args
        result = subprocess.run(
            cmd,
            cwd=self.root,
            capture_output=True,
            text=True,
            env={
                'PYTHONPATH': 'src',
                'HOME': str(self.root)  # 设置 HOME 避免沙箱环境 getpwuid 错误
            }
        )
        return result

    def test_agent_status_help(self):
        """测试 agent status 帮助信息"""
        result = self.run_cli_command(['agent', 'status', '--help'])
        assert result.returncode == 0
        assert '检查工作空间状态' in result.stdout
        assert '--json' in result.stdout
        assert '--root' in result.stdout
        assert '退出码' in result.stdout

    def test_agent_status_missing_workspace(self):
        """测试工作空间不存在时的状态检查"""
        result = self.run_cli_command(['agent', 'status'])
        assert result.returncode == 1  # 应该返回错误
        assert '错误' in result.stdout or 'ERROR' in result.stdout
        assert '.personalmanager' in result.stdout

    def test_agent_status_valid_workspace(self):
        """测试有效工作空间的状态检查"""
        # 先初始化工作空间
        init_result = self.run_cli_command(['workspace', 'init'])
        assert init_result.returncode == 0

        # 检查状态
        result = self.run_cli_command(['agent', 'status'])
        assert result.returncode == 0
        assert '检查通过' in result.stdout or '✅' in result.stdout
        assert '通过' in result.stdout

    def test_agent_status_json_mode(self):
        """测试 JSON 输出模式"""
        # 先初始化工作空间
        init_result = self.run_cli_command(['workspace', 'init'])
        assert init_result.returncode == 0

        # 以 JSON 模式检查状态
        result = self.run_cli_command(['agent', 'status', '--json'])
        assert result.returncode == 0

        # 解析 JSON
        try:
            data = json.loads(result.stdout)
            assert 'items' in data
            assert 'summary' in data
            assert isinstance(data['items'], list)
            assert isinstance(data['summary'], dict)
            assert 'ok' in data['summary']
            assert 'warn' in data['summary']
            assert 'error' in data['summary']
        except json.JSONDecodeError:
            pytest.fail(f"无法解析 JSON 输出: {result.stdout}")

    def test_agent_status_with_errors(self):
        """测试有错误的工作空间"""
        # 创建不完整的工作空间
        workspace_dir = self.root / '.personalmanager'
        workspace_dir.mkdir()

        # 创建语法错误的 YAML 文件
        config_file = workspace_dir / 'workspace-config.yaml'
        config_file.write_text("""
workspace:
  name: test
  invalid yaml syntax
    - wrong indentation
""")

        # 检查状态
        result = self.run_cli_command(['agent', 'status'])
        assert result.returncode == 1  # 有错误应该返回 1
        assert '错误' in result.stdout or 'ERROR' in result.stdout or '❌' in result.stdout

    def test_agent_status_json_with_errors(self):
        """测试 JSON 模式下的错误报告"""
        # 创建不完整的工作空间
        workspace_dir = self.root / '.personalmanager'
        workspace_dir.mkdir()

        # 以 JSON 模式检查状态
        result = self.run_cli_command(['agent', 'status', '--json'])
        assert result.returncode == 1

        # 解析 JSON
        try:
            data = json.loads(result.stdout)
            assert data['summary']['error'] > 0
        except json.JSONDecodeError:
            pytest.fail(f"无法解析 JSON 输出: {result.stdout}")

    def test_agent_status_custom_root(self):
        """测试自定义根目录的状态检查"""
        custom_dir = self.root / 'custom_project'
        custom_dir.mkdir()

        # 在自定义目录初始化
        init_result = self.run_cli_command(['workspace', 'init', '--root', str(custom_dir)])
        assert init_result.returncode == 0

        # 检查自定义目录的状态
        result = self.run_cli_command(['agent', 'status', '--root', str(custom_dir)])
        assert result.returncode == 0
        assert '检查通过' in result.stdout or '✅' in result.stdout

    def test_exit_codes(self):
        """测试退出码语义"""
        # 无工作空间 -> 退出码 1
        result1 = self.run_cli_command(['agent', 'status'])
        assert result1.returncode == 1

        # 初始化工作空间
        init_result = self.run_cli_command(['workspace', 'init'])
        assert init_result.returncode == 0

        # 有效工作空间 -> 退出码 0
        result2 = self.run_cli_command(['agent', 'status'])
        assert result2.returncode == 0

        # 创建带警告的配置（文件过大）
        patterns_file = self.root / '.personalmanager' / 'interaction-patterns.json'
        large_content = json.dumps({
            "version": "1.0",
            "locale": ["zh", "en"],
            "intents": [{"id": f"intent_{i}", "phrases": ["test"] * 100} for i in range(2000)]
        })
        patterns_file.write_text(large_content)

        # 仅有警告 -> 退出码仍为 0
        result3 = self.run_cli_command(['agent', 'status'])
        assert result3.returncode == 0  # 警告不影响退出码


class TestCLIIntegration:
    """测试 CLI 命令集成"""

    def setup_method(self):
        """每个测试方法前创建临时目录"""
        self.temp_dir = tempfile.mkdtemp()
        self.root = Path(self.temp_dir)

    def teardown_method(self):
        """每个测试方法后清理临时目录"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def run_cli_command(self, args):
        """运行 CLI 命令并返回结果"""
        cmd = [sys.executable, '-m', 'pm.cli.main'] + args
        result = subprocess.run(
            cmd,
            cwd=self.root,
            capture_output=True,
            text=True,
            env={
                'PYTHONPATH': 'src',
                'HOME': str(self.root)  # 设置 HOME 避免沙箱环境 getpwuid 错误
            }
        )
        return result

    def test_complete_workflow(self):
        """测试完整的工作流程"""
        # 1. 初始化工作空间
        init_result = self.run_cli_command(['workspace', 'init'])
        assert init_result.returncode == 0

        # 2. 检查状态（人类可读）
        status_result = self.run_cli_command(['agent', 'status'])
        assert status_result.returncode == 0
        assert '检查通过' in status_result.stdout or '✅' in status_result.stdout

        # 3. 检查状态（JSON）
        json_result = self.run_cli_command(['agent', 'status', '--json'])
        assert json_result.returncode == 0
        data = json.loads(json_result.stdout)
        assert data['summary']['error'] == 0

        # 4. 再次初始化（测试幂等性）
        init_result2 = self.run_cli_command(['workspace', 'init'])
        assert init_result2.returncode == 0
        assert '跳过' in init_result2.stdout or '已存在' in init_result2.stdout

        # 5. 强制重新初始化
        force_result = self.run_cli_command(['workspace', 'init', '--force'])
        assert force_result.returncode == 0
        assert '创建' in force_result.stdout or '成功' in force_result.stdout