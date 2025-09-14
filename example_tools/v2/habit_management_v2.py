"""
Example Tool Implementation: Habit Management v2
Demonstrates complete v2 tool specification with:
- Structured input/output
- Permission checking
- Error handling
- Comprehensive validation
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, date
from dataclasses import dataclass
from enum import Enum

# V2 Tool Framework Imports (would be in actual implementation)
@dataclass
class ToolResponse:
    status: str  # "success" | "failed" | "error"
    command: str
    data: Any = None
    error: Optional['ToolError'] = None
    metadata: Optional['ToolMetadata'] = None

@dataclass
class ToolError:
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    recovery_suggestions: Optional[List[str]] = None

@dataclass
class ToolMetadata:
    version: str
    execution_time: float
    tool_info: Dict[str, Any]
    input_validation: Dict[str, Any]

@dataclass
class UserContext:
    roles: List[str]
    capabilities: List[str]
    user_id: str
    session_info: Optional[Dict[str, Any]] = None

class ToolErrorCode:
    INVALID_INPUT = "TOOL_INVALID_INPUT"
    MISSING_REQUIRED_FIELD = "TOOL_MISSING_REQUIRED_FIELD"
    INSUFFICIENT_PERMISSIONS = "TOOL_INSUFFICIENT_PERMISSIONS"
    RESOURCE_NOT_FOUND = "TOOL_RESOURCE_NOT_FOUND"
    RESOURCE_ALREADY_EXISTS = "TOOL_RESOURCE_ALREADY_EXISTS"

# Example Tool Implementation
class HabitManagementV2:
    """
    V2 Habit Management Tool Implementation
    Demonstrates best practices for v2 tools
    """

    def __init__(self):
        self.tool_info = {
            "name": "Habit Management V2",
            "category": "habit_management",
            "version": "2.0.0"
        }

    def create_habit(
        self,
        input_data: Dict[str, Any],
        user_context: UserContext,
        tool_definition: Dict[str, Any]
    ) -> ToolResponse:
        """
        Create a new habit with comprehensive v2 features

        Demonstrates:
        - Input validation with detailed error messages
        - Permission checking with specific capabilities
        - Structured success/error responses
        - Rich metadata collection
        - Recovery suggestions for failures
        """

        start_time = datetime.now()

        try:
            # Step 1: Input Validation
            validation_result = self._validate_input(input_data, tool_definition)
            if not validation_result["is_valid"]:
                return self._create_validation_error_response(
                    validation_result,
                    start_time
                )

            # Step 2: Permission Check
            permission_result = self._check_permissions(user_context, ["habit.write"])
            if not permission_result["is_authorized"]:
                return self._create_permission_error_response(
                    permission_result,
                    start_time
                )

            # Step 3: Business Logic Validation
            business_validation = self._validate_business_rules(input_data, user_context)
            if not business_validation["is_valid"]:
                return self._create_business_error_response(
                    business_validation,
                    start_time
                )

            # Step 4: Execute Habit Creation
            habit_data = self._execute_habit_creation(input_data, user_context)

            # Step 5: Success Response
            return ToolResponse(
                status="success",
                command="habit.create",
                data={
                    "habit_info": habit_data,
                    "created_at": datetime.now().isoformat(),
                    "next_steps": self._generate_next_steps(habit_data)
                },
                metadata=self._generate_success_metadata(
                    start_time,
                    permission_result["permissions_used"],
                    validation_result["validation_time"]
                )
            )

        except Exception as e:
            return self._create_internal_error_response(str(e), start_time)

    def get_habit_recommendations(
        self,
        input_data: Dict[str, Any],
        user_context: UserContext,
        tool_definition: Dict[str, Any]
    ) -> ToolResponse:
        """
        Get personalized habit recommendations

        Demonstrates:
        - Complex AI-driven recommendations
        - Multiple data source integration
        - Confidence scoring
        - Explanation capabilities integration
        """

        start_time = datetime.now()

        try:
            # Validate input
            if not self._has_permission(user_context, ["habit.read", "ai.recommend"]):
                return self._create_permission_error_response(
                    {"missing_permissions": ["habit.read", "ai.recommend"]},
                    start_time
                )

            # Get user habit history
            user_habits = self._get_user_habits(user_context.user_id)

            # Analyze patterns and generate recommendations
            recommendations = self._generate_recommendations(
                user_habits,
                input_data.get("preferences", {}),
                input_data.get("goals", [])
            )

            return ToolResponse(
                status="success",
                command="habit.recommend",
                data={
                    "recommendations": recommendations,
                    "analysis": {
                        "user_habit_count": len(user_habits),
                        "success_rate": self._calculate_success_rate(user_habits),
                        "preferred_categories": self._analyze_preferred_categories(user_habits),
                        "optimal_difficulty": self._analyze_optimal_difficulty(user_habits)
                    },
                    "explanation": {
                        "methodology": "Based on Atomic Habits principles and personal success patterns",
                        "factors_considered": [
                            "Historical success rates by category",
                            "Current habit load and sustainability",
                            "Complementary habit stacking opportunities",
                            "Energy level matching"
                        ]
                    }
                },
                metadata=self._generate_success_metadata(start_time, ["habit.read", "ai.recommend"])
            )

        except Exception as e:
            return self._create_internal_error_response(str(e), start_time)

    def analyze_habit_patterns(
        self,
        input_data: Dict[str, Any],
        user_context: UserContext,
        tool_definition: Dict[str, Any]
    ) -> ToolResponse:
        """
        Advanced habit pattern analysis

        Demonstrates:
        - Complex data analysis
        - Multiple visualization suggestions
        - Actionable insights
        - Integration with explanation protocol
        """

        start_time = datetime.now()

        try:
            # Check permissions
            if not self._has_permission(user_context, ["habit.read", "data.analyze"]):
                return self._create_permission_error_response(
                    {"missing_permissions": ["habit.read", "data.analyze"]},
                    start_time
                )

            # Get analysis parameters
            days = input_data.get("days", 30)
            habit_filter = input_data.get("habit_filter", {})

            # Perform analysis
            habits = self._get_filtered_habits(user_context.user_id, habit_filter)
            analysis_result = self._perform_pattern_analysis(habits, days)

            return ToolResponse(
                status="success",
                command="habit.analyze_patterns",
                data={
                    "time_period": {
                        "days_analyzed": days,
                        "start_date": (datetime.now().date() - timedelta(days=days)).isoformat(),
                        "end_date": datetime.now().date().isoformat()
                    },
                    "habit_patterns": {
                        "completion_trends": analysis_result["trends"],
                        "weekly_patterns": analysis_result["weekly_patterns"],
                        "streak_analysis": analysis_result["streaks"],
                        "category_performance": analysis_result["category_performance"]
                    },
                    "insights": {
                        "key_findings": analysis_result["insights"],
                        "improvement_opportunities": analysis_result["opportunities"],
                        "risk_factors": analysis_result["risks"]
                    },
                    "recommendations": {
                        "immediate_actions": analysis_result["immediate_actions"],
                        "long_term_strategies": analysis_result["long_term_strategies"],
                        "habit_adjustments": analysis_result["adjustments"]
                    },
                    "visualization_data": {
                        "chart_data": analysis_result["chart_data"],
                        "suggested_charts": [
                            "completion_heatmap",
                            "streak_timeline",
                            "category_breakdown"
                        ]
                    }
                },
                metadata=self._generate_success_metadata(
                    start_time,
                    ["habit.read", "data.analyze"],
                    {"habits_analyzed": len(habits), "computations_performed": analysis_result["computation_count"]}
                )
            )

        except Exception as e:
            return self._create_internal_error_response(str(e), start_time)

    # Helper Methods

    def _validate_input(self, input_data: Dict[str, Any], tool_definition: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive input validation with detailed error reporting"""

        validation_start = datetime.now()
        errors = []
        warnings = []

        # Get schema from tool definition
        schema = tool_definition.get("function_signature", {}).get("input", {}).get("schema", {})
        required_fields = schema.get("required", [])

        # Check required fields
        for field in required_fields:
            if field not in input_data:
                errors.append({
                    "field": field,
                    "error_type": "missing_required_field",
                    "message": f"Required field '{field}' is missing",
                    "suggestion": f"Please provide a value for '{field}'"
                })

        # Validate field types and constraints
        properties = schema.get("properties", {})
        for field, value in input_data.items():
            if field in properties:
                field_validation = self._validate_field(field, value, properties[field])
                errors.extend(field_validation["errors"])
                warnings.extend(field_validation["warnings"])

        validation_time = (datetime.now() - validation_start).total_seconds() * 1000

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "validation_time": validation_time
        }

    def _validate_field(self, field_name: str, value: Any, field_schema: Dict[str, Any]) -> Dict[str, Any]:
        """Validate individual field against schema"""

        errors = []
        warnings = []

        # Type validation
        expected_type = field_schema.get("type")
        if expected_type == "string" and not isinstance(value, str):
            errors.append({
                "field": field_name,
                "error_type": "invalid_type",
                "message": f"Field '{field_name}' must be a string, got {type(value).__name__}",
                "provided_value": value,
                "expected_type": "string"
            })

        elif expected_type == "integer" and not isinstance(value, int):
            errors.append({
                "field": field_name,
                "error_type": "invalid_type",
                "message": f"Field '{field_name}' must be an integer, got {type(value).__name__}",
                "provided_value": value,
                "expected_type": "integer"
            })

        # String constraints
        if isinstance(value, str):
            min_length = field_schema.get("minLength")
            max_length = field_schema.get("maxLength")

            if min_length and len(value) < min_length:
                errors.append({
                    "field": field_name,
                    "error_type": "value_too_short",
                    "message": f"Field '{field_name}' must be at least {min_length} characters long",
                    "provided_length": len(value),
                    "minimum_length": min_length
                })

            if max_length and len(value) > max_length:
                errors.append({
                    "field": field_name,
                    "error_type": "value_too_long",
                    "message": f"Field '{field_name}' must be no more than {max_length} characters long",
                    "provided_length": len(value),
                    "maximum_length": max_length
                })

        # Enum validation
        if "enum" in field_schema:
            allowed_values = field_schema["enum"]
            if value not in allowed_values:
                errors.append({
                    "field": field_name,
                    "error_type": "invalid_enum_value",
                    "message": f"Field '{field_name}' must be one of: {', '.join(map(str, allowed_values))}",
                    "provided_value": value,
                    "allowed_values": allowed_values
                })

        return {"errors": errors, "warnings": warnings}

    def _check_permissions(self, user_context: UserContext, required_capabilities: List[str]) -> Dict[str, Any]:
        """Check if user has required permissions"""

        missing_permissions = []
        permissions_used = []

        for capability in required_capabilities:
            if capability in user_context.capabilities:
                permissions_used.append(capability)
            else:
                missing_permissions.append(capability)

        return {
            "is_authorized": len(missing_permissions) == 0,
            "missing_permissions": missing_permissions,
            "permissions_used": permissions_used
        }

    def _has_permission(self, user_context: UserContext, required_capabilities: List[str]) -> bool:
        """Simple permission check"""
        return all(cap in user_context.capabilities for cap in required_capabilities)

    def _validate_business_rules(self, input_data: Dict[str, Any], user_context: UserContext) -> Dict[str, Any]:
        """Validate business-specific rules"""

        errors = []

        # Check for duplicate habit names
        habit_name = input_data.get("name", "")
        if self._habit_name_exists(habit_name, user_context.user_id):
            errors.append({
                "rule": "unique_habit_name",
                "message": f"A habit named '{habit_name}' already exists",
                "suggestion": "Choose a different name or modify the existing habit"
            })

        # Validate habit scheduling conflicts
        reminder_time = input_data.get("reminder_time")
        if reminder_time and self._has_scheduling_conflict(reminder_time, user_context.user_id):
            errors.append({
                "rule": "scheduling_conflict",
                "message": f"You already have habits scheduled at {reminder_time}",
                "suggestion": "Consider a different reminder time or habit stacking"
            })

        # Check habit load sustainability
        if self._would_exceed_sustainable_habit_load(user_context.user_id):
            errors.append({
                "rule": "sustainable_habit_load",
                "message": "Adding this habit may exceed your sustainable habit capacity",
                "suggestion": "Consider starting with tiny habits or reviewing existing habits"
            })

        return {
            "is_valid": len(errors) == 0,
            "errors": errors
        }

    def _execute_habit_creation(self, input_data: Dict[str, Any], user_context: UserContext) -> Dict[str, Any]:
        """Execute the actual habit creation"""

        # This would integrate with the actual storage system
        habit_id = f"hab_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{user_context.user_id[:8]}"

        habit_data = {
            "id": habit_id,
            "name": input_data["name"],
            "category": input_data.get("category", "other"),
            "frequency": input_data.get("frequency", "daily"),
            "difficulty": input_data.get("difficulty", "easy"),
            "description": input_data.get("description", ""),
            "cue": input_data.get("cue"),
            "routine": input_data.get("routine"),
            "reward": input_data.get("reward"),
            "target_duration": input_data.get("target_duration"),
            "reminder_time": input_data.get("reminder_time"),
            "created_at": datetime.now().isoformat(),
            "user_id": user_context.user_id,
            "initial_streak": 0,
            "total_completions": 0
        }

        # Save to storage (simulated)
        # storage.save_habit(habit_data)

        return habit_data

    def _generate_next_steps(self, habit_data: Dict[str, Any]) -> List[str]:
        """Generate personalized next steps for the new habit"""

        next_steps = [
            f"Set up your environment to make '{habit_data['name']}' easy to start",
        ]

        if habit_data.get("cue"):
            next_steps.append(f"Practice the cue: '{habit_data['cue']}' → start habit")
        else:
            next_steps.append("Define a clear cue (trigger) for when to start this habit")

        if habit_data.get("target_duration") and habit_data["target_duration"] > 15:
            next_steps.append("Consider starting with a 2-minute version to build consistency")

        if habit_data["frequency"] == "daily":
            next_steps.append("Track your habit for the first 7 days to establish momentum")

        return next_steps

    def _generate_success_metadata(
        self,
        start_time: datetime,
        permissions_used: List[str],
        validation_time: Optional[float] = None,
        additional_info: Optional[Dict[str, Any]] = None
    ) -> ToolMetadata:
        """Generate comprehensive success metadata"""

        execution_time = (datetime.now() - start_time).total_seconds()

        return ToolMetadata(
            version="2.0.0",
            execution_time=execution_time,
            tool_info={
                **self.tool_info,
                "permissions_used": permissions_used,
                "additional_info": additional_info or {}
            },
            input_validation={
                "schema_version": "2.0.0",
                "validation_time": validation_time or 0
            }
        )

    def _create_validation_error_response(
        self,
        validation_result: Dict[str, Any],
        start_time: datetime
    ) -> ToolResponse:
        """Create detailed validation error response"""

        return ToolResponse(
            status="failed",
            command="habit.create",
            error=ToolError(
                code=ToolErrorCode.INVALID_INPUT,
                message="Input validation failed",
                details={
                    "validation_errors": validation_result["errors"],
                    "validation_warnings": validation_result.get("warnings", [])
                },
                recovery_suggestions=[
                    "Check the required fields and their formats",
                    "Refer to the tool documentation for valid values",
                    "Use the schema validator to check your input"
                ]
            ),
            metadata=self._generate_error_metadata(start_time, "validation_error")
        )

    def _create_permission_error_response(
        self,
        permission_result: Dict[str, Any],
        start_time: datetime
    ) -> ToolResponse:
        """Create permission error response"""

        return ToolResponse(
            status="failed",
            command="habit.create",
            error=ToolError(
                code=ToolErrorCode.INSUFFICIENT_PERMISSIONS,
                message="Insufficient permissions to perform this action",
                details={
                    "missing_permissions": permission_result["missing_permissions"],
                    "user_roles": permission_result.get("user_roles", [])
                },
                recovery_suggestions=[
                    "Contact your administrator to request additional permissions",
                    "Check if you're logged in with the correct account",
                    "Review the permission requirements in the documentation"
                ]
            ),
            metadata=self._generate_error_metadata(start_time, "permission_error")
        )

    def _create_business_error_response(
        self,
        business_validation: Dict[str, Any],
        start_time: datetime
    ) -> ToolResponse:
        """Create business rule validation error response"""

        return ToolResponse(
            status="failed",
            command="habit.create",
            error=ToolError(
                code=ToolErrorCode.RESOURCE_ALREADY_EXISTS,  # or other appropriate code
                message="Business rule validation failed",
                details={
                    "business_rule_violations": business_validation["errors"]
                },
                recovery_suggestions=[
                    suggestion for error in business_validation["errors"]
                    for suggestion in [error.get("suggestion")]
                    if suggestion
                ]
            ),
            metadata=self._generate_error_metadata(start_time, "business_rule_error")
        )

    def _create_internal_error_response(self, error_message: str, start_time: datetime) -> ToolResponse:
        """Create internal error response"""

        return ToolResponse(
            status="error",
            command="habit.create",
            error=ToolError(
                code="TOOL_INTERNAL_ERROR",
                message="An internal error occurred while processing your request",
                details={"internal_error": error_message},
                recovery_suggestions=[
                    "Try the request again in a few moments",
                    "Check if all services are running properly",
                    "Contact support if the problem persists"
                ]
            ),
            metadata=self._generate_error_metadata(start_time, "internal_error")
        )

    def _generate_error_metadata(self, start_time: datetime, error_type: str) -> ToolMetadata:
        """Generate error metadata"""

        execution_time = (datetime.now() - start_time).total_seconds()

        return ToolMetadata(
            version="2.0.0",
            execution_time=execution_time,
            tool_info={
                **self.tool_info,
                "error_type": error_type,
                "permissions_used": []
            },
            input_validation={
                "schema_version": "2.0.0",
                "validation_time": 0
            }
        )

    # Simulated helper methods (would integrate with real system)

    def _habit_name_exists(self, name: str, user_id: str) -> bool:
        """Check if habit name already exists for user"""
        # Simulate database check
        return False

    def _has_scheduling_conflict(self, reminder_time: str, user_id: str) -> bool:
        """Check for scheduling conflicts"""
        # Simulate scheduling check
        return False

    def _would_exceed_sustainable_habit_load(self, user_id: str) -> bool:
        """Check if adding habit would exceed sustainable load"""
        # Simulate capacity check based on user's current habits
        return False

    def _get_user_habits(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's existing habits"""
        # Simulate database query
        return []

    def _get_filtered_habits(self, user_id: str, habit_filter: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get filtered habits for analysis"""
        # Simulate filtered query
        return []

    def _generate_recommendations(self, habits: List[Dict], preferences: Dict, goals: List) -> List[Dict[str, Any]]:
        """Generate habit recommendations"""
        # Simulate AI recommendation engine
        return [
            {
                "habit_name": "Morning Meditation",
                "category": "mindfulness",
                "confidence": 0.85,
                "reasoning": "Based on your successful health habits and expressed interest in stress reduction",
                "difficulty": "easy",
                "estimated_time": "5 minutes",
                "suggested_cue": "After your morning coffee"
            }
        ]

    def _calculate_success_rate(self, habits: List[Dict]) -> float:
        """Calculate overall habit success rate"""
        # Simulate success rate calculation
        return 0.78

    def _analyze_preferred_categories(self, habits: List[Dict]) -> List[str]:
        """Analyze user's preferred habit categories"""
        # Simulate category analysis
        return ["health", "learning", "productivity"]

    def _analyze_optimal_difficulty(self, habits: List[Dict]) -> str:
        """Analyze user's optimal difficulty level"""
        # Simulate difficulty analysis
        return "easy"

    def _perform_pattern_analysis(self, habits: List[Dict], days: int) -> Dict[str, Any]:
        """Perform comprehensive pattern analysis"""
        # Simulate complex pattern analysis
        return {
            "trends": {"overall_trend": "improving", "trend_strength": 0.65},
            "weekly_patterns": {"best_day": "Monday", "worst_day": "Friday"},
            "streaks": {"average_streak": 12, "longest_streak": 28},
            "category_performance": {"health": 0.85, "learning": 0.72},
            "insights": ["You're most consistent with morning habits", "Weekend habits need attention"],
            "opportunities": ["Stack new habits with strong existing ones"],
            "risks": ["Friday completion rate is concerning"],
            "immediate_actions": ["Set weekend reminders"],
            "long_term_strategies": ["Consider habit stacking strategies"],
            "adjustments": ["Move Friday habits to earlier in the day"],
            "chart_data": {"completion_by_day": [85, 90, 88, 87, 65, 70, 75]},
            "computation_count": 15
        }


# Tool Definition for Registry
HABIT_CREATE_TOOL_DEFINITION = {
    "id": "habit.create",
    "name": "Create Habit",
    "category": "habit_management",
    "version": "2.0.0",
    "description": "Create a new habit with comprehensive v2 features",
    "detailed_description": "Creates a new habit with input validation, permission checking, business rule validation, and rich metadata. Demonstrates v2 tool capabilities including detailed error handling and recovery suggestions.",

    "function_signature": {
        "input": {
            "schema": {
                "type": "object",
                "required": ["name"],
                "properties": {
                    "name": {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": 200,
                        "description": "Name of the habit"
                    },
                    "category": {
                        "type": "string",
                        "enum": ["health", "learning", "productivity", "mindfulness", "social", "creative", "other"],
                        "default": "other",
                        "description": "Habit category"
                    },
                    "frequency": {
                        "type": "string",
                        "enum": ["daily", "weekly", "monthly"],
                        "default": "daily",
                        "description": "How often the habit should be performed"
                    },
                    "difficulty": {
                        "type": "string",
                        "enum": ["tiny", "easy", "medium", "hard"],
                        "default": "easy",
                        "description": "Difficulty level of the habit"
                    },
                    "description": {
                        "type": "string",
                        "maxLength": 1000,
                        "description": "Detailed description of the habit"
                    },
                    "cue": {
                        "type": "string",
                        "maxLength": 500,
                        "description": "Trigger or cue for the habit"
                    },
                    "routine": {
                        "type": "string",
                        "maxLength": 500,
                        "description": "The routine or action to be performed"
                    },
                    "reward": {
                        "type": "string",
                        "maxLength": 500,
                        "description": "Reward for completing the habit"
                    },
                    "target_duration": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 480,
                        "description": "Target duration in minutes"
                    },
                    "reminder_time": {
                        "type": "string",
                        "pattern": "^\\d{2}:\\d{2}$",
                        "description": "Reminder time in HH:MM format"
                    }
                }
            },
            "examples": [
                {
                    "name": "simple_habit",
                    "description": "Create a simple daily habit",
                    "input": {
                        "name": "Morning meditation",
                        "category": "mindfulness",
                        "frequency": "daily",
                        "difficulty": "easy"
                    },
                    "expected_output_type": "success"
                },
                {
                    "name": "comprehensive_habit",
                    "description": "Create a habit with all parameters",
                    "input": {
                        "name": "Evening workout",
                        "category": "health",
                        "frequency": "daily",
                        "difficulty": "medium",
                        "description": "30-minute strength training",
                        "cue": "After dinner cleanup",
                        "routine": "15 min strength + 15 min flexibility",
                        "reward": "Listen to favorite podcast",
                        "target_duration": 30,
                        "reminder_time": "19:30"
                    },
                    "expected_output_type": "success"
                }
            ],
            "required_fields": ["name"]
        },
        "output": {
            "success_schema": {
                "type": "object",
                "required": ["habit_info", "created_at", "next_steps"],
                "properties": {
                    "habit_info": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "name": {"type": "string"},
                            "category": {"type": "string"},
                            "frequency": {"type": "string"},
                            "difficulty": {"type": "string"},
                            "created_at": {"type": "string", "format": "date-time"}
                        }
                    },
                    "created_at": {"type": "string", "format": "date-time"},
                    "next_steps": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                }
            },
            "error_schemas": {
                "TOOL_INVALID_INPUT": {
                    "type": "object",
                    "properties": {
                        "validation_errors": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "field": {"type": "string"},
                                    "error_type": {"type": "string"},
                                    "message": {"type": "string"},
                                    "suggestion": {"type": "string"}
                                }
                            }
                        }
                    }
                }
            },
            "examples": [
                {
                    "name": "successful_creation",
                    "scenario": "Habit created successfully with all validations passing",
                    "response": {
                        "status": "success",
                        "command": "habit.create",
                        "data": {
                            "habit_info": {
                                "id": "hab_20250115_143000_abc12345",
                                "name": "Morning meditation",
                                "category": "mindfulness",
                                "frequency": "daily",
                                "difficulty": "easy",
                                "created_at": "2025-01-15T14:30:00Z"
                            },
                            "created_at": "2025-01-15T14:30:00Z",
                            "next_steps": [
                                "Set up your environment to make 'Morning meditation' easy to start",
                                "Define a clear cue (trigger) for when to start this habit",
                                "Track your habit for the first 7 days to establish momentum"
                            ]
                        },
                        "metadata": {
                            "version": "2.0.0",
                            "execution_time": 0.156,
                            "tool_info": {
                                "name": "Habit Management V2",
                                "category": "habit_management",
                                "permissions_used": ["habit.write"]
                            },
                            "input_validation": {
                                "schema_version": "2.0.0",
                                "validation_time": 15.2
                            }
                        }
                    }
                }
            ]
        },
        "side_effects": [
            {
                "type": "write",
                "description": "Creates a new habit record in the user's habit database",
                "reversible": True
            },
            {
                "type": "write",
                "description": "May create reminder notifications in the user's calendar",
                "reversible": True
            }
        ]
    },

    "permissions": {
        "required_roles": ["user", "power_user", "admin"],
        "required_capabilities": [
            {
                "name": "habit.write",
                "scope": "self_only"
            }
        ],
        "resource_access": [
            {
                "resource_type": "habit_data",
                "access_mode": "create",
                "scope_filter": "current_user"
            }
        ]
    },

    "security_level": "internal",

    "implementation": {
        "type": "class_method",
        "module": "example_tools.v2.habit_management_v2",
        "class_name": "HabitManagementV2",
        "function": "create_habit",
        "version_compatibility": ["2.0.0"]
    },

    "validation": {
        "input_validation": "strict",
        "output_validation": "strict",
        "permission_check": "required",
        "rate_limiting": {
            "max_calls_per_minute": 10,
            "max_calls_per_hour": 100,
            "max_calls_per_day": 500
        }
    },

    "author": "PersonalManager Core Team",
    "created_at": "2025-01-15T00:00:00Z",
    "updated_at": "2025-01-15T00:00:00Z"
}


