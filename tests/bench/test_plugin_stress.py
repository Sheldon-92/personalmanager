#!/usr/bin/env python3
"""
Comprehensive Concurrent Plugin Load/Unload Stress Test
Tests concurrent plugin operations with resource tracking and performance metrics

Features:
- Concurrent plugin loading/unloading using multiprocessing and threading
- P95/P99 latency measurements for all operations
- Resource tracking (memory, file handles, threads, network connections)
- Zero resource leak verification (±2% tolerance)
- Statistical analysis and reporting
"""

import asyncio
import gc
import json
import logging
import multiprocessing as mp
import os
import psutil
import queue
import signal
import socket
import sys
import threading
import time
import traceback
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set
import numpy as np
from enum import Enum

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.pm.plugins.sdk import (
    PluginLoader,
    PluginConfigManager,
    HookType,
    HookContext,
    SecurityLevel
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(processName)s - %(threadName)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ===== Configuration =====

@dataclass
class StressTestConfig:
    """Stress test configuration"""
    # Test parameters
    rounds: int = 10
    concurrent_workers: int = 4
    use_multiprocessing: bool = False  # False = threading, True = multiprocessing

    # Plugin selection
    plugin_paths: List[Path] = field(default_factory=list)
    max_plugins_per_worker: int = 3

    # Timing
    load_delay_ms: int = 0  # Delay between loads (milliseconds)
    unload_delay_ms: int = 0  # Delay between unloads
    round_delay_s: float = 1.0  # Delay between rounds

    # Resource tracking
    track_memory: bool = True
    track_file_handles: bool = True
    track_threads: bool = True
    track_network: bool = True
    baseline_samples: int = 5  # Number of baseline measurements
    leak_tolerance_percent: float = 2.0  # Acceptable resource variance

    # Performance thresholds
    max_load_time_ms: float = 500.0
    max_unload_time_ms: float = 200.0
    target_p95_ms: float = 300.0
    target_p99_ms: float = 500.0

    # Output
    output_dir: Path = field(default_factory=lambda: Path("/tmp/plugin_stress_test"))
    save_detailed_metrics: bool = True
    save_resource_timeline: bool = True


class OperationType(Enum):
    """Types of plugin operations"""
    LOAD = "load"
    UNLOAD = "unload"
    RELOAD = "reload"
    HOOK_EXEC = "hook_exec"


@dataclass
class OperationMetric:
    """Metrics for a single operation"""
    operation: OperationType
    plugin_name: str
    worker_id: int
    start_time: float
    end_time: float
    duration_ms: float
    success: bool
    error: Optional[str] = None
    memory_before: Optional[int] = None
    memory_after: Optional[int] = None
    thread_count: Optional[int] = None
    fd_count: Optional[int] = None


@dataclass
class ResourceSnapshot:
    """System resource snapshot"""
    timestamp: float
    memory_rss: int  # Resident Set Size in bytes
    memory_vms: int  # Virtual Memory Size in bytes
    memory_percent: float
    cpu_percent: float
    num_threads: int
    num_fds: int  # File descriptors
    num_connections: int  # Network connections
    gc_stats: Dict[int, int]  # Garbage collection stats by generation

    @classmethod
    def capture(cls, process: Optional[psutil.Process] = None) -> 'ResourceSnapshot':
        """Capture current resource snapshot"""
        if process is None:
            process = psutil.Process()

        # Memory info
        mem_info = process.memory_info()

        # File descriptors (Unix) or handles (Windows)
        try:
            if hasattr(process, 'num_fds'):
                num_fds = process.num_fds()
            else:
                num_fds = len(process.open_files())
        except:
            num_fds = -1

        # Network connections
        try:
            connections = process.connections()
            num_connections = len(connections)
        except:
            num_connections = -1

        # GC stats
        gc_stats = {}
        for i in range(gc.get_count().__len__()):
            gc_stats[i] = gc.get_count()[i]

        return cls(
            timestamp=time.perf_counter(),
            memory_rss=mem_info.rss,
            memory_vms=mem_info.vms,
            memory_percent=process.memory_percent(),
            cpu_percent=process.cpu_percent(),
            num_threads=process.num_threads(),
            num_fds=num_fds,
            num_connections=num_connections,
            gc_stats=gc_stats
        )


@dataclass
class StressTestResults:
    """Aggregated stress test results"""
    config: StressTestConfig
    start_time: datetime
    end_time: datetime
    total_operations: int
    successful_operations: int
    failed_operations: int

    # Timing metrics (milliseconds)
    load_times: List[float] = field(default_factory=list)
    unload_times: List[float] = field(default_factory=list)

    # Percentile metrics
    load_p50: float = 0.0
    load_p95: float = 0.0
    load_p99: float = 0.0
    unload_p50: float = 0.0
    unload_p95: float = 0.0
    unload_p99: float = 0.0

    # Resource tracking
    baseline_resources: Optional[ResourceSnapshot] = None
    final_resources: Optional[ResourceSnapshot] = None
    resource_timeline: List[ResourceSnapshot] = field(default_factory=list)

    # Leak detection
    memory_leak_detected: bool = False
    fd_leak_detected: bool = False
    thread_leak_detected: bool = False
    connection_leak_detected: bool = False

    # Detailed metrics
    operation_metrics: List[OperationMetric] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def calculate_percentiles(self):
        """Calculate percentile metrics"""
        if self.load_times:
            self.load_p50 = np.percentile(self.load_times, 50)
            self.load_p95 = np.percentile(self.load_times, 95)
            self.load_p99 = np.percentile(self.load_times, 99)

        if self.unload_times:
            self.unload_p50 = np.percentile(self.unload_times, 50)
            self.unload_p95 = np.percentile(self.unload_times, 95)
            self.unload_p99 = np.percentile(self.unload_times, 99)

    def check_resource_leaks(self, tolerance_percent: float = 2.0) -> Dict[str, bool]:
        """Check for resource leaks"""
        if not self.baseline_resources or not self.final_resources:
            return {}

        baseline = self.baseline_resources
        final = self.final_resources

        # Calculate deltas with tolerance
        def check_leak(baseline_val: int, final_val: int) -> bool:
            if baseline_val <= 0:
                return False
            delta_percent = abs((final_val - baseline_val) / baseline_val * 100)
            return delta_percent > tolerance_percent

        self.memory_leak_detected = check_leak(baseline.memory_rss, final.memory_rss)
        self.fd_leak_detected = check_leak(baseline.num_fds, final.num_fds) if baseline.num_fds > 0 else False
        self.thread_leak_detected = check_leak(baseline.num_threads, final.num_threads)
        self.connection_leak_detected = check_leak(baseline.num_connections, final.num_connections) if baseline.num_connections >= 0 else False

        return {
            "memory": self.memory_leak_detected,
            "file_descriptors": self.fd_leak_detected,
            "threads": self.thread_leak_detected,
            "connections": self.connection_leak_detected
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert results to dictionary for JSON serialization"""
        return {
            "summary": {
                "start_time": self.start_time.isoformat(),
                "end_time": self.end_time.isoformat(),
                "duration_seconds": (self.end_time - self.start_time).total_seconds(),
                "total_operations": self.total_operations,
                "successful_operations": self.successful_operations,
                "failed_operations": self.failed_operations,
                "success_rate": self.successful_operations / self.total_operations if self.total_operations > 0 else 0
            },
            "performance": {
                "load": {
                    "p50_ms": self.load_p50,
                    "p95_ms": self.load_p95,
                    "p99_ms": self.load_p99,
                    "min_ms": min(self.load_times) if self.load_times else 0,
                    "max_ms": max(self.load_times) if self.load_times else 0,
                    "mean_ms": np.mean(self.load_times) if self.load_times else 0,
                    "std_ms": np.std(self.load_times) if self.load_times else 0
                },
                "unload": {
                    "p50_ms": self.unload_p50,
                    "p95_ms": self.unload_p95,
                    "p99_ms": self.unload_p99,
                    "min_ms": min(self.unload_times) if self.unload_times else 0,
                    "max_ms": max(self.unload_times) if self.unload_times else 0,
                    "mean_ms": np.mean(self.unload_times) if self.unload_times else 0,
                    "std_ms": np.std(self.unload_times) if self.unload_times else 0
                }
            },
            "resources": {
                "baseline": asdict(self.baseline_resources) if self.baseline_resources else None,
                "final": asdict(self.final_resources) if self.final_resources else None,
                "leaks_detected": {
                    "memory": self.memory_leak_detected,
                    "file_descriptors": self.fd_leak_detected,
                    "threads": self.thread_leak_detected,
                    "connections": self.connection_leak_detected
                }
            },
            "config": asdict(self.config) if isinstance(self.config, StressTestConfig) else self.config,
            "errors": self.errors[:10] if self.errors else []  # Limit error list
        }


# ===== Plugin Worker Implementation =====

class PluginWorker:
    """Worker for plugin operations"""

    def __init__(self, worker_id: int, config: StressTestConfig):
        self.worker_id = worker_id
        self.config = config
        self.loader = None
        self.config_manager = None
        self.metrics: List[OperationMetric] = []
        self.process = psutil.Process()

    async def initialize(self):
        """Initialize plugin loader"""
        self.loader = PluginLoader()
        self.config_manager = PluginConfigManager()

    async def load_plugin(self, plugin_path: Path) -> OperationMetric:
        """Load a single plugin with metrics"""
        plugin_name = plugin_path.stem if plugin_path.is_file() else plugin_path.name

        # Capture pre-operation resources
        resource_before = ResourceSnapshot.capture(self.process)

        start_time = time.perf_counter()
        success = False
        error = None

        try:
            # Load configuration
            config = self.config_manager.load_config(plugin_name)

            # Load plugin
            success = await self.loader.load_plugin(plugin_path, config)

            if self.config.load_delay_ms > 0:
                await asyncio.sleep(self.config.load_delay_ms / 1000.0)

        except Exception as e:
            error = str(e)
            logger.error(f"Worker {self.worker_id}: Failed to load {plugin_name}: {e}")

        end_time = time.perf_counter()
        duration_ms = (end_time - start_time) * 1000

        # Capture post-operation resources
        resource_after = ResourceSnapshot.capture(self.process)

        metric = OperationMetric(
            operation=OperationType.LOAD,
            plugin_name=plugin_name,
            worker_id=self.worker_id,
            start_time=start_time,
            end_time=end_time,
            duration_ms=duration_ms,
            success=success,
            error=error,
            memory_before=resource_before.memory_rss,
            memory_after=resource_after.memory_rss,
            thread_count=resource_after.num_threads,
            fd_count=resource_after.num_fds
        )

        self.metrics.append(metric)
        return metric

    async def unload_plugin(self, plugin_name: str) -> OperationMetric:
        """Unload a single plugin with metrics"""
        # Capture pre-operation resources
        resource_before = ResourceSnapshot.capture(self.process)

        start_time = time.perf_counter()
        success = False
        error = None

        try:
            success = await self.loader.unload_plugin(plugin_name)

            if self.config.unload_delay_ms > 0:
                await asyncio.sleep(self.config.unload_delay_ms / 1000.0)

        except Exception as e:
            error = str(e)
            logger.error(f"Worker {self.worker_id}: Failed to unload {plugin_name}: {e}")

        end_time = time.perf_counter()
        duration_ms = (end_time - start_time) * 1000

        # Capture post-operation resources
        resource_after = ResourceSnapshot.capture(self.process)

        metric = OperationMetric(
            operation=OperationType.UNLOAD,
            plugin_name=plugin_name,
            worker_id=self.worker_id,
            start_time=start_time,
            end_time=end_time,
            duration_ms=duration_ms,
            success=success,
            error=error,
            memory_before=resource_before.memory_rss,
            memory_after=resource_after.memory_rss,
            thread_count=resource_after.num_threads,
            fd_count=resource_after.num_fds
        )

        self.metrics.append(metric)
        return metric

    async def execute_round(self, round_num: int, plugins: List[Path]) -> List[OperationMetric]:
        """Execute one round of load/unload operations"""
        round_metrics = []
        loaded_plugins = []

        logger.info(f"Worker {self.worker_id}: Starting round {round_num} with {len(plugins)} plugins")

        # Load phase
        for plugin_path in plugins:
            metric = await self.load_plugin(plugin_path)
            round_metrics.append(metric)
            if metric.success:
                plugin_name = plugin_path.stem if plugin_path.is_file() else plugin_path.name
                loaded_plugins.append(plugin_name)

        # Brief pause between load and unload
        await asyncio.sleep(0.1)

        # Unload phase (in reverse order)
        for plugin_name in reversed(loaded_plugins):
            metric = await self.unload_plugin(plugin_name)
            round_metrics.append(metric)

        return round_metrics


# ===== Stress Test Runner =====

class PluginStressTest:
    """Main stress test orchestrator"""

    def __init__(self, config: StressTestConfig):
        self.config = config
        self.results = StressTestResults(
            config=config,
            start_time=datetime.now(),
            end_time=datetime.now(),
            total_operations=0,
            successful_operations=0,
            failed_operations=0
        )
        self.process = psutil.Process()

    def discover_plugins(self) -> List[Path]:
        """Discover available plugins"""
        plugin_dir = Path("/Users/sheldonzhao/programs/personal-manager/src/pm/plugins/examples")
        plugins = []

        if plugin_dir.exists():
            for plugin_file in plugin_dir.glob("*.py"):
                if plugin_file.name != "__init__.py":
                    plugins.append(plugin_file)

        logger.info(f"Discovered {len(plugins)} plugins: {[p.name for p in plugins]}")
        return plugins

    def capture_baseline(self, samples: int = 5) -> ResourceSnapshot:
        """Capture baseline resource usage"""
        logger.info("Capturing baseline resource usage...")

        # Force garbage collection
        gc.collect()

        # Take multiple samples and average
        snapshots = []
        for i in range(samples):
            snapshot = ResourceSnapshot.capture(self.process)
            snapshots.append(snapshot)
            time.sleep(0.5)

        # Return the median snapshot (by memory)
        snapshots.sort(key=lambda x: x.memory_rss)
        baseline = snapshots[len(snapshots) // 2]

        logger.info(f"Baseline: Memory={baseline.memory_rss / 1024 / 1024:.2f}MB, "
                   f"Threads={baseline.num_threads}, FDs={baseline.num_fds}")

        return baseline

    async def run_threaded_test(self, plugins: List[Path]) -> List[OperationMetric]:
        """Run test using threading"""
        all_metrics = []

        with ThreadPoolExecutor(max_workers=self.config.concurrent_workers) as executor:
            for round_num in range(1, self.config.rounds + 1):
                logger.info(f"\n{'='*60}")
                logger.info(f"Round {round_num}/{self.config.rounds} - Threading Mode")
                logger.info(f"{'='*60}")

                # Create async tasks for each worker
                tasks = []
                for worker_id in range(self.config.concurrent_workers):
                    # Select plugins for this worker
                    worker_plugins = plugins[:min(self.config.max_plugins_per_worker, len(plugins))]

                    # Create worker and run round
                    worker = PluginWorker(worker_id, self.config)
                    await worker.initialize()

                    task = asyncio.create_task(
                        worker.execute_round(round_num, worker_plugins)
                    )
                    tasks.append(task)

                # Wait for all workers to complete
                round_results = await asyncio.gather(*tasks)

                # Collect metrics
                for worker_metrics in round_results:
                    all_metrics.extend(worker_metrics)

                # Capture resource snapshot
                snapshot = ResourceSnapshot.capture(self.process)
                self.results.resource_timeline.append(snapshot)

                logger.info(f"Round {round_num} complete: "
                           f"Memory={snapshot.memory_rss / 1024 / 1024:.2f}MB, "
                           f"Threads={snapshot.num_threads}")

                # Inter-round delay
                if round_num < self.config.rounds:
                    await asyncio.sleep(self.config.round_delay_s)

        return all_metrics

    def run_multiprocess_test(self, plugins: List[Path]) -> List[OperationMetric]:
        """Run test using multiprocessing"""
        all_metrics = []

        def worker_process(worker_id: int, round_num: int, plugin_paths: List[str],
                          result_queue: mp.Queue):
            """Worker process function"""
            try:
                # Run async code in process
                async def process_round():
                    worker = PluginWorker(worker_id, self.config)
                    await worker.initialize()
                    plugins = [Path(p) for p in plugin_paths]
                    return await worker.execute_round(round_num, plugins)

                metrics = asyncio.run(process_round())
                result_queue.put((worker_id, metrics))
            except Exception as e:
                logger.error(f"Process worker {worker_id} error: {e}")
                result_queue.put((worker_id, []))

        with ProcessPoolExecutor(max_workers=self.config.concurrent_workers) as executor:
            for round_num in range(1, self.config.rounds + 1):
                logger.info(f"\n{'='*60}")
                logger.info(f"Round {round_num}/{self.config.rounds} - Multiprocessing Mode")
                logger.info(f"{'='*60}")

                result_queue = mp.Queue()
                processes = []

                # Start worker processes
                for worker_id in range(self.config.concurrent_workers):
                    worker_plugins = [str(p) for p in plugins[:min(self.config.max_plugins_per_worker, len(plugins))]]

                    p = mp.Process(
                        target=worker_process,
                        args=(worker_id, round_num, worker_plugins, result_queue)
                    )
                    p.start()
                    processes.append(p)

                # Collect results
                round_metrics = []
                for _ in range(self.config.concurrent_workers):
                    worker_id, metrics = result_queue.get()
                    round_metrics.extend(metrics)

                all_metrics.extend(round_metrics)

                # Wait for processes to complete
                for p in processes:
                    p.join()

                # Capture resource snapshot
                snapshot = ResourceSnapshot.capture(self.process)
                self.results.resource_timeline.append(snapshot)

                logger.info(f"Round {round_num} complete: "
                           f"Memory={snapshot.memory_rss / 1024 / 1024:.2f}MB, "
                           f"Threads={snapshot.num_threads}")

                # Inter-round delay
                if round_num < self.config.rounds:
                    time.sleep(self.config.round_delay_s)

        return all_metrics

    async def run(self) -> StressTestResults:
        """Run the complete stress test"""
        logger.info("\n" + "="*80)
        logger.info("PLUGIN STRESS TEST - STARTING")
        logger.info("="*80)

        # Discover plugins
        plugins = self.discover_plugins()
        if not plugins:
            raise RuntimeError("No plugins found to test")

        # Capture baseline
        self.results.baseline_resources = self.capture_baseline(self.config.baseline_samples)

        # Run test based on concurrency model
        if self.config.use_multiprocessing:
            metrics = self.run_multiprocess_test(plugins)
        else:
            metrics = await self.run_threaded_test(plugins)

        # Process metrics
        for metric in metrics:
            self.results.operation_metrics.append(metric)
            self.results.total_operations += 1

            if metric.success:
                self.results.successful_operations += 1
            else:
                self.results.failed_operations += 1
                if metric.error:
                    self.results.errors.append(metric.error)

            # Collect timing data
            if metric.operation == OperationType.LOAD:
                self.results.load_times.append(metric.duration_ms)
            elif metric.operation == OperationType.UNLOAD:
                self.results.unload_times.append(metric.duration_ms)

        # Force final garbage collection
        gc.collect()
        time.sleep(1)

        # Capture final resources
        self.results.final_resources = ResourceSnapshot.capture(self.process)

        # Calculate statistics
        self.results.end_time = datetime.now()
        self.results.calculate_percentiles()

        # Check for resource leaks
        leaks = self.results.check_resource_leaks(self.config.leak_tolerance_percent)

        # Print results
        self.print_results()

        # Save results if configured
        if self.config.save_detailed_metrics:
            self.save_results()

        return self.results

    def print_results(self):
        """Print test results to console"""
        logger.info("\n" + "="*80)
        logger.info("STRESS TEST RESULTS")
        logger.info("="*80)

        # Summary
        duration = (self.results.end_time - self.results.start_time).total_seconds()
        logger.info(f"\nTest Duration: {duration:.2f} seconds")
        logger.info(f"Total Operations: {self.results.total_operations}")
        logger.info(f"Successful: {self.results.successful_operations}")
        logger.info(f"Failed: {self.results.failed_operations}")
        logger.info(f"Success Rate: {self.results.successful_operations / self.results.total_operations * 100:.2f}%")

        # Performance metrics
        logger.info("\n" + "-"*40)
        logger.info("PERFORMANCE METRICS")
        logger.info("-"*40)

        logger.info("\nLoad Operations:")
        if self.results.load_times:
            logger.info(f"  P50: {self.results.load_p50:.2f}ms")
            logger.info(f"  P95: {self.results.load_p95:.2f}ms")
            logger.info(f"  P99: {self.results.load_p99:.2f}ms")
            logger.info(f"  Min: {min(self.results.load_times):.2f}ms")
            logger.info(f"  Max: {max(self.results.load_times):.2f}ms")
            logger.info(f"  Mean: {np.mean(self.results.load_times):.2f}ms")

        logger.info("\nUnload Operations:")
        if self.results.unload_times:
            logger.info(f"  P50: {self.results.unload_p50:.2f}ms")
            logger.info(f"  P95: {self.results.unload_p95:.2f}ms")
            logger.info(f"  P99: {self.results.unload_p99:.2f}ms")
            logger.info(f"  Min: {min(self.results.unload_times):.2f}ms")
            logger.info(f"  Max: {max(self.results.unload_times):.2f}ms")
            logger.info(f"  Mean: {np.mean(self.results.unload_times):.2f}ms")

        # Resource usage
        logger.info("\n" + "-"*40)
        logger.info("RESOURCE USAGE")
        logger.info("-"*40)

        if self.results.baseline_resources and self.results.final_resources:
            baseline = self.results.baseline_resources
            final = self.results.final_resources

            logger.info("\nMemory:")
            logger.info(f"  Baseline: {baseline.memory_rss / 1024 / 1024:.2f}MB")
            logger.info(f"  Final: {final.memory_rss / 1024 / 1024:.2f}MB")
            logger.info(f"  Delta: {(final.memory_rss - baseline.memory_rss) / 1024 / 1024:.2f}MB")
            logger.info(f"  Change: {(final.memory_rss - baseline.memory_rss) / baseline.memory_rss * 100:.2f}%")

            logger.info("\nThreads:")
            logger.info(f"  Baseline: {baseline.num_threads}")
            logger.info(f"  Final: {final.num_threads}")
            logger.info(f"  Delta: {final.num_threads - baseline.num_threads}")

            if baseline.num_fds >= 0:
                logger.info("\nFile Descriptors:")
                logger.info(f"  Baseline: {baseline.num_fds}")
                logger.info(f"  Final: {final.num_fds}")
                logger.info(f"  Delta: {final.num_fds - baseline.num_fds}")

            if baseline.num_connections >= 0:
                logger.info("\nNetwork Connections:")
                logger.info(f"  Baseline: {baseline.num_connections}")
                logger.info(f"  Final: {final.num_connections}")
                logger.info(f"  Delta: {final.num_connections - baseline.num_connections}")

        # Leak detection
        logger.info("\n" + "-"*40)
        logger.info("LEAK DETECTION")
        logger.info("-"*40)

        logger.info(f"\nMemory Leak: {'DETECTED' if self.results.memory_leak_detected else 'PASS'}")
        logger.info(f"Thread Leak: {'DETECTED' if self.results.thread_leak_detected else 'PASS'}")
        logger.info(f"FD Leak: {'DETECTED' if self.results.fd_leak_detected else 'PASS'}")
        logger.info(f"Connection Leak: {'DETECTED' if self.results.connection_leak_detected else 'PASS'}")

        # Performance targets
        logger.info("\n" + "-"*40)
        logger.info("PERFORMANCE TARGETS")
        logger.info("-"*40)

        p95_pass = self.results.load_p95 <= self.config.target_p95_ms
        p99_pass = self.results.load_p99 <= self.config.target_p99_ms

        logger.info(f"\nP95 Target ({self.config.target_p95_ms}ms): {'PASS' if p95_pass else 'FAIL'}")
        logger.info(f"P99 Target ({self.config.target_p99_ms}ms): {'PASS' if p99_pass else 'FAIL'}")

        # Overall status
        logger.info("\n" + "="*80)
        all_pass = (
            not self.results.memory_leak_detected and
            not self.results.thread_leak_detected and
            not self.results.fd_leak_detected and
            not self.results.connection_leak_detected and
            p95_pass and p99_pass and
            self.results.failed_operations == 0
        )

        if all_pass:
            logger.info("OVERALL RESULT: PASS ✓")
        else:
            logger.info("OVERALL RESULT: FAIL ✗")
        logger.info("="*80)

    def save_results(self):
        """Save detailed results to files"""
        self.config.output_dir.mkdir(parents=True, exist_ok=True)

        # Save summary
        summary_file = self.config.output_dir / f"stress_test_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_file, 'w') as f:
            json.dump(self.results.to_dict(), f, indent=2, default=str)
        logger.info(f"\nResults saved to: {summary_file}")

        # Save detailed metrics if configured
        if self.config.save_detailed_metrics and self.results.operation_metrics:
            metrics_file = self.config.output_dir / f"detailed_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
            with open(metrics_file, 'w') as f:
                for metric in self.results.operation_metrics:
                    f.write(json.dumps(asdict(metric), default=str) + '\n')
            logger.info(f"Detailed metrics saved to: {metrics_file}")

        # Save resource timeline if configured
        if self.config.save_resource_timeline and self.results.resource_timeline:
            timeline_file = self.config.output_dir / f"resource_timeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
            with open(timeline_file, 'w') as f:
                for snapshot in self.results.resource_timeline:
                    f.write(json.dumps(asdict(snapshot), default=str) + '\n')
            logger.info(f"Resource timeline saved to: {timeline_file}")


# ===== Main Entry Point =====

async def main():
    """Main entry point for stress test"""

    # Create test configuration
    config = StressTestConfig(
        rounds=10,
        concurrent_workers=4,
        use_multiprocessing=False,  # Use threading by default
        max_plugins_per_worker=2,
        load_delay_ms=10,
        unload_delay_ms=5,
        round_delay_s=1.0,
        track_memory=True,
        track_file_handles=True,
        track_threads=True,
        track_network=True,
        baseline_samples=5,
        leak_tolerance_percent=2.0,
        max_load_time_ms=500.0,
        max_unload_time_ms=200.0,
        target_p95_ms=300.0,
        target_p99_ms=500.0,
        save_detailed_metrics=True,
        save_resource_timeline=True
    )

    # Override with command line arguments if provided
    if len(sys.argv) > 1:
        import argparse
        parser = argparse.ArgumentParser(description="Plugin System Stress Test")
        parser.add_argument("--rounds", type=int, default=10, help="Number of test rounds")
        parser.add_argument("--workers", type=int, default=4, help="Number of concurrent workers")
        parser.add_argument("--multiprocess", action="store_true", help="Use multiprocessing instead of threading")
        parser.add_argument("--p95-target", type=float, default=300.0, help="P95 latency target (ms)")
        parser.add_argument("--p99-target", type=float, default=500.0, help="P99 latency target (ms)")
        parser.add_argument("--leak-tolerance", type=float, default=2.0, help="Resource leak tolerance (%)")

        args = parser.parse_args()

        config.rounds = args.rounds
        config.concurrent_workers = args.workers
        config.use_multiprocessing = args.multiprocess
        config.target_p95_ms = args.p95_target
        config.target_p99_ms = args.p99_target
        config.leak_tolerance_percent = args.leak_tolerance

    # Run stress test
    stress_test = PluginStressTest(config)
    results = await stress_test.run()

    # Exit with appropriate code
    if (results.failed_operations > 0 or
        results.memory_leak_detected or
        results.thread_leak_detected or
        results.fd_leak_detected or
        results.load_p95 > config.target_p95_ms or
        results.load_p99 > config.target_p99_ms):
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    # Set up signal handling for clean shutdown
    def signal_handler(sig, frame):
        logger.info("\nReceived interrupt signal, shutting down...")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    # Run the test
    asyncio.run(main())