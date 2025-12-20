"""
Unit tests for sprint-review workflow EPIC auto-completion logic.

Tests Task #1124 implementation: Auto-mark Epic Done in sprint-review when all
child Features Done and tests pass.

This tests the Step 1.9 logic that marks EPICs as Done when:
1. All acceptance tests pass (deployment_ready=True, overall_status='pass')
2. All child Features are in "Done" state
"""

import pytest
from pathlib import Path
from workflows.registry import WorkflowRegistry
from config.loader import load_config


@pytest.mark.unit
class TestSprintReviewEpicCompletion:
    """Unit tests for EPIC auto-completion in sprint-review workflow."""

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

    def test_step_19_present_in_workflow(self, workflow_registry):
        """Test that Step 1.9 is present in the rendered workflow."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # Step 1.9 should be present
        assert 'Step 1.9: Auto-Mark EPICs Done Based on Completion Criteria' in rendered

    def test_step_19_position_after_step_18(self, workflow_registry):
        """Test that Step 1.9 appears after Step 1.8 and before Step 2."""
        rendered = workflow_registry.render_workflow('sprint-review')

        step_18_pos = rendered.find('Step 1.8: Attach Test Reports')
        step_19_pos = rendered.find('Step 1.9: Auto-Mark EPICs Done')
        step_2_pos = rendered.find('Step 2: Run Acceptance Tests')

        assert step_18_pos > 0, "Step 1.8 should be present"
        assert step_19_pos > 0, "Step 1.9 should be present"
        assert step_2_pos > 0, "Step 2 should be present"

        # Verify ordering
        assert step_18_pos < step_19_pos < step_2_pos, \
            "Step 1.9 should be between Step 1.8 and Step 2"

    def test_step_19_includes_critical_comment(self, workflow_registry):
        """Test that Step 1.9 includes CRITICAL verification comment."""
        rendered = workflow_registry.render_workflow('sprint-review')

        step_19_section = rendered[
            rendered.find('Step 1.9: Auto-Mark EPICs Done'):
            rendered.find('Step 2: Run Acceptance Tests')
        ]

        # Should have CRITICAL comment about external source of truth
        assert 'CRITICAL' in step_19_section
        assert 'External Source of Truth' in step_19_section or 'Querying child Features' in step_19_section

    def test_step_19_checks_deployment_ready(self, workflow_registry):
        """Test that Step 1.9 checks deployment_ready flag."""
        rendered = workflow_registry.render_workflow('sprint-review')

        step_19_section = rendered[
            rendered.find('Step 1.9: Auto-Mark EPICs Done'):
            rendered.find('Step 2: Run Acceptance Tests')
        ]

        # Should check deployment_ready
        assert 'deployment_ready' in step_19_section
        assert 'if not deployment_ready' in step_19_section or 'deployment_ready=True' in step_19_section

    def test_step_19_checks_overall_status(self, workflow_registry):
        """Test that Step 1.9 checks overall_status equals 'pass'."""
        rendered = workflow_registry.render_workflow('sprint-review')

        step_19_section = rendered[
            rendered.find('Step 1.9: Auto-Mark EPICs Done'):
            rendered.find('Step 2: Run Acceptance Tests')
        ]

        # Should check overall_status
        assert 'overall_status' in step_19_section
        assert "'pass'" in step_19_section or "== 'pass'" in step_19_section

    def test_step_19_queries_child_features(self, workflow_registry):
        """Test that Step 1.9 queries child Features using work tracking adapter."""
        rendered = workflow_registry.render_workflow('sprint-review')

        step_19_section = rendered[
            rendered.find('Step 1.9: Auto-Mark EPICs Done'):
            rendered.find('Step 2: Run Acceptance Tests')
        ]

        # Should query work item for relations
        assert 'get_work_item' in step_19_section
        assert 'relations' in step_19_section

        # Should extract child Features
        assert 'Hierarchy-Forward' in step_19_section or 'Child' in step_19_section

    def test_step_19_verifies_feature_states(self, workflow_registry):
        """Test that Step 1.9 verifies all child Features are Done."""
        rendered = workflow_registry.render_workflow('sprint-review')

        step_19_section = rendered[
            rendered.find('Step 1.9: Auto-Mark EPICs Done'):
            rendered.find('Step 2: Run Acceptance Tests')
        ]

        # Should check Feature state
        assert 'System.State' in step_19_section
        assert "'Done'" in step_19_section

        # Should track Features done vs not done
        assert 'features_done' in step_19_section
        assert 'features_not_done' in step_19_section

    def test_step_19_updates_epic_state(self, workflow_registry):
        """Test that Step 1.9 updates EPIC state to Done."""
        rendered = workflow_registry.render_workflow('sprint-review')

        step_19_section = rendered[
            rendered.find('Step 1.9: Auto-Mark EPICs Done'):
            rendered.find('Step 2: Run Acceptance Tests')
        ]

        # Should update EPIC state
        assert 'update_work_item' in step_19_section
        assert "'System.State': 'Done'" in step_19_section or '"System.State": "Done"' in step_19_section

    def test_step_19_verifies_epic_state_update(self, workflow_registry):
        """Test that Step 1.9 verifies EPIC state was updated successfully."""
        rendered = workflow_registry.render_workflow('sprint-review')

        step_19_section = rendered[
            rendered.find('Step 1.9: Auto-Mark EPICs Done'):
            rendered.find('Step 2: Run Acceptance Tests')
        ]

        # Should verify state change
        assert 'verify' in step_19_section.lower()
        assert 'get_work_item' in step_19_section  # Re-query to verify

    def test_step_19_handles_already_done_epics(self, workflow_registry):
        """Test that Step 1.9 handles EPICs already in Done state."""
        rendered = workflow_registry.render_workflow('sprint-review')

        step_19_section = rendered[
            rendered.find('Step 1.9: Auto-Mark EPICs Done'):
            rendered.find('Step 2: Run Acceptance Tests')
        ]

        # Should check if already Done
        assert "== 'Done'" in step_19_section or "current_epic_state" in step_19_section
        assert 'already' in step_19_section.lower() or 'already_done' in step_19_section

    def test_step_19_tracks_completion_results(self, workflow_registry):
        """Test that Step 1.9 tracks EPICs marked done vs not ready."""
        rendered = workflow_registry.render_workflow('sprint-review')

        step_19_section = rendered[
            rendered.find('Step 1.9: Auto-Mark EPICs Done'):
            rendered.find('Step 2: Run Acceptance Tests')
        ]

        # Should track results
        assert 'epics_marked_done' in step_19_section
        assert 'epics_not_ready' in step_19_section
        assert 'epic_completion_failures' in step_19_section

    def test_step_19_logs_completion_summary(self, workflow_registry):
        """Test that Step 1.9 logs completion summary."""
        rendered = workflow_registry.render_workflow('sprint-review')

        step_19_section = rendered[
            rendered.find('Step 1.9: Auto-Mark EPICs Done'):
            rendered.find('Step 2: Run Acceptance Tests')
        ]

        # Should log summary
        assert 'EPIC Completion Summary' in step_19_section
        assert 'Total EPICs processed' in step_19_section
        assert 'EPICs marked Done' in step_19_section
        assert 'EPICs not ready' in step_19_section

    def test_step_19_handles_errors(self, workflow_registry):
        """Test that Step 1.9 handles errors gracefully."""
        rendered = workflow_registry.render_workflow('sprint-review')

        step_19_section = rendered[
            rendered.find('Step 1.9: Auto-Mark EPICs Done'):
            rendered.find('Step 2: Run Acceptance Tests')
        ]

        # Should have error handling
        assert 'try:' in step_19_section or 'except' in step_19_section
        assert 'Exception' in step_19_section

    def test_step_19_stores_completion_state(self, workflow_registry):
        """Test that Step 1.9 stores completion state for workflow persistence."""
        rendered = workflow_registry.render_workflow('sprint-review')

        step_19_section = rendered[
            rendered.find('Step 1.9: Auto-Mark EPICs Done'):
            rendered.find('Step 2: Run Acceptance Tests')
        ]

        # Should store state
        assert 'epic_completion_state' in step_19_section
        assert 'completion_timestamp' in step_19_section

    def test_step_19_workflow_overview_updated(self, workflow_registry):
        """Test that workflow overview includes Step 1.9."""
        rendered = workflow_registry.render_workflow('sprint-review')

        overview_section = rendered[
            rendered.find('Workflow Overview'):
            rendered.find('Initialize Workflow')
        ]

        # Should list Step 1.9 in overview
        assert 'Step 1.9' in overview_section
        assert 'Auto-mark EPICs Done' in overview_section or 'Features Done' in overview_section

    def test_step_19_uses_test_execution_results(self, workflow_registry):
        """Test that Step 1.9 uses test_execution_results_all from Step 1.7."""
        rendered = workflow_registry.render_workflow('sprint-review')

        step_19_section = rendered[
            rendered.find('Step 1.9: Auto-Mark EPICs Done'):
            rendered.find('Step 2: Run Acceptance Tests')
        ]

        # Should iterate over test execution results
        assert 'test_execution_results_all' in step_19_section
        assert 'for' in step_19_section  # Loop over results

    def test_step_19_extracts_child_ids_from_url(self, workflow_registry):
        """Test that Step 1.9 extracts child work item IDs from relation URLs."""
        rendered = workflow_registry.render_workflow('sprint-review')

        step_19_section = rendered[
            rendered.find('Step 1.9: Auto-Mark EPICs Done'):
            rendered.find('Step 2: Run Acceptance Tests')
        ]

        # Should extract ID from URL
        assert 'url' in step_19_section
        assert 'split' in step_19_section or 'child_id' in step_19_section

    def test_step_19_handles_epics_without_children(self, workflow_registry):
        """Test that Step 1.9 handles EPICs with no child Features."""
        rendered = workflow_registry.render_workflow('sprint-review')

        step_19_section = rendered[
            rendered.find('Step 1.9: Auto-Mark EPICs Done'):
            rendered.find('Step 2: Run Acceptance Tests')
        ]

        # Should handle empty children case
        assert 'len(child_feature_ids)' in step_19_section or 'no child Features' in step_19_section

    def test_step_19_logs_feature_details(self, workflow_registry):
        """Test that Step 1.9 logs details for each child Feature."""
        rendered = workflow_registry.render_workflow('sprint-review')

        step_19_section = rendered[
            rendered.find('Step 1.9: Auto-Mark EPICs Done'):
            rendered.find('Step 2: Run Acceptance Tests')
        ]

        # Should log Feature details
        assert 'feature_state' in step_19_section
        assert 'feature_title' in step_19_section
        assert 'Feature #' in step_19_section

    def test_step_19_continues_on_epic_failure(self, workflow_registry):
        """Test that Step 1.9 continues processing other EPICs if one fails."""
        rendered = workflow_registry.render_workflow('sprint-review')

        step_19_section = rendered[
            rendered.find('Step 1.9: Auto-Mark EPICs Done'):
            rendered.find('Step 2: Run Acceptance Tests')
        ]

        # Should use continue to skip failed EPICs
        assert 'continue' in step_19_section
        assert 'epic_completion_failures' in step_19_section

    def test_step_19_captures_failure_reasons(self, workflow_registry):
        """Test that Step 1.9 captures detailed failure reasons."""
        rendered = workflow_registry.render_workflow('sprint-review')

        step_19_section = rendered[
            rendered.find('Step 1.9: Auto-Mark EPICs Done'):
            rendered.find('Step 2: Run Acceptance Tests')
        ]

        # Should capture reasons
        assert 'reason' in step_19_section
        assert 'Acceptance tests did not pass' in step_19_section or 'not ready' in step_19_section

    def test_step_19_state_includes_timestamps(self, workflow_registry):
        """Test that Step 1.9 includes timestamp in completion state."""
        rendered = workflow_registry.render_workflow('sprint-review')

        step_19_section = rendered[
            rendered.find('Step 1.9: Auto-Mark EPICs Done'):
            rendered.find('Step 2: Run Acceptance Tests')
        ]

        # Should include timestamp
        assert 'datetime.now()' in step_19_section or 'completion_timestamp' in step_19_section
        assert 'isoformat()' in step_19_section
