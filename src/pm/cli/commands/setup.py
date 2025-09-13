"""Setup wizard for PersonalManager initialization.

Refactored for Sprint 13: Uses AI-callable tool functions
CLI commands now act as thin wrappers around tool functions
"""

import os
import sys
from pathlib import Path
from typing import List
import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from pm.core.config import PMConfig
from pm.tools.setup_tools import (
    initialize_system, get_system_status, reset_system, 
    update_preferences, validate_system_setup
)

console = Console()


def setup_wizard(reset: bool = False) -> None:
    """PersonalManager设置向导 - 重构后使用AI可调用工具函数
    
    根据US-015验收标准实现：
    - 通过 `/pm setup` 启动设置向导
    - 设置基本工作偏好（工作时间、精力周期等）
    - 配置项目文件夹路径
    - 选择启用的书籍理论模块
    """
    
    # 检测是否在非交互式环境中运行
    is_interactive = sys.stdout.isatty() and sys.stdin.isatty() and os.getenv('CI') is None
    
    if not is_interactive:
        console.print(Panel(
            "[yellow]🤖 非交互模式检测\n\n"
            "检测到您在非交互式环境中运行（如CI/CD、脚本等）。\n"
            "将使用默认配置完成初始化。",
            title="非交互模式",
            border_style="yellow"
        ))
        
        # 使用默认配置进行初始化
        _initialize_with_defaults(reset)
        return
    
    console.print(Panel(
        "[bold blue]🚀 PersonalManager Agent 设置向导\n\n"
        "欢迎使用 PersonalManager！我们将引导您完成初始设置，\n"
        "这将帮助系统为您提供个性化的管理建议。",
        title="欢迎",
        border_style="blue"
    ))
    
    # 检查当前系统状态
    console.print("🔍 检查系统状态...")
    success, status_msg, status_info = get_system_status()
    
    if success and status_info:
        if status_info["system_initialized"] and not reset:
            console.print(f"[green]✅ {status_msg}")
            if not Confirm.ask("系统已初始化，是否重新配置？", default=False):
                return
        else:
            console.print(f"[yellow]ℹ️ {status_msg}")
    
    if reset:
        console.print("[yellow]⚠️ 重置模式：将清除现有配置")
        keep_data = Confirm.ask("是否保留用户数据？", default=True)
        success, reset_msg, reset_info = reset_system(keep_data=keep_data)
        if success:
            console.print(f"[green]✅ {reset_msg}")
        else:
            console.print(f"[red]❌ {reset_msg}")
            return
    
    # 1. 基本工作偏好设置
    console.print("\n[bold]📅 工作时间偏好设置")
    
    work_start = IntPrompt.ask(
        "请设置您的工作开始时间（24小时制）",
        default=9,
        show_default=True
    )
    
    work_end = IntPrompt.ask(
        "请设置您的工作结束时间（24小时制）", 
        default=18,
        show_default=True
    )
    
    # 2. 功能模块配置
    console.print("\n[bold]🔧 功能模块配置")
    
    enable_ai = Confirm.ask(
        "是否启用AI工具（报告生成、智能分析等）？", 
        default=True
    )
    
    enable_google = Confirm.ask(
        "是否启用Google集成（Calendar、Tasks、Gmail）？", 
        default=True
    )
    
    # 3. 项目根目录配置
    console.print("\n[bold]📁 项目根目录配置")
    
    current_dir = Path.cwd()
    default_projects_root = str(current_dir.parent)
    
    projects_root = Prompt.ask(
        "请设置项目根目录路径",
        default=default_projects_root
    )
    
    # 验证项目根目录
    projects_path = Path(projects_root).expanduser().resolve()
    if not projects_path.exists():
        if Confirm.ask(f"目录 {projects_path} 不存在，是否创建？", default=True):
            try:
                projects_path.mkdir(parents=True, exist_ok=True)
                console.print(f"[green]✅ 已创建项目根目录: {projects_path}")
            except Exception as e:
                console.print(f"[red]❌ 创建目录失败: {e}")
                projects_root = str(current_dir.parent)
        else:
            projects_root = str(current_dir.parent)
    
    # 4. 书籍理论模块配置
    console.print("\n[bold]📚 书籍理论模块配置")
    console.print("PersonalManager 整合了多本管理理论书籍的智慧，您可以选择启用哪些模块：")
    
    # 从PMConfig获取可用的书籍模块
    config = PMConfig()
    available_modules = {
        "gtd": "《搞定》(Getting Things Done) - GTD工作流",
        "atomic_habits": "《原子习惯》- 习惯养成理论",
        "deep_work": "《深度工作》- 专注力管理",
        "the_power_of_full_engagement": "《全力以赴》- 精力管理",
        "essentialism": "《本质主义》- 要事优先",
        "first_things_first": "《要事第一》- 时间管理矩阵",
    }
    
    enabled_book_modules = []
    for module_key, module_desc in available_modules.items():
        # 默认启用前三个核心模块
        default_enabled = module_key in ["gtd", "atomic_habits", "deep_work"]
        if Confirm.ask(f"启用 {module_desc}？", default=default_enabled):
            enabled_book_modules.append(module_key)
    
    # 5. 精力管理配置
    console.print("\n[bold]⚡ 精力管理配置")
    console.print("基于《全力以赴》理论，我们可以帮您跟踪和优化精力使用")
    
    energy_tracking_enabled = Confirm.ask("是否启用精力管理功能？", default=True)
    energy_peak_hours = []
    energy_low_hours = []
    
    if energy_tracking_enabled:
        peak_hours_input = Prompt.ask(
            "请输入您的精力高峰时段（24小时制，用逗号分隔，如：9,10,15）",
            default="9,10,11,14,15"
        )
        try:
            energy_peak_hours = [int(h.strip()) for h in peak_hours_input.split(",") if h.strip().isdigit()]
        except ValueError:
            console.print("[yellow]⚠️ 输入格式不正确，使用默认值")
            energy_peak_hours = [9, 10, 11, 14, 15]
        
        low_hours_input = Prompt.ask(
            "请输入您的精力低谷时段（24小时制，用逗号分隔，如：13,17,18）",
            default="13,17,18"
        )
        try:
            energy_low_hours = [int(h.strip()) for h in low_hours_input.split(",") if h.strip().isdigit()]
        except ValueError:
            console.print("[yellow]⚠️ 输入格式不正确，使用默认值")
            energy_low_hours = [13, 17, 18]

    # 6. 语言设置
    console.print("\n[bold]🌐 语言偏好设置")
    
    language = Prompt.ask(
        "请选择首选语言",
        choices=["zh", "en"],
        default="zh"
    )
    
    # 7. 调用AI可调用工具函数执行初始化
    console.print("\n[bold]💾 初始化系统...")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
    ) as progress:
        task = progress.add_task("正在初始化系统...", total=None)
        
        # 调用AI可调用工具函数
        success, init_msg, config_info = initialize_system(
            work_start=work_start,
            work_end=work_end,
            projects_root=projects_root,
            enable_ai_tools=enable_ai,
            enable_google_integration=enable_google,
            preferred_language=language,
            enabled_book_modules=enabled_book_modules,
            energy_tracking_enabled=energy_tracking_enabled,
            energy_peak_hours=energy_peak_hours,
            energy_low_hours=energy_low_hours
        )
        
        progress.update(task, description="系统初始化完成！")
    
    if not success:
        console.print(f"[red]❌ {init_msg}")
        raise typer.Exit(1)
    
    console.print(f"[green]✅ {init_msg}")
    
    # 6. 验证系统设置
    console.print("\n[bold]🔍 验证系统设置...")
    
    val_success, val_msg, val_results = validate_system_setup()
    if val_success and val_results:
        console.print(f"[green]✅ {val_msg}")
        
        # 显示验证结果摘要
        if val_results.get("summary"):
            summary = val_results["summary"]
            console.print(f"[blue]检查项: {summary['total_checks']}, 通过: {summary['passed_count']}, 警告: {summary['warning_count']}, 失败: {summary['failed_count']}")
    else:
        console.print(f"[yellow]⚠️ {val_msg}")
    
    # 8. 配置总结
    console.print("\n[bold green]✅ 设置完成！")
    
    if config_info:
        summary_table = Table(title="配置总结")
        summary_table.add_column("设置项", style="cyan")
        summary_table.add_column("值", style="green")
        
        summary_table.add_row("工作时间", config_info["work_hours"])
        summary_table.add_row("AI工具", "✅ 已启用" if config_info["ai_tools_enabled"] else "❌ 已禁用")
        summary_table.add_row("Google集成", "✅ 已启用" if config_info["google_integration_enabled"] else "❌ 已禁用")
        summary_table.add_row("项目根目录", str(config_info["projects_root"]))
        summary_table.add_row("数据目录", str(config_info["data_directory"]))
        summary_table.add_row("首选语言", config_info["language"])
        
        # 添加书籍模块信息
        if "enabled_book_modules" in config_info and config_info["enabled_book_modules"]:
            modules_str = ", ".join(config_info["enabled_book_modules"])
            summary_table.add_row("启用的理论模块", modules_str)
        else:
            summary_table.add_row("启用的理论模块", "无")
        
        # 添加精力管理信息
        if "energy_tracking_enabled" in config_info:
            energy_status = "✅ 已启用" if config_info["energy_tracking_enabled"] else "❌ 已禁用"
            summary_table.add_row("精力管理", energy_status)
            
            if config_info["energy_tracking_enabled"]:
                if "energy_peak_hours" in config_info:
                    peak_hours = ", ".join(map(str, config_info["energy_peak_hours"]))
                    summary_table.add_row("精力高峰时段", f"{peak_hours}点")
                
                if "energy_low_hours" in config_info:
                    low_hours = ", ".join(map(str, config_info["energy_low_hours"]))
                    summary_table.add_row("精力低谷时段", f"{low_hours}点")
        
        console.print(summary_table)
    
    console.print(Panel(
        "[green]🎉 PersonalManager Agent 已准备就绪！\n\n"
        "您现在可以开始使用以下功能：\n"
        "• [cyan]pm help[/cyan] - 查看所有可用命令\n"
        "• [cyan]pm habits create \"习惯名称\"[/cyan] - 创建新习惯\n"
        "• [cyan]pm capture \"任务描述\"[/cyan] - 快速捕获任务\n"
        "• [cyan]pm next[/cyan] - 查看下一步行动\n"
        "• [cyan]pm report update[/cyan] - 生成AI项目报告",
        title="🚀 设置成功",
        border_style="green"
    ))


