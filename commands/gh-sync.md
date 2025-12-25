---
name: gh-sync
description: 同步当前项目到 GitHub 私有仓库 - 自动创建仓库或推送更新
---

# /gh-sync - GitHub 私有仓库同步

将当前项目同步到 GitHub 私有仓库。首次使用会自动创建仓库，之后执行拉取和推送。

## 执行流程

### 阶段 1: 环境检查

1. **检查当前目录**
   - 运行 `pwd` 确认工作目录
   - 如果在用户 home 目录或系统目录，**停止执行**并提示用户进入正确的项目目录

2. **检查 gh CLI 认证状态**
   - 运行 `gh auth status`
   - 如果未认证，提示用户运行 `gh auth login` 后再试

### 阶段 2: Git 仓库初始化

1. **检测是否是 git 仓库**
   - 运行 `git rev-parse --is-inside-work-tree 2>/dev/null`

2. **如果不是 git 仓库**
   - 询问用户："当前目录不是 git 仓库，是否要初始化？(Y/n)"
   - 如果用户同意：
     - 检查是否存在 `.gitignore`，如果没有，创建标准 `.gitignore`（见下方模板）
     - 运行 `git init`
     - 运行 `git add -A`
     - 运行 `git commit -m "Initial commit"`
   - 如果用户拒绝：停止执行

### 阶段 3: 检测远程仓库

1. **检查远程仓库配置**
   - 运行 `git remote -v`

2. **如果没有远程仓库 → 首次同步流程**
   - 从目录名推断仓库名称
   - 询问用户："将创建私有仓库 'sheldon-92/[仓库名]'，确认？(Y/n)"
   - 如果用户同意：
     - 运行 `gh repo create --private --source=. --push`
     - 显示成功信息，包含仓库 URL
   - 如果用户拒绝：停止执行

3. **如果已有远程仓库 → 日常同步流程**
   - 继续阶段 4

### 阶段 4: 日常同步

1. **检查本地状态**
   - 运行 `git status --porcelain`
   - 记录是否有未提交的改动

2. **暂存本地改动**（如果有改动）
   - 运行 `git stash push -m "gh-sync auto stash"`
   - 记录 stash 是否成功

3. **拉取远程更新**
   - 运行 `git pull --rebase origin $(git branch --show-current)`
   - 如果失败（冲突），进入**冲突处理流程 A**

4. **恢复暂存的改动**（如果之前有 stash）
   - 运行 `git stash pop`
   - 如果失败（冲突），进入**冲突处理流程 B**

5. **提交本地改动**（如果有改动）
   - 运行 `git add -A`
   - 运行 `git diff --cached --quiet` 检查是否有实际改动
   - 如果有改动，询问用户 commit message，或使用默认: `Sync: [当前日期时间]`
   - 运行 `git commit -m "[message]"`

6. **推送到远程**
   - 运行 `git push origin $(git branch --show-current)`
   - 显示成功信息

### 阶段 5: 完成报告

显示同步结果摘要：

```
--- GitHub 同步完成 ---

仓库: [owner/repo-name]
分支: [branch-name]
状态: 成功同步

操作详情:
- [拉取了 X 个提交 / 无新提交]
- [推送了 X 个提交 / 无需推送]
- [文件变更: +X -Y ~Z]
```

## 冲突处理

### 冲突处理流程 A: Pull Rebase 冲突

```
--- 发现冲突 ---

远程仓库有与本地冲突的更改。请手动解决：

1. 查看冲突文件: git status
2. 编辑冲突文件，解决冲突标记 (<<<< ==== >>>>)
3. 标记解决: git add [文件]
4. 继续 rebase: git rebase --continue
5. 完成后重新运行 /gh-sync

或者放弃本次同步: git rebase --abort
```

**停止执行，等待用户手动处理**

### 冲突处理流程 B: Stash Pop 冲突

```
--- Stash 恢复冲突 ---

暂存的本地改动与拉取的更新冲突。请手动解决：

1. 查看冲突文件: git status
2. 编辑冲突文件，解决冲突
3. 完成后运行: git stash drop (清理 stash)
4. 然后正常提交你的改动

注意: 你的改动仍在 stash 中，不会丢失
查看 stash: git stash show -p
```

