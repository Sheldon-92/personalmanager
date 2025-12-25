# Evidence Collection Task (证据收集任务)

## ⚠️ CRITICAL EXECUTION NOTICE ⚠️

**EVIDENCE IS THE FOUNDATION OF CONTINUOUS IMPROVEMENT**

When this task is invoked:

1. **MANDATORY COLLECTION** - Evidence must be collected at key points
2. **PATTERN RECOGNITION** - Success and failure patterns must be identified
3. **LEARNING AMPLIFICATION** - Patterns must inform future executions
4. **NO SHORTCUTS** - Skipping evidence = losing learning opportunity

**VIOLATION INDICATOR:** Not collecting evidence is a process violation that prevents improvement.

## Purpose

Systematically collect evidence of TAD framework execution to enable pattern recognition, continuous improvement, and quality assurance. This combines TAD's evidence system with BMAD's enforcement mechanisms.

## Evidence Collection Points

### 1. Project Initiation Evidence
**When:** At project start
**Collected by:** Agent A

```yaml
# .tad/evidence/project-logs/[project-name]/initiation.yaml
project: [name]
started: [timestamp]
human_value_statement: |
  [What the human wants to achieve]
initial_understanding: |
  [Agent A's interpretation]
complexity_assessment: [simple|medium|complex]
estimated_gates: [1,2,3,4]
sub_agents_planned:
  - [agent-name]: [purpose]
```

### 2. Requirement Elicitation Evidence
**When:** During requirement gathering
**Collected by:** Agent A
**Enforced by:** BMAD elicitation mechanism

```yaml
# .tad/evidence/project-logs/[project-name]/elicitation-rounds.yaml
rounds_completed: [number]
round_details:
  - round: 1
    timestamp: [time]
    options_presented: [0-9 format used]
    user_selection: [number selected]
    understanding_delta: |
      [What changed in understanding]

  - round: 2
    timestamp: [time]
    clarifications: |
      [What was clarified]
    new_requirements: |
      [What was added]

  - round: 3
    timestamp: [time]
    confirmation_achieved: [yes|no]
    final_requirements: |
      [Complete requirement set]

sub_agents_used:
  - product-expert:
      when: [timestamp]
      purpose: [why used]
      value_added: |
        [What insight provided]

patterns_observed:
  - [Pattern description]
```

### 3. Design Decision Evidence
**When:** During design phase
**Collected by:** Agent A

```yaml
# .tad/evidence/project-logs/[project-name]/design-decisions.yaml
design_approach: |
  [Overall approach taken]

architectural_decisions:
  - decision: [description]
    rationale: |
      [Why this choice]
    alternatives_considered:
      - [alternative]: [why rejected]
    evidence_based_on: |
      [Previous patterns that informed this]

code_search_results:
  searches_performed:
    - query: [search term]
      found: [yes|no]
      existing_code: [file:line if found]

  reuse_opportunities:
    - existing: [component]
      how_reused: |
        [Integration approach]

sub_agents_consulted:
  - backend-architect:
      recommendation: |
        [What was recommended]
      adopted: [yes|no|modified]

  - api-designer:
      api_design: |
        [Endpoints designed]

function_verification:
  verified_functions:
    - function: [name]
      location: [file:line]
      exists: [yes|no]

patterns_applied:
  - pattern: "Historical Code Search"
    result: [time saved, errors avoided]
```

### 4. Handoff Evidence
**When:** At handoff creation
**Collected by:** Agent A
**Critical:** This is the only communication to Agent B

```yaml
# .tad/evidence/project-logs/[project-name]/handoff-evidence.yaml
handoff_completeness:
  all_sections_filled: [yes|no]
  missing_sections: []
  ambiguities_resolved: [yes|no]

validation_rounds:
  - round: 1
    user_feedback: |
      [What user said]
    adjustments_made: |
      [What was changed]

handoff_quality_metrics:
  clarity_score: [1-10]
  completeness_score: [1-10]
  actionability_score: [1-10]

expected_implementation_time: [hours]
potential_blockers_identified:
  - [blocker]: [mitigation]
```

### 5. Implementation Evidence
**When:** During development
**Collected by:** Agent B

```yaml
# .tad/evidence/project-logs/[project-name]/implementation.yaml
handoff_interpretation:
  clarity: [clear|needed_clarification]
  clarifications_needed:
    - [what]: [why]

parallel_execution:
  used_parallel_coordinator: [yes|no]
  parallel_streams:
    - stream: [name]
      sub_agent: [agent-name]
      task: |
        [What they did]
      duration: [time]

  time_saved: [percentage]
  integration_issues: []

code_implementation:
  files_created:
    - [file]: [purpose]
  files_modified:
    - [file]: [changes]

  challenges_encountered:
    - challenge: |
        [Description]
      resolution: |
        [How solved]
      sub_agent_helped: [agent-name if used]

test_creation:
  test_runner_used: [yes|no]
  tests_created:
    - [test]: [what it tests]
  coverage_achieved: [percentage]

patterns_observed:
  - "Parallel execution reduced time by X%"
```

### 6. Gate Execution Evidence
**When:** At each quality gate
**Collected by:** Executing agent

