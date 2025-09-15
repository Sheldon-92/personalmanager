"""
Plugin SDK for Personal Manager v1.0.0 GA

Features:
- Enhanced RBAC with fine-grained permission control
- Secure sandboxing with path/network/environment whitelisting
- Version negotiation mechanism
- Resource leak detection
- Complete audit logging
- Isolation and capability-based security
"""

__version__ = "1.0.0"
__status__ = "GA"

import abc
import asyncio
import contextlib
import functools
import hashlib
import inspect
import json
import logging
import os
import re
import resource
import signal
import sys
import tempfile
import threading
import time
import traceback
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Type, Union
from datetime import datetime, timedelta
import importlib.util
import importlib.machinery

logger = logging.getLogger(__name__)

# Version compatibility
SDK_VERSION = "1.0.0"
MIN_SUPPORTED_VERSION = "0.9.0"
MAX_SUPPORTED_VERSION = "1.1.0"


class SecurityLevel(Enum):
    """Security levels for plugin operation"""
    MINIMAL = "minimal"      # Basic sandboxing
    STANDARD = "standard"    # Default RBAC + sandboxing
    STRICT = "strict"        # Full isolation + audit
    PARANOID = "paranoid"    # Maximum restrictions


class PluginCapability(Enum):
    """Fine-grained plugin capabilities"""
    # File System
    FS_READ_USER = "fs.read.user"          # Read user data
    FS_READ_SYSTEM = "fs.read.system"      # Read system files
    FS_WRITE_USER = "fs.write.user"        # Write user data
    FS_WRITE_SYSTEM = "fs.write.system"    # Write system files
    FS_DELETE = "fs.delete"                # Delete files
    FS_EXECUTE = "fs.execute"              # Execute files

    # Network
    NET_HTTP = "net.http"                  # HTTP/HTTPS access
    NET_SOCKET = "net.socket"              # Raw socket access
    NET_LOCALHOST = "net.localhost"        # Local network only

    # System
    SYS_PROCESS = "sys.process"            # Process management
    SYS_ENVIRONMENT = "sys.environment"    # Environment variables
    SYS_RESOURCE = "sys.resource"          # System resources

    # Data
    DATA_READ = "data.read"                # Read app data
    DATA_WRITE = "data.write"              # Write app data
    DATA_EXPORT = "data.export"            # Export data
    DATA_IMPORT = "data.import"            # Import data

    # API
    API_INTERNAL = "api.internal"          # Internal API access
    API_EXTERNAL = "api.external"          # External API access
    API_ADMIN = "api.admin"                # Admin API access

    # Hooks
    HOOK_SYSTEM = "hook.system"            # System hooks
    HOOK_DATA = "hook.data"                # Data hooks
    HOOK_UI = "hook.ui"                    # UI hooks


class ResourceType(Enum):
    """Types of resources monitored"""
    MEMORY = auto()
    CPU = auto()
    FILE_HANDLES = auto()
    NETWORK_CONNECTIONS = auto()
    THREADS = auto()


@dataclass
class ResourceLimit:
    """Resource limits for plugins"""
    max_memory_mb: int = 100
    max_cpu_percent: float = 25.0
    max_file_handles: int = 50
    max_network_connections: int = 10
    max_threads: int = 5
    max_execution_time_seconds: int = 60


@dataclass
class PathWhitelist:
    """Whitelisted paths for file system access"""
    read_paths: Set[Path] = field(default_factory=set)
    write_paths: Set[Path] = field(default_factory=set)

    def can_read(self, path: Path) -> bool:
        """Check if path is readable"""
        path = path.resolve()
        for allowed in self.read_paths:
            allowed = allowed.resolve()
            try:
                # Check if path is under allowed directory or is the allowed directory
                if path == allowed or path.is_relative_to(allowed):
                    return True
            except ValueError:
                # is_relative_to can raise ValueError in some cases
                continue
        return False

    def can_write(self, path: Path) -> bool:
        """Check if path is writable"""
        path = path.resolve()
        for allowed in self.write_paths:
            allowed = allowed.resolve()
            try:
                # Check if path is under allowed directory or is the allowed directory
                if path == allowed or path.is_relative_to(allowed):
                    return True
            except ValueError:
                # is_relative_to can raise ValueError in some cases
                continue
        return False


@dataclass
class NetworkWhitelist:
    """Whitelisted network endpoints"""
    allowed_hosts: Set[str] = field(default_factory=set)
    allowed_ports: Set[int] = field(default_factory=set)
    allow_localhost: bool = False

    def can_connect(self, host: str, port: int) -> bool:
        """Check if connection is allowed"""
        if self.allow_localhost and host in ['localhost', '127.0.0.1', '::1']:
            return True
        return host in self.allowed_hosts and port in self.allowed_ports


@dataclass
class EnvironmentWhitelist:
    """Whitelisted environment variables"""
    readable_vars: Set[str] = field(default_factory=set)
    writable_vars: Set[str] = field(default_factory=set)

    def can_read(self, var: str) -> bool:
        """Check if variable is readable"""
        return var in self.readable_vars

    def can_write(self, var: str) -> bool:
        """Check if variable is writable"""
        return var in self.writable_vars


@dataclass
class AuditEntry:
    """Audit log entry"""
    timestamp: datetime
    plugin_name: str
    action: str
    resource: str
    result: str
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "plugin_name": self.plugin_name,
            "action": self.action,
            "resource": self.resource,
            "result": self.result,
            "details": self.details
        }


