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

logger = structlog.get_logger()


class BriefingGenerator:
    """双向简报生成器 - 为用户和Claude生成个性化简报"""

    def __init__(self, config: PMConfig):
        self.config = config
        self.session_dir = Path.home() / ".personalmanager" / "session"
        self.user_briefing_file = self.session_dir / "user_briefing.md"
        self.claude_context_file = self.session_dir / "claude_context.json"
        self.session_state_file = self.session_dir / "session_state.json"

        # 初始化核心组件
        self.function_registry = FunctionRegistry(config)
        self.gmail_processor = GmailProcessor(config)
        self.gtd_agent = GTDAgent(config)

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

    def _collect_briefing_data(self, force_refresh: bool = False) -> Dict[str, Any]:
        """收集简报所需的所有数据"""

        logger.info("Collecting briefing data")

        data = {
            "timestamp": datetime.now(),
            "date_str": datetime.now().strftime("%Y-%m-%d"),
            "time_str": datetime.now().strftime("%H:%M")
        }

        try:
            # 1. 任务数据
            data["tasks"] = self._collect_task_data()

            # 2. 邮件数据
            data["emails"] = self._collect_email_data()

            # 3. 项目数据
            data["projects"] = self._collect_project_data()

            # 4. 系统状态
            data["system_status"] = self._collect_system_status()

            # 5. 功能注册表
            data["capabilities"] = self._collect_capabilities_data(force_refresh)

            # 6. 开发历史
            data["development_history"] = self._collect_development_history()

        except Exception as e:
            logger.error("Error collecting briefing data", error=str(e))
            # 使用默认数据继续
            data.update(self._get_fallback_data())

        return data

    def _collect_task_data(self) -> Dict[str, Any]:
        """收集任务数据"""

        try:
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
                "high_priority_tasks": [self._task_to_dict(t) for t in high_priority[:5]],
                "due_today_tasks": [self._task_to_dict(t) for t in due_today],
                "overdue_tasks": [self._task_to_dict(t) for t in overdue],
                "inbox_tasks": [self._task_to_dict(t) for t in inbox_tasks[:15]],  # 增加到15个
                "next_action_tasks": [self._task_to_dict(t) for t in next_action_tasks[:5]]  # 添加下一步行动
            }

        except Exception as e:
            logger.error("Error collecting task data", error=str(e))
            return self._get_fallback_task_data()

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
                        "subject": email.subject[:50] + "..." if len(email.subject) > 50 else email.subject,
                        "sender": email.sender_name,
                        "importance_score": email.importance_score,
                        "is_urgent": email.is_urgent,
                        "is_important": email.is_important
                    }
                    for email in important_emails[:3]
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
                    "双向简报系统",
                    "功能自发现机制",
                    "邮件智能处理"
                ]
            }

        except Exception as e:
            logger.error("Error collecting development history", error=str(e))
            return {"error": str(e)}

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

        # 逾期任务 - 最重要，详细展示
        if task_data.get("overdue_tasks"):
            briefing_lines.append("### 🚨 逾期任务（需要立即处理）")
            for task in task_data["overdue_tasks"]:
                due_date = task.get('due_date', '未设置截止时间')
                context = task.get('context', '').replace('@', '') if task.get('context') else '一般'
                priority = task.get('priority', 'medium')

                briefing_lines.append(f"- **{task['title']}**")
                briefing_lines.append(f"  - 截止时间: {due_date}")
                briefing_lines.append(f"  - 优先级: {priority} | 场景: {context}")
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
                briefing_lines.append(f"  - 来自: {email['sender']}")
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

        # 智能工作建议 - 基于当前状态的具体行动指导
        briefing_lines.extend([
            "## 🎯 智能工作计划（编号选择模式）",
            ""
        ])

        # 生成编号化的具体行动选项
        action_options = []
        option_num = 1

        if task_data.get("overdue_count", 0) > 0:
            action_options.append(f"**{option_num}. 🚨 处理逾期任务** - 立即解决'{task_data['overdue_tasks'][0]['title']}'，防止进一步延误")
            option_num += 1

        if task_data.get("due_today_count", 0) > 0:
            action_options.append(f"**{option_num}. 📅 完成今日任务** - 处理今日截止的{task_data['due_today_count']}个任务")
            option_num += 1

        if task_data.get("inbox_count", 0) > 0:
            # 提供不同的收件箱处理策略
            if task_data.get("inbox_count") <= 5:
                action_options.append(f"**{option_num}. 📥 快速清空收件箱** - 只有{task_data['inbox_count']}个任务，预计20分钟完成")
            else:
                action_options.append(f"**{option_num}. 📥 分批处理收件箱** - 先处理测试/学习类任务（可快速完成）")
                option_num += 1
                action_options.append(f"**{option_num}. 🧹 清理无用任务** - 删除测试数据，减少收件箱负担")
            option_num += 1

        if task_data.get("next_action_count", 0) > 0:
            action_options.append(f"**{option_num}. ⚡ 执行下一步行动** - 查看{task_data['next_action_count']}个可立即执行的任务")
            option_num += 1

        if email_data.get("recent_important_count", 0) > 0:
            action_options.append(f"**{option_num}. 📧 处理重要邮件** - 转换{email_data['recent_important_count']}封邮件为任务")
            option_num += 1

        # 总是提供的基础选项
        action_options.append(f"**{option_num}. 📊 获取今日推荐** - AI智能分析推荐最适合的任务")
        option_num += 1

        if not email_data.get("authenticated"):
            action_options.append(f"**{option_num}. 🔑 启用邮件集成** - 配置Gmail智能处理")

        # 显示选项
        for action in action_options:
            briefing_lines.append(action)

        briefing_lines.extend([
            "",
            "💡 **使用方法**: 直接回复编号（如'1'、'1,3'、'2-4'）即可执行对应操作",
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
            "session_recommendations": self._generate_session_recommendations(data)
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