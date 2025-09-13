"""预测性分析和洞察功能

基于历史数据和趋势分析的预测系统，提供：
- 项目完成率预测
- 生产力趋势分析
- 目标达成概率预测
- 风险预警和干预建议
- 性能优化建议
"""

import numpy as np
import json
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field, asdict
from collections import defaultdict, deque
import structlog
import math
from enum import Enum

from pm.core.config import PMConfig
from pm.models.task import Task, TaskStatus, TaskContext, TaskPriority, EnergyLevel
from pm.models.project import ProjectStatus, ProjectStatus, ProjectHealth

logger = structlog.get_logger(__name__)


class PredictionType(Enum):
    """预测类型枚举"""
    COMPLETION_RATE = "completion_rate"
    PRODUCTIVITY_TREND = "productivity_trend"  
    GOAL_ACHIEVEMENT = "goal_achievement"
    PERFORMANCE_SCORE = "performance_score"
    WORKLOAD_CAPACITY = "workload_capacity"
    STRESS_LEVEL = "stress_level"
    ENERGY_PATTERN = "energy_pattern"
    CONTEXT_EFFICIENCY = "context_efficiency"


class TrendDirection(Enum):
    """趋势方向"""
    IMPROVING = "improving"
    DECLINING = "declining"
    STABLE = "stable"
    VOLATILE = "volatile"


@dataclass
class TimeSeriesPoint:
    """时间序列数据点"""
    timestamp: datetime
    value: float
    context: Dict[str, Any] = field(default_factory=dict)
    

@dataclass
class TrendAnalysis:
    """趋势分析结果"""
    metric_name: str
    direction: TrendDirection
    slope: float  # 变化率
    confidence: float  # 0.0-1.0
    r_squared: float  # 拟合优度
    volatility: float  # 波动性
    recent_change_pct: float  # 最近变化百分比
    

@dataclass
class PredictionResult:
    """预测结果"""
    prediction_id: str
    prediction_type: PredictionType
    current_value: float
    predicted_value: float
    confidence_interval: Tuple[float, float]  # (下界, 上界)
    confidence_score: float  # 0.0-1.0
    prediction_horizon: timedelta
    contributing_factors: Dict[str, float]  # 因子 -> 贡献度
    trend_analysis: TrendAnalysis
    risk_factors: List[str]
    recommended_actions: List[str]
    created_at: datetime


@dataclass
class InsightAlert:
    """洞察预警"""
    alert_id: str
    alert_type: str  # 'opportunity', 'risk', 'trend', 'anomaly'
    severity: str  # 'low', 'medium', 'high', 'critical'
    title: str
    description: str
    affected_metrics: List[str]
    recommended_actions: List[str]
    confidence: float
    expiry_date: datetime
    

