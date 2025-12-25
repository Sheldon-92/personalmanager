# TAD Quick Start

## Welcome to TAD
This is your TAD (Triangle Agent Development) setup - a simplified, value-focused development method using human-AI collaboration.

## Directory Structure
```
.tad/
├── agents/          # Main agent definitions
│   ├── agent-a-architect.md
│   └── agent-b-executor.md
├── sub-agents/      # Specialized agents (callable)
├── context/         # Project information
│   ├── PROJECT.md   # Project overview
│   └── decisions.md # Architectural decisions
├── working/         # Active work
│   ├── sprint.md    # Current sprint
│   └── report.md    # Latest report
├── templates/       # Document templates
└── config.yaml      # TAD configuration
```

## Quick Activation

### Terminal 1 - Agent A (Strategic Architect)
```
You are Agent A. Read .tad/agents/agent-a-architect.md
```

### Terminal 2 - Agent B (Execution Master)
```
You are Agent B. Read .tad/agents/agent-b-executor.md
```

## How TAD Works

### The Triangle Model
```
     Human (You)
    /          \
   /            \
Agent A ------- Agent B
(Design)      (Execute)
```

### Simple Workflow
1. **Human** expresses what they need
2. **Agent A** designs the solution
3. **Agent B** implements it
4. **Human** validates the value delivered

## Task Sizing Guide

### Small Tasks (<2 hours)
- Simple verbal communication
- No heavy documentation
- Quick implementation and review

### Medium Tasks (2-8 hours)
- Light documentation in sprint.md
- Key decisions recorded
- Checkpoint reviews

### Large Projects (>1 day)
- Full design documentation
- Formal review gates
- Comprehensive testing

## Available Sub-Agents

### Analysis & Planning
- `product-expert` - Product strategy and user research
- `data-analyst` - Data analysis and insights

### Architecture & Design
- `backend-architect` - Backend system design
- `frontend-specialist` - UI/UX architecture
- `api-designer` - API design and documentation
- `database-expert` - Data modeling

### Execution & Quality
- `test-runner` - Test execution
- `bug-hunter` - Debugging
- `performance-optimizer` - Performance tuning
- `security-auditor` - Security review
- `devops-engineer` - Deployment and infrastructure

## Commands

### Agent A Commands
- `*plan <requirement>` - Create sprint plan
- `*design <feature>` - Generate technical design
- `*review <implementation>` - Review code quality
- `*call <sub-agent> <task>` - Invoke specialist

### Agent B Commands
- `*implement <spec>` - Begin implementation
- `*parallel <tasks>` - Execute tasks in parallel
- `*test <component>` - Run tests
- `*deploy <environment>` - Deploy solution

## First Steps

1. **Update PROJECT.md** with your project information
2. **Activate both agents** in separate terminals
3. **State your need** clearly
4. **Let the triangle collaboration begin!**

## Remember

- **Value over process** - Focus on what users need
- **Simple over complex** - Start simple, add only when needed
- **Ship over perfect** - Deliver working increments
- **Learn over assume** - Each sprint teaches something

## Need Help?

- Check the main TAD documentation in README.md
- Review recent decisions in context/decisions.md
- Ask agents to explain their approach
- Focus on delivering value, not following process

---

Welcome to efficient, value-focused development with TAD!