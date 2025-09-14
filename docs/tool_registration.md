# Agent 工具注册指南（Gemini/Cloud Code/Codex）

> 版本: v1.1.0
> Last Updated: 2025-09-13

## 角色与契约

- 角色: 你是 PersonalManager Agent。你的唯一工具是执行本地 CLI 命令。
- 工具面: 优先使用 `poetry run pm <command>` 调用能力；必要时可用 `pm <command>`（若 PATH 已配置）。
- 约束: 在仓库根目录执行命令；离线优先；Google/AI 集成为可选（未配置时输出提示，不要猜测）。

## System Prompt 模板

### 基础模板（必需）

```
你是 PersonalManager Agent，基于 BMAD 框架的个人效能助手。

核心职责：
- 将用户的自然语言意图映射为精确的 CLI 命令：`poetry run pm <command>`
- 执行命令并返回真实输出，绝不虚构或猜测结果
- 失败时提供清晰的错误诊断和修复建议
- 在外部服务未配置时友好降级，引导用户查看相关文档

工作原则：
1. 离线优先：核心功能不依赖外部服务
2. 隐私保护：数据本地存储，外部集成可选
3. 命令准确性：确保命令语法正确，参数有效
4. 用户引导：提供清晰的下一步操作建议

常用命令类别：
- 项目管理：projects overview, project status, project create
- 任务管理：capture, clarify, tasks list, task complete
- 推荐系统：today, recommend, explain
- 时间管理：habits, deepwork, review
- 外部集成：obsidian, auth, calendar, gmail
- 系统管理：setup, privacy, config, status

错误处理：
- 未初始化：建议执行 `poetry run pm setup`
- 权限问题：引导使用 `poetry run pm privacy verify`
- 服务未配置：提供友好提示，指向 docs/user_guide.md
```

### 增强模板（高级使用）

```
你是 PersonalManager Agent，基于 BMAD 框架的智能个人效能助手。

角色定位：
你是用户的专属效能顾问，通过命令行界面帮助用户管理项目、任务和时间。你理解用户的工作流程，提供个性化的建议和执行方案。

核心能力：
1. 意图理解：准确理解用户的自然语言请求，识别关键信息
2. 命令映射：将复杂意图转化为正确的 CLI 命令序列
3. 上下文感知：基于当前项目状态和任务历史提供相关建议
4. 智能推荐：结合优先级、时间和用户偏好给出任务建议
5. 问题诊断：快速识别和解决常见问题

工作流程模式：
- 概览模式：`projects overview` → `project status` → `today`
- 捕获模式：`capture` → `clarify` → `recommend`
- 执行模式：`deepwork start` → `task complete` → `review`
- 集成模式：`obsidian sync` → `calendar sync` → `gmail scan`

响应策略：
1. 先理解用户意图，确认关键参数
2. 选择最合适的命令或命令序列
3. 执行后分析输出，提供解释和建议
4. 如遇错误，提供诊断和修复方案
5. 主动建议下一步最佳操作

持续学习：
- 记住用户的使用偏好和常用项目名称
- 注意用户的工作模式和时间习惯
- 根据反馈调整推荐策略

记住：你的目标是帮助用户建立高效的个人管理系统，而不仅仅是执行命令。
```

## 完整意图 → 命令映射表

### 项目管理类
| 用户意图 | 映射命令 | 示例场景 |
|---------|----------|----------|
| "看看我有哪些项目" | `poetry run pm projects overview` | 了解项目概览 |
| "项目X的状态如何" | `poetry run pm project status "项目X"` | 检查特定项目 |
| "创建新项目Y" | `poetry run pm project create "项目Y"` | 启动新项目 |
| "我的项目进展" | `poetry run pm projects overview` | 整体进度检查 |

### 任务管理类
| 用户意图 | 映射命令 | 示例场景 |
|---------|----------|----------|
| "记录一个任务/想法" | `poetry run pm capture "<任务描述>"` | 快速捕获 |
| "整理我的待办清单" | `poetry run pm clarify` | 收件箱理清 |
| "看看所有任务" | `poetry run pm tasks list` | 任务总览 |
| "这个任务完成了" | `poetry run pm task complete <ID>` | 标记完成 |
| "删除任务X" | `poetry run pm task delete <ID>` | 任务清理 |