class ResourceMonitor:
    """Monitors and enforces resource limits"""

    def __init__(self, plugin_name: str, limits: ResourceLimit):
        self.plugin_name = plugin_name
        self.limits = limits
        self.start_time = time.time()
        self.start_resources = self._get_current_resources()
        self.violations: List[Dict[str, Any]] = []
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None

    def _get_current_resources(self) -> Dict[str, Any]:
        """Get current resource usage"""
        try:
            import psutil
            process = psutil.Process()
            return {
                "memory_mb": process.memory_info().rss / 1024 / 1024,
                "cpu_percent": process.cpu_percent(),
                "num_fds": process.num_fds() if hasattr(process, 'num_fds') else 0,
                "num_threads": process.num_threads(),
                "connections": len(process.connections())
            }
        except ImportError:
            # Fallback if psutil not available
            return {
                "memory_mb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024,
                "cpu_percent": 0,
                "num_fds": 0,
                "num_threads": threading.active_count(),
                "connections": 0
            }

    def check_limits(self) -> Tuple[bool, List[str]]:
        """Check if resource limits are exceeded"""
        violations = []
        current = self._get_current_resources()

        # Memory check
        if current["memory_mb"] > self.limits.max_memory_mb:
            violations.append(f"Memory usage {current['memory_mb']:.1f}MB exceeds limit {self.limits.max_memory_mb}MB")

        # CPU check
        if current["cpu_percent"] > self.limits.max_cpu_percent:
            violations.append(f"CPU usage {current['cpu_percent']:.1f}% exceeds limit {self.limits.max_cpu_percent}%")

        # File handles check
        if current["num_fds"] > self.limits.max_file_handles:
            violations.append(f"Open file handles {current['num_fds']} exceeds limit {self.limits.max_file_handles}")

        # Thread check
        if current["num_threads"] > self.limits.max_threads:
            violations.append(f"Thread count {current['num_threads']} exceeds limit {self.limits.max_threads}")

        # Execution time check
        elapsed = time.time() - self.start_time
        if elapsed > self.limits.max_execution_time_seconds:
            violations.append(f"Execution time {elapsed:.1f}s exceeds limit {self.limits.max_execution_time_seconds}s")

        if violations:
            self.violations.extend([{
                "timestamp": datetime.now().isoformat(),
                "plugin": self.plugin_name,
                "violations": violations
            }])

        return len(violations) == 0, violations

    def start_monitoring(self, interval: float = 1.0):
        """Start resource monitoring in background"""
        self._monitoring = True

        def monitor_loop():
            while self._monitoring:
                self.check_limits()
                time.sleep(interval)

        self._monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self._monitor_thread.start()

    def stop_monitoring(self):
        """Stop resource monitoring"""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2)

    def get_resource_summary(self) -> Dict[str, Any]:
        """Get resource usage summary"""
        current = self._get_current_resources()
        elapsed = time.time() - self.start_time

        return {
            "plugin": self.plugin_name,
            "elapsed_seconds": elapsed,
            "current_usage": current,
            "limits": {
                "memory_mb": self.limits.max_memory_mb,
                "cpu_percent": self.limits.max_cpu_percent,
                "file_handles": self.limits.max_file_handles,
                "threads": self.limits.max_threads,
                "execution_time": self.limits.max_execution_time_seconds
            },
            "violations": self.violations[-10:] if self.violations else []
        }


