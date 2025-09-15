"""Report Ready Event Handler."""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Any
from ..bus import Event


class ReportReadyHandler:
    """Handler for report ready events."""

    def __init__(self, auto_distribute: bool = True):
        """Initialize report ready handler.

        Args:
            auto_distribute: Whether to automatically distribute reports
        """
        self.logger = logging.getLogger("pm.events.report_ready")
        self.auto_distribute = auto_distribute

        # Create reports log directory
        self.reports_log_dir = Path.cwd() / "logs" / "reports"
        self.reports_log_dir.mkdir(parents=True, exist_ok=True)

    async def handle_report_ready(self, event: Event) -> None:
        """Handle report ready event.

        Expected event.data format:
        {
            "report_id": "unique_report_id",
            "report_type": "daily|weekly|monthly|custom",
            "report_path": "/path/to/report.pdf",
            "report_format": "pdf|html|json",
            "generated_at": "2023-01-01T12:00:00Z",
            "size_bytes": 1234567,
            "recipients": ["email1@example.com", "email2@example.com"],
            "metadata": {
                "author": "pm_system",
                "tags": ["daily", "summary"]
            }
        }
        """
        try:
            data = event.data
            report_id = data.get("report_id", "unknown")
            report_type = data.get("report_type", "unknown")
            report_path = data.get("report_path", "")
            report_format = data.get("report_format", "unknown")
            size_bytes = data.get("size_bytes", 0)

            self.logger.info(
                f"Report ready: {report_type} [{report_id}] "
                f"- {report_path} ({size_bytes} bytes, {report_format})"
            )

            # Validate report exists
            if report_path and Path(report_path).exists():
                self.logger.info(f"Report file validated: {report_path}")
                await self._validate_report(data)
            else:
                self.logger.warning(f"Report file not found: {report_path}")

            # Log report generation
            await self._log_report_generation(event)

            # Auto-distribute if enabled
            if self.auto_distribute:
                await self._distribute_report(data)

            # Generate report metadata
            await self._generate_report_metadata(data)

            # Trigger webhook callbacks
            await self._trigger_webhook_callback(event)

        except Exception as e:
            self.logger.error(f"Error handling report ready event: {e}")

    async def _validate_report(self, data: Dict[str, Any]) -> bool:
        """Validate the generated report."""
        report_path = Path(data["report_path"])

        if not report_path.exists():
            self.logger.error(f"Report file not found: {report_path}")
            return False

        # Check file size
        size = report_path.stat().st_size
        if size == 0:
            self.logger.error(f"Report file is empty: {report_path}")
            return False

        # Validate format-specific requirements
        report_format = data.get("report_format", "").lower()

        if report_format == "pdf":
            # Basic PDF validation (check magic bytes)
            with open(report_path, "rb") as f:
                header = f.read(4)
                if header != b"%PDF":
                    self.logger.error(f"Invalid PDF file: {report_path}")
                    return False

        elif report_format == "json":
            # Validate JSON structure
            try:
                with open(report_path, "r", encoding="utf-8") as f:
                    json.load(f)
            except json.JSONDecodeError as e:
                self.logger.error(f"Invalid JSON in report: {e}")
                return False

        self.logger.info(f"Report validation passed: {report_path}")
        return True

    async def _log_report_generation(self, event: Event) -> None:
        """Log report generation to dedicated file."""
        log_file = self.reports_log_dir / "report_generations.jsonl"

        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(event.to_json() + "\n")
        except Exception as e:
            self.logger.error(f"Failed to log report generation: {e}")

    async def _distribute_report(self, data: Dict[str, Any]) -> None:
        """Distribute report to recipients."""
        recipients = data.get("recipients", [])
        report_path = data.get("report_path", "")
        report_type = data.get("report_type", "unknown")

        if not recipients:
            self.logger.info("No recipients specified for report distribution")
            return

        self.logger.info(f"Distributing {report_type} report to {len(recipients)} recipients")

        # In a real implementation, this would:
        # - Send emails with report attachments
        # - Upload to shared storage (S3, etc.)
        # - Post to Slack/Teams channels
        # - Update dashboards

        for recipient in recipients:
            self.logger.info(f"Report distributed to: {recipient}")

    async def _generate_report_metadata(self, data: Dict[str, Any]) -> None:
        """Generate and store report metadata."""
        report_id = data.get("report_id")
        metadata_file = self.reports_log_dir / f"{report_id}_metadata.json"

        metadata = {
            "report_id": report_id,
            "generated_at": data.get("generated_at"),
            "type": data.get("report_type"),
            "format": data.get("report_format"),
            "size_bytes": data.get("size_bytes"),
            "path": data.get("report_path"),
            "recipients_count": len(data.get("recipients", [])),
            "custom_metadata": data.get("metadata", {})
        }

        try:
            with open(metadata_file, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2)
            self.logger.info(f"Report metadata saved: {metadata_file}")
        except Exception as e:
            self.logger.error(f"Failed to save report metadata: {e}")

    async def _trigger_webhook_callback(self, event: Event) -> None:
        """Trigger webhook callback for report ready events."""
        from ..bus import get_event_bus

        webhook_data = {
            "trigger": "report_ready",
            "original_event": event.to_dict(),
            "callback_url": os.getenv("REPORT_READY_WEBHOOK_URL"),
            "callback_method": "POST",
            "callback_headers": {
                "Content-Type": "application/json",
                "X-PM-Event-Type": "report_ready"
            }
        }

        bus = get_event_bus()
        await bus.publish("webhook_trigger", webhook_data)