# Phase 5 RC 专项修复计划（7–14 天）

> 目标: 达到 GA 门槛（可用性 ≥99.5%，兼容性 100%），关闭 CONDITIONAL GO 条件。
> 范围: 修复合同测试执行、组件集成稳定性、插件稳定性、可观测性一致性。

## 1. 阶段目标与里程碑
- 里程碑 M1（T+3 天）: 合同测试框架恢复，执行率 100%，零中断
- 里程碑 M2（T+7 天）: 兼容性 100%（API 契约 + 跨组件集成通过）
- 里程碑 M3（T+10 天）: 可用性 ≥99.5%（连续 7 天），错误预算 burn-rate <1.0x
- 里程碑 M4（T+14 天）: 插件稳定性与观测一致性达标，发布 GA 决策评审

## 2. 任务拆解与验收标准（AC）

### T1 合同测试修复（Critical）
- 目标: pytest 发现与执行完整恢复，OpenAPI 契约校验通过
- AC:
  - 恢复 `tests/api/*` 的发现与执行，报告收敛
  - `docs/api/openapi.yaml` 载入校验 100% 通过
  - 生成 `api_test_results.json`（含 endpoints/schemas/valid 标记）

### T2 组件集成稳定性（Critical）
- 目标: 跨组件集成测试 100% 通过
- AC:
  - 事件总线、插件加载、监控指标三者联测通过
  - `tests/integration/*` 通过率 100%
  - 产出 `logs/phase5_integration_fix.log`（关键场景日志）

### T3 插件稳定性与资源泄漏（High）
- 目标: 并发 10 次装载/卸载 100% 成功，资源泄漏 0
- AC:
  - 资源基线/峰值/回落验证报告
  - `tests/plugins/*` 100% 通过
  - 产出 `docs/reports/phase_5/plugin_stability_fix.md`

### T4 可用性与 SLO（High）
- 目标: 连续 7 天可用性 ≥99.5%，错误预算 burn-rate <1.0x
- AC:
  - `observability_metrics` 与运行日志指标偏差 <3%
  - 产出 `docs/reports/phase_5/availability_validation.md`

### T5 观测一致性与告警（Medium）
- 目标: 告警误报 <5%，阈值对齐
- AC:
  - 统一指标字段/单位，提供映射表
  - 产出 `docs/reports/phase_5/observability_alignment.md`

## 3. 风险与对策
- 测试环境差异: 固化依赖与固定种子；在 CI 与本地各跑一遍
- 接口漂移风险: 冻结 API v1.0；新增仅增量且可选
- 观测偏差: 双写比对，设置容差 3%

## 4. 验证与汇报
- 每日: 冒烟 + 关键用例回归，更新 `PHASE5_INDEX.md`
- 每里程碑: 生成阶段小结与指标快照

## 5. 相关文档
- Phase 5 证据索引: `docs/reports/phase_5/PHASE5_INDEX.md`
- GA 决策: `docs/reports/phase_5/GA_RELEASE_DECISION.md`
- PO 验收: `docs/reports/phase_5/PO_VALIDATION.md`
