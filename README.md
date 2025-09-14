# PersonalManager - 您的AI个人效能操作系统

**PersonalManager** 是一个功能强大的、AI驱动的个人效能工具集，旨在通过自然语言交互，帮助您无缝地管理项目、任务、目标、习惯和专注力。它深度整合了多种经典的生产力方法论，是您在数字时代实现“心如止水”和“深度工作”的智能伙伴。

---

## 核心特性

- **🗣️ 自然语言交互**: 通过与AI Agent（如Gemini, Claude）对话，直接管理您的个人效能系统。
- **🗂️ 项目管理 (独创)**: 独创的“以报告为中心”的项目管理模式。您只需用自然语言编写 `PROJECT_STATUS.md`，系统即可自动解析、跟踪和分析项目状态。
- **✅ 任务管理 (GTD)**: 内置完整的《搞定》(GTD)工作流，支持任务的快速捕获、理清、组织和回顾。
- **🎯 习惯养成 (原子习惯)**: 基于《原子习惯》理论，提供强大的习惯创建、跟踪和分析功能，助您建立良好习惯。
- **🚀 深度工作 (Deep Work)**: 基于《深度工作》理论，帮助您规划、执行和复盘高质量的专注工作时段。
- **🤔 回顾与反思**: 系统化的每周回顾、项目复盘和决策追踪功能，助您持续学习和成长。
- **🔗 Google服务集成**: 无缝集成Google Calendar, Tasks, 和 Gmail，自动将日程和重要邮件转化为任务。
- **💡 Obsidian集成**: 连接您的Obsidian知识库，实现笔记的创建、搜索和任务同步。
- **🧠 智能推荐引擎**: 基于多种生产力理论，结合您的个人偏好，为您提供每日任务的智能推荐。

---

## 快速开始

### 1. 安装

```bash
# 克隆项目
git clone <repository-url>
cd personal-manager

# 安装依赖
poetry install
```

### 2. 配置

首次运行时，系统会引导您完成设置。您也可以随时运行以下命令进行配置：

```bash
# 启动交互式设置向导
poetry run pm setup
```
设置向导将帮助您配置Google API凭证、项目根目录、个人偏好等。

### 3. 基本用法

`PersonalManager` 主要通过CLI命令进行交互。所有命令均可通过 `poetry run pm <command>` 或项目级启动器 `./bin/pm-local <command>` 执行。

#### Agent 使用场景

PersonalManager 专为与 AI Agent（如 Claude、Gemini CLI）协作而设计。通过自然语言对话，Agent 可以自动将您的需求转换为具体的 CLI 命令：

**使用项目级启动器**：
```bash
# Agent 会自动使用项目级入口点
./bin/pm-local projects overview
./bin/pm-local today
./bin/pm-local capture "准备下周的项目汇报"
```

**自然语言交互示例**：
- **用户**："帮我查看今天的重点任务"
- **Agent**：执行 `./bin/pm-local today`
- **用户**："添加一个任务：准备团队会议"  
- **Agent**：执行 `./bin/pm-local capture "准备团队会议"`

> 💡 **推荐**：在远程环境中使用 Claude Code、Gemini CLI 或其他 Agent 工具，通过自然语言轻松管理您的个人效能系统。

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
