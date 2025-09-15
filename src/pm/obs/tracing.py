"""Distributed Tracing Module

Provides distributed tracing capabilities for tracking critical paths
across AI routing, event processing, and plugin execution.
"""

import time
import uuid
import json
import threading
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Union, Callable, ContextManager
from dataclasses import dataclass, asdict, field
from enum import Enum
from collections import defaultdict, deque
from contextlib import contextmanager
import functools

from pm.obs.metrics import get_metrics_registry, MetricsRegistry


class SpanKind(str, Enum):
    """Types of spans"""
    INTERNAL = "internal"
    SERVER = "server"
    CLIENT = "client"
    PRODUCER = "producer"
    CONSUMER = "consumer"


class SpanStatus(str, Enum):
    """Span execution status"""
    OK = "ok"
    ERROR = "error"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class SpanContext:
    """Span context for distributed tracing"""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    baggage: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class Span:
    """Represents a traced operation"""
    context: SpanContext
    operation_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    status: SpanStatus = SpanStatus.OK
    kind: SpanKind = SpanKind.INTERNAL
    tags: Dict[str, Any] = field(default_factory=dict)
    logs: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None

    def finish(self, status: Optional[SpanStatus] = None, error: Optional[str] = None):
        """Finish the span"""
        self.end_time = datetime.now(timezone.utc)
        self.duration_ms = (self.end_time - self.start_time).total_seconds() * 1000

        if status:
            self.status = status
        if error:
            self.error = error
            self.status = SpanStatus.ERROR

    def set_tag(self, key: str, value: Any):
        """Set a tag on the span"""
        self.tags[key] = value

    def log(self, message: str, level: str = "info", **kwargs):
        """Add a log entry to the span"""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "message": message,
            **kwargs
        }
        self.logs.append(log_entry)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['start_time'] = self.start_time.isoformat()
        if self.end_time:
            data['end_time'] = self.end_time.isoformat()
        data['status'] = self.status.value
        data['kind'] = self.kind.value
        return data


@dataclass
class Trace:
    """Represents a complete trace with multiple spans"""
    trace_id: str
    spans: List[Span] = field(default_factory=list)
    root_span: Optional[Span] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None

    def add_span(self, span: Span):
        """Add a span to the trace"""
        self.spans.append(span)

        # Set root span if this is the first span or has no parent
        if not self.root_span or not span.context.parent_span_id:
            self.root_span = span
            self.start_time = span.start_time

    def finish(self):
        """Finish the trace by calculating total duration"""
        if self.spans:
            self.start_time = min(span.start_time for span in self.spans)
            finished_spans = [span for span in self.spans if span.end_time]
            if finished_spans:
                self.end_time = max(span.end_time for span in finished_spans)
                self.duration_ms = (self.end_time - self.start_time).total_seconds() * 1000

    def get_critical_path(self) -> List[Span]:
        """Get the critical path (longest duration chain) through the trace"""
        if not self.root_span:
            return []

        # Build span hierarchy
        children_map = defaultdict(list)
        for span in self.spans:
            if span.context.parent_span_id:
                children_map[span.context.parent_span_id].append(span)

        def find_longest_path(span: Span) -> List[Span]:
            """Recursively find the longest path from this span"""
            children = children_map.get(span.context.span_id, [])
            if not children:
                return [span]

            longest_child_path = []
            max_duration = 0

            for child in children:
                child_path = find_longest_path(child)
                child_duration = sum(s.duration_ms or 0 for s in child_path)
                if child_duration > max_duration:
                    max_duration = child_duration
                    longest_child_path = child_path

            return [span] + longest_child_path

        return find_longest_path(self.root_span)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = {
            "trace_id": self.trace_id,
            "spans": [span.to_dict() for span in self.spans],
            "root_span_id": self.root_span.context.span_id if self.root_span else None,
            "duration_ms": self.duration_ms,
            "span_count": len(self.spans)
        }

        if self.start_time:
            data["start_time"] = self.start_time.isoformat()
        if self.end_time:
            data["end_time"] = self.end_time.isoformat()

        return data


