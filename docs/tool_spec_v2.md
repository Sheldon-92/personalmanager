# Tool Specification v2.0 - PersonalManager

**Protocol Version**: 2.0.0
**Document Version**: 1.0
**Last Updated**: 2025-01-15
**Status**: Draft
**Based on**: Explain Protocol v1.0, AI_PROTOCOL_COMPATIBILITY.md

## Executive Summary

Tool Specification v2.0 standardizes input validation, output formats, error handling, and permissions for AI-callable tools in PersonalManager. Building on the success of the Explain Protocol, it provides a unified framework for tool development, registration, discovery, and execution with enhanced security and interoperability.

## Core Design Principles

1. **Backward Compatibility**: Gradual migration path from v1 with clear deprecation strategy
2. **Type Safety**: Comprehensive input validation and output schemas
3. **Security First**: RBAC permissions and capability-based access control
4. **Protocol Alignment**: Consistent with AI_PROTOCOL_COMPATIBILITY.md standards
5. **Developer Experience**: Clear APIs, excellent documentation, easy testing

## Base Tool Response Format

All v2 tools follow the established AI protocol structure:

```typescript
interface ToolResponse<T = any> extends AIResponse {
  status: "success" | "failed" | "error";
  command: string;           // Tool identifier (e.g., "tools.habit.create")
  data: T | null;           // Tool-specific response data
  error?: ToolError;        // Standardized error information
  metadata: ToolMetadata;   // Tool execution metadata
}

interface ToolError {
  code: ToolErrorCode;      // Standardized error code
  message: string;          // Human-readable error message
  details?: any;            // Additional error context
  recovery_suggestions?: string[]; // Actionable recovery steps
}

interface ToolMetadata {
  version: string;          // Tool spec version (semver)
  execution_time: number;   // Execution time in seconds
  tool_info: {
    name: string;           // Tool name
    category: ToolCategory; // Tool category
    permissions_used: string[]; // Permissions actually used
  };
  input_validation: {
    schema_version: string; // Input schema version used
    validation_time: number; // Input validation time (ms)
  };
}
```

## Tool Definition Schema

### Core Tool Definition

```typescript
interface ToolDefinition {
  // Tool Identity
  id: string;               // Unique tool identifier (e.g., "habit.create")
  name: string;             // Human-readable tool name
  category: ToolCategory;   // Tool categorization
  version: string;          // Tool version (semver)

  // Tool Specification
  description: string;      // Brief tool description
  detailed_description?: string; // Extended description
  function_signature: FunctionSignature; // Input/output schema

  // Permissions & Security
  permissions: ToolPermissions; // Required permissions
  security_level: SecurityLevel; // Security classification

  // Runtime Information
  implementation: ToolImplementation; // How to execute tool
  validation: ValidationRules; // Input validation rules

  // Metadata
  author?: string;          // Tool author
  created_at: string;       // ISO datetime
  updated_at: string;       // ISO datetime
  deprecated_at?: string;   // If deprecated, when
  replacement_tool?: string; // If deprecated, replacement
}

enum ToolCategory {
  HABIT_MANAGEMENT = "habit_management",
  PROJECT_MANAGEMENT = "project_management",
  TASK_MANAGEMENT = "task_management",
  TIME_MANAGEMENT = "time_management",
  KNOWLEDGE_MANAGEMENT = "knowledge_management",
  SYSTEM_ADMINISTRATION = "system_admin",
  AI_EXPLANATION = "ai_explanation",
  DATA_ANALYSIS = "data_analysis",
  INTEGRATION = "integration",
  CUSTOM = "custom"
}

enum SecurityLevel {
  PUBLIC = "public",        // No sensitive data access
  INTERNAL = "internal",    // Internal system access
  CONFIDENTIAL = "confidential", // User data access
  RESTRICTED = "restricted"  // Admin-level access
}
```

### Function Signature Definition

