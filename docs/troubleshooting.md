# PersonalManager 故障排查指南

> **版本**: v1.0.0
> **最后更新**: 2025-09-13

本文档提供 PersonalManager 常见问题的诊断和解决方案，包括错误码清单、故障排查流程和修复建议。

## 🚨 错误码清单

### E1000 系列 - 系统初始化错误

#### E1001: 系统未初始化
**错误消息**: `PersonalManager 系统未初始化，请运行 'pm setup' 进行配置`

**原因**:
- 首次使用未运行初始化
- 配置文件丢失或损坏
- 数据目录权限问题

**解决方案**:
```bash
# 方案1: 标准初始化
pm setup

# 方案2: 引导式初始化（推荐新用户）
pm setup --guided

# 方案3: 重置初始化
pm setup --reset
```

**验证修复**:
```bash
pm --version
pm status  # 应显示系统状态而非初始化提示
```

#### E1002: 数据目录权限不足
**错误消息**: `无法访问数据目录 ~/.personalmanager，权限不足`

**原因**:
- 数据目录不可写
- 文件系统权限配置错误
- 磁盘空间不足

**解决方案**:
```bash
# 检查目录权限
ls -la ~/.personalmanager

# 修复权限（Linux/macOS）
chmod 755 ~/.personalmanager
chmod -R 644 ~/.personalmanager/*

# 检查磁盘空间
df -h ~/.personalmanager

# 运行诊断
pm doctor
```

#### E1003: 配置文件损坏
**错误消息**: `配置文件格式错误或损坏，无法解析`

**原因**:
- YAML 格式语法错误
- 文件编码问题
- 意外的文件截断

**解决方案**:
```bash
# 检查配置文件
cat ~/.personalmanager/config.yaml

# 从备份恢复（如果有）
pm config restore --from-backup

# 重新生成配置文件
pm setup --reset

# 验证配置文件格式
pm config validate
```

### E2000 系列 - 命令执行错误

#### E2001: 命令参数无效
**错误消息**: `无效的命令参数或选项`

**原因**:
- 参数格式错误
- 必需参数缺失
- 参数值超出范围

**解决方案**:
```bash
# 查看命令帮助
pm <command> --help

# 查看所有可用命令
pm --help

# 示例：正确的命令格式
pm capture "任务描述"  # 正确
pm capture 任务描述     # 错误：缺少引号
```

#### E2002: 资源不存在
**错误消息**: `指定的项目/任务/习惯不存在`

**原因**:
- ID 或名称错误
- 资源已被删除
- 数据同步问题

**解决方案**:
```bash
# 列出所有可用资源
pm projects list
pm tasks list
pm habits list

# 使用正确的 ID 或名称
pm project status "正确的项目名"

# 刷新数据
pm sync --all
```

### E3000 系列 - 外部集成错误

#### E3001: Google 服务未配置
**错误消息**: `Google 服务未配置，请先完成认证或使用离线模式`

**原因**:
- 未设置 Google API 凭证
- 认证 Token 过期
- 网络连接问题

**解决方案**:
```bash
# 检查认证状态
pm auth status

# 重新认证
pm auth login google

# 或使用离线替代功能
pm tasks list      # 本地任务
pm projects overview  # 本地项目
```

#### E3002: AI 服务不可用
**错误消息**: `AI 服务未配置或不可用，无法生成智能推荐`

**原因**:
- API 密钥未设置
- API 服务限额超出
- 网络连接问题

**解决方案**:
```bash
# 检查 AI 服务状态
pm report status

# 设置 API 密钥
export PM_CLAUDE_API_KEY=your_key
export PM_GEMINI_API_KEY=your_key
export PM_AI_TOOLS_ENABLED=true

# 或使用基础推荐功能
pm recommend --offline
pm today  # 基于本地数据的推荐
```

### E4000 系列 - 数据操作错误

#### E4001: 数据完整性验证失败
**错误消息**: `数据文件损坏或格式不正确`

**原因**:
- JSON 文件格式错误
- 数据结构版本不兼容
- 文件系统错误

**解决方案**:
```bash
# 运行数据完整性检查
pm privacy verify

# 尝试修复数据
pm privacy cleanup

# 从备份恢复
pm privacy restore --from-backup

# 最后手段：重新开始
pm privacy clear  # ⚠️ 危险操作
```

#### E4002: 存储空间不足
**错误消息**: `磁盘空间不足，无法保存数据`

**原因**:
- 磁盘空间不足
- 临时文件过多
- 日志文件过大

**解决方案**:
```bash
# 检查磁盘空间
df -h ~/.personalmanager

# 清理临时文件和日志
pm privacy cleanup

# 清理旧备份
pm privacy cleanup --old-backups

# 运行系统诊断
pm doctor
```

## 🔧 常见问题排查流程

