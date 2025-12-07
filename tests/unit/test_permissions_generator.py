"""
Unit tests for Permissions Template Generator.

Tests permissions generation for different platforms and workflow modes.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch

from cli.permissions_generator import PermissionsTemplateGenerator
from cli.platform_detector import PlatformDetector


@pytest.mark.unit
class TestPermissionsGeneration:
    """Test permissions generation for different modes and platforms."""

    def test_generate_permissions_development_mode(self):
        """Test permissions generation in development mode."""
        generator = PermissionsTemplateGenerator()
        platform_info = {
            "os": "Linux",
            "is_wsl": False,
            "shell": "bash",
            "platform_specific": {},
        }

        permissions = generator.generate_permissions(
            platform_info, mode="development"
        )

        assert "permissions" in permissions
        assert "allow" in permissions["permissions"]
        assert "deny" in permissions["permissions"]
        assert "ask" in permissions["permissions"]

        # Development mode should be permissive
        assert len(permissions["permissions"]["allow"]) > 0
        assert isinstance(permissions["permissions"]["allow"], list)
        assert isinstance(permissions["permissions"]["deny"], list)
        assert isinstance(permissions["permissions"]["ask"], list)

    def test_generate_permissions_production_mode(self):
        """Test permissions generation in production mode."""
        generator = PermissionsTemplateGenerator()
        platform_info = {
            "os": "Linux",
            "is_wsl": False,
            "shell": "bash",
            "platform_specific": {},
        }

        permissions = generator.generate_permissions(
            platform_info, mode="production"
        )

        # Production mode should be more conservative
        assert "permissions" in permissions
        assert len(permissions["permissions"]["allow"]) > 0
        assert len(permissions["permissions"]["ask"]) > 0

        # Production should have fewer auto-approved operations
        dev_permissions = generator.generate_permissions(
            platform_info, mode="development"
        )
        assert len(permissions["permissions"]["allow"]) < len(
            dev_permissions["permissions"]["allow"]
        )

    def test_generate_permissions_invalid_mode(self):
        """Test that invalid mode raises ValueError."""
        generator = PermissionsTemplateGenerator()
        platform_info = {
            "os": "Linux",
            "is_wsl": False,
            "shell": "bash",
            "platform_specific": {},
        }

        with pytest.raises(ValueError, match="Invalid mode"):
            generator.generate_permissions(platform_info, mode="invalid")

    def test_generate_permissions_windows(self):
        """Test permissions generation for Windows platform."""
        generator = PermissionsTemplateGenerator()
        platform_info = {
            "os": "Windows",
            "is_wsl": False,
            "shell": "powershell",
            "platform_specific": {
                "command_extensions": [".exe", ".bat", ".cmd", ".ps1"]
            },
        }

        permissions = generator.generate_permissions(
            platform_info, mode="development"
        )

        assert "permissions" in permissions
        # Should still have basic permissions structure
        assert "allow" in permissions["permissions"]
        assert "deny" in permissions["permissions"]

    def test_generate_permissions_macos(self):
        """Test permissions generation for macOS platform."""
        generator = PermissionsTemplateGenerator()
        platform_info = {
            "os": "Darwin",
            "is_wsl": False,
            "shell": "zsh",
            "platform_specific": {"command_extensions": [""]},
        }

        permissions = generator.generate_permissions(
            platform_info, mode="development"
        )

        assert "permissions" in permissions
        assert "allow" in permissions["permissions"]

    def test_generate_permissions_wsl(self):
        """Test permissions generation for WSL platform."""
        generator = PermissionsTemplateGenerator()
        platform_info = {
            "os": "Linux",
            "is_wsl": True,
            "shell": "bash",
            "platform_specific": {"wsl_interop": True},
        }

        permissions = generator.generate_permissions(
            platform_info, mode="development"
        )

        assert "permissions" in permissions
        assert "allow" in permissions["permissions"]


@pytest.mark.unit
class TestSafePatterns:
    """Test safe command pattern generation."""

    def test_safe_patterns_include_git_readonly(self):
        """Test that safe patterns include git read-only commands."""
        generator = PermissionsTemplateGenerator()
        platform_info = {
            "os": "Linux",
            "is_wsl": False,
            "shell": "bash",
            "platform_specific": {},
        }

        patterns = generator.get_safe_patterns(platform_info, mode="development")

        # Git read-only commands should be safe
        assert any("git status" in p for p in patterns)
        assert any("git diff" in p for p in patterns)
        assert any("git log" in p for p in patterns)

    def test_safe_patterns_include_git_local_writes_in_dev_mode(self):
        """Test that safe patterns include git local writes in development mode."""
        generator = PermissionsTemplateGenerator()
        platform_info = {
            "os": "Linux",
            "is_wsl": False,
            "shell": "bash",
            "platform_specific": {},
        }

        patterns = generator.get_safe_patterns(platform_info, mode="development")

        # Git local writes should be safe in development
        assert any("git add" in p for p in patterns)
        assert any("git commit" in p for p in patterns)

    def test_safe_patterns_exclude_git_writes_in_production_mode(self):
        """Test that git writes are excluded in production mode."""
        generator = PermissionsTemplateGenerator()
        platform_info = {
            "os": "Linux",
            "is_wsl": False,
            "shell": "bash",
            "platform_specific": {},
        }

        patterns = generator.get_safe_patterns(platform_info, mode="production")

        # Git writes should not be in safe patterns in production
        assert not any("git add" in p for p in patterns)
        assert not any("git commit" in p for p in patterns)

    def test_safe_patterns_include_file_operations(self):
        """Test that safe patterns include file read operations."""
        generator = PermissionsTemplateGenerator()
        platform_info = {
            "os": "Linux",
            "is_wsl": False,
            "shell": "bash",
            "platform_specific": {},
        }

        patterns = generator.get_safe_patterns(platform_info, mode="development")

        # File operations should be safe
        assert any("cat" in p for p in patterns)
        assert any("ls" in p for p in patterns)
        assert any("grep" in p for p in patterns)

    def test_safe_patterns_include_test_execution(self):
        """Test that safe patterns include test execution commands."""
        generator = PermissionsTemplateGenerator()
        platform_info = {
            "os": "Linux",
            "is_wsl": False,
            "shell": "bash",
            "platform_specific": {},
        }

        patterns = generator.get_safe_patterns(platform_info, mode="development")

        # Test execution should be safe
        assert any("pytest" in p for p in patterns)

    def test_safe_patterns_include_work_tracking_in_dev_mode(self):
        """Test that work tracking CRUD is safe in development mode."""
        generator = PermissionsTemplateGenerator()
        platform_info = {
            "os": "Linux",
            "is_wsl": False,
            "shell": "bash",
            "platform_specific": {},
        }

        patterns = generator.get_safe_patterns(platform_info, mode="development")

        # Work tracking CRUD should be safe in development
        assert any("az boards work-item show" in p for p in patterns)
        assert any("az boards work-item create" in p for p in patterns)
        assert any("az boards work-item update" in p for p in patterns)

    def test_safe_patterns_include_common_operations(self):
        """Test that common safe operations are always included."""
        generator = PermissionsTemplateGenerator()
        platform_info = {
            "os": "Linux",
            "is_wsl": False,
            "shell": "bash",
            "platform_specific": {},
        }

        patterns = generator.get_safe_patterns(platform_info, mode="production")

        # Common operations should always be safe
        assert any("pwd" in p for p in patterns)
        assert any("echo" in p for p in patterns)
        assert any("date" in p for p in patterns)

    def test_safe_patterns_claude_code_format(self):
        """Test that safe patterns use correct Claude Code format."""
        generator = PermissionsTemplateGenerator()
        platform_info = {
            "os": "Linux",
            "is_wsl": False,
            "shell": "bash",
            "platform_specific": {},
        }

        patterns = generator.get_safe_patterns(platform_info, mode="development")

        # All patterns should use Bash(...:*) format
        for pattern in patterns:
            assert pattern.startswith("Bash(")
            assert pattern.endswith(":*)")

    def test_safe_patterns_no_duplicates(self):
        """Test that safe patterns contain no duplicates."""
        generator = PermissionsTemplateGenerator()
        platform_info = {
            "os": "Linux",
            "is_wsl": False,
            "shell": "bash",
            "platform_specific": {},
        }

        patterns = generator.get_safe_patterns(platform_info, mode="development")

        # Should have no duplicates
        assert len(patterns) == len(set(patterns))

    def test_safe_patterns_sorted(self):
        """Test that safe patterns are sorted."""
        generator = PermissionsTemplateGenerator()
        platform_info = {
            "os": "Linux",
            "is_wsl": False,
            "shell": "bash",
            "platform_specific": {},
        }

        patterns = generator.get_safe_patterns(platform_info, mode="development")

        # Should be sorted
        assert patterns == sorted(patterns)


@pytest.mark.unit
class TestDenyPatterns:
    """Test dangerous/deny pattern generation."""

    def test_deny_patterns_include_destructive_operations(self):
        """Test that deny patterns include destructive operations."""
        generator = PermissionsTemplateGenerator()
        platform_info = {
            "os": "Linux",
            "is_wsl": False,
            "shell": "bash",
            "platform_specific": {},
        }

        patterns = generator.get_deny_patterns(platform_info)

        # Destructive operations should be denied
        # Check for force operations and hard resets which are destructive
        assert any("--force" in p for p in patterns)
        assert any("--hard" in p for p in patterns)
        # Should have some deny patterns
        assert len(patterns) > 0

    def test_deny_patterns_include_work_item_deletion(self):
        """Test that work item deletion is denied."""
        generator = PermissionsTemplateGenerator()
        platform_info = {
            "os": "Linux",
            "is_wsl": False,
            "shell": "bash",
            "platform_specific": {},
        }

        patterns = generator.get_deny_patterns(platform_info)

        # Work item deletion should be denied
        assert any("delete" in p for p in patterns)

    def test_deny_patterns_windows_destructive(self):
        """Test Windows-specific destructive patterns are denied."""
        generator = PermissionsTemplateGenerator()
        platform_info = {
            "os": "Windows",
            "is_wsl": False,
            "shell": "powershell",
            "platform_specific": {},
        }

        patterns = generator.get_deny_patterns(platform_info)

        # Windows destructive commands should be denied
        assert any("/s /q" in p or "-Recurse -Force" in p for p in patterns)

    def test_deny_patterns_claude_code_format(self):
        """Test that deny patterns use correct Claude Code format."""
        generator = PermissionsTemplateGenerator()
        platform_info = {
            "os": "Linux",
            "is_wsl": False,
            "shell": "bash",
            "platform_specific": {},
        }

        patterns = generator.get_deny_patterns(platform_info)

        # All patterns should use Bash(...:*) format
        for pattern in patterns:
            assert pattern.startswith("Bash(")
            assert pattern.endswith(":*)")

    def test_deny_patterns_no_duplicates(self):
        """Test that deny patterns contain no duplicates."""
        generator = PermissionsTemplateGenerator()
        platform_info = {
            "os": "Linux",
            "is_wsl": False,
            "shell": "bash",
            "platform_specific": {},
        }

        patterns = generator.get_deny_patterns(platform_info)

        # Should have no duplicates
        assert len(patterns) == len(set(patterns))

    def test_deny_patterns_sorted(self):
        """Test that deny patterns are sorted."""
        generator = PermissionsTemplateGenerator()
        platform_info = {
            "os": "Linux",
            "is_wsl": False,
            "shell": "bash",
            "platform_specific": {},
        }

        patterns = generator.get_deny_patterns(platform_info)

        # Should be sorted
        assert patterns == sorted(patterns)


@pytest.mark.unit
class TestAskPatterns:
    """Test ask pattern generation (require approval but not deny)."""

    def test_ask_patterns_include_git_push_in_dev_mode(self):
        """Test that git push requires approval in development mode."""
        generator = PermissionsTemplateGenerator()
        platform_info = {
            "os": "Linux",
            "is_wsl": False,
            "shell": "bash",
            "platform_specific": {},
        }

        permissions = generator.generate_permissions(
            platform_info, mode="development"
        )

        # git push should be in ask list
        assert any("git push" in p for p in permissions["permissions"]["ask"])

    def test_ask_patterns_include_production_deployments(self):
        """Test that production deployments require approval."""
        generator = PermissionsTemplateGenerator()
        platform_info = {
            "os": "Linux",
            "is_wsl": False,
            "shell": "bash",
            "platform_specific": {},
        }

        ask_patterns = generator._get_ask_patterns(
            platform_info, mode="development"
        )

        # Production deployments should require approval
        assert any("kubectl" in p for p in ask_patterns)
        assert any("terraform" in p for p in ask_patterns)

    def test_ask_patterns_include_network_access(self):
        """Test that network access requires approval."""
        generator = PermissionsTemplateGenerator()
        platform_info = {
            "os": "Linux",
            "is_wsl": False,
            "shell": "bash",
            "platform_specific": {},
        }

        ask_patterns = generator._get_ask_patterns(
            platform_info, mode="development"
        )

        # Network access should require approval
        assert any("curl" in p for p in ask_patterns)
        assert any("wget" in p for p in ask_patterns)
        assert any("ssh" in p for p in ask_patterns)

    def test_ask_patterns_include_privileged_operations(self):
        """Test that privileged operations require approval."""
        generator = PermissionsTemplateGenerator()
        platform_info = {
            "os": "Linux",
            "is_wsl": False,
            "shell": "bash",
            "platform_specific": {},
        }

        ask_patterns = generator._get_ask_patterns(
            platform_info, mode="development"
        )

        # Privileged operations should require approval
        assert any("sudo" in p for p in ask_patterns)

    def test_ask_patterns_more_conservative_in_production(self):
        """Test that production mode has more ask patterns than development."""
        generator = PermissionsTemplateGenerator()
        platform_info = {
            "os": "Linux",
            "is_wsl": False,
            "shell": "bash",
            "platform_specific": {},
        }

        dev_ask = generator._get_ask_patterns(platform_info, mode="development")
        prod_ask = generator._get_ask_patterns(platform_info, mode="production")

        # Production should have more operations requiring approval
        assert len(prod_ask) > len(dev_ask)

    def test_ask_patterns_include_work_tracking_in_production(self):
        """Test that work tracking operations require approval in production."""
        generator = PermissionsTemplateGenerator()
        platform_info = {
            "os": "Linux",
            "is_wsl": False,
            "shell": "bash",
            "platform_specific": {},
        }

        ask_patterns = generator._get_ask_patterns(
            platform_info, mode="production"
        )

        # Work tracking should require approval in production
        assert any("az boards work-item create" in p for p in ask_patterns)
        assert any("az boards work-item update" in p for p in ask_patterns)


@pytest.mark.unit
class TestFileWriting:
    """Test permissions file writing."""

    def test_write_to_file_creates_json(self, tmp_path):
        """Test that permissions are written as valid JSON."""
        generator = PermissionsTemplateGenerator()
        platform_info = {
            "os": "Linux",
            "is_wsl": False,
            "shell": "bash",
            "platform_specific": {},
        }

        permissions = generator.generate_permissions(
            platform_info, mode="development"
        )

        output_path = tmp_path / "settings.local.json"
        generator.write_to_file(permissions, output_path)

        # File should exist
        assert output_path.exists()

        # Should be valid JSON
        with output_path.open("r") as f:
            loaded = json.load(f)

        assert loaded == permissions

    def test_write_to_file_creates_parent_directory(self, tmp_path):
        """Test that parent directory is created if it doesn't exist."""
        generator = PermissionsTemplateGenerator()
        platform_info = {
            "os": "Linux",
            "is_wsl": False,
            "shell": "bash",
            "platform_specific": {},
        }

        permissions = generator.generate_permissions(
            platform_info, mode="development"
        )

        output_path = tmp_path / "subdir" / "settings.local.json"
        generator.write_to_file(permissions, output_path)

        # File and parent directory should exist
        assert output_path.exists()
        assert output_path.parent.exists()

    def test_write_to_file_invalid_permissions_missing_key(self, tmp_path):
        """Test that invalid permissions dict raises ValueError."""
        generator = PermissionsTemplateGenerator()

        output_path = tmp_path / "settings.local.json"

        # Missing "permissions" key
        with pytest.raises(ValueError, match="missing 'permissions' key"):
            generator.write_to_file({"invalid": "data"}, output_path)

    def test_write_to_file_invalid_permissions_missing_allow(self, tmp_path):
        """Test that missing 'allow' key raises ValueError."""
        generator = PermissionsTemplateGenerator()

        output_path = tmp_path / "settings.local.json"

        # Missing "allow" key
        with pytest.raises(ValueError, match="missing 'permissions.allow' key"):
            generator.write_to_file(
                {"permissions": {"deny": [], "ask": []}}, output_path
            )

    def test_write_to_file_invalid_permissions_missing_deny(self, tmp_path):
        """Test that missing 'deny' key raises ValueError."""
        generator = PermissionsTemplateGenerator()

        output_path = tmp_path / "settings.local.json"

        # Missing "deny" key
        with pytest.raises(ValueError, match="missing 'permissions.deny' key"):
            generator.write_to_file(
                {"permissions": {"allow": [], "ask": []}}, output_path
            )

    def test_write_to_file_invalid_permissions_missing_ask(self, tmp_path):
        """Test that missing 'ask' key raises ValueError."""
        generator = PermissionsTemplateGenerator()

        output_path = tmp_path / "settings.local.json"

        # Missing "ask" key
        with pytest.raises(ValueError, match="missing 'permissions.ask' key"):
            generator.write_to_file(
                {"permissions": {"allow": [], "deny": []}}, output_path
            )

    def test_write_to_file_pretty_formatted(self, tmp_path):
        """Test that JSON is pretty-formatted with indentation."""
        generator = PermissionsTemplateGenerator()
        platform_info = {
            "os": "Linux",
            "is_wsl": False,
            "shell": "bash",
            "platform_specific": {},
        }

        permissions = generator.generate_permissions(
            platform_info, mode="development"
        )

        output_path = tmp_path / "settings.local.json"
        generator.write_to_file(permissions, output_path)

        # Read file content
        content = output_path.read_text()

        # Should be indented (pretty-printed)
        assert "  " in content  # Has indentation
        assert "\n" in content  # Has newlines

    def test_write_to_file_accepts_string_path(self, tmp_path):
        """Test that write_to_file accepts string path."""
        generator = PermissionsTemplateGenerator()
        platform_info = {
            "os": "Linux",
            "is_wsl": False,
            "shell": "bash",
            "platform_specific": {},
        }

        permissions = generator.generate_permissions(
            platform_info, mode="development"
        )

        output_path = str(tmp_path / "settings.local.json")
        generator.write_to_file(permissions, output_path)

        # File should exist
        assert Path(output_path).exists()

    def test_write_to_file_overwrites_existing(self, tmp_path):
        """Test that writing overwrites existing file."""
        generator = PermissionsTemplateGenerator()
        platform_info = {
            "os": "Linux",
            "is_wsl": False,
            "shell": "bash",
            "platform_specific": {},
        }

        output_path = tmp_path / "settings.local.json"

        # Write initial content
        output_path.write_text('{"old": "data"}')

        # Write new permissions
        permissions = generator.generate_permissions(
            platform_info, mode="development"
        )
        generator.write_to_file(permissions, output_path)

        # Should be overwritten
        with output_path.open("r") as f:
            loaded = json.load(f)

        assert loaded == permissions
        assert "old" not in loaded


