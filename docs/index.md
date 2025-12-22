# PersonalManager 文档

极简任务管理工具 - 整合 Google Calendar 和 Google Tasks

## 核心文档

- [README.md](../README.md) - 项目说明和快速开始
- [PROJECT_STATUS.md](../PROJECT_STATUS.md) - 项目状态

## 命令参考

| 命令 | 说明 |
|------|------|
| `pm today` | 查看今日日程和任务 |
| `pm inbox` | 查看待处理任务 |
| `pm sync` | 连接 Google 账户 |
| `pm add <标题>` | 添加新任务 |
| `pm cal` | 查看未来日历 |
| `pm version` | 显示版本 |

## 技术架构

```
src/pm/
├── cli/main.py           # CLI 入口
├── core/config.py        # 配置管理
├── integrations/
│   ├── google_auth.py    # OAuth 认证
│   ├── google_calendar.py
│   └── google_tasks.py
├── models/task.py        # 数据模型
└── security/secrets.py   # 密钥管理
```

---
*最后更新: 2025-12-22*
