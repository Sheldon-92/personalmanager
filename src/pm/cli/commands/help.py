"""Help system for PersonalManager commands."""

from typing import Optional, Dict, List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from pm.tools.help_tools import (
    get_help_overview,
    get_command_help,
    search_commands,
    get_command_suggestions,
    get_available_commands,
    validate_command_exists
)

console = Console()


def help_system(command: Optional[str] = None) -> None:
    """显示帮助系统
    
    根据US-017验收标准实现：
    - 通过 `/pm help` 显示所有可用命令
    - 通过 `/pm help <command>` 显示特定命令详情
    - 提供命令使用示例
    - 支持模糊搜索命令
    """
    
    if command is None:
        _show_all_commands()
    else:
        _show_command_help(command)


def _show_all_commands() -> None:
    """显示所有可用命令概览"""
    
    success, message, data = get_help_overview()
    
    if not success:
        console.print(Panel(
            f"[red]❌ {message}",
            title="获取帮助信息失败",
            border_style="red"
        ))
        return
        
    if not data:
        console.print(Panel(
            "[yellow]无法获取帮助信息",
            title="⚠️ 信息不可用",
            border_style="yellow"
        ))
        return
        
    console.print(Panel(
        f"[bold blue]{data['system_title']}\n\n"
        f"[green]{data['system_description']}",
        title="📚 帮助系统",
        border_style="blue"
    ))
    
    # 按分类显示命令
    for category, commands in data['categories'].items():
        if commands:  # 只显示有命令的分类
            console.print(f"\n[bold]{category}")
            
            table = Table(show_header=False, box=None, padding=(0, 2))
            table.add_column("命令", style="cyan", min_width=15)
            table.add_column("描述", style="white")
            
            for cmd in commands:
                table.add_row(f"pm {cmd['name']}", cmd['description'])
            
            console.print(table)
    
    # 底部提示
    tips_text = "\n".join([f"• {tip}" for tip in data['usage_tips']])
    console.print(Panel(
        f"[yellow]💡 使用技巧：\n\n{tips_text}",
        title="使用提示",
        border_style="yellow"
    ))


def _show_command_help(command: str) -> None:
    """显示特定命令的详细帮助"""
    
    success, message, data = get_command_help(command)
    
    if not success:
        console.print(Panel(
            f"[red]❌ {message}",
            title="获取命令帮助失败",
            border_style="red"
        ))
        return
        
    if not data:
        console.print(Panel(
            "[yellow]无法获取命令帮助信息",
            title="⚠️ 信息不可用",
            border_style="yellow"
        ))
        return
        
    # 处理未找到命令的情况
    if not data['found']:
        if 'fuzzy_matches' in data:
            console.print(f"[yellow]找到多个匹配的命令: {', '.join(data['fuzzy_matches'])}")
            console.print("请指定具体的命令名称")
        else:
            console.print(f"[red]未找到命令: {data['command']}")
            console.print("使用 [cyan]pm help[/cyan] 查看所有可用命令")
        return
    
    help_info = data['help_info']
    
    # 标题
    console.print(Panel(
        f"[bold cyan]pm {data['command']}[/bold cyan]\n\n{help_info['description']}",
        title="📖 命令帮助",
        border_style="cyan"
    ))
    
    # 用法
    console.print(f"\n[bold]用法:")
    console.print(f"  [cyan]{help_info['usage']}[/cyan]")
    
    # 选项
    if help_info.get('options'):
        console.print(f"\n[bold]选项:")
        options_table = Table(show_header=False, box=None, padding=(0, 2))
        options_table.add_column("选项", style="green", min_width=15)
        options_table.add_column("描述", style="white")
        
        for option, desc in help_info['options'].items():
            options_table.add_row(option, desc)
        
        console.print(options_table)
    
    # 子命令
    if help_info.get('subcommands'):
        console.print(f"\n[bold]子命令:")
        sub_table = Table(show_header=False, box=None, padding=(0, 2))
        sub_table.add_column("子命令", style="magenta", min_width=15)
        sub_table.add_column("描述", style="white")
        
        for subcmd, desc in help_info['subcommands'].items():
            sub_table.add_row(subcmd, desc)
        
        console.print(sub_table)
    
    # 示例
    if help_info.get('examples'):
        console.print(f"\n[bold]示例:")
        for example in help_info['examples']:
            console.print(f"  [dim]$[/dim] [green]{example}[/green]")
    
    # 相关命令推荐
    related_commands = data.get('related_commands', [])
    if related_commands:
        console.print(f"\n[bold]相关命令:")
        for related in related_commands:
            console.print(f"  [cyan]pm {related['name']}[/cyan] - {related['description']}")


def search_help_commands(query: str) -> List[str]:
    """搜索命令（供其他模块使用）"""
    success, message, data = search_commands(query)
    if success and data:
        return [match['command'] for match in data['matches']]
    return []


def get_help_command_suggestions(partial_command: str) -> List[str]:
    """根据部分命令名获取建议（用于命令补全）"""
    success, message, data = get_command_suggestions(partial_command)
    if success and data:
        return [suggestion['command'] for suggestion in data['suggestions']]
    return []