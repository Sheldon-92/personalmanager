"""AI Agent 工具集 CLI 命令"""

import sys
import json
import typer
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from pm.workspace import validate_workspace, ValidationReport, CheckLevel

console = Console()

agent_app = typer.Typer(
    name="agent",
    help="AI Agent 工具集（实验性功能）",
    no_args_is_help=True,
    rich_markup_mode="rich"
)


@agent_app.command("status")
def agent_status(
    json_output: bool = typer.Option(False, "--json", help="以 JSON 格式输出（适合程序化消费）"),
    root: Optional[str] = typer.Option(None, "--root", "-r", help="工作空间根目录（默认为当前目录）")
) -> None:
    """检查工作空间状态和配置

    执行全面的工作空间校验，包括：
    • 文件存在性检查
    • 语法验证（YAML/JSON）
    • 必填字段检查
    • 配置值合法性验证
    • 文件大小检查

    [yellow]⚠️  实验性功能：接口可能在后续版本中变化[/yellow]

    退出码：
    • 0 - 验证通过或仅有警告
    • 1 - 存在错误
    """
    # 确定根目录
    workspace_root = Path(root) if root else Path.cwd()

    try:
        # 调用库函数
        report = validate_workspace(workspace_root)

        # 根据输出模式显示结果
        if json_output:
            _output_json_report(report)
        else:
            _display_human_report(report, workspace_root)

        # 设置退出码
        exit_code = 0 if report.is_valid() else 1
        raise typer.Exit(exit_code)

    except typer.Exit:
        # 重新抛出 typer.Exit 以保留退出码
        raise
    except Exception as e:
        if json_output:
            # JSON 模式下输出错误
            error_report = {
                "error": str(e),
                "items": [],
                "summary": {"ok": 0, "warn": 0, "error": 1}
            }
            console.print(json.dumps(error_report, ensure_ascii=False, indent=2))
        else:
            # 人类可读模式下显示错误面板
            console.print(Panel(
                f"[red]❌ 状态检查失败: {str(e)}[/red]",
                title="错误",
                border_style="red"
            ))
        raise typer.Exit(1)


def _output_json_report(report: ValidationReport) -> None:
    """输出 JSON 格式的校验报告"""
    report_dict = report.to_dict()
    console.print(json.dumps(report_dict, ensure_ascii=False, indent=2))


def _display_human_report(report: ValidationReport, root: Path) -> None:
    """显示人类可读的校验报告"""

    # 显示标题
    console.print(f"\n[bold blue]🔍 工作空间状态检查[/bold blue]")
    console.print(f"📁 检查目录: {root}")
    console.print()

    # 创建状态表格
    table = Table(
        title="📋 检查结果",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan"
    )
    table.add_column("检查项", style="white", width=35)
    table.add_column("级别", justify="center", width=8)
    table.add_column("消息", style="white", width=45)

    # 按级别分组项目
    errors = []
    warnings = []
    infos = []

    for item in report.items:
        if item.level == CheckLevel.ERROR:
            errors.append(item)
        elif item.level == CheckLevel.WARN:
            warnings.append(item)
        else:
            infos.append(item)

    # 先显示错误
    for item in errors:
        level_display = "[red]❌ 错误[/red]"
        table.add_row(item.check, level_display, item.message)

    # 再显示警告
    for item in warnings:
        level_display = "[yellow]⚠️  警告[/yellow]"
        table.add_row(item.check, level_display, item.message)

    # 最后显示成功项（只显示前5个）
    displayed_ok = 0
    for item in infos[:5]:
        level_display = "[green]✅ 通过[/green]"
        table.add_row(item.check, level_display, item.message)
        displayed_ok += 1

    if len(infos) > 5:
        table.add_row("...", "[dim]...[/dim]", f"[dim]还有 {len(infos) - 5} 个检查项通过[/dim]")

    console.print(table)

    # 显示修复建议（如果有错误或警告）
    if errors or warnings:
        console.print("\n[bold yellow]💡 修复建议[/bold yellow]")
        suggestions = []

        # 收集带建议的项目
        for item in errors[:3]:  # 最多显示3个错误的建议
            if item.suggest:
                suggestions.append(f"[red]•[/red] {item.suggest}")

        for item in warnings[:2]:  # 最多显示2个警告的建议
            if item.suggest:
                suggestions.append(f"[yellow]•[/yellow] {item.suggest}")

        if suggestions:
            for suggestion in suggestions:
                console.print(suggestion)
        console.print()

    # 显示摘要面板
    _display_summary_panel(report)


def _display_summary_panel(report: ValidationReport) -> None:
    """显示摘要面板"""
    summary = report.summary

    # 确定面板样式和标题
    if summary["error"] > 0:
        panel_style = "red"
        title = "❌ 检查未通过"
        status = f"[red]发现 {summary['error']} 个错误需要修复[/red]"
    elif summary["warn"] > 0:
        panel_style = "yellow"
        title = "⚠️  检查通过（有警告）"
        status = f"[yellow]发现 {summary['warn']} 个警告建议处理[/yellow]"
    else:
        panel_style = "green"
        title = "✅ 检查通过"
        status = "[green]工作空间配置完全正常[/green]"

    # 构建统计信息
    stats = f"""
{status}

统计：
• [green]通过: {summary['ok']}[/green]
• [yellow]警告: {summary['warn']}[/yellow]
• [red]错误: {summary['error']}[/red]
"""

    # 添加下一步建议
    if summary["error"] > 0:
        next_steps = """
下一步：
1. 根据上述建议修复错误
2. 重新运行 [cyan]pm agent status[/cyan] 验证
3. 如需重新初始化，运行 [cyan]pm workspace init --force[/cyan]"""
    elif summary["warn"] > 0:
        next_steps = """
下一步：
1. 考虑处理警告以优化配置
2. 查看 [cyan]pm help agent[/cyan] 了解更多"""
    else:
        next_steps = """
下一步：
1. 工作空间已就绪，可以开始使用
2. 在 AI Agent 中加载项目配置"""

    console.print(Panel(
        stats.strip() + "\n" + next_steps,
        title=title,
        border_style=panel_style
    ))


def _map_to_error_code(check: str, level: CheckLevel) -> Optional[str]:
    """将检查项映射到错误码"""
    if level != CheckLevel.ERROR:
        return None

    error_map = {
        "workspace_directory": "E1001",  # 配置未初始化
        "file_exists_": "E1003",  # 文件不存在
        "yaml_syntax_": "E1004",  # 语法错误
        "json_syntax_": "E1004",  # 语法错误
        "required_fields_": "E2004",  # 配置无效
        "routing_threshold": "E2004",  # 配置无效
        "context_path": "E2004",  # 配置无效
    }

    for pattern, code in error_map.items():
        if pattern in check:
            return code

    return "E2004"  # 默认配置错误