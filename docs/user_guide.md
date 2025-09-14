# PersonalManager 用户指南

> 版本: v1.1.0
> Last Updated: 2025-09-13

## 概览

PersonalManager 是基于 BMAD 框架的"无头 + CLI + Agent 可调用"的个人效能工具包。推荐在远程环境用 Cloud Code、Gemini CLI 或 Codex 打开 Terminal，由 Agent 将自然语言映射为本地 `pm` 命令。

## 安装与初始化

### npx 一行式安装（推荐）

最快速的安装方式，适合新用户和远程环境：

```bash
# 一行命令自动安装 PersonalManager
npx @personal-manager/pm-bootstrap

# 指定版本安装
npx @personal-manager/pm-bootstrap --version v0.1.0
```

**平台注意事项**：
- **macOS/Linux**: 安装后可能需要重启终端或运行 `source ~/.bashrc` 使 PATH 生效
- **Windows**: 如提示 PATH 问题，请重启命令行或使用完整路径 `pipx run pm --version`

**故障排查**：
- **缺少 Python**: 先安装 Python 3.9+ (`python --version`)
- **缺少 pipx**: 自动安装失败时，手动安装 `pip install pipx`
- **网络问题**: 使用 `--source git` 参数从源码安装
- **权限问题**: 在用户目录使用 `pipx install --user` 模式

### 开发环境安装

适合贡献者和高级用户：

- 系统要求: Python 3.11，Poetry 1.6+（开发环境）
- 安装
```bash
git clone <repository-url>
cd personal-manager
poetry install
```

### 系统初始化

PersonalManager 提供三种初始化模式，适应不同用户需求：

#### 初始化模式说明

**引导模式（推荐新用户）**:
```bash
pm setup --guided
```
- 分步骤交互式配置向导
- 详细解释每个配置项的作用
- 提供配置建议和示例
- 适合：首次使用者、需要详细了解配置项的用户

**快速模式（默认）**:
```bash
pm setup --quick
# 或简写
pm setup
```
- 使用智能默认值，最小化用户输入
- 只询问必需的配置项
- 跳过高级和可选配置
- 适合：有一定经验的用户、快速部署场景

**高级模式（专家用户）**:
```bash
pm setup --advanced
```
- 暴露所有配置选项
- 支持自定义高级设置
- 允许精确控制系统行为
- 适合：技术用户、企业定制场景

#### 重要操作确认

系统会在危险操作前要求确认：

**数据清除确认**:
```
⚠️ 危险操作确认
您即将清除所有现有配置和数据。此操作不可恢复！

现有数据位置: ~/.personalmanager/
包含内容: 配置文件, 任务数据, 项目信息, 习惯记录

是否继续？请输入 "DELETE" 确认: _
```

**配置重置确认**:
```
🔄 配置重置确认
这将重置系统配置为默认值，但保留用户数据。

要重置的配置: 项目路径, 语言设置, 集成配置
保留的数据: 任务, 项目状态, 习惯记录

确认重置配置？[y/N]: _
```

#### 失败分支修复建议

如果初始化失败，可以尝试以下修复方案：

**常见问题诊断**:
```bash
# 运行系统诊断
pm doctor

# 检查具体问题
pm doctor --verbose
```

**权限问题修复**:
```bash
# 检查数据目录权限
pm privacy verify

# 手动修复权限（Linux/macOS）
chmod 755 ~/.personalmanager
chmod 644 ~/.personalmanager/config.yaml
```

**配置文件问题**:
```bash
# 重新生成配置文件
pm setup --reset

# 从备份恢复配置
pm config restore --from-backup
```

**依赖环境问题**:
```bash
# 检查 Python 环境
python --version  # 需要 >= 3.9

# 检查必要命令
which git  # 必须可用
```

