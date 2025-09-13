"""Best practices guide and interactive tutorials tools for PersonalManager."""

import structlog
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

logger = structlog.get_logger(__name__)


# 最佳实践指导内容
BEST_PRACTICES = {
    "gtd_workflow": {
        "title": "GTD工作流程最佳实践",
        "description": "基于《Getting Things Done》的完整工作流程",
        "steps": [
            {
                "name": "📥 捕获 (Capture)",
                "description": "将所有想法和任务快速记录下来",
                "command": "pm capture \"任务描述\"",
                "tips": [
                    "随时随地捕获，不要判断重要性",
                    "使用自然语言描述，无需完美格式",
                    "一次只捕获一个想法或任务",
                    "定期清空大脑，确保没有遗漏"
                ]
            },
            {
                "name": "🤔 理清 (Clarify)",
                "description": "确定每个条目的性质和下一步行动",
                "command": "pm clarify",
                "tips": [
                    "问自己：这是什么？需要行动吗？",
                    "如果需要行动，下一步具体是什么？",
                    "两分钟内能完成的立即去做",
                    "需要多步骤的转化为项目"
                ]
            },
            {
                "name": "📋 整理 (Organize)",
                "description": "将理清的条目放入合适的清单",
                "command": "pm organize",
                "tips": [
                    "按情境分类：@电脑、@电话、@外出",
                    "设置适当的优先级和截止日期",
                    "将相关任务关联到项目",
                    "定期检查和更新分类"
                ]
            },
            {
                "name": "🔄 回顾 (Review)",
                "description": "定期检查和更新整个系统",
                "command": "pm review",
                "tips": [
                    "每日回顾：检查今日任务和日程",
                    "每周回顾：全面检查所有项目和清单",
                    "每月回顾：评估目标进展和系统效果",
                    "保持系统的更新和相关性"
                ]
            },
            {
                "name": "⚡ 执行 (Engage)",
                "description": "基于情境和优先级选择行动",
                "command": "pm next",
                "tips": [
                    "根据当前情境选择任务",
                    "考虑可用时间和精力水平",
                    "优先处理重要和紧急的事项",
                    "保持专注，避免多任务切换"
                ]
            }
        ]
    },
    "project_setup": {
        "title": "项目设置最佳实践",
        "description": "如何有效设置和管理项目",
        "guidelines": [
            {
                "category": "项目定义",
                "practices": [
                    "明确项目的期望结果和成功标准",
                    "将大项目拆分为可管理的子项目",
                    "为每个项目设置现实的时间框架",
                    "定义项目的关键里程碑"
                ]
            },
            {
                "category": "PROJECT_STATUS.md设置",
                "practices": [
                    "在项目根目录创建PROJECT_STATUS.md文件",
                    "使用标准化的状态字段：进度、健康度、风险",
                    "定期更新项目状态，保持信息新鲜",
                    "记录重要的决策和变更历史"
                ]
            },
            {
                "category": "团队协作",
                "practices": [
                    "与团队成员分享项目状态文件",
                    "建立定期的项目同步会议",
                    "使用版本控制跟踪项目文档变化",
                    "建立清晰的责任分工和沟通渠道"
                ]
            }
        ]
    },
    "common_scenarios": {
        "title": "常见使用场景",
        "scenarios": [
            {
                "name": "🌅 晨间规划",
                "description": "开始新一天的最佳实践",
                "workflow": [
                    "运行 `pm today` 获取今日建议",
                    "查看 `pm next --context @电脑` 查看可执行任务",
                    "检查 `pm projects overview` 了解项目状态",
                    "规划今日3个最重要的任务（MIT）"
                ]
            },
            {
                "name": "📧 邮件处理",
                "description": "高效处理电子邮件",
                "workflow": [
                    "批量处理邮件，避免频繁检查",
                    "使用2分钟规则：能立即回复的立即处理",
                    "需要后续行动的用 `pm capture` 捕获",
                    "需要参考的邮件归档到项目文件夹"
                ]
            },
            {
                "name": "🚀 项目启动",
                "description": "启动新项目的标准流程",
                "workflow": [
                    "创建项目文件夹和PROJECT_STATUS.md",
                    "定义项目的期望结果和成功标准",
                    "分解项目为具体的下一步行动",
                    "设置项目里程碑和检查点"
                ]
            },
            {
                "name": "🔄 每周回顾",
                "description": "每周系统维护",
                "workflow": [
                    "运行 `pm review --weekly` 启动回顾流程",
                    "检查完成的任务和项目进展",
                    "更新下周的优先级和目标",
                    "清理和整理系统中的过时信息"
                ]
            }
        ]
    }
}


