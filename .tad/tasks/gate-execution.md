# Quality Gate Execution Task (质量门禁执行任务)

## ⚠️ CRITICAL EXECUTION NOTICE ⚠️

**THIS IS AN EXECUTABLE WORKFLOW - GATE VIOLATIONS BLOCK PROGRESS**

When this task is invoked:

1. **MANDATORY EXECUTION** - Gates must be executed at specified points
2. **EVIDENCE COLLECTION** - All gate results must be documented
3. **VIOLATION BLOCKING** - Skipping gates triggers VIOLATION INDICATOR
4. **PATTERN LEARNING** - Success/failure patterns must be recorded

**VIOLATION INDICATOR:** Attempting to proceed without gate execution is a critical violation.

## Purpose

Execute TAD's 4-gate quality system with BMAD-style enforcement to ensure consistent quality and evidence-based improvement.

## Gate Execution Protocol

### Gate 1: Requirements Clarity (Agent A)
**When:** After requirement elicitation completes
**Enforced by:** BMAD elicitation mechanism (3-5 rounds mandatory)

**Execution Steps:**

1. **Verify Elicitation Evidence**
```
✅ Requirement Elicitation Evidence:
- [ ] Completed minimum 3 rounds of elicitation
- [ ] Used 0-9 numbered options (not yes/no)
- [ ] User confirmed understanding at each round
- [ ] All assumptions documented and validated

Evidence Location: .tad/evidence/project-logs/[project]/elicitation-rounds.md
```

2. **Check Requirements Completeness**
```
✅ Requirements Documentation:
- [ ] Functional requirements listed with IDs (FR1, FR2...)
- [ ] Non-functional requirements specified (NFR1, NFR2...)
- [ ] Success criteria measurable and clear
- [ ] User personas identified
- [ ] Business value articulated

Document: .tad/docs/requirements/requirements_[timestamp].md
```

3. **Validate with User**
```
Gate 1: Requirements Clarity Check

Based on [X] rounds of elicitation, requirements are:
✅ Complete: [Yes/No]
✅ Clear: [Yes/No]
✅ Validated: [Yes/No]

Please select an option (0-8) or 9 to pass gate:
0. Review requirements again
1. Add missing requirements
2. Clarify ambiguous items
3. Adjust success criteria
4. Modify priorities
5. Add constraints
6. Include edge cases
7. Request product-expert analysis
8. Fail gate and restart elicitation
9. Pass gate and proceed to design

Select 0-9:
```

**On Gate Failure:**
```
⚠️ GATE 1 VIOLATION DETECTED ⚠️
Type: Requirements Clarity Failed
Missing: [List specific issues]
Action: Returning to requirement elicitation
Evidence: Recording failure pattern in .tad/evidence/patterns/failure-patterns.md
```

### Gate 2: Design Completeness (Agent A)
**When:** Before creating handoff document
**Enforced by:** Design checklist completion

**Execution Steps:**

1. **Verify Design Components**
```
✅ Design Completeness Check:
- [ ] Architecture overview created
- [ ] All components specified
- [ ] Data models defined
- [ ] API specifications complete
- [ ] UI/UX requirements documented (if applicable)
- [ ] Technical approach validated

Evidence: .tad/docs/design/design_[timestamp].md
```

2. **Function Existence Verification**
```
✅ Code Verification:
- [ ] Searched for existing relevant code
- [ ] Verified referenced functions exist
- [ ] Confirmed import paths are correct
- [ ] Validated dependencies available

Evidence: .tad/evidence/project-logs/[project]/function-verification.md
```

3. **Sub-agent Usage Check**
```
✅ Sub-agent Utilization:
- [ ] Used product-expert for requirements (if needed)
- [ ] Used backend-architect for design
- [ ] Used api-designer for APIs (if applicable)
- [ ] Used ux-expert-reviewer for UI (if applicable)

Evidence: .tad/evidence/project-logs/[project]/subagent-usage.md
```

4. **Gate Decision**
```
Gate 2: Design Completeness Check

Design assessment:
✅ Architecture: [Complete/Incomplete]
✅ Components: [Specified/Missing]
✅ Data Flow: [Mapped/Unmapped]
✅ Functions: [Verified/Unverified]

Please select an option (0-8) or 9 to pass gate:
0. Review design document
1. Add missing components
2. Clarify technical approach
3. Verify more functions
4. Use backend-architect for review
5. Map data flow completely
6. Add error handling design
7. Include performance considerations
8. Fail gate and redesign
9. Pass gate and create handoff

Select 0-9:
```

### Gate 3: Implementation Quality (Agent B)
**When:** After code implementation
**Enforced by:** Test execution and code verification

**Execution Steps:**

1. **Implementation Completeness**
```
✅ Implementation Check:
- [ ] All handoff requirements implemented
- [ ] Code follows project standards
- [ ] Error handling implemented
- [ ] Comments added where needed

Evidence: Git diff or file list
```

