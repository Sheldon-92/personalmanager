# PersonalManager v0.5.0 - AI-Powered Productivity Platform

**PersonalManager** has evolved from a traditional GTD task manager to an intelligent productivity platform. Through Session-based work tracking, smart time-blocking, and AI-assisted decision making, it solves the core time management challenges faced by knowledge workers.

**Current Version**: v0.5.0 (100% Complete - All 6 Sprints Delivered)

---

## 📖 完整项目文档
👉 **[项目总览](docs/PROJECT_OVERVIEW.md)** - 了解项目使命、架构和价值
👉 **[项目现状](PROJECT_STATUS_CORRECTED.md)** - 当前进展和真实状态
👉 **[快速上手](docs/user-guides/QUICK_REFERENCE_V05.md)** - 5分钟入门指南
👉 **[模板系统指南](docs/user-guides/templates.md)** - 批量操作和模板管理完整指南

---

## 🎯 核心特性

### 🆕 v0.5.0 Complete Feature Set
- **🤖 AI Decision Engine**: Intelligent "what should I work on now?" recommendations
- **📁 Project Management System**: 5 intelligent project types (Exploratory, Rhythmic, Goal, Iterative, Habitual)
- **⏱️ Session-Based Work Tracking**: 25-90 minute focus sessions with 5 specialized modes
- **💰 Time Budget Management**: Financial-inspired time allocation and tracking
- **📅 Smart Time-Block Planning**: Conflict-free scheduling with energy optimization
- **⚡ Automated Workflows**: Background activity tracking and intelligent automation
- **📊 Comprehensive Analytics**: Deep productivity insights and pattern recognition
- **🔗 Seamless GTD Integration**: Tasks and projects unified with full backward compatibility

### 🤖 Sprint 6: AI-Powered Decision Making (NEW)
- **🧠 Intelligent Recommendations**: AI suggests optimal next actions based on energy, deadlines, and patterns
- **📊 Productivity Pattern Analysis**: Discovers your peak performance times and work rhythms
- **⚡ Smart Break Timing**: Fatigue-aware break recommendations and activity suggestions
- **🎯 AI-Guided Focus Sessions**: Optimal task selection for focus periods
- **🔍 Decision Explanations**: Transparent reasoning behind all AI recommendations
- **📈 Learning System**: Continuously improves through user feedback and pattern recognition
- **📋 JSON API Support**: All commands support `--json` for programmatic integration
- **⚡ Non-Interactive Mode**: Use `--assume-no` or `--yes` for automated workflows

### 📅 Sprint 4: Smart Time-Block Planning
- **📅 Interactive Schedule Planning**: Step-by-step guided time-block creation with conflict resolution
- **🎯 Energy-Optimized Scheduling**: Align tasks with personal energy curves for maximum productivity
- **📊 Visual Calendar System**: Beautiful ASCII-art day/week/month views with session integration
- **🔄 Template Management**: Save and reuse common scheduling patterns
- **⚡ Dynamic Adjustments**: Real-time schedule modifications with smart suggestions
- **📈 Planning Analytics**: Schedule adherence analysis and time estimation accuracy insights

### 💰 Sprint 3: Time Budget Management
- **💰 Project Time Budgets**: Set weekly/monthly time allocation limits with intelligent tracking
- **📈 Real-Time Budget Monitoring**: Live budget consumption tracking during active sessions
- **🔮 Predictive Analytics**: Forecast budget depletion and consumption rate analysis
- **📊 Visual Budget Analytics**: Charts and trends for budget optimization and planning
- **⚠️ Smart Alerting**: Proactive warnings at 80%, 95%, and 100% budget thresholds
- **🧠 AI-Driven Insights**: Intelligent budget optimization and allocation recommendations

