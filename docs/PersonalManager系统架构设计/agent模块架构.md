# 🤖 Agent模块架构

## Agent 角色矩阵

| Agent 名称 | 主要职责 | 输入数据 | 输出数据 | 依赖关系 |
|------------|----------|----------|----------|----------|
| **pm-orchestrator** | 总控协调、用户交互 | 用户命令、CLI输入 | 格式化响应、状态更新 | 所有下级Agent |
| **project-manager** | 项目生命周期管理 | PROJECT_STATUS.md报告、项目文件夹 | 项目状态、跨项目分析 | status-analyzer |
| **priority-engine** | 项目优先级计算 | 项目状态报告、用户目标 | 项目优先级排序、时间分配建议 | insight-engine |
| **goal-tracker** | 目标设定和追踪 | 目标定义、进度数据 | 达成分析、调整建议 | schedule-manager |
| **decision-support** | 智能决策支持 | 选择场景、历史数据 | 决策建议、风险分析 | automation-manager |
| **status-analyzer** | PROJECT_STATUS.md报告解析 | AI生成的项目报告 | 结构化状态数据、趋势分析 | 无 |
| **insight-engine** | 智慧洞见生成 | 19本书算法、用户数据 | 个性化建议、模式识别 | 无 |
| **schedule-manager** | 日程和时间管理 | Calendar数据、任务列表 | 时间分配、冲突检测 | Google APIs |
| **automation-manager** | AI工具集成与文件监控 | 文件变化事件、AI工具接口 | 报告更新通知、集成状态 | AI APIs/FileSystem |

## 详细 Agent 设计

### 1. pm-orchestrator (总控Agent)

```yaml
name: pm-orchestrator
role: master-coordinator
persona: |
  我是PersonalManager的总控协调者，负责理解用户意图，
  协调各专业Agent，并提供统一的响应界面。
  我精通自然语言理解和工作流协调。

commands:
  - name: analyze-situation
    description: 分析当前项目和任务状况
    triggers: ["/pm 分析当前状况", "/pm 项目概览"]
    
  - name: priority-advice
    description: 提供优先级建议
    triggers: ["/pm 今天做什么", "/pm 优先级建议"]
    
  - name: goal-review
    description: 目标回顾和进度分析
    triggers: ["/pm 目标进度", "/pm 回顾目标"]

dependencies:
  - project-manager
  - priority-engine
  - goal-tracker
  - decision-support

workflow:
  1. 解析用户输入和意图
  2. 识别需要调用的专业Agent
  3. 协调Agent间的数据流
  4. 整合响应并格式化输出
  5. 更新系统状态和学习数据
```

### 2. priority-engine (优先级引擎Agent)

```yaml
name: priority-engine
role: priority-calculator
persona: |
  我是优先级计算的专家，基于多维度算法为任务和项目
  计算动态优先级。我整合了时间管理、决策心理学和
  效率优化的最佳实践。

algorithms:
  eisenhower_matrix:
    urgent_important: weight=1.0
    important_not_urgent: weight=0.8
    urgent_not_important: weight=0.6
    neither: weight=0.2
    
  time_decay:
    formula: "priority * (1 - decay_rate * days_elapsed)"
    decay_rate: 0.05
    
  completion_bonus:
    near_completion: multiplier=1.2
    started: multiplier=1.1
    blocked: multiplier=0.5

data_sources:
  - task_definitions
  - deadline_constraints
  - historical_completion_data
  - user_energy_patterns
  - external_commitments

output_format:
  priority_score: float(0.0-1.0)
  reasoning: string
  recommended_action: enum[start, continue, defer, delegate]
  optimal_time_slot: datetime_range
```

### 3. project-manager (项目管理Agent)

```yaml
name: project-manager
role: project-lifecycle-manager
persona: |
  我是项目管理专家，负责跟踪多类型项目生命周期，
  基于AI生成的PROJECT_STATUS.md报告监控进度，
  识别风险，并提供项目健康度分析。

project_types:
  - code: 编程开发项目
  - design: 设计创作项目  
  - video: 视频制作项目
  - research: 研究学习项目
  - art: 艺术创作项目
  - general: 通用项目类型

health_indicators:
  report_freshness: "状态报告更新频率"
  progress_velocity: "进度推进速度"
  issue_resolution: "问题解决效率"
  ai_tool_utilization: "AI工具使用情况"
  
risk_detection:
  - stalled_progress: 项目进度长期无变化
  - missing_reports: 缺少PROJECT_STATUS.md报告
  - critical_health_status: 项目健康状态为critical
  - overdue_deliverables: 交付物超期风险

integration_points:
  - status-analyzer: 解析PROJECT_STATUS.md报告
  - automation-manager: 监控报告文件变化
  - AI工具APIs: 触发报告生成和更新
  - FileSystem: 检测项目文件夹结构变化
```

### 4. goal-tracker (目标追踪Agent)

