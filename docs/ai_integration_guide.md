# PersonalManager AI集成指南

> **版本**: v1.0
> **更新时间**: 2025-09-13
> **目标用户**: 希望通过AI工具（Claude Code、Gemini CLI）来使用PersonalManager的用户

## 📖 概述

PersonalManager采用"AI-first"设计理念，你可以通过自然语言对话来管理所有个人效能功能，而不需要记忆复杂的命令行语法。本指南将帮助你配置和使用AI集成功能。

## 🎯 AI集成的两种层次

### 当前状态（Phase 1）- AI作为智能交互界面
```
你的自然语言 → AI理解意图 → 执行对应命令 → 返回结果
```

**示例对话**:
- 你："帮我查看今天应该做什么"
- Claude执行：`pm today`
- 显示智能推荐的任务列表

### 未来计划（Phase 2-3）- 真正的AI自动化
- **主动监控**: 系统发现项目问题时主动提醒
- **智能报告**: AI自动分析项目健康度和效率模式
- **学习偏好**: 根据你的使用习惯个性化推荐
- **上下文感知**: 基于当前状态和环境智能建议行动

## 🔧 Claude Code 集成配置

Claude Code是Anthropic官方的AI编程助手，通过配置可以让Claude直接控制PersonalManager。

### 步骤1: 复制配置模板
```bash
# 创建Claude配置目录
mkdir -p ~/.claude

# 复制官方模板
cp configs/agent-templates/claude/settings.sample.json ~/.claude/settings.json
```

### 步骤2: 编辑配置文件
打开 `~/.claude/settings.json`，修改以下关键配置：

```json
{
  "api": {
    "anthropic_api_key": "sk-ant-api-你的真实密钥",
    "model": "claude-3-5-sonnet-20241022",
    "temperature": 0.1
  },
  "workspace": {
    "default_project_path": "~/projects",
    "preferred_language": "zh",
    "timezone": "Asia/Shanghai"
  },
  "personalmanager_integration": {
    "enabled": true,
    "pm_command": "pm",
    "auto_register_tools": true,
    "context_sharing": {
      "tasks": true,
      "projects": true,
      "preferences": true
    }
  },
  "tools": {
    "pm_capture": { "enabled": true },
    "pm_today": { "enabled": true, "default_count": 3 },
    "pm_projects": { "enabled": true },
    "pm_recommend": { "enabled": true, "context_aware": true }
  }
}
```

### 步骤3: 验证Claude Code集成
在Claude Code中测试以下对话：

```
你: "帮我查看今天的推荐任务"
Claude: [执行] pm today --count 3
[显示今日推荐任务列表]

你: "记录一个任务：准备周五的演示PPT"
Claude: [执行] pm capture "准备周五的演示PPT"
[确认任务已捕获到收件箱]
```

## 🔧 Gemini CLI 集成配置

Gemini CLI是Google的命令行AI工具，同样支持PersonalManager集成。

### 步骤1: 复制配置模板
```bash
# 创建Gemini配置目录
mkdir -p ~/.gemini

# 复制官方模板
cp configs/agent-templates/gemini/settings.sample.json ~/.gemini/config.json
```

### 步骤2: 编辑配置文件
打开 `~/.gemini/config.json`，修改关键配置：

```json
{
  "api": {
    "google_api_key": "AIzaSy-你的真实密钥",
    "model": "gemini-1.5-pro-latest",
    "generation_config": {
      "temperature": 0.1,
      "top_p": 0.8,
      "max_output_tokens": 8192
    }
  },
  "workspace": {
    "project_root": "~/projects",
    "preferred_locale": "zh-CN",
    "timezone": "Asia/Shanghai"
  },
  "personalmanager_tools": {
    "enabled": true,
    "pm_binary_path": "pm",
    "command_mapping": {
      "task_capture": "pm capture",
      "daily_recommend": "pm today",
      "project_overview": "pm projects overview",
      "smart_recommend": "pm recommend"
    }
  },
  "safety": {
    "privacy_mode": true,
    "data_retention": "session_only"
  }
}
```

### 步骤3: 验证Gemini CLI集成
在Gemini CLI中测试：

```
你: "显示我的项目状态概览"
Gemini: [执行] pm projects overview
[显示所有项目的健康状态和进度]

你: "我想整理一下待办事项"
Gemini: [执行] pm clarify
[启动交互式GTD理清流程]
```

