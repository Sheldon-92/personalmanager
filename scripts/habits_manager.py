#!/usr/bin/env python3
"""
习惯管理便捷脚本

提供习惯管理的快捷命令，包括同步、查看统计等
"""

import sys
import os
import argparse
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def sync_habits_to_tasks(mode='today'):
    """同步习惯到Google Tasks"""
    script_path = os.path.join(os.path.dirname(__file__), 'sync_habits_to_tasks.py')
    cmd = f"python3 {script_path} --mode {mode}"
    os.system(cmd)

def sync_habits_to_obsidian():
    """同步习惯追踪到Obsidian"""
    script_path = os.path.join(os.path.dirname(__file__), 'sync_habits_to_obsidian.py')
    cmd = f"python3 {script_path}"
    os.system(cmd)

def show_habits_status():
    """显示习惯状态"""
    from pm.cli.commands.habits import show_habit_status
    show_habit_status()

def main():
    parser = argparse.ArgumentParser(description='习惯管理工具')
    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # 同步到Tasks
    sync_tasks_parser = subparsers.add_parser('sync-tasks', help='同步习惯到Google Tasks')
    sync_tasks_parser.add_argument('--mode', choices=['today', 'tomorrow', 'week'],
                                  default='today', help='同步模式')

    # 同步到Obsidian
    subparsers.add_parser('sync-obsidian', help='同步习惯追踪到Obsidian')

    # 显示状态
    subparsers.add_parser('status', help='显示习惯状态')

    # 一键同步所有
    subparsers.add_parser('sync-all', help='一键同步所有')

    args = parser.parse_args()

    if args.command == 'sync-tasks':
        print(f"🔄 同步习惯到Google Tasks ({args.mode})...")
        sync_habits_to_tasks(args.mode)
        print("✅ 同步完成")

    elif args.command == 'sync-obsidian':
        print("🔄 同步习惯追踪到Obsidian...")
        sync_habits_to_obsidian()
        print("✅ 同步完成")

    elif args.command == 'status':
        print("📊 习惯状态:")
        show_habits_status()

    elif args.command == 'sync-all':
        print("🔄 一键同步所有习惯数据...")
        sync_habits_to_tasks('today')
        sync_habits_to_obsidian()
        print("✅ 全部同步完成")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()