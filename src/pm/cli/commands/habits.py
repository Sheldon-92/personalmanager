"""习惯管理CLI命令 - Sprint 13

这个CLI接口是对AI可调用工具函数的薄包装层
展示了新架构模式：CLI -> 工具函数 -> 业务逻辑
"""

import typer
from datetime import date
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

from pm.core.config import PMConfig
from pm.tools.habit_tools import (
    create_habit,
    record_habit_completion,
    get_habit_status,
    get_today_habit_plan,
    analyze_habit_trends,
    suggest_habit_improvements
)

console = Console()


def create_new_habit(
    name: str = typer.Argument(..., help="习惯名称"),
    category: str = typer.Option("other", "--category", "-c", help="习惯分类"),
    frequency: str = typer.Option("daily", "--frequency", "-f", help="执行频率"),
    difficulty: str = typer.Option("easy", "--difficulty", "-d", help="难度级别"),
    description: Optional[str] = typer.Option(None, "--desc", help="习惯描述"),
    cue: Optional[str] = typer.Option(None, "--cue", help="触发提示"),
    routine: Optional[str] = typer.Option(None, "--routine", help="具体行为"),
    reward: Optional[str] = typer.Option(None, "--reward", help="奖励机制"),
    duration: Optional[int] = typer.Option(None, "--duration", help="目标时长(分钟)"),
    reminder: Optional[str] = typer.Option(None, "--reminder", help="提醒时间 HH:MM")
) -> None:
    """创建新的习惯"""
    
    console.print("🌱 创建新习惯...", style="bold green")
    
    # 调用AI可调用工具函数
    success, message, habit_info = create_habit(
        name=name,
        category=category,
        frequency=frequency,
        difficulty=difficulty,
        description=description,
        cue=cue,
        routine=routine,
        reward=reward,
        target_duration=duration,
        reminder_time=reminder
    )
    
    if success:
        console.print(f"✅ {message}", style="bold green")
        
        if habit_info:
            # 显示习惯详情
            details_table = Table(show_header=False, box=box.SIMPLE)
            details_table.add_column("属性", style="cyan")
            details_table.add_column("值", style="white")
            
            details_table.add_row("习惯ID", habit_info["id"][:8] + "...")
            details_table.add_row("分类", habit_info["category"])
            details_table.add_row("频率", habit_info["frequency"])
            details_table.add_row("难度", habit_info["difficulty"])
            
            console.print("\n📋 习惯详情:")
            console.print(details_table)
            
            # 显示《原子习惯》建议
            tips = [
                "💡 让习惯显而易见：设置明确的提示和环境",
                "🎯 让习惯有吸引力：与你的身份认同联系起来", 
                "⚡ 让习惯简便易行：从2分钟版本开始",
                "🎉 让习惯令人愉悦：设计即时奖励机制"
            ]
            
            console.print(f"\n🔥 原子习惯建议:")
            for tip in tips:
                console.print(f"   {tip}")
    else:
        console.print(f"❌ {message}", style="bold red")


def track_habit(
    name: str = typer.Argument(..., help="习惯名称"),
    completed: bool = typer.Option(True, "--done/--skip", help="是否完成"),
    notes: Optional[str] = typer.Option(None, "--notes", "-n", help="备注"),
    quality: Optional[int] = typer.Option(None, "--quality", "-q", help="质量评分(1-5)"),
    record_date: Optional[str] = typer.Option(None, "--date", help="记录日期(YYYY-MM-DD)")
) -> None:
    """记录习惯完成情况"""
    
    action = "完成" if completed else "跳过"
    console.print(f"📝 记录习惯{action}情况...", style="bold blue")
    
    # 调用AI可调用工具函数
    success, message, record_info = record_habit_completion(
        habit_name=name,
        completed=completed,
        notes=notes,
        quality_score=quality,
        record_date=record_date
    )
    
    if success:
        console.print(f"✅ {message}", style="bold green")
        
        if record_info:
            # 显示更新后的统计
            stats_table = Table(show_header=False, box=box.ROUNDED)
            stats_table.add_column("统计项", style="cyan")
            stats_table.add_column("数值", style="white")
            
            stats_table.add_row("当前连续", f"{record_info['current_streak']} 天")
            stats_table.add_row("总完成次数", str(record_info['total_completions']))
            if record_info.get('quality_score'):
                stats_table.add_row("本次质量", f"{record_info['quality_score']}/5 ⭐")
            
            console.print("\n📊 习惯统计:")
            console.print(stats_table)
            
            # 连续打卡鼓励
            streak = record_info['current_streak']
            if completed and streak > 0:
                if streak >= 21:
                    console.print("\n🔥 太棒了！21天连续打卡，习惯正在巩固！", style="bold yellow")
                elif streak >= 7:
                    console.print("\n⭐ 很好！一周连续打卡，继续保持！", style="bold yellow")
                elif streak >= 3:
                    console.print("\n🌱 不错！连续3天，好习惯正在形成！", style="bold yellow")
    else:
        console.print(f"❌ {message}", style="bold red")


