"""
Integration tests for CLI validate command.

Tests validation of configuration and setup.
"""
import pytest
from pathlib import Path
from click.testing import CliRunner

from cli.main import cli


@pytest.mark.integration
class TestValidateCommand:
    """Test suite for cwf validate command."""

    def test_validate_without_config(self):
        """Test validation without configuration."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            result = runner.invoke(cli, ['validate'])

            # Should report missing configuration
            assert 'config' in result.output.lower()
            assert result.exit_code != 0

    def test_validate_with_valid_config(self, sample_config_yaml):
        """Test validation with valid configuration."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Create config
            config_path = Path('.claude/config.yaml')
            config_path.parent.mkdir(parents=True)
            config_path.write_text(sample_config_yaml)

            # Create required directories
            Path('.claude/agents').mkdir(parents=True)
            Path('.claude/workflows').mkdir(parents=True)
            Path('.claude/commands').mkdir(parents=True)

            result = runner.invoke(cli, ['validate'])

            assert result.exit_code == 0
            assert 'valid' in result.output.lower() or '✓' in result.output

    def test_validate_reports_missing_directories(self, sample_config_yaml):
        """Test that validation reports missing directories."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            config_path = Path('.claude/config.yaml')
            config_path.parent.mkdir(parents=True)
            config_path.write_text(sample_config_yaml)

            # Don't create subdirectories

            result = runner.invoke(cli, ['validate'])

            # Should warn about missing directories
            assert 'agents' in result.output.lower() or 'directory' in result.output.lower()

    def test_validate_checks_agent_templates(self, sample_config_yaml):
        """Test that validation checks for agent templates."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            config_path = Path('.claude/config.yaml')
            config_path.parent.mkdir(parents=True)
            config_path.write_text(sample_config_yaml)

            Path('.claude/agents').mkdir(parents=True)
            Path('.claude/workflows').mkdir(parents=True)
            Path('.claude/commands').mkdir(parents=True)

            result = runner.invoke(cli, ['validate'])

            # Should validate agents
            assert 'agent' in result.output.lower()

    def test_validate_custom_config_path(self, sample_config_yaml):
        """Test validation with custom config path."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            config_path = Path('custom-config.yaml')
            config_path.write_text(sample_config_yaml)

            result = runner.invoke(cli, [
                'validate',
                '--config-path', 'custom-config.yaml'
            ])

            # Should validate custom config
            assert result.exit_code == 0 or 'config' in result.output.lower()

    def test_validate_reports_config_errors(self):
        """Test that validation reports configuration errors."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Create invalid config
            config_path = Path('.claude/config.yaml')
            config_path.parent.mkdir(parents=True)
            config_path.write_text('invalid: yaml: content: [')

            result = runner.invoke(cli, ['validate'])

            assert result.exit_code != 0
            assert 'error' in result.output.lower() or 'failed' in result.output.lower()


@pytest.mark.integration
class TestValidateWorkTracking:
    """Test validation of work tracking configuration."""

    def test_validate_azure_devops_config(self, sample_config_yaml):
        """Test validation of Azure DevOps configuration."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            config_path = Path('.claude/config.yaml')
            config_path.parent.mkdir(parents=True)
            config_path.write_text(sample_config_yaml)

            Path('.claude/agents').mkdir(parents=True)
            Path('.claude/workflows').mkdir(parents=True)
            Path('.claude/commands').mkdir(parents=True)

            result = runner.invoke(cli, ['validate'])

            # Should validate work tracking config
            assert 'azure' in result.output.lower() or 'work tracking' in result.output.lower()

    def test_validate_quality_standards(self, sample_config_yaml):
        """Test validation of quality standards."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            config_path = Path('.claude/config.yaml')
            config_path.parent.mkdir(parents=True)
            config_path.write_text(sample_config_yaml)

            Path('.claude/agents').mkdir(parents=True)
            Path('.claude/workflows').mkdir(parents=True)
            Path('.claude/commands').mkdir(parents=True)

            result = runner.invoke(cli, ['validate'])

            # Should validate quality standards
            assert 'quality' in result.output.lower() or 'coverage' in result.output.lower()
