# Sprint 1 — 工作空间与 Prompt 编译器（仅文档）

> 目标：以 BMAD 的“配置驱动”模式，为 PersonalManager 引入项目级 AI 工作空间与 Prompt 编译能力。

## Epic SP1-E1 — 工作空间脚手架与校验

### Story SP1-E1-01 — 生成三件套（脚手架）
- 背景与目标：在项目根目录生成 `.personalmanager/workspace-config.yaml`、`ai-agent-definition.md`、`interaction-patterns.json`。
- 前置学习：
  - `docs/specs/workspace_config.md`
  - `README.md`（AI 工作空间模式章节）
  - `docs/user_guide.md`（AI 工作空间模式章节）
- 任务分解：
  - 定义默认模板内容与最小字段集
  - 幂等创建：存在则跳过；支持 `--force` 覆写（规范层描述逻辑，不实现）
  - 多语言占位（zh/en）与字段注释
- AC（验收标准）：
  - 2 分钟内完成脚手架；若文件已存在不覆写（除非指定）
  - 生成文件均通过 YAML/JSON 基础校验，字段齐备
  - 文档中明确模板示例与字段说明
- 验证步骤（命令/流程）：
  - 检查目录：`ls -la .personalmanager/`
  - 校验语法：`yq . .personalmanager/workspace-config.yaml` / `jq . .personalmanager/interaction-patterns.json`
  - 复查注释与多语言占位

#### 输入/输出样例

**Python 调用示例**：
```python
from pathlib import Path
from pm.workspace import init_workspace

# 初次创建
report = init_workspace(Path("/my/project"))
# 输出：
# ScaffoldReport(
#   success=True,
#   created_files=[
#     '.personalmanager/workspace-config.yaml',
#     '.personalmanager/ai-agent-definition.md',
#     '.personalmanager/interaction-patterns.json'
#   ],
#   skipped_files=[],
#   errors=[],
#   force_mode=False
# )

# 再次运行（幂等）
report = init_workspace(Path("/my/project"))
# 输出：
# ScaffoldReport(
#   success=True,
#   created_files=[],
#   skipped_files=[
#     '.personalmanager/workspace-config.yaml',
#     '.personalmanager/ai-agent-definition.md',
#     '.personalmanager/interaction-patterns.json'
#   ],
#   errors=[],
#   force_mode=False
# )

# 强制覆盖
report = init_workspace(Path("/my/project"), force=True)
# 输出：所有文件重新创建
```

#### 常见错误与修复提示

| 错误场景 | 错误信息 | 修复建议 |
|---------|---------|---------|
| 目录权限不足 | `无法创建工作空间目录: Permission denied` | 检查目录权限，确保有写入权限 |
| 模板文件缺失 | `模板文件不存在: templates/xxx` | 重新安装 PersonalManager 或检查安装完整性 |
| 磁盘空间不足 | `复制文件失败: No space left on device` | 清理磁盘空间后重试 |

### Story SP1-E1-02 — 工作空间状态校验（agent status）
- 背景与目标：提供一致的校验项（文档先行），便于后续 CLI 实现。
- 前置学习：
  - `docs/specs/workspace_config.md`
  - `docs/specs/interaction_patterns.md`
- 任务分解：
  - 定义校验项：存在性、语法、字段、大小限制、路径合法性
  - 定义输出结构：OK/WARN/ERROR 分类，修复建议
- AC：
  - 校验项与结果格式文档化；包含示例输入/输出
  - 指明大小上限与路径规则
- 验证步骤：
  - 以"示例配置"运行文档给出的校验流程（手动/脚本样例）

#### 输入/输出样例

**Python 调用示例**：
```python
from pathlib import Path
from pm.workspace import validate_workspace

# 校验工作空间
report = validate_workspace(Path("/my/project"))

# 成功输出示例：
# ValidationReport(
#   items=[
#     ValidationItem(check='workspace_directory', level='OK', message='.personalmanager 目录存在'),
#     ValidationItem(check='file_exists_workspace-config.yaml', level='OK', message='文件存在: workspace-config.yaml'),
#     ValidationItem(check='yaml_syntax_workspace-config.yaml', level='OK', message='YAML 语法正确'),
#     ValidationItem(check='required_fields_workspace-config.yaml', level='OK', message='所有必填字段存在'),
#     ...
#   ],
#   summary={'ok': 15, 'warn': 0, 'error': 0}
# )

# 错误输出示例：
# ValidationReport(
#   items=[
#     ValidationItem(
#       check='yaml_syntax_workspace-config.yaml',
#       level='ERROR',
#       message='YAML 语法错误: expected <block end>, but found...',
#       suggest='修复 YAML 语法错误，确保缩进和格式正确'
#     ),
#     ValidationItem(
#       check='file_size_interaction-patterns.json',
#       level='WARN',
#       message='文件过大: interaction-patterns.json (65536 > 51200 bytes)',
#       suggest='减少文件内容，保持在 51200 字节以内'
#     ),
#     ...
#   ],
#   summary={'ok': 10, 'warn': 2, 'error': 3}
# )
```

