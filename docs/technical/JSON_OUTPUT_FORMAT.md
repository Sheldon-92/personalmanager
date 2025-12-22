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

### 1. Budget Commands

#### Budget Status Command

```bash
pm budget status --json [project_name]
```

**Success Response (Single Project):**
```json
{
  "status": "success",
  "command": "budget.status",
  "timestamp": "2025-09-18T10:30:00Z",
  "data": {
    "project": "PersonalManager",
    "has_budget": true,
    "weekly": {
      "budget": 1200,
      "consumed": 480,
      "percentage": 40.0,
      "remaining": 720
    },
    "monthly": {
      "budget": 4800,
      "consumed": 1920,
      "percentage": 40.0,
      "remaining": 2880
    },
    "alert_level": "ok"
  },
  "error": null,
  "metadata": {
    "version": "0.5.0",
    "execution_time": 0.123
  }
}
```

**Success Response (All Projects):**
```json
{
  "status": "success",
  "command": "budget.status",
  "timestamp": "2025-09-18T10:30:00Z",
  "data": {
    "projects": [
      {
        "project_name": "PersonalManager",
        "weekly_budget": 1200,
        "weekly_consumed": 480,
        "weekly_percentage": 40.0,
        "monthly_budget": 4800,
        "monthly_consumed": 1920,
        "monthly_percentage": 40.0,
        "alert_level": "ok",
        "burn_rate": 2.5
      }
    ],
    "total_projects": 1
  },
  "error": null,
  "metadata": {
    "version": "0.5.0",
    "execution_time": 0.089
  }
}
```

#### Budget Forecast Command

```bash
pm budget forecast --json project_name
```

**Success Response:**
```json
{
  "status": "success",
  "command": "budget.forecast",
  "timestamp": "2025-09-18T10:30:00Z",
  "data": {
    "project": "PersonalManager",
    "has_budget": true,
    "current_burn_rate": 2.5,
    "current_burn_rate_display": "2.5h/day",
    "projections": {
      "weekly": {
        "projected": 1050,
        "budget": 1200,
        "projected_display": "17.5h"
      },
      "monthly": {
        "projected": 4500,
        "budget": 4800,
        "projected_display": "75.0h"
      }
    },
    "days_until_exhausted": 15,
    "exhaustion_status": "15 days",
    "recommendation": "Current pace is sustainable. Consider allocating more time if project scope increases.",
    "alert_level": "ok"
  },
  "error": null,
  "metadata": {
    "version": "0.5.0",
    "execution_time": 0.234
  }
}
```

### 2. Session Commands

#### Session List Command

```bash
pm session list --json [--active] [--today] [--temp] [--limit 10]
```

**Success Response:**
```json
{
  "status": "success",
  "command": "session.list",
  "timestamp": "2025-09-18T10:30:00Z",
  "data": {
    "sessions": [
      {
        "id": "sess_abc123def456",
        "project_id": "proj_xyz789",
        "project_name": "PersonalManager",
        "is_temporary": false,
        "description": "Implementing CLI contract coverage",
        "status": "active",
        "duration_seconds": 3600,
        "duration_display": "1:00:00",
        "start_time": "2025-09-18T09:30:00",
        "start_time_display": "09:30",
        "focus_mode": "deep_work",
        "notes": "Making good progress on JSON output"
      }
    ],
    "total": 1,
    "filters": {
      "active": true,
      "today": false,
      "temp": false,
      "limit": 10
    }
  },
  "error": null,
  "metadata": {
    "version": "0.5.0",
    "execution_time": 0.156
  }
}
```

### 3. Project Commands

#### Project List Command

```bash
pm project list --json [--all] [--type type] [--status status]
```

**Success Response:**
```json
{
  "status": "success",
  "command": "project.list",
  "timestamp": "2025-09-18T10:30:00Z",
  "data": {
    "projects": [
      {
        "id": "proj_abc123",
        "name": "PersonalManager",
        "type": "iterative",
        "status": "active",
        "priority": "high",
        "directory": "/Users/user/projects/personal-manager",
        "time_budget_weekly": 1200,
        "time_budget_display": "1200m",
        "deadline": "2025-12-31",
        "deadline_display": "2025-12-31",
        "created_at": "2025-09-01T00:00:00Z",
        "updated_at": "2025-09-18T10:00:00Z"
      }
    ],
    "total": 1,
    "filters": {
      "all_projects": false,
      "project_type": null,
      "status": "active"
    }
  },
  "error": null,
  "metadata": {
    "version": "0.5.0",
    "execution_time": 0.078
  }
}
```

### 4. AI Route Command

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
- **v0.5.0** (2025-09-18): Added comprehensive contract coverage
  - Budget commands: `status` and `forecast` with JSON support
  - Session commands: `list` with JSON support
  - Project commands: `list` with JSON support
  - Shared contract utilities in `pm.cli.contracts`
- Sprint 3: Standardized across all commands

---

*This specification is part of PersonalManager v0.1.0 documentation*