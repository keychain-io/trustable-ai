"""
Integration tests for Permissions Template Generator.

Tests end-to-end permission generation with actual PlatformDetector integration,
file writing, and JSON validation.
"""

import pytest
import json
from pathlib import Path

from cli.permissions_generator import PermissionsTemplateGenerator
from cli.platform_detector import PlatformDetector


@pytest.mark.integration
class TestPermissionsGeneratorIntegration:
    """Integration tests for permissions generation with actual platform detection."""

    def test_end_to_end_permissions_generation_current_platform(self):
        """Test complete flow from platform detection to permissions generation."""
        # Detect current platform
        detector = PlatformDetector()
        platform_info = detector.detect_platform()

        # Generate permissions
        generator = PermissionsTemplateGenerator()
        permissions = generator.generate_permissions(
            platform_info, mode="development"
        )

        # Validate structure
        assert "permissions" in permissions
        assert "allow" in permissions["permissions"]
        assert "deny" in permissions["permissions"]
        assert "ask" in permissions["permissions"]

        # Validate all are lists
        assert isinstance(permissions["permissions"]["allow"], list)
        assert isinstance(permissions["permissions"]["deny"], list)
        assert isinstance(permissions["permissions"]["ask"], list)

        # Validate all patterns are properly formatted
        for key in ["allow", "deny", "ask"]:
            for pattern in permissions["permissions"][key]:
                assert isinstance(pattern, str)
                assert pattern.startswith("Bash(")
                assert pattern.endswith(":*)")

        # Validate we have some patterns
        assert len(permissions["permissions"]["allow"]) > 0

    def test_file_writing_creates_valid_json(self, tmp_path):
        """Test that writing permissions creates valid, readable JSON file."""
        detector = PlatformDetector()
        platform_info = detector.detect_platform()

        generator = PermissionsTemplateGenerator()
        permissions = generator.generate_permissions(
            platform_info, mode="development"
        )

        output_path = tmp_path / ".claude" / "settings.local.json"
        generator.write_to_file(permissions, output_path)

        # File should exist
        assert output_path.exists()

        # Should be valid JSON
        with output_path.open("r") as f:
            loaded = json.load(f)

        # Should match original
        assert loaded == permissions

        # Verify structure
        assert "permissions" in loaded
        assert "allow" in loaded["permissions"]
        assert "deny" in loaded["permissions"]
        assert "ask" in loaded["permissions"]

    def test_production_mode_more_conservative_than_dev(self):
        """Test that production mode generates more conservative permissions."""
        detector = PlatformDetector()
        platform_info = detector.detect_platform()

        generator = PermissionsTemplateGenerator()

        dev_permissions = generator.generate_permissions(
            platform_info, mode="development"
        )
        prod_permissions = generator.generate_permissions(
            platform_info, mode="production"
        )

        # Production should have fewer auto-approved operations
        assert len(prod_permissions["permissions"]["allow"]) < len(
            dev_permissions["permissions"]["allow"]
        )

        # Production should have more operations requiring approval
        assert len(prod_permissions["permissions"]["ask"]) > len(
            dev_permissions["permissions"]["ask"]
        )

    def test_platform_specific_patterns_included(self):
        """Test that platform-specific commands are included appropriately."""
        detector = PlatformDetector()
        platform_info = detector.detect_platform()

        generator = PermissionsTemplateGenerator()
        permissions = generator.generate_permissions(
            platform_info, mode="development"
        )

        all_patterns = (
            permissions["permissions"]["allow"]
            + permissions["permissions"]["deny"]
            + permissions["permissions"]["ask"]
        )

        # All patterns should be in Claude Code format
        for pattern in all_patterns:
            assert pattern.startswith("Bash(")
            assert pattern.endswith(":*)")

        # Should have git patterns
        assert any("git status" in p for p in all_patterns)

        # Should have file patterns
        assert any("ls" in p or "cat" in p for p in all_patterns)

    def test_dangerous_patterns_properly_categorized(self):
        """Test that dangerous patterns are in deny or ask, not allow."""
        detector = PlatformDetector()
        platform_info = detector.detect_platform()

        generator = PermissionsTemplateGenerator()
        permissions = generator.generate_permissions(
            platform_info, mode="development"
        )

        allow_patterns = permissions["permissions"]["allow"]
        deny_patterns = permissions["permissions"]["deny"]
        ask_patterns = permissions["permissions"]["ask"]

        # git push should be in ask (not allow, not deny)
        assert any("git push" in p for p in ask_patterns)
        assert not any("git push" in p for p in allow_patterns)

        # Force operations should be in deny
        destructive_in_deny = any("--force" in p or "--hard" in p for p in deny_patterns)
        assert destructive_in_deny

        # Network operations should be in ask
        assert any("curl" in p or "wget" in p or "ssh" in p for p in ask_patterns)
        assert not any("curl" in p or "wget" in p for p in allow_patterns)

    def test_no_pattern_overlaps_between_categories(self):
        """Test that patterns don't appear in multiple categories."""
        detector = PlatformDetector()
        platform_info = detector.detect_platform()

        generator = PermissionsTemplateGenerator()
        permissions = generator.generate_permissions(
            platform_info, mode="development"
        )

        allow_patterns = set(permissions["permissions"]["allow"])
        deny_patterns = set(permissions["permissions"]["deny"])
        ask_patterns = set(permissions["permissions"]["ask"])

        # No overlaps between categories
        assert len(allow_patterns & deny_patterns) == 0, "Patterns in both allow and deny"
        assert len(allow_patterns & ask_patterns) == 0, "Patterns in both allow and ask"
        assert len(deny_patterns & ask_patterns) == 0, "Patterns in both deny and ask"

    def test_file_writing_preserves_structure(self, tmp_path):
        """Test that writing and reading preserves exact permission structure."""
        detector = PlatformDetector()
        platform_info = detector.detect_platform()

        generator = PermissionsTemplateGenerator()
        original = generator.generate_permissions(platform_info, mode="development")

        output_path = tmp_path / "settings.local.json"
        generator.write_to_file(original, output_path)

        # Read back
        with output_path.open("r") as f:
            loaded = json.load(f)

        # Should be identical
        assert loaded == original

        # Verify lists are in same order
        assert loaded["permissions"]["allow"] == original["permissions"]["allow"]
        assert loaded["permissions"]["deny"] == original["permissions"]["deny"]
        assert loaded["permissions"]["ask"] == original["permissions"]["ask"]

    def test_git_operations_categorized_correctly(self):
        """Test that git operations are properly categorized by safety."""
        detector = PlatformDetector()
        platform_info = detector.detect_platform()

        generator = PermissionsTemplateGenerator()
        dev_permissions = generator.generate_permissions(
            platform_info, mode="development"
        )

        allow = dev_permissions["permissions"]["allow"]
        ask = dev_permissions["permissions"]["ask"]
        deny = dev_permissions["permissions"]["deny"]

        # Read-only git commands should be in allow
        assert any("git status" in p for p in allow)
        assert any("git diff" in p for p in allow)
        assert any("git log" in p for p in allow)

        # Local writes should be in allow in dev mode
        assert any("git add" in p for p in allow)
        assert any("git commit" in p for p in allow)

        # Remote push should be in ask
        assert any("git push" in p for p in ask)

        # Force operations should be in deny
        assert any("--force" in p for p in deny)

    def test_work_tracking_operations_in_dev_mode(self):
        """Test work tracking operations are categorized correctly in dev mode."""
        detector = PlatformDetector()
        platform_info = detector.detect_platform()

        generator = PermissionsTemplateGenerator()
        dev_permissions = generator.generate_permissions(
            platform_info, mode="development"
        )

        allow = dev_permissions["permissions"]["allow"]
        deny = dev_permissions["permissions"]["deny"]

        # CRUD operations should be in allow (dev mode)
        assert any("az boards work-item show" in p for p in allow)
        assert any("az boards work-item create" in p for p in allow)
        assert any("az boards work-item update" in p for p in allow)

        # Delete should be in deny
        assert any("delete" in p for p in deny)

    def test_work_tracking_operations_in_production_mode(self):
        """Test work tracking operations require approval in production mode."""
        detector = PlatformDetector()
        platform_info = detector.detect_platform()

        generator = PermissionsTemplateGenerator()
        prod_permissions = generator.generate_permissions(
            platform_info, mode="production"
        )

        allow = prod_permissions["permissions"]["allow"]
        ask = prod_permissions["permissions"]["ask"]

        # Writes should require approval in production
        assert any("az boards work-item create" in p for p in ask)
        assert any("az boards work-item update" in p for p in ask)

        # Shouldn't be in allow
        assert not any("az boards work-item create" in p for p in allow)
        assert not any("az boards work-item update" in p for p in allow)

    def test_common_safe_operations_always_allowed(self):
        """Test that common safe operations are always in allow."""
        detector = PlatformDetector()
        platform_info = detector.detect_platform()

        generator = PermissionsTemplateGenerator()

        for mode in ["development", "production"]:
            permissions = generator.generate_permissions(platform_info, mode=mode)
            allow = permissions["permissions"]["allow"]

            # Common safe operations should always be allowed
            assert any("pwd" in p for p in allow), f"pwd not in allow for {mode}"
            assert any("echo" in p for p in allow), f"echo not in allow for {mode}"
            assert any("date" in p for p in allow), f"date not in allow for {mode}"
            assert any("whoami" in p for p in allow), f"whoami not in allow for {mode}"

    def test_permissions_json_is_pretty_formatted(self, tmp_path):
        """Test that written JSON is human-readable with proper formatting."""
        detector = PlatformDetector()
        platform_info = detector.detect_platform()

        generator = PermissionsTemplateGenerator()
        permissions = generator.generate_permissions(platform_info, mode="development")

        output_path = tmp_path / "settings.local.json"
        generator.write_to_file(permissions, output_path)

        content = output_path.read_text()

        # Should have indentation (pretty-printed)
        assert "  " in content
        assert "\n" in content

        # Should be valid JSON
        parsed = json.loads(content)
        assert parsed == permissions

    def test_all_patterns_unique_and_sorted(self):
        """Test that all pattern lists are unique and sorted."""
        detector = PlatformDetector()
        platform_info = detector.detect_platform()

        generator = PermissionsTemplateGenerator()
        permissions = generator.generate_permissions(platform_info, mode="development")

        for key in ["allow", "deny", "ask"]:
            patterns = permissions["permissions"][key]

            # No duplicates
            assert len(patterns) == len(set(patterns)), f"Duplicates in {key}"

            # Sorted
            assert patterns == sorted(patterns), f"{key} patterns not sorted"

    def test_invalid_mode_raises_error(self):
        """Test that invalid workflow mode raises ValueError."""
        detector = PlatformDetector()
        platform_info = detector.detect_platform()

        generator = PermissionsTemplateGenerator()

        with pytest.raises(ValueError, match="Invalid mode"):
            generator.generate_permissions(platform_info, mode="invalid")

        with pytest.raises(ValueError, match="Invalid mode"):
            generator.generate_permissions(platform_info, mode="staging")
