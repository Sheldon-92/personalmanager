"""Main CLI entry point for PersonalManager."""

import typer
from rich.console import Console
from rich.panel import Panel
from typing import Optional

from pm.core.config import PMConfig
from pm.cli.commands.setup import setup_wizard
from pm.cli.commands.help import help_system
from pm.cli.commands.guide import show_best_practices
from pm.cli.commands.privacy import (
    show_privacy_info, export_data, backup_data, 
    cleanup_old_data, clear_all_data, verify_data_integrity
)
from pm.cli.commands.projects import (
    show_projects_overview, show_project_status, search_projects
)
from pm.cli.commands.update import update_project_status, force_refresh_all
from pm.cli.commands.monitor import (
    start_monitoring, stop_monitoring, show_monitoring_status, 
    show_monitoring_logs, restart_monitoring
)
from pm.cli.commands.tasks import (
    capture_task, show_inbox, show_next_actions, show_task_details, show_classification_stats,
    show_context_detection, show_smart_next_actions, show_intelligent_recommendations
)
from pm.cli.commands.clarify import clarify_tasks
from pm.cli.commands.explain import explain_recommendation
from pm.cli.commands.preferences import show_preference_learning_stats
from pm.cli.commands.auth import google_auth_login, google_auth_logout, show_auth_status
from pm.cli.commands.calendar import sync_calendar, show_today_schedule, show_weekly_schedule, create_event_from_task, delete_calendar_events
from pm.cli.commands.tasks_sync import sync_from_google_tasks, sync_to_google_tasks, show_google_tasks_lists, show_sync_status
from pm.cli.commands.gmail import scan_important_emails, show_email_preview, show_email_stats
from pm.cli.commands.report import update_project_report, show_ai_service_status, create_sample_project_config
from pm.cli.commands.habits import (
    create_new_habit, track_habit, show_habit_status, show_today_plan, 
    analyze_trends, get_suggestions
)
from pm.cli.commands.deep_work import deep_work_app
from pm.cli.commands.review import review_app
from pm.cli.commands.obsidian import obsidian_app
from pm.cli.commands.doctor import doctor_app
from pm.cli.commands.ai import ai_app
from pm.cli.commands.briefing import (
    generate_briefing, start_session, refresh_capabilities,
    show_context_summary, check_session_health, show_session_info, show_capabilities
)
from pm.core.interaction_manager import InteractionManager
from pm.core.command_executor import CommandExecutor

app = typer.Typer(
    name="pm",
    help="PersonalManager Agent - AI-driven personal management system",
    no_args_is_help=False,
    rich_markup_mode="rich"
)

console = Console()


@app.command("setup")
def setup(
    reset: bool = typer.Option(False, "--reset", help="重置所有配置")
) -> None:
    """启动PersonalManager系统设置向导"""
    try:
        setup_wizard(reset=reset)
        console.print(Panel(
            "[green]✅ PersonalManager 设置完成！\n"
            "现在您可以开始使用以下命令：\n"
            "• [cyan]pm help[/cyan] - 查看帮助\n"
            "• [cyan]pm capture[/cyan] - 捕获新任务\n"
            "• [cyan]pm today[/cyan] - 获取今日建议",
            title="🎉 设置成功",
            border_style="green"
        ))
    except Exception as e:
        console.print(Panel(
            f"[red]❌ 设置失败: {str(e)}",
            title="设置错误",
            border_style="red"
        ))
        raise typer.Exit(1)


@app.command("help") 
def help_cmd(
    command: Optional[str] = typer.Argument(None, help="要获取帮助的具体命令")
) -> None:
    """显示命令帮助信息"""
    help_system(command)


@app.command("version")
def version() -> None:
    """显示版本信息"""
    from pm import __version__
    console.print(f"PersonalManager Agent v{__version__}")


@app.command("guide")
def guide(
    category: Optional[str] = typer.Argument(None, help="指导类别：gtd, projects, scenarios, interactive")
) -> None:
    """显示最佳实践指导和交互式教程"""
    show_best_practices(category)


# 项目管理命令组
projects_app = typer.Typer(help="项目状态管理工具")
app.add_typer(projects_app, name="projects")

@projects_app.command("overview")
def projects_overview(
    sort: str = typer.Option("health", help="排序方式: health, priority, progress, name")
) -> None:
    """显示所有项目的状态概览"""
    show_projects_overview(sort_by=sort)

@projects_app.command("search")
def projects_search(
    query: str = typer.Argument(..., help="搜索关键词")
) -> None:
    """搜索项目"""
    search_projects(query)