#### 校验项清单

| 校验类别 | 检查项 | 级别 | 说明 |
|---------|--------|------|------|
| **存在性** | workspace_directory | ERROR | .personalmanager 目录必须存在 |
| | file_exists_* | ERROR | 三件套文件必须存在 |
| **语法** | yaml_syntax_* | ERROR | YAML 文件语法必须正确 |
| | json_syntax_* | ERROR | JSON 文件语法必须正确 |
| **必填字段** | required_fields_* | ERROR | 必填字段不能缺失 |
| **文件大小** | file_size_* | WARN | 超出推荐大小限制 |
| | | | workspace-config.yaml: 10KB |
| | | | ai-agent-definition.md: 20KB |
| | | | interaction-patterns.json: 50KB |
| **字段值** | workspace_language | WARN | 语言必须是 zh 或 en |
| | agent_platform | WARN | 平台必须是 claude 或 gemini |
| | privacy_external_calls | WARN | 策略必须是 user_consent 或 deny_all |
| | routing_threshold | ERROR | 阈值必须在 0-1 范围内 |
| **逻辑检查** | routing_threshold | WARN | low_threshold 必须小于 high_threshold |
| | intents_empty | WARN | intents 数组不应为空 |
| | markdown_sections | WARN | 建议包含所有标准章节 |
| **路径检查** | context_path | WARN/ERROR | always_load 中的文件必须存在且是文件 |

#### 常见错误与修复提示

| 错误场景 | 校验结果 | 修复建议 |
|---------|---------|---------|
| 工作空间未初始化 | `workspace_directory: ERROR` | 运行 `init_workspace()` 创建工作空间 |
| YAML 格式错误 | `yaml_syntax_*: ERROR` | 使用 YAML 验证工具检查缩进和语法 |
| JSON 格式错误 | `json_syntax_*: ERROR` | 使用 JSON 格式化工具修复语法 |
| 缺少必填字段 | `required_fields_*: ERROR` | 根据提示添加缺失的字段 |
| 文件过大 | `file_size_*: WARN` | 精简内容或分割文件 |
| 无效枚举值 | `*: WARN` | 使用建议的有效值 |
| 阈值设置错误 | `routing_threshold: ERROR/WARN` | 调整阈值确保 0 ≤ low < high ≤ 1 |
| 引用文件不存在 | `context_path: WARN` | 创建文件或从配置中移除引用 |

## Epic SP1-E2 — Prompt 编译器

### Story SP1-E2-01 — 编译模板与骨架
- 背景与目标：将身份/启动仪式/映射规则/隐私/记忆摘要等编译为短小稳定的项目指令。
- 前置学习：
  - `docs/specs/prompt_compiler.md`
  - `.bmad-core/agents/*.md`（人格/启动模式参考）
- 任务分解：
  - 确定模板骨架与段落次序
  - 记忆摘要注入位置与最大行数（3–5 行）
  - 截断/压缩策略（优先保留规则与映射）
- AC：
  - 产出示例 ≤ 10k 字符；结构稳定
  - 启动仪式仅包含必要动作与提示
- 验证步骤：
  - 在文档中提供“输入示例→输出示例”对照
  - 手动检查段落顺序与大小限制

### Story SP1-E2-02 — 平台落地片段（Claude/Gemini）
- 背景与目标：从同一编译结果生成 Claude/Gemini 的项目级指令片段（不覆盖用户自有配置）。
- 前置学习：
  - `docs/ai_integration_guide.md`
  - `configs/agent-templates/*/settings.sample.json`
- 任务分解：
  - Claude：输出 `.claude/project-instructions.md`
  - Gemini：输出 `~/.gemini/config.json` 追加段
  - 字符集/转义与安全字段过滤
- AC：
  - 示例展示两端产物；不影响原有配置
  - 指定追加策略与安全注意点
- 验证步骤：
  - 本地打开 Claude/Gemini，检查会话开场行为是否符合“启动仪式”

## Epic SP1-E3 — 文档与模板

### Story SP1-E3-01 — 默认模板与示例
- 背景与目标：为三件套提供默认模板与注释，方便用户自定义。
- 前置学习：
  - `docs/specs/workspace_config.md`
  - `docs/specs/interaction_patterns.md`
- 任务分解：
  - 工作空间配置模板（含注释）
  - 常用意图短语库（中英）
- AC：
  - 模板可直接通过语法校验
  - 至少覆盖 5 个核心意图（today/capture/overview/status/explain）
- 验证步骤：
  - 以模板跑一遍“编译→平台片段”示例
