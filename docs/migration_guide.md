# Tool Specification Migration Guide: v1 to v2

**Guide Version**: 1.0
**Migration Target**: Tool Spec v1.x → Tool Spec v2.0
**Last Updated**: 2025-01-15

## Overview

This guide provides step-by-step instructions for migrating existing v1 tools to the new v2 specification. The migration is designed to be gradual and non-breaking, with extensive backward compatibility support.

## Pre-Migration Assessment

### Current Tool Analysis

Before migrating, analyze your existing v1 tools:

```bash
# List all current v1 tools
find src/pm/tools -name "*.py" -exec grep -l "def.*(" {} \;

# Check current function signatures
grep -n "def [a-z_]*(" src/pm/tools/*.py | head -10

# Identify return patterns
grep -n "return.*True.*False" src/pm/tools/*.py | head -5
```

### V1 vs V2 Key Differences

| Aspect | V1 Pattern | V2 Pattern | Breaking Change |
|--------|------------|------------|------------------|
| **Return Format** | `Tuple[bool, str, Optional[Dict]]` | `ToolResponse` object | ⚠️ Yes |
| **Error Handling** | Simple string messages | Structured `ToolError` | ⚠️ Yes |
| **Input Validation** | Manual validation | Schema-based validation | ✅ No |
| **Permissions** | Implicit (config-based) | Explicit RBAC/capabilities | ⚠️ Partial |
| **Metadata** | None | Rich execution metadata | ✅ No |
| **Registration** | File-based discovery | Registry-based | ✅ No |

## Step-by-Step Migration Process

### Step 1: Install Migration Tools

```bash
# Create migration utilities (to be implemented)
mkdir -p scripts/migration
cat > scripts/migration/v1_to_v2_converter.py << 'EOF'
"""Tool to assist with v1 to v2 migration"""

import ast
import json
from pathlib import Path
from typing import Dict, List, Any

class V1ToV2Converter:
    def __init__(self):
        self.v1_patterns = []
        self.v2_templates = {}

    def analyze_v1_tool(self, file_path: Path) -> Dict[str, Any]:
        """Analyze existing v1 tool file"""
        # Implementation would parse AST and extract tool information
        pass

    def generate_v2_definition(self, v1_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate v2 tool definition from v1 analysis"""
        pass

    def generate_v2_wrapper(self, v1_analysis: Dict[str, Any]) -> str:
        """Generate v2 wrapper code for existing v1 function"""
        pass

if __name__ == "__main__":
    converter = V1ToV2Converter()
    # CLI interface for conversion
EOF
```

### Step 2: Create V2 Tool Definitions

For each existing v1 tool, create a v2 definition:

#### Example: Habit Creation Tool

**Original V1 Function (habit_tools.py):**
```python
def create_habit(
    name: str,
    category: str = "other",
    # ... other parameters
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    # ... implementation
    return True, f"习惯 '{habit.name}' 创建成功", habit_info
```

**New V2 Definition:**
```json
{
  "id": "habit.create",
  "name": "Create Habit",
  "category": "habit_management",
  "version": "2.0.0",
  "description": "Create a new habit with specified parameters",
  "function_signature": {
    "input": {
      "schema": {
        "type": "object",
        "required": ["name"],
        "properties": {
          "name": {
            "type": "string",
            "minLength": 1,
            "maxLength": 200
          },
          "category": {
            "type": "string",
            "enum": ["health", "learning", "productivity", "mindfulness", "social", "creative", "other"],
            "default": "other"
          }
        }
      }
    }
  }
}
```

### Step 3: Create V2 Response Adapters

Create adapters that convert v1 responses to v2 format:

