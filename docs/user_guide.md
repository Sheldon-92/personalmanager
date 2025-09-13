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

