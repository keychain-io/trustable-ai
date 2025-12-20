"""
Integration tests for sprint-execution workflow hierarchical state management.

Tests Feature #1118 end-to-end integration:
1. Full upward state cascading flow (Task -> Feature -> Epic)
2. Test report generation and attachment
3. Full Feature completion flow

These tests verify the complete workflow with all components integrated.
"""

import pytest
from pathlib import Path
from workflows.registry import WorkflowRegistry
from config.loader import load_config


@pytest.mark.integration
class TestSprintExecutionHierarchicalIntegration:
    """Integration tests for hierarchical state management."""

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

    def test_workflow_renders_without_errors(self, workflow_registry):
        """Test that sprint-execution workflow renders without errors."""
        rendered = workflow_registry.render_workflow('sprint-execution')

        assert rendered
        assert len(rendered) > 1000  # Should be substantial content

    def test_all_three_steps_present(self, workflow_registry):
        """Test that all three modified steps are present."""
        rendered = workflow_registry.render_workflow('sprint-execution')

        # All three steps should be present
        assert 'Step A1.5: Mark Task In Progress and Cascade to Parent Feature/Epic' in rendered
        assert 'Step A4.5: Generate and Attach Test Report' in rendered
        assert 'Step A6: Update Work Item Status and Cascade Feature Completion' in rendered

    def test_steps_in_correct_order(self, workflow_registry):
        """Test that steps appear in correct order."""
        rendered = workflow_registry.render_workflow('sprint-execution')

        # Find positions
        a15_pos = rendered.find('Step A1.5: Mark Task In Progress')
        a2_pos = rendered.find('Step A2: Engineer Implementation')
        a4_pos = rendered.find('Step A4: Tester Validation')
        a45_pos = rendered.find('Step A4.5: Generate and Attach Test Report')
        a4b_pos = rendered.find('Step A4b: Handle Test Failures')
        a5_pos = rendered.find('Step A5: Auto-Commit')
        a6_pos = rendered.find('Step A6: Update Work Item Status')

        # Verify ordering
        assert a15_pos < a2_pos < a4_pos < a45_pos < a4b_pos < a5_pos < a6_pos

    def test_upward_cascading_flow_complete(self, workflow_registry):
        """Test complete upward cascading flow (Task -> Feature -> Epic)."""
        rendered = workflow_registry.render_workflow('sprint-execution')

        # Extract Step A1.5 section
        step_a15_section = rendered[
            rendered.find('Step A1.5: Mark Task In Progress'):
            rendered.find('Step A2: Engineer Implementation')
        ]

        # Verify complete cascade flow
        assert 'adapter.update_work_item' in step_a15_section  # Task update
        assert 'parent_feature_id' in step_a15_section  # Feature lookup
        assert 'parent_epic_id' in step_a15_section  # Epic lookup
        assert step_a15_section.count("'System.State': 'In Progress'") >= 3  # Task, Feature, Epic

    def test_test_report_attachment_flow_complete(self, workflow_registry):
        """Test complete test report attachment flow."""
        rendered = workflow_registry.render_workflow('sprint-execution')

        # Extract Step A4.5 section
        step_a45_section = rendered[
            rendered.find('Step A4.5: Generate and Attach Test Report'):
            rendered.find('Step A4b: Handle Test Failures')
        ]

        # Verify complete attachment flow
        assert 'test_reports_dir' in step_a45_section  # Directory creation
        assert 'report_content' in step_a45_section  # Content generation
        assert 'with open(report_filepath' in step_a45_section  # File write
        assert 'attach_file_to_work_item' in step_a45_section  # Attachment
        assert 'verify_attachment_exists' in step_a45_section  # Verification

    def test_feature_completion_flow_complete(self, workflow_registry):
        """Test complete Feature completion flow."""
        rendered = workflow_registry.render_workflow('sprint-execution')

        # Extract Step A6 section
        step_a6_section = rendered[
            rendered.find('Step A6: Update Work Item Status'):
            rendered.find('## PART B: MONITORING CYCLE')
        ]

        # Verify complete completion flow
        assert 'parent_feature_id' in step_a6_section  # Feature lookup
        assert 'child_task_ids' in step_a6_section  # Child Task query
        assert 'all_tasks_done' in step_a6_section  # State check
        assert 'adapter.update_work_item' in step_a6_section  # Feature update
        assert 'verify_feature' in step_a6_section  # Verification

    def test_error_handling_present_in_all_steps(self, workflow_registry):
        """Test that all steps have error handling."""
        rendered = workflow_registry.render_workflow('sprint-execution')

        # Step A1.5
        step_a15_section = rendered[
            rendered.find('Step A1.5: Mark Task In Progress'):
            rendered.find('Step A2: Engineer Implementation')
        ]
        assert 'except Exception as e:' in step_a15_section

        # Step A4.5
        step_a45_section = rendered[
            rendered.find('Step A4.5: Generate and Attach Test Report'):
            rendered.find('Step A4b: Handle Test Failures')
        ]
        assert 'except Exception as e:' in step_a45_section

        # Step A6
        step_a6_section = rendered[
            rendered.find('Step A6: Update Work Item Status'):
            rendered.find('## PART B: MONITORING CYCLE')
        ]
        assert 'except Exception as e:' in step_a6_section

    def test_verification_gates_present_in_all_steps(self, workflow_registry):
        """Test that verification gates are present."""
        rendered = workflow_registry.render_workflow('sprint-execution')

        # Step A1.5 - verifies parent states before updating
        step_a15_section = rendered[
            rendered.find('Step A1.5: Mark Task In Progress'):
            rendered.find('Step A2: Engineer Implementation')
        ]
        assert 'parent_feature_state' in step_a15_section
        assert 'parent_epic_state' in step_a15_section

        # Step A4.5 - verifies attachment exists
        step_a45_section = rendered[
            rendered.find('Step A4.5: Generate and Attach Test Report'):
            rendered.find('Step A4b: Handle Test Failures')
        ]
        assert 'verify_attachment_exists' in step_a45_section

        # Step A6 - verifies Feature state update
        step_a6_section = rendered[
            rendered.find('Step A6: Update Work Item Status'):
            rendered.find('## PART B: MONITORING CYCLE')
        ]
        assert 'verify_feature' in step_a6_section or 'Verified: Feature' in step_a6_section

    def test_external_source_of_truth_pattern(self, workflow_registry):
        """Test that External Source of Truth pattern is used."""
        rendered = workflow_registry.render_workflow('sprint-execution')

        # All steps should query external system
        assert rendered.count('adapter.get_work_item') >= 6  # Multiple queries
        assert 'External Source of Truth' in rendered  # Documented

    def test_non_blocking_error_handling(self, workflow_registry):
        """Test that errors are non-blocking."""
        rendered = workflow_registry.render_workflow('sprint-execution')

        # All error handlers should be non-blocking
        assert rendered.count('non-blocking') >= 2  # At least in A1.5 and A6

    def test_logging_output_present(self, workflow_registry):
        """Test that logging output is present."""
        rendered = workflow_registry.render_workflow('sprint-execution')

        # Should have comprehensive logging
        assert rendered.count('print(f"✅') >= 10  # Success messages
        assert rendered.count('print(f"⚠️') >= 5  # Warning messages
        assert rendered.count('print(f"ℹ️') >= 3  # Info messages

    def test_state_history_updates(self, workflow_registry):
        """Test that state history is updated with context."""
        rendered = workflow_registry.render_workflow('sprint-execution')

        # All state updates should include history
        assert rendered.count('System.History') >= 5

    def test_claude_code_attribution(self, workflow_registry):
        """Test that Claude Code attribution is included."""
        rendered = workflow_registry.render_workflow('sprint-execution')

        # Should have attribution in multiple places
        assert rendered.count('Generated with [Claude Code]') >= 5
        assert rendered.count('Co-Authored-By: Claude Sonnet 4.5') >= 5

    def test_test_report_includes_all_required_fields(self, workflow_registry):
        """Test that test report includes all required fields."""
        rendered = workflow_registry.render_workflow('sprint-execution')

        step_a45_section = rendered[
            rendered.find('Step A4.5: Generate and Attach Test Report'):
            rendered.find('Step A4b: Handle Test Failures')
        ]

        # Report should include all fields
        required_fields = [
            'Validation Status',
            'Confidence Level',
            'Recommendation',
            'Unit Tests',
            'Integration Tests',
            'Code Coverage',
            'Issues Found',
            'Test Validation Details'
        ]

        for field in required_fields:
            assert field in step_a45_section, f"Test report missing field: {field}"

    def test_workflow_preserves_existing_functionality(self, workflow_registry):
        """Test that existing workflow steps are preserved."""
        rendered = workflow_registry.render_workflow('sprint-execution')

        # All original steps should still be present
        original_steps = [
            'Step A1: Select Task to Implement',
            'Step A2: Engineer Implementation',
            'Step A3: Run Unit Tests',
            'Step A4: Tester Validation',
            'Step A4b: Handle Test Failures',
            'Step A5: Auto-Commit',
            'Step B1: Collect Sprint Status Data',
            'Step B2: Generate Daily Standup Report'
        ]

        for step in original_steps:
            assert step in rendered, f"Original step missing: {step}"

    def test_workflow_overview_updated(self, workflow_registry):
        """Test that workflow overview reflects new steps."""
        rendered = workflow_registry.render_workflow('sprint-execution')

        # Workflow overview should mention hierarchical state management
        overview_section = rendered[
            rendered.find('Workflow Overview'):
            rendered.find('Initialize Workflow')
        ]

        # Should reference the new functionality
        assert 'In Progress' in overview_section or 'Done' in overview_section