```yaml
name: goal-tracker
role: goal-achievement-monitor
persona: |
  我是目标追踪专家，帮助设定SMART目标，
  监控进度，并提供达成策略建议。

goal_types:
  project_goals: 项目完成目标
  skill_goals: 技能提升目标
  habit_goals: 习惯养成目标
  health_goals: 健康生活目标

tracking_metrics:
  completion_rate: 完成率
  consistency_score: 一致性分数
  trend_analysis: 趋势分析
  milestone_achievement: 里程碑达成

adjustment_strategies:
  behind_schedule:
    - 分解任务粒度
    - 调整时间分配
    - 降低标准或延期
  ahead_schedule:
    - 提高目标标准
    - 增加挑战性
    - 设定延伸目标

reporting_format:
  weekly_review: 周度目标回顾
  monthly_assessment: 月度达成评估
  quarterly_planning: 季度目标规划
```

### 5. decision-support (决策支持Agent)

```yaml
name: decision-support
role: intelligent-decision-advisor
persona: |
  我是决策支持专家，基于认知心理学和决策理论，
  帮助用户做出更好的选择和判断。

decision_frameworks:
  - eisenhower_matrix: 重要性-紧急性矩阵
  - cost_benefit_analysis: 成本收益分析
  - pros_cons_weighting: 优缺点权重分析
  - risk_assessment: 风险评估模型

cognitive_bias_detection:
  - confirmation_bias: 确认偏误检测
  - anchoring_bias: 锚定效应识别  
  - availability_heuristic: 可得性启发式
  - sunk_cost_fallacy: 沉没成本谬误

recommendation_engine:
  input_factors: [options, constraints, goals, preferences]
  output_format: 
    primary_recommendation: string
    confidence_level: float
    reasoning: array<string>
    alternatives: array<option>
    risk_factors: array<risk>
```

### 6. status-analyzer (状态分析Agent)

```yaml
name: status-analyzer  
role: project-report-parser
persona: |
  我是PROJECT_STATUS.md报告解析专家，负责解析AI工具
  生成的项目状态报告，提取结构化数据，并进行智能分析。

parsing_capabilities:
  yaml_frontmatter:
    - project_metadata: 项目元数据解析
    - progress_indicators: 进度指标提取
    - health_status: 健康状态识别
    - timeline_information: 时间线信息
    
  markdown_content:
    - completed_work_extraction: 已完成工作提取
    - next_actions_identification: 下一步行动识别
    - issue_detection: 问题和风险检测
    - time_planning_analysis: 时间规划分析
    
  ai_tool_compatibility:
    - claude_format: Claude Code生成的报告
    - gemini_format: Gemini生成的报告  
    - cortex_format: Cortex生成的报告
    - manual_format: 手动编辑的报告

health_scoring:
  excellent: 进度>80% AND 健康状态=excellent
  good: 进度>60% AND 健康状态=good
  warning: 进度<60% OR 健康状态=warning  
  critical: 健康状态=critical OR 长期无更新

alert_conditions:
  - report_missing: 项目缺少PROJECT_STATUS.md
  - report_outdated: 报告超过7天未更新
  - critical_status: 健康状态标记为critical
  - progress_stalled: 进度长期无变化
```

### 7. habit-tracker (习惯跟踪Agent)

```yaml
name: habit-tracker
role: behavior-pattern-monitor
persona: |
  我是习惯养成专家，基于行为科学理论，
  帮助建立和维护良好的工作和生活习惯。

habit_categories:
  work_habits: 工作习惯
  health_habits: 健康习惯  
  learning_habits: 学习习惯
  productivity_habits: 效率习惯

tracking_metrics:
  streak_counting: 连续执行天数
  consistency_rate: 一致性比率
  habit_strength: 习惯强度评分
  context_analysis: 执行环境分析

formation_strategies:
  habit_stacking: 习惯叠加法
  tiny_habits: 微习惯策略
  environmental_design: 环境设计
  reward_systems: 奖励机制

analytics:
  best_time_patterns: 最佳执行时间模式
  success_factors: 成功影响因子
  failure_analysis: 失败原因分析
  personalized_recommendations: 个性化建议
```

### 8. automation-manager (自动化管理Agent)

```yaml
name: automation-manager
role: ai-tool-integration-coordinator
persona: |
  我是AI工具集成专家，负责管理Claude Code、Gemini、
  Cortex等AI工具的接口调用，以及PROJECT_STATUS.md
  文件的自动化监控和更新触发。

supported_ai_tools:
  claude_code:
    - report_generation: PROJECT_STATUS.md报告生成
    - code_analysis: 代码项目分析
    - status_update: 状态自动更新
    
  gemini:
    - multi_modal_analysis: 多模态项目分析
    - creative_project_support: 创意项目支持
    - research_assistance: 研究项目辅助
    
  cortex:
    - workflow_automation: 工作流自动化
    - intelligent_scheduling: 智能调度
    - cross_project_insights: 跨项目洞察

file_monitoring:
  project_folder_scanning: 项目文件夹扫描
  status_report_tracking: 状态报告跟踪
  real_time_updates: 实时更新通知
  missing_report_detection: 缺失报告检测

automation_triggers:
  schedule_based: 定时触发报告更新
  file_change_based: 文件变化触发分析
  user_request_based: 用户请求触发
  health_check_based: 健康检查触发

error_handling:
  ai_api_failures: AI API调用失败处理
  file_access_issues: 文件访问问题处理
  report_parsing_errors: 报告解析错误处理
  integration_conflicts: 集成冲突解决
  data_consistency_check: 数据一致性检查
```

---
