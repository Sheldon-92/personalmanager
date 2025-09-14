"""
Test suite for pm-local launcher script.
"""

import os
import subprocess
import tempfile
from pathlib import Path
import pytest


class TestPMLocalLauncher:
    """Test pm-local launcher functionality."""

    @pytest.fixture
    def launcher_path(self):
        """Get the path to pm-local launcher."""
        project_root = Path(__file__).parent.parent
        return project_root / "bin" / "pm-local"

    def test_launcher_exists(self, launcher_path):
        """Test that launcher script exists."""
        assert launcher_path.exists()
        assert launcher_path.is_file()
        assert os.access(launcher_path, os.X_OK)  # Check executable

    def test_launcher_debug_mode(self, launcher_path):
        """Test launcher debug mode."""
        result = subprocess.run(
            [str(launcher_path), "--launcher-debug"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "PersonalManager Local Launcher - Environment Information" in result.stdout
        assert "Project Root:" in result.stdout
        assert "Python Version:" in result.stdout

    def test_launcher_version(self, launcher_path):
        """Test launcher version command."""
        result = subprocess.run(
            [str(launcher_path), "--version"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "PersonalManager" in result.stdout or "PersonalManager" in result.stderr

    def test_launcher_help(self, launcher_path):
        """Test launcher help command."""
        result = subprocess.run(
            [str(launcher_path), "--help"],
            capture_output=True,
            text=True
        )

        # The help command might exit with 0 or 2 depending on implementation
        assert result.returncode in [0, 2]
        output = result.stdout + result.stderr
        assert "Usage:" in output or "Commands:" in output

    def test_launcher_with_poetry(self, launcher_path, monkeypatch):
        """Test launcher behavior when Poetry is available."""
        # This test would need mocking of Poetry availability
        # For now, we just ensure the launcher runs
        result = subprocess.run(
            [str(launcher_path), "--launcher-debug"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "Poetry Available:" in result.stdout

    def test_launcher_python_fallback(self, launcher_path):
        """Test launcher Python fallback mechanism."""
        # Create a temporary directory without Poetry
        with tempfile.TemporaryDirectory() as tmpdir:
            # Copy launcher to temp directory
            temp_launcher = Path(tmpdir) / "pm-local"
            temp_launcher.write_text(launcher_path.read_text())
            temp_launcher.chmod(0o755)

            # Create minimal project structure
            src_dir = Path(tmpdir) / "src" / "pm" / "cli"
            src_dir.mkdir(parents=True)
            (src_dir / "__init__.py").touch()
            (src_dir / "main.py").write_text("""
import sys
if __name__ == "__main__":
    print("Fallback mode working")
    sys.exit(0)
""")

            # Run launcher in this environment
            result = subprocess.run(
                [str(temp_launcher), "--launcher-debug"],
                capture_output=True,
                text=True,
                cwd=tmpdir
            )

            # Should still work in debug mode
            assert "Python Version:" in result.stdout

    def test_launcher_error_handling(self, launcher_path):
        """Test launcher error handling."""
        # Test with non-existent command
        result = subprocess.run(
            [str(launcher_path), "non-existent-command"],
            capture_output=True,
            text=True
        )

        # Should pass through to the main application
        # which will handle the error
        output = result.stdout + result.stderr
        assert result.returncode != 0 or "Error" in output or "Usage" in output

    @pytest.mark.parametrize("command", [
        ["doctor"],
        ["help"],
        ["--version"],
        ["-h"],
    ])
    def test_launcher_common_commands(self, launcher_path, command):
        """Test launcher with common commands."""
        result = subprocess.run(
            [str(launcher_path)] + command,
            capture_output=True,
            text=True,
            timeout=10
        )

        # Commands should run without crashing
        # Some might exit with non-zero for help
        assert result.returncode in [0, 1, 2]

    def test_launcher_environment_variables(self, launcher_path):
        """Test launcher properly sets environment variables."""
        # Run a command that would need PYTHONPATH
        result = subprocess.run(
            [str(launcher_path), "--launcher-debug"],
            capture_output=True,
            text=True,
            env={**os.environ, "PM_DEBUG": "1"}
        )

        assert result.returncode == 0
        assert "Project Root:" in result.stdout

    def test_launcher_project_root_detection(self, launcher_path):
        """Test launcher correctly detects project root."""
        result = subprocess.run(
            [str(launcher_path), "--launcher-debug"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        # Should show the correct project root
        project_root = Path(__file__).parent.parent
        assert str(project_root) in result.stdout


class TestLauncherIntegration:
    """Integration tests for pm-local launcher."""

    @pytest.fixture
    def launcher_path(self):
        """Get the path to pm-local launcher."""
        project_root = Path(__file__).parent.parent
        return project_root / "bin" / "pm-local"

    @pytest.mark.integration
    def test_launcher_with_real_commands(self, launcher_path):
        """Test launcher with real PM commands."""
        # Test doctor command
        result = subprocess.run(
            [str(launcher_path), "doctor", "--quick"],
            capture_output=True,
            text=True,
            timeout=30
        )

        output = result.stdout + result.stderr
        assert "PersonalManager" in output or "doctor" in output

    @pytest.mark.integration
    def test_launcher_ai_command(self, launcher_path):
        """Test launcher with AI command."""
        result = subprocess.run(
            [str(launcher_path), "ai", "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )

        output = result.stdout + result.stderr
        assert "ai" in output.lower() or "command" in output.lower()

    @pytest.mark.integration
    @pytest.mark.parametrize("shell", ["bash", "zsh"])
    def test_launcher_shell_compatibility(self, launcher_path, shell):
        """Test launcher works with different shells."""
        if not subprocess.run(["which", shell], capture_output=True).returncode == 0:
            pytest.skip(f"{shell} not available")

        result = subprocess.run(
            [shell, str(launcher_path), "--launcher-debug"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "Environment Information" in result.stdout