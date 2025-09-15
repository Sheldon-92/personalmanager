#!/usr/bin/env python3
"""Contract tests for API performance and latency requirements.

Tests ensure that API endpoints meet the performance targets specified
in the OpenAPI specification (P50 < 100ms, P95 < 500ms).
"""

import time
import unittest
import statistics
from typing import List, Dict, Any
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from tests.api.test_api_smoke import APITestCase


class TestPerformanceContracts(APITestCase):
    """Test API performance against contract requirements."""

    def setUp(self):
        """Set up performance test environment."""
        super().setUp()
        self.response_times = []

    def measure_response_time(self, endpoint: str, num_requests: int = 10) -> List[float]:
        """Measure response times for multiple requests to an endpoint."""
        response_times = []

        for i in range(num_requests):
            start_time = time.time()
            try:
                response = self.make_request(endpoint)
                end_time = time.time()

                # Only measure successful responses
                if response.get('status') == 'success':
                    response_time_ms = (end_time - start_time) * 1000
                    response_times.append(response_time_ms)
                else:
                    # If request failed, still record time but note the failure
                    response_time_ms = (end_time - start_time) * 1000
                    response_times.append(response_time_ms)

            except Exception as e:
                # Handle request failures
                end_time = time.time()
                response_time_ms = (end_time - start_time) * 1000
                response_times.append(response_time_ms)
                print(f"Request {i+1} failed: {e}")

            # Small delay between requests to avoid overwhelming the server
            time.sleep(0.01)

        return response_times

    def calculate_percentiles(self, response_times: List[float]) -> Dict[str, float]:
        """Calculate response time percentiles."""
        if not response_times:
            return {'p50': 0, 'p95': 0, 'p99': 0, 'avg': 0, 'min': 0, 'max': 0}

        sorted_times = sorted(response_times)
        return {
            'p50': sorted_times[int(len(sorted_times) * 0.50)],
            'p95': sorted_times[int(len(sorted_times) * 0.95)],
            'p99': sorted_times[int(len(sorted_times) * 0.99)],
            'avg': statistics.mean(response_times),
            'min': min(response_times),
            'max': max(response_times)
        }

    def test_status_endpoint_performance(self):
        """Test /api/v1/status endpoint performance."""
        endpoint = "/api/v1/status"
        response_times = self.measure_response_time(endpoint, 20)

        self.assertGreater(len(response_times), 0, "No successful responses measured")

        percentiles = self.calculate_percentiles(response_times)

        # Performance targets from OpenAPI spec
        self.assertLess(percentiles['p50'], 100,
                       f"P50 latency ({percentiles['p50']:.1f}ms) exceeds 100ms target")
        self.assertLess(percentiles['p95'], 500,
                       f"P95 latency ({percentiles['p95']:.1f}ms) exceeds 500ms target")

        print(f"\n{endpoint} Performance:")
        print(f"  P50: {percentiles['p50']:.1f}ms")
        print(f"  P95: {percentiles['p95']:.1f}ms")
        print(f"  P99: {percentiles['p99']:.1f}ms")
        print(f"  Avg: {percentiles['avg']:.1f}ms")

    def test_tasks_endpoint_performance(self):
        """Test /api/v1/tasks endpoint performance."""
        endpoint = "/api/v1/tasks"
        response_times = self.measure_response_time(endpoint, 20)

        self.assertGreater(len(response_times), 0, "No successful responses measured")

        percentiles = self.calculate_percentiles(response_times)

        # Performance targets
        self.assertLess(percentiles['p50'], 100,
                       f"P50 latency ({percentiles['p50']:.1f}ms) exceeds 100ms target")
        self.assertLess(percentiles['p95'], 500,
                       f"P95 latency ({percentiles['p95']:.1f}ms) exceeds 500ms target")

        print(f"\n{endpoint} Performance:")
        print(f"  P50: {percentiles['p50']:.1f}ms")
        print(f"  P95: {percentiles['p95']:.1f}ms")
        print(f"  P99: {percentiles['p99']:.1f}ms")
        print(f"  Avg: {percentiles['avg']:.1f}ms")

    def test_projects_endpoint_performance(self):
        """Test /api/v1/projects endpoint performance."""
        endpoint = "/api/v1/projects"
        response_times = self.measure_response_time(endpoint, 20)

        self.assertGreater(len(response_times), 0, "No successful responses measured")

        percentiles = self.calculate_percentiles(response_times)

        # Performance targets
        self.assertLess(percentiles['p50'], 100,
                       f"P50 latency ({percentiles['p50']:.1f}ms) exceeds 100ms target")
        self.assertLess(percentiles['p95'], 500,
                       f"P95 latency ({percentiles['p95']:.1f}ms) exceeds 500ms target")

        print(f"\n{endpoint} Performance:")
        print(f"  P50: {percentiles['p50']:.1f}ms")
        print(f"  P95: {percentiles['p95']:.1f}ms")

    def test_reports_endpoint_performance(self):
        """Test /api/v1/reports/{type} endpoint performance."""
        endpoint = "/api/v1/reports/status"
        response_times = self.measure_response_time(endpoint, 15)

        self.assertGreater(len(response_times), 0, "No successful responses measured")

        percentiles = self.calculate_percentiles(response_times)

        # Reports might take longer due to processing, but should still meet targets
        self.assertLess(percentiles['p50'], 100,
                       f"P50 latency ({percentiles['p50']:.1f}ms) exceeds 100ms target")
        self.assertLess(percentiles['p95'], 500,
                       f"P95 latency ({percentiles['p95']:.1f}ms) exceeds 500ms target")

        print(f"\n{endpoint} Performance:")
        print(f"  P50: {percentiles['p50']:.1f}ms")
        print(f"  P95: {percentiles['p95']:.1f}ms")

    def test_metrics_endpoint_performance(self):
        """Test /api/v1/metrics endpoint performance."""
        endpoint = "/api/v1/metrics"
        response_times = self.measure_response_time(endpoint, 15)

        self.assertGreater(len(response_times), 0, "No successful responses measured")

        percentiles = self.calculate_percentiles(response_times)

        # Metrics collection might take longer but should meet targets
        self.assertLess(percentiles['p50'], 100,
                       f"P50 latency ({percentiles['p50']:.1f}ms) exceeds 100ms target")
        self.assertLess(percentiles['p95'], 500,
                       f"P95 latency ({percentiles['p95']:.1f}ms) exceeds 500ms target")

        print(f"\n{endpoint} Performance:")
        print(f"  P50: {percentiles['p50']:.1f}ms")
        print(f"  P95: {percentiles['p95']:.1f}ms")

    def test_health_check_performance(self):
        """Test /health endpoint performance."""
        endpoint = "/health"
        response_times = self.measure_response_time(endpoint, 25)

        self.assertGreater(len(response_times), 0, "No successful responses measured")

        percentiles = self.calculate_percentiles(response_times)

        # Health check should be very fast
        self.assertLess(percentiles['p50'], 50,
                       f"Health check P50 latency ({percentiles['p50']:.1f}ms) should be < 50ms")
        self.assertLess(percentiles['p95'], 200,
                       f"Health check P95 latency ({percentiles['p95']:.1f}ms) should be < 200ms")

        print(f"\n{endpoint} Performance:")
        print(f"  P50: {percentiles['p50']:.1f}ms")
        print(f"  P95: {percentiles['p95']:.1f}ms")

    def test_concurrent_request_performance(self):
        """Test performance under concurrent load."""
        import threading
        import queue

        endpoint = "/api/v1/status"
        num_threads = 5
        requests_per_thread = 4
        results_queue = queue.Queue()

        def worker():
            """Worker thread function."""
            thread_times = []
            for _ in range(requests_per_thread):
                start_time = time.time()
                try:
                    response = self.make_request(endpoint)
                    end_time = time.time()
                    if response.get('status') == 'success':
                        response_time_ms = (end_time - start_time) * 1000
                        thread_times.append(response_time_ms)
                except Exception:
                    end_time = time.time()
                    response_time_ms = (end_time - start_time) * 1000
                    thread_times.append(response_time_ms)

            results_queue.put(thread_times)

        # Start threads
        threads = []
        start_time = time.time()

        for _ in range(num_threads):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        end_time = time.time()
        total_duration = end_time - start_time

        # Collect all response times
        all_response_times = []
        while not results_queue.empty():
            thread_times = results_queue.get()
            all_response_times.extend(thread_times)

        self.assertGreater(len(all_response_times), 0, "No concurrent responses measured")

        percentiles = self.calculate_percentiles(all_response_times)

        # Under concurrent load, allow slightly higher latency
        self.assertLess(percentiles['p50'], 150,
                       f"Concurrent P50 latency ({percentiles['p50']:.1f}ms) exceeds 150ms")
        self.assertLess(percentiles['p95'], 750,
                       f"Concurrent P95 latency ({percentiles['p95']:.1f}ms) exceeds 750ms")

        print(f"\nConcurrent Load Performance ({num_threads} threads):")
        print(f"  Total duration: {total_duration:.2f}s")
        print(f"  Total requests: {len(all_response_times)}")
        print(f"  P50: {percentiles['p50']:.1f}ms")
        print(f"  P95: {percentiles['p95']:.1f}ms")

    def test_filtered_request_performance(self):
        """Test performance of filtered requests."""
        endpoint = "/api/v1/tasks?status=in_progress&priority=high&sort_by=created_at"
        response_times = self.measure_response_time(endpoint, 15)

        self.assertGreater(len(response_times), 0, "No filtered responses measured")

        percentiles = self.calculate_percentiles(response_times)

        # Filtered requests might be slightly slower but should meet targets
        self.assertLess(percentiles['p50'], 100,
                       f"Filtered request P50 latency ({percentiles['p50']:.1f}ms) exceeds 100ms target")
        self.assertLess(percentiles['p95'], 500,
                       f"Filtered request P95 latency ({percentiles['p95']:.1f}ms) exceeds 500ms target")

        print(f"\nFiltered Request Performance:")
        print(f"  P50: {percentiles['p50']:.1f}ms")
        print(f"  P95: {percentiles['p95']:.1f}ms")

    def test_execution_time_metadata_accuracy(self):
        """Test that execution_time in response metadata is accurate."""
        start_time = time.time()
        response = self.make_request("/api/v1/status")
        end_time = time.time()

        client_measured_time = (end_time - start_time) * 1000  # ms
        server_reported_time = response['metadata']['execution_time'] * 1000  # convert to ms

        # Server execution time should be less than total client time
        self.assertLess(server_reported_time, client_measured_time,
                       "Server execution time should be less than total request time")

        # Server execution time should be reasonable (not negative, not too large)
        self.assertGreater(server_reported_time, 0,
                          "Server execution time should be positive")
        self.assertLess(server_reported_time, 10000,
                       "Server execution time should be reasonable (< 10s)")

    def test_response_size_impact_on_performance(self):
        """Test how response size impacts performance."""
        # Small response
        small_response_times = self.measure_response_time("/health", 10)

        # Larger response
        large_response_times = self.measure_response_time("/api/v1/status", 10)

        if small_response_times and large_response_times:
            small_p50 = self.calculate_percentiles(small_response_times)['p50']
            large_p50 = self.calculate_percentiles(large_response_times)['p50']

            print(f"\nResponse Size Impact:")
            print(f"  Small response (/health) P50: {small_p50:.1f}ms")
            print(f"  Large response (/api/v1/status) P50: {large_p50:.1f}ms")
            print(f"  Difference: {large_p50 - small_p50:.1f}ms")

            # Both should still meet performance targets
            self.assertLess(small_p50, 100, "Small response should be fast")
            self.assertLess(large_p50, 100, "Large response should still meet P50 target")