class TraceCollector:
    """Collects and manages distributed traces"""

    def __init__(self, storage_path: Optional[Path] = None, max_traces: int = 1000):
        self.storage_path = storage_path or Path.home() / '.pm' / 'traces'
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.max_traces = max_traces
        self._traces: Dict[str, Trace] = {}
        self._lock = threading.Lock()

        # Critical path tracking
        self._critical_paths = deque(maxlen=100)
        self._slo_violations = deque(maxlen=500)

        # SLO thresholds (milliseconds)
        self._slo_thresholds = {
            "ai_routing": 5000,  # 5 seconds
            "event_processing": 1000,  # 1 second
            "plugin_execution": 2000,  # 2 seconds
            "api_request": 3000,  # 3 seconds
            "cache_operation": 100,  # 100ms
            "database_query": 500,  # 500ms
        }

        # Initialize metrics
        self._metrics = get_metrics_registry()
        self._init_tracing_metrics()

    def _init_tracing_metrics(self):
        """Initialize tracing-specific metrics"""
        self._metrics.register_counter('traces_created', 'count')
        self._metrics.register_counter('spans_created', 'count')
        self._metrics.register_counter('slo_violations', 'count')
        self._metrics.register_timer('trace_duration', 'ms')
        self._metrics.register_timer('span_duration', 'ms')
        self._metrics.register_gauge('active_traces', 'count')
        self._metrics.register_histogram('critical_path_length', 'count')

    def create_trace(self, operation_name: str, trace_id: Optional[str] = None) -> Trace:
        """Create a new trace"""
        if not trace_id:
            trace_id = str(uuid.uuid4())

        trace = Trace(trace_id=trace_id)

        with self._lock:
            self._traces[trace_id] = trace

            # Cleanup old traces if we exceed max
            if len(self._traces) > self.max_traces:
                oldest_trace_id = next(iter(self._traces))
                del self._traces[oldest_trace_id]

        self._metrics.counter('traces_created').increment()
        self._metrics.gauge('active_traces').set(len(self._traces))

        return trace

    def get_trace(self, trace_id: str) -> Optional[Trace]:
        """Get a trace by ID"""
        return self._traces.get(trace_id)

    def finish_trace(self, trace_id: str):
        """Finish a trace and analyze it"""
        trace = self._traces.get(trace_id)
        if not trace:
            return

        trace.finish()

        if trace.duration_ms:
            self._metrics.timer('trace_duration').record(trace.duration_ms)

        # Analyze critical path
        critical_path = trace.get_critical_path()
        if critical_path:
            self._critical_paths.append({
                "trace_id": trace_id,
                "critical_path": [span.operation_name for span in critical_path],
                "total_duration_ms": sum(span.duration_ms or 0 for span in critical_path),
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

            self._metrics.histogram('critical_path_length').record(len(critical_path))

        # Check SLO violations
        self._check_slo_violations(trace)

        # Save trace to storage
        self._save_trace(trace)

    def _check_slo_violations(self, trace: Trace):
        """Check for SLO violations in the trace"""
        violations = []

        for span in trace.spans:
            if not span.duration_ms:
                continue

            # Check operation-specific SLOs
            for operation_type, threshold in self._slo_thresholds.items():
                if operation_type in span.operation_name.lower():
                    if span.duration_ms > threshold:
                        violation = {
                            "trace_id": trace.trace_id,
                            "span_id": span.context.span_id,
                            "operation": span.operation_name,
                            "duration_ms": span.duration_ms,
                            "threshold_ms": threshold,
                            "violation_ratio": span.duration_ms / threshold,
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        }
                        violations.append(violation)
                        self._slo_violations.append(violation)
                        self._metrics.counter('slo_violations').increment()

        return violations

    def _save_trace(self, trace: Trace):
        """Save trace to storage"""
        try:
            # Save individual trace
            trace_file = self.storage_path / f"trace_{trace.trace_id}.json"
            with open(trace_file, 'w') as f:
                json.dump(trace.to_dict(), f, indent=2)

            # Update latest traces index
            self._update_traces_index(trace)

        except Exception as e:
            # Don't let tracing errors break the application
            pass

    def _update_traces_index(self, trace: Trace):
        """Update the traces index file"""
        index_file = self.storage_path / "traces_index.json"

        try:
            if index_file.exists():
                with open(index_file, 'r') as f:
                    index = json.load(f)
            else:
                index = {"traces": []}

            # Add new trace to index
            trace_entry = {
                "trace_id": trace.trace_id,
                "root_operation": trace.root_span.operation_name if trace.root_span else "unknown",
                "duration_ms": trace.duration_ms,
                "span_count": len(trace.spans),
                "timestamp": trace.start_time.isoformat() if trace.start_time else None,
                "status": "error" if any(span.status == SpanStatus.ERROR for span in trace.spans) else "ok"
            }

            index["traces"].insert(0, trace_entry)

            # Keep only last 1000 traces in index
            index["traces"] = index["traces"][:1000]

            with open(index_file, 'w') as f:
                json.dump(index, f, indent=2)

        except Exception:
            pass

    def get_recent_traces(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent traces summary"""
        index_file = self.storage_path / "traces_index.json"

        try:
            if index_file.exists():
                with open(index_file, 'r') as f:
                    index = json.load(f)
                return index["traces"][:limit]
        except Exception:
            pass

        return []

    def get_slo_violations(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get SLO violations from the last N hours"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)

        violations = []
        for violation in self._slo_violations:
            violation_time = datetime.fromisoformat(violation["timestamp"].replace('Z', '+00:00'))
            if violation_time >= cutoff_time:
                violations.append(violation)

        return violations

    def get_critical_paths(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent critical paths"""
        return list(self._critical_paths)[-limit:]

    def calculate_burn_rate(self, slo_target: float = 0.95, window_hours: int = 1) -> Dict[str, float]:
        """Calculate SLO burn rate for alerting"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=window_hours)

        # Count total operations and violations in the window
        total_operations = 0
        total_violations = 0

        for violation in self._slo_violations:
            violation_time = datetime.fromisoformat(violation["timestamp"].replace('Z', '+00:00'))
            if violation_time >= cutoff_time:
                total_violations += 1

        # Estimate total operations (this would be more accurate with full telemetry)
        total_operations = max(total_violations * 10, 100)  # Conservative estimate

        if total_operations == 0:
            return {"burn_rate": 0.0, "error_budget_remaining": 1.0}

        error_rate = total_violations / total_operations
        error_budget_consumed = error_rate / (1 - slo_target)
        burn_rate = error_budget_consumed * (24 / window_hours)  # Normalize to daily rate

        return {
            "burn_rate": burn_rate,
            "error_rate": error_rate,
            "error_budget_remaining": max(0, 1 - error_budget_consumed),
            "total_operations": total_operations,
            "total_violations": total_violations
        }

    def get_trace_analytics(self) -> Dict[str, Any]:
        """Get comprehensive trace analytics"""
        recent_violations = self.get_slo_violations(hours=24)
        critical_paths = self.get_critical_paths()
        burn_rate = self.calculate_burn_rate()

        # Operation performance analysis
        operation_stats = defaultdict(lambda: {"count": 0, "total_duration": 0, "violations": 0})

        with self._lock:
            for trace in self._traces.values():
                for span in trace.spans:
                    if span.duration_ms:
                        operation_stats[span.operation_name]["count"] += 1
                        operation_stats[span.operation_name]["total_duration"] += span.duration_ms

                        if span.status == SpanStatus.ERROR:
                            operation_stats[span.operation_name]["violations"] += 1

        # Calculate averages
        performance_summary = {}
        for operation, stats in operation_stats.items():
            if stats["count"] > 0:
                performance_summary[operation] = {
                    "avg_duration_ms": stats["total_duration"] / stats["count"],
                    "total_count": stats["count"],
                    "error_rate": stats["violations"] / stats["count"],
                    "violation_count": stats["violations"]
                }

        return {
            "active_traces": len(self._traces),
            "recent_violations": len(recent_violations),
            "critical_path_analysis": {
                "avg_length": sum(len(cp["critical_path"]) for cp in critical_paths) / max(len(critical_paths), 1),
                "longest_path": max((len(cp["critical_path"]) for cp in critical_paths), default=0)
            },
            "slo_burn_rate": burn_rate,
            "operation_performance": performance_summary,
            "violation_summary": recent_violations[:10]  # Top 10 recent violations
        }


# Global tracer instance
_global_tracer: Optional[TraceCollector] = None


def get_tracer() -> TraceCollector:
    """Get or create global tracer"""
    global _global_tracer
    if _global_tracer is None:
        _global_tracer = TraceCollector()
    return _global_tracer


# Thread-local storage for active span context
_local = threading.local()


def get_current_span() -> Optional[Span]:
    """Get the current active span"""
    return getattr(_local, 'current_span', None)


def set_current_span(span: Optional[Span]):
    """Set the current active span"""
    _local.current_span = span


@contextmanager
def start_span(
    operation_name: str,
    parent_span: Optional[Span] = None,
    kind: SpanKind = SpanKind.INTERNAL,
    **tags
) -> ContextManager[Span]:
    """Start a new span with context management"""
    tracer = get_tracer()

    # Get parent context
    if parent_span is None:
        parent_span = get_current_span()

    # Create span context
    if parent_span:
        trace_id = parent_span.context.trace_id
        parent_span_id = parent_span.context.span_id
        trace = tracer.get_trace(trace_id)
    else:
        trace_id = str(uuid.uuid4())
        parent_span_id = None
        trace = tracer.create_trace(operation_name, trace_id)

    span_id = str(uuid.uuid4())
    context = SpanContext(
        trace_id=trace_id,
        span_id=span_id,
        parent_span_id=parent_span_id
    )

    # Create span
    span = Span(
        context=context,
        operation_name=operation_name,
        start_time=datetime.now(timezone.utc),
        kind=kind,
        tags=tags
    )

    # Add to trace
    if trace:
        trace.add_span(span)

    # Track metrics
    tracer._metrics.counter('spans_created').increment()

    # Set as current span
    previous_span = get_current_span()
    set_current_span(span)

    try:
        yield span
    except Exception as e:
        span.finish(status=SpanStatus.ERROR, error=str(e))
        raise
    else:
        span.finish()
    finally:
        # Record span duration
        if span.duration_ms:
            tracer._metrics.timer('span_duration').record(span.duration_ms)

        # Restore previous span
        set_current_span(previous_span)

        # If this was a root span, finish the trace
        if not parent_span and trace:
            tracer.finish_trace(trace_id)


def trace_operation(operation_name: str, kind: SpanKind = SpanKind.INTERNAL, **tags):
    """Decorator to trace a function or method"""
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with start_span(operation_name, kind=kind, **tags) as span:
                # Add function metadata
                span.set_tag("function_name", func.__name__)
                span.set_tag("module", func.__module__)

                # Add argument count (but not values for security)
                span.set_tag("arg_count", len(args))
                span.set_tag("kwarg_count", len(kwargs))

                result = func(*args, **kwargs)

                # Add result metadata if it's serializable
                if isinstance(result, (str, int, float, bool, type(None))):
                    span.set_tag("result_type", type(result).__name__)
                    if isinstance(result, str):
                        span.set_tag("result_length", len(result))

                return result
        return wrapper
    return decorator


# Convenience decorators for common operations
def trace_ai_operation(operation_name: str, **tags):
    """Decorator for AI-related operations"""
    return trace_operation(f"ai_{operation_name}", kind=SpanKind.CLIENT, component="ai", **tags)


def trace_event_processing(operation_name: str, **tags):
    """Decorator for event processing operations"""
    return trace_operation(f"event_{operation_name}", kind=SpanKind.CONSUMER, component="events", **tags)


def trace_plugin_execution(operation_name: str, **tags):
    """Decorator for plugin execution"""
    return trace_operation(f"plugin_{operation_name}", kind=SpanKind.INTERNAL, component="plugins", **tags)


def trace_api_request(operation_name: str, **tags):
    """Decorator for API requests"""
    return trace_operation(f"api_{operation_name}", kind=SpanKind.SERVER, component="api", **tags)


# CLI interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="PM Distributed Tracing")
    parser.add_argument('--trace', action='store_true', help='Enable trace collection mode')
    parser.add_argument('--analytics', action='store_true', help='Show trace analytics')
    parser.add_argument('--violations', action='store_true', help='Show SLO violations')
    parser.add_argument('--simulate', action='store_true', help='Simulate traces for testing')

    args = parser.parse_args()

    tracer = get_tracer()

    if args.simulate:
        # Simulate some traces for testing
        import random
        import time as time_module

        for i in range(10):
            with start_span("ai_routing_request") as root_span:
                root_span.set_tag("request_id", f"req_{i}")

                # Simulate AI processing
                with start_span("ai_text_generation", kind=SpanKind.CLIENT) as ai_span:
                    ai_span.set_tag("model", "claude-3-sonnet")
                    ai_span.set_tag("tokens", random.randint(100, 500))
                    time_module.sleep(random.uniform(0.1, 2.0))

                # Simulate event processing
                with start_span("event_processing") as event_span:
                    event_span.set_tag("event_type", "user_interaction")
                    time_module.sleep(random.uniform(0.01, 0.1))

                # Simulate plugin execution
                with start_span("plugin_execution") as plugin_span:
                    plugin_span.set_tag("plugin_name", f"plugin_{random.randint(1, 5)}")
                    time_module.sleep(random.uniform(0.05, 0.5))

                    # Occasionally simulate errors
                    if random.random() < 0.1:
                        plugin_span.finish(status=SpanStatus.ERROR, error="Plugin execution failed")

        print("Simulated traces generated")

    if args.analytics:
        analytics = tracer.get_trace_analytics()
        print(json.dumps(analytics, indent=2))

    elif args.violations:
        violations = tracer.get_slo_violations()
        print(json.dumps(violations, indent=2))

    elif args.trace:
        # Run in trace collection mode
        print("Trace collection mode enabled. Monitoring...")
        try:
            while True:
                time_module.sleep(10)
                analytics = tracer.get_trace_analytics()
                print(f"Active traces: {analytics['active_traces']}, "
                      f"Recent violations: {analytics['recent_violations']}")
        except KeyboardInterrupt:
            print("\nStopping trace collection...")

    else:
        # Show recent traces by default
        recent_traces = tracer.get_recent_traces()
        print(json.dumps(recent_traces, indent=2))