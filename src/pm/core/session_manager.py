"""会话管理系统 - 统一管理PersonalManager会话状态和启动流程

负责协调简报生成、功能发现、会话启动等核心流程
"""

import json
import subprocess
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import structlog

from pm.core.config import PMConfig
from pm.core.briefing_generator import BriefingGenerator
from pm.core.function_registry import FunctionRegistry

logger = structlog.get_logger()


class SessionManager:
    """PersonalManager会话管理器"""

    def __init__(self, config: PMConfig):
        self.config = config
        self.session_dir = Path.home() / ".personalmanager" / "session"
        self.scripts_dir = Path.home() / ".personalmanager" / "scripts"

        # 核心组件
        self.briefing_generator = BriefingGenerator(config)
        self.function_registry = FunctionRegistry(config)

        # 会话状态文件
        self.session_state_file = self.session_dir / "session_state.json"
        self.development_log_file = self.session_dir / "development_log.json"

    def start_session(self, force_refresh: bool = False, show_briefing: bool = True) -> Dict[str, Any]:
        """启动PersonalManager完整会话"""

        logger.info("Starting PersonalManager session", force_refresh=force_refresh)

        try:
            # 确保目录存在
            self.session_dir.mkdir(parents=True, exist_ok=True)
            self.scripts_dir.mkdir(parents=True, exist_ok=True)

            # 生成双向简报
            user_briefing, claude_context = self.briefing_generator.generate_dual_briefing(force_refresh)

            # 检测功能变更
            capability_changes = self._detect_capability_changes()

            # 更新开发日志
            self._update_development_log(capability_changes)

            # 生成启动脚本
            self._generate_startup_scripts()

            session_info = {
                "session_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
                "start_time": datetime.now().isoformat(),
                "briefing_generated": True,
                "capabilities_refreshed": force_refresh or bool(capability_changes.get("has_changes")),
                "user_briefing_path": str(self.briefing_generator.user_briefing_file),
                "claude_context_path": str(self.briefing_generator.claude_context_file),
                "capability_changes": capability_changes
            }

            # 显示用户简报
            if show_briefing:
                print(user_briefing)

                # 如果有新功能，特别提示
                if capability_changes.get("has_changes"):
                    self._show_capability_changes(capability_changes)

            logger.info("PersonalManager session started successfully")
            return session_info

        except Exception as e:
            logger.error("Failed to start PersonalManager session", error=str(e))
            raise

    def refresh_capabilities(self) -> Dict[str, Any]:
        """刷新功能注册表"""

        logger.info("Refreshing PersonalManager capabilities")

        try:
            # 获取旧的注册表用于比较
            old_registry = self.function_registry.load_registry()

            # 重新发现所有功能
            new_registry = self.function_registry.discover_all_capabilities()

            # 检测变更
            changes = self._compare_capabilities(old_registry, new_registry)

            # 更新开发日志
            if changes["has_changes"]:
                self._log_capability_changes(changes)

            logger.info("Capabilities refreshed successfully",
                       new_functions=len(changes.get("new_functions", [])),
                       updated_functions=len(changes.get("updated_functions", [])))

            return {
                "refresh_time": datetime.now().isoformat(),
                "changes": changes,
                "summary": self.function_registry.get_capability_summary()
            }

        except Exception as e:
            logger.error("Failed to refresh capabilities", error=str(e))
            raise

    def generate_context_summary(self) -> str:
        """生成上下文摘要供Claude使用"""

        try:
            claude_context = self.briefing_generator.load_claude_context()
            if not claude_context:
                return "无法加载上下文信息，请运行 pm start-session"

            # 生成简洁的上下文摘要
            summary_lines = [
                "🤖 PersonalManager AI Assistant - 上下文摘要",
                "=" * 50
            ]

            # 身份和角色
            identity = claude_context.get("identity", {})
            summary_lines.extend([
                f"角色: {identity.get('role', 'PersonalManager Assistant')}",
                f"能力: {identity.get('capabilities', '任务管理、邮件处理、项目协调')}",
                ""
            ])

            # 当前工作状态
            work_context = claude_context.get("current_work_context", {})
            summary_lines.extend([
                "📊 当前工作状态:",
                f"  • 总任务: {work_context.get('total_tasks', 0)} 个",
                f"  • 收件箱: {work_context.get('inbox_tasks', 0)} 个",
                f"  • 下一步行动: {work_context.get('next_actions', 0)} 个",
                f"  • 高优先级: {work_context.get('high_priority_tasks', 0)} 个",
                f"  • 逾期任务: {work_context.get('overdue_tasks', 0)} 个",
                ""
            ])

            # 系统状态
            system_status = claude_context.get("system_status", {})
            summary_lines.extend([
                "🔧 系统状态:",
                f"  • Gmail集成: {'✅' if system_status.get('gmail_authenticated') else '❌'}",
                f"  • 配置完成: {'✅' if system_status.get('config_initialized') else '❌'}",
                ""
            ])

            # 可用功能
            functions = claude_context.get("available_functions", {})
            core_functions = functions.get("core_functions", {})
            if core_functions:
                summary_lines.extend([
                    "🛠️ 核心功能:",
                    f"  • Gmail: {', '.join(core_functions.get('gmail_integration', []))}",
                    f"  • 任务: {', '.join(core_functions.get('task_management', []))}",
                    f"  • 会话: {', '.join(core_functions.get('session_management', []))}",
                    ""
                ])

            # 今日重点
            today_focus = claude_context.get("today_focus", [])
            if today_focus:
                summary_lines.extend([
                    "🎯 今日重点:",
                    *[f"  • {item}" for item in today_focus[:3]],
                    ""
                ])

            # 协作建议
            recommendations = claude_context.get("session_recommendations", [])
            if recommendations:
                summary_lines.extend([
                    "💡 协作建议:",
                    *[f"  • {rec}" for rec in recommendations[:3]],
                    ""
                ])

            summary_lines.extend([
                "=" * 50,
                f"上下文更新时间: {claude_context.get('briefing_timestamp', '未知')}"
            ])

            return "\n".join(summary_lines)

        except Exception as e:
            logger.error("Failed to generate context summary", error=str(e))
            return f"上下文摘要生成失败: {str(e)}"

    def check_session_health(self) -> Dict[str, Any]:
        """检查会话健康状态"""

        health_status = {
            "timestamp": datetime.now().isoformat(),
            "overall_healthy": True,
            "issues": [],
            "recommendations": []
        }

        try:
            # 检查必要文件
            required_files = [
                self.briefing_generator.user_briefing_file,
                self.briefing_generator.claude_context_file,
                self.function_registry.registry_file
            ]

            for file_path in required_files:
                if not file_path.exists():
                    health_status["overall_healthy"] = False
                    health_status["issues"].append(f"缺少文件: {file_path.name}")

            # 检查数据新鲜度
            if self.briefing_generator.user_briefing_file.exists():
                briefing_time = datetime.fromtimestamp(
                    self.briefing_generator.user_briefing_file.stat().st_mtime
                )
                hours_old = (datetime.now() - briefing_time).total_seconds() / 3600

                if hours_old > 8:  # 超过8小时
                    health_status["issues"].append(f"简报数据过旧 ({hours_old:.1f}小时)")
                    health_status["recommendations"].append("运行 pm briefing 更新数据")

            # 检查系统状态
            claude_context = self.briefing_generator.load_claude_context()
            if claude_context:
                system_status = claude_context.get("system_status", {})
                if not system_status.get("gmail_authenticated"):
                    health_status["recommendations"].append("运行 pm auth login google 启用邮件集成")

                work_context = claude_context.get("current_work_context", {})
                if work_context.get("overdue_tasks", 0) > 0:
                    health_status["recommendations"].append(f"处理 {work_context['overdue_tasks']} 个逾期任务")

            # 如果有问题，标记为不健康
            if health_status["issues"]:
                health_status["overall_healthy"] = False

        except Exception as e:
            health_status["overall_healthy"] = False
            health_status["issues"].append(f"健康检查失败: {str(e)}")

        return health_status

    def _detect_capability_changes(self) -> Dict[str, Any]:
        """检测功能变更"""

        try:
            # 加载开发日志
            dev_log = self._load_development_log()
            last_check = dev_log.get("last_capability_check")

            if not last_check:
                # 首次检查
                return {
                    "has_changes": False,
                    "message": "首次功能检查",
                    "new_functions": [],
                    "updated_functions": []
                }

            # 这里可以实现更复杂的变更检测逻辑
            # 现在简化处理，检查注册表时间戳
            registry = self.function_registry.load_registry()
            if not registry:
                return {"has_changes": False}

            registry_time = datetime.fromisoformat(registry.get("discovery_timestamp", "2000-01-01"))
            last_check_time = datetime.fromisoformat(last_check)

            if registry_time > last_check_time:
                return {
                    "has_changes": True,
                    "message": "检测到功能更新",
                    "last_update": registry_time.isoformat()
                }

            return {"has_changes": False}

        except Exception as e:
            logger.error("Error detecting capability changes", error=str(e))
            return {"has_changes": False, "error": str(e)}

    def _compare_capabilities(self, old_registry: Optional[Dict], new_registry: Dict) -> Dict[str, Any]:
        """比较新旧功能注册表"""

        if not old_registry:
            return {
                "has_changes": True,
                "message": "首次功能发现",
                "new_functions": [],
                "updated_functions": []
            }

        changes = {
            "has_changes": False,
            "new_functions": [],
            "updated_functions": [],
            "removed_functions": []
        }

        try:
            # 比较CLI命令
            old_cli = set(old_registry.get("cli_commands", {}).keys())
            new_cli = set(new_registry.get("cli_commands", {}).keys())

            new_commands = new_cli - old_cli
            removed_commands = old_cli - new_cli

            if new_commands or removed_commands:
                changes["has_changes"] = True
                changes["new_functions"].extend([f"CLI命令: {cmd}" for cmd in new_commands])
                changes["removed_functions"].extend([f"CLI命令: {cmd}" for cmd in removed_commands])

            # 比较集成模块
            old_integrations = set(old_registry.get("integrations", {}).keys())
            new_integrations = set(new_registry.get("integrations", {}).keys())

            new_integ = new_integrations - old_integrations
            removed_integ = old_integrations - new_integrations

            if new_integ or removed_integ:
                changes["has_changes"] = True
                changes["new_functions"].extend([f"集成模块: {mod}" for mod in new_integ])
                changes["removed_functions"].extend([f"集成模块: {mod}" for mod in removed_integ])

        except Exception as e:
            logger.error("Error comparing capabilities", error=str(e))

        return changes

    def _show_capability_changes(self, changes: Dict[str, Any]) -> None:
        """显示功能变更信息"""

        if not changes.get("has_changes"):
            return

        print("\n🆕 PersonalManager 功能更新")
        print("=" * 40)

        if changes.get("new_functions"):
            print("新增功能:")
            for func in changes["new_functions"]:
                print(f"  + {func}")

        if changes.get("updated_functions"):
            print("更新功能:")
            for func in changes["updated_functions"]:
                print(f"  ~ {func}")

        if changes.get("removed_functions"):
            print("移除功能:")
            for func in changes["removed_functions"]:
                print(f"  - {func}")

        print("\n我现在知道这些新功能了！可以更好地为你服务。")
        print("=" * 40)

    def _update_development_log(self, changes: Dict[str, Any]) -> None:
        """更新开发日志"""

        try:
            dev_log = self._load_development_log()

            # 更新检查时间
            dev_log["last_capability_check"] = datetime.now().isoformat()

            # 记录变更
            if changes.get("has_changes"):
                if "change_history" not in dev_log:
                    dev_log["change_history"] = []

                change_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "changes": changes
                }
                dev_log["change_history"].append(change_entry)

                # 只保留最近10次变更
                dev_log["change_history"] = dev_log["change_history"][-10:]

            self._save_development_log(dev_log)

        except Exception as e:
            logger.error("Failed to update development log", error=str(e))

    def _log_capability_changes(self, changes: Dict[str, Any]) -> None:
        """记录功能变更到日志"""

        try:
            dev_log = self._load_development_log()

            if "capability_updates" not in dev_log:
                dev_log["capability_updates"] = []

            update_entry = {
                "timestamp": datetime.now().isoformat(),
                "changes": changes,
                "type": "capability_refresh"
            }

            dev_log["capability_updates"].append(update_entry)
            dev_log["capability_updates"] = dev_log["capability_updates"][-20:]  # 保留最近20次

            self._save_development_log(dev_log)

        except Exception as e:
            logger.error("Failed to log capability changes", error=str(e))

    def _load_development_log(self) -> Dict[str, Any]:
        """加载开发日志"""

        try:
            if self.development_log_file.exists():
                with open(self.development_log_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error("Failed to load development log", error=str(e))

        return {
            "created": datetime.now().isoformat(),
            "last_capability_check": None,
            "change_history": [],
            "capability_updates": []
        }

    def _save_development_log(self, dev_log: Dict[str, Any]) -> None:
        """保存开发日志"""

        try:
            with open(self.development_log_file, 'w', encoding='utf-8') as f:
                json.dump(dev_log, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error("Failed to save development log", error=str(e))

    def _generate_startup_scripts(self) -> None:
        """生成启动脚本"""

        try:
            # 生成bash启动脚本
            startup_script = self.scripts_dir / "pm-claude-start.sh"

            script_content = '''#!/bin/bash
# PersonalManager + Claude Code 启动脚本

echo "🚀 启动PersonalManager + Claude Code..."
echo ""

# 检查PersonalManager状态
pm_status=$(pm briefing --quiet 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "✅ PersonalManager状态正常"
else
    echo "⚠️  PersonalManager需要初始化，运行简报生成..."
    pm start-session --force-refresh
fi

echo ""
echo "📋 准备完成！启动Claude Code..."
echo "💡 PersonalManager已准备就绪，可以直接开始工作"
echo ""

# 如果可用，启动Claude Code
if command -v claude-code &> /dev/null; then
    claude-code
else
    echo "注意: 未找到claude-code命令"
    echo "请手动启动Claude Code"
fi
'''

            with open(startup_script, 'w', encoding='utf-8') as f:
                f.write(script_content)

            # 设置执行权限
            startup_script.chmod(0o755)

            logger.info("Startup scripts generated", script_path=str(startup_script))

        except Exception as e:
            logger.error("Failed to generate startup scripts", error=str(e))

    def get_session_summary(self) -> Dict[str, Any]:
        """获取会话摘要信息"""

        try:
            # 加载各种状态文件
            claude_context = self.briefing_generator.load_claude_context()
            session_state = {}

            if self.session_state_file.exists():
                with open(self.session_state_file, 'r', encoding='utf-8') as f:
                    session_state = json.load(f)

            dev_log = self._load_development_log()
            capabilities = self.function_registry.get_capability_summary()

            return {
                "session_active": bool(claude_context),
                "last_briefing": session_state.get("last_briefing"),
                "capabilities_summary": capabilities,
                "recent_changes": len(dev_log.get("change_history", [])),
                "health_status": self.check_session_health(),
                "available_scripts": list(self.scripts_dir.glob("*.sh")) if self.scripts_dir.exists() else []
            }

        except Exception as e:
            logger.error("Failed to get session summary", error=str(e))
            return {"error": str(e)}