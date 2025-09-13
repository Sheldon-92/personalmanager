"""Task and GTD data models."""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from pydantic import BaseModel, Field, validator


class TaskStatus(str, Enum):
    """任务状态枚举"""
    INBOX = "inbox"              # 收件箱 - 待理清
    NEXT_ACTION = "next_action"  # 下一步行动
    PROJECT = "project"          # 项目
    WAITING_FOR = "waiting_for"  # 等待他人
    SOMEDAY_MAYBE = "someday_maybe"  # 将来/也许
    REFERENCE = "reference"      # 参考资料
    COMPLETED = "completed"      # 已完成
    DELETED = "deleted"          # 已删除


class TaskPriority(str, Enum):
    """任务优先级枚举"""
    HIGH = "high"       # 高优先级
    MEDIUM = "medium"   # 中优先级
    LOW = "low"         # 低优先级


class TaskContext(str, Enum):
    """任务情境枚举"""
    COMPUTER = "@电脑"      # 需要电脑
    PHONE = "@电话"        # 需要打电话
    ERRANDS = "@外出"      # 外出办事
    HOME = "@家"          # 在家
    OFFICE = "@办公室"     # 在办公室
    ONLINE = "@网络"       # 需要网络
    WAITING = "@等待"      # 等待他人
    READING = "@阅读"      # 阅读
    MEETING = "@会议"      # 会议
    FOCUS = "@专注"       # 需要专注


class EnergyLevel(str, Enum):
    """精力水平枚举"""
    HIGH = "high"       # 高精力
    MEDIUM = "medium"   # 中精力
    LOW = "low"         # 低精力


class Task(BaseModel):
    """任务数据模型"""
    
    # 基本信息
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="任务唯一ID")
    title: str = Field(..., description="任务标题")
    description: Optional[str] = Field(None, description="任务详细描述")
    
    # GTD分类
    status: TaskStatus = Field(TaskStatus.INBOX, description="任务状态")
    priority: TaskPriority = Field(TaskPriority.MEDIUM, description="优先级")
    context: Optional[TaskContext] = Field(None, description="执行情境")
    
    # 时间信息
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    due_date: Optional[datetime] = Field(None, description="截止日期")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    
    # 估算信息
    estimated_duration: Optional[int] = Field(None, description="预估时长(分钟)")
    energy_required: Optional[EnergyLevel] = Field(None, description="所需精力水平")
    
    # 关联信息
    project_id: Optional[str] = Field(None, description="关联项目ID")
    project_name: Optional[str] = Field(None, description="关联项目名称")
    parent_task_id: Optional[str] = Field(None, description="父任务ID")
    waiting_for: Optional[str] = Field(None, description="等待的人或事")
    
    # 捕获上下文
    capture_source: Optional[str] = Field(None, description="捕获来源")
    capture_location: Optional[str] = Field(None, description="捕获时的工作目录")
    capture_device: Optional[str] = Field(None, description="捕获设备")
    
    # 外部集成
    source: Optional[str] = Field(None, description="数据来源系统")
    source_id: Optional[str] = Field(None, description="外部系统中的ID")
    
    # 标签和分类
    tags: List[str] = Field(default_factory=list, description="标签列表")
    categories: List[str] = Field(default_factory=list, description="分类列表")
    
    # 智能分类支持
    classification_confidence: Optional[float] = Field(None, description="分类置信度")
    suggested_context: Optional[TaskContext] = Field(None, description="建议情境")
    suggested_priority: Optional[TaskPriority] = Field(None, description="建议优先级")
    
    # 元数据
    notes: List[str] = Field(default_factory=list, description="备注列表")
    attachments: List[str] = Field(default_factory=list, description="附件路径")
    
    @validator('title')
    def validate_title(cls, v):
        """验证任务标题"""
        if not v or not v.strip():
            raise ValueError("任务标题不能为空")
        return v.strip()
    
    @validator('estimated_duration')
    def validate_duration(cls, v):
        """验证预估时长"""
        if v is not None and v <= 0:
            raise ValueError("预估时长必须大于0")
        return v
    
    def is_actionable(self) -> bool:
        """判断任务是否可执行"""
        return self.status in [
            TaskStatus.NEXT_ACTION,
            TaskStatus.PROJECT
        ]
    
    def is_waiting(self) -> bool:
        """判断任务是否在等待"""
        return self.status == TaskStatus.WAITING_FOR
    
    def is_completed(self) -> bool:
        """判断任务是否已完成"""
        return self.status == TaskStatus.COMPLETED
    
    def is_inbox(self) -> bool:
        """判断任务是否在收件箱"""
        return self.status == TaskStatus.INBOX
    
    def mark_completed(self) -> None:
        """标记任务为已完成"""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now()
        self.updated_at = datetime.now()
    
    def update_status(self, new_status: TaskStatus) -> None:
        """更新任务状态"""
        self.status = new_status
        self.updated_at = datetime.now()
        
        if new_status == TaskStatus.COMPLETED and not self.completed_at:
            self.completed_at = datetime.now()
    
    def add_note(self, note: str) -> None:
        """添加备注"""
        if note and note.strip():
            self.notes.append(f"{datetime.now().isoformat()}: {note.strip()}")
            self.updated_at = datetime.now()
    
    def add_tag(self, tag: str) -> None:
        """添加标签"""
        if tag and tag.strip() and tag not in self.tags:
            self.tags.append(tag.strip())
            self.updated_at = datetime.now()
    
    def get_context_emoji(self) -> str:
        """获取情境表情符号"""
        emoji_map = {
            TaskContext.COMPUTER: "💻",
            TaskContext.PHONE: "📞",
            TaskContext.ERRANDS: "🚗",
            TaskContext.HOME: "🏠",
            TaskContext.OFFICE: "🏢",
            TaskContext.ONLINE: "🌐",
            TaskContext.WAITING: "⏳",
            TaskContext.READING: "📚",
            TaskContext.MEETING: "🤝",
            TaskContext.FOCUS: "🎯"
        }
        return emoji_map.get(self.context, "📋")
    
    def get_priority_emoji(self) -> str:
        """获取优先级表情符号"""
        emoji_map = {
            TaskPriority.HIGH: "🔥",
            TaskPriority.MEDIUM: "📋",
            TaskPriority.LOW: "📝"
        }
        return emoji_map.get(self.priority, "📋")
    
    def get_energy_emoji(self) -> str:
        """获取精力水平表情符号"""
        emoji_map = {
            EnergyLevel.HIGH: "⚡",
            EnergyLevel.MEDIUM: "🔋",
            EnergyLevel.LOW: "🪫"
        }
        return emoji_map.get(self.energy_required, "🔋")


