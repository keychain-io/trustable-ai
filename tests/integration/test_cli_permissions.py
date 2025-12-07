"""
Integration tests for CLI permissions command.

Tests the complete permissions validate workflow with real file system operations.
"""

import pytest
import json
from pathlib import Path
from click.testing import CliRunner

from cli.main import cli


@pytest.mark.integration
class TestPermissionsValidateCommand:
    """Test suite for trustable-ai permissions validate command."""

    def test_validate_file_not_found(self):
        """Test validate command when permissions file doesn't exist."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["permissions", "validate"])

            assert result.exit_code == 2  # Error exit code
            assert "not found" in result.output.lower()
            assert "trustable-ai init" in result.output

    def test_validate_valid_permissions(self):
        """Test validate command with valid permissions file."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Create .claude directory and valid settings file
            claude_dir = Path(".claude")
            claude_dir.mkdir()

            settings = {
                "permissions": {
                    "allow": [
                        "Bash(git status:*)",
                        "Bash(git diff:*)",
                        "Bash(ls:*)",
                    ],
                    "deny": ["Bash(rm -rf:*)"],
                    "ask": ["Bash(git push:*)", "Bash(curl:*)"],
                }
            }

            settings_path = claude_dir / "settings.local.json"
            with settings_path.open("w") as f:
                json.dump(settings, f)

            result = runner.invoke(cli, ["permissions", "validate"])

            assert result.exit_code == 0
            assert "Validating permissions" in result.output
            assert "Permissions file found" in result.output
            assert "Valid JSON structure" in result.output
            assert "All required fields present" in result.output
            assert "No issues found" in result.output

    def test_validate_shows_counts(self):
        """Test validate command displays permission counts."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            claude_dir = Path(".claude")
            claude_dir.mkdir()

            settings = {
                "permissions": {
                    "allow": ["Bash(git status:*)", "Bash(ls:*)"],
                    "deny": ["Bash(rm -rf:*)"],
                    "ask": ["Bash(git push:*)", "Bash(curl:*)", "Bash(ssh:*)"],
                }
            }

            settings_path = claude_dir / "settings.local.json"
            with settings_path.open("w") as f:
                json.dump(settings, f)

            result = runner.invoke(cli, ["permissions", "validate"])

            assert result.exit_code == 0
            assert "Validation Results" in result.output
            assert "Auto-approved (allow): 2" in result.output
            assert "Require approval (ask): 3" in result.output
            assert "Denied: 1" in result.output

    def test_validate_invalid_json(self):
        """Test validate command with invalid JSON."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            claude_dir = Path(".claude")
            claude_dir.mkdir()

            settings_path = claude_dir / "settings.local.json"
            settings_path.write_text("{ invalid json !!")

            result = runner.invoke(cli, ["permissions", "validate"])

            assert result.exit_code == 2
            assert "Invalid JSON" in result.output

    def test_validate_missing_permissions_key(self):
        """Test validate command when permissions key is missing."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            claude_dir = Path(".claude")
            claude_dir.mkdir()

            settings = {"other_key": "value"}

            settings_path = claude_dir / "settings.local.json"
            with settings_path.open("w") as f:
                json.dump(settings, f)

            result = runner.invoke(cli, ["permissions", "validate"])

            assert result.exit_code == 2
            assert "Missing 'permissions' key" in result.output

    def test_validate_missing_required_fields(self):
        """Test validate command when required fields are missing."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            claude_dir = Path(".claude")
            claude_dir.mkdir()

            # Missing 'ask' field
            settings = {"permissions": {"allow": [], "deny": []}}

            settings_path = claude_dir / "settings.local.json"
            with settings_path.open("w") as f:
                json.dump(settings, f)

            result = runner.invoke(cli, ["permissions", "validate"])

            assert result.exit_code == 2
            assert "Missing required field" in result.output
            assert "permissions.ask" in result.output

    def test_validate_with_warnings(self):
        """Test validate command with warnings (duplicates, unsafe patterns)."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            claude_dir = Path(".claude")
            claude_dir.mkdir()

            settings = {
                "permissions": {
                    "allow": [
                        "Bash(git status:*)",
                        "Bash(git status:*)",  # Duplicate
                        "Bash(git push:*)",  # Should be in ask
                    ],
                    "deny": [],
                    "ask": [],
                }
            }

            settings_path = claude_dir / "settings.local.json"
            with settings_path.open("w") as f:
                json.dump(settings, f)

            result = runner.invoke(cli, ["permissions", "validate"])

            assert result.exit_code == 1  # Warning exit code
            assert "Warnings:" in result.output
            assert "Duplicate" in result.output
            assert "Recommendations:" in result.output

    def test_validate_with_conflicts(self):
        """Test validate command with conflicting patterns."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            claude_dir = Path(".claude")
            claude_dir.mkdir()

            settings = {
                "permissions": {
                    "allow": ["Bash(git status:*)"],
                    "deny": ["Bash(git status:*)"],  # Conflict
                    "ask": [],
                }
            }

            settings_path = claude_dir / "settings.local.json"
            with settings_path.open("w") as f:
                json.dump(settings, f)

            result = runner.invoke(cli, ["permissions", "validate"])

            assert result.exit_code == 2  # Error exit code
            assert "Errors:" in result.output
            assert "Conflict" in result.output
            assert "allow and deny" in result.output

    def test_validate_custom_settings_path(self):
        """Test validate command with custom settings path."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            custom_dir = Path("custom")
            custom_dir.mkdir()

            settings = {
                "permissions": {
                    "allow": ["Bash(git status:*)"],
                    "deny": [],
                    "ask": [],
                }
            }

            settings_path = custom_dir / "settings.json"
            with settings_path.open("w") as f:
                json.dump(settings, f)

            result = runner.invoke(
                cli, ["permissions", "validate", "--settings-path", str(settings_path)]
            )

            assert result.exit_code == 0
            assert str(settings_path) in result.output

    def test_validate_displays_recommendations(self):
        """Test validate command displays actionable recommendations."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            claude_dir = Path(".claude")
            claude_dir.mkdir()

            settings = {
                "permissions": {
                    "allow": [
                        "Bash(git status:*)",
                        "Bash(git status:*)",  # Duplicate
                    ],
                    "deny": [],
                    "ask": [],
                }
            }

            settings_path = claude_dir / "settings.local.json"
            with settings_path.open("w") as f:
                json.dump(settings, f)

            result = runner.invoke(cli, ["permissions", "validate"])

            assert result.exit_code == 1
            assert "Recommendations:" in result.output
            assert "Remove duplicate patterns" in result.output

    def test_validate_multiple_errors_and_warnings(self):
        """Test validate command with both errors and warnings."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            claude_dir = Path(".claude")
            claude_dir.mkdir()

            settings = {
                "permissions": {
                    "allow": [
                        "Bash(git status:*)",
                        "Bash(git status:*)",  # Duplicate (warning)
                        "Bash(git push:*)",  # Overly permissive (warning)
                    ],
                    "deny": ["Bash(git status:*)"],  # Conflict (error)
                    "ask": [],
                }
            }

            settings_path = claude_dir / "settings.local.json"
            with settings_path.open("w") as f:
                json.dump(settings, f)

            result = runner.invoke(cli, ["permissions", "validate"])

            assert result.exit_code == 2  # Errors take precedence
            assert "Errors:" in result.output
            assert "Warnings:" in result.output
            assert "Conflict" in result.output
            assert "Duplicate" in result.output


@pytest.mark.integration
class TestPermissionsCommandGroup:
    """Test permissions command group."""

    def test_permissions_help(self):
        """Test permissions command shows help."""
        runner = CliRunner()

        result = runner.invoke(cli, ["permissions", "--help"])

        assert result.exit_code == 0
        assert "permissions" in result.output.lower()
        assert "validate" in result.output.lower()

    def test_permissions_validate_help(self):
        """Test permissions validate subcommand shows help."""
        runner = CliRunner()

        result = runner.invoke(cli, ["permissions", "validate", "--help"])

        assert result.exit_code == 0
        assert "validate" in result.output.lower()
        assert "settings-path" in result.output.lower()


@pytest.mark.integration
class TestPermissionsValidateIntegrationWithInit:
    """Test permissions validate integration with init command."""

    def test_validate_after_init(self):
        """Test that permissions file generated by init validates successfully."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Run init to generate permissions
            init_result = runner.invoke(cli, ["init", "--no-interactive"])
            assert init_result.exit_code == 0

            # Now validate the generated permissions
            validate_result = runner.invoke(cli, ["permissions", "validate"])

            assert validate_result.exit_code == 0
            assert "Valid JSON structure" in validate_result.output
            assert "All required fields present" in validate_result.output

    def test_validate_counts_match_init_summary(self):
        """Test that validate shows same counts as init summary."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Run init
            init_result = runner.invoke(cli, ["init", "--no-interactive"])
            assert init_result.exit_code == 0

            # Extract counts from init output
            init_output = init_result.output

            # Run validate
            validate_result = runner.invoke(cli, ["permissions", "validate"])
            validate_output = validate_result.output

            # Both should show permission counts
            assert "Auto-approved" in init_output
            assert "Auto-approved" in validate_output

    def test_validate_detects_manual_corruption(self):
        """Test that validate detects manual corruption after init."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Run init
            init_result = runner.invoke(cli, ["init", "--no-interactive"])
            assert init_result.exit_code == 0

            # Manually corrupt the permissions file
            settings_path = Path(".claude/settings.local.json")
            with settings_path.open("r") as f:
                settings = json.load(f)

            # Add a conflicting pattern
            settings["permissions"]["allow"].append("Bash(git status:*)")
            settings["permissions"]["deny"].append("Bash(git status:*)")

            with settings_path.open("w") as f:
                json.dump(settings, f)

            # Validate should detect the conflict
            validate_result = runner.invoke(cli, ["permissions", "validate"])

            assert validate_result.exit_code == 2
            assert "Conflict" in validate_result.output


