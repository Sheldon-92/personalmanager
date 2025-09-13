"""Task management CLI commands for GTD workflow."""

from typing import Optional, List
from pathlib import Path
import os
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
import typer

from pm.core.config import PMConfig
from pm.agents.gtd_agent import GTDAgent
from pm.models.task import Task, TaskStatus, TaskContext, TaskPriority, EnergyLevel

console = Console()


def capture_task(content: str) -> None:
    """快速捕获任务到收件箱
    
    根据US-005验收标准实现：
    - 通过 `/pm capture "任务内容"` 快速添加任务
    - 支持多行文本输入
    - 任务自动进入"收件箱"待处理列表
    - 命令执行时间不超过1秒
    """
    
    config = PMConfig()
    if not config.is_initialized():
        console.print(Panel(
            "[yellow]系统未初始化。请先运行 [cyan]pm setup[/cyan] 进行设置。",
            title="⚠️ 未初始化",
            border_style="yellow"
        ))
        return
    
    # 解析多行输入
    if "\\n" in content:
        lines = content.replace("\\n", "\n").split("\n")
        title = lines[0].strip()
        description = "\n".join(lines[1:]).strip() if len(lines) > 1 else None
    else:
        title = content.strip()
        description = None
    
    if not title:
        console.print("[red]任务内容不能为空")
        return
    
    # 初始化GTD Agent
    agent = GTDAgent(config)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
    ) as progress:
        task = progress.add_task("正在捕获任务...", total=None)
        
        try:
            # 收集捕获上下文（US-006要求）
            capture_context = {
                'source': 'cli',
                'location': str(Path.cwd()) if Path.cwd().exists() else None,
                'device': os.uname().nodename if hasattr(os, 'uname') else 'unknown'
            }
            
            # 捕获任务
            new_task = agent.capture_task(
                title=title,
                description=description,
                capture_context=capture_context
            )
            
            progress.update(task, description="任务捕获成功")
            
        except Exception as e:
            console.print(Panel(
                f"[red]任务捕获失败: {str(e)}",
                title="❌ 错误",
                border_style="red"
            ))
            return
    
    # 显示捕获结果
    console.print(Panel(
        f"[green]✅ 任务已成功捕获到收件箱！\n\n"
        f"[bold]任务标题:[/bold] {new_task.title}\n"
        f"[bold]任务ID:[/bold] {new_task.id[:8]}...\n"
        f"[bold]捕获时间:[/bold] {new_task.created_at.strftime('%Y-%m-%d %H:%M:%S')}",
        title="🎉 捕获成功",
        border_style="green"
    ))
    
    # 显示智能建议
    suggestions = []
    if new_task.project_name:
        suggestions.append(f"🔗 已关联到项目: {new_task.project_name}")
    
    if new_task.suggested_context:
        suggestions.append(f"💡 建议情境: {new_task.suggested_context}")
    
    if new_task.suggested_priority:
        suggestions.append(f"📊 建议优先级: {new_task.suggested_priority.value}")
    
    if suggestions:
        console.print(Panel(
            "\n".join(suggestions),
            title="🤖 智能建议",
            border_style="blue"
        ))
    
    # 操作提示
    console.print(Panel(
        "[bold blue]💡 下一步操作：\n\n"
        "• [cyan]pm inbox[/cyan] - 查看收件箱所有任务\n"
        "• [cyan]pm clarify[/cyan] - 开始理清任务流程\n"
        f"• [cyan]pm task {new_task.id[:8]}[/cyan] - 查看此任务详情",
        title="操作建议",
        border_style="blue"
    ))


