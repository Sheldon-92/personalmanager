"""深度工作管理CLI命令 - Sprint 14核心功能

CLI命令作为AI可调用工具函数的薄包装层
基于《深度工作》理论的专注管理和时段跟踪
"""

from datetime import datetime, timedelta
from typing import List, Optional
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
from rich.prompt import Prompt, Confirm, IntPrompt

from pm.core.config import PMConfig
from pm.tools.deep_work_tools import (
    create_deep_work_session, start_deep_work_session, end_deep_work_session,
    add_distraction_to_session, get_active_deep_work_session, get_todays_deep_work_sessions,
    get_deep_work_statistics, get_focus_trends, create_reflection_entry, get_recent_reflections
)

console = Console()
deep_work_app = typer.Typer(name="deepwork", help="深度工作时段管理 - 基于《深度工作》理论")


@deep_work_app.command("create")
def create_session(
    title: str = typer.Argument(..., help="深度工作时段标题"),
    duration: int = typer.Option(60, "--duration", "-d", help="计划持续时间（分钟）"),
    work_type: str = typer.Option("rhythmic", "--type", "-t", 
                                 help="深度工作类型 (monasticism/bimodal/rhythmic/journalistic)"),
    focus_level: str = typer.Option("deep", "--focus", "-f", 
                                   help="目标专注级别 (shallow/semi_deep/deep/profound)"),
    task: Optional[str] = typer.Option(None, "--task", help="主要任务描述"),
    project: Optional[str] = typer.Option(None, "--project", help="关联项目ID"),
    start_time: Optional[str] = typer.Option(None, "--start", help="计划开始时间 (HH:MM)"),
    environment: str = typer.Option("home_office", "--env", "-e", 
                                   help="工作环境 (home_office/coworking/library/cafe/outdoor/other)"),
    description: Optional[str] = typer.Option(None, "--desc", help="时段描述"),
    tags: Optional[List[str]] = typer.Option(None, "--tag", help="标签（可多个）")
) -> None:
    """创建新的深度工作时段"""
    
    config = PMConfig()
    
    # 处理开始时间
    planned_start = None
    if start_time:
        try:
            today = datetime.now().date()
            hour, minute = map(int, start_time.split(":"))
            planned_start = datetime.combine(today, datetime.min.time().replace(hour=hour, minute=minute))
            if planned_start < datetime.now():
                planned_start += timedelta(days=1)  # 如果时间已过，设置为明天
        except ValueError:
            console.print("[red]❌ 时间格式无效，请使用 HH:MM 格式")
            raise typer.Exit(1)
    
    # 调用AI可调用工具函数
    success, message, session_info = create_deep_work_session(
        title=title,
        planned_duration_minutes=duration,
        work_type=work_type,
        target_focus_level=focus_level,
        primary_task=task,
        project_id=project,
        description=description,
        planned_start=planned_start.isoformat() if planned_start else None,
        environment_location=environment,
        tags=tags,
        config=config
    )
    
    if success:
        console.print(f"[green]✅ {message}")
        
        if session_info:
            # 显示创建的时段信息
            table = Table(title="深度工作时段详情")
            table.add_column("属性", style="cyan")
            table.add_column("值", style="green")
            
            table.add_row("时段ID", session_info["session_id"][:8])
            table.add_row("标题", session_info["title"])
            table.add_row("工作类型", session_info["work_type"])
            table.add_row("目标专注级别", session_info["target_focus_level"])
            table.add_row("计划时长", f"{session_info['planned_duration_minutes']} 分钟")
            table.add_row("计划开始", datetime.fromisoformat(session_info["planned_start"]).strftime("%Y-%m-%d %H:%M"))
            if session_info.get("primary_task"):
                table.add_row("主要任务", session_info["primary_task"])
            table.add_row("工作环境", session_info["environment_location"])
            
            console.print(table)
            
            # 询问是否立即开始
            if Confirm.ask("是否立即开始这个深度工作时段？", default=False):
                start_session_command(session_info["session_id"][:8])
    else:
        console.print(f"[red]❌ {message}")
        raise typer.Exit(1)


