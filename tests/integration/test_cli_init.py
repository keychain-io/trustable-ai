"""
Integration tests for CLI init command.

Tests the complete init workflow with real file system operations.
"""
import pytest
from pathlib import Path
from click.testing import CliRunner

from cli.main import cli


@pytest.mark.integration
class TestInitCommand:
    """Test suite for cwf init command."""

    def test_init_interactive_success(self):
        """Test successful interactive initialization."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            result = runner.invoke(cli, ['init'], input='\n'.join([
                'Test Project',           # Project name
                '1',                       # Project type: web-application
                'Python,TypeScript',       # Languages
                'FastAPI,React',          # Frameworks
                'Azure,Docker',           # Platforms
                'https://dev.azure.com/test',  # Azure DevOps org
                'Test Project',           # Azure DevOps project
                'Sprint {number}',        # Sprint naming
            ]))

            assert result.exit_code == 0
            assert 'Configuration created successfully' in result.output

            # Verify files created
            assert Path('.claude/config.yaml').exists()
            assert Path('.claude/agents/').exists()
            assert Path('.claude/workflows/').exists()

    def test_init_non_interactive(self):
        """Test non-interactive initialization."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            result = runner.invoke(cli, [
                'init',
                '--project-name', 'Test Project',
                '--project-type', 'api',
                '--no-interactive'
            ])

            assert result.exit_code == 0
            assert Path('.claude/config.yaml').exists()

    def test_init_custom_config_path(self):
        """Test initialization with custom config path."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            result = runner.invoke(cli, [
                'init',
                '--config-path', 'custom-config.yaml',
                '--project-name', 'Test Project',
                '--project-type', 'api',
                '--no-interactive'
            ])

            assert result.exit_code == 0
            assert Path('custom-config.yaml').exists()

    def test_init_already_initialized(self):
        """Test initialization when already initialized."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # First init
            runner.invoke(cli, [
                'init',
                '--project-name', 'Test Project',
                '--project-type', 'api',
                '--no-interactive'
            ])

            # Second init should warn
            result = runner.invoke(cli, [
                'init',
                '--project-name', 'Test Project',
                '--project-type', 'api',
                '--no-interactive'
            ])

            assert 'already exists' in result.output.lower() or result.exit_code != 0


@pytest.mark.integration
class TestInitDirectoryStructure:
    """Test directory structure creation during init."""

    def test_creates_claude_directory(self):
        """Test that .claude directory is created."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            runner.invoke(cli, [
                'init',
                '--project-name', 'Test',
                '--project-type', 'api',
                '--no-interactive'
            ])

            assert Path('.claude').exists()
            assert Path('.claude').is_dir()

    def test_creates_subdirectories(self):
        """Test that required subdirectories are created."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            runner.invoke(cli, [
                'init',
                '--project-name', 'Test',
                '--project-type', 'api',
                '--no-interactive'
            ])

            assert Path('.claude/agents').exists()
            assert Path('.claude/workflows').exists()
            assert Path('.claude/commands').exists()
            assert Path('.claude/workflow-state').exists()
            assert Path('.claude/profiling').exists()

    def test_config_file_valid_yaml(self):
        """Test that generated config file is valid YAML."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            runner.invoke(cli, [
                'init',
                '--project-name', 'Test Project',
                '--project-type', 'api',
                '--no-interactive'
            ])

            config_path = Path('.claude/config.yaml')
            assert config_path.exists()

            # Try to load the config
            from config.loader import ConfigLoader
            loader = ConfigLoader(config_path)
            config = loader.load()

            assert config.project.name == 'Test Project'
            assert config.project.type == 'api'
