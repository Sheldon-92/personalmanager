"""深度工作数据模型 - Sprint 14核心功能

基于《深度工作》理论的专注管理和深度工作时段跟踪模型
设计为AI可调用的工具函数支持
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Dict, Optional, Any


class DeepWorkType(Enum):
    """深度工作类型（基于《深度工作》理论）"""
    MONASTICISM = "monasticism"        # 禁欲主义哲学：完全隔离
    BIMODAL = "bimodal"               # 双峰哲学：分时段深度工作
    RHYTHMIC = "rhythmic"             # 节奏哲学：固定时间深度工作
    JOURNALISTIC = "journalistic"     # 记者哲学：随时转换


class FocusLevel(Enum):
    """专注程度评级"""
    SHALLOW = "shallow"               # 浅层工作
    SEMI_DEEP = "semi_deep"          # 半深度工作
    DEEP = "deep"                    # 深度工作
    PROFOUND = "profound"            # 极深工作


class DistractionType(Enum):
    """干扰类型"""
    INTERNAL = "internal"            # 内部干扰（思维游走、焦虑等）
    EXTERNAL = "external"            # 外部干扰（通知、噪音等）
    SOCIAL = "social"                # 社交干扰（他人打扰）
    TECH = "tech"                    # 技术干扰（设备、网络等）


class WorkEnvironment(Enum):
    """工作环境类型"""
    HOME_OFFICE = "home_office"      # 家庭办公室
    COWORKING = "coworking"          # 共享办公空间
    LIBRARY = "library"              # 图书馆
    CAFE = "cafe"                    # 咖啡厅
    OUTDOOR = "outdoor"              # 户外
    OTHER = "other"                  # 其他


@dataclass
class DistractionEvent:
    """干扰事件记录"""
    
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    distraction_type: DistractionType = DistractionType.EXTERNAL
    description: Optional[str] = None
    duration_seconds: Optional[int] = None  # 干扰持续时间
    recovery_time_seconds: Optional[int] = None  # 恢复专注所需时间
    severity: int = 1  # 严重程度 1-5 级
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "event_id": self.event_id,
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat(),
            "distraction_type": self.distraction_type.value,
            "description": self.description,
            "duration_seconds": self.duration_seconds,
            "recovery_time_seconds": self.recovery_time_seconds,
            "severity": self.severity
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DistractionEvent':
        """从字典创建对象"""
        return cls(
            event_id=data.get("event_id", str(uuid.uuid4())),
            session_id=data["session_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            distraction_type=DistractionType(data["distraction_type"]),
            description=data.get("description"),
            duration_seconds=data.get("duration_seconds"),
            recovery_time_seconds=data.get("recovery_time_seconds"),
            severity=data.get("severity", 1)
        )


@dataclass
class FocusMetrics:
    """专注度量化指标"""
    
    deep_work_minutes: int = 0           # 深度工作分钟数
    shallow_work_minutes: int = 0        # 浅层工作分钟数
    break_minutes: int = 0               # 休息分钟数
    distraction_count: int = 0           # 干扰次数
    focus_score: float = 0.0             # 专注评分 (0-100)
    flow_periods: int = 0                # 心流时段数量
    attention_residue: float = 0.0       # 注意力残留程度 (0-100)
    
    def calculate_focus_score(self, total_minutes: int, distractions: List[DistractionEvent]) -> float:
        """计算专注评分"""
        if total_minutes <= 0:
            return 0.0
        
        # 基础分数：深度工作时间占比
        deep_ratio = self.deep_work_minutes / total_minutes
        base_score = deep_ratio * 80  # 最高80分
        
        # 干扰惩罚：每次干扰扣分
        distraction_penalty = min(len(distractions) * 2, 30)  # 最多扣30分
        
        # 严重干扰额外惩罚
        severity_penalty = sum(d.severity for d in distractions if d.severity > 3)
        
        self.focus_score = max(0, base_score - distraction_penalty - severity_penalty)
        return self.focus_score
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "deep_work_minutes": self.deep_work_minutes,
            "shallow_work_minutes": self.shallow_work_minutes,
            "break_minutes": self.break_minutes,
            "distraction_count": self.distraction_count,
            "focus_score": self.focus_score,
            "flow_periods": self.flow_periods,
            "attention_residue": self.attention_residue
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FocusMetrics':
        """从字典创建对象"""
        return cls(
            deep_work_minutes=data.get("deep_work_minutes", 0),
            shallow_work_minutes=data.get("shallow_work_minutes", 0),
            break_minutes=data.get("break_minutes", 0),
            distraction_count=data.get("distraction_count", 0),
            focus_score=data.get("focus_score", 0.0),
            flow_periods=data.get("flow_periods", 0),
            attention_residue=data.get("attention_residue", 0.0)
        )


@dataclass
class EnvironmentSettings:
    """工作环境设置"""
    
    location: WorkEnvironment = WorkEnvironment.HOME_OFFICE
    noise_level: int = 1        # 噪音水平 1-5
    lighting_quality: int = 3   # 光照质量 1-5
    temperature: Optional[int] = None  # 温度
    air_quality: int = 3        # 空气质量 1-5
    distractions_blocked: List[str] = field(default_factory=list)  # 阻断的干扰源
    tools_available: List[str] = field(default_factory=list)       # 可用工具
    environment_score: float = 0.0  # 环境综合评分
    
    def calculate_environment_score(self) -> float:
        """计算环境综合评分"""
        # 基于各项指标计算环境评分
        factors = [self.noise_level, self.lighting_quality, self.air_quality]
        avg_score = sum(factors) / len(factors)
        
        # 干扰阻断奖励
        block_bonus = min(len(self.distractions_blocked) * 5, 20)
        
        self.environment_score = min((avg_score * 20) + block_bonus, 100)
        return self.environment_score
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "location": self.location.value,
            "noise_level": self.noise_level,
            "lighting_quality": self.lighting_quality,
            "temperature": self.temperature,
            "air_quality": self.air_quality,
            "distractions_blocked": self.distractions_blocked,
            "tools_available": self.tools_available,
            "environment_score": self.environment_score
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EnvironmentSettings':
        """从字典创建对象"""
        return cls(
            location=WorkEnvironment(data.get("location", "home_office")),
            noise_level=data.get("noise_level", 1),
            lighting_quality=data.get("lighting_quality", 3),
            temperature=data.get("temperature"),
            air_quality=data.get("air_quality", 3),
            distractions_blocked=data.get("distractions_blocked", []),
            tools_available=data.get("tools_available", []),
            environment_score=data.get("environment_score", 0.0)
        )


@dataclass
class DeepWorkSession:
    """深度工作时段主模型"""
    
    # 基本信息
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: Optional[str] = None
    work_type: DeepWorkType = DeepWorkType.RHYTHMIC
    
    # 时间信息
    planned_start: datetime = field(default_factory=datetime.now)
    planned_end: Optional[datetime] = None
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    planned_duration_minutes: int = 60
    
    # 工作内容
    primary_task: Optional[str] = None
    secondary_tasks: List[str] = field(default_factory=list)
    project_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    # 专注管理
    target_focus_level: FocusLevel = FocusLevel.DEEP
    actual_focus_level: Optional[FocusLevel] = None
    energy_level_start: int = 5    # 开始时精力水平 1-5
    energy_level_end: Optional[int] = None  # 结束时精力水平
    
    # 环境和干扰
    environment: EnvironmentSettings = field(default_factory=EnvironmentSettings)
    distractions: List[DistractionEvent] = field(default_factory=list)
    
    # 度量指标
    metrics: FocusMetrics = field(default_factory=FocusMetrics)
    
    # 反思记录
    pre_session_notes: Optional[str] = None
    post_session_reflection: Optional[str] = None
    lessons_learned: List[str] = field(default_factory=list)
    improvement_actions: List[str] = field(default_factory=list)
    
    # 元数据
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    completed: bool = False
    
    def __post_init__(self):
        """初始化后处理"""
        if not self.title:
            self.title = f"深度工作时段 - {self.planned_start.strftime('%Y-%m-%d %H:%M')}"
        
        if not self.planned_end:
            self.planned_end = self.planned_start + timedelta(minutes=self.planned_duration_minutes)
    
    def start_session(self) -> None:
        """开始深度工作时段"""
        self.actual_start = datetime.now()
        self.updated_at = datetime.now()
    
    def end_session(self, reflection: Optional[str] = None) -> None:
        """结束深度工作时段"""
        self.actual_end = datetime.now()
        self.completed = True
        self.updated_at = datetime.now()
        
        if reflection:
            self.post_session_reflection = reflection
        
        # 计算实际持续时间和度量指标
        if self.actual_start:
            total_minutes = int((self.actual_end - self.actual_start).total_seconds() / 60)
            self.metrics.calculate_focus_score(total_minutes, self.distractions)
    
    def add_distraction(self, distraction_type: DistractionType, 
                       description: Optional[str] = None,
                       severity: int = 1) -> DistractionEvent:
        """添加干扰事件"""
        distraction = DistractionEvent(
            session_id=self.session_id,
            distraction_type=distraction_type,
            description=description,
            severity=severity
        )
        self.distractions.append(distraction)
        self.metrics.distraction_count = len(self.distractions)
        self.updated_at = datetime.now()
        
        return distraction
    
    def get_actual_duration_minutes(self) -> int:
        """获取实际持续时间（分钟）"""
        if self.actual_start and self.actual_end:
            return int((self.actual_end - self.actual_start).total_seconds() / 60)
        return 0
    
    def get_efficiency_score(self) -> float:
        """计算效率评分"""
        if not self.completed:
            return 0.0
        
        actual_minutes = self.get_actual_duration_minutes()
        if actual_minutes <= 0:
            return 0.0
        
        # 基于专注度和时间效率计算
        time_efficiency = min(actual_minutes / self.planned_duration_minutes, 1.0) * 50
        focus_efficiency = self.metrics.focus_score * 0.5
        
        return min(time_efficiency + focus_efficiency, 100.0)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式（用于存储）"""
        return {
            "session_id": self.session_id,
            "title": self.title,
            "description": self.description,
            "work_type": self.work_type.value,
            "planned_start": self.planned_start.isoformat(),
            "planned_end": self.planned_end.isoformat() if self.planned_end else None,
            "actual_start": self.actual_start.isoformat() if self.actual_start else None,
            "actual_end": self.actual_end.isoformat() if self.actual_end else None,
            "planned_duration_minutes": self.planned_duration_minutes,
            "primary_task": self.primary_task,
            "secondary_tasks": self.secondary_tasks,
            "project_id": self.project_id,
            "tags": self.tags,
            "target_focus_level": self.target_focus_level.value,
            "actual_focus_level": self.actual_focus_level.value if self.actual_focus_level else None,
            "energy_level_start": self.energy_level_start,
            "energy_level_end": self.energy_level_end,
            "environment": self.environment.to_dict(),
            "distractions": [d.to_dict() for d in self.distractions],
            "metrics": self.metrics.to_dict(),
            "pre_session_notes": self.pre_session_notes,
            "post_session_reflection": self.post_session_reflection,
            "lessons_learned": self.lessons_learned,
            "improvement_actions": self.improvement_actions,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed": self.completed
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DeepWorkSession':
        """从字典创建深度工作时段对象"""
        session = cls(
            session_id=data["session_id"],
            title=data["title"],
            description=data.get("description"),
            work_type=DeepWorkType(data["work_type"]),
            planned_start=datetime.fromisoformat(data["planned_start"]),
            planned_end=datetime.fromisoformat(data["planned_end"]) if data.get("planned_end") else None,
            actual_start=datetime.fromisoformat(data["actual_start"]) if data.get("actual_start") else None,
            actual_end=datetime.fromisoformat(data["actual_end"]) if data.get("actual_end") else None,
            planned_duration_minutes=data["planned_duration_minutes"],
            primary_task=data.get("primary_task"),
            secondary_tasks=data.get("secondary_tasks", []),
            project_id=data.get("project_id"),
            tags=data.get("tags", []),
            target_focus_level=FocusLevel(data["target_focus_level"]),
            actual_focus_level=FocusLevel(data["actual_focus_level"]) if data.get("actual_focus_level") else None,
            energy_level_start=data.get("energy_level_start", 5),
            energy_level_end=data.get("energy_level_end"),
            pre_session_notes=data.get("pre_session_notes"),
            post_session_reflection=data.get("post_session_reflection"),
            lessons_learned=data.get("lessons_learned", []),
            improvement_actions=data.get("improvement_actions", []),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            completed=data.get("completed", False)
        )
        
        # 加载环境设置
        session.environment = EnvironmentSettings.from_dict(data.get("environment", {}))
        
        # 加载干扰事件
        session.distractions = [DistractionEvent.from_dict(d) for d in data.get("distractions", [])]
        
        # 加载度量指标
        session.metrics = FocusMetrics.from_dict(data.get("metrics", {}))
        
        return session
    
    def get_analysis_summary(self) -> Dict[str, Any]:
        """获取时段分析摘要（供AI使用）"""
        return {
            "session_id": self.session_id,
            "title": self.title,
            "work_type": self.work_type.value,
            "planned_duration_minutes": self.planned_duration_minutes,
            "actual_duration_minutes": self.get_actual_duration_minutes(),
            "focus_score": self.metrics.focus_score,
            "efficiency_score": self.get_efficiency_score(),
            "distraction_count": len(self.distractions),
            "environment_score": self.environment.environment_score,
            "target_focus_level": self.target_focus_level.value,
            "actual_focus_level": self.actual_focus_level.value if self.actual_focus_level else None,
            "energy_change": (self.energy_level_end - self.energy_level_start) if self.energy_level_end else None,
            "completed": self.completed,
            "primary_task": self.primary_task,
            "tags": self.tags
        }


@dataclass
class ReflectionEntry:
    """深度工作反思记录"""
    
    reflection_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    date: datetime = field(default_factory=datetime.now)
    period_type: str = "daily"  # daily/weekly/monthly
    
    # 反思内容
    what_worked_well: List[str] = field(default_factory=list)
    what_could_improve: List[str] = field(default_factory=list)
    key_insights: List[str] = field(default_factory=list)
    next_actions: List[str] = field(default_factory=list)
    
    # 量化评估
    overall_satisfaction: int = 3  # 1-5 总体满意度
    focus_quality_rating: int = 3  # 1-5 专注质量评分
    productivity_rating: int = 3   # 1-5 生产力评分
    energy_management_rating: int = 3  # 1-5 精力管理评分
    
    # 关联数据
    related_sessions: List[str] = field(default_factory=list)  # 相关时段ID
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "reflection_id": self.reflection_id,
            "date": self.date.isoformat(),
            "period_type": self.period_type,
            "what_worked_well": self.what_worked_well,
            "what_could_improve": self.what_could_improve,
            "key_insights": self.key_insights,
            "next_actions": self.next_actions,
            "overall_satisfaction": self.overall_satisfaction,
            "focus_quality_rating": self.focus_quality_rating,
            "productivity_rating": self.productivity_rating,
            "energy_management_rating": self.energy_management_rating,
            "related_sessions": self.related_sessions
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReflectionEntry':
        """从字典创建反思记录对象"""
        return cls(
            reflection_id=data.get("reflection_id", str(uuid.uuid4())),
            date=datetime.fromisoformat(data["date"]),
            period_type=data.get("period_type", "daily"),
            what_worked_well=data.get("what_worked_well", []),
            what_could_improve=data.get("what_could_improve", []),
            key_insights=data.get("key_insights", []),
            next_actions=data.get("next_actions", []),
            overall_satisfaction=data.get("overall_satisfaction", 3),
            focus_quality_rating=data.get("focus_quality_rating", 3),
            productivity_rating=data.get("productivity_rating", 3),
            energy_management_rating=data.get("energy_management_rating", 3),
            related_sessions=data.get("related_sessions", [])
        )