@deep_work_app.command("start")
def start_session_command(
    session_id: str = typer.Argument(..., help="时段ID（可使用短ID）"),
    notes: Optional[str] = typer.Option(None, "--notes", "-n", help="开始前笔记"),
    energy: int = typer.Option(5, "--energy", "-e", help="当前精力水平 (1-5)")
) -> None:
    """开始深度工作时段"""
    
    config = PMConfig()
    
    # 调用AI可调用工具函数
    success, message, session_info = start_deep_work_session(
        session_id=session_id,
        pre_session_notes=notes,
        energy_level=energy,
        config=config
    )
    
    if success:
        console.print(f"[green]✅ {message}")
        
        if session_info:
            console.print(Panel(
                f"[bold blue]🎯 深度工作开始！[/bold blue]\\n\\n"
                f"时段: {session_info['title']}\\n"
                f"开始时间: {datetime.fromisoformat(session_info['actual_start']).strftime('%H:%M')}\\n"
                f"计划结束: {datetime.fromisoformat(session_info['planned_end']).strftime('%H:%M') if session_info.get('planned_end') else '未设定'}\\n"
                f"当前精力: {session_info['energy_level_start']}/5",
                title="🚀 深度工作进行中",
                border_style="green"
            ))
            
            console.print("[dim]💡 使用以下命令管理时段：")
            console.print("[dim]  • pm deepwork distract - 记录干扰事件")
            console.print("[dim]  • pm deepwork status - 查看当前状态")
            console.print("[dim]  • pm deepwork end - 结束时段")
    else:
        console.print(f"[red]❌ {message}")
        raise typer.Exit(1)


@deep_work_app.command("end")
def end_session_command(
    session_id: Optional[str] = typer.Argument(None, help="时段ID（留空自动选择活跃时段）"),
    focus_level: Optional[str] = typer.Option(None, "--focus", "-f", 
                                             help="实际专注级别 (shallow/semi_deep/deep/profound)"),
    energy_end: Optional[int] = typer.Option(None, "--energy", "-e", help="结束时精力水平 (1-5)"),
    reflection: Optional[str] = typer.Option(None, "--reflection", "-r", help="结束后反思")
) -> None:
    """结束深度工作时段"""
    
    config = PMConfig()
    
    # 如果没有提供session_id，获取当前活跃时段
    if not session_id:
        active_success, active_message, active_info = get_active_deep_work_session(config)
        if not active_success:
            console.print(f"[red]❌ {active_message}")
            raise typer.Exit(1)
        session_id = active_info["session_id"]
        console.print(f"[blue]ℹ️ 将结束活跃时段: {active_info['title']}")
    
    # 交互式输入缺失的参数
    if not focus_level:
        focus_level = Prompt.ask(
            "实际达到的专注级别",
            choices=["shallow", "semi_deep", "deep", "profound"],
            default="deep"
        )
    
    if not energy_end:
        energy_end = IntPrompt.ask(
            "结束时的精力水平 (1-5)",
            default=3,
            show_default=True
        )
    
    if not reflection:
        reflection = Prompt.ask(
            "结束后反思（可留空）",
            default=""
        ) or None
    
    # 询问经验教训和改进行动
    lessons_learned = []
    improvement_actions = []
    
    if Confirm.ask("是否添加经验教训？", default=False):
        while True:
            lesson = Prompt.ask("经验教训（留空结束）", default="")
            if not lesson:
                break
            lessons_learned.append(lesson)
    
    if Confirm.ask("是否添加改进行动？", default=False):
        while True:
            action = Prompt.ask("改进行动（留空结束）", default="")
            if not action:
                break
            improvement_actions.append(action)
    
    # 调用AI可调用工具函数
    success, message, session_summary = end_deep_work_session(
        session_id=session_id,
        actual_focus_level=focus_level,
        energy_level_end=energy_end,
        post_session_reflection=reflection,
        lessons_learned=lessons_learned if lessons_learned else None,
        improvement_actions=improvement_actions if improvement_actions else None,
        config=config
    )
    
    if success:
        console.print(f"[green]✅ {message}")
        
        if session_summary:
            # 显示时段总结
            table = Table(title="深度工作时段总结")
            table.add_column("指标", style="cyan")
            table.add_column("值", style="green")
            
            table.add_row("时段标题", session_summary["title"])
            table.add_row("实际时长", f"{session_summary['actual_duration_minutes']} 分钟")
            table.add_row("计划时长", f"{session_summary['planned_duration_minutes']} 分钟")
            table.add_row("目标专注级别", session_summary["target_focus_level"])
            table.add_row("实际专注级别", session_summary["actual_focus_level"])
            table.add_row("专注评分", f"{session_summary['focus_score']:.1f}/100")
            table.add_row("效率评分", f"{session_summary['efficiency_score']:.1f}/100")
            table.add_row("干扰次数", str(session_summary["distraction_count"]))
            table.add_row("精力变化", f"{session_summary['energy_change']:+d}" if session_summary['energy_change'] is not None else "未记录")
            
            console.print(table)
            
            if session_summary.get("lessons_learned"):
                console.print("\\n[bold]📝 经验教训：")
                for lesson in session_summary["lessons_learned"]:
                    console.print(f"  • {lesson}")
            
            if session_summary.get("improvement_actions"):
                console.print("\\n[bold]🎯 改进行动：")
                for action in session_summary["improvement_actions"]:
                    console.print(f"  • {action}")
    else:
        console.print(f"[red]❌ {message}")
        raise typer.Exit(1)


