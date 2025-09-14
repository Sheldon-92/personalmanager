# PersonalManager 用户指南

> 版本: v1.1.0
> Last Updated: 2025-09-13

## 概览

PersonalManager 是基于 BMAD 框架的"无头 + CLI + Agent 可调用"的个人效能工具包。推荐在远程环境用 Cloud Code、Gemini CLI 或 Codex 打开 Terminal，由 Agent 将自然语言映射为本地 `pm` 命令。

## 安装与初始化

- 系统要求: Python 3.11，Poetry 1.6+（开发环境）
- 安装
```bash
git clone <repository-url>
cd personal-manager
poetry install
```
- 初始化
```bash
poetry run pm setup
```
说明: 首次可跳过 Google/AI 配置；默认离线可用。配置文件与数据位于 `~/.personalmanager/`。

## 命令-功能对照表

| 功能类别 | 命令 | 功能说明 | 示例 |
|---------|------|----------|------|
| **项目管理** | `pm projects overview` | 查看所有项目概览 | `poetry run pm projects overview` |
| | `pm project status <项目名>` | 查看特定项目状态 | `poetry run pm project status "工作项目A"` |
| | `pm project create <项目名>` | 创建新项目 | `poetry run pm project create "新项目"` |
| **任务管理** | `pm capture <任务描述>` | 快速捕获任务或想法 | `poetry run pm capture "准备周报"` |
| | `pm clarify` | 理清收件箱中的任务 | `poetry run pm clarify` |
| | `pm tasks list` | 列出所有任务 | `poetry run pm tasks list` |
| | `pm task complete <任务ID>` | 标记任务完成 | `poetry run pm task complete 123` |
| **推荐系统** | `pm today` | 获取今日重点任务 | `poetry run pm today` |
| | `pm recommend` | 获取任务推荐 | `poetry run pm recommend --count 5` |
| | `pm explain <任务ID>` | 解释推荐原因 | `poetry run pm explain 456` |
| **时间管理** | `pm habits` | 管理习惯追踪 | `poetry run pm habits` |
| | `pm deepwork start` | 开始深度工作 | `poetry run pm deepwork start` |
| | `pm review daily` | 日回顾 | `poetry run pm review daily` |
| | `pm review weekly` | 周回顾 | `poetry run pm review weekly` |
| **外部集成** | `pm obsidian status` | 检查 Obsidian 集成状态 | `poetry run pm obsidian status` |
| | `pm obsidian sync` | 同步 Obsidian 笔记 | `poetry run pm obsidian sync` |
| | `pm auth login` | Google 服务认证 | `poetry run pm auth login` |
| | `pm calendar sync` | 同步 Google 日历 | `poetry run pm calendar sync` |
| | `pm gmail scan` | 扫描 Gmail 邮件 | `poetry run pm gmail scan` |
| **系统管理** | `pm setup` | 初始化系统配置 | `poetry run pm setup --reset` |
| | `pm privacy info` | 查看隐私信息 | `poetry run pm privacy info` |
| | `pm privacy verify` | 验证数据权限 | `poetry run pm privacy verify` |
| | `pm config show` | 显示当前配置 | `poetry run pm config show` |
| | `pm status` | 系统状态检查 | `poetry run pm status` |

## 完整工作流程：从 0 到 1 演练

### 步骤 1: 概览 - 了解全局状态

```bash
# 查看系统状态
poetry run pm status

# 查看所有项目概览
poetry run pm projects overview

# 检查隐私设置
poetry run pm privacy info
```

**目标**: 了解当前系统状态，确认项目结构和数据安全。

### 步骤 2: 捕获 - 收集任务和想法

```bash
# 快速捕获一个任务
poetry run pm capture "准备下周的项目汇报"

# 捕获更多任务
poetry run pm capture "整理桌面文件"
poetry run pm capture "回复客户邮件"
poetry run pm capture "学习新的 Python 框架"
```

**目标**: 将脑海中的各种任务和想法快速记录到系统中。

### 步骤 3: 理清 - 组织和分类任务

