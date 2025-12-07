"""
Unit tests for Permissions Validator.

Tests permissions validation logic for different scenarios.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch

from cli.commands.permissions import PermissionsValidator


@pytest.mark.unit
class TestPermissionsValidator:
    """Test permissions validator initialization."""

    def test_validator_initialization(self):
        """Test that validator initializes correctly."""
        validator = PermissionsValidator()
        assert validator is not None
        assert validator._detector is not None
        assert validator._platform_info is not None

    def test_validator_has_platform_info(self):
        """Test that validator detects platform on initialization."""
        validator = PermissionsValidator()
        platform_info = validator._platform_info

        assert "os" in platform_info
        assert "shell" in platform_info
        assert "is_wsl" in platform_info


@pytest.mark.unit
class TestValidateFileNotFound:
    """Test validation when file doesn't exist."""

    def test_validate_file_not_found(self, tmp_path):
        """Test validation fails when file doesn't exist."""
        validator = PermissionsValidator()
        settings_path = tmp_path / "nonexistent.json"

        is_valid, errors, warnings = validator.validate_file(settings_path)

        assert not is_valid
        assert len(errors) == 1
        assert "not found" in errors[0].lower()
        assert len(warnings) == 0


@pytest.mark.unit
class TestValidateInvalidJSON:
    """Test validation with invalid JSON."""

    def test_validate_invalid_json(self, tmp_path):
        """Test validation fails with invalid JSON."""
        validator = PermissionsValidator()
        settings_path = tmp_path / "settings.json"

        # Write invalid JSON
        settings_path.write_text("{ invalid json !!")

        is_valid, errors, warnings = validator.validate_file(settings_path)

        assert not is_valid
        assert len(errors) == 1
        assert "Invalid JSON" in errors[0]


@pytest.mark.unit
class TestValidateStructure:
    """Test permissions structure validation."""

    def test_validate_missing_permissions_key(self, tmp_path):
        """Test validation fails when permissions key is missing."""
        validator = PermissionsValidator()
        settings_path = tmp_path / "settings.json"

        # Write settings without permissions key
        settings_path.write_text(json.dumps({"other_key": "value"}))

        is_valid, errors, warnings = validator.validate_file(settings_path)

        assert not is_valid
        assert any("Missing 'permissions' key" in e for e in errors)

    def test_validate_missing_allow_field(self, tmp_path):
        """Test validation fails when allow field is missing."""
        validator = PermissionsValidator()
        settings_path = tmp_path / "settings.json"

        # Write settings without allow field
        settings = {"permissions": {"deny": [], "ask": []}}
        settings_path.write_text(json.dumps(settings))

        is_valid, errors, warnings = validator.validate_file(settings_path)

        assert not is_valid
        assert any("Missing required field: permissions.allow" in e for e in errors)

    def test_validate_missing_deny_field(self, tmp_path):
        """Test validation fails when deny field is missing."""
        validator = PermissionsValidator()
        settings_path = tmp_path / "settings.json"

        # Write settings without deny field
        settings = {"permissions": {"allow": [], "ask": []}}
        settings_path.write_text(json.dumps(settings))

        is_valid, errors, warnings = validator.validate_file(settings_path)

        assert not is_valid
        assert any("Missing required field: permissions.deny" in e for e in errors)

    def test_validate_missing_ask_field(self, tmp_path):
        """Test validation fails when ask field is missing."""
        validator = PermissionsValidator()
        settings_path = tmp_path / "settings.json"

        # Write settings without ask field
        settings = {"permissions": {"allow": [], "deny": []}}
        settings_path.write_text(json.dumps(settings))

        is_valid, errors, warnings = validator.validate_file(settings_path)

        assert not is_valid
        assert any("Missing required field: permissions.ask" in e for e in errors)

    def test_validate_allow_not_list(self, tmp_path):
        """Test validation fails when allow is not a list."""
        validator = PermissionsValidator()
        settings_path = tmp_path / "settings.json"

        # Write settings with allow as string
        settings = {"permissions": {"allow": "not a list", "deny": [], "ask": []}}
        settings_path.write_text(json.dumps(settings))

        is_valid, errors, warnings = validator.validate_file(settings_path)

        assert not is_valid
        assert any("permissions.allow must be a list" in e for e in errors)

    def test_validate_deny_not_list(self, tmp_path):
        """Test validation fails when deny is not a list."""
        validator = PermissionsValidator()
        settings_path = tmp_path / "settings.json"

        # Write settings with deny as dict
        settings = {"permissions": {"allow": [], "deny": {}, "ask": []}}
        settings_path.write_text(json.dumps(settings))

        is_valid, errors, warnings = validator.validate_file(settings_path)

        assert not is_valid
        assert any("permissions.deny must be a list" in e for e in errors)

    def test_validate_ask_not_list(self, tmp_path):
        """Test validation fails when ask is not a list."""
        validator = PermissionsValidator()
        settings_path = tmp_path / "settings.json"

        # Write settings with ask as number
        settings = {"permissions": {"allow": [], "deny": [], "ask": 123}}
        settings_path.write_text(json.dumps(settings))

        is_valid, errors, warnings = validator.validate_file(settings_path)

        assert not is_valid
        assert any("permissions.ask must be a list" in e for e in errors)


