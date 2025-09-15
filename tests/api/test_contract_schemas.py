#!/usr/bin/env python3
"""Contract tests for API response schemas and data structure validation.

Tests ensure that API responses match the OpenAPI specification exactly,
validating field types, required fields, enum values, and data constraints.
"""

import json
import unittest
from datetime import datetime
from typing import Dict, Any, List
import jsonschema
import yaml
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from tests.api.test_api_smoke import APITestCase


class OpenAPIValidator:
    """OpenAPI schema validator for contract testing."""

    def __init__(self):
        """Load OpenAPI specification and prepare validators."""
        openapi_path = project_root / "docs" / "api" / "openapi.yaml"
        with open(openapi_path, 'r') as f:
            self.spec = yaml.safe_load(f)

        # Extract component schemas
        self.schemas = self.spec.get('components', {}).get('schemas', {})

        # Prepare resolvers for $ref resolution
        self.resolver = jsonschema.RefResolver(
            base_uri=f"file://{openapi_path}",
            referrer=self.spec
        )

    def validate_response(self, response: Dict[str, Any], endpoint: str, status_code: int) -> List[str]:
        """Validate response against OpenAPI schema."""
        errors = []

        try:
            # Get the endpoint definition
            path_item = self._find_path_item(endpoint)
            if not path_item:
                errors.append(f"Endpoint {endpoint} not found in OpenAPI spec")
                return errors

            # Get the response schema for the status code
            responses = path_item.get('get', {}).get('responses', {})
            response_def = responses.get(str(status_code))
            if not response_def:
                errors.append(f"Status code {status_code} not defined for {endpoint}")
                return errors

            # Extract schema from response definition
            content = response_def.get('content', {})
            json_content = content.get('application/json', {})
            schema = json_content.get('schema', {})

            if not schema:
                return errors

            # Validate response against schema
            try:
                jsonschema.validate(response, schema, resolver=self.resolver)
            except jsonschema.ValidationError as e:
                errors.append(f"Schema validation failed: {e.message} at {e.absolute_path}")
            except jsonschema.SchemaError as e:
                errors.append(f"Invalid schema: {e.message}")

        except Exception as e:
            errors.append(f"Validation error: {str(e)}")

        return errors

    def _find_path_item(self, endpoint: str) -> Dict[str, Any]:
        """Find path item in OpenAPI spec, handling path parameters."""
        paths = self.spec.get('paths', {})

        # Direct match
        if endpoint in paths:
            return paths[endpoint]

        # Handle parameterized paths
        for path_pattern, path_item in paths.items():
            if self._match_parameterized_path(endpoint, path_pattern):
                return path_item

        return {}

    def _match_parameterized_path(self, actual_path: str, pattern: str) -> bool:
        """Match actual path against OpenAPI path pattern with parameters."""
        import re

        # Convert OpenAPI path parameters to regex
        # e.g., /api/v1/reports/{type} -> /api/v1/reports/[^/]+
        regex_pattern = re.sub(r'\{[^}]+\}', r'[^/]+', pattern)
        regex_pattern = f"^{regex_pattern}$"

        return bool(re.match(regex_pattern, actual_path))

    def validate_api_response_structure(self, response: Dict[str, Any]) -> List[str]:
        """Validate standard API response structure."""
        errors = []
        schema = self.schemas.get('APIResponse', {})

        if not schema:
            errors.append("APIResponse schema not found in OpenAPI spec")
            return errors

        try:
            jsonschema.validate(response, schema, resolver=self.resolver)
        except jsonschema.ValidationError as e:
            errors.append(f"APIResponse validation failed: {e.message} at {e.absolute_path}")

        return errors


