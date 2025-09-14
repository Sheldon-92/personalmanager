"""
E2E测试辅助函数和配置

提供运行CLI命令的辅助函数，用于端到端测试。
"""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any
import pytest


def run_cli(command: str, input_text: Optional[str] = None, env: Optional[Dict[str, str]] = None) -> subprocess.CompletedProcess:
    """运行CLI命令的辅助函数
    
    Args:
        command: 要执行的CLI命令（不包含 'python -m pm.cli.main'）
        input_text: 模拟用户输入的文本
        env: 额外的环境变量
    
    Returns:
        subprocess.CompletedProcess: 命令执行结果
    """
    # 构建完整命令
    full_command = f"python3 -m pm.cli.main {command}"
    
    # 设置环境变量
    test_env = os.environ.copy()
    # 获取项目根目录
    project_root = Path(__file__).parent.parent.parent
    src_path = project_root / "src"
    test_env["PYTHONPATH"] = str(src_path)
    
    if env:
        test_env.update(env)
    
    try:
        # 执行命令
        result = subprocess.run(
            full_command,
            shell=True,
            capture_output=True,
            text=True,
            input=input_text,
            env=test_env,
            timeout=30  # 30秒超时
        )
        return result
    except subprocess.TimeoutExpired:
        # 超时处理
        return subprocess.CompletedProcess(
            full_command,
            returncode=124,  # timeout exit code
            stdout="",
            stderr="Command timed out after 30 seconds"
        )


def assert_success(result: subprocess.CompletedProcess, expected_output: Optional[str] = None) -> None:
    """断言命令执行成功
    
    Args:
        result: 命令执行结果
        expected_output: 期望的输出内容（可选）
    """
    assert result.returncode == 0, f"Command failed with exit code {result.returncode}. stderr: {result.stderr}"
    
    if expected_output:
        assert expected_output in result.stdout, f"Expected '{expected_output}' not found in stdout: {result.stdout}"


def assert_failure(result: subprocess.CompletedProcess, expected_error: Optional[str] = None) -> None:
    """断言命令执行失败
    
    Args:
        result: 命令执行结果
        expected_error: 期望的错误内容（可选）
    """
    assert result.returncode != 0, f"Command unexpectedly succeeded. stdout: {result.stdout}"
    
    if expected_error:
        error_text = result.stderr + result.stdout
        assert expected_error in error_text, f"Expected error '{expected_error}' not found in output: {error_text}"


def assert_json_response(result: subprocess.CompletedProcess, expected_fields: Optional[list] = None) -> Dict[str, Any]:
    """断言命令返回有效的JSON格式
    
    Args:
        result: 命令执行结果
        expected_fields: 期望存在的字段列表（可选）
    
    Returns:
        Dict[str, Any]: 解析后的JSON数据
    """
    assert result.returncode == 0, f"Command failed with exit code {result.returncode}. stderr: {result.stderr}"
    
    try:
        import json
        data = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        pytest.fail(f"Invalid JSON output: {e}. stdout: {result.stdout}")
    
    if expected_fields:
        for field in expected_fields:
            assert field in data, f"Expected field '{field}' not found in JSON response: {data}"
    
    return data


@pytest.fixture
def temp_project_dir():
    """创建临时项目目录用于测试"""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir) / "test_project"
        project_dir.mkdir()
        yield str(project_dir)


@pytest.fixture
def mock_home_dir():
    """创建模拟的用户主目录用于测试"""
    with tempfile.TemporaryDirectory() as tmpdir:
        home_dir = Path(tmpdir)
        pm_dir = home_dir / ".personalmanager"
        pm_dir.mkdir()
        
        # 设置环境变量
        old_home = os.environ.get('HOME')
        os.environ['HOME'] = str(home_dir)
        
        yield str(home_dir)
        
        # 恢复环境变量
        if old_home:
            os.environ['HOME'] = old_home
        else:
            del os.environ['HOME']


def is_cli_available() -> bool:
    """检查CLI是否可用"""
    try:
        result = run_cli("--version")
        return result.returncode == 0
    except Exception:
        return False


def skip_if_cli_not_available():
    """如果CLI不可用则跳过测试"""
    return pytest.mark.skipif(not is_cli_available(), reason="CLI not available")


# 常用测试数据
TEST_UTTERANCES = {
    "today": [
        "今天做什么",
        "今日重点",
        "今天的任务",
        "what should i do today"
    ],
    "capture": [
        "记录 完成项目文档",
        "添加任务 学习Python",
        "capture write unit tests",
        "记一下 买牛奶"
    ],
    "projects_overview": [
        "项目概览",
        "项目状态",
        "all projects",
        "overview projects"
    ],
    "project_status": [
        "PersonalManager项目进展",
        "前端重构 项目状态",
        "mobile app project status"
    ],
    "inbox": [
        "收件箱",
        "待处理",
        "inbox",
        "pending tasks"
    ]
}

# 危险命令测试数据
DANGEROUS_COMMANDS = [
    "rm -rf /",
    "sudo rm -rf /*",
    "format c:",
    "del /f /s /q c:\\*",
    "dd if=/dev/zero of=/dev/sda"
]