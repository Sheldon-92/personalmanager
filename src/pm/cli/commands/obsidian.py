"""Obsidian深度集成CLI命令 - Sprint 18核心功能"""

from typing import Optional
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree
from rich.progress import Progress, SpinnerColumn, TextColumn
import typer

from pm.core.config import PMConfig
from pm.tools.obsidian_tools import (
    connect_obsidian_vault,
    scan_obsidian_vault, 
    search_obsidian_notes,
    create_obsidian_note,
    sync_tasks_to_obsidian,
    generate_knowledge_graph,
    get_vault_statistics
)

console = Console()
obsidian_app = typer.Typer(help="Obsidian集成管理")


@obsidian_app.command("connect")
def connect_vault(vault_path: str = typer.Argument(..., help="Obsidian Vault路径")):
    """连接到Obsidian Vault"""
    
    config = PMConfig()
    
    with console.status("[bold blue]连接到Obsidian Vault...", spinner="dots"):
        success, message, data = connect_obsidian_vault(vault_path, config)
    
    if success:
        console.print(Panel(
            f"[green]✅ {message}[/green]\n\n"
            f"• Vault路径: [cyan]{data['vault_path']}[/cyan]\n"
            f"• 笔记数量: [yellow]{data['scan_results']['total_notes']}[/yellow]\n"
            f"• 附件数量: [blue]{data['scan_results']['total_attachments']}[/blue]",
            title="🔗 Vault连接成功",
            border_style="green"
        ))
    else:
        console.print(Panel(
            f"[red]❌ {message}[/red]",
            title="连接失败",
            border_style="red"
        ))


@obsidian_app.command("scan")
def scan_vault(
    vault_path: str = typer.Argument(..., help="Obsidian Vault路径"),
    force: bool = typer.Option(False, "--force", "-f", help="强制重新扫描")
):
    """扫描Obsidian Vault并建立索引"""
    
    config = PMConfig()
    
    with console.status("[bold blue]扫描Vault中...", spinner="dots"):
        success, message, data = scan_obsidian_vault(vault_path, force, config)
    
    if success:
        console.print(Panel(
            f"[green]✅ {message}[/green]\n\n"
            f"• 扫描的笔记: [yellow]{data['total_notes']}[/yellow]\n"
            f"• 发现的附件: [blue]{data['total_attachments']}[/blue]\n"
            f"• 最后扫描: [dim]{data['last_scan']}[/dim]",
            title="📊 扫描完成",
            border_style="green"
        ))
    else:
        console.print(Panel(
            f"[red]❌ {message}[/red]",
            title="扫描失败",
            border_style="red"
        ))


@obsidian_app.command("search")
def search_notes(
    vault_path: str = typer.Argument(..., help="Obsidian Vault路径"),
    query: str = typer.Argument(..., help="搜索查询"),
    content: bool = typer.Option(True, "--content/--no-content", help="搜索内容"),
    titles: bool = typer.Option(True, "--titles/--no-titles", help="搜索标题"),
    tags: bool = typer.Option(True, "--tags/--no-tags", help="搜索标签")
):
    """搜索Obsidian笔记"""
    
    config = PMConfig()
    
    with console.status(f"[bold blue]搜索 '{query}'...", spinner="dots"):
        success, message, data = search_obsidian_notes(
            vault_path, query, content, titles, tags, config
        )
    
    if success:
        console.print(Panel(
            f"[green]✅ {message}[/green]",
            title="🔍 搜索完成",
            border_style="green"
        ))
        
        if data['total_results'] > 0:
            # 显示搜索结果表格
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("标题", style="cyan", width=30)
            table.add_column("路径", style="dim", width=40)
            table.add_column("标签", style="yellow", width=20)
            table.add_column("字数", style="green", justify="right")
            
            for result in data['results']:
                tags_str = ', '.join(result['tags'][:3]) if result['tags'] else "无"
                table.add_row(
                    result['title'],
                    result['file_path'],
                    tags_str,
                    str(result['word_count'])
                )
            
            console.print(table)
            
            if data['total_results'] > len(data['results']):
                console.print(f"\n[dim]显示前 {len(data['results'])} 个结果，共找到 {data['total_results']} 个匹配项[/dim]")
        
    else:
        console.print(Panel(
            f"[red]❌ {message}[/red]",
            title="搜索失败",
            border_style="red"
        ))


