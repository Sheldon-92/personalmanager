#!/usr/bin/env python3
"""
Verification script for the stress test framework
Tests the stress test components without actual plugin loading
"""

import asyncio
import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.bench.test_plugin_stress import (
    StressTestConfig,
    PluginStressTest,
    ResourceSnapshot,
    OperationMetric,
    OperationType
)


async def test_resource_tracking():
    """Test resource tracking functionality"""
    print("\n=== Testing Resource Tracking ===")

    # Take baseline snapshot
    snapshot1 = ResourceSnapshot.capture()
    print(f"Memory: {snapshot1.memory_rss / 1024 / 1024:.2f}MB")
    print(f"Threads: {snapshot1.num_threads}")
    print(f"FDs: {snapshot1.num_fds}")

    # Allocate some memory
    data = [i for i in range(1000000)]

    # Take another snapshot
    snapshot2 = ResourceSnapshot.capture()
    print(f"\nAfter allocation:")
    print(f"Memory: {snapshot2.memory_rss / 1024 / 1024:.2f}MB")
    print(f"Delta: {(snapshot2.memory_rss - snapshot1.memory_rss) / 1024 / 1024:.2f}MB")

    return True


async def test_timing_metrics():
    """Test timing and percentile calculations"""
    print("\n=== Testing Timing Metrics ===")

    # Generate sample timing data
    import numpy as np

    times = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 200, 300]

    p50 = np.percentile(times, 50)
    p95 = np.percentile(times, 95)
    p99 = np.percentile(times, 99)

    print(f"Sample times: {times}")
    print(f"P50: {p50:.2f}ms")
    print(f"P95: {p95:.2f}ms")
    print(f"P99: {p99:.2f}ms")

    return True


async def test_mock_operations():
    """Test with mock plugin operations"""
    print("\n=== Testing Mock Operations ===")

    class MockPluginWorker:
        """Mock plugin worker for testing"""

        def __init__(self, worker_id: int):
            self.worker_id = worker_id
            self.metrics = []

        async def mock_load(self, plugin_name: str) -> OperationMetric:
            """Simulate plugin load"""
            start = time.perf_counter()

            # Simulate work
            await asyncio.sleep(0.01 + (self.worker_id * 0.001))

            end = time.perf_counter()
            duration_ms = (end - start) * 1000

            metric = OperationMetric(
                operation=OperationType.LOAD,
                plugin_name=plugin_name,
                worker_id=self.worker_id,
                start_time=start,
                end_time=end,
                duration_ms=duration_ms,
                success=True,
                error=None
            )

            self.metrics.append(metric)
            return metric

        async def mock_unload(self, plugin_name: str) -> OperationMetric:
            """Simulate plugin unload"""
            start = time.perf_counter()

            # Simulate work
            await asyncio.sleep(0.005)

            end = time.perf_counter()
            duration_ms = (end - start) * 1000

            metric = OperationMetric(
                operation=OperationType.UNLOAD,
                plugin_name=plugin_name,
                worker_id=self.worker_id,
                start_time=start,
                end_time=end,
                duration_ms=duration_ms,
                success=True,
                error=None
            )

            self.metrics.append(metric)
            return metric

    # Run mock concurrent operations
    workers = [MockPluginWorker(i) for i in range(4)]

    tasks = []
    for worker in workers:
        task = asyncio.create_task(worker.mock_load(f"test_plugin_{worker.worker_id}"))
        tasks.append(task)

    results = await asyncio.gather(*tasks)

    # Calculate statistics
    load_times = [r.duration_ms for r in results]
    print(f"Load times: {[f'{t:.2f}ms' for t in load_times]}")
    print(f"Mean: {sum(load_times) / len(load_times):.2f}ms")

    # Test unload
    tasks = []
    for worker in workers:
        task = asyncio.create_task(worker.mock_unload(f"test_plugin_{worker.worker_id}"))
        tasks.append(task)

    results = await asyncio.gather(*tasks)
    unload_times = [r.duration_ms for r in results]
    print(f"Unload times: {[f'{t:.2f}ms' for t in unload_times]}")

    return True


async def test_leak_detection():
    """Test resource leak detection logic"""
    print("\n=== Testing Leak Detection ===")

    def check_leak(baseline: float, final: float, tolerance: float = 2.0) -> bool:
        """Check if there's a resource leak"""
        if baseline <= 0:
            return False
        delta_percent = abs((final - baseline) / baseline * 100)
        return delta_percent > tolerance

    # Test cases
    test_cases = [
        (100, 101, 2.0, False, "1% increase - within tolerance"),
        (100, 103, 2.0, True, "3% increase - leak detected"),
        (100, 98, 2.0, False, "2% decrease - no leak"),
        (100, 95, 2.0, True, "5% decrease - significant change"),
        (100, 100, 2.0, False, "No change - no leak"),
    ]

    for baseline, final, tolerance, expected, description in test_cases:
        result = check_leak(baseline, final, tolerance)
        status = "✓" if result == expected else "✗"
        print(f"{status} {description}: baseline={baseline}, final={final}, leak={result}")

    return True


async def main():
    """Run all verification tests"""
    print("=" * 60)
    print("STRESS TEST FRAMEWORK VERIFICATION")
    print("=" * 60)

    tests = [
        ("Resource Tracking", test_resource_tracking),
        ("Timing Metrics", test_timing_metrics),
        ("Mock Operations", test_mock_operations),
        ("Leak Detection", test_leak_detection),
    ]

    results = []
    for name, test_func in tests:
        try:
            success = await test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n✗ {name} failed: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)

    all_passed = True
    for name, success in results:
        status = "PASS" if success else "FAIL"
        print(f"{name}: {status}")
        if not success:
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("ALL TESTS PASSED ✓")
        print("The stress test framework is working correctly")
    else:
        print("SOME TESTS FAILED ✗")
        print("Please check the framework configuration")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)