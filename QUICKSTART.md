# PersonalManager 快速开始指南

## 🚀 3分钟上手

### 第一步：获取代码
```bash
git clone https://github.com/Sheldon-92/personalmanager.git
cd personal-manager
```

### 第二步：快速体验
```bash
# 查看版本
./bin/pm-local --version

# 生成今日简报
./bin/pm-briefing

# 启动交互模式
./bin/pm-interactive
```

## 💡 核心功能速览

### 1. 交互模式（最推荐）
```bash
./bin/pm-interactive
```
- 输入 `/` 查看所有斜杠命令
- 输入 `/pm` 生成简报
- 输入数字选择操作（如 1,2,3）

### 2. 双向简报
```bash
./bin/pm-briefing
```
获取包含任务、日程、习惯的高密度信息简报

### 3. 任务管理
```bash
# 快速捕获
./bin/pm-local capture "完成项目报告"

# 查看收件箱
./bin/pm-inbox

# 今日推荐
./bin/pm-local today
```

### 4. Obsidian同步
```bash
# 同步习惯到Obsidian
./bin/pm-local obsidian sync
```

## 🎯 常见使用场景

### 早晨开始工作
```bash
./bin/pm-briefing          # 查看今日简报
./bin/pm-local today        # 获取任务推荐
```

### 快速记录想法
```bash
./bin/pm-local capture "新的想法或任务"
```

### 整理任务
```bash
./bin/pm-local inbox        # 查看待处理
./bin/pm-local clarify      # GTD理清流程
```

### 与AI协作
在Claude Code或其他AI工具中：
- "帮我生成今日简报" → AI执行 `./bin/pm-briefing`
- "添加任务：准备会议" → AI执行 `./bin/pm-local capture "准备会议"`

## ⚙️ 配置（可选）

### 首次设置
```bash
./bin/pm-local setup
```

### Google服务集成
```bash
./bin/pm-local auth login
```

## 📖 了解更多

- 完整命令列表：运行 `./bin/pm-local --help`
- 详细文档：查看 `docs/` 目录
- 安装指南：[INSTALL_GUIDE.md](INSTALL_GUIDE.md)
- 项目主页：[README.md](README.md)

## 💬 获取帮助

遇到问题？
1. 运行诊断：`./bin/pm-local doctor`
2. 查看日志：`~/.personalmanager/logs/`
3. 提交Issue：https://github.com/Sheldon-92/personalmanager/issues

---

**版本**: v0.4.0-rc1 | **更新日期**: 2025-09-15