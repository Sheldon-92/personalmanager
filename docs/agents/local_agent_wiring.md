# 项目级 Agent 接入与命令映射实施指南

> 版本: v1.0
> 创建日期: 2025-09-14
> 最后更新: 2025-09-14

## 背景与目标

### 背景
PersonalManager 作为一个"无头 + CLI + Agent 可调用"的个人效能工具包，设计目标是通过 AI Agent（如 Claude、Gemini CLI）将自然语言意图映射为具体的本地 CLI 命令。为了实现这一愿景，需要建立一套完整的项目级 Agent 接入机制。

### 核心目标
1. **无缝 Agent 集成**：使 AI Agent 能够直接调用 PersonalManager 功能
2. **统一启动器**：提供 `./bin/pm-local` 作为标准化的项目级入口点
3. **环境自适应**：自动检测并选择最佳的执行策略（Poetry 或直接 Python）
4. **开发者友好**：简化本地开发和远程协作的复杂性

## 架构设计

### 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    AI Agent Layer                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   Claude    │  │ Gemini CLI  │  │    Other Agents     │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────┬───────────────────────────────────────┘
                      │ Natural Language → CLI Commands
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                Project-Level Entry Point                   │
│                     ./bin/pm-local                         │
└─────────────────────┬───────────────────────────────────────┘
                      │ Auto-detection & Route
                      ▼
    ┌─────────────────────────────────────────────────────┐
    │              Execution Strategy                    │
    ├─────────────────────┬───────────────────────────────┤
    │                     │                               │
    ▼                     ▼                               ▼
┌─────────────┐    ┌─────────────┐              ┌─────────────┐
│   Poetry    │    │   Direct    │              │   Docker    │
│Environment  │    │   Python    │              │Container    │
│             │    │             │              │ (Future)    │
└─────────────┘    └─────────────┘              └─────────────┘
    │                     │                               │
    ▼                     ▼                               ▼
┌─────────────────────────────────────────────────────────────┐
│              PersonalManager Core                          │
│         (CLI Commands & Business Logic)                    │
└─────────────────────────────────────────────────────────────┘
```

### 核心组件

#### 1. 统一启动器 (`bin/pm-local`)
- **职责**：作为项目级的统一入口点
- **智能路由**：自动检测环境并选择最佳执行策略
- **错误处理**：提供友好的错误提示和诊断信息
- **调试支持**：内置 `--launcher-debug` 模式

#### 2. 环境检测模块
- **Poetry 检测**：验证 Poetry 可用性和 `pyproject.toml` 存在性
- **Python 模块检测**：确保 PersonalManager 模块可正确导入
- **依赖验证**：检查必要的 Python 依赖和环境配置

#### 3. 执行策略引擎
- **策略 1**：优先使用 Poetry 环境 (`poetry run pm`)
- **策略 2**：回退到直接 Python 执行 (`PYTHONPATH=src python3 -m pm.cli.main`)
- **策略 3**：（未来）支持容器化执行

## 实施细节

### bin/pm-local 启动器

#### 核心功能实现

**环境检测逻辑**：
```bash
# Poetry 环境检测
check_poetry() {
    if command_exists poetry && [ -f "pyproject.toml" ]; then
        return 0  # Poetry 可用
    else
        return 1  # 回退到 Python 直接执行
    fi
}

# Python 模块可用性检测
check_python_module() {
    PYTHONPATH="$PROJECT_ROOT/src" python3 -c "import pm.cli.main" >/dev/null 2>&1
}
```

**执行策略选择**：
```bash
# 主执行逻辑
main() {
    if check_poetry; then
        launch_with_poetry "$@"      # 策略 1：Poetry
    else
        launch_with_python "$@"      # 策略 2：直接 Python
    fi
}
```

**错误处理机制**：
- 颜色化输出：使用 ANSI 颜色代码提供清晰的状态反馈
- 分层诊断：从环境检测到模块导入的逐层错误排查
- 友好提示：针对常见问题提供具体的解决建议

#### 特殊功能

**调试模式** (`--launcher-debug`)：
```bash
./bin/pm-local --launcher-debug
```
输出示例：
```
PersonalManager Local Launcher - Environment Information
=======================================================
Project Root: /path/to/personal-manager
Python Version: Python 3.11.5
Poetry Available: Yes
pyproject.toml: Found
Source Directory: Found
```

### Claude 集成配置

#### Claude Code 环境集成

**使用场景**：
- 在 Claude Code 中打开 PersonalManager 项目
- 通过自然语言描述个人效能需求
- Claude 自动将需求转换为相应的 CLI 命令

**集成示例**：

用户输入：
> "帮我查看今天的重点任务，并开始一个深度工作会话"

Claude 的执行流程：
```bash
# 1. 查看今日推荐任务
./bin/pm-local today

