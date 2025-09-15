#!/bin/bash
# PersonalManager 交互模式启动脚本

echo "🚀 启动PersonalManager交互模式..."
cd "$(dirname "$0")"
PYTHONPATH=src python3 -m pm.cli.main interactive