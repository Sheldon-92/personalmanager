"""Privacy protection and data management commands."""

import shutil
import json
from pathlib import Path
from typing import Dict, Any, List
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
import typer

from pm.core.config import PMConfig
from pm.tools.privacy_tools import (
    get_privacy_information,
    export_user_data,
    create_data_backup,
    cleanup_old_data as cleanup_old_data_tool,
    clear_all_data as clear_all_data_tool,
    verify_data_integrity as verify_data_integrity_tool,
    repair_data_issues,
    get_storage_statistics
)

console = Console()


def show_privacy_info() -> None:
    """显示数据隐私信息
    
    根据US-016验收标准实现：
    - 明确说明数据存储位置（本地）
    - 解释数据不会上传到云端
    - 提供数据导出功能
    - 提供数据清除功能
    """
    
    success, message, data = get_privacy_information()
    
    if not success:
        console.print(Panel(
            f"[red]❌ {message}",
            title="隐私信息获取失败",
            border_style="red"
        ))
        return
        
    if not data:
        console.print(Panel(
            "[yellow]无法获取隐私信息",
            title="⚠️ 信息不可用",
            border_style="yellow"
        ))
        return
        
    console.print(Panel(
        "[bold green]🔒 PersonalManager 隐私保护承诺\n\n"
        "[white]您的数据隐私是我们的首要关注。PersonalManager\n"
        "采用完全本地化的数据存储策略，确保您的个人信息\n"
        "始终在您的控制之下。",
        title="隐私保护",
        border_style="green"
    ))
    
    # 数据存储信息表
    storage_table = Table(title="数据存储详情")
    storage_table.add_column("项目", style="cyan", min_width=20)
    storage_table.add_column("详情", style="white")
    
    storage_table.add_row(
        "🏠 存储位置", 
        f"[green]本地存储[/green]\n{data['storage_location']}"
    )
    storage_table.add_row(
        "☁️ 云端同步", 
        "[red]已禁用[/red]\n数据不会上传到任何云端服务"
    )
    storage_table.add_row(
        "🔐 数据加密", 
        "[green]文件系统级别[/green]\n依赖操作系统的文件加密"
    )
    storage_table.add_row(
        "📊 数据大小", 
        f"[yellow]{data['estimated_storage_size']}[/yellow]\n当前占用空间"
    )
    storage_table.add_row(
        "🔄 备份状态", 
        "[green]本地备份[/green]\n定期创建本地备份文件" if data['backup_enabled'] else "[yellow]已禁用[/yellow]"
    )
    storage_table.add_row(
        "⏰ 数据保留", 
        f"[blue]{data['data_retention_days']} 天[/blue]\n超过期限的数据将被自动清理"
    )
    
    console.print(storage_table)
    
    # 隐私保护承诺
    commitments_text = "\n".join([f"✅ [green]{commitment}[/green]" for commitment in data['privacy_commitments']])
    console.print(Panel(
        f"[bold yellow]📋 我们的隐私承诺：\n\n{commitments_text}",
        title="隐私承诺",
        border_style="yellow"
    ))
    
    # 数据类别信息
    categories_text = " | ".join(data['data_categories'])
    console.print(Panel(
        f"[bold cyan]📂 数据类别：\n\n{categories_text}",
        title="数据分类",
        border_style="cyan"
    ))
    
    # 数据管理选项
    console.print(Panel(
        "[bold blue]🛠️ 数据管理选项：\n\n"
        "• [cyan]pm privacy export[/cyan] - 导出所有数据\n"
        "• [cyan]pm privacy backup[/cyan] - 创建数据备份\n"
        "• [cyan]pm privacy cleanup[/cyan] - 清理过期数据\n"
        "• [cyan]pm privacy clear[/cyan] - 完全清除所有数据\n"
        "• [cyan]pm privacy verify[/cyan] - 验证数据完整性\n"
        "• [cyan]pm privacy stats[/cyan] - 查看存储统计",
        title="管理工具",
        border_style="blue"
    ))


def export_data() -> None:
    """导出所有用户数据"""
    
    console.print(Panel(
        f"[bold blue]📤 数据导出\n\n"
        f"将导出所有PersonalManager数据到默认位置",
        title="数据导出",
        border_style="blue"
    ))
    
    if not Confirm.ask("开始导出数据？"):
        return
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
    ) as progress:
        task = progress.add_task("正在导出数据...", total=None)
        
        success, message, data = export_user_data()
        
        progress.update(task, description="导出完成！" if success else "导出失败")
        
        if success and data:
            console.print(Panel(
                f"[green]✅ 数据导出成功！\n\n"
                f"导出位置: [cyan]{data['export_path']}[/cyan]\n"
                f"导出大小: [yellow]{data['export_size_mb']} MB[/yellow]\n"
                f"导出项目: {', '.join(data['exported_items'])}\n"
                f"清单文件: {Path(data['manifest_file']).name}\n\n"
                f"[yellow]⚠️  {data['security_reminder']}",
                title="导出成功",
                border_style="green"
            ))
        else:
            console.print(Panel(
                f"[red]❌ {message}",
                title="导出错误",
                border_style="red"
            ))


