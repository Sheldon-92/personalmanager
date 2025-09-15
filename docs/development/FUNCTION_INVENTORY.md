# PersonalManager 功能库存盘点

> **目的**: 完整记录系统中所有可用功能，避免重复开发和功能遗漏。
> **更新时间**: 2025-09-15 01:25
> **盘点范围**: CLI命令、脚本、集成服务、自动化任务

---

## 📋 CLI命令完整清单

### 🏠 核心系统命令

| 命令 | 功能描述 | 使用频率 | 状态 |
|------|----------|---------|------|
| `pm` | 主入口，显示系统状态 | 高 | ✅ 完全可用 |
| `pm --version` | 显示版本信息 | 低 | ✅ 完全可用 |
| `pm setup` | 系统设置向导 | 低 | ✅ 完全可用 |
| `pm help` | 显示帮助信息 | 中 | ✅ 完全可用 |
| `pm doctor` | 系统环境诊断 | 中 | ✅ 完全可用 |

### 📝 GTD任务管理

| 命令 | 功能描述 | 使用频率 | 状态 |
|------|----------|---------|------|
| `pm capture "任务"` | 快速捕获任务到收件箱 | 高 | ✅ 完全可用 |
| `pm inbox` | 显示收件箱任务列表 | 高 | ✅ 完全可用 |
| `pm clarify` | 启动GTD任务理清流程 | 中 | ✅ 完全可用 |
| `pm next` | 显示下一步行动列表 | 高 | ✅ 完全可用 |
| `pm smart-next` | 智能情境过滤的下一步行动 | 中 | ✅ 完全可用 |
| `pm recommend` | AI智能任务推荐 | 高 | ✅ 完全可用 |
| `pm today` | 今日重点推荐（recommend别名） | 高 | ✅ 完全可用 |
| `pm explain <ID>` | 解释任务推荐逻辑 | 中 | ✅ 完全可用 |
| `pm task <ID>` | 显示任务详细信息 | 中 | ✅ 完全可用 |

### 🏃‍♂️ 习惯管理

| 命令 | 功能描述 | 使用频率 | 状态 |
|------|----------|---------|------|
| `pm habits create` | 创建新习惯 | 低 | ✅ 完全可用 |
| `pm habits status` | 习惯完成状态总览 | 高 | ✅ 完全可用 |
| `pm habits today` | 今日习惯计划 | 高 | ✅ 完全可用 |
| `pm habits track` | 记录习惯完成情况 | 高 | ✅ 完全可用 |
| `pm habits trends` | 习惯趋势分析 | 中 | ✅ 完全可用 |
| `pm habits suggest` | 习惯改进建议 | 低 | ✅ 完全可用 |

### 💼 项目管理

| 命令 | 功能描述 | 使用频率 | 状态 |
|------|----------|---------|------|
| `pm project` | 项目管理命令 | 中 | ✅ 完全可用 |
| `pm projects` | 项目状态管理工具 | 中 | ✅ 完全可用 |
| `pm report` | AI驱动的项目报告生成 | 低 | ✅ 完全可用 |
| `pm monitor` | 项目文件监控工具 | 低 | ✅ 完全可用 |

### 🧠 深度工作

| 命令 | 功能描述 | 使用频率 | 状态 |
|------|----------|---------|------|
| `pm deepwork` | 深度工作时段管理 | 中 | ✅ 完全可用 |

### 📚 学习与回顾

| 命令 | 功能描述 | 使用频率 | 状态 |
|------|----------|---------|------|
| `pm review` | 回顾与反思管理 | 中 | ✅ 完全可用 |
| `pm learn` | 智能分类学习统计 | 低 | ✅ 完全可用 |
| `pm preferences` | 用户偏好学习统计 | 低 | ✅ 完全可用 |

### 🤖 AI集成

| 命令 | 功能描述 | 使用频率 | 状态 |
|------|----------|---------|------|
| `pm ai` | AI助手集成入口 | 中 | ✅ 完全可用 |
| `pm ai route <query>` | AI查询路由 | 中 | ✅ 完全可用 |
| `pm ai status` | AI服务状态检查 | 低 | ✅ 完全可用 |
| `pm ai config` | AI服务配置管理 | 低 | ✅ 完全可用 |

### 🔗 外部服务集成

#### Google服务
| 命令 | 功能描述 | 使用频率 | 状态 |
|------|----------|---------|------|
| `pm auth` | Google服务认证管理 | 低 | ✅ 完全可用 |
| `pm auth login` | Google服务登录 | 低 | ✅ 完全可用 |
| `pm auth logout` | Google服务登出 | 低 | ✅ 完全可用 |
| `pm calendar` | Google Calendar集成 | 中 | ✅ 完全可用 |
| `pm calendar sync` | 同步日历事件为任务 | 中 | ✅ 完全可用 |
| `pm gmail` | Gmail重要邮件处理 | 中 | ✅ 完全可用 |
| `pm gmail scan` | 扫描重要邮件转任务 | 中 | ✅ 完全可用 |
| `pm tasks` | Google Tasks集成 | 高 | ✅ 完全可用 |
| `pm tasks sync-from` | 从Google Tasks同步 | 中 | ✅ 完全可用 |
| `pm tasks sync-to` | 同步到Google Tasks | 中 | ✅ 完全可用 |

