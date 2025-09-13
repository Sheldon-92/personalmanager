"""Best practices guide and interactive tutorials for PersonalManager."""

from typing import Optional, List, Dict
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.prompt import Prompt, Confirm
from rich.markdown import Markdown

from pm.tools.guide_tools import (
    get_guide_overview,
    get_gtd_workflow_guide,
    get_project_setup_guide, 
    get_common_scenarios_guide,
    get_interactive_tutorial_info,
    search_best_practices,
    get_available_guide_topics,
    validate_guide_category
)

console = Console()


def show_best_practices(category: Optional[str] = None) -> None:
    """显示最佳实践指导
    
    根据US-018验收标准实现：
    - 提供GTD工作流程指导
    - 提供项目设置最佳实践
    - 提供常见使用场景示例
    - 集成交互式教程
    """
    
    if category is None:
        _show_practice_menu()
    elif category == "gtd":
        _show_gtd_workflow()
    elif category == "projects":
        _show_project_setup()
    elif category == "scenarios":
        _show_common_scenarios()
    elif category == "interactive":
        _run_interactive_tutorial()
    else:
        # 验证类别
        success, message, data = validate_guide_category(category)
        if success and data and data['is_valid']:
            console.print(f"[red]功能尚未实现: {category}")
        else:
            console.print(f"[red]未找到指导类别: {category}")
            if data and data['valid_categories']:
                console.print(f"[yellow]可用类别: {', '.join(data['valid_categories'])}")


def _show_practice_menu() -> None:
    """显示最佳实践菜单"""
    
    success, message, data = get_guide_overview()
    
    if not success:
        console.print(Panel(
            f"[red]❌ {message}",
            title="获取指导概览失败",
            border_style="red"
        ))
        return
        
    if not data:
        console.print(Panel(
            "[yellow]无法获取指导概览信息",
            title="⚠️ 信息不可用",
            border_style="yellow"
        ))
        return
        
    console.print(Panel(
        f"[bold blue]{data['overview_title']}\n\n"
        f"[green]{data['overview_description']}",
        title="📚 最佳实践",
        border_style="blue"
    ))
    
    # 创建指导类别表格
    table = Table(title="可用指导类别")
    table.add_column("类别", style="cyan", min_width=15)
    table.add_column("描述", style="white")
    table.add_column("命令", style="green")
    
    for category in data['categories']:
        table.add_row(category['name'], category['description'], category['command'])
    
    console.print(table)
    
    # 显示使用提示
    tips_text = "\n".join([f"• {tip}" for tip in data['usage_tips']])
    console.print(Panel(
        f"[yellow]💡 使用提示：\n\n{tips_text}",
        title="使用说明",
        border_style="yellow"
    ))


def _show_gtd_workflow() -> None:
    """显示GTD工作流程指导"""
    
    success, message, data = get_gtd_workflow_guide()
    
    if not success:
        console.print(Panel(
            f"[red]❌ {message}",
            title="获取GTD工作流程失败",
            border_style="red"
        ))
        return
        
    if not data:
        console.print(Panel(
            "[yellow]无法获取GTD工作流程信息",
            title="⚠️ 信息不可用",
            border_style="yellow"
        ))
        return
        
    console.print(Panel(
        f"[bold]{data['title']}[/bold]\n\n{data['description']}",
        title="🔄 GTD工作流程",
        border_style="green"
    ))
    
    for i, step in enumerate(data["steps"], 1):
        console.print(f"\n[bold cyan]{i}. {step['name']}[/bold cyan]")
        console.print(f"   {step['description']}")
        console.print(f"   [dim]命令: [green]{step['command']}[/green]")
        
        console.print(f"   [bold]实践技巧:")
        for tip in step["tips"]:
            console.print(f"   • {tip}")
    
    # 显示核心原则
    principles_text = ""
    for i, principle in enumerate(data["core_principles"], 1):
        principles_text += f"{i}. [bold]{principle['name']}[/bold] - {principle['description']}\n"
    
    console.print(Panel(
        f"[green]🎯 GTD工作流程核心原则：\n\n{principles_text.strip()}",
        title="核心原则",
        border_style="green"
    ))


def _show_project_setup() -> None:
    """显示项目设置最佳实践"""
    
    success, message, data = get_project_setup_guide()
    
    if not success:
        console.print(Panel(
            f"[red]❌ {message}",
            title="获取项目设置指导失败",
            border_style="red"
        ))
        return
        
    if not data:
        console.print(Panel(
            "[yellow]无法获取项目设置指导信息",
            title="⚠️ 信息不可用",
            border_style="yellow"
        ))
        return
        
    console.print(Panel(
        f"[bold]{data['title']}[/bold]\n\n{data['description']}",
        title="📋 项目管理",
        border_style="blue"
    ))
    
    for guideline in data["guidelines"]:
        console.print(f"\n[bold magenta]{guideline['category']}[/bold magenta]")
        for practice in guideline["practices"]:
            console.print(f"   • {practice}")