def show_inbox() -> None:
    """显示收件箱任务列表"""
    
    config = PMConfig()
    agent = GTDAgent(config)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
    ) as progress:
        task = progress.add_task("正在加载收件箱...", total=None)
        
        try:
            inbox_tasks = agent.get_inbox_tasks()
            progress.update(task, description="加载完成")
        except Exception as e:
            console.print(Panel(
                f"[red]加载收件箱失败: {str(e)}",
                title="❌ 错误",
                border_style="red"
            ))
            return
    
    if not inbox_tasks:
        console.print(Panel(
            "[green]🎉 收件箱为空！\n\n"
            "所有任务都已理清。这是GTD的理想状态！\n\n"
            "使用 [cyan]pm capture \"新任务\"[/cyan] 捕获新的想法或任务",
            title="📥 收件箱",
            border_style="green"
        ))
        return
    
    # 显示收件箱标题
    console.print(Panel(
        f"[bold blue]📥 收件箱 ({len(inbox_tasks)} 个待理清任务)\n\n"
        "[dim]根据GTD原则，收件箱应该定期清空。建议使用 pm clarify 开始理清流程。",
        title="收件箱",
        border_style="blue"
    ))
    
    # 创建任务列表表格
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("序号", justify="center", style="dim", min_width=4)
    table.add_column("任务", style="white", min_width=30)
    table.add_column("捕获时间", style="dim", min_width=12)
    table.add_column("项目关联", style="green", min_width=15)
    table.add_column("建议", style="yellow", min_width=10)
    
    for i, task in enumerate(inbox_tasks, 1):
        # 任务标题（截断长标题）
        title = task.title
        if len(title) > 50:
            title = title[:47] + "..."
        
        # 捕获时间
        capture_time = task.created_at.strftime("%m-%d %H:%M")
        
        # 项目关联
        project = task.project_name or "[dim]无[/dim]"
        
        # 智能建议
        suggestions = []
        if task.suggested_context:
            suggestions.append(task.suggested_context.value)
        if task.suggested_priority and task.suggested_priority != TaskPriority.MEDIUM:
            suggestions.append(task.suggested_priority.value)
        
        suggestion_text = ", ".join(suggestions) if suggestions else "[dim]无[/dim]"
        
        table.add_row(
            str(i),
            title,
            capture_time,
            project,
            suggestion_text
        )
    
    console.print(table)
    
    # 收件箱健康度提醒
    if len(inbox_tasks) > 20:
        console.print(Panel(
            "[red]⚠️ 收件箱溢出警告！\n\n"
            f"收件箱有 {len(inbox_tasks)} 个未理清任务，建议立即开始理清流程。\n"
            "GTD的核心原则是保持收件箱清空，这样才能保持\"心如止水\"的状态。",
            title="🚨 注意",
            border_style="red"
        ))
    elif len(inbox_tasks) > 10:
        console.print(Panel(
            "[yellow]📝 建议理清任务\n\n"
            f"收件箱有 {len(inbox_tasks)} 个任务待理清。\n"
            "建议抽时间进行理清，确定每个任务的下一步行动。",
            title="💡 提醒",
            border_style="yellow"
        ))
    
    # 操作提示
    console.print(Panel(
        "[bold blue]💡 可用操作：\n\n"
        "• [cyan]pm clarify[/cyan] - 开始交互式理清流程\n"
        "• [cyan]pm task <ID>[/cyan] - 查看特定任务详情\n"
        "• [cyan]pm capture \"新任务\"[/cyan] - 添加新任务到收件箱",
        title="操作选项",
        border_style="blue"
    ))


