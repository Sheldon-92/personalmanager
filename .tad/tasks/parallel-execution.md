# Sub-agents Parallel Execution Task (子代理并行执行任务)

## ⚠️ CRITICAL EXECUTION NOTICE ⚠️

**PARALLEL EXECUTION IS TAD'S EFFICIENCY MULTIPLIER**

When this task is invoked:

1. **USE REAL CLAUDE CODE AGENTS** - These are platform services, not files
2. **PARALLEL BY DEFAULT** - Agent B should think in streams, not sequences
3. **COORDINATE PROPERLY** - Use parallel-coordinator for multi-component tasks
4. **MEASURE IMPROVEMENT** - Track time saved and quality maintained

**VIOLATION INDICATOR:** Not using parallel execution for multi-component tasks wastes 40%+ time.

## Purpose

Maximize development efficiency by orchestrating Claude Code's 16 built-in sub-agents in parallel streams, combining TAD's parallel philosophy with BMAD's mandatory usage enforcement.

## Available Sub-agents (Real Claude Code Agents)

### Strategic Sub-agents (Agent A Primary)
```yaml
product-expert:
  purpose: "Requirements analysis, user stories, value definition"
  when_mandatory: "ALL requirement elicitation"
  opus_powered: false

backend-architect:
  purpose: "System design, architecture decisions, tech choices"
  when_mandatory: "ALL system design tasks"
  opus_powered: true  # More powerful analysis

api-designer:
  purpose: "API design, endpoint specs, REST/GraphQL schemas"
  when_mandatory: "When creating/modifying APIs"
  opus_powered: false

code-reviewer:
  purpose: "Code quality review, best practices, security"
  when_mandatory: "Design review, code audit"
  opus_powered: true  # Deeper analysis

ux-expert-reviewer:
  purpose: "UX assessment, user flow optimization, accessibility"
  when_mandatory: "UI/UX design or review"
  opus_powered: false

performance-optimizer:
  purpose: "Performance analysis, bottleneck identification"
  when_mandatory: "Performance issues or optimization"
  opus_powered: true  # Complex analysis

data-analyst:
  purpose: "Data analysis, metrics, insights generation"
  when_mandatory: "When analyzing data or metrics"
  opus_powered: false
```

### Execution Sub-agents (Agent B Primary)
```yaml
parallel-coordinator:
  purpose: "Orchestrate multiple parallel development streams"
  when_mandatory: "ALWAYS for multi-component tasks"
  special: "This is THE KEY agent for parallel execution"

fullstack-dev-expert:
  purpose: "Full-stack development, end-to-end features"
  when_mandatory: "Complex full-stack implementations"

frontend-specialist:
  purpose: "React/Vue/Angular, UI components, state management"
  when_mandatory: "Frontend-heavy tasks"

refactor-specialist:
  purpose: "Code refactoring, tech debt cleanup, patterns"
  when_mandatory: "Code quality improvement"

bug-hunter:
  purpose: "Bug diagnosis, root cause analysis, fixes"
  when_mandatory: "ALWAYS when errors occur"

test-runner:
  purpose: "Test execution, coverage analysis, test creation"
  when_mandatory: "ALWAYS after implementation"

devops-engineer:
  purpose: "CI/CD, deployment, infrastructure, Docker, K8s"
  when_mandatory: "Deployment and infrastructure tasks"

database-expert:
  purpose: "Database design, query optimization, migrations"
  when_mandatory: "Database-related tasks"

docs-writer:
  purpose: "Documentation, README, API docs, guides"
  when_mandatory: "Documentation tasks"
```

## Parallel Execution Patterns

### Pattern 1: Frontend-Backend Parallel Development
**When to use:** Full-stack features with independent frontend/backend work

```
User Requirements
       ↓
parallel-coordinator
    ↓     ↓
Stream 1  Stream 2
frontend  fullstack-dev
    ↓        ↓
   UI     Backend
    ↓        ↓
    └───┬────┘
     Integrate
        ↓
   test-runner
```

