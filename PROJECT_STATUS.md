# 项目：PersonalManager - 极简任务管理

## 状态
- **进度**: 100%
- **健康度**: 良好 (Good)
- **优先级**: 中 (Medium)
- **最后更新**: 2025-12-22
- **版本**: v2.0.0 (极简版)

## 项目描述
一个极简的命令行工具，整合 Google Calendar 和 Google Tasks，让你在终端里管理日程和任务。

## 核心功能
- **today** - 查看今日日程和任务
- **inbox** - 查看待处理任务
- **sync** - 连接并验证 Google 账户
- **add** - 快速添加任务
- **cal** - 查看未来日历
- **version** - 显示版本信息

## 技术栈
- Python 3.9+
- Typer CLI 框架
- Rich 终端美化
- Google Calendar/Tasks API

## 项目结构
```
src/pm/
├── cli/main.py           # CLI 入口 (6个命令)
├── core/config.py        # 配置管理
├── integrations/         # Google API 集成
├── models/task.py        # 数据模型
└── security/secrets.py   # 密钥管理
```

## 已完成
- [x] Google OAuth 认证
- [x] Google Calendar 集成
- [x] Google Tasks 集成
- [x] CLI 界面
- [x] 代码清理和精简

## 维护状态
功能完整，进入维护模式。
