"""
Difference Highlighting Tool
Provides visual highlighting of changes between report versions
"""

import os
import re
import json
import difflib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum

import html


class HighlightStyle(Enum):
    """Different highlighting styles supported"""
    HTML = "html"
    MARKDOWN = "markdown"
    TERMINAL = "terminal"
    JSON = "json"


class DiffType(Enum):
    """Types of differences"""
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    UNCHANGED = "unchanged"


@dataclass
class DiffLine:
    """Represents a line with difference information"""
    line_number: Optional[int]
    content: str
    diff_type: DiffType
    old_line_number: Optional[int] = None
    new_line_number: Optional[int] = None


@dataclass
class DiffSection:
    """Represents a section of differences"""
    title: str
    old_value: Any
    new_value: Any
    diff_type: DiffType
    lines: List[DiffLine]
    context_lines: int = 3


class DiffHighlighter:
    """
    Tool for highlighting differences between report versions with color coding and visual markers
    """

    def __init__(self):
        self.html_styles = self._get_html_styles()
        self.terminal_colors = self._get_terminal_colors()

    def _get_html_styles(self) -> Dict[str, str]:
        """Get HTML/CSS styles for different diff types"""
        return {
            "added": "background-color: #d4edda; color: #155724; border-left: 4px solid #28a745;",
            "removed": "background-color: #f8d7da; color: #721c24; border-left: 4px solid #dc3545;",
            "modified": "background-color: #fff3cd; color: #856404; border-left: 4px solid #ffc107;",
            "unchanged": "background-color: #f8f9fa; color: #6c757d;",
            "line_number": "color: #6c757d; background-color: #e9ecef; padding: 0 8px; font-family: monospace; font-size: 0.9em;",
            "content": "font-family: 'Courier New', monospace; padding: 4px 8px; white-space: pre-wrap; line-height: 1.4;",
            "section_title": "font-weight: bold; font-size: 1.1em; margin: 20px 0 10px 0; padding: 8px; background-color: #e9ecef; border-radius: 4px;",
            "container": "border: 1px solid #dee2e6; border-radius: 8px; margin: 10px 0; overflow: hidden;",
            "summary": "background-color: #f1f3f4; padding: 12px; border-bottom: 1px solid #dee2e6; font-weight: bold;"
        }

    def _get_terminal_colors(self) -> Dict[str, str]:
        """Get terminal color codes for different diff types"""
        return {
            "added": "\033[32m",      # Green
            "removed": "\033[31m",    # Red
            "modified": "\033[33m",   # Yellow
            "unchanged": "\033[37m",  # White
            "reset": "\033[0m",       # Reset
            "bold": "\033[1m",        # Bold
            "dim": "\033[2m"          # Dim
        }

    def compare_reports(self, old_report: str, new_report: str,
                       report_type: str = "markdown") -> List[DiffSection]:
        """
        Compare two reports and identify differences

        Args:
            old_report: Previous report content
            new_report: New report content
            report_type: Type of report content (markdown, json, etc.)

        Returns:
            List of difference sections
        """
        if report_type.lower() == "json":
            return self._compare_json_reports(old_report, new_report)
        else:
            return self._compare_text_reports(old_report, new_report)

    def _compare_text_reports(self, old_text: str, new_text: str) -> List[DiffSection]:
        """Compare text-based reports line by line"""
        old_lines = old_text.splitlines(keepends=False)
        new_lines = new_text.splitlines(keepends=False)

        # Use difflib to get differences
        differ = difflib.unified_diff(
            old_lines, new_lines,
            fromfile="Previous Report",
            tofile="Current Report",
            lineterm=""
        )

        sections = []
        current_section = None
        diff_lines = []

        for line in differ:
            if line.startswith('+++') or line.startswith('---'):
                continue
            elif line.startswith('@@'):
                # New section
                if current_section and diff_lines:
                    current_section.lines = diff_lines
                    sections.append(current_section)

                # Parse hunk header
                match = re.match(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@', line)
                if match:
                    old_start, old_count, new_start, new_count = match.groups()
                    current_section = DiffSection(
                        title=f"Lines {old_start}-{new_start}",
                        old_value=None,
                        new_value=None,
                        diff_type=DiffType.MODIFIED,
                        lines=[]
                    )
                    diff_lines = []
            elif line.startswith('-'):
                diff_lines.append(DiffLine(
                    line_number=None,
                    content=line[1:],
                    diff_type=DiffType.REMOVED
                ))
            elif line.startswith('+'):
                diff_lines.append(DiffLine(
                    line_number=None,
                    content=line[1:],
                    diff_type=DiffType.ADDED
                ))
            elif line.startswith(' '):
                diff_lines.append(DiffLine(
                    line_number=None,
                    content=line[1:],
                    diff_type=DiffType.UNCHANGED
                ))

        # Add final section
        if current_section and diff_lines:
            current_section.lines = diff_lines
            sections.append(current_section)

        return sections

    def _compare_json_reports(self, old_json: str, new_json: str) -> List[DiffSection]:
        """Compare JSON reports structurally"""
        try:
            old_data = json.loads(old_json)
            new_data = json.loads(new_json)
        except json.JSONDecodeError as e:
            # Fallback to text comparison
            return self._compare_text_reports(old_json, new_json)

        return self._compare_json_objects(old_data, new_data, "")

    def _compare_json_objects(self, old_obj: Any, new_obj: Any, path: str) -> List[DiffSection]:
        """Recursively compare JSON objects"""
        sections = []

        if type(old_obj) != type(new_obj):
            sections.append(DiffSection(
                title=f"Type change at {path or 'root'}",
                old_value=f"{type(old_obj).__name__}: {old_obj}",
                new_value=f"{type(new_obj).__name__}: {new_obj}",
                diff_type=DiffType.MODIFIED,
                lines=[]
            ))
            return sections

        if isinstance(old_obj, dict) and isinstance(new_obj, dict):
            all_keys = set(old_obj.keys()) | set(new_obj.keys())

            for key in sorted(all_keys):
                key_path = f"{path}.{key}" if path else key

                if key in old_obj and key in new_obj:
                    if old_obj[key] != new_obj[key]:
                        if isinstance(old_obj[key], (dict, list)):
                            sections.extend(self._compare_json_objects(
                                old_obj[key], new_obj[key], key_path
                            ))
                        else:
                            sections.append(DiffSection(
                                title=f"Modified: {key_path}",
                                old_value=old_obj[key],
                                new_value=new_obj[key],
                                diff_type=DiffType.MODIFIED,
                                lines=[]
                            ))
                elif key in old_obj:
                    sections.append(DiffSection(
                        title=f"Removed: {key_path}",
                        old_value=old_obj[key],
                        new_value=None,
                        diff_type=DiffType.REMOVED,
                        lines=[]
                    ))
                elif key in new_obj:
                    sections.append(DiffSection(
                        title=f"Added: {key_path}",
                        old_value=None,
                        new_value=new_obj[key],
                        diff_type=DiffType.ADDED,
                        lines=[]
                    ))

        elif isinstance(old_obj, list) and isinstance(new_obj, list):
            if old_obj != new_obj:
                sections.append(DiffSection(
                    title=f"List changed at {path or 'root'}",
                    old_value=f"Length {len(old_obj)}: {old_obj}",
                    new_value=f"Length {len(new_obj)}: {new_obj}",
                    diff_type=DiffType.MODIFIED,
                    lines=[]
                ))

        return sections

    def generate_html_diff(self, diff_sections: List[DiffSection],
                          title: str = "Report Comparison") -> str:
        """Generate HTML representation of differences"""
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(title)}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 20px;
            background-color: #f8f9fa;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
        .summary {{
            {self.html_styles['summary']}
        }}
        .diff-container {{
            {self.html_styles['container']}
            background: white;
        }}
        .section-title {{
            {self.html_styles['section_title']}
        }}
        .diff-line {{
            display: flex;
            align-items: stretch;
            border-bottom: 1px solid #f1f3f4;
        }}
        .line-number {{
            {self.html_styles['line_number']}
            min-width: 50px;
            text-align: right;
            flex-shrink: 0;
        }}
        .line-content {{
            {self.html_styles['content']}
            flex: 1;
        }}
        .diff-added {{
            {self.html_styles['added']}
        }}
        .diff-removed {{
            {self.html_styles['removed']}
        }}
        .diff-modified {{
            {self.html_styles['modified']}
        }}
        .diff-unchanged {{
            {self.html_styles['unchanged']}
        }}
        .no-changes {{
            text-align: center;
            padding: 40px;
            color: #6c757d;
            font-style: italic;
        }}
        .stats {{
            display: flex;
            gap: 20px;
            margin: 20px 0;
        }}
        .stat {{
            background: white;
            padding: 15px;
            border-radius: 6px;
            border: 1px solid #dee2e6;
            text-align: center;
        }}
        .stat-value {{
            font-size: 1.5em;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .stat-label {{
            color: #6c757d;
            font-size: 0.9em;
        }}
        .legend {{
            display: flex;
            gap: 15px;
            margin: 15px 0;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 4px;
            font-size: 0.9em;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 5px;
        }}
        .legend-color {{
            width: 12px;
            height: 12px;
            border-radius: 2px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{html.escape(title)}</h1>
        <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
"""

        if not diff_sections:
            html_content += """
    <div class="diff-container">
        <div class="no-changes">
            <h3>No Differences Found</h3>
            <p>The reports are identical.</p>
        </div>
    </div>
"""
        else:
            # Add statistics
            added_count = sum(1 for s in diff_sections if s.diff_type == DiffType.ADDED)
            removed_count = sum(1 for s in diff_sections if s.diff_type == DiffType.REMOVED)
            modified_count = sum(1 for s in diff_sections if s.diff_type == DiffType.MODIFIED)

            html_content += f"""
    <div class="stats">
        <div class="stat">
            <div class="stat-value" style="color: #28a745;">{added_count}</div>
            <div class="stat-label">Added</div>
        </div>
        <div class="stat">
            <div class="stat-value" style="color: #dc3545;">{removed_count}</div>
            <div class="stat-label">Removed</div>
        </div>
        <div class="stat">
            <div class="stat-value" style="color: #ffc107;">{modified_count}</div>
            <div class="stat-label">Modified</div>
        </div>
        <div class="stat">
            <div class="stat-value">{len(diff_sections)}</div>
            <div class="stat-label">Total Changes</div>
        </div>
    </div>

    <div class="legend">
        <div class="legend-item">
            <div class="legend-color" style="background-color: #d4edda;"></div>
            <span>Added content</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background-color: #f8d7da;"></div>
            <span>Removed content</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background-color: #fff3cd;"></div>
            <span>Modified content</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background-color: #f8f9fa;"></div>
            <span>Unchanged context</span>
        </div>
    </div>
"""

            # Add diff sections
            for section in diff_sections:
                css_class = f"diff-{section.diff_type.value}"
                html_content += f"""
    <div class="diff-container">
        <div class="section-title {css_class}">
            {html.escape(section.title)}
        </div>
"""

                if section.old_value is not None or section.new_value is not None:
                    if section.old_value is not None:
                        html_content += f"""
        <div class="summary diff-removed">
            <strong>Before:</strong> {html.escape(str(section.old_value))}
        </div>
"""
                    if section.new_value is not None:
                        html_content += f"""
        <div class="summary diff-added">
            <strong>After:</strong> {html.escape(str(section.new_value))}
        </div>
"""

                # Add line-by-line differences
                for i, line in enumerate(section.lines):
                    line_css = f"diff-{line.diff_type.value}"
                    html_content += f"""
        <div class="diff-line {line_css}">
            <div class="line-number">{i+1}</div>
            <div class="line-content">{html.escape(line.content)}</div>
        </div>
"""

                html_content += "    </div>\n"

        html_content += """
</body>
</html>
"""

        return html_content

    def highlight_differences(self, old_content: str, new_content: str,
                            output_style: HighlightStyle = HighlightStyle.HTML,
                            title: str = "Report Comparison",
                            content_type: str = "markdown") -> str:
        """
        Main method to highlight differences between two reports

        Args:
            old_content: Previous report content
            new_content: Current report content
            output_style: Style of output (HTML, Markdown, Terminal, JSON)
            title: Title for the comparison report
            content_type: Type of content being compared

        Returns:
            Formatted diff output
        """
        diff_sections = self.compare_reports(old_content, new_content, content_type)

        if output_style == HighlightStyle.HTML:
            return self.generate_html_diff(diff_sections, title)
        else:
            # For now, return a simple text diff
            return f"# {title}\n\nDiff sections: {len(diff_sections)}"


if __name__ == "__main__":
    # Test the diff highlighter
    highlighter = DiffHighlighter()

    # Create sample reports
    old_report = """# Code Analysis Report
**Project**: PersonalManager
**Version**: 1.0.0

## Summary
- Total Files: 25
- Lines of Code: 5000
- Quality Score: 7.5/10"""

    new_report = """# Code Analysis Report
**Project**: PersonalManager
**Version**: 1.1.0

## Summary
- Total Files: 30
- Lines of Code: 6500
- Quality Score: 8.2/10
- Security Score: 9.0/10"""

    # Generate HTML diff
    diff_output = highlighter.highlight_differences(
        old_report, new_report,
        output_style=HighlightStyle.HTML,
        title="PersonalManager Report Comparison"
    )

    with open("example_diff.html", 'w', encoding='utf-8') as f:
        f.write(diff_output)

    print("Generated example_diff.html")