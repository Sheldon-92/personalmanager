"""Security scanner for PersonalManager.

Performs comprehensive security scanning including vulnerability detection,
dependency checking, code analysis, and configuration auditing.
"""

import ast
import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from uuid import uuid4


class VulnerabilityLevel(Enum):
    """Security vulnerability severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class VulnerabilityType(Enum):
    """Types of security vulnerabilities."""
    # Code vulnerabilities
    SQL_INJECTION = "sql_injection"
    COMMAND_INJECTION = "command_injection"
    PATH_TRAVERSAL = "path_traversal"
    XSS = "cross_site_scripting"
    XXE = "xml_external_entity"
    SSRF = "server_side_request_forgery"

    # Authentication/Authorization
    WEAK_AUTHENTICATION = "weak_authentication"
    MISSING_AUTHORIZATION = "missing_authorization"
    INSECURE_SESSION = "insecure_session"

    # Cryptography
    WEAK_CRYPTO = "weak_cryptography"
    HARDCODED_SECRET = "hardcoded_secret"
    INSECURE_RANDOM = "insecure_random"

    # Configuration
    DEBUG_ENABLED = "debug_enabled"
    INSECURE_CONFIG = "insecure_configuration"
    MISSING_SECURITY_HEADER = "missing_security_header"

    # Dependencies
    VULNERABLE_DEPENDENCY = "vulnerable_dependency"
    OUTDATED_DEPENDENCY = "outdated_dependency"

    # Data exposure
    SENSITIVE_DATA_EXPOSURE = "sensitive_data_exposure"
    INFORMATION_DISCLOSURE = "information_disclosure"

    # Other
    RACE_CONDITION = "race_condition"
    DENIAL_OF_SERVICE = "denial_of_service"


@dataclass
class Vulnerability:
    """Security vulnerability finding."""
    id: str
    type: VulnerabilityType
    level: VulnerabilityLevel
    title: str
    description: str
    file_path: Optional[str]
    line_number: Optional[int]
    code_snippet: Optional[str]
    cwe_id: Optional[str]
    cvss_score: Optional[float]
    remediation: str
    references: List[str]
    metadata: Dict[str, Any]


class SecurityScanner:
    """Comprehensive security scanner for code and configuration."""

    def __init__(self, project_root: Optional[Path] = None):
        """Initialize security scanner.

        Args:
            project_root: Root directory of project to scan
        """
        self.project_root = project_root or Path.cwd()
        self.vulnerabilities: List[Vulnerability] = []
        self.scan_id = str(uuid4())
        self.scan_time = datetime.utcnow()

    def scan(self,
             include_code: bool = True,
             include_dependencies: bool = True,
             include_config: bool = True,
             include_secrets: bool = True) -> Dict[str, Any]:
        """Perform comprehensive security scan.

        Args:
            include_code: Scan source code
            include_dependencies: Scan dependencies
            include_config: Scan configuration
            include_secrets: Scan for secrets

        Returns:
            Scan results dictionary
        """
        self.vulnerabilities = []

        if include_code:
            self._scan_code()

        if include_dependencies:
            self._scan_dependencies()

        if include_config:
            self._scan_configuration()

        if include_secrets:
            self._scan_secrets()

        return self._generate_report()

    def _scan_code(self):
        """Scan source code for vulnerabilities."""
        # Find all Python files
        python_files = list(self.project_root.rglob("*.py"))

        for file_path in python_files:
            # Skip test files and virtual environments
            if any(part in file_path.parts for part in ['venv', '.venv', 'test', '__pycache__']):
                continue

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Parse AST for analysis
                tree = ast.parse(content, filename=str(file_path))

                # Run various security checks
                self._check_sql_injection(file_path, content, tree)
                self._check_command_injection(file_path, content, tree)
                self._check_path_traversal(file_path, content, tree)
                self._check_weak_crypto(file_path, content, tree)
                self._check_insecure_random(file_path, content, tree)
                self._check_hardcoded_secrets(file_path, content)
                self._check_dangerous_functions(file_path, content, tree)

            except Exception as e:
                print(f"Error scanning {file_path}: {e}")

    def _check_sql_injection(self, file_path: Path, content: str, tree: ast.AST):
        """Check for SQL injection vulnerabilities."""
        # Look for string formatting in SQL queries
        sql_patterns = [
            r'(SELECT|INSERT|UPDATE|DELETE|DROP).*%[s|d]',
            r'(SELECT|INSERT|UPDATE|DELETE|DROP).*\.format\(',
            r'(SELECT|INSERT|UPDATE|DELETE|DROP).*\+\s*["\']',
            r'execute\(["\'].*%[s|d]',
            r'execute\(["\'].*\.format\(',
        ]

        for pattern in sql_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                self.vulnerabilities.append(Vulnerability(
                    id=str(uuid4()),
                    type=VulnerabilityType.SQL_INJECTION,
                    level=VulnerabilityLevel.HIGH,
                    title="Potential SQL Injection",
                    description="SQL query appears to use string formatting which may be vulnerable to injection",
                    file_path=str(file_path),
                    line_number=line_num,
                    code_snippet=match.group(0)[:100],
                    cwe_id="CWE-89",
                    cvss_score=8.6,
                    remediation="Use parameterized queries or prepared statements instead of string formatting",
                    references=[
                        "https://owasp.org/www-community/attacks/SQL_Injection",
                        "https://cwe.mitre.org/data/definitions/89.html"
                    ],
                    metadata={"pattern": pattern}
                ))

    def _check_command_injection(self, file_path: Path, content: str, tree: ast.AST):
        """Check for command injection vulnerabilities."""
        dangerous_functions = ['os.system', 'subprocess.call', 'subprocess.run',
                             'subprocess.Popen', 'eval', 'exec']

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_function_name(node)
                if func_name in dangerous_functions:
                    # Check if using user input
                    if self._uses_variable_input(node):
                        self.vulnerabilities.append(Vulnerability(
                            id=str(uuid4()),
                            type=VulnerabilityType.COMMAND_INJECTION,
                            level=VulnerabilityLevel.CRITICAL,
                            title="Potential Command Injection",
                            description=f"Use of {func_name} with variable input may allow command injection",
                            file_path=str(file_path),
                            line_number=node.lineno,
                            code_snippet=None,
                            cwe_id="CWE-78",
                            cvss_score=9.8,
                            remediation="Use subprocess with shell=False and pass arguments as a list",
                            references=[
                                "https://owasp.org/www-community/attacks/Command_Injection",
                                "https://cwe.mitre.org/data/definitions/78.html"
                            ],
                            metadata={"function": func_name}
                        ))

    def _check_path_traversal(self, file_path: Path, content: str, tree: ast.AST):
        """Check for path traversal vulnerabilities."""
        file_functions = ['open', 'Path', 'os.path.join', 'pathlib.Path']

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_function_name(node)
                if func_name in file_functions:
                    # Check if path comes from user input
                    if self._uses_variable_input(node):
                        self.vulnerabilities.append(Vulnerability(
                            id=str(uuid4()),
                            type=VulnerabilityType.PATH_TRAVERSAL,
                            level=VulnerabilityLevel.HIGH,
                            title="Potential Path Traversal",
                            description="File path appears to use user input without validation",
                            file_path=str(file_path),
                            line_number=node.lineno,
                            code_snippet=None,
                            cwe_id="CWE-22",
                            cvss_score=7.5,
                            remediation="Validate and sanitize file paths, use os.path.abspath() and check against allowed directories",
                            references=[
                                "https://owasp.org/www-community/attacks/Path_Traversal",
                                "https://cwe.mitre.org/data/definitions/22.html"
                            ],
                            metadata={"function": func_name}
                        ))

    def _check_weak_crypto(self, file_path: Path, content: str, tree: ast.AST):
        """Check for weak cryptography usage."""
        weak_algorithms = {
            'md5': (VulnerabilityLevel.HIGH, "MD5 is cryptographically broken"),
            'sha1': (VulnerabilityLevel.MEDIUM, "SHA1 is deprecated for security use"),
            'DES': (VulnerabilityLevel.HIGH, "DES encryption is weak"),
            'RC4': (VulnerabilityLevel.HIGH, "RC4 cipher is broken"),
        }

        for algo, (level, desc) in weak_algorithms.items():
            if algo.lower() in content.lower():
                # Find line number
                for i, line in enumerate(content.split('\n'), 1):
                    if algo.lower() in line.lower():
                        self.vulnerabilities.append(Vulnerability(
                            id=str(uuid4()),
                            type=VulnerabilityType.WEAK_CRYPTO,
                            level=level,
                            title=f"Weak Cryptographic Algorithm: {algo}",
                            description=desc,
                            file_path=str(file_path),
                            line_number=i,
                            code_snippet=line.strip()[:100],
                            cwe_id="CWE-327",
                            cvss_score=7.4 if level == VulnerabilityLevel.HIGH else 5.3,
                            remediation="Use strong cryptographic algorithms like SHA-256, AES, or RSA with appropriate key sizes",
                            references=[
                                "https://owasp.org/www-community/vulnerabilities/Weak_Cryptography",
                                "https://cwe.mitre.org/data/definitions/327.html"
                            ],
                            metadata={"algorithm": algo}
                        ))

    def _check_insecure_random(self, file_path: Path, content: str, tree: ast.AST):
        """Check for insecure random number generation."""
        if 'random.' in content and any(x in content for x in ['token', 'password', 'key', 'secret']):
            for node in ast.walk(tree):
                if isinstance(node, ast.Attribute):
                    if hasattr(node.value, 'id') and node.value.id == 'random':
                        self.vulnerabilities.append(Vulnerability(
                            id=str(uuid4()),
                            type=VulnerabilityType.INSECURE_RANDOM,
                            level=VulnerabilityLevel.MEDIUM,
                            title="Insecure Random Number Generator",
                            description="Using random module for security-sensitive operations",
                            file_path=str(file_path),
                            line_number=node.lineno if hasattr(node, 'lineno') else None,
                            code_snippet=None,
                            cwe_id="CWE-330",
                            cvss_score=5.3,
                            remediation="Use secrets module or os.urandom() for cryptographic randomness",
                            references=[
                                "https://docs.python.org/3/library/secrets.html",
                                "https://cwe.mitre.org/data/definitions/330.html"
                            ],
                            metadata={}
                        ))
                        break

    def _check_hardcoded_secrets(self, file_path: Path, content: str):
        """Check for hardcoded secrets and credentials."""
        # Patterns for potential secrets
        secret_patterns = [
            (r'["\'](?:api[_-]?key|apikey)["\'][\s]*[:=][\s]*["\'][A-Za-z0-9+/]{20,}["\']', "API Key"),
            (r'["\'](?:secret|token)["\'][\s]*[:=][\s]*["\'][A-Za-z0-9+/]{20,}["\']', "Secret/Token"),
            (r'(?:password|passwd|pwd)[\s]*[:=][\s]*["\'][^"\']{8,}["\']', "Password"),
            (r'["\'](?:aws[_-]?access[_-]?key[_-]?id|aws[_-]?secret[_-]?access[_-]?key)["\']', "AWS Credentials"),
            (r'(?:private[_-]?key)[\s]*[:=][\s]*["\']-----BEGIN', "Private Key"),
        ]

        for pattern, secret_type in secret_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                self.vulnerabilities.append(Vulnerability(
                    id=str(uuid4()),
                    type=VulnerabilityType.HARDCODED_SECRET,
                    level=VulnerabilityLevel.CRITICAL,
                    title=f"Hardcoded {secret_type}",
                    description=f"Potential hardcoded {secret_type} found in source code",
                    file_path=str(file_path),
                    line_number=line_num,
                    code_snippet=match.group(0)[:50] + "...",
                    cwe_id="CWE-798",
                    cvss_score=9.1,
                    remediation="Store secrets in environment variables or secure secret management system",
                    references=[
                        "https://owasp.org/www-community/vulnerabilities/Use_of_hard-coded_password",
                        "https://cwe.mitre.org/data/definitions/798.html"
                    ],
                    metadata={"secret_type": secret_type}
                ))

    def _check_dangerous_functions(self, file_path: Path, content: str, tree: ast.AST):
        """Check for use of dangerous functions."""
        dangerous = {
            'pickle.loads': (VulnerabilityLevel.HIGH, "Pickle can execute arbitrary code", "CWE-502"),
            'yaml.load': (VulnerabilityLevel.HIGH, "Use yaml.safe_load instead", "CWE-502"),
            'eval': (VulnerabilityLevel.CRITICAL, "eval() executes arbitrary code", "CWE-95"),
            'exec': (VulnerabilityLevel.CRITICAL, "exec() executes arbitrary code", "CWE-95"),
            '__import__': (VulnerabilityLevel.MEDIUM, "Dynamic imports can be dangerous", "CWE-470"),
        }

        for func, (level, desc, cwe) in dangerous.items():
            if func in content:
                for i, line in enumerate(content.split('\n'), 1):
                    if func in line:
                        self.vulnerabilities.append(Vulnerability(
                            id=str(uuid4()),
                            type=VulnerabilityType.COMMAND_INJECTION,
                            level=level,
                            title=f"Dangerous Function: {func}",
                            description=desc,
                            file_path=str(file_path),
                            line_number=i,
                            code_snippet=line.strip()[:100],
                            cwe_id=cwe,
                            cvss_score=9.8 if level == VulnerabilityLevel.CRITICAL else 7.5,
                            remediation=f"Avoid using {func} or ensure input is properly validated",
                            references=[
                                f"https://cwe.mitre.org/data/definitions/{cwe.split('-')[1]}.html"
                            ],
                            metadata={"function": func}
                        ))

    def _scan_dependencies(self):
        """Scan project dependencies for vulnerabilities."""
        # Check for requirements.txt
        req_file = self.project_root / "requirements.txt"
        if req_file.exists():
            with open(req_file, 'r') as f:
                requirements = f.read()

            # Check for known vulnerable packages
            vulnerable_packages = {
                'django<2.2': (VulnerabilityLevel.HIGH, "Django versions before 2.2 have known security issues"),
                'flask<1.0': (VulnerabilityLevel.HIGH, "Flask versions before 1.0 have security vulnerabilities"),
                'requests<2.20.0': (VulnerabilityLevel.MEDIUM, "Requests versions before 2.20.0 have CVE-2018-18074"),
                'pyyaml<5.4': (VulnerabilityLevel.HIGH, "PyYAML versions before 5.4 have arbitrary code execution vulnerability"),
                'urllib3<1.26.5': (VulnerabilityLevel.MEDIUM, "urllib3 versions before 1.26.5 have security issues"),
            }

            for package, (level, desc) in vulnerable_packages.items():
                if package.split('<')[0] in requirements.lower():
                    self.vulnerabilities.append(Vulnerability(
                        id=str(uuid4()),
                        type=VulnerabilityType.VULNERABLE_DEPENDENCY,
                        level=level,
                        title=f"Vulnerable Dependency: {package}",
                        description=desc,
                        file_path=str(req_file),
                        line_number=None,
                        code_snippet=None,
                        cwe_id="CWE-1104",
                        cvss_score=7.5 if level == VulnerabilityLevel.HIGH else 5.3,
                        remediation=f"Update {package.split('<')[0]} to the latest secure version",
                        references=[
                            "https://github.com/advisories"
                        ],
                        metadata={"package": package}
                    ))

    def _scan_configuration(self):
        """Scan configuration files for security issues."""
        # Check for common config files
        config_files = [
            self.project_root / "config.py",
            self.project_root / "settings.py",
            self.project_root / ".env",
        ]

        for config_file in config_files:
            if config_file.exists():
                with open(config_file, 'r') as f:
                    content = f.read()

                # Check for debug mode
                if re.search(r'DEBUG\s*=\s*True', content):
                    self.vulnerabilities.append(Vulnerability(
                        id=str(uuid4()),
                        type=VulnerabilityType.DEBUG_ENABLED,
                        level=VulnerabilityLevel.MEDIUM,
                        title="Debug Mode Enabled",
                        description="Debug mode is enabled which may expose sensitive information",
                        file_path=str(config_file),
                        line_number=None,
                        code_snippet=None,
                        cwe_id="CWE-489",
                        cvss_score=5.3,
                        remediation="Disable debug mode in production",
                        references=[
                            "https://cwe.mitre.org/data/definitions/489.html"
                        ],
                        metadata={}
                    ))

    def _scan_secrets(self):
        """Scan for exposed secrets in various files."""
        # Scan all text files for secrets
        text_extensions = ['.py', '.js', '.json', '.yaml', '.yml', '.env', '.config', '.conf', '.ini']

        for ext in text_extensions:
            for file_path in self.project_root.rglob(f"*{ext}"):
                if any(part in file_path.parts for part in ['venv', '.venv', '__pycache__']):
                    continue

                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    self._check_hardcoded_secrets(file_path, content)
                except Exception:
                    continue

    def _get_function_name(self, node: ast.Call) -> Optional[str]:
        """Extract function name from AST Call node."""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            parts = []
            current = node.func
            while isinstance(current, ast.Attribute):
                parts.append(current.attr)
                current = current.value
            if isinstance(current, ast.Name):
                parts.append(current.id)
            return '.'.join(reversed(parts))
        return None

    def _uses_variable_input(self, node: ast.Call) -> bool:
        """Check if function call uses variable input."""
        for arg in node.args:
            if not isinstance(arg, ast.Constant):
                return True
        return False

    def _generate_report(self) -> Dict[str, Any]:
        """Generate security scan report."""
        # Count vulnerabilities by level
        level_counts = {level: 0 for level in VulnerabilityLevel}
        for vuln in self.vulnerabilities:
            level_counts[vuln.level] += 1

        # Count by type
        type_counts = {}
        for vuln in self.vulnerabilities:
            type_counts[vuln.type.value] = type_counts.get(vuln.type.value, 0) + 1

        # Generate summary
        report = {
            "scan_id": self.scan_id,
            "scan_time": self.scan_time.isoformat(),
            "project_root": str(self.project_root),
            "summary": {
                "total_vulnerabilities": len(self.vulnerabilities),
                "critical": level_counts[VulnerabilityLevel.CRITICAL],
                "high": level_counts[VulnerabilityLevel.HIGH],
                "medium": level_counts[VulnerabilityLevel.MEDIUM],
                "low": level_counts[VulnerabilityLevel.LOW],
                "info": level_counts[VulnerabilityLevel.INFO],
            },
            "by_type": type_counts,
            "vulnerabilities": [self._vuln_to_dict(v) for v in self.vulnerabilities],
            "risk_score": self._calculate_risk_score(),
            "recommendations": self._generate_recommendations()
        }

        return report

    def _vuln_to_dict(self, vuln: Vulnerability) -> Dict[str, Any]:
        """Convert vulnerability to dictionary."""
        return {
            "id": vuln.id,
            "type": vuln.type.value,
            "level": vuln.level.value,
            "title": vuln.title,
            "description": vuln.description,
            "file_path": vuln.file_path,
            "line_number": vuln.line_number,
            "code_snippet": vuln.code_snippet,
            "cwe_id": vuln.cwe_id,
            "cvss_score": vuln.cvss_score,
            "remediation": vuln.remediation,
            "references": vuln.references,
            "metadata": vuln.metadata
        }

    def _calculate_risk_score(self) -> float:
        """Calculate overall risk score."""
        score = 0.0
        weights = {
            VulnerabilityLevel.CRITICAL: 10.0,
            VulnerabilityLevel.HIGH: 7.5,
            VulnerabilityLevel.MEDIUM: 5.0,
            VulnerabilityLevel.LOW: 2.5,
            VulnerabilityLevel.INFO: 1.0
        }

        for vuln in self.vulnerabilities:
            score += weights[vuln.level]

        # Normalize to 0-100 scale
        return min(score, 100.0)

    def _generate_recommendations(self) -> List[str]:
        """Generate security recommendations based on findings."""
        recommendations = []

        # Count by level
        critical_count = sum(1 for v in self.vulnerabilities if v.level == VulnerabilityLevel.CRITICAL)
        high_count = sum(1 for v in self.vulnerabilities if v.level == VulnerabilityLevel.HIGH)

        if critical_count > 0:
            recommendations.append(f"URGENT: Address {critical_count} critical vulnerabilities immediately")

        if high_count > 0:
            recommendations.append(f"Fix {high_count} high-severity vulnerabilities as soon as possible")

        # Check for specific issues
        if any(v.type == VulnerabilityType.HARDCODED_SECRET for v in self.vulnerabilities):
            recommendations.append("Implement secure secrets management system")

        if any(v.type == VulnerabilityType.SQL_INJECTION for v in self.vulnerabilities):
            recommendations.append("Use parameterized queries for all database operations")

        if any(v.type == VulnerabilityType.WEAK_CRYPTO for v in self.vulnerabilities):
            recommendations.append("Update to modern cryptographic algorithms")

        if any(v.type == VulnerabilityType.VULNERABLE_DEPENDENCY for v in self.vulnerabilities):
            recommendations.append("Update all dependencies to secure versions")

        if not self.vulnerabilities:
            recommendations.append("No vulnerabilities detected. Continue following security best practices.")

        return recommendations


if __name__ == "__main__":
    # Run security scan when module is executed directly
    scanner = SecurityScanner()
    report = scanner.scan()

    print(f"Security Scan Report")
    print(f"=" * 50)
    print(f"Total Vulnerabilities: {report['summary']['total_vulnerabilities']}")
    print(f"Critical: {report['summary']['critical']}")
    print(f"High: {report['summary']['high']}")
    print(f"Medium: {report['summary']['medium']}")
    print(f"Low: {report['summary']['low']}")
    print(f"Risk Score: {report['risk_score']:.1f}/100")

    print(f"\nRecommendations:")
    for rec in report['recommendations']:
        print(f"  - {rec}")

    # Save detailed report
    report_path = Path.home() / ".pm" / "security_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"\nDetailed report saved to: {report_path}")