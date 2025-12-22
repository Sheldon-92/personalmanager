"""每日任务追踪存储系统

追踪每日任务完成状态，特别是未完成任务的延续
"""

import json
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import structlog

logger = structlog.get_logger()


@dataclass
class DailyTaskRecord:
    """每日任务记录"""
    task_id: str
    title: str
    category: str  # habit, event, task
    due_date: Optional[str] = None
    planned_date: str = None  # 计划执行日期
    completed: bool = False
    completed_at: Optional[str] = None
    carried_over_from: Optional[str] = None  # 从哪天延续过来的
    notes: Optional[str] = None
    source_id: Optional[str] = None  # Google Tasks ID

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DailyTaskRecord':
        return cls(**data)


class DailyTaskTracker:
    """每日任务追踪器"""

    def __init__(self, data_dir: Optional[Path] = None):
        """初始化追踪器

        Args:
            data_dir: 数据存储目录，默认为 ~/.personalmanager/data/daily_tasks
        """
        if data_dir is None:
            data_dir = Path.home() / ".personalmanager" / "data" / "daily_tasks"

        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)

        logger.info("Daily task tracker initialized", data_dir=str(self.data_dir))

    def _get_date_file(self, date_str: str) -> Path:
        """获取指定日期的数据文件路径"""
        return self.data_dir / f"{date_str}.json"

    def save_daily_tasks(self, date_str: str, tasks: List[DailyTaskRecord]) -> bool:
        """保存某天的任务记录

        Args:
            date_str: 日期字符串 (YYYY-MM-DD)
            tasks: 任务记录列表

        Returns:
            是否保存成功
        """
        try:
            file_path = self._get_date_file(date_str)

            data = {
                "date": date_str,
                "updated_at": datetime.now().isoformat(),
                "tasks": [task.to_dict() for task in tasks]
            }

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info("Daily tasks saved", date=date_str, task_count=len(tasks))
            return True

        except Exception as e:
            logger.error("Failed to save daily tasks", date=date_str, error=str(e))
            return False

    def load_daily_tasks(self, date_str: str) -> List[DailyTaskRecord]:
        """加载某天的任务记录

        Args:
            date_str: 日期字符串 (YYYY-MM-DD)

        Returns:
            任务记录列表
        """
        try:
            file_path = self._get_date_file(date_str)

            if not file_path.exists():
                return []

            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            tasks = [DailyTaskRecord.from_dict(task_data)
                    for task_data in data.get("tasks", [])]

            logger.info("Daily tasks loaded", date=date_str, task_count=len(tasks))
            return tasks

        except Exception as e:
            logger.error("Failed to load daily tasks", date=date_str, error=str(e))
            return []

    def get_incomplete_tasks(self, date_str: str) -> List[DailyTaskRecord]:
        """获取某天未完成的任务

        Args:
            date_str: 日期字符串 (YYYY-MM-DD)

        Returns:
            未完成任务列表
        """
        tasks = self.load_daily_tasks(date_str)
        incomplete = [task for task in tasks if not task.completed]

        logger.info("Incomplete tasks retrieved",
                   date=date_str,
                   incomplete_count=len(incomplete),
                   total_count=len(tasks))

        return incomplete

    def get_carried_over_tasks(self, from_date: str, to_date: str) -> List[DailyTaskRecord]:
        """获取需要延续到新日期的任务

        Args:
            from_date: 源日期 (YYYY-MM-DD)
            to_date: 目标日期 (YYYY-MM-DD)

        Returns:
            需要延续的任务列表
        """
        incomplete = self.get_incomplete_tasks(from_date)

        # 为延续任务更新信息
        carried_over = []
        for task in incomplete:
            # 排除习惯类任务（习惯每天重新开始）
            if task.category == "habit":
                continue

            carried_task = DailyTaskRecord(
                task_id=task.task_id,
                title=task.title,
                category=task.category,
                due_date=task.due_date,
                planned_date=to_date,
                completed=False,
                carried_over_from=from_date if not task.carried_over_from else task.carried_over_from,
                notes=f"延续自 {from_date}",
                source_id=task.source_id
            )
            carried_over.append(carried_task)

        logger.info("Tasks carried over",
                   from_date=from_date,
                   to_date=to_date,
                   carried_count=len(carried_over))

        return carried_over

    def ensure_today_tasks(self) -> bool:
        """确保今天有任务文件，创建全新的习惯任务（不延续）

        Returns:
            是否成功创建或已存在
        """
        from datetime import datetime, timedelta

        today = datetime.now().date()
        today_str = today.isoformat()
        yesterday = today - timedelta(days=1)
        yesterday_str = yesterday.isoformat()

        # 检查今天的文件是否已存在
        today_file = self.data_dir / f"{today_str}.json"
        if today_file.exists():
            logger.debug("Today's tasks file already exists", date=today_str)
            return True

        logger.info("Creating today's tasks file", date=today_str)

        # 今天的任务列表
        today_tasks = []

        # 1. 延续昨天未完成的普通任务（不包括习惯任务）
        if (self.data_dir / f"{yesterday_str}.json").exists():
            incomplete = self.get_incomplete_tasks(yesterday_str)
            for task in incomplete:
                # 习惯任务不延续，每天重新生成
                if task.category != "habit" and not task.completed:
                    carried_task = DailyTaskRecord(
                        task_id=f"{task.task_id}_carried" if not task.task_id.endswith("_carried") else task.task_id,
                        title=task.title,
                        category=task.category,
                        due_date=task.due_date,
                        planned_date=today_str,
                        completed=False,
                        carried_over_from=yesterday_str,
                        notes=f"延续自 {yesterday_str}",
                        source_id=task.source_id
                    )
                    today_tasks.append(carried_task)

            logger.info("Carried over non-habit tasks from yesterday",
                       date=today_str,
                       count=len(today_tasks))

        # 2. 生成今天全新的习惯任务
        self._create_fresh_habit_tasks(today_str, today_tasks)

        # 保存今天的任务
        self.save_daily_tasks(today_str, today_tasks)

        return True

    def _create_fresh_habit_tasks(self, date_str: str, existing_tasks: List[DailyTaskRecord]) -> None:
        """为今天创建全新的习惯任务

        Args:
            date_str: 日期字符串
            existing_tasks: 已存在的任务列表（会被修改）
        """
        try:
            # 从习惯存储加载所有活跃习惯
            from pm.storage.habit_storage import HabitStorage
            from pm.core.config import PMConfig

            config = PMConfig()
            habit_storage = HabitStorage(config=config)
            habits = habit_storage.get_all_habits()

            for habit in habits:
                if not habit.active:
                    continue

                # 每个习惯每天都生成全新的任务
                habit_task = DailyTaskRecord(
                    task_id=f"habit_{habit.id}_{date_str}",
                    title=habit.name,
                    category="habit",
                    due_date=None,
                    planned_date=date_str,
                    completed=False,
                    notes=f"习惯任务 - {habit.description or habit.name}",
                    source_id=f"habit_{habit.id}"
                )
                existing_tasks.append(habit_task)
                logger.info("Created fresh habit task",
                           date=date_str,
                           habit_name=habit.name)

            logger.info("Created all habit tasks for today",
                       date=date_str,
                       habit_count=len([h for h in habits if h.active]))

        except Exception as e:
            logger.error("Failed to create habit tasks",
                        date=date_str,
                        error=str(e))

    def _ensure_habit_tasks(self, date_str: str, existing_tasks: List[DailyTaskRecord]) -> None:
        """已废弃 - 请使用 _create_fresh_habit_tasks
        保留此方法以兼容旧代码
        """
        self._create_fresh_habit_tasks(date_str, existing_tasks)

    def update_task_status(self, date_str: str, task_id: str, completed: bool) -> bool:
        """更新任务完成状态

        Args:
            date_str: 日期字符串
            task_id: 任务ID
            completed: 是否完成

        Returns:
            是否更新成功
        """
        tasks = self.load_daily_tasks(date_str)

        updated = False
        for task in tasks:
            if task.task_id == task_id:
                task.completed = completed
                if completed:
                    task.completed_at = datetime.now().isoformat()
                else:
                    task.completed_at = None
                updated = True
                break

        if updated:
            self.save_daily_tasks(date_str, tasks)
            logger.info("Task status updated",
                       date=date_str,
                       task_id=task_id,
                       completed=completed)

        return updated

    def get_task_summary(self, date_str: str) -> Dict[str, Any]:
        """获取某天任务摘要

        Args:
            date_str: 日期字符串

        Returns:
            任务摘要信息
        """
        tasks = self.load_daily_tasks(date_str)

        # 按分类分组
        habits = [t for t in tasks if t.category == "habit"]
        events = [t for t in tasks if t.category == "event"]
        normal_tasks = [t for t in tasks if t.category == "task"]

        # 分别统计完成情况
        summary = {
            "date": date_str,
            "total_count": len(tasks),
            "completed_count": len([t for t in tasks if t.completed]),
            "habits": {
                "tasks": habits,
                "completed": [t for t in habits if t.completed],
                "incomplete": [t for t in habits if not t.completed]
            },
            "events": {
                "tasks": events,
                "completed": [t for t in events if t.completed],
                "incomplete": [t for t in events if not t.completed]
            },
            "tasks": {
                "tasks": normal_tasks,
                "completed": [t for t in normal_tasks if t.completed],
                "incomplete": [t for t in normal_tasks if not t.completed]
            },
            "carried_over": [t for t in tasks if t.carried_over_from]
        }

        return summary

    def sync_from_google_tasks(self, google_tasks: List, date_str: Optional[str] = None) -> int:
        """从Google Tasks同步任务到每日追踪

        Args:
            google_tasks: Google Tasks任务列表
            date_str: 日期字符串，默认为今天

        Returns:
            同步的任务数量
        """
        if date_str is None:
            date_str = date.today().isoformat()

        # 获取现有任务（保留完成状态）
        existing_tasks = self.load_daily_tasks(date_str)
        existing_by_id = {t.source_id: t for t in existing_tasks if t.source_id}

        # 转换Google Tasks为记录
        daily_records = []
        for gt in google_tasks:
            # 获取分类
            category = gt.get_task_category()

            # 检查是否已存在
            if gt.task_id in existing_by_id:
                # 更新现有任务
                record = existing_by_id[gt.task_id]
                record.title = gt.get_clean_title()
                record.completed = gt.is_completed
                if gt.is_completed and gt.completed:
                    record.completed_at = gt.completed.isoformat()
            else:
                # 创建新记录
                record = DailyTaskRecord(
                    task_id=f"gt_{gt.task_id[:8]}",
                    title=gt.get_clean_title(),
                    category=category.value,
                    due_date=gt.due.isoformat() if gt.due else None,
                    planned_date=date_str,
                    completed=gt.is_completed,
                    completed_at=gt.completed.isoformat() if gt.completed else None,
                    source_id=gt.task_id
                )

            daily_records.append(record)

        # 保存记录
        self.save_daily_tasks(date_str, daily_records)

        logger.info("Synced from Google Tasks",
                   date=date_str,
                   task_count=len(daily_records))

        return len(daily_records)