def _show_common_scenarios() -> None:
    """显示常见使用场景"""
    
    success, message, data = get_common_scenarios_guide()
    
    if not success:
        console.print(Panel(
            f"[red]❌ {message}",
            title="获取使用场景失败",
            border_style="red"
        ))
        return
        
    if not data:
        console.print(Panel(
            "[yellow]无法获取使用场景信息",
            title="⚠️ 信息不可用",
            border_style="yellow"
        ))
        return
        
    console.print(Panel(
        f"[bold]{data['title']}[/bold]",
        title="💼 使用场景",
        border_style="yellow"
    ))
    
    for scenario in data["scenarios"]:
        console.print(f"\n[bold cyan]{scenario['name']}[/bold cyan]")
        console.print(f"   {scenario['description']}")
        console.print(f"   [bold]推荐流程:")
        
        for i, step in enumerate(scenario["workflow"], 1):
            console.print(f"   {i}. {step}")


def _run_interactive_tutorial() -> None:
    """运行交互式教程"""
    
    success, message, data = get_interactive_tutorial_info()
    
    if not success:
        console.print(Panel(
            f"[red]❌ {message}",
            title="获取教程信息失败",
            border_style="red"
        ))
        return
        
    if not data:
        console.print(Panel(
            "[yellow]无法获取教程信息",
            title="⚠️ 信息不可用",
            border_style="yellow"
        ))
        return
        
    console.print(Panel(
        f"[bold blue]{data['tutorial_title']}\n\n"
        f"{data['tutorial_description']}",
        title="交互式学习",
        border_style="blue"
    ))
    
    # 显示教程概览
    console.print(f"\n[bold yellow]📋 教程概览（共{data['total_steps']}步）：[/bold yellow]")
    for step in data['steps']:
        console.print(f"   {step['step']}. {step['title']} - {step['description']}")
    
    current_step = 0
    while current_step < len(data['steps']):
        step_data = data['steps'][current_step]
        
        console.print(f"\n[bold green]第{step_data['step']}步：{step_data['title']}[/bold green]")
        console.print(f"{step_data['description']}")
        
        if Confirm.ask("开始这一步的学习？", default=True):
            _show_tutorial_step_content(step_data)
            console.print("[green]✅ 完成！")
        
        if current_step < len(data['steps']) - 1:
            if not Confirm.ask("继续下一步？", default=True):
                break
        
        current_step += 1
    
    # 显示完成信息
    benefits_text = "\n".join([f"• {benefit}" for benefit in data['completion_benefits']])
    console.print(Panel(
        f"[green]🎉 恭喜！您已完成PersonalManager交互式教程！\n\n"
        f"现在您已经：\n{benefits_text}\n\n"
        f"可以开始使用：\n"
        f"• [cyan]pm capture[/cyan] - 捕获新想法\n"
        f"• [cyan]pm today[/cyan] - 获取每日建议\n"
        f"• [cyan]pm projects overview[/cyan] - 管理项目\n\n"
        f"记住：最好的系统是您实际使用的系统！",
        title="🎓 教程完成",
        border_style="green"
    ))


