# PROJECT_STATUS.md 标准规范与模板

> **版本**: v1.0  
> **创建日期**: 2025-09-11  
> **适用范围**: PersonalManager项目管理系统  
> **文档类型**: 技术规范 + 使用模板  
> **目标用户**: AI工具 (Claude Code/Gemini/Cortex) + 手动编辑用户

## 📋 文档概述

PROJECT_STATUS.md是PersonalManager系统的核心数据文件，用于描述单个项目的当前状态、进展情况和未来计划。本文档提供了完整的格式规范、最佳实践和各种项目类型的模板，确保AI工具和用户能够生成和维护高质量的项目状态报告。

## 🎯 设计目标

### 1. 标准化
- 统一的YAML frontmatter格式
- 一致的Markdown章节结构
- 标准化的数据字段和枚举值

### 2. 多工具兼容
- Claude Code原生支持
- Gemini多模态分析
- Cortex工作流自动化
- 人工编辑友好

### 3. 智能解析
- 结构化数据提取
- 语义内容分析
- 自动进度计算
- 趋势识别能力

## 📐 文件格式规范

### 基本结构
```
PROJECT_STATUS.md
├── YAML Front Matter    # 结构化元数据
├── 项目概览            # 必需章节
├── 已完成工作          # 必需章节  
├── 进行中工作          # 可选章节
├── 下一步行动          # 推荐章节
├── 问题和风险          # 可选章节
└── 时间规划            # 可选章节
```

### 文件编码与命名
- **文件名**: `PROJECT_STATUS.md` (固定名称)
- **编码**: UTF-8
- **位置**: 项目根目录 `{project_root}/PROJECT_STATUS.md`
- **换行**: LF (Unix风格)

## 🔧 YAML Front Matter 规范

### 必需字段
```yaml
---
project_name: string          # 项目名称
project_type: enum            # 项目类型 [code/design/video/research/art/general]
current_progress: number      # 当前进度 0-100
health_status: enum           # 健康状态 [excellent/good/warning/critical]
last_updated: datetime        # 最后更新时间 ISO 8601格式
---
```

### 可选字段
```yaml
---
# 时间相关
start_date: date              # 项目开始日期 YYYY-MM-DD
target_completion: date       # 目标完成日期 YYYY-MM-DD
estimated_remaining_time: str # 预估剩余时间 "2 weeks", "3 days"

# AI工具信息
report_source: enum           # claude/gemini/cortex/chatgpt/manual/hybrid
ai_tool_version: string       # AI工具版本信息
generation_timestamp: datetime # 报告生成时间戳

# 项目特定字段 (根据project_type动态添加)
repository_url: url           # 代码项目: Git仓库地址
tech_stack: array[string]     # 代码项目: 技术栈
design_tools: array[string]   # 设计项目: 设计工具
video_length: string          # 视频项目: 目标时长
research_scope: string        # 研究项目: 研究范围
---
```

### 字段值规范

#### project_type枚举值
| 值 | 描述 | 适用场景 |
|---|------|---------|
| `code` | 编程开发项目 | 软件开发、网站建设、API开发 |
| `design` | 设计创作项目 | UI/UX设计、平面设计、品牌设计 |
| `video` | 视频制作项目 | 视频剪辑、动画制作、纪录片 |
| `research` | 研究学习项目 | 学术研究、市场调研、技术调研 |
| `art` | 艺术创作项目 | 绘画、雕塑、音乐创作 |
| `general` | 通用项目 | 其他不明确分类的项目 |

#### health_status枚举值
| 状态 | 描述 | 触发条件 |
|-----|------|----------|
| `excellent` | 优秀状态 | 进度超前，无重大问题 |
| `good` | 良好状态 | 按计划进行，问题可控 |
| `warning` | 需要关注 | 进度滞后或存在风险 |
| `critical` | 需要紧急处理 | 严重阻塞或重大问题 |

## 📝 Markdown 内容规范

### 1. 项目概览 (必需)
```markdown
## 🎯 项目概览

简要描述项目的目标、背景和当前整体状况。建议1-3段话，包含：
- 项目目标和价值
- 当前所处阶段
- 关键里程碑进展
```

### 2. 已完成工作 (必需)
```markdown
## ✅ 已完成工作

使用以下格式之一记录已完成的工作：

### 方式1: 复选框列表
- [x] 完成需求分析文档
- [x] 设计数据库架构
- [x] 实现用户认证模块

### 方式2: 带描述的完成项
✅ **完成需求分析文档**
- 调研了5个同类产品
- 整理了20个核心功能需求
- 完成了用户故事映射

### 方式3: 按时间分组
#### 本周完成 (2025-09-04 - 2025-09-11)
- [x] API接口设计
- [x] 数据库表结构优化
```

### 3. 进行中工作 (可选)
```markdown
## ⏳ 进行中工作

记录当前正在执行的任务，建议包含进度百分比：

- [ ] 前端界面开发 (进度: 60%)
  - 已完成登录页面和主界面
  - 正在开发用户设置页面
  - 预计2天内完成

- [ ] 单元测试编写 (进度: 30%)
  - 完成了核心模块的测试
  - 还需覆盖API层的测试
```

