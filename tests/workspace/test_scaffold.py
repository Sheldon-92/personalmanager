"""测试工作空间脚手架功能"""

import pytest
import tempfile
import shutil
from pathlib import Path

from pm.workspace.scaffold import init_workspace, ScaffoldReport


class TestInitWorkspace:
    """测试 init_workspace 函数"""

    def setup_method(self):
        """每个测试方法前创建临时目录"""
        self.temp_dir = tempfile.mkdtemp()
        self.root = Path(self.temp_dir)

    def teardown_method(self):
        """每个测试方法后清理临时目录"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_init_workspace_creates_files(self):
        """测试首次创建工作空间文件"""
        report = init_workspace(self.root)

        assert report.success is True
        assert len(report.created_files) == 3
        assert len(report.skipped_files) == 0
        assert len(report.errors) == 0

        # 验证文件存在
        workspace_dir = self.root / ".personalmanager"
        assert workspace_dir.exists()
        assert (workspace_dir / "workspace-config.yaml").exists()
        assert (workspace_dir / "ai-agent-definition.md").exists()
        assert (workspace_dir / "interaction-patterns.json").exists()

    def test_init_workspace_idempotent(self):
        """测试幂等性：第二次运行不覆盖文件"""
        # 第一次创建
        report1 = init_workspace(self.root)
        assert report1.success is True
        assert len(report1.created_files) == 3

        # 第二次运行
        report2 = init_workspace(self.root)
        assert report2.success is True
        assert len(report2.created_files) == 0
        assert len(report2.skipped_files) == 3
        assert len(report2.errors) == 0

    def test_init_workspace_force_overwrite(self):
        """测试强制覆盖模式"""
        # 第一次创建
        report1 = init_workspace(self.root)
        assert report1.success is True

        # 修改一个文件
        config_file = self.root / ".personalmanager" / "workspace-config.yaml"
        with open(config_file, 'w') as f:
            f.write("# Modified content\n")

        # 强制覆盖
        report2 = init_workspace(self.root, force=True)
        assert report2.success is True
        assert report2.force_mode is True
        assert len(report2.created_files) == 3
        assert len(report2.skipped_files) == 0

        # 验证文件被覆盖（内容不是 Modified content）
        with open(config_file, 'r') as f:
            content = f.read()
            assert "Modified content" not in content
            assert "PersonalManager" in content

    def test_init_workspace_partial_exists(self):
        """测试部分文件已存在的情况"""
        # 手动创建部分文件
        workspace_dir = self.root / ".personalmanager"
        workspace_dir.mkdir(parents=True)
        config_file = workspace_dir / "workspace-config.yaml"
        config_file.write_text("existing: true")

        # 初始化工作空间
        report = init_workspace(self.root)
        assert report.success is True
        assert len(report.created_files) == 2  # 只创建缺失的两个文件
        assert len(report.skipped_files) == 1  # 跳过已存在的文件
        assert "workspace-config.yaml" in report.skipped_files[0]

        # 验证已存在的文件未被修改
        with open(config_file, 'r') as f:
            assert f.read() == "existing: true"

    def test_init_workspace_handles_permission_error(self):
        """测试处理权限错误"""
        import os
        import platform

        # 仅在非 Windows 系统测试（Windows 权限模型不同）
        if platform.system() != "Windows":
            # 创建只读目录
            readonly_dir = self.root / "readonly"
            readonly_dir.mkdir()
            os.chmod(readonly_dir, 0o444)

            report = init_workspace(readonly_dir)
            assert report.success is False
            assert len(report.errors) > 0
            assert "无法创建工作空间目录" in report.errors[0]

            # 恢复权限以便清理
            os.chmod(readonly_dir, 0o755)

    def test_init_workspace_report_structure(self):
        """测试报告结构完整性"""
        report = init_workspace(self.root)

        # 验证报告包含所有字段
        assert hasattr(report, 'success')
        assert hasattr(report, 'created_files')
        assert hasattr(report, 'skipped_files')
        assert hasattr(report, 'errors')
        assert hasattr(report, 'timestamp')
        assert hasattr(report, 'force_mode')

        # 验证时间戳格式
        from datetime import datetime
        datetime.fromisoformat(report.timestamp)  # 应该不抛出异常

    def test_init_workspace_file_content_validity(self):
        """测试生成的文件内容有效性"""
        import yaml
        import json

        report = init_workspace(self.root)
        assert report.success is True

        workspace_dir = self.root / ".personalmanager"

        # 测试 YAML 文件
        with open(workspace_dir / "workspace-config.yaml", 'r') as f:
            yaml_content = yaml.safe_load(f)
            assert yaml_content is not None
            assert "workspace" in yaml_content
            assert "startup" in yaml_content
            assert "agents" in yaml_content
            assert "privacy" in yaml_content

        # 测试 JSON 文件
        with open(workspace_dir / "interaction-patterns.json", 'r') as f:
            json_content = json.load(f)
            assert "version" in json_content
            assert "locale" in json_content
            assert "intents" in json_content
            assert isinstance(json_content["intents"], list)

        # 测试 Markdown 文件
        with open(workspace_dir / "ai-agent-definition.md", 'r') as f:
            md_content = f.read()
            assert "身份与角色" in md_content
            assert "工作原则" in md_content
            assert "交互规范" in md_content
            assert "服务边界" in md_content

    def test_init_workspace_nested_path(self):
        """测试嵌套路径创建"""
        nested_path = self.root / "deep" / "nested" / "project"
        report = init_workspace(nested_path)

        assert report.success is True
        assert (nested_path / ".personalmanager").exists()
        assert len(report.created_files) == 3

    def test_init_workspace_relative_paths_in_report(self):
        """测试报告中使用相对路径"""
        report = init_workspace(self.root)

        # 所有路径应该是相对于 root 的
        for path in report.created_files:
            assert not path.startswith('/')
            assert ".personalmanager" in path