# BMAD框架技术参考指南

> **版本**: v1.0  
> **创建日期**: 2025-09-11  
> **适用版本**: BMAD-METHOD™ v4.43.1  
> **目标用户**: PersonalManager系统开发者、BMAD框架使用者

## 📖 指南概述

本指南深入解析BMAD框架的技术架构，为PersonalManager系统的实现提供可靠的技术基础。通过系统化分析框架配置、Agent定义、任务流程和CLI集成，帮助开发者掌握BMAD的核心机制和最佳实践。

### 核心价值
- **深度理解**: BMAD框架配置约束和能力边界
- **标准模板**: Agent定义、任务配置的标准模板
- **实施指导**: PersonalManager系统技术实现基础
- **最佳实践**: 可复用的配置模板和问题解决方案

---

## 1. 🏗️ BMAD框架系统架构

### 1.1 框架版本与安装信息
```yaml
version: 4.43.1
installed_at: '2025-09-11T01:32:32.222Z'
install_type: full
ides_setup:
  - claude-code
  - gemini
  - codex
expansion_packs: []
```

### 1.2 核心目录结构
```
.bmad-core/
├── core-config.yaml          # 核心配置文件
├── install-manifest.yaml     # 系统安装清单
├── agents/                   # Agent定义文件 (8个)
├── tasks/                    # 任务流程文件 (22个)
├── templates/               # 文档模板 (13个)
├── workflows/               # 工作流配置 (6个)
├── checklists/             # 检查清单 (6个)
├── data/                   # 数据文件 (6个)
├── agent-teams/            # Agent团队配置 (4个)
└── utils/                  # 工具文件 (2个)

.claude/
├── settings.local.json     # CLI权限配置
└── commands/BMad/         # CLI命令定义
    ├── agents/           # Agent命令 (10个)
    └── tasks/           # 任务命令 (22个)
```

### 1.3 文件完整性验证
BMAD使用哈希值确保所有文件的完整性，每个文件都有对应的hash值和modified状态标记，确保框架运行的可靠性。

---

## 2. ⚙️ 核心配置文件解析

### 2.1 core-config.yaml 详细配置

```yaml
# Markdown文档处理配置
markdownExploder: true

# QA质量保证配置
qa:
  qaLocation: docs/qa              # QA文件存储位置

# PRD产品需求文档配置
prd:
  prdFile: docs/prd.md            # PRD主文件路径
  prdVersion: v4                   # PRD版本
  prdSharded: true                 # 启用PRD分片
  prdShardedLocation: docs/prd     # 分片文件存储位置
  epicFilePattern: epic-{n}*.md   # Epic文件命名模式

# 架构文档配置
architecture:
  architectureFile: docs/architecture.md        # 架构主文件路径
  architectureVersion: v4                       # 架构文档版本
  architectureSharded: true                     # 启用架构分片
  architectureShardedLocation: docs/architecture # 分片文件存储位置

# 自定义技术文档
customTechnicalDocuments: null

# 开发者必需文件配置
devLoadAlwaysFiles:
  - docs/architecture/coding-standards.md      # 编码标准
  - docs/architecture/tech-stack.md           # 技术栈定义
  - docs/architecture/source-tree.md          # 源码结构

# 开发调试配置
devDebugLog: .ai/debug-log.md    # 调试日志位置
devStoryLocation: docs/stories   # 用户故事存储位置

# CLI命令前缀
slashPrefix: BMad                # CLI命令前缀 (/BMad)
```

### 2.2 配置项作用说明

| 配置项 | 作用 | 取值范围 | 影响范围 |
|--------|------|----------|----------|
| `markdownExploder` | 启用Markdown文档分解功能 | `true/false` | 文档生成流程 |
| `prdSharded` | 启用PRD文档分片，便于IDE处理 | `true/false` | 文档管理 |
| `devLoadAlwaysFiles` | 开发者Agent必需加载的文件 | 文件路径数组 | Agent初始化 |
| `slashPrefix` | CLI命令的前缀标识符 | 字符串 | CLI交互 |
| `qaLocation` | QA相关文件的存储路径 | 相对路径 | 质量保证流程 |

---

## 3. 🤖 Agent定义规范与架构

### 3.1 Agent文件结构标准

每个Agent文件遵循统一的结构模式：

```markdown
<!-- Powered by BMAD™ Core -->

# {agent_id}

ACTIVATION-NOTICE: 完整Agent定义包含在下方YAML块中

CRITICAL: 阅读完整YAML块以理解操作参数

## 完整AGENT定义如下 - 无需外部文件

```yaml
# Agent定义YAML块
```
```

