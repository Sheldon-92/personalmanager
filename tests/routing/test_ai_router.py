"""AIRouter 测试套件"""

import pytest
from pm.routing.ai_router import AIRouter, RouteResult


class TestAIRouter:
    """AIRouter 测试类"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.router = AIRouter()
    
    def test_initialization(self):
        """测试初始化"""
        assert self.router.command_patterns is not None
        assert len(self.router.command_patterns) > 0
    
    def test_command_patterns_loaded(self):
        """测试命令模式加载"""
        expected_patterns = [
            "capture", "inbox", "today", "next",
            "projects_overview", "habits_create", "help"
        ]
        
        for pattern in expected_patterns:
            assert pattern in self.router.command_patterns
    
    def test_clean_utterance(self):
        """测试输入清理"""
        test_cases = [
            ("  Hello   World  ", "hello world"),
            ("UPPER CASE", "upper case"),
            ("Mixed   Spacing", "mixed spacing"),
            ("", ""),
            ("   ", "")
        ]
        
        for input_text, expected in test_cases:
            result = self.router._clean_utterance(input_text)
            assert result == expected
    
    def test_extract_content_simple(self):
        """测试简单内容提取"""
        pattern = {
            "keywords": ["添加", "创建"],
            "contexts": ["任务"]
        }
        
        test_cases = [
            ("添加任务学习Python", "学习python"),
            ("创建任务买菜", "买菜"),
            ("添加学习任务", "学习"),
            ("创建", "")
        ]
        
        for utterance, expected in test_cases:
            result = self.router._extract_content(utterance.lower(), pattern)
            expected_result = expected if expected else None
            assert result == expected_result
    
    def test_extract_project_name(self):
        """测试项目名称提取"""
        test_cases = [
            ('查看项目 "PersonalManager" 状态', "PersonalManager"),
            ("显示前端重构项目状态", "前端重构"),  # 取最后两个有意义的词
            ("查看项目状态", None),
            ("", None)
        ]
        
        for utterance, expected in test_cases:
            result = self.router._extract_project_name(utterance)
            assert result == expected
    
    def test_calculate_match_score_high_match(self):
        """测试高匹配度分数计算"""
        pattern = {
            "keywords": ["添加", "创建"],
            "contexts": ["任务"],
            "confidence_boost": 0.1
        }
        
        utterance = "添加新任务到收件箱"
        score = self.router._calculate_match_score(utterance, pattern)
        
        # 期望得分: 关键词匹配(0.4) + 上下文匹配(0.3) + 置信度提升(0.1) = 0.8
        assert score >= 0.7
        assert score <= 1.0
    
    def test_calculate_match_score_partial_match(self):
        """测试部分匹配度分数计算"""
        pattern = {
            "keywords": ["添加", "创建"],
            "contexts": ["任务"],
            "confidence_boost": 0.0
        }
        
        utterance = "添加新内容"  # 只有关键词匹配，没有上下文
        score = self.router._calculate_match_score(utterance, pattern)
        
        # 期望得分: 关键词匹配(0.4) = 0.4
        assert score >= 0.35
        assert score <= 0.5
    
    def test_calculate_match_score_no_match(self):
        """测试无匹配度分数计算"""
        pattern = {
            "keywords": ["添加", "创建"],
            "contexts": ["任务"],
            "confidence_boost": 0.0
        }
        
        utterance = "显示帮助信息"  # 完全不匹配
        score = self.router._calculate_match_score(utterance, pattern)
        
        assert score == 0.0
    
    def test_route_capture_task(self):
        """测试任务捕获路由"""
        test_cases = [
            "添加任务学习Python",
            "创建新任务买菜",
            "记录任务开会讨论"
        ]
        
        for utterance in test_cases:
            result = self.router.route(utterance)
            
            assert result["command"] == "pm capture"
            assert len(result["args"]) > 0
            assert result["confidence"] > 0.5
            assert "任务" in result["explanation"] or "capture" in result["command"]
    
    def test_route_inbox_view(self):
        """测试收件箱查看路由"""
        test_cases = [
            "查看收件箱",
            "显示inbox",
            "show收件箱任务"
        ]
        
        for utterance in test_cases:
            result = self.router.route(utterance)
            
            assert result["command"] == "pm inbox"
            assert result["confidence"] > 0.5
    
    def test_route_today_recommendations(self):
        """测试今日推荐路由"""
        test_cases = [
            "今日推荐",
            "显示今日任务", 
            "今天做什么",
            "recommend today"
        ]
        
        for utterance in test_cases:
            result = self.router.route(utterance)
            
            assert result["command"] == "pm today"
            assert result["confidence"] >= 0.5
    
    def test_route_next_actions(self):
        """测试下一步行动路由"""
        test_cases = [
            "下一步行动",
            "接下来做什么",
            "next actions"
        ]
        
        for utterance in test_cases:
            result = self.router.route(utterance)
            
            assert result["command"] == "pm next"
            assert result["confidence"] > 0.4
    
    def test_route_projects_overview(self):
        """测试项目概览路由"""
        test_cases = [
            "查看项目概览",
            "显示所有项目",
            "项目overview"
        ]
        
        for utterance in test_cases:
            result = self.router.route(utterance)
            
            assert result["command"] == "pm projects overview"
            assert result["confidence"] > 0.4
    
    def test_route_habits_create(self):
        """测试习惯创建路由"""
        test_cases = [
            "创建新习惯读书",
            "添加习惯运动",
            "新建习惯早起"
        ]
        
        for utterance in test_cases:
            result = self.router.route(utterance)
            
            assert result["command"] == "pm habits create"
            assert len(result["args"]) > 0
            assert result["confidence"] > 0.4
    
    def test_route_habits_status(self):
        """测试习惯状态路由"""
        test_cases = [
            "查看习惯状态",
            "显示习惯情况",
            "habits status"
        ]
        
        for utterance in test_cases:
            result = self.router.route(utterance)
            
            assert result["command"] == "pm habits status"
            assert result["confidence"] > 0.4
    
    def test_route_help(self):
        """测试帮助路由"""
        test_cases = [
            "帮助",
            "help",
            "怎么使用",
            "如何操作",
            "不懂"
        ]
        
        for utterance in test_cases:
            result = self.router.route(utterance)
            
            assert result["command"] == "pm help"
            assert result["confidence"] > 0.5
    
    def test_route_version(self):
        """测试版本查询路由"""
        test_cases = [
            "版本信息",
            "version",
            "当前版本"
        ]
        
        for utterance in test_cases:
            result = self.router.route(utterance)
            
            assert result["command"] == "pm version"
            assert result["confidence"] > 0.4
    
    def test_route_fallback(self):
        """测试备用路由"""
        test_cases = [
            "完全不相关的内容",
            "随机文本",
            "xyz123"
        ]
        
        for utterance in test_cases:
            result = self.router.route(utterance)
            
            assert result["command"] == "pm help"
            assert result["confidence"] <= 0.3
            assert "无法理解" in result["explanation"]
    
    def test_route_confidence_levels(self):
        """测试置信度水平"""
        # 高置信度案例
        high_confidence_utterance = "help"
        result = self.router.route(high_confidence_utterance)
        assert result["confidence"] >= 0.7
        # 根据新的置信度阈值 (0.85)，help 命令可能还是需要确认
        
        # 低置信度案例
        low_confidence_utterance = "random text"
        result = self.router.route(low_confidence_utterance)
        assert result["confidence"] <= 0.3
        assert result["requires_confirmation"] is True
    
    def test_route_error_handling(self):
        """测试路由错误处理"""
        # 测试异常情况不会崩溃
        test_cases = [
            None,  # 注意：这会在_clean_utterance中失败
            "",
            " ",
            "a" * 1000  # 很长的字符串
        ]
        
        for utterance in test_cases:
            if utterance is None:
                # None 会导致异常，应该返回错误结果
                result = self.router.route(utterance)
                assert "error" in result or result["confidence"] <= 0.2
            else:
                result = self.router.route(utterance)
                assert "command" in result
                assert "confidence" in result
    
    def test_suggest_alternatives(self):
        """测试建议替代方案"""
        utterance = "任务管理"  # 模糊输入
        alternatives = self.router.suggest_alternatives(utterance)
        
        assert isinstance(alternatives, list)
        assert len(alternatives) > 0
        assert len(alternatives) <= 3
        
        for alt in alternatives:
            assert "command" in alt
            assert "explanation" in alt
            assert "confidence" in alt
            assert "similarity" in alt
    
    def test_find_best_match_threshold(self):
        """测试最佳匹配阈值"""
        # 低于阈值的匹配应该返回None
        very_low_match_utterance = "xyz random text"
        result = self.router._find_best_match(very_low_match_utterance)
        
        # 由于完全不匹配，应该返回None或得分很低
        if result:
            _, _, score = result
            assert score <= 0.3
        else:
            assert result is None


class TestRouteResult:
    """RouteResult 数据类测试"""
    
    def test_route_result_creation(self):
        """测试路由结果创建"""
        result = RouteResult(
            command="pm help",
            args=["capture"],
            confidence=0.9,
            explanation="显示捕获任务帮助"
        )
        
        assert result.command == "pm help"
        assert result.args == ["capture"]
        assert result.confidence == 0.9
        assert result.explanation == "显示捕获任务帮助"
        assert result.requires_confirmation is True  # 默认值
    
    def test_route_result_with_confirmation(self):
        """测试路由结果确认设置"""
        result = RouteResult(
            command="pm version",
            args=[],
            confidence=0.95,
            explanation="显示版本信息",
            requires_confirmation=False
        )
        
        assert result.requires_confirmation is False