```bash
# 理清收件箱中的所有任务
poetry run pm clarify

# 查看任务列表确认分类效果
poetry run pm tasks list
```

**目标**: 对捕获的任务进行分类、优先级设定和项目归属。

### 步骤 4: 推荐 - 获取智能建议

```bash
# 获取今日重点任务
poetry run pm today

# 获取更多推荐任务（5个）
poetry run pm recommend --count 5

# 解释推荐原因（假设任务ID为123）
poetry run pm explain 123
```

**目标**: 基于优先级、时间和上下文获取个性化的任务推荐。

### 步骤 5: 解释 - 理解和执行

```bash
# 查看特定项目的详细状态
poetry run pm project status "工作项目A"

# 开始深度工作会话
poetry run pm deepwork start

# 完成任务后标记
poetry run pm task complete 123
```

**目标**: 深入理解推荐背后的逻辑，高效执行重要任务。

### 完整演练示例（10分钟体验）

```bash
# 1. 初始化（30秒）
poetry run pm setup
poetry run pm status

# 2. 快速捕获（1分钟）
poetry run pm capture "写月度总结报告"
poetry run pm capture "安排下月项目计划"
poetry run pm capture "整理个人知识库"

# 3. 理清收件箱（2分钟）
poetry run pm clarify

# 4. 查看推荐（1分钟）
poetry run pm today
poetry run pm recommend --count 3

# 5. 开始工作（5分钟）
poetry run pm deepwork start
# 执行实际工作...

# 6. 回顾总结（30秒）
poetry run pm review daily
```

### 高级工作流程

#### A. 项目驱动流程
```bash
# 查看项目概览
poetry run pm projects overview

# 专注特定项目
poetry run pm project status "重要项目X"

# 获取项目相关推荐
poetry run pm today

# 执行和回顾
poetry run pm deepwork start
poetry run pm review daily
```

#### B. 任务驱动流程
```bash
# 批量捕获任务
poetry run pm capture "任务1"
poetry run pm capture "任务2"
poetry run pm capture "任务3"

# 理清和组织
poetry run pm clarify

# 获取推荐并执行
poetry run pm recommend --count 5
poetry run pm explain <选中任务ID>

# 标记完成
poetry run pm task complete <任务ID>
```

## Obsidian 集成（MVP）

- 目标: 与 Obsidian 知识库连接，读写 `PROJECT_STATUS.md` 等笔记/状态文件。
- 最小验证
```bash
poetry run pm obsidian status
# 或根据你的库路径执行同步/读取命令
```
注意: 具体命令以 `pm obsidian` 子命令内为准；首次使用前在 `pm setup` 中设置根路径或在配置文件中补充。

## Google 与 AI 集成（可选）

- 默认关闭 Google 集成（隐私优先）。如需启用：
```bash
poetry run pm auth login
poetry run pm calendar sync
poetry run pm gmail scan
```
未配置或无网络时，相关命令会输出友好提示与指引（不崩溃）。

## 隐私与数据安全

PersonalManager 提供完整的数据隐私管理工具，确保您对个人数据的完全控制：

```bash
# 查看隐私信息和数据存储位置
poetry run pm privacy info

# 验证数据完整性和权限设置
poetry run pm privacy verify

# 导出所有个人数据（可用于备份或迁移）
poetry run pm privacy export

# 清理过期或冗余数据
poetry run pm privacy cleanup

# ⚠️ 危险操作：完全清除所有数据
poetry run pm privacy clear  # 请谨慎使用
```

**安全提示**：
- 定期运行 `pm privacy verify` 检查数据完整性
- 使用 `pm privacy export` 定期备份重要数据
- `pm privacy clear` 将永久删除所有数据，无法恢复，请谨慎使用

**推荐的最佳实践**：
- **每周验证**：建议每周运行一次 `pm privacy verify` 确保数据健康
- **月度备份**：建议每月执行 `pm privacy export` 创建数据备份
- **重要操作前备份**：在执行系统更新或重要配置变更前，先备份数据

