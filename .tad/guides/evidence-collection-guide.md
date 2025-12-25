# TAD v3.1 证据收集指南
## Alex和Blake的证据提供指南

---

## 证据类型概览

TAD v3.1定义了6种证据类型，每种都有特定的格式和用途：

### 1. 搜索结果（search_result）
- **用途**：证明确实搜索了历史代码
- **格式**：命令 + 结果截图或文本输出
- **必需于**：MQ1 历史代码搜索

**示例**：
\`\`\`bash
# 搜索命令
grep -r "calculateScore" src/

# 结果
src/lib/utils.ts:42: export function calculateScoreAndReasons(...)
src/api/recommend.ts:156: const score = calculateScore(menu, prefs)
\`\`\`

### 2. 代码位置证明（code_location）
- **用途**：证明函数/组件确实存在
- **格式**：Markdown表格：函数名 | 文件位置 | 行号 | 代码片段 | 验证状态
- **必需于**：MQ2 函数存在性验证

**示例**：
| 函数名 | 位置 | 行号 | 代码片段 | 验证 |
|--------|------|------|---------|------|
| calculateScore | src/lib/utils.ts | 42 | \`export function calculateScore(...)\` | ✅ |
| getMenuData | src/api/menu.ts | 23 | \`export async function getMenuData()\` | ✅ |

### 3. 数据流图（data_flow_diagram）
- **用途**：展示数据从后端到前端的完整流动
- **格式**：Mermaid图 + Markdown对照表
- **必需于**：MQ3 数据流完整性

**示例**：
\`\`\`mermaid
graph LR
  A[Backend API] -->|计算| B[score, reasons, warnings]
  B -->|传递| C[Frontend]
  C -->|显示| D[ScoreDisplay]
  C -->|显示| E[ReasonList]
  C -->|显示| F[WarningAlert]
\`\`\`

| 后端字段 | 前端组件 | 是否显示 | 不显示原因 |
|---------|---------|---------|-----------|
| score | ScoreDisplay | ✅ | - |
| matchReasons | ReasonList | ✅ | - |
| warnings | WarningAlert | ✅ | - |

### 4. 状态流图（state_flow_diagram）
- **用途**：展示状态的来源、存储位置、同步时机
- **格式**：ASCII图或Mermaid状态图
- **必需于**：MQ5 状态同步

**单一状态示例**：
\`\`\`
[用户输入] → state.preferences (唯一存储)
✅ 只有一个状态，无需同步
\`\`\`

**多状态同步示例**：
\`\`\`
[用户输入] → preferences.allergens (主状态，Source of Truth)
              ↓ 同步时机：onSubmit事件触发
           dietaryRestrictions.allergies (备份状态)
\`\`\`

### 5. UI截图（ui_screenshot）
- **用途**：证明功能的视觉效果
- **格式**：浏览器截图或UI mockup
- **必需于**：MQ4（视觉层级）、Phase完成报告

**要求**：
- 清晰显示UI的关键元素
- 能看出不同状态的视觉区别
- 可以是实际截图或设计稿

### 6. 测试结果（test_result）
- **用途**：证明代码能运行、测试通过
- **格式**：测试运行截图或日志输出
- **必需于**：Phase完成报告

**示例**：
\`\`\`
✓ 42 tests passing
✓ Coverage: 87%
✓ All edge cases handled
\`\`\`

---

## Alex的证据收集清单

### Gate 2（设计完成时）

在创建handoff前，Alex必须收集并提供以下证据：

#### MQ1：历史代码搜索
- [ ] 执行搜索命令
- [ ] 截图或复制搜索结果
- [ ] 说明决策理由（复用/创建新的）

#### MQ2：函数存在性
- [ ] 列出所有将调用的函数
- [ ] 找到每个函数的位置（文件:行号）
- [ ] 复制函数签名代码片段
- [ ] 标记验证状态（✅/❌）

#### MQ3：数据流完整性
- [ ] 列出后端返回的所有字段
- [ ] 为每个字段指定前端显示组件
- [ ] 绘制数据流Mermaid图
- [ ] 说明不显示字段的原因

#### MQ4：视觉层级
- [ ] 列出不同状态
- [ ] 为每个状态定义视觉表现
- [ ] 提供UI mockup或截图

#### MQ5：状态同步
- [ ] 列出所有存储位置
- [ ] 标注主状态（Source of Truth）
- [ ] 绘制状态流图
- [ ] 说明同步时机和触发条件

---

## Blake的证据收集清单

### Phase完成时

每个Phase完成后，Blake必须提供：

#### 代码证据
- [ ] 关键函数的代码截图
- [ ] 文件路径和行号说明
- [ ] 简要实现说明

#### 测试证据
- [ ] 测试运行截图（所有通过）
- [ ] 覆盖率报告
- [ ] Edge case测试日志

#### UI证据（如有UI变化）
- [ ] 浏览器截图
- [ ] 不同状态的UI展示
- [ ] 响应式布局验证

#### 进度说明
- [ ] 遇到的问题和解决方法
- [ ] 偏离设计的地方（如有）及原因
- [ ] 下个Phase的准备情况

---

## 快速收集技巧

### 对于Alex

**搜索历史代码**：
\`\`\`bash
# 搜索函数
grep -r "functionName" src/

# 搜索组件
find src -name "*ComponentName*"

# 搜索关键字
rg "keyword" src/
\`\`\`

**验证函数存在**：
\`\`\`bash
# 快速定位函数
grep -n "export function functionName" src/**/*.ts
\`\`\`

**生成数据流图**：
- 先列出后端响应的所有字段
- 再逐个找到前端使用的地方
- 使用Mermaid Live Editor绘图

### 对于Blake

**截图测试结果**：
\`\`\`bash
# 运行测试并保存输出
npm test | tee test-output.txt

# 生成覆盖率报告
npm run test:coverage
\`\`\`

**截图UI**：
- 使用浏览器开发者工具截图
- 确保截图包含关键元素
- 标注重要区域（可选）

---

## 证据质量标准

### 好的证据
✅ 完整：包含所有必需信息
✅ 清晰：Human能看懂
✅ 具体：有文件位置、行号
✅ 可验证：Human可以自己查看

### 不合格的证据
❌ "我检查过了，都存在" - 没有证据
❌ 模糊的描述 - 缺少具体位置
❌ "应该没问题" - 没有实际验证
❌ 截图模糊或不完整

---

## 常见问题

### Q: 证据收集会花很多时间吗？
**A**: 不会。大部分证据是正常工作流程的副产品：
- 搜索代码：设计时本来就要做
- 验证函数：写代码时本来就要查
- 测试截图：运行测试时顺手截图

额外时间：<10分钟/handoff

### Q: 可以省略某些证据吗？
**A**: 不可以。证据要求是"强制"的，因为它们对应历史失败模式。省略证据 = 重蹈覆辙。

### Q: Human不看懂技术证据怎么办？
**A**: 证据设计就是为非技术Human准备的：
- 图表（数据流、状态流）- 直观
- 表格（函数列表）- 清晰
- ✅/❌标记 - 一目了然

---

## 总结

证据收集不是额外负担，而是：
- 设计时的自我检查清单
- 实现时的质量保证
- Human审查的判断依据

**记住**：提供证据 = 避免返工 = 节省时间