### 3.2 Agent YAML结构详解

```yaml
# IDE文件解析规则 (仅在执行命令时使用)
IDE-FILE-RESOLUTION:
  - 依赖文件映射到 .bmad-core/{type}/{name}
  - type=文件夹类型 (tasks|templates|checklists|data等)
  - 仅在用户请求特定命令执行时加载

# 请求解析规则
REQUEST-RESOLUTION: 
  - 灵活匹配用户请求到命令/依赖
  - 无明确匹配时要求澄清

# 激活指令 (Agent启动时的执行步骤)
activation-instructions:
  - STEP 1: 读取此文件完整内容
  - STEP 2: 采纳persona定义的角色
  - STEP 3: 加载并阅读core-config.yaml
  - STEP 4: 问候用户并自动运行*help命令
  - 关键规则: 仅在命令执行时加载依赖文件

# Agent基本信息
agent:
  name: {Agent姓名}           # 人性化姓名
  id: {agent_id}              # 系统标识符
  title: {职位标题}           # 专业职位
  icon: {表情符号}            # 可视化图标
  whenToUse: {使用场景描述}   # 何时使用此Agent
  customization: null         # 自定义配置 (可覆盖默认行为)

# 角色人格定义
persona:
  role: {角色定位}            # 专业角色定义
  style: {工作风格}           # 沟通和工作方式
  identity: {身份认知}        # 角色身份定位
  focus: {关注重点}           # 主要关注领域
  core_principles:            # 核心原则列表
    - {原则1}
    - {原则2}
    # ...

# 可用命令 (必须使用*前缀)
commands:
  - help: 显示编号的命令列表
  - {command_name}: {命令描述}
  # ...
  - exit: 退出Agent模式

# 依赖资源
dependencies:
  checklists:               # 检查清单
    - {checklist-file.md}
  tasks:                   # 任务定义
    - {task-file.md}
  templates:               # 模板文件
    - {template-file.yaml}
  data:                    # 数据文件
    - {data-file.md}
```

### 3.3 标准Agent模板示例

#### 3.3.1 Product Owner Agent模板

> **PersonalManager映射**: 在PersonalManager系统中，此角色功能由 `project-manager` Agent承接

```yaml
agent:
  name: Sarah
  id: po
  title: Product Owner
  icon: 📝
  whenToUse: 用于backlog管理、故事细化、验收标准、冲刺规划和优先级决策
  
persona:
  role: 技术产品负责人 & 流程管理员
  style: 细致、分析型、注重细节、系统化、协作性
  focus: 计划完整性、文档质量、可执行开发任务、流程遵守
  
commands:
  - help: 显示编号命令列表
  - create-epic: 为brownfield项目创建Epic
  - create-story: 从需求创建用户故事
  - validate-story-draft: 验证故事草稿
  - shard-doc: 分割文档到指定目标
  
dependencies:
  checklists: [po-master-checklist.md]
  tasks: [validate-next-story.md, shard-doc.md]
  templates: [story-tmpl.yaml]
```

#### 3.3.2 Architect Agent模板

> **PersonalManager映射**: 在PersonalManager系统中，此角色功能由 `pm-orchestrator` Agent的架构规划模块承接

```yaml
agent:
  name: Winston
  id: architect
  title: Architect
  icon: 🏗️
  whenToUse: 用于系统设计、架构文档、技术选型、API设计和基础设施规划
  
persona:
  role: 全栈系统架构师 & 技术领导者
  style: 全面、务实、用户为中心、技术深度且易理解
  focus: 完整系统架构、跨栈优化、务实技术选择
  
commands:
  - create-backend-architecture: 使用architecture-tmpl.yaml
  - create-fullstack-architecture: 使用fullstack-architecture-tmpl.yaml
  - research: 执行深度研究提示任务
  
dependencies:
  templates: [architecture-tmpl.yaml, fullstack-architecture-tmpl.yaml]
  tasks: [create-deep-research-prompt.md, document-project.md]
```

#### 3.3.3 Developer Agent模板

> **PersonalManager映射**: 在PersonalManager系统中，此角色功能由 `automation-manager` Agent的执行引擎承接

