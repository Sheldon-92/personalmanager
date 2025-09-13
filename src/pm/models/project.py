"""Project data models and PROJECT_STATUS.md parser."""

import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from pydantic import BaseModel, Field, validator
import yaml


class ProjectHealth(str, Enum):
    """项目健康状态枚举"""
    EXCELLENT = "excellent"    # 优秀 - 进展顺利
    GOOD = "good"             # 良好 - 正常进展
    WARNING = "warning"       # 警告 - 存在风险
    CRITICAL = "critical"     # 危急 - 严重问题
    UNKNOWN = "unknown"       # 未知 - 无法确定


class ProjectPriority(str, Enum):
    """项目优先级枚举"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ProjectStatus(BaseModel):
    """项目状态数据模型"""
    
    # 基本信息
    name: str = Field(..., description="项目名称")
    path: Path = Field(..., description="项目路径")
    
    # 状态信息
    progress: float = Field(0.0, ge=0.0, le=100.0, description="进度百分比")
    health: ProjectHealth = Field(ProjectHealth.UNKNOWN, description="健康状态")
    priority: ProjectPriority = Field(ProjectPriority.MEDIUM, description="优先级")
    
    # 时间信息
    last_updated: Optional[datetime] = Field(None, description="最后更新时间")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    deadline: Optional[datetime] = Field(None, description="截止日期")
    
    # 项目内容
    description: Optional[str] = Field(None, description="项目描述")
    current_phase: Optional[str] = Field(None, description="当前阶段")
    completed_work: List[str] = Field(default_factory=list, description="已完成工作")
    next_actions: List[str] = Field(default_factory=list, description="下一步行动")
    risks: List[str] = Field(default_factory=list, description="风险和问题")
    
    # 元数据
    team_members: List[str] = Field(default_factory=list, description="团队成员")
    tags: List[str] = Field(default_factory=list, description="标签")
    dependencies: List[str] = Field(default_factory=list, description="依赖项目")
    
    # 原始数据
    raw_content: Optional[str] = Field(None, description="原始PROJECT_STATUS.md内容")
    parse_errors: List[str] = Field(default_factory=list, description="解析错误")
    
    @validator('progress')
    def validate_progress(cls, v):
        """验证进度百分比"""
        return max(0.0, min(100.0, v))
    
    @validator('name')
    def validate_name(cls, v):
        """验证项目名称"""
        if not v or not v.strip():
            raise ValueError("项目名称不能为空")
        return v.strip()
    
    def is_healthy(self) -> bool:
        """判断项目是否健康"""
        return self.health in [ProjectHealth.EXCELLENT, ProjectHealth.GOOD]
    
    def is_at_risk(self) -> bool:
        """判断项目是否有风险"""
        return self.health in [ProjectHealth.WARNING, ProjectHealth.CRITICAL]
    
    def get_status_emoji(self) -> str:
        """获取状态表情符号"""
        emoji_map = {
            ProjectHealth.EXCELLENT: "🟢",
            ProjectHealth.GOOD: "🟡", 
            ProjectHealth.WARNING: "🟠",
            ProjectHealth.CRITICAL: "🔴",
            ProjectHealth.UNKNOWN: "⚪"
        }
        return emoji_map.get(self.health, "⚪")
    
    def get_priority_emoji(self) -> str:
        """获取优先级表情符号"""
        emoji_map = {
            ProjectPriority.HIGH: "🔥",
            ProjectPriority.MEDIUM: "📋", 
            ProjectPriority.LOW: "📝"
        }
        return emoji_map.get(self.priority, "📋")


class ProjectStatusParser:
    """PROJECT_STATUS.md文件解析器
    
    基于"以报告为中心"的方案，解析AI工具生成的PROJECT_STATUS.md文件
    """
    
    def __init__(self):
        self.section_patterns = {
            'progress': [
                # 修复：支持Markdown格式的进度解析，包括项目符号和粗体标记
                r'(?i)[\-\*]*\s*\*{0,2}progress\*{0,2}[:\s]*(\d+(?:\.\d+)?)\s*%?',
                r'(?i)[\-\*]*\s*\*{0,2}进度\*{0,2}[:\s]*(\d+(?:\.\d+)?)\s*%?',
                r'(?i)[\-\*]*\s*\*{0,2}completion\*{0,2}[:\s]*(\d+(?:\.\d+)?)\s*%?',
                r'(?i)[\-\*]*\s*\*{0,2}完成[度率]*\*{0,2}[:\s]*(\d+(?:\.\d+)?)\s*%?'
            ],
            'health': [
                # 修复：支持Markdown格式的健康度解析，并优化匹配精度
                r'(?i)[\-\*]*\s*\*{0,2}health\*{0,2}[:\s]*([a-zA-Z\u4e00-\u9fff\s]+?)(?:\s*\([^)]*\))?',
                r'(?i)[\-\*]*\s*\*{0,2}健康[度状态]*\*{0,2}[:\s]*([^(\n\r,]+)',
                r'(?i)[\-\*]*\s*\*{0,2}status\*{0,2}[:\s]*([a-zA-Z\u4e00-\u9fff]+)'
            ],
            'priority': [
                # 修复：支持Markdown格式的优先级解析，并优化匹配精度
                r'(?i)[\-\*]*\s*\*{0,2}priority\*{0,2}[:\s]*([a-zA-Z\u4e00-\u9fff]+)',
                r'(?i)[\-\*]*\s*\*{0,2}优先级\*{0,2}[:\s]*([^\n\r,()]+?)(?:\s*\([^)]*\))?',
                r'(?i)[\-\*]*\s*\*{0,2}importance\*{0,2}[:\s]*([a-zA-Z\u4e00-\u9fff]+)'
            ]
        }
    
    def parse_file(self, file_path: Path) -> ProjectStatus:
        """解析PROJECT_STATUS.md文件"""
        
        if not file_path.exists():
            raise FileNotFoundError(f"PROJECT_STATUS.md文件不存在: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            raise ValueError(f"读取文件失败: {e}")
        
        return self.parse_content(content, file_path)
    
    def parse_content(self, content: str, file_path: Optional[Path] = None) -> ProjectStatus:
        """解析PROJECT_STATUS.md内容"""
        
        project_name = self._extract_project_name(content, file_path)
        
        # 解析基本状态信息
        progress = self._extract_progress(content)
        health = self._extract_health(content)
        priority = self._extract_priority(content)
        
        # 解析时间信息
        last_updated = self._extract_last_updated(content)
        deadline = self._extract_deadline(content)
        
        # 解析项目内容
        description = self._extract_description(content)
        current_phase = self._extract_current_phase(content)
        completed_work = self._extract_completed_work(content)
        next_actions = self._extract_next_actions(content)
        risks = self._extract_risks(content)
        
        # 解析元数据
        team_members = self._extract_team_members(content)
        tags = self._extract_tags(content)
        dependencies = self._extract_dependencies(content)
        
        return ProjectStatus(
            name=project_name,
            path=file_path or Path("."),
            progress=progress,
            health=health,
            priority=priority,
            last_updated=last_updated,
            deadline=deadline,
            description=description,
            current_phase=current_phase,
            completed_work=completed_work,
            next_actions=next_actions,
            risks=risks,
            team_members=team_members,
            tags=tags,
            dependencies=dependencies,
            raw_content=content
        )
    
    def _extract_project_name(self, content: str, file_path: Optional[Path] = None) -> str:
        """提取项目名称"""
        
        # 优先从文件路径推断
        if file_path:
            project_dir = file_path.parent
            if project_dir.name not in ['.', '..']:
                return project_dir.name
        
        # 从标题提取
        title_patterns = [
            r'^#\s+(.+)$',
            r'(?i)^#*\s*project\s*[:\s]*(.+)$',
            r'(?i)^#*\s*项目\s*[:\s]*(.+)$'
        ]
        
        for pattern in title_patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            if matches:
                return matches[0].strip()
        
        # 默认名称
        return "Unknown Project"
    
    def _extract_progress(self, content: str) -> float:
        """提取进度百分比"""
        for pattern in self.section_patterns['progress']:
            matches = re.findall(pattern, content, re.MULTILINE | re.IGNORECASE)
            if matches:
                try:
                    return float(matches[0])
                except ValueError:
                    continue
        return 0.0
    
    def _extract_health(self, content: str) -> ProjectHealth:
        """提取健康状态"""
        
        health_mapping = {
            'excellent': ProjectHealth.EXCELLENT,
            'good': ProjectHealth.GOOD,
            'warning': ProjectHealth.WARNING,
            'critical': ProjectHealth.CRITICAL,
            'green': ProjectHealth.EXCELLENT,
            'yellow': ProjectHealth.WARNING,
            'red': ProjectHealth.CRITICAL,
            '优秀': ProjectHealth.EXCELLENT,
            '良好': ProjectHealth.GOOD,
            '正常': ProjectHealth.GOOD,
            '警告': ProjectHealth.WARNING,
            '危急': ProjectHealth.CRITICAL,
            '严重': ProjectHealth.CRITICAL
        }
        
        for pattern in self.section_patterns['health']:
            matches = re.findall(pattern, content, re.MULTILINE | re.IGNORECASE)
            if matches:
                health_str = matches[0].strip().lower()
                return health_mapping.get(health_str, ProjectHealth.UNKNOWN)
        
        return ProjectHealth.UNKNOWN
    
    def _extract_priority(self, content: str) -> ProjectPriority:
        """提取优先级"""
        
        priority_mapping = {
            'high': ProjectPriority.HIGH,
            'medium': ProjectPriority.MEDIUM,
            'low': ProjectPriority.LOW,
            'critical': ProjectPriority.HIGH,
            'urgent': ProjectPriority.HIGH,
            '高': ProjectPriority.HIGH,
            '中': ProjectPriority.MEDIUM,
            '低': ProjectPriority.LOW,
            '紧急': ProjectPriority.HIGH,
            '重要': ProjectPriority.HIGH
        }
        
        for pattern in self.section_patterns['priority']:
            matches = re.findall(pattern, content, re.MULTILINE | re.IGNORECASE)
            if matches:
                priority_str = matches[0].strip().lower()
                return priority_mapping.get(priority_str, ProjectPriority.MEDIUM)
        
        return ProjectPriority.MEDIUM
    
    def _extract_last_updated(self, content: str) -> Optional[datetime]:
        """提取最后更新时间"""
        
        date_patterns = [
            r'(?i)last\s+updated[:\s]*([0-9-]+)',
            r'(?i)updated[:\s]*([0-9-]+)',
            r'(?i)最后更新[:\s]*([0-9-]+)',
            r'(?i)更新时间[:\s]*([0-9-]+)'
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            if matches:
                try:
                    return datetime.fromisoformat(matches[0])
                except ValueError:
                    continue
        
        return None
    
    def _extract_deadline(self, content: str) -> Optional[datetime]:
        """提取截止日期"""
        
        deadline_patterns = [
            r'(?i)deadline[:\s]*([0-9-]+)',
            r'(?i)due\s+date[:\s]*([0-9-]+)',
            r'(?i)截止[日期]*[:\s]*([0-9-]+)',
            r'(?i)交付[日期]*[:\s]*([0-9-]+)'
        ]
        
        for pattern in deadline_patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            if matches:
                try:
                    return datetime.fromisoformat(matches[0])
                except ValueError:
                    continue
        
        return None
    
    def _extract_description(self, content: str) -> Optional[str]:
        """提取项目描述"""
        
        desc_patterns = [
            r'(?i)description[:\s]*([^\n]+)',
            r'(?i)项目描述[:\s]*([^\n]+)',
            r'(?i)概述[:\s]*([^\n]+)'
        ]
        
        for pattern in desc_patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            if matches:
                return matches[0].strip()
        
        return None
    
    def _extract_current_phase(self, content: str) -> Optional[str]:
        """提取当前阶段"""
        
        phase_patterns = [
            r'(?i)current\s+phase[:\s]*([^\n]+)',
            r'(?i)phase[:\s]*([^\n]+)',
            r'(?i)当前阶段[:\s]*([^\n]+)',
            r'(?i)阶段[:\s]*([^\n]+)'
        ]
        
        for pattern in phase_patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            if matches:
                return matches[0].strip()
        
        return None
    
    def _extract_list_items(self, content: str, section_patterns: List[str]) -> List[str]:
        """提取列表项目的通用方法"""
        
        items = []
        
        for pattern in section_patterns:
            # 查找段落开始
            section_match = re.search(pattern, content, re.MULTILINE | re.IGNORECASE)
            if section_match:
                # 从匹配位置开始查找列表项
                start_pos = section_match.end()
                remaining_content = content[start_pos:]
                
                # 查找下一个段落标题（## 标题格式）来限制提取范围
                next_section_match = re.search(r'^\s*#{2,}\s+', remaining_content, re.MULTILINE)
                if next_section_match:
                    # 只提取到下一个段落开始之前的内容
                    section_content = remaining_content[:next_section_match.start()]
                else:
                    # 如果没有下一个段落，提取到文档末尾
                    section_content = remaining_content
                
                # 提取列表项 (-, *, +, 数字., [x], [ ])
                list_patterns = [
                    r'^\s*[-\*\+]\s+(.+)$',
                    r'^\s*\d+\.\s+(.+)$',
                    r'^\s*•\s+(.+)$',
                    r'^\s*\[x\]\s+(.+)$',  # 已完成的复选框
                    r'^\s*\[\s\]\s+(.+)$'  # 未完成的复选框
                ]
                
                for list_pattern in list_patterns:
                    matches = re.findall(list_pattern, section_content, re.MULTILINE)
                    items.extend([match.strip() for match in matches])
                
                if items:
                    break
        
        return list(set(items))  # 去重
    
    def _extract_completed_work(self, content: str) -> List[str]:
        """提取已完成工作"""
        
        patterns = [
            r'(?i)completed?\s+work[:\s]*',
            r'(?i)completed?\s+tasks?[:\s]*',
            r'(?i)已完成[工作任务]*[:\s]*',
            r'(?i)完成[的工作任务]*[:\s]*'
        ]
        
        return self._extract_list_items(content, patterns)
    
    def _extract_next_actions(self, content: str) -> List[str]:
        """提取下一步行动"""
        
        patterns = [
            r'(?i)next\s+actions?[:\s]*',
            r'(?i)todo[:\s]*',
            r'(?i)下一步[行动]*[:\s]*',
            r'(?i)待办[事项]*[:\s]*'
        ]
        
        return self._extract_list_items(content, patterns)
    
    def _extract_risks(self, content: str) -> List[str]:
        """提取风险和问题"""
        
        patterns = [
            r'(?i)risks?[:\s]*',
            r'(?i)issues?[:\s]*',
            r'(?i)problems?[:\s]*',
            r'(?i)风险[:\s]*',
            r'(?i)问题[:\s]*'
        ]
        
        return self._extract_list_items(content, patterns)
    
    def _extract_team_members(self, content: str) -> List[str]:
        """提取团队成员"""
        
        # 首先尝试精确匹配团队成员行
        team_member_patterns = [
            r'(?i)[-\*\+]\s*\*{0,2}team\s+members?\*{0,2}[:\s]*([^:\n\r]+)',
            r'(?i)[-\*\+]\s*\*{0,2}团队成员\*{0,2}[:\s]*([^:\n\r]+)',
            r'(?i)[-\*\+]\s*\*{0,2}成员\*{0,2}[:\s]*([^:\n\r]+)'
        ]
        
        members = []
        for pattern in team_member_patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            for match in matches:
                # 按逗号分割团队成员
                member_list = [member.strip() for member in match.split(',')]
                members.extend(member_list)
        
        if members:
            return list(set(members))
        
        # 如果没有找到精确匹配，退回到段落级别提取
        patterns = [
            r'(?i)team\s+members?[:\s]*',
            r'(?i)team[:\s]*',
            r'(?i)members?[:\s]*',
            r'(?i)团队[成员]*[:\s]*',
            r'(?i)成员[:\s]*'
        ]
        
        return self._extract_list_items(content, patterns)
    
    def _extract_tags(self, content: str) -> List[str]:
        """提取标签"""
        
        # 查找标签格式: #tag, @tag
        tag_patterns = [
            r'#([a-zA-Z0-9_\u4e00-\u9fff]+)',
            r'@([a-zA-Z0-9_\u4e00-\u9fff]+)'
        ]
        
        tags = []
        for pattern in tag_patterns:
            matches = re.findall(pattern, content)
            tags.extend(matches)
        
        return list(set(tags))
    
    def _extract_dependencies(self, content: str) -> List[str]:
        """提取依赖项目"""
        
        # 首先尝试精确匹配依赖项目行
        dependency_patterns = [
            r'(?i)[-\*\+]\s*\*{0,2}dependencies?\*{0,2}[:\s]*([^:\n\r]+)',
            r'(?i)[-\*\+]\s*\*{0,2}depends\s+on\*{0,2}[:\s]*([^:\n\r]+)',
            r'(?i)[-\*\+]\s*\*{0,2}依赖项目\*{0,2}[:\s]*([^:\n\r]+)'
        ]
        
        dependencies = []
        for pattern in dependency_patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            for match in matches:
                # 清理匹配结果，移除多余的格式化字符
                clean_match = re.sub(r'\*{2,}', '', match).strip()
                # 按逗号分割依赖项目
                dep_list = [dep.strip() for dep in clean_match.split(',') if dep.strip()]
                dependencies.extend(dep_list)
        
        if dependencies:
            return list(set(dependencies))
        
        # 如果没有找到精确匹配，退回到段落级别提取
        patterns = [
            r'(?i)dependencies[:\s]*',
            r'(?i)depends\s+on[:\s]*',
            r'(?i)依赖[项目]*[:\s]*',
            r'(?i)前置[条件]*[:\s]*'
        ]
        
        return self._extract_list_items(content, patterns)