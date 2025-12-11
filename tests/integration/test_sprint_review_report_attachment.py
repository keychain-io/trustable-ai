"""
Integration tests for sprint-review workflow Step 1.8: Test report attachment and linking.

Tests the complete workflow integration for attaching/linking test reports to EPIC work items,
including platform-specific attachment (Azure DevOps) or linking (file-based) and verification.
"""

import pytest
from pathlib import Path
from workflows.registry import WorkflowRegistry


class TestSprintReviewReportAttachmentIntegration:
    """Integration tests for test report attachment in sprint-review workflow."""

    @pytest.fixture
    def workflow_registry(self):
        """Create workflow registry for rendering workflows."""
        from config.loader import load_config

        config = load_config('.claude/config.yaml')
        return WorkflowRegistry(config)

    def test_workflow_renders_with_step_1_8(self, workflow_registry):
        """Test that sprint-review workflow includes Step 1.8."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # Verify Step 1.8 is present
        assert 'Step 1.8: Attach Test Reports to EPIC Work Items' in rendered
        assert 'Attach or link test report files to EPIC work items' in rendered

    def test_workflow_overview_includes_step_1_8(self, workflow_registry):
        """Test that workflow overview diagram includes Step 1.8."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # Verify overview includes Step 1.8
        assert 'Step 1.8: Attach test reports to EPIC work items' in rendered

        # Verify it's positioned correctly
        step_17_pos = rendered.find('Step 1.7: Execute tests and generate reports')
        step_18_pos = rendered.find('Step 1.8: Attach test reports to EPIC work items')
        step_2_pos = rendered.find('Step 2: /tester')

        assert step_17_pos > 0
        assert step_18_pos > 0
        assert step_2_pos > 0
        assert step_17_pos < step_18_pos < step_2_pos

    def test_azure_devops_attachment_logic_present(self, workflow_registry):
        """Test that Azure DevOps attachment logic is documented."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # Verify Azure DevOps attachment
        assert "if adapter.platform == 'azure-devops':" in rendered
        assert 'attach_file_to_work_item' in rendered
        assert 'azure_cli.attach_file_to_work_item(' in rendered

    def test_azure_devops_attachment_parameters(self, workflow_registry):
        """Test that Azure DevOps attachment parameters are correct."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # Verify attachment parameters
        assert 'work_item_id=' in rendered
        assert 'file_path=' in rendered
        assert 'comment=' in rendered
        assert 'Test Execution Report' in rendered

    def test_azure_devops_verification_present(self, workflow_registry):
        """Test that Azure DevOps attachment verification is present."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # Verify verification logic
        assert 'verify_attachment_exists' in rendered
        assert 'attachment_exists' in rendered
        assert 'Attachment verified:' in rendered

    def test_file_based_comment_logic_present(self, workflow_registry):
        """Test that file-based comment logic is documented."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # Verify file-based linking
        assert "elif adapter.platform == 'file-based':" in rendered
        assert 'adapter.add_comment(' in rendered
        assert 'Recording test report path in EPIC metadata' in rendered

    def test_file_based_comment_structure(self, workflow_registry):
        """Test that file-based comment structure is present."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # Verify comment structure
        assert 'Test Report:' in rendered
        assert 'Overall Status:' in rendered
        assert 'Pass Rate:' in rendered
        assert 'Deployment Ready:' in rendered

    def test_file_based_verification_present(self, workflow_registry):
        """Test that file-based comment verification is present."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # Verify verification logic
        assert 'comment_found = any(' in rendered
        assert 'Comment verified in EPIC' in rendered

    def test_attachment_failure_tracking_present(self, workflow_registry):
        """Test that attachment failure tracking is present."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # Verify failure tracking
        assert 'failed_attachments' in rendered
        assert 'failed_attachments.append({' in rendered

    def test_attachment_summary_output(self, workflow_registry):
        """Test that attachment summary output is present."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # Verify summary output
        assert 'Test Report Attachment Summary:' in rendered
        assert 'Total test reports:' in rendered
        assert 'Successfully attached/linked:' in rendered
        assert 'Failed:' in rendered

    def test_workflow_halt_on_failure(self, workflow_registry):
        """Test that workflow halts on attachment failures."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # Verify halt logic
        assert 'TEST REPORT ATTACHMENT VERIFICATION FAILED' in rendered
        assert 'Workflow cannot proceed without verified test report attachments' in rendered
        assert 'sys.exit(1)' in rendered

    def test_workflow_continuation_on_success(self, workflow_registry):
        """Test that workflow continues on attachment success."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # Verify success continuation
        assert 'All {attached_count} test reports attached/linked and verified successfully' in rendered

    def test_attachment_state_storage(self, workflow_registry):
        """Test that attachment state is stored in workflow state."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # Verify state storage
        assert 'report_attachment_state = {' in rendered
        assert "'attached_count'" in rendered or '"attached_count"' in rendered
        assert "'failed_count'" in rendered or '"failed_count"' in rendered
        assert "'test_report_files'" in rendered or '"test_report_files"' in rendered
        assert "'failed_attachments'" in rendered or '"failed_attachments"' in rendered
        assert "'attachment_timestamp'" in rendered or '"attachment_timestamp"' in rendered

    def test_error_handling_present(self, workflow_registry):
        """Test that error handling is comprehensive."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # Verify error handling
        assert 'except Exception as e:' in rendered
        assert 'Failed to attach/link test report' in rendered

    def test_platform_attribute_usage(self, workflow_registry):
        """Test that platform attribute is used for branching."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # Verify platform branching
        assert 'adapter.platform' in rendered
        assert "Platform: {adapter.platform}" in rendered

    def test_critical_marker_present(self, workflow_registry):
        """Test that CRITICAL marker is present for verification gate."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # Find Step 1.8 section
        step_18_start = rendered.find('Step 1.8: Attach Test Reports to EPIC Work Items')
        step_2_start = rendered.find('Step 2: Run Acceptance Tests')
        step_18_section = rendered[step_18_start:step_2_start]

        # Verify CRITICAL marker
        assert 'CRITICAL' in step_18_section

    def test_external_source_of_truth_reference(self, workflow_registry):
        """Test that External Source of Truth is referenced."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # Verify VISION.md reference
        assert 'VISION.md Pillar #2' in rendered or 'External Source of Truth' in rendered

    def test_loop_over_test_execution_results(self, workflow_registry):
        """Test that step loops over test execution results."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # Verify loop
        assert 'for test_result_entry in test_execution_results_all:' in rendered

    def test_epic_metadata_extraction(self, workflow_registry):
        """Test that EPIC metadata is extracted from test results."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # Verify metadata extraction
        assert "epic_id = test_result_entry['epic_id']" in rendered
        assert "epic_title = test_result_entry['epic_title']" in rendered
        assert "report_filepath = test_result_entry['report_filepath']" in rendered
        assert "report_filename = test_result_entry['report_filename']" in rendered

    def test_azure_cli_import_present(self, workflow_registry):
        """Test that Azure CLI wrapper import is present."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # Verify import
        assert 'from azure_devops.cli_wrapper import azure_cli' in rendered
        assert 'sys.path.insert(0, ".claude/skills")' in rendered

    def test_pathlib_usage_present(self, workflow_registry):
        """Test that Path objects are used for file paths."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # Verify Path usage
        assert 'from pathlib import Path' in rendered
        assert 'Path(' in rendered

    def test_report_filepath_in_comment(self, workflow_registry):
        """Test that report filepath is included in file-based comment."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # Verify filepath in comment
        assert 'Test report file: {report_filepath}' in rendered

    def test_test_results_summary_in_comment(self, workflow_registry):
        """Test that test results summary is in file-based comment."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # Verify summary fields
        assert "test_result_entry['overall_status']" in rendered
        assert "test_result_entry['pass_rate']" in rendered
        assert "test_result_entry['deployment_ready']" in rendered

    def test_failure_error_details_present(self, workflow_registry):
        """Test that failure error details are captured."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # Verify error details
        assert "'error':" in rendered or '"error":' in rendered
        assert 'Attachment not found after upload' in rendered
        assert 'Attachment upload failed' in rendered
        assert 'Comment not found after creation' in rendered

    def test_unsupported_platform_handling(self, workflow_registry):
        """Test that unsupported platforms are handled gracefully."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # Verify unsupported platform handling
        assert 'else:' in rendered
        assert 'Unsupported' in rendered or 'not supported' in rendered
        assert 'Test report available at:' in rendered

    def test_step_18_follows_step_17_data_flow(self, workflow_registry):
        """Test that Step 1.8 uses data from Step 1.7."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # Step 1.7 should produce test_execution_results_all
        step_17_section = rendered[rendered.find('Step 1.7: Execute Tests'):
                                    rendered.find('Step 1.8: Attach Test Reports')]
        assert 'test_execution_results_all' in step_17_section

        # Step 1.8 should consume test_execution_results_all
        step_18_section = rendered[rendered.find('Step 1.8: Attach Test Reports'):
                                    rendered.find('Step 2: Run Acceptance Tests')]
        assert 'test_execution_results_all' in step_18_section
        assert 'for test_result_entry in test_execution_results_all' in step_18_section

    def test_checkpoint_message_present(self, workflow_registry):
        """Test that checkpoint message is present."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # Verify checkpoint
        assert 'Test report attachment state stored for workflow verification' in rendered

    def test_iteration_output_present(self, workflow_registry):
        """Test that per-EPIC output is documented."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # Verify per-EPIC output
        assert 'Processing EPIC #{epic_id}' in rendered
        assert 'Test report file:' in rendered

    def test_attachment_result_messages(self, workflow_registry):
        """Test that attachment result messages are present."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # Verify result messages
        assert '✅ File attached successfully' in rendered
        assert '✅ Attachment verified:' in rendered
        assert '❌ ERROR: Attachment verification failed' in rendered
        assert '✅ Test report path recorded in EPIC comments' in rendered
        assert '✅ Comment verified in EPIC' in rendered

    def test_numeric_epic_id_handling(self, workflow_registry):
        """Test that numeric EPIC ID extraction is handled."""
        rendered = workflow_registry.render_workflow('sprint-review')

        # Verify numeric ID extraction
        assert "int(epic_id.split('-')[-1])" in rendered