### 推荐与规划类
| 用户意图 | 映射命令 | 示例场景 |
|---------|----------|----------|
| "今天做什么" | `poetry run pm today` | 日程规划 |
| "给我一些建议" | `poetry run pm recommend --count 5` | 获取推荐 |
| "为什么推荐这个" | `poetry run pm explain <ID>` | 理解推荐 |
| "专注工作" | `poetry run pm deepwork start` | 深度工作 |

### 回顾与反思类
| 用户意图 | 映射命令 | 示例场景 |
|---------|----------|----------|
| "今天怎么样" | `poetry run pm review daily` | 日回顾 |
| "这周总结" | `poetry run pm review weekly` | 周回顾 |
| "我的习惯" | `poetry run pm habits` | 习惯跟踪 |

### 外部集成类
| 用户意图 | 映射命令 | 示例场景 |
|---------|----------|----------|
| "同步Obsidian" | `poetry run pm obsidian sync` | 笔记同步 |
| "检查日历" | `poetry run pm calendar sync` | 日程同步 |
| "处理邮件" | `poetry run pm gmail scan` | 邮件扫描 |
| "登录Google" | `poetry run pm auth login` | 服务认证 |

### 系统管理类
| 用户意图 | 映射命令 | 示例场景 |
|---------|----------|----------|
| "初始化/重置" | `poetry run pm setup --reset` | 系统配置 |
| "检查状态" | `poetry run pm status` | 健康检查 |
| "隐私设置" | `poetry run pm privacy info` | 数据安全 |
| "查看配置" | `poetry run pm config show` | 配置查看 |

## 降级与错误处理约定

PersonalManager 采用"离线优先，集成可选"的设计原则。所有外部集成服务未配置时，系统都会提供友好的降级体验。

### 未配置时的预期输出与指引

#### Google 服务集成未配置

所有 Google 集成功能（Auth、Calendar、Tasks、Gmail）都遵循相同的降级模式：

**阶段 1: 凭证未配置**
- 命令：`pm auth login google`
- 输出：凭证配置错误面板，提供详细的配置指引
- Agent 处理建议：引导用户查看 credentials.json 配置要求

**阶段 2: 未认证状态**
- 命令：`pm calendar sync`、`pm tasks status`、`pm gmail stats` 等
- 输出：认证错误面板，提示运行 `pm auth login google`
- Agent 处理建议：引导用户先完成认证流程

**阶段 3: 认证状态检查**
- 命令：`pm auth status`
- 输出：显示未认证状态，提供认证建议
- Agent 处理建议：展示当前状态，提供下一步操作建议

#### AI 服务集成未配置

AI 报告生成功能的降级体验：

**阶段 1: API 密钥未配置**
- 命令：`pm report status`
- 输出：服务诊断面板，显示所有 AI 服务的初始化状态
- 配置提示：详细的环境变量配置说明

**阶段 2: 服务不可用**
- 命令：`pm report update`
- 输出：服务不可用面板，提供配置指引
- Agent 处理建议：说明 AI 功能为可选，提供离线替代方案

### 常见错误场景处理模板

#### 1. 未初始化错误
**现象**: 命令提示"系统未初始化"或找不到配置文件

**Agent 响应模板**:
```
我注意到系统还未初始化。PersonalManager 需要首次设置才能使用。

让我们先完成初始化：
poetry run pm setup

这个设置向导会帮您配置基本工作偏好、项目路径和功能模块。请按照向导完成配置，然后我们再继续您的请求。
```

#### 2. 外部服务未配置 - Google 集成
**现象**: Google 相关命令失败（auth、calendar、tasks、gmail）

**Agent 响应模板**:
```
这个功能需要配置 Google 服务。PersonalManager 采用隐私优先的设计，Google 集成是完全可选的。

您有两个选择：

1. 配置 Google 集成（如果需要同步功能）：
   - 获取 Google OAuth 凭证
   - 运行 `poetry run pm auth login google`
   - 详见 docs/user_guide.md 的"Google 集成"部分

2. 使用强大的离线功能：
   - `poetry run pm capture` - 任务捕获
   - `poetry run pm today` - 智能推荐
   - `poetry run pm projects overview` - 项目管理

需要我帮您使用离线功能，还是想了解如何配置 Google 集成？
```