```yaml
agent:
  name: James
  id: dev
  title: Full Stack Developer
  icon: 💻
  whenToUse: 用于代码实现、调试、重构和开发最佳实践
  
persona:
  role: 专家级高级软件工程师 & 实现专家
  style: 极其简洁、务实、注重细节、解决方案导向
  focus: 精确执行故事任务，仅更新开发者记录部分
  
commands:
  - develop-story: 按顺序执行任务实现故事
  - run-tests: 执行代码检查和测试
  - review-qa: 运行QA修复任务
  
dependencies:
  checklists: [story-dod-checklist.md]
  tasks: [apply-qa-fixes.md, execute-checklist.md]
```

#### 3.3.4 QA Agent模板

> **PersonalManager映射**: 在PersonalManager系统中，此角色功能由 `status-analyzer` Agent的质量检测模块承接

```yaml
agent:
  name: Quinn
  id: qa
  title: Test Architect & Quality Advisor
  icon: 🧪
  whenToUse: 用于全面测试架构审查、质量门决策和代码改进
  
persona:
  role: 具有质量咨询权威的测试架构师
  style: 全面、系统化、咨询性、教育性、务实
  focus: 通过测试架构、风险评估和咨询门的全面质量分析
  
commands:
  - review: 自适应、风险感知的全面审查
  - gate: 执行质量门任务生成决策文件
  - nfr-assess: 验证非功能需求
  - test-design: 创建全面测试场景
  
dependencies:
  tasks: [review-story.md, qa-gate.md, test-design.md]
  templates: [qa-gate-tmpl.yaml]
```

#### 3.3.5 Orchestrator Agent模板
```yaml
agent:
  name: BMad Orchestrator
  id: bmad-orchestrator
  title: BMad Master Orchestrator
  icon: 🎭
  whenToUse: 用于工作流协调、多Agent任务、角色切换指导
  
persona:
  role: 主协调者 & BMad方法专家
  style: 知识渊博、指导性、适应性、高效、鼓励性
  focus: 为每个需求协调正确的Agent/能力，仅在需要时加载资源
  
commands:
  - agent: 转换为专业Agent
  - workflow: 启动特定工作流
  - kb-mode: 加载完整BMad知识库
  - status: 显示当前上下文和进度
  
dependencies:
  data: [bmad-kb.md, elicitation-methods.md]
  tasks: [kb-mode-interaction.md, create-doc.md]
```

---

## 4. 📋 任务工作流定义标准

### 4.1 任务文件结构

```markdown
<!-- Powered by BMAD™ Core -->

# {任务标题}

## ⚠️ 关键执行通知 ⚠️

**这是可执行工作流 - 不是参考材料**

调用此任务时：
1. 禁用所有效率优化
2. 必须逐步执行
3. 当elicit: true时需要用户交互
4. 不允许快捷方式

## 任务处理流程
{详细的任务执行步骤}

## 关键提醒
- ❌ 永远不要: {禁止行为}
- ✅ 总是要: {必须行为}
```

### 4.2 交互式任务模式

#### elicit=true 强制交互格式
```yaml
elicit: true  # 强制用户交互标记
```

当任务标记为`elicit: true`时，必须：
1. 呈现部分内容
2. 提供详细理由说明
3. **停止并呈现编号选项1-9**：
   - **选项1**: 总是"进行到下一部分"
   - **选项2-9**: 从elicitation-methods中选择8种方法
   - 结尾: "选择1-9或直接输入问题/反馈："
4. **等待用户响应** - 在用户选择前不得继续

### 4.3 任务类型与示例

#### 文档创建任务 (create-doc.md)
```yaml
目的: 从YAML模板驱动的文档创建
特点: 
  - 模板发现和加载
  - 逐节处理流程
  - 强制交互验证
  - 详细理由要求
```

#### 检查清单执行 (execute-checklist.md)
```yaml
目的: 根据检查清单验证文档
特点:
  - 文档收集阶段
  - 逐项验证流程
  - 通过率计算
  - 改进建议生成
```

#### 故事验证任务 (validate-next-story.md)
```yaml
目的: 验证用户故事完整性和质量
特点:
  - 需求完整性检查
  - 验收标准验证
  - 依赖关系分析
  - 可实施性评估
```

---

## 5. 📄 模板系统使用指南

### 5.1 模板文件结构标准

