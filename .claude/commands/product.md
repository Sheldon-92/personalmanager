# /product Command (Quick Launch Product-Expert)

When this command is triggered, immediately launch the product-expert sub-agent:

## Immediate Execution

```
Launching Product-Expert Sub-agent
===================================

Purpose: Requirements analysis, user stories, business value definition

[Calling product-expert via Task tool with subagent_type="product-expert"]
```

## When to Use

- **MANDATORY**: For ALL requirement analysis (Agent A)
- **Recommended**: When defining user value
- **Useful**: For prioritization decisions
- **Critical**: For elicitation rounds

## Typical Prompt Template

```
I need to analyze requirements for [feature/project].

Context:
- Current situation: [describe]
- User need: [what users want]
- Business goal: [what business wants]

Please help me:
1. Understand the core user value
2. Define clear requirements
3. Create user stories with acceptance criteria
4. Identify edge cases and constraints
5. Prioritize based on value/effort

Specific questions:
- [Question 1]
- [Question 2]
```

## Evidence to Collect

After product-expert provides insights:
- Document in requirements file
- Update evidence log with patterns found
- Note any new user personas identified
- Record business value metrics

[[LLM: This command immediately launches product-expert sub-agent via Task tool. This is mandatory for Agent A during requirement analysis.]]