class TestAPIResponseContracts(APITestCase):
    """Test API responses against OpenAPI contracts."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment and OpenAPI validator."""
        super().setUpClass()
        cls.validator = OpenAPIValidator()

    def test_status_endpoint_contract(self):
        """Test /api/v1/status response contract."""
        response = self.make_request("/api/v1/status")

        # Validate standard API response structure
        errors = self.validator.validate_api_response_structure(response)
        self.assertEqual(errors, [], f"APIResponse structure validation failed: {errors}")

        # Validate endpoint-specific schema
        errors = self.validator.validate_response(response, "/api/v1/status", 200)
        self.assertEqual(errors, [], f"Status endpoint validation failed: {errors}")

        # Additional specific validations
        self.assertEqual(response['status'], 'success')
        self.assertIn('system', response['data'])
        self.assertIn('services', response['data'])
        self.assertIn('endpoints', response['data'])

        # Validate system data structure
        system = response['data']['system']
        self.assertIsInstance(system['version'], str)
        self.assertIn(system['status'], ['running', 'stopped', 'error'])
        self.assertIsInstance(system['uptime'], (int, float))

    def test_tasks_endpoint_contract(self):
        """Test /api/v1/tasks response contract."""
        response = self.make_request("/api/v1/tasks")

        # Validate API response structure
        errors = self.validator.validate_api_response_structure(response)
        self.assertEqual(errors, [], f"APIResponse structure validation failed: {errors}")

        # Validate endpoint-specific schema
        errors = self.validator.validate_response(response, "/api/v1/tasks", 200)
        self.assertEqual(errors, [], f"Tasks endpoint validation failed: {errors}")

        # Validate required data structure
        data = response['data']
        self.assertIn('tasks', data)
        self.assertIn('summary', data)
        self.assertIn('filters_applied', data)

        # Validate task objects structure
        tasks = data['tasks']
        self.assertIsInstance(tasks, list)

        if tasks:  # If tasks exist, validate first task structure
            task = tasks[0]
            required_fields = ['id', 'title', 'status', 'priority', 'context', 'created_at', 'updated_at']

            for field in required_fields:
                self.assertIn(field, task, f"Required field '{field}' missing from task")

            # Validate field types and constraints
            self.assertIsInstance(task['id'], str)
            self.assertTrue(task['id'].startswith('task-'), f"Task ID format invalid: {task['id']}")
            self.assertIsInstance(task['title'], str)
            self.assertGreater(len(task['title']), 0, "Task title cannot be empty")

            # Validate enum values
            valid_statuses = ['inbox', 'next_action', 'project', 'waiting_for', 'someday_maybe', 'reference', 'completed', 'deleted']
            self.assertIn(task['status'], valid_statuses, f"Invalid task status: {task['status']}")

            valid_priorities = ['high', 'medium', 'low']
            self.assertIn(task['priority'], valid_priorities, f"Invalid task priority: {task['priority']}")

            # Validate datetime formats
            self._validate_iso8601_datetime(task['created_at'], 'task.created_at')
            self._validate_iso8601_datetime(task['updated_at'], 'task.updated_at')

        # Validate summary structure
        summary = data['summary']
        self.assertIn('total', summary)
        self.assertIn('by_status', summary)
        self.assertIn('by_priority', summary)
        self.assertIn('by_context', summary)

        self.assertIsInstance(summary['total'], int)
        self.assertGreaterEqual(summary['total'], 0)

    def test_projects_endpoint_contract(self):
        """Test /api/v1/projects response contract."""
        response = self.make_request("/api/v1/projects")

        # Validate API response structure
        errors = self.validator.validate_api_response_structure(response)
        self.assertEqual(errors, [], f"APIResponse structure validation failed: {errors}")

        # Validate endpoint-specific schema
        errors = self.validator.validate_response(response, "/api/v1/projects", 200)
        self.assertEqual(errors, [], f"Projects endpoint validation failed: {errors}")

        # Validate data structure
        data = response['data']
        self.assertIn('projects', data)
        self.assertIn('summary', data)
        self.assertIn('filters_applied', data)

        # Validate project objects
        projects = data['projects']
        self.assertIsInstance(projects, list)

        if projects:
            project = projects[0]
            required_fields = ['id', 'name', 'status', 'priority', 'health', 'progress', 'created_at', 'updated_at']

            for field in required_fields:
                self.assertIn(field, project, f"Required field '{field}' missing from project")

            # Validate field types and constraints
            self.assertIsInstance(project['id'], str)
            self.assertTrue(project['id'].startswith('project-'), f"Project ID format invalid: {project['id']}")
            self.assertIsInstance(project['name'], str)
            self.assertGreater(len(project['name']), 0)

            # Validate enum values
            valid_statuses = ['active', 'completed', 'planning', 'on_hold', 'cancelled']
            self.assertIn(project['status'], valid_statuses, f"Invalid project status: {project['status']}")

            valid_priorities = ['high', 'medium', 'low']
            self.assertIn(project['priority'], valid_priorities, f"Invalid project priority: {project['priority']}")

            valid_health = ['excellent', 'good', 'warning', 'critical', 'unknown']
            self.assertIn(project['health'], valid_health, f"Invalid project health: {project['health']}")

            # Validate progress constraints
            self.assertIsInstance(project['progress'], (int, float))
            self.assertGreaterEqual(project['progress'], 0)
            self.assertLessEqual(project['progress'], 100)

            # Validate datetime formats
            self._validate_iso8601_datetime(project['created_at'], 'project.created_at')
            self._validate_iso8601_datetime(project['updated_at'], 'project.updated_at')

    def test_reports_endpoint_contract(self):
        """Test /api/v1/reports/{type} response contract."""
        report_types = ['status', 'progress', 'performance', 'summary']

        for report_type in report_types:
            with self.subTest(report_type=report_type):
                response = self.make_request(f"/api/v1/reports/{report_type}")

                # Validate API response structure
                errors = self.validator.validate_api_response_structure(response)
                self.assertEqual(errors, [], f"APIResponse structure validation failed: {errors}")

                # Validate endpoint-specific schema
                errors = self.validator.validate_response(response, f"/api/v1/reports/{report_type}", 200)
                self.assertEqual(errors, [], f"Reports endpoint validation failed for {report_type}: {errors}")

                # Validate report structure
                data = response['data']
                self.assertIn('report', data)
                self.assertIn('metadata', data)

                report = data['report']
                self.assertEqual(report['report_type'], report_type)
                self.assertIn('generated_at', report)
                self.assertIn('period', report)
                self.assertIn('data', report)

                # Validate datetime format
                self._validate_iso8601_datetime(report['generated_at'], f'report.{report_type}.generated_at')

    def test_metrics_endpoint_contract(self):
        """Test /api/v1/metrics response contract."""
        response = self.make_request("/api/v1/metrics")

        # Validate API response structure
        errors = self.validator.validate_api_response_structure(response)
        self.assertEqual(errors, [], f"APIResponse structure validation failed: {errors}")

        # Validate endpoint-specific schema
        errors = self.validator.validate_response(response, "/api/v1/metrics", 200)
        self.assertEqual(errors, [], f"Metrics endpoint validation failed: {errors}")

        # Validate metrics structure
        data = response['data']
        expected_sections = ['system_metrics', 'api_metrics', 'application_metrics']

        for section in expected_sections:
            if section in data:  # Some sections might be optional based on system capabilities
                self.assertIsInstance(data[section], dict, f"{section} should be a dictionary")

    def test_health_endpoint_contract(self):
        """Test /health endpoint response contract."""
        response = self.make_request("/health")

        # Health endpoint uses different response format (not standard API response)
        self.assertIn('status', response)
        self.assertIn('timestamp', response)
        self.assertIn('version', response)

        # Validate field types
        self.assertIsInstance(response['status'], str)
        self.assertIn(response['status'], ['healthy', 'degraded', 'unhealthy'])

        # Validate timestamp format
        self._validate_iso8601_datetime(response['timestamp'], 'health.timestamp')

        self.assertIsInstance(response['version'], str)
        self.assertEqual(response['version'], '1.0.0')

    def test_root_endpoint_contract(self):
        """Test / endpoint response contract."""
        response = self.make_request("/")

        # Root endpoint has its own format
        required_fields = ['name', 'version', 'description', 'endpoints']

        for field in required_fields:
            self.assertIn(field, response, f"Required field '{field}' missing from root response")

        self.assertEqual(response['name'], "PersonalManager API")
        self.assertEqual(response['version'], "1.0.0")
        self.assertIsInstance(response['endpoints'], dict)

    def test_error_response_contracts(self):
        """Test error response formats match contracts."""
        # Test 404 error for invalid report type
        response = self.make_request("/api/v1/reports/invalid", expected_status=400)

        # Validate error response structure
        errors = self.validator.validate_api_response_structure(response)
        self.assertEqual(errors, [], f"Error response structure validation failed: {errors}")

        self.assertEqual(response['status'], 'failed')
        self.assertIsNotNone(response['error'])
        self.assertIsNone(response['data'])

        # Validate error object structure
        error = response['error']
        self.assertIn('code', error)
        self.assertIn('message', error)
        self.assertIn('details', error)

        self.assertIsInstance(error['code'], str)
        self.assertIsInstance(error['message'], str)
        self.assertIsInstance(error['details'], dict)

    def _validate_iso8601_datetime(self, timestamp: str, field_name: str):
        """Validate ISO-8601 datetime format."""
        self.assertIsInstance(timestamp, str, f"{field_name} should be a string")

        try:
            # Parse ISO format datetime
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            self.assertIsInstance(dt, datetime)
        except ValueError as e:
            self.fail(f"Invalid ISO-8601 datetime format for {field_name}: {timestamp}, error: {e}")

        # Check that it ends with 'Z' for UTC
        self.assertTrue(timestamp.endswith('Z'), f"{field_name} should end with 'Z' for UTC: {timestamp}")


