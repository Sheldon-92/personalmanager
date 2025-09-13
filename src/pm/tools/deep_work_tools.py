"""深度工作AI可调用工具函数 - Sprint 14核心功能

这些函数被设计为独立的、可供AI直接调用的工具函数
不依赖CLI框架，可以被其他Python代码或AI代理直接调用
基于《深度工作》理论的专注管理和时段跟踪
"""

import structlog
from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional, Tuple

from pm.core.config import PMConfig
from pm.storage.deep_work_storage import DeepWorkStorage
from pm.models.deep_work import (
    DeepWorkSession, ReflectionEntry, DeepWorkType, FocusLevel, 
    WorkEnvironment, DistractionType, EnvironmentSettings
)

logger = structlog.get_logger()


# ========== 深度工作时段管理工具 ==========

def create_deep_work_session(
    title: str,
    planned_duration_minutes: int = 60,
    work_type: str = "rhythmic",
    target_focus_level: str = "deep",
    primary_task: Optional[str] = None,
    project_id: Optional[str] = None,
    description: Optional[str] = None,
    planned_start: Optional[str] = None,  # ISO格式字符串
    environment_location: str = "home_office",
    tags: Optional[List[str]] = None,
    config: Optional[PMConfig] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """创建深度工作时段
    
    Args:
        title: 时段标题
        planned_duration_minutes: 计划持续时间（分钟）
        work_type: 深度工作类型 (monasticism/bimodal/rhythmic/journalistic)
        target_focus_level: 目标专注级别 (shallow/semi_deep/deep/profound)
        primary_task: 主要任务描述
        project_id: 关联项目ID
        description: 时段描述
        planned_start: 计划开始时间（ISO格式）
        environment_location: 工作环境 (home_office/coworking/library/cafe/outdoor/other)
        tags: 标签列表
        config: 配置对象
        
    Returns:
        Tuple[成功标志, 消息, 时段信息字典]
    """
    try:
        if not title.strip():
            return False, "时段标题不能为空", None
        
        if planned_duration_minutes <= 0 or planned_duration_minutes > 480:
            return False, "计划持续时间必须在1-480分钟之间", None
        
        config = config or PMConfig()
        storage = DeepWorkStorage(config)
        
        # 验证枚举值
        try:
            session_work_type = DeepWorkType(work_type.lower())
            session_focus_level = FocusLevel(target_focus_level.lower())
            env_location = WorkEnvironment(environment_location.lower())
        except ValueError as e:
            return False, f"参数值无效: {str(e)}", None
        
        # 解析计划开始时间
        if planned_start:
            try:
                start_time = datetime.fromisoformat(planned_start)
            except ValueError:
                return False, "计划开始时间格式无效，请使用ISO格式", None
        else:
            start_time = datetime.now()
        
        # 检查是否有冲突的活跃时段
        active_session = storage.get_active_session()
        if active_session:
            return False, f"已有进行中的深度工作时段: {active_session.title}", None
        
        # 创建环境设置
        environment = EnvironmentSettings(location=env_location)
        environment.calculate_environment_score()
        
        # 创建深度工作时段对象
        session = DeepWorkSession(
            title=title.strip(),
            description=description,
            work_type=session_work_type,
            target_focus_level=session_focus_level,
            planned_duration_minutes=planned_duration_minutes,
            planned_start=start_time,
            primary_task=primary_task,
            project_id=project_id,
            tags=tags or [],
            environment=environment
        )
        
        # 保存时段
        success = storage.save_session(session)
        if success:
            session_info = {
                "session_id": session.session_id,
                "title": session.title,
                "work_type": session.work_type.value,
                "target_focus_level": session.target_focus_level.value,
                "planned_duration_minutes": session.planned_duration_minutes,
                "planned_start": session.planned_start.isoformat(),
                "planned_end": session.planned_end.isoformat() if session.planned_end else None,
                "primary_task": session.primary_task,
                "environment_location": session.environment.location.value,
                "created_at": session.created_at.isoformat()
            }
            
            logger.info("Deep work session created via tool function", 
                       session_id=session.session_id,
                       title=session.title)
            
            return True, f"深度工作时段 '{title}' 创建成功", session_info
        else:
            return False, "保存深度工作时段失败", None
            
    except Exception as e:
        logger.error("Failed to create deep work session", error=str(e))
        return False, f"创建深度工作时段时发生错误: {str(e)}", None


def start_deep_work_session(
    session_id: str,
    pre_session_notes: Optional[str] = None,
    energy_level: int = 5,
    config: Optional[PMConfig] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """开始深度工作时段
    
    Args:
        session_id: 时段ID
        pre_session_notes: 开始前的笔记
        energy_level: 开始时精力水平 (1-5)
        config: 配置对象
        
    Returns:
        Tuple[成功标志, 消息, 时段信息字典]
    """
    try:
        config = config or PMConfig()
        storage = DeepWorkStorage(config)
        
        session = storage.get_session(session_id)
        if not session:
            return False, f"找不到ID为 {session_id} 的深度工作时段", None
        
        if session.actual_start:
            return False, f"时段 '{session.title}' 已经开始", None
        
        if session.completed:
            return False, f"时段 '{session.title}' 已经完成", None
        
        # 检查是否有其他活跃时段
        active_session = storage.get_active_session()
        if active_session and active_session.session_id != session_id:
            return False, f"已有进行中的深度工作时段: {active_session.title}", None
        
        # 开始时段
        session.start_session()
        session.pre_session_notes = pre_session_notes
        session.energy_level_start = max(1, min(5, energy_level))
        
        # 保存更新
        success = storage.save_session(session)
        if success:
            session_info = {
                "session_id": session.session_id,
                "title": session.title,
                "actual_start": session.actual_start.isoformat(),
                "planned_end": session.planned_end.isoformat() if session.planned_end else None,
                "energy_level_start": session.energy_level_start,
                "pre_session_notes": session.pre_session_notes
            }
            
            logger.info("Deep work session started", 
                       session_id=session.session_id,
                       title=session.title)
            
            return True, f"深度工作时段 '{session.title}' 已开始", session_info
        else:
            return False, "保存时段开始状态失败", None
            
    except Exception as e:
        logger.error("Failed to start deep work session", 
                    session_id=session_id, error=str(e))
        return False, f"开始深度工作时段时发生错误: {str(e)}", None


def end_deep_work_session(
    session_id: str,
    actual_focus_level: str = "deep",
    energy_level_end: int = 3,
    post_session_reflection: Optional[str] = None,
    lessons_learned: Optional[List[str]] = None,
    improvement_actions: Optional[List[str]] = None,
    config: Optional[PMConfig] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """结束深度工作时段
    
    Args:
        session_id: 时段ID
        actual_focus_level: 实际专注级别 (shallow/semi_deep/deep/profound)
        energy_level_end: 结束时精力水平 (1-5)
        post_session_reflection: 结束后反思
        lessons_learned: 经验教训列表
        improvement_actions: 改进行动列表
        config: 配置对象
        
    Returns:
        Tuple[成功标志, 消息, 时段总结字典]
    """
    try:
        config = config or PMConfig()
        storage = DeepWorkStorage(config)
        
        session = storage.get_session(session_id)
        if not session:
            return False, f"找不到ID为 {session_id} 的深度工作时段", None
        
        if not session.actual_start:
            return False, f"时段 '{session.title}' 尚未开始", None
        
        if session.completed:
            return False, f"时段 '{session.title}' 已经完成", None
        
        # 验证专注级别
        try:
            focus_level = FocusLevel(actual_focus_level.lower())
        except ValueError:
            return False, f"无效的专注级别: {actual_focus_level}", None
        
        # 结束时段
        session.actual_focus_level = focus_level
        session.energy_level_end = max(1, min(5, energy_level_end))
        session.lessons_learned = lessons_learned or []
        session.improvement_actions = improvement_actions or []
        session.end_session(post_session_reflection)
        
        # 保存更新
        success = storage.save_session(session)
        if success:
            actual_duration = session.get_actual_duration_minutes()
            efficiency_score = session.get_efficiency_score()
            
            session_summary = {
                "session_id": session.session_id,
                "title": session.title,
                "actual_start": session.actual_start.isoformat(),
                "actual_end": session.actual_end.isoformat(),
                "planned_duration_minutes": session.planned_duration_minutes,
                "actual_duration_minutes": actual_duration,
                "target_focus_level": session.target_focus_level.value,
                "actual_focus_level": session.actual_focus_level.value,
                "energy_change": session.energy_level_end - session.energy_level_start,
                "focus_score": session.metrics.focus_score,
                "efficiency_score": efficiency_score,
                "distraction_count": len(session.distractions),
                "completed": session.completed,
                "post_session_reflection": session.post_session_reflection,
                "lessons_learned": session.lessons_learned,
                "improvement_actions": session.improvement_actions
            }
            
            logger.info("Deep work session ended", 
                       session_id=session.session_id,
                       title=session.title,
                       actual_duration=actual_duration)
            
            return True, f"深度工作时段 '{session.title}' 已完成（{actual_duration}分钟）", session_summary
        else:
            return False, "保存时段结束状态失败", None
            
    except Exception as e:
        logger.error("Failed to end deep work session", 
                    session_id=session_id, error=str(e))
        return False, f"结束深度工作时段时发生错误: {str(e)}", None


def add_distraction_to_session(
    session_id: str,
    distraction_type: str,
    description: Optional[str] = None,
    severity: int = 1,
    duration_seconds: Optional[int] = None,
    config: Optional[PMConfig] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """向深度工作时段添加干扰事件
    
    Args:
        session_id: 时段ID
        distraction_type: 干扰类型 (internal/external/social/tech)
        description: 干扰描述
        severity: 严重程度 (1-5)
        duration_seconds: 干扰持续时间（秒）
        config: 配置对象
        
    Returns:
        Tuple[成功标志, 消息, 干扰事件字典]
    """
    try:
        config = config or PMConfig()
        storage = DeepWorkStorage(config)
        
        session = storage.get_session(session_id)
        if not session:
            return False, f"找不到ID为 {session_id} 的深度工作时段", None
        
        if not session.actual_start or session.completed:
            return False, "只能向进行中的时段添加干扰事件", None
        
        # 验证干扰类型
        try:
            dtype = DistractionType(distraction_type.lower())
        except ValueError:
            return False, f"无效的干扰类型: {distraction_type}", None
        
        # 添加干扰事件
        distraction = session.add_distraction(
            distraction_type=dtype,
            description=description,
            severity=max(1, min(5, severity))
        )
        
        if duration_seconds:
            distraction.duration_seconds = duration_seconds
        
        # 保存更新
        success = storage.save_session(session)
        if success:
            distraction_info = {
                "event_id": distraction.event_id,
                "session_id": distraction.session_id,
                "distraction_type": distraction.distraction_type.value,
                "description": distraction.description,
                "severity": distraction.severity,
                "timestamp": distraction.timestamp.isoformat(),
                "duration_seconds": distraction.duration_seconds,
                "total_distractions": len(session.distractions)
            }
            
            logger.info("Distraction added to session", 
                       session_id=session.session_id,
                       distraction_type=dtype.value,
                       severity=severity)
            
            return True, f"干扰事件已记录到时段 '{session.title}'", distraction_info
        else:
            return False, "保存干扰事件失败", None
            
    except Exception as e:
        logger.error("Failed to add distraction to session", 
                    session_id=session_id, error=str(e))
        return False, f"添加干扰事件时发生错误: {str(e)}", None


def get_active_deep_work_session(
    config: Optional[PMConfig] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """获取当前活跃的深度工作时段
    
    Args:
        config: 配置对象
        
    Returns:
        Tuple[成功标志, 消息, 时段信息字典]
    """
    try:
        config = config or PMConfig()
        storage = DeepWorkStorage(config)
        
        active_session = storage.get_active_session()
        if not active_session:
            return False, "当前没有进行中的深度工作时段", None
        
        elapsed_minutes = 0
        remaining_minutes = 0
        if active_session.actual_start:
            elapsed = datetime.now() - active_session.actual_start
            elapsed_minutes = int(elapsed.total_seconds() / 60)
            remaining_minutes = max(0, active_session.planned_duration_minutes - elapsed_minutes)
        
        session_info = {
            "session_id": active_session.session_id,
            "title": active_session.title,
            "work_type": active_session.work_type.value,
            "target_focus_level": active_session.target_focus_level.value,
            "planned_duration_minutes": active_session.planned_duration_minutes,
            "elapsed_minutes": elapsed_minutes,
            "remaining_minutes": remaining_minutes,
            "actual_start": active_session.actual_start.isoformat() if active_session.actual_start else None,
            "primary_task": active_session.primary_task,
            "distraction_count": len(active_session.distractions),
            "environment_location": active_session.environment.location.value,
            "energy_level_start": active_session.energy_level_start
        }
        
        return True, f"当前正在进行: {active_session.title}", session_info
        
    except Exception as e:
        logger.error("Failed to get active session", error=str(e))
        return False, f"获取活跃时段时发生错误: {str(e)}", None


def get_todays_deep_work_sessions(
    config: Optional[PMConfig] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """获取今天的深度工作时段
    
    Args:
        config: 配置对象
        
    Returns:
        Tuple[成功标志, 消息, 今日时段信息字典]
    """
    try:
        config = config or PMConfig()
        storage = DeepWorkStorage(config)
        
        todays_sessions = storage.get_todays_sessions()
        
        if not todays_sessions:
            return False, "今天还没有深度工作时段", None
        
        total_planned = sum(s.planned_duration_minutes for s in todays_sessions)
        completed_sessions = [s for s in todays_sessions if s.completed]
        total_actual = sum(s.get_actual_duration_minutes() for s in completed_sessions)
        active_session = next((s for s in todays_sessions if s.actual_start and not s.completed), None)
        
        sessions_info = []
        for session in sorted(todays_sessions, key=lambda x: x.planned_start):
            session_data = {
                "session_id": session.session_id,
                "title": session.title,
                "planned_start": session.planned_start.strftime("%H:%M"),
                "planned_duration_minutes": session.planned_duration_minutes,
                "status": "active" if session.actual_start and not session.completed 
                         else "completed" if session.completed 
                         else "planned",
                "actual_duration_minutes": session.get_actual_duration_minutes() if session.completed else 0,
                "focus_score": session.metrics.focus_score if session.completed else None,
                "distraction_count": len(session.distractions)
            }
            sessions_info.append(session_data)
        
        summary = {
            "date": date.today().isoformat(),
            "total_sessions": len(todays_sessions),
            "completed_sessions": len(completed_sessions),
            "total_planned_minutes": total_planned,
            "total_actual_minutes": total_actual,
            "has_active_session": active_session is not None,
            "active_session_title": active_session.title if active_session else None,
            "sessions": sessions_info,
            "average_focus_score": round(sum(s.metrics.focus_score for s in completed_sessions) / len(completed_sessions), 1) if completed_sessions else 0
        }
        
        return True, f"今天共有 {len(todays_sessions)} 个深度工作时段", summary
        
    except Exception as e:
        logger.error("Failed to get today's sessions", error=str(e))
        return False, f"获取今日时段时发生错误: {str(e)}", None


# ========== 分析和统计工具 ==========

def get_deep_work_statistics(
    days: int = 30,
    config: Optional[PMConfig] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """获取深度工作统计信息
    
    Args:
        days: 统计天数（默认30天）
        config: 配置对象
        
    Returns:
        Tuple[成功标志, 消息, 统计信息字典]
    """
    try:
        if days <= 0 or days > 365:
            return False, "统计天数必须在1-365天之间", None
        
        config = config or PMConfig()
        storage = DeepWorkStorage(config)
        
        statistics = storage.get_session_statistics(days)
        
        if statistics["total_sessions"] == 0:
            return False, f"过去 {days} 天内没有深度工作时段", None
        
        # 添加额外的分析信息
        stats_info = {
            **statistics,
            "analysis_period_days": days,
            "daily_average_sessions": round(statistics["total_sessions"] / days, 1),
            "daily_average_deep_work_minutes": round(statistics["total_deep_work_minutes"] / days, 1),
            "productivity_rating": "高" if statistics["average_focus_score"] >= 80 
                                  else "中" if statistics["average_focus_score"] >= 60 
                                  else "低",
            "distraction_rating": "低" if statistics["distraction_rate"] <= 2 
                                 else "中" if statistics["distraction_rate"] <= 5 
                                 else "高"
        }
        
        # 添加建议
        recommendations = []
        if statistics["average_focus_score"] < 70:
            recommendations.append("考虑减少干扰源，提升专注环境质量")
        if statistics["distraction_rate"] > 3:
            recommendations.append("尝试使用番茄工作法或其他专注技巧")
        if statistics["completion_rate"] < 80:
            recommendations.append("建议调整时段规划，设置更现实的目标")
        
        stats_info["recommendations"] = recommendations
        
        return True, f"过去 {days} 天深度工作统计", stats_info
        
    except Exception as e:
        logger.error("Failed to get deep work statistics", days=days, error=str(e))
        return False, f"获取统计信息时发生错误: {str(e)}", None


def get_focus_trends(
    days: int = 30,
    config: Optional[PMConfig] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """获取专注度趋势分析
    
    Args:
        days: 分析天数（默认30天）
        config: 配置对象
        
    Returns:
        Tuple[成功标志, 消息, 趋势分析字典]
    """
    try:
        if days <= 0 or days > 365:
            return False, "分析天数必须在1-365天之间", None
        
        config = config or PMConfig()
        storage = DeepWorkStorage(config)
        
        trends = storage.get_focus_trends(days)
        
        if not trends:
            return False, f"过去 {days} 天内没有完成的深度工作时段", None
        
        # 计算趋势指标
        focus_scores = [day["average_focus_score"] for day in trends if day["average_focus_score"] > 0]
        if not focus_scores:
            return False, "没有足够的数据进行趋势分析", None
        
        avg_focus = sum(focus_scores) / len(focus_scores)
        max_focus = max(focus_scores)
        min_focus = min(focus_scores)
        
        # 计算趋势方向（最近7天 vs 之前的平均值）
        recent_scores = focus_scores[-7:] if len(focus_scores) >= 7 else focus_scores
        earlier_scores = focus_scores[:-7] if len(focus_scores) > 7 else focus_scores[:len(focus_scores)//2]
        
        recent_avg = sum(recent_scores) / len(recent_scores) if recent_scores else 0
        earlier_avg = sum(earlier_scores) / len(earlier_scores) if earlier_scores else recent_avg
        
        trend_direction = "上升" if recent_avg > earlier_avg + 5 else "下降" if recent_avg < earlier_avg - 5 else "稳定"
        
        trends_info = {
            "analysis_period_days": days,
            "total_data_points": len(trends),
            "daily_trends": trends,
            "average_focus_score": round(avg_focus, 1),
            "max_focus_score": round(max_focus, 1),
            "min_focus_score": round(min_focus, 1),
            "trend_direction": trend_direction,
            "recent_average": round(recent_avg, 1),
            "earlier_average": round(earlier_avg, 1),
            "improvement_percentage": round(((recent_avg - earlier_avg) / earlier_avg * 100), 1) if earlier_avg > 0 else 0
        }
        
        return True, f"过去 {days} 天专注度趋势分析", trends_info
        
    except Exception as e:
        logger.error("Failed to get focus trends", days=days, error=str(e))
        return False, f"获取趋势分析时发生错误: {str(e)}", None


# ========== 反思记录管理工具 ==========

def create_reflection_entry(
    period_type: str = "daily",
    what_worked_well: Optional[List[str]] = None,
    what_could_improve: Optional[List[str]] = None,
    key_insights: Optional[List[str]] = None,
    next_actions: Optional[List[str]] = None,
    overall_satisfaction: int = 3,
    focus_quality_rating: int = 3,
    productivity_rating: int = 3,
    energy_management_rating: int = 3,
    config: Optional[PMConfig] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """创建深度工作反思记录
    
    Args:
        period_type: 反思周期类型 (daily/weekly/monthly)
        what_worked_well: 工作良好的方面
        what_could_improve: 可改进的方面
        key_insights: 关键洞察
        next_actions: 下一步行动
        overall_satisfaction: 总体满意度 (1-5)
        focus_quality_rating: 专注质量评分 (1-5)
        productivity_rating: 生产力评分 (1-5)
        energy_management_rating: 精力管理评分 (1-5)
        config: 配置对象
        
    Returns:
        Tuple[成功标志, 消息, 反思记录字典]
    """
    try:
        if period_type not in ["daily", "weekly", "monthly"]:
            return False, "反思周期类型必须是 daily/weekly/monthly 之一", None
        
        config = config or PMConfig()
        storage = DeepWorkStorage(config)
        
        # 获取相关的深度工作时段
        if period_type == "daily":
            related_sessions = storage.get_todays_sessions()
        elif period_type == "weekly":
            related_sessions = storage.get_recent_sessions(7)
        else:  # monthly
            related_sessions = storage.get_recent_sessions(30)
        
        # 创建反思记录
        reflection = ReflectionEntry(
            period_type=period_type,
            what_worked_well=what_worked_well or [],
            what_could_improve=what_could_improve or [],
            key_insights=key_insights or [],
            next_actions=next_actions or [],
            overall_satisfaction=max(1, min(5, overall_satisfaction)),
            focus_quality_rating=max(1, min(5, focus_quality_rating)),
            productivity_rating=max(1, min(5, productivity_rating)),
            energy_management_rating=max(1, min(5, energy_management_rating)),
            related_sessions=[s.session_id for s in related_sessions]
        )
        
        # 保存反思记录
        success = storage.save_reflection(reflection)
        if success:
            reflection_info = {
                "reflection_id": reflection.reflection_id,
                "period_type": reflection.period_type,
                "date": reflection.date.isoformat(),
                "overall_satisfaction": reflection.overall_satisfaction,
                "focus_quality_rating": reflection.focus_quality_rating,
                "productivity_rating": reflection.productivity_rating,
                "energy_management_rating": reflection.energy_management_rating,
                "what_worked_well": reflection.what_worked_well,
                "what_could_improve": reflection.what_could_improve,
                "key_insights": reflection.key_insights,
                "next_actions": reflection.next_actions,
                "related_sessions_count": len(reflection.related_sessions)
            }
            
            logger.info("Reflection entry created", 
                       reflection_id=reflection.reflection_id,
                       period_type=period_type)
            
            return True, f"{period_type}反思记录创建成功", reflection_info
        else:
            return False, "保存反思记录失败", None
            
    except Exception as e:
        logger.error("Failed to create reflection entry", error=str(e))
        return False, f"创建反思记录时发生错误: {str(e)}", None


def get_recent_reflections(
    days: int = 30,
    period_type: Optional[str] = None,
    config: Optional[PMConfig] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """获取最近的反思记录
    
    Args:
        days: 查询天数
        period_type: 反思周期类型过滤 (daily/weekly/monthly)
        config: 配置对象
        
    Returns:
        Tuple[成功标志, 消息, 反思记录字典]
    """
    try:
        if days <= 0 or days > 365:
            return False, "查询天数必须在1-365天之间", None
        
        config = config or PMConfig()
        storage = DeepWorkStorage(config)
        
        reflections = storage.get_recent_reflections(days)
        
        # 按周期类型过滤
        if period_type:
            if period_type not in ["daily", "weekly", "monthly"]:
                return False, "反思周期类型必须是 daily/weekly/monthly 之一", None
            reflections = [r for r in reflections if r.period_type == period_type]
        
        if not reflections:
            filter_msg = f" ({period_type})" if period_type else ""
            return False, f"过去 {days} 天内没有反思记录{filter_msg}", None
        
        reflections_info = []
        for reflection in reflections:
            reflection_data = {
                "reflection_id": reflection.reflection_id,
                "date": reflection.date.strftime("%Y-%m-%d"),
                "period_type": reflection.period_type,
                "overall_satisfaction": reflection.overall_satisfaction,
                "focus_quality_rating": reflection.focus_quality_rating,
                "productivity_rating": reflection.productivity_rating,
                "energy_management_rating": reflection.energy_management_rating,
                "what_worked_well": reflection.what_worked_well,
                "what_could_improve": reflection.what_could_improve,
                "key_insights": reflection.key_insights,
                "next_actions": reflection.next_actions,
                "related_sessions_count": len(reflection.related_sessions)
            }
            reflections_info.append(reflection_data)
        
        # 计算平均评分
        avg_satisfaction = sum(r.overall_satisfaction for r in reflections) / len(reflections)
        avg_focus = sum(r.focus_quality_rating for r in reflections) / len(reflections)
        avg_productivity = sum(r.productivity_rating for r in reflections) / len(reflections)
        avg_energy = sum(r.energy_management_rating for r in reflections) / len(reflections)
        
        summary = {
            "query_days": days,
            "period_type_filter": period_type,
            "total_reflections": len(reflections),
            "reflections": reflections_info,
            "average_ratings": {
                "overall_satisfaction": round(avg_satisfaction, 1),
                "focus_quality": round(avg_focus, 1),
                "productivity": round(avg_productivity, 1),
                "energy_management": round(avg_energy, 1)
            }
        }
        
        return True, f"找到 {len(reflections)} 条反思记录", summary
        
    except Exception as e:
        logger.error("Failed to get recent reflections", days=days, error=str(e))
        return False, f"获取反思记录时发生错误: {str(e)}", None