"""AI驱动的项目报告命令 - Sprint 11-12核心功能"""

import os
import typer
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from typing import Optional

from pm.core.config import PMConfig
from pm.integrations.report_generator import ReportGenerator
from pm.integrations.ai_service import AIServiceError

console = Console()


def update_project_report(
    project_name: Optional[str] = None,
    project_path: Optional[str] = None
) -> None:
    """更新项目状态报告
    
    Args:
        project_name: 项目名称（可选）
        project_path: 项目路径（可选，默认使用当前目录）
    """
    
    config = PMConfig()
    
    # 检查AI工具是否启用
    if not config.ai_tools_enabled:
        console.print(Panel(
            "[red]❌ AI工具已禁用[/red]\\n\\n"
            "请在配置中启用AI工具，或设置环境变量：\\n"
            "[cyan]export PM_AI_TOOLS_ENABLED=true[/cyan]",
            title="AI工具未启用",
            border_style="red"
        ))
        return
    
    # 确定项目路径
    if project_path:
        target_path = Path(project_path).resolve()
    else:
        target_path = Path.cwd()
    
    if not target_path.exists() or not target_path.is_dir():
        console.print(Panel(
            f"[red]❌ 项目路径不存在或不是目录[/red]\\n\\n"
            f"路径: {target_path}",
            title="路径错误",
            border_style="red"
        ))
        return
    
    # 确定项目名称
    if not project_name:
        project_name = target_path.name
    
    console.print(Panel(
        f"[cyan]🤖 AI项目报告生成[/cyan]\\n\\n"
        f"• 项目名称: [yellow]{project_name}[/yellow]\\n"
        f"• 项目路径: [dim]{target_path}[/dim]\\n"
        f"• 输出文件: [green]PROJECT_STATUS.md[/green]\\n\\n"
        f"AI将分析项目文档并自动生成状态报告...",
        title="📊 项目分析开始",
        border_style="blue"
    ))
    
    # 检查AI服务可用性
    report_generator = ReportGenerator(config)
    
    if not report_generator.ai_service.is_any_service_available():
        console.print(Panel(
            "[red]❌ 没有可用的AI服务[/red]\\n\\n"
            "请检查API密钥配置：\\n"
            "• Claude: [cyan]export PM_CLAUDE_API_KEY=your_key[/cyan]\\n"
            "• Gemini: [cyan]export PM_GEMINI_API_KEY=your_key[/cyan]\\n\\n"
            "或在配置文件中设置相应的API密钥。",
            title="AI服务不可用",
            border_style="red"
        ))
        return
    
    # 显示可用的AI服务
    available_services = report_generator.ai_service.get_available_services()
    service_names = [service.value.title() for service in available_services]
    console.print(f"[dim]🔧 可用AI服务: {', '.join(service_names)}[/dim]\\n")
    
    # 执行报告生成
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            
            # 分析项目文档
            task1 = progress.add_task("📖 分析项目文档...", total=None)
            
            # 调用AI生成报告
            progress.update(task1, description="🤖 AI分析中...")
            
            success, message = report_generator.generate_report(
                project_path=str(target_path),
                project_name=project_name
            )
            
            progress.update(task1, description="✅ 报告生成完成")
        
        if success:
            # 成功生成报告
            status_file = target_path / "PROJECT_STATUS.md"
            
            console.print(Panel(
                f"[green]✅ 报告生成成功！[/green]\\n\\n"
                f"• 输出文件: [cyan]{status_file}[/cyan]\\n"
                f"• 生成时间: [dim]{_get_current_time()}[/dim]\\n\\n"
                f"[yellow]📋 报告内容已保存到 PROJECT_STATUS.md[/yellow]\\n"
                f"您可以查看和编辑这份AI生成的状态报告。",
                title="🎉 生成完成",
                border_style="green"
            ))
            
            # 显示快速预览
            if status_file.exists():
                try:
                    with open(status_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 提取前几行作为预览
                    lines = content.split('\\n')[:8]
                    preview = '\\n'.join(lines)
                    
                    console.print(Panel(
                        f"[dim]{preview}...[/dim]",
                        title="📄 报告预览",
                        border_style="dim"
                    ))
                    
                except Exception:
                    pass  # 预览失败不影响主要功能
            
        else:
            # 生成失败
            console.print(Panel(
                f"[red]❌ 报告生成失败[/red]\\n\\n"
                f"错误信息: {message}\\n\\n"
                f"请检查项目配置和文档结构。",
                title="生成失败",
                border_style="red"
            ))
        
    except AIServiceError as e:
        console.print(Panel(
            f"[red]❌ AI服务调用失败[/red]\\n\\n"
            f"错误详情: {str(e)}\\n\\n"
            f"请检查API密钥配置和网络连接。",
            title="AI服务错误",
            border_style="red"
        ))
    except Exception as e:
        console.print(Panel(
            f"[red]❌ 发生未知错误[/red]\\n\\n"
            f"错误详情: {str(e)}\\n\\n"
            f"请联系支持或查看日志了解详情。",
            title="系统错误",
            border_style="red"
        ))


def show_ai_service_status() -> None:
    """显示AI服务状态"""
    
    config = PMConfig()
    report_generator = ReportGenerator(config)
    
    console.print(Panel(
        "[cyan]🤖 AI服务状态检查[/cyan]",
        title="服务诊断",
        border_style="blue"
    ))
    
    # 获取服务状态
    service_status = report_generator.ai_service.get_service_status()
    
    for service_name, status in service_status.items():
        if status["initialized"] and status["available"]:
            status_icon = "[green]✅[/green]"
            status_text = "[green]可用[/green]"
        elif status["initialized"] and not status["available"]:
            status_icon = "[yellow]⚠️[/yellow]"
            status_text = "[yellow]已初始化但不可用[/yellow]"
        else:
            status_icon = "[red]❌[/red]"
            status_text = "[red]未初始化[/red]"
        
        console.print(f"{status_icon} {service_name.title()}: {status_text}")
        
        if status["error"]:
            console.print(f"   [dim]错误: {status['error']}[/dim]")
    
    # 显示配置建议
    console.print("\\n[dim]💡 配置提示:[/dim]")
    console.print("[dim]• Claude API: export PM_CLAUDE_API_KEY=your_key[/dim]")
    console.print("[dim]• Gemini API: export PM_GEMINI_API_KEY=your_key[/dim]")
    console.print("[dim]• AI功能启用: export PM_AI_TOOLS_ENABLED=true[/dim]")


def create_sample_project_config() -> None:
    """在当前目录创建示例项目配置"""
    
    config_file = Path.cwd() / ".pm-config.yaml"
    
    if config_file.exists():
        console.print(Panel(
            "[yellow]⚠️ 配置文件已存在[/yellow]\\n\\n"
            f"文件位置: {config_file}\\n\\n"
            "如需重新创建，请先删除现有文件。",
            title="文件已存在",
            border_style="yellow"
        ))
        return
    
    sample_config = '''# PersonalManager项目配置文件
# 用于AI报告生成功能

report_generation:
  # 计划文档 - 用于评估进度的基准文件
  plan_documents:
    - "GOALS.md"
    - "OUTLINE.md"
    - "README.md"
    - "PLAN.md"
    - "docs/requirements.md"
  
  # 工作成果文档 - 体现实际工作进展的文件
  work_documents:
    - "*.md"
    - "docs/*.md"
    - "chapters/*.md"
    - "src/**/*.py"
    - "progress/*.md"
    - "implementation/*.md"

# 其他配置选项可以在这里添加
'''
    
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(sample_config)
        
        console.print(Panel(
            f"[green]✅ 示例配置文件已创建[/green]\\n\\n"
            f"文件位置: [cyan]{config_file}[/cyan]\\n\\n"
            f"请根据项目结构编辑配置文件，然后运行:\\n"
            f"[yellow]pm report update[/yellow]",
            title="配置创建成功",
            border_style="green"
        ))
        
    except Exception as e:
        console.print(Panel(
            f"[red]❌ 创建配置文件失败[/red]\\n\\n"
            f"错误: {str(e)}",
            title="创建失败",
            border_style="red"
        ))


def _get_current_time() -> str:
    """获取当前时间字符串"""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")