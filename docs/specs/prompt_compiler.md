# Prompt 编译器规范（规划）

> 目标：从工作空间配置与路由/记忆信息生成精简、确定性的项目级系统提示，供 Claude/Gemini 在会话开场加载。

## 输入
- `.personalmanager/workspace-config.yaml`
- `.personalmanager/ai-agent-definition.md`
- `.personalmanager/interaction-patterns.json`
- （可选）内存画像摘要：`~/.personalmanager/data/memory/profile.md`

## 输出
- `.claude/project-instructions.md`
- `~/.gemini/config.json` 追加段（不覆盖原有用户配置）

## 约束
- 大小限制：单端 < 10k 字符（含安全与隐私说明）。
- 风格：短、规则化、编号；少形容词，多规则与命令。
- 只在需要时加载：禁止在开场时引入长文档。

## 模板骨架（示意）
```md
# PersonalManager Expert — Project Instructions

1) 角色与职责（来自 ai-agent-definition.md，精简版）
2) 启动仪式（来自 workspace-config.yaml.startup）
   - 若启用 doctor：执行/展示下一步
   - 若启用 today：执行 pm today --count N
3) 自然语言→命令映射（交互规范）
   - 当用户使用自然语时，优先匹配 `interaction-patterns.json`
   - 低置信度先确认，高置信度可直接执行
4) 错误处理与降级（统一错误码/建议）
5) 安全与隐私（不上传、需同意等）
6) 记忆注入（profile.md 的 3-5 行摘要）
```

## 生成流程（伪代码）
```python
cfg = load_yaml(".personalmanager/workspace-config.yaml")
aid = load_md(".personalmanager/ai-agent-definition.md")
pat = load_json(".personalmanager/interaction-patterns.json")
mem = try_read("~/.personalmanager/data/memory/profile.md")

sections = []
sections.append(render_role(aid))
sections.append(render_startup(cfg.startup))
sections.append(render_mapping_rules(pat, cfg.routing))
sections.append(render_error_contract())
sections.append(render_privacy(cfg.privacy))
sections.append(render_memory(mem))

doc = join_and_truncate(sections, limit=10_000)
write(".claude/project-instructions.md", doc)
write_gemini_snippet(doc)
```

## 验收要点
- 编译成功率 100%，字段缺失能给出清晰提示。
- 产物稳定、可重复生成，不随对话波动变化。
- 端到端配合：Claude/Gemini 会话首句无需额外提示即可进入“专家模式”。
