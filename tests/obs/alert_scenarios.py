"""OBS-O2 Alert Testing Scenarios

Comprehensive alert tuning test scenarios for achieving:
- <5% false positive rate
- 0% false negative rate
- Optimal alert threshold tuning

Test Categories:
1. Network failures
2. High latency scenarios
3. Error rate spikes
4. Resource exhaustion
5. Cascading failures
"""

import time
import random
import json
import threading
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import unittest
from unittest.mock import Mock, patch
import psutil

from src.pm.obs.metrics import (
    MetricsRegistry, Counter, Gauge, Timer, Histogram,
    AlertRule, SLOConfig
)


@dataclass
class FailureScenario:
    """Represents a failure scenario for testing"""
    name: str
    category: str
    description: str
    duration_seconds: int
    expected_alerts: List[str]
    false_positive_risk: float  # 0.0 - 1.0
    severity: str  # 'low', 'medium', 'high', 'critical'

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AlertTestResult:
    """Result of an alert test scenario"""
    scenario_name: str
    expected_alerts: List[str]
    triggered_alerts: List[str]
    false_positives: List[str]
    false_negatives: List[str]
    alert_latency_ms: float
    test_duration_seconds: float
    timestamp: datetime

    @property
    def false_positive_rate(self) -> float:
        total_alerts = len(self.triggered_alerts)
        return len(self.false_positives) / max(total_alerts, 1)

    @property
    def false_negative_rate(self) -> float:
        total_expected = len(self.expected_alerts)
        return len(self.false_negatives) / max(total_expected, 1)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['false_positive_rate'] = self.false_positive_rate
        data['false_negative_rate'] = self.false_negative_rate
        return data


