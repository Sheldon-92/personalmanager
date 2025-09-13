"""高级决策支持系统

基于19本书籍理论框架的综合决策支持引擎，提供：
- 多理论框架决策分析
- 风险评估和机会识别
- 认知偏差检测和纠正
- 决策路径优化
- 结果预测和影响分析
"""

import numpy as np
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field, asdict
from collections import defaultdict, deque
from enum import Enum
import structlog
import math

from pm.core.config import PMConfig
from pm.models.task import Task, TaskStatus, TaskContext, TaskPriority, EnergyLevel
from pm.models.project import ProjectStatus, ProjectStatus, ProjectHealth
from pm.engines.intelligent_analysis_engine import AdvancedTheoryFramework, BookCategory

logger = structlog.get_logger(__name__)


class DecisionType(Enum):
    """决策类型"""
    STRATEGIC = "strategic"  # 战略决策
    OPERATIONAL = "operational"  # 运营决策
    TACTICAL = "tactical"  # 战术决策
    PERSONAL = "personal"  # 个人决策
    RESOURCE_ALLOCATION = "resource_allocation"  # 资源分配
    PRIORITY_SETTING = "priority_setting"  # 优先级设置
    GOAL_SETTING = "goal_setting"  # 目标设定
    RISK_MANAGEMENT = "risk_management"  # 风险管理


class CognitiveBias(Enum):
    """认知偏差类型"""
    CONFIRMATION_BIAS = "confirmation_bias"  # 确认偏差
    ANCHORING_BIAS = "anchoring_bias"  # 锚定偏差
    AVAILABILITY_HEURISTIC = "availability_heuristic"  # 可得性启发
    OVERCONFIDENCE = "overconfidence"  # 过度自信
    LOSS_AVERSION = "loss_aversion"  # 损失厌恶
    FRAMING_EFFECT = "framing_effect"  # 框架效应
    SUNK_COST_FALLACY = "sunk_cost_fallacy"  # 沉没成本谬误
    PLANNING_FALLACY = "planning_fallacy"  # 规划谬误


class RiskLevel(Enum):
    """风险等级"""
    VERY_LOW = "very_low"
    LOW = "low" 
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass
class DecisionOption:
    """决策选项"""
    option_id: str
    name: str
    description: str
    pros: List[str] = field(default_factory=list)
    cons: List[str] = field(default_factory=list)
    estimated_cost: Optional[float] = None
    estimated_benefit: Optional[float] = None
    risk_level: RiskLevel = RiskLevel.MEDIUM
    time_to_implement: Optional[timedelta] = None
    resource_requirements: Dict[str, Any] = field(default_factory=dict)
    success_probability: float = 0.5


@dataclass
class CognitiveBiasWarning:
    """认知偏差警告"""
    bias_type: CognitiveBias
    confidence: float  # 0.0-1.0
    description: str
    detected_patterns: List[str]
    mitigation_strategies: List[str]


@dataclass
class RiskAssessment:
    """风险评估"""
    risk_id: str
    risk_type: str
    probability: float  # 0.0-1.0
    impact: float  # 0.0-1.0 
    risk_score: float  # probability * impact
    description: str
    mitigation_strategies: List[str]
    contingency_plans: List[str]


@dataclass
class DecisionAnalysis:
    """决策分析结果"""
    decision_id: str
    decision_type: DecisionType
    context: str
    options: List[DecisionOption]
    
    # 分析结果
    recommended_option: str
    confidence_score: float
    reasoning: List[str]
    
    # 理论框架评分
    theory_framework_scores: Dict[AdvancedTheoryFramework, float]
    
    # 风险和偏差分析
    risk_assessments: List[RiskAssessment]
    cognitive_bias_warnings: List[CognitiveBiasWarning]
    
    # 预测结果
    predicted_outcomes: Dict[str, float]  # 结果类型 -> 预测值
    sensitivity_analysis: Dict[str, float]  # 因子 -> 敏感性
    
    # 元数据
    analysis_timestamp: datetime
    frameworks_used: List[AdvancedTheoryFramework]