class SecureSandbox:
    """Enhanced secure sandbox with full isolation"""

    def __init__(self,
                 plugin_name: str,
                 capabilities: Set[PluginCapability],
                 security_level: SecurityLevel = SecurityLevel.STANDARD,
                 resource_limits: Optional[ResourceLimit] = None,
                 path_whitelist: Optional[PathWhitelist] = None,
                 network_whitelist: Optional[NetworkWhitelist] = None,
                 env_whitelist: Optional[EnvironmentWhitelist] = None):

        self.plugin_name = plugin_name
        self.capabilities = capabilities
        self.security_level = security_level
        self.resource_limits = resource_limits or ResourceLimit()
        self.path_whitelist = path_whitelist or PathWhitelist()
        self.network_whitelist = network_whitelist or NetworkWhitelist()
        self.env_whitelist = env_whitelist or EnvironmentWhitelist()

        self.audit_log: deque = deque(maxlen=1000)
        self.access_counter = defaultdict(int)
        self.resource_monitor = ResourceMonitor(plugin_name, self.resource_limits)
        self._original_functions: Dict[str, Any] = {}
        self._sandboxed = False

    def audit(self, action: str, resource: str, result: str, details: Optional[Dict] = None):
        """Add entry to audit log"""
        entry = AuditEntry(
            timestamp=datetime.now(),
            plugin_name=self.plugin_name,
            action=action,
            resource=resource,
            result=result,
            details=details or {}
        )
        self.audit_log.append(entry)
        self.access_counter[f"{action}:{result}"] += 1

    def check_capability(self, capability: PluginCapability, resource: str = "") -> bool:
        """Check if plugin has capability"""
        has_cap = capability in self.capabilities
        self.audit(
            f"capability_check:{capability.value}",
            resource,
            "granted" if has_cap else "denied"
        )

        if not has_cap:
            logger.warning(f"Plugin {self.plugin_name} denied capability {capability.value} for {resource}")

        return has_cap

    def check_path_access(self, path: Path, mode: str = "r") -> bool:
        """Check path access permission"""
        path = path.resolve()

        if mode == "r":
            if not self.check_capability(PluginCapability.FS_READ_USER, str(path)):
                return False
            allowed = self.path_whitelist.can_read(path)
        elif mode == "w":
            if not self.check_capability(PluginCapability.FS_WRITE_USER, str(path)):
                return False
            allowed = self.path_whitelist.can_write(path)
        else:
            allowed = False

        self.audit(f"path_access:{mode}", str(path), "allowed" if allowed else "blocked")
        return allowed

    def check_network_access(self, host: str, port: int) -> bool:
        """Check network access permission"""
        if not self.check_capability(PluginCapability.NET_HTTP, f"{host}:{port}"):
            return False

        allowed = self.network_whitelist.can_connect(host, port)
        self.audit("network_access", f"{host}:{port}", "allowed" if allowed else "blocked")
        return allowed

    def check_env_access(self, var: str, mode: str = "r") -> bool:
        """Check environment variable access"""
        if not self.check_capability(PluginCapability.SYS_ENVIRONMENT, var):
            return False

        if mode == "r":
            allowed = self.env_whitelist.can_read(var)
        elif mode == "w":
            allowed = self.env_whitelist.can_write(var)
        else:
            allowed = False

        self.audit(f"env_access:{mode}", var, "allowed" if allowed else "blocked")
        return allowed

    def wrap_function(self, func: Callable, check_func: Callable) -> Callable:
        """Wrap function with security check"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not check_func(*args, **kwargs):
                raise PermissionError(f"Access denied for {func.__name__}")
            return func(*args, **kwargs)
        return wrapper

    def activate(self):
        """Activate sandbox restrictions"""
        if self._sandboxed:
            return

        # Start resource monitoring
        self.resource_monitor.start_monitoring()

        # Patch dangerous functions based on security level
        if self.security_level in [SecurityLevel.STRICT, SecurityLevel.PARANOID]:
            self._patch_file_operations()
            self._patch_network_operations()
            self._patch_process_operations()

        self._sandboxed = True
        self.audit("sandbox", "activation", "success", {"security_level": self.security_level.value})

    def deactivate(self):
        """Deactivate sandbox restrictions"""
        if not self._sandboxed:
            return

        # Stop resource monitoring
        self.resource_monitor.stop_monitoring()

        # Restore original functions
        for name, func in self._original_functions.items():
            module_name, func_name = name.rsplit('.', 1)
            module = sys.modules.get(module_name)
            if module:
                setattr(module, func_name, func)

        self._sandboxed = False
        self.audit("sandbox", "deactivation", "success")

    def _patch_file_operations(self):
        """Patch file operations for sandboxing"""
        import builtins

        # Store originals
        self._original_functions['builtins.open'] = builtins.open

        # Patch open
        def sandboxed_open(file, mode='r', *args, **kwargs):
            path = Path(file)
            access_mode = 'r' if 'r' in mode else 'w'
            if not self.check_path_access(path, access_mode):
                raise PermissionError(f"Access denied: {file}")
            return self._original_functions['builtins.open'](file, mode, *args, **kwargs)

        builtins.open = sandboxed_open

    def _patch_network_operations(self):
        """Patch network operations for sandboxing"""
        import socket

        # Store original
        self._original_functions['socket.socket.connect'] = socket.socket.connect

        # Patch connect
        original_connect = socket.socket.connect
        def sandboxed_connect(self, address):
            host, port = address
            if not self.check_network_access(host, port):
                raise PermissionError(f"Network access denied: {host}:{port}")
            return original_connect(self, address)

        socket.socket.connect = sandboxed_connect

    def _patch_process_operations(self):
        """Patch process operations for sandboxing"""
        import subprocess

        # Store original
        self._original_functions['subprocess.Popen'] = subprocess.Popen

        # Patch subprocess
        def sandboxed_popen(*args, **kwargs):
            if not self.check_capability(PluginCapability.SYS_PROCESS, str(args)):
                raise PermissionError("Process execution denied")
            return self._original_functions['subprocess.Popen'](*args, **kwargs)

        subprocess.Popen = sandboxed_popen

    def get_audit_summary(self) -> Dict[str, Any]:
        """Get audit summary"""
        recent_entries = [entry.to_dict() for entry in list(self.audit_log)[-20:]]

        return {
            "plugin": self.plugin_name,
            "security_level": self.security_level.value,
            "total_actions": sum(self.access_counter.values()),
            "access_summary": dict(self.access_counter),
            "recent_audit_entries": recent_entries,
            "resource_usage": self.resource_monitor.get_resource_summary()
        }

    def __enter__(self):
        """Context manager entry"""
        self.activate()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.deactivate()
        return False


class VersionNegotiator:
    """Handles plugin version compatibility negotiation"""

    @staticmethod
    def parse_version(version: str) -> Tuple[int, int, int]:
        """Parse semantic version string"""
        parts = version.split('.')
        return tuple(int(p) for p in parts[:3])

    @staticmethod
    def is_compatible(plugin_version: str,
                     min_sdk: str,
                     max_sdk: Optional[str] = None) -> bool:
        """Check if plugin version is compatible with SDK"""
        plugin_v = VersionNegotiator.parse_version(plugin_version)
        min_v = VersionNegotiator.parse_version(min_sdk)
        current_v = VersionNegotiator.parse_version(SDK_VERSION)

        # Check if current SDK version meets plugin's minimum requirement
        if current_v < min_v:
            return False

        # Check if current SDK version doesn't exceed plugin's maximum requirement
        if max_sdk:
            max_v = VersionNegotiator.parse_version(max_sdk)
            if current_v > max_v:
                return False

        return True

    @staticmethod
    def negotiate_features(plugin_version: str) -> Dict[str, bool]:
        """Negotiate available features based on version"""
        features = {
            "async_hooks": True,
            "resource_monitoring": True,
            "secure_sandbox": True,
            "capability_system": True,
            "audit_logging": True,
            "version_negotiation": True
        }

        # Disable features for older plugins
        plugin_v = VersionNegotiator.parse_version(plugin_version)
        if plugin_v < (1, 0, 0):
            features["capability_system"] = False
            features["secure_sandbox"] = False

        return features


class PluginPermission(Enum):
    """Legacy permission enum for backward compatibility"""
    READ_CONFIG = "read_config"
    WRITE_CONFIG = "write_config"
    READ_DATA = "read_data"
    WRITE_DATA = "write_data"
    EXECUTE_COMMANDS = "execute_commands"
    NETWORK_ACCESS = "network_access"
    FILE_SYSTEM_READ = "file_system_read"
    FILE_SYSTEM_WRITE = "file_system_write"
    HOOK_REGISTRATION = "hook_registration"
    API_ACCESS = "api_access"

    def to_capabilities(self) -> Set[PluginCapability]:
        """Convert legacy permission to new capabilities"""
        mapping = {
            self.READ_CONFIG: {PluginCapability.DATA_READ},
            self.WRITE_CONFIG: {PluginCapability.DATA_WRITE},
            self.READ_DATA: {PluginCapability.DATA_READ},
            self.WRITE_DATA: {PluginCapability.DATA_WRITE},
            self.EXECUTE_COMMANDS: {PluginCapability.SYS_PROCESS},
            self.NETWORK_ACCESS: {PluginCapability.NET_HTTP},
            self.FILE_SYSTEM_READ: {PluginCapability.FS_READ_USER},
            self.FILE_SYSTEM_WRITE: {PluginCapability.FS_WRITE_USER},
            self.HOOK_REGISTRATION: {PluginCapability.HOOK_SYSTEM},
            self.API_ACCESS: {PluginCapability.API_INTERNAL}
        }
        return mapping.get(self, set())


class PluginState(Enum):
    """Plugin lifecycle states"""
    UNLOADED = "unloaded"
    LOADING = "loading"
    LOADED = "loaded"
    INITIALIZED = "initialized"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    ERROR = "error"
    UNLOADING = "unloading"


class HookType(Enum):
    """Available hook points in the system"""
    PRE_COMMAND = "pre_command"
    POST_COMMAND = "post_command"
    PRE_DATA_SAVE = "pre_data_save"
    POST_DATA_SAVE = "post_data_save"
    PRE_REPORT_GENERATE = "pre_report_generate"
    POST_REPORT_GENERATE = "post_report_generate"
    PRE_RECOMMENDATION = "pre_recommendation"
    POST_RECOMMENDATION = "post_recommendation"
    SYSTEM_STARTUP = "system_startup"
    SYSTEM_SHUTDOWN = "system_shutdown"


@dataclass
class PluginMetadata:
    """Plugin metadata and manifest"""
    name: str
    version: str
    author: str
    description: str
    required_permissions: Set[PluginPermission] = field(default_factory=set)
    required_capabilities: Set[PluginCapability] = field(default_factory=set)
    dependencies: List[str] = field(default_factory=list)
    hooks: Dict[HookType, List[str]] = field(default_factory=dict)
    config_schema: Dict[str, Any] = field(default_factory=dict)
    min_sdk_version: str = "1.0.0"
    max_sdk_version: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary"""
        return {
            "name": self.name,
            "version": self.version,
            "author": self.author,
            "description": self.description,
            "required_permissions": [p.value for p in self.required_permissions],
            "required_capabilities": [c.value for c in self.required_capabilities],
            "dependencies": self.dependencies,
            "hooks": {k.value: v for k, v in self.hooks.items()},
            "config_schema": self.config_schema,
            "min_sdk_version": self.min_sdk_version,
            "max_sdk_version": self.max_sdk_version
        }


