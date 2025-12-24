"""NEXT.md Parser - Parse and manipulate NEXT.md files

Provides data models and parsing logic for NEXT.md task files.
"""

import re
from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum
from pathlib import Path
from typing import List, Optional


class TaskPriority(Enum):
    """Task priority levels based on NEXT.md sections"""
    TODAY = "今天"
    THIS_WEEK = "本周"
    SOMEDAY = "待定"
    BLOCKED = "阻塞"
    COMPLETED = "已完成"


@dataclass
class NextTask:
    """Represents a task from NEXT.md"""
    title: str
    project: str
    priority: TaskPriority
    is_completed: bool = False
    completed_date: Optional[date] = None
    line_number: int = 0

    @property
    def due_date(self) -> Optional[date]:
        """Calculate due date based on priority"""
        if self.priority == TaskPriority.TODAY:
            return date.today()
        elif self.priority == TaskPriority.THIS_WEEK:
            # Return this Friday
            today = date.today()
            days_until_friday = (4 - today.weekday()) % 7
            if days_until_friday == 0 and today.weekday() != 4:
                days_until_friday = 7
            return today + timedelta(days=days_until_friday)
        else:
            # SOMEDAY, BLOCKED have no due date
            return None

    @property
    def formatted_title(self) -> str:
        """Format title with project prefix"""
        return f"[{self.project}] {self.title}"

    @property
    def unique_key(self) -> str:
        """Unique identifier for deduplication"""
        return f"{self.project}::{self.title}".lower()

    def to_google_task_title(self) -> str:
        """Format for Google Tasks"""
        return self.formatted_title


@dataclass
class NextMdFile:
    """Represents a parsed NEXT.md file"""
    project_name: str
    file_path: Path
    tasks: List[NextTask] = field(default_factory=list)

    @property
    def pending_tasks(self) -> List[NextTask]:
        """Get uncompleted tasks"""
        return [t for t in self.tasks if not t.is_completed]

    @property
    def completed_tasks(self) -> List[NextTask]:
        """Get completed tasks"""
        return [t for t in self.tasks if t.is_completed]


@dataclass
class SyncStats:
    """Statistics for sync operations"""
    projects_scanned: int = 0
    tasks_found: int = 0
    tasks_pushed: int = 0
    tasks_skipped: int = 0
    tasks_pulled: int = 0
    tasks_updated: int = 0
    errors: List[str] = field(default_factory=list)

    def add_error(self, error: str):
        """Add an error message"""
        self.errors.append(error)

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0


