# Claude Code PersonalManager v0.5.0 集成配置

## 问题诊断

您的截图显示新功能没有出现在Claude Code命令列表中，原因是：
- 之前创建的配置文件位于项目目录 (`/Users/sheldonzhao/programs/personal-manager/config/`)
- 但Claude Code实际读取的配置位置是 `~/.claude/`

## 已完成的修复

### 1. 创建了Claude命令文件
在 `~/.claude/commands/pm/` 目录下创建了以下命令文件：

| 文件名 | 命令 | 功能 |
|--------|------|------|
| `next.md` | `/pm next` | AI推荐下一个任务 |
| `analyze.md` | `/pm analyze` | 分析生产力模式 |
| `break.md` | `/pm break` | 检查是否需要休息 |
| `focus.md` | `/pm focus` | 开始AI引导专注会话 |
| `session-start.md` | `/pm session-start` | 开始工作会话 |
| `session-end.md` | `/pm session-end` | 结束会话并评分 |
| `plan-today.md` | `/pm plan-today` | 查看今日时间块 |
| `plan-tomorrow.md` | `/pm plan-tomorrow` | 规划明日时间块 |
| `budget.md` | `/pm budget` | 查看时间预算 |

### 2. 更新了索引文件
更新 `~/.claude/commands/pm/index.md`，添加了v0.5.0新功能分类：
- 🤖 AI智能功能
- 🎯 会话管理
- 📅 时间规划

### 3. 更新了设置文件
更新 `~/.claude/settings.json`，在tools部分添加了所有新工具的注册。

## 如何验证

1. **重启Claude Code** (重要！)
   - 关闭Claude Code应用
   - 重新打开

2. **测试命令**
   输入 `/` 应该能看到以下新命令：
   - `/pm next`
   - `/pm analyze`
   - `/pm break`
   - `/pm focus`
   - `/pm session-start`
   - `/pm session-end`
   - `/pm plan-today`
   - `/pm plan-tomorrow`
   - `/pm budget`

3. **验证命令执行**
   ```bash
   # 测试AI推荐
   /pm next

   # 测试分析
   /pm analyze

   # 测试休息建议
   /pm break
   ```

## 文件位置汇总

### Claude Code配置文件
```
~/.claude/
├── commands/
│   └── pm/
│       ├── index.md          # 命令索引（已更新）
│       ├── next.md            # AI推荐（新增）
│       ├── analyze.md         # 分析（新增）
│       ├── break.md           # 休息（新增）
│       ├── focus.md           # 专注（新增）
│       ├── session-start.md   # 开始会话（新增）
│       ├── session-end.md     # 结束会话（新增）
│       ├── plan-today.md      # 今日计划（新增）
│       ├── plan-tomorrow.md   # 明日计划（新增）
│       └── budget.md          # 预算（新增）
└── settings.json              # 设置文件（已更新）
```

### PersonalManager项目配置（供参考）
```
/Users/sheldonzhao/programs/personal-manager/
├── config/
│   ├── tools/
│   │   └── personalmanager_tools.json
│   ├── slash/
│   │   └── slash_mappings.yaml
│   └── prompts/
│       └── personalmanager_system.md
└── docs/api/
    └── FUNCTIONS_REGISTRY_v050.json
```

## 故障排除

如果命令仍然不显示：

1. **检查权限**
   ```bash
   ls -la ~/.claude/commands/pm/
   # 确保文件可读
   ```

2. **检查Claude Code版本**
   - 确保使用最新版本的Claude Code

3. **手动刷新**
   - 在Claude Code中输入 `/reload` 或 `/refresh`

4. **检查日志**
   ```bash
   tail -f ~/Library/Logs/Claude/claude.log
   ```

## 使用示例

### 早晨工作流
```
/pm briefing        # 查看今日简报
/pm next           # 获取AI任务推荐
/pm focus          # 开始专注会话
```

### 工作会话管理
```
/pm session-start "PersonalManager开发" deep
# ... 工作中 ...
/pm session-end energy=4 prod=5
```

### 时间规划
```
/pm plan-today     # 查看今天安排
/pm budget         # 检查时间预算
/pm plan-tomorrow  # 规划明天
```

---

配置完成！请重启Claude Code后测试新命令。