"""AI可调用的分类学习统计工具函数 - 重构自learn命令"""

from typing import Tuple, Optional, Dict, Any, List
import structlog
from datetime import datetime

from pm.core.config import PMConfig
from pm.agents.gtd_agent import GTDAgent

logger = structlog.get_logger()


def get_classification_learning_stats(
    config: Optional[PMConfig] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """获取智能分类学习统计信息的AI可调用工具函数
    
    提供分类学习系统的详细统计信息，包括：
    - 学习进展和准确率
    - 已学习的模式和规律
    - 情境分类能力评估
    - 系统健康状态分析
    
    Args:
        config: 可选的PMConfig实例
        
    Returns:
        Tuple[bool, str, Optional[Dict[str, Any]]]: (成功状态, 消息, 学习统计数据)
    """
    
    try:
        # 初始化配置
        if config is None:
            config = PMConfig()
        
        if not config.is_initialized():
            return False, "系统未初始化。请先运行 pm setup 进行设置。", None
        
        # 创建GTD Agent
        agent = GTDAgent(config)
        
        # 获取分类学习统计
        stats = agent.get_classification_stats()
        
        # 丰富统计数据
        enhanced_stats = _enhance_classification_stats(stats)
        
        logger.info("Classification learning stats retrieved successfully",
                   learned_tasks=stats['total_learned_tasks'],
                   accuracy=stats['recent_accuracy'])
        
        return True, "分类学习统计获取成功", enhanced_stats
        
    except Exception as e:
        logger.error("Failed to get classification learning stats", error=str(e))
        return False, f"获取分类学习统计时发生错误: {str(e)}", None


def analyze_learning_patterns(
    config: Optional[PMConfig] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """分析已学习的分类模式
    
    Args:
        config: 可选的PMConfig实例
        
    Returns:
        Tuple[bool, str, Optional[Dict[str, Any]]]: (成功状态, 消息, 模式分析)
    """
    
    try:
        if config is None:
            config = PMConfig()
        
        if not config.is_initialized():
            return False, "系统未初始化", None
        
        agent = GTDAgent(config)
        stats = agent.get_classification_stats()
        
        if not stats['context_patterns']:
            return True, "暂无学习模式数据", {
                'has_data': False,
                'context_patterns': {},
                'recommendations': ["使用 pm clarify 处理更多任务以积累学习数据"]
            }
        
        # 分析学习模式
        pattern_analysis = _analyze_learning_patterns(stats['context_patterns'])
        
        return True, "学习模式分析完成", pattern_analysis
        
    except Exception as e:
        logger.error("Failed to analyze learning patterns", error=str(e))
        return False, f"分析学习模式时发生错误: {str(e)}", None


def get_learning_health_assessment(
    config: Optional[PMConfig] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """获取学习系统健康评估
    
    Args:
        config: 可选的PMConfig实例
        
    Returns:
        Tuple[bool, str, Optional[Dict[str, Any]]]: (成功状态, 消息, 健康评估)
    """
    
    try:
        if config is None:
            config = PMConfig()
        
        if not config.is_initialized():
            return False, "系统未初始化", None
        
        agent = GTDAgent(config)
        stats = agent.get_classification_stats()
        
        # 生成详细健康评估
        health_assessment = _generate_health_assessment(stats)
        
        return True, "学习健康评估完成", health_assessment
        
    except Exception as e:
        logger.error("Failed to get learning health assessment", error=str(e))
        return False, f"获取健康评估时发生错误: {str(e)}", None


def get_learning_recommendations(
    config: Optional[PMConfig] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """获取学习改进建议
    
    Args:
        config: 可选的PMConfig实例
        
    Returns:
        Tuple[bool, str, Optional[Dict[str, Any]]]: (成功状态, 消息, 改进建议)
    """
    
    try:
        if config is None:
            config = PMConfig()
        
        if not config.is_initialized():
            return False, "系统未初始化", None
        
        agent = GTDAgent(config)
        stats = agent.get_classification_stats()
        
        # 生成个性化改进建议
        recommendations = _generate_learning_recommendations(stats)
        
        return True, "学习建议生成成功", recommendations
        
    except Exception as e:
        logger.error("Failed to get learning recommendations", error=str(e))
        return False, f"生成学习建议时发生错误: {str(e)}", None


def _enhance_classification_stats(stats: Dict[str, Any]) -> Dict[str, Any]:
    """丰富分类统计数据"""
    
    enhanced = stats.copy()
    
    # 添加学习阶段分析
    enhanced['learning_stage'] = _determine_learning_stage(stats)
    
    # 添加准确率分析
    enhanced['accuracy_analysis'] = _analyze_accuracy(stats['recent_accuracy'])
    
    # 添加模式丰富度分析
    enhanced['pattern_richness'] = _analyze_pattern_richness(stats)
    
    # 添加改进建议
    enhanced['improvement_suggestions'] = _generate_learning_recommendations(stats)
    
    # 添加学习里程碑
    enhanced['learning_milestones'] = _calculate_learning_milestones(stats)
    
    return enhanced


def _determine_learning_stage(stats: Dict[str, Any]) -> Dict[str, str]:
    """确定学习阶段"""
    
    total_tasks = stats['total_learned_tasks']
    patterns = stats['learned_patterns']
    accuracy = stats['recent_accuracy']
    
    if total_tasks < 5:
        stage = "初始探索"
        description = "系统正在收集初始数据，学习您的分类习惯"
    elif total_tasks < 20:
        stage = "快速学习"
        description = "系统正在积极学习，识别分类模式"
    elif accuracy > 0.8:
        stage = "成熟应用"
        description = "系统已经很好地理解了您的分类偏好"
    elif accuracy > 0.6:
        stage = "持续优化"
        description = "系统在不断改进分类准确性"
    else:
        stage = "需要调整"
        description = "系统需要更多数据或调整学习策略"
    
    return {
        'stage': stage,
        'description': description,
        'progress_percentage': min(100, (total_tasks / 50) * 100)
    }


def _analyze_accuracy(accuracy: float) -> Dict[str, Any]:
    """分析准确率"""
    
    if accuracy == 0:
        level = "无数据"
        color = "gray"
        advice = "继续使用clarify命令处理任务，系统将开始学习"
    elif accuracy > 0.8:
        level = "优秀"
        color = "green"
        advice = "分类准确率很高，继续保持当前使用习惯"
    elif accuracy > 0.6:
        level = "良好"
        color = "yellow"
        advice = "准确率不错，可以尝试处理更多不同类型的任务"
    elif accuracy > 0.4:
        level = "一般"
        color = "orange"
        advice = "建议更频繁地使用clarify命令，让系统学习更多模式"
    else:
        level = "需改进"
        color = "red"
        advice = "准确率较低，建议检查分类一致性或联系支持"
    
    return {
        'level': level,
        'color': color,
        'percentage': f"{accuracy:.1%}" if accuracy > 0 else "暂无",
        'advice': advice
    }


def _analyze_pattern_richness(stats: Dict[str, Any]) -> Dict[str, Any]:
    """分析模式丰富度"""
    
    patterns = stats['learned_patterns']
    context_patterns = stats.get('context_patterns', {})
    
    if patterns == 0:
        richness = "空白"
        description = "尚未学习任何分类模式"
    elif patterns < 3:
        richness = "简单"
        description = "学习了基础的分类模式"
    elif patterns < 6:
        richness = "丰富"
        description = "掌握了多种情境的分类规律"
    else:
        richness = "复杂"
        description = "形成了复杂的多情境分类体系"
    
    # 分析最活跃的情境
    most_active_context = None
    max_keywords = 0
    
    for context, keyword_count in context_patterns.items():
        if keyword_count > max_keywords:
            max_keywords = keyword_count
            most_active_context = context
    
    return {
        'richness': richness,
        'description': description,
        'total_patterns': patterns,
        'most_active_context': most_active_context,
        'max_keywords': max_keywords,
        'coverage': list(context_patterns.keys())
    }


def _generate_learning_recommendations(stats: Dict[str, Any]) -> Dict[str, Any]:
    """生成学习改进建议"""
    
    total_tasks = stats['total_learned_tasks']
    patterns = stats['learned_patterns']
    accuracy = stats['recent_accuracy']
    
    recommendations = {
        'primary_action': "",
        'suggestions': [],
        'next_steps': []
    }
    
    if total_tasks < 10:
        recommendations['primary_action'] = "积累更多学习数据"
        recommendations['suggestions'] = [
            "系统需要更多任务样本来建立准确的分类模型",
            f"当前已处理 {total_tasks} 个任务，建议处理至少20个任务"
        ]
        recommendations['next_steps'] = [
            "使用 pm clarify 处理收件箱中的任务",
            "保持分类的一致性",
            "覆盖不同类型的工作情境"
        ]
    elif accuracy < 0.6:
        recommendations['primary_action'] = "提高分类一致性"
        recommendations['suggestions'] = [
            f"当前准确率为 {accuracy:.1%}，建议保持分类标准的一致性",
            "系统可能遇到了相互矛盾的分类决策"
        ]
        recommendations['next_steps'] = [
            "回顾最近的分类决策，确保逻辑一致",
            "对相似任务使用相同的分类标准",
            "如有疑问可以重新训练特定情境"
        ]
    else:
        recommendations['primary_action'] = "继续优化和完善"
        recommendations['suggestions'] = [
            f"系统运行良好，准确率达到 {accuracy:.1%}",
            "可以探索更复杂的任务分类场景"
        ]
        recommendations['next_steps'] = [
            "继续处理新类型的任务",
            "使用智能推荐功能提升效率",
            "定期检查学习状态"
        ]
    
    return recommendations


def _generate_health_assessment(stats: Dict[str, Any]) -> Dict[str, Any]:
    """生成详细健康评估"""
    
    health = stats['learning_health']
    total_tasks = stats['total_learned_tasks']
    accuracy = stats['recent_accuracy']
    patterns = stats['learned_patterns']
    
    assessment = {
        'overall_health': health,
        'health_score': 0,
        'components': {},
        'strengths': [],
        'weaknesses': [],
        'priorities': []
    }
    
    # 评估各个组件
    # 数据量评估
    if total_tasks >= 20:
        data_health = "excellent"
        assessment['strengths'].append("拥有充足的学习数据")
        data_score = 100
    elif total_tasks >= 10:
        data_health = "good"
        data_score = 70
    else:
        data_health = "needs_improvement"
        assessment['weaknesses'].append("学习数据不足")
        assessment['priorities'].append("积累更多学习样本")
        data_score = 30
    
    assessment['components']['data_volume'] = {
        'health': data_health,
        'score': data_score,
        'value': total_tasks
    }
    
    # 准确率评估
    if accuracy > 0.8:
        accuracy_health = "excellent"
        assessment['strengths'].append("预测准确率优秀")
        accuracy_score = 100
    elif accuracy > 0.6:
        accuracy_health = "good"
        accuracy_score = 80
    elif accuracy > 0.4:
        accuracy_health = "fair"
        accuracy_score = 60
    else:
        accuracy_health = "needs_improvement"
        if accuracy > 0:
            assessment['weaknesses'].append("预测准确率偏低")
            assessment['priorities'].append("提升分类一致性")
        accuracy_score = 20
    
    assessment['components']['accuracy'] = {
        'health': accuracy_health,
        'score': accuracy_score,
        'value': accuracy
    }
    
    # 模式丰富度评估
    if patterns >= 5:
        pattern_health = "excellent"
        assessment['strengths'].append("掌握丰富的分类模式")
        pattern_score = 100
    elif patterns >= 3:
        pattern_health = "good"
        pattern_score = 80
    else:
        pattern_health = "needs_improvement"
        assessment['weaknesses'].append("分类模式相对单一")
        assessment['priorities'].append("在不同情境下处理任务")
        pattern_score = 50
    
    assessment['components']['pattern_richness'] = {
        'health': pattern_health,
        'score': pattern_score,
        'value': patterns
    }
    
    # 计算总体健康分数
    assessment['health_score'] = int((data_score + accuracy_score + pattern_score) / 3)
    
    return assessment


def _calculate_learning_milestones(stats: Dict[str, Any]) -> List[Dict[str, Any]]:
    """计算学习里程碑"""
    
    total_tasks = stats['total_learned_tasks']
    accuracy = stats['recent_accuracy']
    
    milestones = [
        {
            'milestone': "首次分类",
            'target': 1,
            'achieved': total_tasks >= 1,
            'description': "完成第一次智能分类"
        },
        {
            'milestone': "基础学习",
            'target': 10,
            'achieved': total_tasks >= 10,
            'description': "处理10个任务，建立基础模式"
        },
        {
            'milestone': "进阶应用", 
            'target': 25,
            'achieved': total_tasks >= 25,
            'description': "处理25个任务，形成稳定模式"
        },
        {
            'milestone': "专家级别",
            'target': 50,
            'achieved': total_tasks >= 50,
            'description': "处理50个任务，成为分类专家"
        },
        {
            'milestone': "高准确率",
            'target': 0.8,
            'achieved': accuracy >= 0.8,
            'description': "达到80%以上的预测准确率"
        }
    ]
    
    return milestones