def show_next_actions(context: Optional[str] = None) -> None:
    """显示下一步行动列表
    
    根据US-009验收标准实现：
    - 通过 `/pm next` 显示所有情境的下一步行动
    - 通过 `/pm next @电脑` 显示特定情境的行动
    - 按优先级排序显示
    - 显示预估时间和精力需求
    """
    
    config = PMConfig()
    agent = GTDAgent(config)
    
    # 解析情境参数
    task_context = None
    if context:
        # 尝试匹配情境
        context_mapping = {
            "@电脑": TaskContext.COMPUTER,
            "@电话": TaskContext.PHONE,
            "@外出": TaskContext.ERRANDS,
            "@家": TaskContext.HOME,
            "@办公室": TaskContext.OFFICE,
            "@网络": TaskContext.ONLINE,
            "@等待": TaskContext.WAITING,
            "@阅读": TaskContext.READING,
            "@会议": TaskContext.MEETING,
            "@专注": TaskContext.FOCUS
        }
        
        task_context = context_mapping.get(context)
        if not task_context:
            console.print(f"[red]未知情境: {context}")
            console.print("可用情境: " + ", ".join(context_mapping.keys()))
            return
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
    ) as progress:
        task = progress.add_task("正在加载下一步行动...", total=None)
        
        try:
            next_actions = agent.get_next_actions(task_context)
            progress.update(task, description="加载完成")
        except Exception as e:
            console.print(Panel(
                f"[red]加载下一步行动失败: {str(e)}",
                title="❌ 错误",
                border_style="red"
            ))
            return
    
    # 标题
    if task_context:
        title = f"⚡ 下一步行动 - {context} ({len(next_actions)} 个任务)"
    else:
        title = f"⚡ 所有下一步行动 ({len(next_actions)} 个任务)"
    
    if not next_actions:
        console.print(Panel(
            "[yellow]暂无下一步行动任务。\n\n"
            "可能的原因：\n"
            "• 收件箱中的任务尚未理清\n"
            "• 所有任务已完成\n"
            "• 指定情境下没有可执行任务\n\n"
            "建议使用 [cyan]pm clarify[/cyan] 理清收件箱任务",
            title="📋 下一步行动",
            border_style="yellow"
        ))
        return
    
    console.print(Panel(
        f"[bold blue]{title}",
        title="下一步行动",
        border_style="blue"
    ))
    
    # 创建下一步行动表格
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("优先级", justify="center", style="white", min_width=8)
    table.add_column("任务", style="white", min_width=35)
    table.add_column("情境", justify="center", style="cyan", min_width=10)
    table.add_column("项目", style="green", min_width=15)
    table.add_column("时间", justify="center", style="yellow", min_width=8)
    table.add_column("精力", justify="center", style="magenta", min_width=6)
    
    for task in next_actions:
        # 优先级
        priority_text = f"{task.get_priority_emoji()} {task.priority.value}"
        
        # 任务标题
        title = task.title
        if len(title) > 45:
            title = title[:42] + "..."
        
        # 情境
        context_text = f"{task.get_context_emoji()}" if task.context else "📋"
        
        # 项目
        project = task.project_name or "[dim]无[/dim]"
        if len(project) > 12:
            project = project[:9] + "..."
        
        # 预估时间
        duration = f"{task.estimated_duration}分" if task.estimated_duration else "[dim]未知[/dim]"
        
        # 精力需求
        energy = f"{task.get_energy_emoji()}" if task.energy_required else "🔋"
        
        table.add_row(
            priority_text,
            title,
            context_text,
            project,
            duration,
            energy
        )
    
    console.print(table)
    
    # 智能推荐提示
    console.print(Panel(
        "[bold green]🤖 智能执行建议：\n\n"
        "• 高优先级任务优先执行\n"
        "• 根据当前精力水平选择合适任务\n"
        "• 相同情境的任务可以批量处理\n"
        "• 预估时间短的任务可以快速完成",
        title="执行建议",
        border_style="green"
    ))
    
    # 操作提示
    console.print(Panel(
        "[bold blue]💡 可用操作：\n\n"
        "• [cyan]pm task <ID>[/cyan] - 查看任务详情\n"
        "• [cyan]pm complete <ID>[/cyan] - 标记任务为完成\n"
        "• [cyan]pm next @电脑[/cyan] - 查看特定情境任务\n"
        "• [cyan]pm recommend[/cyan] - 获取智能任务推荐",
        title="操作选项",
        border_style="blue"
    ))


def show_classification_stats() -> None:
    """显示智能分类学习统计信息（US-008验收标准）- 重构为使用AI可调用工具"""
    
    from pm.tools.learn_tools import get_classification_learning_stats
    
    config = PMConfig()
    
    # 使用AI可调用工具获取分类学习统计
    with console.status("[bold blue]分析分类学习数据...", spinner="dots"):
        success, message, stats = get_classification_learning_stats(config)
    
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
    _show_classification_overview_from_data(stats)
    
    # 显示学习阶段信息
    if 'learning_stage' in stats:
        _show_learning_stage_from_data(stats['learning_stage'])
    
    # 显示情境模式详情
    if stats['context_patterns']:
        _show_context_patterns_from_data(stats['context_patterns'])
    
    # 显示学习建议
    if 'improvement_suggestions' in stats:
        _show_learning_suggestions_from_data(stats['improvement_suggestions'])
    
    # 显示学习里程碑
    if 'learning_milestones' in stats:
        _show_learning_milestones_from_data(stats['learning_milestones'])