# 2. 基于推荐结果开始深度工作
./bin/pm-local deepwork start
```

**优势**：
- 无需记忆具体命令语法
- 自然语言交互更符合人类思维
- 错误处理和异常情况由 Claude 智能处理

#### 配置要求

**环境变量**：
```bash
# 可选：启用 AI 工具集成
export PM_AI_TOOLS_ENABLED=true

# 可选：Claude API 密钥（用于 AI 报告生成）
export PM_CLAUDE_API_KEY=your_claude_api_key
```

**项目结构验证**：
Claude 在执行命令前会自动验证：
- `./bin/pm-local` 文件存在且可执行
- 项目根目录结构正确
- 必要的依赖已安装

### Gemini CLI 集成

#### 集成方式

**命令映射**：Gemini CLI 可以通过以下方式调用 PersonalManager：

```bash
# 通过 Gemini CLI 的工具调用能力
gemini chat --tools ./bin/pm-local

# 或者在 Gemini CLI 会话中直接执行
./bin/pm-local projects overview
./bin/pm-local capture "准备下周的项目汇报"
```

**自然语言示例**：

用户：
> "帮我管理一个新项目'网站重构'，并添加几个初始任务"

Gemini CLI 执行：
```bash
# 1. 创建项目
./bin/pm-local project create "网站重构"

# 2. 添加相关任务
./bin/pm-local capture "设计新的网站架构"
./bin/pm-local capture "迁移现有内容"
./bin/pm-local capture "测试和部署"

# 3. 查看项目状态
./bin/pm-local project status "网站重构"
```

#### 配置说明

**Gemini API 配置**：
```bash
# 可选：Gemini API 密钥
export PM_GEMINI_API_KEY=your_gemini_api_key

# Gemini CLI 配置文件路径（如需要）
export GEMINI_CONFIG_PATH=~/.config/gemini/config.yaml
```

**工具注册**：
在 Gemini CLI 中注册 PersonalManager 工具：
```yaml
# ~/.config/gemini/tools.yaml
tools:
  - name: "personal_manager"
    command: "./bin/pm-local"
    description: "PersonalManager 个人效能工具集"
    working_directory: "/path/to/personal-manager"
```

## 使用指南

### 基础使用流程

#### 1. 环境准备
```bash
# 确保在 PersonalManager 项目根目录
cd /path/to/personal-manager

# 验证启动器可用性
./bin/pm-local --launcher-debug

# 首次初始化（如需要）
./bin/pm-local setup
```

#### 2. Agent 集成使用

**Claude Code 场景**：
1. 在 Claude Code 中打开 PersonalManager 项目
2. 使用自然语言描述需求
3. Claude 自动执行相应的 `./bin/pm-local` 命令
4. 查看执行结果并继续对话

**Gemini CLI 场景**：
1. 启动 Gemini CLI 并切换到项目目录
2. 使用自然语言描述个人效能需求
3. Gemini 将需求转换为具体命令并执行
4. 基于结果继续深入对话

### 常用 Agent 场景示例

#### 场景 1：项目状态检查
**用户需求**："帮我了解一下当前所有项目的状态"
**Agent 执行**：
```bash
./bin/pm-local projects overview
```

#### 场景 2：任务管理工作流
**用户需求**："我想添加一些任务，然后看看今天应该重点做什么"
**Agent 执行**：
```bash
# 添加任务
./bin/pm-local capture "完成季度报告"
./bin/pm-local capture "准备团队会议"
./bin/pm-local capture "回复重要邮件"

# 理清任务
./bin/pm-local clarify

# 获取今日推荐
./bin/pm-local today
```

#### 场景 3：深度工作会话
**用户需求**："帮我安排一个专注工作时段，我需要完成重要的设计工作"
**Agent 执行**：
```bash
# 创建深度工作会话
./bin/pm-local deepwork create "UI设计优化"

# 开始深度工作
./bin/pm-local deepwork start

# 完成后结束并记录反思
# （在工作完成后）
./bin/pm-local deepwork end
```

#### 场景 4：习惯跟踪
**用户需求**："帮我查看今天的习惯计划，并记录完成情况"
**Agent 执行**：
```bash
# 查看今日习惯
./bin/pm-local habits today

