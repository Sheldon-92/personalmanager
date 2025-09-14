"""CommandExecutor 测试套件"""

import pytest
import subprocess
from unittest.mock import Mock, patch, MagicMock
from pm.routing.command_executor import CommandExecutor, ExecutionResult


class TestCommandExecutor:
    """CommandExecutor 测试类"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.executor = CommandExecutor()
    
    def test_initialization(self):
        """测试初始化"""
        assert self.executor.safe_commands is not None
        assert len(self.executor.safe_commands) > 0
        assert self.executor.dangerous_patterns is not None
        assert len(self.executor.dangerous_patterns) > 0
    
    def test_safe_commands_loaded(self):
        """测试安全命令白名单加载"""
        expected_commands = [
            "pm", "pm help", "pm version", "pm capture", "pm inbox", 
            "pm today", "pm next", "pm projects", "pm habits"
        ]
        
        for cmd in expected_commands:
            assert cmd in self.executor.safe_commands
    
    def test_validate_route_result_valid(self):
        """测试有效路由结果验证"""
        valid_result = {
            "command": "pm help",
            "args": [],
            "confidence": 0.9
        }
        
        assert self.executor._validate_route_result(valid_result) is True
    
    def test_validate_route_result_invalid(self):
        """测试无效路由结果验证"""
        invalid_results = [
            {},  # 空字典
            {"args": []},  # 缺少command
            None,  # None值
        ]
        
        for invalid_result in invalid_results:
            assert self.executor._validate_route_result(invalid_result) is False
    
    def test_validate_command_safety_safe_commands(self):
        """测试安全命令验证"""
        safe_commands = [
            "pm help",
            "pm version",
            "pm capture test task",
            "pm inbox",
            "pm today --count 5"
        ]
        
        for cmd in safe_commands:
            assert self.executor._validate_command_safety(cmd) is True
    
    def test_validate_command_safety_dangerous_commands(self):
        """测试危险命令拦截"""
        dangerous_commands = [
            "rm -rf /",
            "pm capture test; rm file",
            "pm help | cat /etc/passwd",
            "pm capture `evil command`",
            "pm capture $(malicious)",
            "pm capture test > /etc/hosts",
            "sudo pm help",
            "python malicious.py",
            "curl http://evil.com"
        ]
        
        for cmd in dangerous_commands:
            assert self.executor._validate_command_safety(cmd) is False
    
    def test_extract_base_command(self):
        """测试基础命令提取"""
        test_cases = [
            ("pm help", "pm help"),
            ("pm capture task content", "pm capture"),
            ("pm projects overview", "pm projects"),
            ("help", "help"),
            ("", "")
        ]
        
        for input_cmd, expected in test_cases:
            result = self.executor._extract_base_command(input_cmd)
            assert result == expected
    
    def test_sanitize_argument(self):
        """测试参数清理"""
        test_cases = [
            ("normal text", "normal text"),
            ("text with `backticks`", "text with backticks"),
            ("text with $variables", "text with variables"),
            ("text; with; semicolons", "text with semicolons"),
            ("text & with & ampersands", "text  with  ampersands"),
            ("", ""),
        ]
        
        for input_arg, expected in test_cases:
            result = self.executor._sanitize_argument(input_arg)
            assert result == expected
    
    def test_dry_run_valid_command(self):
        """测试干运行 - 有效命令"""
        route_result = {
            "command": "pm help",
            "args": ["capture"],
            "confidence": 0.9
        }
        
        result = self.executor.dry_run(route_result)
        
        assert result["valid"] is True
        assert result["command"] == "pm help capture"
        assert result["base_command"] == "pm help"
        assert result["args"] == ["capture"]
    
    def test_dry_run_invalid_command(self):
        """测试干运行 - 无效命令"""
        route_result = {
            "command": "rm -rf",
            "args": ["/"],
            "confidence": 0.9
        }
        
        result = self.executor.dry_run(route_result)
        
        assert result["valid"] is False
        assert "安全策略阻止" in result["error"]
    
    def test_dry_run_invalid_format(self):
        """测试干运行 - 无效格式"""
        invalid_result = {"args": []}  # 缺少command
        
        result = self.executor.dry_run(invalid_result)
        
        assert result["valid"] is False
        assert "无效的路由结果格式" in result["error"]
    
    @patch('subprocess.run')
    def test_execute_safe_command_success(self, mock_run):
        """测试安全命令执行成功"""
        # 模拟成功的命令执行
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Command executed successfully"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        result = self.executor._execute_safe_command("pm help", ["capture"])
        
        assert result.status == "success"
        assert result.output == "Command executed successfully"
        assert result.command_executed == "pm help capture"
        assert result.exit_code == 0
    
    @patch('subprocess.run')
    def test_execute_safe_command_failure(self, mock_run):
        """测试安全命令执行失败"""
        # 模拟失败的命令执行
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Command failed"
        mock_run.return_value = mock_result
        
        result = self.executor._execute_safe_command("pm nonexistent", [])
        
        assert result.status == "error"
        assert result.exit_code == 1
        assert result.error_message == "Command failed"
    
    @patch('subprocess.run')
    def test_execute_safe_command_timeout(self, mock_run):
        """测试命令执行超时"""
        mock_run.side_effect = subprocess.TimeoutExpired("pm", 300)
        
        result = self.executor._execute_safe_command("pm long_command", [])
        
        assert result.status == "error"
        assert result.exit_code == 124
        assert "超时" in result.error_message
    
    @patch('subprocess.run')
    def test_execute_safe_command_not_found(self, mock_run):
        """测试命令未找到"""
        mock_run.side_effect = FileNotFoundError()
        
        result = self.executor._execute_safe_command("nonexistent_command", [])
        
        assert result.status == "error"
        assert result.exit_code == 127
        assert "未找到命令" in result.error_message
    
    def test_execute_valid_route_result(self):
        """测试执行有效路由结果"""
        route_result = {
            "command": "pm help",
            "args": [],
            "confidence": 0.9
        }
        
        with patch.object(self.executor, '_execute_safe_command') as mock_execute:
            mock_execute.return_value = ExecutionResult(
                status="success",
                output="Help displayed",
                command_executed="pm help"
            )
            
            result = self.executor.execute(route_result)
            
            assert result["status"] == "success"
            assert result["output"] == "Help displayed"
            assert result["command_executed"] == "pm help"
    
    def test_execute_invalid_route_result(self):
        """测试执行无效路由结果"""
        invalid_route_result = {"args": []}  # 缺少command
        
        result = self.executor.execute(invalid_route_result)
        
        assert result["status"] == "error"
        assert "无效的路由结果格式" in result["error_message"]
    
    def test_execute_dangerous_command(self):
        """测试执行危险命令被拦截"""
        dangerous_route_result = {
            "command": "rm -rf",
            "args": ["/"],
            "confidence": 0.9
        }
        
        result = self.executor.execute(dangerous_route_result)
        
        assert result["status"] == "error"
        assert "安全策略阻止" in result["error_message"]
    
    def test_should_confirm_high_confidence(self):
        """测试高置信度不需要确认"""
        assert self.executor._should_confirm(0.9) is False
        assert self.executor._should_confirm(0.8) is False
    
    def test_should_confirm_low_confidence(self):
        """测试低置信度需要确认"""
        assert self.executor._should_confirm(0.7) is True
        assert self.executor._should_confirm(0.5) is True
        assert self.executor._should_confirm(0.3) is True
    
    @patch('rich.prompt.Confirm.ask')
    def test_get_user_confirmation_low_confidence(self, mock_confirm):
        """测试低置信度确认提示"""
        mock_confirm.return_value = True
        
        result = self.executor._get_user_confirmation("pm help", "显示帮助", 0.3)
        
        assert result is True
        mock_confirm.assert_called_once_with("是否继续执行？", default=False)
    
    @patch('rich.prompt.Confirm.ask')
    def test_get_user_confirmation_medium_confidence(self, mock_confirm):
        """测试中等置信度确认提示"""
        mock_confirm.return_value = True
        
        result = self.executor._get_user_confirmation("pm help", "显示帮助", 0.6)
        
        assert result is True
        mock_confirm.assert_called_once_with("继续执行？", default=True)
    
    @patch('rich.prompt.Confirm.ask')
    def test_execute_with_confirmation_cancelled(self, mock_confirm):
        """测试用户取消执行"""
        mock_confirm.return_value = False
        
        route_result = {
            "command": "pm help",
            "args": [],
            "confidence": 0.5,
            "explanation": "显示帮助"
        }
        
        result = self.executor.execute_with_confirmation(route_result, skip_confirm=False)
        
        assert result["status"] == "cancelled"
        assert "用户取消执行" in result["error_message"]
    
    def test_execute_with_confirmation_skip_confirm(self):
        """测试跳过确认直接执行"""
        route_result = {
            "command": "pm help",
            "args": [],
            "confidence": 0.5,
            "explanation": "显示帮助"
        }
        
        with patch.object(self.executor, 'execute') as mock_execute:
            mock_execute.return_value = {"status": "success"}
            
            result = self.executor.execute_with_confirmation(route_result, skip_confirm=True)
            
            mock_execute.assert_called_once_with(route_result)


class TestExecutionResult:
    """ExecutionResult 测试类"""
    
    def test_execution_result_creation(self):
        """测试执行结果创建"""
        result = ExecutionResult(
            status="success",
            output="Command output",
            command_executed="pm help"
        )
        
        assert result.status == "success"
        assert result.output == "Command output"
        assert result.command_executed == "pm help"
        assert result.exit_code == 0  # 默认值
        assert result.error_message == ""  # 默认值
        assert result.duration == 0.0  # 默认值
    
    def test_execution_result_dict_conversion(self):
        """测试执行结果转字典"""
        result = ExecutionResult(
            status="error",
            output="",
            command_executed="pm invalid",
            exit_code=1,
            error_message="Command failed",
            duration=1.5
        )
        
        result_dict = result.__dict__
        
        assert result_dict["status"] == "error"
        assert result_dict["output"] == ""
        assert result_dict["command_executed"] == "pm invalid"
        assert result_dict["exit_code"] == 1
        assert result_dict["error_message"] == "Command failed"
        assert result_dict["duration"] == 1.5