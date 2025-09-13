"""习惯管理数据模型 - Sprint 13核心功能

基于《原子习惯》理论的习惯跟踪和管理模型
设计为AI可调用的工具函数支持
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from enum import Enum
from typing import List, Dict, Optional, Any
from pathlib import Path
import json


class HabitFrequency(Enum):
    """习惯频率类型"""
    DAILY = "daily"           # 每日
    WEEKLY = "weekly"         # 每周
    MONTHLY = "monthly"       # 每月
    CUSTOM = "custom"         # 自定义频率


class HabitDifficulty(Enum):
    """习惯难度级别（基于原子习惯理论）"""
    TINY = "tiny"             # 微习惯（2分钟法则）
    EASY = "easy"             # 简单习惯
    MEDIUM = "medium"         # 中等习惯
    HARD = "hard"             # 困难习惯


class HabitCategory(Enum):
    """习惯分类"""
    HEALTH = "health"         # 健康
    LEARNING = "learning"     # 学习成长
    PRODUCTIVITY = "productivity"  # 效率提升
    MINDFULNESS = "mindfulness"    # 正念冥想
    SOCIAL = "social"         # 社交关系
    CREATIVE = "creative"     # 创造性活动
    OTHER = "other"           # 其他


@dataclass
class HabitRecord:
    """习惯执行记录"""
    
    record_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    habit_id: str = ""
    date: date = field(default_factory=date.today)
    completed: bool = False
    notes: Optional[str] = None
    completion_time: Optional[datetime] = None
    quality_score: Optional[int] = None  # 1-5分，执行质量评分
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "record_id": self.record_id,
            "habit_id": self.habit_id,
            "date": self.date.isoformat(),
            "completed": self.completed,
            "notes": self.notes,
            "completion_time": self.completion_time.isoformat() if self.completion_time else None,
            "quality_score": self.quality_score,
            "created_at": self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HabitRecord':
        """从字典创建对象"""
        return cls(
            record_id=data.get("record_id", str(uuid.uuid4())),
            habit_id=data["habit_id"],
            date=date.fromisoformat(data["date"]),
            completed=data["completed"],
            notes=data.get("notes"),
            completion_time=datetime.fromisoformat(data["completion_time"]) if data.get("completion_time") else None,
            quality_score=data.get("quality_score"),
            created_at=datetime.fromisoformat(data["created_at"])
        )


@dataclass  
class HabitStreak:
    """习惯连续打卡统计"""
    
    current_streak: int = 0      # 当前连续天数
    longest_streak: int = 0      # 历史最长连续天数
    total_completions: int = 0   # 总完成次数
    success_rate: float = 0.0    # 成功率（0-100）
    last_completion: Optional[date] = None
    
    def update_from_records(self, records: List[HabitRecord], habit_created: date):
        """根据记录更新统计数据"""
        if not records:
            return
            
        # 按日期排序
        sorted_records = sorted(records, key=lambda x: x.date)
        
        # 计算总完成次数和成功率
        completed_records = [r for r in sorted_records if r.completed]
        self.total_completions = len(completed_records)
        
        # 计算应该执行的总天数
        total_days = (date.today() - habit_created).days + 1
        self.success_rate = (self.total_completions / total_days * 100) if total_days > 0 else 0.0
        
        if completed_records:
            self.last_completion = max(r.date for r in completed_records)
            
            # 计算当前和最长连续打卡
            self._calculate_streaks(completed_records)
    
    def _calculate_streaks(self, completed_records: List[HabitRecord]):
        """计算连续打卡天数"""
        if not completed_records:
            return
            
        # 按日期排序的完成记录
        dates = sorted([r.date for r in completed_records])
        
        current_streak = 0
        longest_streak = 0
        temp_streak = 1
        
        # 检查是否包含今天或昨天（当前连续）
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        if today in dates:
            current_streak = 1
            # 从今天往前计算
            check_date = today - timedelta(days=1)
            while check_date in dates:
                current_streak += 1
                check_date -= timedelta(days=1)
        elif yesterday in dates:
            current_streak = 1
            # 从昨天往前计算
            check_date = yesterday - timedelta(days=1)
            while check_date in dates:
                current_streak += 1
                check_date -= timedelta(days=1)
        
        # 计算历史最长连续
        for i in range(1, len(dates)):
            if dates[i] - dates[i-1] == timedelta(days=1):
                temp_streak += 1
            else:
                longest_streak = max(longest_streak, temp_streak)
                temp_streak = 1
        
        longest_streak = max(longest_streak, temp_streak)
        self.longest_streak = max(longest_streak, current_streak)
        self.current_streak = current_streak


@dataclass
class Habit:
    """习惯定义和跟踪主模型"""
    
    # 基本信息
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: Optional[str] = None
    category: HabitCategory = HabitCategory.OTHER
    
    # 执行设置
    frequency: HabitFrequency = HabitFrequency.DAILY
    difficulty: HabitDifficulty = HabitDifficulty.EASY
    target_duration: Optional[int] = None  # 目标时长（分钟）
    reminder_time: Optional[str] = None    # 提醒时间 "HH:MM"
    
    # 原子习惯要素
    cue: Optional[str] = None              # 提示/触发条件
    routine: Optional[str] = None          # 惯常行为
    reward: Optional[str] = None           # 奖励
    
    # 元数据
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    active: bool = True
    
    # 跟踪数据（运行时计算）
    records: List[HabitRecord] = field(default_factory=list)
    streak: HabitStreak = field(default_factory=HabitStreak)
    
    def __post_init__(self):
        """初始化后处理"""
        if not self.name:
            raise ValueError("习惯名称不能为空")
    
    def add_record(self, completed: bool, notes: Optional[str] = None, 
                  quality_score: Optional[int] = None, record_date: Optional[date] = None) -> HabitRecord:
        """添加执行记录"""
        record_date = record_date or date.today()
        
        # 检查是否已有当天记录
        existing = self.get_record_for_date(record_date)
        if existing:
            existing.completed = completed
            existing.notes = notes
            existing.quality_score = quality_score
            existing.completion_time = datetime.now() if completed else None
            record = existing
        else:
            record = HabitRecord(
                habit_id=self.id,
                date=record_date,
                completed=completed,
                notes=notes,
                quality_score=quality_score,
                completion_time=datetime.now() if completed else None
            )
            self.records.append(record)
        
        # 更新统计
        self.streak.update_from_records(self.records, self.created_at.date())
        self.updated_at = datetime.now()
        
        return record
    
    def get_record_for_date(self, target_date: date) -> Optional[HabitRecord]:
        """获取指定日期的记录"""
        return next((r for r in self.records if r.date == target_date), None)
    
    def is_due_today(self) -> bool:
        """检查今天是否应该执行"""
        if not self.active:
            return False
            
        today = date.today()
        
        if self.frequency == HabitFrequency.DAILY:
            return True
        elif self.frequency == HabitFrequency.WEEKLY:
            # 简单实现：每周一执行
            return today.weekday() == 0
        elif self.frequency == HabitFrequency.MONTHLY:
            # 每月第一天执行
            return today.day == 1
            
        return False
    
    def is_completed_today(self) -> bool:
        """检查今天是否已完成"""
        today_record = self.get_record_for_date(date.today())
        return today_record and today_record.completed
    
    def get_completion_rate(self, days: int = 30) -> float:
        """获取指定天数内的完成率"""
        if not self.active or days <= 0:
            return 0.0
            
        start_date = date.today() - timedelta(days=days-1)
        end_date = date.today()
        
        total_days = 0
        completed_days = 0
        
        current_date = start_date
        while current_date <= end_date:
            if self.frequency == HabitFrequency.DAILY:
                total_days += 1
                record = self.get_record_for_date(current_date)
                if record and record.completed:
                    completed_days += 1
            current_date += timedelta(days=1)
        
        return (completed_days / total_days * 100) if total_days > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式（用于存储）"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "frequency": self.frequency.value,
            "difficulty": self.difficulty.value,
            "target_duration": self.target_duration,
            "reminder_time": self.reminder_time,
            "cue": self.cue,
            "routine": self.routine,
            "reward": self.reward,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "active": self.active,
            "records": [r.to_dict() for r in self.records]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Habit':
        """从字典创建习惯对象"""
        habit = cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description"),
            category=HabitCategory(data["category"]),
            frequency=HabitFrequency(data["frequency"]),
            difficulty=HabitDifficulty(data["difficulty"]),
            target_duration=data.get("target_duration"),
            reminder_time=data.get("reminder_time"),
            cue=data.get("cue"),
            routine=data.get("routine"),
            reward=data.get("reward"),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            active=data.get("active", True)
        )
        
        # 加载记录
        habit.records = [HabitRecord.from_dict(r) for r in data.get("records", [])]
        
        # 更新统计
        habit.streak.update_from_records(habit.records, habit.created_at.date())
        
        return habit
    
    def get_analysis_summary(self) -> Dict[str, Any]:
        """获取习惯分析摘要（供AI使用）"""
        return {
            "name": self.name,
            "category": self.category.value,
            "difficulty": self.difficulty.value,
            "current_streak": self.streak.current_streak,
            "longest_streak": self.streak.longest_streak,
            "success_rate": round(self.streak.success_rate, 1),
            "total_completions": self.streak.total_completions,
            "completion_rate_7d": round(self.get_completion_rate(7), 1),
            "completion_rate_30d": round(self.get_completion_rate(30), 1),
            "is_due_today": self.is_due_today(),
            "completed_today": self.is_completed_today(),
            "active_days": (date.today() - self.created_at.date()).days + 1
        }