"""Google Tasks同步命令 - Sprint 9-10核心功能"""

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from typing import Optional

from pm.core.config import PMConfig
from pm.integrations.google_tasks import GoogleTasksIntegration
from pm.agents.gtd_agent import GTDAgent

console = Console()


def sync_from_google_tasks() -> None:
    """从Google Tasks同步任务到GTD系统"""
    
    config = PMConfig()
    if not config.is_initialized():
        console.print(Panel(
            "[yellow]系统未初始化。请先运行 [cyan]pm setup[/cyan] 进行设置。",
            title="⚠️ 未初始化",
            border_style="yellow"
        ))
        return
    
    tasks_integration = GoogleTasksIntegration(config)
    
    # 检查认证状态
    if not tasks_integration.google_auth.is_google_authenticated():
        console.print(Panel(
            "[red]未通过Google认证。请先运行：[cyan]pm auth login google[/cyan]",
            title="❌ 认证错误",
            border_style="red"
        ))
        return
    
    console.print(Panel(
        "[cyan]📝 Google Tasks 同步[/cyan]\\n\\n"
        "正在从Google Tasks同步任务到GTD系统...",
        title="🔄 任务同步",
        border_style="blue"
    ))
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("同步Google Tasks...", total=None)
            
            added_count, updated_count, errors = tasks_integration.sync_tasks_from_google()
            
            progress.update(task, description="同步完成")
        
        # 显示同步结果
        if added_count > 0 or updated_count > 0:
            console.print(Panel(
                f"[green]✅ 同步成功！[/green]\\n\\n"
                f"• 新增任务: [cyan]{added_count}[/cyan] 个\\n"
                f"• 更新任务: [yellow]{updated_count}[/yellow] 个\\n\\n"
                "您可以通过以下命令查看：\\n"
                "• [cyan]pm next[/cyan] - 查看下一步行动\\n"
                "• [cyan]pm recommend[/cyan] - 获取智能推荐",
                title="🎉 同步完成",
                border_style="green"
            ))
        else:
            console.print(Panel(
                "[yellow]ℹ️ 没有需要同步的新任务或更新[/yellow]\\n\\n"
                "可能的原因：\\n"
                "• Google Tasks中没有新任务\\n"
                "• 任务已经是最新状态\\n"
                "• Google Tasks暂时无法访问",
                title="📋 同步结果",
                border_style="yellow"
            ))
        
        # 显示错误信息
        if errors:
            console.print(Panel(
                "[red]⚠️ 同步过程中遇到以下问题：[/red]\\n\\n" +
                "\\n".join([f"• {error}" for error in errors]),
                title="❗ 警告",
                border_style="red"
            ))
    
    except Exception as e:
        console.print(Panel(
            f"[red]❌ 同步失败: {str(e)}[/red]",
            title="同步错误",
            border_style="red"
        ))


def sync_to_google_tasks(task_id: str) -> None:
    """将GTD任务同步到Google Tasks"""
    
    config = PMConfig()
    if not config.is_initialized():
        console.print(Panel(
            "[yellow]系统未初始化。请先运行 [cyan]pm setup[/cyan] 进行设置。",
            title="⚠️ 未初始化",
            border_style="yellow"
        ))
        return
    
    tasks_integration = GoogleTasksIntegration(config)
    agent = GTDAgent(config)
    
    # 检查认证状态
    if not tasks_integration.google_auth.is_google_authenticated():
        console.print(Panel(
            "[red]未通过Google认证。请先运行：[cyan]pm auth login google[/cyan]",
            title="❌ 认证错误",
            border_style="red"
        ))
        return
    
    # 获取任务
    task = agent.storage.get_task(task_id)
    if not task:
        console.print(Panel(
            f"[red]未找到任务ID: {task_id}[/red]\\n\\n"
            "请检查任务ID是否正确。",
            title="❌ 任务不存在",
            border_style="red"
        ))
        return
    
    # 检查是否已经从Google Tasks同步过来的任务
    if task.source == "google_tasks":
        console.print(Panel(
            "[yellow]该任务原本就来自Google Tasks[/yellow]\\n\\n"
            f"任务: {task.title}\\n"
            f"Google Tasks ID: {task.source_id}\\n\\n"
            "无需重复同步。",
            title="ℹ️ 任务信息",
            border_style="yellow"
        ))
        return
    
    # 同步到Google Tasks
    with console.status(f"[bold blue]将任务'{task.title[:30]}...'同步到Google Tasks...", spinner="dots"):
        success, message = tasks_integration.sync_task_to_google(task)
    
    if success:
        console.print(Panel(
            f"[green]✅ {message}[/green]\\n\\n"
            f"任务详情：\\n"
            f"• 标题: {task.title}\\n"
            f"• 上下文: @{task.context.value}\\n"
            f"• 优先级: {task.priority.value}\\n"
            f"• 截止时间: {task.due_date.strftime('%Y-%m-%d %H:%M') if task.due_date else 'N/A'}",
            title="🎉 同步成功",
            border_style="green"
        ))
    else:
        console.print(Panel(
            f"[red]❌ {message}[/red]",
            title="同步失败",
            border_style="red"
        ))


