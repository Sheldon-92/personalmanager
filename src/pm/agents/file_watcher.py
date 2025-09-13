"""File system monitoring agent for PROJECT_STATUS.md files."""

import time
from pathlib import Path
from typing import Dict, List, Callable, Optional, Set
from datetime import datetime
from threading import Thread, Event
import structlog
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent

from pm.core.config import PMConfig
from pm.agents.project_manager import ProjectManagerAgent

logger = structlog.get_logger()


class ProjectStatusFileHandler(FileSystemEventHandler):
    """PROJECT_STATUS.md文件变化处理器"""
    
    def __init__(self, callback: Callable[[str], None]):
        self.callback = callback
        self.last_processed: Dict[str, float] = {}
        
    def on_modified(self, event):
        """文件修改事件处理"""
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        if file_path.name == "PROJECT_STATUS.md":
            self._handle_file_change(str(file_path))
    
    def on_created(self, event):
        """文件创建事件处理"""
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        if file_path.name == "PROJECT_STATUS.md":
            self._handle_file_change(str(file_path))
    
    def _handle_file_change(self, file_path: str):
        """处理文件变化"""
        
        current_time = time.time()
        
        # 防止重复处理（1秒内的重复事件）
        if file_path in self.last_processed:
            if current_time - self.last_processed[file_path] < 1.0:
                return
        
        self.last_processed[file_path] = current_time
        
        logger.info("PROJECT_STATUS.md file changed", path=file_path)
        
        # 延迟处理，等待文件写入完成
        time.sleep(0.5)
        
        try:
            self.callback(file_path)
        except Exception as e:
            logger.error("Failed to process file change", path=file_path, error=str(e))


class FileWatcherAgent:
    """文件系统监控Agent
    
    根据US-003验收标准实现：
    - 文件系统监控能检测.md文件变化
    - 变化后1分钟内更新内部状态
    - 支持多个项目文件夹同时监控
    - 提供变化通知功能
    """
    
    def __init__(self, config: Optional[PMConfig] = None):
        self.config = config or PMConfig()
        self.project_agent = ProjectManagerAgent(self.config)
        
        self.observer = Observer()
        self.is_watching = False
        self.watch_handles: Dict[str, any] = {}
        
        # 变化通知队列
        self.change_notifications: List[Dict] = []
        self.notification_callbacks: List[Callable] = []
        
        # 统计信息
        self.stats = {
            "total_changes": 0,
            "successful_updates": 0,
            "failed_updates": 0,
            "last_change_time": None,
            "watched_folders": 0
        }
        
        logger.info("FileWatcherAgent initialized")
    
    def start_watching(self) -> bool:
        """开始监控文件系统变化
        
        Returns:
            是否成功启动监控
        """
        
        if self.is_watching:
            logger.warning("File watcher already running")
            return True
        
        if not self.config.project_folders:
            logger.error("No project folders configured for watching")
            return False
        
        try:
            # 为每个项目文件夹设置监控
            for folder_path in self.config.project_folders:
                folder = Path(folder_path)
                if not folder.exists():
                    logger.warning("Project folder not found, skipping", path=folder_path)
                    continue
                
                # 创建文件处理器
                handler = ProjectStatusFileHandler(self._on_file_changed)
                
                # 添加监控
                watch_handle = self.observer.add_watch(
                    str(folder), 
                    handler, 
                    recursive=True
                )
                
                self.watch_handles[folder_path] = watch_handle
                logger.info("Started watching project folder", path=folder_path)
            
            # 启动观察者
            self.observer.start()
            self.is_watching = True
            self.stats["watched_folders"] = len(self.watch_handles)
            
            logger.info("File system monitoring started", 
                       folders=len(self.watch_handles))
            
            return True
            
        except Exception as e:
            logger.error("Failed to start file watching", error=str(e))
            return False
    
    def stop_watching(self) -> None:
        """停止文件系统监控"""
        
        if not self.is_watching:
            return
        
        try:
            # 移除所有监控
            for folder_path, watch_handle in self.watch_handles.items():
                self.observer.unschedule(watch_handle)
                logger.info("Stopped watching project folder", path=folder_path)
            
            # 停止观察者
            self.observer.stop()
            self.observer.join(timeout=5.0)
            
            self.is_watching = False
            self.watch_handles.clear()
            
            logger.info("File system monitoring stopped")
            
        except Exception as e:
            logger.error("Error stopping file watcher", error=str(e))
    
    def _on_file_changed(self, file_path: str) -> None:
        """处理PROJECT_STATUS.md文件变化"""
        
        change_time = datetime.now()
        self.stats["total_changes"] += 1
        self.stats["last_change_time"] = change_time
        
        try:
            # 解析文件路径，确定项目名
            project_path = Path(file_path).parent
            
            # 更新项目状态
            result = self.project_agent.update_project_status()
            
            if result["updated"] > 0:
                self.stats["successful_updates"] += 1
                status = "success"
                message = f"项目状态已更新: {', '.join(result['updated_projects'])}"
                
                logger.info("Project status updated due to file change", 
                           file=file_path, 
                           updated=result["updated_projects"])
            else:
                self.stats["failed_updates"] += 1
                status = "failed"
                message = f"更新失败: {', '.join(result['errors'])}"
                
                logger.error("Failed to update project status", 
                           file=file_path, 
                           errors=result["errors"])
            
            # 创建变化通知
            notification = {
                "timestamp": change_time,
                "file_path": file_path,
                "project_path": str(project_path),
                "status": status,
                "message": message,
                "result": result
            }
            
            # 添加到通知队列（保留最近50个）
            self.change_notifications.append(notification)
            if len(self.change_notifications) > 50:
                self.change_notifications.pop(0)
            
            # 调用通知回调
            for callback in self.notification_callbacks:
                try:
                    callback(notification)
                except Exception as e:
                    logger.error("Notification callback failed", error=str(e))
            
        except Exception as e:
            self.stats["failed_updates"] += 1
            logger.error("Error processing file change", file=file_path, error=str(e))
    
    def get_monitoring_status(self) -> Dict:
        """获取监控状态信息"""
        
        return {
            "is_watching": self.is_watching,
            "watched_folders": list(self.watch_handles.keys()),
            "stats": self.stats.copy(),
            "recent_notifications": self.change_notifications[-10:] if self.change_notifications else []
        }
    
    def add_notification_callback(self, callback: Callable[[Dict], None]) -> None:
        """添加变化通知回调函数
        
        Args:
            callback: 回调函数，接收通知字典作为参数
        """
        
        if callback not in self.notification_callbacks:
            self.notification_callbacks.append(callback)
            logger.info("Added notification callback")
    
    def remove_notification_callback(self, callback: Callable[[Dict], None]) -> None:
        """移除变化通知回调函数"""
        
        if callback in self.notification_callbacks:
            self.notification_callbacks.remove(callback)
            logger.info("Removed notification callback")
    
    def get_recent_changes(self, limit: int = 20) -> List[Dict]:
        """获取最近的文件变化记录
        
        Args:
            limit: 返回记录数量限制
            
        Returns:
            最近的变化记录列表
        """
        
        return self.change_notifications[-limit:] if self.change_notifications else []
    
    def clear_notifications(self) -> None:
        """清除通知历史"""
        
        self.change_notifications.clear()
        logger.info("Cleared notification history")
    
    def restart_watching(self) -> bool:
        """重启文件系统监控"""
        
        logger.info("Restarting file system monitoring")
        
        if self.is_watching:
            self.stop_watching()
            time.sleep(1)  # 等待完全停止
        
        return self.start_watching()