class PredictiveAnalyticsEngine:
    """预测性分析引擎"""
    
    def __init__(self, config: PMConfig):
        self.config = config
        self.logger = structlog.get_logger(__name__)
        
        # 历史数据存储
        self.time_series_data: Dict[str, List[TimeSeriesPoint]] = defaultdict(list)
        self.prediction_cache: Dict[str, PredictionResult] = {}
        self.active_alerts: List[InsightAlert] = []
        
        # 预测参数
        self.min_data_points = 7  # 最少数据点数量
        self.prediction_horizon_days = 30
        self.confidence_threshold = 0.6
        self.trend_window_days = 14
        self.volatility_threshold = 0.3
        
        self._load_historical_data()
        
    def _load_historical_data(self):
        """加载历史时间序列数据"""
        try:
            data_path = self.config.data_dir / "time_series_data.json"
            if data_path.exists():
                with open(data_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                for metric_name, points_data in data.items():
                    points = []
                    for point_data in points_data:
                        point = TimeSeriesPoint(
                            timestamp=datetime.fromisoformat(point_data['timestamp']),
                            value=point_data['value'],
                            context=point_data.get('context', {})
                        )
                        points.append(point)
                    self.time_series_data[metric_name] = points
                    
                self.logger.info("时间序列数据加载完成", 
                               metrics_count=len(self.time_series_data))
                               
        except Exception as e:
            self.logger.warning("时间序列数据加载失败", error=str(e))
            
    def _save_historical_data(self):
        """保存历史时间序列数据"""
        try:
            data_path = self.config.data_dir / "time_series_data.json"
            
            data = {}
            for metric_name, points in self.time_series_data.items():
                data[metric_name] = [
                    {
                        'timestamp': point.timestamp.isoformat(),
                        'value': point.value,
                        'context': point.context
                    }
                    for point in points[-100:]  # 保留最近100个数据点
                ]
                
            with open(data_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            self.logger.info("时间序列数据保存完成")
            
        except Exception as e:
            self.logger.error("时间序列数据保存失败", error=str(e))
            
    def add_data_point(
        self, 
        metric_name: str, 
        value: float, 
        timestamp: Optional[datetime] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """添加新的数据点"""
        if timestamp is None:
            timestamp = datetime.now()
            
        if context is None:
            context = {}
            
        point = TimeSeriesPoint(
            timestamp=timestamp,
            value=value,
            context=context
        )
        
        self.time_series_data[metric_name].append(point)
        
        # 保持数据点数量在合理范围内
        if len(self.time_series_data[metric_name]) > 200:
            self.time_series_data[metric_name] = self.time_series_data[metric_name][-100:]
            
        self._save_historical_data()
        
    def analyze_trend(self, metric_name: str, days: int = 14) -> Optional[TrendAnalysis]:
        """分析指标趋势"""
        if metric_name not in self.time_series_data:
            return None
            
        points = self.time_series_data[metric_name]
        if len(points) < self.min_data_points:
            return None
            
        # 获取指定天数内的数据
        cutoff_time = datetime.now() - timedelta(days=days)
        recent_points = [p for p in points if p.timestamp >= cutoff_time]
        
        if len(recent_points) < 3:
            return None
            
        # 线性回归分析趋势
        x_values = [(p.timestamp - recent_points[0].timestamp).total_seconds() 
                   for p in recent_points]
        y_values = [p.value for p in recent_points]
        
        # 计算斜率和相关系数
        n = len(recent_points)
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values))
        sum_x2 = sum(x * x for x in x_values)
        sum_y2 = sum(y * y for y in y_values)
        
        # 线性回归系数
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x) if (n * sum_x2 - sum_x * sum_x) != 0 else 0
        intercept = (sum_y - slope * sum_x) / n
        
        # R平方值
        mean_y = sum_y / n
        ss_tot = sum((y - mean_y) ** 2 for y in y_values)
        ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in zip(x_values, y_values))
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        
        # 波动性计算
        volatility = np.std(y_values) / np.mean(y_values) if np.mean(y_values) != 0 else 0
        
        # 最近变化百分比
        recent_change_pct = 0.0
        if len(recent_points) >= 2 and recent_points[0].value != 0:
            recent_change_pct = ((recent_points[-1].value - recent_points[0].value) / 
                               recent_points[0].value) * 100
                               
        # 判断趋势方向
        if abs(slope) < 0.01 and volatility < self.volatility_threshold:
            direction = TrendDirection.STABLE
        elif volatility > self.volatility_threshold * 2:
            direction = TrendDirection.VOLATILE
        elif slope > 0.01:
            direction = TrendDirection.IMPROVING
        else:
            direction = TrendDirection.DECLINING
            
        return TrendAnalysis(
            metric_name=metric_name,
            direction=direction,
            slope=slope,
            confidence=min(r_squared, 1.0),
            r_squared=r_squared,
            volatility=volatility,
            recent_change_pct=recent_change_pct
        )
        
    def predict_metric(
        self, 
        metric_name: str, 
        prediction_type: PredictionType,
        horizon_days: int = 30
    ) -> Optional[PredictionResult]:
        """预测指标值"""
        
        if metric_name not in self.time_series_data:
            return None
            
        points = self.time_series_data[metric_name]
        if len(points) < self.min_data_points:
            return None
            
        # 趋势分析
        trend = self.analyze_trend(metric_name, days=self.trend_window_days)
        if not trend:
            return None
            
        current_value = points[-1].value
        
        # 基于趋势进行预测
        prediction_horizon = timedelta(days=horizon_days)
        seconds_ahead = prediction_horizon.total_seconds()
        
        # 线性预测
        predicted_value = current_value + (trend.slope * seconds_ahead)
        
        # 置信区间计算
        volatility_factor = max(trend.volatility, 0.1)
        confidence_range = predicted_value * volatility_factor * 2
        confidence_interval = (
            predicted_value - confidence_range,
            predicted_value + confidence_range
        )
        
        # 置信度分数
        confidence_score = min(trend.confidence * (1 - volatility_factor), 1.0)
        
        # 贡献因子分析
        contributing_factors = self._analyze_contributing_factors(metric_name, points)
        
        # 风险因子识别
        risk_factors = self._identify_risk_factors(trend, points)
        
        # 推荐行动
        recommended_actions = self._generate_action_recommendations(
            prediction_type, trend, predicted_value, current_value
        )
        
        return PredictionResult(
            prediction_id=f"pred_{metric_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            prediction_type=prediction_type,
            current_value=current_value,
            predicted_value=predicted_value,
            confidence_interval=confidence_interval,
            confidence_score=confidence_score,
            prediction_horizon=prediction_horizon,
            contributing_factors=contributing_factors,
            trend_analysis=trend,
            risk_factors=risk_factors,
            recommended_actions=recommended_actions,
            created_at=datetime.now()
        )
        
    def _analyze_contributing_factors(
        self, 
        metric_name: str, 
        points: List[TimeSeriesPoint]
    ) -> Dict[str, float]:
        """分析贡献因子"""
        
        factors = defaultdict(list)
        
        # 从上下文中提取因子
        for point in points[-20:]:  # 分析最近20个数据点
            for key, value in point.context.items():
                if isinstance(value, (int, float)):
                    factors[key].append((value, point.value))
                    
        # 计算相关性
        correlations = {}
        for factor, values in factors.items():
            if len(values) >= 5:  # 至少5个数据点
                factor_values = [v[0] for v in values]
                metric_values = [v[1] for v in values]
                
                # 皮尔逊相关系数
                correlation = self._calculate_correlation(factor_values, metric_values)
                if not math.isnan(correlation):
                    correlations[factor] = abs(correlation)
                    
        return correlations
        
    def _calculate_correlation(self, x: List[float], y: List[float]) -> float:
        """计算皮尔逊相关系数"""
        if len(x) != len(y) or len(x) < 2:
            return 0.0
            
        mean_x = sum(x) / len(x)
        mean_y = sum(y) / len(y)
        
        numerator = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
        sum_sq_x = sum((xi - mean_x) ** 2 for xi in x)
        sum_sq_y = sum((yi - mean_y) ** 2 for yi in y)
        
        denominator = math.sqrt(sum_sq_x * sum_sq_y)
        
        if denominator == 0:
            return 0.0
            
        return numerator / denominator
        
    def _identify_risk_factors(
        self, 
        trend: TrendAnalysis, 
        points: List[TimeSeriesPoint]
    ) -> List[str]:
        """识别风险因子"""
        
        risk_factors = []
        
        # 趋势风险
        if trend.direction == TrendDirection.DECLINING:
            risk_factors.append("持续下降趋势")
            
        if trend.volatility > self.volatility_threshold:
            risk_factors.append("高波动性")
            
        if trend.confidence < self.confidence_threshold:
            risk_factors.append("低预测置信度")
            
        # 数据质量风险
        if len(points) < 14:
            risk_factors.append("历史数据不足")
            
        # 异常值检测
        recent_values = [p.value for p in points[-10:]]
        if recent_values:
            mean_val = np.mean(recent_values)
            std_val = np.std(recent_values)
            
            for value in recent_values[-3:]:  # 检查最近3个值
                if abs(value - mean_val) > 2 * std_val:
                    risk_factors.append("近期数据异常")
                    break
                    
        return risk_factors
        
    def _generate_action_recommendations(
        self,
        prediction_type: PredictionType,
        trend: TrendAnalysis,
        predicted_value: float,
        current_value: float
    ) -> List[str]:
        """生成行动建议"""
        
        actions = []
        change_pct = ((predicted_value - current_value) / current_value * 100) if current_value != 0 else 0
        
        if prediction_type == PredictionType.COMPLETION_RATE:
            if trend.direction == TrendDirection.DECLINING:
                actions.extend([
                    "重新评估任务优先级和分配",
                    "识别并消除完成障碍",
                    "考虑调整工作方法或流程"
                ])
            elif predicted_value < 0.7:
                actions.append("制定提高完成率的专项计划")
                
        elif prediction_type == PredictionType.PRODUCTIVITY_TREND:
            if trend.direction == TrendDirection.DECLINING:
                actions.extend([
                    "分析生产力下降的根本原因", 
                    "优化工作环境和工具",
                    "考虑休息和恢复策略"
                ])
            elif trend.volatility > 0.4:
                actions.append("建立更稳定的工作节奏")
                
        elif prediction_type == PredictionType.GOAL_ACHIEVEMENT:
            if predicted_value < 0.8:
                actions.extend([
                    "重新审视目标设定是否合理",
                    "分解大目标为更小的可执行步骤",
                    "增加进度检查和调整频率"
                ])
                
        # 通用建议
        if abs(change_pct) > 20:
            actions.append("密切监控关键指标变化")
            
        if trend.volatility > self.volatility_threshold:
            actions.append("识别和控制波动性来源")
            
        return actions
        
    def generate_insights_alerts(self) -> List[InsightAlert]:
        """生成洞察预警"""
        
        alerts = []
        
        for metric_name in self.time_series_data.keys():
            # 分析最近趋势
            trend = self.analyze_trend(metric_name)
            if not trend:
                continue
                
            # 趋势预警
            if trend.direction == TrendDirection.DECLINING and trend.confidence > 0.7:
                alert = InsightAlert(
                    alert_id=f"trend_{metric_name}_{datetime.now().strftime('%Y%m%d')}",
                    alert_type="risk",
                    severity="medium" if trend.recent_change_pct > -15 else "high",
                    title=f"{metric_name} 持续下降趋势",
                    description=f"过去{self.trend_window_days}天{metric_name}下降了{abs(trend.recent_change_pct):.1f}%",
                    affected_metrics=[metric_name],
                    recommended_actions=self._generate_action_recommendations(
                        PredictionType.PRODUCTIVITY_TREND, trend, 0, 1
                    ),
                    confidence=trend.confidence,
                    expiry_date=datetime.now() + timedelta(days=7)
                )
                alerts.append(alert)
                
            # 机会预警
            elif trend.direction == TrendDirection.IMPROVING and trend.confidence > 0.8:
                alert = InsightAlert(
                    alert_id=f"opportunity_{metric_name}_{datetime.now().strftime('%Y%m%d')}",
                    alert_type="opportunity",
                    severity="medium",
                    title=f"{metric_name} 表现优异",
                    description=f"过去{self.trend_window_days}天{metric_name}提升了{trend.recent_change_pct:.1f}%",
                    affected_metrics=[metric_name],
                    recommended_actions=["保持当前策略", "考虑复制成功经验到其他领域"],
                    confidence=trend.confidence,
                    expiry_date=datetime.now() + timedelta(days=7)
                )
                alerts.append(alert)
                
            # 异常预警
            if trend.volatility > self.volatility_threshold * 2:
                alert = InsightAlert(
                    alert_id=f"anomaly_{metric_name}_{datetime.now().strftime('%Y%m%d')}",
                    alert_type="anomaly",
                    severity="medium",
                    title=f"{metric_name} 异常波动",
                    description=f"{metric_name}近期波动性过高({trend.volatility:.2f})",
                    affected_metrics=[metric_name],
                    recommended_actions=["调查异常波动原因", "建立更稳定的执行模式"],
                    confidence=0.8,
                    expiry_date=datetime.now() + timedelta(days=3)
                )
                alerts.append(alert)
                
        # 更新活跃预警列表
        current_time = datetime.now()
        self.active_alerts = [alert for alert in self.active_alerts 
                            if alert.expiry_date > current_time]
        self.active_alerts.extend(alerts)
        
        return alerts
        
    def get_multi_metric_prediction(
        self, 
        metrics: List[str], 
        horizon_days: int = 30
    ) -> Dict[str, PredictionResult]:
        """获取多指标预测"""
        
        predictions = {}
        
        for metric in metrics:
            # 映射指标到预测类型
            prediction_type = self._map_metric_to_prediction_type(metric)
            
            prediction = self.predict_metric(metric, prediction_type, horizon_days)
            if prediction:
                predictions[metric] = prediction
                
        return predictions
        
    def _map_metric_to_prediction_type(self, metric_name: str) -> PredictionType:
        """映射指标名称到预测类型"""
        
        metric_lower = metric_name.lower()
        
        if "completion" in metric_lower or "complete" in metric_lower:
            return PredictionType.COMPLETION_RATE
        elif "productivity" in metric_lower or "efficient" in metric_lower:
            return PredictionType.PRODUCTIVITY_TREND
        elif "goal" in metric_lower or "achievement" in metric_lower:
            return PredictionType.GOAL_ACHIEVEMENT
        elif "performance" in metric_lower:
            return PredictionType.PERFORMANCE_SCORE
        elif "workload" in metric_lower or "capacity" in metric_lower:
            return PredictionType.WORKLOAD_CAPACITY
        elif "stress" in metric_lower:
            return PredictionType.STRESS_LEVEL
        elif "energy" in metric_lower:
            return PredictionType.ENERGY_PATTERN
        elif "context" in metric_lower or "efficiency" in metric_lower:
            return PredictionType.CONTEXT_EFFICIENCY
        else:
            return PredictionType.PRODUCTIVITY_TREND


