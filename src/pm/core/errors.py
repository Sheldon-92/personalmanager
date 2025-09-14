"""Standardized error codes and messages for PersonalManager.

Implements P2-04: Error and logging standardization
with unified error codes, messages, and suggestions.
"""

from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass


class ErrorCode(Enum):
    """PersonalManager标准错误代码"""
    
    # E1xxx: 配置与初始化错误
    E1001 = ("E1001", "系统未初始化", "请运行 'pm setup' 初始化系统配置")
    E1002 = ("E1002", "数据目录权限不足", "请检查数据目录权限，建议运行 'chmod 755 ~/.personalmanager'")
    E1003 = ("E1003", "配置文件缺失", "配置文件不存在或损坏，请运行 'pm setup --reset' 重新配置")
    E1004 = ("E1004", "配置文件格式错误", "配置文件格式不正确，请运行 'pm doctor' 检查并修复")
    E1005 = ("E1005", "数据目录创建失败", "无法创建数据目录，请检查磁盘空间和权限")
    
    # E2xxx: 项目与任务错误  
    E2001 = ("E2001", "项目根目录不存在", "请检查配置中的项目根目录路径，或运行 'pm setup' 重新配置")
    E2002 = ("E2002", "项目文件无法访问", "项目文件不存在或无权限访问，请检查文件路径和权限")
    E2003 = ("E2003", "任务数据损坏", "任务数据文件损坏，请运行 'pm privacy backup' 备份后重新导入")
    E2004 = ("E2004", "项目配置无效", "项目配置文件格式错误，请参考文档修正配置")
    
    # E3xxx: 外部服务错误
    E3001 = ("E3001", "Google服务未配置", "请运行 'pm auth login google' 或在设置中禁用Google集成")
    E3002 = ("E3002", "Google认证过期", "Google认证已过期，请运行 'pm auth login google' 重新认证")
    E3003 = ("E3003", "网络连接失败", "无法连接外部服务，请检查网络连接或使用离线模式")
    E3004 = ("E3004", "API配额超限", "外部服务API调用超限，请稍后重试或升级服务计划")
    
    # E4xxx: 运行时错误
    E4001 = ("E4001", "磁盘空间不足", "可用磁盘空间不足，请清理磁盘空间或更改数据存储位置")
    E4002 = ("E4002", "内存不足", "系统内存不足，请关闭其他应用程序或减少数据处理量")
    E4003 = ("E4003", "文件锁定冲突", "数据文件被其他进程锁定，请确保没有其他PersonalManager实例运行")
    E4004 = ("E4004", "数据备份失败", "无法创建数据备份，请检查目标目录权限和磁盘空间")
    
    def __init__(self, code: str, message: str, suggestion: str):
        self.code = code
        self.message = message
        self.suggestion = suggestion


@dataclass
class PMError:
    """PersonalManager标准错误类"""
    error_code: ErrorCode
    context: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    
    def __str__(self) -> str:
        """格式化错误消息"""
        base_msg = f"{self.error_code.code}: {self.error_code.message}"
        
        if self.context:
            base_msg += f" ({self.context})"
            
        return base_msg
    
    def get_full_message(self) -> str:
        """获取完整错误消息，包含建议"""
        error_msg = str(self)
        suggestion_msg = f"建议: {self.error_code.suggestion}"
        
        return f"{error_msg}\n{suggestion_msg}"
    
    def get_dict(self) -> Dict[str, Any]:
        """获取错误的字典表示（用于JSON序列化）"""
        result = {
            "error_code": self.error_code.code,
            "message": self.error_code.message,
            "suggestion": self.error_code.suggestion
        }
        
        if self.context:
            result["context"] = self.context
            
        if self.details:
            result["details"] = self.details
            
        return result


def raise_pm_error(error_code: ErrorCode, context: Optional[str] = None, 
                   details: Optional[Dict[str, Any]] = None) -> None:
    """抛出PersonalManager标准错误"""
    error = PMError(error_code, context, details)
    raise Exception(error.get_full_message())


def format_error_message(error_code: ErrorCode, context: Optional[str] = None) -> str:
    """格式化错误消息（不抛出异常）"""
    error = PMError(error_code, context)
    return error.get_full_message()


def check_system_initialized() -> Optional[PMError]:
    """检查系统是否已初始化"""
    try:
        from pm.core.config import PMConfig
        config = PMConfig()
        if not config.is_initialized():
            return PMError(ErrorCode.E1001)
    except Exception:
        return PMError(ErrorCode.E1003, "配置加载失败")
    
    return None


def check_data_directory_permissions() -> Optional[PMError]:
    """检查数据目录权限"""
    try:
        from pm.core.config import PMConfig
        import os
        
        config = PMConfig()
        data_dir = config.data_dir
        
        if not data_dir.exists():
            return PMError(ErrorCode.E1005, f"数据目录不存在: {data_dir}")
        
        # 检查写权限
        test_file = data_dir / ".write_test"
        try:
            test_file.write_text("test")
            test_file.unlink()
        except Exception:
            return PMError(ErrorCode.E1002, f"数据目录: {data_dir}")
            
    except Exception as e:
        return PMError(ErrorCode.E1004, f"权限检查失败: {str(e)}")
    
    return None


def check_projects_root() -> Optional[PMError]:
    """检查项目根目录"""
    try:
        from pm.core.config import PMConfig
        from pathlib import Path
        
        config = PMConfig()
        if not hasattr(config, 'projects_root') or not config.projects_root:
            return PMError(ErrorCode.E2001, "项目根目录未配置")
            
        projects_root = Path(config.projects_root)
        if not projects_root.exists():
            return PMError(ErrorCode.E2001, f"项目根目录不存在: {projects_root}")
            
    except Exception as e:
        return PMError(ErrorCode.E2004, f"项目根目录检查失败: {str(e)}")
    
    return None


# 错误检查函数映射（用于批量检查）
SYSTEM_CHECKS = {
    "system_initialized": check_system_initialized,
    "data_directory_permissions": check_data_directory_permissions,  
    "projects_root": check_projects_root,
}