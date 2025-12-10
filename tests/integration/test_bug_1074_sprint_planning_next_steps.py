"""
Integration tests for Bug #1074 - sprint-planning workflow recommended next steps.

Tests that sprint-planning workflow references correct, modern sprint lifecycle workflows
in the "Next Steps" section, ensuring users follow the proper sprint execution flow.

Bug #1074: The original next steps were outdated, referencing /feature-implementation
for each feature (inefficient) and missing /sprint-review and /sprint-retrospective.
"""
import pytest
from pathlib import Path
from workflows.registry import WorkflowRegistry
from config.loader import load_config


@pytest.mark.integration
class TestBug1074SprintPlanningNextSteps:
    """Test suite for Bug #1074 - sprint-planning next steps references."""

    @pytest.fixture
    def sample_config_yaml(self):
        """Sample configuration for testing sprint-planning workflow."""
        return """
project:
  name: "Test Project"
  type: "web-application"
  tech_stack:
    languages: ["Python"]
    frameworks: ["FastAPI"]
    platforms: ["Azure"]

work_tracking:
  platform: "azure-devops"
  organization: "https://dev.azure.com/testorg"
  project: "TestProject"
  credentials_source: "cli"

  work_item_types:
    epic: "Epic"
    feature: "Feature"
    task: "Task"
    bug: "Bug"

  custom_fields:
    story_points: "Microsoft.VSTS.Scheduling.StoryPoints"

quality_standards:
  test_coverage_min: 80
  critical_vulnerabilities_max: 0
  high_vulnerabilities_max: 0
  code_complexity_max: 10

agent_config:
  models:
    architect: "claude-opus-4"
    engineer: "claude-sonnet-4.5"
  enabled_agents:
    - business-analyst
    - senior-engineer
    - scrum-master
"""

    def test_sprint_planning_does_not_reference_feature_implementation_for_each_feature(
        self, tmp_path, sample_config_yaml
    ):
        """Test that sprint-planning does NOT recommend running /feature-implementation for each feature."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(sample_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        # Should NOT recommend feature-implementation for each feature
        # This was the old, inefficient approach
        assert "Run /feature-implementation for each Feature" not in rendered, \
            "sprint-planning should not recommend /feature-implementation for each feature (outdated pattern)"
        assert "for each Feature" not in rendered.lower() or "feature-implementation" not in rendered, \
            "sprint-planning should not reference per-feature implementation pattern"

    def test_sprint_planning_references_sprint_execution(
        self, tmp_path, sample_config_yaml
    ):
        """Test that sprint-planning recommends /sprint-execution as next step."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(sample_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        # Should recommend sprint-execution (modern approach)
        assert "/sprint-execution" in rendered, \
            "sprint-planning should recommend /sprint-execution workflow"
        assert "implement tasks and monitor progress" in rendered.lower() or \
               "implement" in rendered.lower() and "monitor" in rendered.lower(), \
            "sprint-planning should describe sprint-execution purpose"

    def test_sprint_planning_references_sprint_review(
        self, tmp_path, sample_config_yaml
    ):
        """Test that sprint-planning recommends /sprint-review workflow."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(sample_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        # Should recommend sprint-review
        assert "/sprint-review" in rendered, \
            "sprint-planning should recommend /sprint-review workflow"
        assert "demo" in rendered.lower() and "stakeholders" in rendered.lower(), \
            "sprint-planning should describe sprint-review as demo to stakeholders"

    def test_sprint_planning_references_sprint_retrospective(
        self, tmp_path, sample_config_yaml
    ):
        """Test that sprint-planning recommends /sprint-retrospective workflow."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(sample_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        # Should recommend sprint-retrospective
        assert "/sprint-retrospective" in rendered, \
            "sprint-planning should recommend /sprint-retrospective workflow"
        assert "analyze" in rendered.lower() and ("went well" in rendered.lower() or "poorly" in rendered.lower()), \
            "sprint-planning should describe sprint-retrospective purpose"

    def test_sprint_planning_references_sprint_completion(
        self, tmp_path, sample_config_yaml
    ):
        """Test that sprint-planning still recommends /sprint-completion workflow."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(sample_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        # Should recommend sprint-completion (kept from original)
        assert "/sprint-completion" in rendered, \
            "sprint-planning should recommend /sprint-completion workflow"
        assert "finalize" in rendered.lower() or "close" in rendered.lower(), \
            "sprint-planning should describe sprint-completion purpose"

    def test_sprint_planning_next_steps_logical_order(
        self, tmp_path, sample_config_yaml
    ):
        """Test that next steps appear in logical sprint lifecycle order."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(sample_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        # Find positions of each workflow reference
        pos_execution = rendered.find("/sprint-execution")
        pos_review = rendered.find("/sprint-review")
        pos_retrospective = rendered.find("/sprint-retrospective")
        pos_completion = rendered.find("/sprint-completion")

        # All should be present
        assert pos_execution > 0, "Missing /sprint-execution"
        assert pos_review > 0, "Missing /sprint-review"
        assert pos_retrospective > 0, "Missing /sprint-retrospective"
        assert pos_completion > 0, "Missing /sprint-completion"

        # Order should be: execution → review → retrospective → completion
        assert pos_execution < pos_review, \
            "sprint-execution should come before sprint-review"
        assert pos_review < pos_retrospective, \
            "sprint-review should come before sprint-retrospective"
        assert pos_retrospective < pos_completion, \
            "sprint-retrospective should come before sprint-completion"

    def test_all_referenced_workflows_exist(
        self, tmp_path, sample_config_yaml
    ):
        """Test that all workflows referenced in next steps actually exist."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(sample_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        # Get sprint-planning rendered output
        rendered = registry.render_workflow("sprint-planning")

        # Extract Next Steps section only
        next_steps_start = rendered.find("➡️ Next Steps:")
        next_steps_end = rendered.find("═" * 10, next_steps_start)
        next_steps_section = rendered[next_steps_start:next_steps_end]

        # Extract workflow references that start with "Run /"
        import re
        next_steps_workflows = re.findall(r'Run /([a-z-]+)', next_steps_section)

        # Expected workflows in next steps
        expected_workflows = [
            "sprint-execution",
            "sprint-review",
            "sprint-retrospective",
            "sprint-completion"
        ]

        # Verify all expected workflows are referenced
        for workflow_name in expected_workflows:
            assert workflow_name in next_steps_workflows, \
                f"Expected workflow /{workflow_name} not found in next steps"

        # Test that each referenced workflow can be rendered (exists)
        for workflow_name in next_steps_workflows:
            try:
                workflow_rendered = registry.render_workflow(workflow_name)
                assert len(workflow_rendered) > 0, f"Workflow {workflow_name} is empty"
            except Exception as e:
                pytest.fail(f"Referenced workflow /{workflow_name} does not exist or cannot be rendered: {e}")

    def test_sprint_planning_does_not_reference_daily_standup_in_next_steps(
        self, tmp_path, sample_config_yaml
    ):
        """Test that sprint-planning does not reference /daily-standup as a next step.

        Daily standup is replaced by sprint-execution's monitoring cycle.
        """
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(sample_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        # Extract Next Steps section
        next_steps_start = rendered.find("➡️ Next Steps:")
        next_steps_end = rendered.find("═" * 10, next_steps_start)  # Next section delimiter
        next_steps_section = rendered[next_steps_start:next_steps_end]

        # Should NOT reference daily-standup in next steps (replaced by sprint-execution)
        assert "/daily-standup" not in next_steps_section, \
            "sprint-planning should not recommend /daily-standup in next steps (replaced by sprint-execution)"

    def test_sprint_planning_next_steps_format_consistency(
        self, tmp_path, sample_config_yaml
    ):
        """Test that next steps section maintains consistent formatting."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(sample_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        # Find Next Steps section
        next_steps_start = rendered.find("➡️ Next Steps:")
        assert next_steps_start > 0, "Next Steps section not found"

        next_steps_section = rendered[next_steps_start:next_steps_start + 500]

        # Should have numbered list format
        assert "1. Run /sprint-execution" in next_steps_section, \
            "Next steps should be numbered list starting with 1"
        assert "2. Run /sprint-review" in next_steps_section, \
            "Next steps should continue numbered list with 2"
        assert "3. Run /sprint-retrospective" in next_steps_section, \
            "Next steps should continue numbered list with 3"
        assert "4. Run /sprint-completion" in next_steps_section, \
            "Next steps should continue numbered list with 4"

    def test_sprint_execution_workflow_matches_description(
        self, tmp_path, sample_config_yaml
    ):
        """Test that sprint-execution workflow actually does what sprint-planning claims.

        Sprint-planning says sprint-execution handles implementation + monitoring.
        Verify this is true.
        """
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(sample_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-execution")

        # Verify sprint-execution has BOTH implementation AND monitoring cycles
        assert "PART A: IMPLEMENTATION CYCLE" in rendered or \
               "Implementation Cycle" in rendered, \
            "sprint-execution should have implementation cycle"
        assert "PART B: MONITORING CYCLE" in rendered or \
               "Monitoring Cycle" in rendered or \
               "MONITORING CYCLE" in rendered, \
            "sprint-execution should have monitoring cycle"

        # Should have task implementation
        assert "/engineer" in rendered or "Implement" in rendered, \
            "sprint-execution should implement tasks"

        # Should have daily monitoring
        assert "/scrum-master" in rendered or "standup" in rendered.lower(), \
            "sprint-execution should include standup/monitoring"


@pytest.mark.integration
class TestSprintLifecycleWorkflowsExist:
    """Test that all workflows in the modern sprint lifecycle exist and are valid."""

    @pytest.fixture
    def sample_config_yaml(self):
        """Minimal config for workflow existence testing."""
        return """
project:
  name: "Test Project"
  type: "web-application"
  tech_stack:
    languages: ["Python"]

work_tracking:
  platform: "file-based"
  work_items_directory: ".claude/work-items"
  work_item_types:
    epic: "Epic"
    feature: "Feature"
    task: "Task"
    bug: "Bug"

quality_standards:
  test_coverage_min: 80
  critical_vulnerabilities_max: 0
  high_vulnerabilities_max: 0
  code_complexity_max: 10

agent_config:
  models:
    architect: "claude-opus-4"
    engineer: "claude-sonnet-4.5"
  enabled_agents:
    - business-analyst
    - senior-engineer
"""

    @pytest.mark.parametrize("workflow_name", [
        "sprint-planning",
        "sprint-execution",
        "sprint-review",
        "sprint-retrospective",
        "sprint-completion"
    ])
    def test_sprint_lifecycle_workflow_exists(
        self, tmp_path, sample_config_yaml, workflow_name
    ):
        """Test that each workflow in the sprint lifecycle exists and can be rendered."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(sample_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        # Should not raise exception
        rendered = registry.render_workflow(workflow_name)

        # Should produce non-empty output
        assert len(rendered) > 100, \
            f"Workflow {workflow_name} should produce substantial output"

        # Should have basic workflow structure
        assert "Workflow" in rendered or "WORKFLOW" in rendered, \
            f"Workflow {workflow_name} should have workflow header"