# ==================== AI可调用工具函数 ====================

def initialize_predictive_analytics() -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    初始化预测分析引擎
    
    Returns:
        Tuple[bool, str, Optional[Dict[str, Any]]]: (成功状态, 消息, 系统信息)
    """
    try:
        logger.info("初始化预测分析引擎")
        
        config = PMConfig()
        engine = PredictiveAnalyticsEngine(config)
        
        result = {
            'engine_initialized': True,
            'available_metrics': list(engine.time_series_data.keys()),
            'total_data_points': sum(len(points) for points in engine.time_series_data.values()),
            'prediction_types': [pt.value for pt in PredictionType],
            'initialization_timestamp': datetime.now().isoformat()
        }
        
        logger.info("预测分析引擎初始化完成", 
                   metrics_count=len(engine.time_series_data))
        return True, f"预测分析引擎初始化完成，载入 {len(engine.time_series_data)} 个指标", result
        
    except Exception as e:
        logger.error("预测分析引擎初始化失败", error=str(e))
        return False, f"初始化失败: {str(e)}", None


def add_metric_data_point(
    metric_name: str,
    value: float,
    context: Optional[Dict[str, Any]] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    添加指标数据点
    
    Args:
        metric_name: 指标名称
        value: 指标值
        context: 上下文信息
        
    Returns:
        Tuple[bool, str, Optional[Dict[str, Any]]]: (成功状态, 消息, 数据点信息)
    """
    try:
        logger.info("添加指标数据点", metric=metric_name, value=value)
        
        config = PMConfig()
        engine = PredictiveAnalyticsEngine(config)
        
        # 添加数据点
        engine.add_data_point(metric_name, value, context=context)
        
        result = {
            'metric_name': metric_name,
            'value_added': value,
            'total_data_points': len(engine.time_series_data[metric_name]),
            'timestamp': datetime.now().isoformat(),
            'context': context or {}
        }
        
        logger.info("指标数据点添加完成", 
                   total_points=len(engine.time_series_data[metric_name]))
        return True, f"已添加 {metric_name} 数据点，当前共 {len(engine.time_series_data[metric_name])} 个点", result
        
    except Exception as e:
        logger.error("指标数据点添加失败", error=str(e))
        return False, f"添加失败: {str(e)}", None


