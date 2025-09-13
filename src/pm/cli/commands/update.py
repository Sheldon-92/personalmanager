"""Project status update commands."""

from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
import typer

from pm.core.config import PMConfig
from pm.agents.project_manager import ProjectManagerAgent
from pm.tools.update_tools import (
    update_single_project,
    update_all_projects,
    force_refresh_all_projects,
    get_project_update_status,
    validate_project_update_requirements,
    analyze_update_performance
)

console = Console()


def update_project_status(project_name: Optional[str] = None) -> None:
    """手动更新项目状态
    
    根据US-004验收标准实现：
    - 通过 `/pm update project status <项目名>` 更新状态
    - 支持更新单个项目或所有项目
    - 显示更新进度和结果
    - 处理更新失败的情况
    """
    
    # 显示更新信息
    if project_name:
        console.print(Panel(
            f"[bold blue]🔄 更新项目状态: {project_name}",
            title="项目更新",
            border_style="blue"
        ))
        
        # 更新单个项目
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
        ) as progress:
            task = progress.add_task(f"正在更新 {project_name}...", total=None)
            
            success, message, data = update_single_project(project_name)
            
            progress.update(task, description="更新完成" if success else "更新失败")
            
            if success and data:
                _show_single_project_result(data)
            else:
                console.print(Panel(
                    f"[red]❌ {message}",
                    title="更新失败",
                    border_style="red"
                ))
                
                if data and data.get('troubleshooting_suggestions'):
                    console.print(Panel(
                        "\n".join([f"• {suggestion}" for suggestion in data['troubleshooting_suggestions']]),
                        title="🔧 故障排除建议",
                        border_style="yellow"
                    ))
    else:
        console.print(Panel(
            "[bold blue]🔄 更新所有项目状态",
            title="批量更新",
            border_style="blue"
        ))
        
        # 更新所有项目
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
        ) as progress:
            task = progress.add_task("正在批量更新项目...", total=None)
            
            success, message, data = update_all_projects(force_rescan=True)
            
            progress.update(task, description="批量更新完成" if success else "批量更新失败")
            
            if success and data:
                _show_batch_project_result(data)
            else:
                console.print(Panel(
                    f"[red]❌ {message}",
                    title="批量更新失败",
                    border_style="red"
                ))
                
                if data and data.get('troubleshooting'):
                    console.print(Panel(
                        "\n".join([f"• {item}" for item in data['troubleshooting']]),
                        title="🔧 故障排除",
                        border_style="yellow"
                    ))


def _show_single_project_result(data: dict) -> None:
    """显示单个项目更新结果"""
    
    project_name = data['project_name']
    
    if data['update_successful']:
        console.print(Panel(
            f"[green]✅ 项目 '{project_name}' 状态更新成功！\n\n"
            f"[dim]更新时间: {data['update_time'][:19].replace('T', ' ')}\n"
            f"文件更新数: {data['files_updated']}",
            title="🎉 更新成功",
            border_style="green"
        ))
        
        # 显示操作建议
        if data.get('recommendations'):
            console.print(Panel(
                "\n".join([f"• {rec}" for rec in data['recommendations']]),
                title="💡 下一步操作",
                border_style="blue"
            ))
        
    else:
        # 更新失败
        error_text = "\n".join(data['errors']) if data['errors'] else "未知错误"
        
        console.print(Panel(
            f"[red]❌ 项目 '{project_name}' 更新失败\n\n"
            f"错误详情:\n{error_text}",
            title="更新失败",
            border_style="red"
        ))
        
        # 故障排除建议
        if data.get('troubleshooting_suggestions'):
            console.print(Panel(
                "\n".join([f"{i+1}. {suggestion}" for i, suggestion in enumerate(data['troubleshooting_suggestions'])]),
                title="🔧 故障排除建议",
                border_style="yellow"
            ))
            
        # 推荐命令
        if data.get('recommended_commands'):
            console.print(Panel(
                "\n".join([f"• [cyan]{cmd}[/cyan]" for cmd in data['recommended_commands']]),
                title="🎯 推荐命令",
                border_style="cyan"
            ))


def _show_update_result(result: dict, project_name: str) -> None:
    """显示单个项目更新结果 (向后兼容)"""
    # 转换为新格式
    data = {
        'project_name': project_name,
        'update_successful': result["updated"] > 0,
        'update_time': __import__('datetime').datetime.now().isoformat(),
        'files_updated': result["updated"],
        'errors': result["errors"]
    }
    _show_single_project_result(data)


