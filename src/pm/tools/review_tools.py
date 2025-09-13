"""回顾与反思AI可调用工具函数 - Sprint 16核心功能

这些函数被设计为独立的、可供AI直接调用的工具函数
不依赖CLI框架，可以被其他Python代码或AI代理直接调用
帮助用户实现持续自我提升和成长
"""

import structlog
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple

from pm.core.config import PMConfig
from pm.storage.review_storage import ReviewStorage
from pm.models.review import (
    ReviewEntry, WeeklyReview, ProjectRetrospective, DecisionReview,
    ReviewType, ReviewPriority, GrowthArea, GrowthInsight, ActionItem,
    DecisionOutcome
)

logger = structlog.get_logger()


# ========== 每周回顾管理工具 ==========

def create_weekly_review(
    week_start_date: Optional[str] = None,  # YYYY-MM-DD格式
    achievements: Optional[List[str]] = None,
    challenges: Optional[List[str]] = None,
    lessons_learned: Optional[List[str]] = None,
    what_went_well: Optional[List[str]] = None,
    what_could_improve: Optional[List[str]] = None,
    week_goals_achieved: Optional[List[str]] = None,
    week_goals_missed: Optional[List[str]] = None,
    next_week_goals: Optional[List[str]] = None,
    overall_satisfaction: int = 3,
    productivity_rating: int = 3,
    learning_rating: int = 3,
    work_performance: int = 3,
    personal_development: int = 3,
    health_wellness: int = 3,
    relationships: int = 3,
    config: Optional[PMConfig] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """创建每周回顾
    
    Args:
        week_start_date: 回顾周的开始日期（YYYY-MM-DD）
        achievements: 本周成就列表
        challenges: 遇到的挑战列表
        lessons_learned: 学到的经验教训
        what_went_well: 进展顺利的方面
        what_could_improve: 可以改进的方面
        week_goals_achieved: 完成的周目标
        week_goals_missed: 未完成的周目标
        next_week_goals: 下周目标
        overall_satisfaction: 总体满意度 (1-5)
        productivity_rating: 生产力评分 (1-5)
        learning_rating: 学习成长评分 (1-5)
        work_performance: 工作表现 (1-5)
        personal_development: 个人发展 (1-5)
        health_wellness: 健康状况 (1-5)
        relationships: 人际关系 (1-5)
        config: 配置对象
        
    Returns:
        Tuple[成功标志, 消息, 周回顾信息字典]
    """
    try:
        config = config or PMConfig()
        storage = ReviewStorage(config)
        
        # 解析日期
        if week_start_date:
            try:
                start_date = date.fromisoformat(week_start_date)
            except ValueError:
                return False, "日期格式无效，请使用YYYY-MM-DD格式", None
        else:
            # 默认为本周一
            today = date.today()
            start_date = today - timedelta(days=today.weekday())
        
        # 计算周结束日期
        end_date = start_date + timedelta(days=6)
        
        # 检查是否已有本周的回顾
        existing_reviews = storage.get_reviews_by_date_range(start_date, end_date)
        weekly_reviews = [r for r in existing_reviews if isinstance(r, WeeklyReview)]
        
        if weekly_reviews:
            return False, f"本周（{start_date} 至 {end_date}）已有回顾记录", None
        
        # 创建每周回顾对象
        weekly_review = WeeklyReview(
            review_period_start=start_date,
            review_period_end=end_date,
            achievements=achievements or [],
            challenges=challenges or [],
            lessons_learned=lessons_learned or [],
            what_went_well=what_went_well or [],
            what_could_improve=what_could_improve or [],
            week_goals_achieved=week_goals_achieved or [],
            week_goals_missed=week_goals_missed or [],
            next_week_goals=next_week_goals or [],
            overall_satisfaction=max(1, min(5, overall_satisfaction)),
            productivity_rating=max(1, min(5, productivity_rating)),
            learning_rating=max(1, min(5, learning_rating)),
            work_performance=max(1, min(5, work_performance)),
            personal_development=max(1, min(5, personal_development)),
            health_wellness=max(1, min(5, health_wellness)),
            relationships=max(1, min(5, relationships))
        )
        
        # 保存回顾
        success = storage.save_review(weekly_review)
        if success:
            review_info = {
                "review_id": weekly_review.review_id,
                "title": weekly_review.title,
                "week_start": weekly_review.review_period_start.isoformat(),
                "week_end": weekly_review.review_period_end.isoformat(),
                "weekly_score": weekly_review.calculate_weekly_score(),
                "goal_completion_rate": weekly_review.get_goal_completion_rate(),
                "total_achievements": len(weekly_review.achievements),
                "total_challenges": len(weekly_review.challenges),
                "total_lessons": len(weekly_review.lessons_learned),
                "next_week_goals_count": len(weekly_review.next_week_goals),
                "created_at": weekly_review.created_at.isoformat()
            }
            
            logger.info("Weekly review created via tool function", 
                       review_id=weekly_review.review_id,
                       week_start=start_date.isoformat())
            
            return True, f"每周回顾创建成功：{weekly_review.title}", review_info
        else:
            return False, "保存每周回顾失败", None
            
    except Exception as e:
        logger.error("Failed to create weekly review", error=str(e))
        return False, f"创建每周回顾时发生错误: {str(e)}", None


def get_weekly_review(
    week_start_date: Optional[str] = None,
    config: Optional[PMConfig] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """获取指定周的回顾
    
    Args:
        week_start_date: 周开始日期（YYYY-MM-DD），留空获取本周
        config: 配置对象
        
    Returns:
        Tuple[成功标志, 消息, 周回顾信息字典]
    """
    try:
        config = config or PMConfig()
        storage = ReviewStorage(config)
        
        # 解析日期
        if week_start_date:
            try:
                start_date = date.fromisoformat(week_start_date)
            except ValueError:
                return False, "日期格式无效，请使用YYYY-MM-DD格式", None
        else:
            # 默认为本周一
            today = date.today()
            start_date = today - timedelta(days=today.weekday())
        
        end_date = start_date + timedelta(days=6)
        
        # 查找该周的回顾
        reviews = storage.get_reviews_by_date_range(start_date, end_date)
        weekly_reviews = [r for r in reviews if isinstance(r, WeeklyReview)]
        
        if not weekly_reviews:
            return False, f"未找到 {start_date} 至 {end_date} 的每周回顾", None
        
        # 取第一个匹配的回顾
        review = weekly_reviews[0]
        
        review_info = {
            "review_id": review.review_id,
            "title": review.title,
            "week_start": review.review_period_start.isoformat(),
            "week_end": review.review_period_end.isoformat(),
            "is_completed": review.is_completed,
            "achievements": review.achievements,
            "challenges": review.challenges,
            "lessons_learned": review.lessons_learned,
            "what_went_well": review.what_went_well,
            "what_could_improve": review.what_could_improve,
            "week_goals_achieved": review.week_goals_achieved,
            "week_goals_missed": review.week_goals_missed,
            "next_week_goals": review.next_week_goals,
            "ratings": {
                "overall_satisfaction": review.overall_satisfaction,
                "productivity_rating": review.productivity_rating,
                "learning_rating": review.learning_rating,
                "work_performance": review.work_performance,
                "personal_development": review.personal_development,
                "health_wellness": review.health_wellness,
                "relationships": review.relationships
            },
            "weekly_score": review.calculate_weekly_score(),
            "goal_completion_rate": review.get_goal_completion_rate(),
            "action_items": [item.to_dict() for item in review.action_items],
            "growth_insights": [insight.to_dict() for insight in review.growth_insights],
            "created_at": review.created_at.isoformat(),
            "updated_at": review.updated_at.isoformat()
        }
        
        return True, f"获取每周回顾成功：{review.title}", review_info
        
    except Exception as e:
        logger.error("Failed to get weekly review", error=str(e))
        return False, f"获取每周回顾时发生错误: {str(e)}", None


def get_recent_weekly_reviews(
    weeks: int = 4,
    config: Optional[PMConfig] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """获取最近几周的回顾摘要
    
    Args:
        weeks: 获取最近几周的回顾（默认4周）
        config: 配置对象
        
    Returns:
        Tuple[成功标志, 消息, 周回顾摘要字典]
    """
    try:
        if weeks <= 0 or weeks > 52:
            return False, "周数必须在1-52之间", None
        
        config = config or PMConfig()
        storage = ReviewStorage(config)
        
        # 获取最近的每周回顾
        days = weeks * 7
        recent_reviews = storage.get_recent_reviews(days, ReviewType.WEEKLY)
        weekly_reviews = [r for r in recent_reviews if isinstance(r, WeeklyReview)]
        
        if not weekly_reviews:
            return False, f"最近 {weeks} 周内没有回顾记录", None
        
        # 按时间排序
        weekly_reviews.sort(key=lambda x: x.review_period_start, reverse=True)
        
        # 生成摘要
        reviews_summary = []
        total_score = 0
        total_goals_achieved = 0
        total_goals_missed = 0
        
        for review in weekly_reviews:
            summary = {
                "review_id": review.review_id,
                "title": review.title,
                "week_start": review.review_period_start.isoformat(),
                "week_end": review.review_period_end.isoformat(),
                "weekly_score": review.calculate_weekly_score(),
                "goal_completion_rate": review.get_goal_completion_rate(),
                "achievements_count": len(review.achievements),
                "challenges_count": len(review.challenges),
                "action_items_count": len(review.action_items),
                "insights_count": len(review.growth_insights),
                "is_completed": review.is_completed
            }
            reviews_summary.append(summary)
            
            total_score += review.calculate_weekly_score()
            total_goals_achieved += len(review.week_goals_achieved)
            total_goals_missed += len(review.week_goals_missed)
        
        # 计算趋势
        avg_score = total_score / len(weekly_reviews)
        total_goals = total_goals_achieved + total_goals_missed
        overall_goal_rate = (total_goals_achieved / total_goals * 100) if total_goals > 0 else 0
        
        # 评分趋势分析
        if len(weekly_reviews) >= 2:
            recent_avg = sum(r.calculate_weekly_score() for r in weekly_reviews[:2]) / 2
            earlier_avg = sum(r.calculate_weekly_score() for r in weekly_reviews[2:]) / len(weekly_reviews[2:]) if len(weekly_reviews) > 2 else recent_avg
            trend = "上升" if recent_avg > earlier_avg + 0.2 else "下降" if recent_avg < earlier_avg - 0.2 else "稳定"
        else:
            trend = "数据不足"
        
        summary_info = {
            "period_weeks": weeks,
            "total_reviews": len(weekly_reviews),
            "reviews": reviews_summary,
            "statistics": {
                "average_weekly_score": round(avg_score, 1),
                "overall_goal_completion_rate": round(overall_goal_rate, 1),
                "total_goals_achieved": total_goals_achieved,
                "total_goals_missed": total_goals_missed,
                "score_trend": trend,
                "most_productive_week": max(weekly_reviews, key=lambda x: x.calculate_weekly_score()).title if weekly_reviews else None
            }
        }
        
        return True, f"获取最近 {weeks} 周回顾摘要成功", summary_info
        
    except Exception as e:
        logger.error("Failed to get recent weekly reviews", weeks=weeks, error=str(e))
        return False, f"获取周回顾摘要时发生错误: {str(e)}", None


# ========== 项目复盘管理工具 ==========

def create_project_retrospective(
    project_name: str,
    project_id: Optional[str] = None,
    project_start_date: Optional[str] = None,  # YYYY-MM-DD
    project_end_date: Optional[str] = None,    # YYYY-MM-DD
    original_timeline_days: Optional[int] = None,
    actual_timeline_days: Optional[int] = None,
    objectives_met: Optional[List[str]] = None,
    objectives_missed: Optional[List[str]] = None,
    achievements: Optional[List[str]] = None,
    challenges: Optional[List[str]] = None,
    lessons_learned: Optional[List[str]] = None,
    what_went_well: Optional[List[str]] = None,
    what_could_improve: Optional[List[str]] = None,
    process_improvements: Optional[List[str]] = None,
    deliverables_quality: int = 3,
    stakeholder_satisfaction: int = 3,
    team_performance: int = 3,
    communication_effectiveness: int = 3,
    collaboration_quality: int = 3,
    risk_management_effectiveness: int = 3,
    config: Optional[PMConfig] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """创建项目复盘
    
    Args:
        project_name: 项目名称
        project_id: 项目ID（可选）
        project_start_date: 项目开始日期
        project_end_date: 项目结束日期
        original_timeline_days: 原计划天数
        actual_timeline_days: 实际用时天数
        objectives_met: 达成的目标
        objectives_missed: 未达成的目标
        achievements: 项目成就
        challenges: 项目挑战
        lessons_learned: 学到的经验教训
        what_went_well: 进展顺利的方面
        what_could_improve: 可以改进的方面
        process_improvements: 过程改进建议
        deliverables_quality: 交付物质量 (1-5)
        stakeholder_satisfaction: 利益相关者满意度 (1-5)
        team_performance: 团队表现 (1-5)
        communication_effectiveness: 沟通有效性 (1-5)
        collaboration_quality: 协作质量 (1-5)
        risk_management_effectiveness: 风险管理有效性 (1-5)
        config: 配置对象
        
    Returns:
        Tuple[成功标志, 消息, 项目复盘信息字典]
    """
    try:
        if not project_name.strip():
            return False, "项目名称不能为空", None
        
        config = config or PMConfig()
        storage = ReviewStorage(config)
        
        # 解析日期
        start_date = None
        end_date = None
        
        if project_start_date:
            try:
                start_date = date.fromisoformat(project_start_date)
            except ValueError:
                return False, "项目开始日期格式无效，请使用YYYY-MM-DD格式", None
        
        if project_end_date:
            try:
                end_date = date.fromisoformat(project_end_date)
            except ValueError:
                return False, "项目结束日期格式无效，请使用YYYY-MM-DD格式", None
        
        # 如果没有提供日期，使用今天作为复盘日期
        if not start_date and not end_date:
            end_date = date.today()
            start_date = end_date
        elif not start_date:
            start_date = end_date
        elif not end_date:
            end_date = start_date
        
        # 创建项目复盘对象
        retrospective = ProjectRetrospective(
            project_name=project_name.strip(),
            project_id=project_id,
            project_start_date=start_date,
            project_end_date=end_date,
            original_timeline=original_timeline_days,
            actual_timeline=actual_timeline_days,
            review_period_start=start_date,
            review_period_end=end_date,
            objectives_met=objectives_met or [],
            objectives_missed=objectives_missed or [],
            achievements=achievements or [],
            challenges=challenges or [],
            lessons_learned=lessons_learned or [],
            what_went_well=what_went_well or [],
            what_could_improve=what_could_improve or [],
            process_improvements=process_improvements or [],
            deliverables_quality=max(1, min(5, deliverables_quality)),
            stakeholder_satisfaction=max(1, min(5, stakeholder_satisfaction)),
            team_performance=max(1, min(5, team_performance)),
            communication_effectiveness=max(1, min(5, communication_effectiveness)),
            collaboration_quality=max(1, min(5, collaboration_quality)),
            risk_management_effectiveness=max(1, min(5, risk_management_effectiveness))
        )
        
        # 保存复盘
        success = storage.save_review(retrospective)
        if success:
            timeline_variance = retrospective.calculate_timeline_variance()
            objective_completion = retrospective.calculate_objective_completion_rate()
            
            retro_info = {
                "review_id": retrospective.review_id,
                "title": retrospective.title,
                "project_name": retrospective.project_name,
                "project_id": retrospective.project_id,
                "project_duration_days": (end_date - start_date).days + 1 if start_date and end_date else 0,
                "timeline_variance_percent": timeline_variance,
                "objective_completion_rate": objective_completion,
                "total_achievements": len(retrospective.achievements),
                "total_challenges": len(retrospective.challenges),
                "total_lessons": len(retrospective.lessons_learned),
                "total_improvements": len(retrospective.process_improvements),
                "quality_ratings": {
                    "deliverables": retrospective.deliverables_quality,
                    "stakeholder_satisfaction": retrospective.stakeholder_satisfaction,
                    "team_performance": retrospective.team_performance,
                    "communication": retrospective.communication_effectiveness,
                    "collaboration": retrospective.collaboration_quality,
                    "risk_management": retrospective.risk_management_effectiveness
                },
                "created_at": retrospective.created_at.isoformat()
            }
            
            logger.info("Project retrospective created via tool function", 
                       review_id=retrospective.review_id,
                       project_name=project_name)
            
            return True, f"项目复盘创建成功：{retrospective.title}", retro_info
        else:
            return False, "保存项目复盘失败", None
            
    except Exception as e:
        logger.error("Failed to create project retrospective", 
                    project_name=project_name, error=str(e))
        return False, f"创建项目复盘时发生错误: {str(e)}", None


# ========== 决策跟踪管理工具 ==========

def track_decision(
    title: str,
    decision_context: str,
    options_considered: List[str],
    chosen_option: str,
    decision_rationale: str,
    expected_outcomes: List[str],
    decision_maker: str = "自己",
    decision_date: Optional[str] = None,  # YYYY-MM-DD
    information_quality: int = 3,
    analysis_depth: int = 3,
    stakeholder_involvement: int = 3,
    time_pressure: int = 3,
    decision_confidence: int = 3,
    tags: Optional[List[str]] = None,
    related_project_id: Optional[str] = None,
    config: Optional[PMConfig] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """跟踪重要决策
    
    Args:
        title: 决策标题
        decision_context: 决策背景
        options_considered: 考虑的选项列表
        chosen_option: 选择的方案
        decision_rationale: 决策理由
        expected_outcomes: 预期结果列表
        decision_maker: 决策者
        decision_date: 决策日期
        information_quality: 信息质量 (1-5)
        analysis_depth: 分析深度 (1-5)
        stakeholder_involvement: 利益相关者参与度 (1-5)
        time_pressure: 时间压力 (1-5)
        decision_confidence: 决策信心 (1-5)
        tags: 标签列表
        related_project_id: 相关项目ID
        config: 配置对象
        
    Returns:
        Tuple[成功标志, 消息, 决策记录信息字典]
    """
    try:
        if not title.strip():
            return False, "决策标题不能为空", None
        
        if not chosen_option.strip():
            return False, "选择的方案不能为空", None
        
        config = config or PMConfig()
        storage = ReviewStorage(config)
        
        # 解析决策日期
        if decision_date:
            try:
                dec_date = date.fromisoformat(decision_date)
            except ValueError:
                return False, "决策日期格式无效，请使用YYYY-MM-DD格式", None
        else:
            dec_date = date.today()
        
        # 创建决策记录
        decision = DecisionReview(
            title=title.strip(),
            decision_context=decision_context,
            options_considered=options_considered,
            chosen_option=chosen_option.strip(),
            decision_rationale=decision_rationale,
            expected_outcomes=expected_outcomes,
            decision_maker=decision_maker,
            decision_date=dec_date,
            information_quality=max(1, min(5, information_quality)),
            analysis_depth=max(1, min(5, analysis_depth)),
            stakeholder_involvement=max(1, min(5, stakeholder_involvement)),
            time_pressure=max(1, min(5, time_pressure)),
            decision_confidence=max(1, min(5, decision_confidence)),
            tags=tags or [],
            related_project_id=related_project_id
        )
        
        # 保存决策记录
        success = storage.save_decision(decision)
        if success:
            decision_info = {
                "decision_id": decision.decision_id,
                "title": decision.title,
                "decision_date": decision.decision_date.isoformat(),
                "decision_maker": decision.decision_maker,
                "chosen_option": decision.chosen_option,
                "options_count": len(decision.options_considered),
                "expected_outcomes_count": len(decision.expected_outcomes),
                "decision_quality_score": decision.calculate_decision_quality_score(),
                "process_ratings": {
                    "information_quality": decision.information_quality,
                    "analysis_depth": decision.analysis_depth,
                    "stakeholder_involvement": decision.stakeholder_involvement,
                    "time_pressure": decision.time_pressure,
                    "decision_confidence": decision.decision_confidence
                },
                "tags": decision.tags,
                "related_project_id": decision.related_project_id,
                "created_at": decision.created_at.isoformat()
            }
            
            logger.info("Decision tracked via tool function", 
                       decision_id=decision.decision_id,
                       title=title)
            
            return True, f"决策跟踪创建成功：{decision.title}", decision_info
        else:
            return False, "保存决策记录失败", None
            
    except Exception as e:
        logger.error("Failed to track decision", title=title, error=str(e))
        return False, f"跟踪决策时发生错误: {str(e)}", None


def evaluate_decision_outcome(
    decision_id: str,
    actual_outcomes: List[str],
    outcome_rating: str,  # excellent/good/neutral/poor/unknown
    key_learnings: Optional[List[str]] = None,
    improvement_areas: Optional[List[str]] = None,
    future_considerations: Optional[List[str]] = None,
    config: Optional[PMConfig] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """评估决策结果
    
    Args:
        decision_id: 决策ID
        actual_outcomes: 实际结果列表
        outcome_rating: 结果评价 (excellent/good/neutral/poor/unknown)
        key_learnings: 关键学习
        improvement_areas: 改进领域
        future_considerations: 未来考虑事项
        config: 配置对象
        
    Returns:
        Tuple[成功标志, 消息, 决策评估信息字典]
    """
    try:
        if not decision_id.strip():
            return False, "决策ID不能为空", None
        
        config = config or PMConfig()
        storage = ReviewStorage(config)
        
        # 获取决策记录
        decision = storage.get_decision(decision_id)
        if not decision:
            return False, f"未找到ID为 {decision_id} 的决策记录", None
        
        # 验证结果评价
        try:
            outcome_enum = DecisionOutcome(outcome_rating.lower())
        except ValueError:
            return False, f"无效的结果评价：{outcome_rating}，支持的选项：excellent/good/neutral/poor/unknown", None
        
        # 评估决策结果
        decision.evaluate_outcome(
            actual_outcomes=actual_outcomes,
            outcome_rating=outcome_enum,
            key_learnings=key_learnings or []
        )
        
        # 更新改进领域和未来考虑
        if improvement_areas:
            decision.improvement_areas.extend(improvement_areas)
        
        if future_considerations:
            decision.future_considerations.extend(future_considerations)
        
        # 保存更新
        success = storage.save_decision(decision)
        if success:
            evaluation_info = {
                "decision_id": decision.decision_id,
                "title": decision.title,
                "decision_date": decision.decision_date.isoformat(),
                "evaluation_date": decision.outcome_evaluation_date.isoformat(),
                "outcome_rating": decision.outcome_rating.value,
                "actual_outcomes": decision.actual_outcomes,
                "expected_outcomes": decision.expected_outcomes,
                "key_learnings": decision.key_learnings,
                "improvement_areas": decision.improvement_areas,
                "future_considerations": decision.future_considerations,
                "decision_quality_score": decision.calculate_decision_quality_score(),
                "updated_at": decision.updated_at.isoformat()
            }
            
            logger.info("Decision outcome evaluated", 
                       decision_id=decision_id,
                       outcome_rating=outcome_rating)
            
            return True, f"决策结果评估完成：{decision.title}", evaluation_info
        else:
            return False, "保存决策评估失败", None
            
    except Exception as e:
        logger.error("Failed to evaluate decision outcome", 
                    decision_id=decision_id, error=str(e))
        return False, f"评估决策结果时发生错误: {str(e)}", None


# ========== 成长洞察管理工具 ==========

def add_growth_insight(
    title: str,
    description: str,
    key_learning: str,
    growth_area: str = "other",  # technical_skills/leadership/communication/time_management/etc.
    confidence_level: int = 3,
    actionable_steps: Optional[List[str]] = None,
    tags: Optional[List[str]] = None,
    source_review_id: Optional[str] = None,
    config: Optional[PMConfig] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """添加成长洞察
    
    Args:
        title: 洞察标题
        description: 洞察描述
        key_learning: 关键学习
        growth_area: 成长领域
        confidence_level: 信心程度 (1-5)
        actionable_steps: 可行动步骤
        tags: 标签
        source_review_id: 来源回顾ID
        config: 配置对象
        
    Returns:
        Tuple[成功标志, 消息, 成长洞察信息字典]
    """
    try:
        if not title.strip():
            return False, "洞察标题不能为空", None
        
        if not key_learning.strip():
            return False, "关键学习不能为空", None
        
        config = config or PMConfig()
        storage = ReviewStorage(config)
        
        # 验证成长领域
        try:
            growth_area_enum = GrowthArea(growth_area.lower())
        except ValueError:
            valid_areas = [area.value for area in GrowthArea]
            return False, f"无效的成长领域：{growth_area}，支持的选项：{', '.join(valid_areas)}", None
        
        # 创建成长洞察
        insight = GrowthInsight(
            title=title.strip(),
            description=description,
            key_learning=key_learning.strip(),
            growth_area=growth_area_enum,
            confidence_level=max(1, min(5, confidence_level)),
            actionable_steps=actionable_steps or [],
            tags=tags or [],
            source_review_id=source_review_id
        )
        
        # 保存洞察
        success = storage.save_insight(insight)
        if success:
            insight_info = {
                "insight_id": insight.insight_id,
                "title": insight.title,
                "description": insight.description,
                "key_learning": insight.key_learning,
                "growth_area": insight.growth_area.value,
                "confidence_level": insight.confidence_level,
                "actionable_steps": insight.actionable_steps,
                "tags": insight.tags,
                "source_review_id": insight.source_review_id,
                "created_at": insight.created_at.isoformat()
            }
            
            logger.info("Growth insight added via tool function", 
                       insight_id=insight.insight_id,
                       title=title,
                       growth_area=growth_area)
            
            return True, f"成长洞察添加成功：{insight.title}", insight_info
        else:
            return False, "保存成长洞察失败", None
            
    except Exception as e:
        logger.error("Failed to add growth insight", title=title, error=str(e))
        return False, f"添加成长洞察时发生错误: {str(e)}", None


# ========== 分析和统计工具 ==========

def get_review_statistics(
    days: int = 90,
    config: Optional[PMConfig] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """获取回顾统计信息
    
    Args:
        days: 统计天数（默认90天）
        config: 配置对象
        
    Returns:
        Tuple[成功标志, 消息, 统计信息字典]
    """
    try:
        if days <= 0 or days > 365:
            return False, "统计天数必须在1-365天之间", None
        
        config = config or PMConfig()
        storage = ReviewStorage(config)
        
        statistics = storage.get_review_statistics(days)
        
        if statistics["total_reviews"] == 0:
            return False, f"过去 {days} 天内没有回顾记录", None
        
        # 添加额外分析
        stats_info = {
            **statistics,
            "analysis_period_days": days,
            "daily_average_reviews": round(statistics["total_reviews"] / days, 2),
            "productivity_trend": "高" if statistics["average_ratings"]["productivity"] >= 4 
                                else "中" if statistics["average_ratings"]["productivity"] >= 3 
                                else "低",
            "learning_trend": "高" if statistics["average_ratings"]["learning"] >= 4 
                            else "中" if statistics["average_ratings"]["learning"] >= 3 
                            else "低"
        }
        
        return True, f"过去 {days} 天回顾统计分析完成", stats_info
        
    except Exception as e:
        logger.error("Failed to get review statistics", days=days, error=str(e))
        return False, f"获取回顾统计时发生错误: {str(e)}", None


def get_decision_quality_analysis(
    months: int = 6,
    config: Optional[PMConfig] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """获取决策质量分析
    
    Args:
        months: 分析月数（默认6个月）
        config: 配置对象
        
    Returns:
        Tuple[成功标志, 消息, 决策质量分析字典]
    """
    try:
        if months <= 0 or months > 24:
            return False, "分析月数必须在1-24之间", None
        
        config = config or PMConfig()
        storage = ReviewStorage(config)
        
        analysis = storage.get_decision_quality_trends(months)
        
        if analysis["total_decisions"] == 0:
            return False, f"过去 {months} 个月内没有决策记录", None
        
        # 添加改进建议
        recommendations = []
        if analysis["evaluation_rate"] < 50:
            recommendations.append("建议对更多历史决策进行结果评估")
        if analysis["average_quality_score"] < 3.5:
            recommendations.append("考虑改进决策过程，提高信息收集和分析质量")
        if analysis["pending_evaluations"] > 5:
            recommendations.append(f"有 {analysis['pending_evaluations']} 个决策待评估，建议及时跟进")
        
        analysis["recommendations"] = recommendations
        analysis["analysis_period_months"] = months
        
        return True, f"过去 {months} 个月决策质量分析完成", analysis
        
    except Exception as e:
        logger.error("Failed to get decision quality analysis", months=months, error=str(e))
        return False, f"获取决策质量分析时发生错误: {str(e)}", None


def get_growth_insights_summary(
    months: int = 12,
    config: Optional[PMConfig] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """获取成长洞察摘要
    
    Args:
        months: 分析月数（默认12个月）
        config: 配置对象
        
    Returns:
        Tuple[成功标志, 消息, 成长洞察摘要字典]
    """
    try:
        if months <= 0 or months > 24:
            return False, "分析月数必须在1-24之间", None
        
        config = config or PMConfig()
        storage = ReviewStorage(config)
        
        summary = storage.get_growth_insights_analysis(months)
        
        if summary["total_insights"] == 0:
            return False, f"过去 {months} 个月内没有成长洞察记录", None
        
        # 添加发展建议
        recommendations = []
        if summary["average_confidence"] < 3:
            recommendations.append("建议提高对洞察的信心程度，可能需要更深入的思考和验证")
        
        if summary["most_productive_area"]:
            recommendations.append(f"在 {summary['most_productive_area']} 领域表现突出，可以考虑深度发展")
        
        # 找出薄弱领域
        all_areas = [area.value for area in GrowthArea]
        covered_areas = list(summary["insights_by_area"].keys())
        missing_areas = [area for area in all_areas if area not in covered_areas]
        
        if missing_areas:
            recommendations.append(f"考虑在以下领域加强关注：{', '.join(missing_areas[:3])}")
        
        summary["recommendations"] = recommendations
        summary["analysis_period_months"] = months
        
        return True, f"过去 {months} 个月成长洞察分析完成", summary
        
    except Exception as e:
        logger.error("Failed to get growth insights summary", months=months, error=str(e))
        return False, f"获取成长洞察摘要时发生错误: {str(e)}", None