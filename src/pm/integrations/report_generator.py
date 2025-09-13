"""AI驱动的项目报告生成器 - Sprint 11-12核心功能

实现通用项目分析与报告Prompt模板系统，自动生成PROJECT_STATUS.md
"""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import structlog

from pm.core.config import PMConfig
from pm.integrations.ai_service import UnifiedAIService, AIServiceError

logger = structlog.get_logger()


class ProjectConfig:
    """项目配置管理"""
    
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.config_file = project_path / ".pm-config.yaml"
        self.config_data = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载项目配置文件"""
        if not self.config_file.exists():
            logger.warning("Project config not found, using defaults", 
                         project_path=str(self.project_path))
            return self._get_default_config()
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
            logger.info("Project config loaded", config_file=str(self.config_file))
            return config
        except Exception as e:
            logger.error("Failed to load project config", error=str(e))
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认项目配置"""
        return {
            "report_generation": {
                "plan_documents": [
                    "GOALS.md",
                    "OUTLINE.md", 
                    "README.md",
                    "PLAN.md"
                ],
                "work_documents": [
                    "*.md",
                    "docs/*.md",
                    "chapters/*.md",
                    "src/**/*.py",
                    "progress/*.md"
                ]
            }
        }
    
    def get_plan_documents(self) -> List[str]:
        """获取计划文档模式列表"""
        return self.config_data.get("report_generation", {}).get("plan_documents", [])
    
    def get_work_documents(self) -> List[str]:
        """获取工作成果文档模式列表"""
        return self.config_data.get("report_generation", {}).get("work_documents", [])


class DocumentReader:
    """文档读取器"""
    
    def __init__(self, project_path: Path):
        self.project_path = project_path
    
    def read_documents(self, patterns: List[str]) -> Dict[str, str]:
        """读取匹配模式的文档"""
        documents = {}
        
        for pattern in patterns:
            files = self._find_files_by_pattern(pattern)
            for file_path in files:
                try:
                    content = self._read_file_safely(file_path)
                    if content:
                        relative_path = str(file_path.relative_to(self.project_path))
                        documents[relative_path] = content
                        logger.debug("Document read", file=relative_path, 
                                   length=len(content))
                except Exception as e:
                    logger.warning("Failed to read document", 
                                 file=str(file_path), error=str(e))
        
        logger.info("Documents read", count=len(documents))
        return documents
    
    def _find_files_by_pattern(self, pattern: str) -> List[Path]:
        """根据模式查找文件"""
        from glob import glob
        import fnmatch
        
        files = []
        
        # 如果是绝对路径模式，直接使用
        if "/" in pattern or "*" in pattern:
            # 处理glob模式
            abs_pattern = str(self.project_path / pattern)
            matched_files = glob(abs_pattern, recursive=True)
            files.extend([Path(f) for f in matched_files if Path(f).is_file()])
        else:
            # 处理简单文件名
            target_file = self.project_path / pattern
            if target_file.exists() and target_file.is_file():
                files.append(target_file)
        
        return files
    
    def _read_file_safely(self, file_path: Path) -> Optional[str]:
        """安全地读取文件"""
        try:
            # 跳过二进制文件和过大的文件
            if file_path.stat().st_size > 1024 * 1024:  # 1MB限制
                logger.warning("File too large, skipping", file=str(file_path))
                return None
            
            # 尝试以文本模式读取
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 过滤掉空文件
            if not content.strip():
                return None
            
            return content
        except UnicodeDecodeError:
            logger.debug("File appears to be binary, skipping", file=str(file_path))
            return None
        except Exception as e:
            logger.warning("Error reading file", file=str(file_path), error=str(e))
            return None


