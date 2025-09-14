"""测试工作空间校验功能"""

import pytest
import tempfile
import shutil
import json
import yaml
from pathlib import Path

from pm.workspace.scaffold import init_workspace
from pm.workspace.validate import (
    validate_workspace,
    ValidationReport,
    ValidationItem,
    CheckLevel
)


class TestValidateWorkspace:
    """测试 validate_workspace 函数"""

    def setup_method(self):
        """每个测试方法前创建临时目录"""
        self.temp_dir = tempfile.mkdtemp()
        self.root = Path(self.temp_dir)

    def teardown_method(self):
        """每个测试方法后清理临时目录"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_validate_missing_workspace(self):
        """测试工作空间不存在的情况"""
        report = validate_workspace(self.root)

        assert not report.is_valid()
        assert report.summary["error"] == 1
        assert report.summary["ok"] == 0
        assert len(report.items) == 1
        assert report.items[0].check == "workspace_directory"
        assert report.items[0].level == CheckLevel.ERROR
        assert "不存在" in report.items[0].message

    def test_validate_valid_workspace(self):
        """测试有效工作空间"""
        # 先创建工作空间
        init_workspace(self.root)

        # 校验
        report = validate_workspace(self.root)

        assert report.is_valid()
        assert report.summary["error"] == 0
        assert report.summary["ok"] > 0

        # 检查关键项通过
        checks = [item.check for item in report.items if item.level == CheckLevel.OK]
        assert "workspace_directory" in checks
        assert "file_exists_workspace-config.yaml" in checks
        assert "file_exists_ai-agent-definition.md" in checks
        assert "file_exists_interaction-patterns.json" in checks

    def test_validate_missing_files(self):
        """测试缺少部分文件"""
        # 创建工作空间目录但不创建文件
        workspace_dir = self.root / ".personalmanager"
        workspace_dir.mkdir(parents=True)

        report = validate_workspace(self.root)

        assert not report.is_valid()
        assert report.summary["error"] == 3  # 三个文件都缺失

        # 验证错误消息
        error_checks = [item.check for item in report.items if item.level == CheckLevel.ERROR]
        assert "file_exists_workspace-config.yaml" in error_checks
        assert "file_exists_ai-agent-definition.md" in error_checks
        assert "file_exists_interaction-patterns.json" in error_checks

    def test_validate_yaml_syntax_error(self):
        """测试 YAML 语法错误"""
        workspace_dir = self.root / ".personalmanager"
        workspace_dir.mkdir(parents=True)

        # 创建语法错误的 YAML 文件
        config_file = workspace_dir / "workspace-config.yaml"
        config_file.write_text("""
workspace:
  name: test
  invalid yaml syntax
    - list item without proper indentation