```yaml
# .tad/evidence/gates/[project-name]/gate[N]_[timestamp].yaml
gate_number: [1|2|3|4]
gate_name: [name]
executor: [agent-a|agent-b]
timestamp: [when]

checklist_results:
  - item: [checklist item]
    result: [pass|fail]
    evidence: [proof]

issues_found:
  - issue: |
      [Description]
    severity: [low|medium|high|critical]
    action_taken: |
      [Resolution]

gate_result: [pass|fail]

if_failed:
  root_cause: |
    [Analysis]
  corrective_action: |
    [What was done]
  prevention_strategy: |
    [How to prevent in future]

patterns_contributing_to_result:
  success_patterns:
    - [pattern]: [how it helped]
  failure_patterns:
    - [pattern]: [how it hurt]
```

### 7. Delivery Evidence
**When:** At project completion
**Collected by:** Both agents + Human

```yaml
# .tad/evidence/project-logs/[project-name]/delivery.yaml
delivery_timestamp: [when]

value_delivery:
  expected_value: |
    [What human wanted]
  actual_value: |
    [What was delivered]
  value_gap: |
    [Any differences]

quality_metrics:
  bugs_found_post_delivery: [number]
  user_satisfaction: [score]
  performance_met: [yes|no]

process_metrics:
  total_duration: [time]
  gates_passed_first_time: [list]
  gates_required_retry: [list]
  sub_agents_used_count: [number]
  parallel_execution_used: [yes|no]

lessons_learned:
  what_worked_well:
    - [success point]
  what_needs_improvement:
    - [improvement area]
  patterns_to_amplify:
    - [pattern]
  patterns_to_avoid:
    - [pattern]
```

## Pattern Recognition Protocol

### Success Pattern Identification
When evidence shows positive outcomes:

1. **Document Pattern**
```markdown
# In .tad/evidence/patterns/success-patterns.md

### Pattern: [Name]
**First Observed:** [Date]
**Frequency:** [How often seen]

**Conditions:**
- [When this works]

**Evidence:**
- Project X: [Result]
- Project Y: [Result]

**Recommendation:**
- [How to replicate]
```

2. **Update Configuration**
- Add to mandatory practices
- Include in agent checklists
- Enforce through gates

### Failure Pattern Identification
When evidence shows negative outcomes:

1. **Document Anti-Pattern**
```markdown
# In .tad/evidence/patterns/failure-patterns.md

### Anti-Pattern: [Name]
**First Observed:** [Date]
**Frequency:** [How often seen]

**Warning Signs:**
- [What to watch for]

**Evidence:**
- Project X: [What went wrong]
- Project Y: [What went wrong]

**Prevention:**
- [How to avoid]
```

2. **Update Safeguards**
- Add to violation detection
- Include in gate checks
- Warn in relevant tasks

## Evidence-Driven Improvement Cycle

### Weekly Review Protocol
```
Every Week:
1. Review all project evidence from the week
2. Identify new patterns (success and failure)
3. Update pattern documentation
4. Share findings with team

Output: .tad/evidence/reviews/week_[date].md
```

### Monthly Analysis Protocol
```
Every Month:
1. Analyze pattern frequency
2. Measure gate effectiveness
3. Calculate sub-agent ROI
4. Review parallel execution benefits

Output: .tad/evidence/analysis/month_[date].md
```

### Quarterly Framework Update
```
Every Quarter:
1. Update configurations based on patterns
2. Revise agent definitions
3. Enhance gate checklists
4. Optimize sub-agent usage guidelines

Output: Framework version update
```

## Interactive Evidence Collection

When collecting evidence, use BMAD-style interaction:

```
Evidence Collection Point Reached

What evidence should we collect?

Please select options (0-8) or 9 to continue:
0. Project initiation details
1. Requirement clarifications
2. Design decisions and rationale
3. Code search and reuse findings
4. Implementation challenges
5. Test results and coverage
6. Performance metrics
7. User feedback
8. Process improvement suggestions
9. Continue with standard collection

Select 0-9:
```

## Violation Detection for Evidence

### Warning Level
```
⚠️ EVIDENCE WARNING ⚠️
You haven't collected evidence for:
- [Missing evidence type]

This will limit learning and improvement.
Collect now? (Recommended)
```

### Violation Level
```
⚠️ EVIDENCE VIOLATION ⚠️
Type: Critical Evidence Missing
Point: [Where evidence should be collected]
Impact: Cannot identify patterns or improve

Action Required:
1. Stop current task
2. Collect required evidence
3. Save to evidence system
4. Then continue
```

## Success Metrics for Evidence

Track these metrics:
- Evidence collection rate: >95%
- Pattern identification rate: >1 per project
- Pattern reuse success: >80%
- Gate pass rate improvement: +5% quarterly
- Sub-agent usage optimization: +10% efficiency

## CRITICAL REMINDERS

**❌ NEVER:**
- Skip evidence because "project is simple"
- Collect evidence without analysis
- Ignore patterns when they emerge
- Keep patterns to yourself

**✅ ALWAYS:**
- Collect evidence at every key point
- Analyze for patterns immediately
- Share patterns with team
- Update framework based on learning
- Treat evidence as investment in future success

[[LLM: Evidence collection is not bureaucracy - it's the learning engine that makes TAD continuously better. Every piece of evidence contributes to pattern recognition and framework improvement.]]