def _initialize_with_defaults(reset: bool = False) -> None:
    """在非交互模式下使用默认配置初始化系统"""
    try:
        # 检查是否需要重置
        if reset:
            console.print("[yellow]⚠️ 重置模式：清除现有配置")
            success, reset_msg, reset_info = reset_system(keep_data=True)
            if success:
                console.print(f"[green]✅ {reset_msg}")
            else:
                console.print(f"[red]❌ {reset_msg}")
                return
        
        # 使用默认配置初始化
        console.print("💾 使用默认配置初始化系统...")
        
        # 默认配置参数
        current_dir = Path.cwd()
        default_projects_root = str(current_dir.parent)
        
        success, init_msg, config_info = initialize_system(
            work_start=9,
            work_end=18,
            projects_root=default_projects_root,
            enable_ai_tools=True,
            enable_google_integration=False,  # 隐私优先：默认关闭Google集成
            preferred_language="zh",
            enabled_book_modules=["gtd", "atomic_habits", "deep_work"],
            energy_tracking_enabled=True,
            energy_peak_hours=[9, 10, 11, 14, 15],
            energy_low_hours=[13, 17, 18]
        )
        
        if success:
            console.print(f"[green]✅ {init_msg}")
            console.print(Panel(
                "[green]🎉 PersonalManager 默认配置初始化完成！\n\n"
                "默认设置：\n"
                "• 工作时间: 9:00-18:00\n"
                "• AI工具: 启用\n"
                "• Google集成: 禁用（隐私优先）\n"
                "• 理论模块: GTD, 原子习惯, 深度工作\n"
                "• 精力管理: 启用\n\n"
                "您可以稍后通过 'pm setup --reset' 重新配置。",
                title="🚀 初始化成功",
                border_style="green"
            ))
        else:
            console.print(f"[red]❌ {init_msg}")
            raise typer.Exit(1)
            
    except Exception as e:
        console.print(f"[red]❌ 非交互模式初始化失败: {str(e)}")
        raise typer.Exit(1)