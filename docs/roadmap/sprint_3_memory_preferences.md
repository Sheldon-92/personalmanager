# Sprint 3 — 本地记忆与偏好（仅文档）

> 目标：将用户行为事件化、本地持久化，并定期生成“画像摘要”，用于个性化推荐与解释，且符合隐私与可清除要求。

## Epic SP3-E1 — 事件日志与 schema

### Story SP3-E1-01 — 事件结构与写入时机
- 背景与目标：定义事件类型、字段与记录策略（追加写、异常可恢复）。
- 前置学习：
  - `docs/specs/memory_model.md`
  - `src/pm/engines/recommendation_engine.py`（读取点位，仅了解）
- 任务分解：
  - 事件类型：recommendation_view|task_capture|task_complete|clarify_session|deepwork_session|habit_track
  - 字段：ts/type/payload/source/meta
  - 写入策略：jsonl 逐行追加；异常回滚与锁策略（规范层描述）
- AC：
  - 给出完整 schema 与样例
  - 定义写入/回滚/冲突策略
- 验证步骤：
  - 用 10 条样例事件过一遍 schema 校验

## Epic SP3-E2 — 画像摘要与限制

### Story SP3-E2-01 — 摘要生成与注入策略
- 背景与目标：从事件生成每日/每周画像，注入 Prompt 的 3–5 行摘要。
- 前置学习：
  - `docs/specs/memory_model.md`
  - `docs/specs/prompt_compiler.md`
- 任务分解：
  - 每日/每周摘要字段与阈值
  - 脱敏原则与大小限制
  - 与 Prompt 编译器的注入接口（仅定义）
- AC：
  - 提供摘要样例（最小+扩展版）
  - 约束：3–5 行、< 500 字
- 验证步骤：
  - 将样例摘要注入示例 Prompt 输出，检查大小与位置

## Epic SP3-E3 — 与推荐引擎的联动（只读接入）

### Story SP3-E3-01 — 偏好因子读取与解释增强
- 背景与目标：推荐时引用偏好摘要，提升“解释”可信度（不改动现有引擎，只定义读取口）。
- 前置学习：
  - `src/pm/engines/recommendation_engine.py`
  - `src/pm/engines/preference_learning.py`
- 任务分解：
  - 只读读取 profile.md 的偏好要点
  - “解释”中新增“基于近期偏好”的说明片段（规范）
- AC：
  - 给出“解释”输出样例（含偏好片段）
  - 保持离线优先，未配置时降级不报错
- 验证步骤：
  - 用 today/recommend/explain 的样例输出验证片段插入效果

## Epic SP3-E4 — 隐私与清理

### Story SP3-E4-01 — 清理/导出策略
- 背景与目标：定义本地记忆的清空、导出与留存策略，符合隐私优先原则。
- 前置学习：
  - `docs/troubleshooting.md`
  - `docs/specs/memory_model.md`
- 任务分解：
  - 清空事件与画像文件（规范层）
  - 导出安全副本（mask 处理）
  - 数据留存时间与归档建议
- AC：
  - 给出 CLI 行为定义与示例（文档先行）
  - 明确数据安全与用户同意要求
- 验证步骤：
  - 走查“清理→检查空→导出→导入”的文档流程
