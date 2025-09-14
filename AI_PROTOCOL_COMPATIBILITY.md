# AI协议变更与兼容性说明

## 新协议结构定义

当前PersonalManager AI命令采用标准化的JSON响应格式：

```typescript
interface AIResponse {
  status: "success" | "failed" | "error";
  command: string;       // 命令标识符，如 "ai.route", "ai.config", "ai.status"
  data: any | null;      // 成功时的返回数据
  error?: {
    code: string;        // 错误码枚举
    message: string;     // 用户友好的错误信息
    details?: any;       // 额外的错误上下文
  };
  metadata: {
    version: string;     // API版本
    execution_time: number; // 执行时间（秒）
  };
}
```

## 错误码枚举

- `INTERNAL_ERROR`: 内部处理错误
- `API_KEY_NOT_CONFIGURED`: API密钥未配置
- `SERVICE_UNAVAILABLE`: 服务不可用
- `INVALID_REQUEST`: 无效请求参数
- `RATE_LIMIT_EXCEEDED`: 超过速率限制
- `NOT_IMPLEMENTED`: 功能未实现

## 与旧版本的差异

### Sprint 2原型 → Sprint 3正式版

| 字段 | Sprint 2 | Sprint 3 | 变更说明 |
|------|----------|----------|----------|
| args | `{"count": 3}` | - | **已移除**，参数通过details传递 |
| status | - | `"success"/"failed"/"error"` | **新增**，标准化状态码 |
| data | - | `any | null` | **新增**，成功响应数据 |
| error | 简单字符串 | 结构化对象 | **改进**，包含code/message/details |
| metadata | - | 版本和性能信息 | **新增**，调试和监控信息 |

## AI子命令帮助文档

### pm ai config --help
```bash
$ ./bin/pm-local ai config --help
[INFO] Using Poetry environment (poetry run pm)

Usage: pm ai config [OPTIONS] [SET_KEY]

  配置AI服务

  Examples:
      pm ai config                    # 显示当前配置
      pm ai config claude.api_key=xxx # 设置Claude API密钥
      pm ai config --list             # 列出所有配置项

╭─ Arguments ──────────────────────────────────────────────────────────────────╮
│   set_key      [SET_KEY]  设置配置项 (格式: key=value)                      │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --list        -l        列出所有可用配置项                                   │
│ --json                  JSON格式输出                                         │
│ --help                  Show this message and exit.                          │
╰──────────────────────────────────────────────────────────────────────────────╯
```

### pm ai status --help
```bash
$ ./bin/pm-local ai status --help
[INFO] Using Poetry environment (poetry run pm)

Usage: pm ai status [OPTIONS]

  显示AI服务状态

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --json        JSON格式输出                                                   │
│ --help        Show this message and exit.                                    │
╰──────────────────────────────────────────────────────────────────────────────╯
```

### pm ai route --help
```bash
$ ./bin/pm-local ai route --help
[INFO] Using Poetry environment (poetry run pm)

Usage: pm ai route [OPTIONS] QUERY

  AI路由 - 自然语言转命令

  Examples:
      pm ai route "今天有什么任务"
      pm ai route "创建一个新习惯" --service gemini
      pm ai route "查看项目状态" --json

╭─ Arguments ──────────────────────────────────────────────────────────────────╮
│ *    query      TEXT  自然语言查询 [required]                                │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --service        -s      TEXT  AI服务 (claude/gemini) [default: claude]     │
│ --json                         JSON格式输出                                  │
│ --help                         Show this message and exit.                   │
╰──────────────────────────────────────────────────────────────────────────────╯
```

## 实际输出示例

### 成功响应（理论）
```json
{
  "status": "success",
  "command": "ai.route",
  "data": {
    "intent": "get_today_tasks",
    "confidence": 0.95,
    "suggested_command": "pm today",
    "parameters": []
  },
  "error": null,
  "metadata": {
    "version": "0.1.0",
    "execution_time": 0.234
  }
}
```

### 错误响应（实际）
```json
{
  "status": "failed",
  "command": "ai.route",
  "error": {
    "code": "API_KEY_NOT_CONFIGURED",
    "message": "Claude API key not configured. Please set PM_CLAUDE_API_KEY environment variable or run: pm ai config claude.api_key=<your-key>",
    "details": {
      "service": "claude",
      "query": "今天做什么"
    }
  },
  "data": null,
  "metadata": {
    "version": "0.1.0",
    "execution_time": 0.001
  }
}
```

## 文档统一状态

✅ **已完成统一**：
- 所有Sprint 3文档使用新协议格式
- Sprint 2历史文档保留并标注"已废弃"
- 技术规范文档包含完整协议定义
- 用户指南将在Phase 2更新

## 向后兼容性

- **破坏性变更**：移除了`args`字段
- **迁移路径**：参数现通过`data`或`error.details`传递
- **版本标识**：通过`metadata.version`字段识别协议版本
- **降级支持**：错误时提供手动执行命令的fallback指引