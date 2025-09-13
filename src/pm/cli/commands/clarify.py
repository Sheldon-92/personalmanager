"""GTD clarification process commands."""

from typing import Optional, List, Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.text import Text
import typer

from pm.core.config import PMConfig
from pm.agents.gtd_agent import GTDAgent
from pm.models.task import Task, TaskStatus, TaskContext, TaskPriority, EnergyLevel

console = Console()


def clarify_tasks() -> None:
    """GTD任务理清流程
    
    根据US-007验收标准实现：
    - 通过 `/pm clarify` 启动交互式理清流程
    - 系统依次询问：是否需要行动？期望结果是什么？下一步行动是什么？
    - 根据答案自动分类：项目、下一步行动、将来/也许、参考资料、垃圾
    - 支持批量理清多个项目
    """
    
    config = PMConfig()
    if not config.is_initialized():
        console.print(Panel(
            "[yellow]系统未初始化。请先运行 [cyan]pm setup[/cyan] 进行设置。",
            title="⚠️ 未初始化",
            border_style="yellow"
        ))
        return
    
    agent = GTDAgent(config)
    inbox_tasks = agent.get_inbox_tasks()
    
    if not inbox_tasks:
        console.print(Panel(
            "[green]🎉 收件箱为空！\n\n"
            "所有任务都已理清。这是GTD的理想状态！\n\n"
            "使用 [cyan]pm capture \"新任务\"[/cyan] 捕获新的想法或任务",
            title="📥 收件箱已清空",
            border_style="green"
        ))
        return
    
    # 显示理清流程介绍
    console.print(Panel(
        f"[bold blue]🤔 GTD理清流程\n\n"
        f"[green]收件箱中有 {len(inbox_tasks)} 个任务待理清。\n\n"
        "[white]理清流程将帮助您：\n"
        "• 确定每个任务是否需要行动\n"
        "• 明确期望结果和下一步行动\n"
        "• 正确分类任务到合适的清单\n\n"
        "[dim]按照GTD原则，我们将逐一处理每个任务。",
        title="开始理清",
        border_style="blue"
    ))
    
    if not Confirm.ask("开始理清流程？", default=True):
        console.print("[yellow]理清流程已取消")
        return
    
    # 统计变量
    clarified_count = 0
    next_actions_count = 0
    projects_count = 0
    someday_count = 0
    reference_count = 0
    deleted_count = 0
    
    # 逐个理清任务
    for i, task in enumerate(inbox_tasks, 1):
        console.print(f"\n[bold cyan]正在理清任务 {i}/{len(inbox_tasks)}[/bold cyan]")
        
        # 显示任务信息
        task_panel = Panel(
            f"[bold white]{task.title}[/bold white]\n\n"
            f"[dim]任务ID: {task.id[:8]}...\n"
            f"捕获时间: {task.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"捕获位置: {task.capture_location if task.capture_location else '未知'}[/dim]"
            + (f"\n\n[yellow]描述: {task.description}[/yellow]" if task.description else ""),
            title="📋 当前任务",
            border_style="cyan"
        )
        console.print(task_panel)
        
        # 显示智能建议
        if any([task.suggested_context, task.suggested_priority]):
            suggestions = []
            if task.suggested_context:
                suggestions.append(f"建议情境: {task.suggested_context.value}")
            if task.suggested_priority:
                suggestions.append(f"建议优先级: {task.suggested_priority.value}")
            
            console.print(Panel(
                "\n".join(suggestions),
                title="🤖 智能建议",
                border_style="green"
            ))
        
        try:
            result = _clarify_single_task(task, agent)
            
            if result["action"] == "clarified":
                clarified_count += 1
                if result["status"] == TaskStatus.NEXT_ACTION:
                    next_actions_count += 1
                elif result["status"] == TaskStatus.PROJECT:
                    projects_count += 1
                elif result["status"] == TaskStatus.SOMEDAY_MAYBE:
                    someday_count += 1
                elif result["status"] == TaskStatus.REFERENCE:
                    reference_count += 1
                elif result["status"] == TaskStatus.DELETED:
                    deleted_count += 1
            
            elif result["action"] == "skip":
                console.print("[yellow]⏭️ 跳过此任务")
            
            elif result["action"] == "quit":
                console.print("[yellow]退出理清流程")
                break
                
        except KeyboardInterrupt:
            console.print("\n[yellow]理清流程被中断")
            break
        except Exception as e:
            console.print(f"\n[red]处理任务时出错: {str(e)}")
            continue
    
    # 显示理清结果总结
    _show_clarify_summary(clarified_count, next_actions_count, projects_count, 
                         someday_count, reference_count, deleted_count)


