"""Project Manager Agent - 项目状态管理核心Agent"""

from pathlib import Path
from typing import List, Dict, Optional, Set
from datetime import datetime
import structlog

from pm.core.config import PMConfig
from pm.models.project import ProjectStatus, ProjectStatusParser, ProjectHealth, ProjectPriority

logger = structlog.get_logger()


class ProjectManagerAgent:
    """项目管理Agent
    
    基于"以报告为中心"的方案，管理和解析PROJECT_STATUS.md文件
    实现项目状态的读取、解析、汇总和监控功能
    """
    
    def __init__(self, config: Optional[PMConfig] = None):
        self.config = config or PMConfig()
        self.parser = ProjectStatusParser()
        self._project_cache: Dict[str, ProjectStatus] = {}
        self._last_scan_time: Optional[datetime] = None
        
        logger.info("ProjectManagerAgent initialized")
    
    def discover_projects(self, force_rescan: bool = False) -> List[ProjectStatus]:
        """发现所有项目
        
        Args:
            force_rescan: 是否强制重新扫描
            
        Returns:
            项目状态列表
        """
        
        if not force_rescan and self._project_cache and self._last_scan_time:
            # 使用缓存（5分钟内有效）
            time_diff = datetime.now() - self._last_scan_time
            if time_diff.total_seconds() < 300:  # 5分钟
                return list(self._project_cache.values())
        
        logger.info("Scanning for projects", folders=self.config.project_folders)
        
        projects = []
        self._project_cache.clear()
        
        for folder_path in self.config.project_folders:
            folder = Path(folder_path)
            if not folder.exists():
                logger.warning("Project folder not found", path=folder_path)
                continue
            
            # 查找PROJECT_STATUS.md文件
            project_files = self._find_project_status_files(folder)
            
            for project_file in project_files:
                try:
                    project = self.parser.parse_file(project_file)
                    # 确保项目路径指向目录而不是文件
                    project.path = project_file.parent
                    projects.append(project)
                    self._project_cache[project.name] = project
                    
                    logger.info("Project discovered", 
                               name=project.name, 
                               path=str(project.path),
                               progress=project.progress,
                               health=project.health.value)
                    
                except Exception as e:
                    logger.error("Failed to parse project", 
                               file=str(project_file), 
                               error=str(e))
        
        self._last_scan_time = datetime.now()
        
        logger.info("Project discovery completed", count=len(projects))
        return projects
    
    def get_project_overview(self, sort_by: str = "health") -> List[Dict]:
        """获取项目概览
        
        Args:
            sort_by: 排序方式 (health, priority, progress, name)
            
        Returns:
            项目概览列表
        """
        
        projects = self.discover_projects()
        
        overview = []
        for project in projects:
            overview.append({
                "name": project.name,
                "progress": project.progress,
                "health": project.health,
                "priority": project.priority,
                "health_emoji": project.get_status_emoji(),
                "priority_emoji": project.get_priority_emoji(),
                "last_updated": project.last_updated,
                "path": str(project.path),
                "is_at_risk": project.is_at_risk(),
                "next_actions_count": len(project.next_actions),
                "risks_count": len(project.risks)
            })
        
        # 排序
        overview = self._sort_projects(overview, sort_by)
        
        logger.info("Project overview generated", 
                   count=len(overview), 
                   sort_by=sort_by)
        
        return overview
    
    def get_project_details(self, project_name: str) -> Optional[ProjectStatus]:
        """获取项目详细信息
        
        Args:
            project_name: 项目名称
            
        Returns:
            项目详细状态，如果不存在返回None
        """
        
        # 首先从缓存查找
        if project_name in self._project_cache:
            project = self._project_cache[project_name]
            
            # 检查文件是否有更新
            project_file = project.path / "PROJECT_STATUS.md"
            if project_file.exists():
                try:
                    file_mtime = datetime.fromtimestamp(project_file.stat().st_mtime)
                    if project.last_updated and file_mtime > project.last_updated:
                        # 文件已更新，重新解析
                        logger.info("Project file updated, reparsing", name=project_name)
                        updated_project = self.parser.parse_file(project_file)
                        self._project_cache[project_name] = updated_project
                        return updated_project
                except Exception as e:
                    logger.error("Failed to check file update time", 
                               name=project_name, error=str(e))
            
            return project
        
        # 缓存中没有，重新扫描
        projects = self.discover_projects(force_rescan=True)
        
        for project in projects:
            if project.name == project_name:
                return project
        
        logger.warning("Project not found", name=project_name)
        return None
    
    def update_project_status(self, project_name: Optional[str] = None) -> Dict[str, any]:
        """更新项目状态
        
        Args:
            project_name: 项目名称，None表示更新所有项目
            
        Returns:
            更新结果统计
        """
        
        result = {
            "updated": 0,
            "failed": 0,
            "errors": [],
            "updated_projects": []
        }
        
        if project_name:
            # 更新单个项目
            project = self.get_project_details(project_name)
            if project:
                try:
                    # 重新解析文件
                    project_file = project.path / "PROJECT_STATUS.md"
                    if project_file.exists():
                        updated_project = self.parser.parse_file(project_file)
                        self._project_cache[project_name] = updated_project
                        result["updated"] += 1
                        result["updated_projects"].append(project_name)
                        
                        logger.info("Project status updated", name=project_name)
                    else:
                        error_msg = f"PROJECT_STATUS.md not found for {project_name}"
                        result["errors"].append(error_msg)
                        result["failed"] += 1
                        
                except Exception as e:
                    error_msg = f"Failed to update {project_name}: {str(e)}"
                    result["errors"].append(error_msg)
                    result["failed"] += 1
                    logger.error("Project update failed", name=project_name, error=str(e))
            else:
                error_msg = f"Project not found: {project_name}"
                result["errors"].append(error_msg)
                result["failed"] += 1
        else:
            # 更新所有项目
            projects = self.discover_projects(force_rescan=True)
            result["updated"] = len(projects)
            result["updated_projects"] = [p.name for p in projects]
            
            logger.info("All projects updated", count=len(projects))
        
        return result
    
    def get_project_statistics(self) -> Dict[str, any]:
        """获取项目统计信息"""
        
        projects = self.discover_projects()
        
        stats = {
            "total_projects": len(projects),
            "health_distribution": {
                "excellent": 0,
                "good": 0,
                "warning": 0,
                "critical": 0,
                "unknown": 0
            },
            "priority_distribution": {
                "high": 0,
                "medium": 0,
                "low": 0
            },
            "average_progress": 0.0,
            "projects_at_risk": 0,
            "projects_with_no_updates": 0
        }
        
        if not projects:
            return stats
        
        total_progress = 0.0
        for project in projects:
            # 健康状态分布
            stats["health_distribution"][project.health.value] += 1
            
            # 优先级分布
            stats["priority_distribution"][project.priority.value] += 1
            
            # 进度统计
            total_progress += project.progress
            
            # 风险项目
            if project.is_at_risk():
                stats["projects_at_risk"] += 1
            
            # 未更新项目
            if not project.last_updated:
                stats["projects_with_no_updates"] += 1
        
        stats["average_progress"] = total_progress / len(projects)
        
        return stats
    
    def search_projects(self, query: str) -> List[ProjectStatus]:
        """搜索项目
        
        Args:
            query: 搜索关键词
            
        Returns:
            匹配的项目列表
        """
        
        projects = self.discover_projects()
        query_lower = query.lower()
        
        matching_projects = []
        
        for project in projects:
            # 搜索项目名称
            if query_lower in project.name.lower():
                matching_projects.append(project)
                continue
            
            # 搜索描述
            if project.description and query_lower in project.description.lower():
                matching_projects.append(project)
                continue
            
            # 搜索标签
            if any(query_lower in tag.lower() for tag in project.tags):
                matching_projects.append(project)
                continue
            
            # 搜索路径
            if query_lower in str(project.path).lower():
                matching_projects.append(project)
                continue
        
        logger.info("Project search completed", 
                   query=query, 
                   results=len(matching_projects))
        
        return matching_projects
    
    def _find_project_status_files(self, folder: Path) -> List[Path]:
        """在文件夹中查找PROJECT_STATUS.md文件"""
        
        project_files = []
        
        # 直接在根目录查找
        root_file = folder / "PROJECT_STATUS.md"
        if root_file.exists():
            project_files.append(root_file)
        
        # 在子目录中查找（最多2层深度）
        for subfolder in folder.iterdir():
            if subfolder.is_dir() and not subfolder.name.startswith('.'):
                sub_file = subfolder / "PROJECT_STATUS.md"
                if sub_file.exists():
                    project_files.append(sub_file)
                
                # 第二层
                for subsubfolder in subfolder.iterdir():
                    if subsubfolder.is_dir() and not subsubfolder.name.startswith('.'):
                        subsub_file = subsubfolder / "PROJECT_STATUS.md"
                        if subsub_file.exists():
                            project_files.append(subsub_file)
        
        return project_files
    
    def _sort_projects(self, projects: List[Dict], sort_by: str) -> List[Dict]:
        """对项目进行排序"""
        
        sort_functions = {
            "health": lambda p: (
                p["is_at_risk"],  # 风险项目排在前面
                p["health"].value  # 然后按健康状态排序
            ),
            "priority": lambda p: (
                {"high": 0, "medium": 1, "low": 2}[p["priority"].value],
                -p["progress"]  # 相同优先级按进度倒序
            ),
            "progress": lambda p: -p["progress"],  # 进度倒序
            "name": lambda p: p["name"].lower(),  # 名称正序
            "updated": lambda p: p["last_updated"] or datetime.min  # 更新时间倒序
        }
        
        if sort_by in sort_functions:
            projects.sort(key=sort_functions[sort_by])
        
        return projects