class PromptTemplate:
    """通用项目分析与报告Prompt模板"""
    
    UNIVERSAL_PROMPT_TEMPLATE = '''### 角色与目标 (Role & Goal)

你是一位顶级的AI项目分析师和进展评估专家。你的任务是深入理解和对比我提供的"目标计划"和"工作成果"两类文档，然后基于你的分析，撰写一份专业、准确、结构化的 `PROJECT_STATUS.md` 项目状态报告。

这份报告需要给我的另一个自动化工具进行解析，所以格式的准确性至关重要。

### 输出格式要求 (Output Format Requirements)

你生成的报告必须严格遵循以下结构和关键词：

1. **项目名称**: 使用一级标题 `# Project Name`。
2. **核心指标**: 必须包含以下格式的行：
   * `Progress: [数字]%`
   * `Health: [Excellent, Good, Warning, Critical]`  
   * `Priority: [High, Medium, Low]`
   * `Last Updated: [YYYY-MM-DD]`
3. **列表式内容**: 必须包含以下二级标题，并在标题下使用 `-` 或 `*` 创建无序列表：
   * `## Completed Work` (已完成工作)
   * `## Next Actions` (下一步行动)
   * `## Risks` (风险与问题)

### 输入信息 (Input Information)

这是你需要分析的所有上下文信息：

#### 1. 项目高级背景
* **[必填] 项目的最终目标是什么？**
  * {project_goal}

#### 2. 规划与目标文档
* **[必填] 这是评估进度的基准。请粘贴项目的主要规划、大纲、需求或目标文档的内容。**
```
{plan_documents}
```

#### 3. 工作成果与现状文档
* **[必填] 这是你的分析对象。请粘贴体现你最新工作成果的文档内容。**
```
{work_documents}
```

#### 4. [可选] 旧的状态报告
* **[如果存在旧的 `PROJECT_STATUS.md`，由Agent动态填入。]**
```
{previous_report}
```

### 分析与生成指令 (Analysis & Generation Instructions)

1. **对比分析**: 深入理解"规划与目标文档"，并将其与"工作成果与现状文档"进行对比。识别出从计划到现状的关键进展和偏差。
2. **提炼已完成工作**: 基于上述对比分析，用人类可读的语言，**从成果的角度**总结出已完成的核心工作。
3. **推断下一步行动**: 根据"规划与目标文档"中尚未完成的部分，以及当前已完成的工作，推断出最合乎逻辑的"下一步行动"。
4. **评估项目状态**:
   * **进度(Progress)**: 根据"工作成果"在"总体规划"中所占的比重，估算一个总体进度百分比。
   * **健康度(Health)**: 评估进展是否顺利。如果实际成果与计划有偏差或出现新的障碍，可以标记为`Warning`。
5. **生成报告**: 将以上所有你分析、提炼和推断出的信息，严格按照"输出格式要求"生成一份完整的 `PROJECT_STATUS.md` 报告。
6. **直接输出**: 请直接输出完整的Markdown文件内容，不要包含任何额外的解释或对话。'''

    @classmethod
    def generate_prompt(
        cls,
        project_name: str,
        project_goal: str,
        plan_documents: Dict[str, str],
        work_documents: Dict[str, str],
        previous_report: Optional[str] = None
    ) -> str:
        """生成完整的分析Prompt"""
        
        # 组装计划文档
        plan_content = cls._format_documents(plan_documents, "规划与目标文档")
        
        # 组装工作成果文档
        work_content = cls._format_documents(work_documents, "工作成果文档")
        
        # 处理之前的报告
        prev_report = previous_report if previous_report else "无之前报告"
        
        # 生成完整Prompt
        prompt = cls.UNIVERSAL_PROMPT_TEMPLATE.format(
            project_goal=project_goal,
            plan_documents=plan_content,
            work_documents=work_content,
            previous_report=prev_report
        )
        
        logger.info("Prompt generated", 
                   project_name=project_name,
                   plan_docs_count=len(plan_documents),
                   work_docs_count=len(work_documents),
                   prompt_length=len(prompt))
        
        return prompt
    
    @classmethod
    def _format_documents(cls, documents: Dict[str, str], category: str) -> str:
        """格式化文档内容"""
        if not documents:
            return f"无{category}找到"
        
        formatted = []
        for file_path, content in documents.items():
            formatted.append(f"=== {file_path} ===")
            formatted.append(content)
            formatted.append("")  # 空行分隔
        
        return "\n".join(formatted)


