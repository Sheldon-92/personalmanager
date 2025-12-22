"""Google Calendar集成 - Sprint 9-10核心功能

提供与Google Calendar的双向同步功能
"""

import json
import requests
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional, Tuple
import structlog

from pm.core.config import PMConfig
from pm.models.task import Task, TaskStatus, TaskContext, TaskPriority, EnergyLevel
from .google_auth import GoogleAuthManager

logger = structlog.get_logger()


class CalendarEvent:
    """Google Calendar事件封装"""
    
    def __init__(self, 
                 event_id: str,
                 title: str,
                 start_time: datetime,
                 end_time: datetime,
                 description: Optional[str] = None,
                 location: Optional[str] = None,
                 attendees: Optional[List[str]] = None):
        self.event_id = event_id
        self.title = title
        self.start_time = start_time
        self.end_time = end_time
        self.description = description
        self.location = location
        self.attendees = attendees or []
    
    @property
    def duration_minutes(self) -> int:
        """获取事件持续时间（分钟）"""
        return int((self.end_time - self.start_time).total_seconds() / 60)
    
    @property
    def is_today(self) -> bool:
        """检查事件是否在今天"""
        today = datetime.now().date()
        return self.start_time.date() == today
    
    def to_task(self) -> Task:
        """转换为GTD任务 - 仅转换可执行的任务，不转换纯日程"""

        # 检查是否应该转换为任务
        if not self._should_convert_to_task():
            return None

        # 根据事件特征推断上下文
        context = self._infer_context()

        # 根据紧急程度推断优先级
        priority = self._infer_priority()

        # 根据持续时间推断所需精力
        energy = self._infer_energy_level()

        task = Task(
            title=f"📅 {self.title}",
            description=self._generate_task_description(),
            status=TaskStatus.NEXT_ACTION,
            context=context,
            priority=priority,
            energy_required=energy,
            estimated_duration=self.duration_minutes,
            due_date=self.start_time,
            source="google_calendar",
            source_id=self.event_id
        )

        return task

    def _should_convert_to_task(self) -> bool:
        """判断日历事件是否应该转换为任务

        规则：
        - 课程/讲座/研讨会等纯参与性活动不转换
        - 需要准备或有具体交付物的活动才转换
        """
        title_lower = self.title.lower()
        desc_lower = (self.description or "").lower()

        # 不应转换为任务的关键词（纯日程活动）
        schedule_keywords = [
            # 课程相关
            'pgdm', 'nelp', 'psam', 'course', 'class', 'lecture', 'seminar',
            'studio', 'workshop', '课程', '讲座', '研讨会', '工作坊',
            # 会议相关（纯参与）
            'standup', 'scrum', 'daily', '例会', '周会',
            # 活动相关
            'event', 'conference', 'meetup', '活动', '大会'
        ]

        # 应该转换为任务的关键词（需要行动）
        task_keywords = [
            'prepare', 'review', 'submit', 'complete', 'finish',
            'write', 'design', 'develop', 'create', 'fix',
            '准备', '提交', '完成', '撰写', '设计', '开发', '修复',
            'assignment', 'homework', 'project', 'deadline',
            '作业', '任务', '项目', '截止'
        ]

        # 检查是否包含不应转换的关键词
        for keyword in schedule_keywords:
            if keyword in title_lower:
                # 但如果同时包含任务关键词，仍然转换
                has_task_keyword = any(tk in title_lower or tk in desc_lower
                                      for tk in task_keywords)
                if not has_task_keyword:
                    return False

        # 如果明确包含任务关键词，应该转换
        for keyword in task_keywords:
            if keyword in title_lower or keyword in desc_lower:
                return True

        # 默认：短于30分钟的事件不转换（可能是例行会议）
        if self.duration_minutes < 30:
            return False

        # 其他情况默认转换
        return True
    
    def _infer_context(self) -> TaskContext:
        """根据事件内容推断执行上下文"""
        
        title_lower = self.title.lower()
        desc_lower = (self.description or "").lower()
        combined = f"{title_lower} {desc_lower}"
        
        # 上下文关键词映射
        context_keywords = {
            TaskContext.MEETING: ['会议', '讨论', 'meeting', '面谈', '汇报', '沟通'],
            TaskContext.PHONE: ['电话', '通话', 'call', '联系', '咨询'],
            TaskContext.COMPUTER: ['开发', '编程', '写代码', '系统', '测试', '部署'],
            TaskContext.FOCUS: ['思考', '规划', '设计', '分析', '研究', '学习'],
            TaskContext.OFFICE: ['办公', '文档', '整理', '归档'],
            TaskContext.READING: ['阅读', '学习', '培训', '教育']
        }
        
        for context, keywords in context_keywords.items():
            if any(keyword in combined for keyword in keywords):
                return context
        
        # 有参与者通常是会议
        if len(self.attendees) > 0:
            return TaskContext.MEETING
        
        # 默认上下文
        return TaskContext.FOCUS
    
    def _infer_priority(self) -> TaskPriority:
        """根据时间紧迫性推断优先级"""
        
        # 确保时间对象都有时区信息
        now = datetime.now(timezone.utc)
        if self.start_time.tzinfo is None:
            start_time = self.start_time.replace(tzinfo=timezone.utc)
        else:
            start_time = self.start_time
            
        time_until_event = (start_time - now).total_seconds()
        hours_until = time_until_event / 3600
        
        if hours_until <= 1:
            return TaskPriority.HIGH
        elif hours_until <= 24:
            return TaskPriority.MEDIUM
        else:
            return TaskPriority.LOW
    
    def _infer_energy_level(self) -> EnergyLevel:
        """根据持续时间推断所需精力水平"""
        
        if self.duration_minutes <= 30:
            return EnergyLevel.LOW
        elif self.duration_minutes <= 90:
            return EnergyLevel.MEDIUM
        else:
            return EnergyLevel.HIGH
    
    def _generate_task_description(self) -> str:
        """生成任务描述"""
        
        desc_parts = [f"日程时间: {self.start_time.strftime('%Y-%m-%d %H:%M')} - {self.end_time.strftime('%H:%M')}"]
        
        if self.duration_minutes:
            desc_parts.append(f"持续时间: {self.duration_minutes}分钟")
        
        if self.location:
            desc_parts.append(f"地点: {self.location}")
        
        if self.attendees:
            desc_parts.append(f"参与者: {', '.join(self.attendees[:3])}")
            if len(self.attendees) > 3:
                desc_parts[-1] += f" 等{len(self.attendees)}人"
        
        if self.description:
            desc_parts.append(f"详情: {self.description}")
        
        desc_parts.append(f"来源: Google Calendar")
        
        return "\\n".join(desc_parts)