参见 [系统诊断与修复](#系统诊断) 获取完整的问题排查指南。

**说明**: 首次可跳过 Google/AI 配置；默认离线可用。配置文件与数据位于 `~/.personalmanager/`。

## AI 工作空间模式（稳定可用）

> 通过项目级配置与编译器，让 Agent 在进入目录后即具备 PersonalManager 专家身份，自动执行"启动仪式"，并将自然语言路由为本地 `pm` 命令。

**注意**：接口可能在后续小版本中优化

### 产物与位置
- `.personalmanager/workspace-config.yaml`：工作空间与启动仪式配置
- `.personalmanager/ai-agent-definition.md`：角色/方法/交互规范
- `.personalmanager/interaction-patterns.json`：自然语言意图→`pm` 映射
- `.claude/project-instructions.md` / `~/.gemini/config.json` 片段：编译产物

### 核心功能

#### 工作空间初始化

```bash
# 初始化工作空间（生成三件套配置文件）
pm workspace init

# 强制覆盖已存在的文件
pm workspace init --force

# 指定自定义根目录
pm workspace init --root /path/to/project
```

**示例输出**：
```
🚀 初始化工作空间
📁 目标目录: /my/project

📋 操作结果
✅ .personalmanager/workspace-config.yaml    创建
✅ .personalmanager/ai-agent-definition.md   创建
✅ .personalmanager/interaction-patterns.json 创建

✨ 初始化成功
✅ 成功创建 3 个文件

下一步操作：
1. 编辑 .personalmanager/workspace-config.yaml 自定义配置
2. 运行 pm agent status 验证工作空间
3. 查看 pm help workspace 了解更多命令
```

#### 工作空间状态检查

```bash
# 人类可读模式（默认）
pm agent status

# JSON 输出模式（适合程序化消费）
pm agent status --json

# 指定自定义根目录
pm agent status --root /path/to/project
```

**人类可读输出示例**：
```
🔍 工作空间状态检查
📁 检查目录: /my/project

📋 检查结果
workspace_directory           ✅ 通过  .personalmanager 目录存在
file_exists_workspace-config  ✅ 通过  文件存在: workspace-config.yaml
yaml_syntax_workspace-config  ✅ 通过  YAML 语法正确
...

✅ 检查通过
工作空间配置完全正常

统计：
• 通过: 15
• 警告: 0
• 错误: 0
```

**JSON 输出示例**：
```json
{
  "items": [
    {
      "check": "workspace_directory",
      "level": "OK",
      "message": ".personalmanager 目录存在"
    },
    ...
  ],
  "summary": {
    "ok": 15,
    "warn": 0,
    "error": 0
  }
}
```

**退出码语义**：
- `0` - 验证通过或仅有警告
- `1` - 存在错误

### Prompt 编译

```bash
# 编译并打印项目指令
pm agent prompt --print

# 编译并写入平台配置文件
pm agent prompt --write
```

### 意图路由与执行（即将推出）

```bash
# 路由自然语言到命令
pm ai route "今天做什么" --json

# 执行自然语言命令
pm ai execute "记录：改进界面"
pm ai execute "记录：改进界面"
```

### 使用流程（建议）
1) 运行 `pm setup` 完成系统初始化
2) 在项目根目录运行 `pm workspace init` 与 `pm agent prompt --write`
3) 在 Claude/Gemini 打开该目录，会话开场即读取项目指令
4) 直接用自然语言对话，Agent 将路由到 `pm` 命令（低置信度先确认）

> 以上为文档先行的设计与规范，具体实现以后续版本为准。

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

> 规划中的命令参考（仅文档，不代表当前版本提供）：`pm workspace init`、`pm agent prompt --print|--write`、`pm agent status`、`pm ai route|execute`。

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

## AI Agent 平台集成

### Claude Code / Gemini CLI 配置

PersonalManager 支持与主流 AI Agent 平台深度集成，提供配置模板和快速设置指南：

#### 快速配置步骤

**1. 选择您的 AI 平台**：
- Claude Code：企业级 AI 编程助手
- Gemini CLI：Google 的多模态 AI 工具

**2. 使用配置模板**：

PersonalManager 提供预配置模板文件，无需从零开始配置：

```bash
# Claude Code 配置 (从 PersonalManager 项目复制)
mkdir -p ~/.claude
cp configs/agent-templates/claude/settings.sample.json ~/.claude/settings.json

# Gemini CLI 配置 (从 PersonalManager 项目复制)
mkdir -p ~/.gemini
cp configs/agent-templates/gemini/settings.sample.json ~/.gemini/config.json
```

