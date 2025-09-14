"""Prompt 编译器模块 - 从工作空间配置生成精简的项目级系统提示"""

import json
import yaml
from pathlib import Path
from typing import Optional, List, Dict, Any


def compile_prompt(
    cfg_path: str,
    aid_path: str,
    pat_path: str,
    profile_path: Optional[str] = None
) -> str:
    """
    编译项目级系统提示

    Args:
        cfg_path: workspace-config.yaml 路径
        aid_path: ai-agent-definition.md 路径
        pat_path: interaction-patterns.json 路径
        profile_path: profile.md 路径（可选）

    Returns:
        编译后的系统提示（< 10k 字符）
    """
    sections = []

    # 1. 角色与职责
    role_section = _render_role(aid_path)
    if role_section:
        sections.append(role_section)

    # 2. 启动仪式
    startup_section = _render_startup(cfg_path)
    if startup_section:
        sections.append(startup_section)

    # 3. 自然语言映射规则
    mapping_section = _render_mapping_rules(pat_path, cfg_path)
    if mapping_section:
        sections.append(mapping_section)

    # 4. 错误处理
    error_section = _render_error_handling()
    sections.append(error_section)

    # 5. 隐私与安全
    privacy_section = _render_privacy(cfg_path)
    sections.append(privacy_section)

    # 6. 记忆摘要（可选）
    if profile_path:
        memory_section = _render_memory(profile_path)
        if memory_section:
            sections.append(memory_section)

    # 合并并截断
    return join_and_truncate(sections, limit=10_000)


def join_and_truncate(sections: List[str], limit: int = 10_000) -> str:
    """
    合并段落并截断到指定长度

    Args:
        sections: 段落列表
        limit: 字符限制

    Returns:
        合并后的文本（不超过 limit 字符）
    """
    # 过滤空段落
    sections = [s for s in sections if s and s.strip()]

    # 直接合并
    result = "\n\n".join(sections)

    # 如果超长，优先保留前面的重要段落
    if len(result) > limit:
        # 优先级：角色 > 启动 > 映射 > 错误 > 隐私 > 记忆
        priority_result = []
        current_length = 0

        for section in sections[:3]:  # 优先保留前三个段落
            section_length = len(section)
            if current_length + section_length + 2 < limit:  # +2 for \n\n
                priority_result.append(section)
                current_length += section_length + 2

        # 添加必要的错误和隐私段落（简化版）
        remaining = limit - current_length - 100  # 预留 100 字符
        if remaining > 200:
            priority_result.append(_render_error_handling_brief())
            priority_result.append(_render_privacy_brief())

        result = "\n\n".join(priority_result)

    return result


def _render_role(aid_path: str) -> str:
    """渲染角色与职责段落"""
    try:
        aid_file = Path(aid_path)
        if not aid_file.exists():
            return ""

        content = aid_file.read_text(encoding='utf-8')

        # 提取精简版角色定义（取前 1500 字符）
        lines = []
        lines.append("# PersonalManager Expert — Project Instructions")
        lines.append("")
        lines.append("## 1) 角色与职责")

        # 简化内容
        if len(content) > 1500:
            content = content[:1500] + "..."

        # 提取关键段落
        for line in content.split('\n'):
            if line.strip() and not line.startswith('#'):
                lines.append(f"- {line.strip()}")
            if len('\n'.join(lines)) > 2000:
                break

        return '\n'.join(lines)
    except Exception:
        return ""


def _render_startup(cfg_path: str) -> str:
    """渲染启动仪式段落"""
    try:
        cfg_file = Path(cfg_path)
        if not cfg_file.exists():
            return ""

        with open(cfg_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}

        startup = config.get('startup', {})
        if not startup.get('enabled', False):
            return ""

        lines = []
        lines.append("## 2) 启动仪式")
        lines.append("会话开始时按顺序执行：")

        steps = startup.get('steps', [])
        for i, step in enumerate(steps, 1):
            if step == 'doctor':
                verbose = startup.get('doctor', {}).get('verbose', False)
                cmd = "pm doctor --verbose" if verbose else "pm doctor"
                lines.append(f"{i}. 执行 `{cmd}` - 系统诊断")
            elif step == 'today':
                count = startup.get('today', {}).get('count', 3)
                lines.append(f"{i}. 执行 `pm today --count {count}` - 今日推荐")
            else:
                lines.append(f"{i}. 执行 `{step}`")

        return '\n'.join(lines)
    except Exception:
        return ""