@pytest.mark.unit
class TestIntegrationWithPlatformDetector:
    """Test integration with PlatformDetector."""

    def test_uses_platform_detector_for_command_patterns(self):
        """Test that generator uses PlatformDetector for command patterns."""
        generator = PermissionsTemplateGenerator()
        platform_info = {
            "os": "Linux",
            "is_wsl": False,
            "shell": "bash",
            "platform_specific": {},
        }

        patterns = generator.get_safe_patterns(platform_info, mode="development")

        # Should include patterns from PlatformDetector.get_command_patterns()
        detector = PlatformDetector()
        detector._platform_info = platform_info
        detector_patterns = detector.get_command_patterns()

        # Check that some patterns from detector are in safe patterns
        for category in ["git", "file", "test"]:
            for command in detector_patterns[category][:2]:  # Check first 2
                assert any(command in p for p in patterns)

    def test_uses_platform_detector_for_dangerous_patterns(self):
        """Test that generator uses PlatformDetector for dangerous patterns."""
        generator = PermissionsTemplateGenerator()
        platform_info = {
            "os": "Linux",
            "is_wsl": False,
            "shell": "bash",
            "platform_specific": {},
        }

        deny_patterns = generator.get_deny_patterns(platform_info)

        # Should include patterns from PlatformDetector.get_dangerous_patterns()
        detector = PlatformDetector()
        detector._platform_info = platform_info
        dangerous = detector.get_dangerous_patterns()

        # Check that some destructive patterns from detector are in deny
        destructive = dangerous["destructive"]
        # Verify that at least one destructive pattern made it into deny list
        assert len(deny_patterns) > 0
        # Check that deny patterns contain dangerous keywords
        assert any(
            any(keyword in p for keyword in ["--force", "--hard", "delete"])
            for p in deny_patterns
        )

    def test_end_to_end_permissions_generation(self):
        """Test end-to-end permissions generation flow."""
        # This simulates the expected usage
        detector = PlatformDetector()
        platform_info = detector.detect_platform()

        generator = PermissionsTemplateGenerator()
        permissions = generator.generate_permissions(
            platform_info, mode="development"
        )

        # Verify structure
        assert "permissions" in permissions
        assert all(
            key in permissions["permissions"] for key in ["allow", "deny", "ask"]
        )

        # Verify all values are lists
        assert all(
            isinstance(permissions["permissions"][key], list)
            for key in ["allow", "deny", "ask"]
        )

        # Verify all patterns are strings in correct format
        for key in ["allow", "deny", "ask"]:
            for pattern in permissions["permissions"][key]:
                assert isinstance(pattern, str)
                assert pattern.startswith("Bash(")
                assert pattern.endswith(":*)")


