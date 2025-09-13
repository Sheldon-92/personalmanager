"""AI可调用的用户偏好学习工具函数 - 重构自preferences命令"""

from typing import Tuple, Optional, Dict, Any
import structlog
from datetime import datetime

from pm.core.config import PMConfig
from pm.agents.gtd_agent import GTDAgent

logger = structlog.get_logger()


def get_preference_learning_stats(
    config: Optional[PMConfig] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """获取用户偏好学习统计信息的AI可调用工具函数
    
    提供偏好学习引擎的详细统计信息，包括：
    - 学习状态和进展
    - 理论框架偏好权重
    - 情境使用偏好
    - 学习准确率和置信度
    - 个性化建议
    
    Args:
        config: 可选的PMConfig实例
        
    Returns:
        Tuple[bool, str, Optional[Dict[str, Any]]]: (成功状态, 消息, 偏好统计数据)
    """
    
    try:
        # 初始化配置
        if config is None:
            config = PMConfig()
        
        if not config.is_initialized():
            return False, "系统未初始化。请先运行 pm setup 进行设置。", None
        
        # 创建GTD Agent
        agent = GTDAgent(config)
        
        # 获取偏好学习统计
        stats = agent.get_preference_learning_stats()
        
        # 丰富统计数据
        enhanced_stats = _enhance_preference_stats(stats)
        
        logger.info("Preference learning stats retrieved successfully",
                   total_choices=stats['total_choices'],
                   accuracy=stats['recent_accuracy'])
        
        return True, "偏好学习统计获取成功", enhanced_stats
        
    except Exception as e:
        logger.error("Failed to get preference learning stats", error=str(e))
        return False, f"获取偏好学习统计时发生错误: {str(e)}", None


def analyze_framework_preferences(
    config: Optional[PMConfig] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """分析用户的理论框架偏好
    
    Args:
        config: 可选的PMConfig实例
        
    Returns:
        Tuple[bool, str, Optional[Dict[str, Any]]]: (成功状态, 消息, 框架偏好分析)
    """
    
    try:
        if config is None:
            config = PMConfig()
        
        if not config.is_initialized():
            return False, "系统未初始化", None
        
        agent = GTDAgent(config)
        stats = agent.get_preference_learning_stats()
        
        if not stats['framework_preferences']:
            return True, "暂无框架偏好数据", {
                'has_data': False,
                'framework_preferences': {},
                'recommendations': ["继续使用推荐功能以收集偏好数据"]
            }
        
        # 分析框架偏好
        framework_analysis = _analyze_framework_preferences(stats['framework_preferences'])
        
        return True, "框架偏好分析完成", framework_analysis
        
    except Exception as e:
        logger.error("Failed to analyze framework preferences", error=str(e))
        return False, f"分析框架偏好时发生错误: {str(e)}", None


def analyze_context_preferences(
    config: Optional[PMConfig] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """分析用户的情境使用偏好
    
    Args:
        config: 可选的PMConfig实例
        
    Returns:
        Tuple[bool, str, Optional[Dict[str, Any]]]: (成功状态, 消息, 情境偏好分析)
    """
    
    try:
        if config is None:
            config = PMConfig()
        
        if not config.is_initialized():
            return False, "系统未初始化", None
        
        agent = GTDAgent(config)
        stats = agent.get_preference_learning_stats()
        
        if not stats['context_preferences']:
            return True, "暂无情境偏好数据", {
                'has_data': False,
                'context_preferences': {},
                'recommendations': ["在不同情境下使用任务以收集偏好数据"]
            }
        
        # 分析情境偏好
        context_analysis = _analyze_context_preferences(stats['context_preferences'])
        
        return True, "情境偏好分析完成", context_analysis
        
    except Exception as e:
        logger.error("Failed to analyze context preferences", error=str(e))
        return False, f"分析情境偏好时发生错误: {str(e)}", None


def get_learning_recommendations(
    config: Optional[PMConfig] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """获取个性化学习建议
    
    Args:
        config: 可选的PMConfig实例
        
    Returns:
        Tuple[bool, str, Optional[Dict[str, Any]]]: (成功状态, 消息, 学习建议)
    """
    
    try:
        if config is None:
            config = PMConfig()
        
        if not config.is_initialized():
            return False, "系统未初始化", None
        
        agent = GTDAgent(config)
        stats = agent.get_preference_learning_stats()
        
        # 生成个性化建议
        recommendations = _generate_learning_recommendations(stats)
        
        return True, "学习建议生成成功", recommendations
        
    except Exception as e:
        logger.error("Failed to get learning recommendations", error=str(e))
        return False, f"生成学习建议时发生错误: {str(e)}", None


def _enhance_preference_stats(stats: Dict[str, Any]) -> Dict[str, Any]:
    """丰富偏好统计数据"""
    
    enhanced = stats.copy()
    
    # 添加框架偏好分析
    if stats['framework_preferences']:
        enhanced['framework_analysis'] = _analyze_framework_preferences(stats['framework_preferences'])
    else:
        enhanced['framework_analysis'] = {'has_data': False}
    
    # 添加情境偏好分析
    if stats['context_preferences']:
        enhanced['context_analysis'] = _analyze_context_preferences(stats['context_preferences'])
    else:
        enhanced['context_analysis'] = {'has_data': False}
    
    # 添加学习建议
    enhanced['learning_recommendations'] = _generate_learning_recommendations(stats)
    
    # 添加状态评估
    enhanced['status_assessment'] = _assess_learning_status_detailed(stats)
    
    return enhanced


def _analyze_framework_preferences(framework_prefs: Dict[str, float]) -> Dict[str, Any]:
    """分析理论框架偏好"""
    
    framework_names = {
        'okr_wig': '《衡量一切》',
        '4dx': '《高效执行4原则》',
        'full_engagement': '《全力以赴》',
        'atomic_habits': '《原子习惯》',
        'gtd': '《搞定》',
        'essentialism': '《精要主义》'
    }
    
    # 按偏好强度排序
    sorted_prefs = sorted(framework_prefs.items(), key=lambda x: x[1], reverse=True)
    
    analysis = {
        'has_data': True,
        'top_framework': {
            'key': sorted_prefs[0][0],
            'name': framework_names.get(sorted_prefs[0][0], sorted_prefs[0][0]),
            'weight': sorted_prefs[0][1]
        },
        'preferences_by_strength': []
    }
    
    for framework_key, weight in sorted_prefs:
        framework_name = framework_names.get(framework_key, framework_key)
        
        # 偏好强度评估
        if weight > 0.3:
            strength = "强偏好"
            strength_level = 4
            icon = "🔥"
        elif weight > 0.2:
            strength = "中偏好"
            strength_level = 3
            icon = "⚡"
        elif weight > 0.1:
            strength = "轻偏好"
            strength_level = 2
            icon = "💡"
        else:
            strength = "低偏好"
            strength_level = 1
            icon = "➖"
        
        analysis['preferences_by_strength'].append({
            'key': framework_key,
            'name': framework_name,
            'weight': weight,
            'strength': strength,
            'strength_level': strength_level,
            'icon': icon
        })
    
    return analysis


def _analyze_context_preferences(context_prefs: Dict[str, float]) -> Dict[str, Any]:
    """分析情境使用偏好"""
    
    # 按使用频率排序
    sorted_contexts = sorted(context_prefs.items(), key=lambda x: x[1], reverse=True)
    
    analysis = {
        'has_data': True,
        'most_used_context': {
            'key': sorted_contexts[0][0],
            'frequency': sorted_contexts[0][1]
        },
        'contexts_by_frequency': []
    }
    
    for context_key, frequency in sorted_contexts:
        if frequency > 0.4:
            level = "高频使用"
            level_rank = 3
            icon = "🌟"
        elif frequency > 0.2:
            level = "常用"
            level_rank = 2
            icon = "⭐"
        else:
            level = "偶用"
            level_rank = 1
            icon = "💫"
        
        analysis['contexts_by_frequency'].append({
            'key': context_key,
            'frequency': frequency,
            'level': level,
            'level_rank': level_rank,
            'icon': icon
        })
    
    return analysis


def _generate_learning_recommendations(stats: Dict[str, Any]) -> Dict[str, Any]:
    """生成个性化学习建议"""
    
    total_choices = stats['total_choices']
    recent_accuracy = stats['recent_accuracy']
    
    recommendations = {
        'primary_message': "",
        'suggestions': [],
        'next_actions': []
    }
    
    if total_choices < 5:
        recommendations['primary_message'] = "开始个性化学习之旅！"
        recommendations['suggestions'] = [
            "系统正在学习您的偏好模式",
            "随着您使用推荐功能，PersonalManager将越来越了解您的工作习惯"
        ]
        recommendations['next_actions'] = [
            "使用 pm recommend 获取智能推荐",
            "选择执行推荐的任务",
            "系统将自动学习您的偏好"
        ]
    elif recent_accuracy > 0.7:
        recommendations['primary_message'] = "学习效果优秀！"
        recommendations['suggestions'] = [
            f"您的推荐准确率达到 {recent_accuracy:.1%}",
            "系统已经很好地理解了您的工作偏好"
        ]
        recommendations['next_actions'] = [
            "继续使用推荐功能，享受个性化的智能建议！"
        ]
    else:
        recommendations['primary_message'] = "持续学习中..."
        recommendations['suggestions'] = [
            f"当前准确率: {recent_accuracy:.1%}",
            "系统正在不断优化对您偏好的理解"
        ]
        recommendations['next_actions'] = [
            "请继续使用推荐功能，提供更多学习样本"
        ]
    
    return recommendations


def _assess_learning_status_detailed(stats: Dict[str, Any]) -> Dict[str, Any]:
    """详细评估学习状态"""
    
    total_choices = stats['total_choices']
    recent_accuracy = stats['recent_accuracy']
    confidence_score = stats['confidence_score']
    learning_status = stats['learning_status']
    
    status_details = {
        'status': learning_status,
        'progress_percentage': min(100, (total_choices / 20) * 100),
        'accuracy_trend': "上升" if recent_accuracy > 0.6 else "平稳" if recent_accuracy > 0.4 else "待提升",
        'confidence_level': "高" if confidence_score > 0.7 else "中" if confidence_score > 0.4 else "低",
        'data_sufficiency': "充足" if total_choices >= 20 else "适中" if total_choices >= 5 else "不足"
    }
    
    return status_details