def show_habit_status(
    name: Optional[str] = typer.Argument(None, help="习惯名称（可选）")
) -> None:
    """显示习惯状态"""
    
    if name:
        console.print(f"📊 获取习惯 '{name}' 的状态信息...", style="bold blue")
    else:
        console.print("📊 获取习惯管理系统概览...", style="bold blue")
    
    # 调用AI可调用工具函数
    success, message, status_info = get_habit_status(habit_name=name)
    
    if not success:
        console.print(f"❌ {message}", style="bold red")
        return
    
    if name:
        # 显示特定习惯的详细状态
        habit_data = status_info["habit"]
        
        # 基本信息面板
        basic_info = Table(show_header=False, box=box.SIMPLE)
        basic_info.add_column("属性", style="cyan")
        basic_info.add_column("值", style="white")
        
        basic_info.add_row("习惯名称", habit_data["name"])
        basic_info.add_row("分类", habit_data["category"])
        basic_info.add_row("难度", habit_data["difficulty"])
        basic_info.add_row("活跃天数", f"{habit_data['active_days']} 天")
        
        console.print(Panel(basic_info, title="📋 基本信息", border_style="blue"))
        
        # 表现统计面板
        stats_table = Table(show_header=False, box=box.SIMPLE)
        stats_table.add_column("指标", style="cyan")
        stats_table.add_column("数值", style="white")
        
        stats_table.add_row("当前连续", f"{habit_data['current_streak']} 天")
        stats_table.add_row("历史最长", f"{habit_data['longest_streak']} 天")
        stats_table.add_row("总完成次数", str(habit_data['total_completions']))
        stats_table.add_row("整体成功率", f"{habit_data['success_rate']:.1f}%")
        stats_table.add_row("7天完成率", f"{habit_data['completion_rate_7d']:.1f}%")
        stats_table.add_row("30天完成率", f"{habit_data['completion_rate_30d']:.1f}%")
        
        # 今日状态
        today_status = "✅ 已完成" if habit_data['completed_today'] else ("⏰ 待完成" if habit_data['is_due_today'] else "💤 今日无需执行")
        stats_table.add_row("今日状态", today_status)
        
        console.print(Panel(stats_table, title="📊 表现统计", border_style="green"))
        
        # 近期记录
        if status_info["recent_records"]:
            records_table = Table(box=box.SIMPLE)
            records_table.add_column("日期", style="cyan")
            records_table.add_column("完成", style="white")
            records_table.add_column("质量", style="yellow")
            records_table.add_column("备注", style="white")
            
            for record in status_info["recent_records"]:
                completion = "✅" if record["completed"] else "❌"
                quality = f"{record['quality_score']}/5" if record["quality_score"] else "-"
                notes = record["notes"][:30] + "..." if record["notes"] and len(record["notes"]) > 30 else (record["notes"] or "-")
                
                records_table.add_row(
                    record["date"],
                    completion,
                    quality,
                    notes
                )
            
            console.print(Panel(records_table, title="📅 近期记录", border_style="yellow"))
    
    else:
        # 显示系统概览
        stats = status_info["statistics"]
        
        # 整体统计
        overview_table = Table(show_header=False, box=box.ROUNDED)
        overview_table.add_column("指标", style="cyan")
        overview_table.add_column("数值", style="white")
        
        overview_table.add_row("总习惯数", str(stats["total_habits"]))
        overview_table.add_row("活跃习惯", str(stats["active_habits"]))
        overview_table.add_row("已归档", str(stats["archived_habits"]))
        overview_table.add_row("今日应执行", str(stats["due_today"]))
        overview_table.add_row("今日已完成", str(stats["completed_today"]))
        overview_table.add_row("今日完成率", f"{stats['completion_rate_today']:.1f}%")
        overview_table.add_row("平均连续", f"{stats['average_current_streak']} 天")
        overview_table.add_row("最长连续", f"{stats['longest_streak']} 天")
        
        console.print(Panel(overview_table, title="🏠 习惯管理系统概览", border_style="blue"))
        
        # 分类分布
        if stats.get("category_distribution"):
            category_table = Table(box=box.SIMPLE)
            category_table.add_column("分类", style="cyan")
            category_table.add_column("数量", style="white")
            
            for category, count in stats["category_distribution"].items():
                category_table.add_row(category, str(count))
            
            console.print(Panel(category_table, title="📂 分类分布", border_style="green"))
        
        # 今日待办
        if status_info.get("pending_habits"):
            console.print(f"\n⏰ 今日待完成习惯 ({status_info['pending_count']} 个):")
            for habit_name in status_info["pending_habits"]:
                console.print(f"   • {habit_name}")


