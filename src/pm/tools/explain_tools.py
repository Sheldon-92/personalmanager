"""AI可调用的推荐解释工具函数 - 重构自explain命令"""

from typing import Tuple, Optional, Dict, Any
import structlog
from datetime import datetime

from pm.core.config import PMConfig
from pm.agents.gtd_agent import GTDAgent
from pm.models.task import Task

logger = structlog.get_logger()


def explain_task_recommendation(
    task_id: str,
    config: Optional[PMConfig] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """解释任务推荐逻辑的AI可调用工具函数
    
    提供可解释的AI推荐，展示：
    - 各理论框架的评分详情
    - 推荐逻辑的步骤分析
    - 涉及的书籍理论说明
    - 评分计算过程透明化
    
    Args:
        task_id: 任务ID（支持短ID或完整ID）
        config: 可选的PMConfig实例
        
    Returns:
        Tuple[bool, str, Optional[Dict[str, Any]]]: (成功状态, 消息, 解释数据)
    """
    
    try:
        # 初始化配置
        if config is None:
            config = PMConfig()
        
        if not config.is_initialized():
            return False, "系统未初始化。请先运行 pm setup 进行设置。", None
        
        # 创建GTD Agent
        agent = GTDAgent(config)
        
        # 查找任务
        task = agent.storage.get_task(task_id)
        if not task:
            return False, f"未找到任务ID: {task_id}。请确认任务ID正确。", None
        
        # 获取推荐解释
        explanation = agent.explain_recommendation(task)
        
        # 构建返回数据
        result_data = {
            'task_info': {
                'id': task.id,
                'title': task.title,
                'description': task.description,
                'context': task.context.value if task.context else None,
                'priority': task.priority.value if task.priority else None,
                'energy_required': task.energy_required.value if task.energy_required else None,
                'estimated_duration': task.estimated_duration,
                'due_date': task.due_date.isoformat() if task.due_date else None
            },
            'recommendation_analysis': {
                'total_score': explanation['total_score'],
                'confidence': explanation['confidence'],
                'urgency_factor': explanation['urgency_factor'],
                'energy_match': explanation['energy_match'],
                'framework_scores': explanation['framework_scores']
            },
            'framework_details': _get_framework_details(explanation['framework_scores']),
            'reasoning_steps': _generate_reasoning_steps(explanation, task),
            'theory_explanations': _get_theory_explanations(explanation['framework_scores'])
        }
        
        logger.info("Task recommendation explained successfully",
                   task_id=task_id, total_score=explanation['total_score'])
        
        return True, "任务推荐解释生成成功", result_data
        
    except Exception as e:
        logger.error("Failed to explain task recommendation",
                    task_id=task_id, error=str(e))
        return False, f"解释任务推荐时发生错误: {str(e)}", None


def get_framework_scoring_details(
    task_id: str,
    config: Optional[PMConfig] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """获取任务的理论框架评分详情
    
    Args:
        task_id: 任务ID
        config: 可选的PMConfig实例
        
    Returns:
        Tuple[bool, str, Optional[Dict[str, Any]]]: (成功状态, 消息, 框架评分数据)
    """
    
    try:
        if config is None:
            config = PMConfig()
        
        if not config.is_initialized():
            return False, "系统未初始化", None
        
        agent = GTDAgent(config)
        task = agent.storage.get_task(task_id)
        if not task:
            return False, f"未找到任务ID: {task_id}", None
        
        explanation = agent.explain_recommendation(task)
        framework_scores = explanation['framework_scores']
        
        # 计算详细的框架评分信息
        framework_details = _get_framework_details(framework_scores)
        
        result_data = {
            'framework_scores': framework_scores,
            'framework_details': framework_details,
            'total_weighted_score': sum(score * weight for score, weight in 
                                      zip(framework_scores.values(), 
                                          [0.25, 0.20, 0.20, 0.15, 0.10, 0.10])),
            'top_frameworks': sorted(framework_scores.items(), 
                                   key=lambda x: x[1], reverse=True)[:3]
        }
        
        return True, "框架评分详情获取成功", result_data
        
    except Exception as e:
        logger.error("Failed to get framework scoring details",
                    task_id=task_id, error=str(e))
        return False, f"获取框架评分详情时发生错误: {str(e)}", None


def generate_recommendation_reasoning(
    task_id: str,
    config: Optional[PMConfig] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """生成任务推荐的逻辑推理步骤
    
    Args:
        task_id: 任务ID
        config: 可选的PMConfig实例
        
    Returns:
        Tuple[bool, str, Optional[Dict[str, Any]]]: (成功状态, 消息, 推理步骤数据)
    """
    
    try:
        if config is None:
            config = PMConfig()
        
        if not config.is_initialized():
            return False, "系统未初始化", None
        
        agent = GTDAgent(config)
        task = agent.storage.get_task(task_id)
        if not task:
            return False, f"未找到任务ID: {task_id}", None
        
        explanation = agent.explain_recommendation(task)
        reasoning_steps = _generate_reasoning_steps(explanation, task)
        
        result_data = {
            'reasoning_steps': reasoning_steps,
            'analysis_factors': {
                'urgency_factor': explanation['urgency_factor'],
                'energy_match': explanation['energy_match'],
                'total_score': explanation['total_score'],
                'confidence': explanation['confidence']
            },
            'task_characteristics': {
                'has_due_date': task.due_date is not None,
                'priority_level': task.priority.value if task.priority else None,
                'context_requirement': task.context.value if task.context else None,
                'estimated_duration': task.estimated_duration
            }
        }
        
        return True, "推理步骤生成成功", result_data
        
    except Exception as e:
        logger.error("Failed to generate recommendation reasoning",
                    task_id=task_id, error=str(e))
        return False, f"生成推理步骤时发生错误: {str(e)}", None


def _get_framework_details(framework_scores: Dict[str, float]) -> Dict[str, Dict[str, Any]]:
    """获取理论框架详细信息"""
    
    framework_names = {
        'okr_wig': '《衡量一切》',
        '4dx': '《高效执行4原则》', 
        'full_engagement': '《全力以赴》',
        'atomic_habits': '《原子习惯》',
        'gtd': '《搞定》',
        'essentialism': '《精要主义》'
    }
    
    default_weights = {
        'okr_wig': 0.25,
        '4dx': 0.20,
        'full_engagement': 0.20,
        'atomic_habits': 0.15,
        'gtd': 0.10,
        'essentialism': 0.10
    }
    
    details = {}
    
    for framework_key, score in framework_scores.items():
        framework_name = framework_names.get(framework_key, framework_key)
        weight = default_weights.get(framework_key, 0.10)
        contribution = score * weight
        
        # 评分等级
        if score >= 0.8:
            grade = "优秀"
            grade_level = 4
        elif score >= 0.6:
            grade = "良好"
            grade_level = 3
        elif score >= 0.4:
            grade = "一般"
            grade_level = 2
        else:
            grade = "较低"
            grade_level = 1
        
        details[framework_key] = {
            'name': framework_name,
            'score': score,
            'grade': grade,
            'grade_level': grade_level,
            'weight': weight,
            'contribution': contribution
        }
    
    return details


def _generate_reasoning_steps(explanation: Dict[str, Any], task: Task) -> list[str]:
    """生成推荐逻辑推理步骤"""
    
    reasoning_steps = []
    framework_scores = explanation['framework_scores']
    urgency = explanation['urgency_factor']
    energy_match = explanation['energy_match']
    
    # 基础评分分析
    max_framework = max(framework_scores.items(), key=lambda x: x[1])
    if max_framework[1] > 0.7:
        framework_name = {
            'okr_wig': '《衡量一切》目标对齐理论',
            '4dx': '《高效执行4原则》执行理论',
            'full_engagement': '《全力以赴》精力管理理论',
            'atomic_habits': '《原子习惯》习惯建立理论',
            'gtd': '《搞定》GTD方法论',
            'essentialism': '《精要主义》重要性理论'
        }.get(max_framework[0], max_framework[0])
        
        reasoning_steps.append(f"{framework_name}评分最高({max_framework[1]:.2f})，说明任务在该理论框架下具有优势")
    
    # 紧迫性分析
    if urgency > 0.5:
        if task.due_date:
            reasoning_steps.append(f"任务具有截止时间({task.due_date.strftime('%Y-%m-%d %H:%M')})，紧迫性系数{urgency:.2f}")
        else:
            reasoning_steps.append(f"任务紧迫性系数为{urgency:.2f}")
    
    # 精力匹配分析
    if energy_match > 0.7:
        reasoning_steps.append(f"任务精力需求与当前状态匹配度高({energy_match:.2f})，适合现在执行")
    elif energy_match < 0.3:
        reasoning_steps.append(f"任务精力需求与当前状态匹配度较低({energy_match:.2f})，建议选择合适时机")
    
    # 优先级分析
    if task.priority:
        priority_text = {
            "high": "高优先级任务，应优先处理",
            "medium": "中等优先级任务，可正常安排",
            "low": "低优先级任务，可适当延后"
        }.get(task.priority.value, "")
        if priority_text:
            reasoning_steps.append(priority_text)
    
    # 情境分析
    if task.context:
        reasoning_steps.append(f"任务需要{task.context.value}情境，请确保环境匹配")
    
    # 时长分析
    if task.estimated_duration:
        if task.estimated_duration <= 25:
            reasoning_steps.append(f"短时任务({task.estimated_duration}分钟)，容易完成，有助于建立成就感")
        elif task.estimated_duration <= 60:
            reasoning_steps.append(f"中等时长任务({task.estimated_duration}分钟)，需要专注时间")
        else:
            reasoning_steps.append(f"长时任务({task.estimated_duration}分钟)，建议分解或预留充足时间")
    
    return reasoning_steps


def _get_theory_explanations(framework_scores: Dict[str, float]) -> Dict[str, Dict[str, Any]]:
    """获取理论框架详细说明"""
    
    theory_details = {
        'okr_wig': {
            "book": "《衡量一切》(Measure What Matters)",
            "concept": "OKR & WIG 目标对齐理论",
            "description": "评估任务与关键目标(Objectives and Key Results)和最重要目标(Wildly Important Goals)的对齐程度。高对齐度的任务能够直接推进核心目标实现。",
            "factors": ["项目关联性", "优先级设置", "目标关键词匹配"]
        },
        '4dx': {
            "book": "《高效执行的4个原则》(The 4 Disciplines of Execution)",
            "concept": "4DX 执行效率理论", 
            "description": "基于专注最重要目标、衡量先导性指标、保持引人注目的计分表、营造责任氛围四个原则，评估任务的可执行性。",
            "factors": ["预估时长", "明确性", "行动状态"]
        },
        'full_engagement': {
            "book": "《全力以赴》(The Power of Full Engagement)",
            "concept": "精力管理理论",
            "description": "强调精力而非时间管理。评估任务精力需求与当前精力水平的匹配度，在最佳精力状态下执行最重要的任务。",
            "factors": ["精力需求级别", "当前时间段精力", "精力匹配度"]
        },
        'atomic_habits': {
            "book": "《原子习惯》(Atomic Habits)",
            "concept": "习惯养成理论",
            "description": "通过微小改变获得显著成果。评估任务对良好习惯建立的贡献，偏好小而频繁的行动。",
            "factors": ["重复性特征", "时长适中性", "习惯关键词"]
        },
        'gtd': {
            "book": "《搞定》(Getting Things Done)",
            "concept": "GTD 方法论",
            "description": "通过捕获、澄清、组织、反思、执行五个步骤管理任务。评估任务是否符合GTD最佳实践。",
            "factors": ["明确的下一步行动", "情境设置", "项目关联"]
        },
        'essentialism': {
            "book": "《精要主义》(Essentialism)",
            "concept": "本质重要性理论",
            "description": "只做最重要的事。通过严格标准判断任务的本质价值，专注于真正重要且有影响力的工作。",
            "factors": ["优先级评估", "影响力关键词", "重要性判断"]
        }
    }
    
    # 只返回评分较高的理论框架详情
    top_frameworks = sorted(framework_scores.items(), key=lambda x: x[1], reverse=True)[:3]
    relevant_theories = {}
    
    for framework_key, score in top_frameworks:
        if score >= 0.4 and framework_key in theory_details:
            details = theory_details[framework_key]
            relevant_theories[framework_key] = {
                **details,
                'score': score
            }
    
    return relevant_theories