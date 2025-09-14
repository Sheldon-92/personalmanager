"""
Incremental Report Generator
Handles incremental updates and change tracking for reports
"""

import os
import json
import hashlib
import difflib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum

from jinja2 import Template


class ChangeType(Enum):
    """Types of changes in incremental updates"""
    ADDED = "added"
    MODIFIED = "modified"
    DELETED = "deleted"
    MOVED = "moved"


class ReportFormat(Enum):
    """Supported report output formats"""
    MARKDOWN = "markdown"
    JSON = "json"


@dataclass
class FileChange:
    """Represents a change in a file"""
    file_path: str
    change_type: ChangeType
    old_hash: Optional[str] = None
    new_hash: Optional[str] = None
    old_size: Optional[int] = None
    new_size: Optional[int] = None
    timestamp: Optional[str] = None
    line_changes: Optional[Dict[str, List[str]]] = None


@dataclass
class ReportState:
    """Tracks the state of a report generation"""
    project_path: str
    project_name: str
    report_type: str
    last_generated: str
    last_analysis_hash: str
    file_hashes: Dict[str, str]
    template_version: str
    total_files: int = 0
    total_lines: int = 0


class IncrementalReportGenerator:
    """
    Manages incremental report generation with change tracking and difference highlighting
    """

    def __init__(self, project_path: str, state_dir: Optional[str] = None):
        self.project_path = Path(project_path).resolve()
        self.state_dir = Path(state_dir or self.project_path / ".pm" / "reports")
        self.state_dir.mkdir(parents=True, exist_ok=True)

        # Template directories
        self.template_dir = Path(__file__).parent.parent / "templates"

    def get_state_file(self, report_type: str) -> Path:
        """Get the state file path for a specific report type"""
        return self.state_dir / f"{report_type}_state.json"

    def load_report_state(self, report_type: str) -> Optional[ReportState]:
        """Load the previous report state"""
        state_file = self.get_state_file(report_type)
        if not state_file.exists():
            return None

        try:
            with open(state_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return ReportState(**data)
        except (json.JSONDecodeError, TypeError, KeyError) as e:
            print(f"Warning: Could not load report state: {e}")
            return None

    def save_report_state(self, state: ReportState, report_type: str) -> None:
        """Save the current report state"""
        state_file = self.get_state_file(report_type)
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(state), f, indent=2, ensure_ascii=False)

    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate MD5 hash of a file"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except (IOError, OSError):
            return ""

    def scan_project_files(self, patterns: Optional[List[str]] = None) -> Dict[str, str]:
        """
        Scan project files and return their hashes

        Args:
            patterns: File patterns to include (e.g., ['*.py', '*.md'])

        Returns:
            Dictionary mapping file paths to hashes
        """
        file_hashes = {}
        default_patterns = [
            "*.py", "*.js", "*.ts", "*.jsx", "*.tsx", "*.md", "*.rst", "*.txt",
            "*.yml", "*.yaml", "*.json", "*.toml", "*.cfg", "*.ini"
        ]

        patterns = patterns or default_patterns

        for pattern in patterns:
            for file_path in self.project_path.rglob(pattern):
                if self._should_include_file(file_path):
                    relative_path = str(file_path.relative_to(self.project_path))
                    file_hashes[relative_path] = self.calculate_file_hash(file_path)

        return file_hashes

    def _should_include_file(self, file_path: Path) -> bool:
        """Check if a file should be included in analysis"""
        # Skip hidden files and directories
        if any(part.startswith('.') for part in file_path.parts):
            # Allow .md files and some config files
            if not file_path.suffix in ['.md', '.yml', '.yaml', '.json', '.toml']:
                return False

        # Skip common build/cache directories
        skip_dirs = {
            'node_modules', '__pycache__', '.git', '.venv', 'venv',
            'build', 'dist', '.pytest_cache', '.mypy_cache',
            'coverage', '.coverage', '.tox'
        }

        if any(part in skip_dirs for part in file_path.parts):
            return False

        # Skip very large files (>1MB)
        try:
            if file_path.stat().st_size > 1024 * 1024:
                return False
        except (OSError, IOError):
            return False

        return True

    def detect_changes(self, current_hashes: Dict[str, str],
                      previous_hashes: Dict[str, str]) -> List[FileChange]:
        """Detect changes between current and previous file states"""
        changes = []
        timestamp = datetime.now().isoformat()

        # Find added and modified files
        for file_path, new_hash in current_hashes.items():
            if file_path not in previous_hashes:
                # New file
                changes.append(FileChange(
                    file_path=file_path,
                    change_type=ChangeType.ADDED,
                    new_hash=new_hash,
                    timestamp=timestamp
                ))
            elif previous_hashes[file_path] != new_hash:
                # Modified file
                changes.append(FileChange(
                    file_path=file_path,
                    change_type=ChangeType.MODIFIED,
                    old_hash=previous_hashes[file_path],
                    new_hash=new_hash,
                    timestamp=timestamp
                ))

        # Find deleted files
        for file_path, old_hash in previous_hashes.items():
            if file_path not in current_hashes:
                changes.append(FileChange(
                    file_path=file_path,
                    change_type=ChangeType.DELETED,
                    old_hash=old_hash,
                    timestamp=timestamp
                ))

        return changes

    def generate_incremental_report(self, report_type: str,
                                  template_data: Dict[str, Any],
                                  output_format: ReportFormat = ReportFormat.MARKDOWN) -> Tuple[str, bool]:
        """
        Generate an incremental report

        Args:
            report_type: Type of report ('code' or 'design')
            template_data: Data to populate the template
            output_format: Output format (markdown or json)

        Returns:
            Tuple of (report_content, is_incremental_update)
        """
        # Load previous state
        previous_state = self.load_report_state(report_type)

        # Scan current files
        current_hashes = self.scan_project_files()

        # Detect changes
        changes = []
        is_incremental = False

        if previous_state:
            changes = self.detect_changes(current_hashes, previous_state.file_hashes)
            is_incremental = len(changes) > 0

            # Add line-level changes for modified files
            for change in changes:
                if change.change_type == ChangeType.MODIFIED:
                    change.line_changes = self.analyze_line_changes(
                        change.file_path, change.old_hash, change.new_hash
                    )

        # Prepare template data with change information
        enhanced_data = self._enhance_template_data(
            template_data, changes, is_incremental, previous_state
        )

        # Generate report
        report_content = self._render_template(report_type, enhanced_data, output_format)

        # Update state
        new_state = ReportState(
            project_path=str(self.project_path),
            project_name=enhanced_data.get('project_name', self.project_path.name),
            report_type=report_type,
            last_generated=datetime.now().isoformat(),
            last_analysis_hash=self._calculate_data_hash(enhanced_data),
            file_hashes=current_hashes,
            template_version=enhanced_data.get('template_version', '1.0'),
            total_files=len(current_hashes),
            total_lines=self._count_total_lines(current_hashes)
        )

        self.save_report_state(new_state, report_type)

        return report_content, is_incremental

    def analyze_line_changes(self, file_path: str, old_hash: str, new_hash: str) -> Dict[str, List[str]]:
        """Analyze line-level changes in a file"""
        full_path = self.project_path / file_path

        if not full_path.exists():
            return {"deletions": []}

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                new_lines = f.readlines()
        except (UnicodeDecodeError, IOError):
            return {"modifications": ["Binary file or encoding issue"]}

        # For now, we'll return a simplified analysis
        # In a full implementation, we'd need to store previous versions
        # or use git history to compare
        return {
            "additions": [f"Line analysis not implemented for {file_path}"],
            "modifications": [],
            "deletions": []
        }

    def _enhance_template_data(self, template_data: Dict[str, Any],
                             changes: List[FileChange],
                             is_incremental: bool,
                             previous_state: Optional[ReportState]) -> Dict[str, Any]:
        """Enhance template data with incremental information"""
        enhanced = template_data.copy()

        # Add incremental metadata
        enhanced['has_changes'] = len(changes) > 0
        enhanced['changes_count'] = len(changes)
        enhanced['is_new_analysis'] = previous_state is None
        enhanced['timestamp'] = datetime.now().isoformat()

        if previous_state:
            enhanced['last_analysis_date'] = previous_state.last_generated
            enhanced['last_update_date'] = previous_state.last_generated
            enhanced['last_review_date'] = previous_state.last_generated
        else:
            now = datetime.now().isoformat()
            enhanced['last_analysis_date'] = now
            enhanced['last_update_date'] = now
            enhanced['last_review_date'] = now

        # Add change details
        if changes:
            enhanced['incremental_changes'] = []
            for change in changes:
                change_data = {
                    'change_type': change.change_type.value,
                    'file_path': change.file_path,
                    'file_extension': Path(change.file_path).suffix,
                    'timestamp': change.timestamp
                }

                if change.line_changes:
                    change_data.update({
                        'additions': [{'line_number': i+1, 'content': line.strip()}
                                    for i, line in enumerate(change.line_changes.get('additions', []))],
                        'modifications': [{'line_number': i+1, 'old_content': 'old', 'new_content': line.strip()}
                                        for i, line in enumerate(change.line_changes.get('modifications', []))],
                        'deletions': [{'line_number': i+1, 'content': line.strip()}
                                     for i, line in enumerate(change.line_changes.get('deletions', []))]
                    })

                enhanced['incremental_changes'].append(change_data)

        # Set default values for required template variables
        defaults = {
            'project_name': self.project_path.name,
            'version': '1.0.0',
            'template_version': '1.0',
            'analysis_engine': 'PersonalManager AI',
            'total_files': len(self.scan_project_files()),
            'total_lines': 0,
            'quality_score': 7.5,
            'test_coverage': 75.0,
            'technical_debt_hours': 8.0
        }

        for key, default_value in defaults.items():
            if key not in enhanced:
                enhanced[key] = default_value

        return enhanced

    def _render_template(self, report_type: str, data: Dict[str, Any],
                        output_format: ReportFormat) -> str:
        """Render the report template with data"""
        extension = "md" if output_format == ReportFormat.MARKDOWN else output_format.value
        template_file = f"{report_type}_template.{extension}"
        template_path = self.template_dir / template_file

        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")

        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()

        # Use Jinja2 for templating
        template = Template(template_content)
        return template.render(**data)

    def _calculate_data_hash(self, data: Dict[str, Any]) -> str:
        """Calculate hash of template data for change detection"""
        # Convert to JSON string for consistent hashing
        data_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(data_str.encode('utf-8')).hexdigest()

    def _count_total_lines(self, file_hashes: Dict[str, str]) -> int:
        """Count total lines of code in tracked files"""
        total = 0
        for file_path in file_hashes.keys():
            full_path = self.project_path / file_path
            if full_path.suffix in ['.py', '.js', '.ts', '.jsx', '.tsx']:
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        total += sum(1 for _ in f)
                except (UnicodeDecodeError, IOError):
                    continue
        return total

    def get_change_summary(self, report_type: str) -> Dict[str, Any]:
        """Get a summary of changes since last report"""
        previous_state = self.load_report_state(report_type)
        if not previous_state:
            return {"is_first_run": True}

        current_hashes = self.scan_project_files()
        changes = self.detect_changes(current_hashes, previous_state.file_hashes)

        summary = {
            "is_first_run": False,
            "last_generated": previous_state.last_generated,
            "changes_detected": len(changes),
            "files_added": len([c for c in changes if c.change_type == ChangeType.ADDED]),
            "files_modified": len([c for c in changes if c.change_type == ChangeType.MODIFIED]),
            "files_deleted": len([c for c in changes if c.change_type == ChangeType.DELETED]),
            "total_files_previous": len(previous_state.file_hashes),
            "total_files_current": len(current_hashes)
        }

        return summary


