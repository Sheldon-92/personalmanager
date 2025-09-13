"""AI可调用的监控工具函数

提供项目文件监控的AI可调用接口，包括：
- 启动/停止文件监控
- 获取监控状态
- 查看监控日志
- 管理监控配置
"""

import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import structlog

from pm.core.config import PMConfig
from pm.agents.file_watcher import FileWatcherAgent, BackgroundFileWatcher

logger = structlog.get_logger(__name__)

# 全局监控实例
_global_watcher: Optional[BackgroundFileWatcher] = None


def start_file_monitoring(
    project_folders: Optional[List[str]] = None,
    enable_notifications: bool = True
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    启动项目文件监控
    
    Args:
        project_folders: 要监控的项目文件夹列表，为空则使用配置中的文件夹
        enable_notifications: 是否启用变化通知
        
    Returns:
        Tuple[bool, str, Optional[Dict[str, Any]]]: (成功状态, 消息, 监控状态信息)
    """
    global _global_watcher
    
    try:
        logger.info("启动文件监控", folders=project_folders)
        
        config = PMConfig()
        
        # 检查系统是否初始化
        if not config.is_initialized():
            return False, "系统未初始化，请先运行 pm setup 进行设置", None
            
        # 确定监控文件夹
        folders_to_monitor = project_folders if project_folders else config.project_folders
        if not folders_to_monitor:
            return False, "未配置项目文件夹，请运行 pm setup 添加项目文件夹", None
            
        # 检查是否已在运行
        if _global_watcher and _global_watcher.get_status()["background_thread_alive"]:
            status = _global_watcher.get_status()
            return True, "文件监控已在运行中", {
                'already_running': True,
                'monitored_folders': status["watched_folders"],
                'start_time': status["start_time"].isoformat() if status.get("start_time") else None
            }
            
        # 验证文件夹存在性
        valid_folders = []
        invalid_folders = []
        
        for folder in folders_to_monitor:
            folder_path = Path(folder)
            if folder_path.exists() and folder_path.is_dir():
                valid_folders.append(str(folder_path.absolute()))
            else:
                invalid_folders.append(folder)
                
        if not valid_folders:
            return False, f"所有项目文件夹都不存在: {invalid_folders}", None
            
        # 初始化后台监控
        _global_watcher = BackgroundFileWatcher(config)
        
        # 添加通知回调（如果启用）
        if enable_notifications:
            notification_logs = []
            
            def notification_callback(notification):
                notification_logs.append({
                    'timestamp': notification["timestamp"].isoformat(),
                    'file_path': notification["file_path"],
                    'status': notification["status"],
                    'message': notification["message"]
                })
                logger.info("文件监控通知", 
                           timestamp=notification["timestamp"],
                           status=notification["status"],
                           message=notification["message"])
                           
            _global_watcher.add_notification_callback(notification_callback)
            
        # 启动监控
        if _global_watcher.start_background_watching():
            status = _global_watcher.get_status()
            
            result = {
                'monitoring_started': True,
                'monitored_folders': valid_folders,
                'invalid_folders': invalid_folders,
                'monitoring_features': [
                    '自动检测 PROJECT_STATUS.md 文件变化',
                    '变化后1分钟内自动更新项目状态', 
                    '支持多项目文件夹同时监控',
                    '实时变化通知'
                ],
                'start_time': datetime.now().isoformat(),
                'background_thread_alive': status["background_thread_alive"],
                'is_watching': status["is_watching"]
            }
            
            logger.info("文件监控启动成功", 
                       folders_count=len(valid_folders))
            return True, f"文件监控已启动，监控 {len(valid_folders)} 个文件夹", result
            
        else:
            return False, "文件监控启动失败，可能的原因：项目文件夹无权限访问或系统不支持文件系统监控", None
            
    except Exception as e:
        logger.error("启动文件监控失败", error=str(e))
        return False, f"启动监控时发生错误: {str(e)}", None


def stop_file_monitoring() -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    停止项目文件监控
    
    Returns:
        Tuple[bool, str, Optional[Dict[str, Any]]]: (成功状态, 消息, 停止信息)
    """
    global _global_watcher
    
    try:
        logger.info("停止文件监控")
        
        if not _global_watcher:
            return True, "文件监控未运行", {'monitoring_was_running': False}
            
        status = _global_watcher.get_status()
        if not status["background_thread_alive"]:
            return True, "文件监控未在运行", {'monitoring_was_running': False}
            
        # 获取停止前的统计信息
        stats = status["stats"]
        stop_info = {
            'monitoring_was_running': True,
            'total_changes_processed': stats["total_changes"],
            'successful_updates': stats["successful_updates"],
            'failed_updates': stats["failed_updates"],
            'monitored_folders': status["watched_folders"],
            'stop_time': datetime.now().isoformat()
        }
        
        # 停止监控
        _global_watcher.stop_background_watching()
        _global_watcher = None
        
        logger.info("文件监控已停止", stats=stats)
        return True, f"文件监控已停止，共处理 {stats['total_changes']} 次变化", stop_info
        
    except Exception as e:
        logger.error("停止文件监控失败", error=str(e))
        return False, f"停止监控时发生错误: {str(e)}", None


def get_monitoring_status() -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    获取监控状态信息
    
    Returns:
        Tuple[bool, str, Optional[Dict[str, Any]]]: (成功状态, 消息, 状态信息)
    """
    global _global_watcher
    
    try:
        logger.info("获取监控状态")
        
        if not _global_watcher:
            return True, "文件监控未启动", {
                'monitoring_status': 'not_started',
                'is_watching': False,
                'background_thread_alive': False,
                'recommendation': '使用 start_file_monitoring() 启动监控'
            }
            
        status = _global_watcher.get_status()
        stats = status["stats"]
        
        # 监控状态分类
        if status["is_watching"] and status["background_thread_alive"]:
            monitoring_status = "running"
            status_message = "监控运行中"
        elif status["background_thread_alive"]:
            monitoring_status = "background_alive"
            status_message = "后台线程活跃但未监控"
        else:
            monitoring_status = "stopped"
            status_message = "监控已停止"
            
        result = {
            'monitoring_status': monitoring_status,
            'is_watching': status["is_watching"],
            'background_thread_alive': status["background_thread_alive"],
            'monitored_folders': status["watched_folders"],
            'monitored_folders_count': len(status["watched_folders"]),
            'statistics': {
                'total_changes': stats["total_changes"],
                'successful_updates': stats["successful_updates"],
                'failed_updates': stats["failed_updates"],
                'last_change_time': stats["last_change_time"].isoformat() if stats["last_change_time"] else None
            },
            'recent_notifications': [
                {
                    'timestamp': notif["timestamp"].isoformat(),
                    'status': notif["status"],
                    'message': notif["message"],
                    'file_path': notif.get("file_path", "")
                }
                for notif in status["recent_notifications"][-10:]  # 最近10条
            ],
            'health_score': _calculate_monitoring_health(stats),
            'recommendations': _generate_monitoring_recommendations(status),
            'status_timestamp': datetime.now().isoformat()
        }
        
        logger.info("监控状态获取完成", status=monitoring_status)
        return True, status_message, result
        
    except Exception as e:
        logger.error("获取监控状态失败", error=str(e))
        return False, f"获取状态时发生错误: {str(e)}", None


def get_monitoring_logs(limit: int = 50) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    获取监控日志
    
    Args:
        limit: 返回的日志条数限制
        
    Returns:
        Tuple[bool, str, Optional[Dict[str, Any]]]: (成功状态, 消息, 日志信息)
    """
    global _global_watcher
    
    try:
        logger.info("获取监控日志", limit=limit)
        
        if not _global_watcher:
            return True, "文件监控未启动，无日志可显示", {
                'logs_available': False,
                'logs': [],
                'message': '文件监控未启动'
            }
            
        notifications = _global_watcher.watcher.get_recent_changes(limit)
        
        logs = []
        for notification in reversed(notifications):  # 最新的在前
            logs.append({
                'timestamp': notification["timestamp"].isoformat(),
                'project_path': notification["project_path"],
                'project_name': Path(notification["project_path"]).name,
                'file_path': notification["file_path"],
                'status': notification["status"],
                'message': notification["message"],
                'success': notification["status"] == "success"
            })
            
        result = {
            'logs_available': True,
            'logs_count': len(logs),
            'logs': logs,
            'limit_applied': limit,
            'logs_timestamp': datetime.now().isoformat()
        }
        
        logger.info("监控日志获取完成", logs_count=len(logs))
        return True, f"获取 {len(logs)} 条监控日志", result
        
    except Exception as e:
        logger.error("获取监控日志失败", error=str(e))
        return False, f"获取日志时发生错误: {str(e)}", None


def restart_file_monitoring(
    project_folders: Optional[List[str]] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    重启文件监控
    
    Args:
        project_folders: 要监控的项目文件夹列表
        
    Returns:
        Tuple[bool, str, Optional[Dict[str, Any]]]: (成功状态, 消息, 重启信息)
    """
    try:
        logger.info("重启文件监控")
        
        restart_info = {
            'restart_initiated': True,
            'restart_timestamp': datetime.now().isoformat()
        }
        
        # 获取停止前的状态
        stop_success, stop_message, stop_data = stop_file_monitoring()
        if stop_data:
            restart_info['previous_status'] = stop_data
            
        # 等待一秒确保完全停止
        time.sleep(1)
        
        # 重新启动
        start_success, start_message, start_data = start_file_monitoring(project_folders)
        
        if start_success:
            restart_info.update({
                'restart_successful': True,
                'new_status': start_data
            })
            logger.info("文件监控重启成功")
            return True, "文件监控重启成功", restart_info
        else:
            restart_info.update({
                'restart_successful': False,
                'start_error': start_message
            })
            return False, f"重启失败: {start_message}", restart_info
            
    except Exception as e:
        logger.error("重启文件监控失败", error=str(e))
        return False, f"重启时发生错误: {str(e)}", None


def configure_monitoring_settings(
    settings: Dict[str, Any]
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    配置监控设置
    
    Args:
        settings: 监控配置设置
            - watch_patterns: 监控的文件模式列表
            - ignore_patterns: 忽略的文件模式列表
            - notification_enabled: 是否启用通知
            - update_delay_seconds: 更新延迟秒数
            
    Returns:
        Tuple[bool, str, Optional[Dict[str, Any]]]: (成功状态, 消息, 配置信息)
    """
    global _global_watcher
    
    try:
        logger.info("配置监控设置", settings=settings)
        
        config = PMConfig()
        
        # 更新配置
        updated_settings = {}
        
        if 'watch_patterns' in settings:
            # 这里应该更新到配置文件，简化实现
            updated_settings['watch_patterns'] = settings['watch_patterns']
            
        if 'ignore_patterns' in settings:
            updated_settings['ignore_patterns'] = settings['ignore_patterns']
            
        if 'notification_enabled' in settings:
            updated_settings['notification_enabled'] = settings['notification_enabled']
            
        if 'update_delay_seconds' in settings:
            updated_settings['update_delay_seconds'] = settings['update_delay_seconds']
            
        # 如果监控正在运行，需要重启以应用新设置
        needs_restart = _global_watcher and _global_watcher.get_status()["background_thread_alive"]
        
        result = {
            'settings_updated': True,
            'updated_settings': updated_settings,
            'needs_restart': needs_restart,
            'configuration_timestamp': datetime.now().isoformat()
        }
        
        if needs_restart:
            result['restart_recommendation'] = '监控正在运行，建议重启以应用新设置'
            
        logger.info("监控设置配置完成", needs_restart=needs_restart)
        return True, f"监控设置已更新{'，建议重启监控以应用设置' if needs_restart else ''}", result
        
    except Exception as e:
        logger.error("配置监控设置失败", error=str(e))
        return False, f"配置设置时发生错误: {str(e)}", None


def get_monitoring_health_report() -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    获取监控健康报告
    
    Returns:
        Tuple[bool, str, Optional[Dict[str, Any]]]: (成功状态, 消息, 健康报告)
    """
    global _global_watcher
    
    try:
        logger.info("生成监控健康报告")
        
        if not _global_watcher:
            return True, "文件监控未运行，无法生成健康报告", {
                'monitoring_running': False,
                'health_status': 'not_available'
            }
            
        status = _global_watcher.get_status()
        stats = status["stats"]
        
        # 计算健康指标
        health_score = _calculate_monitoring_health(stats)
        
        # 性能分析
        total_changes = stats["total_changes"]
        successful_rate = (stats["successful_updates"] / max(total_changes, 1)) * 100
        failed_rate = (stats["failed_updates"] / max(total_changes, 1)) * 100
        
        # 确定健康等级
        if health_score >= 0.9:
            health_level = "excellent"
        elif health_score >= 0.7:
            health_level = "good"
        elif health_score >= 0.5:
            health_level = "warning"
        else:
            health_level = "critical"
            
        # 生成改进建议
        improvement_suggestions = _generate_improvement_suggestions(status, health_score)
        
        result = {
            'monitoring_running': True,
            'health_status': health_level,
            'health_score': health_score,
            'performance_metrics': {
                'total_changes_processed': total_changes,
                'successful_update_rate': successful_rate,
                'failed_update_rate': failed_rate,
                'monitored_folders_count': len(status["watched_folders"]),
                'average_response_time': 'N/A'  # 需要实现响应时间统计
            },
            'system_status': {
                'background_thread_alive': status["background_thread_alive"],
                'is_watching': status["is_watching"],
                'last_activity': stats["last_change_time"].isoformat() if stats["last_change_time"] else None
            },
            'improvement_suggestions': improvement_suggestions,
            'monitoring_recommendations': _generate_monitoring_recommendations(status),
            'report_timestamp': datetime.now().isoformat()
        }
        
        logger.info("监控健康报告生成完成", 
                   health_level=health_level,
                   health_score=health_score)
        return True, f"监控健康状态: {health_level}，评分 {health_score:.2f}", result
        
    except Exception as e:
        logger.error("生成监控健康报告失败", error=str(e))
        return False, f"生成报告时发生错误: {str(e)}", None


def _calculate_monitoring_health(stats: Dict[str, Any]) -> float:
    """计算监控健康评分 (0.0-1.0)"""
    
    total_changes = stats["total_changes"]
    successful_updates = stats["successful_updates"]
    failed_updates = stats["failed_updates"]
    
    if total_changes == 0:
        return 0.8  # 无活动但系统正常
        
    # 成功率评分
    success_rate = successful_updates / total_changes
    
    # 失败率惩罚
    failure_penalty = (failed_updates / total_changes) * 0.3
    
    # 活动性评分
    last_change_time = stats.get("last_change_time")
    activity_score = 1.0
    if last_change_time:
        time_since_last = datetime.now() - last_change_time
        if time_since_last > timedelta(days=7):
            activity_score = 0.7  # 长时间无活动
        elif time_since_last > timedelta(days=1):
            activity_score = 0.9
            
    # 综合评分
    health_score = (success_rate * 0.6 + activity_score * 0.4) - failure_penalty
    
    return max(0.0, min(1.0, health_score))


def _generate_monitoring_recommendations(status: Dict[str, Any]) -> List[str]:
    """生成监控建议"""
    
    recommendations = []
    stats = status["stats"]
    
    if not status["is_watching"]:
        recommendations.append("监控未激活，建议启动文件监控")
        
    if not status["background_thread_alive"]:
        recommendations.append("后台监控线程未运行，建议重启监控服务")
        
    if stats["failed_updates"] > stats["successful_updates"] * 0.2:
        recommendations.append("失败更新率较高，建议检查项目文件权限和格式")
        
    if len(status["watched_folders"]) == 0:
        recommendations.append("未配置监控文件夹，建议添加项目文件夹")
        
    last_change_time = stats.get("last_change_time")
    if last_change_time and datetime.now() - last_change_time > timedelta(days=3):
        recommendations.append("长时间无文件变化，建议检查项目活跃度")
        
    if not recommendations:
        recommendations.append("监控运行正常，保持当前配置")
        
    return recommendations


def _generate_improvement_suggestions(
    status: Dict[str, Any], 
    health_score: float
) -> List[str]:
    """生成改进建议"""
    
    suggestions = []
    
    if health_score < 0.5:
        suggestions.extend([
            "监控健康状态较差，建议重启监控服务",
            "检查项目文件夹的读写权限",
            "验证PROJECT_STATUS.md文件格式是否正确"
        ])
    elif health_score < 0.7:
        suggestions.extend([
            "适当优化监控配置以提升性能",
            "定期检查监控日志以发现潜在问题"
        ])
    elif health_score < 0.9:
        suggestions.append("监控表现良好，可以考虑增加更多监控文件夹")
    else:
        suggestions.append("监控表现优秀，继续保持当前配置")
        
    return suggestions