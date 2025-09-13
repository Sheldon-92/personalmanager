# PersonalManager 更新日志

本文档记录了 PersonalManager 项目的所有重要变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
并且本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [0.1.0] - 2025-01-15

### 新增 (Added)

#### 🔧 PersonalManager Agent CLI 核心功能
- **AI原生设计**: 针对与AI Agent自然语言交互优化的命令行界面
- **`pm today` 快速日程指令**: 获取今日重点推荐，默认不超过3项，基于多种生产力理论
- **`pm projects overview` 项目概览功能**: 查看所有项目状态，支持健康度、优先级排序
- **交互式设置向导**: `pm setup` 命令提供完整的系统配置流程
- **非交互式环境自动配置支持**: 检测运行环境并自动调整配置策略

#### 🗂️ GTD、原子习惯、深度工作模块支持
- **完整GTD工作流实现**:
  - `pm capture "任务内容"`: 快速捕获任务到收件箱
  - `pm inbox`: 查看收件箱中待处理的任务
  - `pm clarify`: 启动交互式GTD理清流程
  - `pm next`: 查看下一步行动清单
  - `pm recommend --count N`: 基于AI的智能任务推荐
  - `pm explain <任务ID>`: 解释推荐背后的决策逻辑

- **基于《原子习惯》的习惯管理系统**:
  - `pm habits create`: 创建新习惯，支持提示-惯例-奖励循环
  - `pm habits track`: 记录习惯完成情况和质量评分
  - `pm habits today`: 查看今日习惯计划
  - `pm habits trends`: 分析习惯趋势和完成率

- **基于《深度工作》的专注时段管理**:
  - `pm deepwork` 命令组提供完整的深度工作时段管理
  - 支持时段创建、开始、结束和反思功能
  - 与日程系统集成，避免冲突

#### 📁 本地文件存储系统
- **隐私优先设计**: 所有数据存储在 `~/.personalmanager/` 本地目录
- **JSON/Markdown格式**: 人类可读的数据格式，便于备份和迁移
- **离线优先**: 核心功能无需网络连接即可使用
- **完整的数据管理**: 导出、备份、清理和完整性验证功能

#### 🔗 可选外部集成
- **Google服务集成** (可选):
  - `pm auth login/logout`: Google服务认证管理
  - `pm calendar sync`: 同步Google Calendar事件为GTD任务
  - `pm gmail scan`: 扫描重要邮件并转换为任务
  - `pm tasks sync-from/sync-to`: 与Google Tasks双向同步

- **Obsidian集成** (可选): 
  - 知识库连接和笔记创建
  - 任务与笔记系统的双向同步

#### 🤖 AI驱动的智能推荐引擎
- **多理论融合**: 整合GTD、原子习惯、深度工作等19本书籍的智慧
- **上下文感知**: 基于当前时间、精力水平、可用工具的智能推荐
- **学习能力**: 基于用户反馈不断优化推荐质量
- **解释性AI**: 每个推荐都可以查看详细的决策逻辑

### 变更 (Changed)

#### 🎨 主界面体验优化
- **状态感知显示**: 主界面不再直接显示帮助信息，而是智能检测初始化状态
- **友好欢迎界面**: 首次使用显示设置引导，已配置用户显示快捷操作面板
- **上下文帮助**: 根据用户状态提供相关的下一步建议

#### 🔧 配置初始化逻辑优化
- **智能检测**: 自动识别是否为首次使用，提供对应的引导流程
- **非阻塞配置**: 支持在未完全配置的情况下使用基础功能
- **配置验证**: 增强的配置完整性检查和修复建议

### 安全性 (Security)

#### 🔒 隐私优先设计
- **默认本地存储**: 所有用户数据存储在本地 `~/.personalmanager/` 目录，用户完全控制
- **Google集成默认关闭**: 外部服务集成采用显式启用策略，默认不连接任何云服务
- **本地存储，无强制云同步**: 用户可选择是否使用云服务，核心功能完全离线可用
- **API凭证安全管理**: 支持安全的token存储和刷新机制
- **数据完整性验证**: `pm privacy verify` 提供完整的数据安全检查

### 已知问题 (Known Issues)

### 修复 (Fixed)

- 修复 `pm privacy verify`、`pm privacy cleanup`、`pm privacy clear` 由于同名函数遮蔽导致的递归调用问题：
  - 为工具层函数引入别名（`*_tool`），CLI 包装函数调用别名以避免递归。
  - 位置：`src/pm/cli/commands/privacy.py`
  - 影响：命令不再发生递归或崩溃，验证流程可正常完成。

#### ⚠️ 平台和环境限制
- **平台兼容性**: 主要在macOS和Linux上测试，Windows平台兼容性需进一步验证
- **Python版本要求**: 需要Python 3.9+，部分功能可能在旧版本上不可用
- **依赖服务配置**: Google服务集成需要用户自行申请和配置API凭证

#### 🚧 功能完善度
- **AI推荐算法**: 部分高级推荐功能仍在持续优化中
- **错误处理**: 某些边界情况的错误处理可能不够完善
- **文件监控**: 在不同操作系统上的文件监控行为可能存在差异

#### 📚 文档完善性
- **示例更新**: 文档中的部分示例可能需要根据实际使用场景调整
- **最佳实践**: 需要更多实际使用案例来完善最佳实践指南

### 技术栈 (Technical)

#### 📦 核心依赖
- **Python**: ^3.9
- **CLI框架**: Typer ^0.9.0, Click ^8.1.7, Rich ^13.6.0
- **数据处理**: Pydantic ^2.4.2, PyYAML ^6.0.1
- **AI集成**: Anthropic ^0.3.11, Google-GenerativeAI ^0.3.0
- **监控**: Watchdog ^3.0.0, Structlog ^23.1.0

#### 🧪 开发工具
- **代码质量**: Black, isort, flake8, mypy, pre-commit
- **测试**: pytest, pytest-cov, pytest-asyncio, factory-boy

---

## 如何升级

从无到有安装：
```bash
git clone <repository-url>
cd personal-manager
poetry install
poetry run pm setup
```

查看更多信息：
- [用户指南](docs/user_guide.md)
- [技术文档](docs/)
- [项目状态指南](docs/PROJECT_STATUS_GUIDE.md)

---

**注意**: 这是 PersonalManager 的首个正式版本。我们建议用户在生产环境使用前先进行充分测试。

[0.1.0]: https://github.com/personalmanager/personalmanager/releases/tag/v0.1.0

---

Last Updated: 2025-01-15
