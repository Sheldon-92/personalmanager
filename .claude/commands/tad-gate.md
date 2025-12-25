# /gate Command (Execute Quality Gate)

When this command is triggered, execute the appropriate quality gate based on current context:

## Gate Detection and Execution

```
Quality Gate Execution
======================

Detecting current context...

Available Gates:
1. Gate 1: Requirements Clarity (Agent A - After elicitation)
2. Gate 2: Design Completeness (Agent A - Before handoff)
3. Gate 3: Implementation Quality (Agent B - After coding)
4. Gate 4: Integration Verification (Agent B - Before delivery)

Which gate to execute? (1-4):
```

## Gate 1: Requirements Clarity (Alex)
```yaml
When: After requirement elicitation
Owner: Agent A (Alex)
Check:
  - [ ] Minimum 3 rounds completed
  - [ ] Requirements documented
  - [ ] User confirmed understanding
  - [ ] Success criteria defined
Evidence: .tad/evidence/gates/gate1_[timestamp].yaml
```

## Gate 2: Design Completeness (Alex)
```yaml
When: Before creating handoff
Owner: Agent A (Alex)
Check:
  - [ ] Architecture complete
  - [ ] Components specified
  - [ ] Functions verified
  - [ ] Data flow mapped
Evidence: .tad/evidence/gates/gate2_[timestamp].yaml
```

## Gate 3: Implementation Quality (Blake)
```yaml
When: After implementation
Owner: Agent B (Blake)
Check:
  - [ ] Code complete
  - [ ] Tests written
  - [ ] Coverage >80%
  - [ ] Standards met
Evidence: .tad/evidence/gates/gate3_[timestamp].yaml
```

## Gate 4: Integration Verification (Blake)
```yaml
When: Before delivery
Owner: Agent B (Blake)
Check:
  - [ ] Integration tested
  - [ ] E2E tests pass
  - [ ] Performance acceptable
  - [ ] Ready for user
Evidence: .tad/evidence/gates/gate4_[timestamp].yaml
```

## Interactive Gate Execution

For each gate, use 0-9 options format:

```
Gate [N]: [Name] Execution

Status Check:
✅ [Criterion]: Pass
❌ [Criterion]: Fail - [Issue]
⚠️ [Criterion]: Warning - [Concern]

Please select action (0-8) or 9 to pass gate:
0. Review checklist again
1. Fix failing items
2. Collect more evidence
3. Run additional tests
4. Use sub-agent for help
5. Document issues found
6. Request clarification
7. Partial pass with notes
8. Fail gate (restart phase)
9. Pass gate (all criteria met)

Select 0-9:
```

## Violation Handling

```
⚠️ GATE VIOLATION DETECTED ⚠️
Type: Attempting to skip Gate [N]
Required: Must execute gate before proceeding
Action: BLOCKED until gate executed

To continue:
1. Execute gate properly
2. Address any failures
3. Collect evidence
4. Get pass result
```

[[LLM: This command executes the appropriate quality gate based on current agent and project phase. Gates are mandatory checkpoints that ensure quality.]]