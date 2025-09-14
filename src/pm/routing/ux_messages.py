"""
UX消息模板模块
负责定义不同类型的用户交互消息，包括确认消息、错误提示和成功反馈
"""

from typing import Dict, Any
from enum import Enum


class ConfidenceLevel(Enum):
    """置信度级别枚举"""
    HIGH = "high"      # 高置信度 > 0.8
    MEDIUM = "medium"  # 中置信度 0.5 - 0.8
    LOW = "low"        # 低置信度 < 0.5


class ErrorType(Enum):
    """错误类型枚举"""
    NO_MATCH = "no_match"           # 无法匹配用户意图
    DANGEROUS = "dangerous"         # 危险操作检测
    EXECUTION = "execution"         # 命令执行失败
    PERMISSION = "permission"       # 权限不足
    INVALID_INPUT = "invalid_input" # 无效输入


class UXMessages:
    """
    用户体验消息类
    包含所有用户交互场景的消息模板，支持中英文双语
    """
    
    # 确认消息（根据置信度分级）
    CONFIRM_MESSAGES = {
        ConfidenceLevel.HIGH: {
            "zh": "即将执行：{command}\n是否继续？(y/N)",
            "en": "About to execute: {command}\nContinue? (y/N)"
        },
        ConfidenceLevel.MEDIUM: {
            "zh": "我理解您想要{intent}。\n即将执行：{command}\n是否继续？(y/N)",
            "en": "I understand you want to {intent}.\nAbout to execute: {command}\nContinue? (y/N)"
        },
        ConfidenceLevel.LOW: {
            "zh": "我不太确定您的意图。\n您是想要{intent}吗？\n建议命令：{command}\n是否执行？(y/N)",
            "en": "I'm not sure about your intent.\nDo you want to {intent}?\nSuggested command: {command}\nExecute? (y/N)"
        }
    }
    
    # 错误消息模板
    ERROR_MESSAGES = {
        ErrorType.NO_MATCH: {
            "zh": "😕 抱歉，我不理解 '{utterance}'\n💡 试试：'今天的任务' 或 '记录 内容'",
            "en": "😕 Sorry, I don't understand '{utterance}'\n💡 Try: 'today tasks' or 'record content'"
        },
        ErrorType.DANGEROUS: {
            "zh": "⚠️  检测到潜在危险操作\n原因：{reason}\n建议：请仔细确认后再执行",
            "en": "⚠️  Potentially dangerous operation detected\nReason: {reason}\nSuggestion: Please confirm carefully before proceeding"
        },
        ErrorType.EXECUTION: {
            "zh": "❌ 命令执行失败\n错误：{error}\n💡 可以尝试 'pm doctor' 检查系统状态",
            "en": "❌ Command execution failed\nError: {error}\n💡 Try 'pm doctor' to check system status"
        },
        ErrorType.PERMISSION: {
            "zh": "🔒 权限不足\n需要权限：{permission}\n请联系管理员或检查权限设置",
            "en": "🔒 Insufficient permissions\nRequired: {permission}\nPlease contact admin or check permission settings"
        },
        ErrorType.INVALID_INPUT: {
            "zh": "📝 输入格式不正确\n期望格式：{expected}\n您的输入：{actual}",
            "en": "📝 Invalid input format\nExpected: {expected}\nYour input: {actual}"
        }
    }
    
    # 成功消息
    SUCCESS_MESSAGES = {
        "executed": {
            "zh": "✅ 命令执行成功",
            "en": "✅ Command executed successfully"
        },
        "completed": {
            "zh": "🎉 任务完成！",
            "en": "🎉 Task completed!"
        },
        "saved": {
            "zh": "💾 数据已保存",
            "en": "💾 Data saved"
        },
        "created": {
            "zh": "🆕 创建成功：{item}",
            "en": "🆕 Created successfully: {item}"
        }
    }
    
    # 警告消息
    WARNING_MESSAGES = {
        "backup_recommended": {
            "zh": "💡 建议先备份数据",
            "en": "💡 Backup recommended"
        },
        "irreversible": {
            "zh": "⚠️  此操作不可逆转",
            "en": "⚠️  This operation is irreversible"
        },
        "system_change": {
            "zh": "🔧 将修改系统设置",
            "en": "🔧 Will modify system settings"
        }
    }
    
    @classmethod
    def get_confirm_message(cls, confidence: float, command: str, intent: str = "", language: str = "zh") -> str:
        """
        根据置信度获取确认消息
        
        Args:
            confidence: 置信度 (0-1)
            command: 要执行的命令
            intent: 用户意图描述
            language: 语言 ('zh' 或 'en')
        
        Returns:
            格式化的确认消息
        """
        if confidence > 0.8:
            level = ConfidenceLevel.HIGH
        elif confidence >= 0.5:
            level = ConfidenceLevel.MEDIUM
        else:
            level = ConfidenceLevel.LOW
            
        template = cls.CONFIRM_MESSAGES[level][language]
        
        if level == ConfidenceLevel.HIGH:
            return template.format(command=command)
        else:
            return template.format(command=command, intent=intent)
    
    @classmethod
    def get_error_message(cls, error_type: ErrorType, language: str = "zh", **kwargs) -> str:
        """
        获取错误消息
        
        Args:
            error_type: 错误类型
            language: 语言 ('zh' 或 'en')
            **kwargs: 用于格式化消息的参数
            
        Returns:
            格式化的错误消息
        """
        template = cls.ERROR_MESSAGES[error_type][language]
        return template.format(**kwargs)
    
    @classmethod
    def get_success_message(cls, message_type: str, language: str = "zh", **kwargs) -> str:
        """
        获取成功消息
        
        Args:
            message_type: 消息类型
            language: 语言 ('zh' 或 'en')
            **kwargs: 用于格式化消息的参数
            
        Returns:
            格式化的成功消息
        """
        template = cls.SUCCESS_MESSAGES.get(message_type, cls.SUCCESS_MESSAGES["executed"])[language]
        return template.format(**kwargs)
    
    @classmethod
    def get_warning_message(cls, warning_type: str, language: str = "zh", **kwargs) -> str:
        """
        获取警告消息
        
        Args:
            warning_type: 警告类型
            language: 语言 ('zh' 或 'en')
            **kwargs: 用于格式化消息的参数
            
        Returns:
            格式化的警告消息
        """
        template = cls.WARNING_MESSAGES.get(warning_type, {"zh": "⚠️  警告", "en": "⚠️  Warning"})[language]
        return template.format(**kwargs)