def _show_batch_project_result(data: dict) -> None:
    """显示批量项目更新结果"""
    
    total = data['total_projects']
    updated = data['projects_updated']
    failed = data['projects_failed']
    success_rate = data['success_rate']
    overall_status = data['overall_status']
    
    # 结果总览
    result_table = Table(show_header=False, box=None, padding=(0, 2))
    result_table.add_column("项目", style="cyan", min_width=12)
    result_table.add_column("值", style="white")
    
    result_table.add_row("📊 总项目数", str(total))
    result_table.add_row("✅ 更新成功", f"[green]{updated}[/green]")
    result_table.add_row("❌ 更新失败", f"[red]{failed}[/red]" if failed > 0 else "0")
    result_table.add_row("📈 成功率", f"[green]{success_rate:.1f}%[/green]")
    result_table.add_row("🕒 更新时间", data['update_time'][:19].replace('T', ' '))
    
    # 状态样式映射
    status_styles = {
        'excellent': ('green', '🎉'),
        'good': ('yellow', '⚠️'),
        'poor': ('red', '❌')
    }
    
    border_style, title_emoji = status_styles.get(overall_status, ('white', '📊'))
    title_map = {
        'excellent': '批量更新成功',
        'good': '批量更新部分成功', 
        'poor': '批量更新失败'
    }
    title = title_map.get(overall_status, '批量更新完成')
    
    console.print(Panel(
        result_table,
        title=f"{title_emoji} {title}",
        border_style=border_style
    ))
    
    # 显示错误详情（如果有）
    errors = data.get('errors', [])
    if errors:
        error_count = len(errors)
        if error_count <= 5:
            # 显示所有错误
            error_text = "\n".join([f"• {error}" for error in errors])
        else:
            # 只显示前5个错误
            error_text = "\n".join([f"• {error}" for error in errors[:5]])
            error_text += f"\n\n... 还有 {error_count - 5} 个错误"
        
        console.print(Panel(
            f"[red]失败项目详情:\n\n{error_text}",
            title="❌ 错误详情",
            border_style="red"
        ))
    
    # 显示建议
    recommendations = data.get('recommendations', [])
    if recommendations:
        console.print(Panel(
            "\n".join([f"• {rec}" for rec in recommendations]),
            title="💡 操作建议" if updated > 0 else "🔧 故障排除建议",
            border_style="green" if updated > 0 else "yellow"
        ))


def _show_batch_update_result(updated: int, failed: int, errors: list) -> None:
    """显示批量更新结果 (向后兼容)"""
    # 转换为新格式
    total = updated + failed
    success_rate = (updated / total * 100) if total > 0 else 0
    
    if success_rate >= 90:
        overall_status = "excellent"
    elif success_rate >= 70:
        overall_status = "good"
    else:
        overall_status = "poor"
        
    data = {
        'total_projects': total,
        'projects_updated': updated,
        'projects_failed': failed,
        'success_rate': success_rate,
        'overall_status': overall_status,
        'errors': errors,
        'update_time': __import__('datetime').datetime.now().isoformat()
    }
    _show_batch_project_result(data)


def force_refresh_all() -> None:
    """强制刷新所有项目状态（清除缓存）"""
    
    console.print(Panel(
        "[bold yellow]🔄 强制刷新所有项目状态\n\n"
        "[dim]这将清除缓存并重新扫描所有项目",
        title="强制刷新",
        border_style="yellow"
    ))
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
    ) as progress:
        task = progress.add_task("正在强制刷新...", total=None)
        
        success, message, data = force_refresh_all_projects()
        
        progress.update(task, description="刷新完成" if success else "刷新失败")
        
        if success and data:
            console.print(Panel(
                f"[green]✅ 强制刷新完成！\n\n"
                f"[white]刷新信息：\n"
                f"• 清除缓存: {data['original_cache_size']} 项\n"
                f"• 重新发现项目: {data['projects_rediscovered']} 个\n"
                f"• 刷新时间: {data['refresh_time'][:19].replace('T', ' ')}",
                title="🎉 刷新成功",
                border_style="green"
            ))
            
            # 显示推荐操作
            if data.get('recommendations'):
                console.print(Panel(
                    "\n".join([f"• {rec}" for rec in data['recommendations']]),
                    title="💡 推荐操作",
                    border_style="blue"
                ))
        else:
            console.print(Panel(
                f"[red]❌ {message}",
                title="刷新失败",
                border_style="red"
            ))


