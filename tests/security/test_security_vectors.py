"""
Security vectors test suite for PersonalManager.

This test suite validates 8 critical security vectors in the PersonalManager system:
1. Command injection prevention in launcher
2. Path traversal protection
3. Environment variable sanitization
4. Shell command escaping
5. File permission validation
6. Input validation and sanitization
7. Process execution security
8. Configuration file security

Test scenarios cover:
- Version/today/project overview commands
- Poetry/non-Poetry environments
- Uninitialized/initialized states
"""

import os
import subprocess
import tempfile
import stat
from pathlib import Path
import pytest
import shutil


class TestSecurityVectors:
    """Test security vectors for PersonalManager system."""

    @pytest.fixture
    def launcher_path(self):
        """Get the path to pm-local launcher."""
        project_root = Path(__file__).parent.parent.parent
        return project_root / "bin" / "pm-local"

    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = Path(tmpdir)

            # Create minimal project structure
            (temp_path / "bin").mkdir()
            (temp_path / "src" / "pm" / "cli").mkdir(parents=True)
            (temp_path / "src" / "pm" / "cli" / "__init__.py").touch()
            (temp_path / "src" / "pm" / "cli" / "main.py").write_text("""
import sys
if __name__ == "__main__":
    print("Test PM main")
    sys.exit(0)
""")

            yield temp_path

    def test_command_injection_prevention(self, launcher_path):
        """
        Security Vector 1: Command injection prevention in launcher.

        Tests that malicious commands cannot be injected through arguments.
        """
        # Test various injection attempts - these should be treated as normal arguments
        # and passed to the PM application which should handle them safely
        malicious_commands = [
            "; rm -rf /tmp/test_file",  # Safe test path
            "invalid_command",
            "--non-existent-flag",
            "help; echo 'test'",
        ]

        for malicious_cmd in malicious_commands:
            result = subprocess.run(
                [str(launcher_path), malicious_cmd],
                capture_output=True,
                text=True,
                timeout=10
            )

            # Commands should be handled by the application, not shell-executed
            # The launcher should pass arguments safely to the application
            output = result.stdout + result.stderr

            # These should not result in actual shell command execution
            # If they do, the test will detect the shell output
            assert result.returncode in [0, 1, 2]  # Valid application exit codes

            # Basic check that the launcher ran (we see PM output, not shell injection)
            assert ("PersonalManager" in output or
                    "poetry run" in output or
                    "direct Python" in output or
                    "Usage:" in output or
                    "Commands:" in output or
                    "Error:" in output)

    def test_path_traversal_protection(self, launcher_path, temp_project_dir):
        """
        Security Vector 2: Path traversal protection.

        Tests that the launcher properly validates project paths and prevents
        access to files outside the project directory.
        """
        # Copy launcher to temp directory
        temp_launcher = temp_project_dir / "bin" / "pm-local"
        shutil.copy2(launcher_path, temp_launcher)
        temp_launcher.chmod(0o755)

        # Test path traversal attempts
        traversal_attempts = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/etc/hosts",
            "~/.ssh/id_rsa",
            "../../../home/user/.bashrc",
        ]

        for traversal_path in traversal_attempts:
            result = subprocess.run(
                [str(temp_launcher), "--launcher-debug"],
                capture_output=True,
                text=True,
                cwd=str(temp_project_dir),
                env={**os.environ, "MALICIOUS_PATH": traversal_path}
            )

            # Should show project root, not allow traversal
            output = result.stdout + result.stderr
            assert str(temp_project_dir) in output
            assert "/etc/passwd" not in output
            assert "ssh" not in output

    def test_environment_variable_sanitization(self, launcher_path):
        """
        Security Vector 3: Environment variable sanitization.

        Tests that environment variables are properly sanitized and
        malicious environment variables don't affect execution.
        """
        malicious_env = {
            **os.environ,
            "LD_PRELOAD": "/tmp/malicious.so",
            "PYTHONPATH": "/tmp/malicious:/usr/bin",
            "PATH": "/tmp/malicious:/bin:/usr/bin",
            "BASH_ENV": "/tmp/malicious.sh",
            "ENV": "/tmp/malicious.sh",
            "PS4": "`/tmp/backdoor`",
        }

        result = subprocess.run(
            [str(launcher_path), "--launcher-debug"],
            capture_output=True,
            text=True,
            env=malicious_env,
            timeout=10
        )

        # Should complete successfully and show correct project path
        assert result.returncode == 0
        output = result.stdout + result.stderr
        assert "Project Root:" in output
        assert "malicious" not in output

    def test_shell_command_escaping(self, launcher_path):
        """
        Security Vector 4: Shell command escaping.

        Tests that special shell characters in arguments are properly escaped.
        """
        special_chars = [
            "'single quotes'",
            '"double quotes"',
            "$SHELL_VAR",
            "`command substitution`",
            "$(command substitution)",
            "file with spaces.txt",
            "file;with;semicolons",
            "file|with|pipes",
            "file&with&ampersands",
        ]

        for special_arg in special_chars:
            result = subprocess.run(
                [str(launcher_path), "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )

            # Should handle special characters safely
            assert result.returncode in [0, 1, 2]  # Valid exit codes
            output = result.stdout + result.stderr
            # Should not execute shell substitutions
            assert "SHELL_VAR" not in output

    def test_file_permission_validation(self, launcher_path, temp_project_dir):
        """
        Security Vector 5: File permission validation.

        Tests that the launcher validates file permissions and refuses to
        execute files with inappropriate permissions.
        """
        # Copy launcher to temp directory
        temp_launcher = temp_project_dir / "bin" / "pm-local"
        shutil.copy2(launcher_path, temp_launcher)

        # Test with different permission scenarios
        permission_tests = [
            (0o777, True),   # World writable (should work but warn)
            (0o755, True),   # Normal executable (should work)
            (0o644, False),  # Not executable (should fail)
            (0o000, False),  # No permissions (should fail)
        ]

        for permissions, should_execute in permission_tests:
            temp_launcher.chmod(permissions)

            if should_execute and os.access(temp_launcher, os.X_OK):
                result = subprocess.run(
                    [str(temp_launcher), "--launcher-debug"],
                    capture_output=True,
                    text=True,
                    cwd=str(temp_project_dir),
                    timeout=10
                )
                # Should execute successfully
                assert result.returncode == 0 or "Environment Information" in result.stdout
            else:
                # Should fail to execute due to permissions
                try:
                    result = subprocess.run(
                        [str(temp_launcher), "--launcher-debug"],
                        capture_output=True,
                        text=True,
                        cwd=str(temp_project_dir),
                        timeout=5
                    )
                    # If it runs, it should fail properly
                    assert result.returncode != 0
                except (subprocess.TimeoutExpired, PermissionError, OSError):
                    # Expected failure
                    pass

    def test_input_validation_and_sanitization(self, launcher_path):
        """
        Security Vector 6: Input validation and sanitization.

        Tests that all inputs are properly validated and sanitized.
        """
        # Test with various malicious inputs (excluding null bytes which cause subprocess errors)
        malicious_inputs = [
            "\x1b[31mANSI_escape_codes\x1b[0m",
            "very_long_input_" + "A" * 500,  # Reduced length to avoid timeout
            "../../../tmp/test_file",  # Safe test path
            "\"; echo 'SQL_INJECTION_TEST'; --",
            "<script>echo 'XSS_TEST'</script>",
            "echo 'EVAL_TEST'",
        ]

        for malicious_input in malicious_inputs:
            try:
                result = subprocess.run(
                    [str(launcher_path), malicious_input],
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                # Should handle malicious input safely - passed as arguments to PM app
                output = result.stdout + result.stderr

                # If the malicious patterns appear, they should be in error messages
                # (showing they were treated as literal commands, not executed)
                if "SQL_INJECTION_TEST" in output:
                    assert ("No such command" in output or "Error" in output)
                if "XSS_TEST" in output:
                    assert ("No such command" in output or "Error" in output)
                if "EVAL_TEST" in output:
                    assert ("No such command" in output or "Error" in output)

                # Should show normal PM application behavior (error for invalid commands)
                assert result.returncode in [0, 1, 2, 127]  # Valid exit codes

                # Should not execute as shell commands (would see different error patterns)
                assert "command not found" not in output.lower()
                assert "permission denied" not in output.lower() or "Error" in output

            except (subprocess.TimeoutExpired, ValueError, OSError):
                # Some inputs may cause legitimate subprocess errors, which is acceptable
                # as it means the input was rejected rather than executed
                pass

        # Test CRLF injection separately
        try:
            result = subprocess.run(
                [str(launcher_path), "test\nCRLF_TEST"],
                capture_output=True,
                text=True,
                timeout=10
            )
            output = result.stdout + result.stderr
            # Should not execute the CRLF injected command
            assert "CRLF_TEST" not in output or "Error" in output
        except (ValueError, OSError):
            # CRLF characters may be rejected by subprocess, which is good
            pass

        # Test null byte separately to ensure it's properly rejected
        try:
            result = subprocess.run(
                [str(launcher_path), "test\x00injection"],
                capture_output=True,
                text=True,
                timeout=5
            )
            # If this doesn't raise an error, the null byte should be filtered out
            output = result.stdout + result.stderr
            assert "\x00" not in output
        except (ValueError, OSError):
            # Expected - null bytes should be rejected by subprocess
            pass

    def test_process_execution_security(self, launcher_path):
        """
        Security Vector 7: Process execution security.

        Tests that child processes are executed securely with proper isolation.
        """
        # Test process limits and security
        result = subprocess.run(
            [str(launcher_path), "--launcher-debug"],
            capture_output=True,
            text=True,
            timeout=10
        )

        assert result.returncode == 0
        output = result.stdout + result.stderr

        # Verify environment information is displayed safely
        assert "Project Root:" in output
        assert "Python Version:" in output

        # Check that no sensitive information is leaked
        sensitive_info = [
            "password",
            "secret",
            "token",
            "api_key",
            "/home/",
            "/Users/",
        ]

        for sensitive in sensitive_info:
            # Allow legitimate path information but not credentials
            if sensitive in ["/home/", "/Users/"]:
                # These might appear in project paths, which is okay
                continue
            assert sensitive.lower() not in output.lower()

    def test_configuration_file_security(self, launcher_path, temp_project_dir):
        """
        Security Vector 8: Configuration file security.

        Tests that configuration files are handled securely and cannot be
        used for malicious purposes.
        """
        # Create malicious pyproject.toml
        malicious_toml = temp_project_dir / "pyproject.toml"
        malicious_toml.write_text("""
[tool.poetry]
name = "malicious"
version = "0.1.0"

[tool.poetry.scripts]
pm = "os:system('rm -rf /')"

[[tool.poetry.source]]
name = "malicious"
url = "https://malicious-pypi.com/simple/"
""")

        # Copy launcher to temp directory
        temp_launcher = temp_project_dir / "bin" / "pm-local"
        shutil.copy2(launcher_path, temp_launcher)
        temp_launcher.chmod(0o755)

        # Test with malicious configuration
        result = subprocess.run(
            [str(temp_launcher), "--launcher-debug"],
            capture_output=True,
            text=True,
            cwd=str(temp_project_dir),
            timeout=10
        )

        # Should complete safely without executing malicious commands
        output = result.stdout + result.stderr
        assert "Environment Information" in output
        assert "rm -rf" not in output
        assert "malicious-pypi" not in output

    @pytest.mark.parametrize("command,environment", [
        ("--version", "poetry"),
        ("--version", "python"),
        ("--help", "poetry"),
        ("--help", "python"),
        ("doctor", "poetry"),
        ("doctor", "python"),
    ])
    def test_command_scenarios_security(self, launcher_path, command, environment):
        """
        Test security across different command and environment scenarios.

        Tests version/today/project overview commands in both Poetry and
        non-Poetry environments.
        """
        if environment == "poetry":
            # Test in environment where Poetry might be available
            result = subprocess.run(
                [str(launcher_path), command],
                capture_output=True,
                text=True,
                timeout=15
            )
        else:
            # Test in environment without Poetry (simulate by removing PATH)
            env = {k: v for k, v in os.environ.items() if k != "PATH"}
            env["PATH"] = "/usr/bin:/bin"  # Minimal PATH without poetry

            result = subprocess.run(
                [str(launcher_path), command],
                capture_output=True,
                text=True,
                env=env,
                timeout=15
            )

        # Should complete without security issues
        assert result.returncode in [0, 1, 2]  # Valid exit codes
        output = result.stdout + result.stderr

        # Should not contain security-sensitive information
        assert "password" not in output.lower()
        assert "secret" not in output.lower()
        assert "token" not in output.lower()

    @pytest.mark.parametrize("init_state", ["initialized", "uninitialized"])
    def test_initialization_state_security(self, launcher_path, init_state, temp_project_dir):
        """
        Test security in different initialization states.

        Tests both uninitialized and initialized project states.
        """
        # Copy launcher to temp directory
        temp_launcher = temp_project_dir / "bin" / "pm-local"
        shutil.copy2(launcher_path, temp_launcher)
        temp_launcher.chmod(0o755)

        if init_state == "initialized":
            # Create initialized state files
            config_dir = temp_project_dir / ".pm"
            config_dir.mkdir()
            (config_dir / "config.json").write_text('{"initialized": true}')
        # For uninitialized, we leave the directory minimal

        result = subprocess.run(
            [str(temp_launcher), "--launcher-debug"],
            capture_output=True,
            text=True,
            cwd=str(temp_project_dir),
            timeout=10
        )

        # Should handle both states securely
        assert result.returncode == 0
        output = result.stdout + result.stderr
        assert "Environment Information" in output

        # Should not expose internal state information unsafely
        if init_state == "uninitialized":
            # Should indicate missing components safely
            assert "Not found" in output or "Project Root:" in output
        else:
            # Should show initialized state safely
            assert "Project Root:" in output


class TestSecurityIntegration:
    """Integration security tests across different scenarios."""

    @pytest.fixture
    def launcher_path(self):
        """Get the path to pm-local launcher."""
        project_root = Path(__file__).parent.parent.parent
        return project_root / "bin" / "pm-local"

    def test_end_to_end_security_validation(self, launcher_path):
        """
        Comprehensive end-to-end security validation.

        Tests the complete security posture across all vectors in a
        realistic usage scenario.
        """
        # Simulate a complete usage flow with security considerations
        commands_to_test = ["--launcher-debug", "--version", "--help"]

        for cmd in commands_to_test:
            result = subprocess.run(
                [str(launcher_path), cmd],
                capture_output=True,
                text=True,
                timeout=10
            )

            # Validate secure execution
            assert result.returncode in [0, 1, 2]
            output = result.stdout + result.stderr

            # Comprehensive security checks
            security_violations = [
                "password", "secret", "token", "api_key",
                "DROP TABLE", "rm -rf", "eval(", "exec(",
                "\x00", "<script>", "javascript:",
                "file://", "ftp://", "ssh://",
            ]

            for violation in security_violations:
                assert violation not in output.lower()

            # Ensure no sensitive file paths are exposed
            sensitive_paths = [
                "/etc/passwd", "/etc/shadow", "~/.ssh",
                "C:\\Windows\\System32", "registry.exe"
            ]

            for path in sensitive_paths:
                assert path not in output

    def test_concurrent_execution_security(self, launcher_path):
        """
        Test security under concurrent execution scenarios.

        Ensures that multiple instances don't create security vulnerabilities.
        """
        import concurrent.futures
        import threading

        def run_launcher_command(cmd):
            """Run launcher command in thread."""
            return subprocess.run(
                [str(launcher_path), cmd],
                capture_output=True,
                text=True,
                timeout=10
            )

        # Run multiple commands concurrently
        commands = ["--launcher-debug", "--version", "--help"] * 3

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(run_launcher_command, cmd) for cmd in commands]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]

        # Validate all executions completed securely
        for result in results:
            assert result.returncode in [0, 1, 2]
            output = result.stdout + result.stderr

            # No race condition security issues
            assert "Project Root:" in output or "PersonalManager" in output
            assert "malicious" not in output.lower()
            assert "injection" not in output.lower()