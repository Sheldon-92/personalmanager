# TAD Framework - MCP 使用指南

**版本:** 1.2
**日期:** 2025-01-30
**适用:** TAD Framework v1.2 及以上

---

## 🚨 重要更新: MCP 自动安装机制

**TAD v1.2 采用 Agent 驱动的 MCP 安装方式:**

- ✅ **Alex 自动安装**: 在 Round 2.5 检测到项目类型后,Alex 使用 Bash tool 自动安装 MCP
- ✅ **无需人工 CLI**: 用户**不需要**运行 `tad mcp install` 命令
- ✅ **无缝体验**: 整个过程约 20-30 秒,Alex 自动完成所有安装配置
- ✅ **用户仅需选择**: 看到推荐后,选择 0(全部安装) / 1(自选) / 2(跳过)

**示例流程:**
```
User: "我想用 Next.js 和 Supabase 做一个全栈应用"
Alex: (Round 2.5 自动检测)
      "🎯 检测到项目类型: Web Fullstack (置信度 85%)

      推荐安装的 MCP 工具:
      1. supabase - 数据库操作
      2. playwright - 测试自动化
      3. vercel - 部署管理

      选择 0-2:"
User: "0"
Alex: (自动执行)
      [使用 Bash tool]
      bash: npx -y @supabase/mcp-server --install
      bash: npx -y @playwright/test --install
      bash: npx -y vercel --global

      "✓ 安装完成! (耗时 28 秒)
      现在开始 Round 3..."
```

**本指南中所有 `tad mcp install` 命令已过时,仅作为参考保留。**

---

## 📖 目录