def backup_data() -> None:
    """创建数据备份"""
    
    console.print("[blue]正在创建数据备份...")
    
    success, message, data = create_data_backup()
    
    if success and data:
        console.print(Panel(
            f"[green]✅ 备份创建成功！\n\n"
            f"备份文件: [cyan]{Path(data['backup_file']).name}[/cyan]\n"
            f"备份大小: [yellow]{data['backup_size_mb']} MB[/yellow]\n"
            f"备份内容: {', '.join(data['backed_up_items'])}\n"
            f"清理旧备份: {data['old_backups_cleaned']} 个\n"
            f"备份策略: {data['backup_retention_policy']}",
            title="备份成功",
            border_style="green"
        ))
    else:
        console.print(Panel(
            f"[red]❌ {message}",
            title="备份失败",
            border_style="red"
        ))


def cleanup_old_data() -> None:
    """清理过期数据"""
    
    # 获取配置以显示清理信息
    try:
        config = PMConfig()
        retention_days = config.data_retention_days if config.is_initialized() else 30
    except:
        retention_days = 30
    
    console.print(Panel(
        f"[bold yellow]🧹 数据清理\n\n"
        f"将清理超过 {retention_days} 天的过期数据\n"
        f"包括：日志文件、临时文件、过期备份",
        title="数据清理",
        border_style="yellow"
    ))
    
    if not Confirm.ask("开始清理过期数据？"):
        return
    
    success, message, data = cleanup_old_data_tool(retention_days)
    
    if success and data:
        console.print(Panel(
            f"[green]✅ 清理完成！\n\n"
            f"清理文件数: {data['cleaned_files_count']}\n"
            f"释放空间: {data['cleaned_size_mb']} MB\n"
            f"保留天数: {data['retention_days']} 天\n"
            f"清理时间: {data['cleanup_timestamp'][:19].replace('T', ' ')}",
            title="清理成功",
            border_style="green"
        ))
        
        # 显示清理详情
        if data['cleaned_files'] and len(data['cleaned_files']) <= 10:
            console.print(Panel(
                "\n".join(data['cleaned_files']),
                title="📁 清理的文件",
                border_style="cyan"
            ))
    else:
        console.print(Panel(
            f"[red]❌ {message}",
            title="清理失败",
            border_style="red"
        ))


def clear_all_data() -> None:
    """完全清除所有数据"""
    
    console.print(Panel(
        "[bold red]⚠️  危险操作：完全数据清除\n\n"
        "[white]此操作将永久删除所有PersonalManager数据，包括：\n"
        "• 所有配置设置\n"
        "• 项目和任务数据\n"
        "• 习惯记录\n"
        "• 日志文件\n"
        "• 备份文件\n\n"
        "[yellow]此操作无法撤销！请确保已导出重要数据。",
        title="⚠️ 警告",
        border_style="red"
    ))
    
    if not Confirm.ask("您确定要删除所有数据吗？", default=False):
        console.print("[yellow]操作已取消")
        return
    
    if not Confirm.ask("最后确认：真的要永久删除所有数据吗？", default=False):
        console.print("[yellow]操作已取消")
        return
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
    ) as progress:
        task = progress.add_task("正在清除数据...", total=None)
        
        success, message, data = clear_all_data_tool()
        
        progress.update(task, description="清除完成！" if success else "清除失败")
        
        if success and data:
            console.print(Panel(
                f"[green]✅ 所有数据已清除\n\n"
                f"清除项目: {', '.join(data['cleared_items'])}\n"
                f"释放空间: {data['total_size_cleared_mb']} MB\n\n"
                f"[yellow]{data['warning']}\n"
                f"[dim]{data['recovery_note']}",
                title="清除完成",
                border_style="green"
            ))
        else:
            console.print(Panel(
                f"[red]❌ {message}",
                title="清除错误",
                border_style="red"
            ))


