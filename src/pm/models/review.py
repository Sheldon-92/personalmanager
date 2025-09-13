"""回顾与反思数据模型 - Sprint 16核心功能

基于个人效能管理理论的回顾与反思模型
设计为AI可调用的工具函数支持，帮助用户实现持续自我提升
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from enum import Enum
from typing import List, Dict, Optional, Any, Union


class ReviewType(Enum):
    """回顾类型"""
    WEEKLY = "weekly"                 # 每周回顾
    PROJECT = "project"               # 项目复盘
    DECISION = "decision"             # 决策回顾
    QUARTERLY = "quarterly"           # 季度回顾
    ANNUAL = "annual"                 # 年度回顾


class ReviewPriority(Enum):
    """回顾优先级"""
    HIGH = "high"                     # 高优先级
    MEDIUM = "medium"                 # 中等优先级
    LOW = "low"                       # 低优先级


class DecisionOutcome(Enum):
    """决策结果评价"""
    EXCELLENT = "excellent"           # 优秀决策
    GOOD = "good"                     # 良好决策
    NEUTRAL = "neutral"               # 中性结果
    POOR = "poor"                     # 决策不佳
    UNKNOWN = "unknown"               # 结果未知


class GrowthArea(Enum):
    """成长领域分类"""
    TECHNICAL_SKILLS = "technical_skills"         # 技术技能
    LEADERSHIP = "leadership"                     # 领导力
    COMMUNICATION = "communication"               # 沟通能力
    TIME_MANAGEMENT = "time_management"           # 时间管理
    DECISION_MAKING = "decision_making"           # 决策能力
    PROBLEM_SOLVING = "problem_solving"           # 问题解决
    EMOTIONAL_INTELLIGENCE = "emotional_intelligence"  # 情商
    CREATIVITY = "creativity"                     # 创造力
    OTHER = "other"                               # 其他


@dataclass
class ActionItem:
    """行动项记录"""
    
    item_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    priority: ReviewPriority = ReviewPriority.MEDIUM
    due_date: Optional[date] = None
    assigned_to: Optional[str] = None  # 可以是自己或团队成员
    status: str = "pending"  # pending/in_progress/completed/cancelled
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "item_id": self.item_id,
            "description": self.description,
            "priority": self.priority.value,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "assigned_to": self.assigned_to,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ActionItem':
        """从字典创建对象"""
        return cls(
            item_id=data.get("item_id", str(uuid.uuid4())),
            description=data["description"],
            priority=ReviewPriority(data.get("priority", "medium")),
            due_date=date.fromisoformat(data["due_date"]) if data.get("due_date") else None,
            assigned_to=data.get("assigned_to"),
            status=data.get("status", "pending"),
            created_at=datetime.fromisoformat(data["created_at"]),
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None
        )


@dataclass
class GrowthInsight:
    """成长洞察记录"""
    
    insight_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    growth_area: GrowthArea = GrowthArea.OTHER
    key_learning: str = ""
    source_review_id: Optional[str] = None  # 来源回顾的ID
    confidence_level: int = 3  # 1-5，对洞察的信心程度
    actionable_steps: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "insight_id": self.insight_id,
            "title": self.title,
            "description": self.description,
            "growth_area": self.growth_area.value,
            "key_learning": self.key_learning,
            "source_review_id": self.source_review_id,
            "confidence_level": self.confidence_level,
            "actionable_steps": self.actionable_steps,
            "created_at": self.created_at.isoformat(),
            "tags": self.tags
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GrowthInsight':
        """从字典创建对象"""
        return cls(
            insight_id=data.get("insight_id", str(uuid.uuid4())),
            title=data["title"],
            description=data["description"],
            growth_area=GrowthArea(data.get("growth_area", "other")),
            key_learning=data["key_learning"],
            source_review_id=data.get("source_review_id"),
            confidence_level=data.get("confidence_level", 3),
            actionable_steps=data.get("actionable_steps", []),
            created_at=datetime.fromisoformat(data["created_at"]),
            tags=data.get("tags", [])
        )


@dataclass
class ReviewEntry:
    """回顾条目基类"""
    
    # 基本信息
    review_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    review_type: ReviewType = ReviewType.WEEKLY
    title: str = ""
    description: Optional[str] = None
    
    # 时间信息
    review_period_start: date = field(default_factory=date.today)
    review_period_end: date = field(default_factory=date.today)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # 回顾内容
    achievements: List[str] = field(default_factory=list)          # 成就和完成的事项
    challenges: List[str] = field(default_factory=list)           # 遇到的挑战和困难
    lessons_learned: List[str] = field(default_factory=list)      # 学到的经验教训
    what_went_well: List[str] = field(default_factory=list)       # 进展顺利的方面
    what_could_improve: List[str] = field(default_factory=list)   # 可以改进的方面
    
    # 行动项和洞察
    action_items: List[ActionItem] = field(default_factory=list)   # 行动项
    growth_insights: List[GrowthInsight] = field(default_factory=list)  # 成长洞察
    
    # 评分和标签
    overall_satisfaction: int = 3  # 1-5，总体满意度
    productivity_rating: int = 3   # 1-5，生产力评分
    learning_rating: int = 3       # 1-5，学习成长评分
    tags: List[str] = field(default_factory=list)
    
    # 元数据
    priority: ReviewPriority = ReviewPriority.MEDIUM
    is_completed: bool = False
    
    def __post_init__(self):
        """初始化后处理"""
        if not self.title:
            self.title = f"{self.review_type.value.title()}回顾 - {self.review_period_start}"
    
    def add_action_item(self, description: str, priority: ReviewPriority = ReviewPriority.MEDIUM,
                       due_date: Optional[date] = None) -> ActionItem:
        """添加行动项"""
        action = ActionItem(
            description=description,
            priority=priority,
            due_date=due_date
        )
        self.action_items.append(action)
        self.updated_at = datetime.now()
        return action
    
    def add_growth_insight(self, title: str, description: str, growth_area: GrowthArea = GrowthArea.OTHER,
                          key_learning: str = "", confidence_level: int = 3) -> GrowthInsight:
        """添加成长洞察"""
        insight = GrowthInsight(
            title=title,
            description=description,
            growth_area=growth_area,
            key_learning=key_learning,
            source_review_id=self.review_id,
            confidence_level=confidence_level
        )
        self.growth_insights.append(insight)
        self.updated_at = datetime.now()
        return insight
    
    def complete_review(self):
        """完成回顾"""
        self.is_completed = True
        self.updated_at = datetime.now()
    
    def get_action_items_summary(self) -> Dict[str, int]:
        """获取行动项摘要"""
        status_counts = {"pending": 0, "in_progress": 0, "completed": 0, "cancelled": 0}
        for item in self.action_items:
            status_counts[item.status] = status_counts.get(item.status, 0) + 1
        return status_counts
    
    def get_duration_days(self) -> int:
        """获取回顾覆盖的天数"""
        return (self.review_period_end - self.review_period_start).days + 1
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式（用于存储）"""
        return {
            "review_id": self.review_id,
            "review_type": self.review_type.value,
            "title": self.title,
            "description": self.description,
            "review_period_start": self.review_period_start.isoformat(),
            "review_period_end": self.review_period_end.isoformat(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "achievements": self.achievements,
            "challenges": self.challenges,
            "lessons_learned": self.lessons_learned,
            "what_went_well": self.what_went_well,
            "what_could_improve": self.what_could_improve,
            "action_items": [item.to_dict() for item in self.action_items],
            "growth_insights": [insight.to_dict() for insight in self.growth_insights],
            "overall_satisfaction": self.overall_satisfaction,
            "productivity_rating": self.productivity_rating,
            "learning_rating": self.learning_rating,
            "tags": self.tags,
            "priority": self.priority.value,
            "is_completed": self.is_completed
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReviewEntry':
        """从字典创建回顾条目对象"""
        review = cls(
            review_id=data["review_id"],
            review_type=ReviewType(data["review_type"]),
            title=data["title"],
            description=data.get("description"),
            review_period_start=date.fromisoformat(data["review_period_start"]),
            review_period_end=date.fromisoformat(data["review_period_end"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            achievements=data.get("achievements", []),
            challenges=data.get("challenges", []),
            lessons_learned=data.get("lessons_learned", []),
            what_went_well=data.get("what_went_well", []),
            what_could_improve=data.get("what_could_improve", []),
            overall_satisfaction=data.get("overall_satisfaction", 3),
            productivity_rating=data.get("productivity_rating", 3),
            learning_rating=data.get("learning_rating", 3),
            tags=data.get("tags", []),
            priority=ReviewPriority(data.get("priority", "medium")),
            is_completed=data.get("is_completed", False)
        )
        
        # 加载行动项
        review.action_items = [ActionItem.from_dict(item) for item in data.get("action_items", [])]
        
        # 加载成长洞察
        review.growth_insights = [GrowthInsight.from_dict(insight) for insight in data.get("growth_insights", [])]
        
        return review


@dataclass
class WeeklyReview(ReviewEntry):
    """每周回顾特化模型"""
    
    # 每周回顾特有字段
    week_goals_achieved: List[str] = field(default_factory=list)   # 完成的周目标
    week_goals_missed: List[str] = field(default_factory=list)     # 未完成的周目标
    next_week_goals: List[str] = field(default_factory=list)       # 下周目标
    time_allocation: Dict[str, float] = field(default_factory=dict)  # 时间分配（小时）
    energy_patterns: Dict[str, int] = field(default_factory=dict)    # 精力模式记录
    
    # 具体领域评分
    work_performance: int = 3      # 工作表现 1-5
    personal_development: int = 3  # 个人发展 1-5
    health_wellness: int = 3       # 健康状况 1-5
    relationships: int = 3         # 人际关系 1-5
    
    def __post_init__(self):
        """初始化处理"""
        self.review_type = ReviewType.WEEKLY
        super().__post_init__()
        if not self.title or self.title.startswith("weekly"):
            week_start = self.review_period_start
            self.title = f"每周回顾 - {week_start.strftime('%Y年%m月第%U周')}"
    
    def calculate_weekly_score(self) -> float:
        """计算每周综合评分"""
        scores = [
            self.overall_satisfaction,
            self.productivity_rating,
            self.learning_rating,
            self.work_performance,
            self.personal_development,
            self.health_wellness,
            self.relationships
        ]
        return sum(scores) / len(scores)
    
    def get_goal_completion_rate(self) -> float:
        """计算目标完成率"""
        total_goals = len(self.week_goals_achieved) + len(self.week_goals_missed)
        if total_goals == 0:
            return 0.0
        return len(self.week_goals_achieved) / total_goals * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """扩展基类字典转换"""
        base_dict = super().to_dict()
        base_dict.update({
            "week_goals_achieved": self.week_goals_achieved,
            "week_goals_missed": self.week_goals_missed,
            "next_week_goals": self.next_week_goals,
            "time_allocation": self.time_allocation,
            "energy_patterns": self.energy_patterns,
            "work_performance": self.work_performance,
            "personal_development": self.personal_development,
            "health_wellness": self.health_wellness,
            "relationships": self.relationships
        })
        return base_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WeeklyReview':
        """从字典创建每周回顾对象"""
        # 先创建基础回顾对象
        base_review = ReviewEntry.from_dict(data)
        
        # 创建每周回顾对象
        weekly_review = cls(
            review_id=base_review.review_id,
            review_type=ReviewType.WEEKLY,
            title=base_review.title,
            description=base_review.description,
            review_period_start=base_review.review_period_start,
            review_period_end=base_review.review_period_end,
            created_at=base_review.created_at,
            updated_at=base_review.updated_at,
            achievements=base_review.achievements,
            challenges=base_review.challenges,
            lessons_learned=base_review.lessons_learned,
            what_went_well=base_review.what_went_well,
            what_could_improve=base_review.what_could_improve,
            action_items=base_review.action_items,
            growth_insights=base_review.growth_insights,
            overall_satisfaction=base_review.overall_satisfaction,
            productivity_rating=base_review.productivity_rating,
            learning_rating=base_review.learning_rating,
            tags=base_review.tags,
            priority=base_review.priority,
            is_completed=base_review.is_completed,
            week_goals_achieved=data.get("week_goals_achieved", []),
            week_goals_missed=data.get("week_goals_missed", []),
            next_week_goals=data.get("next_week_goals", []),
            time_allocation=data.get("time_allocation", {}),
            energy_patterns=data.get("energy_patterns", {}),
            work_performance=data.get("work_performance", 3),
            personal_development=data.get("personal_development", 3),
            health_wellness=data.get("health_wellness", 3),
            relationships=data.get("relationships", 3)
        )
        
        return weekly_review


@dataclass
class ProjectRetrospective(ReviewEntry):
    """项目复盘特化模型"""
    
    # 项目复盘特有字段
    project_name: str = ""
    project_id: Optional[str] = None
    project_start_date: Optional[date] = None
    project_end_date: Optional[date] = None
    original_timeline: Optional[int] = None  # 原计划天数
    actual_timeline: Optional[int] = None    # 实际用时天数
    
    # 项目成果评估
    objectives_met: List[str] = field(default_factory=list)        # 达成的目标
    objectives_missed: List[str] = field(default_factory=list)     # 未达成的目标
    deliverables_quality: int = 3    # 交付物质量 1-5
    stakeholder_satisfaction: int = 3  # 利益相关者满意度 1-5
    
    # 团队和协作
    team_performance: int = 3        # 团队表现 1-5
    communication_effectiveness: int = 3  # 沟通有效性 1-5
    collaboration_quality: int = 3   # 协作质量 1-5
    
    # 过程分析
    process_improvements: List[str] = field(default_factory=list)  # 过程改进建议
    tool_effectiveness: Dict[str, int] = field(default_factory=dict)  # 工具有效性评分
    risk_management_effectiveness: int = 3  # 风险管理有效性 1-5
    
    def __post_init__(self):
        """初始化处理"""
        self.review_type = ReviewType.PROJECT
        super().__post_init__()
        if not self.title or self.title.startswith("project"):
            self.title = f"项目复盘 - {self.project_name}" if self.project_name else "项目复盘"
    
    def calculate_timeline_variance(self) -> Optional[float]:
        """计算时间偏差百分比"""
        if self.original_timeline and self.actual_timeline:
            return ((self.actual_timeline - self.original_timeline) / self.original_timeline) * 100
        return None
    
    def calculate_objective_completion_rate(self) -> float:
        """计算目标完成率"""
        total_objectives = len(self.objectives_met) + len(self.objectives_missed)
        if total_objectives == 0:
            return 0.0
        return len(self.objectives_met) / total_objectives * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """扩展基类字典转换"""
        base_dict = super().to_dict()
        base_dict.update({
            "project_name": self.project_name,
            "project_id": self.project_id,
            "project_start_date": self.project_start_date.isoformat() if self.project_start_date else None,
            "project_end_date": self.project_end_date.isoformat() if self.project_end_date else None,
            "original_timeline": self.original_timeline,
            "actual_timeline": self.actual_timeline,
            "objectives_met": self.objectives_met,
            "objectives_missed": self.objectives_missed,
            "deliverables_quality": self.deliverables_quality,
            "stakeholder_satisfaction": self.stakeholder_satisfaction,
            "team_performance": self.team_performance,
            "communication_effectiveness": self.communication_effectiveness,
            "collaboration_quality": self.collaboration_quality,
            "process_improvements": self.process_improvements,
            "tool_effectiveness": self.tool_effectiveness,
            "risk_management_effectiveness": self.risk_management_effectiveness
        })
        return base_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectRetrospective':
        """从字典创建项目复盘对象"""
        # 先创建基础回顾对象
        base_review = ReviewEntry.from_dict(data)
        
        # 创建项目复盘对象
        project_retro = cls(
            review_id=base_review.review_id,
            review_type=ReviewType.PROJECT,
            title=base_review.title,
            description=base_review.description,
            review_period_start=base_review.review_period_start,
            review_period_end=base_review.review_period_end,
            created_at=base_review.created_at,
            updated_at=base_review.updated_at,
            achievements=base_review.achievements,
            challenges=base_review.challenges,
            lessons_learned=base_review.lessons_learned,
            what_went_well=base_review.what_went_well,
            what_could_improve=base_review.what_could_improve,
            action_items=base_review.action_items,
            growth_insights=base_review.growth_insights,
            overall_satisfaction=base_review.overall_satisfaction,
            productivity_rating=base_review.productivity_rating,
            learning_rating=base_review.learning_rating,
            tags=base_review.tags,
            priority=base_review.priority,
            is_completed=base_review.is_completed,
            project_name=data.get("project_name", ""),
            project_id=data.get("project_id"),
            project_start_date=date.fromisoformat(data["project_start_date"]) if data.get("project_start_date") else None,
            project_end_date=date.fromisoformat(data["project_end_date"]) if data.get("project_end_date") else None,
            original_timeline=data.get("original_timeline"),
            actual_timeline=data.get("actual_timeline"),
            objectives_met=data.get("objectives_met", []),
            objectives_missed=data.get("objectives_missed", []),
            deliverables_quality=data.get("deliverables_quality", 3),
            stakeholder_satisfaction=data.get("stakeholder_satisfaction", 3),
            team_performance=data.get("team_performance", 3),
            communication_effectiveness=data.get("communication_effectiveness", 3),
            collaboration_quality=data.get("collaboration_quality", 3),
            process_improvements=data.get("process_improvements", []),
            tool_effectiveness=data.get("tool_effectiveness", {}),
            risk_management_effectiveness=data.get("risk_management_effectiveness", 3)
        )
        
        return project_retro


@dataclass
class DecisionReview:
    """决策质量跟踪模型"""
    
    decision_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    
    # 决策信息
    decision_date: date = field(default_factory=date.today)
    decision_maker: str = ""  # 决策者
    decision_context: str = ""  # 决策背景
    options_considered: List[str] = field(default_factory=list)  # 考虑的选项
    chosen_option: str = ""  # 选择的方案
    decision_rationale: str = ""  # 决策理由
    
    # 决策过程评估
    information_quality: int = 3   # 信息质量 1-5
    analysis_depth: int = 3        # 分析深度 1-5
    stakeholder_involvement: int = 3  # 利益相关者参与度 1-5
    time_pressure: int = 3         # 时间压力 1-5
    decision_confidence: int = 3   # 决策信心 1-5
    
    # 结果跟踪
    expected_outcomes: List[str] = field(default_factory=list)     # 预期结果
    actual_outcomes: List[str] = field(default_factory=list)       # 实际结果
    outcome_evaluation_date: Optional[date] = None                # 结果评估日期
    outcome_rating: Optional[DecisionOutcome] = None              # 结果评价
    
    # 学习和改进
    key_learnings: List[str] = field(default_factory=list)        # 关键学习
    improvement_areas: List[str] = field(default_factory=list)    # 改进领域
    future_considerations: List[str] = field(default_factory=list)  # 未来考虑事项
    
    # 元数据
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)
    related_project_id: Optional[str] = None
    
    def evaluate_outcome(self, actual_outcomes: List[str], outcome_rating: DecisionOutcome,
                        key_learnings: List[str] = None):
        """评估决策结果"""
        self.actual_outcomes = actual_outcomes
        self.outcome_rating = outcome_rating
        self.outcome_evaluation_date = date.today()
        if key_learnings:
            self.key_learnings.extend(key_learnings)
        self.updated_at = datetime.now()
    
    def calculate_decision_quality_score(self) -> float:
        """计算决策质量评分"""
        process_score = (
            self.information_quality + 
            self.analysis_depth + 
            self.stakeholder_involvement + 
            self.decision_confidence
        ) / 4
        
        # 如果有结果评价，结合结果评分
        if self.outcome_rating:
            outcome_scores = {
                DecisionOutcome.EXCELLENT: 5,
                DecisionOutcome.GOOD: 4,
                DecisionOutcome.NEUTRAL: 3,
                DecisionOutcome.POOR: 2,
                DecisionOutcome.UNKNOWN: 3
            }
            outcome_score = outcome_scores[self.outcome_rating]
            return (process_score * 0.6 + outcome_score * 0.4)
        
        return process_score
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "decision_id": self.decision_id,
            "title": self.title,
            "description": self.description,
            "decision_date": self.decision_date.isoformat(),
            "decision_maker": self.decision_maker,
            "decision_context": self.decision_context,
            "options_considered": self.options_considered,
            "chosen_option": self.chosen_option,
            "decision_rationale": self.decision_rationale,
            "information_quality": self.information_quality,
            "analysis_depth": self.analysis_depth,
            "stakeholder_involvement": self.stakeholder_involvement,
            "time_pressure": self.time_pressure,
            "decision_confidence": self.decision_confidence,
            "expected_outcomes": self.expected_outcomes,
            "actual_outcomes": self.actual_outcomes,
            "outcome_evaluation_date": self.outcome_evaluation_date.isoformat() if self.outcome_evaluation_date else None,
            "outcome_rating": self.outcome_rating.value if self.outcome_rating else None,
            "key_learnings": self.key_learnings,
            "improvement_areas": self.improvement_areas,
            "future_considerations": self.future_considerations,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "tags": self.tags,
            "related_project_id": self.related_project_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DecisionReview':
        """从字典创建决策回顾对象"""
        return cls(
            decision_id=data.get("decision_id", str(uuid.uuid4())),
            title=data["title"],
            description=data["description"],
            decision_date=date.fromisoformat(data["decision_date"]),
            decision_maker=data["decision_maker"],
            decision_context=data["decision_context"],
            options_considered=data.get("options_considered", []),
            chosen_option=data["chosen_option"],
            decision_rationale=data["decision_rationale"],
            information_quality=data.get("information_quality", 3),
            analysis_depth=data.get("analysis_depth", 3),
            stakeholder_involvement=data.get("stakeholder_involvement", 3),
            time_pressure=data.get("time_pressure", 3),
            decision_confidence=data.get("decision_confidence", 3),
            expected_outcomes=data.get("expected_outcomes", []),
            actual_outcomes=data.get("actual_outcomes", []),
            outcome_evaluation_date=date.fromisoformat(data["outcome_evaluation_date"]) if data.get("outcome_evaluation_date") else None,
            outcome_rating=DecisionOutcome(data["outcome_rating"]) if data.get("outcome_rating") else None,
            key_learnings=data.get("key_learnings", []),
            improvement_areas=data.get("improvement_areas", []),
            future_considerations=data.get("future_considerations", []),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            tags=data.get("tags", []),
            related_project_id=data.get("related_project_id")
        )