@pytest.mark.unit
class TestValidatePatternFormats:
    """Test pattern format validation."""

    def test_validate_correct_format(self, tmp_path):
        """Test validation passes with correct pattern format."""
        validator = PermissionsValidator()
        settings_path = tmp_path / "settings.json"

        settings = {
            "permissions": {
                "allow": ["Bash(git status:*)", "Bash(ls:*)"],
                "deny": ["Bash(rm -rf:*)"],
                "ask": ["Bash(git push:*)"],
            }
        }
        settings_path.write_text(json.dumps(settings))

        is_valid, errors, warnings = validator.validate_file(settings_path)

        assert is_valid
        assert len(errors) == 0
        # Should have no format warnings for correct patterns
        assert not any("invalid format" in w.lower() for w in warnings)

    def test_validate_pattern_not_string(self, tmp_path):
        """Test validation fails when pattern is not a string."""
        validator = PermissionsValidator()
        settings_path = tmp_path / "settings.json"

        settings = {
            "permissions": {
                "allow": [123, "Bash(ls:*)"],  # Number instead of string
                "deny": [],
                "ask": [],
            }
        }
        settings_path.write_text(json.dumps(settings))

        is_valid, errors, warnings = validator.validate_file(settings_path)

        assert not is_valid
        assert any("must be string" in e for e in errors)

    def test_validate_pattern_missing_bash_prefix(self, tmp_path):
        """Test validation warns about pattern missing Bash( prefix."""
        validator = PermissionsValidator()
        settings_path = tmp_path / "settings.json"

        settings = {
            "permissions": {
                "allow": ["git status:*"],  # Missing Bash(
                "deny": [],
                "ask": [],
            }
        }
        settings_path.write_text(json.dumps(settings))

        is_valid, errors, warnings = validator.validate_file(settings_path)

        assert is_valid  # Warning, not error
        assert len(errors) == 0
        assert any("invalid format" in w.lower() for w in warnings)
        assert any("expected format: 'Bash(command:*)'" in w for w in warnings)

    def test_validate_pattern_missing_suffix(self, tmp_path):
        """Test validation warns about pattern missing :*) suffix."""
        validator = PermissionsValidator()
        settings_path = tmp_path / "settings.json"

        settings = {
            "permissions": {
                "allow": ["Bash(git status"],  # Missing :*)
                "deny": [],
                "ask": [],
            }
        }
        settings_path.write_text(json.dumps(settings))

        is_valid, errors, warnings = validator.validate_file(settings_path)

        assert is_valid  # Warning, not error
        assert len(errors) == 0
        assert any("invalid format" in w.lower() for w in warnings)