```typescript
interface FunctionSignature {
  input: {
    schema: JSONSchema;     // JSON Schema for input validation
    examples: InputExample[]; // Example inputs
    required_fields: string[]; // Required field names
  };
  output: {
    success_schema: JSONSchema; // Schema for successful responses
    error_schemas: Record<string, JSONSchema>; // Schemas for error responses
    examples: OutputExample[]; // Example outputs
  };
  side_effects?: SideEffect[]; // Declared side effects
}

interface InputExample {
  name: string;             // Example name
  description: string;      // What this example demonstrates
  input: any;              // Example input data
  expected_output_type: "success" | "error"; // Expected result type
}

interface OutputExample {
  name: string;             // Example name
  scenario: string;         // When this output occurs
  response: ToolResponse;   // Example response
}

interface SideEffect {
  type: "read" | "write" | "delete" | "network" | "filesystem";
  description: string;      // What the side effect does
  reversible: boolean;      // Can this be undone
}
```

## Permission System

### RBAC (Role-Based Access Control)

```typescript
interface ToolPermissions {
  required_roles: Role[];   // Roles that can use this tool
  required_capabilities: Capability[]; // Specific capabilities needed
  resource_access: ResourceAccess[]; // Resource access patterns
}

enum Role {
  USER = "user",            // Regular user
  POWER_USER = "power_user", // Advanced user
  ADMIN = "admin",          // System administrator
  DEVELOPER = "developer",  // Tool developer
  AI_AGENT = "ai_agent"     // AI agent execution
}

interface Capability {
  name: string;             // Capability name (e.g., "habit.write")
  scope?: string;           // Scope restriction (e.g., "self_only")
  conditions?: CapabilityCondition[]; // When this capability applies
}

interface ResourceAccess {
  resource_type: ResourceType; // Type of resource
  access_mode: AccessMode;  // How resource is accessed
  scope_filter?: string;    // Scope limitations
}

enum ResourceType {
  HABIT_DATA = "habit_data",
  TASK_DATA = "task_data",
  PROJECT_DATA = "project_data",
  USER_PREFERENCES = "user_preferences",
  SYSTEM_CONFIG = "system_config",
  EXTERNAL_API = "external_api",
  FILESYSTEM = "filesystem"
}

enum AccessMode {
  READ = "read",
  WRITE = "write",
  DELETE = "delete",
  CREATE = "create",
  UPDATE = "update"
}
```

### Capability-Based Security

```typescript
interface CapabilityCondition {
  type: "time_restriction" | "rate_limit" | "user_consent" | "admin_approval";
  parameters: Record<string, any>; // Condition-specific parameters
}

// Example capabilities
const STANDARD_CAPABILITIES = {
  // Habit Management
  "habit.read": { resource: "habit_data", mode: "read", scope: "self" },
  "habit.write": { resource: "habit_data", mode: "write", scope: "self" },
  "habit.delete": { resource: "habit_data", mode: "delete", scope: "self" },

  // Project Management
  "project.read": { resource: "project_data", mode: "read", scope: "accessible" },
  "project.write": { resource: "project_data", mode: "write", scope: "owned" },

  // System Administration
  "system.config.read": { resource: "system_config", mode: "read", scope: "all" },
  "system.config.write": { resource: "system_config", mode: "write", scope: "all" },

  // AI Explanation
  "ai.explain": { resource: "any", mode: "read", scope: "analysis_only" }
};
```

## Error Handling System

### Standardized Error Codes

