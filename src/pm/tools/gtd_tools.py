"""GTD核心工具AI可调用函数 - Sprint 13架构重构

这些函数被设计为独立的、可供AI直接调用的工具函数
实现pm capture、pm next、pm clarify等核心GTD命令的业务逻辑
"""

import structlog
from datetime import datetime, date
from typing import List, Dict, Any, Optional, Tuple

from pm.core.config import PMConfig
from pm.agents.gtd_agent import GTDAgent
from pm.models.task import Task, TaskStatus, TaskContext, TaskPriority

logger = structlog.get_logger()


# ========== 核心工具函数 ==========

def capture_task(
    content: str,
    context: Optional[str] = None,
    priority: Optional[str] = None,
    due_date: Optional[str] = None,
    project: Optional[str] = None,
    config: Optional[PMConfig] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """快速捕获任务到收件箱
    
    Args:
        content: 任务内容描述
        context: 执行上下文 (@电脑, @电话等)
        priority: 优先级 (high/medium/low)
        due_date: 截止日期 (YYYY-MM-DD)
        project: 所属项目名称
        config: 配置对象
        
    Returns:
        Tuple[成功标志, 消息, 任务信息字典]
    """
    try:
        if not content or not content.strip():
            return False, "任务内容不能为空", None
        
        config = config or PMConfig()
        agent = GTDAgent(config)
        
        # 解析优先级
        task_priority = None
        if priority:
            priority_map = {
                "high": TaskPriority.HIGH,
                "medium": TaskPriority.MEDIUM,
                "low": TaskPriority.LOW
            }
            task_priority = priority_map.get(priority.lower())
        
        # 解析上下文
        task_context = None
        if context:
            context_map = {
                "@电脑": TaskContext.COMPUTER,
                "@电话": TaskContext.PHONE,
                "@会议": TaskContext.MEETING,
                "@专注": TaskContext.FOCUS,
                "@办公室": TaskContext.OFFICE,
                "@阅读": TaskContext.READING,
                "@家": TaskContext.HOME
            }
            task_context = context_map.get(context)
        
        # 解析截止日期
        task_due_date = None
        if due_date:
            try:
                task_due_date = datetime.fromisoformat(due_date)
            except ValueError:
                return False, f"日期格式无效: {due_date}，请使用 YYYY-MM-DD 格式", None
        
        # 使用GTD智能捕获
        task = agent.capture_task(
            title=content.strip(),
            description=None,
            capture_context={
                "source": "ai_tool_function",
                "context": context,
                "priority": priority,
                "due_date": due_date,
                "project": project
            }
        )
        
        # 手动设置额外属性
        if task:
            if task_context:
                task.context = task_context
            if task_priority:
                task.priority = task_priority
            if task_due_date:
                task.due_date = task_due_date
            if project:
                task.project_name = project
            
            # 保存更新后的任务
            success = agent.storage.save_task(task)
            task_id = task.id if success else None
        else:
            success = False
            task_id = None
        
        if success and task_id:
            # 获取创建的任务信息
            task = agent.storage.get_task(task_id)
            if task:
                task_info = {
                    "task_id": task.id,
                    "short_id": task.id[:8],
                    "title": task.title,
                    "status": task.status.value,
                    "context": task.context.value if task.context else None,
                    "priority": task.priority.value if task.priority else None,
                    "created_at": task.created_at.isoformat(),
                    "due_date": task.due_date.isoformat() if task.due_date else None,
                    "project_name": task.project_name
                }
                
                logger.info("Task captured via tool function", 
                           task_id=task.id,
                           title=task.title[:50])
                
                return True, f"任务已捕获到收件箱: {task.title}", task_info
        
        return False, "捕获任务失败", None
        
    except Exception as e:
        error_msg = f"捕获任务时发生错误: {str(e)}"
        logger.error("capture_task tool function failed", error=str(e))
        return False, error_msg, None


def get_next_actions(
    context: Optional[str] = None,
    limit: int = 10,
    energy_level: Optional[str] = None,
    config: Optional[PMConfig] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """获取下一步行动任务列表
    
    Args:
        context: 执行上下文过滤
        limit: 返回任务数量限制
        energy_level: 精力水平过滤 (high/medium/low)
        config: 配置对象
        
    Returns:
        Tuple[成功标志, 消息, 下一步行动信息字典]
    """
    try:
        config = config or PMConfig()
        agent = GTDAgent(config)
        
        # 解析上下文过滤器
        context_enum = None
        if context:
            context_map = {
                "@电脑": TaskContext.COMPUTER,
                "@电话": TaskContext.PHONE,
                "@会议": TaskContext.MEETING,
                "@专注": TaskContext.FOCUS,
                "@办公室": TaskContext.OFFICE,
                "@阅读": TaskContext.READING,
                "@家": TaskContext.HOME
            }
            context_enum = context_map.get(context)
        
        # 获取下一步行动
        next_tasks = agent.get_next_actions(context=context_enum)
        
        if not next_tasks:
            return True, "当前没有下一步行动任务", {
                "tasks": [],
                "count": 0,
                "message": "所有任务都已完成或在处理中"
            }
        
        # 按能量级别过滤
        if energy_level:
            energy_map = {
                "high": "high",
                "medium": "medium", 
                "low": "low"
            }
            target_energy = energy_map.get(energy_level.lower())
            if target_energy:
                filtered_tasks = [t for t in next_tasks if t.energy_required and t.energy_required.value == target_energy]
                if filtered_tasks:
                    next_tasks = filtered_tasks
        
        # 格式化任务信息
        tasks_info = []
        for task in next_tasks[:limit]:
            task_info = {
                "task_id": task.id,
                "short_id": task.id[:8],
                "title": task.title,
                "description": task.description,
                "context": task.context.value if task.context else "未分类",
                "priority": task.priority.value if task.priority else "medium",
                "energy_required": task.energy_required.value if task.energy_required else "medium",
                "estimated_duration": task.estimated_duration,
                "due_date": task.due_date.isoformat() if task.due_date else None,
                "project_name": task.project_name,
                "created_at": task.created_at.isoformat(),
                "is_overdue": task.is_overdue() if hasattr(task, 'is_overdue') else False
            }
            tasks_info.append(task_info)
        
        result_info = {
            "tasks": tasks_info,
            "count": len(tasks_info),
            "total_next_actions": len(next_tasks),
            "context_filter": context,
            "energy_filter": energy_level
        }
        
        message = f"找到 {len(tasks_info)} 个下一步行动任务"
        if context:
            message += f"（上下文: {context}）"
        if energy_level:
            message += f"（精力级别: {energy_level}）"
        
        logger.info("Next actions retrieved via tool function", 
                   count=len(tasks_info),
                   context=context,
                   energy=energy_level)
        
        return True, message, result_info
        
    except Exception as e:
        error_msg = f"获取下一步行动时发生错误: {str(e)}"
        logger.error("get_next_actions tool function failed", error=str(e))
        return False, error_msg, None


def clarify_inbox_tasks(
    auto_process: bool = False,
    batch_size: int = 5,
    config: Optional[PMConfig] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """GTD理清流程 - 处理收件箱任务
    
    Args:
        auto_process: 是否自动处理（使用AI分类）
        batch_size: 批量处理任务数量
        config: 配置对象
        
    Returns:
        Tuple[成功标志, 消息, 理清结果字典]
    """
    try:
        config = config or PMConfig()
        agent = GTDAgent(config)
        
        # 获取收件箱任务
        inbox_tasks = agent.storage.get_tasks_by_status(TaskStatus.INBOX)
        
        if not inbox_tasks:
            return True, "收件箱为空，没有需要理清的任务", {
                "processed_count": 0,
                "remaining_count": 0,
                "actions": []
            }
        
        processed_count = 0
        actions = []
        tasks_to_process = inbox_tasks[:batch_size]
        
        for task in tasks_to_process:
            try:
                if auto_process:
                    # 使用AI自动分类和处理
                    classification_result = agent.classify_and_organize_task(task.id)
                    
                    if classification_result:
                        processed_count += 1
                        actions.append({
                            "task_id": task.id[:8],
                            "title": task.title,
                            "action": "自动分类",
                            "new_status": classification_result.get("status", "未知"),
                            "new_context": classification_result.get("context", "未分类"),
                            "new_priority": classification_result.get("priority", "medium")
                        })
                    else:
                        actions.append({
                            "task_id": task.id[:8],
                            "title": task.title,
                            "action": "分类失败",
                            "reason": "AI分类系统暂时不可用"
                        })
                else:
                    # 标记为需要手动处理
                    actions.append({
                        "task_id": task.id[:8],
                        "title": task.title,
                        "action": "待手动处理",
                        "current_status": task.status.value,
                        "suggestions": _get_task_processing_suggestions(task)
                    })
                
            except Exception as e:
                actions.append({
                    "task_id": task.id[:8],
                    "title": task.title,
                    "action": "处理失败",
                    "error": str(e)
                })
        
        remaining_count = len(inbox_tasks) - processed_count
        
        result_info = {
            "processed_count": processed_count,
            "remaining_count": remaining_count,
            "total_inbox_count": len(inbox_tasks),
            "actions": actions,
            "auto_processed": auto_process,
            "batch_size": batch_size
        }
        
        if auto_process:
            message = f"自动理清完成，处理了 {processed_count} 个任务，剩余 {remaining_count} 个"
        else:
            message = f"理清分析完成，发现 {len(tasks_to_process)} 个任务需要处理"
        
        logger.info("Clarify process completed via tool function", 
                   processed=processed_count,
                   remaining=remaining_count,
                   auto=auto_process)
        
        return True, message, result_info
        
    except Exception as e:
        error_msg = f"理清任务时发生错误: {str(e)}"
        logger.error("clarify_inbox_tasks tool function failed", error=str(e))
        return False, error_msg, None


def process_single_task(
    task_id: str,
    action: str,
    new_status: Optional[str] = None,
    new_context: Optional[str] = None,
    new_priority: Optional[str] = None,
    notes: Optional[str] = None,
    config: Optional[PMConfig] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """处理单个任务（GTD理清流程的一部分）
    
    Args:
        task_id: 任务ID
        action: 处理动作 (complete/defer/delegate/delete/organize)
        new_status: 新状态
        new_context: 新上下文
        new_priority: 新优先级  
        notes: 处理备注
        config: 配置对象
        
    Returns:
        Tuple[成功标志, 消息, 处理结果字典]
    """
    try:
        config = config or PMConfig()
        agent = GTDAgent(config)
        
        # 查找任务
        task = agent.storage.get_task(task_id)
        if not task:
            return False, f"未找到任务: {task_id}", None
        
        old_status = task.status.value
        old_context = task.context.value if task.context else "未分类"
        old_priority = task.priority.value if task.priority else "medium"
        
        result_info = {
            "task_id": task.id,
            "short_id": task.id[:8],
            "title": task.title,
            "action": action,
            "old_status": old_status,
            "old_context": old_context,
            "old_priority": old_priority
        }
        
        # 根据动作执行相应操作
        if action == "complete":
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            message = f"任务已标记为完成: {task.title}"
            
        elif action == "defer":
            task.status = TaskStatus.SOMEDAY_MAYBE
            message = f"任务已推迟到将来: {task.title}"
            
        elif action == "delegate":
            task.status = TaskStatus.WAITING_FOR
            if notes:
                task.waiting_for = notes
            message = f"任务已委派: {task.title}"
            
        elif action == "delete":
            agent.storage.delete_task(task.id)
            result_info["deleted"] = True
            message = f"任务已删除: {task.title}"
            return True, message, result_info
            
        elif action == "organize":
            # 重新组织任务
            if new_status:
                status_map = {
                    "next_action": TaskStatus.NEXT_ACTION,
                    "project": TaskStatus.PROJECT,
                    "waiting": TaskStatus.WAITING_FOR,
                    "someday": TaskStatus.SOMEDAY_MAYBE
                }
                if new_status in status_map:
                    task.status = status_map[new_status]
            
            if new_context:
                context_map = {
                    "@电脑": TaskContext.COMPUTER,
                    "@电话": TaskContext.PHONE,
                    "@会议": TaskContext.MEETING,
                    "@专注": TaskContext.FOCUS,
                    "@办公室": TaskContext.OFFICE,
                    "@阅读": TaskContext.READING,
                    "@家": TaskContext.HOME
                }
                if new_context in context_map:
                    task.context = context_map[new_context]
            
            if new_priority:
                priority_map = {
                    "high": TaskPriority.HIGH,
                    "medium": TaskPriority.MEDIUM,
                    "low": TaskPriority.LOW
                }
                if new_priority in priority_map:
                    task.priority = priority_map[new_priority]
            
            message = f"任务已重新组织: {task.title}"
            
        else:
            return False, f"未知的处理动作: {action}", None
        
        # 添加处理备注
        if notes:
            if not hasattr(task, 'notes') or not task.notes:
                task.notes = []
            task.notes.append({
                "content": notes,
                "created_at": datetime.now().isoformat(),
                "action": action
            })
        
        # 保存任务
        success = agent.storage.save_task(task)
        if not success:
            return False, "保存任务失败", None
        
        # 更新结果信息
        result_info.update({
            "new_status": task.status.value,
            "new_context": task.context.value if task.context else "未分类",
            "new_priority": task.priority.value if task.priority else "medium",
            "notes_added": bool(notes),
            "updated_at": task.updated_at.isoformat()
        })
        
        logger.info("Task processed via tool function", 
                   task_id=task.id,
                   action=action,
                   new_status=task.status.value)
        
        return True, message, result_info
        
    except Exception as e:
        error_msg = f"处理任务时发生错误: {str(e)}"
        logger.error("process_single_task tool function failed", task_id=task_id, error=str(e))
        return False, error_msg, None


def get_task_details(
    task_id: str,
    config: Optional[PMConfig] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """获取任务详细信息
    
    Args:
        task_id: 任务ID（支持短ID）
        config: 配置对象
        
    Returns:
        Tuple[成功标志, 消息, 任务详情字典]
    """
    try:
        config = config or PMConfig()
        agent = GTDAgent(config)
        
        # 查找任务（支持短ID）
        task = agent.storage.get_task(task_id)
        if not task:
            # 尝试通过短ID查找
            all_tasks = agent.storage.get_all_tasks()
            matching_tasks = [t for t in all_tasks if t.id.startswith(task_id)]
            if len(matching_tasks) == 1:
                task = matching_tasks[0]
            elif len(matching_tasks) > 1:
                return False, f"找到多个匹配的任务ID: {task_id}，请提供更具体的ID", None
            else:
                return False, f"未找到任务: {task_id}", None
        
        # 构建详细信息
        task_details = {
            "id": task.id,
            "short_id": task.id[:8],
            "title": task.title,
            "description": task.description,
            "status": task.status.value,
            "context": task.context.value if task.context else None,
            "priority": task.priority.value if task.priority else None,
            "energy_required": task.energy_required.value if task.energy_required else None,
            "estimated_duration": task.estimated_duration,
            "created_at": task.created_at.isoformat(),
            "updated_at": task.updated_at.isoformat(),
            "due_date": task.due_date.isoformat() if task.due_date else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "project_name": task.project_name,
            "parent_task_id": task.parent_task_id,
            "waiting_for": task.waiting_for,
            "tags": task.tags,
            "categories": task.categories,
            "notes": getattr(task, 'notes', []),
            "attachments": getattr(task, 'attachments', [])
        }
        
        # 添加计算字段
        if hasattr(task, 'is_overdue'):
            task_details["is_overdue"] = task.is_overdue()
        
        if task.due_date:
            days_until_due = (task.due_date.date() - date.today()).days
            task_details["days_until_due"] = days_until_due
            task_details["due_status"] = "过期" if days_until_due < 0 else "今天到期" if days_until_due == 0 else f"{days_until_due}天后到期"
        
        message = f"任务详情: {task.title}"
        
        return True, message, task_details
        
    except Exception as e:
        error_msg = f"获取任务详情时发生错误: {str(e)}"
        logger.error("get_task_details tool function failed", task_id=task_id, error=str(e))
        return False, error_msg, None


# ========== 辅助函数 ==========

def _get_task_processing_suggestions(task: Task) -> List[str]:
    """为任务生成处理建议"""
    suggestions = []
    
    # 基于任务内容的建议
    content_lower = task.title.lower()
    
    if any(word in content_lower for word in ["会议", "讨论", "面谈"]):
        suggestions.append("建议设置上下文为 @会议")
    
    if any(word in content_lower for word in ["电话", "通话", "联系"]):
        suggestions.append("建议设置上下文为 @电话")
    
    if any(word in content_lower for word in ["代码", "编程", "系统"]):
        suggestions.append("建议设置上下文为 @电脑")
    
    if any(word in content_lower for word in ["阅读", "学习", "研究"]):
        suggestions.append("建议设置上下文为 @阅读")
    
    # 基于紧急性的建议
    if any(word in content_lower for word in ["紧急", "立即", "马上"]):
        suggestions.append("建议设置优先级为高")
    
    # 基于时间的建议
    if task.due_date:
        days_left = (task.due_date.date() - date.today()).days
        if days_left <= 0:
            suggestions.append("任务已过期，建议立即处理或重新安排")
        elif days_left <= 3:
            suggestions.append("任务即将到期，建议优先处理")
    
    # 默认建议
    if not suggestions:
        suggestions.append("建议分析任务是否可行动，如果是则移至下一步行动")
    
    return suggestions