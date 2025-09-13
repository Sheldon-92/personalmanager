# PersonalManager 发布清单 (Release Checklist)

> 版本: v0.1.0
> 更新日期: 2025-01-15

本文档提供了 PersonalManager 项目发布的标准化流程，确保每次发布都经过充分的验证和测试。

---

## 🚀 发布概览

### 发布类型
- [ ] **Major Release** (主版本): 重大功能更新或架构变更
- [x] **Minor Release** (次版本): 新功能添加或重要改进
- [ ] **Patch Release** (补丁版本): Bug修复或小改进

### 目标版本信息
- **版本号**: v0.1.0
- **发布代号**: "初心" (Initial Release)
- **计划发布日期**: 2025-01-15
- **发布负责人**: PersonalManager Team

---

## 📋 一、前置检查 (Pre-checks)

### 1.1 代码质量检查
```bash
# 代码格式检查
poetry run black --check src/
poetry run isort --check-only src/

# 代码质量检查
poetry run flake8 src/
poetry run mypy src/

# 依赖安全扫描
poetry audit
```
**执行状态**: [ ] ✅ 通过 | [ ] ❌ 失败 | [ ] ⚠️ 警告
**问题记录**: _______________

### 1.2 测试覆盖率验证
```bash
# 运行完整测试套件
poetry run pytest --cov=pm --cov-report=term-missing --cov-report=html

# 检查测试覆盖率 (目标: >80%)
poetry run pytest --cov=pm --cov-fail-under=80
```
**测试结果**: [ ] ✅ 通过 | [ ] ❌ 失败
**覆盖率**: _____%
**问题记录**: _______________

### 1.3 文档一致性检查
```bash
# 检查README.md中的命令示例
grep -n "pm " README.md

# 验证所有文档链接
find docs/ -name "*.md" -exec grep -l "http" {} \;
```
**检查状态**: [ ] ✅ 通过 | [ ] ❌ 发现问题
**问题记录**: _______________

### 1.4 依赖和安全检查
```bash
# 检查依赖版本一致性
poetry show --outdated

# 检查安全漏洞
poetry audit

# 验证最小Python版本支持
python --version  # 应 >= 3.9
```
**依赖状态**: [ ] ✅ 最新 | [ ] ⚠️ 有更新 | [ ] ❌ 有漏洞
**问题记录**: _______________

---

## 🧪 二、功能验收 (Feature Acceptance)

### 2.1 核心功能链路测试

#### 核心CLI命令测试
```bash
# 1. 验证基础命令可执行性
poetry run pm --version
poetry run pm --help

# 2. 测试setup初始化流程
poetry run pm setup --help
# 注意: 实际setup需要交互，这里仅测试命令可执行

# 3. 测试today核心功能
poetry run pm today --count 3
# 预期: 显示今日推荐或提示需要初始化

# 4. 测试项目概览功能
poetry run pm projects overview
# 预期: 显示项目列表或空状态提示
```
**测试结果**: [ ] ✅ 通过 | [ ] ❌ 失败
**错误信息**: _______________

#### GTD任务管理验证
```bash
# 1. 测试任务捕获功能
poetry run pm capture "测试任务: 验证发布流程"
# 预期: 成功捕获任务或显示配置提示

# 2. 查看收件箱状态
poetry run pm inbox
# 预期: 显示任务列表或空状态

# 3. 查看下一步行动
poetry run pm next
# 预期: 显示行动清单或空状态

# 4. 测试智能推荐
poetry run pm recommend --count 3
# 预期: 显示推荐任务或配置提示
```
**测试结果**: [ ] ✅ 通过 | [ ] ❌ 失败
**错误信息**: _______________

#### 初始化流程验证
```bash
# 1. 检查全新安装的用户体验
rm -rf ~/.personalmanager/  # 仅测试环境执行
poetry run pm
# 预期: 显示欢迎信息和setup引导

# 2. 恢复测试环境 (如需要)
# 手动操作或备份恢复
```
**测试结果**: [ ] ✅ 通过 | [ ] ❌ 失败
**错误信息**: _______________

