"""工作空间校验功能实现"""

import json
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class CheckLevel(Enum):
    """检查级别枚举"""
    OK = "OK"
    WARN = "WARN"
    ERROR = "ERROR"


@dataclass
class ValidationItem:
    """单个校验项结果"""
    check: str  # 检查项名称
    level: CheckLevel  # 级别
    message: str  # 消息
    suggest: Optional[str] = None  # 修复建议

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            "check": self.check,
            "level": self.level.value,
            "message": self.message
        }
        if self.suggest:
            result["suggest"] = self.suggest
        return result


@dataclass
class ValidationReport:
    """校验报告"""
    items: List[ValidationItem] = field(default_factory=list)
    summary: Dict[str, int] = field(default_factory=lambda: {"ok": 0, "warn": 0, "error": 0})

    def add_item(self, item: ValidationItem) -> None:
        """添加校验项"""
        self.items.append(item)
        # 更新统计
        if item.level == CheckLevel.OK:
            self.summary["ok"] += 1
        elif item.level == CheckLevel.WARN:
            self.summary["warn"] += 1
        elif item.level == CheckLevel.ERROR:
            self.summary["error"] += 1

    def is_valid(self) -> bool:
        """判断是否通过校验（无错误）"""
        return self.summary["error"] == 0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "items": [item.to_dict() for item in self.items],
            "summary": self.summary
        }


def validate_workspace(root: Path) -> ValidationReport:
    """
    校验工作空间配置

    Args:
        root: 工作空间根目录

    Returns:
        ValidationReport: 校验报告
    """
    report = ValidationReport()
    root = Path(root)
    workspace_dir = root / ".personalmanager"

    # 检查工作空间目录存在性
    if not workspace_dir.exists():
        report.add_item(ValidationItem(
            check="workspace_directory",
            level=CheckLevel.ERROR,
            message=".personalmanager 目录不存在",
            suggest="运行 init_workspace() 创建工作空间"
        ))
        return report
    else:
        report.add_item(ValidationItem(
            check="workspace_directory",
            level=CheckLevel.OK,
            message=".personalmanager 目录存在"
        ))

    # 三件套文件定义
    files_to_check = {
        "workspace-config.yaml": {
            "type": "yaml",
            "required_fields": ["workspace", "startup", "agents", "privacy"],
            "max_size": 10240  # 10KB
        },
        "ai-agent-definition.md": {
            "type": "markdown",
            "max_size": 20480  # 20KB
        },
        "interaction-patterns.json": {
            "type": "json",
            "required_fields": ["version", "locale", "intents"],
            "max_size": 51200  # 50KB
        }
    }

    # 检查每个文件
    for filename, spec in files_to_check.items():
        filepath = workspace_dir / filename

        # 1. 检查文件存在性
        if not filepath.exists():
            report.add_item(ValidationItem(
                check=f"file_exists_{filename}",
                level=CheckLevel.ERROR,
                message=f"文件不存在: {filename}",
                suggest=f"运行 init_workspace() 创建缺失的文件"
            ))
            continue
        else:
            report.add_item(ValidationItem(
                check=f"file_exists_{filename}",
                level=CheckLevel.OK,
                message=f"文件存在: {filename}"
            ))

        # 2. 检查文件大小
        file_size = filepath.stat().st_size
        max_size = spec.get("max_size", float('inf'))
        if file_size > max_size:
            report.add_item(ValidationItem(
                check=f"file_size_{filename}",
                level=CheckLevel.WARN,
                message=f"文件过大: {filename} ({file_size} > {max_size} bytes)",
                suggest=f"减少文件内容，保持在 {max_size} 字节以内"
            ))
        else:
            report.add_item(ValidationItem(
                check=f"file_size_{filename}",
                level=CheckLevel.OK,
                message=f"文件大小正常: {filename} ({file_size} bytes)"
            ))

        # 3. 检查文件语法和字段
        if spec["type"] == "yaml":
            _validate_yaml_file(filepath, spec.get("required_fields", []), report, filename)
        elif spec["type"] == "json":
            _validate_json_file(filepath, spec.get("required_fields", []), report, filename)
        elif spec["type"] == "markdown":
            _validate_markdown_file(filepath, report, filename)

    # 额外的路径合法性检查
    _validate_paths(workspace_dir, report)

    return report


