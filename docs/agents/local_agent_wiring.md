# 项目级 Agent 接入与命令映射（Cloud Code / Gemini COI / Claude）

版本: v1.0
最后更新: 2025-09-14

## 目标
- 在“项目级”无全局安装前提下，让 AI Agent 自动识别并调用 PersonalManager 命令。
- 支持 Cloud Code、Gemini COI、Claude Code 等环境的本地工具调用与降级回退。

## 一、项目内可执行入口

- 新增脚本: `bin/pm-local`
- 行为:
  - 优先执行 `poetry run pm <...>`
  - 回退到 `PYTHONPATH=src python3 -m pm.cli.main <...>`
- 使用:
```bash
./bin/pm-local today
./bin/pm-local projects overview
```

## 二、Claude Code 集成

- 权限文件: `.claude/settings.local.json`
- 已新增通配权限: `Bash(./bin/pm-local:*)`
- 建议调用约定:
  - 统一使用 `./bin/pm-local <cmd>`，避免依赖全局安装与绝对路径
  - 例如: `./bin/pm-local today --count 5`

## 三、Gemini COI/CLI 集成（建议）

- 目录: `.gemini/commands/`
- 建议增加 `pm/` 命令族（或在现有 BMad 命令集中提供 `/pm` 别名任务），将自然语言映射到 `./bin/pm-local`
- 示例任务（伪示例，按你使用的命令格式落地）:
  - `pm/today`: 运行 `./bin/pm-local today --count $COUNT`
  - `pm/projects-overview`: 运行 `./bin/pm-local projects overview`
  - `pm/capture`: 运行 `./bin/pm-local capture "$TEXT"`

> 说明：当前仓库已包含 `.gemini/commands/BMad/*`，你可新增 `pm/` 目录或在 BMad 任务内转发到 `./bin/pm-local`，以达到“自然语言 → 本地命令”的自动映射。

## 四、BMAD/BMAT 框架下的前缀对齐

- `.bmad-core/core-config.yaml` 中 `slashPrefix: BMad` 主要影响 BMAD 自身命令前缀。
- 为避免侵入式修改，可通过“新增 pm 命令族 + 转发脚本”实现 `/pm` 风格的就地可用：
  - 不强制改动 `slashPrefix`；
  - 在 `.gemini/commands/pm` 和 `.claude/commands/pm` 下建立命令映射；
  - 或在现有 BMad 任务集中提供 `/pm` 的别名任务（内部转发到 `./bin/pm-local`）。

## 五、验收标准（AC）
- 不安装任何全局包，在项目根目录：
  - [ ] `./bin/pm-local --version` 输出版本
  - [ ] `./bin/pm-local today` 正常返回推荐（或友好提示要求初始化）
  - [ ] Claude/Gemini 环境中，能直接调用 `./bin/pm-local <cmd>` 并获得真实输出
  - [ ] Agent 层面无需再手写绝对路径或 `PYTHONPATH`，通过通配权限/任务映射自动工作

## 六、常见问题
- 若无 Poetry：脚本自动回退至 `python3 -m pm.cli.main`
- 若 `src/` 不在默认路径：保持脚本相对路径，勿移动 `bin/pm-local`
- 若需要路径白名单：在对应 Agent 权限配置中加入 `Bash(./bin/pm-local:*)`

## 七、下一步（可选增强）
- 生成机器可读的工具清单（如 `.personalmanager-tools.json`），供 Agent 动态加载命令描述与参数信息
- 在 `.gemini/commands/pm` 下分组维护常用命令任务文件，提供 pm 命令帮助/演示工作流

