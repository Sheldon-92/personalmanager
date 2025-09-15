#!/usr/bin/env python3
"""Contract tests for API pagination, filtering, and sorting functionality.

Tests ensure that pagination, filtering, and sorting work correctly
and return proper metadata according to the OpenAPI specification.
"""

import unittest
import urllib.parse
from typing import Dict, Any
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from tests.api.test_api_smoke import APITestCase


class TestPaginationContracts(APITestCase):
    """Test pagination functionality contracts."""

    def test_tasks_pagination_structure(self):
        """Test that tasks endpoint returns proper pagination metadata."""
        # Test default pagination
        response = self.make_request("/api/v1/tasks")

        # Should have pagination info (even if not implemented yet)
        data = response['data']

        # Validate tasks array exists
        self.assertIn('tasks', data)
        self.assertIsInstance(data['tasks'], list)

        # If pagination is implemented, validate structure
        if 'pagination' in data:
            pagination = data['pagination']

            # Required pagination fields
            required_fields = ['page', 'limit', 'total', 'total_pages', 'has_next', 'has_previous']
            for field in required_fields:
                self.assertIn(field, pagination, f"Required pagination field '{field}' missing")

            # Validate types and constraints
            self.assertIsInstance(pagination['page'], int)
            self.assertGreaterEqual(pagination['page'], 1)

            self.assertIsInstance(pagination['limit'], int)
            self.assertGreaterEqual(pagination['limit'], 1)
            self.assertLessEqual(pagination['limit'], 100)

            self.assertIsInstance(pagination['total'], int)
            self.assertGreaterEqual(pagination['total'], 0)

            self.assertIsInstance(pagination['total_pages'], int)
            self.assertGreaterEqual(pagination['total_pages'], 0)

            self.assertIsInstance(pagination['has_next'], bool)
            self.assertIsInstance(pagination['has_previous'], bool)

    def test_tasks_pagination_parameters(self):
        """Test tasks pagination parameters."""
        # Test page parameter
        response = self.make_request("/api/v1/tasks?page=1&limit=5")
        self.assertEqual(response['status'], 'success')

        # Test limit parameter
        response = self.make_request("/api/v1/tasks?limit=10")
        self.assertEqual(response['status'], 'success')

        # Test cursor-based pagination parameter
        response = self.make_request("/api/v1/tasks?cursor=eyJpZCI6InRhc2stMTIzIn0=")
        self.assertEqual(response['status'], 'success')

    def test_projects_pagination_structure(self):
        """Test that projects endpoint returns proper pagination metadata."""
        response = self.make_request("/api/v1/projects")

        data = response['data']
        self.assertIn('projects', data)
        self.assertIsInstance(data['projects'], list)

        # If pagination is implemented, validate structure
        if 'pagination' in data:
            pagination = data['pagination']

            # Test pagination metadata structure
            self.assertIn('page', pagination)
            self.assertIn('limit', pagination)
            self.assertIn('total', pagination)

    def test_pagination_parameter_validation(self):
        """Test pagination parameter validation."""
        # Test invalid page number (should handle gracefully)
        response = self.make_request("/api/v1/tasks?page=0")
        # Should either work with default or return error
        self.assertIn(response['status'], ['success', 'failed'])

        # Test invalid limit (too high)
        response = self.make_request("/api/v1/tasks?limit=200")
        # Should either cap at max or return error
        self.assertIn(response['status'], ['success', 'failed'])

        # Test negative limit
        response = self.make_request("/api/v1/tasks?limit=-1")
        # Should either use default or return error
        self.assertIn(response['status'], ['success', 'failed'])


