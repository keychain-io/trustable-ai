"""
Unit tests for sprint-execution workflow hierarchical state management.

Tests Feature #1118 implementation:
1. Upward state cascading (Task -> Feature -> Epic) in Step A1.5
2. Test report attachment in Step A4.5
3. Feature completion in Step A6

This tests the workflow logic for parent-child work item synchronization.
"""

import pytest
from pathlib import Path
from workflows.registry import WorkflowRegistry
from config.loader import load_config


@pytest.mark.unit
class TestSprintExecutionHierarchicalState:
    """Unit tests for hierarchical state management in sprint-execution workflow."""

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

    # Step A1.5: Upward State Cascading Tests

    def test_step_a15_title_updated(self, workflow_registry):
        """Test that Step A1.5 title reflects upward cascading."""
        rendered = workflow_registry.render_workflow('sprint-execution')

        assert 'Step A1.5: Mark Task In Progress and Cascade to Parent Feature/Epic' in rendered

    def test_step_a15_queries_task_for_parent(self, workflow_registry):
        """Test that Step A1.5 queries Task for parent relations."""
        rendered = workflow_registry.render_workflow('sprint-execution')

        step_a15_section = rendered[
            rendered.find('Step A1.5: Mark Task In Progress'):
            rendered.find('Step A2: Engineer Implementation')
        ]

        # Should query Task for relations
        assert 'adapter.get_work_item(selected_task' in step_a15_section
        assert 'relations' in step_a15_section

    def test_step_a15_extracts_parent_feature_id(self, workflow_registry):
        """Test that Step A1.5 extracts parent Feature ID from relations."""
        rendered = workflow_registry.render_workflow('sprint-execution')

        step_a15_section = rendered[
            rendered.find('Step A1.5: Mark Task In Progress'):
            rendered.find('Step A2: Engineer Implementation')
        ]

        # Should find parent Feature
        assert 'parent_feature_id' in step_a15_section
        assert 'Hierarchy-Reverse' in step_a15_section
        assert "url.split('/')[-1]" in step_a15_section

    def test_step_a15_checks_feature_state(self, workflow_registry):
        """Test that Step A1.5 checks parent Feature state."""
        rendered = workflow_registry.render_workflow('sprint-execution')

        step_a15_section = rendered[
            rendered.find('Step A1.5: Mark Task In Progress'):
            rendered.find('Step A2: Engineer Implementation')
        ]

        # Should check Feature state
        assert 'parent_feature_state' in step_a15_section
        assert "'New'" in step_a15_section
        assert "'To Do'" in step_a15_section

    def test_step_a15_updates_feature_state(self, workflow_registry):
        """Test that Step A1.5 updates parent Feature to In Progress."""
        rendered = workflow_registry.render_workflow('sprint-execution')

        step_a15_section = rendered[
            rendered.find('Step A1.5: Mark Task In Progress'):
            rendered.find('Step A2: Engineer Implementation')
        ]

        # Should update Feature state
        assert "adapter.update_work_item" in step_a15_section
        assert "'System.State': 'In Progress'" in step_a15_section
        assert "parent_feature_id" in step_a15_section

    def test_step_a15_queries_feature_for_epic(self, workflow_registry):
        """Test that Step A1.5 queries parent Feature for parent Epic."""
        rendered = workflow_registry.render_workflow('sprint-execution')

        step_a15_section = rendered[
            rendered.find('Step A1.5: Mark Task In Progress'):
            rendered.find('Step A2: Engineer Implementation')
        ]

        # Should query Feature for Epic
        assert 'parent_feature_relations' in step_a15_section
        assert 'parent_epic_id' in step_a15_section

    def test_step_a15_extracts_parent_epic_id(self, workflow_registry):
        """Test that Step A1.5 extracts parent Epic ID from Feature relations."""
        rendered = workflow_registry.render_workflow('sprint-execution')

        step_a15_section = rendered[
            rendered.find('Step A1.5: Mark Task In Progress'):
            rendered.find('Step A2: Engineer Implementation')
        ]

        # Should extract Epic ID
        assert 'parent_epic_id' in step_a15_section
        assert 'Hierarchy-Reverse' in step_a15_section

    def test_step_a15_checks_epic_state(self, workflow_registry):
        """Test that Step A1.5 checks parent Epic state."""
        rendered = workflow_registry.render_workflow('sprint-execution')

        step_a15_section = rendered[
            rendered.find('Step A1.5: Mark Task In Progress'):
            rendered.find('Step A2: Engineer Implementation')
        ]

        # Should check Epic state
        assert 'parent_epic_state' in step_a15_section
        assert "'New'" in step_a15_section or "'To Do'" in step_a15_section

    def test_step_a15_updates_epic_state(self, workflow_registry):
        """Test that Step A1.5 updates parent Epic to In Progress."""
        rendered = workflow_registry.render_workflow('sprint-execution')

        step_a15_section = rendered[
            rendered.find('Step A1.5: Mark Task In Progress'):
            rendered.find('Step A2: Engineer Implementation')
        ]

        # Should update Epic state
        assert 'parent_epic_id' in step_a15_section
        assert "'System.State': 'In Progress'" in step_a15_section

    def test_step_a15_handles_no_parent_feature(self, workflow_registry):
        """Test that Step A1.5 handles Tasks with no parent Feature."""
        rendered = workflow_registry.render_workflow('sprint-execution')

        step_a15_section = rendered[
            rendered.find('Step A1.5: Mark Task In Progress'):
            rendered.find('Step A2: Engineer Implementation')
        ]

        # Should handle missing parent
        assert 'has no parent Feature' in step_a15_section

    def test_step_a15_handles_no_parent_epic(self, workflow_registry):
        """Test that Step A1.5 handles Features with no parent Epic."""
        rendered = workflow_registry.render_workflow('sprint-execution')

        step_a15_section = rendered[
            rendered.find('Step A1.5: Mark Task In Progress'):
            rendered.find('Step A2: Engineer Implementation')
        ]

        # Should handle missing Epic
        assert 'has no parent Epic' in step_a15_section

    def test_step_a15_error_handling(self, workflow_registry):
        """Test that Step A1.5 handles errors gracefully."""
        rendered = workflow_registry.render_workflow('sprint-execution')

        step_a15_section = rendered[
            rendered.find('Step A1.5: Mark Task In Progress'):
            rendered.find('Step A2: Engineer Implementation')
        ]

        # Should have error handling
        assert 'try:' in step_a15_section
        assert 'except Exception as e:' in step_a15_section
        assert 'Failed to cascade state to parents' in step_a15_section

    def test_step_a15_non_blocking_on_cascade_failure(self, workflow_registry):
        """Test that Step A1.5 continues if cascade fails."""
        rendered = workflow_registry.render_workflow('sprint-execution')

        step_a15_section = rendered[
            rendered.find('Step A1.5: Mark Task In Progress'):
            rendered.find('Step A2: Engineer Implementation')
        ]

        # Should be non-blocking
        assert 'non-blocking' in step_a15_section.lower()

    def test_step_a15_logs_parent_titles(self, workflow_registry):
        """Test that Step A1.5 logs parent Feature and Epic titles."""
        rendered = workflow_registry.render_workflow('sprint-execution')

        step_a15_section = rendered[
            rendered.find('Step A1.5: Mark Task In Progress'):
            rendered.find('Step A2: Engineer Implementation')
        ]

        # Should log titles
        assert 'parent_feature_title' in step_a15_section
        assert 'parent_epic_title' in step_a15_section

    def test_step_a15_logs_state_transitions(self, workflow_registry):
        """Test that Step A1.5 logs successful state transitions."""
        rendered = workflow_registry.render_workflow('sprint-execution')

        step_a15_section = rendered[
            rendered.find('Step A1.5: Mark Task In Progress'):
            rendered.find('Step A2: Engineer Implementation')
        ]

        # Should log updates
        assert 'Updated parent Feature' in step_a15_section
        assert 'Updated parent Epic' in step_a15_section

    def test_step_a15_skips_already_in_progress_feature(self, workflow_registry):
        """Test that Step A1.5 skips Feature already In Progress."""
        rendered = workflow_registry.render_workflow('sprint-execution')

        step_a15_section = rendered[
            rendered.find('Step A1.5: Mark Task In Progress'):
            rendered.find('Step A2: Engineer Implementation')
        ]

        # Should check if already in state
        assert 'already in state' in step_a15_section

    def test_step_a15_skips_already_in_progress_epic(self, workflow_registry):
        """Test that Step A1.5 skips Epic already In Progress."""
        rendered = workflow_registry.render_workflow('sprint-execution')

        step_a15_section = rendered[
            rendered.find('Step A1.5: Mark Task In Progress'):
            rendered.find('Step A2: Engineer Implementation')
        ]

        # Should check Epic state
        assert 'parent_epic_state' in step_a15_section

    # Step A4.5: Test Report Attachment Tests

    def test_step_a45_present(self, workflow_registry):
        """Test that Step A4.5 is present in the workflow."""
        rendered = workflow_registry.render_workflow('sprint-execution')

        assert 'Step A4.5: Generate and Attach Test Report' in rendered

    def test_step_a45_position_after_a4(self, workflow_registry):
        """Test that Step A4.5 appears after Step A4 and before Step A4b."""
        rendered = workflow_registry.render_workflow('sprint-execution')

        step_a4_pos = rendered.find('Step A4: Tester Validation')
        step_a45_pos = rendered.find('Step A4.5: Generate and Attach Test Report')
        step_a4b_pos = rendered.find('Step A4b: Handle Test Failures')

        assert step_a4_pos > 0
        assert step_a45_pos > 0
        assert step_a4b_pos > 0

        # Verify ordering
        assert step_a4_pos < step_a45_pos < step_a4b_pos

    def test_step_a45_critical_comment(self, workflow_registry):
        """Test that Step A4.5 includes CRITICAL comment."""
        rendered = workflow_registry.render_workflow('sprint-execution')

        step_a45_section = rendered[
            rendered.find('Step A4.5: Generate and Attach Test Report'):
            rendered.find('Step A4b: Handle Test Failures')
        ]

        assert 'CRITICAL' in step_a45_section
        assert 'External Source of Truth' in step_a45_section

    def test_step_a45_creates_report_directory(self, workflow_registry):
        """Test that Step A4.5 creates test report directory."""
        rendered = workflow_registry.render_workflow('sprint-execution')

        step_a45_section = rendered[
            rendered.find('Step A4.5: Generate and Attach Test Report'):
            rendered.find('Step A4b: Handle Test Failures')
        ]

        # Should create directory
        assert '.claude/test-reports' in step_a45_section
        assert 'mkdir' in step_a45_section

    def test_step_a45_generates_report_filename(self, workflow_registry):
        """Test that Step A4.5 generates timestamped report filename."""
        rendered = workflow_registry.render_workflow('sprint-execution')

        step_a45_section = rendered[
            rendered.find('Step A4.5: Generate and Attach Test Report'):
            rendered.find('Step A4b: Handle Test Failures')
        ]

        # Should generate filename with task ID and timestamp
        assert 'report_filename' in step_a45_section
        assert 'task_id' in step_a45_section
        assert 'timestamp' in step_a45_section
        assert '-test-report.md' in step_a45_section

    def test_step_a45_includes_validation_results(self, workflow_registry):
        """Test that Step A4.5 includes validation results in report."""
        rendered = workflow_registry.render_workflow('sprint-execution')

        step_a45_section = rendered[
            rendered.find('Step A4.5: Generate and Attach Test Report'):
            rendered.find('Step A4b: Handle Test Failures')
        ]

        # Should extract validation results
        assert 'validation_status' in step_a45_section
        assert 'confidence' in step_a45_section
        assert 'test_results' in step_a45_section
        assert 'unit_tests_pass' in step_a45_section
        assert 'integration_tests_pass' in step_a45_section
        assert 'coverage_percent' in step_a45_section

    def test_step_a45_includes_issues_found(self, workflow_registry):
        """Test that Step A4.5 includes issues found in report."""
        rendered = workflow_registry.render_workflow('sprint-execution')

        step_a45_section = rendered[
            rendered.find('Step A4.5: Generate and Attach Test Report'):
            rendered.find('Step A4b: Handle Test Failures')
        ]

        # Should include issues
        assert 'issues_found' in step_a45_section
        assert 'Issues Found' in step_a45_section

    def test_step_a45_writes_report_file(self, workflow_registry):
        """Test that Step A4.5 writes report file with UTF-8 encoding."""
        rendered = workflow_registry.render_workflow('sprint-execution')

        step_a45_section = rendered[
            rendered.find('Step A4.5: Generate and Attach Test Report'):
            rendered.find('Step A4b: Handle Test Failures')
        ]

        # Should write file
        assert 'with open(report_filepath' in step_a45_section
        assert "encoding='utf-8'" in step_a45_section
        assert 'write(report_content)' in step_a45_section

    def test_step_a45_attaches_to_azure_devops(self, workflow_registry):
        """Test that Step A4.5 attaches report to Azure DevOps work item."""
        rendered = workflow_registry.render_workflow('sprint-execution')

        step_a45_section = rendered[
            rendered.find('Step A4.5: Generate and Attach Test Report'):
            rendered.find('Step A4b: Handle Test Failures')
        ]

        # Should attach file
        assert 'attach_file_to_work_item' in step_a45_section
        assert 'work_item_id=task_id' in step_a45_section
        assert 'file_path=report_filepath' in step_a45_section

    def test_step_a45_verifies_attachment(self, workflow_registry):
        """Test that Step A4.5 verifies attachment exists."""
        rendered = workflow_registry.render_workflow('sprint-execution')

        step_a45_section = rendered[
            rendered.find('Step A4.5: Generate and Attach Test Report'):
            rendered.find('Step A4b: Handle Test Failures')
        ]

        # Should verify attachment
        assert 'verify_attachment_exists' in step_a45_section
        assert 'attachment_exists' in step_a45_section

    def test_step_a45_handles_file_based_adapter(self, workflow_registry):
        """Test that Step A4.5 handles file-based adapter with comments."""
        rendered = workflow_registry.render_workflow('sprint-execution')

        step_a45_section = rendered[
            rendered.find('Step A4.5: Generate and Attach Test Report'):
            rendered.find('Step A4b: Handle Test Failures')
        ]

        # Should add comment for file-based
        assert 'add_comment' in step_a45_section
        assert 'Test Report:' in step_a45_section

    def test_step_a45_error_handling(self, workflow_registry):
        """Test that Step A4.5 handles errors gracefully."""
        rendered = workflow_registry.render_workflow('sprint-execution')

        step_a45_section = rendered[
            rendered.find('Step A4.5: Generate and Attach Test Report'):
            rendered.find('Step A4b: Handle Test Failures')
        ]

        # Should have error handling
        assert 'try:' in step_a45_section
        assert 'except Exception as e:' in step_a45_section

    def test_step_a45_logs_report_generation(self, workflow_registry):
        """Test that Step A4.5 logs report generation."""
        rendered = workflow_registry.render_workflow('sprint-execution')

        step_a45_section = rendered[
            rendered.find('Step A4.5: Generate and Attach Test Report'):
            rendered.find('Step A4b: Handle Test Failures')
        ]

        # Should log generation
        assert 'Generated test report' in step_a45_section
        assert 'Attached test report' in step_a45_section

    def test_step_a45_happens_regardless_of_pass_fail(self, workflow_registry):
        """Test that Step A4.5 happens regardless of test pass/fail."""
        rendered = workflow_registry.render_workflow('sprint-execution')

        step_a45_section = rendered[
            rendered.find('Step A4.5: Generate and Attach Test Report'):
            rendered.find('Step A4b: Handle Test Failures')
        ]

        # Should happen for all test results
        assert 'Regardless of test pass/fail' in step_a45_section or 'if selected_task:' in step_a45_section

    # Step A6: Feature Completion Tests

    def test_step_a6_title_updated(self, workflow_registry):
        """Test that Step A6 title reflects Feature completion."""
        rendered = workflow_registry.render_workflow('sprint-execution')

        assert 'Step A6: Update Work Item Status and Cascade Feature Completion' in rendered

    def test_step_a6_queries_task_for_parent(self, workflow_registry):
        """Test that Step A6 queries Task for parent Feature."""
        rendered = workflow_registry.render_workflow('sprint-execution')

        step_a6_section = rendered[
            rendered.find('Step A6: Update Work Item Status'):
            rendered.find('## PART B: MONITORING CYCLE')
        ]

        # Should query Task for relations
        assert 'adapter.get_work_item(selected_task' in step_a6_section
        assert 'relations' in step_a6_section

    def test_step_a6_extracts_parent_feature_id(self, workflow_registry):
        """Test that Step A6 extracts parent Feature ID."""
        rendered = workflow_registry.render_workflow('sprint-execution')

        step_a6_section = rendered[
            rendered.find('Step A6: Update Work Item Status'):
            rendered.find('## PART B: MONITORING CYCLE')
        ]

        # Should extract Feature ID
        assert 'parent_feature_id' in step_a6_section
        assert 'Hierarchy-Reverse' in step_a6_section

    def test_step_a6_queries_all_child_tasks(self, workflow_registry):
        """Test that Step A6 queries all child Tasks of Feature."""
        rendered = workflow_registry.render_workflow('sprint-execution')

        step_a6_section = rendered[
            rendered.find('Step A6: Update Work Item Status'):
            rendered.find('## PART B: MONITORING CYCLE')
        ]

        # Should query child Tasks
        assert 'child_task_ids' in step_a6_section
        assert 'Hierarchy-Forward' in step_a6_section

    def test_step_a6_checks_all_task_states(self, workflow_registry):
        """Test that Step A6 checks state of all child Tasks."""
        rendered = workflow_registry.render_workflow('sprint-execution')

        step_a6_section = rendered[
            rendered.find('Step A6: Update Work Item Status'):
            rendered.find('## PART B: MONITORING CYCLE')
        ]

        # Should check all states
        assert 'all_tasks_done' in step_a6_section
        assert 'tasks_done_count' in step_a6_section
        assert 'tasks_not_done_count' in step_a6_section

    def test_step_a6_marks_feature_done_when_all_tasks_done(self, workflow_registry):
        """Test that Step A6 marks Feature Done when all Tasks Done."""
        rendered = workflow_registry.render_workflow('sprint-execution')

        step_a6_section = rendered[
            rendered.find('Step A6: Update Work Item Status'):
            rendered.find('## PART B: MONITORING CYCLE')
        ]

        # Should mark Feature Done
        assert 'if all_tasks_done:' in step_a6_section
        assert "'System.State': 'Done'" in step_a6_section

    def test_step_a6_verifies_feature_state_update(self, workflow_registry):
        """Test that Step A6 verifies Feature state was updated."""
        rendered = workflow_registry.render_workflow('sprint-execution')

        step_a6_section = rendered[
            rendered.find('Step A6: Update Work Item Status'):
            rendered.find('## PART B: MONITORING CYCLE')
        ]

        # Should verify update
        assert 'verify_feature' in step_a6_section or 'Verified: Feature' in step_a6_section
        assert 'is Done in Azure DevOps' in step_a6_section

    def test_step_a6_handles_feature_already_done(self, workflow_registry):
        """Test that Step A6 handles Feature already Done."""
        rendered = workflow_registry.render_workflow('sprint-execution')

        step_a6_section = rendered[
            rendered.find('Step A6: Update Work Item Status'):
            rendered.find('## PART B: MONITORING CYCLE')
        ]

        # Should check if already Done
        assert 'already Done' in step_a6_section

    def test_step_a6_handles_tasks_not_all_done(self, workflow_registry):
        """Test that Step A6 handles when not all Tasks are Done."""
        rendered = workflow_registry.render_workflow('sprint-execution')

        step_a6_section = rendered[
            rendered.find('Step A6: Update Work Item Status'):
            rendered.find('## PART B: MONITORING CYCLE')
        ]

        # Should handle incomplete
        assert 'not ready for completion' in step_a6_section
        assert 'Tasks remaining' in step_a6_section

    def test_step_a6_handles_no_parent_feature(self, workflow_registry):
        """Test that Step A6 handles Tasks with no parent Feature."""
        rendered = workflow_registry.render_workflow('sprint-execution')

        step_a6_section = rendered[
            rendered.find('Step A6: Update Work Item Status'):
            rendered.find('## PART B: MONITORING CYCLE')
        ]

        # Should handle missing parent
        assert 'has no parent Feature' in step_a6_section

    def test_step_a6_handles_feature_with_no_children(self, workflow_registry):
        """Test that Step A6 handles Features with no child Tasks."""
        rendered = workflow_registry.render_workflow('sprint-execution')

        step_a6_section = rendered[
            rendered.find('Step A6: Update Work Item Status'):
            rendered.find('## PART B: MONITORING CYCLE')
        ]

        # Should handle no children
        assert 'has no child Tasks' in step_a6_section

    def test_step_a6_error_handling(self, workflow_registry):
        """Test that Step A6 handles errors gracefully."""
        rendered = workflow_registry.render_workflow('sprint-execution')

        step_a6_section = rendered[
            rendered.find('Step A6: Update Work Item Status'):
            rendered.find('## PART B: MONITORING CYCLE')
        ]

        # Should have error handling
        assert 'try:' in step_a6_section
        assert 'except Exception as e:' in step_a6_section
        assert 'Failed to check Feature completion' in step_a6_section

    def test_step_a6_non_blocking_on_feature_check_failure(self, workflow_registry):
        """Test that Step A6 continues if Feature completion check fails."""
        rendered = workflow_registry.render_workflow('sprint-execution')

        step_a6_section = rendered[
            rendered.find('Step A6: Update Work Item Status'):
            rendered.find('## PART B: MONITORING CYCLE')
        ]

        # Should be non-blocking
        assert 'non-blocking' in step_a6_section.lower()

    def test_step_a6_logs_feature_summary(self, workflow_registry):
        """Test that Step A6 logs Feature completion summary."""
        rendered = workflow_registry.render_workflow('sprint-execution')

        step_a6_section = rendered[
            rendered.find('Step A6: Update Work Item Status'):
            rendered.find('## PART B: MONITORING CYCLE')
        ]

        # Should log summary
        assert 'Total Tasks' in step_a6_section
        assert 'Tasks Done' in step_a6_section
        assert 'Tasks Not Done' in step_a6_section

    def test_step_a6_logs_task_details(self, workflow_registry):
        """Test that Step A6 logs details for each child Task."""
        rendered = workflow_registry.render_workflow('sprint-execution')

        step_a6_section = rendered[
            rendered.find('Step A6: Update Work Item Status'):
            rendered.find('## PART B: MONITORING CYCLE')
        ]

        # Should log Task details
        assert 'child_task_state' in step_a6_section
        assert 'child_task_title' in step_a6_section
        assert 'Task #' in step_a6_section
