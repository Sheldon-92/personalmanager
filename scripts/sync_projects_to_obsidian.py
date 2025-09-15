#!/usr/bin/env python3
"""
同步PROJECT_STATUS.md到Obsidian的脚本
可以通过cron定时运行或手动执行
"""

import os
import json
from pathlib import Path
from datetime import datetime
import re

# 配置路径
PROGRAMS_DIR = Path("/Users/sheldonzhao/programs")
OBSIDIAN_PROJECTS_DIR = Path("/Users/sheldonzhao/Documents/Obsidian Vault/PersonalManager/项目")

def parse_project_status(file_path):
    """解析PROJECT_STATUS.md文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 提取关键信息（简化版解析）
    project_data = {
        'name': '',
        'progress': 0,
        'health': 'unknown',
        'priority': 'medium',
        'updated': datetime.now().strftime('%Y-%m-%d'),
        'content': content
    }

    # 尝试提取进度
    progress_match = re.search(r'\*\*进度\*\*[:：]\s*(\d+)%', content)
    if progress_match:
        project_data['progress'] = int(progress_match.group(1))

    # 尝试提取健康度
    if '良好' in content or 'Good' in content:
        project_data['health'] = 'good'
    elif '注意' in content or 'Warning' in content:
        project_data['health'] = 'warning'
    elif '危险' in content or 'Critical' in content:
        project_data['health'] = 'critical'

    # 尝试提取优先级
    if '高' in content or 'High' in content:
        project_data['priority'] = 'high'
    elif '低' in content or 'Low' in content:
        project_data['priority'] = 'low'

    return project_data

def sync_to_obsidian():
    """同步所有项目到Obsidian"""
    synced_projects = []

    # 扫描所有PROJECT_STATUS.md文件
    for project_dir in PROGRAMS_DIR.iterdir():
        if project_dir.is_dir():
            status_file = project_dir / "PROJECT_STATUS.md"
            if status_file.exists():
                project_name = project_dir.name
                print(f"同步项目: {project_name}")

                # 解析项目状态
                project_data = parse_project_status(status_file)
                project_data['name'] = project_name

                # 创建或更新Obsidian笔记
                obsidian_file = OBSIDIAN_PROJECTS_DIR / f"{project_name}.md"

                # 生成Obsidian笔记内容
                obsidian_content = f"""# {project_name}

## 📊 状态概览
*最后同步: {datetime.now().strftime('%Y-%m-%d %H:%M')}*

- **进度**: {project_data['progress']}%
- **健康度**: {project_data['health']}
- **优先级**: {project_data['priority']}

## 📝 PROJECT_STATUS.md 内容

{project_data['content']}

---
*此文档由PersonalManager自动同步*
#项目 #自动同步
"""

                # 写入Obsidian文件
                obsidian_file.write_text(obsidian_content, encoding='utf-8')
                synced_projects.append(project_name)

    # 更新项目总览
    update_projects_overview(synced_projects)

    print(f"\n✅ 同步完成！共同步 {len(synced_projects)} 个项目")
    return synced_projects

def update_projects_overview(projects):
    """更新项目总览文档"""
    overview_file = OBSIDIAN_PROJECTS_DIR / "项目总览.md"

    content = f"""# 📊 项目总览
*最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M')}*
*自动同步自PROJECT_STATUS.md*

## 📈 项目列表

"""

    for project_name in projects:
        content += f"- [[{project_name}]]\n"

    content += f"""

## 🔄 同步信息
- 同步时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}
- 项目数量: {len(projects)}
- 同步方式: 自动脚本

---
#项目管理 #总览 #自动同步
"""

    overview_file.write_text(content, encoding='utf-8')

if __name__ == "__main__":
    print("🔄 开始同步PROJECT_STATUS.md到Obsidian...")
    sync_to_obsidian()