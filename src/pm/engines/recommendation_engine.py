"""智能推荐引擎 - 基于多书籍理论的任务优先级推荐系统

集成理论框架：
- 《衡量一切》(OKR/WIG) - 目标对齐度评估
- 《高效执行的4个原则》(4DX) - 执行优先级计算
- 《全力以赴》- 精力水平匹配
- 《原子习惯》- 习惯关联分析
- 《搞定》(GTD) - 下一步行动原则
- 《精要主义》- 重要性评估模型
"""

import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import structlog

from pm.models.task import Task, TaskStatus, TaskContext, TaskPriority, EnergyLevel
from pm.core.config import PMConfig

logger = structlog.get_logger()


class TheoryFramework(Enum):
    """理论框架枚举"""
    OKR_WIG = "okr_wig"  # 《衡量一切》- 目标对齐
    FOUR_DX = "4dx"  # 《高效执行的4个原则》
    FULL_ENGAGEMENT = "full_engagement"  # 《全力以赴》
    ATOMIC_HABITS = "atomic_habits"  # 《原子习惯》
    GTD = "gtd"  # 《搞定》
    ESSENTIALISM = "essentialism"  # 《精要主义》


@dataclass
class RecommendationScore:
    """推荐评分详情"""
    total_score: float
    framework_scores: Dict[TheoryFramework, float]
    reasoning: List[str]
    confidence: float
    urgency_factor: float
    energy_match: float


@dataclass
class UserPreferences:
    """用户偏好配置"""
    framework_weights: Dict[TheoryFramework, float]
    energy_patterns: Dict[str, float]  # 时间段 -> 精力水平
    context_preferences: Dict[TaskContext, float]
    goal_alignment_weight: float = 0.25
    execution_weight: float = 0.20
    energy_weight: float = 0.20
    habits_weight: float = 0.15
    gtd_weight: float = 0.10
    essentialism_weight: float = 0.10