@projects_app.command("refresh")
def projects_refresh() -> None:
    """强制刷新所有项目状态（清除缓存）"""
    force_refresh_all()

@app.command("project")
def project(
    subcommand: str = typer.Argument(..., help="子命令: status"),
    name: Optional[str] = typer.Argument(None, help="项目名称")
) -> None:
    """项目管理命令"""
    if subcommand == "status":
        if not name:
            console.print("[red]请指定项目名称: pm project status <项目名>")
            raise typer.Exit(1)
        show_project_status(name)
    else:
        console.print(f"[red]未知子命令: {subcommand}")
        console.print("可用子命令: status")
        raise typer.Exit(1)

# 隐私和数据管理命令组
privacy_app = typer.Typer(help="数据隐私和管理工具")
app.add_typer(privacy_app, name="privacy")

@privacy_app.command("info")
def privacy_info() -> None:
    """显示数据隐私和存储信息"""
    show_privacy_info()

@privacy_app.command("export")
def privacy_export() -> None:
    """导出所有用户数据"""
    export_data()

@privacy_app.command("backup")
def privacy_backup() -> None:
    """创建数据备份"""
    backup_data()

@privacy_app.command("cleanup")
def privacy_cleanup() -> None:
    """清理过期数据"""
    cleanup_old_data()

@privacy_app.command("clear")
def privacy_clear() -> None:
    """完全清除所有数据（危险操作）"""
    clear_all_data()

@privacy_app.command("verify")
def privacy_verify() -> None:
    """验证数据完整性"""
    verify_data_integrity()

# 更新命令组
update_app = typer.Typer(help="状态更新工具")
app.add_typer(update_app, name="update")

@update_app.command("project")
def update_project(
    name: Optional[str] = typer.Argument(None, help="项目名称，留空更新所有项目")
) -> None:
    """更新项目状态"""
    update_project_status(name)

# 监控命令组
monitor_app = typer.Typer(help="项目文件监控工具")
app.add_typer(monitor_app, name="monitor")

@monitor_app.command("start")
def monitor_start() -> None:
    """启动项目文件监控"""
    start_monitoring()

@monitor_app.command("stop")
def monitor_stop() -> None:
    """停止项目文件监控"""
    stop_monitoring()

@monitor_app.command("status")
def monitor_status() -> None:
    """显示监控状态"""
    show_monitoring_status()

@monitor_app.command("logs")
def monitor_logs(
    limit: int = typer.Option(50, help="显示日志条数")
) -> None:
    """显示监控日志"""
    show_monitoring_logs(limit)

@monitor_app.command("restart")
def monitor_restart() -> None:
    """重启文件监控"""
    restart_monitoring()

# 任务管理命令
@app.command("capture")
def capture(
    content: str = typer.Argument(..., help="任务内容，支持多行文本")
) -> None:
    """快速捕获任务到收件箱"""
    capture_task(content)

@app.command("inbox")
def inbox() -> None:
    """显示收件箱任务列表"""
    show_inbox()

@app.command("next")
def next_actions(
    context: Optional[str] = typer.Argument(None, help="情境过滤，如 @电脑, @电话")
) -> None:
    """显示下一步行动列表"""
    show_next_actions(context)

@app.command("task")
def task(
    task_id: str = typer.Argument(..., help="任务ID（支持短ID）")
) -> None:
    """显示任务详细信息"""
    show_task_details(task_id)

@app.command("clarify")
def clarify() -> None:
    """启动GTD任务理清流程"""
    clarify_tasks()

@app.command("learn")
def learn() -> None:
    """显示智能分类学习统计"""
    show_classification_stats()

@app.command("context")
def context() -> None:
    """显示当前情境检测信息"""
    show_context_detection()

@app.command("smart-next")
def smart_next(
    context: Optional[str] = typer.Argument(None, help="指定情境过滤，如 @电脑"),
    energy: Optional[str] = typer.Option(None, "--energy", help="精力水平：low/medium/high")
) -> None:
    """智能情境过滤的下一步行动"""
    show_smart_next_actions(context, energy)

@app.command("recommend")
def recommend(
    context: Optional[str] = typer.Argument(None, help="指定情境过滤，如 @电脑"),
    count: int = typer.Option(5, "--count", help="推荐数量，默认5个")
) -> None:
    """基于多书籍理论的智能任务推荐"""
    show_intelligent_recommendations(context, count)


@app.command("today")
def today(
    count: int = typer.Option(3, "--count", help="今日重点推荐数量，默认3个")
) -> None:
    """获取今日重点推荐（别名，等价于 recommend --count 3）"""
    show_intelligent_recommendations(None, count)

