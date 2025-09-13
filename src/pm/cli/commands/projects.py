"""Project management CLI commands - Sprint 14 重构为AI可调用工具架构

CLI命令作为AI可调用工具函数的薄包装层
核心业务逻辑已迁移到 pm.tools.project_tools
"""

from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.text import Text
from rich.layout import Layout
from rich.columns import Columns
import typer

from pm.core.config import PMConfig
from pm.tools.project_tools import (
    get_projects_overview, get_project_status, search_projects as search_projects_tool,
    get_project_next_actions, get_project_risks_summary, get_project_statistics_summary
)
from pm.models.project import ProjectHealth, ProjectPriority

console = Console()


def show_projects_overview(sort_by: str = "health") -> None:
    """显示项目概览 - 重构为使用AI可调用工具函数
    
    根据US-001验收标准实现：
    - 能够通过 `/pm projects overview` 命令查看所有项目
    - 显示项目名称、进度百分比、健康状态
    - 按照优先级或健康状态排序
    - 支持不超过50个项目的显示
    """
    
    config = PMConfig()
    
    # 调用AI可调用工具函数
    success, message, overview_info = get_projects_overview(
        sort_by=sort_by,
        max_projects=50,
        config=config
    )
    
    if not success:
        console.print(Panel(
            f"[red]{message}",
            title="❌ 错误",
            border_style="red"
        ))
        return
    
    # 显示概览标题
    projects = overview_info["projects"]
    console.print(Panel(
        f"[bold green]📋 项目状态概览 ({overview_info['displayed_projects']} 个项目)\n\n"
        f"[dim]排序方式: {sort_by} | 扫描时间: {overview_info['scan_time'][:19] if overview_info['scan_time'] else '未知'}",
        title="项目管理",
        border_style="green"
    ))
    
    # 创建项目概览表格
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("项目", style="white", min_width=20)
    table.add_column("进度", justify="center", min_width=8)
    table.add_column("健康", justify="center", min_width=8)
    table.add_column("优先级", justify="center", min_width=8)
    table.add_column("风险", justify="center", min_width=6)
    table.add_column("行动", justify="center", min_width=6)
    table.add_column("最后更新", style="dim", min_width=12)
    
    for project in projects:
        # 项目名称（带路径）
        name_text = Text(project["name"])
        if project["is_at_risk"]:
            name_text.style = "bold red"
        elif project["health"] == "excellent":
            name_text.style = "bold green"
        
        # 进度条和百分比
        progress_percent = project["progress"]
        if progress_percent >= 80:
            progress_style = "green"
        elif progress_percent >= 50:
            progress_style = "yellow"
        else:
            progress_style = "red"
        
        progress_text = f"[{progress_style}]{progress_percent:.1f}%[/{progress_style}]"
        
        # 健康状态
        health_text = f"{project['health_emoji']} {project['health']}"
        
        # 优先级
        priority_text = f"{project['priority_emoji']} {project['priority']}"
        
        # 风险指示器
        risk_text = "🚨" if project["is_at_risk"] else "✅"
        
        # 下一步行动数量
        actions_count = project["next_actions_count"]
        actions_text = f"📋 {actions_count}" if actions_count > 0 else "➖"
        
        # 最后更新时间
        last_updated = project["last_updated"]
        if last_updated:
            from datetime import datetime
            update_dt = datetime.fromisoformat(last_updated)
            update_text = update_dt.strftime("%m-%d %H:%M")
        else:
            update_text = "[dim]未知[/dim]"
        
        table.add_row(
            name_text,
            progress_text,
            health_text,
            priority_text,
            risk_text,
            actions_text,
            update_text
        )
    
    console.print(table)
    
    # 显示统计信息
    stats = overview_info["statistics"]
    _show_project_statistics(stats)
    
    # 显示操作提示
    console.print(Panel(
        "[bold blue]💡 操作提示：\n\n"
        "• [cyan]pm project status <项目名>[/cyan] - 查看项目详情\n"
        "• [cyan]pm projects overview --sort priority[/cyan] - 按优先级排序\n"
        "• [cyan]pm update project status[/cyan] - 更新所有项目状态\n"
        "• [cyan]pm projects search <关键词>[/cyan] - 搜索项目",
        title="使用提示",
        border_style="blue"
    ))