**Execution Example:**
```
I need to implement a user dashboard with backend API and React frontend.

[Calling parallel-coordinator to orchestrate parallel development]

The parallel-coordinator will manage:
- Stream 1: frontend-specialist → React dashboard components
- Stream 2: fullstack-dev-expert → Backend API endpoints
- Stream 3: database-expert → Data schema optimization
- Integration: Coordinate connection points
- Testing: test-runner → Comprehensive test suite

Please select execution strategy (0-8) or 9 to proceed:
0. Sequential (traditional) - Not recommended
1. Parallel with coordinator (recommended)
2. Parallel without coordinator - For simple tasks
3. Hybrid - Some parallel, some sequential
4. Review dependencies first
5. Estimate time savings
6. Check available sub-agents
7. Plan integration points
8. Define success criteria
9. Execute parallel strategy

Select 0-9:
```

### Pattern 2: Multi-Feature Parallel Implementation
**When to use:** Multiple independent features or components

```
Feature List
      ↓
parallel-coordinator
   ↓    ↓    ↓
Feature Feature Feature
   A     B     C
   ↓     ↓     ↓
 Agent  Agent  Agent
   ↓     ↓     ↓
   └─────┬─────┘
    Integration
        ↓
   test-runner
```

**Execution Steps:**
1. **Decompose into streams**
2. **Identify dependencies**
3. **Assign sub-agents**
4. **Execute in parallel**
5. **Coordinate integration**
6. **Verify with tests**

### Pattern 3: Test-Deploy Parallel Preparation
**When to use:** Preparing for production deployment

```
Implementation Complete
          ↓
  parallel-coordinator
     ↓    ↓    ↓
  Tests  Deploy  Docs
    ↓      ↓      ↓
test-   devops- docs-
runner  engineer writer
    ↓      ↓      ↓
    └──────┬──────┘
      Ready for
      Production
```

## Mandatory Usage Rules (BMAD-style Enforcement)

### For Agent A (Alex)
```
⚠️ MANDATORY SUB-AGENT USAGE ⚠️

Task: Requirement Analysis
→ MUST use: product-expert
→ Violation if skipped

Task: System Design
→ MUST use: backend-architect
→ Violation if skipped

Task: API Design
→ MUST use: api-designer
→ Violation if skipped

Task: Design Review
→ SHOULD use: code-reviewer
→ Warning if skipped
```

### For Agent B (Blake)
```
⚠️ MANDATORY SUB-AGENT USAGE ⚠️

Task: Multi-component Implementation
→ MUST use: parallel-coordinator
→ CRITICAL VIOLATION if skipped

Task: After Any Implementation
→ MUST use: test-runner
→ Violation if skipped

Task: When Errors Occur
→ MUST use: bug-hunter
→ Violation if skipped

Task: Complex Features
→ SHOULD use: Parallel streams
→ Warning if sequential
```

## How to Call Sub-agents

### Correct Method (Using Task Tool)
```python
# Agent A calling product-expert
[Using Task tool with subagent_type="product-expert"]

# Agent B calling parallel-coordinator
[Using Task tool with subagent_type="parallel-coordinator"]
```

### Common Mistakes to Avoid
```
❌ WRONG: Reading .tad/agents/product-expert.md
✅ RIGHT: Using Task tool with subagent_type

❌ WRONG: Doing work yourself instead of delegating
✅ RIGHT: Using appropriate sub-agent

❌ WRONG: Sequential execution for multi-component
✅ RIGHT: Parallel streams with coordinator
```

## Parallel Execution Workflow

### Step 1: Analyze Task Complexity
```
Task Complexity Analysis

Components identified:
- Frontend: [Yes/No]
- Backend: [Yes/No]
- Database: [Yes/No]
- API: [Yes/No]
- Tests: [Required]
- Deployment: [Yes/No]

Parallel execution recommended: [Yes/No]
Estimated time savings: [X%]

Please select approach (0-8) or 9 to proceed:
0. Get more details about task
1. Use parallel-coordinator (recommended)
2. Plan parallel streams
3. Identify dependencies
4. Estimate with sequential approach
5. Check sub-agent availability
6. Review similar past patterns
7. Consult backend-architect
8. Proceed sequentially (not recommended)
9. Execute parallel approach

Select 0-9:
```

