"""NextSyncManager - Bidirectional sync between NEXT.md and Google Tasks

Provides push/pull functionality for syncing tasks across projects.
"""

import re
from datetime import date, datetime
from pathlib import Path
from typing import Optional, Set

import structlog

from pm.core.config import PMConfig
from pm.integrations.google_tasks import GoogleTasksIntegration
from pm.parsers.next_md_parser import (
    NextMdParser,
    NextTask,
    NextMdFile,
    SyncStats,
    TaskPriority,
)

logger = structlog.get_logger()


class NextSyncManager:
    """Manager for syncing NEXT.md files with Google Tasks"""

    GOOGLE_LIST_NAME = "NEXT Tasks"
    MASTER_FILE_NAME = "MASTER.md"

    def __init__(self, config: PMConfig, projects_path: str = "~/programs"):
        """Initialize sync manager

        Args:
            config: PMConfig instance
            projects_path: Path to directory containing project folders
        """
        self.config = config
        self.projects_path = Path(projects_path).expanduser()
        self.parser = NextMdParser()
        self.google_tasks = GoogleTasksIntegration(config)

        # MASTER.md location (in personal-manager project root)
        self.master_path = Path(__file__).parent.parent.parent.parent / self.MASTER_FILE_NAME

    def push(self) -> SyncStats:
        """Push tasks from all NEXT.md files to Google Tasks

        Flow:
        1. Scan all projects for NEXT.md
        2. Generate MASTER.md with aggregated tasks
        3. Push to Google Tasks "NEXT Tasks" list
        4. Skip duplicate tasks

        Returns:
            SyncStats with operation statistics
        """
        stats = SyncStats()

        logger.info("Starting push sync", projects_path=str(self.projects_path))

        # Step 1: Scan all projects
        next_files = self.parser.scan_projects(self.projects_path)
        stats.projects_scanned = len(next_files)

        if not next_files:
            stats.add_error(f"No NEXT.md files found in {self.projects_path}")
            return stats

        # Collect all pending tasks
        all_tasks = []
        for next_file in next_files:
            for task in next_file.pending_tasks:
                all_tasks.append(task)
                stats.tasks_found += 1

        logger.info("Found tasks to push",
                   projects=stats.projects_scanned,
                   tasks=stats.tasks_found)

        # Step 2: Generate MASTER.md
        self._generate_master_md(all_tasks)

        # Step 3: Get or create Google Tasks list
        list_id = self.google_tasks.find_or_create_task_list(self.GOOGLE_LIST_NAME)
        if not list_id:
            stats.add_error("Failed to create/find Google Tasks list")
            return stats

        # Step 4: Get existing tasks for deduplication
        existing_tasks = self.google_tasks.get_tasks_from_list(list_id)
        existing_titles = {t.title.lower() for t in existing_tasks}

        # Step 5: Push tasks (skip duplicates)
        for task in all_tasks:
            google_title = task.formatted_title

            if google_title.lower() in existing_titles:
                stats.tasks_skipped += 1
                logger.debug("Skipping duplicate task", title=google_title)
                continue

            success, result = self.google_tasks.create_task(
                list_id=list_id,
                title=google_title,
                notes=f"Project: {task.project}\nPriority: {task.priority.value}",
                due_date=task.due_date
            )

            if success:
                stats.tasks_pushed += 1
                existing_titles.add(google_title.lower())
                logger.info("Pushed task", title=google_title)
            else:
                stats.add_error(f"Failed to push: {task.title} - {result}")

        logger.info("Push sync completed",
                   pushed=stats.tasks_pushed,
                   skipped=stats.tasks_skipped,
                   errors=len(stats.errors))

        return stats

    def pull(self) -> SyncStats:
        """Pull completed tasks from Google Tasks and update NEXT.md files

        Flow:
        1. Get completed tasks from "NEXT Tasks" list
        2. Parse project name from task title [project]
        3. Update corresponding NEXT.md files
        4. Move completed tasks to "已完成" section

        Returns:
            SyncStats with operation statistics
        """
        stats = SyncStats()

        logger.info("Starting pull sync")

        # Step 1: Find the NEXT Tasks list
        list_id = self._find_next_tasks_list()
        if not list_id:
            stats.add_error("NEXT Tasks list not found in Google Tasks")
            return stats

        # Step 2: Get completed tasks
        completed_tasks = self.google_tasks.get_completed_tasks(list_id)

        if not completed_tasks:
            logger.info("No completed tasks to pull")
            return stats

        stats.tasks_pulled = len(completed_tasks)

        # Step 3: Parse and distribute to projects
        project_pattern = re.compile(r'^\[([^\]]+)\]\s*(.+)$')

        for google_task in completed_tasks:
            match = project_pattern.match(google_task.title)
            if not match:
                logger.warning("Cannot parse project from task title",
                             title=google_task.title)
                continue

            project_name, task_title = match.groups()
            next_file_path = self.projects_path / project_name / "NEXT.md"

            if not next_file_path.exists():
                logger.warning("NEXT.md not found for project",
                             project=project_name)
                continue

            # Update the NEXT.md file
            completed_date = google_task.completed.date() if google_task.completed else date.today()

            if self.parser.update_task_completion(
                next_file_path,
                task_title.strip(),
                completed_date
            ):
                stats.tasks_updated += 1
                logger.info("Updated task completion",
                           project=project_name,
                           task=task_title)
            else:
                stats.add_error(f"Failed to update: {project_name}/{task_title}")

        # Step 4: Update MASTER.md
        self._update_master_md_completions()

        logger.info("Pull sync completed",
                   pulled=stats.tasks_pulled,
                   updated=stats.tasks_updated,
                   errors=len(stats.errors))

        return stats

    def _find_next_tasks_list(self) -> Optional[str]:
        """Find the NEXT Tasks list ID"""
        task_lists = self.google_tasks.get_google_tasks_lists()
        for task_list in task_lists:
            if task_list.get('title', '').lower() == self.GOOGLE_LIST_NAME.lower():
                return task_list['id']
        return None

    def _generate_master_md(self, tasks: list[NextTask]) -> None:
        """Generate MASTER.md file with aggregated tasks

        Args:
            tasks: List of NextTask objects from all projects
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        # Group tasks by priority
        by_priority = {
            TaskPriority.TODAY: [],
            TaskPriority.THIS_WEEK: [],
            TaskPriority.BLOCKED: [],
            TaskPriority.SOMEDAY: [],
        }

        for task in tasks:
            if task.priority in by_priority:
                by_priority[task.priority].append(task)

        # Build MASTER.md content
        lines = [
            "# MASTER - 跨项目任务汇总",
            "",
            f"*自动生成于 {now}*",
            "",
        ]

        # Add sections
        section_names = {
            TaskPriority.TODAY: "今天",
            TaskPriority.THIS_WEEK: "本周",
            TaskPriority.BLOCKED: "阻塞",
            TaskPriority.SOMEDAY: "待定",
        }

        for priority in [TaskPriority.TODAY, TaskPriority.THIS_WEEK,
                        TaskPriority.BLOCKED, TaskPriority.SOMEDAY]:
            section_tasks = by_priority[priority]
            if section_tasks:
                lines.append(f"## {section_names[priority]}")
                for task in section_tasks:
                    date_suffix = ""
                    if task.due_date:
                        date_suffix = f" @{task.due_date.strftime('%m-%d')}"
                    lines.append(f"- [ ] [{task.project}] {task.title}{date_suffix}")
                lines.append("")

        # Add placeholder for completed section
        lines.extend([
            "## 已完成",
            f"### {datetime.now().strftime('%Y-W%W')}",
            "",
        ])

        # Write MASTER.md
        try:
            self.master_path.write_text('\n'.join(lines), encoding='utf-8')
            logger.info("Generated MASTER.md", path=str(self.master_path))
        except Exception as e:
            logger.error("Failed to write MASTER.md", error=str(e))

    def _update_master_md_completions(self) -> None:
        """Update MASTER.md with completed tasks from all projects"""
        if not self.master_path.exists():
            return

        try:
            # Re-scan all projects for completed tasks
            next_files = self.parser.scan_projects(self.projects_path)

            completed_tasks = []
            for next_file in next_files:
                for task in next_file.completed_tasks:
                    completed_tasks.append(task)

            if not completed_tasks:
                return

            # Read current MASTER.md
            content = self.master_path.read_text(encoding='utf-8')
            lines = content.split('\n')

            # Find completed section
            completed_idx = -1
            for i, line in enumerate(lines):
                if line.strip().startswith('## 已完成'):
                    completed_idx = i
                    break

            if completed_idx < 0:
                # Add completed section
                lines.extend(["", "## 已完成", f"### {datetime.now().strftime('%Y-W%W')}"])
                completed_idx = len(lines) - 1

            # Add completed tasks
            week_header = f"### {datetime.now().strftime('%Y-W%W')}"
            week_idx = -1
            for i in range(completed_idx, len(lines)):
                if lines[i].strip() == week_header:
                    week_idx = i
                    break

            if week_idx < 0:
                lines.insert(completed_idx + 1, week_header)
                week_idx = completed_idx + 1

            # Add completed tasks after week header
            for task in completed_tasks:
                date_str = task.completed_date.strftime("%m-%d") if task.completed_date else ""
                completed_line = f"- [x] [{task.project}] {task.title} ✓{date_str}"
                # Check if already exists
                if completed_line not in lines:
                    lines.insert(week_idx + 1, completed_line)

            self.master_path.write_text('\n'.join(lines), encoding='utf-8')

        except Exception as e:
            logger.error("Failed to update MASTER.md completions", error=str(e))
