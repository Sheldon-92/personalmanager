"""功能自发现和注册系统 - 支持PersonalManager自进化能力

自动发现和跟踪PersonalManager的所有功能，包括CLI命令、集成模块、API方法等
"""

import os
import json
import ast
import inspect
import importlib
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import structlog

logger = structlog.get_logger()


class FunctionRegistry:
    """PersonalManager功能注册表 - 自动发现和管理所有功能"""

    def __init__(self, config=None):
        self.config = config
        self.registry_file = Path.home() / ".personalmanager" / "session" / "function_registry.json"
        self.src_path = Path(__file__).parent.parent.parent  # pm/src 目录
        self.pm_path = self.src_path / "pm"
        self._registry_cache = None

    def discover_all_capabilities(self) -> Dict[str, Any]:
        """全面发现PersonalManager的所有能力"""

        logger.info("Starting comprehensive capability discovery")

        capabilities = {
            "discovery_timestamp": datetime.now().isoformat(),
            "cli_commands": self._discover_cli_commands(),
            "integrations": self._discover_integrations(),
            "api_methods": self._discover_api_methods(),
            "models": self._discover_models(),
            "agents": self._discover_agents(),
            "version_info": self._get_version_info()
        }

        # 保存到注册表文件
        self._save_registry(capabilities)

        logger.info("Capability discovery completed",
                   cli_commands=len(capabilities["cli_commands"]),
                   integrations=len(capabilities["integrations"]),
                   api_methods=len(capabilities["api_methods"]))

        return capabilities

    def _discover_cli_commands(self) -> Dict[str, Any]:
        """发现所有CLI命令"""

        commands = {}
        cli_path = self.pm_path / "cli"

        if not cli_path.exists():
            return commands

        try:
            # 扫描CLI commands目录
            for py_file in cli_path.rglob("*.py"):
                if py_file.name.startswith("__"):
                    continue

                module_name = self._get_module_name(py_file, "pm.cli")
                try:
                    module = importlib.import_module(module_name)
                    commands.update(self._extract_cli_functions(module, py_file))
                except Exception as e:
                    logger.warning(f"Failed to import CLI module",
                                 module=module_name, error=str(e))

        except Exception as e:
            logger.error("Error discovering CLI commands", error=str(e))

        return commands

    def _discover_integrations(self) -> Dict[str, Any]:
        """发现所有集成模块"""

        integrations = {}
        integrations_path = self.pm_path / "integrations"

        if not integrations_path.exists():
            return integrations

        try:
            for py_file in integrations_path.glob("*.py"):
                if py_file.name.startswith("__"):
                    continue

                module_name = f"pm.integrations.{py_file.stem}"
                try:
                    module = importlib.import_module(module_name)
                    integration_info = self._extract_integration_info(module, py_file)
                    if integration_info:
                        integrations[py_file.stem] = integration_info
                except Exception as e:
                    logger.warning(f"Failed to analyze integration",
                                 module=module_name, error=str(e))

        except Exception as e:
            logger.error("Error discovering integrations", error=str(e))

        return integrations

    def _discover_api_methods(self) -> Dict[str, Any]:
        """发现所有API方法"""

        api_methods = {}

        # 扫描所有模块的公共方法
        for py_file in self.pm_path.rglob("*.py"):
            if py_file.name.startswith("__"):
                continue

            try:
                module_name = self._get_module_name(py_file, "pm")
                module = importlib.import_module(module_name)
                methods = self._extract_public_methods(module, py_file)
                if methods:
                    api_methods[module_name] = methods
            except Exception as e:
                logger.debug(f"Skipped module analysis",
                           module=py_file.stem, error=str(e))

        return api_methods

    def _discover_models(self) -> Dict[str, Any]:
        """发现所有数据模型"""

        models = {}
        models_path = self.pm_path / "models"

        if not models_path.exists():
            return models

        for py_file in models_path.glob("*.py"):
            if py_file.name.startswith("__"):
                continue

            try:
                module_name = f"pm.models.{py_file.stem}"
                module = importlib.import_module(module_name)
                model_classes = self._extract_model_classes(module)
                if model_classes:
                    models[py_file.stem] = model_classes
            except Exception as e:
                logger.warning(f"Failed to analyze model",
                             module=py_file.stem, error=str(e))

        return models

    def _discover_agents(self) -> Dict[str, Any]:
        """发现所有智能代理"""

        agents = {}
        agents_path = self.pm_path / "agents"

        if not agents_path.exists():
            return agents

        for py_file in agents_path.glob("*.py"):
            if py_file.name.startswith("__"):
                continue

            try:
                module_name = f"pm.agents.{py_file.stem}"
                module = importlib.import_module(module_name)
                agent_classes = self._extract_agent_classes(module)
                if agent_classes:
                    agents[py_file.stem] = agent_classes
            except Exception as e:
                logger.warning(f"Failed to analyze agent",
                             module=py_file.stem, error=str(e))

        return agents

    def _extract_cli_functions(self, module, file_path) -> Dict[str, Any]:
        """提取CLI函数信息"""

        functions = {}

        for name in dir(module):
            obj = getattr(module, name)
            if callable(obj) and not name.startswith("_"):
                try:
                    sig = inspect.signature(obj)
                    doc = inspect.getdoc(obj) or ""

                    functions[name] = {
                        "name": name,
                        "signature": str(sig),
                        "description": doc.split('\n')[0] if doc else "",
                        "full_doc": doc,
                        "module": str(file_path.relative_to(self.src_path)),
                        "type": "cli_function"
                    }
                except Exception:
                    continue

        return functions

    def _extract_integration_info(self, module, file_path) -> Optional[Dict[str, Any]]:
        """提取集成模块信息"""

        try:
            doc = inspect.getdoc(module) or ""

            # 查找主要的集成类
            main_classes = []
            for name in dir(module):
                obj = getattr(module, name)
                if (inspect.isclass(obj) and
                    not name.startswith("_") and
                    obj.__module__ == module.__name__):

                    class_info = {
                        "name": name,
                        "description": inspect.getdoc(obj) or "",
                        "methods": self._extract_class_methods(obj)
                    }
                    main_classes.append(class_info)

            return {
                "module_name": module.__name__,
                "description": doc.split('\n')[0] if doc else "",
                "full_doc": doc,
                "file_path": str(file_path.relative_to(self.src_path)),
                "main_classes": main_classes,
                "type": "integration"
            }
        except Exception:
            return None

    def _extract_public_methods(self, module, file_path) -> List[Dict[str, Any]]:
        """提取模块的公共方法"""

        methods = []

        for name in dir(module):
            if name.startswith("_"):
                continue

            obj = getattr(module, name)
            if callable(obj):
                try:
                    methods.append({
                        "name": name,
                        "signature": str(inspect.signature(obj)),
                        "description": (inspect.getdoc(obj) or "").split('\n')[0],
                        "type": "function"
                    })
                except Exception:
                    continue

        return methods

    def _extract_class_methods(self, cls) -> List[Dict[str, Any]]:
        """提取类的方法信息"""

        methods = []

        for name in dir(cls):
            if name.startswith("_") and name not in ["__init__"]:
                continue

            method = getattr(cls, name)
            if callable(method):
                try:
                    methods.append({
                        "name": name,
                        "signature": str(inspect.signature(method)),
                        "description": (inspect.getdoc(method) or "").split('\n')[0]
                    })
                except Exception:
                    continue

        return methods

    def _extract_model_classes(self, module) -> List[Dict[str, Any]]:
        """提取数据模型类"""

        models = []

        for name in dir(module):
            obj = getattr(module, name)
            if (inspect.isclass(obj) and
                not name.startswith("_") and
                obj.__module__ == module.__name__):

                models.append({
                    "name": name,
                    "description": inspect.getdoc(obj) or "",
                    "attributes": self._extract_class_attributes(obj)
                })

        return models

    def _extract_agent_classes(self, module) -> List[Dict[str, Any]]:
        """提取智能代理类"""

        agents = []

        for name in dir(module):
            obj = getattr(module, name)
            if (inspect.isclass(obj) and
                not name.startswith("_") and
                obj.__module__ == module.__name__ and
                "agent" in name.lower()):

                agents.append({
                    "name": name,
                    "description": inspect.getdoc(obj) or "",
                    "methods": self._extract_class_methods(obj)
                })

        return agents

    def _extract_class_attributes(self, cls) -> List[str]:
        """提取类属性"""

        attributes = []

        # 尝试从__init__方法提取属性
        try:
            init_method = getattr(cls, "__init__", None)
            if init_method:
                source = inspect.getsource(init_method)
                # 简单解析self.attribute = value模式
                import re
                matches = re.findall(r'self\.(\w+)\s*=', source)
                attributes.extend(matches)
        except Exception:
            pass

        return list(set(attributes))

    def _get_module_name(self, file_path: Path, base_package: str) -> str:
        """获取模块名"""

        relative_path = file_path.relative_to(self.src_path)
        module_parts = list(relative_path.parts[:-1]) + [relative_path.stem]
        return ".".join(module_parts)

    def _get_version_info(self) -> Dict[str, str]:
        """获取版本信息"""

        try:
            # 尝试获取git信息
            git_hash = subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                cwd=self.src_path.parent,
                stderr=subprocess.DEVNULL
            ).decode().strip()

            git_branch = subprocess.check_output(
                ["git", "branch", "--show-current"],
                cwd=self.src_path.parent,
                stderr=subprocess.DEVNULL
            ).decode().strip()

            return {
                "git_hash": git_hash[:8],
                "git_branch": git_branch,
                "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}"
            }
        except Exception:
            return {
                "git_hash": "unknown",
                "git_branch": "unknown",
                "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}"
            }

    def _save_registry(self, capabilities: Dict[str, Any]) -> None:
        """保存功能注册表"""

        try:
            self.registry_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.registry_file, 'w', encoding='utf-8') as f:
                json.dump(capabilities, f, indent=2, ensure_ascii=False)

            self._registry_cache = capabilities
            logger.info("Function registry saved", file=str(self.registry_file))

        except Exception as e:
            logger.error("Failed to save function registry", error=str(e))

    def load_registry(self) -> Optional[Dict[str, Any]]:
        """加载功能注册表"""

        if self._registry_cache:
            return self._registry_cache

        try:
            if self.registry_file.exists():
                with open(self.registry_file, 'r', encoding='utf-8') as f:
                    self._registry_cache = json.load(f)
                return self._registry_cache
        except Exception as e:
            logger.error("Failed to load function registry", error=str(e))

        return None

    def get_capability_summary(self) -> Dict[str, int]:
        """获取能力摘要统计"""

        registry = self.load_registry()
        if not registry:
            return {}

        return {
            "cli_commands": len(registry.get("cli_commands", {})),
            "integrations": len(registry.get("integrations", {})),
            "api_methods": sum(len(methods) for methods in registry.get("api_methods", {}).values()),
            "models": sum(len(models) for models in registry.get("models", {}).values()),
            "agents": sum(len(agents) for agents in registry.get("agents", {}).values()),
            "last_updated": registry.get("discovery_timestamp", "unknown")
        }

    def detect_new_capabilities(self, previous_registry: Optional[Dict[str, Any]] = None) -> Dict[str, List[str]]:
        """检测新增的功能"""

        current = self.load_registry()
        if not current:
            return {}

        if not previous_registry:
            return {"message": "首次功能发现，无法比较变更"}

        new_capabilities = {
            "new_cli_commands": [],
            "new_integrations": [],
            "new_api_methods": [],
            "new_models": [],
            "new_agents": []
        }

        # 比较CLI命令
        current_cli = set(current.get("cli_commands", {}).keys())
        previous_cli = set(previous_registry.get("cli_commands", {}).keys())
        new_capabilities["new_cli_commands"] = list(current_cli - previous_cli)

        # 比较集成模块
        current_integrations = set(current.get("integrations", {}).keys())
        previous_integrations = set(previous_registry.get("integrations", {}).keys())
        new_capabilities["new_integrations"] = list(current_integrations - previous_integrations)

        # 比较其他功能...

        return new_capabilities