### 未配置时的预期输出与指引

PersonalManager 采用离线优先设计，所有外部集成都是可选的。当您尝试使用未配置的集成时，系统会提供友好的降级体验：

#### Google 服务认证

**命令**: `pm auth status`
**未配置时输出**:
```
╭──────────────────────────────── 🔐 认证状态 ─────────────────────────────────╮
│ 服务            认证状态    详细信息
│ Google Services ❌ 未认证   未认证
╰──────────────────────────────────────────────────────────────────────────────╯
╭──────────────────────────────── 🔑 认证提示 ─────────────────────────────────╮
│ ⚠️ 需要认证Google服务
│
│ 请运行以下命令进行认证：
│ pm auth login google
╰──────────────────────────────────────────────────────────────────────────────╯
```

**命令**: `pm auth login google`
**未配置凭证时输出**:
```
╭────────────────────────────── ❌ 凭证配置错误 ───────────────────────────────╮
│ Google OAuth凭证未配置
│
│ 请确保已将Google OAuth凭证文件放置在：
│ ~/.personalmanager/credentials.json
│
│ 凭证文件应包含以下格式：
│ {
│   "web": {
│     "client_id": "your-client-id",
│     "client_secret": "your-client-secret"
│   }
│ }
│
│ 或简化格式：
│ {
│   "client_id": "your-client-id",
│   "client_secret": "your-client-secret"
│ }
╰──────────────────────────────────────────────────────────────────────────────╯
```

#### Google Calendar 集成

**命令**: `pm calendar sync`, `pm calendar today`
**未认证时输出**:
```
╭──────────────────────────────── ❌ 认证错误 ─────────────────────────────────╮
│ 未通过Google认证。请先运行：pm auth login google
╰──────────────────────────────────────────────────────────────────────────────╯
```

#### Google Tasks 集成

**命令**: `pm tasks status`, `pm tasks sync-from`
**未认证时输出**:
```
╭──────────────────────────────── ❌ 认证错误 ─────────────────────────────────╮
│ 未通过Google认证。请先运行：pm auth login google
╰──────────────────────────────────────────────────────────────────────────────╯
```

#### Gmail 集成

**命令**: `pm gmail stats`, `pm gmail scan`
**未认证时输出**:
```
╭──────────────────────────────── ❌ 认证错误 ─────────────────────────────────╮
│ 未通过Google认证。请先运行：pm auth login google
╰──────────────────────────────────────────────────────────────────────────────╯
```

#### AI 报告生成

**命令**: `pm report status`
**未配置API密钥时输出**:
```
╭────────────────────────────────── 服务诊断 ──────────────────────────────────╮
│ 🤖 AI服务状态检查
╰──────────────────────────────────────────────────────────────────────────────╯
❌ Claude: 未初始化
   错误: API key not found or initialization failed
❌ Gemini: 未初始化
   错误: API key not found or initialization failed

💡 配置提示:
• Claude API: export PM_CLAUDE_API_KEY=your_key
• Gemini API: export PM_GEMINI_API_KEY=your_key
• AI功能启用: export PM_AI_TOOLS_ENABLED=true
```

**命令**: `pm report update`
**未配置AI服务时输出**:
```
╭──────────────────────────────── AI服务不可用 ────────────────────────────────╮
│ ❌ 没有可用的AI服务
│
│ 请检查API密钥配置：
│ • Claude: export PM_CLAUDE_API_KEY=your_key
│ • Gemini: export PM_GEMINI_API_KEY=your_key
│
│ 或在配置文件中设置相应的API密钥。
╰──────────────────────────────────────────────────────────────────────────────╯
```

### 离线替代方案

即使未配置外部集成，PersonalManager 仍提供强大的离线功能：

**项目管理**: 完全离线可用
- `pm projects overview` - 项目概览
- `pm project status <项目名>` - 项目状态

**任务管理**: 完全离线可用
- `pm capture <任务>` - 任务捕获
- `pm inbox` - 收件箱查看
- `pm clarify` - 任务理清
- `pm next` - 下一步行动

