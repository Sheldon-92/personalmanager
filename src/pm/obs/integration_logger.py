"""Integration Logger - Standardized chain tracing for Personal Manager

Provides standardized logging for request flow through all components including:
- API endpoints
- Event bus
- Plugin manager
- Metrics collection

Log Format: req=<id>|event=<type>|handler=<status>|plugin=<status>|metrics=<operation:status>|time=<ms>
"""

import time
import threading
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum


class HandlerStatus(Enum):
    """Handler execution status"""
    OK = "ok"
    ERROR = "error"
    TIMEOUT = "timeout"
    PENDING = "pending"


class PluginStatus(Enum):
    """Plugin operation status"""
    LOADED = "loaded"
    RUN_OK = "run:ok"
    RUN_ERROR = "run:error"
    NOT_FOUND = "not_found"
    DISABLED = "disabled"


class MetricsStatus(Enum):
    """Metrics operation status"""
    WRITE_OK = "write:ok"
    WRITE_ERROR = "write:error"
    COLLECT_OK = "collect:ok"
    COLLECT_ERROR = "collect:error"


@dataclass
class IntegrationLogEntry:
    """Single integration log entry"""
    req_id: str
    event_type: str = ""
    handler_status: HandlerStatus = HandlerStatus.PENDING
    plugin_status: Optional[PluginStatus] = None
    metrics_status: Optional[MetricsStatus] = None
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    component_timings: Dict[str, float] = field(default_factory=dict)

    def add_timing(self, component: str, duration_ms: float):
        """Add timing for a specific component"""
        self.component_timings[component] = duration_ms

    def set_end_time(self):
        """Set the end time for this entry"""
        self.end_time = time.time()

    def get_total_time_ms(self) -> int:
        """Get total execution time in milliseconds"""
        if self.end_time is None:
            return int((time.time() - self.start_time) * 1000)
        return int((self.end_time - self.start_time) * 1000)

    def to_log_line(self) -> str:
        """Convert to standardized log line format"""
        parts = [f"req={self.req_id}"]

        if self.event_type:
            parts.append(f"event={self.event_type}")

        parts.append(f"handler={self.handler_status.value}")

        if self.plugin_status:
            parts.append(f"plugin={self.plugin_status.value}")

        if self.metrics_status:
            parts.append(f"metrics={self.metrics_status.value}")

        parts.append(f"time={self.get_total_time_ms()}")

        return "|".join(parts)


class IntegrationLogger:
    """Thread-safe integration logger for chain tracing"""

    def __init__(self, log_file: Optional[Path] = None):
        """Initialize integration logger

        Args:
            log_file: Path to log file. Defaults to logs/int.log
        """
        if log_file is None:
            log_file = Path("logs/int.log")

        self.log_file = log_file
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        # Thread-safe storage for active log entries
        self._active_entries: Dict[str, IntegrationLogEntry] = {}
        self._lock = threading.Lock()
        self._request_counter = 0

    def generate_request_id(self, prefix: str = "req") -> str:
        """Generate unique request ID"""
        with self._lock:
            self._request_counter += 1
            return f"{prefix}_{self._request_counter:06d}"

    def start_request(self, req_id: Optional[str] = None, event_type: str = "") -> str:
        """Start tracking a new request

        Args:
            req_id: Optional request ID. If None, one will be generated
            event_type: Type of event being processed

        Returns:
            The request ID for this request
        """
        if req_id is None:
            req_id = self.generate_request_id()

        with self._lock:
            entry = IntegrationLogEntry(
                req_id=req_id,
                event_type=event_type
            )
            self._active_entries[req_id] = entry

        return req_id

    def update_handler_status(self, req_id: str, status: HandlerStatus):
        """Update handler status for a request"""
        with self._lock:
            if req_id in self._active_entries:
                self._active_entries[req_id].handler_status = status

    def update_plugin_status(self, req_id: str, status: PluginStatus):
        """Update plugin status for a request"""
        with self._lock:
            if req_id in self._active_entries:
                self._active_entries[req_id].plugin_status = status

    def update_metrics_status(self, req_id: str, status: MetricsStatus):
        """Update metrics status for a request"""
        with self._lock:
            if req_id in self._active_entries:
                self._active_entries[req_id].metrics_status = status

    def add_component_timing(self, req_id: str, component: str, duration_ms: float):
        """Add timing information for a component"""
        with self._lock:
            if req_id in self._active_entries:
                self._active_entries[req_id].add_timing(component, duration_ms)

    def complete_request(self, req_id: str):
        """Complete a request and write to log"""
        with self._lock:
            if req_id not in self._active_entries:
                return

            entry = self._active_entries[req_id]
            entry.set_end_time()

            # Write to log file
            log_line = entry.to_log_line()
            with open(self.log_file, 'a') as f:
                f.write(f"{log_line}\n")

            # Remove from active tracking
            del self._active_entries[req_id]

    @contextmanager
    def trace_request(self, event_type: str = "", req_id: Optional[str] = None):
        """Context manager for request tracing

        Args:
            event_type: Type of event being processed
            req_id: Optional request ID

        Yields:
            Request ID for this trace
        """
        req_id = self.start_request(req_id, event_type)
        try:
            yield req_id
        except Exception as e:
            self.update_handler_status(req_id, HandlerStatus.ERROR)
            raise
        finally:
            self.complete_request(req_id)

    @contextmanager
    def time_component(self, req_id: str, component: str):
        """Context manager for timing a component operation

        Args:
            req_id: Request ID to associate timing with
            component: Name of the component being timed
        """
        start_time = time.time()
        try:
            yield
        finally:
            duration_ms = (time.time() - start_time) * 1000
            self.add_component_timing(req_id, component, duration_ms)

    def get_active_requests(self) -> Dict[str, IntegrationLogEntry]:
        """Get currently active requests (for debugging)"""
        with self._lock:
            return self._active_entries.copy()


