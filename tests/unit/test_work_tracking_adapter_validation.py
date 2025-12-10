"""
Unit tests for work tracking adapter platform validation.

Tests Bug #1078 fix - ensures adapter selection strictly enforces
configured platform with no silent fallback to file-based adapter.
"""
import pytest
from pathlib import Path
import yaml
import sys

# Add skills to path for import
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "skills"))

from work_tracking import UnifiedWorkTrackingAdapter, get_adapter


@pytest.mark.unit
class TestAdapterPlatformValidation:
    """Test suite for strict platform validation in adapter initialization."""

    def test_missing_platform_raises_error(self, tmp_path):
        """Test that missing platform configuration raises ValueError."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)

        # Config without work_tracking.platform
        config = {
            "project": {
                "name": "test",
                "type": "web-application"
            },
            "work_tracking": {
                # platform key missing
                "organization": "https://dev.azure.com/test"
            }
        }

        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f)

        # Should raise ValueError, not silently fall back to file-based
        with pytest.raises(ValueError, match="Work tracking platform not configured"):
            UnifiedWorkTrackingAdapter(config_path)

    def test_empty_platform_raises_error(self, tmp_path):
        """Test that empty platform string raises ValueError."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)

        config = {
            "work_tracking": {
                "platform": ""  # Empty string
            }
        }

        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f)

        with pytest.raises(ValueError, match="Work tracking platform not configured"):
            UnifiedWorkTrackingAdapter(config_path)

    def test_none_platform_raises_error(self, tmp_path):
        """Test that null/None platform raises ValueError."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)

        config = {
            "work_tracking": {
                "platform": None  # Explicit null
            }
        }

        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f)

        with pytest.raises(ValueError, match="Work tracking platform not configured"):
            UnifiedWorkTrackingAdapter(config_path)

    def test_invalid_platform_raises_error(self, tmp_path):
        """Test that invalid platform name raises ValueError with clear message."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)

        config = {
            "work_tracking": {
                "platform": "jira"  # Not implemented yet
            }
        }

        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f)

        with pytest.raises(ValueError) as exc_info:
            UnifiedWorkTrackingAdapter(config_path)

        # Error message should mention valid options
        error_msg = str(exc_info.value)
        assert "Invalid work tracking platform: 'jira'" in error_msg
        assert "azure-devops" in error_msg
        assert "file-based" in error_msg

    def test_misspelled_platform_raises_error(self, tmp_path):
        """Test that misspelled platform raises error, not silent fallback."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)

        config = {
            "work_tracking": {
                "platform": "azure-devop"  # Missing 's'
            }
        }

        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f)

        with pytest.raises(ValueError, match="Invalid work tracking platform: 'azure-devop'"):
            UnifiedWorkTrackingAdapter(config_path)

    def test_case_sensitive_platform_validation(self, tmp_path):
        """Test that platform name is case-sensitive."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)

        config = {
            "work_tracking": {
                "platform": "Azure-DevOps"  # Wrong case
            }
        }

        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f)

        with pytest.raises(ValueError, match="Invalid work tracking platform"):
            UnifiedWorkTrackingAdapter(config_path)

    def test_azure_devops_platform_accepted(self, tmp_path):
        """Test that 'azure-devops' platform is accepted."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)

        config = {
            "work_tracking": {
                "platform": "azure-devops",
                "organization": "https://dev.azure.com/test",
                "project": "TestProject",
                "credentials_source": "cli"
            }
        }

        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f)

        # Should not raise ValueError for invalid platform
        # May raise ImportError if Azure CLI not available (that's ok - platform is valid)
        try:
            adapter = UnifiedWorkTrackingAdapter(config_path)
            # If it succeeds, platform is azure-devops
            assert adapter.platform == "azure-devops"
        except ImportError as e:
            # Expected if Azure CLI dependencies not installed
            assert "Azure DevOps adapter requires azure-cli" in str(e)

    def test_file_based_platform_accepted(self, tmp_path):
        """Test that 'file-based' platform is accepted."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)

        config = {
            "work_tracking": {
                "platform": "file-based",
                "work_items_directory": str(tmp_path / "work-items"),
                "project": "TestProject"
            }
        }

        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f)

        # Should successfully create adapter
        adapter = UnifiedWorkTrackingAdapter(config_path)
        assert adapter.platform == "file-based"
        assert adapter.is_file_based is True
        assert adapter.is_azure_devops is False

    def test_get_adapter_factory_respects_validation(self, tmp_path):
        """Test that get_adapter() factory function enforces validation."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)

        config = {
            "work_tracking": {
                "platform": "invalid-platform"
            }
        }

        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f)

        # Factory function should raise same validation error
        with pytest.raises(ValueError, match="Invalid work tracking platform"):
            get_adapter(config_path)

    def test_no_silent_fallback_to_file_based(self, tmp_path):
        """
        Critical test: Verify NO silent fallback to file-based adapter.

        This is the core bug #1078 - when Azure DevOps is configured but
        something is wrong, adapter should FAIL LOUDLY, not silently
        fall back to file-based adapter.
        """
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)

        # Config that looks like Azure DevOps but has typo
        config = {
            "work_tracking": {
                "platform": "azuredevops",  # Missing hyphen
                "organization": "https://dev.azure.com/test",
                "project": "TestProject"
            }
        }

        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f)

        # MUST raise error, not silently use file-based
        with pytest.raises(ValueError) as exc_info:
            adapter = UnifiedWorkTrackingAdapter(config_path)

        # Verify we didn't get file-based adapter
        error_msg = str(exc_info.value)
        assert "azuredevops" in error_msg
        assert "Valid options: 'azure-devops', 'file-based'" in error_msg

    def test_missing_config_file_defaults_to_file_based(self, tmp_path):
        """
        Test that missing config file defaults to file-based.

        This is the ONE exception to strict validation - when config file
        doesn't exist at all (new project), we default to file-based for
        ease of getting started.
        """
        config_path = tmp_path / ".claude" / "config.yaml"
        # Don't create the file - it doesn't exist

        # When config doesn't exist, _load_config returns default with file-based
        adapter = UnifiedWorkTrackingAdapter(config_path)

        # Should default to file-based when config missing
        assert adapter.platform == "file-based"


@pytest.mark.unit
class TestAdapterPlatformProperties:
    """Test platform detection properties."""

    def test_is_azure_devops_property(self, tmp_path):
        """Test is_azure_devops property returns correct value."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)

        config = {
            "work_tracking": {
                "platform": "file-based",
                "work_items_directory": str(tmp_path / "work-items")
            }
        }

        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f)

        adapter = UnifiedWorkTrackingAdapter(config_path)
        assert adapter.is_azure_devops is False
        assert adapter.is_file_based is True

    def test_platform_property_exposes_configured_value(self, tmp_path):
        """Test that platform property exposes the configured platform."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)

        config = {
            "work_tracking": {
                "platform": "file-based"
            }
        }

        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f)

        adapter = UnifiedWorkTrackingAdapter(config_path)
        assert adapter.platform == "file-based"


@pytest.mark.unit
class TestErrorMessages:
    """Test that error messages are helpful and actionable."""

    def test_missing_platform_error_message_helpful(self, tmp_path):
        """Test that missing platform error provides clear guidance."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)

        config = {"work_tracking": {}}  # No platform

        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f)

        with pytest.raises(ValueError) as exc_info:
            UnifiedWorkTrackingAdapter(config_path)

        error_msg = str(exc_info.value)
        # Should tell user what to do
        assert "work_tracking.platform" in error_msg
        assert ".claude/config.yaml" in error_msg
        assert "azure-devops" in error_msg or "file-based" in error_msg

    def test_invalid_platform_error_lists_valid_options(self, tmp_path):
        """Test that invalid platform error lists all valid options."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)

        config = {
            "work_tracking": {
                "platform": "github"  # Not yet supported
            }
        }

        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f)

        with pytest.raises(ValueError) as exc_info:
            UnifiedWorkTrackingAdapter(config_path)

        error_msg = str(exc_info.value)
        # Should list all valid platforms
        assert "azure-devops" in error_msg
        assert "file-based" in error_msg
        assert "github" in error_msg  # Shows what user entered
        assert "Valid options" in error_msg or "Valid" in error_msg