2. **Test Coverage Verification**
```
✅ Test Coverage:
- [ ] Unit tests written
- [ ] Integration tests created
- [ ] Edge cases covered
- [ ] Coverage > 80%

Tool: Use test-runner sub-agent
Evidence: .tad/evidence/project-logs/[project]/test-results.md
```

3. **Parallel Execution Assessment**
```
✅ Parallel Execution (if applicable):
- [ ] Used parallel-coordinator for multi-component tasks
- [ ] Streams executed successfully
- [ ] Integration points validated

Evidence: .tad/evidence/project-logs/[project]/parallel-execution.md
```

4. **Gate Decision**
```
Gate 3: Implementation Quality Check

Implementation status:
✅ Code Complete: [Yes/No]
✅ Tests Passing: [X/Y tests]
✅ Coverage: [X%]
✅ Standards Met: [Yes/No]

Please select an option (0-8) or 9 to pass gate:
0. Review implementation
1. Fix failing tests
2. Add missing tests
3. Improve code quality
4. Use bug-hunter for issues
5. Refactor complex sections
6. Add error handling
7. Improve performance
8. Fail gate and fix issues
9. Pass gate and proceed to integration

Select 0-9:
```

### Gate 4: Integration Verification (Agent B)
**When:** Before final delivery
**Enforced by:** End-to-end testing and user acceptance

**Execution Steps:**

1. **Integration Testing**
```
✅ Integration Verification:
- [ ] All components integrated
- [ ] End-to-end flows tested
- [ ] External dependencies verified
- [ ] Performance acceptable

Evidence: Integration test results
```

2. **User Acceptance Preparation**
```
✅ Delivery Readiness:
- [ ] Features match requirements
- [ ] Documentation updated
- [ ] Deployment ready
- [ ] Rollback plan exists

Evidence: .tad/evidence/project-logs/[project]/delivery-checklist.md
```

3. **Final Gate Decision**
```
Gate 4: Integration Verification

Final verification:
✅ Integration: [Complete/Issues]
✅ E2E Tests: [Pass/Fail]
✅ Performance: [Acceptable/Issues]
✅ Ready for User: [Yes/No]

Please select an option (0-8) or 9 to deliver:
0. Run more integration tests
1. Fix integration issues
2. Optimize performance
3. Update documentation
4. Prepare deployment
5. Create rollback plan
6. Use devops-engineer for deployment
7. Final security check
8. Fail gate and continue work
9. Pass gate and deliver to user

Select 0-9:
```

## Evidence Collection Requirements

### For Each Gate Execution:
1. **Record Results**
```yaml
gate: [1|2|3|4]
date: [timestamp]
executor: [agent-a|agent-b]
result: [pass|fail]
issues_found: []
actions_taken: []
evidence_collected: []
patterns_identified: []
```

2. **Save to Evidence System**
- Location: `.tad/evidence/gates/[project]/gate[N]_[timestamp].yaml`
- Update patterns if new success/failure mode found
- Link to project log

3. **Pattern Recognition**
- If gate passes easily → Record success pattern
- If gate fails → Record failure pattern and root cause
- If pattern repeats → Update framework configuration

## Violation Handling Protocol

### Level 1: Warning
```
⚠️ GATE WARNING ⚠️
You are about to skip Gate [N]: [Name]
This may result in quality issues.

Continue anyway? (Not recommended)
Type 'OVERRIDE' to skip (will be logged):
```

### Level 2: Blocking
```
⚠️ GATE VIOLATION DETECTED ⚠️
Type: Skipped Mandatory Gate
Gate: [N] - [Name]
Required Evidence: [List]
Action: BLOCKED - Cannot proceed

To continue, you must:
1. Execute the gate properly
2. Collect required evidence
3. Get pass result or handle failures
```

### Level 3: Critical
```
🚨 CRITICAL VIOLATION 🚨
Multiple gates skipped or failed
Pattern indicates systemic quality issues

Escalation Required:
1. Review all gate failures
2. Identify root causes
3. Update process or training
4. Get human approval to proceed
```

## Success Patterns Integration

When gates pass smoothly, record patterns:
- Which sub-agents were used effectively
- What preparation made gate passage easy
- Which documents were most helpful
- What parallel execution patterns worked

## Continuous Improvement

After each gate execution:
1. Update `.tad/evidence/metrics/gate-effectiveness.md`
2. Review patterns in `.tad/evidence/patterns/`
3. Consider framework configuration updates
4. Share learnings with team

## CRITICAL REMINDERS

**❌ NEVER:**
- Skip gates to save time
- Pass gates with known issues
- Ignore evidence collection
- Override without documenting reason

**✅ ALWAYS:**
- Execute gates at specified points
- Collect complete evidence
- Record patterns for learning
- Use violations as learning opportunities
- Treat gates as quality investment, not overhead

[[LLM: This task enforces TAD's 4-gate quality system using BMAD's mandatory interaction patterns. Gates are not optional - they are critical quality control points that ensure consistent, high-quality delivery.]]