## 🎯 自然语言 → 命令映射表

AI会自动将你的自然语言转换为精确的PersonalManager命令：

### 项目管理类
| 你说的话 | AI执行的命令 | 功能说明 |
|---------|-------------|----------|
| "看看我有哪些项目" | `pm projects overview` | 显示所有项目概览 |
| "XXX项目进展如何" | `pm project status "XXX"` | 查看特定项目详情 |
| "我的项目健康状况" | `pm projects overview` | 项目健康度分析 |

### 任务管理类
| 你说的话 | AI执行的命令 | 功能说明 |
|---------|-------------|----------|
| "记录一个想法/任务" | `pm capture "..."` | 快速捕获到收件箱 |
| "整理我的待办清单" | `pm clarify` | GTD理清流程 |
| "今天做什么" | `pm today` | 智能推荐3个任务 |
| "给我更多建议" | `pm recommend --count 5` | 扩展推荐列表 |
| "为什么推荐这个任务" | `pm explain <任务ID>` | 解释推荐原因 |

### 时间管理类
| 你说的话 | AI执行的命令 | 功能说明 |
|---------|-------------|----------|
| "开始深度工作" | `pm deepwork start` | 启动专注模式 |
| "结束工作，记录成果" | `pm deepwork end` | 结束并反思 |
| "查看我的习惯" | `pm habits today` | 今日习惯计划 |
| "这周工作总结" | `pm review weekly` | 生成周回顾 |

### 外部集成类
| 你说的话 | AI执行的命令 | 功能说明 |
|---------|-------------|----------|
| "同步我的Obsidian笔记" | `pm obsidian sync` | 同步知识库 |
| "检查日历安排" | `pm calendar sync` | 同步Google日历 |
| "处理重要邮件" | `pm gmail scan` | 扫描重要邮件 |

## 🚀 实际使用演示

### 场景1：每日工作规划
```
你: "早上好，帮我规划一下今天的工作"

AI: 让我先查看你的项目状态和今日推荐。
[执行] pm projects overview
[执行] pm today

根据当前项目状态，建议你优先处理以下3个任务：
1. [高优先级] 完成项目A的技术文档
2. [适合上午] 代码审查和优化
3. [下午精力低时] 整理邮件和回复

---

## 项目级指令编译（规划）

> 为了让 Claude/Gemini 在进入项目后即具备 PersonalManager 专家身份，我们将提供编译器从工作空间配置生成“项目指令”。

### 步骤（文档先行）
```bash
# 在项目根目录生成三件套
pm workspace init

# 生成项目级指令
pm agent prompt --write
```

### Claude / Gemini 接入（示意）
- Claude：在项目内存在 `.claude/project-instructions.md` 后，新会话会自动参考该文件。
- Gemini：向 `~/.gemini/config.json` 追加一段 PM 指令片段，或在会话开场以 System 指令载入。

### 行为准则（精简）
- 会话开场执行“启动仪式”（doctor/today）
- 自然语言→命令的路由规则以 `interaction-patterns.json` 为准
- 低置信度先确认，高置信度可直接执行（需用户同意）

需要我帮你开始深度工作模式吗？
```

### 场景2：项目健康检查
```
你: "我的项目们现在情况怎么样？"

AI: 让我检查所有项目的健康状况。
[执行] pm projects overview

📊 项目概览：
• 项目A (85%) - 健康状态良好，按计划进行
• 项目B (45%) - ⚠️ 有风险，3天未更新
• 项目C (100%) - ✅ 已完成

建议重点关注项目B，需要我查看详细状态吗？
```

### 场景3：任务捕获和理清
```
你: "突然想到要准备下周的客户演示，还有修复那个登录bug"

AI: 我来帮你记录这些任务。
[执行] pm capture "准备下周的客户演示"
[执行] pm capture "修复登录bug"

✅ 已捕获2个任务到收件箱。要不要现在理清一下所有待办事项？
[执行] pm clarify

现在可以开始分类和安排优先级了...
```

## 🔍 故障排查

### 常见问题及解决方案

#### 1. AI提示找不到pm命令
**原因**: PersonalManager未正确安装或不在PATH中

