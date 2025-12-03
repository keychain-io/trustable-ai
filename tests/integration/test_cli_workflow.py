"""
Integration tests for CLI workflow commands.

Tests workflow management commands with real file system operations.
"""
import pytest
from pathlib import Path
from click.testing import CliRunner

from cli.main import cli


@pytest.mark.integration
class TestWorkflowListCommand:
    """Test suite for cwf workflow list command."""

    def test_workflow_list_without_config(self):
        """Test listing workflows without configuration shows error."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            result = runner.invoke(cli, ['workflow', 'list'])

            # Should show error about missing config
            assert 'Error' in result.output or 'not found' in result.output.lower()
            assert 'trustable-ai init' in result.output

    def test_workflow_list_with_config(self, sample_config_yaml):
        """Test listing workflows with configuration."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            config_path = Path('.claude/config.yaml')
            config_path.parent.mkdir(parents=True)
            config_path.write_text(sample_config_yaml)

            result = runner.invoke(cli, ['workflow', 'list'])

            assert result.exit_code == 0
            assert 'sprint-planning' in result.output


@pytest.mark.integration
class TestWorkflowRenderCommand:
    """Test suite for cwf workflow render command."""

    def test_render_workflow_success(self, sample_config_yaml):
        """Test rendering a workflow."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            config_path = Path('.claude/config.yaml')
            config_path.parent.mkdir(parents=True)
            config_path.write_text(sample_config_yaml)

            result = runner.invoke(cli, ['workflow', 'render', 'sprint-planning'])

            assert result.exit_code == 0
            assert 'Sprint Planning Workflow' in result.output or 'sprint' in result.output.lower()

    def test_render_workflow_to_file(self, sample_config_yaml):
        """Test rendering workflow to file."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            config_path = Path('.claude/config.yaml')
            config_path.parent.mkdir(parents=True)
            config_path.write_text(sample_config_yaml)

            Path('.claude/commands').mkdir(parents=True)

            result = runner.invoke(cli, [
                'workflow', 'render', 'sprint-planning',
                '-o', '.claude/commands/sprint-planning.md'
            ])

            assert result.exit_code == 0
            assert Path('.claude/commands/sprint-planning.md').exists()

            content = Path('.claude/commands/sprint-planning.md').read_text()
            assert 'Test Project' in content

    def test_render_workflow_includes_enabled_agents(self, sample_config_yaml):
        """Test that rendered workflow includes only enabled agents."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            config_path = Path('.claude/config.yaml')
            config_path.parent.mkdir(parents=True)
            config_path.write_text(sample_config_yaml)

            result = runner.invoke(cli, ['workflow', 'render', 'sprint-planning'])

            assert result.exit_code == 0
            # Should include business analyst (enabled)
            assert 'business-analyst' in result.output.lower() or 'Business Analyst' in result.output

    def test_render_all_workflows(self, sample_config_yaml):
        """Test rendering all workflows."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            config_path = Path('.claude/config.yaml')
            config_path.parent.mkdir(parents=True)
            config_path.write_text(sample_config_yaml)

            Path('.claude/commands').mkdir(parents=True)

            result = runner.invoke(cli, [
                'workflow', 'render-all',
                '-o', '.claude/commands'
            ])

            assert result.exit_code == 0
            assert Path('.claude/commands/sprint-planning.md').exists()


@pytest.mark.integration
class TestWorkflowRunCommand:
    """Test suite for cwf workflow run command."""

    def test_workflow_run_dry_run(self, sample_config_yaml):
        """Test workflow dry-run mode."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            config_path = Path('.claude/config.yaml')
            config_path.parent.mkdir(parents=True)
            config_path.write_text(sample_config_yaml)

            result = runner.invoke(cli, [
                'workflow', 'run', 'sprint-planning',
                '--dry-run'
            ])

            # Dry run should show workflow definition
            assert result.exit_code == 0
            assert 'dry-run' in result.output.lower() or 'workflow definition' in result.output.lower()

    def test_workflow_run_requires_config(self):
        """Test that workflow run shows message about implementation status."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            result = runner.invoke(cli, [
                'workflow', 'run', 'sprint-planning'
            ])

            # Should show workflow or message (engine not yet implemented)
            assert result.exit_code == 0
            assert 'workflow' in result.output.lower()
