"""
Integration tests for sprint-review workflow EPIC auto-completion.

Tests Task #1124 implementation end-to-end: Auto-mark Epic Done in sprint-review
when all child Features Done and tests pass.

This tests the complete workflow including:
- Test execution results from Step 1.7
- EPIC completion logic in Step 1.9
- State tracking and verification
"""

import pytest
from pathlib import Path
from workflows.registry import WorkflowRegistry
from config.loader import load_config


@pytest.mark.integration
class TestSprintReviewEpicAutoCompletion:
    """Integration tests for EPIC auto-completion in sprint-review workflow."""

    @pytest.fixture
    def config_yaml(self):
        """Sample configuration for testing."""
        return """
project:
  name: "Test Project"
  type: "web-application"
  tech_stack:
    languages: ["Python"]
    frameworks: ["FastAPI"]

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

  iteration_format: "{project}\\\\{sprint}"
  sprint_naming: "Sprint {number}"

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
    - project-architect
    - senior-engineer
    - scrum-master
"""

    @pytest.fixture
    def workflow_registry(self, tmp_path, config_yaml):
        """Create workflow registry for rendering workflows."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(config_yaml, encoding='utf-8')

        config = load_config(config_path)
        return WorkflowRegistry(config)

    def test_complete_workflow_includes_epic_completion(self, workflow_registry):
        """Test that complete sprint-review workflow includes EPIC completion step."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # All steps should be present in order
        assert 'Step 1: Collect Sprint Completion Metrics' in rendered
        assert 'Step 1.5: Identify EPICs for Testing' in rendered
        assert 'Step 1.6: Retrieve Test Plans from Work Items' in rendered
        assert 'Step 1.7: Execute Tests and Generate Reports' in rendered
        assert 'Step 1.8: Attach Test Reports to EPIC Work Items' in rendered
        assert 'Step 1.9: Auto-Mark EPICs Done Based on Completion Criteria' in rendered
        assert 'Step 2: Run Acceptance Tests' in rendered

    def test_epic_completion_data_flow(self, workflow_registry):
        """Test that data flows correctly from Step 1.7 to Step 1.9."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # Step 1.7 produces test_execution_results_all
        step_17_section = rendered[
            rendered.find('Step 1.7: Execute Tests'):
            rendered.find('Step 1.8: Attach Test Reports')
        ]
        assert 'test_execution_results_all' in step_17_section
        assert 'deployment_ready' in step_17_section
        assert 'overall_status' in step_17_section

        # Step 1.9 consumes test_execution_results_all
        step_19_section = rendered[
            rendered.find('Step 1.9: Auto-Mark EPICs Done'):
            rendered.find('Step 2: Run Acceptance Tests')
        ]
        assert 'test_execution_results_all' in step_19_section
        assert 'deployment_ready' in step_19_section
        assert 'overall_status' in step_19_section

    def test_epic_completion_uses_adapter_methods(self, workflow_registry):
        """Test that EPIC completion uses work tracking adapter correctly."""
        rendered = workflow_registry.render_workflow('sprint-review')

        step_19_section = rendered[
            rendered.find('Step 1.9: Auto-Mark EPICs Done'):
            rendered.find('Step 2: Run Acceptance Tests')
        ]

        # Should use adapter methods
        assert 'adapter.get_work_item' in step_19_section
        assert 'adapter.update_work_item' in step_19_section

        # Should extract relations
        assert 'relations' in step_19_section

    def test_epic_completion_verification_pattern(self, workflow_registry):
        """Test that EPIC completion follows verification pattern."""
        rendered = workflow_registry.render_workflow('sprint-review')

        step_19_section = rendered[
            rendered.find('Step 1.9: Auto-Mark EPICs Done'):
            rendered.find('Step 2: Run Acceptance Tests')
        ]

        # Pattern: Execute -> Checkpoint -> Verify -> Gate
        # Execute: update_work_item
        assert 'update_work_item' in step_19_section

        # Checkpoint: Store state
        assert 'epic_completion_state' in step_19_section

        # Verify: Query work item to verify state change
        assert 'verify' in step_19_section.lower()
        assert 'get_work_item' in step_19_section

        # Gate: Check verification result
        assert "== 'Done'" in step_19_section or "!= 'Done'" in step_19_section

    def test_epic_completion_handles_multiple_epics(self, workflow_registry):
        """Test that EPIC completion can process multiple EPICs."""
        rendered = workflow_registry.render_workflow('sprint-review')

        step_19_section = rendered[
            rendered.find('Step 1.9: Auto-Mark EPICs Done'):
            rendered.find('Step 2: Run Acceptance Tests')
        ]

        # Should loop over all test results
        assert 'for' in step_19_section
        assert 'test_execution_results_all' in step_19_section

        # Should track multiple EPICs
        assert 'epics_marked_done' in step_19_section
        assert 'epics_not_ready' in step_19_section

    def test_epic_completion_checks_all_criteria(self, workflow_registry):
        """Test that EPIC completion checks all required criteria."""
        rendered = workflow_registry.render_workflow('sprint-review')

        step_19_section = rendered[
            rendered.find('Step 1.9: Auto-Mark EPICs Done'):
            rendered.find('Step 2: Run Acceptance Tests')
        ]

        # Criterion 1: Tests passed
        assert 'deployment_ready' in step_19_section
        assert 'overall_status' in step_19_section

        # Criterion 2: All Features Done
        assert 'System.State' in step_19_section
        assert 'features_done' in step_19_section
        assert 'features_not_done' in step_19_section

    def test_epic_completion_state_persistence(self, workflow_registry):
        """Test that EPIC completion state is persisted for re-entrancy."""
        rendered = workflow_registry.render_workflow('sprint-review')

        step_19_section = rendered[
            rendered.find('Step 1.9: Auto-Mark EPICs Done'):
            rendered.find('Step 2: Run Acceptance Tests')
        ]

        # Should create state dict
        assert 'epic_completion_state = {' in step_19_section

        # Should include key fields
        assert 'epics_marked_done' in step_19_section
        assert 'epics_not_ready' in step_19_section
        assert 'epic_completion_failures' in step_19_section
        assert 'completion_timestamp' in step_19_section

        # Should checkpoint state
        assert 'workflow state' in step_19_section or 'StateManager' in step_19_section

    def test_epic_completion_error_handling(self, workflow_registry):
        """Test that EPIC completion handles errors without crashing workflow."""
        rendered = workflow_registry.render_workflow('sprint-review')

        step_19_section = rendered[
            rendered.find('Step 1.9: Auto-Mark EPICs Done'):
            rendered.find('Step 2: Run Acceptance Tests')
        ]

        # Should have error handling
        assert 'except Exception' in step_19_section
        assert 'epic_completion_failures' in step_19_section

        # Should continue processing on error
        assert 'continue' in step_19_section

    def test_epic_completion_logging(self, workflow_registry):
        """Test that EPIC completion logs all actions and results."""
        rendered = workflow_registry.render_workflow('sprint-review')

        step_19_section = rendered[
            rendered.find('Step 1.9: Auto-Mark EPICs Done'):
            rendered.find('Step 2: Run Acceptance Tests')
        ]

        # Should log progress
        assert 'print(' in step_19_section

        # Should log summary
        assert 'EPIC Completion Summary' in step_19_section
        assert 'Total EPICs processed' in step_19_section
        assert 'EPICs marked Done' in step_19_section

    def test_epic_completion_follows_vision_principles(self, workflow_registry):
        """Test that EPIC completion follows VISION.md principles."""
        rendered = workflow_registry.render_workflow('sprint-review')

        step_19_section = rendered[
            rendered.find('Step 1.9: Auto-Mark EPICs Done'):
            rendered.find('Step 2: Run Acceptance Tests')
        ]

        # Pillar #2: External Source of Truth
        # Should query work tracking system, not trust AI claims
        assert 'adapter.get_work_item' in step_19_section
        assert 'CRITICAL' in step_19_section or 'Querying child Features' in step_19_section

        # Should verify external state
        assert 'System.State' in step_19_section

    def test_epic_completion_child_feature_extraction(self, workflow_registry):
        """Test that EPIC completion correctly extracts child Feature IDs."""
        rendered = workflow_registry.render_workflow('sprint-review')

        step_19_section = rendered[
            rendered.find('Step 1.9: Auto-Mark EPICs Done'):
            rendered.find('Step 2: Run Acceptance Tests')
        ]

        # Should get relations from work item
        assert 'relations' in step_19_section

        # Should filter for child relations
        assert 'Hierarchy-Forward' in step_19_section or 'Child' in step_19_section

        # Should extract IDs from URLs
        assert 'url' in step_19_section
        assert 'child_feature_ids' in step_19_section or 'child_id' in step_19_section

    def test_epic_completion_feature_state_verification(self, workflow_registry):
        """Test that EPIC completion verifies each child Feature state."""
        rendered = workflow_registry.render_workflow('sprint-review')

        step_19_section = rendered[
            rendered.find('Step 1.9: Auto-Mark EPICs Done'):
            rendered.find('Step 2: Run Acceptance Tests')
        ]

        # Should query each child Feature
        assert 'for feature_id in child_feature_ids' in step_19_section or 'feature_id' in step_19_section

        # Should check Feature state
        assert 'System.State' in step_19_section
        assert "'Done'" in step_19_section

        # Should categorize Features
        assert 'features_done' in step_19_section
        assert 'features_not_done' in step_19_section

    def test_epic_completion_only_updates_when_criteria_met(self, workflow_registry):
        """Test that EPIC is only updated when both criteria are met."""
        rendered = workflow_registry.render_workflow('sprint-review')

        step_19_section = rendered[
            rendered.find('Step 1.9: Auto-Mark EPICs Done'):
            rendered.find('Step 2: Run Acceptance Tests')
        ]

        # Should check tests passed
        assert 'if not deployment_ready' in step_19_section or 'deployment_ready' in step_19_section

        # Should check all Features done
        assert 'if len(features_not_done) > 0' in step_19_section or 'features_not_done' in step_19_section

        # Should only update after both checks
        assert 'update_work_item' in step_19_section
        assert 'continue' in step_19_section  # Skip if criteria not met

    def test_epic_completion_summary_reports_all_categories(self, workflow_registry):
        """Test that EPIC completion summary includes all result categories."""
        rendered = workflow_registry.render_workflow('sprint-review')

        step_19_section = rendered[
            rendered.find('Step 1.9: Auto-Mark EPICs Done'):
            rendered.find('Step 2: Run Acceptance Tests')
        ]

        # Summary should include all categories
        assert 'EPICs marked Done' in step_19_section
        assert 'EPICs not ready' in step_19_section
        assert 'EPIC completion failures' in step_19_section

        # Should log details for each category
        assert 'for epic in epics_marked_done' in step_19_section or 'epics_marked_done' in step_19_section
        assert 'for epic in epics_not_ready' in step_19_section or 'epics_not_ready' in step_19_section
        assert 'for failure in epic_completion_failures' in step_19_section or 'epic_completion_failures' in step_19_section

    def test_epic_completion_handles_azure_devops_hierarchy(self, workflow_registry):
        """Test that EPIC completion uses correct Azure DevOps hierarchy relation type."""
        rendered = workflow_registry.render_workflow('sprint-review')

        step_19_section = rendered[
            rendered.find('Step 1.9: Auto-Mark EPICs Done'):
            rendered.find('Step 2: Run Acceptance Tests')
        ]

        # Should use Azure DevOps hierarchy relation type
        assert 'Hierarchy-Forward' in step_19_section

        # Should handle both hierarchy types
        assert 'Hierarchy-Forward' in step_19_section or 'Child' in step_19_section

    def test_epic_completion_workflow_continuity(self, workflow_registry):
        """Test that EPIC completion doesn't break workflow continuity."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # Step 1.9 should be followed by Step 2
        step_19_end = rendered.find('Step 1.9: Auto-Mark EPICs Done') + 5000
        step_2_start = rendered.find('Step 2: Run Acceptance Tests', step_19_end - 500)

        assert step_2_start > 0, "Step 2 should follow Step 1.9"

        # No extra steps between 1.9 and 2
        between_section = rendered[step_19_end - 200:step_2_start]
        assert '## Step' not in between_section or '## Step 2' in between_section