class TestAPIResponseMetadata(APITestCase):
    """Test API response metadata consistency."""

    def test_metadata_consistency(self):
        """Test that all API responses have consistent metadata."""
        endpoints = [
            "/api/v1/status",
            "/api/v1/tasks",
            "/api/v1/projects",
            "/api/v1/reports/status",
            "/api/v1/metrics"
        ]

        for endpoint in endpoints:
            with self.subTest(endpoint=endpoint):
                response = self.make_request(endpoint)

                # Check metadata presence and structure
                self.assertIn('metadata', response)
                metadata = response['metadata']

                self.assertIn('version', metadata)
                self.assertIn('execution_time', metadata)

                self.assertEqual(metadata['version'], '1.0.0')
                self.assertIsInstance(metadata['execution_time'], (int, float))
                self.assertGreaterEqual(metadata['execution_time'], 0)

    def test_timestamp_consistency(self):
        """Test that timestamps are consistent and recent."""
        response = self.make_request("/api/v1/status")
        timestamp_str = response['timestamp']

        # Parse timestamp
        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        now = datetime.now().astimezone()

        # Should be within last 5 seconds
        time_diff = abs((now - timestamp).total_seconds())
        self.assertLess(time_diff, 5, f"Timestamp {timestamp_str} is not recent enough")

    def test_command_naming_consistency(self):
        """Test that command names follow consistent pattern."""
        test_cases = [
            ("/api/v1/status", "api.status"),
            ("/api/v1/tasks", "api.tasks"),
            ("/api/v1/projects", "api.projects"),
            ("/api/v1/reports/status", "api.reports"),
            ("/api/v1/metrics", "api.metrics")
        ]

        for endpoint, expected_command in test_cases:
            with self.subTest(endpoint=endpoint):
                response = self.make_request(endpoint)
                self.assertEqual(response['command'], expected_command)


if __name__ == "__main__":
    # Run contract tests
    unittest.main(verbosity=2)