### v0.4.0 功能
- **💬 交互模式**: 斜杠命令 (`/pm`, `/gmail`, `/task`) 和编号选择界面
- **📊 双向简报**: 用户工作简报 + Claude技术简报的高密度信息展示
- **🔗 Obsidian深度集成**: 7个子命令完整同步习惯、项目和笔记
- **🚀 项目本地化**: 所有功能在项目目录内运行，无需全局安装

### 基础功能
- **✅ GTD任务管理**: 完整的收件箱、理清、下一步行动工作流
- **🎯 习惯养成**: 基于《原子习惯》的习惯跟踪系统
- **🧠 智能推荐**: AI驱动的每日任务推荐
- **🔗 Google集成**: Calendar、Tasks、Gmail无缝同步

---

## 🚀 v0.5.0 Quick Experience

### Get AI Guidance Right Now
```bash
# Ask AI what to work on next
./bin/pm-local ai suggest

# Get detailed productivity analysis
./bin/pm-local ai analyze --detailed

# Check if you need a break
./bin/pm-local ai break

# Start an AI-guided focus session
./bin/pm-local ai focus --duration 90

# JSON output for scripts (NEW)
./bin/pm-local now --json
./bin/pm-local briefing --json
```

### Create Your First Project
```bash
# Intelligently create project (auto-categorizes project type)
./bin/pm-local project create "Learn Python Programming"

# View all projects
./bin/pm-local project list

# View project details
./bin/pm-local project info "Learn Python Programming"
```

### Start Focused Work Sessions
```bash
# Launch deep work mode (90 minutes)
./bin/pm-local session start "Learn Python Programming" --focus-mode deep_work

# Record progress checkpoints
./bin/pm-local session checkpoint "Completed basic syntax learning"

# End session with ratings
./bin/pm-local session end --energy 4 --productivity 5
```

### Plan Your Day with Time Blocks
```bash
# Interactive time-block planning
./bin/pm-local timeblock plan

# Quick time block creation
./bin/pm-local timeblock quick 09:00-11:00 deep_work

# View today's schedule
./bin/pm-local timeblock today

# Visualize your calendar
./bin/pm-local timeblock calendar --view day
```

### Manage Time Budgets
```bash
# Set project time budget
./bin/pm-local budget set "Learn Python Programming" --weekly 20 --monthly 80

# Check budget status
./bin/pm-local budget status

# Visualize budget consumption
./bin/pm-local budget chart consumption --period week
```

### Use Template System for Batch Operations
```bash
# List available templates
./bin/pm-local template list

# Apply a template (creates time blocks, tasks, budgets, projects in batch)
./bin/pm-local template apply morning_routine

# Preview template changes without applying
./bin/pm-local template apply project_kickoff --dry-run

# Create your own template from current day
./bin/pm-local template create my_workflow

# Apply with JSON output for automation
./bin/pm-local template apply budget_weekly_sample --json
```

### Analyze Your Productivity
```bash
# Daily statistics
./bin/pm-local stats daily

# Weekly trends
./bin/pm-local stats weekly

# Time allocation analysis
./bin/pm-local time today

# Personalized optimization suggestions
./bin/pm-local productivity trends
```

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
./bin/pm-local briefing         # 生成双向简报（仅报告，无操作）
./bin/pm-local inbox            # 查看收件箱
./bin/pm-local now              # 当前任务推荐（推荐用法）
./bin/pm-local capture "任务"   # 快速捕获任务