@obsidian_app.command("create")
def create_note(
    vault_path: str = typer.Argument(..., help="Obsidian Vault路径"),
    title: str = typer.Argument(..., help="笔记标题"),
    content: str = typer.Option("", "--content", "-c", help="笔记内容"),
    folder: Optional[str] = typer.Option(None, "--folder", "-f", help="目标文件夹"),
    tags: Optional[str] = typer.Option(None, "--tags", "-t", help="标签（逗号分隔）")
):
    """在Obsidian中创建新笔记"""
    
    config = PMConfig()
    
    # 处理标签
    tag_list = None
    if tags:
        tag_list = [tag.strip() for tag in tags.split(',')]
    
    with console.status(f"[bold blue]创建笔记 '{title}'...", spinner="dots"):
        success, message, data = create_obsidian_note(
            vault_path, title, content, folder, tag_list, None, config
        )
    
    if success:
        console.print(Panel(
            f"[green]✅ {message}[/green]\n\n"
            f"• 文件路径: [cyan]{data['file_path']}[/cyan]\n"
            f"• 文件夹: [blue]{data['folder'] or '根目录'}[/blue]\n"
            f"• 标签: [yellow]{', '.join(data['tags']) if data['tags'] else '无'}[/yellow]\n"
            f"• 字数: [magenta]{data['word_count']}[/magenta]",
            title="📝 笔记创建成功",
            border_style="green"
        ))
    else:
        console.print(Panel(
            f"[red]❌ {message}[/red]",
            title="创建失败",
            border_style="red"
        ))


@obsidian_app.command("sync-tasks")
def sync_tasks(
    vault_path: str = typer.Argument(..., help="Obsidian Vault路径"),
    folder: str = typer.Option("Tasks", "--folder", "-f", help="目标文件夹"),
    status: Optional[str] = typer.Option(None, "--status", "-s", help="筛选任务状态"),
    priority: Optional[str] = typer.Option(None, "--priority", "-p", help="筛选任务优先级")
):
    """将PersonalManager任务同步到Obsidian"""
    
    config = PMConfig()
    
    # 构建过滤条件
    task_filter = {}
    if status:
        task_filter['status'] = status
    if priority:
        task_filter['priority'] = priority
    
    with console.status("[bold blue]同步任务到Obsidian...", spinner="dots"):
        success, message, data = sync_tasks_to_obsidian(
            vault_path, task_filter, folder, config
        )
    
    if success:
        console.print(Panel(
            f"[green]✅ {message}[/green]\n\n"
            f"• 总任务数: [cyan]{data['total_tasks']}[/cyan]\n"
            f"• 成功同步: [green]{data['synced_count']}[/green]\n"
            f"• 同步失败: [red]{data['failed_count']}[/red]\n"
            f"• 目标文件夹: [blue]{data['target_folder']}[/blue]",
            title="🔄 任务同步完成",
            border_style="green"
        ))
    else:
        console.print(Panel(
            f"[red]❌ {message}[/red]",
            title="同步失败",
            border_style="red"
        ))


