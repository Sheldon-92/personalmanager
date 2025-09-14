# feat(prompt): compiler+platform snippets (no CLI wire)

## 概述
实现 Sprint 1 轨道 B - Prompt 编译器与平台片段生成功能。该功能将工作空间配置编译为精简的项目级系统提示，并生成 Claude/Gemini 平台特定格式。

**注意**: 本 PR 仅包含库模块实现，**不接入 CLI**，CLI 接线工作由轨道 A 负责。

## 变更内容

### 新增文件
- `src/pm/agent/prompt_compiler.py` - Prompt 编译器核心模块
  - `compile_prompt()` - 主编译函数
  - `join_and_truncate()` - 段落合并与截断（< 10k 字符）
  - 6个段落渲染函数（角色、启动、映射、错误、隐私、记忆）

- `src/pm/agent/platform_snippets.py` - 平台片段生成器
  - `to_claude()` - 生成 Claude Markdown 格式
  - `to_gemini()` - 生成 Gemini JSON 配置
  - `to_gemini_script()` - 生成安全追加脚本
  - `validate_platform_output()` - 输出格式验证

### 测试覆盖
- `tests/agent/test_prompt_compiler.py` - 16个测试用例
- `tests/agent/test_platform_snippets.py` - 16个测试用例
- **测试结果**: ✅ 32 passed in 0.12s

### 样例文档
- `docs/samples/prompt_compiler/inputs/` - 输入样例
  - workspace-config.yaml
  - ai-agent-definition.md
  - interaction-patterns.json
  - profile.md

- `docs/samples/prompt_compiler/outputs/` - 输出样例
  - claude_project_instructions.md (3,920 字符)
  - gemini_config_snippet.json (5,137 字符)
  - **总大小**: 9,057 字符 < 10k 限制 ✅

### 文档更新
- `docs/ai_integration_guide.md` - 添加样例链接章节
- `docs/tool_registration.md` - 在意图路由协议下添加样例片段链接

### 清理工作
- 删除 `src/pm/workspace/prompt_compiler.py` - 确保编译器唯一源在 `src/pm/agent/`

## 验收标准达成

| 标准 | 状态 | 说明 |
|------|------|------|
| AC-1 | ✅ | 编译器唯一源：`src/pm/agent/prompt_compiler.py` |
| AC-2 | ✅ | 测试全绿：32 passed |
| AC-3 | ✅ | 文档链接到样例目录，示例可复现 |
| AC-4 | ✅ | PR 明确说明"不接入 CLI" |

## 测试命令
```bash
# 运行测试
pytest tests/agent -q

# 验证样例大小
wc -c docs/samples/prompt_compiler/outputs/*

# 确认唯一源
find . -name "prompt_compiler.py" -type f | grep -v __pycache__
```

## 相关文档
- [Prompt 编译器规范](docs/specs/prompt_compiler.md)
- [意图路由规范](docs/specs/interaction_patterns.md)
- [Sprint 1 计划](docs/roadmap/sprint_1_workspace_prompt.md)

## 注意事项
- 本 PR 不修改 `src/pm/cli/*` 和 `pyproject.toml`
- 不触碰 `src/pm/workspace/*` 其他文件（轨道 A 的地盘）
- 所有样例在 `docs/samples/`，不写入用户真实目录
- 未引入任何外部网络依赖

## 后续工作
- 轨道 A 负责 CLI 接线（`pm agent prompt` 命令）
- Sprint 2 实现意图路由执行
- Sprint 3 实现本地记忆系统