```python
# File: src/pm/tools/adapters/v2_response_adapter.py

from typing import Tuple, Optional, Dict, Any
from datetime import datetime
import time

from pm.tools.v2.types import ToolResponse, ToolError, ToolMetadata, ToolErrorCode

class V1ToV2ResponseAdapter:
    """Converts v1 tool responses to v2 format"""

    def __init__(self, tool_id: str, tool_name: str, tool_category: str):
        self.tool_id = tool_id
        self.tool_name = tool_name
        self.tool_category = tool_category
        self.start_time = time.time()

    def adapt_response(
        self,
        v1_response: Tuple[bool, str, Optional[Dict[str, Any]]],
        permissions_used: List[str] = None
    ) -> ToolResponse:
        """Convert v1 tuple response to v2 ToolResponse"""

        success, message, data = v1_response
        execution_time = time.time() - self.start_time

        if success:
            return ToolResponse(
                status="success",
                command=self.tool_id,
                data=data,
                error=None,
                metadata=ToolMetadata(
                    version="2.0.0",
                    execution_time=execution_time,
                    tool_info={
                        "name": self.tool_name,
                        "category": self.tool_category,
                        "permissions_used": permissions_used or []
                    },
                    input_validation={
                        "schema_version": "2.0.0",
                        "validation_time": 0  # v1 didn't have validation timing
                    }
                )
            )
        else:
            # Convert v1 error message to structured v2 error
            error_code = self._determine_error_code(message)

            return ToolResponse(
                status="failed",
                command=self.tool_id,
                data=None,
                error=ToolError(
                    code=error_code,
                    message=message,
                    details=data,
                    recovery_suggestions=self._generate_recovery_suggestions(error_code)
                ),
                metadata=ToolMetadata(
                    version="2.0.0",
                    execution_time=execution_time,
                    tool_info={
                        "name": self.tool_name,
                        "category": self.tool_category,
                        "permissions_used": permissions_used or []
                    },
                    input_validation={
                        "schema_version": "2.0.0",
                        "validation_time": 0
                    }
                )
            )

    def _determine_error_code(self, message: str) -> ToolErrorCode:
        """Map v1 error messages to v2 error codes"""
        message_lower = message.lower()

        if "未找到" in message or "not found" in message_lower:
            return ToolErrorCode.TOOL_RESOURCE_NOT_FOUND
        elif "已存在" in message or "already exists" in message_lower:
            return ToolErrorCode.TOOL_RESOURCE_ALREADY_EXISTS
        elif "参数" in message or "invalid" in message_lower:
            return ToolErrorCode.TOOL_INVALID_INPUT
        elif "权限" in message or "permission" in message_lower:
            return ToolErrorCode.TOOL_INSUFFICIENT_PERMISSIONS
        elif "未初始化" in message or "not initialized" in message_lower:
            return ToolErrorCode.TOOL_CONFIGURATION_ERROR
        else:
            return ToolErrorCode.TOOL_INTERNAL_ERROR

    def _generate_recovery_suggestions(self, error_code: ToolErrorCode) -> List[str]:
        """Generate recovery suggestions based on error code"""
        suggestions_map = {
            ToolErrorCode.TOOL_RESOURCE_NOT_FOUND: [
                "检查资源名称是否正确",
                "使用列表命令查看可用资源"
            ],
            ToolErrorCode.TOOL_RESOURCE_ALREADY_EXISTS: [
                "使用不同的名称",
                "先删除现有资源"
            ],
            ToolErrorCode.TOOL_INVALID_INPUT: [
                "检查输入参数格式",
                "查看工具帮助文档"
            ],
            ToolErrorCode.TOOL_CONFIGURATION_ERROR: [
                "运行 pm setup 初始化系统",
                "检查配置文件是否完整"
            ]
        }
        return suggestions_map.get(error_code, ["请查看文档或联系管理员"])
```

### Step 4: Create V2 Wrapper Functions

Create wrapper functions that provide v2 interface while calling v1 implementations:

```python
# File: src/pm/tools/v2/habit_tools_v2.py

from typing import Dict, Any, Optional
from pm.tools.adapters.v2_response_adapter import V1ToV2ResponseAdapter
from pm.tools.v2.validation import validate_tool_input
from pm.tools.v2.permissions import check_tool_permissions
from pm.tools.v2.types import ToolResponse, UserContext

# Import original v1 function
from pm.tools.habit_tools import create_habit as create_habit_v1

def create_habit(
    input_data: Dict[str, Any],
    user_context: UserContext,
    tool_definition: Dict[str, Any]
) -> ToolResponse:
    """V2 wrapper for habit creation tool"""

    # Initialize adapter
    adapter = V1ToV2ResponseAdapter(
        tool_id="habit.create",
        tool_name="Create Habit",
        tool_category="habit_management"
    )

    try:
        # Step 1: Validate input against schema
        validation_result = validate_tool_input(
            input_data,
            tool_definition["function_signature"]["input"]["schema"]
        )
        if not validation_result.is_valid:
            return adapter.create_validation_error_response(validation_result.errors)

        # Step 2: Check permissions
        permission_result = check_tool_permissions(
            tool_definition["permissions"],
            user_context
        )
        if not permission_result.is_authorized:
            return adapter.create_permission_error_response(permission_result.missing_permissions)

        # Step 3: Extract parameters for v1 function
        name = input_data["name"]
        category = input_data.get("category", "other")
        frequency = input_data.get("frequency", "daily")
        difficulty = input_data.get("difficulty", "easy")
        description = input_data.get("description")
        cue = input_data.get("cue")
        routine = input_data.get("routine")
        reward = input_data.get("reward")
        target_duration = input_data.get("target_duration")
        reminder_time = input_data.get("reminder_time")

        # Step 4: Call original v1 function
        v1_response = create_habit_v1(
            name=name,
            category=category,
            frequency=frequency,
            difficulty=difficulty,
            description=description,
            cue=cue,
            routine=routine,
            reward=reward,
            target_duration=target_duration,
            reminder_time=reminder_time,
            config=user_context.config
        )

        # Step 5: Convert response to v2 format
        return adapter.adapt_response(
            v1_response,
            permissions_used=permission_result.permissions_used
        )

    except Exception as e:
        return adapter.create_internal_error_response(str(e))
```

### Step 5: Update Tool Registry

Create or update the tool registry:

```python
# File: src/pm/tools/v2/registry.py

from typing import Dict, List, Optional
import json
from pathlib import Path

class ToolRegistry:
    """V2 Tool Registry Management"""

    def __init__(self, registry_path: Optional[Path] = None):
        self.registry_path = registry_path or Path("config/tool_registry_v2.json")
        self.tools: Dict[str, dict] = {}
        self.load_registry()

    def load_registry(self):
        """Load tool registry from file"""
        if self.registry_path.exists():
            with open(self.registry_path) as f:
                registry_data = json.load(f)
                self.tools = registry_data.get("tools", {})

    def register_tool(self, tool_definition: dict):
        """Register a new tool"""
        tool_id = tool_definition["id"]
        self.tools[tool_id] = tool_definition
        self._save_registry()

    def register_v1_tool_as_v2(self, v1_module: str, v1_function: str, v2_definition: dict):
        """Register a v1 tool with v2 definition"""
        tool_id = v2_definition["id"]

        # Add v1 compatibility information
        v2_definition["v1_compatibility"] = {
            "module": v1_module,
            "function": v1_function,
            "wrapper_module": f"pm.tools.v2.{v1_module.split('.')[-1]}_v2",
            "wrapper_function": v1_function
        }

        self.tools[tool_id] = v2_definition
        self._save_registry()

    def _save_registry(self):
        """Save registry to file"""
        registry_data = {
            "version": "2.0.0",
            "last_updated": datetime.utcnow().isoformat(),
            "tools": self.tools,
            "categories": self._generate_category_info(),
            "permissions": self._generate_permission_scheme()
        }

        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.registry_path, 'w') as f:
            json.dump(registry_data, f, indent=2)
```

### Step 6: Migration Script

Create an automated migration script:

```bash
#!/bin/bash
# File: scripts/migrate_tools_v1_to_v2.sh

set -e

echo "🔄 Starting Tool Migration: v1 → v2"
echo "======================================"

# Step 1: Backup existing tools
echo "📦 Creating backup..."
cp -r src/pm/tools src/pm/tools.backup.$(date +%Y%m%d_%H%M%S)

# Step 2: Create v2 directory structure
echo "📁 Creating v2 directory structure..."
mkdir -p src/pm/tools/v2/{adapters,validation,permissions,types}
mkdir -p config/tools/definitions

# Step 3: Generate v2 tool definitions
echo "🏗️  Generating v2 tool definitions..."
python scripts/migration/generate_v2_definitions.py

# Step 4: Create wrapper functions
echo "🔧 Creating v2 wrapper functions..."
python scripts/migration/generate_v2_wrappers.py

# Step 5: Update registry
echo "📋 Updating tool registry..."
python scripts/migration/update_registry.py

# Step 6: Run validation tests
echo "✅ Running validation tests..."
python -m pytest tests/tools/test_v2_migration.py -v

echo "✅ Migration completed successfully!"
echo "📖 Next steps:"
echo "   1. Review generated v2 wrapper functions"
echo "   2. Test individual tools with v2 interface"
echo "   3. Update CLI commands to use v2 tools"
echo "   4. Enable deprecation warnings for v1 tools"
```