```yaml
# <!-- Powered by BMAD™ Core -->
template:
  id: {template-id}
  name: {模板名称}
  version: {版本号}
  output:
    format: markdown
    filename: {输出文件路径}
    title: {文档标题}

workflow:
  mode: interactive           # interactive | automatic
  elicitation: advanced-elicitation  # 启用高级引导方法

sections:
  - id: {section-id}
    title: {节标题}
    instruction: |
      {详细的内容生成指令}
    elicit: true              # 是否需要用户交互
    condition: {条件表达式}   # 可选的显示条件
    sections:                 # 子节定义
      - id: {sub-section-id}
        title: {子节标题}
        type: {内容类型}      # bullet-list, paragraphs, table等
```

### 5.2 内容类型定义

| 类型 | 用途 | 示例 |
|------|------|------|
| `bullet-list` | 无序列表 | 功能需求列表 |
| `numbered-list` | 编号列表 | 验收标准 |
| `paragraphs` | 段落文本 | 背景介绍 |
| `table` | 表格数据 | 变更日志 |

### 5.3 模板系统最佳实践

#### PRD模板示例
```yaml
template:
  id: prd-template-v2
  name: Product Requirements Document
  version: 2.0

sections:
  - id: goals-context
    title: Goals and Background Context
    instruction: |
      询问是否存在项目简报文档。如不存在，强烈建议先创建。
      确定范围和需求的关键部分。
    
  - id: requirements
    title: Requirements
    elicit: true
    sections:
      - id: functional
        title: Functional
        type: numbered-list
        prefix: FR
        examples:
          - "FR6: Todo List使用AI检测潜在重复项目"
```

---

## 6. 🔧 CLI集成方法

### 6.1 权限配置系统

#### settings.local.json配置
```json
{
  "permissions": {
    "allow": [
      "WebSearch",
      "WebFetch(domain:bmadcodes.com)",
      "WebFetch(domain:github.com)",
      "Bash(npm run bmad:list:*)"
    ],
    "deny": [],
    "ask": []
  }
}
```

### 6.2 命令注册机制

#### 命令目录结构
```
.claude/commands/BMad/
├── agents/          # Agent激活命令
│   ├── po.toml
│   ├── architect.toml  
│   ├── dev.toml
│   └── ...
└── tasks/           # 任务执行命令
    ├── create-doc.toml
    ├── execute-checklist.toml
    └── ...
```

#### Agent命令定义 (po.toml示例)
```toml
description = "Activates the Product Manager agent from the BMad Method."
prompt = """
CRITICAL: You are now the BMad 'Product Manager' agent...
@{.bmad-core/agents/po.md}
"""
```

### 6.3 CLI使用模式

#### 基本命令格式
```bash
# Agent激活
/pm agents po              # 激活Product Owner
/pm agents architect       # 激活Architect

# 任务执行  
/pm tasks create-doc       # 创建文档
/pm tasks execute-checklist # 执行检查清单

# Agent内部命令 (需要*前缀)
*help                        # 显示Agent帮助
*create-story               # 创建用户故事
*exit                       # 退出Agent模式
```

#### 权限控制最佳实践
```json
{
  "permissions": {
    "allow": [
      "WebSearch",                    // 允许网络搜索
      "WebFetch(domain:specific.com)", // 限制特定域名
      "Bash(npm run bmad:*)"          // 限制特定命令模式
    ],
    "deny": [
      "Bash(rm *)",                   // 拒绝危险操作
      "Bash(sudo *)"                  // 拒绝系统管理命令
    ],
    "ask": [
      "Write",                        // 文件写入需要确认
      "Edit"                          // 文件编辑需要确认
    ]
  }
}
```

---

## 7. 🔄 工作流配置规范

### 7.1 工作流文件结构

```yaml
# <!-- Powered by BMAD™ Core -->
workflow:
  id: {workflow-id}
  name: {工作流名称}
  description: {工作流描述}
  type: {greenfield|brownfield}
  project_types:
    - web-app
    - saas
    - prototype

sequence:
  - agent: {agent-id}
    creates: {输出文档}
    requires: {依赖文档}
    optional_steps:
      - {可选步骤}
    notes: {执行注意事项}
```

### 7.2 Greenfield全栈开发工作流示例

```yaml
workflow:
  id: greenfield-fullstack
  name: Greenfield Full-Stack Application Development
  type: greenfield

sequence:
  - agent: analyst
    creates: project-brief.md
    optional_steps: [brainstorming_session, market_research]
    
  - agent: pm  
    creates: prd.md
    requires: project-brief.md
    
  - agent: ux-expert
    creates: front-end-spec.md
    requires: prd.md
    
  - agent: architect
    creates: fullstack-architecture.md
    requires: [prd.md, front-end-spec.md]
    
  - agent: po
    validates: all_artifacts
    uses: po-master-checklist
```

