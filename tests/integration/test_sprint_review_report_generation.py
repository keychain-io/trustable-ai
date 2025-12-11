"""
Integration tests for sprint-review workflow Step 1.7: Test report generation.

Tests the complete workflow integration for executing tests and generating reports,
including agent invocation, report formatting, and filesystem storage.
"""

import pytest
from pathlib import Path
from workflows.registry import WorkflowRegistry


class TestSprintReviewReportGenerationIntegration:
    """Integration tests for test report generation in sprint-review workflow."""

    @pytest.fixture
    def workflow_registry(self):
        """Create workflow registry for rendering workflows."""
        from config.loader import load_config

        config = load_config('.claude/config.yaml')
        return WorkflowRegistry(config)

    def test_workflow_renders_with_step_1_7(self, workflow_registry):
        """Test that sprint-review workflow includes Step 1.7."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # Verify Step 1.7 is present
        assert 'Step 1.7: Execute Tests and Generate Reports' in rendered
        assert 'Execute acceptance tests for each EPIC' in rendered

    def test_workflow_overview_includes_step_1_7(self, workflow_registry):
        """Test that workflow overview diagram includes Step 1.7."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # Verify overview includes Step 1.7
        assert 'Step 1.7: Execute tests and generate reports' in rendered

        # Verify it's positioned correctly
        step_16_pos = rendered.find('Step 1.6: Retrieve test plans')
        step_17_pos = rendered.find('Step 1.7: Execute tests and generate reports')
        step_2_pos = rendered.find('Step 2: /tester')

        assert step_16_pos > 0
        assert step_17_pos > 0
        assert step_2_pos > 0
        assert step_16_pos < step_17_pos < step_2_pos

    def test_agent_execution_mode_invocation_present(self, workflow_registry):
        """Test that qa-tester agent execution mode invocation is documented."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # Verify agent spawning logic
        assert 'qa-tester agent in execution mode' in rendered
        assert '"mode": "execute"' in rendered
        assert 'execution_request' in rendered

    def test_execution_request_structure_documented(self, workflow_registry):
        """Test that execution request structure is present."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # Verify request structure
        assert '"epic_id": epic_id' in rendered
        assert '"epic_title": epic_title' in rendered
        assert '"test_plan_content": test_plan_content' in rendered
        assert '"sprint_context"' in rendered

    def test_report_generation_logic_present(self, workflow_registry):
        """Test that report generation logic is present."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # Verify report building
        assert 'Generate markdown test report' in rendered
        assert 'report_lines = []' in rendered
        assert '# EPIC Acceptance Test Execution Report' in rendered

    def test_report_sections_present(self, workflow_registry):
        """Test that all report sections are present."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # Verify report sections
        assert '## Executive Summary' in rendered
        assert '## Quality Gates' in rendered
        assert '## Test Case Results' in rendered
        assert '## Defects Found' in rendered
        assert '## Deployment Readiness' in rendered
        assert '## Overall Assessment' in rendered

    def test_report_file_writing_logic_present(self, workflow_registry):
        """Test that report file writing logic is present."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # Verify file writing
        assert 'reports_dir = Path' in rendered
        assert 'acceptance-tests' in rendered
        assert 'test-report.md' in rendered
        assert "encoding='utf-8'" in rendered

    def test_error_handling_present(self, workflow_registry):
        """Test that error handling is comprehensive."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # Verify error handling
        assert 'except json.JSONDecodeError' in rendered
        assert 'except IOError' in rendered
        assert 'except Exception' in rendered
        assert 'execution_failures' in rendered

    def test_workflow_state_storage_present(self, workflow_registry):
        """Test that workflow state storage is present."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # Verify state storage
        assert 'test_execution_state = {' in rendered
        assert "'test_execution_results'" in rendered
        assert "'test_report_files'" in rendered
        assert "'execution_failures'" in rendered

    def test_summary_output_present(self, workflow_registry):
        """Test that execution summary output is present."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # Verify summary
        assert 'Test Execution and Report Generation Summary' in rendered
        assert 'Total EPICs tested' in rendered
        assert 'Test reports generated' in rendered

    def test_status_emoji_mapping_present(self, workflow_registry):
        """Test that status emoji mappings are present."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # Verify emoji mappings
        assert "'pass': '✅'" in rendered or '"pass": "✅"' in rendered
        assert "'fail': '❌'" in rendered or '"fail": "❌"' in rendered

    def test_severity_emoji_mapping_present(self, workflow_registry):
        """Test that severity emoji mappings are present."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # Verify severity mappings
        assert "'critical': '🔴'" in rendered or '"critical": "🔴"' in rendered
        assert "'high': '🟠'" in rendered or '"high": "🟠"' in rendered

    def test_report_metadata_present(self, workflow_registry):
        """Test that report metadata is included."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # Verify metadata
        assert 'execution_timestamp' in rendered
        assert 'sprint_context' in rendered
        assert 'environment' in rendered

    def test_quality_gates_evaluation_present(self, workflow_registry):
        """Test that quality gates evaluation is present."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # Verify quality gates
        assert 'quality_gates' in rendered
        assert 'gates_passed' in rendered
        assert 'all_high_priority_pass' in rendered

    def test_deployment_readiness_logic_present(self, workflow_registry):
        """Test that deployment readiness logic is present."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # Verify deployment readiness
        assert 'deployment_ready' in rendered
        assert 'required_fixes' in rendered
        assert 'optional_improvements' in rendered

    def test_critical_marker_present(self, workflow_registry):
        """Test that CRITICAL marker is present for verification gate."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # Find Step 1.7 section
        step_17_start = rendered.find('Step 1.7: Execute Tests and Generate Reports')
        step_2_start = rendered.find('Step 2: Run Acceptance Tests')
        step_17_section = rendered[step_17_start:step_2_start]

        # Verify CRITICAL marker
        assert 'CRITICAL' in step_17_section

    def test_external_source_of_truth_reference(self, workflow_registry):
        """Test that External Source of Truth is referenced."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # Verify VISION.md reference
        assert 'VISION.md Pillar #2' in rendered or 'External Source of Truth' in rendered

    def test_utf8_encoding_specified(self, workflow_registry):
        """Test that UTF-8 encoding is explicitly specified."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # Verify UTF-8 encoding
        assert "encoding='utf-8'" in rendered

    def test_path_handling_with_pathlib(self, workflow_registry):
        """Test that Path objects are used for filesystem operations."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # Verify Path usage
        assert 'from pathlib import Path' in rendered or 'Path(' in rendered

    def test_datetime_usage_present(self, workflow_registry):
        """Test that datetime is used for timestamps."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # Verify datetime usage
        assert 'from datetime import datetime' in rendered
        assert 'datetime.now()' in rendered

    def test_json_handling_present(self, workflow_registry):
        """Test that JSON handling is present."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # Verify JSON usage
        assert 'import json' in rendered
        assert 'json.loads' in rendered or 'json.dumps' in rendered

    def test_report_footer_generation(self, workflow_registry):
        """Test that report footer is generated."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # Verify footer
        assert 'Report generated by Trustable AI Workbench' in rendered

    def test_step_17_follows_step_16_data_flow(self, workflow_registry):
        """Test that Step 1.7 uses data from Step 1.6."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # Step 1.6 should produce retrieved_test_plans
        step_16_section = rendered[rendered.find('Step 1.6: Retrieve Test Plans'):
                                    rendered.find('Step 1.7: Execute Tests')]
        assert 'retrieved_test_plans' in step_16_section

        # Step 1.7 should consume retrieved_test_plans
        step_17_section = rendered[rendered.find('Step 1.7: Execute Tests'):
                                    rendered.find('Step 2: Run Acceptance Tests')]
        assert 'retrieved_test_plans' in step_17_section
        assert 'for epic_test_data in retrieved_test_plans' in step_17_section

    def test_report_storage_directory_creation(self, workflow_registry):
        """Test that report storage directory creation is present."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # Verify directory creation
        assert '.claude/acceptance-tests' in rendered
        assert 'mkdir(parents=True, exist_ok=True)' in rendered

    def test_placeholder_documentation_present(self, workflow_registry):
        """Test that placeholder documentation is present for agent call."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # Verify placeholder comments
        assert 'PLACEHOLDER' in rendered or 'In production' in rendered
        assert 'Task tool' in rendered or 'Task(' in rendered
