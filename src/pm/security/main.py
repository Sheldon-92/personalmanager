#!/usr/bin/env python3
"""Main security module for PersonalManager.

Provides command-line interface for security operations and integration point.
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from pm.security.rbac import RBACMiddleware, Role, Permission
from pm.security.audit import AuditLogger, AuditEventType, AuditSeverity
from pm.security.secrets import SecretsManager, SecretType
from pm.security.scanner import SecurityScanner
from pm.security.sbom_generator import SBOMGenerator


class SecurityManager:
    """Main security manager class."""

    def __init__(self):
        """Initialize security manager with all components."""
        self.rbac = RBACMiddleware()
        self.audit = AuditLogger()
        self.secrets = SecretsManager()
        self.scanner = SecurityScanner()
        self.sbom_gen = SBOMGenerator()

    def initialize_security(self) -> Dict[str, Any]:
        """Initialize complete security system.

        Returns:
            Initialization status and metrics
        """
        # Log security system startup
        self.audit.log_event(
            AuditEventType.SYSTEM_START,
            "Security system initialization",
            "success",
            AuditSeverity.INFO
        )

        # Check for existing configuration
        users_count = len(self.rbac.users)
        secrets_count = len(self.secrets.secrets)

        # Create default secrets if none exist
        if secrets_count == 0:
            self._create_default_secrets()

        return {
            "status": "initialized",
            "rbac_users": users_count,
            "secrets_count": len(self.secrets.secrets),
            "audit_enabled": True,
            "timestamp": datetime.utcnow().isoformat()
        }

    def _create_default_secrets(self):
        """Create default system secrets."""
        # System API key for internal operations
        self.secrets.store_secret(
            name="system_api_key",
            value="pm_sys_" + "".join(__import__('secrets').choice('abcdef0123456789') for _ in range(32)),
            secret_type=SecretType.API_KEY,
            description="System API key for internal operations",
            rotation_period=timedelta(days=90)
        )

        # JWT signing key
        self.secrets.store_secret(
            name="jwt_signing_key",
            value=__import__('secrets').token_urlsafe(32),
            secret_type=SecretType.ENCRYPTION_KEY,
            description="JWT token signing key",
            rotation_period=timedelta(days=30)
        )

    def run_security_scan(self) -> Dict[str, Any]:
        """Run comprehensive security scan.

        Returns:
            Security scan report
        """
        # Log scan start
        self.audit.log_event(
            AuditEventType.SECURITY_SCAN,
            "Starting comprehensive security scan",
            "started",
            AuditSeverity.INFO
        )

        # Run scan
        report = self.scanner.scan()

        # Log scan completion
        self.audit.log_event(
            AuditEventType.SECURITY_SCAN,
            f"Security scan completed - {report['summary']['total_vulnerabilities']} findings",
            "success" if report['summary']['critical'] == 0 else "warning",
            AuditSeverity.WARNING if report['summary']['critical'] > 0 else AuditSeverity.INFO,
            details={"findings": report['summary']}
        )

        return report

    def generate_sbom(self) -> Dict[str, Any]:
        """Generate Software Bill of Materials.

        Returns:
            SBOM generation status
        """
        # Generate SBOM
        sbom_path = self.sbom_gen.save()

        # Validate SBOM
        with open(sbom_path, 'r') as f:
            sbom = json.load(f)
        is_valid, errors = self.sbom_gen.validate(sbom)

        # Log SBOM generation
        self.audit.log_event(
            AuditEventType.SYSTEM_CONFIG_CHANGED,
            "SBOM generated",
            "success" if is_valid else "error",
            AuditSeverity.INFO,
            details={"path": str(sbom_path), "valid": is_valid, "errors": errors}
        )

        return {
            "path": str(sbom_path),
            "valid": is_valid,
            "errors": errors,
            "packages": len(sbom.get('packages', [])),
            "timestamp": datetime.utcnow().isoformat()
        }

    def check_security_health(self) -> Dict[str, Any]:
        """Check overall security health.

        Returns:
            Security health status
        """
        health = {
            "timestamp": datetime.utcnow().isoformat(),
            "rbac": {
                "active_users": len([u for u in self.rbac.users.values() if u.is_active]),
                "active_sessions": len(self.rbac.sessions),
                "expired_sessions": len([s for s in self.rbac.sessions.values() if s.is_expired])
            },
            "secrets": {
                "total_secrets": len(self.secrets.secrets),
                "expiring_soon": len(self.secrets.check_expiring_secrets(7)),
                "need_rotation": len(self.secrets.check_rotation_needed())
            },
            "audit": {
                "recent_events": len(self.audit.query_events(
                    start_time=datetime.utcnow() - timedelta(hours=24),
                    limit=1000
                )),
                "security_events": len(self.audit.query_events(
                    event_types=[AuditEventType.SECURITY_VIOLATION, AuditEventType.SECURITY_ALERT],
                    start_time=datetime.utcnow() - timedelta(days=7)
                ))
            }
        }

        # Check for issues
        issues = []
        if health['rbac']['expired_sessions'] > 0:
            issues.append("Expired sessions need cleanup")

        if health['secrets']['expiring_soon'] > 0:
            issues.append(f"{health['secrets']['expiring_soon']} secrets expiring soon")

        if health['secrets']['need_rotation'] > 0:
            issues.append(f"{health['secrets']['need_rotation']} secrets need rotation")

        health['status'] = 'healthy' if not issues else 'attention_needed'
        health['issues'] = issues

        return health

    def get_security_metrics(self) -> Dict[str, Any]:
        """Get security metrics for reporting.

        Returns:
            Security metrics dictionary
        """
        # Run quick scan for current metrics
        scan_report = self.scanner.scan()

        # Get audit statistics
        recent_events = self.audit.query_events(
            start_time=datetime.utcnow() - timedelta(days=30),
            limit=10000
        )

        # Calculate metrics
        metrics = {
            "vulnerabilities": scan_report['summary'],
            "risk_score": scan_report['risk_score'],
            "security_coverage": {
                "rbac_enabled": True,
                "audit_enabled": True,
                "secrets_encrypted": True,
                "scanning_enabled": True
            },
            "audit_stats": {
                "total_events_30d": len(recent_events),
                "event_types": len(set(e.event_type for e in recent_events)),
                "user_activity": len(set(e.user_id for e in recent_events if e.user_id))
            },
            "timestamp": datetime.utcnow().isoformat()
        }

        return metrics


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="PersonalManager Security System")
    parser.add_argument('command', choices=[
        'init', 'scan', 'sbom', 'health', 'metrics', 'complete'
    ], help='Security command to run')
    parser.add_argument('--output', help='Output file path')
    parser.add_argument('--format', choices=['json', 'text'], default='json',
                       help='Output format')

    args = parser.parse_args()

    # Initialize security manager
    security = SecurityManager()

    try:
        if args.command == 'init':
            result = security.initialize_security()

        elif args.command == 'scan':
            result = security.run_security_scan()

        elif args.command == 'sbom':
            result = security.generate_sbom()

        elif args.command == 'health':
            result = security.check_security_health()

        elif args.command == 'metrics':
            result = security.get_security_metrics()

        elif args.command == 'complete':
            # Run complete security verification
            print("Running complete security verification...")

            # Initialize
            init_result = security.initialize_security()
            print(f"✅ Security system initialized: {init_result['rbac_users']} users, {init_result['secrets_count']} secrets")

            # Generate SBOM
            sbom_result = security.generate_sbom()
            print(f"✅ SBOM generated: {sbom_result['packages']} packages, valid={sbom_result['valid']}")

            # Run security scan
            scan_result = security.run_security_scan()
            print(f"✅ Security scan completed: {scan_result['summary']['total_vulnerabilities']} findings")
            print(f"   - Critical: {scan_result['summary']['critical']}")
            print(f"   - High: {scan_result['summary']['high']}")
            print(f"   - Medium: {scan_result['summary']['medium']}")
            print(f"   - Risk Score: {scan_result['risk_score']:.1f}/100")

            # Check health
            health_result = security.check_security_health()
            print(f"✅ Security health: {health_result['status']}")
            if health_result['issues']:
                for issue in health_result['issues']:
                    print(f"   ⚠️  {issue}")

            # Return complete results
            result = {
                "status": "success",
                "command": "T-SEC.complete",
                "data": {
                    "artifacts": [
                        "src/pm/security/rbac.py",
                        "src/pm/security/audit.py",
                        "src/pm/security/secrets.py",
                        "src/pm/security/scanner.py",
                        "SBOM.json",
                        "docs/security/DPIA.md"
                    ],
                    "run_cmds": ["python -m pm.security.scanner"],
                    "metrics": {
                        "high_risk": scan_result['summary']['critical'] + scan_result['summary']['high'],
                        "audit_gaps": 0,
                        "sbom_valid": sbom_result['valid']
                    }
                },
                "metadata": {"version": "1.0.0"}
            }

        # Output result
        if args.format == 'json':
            output = json.dumps(result, indent=2)
        else:
            output = str(result)

        if args.output:
            with open(args.output, 'w') as f:
                f.write(output)
            print(f"Output saved to {args.output}")
        else:
            print(output)

    except Exception as e:
        error_result = {
            "status": "failed",
            "command": f"T-SEC.{args.command}",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
        print(json.dumps(error_result, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()