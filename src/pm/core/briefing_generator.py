"""双向简报生成系统 - PersonalManager自进化核心组件

生成用户工作简报和Claude技术简报，建立共同对话语境
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import structlog

from pm.core.config import PMConfig
from pm.core.function_registry import FunctionRegistry
from pm.integrations.gmail_processor import GmailProcessor
from pm.agents.gtd_agent import GTDAgent
from pm.storage.daily_task_tracker import DailyTaskTracker, DailyTaskRecord
from pm.core.briefing_session_integration import BriefingSessionIntegration

logger = structlog.get_logger()


class BriefingGenerator:
    """双向简报生成器 - 为用户和Claude生成个性化简报"""

    def __init__(self, config: PMConfig):
        self.config = config
        self.session_dir = Path.home() / ".personalmanager" / "session"
        self.user_briefing_file = self.session_dir / "user_briefing.md"
        self.claude_context_file = self.session_dir / "claude_context.json"
        self.session_state_file = self.session_dir / "session_state.json"
        self.ai_recommendations_file = self.session_dir / "ai_recommendations.json"

        # 初始化核心组件
        self.function_registry = FunctionRegistry(config)
        self.gmail_processor = GmailProcessor(config)
        self.gtd_agent = GTDAgent(config)
        self.task_tracker = DailyTaskTracker()

        # 初始化Session统计集成（可选，失败时不影响主功能）
        try:
            self.session_integration = BriefingSessionIntegration(config)
        except Exception as e:
            logger.warning("Session integration not available", error=str(e))
            self.session_integration = None

        # 存储最后生成的AI建议
        self.last_ai_recommendations = []

    def generate_dual_briefing(self, force_refresh: bool = False) -> Tuple[str, Dict[str, Any]]:
        """生成双向简报：用户工作简报 + Claude技术简报"""

        logger.info("Starting dual briefing generation", force_refresh=force_refresh)

        # 确保session目录存在
        self.session_dir.mkdir(parents=True, exist_ok=True)

        try:
            # 收集当前状态数据
            briefing_data = self._collect_briefing_data(force_refresh)

            # 生成用户工作简报
            user_briefing = self._generate_user_briefing(briefing_data)

            # 生成Claude技术简报
            claude_context = self._generate_claude_context(briefing_data)

            # 保存简报文件
            self._save_briefings(user_briefing, claude_context)

            # 更新会话状态
            self._update_session_state(briefing_data)

            logger.info("Dual briefing generation completed successfully")
            return user_briefing, claude_context

        except Exception as e:
            logger.error("Failed to generate dual briefing", error=str(e))
            raise

    def generate_json_briefing(self, force_refresh: bool = False) -> Dict[str, Any]:
        """生成JSON格式简报数据"""

        logger.info("Starting JSON briefing generation", force_refresh=force_refresh)

        try:
            # 收集简报数据
            briefing_data = self._collect_briefing_data(force_refresh)

            # 构建JSON输出结构
            json_briefing = {
                "timestamp": briefing_data["timestamp"].isoformat(),
                "date": briefing_data["date_str"],
                "time": briefing_data["time_str"],
                "tasks": self._format_tasks_for_json(briefing_data.get("tasks", {})),
                "overdue_tasks": self._format_overdue_tasks_for_json(briefing_data.get("overdue_tasks", [])),
                "emails": self._format_emails_for_json(briefing_data.get("emails", {})),
                "projects": self._format_projects_for_json(briefing_data.get("projects", {})),
                "summary": {
                    "total_items": 0,
                    "categories": {}
                }
            }

            # Add AI recommendations with execute handles
            ai_recommendations = self._generate_ai_recommendations(briefing_data)
            json_briefing["ai_recommendations"] = ai_recommendations

            # Calculate summary statistics
            all_items = json_briefing["tasks"] + json_briefing["overdue_tasks"] + json_briefing["emails"] + json_briefing["projects"]
            json_briefing["summary"]["total_items"] = len(all_items)

            # Count items by category
            for item in all_items:
                category = item.get("category", "unknown")
                json_briefing["summary"]["categories"][category] = json_briefing["summary"]["categories"].get(category, 0) + 1

            logger.info("JSON briefing generation completed successfully")
            return json_briefing

        except Exception as e:
            logger.error("Failed to generate JSON briefing", error=str(e))
            # Return minimal fallback data
            return {
                "timestamp": datetime.now().isoformat(),
                "date": datetime.now().strftime("%Y-%m-%d"),
                "time": datetime.now().strftime("%H:%M"),
                "error": str(e),
                "tasks": [],
                "overdue_tasks": [],
                "emails": [],
                "projects": [],
                "system_status": {},
                "capabilities": {},
                "session_statistics": {}
            }

    def _format_tasks_for_json(self, tasks_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """格式化任务数据为JSON格式"""
        formatted_tasks = []

        if not tasks_data:
            return formatted_tasks

        # 处理各个任务列表
        task_lists = [
            ("inbox", tasks_data.get("inbox_tasks", [])),
            ("next_actions", tasks_data.get("next_actions", [])),
            ("waiting_for", tasks_data.get("waiting_for", [])),
            ("someday_maybe", tasks_data.get("someday_maybe", [])),
            ("today_habits", tasks_data.get("today_habits", []))
        ]

        index = 1
        for category, task_list in task_lists:
            for task in task_list:
                # Safely extract attributes
                task_id = task.id if hasattr(task, 'id') else f"{category}_{index}"

                # Handle title properly - if it's a string, use it directly
                if isinstance(task, str):
                    title = task
                elif hasattr(task, 'title') and not callable(task.title):
                    title = task.title
                else:
                    title = str(task)

                due_date = task.due_date if hasattr(task, 'due_date') else None
                priority = task.priority.value if hasattr(task, 'priority') and task.priority else None
                context = task.context.value if hasattr(task, 'context') and task.context else None
                project = task.project_name if hasattr(task, 'project_name') else None

                formatted_task = {
                    "index": index,
                    "task_id": str(task_id),
                    "title": str(title),
                    "category": category,
                    "due_date": due_date,
                    "priority": priority,
                    "context": context,
                    "project": project
                }
                # Convert dates to strings if they exist
                if formatted_task["due_date"]:
                    try:
                        if hasattr(formatted_task["due_date"], 'isoformat'):
                            formatted_task["due_date"] = formatted_task["due_date"].isoformat()
                        else:
                            formatted_task["due_date"] = str(formatted_task["due_date"])
                    except:
                        formatted_task["due_date"] = None

                formatted_tasks.append(formatted_task)
                index += 1

        return formatted_tasks

    def _format_overdue_tasks_for_json(self, overdue_tasks: List[Any]) -> List[Dict[str, Any]]:
        """格式化过期任务数据为JSON格式"""
        formatted_tasks = []

        for i, task in enumerate(overdue_tasks):
            # Safely extract attributes
            task_id = task.id if hasattr(task, 'id') else f"overdue_{i+1}"

            # Handle title properly - if it's a string, use it directly
            if isinstance(task, str):
                title = task
            elif hasattr(task, 'title') and not callable(task.title):
                title = task.title
            else:
                title = str(task)

            due_date = task.due_date if hasattr(task, 'due_date') else None
            priority = task.priority.value if hasattr(task, 'priority') and task.priority else None
            days_overdue = task.days_overdue if hasattr(task, 'days_overdue') else None

            formatted_task = {
                "index": i + 1,
                "task_id": str(task_id),
                "title": str(title),
                "category": "overdue",
                "due_date": due_date,
                "priority": priority,
                "days_overdue": days_overdue
            }

            # Convert dates to strings if they exist
            if formatted_task["due_date"]:
                try:
                    if hasattr(formatted_task["due_date"], 'isoformat'):
                        formatted_task["due_date"] = formatted_task["due_date"].isoformat()
                    else:
                        formatted_task["due_date"] = str(formatted_task["due_date"])
                except:
                    formatted_task["due_date"] = None

            formatted_tasks.append(formatted_task)

        return formatted_tasks

    def _format_emails_for_json(self, emails_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """格式化邮件数据为JSON格式"""
        formatted_emails = []

        if not emails_data:
            return formatted_emails

        recent_emails = emails_data.get("recent_emails", [])
        for i, email in enumerate(recent_emails):
            formatted_email = {
                "index": i + 1,
                "task_id": f"email_{i+1}",
                "title": f"Email: {getattr(email, 'subject', 'No Subject')}",
                "category": "email",
                "sender": getattr(email, 'sender', ''),
                "subject": getattr(email, 'subject', ''),
                "date": getattr(email, 'date', None),
                "is_unread": getattr(email, 'is_unread', False)
            }

            # Convert dates to strings if they exist
            if formatted_email["date"]:
                try:
                    if hasattr(formatted_email["date"], 'isoformat'):
                        formatted_email["date"] = formatted_email["date"].isoformat()
                    else:
                        formatted_email["date"] = str(formatted_email["date"])
                except:
                    formatted_email["date"] = None

            formatted_emails.append(formatted_email)

        return formatted_emails

    def _format_projects_for_json(self, projects_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """格式化项目数据为JSON格式"""
        formatted_projects = []

        if not projects_data:
            return formatted_projects

        active_projects = projects_data.get("active_projects", [])
        for i, project in enumerate(active_projects):
            formatted_project = {
                "index": i + 1,
                "task_id": f"project_{i+1}",
                "title": f"Project: {getattr(project, 'name', 'Unnamed Project')}",
                "category": "project",
                "name": getattr(project, 'name', ''),
                "status": getattr(project, 'status', ''),
                "description": getattr(project, 'description', ''),
                "created_date": getattr(project, 'created_date', None)
            }

            # Convert dates to strings if they exist
            if formatted_project["created_date"]:
                try:
                    if hasattr(formatted_project["created_date"], 'isoformat'):
                        formatted_project["created_date"] = formatted_project["created_date"].isoformat()
                    else:
                        formatted_project["created_date"] = str(formatted_project["created_date"])
                except:
                    formatted_project["created_date"] = None

            formatted_projects.append(formatted_project)

        return formatted_projects

    def _sanitize_for_json(self, data: Any) -> Any:
        """递归清理数据使其可以JSON序列化"""
        import types

        if isinstance(data, dict):
            return {k: self._sanitize_for_json(v) for k, v in data.items() if not callable(v) and not isinstance(v, types.BuiltinFunctionType)}
        elif isinstance(data, list):
            return [self._sanitize_for_json(item) for item in data if not callable(item) and not isinstance(item, types.BuiltinFunctionType)]
        elif isinstance(data, (str, int, float, bool)) or data is None:
            return data
        elif callable(data) or isinstance(data, types.BuiltinFunctionType):
            return None  # Skip functions and methods
        elif hasattr(data, 'isoformat'):  # datetime objects
            try:
                return data.isoformat()
            except:
                return str(data)
        elif hasattr(data, '__dict__'):  # complex objects
            try:
                return self._sanitize_for_json(data.__dict__)
            except:
                return str(data)
        else:
            return str(data)  # fallback to string representation

    def _collect_briefing_data(self, force_refresh: bool = False) -> Dict[str, Any]:
        """收集简报所需的所有数据"""

        logger.info("Collecting briefing data")

        data = {
            "timestamp": datetime.now(),
            "date_str": datetime.now().strftime("%Y-%m-%d"),
            "time_str": datetime.now().strftime("%H:%M")
        }

        try:
            # 1. 任务数据（包含过期任务）
            data["tasks"] = self._collect_task_data()

            # 2. 过期任务专项收集
            data["overdue_tasks"] = self._collect_overdue_tasks()

            # 3. 习惯数据
            data["habits"] = self._collect_habits_data()

            # 4. 邮件数据
            data["emails"] = self._collect_email_data()

            # 5. 项目数据
            data["projects"] = self._collect_project_data()

            # 6. 系统状态
            data["system_status"] = self._collect_system_status()

            # 7. 功能注册表
            data["capabilities"] = self._collect_capabilities_data(force_refresh)

            # 8. 开发历史
            data["development_history"] = self._collect_development_history()

            # 9. Session统计数据（可选）
            data["session_statistics"] = self._collect_session_statistics()

        except Exception as e:
            logger.error("Error collecting briefing data", error=str(e))
            # 使用默认数据继续
            data.update(self._get_fallback_data())

        return data

    def _collect_task_data(self) -> Dict[str, Any]:
        """收集任务数据（包含未完成任务追踪）"""

        try:
            # 确保今天的任务文件存在（包括习惯任务）
            self.task_tracker.ensure_today_tasks()
            logger.info("Ensured today's tasks file exists")

            all_tasks = self.gtd_agent.storage.get_all_tasks()

            # 按状态分类
            inbox_tasks = [t for t in all_tasks if t.status.value == "inbox"]
            next_action_tasks = [t for t in all_tasks if t.status.value == "next_action"]
            project_tasks = [t for t in all_tasks if t.status.value == "project"]
            completed_tasks = [t for t in all_tasks if t.status.value == "completed"]

            # 按优先级分类
            high_priority = [t for t in all_tasks if t.priority.value == "high"]
            medium_priority = [t for t in all_tasks if t.priority.value == "medium"]

            # 今日相关任务
            today = datetime.now().date()
            due_today = [t for t in all_tasks if t.due_date and t.due_date.date() == today]
            overdue = [t for t in all_tasks if t.due_date and t.due_date.date() < today and t.status.value != "completed"]

            # 获取昨日未完成任务
            yesterday = (today - timedelta(days=1)).isoformat()
            yesterday_incomplete = self.task_tracker.get_incomplete_tasks(yesterday)

            # 获取需要延续的任务
            carried_over_tasks = self.task_tracker.get_carried_over_tasks(
                yesterday,
                today.isoformat()
            )

            # 获取今日任务摘要
            today_summary = self.task_tracker.get_task_summary(today.isoformat())

            return {
                "total_tasks": len(all_tasks),
                "inbox_count": len(inbox_tasks),
                "next_action_count": len(next_action_tasks),
                "project_count": len(project_tasks),
                "completed_count": len(completed_tasks),
                "high_priority_count": len(high_priority),
                "medium_priority_count": len(medium_priority),
                "due_today_count": len(due_today),
                "overdue_count": len(overdue),
                "high_priority_tasks": [self._task_to_dict(t) for t in high_priority[:20]],  # 增加到20个
                "due_today_tasks": [self._task_to_dict(t) for t in due_today],
                "overdue_tasks": [self._task_to_dict(t) for t in overdue],  # 显示所有逾期任务
                "inbox_tasks": [self._task_to_dict(t) for t in inbox_tasks[:30]],  # 增加到30个
                "next_action_tasks": [self._task_to_dict(t) for t in next_action_tasks[:20]],  # 增加到20个
                # 新增：昨日未完成和延续任务
                "yesterday_incomplete": yesterday_incomplete,
                "carried_over_tasks": carried_over_tasks,
                "today_summary": today_summary
            }

        except Exception as e:
            logger.error("Error collecting task data", error=str(e))
            return self._get_fallback_task_data()

    def _collect_overdue_tasks(self) -> Dict[str, Any]:
        """收集过期任务数据"""

        try:
            from datetime import date
            today = date.today()
            all_tasks = self.gtd_agent.storage.get_all_tasks()

            overdue_tasks = []
            for task in all_tasks:
                if task.status.value != "completed" and task.due_date:
                    task_date = task.due_date.date() if hasattr(task.due_date, 'date') else task.due_date
                    if task_date < today:
                        # 排除习惯任务（它们会自动重置）
                        if not (task.title.startswith('🎯') or 'category:habit' in task.tags):
                            days_overdue = (today - task_date).days
                            overdue_tasks.append({
                                "id": task.id,
                                "title": task.title,
                                "due_date": str(task_date),
                                "days_overdue": days_overdue,
                                "priority": task.priority,
                                "context": task.context.value if task.context else None
                            })

            # 按过期天数排序
            overdue_tasks.sort(key=lambda x: x['days_overdue'], reverse=True)

            return {
                "count": len(overdue_tasks),
                "tasks": overdue_tasks[:10],  # 只显示前10个最过期的
                "needs_attention": len(overdue_tasks) > 0
            }

        except Exception as e:
            logger.error("Error collecting overdue tasks", error=str(e))
            return {"count": 0, "tasks": [], "needs_attention": False}

    def _collect_habits_data(self) -> Dict[str, Any]:
        """收集习惯数据"""
        try:
            habits_file = Path.home() / ".personalmanager" / "data" / "habits" / "habits.json"
            if habits_file.exists():
                with open(habits_file, 'r', encoding='utf-8') as f:
                    habits_data = json.load(f)
                    active_habits = [h for h in habits_data.get('habits', []) if h.get('active', True)]
                    return {
                        "count": len(active_habits),
                        "habits": active_habits,
                        "has_habits": len(active_habits) > 0
                    }
            return {"count": 0, "habits": [], "has_habits": False}
        except Exception as e:
            logger.error("Error collecting habits data", error=str(e))
            return {"count": 0, "habits": [], "has_habits": False}

    def _collect_email_data(self) -> Dict[str, Any]:
        """收集邮件数据"""

        try:
            # 检查认证状态
            if not self.gmail_processor.google_auth.is_google_authenticated():
                return {
                    "authenticated": False,
                    "message": "Gmail未认证，请运行 pm auth login google"
                }

            # 获取最近邮件摘要
            important_emails, errors = self.gmail_processor.scan_important_emails(
                days_back=1, max_emails=10
            )

            # 统计邮件任务
            all_tasks = self.gtd_agent.storage.get_all_tasks()
            email_tasks = [t for t in all_tasks if t.source == "gmail"]

            return {
                "authenticated": True,
                "recent_important_count": len(important_emails),
                "email_tasks_count": len(email_tasks),
                "scan_errors": len(errors),
                "recent_emails_summary": [
                    {
                        "subject": email.subject[:100] + "..." if len(email.subject) > 100 else email.subject,
                        "sender": email.sender_name,
                        "sender_email": email.sender_email,
                        "snippet": email.snippet[:200] + "..." if len(email.snippet) > 200 else email.snippet,  # 添加邮件摘要
                        "importance_score": email.importance_score,
                        "is_urgent": email.is_urgent,
                        "is_important": email.is_important,
                        "received_date": email.date.strftime("%Y-%m-%d %H:%M") if email.date else "Unknown"
                    }
                    for email in important_emails[:10]  # 增加到10封邮件
                ]
            }

        except Exception as e:
            logger.error("Error collecting email data", error=str(e))
            return {
                "authenticated": False,
                "error": str(e),
                "message": "邮件数据收集失败"
            }

    def _collect_project_data(self) -> Dict[str, Any]:
        """收集项目数据"""

        try:
            # 这里可以扩展项目管理功能
            # 现在从任务中推断项目状态
            all_tasks = self.gtd_agent.storage.get_all_tasks()

            # 按上下文分组任务
            context_groups = {}
            for task in all_tasks:
                context = task.context.value if task.context else "other"
                if context not in context_groups:
                    context_groups[context] = []
                context_groups[context].append(task)

            return {
                "context_distribution": {
                    context: len(tasks) for context, tasks in context_groups.items()
                },
                "active_contexts": list(context_groups.keys()),
                "total_contexts": len(context_groups)
            }

        except Exception as e:
            logger.error("Error collecting project data", error=str(e))
            return {"error": str(e)}

    def _collect_system_status(self) -> Dict[str, Any]:
        """收集系统状态"""

        try:
            # 检查各种集成状态
            gmail_auth = self.gmail_processor.google_auth.is_google_authenticated()

            # 检查数据目录
            data_dir = self.config.data_dir
            tasks_dir = data_dir / "tasks"

            return {
                "gmail_authenticated": gmail_auth,
                "data_directory_exists": data_dir.exists(),
                "tasks_directory_exists": tasks_dir.exists(),
                "config_initialized": self.config.is_initialized(),
                "last_check": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error("Error collecting system status", error=str(e))
            return {"error": str(e)}

    def _collect_capabilities_data(self, force_refresh: bool = False) -> Dict[str, Any]:
        """收集功能能力数据"""

        try:
            # 检查是否需要更新功能注册表
            registry = self.function_registry.load_registry()

            if force_refresh or not registry or self._should_refresh_capabilities(registry):
                logger.info("Refreshing capabilities registry")
                registry = self.function_registry.discover_all_capabilities()

            return {
                "capabilities_summary": self.function_registry.get_capability_summary(),
                "full_registry": registry
            }

        except Exception as e:
            logger.error("Error collecting capabilities data", error=str(e))
            return {"error": str(e)}

    def _collect_development_history(self) -> Dict[str, Any]:
        """收集开发历史（简化版）"""

        try:
            # 这里可以集成Git历史分析
            # 现在返回基本信息
            return {
                "last_update": datetime.now().isoformat(),
                "version": "development",
                "recent_features": [
                    "Final repository cleanup: Organize all documentation",
                    "Clean up repository structure and organize documentation",
                    "Documentation update: Project localization and simplified installation"
                ]
            }

        except Exception as e:
            logger.error("Error collecting development history", error=str(e))
            return {"error": str(e)}

    def _collect_session_statistics(self) -> Dict[str, Any]:
        """收集Session统计数据"""

        try:
            if not self.session_integration or not self.session_integration.is_integration_enabled():
                return {
                    "enabled": False,
                    "message": "Session统计功能未启用或无数据"
                }

            # 收集昨日概览数据 (AC-3.1)
            yesterday_overview = self.session_integration.get_yesterday_time_overview()
            
            # 收集本周进展数据 (AC-3.2)
            week_progress = self.session_integration.get_week_project_progress()
            
            # 收集预算预警数据 (AC-3.3)
            budget_warnings = self.session_integration.get_budget_warnings()
            
            # 收集活跃session信息
            active_session = self.session_integration.get_active_session_info()
            
            # 收集工作建议
            recommendations = self.session_integration.get_session_recommendations()

            return {
                "enabled": True,
                "yesterday_overview": yesterday_overview,
                "week_progress": week_progress,
                "budget_warnings": budget_warnings,
                "active_session": active_session,
                "recommendations": recommendations,
                "integration_config": {
                    "detail_level": self.session_integration.integration_config.detail_level,
                    "show_charts": self.session_integration.integration_config.show_charts,
                    "show_yesterday": self.session_integration.integration_config.show_yesterday,
                    "show_week_progress": self.session_integration.integration_config.show_week_progress,
                    "show_budget_warnings": self.session_integration.integration_config.show_budget_warnings
                }
            }

        except Exception as e:
            logger.error("Error collecting session statistics", error=str(e))
            return {
                "enabled": False,
                "error": str(e),
                "message": "Session统计数据收集失败"
            }

    def _should_refresh_capabilities(self, registry: Dict[str, Any]) -> bool:
        """检查是否需要刷新功能注册表"""

        try:
            # 检查上次更新时间
            last_update = datetime.fromisoformat(registry.get("discovery_timestamp", "2000-01-01"))
            hours_since_update = (datetime.now() - last_update).total_seconds() / 3600

            # 如果超过6小时，刷新注册表
            return hours_since_update > 6

        except Exception:
            return True

    def _generate_user_briefing(self, data: Dict[str, Any]) -> str:
        """生成用户工作简报"""

        # 构建Markdown格式的用户简报
        briefing_lines = []

        # 标题
        briefing_lines.extend([
            f"# 📊 PersonalManager 工作简报",
            f"**日期**: {data['date_str']} {data['time_str']}",
            "",
            "---",
            ""
        ])

        # 今日重点任务
        task_data = data.get("tasks", {})
        briefing_lines.extend([
            "## 🎯 今日重点",
            ""
        ])

        # 昨日未完成任务提醒
        yesterday_incomplete = task_data.get("yesterday_incomplete", [])
        if yesterday_incomplete:
            briefing_lines.append("### ⚠️ 昨日未完成任务（需要处理）")
            briefing_lines.append("")
            for task in yesterday_incomplete:
                if hasattr(task, 'category'):
                    if task.category == "event":
                        briefing_lines.append(f"- **📅 [日程] {task.title}**")
                    elif task.category == "habit":
                        briefing_lines.append(f"- **🎯 [习惯] {task.title}**")
                    else:
                        briefing_lines.append(f"- **📝 [任务] {task.title}**")
                    if hasattr(task, 'carried_over_from') and task.carried_over_from:
                        briefing_lines.append(f"  - 延续自: {task.carried_over_from}")
            briefing_lines.append("")
            briefing_lines.append("💡 **提醒**: 这些任务昨天未完成，是否需要今天继续？")
            briefing_lines.append("")

        # 延续任务
        carried_over = task_data.get("carried_over_tasks", [])
        if carried_over:
            briefing_lines.append("### 📌 延续任务（自动转入今日）")
            briefing_lines.append("")
            for task in carried_over:
                if hasattr(task, 'title'):
                    briefing_lines.append(f"- **{task.title}**")
                    if hasattr(task, 'due_date') and task.due_date:
                        briefing_lines.append(f"  - 原截止时间: {task.due_date}")
            briefing_lines.append("")

        # 逾期任务 - 使用新的overdue_tasks数据
        overdue_data = data.get("overdue_tasks", {})
        if overdue_data.get("needs_attention") and overdue_data.get("tasks"):
            briefing_lines.append(f"### 🚨 逾期任务提醒 ({overdue_data['count']} 个需要处理)")
            briefing_lines.append("")
            briefing_lines.append("**以下任务已过期，请立即处理或重新安排：**")
            briefing_lines.append("")

            for task in overdue_data["tasks"][:5]:  # 只显示前5个最紧急的
                days_overdue = task.get('days_overdue', 0)
                due_date = task.get('due_date', '未知')
                context = task.get('context', '').replace('@', '') if task.get('context') else '一般'
                priority = task.get('priority', 'medium')

                # 根据过期天数调整紧急程度标记
                if days_overdue > 7:
                    urgency = "🔴"  # 严重过期
                elif days_overdue > 3:
                    urgency = "🟠"  # 中度过期
                else:
                    urgency = "🟡"  # 轻度过期

                briefing_lines.append(f"- {urgency} **{task['title']}**")
                briefing_lines.append(f"  - 原定日期: {due_date} (已过期 **{days_overdue}** 天)")
                briefing_lines.append(f"  - 优先级: {priority} | 场景: {context}")
                briefing_lines.append("")

            if overdue_data['count'] > 5:
                briefing_lines.append(f"  ... 还有 {overdue_data['count'] - 5} 个过期任务")
                briefing_lines.append("")

            briefing_lines.append("💡 **建议操作**：")
            briefing_lines.append("- 运行 `pm today` 查看和处理所有过期任务")
            briefing_lines.append("- 运行 `pm postpone <任务ID> <新日期>` 推迟任务")
            briefing_lines.append("")

        # 每日习惯
        habits_data = data.get("habits", {})
        if habits_data.get("has_habits") and habits_data.get("habits"):
            briefing_lines.append("### 🎯 每日习惯")
            briefing_lines.append("")
            for habit in habits_data["habits"]:
                reminder_time = habit.get('reminder_time', '未设置')
                briefing_lines.append(f"- **{habit['name']}** - {reminder_time}")
                if habit.get('description'):
                    briefing_lines.append(f"  - {habit['description']}")
            briefing_lines.append("")

        # 今日截止任务
        if task_data.get("due_today_tasks"):
            briefing_lines.append("### 📅 今日必须完成")
            for task in task_data["due_today_tasks"]:
                context = task.get('context', '').replace('@', '') if task.get('context') else '一般'
                briefing_lines.append(f"- **{task['title']}** (场景: {context})")
            briefing_lines.append("")

        # 高优先级任务
        if task_data.get("high_priority_tasks"):
            briefing_lines.append("### ⚡ 高优先级任务")
            for task in task_data["high_priority_tasks"]:
                due_info = f" | 截止: {task.get('due_date', '无截止')}" if task.get("due_date") else ""
                context = task.get('context', '').replace('@', '') if task.get('context') else '一般'
                briefing_lines.append(f"- **{task['title']}** (场景: {context}{due_info})")
            briefing_lines.append("")

        # 收件箱任务详情 - 用户最需要知道的
        if task_data.get("inbox_tasks"):
            briefing_lines.extend([
                "## 📥 收件箱任务（需要澄清和分类）",
                ""
            ])

            # 按类型和重要性分析任务
            categorized_tasks = self._categorize_inbox_tasks(task_data["inbox_tasks"])

            # 显示分类后的任务
            for category, tasks in categorized_tasks.items():
                if tasks:
                    briefing_lines.append(f"### {category}")
                    for i, task in enumerate(tasks[:8], 1):  # 每类最多8个
                        task_line = f"{i}. **{task['title']}**"
                        # 添加更多上下文信息
                        details = []
                        if task.get('due_date'):
                            details.append(f"截止: {task['due_date']}")
                        if task.get('context') and task['context'] != '@其他':
                            details.append(f"场景: {task['context'].replace('@', '')}")
                        if task.get('priority') and task['priority'] != 'medium':
                            details.append(f"优先级: {task['priority']}")

                        if details:
                            task_line += f" ({' | '.join(details)})"
                        briefing_lines.append(task_line)

                    if len(tasks) > 8:
                        briefing_lines.append(f"   ... 还有 {len(tasks) - 8} 个{category.split()[1]}任务")
                    briefing_lines.append("")

            remaining = task_data.get('inbox_count', 0) - len(task_data["inbox_tasks"])
            if remaining > 0:
                briefing_lines.append(f"📊 **统计**: 总共 {task_data.get('inbox_count', 0)} 个收件箱任务，上述显示前 {len(task_data['inbox_tasks'])} 个")

            briefing_lines.extend([
                "",
                "💡 **处理策略**: ",
                "- 🔥 优先处理测试和学习类任务（可快速完成）",
                "- ⚡ 技术集成任务可批量处理",
                "- 🧹 清理无意义的测试数据",
                ""
            ])

        # 下一步行动（可执行的任务）
        if task_data.get("next_action_count", 0) > 0:
            briefing_lines.extend([
                "## ✅ 下一步行动（可立即执行）",
                f"共 {task_data.get('next_action_count', 0)} 个已分类的可执行任务",
                "",
                "💡 **建议**: 运行 `pm next` 查看按场景分组的行动清单",
                ""
            ])

        # 邮件处理状态
        email_data = data.get("emails", {})
        if email_data.get("authenticated") and email_data.get("recent_emails_summary"):
            briefing_lines.extend([
                "## 📧 重要邮件",
                ""
            ])
            for email in email_data["recent_emails_summary"]:
                urgency = "🚨 紧急" if email["is_urgent"] else "⚡ 重要" if email["is_important"] else "📧 一般"
                briefing_lines.append(f"- {urgency}: **{email['subject']}**")
                briefing_lines.append(f"  - 发件人: {email['sender']} <{email.get('sender_email', '')}>")
                briefing_lines.append(f"  - 时间: {email.get('received_date', 'Unknown')}")
                if email.get('snippet'):
                    briefing_lines.append(f"  - 摘要: {email['snippet']}")
                briefing_lines.append("")
            briefing_lines.append("💡 **建议**: 运行 `pm gmail scan` 将重要邮件转换为任务")
            briefing_lines.append("")
        elif not email_data.get("authenticated"):
            briefing_lines.extend([
                "## 📧 邮件集成",
                "- ❌ Gmail未认证，无法自动处理邮件",
                "- 💡 **建议**: 运行 `pm auth login google` 启用邮件智能处理",
                ""
            ])

        # Session统计集成部分 (AC-3.1, AC-3.2, AC-3.3)
        session_data = data.get("session_statistics", {})
        if session_data.get("enabled"):
            session_section = self._generate_session_statistics_section(session_data)
            if session_section:
                briefing_lines.append(session_section)

        # 智能工作建议 - 基于当前状态的具体行动指导
        briefing_lines.extend([
            "## 🎯 智能工作建议（可执行）",
            ""
        ])

        # 生成带执行手柄的AI建议
        ai_recommendations = self._generate_ai_recommendations(data)

        # 保存建议到实例变量，供执行时使用
        self.last_ai_recommendations = ai_recommendations

        # 显示建议
        for i, rec in enumerate(ai_recommendations[:8], 1):  # 显示前8个建议
            priority_emoji = "🔴" if rec['priority'] >= 5 else "🟠" if rec['priority'] >= 4 else "🟡" if rec['priority'] >= 3 else "🟢"
            briefing_lines.append(
                f"**{i}. {priority_emoji} {rec['title']}** - {rec['description']} "
                f"[Execute: `{rec['execute_handle']}`]"
            )

        briefing_lines.extend([
            "",
            "💡 **使用方法**:",
            "- 直接运行命令: 复制 [Execute: ...] 中的命令运行",
            "- 快速执行: `pm ai execute <编号>` (如 `pm ai execute 1`)",
            "- 批量执行: `pm ai execute 1,3,5` 或 `pm ai execute 1-3`",
            "",
            "## ⏱️ 时间估算和效率建议",
            ""
        ])

        # 添加时间估算信息
        time_estimates = []
        if task_data.get("overdue_count", 0) > 0:
            time_estimates.append("🚨 逾期任务: 优先处理，预计15-30分钟")

        if task_data.get("inbox_count", 0) > 0:
            test_tasks = len([t for t in task_data.get("inbox_tasks", []) if any(k in t.get('title', '').lower() for k in ['test', '测试'])])
            if test_tasks > 0:
                time_estimates.append(f"🔥 测试类任务: {test_tasks}个，预计每个2-5分钟")

            cleanup_tasks = len([t for t in task_data.get("inbox_tasks", []) if 'aaa' in t.get('title', '').lower()])
            if cleanup_tasks > 0:
                time_estimates.append(f"🧹 清理任务: {cleanup_tasks}个，可批量删除（5分钟）")

        if task_data.get("next_action_count", 0) > 0:
            time_estimates.append(f"⚡ 下一步行动: {task_data['next_action_count']}个，已分类可直接执行")

        for estimate in time_estimates:
            briefing_lines.append(f"- {estimate}")

        briefing_lines.extend([
            "",
            "## 🎯 推荐执行顺序",
            ""
        ])

        # 智能推荐执行顺序
        if task_data.get("overdue_count", 0) > 0:
            briefing_lines.append("**最优路径**: 1 → 3 → 2 → 4 (逾期→清理→收件箱→行动)")
        else:
            briefing_lines.append("**最优路径**: 3 → 2 → 4 (快速清理→收件箱→可执行任务)")

        briefing_lines.extend([
            "",
            "---",
            f"*📊 简报时间: {data['time_str']} | 🔄 更新: `pm briefing` | 💬 选择: 回复编号*"
        ])

        return "\n".join(briefing_lines)

    def _generate_claude_context(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """生成Claude技术简报"""

        capabilities_data = data.get("capabilities", {})
        task_data = data.get("tasks", {})
        email_data = data.get("emails", {})
        system_data = data.get("system_status", {})

        context = {
            "briefing_timestamp": data["timestamp"].isoformat(),
            "identity": {
                "role": "PersonalManager AI Assistant",
                "description": "专门帮助用户进行GTD任务管理、邮件处理和项目协调的AI助手",
                "capabilities": "邮件智能处理、任务管理、项目协调、自动化工作流程"
            },
            "system_status": {
                "gmail_authenticated": system_data.get("gmail_authenticated", False),
                "config_initialized": system_data.get("config_initialized", False),
                "data_ready": system_data.get("tasks_directory_exists", False)
            },
            "current_work_context": {
                "total_tasks": task_data.get("total_tasks", 0),
                "inbox_tasks": task_data.get("inbox_count", 0),
                "next_actions": task_data.get("next_action_count", 0),
                "high_priority_tasks": task_data.get("high_priority_count", 0),
                "overdue_tasks": task_data.get("overdue_count", 0),
                "recent_emails": email_data.get("recent_important_count", 0)
            },
            "available_functions": self._format_available_functions(capabilities_data),
            "collaboration_guidance": {
                "user_preferences": [
                    "偏好简洁高效的交互",
                    "关注学术截止日期管理",
                    "习惯手动转发重要邮件到Gmail",
                    "需要项目进展追踪"
                ],
                "priority_areas": [
                    "任务优先级管理",
                    "截止日期提醒",
                    "邮件智能处理",
                    "项目状态跟踪"
                ]
            },
            "today_focus": self._generate_today_focus(data),
            "development_context": data.get("development_history", {}),
            "session_recommendations": self._generate_session_recommendations(data),
            "session_insights": self._format_session_insights_for_claude(data.get("session_statistics", {}))
        }

        return context

    def _format_available_functions(self, capabilities_data: Dict[str, Any]) -> Dict[str, Any]:
        """格式化可用功能列表"""

        summary = capabilities_data.get("capabilities_summary", {})

        return {
            "cli_commands_count": summary.get("cli_commands", 0),
            "integrations_count": summary.get("integrations", 0),
            "api_methods_count": summary.get("api_methods", 0),
            "core_functions": {
                "gmail_integration": ["pm gmail scan", "pm gmail preview", "pm gmail stats"],
                "task_management": ["pm inbox", "pm clarify", "pm projects", "pm next"],
                "session_management": ["pm briefing", "pm start-session"],
                "auth_management": ["pm auth login", "pm auth status"]
            },
            "last_capability_update": summary.get("last_updated", "unknown")
        }

    def _generate_today_focus(self, data: Dict[str, Any]) -> List[str]:
        """生成今日重点关注事项"""

        focus_items = []
        task_data = data.get("tasks", {})
        email_data = data.get("emails", {})

        if task_data.get("overdue_count", 0) > 0:
            focus_items.append(f"处理 {task_data['overdue_count']} 个逾期任务")

        if task_data.get("due_today_count", 0) > 0:
            focus_items.append(f"完成 {task_data['due_today_count']} 个今日截止任务")

        if task_data.get("high_priority_count", 0) > 0:
            focus_items.append(f"推进 {task_data['high_priority_count']} 个高优先级任务")

        if email_data.get("recent_important_count", 0) > 0:
            focus_items.append(f"处理 {email_data['recent_important_count']} 封重要邮件")

        if task_data.get("inbox_count", 0) > 0:
            focus_items.append(f"澄清 {task_data['inbox_count']} 个收件箱任务")

        return focus_items

    def _generate_session_recommendations(self, data: Dict[str, Any]) -> List[str]:
        """生成会话建议"""

        recommendations = []
        task_data = data.get("tasks", {})
        email_data = data.get("emails", {})
        system_data = data.get("system_status", {})

        # 基于当前状态生成建议
        if not system_data.get("gmail_authenticated"):
            recommendations.append("建议首先运行 'pm auth login google' 启用邮件集成")

        if task_data.get("inbox_count", 0) > 0:
            recommendations.append("可以从处理收件箱任务开始：'pm clarify'")

        if task_data.get("overdue_count", 0) > 0:
            recommendations.append("优先处理逾期任务，避免进一步延误")

        if email_data.get("recent_important_count", 0) > 0:
            recommendations.append("检查重要邮件并转换为任务：'pm gmail scan'")

        return recommendations

    def _generate_ai_recommendations(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成带执行手柄的AI建议

        Returns:
            List of recommendation dicts with structure:
            {
                'title': str,           # 建议标题
                'description': str,     # 详细描述
                'execute_handle': str,  # 完整命令
                'tool': str,           # 工具名称
                'args': List[str],     # 命令参数
                'priority': int,       # 优先级 (1-5)
                'confidence': float,   # 置信度 (0-1)
                'locate': Dict[str, Any] # 位置信息，兼容now命令索引
            }
        """
        recommendations = []
        task_data = data.get("tasks", {})
        email_data = data.get("emails", {})
        overdue_data = data.get("overdue_tasks", {})
        system_data = data.get("system_status", {})

        # Get task service data for consistent indexing
        from pm.core.services import TaskService
        try:
            task_service = TaskService(self.config)
            service_result = task_service.get_next_actions(limit=20)
            now_tasks = service_result.get('tasks', [])
        except Exception:
            now_tasks = []

        # 1. 处理过期任务
        if overdue_data.get("needs_attention") and overdue_data.get("tasks"):
            recommendations.append({
                'title': '处理过期任务',
                'description': f"立即处理 {overdue_data['count']} 个过期任务，防止进一步延误",
                'execute_handle': 'pm today --overdue',
                'tool': 'today',
                'args': ['--overdue'],
                'priority': 5,
                'confidence': 0.95,
                'locate': {
                    'type': 'command',
                    'command': 'pm today --overdue',
                    'description': 'Show overdue tasks'
                }
            })

        # 2. 完成今日任务
        if task_data.get("due_today_count", 0) > 0:
            recommendations.append({
                'title': '完成今日截止任务',
                'description': f"处理 {task_data['due_today_count']} 个今日截止的任务",
                'execute_handle': 'pm today --due',
                'tool': 'today',
                'args': ['--due'],
                'priority': 4,
                'confidence': 0.9,
                'locate': {
                    'type': 'command',
                    'command': 'pm today --due',
                    'description': 'Show tasks due today'
                }
            })

        # 3. 清空收件箱
        if task_data.get("inbox_count", 0) > 0:
            inbox_count = task_data["inbox_count"]
            if inbox_count <= 5:
                recommendations.append({
                    'title': '快速清空收件箱',
                    'description': f"只有 {inbox_count} 个任务，预计20分钟完成",
                    'execute_handle': 'pm clarify',
                    'tool': 'clarify',
                    'args': [],
                    'priority': 3,
                    'confidence': 0.85,
                    'locate': {
                        'type': 'command',
                        'command': 'pm clarify',
                        'description': 'Quick inbox processing'
                    }
                })
            else:
                recommendations.append({
                    'title': '分批处理收件箱',
                    'description': f"处理 {inbox_count} 个收件箱任务，建议分批进行",
                    'execute_handle': 'pm clarify --batch 10',
                    'tool': 'clarify',
                    'args': ['--batch', '10'],
                    'priority': 3,
                    'confidence': 0.8,
                    'locate': {
                        'type': 'command',
                        'command': 'pm clarify --batch 10',
                        'description': 'Batch inbox processing'
                    }
                })

        # 4. 查看下一步行动
        if task_data.get("next_action_count", 0) > 0:
            # Find top priority next action tasks and include their indexes
            next_action_indices = []
            for idx, task in enumerate(now_tasks[:5], 1):  # Top 5 tasks
                if task.get('status') == 'needsAction':
                    next_action_indices.append({
                        'index': idx,
                        'task_id': task.get('id'),
                        'title': task.get('title', '')[:50]
                    })

            recommendations.append({
                'title': '执行下一步行动',
                'description': f"查看 {task_data['next_action_count']} 个可立即执行的任务",
                'execute_handle': 'pm next',
                'tool': 'next',
                'args': [],
                'priority': 3,
                'confidence': 0.85,
                'locate': {
                    'type': 'task_list',
                    'command': 'pm now --json',
                    'tasks': next_action_indices,
                    'description': 'Next actions available in now list'
                }
            })

        # 5. 处理重要邮件
        if email_data.get("authenticated") and email_data.get("recent_important_count", 0) > 0:
            recommendations.append({
                'title': '处理重要邮件',
                'description': f"扫描并转换 {email_data['recent_important_count']} 封重要邮件为任务",
                'execute_handle': 'pm gmail scan',
                'tool': 'gmail',
                'args': ['scan'],
                'priority': 3,
                'confidence': 0.8,
                'locate': {
                    'type': 'command',
                    'command': 'pm gmail scan',
                    'description': 'Scan important emails'
                }
            })

        # 6. 启动深度工作会话
        if task_data.get("high_priority_count", 0) > 0:
            # Find high priority tasks in now list
            high_priority_indices = []
            for idx, task in enumerate(now_tasks[:10], 1):
                if task.get('priority') and 'high' in task.get('priority', '').lower():
                    high_priority_indices.append({
                        'index': idx,
                        'task_id': task.get('id'),
                        'title': task.get('title', '')[:50]
                    })

            recommendations.append({
                'title': '开始深度工作',
                'description': f"进入专注模式处理 {task_data['high_priority_count']} 个高优先级任务",
                'execute_handle': 'pm start-session "Deep Work"',
                'tool': 'start-session',
                'args': ['Deep Work'],
                'priority': 4,
                'confidence': 0.85,
                'locate': {
                    'type': 'task_list',
                    'command': 'pm now --json',
                    'tasks': high_priority_indices,
                    'description': 'High priority tasks for deep work session'
                }
            })

        # 7. 获取AI建议
        recommendations.append({
            'title': '获取智能建议',
            'description': 'AI分析当前状态并推荐最适合的任务',
            'execute_handle': 'pm ai suggest --detailed',
            'tool': 'ai',
            'args': ['suggest', '--detailed'],
            'priority': 2,
            'confidence': 0.9,
            'locate': {
                'type': 'ai_analysis',
                'command': 'pm ai suggest --detailed',
                'description': 'Get AI-powered task recommendations'
            }
        })

        # 8. 项目回顾
        if task_data.get("project_count", 0) > 0:
            recommendations.append({
                'title': '项目进度回顾',
                'description': f"查看 {task_data['project_count']} 个活跃项目的进展",
                'execute_handle': 'pm projects',
                'tool': 'projects',
                'args': [],
                'priority': 2,
                'confidence': 0.75,
                'locate': {
                    'type': 'command',
                    'command': 'pm projects',
                    'description': 'Review active projects'
                }
            })

        # 9. 系统设置
        if not system_data.get("gmail_authenticated"):
            recommendations.append({
                'title': '启用邮件集成',
                'description': '配置Gmail以启用智能邮件处理功能',
                'execute_handle': 'pm auth login google',
                'tool': 'auth',
                'args': ['login', 'google'],
                'priority': 2,
                'confidence': 0.95,
                'locate': {
                    'type': 'setup',
                    'command': 'pm auth login google',
                    'description': 'Enable Gmail integration'
                }
            })

        # 10. 时间块规划
        recommendations.append({
            'title': '规划时间块',
            'description': '查看今日时间块安排，优化工作节奏',
            'execute_handle': 'pm timeblock today',
            'tool': 'timeblock',
            'args': ['today'],
            'priority': 2,
            'confidence': 0.7,
            'locate': {
                'type': 'planning',
                'command': 'pm timeblock today',
                'description': 'View today\'s time blocks'
            }
        })

        # 按优先级和置信度排序
        recommendations.sort(key=lambda x: (x['priority'], x['confidence']), reverse=True)

        return recommendations[:10]  # 返回前10个建议

    def _format_session_insights_for_claude(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """为Claude格式化session洞察信息
        
        Args:
            session_data: Session统计数据
            
        Returns:
            格式化的session洞察，供Claude使用
        """
        
        try:
            if not session_data.get("enabled"):
                return {
                    "available": False,
                    "message": "Session统计功能未启用"
                }
            
            yesterday_overview = session_data.get("yesterday_overview", {})
            week_progress = session_data.get("week_progress", {})
            budget_warnings = session_data.get("budget_warnings", [])
            active_session = session_data.get("active_session")
            recommendations = session_data.get("recommendations", [])
            
            insights = {
                "available": True,
                "yesterday_summary": {
                    "sessions_count": yesterday_overview.get("sessions_count", 0),
                    "total_hours": yesterday_overview.get("total_hours", 0),
                    "avg_productivity": yesterday_overview.get("avg_productivity", 0),
                    "top_project": yesterday_overview.get("top_project"),
                    "completion_rate": yesterday_overview.get("completion_rate", 0)
                },
                "week_summary": {
                    "active_projects": len(week_progress.get("active_projects", [])),
                    "trending_up": week_progress.get("trending_up", []),
                    "needs_attention": week_progress.get("needs_attention", []),
                    "total_hours_this_week": week_progress.get("week_comparison", {}).get("this_week_total_hours", 0),
                    "total_hours_last_week": week_progress.get("week_comparison", {}).get("last_week_total_hours", 0)
                },
                "current_state": {
                    "has_active_session": active_session is not None,
                    "active_session_duration": active_session.get("duration_minutes", 0) if active_session else 0,
                    "budget_alerts_count": len(budget_warnings),
                    "critical_alerts": len([w for w in budget_warnings if w.get("severity") == "critical"])
                },
                "ai_recommendations": recommendations,
                "context_for_claude": {
                    "user_work_patterns": self._analyze_work_patterns(yesterday_overview, week_progress),
                    "productivity_context": self._analyze_productivity_context(yesterday_overview),
                    "attention_areas": week_progress.get("needs_attention", []) + 
                                     [w.get("project", "") for w in budget_warnings if w.get("severity") in ["high", "critical"]]
                }
            }
            
            return insights
            
        except Exception as e:
            logger.error("Error formatting session insights for Claude", error=str(e))
            return {
                "available": False,
                "error": str(e)
            }

    def _analyze_work_patterns(self, yesterday: Dict[str, Any], week: Dict[str, Any]) -> List[str]:
        """分析用户工作模式"""
        patterns = []
        
        # 昨日工作强度分析
        yesterday_hours = yesterday.get("total_hours", 0)
        if yesterday_hours > 8:
            patterns.append("高强度工作者：昨日工作时间超过8小时")
        elif yesterday_hours < 2:
            patterns.append("低活跃度：昨日工作时间不足2小时")
        else:
            patterns.append("适度工作：昨日工作时间合理")
        
        # 生产力模式分析
        avg_productivity = yesterday.get("avg_productivity", 0)
        if avg_productivity >= 4.0:
            patterns.append("高效工作者：昨日平均生产力4.0+")
        elif avg_productivity < 3.0:
            patterns.append("需要优化：昨日平均生产力低于3.0")
        
        # 项目专注度分析
        active_projects = len(week.get("active_projects", []))
        if active_projects > 5:
            patterns.append("多项目并行：本周活跃项目较多，可能分散注意力")
        elif active_projects == 1:
            patterns.append("单项目专注：本周主要专注一个项目")
        
        return patterns[:3]  # 限制到3个关键模式
    
    def _analyze_productivity_context(self, yesterday: Dict[str, Any]) -> str:
        """分析生产力背景"""
        avg_productivity = yesterday.get("avg_productivity", 0)
        sessions_count = yesterday.get("sessions_count", 0)
        
        if sessions_count == 0:
            return "昨日无session记录，缺乏时间追踪数据"
        elif avg_productivity >= 4.0:
            return "昨日生产力优秀，工作状态良好"
        elif avg_productivity >= 3.0:
            return "昨日生产力中等，有改进空间"
        else:
            return "昨日生产力偏低，建议关注工作环境和专注度"

    def _generate_session_statistics_section(self, session_data: Dict[str, Any]) -> str:
        """生成Session统计部分 (AC-3.1, AC-3.2, AC-3.3, AC-3.4)
        
        Args:
            session_data: Session统计数据
            
        Returns:
            格式化的session统计section，保持briefing风格
        """
        
        try:
            if not session_data.get("enabled"):
                return ""
            
            # 使用现有的BriefingSessionIntegration格式化方法 (AC-3.4)
            if self.session_integration:
                formatted_section = self.session_integration.format_briefing_section(
                    yesterday_overview=session_data.get("yesterday_overview", {}),
                    week_progress=session_data.get("week_progress", {}),
                    budget_warnings=session_data.get("budget_warnings", []),
                    active_session=session_data.get("active_session")
                )
                return formatted_section
            
            return ""
            
        except Exception as e:
            logger.error("Error generating session statistics section", error=str(e))
            # 发生错误时，不显示任何内容，确保briefing正常工作
            return ""

    def _task_to_dict(self, task) -> Dict[str, Any]:
        """将任务对象转换为字典"""

        return {
            "title": task.title,
            "status": task.status.value,
            "priority": task.priority.value if task.priority else "medium",
            "due_date": task.due_date.isoformat() if task.due_date else None,
            "context": task.context.value if task.context else None
        }

    def _get_fallback_data(self) -> Dict[str, Any]:
        """获取错误时的默认数据"""

        return {
            "tasks": self._get_fallback_task_data(),
            "emails": {"authenticated": False, "error": "数据收集失败"},
            "projects": {"error": "数据收集失败"},
            "system_status": {"error": "状态检查失败"},
            "capabilities": {"error": "功能发现失败"}
        }

    def _categorize_inbox_tasks(self, tasks: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """将收件箱任务按类型分类，提高信息密度"""

        categories = {
            "🔥 测试和学习类": [],
            "⚡ 技术集成类": [],
            "📋 工作任务类": [],
            "🧹 清理类": []
        }

        for task in tasks:
            title = task.get('title', '').lower()

            # 基于标题关键词分类
            if any(keyword in title for keyword in ['test', '测试', 'learn', '学习', 'rehearsal']):
                categories["🔥 测试和学习类"].append(task)
            elif any(keyword in title for keyword in ['integration', '集成', 'cli', 'api', 'gemini', 'wrapper']):
                categories["⚡ 技术集成类"].append(task)
            elif any(keyword in title for keyword in ['aaaa', 'aaa', 'test task']):
                categories["🧹 清理类"].append(task)
            else:
                categories["📋 工作任务类"].append(task)

        # 移除空分类
        return {k: v for k, v in categories.items() if v}

    def _get_fallback_task_data(self) -> Dict[str, Any]:
        """获取任务数据失败时的默认值"""

        return {
            "total_tasks": 0,
            "inbox_count": 0,
            "next_action_count": 0,
            "project_count": 0,
            "completed_count": 0,
            "high_priority_count": 0,
            "medium_priority_count": 0,
            "due_today_count": 0,
            "overdue_count": 0,
            "high_priority_tasks": [],
            "due_today_tasks": [],
            "overdue_tasks": [],
            "inbox_tasks": []
        }

    def _save_briefings(self, user_briefing: str, claude_context: Dict[str, Any]) -> None:
        """保存简报文件"""

        try:
            # 保存用户简报
            with open(self.user_briefing_file, 'w', encoding='utf-8') as f:
                f.write(user_briefing)

            # 保存Claude上下文
            with open(self.claude_context_file, 'w', encoding='utf-8') as f:
                json.dump(claude_context, f, indent=2, ensure_ascii=False)

            # 保存AI建议供执行使用
            if self.last_ai_recommendations:
                with open(self.ai_recommendations_file, 'w', encoding='utf-8') as f:
                    json.dump(self.last_ai_recommendations, f, indent=2, ensure_ascii=False)

            logger.info("Briefings saved successfully",
                       user_briefing=str(self.user_briefing_file),
                       claude_context=str(self.claude_context_file))

        except Exception as e:
            logger.error("Failed to save briefings", error=str(e))
            raise

    def _update_session_state(self, data: Dict[str, Any]) -> None:
        """更新会话状态"""

        try:
            session_state = {
                "last_briefing": data["timestamp"].isoformat(),
                "last_data_summary": {
                    "total_tasks": data.get("tasks", {}).get("total_tasks", 0),
                    "recent_emails": data.get("emails", {}).get("recent_important_count", 0),
                    "system_healthy": all([
                        data.get("system_status", {}).get("gmail_authenticated", False),
                        data.get("system_status", {}).get("config_initialized", False)
                    ])
                }
            }

            with open(self.session_state_file, 'w', encoding='utf-8') as f:
                json.dump(session_state, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.error("Failed to update session state", error=str(e))

    def load_user_briefing(self) -> Optional[str]:
        """加载用户简报"""

        try:
            if self.user_briefing_file.exists():
                return self.user_briefing_file.read_text(encoding='utf-8')
        except Exception as e:
            logger.error("Failed to load user briefing", error=str(e))

        return None

    def load_claude_context(self) -> Optional[Dict[str, Any]]:
        """加载Claude上下文"""

        try:
            if self.claude_context_file.exists():
                with open(self.claude_context_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error("Failed to load Claude context", error=str(e))

        return None

    def load_ai_recommendations(self) -> Optional[List[Dict[str, Any]]]:
        """加载保存的AI建议"""

        try:
            if self.ai_recommendations_file.exists():
                with open(self.ai_recommendations_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error("Failed to load AI recommendations", error=str(e))

        return None