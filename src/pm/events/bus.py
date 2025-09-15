"""Event Bus - Core event system for Personal Manager."""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Callable, Optional, Union
from uuid import uuid4

# Import async compatibility layer
try:
    from .async_compat import AsyncCompatibilityBridge, run_async_from_sync
except ImportError:
    from async_compat import AsyncCompatibilityBridge, run_async_from_sync

# Import integration logging
try:
    from ..obs.integration_logger import (
        get_integration_logger, trace_event_processing,
        HandlerStatus, PluginStatus, MetricsStatus
    )
except ImportError:
    # Fallback for standalone usage
    def get_integration_logger():
        return None
    def trace_event_processing(*args, **kwargs):
        return None


@dataclass
class Event:
    """Event data structure."""
    type: str
    data: Dict[str, Any]
    timestamp: float = None
    event_id: str = None
    source: str = "pm_system"

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.event_id is None:
            self.event_id = str(uuid4())

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return asdict(self)

    def to_json(self) -> str:
        """Convert event to JSON string."""
        return json.dumps(self.to_dict(), default=str)


class EventBus:
    """Asynchronous event bus with subscription/publishing mechanisms."""

    def __init__(self, log_dir: str = None):
        """Initialize event bus.

        Args:
            log_dir: Directory for event logs. Defaults to logs/events/
        """
        self._subscribers: Dict[str, List[Callable]] = {}
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._is_running: bool = False
        self._processor_task: Optional[asyncio.Task] = None

        # Setup logging
        if log_dir is None:
            log_dir = Path.cwd() / "logs" / "events"
        else:
            log_dir = Path(log_dir)

        log_dir.mkdir(parents=True, exist_ok=True)
        self._log_file = log_dir / f"events_{datetime.now().strftime('%Y%m%d')}.log"

        # Configure event logger
        self._logger = logging.getLogger("pm.events")
        self._logger.setLevel(logging.INFO)

        # Remove existing handlers to avoid duplicates
        for handler in self._logger.handlers[:]:
            self._logger.removeHandler(handler)

        # File handler for events
        file_handler = logging.FileHandler(self._log_file)
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        self._logger.addHandler(file_handler)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self._logger.addHandler(console_handler)

        self._logger.info("EventBus initialized with log file: %s", self._log_file)

    def subscribe(self, event_type: str, handler: Callable[[Event], Any]) -> None:
        """Subscribe to an event type.

        Args:
            event_type: Type of event to subscribe to
            handler: Async function to handle the event
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []

        self._subscribers[event_type].append(handler)
        self._logger.info(f"Handler subscribed to event type: {event_type}")

    def unsubscribe(self, event_type: str, handler: Callable[[Event], Any]) -> None:
        """Unsubscribe from an event type.

        Args:
            event_type: Type of event to unsubscribe from
            handler: Handler function to remove
        """
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(handler)
                self._logger.info(f"Handler unsubscribed from event type: {event_type}")
            except ValueError:
                self._logger.warning(f"Handler not found for event type: {event_type}")

    async def publish(self, event: Union[Event, str], data: Dict[str, Any] = None) -> None:
        """Publish an event to the bus.

        Args:
            event: Event object or event type string
            data: Event data (if event is a string)
        """
        if isinstance(event, str):
            event = Event(type=event, data=data or {})

        await self._event_queue.put(event)
        self._logger.info(f"Event published: {event.type} [{event.event_id}]")

        # Integration logging for event publication
        integration_logger = get_integration_logger()
        if integration_logger:
            req_id = integration_logger.generate_request_id("event")
            integration_logger.start_request(req_id, f"EventPub:{event.type}")
            integration_logger.update_handler_status(req_id, HandlerStatus.OK)
            integration_logger.update_metrics_status(req_id, MetricsStatus.WRITE_OK)
            integration_logger.complete_request(req_id)

    def publish_sync(self, event: Union[Event, str], data: Dict[str, Any] = None) -> None:
        """Synchronous event publishing with compatibility handling.

        Args:
            event: Event object or event type string
            data: Event data (if event is a string)
        """
        if isinstance(event, str):
            event = Event(type=event, data=data or {})

        # Use compatibility bridge to handle async in any context
        result = run_async_from_sync(self.publish(event))

        # If result is a Task, we're in async context and task is scheduled
        if isinstance(result, asyncio.Task):
            self._logger.debug(f"Event {event.type} scheduled as async task")
        else:
            self._logger.debug(f"Event {event.type} published synchronously")

    async def start(self) -> None:
        """Start the event processor."""
        if self._is_running:
            return

        self._is_running = True
        self._processor_task = asyncio.create_task(self._process_events())
        self._logger.info("EventBus started")

    async def stop(self) -> None:
        """Stop the event processor."""
        if not self._is_running:
            return

        self._is_running = False
        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass

        self._logger.info("EventBus stopped")

    async def _process_events(self) -> None:
        """Process events from the queue."""
        while self._is_running:
            try:
                # Wait for an event with timeout to allow graceful shutdown
                event = await asyncio.wait_for(self._event_queue.get(), timeout=1.0)
                await self._handle_event(event)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self._logger.error(f"Error processing event: {e}")

    async def _handle_event(self, event: Event) -> None:
        """Handle a single event by calling all subscribers.

        Args:
            event: Event to handle
        """
        integration_logger = get_integration_logger()
        req_id = None

        if integration_logger:
            req_id = integration_logger.generate_request_id("event")
            integration_logger.start_request(req_id, f"EventProcess:{event.type}")

        try:
            self._logger.info(f"Processing event: {event.type} [{event.event_id}] - {json.dumps(event.data)}")

            # Get handlers for exact match
            handlers = self._subscribers.get(event.type, [])

            # Also check for wildcard pattern matches
            import fnmatch
            for pattern, pattern_handlers in self._subscribers.items():
                if '*' in pattern and fnmatch.fnmatch(event.type, pattern):
                    handlers.extend(pattern_handlers)

            if not handlers:
                self._logger.warning(f"No handlers registered for event type: {event.type}")
                if integration_logger and req_id:
                    integration_logger.update_handler_status(req_id, HandlerStatus.OK)
                    integration_logger.update_plugin_status(req_id, PluginStatus.NOT_FOUND)
                    integration_logger.update_metrics_status(req_id, MetricsStatus.COLLECT_OK)
                return

            # Execute all handlers concurrently
            tasks = []
            for handler in handlers:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        task = asyncio.create_task(handler(event))
                    else:
                        # Wrap sync function in async
                        task = asyncio.create_task(self._run_sync_handler(handler, event))
                    tasks.append(task)
                except Exception as e:
                    self._logger.error(f"Error creating task for handler: {e}")

            # Wait for all handlers to complete
            if tasks:
                if integration_logger and req_id:
                    with integration_logger.time_component(req_id, "event_handlers"):
                        results = await asyncio.gather(*tasks, return_exceptions=True)
                else:
                    results = await asyncio.gather(*tasks, return_exceptions=True)

                handler_errors = 0
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        self._logger.error(f"Handler {i} failed: {result}")
                        handler_errors += 1
                    else:
                        self._logger.debug(f"Handler {i} completed successfully")

                # Update integration logging based on results
                if integration_logger and req_id:
                    if handler_errors == 0:
                        integration_logger.update_handler_status(req_id, HandlerStatus.OK)
                        integration_logger.update_plugin_status(req_id, PluginStatus.RUN_OK)
                    else:
                        integration_logger.update_handler_status(req_id, HandlerStatus.ERROR if handler_errors == len(results) else HandlerStatus.OK)
                        integration_logger.update_plugin_status(req_id, PluginStatus.RUN_ERROR if handler_errors > 0 else PluginStatus.RUN_OK)

                    integration_logger.update_metrics_status(req_id, MetricsStatus.WRITE_OK)

        except Exception as e:
            self._logger.error(f"Error handling event {event.type}: {e}")
            if integration_logger and req_id:
                integration_logger.update_handler_status(req_id, HandlerStatus.ERROR)

        finally:
            if integration_logger and req_id:
                integration_logger.complete_request(req_id)

    async def _run_sync_handler(self, handler: Callable, event: Event) -> Any:
        """Run a synchronous handler in an executor.

        Args:
            handler: Synchronous handler function
            event: Event to process
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, handler, event)

    def get_subscribers(self) -> Dict[str, int]:
        """Get subscriber counts by event type.

        Returns:
            Dictionary mapping event types to subscriber counts
        """
        return {event_type: len(handlers) for event_type, handlers in self._subscribers.items()}

    def get_log_file(self) -> Path:
        """Get the current log file path.

        Returns:
            Path to the current log file
        """
        return self._log_file


# Global event bus instance
_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get the global event bus instance.

    Returns:
        Global EventBus instance
    """
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


async def publish_event(event_type: str, data: Dict[str, Any]) -> None:
    """Convenience function to publish an event.

    Args:
        event_type: Type of event
        data: Event data
    """
    bus = get_event_bus()
    await bus.publish(event_type, data)


def publish_event_sync(event_type: str, data: Dict[str, Any]) -> None:
    """Convenience function to publish an event synchronously.

    Args:
        event_type: Type of event
        data: Event data
    """
    bus = get_event_bus()
    bus.publish_sync(event_type, data)