@pytest.mark.unit
class TestConservativeDefaults:
    """Test conservative defaults when uncertain."""

    def test_production_mode_excludes_writes_from_safe_patterns(self):
        """Test that production mode is conservative about write operations."""
        generator = PermissionsTemplateGenerator()
        platform_info = {
            "os": "Linux",
            "is_wsl": False,
            "shell": "bash",
            "platform_specific": {},
        }

        safe_patterns = generator.get_safe_patterns(
            platform_info, mode="production"
        )

        # Git writes should not be safe in production
        assert not any("git add" in p for p in safe_patterns)
        assert not any("git commit" in p for p in safe_patterns)

    def test_uncertain_operations_in_ask_not_allow(self):
        """Test that uncertain operations require approval."""
        generator = PermissionsTemplateGenerator()
        platform_info = {
            "os": "Linux",
            "is_wsl": False,
            "shell": "bash",
            "platform_specific": {},
        }

        permissions = generator.generate_permissions(
            platform_info, mode="development"
        )

        # Network operations are uncertain - should ask
        assert any("curl" in p for p in permissions["permissions"]["ask"])
        assert any("ssh" in p for p in permissions["permissions"]["ask"])

        # Should not be in allow
        assert not any("curl" in p for p in permissions["permissions"]["allow"])

    def test_only_truly_destructive_in_deny(self):
        """Test that only truly destructive operations are denied."""
        generator = PermissionsTemplateGenerator()
        platform_info = {
            "os": "Linux",
            "is_wsl": False,
            "shell": "bash",
            "platform_specific": {},
        }

        deny_patterns = generator.get_deny_patterns(platform_info)

        # Only destructive patterns should be denied
        for pattern in deny_patterns:
            # Each pattern should contain at least one truly dangerous keyword
            assert any(
                dangerous in pattern
                for dangerous in [
                    "rm -rf",
                    "--force",
                    "--hard",
                    "delete",
                    "/s /q",
                    "-Recurse -Force",
                ]
            )