@pytest.mark.integration
class TestExitCodes:
    """Test exit codes for different validation scenarios."""

    def test_exit_code_0_for_valid(self):
        """Test exit code 0 for valid permissions."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            claude_dir = Path(".claude")
            claude_dir.mkdir()

            settings = {
                "permissions": {
                    "allow": ["Bash(git status:*)"],
                    "deny": [],
                    "ask": [],
                }
            }

            with (claude_dir / "settings.local.json").open("w") as f:
                json.dump(settings, f)

            result = runner.invoke(cli, ["permissions", "validate"])
            assert result.exit_code == 0

    def test_exit_code_1_for_warnings(self):
        """Test exit code 1 for warnings only."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            claude_dir = Path(".claude")
            claude_dir.mkdir()

            settings = {
                "permissions": {
                    "allow": [
                        "Bash(git status:*)",
                        "Bash(git status:*)",  # Duplicate (warning)
                    ],
                    "deny": [],
                    "ask": [],
                }
            }

            with (claude_dir / "settings.local.json").open("w") as f:
                json.dump(settings, f)

            result = runner.invoke(cli, ["permissions", "validate"])
            assert result.exit_code == 1

    def test_exit_code_2_for_errors(self):
        """Test exit code 2 for errors."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            claude_dir = Path(".claude")
            claude_dir.mkdir()

            settings = {
                "permissions": {
                    "allow": ["Bash(git status:*)"],
                    "deny": ["Bash(git status:*)"],  # Conflict (error)
                    "ask": [],
                }
            }

            with (claude_dir / "settings.local.json").open("w") as f:
                json.dump(settings, f)

            result = runner.invoke(cli, ["permissions", "validate"])
            assert result.exit_code == 2

    def test_exit_code_2_for_file_not_found(self):
        """Test exit code 2 when file doesn't exist."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["permissions", "validate"])
            assert result.exit_code == 2