def show_update_status() -> None:
    """显示项目更新状态信息"""
    
    success, message, data = get_project_update_status()
    
    if not success:
        console.print(Panel(
            f"[red]❌ {message}",
            title="状态获取失败",
            border_style="red"
        ))
        return
        
    if not data:
        console.print(Panel(
            "[yellow]无法获取项目更新状态信息",
            title="⚠️ 状态不可用",
            border_style="yellow"
        ))
        return
        
    # 状态概览表
    status_table = Table(show_header=False, box=None, padding=(0, 2))
    status_table.add_column("项目", style="cyan", min_width=18)
    status_table.add_column("值", style="white")
    
    status_table.add_row("📊 总项目数", str(data['total_projects']))
    status_table.add_row("📁 有状态文件", f"[green]{data['projects_with_status_file']}[/green]")
    status_table.add_row("❓ 无状态文件", f"[red]{data['projects_without_status_file']}[/red]" if data['projects_without_status_file'] > 0 else "0")
    status_table.add_row("💾 缓存项目数", str(data['cached_projects']))
    status_table.add_row("📈 缓存命中率", f"{data['cache_hit_rate']:.1f}%")
    
    if data['last_scan_time']:
        status_table.add_row("🕒 最后扫描", data['last_scan_time'][:19].replace('T', ' '))
        
    console.print(Panel(
        status_table,
        title="📊 项目更新状态概览",
        border_style="blue"
    ))
    
    # 项目文件夹信息
    if data['project_folders']:
        folders_table = Table(show_header=True, header_style="bold cyan")
        folders_table.add_column("项目文件夹", style="white")
        folders_table.add_column("状态", justify="center")
        
        for folder in data['project_folders']:
            folders_table.add_row(folder, "[green]✅ 配置[/green]")
        
        console.print(Panel(
            folders_table,
            title="📁 配置的项目文件夹",
            border_style="green"
        ))
    
    # 推荐操作
    if data.get('recommendations'):
        console.print(Panel(
            "\n".join([f"• {rec}" for rec in data['recommendations']]),
            title="💡 推荐操作",
            border_style="cyan"
        ))


def validate_update_environment() -> None:
    """验证项目更新环境"""
    
    console.print(Panel(
        "[bold blue]🔍 验证项目更新环境\n\n"
        "[dim]检查更新前置条件...",
        title="环境验证",
        border_style="blue"
    ))
    
    success, message, data = validate_project_update_requirements()
    
    if not data:
        console.print(Panel(
            f"[red]❌ {message}",
            title="验证失败",
            border_style="red"
        ))
        return
        
    # 验证结果表
    validation_table = Table(show_header=False, box=None, padding=(0, 2))
    validation_table.add_column("检查项", style="cyan", min_width=20)
    validation_table.add_column("状态", justify="center")
    
    validation_table.add_row(
        "系统初始化", 
        "[green]✅ 通过[/green]" if data['system_initialized'] else "[red]❌ 失败[/red]"
    )
    validation_table.add_row(
        "项目文件夹配置", 
        "[green]✅ 通过[/green]" if data['project_folders_configured'] else "[red]❌ 失败[/red]"
    )
    validation_table.add_row(
        "文件夹访问权限", 
        "[green]✅ 通过[/green]" if data['project_folders_accessible'] else "[red]❌ 失败[/red]"
    )
    validation_table.add_row(
        "项目可发现性", 
        "[green]✅ 通过[/green]" if data['projects_discoverable'] else "[red]❌ 失败[/red]"
    )
    
    overall_status = data['overall_status']
    if overall_status == 'ready':
        border_style = "green"
        title_emoji = "✅"
    else:
        border_style = "red"
        title_emoji = "❌"
        
    console.print(Panel(
        validation_table,
        title=f"{title_emoji} 环境验证结果",
        border_style=border_style
    ))
    
    # 显示验证问题
    if data['validation_issues']:
        console.print(Panel(
            "\n".join([f"• {issue}" for issue in data['validation_issues']]),
            title="⚠️ 发现的问题",
            border_style="red"
        ))
    else:
        console.print(Panel(
            "[green]🎉 所有验证项目都已通过！\n\n"
            "项目更新环境已就绪，可以安全进行项目状态更新。",
            title="验证通过",
            border_style="green"
        ))