"""File Change Event Handler."""

import logging
import os
from pathlib import Path
from typing import Dict, Any
from ..bus import Event


class FileChangeHandler:
    """Handler for file change events."""

    def __init__(self, log_changes: bool = True):
        """Initialize file change handler.

        Args:
            log_changes: Whether to log file changes to disk
        """
        self.logger = logging.getLogger("pm.events.file_change")
        self.log_changes = log_changes

        # Create changes log directory
        self.changes_log_dir = Path.cwd() / "logs" / "file_changes"
        self.changes_log_dir.mkdir(parents=True, exist_ok=True)

    async def handle_file_change(self, event: Event) -> None:
        """Handle file change event.

        Expected event.data format:
        {
            "file_path": "/path/to/file",
            "change_type": "created|modified|deleted",
            "size": 1234,
            "modified_time": "2023-01-01T12:00:00Z",
            "checksum": "optional_md5_hash"
        }
        """
        try:
            data = event.data
            file_path = data.get("file_path", "unknown")
            change_type = data.get("change_type", "unknown")
            size = data.get("size", 0)
            modified_time = data.get("modified_time", "unknown")

            self.logger.info(
                f"File {change_type}: {file_path} "
                f"(size: {size} bytes, modified: {modified_time})"
            )

            # Log to dedicated file changes log
            if self.log_changes:
                await self._log_change_to_file(event)

            # Process specific change types
            if change_type == "created":
                await self._handle_file_created(data)
            elif change_type == "modified":
                await self._handle_file_modified(data)
            elif change_type == "deleted":
                await self._handle_file_deleted(data)

            # Trigger webhooks if configured
            await self._trigger_webhook_callback(event)

        except Exception as e:
            self.logger.error(f"Error handling file change event: {e}")

    async def _handle_file_created(self, data: Dict[str, Any]) -> None:
        """Handle file creation."""
        file_path = data["file_path"]
        self.logger.info(f"New file detected: {file_path}")

        # Could trigger additional processing like:
        # - Index the file for search
        # - Generate file metadata
        # - Check for security scans

    async def _handle_file_modified(self, data: Dict[str, Any]) -> None:
        """Handle file modification."""
        file_path = data["file_path"]
        self.logger.info(f"File modified: {file_path}")

        # Could trigger additional processing like:
        # - Update search index
        # - Generate diff report
        # - Check for breaking changes

    async def _handle_file_deleted(self, data: Dict[str, Any]) -> None:
        """Handle file deletion."""
        file_path = data["file_path"]
        self.logger.info(f"File deleted: {file_path}")

        # Could trigger additional processing like:
        # - Remove from search index
        # - Archive file metadata
        # - Check for dependency breaks

    async def _log_change_to_file(self, event: Event) -> None:
        """Log change to dedicated file."""
        log_file = self.changes_log_dir / "file_changes.jsonl"

        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(event.to_json() + "\n")
        except Exception as e:
            self.logger.error(f"Failed to log change to file: {e}")

    async def _trigger_webhook_callback(self, event: Event) -> None:
        """Trigger webhook callback for file changes."""
        # This would integrate with WebhookHandler
        from ..bus import get_event_bus

        webhook_data = {
            "trigger": "file_change",
            "original_event": event.to_dict(),
            "callback_url": os.getenv("FILE_CHANGE_WEBHOOK_URL"),
            "callback_method": "POST"
        }

        bus = get_event_bus()
        await bus.publish("webhook_trigger", webhook_data)