# 🆕 新增功能
./bin/pm-local now --json       # JSON格式输出
./bin/pm-local briefing --json  # JSON格式简报
./bin/pm-local setup --yes      # 自动确认设置
```

#### **🤖 AI Commands (v0.5.0 NEW)**
- `pm ai suggest`: Get intelligent recommendations for what to work on right now
- `pm ai suggest --detailed`: Get comprehensive analysis with decision reasoning
- `pm ai analyze --days 7`: AI analysis of productivity patterns and suggestions
- `pm ai break`: Get smart break timing recommendations based on fatigue
- `pm ai focus --duration 90`: Start AI-guided focus session with optimal task selection

#### **📁 Project Management (v0.5.0 Enhanced)**
- `pm project create "项目名称"`: 创建新项目，AI自动分类项目类型
- `pm project list`: 查看所有项目列表，支持筛选和排序
- `pm project info "项目名称"`: 查看项目详细信息和统计
- `pm project archive "项目名称"`: 归档已完成的项目
- `pm project workflow "项目名称"`: 获取项目下一步行动建议
- `pm projects overview`: 查看所有项目的状态概览
- `pm project status <项目名>`: 查看单个项目的详细状态
- `pm monitor start`: 在后台启动对 `PROJECT_STATUS.md` 文件的自动监控

#### **Session工作法 (v0.5.0 新增)**
- `pm session start "项目名称"`: 开始专注工作时段
- `pm session start --focus-mode pomodoro`: 启动番茄工作法（25分钟）
- `pm session checkpoint "进度描述"`: 记录工作进度检查点
- `pm session pause` / `pm session resume`: 暂停/恢复会话
- `pm session end --energy 4 --productivity 5`: 结束会话并评分
- `pm session status`: 查看当前会话状态
- `pm session list`: 查看历史会话记录

#### **时间追踪与分析 (v0.5.0 新增)**
- `pm stats daily`: 查看今日生产力统计
- `pm stats weekly`: 查看一周生产力趋势
- `pm time today`: 查看今日时间分配
- `pm time project "项目名称"`: 查看项目时间投入
- `pm productivity trends`: 分析生产力模式和趋势
- `pm productivity optimal`: 获取个性化优化建议

#### **💰 Time Budget Management (Sprint 3 NEW)**
- `pm budget set "项目名称" --weekly 20 --monthly 80`: 设置项目时间预算
- `pm budget status`: 查看所有项目预算状态
- `pm budget status "项目名称"`: 查看特定项目预算状态  
- `pm budget forecast "项目名称"`: 预测预算消耗和耗尽时间
- `pm budget chart consumption --period week`: 消耗情况柱状图
- `pm budget chart trend --project "项目名称" --days 7`: 趋势分析图表
- `pm budget chart forecast --project "项目名称"`: 预测可视化图表
- `pm budget review --period week`: 周度预算使用回顾

#### **📅 Time-Block Planning (Sprint 4 NEW)**
- `pm timeblock plan`: 启动交互式时间块规划会话
- `pm timeblock quick 09:00-11:00 deep_work`: 快速创建时间块
- `pm timeblock view --date 2024-01-15`: 查看指定日期的时间安排
- `pm timeblock today`: 查看今日时间表和当前活动块
- `pm timeblock calendar --view day/week/month`: 可视化日历视图
- `pm timeblock adjust BLOCK-ID --start 10:00`: 调整现有时间块
- `pm timeblock template save "模板名"`: 保存当前安排为模板
- `pm timeblock template load "模板名"`: 应用已保存的模板
- `pm timeblock status`: 查看当前时间块状态和统计信息

#### **任务管理 (GTD)**
- `pm capture "任务内容"`: 快速捕获任务到收件箱。
- `pm inbox`: 查看收件箱中待处理的任务。
- `pm clarify`: 启动交互式GTD理清流程。
- `pm next`: 查看下一步行动清单。

#### **智能推荐 🆕 已升级**
- `pm now`: **推荐命令** - 获取当前最佳任务推荐（取代旧命令）
- `pm now --json`: 获取JSON格式输出，适合脚本集成
- `pm explain <任务ID>`: 解释某条推荐背后的决策逻辑

**⚠️ 命令迁移说明**:
- `pm today` → `pm now` (推荐使用)
- `pm recommend` → `pm now` (推荐使用)
- `pm next` → `pm now` (推荐使用)
- `pm smart-next` → `pm now` (推荐使用)

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

## 🤖 AI Decision Engine (v0.5.0)

### Intelligent "What Should I Work On Now?" Recommendations

PersonalManager v0.5.0 introduces an advanced AI decision engine that analyzes your work patterns, energy levels, deadlines, and project priorities to provide intelligent recommendations.

#### AI Command Examples

**Get Current Recommendation:**
```bash
$ pm ai suggest

