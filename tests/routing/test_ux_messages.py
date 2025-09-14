"""
UX消息模块测试
验证用户体验消息的正确性和多语言支持
"""

import pytest
from pm.routing.ux_messages import UXMessages, ConfidenceLevel, ErrorType


class TestUXMessages:
    """UX消息类的测试套件"""
    
    def test_confidence_levels(self):
        """测试置信度级别枚举"""
        assert ConfidenceLevel.HIGH.value == "high"
        assert ConfidenceLevel.MEDIUM.value == "medium" 
        assert ConfidenceLevel.LOW.value == "low"
    
    def test_error_types(self):
        """测试错误类型枚举"""
        assert ErrorType.NO_MATCH.value == "no_match"
        assert ErrorType.DANGEROUS.value == "dangerous"
        assert ErrorType.EXECUTION.value == "execution"
        assert ErrorType.PERMISSION.value == "permission"
        assert ErrorType.INVALID_INPUT.value == "invalid_input"
    
    def test_get_confirm_message_high_confidence(self):
        """测试高置信度确认消息"""
        message = UXMessages.get_confirm_message(
            confidence=0.9,
            command="pm tasks today",
            language="zh"
        )
        assert "即将执行：pm tasks today" in message
        assert "是否继续？(y/N)" in message
        
        # 英文版本
        message_en = UXMessages.get_confirm_message(
            confidence=0.9,
            command="pm tasks today", 
            language="en"
        )
        assert "About to execute: pm tasks today" in message_en
        assert "Continue? (y/N)" in message_en
    
    def test_get_confirm_message_medium_confidence(self):
        """测试中置信度确认消息"""
        message = UXMessages.get_confirm_message(
            confidence=0.6,
            command="pm tasks today",
            intent="查看今天的任务",
            language="zh"
        )
        assert "我理解您想要查看今天的任务" in message
        assert "即将执行：pm tasks today" in message
        assert "是否继续？(y/N)" in message
    
    def test_get_confirm_message_low_confidence(self):
        """测试低置信度确认消息"""
        message = UXMessages.get_confirm_message(
            confidence=0.3,
            command="pm tasks today",
            intent="查看今天的任务",
            language="zh"
        )
        assert "我不太确定您的意图" in message
        assert "您是想要查看今天的任务吗？" in message
        assert "建议命令：pm tasks today" in message
    
    def test_get_error_message_no_match(self):
        """测试无匹配错误消息"""
        message = UXMessages.get_error_message(
            ErrorType.NO_MATCH,
            language="zh",
            utterance="随机文本"
        )
        assert "抱歉，我不理解 '随机文本'" in message
        assert "试试：'今天的任务' 或 '记录 内容'" in message
        
        # 英文版本
        message_en = UXMessages.get_error_message(
            ErrorType.NO_MATCH,
            language="en",
            utterance="random text"
        )
        assert "Sorry, I don't understand 'random text'" in message_en
    
    def test_get_error_message_dangerous(self):
        """测试危险操作错误消息"""
        message = UXMessages.get_error_message(
            ErrorType.DANGEROUS,
            language="zh",
            reason="包含rm -rf命令"
        )
        assert "检测到潜在危险操作" in message
        assert "原因：包含rm -rf命令" in message
        assert "请仔细确认后再执行" in message
    
    def test_get_error_message_execution(self):
        """测试执行失败错误消息"""
        message = UXMessages.get_error_message(
            ErrorType.EXECUTION,
            language="zh",
            error="命令未找到"
        )
        assert "命令执行失败" in message
        assert "错误：命令未找到" in message
        assert "pm doctor" in message
    
    def test_get_error_message_permission(self):
        """测试权限错误消息"""
        message = UXMessages.get_error_message(
            ErrorType.PERMISSION,
            language="zh",
            permission="写入权限"
        )
        assert "权限不足" in message
        assert "需要权限：写入权限" in message
    
    def test_get_error_message_invalid_input(self):
        """测试无效输入错误消息"""
        message = UXMessages.get_error_message(
            ErrorType.INVALID_INPUT,
            language="zh",
            expected="日期格式 YYYY-MM-DD",
            actual="明天"
        )
        assert "输入格式不正确" in message
        assert "期望格式：日期格式 YYYY-MM-DD" in message
        assert "您的输入：明天" in message
    
    def test_get_success_message(self):
        """测试成功消息"""
        message = UXMessages.get_success_message("executed", "zh")
        assert "命令执行成功" in message
        
        message = UXMessages.get_success_message("completed", "zh")
        assert "任务完成" in message
        
        message = UXMessages.get_success_message("saved", "zh")
        assert "数据已保存" in message
        
        message = UXMessages.get_success_message("created", "zh", item="新任务")
        assert "创建成功：新任务" in message
    
    def test_get_success_message_english(self):
        """测试英文成功消息"""
        message = UXMessages.get_success_message("executed", "en")
        assert "Command executed successfully" in message
        
        message = UXMessages.get_success_message("completed", "en")
        assert "Task completed" in message
    
    def test_get_warning_message(self):
        """测试警告消息"""
        message = UXMessages.get_warning_message("backup_recommended", "zh")
        assert "建议先备份数据" in message
        
        message = UXMessages.get_warning_message("irreversible", "zh")
        assert "此操作不可逆转" in message
        
        message = UXMessages.get_warning_message("system_change", "zh")
        assert "将修改系统设置" in message
    
    def test_get_warning_message_english(self):
        """测试英文警告消息"""
        message = UXMessages.get_warning_message("backup_recommended", "en")
        assert "Backup recommended" in message
        
        message = UXMessages.get_warning_message("irreversible", "en")
        assert "This operation is irreversible" in message
    
    def test_message_formatting_with_parameters(self):
        """测试消息参数化格式"""
        # 测试确认消息的参数替换
        message = UXMessages.get_confirm_message(
            confidence=0.7,
            command="rm important.txt",
            intent="删除重要文件",
            language="zh"
        )
        assert "rm important.txt" in message
        assert "删除重要文件" in message
        
        # 测试错误消息的参数替换
        message = UXMessages.get_error_message(
            ErrorType.DANGEROUS,
            language="zh",
            reason="尝试删除系统文件"
        )
        assert "尝试删除系统文件" in message
    
    def test_edge_cases(self):
        """测试边界情况"""
        # 置信度边界值
        message = UXMessages.get_confirm_message(0.0, "test", language="zh")
        assert "不太确定" in message  # 应该是低置信度消息
        
        message = UXMessages.get_confirm_message(1.0, "test", language="zh")
        assert "即将执行" in message  # 应该是高置信度消息
        
        message = UXMessages.get_confirm_message(0.5, "test", language="zh")
        assert "理解您想要" in message  # 边界值，应该是中置信度
        
        # 不存在的消息类型
        message = UXMessages.get_success_message("nonexistent", "zh")
        assert "命令执行成功" in message  # 应该回退到默认消息
        
        message = UXMessages.get_warning_message("nonexistent", "zh")
        assert "警告" in message  # 应该回退到默认警告