@deep_work_app.command("distract")
def add_distraction(
    session_id: Optional[str] = typer.Argument(None, help="时段ID（留空自动选择活跃时段）"),
    distraction_type: str = typer.Option("external", "--type", "-t", 
                                        help="干扰类型 (internal/external/social/tech)"),
    description: Optional[str] = typer.Option(None, "--desc", "-d", help="干扰描述"),
    severity: int = typer.Option(1, "--severity", "-s", help="严重程度 (1-5)"),
    duration: Optional[int] = typer.Option(None, "--duration", help="干扰持续时间（秒）")
) -> None:
    """记录干扰事件到当前深度工作时段"""
    
    config = PMConfig()
    
    # 如果没有提供session_id，获取当前活跃时段
    if not session_id:
        active_success, active_message, active_info = get_active_deep_work_session(config)
        if not active_success:
            console.print(f"[red]❌ {active_message}")
            raise typer.Exit(1)
        session_id = active_info["session_id"]
    
    # 交互式输入描述（如果未提供）
    if not description:
        description = Prompt.ask("干扰描述", default="")
        if not description:
            description = None
    
    # 调用AI可调用工具函数
    success, message, distraction_info = add_distraction_to_session(
        session_id=session_id,
        distraction_type=distraction_type,
        description=description,
        severity=severity,
        duration_seconds=duration,
        config=config
    )
    
    if success:
        console.print(f"[yellow]⚠️ {message}")
        
        if distraction_info:
            console.print(f"[dim]干扰类型: {distraction_info['distraction_type']}")
            console.print(f"[dim]严重程度: {distraction_info['severity']}/5")
            console.print(f"[dim]总干扰次数: {distraction_info['total_distractions']}")
    else:
        console.print(f"[red]❌ {message}")
        raise typer.Exit(1)


@deep_work_app.command("status")
def show_status() -> None:
    """显示当前深度工作状态"""
    
    config = PMConfig()
    
    # 获取活跃时段
    active_success, active_message, active_info = get_active_deep_work_session(config)
    
    if active_success and active_info:
        # 显示活跃时段详情
        elapsed = active_info["elapsed_minutes"]
        remaining = active_info["remaining_minutes"]
        
        console.print(Panel(
            f"[bold blue]🎯 {active_info['title']}[/bold blue]\\n\\n"
            f"工作类型: {active_info['work_type']}\\n"
            f"目标专注: {active_info['target_focus_level']}\\n"
            f"已用时间: {elapsed} 分钟\\n"
            f"剩余时间: {remaining} 分钟\\n"
            f"干扰次数: {active_info['distraction_count']}\\n"
            f"开始精力: {active_info['energy_level_start']}/5",
            title="🚀 深度工作进行中",
            border_style="green"
        ))
        
        # 显示进度条
        if active_info["planned_duration_minutes"] > 0:
            progress_percentage = min((elapsed / active_info["planned_duration_minutes"]) * 100, 100)
            console.print(f"\\n进度: {progress_percentage:.1f}%")
            
            with Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(complete_style="green", finished_style="blue"),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            ) as progress:
                task = progress.add_task("专注进度", completed=progress_percentage, total=100)
    else:
        console.print("[blue]ℹ️ 当前没有进行中的深度工作时段")
    
    # 显示今日时段概览
    today_success, today_message, today_info = get_todays_deep_work_sessions(config)
    
    if today_success and today_info:
        console.print(f"\\n[bold]📊 今日深度工作概览[/bold]")
        console.print(f"总时段数: {today_info['total_sessions']}")
        console.print(f"已完成: {today_info['completed_sessions']}")
        console.print(f"计划总时长: {today_info['total_planned_minutes']} 分钟")
        console.print(f"实际总时长: {today_info['total_actual_minutes']} 分钟")
        
        if today_info["average_focus_score"] > 0:
            console.print(f"平均专注度: {today_info['average_focus_score']}/100")
    
    console.print("\\n[dim]💡 可用命令：")
    console.print("[dim]  • pm deepwork create - 创建新时段")
    console.print("[dim]  • pm deepwork start - 开始时段")
    console.print("[dim]  • pm deepwork end - 结束当前时段")
    console.print("[dim]  • pm deepwork distract - 记录干扰")


