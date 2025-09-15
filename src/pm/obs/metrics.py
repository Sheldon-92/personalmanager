"""Metrics Collection Module

Collects and tracks performance metrics including latency percentiles,
error rates, cache hit rates, and other observability metrics.
"""

import time
import json
import threading
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Union, Callable
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from enum import Enum
import statistics
import psutil
import math

# Import integration logging
try:
    from .integration_logger import (
        get_integration_logger, trace_metrics_collection,
        HandlerStatus, MetricsStatus
    )
except ImportError:
    # Fallback for standalone usage
    def get_integration_logger():
        return None
    def trace_metrics_collection(*args, **kwargs):
        return None


class MetricType(Enum):
    """Types of metrics"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class MetricSnapshot:
    """Snapshot of a metric at a point in time"""
    name: str
    type: MetricType
    value: Union[float, Dict[str, float]]
    timestamp: datetime
    tags: Dict[str, str]
    unit: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['type'] = self.type.value
        data['timestamp'] = self.timestamp.isoformat()
        return data


class MetricCollector:
    """Base collector for metrics"""

    def __init__(self, name: str, unit: Optional[str] = None):
        self.name = name
        self.unit = unit
        self._lock = threading.Lock()

    def get_snapshot(self, tags: Optional[Dict[str, str]] = None) -> MetricSnapshot:
        """Get current metric snapshot"""
        raise NotImplementedError


class Counter(MetricCollector):
    """Counter metric - always increases"""

    def __init__(self, name: str, unit: Optional[str] = None):
        super().__init__(name, unit)
        self._value = 0

    def increment(self, value: float = 1):
        """Increment counter"""
        with self._lock:
            self._value += value

    def get_value(self) -> float:
        """Get current value"""
        with self._lock:
            return self._value

    def get_snapshot(self, tags: Optional[Dict[str, str]] = None) -> MetricSnapshot:
        """Get metric snapshot"""
        return MetricSnapshot(
            name=self.name,
            type=MetricType.COUNTER,
            value=self.get_value(),
            timestamp=datetime.now(timezone.utc),
            tags=tags or {},
            unit=self.unit
        )


class Gauge(MetricCollector):
    """Gauge metric - can go up or down"""

    def __init__(self, name: str, unit: Optional[str] = None):
        super().__init__(name, unit)
        self._value = 0

    def set(self, value: float):
        """Set gauge value"""
        with self._lock:
            self._value = value

    def increment(self, value: float = 1):
        """Increment gauge"""
        with self._lock:
            self._value += value

    def decrement(self, value: float = 1):
        """Decrement gauge"""
        with self._lock:
            self._value -= value

    def get_value(self) -> float:
        """Get current value"""
        with self._lock:
            return self._value

    def get_snapshot(self, tags: Optional[Dict[str, str]] = None) -> MetricSnapshot:
        """Get metric snapshot"""
        return MetricSnapshot(
            name=self.name,
            type=MetricType.GAUGE,
            value=self.get_value(),
            timestamp=datetime.now(timezone.utc),
            tags=tags or {},
            unit=self.unit
        )


class Histogram(MetricCollector):
    """Histogram metric with percentile calculations"""

    def __init__(
        self,
        name: str,
        unit: Optional[str] = None,
        max_samples: int = 10000
    ):
        super().__init__(name, unit)
        self._samples = deque(maxlen=max_samples)
        self._count = 0
        self._sum = 0

    def record(self, value: float):
        """Record a value"""
        with self._lock:
            self._samples.append(value)
            self._count += 1
            self._sum += value

    def get_percentiles(self) -> Dict[str, float]:
        """Calculate percentiles"""
        with self._lock:
            if not self._samples:
                return {
                    'p50': 0,
                    'p95': 0,
                    'p99': 0,
                    'p999': 0,
                    'mean': 0,
                    'min': 0,
                    'max': 0,
                    'count': 0
                }

            sorted_samples = sorted(self._samples)
            n = len(sorted_samples)

            return {
                'p50': sorted_samples[int(n * 0.5)],
                'p95': sorted_samples[int(n * 0.95)],
                'p99': sorted_samples[int(n * 0.99)],
                'p999': sorted_samples[min(int(n * 0.999), n - 1)],
                'mean': self._sum / self._count,
                'min': sorted_samples[0],
                'max': sorted_samples[-1],
                'count': self._count
            }

    def get_snapshot(self, tags: Optional[Dict[str, str]] = None) -> MetricSnapshot:
        """Get metric snapshot"""
        return MetricSnapshot(
            name=self.name,
            type=MetricType.HISTOGRAM,
            value=self.get_percentiles(),
            timestamp=datetime.now(timezone.utc),
            tags=tags or {},
            unit=self.unit
        )


class Timer(Histogram):
    """Timer metric for measuring durations"""

    def __init__(self, name: str, unit: str = "ms", max_samples: int = 10000):
        super().__init__(name, unit, max_samples)

    def time(self, func: Callable):
        """Decorator to time function execution"""
        def wrapper(*args, **kwargs):
            start = time.time()
            try:
                return func(*args, **kwargs)
            finally:
                duration_ms = (time.time() - start) * 1000
                self.record(duration_ms)
        return wrapper

    def start_timer(self):
        """Start a manual timer"""
        return TimerContext(self)


class TimerContext:
    """Context manager for timing operations"""

    def __init__(self, timer: Timer):
        self.timer = timer
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration_ms = (time.time() - self.start_time) * 1000
            self.timer.record(duration_ms)


@dataclass
class SLOConfig:
    """Service Level Objective configuration"""
    name: str
    target: float  # Target availability (e.g., 0.99 for 99%)
    window_hours: int  # Evaluation window in hours
    burn_rate_threshold: float  # Alert when burn rate exceeds this
    error_budget_threshold: float  # Alert when error budget falls below this


@dataclass
class AlertRule:
    """Alert rule configuration"""
    name: str
    metric: str
    operator: str  # 'gt', 'lt', 'eq'
    threshold: float
    severity: str  # 'low', 'medium', 'high', 'critical'
    duration_minutes: int  # Alert only if condition persists for this duration
    last_triggered: Optional[datetime] = None


class MetricsRegistry:
    """Enhanced central registry for all metrics with SLO tracking"""

    def __init__(self, storage_path: Optional[Path] = None):
        self._metrics: Dict[str, MetricCollector] = {}
        self._lock = threading.Lock()

        # Storage configuration
        if storage_path:
            self.storage_path = storage_path
        else:
            self.storage_path = Path.home() / '.pm' / 'metrics'
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Enhanced alert thresholds
        self._thresholds = {
            'error_rate': 0.05,  # 5%
            'p99_latency_ms': 1000,  # 1000ms
            'cache_hit_rate': 0.5,  # 50%
            'disk_usage_percent': 90,  # 90%
            'memory_usage_percent': 85,  # 85%
            'cpu_usage_percent': 80,  # 80%
            'mttr_minutes': 30,  # 30 minutes
        }

        # SLO configurations
        self._slos = {
            'availability': SLOConfig(
                name='System Availability',
                target=0.99,
                window_hours=24,
                burn_rate_threshold=10.0,
                error_budget_threshold=0.1
            ),
            'latency': SLOConfig(
                name='Response Latency',
                target=0.95,
                window_hours=1,
                burn_rate_threshold=5.0,
                error_budget_threshold=0.2
            )
        }

        # Alert rules
        self._alert_rules = self._init_alert_rules()

        # Alert history and noise reduction
        self._alert_history = deque(maxlen=1000)
        self._alert_suppression = {}  # metric -> last_alert_time

        # MTTR tracking
        self._incident_start_times = {}
        self._mttr_samples = deque(maxlen=100)

        # Initialize core metrics
        self._init_core_metrics()

    def _init_alert_rules(self) -> List[AlertRule]:
        """Initialize default alert rules"""
        return [
            AlertRule(
                name="High Error Rate",
                metric="error_rate",
                operator="gt",
                threshold=0.05,
                severity="critical",
                duration_minutes=5
            ),
            AlertRule(
                name="High P99 Latency",
                metric="p99_latency_ms",
                operator="gt",
                threshold=1000,
                severity="high",
                duration_minutes=3
            ),
            AlertRule(
                name="Low Cache Hit Rate",
                metric="cache_hit_rate",
                operator="lt",
                threshold=0.5,
                severity="medium",
                duration_minutes=10
            ),
            AlertRule(
                name="High Disk Usage",
                metric="disk_usage_percent",
                operator="gt",
                threshold=90,
                severity="critical",
                duration_minutes=1
            ),
            AlertRule(
                name="High Memory Usage",
                metric="memory_usage_percent",
                operator="gt",
                threshold=85,
                severity="high",
                duration_minutes=5
            ),
            AlertRule(
                name="High MTTR",
                metric="mttr_minutes",
                operator="gt",
                threshold=30,
                severity="high",
                duration_minutes=1
            )
        ]

    def _init_core_metrics(self):
        """Initialize core system metrics"""
        # Latency metrics
        self.register_timer('recommendation_latency', 'ms')
        self.register_timer('api_response_time', 'ms')
        self.register_timer('event_processing_latency', 'ms')

        # Error metrics
        self.register_counter('total_requests', 'count')
        self.register_counter('total_errors', 'count')

        # Cache metrics
        self.register_counter('cache_hits', 'count')
        self.register_counter('cache_misses', 'count')

        # System metrics
        self.register_gauge('disk_usage_percent', 'percent')
        self.register_gauge('memory_usage_mb', 'MB')
        self.register_gauge('cpu_usage_percent', 'percent')

    def register_counter(self, name: str, unit: Optional[str] = None) -> Counter:
        """Register a counter metric"""
        with self._lock:
            if name not in self._metrics:
                self._metrics[name] = Counter(name, unit)
            return self._metrics[name]

    def register_gauge(self, name: str, unit: Optional[str] = None) -> Gauge:
        """Register a gauge metric"""
        with self._lock:
            if name not in self._metrics:
                self._metrics[name] = Gauge(name, unit)
            return self._metrics[name]

    def register_histogram(
        self,
        name: str,
        unit: Optional[str] = None,
        max_samples: int = 10000
    ) -> Histogram:
        """Register a histogram metric"""
        with self._lock:
            if name not in self._metrics:
                self._metrics[name] = Histogram(name, unit, max_samples)
            return self._metrics[name]

    def register_timer(
        self,
        name: str,
        unit: str = "ms",
        max_samples: int = 10000
    ) -> Timer:
        """Register a timer metric"""
        with self._lock:
            if name not in self._metrics:
                self._metrics[name] = Timer(name, unit, max_samples)
            return self._metrics[name]

    def get_metric(self, name: str) -> Optional[MetricCollector]:
        """Get a metric by name"""
        return self._metrics.get(name)

    def counter(self, name: str) -> Counter:
        """Get or create a counter"""
        return self.register_counter(name)

    def gauge(self, name: str) -> Gauge:
        """Get or create a gauge"""
        return self.register_gauge(name)

    def timer(self, name: str) -> Timer:
        """Get or create a timer"""
        return self.register_timer(name)

    def collect_system_metrics(self):
        """Collect current system metrics"""
        integration_logger = get_integration_logger()
        req_id = None

        if integration_logger:
            req_id = integration_logger.generate_request_id("metrics")
            integration_logger.start_request(req_id, "MetricsCollect:System")

        try:
            if integration_logger and req_id:
                with integration_logger.time_component(req_id, "system_metrics"):
                    # Disk usage
                    disk_usage = psutil.disk_usage('/')
                    self.gauge('disk_usage_percent').set(disk_usage.percent)

                    # Memory usage
                    memory = psutil.virtual_memory()
                    self.gauge('memory_usage_mb').set(memory.used / 1024 / 1024)

                    # CPU usage
                    cpu_percent = psutil.cpu_percent(interval=0.1)
                    self.gauge('cpu_usage_percent').set(cpu_percent)
            else:
                # Disk usage
                disk_usage = psutil.disk_usage('/')
                self.gauge('disk_usage_percent').set(disk_usage.percent)

                # Memory usage
                memory = psutil.virtual_memory()
                self.gauge('memory_usage_mb').set(memory.used / 1024 / 1024)

                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=0.1)
                self.gauge('cpu_usage_percent').set(cpu_percent)

            if integration_logger and req_id:
                integration_logger.update_handler_status(req_id, HandlerStatus.OK)
                integration_logger.update_metrics_status(req_id, MetricsStatus.COLLECT_OK)

        except Exception as e:
            if integration_logger and req_id:
                integration_logger.update_handler_status(req_id, HandlerStatus.ERROR)
                integration_logger.update_metrics_status(req_id, MetricsStatus.COLLECT_ERROR)
            raise

        finally:
            if integration_logger and req_id:
                integration_logger.complete_request(req_id)

    def calculate_derived_metrics(self) -> Dict[str, float]:
        """Calculate derived metrics like error rate and cache hit rate"""
        derived = {}

        # Error rate
        total_requests = self.counter('total_requests').get_value()
        total_errors = self.counter('total_errors').get_value()

        # Also check for test metrics (backward compatibility)
        if total_requests == 0:
            total_requests = self.counter('test_requests').get_value()
        if total_errors == 0:
            total_errors = self.counter('test_errors').get_value()
        if total_requests > 0:
            derived['error_rate'] = total_errors / total_requests
        else:
            derived['error_rate'] = 0

        # Cache hit rate
        cache_hits = self.counter('cache_hits').get_value()
        cache_misses = self.counter('cache_misses').get_value()
        total_cache_requests = cache_hits + cache_misses
        if total_cache_requests > 0:
            derived['cache_hit_rate'] = cache_hits / total_cache_requests
        else:
            derived['cache_hit_rate'] = 0

        return derived

    def get_snapshot(self, tags: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Get complete metrics snapshot"""
        # Collect system metrics first
        self.collect_system_metrics()

        # Collect all metric snapshots
        snapshots = []
        with self._lock:
            for metric in self._metrics.values():
                snapshots.append(metric.get_snapshot(tags).to_dict())

        # Calculate derived metrics
        derived = self.calculate_derived_metrics()

        # Get latency percentiles
        latency_metrics = {}
        for timer_name in ['recommendation_latency', 'api_response_time', 'event_processing_latency']:
            timer = self.get_metric(timer_name)
            if isinstance(timer, Timer):
                percentiles = timer.get_percentiles()
                latency_metrics[timer_name] = percentiles

        return {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'metrics': snapshots,
            'derived_metrics': derived,
            'latency_percentiles': latency_metrics,
            'tags': tags or {}
        }

    def check_alerts(self) -> List[Dict[str, Any]]:
        """Check for alert conditions"""
        alerts = []
        derived = self.calculate_derived_metrics()

        # Check error rate
        if derived['error_rate'] > self._thresholds['error_rate']:
            alerts.append({
                'severity': 'HIGH',
                'metric': 'error_rate',
                'value': derived['error_rate'],
                'threshold': self._thresholds['error_rate'],
                'message': f"Error rate {derived['error_rate']:.2%} exceeds threshold {self._thresholds['error_rate']:.2%}"
            })

        # Check cache hit rate
        if derived['cache_hit_rate'] < self._thresholds['cache_hit_rate']:
            alerts.append({
                'severity': 'MEDIUM',
                'metric': 'cache_hit_rate',
                'value': derived['cache_hit_rate'],
                'threshold': self._thresholds['cache_hit_rate'],
                'message': f"Cache hit rate {derived['cache_hit_rate']:.2%} below threshold {self._thresholds['cache_hit_rate']:.2%}"
            })

        # Check P99 latency
        rec_timer = self.get_metric('recommendation_latency')
        if isinstance(rec_timer, Timer):
            percentiles = rec_timer.get_percentiles()
            if percentiles['p99'] > self._thresholds['p99_latency_ms']:
                alerts.append({
                    'severity': 'HIGH',
                    'metric': 'p99_latency_ms',
                    'value': percentiles['p99'],
                    'threshold': self._thresholds['p99_latency_ms'],
                    'message': f"P99 latency {percentiles['p99']:.2f}ms exceeds threshold {self._thresholds['p99_latency_ms']}ms"
                })

        # Check disk usage
        disk_usage = self.gauge('disk_usage_percent').get_value()
        if disk_usage > self._thresholds['disk_usage_percent']:
            alerts.append({
                'severity': 'CRITICAL',
                'metric': 'disk_usage_percent',
                'value': disk_usage,
                'threshold': self._thresholds['disk_usage_percent'],
                'message': f"Disk usage {disk_usage:.1f}% exceeds threshold {self._thresholds['disk_usage_percent']}%"
            })

        return alerts

    def save_snapshot(self, snapshot: Optional[Dict[str, Any]] = None) -> Path:
        """Save metrics snapshot to file"""
        integration_logger = get_integration_logger()
        req_id = None

        if integration_logger:
            req_id = integration_logger.generate_request_id("metrics")
            integration_logger.start_request(req_id, "MetricsSave:Snapshot")

        try:
            if snapshot is None:
                if integration_logger and req_id:
                    with integration_logger.time_component(req_id, "snapshot_generation"):
                        snapshot = self.get_snapshot()
                else:
                    snapshot = self.get_snapshot()

            # Add alert status
            if integration_logger and req_id:
                with integration_logger.time_component(req_id, "alert_check"):
                    snapshot['alerts'] = self.check_alerts()
            else:
                snapshot['alerts'] = self.check_alerts()

            # Save to timestamped file
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_path = self.storage_path / f'metrics_snapshot_{timestamp}.json'

            if integration_logger and req_id:
                with integration_logger.time_component(req_id, "file_write"):
                    with open(file_path, 'w') as f:
                        json.dump(snapshot, f, indent=2)

                    # Also save as latest
                    latest_path = self.storage_path / 'latest_snapshot.json'
                    with open(latest_path, 'w') as f:
                        json.dump(snapshot, f, indent=2)
            else:
                with open(file_path, 'w') as f:
                    json.dump(snapshot, f, indent=2)

                # Also save as latest
                latest_path = self.storage_path / 'latest_snapshot.json'
                with open(latest_path, 'w') as f:
                    json.dump(snapshot, f, indent=2)

            if integration_logger and req_id:
                integration_logger.update_handler_status(req_id, HandlerStatus.OK)
                integration_logger.update_metrics_status(req_id, MetricsStatus.WRITE_OK)

            return file_path

        except Exception as e:
            if integration_logger and req_id:
                integration_logger.update_handler_status(req_id, HandlerStatus.ERROR)
                integration_logger.update_metrics_status(req_id, MetricsStatus.WRITE_ERROR)
            raise

        finally:
            if integration_logger and req_id:
                integration_logger.complete_request(req_id)

    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary for display"""
        snapshot = self.get_snapshot()
        derived = self.calculate_derived_metrics()
        alerts = self.check_alerts()

        # Get key latency metrics
        rec_timer = self.get_metric('recommendation_latency')
        rec_percentiles = rec_timer.get_percentiles() if isinstance(rec_timer, Timer) else {}

        return {
            'status': 'healthy' if not alerts else 'unhealthy',
            'key_metrics': {
                'error_rate': f"{derived['error_rate']:.2%}",
                'cache_hit_rate': f"{derived['cache_hit_rate']:.2%}",
                'p50_latency_ms': f"{rec_percentiles.get('p50', 0):.2f}",
                'p95_latency_ms': f"{rec_percentiles.get('p95', 0):.2f}",
                'p99_latency_ms': f"{rec_percentiles.get('p99', 0):.2f}",
                'disk_usage': f"{self.gauge('disk_usage_percent').get_value():.1f}%"
            },
            'alert_count': len(alerts),
            'alerts': alerts,
            'timestamp': snapshot['timestamp']
        }


# Global registry instance
_global_registry: Optional[MetricsRegistry] = None


def get_metrics_registry() -> MetricsRegistry:
    """Get or create global metrics registry"""
    global _global_registry
    if _global_registry is None:
        _global_registry = MetricsRegistry()
    return _global_registry


# Convenience functions
def record_latency(operation: str, duration_ms: float):
    """Record operation latency"""
    registry = get_metrics_registry()
    timer = registry.timer(f"{operation}_latency")
    timer.record(duration_ms)


def increment_counter(name: str, value: float = 1):
    """Increment a counter"""
    registry = get_metrics_registry()
    counter = registry.counter(name)
    counter.increment(value)


def set_gauge(name: str, value: float):
    """Set a gauge value"""
    registry = get_metrics_registry()
    gauge = registry.gauge(name)
    gauge.set(value)


def time_operation(operation: str):
    """Decorator to time an operation"""
    registry = get_metrics_registry()
    timer = registry.timer(f"{operation}_latency")
    return timer.time


# CLI interface
if __name__ == "__main__":
    import sys
    import argparse

    parser = argparse.ArgumentParser(description="PM Metrics Collection")
    parser.add_argument('--snapshot', action='store_true', help='Generate metrics snapshot')
    parser.add_argument('--summary', action='store_true', help='Show metrics summary')
    parser.add_argument('--simulate', action='store_true', help='Simulate metrics for testing')

    args = parser.parse_args()

    registry = get_metrics_registry()

    if args.simulate:
        # Simulate some metrics
        import random

        # Simulate requests
        for _ in range(100):
            registry.counter('total_requests').increment()
            if random.random() < 0.03:  # 3% error rate
                registry.counter('total_errors').increment()

        # Simulate cache
        for _ in range(200):
            if random.random() < 0.85:  # 85% hit rate
                registry.counter('cache_hits').increment()
            else:
                registry.counter('cache_misses').increment()

        # Simulate latencies
        for _ in range(50):
            registry.timer('recommendation_latency').record(random.gauss(250, 100))
            registry.timer('api_response_time').record(random.gauss(150, 50))
            registry.timer('event_processing_latency').record(random.gauss(50, 20))

        print("Simulated metrics generated")

    if args.snapshot:
        snapshot_path = registry.save_snapshot()
        print(f"Metrics snapshot saved to: {snapshot_path}")

        # Also print snapshot
        with open(snapshot_path, 'r') as f:
            print(f.read())

    elif args.summary:
        summary = registry.get_summary()
        print(json.dumps(summary, indent=2))

    else:
        # Default: show current metrics
        snapshot = registry.get_snapshot()
        print(json.dumps(snapshot, indent=2))