## Compatibility Layer

### Automatic V1 Call Detection

```python
# File: src/pm/tools/v2/compatibility.py

import functools
import warnings
from typing import Callable, Any, Tuple, Optional, Dict

def v1_compatibility_wrapper(tool_id: str, v2_function: Callable):
    """Decorator to maintain v1 compatibility while using v2 implementation"""

    @functools.wraps(v2_function)
    def wrapper(*args, **kwargs):
        # Detect v1-style call (expecting tuple return)
        if hasattr(wrapper, '_v1_mode'):
            # Convert v2 call to v1 parameters
            # This would need to be customized per tool
            pass

        # Call v2 function
        v2_response = v2_function(*args, **kwargs)

        # If caller expects v1 response format, convert it
        if wrapper._expecting_v1_response():
            return _convert_v2_to_v1_response(v2_response)

        return v2_response

    wrapper._tool_id = tool_id
    return wrapper

def _convert_v2_to_v1_response(v2_response) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """Convert v2 ToolResponse back to v1 tuple format"""
    if v2_response.status == "success":
        return True, "操作成功", v2_response.data
    else:
        return False, v2_response.error.message, v2_response.error.details
```

## Testing Migration

### Create Migration Tests

```python
# File: tests/tools/test_v2_migration.py

import pytest
from pm.tools.v2.habit_tools_v2 import create_habit as create_habit_v2
from pm.tools.habit_tools import create_habit as create_habit_v1
from pm.tools.v2.types import UserContext

class TestV2Migration:
    """Test v1 to v2 migration compatibility"""

    def test_habit_creation_equivalent_results(self):
        """Test that v1 and v2 tools produce equivalent results"""

        # V1 call
        v1_success, v1_message, v1_data = create_habit_v1(
            name="Test Habit",
            category="health"
        )

        # V2 call
        user_context = UserContext(roles=["user"], capabilities=["habit.write"])
        v2_response = create_habit_v2(
            input_data={"name": "Test Habit", "category": "health"},
            user_context=user_context,
            tool_definition=load_tool_definition("habit.create")
        )

        # Compare results
        assert v1_success == (v2_response.status == "success")
        if v1_success:
            assert v1_data["name"] == v2_response.data["habit_info"]["name"]

    def test_error_handling_compatibility(self):
        """Test that error handling is properly migrated"""

        # Test invalid input
        v1_success, v1_message, v1_data = create_habit_v1(name="")

        user_context = UserContext(roles=["user"], capabilities=["habit.write"])
        v2_response = create_habit_v2(
            input_data={"name": ""},
            user_context=user_context,
            tool_definition=load_tool_definition("habit.create")
        )

        assert not v1_success
        assert v2_response.status == "failed"
        assert v2_response.error.code == "TOOL_INVALID_INPUT"
```

## Rollback Plan

### Emergency Rollback

If issues arise during migration:

```bash
#!/bin/bash
# File: scripts/rollback_v2_migration.sh

echo "🔄 Rolling back v2 migration..."

# Restore v1 tools from backup
if [ -d "src/pm/tools.backup.*" ]; then
    latest_backup=$(ls -d src/pm/tools.backup.* | tail -1)
    rm -rf src/pm/tools
    cp -r "$latest_backup" src/pm/tools
    echo "✅ Restored v1 tools from $latest_backup"
fi

# Disable v2 features
sed -i 's/ENABLE_V2_TOOLS=true/ENABLE_V2_TOOLS=false/' .env

# Restart services
echo "🔄 Restarting services..."
pm restart

echo "✅ Rollback completed"
```

