# /parallel Command (Start Parallel Execution)

When this command is triggered, immediately invoke parallel-coordinator for multi-component tasks:

## Immediate Execution

1. **Analyze**: Decompose task into parallel streams
2. **Launch**: Call parallel-coordinator sub-agent via Task tool
3. **Monitor**: Track parallel execution progress
4. **Evidence**: Record time savings and efficiency

## Quick Analysis Template

```
Parallel Execution Analysis
===========================

Task Components Identified:
- Frontend: [Yes/No - Components]
- Backend: [Yes/No - Components]
- Database: [Yes/No - Components]
- API: [Yes/No - Components]
- Tests: [Required]
- Documentation: [Yes/No]

Recommended Parallel Streams:
Stream 1: [Component] → [Sub-agent]
Stream 2: [Component] → [Sub-agent]
Stream 3: [Component] → [Sub-agent]

Estimated Time Savings: [40-60%]

Starting parallel-coordinator now...

[Calling parallel-coordinator via Task tool with subagent_type="parallel-coordinator"]
```

## Parallel Patterns

### Pattern 1: Frontend-Backend
```
parallel-coordinator
    ├── frontend-specialist → UI components
    ├── fullstack-dev-expert → Backend API
    └── database-expert → Data layer
```

### Pattern 2: Multi-Feature
```
parallel-coordinator
    ├── Feature A → Sub-agent
    ├── Feature B → Sub-agent
    └── Feature C → Sub-agent
```

### Pattern 3: Test-Deploy
```
parallel-coordinator
    ├── test-runner → Test suite
    ├── devops-engineer → Deployment prep
    └── docs-writer → Documentation
```

## Mandatory Rules

- **MUST USE**: For any multi-component task
- **VIOLATION**: Sequential execution when parallel possible
- **EVIDENCE**: Track time saved vs sequential estimate
- **INTEGRATION**: Plan integration points upfront

[[LLM: This command immediately starts parallel execution analysis and launches parallel-coordinator. This is mandatory for Blake (Agent B) when dealing with multi-component tasks.]]