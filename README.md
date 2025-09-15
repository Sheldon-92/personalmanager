# PersonalManager - AI驱动的个人效能管理系统

**PersonalManager** 是一个基于项目本地化的AI个人效能工具，通过自然语言交互管理任务、项目、习惯和专注力。采用项目本地化架构，避免全局污染，支持斜杠命令和编号选择的交互方式。

**当前版本**: v0.4.0-rc1 (2025-09-15)

---

## 🎯 核心特性

### 新增功能 (v0.4.0)
- **💬 交互模式**: 斜杠命令 (`/pm`, `/gmail`, `/task`) 和编号选择界面
- **📊 双向简报**: 用户工作简报 + Claude技术简报的高密度信息展示
- **🔗 Obsidian深度集成**: 7个子命令完整同步习惯、项目和笔记
- **🚀 项目本地化**: 所有功能在项目目录内运行，无需全局安装

### 基础功能
- **✅ GTD任务管理**: 完整的收件箱、理清、下一步行动工作流
- **🎯 习惯养成**: 基于《原子习惯》的习惯跟踪系统
- **📂 项目管理**: 以报告为中心的项目状态跟踪
- **🧠 智能推荐**: AI驱动的每日任务推荐
- **🔗 Google集成**: Calendar、Tasks、Gmail无缝同步

---

## 🚀 快速开始

### 1. 克隆并进入项目

```bash
git clone https://github.com/Sheldon-92/personalmanager.git
cd personal-manager
```

### 2. 项目本地化使用（推荐）

```bash
# 使用Poetry环境（自动检测）
./bin/pm-local --version

# 或直接使用Python
PYTHONPATH=src python3 -m pm.cli.main --version
```

### 3. 快捷命令

```bash
# 斜杠命令快捷方式
./bin/pm-briefing       # 生成双向简报
./bin/pm-interactive    # 启动交互模式
./bin/pm-inbox          # 查看任务收件箱
./bin/pm-quick          # 快速命令菜单
```

---

## 💡 使用方式

### 交互模式（推荐）

启动交互模式，支持斜杠命令和编号选择：

```bash
./bin/pm-interactive
# 或
./start_interactive.sh
```

在交互模式中：
- 输入 `/` 查看所有斜杠命令
- 输入 `/pm` 生成简报
- 输入 `/gmail` 预览邮件
- 输入数字选择操作（如 1,2,3 或 1-3）

### 命令行模式

```bash
# 基础命令格式
./bin/pm-local <command> [options]

# 常用命令示例
./bin/pm-local briefing         # 生成双向简报
./bin/pm-local inbox            # 查看收件箱
./bin/pm-local today            # 今日任务推荐
./bin/pm-local capture "任务"   # 快速捕获任务
```

#### **项目管理**
- `pm projects overview`: 查看所有项目的状态概览。
- `pm project status <项目名>`: 查看单个项目的详细状态。
- `pm monitor start`: 在后台启动对 `PROJECT_STATUS.md` 文件的自动监控。

#### **任务管理 (GTD)**
- `pm capture "任务内容"`: 快速捕获任务到收件箱。
- `pm inbox`: 查看收件箱中待处理的任务。
- `pm clarify`: 启动交互式GTD理清流程。
- `pm next`: 查看下一步行动清单。

#### **智能推荐**
- `pm today`: 获取今日重点推荐（默认返回不超过3项）。
- `pm recommend --count 5`: 获取更丰富的任务推荐列表。
- `pm explain <任务ID>`: 解释某条推荐背后的决策逻辑。

#### **习惯养成**
- `pm habits create "习惯名称"`: 创建一个新习惯。
- `pm habits track "习惯名称"`: 记录一次习惯完成情况。
- `pm habits today`: 查看今日习惯计划。

#### **深度工作**
- `pm deepwork create "时段标题"`: 创建一个深度工作时段。
- `pm deepwork start <时段ID>`: 开始一个深度工作时段。
- `pm deepwork end`: 结束当前时段并进行反思。

#### **回顾与反思**
- `pm review weekly`: 创建或查看每周回顾。
- `pm review project "项目名称"`: 对一个已完成的项目进行复盘。

#### **Google 集成**
- `pm auth login`: 登录并授权Google服务。
- `pm calendar sync`: 同步Google Calendar日程为任务。
- `pm gmail scan`: 扫描重要邮件并创建任务。

---

## `PROJECT_STATUS.md` - 报告驱动的项目管理

本系统的一大特色是“以报告为中心”的项目管理。您无需在复杂的UI中点击，只需在您的项目文件夹下创建一个 `PROJECT_STATUS.md` 文件，用自然语言描述项目状态即可。

**一份简单的 `PROJECT_STATUS.md` 示例:**

```markdown
# 项目：个人网站重构

## 状态
- **进度**: 75%
- **健康度**: 良好 (Good)
- **优先级**: 高 (High)
- **最后更新**: 2025-09-15

## 下一步行动
- [ ] 修复Safari浏览器的动画卡顿问题。
- [ ] 完成移动端响应式布局的最后调整。

## 风险与问题
- 动画问题可能会影响最终上线时间。
```

系统会自动发现并解析此文件，并在 `pm projects overview` 中展示。详细的编写方法请参考 `docs/PROJECT_STATUS_GUIDE.md`。

---

## 技术架构

- **核心理念**: AI原生、工具化、方法论驱动
- **主要框架**: Python, Typer, Rich
- **数据存储**: 本地文件系统 (JSON, Markdown)
- **核心依赖**: `watchdog` (文件监控), `pydantic` (数据建模)

---

## 更新日志

查看详细的版本更新历史和功能变更，请参阅 [CHANGELOG.md](CHANGELOG.md)。

---

## 文档与流程规范

- 产品角色与职责（PO Persona）: docs/prompts/po_persona_and_responsibilities.md
- 产品负责人工作流程（PO Playbook）: docs/prompts/po_operational_playbook.md
- Phase 5 RC 专项修复计划: docs/phase_5_rc_fix_plan.md
- RC 用户快速试用指南: docs/quickstart_rc_user_testing.md
- 用户试用反馈模板: docs/USER_FEEDBACK_TEMPLATE.md
  

---
