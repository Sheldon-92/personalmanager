"""回顾与反思管理CLI命令 - Sprint 16核心功能

CLI命令作为AI可调用工具函数的薄包装层
基于个人效能管理理论的回顾与反思系统
"""

from datetime import date, datetime, timedelta
from typing import List, Optional
import sys
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm, IntPrompt

from pm.core.config import PMConfig
from pm.tools.review_tools import (
    create_weekly_review, get_weekly_review, get_recent_weekly_reviews,
    create_project_retrospective, track_decision, evaluate_decision_outcome,
    add_growth_insight, get_review_statistics, get_decision_quality_analysis,
    get_growth_insights_summary
)

console = Console()
review_app = typer.Typer(name="review", help="回顾与反思管理 - 持续自我提升")

def safe_prompt_ask(prompt_text: str, default: str = "") -> str:
    """安全的提示输入，处理stdin和交互式模式"""
    # 检测是否为非交互式模式（管道输入）
    if not sys.stdin.isatty():
        try:
            line = input().strip()  # 使用标准input()处理管道输入
            return line if line else default
        except EOFError:
            return default
    else:
        return Prompt.ask(prompt_text, default=default)

def safe_int_prompt_ask(prompt_text: str, default: int = 3, show_default: bool = True) -> int:
    """安全的整数提示输入，处理stdin和交互式模式"""
    # 检测是否为非交互式模式（管道输入）
    if not sys.stdin.isatty():
        try:
            line = input().strip()
            return int(line) if line.isdigit() else default
        except (EOFError, ValueError):
            return default
    else:
        return IntPrompt.ask(prompt_text, default=default, show_default=show_default)