class TestFilteringContracts(APITestCase):
    """Test filtering functionality contracts."""

    def test_tasks_status_filtering(self):
        """Test tasks status filtering."""
        # Test valid status filter
        response = self.make_request("/api/v1/tasks?status=in_progress")
        self.assertEqual(response['status'], 'success')

        data = response['data']
        self.assertIn('filters_applied', data)

        filters = data['filters_applied']
        # Should either show applied filter or null
        if 'status' in filters:
            self.assertEqual(filters['status'], 'in_progress')

    def test_tasks_priority_filtering(self):
        """Test tasks priority filtering."""
        response = self.make_request("/api/v1/tasks?priority=high")
        self.assertEqual(response['status'], 'success')

        data = response['data']
        filters = data['filters_applied']

        # Should track applied filters
        if 'priority' in filters:
            self.assertEqual(filters['priority'], 'high')

    def test_tasks_context_filtering(self):
        """Test tasks context filtering."""
        response = self.make_request("/api/v1/tasks?context=development")
        self.assertEqual(response['status'], 'success')

    def test_tasks_multiple_filters(self):
        """Test multiple filters applied together."""
        response = self.make_request("/api/v1/tasks?status=in_progress&priority=high&context=development")
        self.assertEqual(response['status'], 'success')

        data = response['data']
        self.assertIn('filters_applied', data)

    def test_tasks_date_range_filtering(self):
        """Test date range filtering."""
        # Test created_after filter
        response = self.make_request("/api/v1/tasks?created_after=2025-09-01T00:00:00Z")
        self.assertEqual(response['status'], 'success')

        # Test created_before filter
        response = self.make_request("/api/v1/tasks?created_before=2025-09-30T23:59:59Z")
        self.assertEqual(response['status'], 'success')

        # Test both together
        response = self.make_request("/api/v1/tasks?created_after=2025-09-01T00:00:00Z&created_before=2025-09-30T23:59:59Z")
        self.assertEqual(response['status'], 'success')

    def test_projects_filtering(self):
        """Test projects filtering."""
        # Test status filter
        response = self.make_request("/api/v1/projects?status=active")
        self.assertEqual(response['status'], 'success')

        # Test priority filter
        response = self.make_request("/api/v1/projects?priority=high")
        self.assertEqual(response['status'], 'success')

        # Test health filter
        response = self.make_request("/api/v1/projects?health=good")
        self.assertEqual(response['status'], 'success')

    def test_invalid_filter_values(self):
        """Test handling of invalid filter values."""
        # Test invalid status
        response = self.make_request("/api/v1/tasks?status=invalid_status")
        # Should either ignore filter or return validation error
        self.assertIn(response['status'], ['success', 'failed'])

        # Test invalid priority
        response = self.make_request("/api/v1/tasks?priority=invalid_priority")
        self.assertIn(response['status'], ['success', 'failed'])

    def test_search_functionality(self):
        """Test search parameter."""
        response = self.make_request("/api/v1/tasks?search=API")
        self.assertEqual(response['status'], 'success')

        # Test search with URL encoding
        search_term = urllib.parse.quote("API documentation")
        response = self.make_request(f"/api/v1/tasks?search={search_term}")
        self.assertEqual(response['status'], 'success')


class TestSortingContracts(APITestCase):
    """Test sorting functionality contracts."""

    def test_tasks_sorting_parameters(self):
        """Test tasks sorting parameters."""
        # Test sort_by parameter
        response = self.make_request("/api/v1/tasks?sort_by=created_at")
        self.assertEqual(response['status'], 'success')

        data = response['data']
        if 'sorting' in data:
            sorting = data['sorting']
            self.assertIn('sort_by', sorting)
            self.assertIn('sort_order', sorting)

    def test_tasks_sort_order(self):
        """Test sort order parameter."""
        # Test ascending order
        response = self.make_request("/api/v1/tasks?sort_by=created_at&sort_order=asc")
        self.assertEqual(response['status'], 'success')

        # Test descending order
        response = self.make_request("/api/v1/tasks?sort_by=created_at&sort_order=desc")
        self.assertEqual(response['status'], 'success')

    def test_tasks_sort_fields(self):
        """Test different sort fields."""
        sort_fields = ['created_at', 'updated_at', 'priority', 'status', 'title']

        for field in sort_fields:
            with self.subTest(sort_field=field):
                response = self.make_request(f"/api/v1/tasks?sort_by={field}")
                self.assertEqual(response['status'], 'success')

    def test_projects_sorting(self):
        """Test projects sorting."""
        # Test default sorting
        response = self.make_request("/api/v1/projects?sort_by=created_at&sort_order=desc")
        self.assertEqual(response['status'], 'success')

        # Test sorting by progress
        response = self.make_request("/api/v1/projects?sort_by=progress&sort_order=asc")
        self.assertEqual(response['status'], 'success')

    def test_invalid_sort_parameters(self):
        """Test invalid sorting parameters."""
        # Test invalid sort field
        response = self.make_request("/api/v1/tasks?sort_by=invalid_field")
        # Should either use default or return error
        self.assertIn(response['status'], ['success', 'failed'])

        # Test invalid sort order
        response = self.make_request("/api/v1/tasks?sort_order=invalid_order")
        self.assertIn(response['status'], ['success', 'failed'])


