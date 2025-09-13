"""Configuration management for PersonalManager."""

import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import yaml
from pydantic_settings import BaseSettings
from pydantic import validator
from rich.console import Console

console = Console()


class PMConfig(BaseSettings):
    """PersonalManager配置管理类"""
    
    # 基础路径配置
    home_dir: Path = Path.home()
    config_dir: Path = Path.home() / ".personalmanager"
    config_file: Path = Path.home() / ".personalmanager" / "config.yaml"
    data_dir: Path = Path.home() / ".personalmanager" / "data"
    
    # 用户偏好配置
    work_hours_start: int = 9
    work_hours_end: int = 18
    timezone: str = "Asia/Shanghai"
    language: str = "zh-CN"
    
    # 项目配置
    projects_root: str = str(Path.home() / "projects")
    project_folders: List[str] = []
    default_project_folder: Optional[str] = None
    
    # 书籍理论模块配置
    enabled_book_modules: List[str] = [
        "gtd",  # Getting Things Done
        "atomic_habits",  # 原子习惯
        "deep_work",  # 深度工作
    ]
    
    # 精力管理配置（基于《全力以赴》）
    energy_tracking_enabled: bool = True
    energy_peak_hours: List[int] = [9, 10, 11, 14, 15]
    energy_low_hours: List[int] = [13, 17, 18]
    
    # AI工具配置
    enable_ai_tools: bool = True
    ai_tools_enabled: bool = True  # 向后兼容
    claude_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    
    # Google集成配置
    enable_google_integration: bool = False
    
    # 语言偏好
    preferred_language: str = "zh"
    
    # 隐私与数据配置
    data_retention_days: int = 365
    backup_enabled: bool = True
    cloud_sync_enabled: bool = False  # 默认关闭云同步，确保隐私
    
    class Config:
        env_prefix = "PM_"
        case_sensitive = False
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._ensure_directories()
        self.load_from_file()
    
    def _ensure_directories(self) -> None:
        """确保必要的目录存在"""
        self.config_dir.mkdir(exist_ok=True)
        self.data_dir.mkdir(exist_ok=True)
        (self.data_dir / "projects").mkdir(exist_ok=True)
        (self.data_dir / "tasks").mkdir(exist_ok=True)
        (self.data_dir / "habits").mkdir(exist_ok=True)
        (self.data_dir / "logs").mkdir(exist_ok=True)
        (self.data_dir / "tokens").mkdir(exist_ok=True)
    
    def is_initialized(self) -> bool:
        """检查系统是否已初始化"""
        # 主要检查配置文件是否存在，同时确保基本配置有效
        return (self.config_file.exists() and 
                hasattr(self, 'projects_root') and 
                self.projects_root and 
                Path(self.projects_root).exists())
    
    def load_from_file(self) -> None:
        """从配置文件加载设置"""
        if not self.config_file.exists():
            return
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f) or {}
            
            # 更新配置
            for key, value in config_data.items():
                if hasattr(self, key):
                    setattr(self, key, value)
                    
        except Exception as e:
            console.print(f"[yellow]⚠️  加载配置文件时出错: {e}")
    
    def save_to_file(self) -> bool:
        """保存配置到文件"""
        config_data = {
            "work_hours_start": self.work_hours_start,
            "work_hours_end": self.work_hours_end,
            "timezone": self.timezone,
            "language": self.language,
            "projects_root": self.projects_root,
            "project_folders": self.project_folders,
            "default_project_folder": self.default_project_folder,
            "enabled_book_modules": self.enabled_book_modules,
            "energy_tracking_enabled": self.energy_tracking_enabled,
            "energy_peak_hours": self.energy_peak_hours,
            "energy_low_hours": self.energy_low_hours,
            "enable_ai_tools": self.enable_ai_tools,
            "ai_tools_enabled": self.ai_tools_enabled,
            "enable_google_integration": self.enable_google_integration,
            "preferred_language": self.preferred_language,
            "data_retention_days": self.data_retention_days,
            "backup_enabled": self.backup_enabled,
            "cloud_sync_enabled": self.cloud_sync_enabled,
        }
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, 
                         allow_unicode=True, sort_keys=False)
            return True
        except Exception as e:
            console.print(f"[red]❌ 保存配置文件时出错: {e}")
            return False
    
    def reset_to_defaults(self) -> None:
        """重置配置为默认值"""
        self.work_hours_start = 9
        self.work_hours_end = 18
        self.timezone = "Asia/Shanghai"
        self.language = "zh-CN"
        self.projects_root = str(Path.home() / "projects")
        self.project_folders = []
        self.default_project_folder = None
        self.enabled_book_modules = ["gtd", "atomic_habits", "deep_work"]
        self.energy_tracking_enabled = True
        self.energy_peak_hours = [9, 10, 11, 14, 15]
        self.energy_low_hours = [13, 17, 18]
        self.enable_ai_tools = True
        self.ai_tools_enabled = True
        self.enable_google_integration = False
        self.preferred_language = "zh"
        self.data_retention_days = 365
        self.backup_enabled = True
        self.cloud_sync_enabled = False
    
    def add_project_folder(self, folder_path: str) -> None:
        """添加项目文件夹"""
        path = Path(folder_path).resolve()
        if path.exists() and path.is_dir():
            path_str = str(path)
            if path_str not in self.project_folders:
                self.project_folders.append(path_str)
                if not self.default_project_folder:
                    self.default_project_folder = path_str
                self.save_to_file()
        else:
            raise ValueError(f"文件夹路径不存在或不是目录: {folder_path}")
    
    def get_data_storage_info(self) -> Dict[str, Any]:
        """获取数据存储信息（用于隐私说明）"""
        return {
            "storage_location": str(self.data_dir),
            "config_location": str(self.config_file),
            "cloud_sync_enabled": self.cloud_sync_enabled,
            "backup_enabled": self.backup_enabled,
            "data_retention_days": self.data_retention_days,
            "estimated_storage_size": self._calculate_storage_size()
        }
    
    def _calculate_storage_size(self) -> str:
        """计算当前数据存储大小"""
        try:
            total_size = 0
            for path in self.data_dir.rglob('*'):
                if path.is_file():
                    total_size += path.stat().st_size
            
            # 转换为人类可读格式
            if total_size < 1024:
                return f"{total_size} B"
            elif total_size < 1024 * 1024:
                return f"{total_size / 1024:.1f} KB"
            else:
                return f"{total_size / (1024 * 1024):.1f} MB"
        except:
            return "未知"