# RC Fix Task 2 — Component Integration Stability

## 1. 项目背景与目标
- 背景: Phase 5 指出跨组件集成不稳定（事件总线、插件加载、观测指标），影响兼容性与可用性 SLO。
- 目标: 修复跨组件集成问题，确保集成测试 100% 通过，并生成联测证据。

## 2. 前置学习清单
- `src/pm/events/bus.py`, `src/pm/events/handlers/*`
- `src/pm/plugins/sdk.py`, `src/pm/plugins/loader.py`
- `src/pm/obs/{metrics.py,logging.py,tracing.py,enhanced_metrics.py}`
- `tests/integration/`, `tests/obs/`, `tests/plugins/`
- `docs/reports/phase_5/PHASE5_INDEX.md`, `plugin_conformance.md`, `observability_metrics.md`

## 3. 具体任务与验收标准（AC）
- AC-1: `pytest tests/integration -q` 100% 通过
- AC-2: 事件→插件→观测 的端到端链路验证通过（触发/处理/记录完整）
- AC-3: 产出 `logs/phase5_integration_fix.log`（包含事件触发、插件执行、指标落盘的关键日志）
- AC-4: 在 `docs/reports/phase_5/PHASE5_INDEX.md` 增补“Integration Fix”段落，贴关键指标

## 4. 执行与自验证步骤
1) 运行 `python3 -m pytest tests/integration -q`，记录失败模块与栈
2) 以最小可复现场景重放（可用 `tests/obs/*` 和 `tests/plugins/*` 辅助）
3) 核查事件处理的错误容忍与重试策略；确保观测指标字段与单位一致
4) 复测并在日志中打点关键阶段，形成 `logs/phase5_integration_fix.log`
5) 更新 `PHASE5_INDEX.md` “Integration Fix”摘要

—
交付物: 集成测试通过记录、关键日志文件、索引更新
