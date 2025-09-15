#!/usr/bin/env python3
"""
习惯完成情况同步到Obsidian脚本

从Google Tasks获取习惯完成数据，生成可视化的习惯追踪报告到Obsidian
"""

import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json
import re

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from pm.storage.habit_storage import HabitStorage
from pm.integrations.google_auth import GoogleAuthManager
from pm.core.config import PMConfig
import structlog
import requests

logger = structlog.get_logger()


class HabitTrackingSync:
    """习惯追踪Obsidian同步器"""

    def __init__(self):
        self.config = PMConfig()
        self.habit_storage = HabitStorage(self.config)
        self.auth_manager = GoogleAuthManager(self.config)

        # Obsidian路径配置
        self.obsidian_vault_path = self.config.home_dir / "Documents" / "Obsidian Vault"
        self.habits_folder = self.obsidian_vault_path / "PersonalManager" / "习惯追踪"

        # 确保目录存在
        self.habits_folder.mkdir(parents=True, exist_ok=True)

        logger.info("习惯追踪同步器初始化成功")

    def get_google_tasks_data(self, days_back: int = 30) -> List[Dict[str, Any]]:
        """获取Google Tasks中的习惯任务数据"""
        if not self.auth_manager.is_google_authenticated():
            logger.warning("Google认证未通过")
            return []

        token = self.auth_manager.get_google_token()
        if not token or token.is_expired:
            logger.warning("Google认证已过期")
            return []

        try:
            # 获取任务列表
            api_url = 'https://www.googleapis.com/tasks/v1/users/@me/lists'
            headers = {
                'Authorization': token.authorization_header,
                'Accept': 'application/json'
            }

            response = requests.get(api_url, headers=headers)
            if response.status_code != 200:
                logger.error(f"获取任务列表失败: {response.status_code}")
                return []

            lists_data = response.json()
            if not lists_data.get('items'):
                logger.warning("没有找到任务列表")
                return []

            # 使用第一个列表
            list_id = lists_data['items'][0]['id']

            # 获取任务数据
            tasks_url = f'https://www.googleapis.com/tasks/v1/lists/{list_id}/tasks'

            # 添加时间范围过滤
            since_date = datetime.now() - timedelta(days=days_back)
            params = {
                'showCompleted': 'true',
                'showHidden': 'true',
                'maxResults': 1000,
                'updatedMin': since_date.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            }

            response = requests.get(tasks_url, headers=headers, params=params)
            if response.status_code != 200:
                logger.error(f"获取任务失败: {response.status_code}")
                return []

            tasks_data = response.json()
            tasks = tasks_data.get('items', [])

            # 过滤出习惯相关的任务
            habit_tasks = []
            for task in tasks:
                if self._is_habit_task(task):
                    habit_tasks.append(task)

            logger.info(f"找到 {len(habit_tasks)} 个习惯任务")
            return habit_tasks

        except Exception as e:
            logger.error(f"获取Google Tasks数据失败: {e}")
            return []

    def _is_habit_task(self, task: Dict[str, Any]) -> bool:
        """判断是否为习惯任务"""
        title = task.get('title', '')
        notes = task.get('notes', '')

        # 检查是否包含习惯标识
        return ('习惯ID:' in notes or
                '⏰' in title or
                any(habit in title for habit in ['睡前阅读', '早起开电脑', '查看TWL']))

    def _extract_habit_info(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """从任务中提取习惯信息"""
        notes = task.get('notes', '')
        title = task.get('title', '')

        # 提取习惯ID
        habit_id_match = re.search(r'习惯ID: ([a-f0-9-]+)', notes)
        habit_id = habit_id_match.group(1) if habit_id_match else None

        # 提取日期
        date_match = re.search(r'日期: (\d{4}-\d{2}-\d{2})', notes)
        task_date = date_match.group(1) if date_match else None

        # 提取习惯名称
        habit_name = title.replace('⏰', '').strip()
        if ' - ' in habit_name:
            habit_name = habit_name.split(' - ', 1)[1]

        # 完成状态
        is_completed = task.get('status') == 'completed'
        completed_at = task.get('completed') if is_completed else None

        return {
            'habit_id': habit_id,
            'habit_name': habit_name,
            'task_date': task_date,
            'is_completed': is_completed,
            'completed_at': completed_at,
            'task_title': title,
            'notes': notes
        }

    def generate_habit_overview(self, habit_tasks: List[Dict[str, Any]]) -> str:
        """生成习惯总览报告"""

        # 基础报告头部 - 总是显示当前习惯设置
        report = f"""# 🏃‍♂️ 习惯追踪总览

> 📅 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
> 📊 统计周期: 最近30天

## 📋 当前习惯设置

✅ **早上吃维生素** (08:30) - 健康类，1分钟
   - 提示：刷牙后
   - 行为：吃一颗复合维生素
   - 奖励：为健康打卡

✅ **有氧运动15分钟** (18:00) - 健康类，15分钟
   - 提示：换运动服后
   - 行为：跑步、快走或骑车15分钟
   - 奖励：感受内啡肽释放

✅ **睡前阅读5分钟** (22:30) - 学习类，5分钟
   - 提示：刷牙后躺床上
   - 行为：阅读书籍、文章或电子书
   - 奖励：放松心情助眠

## 📈 习惯完成情况

"""

        if not habit_tasks:
            report += """暂无完成数据，请在Google Tasks中完成习惯任务后数据会自动同步。

## 📅 最近7天习惯日历

| 日期 | 早上吃维生素 | 有氧运动15分钟 | 睡前阅读5分钟 |
|------|--------------|----------------|---------------|
| 09-09 | ➖ | ➖ | ➖ |
| 09-10 | ➖ | ➖ | ➖ |
| 09-11 | ➖ | ➖ | ➖ |
| 09-12 | ➖ | ➖ | ➖ |
| 09-13 | ➖ | ➖ | ➖ |
| 09-14 | ➖ | ➖ | ➖ |
| 09-15 | ➖ | ➖ | ➖ |

> 💡 **使用说明**：
> 1. 每天早上6:30系统会自动在Google Tasks中创建习惯任务
> 2. 在手机或网页版Google Tasks中点击完成任务
> 3. 每2小时系统会自动同步完成数据到此页面
> 4. 坚持21天养成习惯！🎯
"""
            return report

        # 按习惯分组
        habits_data = {}
        for task in habit_tasks:
            habit_info = self._extract_habit_info(task)
            habit_name = habit_info['habit_name']

            if habit_name not in habits_data:
                habits_data[habit_name] = {
                    'total_tasks': 0,
                    'completed_tasks': 0,
                    'recent_completions': [],
                    'streak': 0,
                    'max_streak': 0
                }

            habits_data[habit_name]['total_tasks'] += 1
            if habit_info['is_completed']:
                habits_data[habit_name]['completed_tasks'] += 1
                habits_data[habit_name]['recent_completions'].append(habit_info['task_date'])

        # 计算连续天数
        for habit_name, data in habits_data.items():
            data['completion_rate'] = (data['completed_tasks'] / data['total_tasks'] * 100) if data['total_tasks'] > 0 else 0
            data['recent_completions'].sort()
            data['streak'] = self._calculate_current_streak(data['recent_completions'])
            data['max_streak'] = self._calculate_max_streak(data['recent_completions'])

        # 继续处理有数据的情况

        for habit_name, data in habits_data.items():
            completion_rate = data['completion_rate']

            # 生成进度条
            progress_bar = self._generate_progress_bar(completion_rate)

            # 状态emoji
            if completion_rate >= 80:
                status_emoji = "🔥"
            elif completion_rate >= 60:
                status_emoji = "✅"
            elif completion_rate >= 40:
                status_emoji = "⚠️"
            else:
                status_emoji = "❌"

            report += f"""### {status_emoji} {habit_name}

- **完成率**: {completion_rate:.1f}% ({data['completed_tasks']}/{data['total_tasks']})
- **连续天数**: {data['streak']} 天
- **最长连续**: {data['max_streak']} 天

{progress_bar}

"""

        # 添加详细数据
        report += self._generate_habit_calendar(habits_data)

        return report

    def _generate_progress_bar(self, percentage: float, length: int = 20) -> str:
        """生成进度条"""
        filled = int(percentage / 100 * length)
        empty = length - filled
        return f"`{'█' * filled}{'░' * empty}` {percentage:.1f}%"

    def _calculate_current_streak(self, completion_dates: List[str]) -> int:
        """计算当前连续天数"""
        if not completion_dates:
            return 0

        completion_dates.sort(reverse=True)
        today = datetime.now().date()
        streak = 0

        for i, date_str in enumerate(completion_dates):
            if not date_str:
                continue

            completion_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            expected_date = today - timedelta(days=i)

            if completion_date == expected_date:
                streak += 1
            else:
                break

        return streak

    def _calculate_max_streak(self, completion_dates: List[str]) -> int:
        """计算历史最长连续天数"""
        if not completion_dates:
            return 0

        completion_dates = [datetime.strptime(d, '%Y-%m-%d').date() for d in completion_dates if d]
        completion_dates.sort()

        max_streak = 1
        current_streak = 1

        for i in range(1, len(completion_dates)):
            if completion_dates[i] - completion_dates[i-1] == timedelta(days=1):
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 1

        return max_streak

    def _generate_habit_calendar(self, habits_data: Dict[str, Dict]) -> str:
        """生成习惯日历视图"""
        calendar_section = """
## 📅 最近7天习惯日历

| 日期 | 早上吃维生素 | 有氧运动15分钟 | 睡前阅读5分钟 |
|------|--------------|----------------|---------------|
"""

        # 生成最近7天的数据
        for i in range(6, -1, -1):
            date = datetime.now().date() - timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')
            row = f"| {date.strftime('%m-%d')} |"

            for habit_name in ["早上吃维生素", "有氧运动15分钟", "睡前阅读5分钟"]:
                if habit_name in habits_data:
                    if date_str in habits_data[habit_name].get('recent_completions', []):
                        row += " ✅ |"
                    else:
                        row += " ❌ |"
                else:
                    row += " ➖ |"

            calendar_section += row + "\n"

        return calendar_section

    def sync_to_obsidian(self, days_back: int = 30) -> bool:
        """同步习惯数据到Obsidian"""
        try:
            logger.info("开始同步习惯数据到Obsidian")

            # 获取Google Tasks数据
            habit_tasks = self.get_google_tasks_data(days_back)

            # 生成总览报告
            overview_content = self.generate_habit_overview(habit_tasks)

            # 写入Obsidian文件
            overview_file = self.habits_folder / "习惯追踪总览.md"
            with open(overview_file, 'w', encoding='utf-8') as f:
                f.write(overview_content)

            logger.info(f"习惯总览已更新: {overview_file}")

            # 为每个习惯创建详细页面
            self._create_individual_habit_pages(habit_tasks)

            return True

        except Exception as e:
            logger.error(f"同步到Obsidian失败: {e}")
            return False

    def _create_individual_habit_pages(self, habit_tasks: List[Dict[str, Any]]):
        """为每个习惯创建详细页面"""
        habits_by_name = {}

        for task in habit_tasks:
            habit_info = self._extract_habit_info(task)
            habit_name = habit_info['habit_name']

            if habit_name not in habits_by_name:
                habits_by_name[habit_name] = []
            habits_by_name[habit_name].append(habit_info)

        for habit_name, habit_records in habits_by_name.items():
            self._create_habit_detail_page(habit_name, habit_records)

    def _create_habit_detail_page(self, habit_name: str, records: List[Dict[str, Any]]):
        """创建单个习惯的详细页面"""
        records.sort(key=lambda x: x['task_date'] or '', reverse=True)

        content = f"""# 📊 {habit_name} - 详细记录

> 📅 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📈 统计信息

- **总记录数**: {len(records)}
- **完成次数**: {sum(1 for r in records if r['is_completed'])}
- **完成率**: {(sum(1 for r in records if r['is_completed']) / len(records) * 100):.1f}%

## 📅 完成记录

| 日期 | 状态 | 完成时间 |
|------|------|----------|
"""

        for record in records:
            status = "✅ 已完成" if record['is_completed'] else "❌ 未完成"
            completed_time = ""

            if record['completed_at']:
                try:
                    completed_dt = datetime.fromisoformat(record['completed_at'].replace('Z', '+00:00'))
                    completed_time = completed_dt.strftime('%H:%M')
                except:
                    completed_time = "未知"

            content += f"| {record['task_date']} | {status} | {completed_time} |\n"

        # 保存到文件
        filename = f"{habit_name.replace('/', '_')}.md"
        habit_file = self.habits_folder / filename

        with open(habit_file, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"习惯详细页面已更新: {habit_file}")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='同步习惯数据到Obsidian')
    parser.add_argument('--days', type=int, default=30, help='回溯天数')
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

    # 执行同步
    try:
        syncer = HabitTrackingSync()
        success = syncer.sync_to_obsidian(args.days)

        if success:
            print("✅ 习惯数据已成功同步到Obsidian")
            return 0
        else:
            print("❌ 同步失败")
            return 1

    except Exception as e:
        print(f"❌ 同步过程出错: {e}")
        return 1


if __name__ == "__main__":
    exit(main())