```typescript
enum ToolErrorCode {
  // Input Validation Errors (1000-1099)
  INVALID_INPUT = "TOOL_INVALID_INPUT",
  MISSING_REQUIRED_FIELD = "TOOL_MISSING_REQUIRED_FIELD",
  INVALID_FIELD_TYPE = "TOOL_INVALID_FIELD_TYPE",
  INVALID_FIELD_VALUE = "TOOL_INVALID_FIELD_VALUE",
  INPUT_TOO_LARGE = "TOOL_INPUT_TOO_LARGE",

  // Permission Errors (1100-1199)
  INSUFFICIENT_PERMISSIONS = "TOOL_INSUFFICIENT_PERMISSIONS",
  ROLE_NOT_AUTHORIZED = "TOOL_ROLE_NOT_AUTHORIZED",
  CAPABILITY_MISSING = "TOOL_CAPABILITY_MISSING",
  RESOURCE_ACCESS_DENIED = "TOOL_RESOURCE_ACCESS_DENIED",
  RATE_LIMIT_EXCEEDED = "TOOL_RATE_LIMIT_EXCEEDED",

  // Execution Errors (1200-1299)
  TOOL_NOT_FOUND = "TOOL_NOT_FOUND",
  TOOL_DEPRECATED = "TOOL_DEPRECATED",
  TOOL_TEMPORARILY_DISABLED = "TOOL_TEMPORARILY_DISABLED",
  EXECUTION_TIMEOUT = "TOOL_EXECUTION_TIMEOUT",
  RESOURCE_UNAVAILABLE = "TOOL_RESOURCE_UNAVAILABLE",

  // Data Errors (1300-1399)
  RESOURCE_NOT_FOUND = "TOOL_RESOURCE_NOT_FOUND",
  RESOURCE_ALREADY_EXISTS = "TOOL_RESOURCE_ALREADY_EXISTS",
  DATA_CORRUPTION = "TOOL_DATA_CORRUPTION",
  STORAGE_ERROR = "TOOL_STORAGE_ERROR",

  // Integration Errors (1400-1499)
  EXTERNAL_SERVICE_ERROR = "TOOL_EXTERNAL_SERVICE_ERROR",
  API_KEY_INVALID = "TOOL_API_KEY_INVALID",
  NETWORK_ERROR = "TOOL_NETWORK_ERROR",

  // System Errors (1500-1599)
  INTERNAL_ERROR = "TOOL_INTERNAL_ERROR",
  CONFIGURATION_ERROR = "TOOL_CONFIGURATION_ERROR",
  DEPENDENCY_ERROR = "TOOL_DEPENDENCY_ERROR"
}
```

### Error Recovery System

```typescript
interface ErrorRecoveryInfo {
  error_code: ToolErrorCode;
  is_recoverable: boolean;
  recovery_strategies: RecoveryStrategy[];
  user_actions: UserAction[];
}

interface RecoveryStrategy {
  strategy_id: string;      // Strategy identifier
  description: string;      // What this strategy does
  automatic: boolean;       // Can be applied automatically
  side_effects: string[];   // What applying this strategy affects
}

interface UserAction {
  action_type: "retry" | "modify_input" | "check_permissions" | "contact_admin";
  description: string;      // What the user should do
  command_example?: string; // Example command to fix issue
}
```

## Tool Registration & Discovery

### Tool Registry

```typescript
interface ToolRegistry {
  version: string;          // Registry format version
  last_updated: string;     // Last registry update
  tools: Record<string, ToolDefinition>; // All registered tools
  categories: Record<ToolCategory, ToolCategoryInfo>; // Category metadata
  permissions: PermissionSchemeDefinition; // Permission scheme
}

interface ToolCategoryInfo {
  category: ToolCategory;
  name: string;             // Human-readable name
  description: string;      // Category description
  tool_count: number;       // Number of tools in category
  common_permissions: Capability[]; // Commonly needed permissions
}

interface PermissionSchemeDefinition {
  version: string;          // Permission scheme version
  roles: Record<Role, RoleDefinition>; // Role definitions
  capabilities: Record<string, CapabilityDefinition>; // Capability definitions
  default_grants: Record<Role, string[]>; // Default capability grants
}
```

### Tool Discovery API

```typescript
interface ToolDiscoveryAPI {
  // Basic Discovery
  listTools(category?: ToolCategory, role?: Role): ToolDefinition[];
  getTool(toolId: string): ToolDefinition | null;
  searchTools(query: string, options?: SearchOptions): ToolSearchResult[];

  // Permission Queries
  getAvailableTools(userRoles: Role[], capabilities: string[]): ToolDefinition[];
  checkPermissions(toolId: string, userContext: UserContext): PermissionCheckResult;

  // Registry Management
  registerTool(tool: ToolDefinition): RegistrationResult;
  updateTool(toolId: string, updates: Partial<ToolDefinition>): UpdateResult;
  deprecateTool(toolId: string, replacement?: string): DeprecationResult;
}

interface SearchOptions {
  category_filter?: ToolCategory[];
  permission_filter?: string[];
  security_level?: SecurityLevel;
  include_deprecated?: boolean;
}

interface UserContext {
  roles: Role[];
  capabilities: string[];
  session_info?: SessionInfo;
}
```

