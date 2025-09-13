"""AI可调用的项目更新工具函数

提供项目状态更新的AI可调用接口，包括：
- 单个项目状态更新
- 批量项目状态更新
- 强制刷新项目缓存
- 更新结果分析
"""

from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import structlog

from pm.core.config import PMConfig
from pm.agents.project_manager import ProjectManagerAgent

logger = structlog.get_logger(__name__)


def update_single_project(project_name: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    更新单个项目状态
    
    Args:
        project_name: 项目名称
        
    Returns:
        Tuple[bool, str, Optional[Dict[str, Any]]]: (成功状态, 消息, 更新结果)
    """
    try:
        logger.info("更新单个项目状态", project_name=project_name)
        
        config = PMConfig()
        
        # 检查系统初始化状态
        if not config.is_initialized():
            return False, "系统未初始化，请先运行 pm setup 进行设置", None
            
        if not config.project_folders:
            return False, "未配置项目文件夹，请运行 pm setup 添加项目文件夹", None
            
        # 初始化项目管理Agent
        agent = ProjectManagerAgent(config)
        
        # 执行更新
        result = agent.update_project_status(project_name)
        
        if result["updated"] > 0:
            update_result = {
                'project_name': project_name,
                'update_successful': True,
                'update_time': datetime.now().isoformat(),
                'files_updated': result["updated"],
                'errors': result["errors"],
                'recommendations': [
                    f"查看项目详细状态: pm project status {project_name}",
                    "查看所有项目概览: pm projects overview"
                ]
            }
            
            logger.info("项目状态更新成功", 
                       project_name=project_name,
                       files_updated=result["updated"])
            return True, f"项目 '{project_name}' 状态更新成功", update_result
            
        else:
            # 更新失败
            error_details = result["errors"] if result["errors"] else ["未知错误"]
            
            update_result = {
                'project_name': project_name,
                'update_successful': False,
                'update_time': datetime.now().isoformat(),
                'files_updated': 0,
                'errors': error_details,
                'troubleshooting_suggestions': [
                    "检查 PROJECT_STATUS.md 文件是否存在",
                    "验证文件格式是否正确",
                    "确认文件权限允许读取",
                    "检查项目路径是否正确"
                ],
                'recommended_commands': [
                    f"pm project status {project_name}",
                    "pm privacy verify"
                ]
            }
            
            logger.warning("项目状态更新失败", 
                          project_name=project_name,
                          errors=error_details)
            return False, f"项目 '{project_name}' 更新失败: {'; '.join(error_details)}", update_result
            
    except Exception as e:
        logger.error("更新项目状态时发生错误", 
                    project_name=project_name,
                    error=str(e))
        return False, f"更新项目时发生错误: {str(e)}", None


def update_all_projects(force_rescan: bool = True) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    更新所有项目状态
    
    Args:
        force_rescan: 是否强制重新扫描项目
        
    Returns:
        Tuple[bool, str, Optional[Dict[str, Any]]]: (成功状态, 消息, 批量更新结果)
    """
    try:
        logger.info("启动批量项目状态更新", force_rescan=force_rescan)
        
        config = PMConfig()
        
        # 检查系统初始化状态
        if not config.is_initialized():
            return False, "系统未初始化，请先运行 pm setup 进行设置", None
            
        if not config.project_folders:
            return False, "未配置项目文件夹，请运行 pm setup 添加项目文件夹", None
            
        # 初始化项目管理Agent
        agent = ProjectManagerAgent(config)
        
        # 发现项目
        projects = agent.discover_projects(force_rescan=force_rescan)
        
        if not projects:
            return False, "未发现任何项目，请确保项目文件夹路径正确且包含 PROJECT_STATUS.md 文件", {
                'projects_discovered': 0,
                'troubleshooting': [
                    "检查项目文件夹路径是否正确",
                    "确保项目目录中存在 PROJECT_STATUS.md 文件",
                    "验证文件夹权限"
                ]
            }
            
        # 批量更新
        total_updated = 0
        total_failed = 0
        errors = []
        project_results = []
        
        for project in projects:
            try:
                project_result = agent.update_project_status(project.name)
                
                project_info = {
                    'project_name': project.name,
                    'files_updated': project_result["updated"],
                    'success': project_result["updated"] > 0,
                    'errors': project_result["errors"]
                }
                
                if project_result["updated"] > 0:
                    total_updated += 1
                else:
                    total_failed += 1
                    errors.extend([f"{project.name}: {error}" for error in project_result["errors"]])
                    
                project_results.append(project_info)
                
            except Exception as e:
                total_failed += 1
                error_msg = f"{project.name}: {str(e)}"
                errors.append(error_msg)
                
                project_results.append({
                    'project_name': project.name,
                    'files_updated': 0,
                    'success': False,
                    'errors': [str(e)]
                })
                
        # 计算成功率
        total_projects = len(projects)
        success_rate = (total_updated / total_projects * 100) if total_projects > 0 else 0
        
        # 确定整体状态
        if success_rate >= 90:
            overall_status = "excellent"
            status_message = "批量更新成功"
        elif success_rate >= 70:
            overall_status = "good"
            status_message = "批量更新部分成功"
        else:
            overall_status = "poor"
            status_message = "批量更新失败"
            
        batch_result = {
            'total_projects': total_projects,
            'projects_updated': total_updated,
            'projects_failed': total_failed,
            'success_rate': success_rate,
            'overall_status': overall_status,
            'project_results': project_results,
            'errors': errors,
            'update_time': datetime.now().isoformat(),
            'recommendations': []
        }
        
        # 生成建议
        if total_updated > 0:
            batch_result['recommendations'].extend([
                "查看更新后的项目概览: pm projects overview",
                "按进度排序查看: pm projects overview --sort progress",
                "创建数据备份: pm privacy backup"
            ])
            
        if total_failed > 0:
            batch_result['recommendations'].extend([
                "验证数据完整性: pm privacy verify",
                "检查失败项目的 PROJECT_STATUS.md 文件",
                "验证文件格式和权限"
            ])
            
        logger.info("批量项目状态更新完成", 
                   total_projects=total_projects,
                   updated=total_updated,
                   failed=total_failed,
                   success_rate=success_rate)
                   
        return True, f"{status_message}，成功更新 {total_updated}/{total_projects} 个项目", batch_result
        
    except Exception as e:
        logger.error("批量更新项目状态时发生错误", error=str(e))
        return False, f"批量更新失败: {str(e)}", None


def force_refresh_all_projects() -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    强制刷新所有项目状态（清除缓存）
    
    Returns:
        Tuple[bool, str, Optional[Dict[str, Any]]]: (成功状态, 消息, 刷新结果)
    """
    try:
        logger.info("启动强制刷新所有项目")
        
        config = PMConfig()
        
        if not config.is_initialized():
            return False, "系统未初始化，请先运行 pm setup 进行设置", None
            
        agent = ProjectManagerAgent(config)
        
        # 清除缓存
        original_cache_size = len(getattr(agent, '_project_cache', {}))
        agent._project_cache.clear()
        agent._last_scan_time = None
        
        # 重新发现项目
        projects = agent.discover_projects(force_rescan=True)
        
        refresh_result = {
            'refresh_successful': True,
            'refresh_time': datetime.now().isoformat(),
            'cache_cleared': True,
            'original_cache_size': original_cache_size,
            'projects_rediscovered': len(projects),
            'project_names': [project.name for project in projects],
            'recommendations': [
                "查看重新发现的项目: pm projects overview",
                "更新项目状态: pm update project",
                "验证数据完整性: pm privacy verify"
            ]
        }
        
        logger.info("强制刷新完成", 
                   projects_count=len(projects),
                   cache_cleared=original_cache_size)
        return True, f"强制刷新完成，重新发现 {len(projects)} 个项目", refresh_result
        
    except Exception as e:
        logger.error("强制刷新失败", error=str(e))
        return False, f"强制刷新失败: {str(e)}", None


def get_project_update_status(project_name: Optional[str] = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    获取项目更新状态信息
    
    Args:
        project_name: 项目名称，为空则获取所有项目的更新状态
        
    Returns:
        Tuple[bool, str, Optional[Dict[str, Any]]]: (成功状态, 消息, 状态信息)
    """
    try:
        logger.info("获取项目更新状态", project_name=project_name)
        
        config = PMConfig()
        
        if not config.is_initialized():
            return False, "系统未初始化", None
            
        agent = ProjectManagerAgent(config)
        
        # 获取项目列表
        projects = agent.discover_projects(force_rescan=False)
        
        if project_name:
            # 获取特定项目状态
            target_project = None
            for project in projects:
                if project.name == project_name:
                    target_project = project
                    break
                    
            if not target_project:
                return False, f"未找到项目: {project_name}", None
                
            status_info = {
                'project_name': target_project.name,
                'project_path': str(target_project.path),
                'last_modified': target_project.last_modified.isoformat() if hasattr(target_project, 'last_modified') else None,
                'status_file_exists': (target_project.path / 'PROJECT_STATUS.md').exists(),
                'is_cached': project_name in getattr(agent, '_project_cache', {}),
                'recommendations': [
                    f"查看项目详情: pm project status {project_name}",
                    f"更新项目状态: pm update project {project_name}"
                ]
            }
            
            return True, f"项目 {project_name} 状态信息", status_info
            
        else:
            # 获取所有项目状态概览
            total_projects = len(projects)
            cached_projects = len(getattr(agent, '_project_cache', {}))
            
            projects_with_status = 0
            projects_without_status = 0
            
            for project in projects:
                if (project.path / 'PROJECT_STATUS.md').exists():
                    projects_with_status += 1
                else:
                    projects_without_status += 1
                    
            status_overview = {
                'total_projects': total_projects,
                'projects_with_status_file': projects_with_status,
                'projects_without_status_file': projects_without_status,
                'cached_projects': cached_projects,
                'cache_hit_rate': (cached_projects / max(total_projects, 1)) * 100,
                'last_scan_time': getattr(agent, '_last_scan_time', None),
                'project_folders': config.project_folders,
                'status_timestamp': datetime.now().isoformat(),
                'recommendations': [
                    "更新所有项目: pm update project",
                    "强制刷新缓存: pm update refresh",
                    "查看项目概览: pm projects overview"
                ]
            }
            
            logger.info("项目更新状态概览获取完成", 
                       total_projects=total_projects,
                       cache_hit_rate=status_overview['cache_hit_rate'])
            return True, f"获取 {total_projects} 个项目的状态概览", status_overview
            
    except Exception as e:
        logger.error("获取项目更新状态失败", error=str(e))
        return False, f"获取状态失败: {str(e)}", None


def validate_project_update_requirements() -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    验证项目更新的前置条件
    
    Returns:
        Tuple[bool, str, Optional[Dict[str, Any]]]: (成功状态, 消息, 验证结果)
    """
    try:
        logger.info("验证项目更新前置条件")
        
        config = PMConfig()
        
        validation_result = {
            'system_initialized': False,
            'project_folders_configured': False,
            'project_folders_accessible': False,
            'projects_discoverable': False,
            'validation_issues': [],
            'validation_timestamp': datetime.now().isoformat()
        }
        
        # 检查系统初始化
        if config.is_initialized():
            validation_result['system_initialized'] = True
        else:
            validation_result['validation_issues'].append("系统未初始化，需要运行 pm setup")
            
        # 检查项目文件夹配置
        if config.project_folders:
            validation_result['project_folders_configured'] = True
            validation_result['configured_folders'] = config.project_folders
            
            # 检查文件夹可访问性
            accessible_folders = []
            inaccessible_folders = []
            
            for folder in config.project_folders:
                try:
                    from pathlib import Path
                    folder_path = Path(folder)
                    if folder_path.exists() and folder_path.is_dir():
                        accessible_folders.append(folder)
                    else:
                        inaccessible_folders.append(folder)
                except Exception as e:
                    inaccessible_folders.append(f"{folder} (错误: {str(e)})")
                    
            if accessible_folders:
                validation_result['project_folders_accessible'] = True
                validation_result['accessible_folders'] = accessible_folders
            else:
                validation_result['validation_issues'].append("所有项目文件夹都无法访问")
                
            if inaccessible_folders:
                validation_result['inaccessible_folders'] = inaccessible_folders
                validation_result['validation_issues'].append(f"部分文件夹无法访问: {inaccessible_folders}")
                
        else:
            validation_result['validation_issues'].append("未配置项目文件夹，需要运行 pm setup")
            
        # 检查项目可发现性
        if validation_result['system_initialized'] and validation_result['project_folders_accessible']:
            try:
                agent = ProjectManagerAgent(config)
                projects = agent.discover_projects(force_rescan=False)
                if projects:
                    validation_result['projects_discoverable'] = True
                    validation_result['discoverable_projects_count'] = len(projects)
                    validation_result['discoverable_project_names'] = [p.name for p in projects]
                else:
                    validation_result['validation_issues'].append("未发现任何项目，检查是否存在 PROJECT_STATUS.md 文件")
                    
            except Exception as e:
                validation_result['validation_issues'].append(f"项目发现过程出错: {str(e)}")
                
        # 确定整体验证状态
        all_checks_passed = (
            validation_result['system_initialized'] and 
            validation_result['project_folders_configured'] and 
            validation_result['project_folders_accessible'] and
            validation_result['projects_discoverable']
        )
        
        if all_checks_passed:
            validation_result['overall_status'] = 'ready'
            message = "项目更新前置条件验证通过"
            logger.info("项目更新前置条件验证通过")
            return True, message, validation_result
        else:
            validation_result['overall_status'] = 'issues_found'
            issues_count = len(validation_result['validation_issues'])
            message = f"发现 {issues_count} 个验证问题，需要解决后才能进行项目更新"
            logger.warning("项目更新前置条件验证失败", issues_count=issues_count)
            return False, message, validation_result
            
    except Exception as e:
        logger.error("验证项目更新前置条件失败", error=str(e))
        return False, f"验证过程出错: {str(e)}", None


def analyze_update_performance() -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    分析项目更新性能
    
    Returns:
        Tuple[bool, str, Optional[Dict[str, Any]]]: (成功状态, 消息, 性能分析)
    """
    try:
        logger.info("分析项目更新性能")
        
        config = PMConfig()
        
        if not config.is_initialized():
            return False, "系统未初始化", None
            
        agent = ProjectManagerAgent(config)
        
        # 获取缓存统计
        cache_size = len(getattr(agent, '_project_cache', {}))
        last_scan_time = getattr(agent, '_last_scan_time', None)
        
        # 发现项目（不强制重新扫描，用于性能测试）
        from datetime import datetime
        start_time = datetime.now()
        projects = agent.discover_projects(force_rescan=False)
        discovery_time = (datetime.now() - start_time).total_seconds()
        
        # 计算缓存命中率
        cache_hit_rate = (cache_size / max(len(projects), 1)) * 100 if projects else 0
        
        # 估算更新性能
        estimated_update_time_per_project = 0.5  # 秒
        estimated_total_update_time = len(projects) * estimated_update_time_per_project
        
        performance_analysis = {
            'total_projects': len(projects),
            'cache_size': cache_size,
            'cache_hit_rate': cache_hit_rate,
            'discovery_time_seconds': discovery_time,
            'last_scan_time': last_scan_time.isoformat() if last_scan_time else None,
            'estimated_update_time_per_project': estimated_update_time_per_project,
            'estimated_total_update_time': estimated_total_update_time,
            'performance_metrics': {
                'discovery_speed': 'fast' if discovery_time < 1.0 else 'slow' if discovery_time > 5.0 else 'normal',
                'cache_efficiency': 'high' if cache_hit_rate > 80 else 'low' if cache_hit_rate < 50 else 'medium',
                'project_count_level': 'small' if len(projects) < 10 else 'large' if len(projects) > 50 else 'medium'
            },
            'optimization_suggestions': [],
            'analysis_timestamp': datetime.now().isoformat()
        }
        
        # 生成优化建议
        if cache_hit_rate < 50:
            performance_analysis['optimization_suggestions'].append("缓存命中率较低，建议减少强制刷新频率")
            
        if discovery_time > 3.0:
            performance_analysis['optimization_suggestions'].append("项目发现速度较慢，考虑优化项目文件夹结构")
            
        if len(projects) > 100:
            performance_analysis['optimization_suggestions'].append("项目数量较多，考虑分批更新以提升性能")
            
        if estimated_total_update_time > 60:
            performance_analysis['optimization_suggestions'].append("预计总更新时间较长，建议使用并行更新")
            
        if not performance_analysis['optimization_suggestions']:
            performance_analysis['optimization_suggestions'].append("性能表现良好，继续保持当前配置")
            
        logger.info("项目更新性能分析完成", 
                   cache_hit_rate=cache_hit_rate,
                   discovery_time=discovery_time)
        return True, f"性能分析完成，缓存命中率 {cache_hit_rate:.1f}%", performance_analysis
        
    except Exception as e:
        logger.error("项目更新性能分析失败", error=str(e))
        return False, f"性能分析失败: {str(e)}", None