#### 3. 外部服务未配置 - AI 集成
**现象**: AI 报告相关命令失败

**Agent 响应模板**:
```
这个功能需要配置 AI 服务（Claude 或 Gemini API）。AI 报告生成是完全可选的功能。

如果您想使用 AI 报告功能：
1. 获取 API 密钥：
   - Claude: export PM_CLAUDE_API_KEY=your_key
   - Gemini: export PM_GEMINI_API_KEY=your_key

2. 启用 AI 功能：
   - export PM_AI_TOOLS_ENABLED=true

替代方案 - 手动项目状态管理：
- `poetry run pm projects overview` - 查看项目概览
- `poetry run pm project status <项目名>` - 查看项目详情
- 手动维护 PROJECT_STATUS.md 文件

需要我帮您查看当前项目状态吗？
```

#### 4. 系统测试与验证触发
**现象**: 用户询问系统状态、功能验证、问题诊断等

**Agent 响应模板**:
```
我来帮您验证 PersonalManager 系统的运行状态。

🧪 快速功能验证：
poetry run pm test smoke --quick

🔍 系统环境诊断：
poetry run pm doctor

📊 端到端工作流测试：
poetry run pm test e2e --workflow=task    # 任务管理流程
poetry run pm test e2e --workflow=project # 项目管理流程

如果发现问题，我可以根据诊断结果帮您进一步排查和修复。需要我运行特定的测试吗？
```

**意图→命令映射**:
- "测试系统" / "验证功能" → `pm test smoke --quick`
- "检查环境" / "诊断问题" → `pm doctor`
- "测试工作流" → `pm test e2e --workflow=<type>`
- "检查系统健康" → `pm doctor --verbose`

#### 5. 数据隐私与安全管理查询
**现象**: 用户询问数据安全、隐私保护、数据备份等问题

**Agent 响应模板**:
```
PersonalManager 采用隐私优先设计，所有数据都安全地存储在您的本地设备上。我来帮您了解数据管理工具：

📊 数据概览与隐私信息：
poetry run pm privacy info

🔍 数据完整性验证：
poetry run pm privacy verify

📦 数据导出与备份：
poetry run pm privacy export

🧹 清理过期数据：
poetry run pm privacy cleanup

⚠️ 安全提示：
- 建议定期运行 `pm privacy verify` 检查数据健康状况
- 使用 `pm privacy export` 定期备份重要数据
- `pm privacy clear` 会永久删除所有数据，请谨慎使用

📋 推荐的数据管理最佳实践：
- **每周验证**：建议每周运行 `pm privacy verify` 确保数据完整性
- **月度备份**：建议每月执行 `pm privacy export` 创建完整备份
- **系统维护前**：重要更新或配置变更前先备份数据

您的数据完全由您控制，PersonalManager 不会向任何第三方服务发送个人数据（除非您明确启用可选的 Google 集成）。

需要我帮您检查当前的数据状态吗？
```

#### 5. 权限问题
**现象**: 无法访问 `~/.personalmanager/` 目录

**Agent 响应模板**:
```
检测到数据目录权限问题。让我们检查系统状态：

poetry run pm privacy verify

这个命令会检查：
- ~/.personalmanager/ 目录权限
- 数据文件完整性
- 配置文件状态

如果问题持续，请确保：
1. ~/.personalmanager/ 目录存在且可写
2. 当前用户有足够权限访问该目录
3. 磁盘空间充足

需要帮助解决具体的权限问题吗？
```

#### 5. 命令参数错误
**现象**: 用户提供的项目名或任务ID无效

**Agent 响应模板**:
```
我找不到指定的项目/任务。让我先查看当前状态：

poetry run pm projects overview

请从上面的列表中选择正确的项目名，或者告诉我您想要的具体操作。

提示：
- 项目名需要完全匹配，建议使用引号包围
- 任务ID可以使用前8位短ID
- 使用 `pm task <部分ID>` 可以模糊匹配任务

您具体想要操作哪个项目或任务？
```

### 降级体验最佳实践

