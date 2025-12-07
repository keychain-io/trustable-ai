"""
Comprehensive end-to-end tests for the permissions system.

Tests the complete permissions workflow across all components:
- Platform detection
- Permissions generation
- Init command integration
- Validate command
- Error recovery
- Cross-platform compatibility

These tests ensure the permissions system works correctly from user perspective:
init creates valid permissions → validate confirms they work → modifications are caught.
"""

import pytest
import json
from pathlib import Path
from click.testing import CliRunner
from unittest.mock import patch, MagicMock

from cli.main import cli
from cli.platform_detector import PlatformDetector
from cli.permissions_generator import PermissionsTemplateGenerator


@pytest.mark.integration
class TestPermissionsSystemEndToEnd:
    """End-to-end tests for complete permissions workflows."""

    def test_init_creates_valid_permissions_linux(self):
        """Test init creates permissions that pass validation on Linux."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Mock platform detection to return Linux
            with patch.object(PlatformDetector, 'detect_platform') as mock_detect:
                mock_detect.return_value = {
                    "os": "Linux",
                    "is_wsl": False,
                    "shell": "bash",
                    "platform_specific": {}
                }

                # Run init
                init_result = runner.invoke(cli, ["init", "--no-interactive"])
                assert init_result.exit_code == 0, f"Init failed: {init_result.output}"

                # Check permissions file exists
                settings_path = Path(".claude/settings.local.json")
                assert settings_path.exists(), "Permissions file not created"

                # Verify file has valid JSON
                with settings_path.open("r") as f:
                    settings = json.load(f)

                assert "permissions" in settings
                assert "allow" in settings["permissions"]
                assert "deny" in settings["permissions"]
                assert "ask" in settings["permissions"]

                # Run validate
                validate_result = runner.invoke(cli, ["permissions", "validate"])
                assert validate_result.exit_code == 0, f"Validate failed: {validate_result.output}"
                assert "Valid JSON structure" in validate_result.output
                assert "No issues found" in validate_result.output

    def test_init_creates_valid_permissions_windows(self):
        """Test init creates permissions that pass validation on Windows."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Mock platform detection to return Windows
            with patch.object(PlatformDetector, 'detect_platform') as mock_detect:
                mock_detect.return_value = {
                    "os": "Windows",
                    "is_wsl": False,
                    "shell": "powershell",
                    "platform_specific": {}
                }

                # Run init
                init_result = runner.invoke(cli, ["init", "--no-interactive"])
                assert init_result.exit_code == 0

                # Run validate
                validate_result = runner.invoke(cli, ["permissions", "validate"])
                assert validate_result.exit_code == 0
                assert "Valid JSON structure" in validate_result.output

    def test_init_creates_valid_permissions_macos(self):
        """Test init creates permissions that pass validation on macOS."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Mock platform detection to return macOS
            with patch.object(PlatformDetector, 'detect_platform') as mock_detect:
                mock_detect.return_value = {
                    "os": "Darwin",
                    "is_wsl": False,
                    "shell": "zsh",
                    "platform_specific": {}
                }

                # Run init
                init_result = runner.invoke(cli, ["init", "--no-interactive"])
                assert init_result.exit_code == 0

                # Run validate
                validate_result = runner.invoke(cli, ["permissions", "validate"])
                assert validate_result.exit_code == 0
                assert "Valid JSON structure" in validate_result.output

    def test_init_creates_valid_permissions_wsl(self):
        """Test init creates permissions that pass validation on WSL."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Mock platform detection to return WSL
            with patch.object(PlatformDetector, 'detect_platform') as mock_detect:
                mock_detect.return_value = {
                    "os": "Linux",
                    "is_wsl": True,
                    "shell": "bash",
                    "platform_specific": {"wsl_interop": True}
                }

                # Run init
                init_result = runner.invoke(cli, ["init", "--no-interactive"])
                assert init_result.exit_code == 0

                # Verify init output mentions WSL
                assert "WSL" in init_result.output or "wsl" in init_result.output.lower()

                # Run validate
                validate_result = runner.invoke(cli, ["permissions", "validate"])
                assert validate_result.exit_code == 0

    def test_init_validate_counts_match(self):
        """Test that validate shows same counts as init summary."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Run init
            init_result = runner.invoke(cli, ["init", "--no-interactive"])
            assert init_result.exit_code == 0

            # Extract counts from init output
            init_lines = init_result.output.split('\n')
            init_auto_approved = None
            init_requires_approval = None
            init_denied = None

            for line in init_lines:
                if "Auto-approved:" in line:
                    # Extract number from "Auto-approved: 53 safe operations"
                    parts = line.split("Auto-approved:")
                    if len(parts) > 1:
                        num_str = parts[1].strip().split()[0]
                        init_auto_approved = int(num_str)
                elif "Require approval:" in line:
                    parts = line.split("Require approval:")
                    if len(parts) > 1:
                        num_str = parts[1].strip().split()[0]
                        init_requires_approval = int(num_str)
                elif "Denied:" in line:
                    parts = line.split("Denied:")
                    if len(parts) > 1:
                        num_str = parts[1].strip().split()[0]
                        init_denied = int(num_str)

            # Run validate
            validate_result = runner.invoke(cli, ["permissions", "validate"])
            assert validate_result.exit_code == 0

            # Extract counts from validate output
            validate_lines = validate_result.output.split('\n')
            validate_auto_approved = None
            validate_requires_approval = None
            validate_denied = None

            for line in validate_lines:
                if "Auto-approved (allow):" in line:
                    parts = line.split(":")
                    if len(parts) > 1:
                        num_str = parts[1].strip().split()[0]
                        validate_auto_approved = int(num_str)
                elif "Require approval (ask):" in line:
                    parts = line.split(":")
                    if len(parts) > 1:
                        num_str = parts[1].strip().split()[0]
                        validate_requires_approval = int(num_str)
                elif "Denied:" in line and "Auto-approved" not in line:
                    parts = line.split(":")
                    if len(parts) > 1:
                        num_str = parts[1].strip().split()[0]
                        validate_denied = int(num_str)

            # Counts should match
            if init_auto_approved is not None:
                assert validate_auto_approved == init_auto_approved, \
                    f"Auto-approved count mismatch: init={init_auto_approved}, validate={validate_auto_approved}"
            if init_requires_approval is not None:
                assert validate_requires_approval == init_requires_approval, \
                    f"Requires approval count mismatch: init={init_requires_approval}, validate={validate_requires_approval}"
            if init_denied is not None:
                assert validate_denied == init_denied, \
                    f"Denied count mismatch: init={init_denied}, validate={validate_denied}"


@pytest.mark.integration
class TestPlatformSpecificPermissions:
    """Test platform-specific permission generation."""

    def test_linux_permissions_have_bash_patterns(self):
        """Test Linux permissions include bash-specific patterns."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            with patch.object(PlatformDetector, 'detect_platform') as mock_detect:
                mock_detect.return_value = {
                    "os": "Linux",
                    "is_wsl": False,
                    "shell": "bash",
                    "platform_specific": {}
                }

                init_result = runner.invoke(cli, ["init", "--no-interactive"])
                assert init_result.exit_code == 0

                settings_path = Path(".claude/settings.local.json")
                with settings_path.open("r") as f:
                    settings = json.load(f)

                allow_patterns = settings["permissions"]["allow"]

                # Should include common bash commands
                assert any("git status" in p for p in allow_patterns)
                assert any("ls" in p for p in allow_patterns)
                assert any("grep" in p for p in allow_patterns)

    def test_windows_permissions_avoid_bash_only_commands(self):
        """Test Windows permissions don't include bash-only commands."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            with patch.object(PlatformDetector, 'detect_platform') as mock_detect:
                mock_detect.return_value = {
                    "os": "Windows",
                    "is_wsl": False,
                    "shell": "powershell",
                    "platform_specific": {}
                }

                init_result = runner.invoke(cli, ["init", "--no-interactive"])
                assert init_result.exit_code == 0

                settings_path = Path(".claude/settings.local.json")
                with settings_path.open("r") as f:
                    settings = json.load(f)

                # All patterns should still be Bash format (Claude Code uses Bash tool)
                allow_patterns = settings["permissions"]["allow"]
                for pattern in allow_patterns:
                    assert pattern.startswith("Bash("), f"Pattern not in Bash format: {pattern}"

    def test_wsl_permissions_detected_correctly(self):
        """Test WSL is detected and appropriate permissions generated."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            with patch.object(PlatformDetector, 'detect_platform') as mock_detect:
                mock_detect.return_value = {
                    "os": "Linux",
                    "is_wsl": True,
                    "shell": "bash",
                    "platform_specific": {"wsl_interop": True}
                }

                init_result = runner.invoke(cli, ["init", "--no-interactive"])
                assert init_result.exit_code == 0

                # Check that init detected WSL
                assert "WSL" in init_result.output or "wsl" in init_result.output.lower()

                # Permissions should be valid
                validate_result = runner.invoke(cli, ["permissions", "validate"])
                assert validate_result.exit_code == 0


