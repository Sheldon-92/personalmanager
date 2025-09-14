"""
Rich富文本格式化模块
使用Rich库提供美观的命令行界面输出
"""

from typing import Optional, Dict, Any
from rich.panel import Panel
from rich.console import Console
from rich.text import Text
from rich.table import Table
from rich.prompt import Confirm
from rich.markdown import Markdown
from rich import box

from .ux_messages import UXMessages, ConfidenceLevel, ErrorType


class RichFormatter:
    """
    Rich富文本格式化器
    负责美化所有命令行输出，提供一致的视觉体验
    """
    
    def __init__(self, console: Optional[Console] = None):
        """
        初始化格式化器
        
        Args:
            console: Rich Console实例，如果为None则创建新的
        """
        self.console = console or Console()
        
        # 颜色主题
        self.colors = {
            "high_confidence": "green",
            "medium_confidence": "yellow", 
            "low_confidence": "red",
            "success": "green",
            "error": "red",
            "warning": "yellow",
            "info": "blue",
            "neutral": "white"
        }
        
        # 图标映射
        self.icons = {
            "success": "✅",
            "error": "❌", 
            "warning": "⚠️",
            "info": "ℹ️",
            "question": "❓",
            "rocket": "🚀",
            "gear": "⚙️",
            "lock": "🔒",
            "lightbulb": "💡"
        }
    
    def format_confirm(self, message: str, command: str, confidence: float, 
                      intent: str = "", language: str = "zh") -> bool:
        """
        格式化并显示确认消息，返回用户选择
        
        Args:
            message: 基础消息内容
            command: 要执行的命令
            confidence: 置信度 (0-1)
            intent: 用户意图
            language: 语言
            
        Returns:
            用户确认结果 (True/False)
        """
        # 根据置信度选择颜色和样式
        if confidence > 0.8:
            color = self.colors["high_confidence"]
            title_icon = "🎯"
            border_style = "green"
        elif confidence > 0.5:
            color = self.colors["medium_confidence"]
            title_icon = "🤔"
            border_style = "yellow"
        else:
            color = self.colors["low_confidence"]
            title_icon = "❓"
            border_style = "red"
        
        # 创建确认消息
        confirm_text = UXMessages.get_confirm_message(confidence, command, intent, language)
        
        # 添加置信度信息
        confidence_text = f"\n置信度: {confidence:.1%}" if language == "zh" else f"\nConfidence: {confidence:.1%}"
        
        # 创建面板
        panel_content = f"{confirm_text}{confidence_text}"
        
        panel = Panel(
            panel_content,
            title=f"{title_icon} 确认执行" if language == "zh" else f"{title_icon} Confirm Execution",
            border_style=border_style,
            padding=(1, 2)
        )
        
        self.console.print(panel)
        
        # 使用Rich的Confirm获取用户输入
        prompt_text = "继续执行？" if language == "zh" else "Continue?"
        return Confirm.ask(prompt_text, default=False)
    
    def format_error(self, error_type: ErrorType, language: str = "zh", **kwargs) -> None:
        """
        格式化并显示错误消息
        
        Args:
            error_type: 错误类型
            language: 语言
            **kwargs: 错误消息的格式化参数
        """
        error_message = UXMessages.get_error_message(error_type, language, **kwargs)
        
        # 根据错误类型选择图标和颜色
        icon_map = {
            ErrorType.NO_MATCH: "❓",
            ErrorType.DANGEROUS: "⚠️",
            ErrorType.EXECUTION: "❌",
            ErrorType.PERMISSION: "🔒",
            ErrorType.INVALID_INPUT: "📝"
        }
        
        icon = icon_map.get(error_type, "❌")
        title = f"{icon} 错误" if language == "zh" else f"{icon} Error"
        
        panel = Panel(
            error_message,
            title=title,
            border_style="red",
            padding=(1, 2)
        )
        
        self.console.print(panel)
    
    def format_success(self, message: str = "", output: str = "", 
                      message_type: str = "executed", language: str = "zh") -> None:
        """
        格式化并显示成功消息
        
        Args:
            message: 自定义成功消息
            output: 命令输出内容
            message_type: 成功消息类型
            language: 语言
        """
        if not message:
            message = UXMessages.get_success_message(message_type, language)
        
        # 创建成功面板
        panel_content = message
        if output:
            panel_content += f"\n\n输出：\n{output}" if language == "zh" else f"\n\nOutput:\n{output}"
        
        panel = Panel(
            panel_content,
            title="✅ 成功" if language == "zh" else "✅ Success",
            border_style="green",
            padding=(1, 2)
        )
        
        self.console.print(panel)
    
    def format_warning(self, warning_type: str, language: str = "zh", **kwargs) -> None:
        """
        格式化并显示警告消息
        
        Args:
            warning_type: 警告类型
            language: 语言
            **kwargs: 警告消息的格式化参数
        """
        warning_message = UXMessages.get_warning_message(warning_type, language, **kwargs)
        
        panel = Panel(
            warning_message,
            title="⚠️  警告" if language == "zh" else "⚠️  Warning", 
            border_style="yellow",
            padding=(1, 2)
        )
        
        self.console.print(panel)
    
    def format_info(self, message: str, title: str = "", language: str = "zh") -> None:
        """
        格式化并显示信息消息
        
        Args:
            message: 信息内容
            title: 标题
            language: 语言
        """
        if not title:
            title = "ℹ️  信息" if language == "zh" else "ℹ️  Info"
        
        panel = Panel(
            message,
            title=title,
            border_style="blue",
            padding=(1, 2)
        )
        
        self.console.print(panel)
    
    def format_table(self, data: Dict[str, Any], title: str = "", 
                    headers: Optional[list] = None) -> None:
        """
        格式化表格数据
        
        Args:
            data: 表格数据
            title: 表格标题
            headers: 列标题
        """
        table = Table(title=title, box=box.ROUNDED)
        
        if headers:
            for header in headers:
                table.add_column(header, style="cyan")
        
        # 添加数据行
        for key, value in data.items():
            table.add_row(str(key), str(value))
        
        self.console.print(table)
    
    def format_progress_status(self, current: int, total: int, 
                              task_name: str = "", language: str = "zh") -> None:
        """
        显示进度状态
        
        Args:
            current: 当前进度
            total: 总数
            task_name: 任务名称
            language: 语言
        """
        percentage = (current / total) * 100 if total > 0 else 0
        progress_bar = "█" * int(percentage // 5) + "░" * (20 - int(percentage // 5))
        
        status_text = f"{task_name}\n进度: [{progress_bar}] {current}/{total} ({percentage:.1f}%)"
        if language == "en":
            status_text = f"{task_name}\nProgress: [{progress_bar}] {current}/{total} ({percentage:.1f}%)"
        
        self.format_info(status_text, "🚀 进度状态" if language == "zh" else "🚀 Progress Status", language)
    
    def format_command_preview(self, command: str, description: str = "", 
                              language: str = "zh") -> None:
        """
        格式化命令预览
        
        Args:
            command: 命令内容
            description: 命令描述
            language: 语言
        """
        content = f"命令: `{command}`" if language == "zh" else f"Command: `{command}`"
        if description:
            content += f"\n描述: {description}" if language == "zh" else f"\nDescription: {description}"
        
        panel = Panel(
            content,
            title="⚙️  命令预览" if language == "zh" else "⚙️  Command Preview",
            border_style="blue",
            padding=(1, 2)
        )
        
        self.console.print(panel)
    
    def clear_screen(self) -> None:
        """清屏"""
        self.console.clear()
    
    def print_separator(self, char: str = "─", length: int = 50) -> None:
        """打印分隔线"""
        self.console.print(char * length, style="dim")