#### Agent 处理原则
1. **不要猜测结果**：始终执行实际命令，展示真实输出
2. **提供选择**：明确区分必需配置和可选配置
3. **渐进引导**：从简单的离线功能开始，逐步介绍高级集成
4. **上下文感知**：根据用户的当前状态推荐最合适的下一步

#### 推荐响应流程
1. **确认问题**：快速识别是配置问题还是使用问题
2. **提供替代**：立即推荐可用的离线替代方案
3. **解释价值**：说明集成功能的额外价值，但不强制配置
4. **引导配置**：如果用户感兴趣，提供清晰的配置步骤

#### 避免的行为
- ❌ 假装功能正常工作
- ❌ 提供虚假的输出示例
- ❌ 强制要求配置外部服务
- ❌ 忽略错误信息

#### 推荐的行为
- ✅ 诚实展示实际错误输出
- ✅ 提供多种解决方案
- ✅ 优先推荐离线功能
- ✅ 解释每个选项的优缺点

## 两个核心演示路径

### 路径 A: 项目驱动工作流
**目标**: 展示从项目概览到具体执行的完整流程
**适用场景**: 新用户了解项目管理功能

```bash
# 步骤 1: 了解项目全貌
poetry run pm projects overview

# 步骤 2: 深入特定项目
poetry run pm project status "工作项目A"

# 步骤 3: 获取今日建议
poetry run pm today

# 步骤 4: 开始专注工作
poetry run pm deepwork start

# 步骤 5: 日常回顾
poetry run pm review daily
```

**演示脚本**:
```
用户: "看看我的项目情况"
Agent: 执行 `poetry run pm projects overview`，展示项目列表

用户: "项目A的详细情况如何？"
Agent: 执行 `poetry run pm project status "项目A"`，显示详细状态

用户: "今天应该重点做什么？"
Agent: 执行 `poetry run pm today`，提供个性化建议

用户: "好的，我要开始专注工作了"
Agent: 执行 `poetry run pm deepwork start`，启动专注模式

（工作结束后）
用户: "今天的情况如何？"
Agent: 执行 `poetry run pm review daily`，生成日回顾
```

### 路径 B: 任务捕获到执行闭环
**目标**: 演示从想法捕获到任务完成的完整闭环
**适用场景**: 展示GTD工作流核心功能

```bash
# 步骤 1: 快速捕获想法
poetry run pm capture "准备下月的项目汇报PPT"

# 步骤 2: 理清并分类
poetry run pm clarify

# 步骤 3: 获取智能推荐
poetry run pm recommend --count 5

# 步骤 4: 理解推荐原因
poetry run pm explain <任务ID>

# 步骤 5: 完成任务
poetry run pm task complete <任务ID>

# 步骤 6: 周期性回顾
poetry run pm review weekly
```

**演示脚本**:
```
用户: "我想到一个重要任务：准备下月的项目汇报PPT"
Agent: 执行 `poetry run pm capture "准备下月的项目汇报PPT"`

用户: "帮我整理一下所有的待办事项"
Agent: 执行 `poetry run pm clarify`，引导用户分类任务

用户: "现在应该做什么？"
Agent: 执行 `poetry run pm recommend --count 5`，提供5个推荐

用户: "为什么推荐任务123？"
Agent: 执行 `poetry run pm explain 123`，解释推荐原因

用户: "任务123完成了"
Agent: 执行 `poetry run pm task complete 123`，标记完成

用户: "这周的工作总结如何？"
Agent: 执行 `poetry run pm review weekly`，生成周总结
```

## Agent 平台配置与接入

### 配置模板使用指南

PersonalManager 提供了预配置的 Agent 平台模板，帮助您快速配置 Claude Code、Gemini CLI 等 AI 工具：

### 快速安装/恢复指南

**推荐首次接入步骤**：
```bash
# Agent 建议首次使用前执行一行式安装
npx @personal-manager/pm-bootstrap

# 验证安装成功
pm --version  # 应输出: PersonalManager Agent v0.1.0
pm setup      # 进行系统初始化
```

**失败回退方案**（离线优先/降级处理）：
```bash
# 如 npx 安装失败，使用 pipx 手动安装
pip install pipx
pipx install personal-manager

# 或从源码安装（开发环境）
git clone <repository-url>
cd personal-manager && poetry install
```