🤖 AI Recommendation (Confidence: 92%)

Right now (9:15 AM), I suggest:
📘 Work on "Backend Refactoring" project

Why this recommendation:
• 🧠 Your cognitive energy peaks 9-11 AM (based on 30-day pattern)
• 🎯 This project requires deep focus (matches current energy)
• ⏰ You have 1.7 hours before your next meeting
• 📊 This project is 2 days behind schedule
• 🔄 No context switch needed (you worked on it yesterday)
```

**Analyze Productivity Patterns:**
```bash
$ pm ai analyze --period month

🧠 Your Productivity Patterns (Last 30 Days)

Peak Performance Times:
• Morning: 9:00-11:00 (87% productivity)
• Afternoon: 14:00-15:30 (72% productivity)
• Evening: 19:00-20:00 (68% productivity)

Best Days for Deep Work:
• Tuesday (avg 4.2h deep work)
• Thursday (avg 3.9h deep work)
• Monday (avg 3.5h deep work)

Recommendations:
1. 📌 Protect 9-11 AM for critical work
2. 🔄 Batch similar tasks together
3. ⏰ Schedule meetings outside peak times
```

**Smart Break Recommendations:**
```bash
$ pm ai break

⚠️ Break Recommended! (Confidence: 95%)

Current state:
• Fatigue: 72%
• Time since break: 85 minutes
• Energy level: 2.3/5

🎯 Recommended Break Activities:
• 🚶 Take a 10-15 minute walk outside
• 🧘 Practice deep breathing or meditation
• 💧 Hydrate and have a healthy snack
```

### AI Learning & Adaptation

The AI system continuously learns from your work patterns:
- **Pattern Recognition**: Identifies your peak performance times
- **Context Awareness**: Considers deadlines, energy, and current workload
- **Feedback Learning**: Improves recommendations based on your choices
- **Privacy-First**: All AI processing happens locally on your machine

## 📁 Project Management System (v0.5.0)

### 五种项目类型

PersonalManager v0.5.0 引入智能项目分类系统，根据项目特征自动归类：

| 项目类型 | 特征描述 | 管理策略 | 示例 |
|----------|----------|----------|------|
| **探索型** (Exploratory) | 研究、学习、开放式调查 | 灵活时段、记录发现 | "学习新框架", "市场调研" |
| **节奏型** (Rhythmic) | 定期重复、可预测的工作 | 固定时间段、自动调度 | "周报撰写", "团队会议" |
| **目标型** (Goal) | 有明确截止日期和交付物 | 里程碑管理、进度追踪 | "产品发布v2.0", "考试准备" |
| **迭代型** (Iterative) | 持续改进、版本演进 | Sprint规划、版本管理 | "代码重构", "PersonalManager开发" |
| **习惯型** (Habitual) | 日常维护、例行事务 | 最小化管理、自动化 | "邮件处理", "每日锻炼" |

### Session工作法模式

专注工作时段支持多种模式，适应不同工作需求：

| 专注模式 | 时长 | 适用场景 | 休息建议 |
|----------|------|----------|----------|
| **深度工作** (deep_work) | 90分钟 | 复杂问题解决、创意工作 | 15-20分钟完全休息 |
| **番茄工作法** (pomodoro) | 25分钟 | 专注冲刺、避免拖延 | 5分钟短休息 |
| **自然节奏** (flow) | 灵活时长 | 跟随自然工作节奏 | 根据感觉调整 |
| **回顾模式** (review) | 30分钟 | 计划、反思、整理 | 散步或轻松活动 |
| **规划模式** (planning) | 45分钟 | 项目组织、战略思考 | 10分钟活动休息 |

### Smart Time-Block Planning System (Sprint 4)

PersonalManager v0.5.0 introduces an advanced time-block planning system for precise time management and intelligent scheduling:

#### 🎯 Core Time-Block Planning Features

| Feature | Description | Command |
|------|------|------|
| **Interactive Planning** | Step-by-step guided schedule creation | `pm timeblock plan` |
| **Quick Add** | Rapid time-block creation | `pm timeblock quick 09:00-11:00 deep_work` |
| **Smart Conflict Resolution** | Auto-detect and suggest conflict solutions | Built into planning flow |
| **Calendar Visualization** | ASCII-art style schedule display | `pm timeblock calendar --view day` |
| **Template Management** | Save and apply schedule templates | `pm timeblock template save/load` |

#### 📅 Calendar & Visualization

```bash
# View today's schedule
pm timeblock today

