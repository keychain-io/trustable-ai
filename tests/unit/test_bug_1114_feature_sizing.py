"""
Unit tests for Bug #1114: Backlog-grooming workflow Feature sizing threshold.

Tests verify that the backlog-grooming workflow template includes guidance for
minimum 50-hour (~10 story point) Feature threshold to prevent over-granular
Feature decomposition.

This validates that:
- Feature extraction guidance specifies minimum 50 hours (~10 story points)
- Bundling logic for remaining functionality < 50 hours
- Verification requirements include Feature size threshold
"""
import pytest
from pathlib import Path
from workflows.registry import WorkflowRegistry
from config.loader import load_config


@pytest.mark.unit
class TestFeatureSizingThreshold:
    """Test suite for Feature sizing threshold guidance."""

    @pytest.fixture
    def config_yaml(self):
        """Sample configuration for testing."""
        return """
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

    def test_feature_extraction_requires_minimum_50_hours(self, tmp_path, config_yaml):
        """Test that Feature extraction guidance specifies minimum 50 hours."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)
        rendered = registry.render_workflow("backlog-grooming")

        # Verify minimum hours specified
        assert "at least 50 estimated hours" in rendered, \
            "Feature extraction should specify minimum 50 estimated hours"

    def test_feature_extraction_specifies_minimum_story_points(self, tmp_path, config_yaml):
        """Test that Feature extraction guidance specifies minimum 10 story points."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)
        rendered = registry.render_workflow("backlog-grooming")

        # Verify minimum story points
        assert "~10 story points" in rendered or "10 story points" in rendered, \
            "Feature extraction should specify ~10 story points minimum"

    def test_feature_extraction_provides_typical_range(self, tmp_path, config_yaml):
        """Test that Feature extraction provides typical story point range."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)
        rendered = registry.render_workflow("backlog-grooming")

        # Verify typical range
        feature_extraction_section = rendered[rendered.find("Feature Extraction"):rendered.find("Task Breakdown")]
        assert "minimum 10 pts" in feature_extraction_section, \
            "Feature extraction should specify minimum 10 pts"
        assert "10-30 pts" in feature_extraction_section or "typically" in feature_extraction_section, \
            "Feature extraction should provide typical story point range"

    def test_feature_extraction_includes_bundling_logic(self, tmp_path, config_yaml):
        """Test that Feature extraction includes bundling logic for remaining functionality."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)
        rendered = registry.render_workflow("backlog-grooming")

        # Verify bundling logic
        assert "remaining uncovered Epic functionality" in rendered or "remaining functionality" in rendered, \
            "Feature extraction should mention remaining functionality"
        assert "less than 50 hours" in rendered, \
            "Bundling logic should reference 50 hour threshold"
        assert "bundle" in rendered.lower(), \
            "Guidance should use 'bundle' terminology for remaining functionality"

    def test_feature_extraction_specifies_one_week_duration(self, tmp_path, config_yaml):
        """Test that Feature extraction specifies ~1 week duration."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)
        rendered = registry.render_workflow("backlog-grooming")

        # Verify 1 week duration
        assert "~1 week" in rendered or "1 week" in rendered, \
            "Feature extraction should specify ~1 week duration"

    def test_feature_extraction_emphasizes_minimum_logically_related_functionality(self, tmp_path, config_yaml):
        """Test that Feature extraction emphasizes minimum logically-related functionality."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)
        rendered = registry.render_workflow("backlog-grooming")

        # Verify minimum logically-related functionality
        feature_extraction_section = rendered[rendered.find("Feature Extraction"):rendered.find("Task Breakdown")]
        assert "minimum logically-related functionality" in feature_extraction_section, \
            "Feature extraction should emphasize minimum logically-related functionality"

    def test_verification_includes_feature_size_threshold(self, tmp_path, config_yaml):
        """Test that Verification section includes Feature size threshold check."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)
        rendered = registry.render_workflow("backlog-grooming")

        # Verify verification includes size threshold
        verification_section = rendered[rendered.find("**Verification**"):rendered.find("### Output Format")]
        assert "at least 10 story points" in verification_section, \
            "Verification should check for at least 10 story points"
        assert "50 hours minimum" in verification_section, \
            "Verification should reference 50 hours minimum"

    def test_verification_warns_against_over_granular_decomposition(self, tmp_path, config_yaml):
        """Test that Verification section warns against over-granular decomposition."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)
        rendered = registry.render_workflow("backlog-grooming")

        # Verify warning against over-granular decomposition
        verification_section = rendered[rendered.find("**Verification**"):rendered.find("### Output Format")]
        assert "over-granular" in verification_section.lower() or "avoid" in verification_section.lower(), \
            "Verification should warn against over-granular decomposition"

    def test_verification_includes_bundling_guidance_for_small_remainder(self, tmp_path, config_yaml):
        """Test that Verification includes guidance for bundling small remainder functionality."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)
        rendered = registry.render_workflow("backlog-grooming")

        # Verify bundling guidance for remainder
        verification_section = rendered[rendered.find("**Verification**"):rendered.find("### Output Format")]
        assert "final remaining Epic functionality < 10 story points" in verification_section or \
               "remaining Epic functionality" in verification_section, \
            "Verification should include guidance for final remaining functionality"
        assert "bundled with an existing Feature" in verification_section or "into one final Feature" in verification_section, \
            "Verification should specify bundling options for small remainder"

    def test_example_feature_meets_minimum_threshold(self, tmp_path, config_yaml):
        """Test that example Feature has at least 10 story points."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)
        rendered = registry.render_workflow("backlog-grooming")

        # Find example Feature story points
        example_feature_start = rendered.find('"title": "Feature 1: User Authentication"')
        assert example_feature_start != -1, "Example Feature not found"

        example_section = rendered[example_feature_start:example_feature_start + 500]

        # Extract story points from example
        # Looking for pattern: "story_points": 13,
        import re
        story_points_match = re.search(r'"story_points":\s*(\d+)', example_section)
        assert story_points_match, "Example Feature should have story_points field"

        story_points = int(story_points_match.group(1))
        assert story_points >= 10, \
            f"Example Feature should have at least 10 story points, found {story_points}"

    def test_template_renders_without_errors_with_new_guidance(self, tmp_path, config_yaml):
        """Test that template renders without errors after adding new Feature sizing guidance."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        # This should not raise any exceptions
        rendered = registry.render_workflow("backlog-grooming")

        # Verify template rendered successfully
        assert len(rendered) > 1000, \
            "Rendered workflow should be substantial (>1000 chars)"
        assert "Backlog Grooming" in rendered, \
            "Rendered workflow should contain workflow title"
        assert "Feature Extraction" in rendered, \
            "Rendered workflow should contain Feature Extraction section"