@app.command("explain")
def explain(
    task_id: str = typer.Argument(..., help="任务ID（支持短ID）")
) -> None:
    """解释任务推荐的详细逻辑"""
    explain_recommendation(task_id)

@app.command("preferences")
def preferences() -> None:
    """显示用户偏好学习统计"""
    show_preference_learning_stats()


# Google服务认证命令组
auth_app = typer.Typer(help="Google服务认证管理")
app.add_typer(auth_app, name="auth")

@auth_app.command("login")
def auth_login(
    service: str = typer.Argument("google", help="认证服务: google")
) -> None:
    """登录Google服务认证"""
    if service == "google":
        google_auth_login()
    else:
        console.print(f"[red]不支持的服务: {service}[/red]")
        console.print("支持的服务: google")
        raise typer.Exit(1)

@auth_app.command("logout")
def auth_logout(
    service: str = typer.Argument("google", help="认证服务: google")
) -> None:
    """登出服务认证"""
    if service == "google":
        google_auth_logout()
    else:
        console.print(f"[red]不支持的服务: {service}[/red]")
        console.print("支持的服务: google")
        raise typer.Exit(1)

@auth_app.command("status")
def auth_status() -> None:
    """显示认证状态"""
    show_auth_status()


# Google Calendar集成命令组
calendar_app = typer.Typer(help="Google Calendar集成管理")
app.add_typer(calendar_app, name="calendar")

@calendar_app.command("sync")
def calendar_sync() -> None:
    """同步Google Calendar事件为GTD任务"""
    sync_calendar()

@calendar_app.command("today")
def calendar_today() -> None:
    """显示今日日程"""
    show_today_schedule()

@calendar_app.command("week")
def calendar_week() -> None:
    """显示本周日程"""
    show_weekly_schedule()

@calendar_app.command("create")
def calendar_create(
    task_id: str = typer.Argument(..., help="任务ID（支持短ID）")
) -> None:
    """为GTD任务创建Google Calendar事件"""
    create_event_from_task(task_id)

@calendar_app.command("delete")
def calendar_delete(
    title_pattern: str = typer.Argument(..., help="要删除的事件标题模式（如：游泳）")
) -> None:
    """删除包含指定标题的Google Calendar事件"""
    delete_calendar_events(title_pattern)


# Google Tasks集成命令组
tasks_app = typer.Typer(help="Google Tasks集成管理")
app.add_typer(tasks_app, name="tasks")

@tasks_app.command("sync-from")
def tasks_sync_from() -> None:
    """从Google Tasks同步任务到GTD系统"""
    sync_from_google_tasks()

@tasks_app.command("sync-to")
def tasks_sync_to(
    task_id: str = typer.Argument(..., help="任务ID（支持短ID）")
) -> None:
    """将GTD任务同步到Google Tasks"""
    sync_to_google_tasks(task_id)

@tasks_app.command("lists")
def tasks_lists() -> None:
    """显示Google Tasks列表"""
    show_google_tasks_lists()

@tasks_app.command("status")
def tasks_status() -> None:
    """显示Google Tasks同步状态"""
    show_sync_status()


# Gmail集成命令组
gmail_app = typer.Typer(help="Gmail重要邮件处理")
app.add_typer(gmail_app, name="gmail")

@gmail_app.command("scan")
def gmail_scan(
    days: int = typer.Option(1, "--days", help="扫描过去多少天的邮件")
) -> None:
    """扫描重要邮件并转换为GTD任务"""
    scan_important_emails(days)

@gmail_app.command("preview")
def gmail_preview(
    days: int = typer.Option(1, "--days", help="预览过去多少天的邮件")
) -> None:
    """预览重要邮件（不转换为任务）"""
    show_email_preview(days)

@gmail_app.command("stats")
def gmail_stats() -> None:
    """显示Gmail集成统计信息"""
    show_email_stats()


# AI报告生成命令组 - Sprint 11-12核心功能
report_app = typer.Typer(help="AI驱动的项目报告生成")
app.add_typer(report_app, name="report")


# 习惯管理命令组 - Sprint 13新功能，AI可调用工具架构示范
habits_app = typer.Typer(help="习惯跟踪和管理（基于原子习惯理论）")
app.add_typer(habits_app, name="habits")

# 深度工作管理命令组 - Sprint 14新功能，AI可调用工具架构
app.add_typer(deep_work_app, name="deepwork")

# 回顾与反思管理命令组 - Sprint 16新功能，AI可调用工具架构
app.add_typer(review_app, name="review")
app.add_typer(obsidian_app, name="obsidian")

