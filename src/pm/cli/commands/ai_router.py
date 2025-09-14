"""
AI Router Command for PersonalManager

Implements natural language intent routing functionality.
Maps user utterances to PersonalManager commands with confidence scoring.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.json import JSON

from pm.routing.intent_matcher import IntentMatcher, MatchResult

console = Console()
ai_app = typer.Typer(name="ai", help="AI助手和自然语言处理工具")


@ai_app.command("route")
def route_command(
    utterance: str = typer.Argument(
        ...,
        help="自然语言输入，例如 '今天做什么'"
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="以JSON格式输出结果"
    ),
    patterns_file: Optional[str] = typer.Option(
        None,
        "--patterns",
        help="自定义交互模式文件路径"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose", "-v",
        help="显示详细信息"
    )
):
    """
    将自然语言输入路由到对应的PersonalManager命令

    示例:
        pm ai route "今天做什么"
        pm ai route "记录 完成项目文档" --json
        pm ai route "项目概览" --verbose
    """
    try:
        # Initialize intent matcher
        matcher = IntentMatcher(patterns_file)

        # Match intent
        result = matcher.match_intent(utterance)

        # Prepare output data
        output_data = {
            "intent": result.intent,
            "confidence": result.confidence,
            "command": result.command,
            "args": result.args,
            "confirm_message": result.confirm_message
        }

        if json_output:
            # Output as JSON
            console.print(JSON.from_data(output_data))
        else:
            # Output as formatted display
            _display_result(utterance, result, verbose)

    except FileNotFoundError as e:
        console.print(f"[red]错误: 找不到交互模式文件: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]路由处理出错: {e}[/red]")
        if verbose:
            console.print_exception()
        raise typer.Exit(1)


@ai_app.command("intents")
def list_intents(
    patterns_file: Optional[str] = typer.Option(
        None,
        "--patterns",
        help="自定义交互模式文件路径"
    )
):
    """列出所有支持的意图"""
    try:
        matcher = IntentMatcher(patterns_file)
        intents = matcher.get_supported_intents()

        console.print(Panel.fit("支持的意图列表", style="blue"))

        for intent_id in intents:
            description = matcher.get_intent_description(intent_id)
            console.print(f"• [bold blue]{intent_id}[/bold blue]: {description or 'No description'}")

    except Exception as e:
        console.print(f"[red]获取意图列表失败: {e}[/red]")
        raise typer.Exit(1)


def _display_result(utterance: str, result: MatchResult, verbose: bool = False):
    """Display routing result in formatted output"""

    # Determine confidence color
    if result.confidence >= 0.8:
        confidence_color = "green"
    elif result.confidence >= 0.5:
        confidence_color = "yellow"
    else:
        confidence_color = "red"

    # Main result panel
    console.print(Panel.fit(
        f"输入: [blue]{utterance}[/blue]\n"
        f"意图: [bold]{result.intent}[/bold]\n"
        f"置信度: [{confidence_color}]{result.confidence:.2f}[/{confidence_color}]\n"
        f"命令: [green]{result.command}[/green]",
        title="路由结果",
        border_style="blue"
    ))

    # Show confirmation message if present
    if result.confirm_message:
        console.print(Panel(
            result.confirm_message,
            title="确认消息",
            border_style="yellow"
        ))

    # Show detailed info in verbose mode
    if verbose and result.args:
        console.print(Panel.fit(
            JSON.from_data(result.args),
            title="提取的参数",
            border_style="dim"
        ))

    # Show recommendations based on confidence
    if result.confidence < 0.5:
        console.print(Panel(
            "置信度较低，建议:\n"
            "• 尝试更清晰的表达方式\n"
            "• 使用 'pm ai intents' 查看支持的意图\n"
            "• 检查输入是否包含必要信息",
            title="建议",
            border_style="red"
        ))


# Export the app for main CLI integration
def get_ai_app():
    """Get the AI app for integration with main CLI"""
    return ai_app


if __name__ == "__main__":
    ai_app()