1. [MCP 快速入门](#1-mcp-快速入门)
2. [核心层 MCP 工具详解](#2-核心层-mcp-工具详解)
3. [项目层 MCP 按场景使用](#3-项目层-mcp-按场景使用)
4. [任务层 MCP 临时安装](#4-任务层-mcp-临时安装)
5. [Alex (Agent A) 使用指南](#5-alex-agent-a-使用指南)
6. [Blake (Agent B) 使用指南](#6-blake-agent-b-使用指南)
7. [常见问题解答](#7-常见问题解答)
8. [故障排除](#8-故障排除)

---

## 1. MCP 快速入门

### 1.1 什么是 MCP?

**MCP (Model Context Protocol)** 是 Anthropic 发布的开放标准,允许 AI 助手(如 Claude)连接到外部工具和数据源。

在 TAD 框架中,MCP 工具**增强**但**不替代**核心功能:

```
✅ TAD 核心功能 (无 MCP 也完全可用)
   - 三角模型 (Human + Alex + Blake)
   - 3-5 轮需求确认
   - Handoff 机制
   - Sub-agents 调用
   - Quality Gates

✨ MCP 增强 (提升效率 70-85%)
   - 实时最新文档 (context7)
   - 项目历史记忆 (memory-bank)
   - 自动文件操作 (filesystem)
   - 智能版本控制 (git)
   - 按需专业工具 (project/task layer)
```

### 1.2 三层 MCP 架构

```
┌─────────────────────────────────────────────────────────┐
│ Layer 1: 核心层 (Core)                                  │
│ 7 个必装工具 - 所有项目都需要                           │
│ context7, sequential-thinking, memory-bank,             │
│ filesystem, git, github, brave-search                   │
└─────────────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────┐
│ Layer 2: 项目层 (Project)                               │
│ 按项目类型安装 - Round 2.5 智能推荐                     │
│ • web_fullstack: supabase, playwright, vercel           │
│ • data_science: jupyter, pandas-mcp, antv-chart         │
│ • machine_learning: jupyter, optuna, huggingface        │
│ • devops: kubernetes, docker, aws, terminal             │
│ • creative: figma, video-audio-mcp, adobe-mcp           │
└─────────────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────┐
│ Layer 3: 任务层 (Task)                                  │
│ 临时按需安装 - 用完即卸                                 │
│ videodb, design-system-extractor, pyairbyte, mongodb    │
└─────────────────────────────────────────────────────────┘
```

### 1.3 快速开始 2 步

**Step 1: 激活 Alex 或 Blake**

```bash
# Terminal 1: 激活 Alex (需求分析+设计)
/alex

# Terminal 2: 激活 Blake (实现+测试+部署)
/blake
```

**Step 2: 开始工作**

- **Alex** 会在 **Round 2.5** 自动检测项目类型并推荐 Project-Layer MCPs
- **Alex** 会使用 Bash tool 自动安装选定的 MCPs（无需人工 CLI 操作）
- 整个过程约 20-30 秒完成

**重要说明:**
- ✅ MCP 工具由 **Agent 自动安装**（Alex 使用 Bash tool）
- ✅ **不需要人工运行** `tad mcp install` 命令
- ✅ Alex 会在需要时自动安装和配置 MCP 工具
- ✅ 用户只需选择是否安装推荐的工具（0/1/2 选项）

---

## 2. 核心层 MCP 工具详解

### 2.1 context7 📚

**用途:** 实时获取最新框架和库的文档

**效率提升:** 90-95%

**自动触发:** 当用户提到任何框架/库名称时

**使用场景:**

✅ **Alex 在 Round 1-2 之间:**
```
用户: "我想用 Next.js 15 和 Supabase 做一个博客系统"

[AUTO-TRIGGER]
⚡ Context7 called for: Next.js 15
✓ Latest Next.js 15 documentation loaded

⚡ Context7 called for: Supabase
✓ Latest Supabase documentation loaded

Alex 现在拥有最新的 API 和最佳实践知识
```

✅ **Blake 在实现代码时:**
```
Blake 实现 Next.js App Router 代码

[AUTO-TRIGGER]
⚡ Context7 called for: Next.js App Router
✓ Latest file-based routing conventions loaded

Blake 使用最新的 routing 规范写代码
```

**关键词触发列表:**
- Next.js, React, Vue, Angular, Svelte
- Tailwind CSS, TypeScript, JavaScript
- Supabase, Firebase, PostgreSQL
- 以及 Upstash 支持的 300+ 框架

**手动调用 (如需要):**
```
Alex: "Use context7 to get the latest Remix documentation"
```

---

### 2.2 sequential-thinking 💭

**用途:** 复杂问题分解和结构化推理

**效率提升:** 60-70%

**建议使用:** 复杂架构设计时

**使用场景:**

✅ **Alex 设计复杂系统架构:**
```
用户: "设计一个支持 10 万并发的实时聊天系统"

Alex: "Let me use sequential-thinking to break down this complex architecture"

[MCP CALL]
问题分解:
1. WebSocket 连接管理
2. 消息持久化策略
3. 负载均衡方案
4. 实时同步机制
5. 扩展性设计

逐步推理每个组件...
```

**触发关键词:**
- "复杂"、"架构"、"系统设计"
- "算法"、"优化"、"大规模"

**建议场景:**
- 微服务架构设计
- 数据库设计(多表关系复杂)
- 算法设计和优化
- 技术选型决策

---

### 2.3 memory-bank 🧠

**用途:** 项目历史决策和上下文记忆

**效率提升:** 70-80%

**推荐调用:** Round 0 (需求分析开始前)

**使用场景:**

✅ **Alex 在 Round 0 (推荐):**
```
Alex 激活后,在 Round 1 开始前:

[RECOMMENDED CALL]
🧠 Memory Bank called
Query: "项目历史决策、相似需求、已有组件"

Found:
- 3 个月前实现过类似的用户认证功能
- 已有可复用的 Supabase Auth 封装
- 上次选择 PostgreSQL 是因为需要复杂查询

✓ Memory Bank Checked
  - Found 5 related decisions
  - Found 2 similar features
  - Found 3 reusable components

Alex 在 Round 1 中提到:
"我注意到我们 3 个月前实现过类似功能,可以复用那个 Auth 封装..."
```

✅ **Alex 在设计阶段回顾决策:**
```
Alex: "Let me check memory-bank for our previous database choices"

[MCP CALL]
Found:
- 之前选择 PostgreSQL 的原因文档
- 数据库性能优化经验
- Schema 设计最佳实践

Alex 设计时参考历史经验,避免重复错误
```

**存储内容:**
- 项目决策和原因
- 技术选型历史
- 已实现功能列表
- 经验教训
- 可复用组件库

**更新时机:**
- 每次 handoff 完成
- 重要决策做出
- 功能实现完成

---

### 2.4 filesystem 📁

**用途:** 文件和目录操作

**效率提升:** 基础必备

**使用者:** **仅 Blake (Agent B)**

**自动使用:** 所有文件操作

**禁止:** Alex 不能使用 (violation)

**使用场景:**

✅ **Blake 创建项目结构:**
```
Blake: *develop

[AUTO-USE filesystem MCP]
Creating project structure...
✓ src/app/page.tsx created
✓ src/components/Header.tsx created
✓ src/lib/supabase.ts created
✓ public/images/ directory created
```

✅ **Blake 读取配置文件:**
```
[AUTO-USE filesystem MCP]
Reading package.json...
Reading .env.local...
Reading tsconfig.json...
```

✅ **Blake 修改代码:**
```
[AUTO-USE filesystem MCP]
Updating src/app/layout.tsx...
Adding new component to src/components/...
```

**Pre-Flight Check (必需):**
```
Before *develop command:

✓ Filesystem MCP active
✓ Git MCP active
✓ Handoff document exists

[PROCEED]
```

---

### 2.5 git 🔀

**用途:** 版本控制操作

**效率提升:** 基础必备

**使用者:** **仅 Blake (Agent B)**

**自动使用:** 所有 Git 操作

**禁止:** Alex 不能使用 (violation)

**使用场景:**

✅ **Blake 自动提交代码:**
```
Blake: *develop (完成一个 task)

[AUTO-USE git MCP]
git add src/app/page.tsx
git add src/components/Header.tsx
git commit -m "feat: Add homepage and header component

Implemented:
- Homepage with hero section
- Responsive header with navigation
- Integrated Tailwind CSS styling

✅ Tests passed
✅ TypeScript checks passed
"
```

✅ **Blake 检查状态:**
```
[AUTO-USE git MCP]
git status
On branch feature/user-auth
Changes not staged for commit:
  modified: src/lib/auth.ts

git diff src/lib/auth.ts
[Shows changes]
```

**安全配置:**
- **自动批准:** `git status`, `git diff`, `git log`
- **需要确认:** `git push`, `git push --force`

---

### 2.6 github 🐙

**用途:** GitHub 协作 (PR/Issue/CI)

**效率提升:** 80-85%

**使用者:** Alex 和 Blake 都可以

**使用场景:**

✅ **Alex 创建 Issue:**
```
Alex: *task create issue

[USE github MCP]
Creating GitHub Issue...

Title: Implement user authentication with Supabase
Body:
## Requirements
- [ ] Email/password login
- [ ] OAuth (Google, GitHub)
- [ ] Session management

Assignee: @blake
Labels: feature, high-priority
```

✅ **Blake 创建 Pull Request:**
```
Blake: *deploy prepare PR

[USE github MCP]
Creating Pull Request...

Title: feat: User authentication with Supabase Auth
Body:
## Summary
- Implemented email/password login
- Added OAuth providers (Google, GitHub)
- Session management with cookies

## Test Plan
- [x] Unit tests passed
- [x] Integration tests passed
- [x] Manual testing completed

Ready for review! 🚀
```

---

### 2.7 brave-search 🔍

**用途:** 隐私优先的技术研究

**效率提升:** 技术研究必备

**使用者:** 主要是 Alex

**建议使用:** Round 2 技术不确定时

**使用场景:**

✅ **Alex 研究技术方案:**
```
用户: "我想用最新的 AI 工具做一个智能摘要功能"

Alex (Round 2): "Let me research the latest AI summarization tools"

[USE brave-search MCP]
Query: "Best AI text summarization APIs 2025"

Found:
1. OpenAI GPT-4 Turbo (最新)
2. Anthropic Claude 3 Opus (推荐)
3. Cohere Summarize API
4. Hugging Face models

Alex: "基于研究,我推荐使用 Claude 3 Opus API,因为..."
```

✅ **Alex 验证技术可行性:**
```
Alex: "Let me verify if Next.js 15 supports the new React Server Actions"

[USE brave-search MCP]
Query: "Next.js 15 React Server Actions support"

Found: 官方文档确认完全支持

Alex: "确认 Next.js 15 原生支持 Server Actions,可以使用"
```

**免费额度:** 2000 次/月

---

## 3. 项目层 MCP 按场景使用

### 3.1 Web 全栈应用 (web_fullstack)

**检测触发词:**
- Next.js, React, Vue, Nuxt, web, 网站, 全栈

**推荐安装 (Round 2.5):**

```
🎯 Project Type Detected: 🌐 Web 全栈应用
Confidence: 85%

📦 Recommended Project-Layer MCPs:

1. ✨ supabase - 数据库和后端服务
   Efficiency Gain: 85%

2. ✨ playwright - E2E 测试自动化
   Efficiency Gain: 80%

3. ⭐ vercel - 一键部署到生产环境
   Efficiency Gain: 90%

4. ⭐ react-mcp - React 组件开发辅助
   Efficiency Gain: 60%

Install Options:
0. Install all recommended (fastest) ←
1. Let me choose which to install
2. Skip for now

Select 0-2:
```

**使用示例:**

#### 3.1.1 supabase MCP

**Blake 使用:**
```
Blake: *develop

Task: 实现用户注册功能

[AUTO-USE supabase MCP]
Creating Supabase Auth client...
✓ supabase.auth.signUp() configured
✓ Email confirmation enabled
✓ RLS policies created

Code generated:
src/lib/supabase.ts
src/app/auth/register/page.tsx
```

#### 3.1.2 playwright MCP

**Blake 使用:**
```
Blake: *test

[USE playwright MCP]
Running E2E tests...

✓ User can register with email
✓ User can login
✓ Protected routes redirect to login
✓ User can logout

All E2E tests passed! 🎉
```

#### 3.1.3 vercel MCP

**Blake 使用:**
```
Blake: *deploy

[USE vercel MCP]
Deploying to Vercel...

✓ Build successful
✓ Deployed to: https://myapp-xyz.vercel.app
✓ Environment variables configured
✓ Domain ready

Deployment complete! 🚀
```

---

### 3.2 数据科学/分析 (data_science)

**检测触发词:**
- 数据分析, pandas, jupyter, 可视化, 图表

**推荐安装 (Round 2.5):**

```
🎯 Project Type Detected: 📊 数据科学/分析
Confidence: 78%

📦 Recommended Project-Layer MCPs:

1. ✨ jupyter - 交互式数据分析环境
   Efficiency Gain: 90%

2. ✨ pandas-mcp - 数据处理和清洗
   Efficiency Gain: 85%

3. ⭐ antv-chart - 专业数据可视化
   Efficiency Gain: 75%

4. ⭐ postgres-mcp-pro - 数据库性能优化
   Efficiency Gain: 70%

Install Options:
0. Install all recommended (fastest) ←
1. Let me choose which to install
2. Skip for now

Select 0-2:
```

**使用示例:**

#### 3.2.1 jupyter MCP

**Blake 使用:**
```
Blake: *develop

Task: 探索性数据分析

[USE jupyter MCP]
Starting Jupyter environment...

Creating notebook: analysis.ipynb
✓ Pandas imported
✓ Matplotlib configured
✓ Sample data loaded

Ready for interactive analysis! 📊
```

#### 3.2.2 pandas-mcp MCP

**Blake 使用:**
```
Blake: Processing sales data...

[USE pandas-mcp MCP]
Reading sales.csv...
✓ 10,000 rows loaded
✓ Missing values handled
✓ Data types corrected
✓ Duplicates removed

Clean dataset ready! ✓
```

#### 3.2.3 antv-chart MCP

**Blake 使用:**
```
Blake: Creating visualizations...

[USE antv-chart MCP]
Generating charts...

✓ Sales trend line chart created
✓ Revenue by category bar chart created
✓ Customer distribution pie chart created

Interactive dashboard ready! 📈
```

---

### 3.3 机器学习 (machine_learning)

**检测触发词:**
- 机器学习, 深度学习, 模型训练, AI, PyTorch

**推荐安装 (Round 2.5):**

```
🎯 Project Type Detected: 🤖 机器学习
Confidence: 92%

📦 Recommended Project-Layer MCPs:

1. ✨ jupyter - ML 实验和探索
   Efficiency Gain: 90%

2. ✨ optuna - 自动超参数优化
   Efficiency Gain: 85%

3. ✨ huggingface - 模型发现和加载
   Efficiency Gain: 90%

4. ⭐ zenml - MLOps 管道管理
   Efficiency Gain: 75%

5. ⭐ mlflow - 实验追踪和模型管理
   Efficiency Gain: 70%

Install Options:
0. Install all recommended (fastest) ←
1. Let me choose which to install
2. Skip for now

Select 0-2:
```

**使用示例:**

#### 3.3.1 optuna MCP

**Blake 使用:**
```
Blake: Optimizing model hyperparameters...

[USE optuna MCP]
Starting hyperparameter optimization...

Trial 1/100: learning_rate=0.001, batch_size=32 → accuracy=0.85
Trial 2/100: learning_rate=0.01, batch_size=64 → accuracy=0.88
...
Trial 100/100: learning_rate=0.005, batch_size=128 → accuracy=0.93

✓ Best params found: lr=0.005, batch=128
✓ Best accuracy: 93%

Optimization complete! 🎯
```

#### 3.3.2 huggingface MCP

**Blake 使用:**
```
Blake: Loading pre-trained model...

[USE huggingface MCP]
Searching Hugging Face Hub...

Found: bert-base-uncased
✓ Model downloaded
✓ Tokenizer loaded
✓ Ready for fine-tuning

Model loaded successfully! 🤗
```

---

### 3.4 DevOps/基础设施 (devops)

**检测触发词:**
- Kubernetes, Docker, 容器, CI/CD, 部署

**推荐安装 (Round 2.5):**

```
🎯 Project Type Detected: ⚙️ DevOps/基础设施
Confidence: 81%

📦 Recommended Project-Layer MCPs:

1. ✨ kubernetes - K8s 集群管理和部署
   Efficiency Gain: 85%

2. ✨ docker - 容器构建和管理
   Efficiency Gain: 80%

3. ⭐ aws - AWS 资源管理
   Efficiency Gain: 75%

4. ⭐ terminal - Shell 命令执行
   Efficiency Gain: 70%

Install Options:
0. Install all recommended (fastest) ←
1. Let me choose which to install
2. Skip for now

Select 0-2:
```

**使用示例:**

#### 3.4.1 kubernetes MCP

**Blake 使用:**
```
Blake: *deploy to K8s

[USE kubernetes MCP]
Deploying to Kubernetes...

✓ Deployment manifest created
✓ Service configured
✓ Ingress rules applied
✓ ConfigMap and Secrets synced

kubectl get pods
NAME                    READY   STATUS    RESTARTS
myapp-6d4b8f9c-abc12   1/1     Running   0

Deployment successful! ☸️
```

#### 3.4.2 docker MCP

**Blake 使用:**
```
Blake: Building container image...

[USE docker MCP]
Building Docker image...

Step 1/8: FROM node:20-alpine
Step 2/8: WORKDIR /app
Step 3/8: COPY package*.json ./
...
Step 8/8: CMD ["npm", "start"]

✓ Image built: myapp:latest
✓ Size: 145 MB

docker images
REPOSITORY   TAG      SIZE
myapp        latest   145MB

Build complete! 🐳
```

---

### 3.5 创意/多媒体 (creative)

**检测触发词:**
- Figma, 设计, 视频, 音频, 创意

**推荐安装 (Round 2.5):**

```
🎯 Project Type Detected: 🎨 创意/多媒体
Confidence: 76%

📦 Recommended Project-Layer MCPs:

1. ✨ figma - 设计转代码自动化
   Efficiency Gain: 85%

2. ✨ video-audio-mcp - 视频音频编辑自动化
   Efficiency Gain: 80%

3. ⭐ adobe-mcp - Adobe 工具集成
   Efficiency Gain: 75%

Install Options:
0. Install all recommended (fastest) ←
1. Let me choose which to install
2. Skip for now

Select 0-2:
```

**使用示例:**

#### 3.5.1 figma MCP

**Blake 使用:**
```
Blake: Converting Figma design to code...

[USE figma MCP]
Accessing Figma file...

✓ Design tokens extracted
✓ Components identified
✓ React components generated

Files created:
- src/components/Button.tsx
- src/components/Card.tsx
- src/styles/tokens.css

Design to code complete! 🎨
```

---

## 4. 任务层 MCP 临时安装

**特点:**
- 仅在特定任务需要时安装
- 用完后可以卸载
- 不计入核心或项目层

### 4.1 videodb MCP

**用途:** 高级 AI 视频处理 (转录、语义搜索、配音)

**安装:**
```bash
tad mcp install videodb
```

**使用场景:**
```
Blake: Processing video for AI analysis...

[USE videodb MCP]
Uploading video...
✓ Transcription complete
✓ Scene detection complete
✓ Semantic search index created

You can now search video by content!
```

**卸载:**
```bash
tad mcp uninstall videodb
```

---

### 4.2 design-system-extractor MCP

**用途:** 从 Storybook 提取设计系统

**安装:**
```bash
tad mcp install design-system-extractor
```

**使用场景:**
```
Blake: Extracting design tokens from Storybook...

[USE design-system-extractor MCP]
Analyzing Storybook...

✓ Colors extracted: 24 tokens
✓ Typography extracted: 12 styles
✓ Spacing extracted: 8 values
✓ Components documented: 45

Design system extracted! 🎨
```

---

### 4.3 pyairbyte MCP

**用途:** ETL 数据管道

**安装:**
```bash
tad mcp install pyairbyte
```

**使用场景:**
```
Blake: Setting up data pipeline...

[USE pyairbyte MCP]
Configuring Airbyte connectors...

✓ Source: PostgreSQL connected
✓ Destination: Snowflake connected
✓ Sync schedule: Daily at 2 AM
✓ Transformation rules applied

Data pipeline ready! 🔄
```

---

## 5. Alex (Agent A) 使用指南

### 5.1 Alex 的 MCP 工具包

**Core Layer (可用):**
- ✅ context7 - 自动获取最新文档
- ✅ sequential-thinking - 复杂问题分解
- ✅ memory-bank - 项目历史记忆
- ✅ brave-search - 技术研究

**Forbidden (禁止使用):**
- ❌ filesystem - Blake 的职责
- ❌ git - Blake 的职责
- ❌ docker - Blake 的职责
- ❌ kubernetes - Blake 的职责
- ❌ terminal - Blake 的职责

### 5.2 Alex 典型工作流中的 MCP

#### Round 0: Pre-Elicitation Checks

```
[Alex 激活后,Round 1 开始前]

Alex: "Let me check the project history before we start..."

[CALL memory-bank MCP]
🧠 Memory Bank checked
  - Found 3 related decisions
  - Found 1 similar feature
  - Found 2 reusable components

Alex: "I've reviewed our project history. I see we implemented
a similar auth system 2 months ago. We can potentially reuse
some components."

[PROCEED to Round 1]
```

#### Round 1-2: Context7 Auto-Trigger

```
用户: "我想用 Next.js 15 和 Supabase 做博客"

Alex: "Based on what you've told me, I understand that:
你想创建一个博客系统,使用 Next.js 15 作为框架..."

[AUTO-TRIGGER between Round 1-2]
⚡ Context7 called for: Next.js 15
✓ Latest Next.js 15 documentation loaded

⚡ Context7 called for: Supabase
✓ Latest Supabase documentation loaded

[Alex now has latest API knowledge]

Alex (Round 2): "我已经了解了 Next.js 15 的最新特性...
关于你的博客系统,我有几个关键问题..."
```

#### Round 2: Technical Research (if needed)

```
用户: "我需要实时协作编辑功能,像 Google Docs 那样"

Alex: "Let me research the best real-time collaboration
technologies for your use case..."

[USE brave-search MCP]
Query: "Best real-time collaboration libraries 2025 websocket"

Found:
1. Yjs + y-websocket (推荐)
2. Automerge
3. ShareDB
4. Liveblocks

Alex: "基于研究,我推荐使用 Yjs,因为它性能最好,
并且有成熟的 React 集成..."
```

#### Round 2.5: Project Type Detection

```
[After Round 2, tech stack confirmed]

[AUTO-DETECT project type]
分析中...
- Keywords: Next.js, React, Supabase, web, 博客
- Confidence: 87%

🎯 Project Type Detected: 🌐 Web 全栈应用
Confidence: 87%

📦 Recommended Project-Layer MCPs:
1. ✨ supabase - 数据库和后端服务
2. ✨ playwright - E2E 测试自动化
3. ⭐ vercel - 一键部署

Install Options:
0. Install all recommended (fastest) ←
1. Let me choose which to install
2. Skip for now

Select 0-2:

[WAIT for user response]

用户: "0"

[INSTALL project MCPs]
Installing supabase MCP... ✓
Installing playwright MCP... ✓
Installing vercel MCP... ✓

All recommended MCPs installed! 📦

[PROCEED to Round 3]
```

#### Design Phase: Complex Architecture

```
Alex: *design

Task: 设计实时协作博客系统架构

[USE sequential-thinking MCP]
Breaking down complex architecture...

1. WebSocket 连接管理
   - 使用 Supabase Realtime
   - 连接池策略
   - 断线重连机制

2. 数据同步
   - Yjs CRDT 算法
   - Conflict resolution
   - 增量更新

3. 数据持久化
   - Supabase PostgreSQL
   - 实时触发器
   - 版本历史

4. 性能优化
   - 客户端缓存
   - 服务端 debounce
   - 压缩传输

[USE context7 MCP]
Checking latest Supabase Realtime API...
✓ Latest best practices loaded

Alex: "Architecture design complete. Creating handoff document..."
```

#### Handoff Creation

```
Alex: *handoff

Creating handoff document for Blake...

[USE memory-bank MCP]
Checking similar past implementations...
Found: 之前的实时功能实现经验

[INCLUDE in handoff]
## MCP Tools Recommendation for Blake:
- ✅ supabase MCP - For Realtime and Database
- ✅ filesystem MCP - For file operations (required)
- ✅ git MCP - For version control (required)
- ✅ playwright MCP - For E2E testing

[GENERATE handoff document]
File: .tad/active/handoffs/realtime_blog_20250130.md

✓ Handoff complete! Please share with Blake in Terminal 2.
```

### 5.3 Alex 违规检测

**❌ Violation: Alex 尝试使用 filesystem**

```
Alex: "Let me create the file structure..."

[ATTEMPTING to use filesystem MCP]

⚠️ MCP VIOLATION ⚠️
Agent: Alex (Agent A)
Issue: Attempted to use filesystem MCP
Action: This is Blake's responsibility. Create handoff instead.

Alex: "Sorry, I cannot create files. That's Blake's job.
Let me create a handoff document for Blake to implement this."
```

---

## 6. Blake (Agent B) 使用指南

### 6.1 Blake 的 MCP 工具包

**Core Layer (必需):**
- ✅ filesystem (REQUIRED) - 文件操作
- ✅ git (REQUIRED) - 版本控制
- ✅ github - PR/Issue 管理

**Core Layer (增强):**
- ✅ context7 - 实现代码时自动获取文档

**Project Layer (根据 Alex 推荐):**
- 根据项目类型安装的工具

### 6.2 Blake 典型工作流中的 MCP

#### Pre-Flight Checks (必需)

```
[Blake 激活后]

Blake: "Hello! I'm Blake, your Execution Master. 💻"

[PRE-FLIGHT CHECKS]
Checking required MCP tools...

✓ filesystem MCP active
✓ git MCP active
✓ github MCP active

Checking for handoff document...
✓ Handoff found: realtime_blog_20250130.md

📦 Available MCP Tools:
  Core: filesystem ✓, git ✓, github ✓, context7 ✓
  Project: supabase ✓, playwright ✓, vercel ✓

All systems ready! What would you like me to implement?
```

#### *develop Command

```
用户: "*develop"

Blake: "Reading handoff document..."

[VERIFY handoff completeness]
✓ All required sections present
✓ Implementation steps clear
✓ Alex's MCP recommendations noted

[VERIFY required MCPs]
✓ filesystem MCP active
✓ git MCP active
✓ supabase MCP available (recommended by Alex)

[START implementation]

Task 1: Set up Supabase client
[AUTO-USE filesystem MCP]
Creating src/lib/supabase.ts...
✓ File created

[AUTO-USE supabase MCP]
Configuring Supabase client...
✓ Realtime enabled
✓ Auth configured

[AUTO-USE git MCP]
git add src/lib/supabase.ts
git commit -m "feat: Set up Supabase client with Realtime"
✓ Committed

Task 2: Implement real-time editor
[AUTO-TRIGGER context7 MCP]
⚡ Getting latest Yjs + Supabase integration docs...
✓ Latest patterns loaded

[AUTO-USE filesystem MCP]
Creating src/components/RealtimeEditor.tsx...
✓ File created

[AUTO-USE git MCP]
git add src/components/RealtimeEditor.tsx
git commit -m "feat: Implement real-time collaborative editor"
✓ Committed

All tasks complete! ✓
```

#### *test Command

```
Blake: "*test"

[USE playwright MCP]
Running E2E tests...

Test 1: User can create a post
  ✓ Navigate to /new-post
  ✓ Type content in editor
  ✓ Click publish
  ✓ Post appears in list

Test 2: Real-time collaboration works
  ✓ Open post in two browser tabs
  ✓ Edit in tab 1
  ✓ Changes appear in tab 2 within 100ms
  ✓ No conflicts

All tests passed! 🎉

[AUTO-USE git MCP]
git add tests/
git commit -m "test: Add E2E tests for real-time features"
✓ Committed
```

#### *deploy Command

```
Blake: "*deploy"

[USE vercel MCP]
Deploying to Vercel...

Building...
  ✓ Next.js build complete
  ✓ Type checks passed
  ✓ Linting passed

Deploying...
  ✓ Uploaded to Vercel
  ✓ Deployment: https://realtime-blog-xyz.vercel.app
  ✓ Environment variables synced

Deployment successful! 🚀

[AUTO-USE git MCP]
git tag v1.0.0
git push origin v1.0.0
✓ Tagged and pushed
```

### 6.3 Blake 违规检测

**❌ Violation: Blake 尝试开始但 filesystem MCP 不可用**

```
Blake: "*develop"

[PRE-FLIGHT CHECKS]
Checking required MCP tools...

✓ git MCP active
❌ filesystem MCP NOT ACTIVE

⚠️ MCP VIOLATION ⚠️
Agent: Blake (Agent B)
Issue: filesystem MCP is required but not available
Action: HALT - Cannot proceed without filesystem access

Blake: "I cannot proceed without filesystem MCP.
Please install it with: tad mcp install --core"

[HALT execution]
```

---

## 7. 常见问题解答

### 7.1 关于 MCP 必需性

**Q: MCP 工具是必需的吗?**

A: **不是。** TAD 核心功能在没有 MCP 的情况下完全可用:
- ✅ 三角模型
- ✅ 3-5 轮需求确认
- ✅ Handoff 机制
- ✅ Sub-agents 调用

MCP 是**增强工具**,提升效率 70-85%,但不是必需的。

**例外:** Blake 的 `filesystem` 和 `git` MCP 在实际开发时是必需的,
但在设计和讨论阶段不需要。

---

**Q: 如果某个 MCP 工具失败了怎么办?**

A: **不阻塞流程。**

```
[MCP CALL FAILED]
⚠️ context7 MCP failed to load Next.js docs
Fallback: Using Claude Code built-in knowledge
Logging error for future improvement

[CONTINUE with workflow]
```

TAD 会回退到内置能力,记录错误,但不停止工作。

---

### 7.2 关于 MCP 安装

**Q: 必须安装所有 MCP 工具吗?**

A: **不必须。**

- **Layer 1 (Core):** 强烈推荐全部安装 (7个)
- **Layer 2 (Project):** 根据项目类型选择性安装
- **Layer 3 (Task):** 按需临时安装

最小配置:
```bash
# 仅安装 Blake 必需的
tad mcp install filesystem
tad mcp install git
```

---

**Q: 如何知道该安装哪些 Project-Layer MCPs?**

A: **Alex 会在 Round 2.5 自动推荐。**

```
1. 你在 Round 1-2 描述需求
2. Alex 检测项目类型
3. Alex 在 Round 2.5 推荐 MCPs
4. 你选择 0(全装) / 1(选装) / 2(跳过)
```

如果不确定,选择 **0(全装)** 是最安全的。

---

**Q: 可以稍后再安装 MCP 吗?**

A: **可以。**

```bash
# 随时安装
tad mcp install supabase

# 查看已安装
tad mcp list --installed

# 卸载不需要的
tad mcp uninstall videodb
```

---

### 7.3 关于 MCP 使用

**Q: 如何知道 MCP 何时被调用?**

A: **Alex 和 Blake 会明确告知。**

```
⚡ Context7 called for: Next.js 15
✓ Latest documentation loaded

[AUTO-USE filesystem MCP]
Creating src/app/page.tsx...
✓ File created
```

所有 MCP 调用都会显示。

---

**Q: 可以强制不使用某个 MCP 吗?**

A: **可以。**

临时禁用:
```
用户: "请不要使用 context7,我想测试没有最新文档的情况"

Alex: "Understood. I will not use context7 for this task."
```

或者卸载:
```bash
tad mcp uninstall context7
```

---

**Q: Alex 和 Blake 如何知道对方安装了哪些 MCP?**

A: **通过 Handoff 文档。**

Alex 在 handoff 中推荐 Blake 使用的 MCP:
```markdown
## MCP Tools Recommendation for Blake:
- ✅ supabase MCP - For database operations
- ✅ playwright MCP - For E2E testing
- ✅ vercel MCP - For deployment
```

Blake 收到 handoff 后检查这些 MCP 是否可用。

---

### 7.4 关于效率提升

**Q: MCP 真的能提升 70-85% 效率吗?**

A: **基于以下估算:**

**需求分析阶段:**
- **传统:** 手动查文档 + 调研 = 2-3 小时
- **MCP:** context7 + memory-bank + brave-search = 30-45 分钟
- **提升:** ~75%

**设计阶段:**
- **传统:** 手动设计 + 查最佳实践 = 4-6 小时
- **MCP:** sequential-thinking + context7 = 1-2 小时
- **提升:** ~70%

**实现阶段:**
- **传统:** 手动创建文件 + 手动 Git = 2-3 天
- **MCP:** filesystem + git + project MCPs = 6-12 小时
- **提升:** ~75%

**整体:** 70-85% 效率提升

---

**Q: 具体节省多少时间?**

A: **示例 (Web 全栈博客项目):**

| 阶段 | 传统耗时 | MCP 耗时 | 节省 |
|------|---------|---------|------|
| 需求分析 | 3 小时 | 45 分钟 | 75% |
| 架构设计 | 5 小时 | 1.5 小时 | 70% |
| 实现开发 | 3 天 | 12 小时 | 75% |
| 测试验证 | 1 天 | 3 小时 | 80% |
| 部署上线 | 4 小时 | 30 分钟 | 87% |
| **总计** | **~5.5 天** | **~1.5 天** | **~73%** |

---

## 8. 故障排除

### 8.1 MCP 安装问题

**问题:** `tad mcp install --core` 失败

**解决:**

1. 检查网络连接
```bash
ping registry.npmjs.org
```

2. 检查 Node.js 版本
```bash
node --version  # 需要 >= 18.0.0
```

3. 清理 npm 缓存
```bash
npm cache clean --force
tad mcp install --core
```

4. 手动安装单个 MCP
```bash
npx -y @upstash/context7-mcp@latest
```

---

### 8.2 MCP 调用失败

**问题:** context7 调用超时

**症状:**
```
⚡ Context7 called for: Next.js
❌ Timeout after 30s
```

**解决:**

1. 检查 API key (如果需要)
```bash
echo $UPSTASH_API_KEY
```

2. 重试调用
```
Alex: "Try context7 again for Next.js"
```

3. 使用 fallback
```
Alex 会自动回退到内置知识
不影响工作流程继续
```

---

### 8.3 Blake 无法启动开发

**问题:** Blake 报告 "filesystem MCP not active"

**解决:**

1. 检查 MCP 状态
```bash
tad mcp list --installed
```

2. 重新安装 filesystem
```bash
tad mcp install filesystem
```

3. 验证安装
```bash
tad mcp test filesystem
```

4. 重新激活 Blake
```
/blake
```

---

### 8.4 项目类型检测不准确

**问题:** Round 2.5 检测到错误的项目类型

**解决:**

**方法 1: 在 Round 1-2 明确说明**
```
用户: "这是一个 Web 全栈项目,使用 Next.js"
```

**方法 2: 在 Round 2.5 选择 "1" 手动选择**
```
Install Options:
0. Install all recommended
1. Let me choose which to install ← 选这个
2. Skip for now

Select 0-2: 1

然后手动选择需要的 MCP
```

**方法 3: Round 2.5 后手动安装**
```bash
# 跳过 Round 2.5
Select 0-2: 2

# 稍后手动安装
tad mcp install --preset web_fullstack
```

---

### 8.5 MCP 日志查看

**查看 MCP 使用日志:**
```bash
cat .tad/logs/mcp_usage.log
```

**查看项目类型检测日志:**
```bash
cat .tad/logs/project_detection.log
```

**查看违规日志:**
```bash
cat .tad/logs/violations.log
```

---

## 📚 更多资源

- **TAD 框架文档:** `README.md`
- **MCP Registry:** `.tad/mcp-registry.yaml`
- **项目检测配置:** `.tad/project-detection.yaml`
- **MCP 集成总结:** `.tad/MCP_INTEGRATION_SUMMARY.md`

---

## 🆘 获取帮助

**问题反馈:**
- GitHub Issues: [TAD Repository]
- 文档: [TAD Framework Docs]

**快速命令:**
```bash
# 查看 MCP 帮助
tad mcp --help

# 检查 MCP 状态
tad mcp status

# 测试 MCP 连接
tad mcp test --all
```

---

**祝你使用 TAD + MCP 高效开发! 🚀**
