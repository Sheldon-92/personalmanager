"""
AI执行器命令模块
集成SafetyUX设计，提供安全、友好的AI命令执行体验
"""

import subprocess
import sys
from typing import Optional, Dict, Any, Tuple
from pathlib import Path

import typer
from rich.console import Console

from pm.routing.ux_messages import UXMessages, ErrorType, ConfidenceLevel
from pm.routing.rich_formatter import RichFormatter


# 创建AI执行器应用
ai_executor_app = typer.Typer(
    name="ai",
    help="AI智能执行器 - 安全执行自然语言命令",
    no_args_is_help=True
)

# 全局控制台和格式化器
console = Console()
formatter = RichFormatter(console)


class SafetyAnalyzer:
    """安全分析器 - 检测潜在危险操作"""
    
    DANGEROUS_PATTERNS = [
        "rm -rf",
        "sudo rm",
        "format",
        "del /q",
        "shutdown",
        "reboot",
        "kill -9",
        "pkill",
        "chmod 777",
        "chown -R",
        "> /dev/null",
        "dd if=",
        "mkfs",
        "fdisk"
    ]
    
    SYSTEM_PATHS = [
        "/bin", "/sbin", "/usr/bin", "/usr/sbin",
        "/etc", "/sys", "/proc", "/dev",
        "C:\\Windows", "C:\\System32"
    ]
    
    @classmethod
    def analyze_command(cls, command: str) -> Tuple[bool, str]:
        """
        分析命令安全性
        
        Args:
            command: 要分析的命令
            
        Returns:
            (is_dangerous, reason) 元组
        """
        command_lower = command.lower()
        
        # 检查危险模式
        for pattern in cls.DANGEROUS_PATTERNS:
            if pattern in command_lower:
                return True, f"包含危险模式: {pattern}"
        
        # 检查系统路径操作
        for path in cls.SYSTEM_PATHS:
            if path.lower() in command_lower:
                return True, f"涉及系统路径: {path}"
        
        # 检查文件删除操作
        if any(word in command_lower for word in ["delete", "remove", "unlink"]):
            if any(word in command_lower for word in ["all", "*", "recursive", "-r"]):
                return True, "批量删除操作"
        
        return False, ""


class IntentClassifier:
    """意图分类器 - 识别用户意图并计算置信度"""
    
    INTENT_PATTERNS = {
        "查看文件": ["ls", "dir", "list", "show", "view", "cat", "less", "more"],
        "创建文件": ["touch", "create", "new", "make", "mkdir"],
        "编辑文件": ["edit", "vim", "nano", "code"],
        "删除文件": ["rm", "del", "delete", "remove"],
        "复制文件": ["cp", "copy", "duplicate"],
        "移动文件": ["mv", "move", "rename"],
        "搜索内容": ["find", "grep", "search", "locate"],
        "系统状态": ["ps", "top", "status", "info", "disk", "memory"],
        "网络操作": ["ping", "curl", "wget", "ssh", "scp"],
        "Git操作": ["git", "commit", "push", "pull", "merge", "branch"]
    }
    
    @classmethod
    def classify_intent(cls, utterance: str) -> Tuple[str, float]:
        """
        分类用户意图
        
        Args:
            utterance: 用户输入
            
        Returns:
            (intent, confidence) 元组
        """
        utterance_lower = utterance.lower()
        best_intent = "未知操作"
        best_score = 0.0
        
        for intent, patterns in cls.INTENT_PATTERNS.items():
            score = sum(1 for pattern in patterns if pattern in utterance_lower)
            if score > best_score:
                best_score = score
                best_intent = intent
        
        # 计算置信度 (简化版)
        confidence = min(best_score / 3.0, 1.0) if best_score > 0 else 0.0
        
        # 如果包含明确的命令词，提高置信度
        if any(cmd in utterance_lower for cmd in ["pm", "python", "node", "npm", "pip"]):
            confidence = min(confidence + 0.3, 1.0)
        
        return best_intent, confidence


class CommandGenerator:
    """命令生成器 - 将自然语言转换为可执行命令"""
    
    @classmethod
    def generate_command(cls, utterance: str, intent: str) -> Optional[str]:
        """
        生成可执行命令
        
        Args:
            utterance: 用户输入
            intent: 识别的意图
            
        Returns:
            生成的命令字符串
        """
        utterance_lower = utterance.lower()
        
        # 简化的命令生成逻辑
        if "任务" in utterance or "task" in utterance_lower:
            if "今天" in utterance or "today" in utterance_lower:
                return "pm tasks today"
            elif "列表" in utterance or "list" in utterance_lower:
                return "pm tasks list"
            else:
                return "pm tasks"
        
        elif "习惯" in utterance or "habit" in utterance_lower:
            return "pm habits status"
        
        elif "项目" in utterance or "project" in utterance_lower:
            return "pm projects list"
        
        elif "状态" in utterance or "status" in utterance_lower:
            return "pm doctor"
        
        elif "帮助" in utterance or "help" in utterance_lower:
            return "pm --help"
        
        # 如果输入已经像命令，直接返回
        if utterance_lower.startswith(("pm", "python", "pip", "npm", "node")):
            return utterance
        
        return None


