"""Google Tasks集成 - Sprint 9-10核心功能

提供与Google Tasks的双向同步功能
"""

import json
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import structlog

from pm.core.config import PMConfig
from pm.models.task import Task, TaskStatus, TaskContext, TaskPriority, EnergyLevel
from .google_auth import GoogleAuthManager
from enum import Enum
from pm.storage.daily_task_tracker import DailyTaskTracker
from datetime import date

logger = structlog.get_logger()


class TaskCategory(Enum):
    """任务分类枚举"""
    HABIT = "habit"      # 习惯
    EVENT = "event"      # 日程/事件
    TASK = "task"        # 普通任务


class GoogleTask:
    """Google Tasks任务封装"""
    
    def __init__(self, 
                 task_id: str,
                 title: str,
                 notes: Optional[str] = None,
                 status: str = "needsAction",
                 due: Optional[datetime] = None,
                 completed: Optional[datetime] = None,
                 parent: Optional[str] = None,
                 position: Optional[str] = None,
                 updated: Optional[datetime] = None):
        self.task_id = task_id
        self.title = title
        self.notes = notes
        self.status = status  # "needsAction" or "completed"
        self.due = due
        self.completed = completed
        self.parent = parent  # 父任务ID（用于子任务）
        self.position = position
        self.updated = updated
    
    @property
    def is_completed(self) -> bool:
        """检查任务是否已完成"""
        return self.status == "completed"
    
    @property
    def is_overdue(self) -> bool:
        """检查任务是否已过期"""
        if not self.due:
            return False
        return datetime.now() > self.due and not self.is_completed

    def get_task_category(self) -> TaskCategory:
        """识别任务分类（基于前缀）"""
        title_lower = self.title.lower()

        # 检查习惯前缀
        habit_prefixes = ['[habit]', '习惯:', 'habit:', '[习惯]']
        for prefix in habit_prefixes:
            if title_lower.startswith(prefix.lower()):
                return TaskCategory.HABIT

        # 检查日程/事件前缀
        event_prefixes = ['[event]', '日程:', 'event:', '[日程]', '事件:', '[事件]']
        for prefix in event_prefixes:
            if title_lower.startswith(prefix.lower()):
                return TaskCategory.EVENT

        # 检查任务前缀或默认
        task_prefixes = ['[task]', '任务:', 'task:', '[任务]']
        for prefix in task_prefixes:
            if title_lower.startswith(prefix.lower()):
                return TaskCategory.TASK

        # 默认为普通任务
        return TaskCategory.TASK

    def get_clean_title(self) -> str:
        """获取去除前缀的标题"""
        # 定义所有前缀
        all_prefixes = [
            '[habit]', '习惯:', 'habit:', '[习惯]',
            '[event]', '日程:', 'event:', '[日程]', '事件:', '[事件]',
            '[task]', '任务:', 'task:', '[任务]'
        ]

        clean_title = self.title
        title_lower = self.title.lower()

        # 去除前缀
        for prefix in all_prefixes:
            if title_lower.startswith(prefix.lower()):
                clean_title = self.title[len(prefix):].strip()
                break

        return clean_title
    
    def to_gtd_task(self) -> Task:
        """转换为GTD任务"""

        # 根据任务内容推断上下文
        context = self._infer_context()

        # 根据截止时间推断优先级
        priority = self._infer_priority()

        # 根据任务复杂度推断所需精力
        energy = self._infer_energy_level()

        # 转换状态
        if self.is_completed:
            gtd_status = TaskStatus.COMPLETED
        else:
            gtd_status = TaskStatus.NEXT_ACTION

        # 获取任务分类
        category = self.get_task_category()

        # 使用清理后的标题，但保留分类信息
        clean_title = self.get_clean_title()

        # 根据分类添加不同的表情前缀
        if category == TaskCategory.HABIT:
            title_with_emoji = f"🎯 {clean_title}"
        elif category == TaskCategory.EVENT:
            title_with_emoji = f"📅 {clean_title}"
        else:
            title_with_emoji = f"📝 {clean_title}"

        task = Task(
            title=title_with_emoji,
            description=self._generate_description(),
            status=gtd_status,
            context=context,
            priority=priority,
            energy_required=energy,
            due_date=self.due,
            completed_at=self.completed,
            source="google_tasks",
            source_id=self.task_id,
            tags=[f"category:{category.value}"]  # 添加分类标签
        )

        return task
    
    def _infer_context(self) -> TaskContext:
        """根据任务内容推断执行上下文"""
        
        title_lower = self.title.lower()
        notes_lower = (self.notes or "").lower()
        combined = f"{title_lower} {notes_lower}"
        
        # 上下文关键词映射
        context_keywords = {
            TaskContext.PHONE: ['打电话', '联系', '通话', 'call', '咨询', '沟通'],
            TaskContext.COMPUTER: ['编程', '开发', '写代码', '系统', '网站', '程序', '测试', '部署'],
            TaskContext.MEETING: ['会议', '讨论', 'meeting', '面谈', '汇报', '开会'],
            TaskContext.FOCUS: ['思考', '规划', '设计', '分析', '研究', '学习', '写作'],
            TaskContext.OFFICE: ['办公', '文档', '整理', '归档', '报告', '表格'],
            TaskContext.READING: ['阅读', '学习', '看书', '培训', '教程'],
            TaskContext.ERRANDS: ['购买', '取', '送', '邮寄', '银行', '医院']
        }
        
        for context, keywords in context_keywords.items():
            if any(keyword in combined for keyword in keywords):
                return context
        
        # 默认上下文
        return TaskContext.FOCUS
    
    def _infer_priority(self) -> TaskPriority:
        """根据截止时间推断优先级"""

        if not self.due:
            return TaskPriority.MEDIUM

        # 确保时间对象都有时区信息
        from datetime import timezone
        now = datetime.now(timezone.utc)
        if self.due.tzinfo is None:
            due_date = self.due.replace(tzinfo=timezone.utc)
        else:
            due_date = self.due

        time_until_due = (due_date - now).total_seconds()
        hours_until = time_until_due / 3600

        if hours_until <= 6:
            return TaskPriority.HIGH
        elif hours_until <= 48:
            return TaskPriority.MEDIUM
        else:
            return TaskPriority.LOW
    
    def _infer_energy_level(self) -> EnergyLevel:
        """根据任务复杂度推断所需精力水平"""
        
        # 分析标题和描述的复杂度
        title_words = len(self.title.split())
        notes_length = len(self.notes or "")
        
        # 包含多个步骤或复杂词汇的任务需要更高精力
        complex_keywords = ['设计', '分析', '规划', '开发', '创建', '制定', '评估', '研究']
        has_complex_words = any(word in self.title.lower() or word in (self.notes or "").lower() 
                               for word in complex_keywords)
        
        if has_complex_words or notes_length > 100 or title_words > 8:
            return EnergyLevel.HIGH
        elif notes_length > 20 or title_words > 4:
            return EnergyLevel.MEDIUM
        else:
            return EnergyLevel.LOW
    
    def _generate_description(self) -> str:
        """生成任务描述"""
        
        desc_parts = []
        
        if self.notes:
            desc_parts.append(f"备注: {self.notes}")
        
        if self.due:
            desc_parts.append(f"截止时间: {self.due.strftime('%Y-%m-%d %H:%M')}")
        
        if self.completed:
            desc_parts.append(f"完成时间: {self.completed.strftime('%Y-%m-%d %H:%M')}")
        
        if self.parent:
            desc_parts.append(f"父任务ID: {self.parent}")
        
        desc_parts.append(f"来源: Google Tasks")
        desc_parts.append(f"最后更新: {self.updated.strftime('%Y-%m-%d %H:%M') if self.updated else 'N/A'}")
        
        return "\\n".join(desc_parts)
    
    @classmethod
    def from_api_response(cls, task_data: Dict[str, Any]) -> 'GoogleTask':
        """从Google Tasks API响应创建实例"""
        
        # 解析日期字段
        due_date = None
        if task_data.get('due'):
            try:
                due_date = datetime.fromisoformat(task_data['due'].replace('Z', '+00:00'))
            except:
                pass
        
        completed_date = None
        if task_data.get('completed'):
            try:
                completed_date = datetime.fromisoformat(task_data['completed'].replace('Z', '+00:00'))
            except:
                pass
        
        updated_date = None
        if task_data.get('updated'):
            try:
                updated_date = datetime.fromisoformat(task_data['updated'].replace('Z', '+00:00'))
            except:
                pass
        
        return cls(
            task_id=task_data['id'],
            title=task_data['title'],
            notes=task_data.get('notes'),
            status=task_data.get('status', 'needsAction'),
            due=due_date,
            completed=completed_date,
            parent=task_data.get('parent'),
            position=task_data.get('position'),
            updated=updated_date
        )


