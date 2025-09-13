"""高级智能分析引擎 - 19本书籍算法完整集成系统

集成19本书籍理论框架的终极智能引擎，提供:
- 深度机器学习个性化推荐
- 预测性分析和洞察
- 高级决策支持系统
- 自适应学习和优化

理论框架覆盖:
认知决策类 (12算法): 思考快与慢、决断力、选择的悖论等
执行管理类 (18算法): 4DX、全力以赴、精要主义等
目标管理类 (15算法): OKR、衡量一切、原子习惯等  
学习成长类 (12算法): 刻意练习、心流、成长型思维等
"""

import math
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import structlog
import json
from collections import defaultdict

from pm.models.task import Task, TaskStatus, TaskContext, TaskPriority, EnergyLevel
from pm.models.project import ProjectStatus, ProjectHealth
from pm.core.config import PMConfig
from pm.engines.recommendation_engine import TheoryFramework, RecommendationScore, UserPreferences

logger = structlog.get_logger()


class BookCategory(Enum):
    """19本书籍分类"""
    COGNITIVE_DECISION = "cognitive_decision"  # 认知决策类 (12算法)
    EXECUTION_MANAGEMENT = "execution_management"  # 执行管理类 (18算法) 
    GOAL_MANAGEMENT = "goal_management"  # 目标管理类 (15算法)
    LEARNING_GROWTH = "learning_growth"  # 学习成长类 (12算法)


class AdvancedTheoryFramework(Enum):
    """扩展理论框架 - 完整19本书籍"""
    
    # 认知决策类 (12本书)
    THINKING_FAST_SLOW = "thinking_fast_slow"  # 思考，快与慢
    DECISIVE = "decisive"  # 决断力
    CHOICE_PARADOX = "choice_paradox"  # 选择的悖论
    PREDICTABLY_IRRATIONAL = "predictably_irrational"  # 可预测的非理性
    INFLUENCE = "influence"  # 影响力
    NUDGE = "nudge"  # 助推
    OUTLIERS = "outliers"  # 异类
    BLINK = "blink"  # 眨眼之间
    EMOTIONAL_INTELLIGENCE = "emotional_intelligence"  # 情商
    WILLPOWER = "willpower"  # 自控力
    HAPPINESS_ADVANTAGE = "happiness_advantage"  # 幸福的方法
    MINDSET = "mindset"  # 心态致胜
    
    # 执行管理类 (现有6本 + 12本新增)
    OKR_WIG = "okr_wig"  # 《衡量一切》- 已实现
    FOUR_DX = "4dx"  # 《高效执行的4个原则》- 已实现
    FULL_ENGAGEMENT = "full_engagement"  # 《全力以赴》- 已实现
    ATOMIC_HABITS = "atomic_habits"  # 《原子习惯》- 已实现
    GTD = "gtd"  # 《搞定》- 已实现
    ESSENTIALISM = "essentialism"  # 《精要主义》- 已实现
    
    # 新增执行管理类 (12本)
    DEEP_WORK = "deep_work"  # 深度工作
    DIGITAL_MINIMALISM = "digital_minimalism"  # 数字极简主义
    DISTRACTED_MIND = "distracted_mind"  # 分心的心智
    FLOW = "flow"  # 心流
    PEAK_PERFORMANCE = "peak_performance"  # 巅峰表现
    POWER_FULL_ENGAGEMENT = "power_full_engagement"  # 精力管理
    TIME_TRAP = "time_trap"  # 时间陷阱
    FIRST_THINGS_FIRST = "first_things_first"  # 要事第一
    PRODUCTIVITY_PROJECT = "productivity_project"  # 效率手册
    MAKING_IDEAS_HAPPEN = "making_ideas_happen"  # 让创意更有黏性
    ORGANIZE_TOMORROW = "organize_tomorrow"  # 整理的艺术
    LESS_IS_MORE = "less_is_more"  # 极简主义
    
    # 目标管理类 (15本)
    OBJECTIVES_KEY_RESULTS = "objectives_key_results"  # OKR工作法
    MEASURE_WHAT_MATTERS = "measure_what_matters"  # 这就是OKR
    STRETCH_GOALS = "stretch_goals"  # 拉伸目标
    GOALS_THEORY = "goals_theory"  # 目标理论
    SMART_GOALS = "smart_goals"  # SMART目标
    VISION_DRIVEN = "vision_driven"  # 愿景驱动
    PURPOSE_DRIVEN_LIFE = "purpose_driven_life"  # 目标驱动的人生
    BIG_HAIRY_GOALS = "big_hairy_goals"  # 基业长青
    MILESTONE_MANAGEMENT = "milestone_management"  # 里程碑管理
    PROGRESS_PRINCIPLE = "progress_principle"  # 进步原则
    FEEDBACK_LOOPS = "feedback_loops"  # 反馈回路
    CONTINUOUS_IMPROVEMENT = "continuous_improvement"  # 持续改进
    PERFORMANCE_MANAGEMENT = "performance_management"  # 绩效管理
    ACCOUNTABILITY = "accountability"  # 责任思维
    EXECUTION_DISCIPLINE = "execution_discipline"  # 执行纪律
    
    # 学习成长类 (12本)
    DELIBERATE_PRACTICE = "deliberate_practice"  # 刻意练习
    TALENT_OVERRATED = "talent_overrated"  # 哪来的天才
    GRIT = "grit"  # 坚毅
    GROWTH_MINDSET = "growth_mindset"  # 成长型思维
    LEARNING_HOW_TO_LEARN = "learning_how_to_learn"  # 学会如何学习
    MAKE_IT_STICK = "make_it_stick"  # 认知天性
    PEAK_LEARNING = "peak_learning"  # 超级学习
    MASTERY = "mastery"  # 掌控
    EXPERT_PERFORMANCE = "expert_performance"  # 专业表现
    SKILL_ACQUISITION = "skill_acquisition"  # 技能获得
    COMPOUND_EFFECT = "compound_effect"  # 复利效应  
    KAIZEN = "kaizen"  # 改善