def show_google_tasks_lists() -> None:
    """显示Google Tasks列表"""
    
    config = PMConfig()
    if not config.is_initialized():
        console.print(Panel(
            "[yellow]系统未初始化。请先运行 [cyan]pm setup[/cyan] 进行设置。",
            title="⚠️ 未初始化",
            border_style="yellow"
        ))
        return
    
    tasks_integration = GoogleTasksIntegration(config)
    
    # 检查认证状态
    if not tasks_integration.google_auth.is_google_authenticated():
        console.print(Panel(
            "[red]未通过Google认证。请先运行：[cyan]pm auth login google[/cyan]",
            title="❌ 认证错误",
            border_style="red"
        ))
        return
    
    with console.status("[bold blue]获取Google Tasks列表...", spinner="dots"):
        task_lists = tasks_integration.get_google_tasks_lists()
    
    if not task_lists:
        console.print(Panel(
            "[yellow]📝 没有找到Google Tasks列表[/yellow]\\n\\n"
            "请检查Google Tasks服务是否正常。",
            title="📋 任务列表",
            border_style="yellow"
        ))
        return
    
    # 创建列表表格
    lists_table = Table(show_header=True, header_style="bold magenta")
    lists_table.add_column("列表ID", style="cyan", width=20)
    lists_table.add_column("列表名称", style="white")
    lists_table.add_column("最后更新", style="yellow", width=20)
    
    for task_list in task_lists:
        list_id = task_list.get('id', 'N/A')
        list_title = task_list.get('title', '未命名')
        updated = task_list.get('updated', 'N/A')
        
        # 格式化更新时间
        if updated != 'N/A':
            try:
                from datetime import datetime
                updated_dt = datetime.fromisoformat(updated.replace('Z', '+00:00'))
                updated = updated_dt.strftime('%Y-%m-%d %H:%M')
            except:
                pass
        
        lists_table.add_row(list_id, list_title, updated)
    
    console.print(Panel(
        lists_table,
        title="📝 Google Tasks 列表",
        border_style="blue"
    ))
    
    # 显示操作提示
    console.print(Panel(
        "[dim]💡 相关命令:\\n"
        "• [cyan]pm tasks sync-from[/cyan] - 从默认列表同步任务\\n"
        "• [cyan]pm tasks sync-to <任务ID>[/cyan] - 将任务同步到Google Tasks\\n"
        "• [cyan]pm next[/cyan] - 查看同步后的任务[/dim]",
        border_style="dim"
    ))


def show_sync_status() -> None:
    """显示Google Tasks同步状态"""
    
    config = PMConfig()
    if not config.is_initialized():
        console.print(Panel(
            "[yellow]系统未初始化。请先运行 [cyan]pm setup[/cyan] 进行设置。",
            title="⚠️ 未初始化",
            border_style="yellow"
        ))
        return
    
    agent = GTDAgent(config)
    tasks_integration = GoogleTasksIntegration(config)
    
    # 检查认证状态
    if not tasks_integration.google_auth.is_google_authenticated():
        console.print(Panel(
            "[red]未通过Google认证。请先运行：[cyan]pm auth login google[/cyan]",
            title="❌ 认证错误",
            border_style="red"
        ))
        return
    
    with console.status("[bold blue]分析同步状态...", spinner="dots"):
        all_tasks = agent.storage.get_all_tasks()
        
        # 统计不同来源的任务
        google_tasks_count = len([t for t in all_tasks if t.source == "google_tasks"])
        local_tasks_count = len([t for t in all_tasks if t.source != "google_tasks"])
        total_tasks = len(all_tasks)
    
    # 创建统计表格
    stats_table = Table(show_header=True, header_style="bold magenta")
    stats_table.add_column("任务来源", style="cyan")
    stats_table.add_column("数量", style="green", justify="center")
    stats_table.add_column("占比", style="yellow", justify="center")
    
    if total_tasks > 0:
        google_percentage = (google_tasks_count / total_tasks) * 100
        local_percentage = (local_tasks_count / total_tasks) * 100
    else:
        google_percentage = 0
        local_percentage = 0
    
    stats_table.add_row(
        "Google Tasks",
        str(google_tasks_count),
        f"{google_percentage:.1f}%"
    )
    stats_table.add_row(
        "本地创建",
        str(local_tasks_count),
        f"{local_percentage:.1f}%"
    )
    stats_table.add_row(
        "[bold]总计[/bold]",
        f"[bold]{total_tasks}[/bold]",
        "[bold]100%[/bold]"
    )
    
    console.print(Panel(
        stats_table,
        title="📊 任务同步统计",
        border_style="blue"
    ))
    
    # 显示同步建议
    if google_tasks_count == 0:
        console.print(Panel(
            "[yellow]🔄 建议执行首次同步[/yellow]\\n\\n"
            "看起来您还没有从Google Tasks同步任务。\\n"
            "运行以下命令开始同步：\\n"
            "[cyan]pm tasks sync-from[/cyan]",
            title="💡 同步建议",
            border_style="yellow"
        ))
    else:
        console.print(Panel(
            "[green]✅ 同步状态良好[/green]\\n\\n"
            f"您已同步了 {google_tasks_count} 个Google Tasks。\\n"
            "定期运行同步命令保持数据最新。",
            title="📈 同步状态",
            border_style="green"
        ))