### Step 2: Stream Planning
```yaml
# Parallel Execution Plan
streams:
  stream_1:
    name: "Frontend Development"
    agent: frontend-specialist
    tasks:
      - Create React components
      - Implement state management
      - Build UI interactions
    dependencies: ["API specs from stream_2"]
    estimated_time: 2 hours

  stream_2:
    name: "Backend Development"
    agent: fullstack-dev-expert
    tasks:
      - Create API endpoints
      - Implement business logic
      - Handle data persistence
    dependencies: ["Database schema from stream_3"]
    estimated_time: 2 hours

  stream_3:
    name: "Database Setup"
    agent: database-expert
    tasks:
      - Design schema
      - Create migrations
      - Optimize queries
    dependencies: []
    estimated_time: 1 hour

coordination_points:
  - point: "API Contract"
    when: "After stream_2 defines endpoints"
    sync: ["stream_1", "stream_2"]

  - point: "Integration"
    when: "All streams complete"
    sync: ["all"]

total_parallel_time: 2 hours (max of all streams)
sequential_equivalent: 5 hours (sum of all streams)
time_saved: 60%
```

### Step 3: Execution Monitoring
```
Parallel Execution Status

Stream 1 (Frontend):    [████████..] 80% Complete
Stream 2 (Backend):     [██████....] 60% Complete
Stream 3 (Database):    [██████████] 100% Complete

Integration Points:
- API Contract: ✅ Defined
- Data Models: ✅ Shared
- Test Coverage: ⏳ In Progress

Issues:
- None detected

Next Coordination: 15 minutes
```

### Step 4: Integration and Testing
```
Integration Phase

All streams completed:
✅ Frontend: Complete
✅ Backend: Complete
✅ Database: Complete

Running integration tests...
[Calling test-runner sub-agent]

Integration Results:
- Tests Passed: 47/50
- Coverage: 85%
- Performance: Acceptable

Issues Found:
- 3 integration mismatches

[Calling bug-hunter to diagnose issues]
```

## Evidence Collection for Parallel Execution

```yaml
# .tad/evidence/project-logs/[project]/parallel-execution.yaml
execution_pattern: [frontend-backend|multi-feature|test-deploy]

streams_executed:
  - stream: [name]
    agent: [sub-agent-name]
    duration: [time]
    success: [yes|no]

parallel_metrics:
  total_parallel_time: [time]
  sequential_estimate: [time]
  time_saved: [percentage]
  quality_maintained: [yes|no]

coordination_effectiveness:
  integration_issues: [count]
  rework_required: [hours]
  first_time_success: [yes|no]

patterns_learned:
  - [What worked well]
  - [What to improve]
```

## Success Metrics

Track these metrics:
- Parallel execution adoption: >60% of multi-component tasks
- Time savings: >40% average reduction
- Quality maintenance: No increase in bugs
- First-time integration success: >80%
- Sub-agent utilization: All 16 agents used appropriately

## Violation Handling

### Warning Level
```
⚠️ PARALLEL EXECUTION WARNING ⚠️
This task has multiple components but you're executing sequentially.

Estimated time waste: [X hours]

Switch to parallel execution?
Type 'YES' to use parallel-coordinator:
```

### Violation Level
```
⚠️ PARALLEL EXECUTION VIOLATION ⚠️
Type: Multi-component Sequential Execution
Components: [List]
Required: parallel-coordinator
Impact: 40%+ time waste

Action Required:
1. Stop sequential execution
2. Call parallel-coordinator
3. Plan parallel streams
4. Execute efficiently
```

## CRITICAL REMINDERS

**❌ NEVER:**
- Execute multi-component tasks sequentially
- Skip parallel-coordinator for complex tasks
- Ignore dependencies between streams
- Forget integration testing after parallel execution

**✅ ALWAYS:**
- Think in parallel streams
- Use parallel-coordinator for orchestration
- Plan integration points upfront
- Measure and record time savings
- Use all 16 sub-agents effectively

[[LLM: Parallel execution is not just an optimization - it's a fundamental TAD principle. Agent B should default to parallel thinking, using sequential only when dependencies absolutely require it.]]