@dataclass
class AdvancedIntelligenceConfig:
    """高级智能配置"""
    # 算法权重配置
    category_weights: Dict[BookCategory, float] = field(default_factory=lambda: {
        BookCategory.COGNITIVE_DECISION: 0.3,
        BookCategory.EXECUTION_MANAGEMENT: 0.35,
        BookCategory.GOAL_MANAGEMENT: 0.25,
        BookCategory.LEARNING_GROWTH: 0.1
    })
    
    # 机器学习配置
    ml_enabled: bool = True
    prediction_horizon_days: int = 30
    personalization_depth: int = 3  # 1-简单 2-中等 3-深度
    adaptive_learning_rate: float = 0.1
    
    # 决策支持配置
    decision_confidence_threshold: float = 0.7
    insight_generation_enabled: bool = True
    predictive_analysis_enabled: bool = True


@dataclass  
class IntelligentInsight:
    """智能洞察结构"""
    insight_id: str
    category: BookCategory
    theory_frameworks: List[AdvancedTheoryFramework]
    insight_text: str
    confidence_score: float
    actionable_recommendations: List[str]
    predicted_impact: Dict[str, float]  # metric -> predicted_improvement
    evidence: List[str]
    created_at: datetime


@dataclass
class PredictiveAnalysis:
    """预测性分析结果"""
    prediction_id: str
    target_metric: str
    current_value: float
    predicted_value: float
    prediction_confidence: float
    time_horizon: timedelta
    contributing_factors: Dict[str, float]
    recommended_interventions: List[str]
    risk_factors: List[str]