### 4. 下一步行动 (推荐)
```markdown
## 📋 下一步行动

### 🔥 高优先级 (下次必做)
- [ ] 修复登录模块的安全漏洞
- [ ] 完成用户反馈功能的实现

### 📈 中优先级 (本周内完成)  
- [ ] 优化数据库查询性能
- [ ] 编写API文档

### 📝 低优先级 (有时间时处理)
- [ ] 代码重构和注释完善
- [ ] 添加更多的单元测试
```

### 5. 问题和风险 (可选)
```markdown
## ⚠️ 问题和风险

### 当前问题
❌ **数据库连接不稳定**
- 出现频率: 每天2-3次
- 影响范围: 用户登录和数据保存
- 临时解决方案: 增加了连接重试机制

### 潜在风险
🔶 **第三方API限制**
- 风险等级: 中等
- 可能影响: 可能导致功能受限
- 缓解策略: 寻找备用API服务商

### 已解决问题
✅ **前端兼容性问题** (已解决 - 2025-09-10)
- 修复了Safari浏览器的显示异常
- 更新了CSS兼容性代码
```

### 6. 时间规划 (可选)
```markdown
## 📅 时间规划

### 本周重点 (2025-09-11 - 2025-09-18)
- 周一-周二: 完成用户模块开发
- 周三-周四: 进行集成测试
- 周五: 代码审查和文档更新

### 里程碑计划
📍 **Beta版本发布** (目标: 2025-09-25)
- 核心功能开发完成
- 基础测试通过
- 用户界面优化

📍 **正式版本发布** (目标: 2025-10-15) 
- 全功能测试完成
- 性能优化
- 用户文档完善
```

## 📊 项目类型专用模板

### 代码项目模板
```markdown
---
project_name: "个人博客网站"
project_type: "code"
current_progress: 65
health_status: "good"
last_updated: "2025-09-11T14:30:00Z"
start_date: "2025-08-15"
target_completion: "2025-10-01"
estimated_remaining_time: "3 weeks"
report_source: "claude"
repository_url: "https://github.com/username/blog"
tech_stack: ["React", "Node.js", "MongoDB", "Express"]
deployment_status: "staging"
test_coverage: 78
---

# 📊 项目状态报告 - 个人博客网站

## 🎯 项目概览
基于React和Node.js的个人博客网站，支持文章发布、评论系统和用户管理。目前已完成核心功能开发，正在进行界面优化和测试。

## ✅ 已完成工作
- [x] React前端框架搭建
- [x] Node.js后端API开发
- [x] MongoDB数据库设计
- [x] 用户认证系统
- [x] 文章CRUD功能
- [x] 响应式界面设计

## ⏳ 进行中工作
- [ ] 评论系统开发 (进度: 40%)
- [ ] SEO优化实现 (进度: 20%)
- [ ] 单元测试编写 (进度: 78%)

## 📋 下一步行动
### 🔥 高优先级
- [ ] 完成评论系统后端API
- [ ] 实现文章搜索功能

### 📈 中优先级  
- [ ] 添加图片上传功能
- [ ] 优化页面加载速度

## ⚠️ 问题和风险
❌ **部署环境配置复杂**
- 需要配置SSL证书和域名解析
- 计划使用Docker简化部署流程

## 📅 时间规划
### 本周重点
- 完成评论系统开发
- 进行全面功能测试

### 里程碑
📍 **Beta版上线** (2025-09-25)
📍 **正式发布** (2025-10-01)
```

### 设计项目模板
```markdown
---
project_name: "品牌视觉识别系统"
project_type: "design"
current_progress: 45
health_status: "good"
last_updated: "2025-09-11T16:20:00Z"
start_date: "2025-08-20"
target_completion: "2025-10-15"
estimated_remaining_time: "5 weeks"
report_source: "gemini"
design_tools: ["Figma", "Adobe Illustrator", "Photoshop"]
design_system: "Material Design"
client_feedback_status: "pending_review"
revision_count: 2
---

# 📊 项目状态报告 - 品牌视觉识别系统

## 🎯 项目概览
为科技创业公司设计完整的品牌视觉识别系统，包括LOGO、色彩搭配、字体规范和应用规范。目前完成了LOGO设计和基础色彩系统。

## ✅ 已完成工作
- [x] 品牌调研和竞品分析
- [x] LOGO概念设计 (3个方案)
- [x] 主色调确定 (#2563EB, #F59E0B)
- [x] 字体系统选择 (Inter + Noto Sans)
- [x] LOGO最终方案确认

## ⏳ 进行中工作
- [ ] 应用系统设计 (进度: 30%)
  - 名片设计已完成
  - 正在设计PPT模板
- [ ] 品牌指导手册编写 (进度: 25%)

## 📋 下一步行动
### 🔥 高优先级
- [ ] 完成网站界面设计稿
- [ ] 提交客户第二轮审查

### 📈 中优先级
- [ ] 设计宣传册版式
- [ ] 制作品牌应用展示

## ⚠️ 问题和风险
🔶 **客户反馈周期较长**
- 影响项目时间进度
- 建议设置明确的反馈时限

## 📅 时间规划
### 本周重点
- 完成所有应用系统设计
- 整理完整设计稿包

### 里程碑
📍 **设计初稿完成** (2025-09-20)
📍 **客户最终确认** (2025-10-01) 
📍 **交付完整VI手册** (2025-10-15)
```