@obsidian_app.command("graph")
def knowledge_graph(vault_path: str = typer.Argument(..., help="Obsidian Vault路径")):
    """生成知识图谱分析"""
    
    config = PMConfig()
    
    with console.status("[bold blue]分析知识图谱...", spinner="dots"):
        success, message, data = generate_knowledge_graph(vault_path, config)
    
    if success:
        console.print(Panel(
            f"[green]✅ {message}[/green]",
            title="🕸️ 知识图谱分析",
            border_style="green"
        ))
        
        # 显示图谱统计
        console.print(Panel(
            f"• 节点数量: [cyan]{data['total_nodes']}[/cyan]\n"
            f"• 连接数量: [yellow]{data['total_edges']}[/yellow]\n"
            f"• 图谱密度: [blue]{data['density']:.3f}[/blue]\n"
            f"• 孤立笔记: [red]{len(data['isolated_notes'])}[/red]",
            title="📊 图谱统计",
            border_style="blue"
        ))
        
        # 显示枢纽笔记
        if data['hub_notes']:
            console.print("\n[bold yellow]🌟 枢纽笔记（链接最多）:[/bold yellow]")
            for i, hub in enumerate(data['hub_notes'][:5], 1):
                node_info = data['nodes'][hub]
                console.print(f"  {i}. [cyan]{node_info['title']}[/cyan] ({node_info['link_count']} 个链接)")
        
        # 显示一些孤立笔记
        if data['isolated_notes']:
            console.print(f"\n[bold red]🏝️ 孤立笔记示例:[/bold red]")
            for isolated in data['isolated_notes'][:5]:
                node_info = data['nodes'][isolated]
                console.print(f"  • [dim]{node_info['title']}[/dim]")
    
    else:
        console.print(Panel(
            f"[red]❌ {message}[/red]",
            title="分析失败",
            border_style="red"
        ))


@obsidian_app.command("stats")
def vault_stats(vault_path: str = typer.Argument(..., help="Obsidian Vault路径")):
    """显示Vault统计信息"""
    
    config = PMConfig()
    
    with console.status("[bold blue]分析Vault统计信息...", spinner="dots"):
        success, message, data = get_vault_statistics(vault_path, config)
    
    if success:
        console.print(Panel(
            f"[green]✅ {message}[/green]",
            title="📈 Vault统计",
            border_style="green"
        ))
        
        # 基础信息
        basic = data['basic_info']
        console.print(Panel(
            f"• Vault名称: [cyan]{basic['vault_name']}[/cyan]\n"
            f"• Vault路径: [dim]{basic['vault_path']}[/dim]\n"
            f"• 最后分析: [yellow]{basic['last_analyzed']}[/yellow]",
            title="ℹ️ 基础信息",
            border_style="cyan"
        ))
        
        # 内容统计
        content = data['content_stats']
        console.print(Panel(
            f"• 笔记数量: [cyan]{content['total_notes']}[/cyan]\n"
            f"• 附件数量: [blue]{content['total_attachments']}[/blue]\n"
            f"• 总字数: [yellow]{content['total_words']:,}[/yellow]\n"
            f"• 预计阅读时长: [magenta]{content['total_reading_time_minutes']}分钟[/magenta]\n"
            f"• 平均笔记长度: [green]{content['average_note_length']}字[/green]",
            title="📝 内容统计",
            border_style="blue"
        ))
        
        # 标签分析
        tag_info = data['tag_analysis']
        if tag_info['top_tags']:
            console.print(f"\n[bold yellow]🏷️ 热门标签 (共{tag_info['total_unique_tags']}个):[/bold yellow]")
            
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("标签", style="cyan")
            table.add_column("使用次数", style="green", justify="right")
            
            for tag, count in tag_info['top_tags']:
                table.add_row(f"#{tag}", str(count))
            
            console.print(table)
        
        # 网络信息
        network = data['network_info']
        console.print(Panel(
            f"• 有链接的笔记: [green]{network['notes_with_links']}[/green]\n"
            f"• 孤立笔记: [red]{network['isolated_notes']}[/red]\n"
            f"• 连接率: [blue]{((content['total_notes'] - network['isolated_notes']) / max(1, content['total_notes']) * 100):.1f}%[/blue]",
            title="🔗 链接网络",
            border_style="magenta"
        ))
    
    else:
        console.print(Panel(
            f"[red]❌ {message}[/red]",
            title="统计失败",
            border_style="red"
        ))