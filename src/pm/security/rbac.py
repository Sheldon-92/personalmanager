"""Role-Based Access Control (RBAC) middleware for PersonalManager API.

Implements fine-grained permission control at the API route level with
support for roles, permissions, and context-aware access control.
"""

import functools
import hashlib
import hmac
import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Callable, Any
from uuid import uuid4


class Permission(Enum):
    """System permissions for API access control."""
    # Read permissions
    READ_TASKS = "tasks.read"
    READ_PROJECTS = "projects.read"
    READ_REPORTS = "reports.read"
    READ_METRICS = "metrics.read"
    READ_LOGS = "logs.read"

    # Write permissions
    WRITE_TASKS = "tasks.write"
    WRITE_PROJECTS = "projects.write"
    WRITE_REPORTS = "reports.write"

    # Admin permissions
    ADMIN_USERS = "admin.users"
    ADMIN_ROLES = "admin.roles"
    ADMIN_AUDIT = "admin.audit"
    ADMIN_SECURITY = "admin.security"

    # System permissions
    SYSTEM_CONFIG = "system.config"
    SYSTEM_BACKUP = "system.backup"
    SYSTEM_RESTORE = "system.restore"


class Role(Enum):
    """Predefined system roles with permission sets."""
    VIEWER = "viewer"
    USER = "user"
    DEVELOPER = "developer"
    ADMIN = "admin"
    SECURITY_ADMIN = "security_admin"
    SYSTEM = "system"


# Role to permissions mapping
ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.VIEWER: {
        Permission.READ_TASKS,
        Permission.READ_PROJECTS,
        Permission.READ_REPORTS,
    },
    Role.USER: {
        Permission.READ_TASKS,
        Permission.READ_PROJECTS,
        Permission.READ_REPORTS,
        Permission.READ_METRICS,
        Permission.WRITE_TASKS,
        Permission.WRITE_PROJECTS,
    },
    Role.DEVELOPER: {
        Permission.READ_TASKS,
        Permission.READ_PROJECTS,
        Permission.READ_REPORTS,
        Permission.READ_METRICS,
        Permission.READ_LOGS,
        Permission.WRITE_TASKS,
        Permission.WRITE_PROJECTS,
        Permission.WRITE_REPORTS,
    },
    Role.ADMIN: {
        Permission.READ_TASKS,
        Permission.READ_PROJECTS,
        Permission.READ_REPORTS,
        Permission.READ_METRICS,
        Permission.READ_LOGS,
        Permission.WRITE_TASKS,
        Permission.WRITE_PROJECTS,
        Permission.WRITE_REPORTS,
        Permission.ADMIN_USERS,
        Permission.ADMIN_ROLES,
        Permission.SYSTEM_CONFIG,
        Permission.SYSTEM_BACKUP,
        Permission.SYSTEM_RESTORE,
    },
    Role.SECURITY_ADMIN: {
        Permission.READ_LOGS,
        Permission.ADMIN_USERS,
        Permission.ADMIN_ROLES,
        Permission.ADMIN_AUDIT,
        Permission.ADMIN_SECURITY,
        Permission.SYSTEM_CONFIG,
    },
    Role.SYSTEM: set(Permission),  # System role has all permissions
}


@dataclass
class User:
    """User entity with roles and permissions."""
    id: str
    username: str
    email: str
    roles: Set[Role] = field(default_factory=set)
    custom_permissions: Set[Permission] = field(default_factory=set)
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    is_active: bool = True

    @property
    def permissions(self) -> Set[Permission]:
        """Get all effective permissions for the user."""
        perms = self.custom_permissions.copy()
        for role in self.roles:
            perms.update(ROLE_PERMISSIONS.get(role, set()))
        return perms

    def has_permission(self, permission: Permission) -> bool:
        """Check if user has specific permission."""
        return permission in self.permissions

    def has_any_permission(self, permissions: List[Permission]) -> bool:
        """Check if user has any of the specified permissions."""
        return any(self.has_permission(p) for p in permissions)

    def has_all_permissions(self, permissions: List[Permission]) -> bool:
        """Check if user has all specified permissions."""
        return all(self.has_permission(p) for p in permissions)