模板包含所有必要字段和推荐配置，您只需要替换 API 密钥即可。

**3. 配置 API 密钥**：
```bash
# 编辑配置文件，替换示例 API 密钥为您的真实密钥
# Claude: 替换 "anthropic_api_key" 字段
# Gemini: 替换 "google_api_key" 字段
```

**4. 验证集成**：
在您的 AI 平台中询问：
- "帮我查看今天的推荐任务" (Claude Code)
- "显示我的项目状态概览" (Gemini CLI)

#### 支持的集成功能

- **任务管理**: `pm capture`, `pm today`, `pm recommend`
- **项目管理**: `pm projects overview`, `pm project status`
- **数据同步**: 自动获取当前项目上下文
- **智能推荐**: 基于 AI 的任务优先级建议

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

## 测试与验证 (Test & Validation)

PersonalManager 提供完整的测试与验证体系，确保系统稳定性和功能正确性：

### 冒烟测试 (Smoke Tests)

快速验证系统核心功能是否正常工作：

```bash
# 快速冒烟测试（约2分钟）
pm test smoke --quick

# 完整冒烟测试（约5分钟）
pm test smoke --full
```

**目标**: 检查所有主要 CLI 命令的基础功能，包括成功路径和常见失败场景。

**示例输出**:
```
🔍 PersonalManager 冒烟测试
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ 基础命令测试      pm --version, pm --help
✅ 配置系统测试      pm setup --check, pm config show
✅ 任务管理测试      pm capture, pm inbox, pm next
✅ 项目管理测试      pm projects overview
✅ 隐私系统测试      pm privacy info, pm privacy verify
⚠️  外部集成测试      Google 服务未配置，跳过

📊 测试结果: 5/6 通过 | 退出码: 0
```

**退出码规则**:
- `0`: 所有核心功能正常（外部集成失败不影响）
- `1`: 存在核心功能问题
- `2`: 测试执行错误

### 端到端测试 (End-to-End Tests)

验证完整工作流程的功能性：

```bash
# 项目管理工作流测试
pm test e2e --workflow=project

# 任务管理工作流测试
pm test e2e --workflow=task

# 时间管理工作流测试
pm test e2e --workflow=time
```

**工作流程与预期**:

**项目管理流程**:
```
概览 → 状态 → 推荐
pm projects overview → pm project status <name> → pm recommend
```

**任务管理流程**:
```
捕获 → 理清 → 推荐 → 解释
pm capture → pm clarify → pm recommend → pm explain <id>
```

**时间管理流程**:
```
深度工作 → 习惯 → 回顾
pm deepwork create → pm habits today → pm review weekly
```

### CI/CD 集成建议

在 GitHub Actions 中集成 PersonalManager 测试：

```yaml
# .github/workflows/test.yml
name: PersonalManager Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Install PersonalManager
        run: |
          npx @personal-manager/pm-bootstrap
          pm setup --quick

      - name: Run Smoke Tests
        run: pm test smoke --quick

      - name: Run E2E Tests
        run: |
          pm test e2e --workflow=project
          pm test e2e --workflow=task
```

### 系统诊断

除了功能测试，还可以使用诊断工具检查环境：

```bash
# 系统环境诊断
pm doctor

# 详细系统信息
pm doctor --verbose

# 尝试自动修复问题
pm doctor --fix
```

参见 [系统诊断指南](#系统诊断与修复) 了解更多诊断选项。

## 常见问题（FAQ）

- 命令无法找到 `pm`？使用 `poetry run pm` 或将虚拟环境的 bin 加入 PATH。
- 初始化后仍提示"未初始化"？运行 `poetry run pm setup --reset` 并按向导填写 `projects_root`。
- 权限/目录问题？确保 `~/.personalmanager/` 可写；参考 `pm privacy verify` 与 `pm setup` 验证结果。
- 语言配置混乱？使用 `preferred_language` 作为主要配置字段，`language` 字段会自动同步。

---
**Document Version**: v1.2.0
**Last Updated**: 2025-09-13

本指南会随功能决策与实现同步更新，以确保"文档即产品"。