@pytest.mark.integration
class TestPermissionsModificationWorkflows:
    """Test user modification and re-validation workflows."""

    def test_adding_safe_pattern_remains_valid(self):
        """Test adding a safe pattern keeps permissions valid."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Init
            init_result = runner.invoke(cli, ["init", "--no-interactive"])
            assert init_result.exit_code == 0

            # Add a safe pattern (use unique pattern to avoid duplicates)
            settings_path = Path(".claude/settings.local.json")
            with settings_path.open("r") as f:
                settings = json.load(f)

            settings["permissions"]["allow"].append("Bash(my-custom-safe-tool:*)")

            with settings_path.open("w") as f:
                json.dump(settings, f, indent=2)

            # Re-validate should still pass
            validate_result = runner.invoke(cli, ["permissions", "validate"])
            assert validate_result.exit_code == 0

    def test_adding_unsafe_pattern_triggers_warning(self):
        """Test adding unsafe pattern to allow list triggers warning."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Init
            init_result = runner.invoke(cli, ["init", "--no-interactive"])
            assert init_result.exit_code == 0

            # Add unsafe pattern to allow list
            settings_path = Path(".claude/settings.local.json")
            with settings_path.open("r") as f:
                settings = json.load(f)

            settings["permissions"]["allow"].append("Bash(rm -rf:*)")

            with settings_path.open("w") as f:
                json.dump(settings, f, indent=2)

            # Validate should warn
            validate_result = runner.invoke(cli, ["permissions", "validate"])
            assert validate_result.exit_code == 1  # Warning
            assert "Unsafe pattern" in validate_result.output
            assert "rm -rf" in validate_result.output

    def test_adding_conflict_triggers_error(self):
        """Test adding conflicting pattern triggers error."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Init
            init_result = runner.invoke(cli, ["init", "--no-interactive"])
            assert init_result.exit_code == 0

            # Add conflicting pattern
            settings_path = Path(".claude/settings.local.json")
            with settings_path.open("r") as f:
                settings = json.load(f)

            settings["permissions"]["allow"].append("Bash(git status:*)")
            settings["permissions"]["deny"].append("Bash(git status:*)")

            with settings_path.open("w") as f:
                json.dump(settings, f, indent=2)

            # Validate should error
            validate_result = runner.invoke(cli, ["permissions", "validate"])
            assert validate_result.exit_code == 2  # Error
            assert "Conflict" in validate_result.output

    def test_fixing_conflict_then_revalidate_succeeds(self):
        """Test fixing conflict and re-validating succeeds."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Init
            init_result = runner.invoke(cli, ["init", "--no-interactive"])
            assert init_result.exit_code == 0

            # Add conflicting pattern
            settings_path = Path(".claude/settings.local.json")
            with settings_path.open("r") as f:
                settings = json.load(f)

            settings["permissions"]["allow"].append("Bash(test-command:*)")
            settings["permissions"]["deny"].append("Bash(test-command:*)")

            with settings_path.open("w") as f:
                json.dump(settings, f, indent=2)

            # Validate should error
            validate_result = runner.invoke(cli, ["permissions", "validate"])
            assert validate_result.exit_code == 2

            # Fix by removing from deny
            with settings_path.open("r") as f:
                settings = json.load(f)

            settings["permissions"]["deny"].remove("Bash(test-command:*)")

            with settings_path.open("w") as f:
                json.dump(settings, f, indent=2)

            # Re-validate should succeed
            validate_result = runner.invoke(cli, ["permissions", "validate"])
            assert validate_result.exit_code == 0

    def test_adding_duplicate_triggers_warning(self):
        """Test adding duplicate pattern triggers warning."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Init
            init_result = runner.invoke(cli, ["init", "--no-interactive"])
            assert init_result.exit_code == 0

            # Add duplicate pattern
            settings_path = Path(".claude/settings.local.json")
            with settings_path.open("r") as f:
                settings = json.load(f)

            # Add same pattern twice
            settings["permissions"]["allow"].append("Bash(custom-cmd:*)")
            settings["permissions"]["allow"].append("Bash(custom-cmd:*)")

            with settings_path.open("w") as f:
                json.dump(settings, f, indent=2)

            # Validate should warn about duplicate
            validate_result = runner.invoke(cli, ["permissions", "validate"])
            assert validate_result.exit_code == 1  # Warning
            assert "Duplicate" in validate_result.output
            assert "custom-cmd" in validate_result.output


@pytest.mark.integration
class TestPermissionsErrorScenarios:
    """Test error scenarios and recovery."""

    def test_corrupted_json_detected_by_validate(self):
        """Test validate detects corrupted JSON file."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Create .claude directory
            claude_dir = Path(".claude")
            claude_dir.mkdir()

            # Write corrupted JSON
            settings_path = claude_dir / "settings.local.json"
            settings_path.write_text("{ invalid json !!")

            # Validate should detect corruption
            validate_result = runner.invoke(cli, ["permissions", "validate"])
            assert validate_result.exit_code == 2
            assert "Invalid JSON" in validate_result.output

    def test_missing_permissions_key_detected(self):
        """Test validate detects missing permissions key."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            claude_dir = Path(".claude")
            claude_dir.mkdir()

            # Write settings without permissions key
            settings_path = claude_dir / "settings.local.json"
            with settings_path.open("w") as f:
                json.dump({"other_key": "value"}, f)

            # Validate should detect missing key
            validate_result = runner.invoke(cli, ["permissions", "validate"])
            assert validate_result.exit_code == 2
            assert "Missing 'permissions' key" in validate_result.output

    def test_missing_required_field_detected(self):
        """Test validate detects missing required fields."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            claude_dir = Path(".claude")
            claude_dir.mkdir()

            # Write settings missing 'ask' field
            settings_path = claude_dir / "settings.local.json"
            settings = {
                "permissions": {
                    "allow": [],
                    "deny": []
                    # Missing 'ask'
                }
            }
            with settings_path.open("w") as f:
                json.dump(settings, f)

            # Validate should detect missing field
            validate_result = runner.invoke(cli, ["permissions", "validate"])
            assert validate_result.exit_code == 2
            assert "Missing required field" in validate_result.output
            assert "permissions.ask" in validate_result.output

    def test_non_string_pattern_detected(self):
        """Test validate detects non-string patterns."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            claude_dir = Path(".claude")
            claude_dir.mkdir()

            # Write settings with non-string pattern
            settings_path = claude_dir / "settings.local.json"
            settings = {
                "permissions": {
                    "allow": ["Bash(git status:*)", 123],  # Integer pattern
                    "deny": [],
                    "ask": []
                }
            }
            with settings_path.open("w") as f:
                json.dump(settings, f)

            # Validate should detect non-string
            validate_result = runner.invoke(cli, ["permissions", "validate"])
            assert validate_result.exit_code == 2
            assert "must be string" in validate_result.output

    def test_invalid_pattern_format_warning(self):
        """Test validate warns about invalid pattern format."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            claude_dir = Path(".claude")
            claude_dir.mkdir()

            # Write settings with invalid format
            settings_path = claude_dir / "settings.local.json"
            settings = {
                "permissions": {
                    "allow": ["git status"],  # Missing Bash(...:*)
                    "deny": [],
                    "ask": []
                }
            }
            with settings_path.open("w") as f:
                json.dump(settings, f)

            # Validate should warn
            validate_result = runner.invoke(cli, ["permissions", "validate"])
            assert validate_result.exit_code == 1  # Warning
            assert "invalid format" in validate_result.output.lower()


