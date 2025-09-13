"""Task storage and persistence manager."""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import structlog

from pm.core.config import PMConfig
from pm.models.task import Task, TaskFilter, TaskStatus, TaskContext

logger = structlog.get_logger()


class TaskStorage:
    """任务存储管理器
    
    负责任务的持久化存储、检索和管理
    使用JSON文件存储，便于人类阅读和调试
    """
    
    def __init__(self, config: Optional[PMConfig] = None):
        self.config = config or PMConfig()
        self.tasks_dir = self.config.data_dir / "tasks"
        self.tasks_dir.mkdir(exist_ok=True)
        
        # 按状态分类存储
        self.inbox_file = self.tasks_dir / "inbox.json"
        self.next_actions_file = self.tasks_dir / "next_actions.json"
        self.projects_file = self.tasks_dir / "projects.json"
        self.waiting_file = self.tasks_dir / "waiting_for.json"
        self.someday_file = self.tasks_dir / "someday_maybe.json"
        self.completed_file = self.tasks_dir / "completed.json"
        self.reference_file = self.tasks_dir / "reference.json"
        
        # 索引文件
        self.index_file = self.tasks_dir / "index.json"
        
        # 内存缓存
        self._task_cache: Dict[str, Task] = {}
        self._index_cache: Dict[str, str] = {}  # task_id -> file_name
        self._cache_loaded = False
        
        logger.info("TaskStorage initialized", tasks_dir=str(self.tasks_dir))
    
    def _get_file_for_status(self, status: TaskStatus) -> Path:
        """根据任务状态获取对应的存储文件"""
        
        file_map = {
            TaskStatus.INBOX: self.inbox_file,
            TaskStatus.NEXT_ACTION: self.next_actions_file,
            TaskStatus.PROJECT: self.projects_file,
            TaskStatus.WAITING_FOR: self.waiting_file,
            TaskStatus.SOMEDAY_MAYBE: self.someday_file,
            TaskStatus.COMPLETED: self.completed_file,
            TaskStatus.REFERENCE: self.reference_file,
            TaskStatus.DELETED: self.completed_file  # 删除的任务也存在完成文件中
        }
        
        return file_map.get(status, self.inbox_file)
    
    def _load_tasks_from_file(self, file_path: Path) -> List[Task]:
        """从文件加载任务列表"""
        
        if not file_path.exists():
            return []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            tasks = []
            for task_data in data.get('tasks', []):
                try:
                    task = Task(**task_data)
                    tasks.append(task)
                except Exception as e:
                    logger.error("Failed to parse task", 
                               task_id=task_data.get('id', 'unknown'),
                               error=str(e))
            
            return tasks
            
        except Exception as e:
            logger.error("Failed to load tasks from file", 
                        file=str(file_path), 
                        error=str(e))
            return []
    
    def _save_tasks_to_file(self, file_path: Path, tasks: List[Task]) -> bool:
        """保存任务列表到文件"""
        
        try:
            # 创建文件目录
            file_path.parent.mkdir(exist_ok=True)
            
            # 准备数据
            data = {
                "saved_at": datetime.now().isoformat(),
                "count": len(tasks),
                "tasks": [task.dict() for task in tasks]
            }
            
            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            
            logger.debug("Tasks saved to file", 
                        file=str(file_path), 
                        count=len(tasks))
            
            return True
            
        except Exception as e:
            logger.error("Failed to save tasks to file", 
                        file=str(file_path), 
                        error=str(e))
            return False
    
    def _ensure_cache_loaded(self) -> None:
        """确保缓存已加载"""
        
        if self._cache_loaded:
            return
        
        logger.info("Loading task cache")
        
        # 加载索引
        self._load_index()
        
        # 加载所有任务文件
        all_files = [
            self.inbox_file,
            self.next_actions_file,
            self.projects_file,
            self.waiting_file,
            self.someday_file,
            self.completed_file,
            self.reference_file
        ]
        
        for file_path in all_files:
            tasks = self._load_tasks_from_file(file_path)
            for task in tasks:
                self._task_cache[task.id] = task
                self._index_cache[task.id] = file_path.name
        
        self._cache_loaded = True
        
        logger.info("Task cache loaded", 
                   total_tasks=len(self._task_cache))
    
    def _load_index(self) -> None:
        """加载任务索引"""
        
        if not self.index_file.exists():
            return
        
        try:
            with open(self.index_file, 'r', encoding='utf-8') as f:
                self._index_cache = json.load(f)
        except Exception as e:
            logger.error("Failed to load task index", error=str(e))
    
    def _save_index(self) -> None:
        """保存任务索引"""
        
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(self._index_cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error("Failed to save task index", error=str(e))
    
    def save_task(self, task: Task) -> bool:
        """保存任务"""
        
        self._ensure_cache_loaded()
        
        try:
            # 更新缓存
            task.updated_at = datetime.now()
            self._task_cache[task.id] = task
            
            # 确定存储文件
            target_file = self._get_file_for_status(task.status)
            
            # 如果任务状态改变，需要从旧文件移除
            if task.id in self._index_cache:
                old_file_name = self._index_cache[task.id]
                old_file = self.tasks_dir / old_file_name
                
                if old_file != target_file:
                    # 从旧文件移除
                    old_tasks = self._load_tasks_from_file(old_file)
                    old_tasks = [t for t in old_tasks if t.id != task.id]
                    self._save_tasks_to_file(old_file, old_tasks)
            
            # 更新索引
            self._index_cache[task.id] = target_file.name
            self._save_index()
            
            # 加载目标文件的现有任务
            existing_tasks = self._load_tasks_from_file(target_file)
            
            # 更新或添加任务
            updated = False
            for i, existing_task in enumerate(existing_tasks):
                if existing_task.id == task.id:
                    existing_tasks[i] = task
                    updated = True
                    break
            
            if not updated:
                existing_tasks.append(task)
            
            # 保存到文件
            success = self._save_tasks_to_file(target_file, existing_tasks)
            
            if success:
                logger.info("Task saved", 
                           task_id=task.id, 
                           title=task.title,
                           status=task.status.value)
            
            return success
            
        except Exception as e:
            logger.error("Failed to save task", 
                        task_id=task.id, 
                        error=str(e))
            return False
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """根据ID获取任务（支持短ID）"""
        
        self._ensure_cache_loaded()
        
        # 首先尝试完整ID匹配
        if task_id in self._task_cache:
            return self._task_cache[task_id]
        
        # 如果没找到，尝试短ID匹配
        matching_tasks = [
            task for full_id, task in self._task_cache.items()
            if full_id.startswith(task_id)
        ]
        
        if len(matching_tasks) == 1:
            return matching_tasks[0]
        elif len(matching_tasks) > 1:
            logger.warning("Multiple tasks match short ID", 
                          short_id=task_id, 
                          matches=len(matching_tasks))
            return matching_tasks[0]  # 返回第一个匹配
        
        return None
    
    def get_tasks_by_status(self, status: TaskStatus) -> List[Task]:
        """根据状态获取任务列表"""
        
        self._ensure_cache_loaded()
        
        return [
            task for task in self._task_cache.values() 
            if task.status == status
        ]
    
    def get_tasks_by_context(self, context: TaskContext) -> List[Task]:
        """根据情境获取任务列表"""
        
        self._ensure_cache_loaded()
        
        return [
            task for task in self._task_cache.values() 
            if task.context == context and task.is_actionable()
        ]
    
    def search_tasks(self, filter_obj: TaskFilter) -> List[Task]:
        """根据过滤条件搜索任务"""
        
        self._ensure_cache_loaded()
        
        matching_tasks = []
        for task in self._task_cache.values():
            if filter_obj.matches(task):
                matching_tasks.append(task)
        
        return matching_tasks
    
    def get_inbox_tasks(self) -> List[Task]:
        """获取收件箱任务"""
        return self.get_tasks_by_status(TaskStatus.INBOX)
    
    def get_next_actions(self) -> List[Task]:
        """获取下一步行动"""
        return self.get_tasks_by_status(TaskStatus.NEXT_ACTION)
    
    def get_all_tasks(self) -> List[Task]:
        """获取所有任务"""
        
        self._ensure_cache_loaded()
        return list(self._task_cache.values())
    
    def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        
        task = self.get_task(task_id)
        if not task:
            return False
        
        # 标记为删除
        task.update_status(TaskStatus.DELETED)
        
        return self.save_task(task)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取任务统计信息"""
        
        self._ensure_cache_loaded()
        
        stats = {
            "total_tasks": len(self._task_cache),
            "by_status": {},
            "by_context": {},
            "by_priority": {},
            "inbox_count": 0,
            "overdue_count": 0,
            "completed_today": 0
        }
        
        today = datetime.now().date()
        
        for task in self._task_cache.values():
            # 按状态统计
            status_key = task.status.value
            stats["by_status"][status_key] = stats["by_status"].get(status_key, 0) + 1
            
            # 按情境统计
            if task.context:
                context_key = task.context.value
                stats["by_context"][context_key] = stats["by_context"].get(context_key, 0) + 1
            
            # 按优先级统计
            priority_key = task.priority.value
            stats["by_priority"][priority_key] = stats["by_priority"].get(priority_key, 0) + 1
            
            # 收件箱计数
            if task.status == TaskStatus.INBOX:
                stats["inbox_count"] += 1
            
            # 过期任务计数
            if task.due_date and task.due_date.date() < today and not task.is_completed():
                stats["overdue_count"] += 1
            
            # 今日完成任务计数
            if task.completed_at and task.completed_at.date() == today:
                stats["completed_today"] += 1
        
        return stats
    
    def cleanup_completed_tasks(self, days_to_keep: int = 30) -> int:
        """清理完成的任务（保留指定天数）"""
        
        cutoff_date = datetime.now() - __import__('datetime').timedelta(days=days_to_keep)
        
        completed_tasks = self.get_tasks_by_status(TaskStatus.COMPLETED)
        deleted_count = 0
        
        for task in completed_tasks:
            if task.completed_at and task.completed_at < cutoff_date:
                if task.id in self._task_cache:
                    del self._task_cache[task.id]
                if task.id in self._index_cache:
                    del self._index_cache[task.id]
                deleted_count += 1
        
        if deleted_count > 0:
            # 重新保存完成任务文件
            remaining_completed = self.get_tasks_by_status(TaskStatus.COMPLETED)
            self._save_tasks_to_file(self.completed_file, remaining_completed)
            self._save_index()
            
            logger.info("Cleaned up completed tasks", 
                       deleted_count=deleted_count,
                       days_to_keep=days_to_keep)
        
        return deleted_count