**智能推荐**: 完全离线可用
- `pm today` - 今日推荐
- `pm recommend` - 智能推荐
- `pm explain <ID>` - 推荐解释

**习惯管理**: 完全离线可用
- `pm habits` - 习惯跟踪
- `pm deepwork` - 深度工作

**系统功能**: 完全离线可用
- `pm setup` - 系统设置
- `pm privacy` - 隐私管理
- `pm status` - 系统状态

## Agent 和远程调用

### 概览

PersonalManager 作为"无头 + CLI + Agent 可调用"的个人效能工具包，专门设计用于与 AI Agent 协作。通过项目级启动器 `./bin/pm-local`，AI Agent 可以无缝调用 PersonalManager 的所有功能，将自然语言需求转换为具体的个人效能管理操作。

### 项目级启动器

#### 使用 ./bin/pm-local

项目级启动器是 PersonalManager 的标准化入口点，支持智能环境检测和自适应执行：

```bash
# 基本命令格式（Agent 使用）
./bin/pm-local <command> [arguments]

# 环境诊断（调试时使用）
./bin/pm-local --launcher-debug
```

**环境自适应**：
- 优先使用 Poetry 环境：`poetry run pm <command>`
- 回退到直接 Python 执行：`PYTHONPATH=src python3 -m pm.cli.main <command>`

#### 与 poetry run pm 的对比

| 特性 | `./bin/pm-local` | `poetry run pm` |
|------|------------------|-----------------|
| **Agent 兼容性** | ✅ 完美支持 | ⚠️ 需要额外配置 |
| **环境检测** | ✅ 自动检测 | ❌ 需要 Poetry |
| **错误处理** | ✅ 友好提示 | ❌ Poetry 原生错误 |
| **调试支持** | ✅ 内置调试模式 | ❌ 无调试功能 |
| **跨环境** | ✅ 支持多种环境 | ❌ 仅 Poetry 环境 |

### Claude Code 集成

#### 使用场景

在 Claude Code 环境中，您可以通过自然语言描述个人效能需求，Claude 会自动转换为相应的 PersonalManager 命令。

#### 典型交互流程

**场景 1：项目管理**
```
用户：帮我查看所有项目的状态，并重点关注优先级高的项目

Claude 执行：
1. ./bin/pm-local projects overview
2. 分析输出结果
3. ./bin/pm-local project status "高优先级项目名称"
4. 提供个性化建议
```

**场景 2：任务工作流**
```
用户：我想添加一些任务，然后看看今天应该重点做什么

Claude 执行：
1. ./bin/pm-local capture "用户描述的任务1"
2. ./bin/pm-local capture "用户描述的任务2"  
3. ./bin/pm-local clarify
4. ./bin/pm-local today
5. 解释推荐原因
```

**场景 3：深度工作会话**
```
用户：帮我安排一个专注的工作时段，我需要完成重要的写作任务

Claude 执行：
1. ./bin/pm-local deepwork create "重要写作任务"
2. ./bin/pm-local deepwork start
3. 提供专注工作建议
4. （工作完成后）./bin/pm-local deepwork end
```

#### Claude Code 优势

- **上下文理解**：Claude 能理解复杂的多步骤需求
- **智能解析**：自动将自然语言转换为准确的命令
- **结果分析**：对命令输出进行智能分析和解释
- **错误处理**：自动处理命令执行中的异常情况
- **工作流编排**：组合多个命令实现复杂工作流

### Gemini CLI 集成

#### 配置方式

**基本配置**：
```bash
# 在项目根目录启动 Gemini CLI
cd /path/to/personal-manager
gemini chat

# 或者配置工具调用
gemini chat --tools ./bin/pm-local
```

**高级配置**：
```yaml
# ~/.config/gemini/tools.yaml（如果支持）
tools:
  - name: "personal_manager"  
    command: "./bin/pm-local"
    description: "PersonalManager 个人效能工具集"
    working_directory: "/path/to/personal-manager"
```

