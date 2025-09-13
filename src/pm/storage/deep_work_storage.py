"""深度工作数据存储管理器 - Sprint 14核心功能

提供深度工作时段和反思记录的持久化存储，支持AI工具调用
"""

import json
import structlog
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta

from pm.core.config import PMConfig
from pm.models.deep_work import (
    DeepWorkSession, ReflectionEntry, DeepWorkType, FocusLevel, WorkEnvironment
)

logger = structlog.get_logger()


class DeepWorkStorage:
    """深度工作数据存储管理器"""
    
    def __init__(self, config: PMConfig):
        self.config = config
        self.data_dir = Path(config.data_dir) / "deep_work"
        self.sessions_file = self.data_dir / "sessions.json"
        self.reflections_file = self.data_dir / "reflections.json"
        
        # 确保目录存在
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 内存缓存
        self._sessions_cache: Dict[str, DeepWorkSession] = {}
        self._reflections_cache: Dict[str, ReflectionEntry] = {}
        self._sessions_cache_loaded = False
        self._reflections_cache_loaded = False
        
        logger.info("DeepWorkStorage initialized", 
                   data_dir=str(self.data_dir),
                   sessions_file=str(self.sessions_file),
                   reflections_file=str(self.reflections_file))
    
    def _load_sessions_cache(self) -> None:
        """加载深度工作时段数据到内存缓存"""
        if self._sessions_cache_loaded:
            return

        # 详细调试：加载前状态
        logger.info("DEBUG: About to load sessions cache",
                   file_exists=self.sessions_file.exists(),
                   file_path=str(self.sessions_file),
                   file_absolute=str(self.sessions_file.absolute()),
                   current_cache_count=len(self._sessions_cache))

        try:
            if self.sessions_file.exists():
                with open(self.sessions_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # 详细调试JSON加载
                logger.info("DEBUG: Loaded data from file",
                           file_data_keys=list(data.keys()),
                           file_count=data.get("count", "N/A"),
                           sessions_list_length=len(data.get("sessions", [])),
                           file_version=data.get("version", "N/A"))

                self._sessions_cache = {}
                sessions_list = data.get("sessions", [])

                for i, session_data in enumerate(sessions_list):
                    try:
                        logger.info(f"DEBUG: Processing session {i+1}/{len(sessions_list)}",
                                   session_id=session_data.get("session_id", "unknown"),
                                   session_title=session_data.get("title", "unknown"))

                        session = DeepWorkSession.from_dict(session_data)
                        self._sessions_cache[session.session_id] = session

                        logger.info(f"DEBUG: Successfully loaded session {i+1}",
                                   session_id=session.session_id,
                                   session_title=session.title,
                                   cache_size=len(self._sessions_cache))

                    except Exception as e:
                        logger.error("Failed to load deep work session",
                                   session_id=session_data.get("session_id", "unknown"),
                                   error=str(e))

                logger.info("Deep work sessions loaded from storage",
                           count=len(self._sessions_cache),
                           file_version=data.get("version", "unknown"),
                           total_in_file=len(sessions_list))
            else:
                logger.info("No existing sessions file, starting fresh")
                self._sessions_cache = {}

        except Exception as e:
            logger.error("Failed to load sessions cache", error=str(e))
            self._sessions_cache = {}

        self._sessions_cache_loaded = True
    
    def _save_sessions_cache(self) -> bool:
        """保存时段缓存到文件"""
        try:
            data = {
                "version": "1.0",
                "saved_at": datetime.now().isoformat(),
                "count": len(self._sessions_cache),
                "sessions": [session.to_dict() for session in self._sessions_cache.values()]
            }

            # 详细调试：保存前状态
            logger.info("DEBUG: About to save sessions",
                       cache_count=len(self._sessions_cache),
                       cache_ids=[session_id for session_id in self._sessions_cache.keys()],
                       file_path=str(self.sessions_file))

            with open(self.sessions_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            # 验证保存后文件状态
            file_exists_after = self.sessions_file.exists()
            file_size = self.sessions_file.stat().st_size if file_exists_after else 0

            logger.info("Deep work sessions saved to storage",
                       count=len(self._sessions_cache),
                       file_exists=file_exists_after,
                       file_size=file_size,
                       absolute_path=str(self.sessions_file.absolute()))

            # 立即验证文件内容
            try:
                with open(self.sessions_file, 'r', encoding='utf-8') as f:
                    verify_data = json.load(f)
                logger.info("DEBUG: File verification after save",
                           file_count=verify_data.get("count", "N/A"),
                           file_sessions_length=len(verify_data.get("sessions", [])))
            except Exception as verify_error:
                logger.error("File verification failed after save", error=str(verify_error))

            return True

        except Exception as e:
            logger.error("Failed to save sessions cache", error=str(e))
            return False
    
    def _load_reflections_cache(self) -> None:
        """加载反思记录数据到内存缓存"""
        if self._reflections_cache_loaded:
            return
            
        try:
            if self.reflections_file.exists():
                with open(self.reflections_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self._reflections_cache = {}
                for reflection_data in data.get("reflections", []):
                    try:
                        reflection = ReflectionEntry.from_dict(reflection_data)
                        self._reflections_cache[reflection.reflection_id] = reflection
                    except Exception as e:
                        logger.error("Failed to load reflection entry", 
                                   reflection_id=reflection_data.get("reflection_id", "unknown"),
                                   error=str(e))
                
                logger.info("Reflection entries loaded from storage", count=len(self._reflections_cache))
            else:
                logger.info("No existing reflections file, starting fresh")
                
        except Exception as e:
            logger.error("Failed to load reflections cache", error=str(e))
            self._reflections_cache = {}
        
        self._reflections_cache_loaded = True
    
    def _save_reflections_cache(self) -> bool:
        """保存反思记录缓存到文件"""
        try:
            data = {
                "version": "1.0",
                "saved_at": datetime.now().isoformat(),
                "count": len(self._reflections_cache),
                "reflections": [reflection.to_dict() for reflection in self._reflections_cache.values()]
            }
            
            with open(self.reflections_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info("Reflection entries saved to storage", count=len(self._reflections_cache))
            return True
            
        except Exception as e:
            logger.error("Failed to save reflections cache", error=str(e))
            return False
    
    # ========== 深度工作时段管理 ==========
    
    def save_session(self, session: DeepWorkSession) -> bool:
        """保存深度工作时段"""
        self._load_sessions_cache()
        
        try:
            self._sessions_cache[session.session_id] = session
            success = self._save_sessions_cache()
            
            if success:
                logger.info("Deep work session saved", 
                           session_id=session.session_id,
                           title=session.title)
            
            return success
            
        except Exception as e:
            logger.error("Failed to save deep work session", 
                        session_id=session.session_id,
                        error=str(e))
            return False
    
    def get_session(self, session_id: str) -> Optional[DeepWorkSession]:
        """获取指定深度工作时段"""
        self._load_sessions_cache()
        return self._sessions_cache.get(session_id)
    
    def get_all_sessions(self) -> List[DeepWorkSession]:
        """获取所有深度工作时段"""
        self._load_sessions_cache()
        return list(self._sessions_cache.values())
    
    def get_sessions_by_date_range(self, start_date: date, end_date: date) -> List[DeepWorkSession]:
        """获取指定日期范围内的深度工作时段"""
        self._load_sessions_cache()
        
        sessions = []
        for session in self._sessions_cache.values():
            session_date = session.planned_start.date()
            if start_date <= session_date <= end_date:
                sessions.append(session)
        
        return sorted(sessions, key=lambda s: s.planned_start)
    
    def get_sessions_by_project(self, project_id: str) -> List[DeepWorkSession]:
        """获取指定项目的深度工作时段"""
        self._load_sessions_cache()
        
        return [session for session in self._sessions_cache.values() 
                if session.project_id == project_id]
    
    def get_recent_sessions(self, days: int = 7) -> List[DeepWorkSession]:
        """获取最近几天的深度工作时段"""
        end_date = date.today()
        start_date = end_date - timedelta(days=days-1)
        return self.get_sessions_by_date_range(start_date, end_date)
    
    def get_active_session(self) -> Optional[DeepWorkSession]:
        """获取当前进行中的深度工作时段"""
        self._load_sessions_cache()
        
        for session in self._sessions_cache.values():
            if session.actual_start and not session.completed:
                return session
        
        return None
    
    def get_todays_sessions(self) -> List[DeepWorkSession]:
        """获取今天的深度工作时段"""
        today = date.today()
        return self.get_sessions_by_date_range(today, today)
    
    def delete_session(self, session_id: str) -> bool:
        """删除深度工作时段"""
        self._load_sessions_cache()
        
        try:
            if session_id in self._sessions_cache:
                del self._sessions_cache[session_id]
                success = self._save_sessions_cache()
                
                if success:
                    logger.info("Deep work session deleted", session_id=session_id)
                
                return success
            else:
                logger.warning("Session not found for deletion", session_id=session_id)
                return False
                
        except Exception as e:
            logger.error("Failed to delete session", 
                        session_id=session_id,
                        error=str(e))
            return False
    
    def find_sessions_by_tags(self, tags: List[str]) -> List[DeepWorkSession]:
        """根据标签查找深度工作时段"""
        self._load_sessions_cache()
        
        matching_sessions = []
        for session in self._sessions_cache.values():
            if any(tag in session.tags for tag in tags):
                matching_sessions.append(session)
        
        return sorted(matching_sessions, key=lambda s: s.planned_start, reverse=True)
    
    def get_sessions_by_focus_level(self, focus_level: FocusLevel) -> List[DeepWorkSession]:
        """获取指定专注级别的深度工作时段"""
        self._load_sessions_cache()
        
        return [session for session in self._sessions_cache.values()
                if session.target_focus_level == focus_level or 
                   session.actual_focus_level == focus_level]
    
    # ========== 反思记录管理 ==========
    
    def save_reflection(self, reflection: ReflectionEntry) -> bool:
        """保存反思记录"""
        self._load_reflections_cache()
        
        try:
            self._reflections_cache[reflection.reflection_id] = reflection
            success = self._save_reflections_cache()
            
            if success:
                logger.info("Reflection entry saved", 
                           reflection_id=reflection.reflection_id,
                           period_type=reflection.period_type)
            
            return success
            
        except Exception as e:
            logger.error("Failed to save reflection entry", 
                        reflection_id=reflection.reflection_id,
                        error=str(e))
            return False
    
    def get_reflection(self, reflection_id: str) -> Optional[ReflectionEntry]:
        """获取指定反思记录"""
        self._load_reflections_cache()
        return self._reflections_cache.get(reflection_id)
    
    def get_reflections_by_period(self, period_type: str) -> List[ReflectionEntry]:
        """获取指定周期类型的反思记录"""
        self._load_reflections_cache()
        
        return [reflection for reflection in self._reflections_cache.values()
                if reflection.period_type == period_type]
    
    def get_recent_reflections(self, days: int = 30) -> List[ReflectionEntry]:
        """获取最近的反思记录"""
        self._load_reflections_cache()
        
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_reflections = []
        
        for reflection in self._reflections_cache.values():
            if reflection.date >= cutoff_date:
                recent_reflections.append(reflection)
        
        return sorted(recent_reflections, key=lambda r: r.date, reverse=True)
    
    def delete_reflection(self, reflection_id: str) -> bool:
        """删除反思记录"""
        self._load_reflections_cache()
        
        try:
            if reflection_id in self._reflections_cache:
                del self._reflections_cache[reflection_id]
                success = self._save_reflections_cache()
                
                if success:
                    logger.info("Reflection entry deleted", reflection_id=reflection_id)
                
                return success
            else:
                logger.warning("Reflection not found for deletion", reflection_id=reflection_id)
                return False
                
        except Exception as e:
            logger.error("Failed to delete reflection", 
                        reflection_id=reflection_id,
                        error=str(e))
            return False
    
    # ========== 统计和分析方法 ==========
    
    def get_session_statistics(self, days: int = 30) -> Dict[str, Any]:
        """获取深度工作时段统计信息"""
        sessions = self.get_recent_sessions(days)
        completed_sessions = [s for s in sessions if s.completed]
        
        if not completed_sessions:
            return {
                "total_sessions": 0,
                "completed_sessions": 0,
                "total_deep_work_minutes": 0,
                "average_focus_score": 0.0,
                "average_efficiency_score": 0.0,
                "most_productive_time": None,
                "common_distractions": []
            }
        
        # 基础统计
        total_deep_work_minutes = sum(s.get_actual_duration_minutes() for s in completed_sessions)
        avg_focus_score = sum(s.metrics.focus_score for s in completed_sessions) / len(completed_sessions)
        avg_efficiency_score = sum(s.get_efficiency_score() for s in completed_sessions) / len(completed_sessions)
        
        # 最佳工作时段分析
        hour_performance = {}
        for session in completed_sessions:
            hour = session.actual_start.hour if session.actual_start else session.planned_start.hour
            if hour not in hour_performance:
                hour_performance[hour] = []
            hour_performance[hour].append(session.metrics.focus_score)
        
        most_productive_hour = max(hour_performance.items(), 
                                 key=lambda x: sum(x[1])/len(x[1]))[0] if hour_performance else None
        
        # 常见干扰分析
        all_distractions = []
        for session in completed_sessions:
            all_distractions.extend(session.distractions)
        
        distraction_types = {}
        for distraction in all_distractions:
            dtype = distraction.distraction_type.value
            distraction_types[dtype] = distraction_types.get(dtype, 0) + 1
        
        common_distractions = sorted(distraction_types.items(), key=lambda x: x[1], reverse=True)[:3]
        
        return {
            "total_sessions": len(sessions),
            "completed_sessions": len(completed_sessions),
            "completion_rate": len(completed_sessions) / len(sessions) * 100 if sessions else 0,
            "total_deep_work_minutes": total_deep_work_minutes,
            "average_session_duration": total_deep_work_minutes / len(completed_sessions) if completed_sessions else 0,
            "average_focus_score": round(avg_focus_score, 1),
            "average_efficiency_score": round(avg_efficiency_score, 1),
            "most_productive_hour": most_productive_hour,
            "common_distractions": common_distractions,
            "total_distractions": len(all_distractions),
            "distraction_rate": len(all_distractions) / len(completed_sessions) if completed_sessions else 0
        }
    
    def get_focus_trends(self, days: int = 30) -> List[Dict[str, Any]]:
        """获取专注度趋势数据"""
        sessions = self.get_recent_sessions(days)
        completed_sessions = [s for s in sessions if s.completed]
        
        # 按日期分组
        daily_focus = {}
        for session in completed_sessions:
            session_date = session.actual_start.date() if session.actual_start else session.planned_start.date()
            date_str = session_date.isoformat()
            
            if date_str not in daily_focus:
                daily_focus[date_str] = {
                    "date": date_str,
                    "sessions": [],
                    "total_minutes": 0,
                    "average_focus_score": 0,
                    "distraction_count": 0
                }
            
            daily_focus[date_str]["sessions"].append(session)
            daily_focus[date_str]["total_minutes"] += session.get_actual_duration_minutes()
            daily_focus[date_str]["distraction_count"] += len(session.distractions)
        
        # 计算每日平均专注度
        for date_data in daily_focus.values():
            sessions_count = len(date_data["sessions"])
            if sessions_count > 0:
                avg_focus = sum(s.metrics.focus_score for s in date_data["sessions"]) / sessions_count
                date_data["average_focus_score"] = round(avg_focus, 1)
                date_data["sessions_count"] = sessions_count
            
            # 清理sessions数据，避免返回过多信息
            del date_data["sessions"]
        
        # 按日期排序返回
        return sorted(daily_focus.values(), key=lambda x: x["date"])
    
    def get_environment_effectiveness(self) -> Dict[str, Any]:
        """获取不同工作环境的有效性分析"""
        sessions = self.get_all_sessions()
        completed_sessions = [s for s in sessions if s.completed]
        
        env_stats = {}
        for session in completed_sessions:
            env_type = session.environment.location.value
            
            if env_type not in env_stats:
                env_stats[env_type] = {
                    "sessions_count": 0,
                    "total_focus_score": 0,
                    "total_efficiency_score": 0,
                    "total_distractions": 0,
                    "total_minutes": 0
                }
            
            stats = env_stats[env_type]
            stats["sessions_count"] += 1
            stats["total_focus_score"] += session.metrics.focus_score
            stats["total_efficiency_score"] += session.get_efficiency_score()
            stats["total_distractions"] += len(session.distractions)
            stats["total_minutes"] += session.get_actual_duration_minutes()
        
        # 计算平均值
        for env_type, stats in env_stats.items():
            count = stats["sessions_count"]
            if count > 0:
                stats["average_focus_score"] = round(stats["total_focus_score"] / count, 1)
                stats["average_efficiency_score"] = round(stats["total_efficiency_score"] / count, 1)
                stats["average_distractions"] = round(stats["total_distractions"] / count, 1)
                stats["average_duration"] = round(stats["total_minutes"] / count, 1)
        
        return env_stats