# PersonalManager 安装指南

## 项目本地化使用（推荐）

PersonalManager 采用项目本地化架构，无需全局安装，避免系统污染。

### 快速开始

```bash
# 1. 克隆项目
git clone https://github.com/Sheldon-92/personalmanager.git
cd personal-manager

# 2. 安装依赖（可选，如果需要完整功能）
poetry install  # 如果有Poetry
# 或
pip install -r requirements.txt  # 使用pip

# 3. 验证安装
./bin/pm-local --version
# 输出: PersonalManager Agent v0.4.0-rc1

# 4. 首次配置
./bin/pm-local setup
```

### 使用方式

#### 方式1：使用封装脚本（推荐）
```bash
./bin/pm-local <command>         # 主命令
./bin/pm-briefing                # 快速简报
./bin/pm-interactive             # 交互模式
./bin/pm-inbox                   # 收件箱
./bin/pm-quick                   # 快速菜单
```

#### 方式2：直接Python执行
```bash
PYTHONPATH=src python3 -m pm.cli.main <command>
```

#### 方式3：交互模式
```bash
./start_interactive.sh
# 或
./bin/pm-interactive
```

## 环境要求

- Python 3.9+
- Poetry 2.0+ （可选）
- Git

## 依赖管理

### 使用Poetry（推荐）
```bash
poetry install              # 安装所有依赖
poetry install --no-dev     # 仅安装生产依赖
poetry shell                # 进入虚拟环境
```

### 使用pip
```bash
pip install -r requirements.txt
```

## 配置文件

用户配置存储在 `~/.personalmanager/`:
- `config.yaml` - 主配置文件
- `credentials.json` - Google API凭证
- `data/` - 任务和项目数据

## 故障排除

### 1. Python版本问题
```bash
# 检查Python版本
python3 --version  # 需要3.9+

# 使用特定版本
python3.9 -m pm.cli.main --version
```

### 2. 依赖缺失
```bash
# 重新安装依赖
poetry install --sync
# 或
pip install -r requirements.txt --force-reinstall
```

### 3. 权限问题
```bash
# 给脚本添加执行权限
chmod +x bin/*
chmod +x start_interactive.sh
```

### 4. 诊断工具
```bash
# 运行诊断
./bin/pm-local doctor

# 查看调试信息
./bin/pm-local --launcher-debug
```

## 卸载

由于是项目本地化，卸载非常简单：

```bash
# 1. 备份用户数据（可选）
cp -r ~/.personalmanager ~/.personalmanager.backup

# 2. 删除项目文件夹
rm -rf /path/to/personal-manager

# 3. 删除用户数据（可选）
rm -rf ~/.personalmanager
```

## 更新

```bash
# 拉取最新代码
git pull origin main

# 更新依赖
poetry install --sync
# 或
pip install -r requirements.txt --upgrade
```

## 支持

- GitHub Issues: https://github.com/Sheldon-92/personalmanager/issues
- 文档: docs/
- 版本: v0.4.0-rc1