if __name__ == "__main__":
    # Example usage demonstration
    from datetime import timedelta

    # Create tool instance
    habit_tool = HabitManagementV2()

    # Mock user context
    user_context = UserContext(
        roles=["user"],
        capabilities=["habit.write", "habit.read", "ai.recommend", "data.analyze"],
        user_id="user_12345",
        session_info={"login_time": datetime.now().isoformat()}
    )

    # Test 1: Successful habit creation
    print("=== Test 1: Successful Habit Creation ===")
    create_input = {
        "name": "Morning pushups",
        "category": "health",
        "frequency": "daily",
        "difficulty": "easy",
        "target_duration": 5,
        "cue": "After brushing teeth"
    }

    result = habit_tool.create_habit(
        input_data=create_input,
        user_context=user_context,
        tool_definition=HABIT_CREATE_TOOL_DEFINITION
    )

    print(f"Status: {result.status}")
    print(f"Execution time: {result.metadata.execution_time:.3f}s")
    if result.status == "success":
        print(f"Created habit: {result.data['habit_info']['name']}")
        print(f"Next steps: {result.data['next_steps']}")

    # Test 2: Validation error
    print("\n=== Test 2: Validation Error ===")
    invalid_input = {
        "name": "",  # Empty name should fail validation
        "category": "invalid_category"  # Invalid category
    }

    result = habit_tool.create_habit(
        input_data=invalid_input,
        user_context=user_context,
        tool_definition=HABIT_CREATE_TOOL_DEFINITION
    )

    print(f"Status: {result.status}")
    print(f"Error code: {result.error.code}")
    print(f"Error message: {result.error.message}")
    print(f"Validation errors: {len(result.error.details['validation_errors'])}")

    # Test 3: Permission error
    print("\n=== Test 3: Permission Error ===")
    limited_user_context = UserContext(
        roles=["user"],
        capabilities=["habit.read"],  # Missing habit.write
        user_id="user_12345"
    )

    result = habit_tool.create_habit(
        input_data=create_input,
        user_context=limited_user_context,
        tool_definition=HABIT_CREATE_TOOL_DEFINITION
    )

    print(f"Status: {result.status}")
    print(f"Error code: {result.error.code}")
    print(f"Missing permissions: {result.error.details['missing_permissions']}")
    print(f"Recovery suggestions: {result.error.recovery_suggestions}")