@review_app.command("weekly")
def create_weekly_review_command(
    week_date: Optional[str] = typer.Argument(None, help="周开始日期 (YYYY-MM-DD，留空为本周)"),
    interactive: bool = typer.Option(True, "--interactive/--no-interactive", "-i/-n", help="是否使用交互式输入")
) -> None:
    """创建每周回顾"""
    
    config = PMConfig()
    
    # 确定回顾的周
    if week_date:
        try:
            target_date = datetime.strptime(week_date, "%Y-%m-%d").date()
            # 调整到周一
            week_start = target_date - timedelta(days=target_date.weekday())
        except ValueError:
            console.print("[red]❌ 日期格式错误，请使用YYYY-MM-DD格式")
            raise typer.Exit(1)
    else:
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
    
    week_end = week_start + timedelta(days=6)
    
    console.print(Panel(
        f"[bold blue]📝 创建每周回顾[/bold blue]\\n\\n"
        f"回顾周期: {week_start.strftime('%Y-%m-%d')} 至 {week_end.strftime('%Y-%m-%d')}",
        title="🗓️ 每周回顾",
        border_style="blue"
    ))
    
    if interactive:
        # 交互式收集回顾内容
        console.print("\\n[cyan]📈 本周成就：[/cyan]")
        console.print("[dim]例如: 完成项目开发、学习新技能、解决重要问题等[/dim]")
        achievements = []
        while True:
            achievement = safe_prompt_ask("添加一项成就（留空结束）", default="")
            if not achievement:
                break
            achievements.append(achievement)
        
        console.print("\\n[yellow]⚠️ 本周挑战：[/yellow]")
        console.print("[dim]例如: 技术难题、时间管理问题、团队协作困难等[/dim]")
        challenges = []
        while True:
            challenge = safe_prompt_ask("添加一项挑战（留空结束）", default="")
            if not challenge:
                break
            challenges.append(challenge)
        
        console.print("\\n[green]💡 经验教训：[/green]")
        console.print("[dim]例如: 提升了沟通技巧、学会了新的工作方法、改进了流程等[/dim]")
        lessons_learned = []
        while True:
            lesson = safe_prompt_ask("添加一条经验教训（留空结束）", default="")
            if not lesson:
                break
            lessons_learned.append(lesson)
        
        console.print("\\n[blue]✅ 进展顺利的方面：[/blue]")
        console.print("[dim]例如: 团队协作高效、代码质量优秀、进度按计划推进等[/dim]")
        what_went_well = []
        while True:
            item = safe_prompt_ask("添加一项（留空结束）", default="")
            if not item:
                break
            what_went_well.append(item)
        
        console.print("\\n[magenta]🔄 可以改进的方面：[/magenta]")
        console.print("[dim]例如: 时间管理需要优化、沟通方式待改进、技术深度有待加强等[/dim]")
        what_could_improve = []
        while True:
            item = safe_prompt_ask("添加一项（留空结束）", default="")
            if not item:
                break
            what_could_improve.append(item)
        
        console.print("\\n[green]🎯 完成的周目标：[/green]")
        console.print("[dim]例如: 完成MVP开发、发布新功能、学习React等[/dim]")
        goals_achieved = []
        while True:
            goal = safe_prompt_ask("添加一个完成的目标（留空结束）", default="")
            if not goal:
                break
            goals_achieved.append(goal)
        
        console.print("\\n[red]❌ 未完成的周目标：[/red]")
        console.print("[dim]例如: 修复重要Bug、完成文档撰写、进行代码重构等[/dim]")
        goals_missed = []
        while True:
            goal = safe_prompt_ask("添加一个未完成的目标（留空结束）", default="")
            if not goal:
                break
            goals_missed.append(goal)
        
        console.print("\\n[cyan]🚀 下周目标：[/cyan]")
        console.print("[dim]例如: 优化性能、增加新功能、改进用户体验等[/dim]")
        next_week_goals = []
        while True:
            goal = safe_prompt_ask("添加一个下周目标（留空结束）", default="")
            if not goal:
                break
            next_week_goals.append(goal)
        
        # 评分
        console.print("\\n[bold]📊 各项评分 (1-5分)：[/bold]")
        overall_satisfaction = safe_int_prompt_ask("总体满意度", default=3, show_default=True)
        productivity_rating = safe_int_prompt_ask("生产力评分", default=3, show_default=True)
        learning_rating = safe_int_prompt_ask("学习成长评分", default=3, show_default=True)
        work_performance = safe_int_prompt_ask("工作表现", default=3, show_default=True)
        personal_development = safe_int_prompt_ask("个人发展", default=3, show_default=True)
        health_wellness = safe_int_prompt_ask("健康状况", default=3, show_default=True)
        relationships = safe_int_prompt_ask("人际关系", default=3, show_default=True)
    else:
        # 非交互模式，使用默认值
        achievements = []
        challenges = []
        lessons_learned = []
        what_went_well = []
        what_could_improve = []
        goals_achieved = []
        goals_missed = []
        next_week_goals = []
        overall_satisfaction = productivity_rating = learning_rating = 3
        work_performance = personal_development = health_wellness = relationships = 3
    
    # 调用AI可调用工具函数
    success, message, review_info = create_weekly_review(
        week_start_date=week_start.isoformat(),
        achievements=achievements,
        challenges=challenges,
        lessons_learned=lessons_learned,
        what_went_well=what_went_well,
        what_could_improve=what_could_improve,
        week_goals_achieved=goals_achieved,
        week_goals_missed=goals_missed,
        next_week_goals=next_week_goals,
        overall_satisfaction=overall_satisfaction,
        productivity_rating=productivity_rating,
        learning_rating=learning_rating,
        work_performance=work_performance,
        personal_development=personal_development,
        health_wellness=health_wellness,
        relationships=relationships,
        config=config
    )
    
    if success:
        console.print(f"\\n[green]✅ {message}")
        
        if review_info:
            # 显示创建的回顾摘要
            table = Table(title="每周回顾摘要")
            table.add_column("指标", style="cyan")
            table.add_column("值", style="green")
            
            table.add_row("回顾ID", review_info["review_id"][:8])
            table.add_row("标题", review_info["title"])
            table.add_row("周期", f"{review_info['week_start']} 至 {review_info['week_end']}")
            table.add_row("综合评分", f"{review_info['weekly_score']:.1f}/5")
            table.add_row("目标完成率", f"{review_info['goal_completion_rate']:.1f}%")
            table.add_row("成就数量", str(review_info["total_achievements"]))
            table.add_row("挑战数量", str(review_info["total_challenges"]))
            table.add_row("经验教训", str(review_info["total_lessons"]))
            table.add_row("下周目标", str(review_info["next_week_goals_count"]))
            
            console.print(table)
    else:
        console.print(f"[red]❌ {message}")
        raise typer.Exit(1)


