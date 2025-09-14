# feat(prompt): compiler+platform snippets (no CLI wire)

## 📋 PR Checklist

### ✅ 变更路径清单（轨道 B 负责区域）

**新增文件：**
```
src/pm/agent/
├── prompt_compiler.py      (287 lines, 9.3KB)
└── platform_snippets.py    (211 lines, 6.4KB)

tests/agent/
├── test_prompt_compiler.py (332 lines, 9.1KB)
└── test_platform_snippets.py (304 lines, 9.5KB)

docs/samples/prompt_compiler/
├── inputs/
│   ├── workspace-config.yaml (31 lines, 524B)
│   ├── ai-agent-definition.md (27 lines, 1.1KB)
│   ├── interaction-patterns.json (118 lines, 4.0KB)
│   └── profile.md (5 lines, 315B)
└── outputs/
    ├── claude_project_instructions.md (115 lines, 3.9KB)
    └── gemini_config_snippet.json (113 lines, 5.1KB)
```

**修改文件：**
```
docs/ai_integration_guide.md      (+15 lines, 添加样例资源章节)
docs/tool_registration.md         (+5 lines, 添加样例片段链接)
```

**删除文件：**
```
src/pm/workspace/prompt_compiler.py  (确保编译器唯一源)
```

### ✅ Pytest 结果摘要

```bash
$ python -m pytest tests/agent -q
................................                                         [100%]
32 passed in 0.12s

# 测试分布
- test_prompt_compiler.py: 16 tests ✅
- test_platform_snippets.py: 16 tests ✅

# 关键测试覆盖
- 编译功能 (compile_prompt)
- 段落截断 (join_and_truncate < 10k)
- 平台输出 (to_claude, to_gemini)
- 格式验证 (validate_platform_output)
- 错误处理 (missing files, invalid YAML/JSON)
```

### ✅ 示例输出对照

**输入样例** → **输出样例**

| 输入文件 | 大小 | → | 输出文件 | 大小 |
|---------|------|---|----------|------|
| workspace-config.yaml | 524B | | claude_project_instructions.md | 3,920B |
| ai-agent-definition.md | 1,145B | | gemini_config_snippet.json | 5,137B |
| interaction-patterns.json | 4,044B | | **总输出** | **9,057B < 10k ✅** |
| profile.md | 315B | | | |

**Claude 输出示例片段：**
```markdown
# PersonalManager Expert — Project Instructions

## 1) 角色与职责
- 您是 PersonalManager 专家助手
- 协助用户管理任务和项目
...

## 2) 启动仪式
会话开始时按顺序执行：
1. 执行 `pm doctor` - 系统诊断
2. 执行 `pm today --count 3` - 今日推荐
```

**Gemini 输出示例片段：**
```json
{
  "_comment": "PersonalManager Agent Configuration",
  "personalmanager": {
    "enabled": true,
    "system_prompt": "...",
    "platform_specific": {
      "model_preferences": {
        "temperature": 0.7,
        "max_tokens": 2048
      }
    }
  }
}
```

### ✅ 关联规范链接

- **Prompt 编译器规范**: [docs/specs/prompt_compiler.md](docs/specs/prompt_compiler.md)
- **意图路由规范**: [docs/specs/interaction_patterns.md](docs/specs/interaction_patterns.md)
- **工作空间配置规范**: [docs/specs/workspace_config.md](docs/specs/workspace_config.md)
- **Sprint 1 计划**: [docs/roadmap/sprint_1_workspace_prompt.md](docs/roadmap/sprint_1_workspace_prompt.md) (SP1-E2)

### ✅ 轨道隔离声明

**未触碰轨道 A 文件：**
- ❌ 未修改 `src/pm/cli/*` 任何文件
- ❌ 未修改 `src/pm/workspace/scaffold.py`
- ❌ 未修改 `src/pm/workspace/validate.py`
- ❌ 未修改 `src/pm/workspace/__init__.py`
- ❌ 未修改 `pyproject.toml`

**轨道 B 专属区域：**
- ✅ `src/pm/agent/` - 编译器和平台片段模块
- ✅ `tests/agent/` - 测试套件
- ✅ `docs/samples/prompt_compiler/` - 输入输出样例

### 📝 实现亮点

1. **大小控制**: 严格限制输出 < 10k 字符，优先级截断策略
2. **平台适配**: Claude (Markdown) 和 Gemini (JSON) 分别优化
3. **安全追加**: Gemini 脚本包含备份和验证逻辑
4. **完整测试**: 100% 核心功能覆盖，包括边界条件
5. **样例齐全**: 提供完整输入输出对照，可直接复现

### ⚠️ 重要说明

- **不接入 CLI**: 本 PR 仅实现库模块，CLI 接线由轨道 A 负责
- **唯一源保证**: 已删除 `src/pm/workspace/prompt_compiler.py`，确保唯一源在 `src/pm/agent/`
- **无外部依赖**: 仅使用 Python 标准库 + yaml/json
- **本地运行**: 不写入用户真实目录，样例在 docs/samples

### 🔄 后续工作

- Sprint 1 轨道 A: CLI 接线 (`pm workspace init`, `pm agent prompt`)
- Sprint 2: 意图路由执行 (`pm ai route|execute`)
- Sprint 3: 本地记忆系统 (events.jsonl, profile.md)

---

**分支**: `feat/sprint1-prompt-compiler-platform`
**测试命令**: `pytest tests/agent -q`
**验证命令**: `find . -name "prompt_compiler.py" | grep -v __pycache__`