#### 使用示例

**任务管理对话**：
```
用户：帮我管理今天的任务

Gemini：我来帮您管理今天的任务。让我先查看您当前的情况：

./bin/pm-local today

基于这些推荐，您想要：
1. 开始执行某个特定任务？
2. 添加新的任务？
3. 重新组织任务优先级？

用户：我想添加"准备明天的演示文稿"这个任务

Gemini：好的，我为您添加这个任务：

./bin/pm-local capture "准备明天的演示文稿"

任务已添加！让我帮您进行理清分类：

./bin/pm-local clarify

现在让我重新查看更新后的今日推荐：

./bin/pm-local today
```

**项目状态检查**：
```
用户：帮我了解项目进展情况

Gemini：我来帮您查看项目状态：

./bin/pm-local projects overview

看起来您有几个项目在进行中。让我为您详细查看需要关注的项目：

./bin/pm-local project status "项目A"
./bin/pm-local project status "项目B"

基于这些信息，我建议您优先关注...
```

#### Gemini CLI 特色

- **对话式交互**：支持持续的对话式项目管理
- **多轮任务规划**：在对话中逐步细化和完善任务
- **实时状态跟踪**：动态跟踪项目和任务状态变化
- **个性化建议**：基于历史对话提供个性化建议

### 远程环境最佳实践

#### 1. 环境准备

**项目设置**：
```bash
# 确保在正确的项目目录
cd /path/to/personal-manager

# 验证启动器可用性
./bin/pm-local --launcher-debug

# 初始化配置（首次使用）
./bin/pm-local setup
```

**权限配置**：
```bash
# 确保启动器可执行
chmod +x ./bin/pm-local

# 验证环境完整性
./bin/pm-local privacy verify
```

#### 2. Agent 交互技巧

**明确意图表达**：
- ✅ "帮我查看今天的重点任务并开始第一个任务"
- ❌ "看看任务"

**提供上下文**：
- ✅ "我正在做网站重构项目，帮我添加相关的测试任务"
- ❌ "添加任务"

**分步骤操作**：
- ✅ "先查看项目状态，然后基于状态添加必要的任务"
- ❌ "帮我处理所有项目相关的事情"

#### 3. 常用工作流模式

**每日启动流程**：
```bash
# 1. 系统状态检查
./bin/pm-local status

# 2. 项目概览
./bin/pm-local projects overview

# 3. 获取今日推荐
./bin/pm-local today

# 4. 开始重点工作
./bin/pm-local deepwork start
```

**任务管理流程**：
```bash  
# 1. 快速捕获想法
./bin/pm-local capture "临时想到的任务"

# 2. 理清收件箱
./bin/pm-local clarify

# 3. 获取智能推荐
./bin/pm-local recommend --count 5

# 4. 解释推荐原因
./bin/pm-local explain <任务ID>
```

**项目推进流程**：
```bash
# 1. 查看特定项目状态
./bin/pm-local project status "项目名称"

# 2. 添加项目相关任务
./bin/pm-local capture "项目相关任务描述"

# 3. 开始深度工作会话
./bin/pm-local deepwork create "项目专注时段"

# 4. 记录工作成果
./bin/pm-local deepwork end
```

#### 4. 错误处理

**常见错误及解决**：

```bash
# 权限错误
chmod +x ./bin/pm-local

# 环境检测失败
./bin/pm-local --launcher-debug

# 模块导入错误
poetry install  # 或 pip install 相关依赖
```

**Agent 错误恢复**：
- 如果 Agent 执行命令失败，可以要求显示详细错误信息
- 使用 `./bin/pm-local --help` 查看可用命令
- 使用 `./bin/pm-local status` 检查系统状态

### 高级 Agent 功能

#### 1. 智能工作流编排

Agent 可以根据上下文自动编排复杂的工作流：

```bash
# 完整的项目管理工作流
./bin/pm-local projects overview && \
./bin/pm-local project status "关键项目" && \
./bin/pm-local capture "项目紧急任务" && \
./bin/pm-local today && \
./bin/pm-local explain <推荐任务ID>
```

