# PersonalManager 自动化工作流程

> **目的**: 确保需求管理、功能更新、简报生成的自动联动
> **创建时间**: 2025-09-15 20:15

## 🔄 自动触发机制

### 1️⃣ 需求接收时 - 自动触发筛选

**触发条件**：
- 用户说："我想要..."、"能不能..."、"需要..."
- 用户报告问题："...不工作"、"...有问题"
- 用户提出改进："应该..."、"最好..."

**Claude必须执行**：
```markdown
1. 立即响应："让我先检查现有功能是否能满足您的需求..."
2. 执行需求筛选（REQUIREMENT_TRIAGE.md）
3. 显示筛选结果
4. 根据分类决定下一步
```

### 2️⃣ 开发完成后 - 自动更新清单

**触发条件**：
- 新增任何文件
- 修改核心功能
- 添加新命令或脚本

**Claude必须执行**：
```markdown
1. 更新 DEVELOPMENT_LOG.md
2. 更新 FUNCTION_INVENTORY.md
3. 如果是新功能，添加到相应类别
4. 运行验证脚本（如果存在）
```

### 3️⃣ 功能更新后 - 自动同步简报

**触发条件**：
- FUNCTION_INVENTORY.md 被更新
- 新功能添加完成
- 每次运行 pm briefing

**系统必须执行**：
```markdown
1. 读取最新的 FUNCTION_INVENTORY.md
2. 更新 claude_context.json 中的功能列表
3. 在简报中显示新功能提示
```

## 📋 Claude行为检查清单

### 收到需求时必须问自己：
- [ ] 我是否先检查了现有功能？
- [ ] 我是否进行了需求分类（Type A-E）？
- [ ] 我是否记录了需求分析？
- [ ] 我是否选择了最简单的解决方案？

### 完成开发后必须：
- [ ] 更新 DEVELOPMENT_LOG.md
- [ ] 更新 FUNCTION_INVENTORY.md
- [ ] 测试新功能
- [ ] 通知用户如何使用

### 简报生成时必须：
- [ ] 读取最新功能清单
- [ ] 检查近期更新
- [ ] 包含新功能提示

## 🔧 实现方案

### 方案1：脚本自动化（推荐）

创建触发脚本：
```python
# scripts/update_function_inventory.py
"""
自动更新功能清单
- 扫描所有命令
- 检查新增脚本
- 更新 FUNCTION_INVENTORY.md
"""

# scripts/sync_to_briefing.py
"""
同步功能到简报系统
- 读取 FUNCTION_INVENTORY.md
- 生成功能统计
- 更新 claude_context.json
"""
```

### 方案2：Git Hooks
```bash
# .git/hooks/post-commit
# 提交后自动更新功能清单
./scripts/update_function_inventory.py
```

### 方案3：实时监控
```python
# 在 briefing_generator.py 中
def generate_briefing():
    # 实时读取最新功能清单
    inventory = read_function_inventory()
    context['available_functions'] = inventory.get_stats()
```

## 🎯 立即行动计划

1. **短期修复**（立即）
   - Claude 承诺：收到需求时自动执行筛选流程
   - Claude 承诺：开发后自动更新文档

2. **中期改进**（本周）
   - 创建自动更新脚本
   - 修改简报生成器读取最新功能

3. **长期优化**（下月）
   - 实现完全自动化的工作流
   - 添加版本控制和回滚机制

## ⚠️ Claude提醒机制

```python
# Claude 内部检查逻辑（伪代码）
def on_user_request(request):
    if contains_requirement_keywords(request):
        print("⚙️ 正在执行需求筛选流程...")
        execute_requirement_triage()

def after_development():
    print("📝 正在更新功能清单...")
    update_function_inventory()
    update_development_log()

def on_briefing_request():
    print("🔄 正在获取最新功能信息...")
    sync_latest_functions()
```

## 📊 成功指标

- 需求筛选执行率：100%
- 功能清单更新及时性：开发后立即更新
- 简报功能准确性：始终显示最新功能

---

**维护者**: Claude
**下次评估**: 每周检查执行情况