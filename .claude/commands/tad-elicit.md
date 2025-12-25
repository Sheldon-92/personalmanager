# /elicit Command (Start Requirement Elicitation)

When this command is triggered, execute the requirement elicitation task with mandatory 3-5 rounds:

## Immediate Execution

1. **Load and execute**: `.tad/tasks/requirement-elicitation.md`
2. **Enforce**: Minimum 3 rounds of elicitation
3. **Format**: Use 0-9 numbered options (never yes/no)
4. **Evidence**: Collect elicitation evidence

## Quick Start Template

```
Starting TAD Requirement Elicitation (3-5 rounds mandatory)

Round 1 of 3 (minimum)
====================

Based on what you've told me, I understand that:
[Initial understanding]

Key value propositions identified:
1. [Value 1]
2. [Value 2]
3. [Value 3]

Please select an option (0-8) or 9 to continue:
0. Expand on requirements
1. Clarify specific details
2. Provide more context
3. Correct my understanding
4. Add constraints or limitations
5. Define priorities
6. Give examples
7. Discuss alternatives
8. Explore edge cases
9. Continue to next round

Select 0-9:
```

## Enforcement

- **VIOLATION**: Attempting to skip rounds or use yes/no format
- **MANDATORY**: Must complete minimum 3 rounds
- **EVIDENCE**: Must document each round in evidence system
- **OUTPUT**: Creates `.tad/docs/requirements/requirements_[timestamp].md`

[[LLM: This command immediately starts the requirement elicitation process with Agent A persona, enforcing all mandatory rules from TAD v1.1.]]