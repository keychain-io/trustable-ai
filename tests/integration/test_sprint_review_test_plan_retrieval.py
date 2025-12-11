"""
Integration tests for sprint-review workflow Step 1.6: Test plan retrieval.

Tests the complete workflow integration for retrieving test plans from EPIC work
items, validating content, and preparing for test execution.
"""

import pytest
from pathlib import Path
import tempfile
import shutil
from workflows.registry import WorkflowRegistry


class TestSprintReviewTestPlanRetrievalIntegration:
    """Integration tests for test plan retrieval in sprint-review workflow."""

    @pytest.fixture
    def workflow_registry(self):
        """Create workflow registry for rendering workflows."""
        from config.loader import load_config

        # Load test configuration
        config = load_config('.claude/config.yaml')
        return WorkflowRegistry(config)

    @pytest.fixture
    def test_plans_dir(self):
        """Create temporary directory for test plans."""
        tmpdir = tempfile.mkdtemp()
        test_plans_path = Path(tmpdir) / 'acceptance-tests'
        test_plans_path.mkdir(parents=True, exist_ok=True)
        yield test_plans_path
        shutil.rmtree(tmpdir)

    def test_workflow_renders_with_test_plan_retrieval_step(self, workflow_registry):
        """Test that sprint-review workflow includes Step 1.6 for test plan retrieval."""
        # Render sprint-review workflow
        rendered = workflow_registry.render_workflow('sprint-review')

        # Verify Step 1.6 is present
        assert 'Step 1.6: Retrieve Test Plans from Work Items' in rendered
        assert 'Retrieve acceptance test plan files from EPIC work item attachments/links' in rendered

        # Verify retrieval logic is present
        assert 'retrieved_test_plans = []' in rendered
        assert 'retrieval_failures = []' in rendered

        # Verify platform-specific logic
        assert "adapter.platform == 'azure-devops'" in rendered
        assert "adapter.platform == 'file-based'" in rendered

        # Verify validation logic
        assert 'required_sections = [' in rendered
        assert "'EPIC'" in rendered
        assert "'FEATURE'" in rendered
        assert "'Test Case'" in rendered

        # Verify error handling
        assert 'except FileNotFoundError' in rendered
        assert 'except PermissionError' in rendered
        assert 'except UnicodeDecodeError' in rendered

        # Verify workflow state storage
        assert 'retrieved_test_plans_state = {' in rendered
        assert "'retrieval_timestamp'" in rendered

    def test_workflow_overview_includes_step_1_6(self, workflow_registry):
        """Test that workflow overview diagram includes Step 1.6."""
        # Render sprint-review workflow
        rendered = workflow_registry.render_workflow('sprint-review')

        # Verify overview includes Step 1.6
        assert 'Step 1.6: Retrieve test plans from work items' in rendered

        # Verify it's positioned correctly (after Step 1.5, before Step 2)
        step_15_pos = rendered.find('Step 1.5: Identify EPICs for testing')
        step_16_pos = rendered.find('Step 1.6: Retrieve test plans from work items')
        step_2_pos = rendered.find('Step 2: /tester')

        assert step_15_pos > 0
        assert step_16_pos > 0
        assert step_2_pos > 0
        assert step_15_pos < step_16_pos < step_2_pos

    def test_azure_devops_retrieval_integration(self, workflow_registry, test_plans_dir):
        """Test integration with Azure DevOps platform for test plan retrieval."""
        # Render workflow
        rendered = workflow_registry.render_workflow('sprint-review')

        # Verify Azure DevOps-specific code
        assert 'from azure_devops.cli_wrapper import azure_cli' in rendered
        assert 'AttachedFile' in rendered
        assert 'attachment_url' in rendered

        # Verify fallback to filesystem
        assert 'test_plan_path_fallback' in rendered

    def test_file_based_retrieval_integration(self, workflow_registry, test_plans_dir):
        """Test integration with file-based platform for test plan retrieval."""
        # Render workflow
        rendered = workflow_registry.render_workflow('sprint-review')

        # Verify file-based-specific code
        assert 'comments = work_item.get' in rendered
        assert "if 'Test Plan:' in comment_text:" in rendered
        assert 're.search' in rendered

    def test_content_validation_integration(self, workflow_registry):
        """Test that content validation is integrated into workflow."""
        # Render workflow
        rendered = workflow_registry.render_workflow('sprint-review')

        # Verify validation checks
        assert 'Check for expected sections' in rendered
        assert 'missing_sections' in rendered
        assert 'WARNING: Test plan missing expected sections' in rendered

        # Verify size check
        assert 'Check file size' in rendered
        assert 'unusually short' in rendered

    def test_error_handling_integration(self, workflow_registry):
        """Test that error handling is properly integrated."""
        # Render workflow
        rendered = workflow_registry.render_workflow('sprint-review')

        # Verify all error types are handled
        error_types = [
            'FileNotFoundError',
            'PermissionError',
            'UnicodeDecodeError',
            'Exception'
        ]

        for error_type in error_types:
            assert f'except {error_type}' in rendered

        # Verify failures are tracked
        assert 'retrieval_failures.append' in rendered

    def test_workflow_state_persistence_integration(self, workflow_registry):
        """Test that workflow state is properly persisted."""
        # Render workflow
        rendered = workflow_registry.render_workflow('sprint-review')

        # Verify state structure
        assert 'retrieved_test_plans_state = {' in rendered
        assert "'retrieved_test_plans':" in rendered
        assert "'retrieval_failures':" in rendered
        assert "'successful_retrievals':" in rendered
        assert "'failed_retrievals':" in rendered
        assert "'retrieval_timestamp':" in rendered

        # Verify checkpoint comment
        assert 'Checkpoint: Save retrieved test plans to workflow state' in rendered

    def test_testable_epics_filtering_integration(self, workflow_registry):
        """Test that testable EPICs are filtered to only include successful retrievals."""
        # Render workflow
        rendered = workflow_registry.render_workflow('sprint-review')

        # Verify filtering logic
        assert 'testable_epics = [' in rendered
        assert 'for epic in testable_epics' in rendered
        assert 'if any(tp' in rendered

        # Verify filtered EPICs count is displayed
        assert 'ready for acceptance testing with retrieved test plans' in rendered

    def test_retrieval_summary_output_integration(self, workflow_registry):
        """Test that retrieval summary is properly formatted."""
        # Render workflow
        rendered = workflow_registry.render_workflow('sprint-review')

        # Verify summary output
        assert 'Test Plan Retrieval Summary:' in rendered
        assert 'Total EPICs with test plans:' in rendered
        assert 'Test plans retrieved successfully:' in rendered
        assert 'Retrieval failures:' in rendered

        # Verify failure logging
        assert 'Failed to retrieve test plans for' in rendered
        assert 'These EPICs cannot proceed to acceptance testing' in rendered

    def test_utf8_encoding_integration(self, workflow_registry):
        """Test that UTF-8 encoding is used for cross-platform compatibility."""
        # Render workflow
        rendered = workflow_registry.render_workflow('sprint-review')

        # Verify UTF-8 encoding is specified
        assert "encoding='utf-8'" in rendered

    def test_path_handling_integration(self, workflow_registry):
        """Test that Path objects are used for filesystem operations."""
        # Render workflow
        rendered = workflow_registry.render_workflow('sprint-review')

        # Verify Path usage
        assert 'from pathlib import Path' in rendered
        assert "Path('.claude/acceptance-tests')" in rendered
        assert 'test_plans_dir.mkdir' in rendered

    def test_step_1_6_follows_step_1_5(self, workflow_registry):
        """Test that Step 1.6 correctly uses data from Step 1.5."""
        # Render workflow
        rendered = workflow_registry.render_workflow('sprint-review')

        # Verify Step 1.6 uses testable_epics from Step 1.5
        step_15_section = rendered[rendered.find('Step 1.5: Identify EPICs for testing'):
                                    rendered.find('Step 1.6: Retrieve Test Plans')]
        step_16_section = rendered[rendered.find('Step 1.6: Retrieve Test Plans'):
                                    rendered.find('Step 2: Run Acceptance Tests')]

        # Step 1.5 should populate testable_epics
        assert 'testable_epics.append(epic)' in step_15_section

        # Step 1.6 should iterate over testable_epics
        assert 'for epic in testable_epics:' in step_16_section
        assert "epic['id']" in step_16_section
        assert "epic['title']" in step_16_section

    def test_retrieval_critical_markers(self, workflow_registry):
        """Test that CRITICAL markers are present for verification gates."""
        # Render workflow
        rendered = workflow_registry.render_workflow('sprint-review')

        # Find Step 1.6 section
        step_16_section = rendered[rendered.find('Step 1.6: Retrieve Test Plans'):
                                    rendered.find('Step 2: Run Acceptance Tests')]

        # Verify CRITICAL marker
        assert 'CRITICAL' in step_16_section
        assert 'External Source of Truth' in step_16_section or 'Pillar #2' in step_16_section
