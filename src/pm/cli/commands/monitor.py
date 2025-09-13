"""Project monitoring and file watching commands."""

from typing import Optional
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
import time
import signal
import sys
import typer

from pm.core.config import PMConfig
from pm.agents.file_watcher import FileWatcherAgent, BackgroundFileWatcher
from pm.tools.monitor_tools import (
    start_file_monitoring,
    stop_file_monitoring,
    get_monitoring_status,
    get_monitoring_logs,
    restart_file_monitoring,
    get_monitoring_health_report
)

console = Console()

# 全局监控实例 (为了向后兼容)
_background_watcher: Optional[BackgroundFileWatcher] = None


def start_monitoring() -> None:
    """启动项目文件监控
    
    根据US-003验收标准实现：
    - 文件系统监控能检测.md文件变化
    - 变化后1分钟内更新内部状态
    - 支持多个项目文件夹同时监控
    - 提供变化通知功能
    """
    
    success, message, data = start_file_monitoring(enable_notifications=True)
    
    if not success:
        console.print(Panel(
            f"[red]❌ {message}",
            title="启动失败",
            border_style="red"
        ))
        return
        
    if data and data.get('already_running'):
        console.print(Panel(
            f"[yellow]文件监控已在运行中。\n\n"
            f"监控文件夹 ({len(data['monitored_folders'])} 个):\n" +
            "\n".join([f"• {folder}" for folder in data['monitored_folders']]) + "\n\n"
            "使用以下命令管理监控：\n"
            "• [cyan]pm monitor status[/cyan] - 查看监控状态\n"
            "• [cyan]pm monitor stop[/cyan] - 停止监控",
            title="⚠️ 监控已运行",
            border_style="yellow"
        ))
        return
        
    if data:
        folders = data.get('monitored_folders', [])
        invalid_folders = data.get('invalid_folders', [])
        
        console.print(Panel(
            f"[bold blue]🔍 启动项目文件监控\n\n"
            f"监控文件夹 ({len(folders)} 个):\n" +
            "\n".join([f"• {folder}" for folder in folders]) +
            (f"\n\n[yellow]⚠️ 无效文件夹 ({len(invalid_folders)} 个):\n" +
             "\n".join([f"• {folder}" for folder in invalid_folders]) if invalid_folders else ""),
            title="文件监控",
            border_style="blue"
        ))
        
        console.print(Panel(
            "[green]✅ 文件监控已启动！\n\n"
            "[white]监控功能：\n" +
            "\n".join([f"• {feature}" for feature in data.get('monitoring_features', [])]) + "\n\n"
            "[dim]监控将在后台持续运行...",
            title="🎉 监控启动成功",
            border_style="green"
        ))
        
        # 显示操作提示
        console.print(Panel(
            "[bold blue]💡 监控管理命令：\n\n"
            "• [cyan]pm monitor status[/cyan] - 查看监控状态\n"
            "• [cyan]pm monitor logs[/cyan] - 查看监控日志\n"
            "• [cyan]pm monitor stop[/cyan] - 停止监控\n"
            "• [cyan]Ctrl+C[/cyan] - 优雅停止监控",
            title="操作提示",
            border_style="blue"
        ))
        
        # 设置信号处理器，优雅退出
        def signal_handler(signum, frame):
            console.print("\n[yellow]接收到中断信号，正在停止监控...")
            stop_success, stop_message, _ = stop_file_monitoring()
            if stop_success:
                console.print(f"[green]✅ {stop_message}")
            else:
                console.print(f"[red]❌ {stop_message}")
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # 持续运行，显示状态
        try:
            while True:
                time.sleep(60)  # 每分钟检查一次状态
                status_success, _, status_data = get_monitoring_status()
                if status_success and status_data:
                    if status_data['monitoring_status'] != 'running':
                        console.print("[red]⚠️ 监控线程意外停止")
                        break
        except KeyboardInterrupt:
            console.print("\n[yellow]收到中断信号，正在停止监控...")
            stop_success, stop_message, _ = stop_file_monitoring()
            if stop_success:
                console.print(f"[green]✅ {stop_message}")
            else:
                console.print(f"[red]❌ {stop_message}")


