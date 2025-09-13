#!/usr/bin/env python3
"""
调试脚本：直接测试create_weekly_review工具函数
"""

import sys
import os
from datetime import date, timedelta

# 添加src路径
sys.path.insert(0, '/Users/sheldonzhao/programs/personal-manager/src')

from pm.tools.review_tools import create_weekly_review
from pm.core.config import PMConfig

def test_create_weekly_review():
    """直接测试create_weekly_review函数"""
    
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    
    # 创建测试参数
    test_achievements = ["完成项目A", "学习新技能B"] 
    test_challenges = ["时间管理", "技术难题"]
    
    config = PMConfig()
    
    print(f"测试参数:")
    print(f"  achievements: {test_achievements}")
    print(f"  challenges: {test_challenges}")
    
    # 调用工具函数
    success, message, review_info = create_weekly_review(
        week_start_date=week_start.isoformat(),
        achievements=test_achievements,
        challenges=test_challenges,
        lessons_learned=["需要更好的规划"],
        what_went_well=["团队协作"],
        what_could_improve=["效率"],
        week_goals_achieved=["目标1"],
        week_goals_missed=["目标2"],
        next_week_goals=["目标3"],
        overall_satisfaction=4,
        productivity_rating=3,
        learning_rating=4,
        work_performance=3,
        personal_development=4,
        health_wellness=3,
        relationships=4,
        config=config
    )
    
    print(f"\n结果:")
    print(f"  success: {success}")
    print(f"  message: {message}")
    if review_info:
        print(f"  成就数量: {review_info.get('total_achievements', 'N/A')}")
        print(f"  挑战数量: {review_info.get('total_challenges', 'N/A')}")
    
    return success, message, review_info

if __name__ == "__main__":
    test_create_weekly_review()