@pytest.mark.unit
class TestFeatureSizingRationale:
    """Test suite to verify rationale for Feature sizing is documented."""

    @pytest.fixture
    def config_yaml(self):
        """Sample configuration for testing."""
        return """
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

    def test_removed_old_5_20_point_guidance(self, tmp_path, config_yaml):
        """Test that old 5-20 point guidance has been removed."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)
        rendered = registry.render_workflow("backlog-grooming")

        # Verify old guidance removed
        feature_extraction_section = rendered[rendered.find("Feature Extraction"):rendered.find("Task Breakdown")]
        assert "5-20 pts" not in feature_extraction_section, \
            "Old 5-20 point guidance should be removed"
        assert "5-20 story points" not in feature_extraction_section, \
            "Old 5-20 story point guidance should be removed"

    def test_removed_3_7_feature_count_guidance(self, tmp_path, config_yaml):
        """Test that old 3-7 Feature count guidance has been removed."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)
        rendered = registry.render_workflow("backlog-grooming")

        # Verify old feature count guidance removed
        feature_extraction_section = rendered[rendered.find("Feature Extraction"):rendered.find("Task Breakdown")]
        assert "3-7 Features" not in feature_extraction_section, \
            "Old 3-7 Features guidance should be removed (no longer prescriptive about count)"
