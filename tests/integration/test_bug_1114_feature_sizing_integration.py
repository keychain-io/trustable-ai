"""
Integration tests for Bug #1114: Feature sizing threshold enforcement.

Tests verify end-to-end behavior of backlog-grooming workflow with new
Feature sizing guidance (minimum 50 hours / 10 story points).

This validates:
- Workflow rendering with Feature sizing guidance
- Cross-platform compatibility (Azure DevOps, file-based)
- Integration with quality standards configuration
"""
import pytest
from pathlib import Path
from workflows.registry import WorkflowRegistry
from config.loader import load_config


@pytest.mark.integration
class TestFeatureSizingIntegration:
    """Integration tests for Feature sizing threshold."""

    @pytest.fixture
    def azure_config_yaml(self):
        """Sample configuration with Azure DevOps adapter."""
        return """
project:
  name: "Test Project"
  type: "web-application"
  tech_stack:
    languages: ["Python", "TypeScript"]
    frameworks: ["FastAPI", "React"]
  source_directory: "src"
  test_directory: "tests"

work_tracking:
  platform: "azure-devops"
  organization: "https://dev.azure.com/testorg"
  project: "TestProject"
  credentials_source: "cli"

  work_item_types:
    epic: "Epic"
    feature: "Feature"
    task: "Task"

  custom_fields:
    story_points: "Microsoft.VSTS.Scheduling.StoryPoints"

quality_standards:
  test_coverage_min: 80
  critical_vulnerabilities_max: 0
  high_vulnerabilities_max: 0
  code_complexity_max: 10

agent_config:
  models:
    senior-engineer: "claude-sonnet-4.5"
  enabled_agents:
    - senior-engineer
"""

    @pytest.fixture
    def filebased_config_yaml(self):
        """Sample configuration with file-based adapter."""
        return """
project:
  name: "Test Project"
  type: "web-application"
  tech_stack:
    languages: ["Python"]
  source_directory: "src"
  test_directory: "tests"

work_tracking:
  platform: "file-based"
  work_items_directory: ".claude/work-items"

  work_item_types:
    epic: "Epic"
    feature: "Feature"
    task: "Task"

  custom_fields:
    story_points: "Microsoft.VSTS.Scheduling.StoryPoints"

quality_standards:
  test_coverage_min: 80
  critical_vulnerabilities_max: 0
  code_complexity_max: 10

agent_config:
  models:
    senior-engineer: "claude-sonnet-4.5"
  enabled_agents:
    - senior-engineer
"""

    def test_workflow_renders_with_feature_sizing_guidance_azure(self, tmp_path, azure_config_yaml):
        """Test that workflow renders correctly with Azure DevOps config."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        # Should render without errors
        rendered = registry.render_workflow("backlog-grooming")

        # Verify key sections present
        assert "at least 50 estimated hours" in rendered, \
            "Feature sizing guidance should be present"
        assert "minimum 10 pts" in rendered, \
            "Minimum story point threshold should be present"
        assert "bundl" in rendered.lower(), \
            "Bundling guidance should be present"

    def test_workflow_renders_with_feature_sizing_guidance_filebased(self, tmp_path, filebased_config_yaml):
        """Test that workflow renders correctly with file-based config."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(filebased_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        # Should render without errors
        rendered = registry.render_workflow("backlog-grooming")

        # Verify key sections present
        assert "at least 50 estimated hours" in rendered, \
            "Feature sizing guidance should be present"
        assert "minimum 10 pts" in rendered, \
            "Minimum story point threshold should be present"

    def test_feature_sizing_integrates_with_verification_section(self, tmp_path, azure_config_yaml):
        """Test that Feature sizing integrates with verification section."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)
        rendered = registry.render_workflow("backlog-grooming")

        # Verify verification section includes Feature size checks
        verification_section = rendered[rendered.find("**Verification**"):rendered.find("### Output Format")]

        assert "at least 10 story points" in verification_section, \
            "Verification should reference 10 story point minimum"
        assert "50 hours minimum" in verification_section, \
            "Verification should reference 50 hours minimum"

    def test_feature_sizing_guidance_complete_workflow(self, tmp_path, azure_config_yaml):
        """Test complete workflow rendering includes all Feature sizing components."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)
        rendered = registry.render_workflow("backlog-grooming")

        # Verify all required components present
        components = [
            "at least 50 estimated hours",  # Feature Extraction guidance
            "~10 story points",  # Story point threshold
            "minimum 10 pts",  # Minimum story points
            "bundle",  # Bundling logic
            "remaining uncovered Epic functionality",  # Bundling condition
            "at least 10 story points",  # Verification threshold
            "over-granular",  # Rationale
        ]

        for component in components:
            assert component in rendered, \
                f"Workflow should contain: {component}"

    def test_feature_sizing_backward_compatible_with_existing_workflows(self, tmp_path, azure_config_yaml):
        """Test that new Feature sizing doesn't break existing workflow structure."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)
        rendered = registry.render_workflow("backlog-grooming")

        # Verify existing workflow sections still present
        existing_sections = [
            "Epic Detection and Decomposition",
            "Feature Extraction",
            "Task Breakdown",
            "Dependency Analysis",
            "Verification",
            "Verifying Epic Decomposition Hierarchy",
            "Epic Decomposition Verification Checklist",
        ]

        for section in existing_sections:
            assert section in rendered, \
                f"Existing workflow section should be preserved: {section}"

    def test_multiple_workflow_renderings_consistent(self, tmp_path, azure_config_yaml):
        """Test that multiple renderings produce consistent Feature sizing guidance."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        # Render multiple times
        rendered1 = registry.render_workflow("backlog-grooming")
        rendered2 = registry.render_workflow("backlog-grooming")

        # Should be identical
        assert rendered1 == rendered2, \
            "Multiple renderings should produce identical output"

        # Both should have Feature sizing guidance
        for rendered in [rendered1, rendered2]:
            assert "at least 50 estimated hours" in rendered
            assert "minimum 10 pts" in rendered


