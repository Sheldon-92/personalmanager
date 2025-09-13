"""Help system tools for PersonalManager commands."""

import structlog
from typing import Dict, Any, Optional, List, Tuple

logger = structlog.get_logger(__name__)


# 命令帮助信息数据库
COMMAND_HELP: Dict[str, Dict] = {
    "setup": {
        "description": "启动PersonalManager系统设置向导",
        "usage": "pm setup [--reset]",
        "options": {
            "--reset": "重置所有现有配置"
        },
        "examples": [
            "pm setup",
            "pm setup --reset"
        ],
        "category": "基础设置"
    },
    "help": {
        "description": "显示命令帮助信息",
        "usage": "pm help [command]",
        "options": {},
        "examples": [
            "pm help",
            "pm help setup",
            "pm help capture"
        ],
        "category": "基础设置"
    },
    "version": {
        "description": "显示PersonalManager版本信息",
        "usage": "pm version",
        "options": {},
        "examples": ["pm version"],
        "category": "基础设置"
    },
    "capture": {
        "description": "快速捕获新任务或想法到收件箱",
        "usage": "pm capture \"任务描述\" [--context] [--project]",
        "options": {
            "--context": "指定任务情境 (如: @电脑, @外出, @电话)",
            "--project": "关联到特定项目"
        },
        "examples": [
            "pm capture \"完成项目报告\"",
            "pm capture \"给客户打电话\" --context @电话",
            "pm capture \"整理文档\" --project myproject"
        ],
        "category": "任务管理"
    },
    "clarify": {
        "description": "理清收件箱中的任务，确定下一步行动",
        "usage": "pm clarify [--all] [--filter]",
        "options": {
            "--all": "理清所有未处理任务",
            "--filter": "按条件过滤任务"
        },
        "examples": [
            "pm clarify",
            "pm clarify --all"
        ],
        "category": "任务管理"
    },
    "next": {
        "description": "查看下一步行动清单",
        "usage": "pm next [--context] [--limit]",
        "options": {
            "--context": "按情境筛选 (@电脑, @外出等)",
            "--limit": "限制显示数量"
        },
        "examples": [
            "pm next",
            "pm next --context @电脑",
            "pm next --limit 5"
        ],
        "category": "任务管理"
    },
    "today": {
        "description": "获取基于AI分析的今日任务建议",
        "usage": "pm today [--detailed]",
        "options": {
            "--detailed": "显示详细的推荐理由"
        },
        "examples": [
            "pm today",
            "pm today --detailed"
        ],
        "category": "智能建议"
    },
    "recommend": {
        "description": "获取AI智能任务推荐",
        "usage": "pm recommend [--context] [--limit]",
        "options": {
            "--context": "指定推荐情境",
            "--limit": "限制推荐数量"
        },
        "examples": [
            "pm recommend",
            "pm recommend --context @电脑",
            "pm recommend --limit 5"
        ],
        "category": "智能建议"
    },
    "projects": {
        "description": "项目管理相关命令",
        "usage": "pm projects <subcommand>",
        "subcommands": {
            "overview": "显示所有项目状态概览",
            "status": "查看特定项目详细状态",
            "update": "更新项目状态"
        },
        "examples": [
            "pm projects overview",
            "pm projects status myproject",
            "pm projects update myproject"
        ],
        "category": "项目管理"
    },
    "tasks": {
        "description": "任务管理相关命令",
        "usage": "pm tasks <subcommand>",
        "subcommands": {
            "list": "列出任务",
            "complete": "完成任务",
            "status": "查看任务状态"
        },
        "examples": [
            "pm tasks list",
            "pm tasks complete <task_id>",
            "pm tasks status"
        ],
        "category": "任务管理"
    },
    "calendar": {
        "description": "日历集成和时间管理",
        "usage": "pm calendar <subcommand>",
        "subcommands": {
            "today": "显示今日日程",
            "sync": "同步日历数据"
        },
        "examples": [
            "pm calendar today",
            "pm calendar sync"
        ],
        "category": "时间管理"
    },
    "gmail": {
        "description": "Gmail集成和邮件管理",
        "usage": "pm gmail <subcommand>",
        "subcommands": {
            "stats": "显示邮件统计",
            "sync": "同步邮件数据"
        },
        "examples": [
            "pm gmail stats",
            "pm gmail sync"
        ],
        "category": "邮件管理"
    },
    "auth": {
        "description": "身份认证管理",
        "usage": "pm auth <subcommand>",
        "subcommands": {
            "status": "查看认证状态",
            "login": "登录服务",
            "logout": "退出服务"
        },
        "examples": [
            "pm auth status",
            "pm auth login",
            "pm auth logout"
        ],
        "category": "身份认证"
    },
    "preferences": {
        "description": "用户偏好设置管理",
        "usage": "pm preferences [--show] [--set key=value]",
        "options": {
            "--show": "显示当前偏好设置",
            "--set": "设置偏好参数"
        },
        "examples": [
            "pm preferences",
            "pm preferences --show",
            "pm preferences --set theme=dark"
        ],
        "category": "设置管理"
    },
    "guide": {
        "description": "最佳实践指导和交互式教程",
        "usage": "pm guide [category]",
        "subcommands": {
            "gtd": "GTD工作流程指导",
            "projects": "项目设置最佳实践",
            "scenarios": "常见使用场景",
            "interactive": "交互式教程"
        },
        "examples": [
            "pm guide",
            "pm guide gtd",
            "pm guide interactive"
        ],
        "category": "指导教程"
    },
    "privacy": {
        "description": "隐私保护和数据管理",
        "usage": "pm privacy <subcommand>",
        "subcommands": {
            "info": "显示隐私信息",
            "export": "导出用户数据",
            "backup": "创建数据备份",
            "cleanup": "清理过期数据",
            "clear": "清除所有数据"
        },
        "examples": [
            "pm privacy info",
            "pm privacy export",
            "pm privacy backup"
        ],
        "category": "隐私管理"
    },
    "monitor": {
        "description": "文件监控和变化检测",
        "usage": "pm monitor <subcommand>",
        "subcommands": {
            "start": "启动文件监控",
            "stop": "停止文件监控",
            "status": "查看监控状态",
            "logs": "查看监控日志"
        },
        "examples": [
            "pm monitor start",
            "pm monitor status",
            "pm monitor logs"
        ],
        "category": "系统监控"
    },
    "update": {
        "description": "项目状态更新和维护",
        "usage": "pm update <subcommand>",
        "subcommands": {
            "status": "更新项目状态",
            "validate": "验证更新环境",
            "force": "强制刷新所有项目"
        },
        "examples": [
            "pm update status",
            "pm update validate",
            "pm update force"
        ],
        "category": "项目维护"
    }
}

