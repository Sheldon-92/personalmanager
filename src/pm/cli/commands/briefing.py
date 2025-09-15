"""简报和会话管理CLI命令 - PersonalManager自进化核心功能

提供用户工作简报、Claude技术简报生成和会话管理功能
"""

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from typing import Optional
import json
from datetime import datetime

from pm.core.config import PMConfig
from pm.core.briefing_generator import BriefingGenerator
from pm.core.session_manager import SessionManager

console = Console()


def generate_briefing(
    force_refresh: bool = False,
    show_claude_context: bool = False,
    quiet: bool = False
) -> None:
    """生成双向简报（用户工作简报 + Claude技术简报）"""

    config = PMConfig()
    if not config.is_initialized():
        console.print(Panel(
            "[yellow]系统未初始化。请先运行 [cyan]pm setup[/cyan] 进行设置。",
            title="⚠️ 未初始化",
            border_style="yellow"
        ))
        return

    try:
        briefing_generator = BriefingGenerator(config)

        if not quiet:
            with console.status("[bold blue]生成双向简报...", spinner="dots"):
                user_briefing, claude_context = briefing_generator.generate_dual_briefing(force_refresh)
        else:
            user_briefing, claude_context = briefing_generator.generate_dual_briefing(force_refresh)

        if not quiet:
            # 显示用户简报
            console.print("\n")
            md = Markdown(user_briefing)
            console.print(md)

            # 如果请求，显示Claude上下文摘要
            if show_claude_context:
                console.print("\n" + "="*60)
                console.print("🤖 Claude技术简报摘要")
                console.print("="*60)

                # 显示核心信息
                identity = claude_context.get("identity", {})
                console.print(f"角色: {identity.get('role', 'PersonalManager Assistant')}")

                work_context = claude_context.get("current_work_context", {})
                console.print(f"当前任务数: {work_context.get('total_tasks', 0)}")
                console.print(f"收件箱: {work_context.get('inbox_tasks', 0)} | 下一步行动: {work_context.get('next_actions', 0)}")

                functions = claude_context.get("available_functions", {})
                console.print(f"可用功能: {functions.get('cli_commands_count', 0)} CLI命令, {functions.get('integrations_count', 0)} 集成模块")

                today_focus = claude_context.get("today_focus", [])
                if today_focus:
                    console.print("\n今日重点:")
                    for item in today_focus[:3]:
                        console.print(f"  • {item}")

            console.print(Panel(
                f"[green]✅ 双向简报生成完成！[/green]\n\n"
                f"• 用户简报: ~/.personalmanager/session/user_briefing.md\n"
                f"• Claude上下文: ~/.personalmanager/session/claude_context.json\n\n"
                f"现在可以启动Claude Code，它将自动获得完整上下文。",
                title="🎉 简报完成",
                border_style="green"
            ))

    except Exception as e:
        console.print(Panel(
            f"[red]❌ 简报生成失败: {str(e)}[/red]",
            title="生成错误",
            border_style="red"
        ))


def start_session(
    force_refresh: bool = False,
    no_briefing: bool = False
) -> None:
    """启动PersonalManager完整会话"""

    config = PMConfig()
    if not config.is_initialized():
        console.print(Panel(
            "[yellow]系统未初始化。请先运行 [cyan]pm setup[/cyan] 进行设置。",
            title="⚠️ 未初始化",
            border_style="yellow"
        ))
        return

    try:
        session_manager = SessionManager(config)

        console.print(Panel(
            "[cyan]🚀 启动PersonalManager会话...[/cyan]",
            title="会话启动",
            border_style="blue"
        ))

        # 启动会话（包含简报生成）
        session_info = session_manager.start_session(
            force_refresh=force_refresh,
            show_briefing=not no_briefing
        )

        # 显示会话启动成功信息
        if session_info.get("capability_changes", {}).get("has_changes"):
            console.print("\n🆕 检测到功能更新！我学会了新技能。")

        console.print(Panel(
            f"[green]✅ PersonalManager会话已启动[/green]\n\n"
            f"会话ID: {session_info.get('session_id', 'unknown')}\n"
            f"简报已生成: {'✅' if session_info.get('briefing_generated') else '❌'}\n"
            f"功能已刷新: {'✅' if session_info.get('capabilities_refreshed') else '❌'}\n\n"
            f"现在可以高效协作了！试试：\n"
            f"• [cyan]pm inbox[/cyan] - 查看待处理任务\n"
            f"• [cyan]pm clarify[/cyan] - 澄清收件箱任务\n"
            f"• [cyan]pm gmail scan[/cyan] - 处理重要邮件",
            title="🎉 会话就绪",
            border_style="green"
        ))

    except Exception as e:
        console.print(Panel(
            f"[red]❌ 会话启动失败: {str(e)}[/red]",
            title="启动错误",
            border_style="red"
        ))


