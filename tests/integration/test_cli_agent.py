"""
Integration tests for CLI agent commands.

Tests agent management commands with real file system operations.
"""
import pytest
from pathlib import Path
from click.testing import CliRunner

from cli.main import cli


@pytest.mark.integration
class TestAgentListCommand:
    """Test suite for cwf agent list command."""

    def test_agent_list_without_config(self):
        """Test listing agents without configuration shows error."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            result = runner.invoke(cli, ['agent', 'list'])

            # Should show error about missing config
            assert 'Error' in result.output or 'not found' in result.output.lower()
            assert 'taid init' in result.output

    def test_agent_list_with_config(self, sample_config_yaml):
        """Test listing agents with configuration."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Create config
            config_path = Path('.claude/config.yaml')
            config_path.parent.mkdir(parents=True)
            config_path.write_text(sample_config_yaml)

            result = runner.invoke(cli, ['agent', 'list'])

            assert result.exit_code == 0
            assert 'business-analyst' in result.output

    def test_agent_list_shows_enabled_status(self, sample_config_yaml):
        """Test that list shows enabled/disabled status."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            config_path = Path('.claude/config.yaml')
            config_path.parent.mkdir(parents=True)
            config_path.write_text(sample_config_yaml)

            result = runner.invoke(cli, ['agent', 'list'])

            # Should show enabled/disabled markers
            assert '✓' in result.output or 'enabled' in result.output.lower()


@pytest.mark.integration
class TestAgentRenderCommand:
    """Test suite for cwf agent render command."""

    def test_render_agent_success(self, sample_config_yaml):
        """Test rendering a single agent."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Create config
            config_path = Path('.claude/config.yaml')
            config_path.parent.mkdir(parents=True)
            config_path.write_text(sample_config_yaml)

            result = runner.invoke(cli, ['agent', 'render', 'business-analyst'])

            assert result.exit_code == 0
            assert 'Test Project' in result.output  # Project name substituted

    def test_render_agent_to_file(self, sample_config_yaml):
        """Test rendering agent to file."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Create config
            config_path = Path('.claude/config.yaml')
            config_path.parent.mkdir(parents=True)
            config_path.write_text(sample_config_yaml)

            # Create output directory
            Path('.claude/agents').mkdir(parents=True)

            result = runner.invoke(cli, [
                'agent', 'render', 'business-analyst',
                '-o', '.claude/agents/business-analyst.md'
            ])

            assert result.exit_code == 0
            assert Path('.claude/agents/business-analyst.md').exists()

            content = Path('.claude/agents/business-analyst.md').read_text()
            assert 'Test Project' in content

    def test_render_nonexistent_agent(self, sample_config_yaml):
        """Test rendering non-existent agent fails."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            config_path = Path('.claude/config.yaml')
            config_path.parent.mkdir(parents=True)
            config_path.write_text(sample_config_yaml)

            result = runner.invoke(cli, ['agent', 'render', 'nonexistent-agent'])

            assert result.exit_code != 0
            assert 'not found' in result.output.lower()

    def test_render_all_agents(self, sample_config_yaml):
        """Test rendering all enabled agents."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            config_path = Path('.claude/config.yaml')
            config_path.parent.mkdir(parents=True)
            config_path.write_text(sample_config_yaml)

            # Create output directory
            Path('.claude/agents').mkdir(parents=True)

            result = runner.invoke(cli, [
                'agent', 'render-all',
                '-o', '.claude/agents'
            ])

            assert result.exit_code == 0
            # Should create files for enabled agents
            assert Path('.claude/agents/business-analyst.md').exists()


@pytest.mark.integration
class TestAgentEnableDisable:
    """Test suite for agent enable/disable commands."""

    def test_enable_agent(self, sample_config_yaml):
        """Test enabling an agent."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            config_path = Path('.claude/config.yaml')
            config_path.parent.mkdir(parents=True)
            config_path.write_text(sample_config_yaml)

            result = runner.invoke(cli, ['agent', 'enable', 'project-architect'])

            assert result.exit_code == 0

            # Verify agent is now enabled in config
            from config.loader import ConfigLoader
            loader = ConfigLoader(config_path)
            config = loader.load()
            assert 'project-architect' in config.agent_config.enabled_agents

    def test_disable_agent(self, sample_config_yaml):
        """Test disabling an agent."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            config_path = Path('.claude/config.yaml')
            config_path.parent.mkdir(parents=True)
            config_path.write_text(sample_config_yaml)

            result = runner.invoke(cli, ['agent', 'disable', 'business-analyst'])

            assert result.exit_code == 0

            # Verify agent is now disabled in config
            from config.loader import ConfigLoader
            loader = ConfigLoader(config_path)
            config = loader.load()
            assert 'business-analyst' not in config.agent_config.enabled_agents

    def test_enable_nonexistent_agent(self, sample_config_yaml):
        """Test enabling non-existent agent fails."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            config_path = Path('.claude/config.yaml')
            config_path.parent.mkdir(parents=True)
            config_path.write_text(sample_config_yaml)

            result = runner.invoke(cli, ['agent', 'enable', 'nonexistent-agent'])

            assert result.exit_code != 0
            assert 'not found' in result.output.lower() or 'invalid' in result.output.lower()

    def test_enable_all_agents(self, sample_config_yaml):
        """Test enabling all agents with 'all' argument."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            config_path = Path('.claude/config.yaml')
            config_path.parent.mkdir(parents=True)
            config_path.write_text(sample_config_yaml)

            result = runner.invoke(cli, ['agent', 'enable', 'all'])

            assert result.exit_code == 0
            assert 'Enabled' in result.output

            # Verify all agents are now enabled in config
            from config.loader import ConfigLoader
            loader = ConfigLoader(config_path)
            config = loader.load()
            # Should have more than the default 3 agents
            assert len(config.agent_config.enabled_agents) >= 10


@pytest.mark.integration
class TestAgentRenderAll:
    """Test suite for agent render all command."""

    def test_render_all_with_all_argument(self, sample_config_yaml):
        """Test rendering all agents using 'all' argument."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            config_path = Path('.claude/config.yaml')
            config_path.parent.mkdir(parents=True)
            config_path.write_text(sample_config_yaml)

            # First enable all agents
            runner.invoke(cli, ['agent', 'enable', 'all'])

            # Create output directory
            Path('.claude/agents').mkdir(parents=True)

            # Render all using the render command with 'all' argument
            result = runner.invoke(cli, ['agent', 'render', 'all', '-o', '.claude/agents'])

            assert result.exit_code == 0
            assert 'Rendering' in result.output or '✓' in result.output

            # Verify files were created
            agent_files = list(Path('.claude/agents').glob('*.md'))
            assert len(agent_files) >= 10