def show_today_plan() -> None:
    """显示今日习惯计划"""
    
    console.print("📅 获取今日习惯计划...", style="bold blue")
    
    # 调用AI可调用工具函数
    success, message, plan_info = get_today_habit_plan()
    
    if not success:
        console.print(f"❌ {message}", style="bold red")
        return
    
    console.print(f"✅ {message}", style="bold green")
    
    if plan_info:
        # 今日概览
        overview_text = f"""
📊 完成进度: {plan_info['completed']}/{plan_info['total_due']} ({plan_info['completion_rate']:.0f}%)
📅 日期: {plan_info['date']}
        """
        console.print(Panel(overview_text.strip(), title="📋 今日概览", border_style="blue"))
        
        # 已完成习惯
        if plan_info["completed_habits"]:
            completed_table = Table(box=box.SIMPLE)
            completed_table.add_column("习惯", style="green")
            completed_table.add_column("分类", style="cyan")
            completed_table.add_column("连续", style="yellow")
            completed_table.add_column("难度", style="white")
            
            for habit in plan_info["completed_habits"]:
                completed_table.add_row(
                    f"✅ {habit['name']}",
                    habit["category"],
                    f"{habit['current_streak']}天",
                    habit["difficulty"]
                )
            
            console.print(Panel(completed_table, title="🎉 已完成习惯", border_style="green"))
        
        # 待完成习惯
        if plan_info["pending_habits"]:
            pending_table = Table(box=box.SIMPLE)
            pending_table.add_column("习惯", style="yellow")
            pending_table.add_column("分类", style="cyan")
            pending_table.add_column("连续", style="white")
            pending_table.add_column("时长", style="white")
            pending_table.add_column("提示", style="white")
            
            for habit in plan_info["pending_habits"]:
                duration = f"{habit.get('target_duration', 0)}分钟" if habit.get('target_duration') else "-"
                cue = habit.get('cue', '-')[:20] + "..." if habit.get('cue') and len(habit.get('cue', '')) > 20 else habit.get('cue', '-')
                
                pending_table.add_row(
                    f"⏰ {habit['name']}",
                    habit["category"],
                    f"{habit['current_streak']}天",
                    duration,
                    cue
                )
            
            console.print(Panel(pending_table, title="📝 待完成习惯", border_style="yellow"))
            
            # 执行建议
            console.print("\n💡 执行建议:")
            console.print("   • 从最简单的习惯开始（2分钟法则）")
            console.print("   • 利用现有的提示和环境")
            console.print("   • 完成后立即给自己奖励")
        
        if not plan_info["completed_habits"] and not plan_info["pending_habits"]:
            console.print("\n🌸 今日没有安排习惯，好好休息！", style="bold green")