def _show_classification_overview_from_data(stats: dict) -> None:
    """显示分类学习概览（基于AI可调用工具数据）"""
    
    # 创建统计表
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("指标", style="cyan")
    table.add_column("值", style="green")
    table.add_column("状态", style="yellow")
    
    # 基础统计
    table.add_row(
        "已学习任务数", 
        str(stats['total_learned_tasks']),
        "🟢 良好" if stats['total_learned_tasks'] >= 10 else "🟡 学习中"
    )
    
    table.add_row(
        "学习模式数",
        str(stats['learned_patterns']),
        "🟢 丰富" if stats['learned_patterns'] >= 5 else "🟡 积累中"
    )
    
    # 准确率信息
    if 'accuracy_analysis' in stats:
        accuracy_info = stats['accuracy_analysis']
        accuracy_colors = {
            "优秀": "green",
            "良好": "yellow", 
            "一般": "orange",
            "需改进": "red",
            "无数据": "dim"
        }
        color = accuracy_colors.get(accuracy_info['level'], "white")
        
        table.add_row(
            "预测准确率", 
            accuracy_info['percentage'],
            f"[{color}]{'🟢' if accuracy_info['level'] == '优秀' else '🟡' if accuracy_info['level'] == '良好' else '🔴' if accuracy_info['level'] in ['一般', '需改进'] else '📚'} {accuracy_info['level']}[/{color}]"
        )
    
    # 系统健康状态
    health = stats['learning_health']
    health_display = {
        'learning': '📚 学习阶段',
        'excellent': '🌟 优秀',
        'good': '✅ 良好', 
        'fair': '🔄 一般',
        'needs_improvement': '⚠️ 需要改进'
    }.get(health, health)
    
    table.add_row("学习状态", health_display, "")
    
    console.print(Panel(
        table,
        title="🧠 智能分类学习统计",
        border_style="blue"
    ))


def _show_learning_stage_from_data(stage_data: dict) -> None:
    """显示学习阶段信息"""
    
    console.print(Panel(
        f"[bold cyan]{stage_data['stage']}[/bold cyan]\n\n"
        f"{stage_data['description']}\n\n"
        f"学习进度: [green]{stage_data['progress_percentage']:.1f}%[/green]",
        title="📈 学习阶段",
        border_style="cyan"
    ))


def _show_context_patterns_from_data(context_patterns: dict) -> None:
    """显示情境模式详情（基于AI可调用工具数据）"""
    
    console.print("\n[yellow]📊 已学习的情境模式:[/yellow]")
    
    patterns_table = Table(show_header=True, header_style="bold cyan")
    patterns_table.add_column("情境", style="magenta")
    patterns_table.add_column("关键词数量", style="green", justify="right")
    
    for context, count in context_patterns.items():
        patterns_table.add_row(context, str(count))
    
    console.print(patterns_table)


def _show_learning_suggestions_from_data(suggestions: dict) -> None:
    """显示学习建议（基于AI可调用工具数据）"""
    
    primary_action = suggestions['primary_action']
    suggestion_list = suggestions['suggestions']
    next_steps = suggestions['next_steps']
    
    # 根据主要行动确定样式
    if "积累" in primary_action:
        title = "🎓 学习指导"
        border_style = "blue"
        icon = "🚀"
    elif "提高" in primary_action or "改进" in primary_action:
        title = "🔧 改进建议" 
        border_style = "yellow"
        icon = "💡"
    else:
        title = "✨ 继续优化"
        border_style = "green"
        icon = "🎯"
    
    # 构建内容
    content_lines = [f"[bold]{icon} {primary_action}[/bold]", ""]
    
    # 添加说明
    for suggestion in suggestion_list:
        content_lines.append(suggestion)
    
    if next_steps:
        content_lines.append("")
        content_lines.append("建议步骤：")
        for step in next_steps:
            content_lines.append(f"• {step}")
    
    console.print(Panel(
        "\n".join(content_lines),
        title=title,
        border_style=border_style
    ))


def _show_learning_milestones_from_data(milestones: List[dict]) -> None:
    """显示学习里程碑"""
    
    console.print("\n[bold yellow]🏆 学习里程碑:[/bold yellow]")
    
    for milestone in milestones:
        status_icon = "✅" if milestone['achieved'] else "⏳"
        status_color = "green" if milestone['achieved'] else "dim"
        
        console.print(f"  {status_icon} [{status_color}]{milestone['milestone']}[/{status_color}] - {milestone['description']}")
        
        if not milestone['achieved']:
            if isinstance(milestone['target'], int):
                console.print(f"    [dim]目标: {milestone['target']}个任务[/dim]")
            else:
                console.print(f"    [dim]目标: {milestone['target']:.0%}准确率[/dim]")


