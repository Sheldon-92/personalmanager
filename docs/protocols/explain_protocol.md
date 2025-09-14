# Explain Protocol Design Specification

**Protocol Version**: 1.0
**Document Version**: 1.0
**Last Updated**: 2025-01-15
**Status**: Draft

## Executive Summary

The Explain Protocol provides a standardized structure for AI recommendation explanations in PersonalManager. It integrates seamlessly with the existing status/command/data/error/metadata format while delivering transparent, actionable insights into AI decision-making processes.

## Core Protocol Structure

### Base Response Format

Following the established AI_PROTOCOL_COMPATIBILITY.md standard:

```typescript
interface ExplainResponse extends AIResponse {
  status: "success" | "failed" | "error";
  command: "ai.explain" | "explain.task" | "explain.project" | "explain.time";
  data: ExplanationData | null;
  error?: {
    code: string;
    message: string;
    details?: any;
  };
  metadata: {
    version: string;
    execution_time: number;
    explanation_type: string;
    confidence_level: "high" | "medium" | "low";
  };
}
```

### Explanation Data Structure

```typescript
interface ExplanationData {
  subject: SubjectInfo;           // What's being explained
  reasoning: ReasoningChain;      // Step-by-step logic
  factors: FactorAnalysis;        // Contributing factors with weights
  confidence: ConfidenceMetrics;  // Reliability indicators
  recommendations: ActionableInsights; // Next steps
  context: ExplanationContext;    // Environmental factors
}
```

## Detailed Component Specifications

### 1. Subject Information

```typescript
interface SubjectInfo {
  id: string;                    // Unique identifier
  type: "task" | "project" | "habit" | "time_slot" | "decision";
  title: string;                 // Human-readable name
  description?: string;          // Optional detailed description
  metadata: {
    created_at: string;          // ISO datetime
    updated_at: string;          // ISO datetime
    priority?: "low" | "medium" | "high";
    status?: string;             // Domain-specific status
  };
}
```

### 2. Reasoning Chain

```typescript
interface ReasoningChain {
  total_steps: number;
  steps: ReasoningStep[];
  primary_logic: string;         // Main reasoning approach
  fallback_logic?: string;       // Alternative reasoning if primary fails
}

interface ReasoningStep {
  step_number: number;
  description: string;           // What happened in this step
  rationale: string;             // Why this step matters
  input_data: Record<string, any>; // What data was considered
  output_result: any;            // What was produced
  confidence: number;            // 0.0 - 1.0
  execution_time_ms: number;     // Performance tracking
}
```

### 3. Factor Analysis

```typescript
interface FactorAnalysis {
  total_score: number;           // Final weighted score (0.0 - 10.0)
  normalization_method: string;  // How scores were combined
  factors: Factor[];
  factor_interactions?: FactorInteraction[]; // How factors affect each other
}

interface Factor {
  id: string;                    // Unique factor identifier
  name: string;                  // Human-readable name
  category: "framework" | "context" | "temporal" | "personal" | "system";

  // Scoring details
  raw_score: number;             // Pre-weighted score (0.0 - 1.0)
  weight: number;                // Importance weight (0.0 - 1.0)
  weighted_contribution: number; // raw_score * weight
  confidence: number;            // Reliability of this factor (0.0 - 1.0)

  // Explanation details
  theory_basis?: {
    framework: string;           // e.g., "GTD", "4DX", "Atomic Habits"
    reference: string;           // Book/paper reference
    concept: string;             // Specific concept applied
  };

  // Evidence
  evidence: Evidence[];
  calculation_method: string;    // How this factor was calculated
  sensitivity_analysis?: {       // How sensitive is this factor?
    high_impact_threshold: number;
    low_impact_threshold: number;
  };
}

interface Evidence {
  type: "data_point" | "pattern" | "rule" | "heuristic";
  description: string;
  value: any;                    // The actual evidence
  weight: number;                // How much this evidence mattered
  source: string;                // Where this evidence came from
}

interface FactorInteraction {
  factor_ids: string[];          // Which factors interact
  interaction_type: "synergy" | "conflict" | "dependency";
  strength: number;              // 0.0 - 1.0
  description: string;           // How they interact
}
```

### 4. Confidence Metrics

