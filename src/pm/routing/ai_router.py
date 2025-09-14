"""AI路由器 - 将自然语言转换为PM命令"""

import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class RouteResult:
    """路由结果"""
    command: str
    args: List[str]
    confidence: float
    explanation: str
    requires_confirmation: bool = True


class AIRouter:
    """AI路由器 - 负责将自然语言意图转换为具体的PM命令"""
    
    def __init__(self):
        self.command_patterns = self._initialize_command_patterns()
        
    def _initialize_command_patterns(self) -> Dict[str, Dict]:
        """初始化命令匹配模式"""
        return {
            # 任务管理命令
            "capture": {
                "keywords": ["添加", "创建", "新建", "记录", "capture", "add", "create"],
                "contexts": ["任务", "task", "事项", "待办"],
                "command": "pm capture",
                "confidence_boost": 0.1,
                "extract_content": True
            },
            "inbox": {
                "keywords": ["查看", "显示", "show", "list"],
                "contexts": ["收件箱", "inbox", "待处理"],
                "command": "pm inbox",
                "confidence_boost": 0.15
            },
            "today": {
                "keywords": ["推荐", "今日", "today", "建议", "recommend"],
                "contexts": ["任务", "task", "行动", "做什么"],
                "command": "pm today",
                "confidence_boost": 0.2
            },
            "next": {
                "keywords": ["下一步", "next", "接下来"],
                "contexts": ["行动", "action", "任务", "task"],
                "command": "pm next",
                "confidence_boost": 0.15
            },
            
            # 项目管理命令
            "projects_overview": {
                "keywords": ["查看", "显示", "show", "概览", "overview"],
                "contexts": ["项目", "project", "工程"],
                "command": "pm projects overview",
                "confidence_boost": 0.1
            },
            "project_status": {
                "keywords": ["状态", "status", "进展", "progress"],
                "contexts": ["项目", "project"],
                "command": "pm project status",
                "confidence_boost": 0.1,
                "extract_project_name": True
            },
            
            # 习惯管理命令
            "habits_create": {
                "keywords": ["创建", "新建", "添加", "create", "add"],
                "contexts": ["习惯", "habit"],
                "command": "pm habits create",
                "confidence_boost": 0.05,
                "extract_content": True
            },
            "habits_status": {
                "keywords": ["状态", "显示", "查看", "status", "show"],
                "contexts": ["习惯", "habit"],
                "command": "pm habits status",
                "confidence_boost": 0.1
            },
            "habits_track": {
                "keywords": ["完成", "记录", "打卡", "track", "done"],
                "contexts": ["习惯", "habit"],
                "command": "pm habits track",
                "confidence_boost": 0.1,
                "extract_content": True
            },
            
            # 系统命令
            "help": {
                "keywords": ["帮助", "help", "怎么", "如何", "不懂"],
                "contexts": [],
                "command": "pm help",
                "confidence_boost": 0.3
            },
            "version": {
                "keywords": ["版本", "version", "ver"],
                "contexts": [],
                "command": "pm version",
                "confidence_boost": 0.2
            }
        }
    
    def route(self, utterance: str) -> Dict[str, Any]:
        """
        将自然语言路由到PM命令
        
        Args:
            utterance: 用户的自然语言输入
            
        Returns:
            路由结果字典
        """
        try:
            # 清理输入
            clean_utterance = self._clean_utterance(utterance)
            
            # 查找最佳匹配
            best_match = self._find_best_match(clean_utterance)
            
            if best_match:
                return self._build_route_result(clean_utterance, best_match)
            else:
                return self._build_fallback_result(utterance)
                
        except Exception as e:
            return self._build_error_result(utterance, str(e))
    
    def _clean_utterance(self, utterance: str) -> str:
        """清理用户输入"""
        # 移除多余空格，转换为小写
        cleaned = re.sub(r'\s+', ' ', utterance.strip().lower())
        return cleaned
    
    def _find_best_match(self, utterance: str) -> Optional[Tuple[str, Dict, float]]:
        """查找最佳匹配的命令"""
        best_score = 0.0
        best_pattern = None
        best_key = None
        
        for pattern_key, pattern in self.command_patterns.items():
            score = self._calculate_match_score(utterance, pattern)
            if score > best_score:
                best_score = score
                best_pattern = pattern
                best_key = pattern_key
        
        # 只返回置信度大于阈值的匹配
        if best_score > 0.3:
            return best_key, best_pattern, best_score
        
        return None
    
    def _calculate_match_score(self, utterance: str, pattern: Dict) -> float:
        """计算匹配分数"""
        score = 0.0
        
        # 检查关键词匹配
        keyword_matches = 0
        for keyword in pattern["keywords"]:
            if keyword.lower() in utterance:
                keyword_matches += 1
        
        if keyword_matches > 0:
            score += 0.4 + (keyword_matches - 1) * 0.1  # 第一个关键词0.4，后续每个0.1
        
        # 检查上下文匹配
        context_matches = 0
        for context in pattern["contexts"]:
            if context.lower() in utterance:
                context_matches += 1
        
        if context_matches > 0:
            score += 0.3 + (context_matches - 1) * 0.05  # 第一个上下文0.3，后续每个0.05
        
        # 应用置信度提升
        score += pattern.get("confidence_boost", 0.0)
        
        # 确保分数不超过1.0
        return min(score, 1.0)
    
    def _build_route_result(self, utterance: str, match_info: Tuple[str, Dict, float]) -> Dict[str, Any]:
        """构建路由结果"""
        pattern_key, pattern, confidence = match_info
        
        command = pattern["command"]
        args = []
        explanation = f"根据输入 '{utterance}' 识别为 {pattern_key} 命令"
        
        # 提取内容参数
        if pattern.get("extract_content"):
            content = self._extract_content(utterance, pattern)
            if content:
                args.append(content)
                explanation += f"，内容：{content}"
        
        # 提取项目名称
        if pattern.get("extract_project_name"):
            project_name = self._extract_project_name(utterance)
            if project_name:
                args.append(project_name)
                explanation += f"，项目：{project_name}"
        
        # 根据置信度决定是否需要确认
        requires_confirmation = confidence < 0.85
        
        return {
            "command": command,
            "args": args,
            "confidence": confidence,
            "explanation": explanation,
            "requires_confirmation": requires_confirmation
        }
    
    def _extract_content(self, utterance: str, pattern: Dict) -> Optional[str]:
        """从输入中提取内容"""
        # 移除命令关键词，剩下的作为内容
        content = utterance
        
        # 移除关键词
        for keyword in pattern["keywords"]:
            content = content.replace(keyword.lower(), "")
        
        # 移除上下文词
        for context in pattern["contexts"]:
            content = content.replace(context.lower(), "")
        
        # 清理并返回
        content = content.strip()
        return content if content else None
    
    def _extract_project_name(self, utterance: str) -> Optional[str]:
        """提取项目名称"""
        # 简单实现：查找引号中的内容
        quoted_match = re.search(r'["\']([^"\']+)["\']', utterance)
        if quoted_match:
            return quoted_match.group(1)
        
        # 对于中文，使用正则表达式匹配项目名称模式
        # 匹配 "显示XXX项目状态" 中的 XXX 部分
        chinese_project_match = re.search(r'(?:显示|查看)([^项目状态]+)(?:项目)?(?:状态)?', utterance)
        if chinese_project_match:
            project_name = chinese_project_match.group(1).strip()
            if project_name:
                return project_name
        
        # 否则按空格分词处理英文
        words = utterance.split()
        if len(words) > 1:
            common_words = {"项目", "project", "状态", "status", "查看", "显示", "show"}
            project_words = [w for w in words if w.lower() not in common_words]
            
            # 只返回最后几个有意义的词
            if len(project_words) >= 2:
                return " ".join(project_words[-2:])
            elif len(project_words) == 1:
                return project_words[0]
        
        return None
    
    def _build_fallback_result(self, utterance: str) -> Dict[str, Any]:
        """构建备用结果（无法理解时）"""
        return {
            "command": "pm help",
            "args": [],
            "confidence": 0.2,
            "explanation": f"无法理解指令 '{utterance}'，显示帮助信息",
            "requires_confirmation": True
        }
    
    def _build_error_result(self, utterance: str, error: str) -> Dict[str, Any]:
        """构建错误结果"""
        return {
            "command": "pm help",
            "args": [],
            "confidence": 0.1,
            "explanation": f"处理指令 '{utterance}' 时出错: {error}",
            "requires_confirmation": True,
            "error": error
        }
    
    def suggest_alternatives(self, utterance: str) -> List[Dict[str, Any]]:
        """为无法理解的输入建议替代方案"""
        alternatives = []
        
        # 计算所有模式的匹配分数
        scores = []
        for pattern_key, pattern in self.command_patterns.items():
            score = self._calculate_match_score(utterance.lower(), pattern)
            if score > 0.1:  # 只考虑有一定相关性的
                scores.append((pattern_key, pattern, score))
        
        # 排序并取前3个
        scores.sort(key=lambda x: x[2], reverse=True)
        
        for pattern_key, pattern, score in scores[:3]:
            alternatives.append({
                "command": pattern["command"],
                "explanation": f"可能想要执行: {pattern['command']}",
                "confidence": score,
                "similarity": score
            })
        
        return alternatives