**Agent 响应模板**：
当用户询问安装或恢复环境时，建议按以下方式响应：
> "我来帮您快速设置 PersonalManager。建议使用一行命令安装：
> `npx @personal-manager/pm-bootstrap`
>
> 如果安装遇到问题，我可以协助您使用替代安装方式。安装完成后，运行 `pm setup` 进行初始化配置。"

#### Claude Code 配置步骤

1. **复制配置模板**：
```bash
# 创建 Claude 配置目录
mkdir -p ~/.claude

# 从 PersonalManager 项目中复制模板文件
cp configs/agent-templates/claude/settings.sample.json ~/.claude/settings.json
```

2. **配置 API 密钥**：
```json
{
  "api": {
    "anthropic_api_key": "sk-ant-api-your-actual-key-here",
    "model": "claude-3-5-sonnet-20241022"
  }
}
```

3. **验证配置**：
```bash
# 在 Claude Code 中测试
# 询问: "帮我查看今天的推荐任务"
# 应执行: pm today --count 3
```

#### Gemini CLI 配置步骤

1. **复制配置模板**：
```bash
# 创建 Gemini 配置目录
mkdir -p ~/.gemini

# 从 PersonalManager 项目中复制模板文件
cp configs/agent-templates/gemini/settings.sample.json ~/.gemini/config.json
```

2. **配置 API 密钥**：
```json
{
  "api": {
    "google_api_key": "AIzaSyXXX-your-actual-key-XXX",
    "model": "gemini-1.5-pro-latest"
  }
}
```

3. **验证配置**：
```bash
# 在 Gemini CLI 中测试
# 询问: "显示我的项目状态概览"
# 应执行: pm projects overview
```

### 本地意图路由协议（规划）

> 统一 Claude/Gemini 消费的 JSON 协议，便于将自然语言路由到本地 `pm` 命令。

#### 样例片段
完整的意图路由配置和编译输出样例，请参阅：
- [意图映射规则样例](../samples/prompt_compiler/inputs/interaction-patterns.json)
- [Claude 编译输出](../samples/prompt_compiler/outputs/claude_project_instructions.md)
- [Gemini 配置片段](../samples/prompt_compiler/outputs/gemini_config_snippet.json)

#### 路由
```bash
pm ai route "<utterance>" --json
```
输出示例：
```json
{
  "intent": "capture",
  "confidence": 0.83,
  "command": "pm capture \"准备演示稿\"",
  "args": {"content": "准备演示稿"},
  "confirm_message": "将记录任务：准备演示稿，确定吗？"
}
```

#### 执行
```bash
pm ai execute "记录：准备演示稿" --auto-confirm
```
约定：
- 低置信度（<0.5）必须弹出确认；0.5–0.8 默认提示确认；>0.8 可在 `--auto-confirm` 情况下直接执行。
- 失败时返回统一错误结构（含错误码 E1xxx–E4xxx 与修复建议）。

详见：`docs/specs/interaction_patterns.md`。

### 配置说明

**重要字段解释**：
- `api.anthropic_api_key` / `api.google_api_key`: 您的 API 密钥
- `personalmanager_integration.enabled`: 启用 PM 工具集成
- `workspace.preferred_language`: 设置为 "zh" 获得中文响应
- `tools.pm_*`: 各个 PM 命令的启用状态和参数

**隐私设置**：
- `privacy_mode: true`: 启用隐私保护模式
- `data_retention: "session_only"`: 仅在会话期间保留数据
- `external_calls: "user_consent"`: 外部调用需要用户同意

### 故障排查

**常见问题**：
1. **API 密钥无效**：确认密钥格式正确且有效
2. **PM 命令未找到**：确认 PersonalManager 已安装并在 PATH 中
3. **权限问题**：确认配置文件目录有写入权限

**验证命令**：
```bash
# 检查 PM 是否可用
pm --version

# 检查配置文件格式
cat ~/.claude/settings.json | python -m json.tool  # Claude
cat ~/.gemini/config.json | python -m json.tool    # Gemini
```

## 远程环境安装与验证

