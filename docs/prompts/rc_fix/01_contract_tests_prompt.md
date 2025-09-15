# RC Fix Task 1 — API Contract Tests Restoration

## 1. 项目背景与目标
- 背景: Phase 5 已达成 API v1.0 GA 冻结，但报告显示“合同测试执行率为 0%（发现/执行问题）”。需恢复 pytest 发现、执行与报告收敛，确保契约校验与性能契约可验证。
- 目标: 修复测试执行链，输出规范化结果文件，作为 GA 前置门槛的证据。

## 2. 前置学习清单
- `docs/api/openapi.yaml`（v1.0 GA 冻结，含性能与兼容策略）
- `tests/api/`（contract_api.py, contract_schemas.py, contract_errors.py, api_smoke.py, performance.py）
- `run_api_tests.py`（结果汇总与文件输出）
- `docs/reports/phase_5/api_contract_report.md`（当前问题背景）
- `docs/reports/phase_5/PHASE5_INDEX.md`（Phase 5 索引）

## 3. 具体任务与验收标准（AC）
- AC-1: `pytest tests/api -q` 能完整发现并执行全部测试，无中断
- AC-2: OpenAPI 规范加载与字段校验通过（版本=1.0.0，paths/schemas 数量与报告一致）
- AC-3: 生成/更新 `api_test_results.json`，包含：
  - `openapi_valid: true`
  - `version: 1.0.0`
  - `endpoints_count`、`schemas_count`
  - `suites: {contract, errors, performance}` 的通过率与耗时
- AC-4: 在 `docs/reports/phase_5/api_contract_report.md` 追加“RC 修复小结”与最新指标

## 4. 执行与自验证步骤
1) 本地运行：`python3 -m pytest tests/api -q`，记录失败点
2) 检查路径与依赖：确保 `yaml` 可用且 `docs/api/openapi.yaml` 路径加载正确
3) 修复测试收集/标记问题（如 `__init__.py`、`conftest.py`、命名不规范）
4) 运行 `python3 run_api_tests.py`，确认输出 `api_test_results.json` 且 `openapi_valid: true`
5) 将关键指标写回报告文件“RC 修复小结”段落，标注时间戳与命令

—
交付物: 更新后的 `api_test_results.json`、报告修订，测试执行截图/日志（可选）
