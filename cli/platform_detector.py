"""
Platform Detection for Permission Configuration.

Detects OS platform (Windows, Linux, macOS, WSL) and generates platform-specific
command patterns for safe-action permission configuration.

Usage:
    from cli.platform_detector import PlatformDetector

    detector = PlatformDetector()
    platform_info = detector.detect_platform()
    # Returns: {"os": "Linux", "is_wsl": True, "shell": "bash"}

    patterns = detector.get_command_patterns()
    # Returns: {"git": ["git status", "git diff"], ...}
"""

import platform
import os
from pathlib import Path
from typing import Dict, List, Any, Optional


class PlatformDetector:
    """
    Detect OS platform and generate platform-specific command patterns.

    Responsibilities:
    - Detect OS platform (Windows, Linux, macOS)
    - Identify Windows Subsystem for Linux (WSL)
    - Generate appropriate permission rules for each platform
    - Support platform-specific command pattern generation
    """

    def __init__(self) -> None:
        """Initialize platform detector."""
        self._platform_info: Optional[Dict[str, Any]] = None

    def detect_platform(self) -> Dict[str, Any]:
        """
        Detect current OS platform and environment.

        Returns:
            Dict with keys:
                - os: str - Platform OS ("Windows", "Linux", "Darwin")
                - is_wsl: bool - True if running in WSL
                - shell: str - Default shell ("powershell", "bash", "zsh")
                - platform_specific: Dict - Additional platform-specific info

        Examples:
            >>> detector = PlatformDetector()
            >>> detector.detect_platform()
            {"os": "Linux", "is_wsl": True, "shell": "bash", "platform_specific": {...}}
        """
        if self._platform_info is not None:
            return self._platform_info

        os_name = platform.system()
        is_wsl = self._is_wsl()

        # Determine default shell
        if os_name == "Windows":
            shell = "powershell"
        elif os_name == "Darwin":
            # macOS uses zsh by default since Catalina
            shell = os.environ.get("SHELL", "/bin/zsh").split("/")[-1]
        else:
            # Linux/WSL
            shell = os.environ.get("SHELL", "/bin/bash").split("/")[-1]

        self._platform_info = {
            "os": os_name,
            "is_wsl": is_wsl,
            "shell": shell,
            "platform_specific": self._get_platform_specific_info(os_name, is_wsl),
        }

        return self._platform_info

    def _is_wsl(self) -> bool:
        """
        Detect if running in Windows Subsystem for Linux.

        WSL detection strategy:
        1. Check /proc/version for "microsoft" or "WSL" (most reliable)
        2. Check if /proc/sys/kernel/osrelease contains "microsoft"
        3. WSL only exists on Linux, so return False for other platforms

        Returns:
            bool: True if running in WSL, False otherwise
        """
        if platform.system() != "Linux":
            return False

        # Strategy 1: Check /proc/version
        try:
            with open("/proc/version", "r") as f:
                version_info = f.read().lower()
                if "microsoft" in version_info or "wsl" in version_info:
                    return True
        except (FileNotFoundError, PermissionError, IOError):
            # If we can't read /proc/version, try alternative methods
            pass

        # Strategy 2: Check /proc/sys/kernel/osrelease
        try:
            with open("/proc/sys/kernel/osrelease", "r") as f:
                osrelease_info = f.read().lower()
                if "microsoft" in osrelease_info:
                    return True
        except (FileNotFoundError, PermissionError, IOError):
            # If both checks fail, assume not WSL
            pass

        return False

    def _get_platform_specific_info(self, os_name: str, is_wsl: bool) -> Dict[str, Any]:
        """
        Get platform-specific information.

        Args:
            os_name: Platform OS name
            is_wsl: Whether running in WSL

        Returns:
            Dict with platform-specific information
        """
        info: Dict[str, Any] = {
            "architecture": platform.machine(),
            "release": platform.release(),
        }

        if os_name == "Windows":
            info["windows_version"] = platform.version()
            info["command_extensions"] = [".exe", ".bat", ".cmd", ".ps1"]
        elif os_name == "Darwin":
            info["macos_version"] = platform.mac_ver()[0]
            info["command_extensions"] = [""]
        else:  # Linux or WSL
            info["command_extensions"] = [""]
            if is_wsl:
                info["wsl_interop"] = self._check_wsl_interop()

        return info

    def _check_wsl_interop(self) -> bool:
        """
        Check if WSL interop is enabled (can run Windows executables).

        Returns:
            bool: True if WSL interop is enabled
        """
        try:
            # Check if /proc/sys/fs/binfmt_misc/WSLInterop exists
            interop_path = Path("/proc/sys/fs/binfmt_misc/WSLInterop")
            if interop_path.exists():
                return True
        except (PermissionError, IOError):
            pass

        return False

    def get_command_patterns(self) -> Dict[str, List[str]]:
        """
        Get platform-specific command patterns for permission configuration.

        Returns safe operations categorized by tool/purpose.

        Returns:
            Dict mapping category to list of safe command patterns:
                - git: Git read-only and local operations
                - file: File reading operations
                - work_tracking: Work tracking CRUD operations
                - test: Test execution commands
                - build: Build and compilation commands
                - inspect: Code inspection and analysis

        Examples:
            >>> detector = PlatformDetector()
            >>> patterns = detector.get_command_patterns()
            >>> patterns["git"]
            ["git status", "git diff", "git log", ...]
        """
        platform_info = self.detect_platform()
        os_name = platform_info["os"]
        is_wsl = platform_info["is_wsl"]

        patterns: Dict[str, List[str]] = {}

        # Git patterns (safe read-only and local operations)
        patterns["git"] = self._get_git_patterns()

        # File operations (read-only)
        patterns["file"] = self._get_file_patterns(os_name, is_wsl)

        # Work tracking operations
        patterns["work_tracking"] = self._get_work_tracking_patterns(os_name)

        # Test execution
        patterns["test"] = self._get_test_patterns(os_name)

        # Build and compilation
        patterns["build"] = self._get_build_patterns(os_name)

        # Code inspection and analysis
        patterns["inspect"] = self._get_inspect_patterns(os_name)

        return patterns

    def _get_git_patterns(self) -> List[str]:
        """Get safe Git command patterns."""
        return [
            "git status",
            "git diff",
            "git log",
            "git show",
            "git branch",
            "git remote -v",
            "git fetch",
            "git add",
            "git commit",
            "git stash",
        ]

    def _get_file_patterns(self, os_name: str, is_wsl: bool) -> List[str]:
        """Get safe file operation patterns."""
        patterns = ["ls", "cat", "head", "tail", "grep", "find", "tree"]

        if os_name == "Windows":
            # Windows-specific file commands
            patterns.extend(["dir", "type", "findstr"])

        return patterns

    def _get_work_tracking_patterns(self, os_name: str) -> List[str]:
        """Get safe work tracking command patterns."""
        patterns = [
            # Azure DevOps commands (read and write, but not delete)
            "az boards work-item show",
            "az boards work-item create",
            "az boards work-item update",
            "az boards query",
            "az boards iteration",
            "az boards area",
        ]

        # Add platform-specific variations if needed
        # (Azure CLI is cross-platform, so same commands work everywhere)

        return patterns

    def _get_test_patterns(self, os_name: str) -> List[str]:
        """Get safe test execution patterns."""
        patterns = [
            "pytest",
            "python -m pytest",
            "npm test",
            "npm run test",
            "mvn test",
            "gradle test",
            "go test",
            "cargo test",
        ]

        if os_name == "Windows":
            # Windows uses python instead of python3
            patterns.extend(["python -m unittest"])
        else:
            patterns.extend(["python3 -m pytest", "python3 -m unittest"])

        return patterns

    def _get_build_patterns(self, os_name: str) -> List[str]:
        """Get safe build command patterns."""
        patterns = [
            "npm install",
            "npm run build",
            "pip install",
            "mvn compile",
            "gradle build",
            "make",
            "cargo build",
            "go build",
        ]

        if os_name == "Windows":
            patterns.extend(["msbuild"])

        return patterns

    def _get_inspect_patterns(self, os_name: str) -> List[str]:
        """Get safe code inspection patterns."""
        return [
            "pylint",
            "flake8",
            "mypy",
            "black --check",
            "ruff",
            "eslint",
            "tsc --noEmit",
        ]

    def get_dangerous_patterns(self) -> Dict[str, List[str]]:
        """
        Get dangerous command patterns that should require approval.

        Returns:
            Dict mapping category to list of dangerous patterns:
                - destructive: Commands that delete or force-overwrite
                - production: Commands that affect production systems
                - network: Commands that access external networks
                - privileged: Commands requiring elevated permissions

        Examples:
            >>> detector = PlatformDetector()
            >>> dangerous = detector.get_dangerous_patterns()
            >>> dangerous["destructive"]
            ["rm -rf", "git push --force", ...]
        """
        platform_info = self.detect_platform()
        os_name = platform_info["os"]

        patterns: Dict[str, List[str]] = {
            "destructive": self._get_destructive_patterns(os_name),
            "production": self._get_production_patterns(),
            "network": self._get_network_patterns(),
            "privileged": self._get_privileged_patterns(os_name),
        }

        return patterns

    def _get_destructive_patterns(self, os_name: str) -> List[str]:
        """Get destructive command patterns."""
        patterns = [
            "rm -rf",
            "git push --force",
            "git reset --hard",
            "git clean -fd",
            "az boards work-item delete",
            "az group delete",
        ]

        if os_name == "Windows":
            patterns.extend(
                [
                    "del /s /q",
                    "rmdir /s /q",
                    "Remove-Item -Recurse -Force",
                ]
            )

        return patterns

    def _get_production_patterns(self) -> List[str]:
        """Get production deployment patterns."""
        return [
            "git push origin main",
            "git push origin master",
            "npm publish",
            "az webapp",
            "az container",
            "az aks",
            "kubectl apply",
            "docker push",
            "terraform apply",
        ]

    def _get_network_patterns(self) -> List[str]:
        """Get network access patterns."""
        return [
            "curl",
            "wget",
            "ping",
            "ssh",
            "scp",
            "rsync",
        ]

    def _get_privileged_patterns(self, os_name: str) -> List[str]:
        """Get privileged operation patterns."""
        patterns = []

        if os_name in ["Linux", "Darwin"]:
            patterns.extend(
                [
                    "sudo",
                    "su",
                    "chmod",
                    "chown",
                ]
            )
        elif os_name == "Windows":
            patterns.extend(
                [
                    "runas",
                    "Set-ExecutionPolicy",
                ]
            )

        return patterns