class BackgroundFileWatcher:
    """后台文件监控服务
    
    在单独线程中运行文件监控，避免阻塞主程序
    """
    
    def __init__(self, config: Optional[PMConfig] = None):
        self.watcher = FileWatcherAgent(config)
        self.background_thread: Optional[Thread] = None
        self.stop_event = Event()
        
    def start_background_watching(self) -> bool:
        """在后台线程中启动文件监控"""
        
        if self.background_thread and self.background_thread.is_alive():
            logger.warning("Background file watcher already running")
            return True
        
        if not self.watcher.start_watching():
            return False
        
        # 创建后台线程
        self.stop_event.clear()
        self.background_thread = Thread(
            target=self._background_worker,
            name="FileWatcher",
            daemon=True
        )
        self.background_thread.start()
        
        logger.info("Background file watcher started")
        return True
    
    def stop_background_watching(self) -> None:
        """停止后台文件监控"""
        
        if not self.background_thread or not self.background_thread.is_alive():
            return
        
        # 发送停止信号
        self.stop_event.set()
        
        # 停止文件监控
        self.watcher.stop_watching()
        
        # 等待线程结束
        if self.background_thread:
            self.background_thread.join(timeout=5.0)
            if self.background_thread.is_alive():
                logger.warning("Background thread did not stop gracefully")
        
        logger.info("Background file watcher stopped")
    
    def _background_worker(self) -> None:
        """后台工作线程"""
        
        logger.info("Background file watcher thread started")
        
        try:
            # 等待停止信号
            while not self.stop_event.wait(timeout=1.0):
                # 定期检查文件监控状态
                if not self.watcher.is_watching:
                    logger.warning("File watcher stopped unexpectedly, restarting")
                    self.watcher.restart_watching()
        
        except Exception as e:
            logger.error("Background file watcher error", error=str(e))
        
        finally:
            logger.info("Background file watcher thread ended")
    
    def get_status(self) -> Dict:
        """获取后台监控状态"""
        
        status = self.watcher.get_monitoring_status()
        status["background_thread_alive"] = (
            self.background_thread and self.background_thread.is_alive()
        )
        
        return status
    
    def add_notification_callback(self, callback: Callable[[Dict], None]) -> None:
        """添加变化通知回调"""
        self.watcher.add_notification_callback(callback)
    
    def remove_notification_callback(self, callback: Callable[[Dict], None]) -> None:
        """移除变化通知回调"""
        self.watcher.remove_notification_callback(callback)