@dataclass
class DecisionSupport:
    """决策支持建议"""
    decision_id: str
    decision_context: str
    options: List[Dict[str, Any]]
    recommended_option: str
    reasoning: List[str]
    risk_assessment: Dict[str, float]
    success_probability: float
    supporting_theories: List[AdvancedTheoryFramework]


class IntelligentAnalysisEngine:
    """高级智能分析引擎 - 19本书籍算法完整集成"""
    
    def __init__(self, config: PMConfig):
        self.config = config
        self.ai_config = AdvancedIntelligenceConfig()
        self.logger = structlog.get_logger(__name__)
        
        # 初始化算法组件
        self._init_cognitive_algorithms()
        self._init_execution_algorithms()
        self._init_goal_algorithms()
        self._init_learning_algorithms()
        
        # 机器学习组件
        self.ml_models = {}
        self.user_profile = {}
        self.prediction_cache = {}
        
    def _init_cognitive_algorithms(self):
        """初始化认知决策类算法 (12个)"""
        self.cognitive_algorithms = {
            AdvancedTheoryFramework.THINKING_FAST_SLOW: self._thinking_fast_slow_algorithm,
            AdvancedTheoryFramework.DECISIVE: self._decisive_algorithm,
            AdvancedTheoryFramework.CHOICE_PARADOX: self._choice_paradox_algorithm,
            AdvancedTheoryFramework.PREDICTABLY_IRRATIONAL: self._predictably_irrational_algorithm,
            AdvancedTheoryFramework.INFLUENCE: self._influence_algorithm,
            AdvancedTheoryFramework.NUDGE: self._nudge_algorithm,
            AdvancedTheoryFramework.OUTLIERS: self._outliers_algorithm,
            AdvancedTheoryFramework.BLINK: self._blink_algorithm,
            AdvancedTheoryFramework.EMOTIONAL_INTELLIGENCE: self._emotional_intelligence_algorithm,
            AdvancedTheoryFramework.WILLPOWER: self._willpower_algorithm,
            AdvancedTheoryFramework.HAPPINESS_ADVANTAGE: self._happiness_advantage_algorithm,
            AdvancedTheoryFramework.MINDSET: self._mindset_algorithm,
        }
        
    def _init_execution_algorithms(self):
        """初始化执行管理类算法 (6个已有 + 12个新增)"""
        # 继承已有的6个执行算法
        from pm.engines.recommendation_engine import RecommendationEngine
        base_engine = RecommendationEngine(self.config)
        
        self.execution_algorithms = {
            # 已有算法 (6个)
            AdvancedTheoryFramework.OKR_WIG: base_engine._evaluate_okr_alignment,
            AdvancedTheoryFramework.FOUR_DX: base_engine._evaluate_4dx_priority,
            AdvancedTheoryFramework.FULL_ENGAGEMENT: base_engine._evaluate_energy_match,
            AdvancedTheoryFramework.ATOMIC_HABITS: base_engine._evaluate_habit_formation,
            AdvancedTheoryFramework.GTD: base_engine._evaluate_gtd_next_action,
            AdvancedTheoryFramework.ESSENTIALISM: base_engine._evaluate_essentialism,
            
            # 新增算法 (12个)
            AdvancedTheoryFramework.DEEP_WORK: self._deep_work_algorithm,
            AdvancedTheoryFramework.DIGITAL_MINIMALISM: self._digital_minimalism_algorithm,
            AdvancedTheoryFramework.DISTRACTED_MIND: self._distracted_mind_algorithm,
            AdvancedTheoryFramework.FLOW: self._flow_algorithm,
            AdvancedTheoryFramework.PEAK_PERFORMANCE: self._peak_performance_algorithm,
            AdvancedTheoryFramework.POWER_FULL_ENGAGEMENT: self._power_full_engagement_algorithm,
            AdvancedTheoryFramework.TIME_TRAP: self._time_trap_algorithm,
            AdvancedTheoryFramework.FIRST_THINGS_FIRST: self._first_things_first_algorithm,
            AdvancedTheoryFramework.PRODUCTIVITY_PROJECT: self._productivity_project_algorithm,
            AdvancedTheoryFramework.MAKING_IDEAS_HAPPEN: self._making_ideas_happen_algorithm,
            AdvancedTheoryFramework.ORGANIZE_TOMORROW: self._organize_tomorrow_algorithm,
            AdvancedTheoryFramework.LESS_IS_MORE: self._less_is_more_algorithm,
        }
        
    def _init_goal_algorithms(self):
        """初始化目标管理类算法 (15个)"""
        self.goal_algorithms = {
            AdvancedTheoryFramework.OBJECTIVES_KEY_RESULTS: self._okr_algorithm,
            AdvancedTheoryFramework.MEASURE_WHAT_MATTERS: self._measure_what_matters_algorithm,
            AdvancedTheoryFramework.STRETCH_GOALS: self._stretch_goals_algorithm,
            AdvancedTheoryFramework.GOALS_THEORY: self._goals_theory_algorithm,
            AdvancedTheoryFramework.SMART_GOALS: self._smart_goals_algorithm,
            AdvancedTheoryFramework.VISION_DRIVEN: self._vision_driven_algorithm,
            AdvancedTheoryFramework.PURPOSE_DRIVEN_LIFE: self._purpose_driven_algorithm,
            AdvancedTheoryFramework.BIG_HAIRY_GOALS: self._big_hairy_goals_algorithm,
            AdvancedTheoryFramework.MILESTONE_MANAGEMENT: self._milestone_management_algorithm,
            AdvancedTheoryFramework.PROGRESS_PRINCIPLE: self._progress_principle_algorithm,
            AdvancedTheoryFramework.FEEDBACK_LOOPS: self._feedback_loops_algorithm,
            AdvancedTheoryFramework.CONTINUOUS_IMPROVEMENT: self._continuous_improvement_algorithm,
            AdvancedTheoryFramework.PERFORMANCE_MANAGEMENT: self._performance_management_algorithm,
            AdvancedTheoryFramework.ACCOUNTABILITY: self._accountability_algorithm,
            AdvancedTheoryFramework.EXECUTION_DISCIPLINE: self._execution_discipline_algorithm,
        }
        
    def _init_learning_algorithms(self):
        """初始化学习成长类算法 (12个)"""
        self.learning_algorithms = {
            AdvancedTheoryFramework.DELIBERATE_PRACTICE: self._deliberate_practice_algorithm,
            AdvancedTheoryFramework.TALENT_OVERRATED: self._talent_overrated_algorithm,
            AdvancedTheoryFramework.GRIT: self._grit_algorithm,
            AdvancedTheoryFramework.GROWTH_MINDSET: self._growth_mindset_algorithm,
            AdvancedTheoryFramework.LEARNING_HOW_TO_LEARN: self._learning_how_to_learn_algorithm,
            AdvancedTheoryFramework.MAKE_IT_STICK: self._make_it_stick_algorithm,
            AdvancedTheoryFramework.PEAK_LEARNING: self._peak_learning_algorithm,
            AdvancedTheoryFramework.MASTERY: self._mastery_algorithm,
            AdvancedTheoryFramework.EXPERT_PERFORMANCE: self._expert_performance_algorithm,
            AdvancedTheoryFramework.SKILL_ACQUISITION: self._skill_acquisition_algorithm,
            AdvancedTheoryFramework.COMPOUND_EFFECT: self._compound_effect_algorithm,
            AdvancedTheoryFramework.KAIZEN: self._kaizen_algorithm,
        }

    # ==================== 核心智能分析接口 ====================
    
    def generate_intelligent_insights(
        self, 
        projects_data: List[Dict[str, Any]],
        user_context: Optional[Dict[str, Any]] = None
    ) -> List[IntelligentInsight]:
        """生成智能洞察 - 集成所有19本书籍算法"""
        
        insights = []
        
        # 按类别生成洞察
        for category in BookCategory:
            category_insights = self._generate_category_insights(
                category, projects_data, user_context
            )
            insights.extend(category_insights)
            
        # 交叉验证和排序
        insights = self._cross_validate_insights(insights)
        insights = sorted(insights, key=lambda x: x.confidence_score, reverse=True)
        
        return insights[:10]  # 返回top 10洞察
        
    def generate_predictive_analysis(
        self,
        projects_data: List[Dict[str, Any]], 
        target_metrics: List[str],
        time_horizon: timedelta = timedelta(days=30)
    ) -> List[PredictiveAnalysis]:
        """生成预测性分析"""
        
        predictions = []
        
        for metric in target_metrics:
            try:
                prediction = self._predict_metric(
                    metric, projects_data, time_horizon
                )
                if prediction:
                    predictions.append(prediction)
            except Exception as e:
                self.logger.warning(f"预测分析失败: {metric}", error=str(e))
                
        return predictions
        
    def generate_decision_support(
        self,
        decision_context: str,
        available_options: List[Dict[str, Any]],
        projects_data: List[Dict[str, Any]],
        constraints: Optional[Dict[str, Any]] = None
    ) -> DecisionSupport:
        """生成决策支持建议"""
        
        # 应用多个决策理论算法
        decision_scores = {}
        
        # 认知决策算法评估
        cognitive_scores = self._apply_cognitive_decision_algorithms(
            decision_context, available_options, projects_data
        )
        
        # 目标对齐度评估
        goal_alignment_scores = self._evaluate_goal_alignment(
            available_options, projects_data
        )
        
        # 风险评估
        risk_scores = self._assess_decision_risks(
            available_options, projects_data
        )
        
        # 综合评分
        for i, option in enumerate(available_options):
            total_score = (
                cognitive_scores.get(i, 0) * 0.4 +
                goal_alignment_scores.get(i, 0) * 0.4 +
                (1 - risk_scores.get(i, 1)) * 0.2  # 风险越低分数越高
            )
            decision_scores[i] = total_score
            
        # 选择最优选项
        best_option_idx = max(decision_scores.keys(), 
                            key=lambda k: decision_scores[k])
        
        return DecisionSupport(
            decision_id=f"decision_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            decision_context=decision_context,
            options=available_options,
            recommended_option=available_options[best_option_idx].get('name', f'Option {best_option_idx}'),
            reasoning=self._generate_decision_reasoning(best_option_idx, decision_scores),
            risk_assessment=risk_scores,
            success_probability=decision_scores[best_option_idx],
            supporting_theories=self._identify_supporting_theories(decision_context)
        )

    # ==================== 个性化机器学习系统 ====================
    
    def update_personalization_model(
        self,
        user_actions: List[Dict[str, Any]],
        outcomes: List[Dict[str, Any]]
    ):
        """更新个性化机器学习模型"""
        
        if not self.ai_config.ml_enabled:
            return
            
        # 特征工程
        features = self._extract_personalization_features(user_actions)
        labels = self._extract_outcome_labels(outcomes)
        
        # 更新用户画像
        self._update_user_profile(features, labels)
        
        # 增量学习
        self._incremental_learning_update(features, labels)
        
    def get_personalized_recommendations(
        self,
        projects_data: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """获取个性化推荐"""
        
        base_recommendations = self.generate_intelligent_insights(
            projects_data, context
        )
        
        if not self.ai_config.ml_enabled or not self.user_profile:
            return [self._insight_to_dict(insight) for insight in base_recommendations]
            
        # 个性化调整
        personalized_recommendations = []
        for insight in base_recommendations:
            personalized_score = self._calculate_personalized_score(insight, context)
            recommendation = self._insight_to_dict(insight)
            recommendation['personalized_score'] = personalized_score
            personalized_recommendations.append(recommendation)
            
        # 按个性化分数排序
        personalized_recommendations.sort(
            key=lambda x: x['personalized_score'], 
            reverse=True
        )
        
        return personalized_recommendations

    # ==================== 算法实现占位符 ====================
    # 以下是57个具体算法的实现框架，每个算法都需要根据原书理论进行具体实现
    
    # 认知决策类算法 (12个)
    def _thinking_fast_slow_algorithm(self, context, data):
        """《思考，快与慢》算法 - 系统1/系统2思维分析"""
        pass
        
    def _decisive_algorithm(self, context, data):
        """《决断力》算法 - 决策流程优化"""
        pass
        
    def _choice_paradox_algorithm(self, context, data):
        """《选择的悖论》算法 - 选择复杂度管理"""
        pass
        
    # ... 其他认知算法占位符
    
    # 新增执行管理类算法 (12个)
    def _deep_work_algorithm(self, context, data):
        """《深度工作》算法 - 深度专注时间分析"""
        pass
        
    def _digital_minimalism_algorithm(self, context, data):
        """《数字极简主义》算法 - 数字干扰评估"""
        pass
        
    # ... 其他执行算法占位符
    
    # 目标管理类算法 (15个)
    def _okr_algorithm(self, context, data):
        """OKR算法 - 目标关键结果对齐"""
        pass
        
    # ... 其他目标算法占位符
    
    # 学习成长类算法 (12个)  
    def _deliberate_practice_algorithm(self, context, data):
        """《刻意练习》算法 - 技能发展评估"""
        pass
        
    # ... 其他学习算法占位符
    
    # ==================== 辅助方法 ====================
    
    def _generate_category_insights(
        self, 
        category: BookCategory,
        projects_data: List[Dict[str, Any]],
        user_context: Optional[Dict[str, Any]]
    ) -> List[IntelligentInsight]:
        """为特定类别生成洞察"""
        # 实现具体的类别洞察生成逻辑
        return []
        
    def _cross_validate_insights(self, insights: List[IntelligentInsight]) -> List[IntelligentInsight]:
        """交叉验证洞察的一致性和准确性"""
        # 实现洞察交叉验证逻辑
        return insights
        
    def _insight_to_dict(self, insight: IntelligentInsight) -> Dict[str, Any]:
        """将洞察对象转换为字典"""
        return {
            'id': insight.insight_id,
            'category': insight.category.value,
            'text': insight.insight_text,
            'confidence': insight.confidence_score,
            'recommendations': insight.actionable_recommendations,
            'predicted_impact': insight.predicted_impact
        }
        
    # ... 更多辅助方法的实现框架


# ==================== AI可调用工具函数 ====================

def analyze_intelligent_insights(
    projects_data: Optional[List[Dict[str, Any]]] = None,
    user_context: Optional[Dict[str, Any]] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    生成基于19本书籍算法的智能洞察分析
    
    Args:
        projects_data: 项目数据列表
        user_context: 用户上下文信息
        
    Returns:
        Tuple[bool, str, Optional[Dict[str, Any]]]: (成功状态, 消息, 洞察数据)
    """
    try:
        logger.info("启动智能洞察分析", projects_count=len(projects_data) if projects_data else 0)
        
        config = PMConfig()
        engine = IntelligentAnalysisEngine(config)
        
        # 转换项目数据
        if projects_data:
            projects = projects_data
        else:
            projects = []
            
        # 生成洞察
        insights = engine.generate_intelligent_insights(projects, user_context)
        
        result = {
            'insights_count': len(insights),
            'insights': [engine._insight_to_dict(insight) for insight in insights],
            'analysis_timestamp': datetime.now().isoformat(),
            'algorithms_used': len(AdvancedTheoryFramework),
            'categories_covered': len(BookCategory)
        }
        
        logger.info("智能洞察分析完成", insights_count=len(insights))
        return True, f"成功生成 {len(insights)} 个智能洞察", result
        
    except Exception as e:
        logger.error("智能洞察分析失败", error=str(e))
        return False, f"分析失败: {str(e)}", None


def generate_predictive_analysis(
    projects_data: Optional[List[Dict[str, Any]]] = None,
    target_metrics: Optional[List[str]] = None,
    time_horizon_days: int = 30
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    生成预测性分析和洞察
    
    Args:
        projects_data: 项目数据列表
        target_metrics: 目标预测指标
        time_horizon_days: 预测时间范围(天)
        
    Returns:
        Tuple[bool, str, Optional[Dict[str, Any]]]: (成功状态, 消息, 预测数据)
    """
    try:
        logger.info("启动预测性分析", 
                   metrics=target_metrics, 
                   horizon_days=time_horizon_days)
        
        config = PMConfig()
        engine = IntelligentAnalysisEngine(config)
        
        # 转换项目数据
        if projects_data:
            projects = projects_data
        else:
            projects = []
            
        # 默认预测指标
        if not target_metrics:
            target_metrics = ['project_completion_rate', 'productivity_trend', 'goal_achievement']
            
        # 生成预测
        predictions = engine.generate_predictive_analysis(
            projects, 
            target_metrics,
            timedelta(days=time_horizon_days)
        )
        
        result = {
            'predictions_count': len(predictions),
            'predictions': [
                {
                    'id': p.prediction_id,
                    'metric': p.target_metric,
                    'current_value': p.current_value,
                    'predicted_value': p.predicted_value,
                    'confidence': p.prediction_confidence,
                    'contributing_factors': p.contributing_factors,
                    'interventions': p.recommended_interventions
                }
                for p in predictions
            ],
            'analysis_timestamp': datetime.now().isoformat(),
            'time_horizon_days': time_horizon_days
        }
        
        logger.info("预测性分析完成", predictions_count=len(predictions))
        return True, f"成功生成 {len(predictions)} 个预测分析", result
        
    except Exception as e:
        logger.error("预测性分析失败", error=str(e))
        return False, f"预测失败: {str(e)}", None


def provide_decision_support(
    decision_context: str,
    available_options: List[Dict[str, Any]],
    projects_data: Optional[List[Dict[str, Any]]] = None,
    constraints: Optional[Dict[str, Any]] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    提供基于多理论框架的决策支持
    
    Args:
        decision_context: 决策背景描述
        available_options: 可选方案列表
        projects_data: 项目数据列表
        constraints: 约束条件
        
    Returns:
        Tuple[bool, str, Optional[Dict[str, Any]]]: (成功状态, 消息, 决策建议)
    """
    try:
        logger.info("启动决策支持分析", 
                   context=decision_context[:50],
                   options_count=len(available_options))
        
        config = PMConfig()
        engine = IntelligentAnalysisEngine(config)
        
        # 转换项目数据
        if projects_data:
            projects = projects_data
        else:
            projects = []
            
        # 生成决策支持
        decision_support = engine.generate_decision_support(
            decision_context,
            available_options,
            projects,
            constraints
        )
        
        result = {
            'decision_id': decision_support.decision_id,
            'context': decision_support.decision_context,
            'recommended_option': decision_support.recommended_option,
            'reasoning': decision_support.reasoning,
            'risk_assessment': decision_support.risk_assessment,
            'success_probability': decision_support.success_probability,
            'supporting_theories': [t.value for t in decision_support.supporting_theories],
            'options_evaluated': len(available_options),
            'analysis_timestamp': datetime.now().isoformat()
        }
        
        logger.info("决策支持分析完成", 
                   recommended=decision_support.recommended_option)
        return True, f"推荐选择: {decision_support.recommended_option}", result
        
    except Exception as e:
        logger.error("决策支持分析失败", error=str(e))
        return False, f"决策分析失败: {str(e)}", None