def stop_monitoring() -> None:
    """停止项目文件监控"""
    
    console.print("[blue]正在停止文件监控...")
    
    success, message, data = stop_file_monitoring()
    
    if success:
        if data and data.get('monitoring_was_running'):
            stats = data
            console.print(Panel(
                f"[green]✅ 文件监控已停止\n\n"
                f"[white]运行统计：\n"
                f"• 处理变化总数: {stats.get('total_changes_processed', 0)}\n"
                f"• 成功更新: [green]{stats.get('successful_updates', 0)}[/green]\n"
                f"• 失败更新: [red]{stats.get('failed_updates', 0)}[/red]\n"
                f"• 监控文件夹: {len(stats.get('monitored_folders', []))}\n",
                title="🛑 监控停止",
                border_style="green"
            ))
        else:
            console.print(Panel(
                "[yellow]文件监控未在运行。",
                title="⚠️ 未运行",
                border_style="yellow"
            ))
    else:
        console.print(Panel(
            f"[red]❌ {message}",
            title="停止失败",
            border_style="red"
        ))


def show_monitoring_status() -> None:
    """显示监控状态"""
    
    success, message, data = get_monitoring_status()
    
    if not success:
        console.print(Panel(
            f"[red]❌ {message}",
            title="状态获取失败",
            border_style="red"
        ))
        return
        
    if not data:
        console.print(Panel(
            "[yellow]无法获取监控状态信息",
            title="⚠️ 状态不可用",
            border_style="yellow"
        ))
        return
        
    status = data['monitoring_status']
    
    if status == 'not_started':
        console.print(Panel(
            "[yellow]文件监控未启动。\n\n"
            "使用 [cyan]pm monitor start[/cyan] 启动监控",
            title="📊 监控状态",
            border_style="yellow"
        ))
        return
    
    # 基本状态信息
    status_table = Table(show_header=False, box=None, padding=(0, 2))
    status_table.add_column("项目", style="cyan", min_width=15)
    status_table.add_column("值", style="white")
    
    # 运行状态
    if status == "running":
        running_status = "[green]✅ 运行中[/green]"
        border_style = "green"
        title_emoji = "🟢"
    else:
        running_status = "[red]❌ 已停止[/red]"
        border_style = "red"
        title_emoji = "🔴"
    
    status_table.add_row("监控状态", running_status)
    status_table.add_row("监控文件夹", str(data["monitored_folders_count"]))
    
    stats = data["statistics"]
    status_table.add_row("总变化次数", str(stats["total_changes"]))
    status_table.add_row("成功更新", f"[green]{stats['successful_updates']}[/green]")
    status_table.add_row("失败更新", f"[red]{stats['failed_updates']}[/red]" if stats['failed_updates'] > 0 else "0")
    
    if stats["last_change_time"]:
        status_table.add_row("最后变化", stats["last_change_time"][:19].replace('T', ' '))
        
    # 健康评分
    health_score = data.get("health_score", 0)
    if health_score >= 0.8:
        health_display = f"[green]{health_score:.2f} (优秀)[/green]"
    elif health_score >= 0.6:
        health_display = f"[yellow]{health_score:.2f} (良好)[/yellow]"
    else:
        health_display = f"[red]{health_score:.2f} (需关注)[/red]"
    status_table.add_row("健康评分", health_display)
    
    console.print(Panel(
        status_table,
        title=f"{title_emoji} 监控状态",
        border_style=border_style
    ))
    
    # 监控文件夹列表
    if data["monitored_folders"]:
        folders_table = Table(show_header=True, header_style="bold cyan")
        folders_table.add_column("监控文件夹", style="white")
        folders_table.add_column("状态", style="green")
        
        for folder in data["monitored_folders"]:
            folders_table.add_row(folder, "✅ 活跃")
        
        console.print(Panel(
            folders_table,
            title="📁 监控文件夹",
            border_style="blue"
        ))
    
    # 最近通知
    recent_notifications = data.get("recent_notifications", [])
    if recent_notifications:
        notifications_text = []
        for notif in recent_notifications[-10:]:  # 最近10条
            timestamp = notif["timestamp"][:8]  # 只显示时间部分
            status_icon = "✅" if notif["status"] == "success" else "❌"
            message = notif["message"]
            if len(message) > 50:
                message = message[:47] + "..."
            notifications_text.append(f"[dim][{timestamp}][/dim] {status_icon} {message}")
            
        console.print(Panel(
            "\n".join(notifications_text),
            title="📋 最近变化 (最近10条)",
            border_style="cyan"
        ))
    
    # 推荐操作
    recommendations = data.get("recommendations", [])
    if recommendations:
        console.print(Panel(
            "\n".join([f"• {rec}" for rec in recommendations[:5]]),
            title="💡 系统建议",
            border_style="blue"
        ))
    
    # 操作提示
    if status == "running":
        console.print(Panel(
            "[bold blue]💡 监控管理：\n\n"
            "• [cyan]pm monitor logs[/cyan] - 查看详细日志\n"
            "• [cyan]pm monitor stop[/cyan] - 停止监控\n"
            "• [cyan]pm projects overview[/cyan] - 查看项目状态\n"
            "• [cyan]pm monitor health[/cyan] - 查看健康报告",
            title="操作选项",
            border_style="blue"
        ))
    else:
        console.print(Panel(
            "[bold yellow]💡 监控已停止：\n\n"
            "• [cyan]pm monitor start[/cyan] - 启动监控\n"
            "• [cyan]pm update project[/cyan] - 手动更新项目状态",
            title="操作选项",
            border_style="yellow"
        ))


