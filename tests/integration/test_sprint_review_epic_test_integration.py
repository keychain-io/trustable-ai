"""
Integration tests for sprint-review workflow EPIC test execution integration.

Tests that EPIC test execution results from Steps 1.5-1.8 are properly integrated
into the sprint closure decision (Step 5) and human approval gate (Step 6).
"""

import pytest
from pathlib import Path
from workflows.registry import WorkflowRegistry


class TestSprintReviewEPICTestIntegration:
    """Integration tests for EPIC test execution integration in sprint-review."""

    @pytest.fixture
    def workflow_registry(self):
        """Create workflow registry for rendering workflows."""
        from config.loader import load_config

        config = load_config('.claude/config.yaml')
        return WorkflowRegistry(config)

    def test_step_5_includes_epic_test_results(self, workflow_registry):
        """Test that Step 5 (Sprint Closure Decision) includes EPIC test results."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # Find Step 5 section
        step_5_start = rendered.find('Step 5: Sprint Closure Decision')
        step_6_start = rendered.find('Step 6: Human Approval Gate')
        step_5_section = rendered[step_5_start:step_6_start]

        # Verify EPIC test results section is present
        assert 'EPIC Acceptance Test Execution Results' in step_5_section
        assert 'Total EPICs Tested:' in step_5_section
        assert 'Successful Executions:' in step_5_section
        assert 'Failed Executions:' in step_5_section

    def test_step_5_epic_results_per_epic_details(self, workflow_registry):
        """Test that Step 5 includes per-EPIC result details."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # Find Step 5 section
        step_5_start = rendered.find('Step 5: Sprint Closure Decision')
        step_6_start = rendered.find('Step 6: Human Approval Gate')
        step_5_section = rendered[step_5_start:step_6_start]

        # Verify per-EPIC details
        assert 'Per-EPIC Results:' in step_5_section
        assert "result['epic_id']" in step_5_section
        assert "result['epic_title']" in step_5_section
        assert "result['overall_status']" in step_5_section
        assert "result['pass_rate']" in step_5_section
        assert "result['deployment_ready']" in step_5_section
        assert "result['report_filepath']" in step_5_section

    def test_step_5_epic_results_execution_failures(self, workflow_registry):
        """Test that Step 5 includes execution failures section."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # Find Step 5 section
        step_5_start = rendered.find('Step 5: Sprint Closure Decision')
        step_6_start = rendered.find('Step 6: Human Approval Gate')
        step_5_section = rendered[step_5_start:step_6_start]

        # Verify execution failures section
        assert 'Execution Failures:' in step_5_section
        assert "test_execution_state['execution_failures']" in step_5_section
        assert "failure['epic_id']" in step_5_section
        assert "failure['epic_title']" in step_5_section
        assert "failure['reason']" in step_5_section

    def test_step_5_epic_results_after_acceptance_tests(self, workflow_registry):
        """Test that EPIC results appear after acceptance test results in Step 5."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # Find Step 5 section first
        step_5_start = rendered.find('Step 5: Sprint Closure Decision')
        step_6_start = rendered.find('Step 6: Human Approval Gate')
        step_5_section = rendered[step_5_start:step_6_start]

        # Find positions within Step 5
        acceptance_pos = step_5_section.find('### Acceptance Test Results')
        epic_results_pos = step_5_section.find('### EPIC Acceptance Test Execution Results')
        security_pos = step_5_section.find('### Security Review')

        # Verify ordering
        assert acceptance_pos > 0
        assert epic_results_pos > 0
        assert security_pos > 0
        assert acceptance_pos < epic_results_pos < security_pos

    def test_step_6_includes_epic_test_summary(self, workflow_registry):
        """Test that Step 6 (Human Approval Gate) includes EPIC test summary."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # Find Step 6 section
        step_6_start = rendered.find('Step 6: Human Approval Gate')
        # Find end of sprint review summary section
        step_6_end = rendered.find('Choose action:', step_6_start) + 500  # Include a bit after
        step_6_section = rendered[step_6_start:step_6_end]

        # Verify EPIC test summary is present
        assert 'EPIC Acceptance Tests:' in step_6_section
        assert 'EPICs Tested:' in step_6_section
        assert 'Execution Failures:' in step_6_section
        assert 'Test Reports Generated:' in step_6_section
        assert 'Reports Attached:' in step_6_section

    def test_step_6_epic_summary_references_state(self, workflow_registry):
        """Test that Step 6 EPIC summary references workflow state variables."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # Find Step 6 section
        step_6_start = rendered.find('Step 6: Human Approval Gate')
        step_6_end = rendered.find('Choose action:', step_6_start) + 500
        step_6_section = rendered[step_6_start:step_6_end]

        # Verify state references
        assert "test_execution_state['successful_executions']" in step_6_section
        assert "test_execution_state['failed_executions']" in step_6_section
        assert "test_execution_state['test_report_files']" in step_6_section
        assert "report_attachment_state['attached_count']" in step_6_section
        assert "len(testable_epics)" in step_6_section

    def test_step_6_epic_summary_after_acceptance_tests(self, workflow_registry):
        """Test that EPIC summary appears after acceptance tests in Step 6."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # Find Step 6 section
        step_6_start = rendered.find('Step 6: Human Approval Gate')
        step_6_section = rendered[step_6_start:step_6_start + 2000]

        # Find positions within Step 6
        acceptance_pos = step_6_section.find('Acceptance Tests:')
        epic_pos = step_6_section.find('EPIC Acceptance Tests:')
        security_pos = step_6_section.find('Security:')

        # Verify ordering
        assert acceptance_pos > 0
        assert epic_pos > 0
        assert security_pos > 0
        assert acceptance_pos < epic_pos < security_pos

    def test_epic_test_results_data_flow(self, workflow_registry):
        """Test that EPIC test data flows from Steps 1.7/1.8 to Steps 5/6."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # Step 1.7 should produce test_execution_state and test_execution_results_all
        step_17_section = rendered[rendered.find('Step 1.7: Execute Tests'):
                                    rendered.find('Step 1.8: Attach Test Reports')]
        assert 'test_execution_state = {' in step_17_section
        assert 'test_execution_results_all' in step_17_section

        # Step 1.8 should produce report_attachment_state
        step_18_section = rendered[rendered.find('Step 1.8: Attach Test Reports'):
                                    rendered.find('Step 2: Run Acceptance Tests')]
        assert 'report_attachment_state = {' in step_18_section
        assert 'attached_count' in step_18_section

        # Step 5 should consume both states
        step_5_section = rendered[rendered.find('Step 5: Sprint Closure Decision'):
                                  rendered.find('Step 6: Human Approval Gate')]
        assert 'test_execution_state' in step_5_section
        assert 'test_execution_results_all' in step_5_section

        # Step 6 should consume both states
        step_6_section = rendered[rendered.find('Step 6: Human Approval Gate'):
                                  rendered.find('Step 6: Human Approval Gate') + 2000]
        assert 'test_execution_state' in step_6_section
        assert 'report_attachment_state' in step_6_section

    def test_epic_test_results_use_jinja_loops(self, workflow_registry):
        """Test that EPIC results use placeholder loops for rendering."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # Step 5 should use placeholder loop syntax for per-EPIC results
        step_5_section = rendered[rendered.find('Step 5: Sprint Closure Decision'):
                                  rendered.find('Step 6: Human Approval Gate')]
        assert '{for result in test_execution_results_all:' in step_5_section
        assert '}' in step_5_section  # Closing brace for loop
        assert 'for failure in test_execution_state' in step_5_section

    def test_epic_test_results_conditional_failures(self, workflow_registry):
        """Test that execution failures use conditional rendering."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # Step 5 should have conditional placeholder syntax for failures
        step_5_section = rendered[rendered.find('Step 5: Sprint Closure Decision'):
                                  rendered.find('Step 6: Human Approval Gate')]
        assert "{if test_execution_state['execution_failures']:" in step_5_section
        assert 'else:' in step_5_section

    def test_epic_test_summary_metrics_present(self, workflow_registry):
        """Test that EPIC test summary includes key metrics."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # Step 6 EPIC summary should have key metrics
        step_6_section = rendered[rendered.find('EPIC Acceptance Tests:'):
                                  rendered.find('EPIC Acceptance Tests:') + 500]

        # Verify metrics are calculated
        assert 'successful_executions' in step_6_section
        assert 'failed_executions' in step_6_section
        assert 'test_report_files' in step_6_section
        assert 'attached_count' in step_6_section

    def test_per_epic_result_formatting(self, workflow_registry):
        """Test that per-EPIC results are formatted correctly."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # Find per-EPIC results section
        step_5_section = rendered[rendered.find('Per-EPIC Results:'):
                                  rendered.find('Execution Failures:')]

        # Verify formatting includes all key fields
        assert "EPIC #" in step_5_section
        assert "Overall Status:" in step_5_section
        assert "Pass Rate:" in step_5_section
        assert "Deployment Ready:" in step_5_section
        assert "Test Report:" in step_5_section

    def test_deployment_ready_emoji_formatting(self, workflow_registry):
        """Test that deployment ready status uses emoji formatting."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # Find per-EPIC results section
        step_5_section = rendered[rendered.find('Per-EPIC Results:'):
                                  rendered.find('Execution Failures:')]

        # Verify emoji formatting
        assert '✅ YES' in step_5_section
        assert '❌ NO' in step_5_section

    def test_epic_results_reference_from_step_17(self, workflow_registry):
        """Test that EPIC results explicitly reference Step 1.7."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # Step 5 should reference Step 1.7
        step_5_section = rendered[rendered.find('EPIC Acceptance Test Execution Results'):
                                  rendered.find('EPIC Acceptance Test Execution Results') + 200]

        assert 'From Step 1.7' in step_5_section or 'Step 1.7' in step_5_section