class TestMessageConsistency:
    """测试消息一致性"""
    
    def test_chinese_english_message_pairs(self):
        """测试中英文消息对的完整性"""
        # 确认消息
        for level in ConfidenceLevel:
            zh_msg = UXMessages.CONFIRM_MESSAGES[level]["zh"]
            en_msg = UXMessages.CONFIRM_MESSAGES[level]["en"]
            assert zh_msg is not None
            assert en_msg is not None
            assert len(zh_msg) > 0
            assert len(en_msg) > 0
        
        # 错误消息
        for error_type in ErrorType:
            zh_msg = UXMessages.ERROR_MESSAGES[error_type]["zh"]
            en_msg = UXMessages.ERROR_MESSAGES[error_type]["en"]
            assert zh_msg is not None
            assert en_msg is not None
            assert len(zh_msg) > 0
            assert len(en_msg) > 0
        
        # 成功消息
        for msg_type in UXMessages.SUCCESS_MESSAGES:
            zh_msg = UXMessages.SUCCESS_MESSAGES[msg_type]["zh"]
            en_msg = UXMessages.SUCCESS_MESSAGES[msg_type]["en"]
            assert zh_msg is not None
            assert en_msg is not None
            assert len(zh_msg) > 0
            assert len(en_msg) > 0
        
        # 警告消息
        for warning_type in UXMessages.WARNING_MESSAGES:
            zh_msg = UXMessages.WARNING_MESSAGES[warning_type]["zh"]
            en_msg = UXMessages.WARNING_MESSAGES[warning_type]["en"]
            assert zh_msg is not None
            assert en_msg is not None
            assert len(zh_msg) > 0
            assert len(en_msg) > 0
    
    def test_emoji_consistency(self):
        """测试表情符号使用的一致性"""
        # 检查成功消息都包含✅
        for msg_type, messages in UXMessages.SUCCESS_MESSAGES.items():
            for lang, msg in messages.items():
                if msg_type != "saved":  # saved使用💾
                    assert "✅" in msg or "🎉" in msg or "🆕" in msg
        
        # 检查错误消息包含相应图标
        error_icons = {"❌", "😕", "⚠️", "🔒", "📝"}
        for error_type, messages in UXMessages.ERROR_MESSAGES.items():
            for lang, msg in messages.items():
                has_icon = any(icon in msg for icon in error_icons)
                assert has_icon, f"错误消息缺少图标: {error_type} - {msg}"
    
    def test_format_string_validity(self):
        """测试格式字符串的有效性"""
        # 测试所有包含格式占位符的消息
        test_params = {
            "command": "test command",
            "intent": "test intent", 
            "utterance": "test utterance",
            "reason": "test reason",
            "error": "test error",
            "permission": "test permission",
            "expected": "test expected",
            "actual": "test actual",
            "item": "test item"
        }
        
        # 确认消息格式测试
        for level in ConfidenceLevel:
            for lang in ["zh", "en"]:
                template = UXMessages.CONFIRM_MESSAGES[level][lang]
                try:
                    formatted = template.format(**test_params)
                    assert len(formatted) > 0
                except KeyError as e:
                    pytest.fail(f"确认消息格式错误 {level}-{lang}: {e}")
        
        # 错误消息格式测试
        for error_type in ErrorType:
            for lang in ["zh", "en"]:
                template = UXMessages.ERROR_MESSAGES[error_type][lang]
                try:
                    formatted = template.format(**test_params)
                    assert len(formatted) > 0
                except KeyError as e:
                    pytest.fail(f"错误消息格式错误 {error_type}-{lang}: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])