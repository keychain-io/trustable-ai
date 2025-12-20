"""
Integration tests for Task #1117: Enhanced backlog-grooming task specifications.

Tests verify the backlog-grooming workflow produces Implementation and Testing tasks
with comprehensive specifications when rendered with real configuration.

This complements unit tests by verifying end-to-end behavior.
"""
import pytest
from pathlib import Path
from workflows.registry import WorkflowRegistry
from config.loader import load_config


@pytest.mark.integration
class TestBacklogGroomingEnhancedSpecsIntegration:
    """Integration tests for enhanced task specifications."""

    @pytest.fixture
    def azure_config_yaml(self):
        """Sample configuration with Azure DevOps adapter."""
        return """
project:
  name: "Test Project"
  type: "web-application"
  tech_stack:
    languages: ["Python"]
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
    story: "User Story"
    task: "Task"
    bug: "Bug"

  custom_fields:
    story_points: "Microsoft.VSTS.Scheduling.StoryPoints"
    business_value: "Microsoft.VSTS.Common.BusinessValue"

  iteration_format: "{project}\\\\{sprint}"
  sprint_naming: "Sprint {number}"

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
    def high_coverage_config_yaml(self):
        """Configuration with higher coverage requirement (90%)."""
        return """
project:
  name: "Test Project"
  type: "library"
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

quality_standards:
  test_coverage_min: 90
  critical_vulnerabilities_max: 0

agent_config:
  models:
    senior-engineer: "claude-sonnet-4.5"
  enabled_agents:
    - senior-engineer
