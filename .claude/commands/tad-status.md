# TAD Status Check Command

When this command is triggered, check and report TAD configuration status:

## ⚠️ MANDATORY OUTPUT FORMAT

**This command MUST produce standardized status output:**

### 📊 Status Report Template
```
TAD Framework Status Report
Generated: [timestamp]

🔍 INSTALLATION CHECK
[✅/❌] Core directory structure
[✅/❌] Agent definition files
[✅/❌] Configuration files
[✅/❌] Template files
[✅/❌] Project context files

📋 CONFIGURATION VERIFICATION
- Version: [version number]
- Scenarios: [count]/6 configured
- Sub-agents: [count]/16 available
- Templates: [count] handoff templates

⚡ READINESS STATUS
[✅/❌] Ready for Agent A activation
[✅/❌] Ready for Agent B activation
[✅/❌] Ready for triangle collaboration

🚨 ISSUES (if any)
- [List specific issues]
- [Remediation suggestions]

📋 NEXT ACTIONS
[Specific next steps based on status]
```

---

## Check TAD Installation Status

```markdown
Checking TAD Framework status...

1. Core Files:
   - Check if .tad/config.yaml exists
   - Check if .tad/agents/agent-a-architect.md exists
   - Check if .tad/agents/agent-b-executor.md exists
   - Check if WORKFLOW_PLAYBOOK.md exists
   - Check if CLAUDE_CODE_SUBAGENTS.md exists

2. Configuration:
   - Read .tad/config.yaml version
   - Verify 6 scenarios configured
   - Verify 16 sub-agents listed

3. Project Files:
   - Check .tad/context/ directory
   - Check .tad/working/ directory
   - List existing project documents

4. Report:
   If all checks pass:
   ✅ TAD Framework v2.0 installed
   ✅ Configuration valid
   ✅ 6 scenarios available
   ✅ 16 sub-agents configured
   ✅ Ready for use

   If issues found:
   ⚠️ Issues detected:
   - [List missing files]
   - [List configuration problems]

   Run '/tad-init' to fix issues.
```