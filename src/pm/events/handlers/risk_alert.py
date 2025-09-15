"""Risk Alert Event Handler."""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, List
from ..bus import Event


class RiskAlertHandler:
    """Handler for risk alert events."""

    # Risk severity levels
    SEVERITY_LEVELS = {
        "low": 1,
        "medium": 2,
        "high": 3,
        "critical": 4
    }

    def __init__(self, escalation_enabled: bool = True):
        """Initialize risk alert handler.

        Args:
            escalation_enabled: Whether to enable automatic escalation
        """
        self.logger = logging.getLogger("pm.events.risk_alert")
        self.escalation_enabled = escalation_enabled

        # Create risk alerts log directory
        self.alerts_log_dir = Path.cwd() / "logs" / "risk_alerts"
        self.alerts_log_dir.mkdir(parents=True, exist_ok=True)

    async def handle_risk_alert(self, event: Event) -> None:
        """Handle risk alert event.

        Expected event.data format:
        {
            "alert_id": "unique_alert_id",
            "risk_type": "security|performance|compliance|financial",
            "severity": "low|medium|high|critical",
            "title": "Brief description",
            "description": "Detailed description",
            "affected_resources": ["resource1", "resource2"],
            "risk_score": 0.85,
            "detected_at": "2023-01-01T12:00:00Z",
            "source_system": "pm_scanner",
            "mitigation_steps": ["step1", "step2"],
            "metadata": {
                "tags": ["automated", "security"],
                "related_incidents": ["inc123"]
            }
        }
        """
        try:
            data = event.data
            alert_id = data.get("alert_id", "unknown")
            risk_type = data.get("risk_type", "unknown")
            severity = data.get("severity", "low")
            title = data.get("title", "Unknown Risk Alert")
            risk_score = data.get("risk_score", 0.0)

            self.logger.warning(
                f"RISK ALERT [{severity.upper()}]: {title} "
                f"({risk_type}, score: {risk_score}, ID: {alert_id})"
            )

            # Validate severity level
            if severity not in self.SEVERITY_LEVELS:
                self.logger.warning(f"Unknown severity level: {severity}, defaulting to 'low'")
                severity = "low"

            # Log alert to dedicated file
            await self._log_risk_alert(event)

            # Process by severity level
            await self._process_by_severity(data, severity)

            # Check for automatic mitigation
            await self._check_auto_mitigation(data)

            # Escalate if necessary
            if self.escalation_enabled:
                await self._check_escalation(data, severity)

            # Trigger webhook notifications
            await self._trigger_webhook_callback(event)

            # Update risk dashboard
            await self._update_risk_dashboard(data)

        except Exception as e:
            self.logger.error(f"Error handling risk alert event: {e}")

    async def _process_by_severity(self, data: Dict[str, Any], severity: str) -> None:
        """Process alert based on severity level."""
        severity_level = self.SEVERITY_LEVELS[severity]

        if severity_level >= self.SEVERITY_LEVELS["critical"]:
            await self._handle_critical_alert(data)
        elif severity_level >= self.SEVERITY_LEVELS["high"]:
            await self._handle_high_alert(data)
        elif severity_level >= self.SEVERITY_LEVELS["medium"]:
            await self._handle_medium_alert(data)
        else:
            await self._handle_low_alert(data)

    async def _handle_critical_alert(self, data: Dict[str, Any]) -> None:
        """Handle critical severity alerts."""
        alert_id = data.get("alert_id")
        title = data.get("title")

        self.logger.critical(f"CRITICAL ALERT {alert_id}: {title}")

        # Critical alerts require immediate action:
        # - Page on-call engineer
        # - Create incident ticket
        # - Send SMS/email notifications
        # - Trigger emergency response procedures

        # Simulate immediate notification
        self.logger.critical(f"🚨 IMMEDIATE ACTION REQUIRED: {title}")

    async def _handle_high_alert(self, data: Dict[str, Any]) -> None:
        """Handle high severity alerts."""
        alert_id = data.get("alert_id")
        title = data.get("title")

        self.logger.error(f"HIGH ALERT {alert_id}: {title}")

        # High alerts require prompt attention:
        # - Notify team leads
        # - Create high-priority ticket
        # - Schedule review within 4 hours

    async def _handle_medium_alert(self, data: Dict[str, Any]) -> None:
        """Handle medium severity alerts."""
        alert_id = data.get("alert_id")
        title = data.get("title")

        self.logger.warning(f"MEDIUM ALERT {alert_id}: {title}")

        # Medium alerts require attention within 24 hours:
        # - Add to daily standup
        # - Create normal priority ticket

    async def _handle_low_alert(self, data: Dict[str, Any]) -> None:
        """Handle low severity alerts."""
        alert_id = data.get("alert_id")
        title = data.get("title")

        self.logger.info(f"LOW ALERT {alert_id}: {title}")

        # Low alerts are informational:
        # - Log for trend analysis
        # - Review in weekly reports

    async def _check_auto_mitigation(self, data: Dict[str, Any]) -> None:
        """Check if automatic mitigation is possible."""
        risk_type = data.get("risk_type", "")
        mitigation_steps = data.get("mitigation_steps", [])

        if not mitigation_steps:
            return

        # Example auto-mitigation scenarios
        auto_mitigatable_types = ["performance", "resource_usage"]

        if risk_type in auto_mitigatable_types:
            self.logger.info(f"Auto-mitigation available for {risk_type} risk")

            for step in mitigation_steps:
                self.logger.info(f"Auto-mitigation step: {step}")
                # In real implementation, execute mitigation commands

    async def _check_escalation(self, data: Dict[str, Any], severity: str) -> None:
        """Check if alert needs escalation."""
        severity_level = self.SEVERITY_LEVELS[severity]
        risk_score = data.get("risk_score", 0.0)

        # Escalation rules
        should_escalate = (
            severity_level >= self.SEVERITY_LEVELS["high"] or
            risk_score >= 0.8
        )

        if should_escalate:
            await self._escalate_alert(data)

    async def _escalate_alert(self, data: Dict[str, Any]) -> None:
        """Escalate alert to higher authorities."""
        alert_id = data.get("alert_id")
        title = data.get("title")

        self.logger.warning(f"ESCALATING ALERT {alert_id}: {title}")

        # Escalation actions:
        # - Notify management
        # - Create incident
        # - Trigger runbook procedures

        # Create escalation event
        from ..bus import get_event_bus

        escalation_data = {
            "original_alert_id": alert_id,
            "escalation_reason": "severity_threshold",
            "escalated_at": data.get("detected_at"),
            "escalation_level": "management"
        }

        bus = get_event_bus()
        await bus.publish("alert_escalated", escalation_data)

    async def _log_risk_alert(self, event: Event) -> None:
        """Log risk alert to dedicated file."""
        log_file = self.alerts_log_dir / "risk_alerts.jsonl"

        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(event.to_json() + "\n")
        except Exception as e:
            self.logger.error(f"Failed to log risk alert: {e}")

    async def _update_risk_dashboard(self, data: Dict[str, Any]) -> None:
        """Update risk dashboard with new alert."""
        dashboard_file = self.alerts_log_dir / "risk_dashboard.json"

        try:
            # Load existing dashboard data
            dashboard_data = {"total_alerts": 0, "by_severity": {}, "by_type": {}}

            if dashboard_file.exists():
                with open(dashboard_file, "r", encoding="utf-8") as f:
                    dashboard_data = json.load(f)

            # Update counters
            dashboard_data["total_alerts"] += 1

            severity = data.get("severity", "low")
            risk_type = data.get("risk_type", "unknown")

            dashboard_data["by_severity"][severity] = dashboard_data["by_severity"].get(severity, 0) + 1
            dashboard_data["by_type"][risk_type] = dashboard_data["by_type"].get(risk_type, 0) + 1

            # Save updated dashboard
            with open(dashboard_file, "w", encoding="utf-8") as f:
                json.dump(dashboard_data, f, indent=2)

            self.logger.info("Risk dashboard updated")

        except Exception as e:
            self.logger.error(f"Failed to update risk dashboard: {e}")

    async def _trigger_webhook_callback(self, event: Event) -> None:
        """Trigger webhook callback for risk alerts."""
        from ..bus import get_event_bus

        data = event.data
        severity = data.get("severity", "low")

        # Different webhook URLs for different severities
        webhook_urls = {
            "critical": os.getenv("CRITICAL_ALERT_WEBHOOK_URL"),
            "high": os.getenv("HIGH_ALERT_WEBHOOK_URL"),
            "medium": os.getenv("MEDIUM_ALERT_WEBHOOK_URL"),
            "low": os.getenv("LOW_ALERT_WEBHOOK_URL")
        }

        webhook_url = webhook_urls.get(severity) or os.getenv("DEFAULT_RISK_WEBHOOK_URL")

        webhook_data = {
            "trigger": "risk_alert",
            "original_event": event.to_dict(),
            "callback_url": webhook_url,
            "callback_method": "POST",
            "callback_headers": {
                "Content-Type": "application/json",
                "X-PM-Event-Type": "risk_alert",
                "X-PM-Alert-Severity": severity
            }
        }

        bus = get_event_bus()
        await bus.publish("webhook_trigger", webhook_data)