@pytest.mark.unit
class TestCheckDuplicates:
    """Test duplicate pattern detection."""

    def test_no_duplicates(self, tmp_path):
        """Test validation passes when no duplicates."""
        validator = PermissionsValidator()
        settings_path = tmp_path / "settings.json"

        settings = {
            "permissions": {
                "allow": ["Bash(git status:*)", "Bash(git diff:*)"],
                "deny": ["Bash(rm -rf:*)"],
                "ask": ["Bash(git push:*)"],
            }
        }
        settings_path.write_text(json.dumps(settings))

        is_valid, errors, warnings = validator.validate_file(settings_path)

        assert is_valid
        assert len(errors) == 0
        assert not any("Duplicate" in w for w in warnings)

    def test_duplicate_in_allow_list(self, tmp_path):
        """Test validation warns about duplicates in allow list."""
        validator = PermissionsValidator()
        settings_path = tmp_path / "settings.json"

        settings = {
            "permissions": {
                "allow": [
                    "Bash(git status:*)",
                    "Bash(git diff:*)",
                    "Bash(git status:*)",  # Duplicate
                ],
                "deny": [],
                "ask": [],
            }
        }
        settings_path.write_text(json.dumps(settings))

        is_valid, errors, warnings = validator.validate_file(settings_path)

        assert is_valid  # Warning, not error
        assert len(errors) == 0
        assert any("Duplicate pattern in allow list" in w for w in warnings)
        assert any("git status" in w for w in warnings)

    def test_duplicate_in_deny_list(self, tmp_path):
        """Test validation warns about duplicates in deny list."""
        validator = PermissionsValidator()
        settings_path = tmp_path / "settings.json"

        settings = {
            "permissions": {
                "allow": [],
                "deny": ["Bash(rm -rf:*)", "Bash(rm -rf:*)"],  # Duplicate
                "ask": [],
            }
        }
        settings_path.write_text(json.dumps(settings))

        is_valid, errors, warnings = validator.validate_file(settings_path)

        assert is_valid  # Warning, not error
        assert any("Duplicate pattern in deny list" in w for w in warnings)

    def test_duplicate_in_ask_list(self, tmp_path):
        """Test validation warns about duplicates in ask list."""
        validator = PermissionsValidator()
        settings_path = tmp_path / "settings.json"

        settings = {
            "permissions": {
                "allow": [],
                "deny": [],
                "ask": ["Bash(git push:*)", "Bash(curl:*)", "Bash(git push:*)"],
            }
        }
        settings_path.write_text(json.dumps(settings))

        is_valid, errors, warnings = validator.validate_file(settings_path)

        assert is_valid  # Warning, not error
        assert any("Duplicate pattern in ask list" in w for w in warnings)


