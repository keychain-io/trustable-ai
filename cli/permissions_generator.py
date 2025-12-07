"""
Permissions Template Generator for Claude Code Safe-Action Configuration.

Generates platform-aware permission templates for .claude/settings.local.json that
auto-approve safe operations while requiring approval for destructive ones.

Usage:
    from cli.permissions_generator import PermissionsTemplateGenerator
    from cli.platform_detector import PlatformDetector

    detector = PlatformDetector()
    platform_info = detector.detect_platform()

    generator = PermissionsTemplateGenerator()
    permissions = generator.generate_permissions(platform_info, mode="development")
    generator.write_to_file(permissions, ".claude/settings.local.json")
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

from cli.platform_detector import PlatformDetector


class PermissionsTemplateGenerator:
    """
    Generate Claude Code permission templates based on platform and workflow mode.

    Responsibilities:
    - Generate safe-action permission patterns for auto-approval
    - Generate deny patterns for destructive operations
    - Support development vs production workflow modes
    - Write permissions to .claude/settings.local.json
    - Use conservative defaults when uncertain
    """

    def __init__(self) -> None:
        """Initialize permissions template generator."""
        self._detector = PlatformDetector()

    def generate_permissions(
        self, platform_info: Dict[str, Any], mode: str = "development"
    ) -> Dict[str, Any]:
        """
        Generate permissions configuration based on platform and mode.

        Args:
            platform_info: Platform information from PlatformDetector.detect_platform()
            mode: Workflow mode - "development" (permissive) or "production" (conservative)

        Returns:
            Dict with permissions structure:
                {
                    "permissions": {
                        "allow": [...],  # Auto-approve patterns
                        "deny": [...],   # Always deny patterns
                        "ask": [...]     # Always ask for approval patterns
                    }
                }

        Raises:
            ValueError: If mode is not "development" or "production"

        Examples:
            >>> generator = PermissionsTemplateGenerator()
            >>> platform_info = {"os": "Linux", "is_wsl": True, "shell": "bash"}
            >>> permissions = generator.generate_permissions(platform_info, mode="development")
            >>> "git status" in str(permissions["permissions"]["allow"])
            True
        """
        if mode not in ["development", "production"]:
            raise ValueError(
                f"Invalid mode '{mode}'. Must be 'development' or 'production'."
            )

        # Get safe patterns that can be auto-approved
        safe_patterns = self.get_safe_patterns(platform_info, mode)

        # Get dangerous patterns that should be denied or require approval
        deny_patterns = self.get_deny_patterns(platform_info)

        # Get patterns that should always ask (neither auto-approve nor deny)
        ask_patterns = self._get_ask_patterns(platform_info, mode)

        return {
            "permissions": {
                "allow": safe_patterns,
                "deny": deny_patterns,
                "ask": ask_patterns,
            }
        }

    def write_to_file(
        self, permissions: Dict[str, Any], output_path: Union[str, Path]
    ) -> None:
        """
        Write permissions configuration to settings.local.json.

        Args:
            permissions: Permissions dict from generate_permissions()
            output_path: Path to settings.local.json file

        Raises:
            OSError: If file cannot be written
            ValueError: If permissions dict is invalid

        Examples:
            >>> generator = PermissionsTemplateGenerator()
            >>> permissions = generator.generate_permissions(...)
            >>> generator.write_to_file(permissions, ".claude/settings.local.json")
        """
        output_path = Path(output_path)

        # Validate permissions structure
        if "permissions" not in permissions:
            raise ValueError(
                "Invalid permissions dict: missing 'permissions' key"
            )

        required_keys = ["allow", "deny", "ask"]
        for key in required_keys:
            if key not in permissions["permissions"]:
                raise ValueError(
                    f"Invalid permissions dict: missing 'permissions.{key}' key"
                )

        # Create parent directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write JSON with pretty formatting
        with output_path.open("w") as f:
            json.dump(permissions, f, indent=2)

    def get_safe_patterns(
        self, platform_info: Dict[str, Any], mode: str = "development"
    ) -> List[str]:
        """
        Get safe command patterns that can be auto-approved.

        Safe operations include:
        - Git read-only: git status, git diff, git log
        - Git local writes: git add, git commit (but not push)
        - Work tracking CRUD (not delete): az boards work-item create/update/show
        - File reads: cat, ls, grep, find
        - Test execution: pytest
        - Build operations: npm install, pip install
        - Code inspection: pylint, mypy, eslint

        Args:
            platform_info: Platform information from PlatformDetector
            mode: Workflow mode ("development" or "production")

        Returns:
            List of bash command patterns in Claude Code format:
                ["Bash(git status:*)", "Bash(git diff:*)", ...]

        Examples:
            >>> generator = PermissionsTemplateGenerator()
            >>> platform_info = {"os": "Linux", "is_wsl": False, "shell": "bash"}
            >>> patterns = generator.get_safe_patterns(platform_info, "development")
            >>> "Bash(git status:*)" in patterns
            True
        """
        # Update detector's platform info to match the provided one
        self._detector._platform_info = platform_info

        # Get command patterns from platform detector
        command_patterns = self._detector.get_command_patterns()

        safe_patterns: List[str] = []

        # Convert each command pattern to Claude Code format: Bash(command:*)
        for category, commands in command_patterns.items():
            for command in commands:
                # In development mode, all command patterns are safe
                # In production mode, be more conservative
                if mode == "production":
                    # In production, only allow truly read-only operations
                    if category in ["git", "file", "inspect"]:
                        # Further filter git commands to exclude writes
                        if category == "git" and any(
                            write_cmd in command
                            for write_cmd in ["add", "commit", "stash"]
                        ):
                            continue
                        safe_patterns.append(f"Bash({command}:*)")
                else:
                    # Development mode: allow all patterns
                    safe_patterns.append(f"Bash({command}:*)")

        # Always include these common safe operations regardless of mode
        common_safe = [
            "Bash(pwd:*)",
            "Bash(whoami:*)",
            "Bash(date:*)",
            "Bash(echo:*)",
            "Bash(which:*)",
        ]
        safe_patterns.extend(common_safe)

        # Sort and deduplicate
        return sorted(list(set(safe_patterns)))

    def get_deny_patterns(self, platform_info: Dict[str, Any]) -> List[str]:
        """
        Get dangerous patterns that should always be denied without asking.

        Dangerous operations include:
        - Destructive: rm -rf, git push --force, git reset --hard
        - Work item deletion: az boards work-item delete
        - Privileged operations that modify system: sudo rm, chmod 777

        Note: Some dangerous operations (like git push) should be in "ask" not "deny"
        because they may be legitimate in certain contexts. This method only returns
        operations that should NEVER be auto-approved.

        Args:
            platform_info: Platform information from PlatformDetector

        Returns:
            List of bash command patterns that are always denied:
                ["Bash(rm -rf /:*)", "Bash(git push --force:*)", ...]

        Examples:
            >>> generator = PermissionsTemplateGenerator()
            >>> platform_info = {"os": "Linux", "is_wsl": False, "shell": "bash"}
            >>> patterns = generator.get_deny_patterns(platform_info)
            >>> any("rm -rf" in p for p in patterns)
            True
        """
        # Update detector's platform info
        self._detector._platform_info = platform_info

        # Get dangerous patterns from platform detector
        dangerous_patterns = self._detector.get_dangerous_patterns()

        deny_patterns: List[str] = []

        # Only include truly destructive operations in deny list
        # Other dangerous operations should be in "ask" list
        destructive_commands = dangerous_patterns.get("destructive", [])

        for command in destructive_commands:
            # Include only the most dangerous destructive commands in deny
            # Others will be in "ask" for user discretion
            if any(
                dangerous in command
                for dangerous in [
                    "rm -rf /",  # Delete root
                    "--force",  # Force operations
                    "--hard",  # Hard resets
                    "delete",  # Deletions (work items, resources)
                    "/s /q",  # Windows recursive delete
                    "-Recurse -Force",  # PowerShell recursive force delete
                ]
            ):
                deny_patterns.append(f"Bash({command}:*)")

        # Sort and deduplicate
        return sorted(list(set(deny_patterns)))

    def _get_ask_patterns(
        self, platform_info: Dict[str, Any], mode: str
    ) -> List[str]:
        """
        Get patterns that should always ask for approval (neither auto-approve nor deny).

        Ask patterns include operations that may be legitimate but require user decision:
        - Git push (to remote repositories)
        - Production deployments
        - Network access (curl, wget, ssh)
        - Privileged operations (sudo, chmod)

        Args:
            platform_info: Platform information from PlatformDetector
            mode: Workflow mode ("development" or "production")

        Returns:
            List of bash command patterns requiring approval

        Examples:
            >>> generator = PermissionsTemplateGenerator()
            >>> platform_info = {"os": "Linux", "is_wsl": False, "shell": "bash"}
            >>> patterns = generator._get_ask_patterns(platform_info, "development")
            >>> any("git push" in p for p in patterns)
            True
        """
        # Update detector's platform info
        self._detector._platform_info = platform_info

        dangerous_patterns = self._detector.get_dangerous_patterns()

        ask_patterns: List[str] = []

        # Production deployments always require approval
        for command in dangerous_patterns.get("production", []):
            ask_patterns.append(f"Bash({command}:*)")

        # Network access requires approval
        for command in dangerous_patterns.get("network", []):
            ask_patterns.append(f"Bash({command}:*)")

        # Privileged operations require approval
        for command in dangerous_patterns.get("privileged", []):
            ask_patterns.append(f"Bash({command}:*)")

        # Git push (without --force) should ask, not deny
        # This catches normal pushes that aren't in the deny list
        ask_patterns.append("Bash(git push:*)")

        # In production mode, be more conservative - ask for more operations
        if mode == "production":
            # In production, also ask for local git writes
            ask_patterns.extend(
                [
                    "Bash(git add:*)",
                    "Bash(git commit:*)",
                    "Bash(git stash:*)",
                ]
            )

            # Ask for work tracking operations in production
            ask_patterns.extend(
                [
                    "Bash(az boards work-item create:*)",
                    "Bash(az boards work-item update:*)",
                ]
            )

        # Sort and deduplicate
        return sorted(list(set(ask_patterns)))