def verify_data_integrity() -> None:
    """验证数据完整性"""
    
    # 使用标准化错误检查
    from pm.core.errors import check_system_initialized, check_data_directory_permissions
    
    error = check_system_initialized()
    if error:
        console.print(Panel(
            error.get_full_message(),
            title="❌ 系统错误",
            border_style="red"
        ))
        raise typer.Exit(1)
        
    error = check_data_directory_permissions()
    if error:
        console.print(Panel(
            error.get_full_message(),
            title="❌ 权限错误",
            border_style="red"
        ))
        raise typer.Exit(1)
    
    console.print("[blue]🔍 正在验证数据完整性...")
    
    success, message, data = verify_data_integrity_tool()
    
    if not success:
        console.print(Panel(
            f"[red]❌ {message}",
            title="验证失败",
            border_style="red"
        ))
        raise typer.Exit(1)
        
    if not data:
        console.print(Panel(
            "[yellow]无法获取验证结果",
            title="⚠️ 验证不可用",
            border_style="yellow"
        ))
        return
        
    # 显示验证结果
    if data['integrity_status'] == 'healthy':
        console.print(Panel(
            "[green]✅ 数据完整性验证通过\n\n"
            "所有数据文件和配置都正常",
            title="验证成功",
            border_style="green"
        ))
    else:
        console.print(Panel(
            f"[red]发现 {data['total_issues']} 个问题：\n\n" +
            "\n".join(f"• {issue}" for issue in data['issues'][:10]),
            title="⚠️ 数据完整性问题",
            border_style="red"
        ))
        
        # 显示统计信息
        stats = data['statistics']
        if any(stats.values()):
            console.print(Panel(
                f"问题统计：\n"
                f"• 缺失目录: {stats['missing_directories']} 个\n"
                f"• 无效项目文件夹: {stats['inaccessible_project_folders']} 个\n"
                f"• 损坏数据文件: {stats['corrupted_data_files']} 个",
                title="📊 问题分析",
                border_style="yellow"
            ))
        
        if data['repair_available'] and Confirm.ask("尝试自动修复这些问题？"):
            repair_success, repair_message, repair_data = repair_data_issues()
            
            if repair_success and repair_data:
                console.print(Panel(
                    f"[green]修复完成！\n\n"
                    f"修复项目: {repair_data['repaired_items_count']} 个\n"
                    f"失败项目: {repair_data['repair_failures_count']} 个\n\n"
                    f"建议: {repair_data['recommendation']}",
                    title="🔧 修复结果",
                    border_style="green"
                ))
            else:
                console.print(Panel(
                    f"[yellow]{repair_message}",
                    title="修复结果",
                    border_style="yellow"
                ))


def show_storage_stats() -> None:
    """显示存储使用统计"""
    
    console.print("[blue]📊 正在分析存储使用情况...")
    
    success, message, data = get_storage_statistics()
    
    if not success:
        console.print(Panel(
            f"[red]❌ {message}",
            title="统计失败",
            border_style="red"
        ))
        return
        
    if not data:
        console.print(Panel(
            "[yellow]无法获取存储统计信息",
            title="⚠️ 统计不可用",
            border_style="yellow"
        ))
        return
        
    # 存储概览
    stats_table = Table(show_header=False, box=None, padding=(0, 2))
    stats_table.add_column("项目", style="cyan", min_width=15)
    stats_table.add_column("值", style="white")
    
    stats_table.add_row("📊 总大小", f"{data['total_size_mb']} MB")
    stats_table.add_row("📁 总文件数", str(data['total_files']))
    
    console.print(Panel(
        stats_table,
        title="💾 存储概览",
        border_style="blue"
    ))
    
    # 分类大小
    if data['category_sizes']:
        category_table = Table(show_header=True, header_style="bold cyan")
        category_table.add_column("数据类别", style="white")
        category_table.add_column("大小 (MB)", justify="right", style="yellow")
        category_table.add_column("文件数", justify="right", style="green")
        
        for category, size_info in data['category_sizes'].items():
            file_count = data['file_counts'].get(category, 0)
            category_table.add_row(
                category.capitalize(),
                f"{size_info['mb']:.2f}",
                str(file_count)
            )
            
        console.print(Panel(
            category_table,
            title="📂 分类统计",
            border_style="green"
        ))
    
    # 最大文件
    if data['largest_files']:
        large_files_table = Table(show_header=True, header_style="bold cyan")
        large_files_table.add_column("文件", style="white", max_width=40)
        large_files_table.add_column("大小 (MB)", justify="right", style="yellow")
        
        for file_info in data['largest_files'][:5]:
            file_name = Path(file_info['path']).name
            size_mb = file_info['size'] / (1024 * 1024)
            large_files_table.add_row(file_name, f"{size_mb:.2f}")
            
        console.print(Panel(
            large_files_table,
            title="📋 最大文件 (前5个)",
            border_style="cyan"
        ))


def _cleanup_old_backups(backup_dir: Path, keep: int = 10) -> int:
    """清理旧备份文件，保留最近的几个"""
    
    backup_files = list(backup_dir.glob("pm_backup_*.tar.gz"))
    backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    cleaned_count = 0
    for old_backup in backup_files[keep:]:
        old_backup.unlink()
        cleaned_count += 1
    
    return cleaned_count


def _repair_data_issues(config: PMConfig, issues: List[str]) -> None:
    """尝试修复数据问题"""
    
    repaired = []
    
    # 修复数据目录结构
    required_dirs = ["projects", "tasks", "habits", "logs"]
    for dir_name in required_dirs:
        dir_path = config.data_dir / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            repaired.append(f"重建数据目录: {dir_name}")
    
    # 修复配置文件
    if not config.config_file.exists():
        try:
            config.save_to_file()
            repaired.append("重建配置文件")
        except Exception:
            pass
    
    if repaired:
        console.print(Panel(
            f"[green]修复了 {len(repaired)} 个问题：\n\n" +
            "\n".join(f"• {repair}" for repair in repaired),
            title="✅ 修复完成",
            border_style="green"
        ))
    else:
        console.print("[yellow]没有可以自动修复的问题")