def _clarify_single_task(task: Task, agent: GTDAgent) -> Dict[str, Any]:
    """理清单个任务"""
    
    # GTD核心问题1: 这是什么？
    console.print("[bold yellow]🔍 首先，让我们明确这个任务的性质...[/bold yellow]")
    
    # GTD核心问题2: 是否需要行动？
    actionable = Confirm.ask(
        "[bold]📝 这个任务是否需要行动？[/bold]",
        default=True
    )
    
    if not actionable:
        return _handle_non_actionable_task(task, agent)
    
    # 需要行动的任务继续理清
    console.print("\n[green]✅ 这个任务需要行动[/green]")
    
    # GTD核心问题3: 期望结果是什么？
    console.print("\n[bold yellow]🎯 让我们明确期望结果...[/bold yellow]")
    
    outcome = Prompt.ask(
        "[bold]期望结果是什么？（描述成功完成后的状态）[/bold]",
        default=task.title
    )
    
    # GTD核心问题4: 下一步行动是什么？
    console.print("\n[bold yellow]⚡ 确定具体的下一步行动...[/bold yellow]")
    
    next_action = Prompt.ask(
        "[bold]下一步具体行动是什么？（可执行的物理动作）[/bold]",
        default=task.title
    )
    
    # 判断是项目还是单一行动
    console.print("\n[bold yellow]🤔 评估任务复杂度...[/bold yellow]")
    
    is_project = Confirm.ask(
        "[bold]完成这个结果需要多个步骤吗？（超过一个行动）[/bold]",
        default=False
    )
    
    if is_project:
        return _handle_project_task(task, agent, outcome, next_action)
    else:
        return _handle_single_action_task(task, agent, next_action)


def _handle_non_actionable_task(task: Task, agent: GTDAgent) -> Dict[str, Any]:
    """处理不需要行动的任务"""
    
    console.print("\n[blue]这个任务不需要立即行动。让我们确定如何处理：[/blue]")
    
    options = [
        "参考资料 - 将来可能需要的信息",
        "将来/也许 - 可能在未来某个时候要做",
        "垃圾 - 不再需要，可以删除"
    ]
    
    choice = _show_choice_menu(options, "选择处理方式:")
    
    if choice == 1:  # 参考资料
        task.update_status(TaskStatus.REFERENCE)
        task.add_note("理清时标记为参考资料")
        agent.storage.save_task(task)
        
        console.print("[blue]📚 任务已移至参考资料")
        return {"action": "clarified", "status": TaskStatus.REFERENCE}
    
    elif choice == 2:  # 将来/也许
        task.update_status(TaskStatus.SOMEDAY_MAYBE)
        task.add_note("理清时标记为将来/也许")
        agent.storage.save_task(task)
        
        console.print("[cyan]🔮 任务已移至将来/也许清单")
        return {"action": "clarified", "status": TaskStatus.SOMEDAY_MAYBE}
    
    elif choice == 3:  # 删除
        task.update_status(TaskStatus.DELETED)
        task.add_note("理清时删除")
        agent.storage.save_task(task)
        
        console.print("[red]🗑️ 任务已删除")
        return {"action": "clarified", "status": TaskStatus.DELETED}
    
    return {"action": "skip"}


def _handle_project_task(task: Task, agent: GTDAgent, outcome: str, next_action: str) -> Dict[str, Any]:
    """处理项目任务"""
    
    console.print("\n[green]📋 这是一个项目！[/green]")
    
    # 更新任务为项目
    task.update_status(TaskStatus.PROJECT)
    task.description = outcome
    task.add_note(f"理清时确定为项目，期望结果：{outcome}")
    
    # 设置项目属性
    task = _set_task_attributes(task, agent)
    
    # 保存项目
    agent.storage.save_task(task)
    
    # 创建第一个下一步行动
    if Confirm.ask("是否立即创建第一个下一步行动？", default=True):
        _create_next_action_for_project(task, next_action, agent)
    
    console.print(f"[green]✅ 项目已创建: {task.title}[/green]")
    return {"action": "clarified", "status": TaskStatus.PROJECT}


def _handle_single_action_task(task: Task, agent: GTDAgent, next_action: str) -> Dict[str, Any]:
    """处理单一行动任务"""
    
    console.print("\n[blue]⚡ 这是一个单一的下一步行动[/blue]")
    
    # 更新任务
    task.update_status(TaskStatus.NEXT_ACTION)
    if next_action != task.title:
        task.title = next_action
    task.add_note("理清时确定为下一步行动")
    
    # 设置任务属性
    task = _set_task_attributes(task, agent)
    
    # 保存任务
    agent.storage.save_task(task)
    
    console.print(f"[blue]✅ 下一步行动已创建: {task.title}[/blue]")
    return {"action": "clarified", "status": TaskStatus.NEXT_ACTION}