def create_sample_report_data(report_type: str) -> Dict[str, Any]:
    """Create sample data for testing templates"""

    if report_type == "code":
        return {
            "project_name": "PersonalManager",
            "version": "0.2.0",
            "total_files": 45,
            "total_lines": 8500,
            "quality_score": 8.2,
            "test_coverage": 87.5,
            "technical_debt_hours": 12.0,
            "dependencies": [
                {"name": "typer", "version": "0.9.0", "status": "current", "last_updated": "2024-01-15", "security_status": "secure", "license": "MIT"},
                {"name": "rich", "version": "13.7.0", "status": "current", "last_updated": "2024-02-01", "security_status": "secure", "license": "MIT"}
            ],
            "high_priority_recommendations": [
                {"title": "Add error handling", "description": "Improve error handling in API endpoints", "impact": "high", "effort": "medium", "priority": "1"}
            ]
        }

    elif report_type == "design":
        return {
            "project_name": "PersonalManager",
            "version": "0.2.0",
            "architecture_completeness": 85,
            "design_doc_coverage": 78,
            "stakeholder_alignment": 4,
            "design_consistency": 4,
            "core_components": [
                {
                    "name": "CLI Interface",
                    "purpose": "Command-line user interaction",
                    "component_type": "Interface",
                    "status": "stable",
                    "dependencies": ["typer", "rich"],
                    "interface_count": 12
                }
            ],
            "auth_method": "API Key",
            "authz_strategy": "Role-based",
            "encryption_strategy": "AES-256",
            "secret_management": "Environment Variables",
            "security_controls": [
                {
                    "control_name": "Input Validation",
                    "implementation_status": "active",
                    "description": "Validate all user inputs",
                    "coverage_percentage": 90,
                    "last_audit_date": "2024-01-01"
                }
            ]
        }

    return {}


if __name__ == "__main__":
    # Test the incremental report generator
    import sys

    if len(sys.argv) < 2:
        print("Usage: python incremental_report.py <project_path> [report_type] [format]")
        sys.exit(1)

    project_path = sys.argv[1]
    report_type = sys.argv[2] if len(sys.argv) > 2 else "code"
    format_str = sys.argv[3] if len(sys.argv) > 3 else "markdown"

    output_format = ReportFormat.MARKDOWN if format_str == "markdown" else ReportFormat.JSON

    generator = IncrementalReportGenerator(project_path)

    # Create sample data
    sample_data = create_sample_report_data(report_type)

    # Generate report
    try:
        report_content, is_incremental = generator.generate_incremental_report(
            report_type, sample_data, output_format
        )

        # Save to file
        output_file = f"{report_type}_report.{output_format.value}"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report_content)

        print(f"Report generated: {output_file}")
        print(f"Incremental update: {'Yes' if is_incremental else 'No'}")

        # Print change summary
        summary = generator.get_change_summary(report_type)
        print(f"Change summary: {summary}")

    except Exception as e:
        print(f"Error generating report: {e}")
        sys.exit(1)