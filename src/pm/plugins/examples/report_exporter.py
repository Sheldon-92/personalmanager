"""
Report Exporter Plugin
Exports PM reports to various formats (PDF, HTML, Markdown, JSON)
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.pm.plugins.sdk import (
    PluginBase,
    PluginMetadata,
    PluginPermission,
    HookType,
    HookContext
)

logger = logging.getLogger(__name__)


class ReportExporterPlugin(PluginBase):
    """Plugin for exporting reports in multiple formats"""

    def get_metadata(self) -> PluginMetadata:
        """Return plugin metadata"""
        return PluginMetadata(
            name="report_exporter",
            version="1.0.0",
            author="PM Team",
            description="Export PM reports to PDF, HTML, Markdown, and JSON formats",
            required_permissions={
                PluginPermission.READ_DATA,
                PluginPermission.FILE_SYSTEM_WRITE,
                PluginPermission.HOOK_REGISTRATION
            },
            hooks={
                HookType.POST_REPORT_GENERATE: ["on_report_generated"],
                HookType.PRE_COMMAND: ["on_command_check"]
            },
            config_schema={
                "type": "object",
                "properties": {
                    "export_dir": {"type": "string", "description": "Directory for exported reports"},
                    "formats": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["pdf", "html", "markdown", "json"]},
                        "default": ["markdown", "json"]
                    },
                    "auto_export": {"type": "boolean", "default": False},
                    "template_dir": {"type": "string", "description": "Directory containing export templates"}
                },
                "required": ["export_dir"]
            }
        )

    async def initialize(self) -> bool:
        """Initialize the plugin"""
        try:
            # Set default configuration
            if "export_dir" not in self.config:
                self.config["export_dir"] = str(Path.home() / ".pm" / "exports")

            if "formats" not in self.config:
                self.config["formats"] = ["markdown", "json"]

            # Create export directory
            self.export_path = Path(self.config["export_dir"])
            self.export_path.mkdir(parents=True, exist_ok=True)

            # Initialize export templates
            self.templates = self._load_templates()

            # Initialize export statistics
            self.export_stats = {
                "total_exports": 0,
                "exports_by_format": {},
                "last_export": None
            }

            self._logger.info(f"Report Exporter initialized with formats: {self.config['formats']}")
            return True

        except Exception as e:
            self._logger.error(f"Failed to initialize Report Exporter: {e}")
            return False

    async def shutdown(self) -> None:
        """Clean up resources"""
        # Save export statistics
        try:
            stats_file = self.export_path / ".export_stats.json"
            with open(stats_file, 'w') as f:
                json.dump(self.export_stats, f, indent=2, default=str)
            self._logger.info("Report Exporter shutdown complete")
        except Exception as e:
            self._logger.error(f"Error saving export stats: {e}")

    def _load_templates(self) -> Dict[str, str]:
        """Load export templates"""
        templates = {
            "markdown": self._get_markdown_template(),
            "html": self._get_html_template(),
            "json": None,  # JSON doesn't need a template
            "pdf": None    # PDF uses HTML template
        }
        return templates

    def _get_markdown_template(self) -> str:
        """Get Markdown export template"""
        return """# {title}

**Generated**: {timestamp}
**Type**: {report_type}

---

## Summary
{summary}

## Details
{content}

## Metadata
- **Version**: {version}
- **Plugin**: Report Exporter v{plugin_version}
- **Export Format**: Markdown