@dataclass
class Session:
    """User session with token management."""
    id: str
    user_id: str
    token: str
    created_at: datetime
    expires_at: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    @property
    def is_expired(self) -> bool:
        """Check if session has expired."""
        return datetime.utcnow() > self.expires_at

    @property
    def is_valid(self) -> bool:
        """Check if session is valid."""
        return not self.is_expired


class RBACMiddleware:
    """RBAC middleware for API request authorization."""

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize RBAC middleware.

        Args:
            config_path: Path to RBAC configuration file
        """
        self.config_path = config_path or Path.home() / ".pm" / "rbac.json"
        self.users: Dict[str, User] = {}
        self.sessions: Dict[str, Session] = {}
        self.secret_key = self._generate_secret_key()
        self._load_config()
        self._initialize_default_users()

    def _generate_secret_key(self) -> bytes:
        """Generate or load secret key for token signing."""
        key_path = Path.home() / ".pm" / ".rbac_secret"
        if key_path.exists():
            return key_path.read_bytes()
        else:
            key = hashlib.sha256(str(uuid4()).encode()).digest()
            key_path.parent.mkdir(parents=True, exist_ok=True)
            key_path.write_bytes(key)
            key_path.chmod(0o600)  # Restrict access to owner only
            return key

    def _load_config(self):
        """Load RBAC configuration from file."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    self._deserialize_users(config.get('users', []))
            except Exception as e:
                print(f"Warning: Failed to load RBAC config: {e}")

    def _save_config(self):
        """Save RBAC configuration to file."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            config = {
                'users': self._serialize_users(),
                'updated_at': datetime.utcnow().isoformat()
            }
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
            self.config_path.chmod(0o600)  # Restrict access
        except Exception as e:
            print(f"Warning: Failed to save RBAC config: {e}")

    def _serialize_users(self) -> List[Dict]:
        """Serialize users for storage."""
        return [
            {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'roles': [r.value for r in user.roles],
                'custom_permissions': [p.value for p in user.custom_permissions],
                'created_at': user.created_at.isoformat(),
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'is_active': user.is_active
            }
            for user in self.users.values()
        ]

    def _deserialize_users(self, users_data: List[Dict]):
        """Deserialize users from storage."""
        for data in users_data:
            user = User(
                id=data['id'],
                username=data['username'],
                email=data['email'],
                roles={Role(r) for r in data.get('roles', [])},
                custom_permissions={Permission(p) for p in data.get('custom_permissions', [])},
                created_at=datetime.fromisoformat(data['created_at']),
                last_login=datetime.fromisoformat(data['last_login']) if data.get('last_login') else None,
                is_active=data.get('is_active', True)
            )
            self.users[user.id] = user

    def _initialize_default_users(self):
        """Initialize default system users if none exist."""
        if not self.users:
            # Create default admin user
            admin = User(
                id=str(uuid4()),
                username='admin',
                email='admin@personal-manager.local',
                roles={Role.ADMIN, Role.SECURITY_ADMIN}
            )
            self.users[admin.id] = admin

            # Create system user for internal operations
            system = User(
                id=str(uuid4()),
                username='system',
                email='system@personal-manager.local',
                roles={Role.SYSTEM}
            )
            self.users[system.id] = system

            self._save_config()

    def create_user(self, username: str, email: str, roles: Set[Role]) -> User:
        """Create new user with specified roles.

        Args:
            username: User's username
            email: User's email
            roles: Set of roles to assign

        Returns:
            Created user object
        """
        user = User(
            id=str(uuid4()),
            username=username,
            email=email,
            roles=roles
        )
        self.users[user.id] = user
        self._save_config()
        return user

    def generate_token(self, user_id: str) -> str:
        """Generate secure session token for user.

        Args:
            user_id: User ID to generate token for

        Returns:
            Secure session token
        """
        timestamp = str(time.time()).encode()
        user_bytes = user_id.encode()
        token_data = timestamp + b':' + user_bytes
        signature = hmac.new(self.secret_key, token_data, hashlib.sha256).hexdigest()
        return f"{user_id}:{time.time()}:{signature}"

    def verify_token(self, token: str) -> Optional[str]:
        """Verify and extract user ID from token.

        Args:
            token: Session token to verify

        Returns:
            User ID if valid, None otherwise
        """
        try:
            parts = token.split(':')
            if len(parts) != 3:
                return None

            user_id, timestamp, signature = parts
            token_data = f"{timestamp}:{user_id}".encode()
            expected_sig = hmac.new(self.secret_key, token_data, hashlib.sha256).hexdigest()

            if hmac.compare_digest(signature, expected_sig):
                # Check token age (24 hour validity)
                token_age = time.time() - float(timestamp)
                if token_age < 86400:  # 24 hours
                    return user_id
        except Exception:
            pass
        return None

    def create_session(self, user: User, ip_address: Optional[str] = None,
                      user_agent: Optional[str] = None) -> Session:
        """Create new session for user.

        Args:
            user: User to create session for
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Created session object
        """
        session = Session(
            id=str(uuid4()),
            user_id=user.id,
            token=self.generate_token(user.id),
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=24),
            ip_address=ip_address,
            user_agent=user_agent
        )
        self.sessions[session.token] = session

        # Update user last login
        user.last_login = datetime.utcnow()
        self._save_config()

        return session

    def validate_session(self, token: str) -> Optional[User]:
        """Validate session token and return associated user.

        Args:
            token: Session token to validate

        Returns:
            User if session is valid, None otherwise
        """
        # Check if session exists and is valid
        session = self.sessions.get(token)
        if session and session.is_valid:
            return self.users.get(session.user_id)

        # Try to verify token directly
        user_id = self.verify_token(token)
        if user_id:
            return self.users.get(user_id)

        return None

    def authorize(self, token: str, permission: Permission) -> bool:
        """Authorize request based on token and required permission.

        Args:
            token: Session token
            permission: Required permission

        Returns:
            True if authorized, False otherwise
        """
        user = self.validate_session(token)
        if user and user.is_active:
            return user.has_permission(permission)
        return False

    def revoke_session(self, token: str):
        """Revoke a session token.

        Args:
            token: Session token to revoke
        """
        if token in self.sessions:
            del self.sessions[token]

    def cleanup_expired_sessions(self):
        """Remove expired sessions from memory."""
        expired = [token for token, session in self.sessions.items()
                  if session.is_expired]
        for token in expired:
            del self.sessions[token]


def require_permission(permission: Permission):
    """Decorator for protecting functions with permission requirements.

    Args:
        permission: Required permission for access

    Returns:
        Decorated function with permission check
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Extract token from kwargs or context
            token = kwargs.get('auth_token') or kwargs.get('token')
            if not token:
                raise PermissionError("Authentication required")

            # Get RBAC instance (should be initialized globally)
            rbac = kwargs.get('rbac') or getattr(wrapper, '_rbac', None)
            if not rbac:
                rbac = RBACMiddleware()
                wrapper._rbac = rbac

            # Check permission
            if not rbac.authorize(token, permission):
                raise PermissionError(f"Permission denied: {permission.value} required")

            # Get user for context
            user = rbac.validate_session(token)
            kwargs['current_user'] = user

            return func(*args, **kwargs)
        return wrapper
    return decorator


# Route to permission mapping for API endpoints
ROUTE_PERMISSIONS: Dict[str, Permission] = {
    "/api/v1/tasks": Permission.READ_TASKS,
    "/api/v1/projects": Permission.READ_PROJECTS,
    "/api/v1/reports": Permission.READ_REPORTS,
    "/api/v1/metrics": Permission.READ_METRICS,
    "/api/v1/admin/users": Permission.ADMIN_USERS,
    "/api/v1/admin/roles": Permission.ADMIN_ROLES,
    "/api/v1/admin/audit": Permission.ADMIN_AUDIT,
    "/api/v1/system/config": Permission.SYSTEM_CONFIG,
    "/api/v1/system/backup": Permission.SYSTEM_BACKUP,
}