# Detailed day view (with session integration)
pm timeblock calendar --view day --date 2024-01-15

# Week overview
pm timeblock calendar --view week

# Monthly summary
pm timeblock calendar --view month

# Export schedule
pm timeblock calendar --export my_schedule.txt
```

#### ⚡ Quick Operations

```bash
# View current status and suggestions
pm timeblock status

# Adjust existing time blocks
pm timeblock adjust BLOCK-ID --start 10:00 --notes "Updated task"

# View specific date details
pm timeblock view --date 2024-01-15 --details
```

#### 🔗 Advanced Planning Features

- **Smart Conflict Detection**: Automatic time overlap identification with resolution suggestions
- **Energy Level Optimization**: Schedule deep work during personal peak energy periods
- **Project Time Allocation**: Intelligent time distribution to meet project budget requirements
- **Buffer Time Insertion**: Automatic addition of reasonable buffer periods between tasks
- **Intelligent Template Application**: Smart template adjustments based on historical data

#### 📊 Planning Analysis & Insights

The time-block system integrates powerful analytics for precise planning insights:

```bash
# Schedule adherence analysis
pm analytics adherence --period week

# Time estimation accuracy
pm analytics estimation --project "Project Name"

# Planning pattern recognition
pm analytics patterns --start 2024-01-01 --end 2024-01-31

# Personalized optimization suggestions
pm analytics insights --focus energy_alignment
```

### Intelligent Analysis & Optimization

v0.5.0 provides personalized productivity analysis:
- **Time Investment Analysis**: Actual vs. expected time across projects
- **Efficiency Trends**: Productivity comparison across different periods and modes
- **Optimal Time Windows**: Personal best work time recommendations based on historical data
- **Project Health Assessment**: Comprehensive evaluation of progress, investment, and output
- **Optimization Recommendations**: AI-driven personalized improvement suggestions

### 📋 JSON API Support (NEW)

PersonalManager now supports JSON output for seamless integration:

```bash
# Get current recommendations in JSON format
pm now --json

# Generate briefing data for external processing
pm briefing --json

# All analytics commands support JSON
pm stats daily --json
pm time today --json
```

**Example JSON Output:**
```json
{
  "timestamp": "2024-01-15T09:30:00",
  "recommendations": [
    {
      "task_id": "TASK-123",
      "title": "Review API documentation",
      "priority": "high",
      "confidence": 0.92,
      "reasoning": "Matches peak energy time"
    }
  ],
  "context": {
    "current_energy": 4,
    "available_time": 120
  }
}
```

### ⚡ Non-Interactive Mode (NEW)

Automated workflow support for scripts and CI/CD:

```bash
# Auto-confirm all prompts
pm setup --yes
pm project create "Auto Project" --yes

# Auto-decline prompts (for conservative automation)
pm capabilities refresh --assume-no
pm cleanup --assume-no

# Perfect for automated scripts
./scripts/daily_sync.sh --yes
```

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
