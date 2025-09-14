# Project Status Snapshot

> Version: v0.1.0 "初心"  
> Last Updated: 2025-09-13

## Current State

- Phase 1: Completed and released (GitHub tag: v0.1.0)
- Phase 2: First batch done
  - P2-06: npx bootstrap installer (local npx verified)
  - P2-02: `pm doctor` environment self-check
  - P2-01/03/04 (docs + code first pass): testing commands, setup modes, error codes/logs
- Sprint 1: Completed (2025-09-14)
  - Workspace scaffolding: `pm workspace init` ready
  - Workspace validation: `pm agent status --json` ready
  - Prompt compiler and platform snippets ready
  - Full test coverage (46/46 tests passing)

## Quick Commands (10s sanity)

```
# Version & readiness
pm --version
pm doctor

# Quick smoke & E2E tests
pm test smoke --quick
pm test e2e --workflow=task

# Initialization (choose one)
pm setup --quick      # fast defaults
pm setup --guided     # step-by-step
pm setup --advanced   # all options

# AI Workspace (Sprint 1)
pm workspace init
pm agent status --json
pm agent prompt --print  # compile project instructions
```

## For Fresh Environments

- One-liner install (recommended):
```
npx @personal-manager/pm-bootstrap
```
- Or via GitHub Release artifact (pipx):
```
pipx install \
  https://github.com/Sheldon-92/personalmanager/releases/download/v0.1.0/personal_manager-0.1.0-py3-none-any.whl
```

## Agent Integrations

- Templates: `configs/agent-templates/claude/settings.sample.json`, `configs/agent-templates/gemini/settings.sample.json`
- Guide: `docs/tool_registration.md` (System Prompt, intent→command mapping, error handling)

## Release Notes

- **Latest Release**: [v0.1.0 "初心"](https://github.com/Sheldon-92/personalmanager/releases/tag/v0.1.0) 
- **npm Package**: [@personal-manager/pm-bootstrap](https://www.npmjs.com/package/@personal-manager/pm-bootstrap) (pending publish)
- CHANGELOG: `CHANGELOG.md`
- Release Checklist: `RELEASE_CHECKLIST.md`
- CI: `.github/workflows/release.yml` (tag → build → GitHub Release; optional npm publish)

## What’s Next (Planned Sprints)

- Sprint 1 — AI 工作空间与 Prompt 编译器（文档/规范先行）
  - workspace-config / ai-agent-definition / interaction-patterns 三件套
  - `pm agent prompt --print|--write` 编译规范与产物要求
- Sprint 2 — 意图路由与执行（协议/样例先行）
  - `pm ai route|execute` JSON 协议与核心意图短语库
- Sprint 3 — 本地记忆与偏好（模型与摘要先行）
  - 事件日志 / 画像摘要 / 隐私与脱敏策略

## Pointers

- User Guide: `docs/user_guide.md`
- Quick Start (docs index): `docs/index.md`
- Troubleshooting & Error Codes: `docs/troubleshooting.md`
- Phase Plans: `docs/phase_2_plan.md`, `docs/phase_3_plan.md`
 - Specs: `docs/specs/workspace_config.md`, `docs/specs/prompt_compiler.md`, `docs/specs/interaction_patterns.md`, `docs/specs/memory_model.md`
