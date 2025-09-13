"""用户偏好学习统计命令 - US-013验收标准（重构为AI可调用工具）"""

from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import typer

from pm.core.config import PMConfig
from pm.tools.preferences_tools import (
    get_preference_learning_stats,
    analyze_framework_preferences,
    analyze_context_preferences,
    get_learning_recommendations
)

console = Console()


def show_preference_learning_stats() -> None:
    """显示用户偏好学习统计（US-013验收标准）- 重构为使用AI可调用工具"""
    
    config = PMConfig()
    
    # 使用AI可调用工具获取偏好学习统计
    with console.status("[bold blue]分析用户偏好学习数据...", spinner="dots"):
        success, message, stats = get_preference_learning_stats(config)
    
    if not success:
        if "未初始化" in message:
            console.print(Panel(
                "[yellow]系统未初始化。请先运行 [cyan]pm setup[/cyan] 进行设置。",
                title="⚠️ 未初始化",
                border_style="yellow"
            ))
        else:
            console.print(Panel(
                f"[red]错误: {message}[/red]",
                title="❌ 处理失败",
                border_style="red"
            ))
        return
    
    # 显示学习概览
    _show_learning_overview(stats)
    
    # 显示理论框架偏好
    if stats['framework_analysis']['has_data']:
        _show_framework_preferences_from_data(stats['framework_analysis'])
    
    # 显示情境偏好
    if stats['context_analysis']['has_data']:
        _show_context_preferences_from_data(stats['context_analysis'])
    
    # 显示学习建议
    _show_learning_recommendations_from_data(stats['learning_recommendations'])
    
    # 操作提示
    console.print(Panel(
        "[dim]💡 相关命令:\n"
        "• [cyan]pm recommend[/cyan] - 获取个性化推荐\n"
        "• [cyan]pm learn[/cyan] - 查看分类学习统计\n"
        "• [cyan]pm complete <ID>[/cyan] - 完成任务（提供学习反馈）[/dim]",
        border_style="dim"
    ))


def _show_learning_overview(stats: dict) -> None:
    """显示学习概览"""
    console.print(Panel(
        f"[bold cyan]🧠 偏好学习引擎状态[/bold cyan]\n\n"
        f"• 学习状态: [yellow]{stats['learning_status']}[/yellow]\n"
        f"• 总选择次数: [green]{stats['total_choices']}[/green]\n"
        f"• 最近准确率: [blue]{stats['recent_accuracy']:.1%}[/blue]\n"
        f"• 学习趋势: [magenta]{stats['learning_trend']}[/magenta]\n"
        f"• 置信度评分: [cyan]{stats['confidence_score']:.2f}[/cyan]",
        title="📊 学习概览",
        border_style="blue"
    ))


def _show_framework_preferences_from_data(framework_analysis: dict) -> None:
    """显示理论框架偏好（基于AI可调用工具数据）"""
    
    console.print("\n[bold yellow]📚 理论框架偏好学习:[/bold yellow]\n")
    
    framework_table = Table(show_header=True, header_style="bold magenta")
    framework_table.add_column("理论框架", style="cyan")
    framework_table.add_column("学习权重", style="green", justify="center")
    framework_table.add_column("偏好强度", style="yellow", justify="center")
    
    for pref in framework_analysis['preferences_by_strength']:
        strength_colors = {
            "强偏好": "red",
            "中偏好": "yellow",
            "轻偏好": "blue",
            "低偏好": "dim"
        }
        strength_color = strength_colors.get(pref['strength'], "white")
        
        framework_table.add_row(
            pref['name'],
            f"{pref['weight']:.1%}",
            f"[{strength_color}]{pref['icon']} {pref['strength']}[/{strength_color}]"
        )
    
    console.print(framework_table)


def _show_context_preferences_from_data(context_analysis: dict) -> None:
    """显示情境偏好（基于AI可调用工具数据）"""
    
    console.print("\n[bold yellow]📍 情境偏好学习:[/bold yellow]\n")
    
    context_table = Table(show_header=True, header_style="bold cyan")
    context_table.add_column("执行情境", style="magenta")
    context_table.add_column("选择频率", style="green", justify="center")
    context_table.add_column("偏好等级", style="yellow", justify="center")
    
    for context in context_analysis['contexts_by_frequency']:
        level_colors = {
            "高频使用": "green",
            "常用": "yellow",
            "偶用": "blue"
        }
        level_color = level_colors.get(context['level'], "white")
        
        context_table.add_row(
            f"@{context['key']}",
            f"{context['frequency']:.1%}",
            f"[{level_color}]{context['icon']} {context['level']}[/{level_color}]"
        )
    
    console.print(context_table)


def _show_learning_recommendations_from_data(recommendations: dict) -> None:
    """显示学习建议（基于AI可调用工具数据）"""
    
    primary_msg = recommendations['primary_message']
    suggestions = recommendations['suggestions']
    next_actions = recommendations['next_actions']
    
    # 根据主要消息确定样式
    if "优秀" in primary_msg:
        title = "✨ 学习成果"
        border_style = "green"
        msg_color = "green"
        icon = "🎯"
    elif "学习之旅" in primary_msg:
        title = "🎓 学习指南"
        border_style = "yellow"
        msg_color = "yellow"
        icon = "🚀"
    else:
        title = "🔄 学习进展"
        border_style = "blue"
        msg_color = "blue"
        icon = "📈"
    
    # 构建面板内容
    content_lines = [f"[{msg_color}]{icon} {primary_msg}[/{msg_color}]", ""]
    
    # 添加建议
    for suggestion in suggestions:
        content_lines.append(suggestion)
    
    if next_actions:
        content_lines.append("")
        if len(next_actions) == 1:
            content_lines.append(next_actions[0])
        else:
            content_lines.append("建议操作：")
            for action in next_actions:
                content_lines.append(f"• {action}")
    
    console.print(Panel(
        "\n".join(content_lines),
        title=title,
        border_style=border_style
    ))