# 命令分类
COMMAND_CATEGORIES = {
    "基础设置": ["setup", "help", "version"],
    "任务管理": ["capture", "clarify", "next", "tasks"],
    "项目管理": ["projects", "update"],
    "智能建议": ["today", "recommend"],
    "时间管理": ["calendar"],
    "邮件管理": ["gmail"],
    "身份认证": ["auth"],
    "设置管理": ["preferences"],
    "指导教程": ["guide"],
    "隐私管理": ["privacy"],
    "系统监控": ["monitor"]
}


def get_help_overview() -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """获取帮助系统概览
    
    Returns:
        Tuple[bool, str, Optional[Dict[str, Any]]]: (成功, 消息, 数据)
    """
    
    try:
        logger.info("获取帮助系统概览")
        
        # 构建分类命令数据
        categorized_commands = {}
        total_commands = 0
        
        for category, commands in COMMAND_CATEGORIES.items():
            categorized_commands[category] = []
            for cmd in commands:
                if cmd in COMMAND_HELP:
                    categorized_commands[category].append({
                        "name": cmd,
                        "description": COMMAND_HELP[cmd]["description"],
                        "usage": COMMAND_HELP[cmd]["usage"]
                    })
                    total_commands += 1
        
        data = {
            "system_title": "PersonalManager Agent 命令帮助",
            "system_description": "智能化的个人项目与时间管理解决方案，基于GTD、原子习惯、深度工作等19本经典理论",
            "total_commands": total_commands,
            "categories": categorized_commands,
            "usage_tips": [
                "使用 pm help <命令名> 查看特定命令的详细帮助",
                "所有命令都支持 --help 参数",
                "首次使用请运行 pm setup 进行初始化",
                "数据完全本地存储，保护您的隐私"
            ]
        }
        
        logger.info("成功获取帮助系统概览", total_commands=total_commands, categories=len(COMMAND_CATEGORIES))
        return True, "获取帮助系统概览成功", data
        
    except Exception as e:
        error_msg = f"获取帮助系统概览失败: {e}"
        logger.error(error_msg, error=str(e))
        return False, error_msg, None