@pytest.mark.unit
class TestCheckConflicts:
    """Test conflict detection (same pattern in multiple lists)."""

    def test_no_conflicts(self, tmp_path):
        """Test validation passes when no conflicts."""
        validator = PermissionsValidator()
        settings_path = tmp_path / "settings.json"

        settings = {
            "permissions": {
                "allow": ["Bash(git status:*)"],
                "deny": ["Bash(rm -rf:*)"],
                "ask": ["Bash(git push:*)"],
            }
        }
        settings_path.write_text(json.dumps(settings))

        is_valid, errors, warnings = validator.validate_file(settings_path)

        assert is_valid
        assert len(errors) == 0
        assert not any("Conflict" in e for e in errors)

    def test_conflict_allow_deny(self, tmp_path):
        """Test validation fails when pattern in both allow and deny."""
        validator = PermissionsValidator()
        settings_path = tmp_path / "settings.json"

        settings = {
            "permissions": {
                "allow": ["Bash(git status:*)"],
                "deny": ["Bash(git status:*)"],  # Conflict
                "ask": [],
            }
        }
        settings_path.write_text(json.dumps(settings))

        is_valid, errors, warnings = validator.validate_file(settings_path)

        assert not is_valid
        assert any("Conflict" in e and "allow and deny" in e for e in errors)

    def test_conflict_allow_ask(self, tmp_path):
        """Test validation fails when pattern in both allow and ask."""
        validator = PermissionsValidator()
        settings_path = tmp_path / "settings.json"

        settings = {
            "permissions": {
                "allow": ["Bash(git push:*)"],
                "deny": [],
                "ask": ["Bash(git push:*)"],  # Conflict
            }
        }
        settings_path.write_text(json.dumps(settings))

        is_valid, errors, warnings = validator.validate_file(settings_path)

        assert not is_valid
        assert any("Conflict" in e and "allow and ask" in e for e in errors)

    def test_conflict_deny_ask(self, tmp_path):
        """Test validation fails when pattern in both deny and ask."""
        validator = PermissionsValidator()
        settings_path = tmp_path / "settings.json"

        settings = {
            "permissions": {
                "allow": [],
                "deny": ["Bash(rm -rf:*)"],
                "ask": ["Bash(rm -rf:*)"],  # Conflict
            }
        }
        settings_path.write_text(json.dumps(settings))

        is_valid, errors, warnings = validator.validate_file(settings_path)

        assert not is_valid
        assert any("Conflict" in e and "deny and ask" in e for e in errors)

    def test_multiple_conflicts(self, tmp_path):
        """Test validation reports all conflicts."""
        validator = PermissionsValidator()
        settings_path = tmp_path / "settings.json"

        settings = {
            "permissions": {
                "allow": ["Bash(git status:*)", "Bash(git push:*)"],
                "deny": ["Bash(git status:*)"],  # Conflict with allow
                "ask": ["Bash(git push:*)"],  # Conflict with allow
            }
        }
        settings_path.write_text(json.dumps(settings))

        is_valid, errors, warnings = validator.validate_file(settings_path)

        assert not is_valid
        assert len([e for e in errors if "Conflict" in e]) == 2


@pytest.mark.unit
class TestCheckUnsafePatterns:
    """Test unsafe pattern detection in allow list."""

    def test_no_unsafe_patterns(self, tmp_path):
        """Test validation passes when no unsafe patterns in allow."""
        validator = PermissionsValidator()
        settings_path = tmp_path / "settings.json"

        settings = {
            "permissions": {
                "allow": ["Bash(git status:*)", "Bash(ls:*)", "Bash(pytest:*)"],
                "deny": [],
                "ask": [],
            }
        }
        settings_path.write_text(json.dumps(settings))

        is_valid, errors, warnings = validator.validate_file(settings_path)

        assert is_valid
        assert not any("Unsafe" in w for w in warnings)

    def test_unsafe_rm_in_allow(self, tmp_path):
        """Test validation warns about rm -rf in allow list."""
        validator = PermissionsValidator()
        settings_path = tmp_path / "settings.json"

        settings = {
            "permissions": {
                "allow": ["Bash(rm -rf:*)"],  # Unsafe
                "deny": [],
                "ask": [],
            }
        }
        settings_path.write_text(json.dumps(settings))

        is_valid, errors, warnings = validator.validate_file(settings_path)

        assert is_valid  # Warning, not error
        assert any("Unsafe pattern in allow list" in w for w in warnings)
        assert any("rm -rf" in w for w in warnings)

    def test_unsafe_git_force_in_allow(self, tmp_path):
        """Test validation warns about git push --force in allow list."""
        validator = PermissionsValidator()
        settings_path = tmp_path / "settings.json"

        settings = {
            "permissions": {
                "allow": ["Bash(git push --force:*)"],  # Unsafe
                "deny": [],
                "ask": [],
            }
        }
        settings_path.write_text(json.dumps(settings))

        is_valid, errors, warnings = validator.validate_file(settings_path)

        assert is_valid  # Warning, not error
        assert any("Unsafe pattern in allow list" in w for w in warnings)

    def test_unsafe_sudo_in_allow(self, tmp_path):
        """Test validation warns about sudo in allow list."""
        validator = PermissionsValidator()
        settings_path = tmp_path / "settings.json"

        settings = {
            "permissions": {
                "allow": ["Bash(sudo:*)"],  # Unsafe
                "deny": [],
                "ask": [],
            }
        }
        settings_path.write_text(json.dumps(settings))

        is_valid, errors, warnings = validator.validate_file(settings_path)

        assert is_valid  # Warning, not error
        assert any("Unsafe pattern in allow list" in w for w in warnings)


