# Sprint 2 — 意图路由与执行

> 目标：实现自然语言到 `pm` 命令的路由与执行，支持多语言、槽位提取、置信度判断与用户确认机制。

## Epic SP2-E1 — 路由协议与核心命令

### Story SP2-E1-01 — 意图路由命令 `pm ai route`
- **背景与目标**：将自然语言映射到具体的 `pm` 命令，输出结构化 JSON
- **前置依赖**：
  - `.personalmanager/interaction-patterns.json` 意图配置
  - `src/pm/workspace/validate.py` 验证工作空间
- **实现要点**：
  - 命令：`pm ai route "<utterance>" --json`
  - 输出结构：`{intent, confidence, command, args, confirm_message}`
  - 支持短语匹配和正则提取
  - 置信度计算：短语精确匹配=1.0，部分匹配=0.5-0.8，正则匹配=0.3-0.7
- **AC（验收标准）**：
  - 5个核心意图命中率 ≥ 90%
  - JSON 输出可解析且字段完整
  - 未匹配时返回 null intent 和 confidence=0

### Story SP2-E1-02 — 意图执行命令 `pm ai execute`
- **背景与目标**：执行路由后的命令，支持确认机制
- **前置依赖**：
  - `pm ai route` 路由功能
  - 现有 `pm` 命令体系
- **实现要点**：
  - 命令：`pm ai execute "<utterance>" [--auto-confirm]`
  - 执行流程：路由 → 确认 → 执行 → 结果摘要
  - 确认策略：
    - confidence < 0.5：强制用户确认
    - 0.5 ≤ confidence < 0.8：默认显示确认提示
    - confidence ≥ 0.8：`--auto-confirm` 时可直接执行
  - 退出码：成功=0，路由失败=1，执行失败=2，用户取消=3
- **AC**：
  - 确认机制按置信度分级工作
  - 执行结果有清晰摘要
  - 退出码语义正确

## Epic SP2-E2 — 多语言短语库与槽位

### Story SP2-E2-01 — 核心意图短语库
- **背景与目标**：完善5个核心意图的中英文短语库
- **核心意图**：
  1. `today`: 今日推荐
  2. `capture`: 任务捕获
  3. `projects_overview`: 项目概览
  4. `project_status`: 单项目状态
  5. `explain`: 解释推荐
- **实现要点**：
  - 扩充 `interaction-patterns.json` 中的 phrases
  - 每个意图至少10个中英文变体
  - 支持口语化表达（"今天干啥"、"what's up today"）
- **AC**：
  - 覆盖常见表达方式
  - 中英文均衡（各占50%）

### Story SP2-E2-02 — 槽位提取与正则
- **背景与目标**：从自然语言中提取命令参数
- **槽位示例**：
  - `capture`: 提取任务内容
  - `project_status`: 提取项目名称
  - `explain`: 提取任务ID
- **实现要点**：
  - 使用命名捕获组：`(?<content>.+)`
  - 支持中英文混合内容
  - 处理引号和特殊字符
- **AC**：
  - 槽位提取准确率 ≥ 85%
  - 支持包含空格的项目名

## 验收指标

### 功能指标
- 5个核心意图 UAT 命中率 ≥ 90%
- 槽位提取准确率 ≥ 85%
- 确认机制分级正确

### 性能指标
- 路由响应时间 < 100ms
- 执行命令额外开销 < 50ms

### 质量指标
- 测试覆盖率 ≥ 80%
- 文档完整性 100%
- 无已知严重bug

## 交付物清单

### 代码
- `src/pm/cli/commands/ai_router.py`
- `src/pm/routing/intent_matcher.py`
- `src/pm/routing/executor.py`

### 测试
- `tests/cli/test_cli_ai_router.py`
- `tests/routing/test_intent_matcher.py`

### 文档
- 更新 `docs/user_guide.md`
- 添加 `docs/samples/ai_router/`
- 更新 `CHANGELOG.md`