def show_context_detection() -> None:
    """显示当前情境检测结果（US-010验收标准）"""
    
    config = PMConfig()
    if not config.is_initialized():
        console.print(Panel(
            "[yellow]系统未初始化。请先运行 [cyan]pm setup[/cyan] 进行设置。",
            title="⚠️ 未初始化",
            border_style="yellow"
        ))
        return
    
    agent = GTDAgent(config)
    
    with console.status("[bold blue]检测当前情境...", spinner="dots"):
        context_info = agent.detect_current_context()
    
    # 创建设备信息表
    device_table = Table(show_header=True, header_style="bold cyan")
    device_table.add_column("属性", style="yellow")
    device_table.add_column("值", style="green")
    
    device_info = context_info.get('device_info', {})
    device_table.add_row("设备类型", device_info.get('type', '未知').upper())
    device_table.add_row("操作系统", device_info.get('platform', '未知'))
    device_table.add_row("主机名", device_info.get('hostname', '未知'))
    
    # 网络状态
    network_info = context_info.get('network_info', {})
    online_status = "🟢 在线" if network_info.get('online', False) else "🔴 离线"
    device_table.add_row("网络状态", online_status)
    
    # 时间情境
    time_info = context_info.get('time_context', {})
    time_period = time_info.get('time_period', 'unknown')
    time_display = {
        'morning': '🌅 上午',
        'afternoon': '☀️ 下午',
        'evening': '🌆 傍晚',
        'night': '🌙 夜晚'
    }.get(time_period, time_period)
    
    device_table.add_row("时间段", time_display)
    device_table.add_row("是否周末", "🎉 是" if time_info.get('is_weekend', False) else "💼 否")
    
    console.print(Panel(
        device_table,
        title="🔍 情境检测结果",
        border_style="blue"
    ))
    
    # 显示建议情境
    suggested_contexts = context_info.get('suggested_contexts', [])
    if suggested_contexts:
        console.print("\n[yellow]💡 建议的执行情境:[/yellow]")
        
        context_display = []
        for ctx in suggested_contexts:
            context_display.append(f"• {ctx.value}")
        
        console.print("\n".join(context_display))
    
    # 显示位置线索
    location_hints = context_info.get('location_hints', {})
    if location_hints.get('working_directory'):
        console.print(f"\n[dim]📁 当前目录: {location_hints['working_directory']}[/dim]")


def show_smart_next_actions(context: Optional[str] = None, energy: Optional[str] = None) -> None:
    """显示智能情境过滤的下一步行动（US-010核心功能）"""
    
    config = PMConfig()
    if not config.is_initialized():
        console.print(Panel(
            "[yellow]系统未初始化。请先运行 [cyan]pm setup[/cyan] 进行设置。",
            title="⚠️ 未初始化",
            border_style="yellow"
        ))
        return
    
    agent = GTDAgent(config)
    
    # 解析参数
    context_filter = None
    if context:
        try:
            context_filter = TaskContext(context.replace("@", ""))
        except ValueError:
            console.print(f"[red]未知情境: {context}[/red]")
            return
    
    energy_filter = None
    if energy:
        try:
            energy_map = {
                'low': EnergyLevel.LOW,
                'medium': EnergyLevel.MEDIUM,
                'high': EnergyLevel.HIGH,
                '低': EnergyLevel.LOW,
                '中': EnergyLevel.MEDIUM,
                '高': EnergyLevel.HIGH
            }
            energy_filter = energy_map.get(energy.lower())
        except (ValueError, KeyError):
            console.print(f"[red]未知精力水平: {energy}[/red]")
            return
    
    with console.status("[bold blue]分析情境并筛选任务...", spinner="dots"):
        result = agent.get_context_filtered_tasks(
            auto_detect=True,
            context_override=context_filter,
            energy_level=energy_filter
        )
    
    filtered_tasks = result['filtered_tasks']
    stats = result['stats']
    detected_context = result.get('detected_context', {})
    
    # 显示检测到的情境信息
    if detected_context and not context_filter:
        suggested = detected_context.get('suggested_contexts', [])
        if suggested:
            context_names = [ctx.value for ctx in suggested]
            console.print(Panel(
                f"[green]🎯 检测到适合的情境: {', '.join(context_names)}[/green]\n"
                f"基于您的设备、时间和环境自动推荐",
                title="智能情境检测",
                border_style="green"
            ))
    
    # 显示筛选统计
    filter_info = f"显示 {stats['filtered_tasks']} / {stats['total_tasks']} 个任务"
    if stats['filter_ratio'] < 1.0:
        filter_info += f" (过滤率: {stats['filter_ratio']:.1%})"
    
    if not filtered_tasks:
        console.print(Panel(
            "[yellow]📝 当前情境下没有适合的任务！\n\n"
            f"• 总任务数: {stats['total_tasks']}\n"
            f"• 匹配情境: {', '.join([ctx.value for ctx in result['active_contexts']])}\n\n"
            "建议：\n"
            "• 使用 [cyan]pm next[/cyan] 查看所有任务\n"
            "• 使用 [cyan]pm smart-next @其他情境[/cyan] 切换情境\n"
            "• 使用 [cyan]pm capture[/cyan] 添加适合当前情境的任务",
            title="💡 智能建议",
            border_style="yellow"
        ))
        return
    
    # 创建任务表格
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("任务", style="cyan", width=40)
    table.add_column("情境", style="blue", width=12)
    table.add_column("优先级", style="yellow", width=8)
    table.add_column("精力", style="green", width=6)
    table.add_column("时长", style="dim", width=8)
    table.add_column("项目", style="magenta", width=15)
    
    for task in filtered_tasks:
        # 格式化任务标题
        title = task.title
        if len(title) > 35:
            title = title[:32] + "..."
        
        # 情境显示
        context_display = task.context.value if task.context else "-"
        
        # 优先级显示
        priority_icons = {
            TaskPriority.HIGH: "🔥 高",
            TaskPriority.MEDIUM: "📋 中", 
            TaskPriority.LOW: "📝 低"
        }
        priority_display = priority_icons.get(task.priority, "📋 中")
        
        # 精力需求显示
        energy_icons = {
            EnergyLevel.HIGH: "⚡",
            EnergyLevel.MEDIUM: "🔋",
            EnergyLevel.LOW: "🪫"
        }
        energy_display = energy_icons.get(task.energy_required, "-")
        
        # 预估时长
        duration = f"{task.estimated_duration}分" if task.estimated_duration else "-"
        
        # 项目名称
        project = task.project_name[:12] + "..." if task.project_name and len(task.project_name) > 15 else (task.project_name or "-")
        
        table.add_row(
            title,
            context_display,
            priority_display, 
            energy_display,
            duration,
            project
        )
    
    console.print(Panel(
        table,
        title=f"🚀 智能推荐行动 ({filter_info})",
        border_style="blue"
    ))
    
    # 显示操作提示
    console.print(Panel(
        "[dim]💡 使用技巧:\n"
        "• [cyan]pm smart-next @电脑[/cyan] - 指定情境筛选\n"
        "• [cyan]pm smart-next --energy low[/cyan] - 按精力水平筛选\n"
        "• [cyan]pm context[/cyan] - 查看当前情境检测\n"
        "• [cyan]pm task <ID>[/cyan] - 查看任务详情[/dim]",
        border_style="dim"
    ))