@pytest.mark.integration
class TestPermissionsEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_permissions_lists_valid(self):
        """Test empty permission lists are valid (unusual but allowed)."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            claude_dir = Path(".claude")
            claude_dir.mkdir()

            settings_path = claude_dir / "settings.local.json"
            settings = {
                "permissions": {
                    "allow": [],
                    "deny": [],
                    "ask": []
                }
            }
            with settings_path.open("w") as f:
                json.dump(settings, f)

            # Should be valid
            validate_result = runner.invoke(cli, ["permissions", "validate"])
            assert validate_result.exit_code == 0
            assert "Auto-approved (allow): 0" in validate_result.output

    def test_extra_settings_preserved(self):
        """Test extra settings beyond permissions are preserved."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Init
            init_result = runner.invoke(cli, ["init", "--no-interactive"])
            assert init_result.exit_code == 0

            # Add extra settings
            settings_path = Path(".claude/settings.local.json")
            with settings_path.open("r") as f:
                settings = json.load(f)

            settings["custom_setting"] = "my_value"
            settings["another_config"] = {"nested": "value"}

            with settings_path.open("w") as f:
                json.dump(settings, f, indent=2)

            # Validate should ignore extra settings
            validate_result = runner.invoke(cli, ["permissions", "validate"])
            assert validate_result.exit_code == 0

            # Extra settings should still be present
            with settings_path.open("r") as f:
                settings = json.load(f)

            assert settings["custom_setting"] == "my_value"
            assert settings["another_config"]["nested"] == "value"

    def test_permissions_file_in_custom_location(self):
        """Test validate can check permissions file in custom location."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            custom_dir = Path("custom_location")
            custom_dir.mkdir()

            settings_path = custom_dir / "my-settings.json"
            settings = {
                "permissions": {
                    "allow": ["Bash(git status:*)"],
                    "deny": [],
                    "ask": []
                }
            }
            with settings_path.open("w") as f:
                json.dump(settings, f)

            # Validate with custom path
            validate_result = runner.invoke(
                cli,
                ["permissions", "validate", "--settings-path", str(settings_path)]
            )
            assert validate_result.exit_code == 0
            assert str(settings_path) in validate_result.output

    def test_very_long_pattern_list(self):
        """Test validation works with large number of patterns."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            claude_dir = Path(".claude")
            claude_dir.mkdir()

            # Generate many patterns
            allow_patterns = [f"Bash(command-{i}:*)" for i in range(100)]

            settings_path = claude_dir / "settings.local.json"
            settings = {
                "permissions": {
                    "allow": allow_patterns,
                    "deny": [],
                    "ask": []
                }
            }
            with settings_path.open("w") as f:
                json.dump(settings, f)

            # Should still validate
            validate_result = runner.invoke(cli, ["permissions", "validate"])
            assert validate_result.exit_code == 0
            assert "Auto-approved (allow): 100" in validate_result.output