@pytest.mark.unit
class TestCheckOverlyPermissive:
    """Test overly permissive pattern detection."""

    def test_git_push_should_be_in_ask(self, tmp_path):
        """Test validation warns about git push in allow list."""
        validator = PermissionsValidator()
        settings_path = tmp_path / "settings.json"

        settings = {
            "permissions": {
                "allow": ["Bash(git push:*)"],  # Should be in ask
                "deny": [],
                "ask": [],
            }
        }
        settings_path.write_text(json.dumps(settings))

        is_valid, errors, warnings = validator.validate_file(settings_path)

        assert is_valid  # Warning, not error
        assert any("Overly permissive" in w for w in warnings)
        assert any("git push" in w for w in warnings)

    def test_curl_should_be_in_ask(self, tmp_path):
        """Test validation warns about curl in allow list."""
        validator = PermissionsValidator()
        settings_path = tmp_path / "settings.json"

        settings = {
            "permissions": {
                "allow": ["Bash(curl:*)"],  # Should be in ask
                "deny": [],
                "ask": [],
            }
        }
        settings_path.write_text(json.dumps(settings))

        is_valid, errors, warnings = validator.validate_file(settings_path)

        assert is_valid  # Warning, not error
        assert any("Overly permissive" in w for w in warnings)

    def test_kubectl_should_be_in_ask(self, tmp_path):
        """Test validation warns about kubectl in allow list."""
        validator = PermissionsValidator()
        settings_path = tmp_path / "settings.json"

        settings = {
            "permissions": {
                "allow": ["Bash(kubectl apply:*)"],  # Should be in ask
                "deny": [],
                "ask": [],
            }
        }
        settings_path.write_text(json.dumps(settings))

        is_valid, errors, warnings = validator.validate_file(settings_path)

        assert is_valid  # Warning, not error
        assert any("Overly permissive" in w for w in warnings)


@pytest.mark.unit
class TestGetPermissionCounts:
    """Test permission counting functionality."""

    def test_get_counts_valid_file(self, tmp_path):
        """Test getting permission counts from valid file."""
        validator = PermissionsValidator()
        settings_path = tmp_path / "settings.json"

        settings = {
            "permissions": {
                "allow": ["Bash(git status:*)", "Bash(ls:*)"],
                "deny": ["Bash(rm -rf:*)"],
                "ask": ["Bash(git push:*)", "Bash(curl:*)", "Bash(ssh:*)"],
            }
        }
        settings_path.write_text(json.dumps(settings))

        counts = validator.get_permission_counts(settings_path)

        assert counts["allow"] == 2
        assert counts["deny"] == 1
        assert counts["ask"] == 3

    def test_get_counts_file_not_found(self, tmp_path):
        """Test getting counts from nonexistent file returns zeros."""
        validator = PermissionsValidator()
        settings_path = tmp_path / "nonexistent.json"

        counts = validator.get_permission_counts(settings_path)

        assert counts["allow"] == 0
        assert counts["deny"] == 0
        assert counts["ask"] == 0

    def test_get_counts_invalid_json(self, tmp_path):
        """Test getting counts from invalid JSON returns zeros."""
        validator = PermissionsValidator()
        settings_path = tmp_path / "settings.json"

        settings_path.write_text("{ invalid json")

        counts = validator.get_permission_counts(settings_path)

        assert counts["allow"] == 0
        assert counts["deny"] == 0
        assert counts["ask"] == 0

    def test_get_counts_missing_permissions_key(self, tmp_path):
        """Test getting counts when permissions key missing returns zeros."""
        validator = PermissionsValidator()
        settings_path = tmp_path / "settings.json"

        settings_path.write_text(json.dumps({"other_key": "value"}))

        counts = validator.get_permission_counts(settings_path)

        assert counts["allow"] == 0
        assert counts["deny"] == 0
        assert counts["ask"] == 0

    def test_get_counts_empty_lists(self, tmp_path):
        """Test getting counts with empty lists."""
        validator = PermissionsValidator()
        settings_path = tmp_path / "settings.json"

        settings = {"permissions": {"allow": [], "deny": [], "ask": []}}
        settings_path.write_text(json.dumps(settings))

        counts = validator.get_permission_counts(settings_path)

        assert counts["allow"] == 0
        assert counts["deny"] == 0
        assert counts["ask"] == 0