""")

        # 创建其他有效文件
        (workspace_dir / "ai-agent-definition.md").write_text("# Test")
        (workspace_dir / "interaction-patterns.json").write_text('{"version": "1.0", "locale": [], "intents": []}')

        report = validate_workspace(self.root)

        assert not report.is_valid()
        yaml_errors = [item for item in report.items if "yaml_syntax" in item.check and item.level == CheckLevel.ERROR]
        assert len(yaml_errors) > 0
        assert "语法错误" in yaml_errors[0].message

    def test_validate_json_syntax_error(self):
        """测试 JSON 语法错误"""
        workspace_dir = self.root / ".personalmanager"
        workspace_dir.mkdir(parents=True)

        # 创建有效的 YAML 和 MD 文件
        (workspace_dir / "workspace-config.yaml").write_text("workspace: {name: test}\nstartup: {}\nagents: {}\nprivacy: {}")
        (workspace_dir / "ai-agent-definition.md").write_text("# Test")

        # 创建语法错误的 JSON 文件
        patterns_file = workspace_dir / "interaction-patterns.json"
        patterns_file.write_text('{"version": "1.0", "locale": [,], "intents": []}')  # 语法错误

        report = validate_workspace(self.root)

        assert not report.is_valid()
        json_errors = [item for item in report.items if "json_syntax" in item.check and item.level == CheckLevel.ERROR]
        assert len(json_errors) > 0
        assert "语法错误" in json_errors[0].message

    def test_validate_missing_required_fields(self):
        """测试缺少必填字段"""
        workspace_dir = self.root / ".personalmanager"
        workspace_dir.mkdir(parents=True)

        # 创建缺少必填字段的文件
        (workspace_dir / "workspace-config.yaml").write_text("workspace: {name: test}")  # 缺少其他必填字段
        (workspace_dir / "ai-agent-definition.md").write_text("# Test")
        (workspace_dir / "interaction-patterns.json").write_text('{"version": "1.0"}')  # 缺少 locale 和 intents

        report = validate_workspace(self.root)

        assert not report.is_valid()

        # 检查必填字段错误
        field_errors = [item for item in report.items if "required_fields" in item.check and item.level == CheckLevel.ERROR]
        assert len(field_errors) == 2  # YAML 和 JSON 都缺少字段

    def test_validate_file_size_limit(self):
        """测试文件大小限制"""
        workspace_dir = self.root / ".personalmanager"
        workspace_dir.mkdir(parents=True)

        # 创建正常大小的文件
        (workspace_dir / "workspace-config.yaml").write_text("workspace: {name: test}\nstartup: {}\nagents: {}\nprivacy: {}")
        (workspace_dir / "ai-agent-definition.md").write_text("# Test")

        # 创建超大的 JSON 文件（超过 50KB 限制）
        large_intents = [{"id": f"intent_{i}", "phrases": ["test"] * 100} for i in range(1000)]
        large_json = {
            "version": "1.0",
            "locale": ["zh", "en"],
            "intents": large_intents
        }
        (workspace_dir / "interaction-patterns.json").write_text(json.dumps(large_json))

        report = validate_workspace(self.root)

        # 应该有文件大小警告
        size_warnings = [item for item in report.items if "file_size" in item.check and item.level == CheckLevel.WARN]
        assert len(size_warnings) > 0
        assert "文件过大" in size_warnings[0].message

    def test_validate_invalid_field_values(self):
        """测试无效的字段值"""
        workspace_dir = self.root / ".personalmanager"
        workspace_dir.mkdir(parents=True)

        # 创建包含无效值的配置
        config = {
            "workspace": {"name": "test", "language": "invalid_lang"},  # 无效语言
            "startup": {},
            "agents": {"preferred": "invalid_agent"},  # 无效平台
            "privacy": {"external_calls": "invalid_policy"},  # 无效策略
            "routing": {
                "low_confidence_threshold": 1.5,  # 超出范围
                "high_confidence_threshold": -0.1  # 超出范围
            }
        }
        (workspace_dir / "workspace-config.yaml").write_text(yaml.dump(config))
        (workspace_dir / "ai-agent-definition.md").write_text("# Test")
        (workspace_dir / "interaction-patterns.json").write_text('{"version": "1.0", "locale": [], "intents": []}')

        report = validate_workspace(self.root)

        # 检查各种警告和错误
        assert not report.is_valid()  # 阈值范围错误

        warnings = [item for item in report.items if item.level == CheckLevel.WARN]
        errors = [item for item in report.items if item.level == CheckLevel.ERROR]

        # 应该有语言、平台、策略的警告
        warning_messages = " ".join([w.message for w in warnings])
        assert "不支持的语言" in warning_messages
        assert "不支持的 Agent 平台" in warning_messages
        assert "无效的外部调用策略" in warning_messages

        # 应该有阈值范围错误
        error_messages = " ".join([e.message for e in errors])
        assert "超出范围" in error_messages

    def test_validate_threshold_logic(self):
        """测试阈值逻辑检查"""
        workspace_dir = self.root / ".personalmanager"
        workspace_dir.mkdir(parents=True)

        # 创建低阈值大于高阈值的配置
        config = {
            "workspace": {"name": "test"},
            "startup": {},
            "agents": {},
            "privacy": {},
            "routing": {
                "low_confidence_threshold": 0.8,
                "high_confidence_threshold": 0.5  # 低于低阈值
            }
        }
        (workspace_dir / "workspace-config.yaml").write_text(yaml.dump(config))
        (workspace_dir / "ai-agent-definition.md").write_text("# Test")
        (workspace_dir / "interaction-patterns.json").write_text('{"version": "1.0", "locale": [], "intents": []}')

        report = validate_workspace(self.root)

        # 应该有阈值逻辑警告
        threshold_warnings = [item for item in report.items
                             if "routing_threshold" in item.check and item.level == CheckLevel.WARN]
        assert len(threshold_warnings) > 0
        assert "低置信度阈值应小于高置信度阈值" in threshold_warnings[0].message

    def test_validate_markdown_sections(self):
        """测试 Markdown 文件章节检查"""
        workspace_dir = self.root / ".personalmanager"
        workspace_dir.mkdir(parents=True)

        # 创建有效的其他文件
        (workspace_dir / "workspace-config.yaml").write_text("workspace: {}\nstartup: {}\nagents: {}\nprivacy: {}")
        (workspace_dir / "interaction-patterns.json").write_text('{"version": "1.0", "locale": [], "intents": []}')

        # 创建缺少章节的 MD 文件
        (workspace_dir / "ai-agent-definition.md").write_text("""
