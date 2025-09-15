"""Audit logging system for PersonalManager.

Provides comprehensive audit trail for security events, API access,
data modifications, and system operations with tamper-proof logging.
"""

import hashlib
import json
import logging
import logging.handlers
import sqlite3
import threading
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from uuid import uuid4


class AuditEventType(Enum):
    """Types of audit events."""
    # Authentication events
    AUTH_LOGIN = "auth.login"
    AUTH_LOGOUT = "auth.logout"
    AUTH_FAILED = "auth.failed"
    AUTH_TOKEN_CREATED = "auth.token_created"
    AUTH_TOKEN_REVOKED = "auth.token_revoked"

    # Authorization events
    AUTHZ_GRANTED = "authz.granted"
    AUTHZ_DENIED = "authz.denied"
    AUTHZ_ESCALATION = "authz.escalation"

    # Data access events
    DATA_READ = "data.read"
    DATA_WRITE = "data.write"
    DATA_DELETE = "data.delete"
    DATA_EXPORT = "data.export"

    # API events
    API_REQUEST = "api.request"
    API_RESPONSE = "api.response"
    API_ERROR = "api.error"

    # User management events
    USER_CREATED = "user.created"
    USER_MODIFIED = "user.modified"
    USER_DELETED = "user.deleted"
    USER_ROLE_CHANGED = "user.role_changed"

    # System events
    SYSTEM_START = "system.start"
    SYSTEM_STOP = "system.stop"
    SYSTEM_CONFIG_CHANGED = "system.config_changed"
    SYSTEM_BACKUP = "system.backup"
    SYSTEM_RESTORE = "system.restore"

    # Security events
    SECURITY_VIOLATION = "security.violation"
    SECURITY_SCAN = "security.scan"
    SECURITY_ALERT = "security.alert"


class AuditSeverity(Enum):
    """Severity levels for audit events."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Audit event data structure."""
    id: str
    timestamp: datetime
    event_type: AuditEventType
    severity: AuditSeverity
    user_id: Optional[str]
    session_id: Optional[str]
    ip_address: Optional[str]
    resource: Optional[str]
    action: str
    outcome: str
    details: Dict[str, Any]
    hash: Optional[str] = None

    def calculate_hash(self, previous_hash: str = "") -> str:
        """Calculate cryptographic hash for event integrity.

        Args:
            previous_hash: Hash of previous event for chain integrity

        Returns:
            SHA256 hash of event data
        """
        event_data = {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'event_type': self.event_type.value,
            'severity': self.severity.value,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'ip_address': self.ip_address,
            'resource': self.resource,
            'action': self.action,
            'outcome': self.outcome,
            'details': json.dumps(self.details, sort_keys=True),
            'previous_hash': previous_hash
        }
        data_string = json.dumps(event_data, sort_keys=True)
        return hashlib.sha256(data_string.encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'event_type': self.event_type.value,
            'severity': self.severity.value,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'ip_address': self.ip_address,
            'resource': self.resource,
            'action': self.action,
            'outcome': self.outcome,
            'details': self.details,
            'hash': self.hash
        }