#### Obsidian集成
| 命令 | 功能描述 | 使用频率 | 状态 |
|------|----------|---------|------|
| `pm obsidian` | Obsidian集成管理 | 中 | ✅ 完全可用 |

### 🔒 数据管理

| 命令 | 功能描述 | 使用频率 | 状态 |
|------|----------|---------|------|
| `pm privacy` | 数据隐私管理工具 | 低 | ✅ 完全可用 |
| `pm privacy verify` | 数据完整性验证 | 低 | ✅ 完全可用 |
| `pm privacy cleanup` | 清理临时数据 | 低 | ✅ 完全可用 |
| `pm privacy clear` | 完整数据清除 | 低 | ✅ 完全可用 |

### 📖 辅助工具

| 命令 | 功能描述 | 使用频率 | 状态 |
|------|----------|---------|------|
| `pm guide` | 最佳实践指导和教程 | 低 | ✅ 完全可用 |
| `pm context` | 当前情境检测信息 | 低 | ✅ 完全可用 |
| `pm update` | 状态更新工具 | 低 | ✅ 完全可用 |

---

## 🔧 脚本库存

### 用户功能脚本

#### 习惯管理自动化
| 脚本名称 | 功能描述 | 使用场景 | 状态 |
|---------|----------|---------|------|
| `sync_habits_to_tasks.py` | 将习惯同步到Google Tasks | 每日01:00自动执行 | ✅ 生产使用 |
| `sync_habits_to_obsidian.py` | 将习惯数据同步到Obsidian | 每2小时自动执行 | ✅ 生产使用 |
| `clean_old_habit_tasks.py` | 清理Google Tasks中的旧习惯 | 按需手动执行 | ✅ 可用 |
| `habits_manager.py` | 习惯管理辅助工具 | 开发/调试用 | ✅ 可用 |

#### 项目管理
| 脚本名称 | 功能描述 | 使用场景 | 状态 |
|---------|----------|---------|------|
| `sync_projects_to_obsidian.py` | 同步项目状态到Obsidian | 每小时自动执行 | ✅ 生产使用 |
| `daily_focus.py` | 每日专注计划生成 | 按需执行 | ✅ 可用 |

#### 认证管理
| 脚本名称 | 功能描述 | 使用场景 | 状态 |
|---------|----------|---------|------|
| `multi_account_auth.py` | 多账户认证管理 | 特殊需求 | ✅ 可用 |

### 开发和运维脚本

#### 系统诊断
| 脚本名称 | 功能描述 | 使用场景 | 状态 |
|---------|----------|---------|------|
| `doctor.sh` | 系统环境诊断 | 问题排查 | ✅ 可用 |
| `verify_installation.sh` | 安装验证 | 部署后验证 | ✅ 可用 |
| `verify_deployment.sh` | 部署验证 | 生产部署验证 | ✅ 可用 |

#### 部署和打包
| 脚本名称 | 功能描述 | 使用场景 | 状态 |
|---------|----------|---------|------|
| `package_offline.sh` | 离线包生成 | 离线部署 | ✅ 可用 |
| `rollback_install.sh` | 安装回滚 | 安装失败恢复 | ✅ 可用 |

#### 监控和测试
| 脚本名称 | 功能描述 | 使用场景 | 状态 |
|---------|----------|---------|------|
| `health_probe.sh` | 健康检查探针 | 系统监控 | ✅ 可用 |
| `start_obs_server.sh` | 启动监控服务 | 可观测性 | ✅ 可用 |
| `deploy_health_probes.sh` | 部署健康检查 | 生产监控 | ✅ 可用 |
| `alert_replay_test.sh` | 告警重放测试 | 告警系统测试 | ✅ 可用 |
| `run_slo_analysis.py` | SLO分析工具 | 性能分析 | ✅ 可用 |
| `validate_alert_thresholds.py` | 验证告警阈值 | 告警配置验证 | ✅ 可用 |

#### 数据生成和测试
| 脚本名称 | 功能描述 | 使用场景 | 状态 |
|---------|----------|---------|------|
| `generate_simulated_data.py` | 生成模拟数据 | 开发测试 | ✅ 可用 |
| `test_dual_write.py` | 双写测试 | 数据一致性测试 | ✅ 可用 |
| `demo_events.sh` | 生成演示事件 | 功能演示 | ✅ 可用 |

#### 开发工具
| 脚本名称 | 功能描述 | 使用场景 | 状态 |
|---------|----------|---------|------|
| `generate_diff.sh` | 生成差异报告 | 代码比较 | ✅ 可用 |
| `verify_package.sh` | 包验证 | 发布前验证 | ✅ 可用 |

---

## 🔄 自动化任务清单

### Crontab任务
| 时间 | 任务 | 脚本 | 状态 |
|------|------|------|------|
| 每天01:00 | 同步习惯到Google Tasks | `sync_habits_to_tasks.py` | ✅ 运行中 |
| 每2小时 | 同步习惯数据到Obsidian | `sync_habits_to_obsidian.py` | ✅ 运行中 |
| 每小时 | 同步项目状态到Obsidian | `sync_projects_to_obsidian.py` | ✅ 运行中 |