def show_monitoring_logs(limit: int = 50) -> None:
    """显示监控日志"""
    
    success, message, data = get_monitoring_logs(limit)
    
    if not success:
        console.print(Panel(
            f"[red]❌ {message}",
            title="日志获取失败",
            border_style="red"
        ))
        return
        
    if not data or not data.get('logs_available'):
        console.print(Panel(
            data.get('message', '暂无监控日志'),
            title="📝 监控日志",
            border_style="cyan"
        ))
        return
        
    logs = data['logs']
    
    if not logs:
        console.print(Panel(
            "[dim]暂无监控日志。",
            title="📝 监控日志",
            border_style="cyan"
        ))
        return
    
    console.print(Panel(
        f"[bold blue]📝 监控日志 (最近 {len(logs)} 条)",
        title="监控日志",
        border_style="blue"
    ))
    
    # 显示详细日志
    logs_table = Table(show_header=True, header_style="bold cyan")
    logs_table.add_column("时间", style="dim", min_width=10)
    logs_table.add_column("项目", style="white", min_width=20)
    logs_table.add_column("状态", justify="center", min_width=8)
    logs_table.add_column("消息", style="white", min_width=30)
    
    for log in logs:  # 已经是最新在前的顺序
        timestamp = log["timestamp"][11:19]  # 提取时间部分 HH:MM:SS
        project_name = log["project_name"]
        success = log["success"]
        message = log["message"]
        
        # 限制消息长度
        if len(message) > 50:
            message = message[:47] + "..."
        
        if success:
            status_text = "[green]✅ 成功[/green]"
        else:
            status_text = "[red]❌ 失败[/red]"
        
        logs_table.add_row(timestamp, project_name, status_text, message)
    
    console.print(logs_table)


def _format_notifications(notifications: list) -> str:
    """格式化通知列表"""
    
    if not notifications:
        return "[dim]暂无通知[/dim]"
    
    formatted_lines = []
    for notification in reversed(notifications):  # 最新的在前
        timestamp = notification["timestamp"].strftime("%H:%M:%S")
        status = notification["status"]
        message = notification["message"]
        
        if status == "success":
            line = f"[green][{timestamp}] ✅ {message}[/green]"
        else:
            line = f"[red][{timestamp}] ❌ {message}[/red]"
        
        formatted_lines.append(line)
    
    return "\n".join(formatted_lines)


