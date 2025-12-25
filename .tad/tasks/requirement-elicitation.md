# Requirement Elicitation Task (需求挖掘任务)

## ⚠️ CRITICAL EXECUTION NOTICE ⚠️

**THIS IS AN EXECUTABLE WORKFLOW - NOT REFERENCE MATERIAL**

When this task is invoked:

1. **DISABLE ALL EFFICIENCY OPTIMIZATIONS** - This workflow requires full user interaction
2. **MANDATORY 3-5 ROUNDS** - Must complete AT LEAST 3 rounds of confirmation
3. **ELICITATION IS REQUIRED** - When `elicit: true`, you MUST use the 0-9 format and wait for user response
4. **NO SHORTCUTS ALLOWED** - Cannot proceed without user confirmation at each round

**VIOLATION INDICATOR:** If you proceed with less than 3 rounds of confirmation, you have violated this workflow.

## Purpose

Deep understanding of user requirements through structured, iterative elicitation. This is Agent A's primary tool for ensuring complete requirement understanding before design.

## Mandatory Process

### Round 0: MCP Pre-Elicitation Checks (NEW - OPTIONAL ENHANCEMENT)

**[NEW] Before starting Round 1, perform these MCP-enhanced checks:**

**STEP 1: Memory Bank Check (RECOMMENDED)**
```
IF memory-bank MCP is available:
  [CALL] memory-bank MCP
  Query: "项目历史决策、相似需求、已有组件"

  Output format:
  ✓ Memory Bank Checked
    - Found X related decisions
    - Found Y similar features
    - Found Z reusable components

  IF found relevant history:
    - Incorporate into understanding
    - Mention to user in Round 1

ELSE:
  [SKIP] Continue to Round 1
```

**STEP 2: Project Context Loading (RECOMMENDED)**
```
[READ] .tad/context/PROJECT.md (if exists)

Output format:
✓ Project Context Loaded
  - Tech Stack: [list]
  - Constraints: [list]
  - Target Users: [list]

Use this context to inform questions in Round 2
```

**NOTE:** These MCP checks are enhancements. If MCP tools are not available, proceed directly to Round 1. The original workflow remains fully functional without MCP.

---

### Round 1: Initial Understanding (MANDATORY - UNCHANGED)

**YOU MUST:**

1. Listen to user's initial requirement
2. Rephrase in your own words
3. Identify key value propositions
4. List initial assumptions

**Present to user:**
```
Based on what you've told me, I understand that:
[Your rephrasing]

Key value propositions I've identified:
1. [Value 1]
2. [Value 2]
3. [Value 3]

My initial assumptions:
- [Assumption 1]
- [Assumption 2]

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

**WAIT FOR USER RESPONSE** - Do not proceed until user selects option or provides feedback

**⚠️ MANDATORY: Call Product-Expert Sub-agent (CRITICAL):**
```
BEFORE proceeding to Round 2, Alex MUST call product-expert sub-agent.

