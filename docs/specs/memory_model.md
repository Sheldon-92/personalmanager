# 记忆与偏好模型（规划）

> 目标：将用户行为、偏好与决策以事件化的方式本地持久化，并定期生成“画像摘要”，在不牺牲隐私的前提下提升个性化体验。

## 存储位置
- 事件日志：`~/.personalmanager/data/memory/events.jsonl`
- 画像摘要：`~/.personalmanager/data/memory/profile.md`

## 事件结构（示例）
```json
{
  "ts": "2025-09-15T08:31:00+08:00",
  "type": "recommendation_view|task_capture|task_complete|clarify_session|deepwork_session|habit_track",
  "payload": {"task_id": "abc", "content": "准备周报", "score": 0.87},
  "source": "cli|agent|router",
  "meta": {"workspace": "my-project"}
}
```

## 摘要生成（示意）
```text
profile.md（每日至少一次/每周归档）
- 偏好倾向：上午处理高投入任务；偏好 @电脑 情境
- 近期完成：本周完成 12 项任务；两次深度工作 ≥ 60 分钟
- 常用命令：today、capture、projects overview
- 待改进：Clarify 频次不足；下午分心次数偏高
```

## 读取路径
- Prompt 编译时注入 3–5 行摘要（不包含敏感数据）。
- 推荐引擎读取事件/摘要，调整因子权重与解释文案。

## 隐私与合规
- 本地优先：不上传；用户可一键清除。
- 脱敏日志：默认不记录原始正文（如邮件内容），仅记录类型/标签。
- 显式授权：任何外部发送需用户确认。

## 验收要点
- 写入可恢复：异常中断不破坏日志；追加写。
- 摘要可控：大小上限与信息级别可配置。
- 与推荐联动：今日推荐能体现个性化依据。