## Version Migration Strategy

### V1 to V2 Migration

```typescript
interface MigrationStrategy {
  migration_version: "1.0_to_2.0";

  // Field Mappings
  field_mappings: FieldMapping[];

  // Transformation Rules
  transformation_rules: TransformationRule[];

  // Deprecation Schedule
  deprecation_timeline: DeprecationPhase[];

  // Compatibility Layer
  compatibility_mode: CompatibilitySettings;
}

interface FieldMapping {
  v1_field: string;         // V1 field name
  v2_field: string;         // V2 field name
  transformation?: string;  // How to transform value
  required_in_v2: boolean;  // Is field required in v2
}

interface TransformationRule {
  applies_to: string[];     // Which tools this rule applies to
  rule_type: "rename" | "restructure" | "validate" | "enrich";
  rule_definition: any;     // Rule-specific configuration
}

interface DeprecationPhase {
  phase_name: string;       // Phase identifier
  start_date: string;       // When phase begins
  end_date: string;         // When phase ends
  actions: DeprecationAction[]; // Actions in this phase
}

interface DeprecationAction {
  action_type: "warn" | "redirect" | "disable" | "remove";
  target: string;           // What's being deprecated
  message: string;          // User-facing message
  alternative: string;      // Recommended alternative
}
```

### Backward Compatibility Layer

```typescript
interface CompatibilitySettings {
  enable_v1_mode: boolean;  // Allow v1 tool calls
  v1_warning_level: "none" | "log" | "user_facing";
  v1_redirect_mode: "transparent" | "explicit";
  v1_support_end_date: string; // When v1 support ends
}

// V1 Tool Call Adapter
interface V1ToolCallAdapter {
  adaptV1Call(v1Request: V1ToolRequest): V2ToolRequest;
  adaptV2Response(v2Response: ToolResponse): V1ToolResponse;
  generateMigrationWarning(toolId: string): MigrationWarning;
}
```

## Implementation Examples

### Example Tool Definition: Habit Creation