@pytest.mark.integration
class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_validate_empty_permissions_lists(self):
        """Test validate with empty permission lists."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            claude_dir = Path(".claude")
            claude_dir.mkdir()

            settings = {"permissions": {"allow": [], "deny": [], "ask": []}}

            with (claude_dir / "settings.local.json").open("w") as f:
                json.dump(settings, f)

            result = runner.invoke(cli, ["permissions", "validate"])

            # Valid structure, no errors
            assert result.exit_code == 0
            assert "Auto-approved (allow): 0" in result.output

    def test_validate_with_extra_settings(self):
        """Test validate ignores extra settings beyond permissions."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            claude_dir = Path(".claude")
            claude_dir.mkdir()

            settings = {
                "custom_setting": "value",
                "another_config": 123,
                "permissions": {
                    "allow": ["Bash(git status:*)"],
                    "deny": [],
                    "ask": [],
                },
            }

            with (claude_dir / "settings.local.json").open("w") as f:
                json.dump(settings, f)

            result = runner.invoke(cli, ["permissions", "validate"])

            assert result.exit_code == 0
            assert "Valid JSON structure" in result.output

    def test_validate_pattern_format_warnings(self):
        """Test validate warns about invalid pattern formats."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            claude_dir = Path(".claude")
            claude_dir.mkdir()

            settings = {
                "permissions": {
                    "allow": [
                        "git status",  # Missing Bash(...:*) format
                    ],
                    "deny": [],
                    "ask": [],
                }
            }

            with (claude_dir / "settings.local.json").open("w") as f:
                json.dump(settings, f)

            result = runner.invoke(cli, ["permissions", "validate"])

            assert result.exit_code == 1  # Warning
            assert "invalid format" in result.output.lower()
            assert "expected format" in result.output.lower()