def _validate_yaml_file(filepath: Path, required_fields: List[str], report: ValidationReport, filename: str) -> None:
    """校验 YAML 文件"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        if data is None:
            report.add_item(ValidationItem(
                check=f"yaml_syntax_{filename}",
                level=CheckLevel.ERROR,
                message=f"YAML 文件为空: {filename}",
                suggest="添加有效的 YAML 内容"
            ))
            return

        report.add_item(ValidationItem(
            check=f"yaml_syntax_{filename}",
            level=CheckLevel.OK,
            message=f"YAML 语法正确: {filename}"
        ))

        # 检查必填字段
        missing_fields = []
        for field in required_fields:
            if field not in data:
                missing_fields.append(field)

        if missing_fields:
            report.add_item(ValidationItem(
                check=f"required_fields_{filename}",
                level=CheckLevel.ERROR,
                message=f"缺少必填字段: {', '.join(missing_fields)}",
                suggest=f"在 {filename} 中添加缺失的字段"
            ))
        else:
            report.add_item(ValidationItem(
                check=f"required_fields_{filename}",
                level=CheckLevel.OK,
                message=f"所有必填字段存在: {filename}"
            ))

        # 特定字段值校验
        if filename == "workspace-config.yaml":
            _validate_workspace_config_values(data, report)

    except yaml.YAMLError as e:
        report.add_item(ValidationItem(
            check=f"yaml_syntax_{filename}",
            level=CheckLevel.ERROR,
            message=f"YAML 语法错误: {str(e)}",
            suggest="修复 YAML 语法错误，确保缩进和格式正确"
        ))
    except Exception as e:
        report.add_item(ValidationItem(
            check=f"yaml_read_{filename}",
            level=CheckLevel.ERROR,
            message=f"无法读取文件: {str(e)}",
            suggest="检查文件权限和编码"
        ))


def _validate_json_file(filepath: Path, required_fields: List[str], report: ValidationReport, filename: str) -> None:
    """校验 JSON 文件"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        report.add_item(ValidationItem(
            check=f"json_syntax_{filename}",
            level=CheckLevel.OK,
            message=f"JSON 语法正确: {filename}"
        ))

        # 检查必填字段
        missing_fields = []
        for field in required_fields:
            if field not in data:
                missing_fields.append(field)

        if missing_fields:
            report.add_item(ValidationItem(
                check=f"required_fields_{filename}",
                level=CheckLevel.ERROR,
                message=f"缺少必填字段: {', '.join(missing_fields)}",
                suggest=f"在 {filename} 中添加缺失的字段"
            ))
        else:
            report.add_item(ValidationItem(
                check=f"required_fields_{filename}",
                level=CheckLevel.OK,
                message=f"所有必填字段存在: {filename}"
            ))

        # 检查 intents 数组
        if filename == "interaction-patterns.json" and "intents" in data:
            intents = data["intents"]
            if not isinstance(intents, list):
                report.add_item(ValidationItem(
                    check="intents_type",
                    level=CheckLevel.ERROR,
                    message="intents 应该是数组类型",
                    suggest="将 intents 字段改为数组"
                ))
            elif len(intents) == 0:
                report.add_item(ValidationItem(
                    check="intents_empty",
                    level=CheckLevel.WARN,
                    message="intents 数组为空",
                    suggest="添加至少一个意图映射规则"
                ))
            else:
                report.add_item(ValidationItem(
                    check="intents_count",
                    level=CheckLevel.OK,
                    message=f"包含 {len(intents)} 个意图映射规则"
                ))

    except json.JSONDecodeError as e:
        report.add_item(ValidationItem(
            check=f"json_syntax_{filename}",
            level=CheckLevel.ERROR,
            message=f"JSON 语法错误: {str(e)}",
            suggest="修复 JSON 语法错误，使用 JSON 验证工具检查"
        ))
    except Exception as e:
        report.add_item(ValidationItem(
            check=f"json_read_{filename}",
            level=CheckLevel.ERROR,
            message=f"无法读取文件: {str(e)}",
            suggest="检查文件权限和编码"
        ))