class ReportGenerator:
    """AI驱动的报告生成器"""
    
    def __init__(self, config: PMConfig):
        self.config = config
        self.ai_service = UnifiedAIService(config)
    
    def generate_report(
        self, 
        project_path: str, 
        project_name: Optional[str] = None
    ) -> Tuple[bool, str]:
        """生成项目状态报告
        
        Args:
            project_path: 项目路径
            project_name: 项目名称（可选，会自动推断）
            
        Returns:
            Tuple[成功标志, 消息或错误信息]
        """
        
        try:
            project_dir = Path(project_path).resolve()
            if not project_dir.exists() or not project_dir.is_dir():
                return False, f"项目路径不存在或不是目录: {project_path}"
            
            # 自动推断项目名称
            if not project_name:
                project_name = project_dir.name
            
            logger.info("Starting report generation", 
                       project_name=project_name,
                       project_path=str(project_dir))
            
            # 1. 加载项目配置
            project_config = ProjectConfig(project_dir)
            
            # 2. 读取相关文档
            doc_reader = DocumentReader(project_dir)
            
            plan_patterns = project_config.get_plan_documents()
            work_patterns = project_config.get_work_documents()
            
            plan_documents = doc_reader.read_documents(plan_patterns)
            work_documents = doc_reader.read_documents(work_patterns)
            
            if not plan_documents and not work_documents:
                return False, "未找到任何项目文档，请检查项目配置和文档结构"
            
            # 3. 读取之前的报告（如果存在）
            status_file = project_dir / "PROJECT_STATUS.md"
            previous_report = None
            if status_file.exists():
                try:
                    with open(status_file, 'r', encoding='utf-8') as f:
                        previous_report = f.read()
                    logger.info("Previous report found", length=len(previous_report))
                except Exception as e:
                    logger.warning("Failed to read previous report", error=str(e))
            
            # 4. 推断项目目标
            project_goal = self._infer_project_goal(project_name, plan_documents)
            
            # 5. 生成AI分析Prompt
            prompt = PromptTemplate.generate_prompt(
                project_name=project_name,
                project_goal=project_goal,
                plan_documents=plan_documents,
                work_documents=work_documents,
                previous_report=previous_report
            )
            
            # 6. 调用AI生成报告
            logger.info("Calling AI service for report generation")
            report_content = self.ai_service.generate_text(
                prompt=prompt,
                max_tokens=4000,
                temperature=0.1
            )
            
            # 7. 保存报告到文件
            try:
                with open(status_file, 'w', encoding='utf-8') as f:
                    f.write(report_content)
                
                logger.info("Report generated successfully", 
                           output_file=str(status_file),
                           report_length=len(report_content))
                
                return True, f"项目报告已生成: {status_file}"
                
            except Exception as e:
                error_msg = f"保存报告文件时出错: {str(e)}"
                logger.error("Failed to save report", error=str(e))
                return False, error_msg
                
        except AIServiceError as e:
            error_msg = f"AI服务调用失败: {str(e)}"
            logger.error("AI service error", error=str(e))
            return False, error_msg
        except Exception as e:
            error_msg = f"生成报告时发生未知错误: {str(e)}"
            logger.error("Unexpected error in report generation", error=str(e))
            return False, error_msg
    
    def _infer_project_goal(self, project_name: str, plan_documents: Dict[str, str]) -> str:
        """推断项目目标"""
        
        # 尝试从计划文档中提取目标信息
        goal_hints = []
        
        for file_path, content in plan_documents.items():
            # 查找目标相关的段落
            lines = content.split('\n')
            for i, line in enumerate(lines):
                lower_line = line.lower()
                if any(keyword in lower_line for keyword in ['目标', 'goal', '目的', 'purpose', '愿景', 'vision']):
                    # 收集相关段落
                    context_lines = lines[max(0, i-1):min(len(lines), i+3)]
                    goal_hints.append(' '.join(context_lines))
        
        if goal_hints:
            return f"{project_name}项目 - " + "; ".join(goal_hints[:2])  # 最多取前2个线索
        else:
            return f"开发和完善{project_name}项目，实现预定的功能和目标"