def get_guide_overview() -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """获取指导概览信息
    
    Returns:
        Tuple[bool, str, Optional[Dict[str, Any]]]: (成功, 消息, 数据)
    """
    
    try:
        logger.info("获取指导概览信息")
        
        categories = [
            {
                "key": "gtd",
                "name": "GTD工作流程",
                "description": "完整的GTD实践指导",
                "command": "pm guide gtd"
            },
            {
                "key": "projects", 
                "name": "项目管理",
                "description": "项目设置和管理最佳实践",
                "command": "pm guide projects"
            },
            {
                "key": "scenarios",
                "name": "使用场景", 
                "description": "常见工作场景的处理方法",
                "command": "pm guide scenarios"
            },
            {
                "key": "interactive",
                "name": "交互教程",
                "description": "逐步指导的交互式学习",
                "command": "pm guide interactive"
            }
        ]
        
        data = {
            "overview_title": "PersonalManager 最佳实践指导",
            "overview_description": "基于19本管理经典书籍的智慧整合，帮助您高效使用PersonalManager系统",
            "categories": categories,
            "usage_tips": [
                "使用 pm guide <类别> 查看具体指导",
                "交互教程将引导您完成实际操作",
                "所有实践都基于科学的管理理论",
                "建议从GTD工作流程开始学习"
            ]
        }
        
        logger.info("成功获取指导概览信息", category_count=len(categories))
        return True, "获取指导概览成功", data
        
    except Exception as e:
        error_msg = f"获取指导概览失败: {e}"
        logger.error(error_msg, error=str(e))
        return False, error_msg, None


def get_gtd_workflow_guide() -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """获取GTD工作流程指导
    
    Returns:
        Tuple[bool, str, Optional[Dict[str, Any]]]: (成功, 消息, 数据)
    """
    
    try:
        logger.info("获取GTD工作流程指导")
        
        workflow = BEST_PRACTICES["gtd_workflow"]
        
        data = {
            "title": workflow["title"],
            "description": workflow["description"],
            "steps": workflow["steps"],
            "core_principles": [
                {
                    "name": "心如水",
                    "description": "保持大脑清净，专注当下"
                },
                {
                    "name": "收集一切", 
                    "description": "不放过任何可能重要的想法"
                },
                {
                    "name": "定期回顾",
                    "description": "保持系统的新鲜和相关性"
                },
                {
                    "name": "情境行动",
                    "description": "根据当前条件选择最合适的任务"
                }
            ]
        }
        
        logger.info("成功获取GTD工作流程指导", step_count=len(workflow["steps"]))
        return True, "获取GTD工作流程指导成功", data
        
    except Exception as e:
        error_msg = f"获取GTD工作流程指导失败: {e}"
        logger.error(error_msg, error=str(e))
        return False, error_msg, None


def get_project_setup_guide() -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """获取项目设置最佳实践指导
    
    Returns:
        Tuple[bool, str, Optional[Dict[str, Any]]]: (成功, 消息, 数据)
    """
    
    try:
        logger.info("获取项目设置指导")
        
        project_guide = BEST_PRACTICES["project_setup"]
        
        data = {
            "title": project_guide["title"],
            "description": project_guide["description"],
            "guidelines": project_guide["guidelines"]
        }
        
        logger.info("成功获取项目设置指导", guideline_count=len(project_guide["guidelines"]))
        return True, "获取项目设置指导成功", data
        
    except Exception as e:
        error_msg = f"获取项目设置指导失败: {e}"
        logger.error(error_msg, error=str(e))
        return False, error_msg, None


