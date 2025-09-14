"""AI执行命令模块 - pm ai execute 命令实现"""

import typer
import json
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.json import JSON

from pm.routing.command_executor import CommandExecutor
from pm.routing.ai_router import AIRouter


# 创建 AI 子应用
ai_app = typer.Typer(help="AI驱动的命令执行", rich_markup_mode="rich")

console = Console()


@ai_app.command("execute")
def ai_execute(
    utterance: str = typer.Argument(..., help="自然语言描述的任务"),
    skip_confirm: bool = typer.Option(False, "--yes", "-y", help="跳过确认提示，直接执行"),
    json_output: bool = typer.Option(False, "--json", help="输出JSON格式结果"),
    dry_run: bool = typer.Option(False, "--dry-run", help="仅验证命令，不实际执行")
) -> None:
    """
    使用AI将自然语言转换为PM命令并执行
    
    示例:
        pm ai execute "添加任务学习Python" 
        pm ai execute "查看今日推荐任务" --yes
        pm ai execute "创建新的读书习惯" --dry-run
    """
    try:
        executor = CommandExecutor()
        router = AIRouter()
        
        # Step 1: 解析自然语言意图
        route_result = router.route(utterance)
        
        if json_output:
            console.print(JSON.from_data({"route_result": route_result}))
        else:
            _display_route_result(route_result)
        
        # Step 2: 干运行模式
        if dry_run:
            validation_result = executor.dry_run(route_result)
            if json_output:
                console.print(JSON.from_data(validation_result))
            else:
                _display_dry_run_result(validation_result)
            return
        
        # Step 3: 执行命令
        if skip_confirm:
            execution_result = executor.execute(route_result)
        else:
            execution_result = executor.execute_with_confirmation(route_result, skip_confirm=False)
        
        # Step 4: 显示结果
        if json_output:
            console.print(JSON.from_data(execution_result))
        else:
            _display_execution_result(execution_result)
            
    except Exception as e:
        error_result = {
            "status": "error",
            "error_message": f"AI执行失败: {str(e)}",
            "output": "",
            "command_executed": ""
        }
        
        if json_output:
            console.print(JSON.from_data(error_result))
        else:
            console.print(Panel(
                f"[red]❌ AI执行失败[/red]\n"
                f"[white]错误: {str(e)}[/white]",
                title="执行错误",
                border_style="red"
            ))
        
        raise typer.Exit(1)




def _display_route_result(route_result: dict) -> None:
    """显示路由解析结果"""
    confidence = route_result.get("confidence", 0.0)
    confidence_color = "green" if confidence >= 0.8 else "yellow" if confidence >= 0.5 else "red"
    
    console.print(Panel(
        f"[blue]解析结果[/blue]\n"
        f"[white]命令: [cyan]{route_result.get('command', '')}[/cyan][/white]\n"
        f"[white]参数: {route_result.get('args', [])}[/white]\n"
        f"[white]说明: {route_result.get('explanation', '')}[/white]\n"
        f"[{confidence_color}]置信度: {confidence:.1%}[/{confidence_color}]",
        title="🤖 AI路由解析",
        border_style="blue"
    ))


def _display_dry_run_result(validation_result: dict) -> None:
    """显示干运行验证结果"""
    if validation_result.get("valid", False):
        console.print(Panel(
            f"[green]✅ 命令验证通过[/green]\n"
            f"[white]命令: [cyan]{validation_result.get('command', '')}[/cyan][/white]\n"
            f"[white]基础命令: {validation_result.get('base_command', '')}[/white]\n"
            f"[white]参数: {validation_result.get('args', [])}[/white]\n"
            f"[white]清理后参数: {validation_result.get('sanitized_args', [])}[/white]",
            title="🔍 干运行验证",
            border_style="green"
        ))
    else:
        console.print(Panel(
            f"[red]❌ 命令验证失败[/red]\n"
            f"[white]命令: [cyan]{validation_result.get('command', '')}[/cyan][/white]\n"
            f"[red]错误: {validation_result.get('error', '')}[/red]",
            title="🔍 干运行验证",
            border_style="red"
        ))


def _display_execution_result(execution_result: dict) -> None:
    """显示命令执行结果"""
    status = execution_result.get("status", "unknown")
    
    if status == "success":
        console.print(Panel(
            f"[green]✅ 执行成功[/green]\n"
            f"[white]命令: [cyan]{execution_result.get('command_executed', '')}[/cyan][/white]\n" +
            (f"[white]耗时: {execution_result.get('duration', 0):.2f}秒[/white]\n" if execution_result.get('duration') else "") +
            (f"[green]输出:[/green]\n{execution_result.get('output', '')}" if execution_result.get('output') else ""),
            title="🎉 执行结果",
            border_style="green"
        ))
    elif status == "cancelled":
        console.print(Panel(
            f"[yellow]⚠️ 执行已取消[/yellow]\n"
            f"[white]命令: [cyan]{execution_result.get('command_executed', '')}[/cyan][/white]\n"
            f"[yellow]原因: {execution_result.get('error_message', '')}[/yellow]",
            title="🚫 执行取消",
            border_style="yellow"
        ))
    else:  # error
        console.print(Panel(
            f"[red]❌ 执行失败[/red]\n"
            f"[white]命令: [cyan]{execution_result.get('command_executed', '')}[/cyan][/white]\n"
            f"[red]错误: {execution_result.get('error_message', '')}[/red]\n" +
            (f"[white]退出码: {execution_result.get('exit_code', 0)}[/white]" if execution_result.get('exit_code') else ""),
            title="❌ 执行失败",
            border_style="red"
        ))