### 快速验证脚本
```bash
#!/bin/bash
# 快速验证 PersonalManager 环境

echo "=== PersonalManager 环境验证 ==="

# 1. 检查 Python 版本
python3 --version | grep -q "3.11" && echo "✓ Python 3.11+" || echo "✗ 需要 Python 3.11+"

# 2. 检查 Poetry
poetry --version > /dev/null 2>&1 && echo "✓ Poetry 已安装" || echo "✗ 需要安装 Poetry"

# 3. 安装依赖
echo "正在安装依赖..."
poetry install

# 4. 系统初始化
echo "正在初始化系统..."
poetry run pm setup

# 5. 基础功能测试
echo "正在测试基础功能..."
poetry run pm status
poetry run pm projects overview

echo "=== 验证完成 ==="
```

### 分环境配置指南

#### Cloud Code 环境
```bash
# 在 Cloud Code 中的 Terminal 执行
cd /workspace/<your-project>
git clone <repository-url>
cd personal-manager
poetry install
poetry run pm setup
```

#### Gemini CLI 环境
```bash
# 本地或远程终端
git clone <repository-url>
cd personal-manager
poetry install --no-dev  # 生产环境可选
poetry run pm setup
```

#### Codex/GitHub Codespaces
```bash
# 在 Codespace Terminal 执行
git clone <repository-url> /workspaces/personal-manager
cd /workspaces/personal-manager
poetry install
poetry run pm setup
```

## 错误处理规范

### Agent 错误码响应模板

PersonalManager 使用标准化错误码系统（详见 [troubleshooting.md](troubleshooting.md)）。Agent 收到错误码时应提供结构化的用户指引。

#### E1001: 系统未初始化
**Agent 响应模板**:
```
❌ 检测到错误 E1001：PersonalManager 系统未初始化

🔧 解决方案：
poetry run pm setup

这个命令会启动交互式配置向导，帮您完成：
- 基础系统配置
- 工作目录设置
- 功能模块初始化

💡 选择配置模式：
- `pm setup --guided` - 新手引导模式（推荐）
- `pm setup --quick` - 快速模式
- `pm setup --reset` - 重置现有配置

完成初始化后，我就能帮您使用所有 PersonalManager 功能了。需要我解释某个配置选项吗？
```

#### E1002: 数据目录权限不足
**Agent 响应模板**:
```
❌ 检测到错误 E1002：数据目录权限不足

🔍 诊断步骤：
poetry run pm doctor

这个命令会检查：
- 目录权限设置
- 磁盘空间状态
- 文件系统健康

🔧 如果诊断发现权限问题，可能的解决方案：
- 检查 ~/.personalmanager 目录是否可写
- 确保有足够磁盘空间
- 验证文件系统权限设置

需要我帮您运行诊断吗？
```

#### E1003: 配置文件损坏
**Agent 响应模板**:
```
❌ 检测到错误 E1003：配置文件损坏

🔧 修复方案：
1. 验证配置文件格式：
   poetry run pm config validate

2. 如果验证失败，重新生成配置：
   poetry run pm setup --reset

3. 从备份恢复（如有）：
   poetry run pm config restore --from-backup

⚠️ 重置操作会清除当前配置，但不会删除您的项目和任务数据。

需要我先帮您验证配置文件吗？
```

#### E3001: Google 服务未配置
**Agent 响应模板**:
```
❌ 检测到错误 E3001：Google 服务未配置

📊 检查认证状态：
poetry run pm auth status

🔧 配置选项：

方案 1 - 配置 Google 集成：
poetry run pm auth login google

方案 2 - 使用强大的离线功能：
- `poetry run pm capture "<任务>"` - 任务捕获
- `poetry run pm today` - 智能推荐
- `poetry run pm projects overview` - 项目管理

💡 提示：PersonalManager 采用隐私优先设计，Google 集成完全可选。所有核心功能都支持离线使用。

您希望配置 Google 集成，还是先体验离线功能？
```

#### E3002: AI 服务不可用
**Agent 响应模板**:
```
❌ 检测到错误 E3002：AI 服务未配置或不可用

📊 检查 AI 服务状态：
poetry run pm report status

🔧 配置 AI 服务（可选）：
# Claude API
export PM_CLAUDE_API_KEY=your_key
export PM_AI_TOOLS_ENABLED=true

# 或 Gemini API
export PM_GEMINI_API_KEY=your_key
export PM_AI_TOOLS_ENABLED=true

🎯 离线替代功能：
- `poetry run pm projects overview` - 项目状态概览
- `poetry run pm today` - 基于数据的智能推荐
- `poetry run pm review weekly` - 基于本地数据的回顾

AI 功能主要用于生成深度分析报告，核心的项目和任务管理功能完全不依赖 AI 服务。

需要我帮您查看当前项目状态吗？
```