# 记录习惯完成
./bin/pm-local habits track "晨间阅读"
./bin/pm-local habits track "运动锻炼"
```

### 高级使用技巧

#### 1. 链式命令执行
Agent 可以组合多个命令实现复杂工作流：
```bash
# 完整的项目管理工作流
./bin/pm-local projects overview && \
./bin/pm-local project status "重要项目" && \
./bin/pm-local capture "项目相关的紧急任务" && \
./bin/pm-local today
```

#### 2. 条件执行
基于命令结果进行条件执行：
```bash
# 如果项目状态良好，则继续添加新任务
./bin/pm-local project status "项目A" | grep -q "Good" && \
./bin/pm-local capture "项目A的后续任务"
```

#### 3. 输出解析
Agent 可以解析命令输出并提供智能分析：
```bash
# 获取项目概览并分析状态分布
./bin/pm-local projects overview > /tmp/projects_status.txt
# Agent 分析输出并提供建议
```

## 测试验证

### 功能测试清单

#### 1. 启动器基础功能测试

**环境检测测试**：
```bash
# 测试 Poetry 环境
./bin/pm-local --launcher-debug

# 测试基本命令执行
./bin/pm-local --help
./bin/pm-local --version
```

**执行策略测试**：
```bash
# 在有 Poetry 的环境中测试
poetry --version && ./bin/pm-local status

# 在无 Poetry 的环境中测试（移除或重命名 pyproject.toml）
mv pyproject.toml pyproject.toml.bak && ./bin/pm-local status
mv pyproject.toml.bak pyproject.toml
```

#### 2. Agent 集成测试

**Claude Code 集成测试**：
1. 在 Claude Code 中打开项目
2. 要求 Claude 执行：`./bin/pm-local projects overview`
3. 验证输出正确性
4. 测试错误处理（如无效命令）

**Gemini CLI 集成测试**：
1. 启动 Gemini CLI
2. 切换到项目目录
3. 要求 Gemini 执行：`./bin/pm-local today`
4. 验证命令映射的准确性

#### 3. 错误处理测试

**环境错误测试**：
```bash
# 测试 Python 不可用的情况
PATH=/usr/bin:/bin ./bin/pm-local status

# 测试源码目录缺失的情况
mv src src.bak && ./bin/pm-local status
mv src.bak src
```

**命令错误测试**：
```bash
# 测试无效命令
./bin/pm-local invalid_command

# 测试参数错误
./bin/pm-local project status
```

### 性能基准测试

#### 1. 启动时间测试
```bash
# 测试启动器启动时间
time ./bin/pm-local --version

# 对比 Poetry 和直接执行的性能差异
time poetry run pm --version
time PYTHONPATH=src python3 -m pm.cli.main --version
```

#### 2. 内存使用测试
```bash
# 监控内存使用
/usr/bin/time -v ./bin/pm-local projects overview
```

### 自动化测试

#### 集成测试脚本

创建 `tests/integration/test_agent_integration.py`：
```python
#!/usr/bin/env python3
"""
Agent 集成自动化测试脚本
"""

import subprocess
import os
import sys
from pathlib import Path

def test_launcher_basic():
    """测试启动器基本功能"""
    result = subprocess.run(
        ["./bin/pm-local", "--help"], 
        capture_output=True, 
        text=True
    )
    assert result.returncode == 0
    assert "PersonalManager" in result.stdout

def test_launcher_debug():
    """测试启动器调试功能"""
    result = subprocess.run(
        ["./bin/pm-local", "--launcher-debug"], 
        capture_output=True, 
        text=True
    )
    assert result.returncode == 0
    assert "Environment Information" in result.stdout

def test_command_execution():
    """测试命令执行"""
    result = subprocess.run(
        ["./bin/pm-local", "status"], 
        capture_output=True, 
        text=True
    )
    # 应该成功执行（返回码 0）或给出友好错误
    assert result.returncode in [0, 1]

if __name__ == "__main__":
    os.chdir(Path(__file__).parent.parent.parent)
    
    print("开始 Agent 集成测试...")
    test_launcher_basic()
    print("✅ 启动器基本功能测试通过")
    
    test_launcher_debug()
    print("✅ 启动器调试功能测试通过")
    
    test_command_execution()
    print("✅ 命令执行测试通过")
    
    print("🎉 所有 Agent 集成测试通过！")
