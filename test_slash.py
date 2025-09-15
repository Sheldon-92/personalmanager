#!/usr/bin/env python3
"""简化的斜杠命令测试"""

import sys
import os
sys.path.insert(0, 'src')

from pm.core.interaction_manager import InteractionManager
from pm.core.command_executor import CommandExecutor
from pm.core.config import PMConfig

def test_slash_commands():
    """测试斜杠命令功能"""

    print("🔧 初始化PersonalManager...")
    config = PMConfig()
    manager = InteractionManager(config)
    executor = CommandExecutor()

    print("\n📋 可用的斜杠命令:")
    help_text = manager.format_slash_help()
    print(help_text)

    print("\n🧪 测试斜杠命令执行:")

    # 测试基本斜杠命令
    test_commands = ["/", "/pm", "/gmail"]

    for cmd in test_commands:
        print(f"\n➤ 测试: {cmd}")

        # 解析输入
        result = manager.process_user_input(cmd)
        print(f"   解析结果: {result['type']}")

        if result['type'] == 'slash_command':
            if cmd == '/':
                print("   📋 显示帮助菜单")
            else:
                print(f"   🔄 执行命令: {cmd}")
                exec_result = executor.execute_slash_command(cmd)
                print(f"   ✅ 成功: {exec_result['success']}")

                if exec_result['success'] and exec_result.get('stdout'):
                    # 只显示前100个字符
                    output_preview = exec_result['stdout'][:100] + "..." if len(exec_result['stdout']) > 100 else exec_result['stdout']
                    print(f"   📤 输出预览: {output_preview}")

if __name__ == "__main__":
    test_slash_commands()