def get_command_help(command: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """获取特定命令的帮助信息
    
    Args:
        command: 命令名称
        
    Returns:
        Tuple[bool, str, Optional[Dict[str, Any]]]: (成功, 消息, 数据)
    """
    
    try:
        logger.info("获取命令帮助", command=command)
        
        if not command or not command.strip():
            return False, "命令名称不能为空", None
        
        command = command.strip().lower()
        
        # 支持模糊搜索
        exact_match = command in COMMAND_HELP
        fuzzy_matches = []
        
        if not exact_match:
            # 查找模糊匹配
            for cmd_name in COMMAND_HELP.keys():
                if command in cmd_name.lower():
                    fuzzy_matches.append(cmd_name)
            
            if len(fuzzy_matches) == 1:
                command = fuzzy_matches[0]
                exact_match = True
            elif len(fuzzy_matches) > 1:
                data = {
                    "command": command,
                    "found": False,
                    "fuzzy_matches": fuzzy_matches,
                    "suggestion": f"找到多个匹配的命令: {', '.join(fuzzy_matches)}，请指定具体的命令名称"
                }
                logger.warning("找到多个模糊匹配", command=command, matches=fuzzy_matches)
                return True, "找到多个匹配命令", data
            else:
                data = {
                    "command": command,
                    "found": False,
                    "suggestion": f"未找到命令 '{command}'，使用 'pm help' 查看所有可用命令"
                }
                logger.warning("未找到命令", command=command)
                return True, "未找到指定命令", data
        
        if exact_match:
            help_info = COMMAND_HELP[command].copy()
            
            # 添加相关命令推荐
            category = help_info.get('category', '')
            related_commands = []
            if category and category in COMMAND_CATEGORIES:
                for related in COMMAND_CATEGORIES[category]:
                    if related != command and related in COMMAND_HELP:
                        related_commands.append({
                            "name": related,
                            "description": COMMAND_HELP[related]["description"]
                        })
            
            data = {
                "command": command,
                "found": True,
                "help_info": help_info,
                "related_commands": related_commands[:3]  # 最多显示3个相关命令
            }
            
            logger.info("成功获取命令帮助", command=command, category=category)
            return True, f"获取命令 '{command}' 的帮助信息成功", data
        
        return False, f"无法获取命令 '{command}' 的帮助信息", None
        
    except Exception as e:
        error_msg = f"获取命令帮助失败: {e}"
        logger.error(error_msg, command=command, error=str(e))
        return False, error_msg, None


def search_commands(query: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """搜索命令
    
    Args:
        query: 搜索查询
        
    Returns:
        Tuple[bool, str, Optional[Dict[str, Any]]]: (成功, 消息, 数据)
    """
    
    try:
        logger.info("搜索命令", query=query)
        
        if not query or not query.strip():
            return False, "搜索查询不能为空", None
        
        query_lower = query.strip().lower()
        matches = []
        
        for cmd_name, cmd_info in COMMAND_HELP.items():
            match_score = 0
            match_reasons = []
            
            # 检查命令名 (最高权重)
            if query_lower == cmd_name.lower():
                match_score += 100
                match_reasons.append("完全匹配命令名")
            elif query_lower in cmd_name.lower():
                match_score += 50
                match_reasons.append("部分匹配命令名")
            
            # 检查描述
            if query_lower in cmd_info['description'].lower():
                match_score += 20
                match_reasons.append("匹配描述")
            
            # 检查分类
            if query_lower in cmd_info.get('category', '').lower():
                match_score += 10
                match_reasons.append("匹配分类")
            
            # 检查示例
            examples = cmd_info.get('examples', [])
            for example in examples:
                if query_lower in example.lower():
                    match_score += 5
                    match_reasons.append("匹配示例")
                    break
            
            if match_score > 0:
                matches.append({
                    "command": cmd_name,
                    "description": cmd_info["description"],
                    "usage": cmd_info["usage"],
                    "category": cmd_info.get("category", ""),
                    "match_score": match_score,
                    "match_reasons": match_reasons
                })
        
        # 按匹配分数排序
        matches.sort(key=lambda x: x["match_score"], reverse=True)
        
        data = {
            "query": query,
            "result_count": len(matches),
            "matches": matches
        }
        
        logger.info("成功搜索命令", query=query, result_count=len(matches))
        return True, f"找到 {len(matches)} 个匹配的命令", data
        
    except Exception as e:
        error_msg = f"搜索命令失败: {e}"
        logger.error(error_msg, query=query, error=str(e))
        return False, error_msg, None


def get_command_suggestions(partial_command: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """根据部分命令名获取建议
    
    Args:
        partial_command: 部分命令名
        
    Returns:
        Tuple[bool, str, Optional[Dict[str, Any]]]: (成功, 消息, 数据)
    """
    
    try:
        logger.info("获取命令建议", partial_command=partial_command)
        
        if not partial_command:
            return False, "部分命令名不能为空", None
        
        partial_lower = partial_command.strip().lower()
        suggestions = []
        
        for cmd_name in COMMAND_HELP.keys():
            if cmd_name.startswith(partial_lower):
                suggestions.append({
                    "command": cmd_name,
                    "description": COMMAND_HELP[cmd_name]["description"]
                })
        
        # 按命令名排序
        suggestions.sort(key=lambda x: x["command"])
        
        data = {
            "partial_command": partial_command,
            "suggestion_count": len(suggestions),
            "suggestions": suggestions
        }
        
        logger.info("成功获取命令建议", partial_command=partial_command, suggestion_count=len(suggestions))
        return True, f"找到 {len(suggestions)} 个建议命令", data
        
    except Exception as e:
        error_msg = f"获取命令建议失败: {e}"
        logger.error(error_msg, partial_command=partial_command, error=str(e))
        return False, error_msg, None


def get_available_commands() -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """获取所有可用命令列表
    
    Returns:
        Tuple[bool, str, Optional[Dict[str, Any]]]: (成功, 消息, 数据)
    """
    
    try:
        logger.info("获取所有可用命令")
        
        all_commands = []
        for cmd_name, cmd_info in COMMAND_HELP.items():
            all_commands.append({
                "command": cmd_name,
                "description": cmd_info["description"],
                "usage": cmd_info["usage"],
                "category": cmd_info.get("category", "")
            })
        
        # 按分类和命令名排序
        all_commands.sort(key=lambda x: (x["category"], x["command"]))
        
        data = {
            "total_commands": len(all_commands),
            "commands": all_commands,
            "categories": list(COMMAND_CATEGORIES.keys())
        }
        
        logger.info("成功获取所有可用命令", command_count=len(all_commands))
        return True, f"获取 {len(all_commands)} 个可用命令", data
        
    except Exception as e:
        error_msg = f"获取可用命令失败: {e}"
        logger.error(error_msg, error=str(e))
        return False, error_msg, None


def validate_command_exists(command: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """验证命令是否存在
    
    Args:
        command: 命令名称
        
    Returns:
        Tuple[bool, str, Optional[Dict[str, Any]]]: (成功, 消息, 数据)
    """
    
    try:
        logger.info("验证命令存在性", command=command)
        
        if not command:
            return False, "命令名称不能为空", None
        
        command = command.strip().lower()
        exists = command in COMMAND_HELP
        
        data = {
            "command": command,
            "exists": exists,
            "available_commands": list(COMMAND_HELP.keys()) if not exists else None
        }
        
        if exists:
            logger.info("命令存在", command=command)
            return True, f"命令 '{command}' 存在", data
        else:
            logger.warning("命令不存在", command=command)
            return True, f"命令 '{command}' 不存在", data
        
    except Exception as e:
        error_msg = f"验证命令存在性失败: {e}"
        logger.error(error_msg, command=command, error=str(e))
        return False, error_msg, None