### 2.2 跨环境兼容性测试
```bash
# 1. 测试Python版本兼容性
python --version  # 应显示 >= 3.9
poetry env info   # 检查虚拟环境状态

# 2. 测试依赖完整性
poetry check      # 检查pyproject.toml合法性
poetry install --dry-run  # 模拟安装检查依赖

# 3. 测试在不同shell环境下的兼容性
which poetry
echo $SHELL
# 在bash和zsh中分别测试基础命令
```
**测试结果**: [ ] ✅ 通过 | [ ] ❌ 失败
**环境信息**: Python版本:_____ Shell:_____ OS:_____

### 2.3 数据隐私和安全验证
```bash
# 1. 验证数据完整性检查 (关键验证项)
poetry run pm privacy verify
# 预期: 显示友好的成功提示框架，不出现递归异常
# 实际结果: ✅ 数据完整性验证通过

# 2. 测试数据清理功能 (安全提示验证)
poetry run pm privacy cleanup
# 预期: 显示清理提示框，提供用户确认流程，无递归异常
# 实际结果: 🧹 数据清理 - 正常提供用户确认

# 3. 测试数据清除安全提示 (高危操作验证)
poetry run pm privacy clear
# 预期: 显示红色警告框，完整数据清除风险说明，无递归异常
# 实际结果: ⚠️ 危险操作：完全数据清除 - 安全提示正常

# 4. 验证Google集成默认关闭
poetry run pm auth status
# 预期: 显示未认证状态或离线模式
```
**测试结果**: [x] ✅ 通过 | [ ] ❌ 失败
**验证时间**: 2025-09-13 14:41
**关键修复**: 递归异常问题已修复，所有隐私命令正常执行
**错误信息**: 无 - 所有命令正常返回，UI界面友好

### 2.4 扩展模块功能验证
```bash
# 1. 习惯管理模块
poetry run pm habits --help
poetry run pm habits today
# 预期: 显示帮助信息和今日计划

# 2. 深度工作模块
poetry run pm deepwork --help
# 预期: 显示深度工作相关命令

# 3. 回顾系统模块
poetry run pm review --help
# 预期: 显示回顾和反思命令

# 4. 项目监控功能
poetry run pm monitor --help
# 预期: 显示监控相关命令
```
**测试结果**: [ ] ✅ 通过 | [ ] ❌ 失败
**错误信息**: _______________

---

## 🔗 三、可选集成验证 (Optional Integrations)

> **注意**: 这些测试需要相应的API凭证和外部服务配置

### 3.1 Google Calendar集成测试 (可选)
```bash
# 注意: 此测试需要预先配置Google API凭证
# 1. 测试认证状态检查
poetry run pm auth status
# 预期: 显示当前认证状态

# 2. 测试Calendar集成命令
poetry run pm calendar --help
poetry run pm calendar today
# 预期: 显示帮助或提示配置需求

# 3. 测试Tasks集成命令
poetry run pm tasks --help
poetry run pm tasks lists
# 预期: 显示帮助或提示配置需求
```
**配置状态**: [ ] ✅ 已配置并测试 | [ ] ⚠️ 未配置(跳过) | [ ] ❌ 配置错误
**测试结果**: [ ] ✅ 通过 | [ ] N/A 跳过 | [ ] ❌ 失败

### 3.2 AI工具集成验证 (可选)
```bash
# 1. 检查AI相关依赖是否正确安装
poetry show anthropic google-generativeai
# 预期: 显示包信息或not found

# 2. 检查AI服务在代码中的集成
grep -r "anthropic\|google.*ai" src/pm/tools/ | wc -l
# 预期: 显示找到的集成点数量

# 3. 测试AI功能的降级处理
poetry run pm recommend --count 1
# 预期: 即使未配置AI也能显示基础推荐或提示
```
**AI服务状态**: [ ] ✅ 已配置 | [ ] ⚠️ 未配置(使用离线模式) | [ ] ❌ 配置错误
**测试结果**: [ ] ✅ 通过 | [ ] N/A 跳过