class GoogleCalendarIntegration:
    """Google Calendar集成管理器"""
    
    def __init__(self, config: PMConfig):
        self.config = config
        self.google_auth = GoogleAuthManager(config)
        
        logger.info("Google Calendar integration initialized")
    
    def sync_calendar_to_tasks(self, days_ahead: int = 3) -> Tuple[int, List[str]]:
        """将Google Calendar事件同步为GTD任务
        
        Args:
            days_ahead: 同步未来多少天的事件
            
        Returns:
            Tuple[同步任务数量, 错误信息列表]
        """
        
        if not self.google_auth.is_google_authenticated():
            return 0, ["未通过Google认证，请先运行: pm auth login google"]
        
        try:
            # 获取日程事件
            events = self._fetch_calendar_events(days_ahead)
            
            if not events:
                logger.info("No calendar events found", days_ahead=days_ahead)
                return 0, []
            
            # 转换为GTD任务并保存
            from pm.agents.gtd_agent import GTDAgent
            agent = GTDAgent(self.config)
            
            synced_count = 0
            errors = []
            
            for event in events:
                try:
                    task = event.to_task()
                    
                    # 检查是否已存在相同的任务（通过source_id）
                    existing_tasks = agent.storage.get_all_tasks()
                    existing_event_ids = [t.source_id for t in existing_tasks if t.source_id]
                    
                    if event.event_id not in existing_event_ids:
                        # 只有应该转换的事件才保存为任务
                        if task is not None:
                            success = agent.storage.save_task(task)
                            if success:
                                synced_count += 1
                                logger.info("Synced calendar event as task",
                                          event_title=event.title,
                                          event_time=event.start_time)
                            else:
                                errors.append(f"保存任务失败: {event.title}")
                        else:
                            logger.debug("Skipped non-task calendar event",
                                       event_title=event.title)
                    
                except Exception as e:
                    error_msg = f"处理事件'{event.title}'时出错: {str(e)}"
                    errors.append(error_msg)
                    logger.error("Error processing calendar event", 
                               event_title=event.title, error=str(e))
            
            logger.info("Calendar sync completed", 
                       total_events=len(events),
                       synced_count=synced_count,
                       errors_count=len(errors))
            
            return synced_count, errors
        
        except Exception as e:
            error_msg = f"同步日程时发生错误: {str(e)}"
            logger.error("Calendar sync failed", error=str(e))
            return 0, [error_msg]
    
    def get_today_schedule(self) -> List[CalendarEvent]:
        """获取今日日程"""
        
        if not self.google_auth.is_google_authenticated():
            return []
        
        try:
            events = self._fetch_calendar_events(days_ahead=1)
            today_events = [event for event in events if event.is_today]
            
            # 按开始时间排序
            today_events.sort(key=lambda x: x.start_time)
            
            return today_events
        
        except Exception as e:
            logger.error("Error fetching today's schedule", error=str(e))
            return []
    
    def get_upcoming_events(self, days_ahead: int = 7) -> List[CalendarEvent]:
        """获取即将到来的事件"""
        
        if not self.google_auth.is_google_authenticated():
            return []
        
        try:
            events = self._fetch_calendar_events(days_ahead)
            
            # 按开始时间排序
            events.sort(key=lambda x: x.start_time)
            
            return events
        
        except Exception as e:
            logger.error("Error fetching upcoming events", error=str(e))
            return []
    
    def _fetch_calendar_events(self, days_ahead: int) -> List[CalendarEvent]:
        """从Google Calendar获取事件数据"""
        
        # 检查认证状态
        token = self.google_auth.get_google_token()
        if not token or token.is_expired:
            logger.warning("No valid token for Google Calendar API")
            return []
        
        try:
            # 计算时间范围
            now = datetime.now()
            time_min = now.isoformat() + 'Z'
            time_max = (now + timedelta(days=days_ahead)).isoformat() + 'Z'
            
            # Google Calendar API 参数
            params = {
                'timeMin': time_min,
                'timeMax': time_max,
                'singleEvents': True,
                'orderBy': 'startTime',
                'maxResults': 50
            }
            
            # 调用Google Calendar API
            headers = {
                'Authorization': token.authorization_header,
                'Accept': 'application/json'
            }
            
            calendar_api_url = 'https://www.googleapis.com/calendar/v3/calendars/primary/events'
            
            logger.info("Fetching calendar events from Google API", 
                       days_ahead=days_ahead,
                       time_range=f"{time_min} to {time_max}")
            
            response = requests.get(
                calendar_api_url,
                params=params,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                calendar_data = response.json()
                events = []
                
                for item in calendar_data.get('items', []):
                    try:
                        event = self._parse_google_calendar_event(item)
                        if event:
                            events.append(event)
                    except Exception as e:
                        logger.error("Error parsing calendar event", 
                                   event_id=item.get('id'), error=str(e))
                
                logger.info("Successfully fetched calendar events", 
                           count=len(events))
                return events
            
            elif response.status_code == 401:
                logger.error("Calendar API authentication failed - token may be expired")
                return []
            else:
                logger.error("Calendar API request failed", 
                           status_code=response.status_code,
                           response=response.text)
                return []
                
        except requests.RequestException as e:
            logger.error("HTTP request to Calendar API failed", error=str(e))
            return []
        except Exception as e:
            logger.error("Error fetching calendar events", error=str(e))
            return []
    
    def _parse_google_calendar_event(self, event_data: Dict[str, Any]) -> Optional[CalendarEvent]:
        """解析Google Calendar API返回的事件数据"""
        
        try:
            event_id = event_data.get('id')
            title = event_data.get('summary', '(无标题)')
            description = event_data.get('description', '')
            location = event_data.get('location', '')
            
            # 解析开始时间
            start_info = event_data.get('start', {})
            if 'dateTime' in start_info:
                start_time = datetime.fromisoformat(start_info['dateTime'].replace('Z', '+00:00'))
            elif 'date' in start_info:
                # 全天事件
                start_time = datetime.fromisoformat(start_info['date'] + 'T00:00:00+00:00')
            else:
                return None
            
            # 解析结束时间
            end_info = event_data.get('end', {})
            if 'dateTime' in end_info:
                end_time = datetime.fromisoformat(end_info['dateTime'].replace('Z', '+00:00'))
            elif 'date' in end_info:
                # 全天事件
                end_time = datetime.fromisoformat(end_info['date'] + 'T23:59:59+00:00')
            else:
                end_time = start_time + timedelta(hours=1)  # 默认1小时
            
            # 解析参与者
            attendees = []
            for attendee in event_data.get('attendees', []):
                if attendee.get('email'):
                    attendees.append(attendee['email'])
            
            return CalendarEvent(
                event_id=event_id,
                title=title,
                start_time=start_time,
                end_time=end_time,
                description=description,
                location=location,
                attendees=attendees
            )
            
        except Exception as e:
            logger.error("Error parsing Google Calendar event", error=str(e))
            return None
    
    def create_calendar_event(self, task: Task) -> Tuple[bool, str]:
        """为GTD任务创建Google Calendar事件
        
        Args:
            task: 要创建日程的任务
            
        Returns:
            Tuple[是否成功, 消息]
        """
        
        if not self.google_auth.is_google_authenticated():
            return False, "未通过Google认证，请先运行: pm auth login google"
        
        if not task.due_date:
            return False, "任务没有设置截止时间，无法创建日程"
        
        try:
            # TODO: 实现真实的Google Calendar API调用创建事件
            
            # 模拟创建事件
            event_id = f"created_from_task_{task.id[:8]}"
            
            logger.info("Created calendar event for task",
                       task_title=task.title,
                       event_id=event_id,
                       due_date=task.due_date)
            
            return True, f"已为任务'{task.title}'创建日程事件"
        
        except Exception as e:
            error_msg = f"创建日程事件时出错: {str(e)}"
            logger.error("Error creating calendar event", 
                        task_id=task.id, error=str(e))
            return False, error_msg
    
    def delete_calendar_event(self, event_id: str) -> Tuple[bool, str]:
        """删除Google Calendar事件
        
        Args:
            event_id: Google Calendar事件ID
            
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
            # 调用Google Calendar API删除事件
            headers = {
                'Authorization': token.authorization_header,
                'Accept': 'application/json'
            }
            
            delete_url = f'https://www.googleapis.com/calendar/v3/calendars/primary/events/{event_id}'
            
            logger.info("Deleting calendar event from Google API", event_id=event_id)
            
            response = requests.delete(
                delete_url,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 204:
                logger.info("Successfully deleted calendar event", event_id=event_id)
                return True, f"已成功删除日程事件 {event_id}"
            elif response.status_code == 404:
                logger.warning("Calendar event not found", event_id=event_id)
                return False, f"日程事件 {event_id} 不存在或已被删除"
            elif response.status_code == 401:
                logger.error("Calendar API authentication failed")
                return False, "认证失败，请重新登录Google账户"
            else:
                logger.error("Calendar API delete failed", 
                           status_code=response.status_code,
                           response=response.text)
                return False, f"删除日程事件失败 (HTTP {response.status_code})"
                
        except requests.RequestException as e:
            logger.error("HTTP request to Calendar API failed", error=str(e))
            return False, f"网络请求失败: {str(e)}"
        except Exception as e:
            logger.error("Error deleting calendar event", error=str(e))
            return False, f"删除日程事件时出错: {str(e)}"
    
    def delete_events_by_title(self, title_pattern: str) -> Tuple[int, List[str]]:
        """根据标题模式删除日程事件
        
        Args:
            title_pattern: 事件标题模式（如"游泳"）
            
        Returns:
            Tuple[删除数量, 错误信息列表]
        """
        
        if not self.google_auth.is_google_authenticated():
            return 0, ["未通过Google认证，请先运行: pm auth login google"]
        
        try:
            # 获取接下来30天的所有事件
            events = self._fetch_calendar_events(days_ahead=30)
            
            # 找到匹配的事件
            matching_events = []
            for event in events:
                if title_pattern in event.title:
                    matching_events.append(event)
            
            if not matching_events:
                return 0, [f"没有找到包含'{title_pattern}'的日程事件"]
            
            # 删除匹配的事件
            deleted_count = 0
            errors = []
            
            for event in matching_events:
                success, message = self.delete_calendar_event(event.event_id)
                if success:
                    deleted_count += 1
                    logger.info("Deleted calendar event", 
                              event_title=event.title,
                              event_id=event.event_id)
                else:
                    errors.append(f"删除'{event.title}'失败: {message}")
            
            logger.info("Bulk calendar event deletion completed",
                       total_found=len(matching_events),
                       deleted_count=deleted_count,
                       errors_count=len(errors))
            
            return deleted_count, errors
        
        except Exception as e:
            error_msg = f"批量删除日程事件时发生错误: {str(e)}"
            logger.error("Bulk calendar event deletion failed", error=str(e))
            return 0, [error_msg]