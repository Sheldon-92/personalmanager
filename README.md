# PersonalManager - 极简个人任务管理

一个极简的命令行工具，整合 Google Calendar 和 Google Tasks，让你在终端里管理日程和任务。

## 功能

- **today** - 查看今日日程和任务
- **inbox** - 查看待处理任务（收件箱）
- **sync** - 连接并验证 Google 账户
- **add** - 快速添加任务到 Google Tasks
- **cal** - 查看未来日历

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/Sheldon-92/personalmanager.git
cd personal-manager
```

### 2. 安装依赖

```bash
# 使用 Poetry
poetry install

# 或使用 pip
pip install -r requirements.txt
```

### 3. 首次使用 - 连接 Google

```bash
./bin/pm-local sync
```

这会打开浏览器让你登录 Google 账户并授权访问 Calendar 和 Tasks。

### 4. 开始使用

```bash
# 查看今日概览
./bin/pm-local today

# 查看待处理任务
./bin/pm-local inbox

# 添加新任务
./bin/pm-local add "完成报告" --due 2024-01-20

# 查看未来7天日历
./bin/pm-local cal

# 查看未来14天日历
./bin/pm-local cal --days 14
```

## 命令详解

### `pm today`
显示今日的任务和日程安排。

```
┌───────────────────────────────────────┐
│ 今日概览 - 2024-01-15 Monday         │
└───────────────────────────────────────┘

今日任务
┌───┬──────────────────┬────────┐
│ # │ 任务             │ 状态   │
├───┼──────────────────┼────────┤
│ 1 │ 完成周报         │ ⬜     │
│ 2 │ 回复客户邮件     │ ⬜     │
└───┴──────────────────┴────────┘

今日日程
┌────────┬──────────────────────┐
│ 时间   │ 事件                 │
├────────┼──────────────────────┤
│ 09:00  │ 团队晨会             │
│ 14:00  │ 项目评审会议         │
└────────┴──────────────────────┘
```

### `pm inbox`
显示所有待处理任务。

### `pm sync`
验证 Google 连接状态。如果未登录，会自动启动认证流程。

### `pm add <标题> [--due DATE]`
添加新任务到 Google Tasks。

```bash
# 不设截止日期
./bin/pm-local add "买牛奶"

# 设置截止日期
./bin/pm-local add "提交报告" --due 2024-01-20
```

### `pm cal [--days N]`
查看未来 N 天的日历（默认 7 天）。

## 技术栈

- **Python 3.9+**
- **Typer** - CLI 框架
- **Rich** - 终端美化输出
- **Google API** - Calendar 和 Tasks 集成

## 项目结构

```
src/pm/
├── cli/main.py              # CLI 入口
├── core/config.py           # 配置管理
├── integrations/
│   ├── google_auth.py       # Google OAuth
│   ├── google_calendar.py   # Calendar API
│   └── google_tasks.py      # Tasks API
├── models/task.py           # 数据模型
└── security/secrets.py      # 密钥管理
```

## 许可证

MIT License