#### 2. 条件执行逻辑

Agent 可以基于命令结果进行条件判断：

```bash
# 根据项目健康度决定后续操作
if ./bin/pm-local project status "项目A" | grep -q "Good"; then
    ./bin/pm-local capture "项目A优化任务"
else
    ./bin/pm-local capture "项目A风险缓解任务"
fi
```

#### 3. 数据分析和报告

Agent 可以分析 PersonalManager 的输出并生成洞察：

```bash
# 获取数据并分析
./bin/pm-local projects overview > /tmp/projects.txt
./bin/pm-local habits today > /tmp/habits.txt

# Agent 分析数据并提供：
# - 项目健康度趋势
# - 习惯完成率统计  
# - 个人效能改进建议
```

### 故障排查

#### Agent 集成问题

**问题**：Agent 无法执行 PersonalManager 命令
**解决步骤**：
1. 确认当前目录：`pwd`
2. 检查启动器：`ls -la bin/pm-local`  
3. 测试权限：`./bin/pm-local --help`
4. 环境诊断：`./bin/pm-local --launcher-debug`

**问题**：命令执行但无响应
**解决步骤**：
1. 检查系统状态：`./bin/pm-local status`
2. 验证配置：`./bin/pm-local privacy verify`
3. 重新初始化：`./bin/pm-local setup --reset`

#### 性能优化

**启动器性能**：
```bash
# 测量启动时间
time ./bin/pm-local --version

# 对比不同执行方式
time poetry run pm --version
time PYTHONPATH=src python3 -m pm.cli.main --version
```

**Agent 响应优化**：
- 使用具体的命令而不是通用查询
- 避免同时执行多个重量级操作
- 定期清理过期数据：`./bin/pm-local privacy cleanup`

### 总结

通过 Agent 和远程调用功能，PersonalManager 实现了真正的"自然语言驱动"个人效能管理。无论是使用 Claude Code 的智能上下文理解，还是 Gemini CLI 的对话式交互，都能让您专注于描述需求，而让 AI Agent 处理具体的技术执行细节。

这种设计哲学让个人效能管理变得更加直观和高效，真正实现了"心如止水"的理想状态——您只需表达意图，系统会智能地处理其余工作。

## 配置说明

### 语言字段配置

PersonalManager 使用两个语言相关的配置字段：

- **`preferred_language`** (推荐使用): 主要语言字段，用于 Agent 通信和用户界面
  - 取值: `zh` (中文) 或 `en` (英文)
  - 默认值: `zh`
  - 配置位置: `~/.personalmanager/config.yaml`

- **`language`** (兼容性字段): 用于向后兼容，保持与旧版本的兼容性
  - 取值: `zh-CN`, `en-US` 等标准语言代码
  - 默认值: `zh-CN`
  - 主要用于内部系统和历史数据处理

**使用建议**:
- 新用户和新配置应使用 `preferred_language` 字段
- `language` 字段主要用于系统兼容性，通常无需手动修改
- 两个字段会自动保持同步，修改任一字段都会相应更新另一个字段

### 配置文件示例

```yaml
# 推荐的语言配置方式
preferred_language: zh  # 主要字段
language: zh-CN        # 兼容性字段，自动设置

# 其他配置...
work_hours_start: 9
work_hours_end: 18
timezone: Asia/Shanghai
```

## 常见问题（FAQ）

- 命令无法找到 `pm`？使用 `poetry run pm` 或将虚拟环境的 bin 加入 PATH。
- 初始化后仍提示"未初始化"？运行 `poetry run pm setup --reset` 并按向导填写 `projects_root`。
- 权限/目录问题？确保 `~/.personalmanager/` 可写；参考 `pm privacy verify` 与 `pm setup` 验证结果。
- 语言配置混乱？使用 `preferred_language` 作为主要配置字段，`language` 字段会自动同步。

---
本指南会随功能决策与实现同步更新，以确保“文档即产品”。

