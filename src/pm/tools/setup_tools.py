"""系统设置AI可调用工具函数 - Sprint 13架构重构

这些函数被设计为独立的、可供AI直接调用的工具函数
不依赖CLI框架，实现pm setup命令的核心逻辑
"""

import structlog
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

from pm.core.config import PMConfig

logger = structlog.get_logger()


# ========== 核心工具函数 ==========

def initialize_system(
    work_start: Optional[int] = None,
    work_end: Optional[int] = None,
    projects_root: Optional[str] = None,
    data_dir: Optional[str] = None,
    enable_ai_tools: bool = True,
    enable_google_integration: bool = False,
    preferred_language: str = "zh",
    enabled_book_modules: Optional[List[str]] = None,
    energy_tracking_enabled: Optional[bool] = None,
    energy_peak_hours: Optional[List[int]] = None,
    energy_low_hours: Optional[List[int]] = None,
    config: Optional[PMConfig] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """初始化PersonalManager系统
    
    Args:
        work_start: 工作开始时间(小时，0-23)
        work_end: 工作结束时间(小时，0-23)
        projects_root: 项目根目录路径
        data_dir: 数据目录路径
        enable_ai_tools: 是否启用AI工具
        enable_google_integration: 是否启用Google集成
        preferred_language: 首选语言 (zh/en)
        enabled_book_modules: 启用的书籍理论模块列表
        energy_tracking_enabled: 是否启用精力管理
        energy_peak_hours: 精力高峰时段列表
        energy_low_hours: 精力低谷时段列表
        config: 配置对象
        
    Returns:
        Tuple[成功标志, 消息, 配置信息字典]
    """
    try:
        config = config or PMConfig()
        
        # 验证输入参数
        if work_start is not None and not (0 <= work_start <= 23):
            return False, "工作开始时间必须在0-23之间", None
        
        if work_end is not None and not (0 <= work_end <= 23):
            return False, "工作结束时间必须在0-23之间", None
        
        if work_start is not None and work_end is not None and work_start >= work_end:
            return False, "工作开始时间必须早于结束时间", None
        
        # 更新配置
        if work_start is not None:
            config.work_hours_start = work_start
        if work_end is not None:
            config.work_hours_end = work_end
        if projects_root is not None:
            config.projects_root = projects_root
        if data_dir is not None:
            config.data_dir = data_dir
        
        config.enable_ai_tools = enable_ai_tools
        config.enable_google_integration = enable_google_integration
        config.preferred_language = preferred_language
        
        # 更新书籍理论模块配置
        if enabled_book_modules is not None:
            config.enabled_book_modules = enabled_book_modules
        
        # 更新精力管理配置
        if energy_tracking_enabled is not None:
            config.energy_tracking_enabled = energy_tracking_enabled
        if energy_peak_hours is not None:
            # 验证精力时段参数
            if not all(0 <= hour <= 23 for hour in energy_peak_hours):
                return False, "精力高峰时段必须在0-23之间", None
            config.energy_peak_hours = energy_peak_hours
        if energy_low_hours is not None:
            # 验证精力时段参数
            if not all(0 <= hour <= 23 for hour in energy_low_hours):
                return False, "精力低谷时段必须在0-23之间", None
            config.energy_low_hours = energy_low_hours
        
        # 创建必要的目录
        success, create_msg = _create_system_directories(config)
        if not success:
            return False, f"创建系统目录失败: {create_msg}", None

        # 确保 projects_root 在 project_folders 中
        if config.projects_root and config.projects_root not in config.project_folders:
            config.project_folders.append(config.projects_root)

        # 保存配置
        success = config.save_to_file()
        if not success:
            return False, "保存配置文件失败", None
        
        # 返回配置信息
        config_info = {
            "config_path": str(config.config_file),
            "data_directory": config.data_dir,
            "projects_root": config.projects_root,
            "work_hours": f"{config.work_hours_start}:00-{config.work_hours_end}:00",
            "ai_tools_enabled": config.enable_ai_tools,
            "google_integration_enabled": config.enable_google_integration,
            "language": config.preferred_language,
            "enabled_book_modules": config.enabled_book_modules,
            "energy_tracking_enabled": config.energy_tracking_enabled,
            "energy_peak_hours": config.energy_peak_hours,
            "energy_low_hours": config.energy_low_hours
        }
        
        logger.info("System initialized via tool function", 
                   config_path=str(config.config_file),
                   ai_enabled=config.enable_ai_tools,
                   google_enabled=config.enable_google_integration)
        
        return True, "PersonalManager系统初始化成功", config_info
        
    except Exception as e:
        error_msg = f"系统初始化时发生错误: {str(e)}"
        logger.error("initialize_system tool function failed", error=str(e))
        return False, error_msg, None


def get_system_status(
    config: Optional[PMConfig] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """获取系统状态信息
    
    Args:
        config: 配置对象
        
    Returns:
        Tuple[成功标志, 消息, 状态信息字典]
    """
    try:
        config = config or PMConfig()
        
        # 检查配置文件是否存在
        config_exists = config.config_file.exists()
        if config_exists:
            config.load_from_file()
        
        # 检查关键目录
        data_dir_exists = Path(config.data_dir).exists()
        tasks_dir_exists = Path(config.data_dir, "tasks").exists()
        habits_dir_exists = Path(config.data_dir, "habits").exists()
        
        # 检查项目根目录
        projects_root_exists = Path(config.projects_root).exists() if config.projects_root else False
        
        # 统计数据文件
        tasks_files = list(Path(config.data_dir, "tasks").glob("*.json")) if tasks_dir_exists else []
        habits_files = list(Path(config.data_dir, "habits").glob("*.json")) if habits_dir_exists else []
        
        # 系统健康度评估
        health_score = 0
        health_issues = []
        
        if config_exists:
            health_score += 30
        else:
            health_issues.append("配置文件不存在")
        
        if data_dir_exists:
            health_score += 25
        else:
            health_issues.append("数据目录不存在")
        
        if tasks_dir_exists:
            health_score += 20
        else:
            health_issues.append("任务数据目录不存在")
        
        if habits_dir_exists:
            health_score += 15
        else:
            health_issues.append("习惯数据目录不存在")
        
        if projects_root_exists:
            health_score += 10
        else:
            health_issues.append("项目根目录不存在或未配置")
        
        status_info = {
            "system_initialized": config_exists,
            "health_score": health_score,
            "health_status": "良好" if health_score >= 80 else "一般" if health_score >= 60 else "需要初始化",
            "health_issues": health_issues,
            "configuration": {
                "config_file_exists": config_exists,
                "config_path": str(config.config_file),
                "data_directory": config.data_dir,
                "projects_root": config.projects_root,
                "work_hours": f"{config.work_hours_start}:00-{config.work_hours_end}:00",
                "ai_tools_enabled": config.enable_ai_tools,
                "google_integration_enabled": config.enable_google_integration,
                "language": config.preferred_language
            },
            "directories": {
                "data_dir_exists": data_dir_exists,
                "tasks_dir_exists": tasks_dir_exists,
                "habits_dir_exists": habits_dir_exists,
                "projects_root_exists": projects_root_exists
            },
            "data_files": {
                "task_files_count": len(tasks_files),
                "habit_files_count": len(habits_files)
            }
        }
        
        return True, f"系统状态检查完成，健康度: {health_score}/100", status_info
        
    except Exception as e:
        error_msg = f"获取系统状态时发生错误: {str(e)}"
        logger.error("get_system_status tool function failed", error=str(e))
        return False, error_msg, None


def reset_system(
    keep_data: bool = True,
    config: Optional[PMConfig] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """重置系统配置
    
    Args:
        keep_data: 是否保留用户数据
        config: 配置对象
        
    Returns:
        Tuple[成功标志, 消息, 操作结果字典]
    """
    try:
        config = config or PMConfig()
        
        operations = []
        
        # 备份现有配置（如果存在）
        backup_path = None
        if config.config_file.exists():
            backup_path = config.config_file.with_suffix('.backup')
            import shutil
            shutil.copy2(config.config_file, backup_path)
            operations.append(f"备份现有配置到: {backup_path}")
        
        # 重置配置为默认值
        config.reset_to_defaults()
        
        if not keep_data:
            # 清理数据目录
            import shutil
            data_path = Path(config.data_dir)
            if data_path.exists():
                shutil.rmtree(data_path)
                operations.append(f"清理数据目录: {data_path}")
        
        # 重新创建必要目录
        success, create_msg = _create_system_directories(config)
        if success:
            operations.append("重新创建系统目录结构")
        else:
            return False, f"创建系统目录失败: {create_msg}", None
        
        # 保存重置后的配置
        success = config.save_to_file()
        if not success:
            return False, "保存重置后的配置失败", None
        
        operations.append("保存默认配置")
        
        result_info = {
            "backup_created": backup_path is not None,
            "backup_path": str(backup_path) if backup_path else None,
            "data_kept": keep_data,
            "operations_performed": operations
        }
        
        logger.info("System reset via tool function", 
                   keep_data=keep_data,
                   operations_count=len(operations))
        
        return True, f"系统重置成功，执行了{len(operations)}个操作", result_info
        
    except Exception as e:
        error_msg = f"系统重置时发生错误: {str(e)}"
        logger.error("reset_system tool function failed", error=str(e))
        return False, error_msg, None


def update_preferences(
    work_start: Optional[int] = None,
    work_end: Optional[int] = None,
    enable_ai_tools: Optional[bool] = None,
    enable_google_integration: Optional[bool] = None,
    preferred_language: Optional[str] = None,
    projects_root: Optional[str] = None,
    config: Optional[PMConfig] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """更新用户偏好设置
    
    Args:
        work_start: 工作开始时间
        work_end: 工作结束时间
        enable_ai_tools: 是否启用AI工具
        enable_google_integration: 是否启用Google集成
        preferred_language: 首选语言
        projects_root: 项目根目录
        config: 配置对象
        
    Returns:
        Tuple[成功标志, 消息, 更新信息字典]
    """
    try:
        config = config or PMConfig()
        
        # 加载现有配置
        if config.config_file.exists():
            config.load_from_file()
        else:
            return False, "系统尚未初始化，请先运行初始化", None
        
        changes = []
        
        # 更新工作时间
        if work_start is not None:
            if not (0 <= work_start <= 23):
                return False, "工作开始时间必须在0-23之间", None
            old_start = config.work_hours_start
            config.work_hours_start = work_start
            changes.append(f"工作开始时间: {old_start}:00 → {work_start}:00")
        
        if work_end is not None:
            if not (0 <= work_end <= 23):
                return False, "工作结束时间必须在0-23之间", None
            old_end = config.work_hours_end
            config.work_hours_end = work_end
            changes.append(f"工作结束时间: {old_end}:00 → {work_end}:00")
        
        # 验证工作时间逻辑
        if config.work_hours_start >= config.work_hours_end:
            return False, "工作开始时间必须早于结束时间", None
        
        # 更新功能开关
        if enable_ai_tools is not None:
            old_ai = config.enable_ai_tools
            config.enable_ai_tools = enable_ai_tools
            changes.append(f"AI工具: {'启用' if old_ai else '禁用'} → {'启用' if enable_ai_tools else '禁用'}")
        
        if enable_google_integration is not None:
            old_google = config.enable_google_integration
            config.enable_google_integration = enable_google_integration
            changes.append(f"Google集成: {'启用' if old_google else '禁用'} → {'启用' if enable_google_integration else '禁用'}")
        
        # 更新语言设置
        if preferred_language is not None:
            old_lang = config.preferred_language
            config.preferred_language = preferred_language
            changes.append(f"首选语言: {old_lang} → {preferred_language}")
        
        # 更新项目根目录
        if projects_root is not None:
            old_root = config.projects_root
            config.projects_root = projects_root
            changes.append(f"项目根目录: {old_root} → {projects_root}")
        
        if not changes:
            return True, "没有任何设置需要更新", {"changes_made": []}
        
        # 保存更新后的配置
        success = config.save_to_file()
        if not success:
            return False, "保存配置更新失败", None
        
        update_info = {
            "changes_made": changes,
            "updated_config": {
                "work_hours": f"{config.work_hours_start}:00-{config.work_hours_end}:00",
                "ai_tools_enabled": config.enable_ai_tools,
                "google_integration_enabled": config.enable_google_integration,
                "language": config.preferred_language,
                "projects_root": config.projects_root
            }
        }
        
        logger.info("Preferences updated via tool function", 
                   changes_count=len(changes))
        
        return True, f"成功更新{len(changes)}项设置", update_info
        
    except Exception as e:
        error_msg = f"更新偏好设置时发生错误: {str(e)}"
        logger.error("update_preferences tool function failed", error=str(e))
        return False, error_msg, None


def validate_system_setup(
    config: Optional[PMConfig] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """验证系统设置完整性
    
    Args:
        config: 配置对象
        
    Returns:
        Tuple[成功标志, 消息, 验证结果字典]
    """
    try:
        config = config or PMConfig()
        
        validation_results = {
            "passed": [],
            "failed": [],
            "warnings": [],
            "overall_status": "unknown"
        }
        
        # 1. 检查配置文件
        if config.config_file.exists():
            config.load_from_file()
            validation_results["passed"].append("配置文件存在且可读取")
        else:
            validation_results["failed"].append("配置文件不存在")
        
        # 2. 检查数据目录结构
        data_dir = Path(config.data_dir)
        if data_dir.exists():
            validation_results["passed"].append("数据目录存在")
            
            # 检查子目录
            required_subdirs = ["tasks", "habits", "tokens"]
            for subdir in required_subdirs:
                subdir_path = data_dir / subdir
                if subdir_path.exists():
                    validation_results["passed"].append(f"{subdir}目录存在")
                else:
                    validation_results["warnings"].append(f"{subdir}目录不存在（将在需要时创建）")
        else:
            validation_results["failed"].append("数据目录不存在")
        
        # 3. 检查项目根目录
        if config.projects_root:
            projects_dir = Path(config.projects_root)
            if projects_dir.exists():
                validation_results["passed"].append("项目根目录存在")
            else:
                validation_results["warnings"].append("项目根目录不存在或无法访问")
        else:
            validation_results["warnings"].append("项目根目录未配置")
        
        # 4. 检查工作时间配置
        if 0 <= config.work_hours_start <= 23 and 0 <= config.work_hours_end <= 23:
            if config.work_hours_start < config.work_hours_end:
                validation_results["passed"].append("工作时间配置有效")
            else:
                validation_results["failed"].append("工作时间配置无效（开始时间不能晚于或等于结束时间）")
        else:
            validation_results["failed"].append("工作时间配置超出有效范围")
        
        # 5. 检查功能模块配置
        if config.enable_ai_tools:
            validation_results["passed"].append("AI工具模块已启用")
        else:
            validation_results["warnings"].append("AI工具模块已禁用")
        
        if config.enable_google_integration:
            validation_results["passed"].append("Google集成模块已启用")
        else:
            validation_results["warnings"].append("Google集成模块已禁用")
        
        # 6. 检查权限
        try:
            # 测试数据目录写权限
            test_file = data_dir / ".write_test"
            test_file.write_text("test")
            test_file.unlink()
            validation_results["passed"].append("数据目录具有写权限")
        except Exception:
            validation_results["failed"].append("数据目录缺少写权限")
        
        # 计算总体状态
        failed_count = len(validation_results["failed"])
        warning_count = len(validation_results["warnings"])
        
        if failed_count == 0:
            if warning_count == 0:
                validation_results["overall_status"] = "excellent"
                status_msg = "系统配置完美"
            else:
                validation_results["overall_status"] = "good"
                status_msg = f"系统配置良好（{warning_count}个警告）"
        elif failed_count <= 2:
            validation_results["overall_status"] = "needs_attention"
            status_msg = f"系统需要关注（{failed_count}个错误，{warning_count}个警告）"
        else:
            validation_results["overall_status"] = "critical"
            status_msg = f"系统存在严重问题（{failed_count}个错误）"
        
        validation_results["summary"] = {
            "total_checks": len(validation_results["passed"]) + len(validation_results["failed"]) + len(validation_results["warnings"]),
            "passed_count": len(validation_results["passed"]),
            "failed_count": len(validation_results["failed"]),
            "warning_count": len(validation_results["warnings"])
        }
        
        return True, status_msg, validation_results
        
    except Exception as e:
        error_msg = f"系统验证时发生错误: {str(e)}"
        logger.error("validate_system_setup tool function failed", error=str(e))
        return False, error_msg, None


# ========== 辅助函数 ==========

def _create_system_directories(config: PMConfig) -> Tuple[bool, str]:
    """创建系统必要的目录结构"""
    try:
        directories_to_create = [
            Path(config.data_dir),
            Path(config.data_dir) / "tasks",
            Path(config.data_dir) / "habits",
            Path(config.data_dir) / "tokens",
            Path(config.data_dir) / "backups",
            Path(config.data_dir) / "logs"
        ]
        
        for directory in directories_to_create:
            directory.mkdir(parents=True, exist_ok=True)
        
        return True, f"成功创建{len(directories_to_create)}个系统目录"
        
    except Exception as e:
        return False, str(e)