def show_project_status(project_name: str) -> None:
    """显示项目详细状态 - 重构为使用AI可调用工具函数
    
    根据US-002验收标准实现：
    - 通过 `/pm project status <项目名>` 查看项目详情
    - 显示项目进度、健康状态、最后更新时间
    - 显示已完成工作和下一步行动
    - 显示项目风险和问题
    """
    
    config = PMConfig()
    
    # 调用AI可调用工具函数
    success, message, project_status = get_project_status(project_name, config)
    
    if not success:
        console.print(Panel(
            f"[red]{message}",
            title="❌ 错误",
            border_style="red"
        ))
        return
    
    # 项目基本信息
    basic_info = project_status["basic_info"]
    status_metrics = project_status["status_metrics"]
    
    console.print(Panel(
        f"[bold green]{status_metrics['health_emoji']} {basic_info['name']}[/bold green]\n\n"
        f"[dim]位置: {basic_info['path']}[/dim]",
        title="📋 项目详情",
        border_style="green"
    ))
    
    # 创建项目状态布局
    layout = Layout()
    layout.split_column(
        Layout(name="status", size=8),
        Layout(name="content")
    )
    
    # 状态信息表格
    status_table = Table(show_header=False, box=None, padding=(0, 2))
    status_table.add_column("项目", style="cyan", min_width=12)
    status_table.add_column("值", style="white")
    
    status_table.add_row("📊 进度", f"[green]{status_metrics['progress']:.1f}%[/green]")
    status_table.add_row("💚 健康状态", f"{status_metrics['health_emoji']} {status_metrics['health']}")
    status_table.add_row("🔥 优先级", f"{status_metrics['priority_emoji']} {status_metrics['priority']}")
    
    if basic_info.get('current_phase'):
        status_table.add_row("🎯 当前阶段", basic_info['current_phase'])
    
    if status_metrics.get('last_updated'):
        from datetime import datetime
        last_updated_dt = datetime.fromisoformat(status_metrics['last_updated'])
        status_table.add_row("⏰ 最后更新", last_updated_dt.strftime("%Y-%m-%d %H:%M:%S"))
    
    if basic_info.get('target_completion'):
        status_table.add_row("📅 目标完成", basic_info['target_completion'])
    
    if basic_info.get('team_members'):
        status_table.add_row("👥 团队成员", ", ".join(basic_info['team_members']))
    
    layout["status"].update(Panel(status_table, title="📊 状态信息", border_style="blue"))
    
    # 内容区域
    content_layout = Layout()
    content_layout.split_row(
        Layout(name="left"),
        Layout(name="right")
    )
    
    # 左侧：已完成工作和下一步行动
    left_content = []
    
    if project_status.get("description"):
        left_content.append(Panel(
            project_status["description"],
            title="📝 项目描述",
            border_style="cyan"
        ))
    
    if project_status.get("completed_work"):
        completed_text = "\n".join([f"✅ {work}" for work in project_status["completed_work"]])
        left_content.append(Panel(
            completed_text if completed_text else "[dim]暂无已完成工作[/dim]",
            title="✅ 已完成工作",
            border_style="green"
        ))
    
    if project_status.get("next_actions"):
        actions_text = "\n".join([f"📋 {action}" for action in project_status["next_actions"]])
        left_content.append(Panel(
            actions_text if actions_text else "[dim]暂无下一步行动[/dim]",
            title="📋 下一步行动",
            border_style="yellow"
        ))
    
    # 右侧：风险和其他信息
    right_content = []
    
    if project_status.get("risks"):
        risks_text = "\n".join([f"⚠️ {risk}" for risk in project_status["risks"]])
        right_content.append(Panel(
            risks_text if risks_text else "[dim]暂无风险[/dim]",
            title="⚠️ 风险和问题",
            border_style="red"
        ))
    
    if project_status.get("dependencies"):
        deps_text = "\n".join([f"🔗 {dep}" for dep in project_status["dependencies"]])
        right_content.append(Panel(
            deps_text,
            title="🔗 依赖项目",
            border_style="magenta"
        ))
    
    if project_status.get("tags"):
        tags_text = " ".join([f"#{tag}" for tag in project_status["tags"]])
        right_content.append(Panel(
            tags_text,
            title="🏷️ 标签",
            border_style="cyan"
        ))
    
    # 组装内容
    if left_content:
        content_layout["left"].update(Columns(left_content, equal=False, expand=True))
    
    if right_content:
        content_layout["right"].update(Columns(right_content, equal=False, expand=True))
    
    layout["content"].update(content_layout)
    
    console.print(layout)
    
    # 操作提示
    console.print(Panel(
        "[bold blue]💡 操作提示：\n\n"
        f"• [cyan]pm update project status {project_name}[/cyan] - 更新此项目状态\n"
        "• [cyan]pm projects overview[/cyan] - 返回项目概览\n"
        f"• [cyan]code {basic_info['path']}[/cyan] - 在编辑器中打开项目",
        title="操作选项",
        border_style="blue"
    ))