def _validate_markdown_file(filepath: Path, report: ValidationReport, filename: str) -> None:
    """校验 Markdown 文件"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        if not content.strip():
            report.add_item(ValidationItem(
                check=f"markdown_content_{filename}",
                level=CheckLevel.WARN,
                message=f"Markdown 文件为空: {filename}",
                suggest="添加 AI Agent 定义内容"
            ))
        else:
            # 检查是否包含必要的章节
            required_sections = ["身份与角色", "工作原则", "交互规范", "服务边界"]
            missing_sections = []
            for section in required_sections:
                if f"## {section}" not in content and f"# {section}" not in content:
                    missing_sections.append(section)

            if missing_sections:
                report.add_item(ValidationItem(
                    check=f"markdown_sections_{filename}",
                    level=CheckLevel.WARN,
                    message=f"缺少建议章节: {', '.join(missing_sections)}",
                    suggest="添加缺失的章节以完善 Agent 定义"
                ))
            else:
                report.add_item(ValidationItem(
                    check=f"markdown_sections_{filename}",
                    level=CheckLevel.OK,
                    message=f"包含所有建议章节: {filename}"
                ))

    except Exception as e:
        report.add_item(ValidationItem(
            check=f"markdown_read_{filename}",
            level=CheckLevel.ERROR,
            message=f"无法读取文件: {str(e)}",
            suggest="检查文件权限和编码"
        ))


def _validate_workspace_config_values(data: Dict[str, Any], report: ValidationReport) -> None:
    """校验 workspace-config.yaml 的具体值"""
    # 检查语言设置
    if "workspace" in data:
        workspace = data["workspace"]
        if "language" in workspace:
            lang = workspace["language"]
            if lang not in ["zh", "en"]:
                report.add_item(ValidationItem(
                    check="workspace_language",
                    level=CheckLevel.WARN,
                    message=f"不支持的语言: {lang}",
                    suggest="使用 'zh' 或 'en'"
                ))

    # 检查 Agent 平台设置
    if "agents" in data:
        agents = data["agents"]
        if "preferred" in agents:
            preferred = agents["preferred"]
            if preferred not in ["claude", "gemini"]:
                report.add_item(ValidationItem(
                    check="agent_platform",
                    level=CheckLevel.WARN,
                    message=f"不支持的 Agent 平台: {preferred}",
                    suggest="使用 'claude' 或 'gemini'"
                ))

    # 检查隐私设置
    if "privacy" in data:
        privacy = data["privacy"]
        if "external_calls" in privacy:
            external = privacy["external_calls"]
            if external not in ["user_consent", "deny_all"]:
                report.add_item(ValidationItem(
                    check="privacy_external_calls",
                    level=CheckLevel.WARN,
                    message=f"无效的外部调用策略: {external}",
                    suggest="使用 'user_consent' 或 'deny_all'"
                ))

    # 检查路由阈值
    if "routing" in data:
        routing = data["routing"]
        if "low_confidence_threshold" in routing and "high_confidence_threshold" in routing:
            low = routing["low_confidence_threshold"]
            high = routing["high_confidence_threshold"]
            if not (0 <= low <= 1):
                report.add_item(ValidationItem(
                    check="routing_threshold",
                    level=CheckLevel.ERROR,
                    message=f"低置信度阈值超出范围: {low}",
                    suggest="设置为 0 到 1 之间的值"
                ))
            if not (0 <= high <= 1):
                report.add_item(ValidationItem(
                    check="routing_threshold",
                    level=CheckLevel.ERROR,
                    message=f"高置信度阈值超出范围: {high}",
                    suggest="设置为 0 到 1 之间的值"
                ))
            if low >= high:
                report.add_item(ValidationItem(
                    check="routing_threshold",
                    level=CheckLevel.WARN,
                    message=f"低置信度阈值应小于高置信度阈值",
                    suggest="调整阈值，确保 low < high"
                ))


def _validate_paths(workspace_dir: Path, report: ValidationReport) -> None:
    """校验路径合法性"""
    config_file = workspace_dir / "workspace-config.yaml"
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            if data and "context" in data and "always_load" in data["context"]:
                always_load = data["context"]["always_load"]
                if always_load:
                    for path_str in always_load:
                        path = workspace_dir.parent / path_str
                        if not path.exists():
                            report.add_item(ValidationItem(
                                check="context_path",
                                level=CheckLevel.WARN,
                                message=f"上下文文件不存在: {path_str}",
                                suggest=f"创建文件或从 always_load 中移除"
                            ))
                        elif not path.is_file():
                            report.add_item(ValidationItem(
                                check="context_path",
                                level=CheckLevel.ERROR,
                                message=f"上下文路径不是文件: {path_str}",
                                suggest="只能加载文件，不能加载目录"
                            ))
        except:
            pass  # 如果读取失败，前面的检查已经报告了