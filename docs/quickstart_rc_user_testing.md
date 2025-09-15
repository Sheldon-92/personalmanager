# RC 用户快速试用指南（5–10 分钟）

> 目的: 快速安装并体验核心价值路径，从用户角度提交反馈。

## 1. 环境准备
- Python: 3.9–3.11（推荐 3.11）
- Shell: bash/zsh
- 可选: Poetry 1.6+

## 2. 获取与安装
```bash
# 克隆项目
git clone <repository-url>
cd personal-manager

# 推荐（Poetry 环境）
poetry install

# 备用（无需全局安装）：使用项目启动器
chmod +x ./bin/pm-local
```

## 3. 5 分钟体验路径
- 版本信息: `./bin/pm-local --version`
- 今日推荐: `./bin/pm-local today`
- 项目概览: `./bin/pm-local projects overview`
- 捕获任务: `./bin/pm-local capture "准备下周的项目汇报"`
- 理清任务: `./bin/pm-local clarify`

期望: 命令均在 2s 内返回，推荐列表与概览可用。

## 4. API v1.0 体验（可选）
```bash
# 本地 API 服务器（只读）
python3 src/pm/api/server.py --port 8001 &

# 健康检查
curl -s http://localhost:8001/health | jq .
# 系统状态
curl -s http://localhost:8001/api/v1/status | jq .
# 任务与项目
curl -s http://localhost:8001/api/v1/tasks | jq .
curl -s http://localhost:8001/api/v1/projects | jq .
```

## 5. 监控与报告（可选）
- 文件监控: `./bin/pm-local monitor start`
- 报告更新: `./bin/pm-local report update`

## 6. 常见问题
- 首次使用提示未初始化: 执行 `poetry run pm setup` 或通过 `pm-local` 引导
- 无网络/代理限制: 可参考 `docs/reports/phase_5/offline_install_validation.md`

## 7. 提交反馈
- 使用模板 `docs/USER_FEEDBACK_TEMPLATE.md`
- 建议附带：命令行输出片段、使用场景、价值评价（1–5）
