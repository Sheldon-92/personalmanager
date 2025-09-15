#!/usr/bin/env python3
"""
习惯到Google Tasks同步脚本

将PersonalManager中的习惯自动转换为Google Tasks中的每日任务模板
支持时间设置和自动创建每日任务实例
"""

import sys
import os
from datetime import datetime, time, timedelta
from typing import List, Dict, Any, Optional

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from pm.storage.habit_storage import HabitStorage
from pm.integrations.google_tasks import GoogleTasksIntegration
from pm.integrations.google_auth import GoogleAuthManager
from pm.core.config import PMConfig
import structlog
import requests

logger = structlog.get_logger()


class HabitToTaskSyncer:
    """习惯到Google Tasks同步器"""

    def __init__(self):
        self.config = PMConfig()
        self.habit_storage = HabitStorage(self.config)

        # 初始化Google Tasks集成
        try:
            # 直接初始化GoogleAuthManager而不是通过GoogleTasksIntegration
            self.auth_manager = GoogleAuthManager(self.config)
            logger.info("Google Auth Manager初始化成功")
        except Exception as e:
            logger.error("Google Auth Manager初始化失败", error=str(e))
            raise

    def get_daily_habits(self) -> List[Dict[str, Any]]:
        """获取所有日常习惯"""
        habits = self.habit_storage.get_all_habits(active_only=True)
        daily_habits = []

        for habit in habits:
            if habit.frequency.value == 'daily':
                # 转换为字典格式
                habit_dict = {
                    'id': habit.id,
                    'name': habit.name,
                    'description': habit.description,
                    'frequency': habit.frequency.value,
                    'active': habit.active,
                    'reminder_time': habit.reminder_time,
                    'cue': habit.cue,
                    'routine': habit.routine,
                    'reward': habit.reward,
                    'target_duration': habit.target_duration
                }
                daily_habits.append(habit_dict)

        logger.info(f"找到 {len(daily_habits)} 个日常习惯")
        return daily_habits

    def get_task_lists(self) -> List[Dict[str, Any]]:
        """获取Google Tasks列表"""
        if not self.auth_manager.is_google_authenticated():
            raise Exception("未通过Google认证")

        token = self.auth_manager.get_google_token()
        if not token or token.is_expired:
            raise Exception("Google认证已过期")

        api_url = 'https://www.googleapis.com/tasks/v1/users/@me/lists'
        headers = {
            'Authorization': token.authorization_header,
            'Accept': 'application/json'
        }

        response = requests.get(api_url, headers=headers)
        if response.status_code != 200:
            raise Exception(f"获取任务列表失败: {response.status_code} - {response.text}")

        data = response.json()
        return data.get('items', [])

    def get_tasks(self, list_id: str) -> List[Dict[str, Any]]:
        """获取指定列表的任务"""
        if not self.auth_manager.is_google_authenticated():
            raise Exception("未通过Google认证")

        token = self.auth_manager.get_google_token()
        if not token or token.is_expired:
            raise Exception("Google认证已过期")

        api_url = f'https://www.googleapis.com/tasks/v1/lists/{list_id}/tasks'
        headers = {
            'Authorization': token.authorization_header,
            'Accept': 'application/json'
        }

        response = requests.get(api_url, headers=headers)
        if response.status_code != 200:
            raise Exception(f"获取任务失败: {response.status_code} - {response.text}")

        data = response.json()
        return data.get('items', [])

    def create_task(self, list_id: str, title: str, notes: str = None, due: datetime = None) -> Dict[str, Any]:
        """在指定列表中创建新任务"""
        if not self.auth_manager.is_google_authenticated():
            raise Exception("未通过Google认证")

        token = self.auth_manager.get_google_token()
        if not token or token.is_expired:
            raise Exception("Google认证已过期")

        api_url = f'https://www.googleapis.com/tasks/v1/lists/{list_id}/tasks'
        headers = {
            'Authorization': token.authorization_header,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        # 构建任务数据
        task_data = {
            'title': title
        }

        if notes:
            task_data['notes'] = notes

        if due:
            # Google Tasks API需要RFC 3339格式的日期
            task_data['due'] = due.strftime('%Y-%m-%dT%H:%M:%S.%fZ')

        response = requests.post(api_url, headers=headers, json=task_data)
        if response.status_code != 200:
            raise Exception(f"创建任务失败: {response.status_code} - {response.text}")

        return response.json()

    def create_daily_task_template(self, habit: Dict[str, Any], target_date: datetime) -> Dict[str, Any]:
        """为习惯创建每日任务模板"""

        # 构建任务标题 - 包含时间信息
        title = habit['name']
        if habit.get('reminder_time'):
            title = f"⏰ {habit['reminder_time']} - {habit['name']}"

        # 构建任务描述
        notes_parts = []
        if habit.get('description'):
            notes_parts.append(f"📝 {habit['description']}")

        if habit.get('cue'):
            notes_parts.append(f"🔔 提示: {habit['cue']}")

        if habit.get('routine'):
            notes_parts.append(f"🎯 行为: {habit['routine']}")

        if habit.get('reward'):
            notes_parts.append(f"🎉 奖励: {habit['reward']}")

        if habit.get('target_duration'):
            notes_parts.append(f"⏱️ 时长: {habit['target_duration']}分钟")

        # 添加习惯追踪标识
        notes_parts.append(f"🏷️ 习惯ID: {habit['id']}")
        notes_parts.append(f"📅 日期: {target_date.strftime('%Y-%m-%d')}")

        notes = "\\n".join(notes_parts)

        # 设置截止时间
        due_datetime = None
        if habit.get('reminder_time'):
            try:
                # 解析时间字符串 (HH:MM)
                time_str = habit['reminder_time']
                hour, minute = map(int, time_str.split(':'))
                due_datetime = target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
            except (ValueError, AttributeError):
                logger.warning(f"无法解析提醒时间: {habit.get('reminder_time')}")

        return {
            'title': title,
            'notes': notes,
            'due': due_datetime,
            'status': 'needsAction'
        }

    def sync_habits_for_date(self, target_date: datetime = None) -> Dict[str, Any]:
        """为指定日期同步习惯到任务"""
        if target_date is None:
            target_date = datetime.now()

        logger.info(f"开始为 {target_date.strftime('%Y-%m-%d')} 同步习惯到任务")

        # 获取日常习惯
        daily_habits = self.get_daily_habits()
        if not daily_habits:
            logger.info("没有找到日常习惯")
            return {"success": True, "created": 0, "message": "没有日常习惯需要同步"}

        # 获取任务列表
        try:
            task_lists = self.get_task_lists()
            if not task_lists:
                logger.error("没有找到Google Tasks列表")
                return {"success": False, "error": "没有找到Google Tasks列表"}

            # 使用第一个列表（通常是"My Tasks"）
            default_list = task_lists[0]
            list_id = default_list['id']

            logger.info(f"使用任务列表: {default_list.get('title', 'Unknown')}")

        except Exception as e:
            logger.error("获取任务列表失败", error=str(e))
            return {"success": False, "error": f"获取任务列表失败: {str(e)}", "target_date": target_date.strftime('%Y-%m-%d')}

        # 为每个习惯创建任务
        created_count = 0
        errors = []

        for habit in daily_habits:
            try:
                # 创建任务模板
                task_data = self.create_daily_task_template(habit, target_date)

                # 检查是否已存在相同的任务（避免重复创建）
                existing_tasks = self.get_tasks(list_id)

                # 更精确的重复检查：检查习惯ID和日期
                date_str = target_date.strftime('%Y-%m-%d')
                habit_id = habit['id']
                duplicate_found = False

                for existing_task in existing_tasks:
                    existing_notes = existing_task.get('notes', '')
                    # 检查是否包含相同的习惯ID和日期
                    if (f"习惯ID: {habit_id}" in existing_notes and
                        f"日期: {date_str}" in existing_notes):
                        logger.info(f"任务已存在，跳过: {habit['name']} ({date_str})")
                        duplicate_found = True
                        break

                if duplicate_found:
                    continue

                # 创建新任务
                created_task = self.create_task(
                    list_id=list_id,
                    title=task_data['title'],
                    notes=task_data['notes'],
                    due=task_data['due']
                )

                if created_task:
                    created_count += 1
                    logger.info(f"✅ 创建任务: {habit['name']}")
                else:
                    errors.append(f"创建任务失败: {habit['name']}")

            except Exception as e:
                error_msg = f"处理习惯 '{habit['name']}' 时出错: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)

        # 构建结果
        result = {
            "success": True,
            "created": created_count,
            "total_habits": len(daily_habits),
            "target_date": target_date.strftime('%Y-%m-%d')
        }

        if errors:
            result["errors"] = errors
            result["success"] = len(errors) < len(daily_habits)  # 部分成功也算成功

        return result

    def sync_habits_for_week(self, start_date: datetime = None) -> Dict[str, Any]:
        """为一周同步习惯任务"""
        if start_date is None:
            start_date = datetime.now()

        results = []
        total_created = 0

        for i in range(7):
            target_date = start_date + timedelta(days=i)
            result = self.sync_habits_for_date(target_date)
            results.append(result)
            total_created += result.get('created', 0)

        return {
            "success": True,
            "total_created": total_created,
            "daily_results": results,
            "week_start": start_date.strftime('%Y-%m-%d')
        }


def main():
    """主函数 - 命令行界面"""
    import argparse

    parser = argparse.ArgumentParser(description='同步习惯到Google Tasks')
    parser.add_argument('--mode', choices=['today', 'tomorrow', 'week'],
                       default='today', help='同步模式')
    parser.add_argument('--date', help='指定日期 (YYYY-MM-DD)')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')

    args = parser.parse_args()

    # 设置日志级别
    if args.verbose:
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.dev.ConsoleRenderer()
            ],
            wrapper_class=structlog.stdlib.BoundLogger,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )

    # 初始化同步器
    try:
        syncer = HabitToTaskSyncer()
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return 1

    # 确定目标日期
    target_date = datetime.now()
    if args.date:
        try:
            target_date = datetime.strptime(args.date, '%Y-%m-%d')
        except ValueError:
            print(f"❌ 日期格式错误: {args.date}，请使用 YYYY-MM-DD 格式")
            return 1
    elif args.mode == 'tomorrow':
        target_date = datetime.now() + timedelta(days=1)

    # 执行同步
    try:
        if args.mode == 'week':
            result = syncer.sync_habits_for_week(target_date)
            print(f"📅 一周习惯同步完成:")
            print(f"   起始日期: {result['week_start']}")
            print(f"   总计创建: {result['total_created']} 个任务")
        else:
            result = syncer.sync_habits_for_date(target_date)
            print(f"📅 {result['target_date']} 习惯同步完成:")
            print(f"   创建任务: {result['created']}/{result['total_habits']}")

        if result.get('errors'):
            print("⚠️  部分错误:")
            for error in result['errors']:
                print(f"   - {error}")

        return 0 if result['success'] else 1

    except Exception as e:
        print(f"❌ 同步失败: {e}")
        return 1


if __name__ == "__main__":
    exit(main())