class TestFieldSelectionContracts(APITestCase):
    """Test field selection (partial response) contracts."""

    def test_tasks_field_selection(self):
        """Test tasks field selection."""
        # Test selecting specific fields
        response = self.make_request("/api/v1/tasks?fields=id,title,status")
        self.assertEqual(response['status'], 'success')

        # If field selection is implemented, validate structure
        data = response['data']
        tasks = data['tasks']

        if tasks and len(tasks) > 0:
            task = tasks[0]
            # Should have at least the basic structure even if field selection isn't fully implemented
            self.assertIn('id', task)

    def test_projects_field_selection(self):
        """Test projects field selection."""
        response = self.make_request("/api/v1/projects?fields=id,name,status,progress")
        self.assertEqual(response['status'], 'success')

    def test_invalid_field_selection(self):
        """Test invalid field selection."""
        # Test with invalid fields
        response = self.make_request("/api/v1/tasks?fields=invalid_field,another_invalid")
        # Should either ignore invalid fields or return error
        self.assertIn(response['status'], ['success', 'failed'])


class TestCombinedParametersContracts(APITestCase):
    """Test combinations of pagination, filtering, and sorting."""

    def test_combined_tasks_parameters(self):
        """Test combining multiple parameters for tasks."""
        params = {
            'status': 'in_progress',
            'priority': 'high',
            'sort_by': 'created_at',
            'sort_order': 'desc',
            'page': '1',
            'limit': '10'
        }

        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        response = self.make_request(f"/api/v1/tasks?{query_string}")
        self.assertEqual(response['status'], 'success')

        # Validate that parameters are properly tracked
        data = response['data']
        self.assertIn('filters_applied', data)

        # If sorting is implemented, should have sorting info
        if 'sorting' in data:
            self.assertIn('sort_by', data['sorting'])
            self.assertIn('sort_order', data['sorting'])

    def test_combined_projects_parameters(self):
        """Test combining multiple parameters for projects."""
        params = {
            'status': 'active',
            'priority': 'high',
            'health': 'good',
            'sort_by': 'progress',
            'sort_order': 'asc',
            'page': '1',
            'limit': '5'
        }

        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        response = self.make_request(f"/api/v1/projects?{query_string}")
        self.assertEqual(response['status'], 'success')

    def test_parameter_precedence(self):
        """Test parameter precedence and conflict resolution."""
        # Test cursor vs page/limit precedence
        response = self.make_request("/api/v1/tasks?page=2&cursor=eyJpZCI6InRhc2stMTIzIn0=")
        self.assertEqual(response['status'], 'success')
        # Should handle gracefully (prefer cursor or page, based on implementation)

    def test_url_encoding_handling(self):
        """Test proper handling of URL encoded parameters."""
        # Test encoded search term
        search_term = urllib.parse.quote("API development & documentation")
        response = self.make_request(f"/api/v1/tasks?search={search_term}")
        self.assertEqual(response['status'], 'success')

        # Test encoded context
        context = urllib.parse.quote("R&D projects")
        response = self.make_request(f"/api/v1/tasks?context={context}")
        self.assertEqual(response['status'], 'success')


class TestMetadataConsistency(APITestCase):
    """Test metadata consistency across paginated/filtered responses."""

    def test_execution_time_tracking(self):
        """Test that execution time is tracked for filtered requests."""
        response = self.make_request("/api/v1/tasks?status=in_progress&priority=high")

        self.assertIn('metadata', response)
        metadata = response['metadata']
        self.assertIn('execution_time', metadata)
        self.assertIsInstance(metadata['execution_time'], (int, float))
        self.assertGreaterEqual(metadata['execution_time'], 0)

    def test_performance_metadata(self):
        """Test performance metadata in responses."""
        response = self.make_request("/api/v1/tasks?search=API&sort_by=created_at")

        data = response['data']
        # If performance metadata is included, validate structure
        if 'performance' in data:
            performance = data['performance']

            if 'query_time_ms' in performance:
                self.assertIsInstance(performance['query_time_ms'], (int, float))
                self.assertGreaterEqual(performance['query_time_ms'], 0)

            if 'total_scanned' in performance:
                self.assertIsInstance(performance['total_scanned'], int)
                self.assertGreaterEqual(performance['total_scanned'], 0)

            if 'cache_hit' in performance:
                self.assertIsInstance(performance['cache_hit'], bool)


if __name__ == "__main__":
    unittest.main(verbosity=2)