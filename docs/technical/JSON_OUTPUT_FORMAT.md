# JSON Output Format Specification

## Overview

This document defines the standardized JSON output format for PersonalManager CLI commands when using the `--json` flag.

## General Principles

1. **Consistency**: All commands follow the same structure
2. **Predictability**: Fields are always present, even if empty
3. **Machine-readable**: Strict JSON formatting
4. **Human-friendly**: Indented output for readability

## Standard Output Structure

```json
{
  "status": "success|failed|warning",
  "command": "command_name",
  "timestamp": "ISO-8601 timestamp",
  "data": {
    // Command-specific data
  },
  "error": null | {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {}
  },
  "metadata": {
    "version": "0.1.0",
    "execution_time": 0.123
  }
}
```

## Command-Specific Formats

### 1. AI Route Command

```bash
pm ai route --json "query text"
```

**Success Response:**
```json
{
  "status": "success",
  "command": "ai.route",
  "timestamp": "2025-09-14T10:30:00Z",
  "data": {
    "service": "claude",
    "query": "query text",
    "response": "AI response text",
    "tokens_used": 150
  },
  "error": null,
  "metadata": {
    "version": "0.1.0",
    "execution_time": 1.234
  }
}
```

**Error Response:**
```json
{
  "status": "failed",
  "command": "ai.route",
  "timestamp": "2025-09-14T10:30:00Z",
  "data": null,
  "error": {
    "code": "API_KEY_MISSING",
    "message": "Claude API key not configured",
    "details": {
      "service": "claude",
      "query": "query text"
    }
  },
  "metadata": {
    "version": "0.1.0",
    "execution_time": 0.012
  }
}
```

### 2. AI Status Command

```bash
pm ai status --json
```

**Response:**
```json
{
  "status": "success",
  "command": "ai.status",
  "timestamp": "2025-09-14T10:30:00Z",
  "data": {
    "claude": {
      "configured": true,
      "status": "ready"
    },
    "gemini": {
      "configured": false,
      "status": "not configured"
    }
  },
  "error": null,
  "metadata": {
    "version": "0.1.0",
    "execution_time": 0.023
  }
}
```

### 3. Doctor Command

```bash
pm doctor --json
```

**Response:**
```json
{
  "status": "success",
  "command": "doctor",
  "timestamp": "2025-09-14T10:30:00Z",
  "data": {
    "checks": {
      "python_version": {
        "status": "pass",
        "value": "3.9.6",
        "required": ">=3.9"
      },
      "dependencies": {
        "status": "pass",
        "missing": [],
        "installed": 15
      },
      "configuration": {
        "status": "pass",
        "files_found": [".personalmanager/config.json"]
      },
      "permissions": {
        "status": "pass",
        "issues": []
      }
    },
    "summary": {
      "total_checks": 4,
      "passed": 4,
      "failed": 0,
      "warnings": 0
    }
  },
  "error": null,
  "metadata": {
    "version": "0.1.0",
    "execution_time": 0.456
  }
}
```

### 4. Tasks List Command

```bash
pm tasks list --json
```

**Response:**
```json
{
  "status": "success",
  "command": "tasks.list",
  "timestamp": "2025-09-14T10:30:00Z",
  "data": {
    "tasks": [
      {
        "id": "task-001",
        "title": "Complete Sprint 3",
        "status": "in_progress",
        "priority": "high",
        "due_date": "2025-09-15",
        "tags": ["sprint3", "development"]
      }
    ],
    "summary": {
      "total": 1,
      "pending": 0,
      "in_progress": 1,
      "completed": 0
    }
  },
  "error": null,
  "metadata": {
    "version": "0.1.0",
    "execution_time": 0.089
  }
}
```

## Error Codes

Standard error codes used across all commands:

| Code | Description |
|------|-------------|
| `CONFIG_ERROR` | Configuration file issue |
| `API_KEY_MISSING` | Required API key not configured |
| `NETWORK_ERROR` | Network connection failed |
| `AUTH_FAILED` | Authentication failed |
| `INVALID_INPUT` | Invalid input parameters |
| `PERMISSION_DENIED` | Insufficient permissions |
| `NOT_FOUND` | Resource not found |
| `INTERNAL_ERROR` | Internal application error |

## Implementation Guidelines

### For Developers

1. **Always include all fields**: Even if null or empty
2. **Use ISO-8601 timestamps**: For consistency
3. **Measure execution time**: From command start to JSON output
4. **Version in metadata**: Always include application version
5. **Pretty-print JSON**: Use 2-space indentation

### Example Implementation

```python
import json
import time
from datetime import datetime

def format_json_output(command, data=None, error=None):
    """Format standardized JSON output."""
    return {
        "status": "failed" if error else "success",
        "command": command,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "data": data,
        "error": error,
        "metadata": {
            "version": "0.1.0",
            "execution_time": time.time() - start_time
        }
    }

# Usage
result = format_json_output(
    command="ai.route",
    data={"service": "claude", "response": "..."}
)
print(json.dumps(result, indent=2))
```

## Testing JSON Output

### Validation Script

```bash
# Validate JSON output
pm ai route --json "test" | python -m json.tool

# Check specific fields
pm ai status --json | jq '.data.claude.configured'

# Test error handling
pm ai route --json "" | jq '.error.code'
```

### Real Command Output Examples (Verified 2025-09-14)

#### AI Route Command (Error Response - No API Key)
```bash
./bin/pm-local ai route --json "test query"
```

**Actual Output:**
```json
{
  "status": "failed",
  "command": "ai.route",
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "Claude API key not configured. Run 'pm ai config --set claude.api_key=YOUR_KEY'",
    "details": {
      "service": "claude",
      "query": "test query"
    }
  },
  "data": null,
  "metadata": {
    "version": "0.1.0",
    "execution_time": 0.001
  }
}
```

#### AI Status Command
```bash
./bin/pm-local ai status --json
```

**Actual Output:**
```json
{
  "status": "success",
  "command": "ai.status",
  "data": {
    "claude": {
      "configured": false,
      "status": "not configured"
    },
    "gemini": {
      "configured": false,
      "status": "not configured"
    }
  },
  "error": null,
  "metadata": {
    "version": "0.1.0",
    "execution_time": 0.001
  }
}
```

**验证时间**: 2025-09-14
**命令版本**: PersonalManager Agent v0.1.0
**测试环境**: macOS with Poetry environment

## Migration Path

For commands being updated to the new format:

1. **Phase 1**: Add new format alongside old (with flag)
2. **Phase 2**: Make new format default, old format deprecated
3. **Phase 3**: Remove old format support

## Version History

- **v0.1.0** (2025-09-14): Initial specification
- Sprint 3: Standardized across all commands

---

*This specification is part of PersonalManager v0.1.0 documentation*