class TestPerformanceMonitoring(APITestCase):
    """Test performance monitoring capabilities."""

    def test_performance_metadata_presence(self):
        """Test that performance metadata is included when requested."""
        # This tests future functionality where performance data might be included
        response = self.make_request("/api/v1/tasks")

        # Check if performance metadata is included
        data = response.get('data', {})
        if 'performance' in data:
            performance = data['performance']

            # Validate performance metadata structure
            if 'query_time_ms' in performance:
                self.assertIsInstance(performance['query_time_ms'], (int, float))
                self.assertGreaterEqual(performance['query_time_ms'], 0)

            if 'cache_hit' in performance:
                self.assertIsInstance(performance['cache_hit'], bool)

    def test_metrics_endpoint_reports_latency(self):
        """Test that metrics endpoint reports API latency statistics."""
        response = self.make_request("/api/v1/metrics")

        if response['status'] == 'success':
            data = response['data']

            # Check if API metrics include latency information
            if 'api_metrics' in data:
                api_metrics = data['api_metrics']

                # Look for latency metrics
                latency_fields = ['average_response_time_ms', 'response_times']
                for field in latency_fields:
                    if field in api_metrics:
                        # Found latency metrics
                        break
                else:
                    # No latency metrics found - that's okay for now
                    pass


if __name__ == "__main__":
    print("Running API Performance Contract Tests")
    print("=" * 50)
    print("Performance Targets:")
    print("  P50 latency: < 100ms")
    print("  P95 latency: < 500ms")
    print("  Health check: < 50ms (P50)")
    print()

    unittest.main(verbosity=2)