def _render_mapping_rules(pat_path: str, cfg_path: str) -> str:
    """渲染自然语言映射规则段落"""
    try:
        pat_file = Path(pat_path)
        if not pat_file.exists():
            return ""

        with open(pat_file, 'r', encoding='utf-8') as f:
            patterns = json.load(f)

        # 读取路由配置
        routing_config = {}
        try:
            cfg_file = Path(cfg_path)
            if cfg_file.exists():
                with open(cfg_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f) or {}
                    routing_config = config.get('routing', {})
        except Exception:
            pass

        lines = []
        lines.append("## 3) 自然语言→命令映射")
        lines.append("当用户使用自然语言时：")
        lines.append("")

        # 置信度阈值
        low_threshold = routing_config.get('low_confidence_threshold', 0.5)
        high_threshold = routing_config.get('high_confidence_threshold', 0.8)

        lines.append(f"- 置信度 ≥ {high_threshold}: 直接执行")
        lines.append(f"- 置信度 {low_threshold}-{high_threshold}: 先确认")
        lines.append(f"- 置信度 < {low_threshold}: 请求澄清")
        lines.append("")
        lines.append("**核心意图映射：**")

        # 列出前 10 个意图
        intents = patterns.get('intents', [])[:10]
        for intent in intents:
            intent_id = intent.get('id', '')
            desc = intent.get('description', '')
            cmd = intent.get('command', '')
            phrases = intent.get('phrases', [])[:3]  # 最多3个示例短语

            lines.append(f"- `{intent_id}`: {desc}")
            if phrases:
                lines.append(f"  短语: {', '.join(phrases)}")
            lines.append(f"  命令: `{cmd}`")

        return '\n'.join(lines)
    except Exception:
        return ""


def _render_error_handling() -> str:
    """渲染错误处理段落"""
    lines = []
    lines.append("## 4) 错误处理与降级")
    lines.append("- E1xxx: 配置错误 → 引导运行 `pm setup`")
    lines.append("- E2xxx: 权限错误 → 检查文件权限")
    lines.append("- E3xxx: 数据错误 → 验证输入格式")
    lines.append("- E4xxx: 集成错误 → 检查外部服务")
    lines.append("- 未知错误 → 提供错误码并建议查看日志")
    return '\n'.join(lines)


def _render_error_handling_brief() -> str:
    """渲染简化版错误处理段落"""
    return "## 4) 错误处理\n统一错误码: E1xxx-E4xxx，提供修复建议"


def _render_privacy(cfg_path: str) -> str:
    """渲染隐私与安全段落"""
    try:
        cfg_file = Path(cfg_path)
        privacy_config = {}

        if cfg_file.exists():
            with open(cfg_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
                privacy_config = config.get('privacy', {})

        lines = []
        lines.append("## 5) 隐私与安全")

        external_calls = privacy_config.get('external_calls', 'user_consent')
        data_retention = privacy_config.get('data_retention', 'session_only')
        redact_logs = privacy_config.get('redact_logs', True)

        lines.append(f"- 外部调用策略: {external_calls}")
        lines.append(f"- 数据保留: {data_retention}")
        lines.append(f"- 日志脱敏: {'启用' if redact_logs else '禁用'}")
        lines.append("- 所有数据本地存储，不上传云端")
        lines.append("- 敏感操作需用户确认")

        return '\n'.join(lines)
    except Exception:
        return _render_privacy_brief()


def _render_privacy_brief() -> str:
    """渲染简化版隐私段落"""
    return "## 5) 隐私与安全\n本地存储，需用户同意，日志脱敏"


def _render_memory(profile_path: str) -> str:
    """渲染记忆摘要段落"""
    try:
        profile_file = Path(profile_path)
        if not profile_file.exists():
            return ""

        content = profile_file.read_text(encoding='utf-8')
        lines = content.strip().split('\n')[:5]  # 最多5行

        if not lines:
            return ""

        result = []
        result.append("## 6) 用户偏好摘要")
        for line in lines:
            if line.strip():
                result.append(f"- {line.strip()}")

        return '\n'.join(result)
    except Exception:
        return ""