def show_intelligent_recommendations(context: Optional[str] = None, count: int = 5) -> None:
    """显示基于多书籍理论的智能任务推荐（US-011核心功能）"""
    
    config = PMConfig()
    if not config.is_initialized():
        console.print(Panel(
            "[yellow]系统未初始化。请先运行 [cyan]pm setup[/cyan] 进行设置。",
            title="⚠️ 未初始化",
            border_style="yellow"
        ))
        return
    
    agent = GTDAgent(config)
    
    # 解析情境参数
    context_filter = None
    if context:
        try:
            context_filter = TaskContext(context.replace("@", ""))
        except ValueError:
            console.print(f"[red]未知情境: {context}[/red]")
            return
    
    with console.status("[bold blue]分析任务并生成智能推荐...", spinner="dots"):
        recommendations = agent.get_intelligent_recommendations(
            max_recommendations=count,
            context_override=context_filter
        )
    
    if not recommendations:
        console.print(Panel(
            "[yellow]📝 暂无可推荐的任务！\n\n"
            "可能的原因：\n"
            "• 收件箱中的任务尚未理清为下一步行动\n"
            "• 指定情境下没有匹配的任务\n\n"
            "建议：\n"
            "• 使用 [cyan]pm clarify[/cyan] 理清收件箱任务\n"
            "• 使用 [cyan]pm next[/cyan] 查看所有下一步行动\n"
            "• 尝试不同的情境过滤",
            title="💡 智能推荐",
            border_style="yellow"
        ))
        return
    
    # 显示推荐理论介绍
    console.print(Panel(
        "[bold blue]🧠 基于多书籍理论的智能推荐[/bold blue]\n\n"
        "本推荐系统融合了以下管理理论：\n"
        "• [cyan]《衡量一切》[/cyan] - 目标对齐度评估\n"
        "• [cyan]《高效执行的4个原则》[/cyan] - 执行效率计算\n" 
        "• [cyan]《全力以赴》[/cyan] - 精力水平匹配\n"
        "• [cyan]《原子习惯》[/cyan] - 习惯建立贡献\n"
        "• [cyan]《搞定》[/cyan] - GTD方法论符合度\n"
        "• [cyan]《精要主义》[/cyan] - 本质重要性评估",
        title="🎯 智能推荐引擎",
        border_style="blue"
    ))
    
    # 创建推荐表格
    table = Table(show_header=True, header_style="bold magenta", title="📊 推荐任务列表")
    table.add_column("排名", style="yellow", width=4, justify="center")
    table.add_column("任务", style="cyan", width=35)
    table.add_column("综合评分", style="green", width=10, justify="center")
    table.add_column("置信度", style="blue", width=8, justify="center")
    table.add_column("情境", style="magenta", width=10)
    table.add_column("优先级", style="red", width=8)
    table.add_column("关键因素", style="dim", width=20)
    
    for idx, (task, score) in enumerate(recommendations, 1):
        # 格式化任务标题
        title = task.title
        if len(title) > 32:
            title = title[:29] + "..."
        
        # 评分显示
        score_display = f"{score.total_score:.1f}/10"
        score_color = (
            "green" if score.total_score >= 7.0 else
            "yellow" if score.total_score >= 5.0 else
            "red"
        )
        
        # 置信度显示  
        confidence_display = f"{score.confidence:.0%}"
        confidence_color = (
            "green" if score.confidence >= 0.7 else
            "yellow" if score.confidence >= 0.5 else
            "red"
        )
        
        # 情境显示
        context_display = task.context.value if task.context else "-"
        
        # 优先级显示
        priority_icons = {
            TaskPriority.HIGH: "🔥 高",
            TaskPriority.MEDIUM: "📋 中",
            TaskPriority.LOW: "📝 低"
        }
        priority_display = priority_icons.get(task.priority, "📋 中")
        
        # 关键因素
        key_factors = []
        if score.urgency_factor > 0.5:
            key_factors.append("紧急")
        if score.energy_match > 0.7:
            key_factors.append("精力匹配")
        
        # 找出得分最高的理论框架
        best_framework = max(score.framework_scores.items(), key=lambda x: x[1])
        if best_framework[1] > 0.7:
            framework_names = {
                "okr_wig": "目标对齐",
                "4dx": "执行效率", 
                "full_engagement": "精力匹配",
                "atomic_habits": "习惯建立",
                "gtd": "GTD原则",
                "essentialism": "本质重要"
            }
            key_factors.append(framework_names.get(best_framework[0].value, best_framework[0].value))
        
        key_factors_display = ", ".join(key_factors[:2]) if key_factors else "-"
        
        table.add_row(
            f"#{idx}",
            title,
            f"[{score_color}]{score_display}[/{score_color}]",
            f"[{confidence_color}]{confidence_display}[/{confidence_color}]",
            context_display,
            priority_display,
            key_factors_display
        )
    
    console.print(table)
    
    # 显示最佳推荐的详细信息
    if recommendations:
        best_task, best_score = recommendations[0]
        
        console.print(Panel(
            f"[bold green]🎯 最佳推荐: {best_task.title}[/bold green]\n\n"
            f"• 综合评分: [green]{best_score.total_score:.1f}/10[/green]\n"
            f"• 推荐置信度: [blue]{best_score.confidence:.0%}[/blue]\n"
            f"• 紧迫性: {'🔥 高' if best_score.urgency_factor > 0.5 else '📋 中等' if best_score.urgency_factor > 0.2 else '😌 较低'}\n"
            f"• 精力匹配: {'⚡ 优秀' if best_score.energy_match > 0.7 else '🔋 良好' if best_score.energy_match > 0.5 else '🪫 一般'}\n"
            f"• 推荐理由: {', '.join(best_score.reasoning) if best_score.reasoning else '综合评估推荐'}",
            title="💡 建议执行",
            border_style="green"
        ))
    
    # 操作提示
    console.print(Panel(
        "[dim]💡 使用技巧:\n"
        "• [cyan]pm recommend @电脑[/cyan] - 指定情境推荐\n"
        "• [cyan]pm recommend --count 10[/cyan] - 显示更多推荐\n"
        "• [cyan]pm explain <ID>[/cyan] - 查看推荐详细解释\n"
        "• [cyan]pm task <ID>[/cyan] - 查看任务详情[/dim]",
        border_style="dim"
    ))


