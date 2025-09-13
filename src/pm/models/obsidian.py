"""Obsidian集成数据模型 - Sprint 18核心功能"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Set, Any
from pathlib import Path
import json


@dataclass
class ObsidianNote:
    """Obsidian笔记模型"""
    
    # 基础信息
    file_path: str
    title: str
    content: str
    created_at: datetime
    modified_at: datetime
    
    # 元数据
    frontmatter: Dict[str, Any] = field(default_factory=dict)
    tags: Set[str] = field(default_factory=set)
    
    # 链接关系
    outgoing_links: Set[str] = field(default_factory=set)  # 指向其他笔记的链接
    incoming_links: Set[str] = field(default_factory=set)  # 来自其他笔记的反向链接
    embedded_files: Set[str] = field(default_factory=set)  # 嵌入的文件
    
    # 分析数据
    word_count: int = 0
    reading_time_minutes: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'file_path': self.file_path,
            'title': self.title,
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'modified_at': self.modified_at.isoformat() if self.modified_at else None,
            'frontmatter': self.frontmatter,
            'tags': list(self.tags),
            'outgoing_links': list(self.outgoing_links),
            'incoming_links': list(self.incoming_links),
            'embedded_files': list(self.embedded_files),
            'word_count': self.word_count,
            'reading_time_minutes': self.reading_time_minutes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ObsidianNote':
        """从字典创建实例"""
        return cls(
            file_path=data['file_path'],
            title=data['title'],
            content=data['content'],
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now(),
            modified_at=datetime.fromisoformat(data['modified_at']) if data.get('modified_at') else datetime.now(),
            frontmatter=data.get('frontmatter', {}),
            tags=set(data.get('tags', [])),
            outgoing_links=set(data.get('outgoing_links', [])),
            incoming_links=set(data.get('incoming_links', [])),
            embedded_files=set(data.get('embedded_files', [])),
            word_count=data.get('word_count', 0),
            reading_time_minutes=data.get('reading_time_minutes', 0)
        )


@dataclass
class ObsidianVault:
    """Obsidian Vault模型"""
    
    vault_path: str
    vault_name: str
    total_notes: int = 0
    total_attachments: int = 0
    last_analyzed: Optional[datetime] = None
    
    # 配置信息
    config: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'vault_path': self.vault_path,
            'vault_name': self.vault_name,
            'total_notes': self.total_notes,
            'total_attachments': self.total_attachments,
            'last_analyzed': self.last_analyzed.isoformat() if self.last_analyzed else None,
            'config': self.config
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ObsidianVault':
        """从字典创建实例"""
        return cls(
            vault_path=data['vault_path'],
            vault_name=data['vault_name'],
            total_notes=data.get('total_notes', 0),
            total_attachments=data.get('total_attachments', 0),
            last_analyzed=datetime.fromisoformat(data['last_analyzed']) if data.get('last_analyzed') else None,
            config=data.get('config', {})
        )


@dataclass  
class KnowledgeGraph:
    """知识图谱模型"""
    
    nodes: Dict[str, Dict[str, Any]] = field(default_factory=dict)  # 节点信息
    edges: List[Dict[str, Any]] = field(default_factory=list)  # 连接关系
    
    # 图谱统计
    total_nodes: int = 0
    total_edges: int = 0
    density: float = 0.0
    
    # 分析结果
    hub_notes: List[str] = field(default_factory=list)  # 枢纽笔记（链接数最多）
    isolated_notes: List[str] = field(default_factory=list)  # 孤立笔记
    clusters: List[List[str]] = field(default_factory=list)  # 笔记聚类
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'nodes': self.nodes,
            'edges': self.edges,
            'total_nodes': self.total_nodes,
            'total_edges': self.total_edges,
            'density': self.density,
            'hub_notes': self.hub_notes,
            'isolated_notes': self.isolated_notes,
            'clusters': self.clusters
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KnowledgeGraph':
        """从字典创建实例"""
        return cls(
            nodes=data.get('nodes', {}),
            edges=data.get('edges', []),
            total_nodes=data.get('total_nodes', 0),
            total_edges=data.get('total_edges', 0),
            density=data.get('density', 0.0),
            hub_notes=data.get('hub_notes', []),
            isolated_notes=data.get('isolated_notes', []),
            clusters=data.get('clusters', [])
        )


@dataclass
class NoteTemplate:
    """笔记模板模型"""
    
    name: str
    description: str
    template_content: str
    variables: List[str] = field(default_factory=list)  # 模板变量
    target_folder: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    # 自动化规则
    auto_apply_conditions: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'name': self.name,
            'description': self.description,
            'template_content': self.template_content,
            'variables': self.variables,
            'target_folder': self.target_folder,
            'tags': self.tags,
            'auto_apply_conditions': self.auto_apply_conditions
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NoteTemplate':
        """从字典创建实例"""
        return cls(
            name=data['name'],
            description=data['description'],
            template_content=data['template_content'],
            variables=data.get('variables', []),
            target_folder=data.get('target_folder'),
            tags=data.get('tags', []),
            auto_apply_conditions=data.get('auto_apply_conditions', {})
        )


@dataclass
class SyncRule:
    """同步规则模型"""
    
    rule_id: str
    name: str
    description: str
    
    # 同步方向和条件
    sync_direction: str  # 'pm_to_obsidian', 'obsidian_to_pm', 'bidirectional'
    source_filter: Dict[str, Any] = field(default_factory=dict)
    target_mapping: Dict[str, str] = field(default_factory=dict)
    
    # 同步配置
    auto_sync: bool = False
    sync_interval_minutes: int = 60
    conflict_resolution: str = "manual"  # "manual", "source_wins", "target_wins", "merge"
    
    # 状态跟踪
    is_active: bool = True
    last_sync: Optional[datetime] = None
    sync_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'rule_id': self.rule_id,
            'name': self.name,
            'description': self.description,
            'sync_direction': self.sync_direction,
            'source_filter': self.source_filter,
            'target_mapping': self.target_mapping,
            'auto_sync': self.auto_sync,
            'sync_interval_minutes': self.sync_interval_minutes,
            'conflict_resolution': self.conflict_resolution,
            'is_active': self.is_active,
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'sync_count': self.sync_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SyncRule':
        """从字典创建实例"""
        return cls(
            rule_id=data['rule_id'],
            name=data['name'],
            description=data['description'],
            sync_direction=data['sync_direction'],
            source_filter=data.get('source_filter', {}),
            target_mapping=data.get('target_mapping', {}),
            auto_sync=data.get('auto_sync', False),
            sync_interval_minutes=data.get('sync_interval_minutes', 60),
            conflict_resolution=data.get('conflict_resolution', 'manual'),
            is_active=data.get('is_active', True),
            last_sync=datetime.fromisoformat(data['last_sync']) if data.get('last_sync') else None,
            sync_count=data.get('sync_count', 0)
        )