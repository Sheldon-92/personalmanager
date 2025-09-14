"""
Example Tool Implementation: AI Explanation v2
Demonstrates v2 tool specification for explanation tools:
- Integration with Explain Protocol v1.0
- Complex reasoning chains
- Factor analysis with confidence metrics
- Actionable insights generation
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

# Import base types from v2 framework
from habit_management_v2 import ToolResponse, ToolError, ToolMetadata, UserContext, ToolErrorCode


class AIExplanationV2:
    """
    V2 AI Explanation Tool Implementation
    Demonstrates integration with Explain Protocol and advanced AI reasoning
    """

    def __init__(self):
        self.tool_info = {
            "name": "AI Explanation V2",
            "category": "ai_explanation",
            "version": "2.0.0"
        }

    def explain_task_recommendation(
        self,
        input_data: Dict[str, Any],
        user_context: UserContext,
        tool_definition: Dict[str, Any]
    ) -> ToolResponse:
        """
        Explain why a specific task is recommended

        Demonstrates:
        - Integration with Explain Protocol v1.0 structure
        - Complex reasoning chain generation
        - Factor analysis with theory basis
        - Confidence metrics calculation
        - Actionable insights generation
        """

        start_time = datetime.now()

        try:
            # Validate permissions
            if not self._has_permission(user_context, ["ai.explain", "task.read"]):
                return self._create_permission_error_response(
                    {"missing_permissions": ["ai.explain", "task.read"]},
                    start_time
                )

            # Validate input
            task_id = input_data.get("task_id")
            if not task_id:
                return self._create_validation_error_response(
                    {"errors": [{"field": "task_id", "message": "Task ID is required"}]},
                    start_time
                )

            # Get task information
            task_info = self._get_task_info(task_id)
            if not task_info:
                return self._create_resource_not_found_response(
                    f"Task with ID '{task_id}' not found",
                    start_time
                )

            # Generate comprehensive explanation following Explain Protocol
            explanation = self._generate_task_explanation(task_info, user_context)

            return ToolResponse(
                status="success",
                command="ai.explain_task_recommendation",
                data=explanation,
                metadata=self._generate_success_metadata(
                    start_time,
                    ["ai.explain", "task.read"],
                    {"explanation_complexity": explanation["metadata"]["complexity_score"]}
                )
            )

        except Exception as e:
            return self._create_internal_error_response(str(e), start_time)

    def explain_habit_pattern_analysis(
        self,
        input_data: Dict[str, Any],
        user_context: UserContext,
        tool_definition: Dict[str, Any]
    ) -> ToolResponse:
        """
        Explain habit pattern analysis results

        Demonstrates:
        - Multi-source data integration explanation
        - Pattern recognition reasoning
        - Confidence interval calculations
        - Comparative analysis explanations
        """

        start_time = datetime.now()

        try:
            # Check permissions
            if not self._has_permission(user_context, ["ai.explain", "habit.read", "data.analyze"]):
                return self._create_permission_error_response(
                    {"missing_permissions": ["ai.explain", "habit.read", "data.analyze"]},
                    start_time
                )

            # Get analysis parameters
            habit_id = input_data.get("habit_id")
            analysis_period = input_data.get("days", 30)

            # Retrieve habit data and analysis
            habit_info = self._get_habit_info(habit_id)
            pattern_analysis = self._get_pattern_analysis(habit_id, analysis_period)

            # Generate explanation
            explanation = self._generate_pattern_explanation(habit_info, pattern_analysis, analysis_period)

            return ToolResponse(
                status="success",
                command="ai.explain_habit_patterns",
                data=explanation,
                metadata=self._generate_success_metadata(
                    start_time,
                    ["ai.explain", "habit.read", "data.analyze"],
                    {"analysis_points": len(pattern_analysis["data_points"])}
                )
            )

        except Exception as e:
            return self._create_internal_error_response(str(e), start_time)

    def explain_project_health_assessment(
        self,
        input_data: Dict[str, Any],
        user_context: UserContext,
        tool_definition: Dict[str, Any]
    ) -> ToolResponse:
        """
        Explain project health assessment reasoning

        Demonstrates:
        - Multi-factor health assessment explanation
        - Risk factor analysis
        - Temporal trend explanations
        - Comparative benchmarking
        """

        start_time = datetime.now()

        try:
            # Permission check
            if not self._has_permission(user_context, ["ai.explain", "project.read"]):
                return self._create_permission_error_response(
                    {"missing_permissions": ["ai.explain", "project.read"]},
                    start_time
                )

            project_name = input_data.get("project_name")
            if not project_name:
                return self._create_validation_error_response(
                    {"errors": [{"field": "project_name", "message": "Project name is required"}]},
                    start_time
                )

            # Get project data
            project_info = self._get_project_info(project_name)
            health_assessment = self._get_project_health_assessment(project_name)

            # Generate comprehensive health explanation
            explanation = self._generate_project_health_explanation(project_info, health_assessment)

            return ToolResponse(
                status="success",
                command="ai.explain_project_health",
                data=explanation,
                metadata=self._generate_success_metadata(
                    start_time,
                    ["ai.explain", "project.read"],
                    {"assessment_factors": len(health_assessment["factors"])}
                )
            )

        except Exception as e:
            return self._create_internal_error_response(str(e), start_time)

    def explain_decision_comparison(
        self,
        input_data: Dict[str, Any],
        user_context: UserContext,
        tool_definition: Dict[str, Any]
    ) -> ToolResponse:
        """
        Explain comparative decision analysis

        Demonstrates:
        - Multi-option comparison explanations
        - Decision matrix breakdowns
        - Trade-off analysis
        - Sensitivity analysis explanations
        """

        start_time = datetime.now()

        try:
            # Check permissions
            if not self._has_permission(user_context, ["ai.explain", "decision.analyze"]):
                return self._create_permission_error_response(
                    {"missing_permissions": ["ai.explain", "decision.analyze"]},
                    start_time
                )

            # Get comparison parameters
            options = input_data.get("options", [])
            criteria = input_data.get("criteria", {})

            if len(options) < 2:
                return self._create_validation_error_response(
                    {"errors": [{"field": "options", "message": "At least 2 options required for comparison"}]},
                    start_time
                )

            # Generate decision analysis
            comparison_analysis = self._generate_decision_comparison(options, criteria, user_context)

            # Create comprehensive explanation
            explanation = self._generate_comparison_explanation(comparison_analysis)

            return ToolResponse(
                status="success",
                command="ai.explain_decision_comparison",
                data=explanation,
                metadata=self._generate_success_metadata(
                    start_time,
                    ["ai.explain", "decision.analyze"],
                    {
                        "options_compared": len(options),
                        "criteria_evaluated": len(criteria),
                        "analysis_depth": comparison_analysis["depth_score"]
                    }
                )
            )

        except Exception as e:
            return self._create_internal_error_response(str(e), start_time)

    # Core explanation generation methods

    def _generate_task_explanation(self, task_info: Dict[str, Any], user_context: UserContext) -> Dict[str, Any]:
        """Generate comprehensive task recommendation explanation following Explain Protocol"""

        # Subject Information (following Explain Protocol structure)
        subject = {
            "id": task_info["id"],
            "type": "task",
            "title": task_info["title"],
            "description": task_info.get("description", ""),
            "metadata": {
                "created_at": task_info.get("created_at", datetime.now().isoformat()),
                "updated_at": task_info.get("updated_at", datetime.now().isoformat()),
                "priority": task_info.get("priority", "medium"),
                "status": task_info.get("status", "pending")
            }
        }

        # Generate reasoning chain
        reasoning_chain = self._generate_task_reasoning_chain(task_info, user_context)

        # Factor analysis
        factor_analysis = self._generate_task_factor_analysis(task_info, user_context)

        # Confidence metrics
        confidence_metrics = self._calculate_task_confidence_metrics(factor_analysis)

        # Actionable insights
        actionable_insights = self._generate_task_actionable_insights(task_info, factor_analysis)

        # Explanation context
        explanation_context = self._generate_task_explanation_context(user_context)

        # Compile complete explanation following Explain Protocol structure
        return {
            "subject": subject,
            "reasoning": reasoning_chain,
            "factors": factor_analysis,
            "confidence": confidence_metrics,
            "recommendations": actionable_insights,
            "context": explanation_context,
            "metadata": {
                "explanation_type": "task_recommendation",
                "generation_time": datetime.now().isoformat(),
                "complexity_score": self._calculate_explanation_complexity(reasoning_chain, factor_analysis),
                "version": "2.0.0"
            }
        }

    def _generate_task_reasoning_chain(self, task_info: Dict[str, Any], user_context: UserContext) -> Dict[str, Any]:
        """Generate step-by-step reasoning chain for task recommendation"""

        steps = []

        # Step 1: Context Assessment
        steps.append({
            "step_number": 1,
            "description": "Assessed current user context and availability",
            "rationale": "Understanding user's current situation is crucial for appropriate task recommendations",
            "input_data": {
                "user_energy_level": user_context.session_info.get("energy_level", "medium"),
                "available_time": user_context.session_info.get("available_time", 60),
                "current_context": user_context.session_info.get("context", "office")
            },
            "output_result": {
                "context_match_score": 0.85,
                "energy_alignment": "high"
            },
            "confidence": 0.90,
            "execution_time_ms": 15
        })

        # Step 2: Priority Analysis
        steps.append({
            "step_number": 2,
            "description": "Analyzed task priority and urgency factors",
            "rationale": "Task priority determines the order of recommendation",
            "input_data": {
                "task_priority": task_info.get("priority", "medium"),
                "due_date": task_info.get("due_date"),
                "dependencies": task_info.get("dependencies", [])
            },
            "output_result": {
                "urgency_score": self._calculate_urgency_score(task_info),
                "priority_weight": 0.8
            },
            "confidence": 0.88,
            "execution_time_ms": 22
        })

        # Step 3: Framework Evaluation
        steps.append({
            "step_number": 3,
            "description": "Evaluated task against productivity frameworks",
            "rationale": "Multiple framework perspectives provide robust recommendation basis",
            "input_data": {
                "frameworks": ["GTD", "4DX", "OKR", "Atomic Habits", "Essentialism"],
                "task_characteristics": task_info
            },
            "output_result": {
                "framework_scores": self._calculate_framework_scores(task_info),
                "best_framework": "GTD",
                "framework_alignment": 0.82
            },
            "confidence": 0.85,
            "execution_time_ms": 45
        })

        # Step 4: Energy Matching
        steps.append({
            "step_number": 4,
            "description": "Matched task energy requirements with user capacity",
            "rationale": "Energy alignment improves task completion likelihood",
            "input_data": {
                "task_energy_required": task_info.get("energy_required", "medium"),
                "user_current_energy": user_context.session_info.get("energy_level", "medium"),
                "time_of_day_factor": self._get_time_of_day_factor()
            },
            "output_result": {
                "energy_match_score": 0.78,
                "optimal_timing": "current"
            },
            "confidence": 0.75,
            "execution_time_ms": 18
        })

        return {
            "total_steps": len(steps),
            "steps": steps,
            "primary_logic": "Multi-framework weighted scoring with energy and context alignment",
            "fallback_logic": "Simple priority-based ranking if framework analysis fails"
        }

    def _generate_task_factor_analysis(self, task_info: Dict[str, Any], user_context: UserContext) -> Dict[str, Any]:
        """Generate comprehensive factor analysis for task recommendation"""

        factors = []

        # Framework factors
        framework_scores = self._calculate_framework_scores(task_info)
        for framework_id, score in framework_scores.items():
            factors.append({
                "id": f"framework_{framework_id}",
                "name": self._get_framework_name(framework_id),
                "category": "framework",
                "raw_score": score,
                "weight": self._get_framework_weight(framework_id),
                "weighted_contribution": score * self._get_framework_weight(framework_id),
                "confidence": 0.85,
                "theory_basis": self._get_framework_theory_basis(framework_id),
                "evidence": self._generate_framework_evidence(framework_id, task_info),
                "calculation_method": f"Applied {framework_id} scoring algorithm to task attributes"
            })

        # Context factors
        factors.append({
            "id": "context_alignment",
            "name": "Context Alignment",
            "category": "context",
            "raw_score": 0.82,
            "weight": 0.15,
            "weighted_contribution": 0.123,
            "confidence": 0.90,
            "evidence": [
                {
                    "type": "data_point",
                    "description": "Task requires office environment",
                    "value": "office",
                    "weight": 0.8,
                    "source": "task_metadata"
                },
                {
                    "type": "pattern",
                    "description": "User currently in optimal context",
                    "value": user_context.session_info.get("context", "office"),
                    "weight": 0.9,
                    "source": "user_session"
                }
            ],
            "calculation_method": "Context matching algorithm with environment preferences"
        })

        # Temporal factors
        factors.append({
            "id": "temporal_urgency",
            "name": "Temporal Urgency",
            "category": "temporal",
            "raw_score": self._calculate_urgency_score(task_info),
            "weight": 0.20,
            "weighted_contribution": self._calculate_urgency_score(task_info) * 0.20,
            "confidence": 0.92,
            "evidence": [
                {
                    "type": "data_point",
                    "description": "Days until due date",
                    "value": self._days_until_due(task_info.get("due_date")),
                    "weight": 0.9,
                    "source": "task_due_date"
                }
            ],
            "calculation_method": "Exponential decay function based on time to deadline"
        })

        # Calculate total score
        total_score = sum(f["weighted_contribution"] for f in factors)

        return {
            "total_score": min(10.0, total_score * 10),  # Scale to 0-10
            "normalization_method": "weighted_average",
            "factors": factors,
            "factor_interactions": [
                {
                    "factor_ids": ["framework_gtd", "context_alignment"],
                    "interaction_type": "synergy",
                    "strength": 0.75,
                    "description": "GTD framework principles align well with context-aware task selection"
                }
            ]
        }

    def _calculate_task_confidence_metrics(self, factor_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate confidence metrics for task recommendation"""

        # Calculate overall confidence from factor confidences
        factor_confidences = [f["confidence"] for f in factor_analysis["factors"]]
        overall_confidence = sum(factor_confidences) / len(factor_confidences)

        # Breakdown components
        confidence_breakdown = {
            "data_quality": 0.88,  # Based on completeness of task information
            "model_certainty": 0.82,  # Based on framework agreement
            "factor_agreement": self._calculate_factor_agreement(factor_analysis["factors"]),
            "historical_accuracy": 0.79  # Based on past recommendation performance
        }

        # Determine confidence level
        if overall_confidence >= 0.8:
            confidence_level = "high"
        elif overall_confidence >= 0.6:
            confidence_level = "medium"
        else:
            confidence_level = "low"

        return {
            "overall_confidence": overall_confidence,
            "confidence_level": confidence_level,
            "confidence_breakdown": confidence_breakdown,
            "uncertainty_factors": [
                "Limited historical data for this task type",
                "User preferences may vary by time of day"
            ],
            "confidence_interval": {
                "lower_bound": max(0, overall_confidence - 0.15),
                "upper_bound": min(1, overall_confidence + 0.10),
                "confidence_level": 0.90
            }
        }

    def _generate_task_actionable_insights(self, task_info: Dict[str, Any], factor_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate actionable insights and recommendations"""

        primary_recommendation = {
            "action": f"Start working on '{task_info['title']}' now",
            "rationale": f"High alignment with current context and {self._get_top_framework(factor_analysis)} principles",
            "expected_impact": "Increased productivity and goal achievement",
            "effort_level": self._estimate_effort_level(task_info),
            "time_sensitivity": self._assess_time_sensitivity(task_info)
        }

        alternative_options = [
            {
                "option_id": "delay_optimal_time",
                "description": "Wait for optimal energy level alignment",
                "pros": ["Better energy match", "Potentially higher quality output"],
                "cons": ["Risk of procrastination", "May conflict with urgency"],
                "score_difference": -1.2,
                "use_case": "When energy levels are expected to improve significantly"
            },
            {
                "option_id": "break_into_subtasks",
                "description": "Divide task into smaller components",
                "pros": ["Lower cognitive load", "Progress visibility", "Easier to start"],
                "cons": ["Additional planning overhead", "Potential loss of flow"],
                "score_difference": 0.5,
                "use_case": "When the task feels overwhelming or complex"
            }
        ]

        optimization_suggestions = [
            {
                "category": "timing",
                "suggestion": "Schedule during your peak productivity hours",
                "potential_improvement": "20-30% faster completion"
            },
            {
                "category": "environment",
                "suggestion": "Minimize distractions and set up focused workspace",
                "potential_improvement": "Reduced context switching overhead"
            }
        ]

        warning_flags = []
        if self._calculate_urgency_score(task_info) > 0.8:
            warning_flags.append({
                "type": "risk",
                "description": "High urgency may lead to rushed execution",
                "severity": "medium",
                "mitigation": "Allocate extra buffer time for quality assurance"
            })

        return {
            "primary_recommendation": primary_recommendation,
            "alternative_options": alternative_options,
            "optimization_suggestions": optimization_suggestions,
            "warning_flags": warning_flags
        }

    def _generate_task_explanation_context(self, user_context: UserContext) -> Dict[str, Any]:
        """Generate explanation context information"""

        return {
            "temporal": {
                "current_time": datetime.now().isoformat(),
                "time_horizon": "next 4 hours",
                "relevant_time_constraints": ["Meeting at 3 PM", "Daily standup at 9 AM"]
            },
            "environmental": {
                "user_state": {
                    "energy_level": user_context.session_info.get("energy_level", "medium"),
                    "available_time": user_context.session_info.get("available_time", 120),
                    "current_context": user_context.session_info.get("context", "office"),
                    "mood": user_context.session_info.get("mood", "focused")
                },
                "system_state": {
                    "active_projects": 3,
                    "pending_tasks": 12,
                    "recent_completions": 8,
                    "system_load": "moderate"
                }
            },
            "personalization": {
                "user_preferences": {
                    "preferred_work_style": "deep_focus",
                    "optimal_task_duration": "45-90 minutes",
                    "energy_patterns": "morning_person"
                },
                "historical_patterns": [
                    "Higher completion rate for morning tasks",
                    "Prefers challenging tasks when energy is high",
                    "Works best with minimal interruptions"
                ],
                "success_factors": [
                    "Clear task definitions",
                    "Adequate time allocation",
                    "Minimal context switching"
                ],
                "avoid_factors": [
                    "Vague task descriptions",
                    "Tight deadlines without buffer",
                    "Too many concurrent tasks"
                ]
            },
            "data_sources": [
                {
                    "source_name": "task_database",
                    "data_freshness": "real-time",
                    "reliability_score": 0.95,
                    "data_points_used": 1
                },
                {
                    "source_name": "user_preferences",
                    "data_freshness": "last_updated_1_week_ago",
                    "reliability_score": 0.88,
                    "data_points_used": 15
                },
                {
                    "source_name": "historical_performance",
                    "data_freshness": "last_30_days",
                    "reliability_score": 0.82,
                    "data_points_used": 47
                }
            ]
        }

    # Helper methods for pattern and project health explanations

    def _generate_pattern_explanation(self, habit_info: Dict[str, Any], pattern_analysis: Dict[str, Any], days: int) -> Dict[str, Any]:
        """Generate pattern analysis explanation"""

        return {
            "subject": {
                "id": habit_info["id"],
                "type": "habit",
                "title": habit_info["name"],
                "metadata": {"analysis_period": f"{days}_days"}
            },
            "reasoning": {
                "total_steps": 4,
                "steps": [
                    {
                        "step_number": 1,
                        "description": "Collected habit completion data",
                        "rationale": "Historical data provides foundation for pattern recognition",
                        "input_data": {"records_analyzed": len(pattern_analysis["data_points"])},
                        "output_result": {"data_quality_score": 0.92},
                        "confidence": 0.95,
                        "execution_time_ms": 25
                    }
                ],
                "primary_logic": "Time series analysis with behavioral pattern recognition"
            },
            "factors": {
                "total_score": pattern_analysis["overall_pattern_strength"],
                "normalization_method": "z_score",
                "factors": [
                    {
                        "id": "consistency_trend",
                        "name": "Consistency Trend",
                        "category": "temporal",
                        "raw_score": pattern_analysis["consistency_score"],
                        "weight": 0.4,
                        "weighted_contribution": pattern_analysis["consistency_score"] * 0.4,
                        "confidence": 0.88,
                        "evidence": [
                            {
                                "type": "pattern",
                                "description": "Weekly completion pattern",
                                "value": pattern_analysis["weekly_pattern"],
                                "weight": 0.9,
                                "source": "completion_history"
                            }
                        ],
                        "calculation_method": "Moving average with trend detection"
                    }
                ]
            },
            "confidence": {
                "overall_confidence": 0.84,
                "confidence_level": "high",
                "confidence_breakdown": {
                    "data_quality": 0.92,
                    "model_certainty": 0.81,
                    "factor_agreement": 0.86,
                    "historical_accuracy": 0.78
                }
            },
            "recommendations": {
                "primary_recommendation": {
                    "action": "Continue current habit approach with minor optimizations",
                    "rationale": "Strong positive patterns indicate effective habit design",
                    "expected_impact": "Maintain high completion rate while reducing effort",
                    "effort_level": "low",
                    "time_sensitivity": "flexible"
                }
            },
            "context": self._generate_pattern_context(habit_info, days)
        }

    def _generate_project_health_explanation(self, project_info: Dict[str, Any], health_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Generate project health assessment explanation"""

        return {
            "subject": {
                "id": project_info["id"],
                "type": "project",
                "title": project_info["name"],
                "metadata": {
                    "health_status": health_assessment["health"],
                    "assessment_date": datetime.now().isoformat()
                }
            },
            "reasoning": {
                "total_steps": 5,
                "steps": [
                    {
                        "step_number": 1,
                        "description": "Analyzed project progress metrics",
                        "rationale": "Progress tracking indicates project momentum and execution effectiveness",
                        "input_data": {
                            "completion_percentage": project_info["progress"],
                            "milestone_count": len(project_info.get("milestones", [])),
                            "overdue_tasks": project_info.get("overdue_count", 0)
                        },
                        "output_result": {
                            "progress_health_score": health_assessment["progress_score"],
                            "momentum_indicator": "positive"
                        },
                        "confidence": 0.91,
                        "execution_time_ms": 32
                    }
                ],
                "primary_logic": "Multi-dimensional health scoring with risk factor weighting"
            },
            "factors": self._generate_project_health_factors(health_assessment),
            "confidence": {
                "overall_confidence": 0.87,
                "confidence_level": "high",
                "confidence_breakdown": {
                    "data_quality": 0.89,
                    "model_certainty": 0.85,
                    "factor_agreement": 0.88,
                    "historical_accuracy": 0.86
                }
            },
            "recommendations": {
                "primary_recommendation": {
                    "action": self._generate_primary_health_recommendation(health_assessment),
                    "rationale": "Address highest-impact risk factors first",
                    "expected_impact": "Improved project health and delivery confidence",
                    "effort_level": "medium",
                    "time_sensitivity": "this_week"
                }
            },
            "context": self._generate_project_context(project_info)
        }

    # Utility methods for calculations and data retrieval

    def _has_permission(self, user_context: UserContext, required_capabilities: List[str]) -> bool:
        """Check if user has required permissions"""
        return all(cap in user_context.capabilities for cap in required_capabilities)

    def _calculate_urgency_score(self, task_info: Dict[str, Any]) -> float:
        """Calculate task urgency score"""
        due_date = task_info.get("due_date")
        if not due_date:
            return 0.3  # Default low urgency for tasks without due dates

        days_remaining = self._days_until_due(due_date)
        if days_remaining <= 1:
            return 0.95
        elif days_remaining <= 3:
            return 0.8
        elif days_remaining <= 7:
            return 0.6
        else:
            return 0.4

    def _calculate_framework_scores(self, task_info: Dict[str, Any]) -> Dict[str, float]:
        """Calculate framework-specific scores"""
        return {
            "gtd": 0.85,
            "4dx": 0.78,
            "okr": 0.82,
            "atomic_habits": 0.71,
            "essentialism": 0.88
        }

    def _days_until_due(self, due_date: Optional[str]) -> Optional[int]:
        """Calculate days until due date"""
        if not due_date:
            return None

        try:
            due = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
            now = datetime.now(due.tzinfo)
            return (due - now).days
        except:
            return None

    def _calculate_explanation_complexity(self, reasoning_chain: Dict[str, Any], factor_analysis: Dict[str, Any]) -> float:
        """Calculate explanation complexity score"""
        steps = reasoning_chain["total_steps"]
        factors = len(factor_analysis["factors"])
        interactions = len(factor_analysis.get("factor_interactions", []))

        return min(10.0, (steps * 0.5) + (factors * 0.3) + (interactions * 0.2))

    # Mock data retrieval methods (would integrate with real systems)

    def _get_task_info(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve task information"""
        # Mock implementation
        return {
            "id": task_id,
            "title": "Review quarterly budget report",
            "description": "Analyze Q4 budget vs actual spending",
            "priority": "high",
            "due_date": "2025-01-16T17:00:00Z",
            "energy_required": "medium",
            "estimated_duration": 90
        }

    def _get_habit_info(self, habit_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve habit information"""
        return {
            "id": habit_id,
            "name": "Morning exercise",
            "category": "health",
            "frequency": "daily"
        }

    def _get_pattern_analysis(self, habit_id: str, days: int) -> Dict[str, Any]:
        """Retrieve habit pattern analysis"""
        return {
            "data_points": list(range(days)),
            "consistency_score": 0.82,
            "overall_pattern_strength": 7.8,
            "weekly_pattern": [0.9, 0.85, 0.88, 0.91, 0.72, 0.65, 0.78]
        }

    def _get_project_info(self, project_name: str) -> Dict[str, Any]:
        """Retrieve project information"""
        return {
            "id": f"proj_{project_name.lower().replace(' ', '_')}",
            "name": project_name,
            "progress": 75,
            "milestones": ["MVP", "Beta", "Launch"],
            "overdue_count": 2
        }

    def _get_project_health_assessment(self, project_name: str) -> Dict[str, Any]:
        """Retrieve project health assessment"""
        return {
            "health": "warning",
            "progress_score": 0.75,
            "factors": ["progress", "team_velocity", "risk_indicators"]
        }

    # Additional helper methods would continue here...

    def _generate_success_metadata(self, start_time: datetime, permissions_used: List[str], additional_info: Dict[str, Any] = None) -> ToolMetadata:
        """Generate success metadata for explanation tools"""
        from habit_management_v2 import ToolMetadata

        execution_time = (datetime.now() - start_time).total_seconds()

        return ToolMetadata(
            version="2.0.0",
            execution_time=execution_time,
            tool_info={
                **self.tool_info,
                "permissions_used": permissions_used,
                **(additional_info or {})
            },
            input_validation={
                "schema_version": "2.0.0",
                "validation_time": 5.0  # Explanation tools typically have lighter validation
            }
        )

    def _create_permission_error_response(self, permission_result: Dict[str, Any], start_time: datetime) -> ToolResponse:
        """Create permission error response"""
        from habit_management_v2 import ToolResponse, ToolError

        return ToolResponse(
            status="failed",
            command="ai.explain",
            error=ToolError(
                code=ToolErrorCode.INSUFFICIENT_PERMISSIONS,
                message="Insufficient permissions for explanation generation",
                details=permission_result,
                recovery_suggestions=[
                    "Request additional permissions from administrator",
                    "Ensure you have access to the resources being explained"
                ]
            ),
            metadata=self._generate_error_metadata(start_time, "permission_error")
        )

    def _create_validation_error_response(self, validation_result: Dict[str, Any], start_time: datetime) -> ToolResponse:
        """Create validation error response"""
        from habit_management_v2 import ToolResponse, ToolError

        return ToolResponse(
            status="failed",
            command="ai.explain",
            error=ToolError(
                code=ToolErrorCode.INVALID_INPUT,
                message="Input validation failed for explanation request",
                details=validation_result,
                recovery_suggestions=[
                    "Provide all required fields",
                    "Check input format and types"
                ]
            ),
            metadata=self._generate_error_metadata(start_time, "validation_error")
        )

    def _create_resource_not_found_response(self, message: str, start_time: datetime) -> ToolResponse:
        """Create resource not found error response"""
        from habit_management_v2 import ToolResponse, ToolError

        return ToolResponse(
            status="failed",
            command="ai.explain",
            error=ToolError(
                code=ToolErrorCode.RESOURCE_NOT_FOUND,
                message=message,
                recovery_suggestions=[
                    "Check that the resource ID is correct",
                    "Verify you have access to this resource"
                ]
            ),
            metadata=self._generate_error_metadata(start_time, "resource_not_found")
        )

    def _create_internal_error_response(self, error_message: str, start_time: datetime) -> ToolResponse:
        """Create internal error response"""
        from habit_management_v2 import ToolResponse, ToolError

        return ToolResponse(
            status="error",
            command="ai.explain",
            error=ToolError(
                code="TOOL_INTERNAL_ERROR",
                message="Internal error during explanation generation",
                details={"error": error_message},
                recovery_suggestions=[
                    "Retry the request",
                    "Contact support if issue persists"
                ]
            ),
            metadata=self._generate_error_metadata(start_time, "internal_error")
        )

    def _generate_error_metadata(self, start_time: datetime, error_type: str) -> ToolMetadata:
        """Generate error metadata"""
        from habit_management_v2 import ToolMetadata

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

    # Additional placeholder methods
    def _get_framework_name(self, framework_id: str) -> str:
        names = {
            "gtd": "Getting Things Done",
            "4dx": "4 Disciplines of Execution",
            "okr": "Objectives and Key Results",
            "atomic_habits": "Atomic Habits",
            "essentialism": "Essentialism"
        }
        return names.get(framework_id, framework_id.upper())

    def _get_framework_weight(self, framework_id: str) -> float:
        weights = {
            "gtd": 0.25,
            "4dx": 0.20,
            "okr": 0.20,
            "atomic_habits": 0.15,
            "essentialism": 0.20
        }
        return weights.get(framework_id, 0.10)

    def _get_framework_theory_basis(self, framework_id: str) -> Dict[str, str]:
        basis = {
            "gtd": {
                "framework": "GTD",
                "reference": "Getting Things Done by David Allen",
                "concept": "Capture, Clarify, Organize, Reflect, Engage"
            }
        }
        return basis.get(framework_id, {"framework": framework_id, "reference": "Unknown", "concept": "Not specified"})

    def _generate_framework_evidence(self, framework_id: str, task_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [
            {
                "type": "data_point",
                "description": f"Task aligns with {framework_id} principles",
                "value": task_info.get("title", ""),
                "weight": 0.8,
                "source": "framework_analyzer"
            }
        ]

    def _calculate_factor_agreement(self, factors: List[Dict[str, Any]]) -> float:
        scores = [f["raw_score"] for f in factors]
        if not scores:
            return 0.0

        avg = sum(scores) / len(scores)
        variance = sum((s - avg) ** 2 for s in scores) / len(scores)

        return max(0.0, 1.0 - variance)

    def _get_top_framework(self, factor_analysis: Dict[str, Any]) -> str:
        framework_factors = [f for f in factor_analysis["factors"] if f["category"] == "framework"]
        if not framework_factors:
            return "GTD"

        top_factor = max(framework_factors, key=lambda x: x["weighted_contribution"])
        return top_factor["name"]

    def _estimate_effort_level(self, task_info: Dict[str, Any]) -> str:
        duration = task_info.get("estimated_duration", 60)
        if duration <= 30:
            return "low"
        elif duration <= 90:
            return "medium"
        else:
            return "high"

    def _assess_time_sensitivity(self, task_info: Dict[str, Any]) -> str:
        urgency = self._calculate_urgency_score(task_info)
        if urgency >= 0.8:
            return "immediate"
        elif urgency >= 0.6:
            return "today"
        elif urgency >= 0.4:
            return "this_week"
        else:
            return "flexible"

    def _get_time_of_day_factor(self) -> float:
        # Mock time-based factor
        return 0.85

    def _generate_pattern_context(self, habit_info: Dict[str, Any], days: int) -> Dict[str, Any]:
        return {
            "temporal": {
                "current_time": datetime.now().isoformat(),
                "analysis_period": f"{days} days",
                "time_horizon": "next 30 days"
            }
        }

    def _generate_project_health_factors(self, health_assessment: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "total_score": health_assessment["progress_score"] * 10,
            "normalization_method": "weighted_average",
            "factors": [
                {
                    "id": "progress_momentum",
                    "name": "Progress Momentum",
                    "category": "temporal",
                    "raw_score": health_assessment["progress_score"],
                    "weight": 0.4,
                    "weighted_contribution": health_assessment["progress_score"] * 0.4,
                    "confidence": 0.91
                }
            ]
        }

    def _generate_primary_health_recommendation(self, health_assessment: Dict[str, Any]) -> str:
        if health_assessment["health"] == "critical":
            return "Immediate intervention required to prevent project failure"
        elif health_assessment["health"] == "warning":
            return "Address key risk factors and resource constraints"
        else:
            return "Continue current approach with minor optimizations"

    def _generate_project_context(self, project_info: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "temporal": {
                "current_time": datetime.now().isoformat(),
                "project_timeline": "6 months",
                "phase": "development"
            }
        }

    def _generate_decision_comparison(self, options: List[Dict], criteria: Dict, user_context: UserContext) -> Dict[str, Any]:
        return {
            "options": options,
            "criteria": criteria,
            "depth_score": 8.5,
            "comparison_matrix": {}
        }

    def _generate_comparison_explanation(self, comparison_analysis: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "subject": {
                "id": "decision_comparison",
                "type": "decision",
                "title": "Multi-option comparison analysis"
            },
            "comparison_results": comparison_analysis
        }


# Example usage
if __name__ == "__main__":
    # Create explanation tool instance
    explanation_tool = AIExplanationV2()

    # Mock user context
    user_context = UserContext(
        roles=["user"],
        capabilities=["ai.explain", "task.read", "habit.read", "project.read", "data.analyze", "decision.analyze"],
        user_id="user_12345",
        session_info={
            "energy_level": "high",
            "available_time": 120,
            "context": "office",
            "mood": "focused"
        }
    )

    print("=== Example 1: Task Recommendation Explanation ===")

    result = explanation_tool.explain_task_recommendation(
        input_data={"task_id": "task_123"},
        user_context=user_context,
        tool_definition={}
    )

    print(f"Status: {result.status}")
    print(f"Execution time: {result.metadata.execution_time:.3f}s")

    if result.status == "success":
        explanation = result.data
        print(f"Task: {explanation['subject']['title']}")
        print(f"Reasoning steps: {explanation['reasoning']['total_steps']}")
        print(f"Factors analyzed: {len(explanation['factors']['factors'])}")
        print(f"Confidence level: {explanation['confidence']['confidence_level']}")
        print(f"Primary recommendation: {explanation['recommendations']['primary_recommendation']['action']}")

        print("\nKey factors:")
        for factor in explanation['factors']['factors'][:3]:
            print(f"  - {factor['name']}: {factor['raw_score']:.2f} (weight: {factor['weight']:.2f})")

    print(f"\n=== Example 2: Habit Pattern Explanation ===")

    result = explanation_tool.explain_habit_pattern_analysis(
        input_data={"habit_id": "habit_456", "days": 30},
        user_context=user_context,
        tool_definition={}
    )

    print(f"Status: {result.status}")
    if result.status == "success":
        explanation = result.data
        print(f"Habit: {explanation['subject']['title']}")
        print(f"Analysis period: {explanation['subject']['metadata']['analysis_period']}")
        print(f"Pattern strength: {explanation['factors']['total_score']:.1f}/10")