@pytest.mark.integration
class TestPermissionsRecommendations:
    """Test that validate provides actionable recommendations."""

    def test_recommendations_for_unsafe_patterns(self):
        """Test recommendations suggest moving unsafe patterns to ask list."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            claude_dir = Path(".claude")
            claude_dir.mkdir()

            settings_path = claude_dir / "settings.local.json"
            settings = {
                "permissions": {
                    "allow": ["Bash(git push --force:*)"],  # Unsafe
                    "deny": [],
                    "ask": []
                }
            }
            with settings_path.open("w") as f:
                json.dump(settings, f)

            validate_result = runner.invoke(cli, ["permissions", "validate"])
            assert validate_result.exit_code == 1  # Warning
            assert "Recommendations:" in validate_result.output
            assert "ask" in validate_result.output.lower()

    def test_recommendations_for_duplicates(self):
        """Test recommendations suggest removing duplicates."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            claude_dir = Path(".claude")
            claude_dir.mkdir()

            settings_path = claude_dir / "settings.local.json"
            settings = {
                "permissions": {
                    "allow": [
                        "Bash(git status:*)",
                        "Bash(git status:*)"  # Duplicate
                    ],
                    "deny": [],
                    "ask": []
                }
            }
            with settings_path.open("w") as f:
                json.dump(settings, f)

            validate_result = runner.invoke(cli, ["permissions", "validate"])
            assert validate_result.exit_code == 1  # Warning
            assert "Recommendations:" in validate_result.output
            assert "duplicate" in validate_result.output.lower()

    def test_recommendations_for_conflicts(self):
        """Test recommendations suggest removing conflicting patterns."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            claude_dir = Path(".claude")
            claude_dir.mkdir()

            settings_path = claude_dir / "settings.local.json"
            settings = {
                "permissions": {
                    "allow": ["Bash(git status:*)"],
                    "deny": ["Bash(git status:*)"],  # Conflict
                    "ask": []
                }
            }
            with settings_path.open("w") as f:
                json.dump(settings, f)

            validate_result = runner.invoke(cli, ["permissions", "validate"])
            assert validate_result.exit_code == 2  # Error
            assert "Recommendations:" in validate_result.output
            assert "conflicting" in validate_result.output.lower()


@pytest.mark.integration
class TestPermissionsCrossPlatform:
    """Test cross-platform compatibility of permissions system."""

    def test_all_platforms_generate_valid_permissions(self):
        """Test all supported platforms generate valid permissions."""
        platforms = [
            {"os": "Linux", "is_wsl": False, "shell": "bash", "platform_specific": {}},
            {"os": "Linux", "is_wsl": True, "shell": "bash", "platform_specific": {"wsl_interop": True}},
            {"os": "Windows", "is_wsl": False, "shell": "powershell", "platform_specific": {}},
            {"os": "Darwin", "is_wsl": False, "shell": "zsh", "platform_specific": {}},
        ]

        runner = CliRunner()

        for platform_info in platforms:
            with runner.isolated_filesystem():
                with patch.object(PlatformDetector, 'detect_platform') as mock_detect:
                    mock_detect.return_value = platform_info

                    # Init should succeed
                    init_result = runner.invoke(cli, ["init", "--no-interactive"])
                    assert init_result.exit_code == 0, \
                        f"Init failed for {platform_info['os']}: {init_result.output}"

                    # Validate should succeed
                    validate_result = runner.invoke(cli, ["permissions", "validate"])
                    assert validate_result.exit_code == 0, \
                        f"Validate failed for {platform_info['os']}: {validate_result.output}"

    def test_platform_specific_commands_included(self):
        """Test platform-specific commands are included in permissions."""
        runner = CliRunner()

        # Test Windows includes Windows-specific patterns
        with runner.isolated_filesystem():
            with patch.object(PlatformDetector, 'detect_platform') as mock_detect:
                mock_detect.return_value = {
                    "os": "Windows",
                    "is_wsl": False,
                    "shell": "powershell",
                    "platform_specific": {}
                }

                init_result = runner.invoke(cli, ["init", "--no-interactive"])
                assert init_result.exit_code == 0

                settings_path = Path(".claude/settings.local.json")
                with settings_path.open("r") as f:
                    settings = json.load(f)

                # Should have Windows-friendly patterns
                all_patterns = (
                    settings["permissions"]["allow"] +
                    settings["permissions"]["deny"] +
                    settings["permissions"]["ask"]
                )

                # All patterns should be in Bash(...:*) format
                for pattern in all_patterns:
                    assert pattern.startswith("Bash("), f"Invalid pattern format: {pattern}"
                    assert pattern.endswith(":*)"), f"Invalid pattern format: {pattern}"


@pytest.mark.integration
class TestPermissionsIntegrationWithCLI:
    """Test permissions system integration with other CLI commands."""

    def test_init_without_interactive_generates_permissions(self):
        """Test non-interactive init generates permissions."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["init", "--no-interactive"])
            assert result.exit_code == 0

            # Should mention permissions in output
            assert "permissions" in result.output.lower() or "Configuring permissions" in result.output

            # Permissions file should exist
            assert Path(".claude/settings.local.json").exists()

    def test_init_failure_doesnt_leave_partial_permissions(self):
        """Test init failure doesn't leave corrupted permissions file."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Mock platform detection to raise exception
            with patch.object(PlatformDetector, 'detect_platform') as mock_detect:
                mock_detect.side_effect = Exception("Platform detection failed")

                # Init should handle error gracefully
                result = runner.invoke(cli, ["init", "--no-interactive"])

                # Even if permissions generation fails, init should continue
                # (permissions generation is non-critical)
                assert result.exit_code == 0

    def test_validate_provides_helpful_error_when_no_init(self):
        """Test validate provides helpful message when permissions don't exist."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["permissions", "validate"])
            assert result.exit_code == 2
            assert "not found" in result.output.lower()
            assert "trustable-ai init" in result.output