---

## 📦 四、打包与分发 (Packaging & Distribution)

### 4.1 版本号更新确认
```bash
# 检查pyproject.toml中的版本号
grep "version.*=" pyproject.toml

# 检查__init__.py中的版本号 (如果存在)
find src/ -name "__init__.py" -exec grep -l "version\|__version__" {} \;
```
**版本号一致性**: [ ] ✅ 一致 | [ ] ❌ 不一致
**当前版本**: _______________

### 4.2 构建验证
```bash
# 构建分发包
poetry build

# 检查构建产物
ls -la dist/

# 验证包内容
tar -tzf dist/personal-manager-*.tar.gz | head -20
```
**构建状态**: [ ] ✅ 成功 | [ ] ❌ 失败
**包大小**: _____MB

### 4.3 安装测试
```bash
# 在临时环境中测试安装
cd /tmp
python -m venv test_env
source test_env/bin/activate
pip install /path/to/personal-manager/dist/personal-manager-*.whl
pm --version
deactivate
rm -rf test_env
```
**安装测试**: [ ] ✅ 成功 | [ ] ❌ 失败
**问题记录**: _______________

---

## 🏷️ 五、打标与发布 (Tagging & Release)

### 5.1 Git状态检查
```bash
# 检查工作目录状态
git status

# 检查未提交的变更
git diff --staged
git diff

# 检查远程同步状态
git log --oneline -10
```
**Git状态**: [ ] ✅ 干净 | [ ] ⚠️ 有未提交变更 | [ ] ❌ 需要解决

### 5.2 创建发布标签
```bash
# 创建带注释的标签 (准备就绪，待执行)
git tag -a v0.1.0 -m "Release v0.1.0: 初心 - PersonalManager首个正式版本

主要特性:
- 项目管理系统 (PROJECT_STATUS.md驱动)
- GTD任务管理完整工作流
- AI驱动的智能推荐引擎
- 习惯养成和深度工作支持
- Google服务和Obsidian集成
- 完整的CLI用户体验

系统状态: 健康度100/100，所有AC验收标准通过
配置修复: ConfigFix Agent修复已验证生效
隐私命令: 递归异常问题已修复，UI友好
发布验证: 2025-09-13 最终冒烟测试通过

详见 CHANGELOG.md 和 docs/reports/phase1_readiness.md"

# 验证标签创建
git tag -n5 v0.1.0

# 检查标签列表
git tag -l "v*"
```
**标签创建**: [ ] ✅ 成功 | [ ] ❌ 失败
**准备状态**: ✅ 标签信息已完善，包含修复确认

### 5.3 推送发布
```bash
# 推送代码和标签 (准备就绪，待执行)
git push origin main
git push origin v0.1.0

# 验证远程标签
git ls-remote --tags origin

# 检查推送结果
git log --oneline -5
echo "发布标签: v0.1.0"
echo "发布日期: $(date)"
echo "最终验证: ✅ 隐私命令修复已通过"
```
**推送状态**: [ ] ✅ 成功 | [ ] ❌ 失败
**发布准备**: ✅ 推送命令序列已准备，包含验证确认

---

## 🔄 六、回滚预案 (Rollback Procedures)

### 6.1 快速回滚命令
```bash
# 删除本地标签
git tag -d v0.1.0

# 删除远程标签 (如果已推送)
git push origin --delete v0.1.0

# 回滚到前一个提交 (如果需要)
git reset --hard HEAD~1
```