@deep_work_app.command("today")
def show_today() -> None:
    """显示今天的深度工作时段"""
    
    config = PMConfig()
    
    # 获取今日时段
    success, message, today_info = get_todays_deep_work_sessions(config)
    
    if not success:
        console.print(f"[blue]ℹ️ {message}")
        return
    
    console.print(f"[bold]📅 今日深度工作时段 ({today_info['date']})[/bold]")
    
    if today_info["sessions"]:
        table = Table()
        table.add_column("时间", style="cyan")
        table.add_column("标题", style="white")
        table.add_column("时长", style="green")
        table.add_column("状态", style="yellow")
        table.add_column("专注度", style="blue")
        table.add_column("干扰", style="red")
        
        for session in today_info["sessions"]:
            status_emoji = {
                "completed": "✅",
                "active": "🏃",
                "planned": "⏰"
            }
            
            status = f"{status_emoji.get(session['status'], '❓')} {session['status']}"
            focus_score = f"{session['focus_score']:.1f}" if session['focus_score'] is not None else "-"
            actual_duration = f"{session['actual_duration_minutes']}min" if session['actual_duration_minutes'] > 0 else "-"
            
            table.add_row(
                session["planned_start"],
                session["title"],
                f"{session['planned_duration_minutes']}min ({actual_duration})",
                status,
                focus_score,
                str(session["distraction_count"])
            )
        
        console.print(table)
    
    # 显示今日统计
    console.print(f"\\n[bold]📊 今日统计[/bold]")
    console.print(f"计划总时长: {today_info['total_planned_minutes']} 分钟")
    console.print(f"实际总时长: {today_info['total_actual_minutes']} 分钟")
    console.print(f"完成率: {today_info['completed_sessions']}/{today_info['total_sessions']}")
    
    if today_info["average_focus_score"] > 0:
        console.print(f"平均专注度: {today_info['average_focus_score']:.1f}/100")


