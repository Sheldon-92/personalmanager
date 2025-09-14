"""工作空间管理 CLI 命令"""

import typer
import json
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from pm.workspace import init_workspace, ScaffoldReport

console = Console()

workspace_app = typer.Typer(
    name="workspace",
    help="AI 工作空间管理（实验性功能）",
    no_args_is_help=True,
    rich_markup_mode="rich"
)


@workspace_app.command("init")
def workspace_init(
    force: bool = typer.Option(False, "--force", "-f", help="强制覆盖已存在的文件"),
    root: Optional[str] = typer.Option(None, "--root", "-r", help="工作空间根目录（默认为当前目录）")
) -> None:
    """初始化 AI 工作空间配置

    生成工作空间三件套：
    • workspace-config.yaml - 工作空间配置
    • ai-agent-definition.md - AI Agent 定义
    • interaction-patterns.json - 意图映射规则

    [yellow]⚠️  实验性功能：接口可能在后续版本中变化[/yellow]
    """
    # 确定根目录
    workspace_root = Path(root) if root else Path.cwd()

    # 显示开始信息
    console.print(f"\n[bold blue]🚀 初始化工作空间[/bold blue]")
    console.print(f"📁 目标目录: {workspace_root}")

    if force:
        console.print("[yellow]⚠️  强制模式：将覆盖已存在的文件[/yellow]")

    console.print()

    try:
        # 调用库函数
        report = init_workspace(workspace_root, force=force)

        # 显示结果
        if report.success:
            _display_init_success(report, workspace_root)
        else:
            _display_init_failure(report)
            raise typer.Exit(1)

    except Exception as e:
        console.print(Panel(
            f"[red]❌ 初始化失败: {str(e)}[/red]",
            title="错误",
            border_style="red"
        ))
        raise typer.Exit(1)


def _display_init_success(report: ScaffoldReport, root: Path) -> None:
    """显示初始化成功信息"""

    # 创建结果表格
    table = Table(
        title="📋 操作结果",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan"
    )
    table.add_column("文件", style="green", width=40)
    table.add_column("状态", justify="center", width=10)

    # 添加创建的文件
    for file in report.created_files:
        table.add_row(f"✅ {file}", "[green]创建[/green]")

    # 添加跳过的文件
    for file in report.skipped_files:
        table.add_row(f"⏭️  {file}", "[yellow]跳过[/yellow]")

    if table.row_count > 0:
        console.print(table)

    # 显示摘要面板
    if report.created_files:
        summary = f"[green]✅ 成功创建 {len(report.created_files)} 个文件[/green]"
        if report.skipped_files:
            summary += f"\n[yellow]ℹ️  跳过 {len(report.skipped_files)} 个已存在的文件[/yellow]"

        next_steps = """
下一步操作：
1. 编辑 [cyan].personalmanager/workspace-config.yaml[/cyan] 自定义配置
2. 运行 [cyan]pm agent status[/cyan] 验证工作空间
3. 查看 [cyan]pm help workspace[/cyan] 了解更多命令"""

        console.print(Panel(
            summary + "\n" + next_steps,
            title="✨ 初始化成功",
            border_style="green"
        ))
    elif report.skipped_files:
        console.print(Panel(
            f"[yellow]ℹ️  工作空间已存在，跳过了所有文件[/yellow]\n"
            f"提示：使用 [cyan]--force[/cyan] 选项强制重新创建",
            title="工作空间已初始化",
            border_style="yellow"
        ))
    else:
        console.print(Panel(
            "[green]✅ 工作空间初始化完成[/green]",
            title="成功",
            border_style="green"
        ))


def _display_init_failure(report: ScaffoldReport) -> None:
    """显示初始化失败信息"""

    error_list = "\n".join([f"• {error}" for error in report.errors])

    console.print(Panel(
        f"[red]初始化过程中遇到以下错误：[/red]\n\n{error_list}\n\n"
        f"[yellow]建议：[/yellow]\n"
        f"• 检查目录权限\n"
        f"• 确保有足够的磁盘空间\n"
        f"• 验证 PersonalManager 安装完整性",
        title="❌ 初始化失败",
        border_style="red"
    ))