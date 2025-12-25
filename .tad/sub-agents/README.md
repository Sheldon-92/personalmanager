# TAD Sub-agents Directory

## Important Note
This directory does NOT contain actual agent files. The sub-agents listed below are **Claude Code built-in agents** that can be called through the Task tool.

## Available Claude Code Sub-agents

These are the 16 real sub-agents provided by Claude Code platform:

### Strategic Sub-agents (Mainly for Agent A)
1. **product-expert** - Requirements analysis, user stories
2. **backend-architect** (Opus) - System design, architecture decisions
3. **api-designer** - API design, endpoint specifications
4. **code-reviewer** (Opus) - Code quality review, best practices
5. **ux-expert-reviewer** - UX assessment, user flow optimization
6. **performance-optimizer** (Opus) - Performance analysis, optimization
7. **data-analyst** - Data analysis, insights generation

### Execution Sub-agents (Mainly for Agent B)
8. **parallel-coordinator** - Parallel task orchestration
9. **fullstack-dev-expert** - Full-stack development
10. **frontend-specialist** - React/Vue/Angular development
11. **refactor-specialist** - Code refactoring, tech debt cleanup
12. **bug-hunter** - Bug diagnosis and fixing
13. **test-runner** - Test execution, coverage analysis
14. **devops-engineer** - CI/CD, deployment, infrastructure
15. **database-expert** - Database design, query optimization
16. **docs-writer** - Documentation, API docs, README

## How to Call Sub-agents

### From Agent A
```
I need to analyze user requirements for this feature.
[Calling product-expert sub-agent via Task tool]

I need to design the system architecture.
[Calling backend-architect sub-agent via Task tool]
```

### From Agent B
```
I'll coordinate parallel development tasks.
[Calling parallel-coordinator sub-agent via Task tool]

I found a bug that needs diagnosis.
[Calling bug-hunter sub-agent via Task tool]
```

## Key Differences from BMAD

| BMAD (Wrong) | TAD (Correct) | Status |
|--------------|---------------|--------|
| analyst.md file | data-analyst agent | ✅ Real Claude Code agent |
| pm.md file | product-expert agent | ✅ Real Claude Code agent |
| dev.md file | fullstack-dev-expert agent | ✅ Real Claude Code agent |
| qa.md file | test-runner agent | ✅ Real Claude Code agent |
| architect.md file | backend-architect agent | ✅ Real Claude Code agent |

## Remember
- These are NOT files to be read
- These are Claude Code platform services
- Called through Task tool with subagent_type parameter
- Each has specific capabilities and use cases
- Use according to task requirements