@review_app.command("show")
def show_weekly_review(
    week_date: Optional[str] = typer.Argument(None, help="周开始日期 (YYYY-MM-DD，留空为本周)")
) -> None:
    """显示指定周的回顾"""
    
    config = PMConfig()
    
    # 调用AI可调用工具函数
    success, message, review_info = get_weekly_review(week_date, config)
    
    if not success:
        console.print(f"[red]❌ {message}")
        return
    
    # 显示详细回顾信息
    console.print(Panel(
        f"[bold green]📋 {review_info['title']}[/bold green]\\n\\n"
        f"[dim]回顾周期: {review_info['week_start']} 至 {review_info['week_end']}[/dim]\\n"
        f"[dim]状态: {'✅ 已完成' if review_info['is_completed'] else '⏳ 进行中'}[/dim]",
        title="🗓️ 每周回顾详情",
        border_style="green"
    ))
    
    # 评分表格
    ratings_table = Table(title="📊 各项评分")
    ratings_table.add_column("领域", style="cyan")
    ratings_table.add_column("评分", style="yellow")
    ratings_table.add_column("状态", style="green")
    
    ratings = review_info["ratings"]
    for field, score in ratings.items():
        status = "优秀" if score >= 4 else "良好" if score >= 3 else "需改进"
        ratings_table.add_row(
            field.replace("_", " ").title(),
            f"{score}/5",
            status
        )
    
    console.print(ratings_table)
    
    # 目标完成情况
    if review_info["week_goals_achieved"] or review_info["week_goals_missed"]:
        console.print("\\n[bold]🎯 目标完成情况[/bold]")
        
        if review_info["week_goals_achieved"]:
            console.print("[green]✅ 已完成目标：[/green]")
            for goal in review_info["week_goals_achieved"]:
                console.print(f"  • {goal}")
        
        if review_info["week_goals_missed"]:
            console.print("\\n[red]❌ 未完成目标：[/red]")
            for goal in review_info["week_goals_missed"]:
                console.print(f"  • {goal}")
        
        console.print(f"\\n目标完成率: {review_info['goal_completion_rate']:.1f}%")
    
    # 其他内容
    sections = [
        ("achievements", "📈 本周成就", "green"),
        ("challenges", "⚠️ 遇到的挑战", "yellow"),
        ("lessons_learned", "💡 经验教训", "blue"),
        ("what_went_well", "✅ 进展顺利", "green"),
        ("what_could_improve", "🔄 可以改进", "magenta")
    ]
    
    for key, title, color in sections:
        items = review_info.get(key, [])
        if items:
            console.print(f"\\n[bold {color}]{title}[/bold {color}]")
            for item in items:
                console.print(f"  • {item}")
    
    # 下周目标
    if review_info["next_week_goals"]:
        console.print("\\n[bold cyan]🚀 下周目标[/bold cyan]")
        for goal in review_info["next_week_goals"]:
            console.print(f"  • {goal}")


@review_app.command("history")
def show_review_history(
    weeks: int = typer.Option(4, "--weeks", "-w", help="显示最近几周的回顾")
) -> None:
    """显示回顾历史"""
    
    config = PMConfig()
    
    # 调用AI可调用工具函数
    success, message, history_info = get_recent_weekly_reviews(weeks, config)
    
    if not success:
        console.print(f"[blue]ℹ️ {message}")
        return
    
    console.print(f"[bold]📊 最近 {weeks} 周回顾历史[/bold]")
    
    # 显示总体统计
    stats = history_info["statistics"]
    console.print(Panel(
        f"[green]平均周评分: {stats['average_weekly_score']}/5[/green]\\n"
        f"[blue]总体目标完成率: {stats['overall_goal_completion_rate']:.1f}%[/blue]\\n"
        f"[yellow]评分趋势: {stats['score_trend']}[/yellow]\\n"
        f"[cyan]最佳表现周: {stats['most_productive_week'] or '暂无'}[/cyan]",
        title="📈 趋势统计",
        border_style="blue"
    ))
    
    # 显示详细历史
    if history_info["reviews"]:
        table = Table()
        table.add_column("周期", style="cyan")
        table.add_column("标题", style="white")
        table.add_column("评分", style="yellow")
        table.add_column("目标完成率", style="green")
        table.add_column("成就", style="blue")
        table.add_column("状态", style="magenta")
        
        for review in history_info["reviews"]:
            status = "✅" if review["is_completed"] else "⏳"
            table.add_row(
                f"{review['week_start']} 至 {review['week_end'][:10]}",
                review["title"],
                f"{review['weekly_score']:.1f}/5",
                f"{review['goal_completion_rate']:.1f}%",
                str(review["achievements_count"]),
                status
            )
        
        console.print(table)