## Post-Migration Checklist

### Verification Steps

- [ ] All v1 tools have v2 definitions
- [ ] V2 wrappers are created and tested
- [ ] Tool registry is populated
- [ ] Permission system is functional
- [ ] Input validation works correctly
- [ ] Error codes are properly mapped
- [ ] CLI commands work with both v1 and v2
- [ ] Backward compatibility is maintained
- [ ] Performance impact is acceptable
- [ ] Documentation is updated

### Monitoring

Set up monitoring for the migration:

```python
# File: src/pm/tools/v2/monitoring.py

import logging
from collections import defaultdict
from datetime import datetime, timedelta

class MigrationMonitor:
    """Monitor v1/v2 tool usage during migration"""

    def __init__(self):
        self.v1_calls = defaultdict(int)
        self.v2_calls = defaultdict(int)
        self.errors = []

    def log_v1_call(self, tool_name: str):
        self.v1_calls[tool_name] += 1

    def log_v2_call(self, tool_name: str):
        self.v2_calls[tool_name] += 1

    def log_migration_error(self, tool_name: str, error: str):
        self.errors.append({
            "tool": tool_name,
            "error": error,
            "timestamp": datetime.utcnow()
        })

    def get_migration_report(self) -> dict:
        return {
            "v1_usage": dict(self.v1_calls),
            "v2_usage": dict(self.v2_calls),
            "migration_rate": self._calculate_migration_rate(),
            "recent_errors": self._get_recent_errors()
        }

    def _calculate_migration_rate(self) -> float:
        total_v1 = sum(self.v1_calls.values())
        total_v2 = sum(self.v2_calls.values())
        total = total_v1 + total_v2
        return (total_v2 / total * 100) if total > 0 else 0

    def _get_recent_errors(self, hours: int = 24) -> list:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return [e for e in self.errors if e["timestamp"] > cutoff]
```

## Common Issues and Solutions

### Issue 1: Permission Mapping

**Problem**: V1 tools relied on implicit permissions through config access.

**Solution**: Create permission mapping:

```python
V1_TO_V2_PERMISSION_MAPPING = {
    "habit_tools": ["habit.read", "habit.write", "habit.delete"],
    "project_tools": ["project.read", "project.write"],
    "task_tools": ["task.read", "task.write", "task.delete"]
}
```

### Issue 2: Input Validation Differences

**Problem**: V1 validation was inconsistent across tools.

**Solution**: Standardize validation with schemas:

```python
def migrate_v1_validation_to_v2_schema(v1_function_code: str) -> dict:
    """Extract validation logic and convert to JSON Schema"""
    # Parse v1 validation code and generate schema
    pass
```

### Issue 3: Error Message Localization

**Problem**: V1 tools had mixed language error messages.

**Solution**: Standardize error messages:

```python
ERROR_MESSAGE_MAPPING = {
    "习惯名称不能为空": "TOOL_MISSING_REQUIRED_FIELD",
    "未找到习惯": "TOOL_RESOURCE_NOT_FOUND",
    # ... more mappings
}
```

## Timeline and Milestones

### Week 1: Preparation
- [ ] Set up migration infrastructure
- [ ] Create v2 directory structure
- [ ] Implement base adapter classes

### Week 2: Core Tools Migration
- [ ] Migrate habit management tools
- [ ] Migrate project management tools
- [ ] Create v2 wrappers

### Week 3: Enhanced Features
- [ ] Implement permission system
- [ ] Add input validation
- [ ] Create tool registry

### Week 4: Testing and Refinement
- [ ] Comprehensive testing
- [ ] Performance optimization
- [ ] Documentation updates

### Week 5: Gradual Rollout
- [ ] Enable v2 tools in development
- [ ] Monitor usage patterns
- [ ] Fix issues

### Week 6: Production Deployment
- [ ] Deploy v2 tools to production
- [ ] Enable deprecation warnings for v1
- [ ] User communication

### Week 7-8: V1 Deprecation
- [ ] Increase deprecation warning levels
- [ ] Plan v1 removal
- [ ] Final migration support

---

This migration guide provides a comprehensive approach to upgrading from v1 to v2 tool specifications while maintaining system stability and user experience.