#!/usr/bin/env python3
"""
自动项目管理器

功能：
1. 自动监控 programs 文件夹的变化
2. 为新文件夹自动创建 PROJECT_STATUS.md
3. 清理已删除文件夹对应的项目记录
4. 智能推测项目类型和基础信息
"""

import sys
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Set
import time
import structlog

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from pm.core.config import PMConfig
from pm.agents.project_manager import ProjectManagerAgent

logger = structlog.get_logger()


class AutoProjectManager:
    """自动项目管理器"""

    def __init__(self):
        self.config = PMConfig()
        self.project_agent = ProjectManagerAgent(self.config)
        self.programs_dir = Path("/Users/sheldonzhao/programs")

        # 项目类型智能识别关键词
        self.project_type_keywords = {
            "web": ["react", "vue", "angular", "nextjs", "nuxt", "website", "web", "frontend", "backend"],
            "mobile": ["react-native", "flutter", "ios", "android", "mobile", "app"],
            "ai": ["ai", "ml", "machine-learning", "tensorflow", "pytorch", "nlp", "chatbot"],
            "data": ["data", "analytics", "jupyter", "pandas", "numpy", "analysis"],
            "game": ["game", "unity", "unreal", "gaming", "godot"],
            "tool": ["tool", "utility", "cli", "script", "automation"],
            "study": ["course", "learning", "tutorial", "study", "class", "课程", "学习"],
            "content": ["blog", "content", "article", "writing", "podcast", "播客"],
            "personal": ["personal", "diary", "journal", "notes", "plan", "travel", "旅行"],
            "work": ["job", "career", "resume", "portfolio", "work", "jobs", "求职"],
            "business": ["business", "startup", "company", "mvp", "product"],
            "research": ["research", "thesis", "paper", "academic", "capstone", "graduation"]
        }

    def get_all_directories(self) -> Set[str]:
        """获取programs文件夹下所有目录名称"""
        directories = set()

        if not self.programs_dir.exists():
            logger.warning("Programs directory not found", path=str(self.programs_dir))
            return directories

        for item in self.programs_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                directories.add(item.name)

        return directories

    def get_existing_projects(self) -> Set[str]:
        """获取已有项目名称（有PROJECT_STATUS.md的目录）"""
        projects = set()

        for directory in self.get_all_directories():
            status_file = self.programs_dir / directory / "PROJECT_STATUS.md"
            if status_file.exists():
                projects.add(directory)

        return projects

    def detect_project_type(self, directory_name: str, directory_path: Path) -> str:
        """智能检测项目类型"""
        name_lower = directory_name.lower()

        # 检查目录名称中的关键词
        for project_type, keywords in self.project_type_keywords.items():
            for keyword in keywords:
                if keyword in name_lower:
                    return project_type

        # 检查目录内容（如果存在特征文件）
        try:
            if (directory_path / "package.json").exists():
                return "web"
            elif (directory_path / "requirements.txt").exists() or (directory_path / "pyproject.toml").exists():
                return "ai" if any(k in name_lower for k in ["ai", "ml", "data"]) else "tool"
            elif (directory_path / "Cargo.toml").exists():
                return "tool"
            elif (directory_path / ".java").exists() or any(directory_path.glob("*.java")):
                return "tool"
            elif any(directory_path.glob("*.md")) and len(list(directory_path.glob("*.md"))) > 3:
                return "content"
        except:
            pass

        return "personal"

    def estimate_progress(self, directory_path: Path) -> int:
        """估算项目进度"""
        try:
            file_count = len(list(directory_path.rglob("*")))

            if file_count < 5:
                return 10
            elif file_count < 20:
                return 30
            elif file_count < 50:
                return 50
            else:
                return 70
        except:
            return 25

    def determine_priority(self, project_type: str, directory_name: str) -> str:
        """确定项目优先级"""
        name_lower = directory_name.lower()

        # 高优先级关键词
        high_priority_keywords = ["capstone", "graduation", "thesis", "job", "work", "mvp", "main", "primary"]
        # 低优先级关键词
        low_priority_keywords = ["test", "demo", "backup", "old", "archive", "temp"]

        for keyword in high_priority_keywords:
            if keyword in name_lower:
                return "high"

        for keyword in low_priority_keywords:
            if keyword in name_lower:
                return "low"

        # 根据项目类型确定优先级
        high_priority_types = ["work", "business", "research"]
        if project_type in high_priority_types:
            return "high"

        return "medium"

    def create_project_status(self, directory_name: str, directory_path: Path) -> bool:
        """为新目录创建PROJECT_STATUS.md文件"""

        project_type = self.detect_project_type(directory_name, directory_path)
        progress = self.estimate_progress(directory_path)
        priority = self.determine_priority(project_type, directory_name)

        # 项目类型描述映射
        type_descriptions = {
            "web": "Web应用开发",
            "mobile": "移动应用开发",
            "ai": "人工智能/机器学习",
            "data": "数据分析",
            "game": "游戏开发",
            "tool": "工具开发",
            "study": "学习项目",
            "content": "内容创作",
            "personal": "个人项目",
            "work": "工作相关",
            "business": "商业项目",
            "research": "研究项目"
        }

        # 根据项目类型生成合适的下一步行动
        next_actions = {
            "web": [
                "完善项目架构设计",
                "实现核心功能模块",
                "编写测试用例",
                "优化用户体验"
            ],
            "study": [
                "整理学习资料",
                "完成课程作业",
                "复习重点内容",
                "准备考试"
            ],
            "work": [
                "完善个人简历",
                "搜索目标职位",
                "准备面试材料",
                "建立职业网络"
            ],
            "content": [
                "制定内容策略",
                "准备创作工具",
                "建立发布流程",
                "分析目标受众"
            ],
            "personal": [
                "明确项目目标",
                "制定实施计划",
                "收集必要资源",
                "开始初步实施"
            ]
        }

        actions = next_actions.get(project_type, next_actions["personal"])

        status_content = f"""# {directory_name}

## 项目信息
**项目名称**: {directory_name}
**创建时间**: {datetime.now().strftime('%Y-%m-%d')}
**项目类型**: {type_descriptions.get(project_type, '未知类型')}
**当前状态**: 🟡 进行中

## 进度概览
**整体进度**: {progress}%
**当前阶段**: 项目开发
**预期完成**: 待定

## 健康状况
**健康等级**: unknown
**优先级**: {priority}
**风险等级**: 低

## 下一步行动
{''.join(f'- [ ] {action}' + chr(10) for action in actions)}

## 风险与挑战
- 需要进一步明确项目目标
- 时间管理需要优化

## 备注
此项目状态文件由系统自动生成。请根据实际情况更新项目信息。

---
*最后更新: {datetime.now().strftime('%Y-%m-%d')}*
*自动创建: 由AutoProjectManager生成*"""

        status_file = directory_path / "PROJECT_STATUS.md"

        try:
            with open(status_file, 'w', encoding='utf-8') as f:
                f.write(status_content)

            logger.info("Created PROJECT_STATUS.md for new directory",
                       name=directory_name,
                       type=project_type,
                       priority=priority,
                       progress=progress)
            return True

        except Exception as e:
            logger.error("Failed to create PROJECT_STATUS.md",
                        name=directory_name,
                        error=str(e))
            return False

    def scan_and_update(self) -> Dict[str, any]:
        """扫描目录变化并更新项目状态"""
        logger.info("开始自动项目扫描和更新")

        current_directories = self.get_all_directories()
        existing_projects = self.get_existing_projects()

        # 找出新增的目录（没有PROJECT_STATUS.md的目录）
        new_directories = current_directories - existing_projects

        # 找出已删除的项目（有PROJECT_STATUS.md但目录已不存在）
        deleted_projects = existing_projects - current_directories

        result = {
            "scanned_at": datetime.now().isoformat(),
            "total_directories": len(current_directories),
            "existing_projects": len(existing_projects),
            "new_directories": list(new_directories),
            "deleted_projects": list(deleted_projects),
            "created_projects": [],
            "errors": []
        }

        # 为新目录创建PROJECT_STATUS.md
        for dir_name in new_directories:
            dir_path = self.programs_dir / dir_name
            if self.create_project_status(dir_name, dir_path):
                result["created_projects"].append(dir_name)
            else:
                result["errors"].append(f"Failed to create status for {dir_name}")

        # 记录删除的项目（仅记录，不实际删除文件）
        if deleted_projects:
            logger.info("发现已删除的项目目录",
                       count=len(deleted_projects),
                       projects=list(deleted_projects))

        logger.info("自动项目扫描完成",
                   new_count=len(new_directories),
                   deleted_count=len(deleted_projects))

        return result

    def run_continuous_monitoring(self, check_interval: int = 300):
        """运行持续监控模式（每5分钟检查一次）"""
        logger.info("启动持续项目监控模式", interval_seconds=check_interval)

        try:
            while True:
                result = self.scan_and_update()

                if result["new_directories"] or result["deleted_projects"]:
                    logger.info("检测到项目变化",
                               new=result["new_directories"],
                               deleted=result["deleted_projects"])

                time.sleep(check_interval)

        except KeyboardInterrupt:
            logger.info("停止持续监控")
        except Exception as e:
            logger.error("持续监控出错", error=str(e))


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='自动项目管理器')
    parser.add_argument('--scan', action='store_true', help='执行一次扫描和更新')
    parser.add_argument('--monitor', action='store_true', help='启动持续监控模式')
    parser.add_argument('--interval', type=int, default=300, help='监控间隔（秒）')

    args = parser.parse_args()

    manager = AutoProjectManager()

    if args.monitor:
        manager.run_continuous_monitoring(args.interval)
    elif args.scan:
        result = manager.scan_and_update()

        print("\\n🔍 自动项目扫描结果")
        print(f"扫描时间: {result['scanned_at']}")
        print(f"总目录数: {result['total_directories']}")
        print(f"现有项目: {result['existing_projects']}")

        if result['new_directories']:
            print(f"\\n✅ 发现新目录: {len(result['new_directories'])}个")
            for name in result['new_directories']:
                print(f"   - {name}")

        if result['created_projects']:
            print(f"\\n🎉 创建新项目: {len(result['created_projects'])}个")
            for name in result['created_projects']:
                print(f"   - {name}")

        if result['deleted_projects']:
            print(f"\\n⚠️ 发现已删除项目: {len(result['deleted_projects'])}个")
            for name in result['deleted_projects']:
                print(f"   - {name}")

        if result['errors']:
            print(f"\\n❌ 错误: {len(result['errors'])}个")
            for error in result['errors']:
                print(f"   - {error}")

        if not result['new_directories'] and not result['deleted_projects']:
            print("\\n✨ 没有发现变化，所有项目都已是最新状态")

    else:
        print("请使用 --scan 进行一次扫描，或使用 --monitor 启动持续监控")
        print("\\n使用示例:")
        print("  python auto_project_manager.py --scan")
        print("  python auto_project_manager.py --monitor --interval 600")


if __name__ == "__main__":
    exit(main())