class AlertTestEngine:
    """Engine for running alert testing scenarios"""

    def __init__(self, metrics_registry: Optional[MetricsRegistry] = None):
        self.registry = metrics_registry or MetricsRegistry()
        self.scenarios = self._init_scenarios()
        self.test_results: List[AlertTestResult] = []
        self.alert_history: List[Dict[str, Any]] = []

        # Enhanced thresholds for testing
        self.test_thresholds = {
            'error_rate': {
                'warning': 0.02,    # 2%
                'critical': 0.05,   # 5%
            },
            'p99_latency_ms': {
                'warning': 500,     # 500ms
                'critical': 1000,   # 1000ms
            },
            'cache_hit_rate': {
                'warning': 0.7,     # 70%
                'critical': 0.5,    # 50%
            },
            'cpu_usage_percent': {
                'warning': 70,      # 70%
                'critical': 85,     # 85%
            },
            'memory_usage_percent': {
                'warning': 75,      # 75%
                'critical': 90,     # 90%
            },
            'disk_usage_percent': {
                'warning': 80,      # 80%
                'critical': 95,     # 95%
            }
        }

    def _init_scenarios(self) -> List[FailureScenario]:
        """Initialize comprehensive failure scenarios"""
        scenarios = []

        # Network Failure Scenarios
        scenarios.extend([
            FailureScenario(
                name="network_timeout_cascade",
                category="network",
                description="Gradual network timeout increase leading to cascade",
                duration_seconds=60,
                expected_alerts=["High P99 Latency", "High Error Rate"],
                false_positive_risk=0.1,
                severity="critical"
            ),
            FailureScenario(
                name="network_partition_partial",
                category="network",
                description="Partial network partition affecting 30% of requests",
                duration_seconds=45,
                expected_alerts=["High Error Rate"],
                false_positive_risk=0.15,
                severity="high"
            ),
            FailureScenario(
                name="dns_resolution_failure",
                category="network",
                description="DNS resolution failures causing timeouts",
                duration_seconds=30,
                expected_alerts=["High P99 Latency", "High Error Rate"],
                false_positive_risk=0.05,
                severity="critical"
            ),
            FailureScenario(
                name="network_jitter_burst",
                category="network",
                description="High network jitter causing intermittent failures",
                duration_seconds=90,
                expected_alerts=["High P99 Latency"],
                false_positive_risk=0.2,
                severity="medium"
            ),
            FailureScenario(
                name="bandwidth_saturation",
                category="network",
                description="Network bandwidth saturation slowing responses",
                duration_seconds=120,
                expected_alerts=["High P99 Latency"],
                false_positive_risk=0.1,
                severity="high"
            )
        ])

        # High Latency Scenarios
        scenarios.extend([
            FailureScenario(
                name="database_lock_contention",
                category="latency",
                description="Database lock contention causing query delays",
                duration_seconds=75,
                expected_alerts=["High P99 Latency"],
                false_positive_risk=0.08,
                severity="high"
            ),
            FailureScenario(
                name="cache_miss_storm",
                category="latency",
                description="Cache invalidation causing miss storm",
                duration_seconds=40,
                expected_alerts=["Low Cache Hit Rate", "High P99 Latency"],
                false_positive_risk=0.12,
                severity="medium"
            ),
            FailureScenario(
                name="gc_pause_spikes",
                category="latency",
                description="Garbage collection pauses causing latency spikes",
                duration_seconds=35,
                expected_alerts=["High P99 Latency"],
                false_positive_risk=0.15,
                severity="medium"
            ),
            FailureScenario(
                name="io_wait_burst",
                category="latency",
                description="High I/O wait times from disk congestion",
                duration_seconds=50,
                expected_alerts=["High P99 Latency"],
                false_positive_risk=0.1,
                severity="high"
            ),
            FailureScenario(
                name="cpu_throttling_thermal",
                category="latency",
                description="CPU thermal throttling causing performance degradation",
                duration_seconds=180,
                expected_alerts=["High P99 Latency", "High CPU Usage"],
                false_positive_risk=0.05,
                severity="critical"
            )
        ])

        # Error Rate Spike Scenarios
        scenarios.extend([
            FailureScenario(
                name="dependency_service_failure",
                category="errors",
                description="External dependency service complete failure",
                duration_seconds=25,
                expected_alerts=["High Error Rate"],
                false_positive_risk=0.02,
                severity="critical"
            ),
            FailureScenario(
                name="authentication_service_down",
                category="errors",
                description="Authentication service downtime",
                duration_seconds=20,
                expected_alerts=["High Error Rate"],
                false_positive_risk=0.01,
                severity="critical"
            ),
            FailureScenario(
                name="rate_limit_breach",
                category="errors",
                description="API rate limits exceeded causing 429 errors",
                duration_seconds=60,
                expected_alerts=["High Error Rate"],
                false_positive_risk=0.3,
                severity="medium"
            ),
            FailureScenario(
                name="malformed_request_surge",
                category="errors",
                description="Surge of malformed requests causing validation errors",
                duration_seconds=45,
                expected_alerts=["High Error Rate"],
                false_positive_risk=0.25,
                severity="medium"
            ),
            FailureScenario(
                name="circuit_breaker_cascade",
                category="errors",
                description="Circuit breaker activation cascading across services",
                duration_seconds=90,
                expected_alerts=["High Error Rate"],
                false_positive_risk=0.1,
                severity="critical"
            )
        ])

        # Resource Exhaustion Scenarios
        scenarios.extend([
            FailureScenario(
                name="memory_leak_gradual",
                category="resources",
                description="Gradual memory leak leading to OOM",
                duration_seconds=300,
                expected_alerts=["High Memory Usage"],
                false_positive_risk=0.05,
                severity="critical"
            ),
            FailureScenario(
                name="disk_space_exhaustion",
                category="resources",
                description="Rapid disk space consumption",
                duration_seconds=120,
                expected_alerts=["High Disk Usage"],
                false_positive_risk=0.02,
                severity="critical"
            ),
            FailureScenario(
                name="file_descriptor_leak",
                category="resources",
                description="File descriptor leak causing resource exhaustion",
                duration_seconds=90,
                expected_alerts=["High Error Rate"],
                false_positive_risk=0.08,
                severity="high"
            ),
            FailureScenario(
                name="connection_pool_exhaustion",
                category="resources",
                description="Database connection pool exhaustion",
                duration_seconds=40,
                expected_alerts=["High Error Rate", "High P99 Latency"],
                false_positive_risk=0.1,
                severity="critical"
            ),
            FailureScenario(
                name="cpu_spike_sustained",
                category="resources",
                description="Sustained high CPU usage from runaway process",
                duration_seconds=150,
                expected_alerts=["High CPU Usage", "High P99 Latency"],
                false_positive_risk=0.05,
                severity="high"
            )
        ])

        # Cascading Failure Scenarios
        scenarios.extend([
            FailureScenario(
                name="cache_db_cascade",
                category="cascade",
                description="Cache failure leading to database overload",
                duration_seconds=180,
                expected_alerts=["Low Cache Hit Rate", "High P99 Latency", "High Error Rate"],
                false_positive_risk=0.08,
                severity="critical"
            ),
            FailureScenario(
                name="load_balancer_node_failure",
                category="cascade",
                description="Load balancer node failure causing traffic redistribution",
                duration_seconds=60,
                expected_alerts=["High P99 Latency", "High CPU Usage"],
                false_positive_risk=0.12,
                severity="high"
            ),
            FailureScenario(
                name="monitoring_system_failure",
                category="cascade",
                description="Monitoring system failure masking other issues",
                duration_seconds=300,
                expected_alerts=[],  # Should detect monitoring failure itself
                false_positive_risk=0.9,  # High risk as we lose visibility
                severity="critical"
            ),
            FailureScenario(
                name="deployment_rollback_cascade",
                category="cascade",
                description="Failed deployment causing multiple service failures",
                duration_seconds=120,
                expected_alerts=["High Error Rate", "High P99 Latency"],
                false_positive_risk=0.15,
                severity="critical"
            ),
            FailureScenario(
                name="thundering_herd_effect",
                category="cascade",
                description="Cache expiration causing thundering herd to database",
                duration_seconds=30,
                expected_alerts=["Low Cache Hit Rate", "High P99 Latency"],
                false_positive_risk=0.2,
                severity="high"
            )
        ])

        # Additional complex scenarios to reach N≥50
        scenarios.extend([
            FailureScenario(
                name="ssl_certificate_expiry",
                category="errors",
                description="SSL certificate expiry causing connection failures",
                duration_seconds=15,
                expected_alerts=["High Error Rate"],
                false_positive_risk=0.01,
                severity="critical"
            ),
            FailureScenario(
                name="redis_cluster_split_brain",
                category="errors",
                description="Redis cluster split-brain scenario",
                duration_seconds=90,
                expected_alerts=["High Error Rate", "Low Cache Hit Rate"],
                false_positive_risk=0.1,
                severity="critical"
            ),
            FailureScenario(
                name="log_disk_full",
                category="resources",
                description="Log disk full causing application hangs",
                duration_seconds=60,
                expected_alerts=["High Disk Usage", "High P99 Latency"],
                false_positive_risk=0.05,
                severity="critical"
            ),
            FailureScenario(
                name="timezone_boundary_bug",
                category="errors",
                description="Timezone boundary causing timestamp validation errors",
                duration_seconds=30,
                expected_alerts=["High Error Rate"],
                false_positive_risk=0.4,
                severity="low"
            ),
            FailureScenario(
                name="backup_process_interference",
                category="latency",
                description="Backup process causing I/O interference",
                duration_seconds=240,
                expected_alerts=["High P99 Latency"],
                false_positive_risk=0.3,
                severity="medium"
            )
        ])

        return scenarios

    async def simulate_network_failure(self, scenario: FailureScenario) -> None:
        """Simulate network failure scenarios"""
        if scenario.name == "network_timeout_cascade":
            # Gradually increase latency and error rate
            for i in range(scenario.duration_seconds):
                latency_base = 200 + (i * 20)  # Increase latency over time
                error_rate = min(0.1, i * 0.002)  # Gradually increase error rate

                # Simulate requests with increasing latency
                for _ in range(10):
                    latency = latency_base + random.gauss(0, 50)
                    self.registry.timer('api_response_time').record(latency)

                    # Simulate errors
                    if random.random() < error_rate:
                        self.registry.counter('total_errors').increment()
                    self.registry.counter('total_requests').increment()

                await asyncio.sleep(1)

        elif scenario.name == "network_partition_partial":
            # 30% of requests fail due to network partition
            for i in range(scenario.duration_seconds):
                for _ in range(15):
                    if random.random() < 0.3:  # 30% failure rate
                        self.registry.counter('total_errors').increment()
                        self.registry.timer('api_response_time').record(5000)  # Timeout
                    else:
                        self.registry.timer('api_response_time').record(random.gauss(150, 30))
                    self.registry.counter('total_requests').increment()
                await asyncio.sleep(1)

        elif scenario.name == "dns_resolution_failure":
            # DNS failures causing very high latency and errors
            for i in range(scenario.duration_seconds):
                for _ in range(12):
                    if random.random() < 0.4:  # 40% DNS failure rate
                        self.registry.counter('total_errors').increment()
                        self.registry.timer('api_response_time').record(3000)  # DNS timeout
                    else:
                        self.registry.timer('api_response_time').record(random.gauss(200, 50))
                    self.registry.counter('total_requests').increment()
                await asyncio.sleep(1)

        elif scenario.name == "network_jitter_burst":
            # High jitter causing variable latency
            for i in range(scenario.duration_seconds):
                for _ in range(8):
                    # High variance in latency due to jitter
                    latency = random.gauss(400, 200)  # High variance
                    latency = max(50, latency)  # Minimum 50ms
                    self.registry.timer('api_response_time').record(latency)
                    self.registry.counter('total_requests').increment()
                await asyncio.sleep(1)

        elif scenario.name == "bandwidth_saturation":
            # Bandwidth saturation causing slower responses
            for i in range(scenario.duration_seconds):
                for _ in range(5):
                    # Slower responses due to bandwidth limits
                    latency = random.gauss(800, 100)  # Consistently high latency
                    self.registry.timer('api_response_time').record(latency)
                    self.registry.counter('total_requests').increment()
                await asyncio.sleep(1)

    async def simulate_latency_scenario(self, scenario: FailureScenario) -> None:
        """Simulate high latency scenarios"""
        if scenario.name == "database_lock_contention":
            # Database locks causing query delays
            for i in range(scenario.duration_seconds):
                for _ in range(8):
                    # Some queries are very slow due to locks
                    if random.random() < 0.3:  # 30% of queries affected
                        latency = random.gauss(2000, 300)  # Very slow queries
                    else:
                        latency = random.gauss(100, 20)  # Normal queries
                    self.registry.timer('api_response_time').record(latency)
                    self.registry.counter('total_requests').increment()
                await asyncio.sleep(1)

        elif scenario.name == "cache_miss_storm":
            # Cache miss storm causing increased latency and reduced hit rate
            for i in range(scenario.duration_seconds):
                for _ in range(20):
                    # Most cache requests miss during storm
                    if random.random() < 0.8:  # 80% miss rate during storm
                        self.registry.counter('cache_misses').increment()
                        latency = random.gauss(300, 50)  # Slower due to cache miss
                    else:
                        self.registry.counter('cache_hits').increment()
                        latency = random.gauss(50, 10)  # Fast cache hit

                    self.registry.timer('api_response_time').record(latency)
                    self.registry.counter('total_requests').increment()
                await asyncio.sleep(1)

        elif scenario.name == "gc_pause_spikes":
            # GC pauses causing periodic latency spikes
            for i in range(scenario.duration_seconds):
                for _ in range(10):
                    # Periodic GC pauses
                    if i % 10 == 0 and random.random() < 0.5:  # GC pause every 10 seconds
                        latency = random.gauss(1500, 200)  # GC pause latency
                    else:
                        latency = random.gauss(80, 15)  # Normal latency

                    self.registry.timer('api_response_time').record(latency)
                    self.registry.counter('total_requests').increment()
                await asyncio.sleep(1)

        elif scenario.name == "io_wait_burst":
            # I/O wait causing latency spikes
            for i in range(scenario.duration_seconds):
                for _ in range(6):
                    # I/O wait affects some requests
                    if random.random() < 0.4:  # 40% affected by I/O wait
                        latency = random.gauss(1200, 150)
                    else:
                        latency = random.gauss(120, 25)

                    self.registry.timer('api_response_time').record(latency)
                    self.registry.counter('total_requests').increment()
                await asyncio.sleep(1)

        elif scenario.name == "cpu_throttling_thermal":
            # CPU throttling causing sustained performance degradation
            for i in range(scenario.duration_seconds):
                # Simulate high CPU usage
                cpu_usage = min(95, 60 + (i * 0.2))  # Gradually increasing CPU
                self.registry.gauge('cpu_usage_percent').set(cpu_usage)

                for _ in range(4):
                    # Slower responses due to throttling
                    throttle_factor = 1 + (cpu_usage - 60) / 40  # 1x to 1.875x slower
                    latency = random.gauss(200, 40) * throttle_factor
                    self.registry.timer('api_response_time').record(latency)
                    self.registry.counter('total_requests').increment()
                await asyncio.sleep(1)

    async def simulate_error_scenario(self, scenario: FailureScenario) -> None:
        """Simulate error rate spike scenarios"""
        if scenario.name == "dependency_service_failure":
            # Complete dependency failure
            for i in range(scenario.duration_seconds):
                for _ in range(15):
                    # High error rate due to dependency failure
                    if random.random() < 0.8:  # 80% error rate
                        self.registry.counter('total_errors').increment()
                    self.registry.counter('total_requests').increment()
                await asyncio.sleep(1)

        elif scenario.name == "authentication_service_down":
            # Auth service down causing authentication failures
            for i in range(scenario.duration_seconds):
                for _ in range(18):
                    # Very high error rate for auth failures
                    if random.random() < 0.9:  # 90% error rate
                        self.registry.counter('total_errors').increment()
                    self.registry.counter('total_requests').increment()
                await asyncio.sleep(1)

        elif scenario.name == "rate_limit_breach":
            # Rate limiting causing 429 errors
            for i in range(scenario.duration_seconds):
                for _ in range(25):  # High request rate
                    # Some requests rate limited
                    if random.random() < 0.3:  # 30% rate limited
                        self.registry.counter('total_errors').increment()
                    self.registry.counter('total_requests').increment()
                await asyncio.sleep(1)

        elif scenario.name == "malformed_request_surge":
            # Surge of malformed requests
            for i in range(scenario.duration_seconds):
                for _ in range(20):
                    # Validation errors from malformed requests
                    if random.random() < 0.25:  # 25% malformed
                        self.registry.counter('total_errors').increment()
                    self.registry.counter('total_requests').increment()
                await asyncio.sleep(1)

        elif scenario.name == "circuit_breaker_cascade":
            # Circuit breaker activations cascading
            for i in range(scenario.duration_seconds):
                for _ in range(12):
                    # Errors due to circuit breaker activation
                    failure_rate = min(0.6, 0.1 + (i * 0.005))  # Escalating failures
                    if random.random() < failure_rate:
                        self.registry.counter('total_errors').increment()
                    self.registry.counter('total_requests').increment()
                await asyncio.sleep(1)

    async def simulate_resource_scenario(self, scenario: FailureScenario) -> None:
        """Simulate resource exhaustion scenarios"""
        if scenario.name == "memory_leak_gradual":
            # Gradual memory leak
            base_memory = 50  # 50% base usage
            for i in range(scenario.duration_seconds):
                # Memory increases over time
                memory_usage = base_memory + (i * 0.15)  # Gradual increase
                memory_usage = min(95, memory_usage)
                self.registry.gauge('memory_usage_percent').set(memory_usage)

                # Slower responses as memory fills up
                if memory_usage > 80:
                    latency = random.gauss(300 + (memory_usage - 80) * 20, 50)
                    self.registry.timer('api_response_time').record(latency)
                    self.registry.counter('total_requests').increment()

                await asyncio.sleep(1)

        elif scenario.name == "disk_space_exhaustion":
            # Rapid disk space consumption
            base_disk = 70  # 70% base usage
            for i in range(scenario.duration_seconds):
                # Disk fills up rapidly
                disk_usage = base_disk + (i * 0.2)  # Fast increase
                disk_usage = min(99, disk_usage)
                self.registry.gauge('disk_usage_percent').set(disk_usage)

                # Errors when disk nearly full
                if disk_usage > 95:
                    if random.random() < 0.5:
                        self.registry.counter('total_errors').increment()
                    self.registry.counter('total_requests').increment()

                await asyncio.sleep(1)

        elif scenario.name == "file_descriptor_leak":
            # File descriptor exhaustion causing errors
            for i in range(scenario.duration_seconds):
                for _ in range(10):
                    # Increasing error rate as FDs are exhausted
                    error_rate = min(0.4, i * 0.004)
                    if random.random() < error_rate:
                        self.registry.counter('total_errors').increment()
                    self.registry.counter('total_requests').increment()
                await asyncio.sleep(1)

        elif scenario.name == "connection_pool_exhaustion":
            # Database connection pool exhausted
            for i in range(scenario.duration_seconds):
                for _ in range(12):
                    # High error rate and latency when pool exhausted
                    if random.random() < 0.6:  # 60% error rate
                        self.registry.counter('total_errors').increment()
                        self.registry.timer('api_response_time').record(3000)  # Timeout
                    else:
                        self.registry.timer('api_response_time').record(random.gauss(200, 50))
                    self.registry.counter('total_requests').increment()
                await asyncio.sleep(1)

        elif scenario.name == "cpu_spike_sustained":
            # Sustained high CPU usage
            for i in range(scenario.duration_seconds):
                # High CPU usage throughout
                cpu_usage = 85 + random.gauss(0, 5)  # Around 85% with variance
                cpu_usage = max(70, min(98, cpu_usage))
                self.registry.gauge('cpu_usage_percent').set(cpu_usage)

                for _ in range(6):
                    # Slower responses due to CPU contention
                    latency = random.gauss(400, 80)
                    self.registry.timer('api_response_time').record(latency)
                    self.registry.counter('total_requests').increment()
                await asyncio.sleep(1)

    async def simulate_cascade_scenario(self, scenario: FailureScenario) -> None:
        """Simulate cascading failure scenarios"""
        if scenario.name == "cache_db_cascade":
            # Cache failure leading to database overload
            for i in range(scenario.duration_seconds):
                # Cache hit rate drops dramatically
                for _ in range(15):
                    if random.random() < 0.9:  # 90% miss rate
                        self.registry.counter('cache_misses').increment()
                        # Database overloaded, slow responses and some errors
                        latency = random.gauss(1500, 300)
                        if random.random() < 0.3:  # 30% error rate
                            self.registry.counter('total_errors').increment()
                    else:
                        self.registry.counter('cache_hits').increment()
                        latency = random.gauss(100, 20)

                    self.registry.timer('api_response_time').record(latency)
                    self.registry.counter('total_requests').increment()
                await asyncio.sleep(1)

        elif scenario.name == "load_balancer_node_failure":
            # Load balancer node failure causing traffic redistribution
            for i in range(scenario.duration_seconds):
                # Higher CPU on remaining nodes
                cpu_usage = 75 + random.gauss(0, 5)
                self.registry.gauge('cpu_usage_percent').set(cpu_usage)

                for _ in range(10):
                    # Higher latency due to increased load
                    latency = random.gauss(600, 100)
                    self.registry.timer('api_response_time').record(latency)
                    self.registry.counter('total_requests').increment()
                await asyncio.sleep(1)

        elif scenario.name == "monitoring_system_failure":
            # Monitoring system failure - simulate loss of metrics
            for i in range(scenario.duration_seconds):
                # Reduced metric collection (simulate monitoring failure)
                if random.random() < 0.3:  # Only 30% of metrics collected
                    latency = random.gauss(200, 50)
                    self.registry.timer('api_response_time').record(latency)
                    self.registry.counter('total_requests').increment()
                await asyncio.sleep(1)

        elif scenario.name == "deployment_rollback_cascade":
            # Failed deployment causing multiple service failures
            for i in range(scenario.duration_seconds):
                for _ in range(8):
                    # High error rate from bad deployment
                    if random.random() < 0.5:  # 50% error rate
                        self.registry.counter('total_errors').increment()
                    # High latency from degraded services
                    latency = random.gauss(1000, 200)
                    self.registry.timer('api_response_time').record(latency)
                    self.registry.counter('total_requests').increment()
                await asyncio.sleep(1)

        elif scenario.name == "thundering_herd_effect":
            # Cache expiration causing thundering herd
            for i in range(scenario.duration_seconds):
                for _ in range(25):  # High request rate
                    # Most requests miss cache initially
                    if random.random() < 0.95:  # 95% miss rate
                        self.registry.counter('cache_misses').increment()
                        latency = random.gauss(800, 150)  # Slow due to cache miss
                    else:
                        self.registry.counter('cache_hits').increment()
                        latency = random.gauss(50, 10)

                    self.registry.timer('api_response_time').record(latency)
                    self.registry.counter('total_requests').increment()
                await asyncio.sleep(1)

    async def run_scenario(self, scenario: FailureScenario) -> AlertTestResult:
        """Run a single failure scenario and measure alert response"""
        print(f"Running scenario: {scenario.name}")

        # Reset metrics for clean test
        self.registry = MetricsRegistry()

        # Record start time
        start_time = time.time()
        alert_start_time = start_time

        # Start alert monitoring
        triggered_alerts = []

        def monitor_alerts():
            while time.time() - start_time < scenario.duration_seconds + 10:
                alerts = self.registry.check_alerts()
                for alert in alerts:
                    alert_name = alert.get('metric', 'unknown')
                    if alert_name not in [a['name'] for a in triggered_alerts]:
                        triggered_alerts.append({
                            'name': alert_name,
                            'time': time.time(),
                            'details': alert
                        })
                time.sleep(1)

        # Start monitoring in background
        monitor_thread = threading.Thread(target=monitor_alerts, daemon=True)
        monitor_thread.start()

        # Run the scenario simulation
        try:
            if scenario.category == "network":
                await self.simulate_network_failure(scenario)
            elif scenario.category == "latency":
                await self.simulate_latency_scenario(scenario)
            elif scenario.category == "errors":
                await self.simulate_error_scenario(scenario)
            elif scenario.category == "resources":
                await self.simulate_resource_scenario(scenario)
            elif scenario.category == "cascade":
                await self.simulate_cascade_scenario(scenario)
            else:
                # Generic scenario - simulate basic metrics
                for i in range(scenario.duration_seconds):
                    for _ in range(10):
                        latency = random.gauss(500, 100)
                        self.registry.timer('api_response_time').record(latency)
                        if random.random() < 0.1:
                            self.registry.counter('total_errors').increment()
                        self.registry.counter('total_requests').increment()
                    await asyncio.sleep(1)

        except Exception as e:
            print(f"Error in scenario {scenario.name}: {e}")

        # Wait a bit more for alerts to trigger
        await asyncio.sleep(5)

        # Calculate results
        end_time = time.time()
        test_duration = end_time - start_time

        # Determine alert latency (time to first relevant alert)
        alert_latency = float('inf')
        for alert in triggered_alerts:
            if any(exp_alert in alert['name'] for exp_alert in scenario.expected_alerts):
                alert_latency = min(alert_latency, (alert['time'] - alert_start_time) * 1000)

        if alert_latency == float('inf'):
            alert_latency = 0  # No relevant alert triggered

        # Analyze false positives and negatives
        triggered_alert_names = [alert['name'] for alert in triggered_alerts]
        false_positives = [name for name in triggered_alert_names if name not in scenario.expected_alerts]
        false_negatives = [name for name in scenario.expected_alerts if name not in triggered_alert_names]

        result = AlertTestResult(
            scenario_name=scenario.name,
            expected_alerts=scenario.expected_alerts,
            triggered_alerts=triggered_alert_names,
            false_positives=false_positives,
            false_negatives=false_negatives,
            alert_latency_ms=alert_latency,
            test_duration_seconds=test_duration,
            timestamp=datetime.now(timezone.utc)
        )

        self.test_results.append(result)
        return result

    async def run_all_scenarios(self) -> Dict[str, Any]:
        """Run all failure scenarios and generate comprehensive report"""
        print(f"Starting comprehensive alert testing with {len(self.scenarios)} scenarios...")

        # Run all scenarios
        for i, scenario in enumerate(self.scenarios):
            print(f"Progress: {i+1}/{len(self.scenarios)}")
            result = await self.run_scenario(scenario)
            print(f"Completed {scenario.name}: FP={result.false_positive_rate:.2%}, FN={result.false_negative_rate:.2%}")

            # Brief pause between scenarios
            await asyncio.sleep(2)

        # Generate comprehensive analysis
        return self.generate_test_report()

    def generate_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report with analysis"""
        if not self.test_results:
            return {"error": "No test results available"}

        # Calculate aggregate metrics
        total_scenarios = len(self.test_results)
        total_fp_rate = sum(r.false_positive_rate for r in self.test_results) / total_scenarios
        total_fn_rate = sum(r.false_negative_rate for r in self.test_results) / total_scenarios
        avg_alert_latency = sum(r.alert_latency_ms for r in self.test_results if r.alert_latency_ms > 0) / max(1, len([r for r in self.test_results if r.alert_latency_ms > 0]))

        # Categorize results
        category_stats = {}
        for result in self.test_results:
            scenario = next(s for s in self.scenarios if s.name == result.scenario_name)
            category = scenario.category

            if category not in category_stats:
                category_stats[category] = {
                    'total': 0,
                    'false_positive_rate': 0,
                    'false_negative_rate': 0,
                    'avg_latency_ms': 0
                }

            stats = category_stats[category]
            stats['total'] += 1
            stats['false_positive_rate'] += result.false_positive_rate
            stats['false_negative_rate'] += result.false_negative_rate
            if result.alert_latency_ms > 0:
                stats['avg_latency_ms'] += result.alert_latency_ms

        # Calculate averages
        for category, stats in category_stats.items():
            if stats['total'] > 0:
                stats['false_positive_rate'] /= stats['total']
                stats['false_negative_rate'] /= stats['total']
                stats['avg_latency_ms'] /= stats['total']

        # Performance analysis
        meets_fp_target = total_fp_rate < 0.05  # <5%
        meets_fn_target = total_fn_rate == 0.0  # 0%

        # Identify problematic scenarios
        high_fp_scenarios = [r for r in self.test_results if r.false_positive_rate > 0.1]
        high_fn_scenarios = [r for r in self.test_results if r.false_negative_rate > 0.0]
        slow_alert_scenarios = [r for r in self.test_results if r.alert_latency_ms > 30000]  # >30s

        # Threshold optimization recommendations
        threshold_recommendations = self._generate_threshold_recommendations()

        return {
            "test_summary": {
                "total_scenarios": total_scenarios,
                "scenarios_tested": len(self.scenarios),
                "test_timestamp": datetime.now(timezone.utc).isoformat(),
                "meets_false_positive_target": meets_fp_target,
                "meets_false_negative_target": meets_fn_target
            },
            "performance_metrics": {
                "overall_false_positive_rate": total_fp_rate,
                "overall_false_negative_rate": total_fn_rate,
                "average_alert_latency_ms": avg_alert_latency,
                "false_positive_target": 0.05,
                "false_negative_target": 0.0
            },
            "category_breakdown": category_stats,
            "problematic_scenarios": {
                "high_false_positive": [r.scenario_name for r in high_fp_scenarios],
                "false_negatives": [r.scenario_name for r in high_fn_scenarios],
                "slow_alerts": [r.scenario_name for r in slow_alert_scenarios]
            },
            "threshold_recommendations": threshold_recommendations,
            "detailed_results": [r.to_dict() for r in self.test_results],
            "coverage_analysis": {
                "network_scenarios": len([s for s in self.scenarios if s.category == "network"]),
                "latency_scenarios": len([s for s in self.scenarios if s.category == "latency"]),
                "error_scenarios": len([s for s in self.scenarios if s.category == "errors"]),
                "resource_scenarios": len([s for s in self.scenarios if s.category == "resources"]),
                "cascade_scenarios": len([s for s in self.scenarios if s.category == "cascade"])
            }
        }

    def _generate_threshold_recommendations(self) -> Dict[str, Any]:
        """Generate threshold optimization recommendations based on test results"""
        recommendations = {
            "current_thresholds": self.test_thresholds,
            "optimizations": []
        }

        # Analyze false positive patterns
        fp_by_metric = {}
        for result in self.test_results:
            for fp_alert in result.false_positives:
                if fp_alert not in fp_by_metric:
                    fp_by_metric[fp_alert] = 0
                fp_by_metric[fp_alert] += 1

        # Recommend threshold adjustments
        for metric, fp_count in fp_by_metric.items():
            if fp_count > len(self.test_results) * 0.1:  # >10% false positive rate
                recommendations["optimizations"].append({
                    "metric": metric,
                    "issue": "high_false_positive_rate",
                    "current_fp_rate": fp_count / len(self.test_results),
                    "recommendation": "increase_threshold",
                    "suggested_adjustment": "increase by 20-30%"
                })

        # Analyze false negative patterns
        fn_by_metric = {}
        for result in self.test_results:
            for fn_alert in result.false_negatives:
                if fn_alert not in fn_by_metric:
                    fn_by_metric[fn_alert] = 0
                fn_by_metric[fn_alert] += 1

        for metric, fn_count in fn_by_metric.items():
            if fn_count > 0:  # Any false negatives are critical
                recommendations["optimizations"].append({
                    "metric": metric,
                    "issue": "false_negatives_detected",
                    "false_negative_count": fn_count,
                    "recommendation": "decrease_threshold",
                    "suggested_adjustment": "decrease by 10-20%"
                })

        return recommendations


class TestAlertScenarios(unittest.TestCase):
    """Unit tests for alert scenarios"""

    def setUp(self):
        self.engine = AlertTestEngine()

    def test_scenario_initialization(self):
        """Test that all scenarios are properly initialized"""
        self.assertGreaterEqual(len(self.engine.scenarios), 50)

        # Check scenario categories
        categories = {s.category for s in self.engine.scenarios}
        expected_categories = {"network", "latency", "errors", "resources", "cascade"}
        self.assertEqual(categories, expected_categories)

    def test_metrics_registry_setup(self):
        """Test that metrics registry is properly configured"""
        registry = self.engine.registry

        # Check core metrics are registered
        self.assertIsNotNone(registry.get_metric('total_requests'))
        self.assertIsNotNone(registry.get_metric('total_errors'))
        self.assertIsNotNone(registry.get_metric('api_response_time'))

    async def test_single_scenario_execution(self):
        """Test execution of a single scenario"""
        # Test a simple network scenario
        scenario = next(s for s in self.engine.scenarios if s.name == "network_timeout_cascade")
        result = await self.engine.run_scenario(scenario)

        self.assertEqual(result.scenario_name, scenario.name)
        self.assertIsInstance(result.false_positive_rate, float)
        self.assertIsInstance(result.false_negative_rate, float)
        self.assertGreaterEqual(result.test_duration_seconds, scenario.duration_seconds * 0.8)

    def test_threshold_recommendations(self):
        """Test threshold recommendation generation"""
        # Add some mock test results
        self.engine.test_results = [
            AlertTestResult(
                scenario_name="test_scenario",
                expected_alerts=["High Error Rate"],
                triggered_alerts=["High Error Rate", "High CPU Usage"],
                false_positives=["High CPU Usage"],
                false_negatives=[],
                alert_latency_ms=5000,
                test_duration_seconds=60,
                timestamp=datetime.now(timezone.utc)
            )
        ]

        recommendations = self.engine._generate_threshold_recommendations()
        self.assertIn("current_thresholds", recommendations)
        self.assertIn("optimizations", recommendations)


# Integration with existing PM metrics system
def integrate_with_pm_metrics():
    """Integration function for PM metrics system"""
    from src.pm.obs.metrics import get_metrics_registry

    # Use existing metrics registry
    registry = get_metrics_registry()
    engine = AlertTestEngine(registry)

    return engine


if __name__ == "__main__":
    # CLI interface for running tests
    import argparse
    import asyncio

    parser = argparse.ArgumentParser(description="OBS-O2 Alert Testing")
    parser.add_argument('--scenario', help='Run specific scenario by name')
    parser.add_argument('--category', help='Run all scenarios in category')
    parser.add_argument('--quick', action='store_true', help='Run quick test subset')
    parser.add_argument('--output', help='Output file for results')

    args = parser.parse_args()

    async def main():
        engine = AlertTestEngine()

        if args.scenario:
            # Run specific scenario
            scenario = next((s for s in engine.scenarios if s.name == args.scenario), None)
            if scenario:
                result = await engine.run_scenario(scenario)
                print(json.dumps(result.to_dict(), indent=2))
            else:
                print(f"Scenario '{args.scenario}' not found")
                return

        elif args.category:
            # Run category of scenarios
            scenarios = [s for s in engine.scenarios if s.category == args.category]
            for scenario in scenarios:
                await engine.run_scenario(scenario)
            report = engine.generate_test_report()
            print(json.dumps(report, indent=2))

        elif args.quick:
            # Run subset of scenarios for quick testing
            quick_scenarios = engine.scenarios[:10]  # First 10 scenarios
            engine.scenarios = quick_scenarios
            report = await engine.run_all_scenarios()
            print(json.dumps(report, indent=2))

        else:
            # Run all scenarios
            report = await engine.run_all_scenarios()

            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(report, f, indent=2)
                print(f"Results saved to {args.output}")
            else:
                print(json.dumps(report, indent=2))

    asyncio.run(main())