# 系统诊断命令组 - Phase 2新功能，环境自检与诊断
app.add_typer(doctor_app, name="doctor")

# AI集成命令组 - Sprint 3核心功能，AI服务集成与协议标准化
app.add_typer(ai_app, name="ai")


# 简报和会话管理命令 - 自进化双向简报系统
@app.command("briefing")
def briefing(
    force_refresh: bool = typer.Option(False, "--force-refresh", help="强制刷新所有数据"),
    claude_context: bool = typer.Option(False, "--claude-context", help="显示Claude技术简报摘要"),
    quiet: bool = typer.Option(False, "--quiet", help="安静模式，不显示输出")
) -> None:
    """生成PersonalManager双向简报（用户工作简报 + Claude技术简报）"""
    generate_briefing(force_refresh, claude_context, quiet)


@app.command("start-session")
def start_session_cmd(
    force_refresh: bool = typer.Option(False, "--force-refresh", help="强制刷新功能和数据"),
    no_briefing: bool = typer.Option(False, "--no-briefing", help="不显示用户简报")
) -> None:
    """启动PersonalManager完整会话（推荐的启动方式）"""
    start_session(force_refresh, no_briefing)


# 会话管理命令组
session_app = typer.Typer(help="PersonalManager会话状态管理")
app.add_typer(session_app, name="session")

@session_app.command("info")
def session_info() -> None:
    """显示当前会话信息"""
    show_session_info()

@session_app.command("health")
def session_health() -> None:
    """检查会话健康状态"""
    check_session_health()

@session_app.command("context")
def session_context() -> None:
    """显示Claude上下文摘要"""
    show_context_summary()


# 功能管理命令组
capabilities_app = typer.Typer(help="PersonalManager功能发现和管理")
app.add_typer(capabilities_app, name="capabilities")

@capabilities_app.command("refresh")
def capabilities_refresh() -> None:
    """刷新PersonalManager功能注册表"""
    refresh_capabilities()

@capabilities_app.command("list")
def capabilities_list() -> None:
    """显示PersonalManager功能清单"""
    show_capabilities()

@report_app.command("update")
def report_update(
    project_name: Optional[str] = typer.Option(None, "--name", "-n", help="项目名称（可选）"),
    project_path: Optional[str] = typer.Option(None, "--path", "-p", help="项目路径（可选，默认当前目录）")
) -> None:
    """使用AI自动更新项目状态报告"""
    update_project_report(project_name, project_path)

@report_app.command("status")
def report_status() -> None:
    """显示AI服务状态"""
    show_ai_service_status()

@report_app.command("init")
def report_init() -> None:
    """在当前目录创建示例项目配置"""
    create_sample_project_config()


@habits_app.command("create")
def habits_create(
    name: str = typer.Argument(..., help="习惯名称"),
    category: str = typer.Option("other", "--category", "-c", help="习惯分类"),
    frequency: str = typer.Option("daily", "--frequency", "-f", help="执行频率"),
    difficulty: str = typer.Option("easy", "--difficulty", "-d", help="难度级别"),
    description: Optional[str] = typer.Option(None, "--desc", help="习惯描述"),
    cue: Optional[str] = typer.Option(None, "--cue", help="触发提示"),
    routine: Optional[str] = typer.Option(None, "--routine", help="具体行为"),
    reward: Optional[str] = typer.Option(None, "--reward", help="奖励机制"),
    duration: Optional[int] = typer.Option(None, "--duration", help="目标时长(分钟)"),
    reminder: Optional[str] = typer.Option(None, "--reminder", help="提醒时间 HH:MM")
) -> None:
    """创建新的习惯"""
    create_new_habit(name, category, frequency, difficulty, description, cue, routine, reward, duration, reminder)

@habits_app.command("track")
def habits_track(
    name: str = typer.Argument(..., help="习惯名称"),
    completed: bool = typer.Option(True, "--done/--skip", help="是否完成"),
    notes: Optional[str] = typer.Option(None, "--notes", "-n", help="备注"),
    quality: Optional[int] = typer.Option(None, "--quality", "-q", help="质量评分(1-5)"),
    record_date: Optional[str] = typer.Option(None, "--date", help="记录日期(YYYY-MM-DD)")
) -> None:
    """记录习惯完成情况"""
    track_habit(name, completed, notes, quality, record_date)

@habits_app.command("status")
def habits_status(
    name: Optional[str] = typer.Argument(None, help="习惯名称（可选）")
) -> None:
    """显示习惯状态"""
    show_habit_status(name)

@habits_app.command("today")
def habits_today() -> None:
    """显示今日习惯计划"""
    show_today_plan()

