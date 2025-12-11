"""
Integration tests for qa-tester agent template rendering with test execution mode.

Tests that the agent template properly renders with test execution mode capabilities,
including input/output structures, guidelines, and examples.
"""

import pytest
from pathlib import Path
from agents.registry import AgentRegistry


class TestQATesterExecutionModeRendering:
    """Integration tests for qa-tester agent execution mode rendering."""

    @pytest.fixture
    def agent_registry(self):
        """Create agent registry for rendering agents."""
        from config.loader import load_config

        config = load_config('.claude/config.yaml')
        return AgentRegistry(config)

    def test_agent_renders_with_execution_mode(self, agent_registry):
        """Test that qa-tester agent renders with execution mode section."""
        # Render qa-tester agent
        rendered = agent_registry.render_agent('qa-tester')

        # Verify execution mode is present
        assert '## Test Execution Mode' in rendered
        assert 'Execute acceptance tests defined in test plans' in rendered

    def test_agent_role_includes_both_modes(self, agent_registry):
        """Test that agent role description includes both plan and execution."""
        rendered = agent_registry.render_agent('qa-tester')

        # Verify role mentions both modes
        assert 'Plan Generation' in rendered
        assert 'Test Execution' in rendered
        assert 'Operates in two modes' in rendered

    def test_operation_modes_section_present(self, agent_registry):
        """Test that Operation Modes section is present."""
        rendered = agent_registry.render_agent('qa-tester')

        # Verify Operation Modes section
        assert '## Operation Modes' in rendered
        assert '### Mode 1: Plan Generation' in rendered
        assert '### Mode 2: Test Execution' in rendered

    def test_responsibilities_split_by_mode(self, agent_registry):
        """Test that responsibilities are split between modes."""
        rendered = agent_registry.render_agent('qa-tester')

        # Verify responsibilities sections
        assert '### Plan Generation Mode' in rendered
        assert '### Test Execution Mode' in rendered
        assert 'Generate blackbox acceptance test plans' in rendered
        assert 'Execute all test cases defined in the test plan' in rendered

    def test_execution_input_structure_documented(self, agent_registry):
        """Test that execution mode input structure is documented."""
        rendered = agent_registry.render_agent('qa-tester')

        # Verify input structure documentation
        assert '### Input: EPIC Test Execution Request' in rendered
        assert '"mode": "execute"' in rendered
        assert '"test_plan_content"' in rendered
        assert '"sprint_context"' in rendered

    def test_execution_output_structure_documented(self, agent_registry):
        """Test that execution mode output structure is documented."""
        rendered = agent_registry.render_agent('qa-tester')

        # Verify output structure documentation
        assert '### Output: JSON with Test Execution Results' in rendered
        assert '"test_execution_results"' in rendered
        assert '"test_case_results"' in rendered
        assert '"quality_gates"' in rendered
        assert '"recommendations"' in rendered

    def test_execution_process_workflow_present(self, agent_registry):
        """Test that execution process workflow is documented."""
        rendered = agent_registry.render_agent('qa-tester')

        # Verify process workflow
        assert '### Process: Execute Tests' in rendered
        assert 'Parse Test Plan' in rendered
        assert 'Verify Preconditions' in rendered
        assert 'Execute Each Test Case' in rendered
        assert 'Determine Overall Status' in rendered

    def test_test_case_result_structure_documented(self, agent_registry):
        """Test that test case result structure is documented."""
        rendered = agent_registry.render_agent('qa-tester')

        # Verify test case result fields
        assert '"test_id"' in rendered
        assert '"status": "pass|fail|blocked|skipped"' in rendered
        assert '"actual_outputs"' in rendered
        assert '"expected_outputs"' in rendered
        assert '"failure_reason"' in rendered
        assert '"evidence"' in rendered

    def test_status_values_documented(self, agent_registry):
        """Test that status values are documented."""
        rendered = agent_registry.render_agent('qa-tester')

        # Verify status documentation
        assert '### Test Execution Status Values' in rendered
        assert '**pass**: Test executed successfully' in rendered
        assert '**fail**: Test executed, one or more pass conditions not met' in rendered
        assert '**blocked**: Test could not execute' in rendered
        assert '**skipped**: Test intentionally not executed' in rendered

    def test_execution_guidelines_present(self, agent_registry):
        """Test that execution guidelines are present."""
        rendered = agent_registry.render_agent('qa-tester')

        # Verify guidelines
        assert '### Test Execution Guidelines' in rendered
        assert '**Blackbox Execution Principles**' in rendered
        assert '**Failure Documentation**' in rendered
        assert '**Pass/Fail Determination**' in rendered

    def test_example_execution_results_present(self, agent_registry):
        """Test that example execution results are present."""
        rendered = agent_registry.render_agent('qa-tester')

        # Verify example
        assert '### Example: Test Execution Results' in rendered
        assert '**Input Test Plan**' in rendered
        assert '**Output Execution Results**' in rendered

    def test_quality_gates_structure_documented(self, agent_registry):
        """Test that quality gates structure is documented."""
        rendered = agent_registry.render_agent('qa-tester')

        # Verify quality gates
        assert '"quality_gates"' in rendered
        assert '"all_high_priority_pass"' in rendered
        assert '"all_medium_priority_pass"' in rendered
        assert '"gates_passed"' in rendered

    def test_defects_structure_documented(self, agent_registry):
        """Test that defects structure is documented."""
        rendered = agent_registry.render_agent('qa-tester')

        # Verify defects structure
        assert '"defects_found"' in rendered
        assert '"severity": "critical|high|medium|low"' in rendered
        assert '"reproduction_steps"' in rendered
        assert '"expected_behavior"' in rendered
        assert '"actual_behavior"' in rendered

    def test_recommendations_structure_documented(self, agent_registry):
        """Test that recommendations structure is documented."""
        rendered = agent_registry.render_agent('qa-tester')

        # Verify recommendations
        assert '"recommendations"' in rendered
        assert '"deployment_ready"' in rendered
        assert '"required_fixes"' in rendered
        assert '"optional_improvements"' in rendered
        assert '"overall_assessment"' in rendered

    def test_feature_results_structure_documented(self, agent_registry):
        """Test that feature-level results structure is documented."""
        rendered = agent_registry.render_agent('qa-tester')

        # Verify feature results
        assert '"feature_results"' in rendered
        assert '"acceptance_criteria_met"' in rendered

    def test_execution_best_practices_present(self, agent_registry):
        """Test that execution best practices are present."""
        rendered = agent_registry.render_agent('qa-tester')

        # Verify best practices
        assert '### Test Execution Best Practices' in rendered
        assert '**Systematic Execution**' in rendered
        assert '**Evidence Collection**' in rendered
        assert '**Failure Analysis**' in rendered
        assert '**Overall Status Determination**' in rendered

    def test_success_criteria_includes_execution_mode(self, agent_registry):
        """Test that success criteria includes execution mode."""
        rendered = agent_registry.render_agent('qa-tester')

        # Verify success criteria sections
        assert '### Plan Generation Mode' in rendered
        assert '### Test Execution Mode' in rendered
        assert 'All test cases from test plan are executed' in rendered
        assert 'Execution results captured for each test case' in rendered

    def test_example_shows_partial_status(self, agent_registry):
        """Test that example shows partial status scenario."""
        rendered = agent_registry.render_agent('qa-tester')

        # Verify example includes realistic partial status
        assert '"overall_status": "partial"' in rendered
        assert '"tests_passed": 4' in rendered or '"tests_passed": 1' in rendered
        assert '"tests_failed": 1' in rendered

    def test_evidence_structure_in_example(self, agent_registry):
        """Test that example includes evidence structure."""
        rendered = agent_registry.render_agent('qa-tester')

        # Verify evidence in example
        assert '"evidence": {' in rendered
        assert '"logs"' in rendered
        assert '"error_messages"' in rendered
        assert '"screenshots"' in rendered

    def test_execution_timestamp_present(self, agent_registry):
        """Test that execution timestamps are documented."""
        rendered = agent_registry.render_agent('qa-tester')

        # Verify timestamps
        assert '"execution_timestamp"' in rendered

    def test_summary_calculations_documented(self, agent_registry):
        """Test that summary calculations are documented."""
        rendered = agent_registry.render_agent('qa-tester')

        # Verify summary fields
        assert '"summary": {' in rendered
        assert '"total_test_cases"' in rendered
        assert '"tests_passed"' in rendered
        assert '"tests_failed"' in rendered
        assert '"pass_rate"' in rendered

    def test_blackbox_principles_apply_to_execution(self, agent_registry):
        """Test that blackbox principles apply to execution mode."""
        rendered = agent_registry.render_agent('qa-tester')

        # Verify blackbox principles in execution
        assert '**Blackbox Execution Principles**' in rendered
        assert 'Test behavior from external perspective only' in rendered
        assert 'No access to internal implementation' in rendered