```typescript
interface ConfidenceMetrics {
  overall_confidence: number;    // 0.0 - 1.0
  confidence_level: "high" | "medium" | "low"; // Categorical

  confidence_breakdown: {
    data_quality: number;        // How good is input data
    model_certainty: number;     // How certain is the AI
    factor_agreement: number;    // How much factors agree
    historical_accuracy: number; // Past performance
  };

  uncertainty_factors: string[]; // What makes this uncertain
  confidence_interval?: {        // Statistical confidence
    lower_bound: number;
    upper_bound: number;
    confidence_level: number;    // e.g., 0.95 for 95% CI
  };
}
```

### 5. Actionable Insights

```typescript
interface ActionableInsights {
  primary_recommendation: {
    action: string;              // What to do
    rationale: string;           // Why do it
    expected_impact: string;     // What will happen
    effort_level: "low" | "medium" | "high";
    time_sensitivity: "immediate" | "today" | "this_week" | "flexible";
  };

  alternative_options: AlternativeOption[];

  optimization_suggestions: {
    category: string;            // e.g., "timing", "context", "preparation"
    suggestion: string;          // Specific advice
    potential_improvement: string; // Expected benefit
  }[];

  warning_flags: {
    type: "risk" | "constraint" | "dependency" | "assumption";
    description: string;
    severity: "low" | "medium" | "high";
    mitigation?: string;         // How to address it
  }[];
}

interface AlternativeOption {
  option_id: string;
  description: string;
  pros: string[];
  cons: string[];
  score_difference: number;      // Compared to primary
  use_case: string;             // When this might be better
}
```

### 6. Explanation Context

```typescript
interface ExplanationContext {
  temporal: {
    current_time: string;        // ISO datetime
    time_horizon: string;        // How far ahead we're considering
    relevant_time_constraints: string[];
  };

  environmental: {
    user_state: {
      energy_level?: "low" | "medium" | "high";
      available_time?: number;   // Minutes
      current_context?: string;  // e.g., "office", "home"
      mood?: string;             // If available
    };
    system_state: {
      active_projects: number;
      pending_tasks: number;
      recent_completions: number;
      system_load: "light" | "moderate" | "heavy";
    };
  };

  personalization: {
    user_preferences: Record<string, any>; // Learned preferences
    historical_patterns: string[];         // Observed patterns
    success_factors: string[];             // What usually works
    avoid_factors: string[];               // What usually doesn't work
  };

  data_sources: {
    source_name: string;
    data_freshness: string;      // How recent is this data
    reliability_score: number;   // 0.0 - 1.0
    data_points_used: number;
  }[];
}
```

## Explanation Types

### 1. Task Recommendation Explanation

**Command**: `explain.task`

Explains why a specific task is recommended for execution now.

**Key Factors**:
- Framework scoring (GTD, 4DX, Full Engagement, etc.)
- Temporal urgency
- Energy matching
- Context alignment
- Priority weighting

**Example Focus**: "Why is 'Review Q4 Budget' recommended right now?"

### 2. Project Prioritization Explanation

**Command**: `explain.project`

Explains project ranking and resource allocation recommendations.

**Key Factors**:
- OKR alignment
- ROI estimation
- Resource availability
- Dependencies
- Strategic importance

**Example Focus**: "Why is 'Mobile App Redesign' ranked higher than 'Internal Dashboard'?"

### 3. Time Allocation Explanation

**Command**: `explain.time`

Explains recommended time blocks and scheduling decisions.

**Key Factors**:
- Energy curves
- Task duration matching
- Context switching costs
- Calendar constraints
- Productivity patterns

**Example Focus**: "Why schedule 'Deep Work' from 9-11 AM instead of 2-4 PM?"

## Protocol Versioning Strategy

### Version Numbering

Using semantic versioning: `MAJOR.MINOR.PATCH`

- **MAJOR**: Breaking changes to core structure
- **MINOR**: New fields or explanation types
- **PATCH**: Bug fixes, clarifications, examples

### Backward Compatibility

```typescript
interface VersionCompatibility {
  supported_versions: string[];          // e.g., ["1.0", "1.1"]
  deprecated_versions: string[];         // Still work but discouraged
  breaking_changes: {
    version: string;
    changes: string[];
    migration_guide_url: string;
  }[];
}
```

### Version Detection

Clients should check `metadata.version` and handle accordingly:

