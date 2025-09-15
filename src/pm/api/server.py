#!/usr/bin/env python3
"""Local read-only REST API server for PersonalManager.

Provides JSON endpoints for tasks, projects, reports and system metrics.
Based on PersonalManager's standardized JSON output format.
"""

import json
import time
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse, parse_qs
import uuid
import sys
import os

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pm.models.task import Task, TaskStatus, TaskPriority, TaskContext
from pm.models.project import ProjectStatus, ProjectHealth, ProjectPriority
from pm.core.config import PMConfig
from pm.obs.integration_logger import (
    get_integration_logger, trace_api_request,
    HandlerStatus, MetricsStatus
)


class APIResponse:
    """Standard API response formatter following PersonalManager JSON protocol."""

    @staticmethod
    def success(command: str, data: Any = None, execution_time: float = 0.0) -> Dict[str, Any]:
        """Format successful API response."""
        return {
            "status": "success",
            "command": command,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "data": data,
            "error": None,
            "metadata": {
                "version": "1.0.0",
                "execution_time": round(execution_time, 3)
            }
        }

    @staticmethod
    def error(command: str, code: str, message: str, details: Dict = None, execution_time: float = 0.0) -> Dict[str, Any]:
        """Format error API response."""
        return {
            "status": "failed",
            "command": command,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "data": None,
            "error": {
                "code": code,
                "message": message,
                "details": details or {}
            },
            "metadata": {
                "version": "1.0.0",
                "execution_time": round(execution_time, 3)
            }
        }


