"""Obsidian深度集成 - Sprint 18核心功能

提供与Obsidian知识库的深度集成功能，包括：
- 双向数据同步
- 知识图谱分析
- 模板自动化
- 插件级集成
"""

import os
import json
import yaml
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any, Tuple
import structlog

from pm.core.config import PMConfig
from pm.models.obsidian import (
    ObsidianNote, ObsidianVault, KnowledgeGraph, 
    NoteTemplate, SyncRule
)
from pm.models.task import Task, TaskStatus

logger = structlog.get_logger()


class ObsidianIntegration:
    """Obsidian集成核心类"""
    
    def __init__(self, config: PMConfig, vault_path: Optional[str] = None):
        self.config = config
        self.vault_path = vault_path
        self.vault_info: Optional[ObsidianVault] = None
        
        # 缓存
        self._notes_cache: Dict[str, ObsidianNote] = {}
        self._graph_cache: Optional[KnowledgeGraph] = None
        self._last_scan: Optional[datetime] = None
        
        logger.info("ObsidianIntegration initialized", vault_path=vault_path)
    
    def connect_vault(self, vault_path: str) -> Tuple[bool, str]:
        """连接到Obsidian Vault"""
        try:
            vault_path_obj = Path(vault_path)
            if not vault_path_obj.exists():
                return False, f"Vault路径不存在: {vault_path}"
            
            # 检查是否为有效的Obsidian vault（包含.obsidian文件夹）
            obsidian_config_path = vault_path_obj / ".obsidian"
            if not obsidian_config_path.exists():
                return False, f"目录不是有效的Obsidian Vault: {vault_path}"
            
            self.vault_path = vault_path
            self.vault_info = ObsidianVault(
                vault_path=vault_path,
                vault_name=vault_path_obj.name,
                last_analyzed=datetime.now()
            )
            
            logger.info("Connected to Obsidian vault", vault_path=vault_path)
            return True, "成功连接到Obsidian Vault"
            
        except Exception as e:
            logger.error("Failed to connect to vault", error=str(e))
            return False, f"连接Vault失败: {str(e)}"
    
    def scan_vault(self, force_rescan: bool = False) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """扫描Vault并建立笔记索引"""
        
        if not self.vault_path:
            return False, "未连接到Vault", None
        
        # 检查是否需要重新扫描
        if not force_rescan and self._last_scan:
            if datetime.now() - self._last_scan < timedelta(minutes=5):
                return True, "使用缓存的扫描结果", self._get_scan_summary()
        
        try:
            vault_path = Path(self.vault_path)
            notes_found = 0
            attachments_found = 0
            
            # 清空缓存
            self._notes_cache.clear()
            
            # 扫描markdown文件
            for md_file in vault_path.rglob("*.md"):
                # 跳过.obsidian文件夹
                if ".obsidian" in md_file.parts:
                    continue
                
                note = self._parse_note_file(md_file)
                if note:
                    self._notes_cache[note.file_path] = note
                    notes_found += 1
            
            # 扫描附件文件
            attachment_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.pdf', '.mp4', '.mov'}
            for attachment_file in vault_path.rglob("*"):
                if attachment_file.is_file() and attachment_file.suffix.lower() in attachment_extensions:
                    if ".obsidian" not in attachment_file.parts:
                        attachments_found += 1
            
            # 更新vault信息
            if self.vault_info:
                self.vault_info.total_notes = notes_found
                self.vault_info.total_attachments = attachments_found
                self.vault_info.last_analyzed = datetime.now()
            
            self._last_scan = datetime.now()
            
            # 构建链接关系
            self._build_link_relationships()
            
            logger.info("Vault scan completed", 
                       notes=notes_found, attachments=attachments_found)
            
            return True, "Vault扫描完成", self._get_scan_summary()
            
        except Exception as e:
            logger.error("Failed to scan vault", error=str(e))
            return False, f"扫描Vault失败: {str(e)}", None
    
    def get_note(self, file_path: str) -> Optional[ObsidianNote]:
        """获取指定笔记"""
        return self._notes_cache.get(file_path)
    
    def search_notes(self, query: str, search_content: bool = True, 
                    search_titles: bool = True, search_tags: bool = True) -> List[ObsidianNote]:
        """搜索笔记"""
        
        results = []
        query_lower = query.lower()
        
        for note in self._notes_cache.values():
            match = False
            
            # 搜索标题
            if search_titles and query_lower in note.title.lower():
                match = True
            
            # 搜索内容
            if search_content and query_lower in note.content.lower():
                match = True
            
            # 搜索标签
            if search_tags:
                for tag in note.tags:
                    if query_lower in tag.lower():
                        match = True
                        break
            
            if match:
                results.append(note)
        
        return results
    
    def get_notes_by_tag(self, tag: str) -> List[ObsidianNote]:
        """根据标签获取笔记"""
        return [note for note in self._notes_cache.values() if tag in note.tags]
    
    def create_note(self, title: str, content: str, folder: Optional[str] = None,
                   tags: Optional[List[str]] = None, frontmatter: Optional[Dict[str, Any]] = None) -> Tuple[bool, str, Optional[str]]:
        """创建新笔记"""
        
        if not self.vault_path:
            return False, "未连接到Vault", None
        
        try:
            # 构建文件路径
            vault_path = Path(self.vault_path)
            if folder:
                target_dir = vault_path / folder
                target_dir.mkdir(parents=True, exist_ok=True)
            else:
                target_dir = vault_path
            
            # 生成文件名
            safe_title = re.sub(r'[<>:"/\\|?*]', '-', title)
            file_path = target_dir / f"{safe_title}.md"
            
            # 如果文件已存在，添加数字后缀
            counter = 1
            while file_path.exists():
                file_path = target_dir / f"{safe_title}_{counter}.md"
                counter += 1
            
            # 构建笔记内容
            note_content = ""
            
            # 添加frontmatter
            if frontmatter or tags:
                note_content += "---\n"
                if frontmatter:
                    for key, value in frontmatter.items():
                        note_content += f"{key}: {value}\n"
                if tags:
                    note_content += f"tags: [{', '.join(tags)}]\n"
                note_content += f"created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                note_content += "---\n\n"
            
            # 添加内容
            note_content += content
            
            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(note_content)
            
            # 更新缓存
            relative_path = str(file_path.relative_to(vault_path))
            new_note = ObsidianNote(
                file_path=relative_path,
                title=title,
                content=content,
                created_at=datetime.now(),
                modified_at=datetime.now(),
                frontmatter=frontmatter or {},
                tags=set(tags) if tags else set()
            )
            
            self._notes_cache[relative_path] = new_note
            
            logger.info("Note created successfully", file_path=str(file_path))
            return True, "笔记创建成功", relative_path
            
        except Exception as e:
            logger.error("Failed to create note", error=str(e))
            return False, f"创建笔记失败: {str(e)}", None
    
    def update_note(self, file_path: str, content: Optional[str] = None,
                   frontmatter: Optional[Dict[str, Any]] = None) -> Tuple[bool, str]:
        """更新笔记"""
        
        if not self.vault_path:
            return False, "未连接到Vault"
        
        try:
            full_path = Path(self.vault_path) / file_path
            if not full_path.exists():
                return False, f"笔记文件不存在: {file_path}"
            
            # 读取现有内容
            existing_note = self._parse_note_file(full_path)
            if not existing_note:
                return False, "无法解析现有笔记"
            
            # 构建更新后的内容
            updated_content = content if content is not None else existing_note.content
            updated_frontmatter = frontmatter if frontmatter is not None else existing_note.frontmatter
            
            # 重新构建文件内容
            file_content = ""
            if updated_frontmatter:
                file_content += "---\n"
                for key, value in updated_frontmatter.items():
                    file_content += f"{key}: {value}\n"
                file_content += f"modified: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                file_content += "---\n\n"
            
            file_content += updated_content
            
            # 写入文件
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(file_content)
            
            # 更新缓存
            if file_path in self._notes_cache:
                note = self._notes_cache[file_path]
                note.content = updated_content
                note.frontmatter = updated_frontmatter
                note.modified_at = datetime.now()
            
            logger.info("Note updated successfully", file_path=file_path)
            return True, "笔记更新成功"
            
        except Exception as e:
            logger.error("Failed to update note", error=str(e))
            return False, f"更新笔记失败: {str(e)}"
    
    def _parse_note_file(self, file_path: Path) -> Optional[ObsidianNote]:
        """解析笔记文件"""
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 解析frontmatter
            frontmatter = {}
            main_content = content
            
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    try:
                        frontmatter = yaml.safe_load(parts[1]) or {}
                        main_content = parts[2].strip()
                    except yaml.YAMLError:
                        pass
            
            # 提取标签
            tags = set()
            if 'tags' in frontmatter:
                if isinstance(frontmatter['tags'], list):
                    tags.update(frontmatter['tags'])
                elif isinstance(frontmatter['tags'], str):
                    tags.add(frontmatter['tags'])
            
            # 从内容中提取标签
            tag_pattern = r'#(\w+)'
            content_tags = re.findall(tag_pattern, main_content)
            tags.update(content_tags)
            
            # 提取链接
            outgoing_links = set()
            link_pattern = r'\[\[([^\]]+)\]\]'
            links = re.findall(link_pattern, main_content)
            outgoing_links.update(links)
            
            # 获取文件信息
            stat = file_path.stat()
            relative_path = str(file_path.relative_to(Path(self.vault_path)))
            
            return ObsidianNote(
                file_path=relative_path,
                title=file_path.stem,
                content=main_content,
                created_at=datetime.fromtimestamp(stat.st_ctime),
                modified_at=datetime.fromtimestamp(stat.st_mtime),
                frontmatter=frontmatter,
                tags=tags,
                outgoing_links=outgoing_links,
                word_count=len(main_content.split()),
                reading_time_minutes=max(1, len(main_content.split()) // 200)
            )
            
        except Exception as e:
            logger.error("Failed to parse note file", file_path=str(file_path), error=str(e))
            return None
    
    def _build_link_relationships(self):
        """构建笔记间的链接关系"""
        
        # 建立反向链接
        for note in self._notes_cache.values():
            for link in note.outgoing_links:
                # 查找目标笔记
                target_note = None
                for candidate in self._notes_cache.values():
                    if candidate.title == link or candidate.file_path == link:
                        target_note = candidate
                        break
                
                if target_note:
                    target_note.incoming_links.add(note.file_path)
    
    def _get_scan_summary(self) -> Dict[str, Any]:
        """获取扫描摘要"""
        return {
            'total_notes': len(self._notes_cache),
            'total_attachments': self.vault_info.total_attachments if self.vault_info else 0,
            'last_scan': self._last_scan.isoformat() if self._last_scan else None,
            'vault_info': self.vault_info.to_dict() if self.vault_info else None
        }