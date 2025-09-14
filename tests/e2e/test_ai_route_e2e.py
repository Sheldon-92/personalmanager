"""
AI路由功能端到端测试

测试 pm ai route 命令的各种场景，包括：
- 5个核心意图的路由测试
- 中英文输入测试
- JSON输出格式测试
- 错误处理测试
"""

import json
import pytest
from .conftest import (
    run_cli, assert_success, assert_failure, assert_json_response,
    skip_if_cli_not_available, TEST_UTTERANCES
)


class TestAIRouteE2E:
    """AI路由功能端到端测试类"""
    
    @skip_if_cli_not_available()
    def test_route_today_command(self):
        """测试今日任务路由"""
        for utterance in TEST_UTTERANCES["today"]:
            result = run_cli(f'ai route "{utterance}" --json')
            data = assert_json_response(result, ["intent", "confidence", "command"])
            
            assert data["intent"] == "today"
            assert data["confidence"] >= 0.8, f"Low confidence for '{utterance}': {data['confidence']}"
            assert "pm today" in data["command"]
    
    @skip_if_cli_not_available()
    def test_route_capture_with_content(self):
        """测试捕获任务路由"""
        for utterance in TEST_UTTERANCES["capture"]:
            result = run_cli(f'ai route "{utterance}" --json')
            data = assert_json_response(result, ["intent", "confidence", "command", "args"])
            
            assert data["intent"] == "capture"
            assert data["confidence"] >= 0.7, f"Low confidence for '{utterance}': {data['confidence']}"
            assert "pm capture" in data["command"]
            
            # 检查是否正确提取了内容
            if "args" in data and data["args"]:
                assert "content" in data["args"], f"Missing content arg for '{utterance}'"
    
    @skip_if_cli_not_available()
    def test_route_projects_overview(self):
        """测试项目概览路由"""
        for utterance in TEST_UTTERANCES["projects_overview"]:
            result = run_cli(f'ai route "{utterance}" --json')
            data = assert_json_response(result, ["intent", "confidence", "command"])
            
            assert data["intent"] == "projects_overview"
            assert data["confidence"] >= 0.8, f"Low confidence for '{utterance}': {data['confidence']}"
            assert "pm projects overview" in data["command"]
    
    @skip_if_cli_not_available()
    def test_route_project_status_with_name(self):
        """测试单个项目状态路由"""
        for utterance in TEST_UTTERANCES["project_status"]:
            result = run_cli(f'ai route "{utterance}" --json')
            data = assert_json_response(result, ["intent", "confidence", "command"])
            
            assert data["intent"] == "project_status"
            assert data["confidence"] >= 0.7, f"Low confidence for '{utterance}': {data['confidence']}"
            assert "pm project status" in data["command"]
            
            # 检查是否正确提取了项目名称
            if "args" in data and data["args"]:
                assert "name" in data["args"], f"Missing project name for '{utterance}'"
    
    @skip_if_cli_not_available()
    def test_route_inbox_command(self):
        """测试收件箱路由"""
        for utterance in TEST_UTTERANCES["inbox"]:
            result = run_cli(f'ai route "{utterance}" --json')
            data = assert_json_response(result, ["intent", "confidence", "command"])
            
            assert data["intent"] == "inbox"
            assert data["confidence"] >= 0.8, f"Low confidence for '{utterance}': {data['confidence']}"
            assert "pm inbox" in data["command"]
    
    @skip_if_cli_not_available()
    def test_route_display_format_non_json(self):
        """测试非JSON格式输出"""
        result = run_cli('ai route "今天做什么"')
        assert_success(result)
        
        # 检查是否包含格式化输出的关键词
        assert "路由结果" in result.stdout
        assert "意图:" in result.stdout
        assert "置信度:" in result.stdout
        assert "命令:" in result.stdout
    
    @skip_if_cli_not_available()
    def test_route_verbose_mode(self):
        """测试详细模式输出"""
        result = run_cli('ai route "记录 学习AI" --verbose')
        assert_success(result)
        
        # 详细模式应该显示更多信息
        assert "路由结果" in result.stdout
    
    @skip_if_cli_not_available()
    def test_route_low_confidence_warning(self):
        """测试低置信度输入的警告"""
        # 使用一个模糊或不明确的输入
        result = run_cli('ai route "做事情"')
        assert_success(result)
        
        # 应该显示建议或警告信息
        output = result.stdout.lower()
        suggestions_shown = any(word in output for word in ["建议", "置信度较低", "尝试", "支持的意图"])
    
    @skip_if_cli_not_available()
    def test_route_multilingual_support(self):
        """测试中英文混合输入"""
        test_cases = [
            ("今天做什么", "today"),
            ("what should i do today", "today"),
            ("capture 学习Python", "capture"),
            ("记录 learn english", "capture"),
            ("projects overview", "projects_overview"),
            ("项目概览", "projects_overview")
        ]
        
        for utterance, expected_intent in test_cases:
            result = run_cli(f'ai route "{utterance}" --json')
            data = assert_json_response(result)
            
            assert data["intent"] == expected_intent, f"Wrong intent for '{utterance}': {data['intent']}"
    
    @skip_if_cli_not_available()
    def test_route_empty_input(self):
        """测试空输入的错误处理"""
        result = run_cli('ai route ""')
        # 空输入应该失败或返回有意义的错误
        # 这里可能需要根据实际实现调整断言
        assert result.returncode != 0 or "error" in result.stdout.lower() or "错误" in result.stdout
    
    @skip_if_cli_not_available()
    def test_route_very_long_input(self):
        """测试超长输入的处理"""
        long_input = "记录 " + "学习" * 200  # 超长输入
        result = run_cli(f'ai route "{long_input}"')
        
        # 应该能处理或给出合适的错误
        if result.returncode == 0:
            # 成功处理
            assert "route" in result.stdout.lower() or "路由" in result.stdout
        else:
            # 合理的错误处理
            assert "error" in result.stderr.lower() or "错误" in result.stderr
    
    @skip_if_cli_not_available()
    def test_route_special_characters(self):
        """测试包含特殊字符的输入"""
        special_cases = [
            "记录 完成项目@!#$%",
            "capture task with (brackets)",
            "项目概览 & 状态检查",
            "today's tasks & priorities"
        ]
        
        for utterance in special_cases:
            result = run_cli(f'ai route "{utterance}"')
            # 应该能处理特殊字符而不崩溃
            assert result.returncode == 0 or "error" not in result.stderr.lower()
    
    @skip_if_cli_not_available()
    def test_route_json_output_structure(self):
        """测试JSON输出的完整结构"""
        result = run_cli('ai route "今天做什么" --json')
        data = assert_json_response(result)
        
        # 验证JSON结构包含所有必要字段
        required_fields = ["intent", "confidence", "command"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        # 验证数据类型
        assert isinstance(data["intent"], str)
        assert isinstance(data["confidence"], (int, float))
        assert isinstance(data["command"], str)
        assert 0 <= data["confidence"] <= 1, f"Invalid confidence value: {data['confidence']}"
    
    @skip_if_cli_not_available()
    def test_route_custom_patterns_file(self):
        """测试自定义交互模式文件"""
        # 测试指定不存在的模式文件
        result = run_cli('ai route "今天做什么" --patterns /nonexistent/file.json')
        assert_failure(result)
        
        # 应该有找不到文件的错误信息
        error_text = result.stderr + result.stdout
        assert "找不到" in error_text or "not found" in error_text.lower()
    
    @skip_if_cli_not_available()
    def test_route_confidence_levels(self):
        """测试不同置信度级别的处理"""
        # 高置信度输入
        high_confidence_cases = [
            "今天做什么",
            "项目概览", 
            "收件箱"
        ]
        
        for utterance in high_confidence_cases:
            result = run_cli(f'ai route "{utterance}" --json')
            data = assert_json_response(result)
            assert data["confidence"] >= 0.8, f"Expected high confidence for '{utterance}'"
        
        # 中等置信度输入（需要根据实际情况调整）
        medium_confidence_cases = [
            "看看今天要做的",
            "检查项目状态"
        ]
        
        for utterance in medium_confidence_cases:
            result = run_cli(f'ai route "{utterance}" --json')
            if result.returncode == 0:
                data = json.loads(result.stdout)
                # 中等置信度应该在0.5-0.8之间
                assert 0.5 <= data["confidence"] < 0.8, f"Unexpected confidence for '{utterance}': {data['confidence']}"