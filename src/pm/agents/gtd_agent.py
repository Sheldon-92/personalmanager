"""GTD Agent - 任务管理和GTD流程核心Agent"""

import os
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
import structlog

from pm.core.config import PMConfig
from pm.core.task_storage import TaskStorage
from pm.models.task import Task, TaskStatus, TaskContext, TaskPriority, TaskFilter, EnergyLevel
from pm.agents.project_manager import ProjectManagerAgent
from pm.engines.recommendation_engine import IntelligentRecommendationEngine

logger = structlog.get_logger()


class GTDAgent:
    """GTD Agent - 任务管理和GTD流程的核心Agent
    
    实现GTD的完整工作流程：
    - 任务捕获 (Capture)
    - 任务理清 (Clarify) 
    - 任务组织 (Organize)
    - 任务执行 (Engage)
    
    融入"更高标准"的智能化特性：
    - 智能项目关联
    - 预测性分类建议
    - 情境智能推荐
    """
    
    def __init__(self, config: Optional[PMConfig] = None):
        self.config = config or PMConfig()
        self.storage = TaskStorage(self.config)
        self.project_agent = ProjectManagerAgent(self.config)
        
        # 智能分类学习系统（US-008）
        self._classification_history: Dict[str, Dict[str, Any]] = {}
        self._context_patterns: Dict[str, List[str]] = {}
        self._load_classification_history()
        
        # 智能推荐引擎（US-011）
        self.recommendation_engine = IntelligentRecommendationEngine(self.config)
        
        logger.info("GTDAgent initialized")
    
    def capture_task(self, 
                    title: str, 
                    description: Optional[str] = None,
                    capture_context: Optional[Dict[str, str]] = None) -> Task:
        """捕获任务到收件箱
        
        根据US-005验收标准实现：
        - 通过 `/pm capture "任务内容"` 快速添加任务
        - 支持多行文本输入
        - 任务自动进入"收件箱"待处理列表
        - 命令执行时间不超过1秒
        
        融入智能化特性：
        - 自动项目关联
        - 智能上下文捕获
        """
        
        logger.info("Capturing task", title=title[:50])
        
        # 创建任务对象
        task = Task(
            title=title,
            description=description,
            status=TaskStatus.INBOX,
            created_at=datetime.now()
        )
        
        # 添加捕获上下文（US-006要求）
        if capture_context:
            task.capture_source = capture_context.get('source', 'cli')
            task.capture_location = capture_context.get('location')
            task.capture_device = capture_context.get('device')
        else:
            # 默认上下文
            task.capture_source = 'cli'
            task.capture_location = str(Path.cwd()) if Path.cwd().exists() else None
            task.capture_device = os.uname().nodename if hasattr(os, 'uname') else 'unknown'
        
        # 智能项目关联
        self._suggest_project_association(task)
        
        # 智能初步分类建议
        self._suggest_initial_classification(task)
        
        # 保存任务
        success = self.storage.save_task(task)
        
        if success:
            logger.info("Task captured successfully", 
                       task_id=task.id,
                       title=task.title,
                       project=task.project_name)
        else:
            logger.error("Failed to capture task", title=task.title)
            raise RuntimeError("任务捕获失败")
        
        return task
    
    def _suggest_project_association(self, task: Task) -> None:
        """智能项目关联建议"""
        
        try:
            # 获取当前项目列表
            projects = self.project_agent.discover_projects()
            
            # 如果捕获位置在某个项目目录内，自动关联
            if task.capture_location:
                capture_path = Path(task.capture_location)
                
                for project in projects:
                    project_path = Path(project.path)
                    try:
                        # 检查是否在项目目录内
                        capture_path.relative_to(project_path)
                        task.project_id = project.name  # 使用项目名作为ID
                        task.project_name = project.name
                        logger.info("Auto-associated task with project", 
                                   task_id=task.id,
                                   project=project.name)
                        return
                    except ValueError:
                        # 不在此项目目录内，继续检查下一个
                        continue
            
            # 基于关键词匹配项目
            task_text = f"{task.title} {task.description or ''}".lower()
            
            for project in projects:
                project_keywords = [
                    project.name.lower(),
                    project.description.lower() if project.description else "",
                    *[tag.lower() for tag in project.tags]
                ]
                
                for keyword in project_keywords:
                    if keyword and len(keyword) > 2 and keyword in task_text:
                        task.project_name = project.name
                        task.add_tag(f"project:{project.name}")
                        logger.info("Suggested project association", 
                                   task_id=task.id,
                                   project=project.name,
                                   matched_keyword=keyword)
                        return
                        
        except Exception as e:
            logger.error("Error in project association", error=str(e))
    
    def _suggest_initial_classification(self, task: Task) -> None:
        """智能初步分类建议"""
        
        # 基于关键词的情境建议
        title_lower = task.title.lower()
        description_lower = (task.description or "").lower()
        text = f"{title_lower} {description_lower}"
        
        # 情境关键词模式
        context_patterns = {
            TaskContext.COMPUTER: ["编程", "代码", "开发", "电脑", "软件", "网站", "系统"],
            TaskContext.PHONE: ["电话", "打电话", "联系", "沟通", "通话"],
            TaskContext.ERRANDS: ["买", "购买", "银行", "邮局", "外出", "取"],
            TaskContext.ONLINE: ["搜索", "查找", "网上", "在线", "下载", "上传"],
            TaskContext.READING: ["读", "阅读", "学习", "研究", "文档", "书"],
            TaskContext.MEETING: ["会议", "讨论", "面谈", "开会"],
            TaskContext.FOCUS: ["写作", "设计", "思考", "计划", "创作"]
        }
        
        for context, keywords in context_patterns.items():
            if any(keyword in text for keyword in keywords):
                task.suggested_context = context
                break
        
        # 优先级建议
        high_priority_keywords = ["紧急", "重要", "deadline", "立即", "马上"]
        low_priority_keywords = ["有空", "sometime", "考虑", "也许"]
        
        if any(keyword in text for keyword in high_priority_keywords):
            task.suggested_priority = TaskPriority.HIGH
        elif any(keyword in text for keyword in low_priority_keywords):
            task.suggested_priority = TaskPriority.LOW
        
        # 精力水平建议
        high_energy_keywords = ["创作", "设计", "规划", "学习", "开发"]
        low_energy_keywords = ["整理", "归档", "清理", "备份", "检查"]
        
        if any(keyword in text for keyword in high_energy_keywords):
            task.energy_required = EnergyLevel.HIGH
        elif any(keyword in text for keyword in low_energy_keywords):
            task.energy_required = EnergyLevel.LOW
    
    def get_inbox_tasks(self) -> List[Task]:
        """获取收件箱任务列表"""
        return self.storage.get_inbox_tasks()
    
    def get_next_actions(self, context: Optional[TaskContext] = None) -> List[Task]:
        """获取下一步行动列表
        
        根据US-009验收标准实现：
        - 通过 `/pm next` 显示所有情境的下一步行动
        - 通过 `/pm next @电脑` 显示特定情境的行动
        - 按优先级排序显示
        - 显示预估时间和精力需求
        """
        
        if context:
            tasks = self.storage.get_tasks_by_context(context)
        else:
            tasks = self.storage.get_next_actions()
        
        # 按优先级和创建时间排序
        def sort_key(task: Task) -> Tuple[int, datetime]:
            priority_order = {
                TaskPriority.HIGH: 0,
                TaskPriority.MEDIUM: 1,
                TaskPriority.LOW: 2
            }
            return (priority_order.get(task.priority, 1), task.created_at)
        
        tasks.sort(key=sort_key)
        
        return tasks
    
    def get_tasks_by_context(self, context: TaskContext) -> List[Task]:
        """根据情境获取任务"""
        return self.storage.get_tasks_by_context(context)
    
    def search_tasks(self, 
                    query: Optional[str] = None,
                    status: Optional[TaskStatus] = None,
                    context: Optional[TaskContext] = None,
                    priority: Optional[TaskPriority] = None) -> List[Task]:
        """搜索任务"""
        
        filter_obj = TaskFilter(
            search_text=query,
            status=[status] if status else None,
            context=[context] if context else None,
            priority=[priority] if priority else None
        )
        
        return self.storage.search_tasks(filter_obj)
    
    def get_task_statistics(self) -> Dict[str, Any]:
        """获取任务统计信息"""
        
        stats = self.storage.get_statistics()
        
        # 添加GTD工作流程健康度评估
        inbox_count = stats.get("inbox_count", 0)
        
        stats["workflow_health"] = {
            "inbox_overflow": inbox_count > 20,
            "needs_review": inbox_count > 10,
            "status": "healthy" if inbox_count <= 10 else "needs_attention"
        }
        
        return stats
    
    def complete_task(self, task_id: str) -> bool:
        """完成任务"""
        
        task = self.storage.get_task(task_id)
        if not task:
            return False
        
        task.mark_completed()
        success = self.storage.save_task(task)
        
        if success:
            logger.info("Task completed", 
                       task_id=task_id,
                       title=task.title)
        
        return success
    
    def update_task(self, task_id: str, updates: Dict[str, Any]) -> bool:
        """更新任务"""
        
        task = self.storage.get_task(task_id)
        if not task:
            return False
        
        # 应用更新
        for field, value in updates.items():
            if hasattr(task, field):
                setattr(task, field, value)
        
        task.updated_at = datetime.now()
        success = self.storage.save_task(task)
        
        if success:
            logger.info("Task updated", 
                       task_id=task_id,
                       title=task.title,
                       updates=list(updates.keys()))
        
        return success
    
    def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        
        task = self.storage.get_task(task_id)
        if not task:
            return False
        
        success = self.storage.delete_task(task_id)
        
        if success:
            logger.info("Task deleted", 
                       task_id=task_id,
                       title=task.title)
        
        return success
    
    def detect_current_context(self) -> Dict[str, Any]:
        """自动检测当前用户情境（US-010核心功能）
        
        自动检测：
        - 设备类型和能力
        - 网络连接状态
        - 时间和位置情境
        - 工作环境特征
        """
        
        import platform
        import subprocess
        import socket
        from pathlib import Path
        
        context = {
            'detected_at': datetime.now().isoformat(),
            'device_info': {},
            'network_info': {},
            'time_context': {},
            'location_hints': {},
            'suggested_contexts': []
        }
        
        # 设备信息检测
        try:
            context['device_info'] = {
                'platform': platform.system(),
                'machine': platform.machine(),
                'processor': platform.processor(),
                'python_version': platform.python_version(),
                'hostname': socket.gethostname()
            }
            
            # 判断设备类型
            system = platform.system()
            if system == 'Darwin':  # macOS
                context['device_info']['type'] = 'mac'
                context['suggested_contexts'].extend([TaskContext.COMPUTER, TaskContext.ONLINE])
            elif system == 'Windows':
                context['device_info']['type'] = 'windows'
                context['suggested_contexts'].extend([TaskContext.COMPUTER, TaskContext.ONLINE])
            elif system == 'Linux':
                context['device_info']['type'] = 'linux'
                context['suggested_contexts'].extend([TaskContext.COMPUTER, TaskContext.ONLINE])
                
        except Exception as e:
            logger.warning("Failed to detect device info", error=str(e))
        
        # 网络连接检测
        try:
            # 检查网络连接
            result = subprocess.run(['ping', '-c', '1', '8.8.8.8'], 
                                  capture_output=True, timeout=3)
            context['network_info']['online'] = result.returncode == 0
            
            if context['network_info']['online']:
                context['suggested_contexts'].append(TaskContext.ONLINE)
        except Exception:
            context['network_info']['online'] = False
        
        # 时间情境检测
        now = datetime.now()
        context['time_context'] = {
            'hour': now.hour,
            'day_of_week': now.weekday(),  # 0=Monday
            'is_weekend': now.weekday() >= 5,
            'time_period': self._get_time_period(now.hour)
        }
        
        # 基于时间推荐情境
        if context['time_context']['is_weekend']:
            context['suggested_contexts'].extend([TaskContext.HOME, TaskContext.ERRANDS])
        elif 9 <= now.hour <= 17:  # 工作时间
            context['suggested_contexts'].extend([TaskContext.OFFICE, TaskContext.MEETING])
        elif 18 <= now.hour <= 22:  # 晚间
            context['suggested_contexts'].extend([TaskContext.HOME, TaskContext.READING])
        elif 6 <= now.hour <= 8:  # 早晨
            context['suggested_contexts'].extend([TaskContext.HOME, TaskContext.READING])
        
        # 位置和环境线索检测
        try:
            # 检查当前工作目录，推测工作环境
            cwd = Path.cwd()
            context['location_hints']['working_directory'] = str(cwd)
            
            # 基于工作目录推测情境
            if 'projects' in str(cwd).lower() or 'work' in str(cwd).lower():
                context['suggested_contexts'].append(TaskContext.FOCUS)
            elif 'documents' in str(cwd).lower():
                context['suggested_contexts'].append(TaskContext.READING)
                
        except Exception as e:
            logger.warning("Failed to detect location hints", error=str(e))
        
        # 去重建议情境
        context['suggested_contexts'] = list(set(context['suggested_contexts']))
        
        logger.info("Context detected", 
                   device=context['device_info'].get('type'),
                   online=context['network_info'].get('online'),
                   suggested=len(context['suggested_contexts']))
        
        return context
    
    def _get_time_period(self, hour: int) -> str:
        """获取时间段描述"""
        if 6 <= hour < 12:
            return "morning"
        elif 12 <= hour < 17:
            return "afternoon"  
        elif 17 <= hour < 21:
            return "evening"
        else:
            return "night"
    
    def get_context_filtered_tasks(self, 
                                  auto_detect: bool = True,
                                  context_override: Optional[TaskContext] = None,
                                  energy_level: Optional[EnergyLevel] = None) -> Dict[str, Any]:
        """获取情境过滤的任务列表（US-010核心功能）
        
        智能情境过滤：
        - 自动检测用户情境
        - 根据情境筛选可执行任务
        - 考虑精力水平匹配
        - 提供情境切换建议
        """
        
        result = {
            'detected_context': None,
            'active_contexts': [],
            'filtered_tasks': [],
            'context_suggestions': [],
            'stats': {}
        }
        
        # 自动检测情境
        if auto_detect:
            detected = self.detect_current_context()
            result['detected_context'] = detected
            result['context_suggestions'] = detected['suggested_contexts']
        
        # 确定活跃情境
        if context_override:
            result['active_contexts'] = [context_override]
        elif auto_detect and result['context_suggestions']:
            result['active_contexts'] = result['context_suggestions']
        else:
            result['active_contexts'] = [TaskContext.COMPUTER]  # 默认情境
        
        # 获取所有下一步行动
        all_tasks = self.get_next_actions()
        
        # 情境过滤
        filtered_tasks = []
        
        for task in all_tasks:
            task_matches = False
            
            # 检查任务情境是否匹配
            if task.context:
                task_matches = task.context in result['active_contexts']
            else:
                # 无情境任务在任何情境下都可执行
                task_matches = True
            
            # 精力水平过滤
            if task_matches and energy_level and task.energy_required:
                # 只有精力需求小于等于当前精力水平的任务才匹配
                energy_order = {
                    EnergyLevel.LOW: 1,
                    EnergyLevel.MEDIUM: 2, 
                    EnergyLevel.HIGH: 3
                }
                current_energy = energy_order.get(energy_level, 2)
                required_energy = energy_order.get(task.energy_required, 2)
                task_matches = required_energy <= current_energy
            
            if task_matches:
                filtered_tasks.append(task)
        
        result['filtered_tasks'] = filtered_tasks
        
        # 统计信息
        result['stats'] = {
            'total_tasks': len(all_tasks),
            'filtered_tasks': len(filtered_tasks),
            'filter_ratio': len(filtered_tasks) / len(all_tasks) if all_tasks else 0.0,
            'contexts_matched': len(result['active_contexts'])
        }
        
        logger.info("Context filtering completed",
                   total=len(all_tasks),
                   filtered=len(filtered_tasks),
                   contexts=len(result['active_contexts']))
        
        return result
    
    def suggest_smart_contexts(self, user_context: Dict[str, Any] = None) -> List[TaskContext]:
        """智能情境推荐（简化版，主要功能已移至detect_current_context）"""
        
        if user_context is None:
            # 使用自动检测
            detected = self.detect_current_context()
            return detected['suggested_contexts']
        
        suggested_contexts = []
        
        # 基于设备类型推荐
        device_type = user_context.get('device_type', 'computer')
        
        if device_type == 'computer':
            suggested_contexts.extend([TaskContext.COMPUTER, TaskContext.ONLINE])
        elif device_type == 'mobile':
            suggested_contexts.extend([TaskContext.PHONE, TaskContext.READING])
        
        # 基于时间推荐
        current_hour = datetime.now().hour
        
        if 9 <= current_hour <= 17:  # 工作时间
            suggested_contexts.extend([TaskContext.OFFICE, TaskContext.MEETING])
        elif 18 <= current_hour <= 22:  # 晚间
            suggested_contexts.extend([TaskContext.HOME, TaskContext.READING])
        
        # 去重并返回
        return list(set(suggested_contexts))
    
    def get_recommended_tasks(self, 
                            context: Optional[TaskContext] = None,
                            energy_level: Optional[EnergyLevel] = None,
                            max_count: int = 10) -> List[Task]:
        """获取智能推荐任务
        
        根据用户当前情境和精力水平推荐最优任务
        """
        
        # 构建过滤条件
        filter_obj = TaskFilter(
            status=[TaskStatus.NEXT_ACTION],
            context=[context] if context else None,
            energy_level=[energy_level] if energy_level else None
        )
        
        # 搜索匹配任务
        tasks = self.storage.search_tasks(filter_obj)
        
        # 智能排序
        def recommendation_score(task: Task) -> float:
            score = 0.0
            
            # 优先级权重
            priority_weights = {
                TaskPriority.HIGH: 3.0,
                TaskPriority.MEDIUM: 2.0,
                TaskPriority.LOW: 1.0
            }
            score += priority_weights.get(task.priority, 2.0)
            
            # 时间紧迫性
            if task.due_date:
                days_until_due = (task.due_date.date() - datetime.now().date()).days
                if days_until_due <= 1:
                    score += 2.0
                elif days_until_due <= 7:
                    score += 1.0
            
            # 项目关联加权
            if task.project_name:
                score += 0.5
            
            # 预估时长偏好（短任务优先）
            if task.estimated_duration and task.estimated_duration <= 30:
                score += 0.5
            
            return score
        
        # 排序并限制数量
        tasks.sort(key=recommendation_score, reverse=True)
        
        return tasks[:max_count]
    
    def _load_classification_history(self) -> None:
        """加载分类学习历史（US-008）"""
        
        history_file = self.config.data_dir / "classification_history.json"
        
        if history_file.exists():
            try:
                import json
                with open(history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._classification_history = data.get('history', {})
                    self._context_patterns = data.get('patterns', {})
                    logger.info("Classification history loaded", 
                               patterns=len(self._context_patterns))
            except Exception as e:
                logger.warning("Failed to load classification history", error=str(e))
                self._classification_history = {}
                self._context_patterns = {}
        else:
            self._classification_history = {}
            self._context_patterns = {}
    
    def _save_classification_history(self) -> None:
        """保存分类学习历史"""
        
        history_file = self.config.data_dir / "classification_history.json"
        
        try:
            import json
            history_file.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                'history': self._classification_history,
                'patterns': self._context_patterns,
                'updated_at': datetime.now().isoformat()
            }
            
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            logger.info("Classification history saved")
            
        except Exception as e:
            logger.error("Failed to save classification history", error=str(e))
    
    def learn_from_classification(self, task: Task, user_decision: Dict[str, Any]) -> None:
        """从用户分类决策中学习（US-008核心功能）
        
        学习用户的分类习惯，包括：
        - 情境选择偏好
        - 优先级判断模式
        - 精力需求评估习惯
        - 项目关联模式
        """
        
        # 提取任务特征
        task_features = self._extract_task_features(task)
        
        # 记录用户决策
        decision_record = {
            'task_id': task.id,
            'task_features': task_features,
            'user_decision': user_decision,
            'timestamp': datetime.now().isoformat(),
            'original_suggestion': {
                'context': task.suggested_context,
                'priority': task.suggested_priority,
                'energy_required': task.energy_required
            }
        }
        
        # 存储到历史记录
        self._classification_history[task.id] = decision_record
        
        # 更新模式学习
        self._update_learning_patterns(task_features, user_decision)
        
        # 保存学习结果
        self._save_classification_history()
        
        logger.info("Learned from user classification", 
                   task_id=task.id,
                   context=user_decision.get('context'),
                   priority=user_decision.get('priority'))
    
    def _extract_task_features(self, task: Task) -> Dict[str, Any]:
        """提取任务特征用于学习"""
        
        title_lower = task.title.lower()
        desc_lower = (task.description or "").lower()
        
        return {
            'title_words': title_lower.split(),
            'description_words': desc_lower.split(),
            'title_length': len(task.title),
            'has_description': bool(task.description),
            'capture_source': task.capture_source,
            'capture_location': task.capture_location,
            'project_associated': bool(task.project_name),
            'has_due_date': bool(task.due_date),
            'contains_keywords': {
                'urgent': any(word in title_lower + desc_lower 
                             for word in ['紧急', '立即', 'urgent', '马上']),
                'meeting': any(word in title_lower + desc_lower 
                              for word in ['会议', '讨论', 'meeting', '开会']),
                'coding': any(word in title_lower + desc_lower 
                             for word in ['编程', '代码', 'code', '开发']),
                'phone': any(word in title_lower + desc_lower 
                            for word in ['电话', '联系', 'call', '通话']),
                'reading': any(word in title_lower + desc_lower 
                              for word in ['读', '阅读', 'read', '学习'])
            }
        }
    
    def _update_learning_patterns(self, features: Dict[str, Any], decision: Dict[str, Any]) -> None:
        """更新学习模式"""
        
        # 学习情境选择模式
        if 'context' in decision:
            context = decision['context']
            if context not in self._context_patterns:
                self._context_patterns[context] = []
            
            # 记录导致此情境选择的关键词
            for word in features['title_words'][:5]:  # 只记录前5个单词
                if len(word) > 2:
                    self._context_patterns[context].append(word)
            
            # 限制模式数量避免过拟合
            if len(self._context_patterns[context]) > 50:
                self._context_patterns[context] = self._context_patterns[context][-30:]
    
    def get_smart_suggestions(self, task: Task) -> Dict[str, Any]:
        """基于学习历史提供智能建议（US-008增强版）
        
        结合基础规则和学习历史提供更准确的分类建议
        """
        
        # 基础建议
        self._suggest_initial_classification(task)
        
        # 基于学习历史的增强建议
        enhanced_suggestions = self._get_learned_suggestions(task)
        
        # 合并建议
        suggestions = {
            'context': enhanced_suggestions.get('context') or task.suggested_context,
            'priority': enhanced_suggestions.get('priority') or task.suggested_priority,
            'energy_required': enhanced_suggestions.get('energy_required') or task.energy_required,
            'confidence': enhanced_suggestions.get('confidence', 0.5),
            'reasoning': enhanced_suggestions.get('reasoning', [])
        }
        
        return suggestions
    
    def _get_learned_suggestions(self, task: Task) -> Dict[str, Any]:
        """基于学习历史生成建议"""
        
        features = self._extract_task_features(task)
        suggestions = {}
        reasoning = []
        confidence = 0.0
        
        # 基于学习模式匹配情境
        title_words = set(features['title_words'])
        
        best_context_match = None
        max_matches = 0
        
        for context, learned_words in self._context_patterns.items():
            matches = len(title_words.intersection(set(learned_words)))
            if matches > max_matches and matches > 0:
                max_matches = matches
                best_context_match = context
                confidence = min(0.9, matches * 0.2)
        
        if best_context_match:
            suggestions['context'] = TaskContext(best_context_match) if isinstance(best_context_match, str) else best_context_match
            reasoning.append(f"基于{max_matches}个关键词匹配选择情境")
        
        # 基于历史记录学习优先级模式
        if features['contains_keywords']['urgent']:
            urgent_history = [
                record for record in self._classification_history.values()
                if record['task_features'].get('contains_keywords', {}).get('urgent', False)
            ]
            
            if urgent_history:
                common_priority = max(set(
                    record['user_decision'].get('priority', TaskPriority.MEDIUM)
                    for record in urgent_history[-10:]  # 最近10次记录
                ), key=lambda x: [
                    record['user_decision'].get('priority', TaskPriority.MEDIUM)
                    for record in urgent_history[-10:]
                ].count(x))
                
                suggestions['priority'] = common_priority
                confidence = max(confidence, 0.7)
                reasoning.append("基于紧急任务历史模式")
        
        suggestions['confidence'] = confidence
        suggestions['reasoning'] = reasoning
        
        return suggestions
    
    def get_classification_stats(self) -> Dict[str, Any]:
        """获取分类学习统计信息（US-008验收标准）"""
        
        return {
            'total_learned_tasks': len(self._classification_history),
            'learned_patterns': len(self._context_patterns),
            'context_patterns': {
                context: len(words) 
                for context, words in self._context_patterns.items()
            },
            'recent_accuracy': self._calculate_recent_accuracy(),
            'learning_health': self._assess_learning_health()
        }
    
    def _calculate_recent_accuracy(self) -> float:
        """计算最近建议的准确率"""
        
        if len(self._classification_history) < 5:
            return 0.0
        
        recent_records = list(self._classification_history.values())[-20:]
        correct_predictions = 0
        
        for record in recent_records:
            original = record.get('original_suggestion', {})
            decision = record.get('user_decision', {})
            
            if original.get('context') == decision.get('context'):
                correct_predictions += 1
        
        return correct_predictions / len(recent_records) if recent_records else 0.0
    
    def _assess_learning_health(self) -> str:
        """评估学习系统健康状态"""
        
        total_tasks = len(self._classification_history)
        patterns_count = len(self._context_patterns)
        recent_accuracy = self._calculate_recent_accuracy()
        
        if total_tasks < 10:
            return "learning"  # 学习初期
        elif recent_accuracy > 0.8:
            return "excellent"  # 优秀
        elif recent_accuracy > 0.6:
            return "good"  # 良好
        elif recent_accuracy > 0.4:
            return "fair"  # 一般
        else:
            return "needs_improvement"  # 需要改进
    
    def get_intelligent_recommendations(self, 
                                      max_recommendations: int = 5,
                                      context_override: Optional[TaskContext] = None) -> List[Tuple[Task, Any]]:
        """获取基于多书籍理论的智能任务推荐（US-011核心功能）
        
        Args:
            max_recommendations: 最大推荐数量
            context_override: 指定情境过滤
            
        Returns:
            推荐任务列表，包含详细评分信息
        """
        
        # 获取所有下一步行动任务
        candidate_tasks = self.get_next_actions()
        
        if context_override:
            # 按情境过滤
            candidate_tasks = [t for t in candidate_tasks if t.context == context_override]
        
        if not candidate_tasks:
            logger.warning("No candidate tasks available for recommendations")
            return []
        
        # 获取当前情境信息
        current_context = self.detect_current_context()
        
        # 使用推荐引擎生成推荐
        recommendations = self.recommendation_engine.recommend_tasks(
            tasks=candidate_tasks,
            current_context=current_context,
            max_recommendations=max_recommendations
        )
        
        logger.info("Intelligent recommendations generated",
                   candidates=len(candidate_tasks),
                   recommendations=len(recommendations))
        
        return recommendations
    
    def explain_recommendation(self, task: Task) -> Dict[str, Any]:
        """解释单个任务的推荐逻辑（为US-012做准备）
        
        Args:
            task: 要解释的任务
            
        Returns:
            包含推荐逻辑说明的详细信息
        """
        
        current_context = self.detect_current_context()
        score = self.recommendation_engine._calculate_recommendation_score(task, current_context)
        
        explanation = {
            'task_title': task.title,
            'total_score': score.total_score,
            'confidence': score.confidence,
            'framework_scores': {
                framework.value: score
                for framework, score in score.framework_scores.items()
            },
            'reasoning': score.reasoning,
            'urgency_factor': score.urgency_factor,
            'energy_match': score.energy_match,
            'framework_explanations': self.recommendation_engine.get_framework_explanations()
        }
        
        return explanation
    
    def record_user_task_choice(self, chosen_task: Task) -> None:
        """记录用户任务选择用于学习（US-013）"""
        
        # 获取最近的推荐结果
        current_recommendations = self.get_intelligent_recommendations(max_recommendations=10)
        
        if current_recommendations:
            # 记录用户选择
            self.recommendation_engine.record_user_choice(chosen_task, current_recommendations)
            logger.info("User task choice recorded for learning",
                       task=chosen_task.title[:30])
        else:
            logger.debug("No recent recommendations to record choice against")
    
    def get_preference_learning_stats(self) -> Dict[str, Any]:
        """获取偏好学习统计信息（US-013验收标准）"""
        
        metrics = self.recommendation_engine.get_learning_metrics()
        
        return {
            'total_choices': metrics.total_choices,
            'recent_accuracy': metrics.recent_accuracy,
            'framework_preferences': metrics.framework_preferences,
            'context_preferences': metrics.context_preferences,
            'learning_trend': metrics.learning_trend,
            'confidence_score': metrics.confidence_score,
            'learning_status': self._assess_learning_status(metrics)
        }
    
    def _assess_learning_status(self, metrics) -> str:
        """评估学习状态"""
        
        if metrics.total_choices < 5:
            return "初期收集"
        elif metrics.total_choices < 20:
            return "积极学习"
        elif metrics.confidence_score > 0.7:
            return "学习成熟"
        elif metrics.confidence_score > 0.4:
            return "持续优化"
        else:
            return "需要更多反馈"