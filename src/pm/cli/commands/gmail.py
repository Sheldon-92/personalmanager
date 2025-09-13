"""Gmail集成命令 - Sprint 9-10核心功能"""

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from typing import Optional

from pm.core.config import PMConfig
from pm.integrations.gmail_processor import GmailProcessor

console = Console()


def scan_important_emails(days: int = 1) -> None:
    """扫描重要邮件并转换为GTD任务"""
    
    config = PMConfig()
    if not config.is_initialized():
        console.print(Panel(
            "[yellow]系统未初始化。请先运行 [cyan]pm setup[/cyan] 进行设置。",
            title="⚠️ 未初始化",
            border_style="yellow"
        ))
        return
    
    gmail_processor = GmailProcessor(config)
    
    # 检查认证状态
    if not gmail_processor.google_auth.is_google_authenticated():
        console.print(Panel(
            "[red]未通过Google认证。请先运行：[cyan]pm auth login google[/cyan]",
            title="❌ 认证错误",
            border_style="red"
        ))
        return
    
    console.print(Panel(
        f"[cyan]📧 Gmail 重要邮件扫描[/cyan]\\n\\n"
        f"正在扫描过去 {days} 天的重要邮件...",
        title="🔍 邮件扫描",
        border_style="blue"
    ))
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            scan_task = progress.add_task("扫描邮件...", total=None)
            
            # 扫描重要邮件
            important_emails, scan_errors = gmail_processor.scan_important_emails(
                days_back=days, max_emails=50
            )
            
            progress.update(scan_task, description="转换为GTD任务...")
            
            # 转换为GTD任务
            converted_count, convert_errors = gmail_processor.convert_emails_to_tasks(important_emails)
            
            progress.update(scan_task, description="扫描完成")
        
        # 显示扫描结果
        if important_emails:
            console.print(Panel(
                f"[green]✅ 扫描完成！[/green]\\n\\n"
                f"• 发现重要邮件: [cyan]{len(important_emails)}[/cyan] 封\\n"
                f"• 转换为GTD任务: [yellow]{converted_count}[/yellow] 个\\n"
                f"• 扫描范围: 过去 {days} 天\\n\\n"
                "新的邮件任务已添加到收件箱：\\n"
                "• [cyan]pm inbox[/cyan] - 查看收件箱\\n"
                "• [cyan]pm clarify[/cyan] - 处理收件箱任务",
                title="🎉 扫描完成",
                border_style="green"
            ))
        else:
            console.print(Panel(
                f"[yellow]ℹ️ 未发现重要邮件[/yellow]\\n\\n"
                f"在过去 {days} 天内没有找到符合重要性标准的邮件。\\n\\n"
                "可能的原因：\\n"
                "• 邮箱中没有新的重要邮件\\n"
                "• 重要邮件已经处理过了\\n"
                "• 邮件重要性评分较低",
                title="📋 扫描结果",
                border_style="yellow"
            ))
        
        # 显示错误信息
        all_errors = scan_errors + convert_errors
        if all_errors:
            console.print(Panel(
                "[red]⚠️ 处理过程中遇到以下问题：[/red]\\n\\n" +
                "\\n".join([f"• {error}" for error in all_errors[:5]]),  # 只显示前5个错误
                title="❗ 警告",
                border_style="red"
            ))
    
    except Exception as e:
        console.print(Panel(
            f"[red]❌ 邮件扫描失败: {str(e)}[/red]",
            title="扫描错误",
            border_style="red"
        ))


def show_email_preview(days: int = 1) -> None:
    """预览重要邮件（不转换为任务）"""
    
    config = PMConfig()
    if not config.is_initialized():
        console.print(Panel(
            "[yellow]系统未初始化。请先运行 [cyan]pm setup[/cyan] 进行设置。",
            title="⚠️ 未初始化",
            border_style="yellow"
        ))
        return
    
    gmail_processor = GmailProcessor(config)
    
    # 检查认证状态
    if not gmail_processor.google_auth.is_google_authenticated():
        console.print(Panel(
            "[red]未通过Google认证。请先运行：[cyan]pm auth login google[/cyan]",
            title="❌ 认证错误",
            border_style="red"
        ))
        return
    
    with console.status(f"[bold blue]扫描过去 {days} 天的重要邮件...", spinner="dots"):
        important_emails, errors = gmail_processor.scan_important_emails(
            days_back=days, max_emails=20
        )
    
    if not important_emails:
        console.print(Panel(
            f"[yellow]📧 未发现重要邮件[/yellow]\\n\\n"
            f"在过去 {days} 天内没有找到重要邮件。",
            title="📋 邮件预览",
            border_style="yellow"
        ))
        return
    
    # 创建邮件预览表格
    emails_table = Table(show_header=True, header_style="bold magenta")
    emails_table.add_column("重要性", style="red", justify="center", width=8)
    emails_table.add_column("发件人", style="cyan", width=20)
    emails_table.add_column("主题", style="white", width=40)
    emails_table.add_column("收到时间", style="yellow", width=16)
    
    for email in important_emails[:10]:  # 只显示前10封
        # 重要性指示器
        if email.is_urgent:
            importance = "🚨 紧急"
            importance_style = "bold red"
        elif email.is_important:
            importance = "⚡ 重要" 
            importance_style = "bold yellow"
        else:
            importance = "📧 一般"
            importance_style = "dim"
        
        # 截断长文本
        sender_name = email.sender_name[:18] + "..." if len(email.sender_name) > 18 else email.sender_name
        subject = email.subject[:38] + "..." if len(email.subject) > 38 else email.subject
        received_time = email.received_date.strftime("%m-%d %H:%M")
        
        emails_table.add_row(
            f"[{importance_style}]{importance}[/{importance_style}]",
            sender_name,
            subject,
            received_time
        )
    
    console.print(Panel(
        emails_table,
        title=f"📧 重要邮件预览 (共{len(important_emails)}封)",
        border_style="blue"
    ))
    
    # 显示操作建议
    console.print(Panel(
        f"[green]💡 发现 {len(important_emails)} 封重要邮件[/green]\\n\\n"
        "建议操作：\\n"
        f"• [cyan]pm gmail scan {days}[/cyan] - 将这些邮件转换为GTD任务\\n"
        "• [cyan]pm inbox[/cyan] - 查看转换后的任务\\n"
        "• [cyan]pm clarify[/cyan] - 处理邮件任务",
        title="📋 操作建议",
        border_style="green"
    ))