@pytest.mark.integration
class TestFeatureSizingWithDifferentConfigurations:
    """Test Feature sizing with various configuration combinations."""

    def test_feature_sizing_with_custom_story_point_field(self, tmp_path):
        """Test that Feature sizing works with custom story point field names."""
        config_yaml = """
project:
  name: "Test Project"
  type: "web-application"
  tech_stack:
    languages: ["Python"]
  source_directory: "src"
  test_directory: "tests"

work_tracking:
  platform: "azure-devops"
  organization: "https://dev.azure.com/testorg"
  project: "TestProject"
  credentials_source: "cli"

  work_item_types:
    epic: "Epic"
    feature: "Feature"
    task: "Task"

  custom_fields:
    story_points: "Custom.StoryPoints"  # Custom field name

quality_standards:
  test_coverage_min: 80

agent_config:
  models:
    senior-engineer: "claude-sonnet-4.5"
  enabled_agents:
    - senior-engineer
"""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)
        rendered = registry.render_workflow("backlog-grooming")

        # Feature sizing should still be present regardless of custom field name
        assert "at least 50 estimated hours" in rendered
        assert "minimum 10 pts" in rendered

    def test_feature_sizing_with_minimal_config(self, tmp_path):
        """Test that Feature sizing works with minimal configuration."""
        config_yaml = """
project:
  name: "Minimal Project"
  type: "library"
  tech_stack:
    languages: ["Python"]

work_tracking:
  platform: "file-based"
  work_items_directory: ".claude/work-items"

  work_item_types:
    epic: "Epic"
    feature: "Feature"
    task: "Task"

quality_standards:
  test_coverage_min: 80

agent_config:
  enabled_agents:
    - senior-engineer
"""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)
        rendered = registry.render_workflow("backlog-grooming")

        # Feature sizing should be present even with minimal config
        assert "at least 50 estimated hours" in rendered
        assert "minimum 10 pts" in rendered
        assert "bundle" in rendered.lower()

    def test_feature_sizing_documentation_clear_and_actionable(self, tmp_path):
        """Test that Feature sizing guidance is clear and actionable."""
        config_yaml = """
project:
  name: "Test Project"
  type: "web-application"
  tech_stack:
    languages: ["Python"]

work_tracking:
  platform: "azure-devops"
  organization: "https://dev.azure.com/testorg"
  project: "TestProject"

  work_item_types:
    epic: "Epic"
    feature: "Feature"
    task: "Task"

quality_standards:
  test_coverage_min: 80

agent_config:
  enabled_agents:
    - senior-engineer
"""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)
        rendered = registry.render_workflow("backlog-grooming")

        # Verify guidance is actionable (uses imperative language)
        feature_extraction = rendered[rendered.find("Feature Extraction"):rendered.find("Task Breakdown")]

        # Should use clear directive language
        assert "should" in feature_extraction.lower() or "must" in feature_extraction.lower(), \
            "Guidance should use clear directive language"

        # Should specify concrete thresholds
        assert "50" in feature_extraction, "Should specify 50 hours"
        assert "10" in feature_extraction, "Should specify 10 story points"
