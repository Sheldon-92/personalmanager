# [Archived] Agents Start Here

> Version: v1.0  
> Last Updated: 2025-09-13

## Your Role

You are operating PersonalManager in an Agent-first setup (BMAD-based). Your tools are local CLI commands.

## Immediate Boot Sequence (1–2 minutes)

```
# If fresh environment
npx @personal-manager/pm-bootstrap

# Sanity & readiness
pm --version
pm doctor
pm test smoke --quick
```

## Command Mapping (intent → CLI)

- Projects overview → `pm projects overview`
- Project status "X" → `pm project status "X"`
- Capture idea → `pm capture "..."`
- Clarify inbox → `pm clarify`
- Today focus → `pm today` (or `pm recommend --count 5`)
- Explain recommendation → `pm explain <TASK_ID>`
- Initialize system → `pm setup --guided|--quick|--advanced`
- Diagnose env → `pm doctor`

See full mapping and prompts in `docs/tool_registration.md`.

Note: This quick-start card已并入用户指南（docs/user_guide.md）的相关章节，此处作为历史文档保留。

## Error Handling Contract

- Unified error codes:
  - E1xxx: config/init; E2xxx: projects/tasks; E3xxx: external; E4xxx: runtime
- When receiving an error:
  1) Echo code + message  2) Suggest next command (often `pm setup` or `pm doctor`)  3) Avoid guessing results

## References

- Quick Start index: `docs/index.md`
- User Guide: `docs/user_guide.md`
- Troubleshooting & Error Codes: `docs/troubleshooting.md`
- Phase Plan: `docs/phase_2_plan.md`, `docs/phase_3_plan.md`
- Agent templates: `configs/agent-templates/*`