@review_app.command("project")
def create_project_retrospective_command(
    project_name: str = typer.Argument(..., help="项目名称"),
    interactive: bool = typer.Option(True, "--interactive/--no-interactive", "-i/-n", help="是否使用交互式输入")
) -> None:
    """创建项目复盘"""
    
    config = PMConfig()
    
    console.print(Panel(
        f"[bold blue]🔍 创建项目复盘[/bold blue]\\n\\n"
        f"项目: {project_name}",
        title="📋 项目复盘",
        border_style="blue"
    ))
    
    if interactive:
        # 交互式收集项目信息
        project_id = safe_prompt_ask("项目ID（可留空）", default="")
        project_start = safe_prompt_ask("项目开始日期 (YYYY-MM-DD，可留空)", default="")
        project_end = safe_prompt_ask("项目结束日期 (YYYY-MM-DD，可留空)", default="")
        
        original_timeline = None
        actual_timeline = None
        try:
            original_days = safe_prompt_ask("原计划天数（可留空）", default="")
            if original_days:
                original_timeline = int(original_days)
            
            actual_days = safe_prompt_ask("实际用时天数（可留空）", default="")
            if actual_days:
                actual_timeline = int(actual_days)
        except ValueError:
            console.print("[yellow]⚠️ 天数格式无效，将跳过时间线分析")
        
        # 收集复盘内容
        console.print("\\n[green]🎯 达成的目标：[/green]")
        objectives_met = []
        while True:
            obj = safe_prompt_ask("添加一个达成的目标（留空结束）", default="")
            if not obj:
                break
            objectives_met.append(obj)
        
        console.print("\\n[red]❌ 未达成的目标：[/red]")
        objectives_missed = []
        while True:
            obj = safe_prompt_ask("添加一个未达成的目标（留空结束）", default="")
            if not obj:
                break
            objectives_missed.append(obj)
        
        console.print("\\n[blue]📈 项目成就：[/blue]")
        achievements = []
        while True:
            achievement = safe_prompt_ask("添加一项成就（留空结束）", default="")
            if not achievement:
                break
            achievements.append(achievement)
        
        console.print("\\n[yellow]⚠️ 项目挑战：[/yellow]")
        challenges = []
        while True:
            challenge = safe_prompt_ask("添加一项挑战（留空结束）", default="")
            if not challenge:
                break
            challenges.append(challenge)
        
        console.print("\\n[magenta]💡 经验教训：[/magenta]")
        lessons_learned = []
        while True:
            lesson = safe_prompt_ask("添加一条经验教训（留空结束）", default="")
            if not lesson:
                break
            lessons_learned.append(lesson)
        
        console.print("\\n[cyan]🔧 过程改进建议：[/cyan]")
        improvements = []
        while True:
            improvement = safe_prompt_ask("添加一个改进建议（留空结束）", default="")
            if not improvement:
                break
            improvements.append(improvement)
        
        # 评分
        console.print("\\n[bold]📊 各项评分 (1-5分)：[/bold]")
        deliverables_quality = safe_int_prompt_ask("交付物质量", default=3, show_default=True)
        stakeholder_satisfaction = safe_int_prompt_ask("利益相关者满意度", default=3, show_default=True)
        team_performance = safe_int_prompt_ask("团队表现", default=3, show_default=True)
        communication = safe_int_prompt_ask("沟通有效性", default=3, show_default=True)
        collaboration = safe_int_prompt_ask("协作质量", default=3, show_default=True)
        risk_management = safe_int_prompt_ask("风险管理有效性", default=3, show_default=True)
    else:
        # 非交互模式，使用基本信息
        project_id = project_start = project_end = ""
        original_timeline = actual_timeline = None
        objectives_met = objectives_missed = achievements = challenges = []
        lessons_learned = improvements = []
        deliverables_quality = stakeholder_satisfaction = team_performance = 3
        communication = collaboration = risk_management = 3
    
    # 调用AI可调用工具函数
    success, message, retro_info = create_project_retrospective(
        project_name=project_name,
        project_id=project_id if project_id else None,
        project_start_date=project_start if project_start else None,
        project_end_date=project_end if project_end else None,
        original_timeline_days=original_timeline,
        actual_timeline_days=actual_timeline,
        objectives_met=objectives_met,
        objectives_missed=objectives_missed,
        achievements=achievements,
        challenges=challenges,
        lessons_learned=lessons_learned,
        process_improvements=improvements,
        deliverables_quality=deliverables_quality,
        stakeholder_satisfaction=stakeholder_satisfaction,
        team_performance=team_performance,
        communication_effectiveness=communication,
        collaboration_quality=collaboration,
        risk_management_effectiveness=risk_management,
        config=config
    )
    
    if success:
        console.print(f"\\n[green]✅ {message}")
        
        if retro_info:
            # 显示复盘摘要
            table = Table(title="项目复盘摘要")
            table.add_column("指标", style="cyan")
            table.add_column("值", style="green")
            
            table.add_row("复盘ID", retro_info["review_id"][:8])
            table.add_row("项目名称", retro_info["project_name"])
            table.add_row("项目持续时间", f"{retro_info['project_duration_days']} 天")
            
            if retro_info["timeline_variance_percent"] is not None:
                variance = retro_info["timeline_variance_percent"]
                variance_text = f"{variance:+.1f}%" if variance != 0 else "准时完成"
                table.add_row("时间偏差", variance_text)
            
            table.add_row("目标完成率", f"{retro_info['objective_completion_rate']:.1f}%")
            table.add_row("成就数量", str(retro_info["total_achievements"]))
            table.add_row("挑战数量", str(retro_info["total_challenges"]))
            table.add_row("经验教训", str(retro_info["total_lessons"]))
            table.add_row("改进建议", str(retro_info["total_improvements"]))
            
            console.print(table)
            
            # 显示质量评分
            ratings = retro_info["quality_ratings"]
            console.print("\\n[bold]📊 质量评分：[/bold]")
            for area, score in ratings.items():
                status = "优秀" if score >= 4 else "良好" if score >= 3 else "需改进"
                console.print(f"  • {area.replace('_', ' ').title()}: {score}/5 ({status})")
    else:
        console.print(f"[red]❌ {message}")
        raise typer.Exit(1)