def analyze_trends(
    name: Optional[str] = typer.Argument(None, help="习惯名称（可选）"),
    days: int = typer.Option(30, "--days", "-d", help="分析天数")
) -> None:
    """分析习惯趋势"""
    
    if name:
        console.print(f"📈 分析习惯 '{name}' 的趋势（过去{days}天）...", style="bold blue")
    else:
        console.print(f"📈 分析整体习惯趋势（过去{days}天）...", style="bold blue")
    
    # 调用AI可调用工具函数
    success, message, analysis = analyze_habit_trends(habit_name=name, days=days)
    
    if not success:
        console.print(f"❌ {message}", style="bold red")
        return
    
    console.print(f"✅ {message}", style="bold green")
    
    if not analysis:
        return
    
    if name:
        # 单个习惯的趋势分析
        trend_table = Table(show_header=False, box=box.ROUNDED)
        trend_table.add_column("指标", style="cyan")
        trend_table.add_column("数值", style="white")
        
        trend_table.add_row("分析周期", analysis["analysis_period"])
        trend_table.add_row("完成率", f"{analysis['completion_rate']}%")
        trend_table.add_row("当前连续", f"{analysis['streak_analysis']['current_streak']} 天")
        trend_table.add_row("最长连续", f"{analysis['streak_analysis']['longest_streak']} 天")
        trend_table.add_row("总完成次数", str(analysis['streak_analysis']['total_completions']))
        trend_table.add_row("质量趋势", analysis["quality_trend"])
        trend_table.add_row("习惯成熟度", analysis["habit_maturity"])
        trend_table.add_row("活跃天数", f"{analysis['active_days']} 天")
        
        console.print(Panel(trend_table, title=f"📊 {analysis['habit_name']} 趋势分析", border_style="blue"))
    
    else:
        # 整体趋势分析
        overview_table = Table(show_header=False, box=box.ROUNDED)
        overview_table.add_column("指标", style="cyan")
        overview_table.add_column("数值", style="white")
        
        overview_table.add_row("分析周期", analysis["analysis_period"])
        overview_table.add_row("习惯总数", str(analysis["total_habits"]))
        overview_table.add_row("整体完成率", f"{analysis['overall_completion_rate']}%")
        overview_table.add_row("系统健康度", analysis["system_health"])
        
        console.print(Panel(overview_table, title="🏠 整体趋势分析", border_style="blue"))
        
        # 分类表现
        if analysis.get("category_breakdown"):
            category_table = Table(box=box.SIMPLE)
            category_table.add_column("分类", style="cyan")
            category_table.add_column("习惯数", style="white")
            category_table.add_column("平均完成率", style="white")
            
            for category, stats in analysis["category_breakdown"].items():
                category_table.add_row(
                    category,
                    str(stats["count"]),
                    f"{stats['avg_completion']}%"
                )
            
            console.print(Panel(category_table, title="📂 分类表现", border_style="green"))
        
        # 表现排行
        if analysis.get("top_performing"):
            console.print("\n🏆 表现最佳:")
            for habit in analysis["top_performing"]:
                console.print(f"   🥇 {habit['name']}: {habit['rate']:.1f}%")
        
        if analysis.get("needs_attention"):
            console.print("\n⚠️  需要关注:")
            for habit in analysis["needs_attention"]:
                console.print(f"   🔴 {habit['name']}: {habit['rate']:.1f}%")


def get_suggestions(
    name: str = typer.Argument(..., help="习惯名称")
) -> None:
    """获取习惯改进建议"""
    
    console.print(f"💡 为习惯 '{name}' 生成改进建议...", style="bold blue")
    
    # 调用AI可调用工具函数
    success, message, suggestions = suggest_habit_improvements(habit_name=name)
    
    if not success:
        console.print(f"❌ {message}", style="bold red")
        return
    
    console.print(f"✅ {message}", style="bold green")
    
    if not suggestions:
        return
    
    # 当前表现
    perf = suggestions["current_performance"]
    perf_table = Table(show_header=False, box=box.SIMPLE)
    perf_table.add_column("指标", style="cyan")
    perf_table.add_column("数值", style="white")
    
    perf_table.add_row("完成率", f"{perf['completion_rate']}%")
    perf_table.add_row("当前连续", f"{perf['current_streak']} 天")
    perf_table.add_row("成熟度", perf["maturity"])
    
    console.print(Panel(perf_table, title=f"📊 {suggestions['habit_name']} 当前表现", border_style="blue"))
    
    # 改进建议
    if suggestions.get("suggestions"):
        console.print("\n💡 改进建议:", style="bold yellow")
        
        for i, suggestion in enumerate(suggestions["suggestions"], 1):
            suggestion_text = f"""
🔹 {suggestion['title']}
   {suggestion['description']}
            """
            console.print(Panel(suggestion_text.strip(), title=f"建议 {i}", border_style="yellow"))
    
    # 原子习惯原则
    principle = suggestions.get("atomic_habits_principle", "")
    if principle:
        console.print(f"\n📚 原子习惯核心原则:", style="bold green")
        console.print(f"   {principle}", style="italic green")