class TaskFilter(BaseModel):
    """任务过滤器"""
    
    status: Optional[List[TaskStatus]] = Field(None, description="状态过滤")
    context: Optional[List[TaskContext]] = Field(None, description="情境过滤")
    priority: Optional[List[TaskPriority]] = Field(None, description="优先级过滤")
    project_id: Optional[str] = Field(None, description="项目ID过滤")
    tags: Optional[List[str]] = Field(None, description="标签过滤")
    energy_level: Optional[List[EnergyLevel]] = Field(None, description="精力水平过滤")
    
    # 时间过滤
    created_after: Optional[datetime] = Field(None, description="创建时间后")
    created_before: Optional[datetime] = Field(None, description="创建时间前")
    due_after: Optional[datetime] = Field(None, description="截止时间后")
    due_before: Optional[datetime] = Field(None, description="截止时间前")
    
    # 搜索
    search_text: Optional[str] = Field(None, description="搜索文本")
    
    def matches(self, task: Task) -> bool:
        """检查任务是否匹配过滤条件"""
        
        # 状态过滤
        if self.status and task.status not in self.status:
            return False
        
        # 情境过滤
        if self.context and task.context not in self.context:
            return False
        
        # 优先级过滤
        if self.priority and task.priority not in self.priority:
            return False
        
        # 项目过滤
        if self.project_id and task.project_id != self.project_id:
            return False
        
        # 标签过滤
        if self.tags and not any(tag in task.tags for tag in self.tags):
            return False
        
        # 精力水平过滤
        if self.energy_level and task.energy_required not in self.energy_level:
            return False
        
        # 时间过滤
        if self.created_after and task.created_at < self.created_after:
            return False
        if self.created_before and task.created_at > self.created_before:
            return False
        if self.due_after and (not task.due_date or task.due_date < self.due_after):
            return False
        if self.due_before and (not task.due_date or task.due_date > self.due_before):
            return False
        
        # 搜索文本过滤
        if self.search_text:
            search_lower = self.search_text.lower()
            if not any([
                search_lower in task.title.lower(),
                task.description and search_lower in task.description.lower(),
                any(search_lower in tag.lower() for tag in task.tags),
                any(search_lower in note.lower() for note in task.notes)
            ]):
                return False
        
        return True


class GTDWorkflow(BaseModel):
    """GTD工作流程状态"""
    
    inbox_count: int = Field(0, description="收件箱任务数")
    next_actions_count: int = Field(0, description="下一步行动数")
    projects_count: int = Field(0, description="项目数")
    waiting_for_count: int = Field(0, description="等待任务数")
    someday_maybe_count: int = Field(0, description="将来/也许任务数")
    
    last_review_date: Optional[datetime] = Field(None, description="最后回顾时间")
    last_capture_date: Optional[datetime] = Field(None, description="最后捕获时间")
    
    def needs_review(self) -> bool:
        """判断是否需要回顾"""
        if not self.last_review_date:
            return True
        
        days_since_review = (datetime.now() - self.last_review_date).days
        return days_since_review >= 7  # 一周回顾一次
    
    def inbox_overflow(self) -> bool:
        """判断收件箱是否溢出"""
        return self.inbox_count > 20  # 超过20个任务提醒理清