@review_app.command("decision")
def track_decision_command(
    title: str = typer.Argument(..., help="决策标题")
) -> None:
    """跟踪重要决策"""
    
    config = PMConfig()
    
    console.print(Panel(
        f"[bold blue]⚖️ 跟踪重要决策[/bold blue]\\n\\n"
        f"决策: {title}",
        title="📝 决策跟踪",
        border_style="blue"
    ))
    
    # 交互式收集决策信息
    decision_context = safe_prompt_ask("决策背景", default="")
    
    console.print("\\n[cyan]考虑的选项（至少输入一个）：[/cyan]")
    options = []
    while True:
        option = safe_prompt_ask("添加一个选项（留空结束）", default="")
        if not option and len(options) == 0:
            console.print("[yellow]⚠️ 至少需要一个选项")
            continue
        if not option:
            break
        options.append(option)
    
    chosen_option = safe_prompt_ask("选择的方案")
    decision_rationale = safe_prompt_ask("决策理由")
    
    console.print("\\n[green]预期结果：[/green]")
    expected_outcomes = []
    while True:
        outcome = safe_prompt_ask("添加一个预期结果（留空结束）", default="")
        if not outcome:
            break
        expected_outcomes.append(outcome)
    
    decision_maker = safe_prompt_ask("决策者", default="自己")
    decision_date = safe_prompt_ask("决策日期 (YYYY-MM-DD，留空为今天)", default="")
    
    # 过程评分
    console.print("\\n[bold]📊 决策过程评分 (1-5分)：[/bold]")
    information_quality = safe_int_prompt_ask("信息质量", default=3, show_default=True)
    analysis_depth = safe_int_prompt_ask("分析深度", default=3, show_default=True)
    stakeholder_involvement = safe_int_prompt_ask("利益相关者参与度", default=3, show_default=True)
    time_pressure = safe_int_prompt_ask("时间压力", default=3, show_default=True)
    decision_confidence = safe_int_prompt_ask("决策信心", default=3, show_default=True)
    
    # 标签和项目关联
    tags = []
    if Confirm.ask("是否添加标签？", default=False):
        while True:
            tag = safe_prompt_ask("添加标签（留空结束）", default="")
            if not tag:
                break
            tags.append(tag)
    
    related_project = safe_prompt_ask("相关项目ID（可留空）", default="")
    
    # 调用AI可调用工具函数
    success, message, decision_info = track_decision(
        title=title,
        decision_context=decision_context,
        options_considered=options,
        chosen_option=chosen_option,
        decision_rationale=decision_rationale,
        expected_outcomes=expected_outcomes,
        decision_maker=decision_maker,
        decision_date=decision_date if decision_date else None,
        information_quality=information_quality,
        analysis_depth=analysis_depth,
        stakeholder_involvement=stakeholder_involvement,
        time_pressure=time_pressure,
        decision_confidence=decision_confidence,
        tags=tags if tags else None,
        related_project_id=related_project if related_project else None,
        config=config
    )
    
    if success:
        console.print(f"\\n[green]✅ {message}")
        
        if decision_info:
            # 显示决策摘要
            table = Table(title="决策跟踪摘要")
            table.add_column("属性", style="cyan")
            table.add_column("值", style="green")
            
            table.add_row("决策ID", decision_info["decision_id"][:8])
            table.add_row("决策日期", decision_info["decision_date"])
            table.add_row("决策者", decision_info["decision_maker"])
            table.add_row("选择方案", decision_info["chosen_option"])
            table.add_row("考虑选项数", str(decision_info["options_count"]))
            table.add_row("预期结果数", str(decision_info["expected_outcomes_count"]))
            table.add_row("决策质量评分", f"{decision_info['decision_quality_score']:.1f}/5")
            
            console.print(table)
            
            console.print("\\n[dim]💡 提示：30天后可以使用 'pm review evaluate <decision_id>' 评估决策结果")
    else:
        console.print(f"[red]❌ {message}")
        raise typer.Exit(1)


