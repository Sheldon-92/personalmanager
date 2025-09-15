# Personal Manager Plugin SDK v1.0 GA Guide

**Version**: 1.0.0 GA
**Status**: Production Ready
**Last Updated**: 2024-09-14

## Overview

The Personal Manager Plugin SDK v1.0 provides a comprehensive, secure, and scalable framework for developing plugins that extend the Personal Manager application. This GA release introduces enhanced security, resource monitoring, and capability-based permissions.

## Table of Contents

- [Quick Start](#quick-start)
- [Architecture Overview](#architecture-overview)
- [Security Model](#security-model)
- [Plugin Development](#plugin-development)
- [Advanced Features](#advanced-features)
- [Best Practices](#best-practices)
- [Migration Guide](#migration-guide)
- [API Reference](#api-reference)

## Quick Start

### Installation

The SDK is included with Personal Manager v0.2.0+. No additional installation required.

### Basic Plugin Structure

```python
from pm.plugins.sdk import PluginBase, PluginMetadata, PluginCapability, HookType

class MyPlugin(PluginBase):
    def get_metadata(self):
        return PluginMetadata(
            name="my_plugin",
            version="1.0.0",
            author="Your Name",
            description="A sample plugin",
            required_capabilities={
                PluginCapability.DATA_READ,
                PluginCapability.DATA_WRITE
            },
            hooks={
                HookType.PRE_COMMAND: ["on_pre_command"]
            },
            min_sdk_version="1.0.0"
        )

    async def initialize(self):
        """Initialize plugin resources"""
        self._logger.info(f"Initializing {self.get_metadata().name}")
        return True

    async def shutdown(self):
        """Clean up plugin resources"""
        self._logger.info("Plugin shutting down")

    def on_pre_command(self, context):
        """Hook handler for pre-command events"""
        context.set("processed_by", self.get_metadata().name)
        return context
```

### Loading Your Plugin

```python
from pm.plugins.sdk import EnhancedPluginLoader
from pathlib import Path

loader = EnhancedPluginLoader(plugin_dir=Path("./plugins"))
success = await loader.load_plugin_secure(Path("./plugins/my_plugin.py"))
```

## Architecture Overview

### Core Components

```
┌─────────────────────────────────────────────────────┐
│                Plugin SDK v1.0                      │
├─────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │ Plugin Base │  │ Hook System │  │ Config Mgmt │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  │
├─────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │ Secure      │  │ Resource    │  │ Audit &     │  │
│  │ Sandbox     │  │ Monitor     │  │ Compliance  │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  │
├─────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │ Version     │  │ Legacy      │  │ Leak        │  │
│  │ Negotiation │  │ Support     │  │ Detection   │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────┘
```

### Plugin Lifecycle

```
Unloaded → Loading → Loaded → Initialized → Active
    ↑                                         ↓
    └── Unloading ← Error ← Suspended ←──────┘
```

## Security Model

### Capability-Based Permissions

The SDK uses a fine-grained capability system instead of broad permissions:

#### File System Capabilities
- `FS_READ_USER`: Read user data files
- `FS_READ_SYSTEM`: Read system configuration files
- `FS_WRITE_USER`: Write to user data directories
- `FS_WRITE_SYSTEM`: Write to system directories
- `FS_DELETE`: Delete files
- `FS_EXECUTE`: Execute files

#### Network Capabilities
- `NET_HTTP`: HTTP/HTTPS network access
- `NET_SOCKET`: Raw socket access
- `NET_LOCALHOST`: Local network access only

#### System Capabilities
- `SYS_PROCESS`: Process management
- `SYS_ENVIRONMENT`: Environment variable access
- `SYS_RESOURCE`: System resource access

#### Data Capabilities
- `DATA_READ`: Read application data
- `DATA_WRITE`: Write application data
- `DATA_EXPORT`: Export data
- `DATA_IMPORT`: Import data

#### API Capabilities
- `API_INTERNAL`: Internal API access
- `API_EXTERNAL`: External API integration
- `API_ADMIN`: Administrative API access

#### Hook Capabilities
- `HOOK_SYSTEM`: System event hooks
- `HOOK_DATA`: Data event hooks
- `HOOK_UI`: User interface hooks

### Security Levels

```python
class SecurityLevel(Enum):
    MINIMAL = "minimal"      # Basic sandboxing
    STANDARD = "standard"    # Default RBAC + sandboxing
    STRICT = "strict"        # Full isolation + audit
    PARANOID = "paranoid"    # Maximum restrictions
```

### Sandbox Environment

The secure sandbox provides:

1. **Path Whitelisting**: Only approved paths accessible
2. **Network Filtering**: Only whitelisted hosts/ports
3. **Environment Protection**: Limited environment variables
4. **Resource Monitoring**: CPU, memory, file handle limits
5. **Audit Logging**: Complete action traceability

```python
# Example sandbox configuration
sandbox = SecureSandbox(
    plugin_name="my_plugin",
    capabilities={PluginCapability.DATA_READ, PluginCapability.NET_HTTP},
    security_level=SecurityLevel.STANDARD,
    resource_limits=ResourceLimit(
        max_memory_mb=100,
        max_cpu_percent=25.0,
        max_file_handles=50,
        max_execution_time_seconds=60
    )
)
```

## Plugin Development

### Plugin Metadata

Comprehensive metadata describes your plugin:

```python
metadata = PluginMetadata(
    name="advanced_plugin",
    version="2.1.0",
    author="Plugin Developer",
    description="Advanced plugin with multiple capabilities",

    # Modern capability system
    required_capabilities={
        PluginCapability.DATA_READ,
        PluginCapability.DATA_WRITE,
        PluginCapability.NET_HTTP,
        PluginCapability.FS_WRITE_USER
    },

    # Legacy permission support (auto-converted)
    required_permissions={
        PluginPermission.READ_DATA,
        PluginPermission.NETWORK_ACCESS
    },

    # Plugin dependencies
    dependencies=["requests", "pandas"],

    # Hook registrations
    hooks={
        HookType.PRE_COMMAND: ["handle_pre_command"],
        HookType.POST_DATA_SAVE: ["handle_data_save"]
    },

    # Configuration schema
    config_schema={
        "type": "object",
        "properties": {
            "api_endpoint": {"type": "string"},
            "timeout": {"type": "number", "default": 30}
        },
        "required": ["api_endpoint"]
    },

    # Version compatibility
    min_sdk_version="1.0.0",
    max_sdk_version="1.9.9"
)
```

### Hook System

Plugins can register handlers for system events:

#### Available Hook Points

- `PRE_COMMAND` / `POST_COMMAND`: Before/after command execution
- `PRE_DATA_SAVE` / `POST_DATA_SAVE`: Before/after data persistence
- `PRE_REPORT_GENERATE` / `POST_REPORT_GENERATE`: Before/after report creation
- `PRE_RECOMMENDATION` / `POST_RECOMMENDATION`: Before/after recommendations
- `SYSTEM_STARTUP` / `SYSTEM_SHUTDOWN`: System lifecycle events

#### Hook Handler Example

```python
def handle_pre_command(self, context: HookContext) -> HookContext:
    """Process commands before execution"""
    command = context.get("command")
    user_id = context.get("user_id")

    # Add plugin-specific processing
    if command.startswith("analyze"):
        context.set("enable_advanced_analysis", True)
        self._logger.info(f"Enhanced analysis enabled for user {user_id}")

    # Modify context and return
    context.metadata["processed_by"] = self.get_metadata().name
    return context

async def handle_data_save(self, context: HookContext) -> HookContext:
    """Process data after save operations"""
    data_type = context.get("data_type")
    record_count = context.get("record_count", 0)

    # Async processing allowed
    if data_type == "preferences" and record_count > 100:
        await self.trigger_analysis_pipeline(context.data)

    return context
```

### Resource Management

The SDK automatically monitors and enforces resource limits:

```python
# Custom resource limits
limits = ResourceLimit(
    max_memory_mb=200,         # 200MB memory limit
    max_cpu_percent=30.0,      # 30% CPU limit
    max_file_handles=100,      # 100 file handles
    max_network_connections=20, # 20 network connections
    max_threads=10,            # 10 threads
    max_execution_time_seconds=300  # 5 minute execution limit
)

# Monitor usage
monitor = ResourceMonitor("my_plugin", limits)
monitor.start_monitoring(interval=1.0)

# Check for violations
is_valid, violations = monitor.check_limits()
if not is_valid:
    for violation in violations:
        logger.warning(f"Resource violation: {violation}")

# Get usage summary
summary = monitor.get_resource_summary()
logger.info(f"Resource usage: {summary}")
```

## Advanced Features

### Version Negotiation

Plugins can specify version compatibility and negotiate features:

```python
# Check compatibility
is_compatible = VersionNegotiator.is_compatible(
    plugin_version="1.2.0",
    min_sdk_version="1.0.0",
    max_sdk_version="1.5.0"
)

# Get available features
features = VersionNegotiator.negotiate_features("1.0.0")
if features["async_hooks"]:
    # Use async hook handlers
    pass
if features["secure_sandbox"]:
    # Use enhanced sandbox features
    pass
```

### Configuration Management

```python
from pm.plugins.sdk import PluginConfigManager

config_manager = PluginConfigManager()

# Load plugin configuration
config = config_manager.load_config("my_plugin")

# Validate against schema
if plugin.validate_config():
    # Configuration is valid
    api_endpoint = config.get("api_endpoint")
    timeout = config.get("timeout", 30)

# Save updated configuration
updated_config = {
    "api_endpoint": "https://api.example.com",
    "timeout": 45,
    "new_feature_enabled": True
}
config_manager.save_config("my_plugin", updated_config)
```

### Audit and Compliance

All plugin operations are automatically audited:

```python
# Audit entries are automatically created
sandbox = SecureSandbox("my_plugin", capabilities)

# Check audit summary
summary = sandbox.get_audit_summary()
print(f"Total actions: {summary['total_actions']}")
print(f"Access summary: {summary['access_summary']}")

# Recent audit entries
for entry in summary["recent_audit_entries"]:
    print(f"{entry['timestamp']}: {entry['action']} -> {entry['result']}")
```

### Resource Leak Detection

Automatic detection of resource leaks:

```python
detector = ResourceLeakDetector()

# Start tracking plugin
detector.track_plugin("my_plugin")

# ... plugin operations ...

# Check for leaks
leaks = detector.check_leaks("my_plugin")
if leaks:
    logger.warning(f"Resource leaks detected: {leaks}")

# Stop tracking
detector.untrack_plugin("my_plugin")
```

## Best Practices

### 1. Minimal Capabilities

Request only the capabilities your plugin actually needs:

```python
# Good - specific capabilities
required_capabilities = {
    PluginCapability.DATA_READ,
    PluginCapability.NET_HTTP
}

# Bad - excessive capabilities
required_capabilities = {
    PluginCapability.FS_READ_SYSTEM,
    PluginCapability.FS_WRITE_SYSTEM,
    PluginCapability.SYS_PROCESS,
    PluginCapability.API_ADMIN
}
```

### 2. Proper Resource Cleanup

Always clean up resources in the `shutdown()` method:

```python
async def shutdown(self):
    """Clean up plugin resources"""
    # Close file handles
    if hasattr(self, '_file_handle'):
        self._file_handle.close()

    # Stop background tasks
    if hasattr(self, '_background_task'):
        self._background_task.cancel()

    # Close network connections
    if hasattr(self, '_session'):
        await self._session.close()

    self._logger.info("Plugin resources cleaned up")
```

### 3. Error Handling

Implement comprehensive error handling:

```python
async def initialize(self):
    """Initialize with proper error handling"""
    try:
        # Plugin initialization logic
        self.api_client = APIClient(self.config['api_endpoint'])
        await self.api_client.connect()

        # Test capabilities
        if not self.check_capability(PluginCapability.NET_HTTP):
            raise PermissionError("Network access required")

        return True

    except Exception as e:
        self._logger.error(f"Plugin initialization failed: {e}")
        return False
```

### 4. Configuration Validation

Validate configuration thoroughly:

```python
def validate_config(self) -> bool:
    """Comprehensive config validation"""
    if not super().validate_config():
        return False

    # Custom validation
    api_endpoint = self.config.get("api_endpoint", "")
    if not api_endpoint.startswith(("http://", "https://")):
        self._logger.error("Invalid API endpoint format")
        return False

    timeout = self.config.get("timeout", 30)
    if not isinstance(timeout, (int, float)) or timeout <= 0:
        self._logger.error("Invalid timeout value")
        return False

    return True
```

### 5. Secure Data Handling

Handle sensitive data securely:

```python
def process_sensitive_data(self, data):
    """Secure data processing"""
    # Check capabilities
    if not self.check_capability(PluginCapability.DATA_READ):
        raise PermissionError("Data read access denied")

    # Sanitize data
    cleaned_data = self.sanitize_input(data)

    # Process with audit trail
    self.audit("data_processing", "sensitive_data", "started")

    try:
        result = self.analyze_data(cleaned_data)
        self.audit("data_processing", "sensitive_data", "completed")
        return result
    except Exception as e:
        self.audit("data_processing", "sensitive_data", "failed", {"error": str(e)})
        raise
```

## Migration Guide

### From Legacy Plugin System

If you have existing plugins using the legacy permission system:

#### 1. Update Metadata

```python
# Old (still supported)
class OldPlugin(PluginBase):
    def get_metadata(self):
        return PluginMetadata(
            # ... other fields ...
            required_permissions={
                PluginPermission.READ_DATA,
                PluginPermission.NETWORK_ACCESS
            }
        )

# New (recommended)
class NewPlugin(PluginBase):
    def get_metadata(self):
        return PluginMetadata(
            # ... other fields ...
            required_capabilities={
                PluginCapability.DATA_READ,
                PluginCapability.NET_HTTP
            },
            min_sdk_version="1.0.0"
        )
```

#### 2. Update Sandbox Usage

```python
# Old
sandbox = PluginSandbox(plugin, granted_permissions)
sandbox.check_permission(PluginPermission.READ_DATA)

# New
sandbox = SecureSandbox(
    plugin_name=plugin.get_metadata().name,
    capabilities=capabilities,
    security_level=SecurityLevel.STANDARD
)
sandbox.check_capability(PluginCapability.DATA_READ, resource_path)
```

#### 3. Utilize New Features

Take advantage of v1.0 features:

```python
class MigratedPlugin(PluginBase):
    async def initialize(self):
        # Check negotiated features
        if self._version_features.get("resource_monitoring"):
            self._logger.info("Resource monitoring available")

        if self._version_features.get("audit_logging"):
            self._logger.info("Audit logging enabled")

        return True
```

## API Reference

### Core Classes

#### `PluginBase`
Abstract base class for all plugins.

**Methods:**
- `get_metadata() -> PluginMetadata`: Return plugin metadata
- `async initialize() -> bool`: Initialize plugin
- `async shutdown() -> None`: Clean up resources
- `validate_config() -> bool`: Validate configuration

#### `PluginMetadata`
Plugin description and requirements.

**Fields:**
- `name: str`: Plugin identifier
- `version: str`: Plugin version
- `author: str`: Plugin author
- `description: str`: Plugin description
- `required_capabilities: Set[PluginCapability]`: Required capabilities
- `required_permissions: Set[PluginPermission]`: Legacy permissions
- `dependencies: List[str]`: Plugin dependencies
- `hooks: Dict[HookType, List[str]]`: Hook registrations
- `config_schema: Dict[str, Any]`: Configuration schema
- `min_sdk_version: str`: Minimum SDK version
- `max_sdk_version: Optional[str]`: Maximum SDK version

#### `SecureSandbox`
Enhanced sandbox with capability-based security.

**Methods:**
- `check_capability(capability, resource) -> bool`: Check capability
- `activate()`: Activate sandbox
- `deactivate()`: Deactivate sandbox
- `get_audit_summary() -> Dict`: Get audit summary

#### `EnhancedPluginLoader`
Enhanced plugin loader with v1.0 features.

**Methods:**
- `async load_plugin_secure(path, config) -> bool`: Load plugin securely
- `async unload_plugin_secure(name) -> bool`: Unload plugin with leak detection
- `get_security_status() -> Dict`: Get comprehensive security status

### Hook System

#### `HookContext`
Context object passed to hook handlers.

**Methods:**
- `get(key, default) -> Any`: Get context value
- `set(key, value) -> None`: Set context value

#### `HookManager`
Manages plugin hooks and execution.

**Methods:**
- `register_hook(type, handler, plugin_name, priority) -> bool`: Register hook
- `unregister_hooks(plugin_name) -> int`: Unregister plugin hooks
- `async execute_hook(type, context) -> HookContext`: Execute hook

### Resource Management

#### `ResourceLimit`
Resource limits for plugins.

**Fields:**
- `max_memory_mb: int`: Maximum memory in MB
- `max_cpu_percent: float`: Maximum CPU percentage
- `max_file_handles: int`: Maximum open file handles
- `max_network_connections: int`: Maximum network connections
- `max_threads: int`: Maximum threads
- `max_execution_time_seconds: int`: Maximum execution time

#### `ResourceMonitor`
Monitors and enforces resource limits.

**Methods:**
- `start_monitoring(interval) -> None`: Start monitoring
- `stop_monitoring() -> None`: Stop monitoring
- `check_limits() -> Tuple[bool, List[str]]`: Check limits
- `get_resource_summary() -> Dict`: Get usage summary

### Version Management

#### `VersionNegotiator`
Handles version compatibility and feature negotiation.

**Static Methods:**
- `parse_version(version) -> Tuple[int, int, int]`: Parse version
- `is_compatible(plugin_version, min_sdk, max_sdk) -> bool`: Check compatibility
- `negotiate_features(plugin_version) -> Dict[str, bool]`: Negotiate features

## Troubleshooting

### Common Issues

#### 1. Plugin Load Failures

```python
# Check logs for specific error
loader = EnhancedPluginLoader(enable_audit=True)
success = await loader.load_plugin_secure(plugin_path)
if not success:
    # Check audit logs for details
    status = loader.get_security_status()
    print(f"Load failure details: {status}")
```

#### 2. Capability Violations

```python
# Monitor sandbox violations
sandbox = plugin._sandbox
summary = sandbox.get_audit_summary()

# Look for denied actions
denied_actions = [
    entry for entry in summary["recent_audit_entries"]
    if entry["result"] == "denied"
]
```

#### 3. Resource Leaks

```python
# Check for resource leaks
detector = ResourceLeakDetector()
leaks = detector.check_leaks(plugin_name)
if leaks:
    logger.warning(f"Detected leaks: {leaks}")
    # Plugin may need resource cleanup fixes
```

#### 4. Version Incompatibility

```python
# Check version compatibility
metadata = plugin.get_metadata()
compatible = VersionNegotiator.is_compatible(
    metadata.version,
    metadata.min_sdk_version,
    metadata.max_sdk_version
)
if not compatible:
    logger.error(f"Plugin {metadata.name} incompatible with SDK {SDK_VERSION}")
```

### Debug Mode

Enable comprehensive debugging:

```python
import logging
logging.getLogger("pm.plugins.sdk").setLevel(logging.DEBUG)

# Enhanced loader with strict security for debugging
loader = EnhancedPluginLoader(
    security_level=SecurityLevel.PARANOID,
    enable_audit=True
)
```

## Support and Resources

- **Documentation**: `/docs/plugins/`
- **Examples**: `/src/pm/plugins/examples/`
- **Issue Tracker**: GitHub Issues
- **SDK Version**: v1.0.0 GA
- **Compatibility**: Personal Manager v0.2.0+

## Changelog

### v1.0.0 GA (2024-09-14)
- ✅ Enhanced RBAC with fine-grained capabilities
- ✅ Secure sandbox with path/network/environment whitelisting
- ✅ Version negotiation mechanism
- ✅ Resource leak detection
- ✅ Complete audit logging
- ✅ Load/unload stability improvements
- ✅ Legacy plugin compatibility
- ✅ Comprehensive conformance testing

### Previous Versions
- v0.9.0: Beta release with core functionality
- v0.8.0: Alpha release with basic plugin system

---

**Personal Manager Plugin SDK v1.0 GA** - Production ready plugin development platform with enterprise-grade security, monitoring, and compliance features.