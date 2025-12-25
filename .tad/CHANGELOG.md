✅ TAD v3.1 配置已安装 - Tue Nov 25 09:51:24 EST 2025

## [3.1.0] - 2025-11-25

### 重大升级：证据式质量保证 + Human可视化赋能 + 持续学习

**基于**: MenuSnap项目实证分析 + 三份核心文档综合
**向后兼容**: 100%兼容v3.0

### 新增功能

#### 1. 证据式验证系统
- 新增6种证据类型：search_result, code_location, data_flow_diagram, state_flow_diagram, ui_screenshot, test_result
- 每种证据都有明确的格式要求和Human验证点
- 证据要求与强制问题（MQ）绑定

#### 2. 强制问题系统（MQ1-5）
- MQ1: 历史代码搜索 - 防止重复造轮子
- MQ2: 函数存在性验证 - 防止调用不存在的函数
- MQ3: 数据流完整性 - 确保后端数据都到前端显示
- MQ4: 视觉层级 - 确保不同状态视觉可区分
- MQ5: 状态同步 - 防止多状态不一致问题
- 所有MQ都有自动触发条件和证据要求

#### 3. 渐进式验证（Progressive Validation）
- Phase划分：将大任务分解为2-4小时的Phase
- Phase检查点：每个Phase完成后Human验证
- 提前发现方向错误，避免全部返工

#### 4. Human角色增强
- 从"被动验收者"升级为"主动验证者+学习者"
- Gate 2审查：设计完成时验证证据（10-15分钟）
- Phase检查点：渐进验证方向（5-10分钟/Phase）
- 不需要技术知识，看图表和截图即可判断

#### 5. 学习机制系统
- Decision Rationale（决策理由）：理解技术权衡
- Interactive Challenge（互动挑战）：主动思考
- Impact Visualization（影响可视化）：看到连锁反应
- What-If Scenarios（假设场景）：对比理解
- Failure Learning Entry（失败学习）：从错误中学习
- 4个学习维度：技术决策、系统思维、产品/UX、质量意识

#### 6. Sub-Agent强制使用
- Agent A强制：product-expert, backend-architect, code-reviewer
- Agent B强制：parallel-coordinator, bug-hunter, test_runner
- 带证据验证和使用记录

#### 7. 失败学习闭环
- 自动捕获Human纠正的错误
- 分析应该由哪个MQ拦截
- 生成MQ更新建议
- Human审核后自动更新配置

### 更新内容

#### 配置文件
- `config.yaml`: 新增v3.1完整配置（716行）
- 修复了原有的YAML格式问题

#### 模板文件
- `handoff-a-to-b.md`: 完全重写为v3.1版本
  - 新增"强制问题回答"部分（MQ1-5）
  - 新增Phase证据要求
  - 新增Sub-Agent使用记录
  - 新增Learning Content部分

#### 新增文件
- `.tad/guides/human-quick-reference.md`: Human快速参考指南
- `.tad/guides/evidence-collection-guide.md`: 证据收集指南
- `.tad/evidence/metrics/tad-v31-metrics.yaml`: 指标追踪文件
- `verify-v31-upgrade.sh`: 升级验证脚本

#### 新增目录
- `.tad/guides/`: 指南文档目录
- `.tad/evidence/patterns/`: 失败模式记录
- `.tad/evidence/failures/`: 失败学习入口
- `.tad/evidence/metrics/`: 指标追踪

### 改进

- **质量提升**: Gate 2问题发现率从0%提升到预期>50%
- **时间节省**: 每个功能节省3-6小时返工时间
- **Human参与**: 投入30-60分钟审查+学习，获得更好的结果
- **系统进化**: 失败自动转化为未来的检查点

### 迁移指南

v3.0项目可无缝迁移到v3.1：
1. 所有v3.0功能100%保留
2. 可选择性启用v3.1特性
3. 完整的回滚支持

### 回滚

如需回滚到v3.0：
```bash
# 恢复config.yaml
cp .tad/config.yaml.backup.v3.0.YYYYMMDD_HHMMSS .tad/config.yaml

# 恢复handoff模板
cp .tad/templates/handoff-a-to-b.md.v3.0.backup .tad/templates/handoff-a-to-b.md

# 更新版本
echo "3.0" > .tad/version.txt
```

### 验证

运行验证脚本确认升级成功：
```bash
./verify-v31-upgrade.sh
```