@deep_work_app.command("stats")
def show_statistics(
    days: int = typer.Option(30, "--days", "-d", help="统计天数")
) -> None:
    """显示深度工作统计信息"""
    
    config = PMConfig()
    
    # 获取统计信息
    success, message, stats_info = get_deep_work_statistics(days, config)
    
    if not success:
        console.print(f"[red]❌ {message}")
        return
    
    console.print(f"[bold]📊 深度工作统计（过去 {days} 天）[/bold]")
    
    # 基础统计表格
    table = Table(title="基础统计")
    table.add_column("指标", style="cyan")
    table.add_column("数值", style="green")
    
    table.add_row("总时段数", str(stats_info["total_sessions"]))
    table.add_row("完成时段数", str(stats_info["completed_sessions"]))
    table.add_row("完成率", f"{stats_info['completion_rate']:.1f}%")
    table.add_row("总深度工作时间", f"{stats_info['total_deep_work_minutes']} 分钟")
    table.add_row("平均时段长度", f"{stats_info['average_session_duration']:.1f} 分钟")
    table.add_row("日均时段数", f"{stats_info['daily_average_sessions']}")
    table.add_row("日均深度工作时间", f"{stats_info['daily_average_deep_work_minutes']:.1f} 分钟")
    
    console.print(table)
    
    # 质量指标
    quality_table = Table(title="质量指标")
    quality_table.add_column("指标", style="cyan")
    quality_table.add_column("数值", style="green")
    quality_table.add_column("评级", style="yellow")
    
    quality_table.add_row("平均专注度", f"{stats_info['average_focus_score']:.1f}/100", stats_info["productivity_rating"])
    quality_table.add_row("平均效率评分", f"{stats_info['average_efficiency_score']:.1f}/100", "")
    quality_table.add_row("总干扰次数", str(stats_info["total_distractions"]), "")
    quality_table.add_row("平均干扰率", f"{stats_info['distraction_rate']:.1f}/时段", stats_info["distraction_rating"])
    
    if stats_info.get("most_productive_hour") is not None:
        quality_table.add_row("最佳工作时段", f"{stats_info['most_productive_hour']}:00", "")
    
    console.print(quality_table)
    
    # 常见干扰类型
    if stats_info.get("common_distractions"):
        console.print("\\n[bold]⚠️ 常见干扰类型[/bold]")
        for dtype, count in stats_info["common_distractions"]:
            console.print(f"  • {dtype}: {count} 次")
    
    # 改进建议
    if stats_info.get("recommendations"):
        console.print("\\n[bold]💡 改进建议[/bold]")
        for recommendation in stats_info["recommendations"]:
            console.print(f"  • {recommendation}")


@deep_work_app.command("trends")
def show_trends(
    days: int = typer.Option(30, "--days", "-d", help="分析天数")
) -> None:
    """显示专注度趋势分析"""
    
    config = PMConfig()
    
    # 获取趋势分析
    success, message, trends_info = get_focus_trends(days, config)
    
    if not success:
        console.print(f"[red]❌ {message}")
        return
    
    console.print(f"[bold]📈 专注度趋势（过去 {days} 天）[/bold]")
    
    # 趋势概览
    overview_table = Table(title="趋势概览")
    overview_table.add_column("指标", style="cyan")
    overview_table.add_column("数值", style="green")
    
    overview_table.add_row("数据天数", str(trends_info["total_data_points"]))
    overview_table.add_row("平均专注度", f"{trends_info['average_focus_score']:.1f}/100")
    overview_table.add_row("最高专注度", f"{trends_info['max_focus_score']:.1f}/100")
    overview_table.add_row("最低专注度", f"{trends_info['min_focus_score']:.1f}/100")
    overview_table.add_row("趋势方向", trends_info["trend_direction"])
    overview_table.add_row("改进幅度", f"{trends_info['improvement_percentage']:.1f}%")
    
    console.print(overview_table)
    
    # 显示最近几天的详细数据
    if trends_info.get("daily_trends"):
        console.print("\\n[bold]📅 每日专注度（最近10天）[/bold]")
        daily_table = Table()
        daily_table.add_column("日期", style="cyan")
        daily_table.add_column("时段数", style="white")
        daily_table.add_column("总时长(分)", style="green")
        daily_table.add_column("专注度", style="blue")
        daily_table.add_column("干扰次数", style="red")
        
        # 显示最近10天
        recent_days = trends_info["daily_trends"][-10:]
        for day in recent_days:
            daily_table.add_row(
                day["date"],
                str(day["sessions_count"]),
                str(day["total_minutes"]),
                f"{day['average_focus_score']:.1f}/100",
                str(day["distraction_count"])
            )
        
        console.print(daily_table)


