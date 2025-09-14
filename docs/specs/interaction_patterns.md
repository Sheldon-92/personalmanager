# 意图路由与命令映射规范（规划）

> 目标：让自然语言成为一等入口，路由到本地 `pm` 命令执行，支持槽位解析、置信度与确认文案，多语言短语库。

## 文件位置
- 项目根目录：`.personalmanager/interaction-patterns.json`

## JSON 结构（草案）
```json
{
  "version": "1.0",
  "locale": ["zh", "en"],
  "intents": [
    {
      "id": "today",
      "description": "获取今日重点推荐",
      "phrases": ["今天做什么", "今日重点", "what should i do today"],
      "pattern": null,
      "command": "pm today",
      "args_schema": {"count": {"type": "int", "default": 3}},
      "confirm": {"low_confidence": "将执行 'pm today'，确定吗？"}
    },
    {
      "id": "capture",
      "description": "记录/捕获任务",
      "phrases": ["记录", "记一下", "capture", "add task"],
      "pattern": "^(?:记录|记一下|capture|add task)[:：]\s*(?<content>.+)$",
      "command": "pm capture \"{content}\"",
      "args_schema": {"content": {"type": "string", "required": true}},
      "confirm": {"low_confidence": "将记录任务：{content}，确定吗？"}
    },
    {
      "id": "projects_overview",
      "description": "项目状态总览",
      "phrases": ["项目概览", "项目状态", "overview projects"],
      "pattern": null,
      "command": "pm projects overview",
      "args_schema": {},
      "confirm": {"low_confidence": "将查看项目概览，确定吗？"}
    },
    {
      "id": "project_status",
      "description": "单个项目状态",
      "phrases": ["X 项目进展", "X 项目状态", "status of X"],
      "pattern": "^(?<name>.+?)\s*(项目)?\s*(?:进展|状态|status)$",
      "command": "pm project status \"{name}\"",
      "args_schema": {"name": {"type": "string", "required": true}},
      "confirm": {"low_confidence": "将查看项目：{name}，确定吗？"}
    },
    {
      "id": "explain",
      "description": "解释推荐原因",
      "phrases": ["为什么推荐", "explain"],
      "pattern": "^(?:为什么推荐|explain)\s*(?<id>[\
\\w-]+)$",
      "command": "pm explain {id}",
      "args_schema": {"id": {"type": "string", "required": true}},
      "confirm": {"low_confidence": "将解释推荐：{id}，确定吗？"}
    }
  ]
}
```

## CLI 协议（规划）
- `pm ai route "<utterance>" --json`
  - 输出：`{ intent, confidence, command, args, confirm_message }`
- `pm ai execute "<utterance>" [--auto-confirm]`
  - 行为：路由→低置信度则提示确认→执行→返回结果摘要（结构化）

## 设计原则
- 先短语后正则：通过短语命中优于复杂正则；正则仅做提取槽位。
- 多语言并行：`phrases` 支持中英文，`locale` 控制优先级。
- 可审计：所有路由决策可打印/记录，便于调试与改进。