```

## 故障排查

### 常见问题与解决方案

#### 1. 启动器无法执行

**问题**：`./bin/pm-local: Permission denied`
**解决方案**：
```bash
chmod +x ./bin/pm-local
```

**问题**：`bash: ./bin/pm-local: No such file or directory`
**解决方案**：
```bash
# 确保在项目根目录
cd /path/to/personal-manager

# 验证文件存在
ls -la bin/pm-local
```

#### 2. 环境检测问题

**问题**：`Poetry not available`
**诊断**：
```bash
# 检查 Poetry 安装
poetry --version

# 检查 pyproject.toml
ls -la pyproject.toml
```

**解决方案**：
```bash
# 安装 Poetry（如需要）
curl -sSL https://install.python-poetry.org | python3 -

# 或使用直接 Python 执行（无需 Poetry）
PYTHONPATH=src python3 -m pm.cli.main --help
```

#### 3. Python 模块导入问题

**问题**：`Cannot import pm.cli.main module`
**诊断**：
```bash
# 检查源码结构
ls -la src/pm/cli/main.py

# 测试模块导入
PYTHONPATH=src python3 -c "import pm.cli.main; print('Import successful')"
```

**解决方案**：
```bash
# 安装依赖（Poetry 环境）
poetry install

# 或安装依赖（pip 环境）
pip install -r requirements.txt  # 如果有的话
```

#### 4. Agent 集成问题

**问题**：Claude/Gemini 无法调用命令
**诊断检查**：
1. 验证 Agent 是否在正确的项目目录
2. 检查 `./bin/pm-local` 文件权限
3. 测试手动执行命令是否正常

**解决方案**：
```bash
# 确保在正确目录
pwd
# 应该显示 PersonalManager 项目路径

# 测试启动器
./bin/pm-local --launcher-debug

# 验证基本功能
./bin/pm-local --help
```

### 调试工具

#### 1. 启动器调试模式
```bash
# 获取详细的环境信息
./bin/pm-local --launcher-debug

# 输出示例分析
Project Root: /path/to/personal-manager  # ✓ 路径正确
Python Version: Python 3.11.5            # ✓ Python 可用
Poetry Available: Yes                     # ✓ Poetry 可用
pyproject.toml: Found                    # ✓ 配置文件存在
Source Directory: Found                  # ✓ 源码目录存在
```

#### 2. 详细错误输出
启动器内置的错误输出会提供：
- 彩色状态指示（红色错误、黄色警告、绿色成功）
- 具体错误原因
- 建议的解决步骤

#### 3. 系统诊断命令
```bash
# PersonalManager 系统状态
./bin/pm-local status

# 配置信息检查
./bin/pm-local setup --dry-run

# 隐私和数据验证
./bin/pm-local privacy verify
```

### 日志和监控

#### 1. 执行日志
启动器会在 stderr 中输出执行信息：
```bash
# 查看详细执行过程
./bin/pm-local projects overview 2>&1 | tee execution.log
```

#### 2. 系统监控
```bash
# 监控系统资源使用
./bin/pm-local monitor start &

# 检查后台监控状态
./bin/pm-local monitor status
```

### 问题上报

如果遇到无法解决的问题，请收集以下信息：

1. **环境信息**：
```bash
./bin/pm-local --launcher-debug > debug_info.txt
```

2. **错误输出**：
```bash
./bin/pm-local <failing_command> 2>&1 > error_output.txt
```

3. **系统信息**：
```bash
# 操作系统
uname -a

# Python 版本
python3 --version

# Poetry 版本（如适用）
poetry --version
```

将以上信息整理后提交到项目的 Issue 跟踪系统，以便开发团队快速定位和解决问题。

---

## 总结

通过实施本文档描述的项目级 Agent 接入与命令映射机制，PersonalManager 实现了：

1. **统一的 Agent 接入点**：`./bin/pm-local` 作为标准化入口
2. **智能环境适配**：自动选择最佳执行策略
3. **无缝 AI 集成**：支持 Claude、Gemini CLI 等多种 Agent
4. **强大的错误处理**：提供友好的诊断和故障排查机制
5. **完整的测试覆盖**：确保系统稳定可靠

这套机制为用户提供了真正"自然语言驱动"的个人效能管理体验，让 AI Agent 成为个人生产力的智能放大器。

---

**文档版本历史**：
- v1.0 (2025-09-14): 初始版本，包含完整的架构设计和实施指南