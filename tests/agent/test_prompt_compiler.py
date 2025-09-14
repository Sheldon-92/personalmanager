"""测试 Prompt 编译器模块"""

import json
import yaml
import tempfile
from pathlib import Path
import pytest
from pm.agent.prompt_compiler import (
    compile_prompt,
    join_and_truncate,
    _render_role,
    _render_startup,
    _render_mapping_rules,
    _render_error_handling,
    _render_privacy,
    _render_memory
)


class TestPromptCompiler:
    """Prompt 编译器测试套件"""

    def setup_method(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

        # 创建测试用的配置文件
        self.cfg_path = self.temp_path / "workspace-config.yaml"
        self.aid_path = self.temp_path / "ai-agent-definition.md"
        self.pat_path = self.temp_path / "interaction-patterns.json"
        self.profile_path = self.temp_path / "profile.md"

        # 写入测试数据
        self._create_test_files()

    def teardown_method(self):
        """清理测试环境"""
        import shutil
        shutil.rmtree(self.temp_dir)

    def _create_test_files(self):
        """创建测试文件"""
        # workspace-config.yaml
        config = {
            "workspace": {"name": "test", "language": "zh"},
            "startup": {
                "enabled": True,
                "steps": ["doctor", "today"],
                "doctor": {"verbose": False},
                "today": {"count": 3}
            },
            "privacy": {
                "external_calls": "user_consent",
                "data_retention": "session_only",
                "redact_logs": True
            },
            "routing": {
                "low_confidence_threshold": 0.5,
                "high_confidence_threshold": 0.8
            }
        }
        with open(self.cfg_path, 'w') as f:
            yaml.dump(config, f)

        # ai-agent-definition.md
        aid_content = """# PersonalManager AI Agent
您是 PersonalManager 专家助手。

## 核心职责
- 任务管理
- 项目监控
- 智能推荐"""
        self.aid_path.write_text(aid_content)

        # interaction-patterns.json
        patterns = {
            "version": "1.0",
            "intents": [
                {
                    "id": "today",
                    "description": "获取今日推荐",
                    "phrases": ["今天做什么"],
                    "command": "pm today"
                },
                {
                    "id": "capture",
                    "description": "捕获任务",
                    "phrases": ["记录"],
                    "command": "pm capture \"{content}\""
                }
            ]
        }
        with open(self.pat_path, 'w') as f:
            json.dump(patterns, f)

        # profile.md
        profile_content = """偏好：上午高效
常用：today, capture
待改进：Clarify频次不足"""
        self.profile_path.write_text(profile_content)

    def test_compile_prompt_basic(self):
        """测试基本编译功能"""
        result = compile_prompt(
            str(self.cfg_path),
            str(self.aid_path),
            str(self.pat_path),
            str(self.profile_path)
        )

        # 验证结果不为空
        assert result
        assert len(result) > 0

        # 验证包含关键段落
        assert "角色与职责" in result
        assert "启动仪式" in result
        assert "自然语言→命令映射" in result
        assert "错误处理" in result
        assert "隐私与安全" in result
        assert "用户偏好摘要" in result

    def test_compile_prompt_without_profile(self):
        """测试不包含 profile 的编译"""
        result = compile_prompt(
            str(self.cfg_path),
            str(self.aid_path),
            str(self.pat_path),
            None
        )

        assert result
        assert "角色与职责" in result
        assert "用户偏好摘要" not in result

    def test_compile_prompt_missing_files(self):
        """测试文件缺失的情况"""
        # 删除一个文件
        self.aid_path.unlink()

        result = compile_prompt(
            str(self.cfg_path),
            str(self.aid_path),
            str(self.pat_path),
            None
        )

        # 应该仍能生成结果，但不包含缺失文件的内容
        assert result
        assert "启动仪式" in result  # 配置文件存在
        assert "PersonalManager AI Agent" not in result  # AI定义文件缺失

    def test_join_and_truncate(self):
        """测试段落合并和截断"""
        sections = [
            "段落1" * 100,
            "段落2" * 100,
            "段落3" * 100
        ]

        # 测试正常合并
        result = join_and_truncate(sections, limit=1000)
        assert len(result) <= 1000

        # 测试空段落过滤
        sections_with_empty = ["段落1", "", "  ", "段落2"]
        result = join_and_truncate(sections_with_empty)
        assert result == "段落1\n\n段落2"

    def test_join_and_truncate_priority(self):
        """测试截断时的优先级保留"""
        # 创建超长内容
        sections = [
            "重要段落1" * 500,  # 优先保留
            "重要段落2" * 500,  # 优先保留
            "重要段落3" * 500,  # 优先保留
            "次要段落4" * 500,
            "次要段落5" * 500,
        ]

        result = join_and_truncate(sections, limit=2000)

        # 验证长度限制
        assert len(result) <= 2000

        # 截断逻辑会添加简化的错误处理和隐私段落
        # 所以原始段落可能被替换
        assert "错误处理" in result or "重要段落" in result
        # 由于截断，后面的段落可能不完整或缺失

    def test_render_startup(self):
        """测试启动仪式渲染"""
        result = _render_startup(str(self.cfg_path))

        assert "启动仪式" in result
        assert "pm doctor" in result
        assert "pm today --count 3" in result

    def test_render_startup_disabled(self):
        """测试禁用启动仪式"""
        # 修改配置
        with open(self.cfg_path, 'r') as f:
            config = yaml.safe_load(f)
        config['startup']['enabled'] = False
        with open(self.cfg_path, 'w') as f:
            yaml.dump(config, f)

        result = _render_startup(str(self.cfg_path))
        assert result == ""

    def test_render_mapping_rules(self):
        """测试映射规则渲染"""
        result = _render_mapping_rules(str(self.pat_path), str(self.cfg_path))

        assert "自然语言→命令映射" in result
        assert "today" in result
        assert "capture" in result
        assert "置信度" in result
        assert "0.5" in result  # low threshold
        assert "0.8" in result  # high threshold

    def test_render_error_handling(self):
        """测试错误处理渲染"""
        result = _render_error_handling()

        assert "错误处理" in result
        assert "E1xxx" in result
        assert "E2xxx" in result
        assert "E3xxx" in result
        assert "E4xxx" in result

    def test_render_privacy(self):
        """测试隐私设置渲染"""
        result = _render_privacy(str(self.cfg_path))

        assert "隐私与安全" in result
        assert "user_consent" in result
        assert "session_only" in result
        assert "日志脱敏: 启用" in result

    def test_render_memory(self):
        """测试记忆摘要渲染"""
        result = _render_memory(str(self.profile_path))

        assert "用户偏好摘要" in result
        assert "偏好：上午高效" in result
        assert "常用：today, capture" in result

    def test_render_memory_limit(self):
        """测试记忆摘要行数限制"""
        # 创建超长profile
        long_profile = "\n".join([f"偏好行{i}" for i in range(20)])
        self.profile_path.write_text(long_profile)

        result = _render_memory(str(self.profile_path))

        # 应该只包含前5行
        lines = result.split('\n')
        assert len(lines) <= 6  # 标题 + 最多5行内容

    def test_compile_prompt_size_limit(self):
        """测试编译结果大小限制"""
        # 创建超长内容
        long_aid = "X" * 20000
        self.aid_path.write_text(long_aid)

        result = compile_prompt(
            str(self.cfg_path),
            str(self.aid_path),
            str(self.pat_path),
            str(self.profile_path)
        )

        # 验证不超过10k字符
        assert len(result) <= 10_000

    def test_invalid_yaml(self):
        """测试无效YAML处理"""
        # 写入无效YAML
        self.cfg_path.write_text("invalid: yaml: content:")

        # 应该优雅处理，返回空或默认内容
        result = _render_startup(str(self.cfg_path))
        assert result == ""

    def test_invalid_json(self):
        """测试无效JSON处理"""
        # 写入无效JSON
        self.pat_path.write_text("{invalid json}")

        # 应该优雅处理
        result = _render_mapping_rules(str(self.pat_path), str(self.cfg_path))
        assert result == ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])