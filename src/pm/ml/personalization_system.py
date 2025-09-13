"""深度机器学习个性化系统

基于用户行为数据和结果反馈的自适应学习系统，提供：
- 用户行为模式识别
- 个性化推荐算法
- 自适应权重调整  
- 增量学习更新
- 用户画像构建
"""

import numpy as np
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field, asdict
from collections import defaultdict, deque
import structlog
import hashlib

from pm.core.config import PMConfig
from pm.models.task import Task, TaskStatus, TaskContext, TaskPriority, EnergyLevel

logger = structlog.get_logger(__name__)


@dataclass
class UserBehaviorPattern:
    """用户行为模式"""
    pattern_id: str
    pattern_type: str  # 'productivity', 'preference', 'decision', 'execution'
    frequency: float  # 0.0-1.0
    confidence: float  # 0.0-1.0
    last_observed: datetime
    feature_vector: List[float]
    outcome_correlation: float  # 与积极结果的相关性
    

@dataclass  
class PersonalizationFeatures:
    """个性化特征集"""
    # 时间偏好特征
    preferred_work_hours: List[int] = field(default_factory=list)
    peak_productivity_times: List[str] = field(default_factory=list)
    work_session_duration_pref: int = 60  # minutes
    break_frequency_pref: int = 15  # minutes
    
    # 任务偏好特征
    preferred_task_contexts: List[TaskContext] = field(default_factory=list)
    preferred_task_durations: List[int] = field(default_factory=list)
    energy_level_patterns: Dict[str, float] = field(default_factory=dict)
    completion_patterns: Dict[str, float] = field(default_factory=dict)
    
    # 决策偏好特征
    decision_speed_preference: str = "moderate"  # 'fast', 'moderate', 'thorough'
    risk_tolerance: float = 0.5  # 0.0-1.0
    novelty_seeking: float = 0.5  # 0.0-1.0
    structure_preference: float = 0.5  # 0.0-1.0 (喜欢结构化vs灵活)
    
    # 学习偏好特征
    learning_style: str = "mixed"  # 'visual', 'auditory', 'kinesthetic', 'mixed'
    feedback_preference: str = "regular"  # 'minimal', 'regular', 'frequent'
    goal_orientation: str = "balanced"  # 'achievement', 'learning', 'balanced'
    
    # 社交偏好特征  
    collaboration_preference: float = 0.5  # 0.0-1.0
    communication_style: str = "direct"  # 'direct', 'collaborative', 'supportive'
    
    def to_feature_vector(self) -> np.ndarray:
        """转换为数值特征向量"""
        vector = []
        
        # 时间特征
        vector.extend([
            len(self.preferred_work_hours) / 24,
            self.work_session_duration_pref / 180,
            self.break_frequency_pref / 60
        ])
        
        # 任务特征
        vector.extend([
            len(self.preferred_task_contexts) / len(TaskContext),
            np.mean(self.preferred_task_durations) / 240 if self.preferred_task_durations else 0.5,
            np.mean(list(self.energy_level_patterns.values())) if self.energy_level_patterns else 0.5
        ])
        
        # 决策特征
        decision_speed_map = {'fast': 0.2, 'moderate': 0.5, 'thorough': 0.8}
        vector.extend([
            decision_speed_map.get(self.decision_speed_preference, 0.5),
            self.risk_tolerance,
            self.novelty_seeking,
            self.structure_preference
        ])
        
        # 学习和社交特征
        vector.extend([
            self.collaboration_preference,
            1.0 if self.goal_orientation == 'achievement' else 0.5 if self.goal_orientation == 'balanced' else 0.0
        ])
        
        return np.array(vector, dtype=np.float32)


@dataclass
class PersonalizationModel:
    """个性化模型"""
    user_id: str
    features: PersonalizationFeatures
    behavior_patterns: List[UserBehaviorPattern] = field(default_factory=list)
    preference_weights: Dict[str, float] = field(default_factory=dict)
    success_history: deque = field(default_factory=lambda: deque(maxlen=100))
    model_version: str = "1.0"
    last_updated: datetime = field(default_factory=datetime.now)
    training_iterations: int = 0
    
    def update_success_history(self, action: str, outcome: float, context: Dict[str, Any]):
        """更新成功历史记录"""
        self.success_history.append({
            'timestamp': datetime.now(),
            'action': action,
            'outcome': outcome,  # 0.0-1.0
            'context': context
        })
        
    def get_feature_importance(self) -> Dict[str, float]:
        """获取特征重要性"""
        if not self.success_history:
            return {}
            
        # 简化的特征重要性计算
        feature_impacts = defaultdict(float)
        for record in self.success_history:
            outcome = record['outcome']
            context = record['context']
            
            for key, value in context.items():
                if isinstance(value, (int, float)):
                    feature_impacts[key] += outcome * abs(value)
                    
        # 归一化
        total_impact = sum(feature_impacts.values())
        if total_impact > 0:
            return {k: v/total_impact for k, v in feature_impacts.items()}
        return {}