```typescript
const HABIT_CREATE_TOOL: ToolDefinition = {
  id: "habit.create",
  name: "Create Habit",
  category: ToolCategory.HABIT_MANAGEMENT,
  version: "2.0.0",

  description: "Create a new habit with specified parameters",
  detailed_description: "Creates a new habit based on atomic habits principles, allowing specification of category, frequency, difficulty, cues, routines, and rewards.",

  function_signature: {
    input: {
      schema: {
        type: "object",
        required: ["name"],
        properties: {
          name: { type: "string", minLength: 1, maxLength: 200 },
          category: {
            type: "string",
            enum: ["health", "learning", "productivity", "mindfulness", "social", "creative", "other"],
            default: "other"
          },
          frequency: {
            type: "string",
            enum: ["daily", "weekly", "monthly"],
            default: "daily"
          },
          difficulty: {
            type: "string",
            enum: ["tiny", "easy", "medium", "hard"],
            default: "easy"
          },
          description: { type: "string", maxLength: 1000 },
          cue: { type: "string", maxLength: 500 },
          routine: { type: "string", maxLength: 500 },
          reward: { type: "string", maxLength: 500 },
          target_duration: { type: "integer", minimum: 1, maximum: 480 },
          reminder_time: { type: "string", pattern: "^\\d{2}:\\d{2}$" }
        }
      },
      examples: [
        {
          name: "simple_habit",
          description: "Create a simple daily habit",
          input: {
            name: "Morning meditation",
            category: "mindfulness",
            frequency: "daily",
            difficulty: "easy"
          },
          expected_output_type: "success"
        },
        {
          name: "complex_habit",
          description: "Create a habit with all parameters",
          input: {
            name: "Evening workout",
            category: "health",
            frequency: "daily",
            difficulty: "medium",
            description: "30-minute strength training session",
            cue: "After dinner cleanup",
            routine: "15 min strength + 15 min flexibility",
            reward: "Listen to favorite podcast",
            target_duration: 30,
            reminder_time: "19:30"
          },
          expected_output_type: "success"
        }
      ],
      required_fields: ["name"]
    },
    output: {
      success_schema: {
        type: "object",
        required: ["habit_info"],
        properties: {
          habit_info: {
            type: "object",
            properties: {
              id: { type: "string" },
              name: { type: "string" },
              category: { type: "string" },
              frequency: { type: "string" },
              difficulty: { type: "string" },
              created_at: { type: "string", format: "date-time" }
            }
          }
        }
      },
      error_schemas: {
        "TOOL_INVALID_INPUT": {
          type: "object",
          properties: {
            validation_errors: {
              type: "array",
              items: {
                type: "object",
                properties: {
                  field: { type: "string" },
                  error: { type: "string" },
                  provided_value: {}
                }
              }
            }
          }
        }
      },
      examples: [
        {
          name: "successful_creation",
          scenario: "Habit created successfully",
          response: {
            status: "success",
            command: "habit.create",
            data: {
              habit_info: {
                id: "hab_abc123",
                name: "Morning meditation",
                category: "mindfulness",
                frequency: "daily",
                difficulty: "easy",
                created_at: "2025-01-15T08:30:00Z"
              }
            },
            metadata: {
              version: "2.0.0",
              execution_time: 0.145,
              tool_info: {
                name: "Create Habit",
                category: "habit_management",
                permissions_used: ["habit.write"]
              },
              input_validation: {
                schema_version: "2.0.0",
                validation_time: 12
              }
            }
          }
        }
      ]
    },
    side_effects: [
      {
        type: "write",
        description: "Creates new habit record in storage",
        reversible: true
      }
    ]
  },

  permissions: {
    required_roles: [Role.USER, Role.POWER_USER, Role.ADMIN],
    required_capabilities: [
      { name: "habit.write", scope: "self_only" }
    ],
    resource_access: [
      {
        resource_type: ResourceType.HABIT_DATA,
        access_mode: AccessMode.CREATE,
        scope_filter: "current_user"
      }
    ]
  },

  security_level: SecurityLevel.INTERNAL,

  implementation: {
    type: "function_call",
    module: "pm.tools.habit_tools",
    function: "create_habit",
    version_compatibility: ["2.0.0"]
  },

  validation: {
    input_validation: "strict",
    output_validation: "strict",
    permission_check: "required",
    rate_limiting: {
      max_calls_per_minute: 10,
      max_calls_per_hour: 100
    }
  },

  author: "PersonalManager Core Team",
  created_at: "2025-01-15T00:00:00Z",
  updated_at: "2025-01-15T00:00:00Z"
};
```

### Example Tool Definition: Project Status