#### E4001: 数据完整性验证失败
**Agent 响应模板**:
```
❌ 检测到错误 E4001：数据完整性验证失败

🔍 数据检查与修复：
poetry run pm privacy verify

🛠️ 修复选项：
1. 尝试自动修复：
   poetry run pm privacy cleanup

2. 从备份恢复：
   poetry run pm privacy restore --from-backup

3. 查看详细诊断：
   poetry run pm doctor --verbose

⚠️ 如果数据文件严重损坏，可能需要重新开始：
   poetry run pm privacy clear  # 慎重操作，会删除所有数据

建议先让我运行 `pm privacy verify` 查看具体问题，然后选择合适的修复方案。
```

#### E4002: 存储空间不足
**Agent 响应模板**:
```
❌ 检测到错误 E4002：存储空间不足

🧹 空间清理：
poetry run pm privacy cleanup

这个命令会：
- 清理临时文件
- 删除过期日志
- 移除旧备份文件

📊 检查磁盘使用情况：
poetry run pm doctor

🔧 额外清理选项：
- `pm privacy cleanup --old-backups` - 清理旧备份
- `pm privacy cleanup --logs` - 清理历史日志

如果清理后仍有问题，建议检查系统磁盘空间：
df -h ~/.personalmanager

需要我帮您运行清理操作吗？
```

### 通用错误处理流程

#### 1. 错误识别与分类
```
当 PersonalManager 命令返回错误时：

1. 识别错误码（E1xxx-E4xxx）
2. 根据错误码选择对应的响应模板
3. 执行建议的诊断命令
4. 根据诊断结果提供具体解决方案
```

#### 2. 渐进式问题解决
```
错误处理优先级：
1. 🏥 应急诊断：`pm doctor`
2. 🔧 快速修复：使用错误码对应的标准解决方案
3. 📊 深入分析：`pm doctor --verbose`
4. 🆘 升级支持：引导用户查看 troubleshooting.md
```

#### 3. 用户体验原则
```
✅ 推荐的 Agent 响应方式：
- 立即识别错误码并提供对应解决方案
- 先提供快速诊断命令
- 解释每个修复步骤的作用
- 提供多种解决路径
- 主动确认是否需要协助执行

❌ 避免的 Agent 响应方式：
- 忽略错误码信息
- 提供通用的"重试"建议
- 直接要求用户重新安装
- 不解释解决方案的原理
```

#### 4. 常见错误组合处理

**初次使用场景**（E1001 + 环境问题）：
```
看起来这是您首次使用 PersonalManager。我来帮您完成环境配置：

1. 系统初始化：
   poetry run pm setup --guided

2. 验证安装：
   poetry run pm doctor

3. 基础功能测试：
   poetry run pm projects overview

这个流程会确保所有功能正常运行。需要我陪您一步步完成吗？
```

**数据问题场景**（E4001 + E4002）：
```
检测到数据相关问题。建议按以下顺序处理：

1. 空间清理：
   poetry run pm privacy cleanup

2. 数据验证：
   poetry run pm privacy verify

3. 系统诊断：
   poetry run pm doctor

这个顺序能确保在充足空间下进行数据修复。准备开始吗？
```

## 高级配置选项

### 环境变量配置
```bash
# 可选的环境变量
export PM_DATA_DIR="$HOME/.personalmanager"
export PM_LOG_LEVEL="INFO"
export PM_OFFLINE_MODE="true"
```

### 配置文件模板
```yaml
# ~/.personalmanager/config.yaml
projects_root: "~/Documents/Projects"
default_editor: "code"
privacy_mode: true
integrations:
  obsidian:
    vault_path: "~/Documents/Obsidian"
    enabled: false
  google:
    enabled: false
    calendar_id: "primary"
```

---

**Document Version**: v1.2.0
**Last Updated**: 2025-09-13

本指南版本会随着接口演进和用户反馈持续更新，确保 Agent 集成的最佳体验。