@dataclass
class HookContext:
    """Context passed to hook handlers"""
    hook_type: HookType
    data: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def get(self, key: str, default: Any = None) -> Any:
        """Get data from context"""
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set data in context"""
        self.data[key] = value


class PluginBase(abc.ABC):
    """Base class for all plugins"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize plugin with optional configuration"""
        self.config = config or {}
        self.state = PluginState.UNLOADED
        self._metadata: Optional[PluginMetadata] = None
        self._sandbox: Optional[Union['PluginSandbox', 'SecureSandbox']] = None
        self._version_features: Dict[str, bool] = {}
        self._logger = logging.getLogger(f"plugin.{self.__class__.__name__}")

    @abc.abstractmethod
    def get_metadata(self) -> PluginMetadata:
        """Return plugin metadata"""
        pass

    @abc.abstractmethod
    async def initialize(self) -> bool:
        """Initialize plugin resources"""
        pass

    @abc.abstractmethod
    async def shutdown(self) -> None:
        """Clean up plugin resources"""
        pass

    async def on_load(self) -> None:
        """Called when plugin is loaded"""
        self.state = PluginState.LOADING
        self._metadata = self.get_metadata()
        self._logger.info(f"Loading plugin: {self._metadata.name} v{self._metadata.version}")

    async def on_unload(self) -> None:
        """Called when plugin is unloaded"""
        self.state = PluginState.UNLOADING
        await self.shutdown()
        self._logger.info(f"Unloaded plugin: {self._metadata.name}")
        self.state = PluginState.UNLOADED

    def validate_config(self) -> bool:
        """Validate plugin configuration against schema"""
        if not self._metadata or not self._metadata.config_schema:
            return True

        # Basic schema validation (can be extended with jsonschema)
        required_keys = self._metadata.config_schema.get("required", [])
        for key in required_keys:
            if key not in self.config:
                self._logger.error(f"Missing required config key: {key}")
                return False
        return True

    def has_permission(self, permission: PluginPermission) -> bool:
        """Check if plugin has requested permission"""
        if not self._metadata:
            return False
        return permission in self._metadata.required_permissions


