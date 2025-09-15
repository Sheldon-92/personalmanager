"""交互管理器 - 处理编号选择和快捷命令

支持编号选择模式和斜杠(/)快捷命令系统
"""

import re
from typing import List, Dict, Any, Optional, Tuple
import structlog

from pm.core.config import PMConfig
from pm.core.briefing_generator import BriefingGenerator

logger = structlog.get_logger()


class InteractionManager:
    """PersonalManager交互管理器"""

    def __init__(self, config: PMConfig):
        self.config = config
        self.briefing_generator = BriefingGenerator(config)
        self.current_options = {}  # 存储当前可用的编号选项

    def parse_number_input(self, user_input: str) -> List[int]:
        """解析用户的编号输入

        支持格式:
        - 单个数字: "1"
        - 多个数字: "1,3,5" 或 "1 3 5"
        - 范围: "2-4" 或 "2-4,6"
        """

        numbers = []
        user_input = user_input.strip()

        # 处理逗号和空格分隔
        parts = re.split(r'[,\s]+', user_input)

        for part in parts:
            part = part.strip()
            if not part:
                continue

            # 处理范围 (如 2-4)
            if '-' in part:
                try:
                    start, end = part.split('-')
                    start, end = int(start.strip()), int(end.strip())
                    numbers.extend(range(start, end + 1))
                except ValueError:
                    continue
            else:
                # 处理单个数字
                try:
                    numbers.append(int(part))
                except ValueError:
                    continue

        return sorted(list(set(numbers)))  # 去重并排序

    def get_slash_commands(self) -> Dict[str, Dict[str, Any]]:
        """获取斜杠(/)快捷命令列表"""

        return {
            "/pm": {
                "description": "PersonalManager 核心功能",
                "commands": {
                    "briefing": "生成工作简报",
                    "inbox": "查看收件箱任务",
                    "clarify": "开始GTD澄清",
                    "next": "查看下一步行动",
                    "today": "获取今日推荐",
                    "session": "会话管理"
                }
            },
            "/gmail": {
                "description": "Gmail邮件处理",
                "commands": {
                    "scan": "扫描重要邮件",
                    "preview": "预览邮件",
                    "stats": "邮件统计"
                }
            },
            "/task": {
                "description": "任务管理",
                "commands": {
                    "add": "添加新任务",
                    "complete": "完成任务",
                    "search": "搜索任务",
                    "delete": "删除任务"
                }
            },
            "/quick": {
                "description": "快速操作",
                "commands": {
                    "cleanup": "清理测试任务",
                    "overdue": "处理逾期任务",
                    "urgent": "查看紧急任务",
                    "health": "系统健康检查"
                }
            }
        }

    def generate_action_options(self) -> Tuple[List[str], Dict[int, str]]:
        """生成当前可执行的行动选项

        Returns:
            (选项描述列表, 编号到命令的映射)
        """

        try:
            # 获取最新的简报数据
            briefing_data = self.briefing_generator._collect_briefing_data()
            task_data = briefing_data.get("tasks", {})
            email_data = briefing_data.get("emails", {})

            options = []
            commands = {}
            option_num = 1

            # 1. 逾期任务
            if task_data.get("overdue_count", 0) > 0:
                overdue_task = task_data.get("overdue_tasks", [{}])[0]
                options.append(f"**{option_num}. 🚨 处理逾期任务** - '{overdue_task.get('title', '未知任务')}'")
                commands[option_num] = f"pm task {overdue_task.get('title', '')}"
                option_num += 1

            # 2. 今日截止任务
            if task_data.get("due_today_count", 0) > 0:
                options.append(f"**{option_num}. 📅 完成今日任务** - {task_data['due_today_count']}个截止任务")
                commands[option_num] = "pm next @today"
                option_num += 1

            # 3. 收件箱处理
            if task_data.get("inbox_count", 0) > 0:
                if task_data.get("inbox_count") <= 5:
                    options.append(f"**{option_num}. 📥 快速清空收件箱** - {task_data['inbox_count']}个任务")
                    commands[option_num] = "pm clarify"
                else:
                    options.append(f"**{option_num}. 📥 分批处理收件箱** - 先处理快速任务")
                    commands[option_num] = "pm clarify --batch 5"
                option_num += 1

                # 清理选项
                cleanup_count = len([t for t in task_data.get("inbox_tasks", [])
                                   if 'aaa' in t.get('title', '').lower()])
                if cleanup_count > 0:
                    options.append(f"**{option_num}. 🧹 清理测试任务** - {cleanup_count}个无用任务")
                    commands[option_num] = "/quick cleanup"
                    option_num += 1

            # 4. 下一步行动
            if task_data.get("next_action_count", 0) > 0:
                options.append(f"**{option_num}. ⚡ 执行下一步行动** - {task_data['next_action_count']}个可执行任务")
                commands[option_num] = "pm next"
                option_num += 1

            # 5. 邮件处理
            if email_data.get("recent_important_count", 0) > 0:
                options.append(f"**{option_num}. 📧 处理重要邮件** - {email_data['recent_important_count']}封邮件")
                commands[option_num] = "pm gmail scan"
                option_num += 1

            # 6. 今日推荐
            options.append(f"**{option_num}. 📊 获取今日推荐** - AI智能推荐")
            commands[option_num] = "pm today"
            option_num += 1

            # 7. 邮件配置（如果需要）
            if not email_data.get("authenticated"):
                options.append(f"**{option_num}. 🔑 启用邮件集成** - 配置Gmail")
                commands[option_num] = "pm auth login google"

            self.current_options = commands
            return options, commands

        except Exception as e:
            logger.error("Failed to generate action options", error=str(e))
            return [], {}

    def execute_numbered_choice(self, numbers: List[int]) -> List[str]:
        """执行编号选择对应的命令

        Args:
            numbers: 用户选择的编号列表

        Returns:
            要执行的命令列表
        """

        commands = []

        for num in numbers:
            if num in self.current_options:
                command = self.current_options[num]
                commands.append(command)
                logger.info("User selected option", number=num, command=command)
            else:
                logger.warning("Invalid option number", number=num)

        return commands

    def format_slash_help(self) -> str:
        """格式化斜杠命令帮助信息"""

        lines = ["## 🚀 快捷命令 (斜杠模式)", ""]

        slash_commands = self.get_slash_commands()

        for prefix, info in slash_commands.items():
            lines.append(f"### {prefix} - {info['description']}")
            lines.append("")

            for cmd, desc in info['commands'].items():
                lines.append(f"- `{prefix} {cmd}` - {desc}")

            lines.append("")

        lines.extend([
            "💡 **使用方法**: 输入 `/pm briefing` 或直接 `/pm` 查看所有选项",
            "🎯 **编号模式**: 回复数字(如'1,3')执行对应操作",
            ""
        ])

        return "\n".join(lines)

    def is_slash_command(self, user_input: str) -> bool:
        """检查输入是否为斜杠命令"""
        return user_input.strip().startswith('/')

    def is_number_input(self, user_input: str) -> bool:
        """检查输入是否为编号选择"""
        # 允许数字、逗号、连字符、空格
        pattern = r'^[\d,\s-]+$'
        return bool(re.match(pattern, user_input.strip()))

    def process_user_input(self, user_input: str) -> Dict[str, Any]:
        """处理用户输入，返回处理结果

        Returns:
            {
                'type': 'slash_command' | 'number_choice' | 'regular_text',
                'commands': [命令列表],
                'numbers': [选择的编号],
                'raw_input': 原始输入
            }
        """

        user_input = user_input.strip()

        if self.is_slash_command(user_input):
            return {
                'type': 'slash_command',
                'commands': [user_input],
                'numbers': [],
                'raw_input': user_input
            }

        elif self.is_number_input(user_input):
            numbers = self.parse_number_input(user_input)
            commands = self.execute_numbered_choice(numbers)

            return {
                'type': 'number_choice',
                'commands': commands,
                'numbers': numbers,
                'raw_input': user_input
            }

        else:
            return {
                'type': 'regular_text',
                'commands': [],
                'numbers': [],
                'raw_input': user_input
            }

    def get_interactive_prompt(self) -> str:
        """生成交互式提示信息"""

        options, _ = self.generate_action_options()

        if not options:
            return "💡 输入 `/pm` 查看可用命令，或 `pm briefing` 生成最新简报"

        prompt_lines = ["## 🎯 选择操作 (编号模式)", ""]
        prompt_lines.extend(options)
        prompt_lines.extend([
            "",
            "💬 **回复方式**:",
            "- 编号选择: `1` 或 `1,3` 或 `2-4`",
            "- 快捷命令: `/pm briefing` 或 `/gmail scan`",
            "- 自然语言: 描述你想做的事情",
            ""
        ])

        return "\n".join(prompt_lines)