class PersonalManagerAPIHandler(BaseHTTPRequestHandler):
    """HTTP request handler for PersonalManager API endpoints."""

    def __init__(self, *args, **kwargs):
        self.start_time = time.time()
        super().__init__(*args, **kwargs)

    def do_GET(self):
        """Handle GET requests for read-only API endpoints."""
        self.start_time = time.time()

        # Start integration logging
        logger = get_integration_logger()
        parsed_url = urlparse(self.path)
        path = parsed_url.path

        with trace_api_request(path) as req_id:
            try:
                query_params = parse_qs(parsed_url.query)

                # Route requests to appropriate handlers
                if path == "/api/v1/status":
                    self._handle_status(req_id)
                elif path == "/api/v1/tasks":
                    self._handle_tasks(query_params, req_id)
                elif path == "/api/v1/projects":
                    self._handle_projects(query_params, req_id)
                elif path.startswith("/api/v1/reports/"):
                    report_type = path.split("/")[-1]
                    self._handle_reports(report_type, query_params, req_id)
                elif path == "/api/v1/metrics":
                    self._handle_metrics(req_id)
                elif path == "/health":
                    self._handle_health_check(req_id)
                elif path == "/":
                    self._handle_root(req_id)
                else:
                    logger.update_handler_status(req_id, HandlerStatus.ERROR)
                    self._send_error_response("api.not_found", "NOT_FOUND", f"Endpoint {path} not found")

            except Exception as e:
                logger.update_handler_status(req_id, HandlerStatus.ERROR)
                self._send_error_response("api.internal_error", "INTERNAL_ERROR", str(e))

    def _handle_status(self, req_id: str):
        """Handle GET /api/v1/status - System status information."""
        logger = get_integration_logger()

        try:
            with logger.time_component(req_id, "status_processing"):
                config = PMConfig()

                data = {
                    "system": {
                        "name": "PersonalManager",
                        "version": "1.0.0",
                        "status": "running",
                        "uptime": time.time() - self.server.start_time if hasattr(self.server, 'start_time') else 0
                    },
                    "services": {
                        "storage": {
                            "status": "available",
                            "location": str(config.storage_path) if hasattr(config, 'storage_path') else "~/.personalmanager"
                        },
                        "ai": {
                            "claude": {
                                "configured": bool(os.getenv("ANTHROPIC_API_KEY")),
                                "status": "configured" if os.getenv("ANTHROPIC_API_KEY") else "not_configured"
                            },
                            "gemini": {
                                "configured": bool(os.getenv("GOOGLE_API_KEY")),
                                "status": "configured" if os.getenv("GOOGLE_API_KEY") else "not_configured"
                            }
                        }
                    },
                    "endpoints": {
                        "available": [
                            "/api/v1/status",
                            "/api/v1/tasks",
                            "/api/v1/projects",
                            "/api/v1/reports/{type}",
                            "/api/v1/metrics"
                        ],
                        "read_only": True,
                        "authentication": "none"
                    }
                }

            logger.update_handler_status(req_id, HandlerStatus.OK)
            logger.update_metrics_status(req_id, MetricsStatus.COLLECT_OK)

            self._send_json_response(
                APIResponse.success("api.status", data, time.time() - self.start_time)
            )
        except Exception as e:
            logger.update_handler_status(req_id, HandlerStatus.ERROR)
            self._send_error_response("api.status", "INTERNAL_ERROR", str(e))

    def _validate_query_params(self, query_params: Dict, endpoint: str) -> Optional[Dict[str, Any]]:
        """Validate query parameters and return error response if invalid."""
        # Define valid values for each endpoint
        valid_task_statuses = ['inbox', 'next_action', 'project', 'waiting_for', 'someday_maybe', 'reference', 'completed', 'deleted',
                              'in_progress', 'pending']  # Support old values for backward compatibility
        valid_priorities = ['high', 'medium', 'low']
        valid_project_statuses = ['active', 'completed', 'planning', 'on_hold', 'cancelled']
        valid_project_health = ['excellent', 'good', 'warning', 'critical', 'unknown']
        valid_sort_fields_tasks = ['created_at', 'updated_at', 'priority', 'status', 'title', 'due_date']
        valid_sort_fields_projects = ['created_at', 'updated_at', 'priority', 'status', 'name', 'progress', 'health']
        valid_sort_orders = ['asc', 'desc']

        # Check limit parameter
        if 'limit' in query_params:
            try:
                limit = int(query_params['limit'][0])
                if limit <= 0 or limit > 100:
                    return self._error_response("INVALID_PARAMETER",
                        "Limit must be between 1 and 100",
                        {"field": "limit", "value": limit, "expected": "1-100"}, 422)
            except (ValueError, IndexError):
                return self._error_response("INVALID_PARAMETER",
                    "Invalid limit value",
                    {"field": "limit", "expected": "integer between 1 and 100"}, 422)

        # Check page parameter
        if 'page' in query_params:
            try:
                page = int(query_params['page'][0])
                if page <= 0:
                    return self._error_response("INVALID_PARAMETER",
                        "Page must be >= 1",
                        {"field": "page", "value": page, "expected": ">= 1"}, 422)
            except (ValueError, IndexError):
                return self._error_response("INVALID_PARAMETER",
                    "Invalid page value",
                    {"field": "page", "expected": "integer >= 1"}, 422)

        # Endpoint-specific validation
        if endpoint == 'tasks':
            # Validate task status
            if 'status' in query_params:
                status = query_params['status'][0]
                if status and status not in valid_task_statuses:
                    return self._error_response("INVALID_FILTER_VALUE",
                        f"Invalid status value: {status}",
                        {"field": "status", "value": status, "expected": valid_task_statuses}, 422)

            # Validate priority
            if 'priority' in query_params:
                priority = query_params['priority'][0]
                if priority and priority not in valid_priorities:
                    return self._error_response("INVALID_FILTER_VALUE",
                        f"Invalid priority value: {priority}",
                        {"field": "priority", "value": priority, "expected": valid_priorities}, 422)

            # Validate sort_by for tasks
            if 'sort_by' in query_params:
                sort_by = query_params['sort_by'][0]
                if sort_by not in valid_sort_fields_tasks:
                    return self._error_response("INVALID_SORT_FIELD",
                        f"Invalid sort field: {sort_by}",
                        {"field": "sort_by", "value": sort_by, "expected": valid_sort_fields_tasks}, 422)

        elif endpoint == 'projects':
            # Validate project status
            if 'status' in query_params:
                status = query_params['status'][0]
                if status and status not in valid_project_statuses:
                    return self._error_response("INVALID_FILTER_VALUE",
                        f"Invalid status value: {status}",
                        {"field": "status", "value": status, "expected": valid_project_statuses}, 422)

            # Validate priority
            if 'priority' in query_params:
                priority = query_params['priority'][0]
                if priority and priority not in valid_priorities:
                    return self._error_response("INVALID_FILTER_VALUE",
                        f"Invalid priority value: {priority}",
                        {"field": "priority", "value": priority, "expected": valid_priorities}, 422)

            # Validate health
            if 'health' in query_params:
                health = query_params['health'][0]
                if health and health not in valid_project_health:
                    return self._error_response("INVALID_FILTER_VALUE",
                        f"Invalid health value: {health}",
                        {"field": "health", "value": health, "expected": valid_project_health}, 422)

            # Validate sort_by for projects
            if 'sort_by' in query_params:
                sort_by = query_params['sort_by'][0]
                if sort_by not in valid_sort_fields_projects:
                    return self._error_response("INVALID_SORT_FIELD",
                        f"Invalid sort field: {sort_by}",
                        {"field": "sort_by", "value": sort_by, "expected": valid_sort_fields_projects}, 422)

        # Validate sort_order for both endpoints
        if 'sort_order' in query_params:
            sort_order = query_params['sort_order'][0]
            if sort_order not in valid_sort_orders:
                return self._error_response("INVALID_PARAMETER",
                    f"Invalid sort order: {sort_order}",
                    {"field": "sort_order", "value": sort_order, "expected": valid_sort_orders}, 422)

        # Validate date parameters - check if created_after is before created_before
        if 'created_after' in query_params and 'created_before' in query_params:
            created_after = query_params['created_after'][0]
            created_before = query_params['created_before'][0]
            if created_after and created_before and created_after > created_before:
                return self._error_response("UNPROCESSABLE_ENTITY",
                    f"created_after ({created_after}) must be before created_before ({created_before})",
                    {"created_after": created_after, "created_before": created_before}, 422)

        return None  # No validation errors

    def _error_response(self, code: str, message: str, details: Dict = None, status_code: int = 400) -> Dict[str, Any]:
        """Create a standardized error response."""
        return {
            "error_response": APIResponse.error("api.validation", code, message, details, time.time() - self.start_time),
            "status_code": status_code
        }

    def _handle_tasks(self, query_params: Dict, req_id: str):
        """Handle GET /api/v1/tasks - Task listing with filters."""
        logger = get_integration_logger()

        try:
            # Validate query parameters
            with logger.time_component(req_id, "validation"):
                validation_error = self._validate_query_params(query_params, 'tasks')
                if validation_error:
                    logger.update_handler_status(req_id, HandlerStatus.ERROR)
                    self._send_json_response(validation_error["error_response"], validation_error["status_code"])
                    return

            # Mock task data - in real implementation, this would come from storage
            with logger.time_component(req_id, "data_retrieval"):
                tasks = [
                {
                    "id": "task-001",
                    "title": "Implement API server",
                    "description": "Create REST API endpoints for PersonalManager",
                    "status": "next_action",
                    "priority": "high",
                    "context": "development",
                    "created_at": "2025-09-14T10:00:00Z",
                    "updated_at": "2025-09-14T15:30:00Z",
                    "due_date": "2025-09-14T18:00:00Z",
                    "tags": ["api", "rest", "sprint-3"],
                    "project_id": "project-001"
                },
                {
                    "id": "task-002",
                    "title": "Write OpenAPI documentation",
                    "description": "Create OpenAPI 3.0 specification for API endpoints",
                    "status": "inbox",
                    "priority": "medium",
                    "context": "documentation",
                    "created_at": "2025-09-14T10:15:00Z",
                    "updated_at": "2025-09-14T10:15:00Z",
                    "due_date": "",
                    "tags": ["documentation", "openapi", "api"],
                    "project_id": "project-001"
                }
            ]

            # Apply filters from query parameters
            status_filter = query_params.get('status', [None])[0]
            priority_filter = query_params.get('priority', [None])[0]

            filtered_tasks = tasks
            if status_filter:
                filtered_tasks = [t for t in filtered_tasks if t['status'] == status_filter]
            if priority_filter:
                filtered_tasks = [t for t in filtered_tasks if t['priority'] == priority_filter]

            # Calculate summary
            summary = {
                "total": len(filtered_tasks),
                "by_status": {},
                "by_priority": {},
                "by_context": {}
            }

            for task in filtered_tasks:
                # Count by status
                status = task['status']
                summary['by_status'][status] = summary['by_status'].get(status, 0) + 1

                # Count by priority
                priority = task['priority']
                summary['by_priority'][priority] = summary['by_priority'].get(priority, 0) + 1

                # Count by context
                context = task['context']
                summary['by_context'][context] = summary['by_context'].get(context, 0) + 1

            # Build filters_applied object ensuring non-null string values
            filters_applied = {
                "status": status_filter if status_filter else "all",
                "priority": priority_filter if priority_filter else "all",
                "context": query_params.get('context', [None])[0] if query_params.get('context', [None])[0] else "all",
                "project_id": query_params.get('project_id', [None])[0] if query_params.get('project_id', [None])[0] else "all",
                "search": query_params.get('search', [None])[0] if query_params.get('search', [None])[0] else "",
                "created_after": query_params.get('created_after', [None])[0] if query_params.get('created_after', [None])[0] else "",
                "created_before": query_params.get('created_before', [None])[0] if query_params.get('created_before', [None])[0] else "",
                "tags": query_params.get('tags', [''])[0].split(',') if query_params.get('tags', [''])[0] else []
            }

            # Add pagination metadata
            page = int(query_params.get('page', ['1'])[0])
            limit = int(query_params.get('limit', ['10'])[0])
            total = len(filtered_tasks)

            pagination = {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": (total + limit - 1) // limit if limit > 0 else 1,
                "has_next": page * limit < total,
                "has_previous": page > 1,
                "next_cursor": "",
                "prev_cursor": ""
            }

            data = {
                "tasks": filtered_tasks,
                "summary": summary,
                "filters_applied": filters_applied,
                "pagination": pagination
            }

            logger.update_handler_status(req_id, HandlerStatus.OK)
            logger.update_metrics_status(req_id, MetricsStatus.WRITE_OK)

            self._send_json_response(
                APIResponse.success("api.tasks", data, time.time() - self.start_time)
            )
        except Exception as e:
            logger.update_handler_status(req_id, HandlerStatus.ERROR)
            self._send_error_response("api.tasks", "INTERNAL_ERROR", str(e))

    def _handle_projects(self, query_params: Dict, req_id: str):
        """Handle GET /api/v1/projects - Project listing."""
        logger = get_integration_logger()
        try:
            # Validate query parameters
            validation_error = self._validate_query_params(query_params, 'projects')
            if validation_error:
                self._send_json_response(validation_error["error_response"], validation_error["status_code"])
                return
            # Mock project data - in real implementation, this would come from storage
            projects = [
                {
                    "id": "project-001",
                    "name": "PersonalManager API Development",
                    "description": "Implement REST API for PersonalManager system",
                    "status": "active",
                    "priority": "high",
                    "health": "good",
                    "progress": 75.0,
                    "created_at": "2025-09-10T09:00:00Z",
                    "updated_at": "2025-09-14T15:30:00Z",
                    "due_date": "2025-09-15T23:59:59Z",
                    "tags": ["api", "development", "sprint-3"],
                    "task_count": 5,
                    "completed_tasks": 3,
                    "owner": "development-team"
                },
                {
                    "id": "project-002",
                    "name": "Documentation Update",
                    "description": "Update all project documentation for Sprint 3",
                    "status": "planning",
                    "priority": "medium",
                    "health": "excellent",
                    "progress": 25.0,
                    "created_at": "2025-09-12T14:00:00Z",
                    "updated_at": "2025-09-14T12:00:00Z",
                    "due_date": "2025-09-20T23:59:59Z",
                    "tags": ["documentation", "sprint-3"],
                    "task_count": 8,
                    "completed_tasks": 2,
                    "owner": "documentation-team"
                }
            ]

            # Apply filters
            status_filter = query_params.get('status', [None])[0]
            priority_filter = query_params.get('priority', [None])[0]

            filtered_projects = projects
            if status_filter:
                filtered_projects = [p for p in filtered_projects if p['status'] == status_filter]
            if priority_filter:
                filtered_projects = [p for p in filtered_projects if p['priority'] == priority_filter]

            # Calculate summary
            summary = {
                "total": len(filtered_projects),
                "active": len([p for p in filtered_projects if p['status'] == 'active']),
                "completed": len([p for p in filtered_projects if p['status'] == 'completed']),
                "planning": len([p for p in filtered_projects if p['status'] == 'planning']),
                "average_progress": sum(p['progress'] for p in filtered_projects) / len(filtered_projects) if filtered_projects else 0
            }

            # Build filters_applied object ensuring non-null values
            filters_applied = {
                "status": status_filter if status_filter else "all",
                "priority": priority_filter if priority_filter else "all",
                "health": query_params.get('health', [None])[0] if query_params.get('health', [None])[0] else "all",
                "owner": query_params.get('owner', [None])[0] if query_params.get('owner', [None])[0] else "all",
                "progress_min": 0,
                "progress_max": 100
            }

            # Handle numeric filters
            if 'progress_min' in query_params:
                try:
                    filters_applied["progress_min"] = float(query_params['progress_min'][0])
                except (ValueError, IndexError):
                    filters_applied["progress_min"] = 0

            if 'progress_max' in query_params:
                try:
                    filters_applied["progress_max"] = float(query_params['progress_max'][0])
                except (ValueError, IndexError):
                    filters_applied["progress_max"] = 100

            # Add pagination metadata
            page = int(query_params.get('page', ['1'])[0])
            limit = int(query_params.get('limit', ['10'])[0])
            total = len(filtered_projects)

            pagination = {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": (total + limit - 1) // limit if limit > 0 else 1,
                "has_next": page * limit < total,
                "has_previous": page > 1,
                "next_cursor": "",
                "prev_cursor": ""
            }

            data = {
                "projects": filtered_projects,
                "summary": summary,
                "filters_applied": filters_applied,
                "pagination": pagination
            }

            logger.update_handler_status(req_id, HandlerStatus.OK)
            logger.update_metrics_status(req_id, MetricsStatus.WRITE_OK)

            self._send_json_response(
                APIResponse.success("api.projects", data, time.time() - self.start_time)
            )
        except Exception as e:
            logger.update_handler_status(req_id, HandlerStatus.ERROR)
            self._send_error_response("api.projects", "INTERNAL_ERROR", str(e))

    def _handle_reports(self, report_type: str, query_params: Dict, req_id: str):
        """Handle GET /api/v1/reports/{type} - Report retrieval."""
        logger = get_integration_logger()
        try:
            valid_report_types = ["status", "progress", "performance", "summary"]

            if report_type not in valid_report_types:
                self._send_error_response(
                    "api.reports",
                    "INVALID_REPORT_TYPE",
                    f"Report type '{report_type}' not supported. Valid types: {', '.join(valid_report_types)}"
                )
                return

            # Mock report data based on type
            if report_type == "status":
                report_data = {
                    "report_type": "status",
                    "generated_at": datetime.utcnow().isoformat() + "Z",
                    "period": "current",
                    "data": {
                        "overall_status": "good",
                        "total_tasks": 15,
                        "completed_tasks": 8,
                        "in_progress_tasks": 5,
                        "blocked_tasks": 2,
                        "total_projects": 3,
                        "active_projects": 2,
                        "completed_projects": 1
                    }
                }
            elif report_type == "progress":
                report_data = {
                    "report_type": "progress",
                    "generated_at": datetime.utcnow().isoformat() + "Z",
                    "period": "weekly",
                    "data": {
                        "tasks_completed_this_week": 12,
                        "projects_advanced": 2,
                        "productivity_score": 85.5,
                        "trend": "increasing",
                        "goals_met": 4,
                        "goals_total": 5
                    }
                }
            elif report_type == "performance":
                report_data = {
                    "report_type": "performance",
                    "generated_at": datetime.utcnow().isoformat() + "Z",
                    "period": "monthly",
                    "data": {
                        "api_response_time_avg": 45.2,
                        "storage_usage_mb": 125.8,
                        "ai_queries_count": 342,
                        "success_rate": 98.7,
                        "error_rate": 1.3
                    }
                }
            else:  # summary
                report_data = {
                    "report_type": "summary",
                    "generated_at": datetime.utcnow().isoformat() + "Z",
                    "period": "all_time",
                    "data": {
                        "total_tasks_created": 156,
                        "total_tasks_completed": 134,
                        "total_projects": 8,
                        "active_since": "2025-09-01T00:00:00Z",
                        "most_productive_day": "Tuesday",
                        "average_task_completion_time_hours": 6.5
                    }
                }

            data = {
                "report": report_data,
                "metadata": {
                    "requested_type": report_type,
                    "available_types": valid_report_types
                }
            }

            logger.update_handler_status(req_id, HandlerStatus.OK)
            logger.update_metrics_status(req_id, MetricsStatus.WRITE_OK)

            self._send_json_response(
                APIResponse.success("api.reports", data, time.time() - self.start_time)
            )
        except Exception as e:
            logger.update_handler_status(req_id, HandlerStatus.ERROR)
            self._send_error_response("api.reports", "INTERNAL_ERROR", str(e))

    def _handle_metrics(self, req_id: str):
        """Handle GET /api/v1/metrics - Performance metrics."""
        logger = get_integration_logger()
        try:
            with logger.time_component(req_id, "metrics_collection"):
                import psutil
                import platform

                # System metrics - reduce interval to improve performance
                cpu_percent = psutil.cpu_percent(interval=0.01)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')

                data = {
                    "system_metrics": {
                        "cpu_usage_percent": cpu_percent,
                        "memory_usage_percent": memory.percent,
                        "memory_available_mb": round(memory.available / (1024 * 1024), 2),
                        "disk_usage_percent": round(disk.used / disk.total * 100, 2),
                        "disk_available_gb": round(disk.free / (1024**3), 2),
                        "platform": platform.system(),
                        "python_version": platform.python_version()
                    },
                    "api_metrics": {
                        "uptime_seconds": time.time() - (self.server.start_time if hasattr(self.server, 'start_time') else time.time()),
                        "requests_served": getattr(self.server, 'request_count', 0),
                        "endpoints_available": 5,
                        "average_response_time_ms": 50.0
                    },
                    "application_metrics": {
                        "tasks_in_system": 15,
                        "projects_in_system": 3,
                        "storage_size_mb": 45.2,
                        "last_backup": "2025-09-14T10:00:00Z",
                        "data_integrity_status": "good"
                    }
                }

            logger.update_handler_status(req_id, HandlerStatus.OK)
            logger.update_metrics_status(req_id, MetricsStatus.COLLECT_OK)

            self._send_json_response(
                APIResponse.success("api.metrics", data, time.time() - self.start_time)
            )
        except ImportError:
            # Fallback if psutil not available
            import platform
            data = {
                "system_metrics": {
                    "cpu_usage_percent": "unavailable",
                    "memory_usage_percent": "unavailable",
                    "platform": platform.system(),
                    "python_version": platform.python_version()
                },
                "api_metrics": {
                    "uptime_seconds": time.time() - (self.server.start_time if hasattr(self.server, 'start_time') else time.time()),
                    "requests_served": getattr(self.server, 'request_count', 0),
                    "endpoints_available": 5,
                    "average_response_time_ms": 50.0
                },
                "note": "System metrics unavailable (psutil not installed)"
            }
            logger.update_handler_status(req_id, HandlerStatus.OK)
            logger.update_metrics_status(req_id, MetricsStatus.COLLECT_OK)
            self._send_json_response(
                APIResponse.success("api.metrics", data, time.time() - self.start_time)
            )
        except Exception as e:
            logger.update_handler_status(req_id, HandlerStatus.ERROR)
            self._send_error_response("api.metrics", "INTERNAL_ERROR", str(e))

    def _handle_health_check(self, req_id: str):
        """Handle GET /health - Simple health check."""
        logger = get_integration_logger()
        logger.update_handler_status(req_id, HandlerStatus.OK)
        logger.update_metrics_status(req_id, MetricsStatus.COLLECT_OK)

        data = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "version": "1.0.0"
        }
        self._send_json_response(data, status_code=200)

    def _handle_root(self, req_id: str):
        """Handle GET / - API information."""
        logger = get_integration_logger()
        logger.update_handler_status(req_id, HandlerStatus.OK)
        logger.update_metrics_status(req_id, MetricsStatus.COLLECT_OK)

        data = {
            "name": "PersonalManager API",
            "version": "1.0.0",
            "description": "Local read-only REST API for PersonalManager",
            "endpoints": {
                "status": "/api/v1/status",
                "tasks": "/api/v1/tasks",
                "projects": "/api/v1/projects",
                "reports": "/api/v1/reports/{type}",
                "metrics": "/api/v1/metrics",
                "health": "/health"
            },
            "documentation": "See OpenAPI specification at /docs/api/openapi.yaml"
        }
        self._send_json_response(data)

    def _send_json_response(self, data: Dict[str, Any], status_code: int = 200):
        """Send JSON response with proper headers."""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

        json_str = json.dumps(data, indent=2, ensure_ascii=False)
        self.wfile.write(json_str.encode('utf-8'))

    def _send_error_response(self, command: str, error_code: str, message: str, status_code: int = 400):
        """Send standardized error response."""
        response = APIResponse.error(command, error_code, message, execution_time=time.time() - self.start_time)
        self._send_json_response(response, status_code)

    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Content-Length', '0')
        self.end_headers()

    def log_message(self, format, *args):
        """Override to provide cleaner logging."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {format % args}")


class PersonalManagerAPI:
    """Main API server class."""

    def __init__(self, host: str = "localhost", port: int = 8000):
        self.host = host
        self.port = port
        self.server = None

    def start(self):
        """Start the API server."""
        try:
            self.server = HTTPServer((self.host, self.port), PersonalManagerAPIHandler)
            self.server.start_time = time.time()
            self.server.request_count = 0

            print(f"PersonalManager API server starting...")
            print(f"Listening on http://{self.host}:{self.port}")
            print(f"Available endpoints:")
            print(f"  - GET /api/v1/status")
            print(f"  - GET /api/v1/tasks")
            print(f"  - GET /api/v1/projects")
            print(f"  - GET /api/v1/reports/{{type}}")
            print(f"  - GET /api/v1/metrics")
            print(f"  - GET /health")
            print(f"\nPress Ctrl+C to stop the server")

            self.server.serve_forever()

        except KeyboardInterrupt:
            print("\nShutting down server...")
            if self.server:
                self.server.shutdown()
                self.server.server_close()
            print("Server stopped.")
        except Exception as e:
            print(f"Error starting server: {e}")
            if self.server:
                self.server.server_close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="PersonalManager Local API Server")
    parser.add_argument("--host", default="localhost", help="Host to bind to (default: localhost)")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to (default: 8000)")

    args = parser.parse_args()

    api = PersonalManagerAPI(host=args.host, port=args.port)
    api.start()