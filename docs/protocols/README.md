# PersonalManager Explain Protocol Documentation

This directory contains the complete specification and implementation guidance for the PersonalManager Explain Protocol v1.0, designed to provide transparent, actionable AI recommendation explanations.

## 📁 Directory Structure

```
docs/protocols/
├── README.md                    # This overview document
├── explain_protocol.md          # Complete protocol specification
├── protocol_comparison.md       # Compatibility analysis
└── ...

schemas/
└── explain_schema.json          # JSON Schema definition

examples/explain/
├── task_recommendation.json     # Task explanation example
├── project_prioritization.json  # Project explanation example
└── time_allocation.json         # Time allocation example
```

## 🚀 Quick Start

### For API Consumers

1. **Review the Protocol**: Read [explain_protocol.md](./explain_protocol.md) for complete specification
2. **Check Examples**: See `examples/explain/` for real-world JSON responses
3. **Validate Responses**: Use `schemas/explain_schema.json` for validation
4. **Ensure Compatibility**: Review [protocol_comparison.md](./protocol_comparison.md)

### For Implementers

1. **Understand Structure**: Follow the protocol specification exactly
2. **Implement Validation**: Use the provided JSON Schema
3. **Test Compatibility**: Ensure existing clients continue working
4. **Reference Examples**: Use examples as implementation templates

## 📊 Protocol Overview

```
ExplainResponse
├── status: "success" | "failed" | "error"
├── command: explain command type
├── data: ExplanationData
│   ├── subject: what's being explained
│   ├── reasoning: step-by-step logic
│   ├── factors: contributing elements with weights
│   ├── confidence: reliability metrics
│   ├── recommendations: actionable insights
│   └── context: environmental factors
├── error?: structured error information
└── metadata: version, timing, confidence
```

## 🔧 Supported Explanation Types

| Type | Command | Purpose | Example Use Case |
|------|---------|---------|------------------|
| **Task** | `explain.task` | Why this task is recommended now | "Why review budget report?" |
| **Project** | `explain.project` | Why this project is prioritized | "Why prioritize mobile redesign?" |
| **Time** | `explain.time` | Why this time slot is optimal | "Why 9-11 AM for deep work?" |

## 🎯 Key Features

### ✅ Complete Transparency
- **Reasoning Chain**: Step-by-step decision logic
- **Factor Analysis**: Weighted contributions with evidence
- **Confidence Metrics**: Reliability indicators
- **Theory Basis**: References to established frameworks

### ✅ Actionable Insights
- **Primary Recommendation**: Clear next action
- **Alternative Options**: Other valid choices with trade-offs
- **Optimization Suggestions**: How to improve outcomes
- **Warning Flags**: Risks and constraints to consider

### ✅ Full Compatibility
- **Backward Compatible**: Existing clients work unchanged
- **Standard Protocols**: Consistent with AI_PROTOCOL_COMPATIBILITY.md
- **Error Handling**: Familiar error codes and structure
- **Version Management**: Semantic versioning support

## 📈 Example Response Preview

```json
{
  "status": "success",
  "command": "explain.task",
  "data": {
    "subject": {
      "id": "tsk_20250115_001",
      "type": "task",
      "title": "Review Q4 Budget Report"
    },
    "reasoning": {
      "total_steps": 5,
      "steps": [
        {
          "step_number": 1,
          "description": "Evaluated task against theoretical frameworks",
          "rationale": "Framework scoring provides objective basis",
          "confidence": 0.88
        }
      ]
    },
    "factors": {
      "total_score": 7.71,
      "factors": [
        {
          "id": "okr_alignment",
          "name": "OKR & Goal Alignment",
          "raw_score": 0.85,
          "weight": 0.25,
          "theory_basis": {
            "framework": "OKR",
            "reference": "Measure What Matters by John Doerr"
          }
        }
      ]
    },
    "confidence": {
      "overall_confidence": 0.87,
      "confidence_level": "high"
    },
    "recommendations": {
      "primary_recommendation": {
        "action": "Start budget review now using focused 90-minute work session",
        "rationale": "High urgency, strong goal alignment, adequate context match"
      }
    }
  },
  "metadata": {
    "version": "1.0.0",
    "execution_time": 0.275,
    "explanation_type": "task",
    "confidence_level": "high"
  }
}
```

## 🛠 Implementation Checklist

### For Backend Implementation
- [ ] Review complete protocol specification
- [ ] Implement JSON Schema validation
- [ ] Create factor calculation engines
- [ ] Add confidence metric computation
- [ ] Implement reasoning chain generation
- [ ] Test error scenarios and edge cases
- [ ] Validate performance requirements
- [ ] Ensure security and privacy compliance

### For Frontend Integration
- [ ] Parse explain response structure
- [ ] Display reasoning chain clearly
- [ ] Visualize factor contributions
- [ ] Show confidence indicators
- [ ] Present actionable recommendations
- [ ] Handle alternative options
- [ ] Display warning flags appropriately
- [ ] Implement graceful error handling

### For Testing
- [ ] Validate against JSON Schema
- [ ] Test backward compatibility
- [ ] Verify error code handling
- [ ] Check response size limits
- [ ] Test confidence calculation accuracy
- [ ] Validate factor scoring consistency
- [ ] Test alternative option generation

## 📚 Reference Documentation

- **[Complete Specification](./explain_protocol.md)**: Full protocol details
- **[Compatibility Analysis](./protocol_comparison.md)**: Integration with existing systems
- **[JSON Schema](../schemas/explain_schema.json)**: Validation schema
- **[Examples](../examples/explain/)**: Real-world response samples
- **[ADR-0004](../decisions/ADR-0004.md)**: Python version requirements

## 🔄 Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-01-15 | Initial protocol specification |

## 🤝 Contributing

When making changes to the protocol:

1. **Follow Semantic Versioning**: MAJOR.MINOR.PATCH
2. **Maintain Compatibility**: Avoid breaking changes when possible
3. **Update Examples**: Keep examples current with specification
4. **Validate Schema**: Ensure JSON Schema matches specification
5. **Document Changes**: Update this README and protocol docs

## ❓ Support

For questions about the Explain Protocol:

1. **Read the Docs**: Start with [explain_protocol.md](./explain_protocol.md)
2. **Check Examples**: Review `examples/explain/` directory
3. **Test Integration**: Use the provided JSON Schema
4. **Review Compatibility**: See [protocol_comparison.md](./protocol_comparison.md)

---

*Generated with Claude Code - PersonalManager Explain Protocol v1.0*