**解决方案**:
```bash
# 检查安装状态
pm --version

# 如果未安装，使用pipx安装
pipx install personal-manager

# 或强制重新安装
pipx install personal-manager --force
```

#### 2. API密钥无效
**现象**: AI提示"API认证失败"

**解决方案**:
1. 检查配置文件中的API密钥格式
2. 确认密钥有效且有足够使用额度
3. 验证配置文件JSON格式正确

```bash
# 验证配置文件格式
cat ~/.claude/settings.json | python -m json.tool    # Claude
cat ~/.gemini/config.json | python -m json.tool     # Gemini
```

#### 3. 系统未初始化
**现象**: AI执行命令时提示"系统未初始化"

**解决方案**:
```bash
# 运行系统初始化
pm setup --guided

# 验证安装
pm doctor
```

#### 4. 权限问题
**现象**: 提示数据目录权限不足

**解决方案**:
```bash
# 检查系统状态
pm doctor

# 验证数据完整性
pm privacy verify

# 如需重置权限
pm setup --reset
```

## 📋 最佳实践建议

### 1. 从简单对话开始
刚开始使用时，建议从这些简单对话开始熟悉：
- "帮我看看项目状态"
- "今天做什么"
- "记录一个想法"

### 2. 利用AI的自然理解能力
不需要记忆精确的命令格式，用自然语言描述你的需求：
- ❌ 不要说："执行pm projects overview命令"
- ✅ 要说："我想了解项目们的情况"

### 3. 建立日常工作流程
通过AI建立固定的工作模式：
```
每天开始: "早上好，帮我规划今天的工作"
工作中: "开始深度工作" / "记录一个想法"
每天结束: "今天工作总结"
每周回顾: "这周的工作情况如何"
```

### 4. 充分利用上下文理解
AI会记住对话上下文，可以进行连续对话：
```
你: "看看我的项目状态"
AI: [显示项目列表]
你: "项目A的详细情况如何？"  # AI会自动理解指的是刚才提到的项目A
AI: [执行] pm project status "项目A"
```

## 🔮 未来功能预览

随着Phase 2和Phase 3的开发完成，你将体验到：

### Phase 2 - 完善的用户体验
- **一行安装**: `npx @personal-manager/pm-bootstrap`
- **智能诊断**: AI自动发现和解决环境问题
- **端到端测试**: 保证所有功能稳定可靠

### Phase 3 - 真正的AI自动化
- **主动监控**: "你的项目A已经3天没更新，需要关注一下"
- **智能报告**: "根据数据分析，你在上午效率最高"
- **学习偏好**: "基于你的习惯，建议现在做深度工作"
- **上下文推荐**: 系统理解你当前的工作状态和环境

## 📞 获取帮助

### 文档资源
- [用户指南](user_guide.md) - 完整功能说明
- [工具注册指南](tool_registration.md) - 详细的Agent集成说明
- [故障排查](troubleshooting.md) - 错误代码和解决方案

### 验证命令
```bash
# 检查PersonalManager状态
pm --version
pm doctor

# 测试核心功能
pm test smoke --quick

# 检查AI配置
pm help
```

### 快速测试AI集成
配置完成后，在AI工具中尝试：
1. "帮我检查系统状态" → 应该执行 `pm doctor`
2. "今天做什么" → 应该执行 `pm today`
3. "记录一个测试任务" → 应该执行 `pm capture`

如果以上测试都通过，说明AI集成配置成功！

## 📚 更多资源

### Prompt 编译器样例
查看完整的工作空间配置和编译输出样例：
- **输入样例**: [docs/samples/prompt_compiler/inputs/](../samples/prompt_compiler/inputs/)
  - workspace-config.yaml - 工作空间配置示例
  - ai-agent-definition.md - AI 代理定义示例
  - interaction-patterns.json - 自然语言映射规则示例
  - profile.md - 用户偏好记忆示例
- **输出样例**: [docs/samples/prompt_compiler/outputs/](../samples/prompt_compiler/outputs/)
  - claude_project_instructions.md - Claude 平台编译输出
  - gemini_config_snippet.json - Gemini 平台配置片段

---

**文档版本**: v1.1
**最后更新**: 2025-09-14
**维护者**: PersonalManager开发团队

欢迎通过GitHub Issues反馈使用问题和改进建议！