def _set_task_attributes(task: Task, agent: GTDAgent) -> Task:
    """设置任务属性（情境、优先级、时间等）
    
    集成US-008智能分类学习功能
    """
    
    console.print("\n[yellow]📝 让我们为任务设置一些属性...[/yellow]")
    
    # 设置情境
    context_options = [
        f"{TaskContext.COMPUTER.value} - 需要电脑",
        f"{TaskContext.PHONE.value} - 需要打电话",
        f"{TaskContext.ERRANDS.value} - 外出办事",
        f"{TaskContext.HOME.value} - 在家",
        f"{TaskContext.OFFICE.value} - 在办公室",
        f"{TaskContext.ONLINE.value} - 需要网络",
        f"{TaskContext.READING.value} - 阅读相关",
        f"{TaskContext.MEETING.value} - 会议相关",
        f"{TaskContext.FOCUS.value} - 需要专注",
        "跳过 - 暂不设置情境"
    ]
    
    # 如果有智能建议，提供快捷选项
    if task.suggested_context:
        console.print(f"[green]💡 建议情境: {task.suggested_context.value}[/green]")
        if Confirm.ask("使用建议的情境？", default=True):
            task.context = task.suggested_context
        else:
            choice = _show_choice_menu(context_options, "选择执行情境:")
            if choice <= len(TaskContext):
                contexts = list(TaskContext)
                task.context = contexts[choice - 1]
    else:
        choice = _show_choice_menu(context_options, "选择执行情境:")
        if choice <= len(TaskContext):
            contexts = list(TaskContext)
            task.context = contexts[choice - 1]
    
    # 设置优先级
    if task.suggested_priority:
        console.print(f"[green]💡 建议优先级: {task.suggested_priority.value}[/green]")
        if Confirm.ask("使用建议的优先级？", default=True):
            task.priority = task.suggested_priority
    else:
        priority_choice = _show_choice_menu([
            "🔥 高优先级 - 重要且紧急",
            "📋 中优先级 - 常规任务", 
            "📝 低优先级 - 不紧急"
        ], "选择优先级:")
        
        priorities = [TaskPriority.HIGH, TaskPriority.MEDIUM, TaskPriority.LOW]
        task.priority = priorities[priority_choice - 1]
    
    # 设置预估时间
    if Confirm.ask("是否设置预估完成时间？", default=False):
        try:
            duration = IntPrompt.ask("预估时长（分钟）", default=30)
            if duration > 0:
                task.estimated_duration = duration
        except Exception:
            pass
    
    # 设置精力需求
    if Confirm.ask("是否设置精力需求？", default=False):
        energy_choice = _show_choice_menu([
            "⚡ 高精力 - 需要专注和创造力",
            "🔋 中精力 - 常规工作",
            "🪫 低精力 - 简单重复任务"
        ], "选择精力需求:")
        
        energies = [EnergyLevel.HIGH, EnergyLevel.MEDIUM, EnergyLevel.LOW]
        task.energy_required = energies[energy_choice - 1]
    
    # 记录用户决策用于智能学习（US-008）
    user_decision = {
        'context': task.context,
        'priority': task.priority,
        'energy_required': task.energy_required,
        'status': task.status
    }
    
    # 让系统从用户决策中学习
    agent.learn_from_classification(task, user_decision)
    
    return task


def _create_next_action_for_project(project_task: Task, next_action: str, agent: GTDAgent) -> None:
    """为项目创建第一个下一步行动"""
    
    from pm.models.task import Task
    
    # 创建下一步行动任务
    action_task = Task(
        title=next_action,
        status=TaskStatus.NEXT_ACTION,
        project_id=project_task.id,
        project_name=project_task.title,
        context=project_task.context,
        priority=project_task.priority,
        energy_required=project_task.energy_required
    )
    
    action_task.add_note(f"项目 {project_task.title} 的第一个行动")
    
    # 保存行动
    agent.storage.save_task(action_task)
    
    console.print(f"[green]✅ 已为项目创建下一步行动: {next_action}[/green]")


def _show_choice_menu(options: List[str], title: str) -> int:
    """显示选择菜单"""
    
    console.print(f"\n[bold]{title}[/bold]")
    
    for i, option in enumerate(options, 1):
        console.print(f"  {i}. {option}")
    
    while True:
        try:
            choice = IntPrompt.ask("请选择", default=1)
            if 1 <= choice <= len(options):
                return choice
            else:
                console.print(f"[red]请输入 1-{len(options)} 之间的数字")
        except Exception:
            console.print("[red]请输入有效数字")


def _show_clarify_summary(clarified: int, next_actions: int, projects: int, 
                         someday: int, reference: int, deleted: int) -> None:
    """显示理清结果总结"""
    
    console.print("\n" + "="*60)
    console.print(Panel(
        f"[bold green]🎉 理清流程完成！\n\n"
        f"[cyan]总计处理: {clarified} 个任务[/cyan]\n\n"
        f"分类结果:\n"
        f"• ⚡ 下一步行动: {next_actions} 个\n"
        f"• 📋 项目: {projects} 个\n"
        f"• 🔮 将来/也许: {someday} 个\n"
        f"• 📚 参考资料: {reference} 个\n"
        f"• 🗑️ 已删除: {deleted} 个",
        title="理清完成",
        border_style="green"
    ))
    
    # 给出后续建议
    suggestions = []
    
    if next_actions > 0:
        suggestions.append("• [cyan]pm next[/cyan] - 查看下一步行动清单")
    
    if projects > 0:
        suggestions.append("• [cyan]pm projects overview[/cyan] - 查看项目概览")
    
    suggestions.append("• [cyan]pm capture \"新想法\"[/cyan] - 继续捕获新任务")
    
    if suggestions:
        console.print(Panel(
            "[bold blue]💡 建议下一步操作：\n\n" + "\n".join(suggestions),
            title="后续操作",
            border_style="blue"
        ))