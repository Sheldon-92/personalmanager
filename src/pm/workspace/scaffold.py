"""工作空间脚手架功能实现"""

import shutil
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ScaffoldReport:
    """脚手架操作报告"""
    success: bool
    created_files: List[str] = field(default_factory=list)
    skipped_files: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    force_mode: bool = False

    def add_created(self, filepath: str) -> None:
        """添加已创建文件"""
        self.created_files.append(filepath)

    def add_skipped(self, filepath: str) -> None:
        """添加已跳过文件"""
        self.skipped_files.append(filepath)

    def add_error(self, error: str) -> None:
        """添加错误信息"""
        self.errors.append(error)
        self.success = False


def init_workspace(root: Path, force: bool = False) -> ScaffoldReport:
    """
    初始化工作空间，生成三件套配置文件

    Args:
        root: 工作空间根目录
        force: 是否强制覆盖已存在的文件

    Returns:
        ScaffoldReport: 脚手架操作报告
    """
    report = ScaffoldReport(success=True, force_mode=force)

    # 确保 root 是 Path 对象
    root = Path(root)

    # 创建 .personalmanager 目录
    workspace_dir = root / ".personalmanager"
    try:
        workspace_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        report.add_error(f"无法创建工作空间目录: {str(e)}")
        return report

    # 模板文件映射
    template_dir = Path(__file__).parent / "templates"
    files_to_create = {
        "workspace-config.yaml": workspace_dir / "workspace-config.yaml",
        "ai-agent-definition.md": workspace_dir / "ai-agent-definition.md",
        "interaction-patterns.json": workspace_dir / "interaction-patterns.json"
    }

    # 处理每个文件
    for template_name, target_path in files_to_create.items():
        template_path = template_dir / template_name

        # 检查模板文件是否存在
        if not template_path.exists():
            report.add_error(f"模板文件不存在: {template_path}")
            continue

        # 检查目标文件是否已存在
        if target_path.exists() and not force:
            report.add_skipped(str(target_path.relative_to(root)))
            continue

        # 复制文件
        try:
            shutil.copy2(template_path, target_path)
            report.add_created(str(target_path.relative_to(root)))
        except Exception as e:
            report.add_error(f"复制文件失败 {template_name}: {str(e)}")

    # 如果没有错误且至少创建了一个文件，则成功
    if not report.errors and (report.created_files or report.skipped_files):
        report.success = True
    elif not report.errors and not report.created_files and report.skipped_files:
        # 所有文件都已存在（跳过），这也算成功
        report.success = True

    return report