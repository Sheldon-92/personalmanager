"""推荐逻辑解释命令 - US-012可解释AI实现（重构为AI可调用工具）"""

from typing import Optional, Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, BarColumn, TextColumn
from rich.text import Text
import typer

from pm.core.config import PMConfig
from pm.tools.explain_tools import (
    explain_task_recommendation,
    get_framework_scoring_details,
    generate_recommendation_reasoning
)

console = Console()


def explain_recommendation(task_id: str) -> None:
    """解释任务推荐的逻辑（US-012核心功能）- 重构为使用AI可调用工具
    
    提供可解释的AI推荐，展示：
    - 各理论框架的评分详情
    - 推荐逻辑的步骤分析
    - 涉及的书籍理论说明
    - 评分计算过程透明化
    """
    
    config = PMConfig()
    
    # 使用AI可调用工具获取推荐解释
    with console.status("[bold blue]分析推荐逻辑...", spinner="dots"):
        success, message, data = explain_task_recommendation(task_id, config)
    
    if not success:
        if "未初始化" in message:
            console.print(Panel(
                "[yellow]系统未初始化。请先运行 [cyan]pm setup[/cyan] 进行设置。",
                title="⚠️ 未初始化",
                border_style="yellow"
            ))
        elif "未找到任务ID" in message:
            console.print(Panel(
                f"[red]{message}[/red]\n\n"
                "请确认任务ID正确，或使用以下命令查看任务：\n"
                "• [cyan]pm next[/cyan] - 查看所有下一步行动\n"
                "• [cyan]pm inbox[/cyan] - 查看收件箱任务",
                title="❌ 任务未找到",
                border_style="red"
            ))
        else:
            console.print(Panel(
                f"[red]错误: {message}[/red]",
                title="❌ 处理失败",
                border_style="red"
            ))
        return
    
    # 显示任务基本信息
    task_info = data['task_info']
    console.print(Panel(
        f"[bold cyan]📝 任务: {task_info['title']}[/bold cyan]\n\n"
        f"• 描述: {task_info['description'] or '无描述'}\n"
        f"• 情境: {task_info['context'] or '未设置'}\n"
        f"• 优先级: {task_info['priority'] or '未设置'}\n"
        f"• 精力需求: {task_info['energy_required'] or '未设置'}\n"
        f"• 预估时长: {task_info['estimated_duration']}分钟" if task_info['estimated_duration'] else "• 预估时长: 未设置",
        title="🔍 任务详情",
        border_style="cyan"
    ))
    
    # 显示推荐总分和置信度
    analysis = data['recommendation_analysis']
    total_score = analysis['total_score']
    confidence = analysis['confidence']
    
    score_color = "green" if total_score >= 7.0 else "yellow" if total_score >= 5.0 else "red"
    confidence_color = "green" if confidence >= 0.7 else "yellow" if confidence >= 0.5 else "red"
    
    console.print(Panel(
        f"[bold]📊 智能推荐评估结果[/bold]\n\n"
        f"• 综合评分: [{score_color}]{total_score:.2f}/10[/{score_color}]\n"
        f"• 推荐置信度: [{confidence_color}]{confidence:.0%}[/{confidence_color}]\n"
        f"• 紧迫性因子: {analysis['urgency_factor']:.2f}\n"
        f"• 精力匹配度: {analysis['energy_match']:.2f}",
        title="🎯 总体评估",
        border_style="blue"
    ))
    
    # 详细理论框架分析
    _show_framework_analysis_from_data(data['framework_details'], analysis['framework_scores'])
    
    # 显示推荐逻辑步骤
    _show_reasoning_steps_from_data(data['reasoning_steps'])
    
    # 显示理论框架说明
    _show_theory_explanations_from_data(data['theory_explanations'])
    
    # 操作建议
    console.print(Panel(
        f"[dim]💡 基于分析结果的建议:\n\n"
        f"{'🎯 强烈推荐立即执行' if total_score >= 7.0 else '📋 建议优先考虑' if total_score >= 5.0 else '🤔 可考虑延后处理'}\n\n"
        "相关命令:\n"
        "• [cyan]pm recommend[/cyan] - 查看智能推荐列表\n"
        "• [cyan]pm next[/cyan] - 查看所有下一步行动\n"
        "• [cyan]pm complete <ID>[/cyan] - 标记任务完成[/dim]",
        border_style="dim"
    ))


def _show_framework_analysis_from_data(framework_details: Dict[str, Dict[str, Any]], framework_scores: Dict[str, float]) -> None:
    """显示理论框架分析详情（基于AI可调用工具数据）"""
    
    # 创建理论框架评分表
    table = Table(show_header=True, header_style="bold magenta", title="📚 理论框架评分详情")
    table.add_column("理论框架", style="cyan", width=20)
    table.add_column("评分", style="green", width=8, justify="center")
    table.add_column("评级", style="yellow", width=8, justify="center")
    table.add_column("权重", style="blue", width=8, justify="center")
    table.add_column("贡献分", style="magenta", width=10, justify="center")
    
    for framework_key, details in framework_details.items():
        # 评分等级颜色
        grade_colors = {
            "优秀": "green",
            "良好": "yellow", 
            "一般": "orange",
            "较低": "red"
        }
        grade_color = grade_colors.get(details['grade'], "white")
        
        table.add_row(
            details['name'],
            f"{details['score']:.2f}",
            f"[{grade_color}]{details['grade']}[/{grade_color}]",
            f"{details['weight']:.0%}",
            f"{details['contribution']:.3f}"
        )
    
    console.print(table)
    
    # 显示评分进度条
    console.print("\n[bold]📈 各理论框架评分可视化:[/bold]\n")
    
    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=40),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
        expand=True
    ) as progress:
        
        for framework_key, details in framework_details.items():
            framework_name = details['name']
            task_prog = progress.add_task(f"{framework_name[:12]:<12}", total=1.0)
            progress.update(task_prog, completed=details['score'])


def _show_reasoning_steps_from_data(reasoning_steps: list[str]) -> None:
    """显示推荐逻辑推理步骤（基于AI可调用工具数据）"""
    
    if reasoning_steps:
        reasoning_text = "\n".join(f"• ✅ {step}" for step in reasoning_steps)
        console.print(Panel(
            f"[bold]🧠 推荐逻辑分析步骤[/bold]\n\n{reasoning_text}",
            title="💭 智能推理过程",
            border_style="magenta"
        ))


def _show_theory_explanations_from_data(theory_explanations: Dict[str, Dict[str, Any]]) -> None:
    """显示理论框架详细说明（基于AI可调用工具数据）"""
    
    if not theory_explanations:
        return
    
    console.print("\n[bold yellow]📖 相关理论框架详细说明:[/bold yellow]\n")
    
    for framework_key, details in theory_explanations.items():
        console.print(Panel(
            f"[bold cyan]{details['concept']}[/bold cyan]\n"
            f"[dim]来源: {details['book']}[/dim]\n\n"
            f"{details['description']}\n\n"
            f"[yellow]评估因素:[/yellow] {', '.join(details['factors'])}\n"
            f"[green]当前评分: {details['score']:.2f}/1.0[/green]",
            border_style="cyan",
            width=80
        ))