def refresh_capabilities() -> None:
    """刷新PersonalManager功能注册表"""

    config = PMConfig()
    if not config.is_initialized():
        console.print(Panel(
            "[yellow]系统未初始化。请先运行 [cyan]pm setup[/cyan] 进行设置。",
            title="⚠️ 未初始化",
            border_style="yellow"
        ))
        return

    try:
        session_manager = SessionManager(config)

        with console.status("[bold blue]刷新功能注册表...", spinner="dots"):
            refresh_result = session_manager.refresh_capabilities()

        changes = refresh_result.get("changes", {})
        summary = refresh_result.get("summary", {})

        # 显示刷新结果
        console.print(Panel(
            f"[green]✅ 功能刷新完成[/green]\n\n"
            f"发现功能:\n"
            f"• CLI命令: {summary.get('cli_commands', 0)} 个\n"
            f"• 集成模块: {summary.get('integrations', 0)} 个\n"
            f"• API方法: {summary.get('api_methods', 0)} 个\n\n"
            f"更新时间: {refresh_result.get('refresh_time', 'unknown')}",
            title="🔄 功能刷新",
            border_style="green"
        ))

        # 如果有变更，显示详细信息
        if changes.get("has_changes"):
            console.print("\n🆕 检测到功能变更:")

            if changes.get("new_functions"):
                console.print("\n新增功能:")
                for func in changes["new_functions"]:
                    console.print(f"  + {func}")

            if changes.get("updated_functions"):
                console.print("\n更新功能:")
                for func in changes["updated_functions"]:
                    console.print(f"  ~ {func}")

    except Exception as e:
        console.print(Panel(
            f"[red]❌ 功能刷新失败: {str(e)}[/red]",
            title="刷新错误",
            border_style="red"
        ))


def show_context_summary() -> None:
    """显示Claude上下文摘要"""

    config = PMConfig()
    if not config.is_initialized():
        console.print(Panel(
            "[yellow]系统未初始化。请先运行 [cyan]pm setup[/cyan] 进行设置。",
            title="⚠️ 未初始化",
            border_style="yellow"
        ))
        return

    try:
        session_manager = SessionManager(config)
        context_summary = session_manager.generate_context_summary()

        console.print(Panel(
            context_summary,
            title="🤖 Claude上下文摘要",
            border_style="blue"
        ))

    except Exception as e:
        console.print(Panel(
            f"[red]❌ 获取上下文失败: {str(e)}[/red]",
            title="上下文错误",
            border_style="red"
        ))


def check_session_health() -> None:
    """检查会话健康状态"""

    config = PMConfig()
    if not config.is_initialized():
        console.print(Panel(
            "[yellow]系统未初始化。请先运行 [cyan]pm setup[/cyan] 进行设置。",
            title="⚠️ 未初始化",
            border_style="yellow"
        ))
        return

    try:
        session_manager = SessionManager(config)
        health_status = session_manager.check_session_health()

        # 创建健康状态表格
        health_table = Table(show_header=True, header_style="bold magenta")
        health_table.add_column("检查项目", style="cyan")
        health_table.add_column("状态", style="green")
        health_table.add_column("说明", style="yellow")

        # 总体健康状态
        overall_status = "✅ 健康" if health_status["overall_healthy"] else "❌ 异常"
        health_table.add_row("总体状态", overall_status, "系统整体运行状态")

        # 具体问题
        if health_status["issues"]:
            for issue in health_status["issues"]:
                health_table.add_row("问题", "⚠️ 发现", issue)

        # 建议
        if health_status["recommendations"]:
            for rec in health_status["recommendations"]:
                health_table.add_row("建议", "💡 推荐", rec)

        console.print(Panel(
            health_table,
            title=f"🏥 会话健康检查 ({health_status['timestamp']})",
            border_style="green" if health_status["overall_healthy"] else "yellow"
        ))

        if not health_status["overall_healthy"]:
            console.print(Panel(
                "[yellow]发现问题，建议运行以下命令修复：[/yellow]\n"
                "• [cyan]pm start-session --force-refresh[/cyan] - 强制刷新会话\n"
                "• [cyan]pm briefing --force-refresh[/cyan] - 重新生成简报",
                title="🔧 修复建议",
                border_style="yellow"
            ))

    except Exception as e:
        console.print(Panel(
            f"[red]❌ 健康检查失败: {str(e)}[/red]",
            title="检查错误",
            border_style="red"
        ))


