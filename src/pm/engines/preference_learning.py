"""用户偏好学习引擎 - US-013核心实现

从用户对推荐任务的选择历史中持续学习，动态调整推荐算法权重，
实现越来越个性化的建议。
"""

import json
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import structlog

from pm.core.config import PMConfig
from pm.engines.recommendation_engine import TheoryFramework, UserPreferences
from pm.models.task import Task, TaskContext, TaskPriority, EnergyLevel

logger = structlog.get_logger()


@dataclass
class UserChoice:
    """用户选择记录"""
    task_id: str
    task_title: str
    chosen_at: datetime
    recommendation_rank: int  # 在推荐列表中的排名（1-based）
    recommendation_score: float
    framework_scores: Dict[str, float]
    context: Optional[str] = None
    priority: Optional[str] = None
    energy_level: Optional[str] = None
    completion_time: Optional[datetime] = None
    user_satisfaction: Optional[float] = None  # 1-5评分


@dataclass
class BayesianMetrics:
    """贝叶斯学习指标"""
    prior_beliefs: Dict[str, float]
    posterior_beliefs: Dict[str, float]
    likelihood_evidence: Dict[str, float]
    confidence_interval: Tuple[float, float]
    update_strength: float


@dataclass
class LearningMetrics:
    """学习指标"""
    total_choices: int
    recent_accuracy: float
    framework_preferences: Dict[str, float]
    context_preferences: Dict[str, float]
    learning_trend: str
    confidence_score: float
    bayesian_metrics: Optional[BayesianMetrics] = None