@ai_executor_app.command("execute")
def execute_command(
    utterance: str = typer.Argument(..., help="自然语言命令描述"),
    auto_confirm: bool = typer.Option(False, "--yes", "-y", help="自动确认执行"),
    language: str = typer.Option("zh", "--lang", "-l", help="界面语言 (zh/en)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="仅显示生成的命令，不执行")
) -> None:
    """
    AI智能执行器 - 将自然语言转换为可执行命令
    
    Example:
        pm ai execute "显示今天的任务"
        pm ai execute "check system status" --lang en
        pm ai execute "列出所有项目" --dry-run
    """
    try:
        # 1. 意图分类和置信度计算
        intent, confidence = IntentClassifier.classify_intent(utterance)
        
        # 2. 生成命令
        command = CommandGenerator.generate_command(utterance, intent)
        
        if not command:
            formatter.format_error(
                ErrorType.NO_MATCH,
                language=language,
                utterance=utterance
            )
            raise typer.Exit(1)
        
        # 3. 安全性分析
        is_dangerous, danger_reason = SafetyAnalyzer.analyze_command(command)
        
        if is_dangerous:
            formatter.format_error(
                ErrorType.DANGEROUS,
                language=language,
                reason=danger_reason
            )
            
            # 显示警告但允许继续
            formatter.format_warning("irreversible", language=language)
        
        # 4. 显示命令预览
        formatter.format_command_preview(
            command, 
            f"意图: {intent}, 置信度: {confidence:.1%}",
            language
        )
        
        # 5. Dry run模式
        if dry_run:
            formatter.format_info(
                f"Dry run模式 - 生成的命令: {command}" if language == "zh" 
                else f"Dry run mode - Generated command: {command}",
                language=language
            )
            return
        
        # 6. 用户确认
        if not auto_confirm:
            confirmed = formatter.format_confirm(
                message="",  # 消息在format_confirm内部生成
                command=command,
                confidence=confidence,
                intent=intent,
                language=language
            )
            
            if not confirmed:
                formatter.format_info(
                    "操作已取消" if language == "zh" else "Operation cancelled",
                    language=language
                )
                return
        
        # 7. 执行命令
        _execute_safe_command(command, language)
        
    except KeyboardInterrupt:
        formatter.format_info(
            "用户中断操作" if language == "zh" else "Operation interrupted by user",
            language=language
        )
        raise typer.Exit(130)
    except Exception as e:
        formatter.format_error(
            ErrorType.EXECUTION,
            language=language,
            error=str(e)
        )
        raise typer.Exit(1)


def _execute_safe_command(command: str, language: str = "zh") -> None:
    """
    安全执行命令
    
    Args:
        command: 要执行的命令
        language: 语言设置
    """
    try:
        # 执行命令
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60  # 60秒超时
        )
        
        if result.returncode == 0:
            # 执行成功
            output = result.stdout.strip() if result.stdout else ""
            formatter.format_success(
                output=output,
                language=language
            )
        else:
            # 执行失败
            error_msg = result.stderr.strip() if result.stderr else f"退出码: {result.returncode}"
            formatter.format_error(
                ErrorType.EXECUTION,
                language=language,
                error=error_msg
            )
            
    except subprocess.TimeoutExpired:
        formatter.format_error(
            ErrorType.EXECUTION,
            language=language,
            error="命令执行超时 (60秒)" if language == "zh" else "Command timeout (60s)"
        )
    except FileNotFoundError:
        formatter.format_error(
            ErrorType.EXECUTION,
            language=language,
            error="命令未找到" if language == "zh" else "Command not found"
        )


@ai_executor_app.command("test")
def test_classifier(
    utterance: str = typer.Argument(..., help="测试用的自然语言输入"),
    language: str = typer.Option("zh", "--lang", "-l", help="界面语言")
) -> None:
    """
    测试意图分类器和命令生成器
    """
    formatter.format_info(f"测试输入: '{utterance}'", "🧪 测试模式", language)
    
    # 意图分类
    intent, confidence = IntentClassifier.classify_intent(utterance)
    
    # 命令生成
    command = CommandGenerator.generate_command(utterance, intent)
    
    # 安全性分析
    is_dangerous, danger_reason = SafetyAnalyzer.analyze_command(command) if command else (False, "")
    
    # 显示结果
    results = {
        "识别意图": intent,
        "置信度": f"{confidence:.1%}",
        "生成命令": command or "无法生成",
        "安全评估": "危险" if is_dangerous else "安全",
        "危险原因": danger_reason or "无"
    }
    
    if language == "en":
        results = {
            "Intent": intent,
            "Confidence": f"{confidence:.1%}",
            "Generated Command": command or "Cannot generate",
            "Safety": "Dangerous" if is_dangerous else "Safe", 
            "Danger Reason": danger_reason or "None"
        }
    
    formatter.format_table(results, "分析结果" if language == "zh" else "Analysis Results")


# 主入口点 - 如果直接运行此文件
if __name__ == "__main__":
    ai_executor_app()