class GoogleTasksIntegration:
    """Google Tasks集成管理器"""
    
    def __init__(self, config: PMConfig):
        self.config = config
        self.google_auth = GoogleAuthManager(config)
        self.task_tracker = DailyTaskTracker()

        logger.info("Google Tasks integration initialized")
    
    def sync_tasks_from_google(self, list_id: str = '@default') -> Tuple[int, int, List[str]]:
        """从Google Tasks同步任务到GTD系统
        
        Args:
            list_id: Google Tasks列表ID，默认为默认列表
            
        Returns:
            Tuple[新增任务数, 更新任务数, 错误信息列表]
        """
        
        if not self.google_auth.is_google_authenticated():
            return 0, 0, ["未通过Google认证，请先运行: pm auth login google"]
        
        try:
            # 获取Google Tasks
            google_tasks = self._fetch_google_tasks(list_id)
            
            if not google_tasks:
                logger.info("No Google tasks found", list_id=list_id)
                return 0, 0, []
            
            # 同步到GTD系统
            from pm.agents.gtd_agent import GTDAgent
            agent = GTDAgent(self.config)
            
            added_count = 0
            updated_count = 0
            errors = []
            
            # 获取现有任务（按source_id索引）
            existing_tasks = agent.storage.get_all_tasks()
            existing_by_source_id = {
                task.source_id: task for task in existing_tasks 
                if task.source_id and task.source == "google_tasks"
            }
            
            for google_task in google_tasks:
                try:
                    gtd_task = google_task.to_gtd_task()
                    
                    if google_task.task_id in existing_by_source_id:
                        # 更新现有任务
                        existing_task = existing_by_source_id[google_task.task_id]
                        existing_task.title = gtd_task.title
                        existing_task.description = gtd_task.description
                        existing_task.status = gtd_task.status
                        existing_task.due_date = gtd_task.due_date
                        existing_task.completed_at = gtd_task.completed_at
                        existing_task.priority = gtd_task.priority
                        
                        success = agent.storage.save_task(existing_task)
                        if success:
                            updated_count += 1
                            logger.info("Updated task from Google Tasks",
                                      task_title=google_task.title)
                        else:
                            errors.append(f"更新任务失败: {google_task.title}")
                    else:
                        # 创建新任务
                        success = agent.storage.save_task(gtd_task)
                        if success:
                            added_count += 1
                            logger.info("Added task from Google Tasks",
                                      task_title=google_task.title)
                        else:
                            errors.append(f"保存新任务失败: {google_task.title}")
                
                except Exception as e:
                    error_msg = f"处理Google任务'{google_task.title}'时出错: {str(e)}"
                    errors.append(error_msg)
                    logger.error("Error processing Google task", 
                               task_title=google_task.title, error=str(e))
            
            # 同步到每日任务追踪器
            synced_to_tracker = self.task_tracker.sync_from_google_tasks(
                google_tasks,
                date.today().isoformat()
            )

            logger.info("Google Tasks sync completed",
                       total_tasks=len(google_tasks),
                       added_count=added_count,
                       updated_count=updated_count,
                       errors_count=len(errors),
                       synced_to_tracker=synced_to_tracker)

            return added_count, updated_count, errors
        
        except Exception as e:
            error_msg = f"同步Google Tasks时发生错误: {str(e)}"
            logger.error("Google Tasks sync failed", error=str(e))
            return 0, 0, [error_msg]
    
    def sync_task_to_google(self, gtd_task: Task, list_id: str = '@default') -> Tuple[bool, str]:
        """将GTD任务同步到Google Tasks
        
        Args:
            gtd_task: GTD任务
            list_id: Google Tasks列表ID
            
        Returns:
            Tuple[是否成功, 消息]
        """
        
        if not self.google_auth.is_google_authenticated():
            return False, "未通过Google认证，请先运行: pm auth login google"
        
        # 检查认证状态
        token = self.google_auth.get_google_token()
        if not token or token.is_expired:
            return False, "Google认证已过期，请重新认证"
        
        try:
            # 准备任务数据
            task_data = {
                'title': gtd_task.title,
                'notes': gtd_task.description or '',
                'status': 'completed' if gtd_task.is_completed() else 'needsAction'
            }
            
            # 添加截止时间
            if gtd_task.due_date:
                task_data['due'] = gtd_task.due_date.isoformat()
            
            # Google Tasks API URL
            api_url = f'https://www.googleapis.com/tasks/v1/lists/{list_id}/tasks'
            
            headers = {
                'Authorization': token.authorization_header,
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            logger.info("Syncing GTD task to Google Tasks",
                       task_title=gtd_task.title,
                       list_id=list_id,
                       task_data=task_data)
            
            response = requests.post(
                api_url,
                headers=headers,
                json=task_data,
                timeout=30
            )
            
            if response.status_code == 200:
                created_task = response.json()
                google_task_id = created_task.get('id')
                
                # 更新GTD任务的source信息
                gtd_task.source = "google_tasks"
                gtd_task.source_id = google_task_id
                
                logger.info("Successfully synced GTD task to Google Tasks",
                           task_title=gtd_task.title,
                           google_task_id=google_task_id)
                
                return True, f"已将任务'{gtd_task.title}'同步到Google Tasks"
            
            elif response.status_code == 401:
                logger.error("Google Tasks API authentication failed")
                return False, "Google认证失败，请重新登录"
            else:
                logger.error("Google Tasks API create task failed", 
                           status_code=response.status_code,
                           response=response.text)
                return False, f"创建Google任务失败 (HTTP {response.status_code})"
                
        except requests.RequestException as e:
            error_msg = f"网络请求失败: {str(e)}"
            logger.error("HTTP request to Google Tasks API failed", error=str(e))
            return False, error_msg
        except Exception as e:
            error_msg = f"同步任务到Google Tasks时出错: {str(e)}"
            logger.error("Error syncing task to Google Tasks", 
                        task_id=gtd_task.id, error=str(e))
            return False, error_msg
    
    def get_google_tasks_lists(self) -> List[Dict[str, Any]]:
        """获取Google Tasks列表"""
        
        if not self.google_auth.is_google_authenticated():
            return []
        
        # 检查认证状态
        token = self.google_auth.get_google_token()
        if not token or token.is_expired:
            logger.warning("No valid token for Google Tasks API")
            return []
        
        try:
            # Google Tasks API URL for task lists
            api_url = 'https://www.googleapis.com/tasks/v1/users/@me/lists'
            
            headers = {
                'Authorization': token.authorization_header,
                'Accept': 'application/json'
            }
            
            # API参数
            params = {
                'maxResults': 100
            }
            
            logger.info("Fetching Google Tasks lists from API")
            
            response = requests.get(
                api_url,
                headers=headers,
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                lists_data = response.json()
                task_lists = []
                
                for list_data in lists_data.get('items', []):
                    task_list = {
                        'id': list_data.get('id'),
                        'title': list_data.get('title'),
                        'updated': list_data.get('updated')
                    }
                    task_lists.append(task_list)
                
                logger.info("Successfully fetched Google Tasks lists", 
                           count=len(task_lists))
                return task_lists
            
            elif response.status_code == 401:
                logger.error("Google Tasks API authentication failed - token may be expired")
                return []
            else:
                logger.error("Google Tasks Lists API request failed", 
                           status_code=response.status_code,
                           response=response.text)
                return []
                
        except requests.RequestException as e:
            logger.error("HTTP request to Google Tasks Lists API failed", error=str(e))
            return []
        except Exception as e:
            logger.error("Error fetching Google Tasks lists", error=str(e))
            return []
    
    def _fetch_google_tasks(self, list_id: str = '@default') -> List[GoogleTask]:
        """从Google Tasks API获取任务数据"""
        
        # 检查认证状态
        token = self.google_auth.get_google_token()
        if not token or token.is_expired:
            logger.warning("No valid token for Google Tasks API")
            return []
        
        try:
            # Google Tasks API URL
            api_url = f'https://www.googleapis.com/tasks/v1/lists/{list_id}/tasks'
            
            headers = {
                'Authorization': token.authorization_header,
                'Accept': 'application/json'
            }
            
            # API参数
            params = {
                'maxResults': 100,  # 最多获取100个任务
                'showCompleted': True,  # 包含已完成的任务
                'showDeleted': False,
                'showHidden': False
            }
            
            logger.info("Fetching Google tasks from API", 
                       list_id=list_id, 
                       api_url=api_url)
            
            response = requests.get(
                api_url,
                headers=headers,
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                tasks_data = response.json()
                google_tasks = []
                
                for task_data in tasks_data.get('items', []):
                    try:
                        google_task = GoogleTask.from_api_response(task_data)
                        google_tasks.append(google_task)
                    except Exception as e:
                        logger.error("Error parsing Google task", 
                                   task_data=task_data, error=str(e))
                
                logger.info("Successfully fetched Google tasks", 
                           count=len(google_tasks))
                return google_tasks
            
            elif response.status_code == 401:
                logger.error("Google Tasks API authentication failed - token may be expired")
                return []
            elif response.status_code == 404:
                logger.warning("Google Tasks list not found", list_id=list_id)
                return []
            else:
                logger.error("Google Tasks API request failed", 
                           status_code=response.status_code,
                           response=response.text)
                return []
                
        except requests.RequestException as e:
            logger.error("HTTP request to Google Tasks API failed", error=str(e))
            return []
        except Exception as e:
            logger.error("Error fetching Google tasks", error=str(e))
            return []
    
    def mark_google_task_completed(self, task_id: str, list_id: str = '@default') -> Tuple[bool, str]:
        """标记Google Tasks中的任务为已完成"""
        
        if not self.google_auth.is_google_authenticated():
            return False, "未通过Google认证"
        
        # 检查认证状态
        token = self.google_auth.get_google_token()
        if not token or token.is_expired:
            return False, "Google认证已过期，请重新认证"
        
        try:
            # 准备更新数据
            task_data = {
                'status': 'completed'
            }
            
            # Google Tasks API URL for updating task
            api_url = f'https://www.googleapis.com/tasks/v1/lists/{list_id}/tasks/{task_id}'
            
            headers = {
                'Authorization': token.authorization_header,
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            logger.info("Marking Google task as completed", 
                       task_id=task_id,
                       list_id=list_id)
            
            response = requests.patch(
                api_url,
                headers=headers,
                json=task_data,
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info("Successfully marked Google task as completed", 
                           task_id=task_id)
                return True, f"已标记Google任务 {task_id[:8]} 为完成"
            
            elif response.status_code == 401:
                logger.error("Google Tasks API authentication failed")
                return False, "Google认证失败，请重新登录"
            elif response.status_code == 404:
                logger.warning("Google task not found", task_id=task_id)
                return False, f"Google任务 {task_id[:8]} 不存在"
            else:
                logger.error("Google Tasks API update failed", 
                           status_code=response.status_code,
                           response=response.text)
                return False, f"更新Google任务失败 (HTTP {response.status_code})"
                
        except requests.RequestException as e:
            error_msg = f"网络请求失败: {str(e)}"
            logger.error("HTTP request to Google Tasks API failed", error=str(e))
            return False, error_msg
        except Exception as e:
            error_msg = f"标记任务完成时出错: {str(e)}"
            logger.error("Error marking Google task completed",
                        task_id=task_id, error=str(e))
            return False, error_msg

    def delete_google_task(self, task_id: str) -> bool:
        """从Google Tasks删除任务

        Args:
            task_id: Google Task ID

        Returns:
            是否成功删除
        """
        try:
            if not self.google_auth.is_google_authenticated():
                logger.warning("Google未认证，无法删除任务")
                return False

            token = self.google_auth.get_google_token()
            if not token:
                return False

            # 删除任务
            api_url = f'https://www.googleapis.com/tasks/v1/lists/@default/tasks/{task_id}'
            headers = {
                'Authorization': token.authorization_header,
            }

            response = requests.delete(api_url, headers=headers)

            if response.status_code == 204:  # No content - 删除成功
                logger.info("Successfully deleted Google task", task_id=task_id)
                return True
            else:
                logger.error("Failed to delete Google task",
                           task_id=task_id,
                           status_code=response.status_code,
                           response=response.text if response.text else "No response")
                return False

        except Exception as e:
            logger.error("Error deleting Google task", task_id=task_id, error=str(e))
            return False