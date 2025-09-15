"""Security module for PersonalManager.

Provides RBAC, audit logging, secrets management, and security scanning.
"""

from .rbac import RBACMiddleware, Permission, Role, require_permission
from .audit import AuditLogger, AuditEvent
from .secrets import SecretsManager
from .scanner import SecurityScanner
from .sbom_generator import SBOMGenerator

__all__ = [
    'RBACMiddleware',
    'Permission',
    'Role',
    'require_permission',
    'AuditLogger',
    'AuditEvent',
    'SecretsManager',
    'SecurityScanner',
    'SBOMGenerator'
]

__version__ = '1.0.0'