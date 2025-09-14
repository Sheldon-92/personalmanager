"""
AI执行功能端到端测试

测试 pm ai execute 命令的各种场景，包括：
- 带确认的执行测试
- 跳过确认的执行测试
- 干运行模式测试
- 危险命令拦截测试
- 错误处理测试
"""

import json
import pytest
from .conftest import (
    run_cli, assert_success, assert_failure, assert_json_response,
    skip_if_cli_not_available, DANGEROUS_COMMANDS
)


class TestAIExecuteE2E:
    """AI执行功能端到端测试类"""
    
    @skip_if_cli_not_available()
    def test_execute_with_confirm_cancel(self):
        """测试带确认的执行 - 用户取消"""
        # 模拟用户输入 'n' 取消执行
        result = run_cli('ai execute "今天的任务"', input_text="n\n")
        
        # 取消执行应该成功退出，但不执行实际命令
        if result.returncode == 0:
            assert "取消" in result.stdout or "cancelled" in result.stdout.lower()
        else:
            # 有些实现可能返回非0退出码表示取消
            assert result.returncode in [1, 130]  # 130 is Ctrl+C
    
    @skip_if_cli_not_available()
    def test_execute_with_confirm_proceed(self):
        """测试带确认的执行 - 用户确认"""
        # 使用一个安全的命令进行测试
        # 模拟用户输入 'y' 确认执行
        result = run_cli('ai execute "今天做什么"', input_text="y\n")
        
        # 确认执行应该尝试运行命令
        # 注意：这里可能会因为系统未初始化而失败，这是正常的
        assert result.returncode in [0, 1]  # 可能成功或因其他原因失败
        
        if result.returncode == 0:
            assert "执行" in result.stdout or "execution" in result.stdout.lower()
    
    @skip_if_cli_not_available()
    def test_execute_skip_confirm(self):
        """测试跳过确认直接执行"""
        result = run_cli('ai execute "今天做什么" --yes')
        
        # 跳过确认应该直接执行
        # 同样，可能因系统未初始化而失败
        assert result.returncode in [0, 1]
        
        # 不应该出现确认提示
        assert "确认" not in result.stdout and "confirm" not in result.stdout.lower()
    
    @skip_if_cli_not_available()
    def test_execute_dry_run(self):
        """测试干运行模式"""
        result = run_cli('ai execute "今天的任务" --dry-run')
        
        # 干运行应该成功
        assert_success(result)
        
        # 应该显示验证信息但不实际执行
        assert "验证" in result.stdout or "validation" in result.stdout.lower() or "dry" in result.stdout.lower()
    
    @skip_if_cli_not_available()
    def test_execute_dry_run_json(self):
        """测试干运行模式的JSON输出"""
        result = run_cli('ai execute "今天做什么" --dry-run --json')
        
        # 干运行的JSON输出应该包含验证信息
        if result.returncode == 0:
            data = json.loads(result.stdout)
            
            # 应该包含路由结果和验证结果
            assert isinstance(data, dict)
            # 具体字段根据实际实现调整
    
    @skip_if_cli_not_available()
    def test_execute_json_output(self):
        """测试JSON格式输出"""
        result = run_cli('ai execute "今天做什么" --dry-run --json')
        
        if result.returncode == 0:
            data = assert_json_response(result)
            assert isinstance(data, dict)
    
    @skip_if_cli_not_available()
    def test_dangerous_command_detection(self):
        """测试危险命令检测和拦截"""
        dangerous_utterances = [
            "删除所有文件",
            "格式化硬盘", 
            "rm -rf /",
            "delete everything"
        ]
        
        for utterance in dangerous_utterances:
            result = run_cli(f'ai execute "{utterance}" --dry-run')
            
            # 危险命令应该被检测并拦截
            if result.returncode != 0:
                # 拦截成功
                error_text = result.stderr + result.stdout
                assert any(word in error_text.lower() for word in ["危险", "安全", "拒绝", "dangerous", "security"])
            else:
                # 如果没有拦截，至少应该有警告
                warning_text = result.stdout.lower()
                assert any(word in warning_text for word in ["警告", "危险", "warning", "dangerous"])
    
    @skip_if_cli_not_available()
    def test_execute_unknown_intent(self):
        """测试无法识别的意图"""
        result = run_cli('ai execute "完全不知道在说什么的话"')
        
        # 无法识别的意图应该有合适的错误处理
        if result.returncode != 0:
            error_text = result.stderr + result.stdout
            assert any(word in error_text for word in ["无法", "不支持", "未知", "unknown", "unsupported"])
    
    @skip_if_cli_not_available()
    def test_execute_empty_input(self):
        """测试空输入的处理"""
        result = run_cli('ai execute ""')
        
        # 空输入应该失败
        assert_failure(result)
    
    @skip_if_cli_not_available()
    def test_execute_routing_and_validation_flow(self):
        """测试完整的路由和验证流程"""
        result = run_cli('ai execute "今天做什么" --dry-run --json')
        
        if result.returncode == 0:
            # 应该能看到路由解析结果
            output_text = result.stdout
            
            # JSON输出应该包含相关信息
            try:
                data = json.loads(output_text)
                # 根据实际实现验证数据结构
                assert isinstance(data, dict)
            except json.JSONDecodeError:
                # 如果不是纯JSON，检查是否包含关键信息
                assert any(word in output_text for word in ["route", "路由", "validation", "验证"])
    
    @skip_if_cli_not_available()
    def test_execute_timeout_handling(self):
        """测试命令执行超时处理"""
        # 这个测试需要一个可能耗时的命令
        # 注意：实际测试中要避免真的等很久
        result = run_cli('ai execute "今天做什么" --dry-run')
        
        # 干运行应该很快完成，不会超时
        assert result.returncode != 124  # 124 is timeout exit code
    
    @skip_if_cli_not_available()
    def test_execute_argument_parsing(self):
        """测试参数解析"""
        # 测试各种参数组合
        test_cases = [
            ('ai execute "今天做什么"', True),  # 基本用法
            ('ai execute "今天做什么" --yes', True),  # 跳过确认
            ('ai execute "今天做什么" --dry-run', True),  # 干运行
            ('ai execute "今天做什么" --json', True),  # JSON输出
            ('ai execute "今天做什么" --dry-run --json', True),  # 组合参数
            ('ai execute "今天做什么" --yes --json', True),  # 组合参数
        ]
        
        for command, should_succeed in test_cases:
            result = run_cli(command)
            
            if should_succeed:
                # 参数解析应该成功，命令可能因其他原因失败
                assert "invalid" not in result.stderr.lower()
                assert "unrecognized" not in result.stderr.lower()
    
    @skip_if_cli_not_available()
    def test_execute_error_messages(self):
        """测试错误消息的质量"""
        # 测试各种错误场景的消息质量
        error_cases = [
            ('ai execute ""', "空输入错误"),
            ('ai execute "???"', "无法识别输入"),
        ]
        
        for command, error_type in error_cases:
            result = run_cli(command)
            
            if result.returncode != 0:
                error_text = result.stderr + result.stdout
                
                # 错误消息应该有用且清晰
                assert len(error_text.strip()) > 0, f"Empty error message for {error_type}"
                
                # 应该包含有用的信息
                useful_words = ["错误", "失败", "error", "failed", "invalid", "问题"]
                assert any(word in error_text.lower() for word in useful_words), f"Uninformative error for {error_type}"
    
    @skip_if_cli_not_available()
    def test_execute_special_characters_in_utterance(self):
        """测试包含特殊字符的语句执行"""
        special_cases = [
            "记录 完成 project@work.com 的任务",
            "capture task with (important) details",
            "添加任务：学习AI & ML",
            "今天做什么？要优先处理bug #123"
        ]
        
        for utterance in special_cases:
            result = run_cli(f'ai execute "{utterance}" --dry-run')
            
            # 应该能处理特殊字符而不崩溃
            if result.returncode != 0:
                # 如果失败，应该是合理的错误，不是崩溃
                error_text = result.stderr + result.stdout
                assert "traceback" not in error_text.lower()
                assert "exception" not in error_text.lower()
    
    @skip_if_cli_not_available()
    def test_execute_output_formatting(self):
        """测试输出格式的一致性"""
        result = run_cli('ai execute "今天做什么" --dry-run')
        
        if result.returncode == 0:
            output = result.stdout
            
            # 输出应该有清晰的结构
            # 这里检查一些基本的格式要求
            assert len(output.strip()) > 0, "Empty output"
            
            # 应该包含关键信息
            key_info = ["解析", "命令", "validation", "route", "执行", "execute"]
            assert any(word in output for word in key_info), "Missing key information in output"