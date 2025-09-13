"""习惯管理AI可调用工具函数 - Sprint 13架构转型示范

这些函数被设计为独立的、可供AI直接调用的工具函数
不依赖CLI框架，可以被其他Python代码或AI代理直接调用
"""

import structlog
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple

from pm.core.config import PMConfig
from pm.storage.habit_storage import HabitStorage
from pm.models.habit import (
    Habit, HabitRecord, HabitCategory, HabitFrequency, HabitDifficulty
)

logger = structlog.get_logger()


# ========== 核心工具函数 ==========

def create_habit(
    name: str,
    category: str = "other",
    frequency: str = "daily",
    difficulty: str = "easy",
    description: Optional[str] = None,
    cue: Optional[str] = None,
    routine: Optional[str] = None,
    reward: Optional[str] = None,
    target_duration: Optional[int] = None,
    reminder_time: Optional[str] = None,
    config: Optional[PMConfig] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """创建新习惯
    
    Args:
        name: 习惯名称
        category: 习惯分类 (health/learning/productivity/mindfulness/social/creative/other)
        frequency: 执行频率 (daily/weekly/monthly)
        difficulty: 难度级别 (tiny/easy/medium/hard)
        description: 习惯描述
        cue: 触发提示
        routine: 惯常行为描述
        reward: 奖励描述
        target_duration: 目标时长(分钟)
        reminder_time: 提醒时间 "HH:MM"
        config: 配置对象
        
    Returns:
        Tuple[成功标志, 消息, 习惯信息字典]
    """
    try:
        if not name.strip():
            return False, "习惯名称不能为空", None
        
        config = config or PMConfig()
        storage = HabitStorage(config)
        
        # 验证枚举值
        try:
            habit_category = HabitCategory(category.lower())
            habit_frequency = HabitFrequency(frequency.lower())
            habit_difficulty = HabitDifficulty(difficulty.lower())
        except ValueError as e:
            return False, f"参数值无效: {str(e)}", None
        
        # 检查习惯名称是否已存在
        existing_habits = storage.find_habits_by_name(name.strip())
        if any(h.name.lower() == name.strip().lower() and h.active for h in existing_habits):
            return False, f"活跃习惯 '{name}' 已存在", None
        
        # 创建习惯对象
        habit = Habit(
            name=name.strip(),
            description=description,
            category=habit_category,
            frequency=habit_frequency,
            difficulty=habit_difficulty,
            cue=cue,
            routine=routine,
            reward=reward,
            target_duration=target_duration,
            reminder_time=reminder_time
        )
        
        # 保存习惯
        success = storage.save_habit(habit)
        if success:
            habit_info = {
                "id": habit.id,
                "name": habit.name,
                "category": habit.category.value,
                "frequency": habit.frequency.value,
                "difficulty": habit.difficulty.value,
                "created_at": habit.created_at.isoformat()
            }
            
            logger.info("Habit created via tool function", 
                       habit_name=habit.name, 
                       habit_id=habit.id)
            
            return True, f"习惯 '{habit.name}' 创建成功", habit_info
        else:
            return False, "保存习惯失败", None
            
    except Exception as e:
        error_msg = f"创建习惯时发生错误: {str(e)}"
        logger.error("create_habit tool function failed", error=str(e))
        return False, error_msg, None


def record_habit_completion(
    habit_name: str,
    completed: bool = True,
    notes: Optional[str] = None,
    quality_score: Optional[int] = None,
    record_date: Optional[str] = None,
    config: Optional[PMConfig] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """记录习惯完成情况
    
    Args:
        habit_name: 习惯名称（模糊匹配）
        completed: 是否完成
        notes: 备注
        quality_score: 质量评分 (1-5)
        record_date: 记录日期 "YYYY-MM-DD"，默认今天
        config: 配置对象
        
    Returns:
        Tuple[成功标志, 消息, 记录信息字典]
    """
    try:
        config = config or PMConfig()
        storage = HabitStorage(config)
        
        # 查找习惯
        matching_habits = storage.find_habits_by_name(habit_name)
        active_habits = [h for h in matching_habits if h.active]
        
        if not active_habits:
            return False, f"未找到活跃习惯: {habit_name}", None
        
        if len(active_habits) > 1:
            habit_names = [h.name for h in active_habits]
            return False, f"找到多个匹配的习惯: {', '.join(habit_names)}，请提供更准确的名称", None
        
        habit = active_habits[0]
        
        # 解析日期
        target_date = date.today()
        if record_date:
            try:
                target_date = date.fromisoformat(record_date)
            except ValueError:
                return False, f"日期格式无效: {record_date}，请使用 YYYY-MM-DD 格式", None
        
        # 验证质量评分
        if quality_score is not None and not (1 <= quality_score <= 5):
            return False, "质量评分必须在1-5之间", None
        
        # 添加记录
        record = habit.add_record(
            completed=completed,
            notes=notes,
            quality_score=quality_score,
            record_date=target_date
        )
        
        # 保存习惯
        success = storage.save_habit(habit)
        if success:
            record_info = {
                "habit_name": habit.name,
                "habit_id": habit.id,
                "record_id": record.record_id,
                "date": record.date.isoformat(),
                "completed": record.completed,
                "quality_score": record.quality_score,
                "current_streak": habit.streak.current_streak,
                "total_completions": habit.streak.total_completions
            }
            
            status = "完成" if completed else "标记为未完成"
            logger.info("Habit completion recorded via tool function", 
                       habit_name=habit.name, 
                       completed=completed,
                       date=target_date.isoformat())
            
            return True, f"习惯 '{habit.name}' 在 {target_date} 的执行已{status}", record_info
        else:
            return False, "保存记录失败", None
            
    except Exception as e:
        error_msg = f"记录习惯完成情况时发生错误: {str(e)}"
        logger.error("record_habit_completion tool function failed", error=str(e))
        return False, error_msg, None


def get_habit_status(
    habit_name: Optional[str] = None,
    config: Optional[PMConfig] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """获取习惯状态信息
    
    Args:
        habit_name: 习惯名称（可选，为空时返回所有习惯概览）
        config: 配置对象
        
    Returns:
        Tuple[成功标志, 消息, 状态信息字典]
    """
    try:
        config = config or PMConfig()
        storage = HabitStorage(config)
        
        if habit_name:
            # 获取特定习惯的详细状态
            matching_habits = storage.find_habits_by_name(habit_name)
            active_habits = [h for h in matching_habits if h.active]
            
            if not active_habits:
                return False, f"未找到活跃习惯: {habit_name}", None
            
            if len(active_habits) > 1:
                habit_names = [h.name for h in active_habits]
                return False, f"找到多个匹配的习惯: {', '.join(habit_names)}，请提供更准确的名称", None
            
            habit = active_habits[0]
            status_info = {
                "habit": habit.get_analysis_summary(),
                "recent_records": [
                    {
                        "date": r.date.isoformat(),
                        "completed": r.completed,
                        "quality_score": r.quality_score,
                        "notes": r.notes
                    }
                    for r in sorted(habit.records, key=lambda x: x.date, reverse=True)[:7]
                ]
            }
            
            return True, f"习惯 '{habit.name}' 的状态信息", status_info
        
        else:
            # 获取所有习惯的概览状态
            stats = storage.get_habit_statistics()
            due_today = storage.get_due_habits_today()
            pending_today = storage.get_pending_habits_today()
            
            status_info = {
                "statistics": stats,
                "due_today": [
                    {
                        "name": h.name,
                        "category": h.category.value,
                        "completed": h.is_completed_today(),
                        "current_streak": h.streak.current_streak
                    }
                    for h in due_today
                ],
                "pending_count": len(pending_today),
                "pending_habits": [h.name for h in pending_today[:5]]  # 最多显示5个
            }
            
            return True, "习惯管理系统状态概览", status_info
            
    except Exception as e:
        error_msg = f"获取习惯状态时发生错误: {str(e)}"
        logger.error("get_habit_status tool function failed", error=str(e))
        return False, error_msg, None


def get_today_habit_plan(
    config: Optional[PMConfig] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """获取今日习惯计划
    
    Args:
        config: 配置对象
        
    Returns:
        Tuple[成功标志, 消息, 今日计划字典]
    """
    try:
        config = config or PMConfig()
        storage = HabitStorage(config)
        
        due_habits = storage.get_due_habits_today()
        completed_habits = [h for h in due_habits if h.is_completed_today()]
        pending_habits = [h for h in due_habits if not h.is_completed_today()]
        
        # 按优先级排序（困难度高的优先）
        def priority_key(habit):
            difficulty_order = {"tiny": 1, "easy": 2, "medium": 3, "hard": 4}
            return difficulty_order.get(habit.difficulty.value, 2)
        
        pending_habits.sort(key=priority_key, reverse=True)
        
        plan_info = {
            "date": date.today().isoformat(),
            "total_due": len(due_habits),
            "completed": len(completed_habits),
            "pending": len(pending_habits),
            "completion_rate": len(completed_habits) / len(due_habits) * 100 if due_habits else 0,
            "completed_habits": [
                {
                    "name": h.name,
                    "category": h.category.value,
                    "difficulty": h.difficulty.value,
                    "current_streak": h.streak.current_streak
                }
                for h in completed_habits
            ],
            "pending_habits": [
                {
                    "name": h.name,
                    "category": h.category.value,
                    "difficulty": h.difficulty.value,
                    "current_streak": h.streak.current_streak,
                    "cue": h.cue,
                    "target_duration": h.target_duration
                }
                for h in pending_habits
            ]
        }
        
        if due_habits:
            message = f"今日习惯计划: {len(completed_habits)}/{len(due_habits)} 已完成"
        else:
            message = "今日没有安排习惯"
        
        return True, message, plan_info
        
    except Exception as e:
        error_msg = f"获取今日习惯计划时发生错误: {str(e)}"
        logger.error("get_today_habit_plan tool function failed", error=str(e))
        return False, error_msg, None


def analyze_habit_trends(
    habit_name: Optional[str] = None,
    days: int = 30,
    config: Optional[PMConfig] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """分析习惯趋势（基于原子习惯理论）
    
    Args:
        habit_name: 习惯名称（可选）
        days: 分析天数
        config: 配置对象
        
    Returns:
        Tuple[成功标志, 消息, 分析结果字典]
    """
    try:
        config = config or PMConfig()
        storage = HabitStorage(config)
        
        if habit_name:
            # 分析特定习惯
            matching_habits = storage.find_habits_by_name(habit_name)
            active_habits = [h for h in matching_habits if h.active]
            
            if not active_habits:
                return False, f"未找到活跃习惯: {habit_name}", None
            
            if len(active_habits) > 1:
                habit_names = [h.name for h in active_habits]
                return False, f"找到多个匹配的习惯: {', '.join(habit_names)}", None
            
            habit = active_habits[0]
            analysis = _analyze_single_habit(habit, days)
            
            return True, f"习惯 '{habit.name}' 的趋势分析", analysis
        
        else:
            # 整体习惯趋势分析
            all_habits = storage.get_all_habits(active_only=True)
            if not all_habits:
                return True, "暂无活跃习惯可供分析", {"habits_count": 0}
            
            overall_analysis = _analyze_overall_trends(all_habits, days)
            
            return True, f"过去{days}天的习惯趋势分析", overall_analysis
            
    except Exception as e:
        error_msg = f"分析习惯趋势时发生错误: {str(e)}"
        logger.error("analyze_habit_trends tool function failed", error=str(e))
        return False, error_msg, None


def suggest_habit_improvements(
    habit_name: str,
    config: Optional[PMConfig] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """基于原子习惯理论提供改进建议
    
    Args:
        habit_name: 习惯名称
        config: 配置对象
        
    Returns:
        Tuple[成功标志, 消息, 建议字典]
    """
    try:
        config = config or PMConfig()
        storage = HabitStorage(config)
        
        matching_habits = storage.find_habits_by_name(habit_name)
        active_habits = [h for h in matching_habits if h.active]
        
        if not active_habits:
            return False, f"未找到活跃习惯: {habit_name}", None
        
        if len(active_habits) > 1:
            habit_names = [h.name for h in active_habits]
            return False, f"找到多个匹配的习惯: {', '.join(habit_names)}", None
        
        habit = active_habits[0]
        suggestions = _generate_habit_suggestions(habit)
        
        return True, f"习惯 '{habit.name}' 的改进建议", suggestions
        
    except Exception as e:
        error_msg = f"生成习惯建议时发生错误: {str(e)}"
        logger.error("suggest_habit_improvements tool function failed", error=str(e))
        return False, error_msg, None


# ========== 辅助函数 ==========

def _analyze_single_habit(habit: Habit, days: int) -> Dict[str, Any]:
    """分析单个习惯的详细趋势"""
    
    # 计算时间范围内的完成率
    completion_rate = habit.get_completion_rate(days)
    
    # 分析连续性
    streak_info = {
        "current_streak": habit.streak.current_streak,
        "longest_streak": habit.streak.longest_streak,
        "total_completions": habit.streak.total_completions
    }
    
    # 质量趋势分析
    recent_records = [r for r in habit.records if r.quality_score is not None]
    quality_trend = "稳定"
    if len(recent_records) >= 3:
        recent_scores = [r.quality_score for r in recent_records[-7:]]
        if len(recent_scores) >= 2:
            avg_recent = sum(recent_scores[-3:]) / 3
            avg_earlier = sum(recent_scores[:-3]) / len(recent_scores[:-3]) if len(recent_scores) > 3 else avg_recent
            
            if avg_recent > avg_earlier + 0.5:
                quality_trend = "改善"
            elif avg_recent < avg_earlier - 0.5:
                quality_trend = "下降"
    
    return {
        "habit_name": habit.name,
        "analysis_period": f"{days}天",
        "completion_rate": round(completion_rate, 1),
        "streak_analysis": streak_info,
        "quality_trend": quality_trend,
        "difficulty_level": habit.difficulty.value,
        "frequency": habit.frequency.value,
        "active_days": (date.today() - habit.created_at.date()).days + 1,
        "habit_maturity": _calculate_habit_maturity(habit)
    }


def _analyze_overall_trends(habits: List[Habit], days: int) -> Dict[str, Any]:
    """分析整体习惯趋势"""
    
    total_habits = len(habits)
    avg_completion = sum(h.get_completion_rate(days) for h in habits) / total_habits
    
    # 按分类统计
    category_stats = {}
    for habit in habits:
        category = habit.category.value
        if category not in category_stats:
            category_stats[category] = {"count": 0, "avg_completion": 0, "habits": []}
        
        category_stats[category]["count"] += 1
        category_stats[category]["habits"].append({
            "name": habit.name,
            "completion_rate": habit.get_completion_rate(days)
        })
    
    # 计算各分类平均完成率
    for category in category_stats:
        rates = [h["completion_rate"] for h in category_stats[category]["habits"]]
        category_stats[category]["avg_completion"] = sum(rates) / len(rates)
    
    # 找出表现最好和最需要关注的习惯
    habits_with_rates = [(h, h.get_completion_rate(days)) for h in habits]
    habits_with_rates.sort(key=lambda x: x[1], reverse=True)
    
    best_habits = [{"name": h.name, "rate": rate} for h, rate in habits_with_rates[:3]]
    struggling_habits = [{"name": h.name, "rate": rate} for h, rate in habits_with_rates[-3:] if rate < 70]
    
    return {
        "analysis_period": f"{days}天",
        "total_habits": total_habits,
        "overall_completion_rate": round(avg_completion, 1),
        "category_breakdown": {
            cat: {
                "count": stats["count"],
                "avg_completion": round(stats["avg_completion"], 1)
            }
            for cat, stats in category_stats.items()
        },
        "top_performing": best_habits,
        "needs_attention": struggling_habits,
        "system_health": "良好" if avg_completion >= 80 else "需要改善" if avg_completion >= 60 else "需要重点关注"
    }


def _calculate_habit_maturity(habit: Habit) -> str:
    """计算习惯成熟度"""
    days_active = (date.today() - habit.created_at.date()).days + 1
    completion_rate = habit.get_completion_rate(min(days_active, 30))
    
    if days_active < 7:
        return "新习惯"
    elif days_active < 21:
        return "形成中" if completion_rate >= 70 else "不稳定"
    elif days_active < 66:
        return "逐渐稳固" if completion_rate >= 75 else "需要加强"
    else:
        return "成熟习惯" if completion_rate >= 80 else "需要重新评估"


def _generate_habit_suggestions(habit: Habit) -> Dict[str, Any]:
    """基于原子习惯理论生成改进建议"""
    
    completion_rate = habit.get_completion_rate(30)
    current_streak = habit.streak.current_streak
    
    suggestions = []
    
    # 完成率低的建议
    if completion_rate < 60:
        suggestions.append({
            "type": "difficulty",
            "title": "降低难度（2分钟法则）",
            "description": "考虑将习惯简化为更小的版本，确保即使在最忙的时候也能完成"
        })
        
        if not habit.cue:
            suggestions.append({
                "type": "cue",
                "title": "设置明确的触发提示",
                "description": "为习惯设置清晰的时间、地点或事件提示，比如'刷牙后'、'坐在办公桌前时'"
            })
    
    # 连续性差的建议
    if current_streak < 3:
        suggestions.append({
            "type": "consistency",
            "title": "关注连续性",
            "description": "专注于不中断连续执行，哪怕执行质量不完美，连续性比完美更重要"
        })
    
    # 奖励机制建议
    if not habit.reward:
        suggestions.append({
            "type": "reward",
            "title": "设置即时奖励",
            "description": "在完成习惯后给自己一个小奖励，强化正反馈循环"
        })
    
    # 环境建议
    if habit.category == HabitCategory.HEALTH:
        suggestions.append({
            "type": "environment",
            "title": "优化环境设计",
            "description": "让好习惯更容易执行，比如把运动装备放在显眼的地方"
        })
    
    # 基于数据的个性化建议
    habit_age = (date.today() - habit.created_at.date()).days
    if habit_age > 30 and completion_rate < 70:
        suggestions.append({
            "type": "reset",
            "title": "考虑重新设计",
            "description": "这个习惯可能需要重新思考，考虑调整时间、方式或目标"
        })
    
    return {
        "habit_name": habit.name,
        "current_performance": {
            "completion_rate": round(completion_rate, 1),
            "current_streak": current_streak,
            "maturity": _calculate_habit_maturity(habit)
        },
        "suggestions": suggestions,
        "atomic_habits_principle": "让好习惯显而易见、有吸引力、简便易行、令人愉悦"
    }