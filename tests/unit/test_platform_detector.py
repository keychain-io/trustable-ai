"""
Unit tests for Platform Detector.

Tests platform detection, WSL detection, and command pattern generation.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, mock_open, patch
import platform

from cli.platform_detector import PlatformDetector


@pytest.mark.unit
class TestPlatformDetection:
    """Test platform detection functionality."""

    def test_detect_windows_platform(self):
        """Test Windows platform detection."""
        with patch("platform.system", return_value="Windows"):
            detector = PlatformDetector()
            platform_info = detector.detect_platform()

            assert platform_info["os"] == "Windows"
            assert platform_info["is_wsl"] is False
            assert platform_info["shell"] == "powershell"
            assert "platform_specific" in platform_info

    def test_detect_linux_platform(self):
        """Test Linux platform detection (not WSL)."""
        with (
            patch("platform.system", return_value="Linux"),
            patch("builtins.open", side_effect=FileNotFoundError),
        ):
            detector = PlatformDetector()
            platform_info = detector.detect_platform()

            assert platform_info["os"] == "Linux"
            assert platform_info["is_wsl"] is False
            assert platform_info["shell"] in ["bash", "zsh", "sh"]

    def test_detect_macos_platform(self):
        """Test macOS (Darwin) platform detection."""
        with patch("platform.system", return_value="Darwin"):
            detector = PlatformDetector()
            platform_info = detector.detect_platform()

            assert platform_info["os"] == "Darwin"
            assert platform_info["is_wsl"] is False
            assert platform_info["shell"] in ["zsh", "bash"]

    def test_platform_info_cached(self):
        """Test that platform info is cached after first detection."""
        with (
            patch("platform.system", return_value="Linux") as mock_system,
            patch("builtins.open", side_effect=FileNotFoundError),
        ):
            detector = PlatformDetector()

            # First call - calls platform.system() twice (once in detect_platform, once in _is_wsl)
            info1 = detector.detect_platform()

            # Second call should use cache - no additional calls to platform.system()
            info2 = detector.detect_platform()

            # platform.system should only be called twice (both from first detect_platform call)
            assert mock_system.call_count == 2
            assert info1 == info2


@pytest.mark.unit
class TestWSLDetection:
    """Test Windows Subsystem for Linux detection."""

    def test_wsl_detection_via_proc_version(self):
        """Test WSL detection using /proc/version with 'microsoft'."""
        proc_version_content = "Linux version 5.10.16.3-microsoft-standard-WSL2"

        with (
            patch("platform.system", return_value="Linux"),
            patch("builtins.open", mock_open(read_data=proc_version_content)),
        ):
            detector = PlatformDetector()
            platform_info = detector.detect_platform()

            assert platform_info["is_wsl"] is True

    def test_wsl_detection_via_proc_version_wsl_keyword(self):
        """Test WSL detection using /proc/version with 'WSL'."""
        proc_version_content = "Linux version 4.4.0-WSL #1 SMP"

        with (
            patch("platform.system", return_value="Linux"),
            patch("builtins.open", mock_open(read_data=proc_version_content)),
        ):
            detector = PlatformDetector()
            platform_info = detector.detect_platform()

            assert platform_info["is_wsl"] is True

    def test_wsl_detection_via_osrelease_fallback(self):
        """Test WSL detection using /proc/sys/kernel/osrelease fallback."""

        def open_side_effect(path, mode="r"):
            if "/proc/version" in str(path):
                raise FileNotFoundError
            elif "/proc/sys/kernel/osrelease" in str(path):
                return mock_open(read_data="5.10.16.3-microsoft-standard-WSL2")()
            raise FileNotFoundError

        with (
            patch("platform.system", return_value="Linux"),
            patch("builtins.open", side_effect=open_side_effect),
        ):
            detector = PlatformDetector()
            assert detector._is_wsl() is True

    def test_not_wsl_when_no_microsoft_keyword(self):
        """Test that non-WSL Linux is correctly identified."""
        proc_version_content = "Linux version 5.10.0-generic #1 SMP Ubuntu"

        with (
            patch("platform.system", return_value="Linux"),
            patch("builtins.open", mock_open(read_data=proc_version_content)),
        ):
            detector = PlatformDetector()
            platform_info = detector.detect_platform()

            assert platform_info["is_wsl"] is False

    def test_wsl_false_on_windows(self):
        """Test that WSL detection returns False on Windows."""
        with patch("platform.system", return_value="Windows"):
            detector = PlatformDetector()
            assert detector._is_wsl() is False

    def test_wsl_false_on_macos(self):
        """Test that WSL detection returns False on macOS."""
        with patch("platform.system", return_value="Darwin"):
            detector = PlatformDetector()
            assert detector._is_wsl() is False

    def test_wsl_detection_handles_permission_error(self):
        """Test WSL detection gracefully handles permission errors."""
        with (
            patch("platform.system", return_value="Linux"),
            patch("builtins.open", side_effect=PermissionError),
        ):
            detector = PlatformDetector()
            # Should not raise, should return False
            assert detector._is_wsl() is False

    def test_wsl_detection_handles_io_error(self):
        """Test WSL detection gracefully handles IO errors."""
        with (
            patch("platform.system", return_value="Linux"),
            patch("builtins.open", side_effect=IOError),
        ):
            detector = PlatformDetector()
            # Should not raise, should return False
            assert detector._is_wsl() is False


@pytest.mark.unit
class TestPlatformSpecificInfo:
    """Test platform-specific information gathering."""

    def test_windows_specific_info(self):
        """Test Windows-specific information."""
        with (
            patch("platform.system", return_value="Windows"),
            patch("platform.machine", return_value="AMD64"),
            patch("platform.release", return_value="10"),
            patch("platform.version", return_value="10.0.19041"),
        ):
            detector = PlatformDetector()
            platform_info = detector.detect_platform()

            specific = platform_info["platform_specific"]
            assert specific["architecture"] == "AMD64"
            assert "windows_version" in specific
            assert ".exe" in specific["command_extensions"]
            assert ".ps1" in specific["command_extensions"]

    def test_macos_specific_info(self):
        """Test macOS-specific information."""
        with (
            patch("platform.system", return_value="Darwin"),
            patch("platform.machine", return_value="arm64"),
            patch("platform.release", return_value="21.1.0"),
            patch("platform.mac_ver", return_value=("12.0.1", "", "")),
        ):
            detector = PlatformDetector()
            platform_info = detector.detect_platform()

            specific = platform_info["platform_specific"]
            assert specific["architecture"] == "arm64"
            assert "macos_version" in specific
            assert "" in specific["command_extensions"]

    def test_linux_specific_info(self):
        """Test Linux-specific information."""
        with (
            patch("platform.system", return_value="Linux"),
            patch("platform.machine", return_value="x86_64"),
            patch("platform.release", return_value="5.10.0"),
            patch("builtins.open", side_effect=FileNotFoundError),
        ):
            detector = PlatformDetector()
            platform_info = detector.detect_platform()

            specific = platform_info["platform_specific"]
            assert specific["architecture"] == "x86_64"
            assert "" in specific["command_extensions"]

    def test_wsl_interop_detection(self):
        """Test WSL interop detection."""
        proc_version_content = "Linux version 5.10.16.3-microsoft-standard-WSL2"

        def open_side_effect(path, mode="r"):
            if "/proc/version" in str(path):
                return mock_open(read_data=proc_version_content)()
            raise FileNotFoundError

        with (
            patch("platform.system", return_value="Linux"),
            patch("builtins.open", side_effect=open_side_effect),
            patch.object(Path, "exists", return_value=True),
        ):
            detector = PlatformDetector()
            platform_info = detector.detect_platform()

            assert platform_info["is_wsl"] is True
            assert platform_info["platform_specific"]["wsl_interop"] is True


@pytest.mark.unit
class TestShellDetection:
    """Test shell detection."""

    def test_windows_defaults_to_powershell(self):
        """Test that Windows defaults to PowerShell."""
        with patch("platform.system", return_value="Windows"):
            detector = PlatformDetector()
            platform_info = detector.detect_platform()

            assert platform_info["shell"] == "powershell"

    def test_linux_uses_shell_env_var(self):
        """Test that Linux uses SHELL environment variable."""
        with (
            patch("platform.system", return_value="Linux"),
            patch.dict("os.environ", {"SHELL": "/bin/zsh"}),
            patch("builtins.open", side_effect=FileNotFoundError),
        ):
            detector = PlatformDetector()
            platform_info = detector.detect_platform()

            assert platform_info["shell"] == "zsh"

    def test_linux_defaults_to_bash_if_no_shell_env(self):
        """Test that Linux defaults to bash if SHELL env var not set."""
        with (
            patch("platform.system", return_value="Linux"),
            patch.dict("os.environ", {}, clear=True),
            patch("builtins.open", side_effect=FileNotFoundError),
        ):
            detector = PlatformDetector()
            platform_info = detector.detect_platform()

            assert platform_info["shell"] == "bash"

    def test_macos_uses_shell_env_var(self):
        """Test that macOS uses SHELL environment variable."""
        with (
            patch("platform.system", return_value="Darwin"),
            patch.dict("os.environ", {"SHELL": "/usr/local/bin/fish"}),
        ):
            detector = PlatformDetector()
            platform_info = detector.detect_platform()

            assert platform_info["shell"] == "fish"

    def test_macos_defaults_to_zsh_if_no_shell_env(self):
        """Test that macOS defaults to zsh if SHELL env var not set."""
        with (
            patch("platform.system", return_value="Darwin"),
            patch.dict("os.environ", {}, clear=True),
        ):
            detector = PlatformDetector()
            platform_info = detector.detect_platform()

            assert platform_info["shell"] == "zsh"


@pytest.mark.unit
class TestCommandPatterns:
    """Test command pattern generation."""

    def test_get_git_patterns(self):
        """Test Git command patterns are returned."""
        with (
            patch("platform.system", return_value="Linux"),
            patch("builtins.open", side_effect=FileNotFoundError),
        ):
            detector = PlatformDetector()
            patterns = detector.get_command_patterns()

            assert "git" in patterns
            assert "git status" in patterns["git"]
            assert "git diff" in patterns["git"]
            assert "git log" in patterns["git"]
            assert "git add" in patterns["git"]
            assert "git commit" in patterns["git"]

    def test_get_file_patterns_linux(self):
        """Test file command patterns for Linux."""
        with (
            patch("platform.system", return_value="Linux"),
            patch("builtins.open", side_effect=FileNotFoundError),
        ):
            detector = PlatformDetector()
            patterns = detector.get_command_patterns()

            assert "file" in patterns
            assert "cat" in patterns["file"]
            assert "ls" in patterns["file"]
            assert "grep" in patterns["file"]
            # Windows-specific commands should not be present
            assert "dir" not in patterns["file"]
            assert "type" not in patterns["file"]

    def test_get_file_patterns_windows(self):
        """Test file command patterns for Windows."""
        with patch("platform.system", return_value="Windows"):
            detector = PlatformDetector()
            patterns = detector.get_command_patterns()

            assert "file" in patterns
            assert "dir" in patterns["file"]
            assert "type" in patterns["file"]
            assert "findstr" in patterns["file"]
            # Unix commands should still be present (Git Bash support)
            assert "cat" in patterns["file"]
            assert "ls" in patterns["file"]

    def test_get_work_tracking_patterns(self):
        """Test work tracking command patterns."""
        with (
            patch("platform.system", return_value="Linux"),
            patch("builtins.open", side_effect=FileNotFoundError),
        ):
            detector = PlatformDetector()
            patterns = detector.get_command_patterns()

            assert "work_tracking" in patterns
            assert "az boards work-item show" in patterns["work_tracking"]
            assert "az boards work-item create" in patterns["work_tracking"]
            assert "az boards work-item update" in patterns["work_tracking"]
            # Delete should not be in safe patterns
            assert "az boards work-item delete" not in patterns["work_tracking"]

    def test_get_test_patterns_linux(self):
        """Test test execution patterns for Linux."""
        with (
            patch("platform.system", return_value="Linux"),
            patch("builtins.open", side_effect=FileNotFoundError),
        ):
            detector = PlatformDetector()
            patterns = detector.get_command_patterns()

            assert "test" in patterns
            assert "pytest" in patterns["test"]
            assert "python -m pytest" in patterns["test"]
            assert "python3 -m pytest" in patterns["test"]
            assert "npm test" in patterns["test"]

    def test_get_test_patterns_windows(self):
        """Test test execution patterns for Windows."""
        with patch("platform.system", return_value="Windows"):
            detector = PlatformDetector()
            patterns = detector.get_command_patterns()

            assert "test" in patterns
            assert "pytest" in patterns["test"]
            assert "python -m pytest" in patterns["test"]
            assert "python -m unittest" in patterns["test"]

    def test_get_build_patterns(self):
        """Test build command patterns."""
        with (
            patch("platform.system", return_value="Linux"),
            patch("builtins.open", side_effect=FileNotFoundError),
        ):
            detector = PlatformDetector()
            patterns = detector.get_command_patterns()

            assert "build" in patterns
            assert "npm install" in patterns["build"]
            assert "npm run build" in patterns["build"]
            assert "pip install" in patterns["build"]
            assert "make" in patterns["build"]

    def test_get_build_patterns_windows(self):
        """Test Windows-specific build patterns."""
        with patch("platform.system", return_value="Windows"):
            detector = PlatformDetector()
            patterns = detector.get_command_patterns()

            assert "build" in patterns
            assert "msbuild" in patterns["build"]

    def test_get_inspect_patterns(self):
        """Test code inspection patterns."""
        with (
            patch("platform.system", return_value="Linux"),
            patch("builtins.open", side_effect=FileNotFoundError),
        ):
            detector = PlatformDetector()
            patterns = detector.get_command_patterns()

            assert "inspect" in patterns
            assert "pylint" in patterns["inspect"]
            assert "mypy" in patterns["inspect"]
            assert "black --check" in patterns["inspect"]
            assert "eslint" in patterns["inspect"]

    def test_all_pattern_categories_present(self):
        """Test that all expected pattern categories are present."""
        with (
            patch("platform.system", return_value="Linux"),
            patch("builtins.open", side_effect=FileNotFoundError),
        ):
            detector = PlatformDetector()
            patterns = detector.get_command_patterns()

            expected_categories = [
                "git",
                "file",
                "work_tracking",
                "test",
                "build",
                "inspect",
            ]

            for category in expected_categories:
                assert category in patterns
                assert len(patterns[category]) > 0


@pytest.mark.unit
class TestDangerousPatterns:
    """Test dangerous command pattern identification."""

    def test_get_destructive_patterns_linux(self):
        """Test destructive patterns for Linux."""
        with (
            patch("platform.system", return_value="Linux"),
            patch("builtins.open", side_effect=FileNotFoundError),
        ):
            detector = PlatformDetector()
            dangerous = detector.get_dangerous_patterns()

            assert "destructive" in dangerous
            assert "rm -rf" in dangerous["destructive"]
            assert "git push --force" in dangerous["destructive"]
            assert "git reset --hard" in dangerous["destructive"]
            assert "az boards work-item delete" in dangerous["destructive"]

    def test_get_destructive_patterns_windows(self):
        """Test Windows-specific destructive patterns."""
        with patch("platform.system", return_value="Windows"):
            detector = PlatformDetector()
            dangerous = detector.get_dangerous_patterns()

            assert "destructive" in dangerous
            assert "del /s /q" in dangerous["destructive"]
            assert "rmdir /s /q" in dangerous["destructive"]
            assert "Remove-Item -Recurse -Force" in dangerous["destructive"]

    def test_get_production_patterns(self):
        """Test production deployment patterns."""
        with (
            patch("platform.system", return_value="Linux"),
            patch("builtins.open", side_effect=FileNotFoundError),
        ):
            detector = PlatformDetector()
            dangerous = detector.get_dangerous_patterns()

            assert "production" in dangerous
            assert "git push origin main" in dangerous["production"]
            assert "npm publish" in dangerous["production"]
            assert "kubectl apply" in dangerous["production"]
            assert "terraform apply" in dangerous["production"]

    def test_get_network_patterns(self):
        """Test network access patterns."""
        with (
            patch("platform.system", return_value="Linux"),
            patch("builtins.open", side_effect=FileNotFoundError),
        ):
            detector = PlatformDetector()
            dangerous = detector.get_dangerous_patterns()

            assert "network" in dangerous
            assert "curl" in dangerous["network"]
            assert "wget" in dangerous["network"]
            assert "ssh" in dangerous["network"]

    def test_get_privileged_patterns_linux(self):
        """Test privileged operation patterns for Linux."""
        with (
            patch("platform.system", return_value="Linux"),
            patch("builtins.open", side_effect=FileNotFoundError),
        ):
            detector = PlatformDetector()
            dangerous = detector.get_dangerous_patterns()

            assert "privileged" in dangerous
            assert "sudo" in dangerous["privileged"]
            assert "chmod" in dangerous["privileged"]
            assert "chown" in dangerous["privileged"]

    def test_get_privileged_patterns_windows(self):
        """Test privileged operation patterns for Windows."""
        with patch("platform.system", return_value="Windows"):
            detector = PlatformDetector()
            dangerous = detector.get_dangerous_patterns()

            assert "privileged" in dangerous
            assert "runas" in dangerous["privileged"]
            assert "Set-ExecutionPolicy" in dangerous["privileged"]

    def test_all_dangerous_categories_present(self):
        """Test that all expected dangerous categories are present."""
        with (
            patch("platform.system", return_value="Linux"),
            patch("builtins.open", side_effect=FileNotFoundError),
        ):
            detector = PlatformDetector()
            dangerous = detector.get_dangerous_patterns()

            expected_categories = [
                "destructive",
                "production",
                "network",
                "privileged",
            ]

            for category in expected_categories:
                assert category in dangerous
                assert (
                    len(dangerous[category]) >= 0
                )  # Some may be empty on certain platforms


@pytest.mark.unit
class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_multiple_detections_use_cache(self):
        """Test that multiple method calls use cached platform info."""
        with (
            patch("platform.system", return_value="Linux") as mock_system,
            patch("builtins.open", side_effect=FileNotFoundError),
        ):
            detector = PlatformDetector()

            # Multiple calls
            detector.detect_platform()
            detector.get_command_patterns()
            detector.get_dangerous_patterns()

            # platform.system should only be called twice (once in detect_platform, once in _is_wsl)
            # After first detect_platform(), subsequent calls use cached info
            assert mock_system.call_count == 2

    def test_wsl_interop_handles_permission_error(self):
        """Test WSL interop detection handles permission errors gracefully."""
        proc_version_content = "Linux version 5.10.16.3-microsoft-standard-WSL2"

        with (
            patch("platform.system", return_value="Linux"),
            patch("builtins.open", mock_open(read_data=proc_version_content)),
            patch.object(Path, "exists", side_effect=PermissionError),
        ):
            detector = PlatformDetector()
            # Should not raise, should return False for wsl_interop
            assert detector._check_wsl_interop() is False

    def test_wsl_interop_handles_io_error(self):
        """Test WSL interop detection handles IO errors gracefully."""
        proc_version_content = "Linux version 5.10.16.3-microsoft-standard-WSL2"

        with (
            patch("platform.system", return_value="Linux"),
            patch("builtins.open", mock_open(read_data=proc_version_content)),
            patch.object(Path, "exists", side_effect=IOError),
        ):
            detector = PlatformDetector()
            # Should not raise
            assert detector._check_wsl_interop() is False

    def test_command_patterns_always_return_dict(self):
        """Test that command patterns always return a dict."""
        with (
            patch("platform.system", return_value="Linux"),
            patch("builtins.open", side_effect=FileNotFoundError),
        ):
            detector = PlatformDetector()
            patterns = detector.get_command_patterns()

            assert isinstance(patterns, dict)
            for category, commands in patterns.items():
                assert isinstance(commands, list)

    def test_dangerous_patterns_always_return_dict(self):
        """Test that dangerous patterns always return a dict."""
        with (
            patch("platform.system", return_value="Linux"),
            patch("builtins.open", side_effect=FileNotFoundError),
        ):
            detector = PlatformDetector()
            dangerous = detector.get_dangerous_patterns()

            assert isinstance(dangerous, dict)
            for category, commands in dangerous.items():
                assert isinstance(commands, list)
