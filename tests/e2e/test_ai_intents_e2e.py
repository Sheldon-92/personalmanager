"""
AI意图列表功能端到端测试

测试 pm ai intents 命令的各种场景，包括：
- 列出所有支持的意图
- 验证核心意图的存在
- 测试输出格式
- 自定义模式文件测试
"""

import pytest
from .conftest import (
    run_cli, assert_success, assert_failure,
    skip_if_cli_not_available
)


class TestAIIntentsE2E:
    """AI意图列表功能端到端测试类"""
    
    @skip_if_cli_not_available()
    def test_list_intents_basic(self):
        """测试基本的意图列表功能"""
        result = run_cli("ai intents")
        assert_success(result)
        
        # 检查是否显示了支持的意图列表标题
        assert "支持的意图" in result.stdout or "intents" in result.stdout.lower()
    
    @skip_if_cli_not_available()
    def test_list_intents_core_intents_present(self):
        """测试核心意图是否都在列表中"""
        result = run_cli("ai intents")
        assert_success(result)
        
        # 检查5个核心意图是否都存在
        core_intents = [
            "today",
            "capture", 
            "projects_overview",
            "project_status",
            "inbox"
        ]
        
        for intent in core_intents:
            assert intent in result.stdout, f"Core intent '{intent}' not found in output"
    
    @skip_if_cli_not_available()
    def test_list_intents_with_descriptions(self):
        """测试意图列表是否包含描述"""
        result = run_cli("ai intents")
        assert_success(result)
        
        # 检查是否有描述性信息
        # 描述通常包含中文或英文说明
        descriptions_found = 0
        lines = result.stdout.split('\n')
        
        for line in lines:
            if any(intent in line for intent in ["today", "capture", "projects", "inbox"]):
                # 这一行包含意图，检查是否也有描述
                if any(desc_word in line for desc_word in ["获取", "记录", "项目", "收件箱", "task", "project", "inbox"]):
                    descriptions_found += 1
        
        assert descriptions_found > 0, "No descriptions found for intents"
    
    @skip_if_cli_not_available()
    def test_list_intents_output_format(self):
        """测试输出格式的一致性"""
        result = run_cli("ai intents")
        assert_success(result)
        
        lines = result.stdout.split('\n')
        intent_lines = [line for line in lines if line.strip() and ('•' in line or '*' in line or line.startswith(' '))]
        
        # 应该有多个意图行
        assert len(intent_lines) >= 5, f"Expected at least 5 intent lines, got {len(intent_lines)}"
        
        # 检查格式一致性
        for line in intent_lines[:3]:  # 检查前几行
            # 每行应该包含意图ID
            assert any(intent in line for intent in ["today", "capture", "projects", "inbox", "explain"]), f"No intent ID found in line: {line}"
    
    @skip_if_cli_not_available()
    def test_list_intents_custom_patterns_file_not_found(self):
        """测试指定不存在的模式文件"""
        result = run_cli("ai intents --patterns /nonexistent/patterns.json")
        assert_failure(result)
        
        # 应该有文件不存在的错误信息
        error_text = result.stderr + result.stdout
        assert any(word in error_text.lower() for word in ["找不到", "不存在", "not found", "no such file"]), "Missing file error not properly reported"
    
    @skip_if_cli_not_available()
    def test_list_intents_help_information(self):
        """测试帮助信息"""
        # 测试help输出
        result = run_cli("ai intents --help")
        assert_success(result)
        
        # 应该包含命令说明
        help_text = result.stdout.lower()
        assert any(word in help_text for word in ["intents", "意图", "list", "列出"]), "Help text missing key information"
    
    @skip_if_cli_not_available()
    def test_list_intents_comprehensive_coverage(self):
        """测试是否涵盖了所有预期的意图类别"""
        result = run_cli("ai intents")
        assert_success(result)
        
        # 检查不同类别的意图都有涵盖
        intent_categories = {
            "时间管理": ["today"],
            "任务管理": ["capture", "inbox"],
            "项目管理": ["projects_overview", "project_status"],
            "系统功能": ["explain"]
        }
        
        found_categories = 0
        for category, intents in intent_categories.items():
            if any(intent in result.stdout for intent in intents):
                found_categories += 1
        
        assert found_categories >= 3, f"Only found {found_categories} out of {len(intent_categories)} intent categories"
    
    @skip_if_cli_not_available()
    def test_list_intents_no_errors_or_warnings(self):
        """测试命令执行没有错误或警告"""
        result = run_cli("ai intents")
        assert_success(result)
        
        # 检查stderr是否为空或只包含无害信息
        if result.stderr.strip():
            # 如果有stderr输出，应该不是错误
            stderr_lower = result.stderr.lower()
            error_indicators = ["error", "exception", "traceback", "failed", "错误", "异常", "失败"]
            
            for indicator in error_indicators:
                assert indicator not in stderr_lower, f"Found error indicator '{indicator}' in stderr: {result.stderr}"
    
    @skip_if_cli_not_available()
    def test_list_intents_output_length(self):
        """测试输出长度合理性"""
        result = run_cli("ai intents")
        assert_success(result)
        
        # 输出不应该太短或太长
        output_length = len(result.stdout)
        assert 100 < output_length < 5000, f"Output length {output_length} seems unreasonable"
        
        # 应该有合理数量的行
        lines = [line for line in result.stdout.split('\n') if line.strip()]
        assert 5 <= len(lines) <= 50, f"Output has {len(lines)} lines, seems unreasonable"
    
    @skip_if_cli_not_available()
    def test_list_intents_chinese_support(self):
        """测试中文支持"""
        result = run_cli("ai intents")
        assert_success(result)
        
        # 检查是否包含中文描述
        chinese_chars_found = any(ord(char) > 127 for char in result.stdout)
        assert chinese_chars_found, "No Chinese characters found in output, may indicate missing localization"
    
    @skip_if_cli_not_available()
    def test_list_intents_consistency_with_route(self):
        """测试与路由功能的一致性"""
        # 首先获取意图列表
        intents_result = run_cli("ai intents")
        assert_success(intents_result)
        
        # 提取意图ID
        core_intents = ["today", "capture", "projects_overview"]
        
        for intent in core_intents:
            if intent in intents_result.stdout:
                # 测试这个意图是否能被路由识别
                if intent == "today":
                    test_utterance = "今天做什么"
                elif intent == "capture":
                    test_utterance = "记录 测试任务"  
                elif intent == "projects_overview":
                    test_utterance = "项目概览"
                else:
                    continue
                
                route_result = run_cli(f'ai route "{test_utterance}"')
                # 路由应该能识别这些意图（可能因其他原因失败，但不应该是意图不存在）
                if route_result.returncode != 0:
                    # 如果失败，检查是否是因为意图不支持
                    error_text = route_result.stderr + route_result.stdout
                    assert "不支持" not in error_text and "unsupported" not in error_text.lower(), f"Intent {intent} listed but not supported in routing"
    
    @skip_if_cli_not_available()
    def test_list_intents_machine_readable_format(self):
        """测试输出是否适合机器解析"""
        result = run_cli("ai intents")
        assert_success(result)
        
        # 输出应该有结构化格式，便于解析
        lines = result.stdout.split('\n')
        structured_lines = 0
        
        for line in lines:
            # 检查是否有结构化标记（如 •, *, -, 或冒号）
            if any(marker in line for marker in ['•', '*', '-', ':']):
                structured_lines += 1
        
        assert structured_lines >= 3, "Output lacks structured format for machine parsing"