---
*Exported by PM Report Exporter Plugin*
"""

    def _get_html_template(self) -> str:
        """Get HTML export template"""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
               line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
        .metadata {{ background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .timestamp {{ color: #7f8c8d; font-size: 0.9em; }}
        pre {{ background: #2c3e50; color: #ecf0f1; padding: 15px; border-radius: 5px; overflow-x: auto; }}
        .summary {{ background: #e8f4fd; padding: 15px; border-left: 4px solid #3498db; margin: 20px 0; }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <div class="metadata">
        <p class="timestamp">Generated: {timestamp}</p>
        <p>Type: <strong>{report_type}</strong></p>
    </div>

    <div class="summary">
        <h2>Summary</h2>
        <p>{summary}</p>
    </div>

    <div class="content">
        <h2>Details</h2>
        {content}
    </div>

    <footer>
        <hr>
        <p style="text-align: center; color: #7f8c8d; font-size: 0.85em;">
            Exported by PM Report Exporter Plugin v{plugin_version}
        </p>
    </footer>
</body>
</html>"""

    async def export_report(self, report_data: Dict[str, Any], formats: Optional[List[str]] = None) -> Dict[str, str]:
        """Export report to specified formats"""
        exported_files = {}
        formats = formats or self.config.get("formats", ["json"])

        # Prepare report data
        report_data = self._prepare_report_data(report_data)

        for format_type in formats:
            try:
                if format_type == "json":
                    file_path = await self._export_json(report_data)
                elif format_type == "markdown":
                    file_path = await self._export_markdown(report_data)
                elif format_type == "html":
                    file_path = await self._export_html(report_data)
                elif format_type == "pdf":
                    file_path = await self._export_pdf(report_data)
                else:
                    self._logger.warning(f"Unsupported format: {format_type}")
                    continue

                exported_files[format_type] = str(file_path)
                self._update_stats(format_type)

            except Exception as e:
                self._logger.error(f"Failed to export to {format_type}: {e}")

        return exported_files

    def _prepare_report_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare and normalize report data"""
        return {
            "title": data.get("title", "PM Report"),
            "timestamp": datetime.now().isoformat(),
            "report_type": data.get("type", "general"),
            "summary": data.get("summary", ""),
            "content": self._format_content(data.get("content", {})),
            "version": data.get("version", "1.0"),
            "plugin_version": self._metadata.version if self._metadata else "1.0.0",
            "metadata": data.get("metadata", {})
        }

    def _format_content(self, content: Any) -> str:
        """Format content for export"""
        if isinstance(content, str):
            return content
        elif isinstance(content, dict) or isinstance(content, list):
            return json.dumps(content, indent=2, default=str)
        else:
            return str(content)

    async def _export_json(self, data: Dict[str, Any]) -> Path:
        """Export report as JSON"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"{data['report_type']}_{timestamp}.json"
        file_path = self.export_path / file_name

        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)

        self._logger.info(f"Exported JSON report to {file_path}")
        return file_path

    async def _export_markdown(self, data: Dict[str, Any]) -> Path:
        """Export report as Markdown"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"{data['report_type']}_{timestamp}.md"
        file_path = self.export_path / file_name

        content = self.templates["markdown"].format(**data)

        with open(file_path, 'w') as f:
            f.write(content)

        self._logger.info(f"Exported Markdown report to {file_path}")
        return file_path

    async def _export_html(self, data: Dict[str, Any]) -> Path:
        """Export report as HTML"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"{data['report_type']}_{timestamp}.html"
        file_path = self.export_path / file_name

        # Convert content to HTML format
        if isinstance(data["content"], str):
            data["content"] = f"<pre>{data['content']}</pre>"

        content = self.templates["html"].format(**data)

        with open(file_path, 'w') as f:
            f.write(content)

        self._logger.info(f"Exported HTML report to {file_path}")
        return file_path

    async def _export_pdf(self, data: Dict[str, Any]) -> Path:
        """Export report as PDF (simplified - would use weasyprint or similar in production)"""
        # For now, we'll create a simple text-based PDF placeholder
        # In production, use libraries like weasyprint, reportlab, or pdfkit
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"{data['report_type']}_{timestamp}.pdf.txt"
        file_path = self.export_path / file_name

        content = f"""[PDF Export Placeholder]
Title: {data['title']}
Generated: {data['timestamp']}
Type: {data['report_type']}

Summary:
{data['summary']}

Content:
{data['content']}

Note: Install a PDF library (weasyprint, reportlab) for actual PDF generation.
"""

        with open(file_path, 'w') as f:
            f.write(content)

        self._logger.info(f"Exported PDF placeholder to {file_path}")
        return file_path

    def _update_stats(self, format_type: str) -> None:
        """Update export statistics"""
        self.export_stats["total_exports"] += 1
        if format_type not in self.export_stats["exports_by_format"]:
            self.export_stats["exports_by_format"][format_type] = 0
        self.export_stats["exports_by_format"][format_type] += 1
        self.export_stats["last_export"] = datetime.now().isoformat()

    # Hook handlers
    async def on_report_generated(self, context: HookContext) -> HookContext:
        """Hook handler for post-report generation"""
        if self.config.get("auto_export", False):
            report_data = context.get("report_data")
            if report_data:
                self._logger.info("Auto-exporting generated report")
                exported = await self.export_report(report_data)
                context.set("exported_files", exported)

        return context

    async def on_command_check(self, context: HookContext) -> HookContext:
        """Hook handler for pre-command execution"""
        command = context.get("command", "")

        # Add export command support
        if command.startswith("export"):
            parts = command.split()
            if len(parts) >= 2:
                report_type = parts[1]
                formats = parts[2:] if len(parts) > 2 else self.config.get("formats")

                # Trigger export
                context.set("handle_export", {
                    "type": report_type,
                    "formats": formats
                })

        return context

    def get_export_statistics(self) -> Dict[str, Any]:
        """Get export statistics"""
        return {
            "stats": self.export_stats,
            "config": {
                "export_dir": str(self.export_path),
                "enabled_formats": self.config.get("formats", []),
                "auto_export": self.config.get("auto_export", False)
            }
        }


# For direct testing
if __name__ == "__main__":
    async def test_plugin():
        """Test the Report Exporter plugin"""
        plugin = ReportExporterPlugin({
            "export_dir": "/tmp/pm_exports",
            "formats": ["json", "markdown", "html"],
            "auto_export": True
        })

        if await plugin.initialize():
            # Test export
            test_report = {
                "title": "Test Report",
                "type": "test",
                "summary": "This is a test report for the exporter plugin",
                "content": {
                    "test_data": "Sample data",
                    "metrics": {"success": True, "count": 42}
                },
                "metadata": {"generator": "test_script"}
            }

            exported = await plugin.export_report(test_report)
            print(f"Exported files: {exported}")

            # Get statistics
            stats = plugin.get_export_statistics()
            print(f"Export statistics: {json.dumps(stats, indent=2)}")

            await plugin.shutdown()

    # Run test
    asyncio.run(test_plugin())