def show_session_info() -> None:
    """显示会话信息"""

    config = PMConfig()
    if not config.is_initialized():
        console.print(Panel(
            "[yellow]系统未初始化。请先运行 [cyan]pm setup[/cyan] 进行设置。",
            title="⚠️ 未初始化",
            border_style="yellow"
        ))
        return

    try:
        session_manager = SessionManager(config)
        session_summary = session_manager.get_session_summary()

        # 创建会话信息表格
        info_table = Table(show_header=True, header_style="bold magenta")
        info_table.add_column("项目", style="cyan")
        info_table.add_column("状态", style="green")
        info_table.add_column("详情", style="yellow")

        # 会话状态
        session_active = "✅ 活跃" if session_summary.get("session_active") else "❌ 未启动"
        info_table.add_row("会话状态", session_active, "PersonalManager会话是否活跃")

        # 最后简报时间
        last_briefing = session_summary.get("last_briefing", "未知")
        if last_briefing != "未知":
            try:
                briefing_time = datetime.fromisoformat(last_briefing)
                last_briefing = briefing_time.strftime("%Y-%m-%d %H:%M")
            except:
                pass
        info_table.add_row("最后简报", last_briefing, "上次生成简报的时间")

        # 功能统计
        capabilities = session_summary.get("capabilities_summary", {})
        if capabilities:
            info_table.add_row("CLI命令", str(capabilities.get("cli_commands", 0)), "可用的命令行功能")
            info_table.add_row("集成模块", str(capabilities.get("integrations", 0)), "已集成的服务模块")
            info_table.add_row("API方法", str(capabilities.get("api_methods", 0)), "可调用的API方法")

        # 最近变更
        recent_changes = session_summary.get("recent_changes", 0)
        info_table.add_row("最近变更", str(recent_changes), "功能变更记录数量")

        console.print(Panel(
            info_table,
            title="📊 PersonalManager 会话信息",
            border_style="blue"
        ))

        # 显示健康状态
        health_status = session_summary.get("health_status", {})
        if health_status:
            overall_healthy = health_status.get("overall_healthy", False)
            status_color = "green" if overall_healthy else "yellow"
            status_text = "✅ 健康" if overall_healthy else "⚠️ 需要关注"

            console.print(Panel(
                f"[{status_color}]系统状态: {status_text}[/{status_color}]",
                title="🏥 健康状态",
                border_style=status_color
            ))

        # 操作建议
        if not session_summary.get("session_active"):
            console.print(Panel(
                "[yellow]会话未启动，建议运行：[/yellow]\n"
                "• [cyan]pm start-session[/cyan] - 启动完整会话",
                title="💡 操作建议",
                border_style="yellow"
            ))

    except Exception as e:
        console.print(Panel(
            f"[red]❌ 获取会话信息失败: {str(e)}[/red]",
            title="信息错误",
            border_style="red"
        ))


def show_capabilities() -> None:
    """显示PersonalManager功能清单"""

    config = PMConfig()
    if not config.is_initialized():
        console.print(Panel(
            "[yellow]系统未初始化。请先运行 [cyan]pm setup[/cyan] 进行设置。",
            title="⚠️ 未初始化",
            border_style="yellow"
        ))
        return

    try:
        from pm.core.function_registry import FunctionRegistry

        function_registry = FunctionRegistry(config)
        registry = function_registry.load_registry()

        if not registry:
            console.print(Panel(
                "[yellow]功能注册表为空。请运行 [cyan]pm capabilities refresh[/cyan] 刷新功能列表。",
                title="⚠️ 无功能数据",
                border_style="yellow"
            ))
            return

        # 显示功能摘要
        summary = function_registry.get_capability_summary()

        summary_table = Table(show_header=True, header_style="bold magenta")
        summary_table.add_column("功能类型", style="cyan")
        summary_table.add_column("数量", style="green", justify="center")
        summary_table.add_column("说明", style="yellow")

        summary_table.add_row("CLI命令", str(summary.get("cli_commands", 0)), "命令行接口功能")
        summary_table.add_row("集成模块", str(summary.get("integrations", 0)), "外部服务集成")
        summary_table.add_row("API方法", str(summary.get("api_methods", 0)), "程序接口方法")
        summary_table.add_row("数据模型", str(summary.get("models", 0)), "数据结构定义")
        summary_table.add_row("智能代理", str(summary.get("agents", 0)), "AI代理组件")

        console.print(Panel(
            summary_table,
            title=f"🛠️ PersonalManager 功能概览 (更新时间: {summary.get('last_updated', '未知')})",
            border_style="blue"
        ))

        # 显示核心集成模块详情
        integrations = registry.get("integrations", {})
        if integrations:
            console.print("\n📋 核心集成模块:")
            for name, info in list(integrations.items())[:5]:  # 只显示前5个
                desc = info.get("description", "无描述")
                console.print(f"  • [cyan]{name}[/cyan]: {desc}")

        # 显示核心CLI命令
        cli_commands = registry.get("cli_commands", {})
        if cli_commands:
            console.print("\n⚡ 核心CLI命令:")
            for name, info in list(cli_commands.items())[:8]:  # 只显示前8个
                desc = info.get("description", "无描述")
                console.print(f"  • [cyan]pm {name}[/cyan]: {desc}")

        console.print(Panel(
            "[green]💡 运行 [cyan]pm capabilities refresh[/cyan] 刷新功能列表\n"
            "💡 运行 [cyan]pm briefing --claude-context[/cyan] 查看完整技术简报",
            title="操作提示",
            border_style="green"
        ))

    except Exception as e:
        console.print(Panel(
            f"[red]❌ 获取功能清单失败: {str(e)}[/red]",
            title="功能错误",
            border_style="red"
        ))