class NextMdParser:
    """Parser for NEXT.md files"""

    # Section header patterns (case insensitive)
    SECTION_PATTERNS = {
        TaskPriority.TODAY: ['今天', 'today'],
        TaskPriority.THIS_WEEK: ['本周', 'week', 'this week'],
        TaskPriority.SOMEDAY: ['待定', 'someday', 'later'],
        TaskPriority.BLOCKED: ['阻塞', 'blocked', 'waiting', '等待'],
        TaskPriority.COMPLETED: ['已完成', 'completed', 'done'],
    }

    # Task line pattern: - [ ] or - [x]
    TASK_PATTERN = re.compile(r'^-\s*\[([ xX])\]\s*(.+)$')

    # Completed date pattern: ✓MM-DD or vMM-DD
    COMPLETED_DATE_PATTERN = re.compile(r'[✓v](\d{1,2})-(\d{1,2})$')

    def parse_file(self, file_path: Path, project_name: str) -> NextMdFile:
        """Parse a single NEXT.md file

        Args:
            file_path: Path to NEXT.md file
            project_name: Name of the project

        Returns:
            NextMdFile with parsed tasks
        """
        result = NextMdFile(
            project_name=project_name,
            file_path=file_path,
            tasks=[]
        )

        if not file_path.exists():
            return result

        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception:
            return result

        current_priority = None
        in_completed_section = False

        for line_num, line in enumerate(content.split('\n'), start=1):
            stripped = line.strip()

            # Check for section headers
            if stripped.startswith('## '):
                section_title = stripped[3:].strip().lower()
                current_priority = self._detect_section(section_title)
                in_completed_section = (current_priority == TaskPriority.COMPLETED)
                continue

            # Parse task lines
            if current_priority and not in_completed_section:
                task = self._parse_task_line(
                    stripped, project_name, current_priority, line_num
                )
                if task:
                    result.tasks.append(task)

            # Parse completed tasks (for pull sync)
            elif in_completed_section:
                task = self._parse_task_line(
                    stripped, project_name, TaskPriority.COMPLETED, line_num,
                    expect_completed=True
                )
                if task:
                    result.tasks.append(task)

        return result

    def scan_projects(self, base_path: Path) -> List[NextMdFile]:
        """Scan all projects under base_path for NEXT.md files

        Args:
            base_path: Directory containing project folders

        Returns:
            List of parsed NextMdFile objects
        """
        results = []

        if not base_path.exists() or not base_path.is_dir():
            return results

        for item in base_path.iterdir():
            if not item.is_dir():
                continue

            next_file = item / "NEXT.md"
            if next_file.exists():
                parsed = self.parse_file(next_file, item.name)
                results.append(parsed)

        return results

    def _detect_section(self, title: str) -> Optional[TaskPriority]:
        """Detect section type from header text"""
        title_lower = title.lower()

        for priority, keywords in self.SECTION_PATTERNS.items():
            for keyword in keywords:
                if keyword.lower() in title_lower:
                    return priority

        return None

    def _parse_task_line(
        self,
        line: str,
        project_name: str,
        priority: TaskPriority,
        line_number: int,
        expect_completed: bool = False
    ) -> Optional[NextTask]:
        """Parse a single task line

        Args:
            line: The line to parse
            project_name: Name of the project
            priority: Current section priority
            line_number: Line number in file
            expect_completed: Whether to expect completed tasks

        Returns:
            NextTask if line is a valid task, None otherwise
        """
        match = self.TASK_PATTERN.match(line)
        if not match:
            return None

        checkbox, title = match.groups()
        is_completed = checkbox.lower() == 'x'

        # Extract completion date if present
        completed_date = None
        clean_title = title.strip()

        date_match = self.COMPLETED_DATE_PATTERN.search(clean_title)
        if date_match:
            month, day = int(date_match.group(1)), int(date_match.group(2))
            try:
                year = date.today().year
                completed_date = date(year, month, day)
                # Remove date suffix from title
                clean_title = self.COMPLETED_DATE_PATTERN.sub('', clean_title).strip()
            except ValueError:
                pass

        return NextTask(
            title=clean_title,
            project=project_name,
            priority=priority if not is_completed else TaskPriority.COMPLETED,
            is_completed=is_completed,
            completed_date=completed_date,
            line_number=line_number
        )

    def update_task_completion(
        self,
        file_path: Path,
        task_title: str,
        completed_date: date
    ) -> bool:
        """Update a task to completed status in NEXT.md file

        Args:
            file_path: Path to NEXT.md file
            task_title: Title of task to mark complete
            completed_date: Date of completion

        Returns:
            True if task was found and updated
        """
        if not file_path.exists():
            return False

        try:
            content = file_path.read_text(encoding='utf-8')
            lines = content.split('\n')
            updated = False
            completed_section_index = -1

            # Find the task and completed section
            for i, line in enumerate(lines):
                stripped = line.strip()

                # Check for completed section
                if stripped.startswith('## '):
                    section_lower = stripped[3:].lower()
                    if any(kw in section_lower for kw in ['已完成', 'completed', 'done']):
                        completed_section_index = i

                # Find and remove the task line
                if not updated and stripped.startswith('- [ ]'):
                    # Check if this is our task (fuzzy match)
                    if task_title.lower() in stripped.lower():
                        lines[i] = ''  # Remove original line
                        updated = True

            if not updated:
                return False

            # Add to completed section
            date_str = completed_date.strftime("%m-%d")
            completed_line = f"- [x] {task_title} ✓{date_str}"

            if completed_section_index > 0:
                # Insert after completed section header
                lines.insert(completed_section_index + 1, completed_line)
            else:
                # Create completed section at end
                lines.append("")
                lines.append("## 已完成")
                lines.append(completed_line)

            # Clean up empty lines and write back
            content = '\n'.join(line for line in lines if line or line == '')
            file_path.write_text(content, encoding='utf-8')

            return True

        except Exception:
            return False