def search_projects(query: str) -> None:
    """搜索项目 - 重构为使用AI可调用工具函数"""
    
    config = PMConfig()
    
    # 搜索项目
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
    ) as progress:
        task = progress.add_task(f"正在搜索 '{query}'...", total=None)
        
        # 调用AI可调用工具函数 (修复参数顺序Bug)
        success, message, search_results = search_projects_tool(query, config=config)
        
        progress.update(task, description="搜索完成")
    
    # 在Progress上下文之外处理结果，避免输出干扰
    if not success:
        console.print(Panel(
            f"[red]{message}",
            title="❌ 错误",
            border_style="red"
        ))
        return
    
    if not search_results or not search_results.get("projects"):
        console.print(Panel(
            f"[yellow]未找到匹配 '{query}' 的项目。\n\n"
            "搜索范围包括：项目名称、描述、标签、路径",
            title="🔍 搜索结果",
            border_style="yellow"
        ))
        return
    
    projects = search_results["projects"]
    console.print(Panel(
        f"[bold green]🔍 搜索结果: '{query}' ({len(projects)} 个匹配)",
        title="搜索结果",
        border_style="green"
    ))
    
    # 显示搜索结果
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("项目", style="white", min_width=20)
    table.add_column("描述", style="dim", min_width=30)
    table.add_column("进度", justify="center", min_width=8)
    table.add_column("健康", justify="center", min_width=8)
    table.add_column("路径", style="dim", min_width=20)
    
    for project in projects:
        description = project.get("description") or "[dim]无描述[/dim]"
        if len(description) > 40:
            description = description[:37] + "..."
        
        table.add_row(
            project["name"],
            description,
            f"{project['progress']:.1f}%",
            f"{project['health_emoji']} {project['health']}",
            project["path_name"]
        )
    
    console.print(table)


def _show_project_statistics(stats: dict) -> None:
    """显示项目统计信息"""
    
    # 健康状态统计
    health_stats = []
    for health, count in stats["health_distribution"].items():
        if count > 0:
            emoji_map = {
                "excellent": "🟢",
                "good": "🟡",
                "warning": "🟠", 
                "critical": "🔴",
                "unknown": "⚪"
            }
            emoji = emoji_map.get(health, "⚪")
            health_stats.append(f"{emoji} {health}: {count}")
    
    # 优先级统计
    priority_stats = []
    for priority, count in stats["priority_distribution"].items():
        if count > 0:
            emoji_map = {
                "high": "🔥",
                "medium": "📋",
                "low": "📝"
            }
            emoji = emoji_map.get(priority, "📋")
            priority_stats.append(f"{emoji} {priority}: {count}")
    
    stats_text = f"""
[bold]📊 项目统计[/bold]

[cyan]总项目数:[/cyan] {stats['total_projects']}
[cyan]平均进度:[/cyan] {stats['average_progress']:.1f}%
[cyan]风险项目:[/cyan] {stats['projects_at_risk']}
[cyan]未更新项目:[/cyan] {stats['projects_with_no_updates']}

[bold]健康状态分布:[/bold]
{chr(10).join(health_stats)}

[bold]优先级分布:[/bold]
{chr(10).join(priority_stats)}
"""
    
    console.print(Panel(
        stats_text.strip(),
        title="📈 统计信息",
        border_style="cyan"
    ))