### 事件驱动任务
| 触发条件 | 动作 | 实现方式 | 状态 |
|---------|------|---------|------|
| 用户认证过期 | 自动提醒重新认证 | 内置逻辑 | ✅ 可用 |
| 数据同步失败 | 日志记录和重试 | 脚本内置 | ✅ 可用 |
| 系统错误 | 错误上报和日志 | 全局异常处理 | ✅ 可用 |

---

## 🗂️ 数据存储结构

### 核心数据文件
```
~/.personalmanager/
├── credentials.json                 # Google服务凭证
├── data/
│   ├── habits/
│   │   └── habits.json             # 习惯数据 (当前3个习惯)
│   ├── gtd/                        # GTD任务数据
│   │   ├── inbox.json              # 收件箱
│   │   ├── next_actions.json       # 下一步行动
│   │   └── projects.json           # 项目数据
│   ├── deepwork/                   # 深度工作数据
│   │   └── sessions.json           # 工作时段记录
│   └── tokens/                     # API认证令牌
│       ├── google_token.json       # Google服务令牌
│       └── refresh_token.json      # 刷新令牌
└── logs/                           # 系统日志
    ├── pm.log                      # 主程序日志
    ├── cron.log                    # Crontab执行日志
    ├── sync.log                    # 同步操作日志
    └── error.log                   # 错误日志
```

### 配置文件
| 文件位置 | 用途 | 内容描述 |
|---------|------|---------|
| `~/.personalmanager/config.json` | 主配置 | 系统设置和用户偏好 |
| `~/.personalmanager/credentials.json` | 认证 | Google服务API凭证 |
| `pyproject.toml` | 项目配置 | Poetry依赖和项目元数据 |

---

## 🔌 外部集成状态

### Google服务集成
| 服务 | API范围 | 功能 | 状态 |
|------|---------|------|------|
| Google Calendar | `calendar.readonly` | 日程同步 | ✅ 已认证 |
| Google Tasks | `tasks` | 任务同步 | ✅ 已认证 |
| Gmail | `gmail.readonly` | 邮件扫描 | ✅ 已认证 |
| Google Drive | 无 | 未集成 | ❌ 未使用 |

### Obsidian集成
| 功能 | 目标路径 | 同步频率 | 状态 |
|------|----------|---------|------|
| 习惯追踪 | `PersonalManager/习惯追踪/` | 每2小时 | ✅ 正常 |
| 项目状态 | `PersonalManager/项目/` | 每小时 | ✅ 正常 |
| 目标管理 | `PersonalManager/目标/` | 手动 | ✅ 可用 |

### AI服务集成
| 服务 | 配置状态 | 功能范围 | 状态 |
|------|----------|---------|------|
| Claude (Anthropic) | 已配置 | 任务推荐、决策解释 | ✅ 可用 |
| Gemini (Google) | 已配置 | 备选AI服务 | ✅ 可用 |

---

## 📊 功能使用统计

### 高频使用功能 (日常)
- `pm today` - 每日重点获取
- `pm habits status` - 习惯状态检查
- `pm capture` - 任务快速捕获
- `pm next` - 下一步行动查看

### 中频使用功能 (每周)
- `pm inbox` - 收件箱整理
- `pm clarify` - 任务理清
- `pm calendar sync` - 日程同步
- `pm habits track` - 习惯记录

### 低频使用功能 (按需)
- `pm setup` - 系统配置
- `pm habits create` - 创建新习惯
- `pm doctor` - 系统诊断
- `pm privacy` - 数据管理

---

## 🔍 功能发现指南

### 当用户说"我想要..."时，检查顺序：

1. **首先检查CLI命令**
   ```bash
   ./bin/pm-local --help
   ./bin/pm-local [模块] --help
   ```

2. **然后检查现有脚本**
   ```bash
   ls -la scripts/ | grep -E "(sync|clean|manage|daily)"
   ```

3. **检查自动化任务**
   ```bash
   crontab -l
   ```

4. **检查数据结构**
   ```bash
   ls -la ~/.personalmanager/data/
   cat ~/.personalmanager/data/habits/habits.json
   ```

5. **检查外部集成**
   - Google服务功能范围
   - Obsidian现有同步内容
   - AI服务可用功能

### 常见需求 → 现有功能映射

| 用户需求 | 现有解决方案 |
|---------|-------------|
| "查看今天要做什么" | `pm today` |
| "记录习惯完成" | `pm habits track` 或 Google Tasks |
| "添加新任务" | `pm capture` |
| "看看项目进度" | `pm projects` |
| "设置新习惯" | `pm habits create` |
| "查看日程" | `pm calendar sync` |
| "清理数据" | `pm privacy cleanup` |
| "系统出问题了" | `pm doctor` |

---

**维护说明**: 此文档应该在每次添加新功能或脚本后立即更新。
**最后验证**: 2025-09-15 01:25
**下次盘点**: 2025-10-15