def _show_tutorial_step_content(step_data: Dict) -> None:
    """显示教程步骤内容"""
    
    content = step_data.get('content', {})
    
    if step_data['step'] == 1:  # GTD基础概念
        console.print("\n[bold]GTD的5个核心步骤：[/bold]")
        for i, concept in enumerate(content.get('concepts', []), 1):
            console.print(f"{i}. [cyan]{concept}[/cyan]")
        
        console.print("\n[bold yellow]核心理念：[/bold yellow]")
        for principle in content.get('principles', []):
            console.print(f"• {principle}")
            
    elif step_data['step'] == 2:  # 任务捕获实践
        console.print("\n[bold]任务捕获最佳实践：[/bold]")
        
        console.print("\n[cyan]好的捕获示例：[/cyan]")
        for example in content.get('good_examples', []):
            console.print(f"• {example}")
            
        console.print("\n[red]避免的捕获方式：[/red]")
        for example in content.get('bad_examples', []):
            console.print(f"• {example}")
            
        console.print("\n[bold yellow]捕获技巧：[/bold yellow]")
        for tip in content.get('tips', []):
            console.print(f"• {tip}")
            
    elif step_data['step'] == 3:  # 项目管理实践
        console.print("\n[bold]项目设置实践：[/bold]")
        
        console.print("\n[cyan]1. 定义项目结果：[/cyan]")
        for item in content.get('project_definition', []):
            console.print(f"• {item}")
            
        console.print("\n[cyan]2. 创建PROJECT_STATUS.md：[/cyan]")
        for item in content.get('status_file', []):
            console.print(f"• {item}")
            
        console.print("\n[cyan]3. 项目分解：[/cyan]")
        for item in content.get('decomposition', []):
            console.print(f"• {item}")
            
    elif step_data['step'] == 4:  # 每日工作流
        console.print("\n[bold]建议的每日工作流：[/bold]")
        
        console.print("\n[cyan]🌅 晨间（5-10分钟）：[/cyan]")
        for item in content.get('morning_routine', []):
            console.print(f"• {item}")
            
        console.print("\n[cyan]⏰ 工作时段：[/cyan]")
        for item in content.get('work_time', []):
            console.print(f"• {item}")
            
        console.print("\n[cyan]🌆 晚间（5分钟）：[/cyan]")
        for item in content.get('evening_routine', []):
            console.print(f"• {item}")
            
        console.print(f"\n[bold yellow]成功的关键：[/bold yellow]")
        console.print(content.get('key_success_factor', ''))


def _tutorial_gtd_basics() -> None:
    """GTD基础概念教程"""
    
    console.print("""
[bold]GTD的5个核心步骤：[/bold]

1. [cyan]📥 收集（Capture）[/cyan]：将所有想法、任务、承诺记录下来
2. [cyan]🤔 理清（Clarify）[/cyan]：确定每个条目的含义和所需行动
3. [cyan]📋 整理（Organize）[/cyan]：将条目分类到合适的清单中
4. [cyan]🔄 回顾（Review）[/cyan]：定期检查和更新整个系统
5. [cyan]⚡ 执行（Engage）[/cyan]：根据情境和优先级选择行动

[bold yellow]核心理念：[/bold yellow]
• 大脑用来思考，不是用来记忆
• 所有承诺都要有可信的外部系统来跟踪
• 定期回顾保持系统的新鲜度
""")


def _tutorial_capture_practice() -> None:
    """任务捕获实践教程"""
    
    console.print("""
[bold]任务捕获最佳实践：[/bold]

[cyan]好的捕获示例：[/cyan]
• "给张总发送项目进度报告"
• "研究新的项目管理工具选项"
• "预约下周的医生检查"

[red]避免的捕获方式：[/red]
• "处理邮件"（太模糊）
• "改善工作效率"（太宽泛）
• "明天的会议"（缺乏行动）

[bold yellow]捕获技巧：[/bold yellow]
• 使用动词开头描述行动
• 包含足够的上下文信息
• 一次只捕获一个想法
• 不要在捕获时判断重要性
""")


def _tutorial_project_practice() -> None:
    """项目管理实践教程"""
    
    console.print("""
[bold]项目设置实践：[/bold]

[cyan]1. 定义项目结果：[/cyan]
• 具体、可测量的成果
• 明确的成功标准
• 现实的时间框架

[cyan]2. 创建PROJECT_STATUS.md：[/cyan]
• 项目进度百分比
• 当前健康状态
• 主要风险和问题
• 下一步关键行动

[cyan]3. 项目分解：[/cyan]
• 将大项目拆分为子项目
• 每个子项目有明确的交付物
• 识别关键路径和依赖关系
""")


def _tutorial_daily_workflow() -> None:
    """每日工作流教程"""
    
    console.print("""
[bold]建议的每日工作流：[/bold]

[cyan]🌅 晨间（5-10分钟）：[/cyan]
• 查看今日日程和任务
• 确定3个最重要任务（MIT）
• 检查项目状态更新

[cyan]⏰ 工作时段：[/cyan]
• 根据精力水平选择任务
• 完成任务后及时标记
• 新想法立即捕获

[cyan]🌆 晚间（5分钟）：[/cyan]
• 回顾今日完成情况
• 捕获明日待办事项
• 更新项目进度

[bold yellow]成功的关键：[/bold yellow]
保持系统简单，专注执行而不是完善系统！
""")


def get_guide_topics() -> List[str]:
    """获取可用的指导主题列表（供其他模块使用）"""
    success, message, data = get_available_guide_topics()
    if success and data:
        return data['topics']
    return ["gtd", "projects", "scenarios", "interactive"]  # 备用列表


def search_guide_content(query: str) -> List[Dict]:
    """搜索最佳实践内容（供其他模块使用）"""
    success, message, data = search_best_practices(query)
    if success and data:
        return data['results']
    return []