#!/usr/bin/env python3
"""Smoke tests for PersonalManager Local API.

Tests basic functionality of all API endpoints to ensure they:
1. Return valid JSON responses
2. Follow the standardized response format
3. Return appropriate HTTP status codes
4. Handle error cases properly
"""

import json
import time
import unittest
import urllib.request
import urllib.error
from typing import Dict, Any
import threading
import subprocess
import signal
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from pm.api.server import PersonalManagerAPI


class APITestCase(unittest.TestCase):
    """Base test case for API testing with server management."""

    @classmethod
    def setUpClass(cls):
        """Start the API server for testing."""
        cls.base_url = "http://localhost:8001"
        cls.server_process = None
        cls.api_server = None

        # Start server in background thread
        cls.api_server = PersonalManagerAPI(host="localhost", port=8001)
        cls.server_thread = threading.Thread(target=cls.api_server.start, daemon=True)
        cls.server_thread.start()

        # Wait for server to start
        cls._wait_for_server()

    @classmethod
    def tearDownClass(cls):
        """Stop the API server after testing."""
        if cls.api_server and hasattr(cls.api_server, 'server') and cls.api_server.server:
            cls.api_server.server.shutdown()
            cls.api_server.server.server_close()

    @classmethod
    def _wait_for_server(cls, timeout=10):
        """Wait for server to be ready."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = urllib.request.urlopen(f"{cls.base_url}/health", timeout=1)
                if response.status == 200:
                    return True
            except (urllib.error.URLError, ConnectionRefusedError):
                time.sleep(0.1)
        raise Exception("Server failed to start within timeout")

    def make_request(self, endpoint: str, expected_status: int = 200) -> Dict[str, Any]:
        """Make a GET request to the API and return parsed JSON response."""
        url = f"{self.base_url}{endpoint}"

        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                self.assertEqual(response.status, expected_status,
                               f"Expected status {expected_status}, got {response.status} for {endpoint}")

                content = response.read().decode('utf-8')
                return json.loads(content)

        except urllib.error.HTTPError as e:
            # For error cases, still try to parse JSON response
            content = e.read().decode('utf-8')
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                self.fail(f"Invalid JSON response from {endpoint}: {content}")
        except Exception as e:
            self.fail(f"Request failed for {endpoint}: {e}")

    def assert_standard_response_format(self, response: Dict[str, Any], command_prefix: str):
        """Assert that response follows PersonalManager standard format."""
        required_fields = ['status', 'command', 'timestamp', 'data', 'error', 'metadata']

        for field in required_fields:
            self.assertIn(field, response, f"Missing required field: {field}")

        # Validate status
        self.assertIn(response['status'], ['success', 'failed', 'warning'],
                     f"Invalid status: {response['status']}")

        # Validate command
        self.assertTrue(response['command'].startswith(command_prefix),
                       f"Command '{response['command']}' should start with '{command_prefix}'")

        # Validate timestamp format (ISO-8601)
        self.assertTrue(response['timestamp'].endswith('Z'),
                       f"Timestamp should be in ISO-8601 format: {response['timestamp']}")

        # Validate metadata
        self.assertIn('version', response['metadata'])
        self.assertIn('execution_time', response['metadata'])
        self.assertEqual(response['metadata']['version'], '1.0.0')
        self.assertIsInstance(response['metadata']['execution_time'], (int, float))

        # Validate data/error exclusivity
        if response['status'] == 'success':
            self.assertIsNotNone(response['data'])
            self.assertIsNone(response['error'])
        else:
            self.assertIsNone(response['data'])
            self.assertIsNotNone(response['error'])
            self.assert_error_format(response['error'])

    def assert_error_format(self, error: Dict[str, Any]):
        """Assert that error follows standard format."""
        required_fields = ['code', 'message', 'details']

        for field in required_fields:
            self.assertIn(field, error, f"Missing error field: {field}")

        self.assertIsInstance(error['code'], str)
        self.assertIsInstance(error['message'], str)
        self.assertIsInstance(error['details'], dict)


class TestAPIInfo(APITestCase):
    """Test API information endpoints."""

    def test_root_endpoint(self):
        """Test GET / returns API information."""
        response = self.make_request("/")

        self.assertIn('name', response)
        self.assertIn('version', response)
        self.assertIn('description', response)
        self.assertIn('endpoints', response)

        self.assertEqual(response['name'], "PersonalManager API")
        self.assertEqual(response['version'], "1.0.0")

    def test_health_check(self):
        """Test GET /health endpoint."""
        response = self.make_request("/health")

        self.assertIn('status', response)
        self.assertIn('timestamp', response)
        self.assertIn('version', response)

        self.assertEqual(response['status'], "healthy")
        self.assertEqual(response['version'], "1.0.0")


class TestSystemStatus(APITestCase):
    """Test system status endpoint."""

    def test_status_endpoint(self):
        """Test GET /api/v1/status returns system status."""
        response = self.make_request("/api/v1/status")

        self.assert_standard_response_format(response, "api.status")
        self.assertEqual(response['status'], 'success')

        data = response['data']
        self.assertIn('system', data)
        self.assertIn('services', data)
        self.assertIn('endpoints', data)

        # Validate system info
        system = data['system']
        self.assertEqual(system['name'], "PersonalManager")
        self.assertEqual(system['version'], "1.0.0")
        self.assertEqual(system['status'], "running")

        # Validate services
        services = data['services']
        self.assertIn('storage', services)
        self.assertIn('ai', services)

        # Validate AI services
        ai_services = services['ai']
        self.assertIn('claude', ai_services)
        self.assertIn('gemini', ai_services)

        for service_name, service_info in ai_services.items():
            self.assertIn('configured', service_info)
            self.assertIn('status', service_info)
            self.assertIsInstance(service_info['configured'], bool)


class TestTasksEndpoint(APITestCase):
    """Test tasks endpoint."""

    def test_tasks_list(self):
        """Test GET /api/v1/tasks returns task list."""
        response = self.make_request("/api/v1/tasks")

        self.assert_standard_response_format(response, "api.tasks")
        self.assertEqual(response['status'], 'success')

        data = response['data']
        self.assertIn('tasks', data)
        self.assertIn('summary', data)
        self.assertIn('filters_applied', data)

        # Validate tasks structure
        tasks = data['tasks']
        self.assertIsInstance(tasks, list)

        if tasks:  # If we have tasks, validate structure
            task = tasks[0]
            required_fields = ['id', 'title', 'status', 'priority', 'context',
                             'created_at', 'updated_at']
            for field in required_fields:
                self.assertIn(field, task, f"Missing task field: {field}")

        # Validate summary
        summary = data['summary']
        self.assertIn('total', summary)
        self.assertIn('by_status', summary)
        self.assertIn('by_priority', summary)
        self.assertIn('by_context', summary)

    def test_tasks_with_filters(self):
        """Test GET /api/v1/tasks with filters."""
        response = self.make_request("/api/v1/tasks?status=in_progress&priority=high")

        self.assert_standard_response_format(response, "api.tasks")
        self.assertEqual(response['status'], 'success')

        data = response['data']
        filters = data['filters_applied']
        self.assertEqual(filters['status'], 'in_progress')
        self.assertEqual(filters['priority'], 'high')


class TestProjectsEndpoint(APITestCase):
    """Test projects endpoint."""

    def test_projects_list(self):
        """Test GET /api/v1/projects returns project list."""
        response = self.make_request("/api/v1/projects")

        self.assert_standard_response_format(response, "api.projects")
        self.assertEqual(response['status'], 'success')

        data = response['data']
        self.assertIn('projects', data)
        self.assertIn('summary', data)
        self.assertIn('filters_applied', data)

        # Validate projects structure
        projects = data['projects']
        self.assertIsInstance(projects, list)

        if projects:  # If we have projects, validate structure
            project = projects[0]
            required_fields = ['id', 'name', 'status', 'priority', 'health',
                             'progress', 'created_at', 'updated_at']
            for field in required_fields:
                self.assertIn(field, project, f"Missing project field: {field}")

            # Validate progress is a number between 0 and 100
            self.assertIsInstance(project['progress'], (int, float))
            self.assertGreaterEqual(project['progress'], 0)
            self.assertLessEqual(project['progress'], 100)

        # Validate summary
        summary = data['summary']
        self.assertIn('total', summary)
        self.assertIn('active', summary)
        self.assertIn('completed', summary)

    def test_projects_with_filters(self):
        """Test GET /api/v1/projects with filters."""
        response = self.make_request("/api/v1/projects?status=active")

        self.assert_standard_response_format(response, "api.projects")
        data = response['data']
        filters = data['filters_applied']
        self.assertEqual(filters['status'], 'active')


class TestReportsEndpoint(APITestCase):
    """Test reports endpoint."""

    def test_status_report(self):
        """Test GET /api/v1/reports/status."""
        response = self.make_request("/api/v1/reports/status")

        self.assert_standard_response_format(response, "api.reports")
        self.assertEqual(response['status'], 'success')

        data = response['data']
        self.assertIn('report', data)
        self.assertIn('metadata', data)

        report = data['report']
        self.assertEqual(report['report_type'], 'status')
        self.assertIn('generated_at', report)
        self.assertIn('period', report)
        self.assertIn('data', report)

    def test_progress_report(self):
        """Test GET /api/v1/reports/progress."""
        response = self.make_request("/api/v1/reports/progress")

        self.assert_standard_response_format(response, "api.reports")
        report = response['data']['report']
        self.assertEqual(report['report_type'], 'progress')

    def test_performance_report(self):
        """Test GET /api/v1/reports/performance."""
        response = self.make_request("/api/v1/reports/performance")

        self.assert_standard_response_format(response, "api.reports")
        report = response['data']['report']
        self.assertEqual(report['report_type'], 'performance')

    def test_summary_report(self):
        """Test GET /api/v1/reports/summary."""
        response = self.make_request("/api/v1/reports/summary")

        self.assert_standard_response_format(response, "api.reports")
        report = response['data']['report']
        self.assertEqual(report['report_type'], 'summary')

    def test_invalid_report_type(self):
        """Test GET /api/v1/reports/invalid returns error."""
        response = self.make_request("/api/v1/reports/invalid", expected_status=400)

        self.assert_standard_response_format(response, "api.reports")
        self.assertEqual(response['status'], 'failed')
        self.assertEqual(response['error']['code'], 'INVALID_REPORT_TYPE')


class TestMetricsEndpoint(APITestCase):
    """Test metrics endpoint."""

    def test_metrics(self):
        """Test GET /api/v1/metrics returns system metrics."""
        response = self.make_request("/api/v1/metrics")

        self.assert_standard_response_format(response, "api.metrics")
        self.assertEqual(response['status'], 'success')

        data = response['data']
        self.assertIn('system_metrics', data)
        self.assertIn('api_metrics', data)
        self.assertIn('application_metrics', data)

        # Validate system metrics
        system_metrics = data['system_metrics']
        self.assertIn('platform', system_metrics)
        self.assertIn('python_version', system_metrics)

        # Validate API metrics
        api_metrics = data['api_metrics']
        self.assertIn('uptime_seconds', api_metrics)
        self.assertIn('endpoints_available', api_metrics)
        self.assertIn('average_response_time_ms', api_metrics)

        # Validate application metrics
        app_metrics = data['application_metrics']
        self.assertIn('tasks_in_system', app_metrics)
        self.assertIn('projects_in_system', app_metrics)


class TestErrorHandling(APITestCase):
    """Test error handling."""

    def test_not_found_endpoint(self):
        """Test GET /api/v1/nonexistent returns 404."""
        response = self.make_request("/api/v1/nonexistent", expected_status=400)

        self.assert_standard_response_format(response, "api.not_found")
        self.assertEqual(response['status'], 'failed')
        self.assertEqual(response['error']['code'], 'NOT_FOUND')


class TestCORSHeaders(APITestCase):
    """Test CORS headers for browser compatibility."""

    def test_cors_headers_present(self):
        """Test that CORS headers are present in responses."""
        url = f"{self.base_url}/api/v1/status"

        try:
            request = urllib.request.Request(url)
            with urllib.request.urlopen(request) as response:
                headers = dict(response.headers)

                self.assertIn('Access-Control-Allow-Origin', headers)
                self.assertIn('Access-Control-Allow-Methods', headers)
                self.assertIn('Access-Control-Allow-Headers', headers)

                self.assertEqual(headers['Access-Control-Allow-Origin'], '*')
                self.assertIn('GET', headers['Access-Control-Allow-Methods'])

        except Exception as e:
            self.fail(f"CORS test failed: {e}")


def run_smoke_tests():
    """Run all smoke tests and return results."""
    # Create test suite
    test_classes = [
        TestAPIInfo,
        TestSystemStatus,
        TestTasksEndpoint,
        TestProjectsEndpoint,
        TestReportsEndpoint,
        TestMetricsEndpoint,
        TestErrorHandling,
        TestCORSHeaders
    ]

    suite = unittest.TestSuite()
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)

    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, buffer=True)
    result = runner.run(suite)

    return result


if __name__ == "__main__":
    print("PersonalManager API Smoke Tests")
    print("=" * 50)
    print()

    result = run_smoke_tests()

    print()
    print("=" * 50)
    print("Test Results Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")

    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")

    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")

    # Exit with appropriate code
    exit_code = 0 if result.wasSuccessful() else 1
    sys.exit(exit_code)