def get_common_scenarios_guide() -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """获取常见使用场景指导
    
    Returns:
        Tuple[bool, str, Optional[Dict[str, Any]]]: (成功, 消息, 数据)
    """
    
    try:
        logger.info("获取常见使用场景指导")
        
        scenarios = BEST_PRACTICES["common_scenarios"]
        
        data = {
            "title": scenarios["title"], 
            "scenarios": scenarios["scenarios"]
        }
        
        logger.info("成功获取常见使用场景指导", scenario_count=len(scenarios["scenarios"]))
        return True, "获取常见使用场景指导成功", data
        
    except Exception as e:
        error_msg = f"获取常见使用场景指导失败: {e}"
        logger.error(error_msg, error=str(e))
        return False, error_msg, None


def get_interactive_tutorial_info() -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """获取交互式教程信息
    
    Returns:
        Tuple[bool, str, Optional[Dict[str, Any]]]: (成功, 消息, 数据)
    """
    
    try:
        logger.info("获取交互式教程信息")
        
        tutorial_steps = [
            {
                "step": 1,
                "title": "理解GTD核心概念",
                "description": "学习收集-理清-整理-回顾-执行的基本流程",
                "content": {
                    "concepts": [
                        "📥 收集（Capture）：将所有想法、任务、承诺记录下来",
                        "🤔 理清（Clarify）：确定每个条目的含义和所需行动",
                        "📋 整理（Organize）：将条目分类到合适的清单中",
                        "🔄 回顾（Review）：定期检查和更新整个系统",
                        "⚡ 执行（Engage）：根据情境和优先级选择行动"
                    ],
                    "principles": [
                        "大脑用来思考，不是用来记忆",
                        "所有承诺都要有可信的外部系统来跟踪",
                        "定期回顾保持系统的新鲜度"
                    ]
                }
            },
            {
                "step": 2,
                "title": "实践任务捕获",
                "description": "学习如何有效捕获和理清任务",
                "content": {
                    "good_examples": [
                        "给张总发送项目进度报告",
                        "研究新的项目管理工具选项", 
                        "预约下周的医生检查"
                    ],
                    "bad_examples": [
                        "处理邮件（太模糊）",
                        "改善工作效率（太宽泛）",
                        "明天的会议（缺乏行动）"
                    ],
                    "tips": [
                        "使用动词开头描述行动",
                        "包含足够的上下文信息",
                        "一次只捕获一个想法",
                        "不要在捕获时判断重要性"
                    ]
                }
            },
            {
                "step": 3,
                "title": "项目管理实践",
                "description": "学习设置和管理项目状态",
                "content": {
                    "project_definition": [
                        "具体、可测量的成果",
                        "明确的成功标准",
                        "现实的时间框架"
                    ],
                    "status_file": [
                        "项目进度百分比",
                        "当前健康状态",
                        "主要风险和问题",
                        "下一步关键行动"
                    ],
                    "decomposition": [
                        "将大项目拆分为子项目",
                        "每个子项目有明确的交付物",
                        "识别关键路径和依赖关系"
                    ]
                }
            },
            {
                "step": 4,
                "title": "构建每日工作流",
                "description": "建立高效的每日工作习惯",
                "content": {
                    "morning_routine": [
                        "查看今日日程和任务",
                        "确定3个最重要任务（MIT）",
                        "检查项目状态更新"
                    ],
                    "work_time": [
                        "根据精力水平选择任务",
                        "完成任务后及时标记",
                        "新想法立即捕获"
                    ],
                    "evening_routine": [
                        "回顾今日完成情况",
                        "捕获明日待办事项",
                        "更新项目进度"
                    ],
                    "key_success_factor": "保持系统简单，专注执行而不是完善系统！"
                }
            }
        ]
        
        data = {
            "tutorial_title": "PersonalManager 交互式教程",
            "tutorial_description": "通过实际操作来学习PersonalManager的核心功能，每一步都有详细说明和实践练习",
            "total_steps": len(tutorial_steps),
            "steps": tutorial_steps,
            "completion_benefits": [
                "掌握基础的使用方法",
                "建立高效的工作习惯",
                "理解GTD核心原则",
                "能够独立使用系统"
            ]
        }
        
        logger.info("成功获取交互式教程信息", step_count=len(tutorial_steps))
        return True, "获取交互式教程信息成功", data
        
    except Exception as e:
        error_msg = f"获取交互式教程信息失败: {e}"
        logger.error(error_msg, error=str(e))
        return False, error_msg, None