### 研究项目模板
```markdown
---
project_name: "人工智能在教育中的应用研究"
project_type: "research"
current_progress: 30
health_status: "good"
last_updated: "2025-09-11T11:45:00Z"
start_date: "2025-09-01"
target_completion: "2025-12-15"
estimated_remaining_time: "3 months"
report_source: "claude"
research_scope: "K-12教育AI应用案例分析"
research_methods: ["文献综述", "案例研究", "专家访谈"]
target_publication: "教育技术学报"
---

# 📊 项目状态报告 - 人工智能在教育中的应用研究

## 🎯 项目概览
系统研究人工智能技术在K-12教育中的应用现状、效果和发展趋势，为教育政策制定和技术应用提供理论支撑和实践指导。

## ✅ 已完成工作
- [x] 文献调研 (已阅读87篇相关论文)
- [x] 研究框架设计
- [x] 数据收集方案制定
- [x] 伦理审查申请提交
- [x] 专家访谈提纲设计

## ⏳ 进行中工作
- [ ] 案例学校实地调研 (进度: 40%)
  - 已完成3所学校的访谈
  - 还需完成7所学校调研
- [ ] 数据整理和编码 (进度: 25%)

## 📋 下一步行动
### 🔥 高优先级
- [ ] 完成剩余学校的实地调研
- [ ] 开始定量数据分析

### 📈 中优先级
- [ ] 撰写文献综述章节
- [ ] 准备中期进展报告

## ⚠️ 问题和风险
❌ **部分学校访谈安排困难**
- 学校教学安排紧张，时间协调困难
- 解决方案: 提供线上访谈选项

🔶 **数据分析工具学习成本高**
- 需要掌握NVIVO和SPSS软件
- 计划参加相关培训课程

## 📅 时间规划
### 本月重点 (九月)
- 完成所有实地调研
- 完成数据收集工作

### 里程碑
📍 **调研阶段完成** (2025-09-30)
📍 **数据分析完成** (2025-10-31)
📍 **初稿撰写完成** (2025-11-30)
📍 **论文投稿** (2025-12-15)
```

## 🔍 质量检查清单

### AI工具生成报告检查
- [ ] YAML frontmatter格式正确
- [ ] 必需字段全部存在
- [ ] 枚举值使用正确
- [ ] 进度数字合理 (0-100)
- [ ] 日期格式符合ISO 8601
- [ ] 必需章节完整
- [ ] Markdown语法正确
- [ ] 内容逻辑连贯

### 人工编辑检查
- [ ] 项目信息准确无误
- [ ] 进度描述与实际情况匹配
- [ ] 风险和问题识别完整
- [ ] 下一步行动具体可执行
- [ ] 时间规划现实可行
- [ ] 语言表达清晰专业

## 📈 最佳实践

### 1. 更新频率
- **活跃项目**: 每周更新1-2次
- **稳定项目**: 每2周更新一次
- **维护项目**: 每月更新一次
- **紧急情况**: 随时更新

### 2. 内容写作
- 使用具体数字而不是模糊描述
- 包含可衡量的进度指标
- 记录具体的完成时间
- 描述具体的问题和解决方案

### 3. AI工具优化
- 为AI工具提供充分的项目上下文
- 使用清晰的项目目录结构
- 保持文件命名规范
- 定期验证AI生成的内容准确性

### 4. 版本控制
- 将PROJECT_STATUS.md纳入版本控制
- 记录重要的状态变更
- 保留历史版本以便追溯
- 避免频繁的无意义更新

## 🛠️ 工具集成

### Claude Code集成
```bash
# 生成项目状态报告
/pm generate-status-report --project-type code --include-analysis

# 更新现有报告
/pm update-status-report --mode incremental
```

### Gemini集成
```python
# 多模态项目分析
gemini.analyze_project_with_visuals(
    project_path="/path/to/project",
    include_images=True,
    output_format="project_status_md"
)
```

### Cortex工作流
```yaml
workflow:
  name: "auto-status-update"
  schedule: "0 9 * * 1"  # 每周一早上9点
  actions:
    - generate_project_reports
    - notify_stakeholders
```

## 📚 参考资源

- [YAML 1.2 规范](https://yaml.org/spec/1.2/spec.html)
- [Markdown CommonMark规范](https://commonmark.org/)
- [ISO 8601日期时间格式](https://www.iso.org/iso-8601-date-and-time-format.html)
- [PersonalManager数据模型设计](./PersonalManager数据模型设计.md)
- [外部系统集成技术规范](./外部系统集成技术规范.md)

---

**文档维护**: 本规范随PersonalManager系统演进而更新，版本变更请参考系统发布说明。