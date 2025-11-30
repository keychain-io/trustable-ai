"""
Unit tests for Configuration System.

Tests configuration schema validation and loading.
"""
import pytest
from pathlib import Path
import os

from config.schema import (
    ProjectConfig,
    WorkTrackingConfig,
    QualityStandards,
    AgentConfig,
    WorkflowConfig,
    DeploymentConfig,
    FrameworkConfig,
)
from config.loader import ConfigLoader, load_config, create_default_config, save_config
from pydantic import ValidationError


@pytest.mark.unit
class TestProjectConfig:
    """Test ProjectConfig schema."""

    def test_valid_project_config(self):
        """Test creating a valid project configuration."""
        config = ProjectConfig(
            name="Test Project",
            type="web-application",
            tech_stack={"languages": ["Python"]},
        )

        assert config.name == "Test Project"
        assert config.type == "web-application"
        assert config.tech_stack["languages"] == ["Python"]

    def test_project_config_defaults(self):
        """Test project configuration defaults."""
        config = ProjectConfig(
            name="Test",
            type="api",
            tech_stack={"languages": ["Python"]},
        )

        assert config.source_directory == "src"
        assert config.test_directory == "tests"

    def test_invalid_project_type(self):
        """Test that invalid project type raises ValidationError."""
        with pytest.raises(ValidationError):
            ProjectConfig(
                name="Test",
                type="invalid-type",
                tech_stack={"languages": ["Python"]},
            )


@pytest.mark.unit
class TestWorkTrackingConfig:
    """Test WorkTrackingConfig schema."""

    def test_valid_work_tracking_config(self):
        """Test creating a valid work tracking configuration."""
        config = WorkTrackingConfig(
            organization="https://dev.azure.com/test",
            project="Test Project",
        )

        assert config.platform == "file-based"  # default
        assert config.organization == "https://dev.azure.com/test"
        assert config.project == "Test Project"

    def test_work_tracking_defaults(self):
        """Test work tracking configuration defaults."""
        config = WorkTrackingConfig(
            organization="https://dev.azure.com/test",
            project="Test",
        )

        assert config.credentials_source == "cli"
        assert "epic" in config.work_item_types
        assert config.work_item_types["epic"] == "Epic"
        assert config.sprint_naming == "Sprint {number}"

    def test_invalid_platform(self):
        """Test that invalid platform raises ValidationError."""
        with pytest.raises(ValidationError):
            WorkTrackingConfig(
                platform="invalid-platform",
                organization="https://dev.azure.com/test",
                project="Test",
            )

    def test_custom_fields(self):
        """Test custom fields configuration."""
        config = WorkTrackingConfig(
            organization="https://dev.azure.com/test",
            project="Test",
            custom_fields={
                "business_value": "Custom.BusinessValueScore",
                "roi": "Custom.ROI",
            },
        )

        assert config.custom_fields["business_value"] == "Custom.BusinessValueScore"


@pytest.mark.unit
class TestQualityStandards:
    """Test QualityStandards schema."""

    def test_default_quality_standards(self):
        """Test default quality standards."""
        standards = QualityStandards()

        assert standards.test_coverage_min == 80
        assert standards.critical_vulnerabilities_max == 0
        assert standards.code_complexity_max == 10

    def test_custom_quality_standards(self):
        """Test custom quality standards."""
        standards = QualityStandards(
            test_coverage_min=90,
            critical_vulnerabilities_max=0,
            high_vulnerabilities_max=5,
        )

        assert standards.test_coverage_min == 90
        assert standards.high_vulnerabilities_max == 5

    def test_invalid_coverage_range(self):
        """Test that coverage outside 0-100 raises ValidationError."""
        with pytest.raises(ValidationError):
            QualityStandards(test_coverage_min=150)


@pytest.mark.unit
class TestAgentConfig:
    """Test AgentConfig schema."""

    def test_default_agent_config(self):
        """Test default agent configuration."""
        config = AgentConfig()

        assert "architect" in config.models
        assert "engineer" in config.models
        assert len(config.enabled_agents) > 0

    def test_custom_agent_config(self):
        """Test custom agent configuration."""
        config = AgentConfig(
            models={"engineer": "claude-opus-4"},
            enabled_agents=["senior-engineer"],
        )

        assert config.models["engineer"] == "claude-opus-4"
        assert config.enabled_agents == ["senior-engineer"]