def show_email_stats() -> None:
    """显示Gmail集成统计信息"""
    
    config = PMConfig()
    if not config.is_initialized():
        console.print(Panel(
            "[yellow]系统未初始化。请先运行 [cyan]pm setup[/cyan] 进行设置。",
            title="⚠️ 未初始化",
            border_style="yellow"
        ))
        return
    
    gmail_processor = GmailProcessor(config)
    
    # 检查认证状态
    if not gmail_processor.google_auth.is_google_authenticated():
        console.print(Panel(
            "[red]未通过Google认证。请先运行：[cyan]pm auth login google[/cyan]",
            title="❌ 认证错误",
            border_style="red"
        ))
        return
    
    from pm.agents.gtd_agent import GTDAgent
    agent = GTDAgent(config)
    
    with console.status("[bold blue]分析Gmail集成统计...", spinner="dots"):
        all_tasks = agent.storage.get_all_tasks()
        
        # 统计邮件任务
        email_tasks = [task for task in all_tasks if task.source == "gmail"]
        
        # 按状态分类
        inbox_emails = len([t for t in email_tasks if t.status.value == "inbox"])
        next_action_emails = len([t for t in email_tasks if t.status.value == "next_action"])
        completed_emails = len([t for t in email_tasks if t.status.value == "completed"])
        
        # 按优先级分类
        high_priority = len([t for t in email_tasks if t.priority.value == "high"])
        medium_priority = len([t for t in email_tasks if t.priority.value == "medium"])
        low_priority = len([t for t in email_tasks if t.priority.value == "low"])
    
    # 创建统计表格
    stats_table = Table(show_header=True, header_style="bold magenta")
    stats_table.add_column("统计项目", style="cyan")
    stats_table.add_column("数量", style="green", justify="center")
    stats_table.add_column("说明", style="yellow")
    
    stats_table.add_row("邮件任务总数", str(len(email_tasks)), "从Gmail转换的任务")
    stats_table.add_row("", "", "")  # 分隔行
    stats_table.add_row("收件箱", str(inbox_emails), "待处理的邮件任务")
    stats_table.add_row("下一步行动", str(next_action_emails), "已分类的邮件任务")
    stats_table.add_row("已完成", str(completed_emails), "已处理的邮件任务")
    stats_table.add_row("", "", "")  # 分隔行
    stats_table.add_row("高优先级", str(high_priority), "紧急重要邮件")
    stats_table.add_row("中优先级", str(medium_priority), "一般重要邮件")
    stats_table.add_row("低优先级", str(low_priority), "普通邮件")
    
    console.print(Panel(
        stats_table,
        title="📊 Gmail 集成统计",
        border_style="blue"
    ))
    
    # 显示使用建议
    if len(email_tasks) == 0:
        console.print(Panel(
            "[yellow]🚀 开始使用Gmail集成功能[/yellow]\\n\\n"
            "您还没有从Gmail导入任何任务。\\n"
            "运行以下命令开始：\\n"
            "[cyan]pm gmail scan[/cyan] - 扫描重要邮件",
            title="💡 使用建议",
            border_style="yellow"
        ))
    elif inbox_emails > 0:
        console.print(Panel(
            f"[yellow]📧 您有 {inbox_emails} 个邮件任务待处理[/yellow]\\n\\n"
            "建议操作：\\n"
            "• [cyan]pm inbox[/cyan] - 查看收件箱\\n"
            "• [cyan]pm clarify[/cyan] - 处理邮件任务",
            title="⏰ 待处理提醒",
            border_style="yellow"
        ))
    else:
        console.print(Panel(
            "[green]✅ 邮件任务处理良好[/green]\\n\\n"
            "所有邮件任务都已处理完毕。\\n"
            "继续保持这个好习惯！",
            title="🎉 状态良好",
            border_style="green"
        ))