class DecisionSupportEngine:
    """高级决策支持引擎"""
    
    def __init__(self, config: PMConfig):
        self.config = config
        self.logger = structlog.get_logger(__name__)
        
        # 决策历史
        self.decision_history: List[DecisionAnalysis] = []
        
        # 理论框架权重配置
        self.framework_weights = {
            # 认知决策类理论权重较高
            BookCategory.COGNITIVE_DECISION: 0.35,
            BookCategory.EXECUTION_MANAGEMENT: 0.25,
            BookCategory.GOAL_MANAGEMENT: 0.25,
            BookCategory.LEARNING_GROWTH: 0.15
        }
        
        # 偏差检测阈值
        self.bias_detection_threshold = 0.6
        self.risk_tolerance_default = 0.5
        
        self._load_decision_history()
        
    def _load_decision_history(self):
        """加载决策历史"""
        try:
            history_path = self.config.data_dir / "decision_history.json"
            if history_path.exists():
                with open(history_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                for item in data:
                    # 重构DecisionAnalysis对象
                    analysis = self._dict_to_decision_analysis(item)
                    if analysis:
                        self.decision_history.append(analysis)
                        
                self.logger.info("决策历史加载完成", 
                               decisions_count=len(self.decision_history))
                               
        except Exception as e:
            self.logger.warning("决策历史加载失败", error=str(e))
            
    def _save_decision_history(self):
        """保存决策历史"""
        try:
            history_path = self.config.data_dir / "decision_history.json"
            
            data = []
            # 保留最近100个决策记录
            for analysis in self.decision_history[-100:]:
                data.append(self._decision_analysis_to_dict(analysis))
                
            with open(history_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            self.logger.info("决策历史保存完成")
            
        except Exception as e:
            self.logger.error("决策历史保存失败", error=str(e))
            
    def analyze_decision(
        self,
        decision_context: str,
        options: List[DecisionOption],
        decision_type: DecisionType = DecisionType.OPERATIONAL,
        user_constraints: Optional[Dict[str, Any]] = None
    ) -> DecisionAnalysis:
        """综合决策分析"""
        
        # 生成决策ID
        decision_id = f"decision_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 多理论框架评估
        framework_scores = self._multi_framework_evaluation(
            decision_context, options, decision_type
        )
        
        # 计算综合评分
        option_scores = self._calculate_comprehensive_scores(
            options, framework_scores, user_constraints
        )
        
        # 选择最优选项
        best_option_id = max(option_scores.keys(), key=lambda k: option_scores[k])
        best_option = next(opt for opt in options if opt.option_id == best_option_id)
        
        # 生成推理过程
        reasoning = self._generate_decision_reasoning(
            best_option, option_scores, framework_scores
        )
        
        # 风险评估
        risk_assessments = self._conduct_risk_assessment(options, decision_type)
        
        # 认知偏差检测
        bias_warnings = self._detect_cognitive_biases(
            decision_context, options, user_constraints
        )
        
        # 结果预测
        predicted_outcomes = self._predict_decision_outcomes(
            best_option, decision_context, decision_type
        )
        
        # 敏感性分析
        sensitivity_analysis = self._conduct_sensitivity_analysis(
            options, framework_scores
        )
        
        # 构建决策分析结果
        analysis = DecisionAnalysis(
            decision_id=decision_id,
            decision_type=decision_type,
            context=decision_context,
            options=options,
            recommended_option=best_option.name,
            confidence_score=max(option_scores.values()),
            reasoning=reasoning,
            theory_framework_scores=framework_scores,
            risk_assessments=risk_assessments,
            cognitive_bias_warnings=bias_warnings,
            predicted_outcomes=predicted_outcomes,
            sensitivity_analysis=sensitivity_analysis,
            analysis_timestamp=datetime.now(),
            frameworks_used=list(framework_scores.keys())
        )
        
        # 保存到历史记录
        self.decision_history.append(analysis)
        self._save_decision_history()
        
        return analysis
        
    def _multi_framework_evaluation(
        self,
        context: str,
        options: List[DecisionOption],
        decision_type: DecisionType
    ) -> Dict[AdvancedTheoryFramework, float]:
        """多理论框架评估"""
        
        scores = {}
        
        # 认知决策类理论
        scores[AdvancedTheoryFramework.THINKING_FAST_SLOW] = self._thinking_fast_slow_evaluation(context, options)
        scores[AdvancedTheoryFramework.DECISIVE] = self._decisive_evaluation(context, options)
        scores[AdvancedTheoryFramework.CHOICE_PARADOX] = self._choice_paradox_evaluation(context, options)
        scores[AdvancedTheoryFramework.PREDICTABLY_IRRATIONAL] = self._predictably_irrational_evaluation(context, options)
        
        # 执行管理类理论
        scores[AdvancedTheoryFramework.ESSENTIALISM] = self._essentialism_evaluation(context, options)
        scores[AdvancedTheoryFramework.FIRST_THINGS_FIRST] = self._first_things_first_evaluation(context, options)
        
        # 目标管理类理论
        scores[AdvancedTheoryFramework.SMART_GOALS] = self._smart_goals_evaluation(context, options)
        scores[AdvancedTheoryFramework.OBJECTIVES_KEY_RESULTS] = self._okr_evaluation(context, options)
        
        return scores
        
    def _thinking_fast_slow_evaluation(
        self,
        context: str,
        options: List[DecisionOption]
    ) -> float:
        """《思考，快与慢》理论评估"""
        
        # 系统1 vs 系统2思维分析
        complexity_score = len(options) / 10.0  # 选项复杂度
        
        # 偏好直观简单的选项(系统1)还是深度分析的选项(系统2)
        has_clear_winner = False
        max_benefit = max((opt.estimated_benefit or 0) for opt in options)
        min_risk = min(opt.risk_level.value for opt in options)
        
        # 如果存在明显的最优选择，系统1思维更适用
        for option in options:
            if ((option.estimated_benefit or 0) >= max_benefit * 0.9 and 
                option.risk_level.value == min_risk):
                has_clear_winner = True
                break
                
        if has_clear_winner and complexity_score < 0.3:
            return 0.8  # 适合快速决策
        elif complexity_score > 0.5:
            return 0.9  # 需要系统2深度思考
        else:
            return 0.6  # 中等复杂度
            
    def _decisive_evaluation(
        self,
        context: str,
        options: List[DecisionOption]
    ) -> float:
        """《决断力》WRAP模型评估"""
        
        # W - 拓宽选项 (Widen options)
        options_diversity = len(set(opt.name[:10] for opt in options)) / len(options)
        
        # R - 现实检验 (Reality-test assumptions) 
        reality_check_score = sum(1 for opt in options if opt.success_probability > 0) / len(options)
        
        # A - 获得距离感 (Attain distance)
        has_long_term_view = any(
            opt.time_to_implement and opt.time_to_implement > timedelta(days=30)
            for opt in options
        )
        
        # P - 为错误做准备 (Prepare to be wrong)
        has_contingency = any(len(opt.cons) > 0 for opt in options)
        
        wrap_score = (
            options_diversity * 0.3 +
            reality_check_score * 0.3 + 
            (0.8 if has_long_term_view else 0.4) * 0.2 +
            (0.8 if has_contingency else 0.4) * 0.2
        )
        
        return wrap_score
        
    def _choice_paradox_evaluation(
        self,
        context: str,
        options: List[DecisionOption]
    ) -> float:
        """《选择的悖论》理论评估 - 选择过载分析"""
        
        options_count = len(options)
        
        # 选择过载检测
        if options_count <= 3:
            return 0.9  # 理想选择数量
        elif options_count <= 7:
            return 0.7  # 可管理的选择数量
        else:
            # 选择过载，需要筛选和简化
            return 0.4
            
    def _predictably_irrational_evaluation(
        self,
        context: str,
        options: List[DecisionOption]
    ) -> float:
        """《可预测的非理性》理论评估"""
        
        # 检测可能的非理性决策模式
        
        # 价格锚定效应
        has_anchoring = False
        if any(opt.estimated_cost for opt in options):
            costs = [opt.estimated_cost for opt in options if opt.estimated_cost]
            if costs:
                cost_range = max(costs) - min(costs)
                has_anchoring = cost_range > min(costs) * 0.5
                
        # 相对性偏差 (选择相对较好的，而非绝对最好的)
        has_decoy_option = False
        for i, opt1 in enumerate(options):
            for j, opt2 in enumerate(options):
                if i != j and opt1.estimated_benefit and opt2.estimated_benefit:
                    if (opt1.estimated_benefit > opt2.estimated_benefit and
                        opt1.risk_level.value <= opt2.risk_level.value):
                        has_decoy_option = True
                        
        irrationality_score = 0.7
        if has_anchoring:
            irrationality_score -= 0.1
        if has_decoy_option:
            irrationality_score += 0.2
            
        return max(0.3, min(0.9, irrationality_score))
        
    def _essentialism_evaluation(
        self,
        context: str, 
        options: List[DecisionOption]
    ) -> float:
        """《精要主义》理论评估"""
        
        # 评估选项是否符合"少即是多"原则
        
        # 检查是否有明确的最重要选项
        benefits = [opt.estimated_benefit or 0 for opt in options]
        if benefits:
            max_benefit = max(benefits)
            essential_options = sum(1 for b in benefits if b >= max_benefit * 0.8)
            
            if essential_options <= 2:
                return 0.9  # 符合精要主义，少数关键选项
            elif essential_options <= len(options) * 0.5:
                return 0.7  # 部分符合
            else:
                return 0.5  # 没有突出的关键选项
        
        return 0.6
        
    def _first_things_first_evaluation(
        self,
        context: str,
        options: List[DecisionOption]
    ) -> float:
        """《要事第一》理论评估"""
        
        # 基于重要性和紧急性矩阵评估
        
        urgent_important_count = 0
        total_evaluated = 0
        
        for option in options:
            if hasattr(option, 'urgency') and hasattr(option, 'importance'):
                total_evaluated += 1
                if option.urgency > 0.7 and option.importance > 0.7:
                    urgent_important_count += 1
                    
        if total_evaluated == 0:
            return 0.6  # 无法评估
            
        # 如果有明确的重要且紧急的选项
        if urgent_important_count > 0:
            return 0.9
        else:
            return 0.5
            
    def _smart_goals_evaluation(
        self,
        context: str,
        options: List[DecisionOption]
    ) -> float:
        """SMART目标理论评估"""
        
        smart_scores = []
        
        for option in options:
            smart_score = 0
            
            # Specific - 具体性
            if len(option.description) > 20 and option.name:
                smart_score += 0.2
                
            # Measurable - 可衡量
            if option.estimated_benefit is not None or option.estimated_cost is not None:
                smart_score += 0.2
                
            # Achievable - 可实现
            if option.success_probability >= 0.6:
                smart_score += 0.2
                
            # Relevant - 相关性 (基于描述关键词)
            relevant_keywords = ['goal', 'objective', 'target', 'improve', 'achieve']
            if any(keyword in option.description.lower() for keyword in relevant_keywords):
                smart_score += 0.2
                
            # Time-bound - 时间限制
            if option.time_to_implement:
                smart_score += 0.2
                
            smart_scores.append(smart_score)
            
        return np.mean(smart_scores) if smart_scores else 0.5
        
    def _okr_evaluation(self, context: str, options: List[DecisionOption]) -> float:
        """OKR理论评估"""
        
        # 检查选项是否符合OKR原则：目标导向、关键结果、挑战性
        
        okr_alignment = 0.6  # 基础分数
        
        # 检查是否有量化的关键结果
        quantified_options = sum(
            1 for opt in options 
            if opt.estimated_benefit is not None or opt.estimated_cost is not None
        )
        
        if quantified_options >= len(options) * 0.7:
            okr_alignment += 0.2
            
        # 检查挑战性目标 (高收益但中等风险)
        challenging_options = sum(
            1 for opt in options
            if opt.estimated_benefit and opt.estimated_benefit > 0.7 and 
            opt.risk_level in [RiskLevel.MEDIUM, RiskLevel.HIGH]
        )
        
        if challenging_options > 0:
            okr_alignment += 0.2
            
        return min(1.0, okr_alignment)
        
    def _calculate_comprehensive_scores(
        self,
        options: List[DecisionOption],
        framework_scores: Dict[AdvancedTheoryFramework, float],
        constraints: Optional[Dict[str, Any]]
    ) -> Dict[str, float]:
        """计算综合评分"""
        
        option_scores = {}
        
        for option in options:
            base_score = self._calculate_base_option_score(option)
            
            # 理论框架加权评分
            framework_weighted_score = sum(
                score * self._get_framework_weight(framework)
                for framework, score in framework_scores.items()
            )
            
            # 约束条件调整
            constraint_penalty = self._apply_constraints(option, constraints)
            
            # 综合评分
            comprehensive_score = (
                base_score * 0.4 +
                framework_weighted_score * 0.4 +
                (1.0 - constraint_penalty) * 0.2
            )
            
            option_scores[option.option_id] = comprehensive_score
            
        return option_scores
        
    def _calculate_base_option_score(self, option: DecisionOption) -> float:
        """计算选项基础评分"""
        
        # 收益评分
        benefit_score = (option.estimated_benefit or 0.5) 
        
        # 成本评分 (成本越低分数越高)
        cost_score = 1.0 - (option.estimated_cost or 0.5) if option.estimated_cost is not None else 0.5
        
        # 风险评分 (风险越低分数越高)
        risk_mapping = {
            RiskLevel.VERY_LOW: 0.9,
            RiskLevel.LOW: 0.7,
            RiskLevel.MEDIUM: 0.5,
            RiskLevel.HIGH: 0.3,
            RiskLevel.VERY_HIGH: 0.1
        }
        risk_score = risk_mapping[option.risk_level]
        
        # 成功概率评分
        success_score = option.success_probability
        
        # 加权计算
        base_score = (
            benefit_score * 0.3 +
            cost_score * 0.2 +
            risk_score * 0.3 +
            success_score * 0.2
        )
        
        return base_score
        
    def _get_framework_weight(self, framework: AdvancedTheoryFramework) -> float:
        """获取理论框架权重"""
        
        # 根据理论框架类别返回权重
        cognitive_frameworks = [
            AdvancedTheoryFramework.THINKING_FAST_SLOW,
            AdvancedTheoryFramework.DECISIVE,
            AdvancedTheoryFramework.CHOICE_PARADOX,
            AdvancedTheoryFramework.PREDICTABLY_IRRATIONAL
        ]
        
        if framework in cognitive_frameworks:
            return self.framework_weights[BookCategory.COGNITIVE_DECISION] / len(cognitive_frameworks)
        else:
            return 0.1  # 其他框架的默认权重
            
    def _apply_constraints(
        self,
        option: DecisionOption,
        constraints: Optional[Dict[str, Any]]
    ) -> float:
        """应用约束条件，返回惩罚分数 (0.0-1.0)"""
        
        if not constraints:
            return 0.0
            
        penalty = 0.0
        
        # 时间约束
        if 'max_time' in constraints and option.time_to_implement:
            max_time = timedelta(days=constraints['max_time'])
            if option.time_to_implement > max_time:
                penalty += 0.3
                
        # 成本约束
        if 'max_cost' in constraints and option.estimated_cost:
            if option.estimated_cost > constraints['max_cost']:
                penalty += 0.4
                
        # 风险约束  
        if 'max_risk' in constraints:
            risk_levels = {
                'very_low': 1, 'low': 2, 'medium': 3, 'high': 4, 'very_high': 5
            }
            if risk_levels.get(option.risk_level.value, 3) > constraints['max_risk']:
                penalty += 0.3
                
        return min(1.0, penalty)
        
    def _conduct_risk_assessment(
        self,
        options: List[DecisionOption],
        decision_type: DecisionType
    ) -> List[RiskAssessment]:
        """进行风险评估"""
        
        risk_assessments = []
        
        for option in options:
            risks = []
            
            # 基于选项特征识别风险
            if option.estimated_cost and option.estimated_cost > 0.8:
                risks.append(RiskAssessment(
                    risk_id=f"cost_risk_{option.option_id}",
                    risk_type="cost_overrun",
                    probability=0.3,
                    impact=0.7,
                    risk_score=0.21,
                    description=f"{option.name} 的高成本可能导致预算超支",
                    mitigation_strategies=["详细成本分析", "分阶段实施", "寻找替代方案"],
                    contingency_plans=["预留应急预算", "准备成本削减计划"]
                ))
                
            if option.success_probability < 0.6:
                risks.append(RiskAssessment(
                    risk_id=f"failure_risk_{option.option_id}",
                    risk_type="implementation_failure", 
                    probability=1 - option.success_probability,
                    impact=0.8,
                    risk_score=(1 - option.success_probability) * 0.8,
                    description=f"{option.name} 实施失败的可能性较高",
                    mitigation_strategies=["增加准备工作", "获得专家支持", "小规模试点"],
                    contingency_plans=["准备回退方案", "设置里程碑检查点"]
                ))
                
            if option.time_to_implement and option.time_to_implement > timedelta(days=90):
                risks.append(RiskAssessment(
                    risk_id=f"timeline_risk_{option.option_id}",
                    risk_type="schedule_delay",
                    probability=0.4,
                    impact=0.5,
                    risk_score=0.2,
                    description=f"{option.name} 实施周期长，可能面临进度延迟",
                    mitigation_strategies=["细化时间规划", "增加检查点", "提前识别瓶颈"],
                    contingency_plans=["准备加速措施", "调整优先级"]
                ))
                
            risk_assessments.extend(risks)
            
        return risk_assessments
        
    def _detect_cognitive_biases(
        self,
        context: str,
        options: List[DecisionOption],
        constraints: Optional[Dict[str, Any]]
    ) -> List[CognitiveBiasWarning]:
        """检测认知偏差"""
        
        warnings = []
        
        # 确认偏差检测
        if constraints and 'preferred_option' in constraints:
            warnings.append(CognitiveBiasWarning(
                bias_type=CognitiveBias.CONFIRMATION_BIAS,
                confidence=0.7,
                description="可能存在确认偏差，偏向支持已有观点的选项",
                detected_patterns=["用户指定偏好选项"],
                mitigation_strategies=[
                    "仔细评估其他选项的优势",
                    "寻求不同观点的反馈",
                    "列出偏好选项的潜在缺点"
                ]
            ))
            
        # 锚定偏差检测
        costs = [opt.estimated_cost for opt in options if opt.estimated_cost]
        if len(costs) >= 3:
            cost_range = max(costs) - min(costs)
            if cost_range > min(costs):
                warnings.append(CognitiveBiasWarning(
                    bias_type=CognitiveBias.ANCHORING_BIAS,
                    confidence=0.6,
                    description="成本估算可能受到锚定效应影响",
                    detected_patterns=["成本估算差异较大"],
                    mitigation_strategies=[
                        "独立验证成本估算",
                        "参考历史数据",
                        "获得多方成本评估"
                    ]
                ))
                
        # 过度自信检测
        high_confidence_options = sum(
            1 for opt in options if opt.success_probability > 0.8
        )
        if high_confidence_options >= len(options) * 0.7:
            warnings.append(CognitiveBiasWarning(
                bias_type=CognitiveBias.OVERCONFIDENCE,
                confidence=0.8,
                description="可能存在过度自信，成功率估计过高",
                detected_patterns=["多数选项成功率估计过高"],
                mitigation_strategies=[
                    "进行悲观情况分析",
                    "参考历史失败案例",
                    "寻求外部评估意见"
                ]
            ))
            
        # 选择过载检测
        if len(options) > 7:
            warnings.append(CognitiveBiasWarning(
                bias_type=CognitiveBias.CHOICE_PARADOX,
                confidence=0.9,
                description="选项过多可能导致决策困难和选择后悔",
                detected_patterns=[f"选项数量达到 {len(options)} 个"],
                mitigation_strategies=[
                    "预先筛选掉明显不合适的选项",
                    "按重要程度分组决策",
                    "使用排除法逐步缩小范围"
                ]
            ))
            
        return warnings
        
    def _predict_decision_outcomes(
        self,
        option: DecisionOption,
        context: str,
        decision_type: DecisionType
    ) -> Dict[str, float]:
        """预测决策结果"""
        
        outcomes = {}
        
        # 基于选项特征预测结果
        outcomes['satisfaction_score'] = min(1.0, (
            option.success_probability * 0.4 +
            (option.estimated_benefit or 0.5) * 0.4 +
            (1.0 - option.risk_level.value / 5.0) * 0.2
        ))
        
        outcomes['implementation_success_rate'] = option.success_probability
        
        # 投资回报率预测
        if option.estimated_benefit and option.estimated_cost:
            outcomes['roi'] = (option.estimated_benefit - option.estimated_cost) / max(option.estimated_cost, 0.01)
        else:
            outcomes['roi'] = 0.0
            
        # 时间效率评分
        if option.time_to_implement:
            time_efficiency = max(0.1, 1.0 - option.time_to_implement.days / 365)
            outcomes['time_efficiency'] = time_efficiency
        else:
            outcomes['time_efficiency'] = 0.7
            
        return outcomes
        
    def _conduct_sensitivity_analysis(
        self,
        options: List[DecisionOption],
        framework_scores: Dict[AdvancedTheoryFramework, float]
    ) -> Dict[str, float]:
        """进行敏感性分析"""
        
        sensitivity = {}
        
        # 分析各因子对决策结果的敏感性
        
        # 成本敏感性
        cost_variance = np.var([opt.estimated_cost or 0.5 for opt in options])
        sensitivity['cost_sensitivity'] = min(1.0, cost_variance * 2)
        
        # 收益敏感性
        benefit_variance = np.var([opt.estimated_benefit or 0.5 for opt in options])
        sensitivity['benefit_sensitivity'] = min(1.0, benefit_variance * 2)
        
        # 风险敏感性
        risk_values = [opt.risk_level.value for opt in options]
        risk_variance = np.var(risk_values) if len(set(risk_values)) > 1 else 0
        sensitivity['risk_sensitivity'] = min(1.0, risk_variance / 4.0)
        
        # 理论框架敏感性
        framework_variance = np.var(list(framework_scores.values()))
        sensitivity['framework_sensitivity'] = min(1.0, framework_variance * 2)
        
        return sensitivity
        
    def _generate_decision_reasoning(
        self,
        best_option: DecisionOption,
        option_scores: Dict[str, float],
        framework_scores: Dict[AdvancedTheoryFramework, float]
    ) -> List[str]:
        """生成决策推理过程"""
        
        reasoning = []
        
        # 选择理由
        best_score = option_scores[best_option.option_id]
        reasoning.append(f"推荐 '{best_option.name}'，综合评分 {best_score:.2f}")
        
        # 主要优势
        if best_option.estimated_benefit and best_option.estimated_benefit > 0.7:
            reasoning.append(f"该选项具有较高预期收益 ({best_option.estimated_benefit:.2f})")
            
        if best_option.risk_level in [RiskLevel.VERY_LOW, RiskLevel.LOW]:
            reasoning.append(f"风险水平较低 ({best_option.risk_level.value})")
            
        if best_option.success_probability > 0.7:
            reasoning.append(f"成功概率较高 ({best_option.success_probability:.2f})")
            
        # 理论框架支持
        top_frameworks = sorted(
            framework_scores.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:3]
        
        framework_names = {
            AdvancedTheoryFramework.THINKING_FAST_SLOW: "思考快与慢",
            AdvancedTheoryFramework.DECISIVE: "决断力WRAP模型",
            AdvancedTheoryFramework.ESSENTIALISM: "精要主义原则"
        }
        
        for framework, score in top_frameworks:
            if score > 0.7:
                name = framework_names.get(framework, framework.value)
                reasoning.append(f"符合 {name} 理论框架 (评分 {score:.2f})")
                
        return reasoning
        
    def _dict_to_decision_analysis(self, data: Dict[str, Any]) -> Optional[DecisionAnalysis]:
        """将字典转换为DecisionAnalysis对象"""
        try:
            # 这里简化实现，实际应该完整重构所有字段
            return None  # 占位符实现
        except Exception:
            return None
            
    def _decision_analysis_to_dict(self, analysis: DecisionAnalysis) -> Dict[str, Any]:
        """将DecisionAnalysis对象转换为字典"""
        return {
            'decision_id': analysis.decision_id,
            'decision_type': analysis.decision_type.value,
            'context': analysis.context,
            'recommended_option': analysis.recommended_option,
            'confidence_score': analysis.confidence_score,
            'reasoning': analysis.reasoning,
            'analysis_timestamp': analysis.analysis_timestamp.isoformat(),
            'predicted_outcomes': analysis.predicted_outcomes
        }


# ==================== AI可调用工具函数 ====================

def analyze_decision_options(
    decision_context: str,
    options: List[Dict[str, Any]],
    decision_type: str = "operational",
    constraints: Optional[Dict[str, Any]] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    分析决策选项并提供建议
    
    Args:
        decision_context: 决策背景描述
        options: 决策选项列表
        decision_type: 决策类型
        constraints: 约束条件
        
    Returns:
        Tuple[bool, str, Optional[Dict[str, Any]]]: (成功状态, 消息, 决策分析结果)
    """
    try:
        logger.info("启动决策选项分析", 
                   context=decision_context[:50],
                   options_count=len(options))
        
        config = PMConfig()
        engine = DecisionSupportEngine(config)
        
        # 转换选项格式
        decision_options = []
        for i, opt_data in enumerate(options):
            option = DecisionOption(
                option_id=opt_data.get('id', f'option_{i}'),
                name=opt_data['name'],
                description=opt_data.get('description', ''),
                pros=opt_data.get('pros', []),
                cons=opt_data.get('cons', []),
                estimated_cost=opt_data.get('estimated_cost'),
                estimated_benefit=opt_data.get('estimated_benefit'),
                risk_level=RiskLevel(opt_data.get('risk_level', 'medium')),
                success_probability=opt_data.get('success_probability', 0.5),
                resource_requirements=opt_data.get('resource_requirements', {})
            )
            decision_options.append(option)
            
        # 执行决策分析
        analysis = engine.analyze_decision(
            decision_context,
            decision_options,
            DecisionType(decision_type),
            constraints
        )
        
        result = {
            'decision_id': analysis.decision_id,
            'recommended_option': analysis.recommended_option,
            'confidence_score': analysis.confidence_score,
            'reasoning': analysis.reasoning,
            'predicted_outcomes': analysis.predicted_outcomes,
            'risk_assessments': [
                {
                    'risk_type': risk.risk_type,
                    'probability': risk.probability,
                    'impact': risk.impact,
                    'description': risk.description,
                    'mitigation_strategies': risk.mitigation_strategies
                }
                for risk in analysis.risk_assessments
            ],
            'cognitive_bias_warnings': [
                {
                    'bias_type': bias.bias_type.value,
                    'confidence': bias.confidence,
                    'description': bias.description,
                    'mitigation_strategies': bias.mitigation_strategies
                }
                for bias in analysis.cognitive_bias_warnings
            ],
            'sensitivity_analysis': analysis.sensitivity_analysis,
            'frameworks_used': [f.value for f in analysis.frameworks_used],
            'analysis_timestamp': analysis.analysis_timestamp.isoformat()
        }
        
        logger.info("决策分析完成", 
                   recommended=analysis.recommended_option,
                   confidence=analysis.confidence_score)
        return True, f"推荐选择: {analysis.recommended_option}", result
        
    except Exception as e:
        logger.error("决策分析失败", error=str(e))
        return False, f"分析失败: {str(e)}", None


def detect_decision_biases(
    decision_context: str,
    options: List[Dict[str, Any]],
    user_preferences: Optional[Dict[str, Any]] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    检测决策中的认知偏差
    
    Args:
        decision_context: 决策上下文
        options: 选项列表
        user_preferences: 用户偏好
        
    Returns:
        Tuple[bool, str, Optional[Dict[str, Any]]]: (成功状态, 消息, 偏差检测结果)
    """
    try:
        logger.info("启动认知偏差检测", 
                   context=decision_context[:50])
        
        config = PMConfig()
        engine = DecisionSupportEngine(config)
        
        # 转换选项格式
        decision_options = []
        for i, opt_data in enumerate(options):
            option = DecisionOption(
                option_id=f'option_{i}',
                name=opt_data['name'],
                description=opt_data.get('description', ''),
                estimated_cost=opt_data.get('estimated_cost'),
                estimated_benefit=opt_data.get('estimated_benefit'),
                success_probability=opt_data.get('success_probability', 0.5)
            )
            decision_options.append(option)
            
        # 检测认知偏差
        bias_warnings = engine._detect_cognitive_biases(
            decision_context, decision_options, user_preferences
        )
        
        result = {
            'biases_detected': len(bias_warnings),
            'bias_warnings': [
                {
                    'bias_type': bias.bias_type.value,
                    'confidence': bias.confidence,
                    'description': bias.description,
                    'detected_patterns': bias.detected_patterns,
                    'mitigation_strategies': bias.mitigation_strategies
                }
                for bias in bias_warnings
            ],
            'detection_timestamp': datetime.now().isoformat()
        }
        
        logger.info("认知偏差检测完成", biases_count=len(bias_warnings))
        return True, f"检测到 {len(bias_warnings)} 个潜在认知偏差", result
        
    except Exception as e:
        logger.error("认知偏差检测失败", error=str(e))
        return False, f"检测失败: {str(e)}", None


def assess_decision_risks(
    options: List[Dict[str, Any]],
    decision_type: str = "operational"
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    评估决策风险
    
    Args:
        options: 决策选项列表
        decision_type: 决策类型
        
    Returns:
        Tuple[bool, str, Optional[Dict[str, Any]]]: (成功状态, 消息, 风险评估结果)
    """
    try:
        logger.info("启动决策风险评估", 
                   options_count=len(options))
        
        config = PMConfig()
        engine = DecisionSupportEngine(config)
        
        # 转换选项格式
        decision_options = []
        for i, opt_data in enumerate(options):
            option = DecisionOption(
                option_id=f'option_{i}',
                name=opt_data['name'],
                description=opt_data.get('description', ''),
                estimated_cost=opt_data.get('estimated_cost'),
                estimated_benefit=opt_data.get('estimated_benefit'),
                risk_level=RiskLevel(opt_data.get('risk_level', 'medium')),
                success_probability=opt_data.get('success_probability', 0.5),
                time_to_implement=timedelta(days=opt_data.get('implementation_days', 30))
            )
            decision_options.append(option)
            
        # 进行风险评估
        risk_assessments = engine._conduct_risk_assessment(
            decision_options, DecisionType(decision_type)
        )
        
        result = {
            'total_risks_identified': len(risk_assessments),
            'risk_assessments': [
                {
                    'risk_id': risk.risk_id,
                    'risk_type': risk.risk_type,
                    'probability': risk.probability,
                    'impact': risk.impact,
                    'risk_score': risk.risk_score,
                    'description': risk.description,
                    'mitigation_strategies': risk.mitigation_strategies,
                    'contingency_plans': risk.contingency_plans
                }
                for risk in risk_assessments
            ],
            'assessment_timestamp': datetime.now().isoformat()
        }
        
        logger.info("决策风险评估完成", risks_count=len(risk_assessments))
        return True, f"识别 {len(risk_assessments)} 个风险因素", result
        
    except Exception as e:
        logger.error("决策风险评估失败", error=str(e))
        return False, f"评估失败: {str(e)}", None