### 7.3 工作流决策指导

#### 何时使用不同工作流类型

**Greenfield工作流**:
- 构建生产就绪应用程序
- 需要全面文档
- 多团队成员参与
- 长期维护预期

**Brownfield工作流**:
- 现有项目功能增强
- 快速原型开发
- 单人或小团队
- 短期交付目标

---

## 8. 📊 配置文件组织结构规范

### 8.1 项目配置层级

```
项目根目录/
├── .bmad-core/              # BMAD框架核心
│   ├── core-config.yaml     # 【核心】项目配置
│   ├── agents/              # 【角色】Agent定义
│   ├── tasks/               # 【流程】任务定义  
│   ├── templates/           # 【模板】文档模板
│   ├── workflows/           # 【工作流】流程配置
│   ├── checklists/          # 【质量】检查清单
│   └── data/                # 【数据】参考数据

├── .claude/                 # Claude CLI配置
│   ├── settings.local.json  # 【权限】CLI权限配置
│   └── commands/BMad/       # 【命令】CLI命令定义

├── docs/                    # 项目文档输出
│   ├── prd/                 # PRD分片文档
│   ├── architecture/        # 架构分片文档
│   ├── stories/             # 用户故事文档
│   └── qa/                  # QA相关文档

└── 项目特定文件/            # 实际项目代码
```

### 8.2 配置优先级规则

1. **Agent自定义配置** > 默认配置
2. **项目级core-config.yaml** > 框架默认
3. **本地CLI权限** > 全局权限
4. **用户运行时选择** > 配置文件设定

### 8.3 配置文件最佳实践

#### 环境分离策略
```yaml
# 开发环境配置
devLoadAlwaysFiles:
  - docs/architecture/coding-standards.md
  - docs/architecture/tech-stack.md

# 生产环境配置  
qa:
  qaLocation: docs/qa
prd:
  prdSharded: true
```

#### 团队协作配置
```yaml
# 文档版本管理
prdVersion: v4
architectureVersion: v4

# 分工明确的文件路径
devStoryLocation: docs/stories
slashPrefix: BMad
```

---

## 9. 🚀 PersonalManager配置映射表

### 9.1 从BMAD到PersonalManager的配置映射

| BMAD配置项 | PersonalManager对应 | 映射说明 |
|------------|---------------------|----------|
| `prd.prdFile` | `personalManager.planFile` | 个人规划文档路径 |
| `devStoryLocation` | `personalManager.goalLocation` | 目标任务存储路径 |
| `qa.qaLocation` | `personalManager.reviewLocation` | 回顾分析文档路径 |
| `slashPrefix` | `personalManager.commandPrefix` | CLI命令前缀(/pm) |
| `devLoadAlwaysFiles` | `personalManager.contextFiles` | 必需上下文文件 |

### 9.2 PersonalManager专用配置

```yaml
# PersonalManager特有配置
personalManager:
  # 个人管理配置
  planFile: docs/personal-plan.md
  goalLocation: docs/goals
  reviewLocation: docs/reviews
  commandPrefix: pm
  
  # 角色配置
  roles:
    project_manager: true
    scheduler: true  
    life_planner: true
    data_manager: true
    advisor: true
    
  # 外部集成
  integrations:
    calendar: google_calendar
    email: gmail
    tasks: google_tasks
    
  # 上下文文件
  contextFiles:
    - docs/personal-preferences.md
    - docs/project-templates.md
    - docs/goal-templates.md
```

### 9.3 Agent定义适配

#### PersonalManager Agent模板
```yaml
agent:
  name: PersonalManager
  id: personal-manager
  title: Personal Productivity Manager
  icon: 🎯
  whenToUse: 个人生产力管理、项目优先级决策、时间规划和目标追踪

persona:
  role: 全能个人管理助理
  style: 智能、高效、洞察力强、结果导向
  identity: 通过角色切换提供多职能管理支持的AI助理
  focus: 智能决策支持、优先级优化、时间管理、目标追踪
  core_principles:
    - 智能角色切换 - 根据上下文自动选择最佳角色
    - 数据驱动决策 - 基于历史数据和实时信息提供建议
    - 个性化优化 - 学习用户偏好并持续优化建议
    - 全生命周期管理 - 从规划到执行到回顾的完整支持

commands:
  - help: 显示可用命令和角色模式
  - today: 生成今日优先级和时间安排建议
  - plan-week: 创建每周规划和目标分解
  - track-goals: 追踪和分析目标进度
  - sync-data: 同步外部系统数据
  - review-performance: 生成个人表现分析报告
  - switch-role: 手动切换专业角色模式

dependencies:
  templates:
    - personal-plan-tmpl.yaml
    - goal-tracking-tmpl.yaml
    - daily-review-tmpl.yaml
  tasks:
    - analyze-priorities.md
    - sync-external-data.md
    - generate-recommendations.md
  data:
    - personal-preferences.md
    - priority-algorithms.md
```