[USE Task tool]
Task(
  subagent_type: "product-expert",
  description: "Analyze user requirement for product perspective",
  prompt: "Analyze the following user requirement:

[User's requirement from Round 1]

Provide:
1. User value analysis - what value does this deliver?
2. Key use cases - how will users actually use this?
3. Edge cases to consider - what could go wrong?
4. Critical questions to ask - what's missing from requirements?
5. Similar features in market - what do competitors do?

Be specific and actionable in your analysis."
)

[WAIT for product-expert response]

Alex then INCORPORATES product-expert's analysis into Round 2:
- Use identified use cases in questions
- Probe edge cases
- Ask critical questions identified
- Reference similar features when relevant

NEVER skip this step - it's mandatory for TAD v1.2 quality assurance.
```

**[NEW] Context7 Auto-Trigger (ENHANCEMENT):**
```
IF user mentions ANY framework/library in Round 1:
  Keywords: ["Next.js", "React", "Vue", "Tailwind", "TypeScript", "Supabase", etc.]

  [AUTO-TRIGGER] context7 MCP
  Action: "use context7 for [detected framework]"

  Output:
  ⚡ Context7 called for: [framework name]
  ✓ Latest documentation loaded

  This information will inform Round 2 questions

ELSE:
  [SKIP] Continue normally
```

**NOTE:** This is an optional enhancement. Round 1 proceeds normally with or without context7.

---

### Round 2: Deep Exploration (MANDATORY - UNCHANGED)

**Based on Round 1 feedback, YOU MUST:**

1. Incorporate all corrections and additions
2. Check for existing/historical solutions
3. Identify technical constraints
4. Explore non-functional requirements

**Present to user:**
```
Updated understanding after your feedback:
[Refined requirements]

Critical questions to explore:
1. Have you implemented something similar before?
2. Are there existing components we can reuse?
3. What are the performance expectations?
4. What are the security requirements?
5. Who are the end users?

[[LLM: You MUST ask these questions and wait for answers]]

Please select an option (0-8) or 9 to continue:
0. Discuss scalability needs
1. Define user personas
2. Explore integration requirements
3. Identify dependencies
4. Discuss error handling
5. Define success metrics
6. Consider future extensions
7. Review technical constraints
8. Analyze risks
9. Continue to next round

Select 0-9:
```

---

### Round 2.5: Project Type Detection & MCP Recommendation (NEW - OPTIONAL)

**[NEW] After Round 2 (when tech stack is confirmed), perform project detection:**

```
[PROJECT TYPE DETECTION]

Based on Round 2 responses, analyze:
- Keywords mentioned (frameworks, tools, domains)
- Technical stack preferences
- Project characteristics

Detection Logic:
IF keywords match "web_fullstack" (>70% confidence):
  Project Type: Web Fullstack Application
  Recommended MCPs: supabase, playwright, vercel, react-mcp

ELSE IF keywords match "data_science" (>60% confidence):
  Project Type: Data Science/Analysis
  Recommended MCPs: jupyter, pandas-mcp, antv-chart, postgres-mcp-pro

ELSE IF keywords match "machine_learning" (>80% confidence):
  Project Type: Machine Learning
  Recommended MCPs: jupyter, optuna, huggingface, zenml

ELSE IF keywords match "devops" (>70% confidence):
  Project Type: DevOps/Infrastructure
  Recommended MCPs: kubernetes, docker, aws, terminal

ELSE IF keywords match "creative" (>70% confidence):
  Project Type: Creative/Multimedia
  Recommended MCPs: figma, video-audio-mcp, adobe-mcp

ELSE:
  [SKIP] No clear project type, continue to Round 3
```

**IF project type detected with confidence > threshold:**

Present to user:
```
---
🎯 Project Type Detected: [Type Name]
Confidence: [XX]%

Based on your requirements, I recommend installing these MCP tools:

📦 Recommended Project-Layer MCPs:
1. ✨ [MCP 1] - [Purpose]
2. ✨ [MCP 2] - [Purpose]
3. ✨ [MCP 3] - [Purpose]
4. ✨ [MCP 4] - [Purpose]

These tools will significantly improve development efficiency:
- [Benefit 1]
- [Benefit 2]
- [Benefit 3]

Installation takes ~20-30 seconds.

Install Options:
0. Install all recommended (fastest) ←
1. Let me choose which to install
2. Skip for now (can install later with: tad mcp install)

Select 0-2:
---
```

**User Selection Handling:**
```
IF user selects 0:
  Alex: "Installing recommended MCP tools..."

  [USE Bash tool - Alex executes directly]
  FOR each recommended MCP:
    Example for Web Fullstack:
      bash: npx -y @supabase/mcp-server --install
      bash: npx -y @playwright/test --install
      bash: npx -y vercel --global

  [REPORT to user]
  ✓ supabase MCP installed
  ✓ playwright MCP installed
  ✓ vercel MCP installed

  Installation complete! (~20-30s)

  [CONTINUE] to Round 3

ELSE IF user selects 1:
  [SHOW] Individual MCP descriptions with checkboxes
  [LET USER] select specific MCPs (e.g., 1,3,4)

  Alex: "Installing selected tools..."
  [USE Bash tool for each selected MCP]

  [CONTINUE] to Round 3

ELSE IF user selects 2:
  [LOG] "MCP installation skipped by user"
  [REMIND] "Blake can still use built-in capabilities. You can enable MCP tools anytime later."
  [CONTINUE] to Round 3
```

**IMPORTANT NOTES:**
- Alex uses Bash tool to install MCPs **automatically** (no human CLI needed)
- This step is OPTIONAL and non-blocking
- If no project type detected, skip directly to Round 3
- If MCP installation fails, log error and continue with built-in capabilities
- The original workflow remains fully functional without this step
- **User never needs to run CLI commands** - Alex handles everything

---

### Round 3: Validation and Confirmation (MANDATORY - UNCHANGED)

**Present complete requirement understanding:**

```
## Complete Requirement Understanding

### Functional Requirements:
1. [Requirement 1]
2. [Requirement 2]
...

### Non-Functional Requirements:
1. [NFR 1]
2. [NFR 2]
...

### Constraints:
- [Constraint 1]
- [Constraint 2]

### Success Criteria:
- [Criterion 1]
- [Criterion 2]

### Risks and Mitigation:
- [Risk 1]: [Mitigation]
- [Risk 2]: [Mitigation]

Please select an option (0-8) or 9 to finalize:
0. Adjust functional requirements
1. Modify non-functional requirements
2. Add missing requirements
3. Change priorities
4. Revise success criteria
5. Add acceptance criteria
6. Include additional stakeholders
7. Define timeline constraints
8. Request another round of refinement
9. Confirm and finalize requirements

Select 0-9:
```

### Rounds 4-5: Additional Refinement (OPTIONAL but RECOMMENDED)

If user selects option 8 in Round 3, or if significant changes were made, continue with:

**Round 4: Edge Cases and Exceptions**
- Explore boundary conditions
- Identify exception scenarios
- Define fallback behaviors

**Round 5: Final Polish**
- Last chance for adjustments
- Confirm all stakeholder needs met
- Verify completeness

## Output Document

After minimum 3 rounds (or when user confirms), create:

**File:** `.tad/docs/requirements/requirements_[timestamp].md`

```markdown
# Requirements Document
Version: 1.0
Date: [Date]
Rounds of Elicitation: [Number]
Status: Confirmed

## Executive Summary
[Brief overview]

## Functional Requirements
[Detailed list with IDs: FR1, FR2, etc.]

## Non-Functional Requirements
[Detailed list with IDs: NFR1, NFR2, etc.]

## User Personas
[Identified users and their needs]

## Success Criteria
[Measurable success indicators]

## Constraints and Assumptions
[Technical and business constraints]

## Risks and Mitigation
[Identified risks with mitigation strategies]

## Traceability
- Elicitation Rounds: [Number]
- Key Decisions: [List]
- Deferred Items: [List]

## Sign-off
- Confirmed by: Human (Value Guardian)
- Date: [Date]
- Ready for: Design Phase

## MCP Tools Used (NEW - OPTIONAL)
- Memory Bank: [✓ Called / ✗ Not available]
- Context7: [✓ Called for: X / ✗ Not called]
- Brave Search: [✓ Called / ✗ Not called]
- Project Type: [Detected: X / Not detected]
- Project MCPs: [Installed: list / Skipped]
```

## MCP Usage Checklist (NEW - OPTIONAL)

**Before finalizing requirements document, verify MCP usage:**

```
□ memory-bank checked for project history (if available)
□ context7 called for mentioned frameworks (if applicable)
□ brave-search used for technical research (if needed)
□ project type detected (if tech stack mentioned)
□ project-layer MCPs recommended and user decision recorded

IF any applicable checkbox unchecked:
  ⚠️ REMINDER: Consider using MCP tools for better analysis
  However, this is NOT a blocking violation - proceed if intentional

MCP Usage is ENHANCEMENT, not REQUIREMENT
The original TAD workflow is complete without MCP
```

## CRITICAL REMINDERS (UNCHANGED)

**❌ NEVER:**
- Skip rounds (minimum 3 required)
- Assume understanding without confirmation
- Use yes/no questions
- Proceed without numbered options
- Create design before requirements confirmed

**✅ ALWAYS:**
- Complete minimum 3 rounds
- Use 0-9 numbered options
- Wait for user selection
- Document all decisions
- Create formal requirements document

## Violation Handling

If you attempt to skip rounds or proceed too quickly:
```
⚠️ VIOLATION DETECTED ⚠️
Type: Insufficient Elicitation
Required: Minimum 3 rounds
Completed: [X] rounds
Action: Returning to Round [X+1]
```

[[LLM: This task is MANDATORY for Agent A before any design work can begin. The 3-round minimum is NOT negotiable unless user explicitly requests YOLO mode.]]