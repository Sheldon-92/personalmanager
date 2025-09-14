# 工作空间配置规范（规划）

> 目标：以 BMAD 的“配置驱动”思想，为 PersonalManager 引入项目级 AI 工作空间，使 Agent 具备持久身份、启动仪式与最小上下文。

## 文件位置
- 项目根目录：`.personalmanager/workspace-config.yaml`

## 字段规范（草案）
```yaml
workspace:
  name: my-project               # 工作空间名称
  language: zh                   # zh|en
  timezone: Asia/Shanghai

startup:
  enabled: true
  steps:                         # 会话启动仪式顺序
    - doctor
    - today
  doctor:
    verbose: false
  today:
    count: 3

agents:
  preferred: claude              # claude|gemini
  platforms: [claude, gemini]

privacy:
  external_calls: user_consent   # user_consent|deny_all
  data_retention: session_only   # session_only|local_persist
  redact_logs: true

context:
  always_load: []                # 例：docs/README.md 的轻量片段
  include_project_status: true

routing:
  locale: auto                   # auto|zh|en，意图路由语言优先级
  low_confidence_threshold: 0.5  # 低于该阈值需用户确认
  high_confidence_threshold: 0.8 # 高于该阈值可自动执行（如允许）
```

## 设计原则
- 最小必要：尽量少注入上下文，避免提示臃肿与不确定性。
- 幂等安全：脚手架不覆写（除非 `--force`），校验缺失项。
- 隐私优先：所有记忆与配置本地存储，外部调用需显式同意。

## 与平台文件的关系
- 由 `pm agent prompt` 编译产出：
  - `.claude/project-instructions.md`
  - `~/.gemini/config.json` 片段（仅追加 PM 指令区）

---

## 验收要点（供实现参考）
- 解析/校验：字段类型、枚举与默认值均通过。
- 大小限制：编译后的指令 < 10k 字符。
- 启动仪式：会话开场只做必要动作与提示，不注入大段说明文。