def analyze_metric_trend(
    metric_name: str,
    analysis_days: int = 14
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    分析指标趋势
    
    Args:
        metric_name: 指标名称
        analysis_days: 分析天数
        
    Returns:
        Tuple[bool, str, Optional[Dict[str, Any]]]: (成功状态, 消息, 趋势分析)
    """
    try:
        logger.info("分析指标趋势", metric=metric_name, days=analysis_days)
        
        config = PMConfig()
        engine = PredictiveAnalyticsEngine(config)
        
        # 分析趋势
        trend = engine.analyze_trend(metric_name, days=analysis_days)
        
        if not trend:
            return False, f"指标 {metric_name} 数据不足，无法分析趋势", None
            
        result = {
            'metric_name': trend.metric_name,
            'trend_direction': trend.direction.value,
            'change_rate': trend.slope,
            'confidence': trend.confidence,
            'r_squared': trend.r_squared,
            'volatility': trend.volatility,
            'recent_change_pct': trend.recent_change_pct,
            'analysis_period_days': analysis_days,
            'analysis_timestamp': datetime.now().isoformat()
        }
        
        logger.info("指标趋势分析完成", 
                   direction=trend.direction.value,
                   confidence=trend.confidence)
        return True, f"{metric_name} 趋势：{trend.direction.value}，置信度 {trend.confidence:.2f}", result
        
    except Exception as e:
        logger.error("指标趋势分析失败", error=str(e))
        return False, f"趋势分析失败: {str(e)}", None


def predict_metric_value(
    metric_name: str,
    prediction_horizon_days: int = 30
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    预测指标值
    
    Args:
        metric_name: 指标名称
        prediction_horizon_days: 预测时间范围(天)
        
    Returns:
        Tuple[bool, str, Optional[Dict[str, Any]]]: (成功状态, 消息, 预测结果)
    """
    try:
        logger.info("预测指标值", 
                   metric=metric_name,
                   horizon_days=prediction_horizon_days)
        
        config = PMConfig()
        engine = PredictiveAnalyticsEngine(config)
        
        # 确定预测类型
        prediction_type = engine._map_metric_to_prediction_type(metric_name)
        
        # 执行预测
        prediction = engine.predict_metric(
            metric_name, 
            prediction_type, 
            prediction_horizon_days
        )
        
        if not prediction:
            return False, f"指标 {metric_name} 数据不足，无法预测", None
            
        result = {
            'prediction_id': prediction.prediction_id,
            'metric_name': metric_name,
            'prediction_type': prediction.prediction_type.value,
            'current_value': prediction.current_value,
            'predicted_value': prediction.predicted_value,
            'confidence_interval': {
                'lower': prediction.confidence_interval[0],
                'upper': prediction.confidence_interval[1]
            },
            'confidence_score': prediction.confidence_score,
            'prediction_horizon_days': prediction_horizon_days,
            'trend_direction': prediction.trend_analysis.direction.value,
            'contributing_factors': prediction.contributing_factors,
            'risk_factors': prediction.risk_factors,
            'recommended_actions': prediction.recommended_actions,
            'prediction_timestamp': prediction.created_at.isoformat()
        }
        
        logger.info("指标预测完成", 
                   predicted_value=prediction.predicted_value,
                   confidence=prediction.confidence_score)
        return True, f"{metric_name} 预测值：{prediction.predicted_value:.2f}，置信度 {prediction.confidence_score:.2f}", result
        
    except Exception as e:
        logger.error("指标预测失败", error=str(e))
        return False, f"预测失败: {str(e)}", None


def generate_insight_alerts() -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    生成洞察预警
    
    Returns:
        Tuple[bool, str, Optional[Dict[str, Any]]]: (成功状态, 消息, 预警信息)
    """
    try:
        logger.info("生成洞察预警")
        
        config = PMConfig()
        engine = PredictiveAnalyticsEngine(config)
        
        # 生成预警
        alerts = engine.generate_insights_alerts()
        
        result = {
            'alerts_generated': len(alerts),
            'active_alerts_total': len(engine.active_alerts),
            'alerts': [
                {
                    'alert_id': alert.alert_id,
                    'type': alert.alert_type,
                    'severity': alert.severity,
                    'title': alert.title,
                    'description': alert.description,
                    'affected_metrics': alert.affected_metrics,
                    'recommended_actions': alert.recommended_actions,
                    'confidence': alert.confidence,
                    'expires': alert.expiry_date.isoformat()
                }
                for alert in alerts
            ],
            'generation_timestamp': datetime.now().isoformat()
        }
        
        logger.info("洞察预警生成完成", 
                   new_alerts=len(alerts),
                   total_active=len(engine.active_alerts))
        return True, f"生成 {len(alerts)} 个新预警，当前活跃预警 {len(engine.active_alerts)} 个", result
        
    except Exception as e:
        logger.error("洞察预警生成失败", error=str(e))
        return False, f"预警生成失败: {str(e)}", None


def get_multi_metric_predictions(
    metrics: List[str],
    prediction_horizon_days: int = 30
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    获取多指标预测
    
    Args:
        metrics: 指标名称列表
        prediction_horizon_days: 预测时间范围(天)
        
    Returns:
        Tuple[bool, str, Optional[Dict[str, Any]]]: (成功状态, 消息, 多指标预测)
    """
    try:
        logger.info("获取多指标预测", 
                   metrics_count=len(metrics),
                   horizon_days=prediction_horizon_days)
        
        config = PMConfig()
        engine = PredictiveAnalyticsEngine(config)
        
        # 获取预测
        predictions = engine.get_multi_metric_prediction(metrics, prediction_horizon_days)
        
        result = {
            'requested_metrics': metrics,
            'successful_predictions': len(predictions),
            'prediction_horizon_days': prediction_horizon_days,
            'predictions': {
                metric: {
                    'current_value': pred.current_value,
                    'predicted_value': pred.predicted_value,
                    'confidence_score': pred.confidence_score,
                    'trend_direction': pred.trend_analysis.direction.value,
                    'risk_factors': pred.risk_factors,
                    'recommended_actions': pred.recommended_actions
                }
                for metric, pred in predictions.items()
            },
            'prediction_timestamp': datetime.now().isoformat()
        }
        
        logger.info("多指标预测完成", 
                   successful_count=len(predictions))
        return True, f"成功预测 {len(predictions)} 个指标", result
        
    except Exception as e:
        logger.error("多指标预测失败", error=str(e))
        return False, f"预测失败: {str(e)}", None