class PluginSandbox:
    """Sandbox environment for plugin execution"""

    def __init__(self, plugin: PluginBase, granted_permissions: Set[PluginPermission]):
        """Initialize sandbox with plugin and granted permissions"""
        self.plugin = plugin
        self.granted_permissions = granted_permissions
        self.access_log: List[Dict[str, Any]] = []

    def check_permission(self, permission: PluginPermission) -> bool:
        """Check if permission is granted"""
        has_permission = permission in self.granted_permissions
        self.access_log.append({
            "timestamp": datetime.now().isoformat(),
            "permission": permission.value,
            "granted": has_permission,
            "plugin": self.plugin._metadata.name if self.plugin._metadata else "unknown"
        })

        if not has_permission:
            plugin_name = self.plugin._metadata.name if self.plugin._metadata else "unknown"
            logger.warning(f"Permission denied: {permission.value} for plugin {plugin_name}")

        return has_permission

    def execute_with_permissions(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with permission checks"""
        # Analyze function for required permissions (simplified)
        func_name = func.__name__

        # Map function patterns to permissions
        permission_map = {
            "read": PluginPermission.READ_DATA,
            "write": PluginPermission.WRITE_DATA,
            "execute": PluginPermission.EXECUTE_COMMANDS,
            "fetch": PluginPermission.NETWORK_ACCESS,
            "save": PluginPermission.FILE_SYSTEM_WRITE,
            "load": PluginPermission.FILE_SYSTEM_READ,
        }

        # Check permissions based on function name
        for pattern, permission in permission_map.items():
            if pattern in func_name.lower():
                if not self.check_permission(permission):
                    raise PermissionError(f"Permission {permission.value} required for {func_name}")

        # Execute function
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error executing {func_name} in sandbox: {e}")
            raise

    def get_access_summary(self) -> Dict[str, Any]:
        """Get summary of permission access attempts"""
        total_attempts = len(self.access_log)
        granted = sum(1 for log in self.access_log if log["granted"])
        denied = total_attempts - granted

        return {
            "total_attempts": total_attempts,
            "granted": granted,
            "denied": denied,
            "access_log": self.access_log[-10:]  # Last 10 entries
        }


class HookManager:
    """Manages plugin hooks and their execution"""

    def __init__(self):
        """Initialize hook manager"""
        self.hooks: Dict[HookType, List[Callable]] = {hook: [] for hook in HookType}
        self.hook_metadata: Dict[str, Dict[str, Any]] = {}

    def register_hook(self, hook_type: HookType, handler: Callable,
                     plugin_name: str, priority: int = 50) -> bool:
        """Register a hook handler"""
        try:
            # Validate handler
            if not callable(handler):
                raise ValueError(f"Handler must be callable: {handler}")

            # Store metadata
            handler_id = f"{plugin_name}.{handler.__name__}"
            self.hook_metadata[handler_id] = {
                "plugin": plugin_name,
                "hook_type": hook_type.value,
                "priority": priority,
                "registered_at": datetime.now().isoformat()
            }

            # Add to hooks with priority sorting
            self.hooks[hook_type].append((priority, handler_id, handler))
            self.hooks[hook_type].sort(key=lambda x: x[0])

            logger.info(f"Registered hook {hook_type.value} for {plugin_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to register hook: {e}")
            return False

    def unregister_hooks(self, plugin_name: str) -> int:
        """Unregister all hooks for a plugin"""
        count = 0
        for hook_type in HookType:
            self.hooks[hook_type] = [
                (p, hid, h) for p, hid, h in self.hooks[hook_type]
                if not hid.startswith(f"{plugin_name}.")
            ]
            count += 1

        # Clean metadata
        self.hook_metadata = {
            k: v for k, v in self.hook_metadata.items()
            if v["plugin"] != plugin_name
        }

        logger.info(f"Unregistered {count} hooks for {plugin_name}")
        return count

    async def execute_hook(self, hook_type: HookType, context: HookContext) -> HookContext:
        """Execute all handlers for a hook"""
        handlers = self.hooks.get(hook_type, [])

        for priority, handler_id, handler in handlers:
            try:
                # Execute handler
                if asyncio.iscoroutinefunction(handler):
                    result = await handler(context)
                else:
                    result = handler(context)

                # Update context if handler returns new context
                if isinstance(result, HookContext):
                    context = result

            except Exception as e:
                logger.error(f"Hook execution error in {handler_id}: {e}")
                # Continue with other handlers

        return context

    def get_hook_summary(self) -> Dict[str, Any]:
        """Get summary of registered hooks"""
        summary = {}
        for hook_type in HookType:
            handlers = self.hooks[hook_type]
            summary[hook_type.value] = {
                "count": len(handlers),
                "handlers": [hid for _, hid, _ in handlers]
            }
        return summary


class PluginLoader:
    """Loads and manages plugins"""

    def __init__(self, plugin_dir: Optional[Path] = None):
        """Initialize plugin loader"""
        self.plugin_dir = plugin_dir or Path(__file__).parent / "examples"
        self.plugins: Dict[str, PluginBase] = {}
        self.sandboxes: Dict[str, PluginSandbox] = {}
        self.hook_manager = HookManager()
        self.config: Dict[str, Any] = {}

    def discover_plugins(self) -> List[Path]:
        """Discover available plugins"""
        plugins = []

        # Find Python plugin files
        for file_path in self.plugin_dir.glob("*.py"):
            if file_path.name.startswith("_"):
                continue
            plugins.append(file_path)

        # Find plugin packages
        for dir_path in self.plugin_dir.iterdir():
            if dir_path.is_dir() and (dir_path / "__init__.py").exists():
                plugins.append(dir_path)

        logger.info(f"Discovered {len(plugins)} plugins")
        return plugins

    def load_plugin_module(self, path: Path) -> Optional[Type[PluginBase]]:
        """Load a plugin module and return plugin class"""
        try:
            # Load module
            if path.is_file():
                spec = importlib.util.spec_from_file_location(path.stem, path)
            else:
                spec = importlib.util.spec_from_file_location(
                    path.name, path / "__init__.py"
                )

            if not spec or not spec.loader:
                raise ImportError(f"Cannot load spec for {path}")

            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)

            # Find plugin class
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and
                    issubclass(obj, PluginBase) and
                    obj != PluginBase):
                    return obj

            logger.warning(f"No PluginBase subclass found in {path}")
            return None

        except Exception as e:
            logger.error(f"Failed to load plugin from {path}: {e}")
            traceback.print_exc()
            return None

    async def load_plugin(self, path: Path, config: Optional[Dict[str, Any]] = None) -> bool:
        """Load and initialize a plugin"""
        try:
            # Load plugin class
            plugin_class = self.load_plugin_module(path)
            if not plugin_class:
                return False

            # Instantiate plugin
            plugin = plugin_class(config)
            await plugin.on_load()

            # Get metadata
            metadata = plugin.get_metadata()

            # Check permissions
            logger.info(f"Plugin {metadata.name} requests permissions: {[p.value for p in metadata.required_permissions]}")

            # Create sandbox (grant all requested permissions for now)
            sandbox = PluginSandbox(plugin, metadata.required_permissions)
            plugin._sandbox = sandbox

            # Validate configuration
            if not plugin.validate_config():
                raise ValueError("Invalid plugin configuration")

            # Initialize plugin
            if await plugin.initialize():
                plugin.state = PluginState.INITIALIZED

                # Register hooks
                for hook_type, handlers in metadata.hooks.items():
                    for handler_name in handlers:
                        handler = getattr(plugin, handler_name, None)
                        if handler:
                            self.hook_manager.register_hook(
                                hook_type, handler, metadata.name
                            )

                # Store plugin
                self.plugins[metadata.name] = plugin
                self.sandboxes[metadata.name] = sandbox

                plugin.state = PluginState.ACTIVE
                logger.info(f"Successfully loaded plugin: {metadata.name} v{metadata.version}")
                return True
            else:
                logger.error(f"Plugin initialization failed: {metadata.name}")
                return False

        except Exception as e:
            logger.error(f"Failed to load plugin {path}: {e}")
            traceback.print_exc()
            return False

    async def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a plugin"""
        if plugin_name not in self.plugins:
            logger.warning(f"Plugin not found: {plugin_name}")
            return False

        try:
            plugin = self.plugins[plugin_name]

            # Unregister hooks
            self.hook_manager.unregister_hooks(plugin_name)

            # Unload plugin
            await plugin.on_unload()

            # Remove from registry
            del self.plugins[plugin_name]
            del self.sandboxes[plugin_name]

            logger.info(f"Unloaded plugin: {plugin_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to unload plugin {plugin_name}: {e}")
            return False

    async def reload_plugin(self, plugin_name: str) -> bool:
        """Reload a plugin"""
        if plugin_name in self.plugins:
            plugin = self.plugins[plugin_name]
            config = plugin.config

            # Find plugin path
            for path in self.discover_plugins():
                module = self.load_plugin_module(path)
                if module:
                    test_instance = module({})
                    if test_instance.get_metadata().name == plugin_name:
                        await self.unload_plugin(plugin_name)
                        return await self.load_plugin(path, config)

        return False

    def get_plugin_status(self) -> Dict[str, Any]:
        """Get status of all plugins"""
        status = {
            "loaded_plugins": [],
            "hook_summary": self.hook_manager.get_hook_summary(),
            "permission_summary": {}
        }

        for name, plugin in self.plugins.items():
            metadata = plugin._metadata
            sandbox = self.sandboxes[name]

            plugin_info = {
                "name": name,
                "version": metadata.version,
                "state": plugin.state.value,
                "permissions": [p.value for p in metadata.required_permissions],
                "hooks": list(metadata.hooks.keys()) if metadata.hooks else [],
                "access_summary": sandbox.get_access_summary()
            }
            status["loaded_plugins"].append(plugin_info)

            # Permission summary
            for perm in metadata.required_permissions:
                if perm.value not in status["permission_summary"]:
                    status["permission_summary"][perm.value] = []
                status["permission_summary"][perm.value].append(name)

        return status

    async def execute_hook(self, hook_type: HookType, data: Dict[str, Any]) -> HookContext:
        """Execute a hook with all registered handlers"""
        context = HookContext(hook_type=hook_type, data=data)
        return await self.hook_manager.execute_hook(hook_type, context)


class EnhancedPluginLoader(PluginLoader):
    """Enhanced plugin loader with v1.0 features"""

    def __init__(self,
                 plugin_dir: Optional[Path] = None,
                 security_level: SecurityLevel = SecurityLevel.STANDARD,
                 enable_audit: bool = True):
        super().__init__(plugin_dir)
        self.security_level = security_level
        self.enable_audit = enable_audit
        self.secure_sandboxes: Dict[str, SecureSandbox] = {}
        self.audit_manager = AuditManager() if enable_audit else None
        self.leak_detector = ResourceLeakDetector()

    async def load_plugin_secure(self,
                                 path: Path,
                                 config: Optional[Dict[str, Any]] = None,
                                 custom_limits: Optional[ResourceLimit] = None) -> bool:
        """Load plugin with enhanced security"""
        try:
            # Load plugin class
            plugin_class = self.load_plugin_module(path)
            if not plugin_class:
                return False

            # Instantiate plugin
            plugin = plugin_class(config)
            await plugin.on_load()

            # Get metadata
            metadata = plugin.get_metadata()

            # Version negotiation
            if not VersionNegotiator.is_compatible(
                metadata.version,
                metadata.min_sdk_version,
                metadata.max_sdk_version
            ):
                logger.error(f"Plugin {metadata.name} version {metadata.version} incompatible with SDK {SDK_VERSION}")
                return False

            # Negotiate features
            plugin._version_features = VersionNegotiator.negotiate_features(metadata.version)

            # Convert legacy permissions to capabilities
            capabilities = metadata.required_capabilities.copy()
            for perm in metadata.required_permissions:
                capabilities.update(perm.to_capabilities())

            # Create secure sandbox
            sandbox = SecureSandbox(
                plugin_name=metadata.name,
                capabilities=capabilities,
                security_level=self.security_level,
                resource_limits=custom_limits or ResourceLimit(),
                path_whitelist=self._create_path_whitelist(metadata),
                network_whitelist=self._create_network_whitelist(metadata),
                env_whitelist=self._create_env_whitelist(metadata)
            )

            # Activate sandbox
            sandbox.activate()
            plugin._sandbox = sandbox

            # Validate configuration
            if not plugin.validate_config():
                sandbox.deactivate()
                raise ValueError("Invalid plugin configuration")

            # Initialize plugin within sandbox
            with sandbox:
                if await plugin.initialize():
                    plugin.state = PluginState.INITIALIZED

                    # Register hooks with capability check
                    for hook_type, handlers in metadata.hooks.items():
                        if sandbox.check_capability(PluginCapability.HOOK_SYSTEM, hook_type.value):
                            for handler_name in handlers:
                                handler = getattr(plugin, handler_name, None)
                                if handler:
                                    self.hook_manager.register_hook(
                                        hook_type, handler, metadata.name
                                    )

                    # Store plugin and sandbox
                    self.plugins[metadata.name] = plugin
                    self.secure_sandboxes[metadata.name] = sandbox

                    # Start leak detection
                    self.leak_detector.track_plugin(metadata.name)

                    plugin.state = PluginState.ACTIVE
                    logger.info(f"Successfully loaded plugin with secure sandbox: {metadata.name} v{metadata.version}")

                    if self.audit_manager:
                        self.audit_manager.log_plugin_load(metadata.name, metadata.version, "success")

                    return True

            sandbox.deactivate()
            logger.error(f"Plugin initialization failed: {metadata.name}")
            return False

        except Exception as e:
            logger.error(f"Failed to load plugin {path}: {e}")
            if self.audit_manager:
                self.audit_manager.log_plugin_load(str(path), "unknown", "failed", str(e))
            return False

    async def unload_plugin_secure(self, plugin_name: str) -> bool:
        """Unload plugin with cleanup verification"""
        if plugin_name not in self.plugins:
            return False

        try:
            plugin = self.plugins[plugin_name]
            sandbox = self.secure_sandboxes.get(plugin_name)

            # Check for resource leaks before unload
            leaks = self.leak_detector.check_leaks(plugin_name)
            if leaks:
                logger.warning(f"Resource leaks detected in {plugin_name}: {leaks}")

            # Unregister hooks
            self.hook_manager.unregister_hooks(plugin_name)

            # Unload plugin
            if sandbox:
                with sandbox:
                    await plugin.on_unload()
                sandbox.deactivate()
            else:
                await plugin.on_unload()

            # Remove from registry
            del self.plugins[plugin_name]
            if plugin_name in self.secure_sandboxes:
                del self.secure_sandboxes[plugin_name]

            # Stop leak detection
            self.leak_detector.untrack_plugin(plugin_name)

            if self.audit_manager:
                self.audit_manager.log_plugin_unload(plugin_name, "success", leaks)

            logger.info(f"Unloaded plugin: {plugin_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to unload plugin {plugin_name}: {e}")
            if self.audit_manager:
                self.audit_manager.log_plugin_unload(plugin_name, "failed", None, str(e))
            return False

    def _create_path_whitelist(self, metadata: PluginMetadata) -> PathWhitelist:
        """Create path whitelist based on capabilities"""
        whitelist = PathWhitelist()

        # Add default paths based on capabilities
        if PluginCapability.FS_READ_USER in metadata.required_capabilities:
            whitelist.read_paths.add(Path.home() / ".pm" / "plugins" / metadata.name)

        if PluginCapability.FS_WRITE_USER in metadata.required_capabilities:
            whitelist.write_paths.add(Path.home() / ".pm" / "plugins" / metadata.name / "data")

        return whitelist

    def _create_network_whitelist(self, metadata: PluginMetadata) -> NetworkWhitelist:
        """Create network whitelist based on capabilities"""
        whitelist = NetworkWhitelist()

        if PluginCapability.NET_LOCALHOST in metadata.required_capabilities:
            whitelist.allow_localhost = True

        if PluginCapability.NET_HTTP in metadata.required_capabilities:
            whitelist.allowed_ports.update({80, 443})

        return whitelist

    def _create_env_whitelist(self, metadata: PluginMetadata) -> EnvironmentWhitelist:
        """Create environment whitelist based on capabilities"""
        whitelist = EnvironmentWhitelist()

        if PluginCapability.SYS_ENVIRONMENT in metadata.required_capabilities:
            whitelist.readable_vars.update({"HOME", "USER", "PATH"})

        return whitelist

    def get_security_status(self) -> Dict[str, Any]:
        """Get comprehensive security status"""
        status = {
            "security_level": self.security_level.value,
            "plugins": {},
            "global_stats": {
                "total_capability_checks": 0,
                "total_violations": 0,
                "resource_leaks": 0
            }
        }

        for name, sandbox in self.secure_sandboxes.items():
            audit_summary = sandbox.get_audit_summary()
            status["plugins"][name] = audit_summary

            # Update global stats
            status["global_stats"]["total_capability_checks"] += audit_summary.get("total_actions", 0)

            # Check for violations
            for key, count in audit_summary.get("access_summary", {}).items():
                if "denied" in key:
                    status["global_stats"]["total_violations"] += count

        # Add leak detection results
        for plugin_name in self.plugins:
            leaks = self.leak_detector.check_leaks(plugin_name)
            if leaks:
                status["global_stats"]["resource_leaks"] += len(leaks)

        return status


class AuditManager:
    """Centralized audit management"""

    def __init__(self, log_dir: Optional[Path] = None):
        self.log_dir = log_dir or Path.home() / ".pm" / "audit"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.current_session = str(uuid.uuid4())
        self.session_start = datetime.now()

    def log_plugin_load(self, plugin_name: str, version: str, status: str, error: Optional[str] = None):
        """Log plugin load event"""
        self._write_log({
            "event": "plugin_load",
            "plugin": plugin_name,
            "version": version,
            "status": status,
            "error": error,
            "timestamp": datetime.now().isoformat()
        })

    def log_plugin_unload(self, plugin_name: str, status: str, leaks: Optional[List] = None, error: Optional[str] = None):
        """Log plugin unload event"""
        self._write_log({
            "event": "plugin_unload",
            "plugin": plugin_name,
            "status": status,
            "resource_leaks": leaks,
            "error": error,
            "timestamp": datetime.now().isoformat()
        })

    def _write_log(self, entry: Dict[str, Any]):
        """Write log entry to file"""
        entry["session"] = self.current_session

        log_file = self.log_dir / f"audit_{datetime.now().strftime('%Y%m%d')}.jsonl"
        with open(log_file, 'a') as f:
            f.write(json.dumps(entry) + "\n")


class ResourceLeakDetector:
    """Detects resource leaks in plugins"""

    def __init__(self):
        self.baseline: Dict[str, Dict[str, Any]] = {}
        self.current: Dict[str, Dict[str, Any]] = {}

    def track_plugin(self, plugin_name: str):
        """Start tracking resources for plugin"""
        self.baseline[plugin_name] = self._capture_resources()

    def untrack_plugin(self, plugin_name: str):
        """Stop tracking resources for plugin"""
        if plugin_name in self.baseline:
            del self.baseline[plugin_name]
        if plugin_name in self.current:
            del self.current[plugin_name]

    def check_leaks(self, plugin_name: str) -> List[str]:
        """Check for resource leaks"""
        if plugin_name not in self.baseline:
            return []

        current = self._capture_resources()
        baseline = self.baseline[plugin_name]
        leaks = []

        # Check file handles
        if current.get("open_files", 0) > baseline.get("open_files", 0):
            leaks.append(f"File handles: {current['open_files'] - baseline['open_files']} not closed")

        # Check threads
        if current.get("threads", 0) > baseline.get("threads", 0):
            leaks.append(f"Threads: {current['threads'] - baseline['threads']} still running")

        # Check memory (allow some variance)
        mem_increase = current.get("memory_mb", 0) - baseline.get("memory_mb", 0)
        if mem_increase > 50:  # 50MB threshold
            leaks.append(f"Memory: {mem_increase:.1f}MB potential leak")

        return leaks

    def _capture_resources(self) -> Dict[str, Any]:
        """Capture current resource state"""
        try:
            import psutil
            process = psutil.Process()
            return {
                "memory_mb": process.memory_info().rss / 1024 / 1024,
                "open_files": len(process.open_files()) if hasattr(process, 'open_files') else 0,
                "threads": process.num_threads(),
                "connections": len(process.connections())
            }
        except ImportError:
            return {
                "memory_mb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024,
                "open_files": 0,
                "threads": threading.active_count(),
                "connections": 0
            }


class PluginConfigManager:
    """Manages plugin configurations"""

    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize config manager"""
        self.config_dir = config_dir or Path.home() / ".pm" / "plugins" / "config"
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def load_config(self, plugin_name: str) -> Dict[str, Any]:
        """Load configuration for a plugin"""
        config_file = self.config_dir / f"{plugin_name}.json"

        # Default configuration for common plugins
        default_configs = {
            'report_exporter': {
                'export_dir': str(Path.home() / '.pm' / 'exports'),
                'formats': ['json', 'markdown', 'csv'],
                'auto_timestamp': True
            },
            'custom_recommender': {
                'algorithm': 'collaborative_filtering',
                'max_recommendations': 10,
                'confidence_threshold': 0.5
            }
        }

        # Load user config if exists
        user_config = {}
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load config for {plugin_name}: {e}")

        # Merge default config with user config
        final_config = default_configs.get(plugin_name, {}).copy()
        final_config.update(user_config)

        # Ensure export directory exists for plugins that need it
        if 'export_dir' in final_config:
            export_path = Path(final_config['export_dir'])
            export_path.mkdir(parents=True, exist_ok=True)

        return final_config

    def save_config(self, plugin_name: str, config: Dict[str, Any]) -> bool:
        """Save configuration for a plugin"""
        config_file = self.config_dir / f"{plugin_name}.json"

        try:
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to save config for {plugin_name}: {e}")
            return False

    def delete_config(self, plugin_name: str) -> bool:
        """Delete configuration for a plugin"""
        config_file = self.config_dir / f"{plugin_name}.json"

        if config_file.exists():
            try:
                config_file.unlink()
                return True
            except Exception as e:
                logger.error(f"Failed to delete config for {plugin_name}: {e}")

        return False


# Export main components
__all__ = [
    # Core
    'PluginBase',
    'PluginMetadata',
    'PluginState',
    'HookType',
    'HookContext',

    # Legacy compatibility
    'PluginPermission',
    'PluginSandbox',

    # v1.0 Enhanced
    'PluginCapability',
    'SecurityLevel',
    'SecureSandbox',
    'ResourceLimit',
    'ResourceMonitor',
    'PathWhitelist',
    'NetworkWhitelist',
    'EnvironmentWhitelist',

    # Managers
    'HookManager',
    'PluginLoader',
    'EnhancedPluginLoader',
    'PluginConfigManager',
    'AuditManager',
    'ResourceLeakDetector',
    'VersionNegotiator',

    # Constants
    'SDK_VERSION',
    'MIN_SUPPORTED_VERSION',
    'MAX_SUPPORTED_VERSION'
]