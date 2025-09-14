"""
Unit tests for IntentMatcher

Tests the core intent matching functionality, confidence calculation,
and argument extraction according to Sprint 2 specifications.
"""

import json
import pytest
import tempfile
import os
from pathlib import Path

from pm.routing.intent_matcher import IntentMatcher, MatchResult


class TestIntentMatcher:
    """Test suite for IntentMatcher class"""

    @pytest.fixture
    def sample_patterns(self):
        """Create sample interaction patterns for testing"""
        return {
            "version": "1.0",
            "locale": ["zh", "en"],
            "description": "Test patterns",
            "intents": [
                {
                    "id": "today",
                    "description": "获取今日重点推荐",
                    "phrases": [
                        "今天做什么",
                        "今日重点",
                        "what should i do today",
                        "today's tasks"
                    ],
                    "pattern": None,
                    "command": "pm today",
                    "args_schema": {
                        "count": {
                            "type": "int",
                            "default": 3,
                            "min": 1,
                            "max": 10
                        }
                    },
                    "confirm": {
                        "low_confidence": "将获取今日推荐任务，确定吗？"
                    }
                },
                {
                    "id": "capture",
                    "description": "记录/捕获任务",
                    "phrases": [
                        "记录",
                        "添加任务",
                        "capture",
                        "add task"
                    ],
                    "pattern": r"^(?:记录|添加任务|capture|add task)[:：\s]+(?P<content>.+)$",
                    "command": "pm capture \"{content}\"",
                    "args_schema": {
                        "content": {
                            "type": "string",
                            "required": True,
                            "min_length": 1
                        }
                    },
                    "confirm": {
                        "low_confidence": "将记录任务：{content}，确定吗？"
                    }
                },
                {
                    "id": "projects_overview",
                    "description": "项目状态总览",
                    "phrases": [
                        "项目概览",
                        "项目状态",
                        "overview projects",
                        "project status"
                    ],
                    "pattern": None,
                    "command": "pm projects overview",
                    "args_schema": {
                        "sort": {
                            "type": "string",
                            "default": "health",
                            "enum": ["health", "priority", "progress", "name"]
                        }
                    },
                    "confirm": {
                        "low_confidence": "将查看项目概览，确定吗？"
                    }
                },
                {
                    "id": "project_status",
                    "description": "单个项目状态",
                    "phrases": [
                        "项目进展",
                        "项目状态"
                    ],
                    "pattern": r"^(?P<name>.+?)\s*(?:项目)?\s*(?:进展|状态)$",
                    "command": "pm project status \"{name}\"",
                    "args_schema": {
                        "name": {
                            "type": "string",
                            "required": True,
                            "min_length": 1
                        }
                    },
                    "confirm": {
                        "low_confidence": "将查看项目 {name} 的状态，确定吗？"
                    }
                },
                {
                    "id": "doctor",
                    "description": "系统诊断",
                    "phrases": [
                        "系统诊断",
                        "检查系统",
                        "system check",
                        "doctor"
                    ],
                    "pattern": None,
                    "command": "pm doctor main",
                    "args_schema": {},
                    "confirm": {
                        "low_confidence": "将运行系统诊断，确定吗？"
                    }
                }
            ]
        }

    @pytest.fixture
    def patterns_file(self, sample_patterns):
        """Create temporary patterns file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_patterns, f, ensure_ascii=False, indent=2)
            patterns_path = f.name

        yield patterns_path

        # Cleanup
        os.unlink(patterns_path)

    @pytest.fixture
    def matcher(self, patterns_file):
        """Create IntentMatcher instance with test patterns"""
        return IntentMatcher(patterns_file)

    def test_exact_phrase_matching(self, matcher):
        """Test exact phrase matching gives confidence 1.0"""
        result = matcher.match_intent("今天做什么")

        assert result.intent == "today"
        assert result.confidence == 1.0
        assert result.command == "pm today"
        assert result.args["count"] == 3  # default value

    def test_partial_phrase_matching(self, matcher):
        """Test partial phrase matching gives confidence between 0.5-0.8"""
        result = matcher.match_intent("今天")

        assert result.intent == "today"
        assert 0.5 <= result.confidence <= 0.8
        assert result.command == "pm today"

    def test_pattern_matching_with_extraction(self, matcher):
        """Test pattern matching with argument extraction"""
        result = matcher.match_intent("记录 完成项目文档")

        assert result.intent == "capture"
        assert result.confidence >= 0.7  # pattern match confidence
        assert result.command == "pm capture \"完成项目文档\""
        assert result.args["content"] == "完成项目文档"

    def test_project_name_extraction(self, matcher):
        """Test project name extraction from pattern"""
        result = matcher.match_intent("PersonalManager 项目状态")

        assert result.intent == "project_status"
        assert result.confidence >= 0.7
        assert result.command == "pm project status \"PersonalManager\""
        assert result.args["name"] == "PersonalManager"

    def test_english_phrase_matching(self, matcher):
        """Test English phrase matching"""
        result = matcher.match_intent("what should i do today")

        assert result.intent == "today"
        assert result.confidence == 1.0
        assert result.command == "pm today"

    def test_unknown_utterance(self, matcher):
        """Test handling of unknown utterances"""
        result = matcher.match_intent("这是一个未知的指令")

        assert result.intent == "unknown"
        assert result.confidence == 0.0
        assert result.command == ""
        assert result.confirm_message == "未识别的指令，请尝试其他表达方式"

    def test_low_confidence_confirmation_message(self, matcher):
        """Test confirmation message for low confidence matches"""
        # Create a partial match to trigger low confidence
        result = matcher.match_intent("记录")  # partial match

        # Should match capture intent but with low confidence
        if result.confidence < 0.8:
            assert result.confirm_message is not None
            assert "记录任务" in result.confirm_message or "capture" in result.confirm_message

    def test_default_argument_values(self, matcher):
        """Test default argument values from schema"""
        result = matcher.match_intent("项目概览")

        assert result.intent == "projects_overview"
        assert result.command == "pm projects overview"
        assert result.args["sort"] == "health"  # default value

    def test_case_insensitive_matching(self, matcher):
        """Test case insensitive matching"""
        result = matcher.match_intent("SYSTEM CHECK")

        assert result.intent == "doctor"
        assert result.confidence == 1.0
        assert result.command == "pm doctor main"

    def test_get_supported_intents(self, matcher):
        """Test getting list of supported intents"""
        intents = matcher.get_supported_intents()

        expected_intents = ["today", "capture", "projects_overview", "project_status", "doctor"]
        assert set(intents) == set(expected_intents)

    def test_get_intent_description(self, matcher):
        """Test getting intent descriptions"""
        description = matcher.get_intent_description("today")
        assert description == "获取今日重点推荐"

        unknown_description = matcher.get_intent_description("unknown_intent")
        assert unknown_description is None

    def test_confidence_calculation_ranges(self, matcher):
        """Test confidence calculation for different match types"""
        # Exact match
        exact_result = matcher.match_intent("系统诊断")
        assert exact_result.confidence == 1.0

        # Partial match (utterance contained in phrase)
        partial_result = matcher.match_intent("诊断")
        assert 0.5 <= partial_result.confidence <= 0.8

        # Pattern match
        pattern_result = matcher.match_intent("添加任务 测试任务")
        assert pattern_result.confidence >= 0.7

    def test_file_not_found_error(self):
        """Test error handling for missing patterns file"""
        with pytest.raises(FileNotFoundError):
            IntentMatcher("/non/existent/file.json")

    def test_invalid_json_error(self):
        """Test error handling for invalid JSON"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content")
            invalid_file = f.name

        try:
            with pytest.raises(ValueError):
                IntentMatcher(invalid_file)
        finally:
            os.unlink(invalid_file)

    def test_command_placeholder_replacement(self, matcher):
        """Test command template placeholder replacement"""
        result = matcher.match_intent("capture 写文档")

        # Should replace {content} placeholder
        assert result.command == "pm capture \"写文档\""
        assert "{content}" not in result.command

    def test_empty_utterance_handling(self, matcher):
        """Test handling of empty or whitespace-only utterances"""
        result = matcher.match_intent("   ")

        assert result.intent == "unknown"
        assert result.confidence == 0.0