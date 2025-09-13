#!/usr/bin/env python3
"""
调试脚本：测试Rich Prompt.ask的输入行为
"""

import sys
import io
from rich.console import Console
from rich.prompt import Prompt

console = Console()

def test_prompt_behavior():
    """测试Prompt.ask的输入行为"""
    
    # 模拟用户输入
    test_input = "完成项目A\n学习新技能B\n\n"
    
    # 重定向stdin
    original_stdin = sys.stdin
    sys.stdin = io.StringIO(test_input)
    
    try:
        console.print("[cyan]📈 本周成就测试：[/cyan]")
        achievements = []
        
        # 模拟原代码的输入循环
        for i in range(5):  # 最多5次，避免无限循环
            achievement = Prompt.ask(f"添加一项成就 #{i+1}（留空结束）", default="")
            console.print(f"输入 #{i+1}: '{achievement}'")
            if not achievement:
                console.print("空输入，结束")
                break
            achievements.append(achievement)
            
        console.print(f"收集到的成就: {achievements}")
        
    finally:
        sys.stdin = original_stdin
    
    return achievements

if __name__ == "__main__":
    result = test_prompt_behavior()
    print(f"最终结果: {result}")