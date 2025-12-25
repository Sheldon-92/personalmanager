# /handoff Command (Create or Verify Handoff Document)

When this command is triggered, create (Alex) or verify (Blake) the critical handoff document:

## For Agent A (Alex) - Create Handoff

```
Creating Handoff Document for Blake
====================================

This is Blake's ONLY source of information for implementation.

Generating comprehensive handoff with 10 mandatory sections:

1. Task Overview
2. Background Context
3. Requirements
4. Technical Design
5. Implementation Steps
6. File Structure
7. Testing Requirements
8. Acceptance Criteria
9. Important Notes and Warnings
10. Questions for Blake

[Loading template from .tad/tasks/handoff-creation.md]
```

### Handoff Creation Checklist
```
✅ Mandatory Sections Check:
- [ ] Task overview complete
- [ ] Requirements copied from confirmed docs
- [ ] Design specifications included
- [ ] Implementation steps specific and numbered
- [ ] File structure clearly defined
- [ ] Test requirements explicit
- [ ] Acceptance criteria measurable
- [ ] No TODOs or placeholders
- [ ] Function existence verified
- [ ] All ambiguities resolved

Ready for Blake? (All must be checked)
```

## For Agent B (Blake) - Verify Handoff

```
Verifying Handoff Document from Alex
=====================================

Checking handoff completeness...

✅ Section Check:
- [ ] Task Overview: [Present/Missing]
- [ ] Background Context: [Present/Missing]
- [ ] Requirements: [Clear/Ambiguous]
- [ ] Technical Design: [Complete/Incomplete]
- [ ] Implementation Steps: [Actionable/Vague]
- [ ] File Structure: [Defined/Missing]
- [ ] Testing Requirements: [Clear/Missing]
- [ ] Acceptance Criteria: [Measurable/Vague]
- [ ] Notes and Warnings: [Helpful/Missing]
- [ ] Questions Addressed: [Yes/No]

Handoff Status: [Ready/Needs Clarification]
```

### If Handoff Incomplete

```
⚠️ HANDOFF VIOLATION DETECTED ⚠️

Missing/Unclear Sections:
- [Section]: [Issue]
- [Section]: [Issue]

Cannot proceed with implementation.

Please select action (0-8) or 9 if complete:
0. Request specific clarification
1. Ask about missing requirements
2. Clarify technical approach
3. Request implementation steps
4. Ask about testing requirements
5. Clarify acceptance criteria
6. Request file structure details
7. Ask about integration points
8. Return handoff to Alex for completion
9. Accept handoff and begin implementation

Select 0-9:
```

## Interactive Validation

```
Handoff Validation with User

The handoff document is ready. Please review:

Select option (0-8) or 9 to approve:
0. Review task overview section
1. Check requirements completeness
2. Examine technical design
3. Verify implementation steps
4. Review test requirements
5. Check acceptance criteria
6. Add warnings or notes
7. Make corrections
8. Request Alex to revise
9. Approve and proceed

Select 0-9:
```

## Evidence Collection

```yaml
# .tad/evidence/project-logs/[project]/handoff-evidence.yaml
handoff_quality:
  completeness: [percentage]
  clarity: [1-10]
  iterations_needed: [number]
  clarifications_required: []
  time_to_approval: [minutes]
```

## Critical Rules

- **Alex**: Handoff must be 100% complete before sending
- **Blake**: Cannot start without complete handoff
- **Violation**: Incomplete handoff blocks all progress
- **Evidence**: Document handoff quality metrics

[[LLM: This command manages the critical handoff document - Alex creates it with all mandatory sections, Blake verifies completeness before implementation. This is the ONLY communication channel between agents.]]