def restart_monitoring() -> None:
    """重启文件监控"""
    
    console.print("[blue]正在重启文件监控...")
    
    success, message, data = restart_file_monitoring()
    
    if success:
        if data and data.get('restart_successful'):
            console.print(Panel(
                f"[green]✅ 文件监控重启成功！\n\n"
                f"[white]重启信息：\n"
                f"• 重启时间: {data.get('restart_timestamp', '')[:19].replace('T', ' ')}\n"
                f"• 前次运行状态: {'正常' if data.get('previous_status', {}).get('monitoring_was_running') else '未运行'}\n"
                f"• 新监控状态: {'运行中' if data.get('new_status', {}).get('monitoring_started') else '启动失败'}",
                title="🔄 监控重启",
                border_style="green"
            ))
        else:
            console.print(Panel(
                f"[red]❌ 重启失败: {data.get('start_error', '未知错误') if data else '未知错误'}",
                title="重启失败",
                border_style="red"
            ))
    else:
        console.print(Panel(
            f"[red]❌ {message}",
            title="重启失败",
            border_style="red"
        ))


def show_monitoring_health() -> None:
    """显示监控健康报告"""
    
    success, message, data = get_monitoring_health_report()
    
    if not success:
        console.print(Panel(
            f"[red]❌ {message}",
            title="健康报告获取失败",
            border_style="red"
        ))
        return
        
    if not data or not data.get('monitoring_running'):
        console.print(Panel(
            "[yellow]文件监控未运行，无法生成健康报告。\n\n"
            "使用 [cyan]pm monitor start[/cyan] 启动监控",
            title="📊 监控健康报告",
            border_style="yellow"
        ))
        return
        
    health_status = data['health_status']
    health_score = data['health_score']
    
    # 状态颜色映射
    status_colors = {
        'excellent': ('green', '🟢'),
        'good': ('blue', '🔵'),
        'warning': ('yellow', '🟡'),
        'critical': ('red', '🔴')
    }
    
    color, emoji = status_colors.get(health_status, ('white', '⚪'))
    
    # 健康概览
    health_table = Table(show_header=False, box=None, padding=(0, 2))
    health_table.add_column("指标", style="cyan", min_width=18)
    health_table.add_column("值", style="white")
    
    health_table.add_row("健康状态", f"[{color}]{emoji} {health_status.upper()}[/{color}]")
    health_table.add_row("健康评分", f"[{color}]{health_score:.2f}/1.00[/{color}]")
    
    # 性能指标
    metrics = data['performance_metrics']
    health_table.add_row("处理变化总数", str(metrics['total_changes_processed']))
    health_table.add_row("成功率", f"[green]{metrics['successful_update_rate']:.1f}%[/green]")
    health_table.add_row("失败率", f"[red]{metrics['failed_update_rate']:.1f}%[/red]")
    health_table.add_row("监控文件夹", str(metrics['monitored_folders_count']))
    
    console.print(Panel(
        health_table,
        title=f"{emoji} 监控健康报告",
        border_style=color
    ))
    
    # 系统状态
    system_status = data['system_status']
    status_table = Table(show_header=True, header_style="bold cyan")
    status_table.add_column("组件", style="white")
    status_table.add_column("状态", justify="center")
    
    status_table.add_row(
        "后台监控线程", 
        "[green]✅ 活跃[/green]" if system_status['background_thread_alive'] else "[red]❌ 停止[/red]"
    )
    status_table.add_row(
        "文件监控", 
        "[green]✅ 运行中[/green]" if system_status['is_watching'] else "[red]❌ 未监控[/red]"
    )
    
    if system_status['last_activity']:
        last_activity = system_status['last_activity'][:19].replace('T', ' ')
        status_table.add_row("最后活动", last_activity)
    
    console.print(Panel(
        status_table,
        title="🔧 系统状态",
        border_style="blue"
    ))
    
    # 改进建议
    suggestions = data.get('improvement_suggestions', [])
    if suggestions:
        console.print(Panel(
            "\n".join([f"• {suggestion}" for suggestion in suggestions[:5]]),
            title="💡 改进建议",
            border_style="blue"
        ))
    
    # 监控建议
    recommendations = data.get('monitoring_recommendations', [])
    if recommendations:
        console.print(Panel(
            "\n".join([f"• {rec}" for rec in recommendations[:3]]),
            title="🎯 监控建议",
            border_style="cyan"
        ))