@habits_app.command("trends")
def habits_trends(
    name: Optional[str] = typer.Argument(None, help="习惯名称（可选）"),
    days: int = typer.Option(30, "--days", "-d", help="分析天数")
) -> None:
    """分析习惯趋势"""
    analyze_trends(name, days)

@habits_app.command("suggest")
def habits_suggest(
    name: str = typer.Argument(..., help="习惯名称")
) -> None:
    """获取习惯改进建议"""
    get_suggestions(name)


@app.command("interactive")
def interactive_mode() -> None:
    """启动交互式模式，支持编号选择和斜杠命令"""
    config = PMConfig()
    interaction_manager = InteractionManager(config)
    command_executor = CommandExecutor()

    console.print(Panel(
        "[green]🎯 进入PersonalManager交互模式\n\n"
        "• 输入数字选择操作 (如: 1, 2-4, 1,3)\n"
        "• 输入 / 查看快捷命令\n"
        "• 输入 'exit' 退出交互模式",
        title="🚀 交互模式",
        border_style="green"
    ))

    # 显示当前可选操作
    prompt = interaction_manager.get_interactive_prompt()
    console.print(prompt)

    while True:
        try:
            user_input = input("\n💬 请选择操作: ").strip()

            if user_input.lower() in ['exit', 'quit', 'q']:
                console.print("👋 退出交互模式")
                break

            if not user_input:
                continue

            # 处理用户输入
            result = interaction_manager.process_user_input(user_input)

            if result['type'] == 'slash_command':
                if user_input == '/':
                    # 显示斜杠命令帮助
                    help_text = interaction_manager.format_slash_help()
                    console.print(help_text)
                else:
                    console.print(f"🔄 执行命令: {user_input}")
                    exec_result = command_executor.execute_slash_command(user_input)

                    if exec_result['success']:
                        if exec_result.get('stdout'):
                            console.print(exec_result['stdout'])
                    else:
                        console.print(f"❌ 命令执行失败: {exec_result.get('error', '未知错误')}")

            elif result['type'] == 'number_choice':
                if result['commands']:
                    for cmd in result['commands']:
                        console.print(f"🔄 执行: {cmd}")

                        if cmd.startswith('/'):
                            exec_result = command_executor.execute_slash_command(cmd)
                        else:
                            exec_result = command_executor.execute_pm_command(cmd)

                        if exec_result['success']:
                            if exec_result.get('stdout'):
                                console.print(exec_result['stdout'])
                        else:
                            console.print(f"❌ 命令执行失败: {exec_result.get('error', '未知错误')}")
                else:
                    console.print(f"❌ 无效的选项编号: {', '.join(map(str, result['numbers']))}")

            elif result['type'] == 'regular_text':
                console.print(f"💭 自然语言输入: {user_input}")
                console.print("🤖 (暂不支持自然语言处理，请使用编号或斜杠命令)")

            # 刷新选项显示
            if result['type'] in ['number_choice', 'slash_command'] and user_input != '/':
                prompt = interaction_manager.get_interactive_prompt()
                console.print("\n" + prompt)

        except KeyboardInterrupt:
            console.print("\n👋 退出交互模式")
            break
        except Exception as e:
            console.print(f"❌ 错误: {str(e)}")


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(None, "--version", "-v", help="显示版本信息")
) -> None:
    """PersonalManager Agent - 智能化的个人项目与时间管理解决方案"""
    if version:
        from pm import __version__
        console.print(f"PersonalManager Agent v{__version__}")
        return

    if ctx.invoked_subcommand is None:
        # 检查是否已初始化
        config = PMConfig()
        if not config.is_initialized():
            console.print(Panel(
                "[yellow]👋 欢迎使用 PersonalManager Agent！\n\n"
                "看起来这是您第一次使用。请先运行设置向导：\n"
                "[cyan]pm setup[/cyan]",
                title="🚀 欢迎",
                border_style="blue"
            ))
        else:
            # 启动交互模式而不是显示静态帮助
            config = PMConfig()
            interaction_manager = InteractionManager(config)

            # 显示简洁的欢迎信息
            console.print(Panel(
                "[green]🎯 PersonalManager Agent 交互模式\n\n"
                "• 输入数字选择操作\n"
                "• 输入 / 查看快捷命令\n"
                "• 'pm help' 查看完整命令",
                title="📋 PersonalManager",
                border_style="green"
            ))

            # 显示当前可选操作
            prompt = interaction_manager.get_interactive_prompt()
            console.print(prompt)


if __name__ == "__main__":
    app()
