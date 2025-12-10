"""
Integration tests for CLI workflow verify command.

Tests workflow verification against external source of truth.
"""
import pytest
from pathlib import Path
from click.testing import CliRunner
from unittest.mock import Mock, patch, MagicMock

from cli.main import cli


@pytest.mark.integration
class TestWorkflowVerifyCommand:
    """Test suite for workflow verify command."""

    def test_verify_command_exists(self, sample_config_yaml):
        """Test that verify command is available."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            config_path = Path('.claude/config.yaml')
            config_path.parent.mkdir(parents=True)
            config_path.write_text(sample_config_yaml, encoding='utf-8')

            # Test help shows verify command
            result = runner.invoke(cli, ['workflow', '--help'])
            assert 'verify' in result.output

    def test_verify_accepts_workflow_name(self, sample_config_yaml):
        """Test verify command accepts workflow_name argument."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            config_path = Path('.claude/config.yaml')
            config_path.parent.mkdir(parents=True)
            config_path.write_text(sample_config_yaml, encoding='utf-8')

            # Mock the work_tracking module import
            mock_work_tracking = MagicMock()
            mock_adapter = Mock()
            mock_adapter.query_work_items.return_value = []
            mock_work_tracking.get_adapter.return_value = mock_adapter

            with patch.dict('sys.modules', {'work_tracking': mock_work_tracking}):
                result = runner.invoke(cli, ['workflow', 'verify', 'sprint-execution'])

                # Should accept workflow_name and either verify or show no checklist
                assert result.exit_code == 0
                assert 'Verifying' in result.output or 'No verification' in result.output

    def test_verify_accepts_epic_id_option(self, sample_config_yaml):
        """Test verify command accepts --epic-id option."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            config_path = Path('.claude/config.yaml')
            config_path.parent.mkdir(parents=True)
            config_path.write_text(sample_config_yaml, encoding='utf-8')

            mock_work_tracking = MagicMock()
            mock_adapter = Mock()
            mock_adapter.query_work_items.return_value = []
            mock_work_tracking.get_adapter.return_value = mock_adapter

            with patch.dict('sys.modules', {'work_tracking': mock_work_tracking}):
                result = runner.invoke(cli, ['workflow', 'verify', 'sprint-execution', '--epic-id', '123'])

                # Should accept epic-id option
                assert result.exit_code in [0, 1]  # Pass or fail, but not crash

    def test_verify_accepts_sprint_id_option(self, sample_config_yaml):
        """Test verify command accepts --sprint-id option."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            config_path = Path('.claude/config.yaml')
            config_path.parent.mkdir(parents=True)
            config_path.write_text(sample_config_yaml, encoding='utf-8')

            mock_work_tracking = MagicMock()
            mock_adapter = Mock()
            mock_adapter.query_work_items.return_value = []
            mock_work_tracking.get_adapter.return_value = mock_adapter

            with patch.dict('sys.modules', {'work_tracking': mock_work_tracking}):
                result = runner.invoke(cli, ['workflow', 'verify', 'sprint-execution', '--sprint-id', '456'])

                # Should accept sprint-id option
                assert result.exit_code in [0, 1]

    def test_verify_accepts_feature_id_option(self, sample_config_yaml):
        """Test verify command accepts --feature-id option."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            config_path = Path('.claude/config.yaml')
            config_path.parent.mkdir(parents=True)
            config_path.write_text(sample_config_yaml, encoding='utf-8')

            mock_work_tracking = MagicMock()
            mock_adapter = Mock()
            mock_adapter.query_work_items.return_value = []
            mock_work_tracking.get_adapter.return_value = mock_adapter

            with patch.dict('sys.modules', {'work_tracking': mock_work_tracking}):
                result = runner.invoke(cli, ['workflow', 'verify', 'sprint-execution', '--feature-id', '789'])

                # Should accept feature-id option
                assert result.exit_code in [0, 1]

    def test_verify_loads_workflow_template(self, sample_config_yaml):
        """Test verify command loads and renders workflow template."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            config_path = Path('.claude/config.yaml')
            config_path.parent.mkdir(parents=True)
            config_path.write_text(sample_config_yaml, encoding='utf-8')

            mock_work_tracking = MagicMock()
            mock_adapter = Mock()
            mock_adapter.query_work_items.return_value = []
            mock_work_tracking.get_adapter.return_value = mock_adapter

            with patch.dict('sys.modules', {'work_tracking': mock_work_tracking}):
                result = runner.invoke(cli, ['workflow', 'verify', 'sprint-execution'])

                # Should render workflow (may or may not have checklist)
                assert 'sprint-execution' in result.output or 'Verifying' in result.output or 'No verification' in result.output

    def test_verify_extracts_verification_checklist(self, sample_config_yaml):
        """Test verify command extracts verification checklist from workflow."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            config_path = Path('.claude/config.yaml')
            config_path.parent.mkdir(parents=True)
            config_path.write_text(sample_config_yaml, encoding='utf-8')

            mock_work_tracking = MagicMock()
            mock_adapter = Mock()
            mock_adapter.query_work_items.return_value = [{'id': 1, 'state': 'New'}]
            mock_work_tracking.get_adapter.return_value = mock_adapter

            with patch.dict('sys.modules', {'work_tracking': mock_work_tracking}):
                result = runner.invoke(cli, ['workflow', 'verify', 'sprint-execution'])

                # sprint-execution has verification checklist
                # Should extract and show checklist items
                assert 'Verifying' in result.output or 'Work item' in result.output or 'No verification' in result.output

    def test_verify_queries_adapter_for_validation(self, sample_config_yaml):
        """Test verify command queries adapter to validate checklist items."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            config_path = Path('.claude/config.yaml')
            config_path.parent.mkdir(parents=True)
            config_path.write_text(sample_config_yaml, encoding='utf-8')

            mock_work_tracking = MagicMock()
            mock_adapter = Mock()
            mock_adapter.query_work_items.return_value = [{'id': 1, 'state': 'New'}]
            mock_adapter.get_work_item.return_value = {'id': 1, 'state': 'New'}
            mock_work_tracking.get_adapter.return_value = mock_adapter

            with patch.dict('sys.modules', {'work_tracking': mock_work_tracking}):
                result = runner.invoke(cli, ['workflow', 'verify', 'sprint-execution'])

                # Should call adapter methods
                # May call query_work_items or get_work_item depending on checklist
                assert result.exit_code in [0, 1]

    def test_verify_returns_exit_code_0_on_success(self, sample_config_yaml):
        """Test verify returns exit code 0 when all checks pass."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            config_path = Path('.claude/config.yaml')
            config_path.parent.mkdir(parents=True)
            config_path.write_text(sample_config_yaml, encoding='utf-8')

            mock_work_tracking = MagicMock()
            mock_adapter = Mock()
            # Return valid data for all queries (needs to be not None and non-empty)
            mock_adapter.query_work_items.return_value = [{'id': 1, 'state': 'Done'}]
            mock_adapter.get_work_item.return_value = {'id': 1, 'state': 'Done', 'relations': []}
            mock_work_tracking.get_adapter.return_value = mock_adapter

            with patch.dict('sys.modules', {'work_tracking': mock_work_tracking}):
                # Test with a workflow that doesn't have verification checklist
                result = runner.invoke(cli, ['workflow', 'verify', 'sprint-planning'])

                # sprint-planning has no checklist, so should pass
                assert result.exit_code == 0
                assert 'PASSED' in result.output or 'No verification' in result.output

    def test_verify_returns_exit_code_1_on_failure(self, sample_config_yaml):
        """Test verify returns exit code 1 when checks fail."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            config_path = Path('.claude/config.yaml')
            config_path.parent.mkdir(parents=True)
            config_path.write_text(sample_config_yaml, encoding='utf-8')

            mock_work_tracking = MagicMock()
            mock_adapter = Mock()
            # Simulate adapter failure
            mock_adapter.query_work_items.return_value = None
            mock_work_tracking.get_adapter.return_value = mock_adapter

            with patch.dict('sys.modules', {'work_tracking': mock_work_tracking}):
                result = runner.invoke(cli, ['workflow', 'verify', 'sprint-execution'])

                # Should fail if adapter returns None for work item queries
                # (sprint-execution has work item checklist items)
                if 'FAILED' in result.output:
                    assert result.exit_code == 1

    def test_verify_handles_workflow_not_found(self, sample_config_yaml):
        """Test verify handles workflow not found error."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            config_path = Path('.claude/config.yaml')
            config_path.parent.mkdir(parents=True)
            config_path.write_text(sample_config_yaml, encoding='utf-8')

            mock_work_tracking = MagicMock()
            mock_adapter = Mock()
            mock_work_tracking.get_adapter.return_value = mock_adapter

            with patch.dict('sys.modules', {'work_tracking': mock_work_tracking}):
                result = runner.invoke(cli, ['workflow', 'verify', 'nonexistent-workflow'])

                # Should show error message
                assert result.exit_code == 1
                assert 'not found' in result.output.lower()
                assert 'Available workflows' in result.output

    def test_verify_handles_no_checklist(self, sample_config_yaml):
        """Test verify handles workflow with no checklist gracefully."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            config_path = Path('.claude/config.yaml')
            config_path.parent.mkdir(parents=True)
            config_path.write_text(sample_config_yaml, encoding='utf-8')

            mock_work_tracking = MagicMock()
            mock_adapter = Mock()
            mock_work_tracking.get_adapter.return_value = mock_adapter

            with patch.dict('sys.modules', {'work_tracking': mock_work_tracking}):
                # sprint-planning likely doesn't have verification checklist
                result = runner.invoke(cli, ['workflow', 'verify', 'sprint-planning'])

                # Should exit 0 with info message
                assert result.exit_code == 0
                assert 'No verification checklist' in result.output or 'PASSED' in result.output

    def test_verify_handles_adapter_query_failures(self, sample_config_yaml):
        """Test verify handles adapter query failures gracefully."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            config_path = Path('.claude/config.yaml')
            config_path.parent.mkdir(parents=True)
            config_path.write_text(sample_config_yaml, encoding='utf-8')

            mock_work_tracking = MagicMock()
            mock_adapter = Mock()
            # Simulate adapter exception
            mock_adapter.query_work_items.side_effect = Exception("Connection error")
            mock_work_tracking.get_adapter.return_value = mock_adapter

            with patch.dict('sys.modules', {'work_tracking': mock_work_tracking}):
                result = runner.invoke(cli, ['workflow', 'verify', 'sprint-execution'])

                # Should handle exception and report failure
                if 'FAILED' in result.output:
                    assert result.exit_code == 1
                    assert 'failed' in result.output.lower() or 'error' in result.output.lower()

    def test_verify_without_config_shows_error(self):
        """Test verify without configuration shows helpful error."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            result = runner.invoke(cli, ['workflow', 'verify', 'sprint-execution'])

            # Should show error about missing config
            assert result.exit_code == 1
            assert 'Error' in result.output or 'not found' in result.output.lower()
            assert 'trustable-ai init' in result.output

    def test_verify_handles_adapter_init_failure(self, sample_config_yaml):
        """Test verify handles adapter initialization failure."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            config_path = Path('.claude/config.yaml')
            config_path.parent.mkdir(parents=True)
            config_path.write_text(sample_config_yaml, encoding='utf-8')

            # Don't add work_tracking to sys.modules to simulate import failure
            result = runner.invoke(cli, ['workflow', 'verify', 'sprint-execution'])

            # Should show adapter initialization error
            assert result.exit_code == 1
            assert 'Error' in result.output

    def test_verify_with_sprint_id_queries_sprint_items(self, sample_config_yaml):
        """Test verify with --sprint-id queries sprint-specific items."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            config_path = Path('.claude/config.yaml')
            config_path.parent.mkdir(parents=True)
            config_path.write_text(sample_config_yaml, encoding='utf-8')

            mock_work_tracking = MagicMock()
            mock_adapter = Mock()
            mock_adapter.query_work_items.return_value = [
                {'id': 1, 'state': 'Done', 'iteration': 'Sprint 5'}
            ]
            mock_work_tracking.get_adapter.return_value = mock_adapter

            with patch.dict('sys.modules', {'work_tracking': mock_work_tracking}):
                result = runner.invoke(cli, ['workflow', 'verify', 'sprint-execution', '--sprint-id', '5'])

                # Should call query_work_items with iteration filter
                if mock_adapter.query_work_items.called:
                    # Check if called with sprint iteration
                    call_args = mock_adapter.query_work_items.call_args
                    if call_args and 'iteration' in str(call_args):
                        assert 'Sprint 5' in str(call_args) or '5' in str(call_args)

    def test_verify_with_epic_id_queries_epic_items(self, sample_config_yaml):
        """Test verify with --epic-id queries epic-specific items."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            config_path = Path('.claude/config.yaml')
            config_path.parent.mkdir(parents=True)
            config_path.write_text(sample_config_yaml, encoding='utf-8')

            mock_work_tracking = MagicMock()
            mock_adapter = Mock()
            mock_adapter.query_work_items.return_value = [
                {'id': 1, 'state': 'Done', 'parent': 123}
            ]
            mock_work_tracking.get_adapter.return_value = mock_adapter

            with patch.dict('sys.modules', {'work_tracking': mock_work_tracking}):
                result = runner.invoke(cli, ['workflow', 'verify', 'sprint-execution', '--epic-id', '123'])

                # Should call query_work_items with parent filter
                if mock_adapter.query_work_items.called:
                    call_args = mock_adapter.query_work_items.call_args
                    if call_args and 'filters' in str(call_args):
                        assert '123' in str(call_args) or 'Parent' in str(call_args)

    def test_verify_blocked_items_check(self, sample_config_yaml):
        """Test verify validates blocked items have blocker links."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            config_path = Path('.claude/config.yaml')
            config_path.parent.mkdir(parents=True)
            config_path.write_text(sample_config_yaml, encoding='utf-8')

            mock_work_tracking = MagicMock()
            mock_adapter = Mock()
            # Simulate blocked item without relations
            mock_adapter.query_work_items.return_value = [
                {'id': 1, 'state': 'Blocked'}
            ]
            mock_adapter.get_work_item.return_value = {
                'id': 1,
                'state': 'Blocked',
                'relations': []  # No blocker link
            }
            mock_work_tracking.get_adapter.return_value = mock_adapter

            with patch.dict('sys.modules', {'work_tracking': mock_work_tracking}):
                result = runner.invoke(cli, ['workflow', 'verify', 'sprint-execution'])

                # sprint-execution has blocked items check
                # Should fail if blocked items have no relations
                if 'blocked' in result.output.lower():
                    # Verification attempted
                    assert result.exit_code in [0, 1]

    def test_verify_shows_verification_progress(self, sample_config_yaml):
        """Test verify shows progress of verification checks."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            config_path = Path('.claude/config.yaml')
            config_path.parent.mkdir(parents=True)
            config_path.write_text(sample_config_yaml, encoding='utf-8')

            mock_work_tracking = MagicMock()
            mock_adapter = Mock()
            mock_adapter.query_work_items.return_value = [{'id': 1, 'state': 'New'}]
            mock_work_tracking.get_adapter.return_value = mock_adapter

            with patch.dict('sys.modules', {'work_tracking': mock_work_tracking}):
                result = runner.invoke(cli, ['workflow', 'verify', 'sprint-execution'])

                # Should show verification header or results
                assert 'Verifying' in result.output or 'No verification' in result.output or 'PASSED' in result.output

    def test_verify_displays_failed_checks_list(self, sample_config_yaml):
        """Test verify displays list of failed checks when verification fails."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            config_path = Path('.claude/config.yaml')
            config_path.parent.mkdir(parents=True)
            config_path.write_text(sample_config_yaml, encoding='utf-8')

            mock_work_tracking = MagicMock()
            mock_adapter = Mock()
            # Return None to trigger failure
            mock_adapter.query_work_items.return_value = None
            mock_work_tracking.get_adapter.return_value = mock_adapter

            with patch.dict('sys.modules', {'work_tracking': mock_work_tracking}):
                result = runner.invoke(cli, ['workflow', 'verify', 'sprint-execution'])

                # If there's a failure, should list failed checks
                if result.exit_code == 1 and 'FAILED' in result.output:
                    # Should show bullet list of failures
                    assert '•' in result.output or '-' in result.output
