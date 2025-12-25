# Gate Execution Guide for Agents

## 🎯 When to Execute Gates

### Gate 1: Requirements Clarity
**WHO**: Agent A (Alex)
**WHEN**: Immediately after receiving human requirements
**BEFORE**: Starting any design work
**COMMAND**: Copy checklist from quality-gate-checklist.md Gate 1

### Gate 2: Design Completeness
**WHO**: Agent A (Alex)
**WHEN**: After completing design, before handoff to Agent B
**BEFORE**: Using any handoff template
**COMMAND**: Copy checklist from quality-gate-checklist.md Gate 2

### Gate 3: Implementation Quality
**WHO**: Agent B (Blake)
**WHEN**: After writing code, before claiming completion
**BEFORE**: Reporting back to Agent A
**COMMAND**: Copy checklist from quality-gate-checklist.md Gate 3

### Gate 4: Integration Verification
**WHO**: Both Agent A & Agent B
**WHEN**: Before final delivery to human
**BEFORE**: Presenting working software
**COMMAND**: Copy checklist from quality-gate-checklist.md Gate 4

---

## ⚡ Quick Gate Execution Protocol

### Step 1: Copy Checklist
```markdown
Create new file: .tad/working/gates/gate-[N]-[project]-[timestamp].md
Copy relevant checklist from quality-gate-checklist.md
```

### Step 2: Execute Verification
```markdown
Work through each checkbox systematically
Document evidence for each check
Mark ✅ only when actually verified
```

### Step 3: Gate Decision
```markdown
PASS: Fill out completion template, proceed to next phase
FAIL: Document failure reasons, fix issues, re-execute gate
OVERRIDE: Get human approval, document risks accepted
```

### Step 4: Archive Results
```markdown
Save completed checklist in .tad/working/gates/
Reference gate completion in handoff documents
```

---

## 🚨 Critical Gate Rules

### NEVER Skip Gates
- Gates catch the exact problems found in real usage transcripts
- Each gate addresses specific failure patterns
- Skipping gates leads to function call errors, missing data flows, safety issues

### NEVER Assume Pass
- Check every box explicitly
- Provide evidence for each verification
- When in doubt, mark as FAIL and investigate

### NEVER Rush Through
- Gates are designed to save time by preventing rework
- Thorough gate execution prevents downstream problems
- Better to spend 5 minutes on gate than 2 hours debugging

### Always Document
- Future projects learn from gate execution logs
- Patterns in gate failures indicate systemic issues
- Evidence supports continuous improvement

---

## 📊 Gate Effectiveness Tracking

### Success Metrics
- **First-time pass rate**: Higher is better
- **Issue detection**: Problems caught at gates vs. later
- **Cycle time improvement**: Faster delivery through fewer reworks

### Warning Signs
- Multiple gate failures on same project
- Same agent failing same gate repeatedly
- Issues discovered after gate passage

### Improvement Actions
- Update checklist when new issue types found
- Additional agent training on frequently failed checks
- Process improvements for common failure patterns

---

## 🎓 Agent Training on Gates

### Agent A (Alex) Gate Focus
- **Requirements Clarity**: Deep user value understanding
- **Design Completeness**: Function existence verification
- **Handoff Quality**: Complete specification packages

### Agent B (Blake) Gate Focus
- **Implementation Quality**: Code compilation verification
- **Data Flow Testing**: End-to-end functionality
- **Integration Verification**: Regression testing

### Shared Responsibilities
- Safety-first mindset: User health and security
- Historical code awareness: Reuse before create
- Sub-agent utilization: Use specialized expertise
- Evidence collection: Document all verifications