**停止执行，等待用户手动处理**

## .gitignore 模板

如果项目没有 .gitignore，创建以下内容：

```gitignore
# OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# IDE and editors
.idea/
.vscode/
*.swp
*.swo
*~
.project
.settings/

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
.venv/
venv/
ENV/
.pytest_cache/
.mypy_cache/

# Node.js
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.npm

# Environment and secrets
.env
.env.local
.env.*.local
*.pem
*.key
credentials.json
token.json
secrets/

# Logs and databases
*.log
*.sqlite
*.db

# Build outputs
/out/
/target/
*.exe
*.dll
*.dylib

# TAD Framework - 全部纳入版本控制，不忽略
# (保留所有过程文件：handoffs, evidence, logs, context)
```

### 阶段 2.5: TAD .gitignore 检查（新增）

如果项目已有 `.gitignore`，检查是否正确配置 TAD：

1. **检查 .gitignore 中的 TAD 规则**
   - 如果发现任何忽略 `.tad/` 的规则（如 `.tad/`, `.tad/*`, `.tad/logs/` 等），提示用户
   - 建议：移除所有 `.tad/` 相关的忽略规则，让全部内容被版本控制

2. **自动修复选项**
   - 询问用户："检测到 .gitignore 忽略了 TAD 文件，是否移除这些规则？(Y/n)"
   - 如果同意，移除所有 `.tad` 相关的忽略规则

## 安全注意事项

- **敏感文件检查**：执行前检查是否有 `.env`、`credentials.json`、`*.key`、`*.pem` 等文件未被 .gitignore 忽略
- 如果发现潜在敏感文件，**警告用户**并询问是否继续
- 只创建 **私有仓库**，保护代码隐私

## 用户交互示例

### 首次同步

```
检测到当前目录不是 git 仓库。

当前目录: /Users/you/projects/my-app

是否初始化 git 仓库并同步到 GitHub? (Y/n)

> Y

正在初始化...
- 创建 .gitignore
- git init
- git add -A
- git commit -m "Initial commit"

将创建 GitHub 私有仓库: sheldon-92/my-app

确认创建? (Y/n)

> Y

正在创建仓库并推送...

--- GitHub 同步完成 ---

仓库: https://github.com/sheldon-92/my-app
分支: main
状态: 首次同步成功

你的代码已安全存储在 GitHub 私有仓库中。
```

### 日常同步

```
正在同步: sheldon-92/my-app (main)

- 暂存本地改动... 完成 (3 个文件)
- 拉取远程更新... 完成 (2 个新提交)
- 恢复本地改动... 完成
- 检测到改动，准备提交

请输入 commit message (直接回车使用默认):
> 修复登录页面样式

- 提交本地改动... 完成
- 推送到远程... 完成

--- GitHub 同步完成 ---

仓库: sheldon-92/my-app
分支: main
状态: 成功同步

操作详情:
- 拉取了 2 个提交
- 推送了 1 个提交
- 文件变更: +15 -8 ~3
```

## 错误处理

| 错误情况 | 处理方式 |
|---------|---------|
| 不在项目目录 | 提示用户 `cd` 到正确目录 |
| gh 未认证 | 提示运行 `gh auth login` |
| 网络错误 | 提示检查网络连接，稍后重试 |
| 远程仓库已存在同名 | 提示用户选择：使用现有仓库 / 更换名称 |
| push 被拒绝 | 提示先 pull，或检查分支保护规则 |
| 权限不足 | 提示检查 gh CLI 权限范围 |

## 快捷选项

用户可以使用参数跳过确认：

- `/gh-sync -y` 或 `/gh-sync --yes`: 自动确认所有提示
- `/gh-sync -m "message"`: 指定 commit message

## 注意事项

- 只处理当前分支，不会影响其他分支
- 如果仓库已存在但本地没有 remote，会提示用户选择是否关联
- 保持 git 历史整洁，使用 rebase 而非 merge
- 遇到无法自动解决的问题，总是停下来让用户决定