```typescript
const PROJECT_STATUS_TOOL: ToolDefinition = {
  id: "project.status",
  name: "Get Project Status",
  category: ToolCategory.PROJECT_MANAGEMENT,
  version: "2.0.0",

  description: "Retrieve detailed status information for a specific project",

  function_signature: {
    input: {
      schema: {
        type: "object",
        required: ["project_name"],
        properties: {
          project_name: {
            type: "string",
            minLength: 1,
            description: "Name or partial name of the project"
          }
        }
      },
      examples: [
        {
          name: "exact_project_name",
          description: "Get status using exact project name",
          input: { project_name: "PersonalManager" },
          expected_output_type: "success"
        }
      ],
      required_fields: ["project_name"]
    },
    output: {
      success_schema: {
        type: "object",
        required: ["basic_info", "status_metrics"],
        properties: {
          basic_info: {
            type: "object",
            properties: {
              name: { type: "string" },
              path: { type: "string" },
              description: { type: "string" },
              current_phase: { type: "string" },
              team_members: { type: "array", items: { type: "string" } },
              target_completion: { type: "string", format: "date-time" }
            }
          },
          status_metrics: {
            type: "object",
            properties: {
              progress: { type: "number", minimum: 0, maximum: 100 },
              health: { type: "string", enum: ["excellent", "good", "warning", "critical"] },
              priority: { type: "string", enum: ["high", "medium", "low"] },
              last_updated: { type: "string", format: "date-time" }
            }
          },
          completed_work: { type: "array", items: { type: "string" } },
          next_actions: { type: "array", items: { type: "string" } },
          risks: { type: "array", items: { type: "string" } }
        }
      },
      error_schemas: {
        "TOOL_RESOURCE_NOT_FOUND": {
          type: "object",
          properties: {
            searched_name: { type: "string" },
            available_projects: { type: "array", items: { type: "string" } }
          }
        }
      }
    },
    side_effects: [
      {
        type: "read",
        description: "Reads project files and status information",
        reversible: false
      }
    ]
  },

  permissions: {
    required_roles: [Role.USER, Role.POWER_USER, Role.ADMIN],
    required_capabilities: [
      { name: "project.read", scope: "accessible" }
    ],
    resource_access: [
      {
        resource_type: ResourceType.PROJECT_DATA,
        access_mode: AccessMode.READ,
        scope_filter: "accessible_to_user"
      }
    ]
  },

  security_level: SecurityLevel.INTERNAL,

  implementation: {
    type: "function_call",
    module: "pm.tools.project_tools",
    function: "get_project_status",
    version_compatibility: ["2.0.0"]
  },

  validation: {
    input_validation: "strict",
    output_validation: "strict",
    permission_check: "required",
    rate_limiting: {
      max_calls_per_minute: 30,
      max_calls_per_hour: 500
    }
  },

  author: "PersonalManager Core Team",
  created_at: "2025-01-15T00:00:00Z",
  updated_at: "2025-01-15T00:00:00Z"
};
```

## Protocol Alignment Checklist

### AI_PROTOCOL_COMPATIBILITY.md Alignment

- ✅ Response format matches `AIResponse` interface structure
- ✅ Status codes follow `"success" | "failed" | "error"` pattern
- ✅ Error structure includes `code`, `message`, and `details` fields
- ✅ Metadata includes `version` and `execution_time` fields
- ✅ Command field follows dot notation convention
- ✅ Data field contains null for errors, structured data for success

### Explain Protocol Integration

- ✅ Compatible with explain protocol v1.0 structure
- ✅ Can be used as base for explanation tools
- ✅ Supports confidence metrics and reasoning chains
- ✅ Allows factor analysis and actionable insights
- ✅ Maintains explanation context patterns

### CLI Command Alignment

- ✅ Tools can be invoked from CLI commands
- ✅ Input validation matches CLI parameter validation
- ✅ Output format suitable for both JSON and human-readable display
- ✅ Error messages provide CLI command alternatives
- ✅ Help text generation from tool definitions

## Migration Timeline

### Phase 1: Foundation (Weeks 1-2)
- Tool registry implementation
- Basic v2 tool infrastructure
- Permission system foundation
- V1 compatibility layer

### Phase 2: Core Tools Migration (Weeks 3-4)
- Migrate habit management tools
- Migrate project management tools
- Migrate task management tools
- Update existing CLI commands

### Phase 3: Enhanced Features (Weeks 5-6)
- Advanced permission system
- Tool discovery API
- Enhanced error recovery
- Performance optimization

### Phase 4: Deprecation & Cleanup (Weeks 7-8)
- V1 deprecation warnings
- Documentation updates
- Final compatibility testing
- V1 removal planning

## Future Extensions

### Planned Enhancements

- **Interactive Tools**: Multi-step tool execution with user input
- **Async Tools**: Long-running tools with status callbacks
- **Composite Tools**: Tools that orchestrate multiple sub-tools
- **External Tools**: Tools provided by plugins or extensions
- **AI-Generated Tools**: Tools created dynamically by AI agents

### API Evolution Support

The v2 specification is designed to support:
- Schema evolution without breaking changes
- New permission models (ABAC, etc.)
- Advanced validation systems (semantic validation)
- Integration with external tool ecosystems
- Multi-tenant tool management

---

*This specification provides the foundation for a robust, secure, and extensible tool ecosystem in PersonalManager while maintaining compatibility with existing systems and protocols.*