def show_task_details(task_id: str) -> None:
    """显示任务详细信息"""
    
    config = PMConfig()
    agent = GTDAgent(config)
    
    # 支持短ID匹配
    all_tasks = agent.storage.get_all_tasks()
    matching_tasks = [t for t in all_tasks if t.id.startswith(task_id)]
    
    if not matching_tasks:
        console.print(Panel(
            f"[red]未找到任务: {task_id}",
            title="❌ 任务不存在",
            border_style="red"
        ))
        return
    
    if len(matching_tasks) > 1:
        console.print(Panel(
            f"[yellow]找到多个匹配的任务 ({len(matching_tasks)} 个):\n\n" +
            "\n".join([f"• {t.id[:8]}... - {t.title}" for t in matching_tasks[:5]]),
            title="⚠️ 多个匹配",
            border_style="yellow"
        ))
        return
    
    task = matching_tasks[0]
    
    # 任务基本信息
    console.print(Panel(
        f"[bold green]{task.get_priority_emoji()} {task.title}[/bold green]\n\n"
        f"[dim]任务ID: {task.id}[/dim]",
        title="📋 任务详情",
        border_style="green"
    ))
    
    # 创建详细信息表格
    info_table = Table(show_header=False, box=None, padding=(0, 2))
    info_table.add_column("项目", style="cyan", min_width=12)
    info_table.add_column("值", style="white")
    
    info_table.add_row("📊 状态", f"{task.status.value}")
    info_table.add_row("🔥 优先级", f"{task.get_priority_emoji()} {task.priority.value}")
    
    if task.context:
        info_table.add_row("🎯 情境", f"{task.get_context_emoji()} {task.context.value}")
    
    if task.energy_required:
        info_table.add_row("⚡ 精力需求", f"{task.get_energy_emoji()} {task.energy_required.value}")
    
    if task.estimated_duration:
        info_table.add_row("⏱️ 预估时长", f"{task.estimated_duration} 分钟")
    
    if task.project_name:
        info_table.add_row("🗂️ 关联项目", task.project_name)
    
    info_table.add_row("📅 创建时间", task.created_at.strftime("%Y-%m-%d %H:%M:%S"))
    info_table.add_row("🔄 更新时间", task.updated_at.strftime("%Y-%m-%d %H:%M:%S"))
    
    if task.due_date:
        info_table.add_row("⏰ 截止日期", task.due_date.strftime("%Y-%m-%d %H:%M:%S"))
    
    if task.completed_at:
        info_table.add_row("✅ 完成时间", task.completed_at.strftime("%Y-%m-%d %H:%M:%S"))
    
    console.print(info_table)
    
    # 任务描述
    if task.description:
        console.print(Panel(
            task.description,
            title="📝 任务描述",
            border_style="cyan"
        ))
    
    # 标签
    if task.tags:
        console.print(Panel(
            " ".join([f"#{tag}" for tag in task.tags]),
            title="🏷️ 标签",
            border_style="magenta"
        ))
    
    # 备注
    if task.notes:
        notes_text = "\n".join(task.notes[-5:])  # 显示最近5条备注
        console.print(Panel(
            notes_text,
            title=f"📄 备注 (最近{min(5, len(task.notes))}条)",
            border_style="yellow"
        ))
    
    # 捕获上下文
    if any([task.capture_source, task.capture_location, task.capture_device]):
        context_info = []
        if task.capture_source:
            context_info.append(f"来源: {task.capture_source}")
        if task.capture_location:
            context_info.append(f"位置: {Path(task.capture_location).name}")
        if task.capture_device:
            context_info.append(f"设备: {task.capture_device}")
        
        console.print(Panel(
            " | ".join(context_info),
            title="🔍 捕获上下文",
            border_style="dim"
        ))
    
    # 操作选项
    actions = []
    if task.status == TaskStatus.INBOX:
        actions.extend([
            "• [cyan]pm clarify[/cyan] - 理清此任务",
        ])
    elif task.status == TaskStatus.NEXT_ACTION:
        actions.extend([
            f"• [cyan]pm complete {task.id[:8]}[/cyan] - 标记为完成",
        ])
    
    actions.extend([
        f"• [cyan]pm edit {task.id[:8]}[/cyan] - 编辑任务",
        f"• [cyan]pm delete {task.id[:8]}[/cyan] - 删除任务",
    ])
    
    console.print(Panel(
        "[bold blue]💡 可用操作：\n\n" + "\n".join(actions),
        title="操作选项",
        border_style="blue"
    ))