### 1. 系统环境问题

**症状**: 命令无法找到、权限错误、Python 版本问题

**诊断步骤**:
```bash
# 1. 基础环境检查
python --version  # 需要 >= 3.9
which pm
echo $PATH

# 2. 运行系统诊断
pm doctor --verbose

# 3. 检查安装状态
pip list | grep personal-manager
# 或
pipx list | grep personal-manager
```

### 2. 配置初始化问题

**症状**: "系统未初始化"、配置文件错误

**诊断步骤**:
```bash
# 1. 检查配置文件
ls -la ~/.personalmanager/
cat ~/.personalmanager/config.yaml

# 2. 验证配置格式
pm config validate

# 3. 重新初始化
pm setup --reset
```

### 3. 数据访问问题

**症状**: 任务丢失、项目状态不正确、数据不同步

**诊断步骤**:
```bash
# 1. 数据完整性检查
pm privacy verify

# 2. 检查数据目录
ls -la ~/.personalmanager/data/
du -sh ~/.personalmanager/data/

# 3. 同步数据
pm sync --all
```

### 4. 外部集成问题

**症状**: Google 服务连接失败、AI 功能不可用

**诊断步骤**:
```bash
# 1. 检查认证状态
pm auth status

# 2. 检查网络连接
ping google.com
curl -I https://api.anthropic.com

# 3. 检查 API 配置
echo $PM_CLAUDE_API_KEY
echo $PM_AI_TOOLS_ENABLED

# 4. 重新认证
pm auth login google
```

## 📋 自助诊断检查清单

在寻求帮助前，请完成以下检查清单：

### 基础检查
- [ ] Python 版本 >= 3.9 (`python --version`)
- [ ] PersonalManager 已正确安装 (`pm --version`)
- [ ] 系统已初始化 (`pm status`)
- [ ] 数据目录可访问 (`ls ~/.personalmanager`)

### 环境检查
- [ ] 运行系统诊断 (`pm doctor`)
- [ ] 检查磁盘空间 (`df -h`)
- [ ] 验证网络连接 (`ping google.com`)
- [ ] 检查权限设置 (`pm privacy verify`)

### 配置检查
- [ ] 配置文件格式正确 (`pm config validate`)
- [ ] 必要的环境变量已设置
- [ ] API 密钥配置正确 (`pm report status`)
- [ ] 项目路径配置正确 (`pm projects overview`)

### 数据检查
- [ ] 数据完整性验证通过 (`pm privacy verify`)
- [ ] 备份文件存在且可用
- [ ] 关键数据文件可读写
- [ ] 没有存储空间问题

## 🆘 获取帮助

如果以上步骤无法解决问题：

### 收集诊断信息
```bash
# 生成完整的系统报告
pm doctor --verbose > system_report.txt

# 检查错误日志
tail -50 ~/.personalmanager/logs/error.log

# 导出配置信息（隐藏敏感数据）
pm config export --safe
```

### 联系支持
- 提供具体的错误消息和错误码
- 包含系统诊断报告
- 说明重现问题的具体步骤
- 提及您的操作系统和 Python 版本

---

**提示**: 大部分问题可以通过运行 `pm doctor` 自动诊断和修复。遇到问题时，这应该是您的第一步。

---

## 工作空间/路由

**症状**: Agent 进入目录后未体现"专家身份"；自然语言无法路由到 `pm`；项目指令无效

### 使用 `pm agent status --json` 快速定位问题

当遇到工作空间相关问题时，推荐使用 JSON 模式进行快速诊断：

```bash
# 获取结构化的诊断报告
pm agent status --json | jq .

# 仅查看错误项
pm agent status --json | jq '.items[] | select(.level == "ERROR")'

# 查看统计摘要
pm agent status --json | jq .summary

# 检查特定类型的问题
pm agent status --json | jq '.items[] | select(.check | contains("yaml_syntax"))'
```

**JSON 输出解读**：
- `level: "ERROR"` - 必须修复的问题
- `level: "WARN"` - 建议处理的问题
- `level: "OK"` - 检查通过
- `suggest` 字段 - 提供具体的修复建议

### 常见问题诊断

**诊断步骤**:
```bash
# 1) 三件套是否存在
ls -la .personalmanager/

# 2) 使用 agent status 进行全面检查（实验性功能）
pm agent status

# 3) 如需程序化处理，使用 JSON 模式
pm agent status --json > workspace_check.json

# 4) 编译产物是否生成（规划中的功能）
ls -la .claude/project-instructions.md
cat ~/.gemini/config.json | python -m json.tool | grep -i personalmanager
```

**修复建议**:
- 运行 `pm workspace init` 生成三件套
- 运行 `pm agent prompt --write` 重新生成指令（规划中）
- 检查 `interaction-patterns.json` 中是否包含你的常用短语/语言