@pytest.mark.unit
class TestComplexScenarios:
    """Test complex validation scenarios."""

    def test_valid_permissions_file(self, tmp_path):
        """Test validation passes for well-formed permissions file."""
        validator = PermissionsValidator()
        settings_path = tmp_path / "settings.json"

        settings = {
            "permissions": {
                "allow": [
                    "Bash(git status:*)",
                    "Bash(git diff:*)",
                    "Bash(git log:*)",
                    "Bash(ls:*)",
                    "Bash(cat:*)",
                    "Bash(pytest:*)",
                ],
                "deny": [
                    "Bash(rm -rf:*)",
                    "Bash(git push --force:*)",
                    "Bash(git reset --hard:*)",
                ],
                "ask": [
                    "Bash(git push:*)",
                    "Bash(curl:*)",
                    "Bash(ssh:*)",
                    "Bash(sudo:*)",
                ],
            }
        }
        settings_path.write_text(json.dumps(settings))

        is_valid, errors, warnings = validator.validate_file(settings_path)

        assert is_valid
        assert len(errors) == 0
        # May have warnings about unsafe patterns in deny (that's ok)

    def test_multiple_errors_and_warnings(self, tmp_path):
        """Test validation reports multiple errors and warnings."""
        validator = PermissionsValidator()
        settings_path = tmp_path / "settings.json"

        settings = {
            "permissions": {
                "allow": [
                    "Bash(git status:*)",
                    "Bash(git status:*)",  # Duplicate
                    "Bash(git push:*)",  # Overly permissive
                    "Bash(rm -rf:*)",  # Unsafe
                ],
                "deny": ["Bash(git status:*)"],  # Conflict with allow
                "ask": [],
            }
        }
        settings_path.write_text(json.dumps(settings))

        is_valid, errors, warnings = validator.validate_file(settings_path)

        assert not is_valid
        # Should have conflict error
        assert any("Conflict" in e for e in errors)
        # Should have multiple warnings
        assert len(warnings) >= 2
        assert any("Duplicate" in w for w in warnings)
        assert any("Unsafe" in w or "permissive" in w for w in warnings)

    def test_file_with_extra_settings(self, tmp_path):
        """Test validation works with extra settings beyond permissions."""
        validator = PermissionsValidator()
        settings_path = tmp_path / "settings.json"

        settings = {
            "custom_setting": "value",
            "another_config": 123,
            "permissions": {
                "allow": ["Bash(git status:*)"],
                "deny": [],
                "ask": [],
            },
        }
        settings_path.write_text(json.dumps(settings))

        is_valid, errors, warnings = validator.validate_file(settings_path)

        assert is_valid
        assert len(errors) == 0