# Global integration logger instance
_global_logger: Optional[IntegrationLogger] = None


def get_integration_logger() -> IntegrationLogger:
    """Get or create global integration logger"""
    global _global_logger
    if _global_logger is None:
        _global_logger = IntegrationLogger()
    return _global_logger


def trace_api_request(endpoint: str, req_id: Optional[str] = None):
    """Convenience function for tracing API requests"""
    logger = get_integration_logger()
    return logger.trace_request(f"API:{endpoint}", req_id)


def trace_event_processing(event_type: str, req_id: Optional[str] = None):
    """Convenience function for tracing event processing"""
    logger = get_integration_logger()
    return logger.trace_request(f"Event:{event_type}", req_id)


def trace_plugin_operation(plugin_name: str, req_id: Optional[str] = None):
    """Convenience function for tracing plugin operations"""
    logger = get_integration_logger()
    return logger.trace_request(f"Plugin:{plugin_name}", req_id)


def trace_metrics_collection(operation: str, req_id: Optional[str] = None):
    """Convenience function for tracing metrics operations"""
    logger = get_integration_logger()
    return logger.trace_request(f"Metrics:{operation}", req_id)


# Example usage:
if __name__ == "__main__":
    # Demo the integration logger
    logger = get_integration_logger()

    # Example 1: Manual request tracking
    req_id = logger.start_request(event_type="TaskCreate")
    logger.update_handler_status(req_id, HandlerStatus.OK)
    logger.update_plugin_status(req_id, PluginStatus.RUN_OK)
    logger.update_metrics_status(req_id, MetricsStatus.WRITE_OK)
    logger.complete_request(req_id)

    # Example 2: Context manager usage
    with logger.trace_request("FileChange") as req_id:
        logger.update_handler_status(req_id, HandlerStatus.OK)
        logger.update_plugin_status(req_id, PluginStatus.NOT_FOUND)
        logger.update_metrics_status(req_id, MetricsStatus.COLLECT_OK)

        # Simulate some work with component timing
        with logger.time_component(req_id, "api"):
            time.sleep(0.01)

        with logger.time_component(req_id, "event_bus"):
            time.sleep(0.005)

    # Example 3: Using convenience functions
    with trace_api_request("/api/v1/tasks") as req_id:
        logger.update_handler_status(req_id, HandlerStatus.OK)
        logger.update_metrics_status(req_id, MetricsStatus.WRITE_OK)

    print(f"Integration logs written to: {logger.log_file}")