class AuditLogger:
    """Centralized audit logging system with integrity protection."""

    def __init__(self, db_path: Optional[Path] = None,
                 log_file: Optional[Path] = None):
        """Initialize audit logger.

        Args:
            db_path: Path to SQLite database for audit storage
            log_file: Path to backup log file
        """
        self.db_path = db_path or Path.home() / ".pm" / "audit.db"
        self.log_file = log_file or Path.home() / ".pm" / "logs" / "audit.log"
        self._lock = threading.Lock()
        self._previous_hash = ""
        self._init_database()
        self._init_file_logger()

    def _init_database(self):
        """Initialize SQLite database for audit storage."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_events (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    user_id TEXT,
                    session_id TEXT,
                    ip_address TEXT,
                    resource TEXT,
                    action TEXT NOT NULL,
                    outcome TEXT NOT NULL,
                    details TEXT,
                    hash TEXT NOT NULL,
                    previous_hash TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create indices for common queries
            conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON audit_events(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_event_type ON audit_events(event_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_user_id ON audit_events(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_severity ON audit_events(severity)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_resource ON audit_events(resource)")

            # Get last event hash for chain integrity
            cursor = conn.execute(
                "SELECT hash FROM audit_events ORDER BY created_at DESC LIMIT 1"
            )
            result = cursor.fetchone()
            if result:
                self._previous_hash = result[0]

    def _init_file_logger(self):
        """Initialize file-based backup logger."""
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        # Configure file handler
        self.file_logger = logging.getLogger('audit')
        self.file_logger.setLevel(logging.INFO)

        # Create file handler with rotation
        handler = logging.handlers.RotatingFileHandler(
            str(self.log_file),
            maxBytes=10 * 1024 * 1024,  # 10MB per file
            backupCount=10
        )

        # Set format
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        self.file_logger.addHandler(handler)

    def log_event(self,
                  event_type: AuditEventType,
                  action: str,
                  outcome: str,
                  severity: AuditSeverity = AuditSeverity.INFO,
                  user_id: Optional[str] = None,
                  session_id: Optional[str] = None,
                  ip_address: Optional[str] = None,
                  resource: Optional[str] = None,
                  details: Optional[Dict[str, Any]] = None) -> AuditEvent:
        """Log an audit event.

        Args:
            event_type: Type of event
            action: Action performed
            outcome: Outcome of action (success/failure/error)
            severity: Event severity level
            user_id: User ID if applicable
            session_id: Session ID if applicable
            ip_address: Client IP address
            resource: Resource accessed/modified
            details: Additional event details

        Returns:
            Created audit event
        """
        with self._lock:
            # Create event
            event = AuditEvent(
                id=str(uuid4()),
                timestamp=datetime.utcnow(),
                event_type=event_type,
                severity=severity,
                user_id=user_id,
                session_id=session_id,
                ip_address=ip_address,
                resource=resource,
                action=action,
                outcome=outcome,
                details=details or {}
            )

            # Calculate hash with chain integrity
            event.hash = event.calculate_hash(self._previous_hash)

            # Store in database
            self._store_event(event)

            # Backup to file
            self._log_to_file(event)

            # Update chain
            self._previous_hash = event.hash

            return event

    def _store_event(self, event: AuditEvent):
        """Store event in database.

        Args:
            event: Audit event to store
        """
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("""
                INSERT INTO audit_events (
                    id, timestamp, event_type, severity, user_id,
                    session_id, ip_address, resource, action, outcome,
                    details, hash, previous_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event.id,
                event.timestamp.isoformat(),
                event.event_type.value,
                event.severity.value,
                event.user_id,
                event.session_id,
                event.ip_address,
                event.resource,
                event.action,
                event.outcome,
                json.dumps(event.details),
                event.hash,
                self._previous_hash
            ))

    def _log_to_file(self, event: AuditEvent):
        """Log event to backup file.

        Args:
            event: Audit event to log
        """
        log_level = {
            AuditSeverity.DEBUG: logging.DEBUG,
            AuditSeverity.INFO: logging.INFO,
            AuditSeverity.WARNING: logging.WARNING,
            AuditSeverity.ERROR: logging.ERROR,
            AuditSeverity.CRITICAL: logging.CRITICAL
        }.get(event.severity, logging.INFO)

        self.file_logger.log(
            log_level,
            f"[{event.event_type.value}] {event.action} - {event.outcome} "
            f"(User: {event.user_id}, IP: {event.ip_address}, Resource: {event.resource})"
        )

    def query_events(self,
                    start_time: Optional[datetime] = None,
                    end_time: Optional[datetime] = None,
                    event_types: Optional[List[AuditEventType]] = None,
                    user_id: Optional[str] = None,
                    resource: Optional[str] = None,
                    severity: Optional[AuditSeverity] = None,
                    limit: int = 100) -> List[AuditEvent]:
        """Query audit events with filters.

        Args:
            start_time: Start time for query
            end_time: End time for query
            event_types: Filter by event types
            user_id: Filter by user ID
            resource: Filter by resource
            severity: Minimum severity level
            limit: Maximum number of results

        Returns:
            List of matching audit events
        """
        query = "SELECT * FROM audit_events WHERE 1=1"
        params = []

        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time.isoformat())

        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time.isoformat())

        if event_types:
            placeholders = ','.join(['?' for _ in event_types])
            query += f" AND event_type IN ({placeholders})"
            params.extend([et.value for et in event_types])

        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)

        if resource:
            query += " AND resource LIKE ?"
            params.append(f"%{resource}%")

        if severity:
            # Get severity levels at or above specified level
            severity_order = {
                AuditSeverity.DEBUG: 0,
                AuditSeverity.INFO: 1,
                AuditSeverity.WARNING: 2,
                AuditSeverity.ERROR: 3,
                AuditSeverity.CRITICAL: 4
            }
            min_level = severity_order[severity]
            allowed_severities = [s.value for s, level in severity_order.items()
                                 if level >= min_level]
            placeholders = ','.join(['?' for _ in allowed_severities])
            query += f" AND severity IN ({placeholders})"
            params.extend(allowed_severities)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        events = []
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)

            for row in cursor:
                event = AuditEvent(
                    id=row['id'],
                    timestamp=datetime.fromisoformat(row['timestamp']),
                    event_type=AuditEventType(row['event_type']),
                    severity=AuditSeverity(row['severity']),
                    user_id=row['user_id'],
                    session_id=row['session_id'],
                    ip_address=row['ip_address'],
                    resource=row['resource'],
                    action=row['action'],
                    outcome=row['outcome'],
                    details=json.loads(row['details']),
                    hash=row['hash']
                )
                events.append(event)

        return events

    def verify_integrity(self, start_time: Optional[datetime] = None) -> tuple[bool, List[str]]:
        """Verify audit log integrity.

        Args:
            start_time: Start time for verification

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        previous_hash = ""

        query = "SELECT * FROM audit_events"
        params = []

        if start_time:
            query += " WHERE timestamp >= ?"
            params.append(start_time.isoformat())

        query += " ORDER BY created_at ASC"

        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)

            for row in cursor:
                # Reconstruct event
                event = AuditEvent(
                    id=row['id'],
                    timestamp=datetime.fromisoformat(row['timestamp']),
                    event_type=AuditEventType(row['event_type']),
                    severity=AuditSeverity(row['severity']),
                    user_id=row['user_id'],
                    session_id=row['session_id'],
                    ip_address=row['ip_address'],
                    resource=row['resource'],
                    action=row['action'],
                    outcome=row['outcome'],
                    details=json.loads(row['details'])
                )

                # Verify hash
                expected_hash = event.calculate_hash(previous_hash)
                if expected_hash != row['hash']:
                    errors.append(f"Hash mismatch for event {row['id']}")

                # Check chain integrity
                if row['previous_hash'] != previous_hash:
                    errors.append(f"Chain broken at event {row['id']}")

                previous_hash = row['hash']

        return len(errors) == 0, errors

    def generate_compliance_report(self,
                                  start_time: datetime,
                                  end_time: datetime) -> Dict[str, Any]:
        """Generate compliance report for audit events.

        Args:
            start_time: Report start time
            end_time: Report end time

        Returns:
            Compliance report dictionary
        """
        # Query all events in timeframe
        events = self.query_events(
            start_time=start_time,
            end_time=end_time,
            limit=10000
        )

        # Verify integrity
        is_valid, integrity_errors = self.verify_integrity(start_time)

        # Analyze events
        stats = {
            'total_events': len(events),
            'integrity_valid': is_valid,
            'integrity_errors': integrity_errors,
            'by_type': {},
            'by_severity': {},
            'by_user': {},
            'security_events': [],
            'failed_authentications': [],
            'permission_denials': [],
            'data_access': []
        }

        for event in events:
            # Count by type
            event_type = event.event_type.value
            stats['by_type'][event_type] = stats['by_type'].get(event_type, 0) + 1

            # Count by severity
            severity = event.severity.value
            stats['by_severity'][severity] = stats['by_severity'].get(severity, 0) + 1

            # Count by user
            if event.user_id:
                stats['by_user'][event.user_id] = stats['by_user'].get(event.user_id, 0) + 1

            # Collect security events
            if event.event_type in [AuditEventType.SECURITY_VIOLATION,
                                   AuditEventType.SECURITY_ALERT]:
                stats['security_events'].append(event.to_dict())

            # Collect failed auth
            if event.event_type == AuditEventType.AUTH_FAILED:
                stats['failed_authentications'].append(event.to_dict())

            # Collect permission denials
            if event.event_type == AuditEventType.AUTHZ_DENIED:
                stats['permission_denials'].append(event.to_dict())

            # Collect data access
            if event.event_type in [AuditEventType.DATA_READ,
                                   AuditEventType.DATA_WRITE,
                                   AuditEventType.DATA_DELETE]:
                stats['data_access'].append(event.to_dict())

        return {
            'report_id': str(uuid4()),
            'generated_at': datetime.utcnow().isoformat(),
            'period': {
                'start': start_time.isoformat(),
                'end': end_time.isoformat()
            },
            'statistics': stats,
            'recommendations': self._generate_recommendations(stats)
        }

    def _generate_recommendations(self, stats: Dict[str, Any]) -> List[str]:
        """Generate security recommendations based on audit analysis.

        Args:
            stats: Audit statistics

        Returns:
            List of recommendations
        """
        recommendations = []

        # Check integrity
        if not stats['integrity_valid']:
            recommendations.append("CRITICAL: Audit log integrity compromised. Investigate immediately.")

        # Check security events
        if len(stats['security_events']) > 0:
            recommendations.append(f"Review {len(stats['security_events'])} security events detected.")

        # Check failed auth
        failed_auth = len(stats['failed_authentications'])
        if failed_auth > 10:
            recommendations.append(f"High number of failed authentications ({failed_auth}). Consider implementing rate limiting.")

        # Check permission denials
        denials = len(stats['permission_denials'])
        if denials > 20:
            recommendations.append(f"Frequent permission denials ({denials}). Review user roles and permissions.")

        return recommendations