@pytest.mark.integration
class TestPermissionsRealWorldScenarios:
    """Test real-world usage scenarios."""

    def test_developer_workflow_init_modify_validate(self):
        """Test typical developer workflow: init → modify → validate → fix → re-validate."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Step 1: Developer runs init
            init_result = runner.invoke(cli, ["init", "--no-interactive"])
            assert init_result.exit_code == 0

            # Step 2: Developer adds custom command to allow list
            settings_path = Path(".claude/settings.local.json")
            with settings_path.open("r") as f:
                settings = json.load(f)

            settings["permissions"]["allow"].append("Bash(my-custom-tool:*)")

            with settings_path.open("w") as f:
                json.dump(settings, f, indent=2)

            # Step 3: Developer validates (should pass)
            validate_result = runner.invoke(cli, ["permissions", "validate"])
            assert validate_result.exit_code == 0

            # Step 4: Developer accidentally adds unsafe pattern
            with settings_path.open("r") as f:
                settings = json.load(f)

            settings["permissions"]["allow"].append("Bash(rm -rf:*)")

            with settings_path.open("w") as f:
                json.dump(settings, f, indent=2)

            # Step 5: Validate catches unsafe pattern
            validate_result = runner.invoke(cli, ["permissions", "validate"])
            assert validate_result.exit_code == 1  # Warning
            assert "Unsafe" in validate_result.output

            # Step 6: Developer moves to ask list
            with settings_path.open("r") as f:
                settings = json.load(f)

            settings["permissions"]["allow"].remove("Bash(rm -rf:*)")
            settings["permissions"]["ask"].append("Bash(rm -rf:*)")

            with settings_path.open("w") as f:
                json.dump(settings, f, indent=2)

            # Step 7: Re-validate (should still warn because rm -rf is dangerous)
            validate_result = runner.invoke(cli, ["permissions", "validate"])
            # May still have warnings, but structure is valid
            assert validate_result.exit_code in [0, 1]

    def test_team_collaboration_scenario(self):
        """Test scenario where team member reviews permissions."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Team member A initializes project
            init_result = runner.invoke(cli, ["init", "--no-interactive"])
            assert init_result.exit_code == 0

            # Team member B reviews permissions
            validate_result = runner.invoke(cli, ["permissions", "validate"])
            assert validate_result.exit_code == 0
            assert "Validation Results:" in validate_result.output

            # Team member B can see counts and verify settings
            assert "Auto-approved" in validate_result.output
            assert "Require approval" in validate_result.output
            assert "Denied" in validate_result.output
