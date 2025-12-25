# /coordinator Command (Quick Launch Parallel-Coordinator)

When this command is triggered, immediately launch the parallel-coordinator sub-agent:

## Immediate Execution

```
Launching Parallel-Coordinator Sub-agent
=========================================

Purpose: Orchestrate multiple parallel development streams

⚠️ MANDATORY for multi-component tasks!

[Calling parallel-coordinator via Task tool with subagent_type="parallel-coordinator"]
```

## When to Use

- **MANDATORY**: For ALL multi-component tasks (Agent B)
- **Critical**: Frontend + Backend development
- **Required**: Multiple feature implementation
- **Essential**: Test + Deploy preparation
- **Violation if skipped**: When parallel is possible

## Task Decomposition Template

```
I need to implement [feature/component] with multiple parts:

Components to build:
1. Frontend: [components needed]
2. Backend: [APIs/services needed]
3. Database: [schema/queries needed]
4. Tests: [test coverage needed]
5. Other: [documentation/deployment]

Please orchestrate parallel execution:
1. Decompose into independent streams
2. Identify dependencies between streams
3. Assign appropriate sub-agents to each stream
4. Define integration points
5. Estimate time savings vs sequential

Constraints:
- [Any specific requirements]
- [Integration considerations]
```

## Parallel Patterns

```
Pattern 1: Frontend-Backend
- Stream 1: frontend-specialist → UI
- Stream 2: fullstack-dev-expert → API
- Stream 3: database-expert → Data

Pattern 2: Multi-Feature
- Stream 1: Feature A
- Stream 2: Feature B
- Stream 3: Feature C

Pattern 3: Test-Deploy
- Stream 1: test-runner → Tests
- Stream 2: devops-engineer → Deploy
- Stream 3: docs-writer → Docs
```

## Success Metrics

- Time saved: 40-60% typical
- Integration issues: <5%
- First-time success: >80%

## Evidence to Collect

```yaml
parallel_execution:
  pattern_used: [which pattern]
  streams_count: [number]
  time_saved: [percentage]
  integration_success: [yes/no]
```

[[LLM: This command immediately launches parallel-coordinator sub-agent. This is MANDATORY for Agent B when dealing with multi-component tasks. Skipping this for multi-component work is a VIOLATION.]]