---

## 10. 🔧 Troubleshooting & 常见问题

### 10.1 Agent激活问题

**问题**: Agent激活后没有加载预期的配置
```yaml
# 解决方案: 检查activation-instructions
activation-instructions:
  - STEP 3: Load and read `bmad-core/core-config.yaml` 
```

**问题**: 命令不被识别
```bash
# 解决方案: 确保使用*前缀
*help          # ✅ 正确
help           # ❌ 错误
```

### 10.2 权限配置问题

**问题**: CLI命令被拒绝执行
```json
// 检查settings.local.json权限配置
{
  "permissions": {
    "allow": ["Bash(npm run bmad:list:*)"],  // 确保命令模式匹配
    "deny": ["Bash(rm *)"]                   // 检查是否被意外拒绝
  }
}
```

### 10.3 文件路径问题

**问题**: 依赖文件无法找到
```yaml
# 确保依赖路径正确
dependencies:
  tasks:
    - create-doc.md          # 映射到 .bmad-core/tasks/create-doc.md
```

### 10.4 模板处理问题

**问题**: elicit=true时没有用户交互
```yaml
# 检查任务是否正确实现交互逻辑
elicit: true  # 必须停止并等待用户输入1-9选项
```

### 10.5 工作流执行问题

**问题**: 工作流在中间步骤停止
```yaml
# 检查依赖文件是否存在
sequence:
  - agent: pm
    requires: project-brief.md  # 确保此文件在前一步骤中创建
```

### 10.6 性能优化建议

1. **避免预加载**: 仅在需要时加载依赖文件
2. **合理分片**: 大文档启用分片功能提高IDE处理效率
3. **缓存配置**: 利用framework的文件完整性验证机制
4. **批量操作**: 相关任务尽量在同一Agent会话中完成

---

## 11. 📋 验收标准检查清单

### ✅ BMAD配置选项说明完整性
- [x] core-config.yaml所有配置项都有详细说明
- [x] 配置项取值范围和影响范围明确
- [x] 提供实际项目配置示例

### ✅ Agent定义模板完整性  
- [x] 包含5个完整Agent定义模板 (PO, Architect, Dev, QA, Orchestrator)
- [x] YAML结构标准化和字段说明
- [x] 激活指令和命令系统详解

### ✅ CLI权限和命令注册说明
- [x] settings.local.json权限配置详解
- [x] 命令注册机制和目录结构说明
- [x] 权限控制最佳实践指导

### ✅ 任务工作流配置示例
- [x] 任务文件结构标准
- [x] 交互式任务(elicit=true)处理流程
- [x] 工作流配置和使用场景指导

### ✅ Troubleshooting章节
- [x] 常见问题诊断和解决方案
- [x] 性能优化建议
- [x] 配置错误排查指导

### ✅ PersonalManager配置映射
- [x] BMAD到PersonalManager的配置映射表
- [x] PersonalManager专用配置设计
- [x] Agent定义适配方案

---

## 12. 📚 参考资源

### 官方文档
- [BMAD-METHOD GitHub](https://github.com/bmad-code-org/BMAD-METHOD)
- [BMAD用户指南](https://bmadcodes.com/user-guide/)
- [Claude Code集成文档](https://docs.anthropic.com/claude-code/)

### 扩展学习
- 敏捷开发方法论
- AI驱动的软件开发流程
- CLI工具开发最佳实践

---

## 📄 文档更新日志

| 日期 | 版本 | 描述 | 作者 |
|------|------|------|------|
| 2025-09-11 | v1.0 | 初始版本，完整技术参考指南 | PersonalManager Team |

---

**💡 使用提示**: 本指南作为PersonalManager系统开发的技术基础，建议结合实际项目需求进行配置调整。遇到问题时，首先查阅Troubleshooting章节，然后参考官方文档获取最新信息。

**🎯 成功关键**: 理解BMAD的模块化设计哲学，合理利用Agent专业化分工，通过标准化模板确保输出质量，最终构建高效的个人生产力管理系统。