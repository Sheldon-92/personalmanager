"""命令执行器 - 用于编程式执行PersonalManager命令"""

import subprocess
import sys
from typing import List, Dict, Any, Optional
import structlog

logger = structlog.get_logger()


class CommandExecutor:
    """PersonalManager命令执行器"""

    def __init__(self):
        # Import here to avoid circular imports
        import os
        current_dir = os.getcwd()
        self.base_command = [sys.executable, "-m", "pm.cli.main"]
        self.env = os.environ.copy()
        self.env["PYTHONPATH"] = f"{current_dir}/src"

    def execute_pm_command(self, command_string: str) -> Dict[str, Any]:
        """执行PM命令字符串

        Args:
            command_string: 命令字符串，如 "pm briefing" 或 "pm next @today"

        Returns:
            执行结果字典
        """

        try:
            # 解析命令字符串
            parts = command_string.strip().split()

            if not parts:
                return {"success": False, "error": "空命令"}

            # 移除 'pm' 前缀（如果存在）
            if parts[0] == "pm":
                parts = parts[1:]

            if not parts:
                return {"success": False, "error": "无效命令"}

            # 构建完整命令
            full_command = self.base_command + parts

            logger.info("Executing command", command=command_string, full_command=full_command)

            # 执行命令
            result = subprocess.run(
                full_command,
                capture_output=True,
                text=True,
                timeout=30,  # 30秒超时
                env=self.env
            )

            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "command": command_string
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "命令执行超时",
                "command": command_string
            }
        except Exception as e:
            logger.error("Command execution failed", command=command_string, error=str(e))
            return {
                "success": False,
                "error": f"执行错误: {str(e)}",
                "command": command_string
            }

    def execute_slash_command(self, slash_command: str) -> Dict[str, Any]:
        """执行斜杠命令

        Args:
            slash_command: 斜杠命令，如 "/pm briefing" 或 "/gmail scan"

        Returns:
            执行结果字典
        """

        if not slash_command.startswith('/'):
            return {"success": False, "error": "不是有效的斜杠命令"}

        # 移除斜杠前缀
        command_without_slash = slash_command[1:]

        # 映射斜杠命令到实际PM命令
        command_mapping = {
            # /pm 系列命令
            "pm": "briefing",  # /pm 默认显示简报
            "pm briefing": "briefing",
            "pm inbox": "inbox",
            "pm clarify": "clarify",
            "pm next": "next",
            "pm today": "today",
            "pm session": "session info",

            # /gmail 系列命令
            "gmail": "gmail preview",  # /gmail 默认预览邮件
            "gmail scan": "gmail scan",
            "gmail preview": "gmail preview",
            "gmail stats": "gmail stats",

            # /task 系列命令
            "task": "inbox",  # /task 默认显示收件箱
            "task add": "capture",
            "task complete": "next",
            "task search": "inbox",

            # /quick 系列命令
            "quick": "today",  # /quick 默认显示今日推荐
            "quick cleanup": "inbox",  # TODO: 实现清理功能
            "quick overdue": "next",
            "quick urgent": "today",
            "quick health": "session health"
        }

        # 查找对应的PM命令
        pm_command = command_mapping.get(command_without_slash)

        if pm_command:
            return self.execute_pm_command(pm_command)
        else:
            return {
                "success": False,
                "error": f"未知的斜杠命令: {slash_command}",
                "available_commands": list(command_mapping.keys())
            }

    def execute_multiple_commands(self, commands: List[str]) -> List[Dict[str, Any]]:
        """批量执行多个命令

        Args:
            commands: 命令列表

        Returns:
            执行结果列表
        """

        results = []

        for command in commands:
            if command.startswith('/'):
                result = self.execute_slash_command(command)
            else:
                result = self.execute_pm_command(command)

            results.append(result)

        return results