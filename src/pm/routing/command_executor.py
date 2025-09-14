"""命令执行引擎 - 安全执行 PM 命令"""

import subprocess
import re
import shlex
import json
from typing import Dict, Any, List, Set, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm

from pm.core.errors import PMExecutionError, PMSecurityError


@dataclass
class ExecutionResult:
    """命令执行结果"""
    status: str  # "success", "error", "cancelled"
    output: str
    command_executed: str
    exit_code: int = 0
    error_message: str = ""
    duration: float = 0.0


class CommandExecutor:
    """命令执行引擎 - 负责安全执行路由结果"""

    def __init__(self):
        self.console = Console()
        self.safe_commands = self._load_safe_commands()
        self.dangerous_patterns = self._load_dangerous_patterns()

    def _load_safe_commands(self) -> Set[str]:
        """加载安全命令白名单"""
        return {
            # PM 核心命令
            "pm", "pm help", "pm version", "pm guide",
            
            # 任务管理
            "pm capture", "pm inbox", "pm next", "pm task", "pm clarify",
            "pm learn", "pm context", "pm smart-next", "pm recommend", "pm today",
            "pm explain", "pm preferences",
            
            # 项目管理
            "pm projects", "pm project", "pm update", "pm monitor",
            
            # Google 服务集成
            "pm auth", "pm calendar", "pm tasks", "pm gmail",
            
            # 报告和分析
            "pm report", "pm habits", "pm deepwork", "pm review", "pm obsidian",
            
            # 系统管理
            "pm privacy", "pm doctor", "pm setup",
            
            # AI 命令
            "pm ai"
        }

    def _load_dangerous_patterns(self) -> List[re.Pattern]:
        """加载危险命令模式"""
        dangerous = [
            r"[;&|`$(){}\\]",  # 命令注入字符
            r">\s*[^>]",       # 重定向
            r"<\s*[^<]",       # 输入重定向  
            r"\*\*",           # 通配符
            r"rm\s+",          # 删除命令
            r"sudo\s+",        # 提权命令
            r"chmod\s+",       # 权限修改
            r"chown\s+",       # 所有者修改
            r"curl\s+",        # 网络请求
            r"wget\s+",        # 网络下载
            r"python\s+",      # Python 执行
            r"node\s+",        # Node.js 执行
            r"bash\s+",        # Shell 执行
            r"sh\s+",          # Shell 执行
        ]
        return [re.compile(pattern, re.IGNORECASE) for pattern in dangerous]

    def execute(self, route_result: dict) -> dict:
        """
        执行路由结果
        
        Args:
            route_result: 包含命令信息的字典
                {
                    "command": "pm tasks capture", 
                    "args": ["Learn Python"],
                    "confidence": 0.9,
                    "explanation": "添加新任务到收件箱"
                }
        
        Returns:
            ExecutionResult 的字典表示
        """
        try:
            # 验证输入格式
            if not self._validate_route_result(route_result):
                return ExecutionResult(
                    status="error",
                    output="",
                    command_executed="",
                    error_message="无效的路由结果格式"
                ).__dict__

            # 构建完整命令
            base_command = route_result["command"]
            args = route_result.get("args", [])
            full_command = f"{base_command} {' '.join(args)}".strip()

            # 安全验证
            if not self._validate_command_safety(full_command):
                return ExecutionResult(
                    status="error",
                    output="",
                    command_executed=full_command,
                    error_message="命令被安全策略阻止"
                ).__dict__

            # 执行命令
            return self._execute_safe_command(base_command, args).__dict__

        except Exception as e:
            return ExecutionResult(
                status="error",
                output="",
                command_executed=route_result.get("command", ""),
                error_message=f"执行器内部错误: {str(e)}"
            ).__dict__

    def _validate_route_result(self, route_result: dict) -> bool:
        """验证路由结果格式"""
        if route_result is None or not isinstance(route_result, dict):
            return False
        required_fields = ["command"]
        return all(field in route_result for field in required_fields)

    def _validate_command_safety(self, command: str) -> bool:
        """验证命令安全性"""
        # 检查命令是否在白名单中
        base_command = self._extract_base_command(command)
        if base_command not in self.safe_commands:
            self.console.print(f"[red]❌ 不安全的命令: {base_command}[/red]")
            return False

        # 检查危险模式
        for pattern in self.dangerous_patterns:
            if pattern.search(command):
                self.console.print(f"[red]❌ 命令包含危险模式: {command}[/red]")
                return False

        return True

    def _extract_base_command(self, command: str) -> str:
        """提取基础命令（前两个词）"""
        parts = command.split()
        if len(parts) >= 2 and parts[0] == "pm":
            return f"{parts[0]} {parts[1]}"
        elif len(parts) >= 1:
            return parts[0]
        return command

    def _execute_safe_command(self, command: str, args: List[str]) -> ExecutionResult:
        """安全执行命令"""
        import time
        start_time = time.time()

        try:
            # 构建命令数组
            cmd_parts = shlex.split(command)
            # 清理和验证参数
            safe_args = [self._sanitize_argument(arg) for arg in args]
            full_cmd = cmd_parts + safe_args
            
            full_command_str = " ".join(full_cmd)
            self.console.print(f"[blue]► 执行: {full_command_str}[/blue]")

            # 执行命令
            result = subprocess.run(
                full_cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5分钟超时
                shell=False   # 禁用 shell 执行
            )

            duration = time.time() - start_time

            if result.returncode == 0:
                return ExecutionResult(
                    status="success",
                    output=result.stdout.strip(),
                    command_executed=full_command_str,
                    duration=duration
                )
            else:
                return ExecutionResult(
                    status="error",
                    output=result.stdout.strip(),
                    command_executed=full_command_str,
                    exit_code=result.returncode,
                    error_message=result.stderr.strip(),
                    duration=duration
                )

        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            return ExecutionResult(
                status="error",
                output="",
                command_executed=" ".join([command] + args),
                exit_code=124,
                error_message="命令执行超时（5分钟）",
                duration=duration
            )

        except FileNotFoundError:
            duration = time.time() - start_time
            return ExecutionResult(
                status="error",
                output="",
                command_executed=" ".join([command] + args),
                exit_code=127,
                error_message=f"未找到命令: {command.split()[0]}",
                duration=duration
            )

        except Exception as e:
            duration = time.time() - start_time
            return ExecutionResult(
                status="error",
                output="",
                command_executed=" ".join([command] + args),
                exit_code=1,
                error_message=f"执行异常: {str(e)}",
                duration=duration
            )

    def _sanitize_argument(self, arg: str) -> str:
        """清理命令参数，移除潜在危险字符"""
        # 移除或转义危险字符
        dangerous_chars = ['`', '$', ';', '&', '|', '>', '<', '(', ')', '{', '}', '\\']
        sanitized = arg
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')
        return sanitized.strip()

    def execute_with_confirmation(
        self, 
        route_result: dict, 
        skip_confirm: bool = False
    ) -> dict:
        """
        带确认的执行命令
        
        Args:
            route_result: 路由结果
            skip_confirm: 跳过确认提示
        
        Returns:
            ExecutionResult 的字典表示
        """
        try:
            command = route_result.get("command", "")
            args = route_result.get("args", [])
            confidence = route_result.get("confidence", 0.0)
            explanation = route_result.get("explanation", "")
            
            full_command = f"{command} {' '.join(args)}".strip()

            # 根据置信度和设置决定是否确认
            if not skip_confirm and self._should_confirm(confidence):
                confirmed = self._get_user_confirmation(
                    full_command, explanation, confidence
                )
                if not confirmed:
                    return ExecutionResult(
                        status="cancelled",
                        output="",
                        command_executed=full_command,
                        error_message="用户取消执行"
                    ).__dict__

            # 执行命令
            return self.execute(route_result)

        except Exception as e:
            return ExecutionResult(
                status="error",
                output="",
                command_executed=route_result.get("command", ""),
                error_message=f"确认流程错误: {str(e)}"
            ).__dict__

    def _should_confirm(self, confidence: float) -> bool:
        """判断是否需要用户确认"""
        return confidence < 0.8  # 置信度低于 80% 需要确认

    def _get_user_confirmation(
        self, 
        command: str, 
        explanation: str, 
        confidence: float
    ) -> bool:
        """获取用户确认"""
        if confidence < 0.5:
            # 低置信度：强制确认
            self.console.print(Panel(
                f"[yellow]⚠️  我不太确定你要执行的操作[/yellow]\n\n"
                f"[white]准备执行：[cyan]{command}[/cyan][/white]\n"
                f"[white]说明：{explanation}[/white]\n"
                f"[white]置信度：{confidence:.1%}[/white]\n\n"
                f"[yellow]请仔细确认是否要继续执行此操作。[/yellow]",
                title="🤔 需要确认",
                border_style="yellow"
            ))
            return Confirm.ask("是否继续执行？", default=False)
        else:
            # 中置信度：默认确认
            self.console.print(Panel(
                f"[blue]即将执行：[cyan]{command}[/cyan][/blue]\n"
                f"[white]{explanation}[/white]\n"
                f"[dim]置信度：{confidence:.1%}[/dim]",
                title="✨ 执行确认",
                border_style="blue"
            ))
            return Confirm.ask("继续执行？", default=True)

    def dry_run(self, route_result: dict) -> dict:
        """
        干运行模式 - 只验证不执行
        
        Args:
            route_result: 路由结果
        
        Returns:
            验证结果字典
        """
        try:
            # 验证输入格式
            if not self._validate_route_result(route_result):
                return {
                    "valid": False,
                    "error": "无效的路由结果格式",
                    "command": ""
                }

            # 构建完整命令
            base_command = route_result["command"]
            args = route_result.get("args", [])
            full_command = f"{base_command} {' '.join(args)}".strip()

            # 安全验证
            if not self._validate_command_safety(full_command):
                return {
                    "valid": False,
                    "error": "命令被安全策略阻止",
                    "command": full_command
                }

            return {
                "valid": True,
                "command": full_command,
                "base_command": base_command,
                "args": args,
                "sanitized_args": [self._sanitize_argument(arg) for arg in args]
            }

        except Exception as e:
            return {
                "valid": False,
                "error": f"验证过程出错: {str(e)}",
                "command": route_result.get("command", "")
            }