# PersonalManager AI Agent

## 身份与角色
测试内容

## 工作原则
测试内容
""")  # 缺少"交互规范"和"服务边界"

        report = validate_workspace(self.root)

        # 应该有章节缺失警告
        section_warnings = [item for item in report.items
                           if "markdown_sections" in item.check and item.level == CheckLevel.WARN]
        assert len(section_warnings) > 0
        assert "缺少建议章节" in section_warnings[0].message
        assert "交互规范" in section_warnings[0].message
        assert "服务边界" in section_warnings[0].message

    def test_validate_context_paths(self):
        """测试上下文路径校验"""
        workspace_dir = self.root / ".personalmanager"
        workspace_dir.mkdir(parents=True)

        # 创建引用不存在文件的配置
        config = {
            "workspace": {},
            "startup": {},
            "agents": {},
            "privacy": {},
            "context": {
                "always_load": ["docs/README.md", "nonexistent.txt"]
            }
        }
        (workspace_dir / "workspace-config.yaml").write_text(yaml.dump(config))
        (workspace_dir / "ai-agent-definition.md").write_text("# Test")
        (workspace_dir / "interaction-patterns.json").write_text('{"version": "1.0", "locale": [], "intents": []}')

        report = validate_workspace(self.root)

        # 应该有路径不存在的警告
        path_warnings = [item for item in report.items
                        if "context_path" in item.check and item.level == CheckLevel.WARN]
        assert len(path_warnings) == 2  # 两个文件都不存在

    def test_validate_empty_intents(self):
        """测试空的意图数组"""
        workspace_dir = self.root / ".personalmanager"
        workspace_dir.mkdir(parents=True)

        (workspace_dir / "workspace-config.yaml").write_text("workspace: {}\nstartup: {}\nagents: {}\nprivacy: {}")
        (workspace_dir / "ai-agent-definition.md").write_text("# Test")
        (workspace_dir / "interaction-patterns.json").write_text('{"version": "1.0", "locale": [], "intents": []}')

        report = validate_workspace(self.root)

        # 应该有空意图数组的警告
        intent_warnings = [item for item in report.items
                          if "intents_empty" in item.check and item.level == CheckLevel.WARN]
        assert len(intent_warnings) > 0
        assert "intents 数组为空" in intent_warnings[0].message

    def test_validate_report_to_dict(self):
        """测试报告转换为字典"""
        init_workspace(self.root)
        report = validate_workspace(self.root)

        # 转换为字典
        report_dict = report.to_dict()

        assert "items" in report_dict
        assert "summary" in report_dict
        assert isinstance(report_dict["items"], list)
        assert isinstance(report_dict["summary"], dict)

        # 每个 item 应该有正确的结构
        for item in report_dict["items"]:
            assert "check" in item
            assert "level" in item
            assert "message" in item
            # suggest 是可选的