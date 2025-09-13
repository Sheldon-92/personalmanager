"""Google Calendar集成命令 - Sprint 9-10核心功能"""

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from typing import Optional
from datetime import datetime

from pm.core.config import PMConfig
from pm.integrations.google_calendar import GoogleCalendarIntegration
from pm.agents.gtd_agent import GTDAgent

console = Console()


def sync_calendar() -> None:
    """同步Google Calendar到GTD任务"""
    
    config = PMConfig()
    if not config.is_initialized():
        console.print(Panel(
            "[yellow]系统未初始化。请先运行 [cyan]pm setup[/cyan] 进行设置。",
            title="⚠️ 未初始化",
            border_style="yellow"
        ))
        return
    
    calendar_integration = GoogleCalendarIntegration(config)
    
    # 检查认证状态
    if not calendar_integration.google_auth.is_google_authenticated():
        console.print(Panel(
            "[red]未通过Google认证。请先运行：[cyan]pm auth login google[/cyan]",
            title="❌ 认证错误",
            border_style="red"
        ))
        return
    
    console.print(Panel(
        "[cyan]📅 Google Calendar 同步[/cyan]\\n\\n"
        "正在同步未来3天的Google Calendar事件到GTD任务系统...",
        title="🔄 日程同步",
        border_style="blue"
    ))
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("同步Calendar事件...", total=None)
            
            synced_count, errors = calendar_integration.sync_calendar_to_tasks(days_ahead=3)
            
            progress.update(task, description="同步完成")
        
        # 显示同步结果
        if synced_count > 0:
            console.print(Panel(
                f"[green]✅ 同步成功！[/green]\\n\\n"
                f"• 已同步 [cyan]{synced_count}[/cyan] 个日程事件为GTD任务\\n"
                f"• 同步范围：未来3天\\n\\n"
                "您可以通过以下命令查看：\\n"
                "• [cyan]pm next[/cyan] - 查看下一步行动\\n"
                "• [cyan]pm smart-next[/cyan] - 智能推荐",
                title="🎉 同步完成",
                border_style="green"
            ))
        else:
            console.print(Panel(
                "[yellow]ℹ️ 未找到需要同步的新事件[/yellow]\\n\\n"
                "可能的原因：\\n"
                "• 未来3天没有新的日程安排\\n"
                "• 事件已经同步过了\\n"
                "• Google Calendar暂时无法访问",
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


def show_today_schedule() -> None:
    """显示今日日程"""
    
    config = PMConfig()
    if not config.is_initialized():
        console.print(Panel(
            "[yellow]系统未初始化。请先运行 [cyan]pm setup[/cyan] 进行设置。",
            title="⚠️ 未初始化",
            border_style="yellow"
        ))
        return
    
    calendar_integration = GoogleCalendarIntegration(config)
    
    # 检查认证状态
    if not calendar_integration.google_auth.is_google_authenticated():
        console.print(Panel(
            "[red]未通过Google认证。请先运行：[cyan]pm auth login google[/cyan]",
            title="❌ 认证错误",
            border_style="red"
        ))
        return
    
    with console.status("[bold blue]获取今日日程...", spinner="dots"):
        today_events = calendar_integration.get_today_schedule()
    
    if not today_events:
        console.print(Panel(
            "[yellow]📅 今天没有日程安排[/yellow]\\n\\n"
            "享受一个相对自由的一天！",
            title="📋 今日日程",
            border_style="yellow"
        ))
        return
    
    # 创建日程表格
    schedule_table = Table(show_header=True, header_style="bold magenta")
    schedule_table.add_column("时间", style="cyan", width=12)
    schedule_table.add_column("事件", style="white")
    schedule_table.add_column("时长", style="yellow", justify="center", width=8)
    schedule_table.add_column("地点/备注", style="dim", width=20)
    
    for event in today_events:
        start_time = event.start_time.strftime("%H:%M")
        end_time = event.end_time.strftime("%H:%M")
        time_range = f"{start_time}-{end_time}"
        
        duration = f"{event.duration_minutes}分钟"
        
        location_or_note = ""
        if event.location:
            location_or_note = f"📍 {event.location}"
        elif event.attendees:
            attendee_count = len(event.attendees)
            location_or_note = f"👥 {attendee_count}人"
        
        schedule_table.add_row(
            time_range,
            event.title,
            duration,
            location_or_note
        )
    
    console.print(Panel(
        schedule_table,
        title=f"📅 今日日程 ({datetime.now().strftime('%Y-%m-%d')})",
        border_style="blue"
    ))
    
    # 显示操作提示
    console.print(Panel(
        "[dim]💡 相关命令:\\n"
        "• [cyan]pm calendar sync[/cyan] - 同步日程为GTD任务\\n"
        "• [cyan]pm calendar week[/cyan] - 查看本周日程\\n"
        "• [cyan]pm smart-next[/cyan] - 结合日程的智能推荐[/dim]",
        border_style="dim"
    ))


def show_weekly_schedule() -> None:
    """显示本周日程"""
    
    config = PMConfig()
    if not config.is_initialized():
        console.print(Panel(
            "[yellow]系统未初始化。请先运行 [cyan]pm setup[/cyan] 进行设置。",
            title="⚠️ 未初始化",
            border_style="yellow"
        ))
        return
    
    calendar_integration = GoogleCalendarIntegration(config)
    
    # 检查认证状态
    if not calendar_integration.google_auth.is_google_authenticated():
        console.print(Panel(
            "[red]未通过Google认证。请先运行：[cyan]pm auth login google[/cyan]",
            title="❌ 认证错误",
            border_style="red"
        ))
        return
    
    with console.status("[bold blue]获取本周日程...", spinner="dots"):
        weekly_events = calendar_integration.get_upcoming_events(days_ahead=7)
    
    if not weekly_events:
        console.print(Panel(
            "[yellow]📅 本周没有日程安排[/yellow]\\n\\n"
            "看起来是一个比较轻松的周！",
            title="📋 本周日程",
            border_style="yellow"
        ))
        return
    
    # 按日期分组事件
    from collections import defaultdict
    events_by_date = defaultdict(list)
    
    for event in weekly_events:
        date_key = event.start_time.date()
        events_by_date[date_key].append(event)
    
    # 显示每日日程
    for date, events in sorted(events_by_date.items()):
        date_str = date.strftime("%Y-%m-%d (%A)")
        
        # 判断是否是今天
        if date == datetime.now().date():
            date_str += " [今天]"
            date_style = "bold cyan"
        else:
            date_style = "bold white"
        
        console.print(f"\\n[{date_style}]📅 {date_str}[/{date_style}]")
        
        # 创建当日事件表格
        daily_table = Table(show_header=False, box=None, padding=(0, 1))
        daily_table.add_column("", style="dim", width=12)
        daily_table.add_column("", style="white")
        daily_table.add_column("", style="yellow", width=8)
        
        for event in sorted(events, key=lambda x: x.start_time):
            start_time = event.start_time.strftime("%H:%M")
            end_time = event.end_time.strftime("%H:%M")
            time_range = f"{start_time}-{end_time}"
            duration = f"{event.duration_minutes}分钟"
            
            title_with_info = event.title
            if event.location:
                title_with_info += f" (📍 {event.location})"
            elif event.attendees:
                title_with_info += f" (👥 {len(event.attendees)}人)"
            
            daily_table.add_row(time_range, title_with_info, duration)
        
        console.print(daily_table)
    
    # 显示统计信息
    total_events = len(weekly_events)
    total_hours = sum(event.duration_minutes for event in weekly_events) / 60
    
    console.print(Panel(
        f"[cyan]📊 本周日程统计[/cyan]\\n\\n"
        f"• 总事件数: [yellow]{total_events}[/yellow] 个\\n"
        f"• 总时长: [green]{total_hours:.1f}[/green] 小时\\n"
        f"• 平均每天: [blue]{total_hours/7:.1f}[/blue] 小时",
        title="📈 统计信息",
        border_style="blue"
    ))


def create_event_from_task(task_id: str) -> None:
    """为GTD任务创建Google Calendar事件"""
    
    config = PMConfig()
    if not config.is_initialized():
        console.print(Panel(
            "[yellow]系统未初始化。请先运行 [cyan]pm setup[/cyan] 进行设置。",
            title="⚠️ 未初始化",
            border_style="yellow"
        ))
        return
    
    calendar_integration = GoogleCalendarIntegration(config)
    agent = GTDAgent(config)
    
    # 检查认证状态
    if not calendar_integration.google_auth.is_google_authenticated():
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
    
    # 创建日程事件
    with console.status(f"[bold blue]为任务'{task.title[:30]}...'创建日程事件...", spinner="dots"):
        success, message = calendar_integration.create_calendar_event(task)
    
    if success:
        console.print(Panel(
            f"[green]✅ {message}[/green]\\n\\n"
            f"任务详情：\\n"
            f"• 标题: {task.title}\\n"
            f"• 截止时间: {task.due_date.strftime('%Y-%m-%d %H:%M') if task.due_date else 'N/A'}\\n"
            f"• 预计时长: {task.estimated_duration or 'N/A'}分钟",
            title="🎉 创建成功",
            border_style="green"
        ))
    else:
        console.print(Panel(
            f"[red]❌ {message}[/red]",
            title="创建失败",
            border_style="red"
        ))


def delete_calendar_events(title_pattern: str) -> None:
    """删除包含指定标题模式的Google Calendar事件"""
    
    config = PMConfig()
    if not config.is_initialized():
        console.print(Panel(
            "[yellow]系统未初始化。请先运行 [cyan]pm setup[/cyan] 进行设置。",
            title="⚠️ 未初始化",
            border_style="yellow"
        ))
        return
    
    calendar_integration = GoogleCalendarIntegration(config)
    
    # 检查认证状态
    if not calendar_integration.google_auth.is_google_authenticated():
        console.print(Panel(
            "[red]未通过Google认证。请先运行：[cyan]pm auth login google[/cyan]",
            title="❌ 认证错误",
            border_style="red"
        ))
        return
    
    # 确认删除操作
    console.print(Panel(
        f"[yellow]⚠️  即将删除包含 '{title_pattern}' 的所有Google Calendar事件[/yellow]\\n\\n"
        f"这个操作是不可逆的！请确认您真的想要删除这些日程。\\n\\n"
        f"删除范围：未来30天内包含 '{title_pattern}' 的所有事件",
        title="🗑️  确认删除",
        border_style="yellow"
    ))
    
    confirm = typer.confirm("确定要删除这些日程事件吗？")
    if not confirm:
        console.print("[yellow]❌ 操作已取消[/yellow]")
        return
    
    # 执行删除
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(f"正在删除包含 '{title_pattern}' 的事件...", total=None)
        
        deleted_count, errors = calendar_integration.delete_events_by_title(title_pattern)
        
        progress.update(task, description="删除完成")
    
    # 显示删除结果
    if deleted_count > 0:
        console.print(Panel(
            f"[green]✅ 删除成功！[/green]\\n\\n"
            f"• 已删除 [cyan]{deleted_count}[/cyan] 个包含 '{title_pattern}' 的日程事件\\n"
            f"• 删除范围：未来30天\\n\\n"
            "[yellow]注意：如果您的GTD系统中已同步了这些事件，\\n"
            "建议运行 [cyan]pm calendar sync[/cyan] 重新同步以保持一致性。[/yellow]",
            title="🎉 删除完成",
            border_style="green"
        ))
    else:
        console.print(Panel(
            f"[yellow]ℹ️ 未找到包含 '{title_pattern}' 的日程事件[/yellow]\\n\\n"
            "可能的原因：\\n"
            f"• 未来30天内没有包含 '{title_pattern}' 的事件\\n"
            "• 事件标题与搜索模式不匹配\\n"
            "• Google Calendar暂时无法访问",
            title="📋 删除结果",
            border_style="yellow"
        ))
    
    # 显示错误信息
    if errors:
        console.print(Panel(
            "[red]⚠️ 删除过程中遇到以下问题：[/red]\\n\\n" +
            "\\n".join([f"• {error}" for error in errors]),
            title="❗ 警告",
            border_style="red"
        ))