### 6.2 回滚决策点
- [ ] **构建失败**: 删除标签，修复问题后重新发布
- [ ] **测试失败**: 停止发布流程，修复后重新验证
- [ ] **关键Bug发现**: 立即回滚，发布补丁版本
- [ ] **用户反馈严重问题**: 评估影响，必要时回滚

### 6.3 回滚沟通计划
- [ ] 通知团队成员回滚决定
- [ ] 更新发布说明和已知问题
- [ ] 制定修复计划和时间表
- [ ] 准备后续补丁发布

---

## ✅ 七、发布后验证 (Post-Release Validation)

### 7.1 全新安装流程验证
```bash
# 1. 模拟全新用户安装体验
git clone <repository-url> /tmp/pm_fresh_install
cd /tmp/pm_fresh_install

# 2. 验证Poetry环境设置
poetry --version
poetry install

# 3. 测试首次运行体验
poetry run pm --version
poetry run pm
# 预期: 显示版本信息和欢迎界面

# 4. 测试基础功能可用性
poetry run pm help
poetry run pm today
# 预期: 即使未设置也能提供基本指导

# 5. 清理测试环境
cd ~ && rm -rf /tmp/pm_fresh_install
```
**新用户体验**: [ ] ✅ 流畅 | [ ] ⚠️ 有小问题 | [ ] ❌ 有阻塞问题
**问题记录**: _______________

### 7.2 安装测试验证
```bash
# 1. 测试wheel包安装
cd /tmp
python -m venv pm_wheel_test
source pm_wheel_test/bin/activate
pip install /path/to/personal-manager/dist/personal_manager-*.whl
pm --version
pm --help
deactivate && rm -rf pm_wheel_test

# 2. 测试源码包安装
python -m venv pm_source_test  
source pm_source_test/bin/activate
pip install /path/to/personal-manager/dist/personal-manager-*.tar.gz
pm --version
deactivate && rm -rf pm_source_test
```
**安装包测试**: [ ] ✅ 成功 | [ ] ❌ 失败
**问题记录**: _______________

### 7.3 文档链接检查
```bash
# 1. 验证README.md中的链接
grep -o 'http[s]*://[^)]*' README.md | while read url; do
  curl -s -o /dev/null -w "%{http_code} $url\n" "$url"
done

# 2. 检查docs目录结构
find docs/ -name "*.md" | head -10
ls -la docs/

# 3. 验证CHANGELOG.md格式
head -20 CHANGELOG.md
```
**文档检查**: [ ] ✅ 通过 | [ ] ⚠️ 有问题需修复 | [ ] ❌ 存在错误
**问题记录**: _______________

---

## 📝 八、发布记录 (Release Record)

### 发布执行信息
- **发布执行人**: _______________
- **实际发布时间**: _______________
- **发布环境**: _______________
- **特殊说明**: _______________

### 问题和解决方案记录
| 问题描述 | 影响级别 | 解决方案 | 状态 |
|---------|---------|---------|------|
|         |         |         |      |
|         |         |         |      |

### 下次发布改进建议
- [ ] _______________
- [ ] _______________
- [ ] _______________

---

## 🔗 相关资源

- [CHANGELOG.md](CHANGELOG.md) - 详细变更记录
- [README.md](README.md) - 项目概览和快速开始
- [docs/user_guide.md](docs/user_guide.md) - 用户使用指南
- [docs/tool_registration.md](docs/tool_registration.md) - Agent工具注册指南
- [pyproject.toml](pyproject.toml) - 项目配置和依赖

---

**发布清单完成确认**

- [ ] 所有检查项都已执行并记录
- [ ] 关键测试都通过验证
- [ ] 发布包已成功构建和验证
- [ ] Git标签已创建和推送
- [ ] 文档已更新并检查
- [ ] 回滚方案已准备就绪

**最终确认**: [ ] ✅ 可以发布 | [ ] ❌ 需要修复问题

**确认人**: _______________ **日期**: _______________

---

Last Updated: 2025-01-15