class UserPreferenceLearning:
    """用户偏好学习引擎 - US-013核心实现"""
    
    def __init__(self, config: PMConfig):
        self.config = config
        self.choice_history: List[UserChoice] = []
        self.preferences_file = config.data_dir / "user_preferences.json"
        self.choices_file = config.data_dir / "user_choices.json"
        
        self._load_choice_history()
        self._initialize_learning_parameters()
        
        logger.info("User preference learning engine initialized",
                   historical_choices=len(self.choice_history))
    
    def _load_choice_history(self) -> None:
        """加载用户选择历史"""
        
        if self.choices_file.exists():
            try:
                with open(self.choices_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                for choice_data in data:
                    # 转换日期字符串
                    choice_data['chosen_at'] = datetime.fromisoformat(choice_data['chosen_at'])
                    if choice_data.get('completion_time'):
                        choice_data['completion_time'] = datetime.fromisoformat(choice_data['completion_time'])
                    
                    choice = UserChoice(**choice_data)
                    self.choice_history.append(choice)
                    
                logger.info("Choice history loaded", 
                           choices=len(self.choice_history))
                           
            except Exception as e:
                logger.warning("Failed to load choice history", error=str(e))
                self.choice_history = []
        else:
            self.choice_history = []
    
    def _save_choice_history(self) -> None:
        """保存用户选择历史"""
        
        try:
            self.choices_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 转换为可序列化格式
            serializable_choices = []
            for choice in self.choice_history:
                choice_dict = asdict(choice)
                choice_dict['chosen_at'] = choice.chosen_at.isoformat()
                if choice.completion_time:
                    choice_dict['completion_time'] = choice.completion_time.isoformat()
                serializable_choices.append(choice_dict)
            
            with open(self.choices_file, 'w', encoding='utf-8') as f:
                json.dump(serializable_choices, f, ensure_ascii=False, indent=2)
                
            logger.info("Choice history saved", choices=len(self.choice_history))
            
        except Exception as e:
            logger.error("Failed to save choice history", error=str(e))
    
    def _initialize_learning_parameters(self) -> None:
        """初始化学习参数"""

        # 学习率参数
        self.learning_rate = 0.1
        self.decay_factor = 0.95  # 历史记录衰减因子
        self.min_samples_for_learning = 5  # 最少需要的样本数

        # 时间权重
        self.recent_weight = 2.0  # 最近选择的权重
        self.time_decay_days = 30  # 30天后权重减半

        # 贝叶斯更新参数
        self.prior_confidence = 0.3  # 先验置信度
        self.evidence_weight = 0.7   # 证据权重

        # 初始化先验分布（均匀分布）
        self.prior_framework_beliefs = {
            'okr_wig': 0.25,
            '4dx': 0.20,
            'full_engagement': 0.20,
            'atomic_habits': 0.15,
            'gtd': 0.10,
            'essentialism': 0.10
        }
    
    def record_user_choice(self, 
                          task: Task,
                          recommendation_rank: int,
                          recommendation_score: float,
                          framework_scores: Dict[str, float]) -> None:
        """记录用户选择（US-013核心功能）
        
        Args:
            task: 用户选择的任务
            recommendation_rank: 在推荐列表中的排名
            recommendation_score: 推荐评分
            framework_scores: 各理论框架的评分
        """
        
        choice = UserChoice(
            task_id=task.id,
            task_title=task.title,
            chosen_at=datetime.now(),
            recommendation_rank=recommendation_rank,
            recommendation_score=recommendation_score,
            framework_scores=framework_scores,
            context=task.context.value if task.context else None,
            priority=task.priority.value if task.priority else None,
            energy_level=task.energy_required.value if task.energy_required else None
        )
        
        self.choice_history.append(choice)
        self._save_choice_history()
        
        logger.info("User choice recorded",
                   task_title=task.title[:30],
                   rank=recommendation_rank,
                   score=recommendation_score)
        
        # 触发偏好更新
        self._update_preferences()
    
    def record_task_completion(self, task_id: str, satisfaction: Optional[float] = None) -> None:
        """记录任务完成情况"""
        
        # 查找对应的选择记录
        for choice in reversed(self.choice_history):
            if choice.task_id == task_id and choice.completion_time is None:
                choice.completion_time = datetime.now()
                choice.user_satisfaction = satisfaction
                self._save_choice_history()
                
                logger.info("Task completion recorded",
                           task_id=task_id,
                           satisfaction=satisfaction)
                break
    
    def _update_preferences(self) -> None:
        """根据用户选择历史更新偏好权重"""
        
        if len(self.choice_history) < self.min_samples_for_learning:
            logger.debug("Insufficient samples for learning", 
                        samples=len(self.choice_history),
                        required=self.min_samples_for_learning)
            return
        
        # 计算理论框架偏好
        framework_preferences = self._calculate_framework_preferences()
        
        # 计算情境偏好
        context_preferences = self._calculate_context_preferences()
        
        # 计算时间偏好
        time_preferences = self._calculate_time_preferences()
        
        # 保存更新的偏好
        self._save_learned_preferences({
            'framework_weights': framework_preferences,
            'context_preferences': context_preferences,
            'time_preferences': time_preferences,
            'last_updated': datetime.now().isoformat(),
            'sample_count': len(self.choice_history)
        })
        
        logger.info("Preferences updated",
                   frameworks=len(framework_preferences),
                   contexts=len(context_preferences))

    def _bayesian_update(self, prior_beliefs: Dict[str, float],
                        evidence: Dict[str, float]) -> Tuple[Dict[str, float], BayesianMetrics]:
        """使用贝叶斯定理更新偏好权重

        P(θ|D) = P(D|θ) × P(θ) / P(D)
        后验 = 似然 × 先验 / 边际化

        Args:
            prior_beliefs: 先验信念分布
            evidence: 观测到的证据/似然

        Returns:
            (posterior_beliefs, bayesian_metrics)
        """

        # 计算似然 × 先验
        unnormalized_posterior = {}
        total_evidence = 0

        for framework in prior_beliefs:
            likelihood = evidence.get(framework, 0.1)  # 默认小概率
            prior = prior_beliefs[framework]
            unnormalized_posterior[framework] = likelihood * prior
            total_evidence += unnormalized_posterior[framework]

        # 归一化获得后验分布
        posterior_beliefs = {}
        for framework in prior_beliefs:
            posterior_beliefs[framework] = (
                unnormalized_posterior[framework] / total_evidence
                if total_evidence > 0 else prior_beliefs[framework]
            )

        # 计算更新强度（KL散度）
        kl_divergence = 0
        for framework in prior_beliefs:
            if posterior_beliefs[framework] > 0 and prior_beliefs[framework] > 0:
                kl_divergence += posterior_beliefs[framework] * math.log(
                    posterior_beliefs[framework] / prior_beliefs[framework]
                )

        # 计算置信区间（基于样本数）
        n_samples = len(self.choice_history)
        confidence_width = 1.96 / math.sqrt(max(n_samples, 1))  # 95%置信区间
        confidence_interval = (
            max(0, self.confidence_score - confidence_width),
            min(1, self.confidence_score + confidence_width)
        )

        bayesian_metrics = BayesianMetrics(
            prior_beliefs=prior_beliefs.copy(),
            posterior_beliefs=posterior_beliefs.copy(),
            likelihood_evidence=evidence.copy(),
            confidence_interval=confidence_interval,
            update_strength=kl_divergence
        )

        logger.info("Bayesian update completed",
                   kl_divergence=round(kl_divergence, 4),
                   confidence_interval=[round(x, 3) for x in confidence_interval])

        return posterior_beliefs, bayesian_metrics

    def _calculate_framework_preferences(self) -> Dict[str, float]:
        """计算理论框架偏好权重"""
        
        # 获取最近的选择记录（最近30天）
        recent_cutoff = datetime.now() - timedelta(days=30)
        recent_choices = [
            choice for choice in self.choice_history
            if choice.chosen_at >= recent_cutoff
        ]
        
        if not recent_choices:
            recent_choices = self.choice_history[-10:]  # 最近10次选择
        
        # 分析高排名选择的框架特征
        framework_scores = {}
        total_weight = 0
        
        for choice in recent_choices:
            # 计算时间权重（越近的选择权重越高）
            days_ago = (datetime.now() - choice.chosen_at).days
            time_weight = math.exp(-days_ago / self.time_decay_days)
            
            # 排名权重（排名越高权重越大）
            rank_weight = 1.0 / choice.recommendation_rank
            
            # 评分权重
            score_weight = choice.recommendation_score / 10.0
            
            combined_weight = time_weight * rank_weight * score_weight
            total_weight += combined_weight
            
            # 累积各框架的加权评分
            for framework, score in choice.framework_scores.items():
                if framework not in framework_scores:
                    framework_scores[framework] = 0
                framework_scores[framework] += score * combined_weight
        
        # 归一化权重
        if total_weight > 0:
            for framework in framework_scores:
                framework_scores[framework] /= total_weight
        
        # 与默认权重进行平滑混合
        default_weights = {
            'okr_wig': 0.25,
            '4dx': 0.20,
            'full_engagement': 0.20,
            'atomic_habits': 0.15,
            'gtd': 0.10,
            'essentialism': 0.10
        }
        
        # 使用贝叶斯更新替代简单线性混合
        # 将观测到的框架评分作为似然证据
        evidence = {}
        for framework in default_weights:
            evidence[framework] = framework_scores.get(framework, 0.1)

        # 使用先验信念进行贝叶斯更新
        posterior_weights, _ = self._bayesian_update(
            prior_beliefs=self.prior_framework_beliefs,
            evidence=evidence
        )

        # 学习强度基于样本数量，控制贝叶斯更新vs默认权重的平衡
        learning_strength = min(len(recent_choices) / 20.0, 1.0)

        final_weights = {}
        for framework in default_weights:
            # 混合贝叶斯后验和默认权重
            bayesian_weight = posterior_weights.get(framework, default_weights[framework])
            final_weights[framework] = (
                (1 - learning_strength) * default_weights[framework] +
                learning_strength * bayesian_weight
            )

        # 确保权重和为1
        total = sum(final_weights.values())
        if total > 0:
            for framework in final_weights:
                final_weights[framework] /= total

        return final_weights
    
    def _calculate_context_preferences(self) -> Dict[str, float]:
        """计算情境偏好"""
        
        context_counts = {}
        total_choices = 0
        
        # 统计最近选择的情境
        recent_cutoff = datetime.now() - timedelta(days=14)  # 最近2周
        recent_choices = [
            choice for choice in self.choice_history
            if choice.chosen_at >= recent_cutoff and choice.context
        ]
        
        for choice in recent_choices:
            context = choice.context
            if context not in context_counts:
                context_counts[context] = 0
            context_counts[context] += 1
            total_choices += 1
        
        # 转换为偏好权重
        context_preferences = {}
        if total_choices > 0:
            for context, count in context_counts.items():
                context_preferences[context] = count / total_choices
        
        return context_preferences
    
    def _calculate_time_preferences(self) -> Dict[str, float]:
        """计算时间偏好模式"""
        
        hour_preferences = {}
        
        for choice in self.choice_history:
            hour = choice.chosen_at.hour
            hour_group = self._get_hour_group(hour)
            
            if hour_group not in hour_preferences:
                hour_preferences[hour_group] = 0
            hour_preferences[hour_group] += 1
        
        # 归一化
        total = sum(hour_preferences.values())
        if total > 0:
            for hour_group in hour_preferences:
                hour_preferences[hour_group] /= total
        
        return hour_preferences
    
    def _get_hour_group(self, hour: int) -> str:
        """获取时间段分组"""
        if 6 <= hour < 12:
            return "morning"
        elif 12 <= hour < 17:
            return "afternoon"
        elif 17 <= hour < 21:
            return "evening"
        else:
            return "night"
    
    def _save_learned_preferences(self, preferences: Dict[str, Any]) -> None:
        """保存学习到的偏好"""
        
        try:
            self.preferences_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.preferences_file, 'w', encoding='utf-8') as f:
                json.dump(preferences, f, ensure_ascii=False, indent=2)
                
            logger.info("Learned preferences saved")
            
        except Exception as e:
            logger.error("Failed to save preferences", error=str(e))
    
    def get_learned_preferences(self) -> Optional[Dict[str, Any]]:
        """获取学习到的偏好"""
        
        if self.preferences_file.exists():
            try:
                with open(self.preferences_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning("Failed to load preferences", error=str(e))
        
        return None
    
    def get_learning_metrics(self) -> LearningMetrics:
        """获取学习指标（US-013验收标准）"""
        
        total_choices = len(self.choice_history)
        
        # 计算最近准确率（用户选择高排名推荐的比例）
        recent_choices = self.choice_history[-20:] if self.choice_history else []
        high_rank_choices = sum(1 for c in recent_choices if c.recommendation_rank <= 3)
        recent_accuracy = high_rank_choices / len(recent_choices) if recent_choices else 0.0
        
        # 获取框架偏好
        learned_prefs = self.get_learned_preferences()
        framework_preferences = learned_prefs.get('framework_weights', {}) if learned_prefs else {}
        context_preferences = learned_prefs.get('context_preferences', {}) if learned_prefs else {}
        
        # 评估学习趋势
        if total_choices < 5:
            learning_trend = "初期学习"
        elif recent_accuracy > 0.7:
            learning_trend = "学习良好"
        elif recent_accuracy > 0.5:
            learning_trend = "稳步改进"
        else:
            learning_trend = "需要更多数据"
        
        # 计算置信度
        confidence_score = min(total_choices / 50.0, 1.0) * recent_accuracy

        # 生成贝叶斯指标演示
        bayesian_metrics = None
        if total_choices >= self.min_samples_for_learning:
            # 计算当前观测证据
            recent_choices = self.choice_history[-10:] if self.choice_history else []
            evidence = {}
            for framework in self.prior_framework_beliefs:
                # 基于最近选择计算每个框架的观测似然
                framework_selections = sum(
                    1 for choice in recent_choices
                    if choice.framework_scores.get(framework, 0) > 0.5
                )
                evidence[framework] = (framework_selections / len(recent_choices)
                                     if recent_choices else 0.1)

            # 执行贝叶斯更新以获取指标
            _, bayesian_metrics = self._bayesian_update(
                prior_beliefs=self.prior_framework_beliefs,
                evidence=evidence
            )

        return LearningMetrics(
            total_choices=total_choices,
            recent_accuracy=recent_accuracy,
            framework_preferences=framework_preferences,
            context_preferences=context_preferences,
            learning_trend=learning_trend,
            confidence_score=confidence_score,
            bayesian_metrics=bayesian_metrics
        )
    
    def suggest_optimal_time(self, task: Task) -> Optional[str]:
        """基于学习到的时间偏好建议最佳执行时间"""
        
        learned_prefs = self.get_learned_preferences()
        if not learned_prefs or 'time_preferences' not in learned_prefs:
            return None
        
        time_prefs = learned_prefs['time_preferences']
        
        # 基于任务特征推荐时间
        if task.energy_required == EnergyLevel.HIGH:
            # 高精力任务建议在用户最活跃的时间段
            best_time = max(time_prefs.items(), key=lambda x: x[1])
            return best_time[0]
        elif task.energy_required == EnergyLevel.LOW:
            # 低精力任务可以在非高峰时段
            time_options = [(k, v) for k, v in time_prefs.items()]
            time_options.sort(key=lambda x: x[1])
            return time_options[0][0] if time_options else None
        
        return None