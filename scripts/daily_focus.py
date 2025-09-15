#!/usr/bin/env python3
"""
每日专注脚本 - 帮助你聚焦最重要的事
"""

import os
import json
import datetime
from pathlib import Path
import subprocess

def get_today_focus():
    """获取今日重点"""
    today = datetime.datetime.now()
    weekday = today.strftime("%A")

    # 根据星期设定重点项目
    focus_map = {
        "Monday": "The World's Table - 功能开发",
        "Tuesday": "The World's Table - 用户访谈",
        "Wednesday": "The World's Table - 迭代优化",
        "Thursday": "Capstone - 推进进度",
        "Friday": "Capstone - 课程作业",
        "Saturday": "PersonalManager - 优化维护",
        "Sunday": "复盘 + 计划 + 摄影"
    }

    return focus_map.get(weekday, "The World's Table")

def create_daily_note():
    """创建今日笔记"""
    today = datetime.datetime.now()
    date_str = today.strftime("%Y-%m-%d")

    obsidian_path = Path.home() / "Documents" / "Obsidian Vault" / "PersonalManager" / "每日记录"
    obsidian_path.mkdir(parents=True, exist_ok=True)

    daily_file = obsidian_path / f"{date_str}.md"

    if not daily_file.exists():
        focus = get_today_focus()
        content = f"""# 📅 {date_str} - {today.strftime("%A")}

## 🎯 今日重点
**{focus}**

## ⏰ 时间块
- [ ] 09:00-12:00：深度工作 - {focus}
- [ ] 14:00-17:00：次要任务
- [ ] 19:00-21:00：学习/优化
- [ ] 22:00-23:00：阅读

## ✅ 必做清单（不超过3项）
1. [ ]
2. [ ]
3. [ ]

## 💰 商业进展
- 用户反馈：
- 收入进展：
- 下一步：

## 📝 项目进度
- The World's Table: __%
- Capstone: __%
- PersonalManager: __%

## 💡 今日学到
-

## 🏊 习惯追踪
- [ ] 游泳/运动
- [ ] 阅读30分钟
- [ ] 深度工作3小时

## 🌟 今日最佳
最有成就感的事：

## 🔄 明日计划
最重要的一件事：

---
*Focus on shipping, not perfecting.*
"""
        daily_file.write_text(content, encoding='utf-8')
        print(f"✅ 创建今日笔记：{daily_file}")
        return daily_file
    else:
        print(f"📝 今日笔记已存在：{daily_file}")
        return daily_file

def show_focus_reminder():
    """显示专注提醒"""
    focus = get_today_focus()

    print("\n" + "="*50)
    print("🎯 今日专注提醒")
    print("="*50)
    print(f"\n📅 {datetime.datetime.now().strftime('%Y-%m-%d %A')}")
    print(f"🔥 今日重点：{focus}")
    print("\n💡 记住你的目标：")
    print("   1. The World's Table → 第一个付费用户")
    print("   2. 月收入$500 → 财务独立")
    print("   3. 3个production-ready项目 → 理想工作")
    print("\n⏰ 深度工作时间：09:00-12:00")
    print("📱 关闭所有通知，全力以赴！")
    print("\n" + "="*50)

def run_pm_today():
    """运行PersonalManager今日推荐"""
    try:
        result = subprocess.run(
            ["./bin/pm-local", "today"],
            capture_output=True,
            text=True,
            cwd="/Users/sheldonzhao/programs/personal-manager"
        )
        print("\n📋 PersonalManager 今日推荐：")
        print(result.stdout)
    except Exception as e:
        print(f"⚠️ 无法运行PersonalManager: {e}")

def main():
    """主函数"""
    print("\n🚀 启动每日专注模式...\n")

    # 1. 显示专注提醒
    show_focus_reminder()

    # 2. 创建今日笔记
    daily_note = create_daily_note()

    # 3. 运行PersonalManager
    run_pm_today()

    # 4. 打开今日笔记
    print(f"\n📝 打开今日笔记编辑...")
    os.system(f"open '{daily_note}'")

    print("\n✨ 准备就绪！开始你的深度工作吧！")
    print("💪 记住：Done is better than perfect!\n")

if __name__ == "__main__":
    main()