"""

    def test_workflow_produces_comprehensive_implementation_spec(self, tmp_path, azure_config_yaml):
        """Test that rendered workflow includes comprehensive Implementation Task specification."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)
        rendered = registry.render_workflow("backlog-grooming")

        # Verify all four test types mentioned in Implementation spec
        spec_section = rendered[rendered.find("Exactly one task should request the complete implementation"):
                                 rendered.find("Exactly one task should request validation")]

        assert "Unit tests" in spec_section, \
            "Implementation spec should mention unit tests"
        assert "Integration tests" in spec_section, \
            "Implementation spec should mention integration tests"
        assert "Edge-case whitebox testing" in spec_section, \
            "Implementation spec should mention edge-case whitebox testing"
        assert "Acceptance tests" in spec_section, \
            "Implementation spec should mention acceptance tests"

    def test_workflow_produces_comprehensive_testing_spec(self, tmp_path, azure_config_yaml):
        """Test that rendered workflow includes comprehensive Testing Task specification."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)
        rendered = registry.render_workflow("backlog-grooming")

        # Verify all three validation types in Testing spec
        spec_section = rendered[rendered.find("Exactly one task should request validation"):
                                 rendered.find("Deployment tasks if Feature requires deployment")]

        assert "Validate presence" in spec_section, \
            "Testing spec should include presence validation"
        assert "Validate completeness" in spec_section, \
            "Testing spec should include completeness validation"
        assert "Validate falsifiability" in spec_section, \
            "Testing spec should include falsifiability validation"

    def test_workflow_references_quality_standards_correctly(self, tmp_path, azure_config_yaml):
        """Test that workflow correctly interpolates quality_standards.test_coverage_min."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)
        rendered = registry.render_workflow("backlog-grooming")

        # Verify 80% coverage from config interpolated
        assert "80% minimum" in rendered, \
            "Workflow should interpolate test_coverage_min as 80%"

    def test_workflow_adapts_to_different_coverage_requirements(self, tmp_path, high_coverage_config_yaml):
        """Test that workflow adapts to different quality standards (90% coverage)."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(high_coverage_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)
        rendered = registry.render_workflow("backlog-grooming")

        # Verify 90% coverage from config interpolated
        assert "90% minimum" in rendered, \
            "Workflow should interpolate test_coverage_min as 90%"

    def test_workflow_example_tasks_demonstrate_enhanced_specs(self, tmp_path, azure_config_yaml):
        """Test that example tasks in workflow demonstrate enhanced specifications."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)
        rendered = registry.render_workflow("backlog-grooming")

        # Find example tasks
        example_start = rendered.find('"features": [')
        example_section = rendered[example_start:example_start + 5000]

        # Verify example Implementation Task demonstrates all test types
        assert '"title": "Implement OAuth2 integration' in example_section, \
            "Example Implementation Task should be present"
        assert "**Unit tests**" in example_section, \
            "Example should demonstrate unit tests"
        assert "**Integration tests**" in example_section, \
            "Example should demonstrate integration tests"
        assert "**Edge-case whitebox testing**" in example_section, \
            "Example should demonstrate edge-case testing"
        assert "**Acceptance tests**" in example_section, \
            "Example should demonstrate acceptance tests"

        # Verify example Testing Task demonstrates all validations
        assert '"title": "Validate authentication test quality' in example_section, \
            "Example Testing Task should be present"
        assert "**Validate presence**" in example_section, \
            "Example should demonstrate presence validation"
        assert "**Validate completeness**" in example_section, \
            "Example should demonstrate completeness validation"
        assert "**Validate falsifiability**" in example_section, \
            "Example should demonstrate falsifiability validation"

    def test_workflow_maintains_backward_compatibility(self, tmp_path, azure_config_yaml):
        """Test that enhanced workflow maintains backward compatibility with existing features."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)
        rendered = registry.render_workflow("backlog-grooming")

        # Verify existing workflow features still present
        assert "Epic Detection and Decomposition" in rendered, \
            "Epic decomposition should still be present"
        assert "Feature Extraction" in rendered, \
            "Feature extraction should still be present"
        assert "Dependency Analysis" in rendered, \
            "Dependency analysis should still be present"
        assert "Verifying Epic Decomposition Hierarchy" in rendered, \
            "Verification gates should still be present"

    def test_workflow_falsifiability_explanation_clear(self, tmp_path, azure_config_yaml):
        """Test that falsifiability validation explanation is clear and actionable."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)
        rendered = registry.render_workflow("backlog-grooming")

        # Find falsifiability section
        falsifiability_pos = rendered.find("Validate falsifiability")
        falsifiability_section = rendered[falsifiability_pos:falsifiability_pos + 500]

        # Verify clear step-by-step explanation
        assert "Introducing intentional bugs" in falsifiability_section or \
               "intentional bugs/failures" in falsifiability_section, \
            "Falsifiability should explain introducing bugs"
        assert "Confirming tests detect" in falsifiability_section or \
               "confirm tests detect" in falsifiability_section, \
            "Falsifiability should explain confirming detection"
        assert "Removing" in falsifiability_section or "remove" in falsifiability_section.lower(), \
            "Falsifiability should explain removing bugs"

    def test_workflow_coverage_targets_consistent(self, tmp_path, azure_config_yaml):
        """Test that coverage targets are consistent throughout workflow."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)
        rendered = registry.render_workflow("backlog-grooming")

        # Count occurrences of coverage target
        coverage_mentions = rendered.count("80% minimum")

        # Should appear multiple times (in spec and examples)
        assert coverage_mentions >= 2, \
            "Coverage target should be mentioned consistently throughout workflow"

    def test_workflow_test_types_labeled_consistently(self, tmp_path, azure_config_yaml):
        """Test that test types use consistent labels throughout workflow."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)
        rendered = registry.render_workflow("backlog-grooming")

        # Verify consistent terminology
        assert "Unit tests" in rendered and "**Unit tests**" in rendered, \
            "Unit tests should be consistently labeled"
        assert "Integration tests" in rendered and "**Integration tests**" in rendered, \
            "Integration tests should be consistently labeled"
        assert "Edge-case whitebox testing" in rendered and "**Edge-case whitebox testing**" in rendered, \
            "Edge-case whitebox testing should be consistently labeled"
        assert "Acceptance tests" in rendered and "**Acceptance tests**" in rendered, \
            "Acceptance tests should be consistently labeled"

    def test_workflow_example_acceptance_criteria_comprehensive(self, tmp_path, azure_config_yaml):
        """Test that example task acceptance criteria are comprehensive."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)
        rendered = registry.render_workflow("backlog-grooming")

        # Find example Implementation Task acceptance criteria
        impl_ac_start = rendered.find('"title": "Implement OAuth2 integration')
        impl_ac_section = rendered[impl_ac_start:impl_ac_start + 2000]

        # Count acceptance criteria for Implementation Task
        # Should have at least 4 (one for each test type minimum)
        ac_count = impl_ac_section.count('"')
        assert ac_count >= 8, \
            "Example Implementation Task should have multiple acceptance criteria"

        # Verify each test type has acceptance criteria
        assert "Unit tests achieve" in impl_ac_section, \
            "Implementation AC should reference unit tests"
        assert "Integration tests verify" in impl_ac_section, \
            "Implementation AC should reference integration tests"
        assert "Edge-case tests" in impl_ac_section, \
            "Implementation AC should reference edge-case tests"
        assert "Acceptance tests verify" in impl_ac_section, \
            "Implementation AC should reference acceptance tests"

    def test_workflow_validation_task_actionable(self, tmp_path, azure_config_yaml):
        """Test that Testing Task specification is actionable with clear steps."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)
        rendered = registry.render_workflow("backlog-grooming")

        # Find Testing Task specification
        testing_spec_start = rendered.find("Exactly one task should request validation")
        testing_spec_section = rendered[testing_spec_start:testing_spec_start + 1500]

        # Verify actionable steps listed
        step_indicators = [
            "Validate presence",
            "Validate completeness",
            "Validate falsifiability",
            "Confirm code coverage",
            "Confirm feature coverage",
            "Run all tests",
            "Report"
        ]

        for step in step_indicators:
            assert step in testing_spec_section, \
                f"Testing Task should include actionable step: {step}"

    def test_workflow_cross_platform_compatibility(self, tmp_path):
        """Test that workflow works with both Azure DevOps and file-based adapters."""
        # Test with file-based config
        filebased_config = """
project:
  name: "Test Project"
  type: "cli-tool"
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

quality_standards:
  test_coverage_min: 85

agent_config:
  models:
    senior-engineer: "claude-sonnet-4.5"
  enabled_agents:
    - senior-engineer
"""

        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(filebased_config, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)
        rendered = registry.render_workflow("backlog-grooming")

        # Verify enhanced specs work with file-based adapter
        assert "Unit tests" in rendered, \
            "Enhanced specs should work with file-based adapter"
        assert "85% minimum" in rendered, \
            "File-based config coverage should interpolate correctly"