class IntelligentRecommendationEngine:
    """智能推荐引擎 - US-011核心实现"""
    
    def __init__(self, config: PMConfig):
        self.config = config
        self.user_preferences = self._load_user_preferences()
        self._initialize_frameworks()
        
        # 集成偏好学习系统（US-013）
        from pm.engines.preference_learning import UserPreferenceLearning
        self.preference_learning = UserPreferenceLearning(config)
        
        # 应用学习到的偏好
        self._apply_learned_preferences()
        
        logger.info("Intelligent recommendation engine initialized")
    
    def _load_user_preferences(self) -> UserPreferences:
        """加载用户偏好配置"""
        
        # 默认理论框架权重
        default_weights = {
            TheoryFramework.OKR_WIG: 0.25,        # 目标对齐最重要
            TheoryFramework.FOUR_DX: 0.20,        # 执行效率
            TheoryFramework.FULL_ENGAGEMENT: 0.20, # 精力匹配
            TheoryFramework.ATOMIC_HABITS: 0.15,   # 习惯建立
            TheoryFramework.GTD: 0.10,             # GTD原则
            TheoryFramework.ESSENTIALISM: 0.10     # 精要主义
        }
        
        # 默认精力模式（24小时制）
        default_energy_patterns = {
            "morning": 0.9,    # 6-12点高精力
            "afternoon": 0.7,  # 12-17点中等精力
            "evening": 0.5,    # 17-21点较低精力
            "night": 0.3       # 21-6点低精力
        }
        
        # 默认情境偏好
        default_context_preferences = {
            TaskContext.COMPUTER: 0.9,
            TaskContext.FOCUS: 0.8,
            TaskContext.OFFICE: 0.7,
            TaskContext.HOME: 0.6,
            TaskContext.MEETING: 0.5,
            TaskContext.PHONE: 0.4,
            TaskContext.ERRANDS: 0.3,
            TaskContext.ONLINE: 0.8,
            TaskContext.READING: 0.7
        }
        
        return UserPreferences(
            framework_weights=default_weights,
            energy_patterns=default_energy_patterns,
            context_preferences=default_context_preferences
        )
    
    def _initialize_frameworks(self) -> None:
        """初始化各理论框架的评估器"""
        self.frameworks = {
            TheoryFramework.OKR_WIG: self._evaluate_okr_alignment,
            TheoryFramework.FOUR_DX: self._evaluate_4dx_priority,
            TheoryFramework.FULL_ENGAGEMENT: self._evaluate_energy_match,
            TheoryFramework.ATOMIC_HABITS: self._evaluate_habit_building,
            TheoryFramework.GTD: self._evaluate_gtd_principles,
            TheoryFramework.ESSENTIALISM: self._evaluate_essentialism
        }
    
    def recommend_tasks(self, 
                       tasks: List[Task],
                       current_context: Optional[Dict[str, Any]] = None,
                       max_recommendations: int = 5) -> List[Tuple[Task, RecommendationScore]]:
        """生成智能任务推荐
        
        Args:
            tasks: 待推荐的任务列表
            current_context: 当前用户情境
            max_recommendations: 最大推荐数量
            
        Returns:
            排序后的任务推荐列表，包含评分详情
        """
        
        logger.info("Generating intelligent recommendations", 
                   task_count=len(tasks),
                   max_recs=max_recommendations)
        
        recommendations = []
        
        for task in tasks:
            score = self._calculate_recommendation_score(task, current_context)
            recommendations.append((task, score))
        
        # 按总分排序
        recommendations.sort(key=lambda x: x[1].total_score, reverse=True)
        
        # 返回前N个推荐
        top_recommendations = recommendations[:max_recommendations]
        
        logger.info("Recommendations generated",
                   total_evaluated=len(tasks),
                   top_recommendations=len(top_recommendations))
        
        return top_recommendations
    
    def _calculate_recommendation_score(self, 
                                      task: Task, 
                                      current_context: Optional[Dict[str, Any]] = None) -> RecommendationScore:
        """计算任务的推荐评分"""
        
        framework_scores = {}
        reasoning = []
        
        # 评估各理论框架
        for framework, evaluator in self.frameworks.items():
            score = evaluator(task, current_context)
            framework_scores[framework] = score
            
            if score > 0.7:
                reasoning.append(f"{framework.value}理论评分高({score:.2f})")
        
        # 计算加权总分
        total_score = sum(
            score * self.user_preferences.framework_weights[framework]
            for framework, score in framework_scores.items()
        )
        
        # 计算紧迫性因子
        urgency_factor = self._calculate_urgency_factor(task)
        
        # 计算精力匹配度
        energy_match = self._calculate_energy_match(task, current_context)
        
        # 应用额外因子
        total_score = total_score * (1 + urgency_factor * 0.3) * (1 + energy_match * 0.2)
        
        # 计算置信度
        confidence = self._calculate_confidence(framework_scores, task)
        
        return RecommendationScore(
            total_score=min(total_score, 10.0),  # 限制最高分为10
            framework_scores=framework_scores,
            reasoning=reasoning,
            confidence=confidence,
            urgency_factor=urgency_factor,
            energy_match=energy_match
        )
    
    def _evaluate_okr_alignment(self, task: Task, context: Optional[Dict[str, Any]] = None) -> float:
        """《衡量一切》- OKR/WIG目标对齐度评估
        
        评估任务与关键目标的对齐程度
        """
        score = 0.5  # 基础分
        
        # 项目关联加分
        if task.project_name:
            score += 0.3
        
        # 优先级对齐
        if task.priority == TaskPriority.HIGH:
            score += 0.2
        elif task.priority == TaskPriority.MEDIUM:
            score += 0.1
        
        # 关键词匹配（模拟目标关键词）
        goal_keywords = ["目标", "关键", "重要", "核心", "战略", "优先"]
        task_text = f"{task.title} {task.description or ''}".lower()
        
        for keyword in goal_keywords:
            if keyword in task_text:
                score += 0.1
                break
        
        return min(score, 1.0)
    
    def _evaluate_4dx_priority(self, task: Task, context: Optional[Dict[str, Any]] = None) -> float:
        """《高效执行的4个原则》- 4DX执行优先级
        
        评估任务的执行重要性和可行性
        """
        score = 0.4  # 基础分
        
        # 预估时长加分（较短任务更容易执行）
        if task.estimated_duration:
            if task.estimated_duration <= 30:  # 30分钟内
                score += 0.3
            elif task.estimated_duration <= 60:  # 1小时内
                score += 0.2
            elif task.estimated_duration <= 120:  # 2小时内
                score += 0.1
        
        # 下一步行动状态加分
        if task.status == TaskStatus.NEXT_ACTION:
            score += 0.2
        
        # 明确性加分
        if task.description and len(task.description) > 10:
            score += 0.1
        
        return min(score, 1.0)
    
    def _evaluate_energy_match(self, task: Task, context: Optional[Dict[str, Any]] = None) -> float:
        """《全力以赴》- 精力水平匹配评估
        
        评估任务精力需求与当前精力的匹配度
        """
        score = 0.5  # 基础分
        
        current_hour = datetime.now().hour
        current_energy = self._get_current_energy_level(current_hour)
        
        if task.energy_required:
            energy_mapping = {
                EnergyLevel.LOW: 0.3,
                EnergyLevel.MEDIUM: 0.6,
                EnergyLevel.HIGH: 0.9
            }
            
            required_energy = energy_mapping[task.energy_required]
            
            # 精力匹配度计算
            if required_energy <= current_energy:
                # 精力充足，额外加分
                score += 0.4
            else:
                # 精力不足，减分
                energy_deficit = required_energy - current_energy
                score -= energy_deficit * 0.3
        else:
            # 未设置精力需求，给予中等分数
            score += 0.2
        
        return max(min(score, 1.0), 0.0)
    
    def _evaluate_habit_building(self, task: Task, context: Optional[Dict[str, Any]] = None) -> float:
        """《原子习惯》- 习惯关联分析
        
        评估任务对习惯建立的贡献
        """
        score = 0.3  # 基础分
        
        # 重复性任务加分
        habit_keywords = ["每日", "定期", "习惯", "练习", "学习", "锻炼", "复习"]
        task_text = f"{task.title} {task.description or ''}".lower()
        
        for keyword in habit_keywords:
            if keyword in task_text:
                score += 0.2
                break
        
        # 小步骤任务加分（更容易养成习惯）
        if task.estimated_duration and task.estimated_duration <= 25:  # 番茄钟时长
            score += 0.3
        
        # 明确的时间设置加分
        if task.due_date:
            score += 0.2
        
        return min(score, 1.0)
    
    def _evaluate_gtd_principles(self, task: Task, context: Optional[Dict[str, Any]] = None) -> float:
        """《搞定》- GTD原则评估
        
        评估任务符合GTD方法论的程度
        """
        score = 0.4  # 基础分
        
        # 明确的下一步行动
        if task.status == TaskStatus.NEXT_ACTION:
            score += 0.3
        
        # 情境设置
        if task.context:
            score += 0.2
        
        # 项目关联
        if task.project_name:
            score += 0.1
        
        return min(score, 1.0)
    
    def _evaluate_essentialism(self, task: Task, context: Optional[Dict[str, Any]] = None) -> float:
        """《精要主义》- 重要性评估
        
        评估任务的本质重要性
        """
        score = 0.3  # 基础分
        
        # 高优先级任务
        if task.priority == TaskPriority.HIGH:
            score += 0.4
        elif task.priority == TaskPriority.MEDIUM:
            score += 0.2
        
        # 影响力关键词
        impact_keywords = ["重要", "关键", "核心", "必须", "critical", "important"]
        task_text = f"{task.title} {task.description or ''}".lower()
        
        for keyword in impact_keywords:
            if keyword in task_text:
                score += 0.3
                break
        
        return min(score, 1.0)
    
    def _get_current_energy_level(self, hour: int) -> float:
        """获取当前时间的精力水平"""
        if 6 <= hour < 12:
            return self.user_preferences.energy_patterns["morning"]
        elif 12 <= hour < 17:
            return self.user_preferences.energy_patterns["afternoon"] 
        elif 17 <= hour < 21:
            return self.user_preferences.energy_patterns["evening"]
        else:
            return self.user_preferences.energy_patterns["night"]
    
    def _calculate_urgency_factor(self, task: Task) -> float:
        """计算紧迫性因子"""
        if not task.due_date:
            return 0.0
        
        days_until_due = (task.due_date.date() - datetime.now().date()).days
        
        if days_until_due <= 0:
            return 1.0  # 已过期
        elif days_until_due == 1:
            return 0.8  # 明天截止
        elif days_until_due <= 3:
            return 0.6  # 3天内
        elif days_until_due <= 7:
            return 0.3  # 一周内
        else:
            return 0.1  # 较远的截止日期
    
    def _calculate_energy_match(self, task: Task, context: Optional[Dict[str, Any]] = None) -> float:
        """计算精力匹配度"""
        current_hour = datetime.now().hour
        current_energy = self._get_current_energy_level(current_hour)
        
        if not task.energy_required:
            return 0.5  # 中性匹配
        
        energy_values = {
            EnergyLevel.LOW: 0.3,
            EnergyLevel.MEDIUM: 0.6, 
            EnergyLevel.HIGH: 0.9
        }
        
        required_energy = energy_values[task.energy_required]
        
        # 计算匹配度
        if required_energy <= current_energy:
            return min(current_energy / required_energy, 1.0)
        else:
            return max(current_energy / required_energy - 0.2, 0.0)
    
    def _calculate_confidence(self, framework_scores: Dict[TheoryFramework, float], task: Task) -> float:
        """计算推荐置信度"""
        
        # 基于框架评分的一致性
        scores = list(framework_scores.values())
        avg_score = sum(scores) / len(scores)
        variance = sum((s - avg_score) ** 2 for s in scores) / len(scores)
        consistency = 1.0 - min(variance, 1.0)
        
        # 基于任务信息完整性
        completeness = 0.0
        if task.description:
            completeness += 0.2
        if task.context:
            completeness += 0.2
        if task.priority != TaskPriority.MEDIUM:  # 非默认优先级
            completeness += 0.2
        if task.estimated_duration:
            completeness += 0.2
        if task.energy_required:
            completeness += 0.2
        
        # 综合置信度
        confidence = (consistency * 0.6 + completeness * 0.4)
        
        return min(confidence, 1.0)
    
    def get_framework_explanations(self) -> Dict[TheoryFramework, str]:
        """获取各理论框架的说明"""
        return {
            TheoryFramework.OKR_WIG: "目标对齐度 - 任务与关键目标的匹配程度",
            TheoryFramework.FOUR_DX: "执行效率 - 任务的可执行性和重要性",
            TheoryFramework.FULL_ENGAGEMENT: "精力匹配 - 任务精力需求与当前状态的匹配",
            TheoryFramework.ATOMIC_HABITS: "习惯建立 - 任务对养成良好习惯的贡献",
            TheoryFramework.GTD: "GTD原则 - 符合Getting Things Done方法论的程度",
            TheoryFramework.ESSENTIALISM: "本质重要性 - 任务的真正价值和影响力"
        }
    
    def _apply_learned_preferences(self) -> None:
        """应用学习到的用户偏好（US-013）"""
        
        learned_prefs = self.preference_learning.get_learned_preferences()
        if not learned_prefs:
            logger.debug("No learned preferences available")
            return
        
        # 应用学习到的框架权重
        if 'framework_weights' in learned_prefs:
            framework_weights = learned_prefs['framework_weights']
            
            for framework_key, weight in framework_weights.items():
                # 转换字符串键为枚举
                try:
                    framework_enum = TheoryFramework(framework_key)
                    self.user_preferences.framework_weights[framework_enum] = weight
                except ValueError:
                    continue
            
            logger.info("Applied learned framework weights",
                       weights=framework_weights)
        
        # 应用学习到的情境偏好
        if 'context_preferences' in learned_prefs:
            context_prefs = learned_prefs['context_preferences']
            
            for context_key, preference in context_prefs.items():
                try:
                    context_enum = TaskContext(context_key)
                    self.user_preferences.context_preferences[context_enum] = preference
                except ValueError:
                    continue
            
            logger.info("Applied learned context preferences",
                       contexts=len(context_prefs))
    
    def record_user_choice(self, 
                          chosen_task: Task,
                          recommendations: List[Tuple[Task, Any]]) -> None:
        """记录用户选择用于学习（US-013核心功能）"""
        
        # 找到用户选择的任务在推荐列表中的位置
        recommendation_rank = None
        recommendation_score = None
        framework_scores = {}
        
        for rank, (task, score) in enumerate(recommendations, 1):
            if task.id == chosen_task.id:
                recommendation_rank = rank
                recommendation_score = score.total_score
                # 转换框架评分为字符串键
                framework_scores = {
                    framework.value: score
                    for framework, score in score.framework_scores.items()
                }
                break
        
        if recommendation_rank is not None:
            self.preference_learning.record_user_choice(
                task=chosen_task,
                recommendation_rank=recommendation_rank,
                recommendation_score=recommendation_score,
                framework_scores=framework_scores
            )
            
            logger.info("User choice recorded for learning",
                       task=chosen_task.title[:30],
                       rank=recommendation_rank)
        else:
            logger.warning("User chose task not in recommendations",
                          task=chosen_task.title[:30])
    
    def get_learning_metrics(self) -> Dict[str, Any]:
        """获取学习指标（US-013验收标准）"""
        return self.preference_learning.get_learning_metrics()
    
    def update_user_preferences(self, feedback: Dict[str, Any]) -> None:
        """根据用户反馈更新偏好设置"""
        # 这个方法现在通过偏好学习系统实现
        logger.info("User preferences update requested", feedback=feedback)
        
        # 重新应用学习到的偏好
        self._apply_learned_preferences()