def search_best_practices(query: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """搜索最佳实践内容
    
    Args:
        query: 搜索关键词
        
    Returns:
        Tuple[bool, str, Optional[Dict[str, Any]]]: (成功, 消息, 数据)
    """
    
    try:
        logger.info("搜索最佳实践内容", query=query)
        
        if not query or not query.strip():
            return False, "搜索关键词不能为空", None
        
        results = []
        query_lower = query.lower().strip()
        
        for category, content in BEST_PRACTICES.items():
            # 搜索标题和描述
            if (query_lower in content["title"].lower() or 
                query_lower in content["description"].lower()):
                
                results.append({
                    "category": category,
                    "title": content["title"],
                    "description": content["description"],
                    "match_type": "title_or_description"
                })
            
            # 搜索步骤内容（对于GTD工作流程）
            if category == "gtd_workflow" and "steps" in content:
                for step in content["steps"]:
                    if (query_lower in step["name"].lower() or 
                        query_lower in step["description"].lower() or
                        any(query_lower in tip.lower() for tip in step["tips"])):
                        
                        results.append({
                            "category": category,
                            "title": content["title"],
                            "description": content["description"],
                            "step_match": step,
                            "match_type": "step_content"
                        })
                        break
            
            # 搜索场景内容
            if category == "common_scenarios" and "scenarios" in content:
                for scenario in content["scenarios"]:
                    if (query_lower in scenario["name"].lower() or
                        query_lower in scenario["description"].lower() or
                        any(query_lower in step.lower() for step in scenario["workflow"])):
                        
                        results.append({
                            "category": category,
                            "title": content["title"],
                            "description": content["description"],
                            "scenario_match": scenario,
                            "match_type": "scenario_content"
                        })
                        break
        
        # 去重
        unique_results = []
        seen = set()
        for result in results:
            key = (result["category"], result.get("match_type", ""))
            if key not in seen:
                unique_results.append(result)
                seen.add(key)
        
        data = {
            "query": query,
            "result_count": len(unique_results),
            "results": unique_results
        }
        
        logger.info("成功搜索最佳实践内容", query=query, result_count=len(unique_results))
        return True, f"找到 {len(unique_results)} 个相关结果", data
        
    except Exception as e:
        error_msg = f"搜索最佳实践内容失败: {e}"
        logger.error(error_msg, query=query, error=str(e))
        return False, error_msg, None


def get_available_guide_topics() -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """获取可用的指导主题列表
    
    Returns:
        Tuple[bool, str, Optional[Dict[str, Any]]]: (成功, 消息, 数据)
    """
    
    try:
        logger.info("获取可用的指导主题")
        
        topics = ["gtd", "projects", "scenarios", "interactive"]
        topic_details = {
            "gtd": "GTD工作流程指导",
            "projects": "项目设置最佳实践", 
            "scenarios": "常见使用场景",
            "interactive": "交互式教程"
        }
        
        data = {
            "topics": topics,
            "topic_details": topic_details,
            "total_count": len(topics)
        }
        
        logger.info("成功获取指导主题", topic_count=len(topics))
        return True, "获取指导主题成功", data
        
    except Exception as e:
        error_msg = f"获取指导主题失败: {e}"
        logger.error(error_msg, error=str(e))
        return False, error_msg, None


def validate_guide_category(category: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """验证指导类别是否有效
    
    Args:
        category: 指导类别
        
    Returns:
        Tuple[bool, str, Optional[Dict[str, Any]]]: (成功, 消息, 数据)
    """
    
    try:
        logger.info("验证指导类别", category=category)
        
        valid_categories = ["gtd", "projects", "scenarios", "interactive"]
        
        if not category:
            return False, "指导类别不能为空", None
        
        is_valid = category.lower() in valid_categories
        
        data = {
            "category": category,
            "is_valid": is_valid,
            "valid_categories": valid_categories
        }
        
        if is_valid:
            logger.info("指导类别验证通过", category=category)
            return True, "指导类别有效", data
        else:
            logger.warning("指导类别无效", category=category, valid_categories=valid_categories)
            return False, f"无效的指导类别: {category}", data
        
    except Exception as e:
        error_msg = f"验证指导类别失败: {e}"
        logger.error(error_msg, category=category, error=str(e))
        return False, error_msg, None