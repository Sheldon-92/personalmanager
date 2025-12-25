# Handoff Creation Task (交接文档创建任务)

## ⚠️ CRITICAL EXECUTION NOTICE ⚠️

**THIS IS THE BRIDGE BETWEEN AGENT A AND AGENT B**

When this task is invoked:

1. **MANDATORY COMPLETENESS CHECK** - Every section must be filled
2. **NO ASSUMPTIONS ALLOWED** - Blake needs explicit instructions
3. **CONTEXT IS EVERYTHING** - Blake won't load other documents
4. **VALIDATION REQUIRED** - User must confirm before sending to Blake

**VIOLATION INDICATOR:** If handoff is incomplete or ambiguous, Blake will reject it.

## Purpose

Create a comprehensive handoff document that gives Blake (Agent B) everything needed to implement Alex's (Agent A's) design. This document is the ONLY source Blake will use for implementation.

## Pre-requisites Check

Before creating handoff, verify:
- [ ] Requirements documented and confirmed (3-5 rounds completed)
- [ ] Design specifications created
- [ ] Technical approach defined
- [ ] Test criteria established

If any unchecked, STOP and complete them first.

## Mandatory Handoff Structure

### Document Template

```markdown
# Handoff Document for Agent B (Blake)

**From:** Alex (Agent A - Solution Lead)
**To:** Blake (Agent B - Execution Master)
**Date:** [Current Date]
**Project:** [Project Name]
**Task ID:** TASK-[YYYYMMDD]-[###]
**Handoff Version:** 1.0

## 1. Task Overview

### What We're Building
[Clear, concise description of what Blake needs to implement]

### Why We're Building It
[Business value and user benefit]

### Success Looks Like
[Concrete description of successful implementation]

## 2. Background Context

### Previous Work
[Any existing code or patterns to follow]
[Location of relevant files if any]

### Current State
[What exists now vs what needs to be built]

### Dependencies
[External libraries, APIs, services needed]

## 3. Requirements

### Functional Requirements
[[Copy from confirmed requirements document]]
- FR1: [Requirement]
- FR2: [Requirement]
...

### Non-Functional Requirements
- NFR1: [Requirement]
- NFR2: [Requirement]
...

## 4. Technical Design

### Architecture Overview
[High-level architecture - components and their relationships]

### Component Specifications

#### Component 1: [Name]
- **Purpose:** [What it does]
- **Location:** [Where to create it]
- **Interface:** [Public API/methods]
- **Implementation Notes:** [Specific guidance]

#### Component 2: [Name]
[Repeat for all components]

### Data Models
[Define all data structures, types, schemas]

### API Specifications
[Endpoints, request/response formats, error codes]

### User Interface Requirements
[If applicable - layouts, components, interactions]

## 5. Implementation Steps

### Step 1: [Setup/Initialization]
- [ ] Specific action 1
- [ ] Specific action 2
- **Verification:** [How to verify this step is complete]

### Step 2: [Core Implementation]
- [ ] Specific action 1
- [ ] Specific action 2
- **Verification:** [How to verify]

### Step 3: [Integration]
- [ ] Specific action 1
- [ ] Specific action 2
- **Verification:** [How to verify]

### Step 4: [Testing]
- [ ] Write unit tests for [components]
- [ ] Write integration tests for [flows]
- **Coverage Target:** [X]%

## 6. File Structure

### Files to Create
```
path/to/file1.ext  # Description of purpose
path/to/file2.ext  # Description of purpose
```

### Files to Modify
```
path/to/existing.ext  # What to change
```

## 7. Testing Requirements

### Unit Tests
- Test [Component 1]: [What to test]
- Test [Component 2]: [What to test]

### Integration Tests
- Test [Flow 1]: [Expected behavior]
- Test [Flow 2]: [Expected behavior]

### Edge Cases to Test
- [Edge case 1]
- [Edge case 2]

## 8. Acceptance Criteria

Blake's implementation is complete when:
- [ ] All functional requirements implemented
- [ ] All tests passing
- [ ] Code follows project standards
- [ ] Documentation updated
- [ ] No critical issues or warnings
- [ ] Performance meets requirements

## 9. Important Notes and Warnings

### Critical Considerations
- ⚠️ [Important warning 1]
- ⚠️ [Important warning 2]

### Known Constraints
- [Constraint 1]
- [Constraint 2]

### Future Considerations
[Things to keep in mind for future extensions]

## 10. Questions for Blake

If Blake encounters these scenarios:
- Scenario 1: [Guidance]
- Scenario 2: [Guidance]
- Ambiguous requirement: Return to Alex for clarification

## Handoff Validation Checklist

Before sending to Blake, confirm:
- [ ] All 10 sections complete
- [ ] No placeholders or TODOs
- [ ] Implementation steps are specific
- [ ] Test requirements clear
- [ ] File structure defined
- [ ] Acceptance criteria measurable

## Sign-off

**Alex confirms:** This handoff contains everything Blake needs for implementation.
**Date:** [Date]
**Status:** Ready for Blake
```

## Validation Process

### Step 1: Self-Check
Go through each section and verify:
- Completeness (no empty sections)
- Clarity (no ambiguous instructions)
- Specificity (concrete, actionable items)

### Step 2: User Review
Present to user:
```
Handoff document is ready for review.

Please select an option (0-8) or 9 to approve:
0. Review task overview section
1. Review requirements section
2. Review technical design
3. Review implementation steps
4. Add missing information
5. Clarify ambiguous points
6. Adjust acceptance criteria
7. Add warnings or notes
8. Request another review pass
9. Approve and send to Blake

Select 0-9:
```

### Step 3: Final Confirmation
```
⚠️ FINAL CONFIRMATION ⚠️

This handoff will be the ONLY document Blake uses for implementation.

Confirmed sections:
✅ Task Overview - Complete
✅ Background Context - Complete
✅ Requirements - Complete
✅ Technical Design - Complete
✅ Implementation Steps - Complete
✅ File Structure - Complete
✅ Testing Requirements - Complete
✅ Acceptance Criteria - Complete
✅ Notes and Warnings - Complete
✅ Questions Addressed - Complete

Ready to send to Blake? (Type 'CONFIRM' to proceed):
```

## Output

**File:** `.tad/docs/handoffs/handoff_[timestamp].md`

After confirmation, instruct user:
```
✅ Handoff document created successfully!

Next steps:
1. Save this handoff document
2. Switch to Terminal 2
3. Provide this handoff to Blake
4. Blake will verify completeness before starting

Important: Blake will ONLY use this handoff document for implementation.
Make sure you've included everything needed!
```

## CRITICAL REMINDERS

**❌ NEVER:**
- Leave sections empty or with placeholders
- Use vague language like "implement as needed"
- Assume Blake will figure things out
- Skip the validation process
- Send incomplete handoffs

**✅ ALWAYS:**
- Fill every section completely
- Be specific and concrete
- Include all context in this document
- Validate with user before sending
- Ensure Blake can work independently with this

## Violation Handling

If attempting to create incomplete handoff:
```
⚠️ VIOLATION DETECTED ⚠️
Type: Incomplete Handoff
Missing: [List of missing sections]
Action: Cannot proceed. Completing missing sections...
```

[[LLM: This is the MOST CRITICAL document in the TAD workflow. It's the only communication channel between Alex and Blake. It must be complete, clear, and self-contained.]]