```typescript
// Version handling example
if (semver.gte(response.metadata.version, "2.0.0")) {
  // Use new fields
  processNewFormat(response.data);
} else {
  // Fallback to legacy handling
  processLegacyFormat(response.data);
}
```

## Error Handling

### Explanation-Specific Error Codes

```typescript
enum ExplainErrorCode {
  SUBJECT_NOT_FOUND = "EXPLAIN_SUBJECT_NOT_FOUND",
  INSUFFICIENT_DATA = "EXPLAIN_INSUFFICIENT_DATA",
  MODEL_UNAVAILABLE = "EXPLAIN_MODEL_UNAVAILABLE",
  EXPLANATION_TIMEOUT = "EXPLAIN_TIMEOUT",
  FACTOR_CALCULATION_FAILED = "EXPLAIN_FACTOR_FAILED",
  CONFIDENCE_TOO_LOW = "EXPLAIN_LOW_CONFIDENCE",
  UNSUPPORTED_TYPE = "EXPLAIN_UNSUPPORTED_TYPE"
}
```

### Graceful Degradation

When full explanation fails, provide partial explanation:

```json
{
  "status": "success",
  "command": "explain.task",
  "data": {
    "subject": {...},
    "reasoning": {
      "total_steps": 2,
      "steps": [...],
      "warning": "Partial explanation due to missing data"
    },
    "factors": {
      "total_score": 7.5,
      "factors": [...],
      "excluded_factors": ["energy_match", "context_alignment"],
      "exclusion_reason": "User context data unavailable"
    }
  }
}
```

## Performance Considerations

### Caching Strategy

- **Factor calculations**: Cache for 5 minutes
- **Theory explanations**: Cache for 1 hour
- **User context**: No caching (always fresh)
- **Framework scores**: Cache for 15 minutes

### Response Size Management

- **Compact mode**: Essential fields only (<5KB typical)
- **Full mode**: Complete explanation (10-50KB typical)
- **Streaming**: For large explanations, support chunked responses

### Computation Optimization

```typescript
interface ComputationHints {
  max_explanation_time_ms: number;    // Time budget
  required_confidence_level: number; // Skip low-confidence factors
  factor_importance_threshold: number; // Skip unimportant factors
  detail_level: "minimal" | "standard" | "comprehensive";
}
```

## Security and Privacy

### Data Sensitivity

- **High sensitivity**: User behavior patterns, personal preferences
- **Medium sensitivity**: Task content, project details
- **Low sensitivity**: Framework scores, timing data

### Data Retention

```typescript
interface DataRetentionPolicy {
  explanation_cache_ttl: string;      // "24h"
  personal_data_ttl: string;          // "30d"
  anonymous_analytics_ttl: string;    // "1y"
  user_deletion_policy: string;       // How to handle user data deletion
}
```

### Access Control

Explanations inherit the same access controls as the subject being explained.

## Implementation Guidelines

### Client Integration

1. **Progressive Enhancement**: Start with basic explanations, add detail incrementally
2. **User Control**: Let users choose explanation depth
3. **Visual Design**: Use consistent visual patterns for different factor types
4. **Performance**: Show basic info immediately, load details asynchronously

### Server Implementation

1. **Modular Design**: Separate factor calculators for easier testing
2. **Fallback Logic**: Always provide some explanation, even if partial
3. **Monitoring**: Track explanation quality and user satisfaction
4. **A/B Testing**: Support multiple explanation approaches

### Quality Assurance

```typescript
interface ExplanationQuality {
  completeness_score: number;      // 0.0-1.0, how complete is this explanation
  accuracy_score?: number;         // If ground truth available
  user_satisfaction?: number;      // From feedback
  time_to_understand: number;      // Seconds for user to comprehend
}
```

## Future Extensions

### Planned Features

- **Interactive Explanations**: Allow users to drill down into specific factors
- **Comparative Explanations**: "Why A instead of B?"
- **Historical Explanations**: "How did our recommendation change over time?"
- **What-If Analysis**: "What if I change this parameter?"

### API Evolution

The protocol is designed to support:
- Multi-modal explanations (text + visual)
- Real-time explanation updates
- Collaborative explanations (team contexts)
- Custom factor definitions (user-defined scoring)

---

*This specification provides the foundation for transparent, actionable AI explanations in PersonalManager while maintaining consistency with existing system protocols.*