@deep_work_app.command("reflect")
def create_reflection(
    period: str = typer.Option("daily", "--period", "-p", help="反思周期 (daily/weekly/monthly)"),
    satisfaction: int = typer.Option(3, "--satisfaction", "-s", help="总体满意度 (1-5)"),
    focus: int = typer.Option(3, "--focus", "-f", help="专注质量评分 (1-5)"),
    productivity: int = typer.Option(3, "--productivity", help="生产力评分 (1-5)"),
    energy: int = typer.Option(3, "--energy", "-e", help="精力管理评分 (1-5)")
) -> None:
    """创建深度工作反思记录"""
    
    config = PMConfig()
    
    console.print(f"[bold]📝 创建{period}反思记录[/bold]")
    
    # 交互式收集反思内容
    console.print("\\n[cyan]工作良好的方面：[/cyan]")
    what_worked_well = []
    while True:
        item = Prompt.ask("添加一项（留空结束）", default="")
        if not item:
            break
        what_worked_well.append(item)
    
    console.print("\\n[yellow]可改进的方面：[/yellow]")
    what_could_improve = []
    while True:
        item = Prompt.ask("添加一项（留空结束）", default="")
        if not item:
            break
        what_could_improve.append(item)
    
    console.print("\\n[blue]关键洞察：[/blue]")
    key_insights = []
    while True:
        item = Prompt.ask("添加一项（留空结束）", default="")
        if not item:
            break
        key_insights.append(item)
    
    console.print("\\n[green]下一步行动：[/green]")
    next_actions = []
    while True:
        item = Prompt.ask("添加一项（留空结束）", default="")
        if not item:
            break
        next_actions.append(item)
    
    # 调用AI可调用工具函数
    success, message, reflection_info = create_reflection_entry(
        period_type=period,
        what_worked_well=what_worked_well if what_worked_well else None,
        what_could_improve=what_could_improve if what_could_improve else None,
        key_insights=key_insights if key_insights else None,
        next_actions=next_actions if next_actions else None,
        overall_satisfaction=satisfaction,
        focus_quality_rating=focus,
        productivity_rating=productivity,
        energy_management_rating=energy,
        config=config
    )
    
    if success:
        console.print(f"\\n[green]✅ {message}")
        
        if reflection_info:
            console.print(f"[dim]反思ID: {reflection_info['reflection_id'][:8]}")
            console.print(f"[dim]关联时段: {reflection_info['related_sessions_count']} 个")
    else:
        console.print(f"[red]❌ {message}")
        raise typer.Exit(1)


@deep_work_app.command("reflections")
def show_reflections(
    days: int = typer.Option(30, "--days", "-d", help="查询天数"),
    period_type: Optional[str] = typer.Option(None, "--type", "-t", help="反思类型 (daily/weekly/monthly)")
) -> None:
    """显示最近的反思记录"""
    
    config = PMConfig()
    
    # 获取反思记录
    success, message, reflections_info = get_recent_reflections(days, period_type, config)
    
    if not success:
        console.print(f"[blue]ℹ️ {message}")
        return
    
    filter_text = f" ({period_type})" if period_type else ""
    console.print(f"[bold]📝 反思记录（过去 {days} 天{filter_text}）[/bold]")
    
    # 显示平均评分
    avg_ratings = reflections_info["average_ratings"]
    console.print(f"\\n[bold]平均评分：[/bold]")
    console.print(f"总体满意度: {avg_ratings['overall_satisfaction']:.1f}/5")
    console.print(f"专注质量: {avg_ratings['focus_quality']:.1f}/5")
    console.print(f"生产力: {avg_ratings['productivity']:.1f}/5")
    console.print(f"精力管理: {avg_ratings['energy_management']:.1f}/5")
    
    # 显示反思记录列表
    for reflection in reflections_info["reflections"][:10]:  # 只显示最近10条
        console.print(f"\\n[bold cyan]{reflection['date']} ({reflection['period_type']})[/bold cyan]")
        console.print(f"满意度: {reflection['overall_satisfaction']}/5  专注: {reflection['focus_quality_rating']}/5")
        
        if reflection["what_worked_well"]:
            console.print("[green]✅ 工作良好：[/green]")
            for item in reflection["what_worked_well"]:
                console.print(f"  • {item}")
        
        if reflection["what_could_improve"]:
            console.print("[yellow]⚠️ 可改进：[/yellow]")
            for item in reflection["what_could_improve"]:
                console.print(f"  • {item}")
        
        if reflection["key_insights"]:
            console.print("[blue]💡 关键洞察：[/blue]")
            for item in reflection["key_insights"]:
                console.print(f"  • {item}")
        
        if reflection["next_actions"]:
            console.print("[green]🎯 下一步行动：[/green]")
            for item in reflection["next_actions"]:
                console.print(f"  • {item}")


# 添加到主CLI应用
if __name__ == "__main__":
    deep_work_app()