@pytest.mark.unit
class TestFrameworkConfig:
    """Test complete FrameworkConfig."""

    def test_complete_config(self, sample_framework_config):
        """Test complete framework configuration."""
        assert isinstance(sample_framework_config, FrameworkConfig)
        assert sample_framework_config.project.name == "Test Project"
        assert sample_framework_config.work_tracking.platform == "azure-devops"

    def test_get_iteration_path(self, sample_framework_config):
        """Test getting iteration path for a sprint."""
        path = sample_framework_config.get_iteration_path("Sprint 10")

        assert "Test Project" in path
        assert "Sprint 10" in path
        assert "\\\\" in path  # Should have escaped backslashes

    def test_get_sprint_name(self, sample_framework_config):
        """Test getting sprint name for a number."""
        name = sample_framework_config.get_sprint_name(10)

        assert name == "Sprint 10"

    def test_get_custom_field(self, sample_framework_config):
        """Test getting custom field mapping."""
        field = sample_framework_config.get_custom_field("business_value")

        assert field == "Custom.BusinessValueScore"

    def test_get_nonexistent_custom_field(self, sample_framework_config):
        """Test getting non-existent custom field returns None."""
        field = sample_framework_config.get_custom_field("nonexistent")

        assert field is None

    def test_is_agent_enabled(self, sample_framework_config):
        """Test checking if agent is enabled."""
        assert sample_framework_config.is_agent_enabled("business-analyst") is True
        assert sample_framework_config.is_agent_enabled("nonexistent") is False

    def test_get_agent_model(self, sample_framework_config):
        """Test getting model for agent type."""
        model = sample_framework_config.get_agent_model("engineer")

        assert "claude" in model.lower()


@pytest.mark.unit
class TestConfigLoader:
    """Test ConfigLoader class."""

    def test_load_from_yaml(self, config_file):
        """Test loading configuration from YAML file."""
        loader = ConfigLoader(config_file)
        config = loader.load()

        assert isinstance(config, FrameworkConfig)
        assert config.project.name == "Test Project"
        assert config.work_tracking.platform == "azure-devops"

    def test_load_nonexistent_file(self, temp_dir):
        """Test loading non-existent file raises FileNotFoundError."""
        loader = ConfigLoader(temp_dir / "nonexistent.yaml")

        with pytest.raises(FileNotFoundError):
            loader.load()

    def test_environment_variable_expansion(self, temp_dir):
        """Test environment variable expansion in configuration."""
        # Set environment variable
        os.environ["TEST_ORG"] = "test-org"

        # Create config with env var
        config_content = """
project:
  name: "Test"
  type: "api"
  tech_stack:
    languages: ["Python"]

work_tracking:
  organization: "https://dev.azure.com/${TEST_ORG}"
  project: "Test"
"""
        config_path = temp_dir / "config.yaml"
        config_path.write_text(config_content)

        loader = ConfigLoader(config_path)
        raw_config = loader.load_raw()

        assert "test-org" in raw_config["work_tracking"]["organization"]

        # Cleanup
        del os.environ["TEST_ORG"]

    def test_environment_variable_with_default(self, temp_dir):
        """Test environment variable with default value."""
        config_content = """
project:
  name: "Test"
  type: "api"
  tech_stack:
    languages: ["Python"]

work_tracking:
  organization: "${NONEXISTENT_VAR:-https://dev.azure.com/default}"
  project: "Test"
"""
        config_path = temp_dir / "config.yaml"
        config_path.write_text(config_content)

        loader = ConfigLoader(config_path)
        raw_config = loader.load_raw()

        assert raw_config["work_tracking"]["organization"] == "https://dev.azure.com/default"

    def test_save_config(self, temp_dir, sample_framework_config):
        """Test saving configuration to YAML file."""
        config_path = temp_dir / "config.yaml"
        loader = ConfigLoader(config_path)

        loader.save(sample_framework_config)

        assert config_path.exists()
        content = config_path.read_text()
        assert "Test Project" in content
        assert "azure-devops" in content


@pytest.mark.unit
class TestConfigurationConvenienceFunctions:
    """Test convenience functions."""

    def test_create_default_config(self):
        """Test creating default configuration."""
        config = create_default_config(
            project_name="Test Project",
            project_type="web-application",
            tech_stack={"languages": ["Python"]},
            organization="https://dev.azure.com/test",
            project="Test",
        )

        assert isinstance(config, FrameworkConfig)
        assert config.project.name == "Test Project"
        assert config.work_tracking.organization == "https://dev.azure.com/test"

    def test_save_and_load_roundtrip(self, temp_dir, sample_framework_config):
        """Test saving and loading configuration roundtrip."""
        config_path = temp_dir / "config.yaml"

        # Save
        save_config(sample_framework_config, config_path)

        # Load
        os.chdir(temp_dir.parent)
        loader = ConfigLoader(config_path)
        loaded_config = loader.load()

        # Compare
        assert loaded_config.project.name == sample_framework_config.project.name
        assert loaded_config.work_tracking.platform == sample_framework_config.work_tracking.platform
