"""Webhook Event Handler for external callbacks."""

import asyncio
import hashlib
import hmac
import json
import logging
import os
import time
from pathlib import Path
from typing import Dict, Any, Optional
from urllib.parse import urlparse

try:
    import aiohttp
except ImportError:
    aiohttp = None

from ..bus import Event


class WebhookHandler:
    """Handler for webhook trigger events and external callbacks."""

    def __init__(self, signature_secret: str = None, max_retries: int = 3):
        """Initialize webhook handler.

        Args:
            signature_secret: Secret key for webhook signature verification
            max_retries: Maximum number of retry attempts for failed webhooks
        """
        self.logger = logging.getLogger("pm.events.webhook")
        self.signature_secret = signature_secret or os.getenv("WEBHOOK_SIGNATURE_SECRET", "default_secret")
        self.max_retries = max_retries

        # Create webhook logs directory
        self.webhook_log_dir = Path.cwd() / "logs" / "webhooks"
        self.webhook_log_dir.mkdir(parents=True, exist_ok=True)

    async def handle_webhook_trigger(self, event: Event) -> None:
        """Handle webhook trigger event.

        Expected event.data format:
        {
            "trigger": "file_change|report_ready|risk_alert",
            "original_event": {...},
            "callback_url": "https://example.com/webhook",
            "callback_method": "POST",
            "callback_headers": {"Content-Type": "application/json"},
            "callback_timeout": 30,
            "retry_on_failure": true
        }
        """
        try:
            data = event.data
            callback_url = data.get("callback_url")

            if not callback_url:
                self.logger.info("No callback URL specified, skipping webhook")
                return

            self.logger.info(f"Processing webhook trigger for: {callback_url}")

            # Prepare webhook payload
            payload = self._prepare_webhook_payload(data)

            # Send webhook with retries
            success = await self._send_webhook_with_retries(
                url=callback_url,
                payload=payload,
                method=data.get("callback_method", "POST"),
                headers=data.get("callback_headers", {}),
                timeout=data.get("callback_timeout", 30),
                retry_enabled=data.get("retry_on_failure", True)
            )

            if success:
                self.logger.info(f"Webhook sent successfully to: {callback_url}")
            else:
                self.logger.error(f"Failed to send webhook to: {callback_url}")

            # Log webhook attempt
            await self._log_webhook_attempt(event, success)

        except Exception as e:
            self.logger.error(f"Error handling webhook trigger: {e}")

    def _prepare_webhook_payload(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare the webhook payload."""
        payload = {
            "event_type": data.get("trigger"),
            "timestamp": int(time.time()),
            "event_id": data.get("original_event", {}).get("event_id"),
            "data": data.get("original_event", {}).get("data", {}),
            "source": "personal-manager"
        }

        # Add signature for security
        payload["signature"] = self._generate_signature(payload)

        return payload

    def _generate_signature(self, payload: Dict[str, Any]) -> str:
        """Generate HMAC signature for webhook payload."""
        # Remove signature from payload for signing
        payload_copy = payload.copy()
        payload_copy.pop("signature", None)

        # Create canonical string
        payload_str = json.dumps(payload_copy, sort_keys=True, separators=(',', ':'))

        # Generate HMAC-SHA256 signature
        signature = hmac.new(
            self.signature_secret.encode('utf-8'),
            payload_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        return f"sha256={signature}"

    async def _send_webhook_with_retries(
        self,
        url: str,
        payload: Dict[str, Any],
        method: str = "POST",
        headers: Dict[str, str] = None,
        timeout: int = 30,
        retry_enabled: bool = True
    ) -> bool:
        """Send webhook with retry logic."""
        if aiohttp is None:
            self.logger.warning("aiohttp not available, simulating webhook send")
            return await self._simulate_webhook_send(url, payload)

        headers = headers or {}
        headers.setdefault("Content-Type", "application/json")
        headers.setdefault("User-Agent", "PersonalManager-Webhook/1.0")
        headers["X-Webhook-Signature"] = payload.get("signature", "")

        for attempt in range(1, self.max_retries + 1):
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                    async with session.request(
                        method=method,
                        url=url,
                        json=payload,
                        headers=headers
                    ) as response:
                        if response.status < 400:
                            self.logger.info(
                                f"Webhook sent successfully (attempt {attempt}): "
                                f"{response.status} {url}"
                            )
                            return True
                        else:
                            self.logger.warning(
                                f"Webhook failed (attempt {attempt}): "
                                f"{response.status} {url}"
                            )

            except asyncio.TimeoutError:
                self.logger.warning(f"Webhook timeout (attempt {attempt}): {url}")
            except Exception as e:
                self.logger.warning(f"Webhook error (attempt {attempt}): {e}")

            # Wait before retry with exponential backoff
            if retry_enabled and attempt < self.max_retries:
                wait_time = 2 ** (attempt - 1)
                self.logger.info(f"Retrying webhook in {wait_time} seconds...")
                await asyncio.sleep(wait_time)

        return False

    async def _simulate_webhook_send(self, url: str, payload: Dict[str, Any]) -> bool:
        """Simulate webhook send when aiohttp is not available."""
        try:
            # Validate URL format
            parsed = urlparse(url)
            if not all([parsed.scheme, parsed.netloc]):
                raise ValueError(f"Invalid URL format: {url}")

            self.logger.info(f"[SIMULATED] Webhook sent to: {url}")
            self.logger.debug(f"[SIMULATED] Payload: {json.dumps(payload, indent=2)}")

            # Simulate network delay
            await asyncio.sleep(0.1)

            # Simulate 90% success rate
            import random
            return random.random() < 0.9

        except Exception as e:
            self.logger.error(f"Error in webhook simulation: {e}")
            return False

    async def _log_webhook_attempt(self, event: Event, success: bool) -> None:
        """Log webhook attempt to file."""
        log_file = self.webhook_log_dir / "webhook_attempts.jsonl"

        log_entry = {
            "timestamp": time.time(),
            "event_id": event.event_id,
            "webhook_url": event.data.get("callback_url"),
            "success": success,
            "trigger_type": event.data.get("trigger"),
            "original_event_id": event.data.get("original_event", {}).get("event_id")
        }

        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            self.logger.error(f"Failed to log webhook attempt: {e}")

    def verify_webhook_signature(self, payload: str, signature: str) -> bool:
        """Verify webhook signature for incoming webhooks.

        Args:
            payload: Raw payload string
            signature: Signature header value (format: "sha256=...")

        Returns:
            True if signature is valid, False otherwise
        """
        try:
            if not signature.startswith("sha256="):
                return False

            expected_signature = signature[7:]  # Remove "sha256=" prefix

            computed_signature = hmac.new(
                self.signature_secret.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()

            return hmac.compare_digest(expected_signature, computed_signature)

        except Exception as e:
            self.logger.error(f"Error verifying webhook signature: {e}")
            return False

    async def handle_incoming_webhook(
        self,
        payload: str,
        signature: str = None,
        headers: Dict[str, str] = None
    ) -> bool:
        """Handle incoming webhook from external systems.

        Args:
            payload: Raw webhook payload
            signature: Webhook signature for verification
            headers: HTTP headers from the request

        Returns:
            True if webhook was processed successfully
        """
        try:
            # Verify signature if provided
            if signature and not self.verify_webhook_signature(payload, signature):
                self.logger.warning("Invalid webhook signature received")
                return False

            # Parse payload
            try:
                webhook_data = json.loads(payload)
            except json.JSONDecodeError as e:
                self.logger.error(f"Invalid JSON in webhook payload: {e}")
                return False

            # Log incoming webhook
            self.logger.info(f"Incoming webhook received: {webhook_data.get('event_type', 'unknown')}")

            # Process webhook based on type
            event_type = webhook_data.get("event_type")
            if event_type:
                from ..bus import get_event_bus
                bus = get_event_bus()

                # Create internal event from webhook
                internal_event_data = {
                    "webhook_source": True,
                    "original_data": webhook_data.get("data", {}),
                    "external_event_id": webhook_data.get("event_id"),
                    "received_headers": headers or {}
                }

                await bus.publish(f"webhook_{event_type}", internal_event_data)

            return True

        except Exception as e:
            self.logger.error(f"Error handling incoming webhook: {e}")
            return False