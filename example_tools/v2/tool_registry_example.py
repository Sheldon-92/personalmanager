"""
Example Tool Registry Implementation for v2
Demonstrates:
- Tool registration and discovery
- Permission management
- Version compatibility
- Migration support
"""

import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum

# Import example tools
from habit_management_v2 import HabitManagementV2, HABIT_CREATE_TOOL_DEFINITION, UserContext
from ai_explanation_v2 import AIExplanationV2


class ToolRegistryV2:
    """
    Complete v2 Tool Registry Implementation
    Demonstrates tool management, discovery, and execution
    """

    def __init__(self, registry_path: Optional[Path] = None):
        self.registry_path = registry_path or Path("config/tool_registry_v2.json")
        self.tools: Dict[str, Dict[str, Any]] = {}
        self.categories: Dict[str, Dict[str, Any]] = {}
        self.permissions: Dict[str, Dict[str, Any]] = {}
        self.tool_instances: Dict[str, Any] = {}

        # Initialize registry
        self._initialize_registry()

    def _initialize_registry(self):
        """Initialize the registry with default tools and configuration"""

        # Load existing registry or create default
        if self.registry_path.exists():
            self.load_registry()
        else:
            self._create_default_registry()

        # Initialize tool instances
        self._initialize_tool_instances()

    def _create_default_registry(self):
        """Create default registry with example tools"""

        # Define categories
        self.categories = {
            "habit_management": {
                "category": "habit_management",
                "name": "Habit Management",
                "description": "Tools for creating, tracking, and analyzing habits",
                "tool_count": 0,
                "common_permissions": [
                    {"name": "habit.read", "scope": "self_only"},
                    {"name": "habit.write", "scope": "self_only"},
                    {"name": "habit.delete", "scope": "self_only"}
                ]
            },
            "ai_explanation": {
                "category": "ai_explanation",
                "name": "AI Explanation",
                "description": "Tools for generating AI-powered explanations and insights",
                "tool_count": 0,
                "common_permissions": [
                    {"name": "ai.explain", "scope": "accessible"},
                    {"name": "data.analyze", "scope": "accessible"}
                ]
            }
        }

        # Define permission scheme
        self.permissions = {
            "version": "2.0.0",
            "roles": {
                "user": {
                    "name": "Standard User",
                    "description": "Regular user with basic permissions",
                    "inherits": []
                },
                "power_user": {
                    "name": "Power User",
                    "description": "Advanced user with extended permissions",
                    "inherits": ["user"]
                },
                "admin": {
                    "name": "Administrator",
                    "description": "System administrator with full permissions",
                    "inherits": ["power_user"]
                }
            },
            "capabilities": {
                "habit.read": {
                    "name": "habit.read",
                    "description": "Read access to habit data",
                    "resource_type": "habit_data",
                    "access_mode": "read",
                    "default_scope": "self_only"
                },
                "habit.write": {
                    "name": "habit.write",
                    "description": "Write access to habit data",
                    "resource_type": "habit_data",
                    "access_mode": "write",
                    "default_scope": "self_only"
                },
                "ai.explain": {
                    "name": "ai.explain",
                    "description": "Access to AI explanation capabilities",
                    "resource_type": "any",
                    "access_mode": "read",
                    "default_scope": "analysis_only"
                },
                "task.read": {
                    "name": "task.read",
                    "description": "Read access to task data",
                    "resource_type": "task_data",
                    "access_mode": "read",
                    "default_scope": "accessible"
                }
            },
            "default_grants": {
                "user": ["habit.read", "habit.write", "task.read"],
                "power_user": ["habit.read", "habit.write", "task.read", "ai.explain"],
                "admin": ["habit.read", "habit.write", "task.read", "ai.explain", "data.analyze"]
            }
        }

        # Register example tools
        self.register_tool(HABIT_CREATE_TOOL_DEFINITION)

        # Create explanation tool definition
        explanation_tool_def = {
            "id": "ai.explain_task_recommendation",
            "name": "Explain Task Recommendation",
            "category": "ai_explanation",
            "version": "2.0.0",
            "description": "Generate comprehensive explanations for task recommendations",
            "function_signature": {
                "input": {
                    "schema": {
                        "type": "object",
                        "required": ["task_id"],
                        "properties": {
                            "task_id": {
                                "type": "string",
                                "description": "ID of the task to explain"
                            }
                        }
                    },
                    "examples": [
                        {
                            "name": "basic_explanation",
                            "description": "Explain why a task is recommended",
                            "input": {"task_id": "task_123"},
                            "expected_output_type": "success"
                        }
                    ],
                    "required_fields": ["task_id"]
                },
                "output": {
                    "success_schema": {
                        "type": "object",
                        "properties": {
                            "subject": {"type": "object"},
                            "reasoning": {"type": "object"},
                            "factors": {"type": "object"},
                            "confidence": {"type": "object"},
                            "recommendations": {"type": "object"},
                            "context": {"type": "object"}
                        }
                    },
                    "examples": []
                }
            },
            "permissions": {
                "required_roles": ["user", "power_user", "admin"],
                "required_capabilities": [
                    {"name": "ai.explain"},
                    {"name": "task.read"}
                ],
                "resource_access": [
                    {
                        "resource_type": "task_data",
                        "access_mode": "read",
                        "scope_filter": "accessible"
                    }
                ]
            },
            "security_level": "internal",
            "implementation": {
                "type": "class_method",
                "module": "example_tools.v2.ai_explanation_v2",
                "class_name": "AIExplanationV2",
                "function": "explain_task_recommendation",
                "version_compatibility": ["2.0.0"]
            },
            "validation": {
                "input_validation": "strict",
                "output_validation": "strict",
                "permission_check": "required"
            },
            "author": "PersonalManager Core Team",
            "created_at": "2025-01-15T00:00:00Z",
            "updated_at": "2025-01-15T00:00:00Z"
        }

        self.register_tool(explanation_tool_def)

        # Save the registry
        self.save_registry()

    def _initialize_tool_instances(self):
        """Initialize instances of registered tools"""

        self.tool_instances = {
            "habit.create": HabitManagementV2(),
            "ai.explain_task_recommendation": AIExplanationV2()
        }

    def register_tool(self, tool_definition: Dict[str, Any]) -> bool:
        """Register a new tool in the registry"""

        try:
            tool_id = tool_definition["id"]

            # Validate tool definition
            validation_result = self._validate_tool_definition(tool_definition)
            if not validation_result["is_valid"]:
                raise ValueError(f"Invalid tool definition: {validation_result['errors']}")

            # Add tool to registry
            self.tools[tool_id] = tool_definition

            # Update category counts
            category = tool_definition["category"]
            if category in self.categories:
                self.categories[category]["tool_count"] += 1
            else:
                # Create new category
                self.categories[category] = {
                    "category": category,
                    "name": category.replace("_", " ").title(),
                    "description": f"Tools for {category.replace('_', ' ')}",
                    "tool_count": 1,
                    "common_permissions": []
                }

            return True

        except Exception as e:
            print(f"Failed to register tool: {e}")
            return False

    def discover_tools(
        self,
        category: Optional[str] = None,
        user_roles: Optional[List[str]] = None,
        search_query: Optional[str] = None,
        include_deprecated: bool = False
    ) -> List[Dict[str, Any]]:
        """Discover tools based on criteria"""

        tools = list(self.tools.values())

        # Filter by category
        if category:
            tools = [t for t in tools if t["category"] == category]

        # Filter by permissions
        if user_roles:
            available_tools = []
            for tool in tools:
                if self._user_can_access_tool(tool, user_roles):
                    available_tools.append(tool)
            tools = available_tools

        # Filter deprecated tools
        if not include_deprecated:
            tools = [t for t in tools if "deprecated_at" not in t]

        # Search filter
        if search_query:
            query_lower = search_query.lower()
            tools = [
                t for t in tools
                if query_lower in t["name"].lower()
                or query_lower in t["description"].lower()
                or query_lower in t["id"].lower()
            ]

        return tools

    def get_tool(self, tool_id: str) -> Optional[Dict[str, Any]]:
        """Get specific tool definition"""
        return self.tools.get(tool_id)

    def execute_tool(
        self,
        tool_id: str,
        input_data: Dict[str, Any],
        user_context: UserContext
    ) -> Any:  # Would return ToolResponse in real implementation
        """Execute a registered tool"""

        # Get tool definition
        tool_definition = self.get_tool(tool_id)
        if not tool_definition:
            raise ValueError(f"Tool '{tool_id}' not found in registry")

        # Check if user has permissions
        if not self.check_permissions(tool_id, user_context):
            raise PermissionError(f"Insufficient permissions for tool '{tool_id}'")

        # Get tool instance
        tool_instance = self.tool_instances.get(tool_id)
        if not tool_instance:
            raise RuntimeError(f"Tool instance '{tool_id}' not available")

        # Execute tool based on implementation type
        implementation = tool_definition["implementation"]

        if implementation["type"] == "class_method":
            method_name = implementation["function"]
            method = getattr(tool_instance, method_name)
            return method(input_data, user_context, tool_definition)

        else:
            raise NotImplementedError(f"Implementation type '{implementation['type']}' not supported")

    def check_permissions(self, tool_id: str, user_context: UserContext) -> bool:
        """Check if user has permissions to execute tool"""

        tool_definition = self.get_tool(tool_id)
        if not tool_definition:
            return False

        required_roles = tool_definition["permissions"]["required_roles"]
        required_capabilities = tool_definition["permissions"]["required_capabilities"]

        # Check roles
        if not any(role in user_context.roles for role in required_roles):
            return False

        # Check capabilities
        for capability in required_capabilities:
            cap_name = capability.get("name") if isinstance(capability, dict) else capability
            if cap_name not in user_context.capabilities:
                return False

        return True

    def get_available_tools(self, user_context: UserContext) -> List[Dict[str, Any]]:
        """Get all tools available to user based on permissions"""

        available_tools = []

        for tool_id, tool_definition in self.tools.items():
            if self.check_permissions(tool_id, user_context):
                available_tools.append(tool_definition)

        return available_tools

    def get_registry_stats(self) -> Dict[str, Any]:
        """Get registry statistics"""

        total_tools = len(self.tools)
        active_tools = len([t for t in self.tools.values() if "deprecated_at" not in t])
        deprecated_tools = total_tools - active_tools

        category_breakdown = {}
        for category, info in self.categories.items():
            category_breakdown[category] = {
                "name": info["name"],
                "tool_count": info["tool_count"]
            }

        return {
            "total_tools": total_tools,
            "active_tools": active_tools,
            "deprecated_tools": deprecated_tools,
            "categories": len(self.categories),
            "category_breakdown": category_breakdown,
            "last_updated": datetime.now().isoformat()
        }

    def search_tools(self, query: str, options: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search tools with advanced options"""

        options = options or {}

        # Basic text search
        results = self.discover_tools(
            category=options.get("category_filter"),
            user_roles=options.get("role_filter"),
            search_query=query,
            include_deprecated=options.get("include_deprecated", False)
        )

        # Additional filtering by security level
        security_filter = options.get("security_level")
        if security_filter:
            results = [r for r in results if r["security_level"] == security_filter]

        # Sort results by relevance (simple scoring)
        def calculate_relevance(tool: Dict[str, Any]) -> float:
            score = 0.0
            query_lower = query.lower()

            # Exact ID match gets highest score
            if query_lower == tool["id"].lower():
                score += 10.0

            # Name matches
            if query_lower in tool["name"].lower():
                score += 5.0

            # Description matches
            if query_lower in tool["description"].lower():
                score += 2.0

            # Category matches
            if query_lower in tool["category"].lower():
                score += 1.0

            return score

        results.sort(key=calculate_relevance, reverse=True)

        return results

    def migrate_v1_tool(
        self,
        v1_module: str,
        v1_function: str,
        v2_definition: Dict[str, Any]
    ) -> bool:
        """Register a v1 tool with v2 compatibility wrapper"""

        try:
            # Add migration metadata
            v2_definition["migration"] = {
                "migrated_from": "v1",
                "original_module": v1_module,
                "original_function": v1_function,
                "migration_date": datetime.now().isoformat(),
                "compatibility_mode": True
            }

            # Register as v2 tool
            return self.register_tool(v2_definition)

        except Exception as e:
            print(f"Failed to migrate v1 tool: {e}")
            return False

    def deprecate_tool(
        self,
        tool_id: str,
        replacement_tool: Optional[str] = None,
        reason: str = "Tool deprecated"
    ) -> bool:
        """Deprecate a tool"""

        if tool_id not in self.tools:
            return False

        self.tools[tool_id]["deprecated_at"] = datetime.now().isoformat()
        self.tools[tool_id]["deprecation_reason"] = reason

        if replacement_tool:
            self.tools[tool_id]["replacement_tool"] = replacement_tool

        # Update category count
        category = self.tools[tool_id]["category"]
        if category in self.categories:
            self.categories[category]["tool_count"] = max(0, self.categories[category]["tool_count"] - 1)

        self.save_registry()
        return True

    def load_registry(self):
        """Load registry from file"""
        try:
            with open(self.registry_path, 'r') as f:
                registry_data = json.load(f)

            self.tools = registry_data.get("tools", {})
            self.categories = registry_data.get("categories", {})
            self.permissions = registry_data.get("permissions", {})

        except Exception as e:
            print(f"Failed to load registry: {e}")

    def save_registry(self):
        """Save registry to file"""
        try:
            registry_data = {
                "version": "2.0.0",
                "last_updated": datetime.now().isoformat(),
                "tools": self.tools,
                "categories": self.categories,
                "permissions": self.permissions
            }

            self.registry_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.registry_path, 'w') as f:
                json.dump(registry_data, f, indent=2, default=str)

        except Exception as e:
            print(f"Failed to save registry: {e}")

    # Helper methods

    def _validate_tool_definition(self, tool_definition: Dict[str, Any]) -> Dict[str, Any]:
        """Validate tool definition against schema"""

        errors = []
        required_fields = ["id", "name", "category", "version", "description", "permissions", "implementation"]

        for field in required_fields:
            if field not in tool_definition:
                errors.append(f"Missing required field: {field}")

        # Validate ID format
        tool_id = tool_definition.get("id", "")
        if not tool_id or "." not in tool_id:
            errors.append("Tool ID must be in format 'category.action'")

        # Validate version format
        version = tool_definition.get("version", "")
        if not version or len(version.split(".")) != 3:
            errors.append("Version must be in semantic versioning format (x.y.z)")

        return {
            "is_valid": len(errors) == 0,
            "errors": errors
        }

    def _user_can_access_tool(self, tool: Dict[str, Any], user_roles: List[str]) -> bool:
        """Check if user with given roles can access tool"""

        required_roles = tool["permissions"]["required_roles"]
        return any(role in user_roles for role in required_roles)


# Tool Registry Manager for advanced operations
class ToolRegistryManager:
    """Advanced tool registry management operations"""

    def __init__(self, registry: ToolRegistryV2):
        self.registry = registry

    def analyze_tool_usage(self, days: int = 30) -> Dict[str, Any]:
        """Analyze tool usage patterns (mock implementation)"""

        # In real implementation, this would query usage logs
        tools = self.registry.tools
        total_tools = len(tools)

        # Mock usage data
        usage_stats = {
            "analysis_period": f"{days} days",
            "total_tools": total_tools,
            "most_used_tools": [
                {"tool_id": "habit.create", "usage_count": 245, "success_rate": 0.94},
                {"tool_id": "ai.explain_task_recommendation", "usage_count": 189, "success_rate": 0.87}
            ],
            "category_usage": {
                "habit_management": {"calls": 312, "success_rate": 0.92},
                "ai_explanation": {"calls": 189, "success_rate": 0.87}
            },
            "performance_metrics": {
                "average_execution_time": 0.156,
                "p95_execution_time": 0.340,
                "error_rate": 0.05
            }
        }

        return usage_stats

    def generate_tool_report(self) -> Dict[str, Any]:
        """Generate comprehensive tool registry report"""

        stats = self.registry.get_registry_stats()

        report = {
            "summary": stats,
            "detailed_analysis": {
                "tools_by_category": {},
                "security_distribution": {},
                "version_distribution": {},
                "migration_status": {}
            },
            "recommendations": []
        }

        # Analyze tools by category
        for tool_id, tool in self.registry.tools.items():
            category = tool["category"]
            if category not in report["detailed_analysis"]["tools_by_category"]:
                report["detailed_analysis"]["tools_by_category"][category] = []

            report["detailed_analysis"]["tools_by_category"][category].append({
                "id": tool_id,
                "name": tool["name"],
                "version": tool["version"],
                "deprecated": "deprecated_at" in tool
            })

        # Security level distribution
        security_levels = {}
        for tool in self.registry.tools.values():
            level = tool.get("security_level", "internal")
            security_levels[level] = security_levels.get(level, 0) + 1

        report["detailed_analysis"]["security_distribution"] = security_levels

        # Generate recommendations
        if stats["deprecated_tools"] > 0:
            report["recommendations"].append(
                f"Consider removing {stats['deprecated_tools']} deprecated tools"
            )

        if len(stats["category_breakdown"]) > 8:
            report["recommendations"].append(
                "Consider consolidating tool categories for better organization"
            )

        return report

    def validate_registry_integrity(self) -> Dict[str, Any]:
        """Validate registry integrity and consistency"""

        issues = []
        warnings = []

        # Check for orphaned tool instances
        registered_tools = set(self.registry.tools.keys())
        instance_tools = set(self.registry.tool_instances.keys())

        orphaned_instances = instance_tools - registered_tools
        missing_instances = registered_tools - instance_tools

        if orphaned_instances:
            issues.append(f"Orphaned tool instances: {list(orphaned_instances)}")

        if missing_instances:
            warnings.append(f"Missing tool instances: {list(missing_instances)}")

        # Check category consistency
        declared_categories = set(self.registry.categories.keys())
        used_categories = set(tool["category"] for tool in self.registry.tools.values())

        unused_categories = declared_categories - used_categories
        undeclared_categories = used_categories - declared_categories

        if unused_categories:
            warnings.append(f"Unused categories: {list(unused_categories)}")

        if undeclared_categories:
            issues.append(f"Undeclared categories: {list(undeclared_categories)}")

        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "validation_time": datetime.now().isoformat()
        }


# Example usage and testing
def main():
    """Demonstrate tool registry functionality"""

    print("=== Tool Registry v2 Demonstration ===\n")

    # Initialize registry
    registry = ToolRegistryV2(Path("example_tool_registry.json"))

    # Create user contexts
    regular_user = UserContext(
        roles=["user"],
        capabilities=["habit.read", "habit.write", "task.read"],
        user_id="user_123",
        session_info={"energy_level": "medium"}
    )

    power_user = UserContext(
        roles=["power_user"],
        capabilities=["habit.read", "habit.write", "task.read", "ai.explain", "data.analyze"],
        user_id="power_user_456",
        session_info={"energy_level": "high"}
    )

    # 1. Tool Discovery
    print("1. Tool Discovery")
    print("=" * 40)

    all_tools = registry.discover_tools()
    print(f"Total tools in registry: {len(all_tools)}")

    habit_tools = registry.discover_tools(category="habit_management")
    print(f"Habit management tools: {len(habit_tools)}")

    # 2. Permission-based tool discovery
    print(f"\n2. Permission-based Tool Access")
    print("=" * 40)

    regular_tools = registry.get_available_tools(regular_user)
    power_tools = registry.get_available_tools(power_user)

    print(f"Tools available to regular user: {len(regular_tools)}")
    print(f"Tools available to power user: {len(power_tools)}")

    for tool in regular_tools:
        print(f"  - {tool['name']} ({tool['id']})")

    # 3. Tool Execution
    print(f"\n3. Tool Execution Example")
    print("=" * 40)

    try:
        # Execute habit creation tool
        result = registry.execute_tool(
            tool_id="habit.create",
            input_data={
                "name": "Morning meditation",
                "category": "mindfulness",
                "difficulty": "easy"
            },
            user_context=regular_user
        )

        print(f"Habit creation result: {result.status}")
        if result.status == "success":
            print(f"Created habit: {result.data['habit_info']['name']}")

    except Exception as e:
        print(f"Execution failed: {e}")

    # 4. Registry Statistics
    print(f"\n4. Registry Statistics")
    print("=" * 40)

    stats = registry.get_registry_stats()
    print(f"Total tools: {stats['total_tools']}")
    print(f"Active tools: {stats['active_tools']}")
    print(f"Categories: {stats['categories']}")

    print("\nCategory breakdown:")
    for category, info in stats['category_breakdown'].items():
        print(f"  - {info['name']}: {info['tool_count']} tools")

    # 5. Tool Search
    print(f"\n5. Tool Search")
    print("=" * 40)

    search_results = registry.search_tools(
        query="habit",
        options={"category_filter": None, "include_deprecated": False}
    )

    print(f"Search results for 'habit': {len(search_results)} tools")
    for tool in search_results:
        print(f"  - {tool['name']} ({tool['id']}) - {tool['description']}")

    # 6. Registry Management
    print(f"\n6. Registry Management")
    print("=" * 40)

    manager = ToolRegistryManager(registry)

    # Usage analysis
    usage_stats = manager.analyze_tool_usage(30)
    print("Usage analysis (30 days):")
    print(f"  Most used: {usage_stats['most_used_tools'][0]['tool_id']} ({usage_stats['most_used_tools'][0]['usage_count']} calls)")
    print(f"  Average execution time: {usage_stats['performance_metrics']['average_execution_time']:.3f}s")

    # Integrity validation
    integrity = manager.validate_registry_integrity()
    print(f"\nRegistry integrity: {'✅ Valid' if integrity['is_valid'] else '❌ Issues found'}")

    if integrity['warnings']:
        print("Warnings:")
        for warning in integrity['warnings']:
            print(f"  - {warning}")

    # 7. Tool Definition Export
    print(f"\n7. Tool Definition Export")
    print("=" * 40)

    habit_tool_def = registry.get_tool("habit.create")
    if habit_tool_def:
        print(f"Habit creation tool definition:")
        print(f"  Name: {habit_tool_def['name']}")
        print(f"  Version: {habit_tool_def['version']}")
        print(f"  Required permissions: {[cap.get('name', cap) for cap in habit_tool_def['permissions']['required_capabilities']]}")
        print(f"  Security level: {habit_tool_def['security_level']}")

    print(f"\n=== Demonstration Complete ===")


if __name__ == "__main__":
    main()