@review_app.command("stats")
def show_statistics(
    days: int = typer.Option(90, "--days", "-d", help="统计天数")
) -> None:
    """显示回顾统计信息"""
    
    config = PMConfig()
    
    # 调用AI可调用工具函数
    success, message, stats_info = get_review_statistics(days, config)
    
    if not success:
        console.print(f"[red]❌ {message}")
        return
    
    console.print(f"[bold]📊 回顾统计（过去 {days} 天）[/bold]")
    
    # 基础统计
    basic_table = Table(title="基础统计")
    basic_table.add_column("指标", style="cyan")
    basic_table.add_column("数值", style="green")
    
    basic_table.add_row("总回顾数", str(stats_info["total_reviews"]))
    basic_table.add_row("完成回顾数", str(stats_info["completed_reviews"]))
    basic_table.add_row("完成率", f"{stats_info['completion_rate']:.1f}%")
    basic_table.add_row("日均回顾数", str(stats_info["daily_average_reviews"]))
    basic_table.add_row("总行动项", str(stats_info["total_action_items"]))
    basic_table.add_row("总成长洞察", str(stats_info["total_insights"]))
    
    console.print(basic_table)
    
    # 按类型分布
    if stats_info["reviews_by_type"]:
        console.print("\\n[bold]📋 回顾类型分布：[/bold]")
        for review_type, count in stats_info["reviews_by_type"].items():
            console.print(f"  • {review_type}: {count} 个")
    
    # 平均评分
    ratings = stats_info["average_ratings"]
    ratings_table = Table(title="平均评分")
    ratings_table.add_column("维度", style="cyan")
    ratings_table.add_column("评分", style="yellow")
    ratings_table.add_column("趋势", style="green")
    
    for dimension, score in ratings.items():
        trend = stats_info.get(f"{dimension.split('_')[0]}_trend", "中")
        ratings_table.add_row(
            dimension.replace("_", " ").title(),
            f"{score}/5",
            trend
        )
    
    console.print(ratings_table)
    
    # 最活跃的成长领域
    if stats_info["most_active_growth_areas"]:
        console.print("\\n[bold]🌱 最活跃成长领域：[/bold]")
        for area, count in stats_info["most_active_growth_areas"]:
            console.print(f"  • {area.replace('_', ' ').title()}: {count} 个洞察")


# 添加到主CLI应用
if __name__ == "__main__":
    review_app()