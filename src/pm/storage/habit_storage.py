"""习惯数据存储管理器 - Sprint 13核心功能

提供习惯和记录的持久化存储，支持AI工具调用
"""

import json
import os
import structlog
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta
from filelock import FileLock

from pm.core.config import PMConfig
from pm.models.habit import Habit, HabitRecord, HabitCategory, HabitFrequency

logger = structlog.get_logger()


class HabitStorage:
    """习惯数据存储管理器"""
    
    def __init__(self, config: PMConfig):
        self.config = config
        
        # 显式调用PMConfig的目录确保方法
        self.config._ensure_directories()
        
        self.data_dir = Path(config.data_dir) / "habits"
        self.habits_file = self.data_dir / "habits.json"
        self.lock_file = self.habits_file.with_suffix('.json.lock')
        
        # 确保所有父目录存在（包括 ~/.personalmanager 和 data 目录）
        Path(config.data_dir).mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 内存缓存
        self._habits_cache: Dict[str, Habit] = {}
        self._cache_loaded = False
        
        # 详细路径诊断日志
        logger.info("HabitStorage initialized", 
                   config_data_dir=str(config.data_dir),
                   habits_data_dir=str(self.data_dir),
                   habits_file_path=str(self.habits_file),
                   habits_file_absolute=str(self.habits_file.absolute()),
                   home_dir=str(Path.home()),
                   file_exists=self.habits_file.exists(),
                   dir_exists=self.data_dir.exists())
    
    def _load_cache(self) -> None:
        """加载习惯数据到内存缓存（使用文件锁和错误恢复）"""
        if self._cache_loaded:
            return
            
        try:
            if self.habits_file.exists():
                # 使用文件锁确保读取时文件不被修改（增强版）
                with FileLock(str(self.lock_file), timeout=10):
                    logger.info("Loading habits with enhanced file lock", 
                               file_path=str(self.habits_file),
                               lock_path=str(self.lock_file))
                    
                    # 详细调试：加载前状态
                    logger.info("DEBUG: Before load operation verification", 
                               habits_file_exists=self.habits_file.exists(),
                               habits_file_path=str(self.habits_file),
                               habits_file_absolute=str(self.habits_file.absolute()),
                               current_cache_count=len(self._habits_cache))
                    
                    max_retries = 3
                    for attempt in range(max_retries):
                        try:
                            # 检查文件是否仍然存在（可能在获取锁的过程中被删除）
                            if not self.habits_file.exists():
                                logger.warning("Habits file disappeared during lock acquisition")
                                self._habits_cache = {}
                                break
                            
                            with open(self.habits_file, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                            
                            # 详细调试JSON加载
                            logger.info("DEBUG: Loaded data from file", 
                                       file_data_keys=list(data.keys()),
                                       habits_count_in_file=data.get("count", "N/A"),
                                       habits_list_length=len(data.get("habits", [])),
                                       file_version=data.get("version", "N/A"))
                            
                            # 验证数据结构
                            if not isinstance(data, dict) or "habits" not in data:
                                raise ValueError("Invalid habits file structure")
                            
                            self._habits_cache = {}
                            habits_list = data.get("habits", [])
                            
                            logger.info("DEBUG: About to process habits list", 
                                       habits_list_type=type(habits_list),
                                       habits_list_length=len(habits_list))
                            
                            for i, habit_data in enumerate(habits_list):
                                try:
                                    logger.info(f"DEBUG: Processing habit {i+1}/{len(habits_list)}", 
                                               habit_id=habit_data.get("id", "unknown"),
                                               habit_name=habit_data.get("name", "unknown"))
                                    
                                    habit = Habit.from_dict(habit_data)
                                    self._habits_cache[habit.id] = habit
                                    
                                    logger.info(f"DEBUG: Successfully loaded habit {i+1}", 
                                               habit_id=habit.id,
                                               habit_name=habit.name,
                                               cache_size=len(self._habits_cache))
                                    
                                except Exception as e:
                                    logger.error("Failed to load habit", 
                                               habit_id=habit_data.get("id", "unknown"),
                                               habit_name=habit_data.get("name", "unknown"),
                                               error=str(e))
                            
                            logger.info("Habits loaded from storage", 
                                       count=len(self._habits_cache),
                                       file_version=data.get("version", "unknown"),
                                       total_in_file=len(habits_list))
                            break  # 成功加载，跳出重试循环
                            
                        except (json.JSONDecodeError, ValueError) as parse_error:
                            logger.error(f"JSON parse error on attempt {attempt + 1}", 
                                       error=str(parse_error),
                                       file_path=str(self.habits_file))
                            
                            if attempt == max_retries - 1:
                                # 最后一次尝试失败，进行文件恢复
                                logger.error("All load attempts failed, handling corrupted file")
                                self._handle_corrupted_file()
                                self._habits_cache = {}
                            else:
                                # 短暂等待后重试
                                import time
                                time.sleep(0.1)
                                
            else:
                logger.info("No existing habits file, starting fresh")
                self._habits_cache = {}
                
        except Exception as e:
            logger.error("Failed to load habits cache", error=str(e))
            self._habits_cache = {}
        
        self._cache_loaded = True
    
    def _handle_corrupted_file(self) -> None:
        """处理损坏的habits.json文件"""
        try:
            # 备份损坏的文件
            backup_path = self.habits_file.with_suffix(f'.corrupted.{datetime.now().strftime("%Y%m%d_%H%M%S")}.bak')
            self.habits_file.rename(backup_path)
            
            logger.warning("Corrupted habits file backed up", 
                          original_path=str(self.habits_file),
                          backup_path=str(backup_path))
            
        except Exception as backup_error:
            logger.error("Failed to backup corrupted file", error=str(backup_error))
            # 如果备份失败，直接删除损坏的文件
            try:
                self.habits_file.unlink()
                logger.warning("Corrupted habits file deleted", file_path=str(self.habits_file))
            except Exception as delete_error:
                logger.error("Failed to delete corrupted file", error=str(delete_error))
    
    def _save_cache(self) -> bool:
        """保存内存缓存到文件（使用文件锁确保原子性）"""
        try:
            # 确保父目录存在（防御性编程）
            self.habits_file.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                "version": "1.0",
                "saved_at": datetime.now().isoformat(),
                "count": len(self._habits_cache),
                "habits": [habit.to_dict() for habit in self._habits_cache.values()]
            }
            
            # 详细的文件写入诊断
            logger.info("Saving habits to file with lock", 
                       file_path=str(self.habits_file),
                       lock_path=str(self.lock_file),
                       file_absolute=str(self.habits_file.absolute()),
                       parent_exists=self.habits_file.parent.exists(),
                       data_count=len(self._habits_cache))
            
            # 使用文件锁确保原子性写入（crash-safe实现）
            with FileLock(str(self.lock_file), timeout=10):
                # 生成唯一的临时文件名避免并发冲突
                temp_suffix = f'.tmp.{datetime.now().strftime("%Y%m%d_%H%M%S_%f")}'
                temp_file = self.habits_file.with_suffix(temp_suffix)
                
                try:
                    # 步骤1: 写入到临时文件
                    with open(temp_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                        f.flush()  # 确保数据写入磁盘
                        os.fsync(f.fileno())  # 强制操作系统写入磁盘
                    
                    # 步骤2: 验证临时文件内容有效性
                    with open(temp_file, 'r', encoding='utf-8') as f:
                        json.load(f)  # 验证JSON有效性
                    
                    # 步骤3: 原子性替换（这是原子操作）
                    temp_file.replace(self.habits_file)
                    
                    logger.info("Atomic file operation completed", 
                               temp_file=str(temp_file),
                               final_file=str(self.habits_file))
                    
                except Exception as write_error:
                    logger.error("Atomic write failed", 
                               temp_file=str(temp_file),
                               error=str(write_error))
                    raise
                finally:
                    # 清理临时文件（如果仍然存在）
                    if temp_file.exists():
                        try:
                            temp_file.unlink()
                            logger.debug("Temporary file cleaned up", temp_file=str(temp_file))
                        except Exception as cleanup_error:
                            logger.warning("Failed to cleanup temp file", 
                                         temp_file=str(temp_file),
                                         error=str(cleanup_error))
            
            # 验证文件写入结果
            file_exists_after = self.habits_file.exists()
            file_size = self.habits_file.stat().st_size if file_exists_after else 0
            
            # 验证JSON完整性
            json_valid = False
            try:
                with open(self.habits_file, 'r', encoding='utf-8') as f:
                    json.load(f)
                json_valid = True
            except Exception as json_error:
                logger.error("JSON validation failed after save", error=str(json_error))
            
            logger.info("Habits saved to storage", 
                       count=len(self._habits_cache),
                       file_exists=file_exists_after,
                       file_size=file_size,
                       json_valid=json_valid,
                       absolute_path=str(self.habits_file.absolute()))
            
            # 详细调试：验证文件持久化
            logger.info("DEBUG: After save operation verification", 
                       habits_file_exists=self.habits_file.exists(),
                       habits_file_path=str(self.habits_file),
                       habits_file_absolute=str(self.habits_file.absolute()),
                       cache_count=len(self._habits_cache),
                       cache_ids=[habit_id for habit_id in self._habits_cache.keys()])
            
            return json_valid
            
        except Exception as e:
            logger.error("Failed to save habits", error=str(e))
            return False
    
    def save_habit(self, habit: Habit) -> bool:
        """保存习惯"""
        try:
            self._load_cache()
            
            # 更新时间戳
            habit.updated_at = datetime.now()
            
            # 更新缓存
            self._habits_cache[habit.id] = habit
            
            # 保存到文件
            success = self._save_cache()
            
            if success:
                logger.info("Habit saved", habit_id=habit.id, habit_name=habit.name)
            
            return success
            
        except Exception as e:
            logger.error("Failed to save habit", habit_id=habit.id, error=str(e))
            return False
    
    def get_habit(self, habit_id: str) -> Optional[Habit]:
        """获取指定习惯"""
        try:
            self._load_cache()
            return self._habits_cache.get(habit_id)
        except Exception as e:
            logger.error("Failed to get habit", habit_id=habit_id, error=str(e))
            return None
    
    def get_all_habits(self, active_only: bool = False) -> List[Habit]:
        """获取所有习惯"""
        try:
            self._load_cache()
            habits = list(self._habits_cache.values())
            
            if active_only:
                habits = [h for h in habits if h.active]
            
            # 按创建时间排序
            habits.sort(key=lambda x: x.created_at)
            return habits
            
        except Exception as e:
            logger.error("Failed to get all habits", error=str(e))
            return []
    
    def find_habits_by_name(self, name_pattern: str) -> List[Habit]:
        """按名称模式查找习惯"""
        try:
            self._load_cache()
            name_lower = name_pattern.lower()
            
            matching_habits = []
            for habit in self._habits_cache.values():
                if name_lower in habit.name.lower():
                    matching_habits.append(habit)
            
            matching_habits.sort(key=lambda x: x.created_at)
            return matching_habits
            
        except Exception as e:
            logger.error("Failed to find habits by name", pattern=name_pattern, error=str(e))
            return []
    
    def get_habits_by_category(self, category: HabitCategory) -> List[Habit]:
        """按分类获取习惯"""
        try:
            self._load_cache()
            habits = [h for h in self._habits_cache.values() if h.category == category]
            habits.sort(key=lambda x: x.created_at)
            return habits
        except Exception as e:
            logger.error("Failed to get habits by category", category=category.value, error=str(e))
            return []
    
    def get_due_habits_today(self) -> List[Habit]:
        """获取今天应该执行的习惯"""
        try:
            self._load_cache()
            due_habits = [h for h in self._habits_cache.values() if h.active and h.is_due_today()]
            due_habits.sort(key=lambda x: x.created_at)
            return due_habits
        except Exception as e:
            logger.error("Failed to get due habits", error=str(e))
            return []
    
    def get_pending_habits_today(self) -> List[Habit]:
        """获取今天尚未完成的习惯"""
        try:
            due_habits = self.get_due_habits_today()
            pending_habits = [h for h in due_habits if not h.is_completed_today()]
            return pending_habits
        except Exception as e:
            logger.error("Failed to get pending habits", error=str(e))
            return []
    
    def delete_habit(self, habit_id: str) -> bool:
        """删除习惯"""
        try:
            self._load_cache()
            
            if habit_id in self._habits_cache:
                habit_name = self._habits_cache[habit_id].name
                del self._habits_cache[habit_id]
                success = self._save_cache()
                
                if success:
                    logger.info("Habit deleted", habit_id=habit_id, habit_name=habit_name)
                
                return success
            else:
                logger.warning("Habit not found for deletion", habit_id=habit_id)
                return False
                
        except Exception as e:
            logger.error("Failed to delete habit", habit_id=habit_id, error=str(e))
            return False
    
    def archive_habit(self, habit_id: str) -> bool:
        """归档习惯（设为非活跃）"""
        try:
            habit = self.get_habit(habit_id)
            if habit:
                habit.active = False
                return self.save_habit(habit)
            return False
        except Exception as e:
            logger.error("Failed to archive habit", habit_id=habit_id, error=str(e))
            return False
    
    def get_habit_statistics(self) -> Dict[str, Any]:
        """获取习惯统计信息"""
        try:
            self._load_cache()
            
            all_habits = list(self._habits_cache.values())
            active_habits = [h for h in all_habits if h.active]
            
            # 分类统计
            category_counts = {}
            for habit in active_habits:
                category = habit.category.value
                category_counts[category] = category_counts.get(category, 0) + 1
            
            # 今日完成统计
            due_today = self.get_due_habits_today()
            completed_today = [h for h in due_today if h.is_completed_today()]
            
            # 连续打卡统计
            current_streaks = [h.streak.current_streak for h in active_habits]
            avg_streak = sum(current_streaks) / len(current_streaks) if current_streaks else 0
            
            return {
                "total_habits": len(all_habits),
                "active_habits": len(active_habits),
                "archived_habits": len(all_habits) - len(active_habits),
                "category_distribution": category_counts,
                "due_today": len(due_today),
                "completed_today": len(completed_today),
                "completion_rate_today": len(completed_today) / len(due_today) * 100 if due_today else 0,
                "average_current_streak": round(avg_streak, 1),
                "longest_streak": max([h.streak.longest_streak for h in active_habits], default=0)
            }
            
        except Exception as e:
            logger.error("Failed to get habit statistics", error=str(e))
            return {}
    
    def backup_habits(self, backup_path: Optional[Path] = None) -> bool:
        """备份习惯数据"""
        try:
            self._load_cache()
            
            if backup_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = self.data_dir / f"habits_backup_{timestamp}.json"
            
            data = {
                "backup_version": "1.0",
                "backup_time": datetime.now().isoformat(),
                "source_file": str(self.habits_file),
                "habits_count": len(self._habits_cache),
                "habits": [habit.to_dict() for habit in self._habits_cache.values()]
            }
            
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info("Habits backed up", backup_file=str(backup_path), count=len(self._habits_cache))
            return True
            
        except Exception as e:
            logger.error("Failed to backup habits", error=str(e))
            return False
    
    def import_habits_from_backup(self, backup_path: Path, merge: bool = True) -> bool:
        """从备份文件导入习惯"""
        try:
            if not backup_path.exists():
                logger.error("Backup file not found", backup_path=str(backup_path))
                return False
            
            with open(backup_path, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            imported_count = 0
            for habit_data in backup_data.get("habits", []):
                try:
                    habit = Habit.from_dict(habit_data)
                    
                    if merge and habit.id in self._habits_cache:
                        # 合并模式：跳过已存在的习惯
                        continue
                    
                    self._habits_cache[habit.id] = habit
                    imported_count += 1
                    
                except Exception as e:
                    logger.error("Failed to import habit", habit_id=habit_data.get("id"), error=str(e))
            
            if imported_count > 0:
                success = self._save_cache()
                if success:
                    logger.info("Habits imported from backup", 
                              imported_count=imported_count, 
                              backup_file=str(backup_path))
                return success
            else:
                logger.info("No new habits to import", backup_file=str(backup_path))
                return True
                
        except Exception as e:
            logger.error("Failed to import habits from backup", backup_path=str(backup_path), error=str(e))
            return False