class PersonalizationSystem:
    """深度机器学习个性化系统"""
    
    def __init__(self, config: PMConfig):
        self.config = config
        self.logger = structlog.get_logger(__name__)
        self.models: Dict[str, PersonalizationModel] = {}
        self.global_patterns: Dict[str, Any] = {}
        
        # 学习超参数
        self.learning_rate = 0.01
        self.decay_factor = 0.99
        self.min_samples_for_learning = 5
        self.feature_importance_threshold = 0.1
        
        self._load_models()
        
    def _load_models(self):
        """加载已保存的个性化模型"""
        try:
            model_path = self.config.data_dir / "personalization_models.json"
            if model_path.exists():
                with open(model_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                for user_id, model_data in data.items():
                    # 重构PersonalizationModel
                    features_data = model_data['features']
                    features = PersonalizationFeatures(**features_data)
                    
                    model = PersonalizationModel(
                        user_id=user_id,
                        features=features,
                        preference_weights=model_data.get('preference_weights', {}),
                        model_version=model_data.get('model_version', '1.0'),
                        training_iterations=model_data.get('training_iterations', 0)
                    )
                    
                    # 重构成功历史
                    for history_item in model_data.get('success_history', []):
                        model.success_history.append(history_item)
                        
                    self.models[user_id] = model
                    
                self.logger.info("个性化模型加载完成", models_count=len(self.models))
                
        except Exception as e:
            self.logger.warning("个性化模型加载失败", error=str(e))
            
    def _save_models(self):
        """保存个性化模型"""
        try:
            model_path = self.config.data_dir / "personalization_models.json"
            
            data = {}
            for user_id, model in self.models.items():
                data[user_id] = {
                    'features': asdict(model.features),
                    'preference_weights': model.preference_weights,
                    'success_history': list(model.success_history),
                    'model_version': model.model_version,
                    'training_iterations': model.training_iterations,
                    'last_updated': model.last_updated.isoformat()
                }
                
            with open(model_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            self.logger.info("个性化模型保存完成", models_count=len(self.models))
            
        except Exception as e:
            self.logger.error("个性化模型保存失败", error=str(e))
            
    def get_or_create_user_model(self, user_id: str) -> PersonalizationModel:
        """获取或创建用户个性化模型"""
        if user_id not in self.models:
            self.models[user_id] = PersonalizationModel(
                user_id=user_id,
                features=PersonalizationFeatures()
            )
            self.logger.info("创建新用户个性化模型", user_id=user_id)
            
        return self.models[user_id]
        
    def update_user_behavior(
        self,
        user_id: str,
        action_taken: str,
        context: Dict[str, Any],
        outcome_score: float
    ):
        """更新用户行为数据"""
        model = self.get_or_create_user_model(user_id)
        
        # 更新成功历史
        model.update_success_history(action_taken, outcome_score, context)
        
        # 提取行为模式
        self._extract_behavior_patterns(model, action_taken, context, outcome_score)
        
        # 更新偏好权重
        self._update_preference_weights(model, action_taken, context, outcome_score)
        
        # 增量学习
        if len(model.success_history) >= self.min_samples_for_learning:
            self._incremental_learning_update(model)
            
        model.last_updated = datetime.now()
        self._save_models()
        
    def _extract_behavior_patterns(
        self,
        model: PersonalizationModel, 
        action: str,
        context: Dict[str, Any],
        outcome: float
    ):
        """从用户行为中提取模式"""
        
        # 时间模式识别
        current_hour = datetime.now().hour
        if outcome > 0.7:  # 高成功率的行为
            if current_hour not in model.features.preferred_work_hours:
                model.features.preferred_work_hours.append(current_hour)
                
        # 任务上下文偏好
        if 'task_context' in context and outcome > 0.6:
            task_context = context['task_context']
            if task_context not in model.features.preferred_task_contexts:
                model.features.preferred_task_contexts.append(TaskContext(task_context))
                
        # 任务时长偏好
        if 'estimated_duration' in context and outcome > 0.6:
            duration = context['estimated_duration']
            model.features.preferred_task_durations.append(duration)
            
            # 保持最近50个偏好记录
            if len(model.features.preferred_task_durations) > 50:
                model.features.preferred_task_durations = model.features.preferred_task_durations[-50:]
                
        # 能量级别模式
        if 'energy_level' in context:
            energy_key = f"{current_hour}_{context['energy_level']}"
            if energy_key not in model.features.energy_level_patterns:
                model.features.energy_level_patterns[energy_key] = outcome
            else:
                # 指数移动平均更新
                current_val = model.features.energy_level_patterns[energy_key]
                model.features.energy_level_patterns[energy_key] = (
                    current_val * 0.8 + outcome * 0.2
                )
                
    def _update_preference_weights(
        self,
        model: PersonalizationModel,
        action: str, 
        context: Dict[str, Any],
        outcome: float
    ):
        """更新偏好权重"""
        
        # 基于结果调整权重
        weight_adjustment = (outcome - 0.5) * self.learning_rate
        
        # 更新相关特征权重
        for key, value in context.items():
            if key in model.preference_weights:
                model.preference_weights[key] += weight_adjustment
            else:
                model.preference_weights[key] = 0.5 + weight_adjustment
                
            # 限制权重范围
            model.preference_weights[key] = max(0.0, min(1.0, model.preference_weights[key]))
            
    def _incremental_learning_update(self, model: PersonalizationModel):
        """增量学习更新"""
        
        if len(model.success_history) < self.min_samples_for_learning:
            return
            
        # 计算最近行为的平均成功率
        recent_outcomes = [record['outcome'] for record in list(model.success_history)[-10:]]
        avg_recent_success = np.mean(recent_outcomes)
        
        # 调整学习率
        if avg_recent_success > 0.7:
            # 表现良好，降低学习率以稳定模型
            self.learning_rate = max(0.001, self.learning_rate * self.decay_factor)
        elif avg_recent_success < 0.4:
            # 表现不佳，提高学习率以快速调整
            self.learning_rate = min(0.05, self.learning_rate * 1.1)
            
        model.training_iterations += 1
        
        # 特征重要性更新
        feature_importance = model.get_feature_importance()
        for feature, importance in feature_importance.items():
            if importance > self.feature_importance_threshold:
                if feature in model.preference_weights:
                    model.preference_weights[feature] = (
                        model.preference_weights[feature] * 0.9 + importance * 0.1
                    )
                    
    def generate_personalized_recommendations(
        self,
        user_id: str,
        base_recommendations: List[Dict[str, Any]],
        current_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """生成个性化推荐"""
        
        model = self.get_or_create_user_model(user_id)
        
        if model.training_iterations < 3:
            # 新用户，使用基础推荐
            return base_recommendations
            
        personalized_recs = []
        
        for rec in base_recommendations:
            # 计算个性化分数
            personalized_score = self._calculate_personalized_score(
                rec, model, current_context
            )
            
            # 添加个性化信息
            personalized_rec = rec.copy()
            personalized_rec['personalized_score'] = personalized_score
            personalized_rec['personalization_reasons'] = self._generate_personalization_reasons(
                rec, model, current_context
            )
            
            personalized_recs.append(personalized_rec)
            
        # 按个性化分数排序
        personalized_recs.sort(key=lambda x: x['personalized_score'], reverse=True)
        
        return personalized_recs
        
    def _calculate_personalized_score(
        self,
        recommendation: Dict[str, Any],
        model: PersonalizationModel,
        context: Dict[str, Any]
    ) -> float:
        """计算个性化评分"""
        
        base_score = recommendation.get('confidence', 0.5)
        
        # 特征匹配度计算
        feature_matches = 0
        total_features = 0
        
        # 时间偏好匹配
        current_hour = datetime.now().hour
        if current_hour in model.features.preferred_work_hours:
            feature_matches += 1
        total_features += 1
        
        # 任务上下文匹配
        if 'context' in recommendation:
            rec_context = recommendation['context']
            if rec_context in [ctx.value for ctx in model.features.preferred_task_contexts]:
                feature_matches += 2  # 权重更高
        total_features += 2
        
        # 估计时长偏好匹配
        if 'estimated_duration' in recommendation and model.features.preferred_task_durations:
            rec_duration = recommendation['estimated_duration']
            avg_preferred_duration = np.mean(model.features.preferred_task_durations)
            
            # 时长相似度
            duration_similarity = 1.0 - abs(rec_duration - avg_preferred_duration) / max(rec_duration, avg_preferred_duration)
            feature_matches += duration_similarity
            
        total_features += 1
        
        # 能量级别匹配
        if 'energy_required' in recommendation:
            energy_key = f"{current_hour}_{recommendation['energy_required']}"
            if energy_key in model.features.energy_level_patterns:
                energy_success_rate = model.features.energy_level_patterns[energy_key]
                feature_matches += energy_success_rate
                
        total_features += 1
        
        # 偏好权重应用
        preference_boost = 0.0
        for key, value in recommendation.items():
            if key in model.preference_weights:
                preference_boost += model.preference_weights[key] * 0.1
                
        # 计算最终个性化分数
        if total_features > 0:
            feature_match_score = feature_matches / total_features
        else:
            feature_match_score = 0.5
            
        personalized_score = (
            base_score * 0.6 + 
            feature_match_score * 0.3 + 
            preference_boost * 0.1
        )
        
        return max(0.0, min(1.0, personalized_score))
        
    def _generate_personalization_reasons(
        self,
        recommendation: Dict[str, Any],
        model: PersonalizationModel,
        context: Dict[str, Any]
    ) -> List[str]:
        """生成个性化原因说明"""
        
        reasons = []
        current_hour = datetime.now().hour
        
        # 时间偏好原因
        if current_hour in model.features.preferred_work_hours:
            reasons.append(f"符合您在 {current_hour}:00 的高效工作时间偏好")
            
        # 任务上下文原因
        if 'context' in recommendation:
            rec_context = recommendation['context']
            if rec_context in [ctx.value for ctx in model.features.preferred_task_contexts]:
                reasons.append(f"匹配您偏好的 {rec_context} 工作场景")
                
        # 任务时长原因
        if 'estimated_duration' in recommendation and model.features.preferred_task_durations:
            rec_duration = recommendation['estimated_duration']
            avg_preferred = np.mean(model.features.preferred_task_durations)
            
            if abs(rec_duration - avg_preferred) < 15:  # 15分钟以内差异
                reasons.append(f"符合您偏好的 {int(avg_preferred)} 分钟任务时长")
                
        # 成功历史原因
        if len(model.success_history) > 10:
            recent_success = np.mean([r['outcome'] for r in list(model.success_history)[-10:]])
            if recent_success > 0.7:
                reasons.append("基于您最近的高成功率表现模式推荐")
                
        # 如果没有具体原因，添加通用原因
        if not reasons:
            reasons.append("基于您的个人行为偏好分析推荐")
            
        return reasons
        
    def get_user_insights(self, user_id: str) -> Dict[str, Any]:
        """获取用户行为洞察"""
        
        if user_id not in self.models:
            return {'message': '用户数据不足，需要更多行为数据进行分析'}
            
        model = self.models[user_id]
        
        insights = {
            'user_id': user_id,
            'model_maturity': 'high' if model.training_iterations > 20 else 'medium' if model.training_iterations > 5 else 'low',
            'data_points': len(model.success_history),
            'last_updated': model.last_updated.isoformat(),
            'preferred_work_hours': model.features.preferred_work_hours,
            'preferred_contexts': [ctx.value for ctx in model.features.preferred_task_contexts],
            'avg_preferred_duration': int(np.mean(model.features.preferred_task_durations)) if model.features.preferred_task_durations else None,
            'recent_success_rate': np.mean([r['outcome'] for r in list(model.success_history)[-10:]]) if len(model.success_history) >= 10 else None,
            'top_preferences': dict(sorted(model.preference_weights.items(), key=lambda x: x[1], reverse=True)[:5]),
            'feature_importance': model.get_feature_importance()
        }
        
        return insights


# ==================== AI可调用工具函数 ====================

def initialize_personalization_system() -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    初始化个性化系统
    
    Returns:
        Tuple[bool, str, Optional[Dict[str, Any]]]: (成功状态, 消息, 系统信息)
    """
    try:
        logger.info("初始化个性化系统")
        
        config = PMConfig()
        system = PersonalizationSystem(config)
        
        result = {
            'system_initialized': True,
            'loaded_models_count': len(system.models),
            'learning_rate': system.learning_rate,
            'initialization_timestamp': datetime.now().isoformat()
        }
        
        logger.info("个性化系统初始化完成", models_count=len(system.models))
        return True, f"个性化系统初始化完成，加载 {len(system.models)} 个用户模型", result
        
    except Exception as e:
        logger.error("个性化系统初始化失败", error=str(e))
        return False, f"初始化失败: {str(e)}", None


def update_user_personalization(
    user_id: str,
    action_taken: str,
    context: Dict[str, Any],
    outcome_score: float
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    更新用户个性化数据
    
    Args:
        user_id: 用户ID
        action_taken: 用户采取的行动
        context: 行动上下文
        outcome_score: 结果评分 (0.0-1.0)
        
    Returns:
        Tuple[bool, str, Optional[Dict[str, Any]]]: (成功状态, 消息, 更新信息)
    """
    try:
        logger.info("更新用户个性化数据", 
                   user_id=user_id, 
                   action=action_taken,
                   outcome=outcome_score)
        
        config = PMConfig()
        system = PersonalizationSystem(config)
        
        # 更新用户行为
        system.update_user_behavior(user_id, action_taken, context, outcome_score)
        
        # 获取更新后的模型信息
        model = system.get_or_create_user_model(user_id)
        
        result = {
            'user_id': user_id,
            'action_recorded': action_taken,
            'outcome_score': outcome_score,
            'total_data_points': len(model.success_history),
            'training_iterations': model.training_iterations,
            'last_updated': model.last_updated.isoformat(),
            'model_maturity': 'high' if model.training_iterations > 20 else 'medium' if model.training_iterations > 5 else 'low'
        }
        
        logger.info("用户个性化数据更新完成", 
                   data_points=len(model.success_history))
        return True, f"已更新用户 {user_id} 的个性化数据", result
        
    except Exception as e:
        logger.error("用户个性化数据更新失败", error=str(e))
        return False, f"更新失败: {str(e)}", None


def get_personalized_recommendations(
    user_id: str,
    base_recommendations: List[Dict[str, Any]],
    current_context: Dict[str, Any]
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    获取个性化推荐
    
    Args:
        user_id: 用户ID
        base_recommendations: 基础推荐列表
        current_context: 当前上下文
        
    Returns:
        Tuple[bool, str, Optional[Dict[str, Any]]]: (成功状态, 消息, 个性化推荐)
    """
    try:
        logger.info("生成个性化推荐", 
                   user_id=user_id,
                   base_count=len(base_recommendations))
        
        config = PMConfig()
        system = PersonalizationSystem(config)
        
        # 生成个性化推荐
        personalized_recs = system.generate_personalized_recommendations(
            user_id, base_recommendations, current_context
        )
        
        result = {
            'user_id': user_id,
            'base_recommendations_count': len(base_recommendations),
            'personalized_recommendations_count': len(personalized_recs),
            'personalized_recommendations': personalized_recs,
            'generation_timestamp': datetime.now().isoformat()
        }
        
        logger.info("个性化推荐生成完成", 
                   recommendations_count=len(personalized_recs))
        return True, f"为用户 {user_id} 生成 {len(personalized_recs)} 个个性化推荐", result
        
    except Exception as e:
        logger.error("个性化推荐生成失败", error=str(e))
        return False, f"推荐生成失败: {str(e)}", None


def get_user_behavior_insights(user_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    获取用户行为洞察
    
    Args:
        user_id: 用户ID
        
    Returns:
        Tuple[bool, str, Optional[Dict[str, Any]]]: (成功状态, 消息, 行为洞察)
    """
    try:
        logger.info("获取用户行为洞察", user_id=user_id)
        
        config = PMConfig()
        system = PersonalizationSystem(config)
        
        # 获取洞察
        insights = system.get_user_insights(user_id)
        
        if 'message' in insights:
            # 用户数据不足
            return True, insights['message'], {'insights': insights}
            
        result = {
            'insights': insights,
            'analysis_timestamp': datetime.now().isoformat()
        }
        
        logger.info("用户行为洞察获取完成", 
                   data_points=insights.get('data_points', 0))
        return True, f"获取用户 {user_id} 的行为洞察完成", result
        
    except Exception as e:
        logger.error("用户行为洞察获取失败", error=str(e))
        return False, f"洞察获取失败: {str(e)}", None