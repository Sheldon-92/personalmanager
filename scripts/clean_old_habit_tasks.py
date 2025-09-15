#!/usr/bin/env python3
"""
清理Google Tasks中的旧习惯任务

删除不再需要的旧习惯任务，只保留当前的三个新习惯
"""

import sys
import os
from datetime import datetime
from typing import List, Dict, Any

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from pm.integrations.google_auth import GoogleAuthManager
from pm.core.config import PMConfig
import structlog
import requests

logger = structlog.get_logger()


class HabitTaskCleaner:
    """习惯任务清理器"""

    def __init__(self):
        self.config = PMConfig()
        self.auth_manager = GoogleAuthManager(self.config)

        # 当前有效的习惯名称
        self.current_habits = [
            "早上吃维生素",
            "有氧运动15分钟",
            "睡前阅读5分钟"
        ]

        # 要删除的旧习惯名称
        self.old_habits = [
            "早起开电脑",
            "查看TWL进展"
        ]

    def get_task_lists(self) -> List[Dict[str, Any]]:
        """获取Google Tasks列表"""
        if not self.auth_manager.is_google_authenticated():
            raise Exception("未通过Google认证")

        token = self.auth_manager.get_google_token()
        if not token or token.is_expired:
            raise Exception("Google认证已过期")

        api_url = 'https://www.googleapis.com/tasks/v1/users/@me/lists'
        headers = {
            'Authorization': token.authorization_header,
            'Accept': 'application/json'
        }

        response = requests.get(api_url, headers=headers)
        if response.status_code != 200:
            raise Exception(f"获取任务列表失败: {response.status_code}")

        data = response.json()
        return data.get('items', [])

    def get_tasks(self, list_id: str) -> List[Dict[str, Any]]:
        """获取指定列表的任务"""
        if not self.auth_manager.is_google_authenticated():
            raise Exception("未通过Google认证")

        token = self.auth_manager.get_google_token()
        if not token or token.is_expired:
            raise Exception("Google认证已过期")

        api_url = f'https://www.googleapis.com/tasks/v1/lists/{list_id}/tasks'
        headers = {
            'Authorization': token.authorization_header,
            'Accept': 'application/json'
        }

        response = requests.get(api_url, headers=headers)
        if response.status_code != 200:
            raise Exception(f"获取任务失败: {response.status_code}")

        data = response.json()
        return data.get('items', [])

    def delete_task(self, list_id: str, task_id: str) -> bool:
        """删除指定任务"""
        if not self.auth_manager.is_google_authenticated():
            raise Exception("未通过Google认证")

        token = self.auth_manager.get_google_token()
        if not token or token.is_expired:
            raise Exception("Google认证已过期")

        api_url = f'https://www.googleapis.com/tasks/v1/lists/{list_id}/tasks/{task_id}'
        headers = {
            'Authorization': token.authorization_header,
            'Accept': 'application/json'
        }

        response = requests.delete(api_url, headers=headers)
        return response.status_code == 204

    def is_old_habit_task(self, task: Dict[str, Any]) -> bool:
        """判断是否为旧习惯任务"""
        title = task.get('title', '')

        # 检查是否包含旧习惯名称
        for old_habit in self.old_habits:
            if old_habit in title:
                return True

        return False

    def clean_old_habit_tasks(self) -> Dict[str, Any]:
        """清理旧习惯任务"""
        try:
            logger.info("开始清理旧习惯任务")

            # 获取任务列表
            task_lists = self.get_task_lists()
            if not task_lists:
                return {"success": False, "error": "没有找到任务列表"}

            # 使用第一个列表
            list_id = task_lists[0]['id']
            list_name = task_lists[0].get('title', 'Unknown')

            logger.info(f"检查任务列表: {list_name}")

            # 获取所有任务
            tasks = self.get_tasks(list_id)

            deleted_count = 0
            deleted_tasks = []
            errors = []

            for task in tasks:
                if self.is_old_habit_task(task):
                    try:
                        task_title = task.get('title', '')
                        task_id = task.get('id', '')

                        success = self.delete_task(list_id, task_id)
                        if success:
                            deleted_count += 1
                            deleted_tasks.append(task_title)
                            logger.info(f"✅ 删除旧习惯任务: {task_title}")
                        else:
                            errors.append(f"删除失败: {task_title}")

                    except Exception as e:
                        error_msg = f"删除任务 '{task.get('title', '')}' 时出错: {str(e)}"
                        errors.append(error_msg)
                        logger.error(error_msg)

            result = {
                "success": True,
                "deleted_count": deleted_count,
                "deleted_tasks": deleted_tasks,
                "total_tasks_checked": len(tasks)
            }

            if errors:
                result["errors"] = errors

            logger.info(f"清理完成: 删除了 {deleted_count} 个旧习惯任务")
            return result

        except Exception as e:
            logger.error(f"清理旧习惯任务失败: {e}")
            return {"success": False, "error": str(e)}


def main():
    """主函数"""
    try:
        cleaner = HabitTaskCleaner()
        result = cleaner.clean_old_habit_tasks()

        if result["success"]:
            print(f"✅ 清理完成!")
            print(f"   检查任务总数: {result['total_tasks_checked']}")
            print(f"   删除旧习惯任务: {result['deleted_count']}")

            if result.get('deleted_tasks'):
                print("   删除的任务:")
                for task in result['deleted_tasks']:
                    print(f"   - {task}")

            if result.get('errors'):
                print("⚠️  部分错误:")
                for error in result['errors']:
                    print(f"   - {error}")

            return 0
        else:
            print(f"❌ 清理失败: {result.get('error', '未知错误')}")
            return 1

    except Exception as e:
        print(f"❌ 清理过程出错: {e}")
        return 1


if __name__ == "__main__":
    exit(main())