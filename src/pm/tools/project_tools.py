"""项目管理AI可调用工具函数 - Sprint 14次要目标

这些函数被设计为独立的、可供AI直接调用的工具函数
不依赖CLI框架，可以被其他Python代码或AI代理直接调用
将pm projects overview和pm project status核心逻辑重构为AI可调用工具
"""

import structlog
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

from pm.core.config import PMConfig
from pm.agents.project_manager import ProjectManagerAgent
from pm.models.project import ProjectHealth, ProjectPriority

logger = structlog.get_logger()


# ========== 项目概览工具 ==========

def get_projects_overview(
    sort_by: str = "health",
    max_projects: int = 50,
    config: Optional[PMConfig] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """获取项目概览信息
    
    Args:
        sort_by: 排序方式 (health/priority/name/progress)
        max_projects: 最大显示项目数量
        config: 配置对象
        
    Returns:
        Tuple[成功标志, 消息, 项目概览信息字典]
    """
    try:
        config = config or PMConfig()
        
        # 检查系统初始化状态
        if not config.is_initialized():
            return False, "系统未初始化，请先运行设置向导", None
        
        if not config.project_folders:
            return False, "未配置项目文件夹，请先配置项目根目录", None
        
        # 验证排序参数
        valid_sort_options = ["health", "priority", "name", "progress"]
        if sort_by not in valid_sort_options:
            return False, f"无效的排序选项，支持的选项: {', '.join(valid_sort_options)}", None
        
        # 初始化项目管理Agent
        agent = ProjectManagerAgent(config)
        
        # 获取项目概览
        try:
            overview = agent.get_project_overview(sort_by=sort_by)
        except Exception as e:
            logger.error("Failed to get project overview", error=str(e))
            return False, f"扫描项目失败: {str(e)}", None
        
        if not overview:
            return False, "未发现任何项目，请检查项目文件夹配置和PROJECT_STATUS.md文件", None
        
        # 限制显示数量
        if len(overview) > max_projects:
            overview = overview[:max_projects]
        
        # 获取完整的统计信息（包含health_distribution和priority_distribution）
        stats = agent.get_project_statistics()
        
        # 转换项目数据为更适合AI处理的格式
        projects_data = []
        for project in overview:
            project_info = {
                "name": project["name"],
                "path": project["path"],
                "progress": project["progress"],
                "health": project["health"].value,
                "health_emoji": project["health_emoji"],
                "priority": project["priority"].value,
                "priority_emoji": project["priority_emoji"],
                "is_at_risk": project["is_at_risk"],
                "next_actions_count": project["next_actions_count"],
                "last_updated": project["last_updated"].isoformat() if project["last_updated"] else None,
                "description": project.get("description", ""),
                "current_phase": project.get("current_phase", ""),
                "team_members": project.get("team_members", []),
                "technologies": project.get("technologies", [])
            }
            projects_data.append(project_info)
        
        # 构建返回信息
        overview_info = {
            "total_projects_found": len(overview) if len(overview) <= max_projects else f"{len(overview)}+",
            "displayed_projects": len(projects_data),
            "sort_by": sort_by,
            "scan_time": agent._last_scan_time.isoformat() if agent._last_scan_time else None,
            "projects": projects_data,
            "statistics": {
                "total_projects": stats.get("total_projects", 0),
                "average_progress": stats.get("average_progress", 0),
                "projects_at_risk": stats.get("projects_at_risk", 0),
                "projects_with_no_updates": stats.get("projects_with_no_updates", 0),
                "health_distribution": stats.get("health_distribution", {}),
                "priority_distribution": stats.get("priority_distribution", {})
            },
            "config_info": {
                "project_folders": config.project_folders,
                "projects_root": config.projects_root
            }
        }
        
        logger.info("Projects overview retrieved successfully", 
                   project_count=len(projects_data),
                   sort_by=sort_by)
        
        return True, f"成功获取 {len(projects_data)} 个项目的概览信息", overview_info
        
    except Exception as e:
        logger.error("Failed to get projects overview", error=str(e))
        return False, f"获取项目概览时发生错误: {str(e)}", None


def search_projects(
    query: str,
    max_results: int = 20,
    config: Optional[PMConfig] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """搜索项目
    
    Args:
        query: 搜索关键词
        max_results: 最大返回结果数
        config: 配置对象
        
    Returns:
        Tuple[成功标志, 消息, 搜索结果字典]
    """
    try:
        if not query.strip():
            return False, "搜索关键词不能为空", None
        
        config = config or PMConfig()
        
        if not config.is_initialized():
            return False, "系统未初始化，请先运行设置向导", None
        
        # 初始化项目管理Agent
        agent = ProjectManagerAgent(config)
        
        # 搜索项目 (修复参数不匹配Bug)
        try:
            all_results = agent.search_projects(query)
            # 限制结果数量
            results = all_results[:max_results] if len(all_results) > max_results else all_results
        except Exception as e:
            logger.error("Failed to search projects", query=query, error=str(e))
            return False, f"搜索项目失败: {str(e)}", None
        
        if not results:
            return False, f"没有找到包含关键词 '{query}' 的项目", None
        
        # 转换搜索结果 (修复ProjectStatus对象访问Bug)
        search_results = []
        for project in results:
            result_info = {
                "name": project.name,
                "path": str(project.path),
                "path_name": project.path.name,
                "progress": project.progress,
                "health": project.health.value,
                "health_emoji": "🟢" if project.health.value == "excellent" else "🟡" if project.health.value == "good" else "🟠" if project.health.value == "warning" else "🔴" if project.health.value == "critical" else "⚪",
                "priority": project.priority.value,
                "description": project.description or ""
            }
            search_results.append(result_info)
        
        search_info = {
            "query": query,
            "total_results": len(search_results),
            "max_results": max_results,
            "projects": search_results
        }
        
        logger.info("Projects search completed", 
                   query=query,
                   results_count=len(search_results))
        
        return True, f"找到 {len(search_results)} 个匹配的项目", search_info
        
    except Exception as e:
        logger.error("Failed to search projects", query=query, error=str(e))
        return False, f"搜索项目时发生错误: {str(e)}", None


# ========== 项目详情工具 ==========

def get_project_status(
    project_name: str,
    config: Optional[PMConfig] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """获取项目详细状态信息
    
    Args:
        project_name: 项目名称
        config: 配置对象
        
    Returns:
        Tuple[成功标志, 消息, 项目详情字典]
    """
    try:
        if not project_name.strip():
            return False, "项目名称不能为空", None
        
        config = config or PMConfig()
        
        if not config.is_initialized():
            return False, "系统未初始化，请先运行设置向导", None
        
        # 初始化项目管理Agent
        agent = ProjectManagerAgent(config)
        
        # 获取项目详情
        try:
            project = agent.get_project_details(project_name)
        except Exception as e:
            logger.error("Failed to get project details", 
                        project_name=project_name, error=str(e))
            return False, f"加载项目失败: {str(e)}", None
        
        if not project:
            return False, f"未找到项目 '{project_name}'，请检查项目名称是否正确", None
        
        # 转换项目详情为AI友好格式 (修复对象访问Bug)
        # 生成表情符号
        health_emoji = "🟢" if project.health.value == "excellent" else "🟡" if project.health.value == "good" else "🟠" if project.health.value == "warning" else "🔴" if project.health.value == "critical" else "⚪"
        priority_emoji = "🔥" if project.priority.value == "high" else "📋" if project.priority.value == "medium" else "📝"
        
        project_status = {
            "basic_info": {
                "name": project.name,
                "path": str(project.path),
                "description": project.description or "",
                "current_phase": project.current_phase or "",
                "team_members": project.team_members or [],
                "target_completion": project.deadline.isoformat() if project.deadline else None
            },
            "status_metrics": {
                "progress": project.progress,
                "health": project.health.value,
                "health_emoji": health_emoji,
                "priority": project.priority.value,
                "priority_emoji": priority_emoji,
                "last_updated": project.last_updated.isoformat() if project.last_updated else None
            },
            "description": project.description or "",
            "completed_work": project.completed_work,
            "next_actions": project.next_actions,
            "risks": project.risks,
            "dependencies": getattr(project, 'dependencies', []),
            "tags": getattr(project, 'tags', [])
        }
        
        logger.info("Project status retrieved successfully", 
                   project_name=project_name,
                   health=project_status["status_metrics"]["health"],
                   progress=project_status["status_metrics"]["progress"])
        
        return True, f"成功获取项目 '{project_name}' 的详细状态", project_status
        
    except Exception as e:
        logger.error("Failed to get project status", 
                    project_name=project_name, error=str(e))
        return False, f"获取项目状态时发生错误: {str(e)}", None


def get_project_next_actions(
    project_name: str,
    limit: int = 10,
    config: Optional[PMConfig] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """获取项目的下一步行动列表
    
    Args:
        project_name: 项目名称
        limit: 返回行动项的最大数量
        config: 配置对象
        
    Returns:
        Tuple[成功标志, 消息, 下一步行动字典]
    """
    try:
        if not project_name.strip():
            return False, "项目名称不能为空", None
        
        # 首先获取项目状态
        success, message, project_status = get_project_status(project_name, config)
        
        if not success:
            return success, message, None
        
        # 提取下一步行动
        next_actions = project_status["work_breakdown"]["next_actions"]
        
        if not next_actions:
            return False, f"项目 '{project_name}' 暂无下一步行动", None
        
        # 限制数量
        limited_actions = next_actions[:limit] if len(next_actions) > limit else next_actions
        
        actions_info = {
            "project_name": project_name,
            "total_actions": len(next_actions),
            "displayed_actions": len(limited_actions),
            "actions": limited_actions,
            "project_health": project_status["status_metrics"]["health"],
            "project_progress": project_status["status_metrics"]["progress"],
            "is_at_risk": project_status["status_metrics"]["is_at_risk"]
        }
        
        return True, f"获取到项目 '{project_name}' 的 {len(limited_actions)} 个下一步行动", actions_info
        
    except Exception as e:
        logger.error("Failed to get project next actions", 
                    project_name=project_name, error=str(e))
        return False, f"获取项目下一步行动时发生错误: {str(e)}", None


def get_project_risks_summary(
    config: Optional[PMConfig] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """获取所有项目的风险摘要
    
    Args:
        config: 配置对象
        
    Returns:
        Tuple[成功标志, 消息, 风险摘要字典]
    """
    try:
        # 获取项目概览
        success, message, overview_info = get_projects_overview(
            sort_by="health", 
            max_projects=100, 
            config=config
        )
        
        if not success:
            return success, message, None
        
        projects = overview_info["projects"]
        at_risk_projects = [p for p in projects if p["is_at_risk"]]
        critical_health_projects = [p for p in projects if p["health"] == "critical"]
        warning_health_projects = [p for p in projects if p["health"] == "warning"]
        
        # 分析风险趋势
        risk_categories = {}
        for project in at_risk_projects:
            # 这里可以根据项目的具体风险因素进行分类
            # 目前基于健康状态进行基础分类
            category = f"{project['health']}_risk"
            if category not in risk_categories:
                risk_categories[category] = []
            risk_categories[category].append({
                "name": project["name"],
                "progress": project["progress"],
                "health": project["health"],
                "priority": project["priority"],
                "last_updated": project["last_updated"]
            })
        
        risks_summary = {
            "overall_risk_level": "high" if len(at_risk_projects) > len(projects) * 0.3 
                                 else "medium" if len(at_risk_projects) > len(projects) * 0.1 
                                 else "low",
            "total_projects": len(projects),
            "at_risk_projects": len(at_risk_projects),
            "critical_health_projects": len(critical_health_projects),
            "warning_health_projects": len(warning_health_projects),
            "risk_percentage": round((len(at_risk_projects) / len(projects)) * 100, 1) if projects else 0,
            "at_risk_project_details": at_risk_projects,
            "risk_categories": risk_categories,
            "recommendations": []
        }
        
        # 生成建议
        if risks_summary["risk_percentage"] > 30:
            risks_summary["recommendations"].append("整体项目风险较高，建议优先处理关键健康问题")
        if len(critical_health_projects) > 0:
            risks_summary["recommendations"].append(f"有 {len(critical_health_projects)} 个关键健康项目需要立即关注")
        if len(warning_health_projects) > 3:
            risks_summary["recommendations"].append("多个项目处于警告状态，建议制定预防措施")
        
        logger.info("Project risks summary generated", 
                   total_projects=len(projects),
                   at_risk_count=len(at_risk_projects),
                   risk_percentage=risks_summary["risk_percentage"])
        
        return True, f"生成项目风险摘要：{len(projects)} 个项目中有 {len(at_risk_projects)} 个存在风险", risks_summary
        
    except Exception as e:
        logger.error("Failed to get project risks summary", error=str(e))
        return False, f"获取项目风险摘要时发生错误: {str(e)}", None


def get_project_statistics_summary(
    config: Optional[PMConfig] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """获取项目统计摘要信息
    
    Args:
        config: 配置对象
        
    Returns:
        Tuple[成功标志, 消息, 统计摘要字典]
    """
    try:
        # 获取项目概览
        success, message, overview_info = get_projects_overview(
            sort_by="health", 
            max_projects=100, 
            config=config
        )
        
        if not success:
            return success, message, None
        
        stats = overview_info["statistics"]
        projects = overview_info["projects"]
        
        # 增强统计信息
        enhanced_stats = {
            **stats,
            "health_distribution": {
                "excellent": len([p for p in projects if p["health"] == "excellent"]),
                "good": len([p for p in projects if p["health"] == "good"]),
                "warning": len([p for p in projects if p["health"] == "warning"]),
                "critical": len([p for p in projects if p["health"] == "critical"])
            },
            "priority_distribution": {
                "high": len([p for p in projects if p["priority"] == "high"]),
                "medium": len([p for p in projects if p["priority"] == "medium"]),
                "low": len([p for p in projects if p["priority"] == "low"])
            },
            "progress_distribution": {
                "completed": len([p for p in projects if p["progress"] >= 100]),
                "nearly_complete": len([p for p in projects if 80 <= p["progress"] < 100]),
                "in_progress": len([p for p in projects if 20 <= p["progress"] < 80]),
                "just_started": len([p for p in projects if p["progress"] < 20])
            },
            "scan_info": {
                "scan_time": overview_info["scan_time"],
                "total_projects_scanned": overview_info["total_projects_found"],
                "project_folders": len(overview_info["config_info"]["project_folders"])
            }
        }
        
        logger.info("Project statistics summary generated", 
                   total_projects=stats["total_projects"],
                   active_projects=stats["active_projects"],
                   at_risk_projects=stats["at_risk_projects"])
        
        return True, f"生成项目统计摘要：共 {stats['total_projects']} 个项目", enhanced_stats
        
    except Exception as e:
        logger.error("Failed to get project statistics summary", error=str(e))
        return False, f"获取项目统计摘要时发生错误: {str(e)}", None