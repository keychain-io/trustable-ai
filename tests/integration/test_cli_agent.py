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
            assert 'trustable-ai init' in result.output

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
        """Test rendering all available agents regardless of enabled status."""
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
            # Should create files for ALL available agents, not just enabled ones
            # At minimum, we expect the core agents to be rendered
            assert Path('.claude/agents/business-analyst.md').exists()
            assert Path('.claude/agents/architect.md').exists()
            assert Path('.claude/agents/senior-engineer.md').exists()
            assert Path('.claude/agents/engineer.md').exists()
            assert Path('.claude/agents/tester.md').exists()
            assert Path('.claude/agents/security-specialist.md').exists()
            assert Path('.claude/agents/scrum-master.md').exists()

            # Count rendered agents - should be all non-deprecated agents
            agent_files = list(Path('.claude/agents').glob('*.md'))
            assert len(agent_files) >= 7  # At least the 7 core agents


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

            result = runner.invoke(cli, ['agent', 'enable', 'architect'])

            assert result.exit_code == 0

            # Verify agent is now enabled in config
            from config.loader import ConfigLoader
            loader = ConfigLoader(config_path)
            config = loader.load()
            assert 'architect' in config.agent_config.enabled_agents

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
            # Should have all non-deprecated agents (8 in v2.0)
            assert len(config.agent_config.enabled_agents) >= 8


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

            # Verify files were created (7+ non-deprecated agents in v2.0)
            agent_files = list(Path('.claude/agents').glob('*.md'))
            assert len(agent_files) >= 7

    def test_render_all_renders_disabled_agents(self, sample_config_yaml):
        """Test that render-all renders agents that are NOT enabled (Bug #1077)."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            config_path = Path('.claude/config.yaml')
            config_path.parent.mkdir(parents=True)
            config_path.write_text(sample_config_yaml)

            # Verify the architect agent is NOT in the enabled list initially
            from config.loader import ConfigLoader
            loader = ConfigLoader(config_path)
            config = loader.load()
            assert 'architect' not in config.agent_config.enabled_agents

            # Create output directory
            Path('.claude/agents').mkdir(parents=True)

            # Run render-all command
            result = runner.invoke(cli, ['agent', 'render-all', '-o', '.claude/agents'])

            assert result.exit_code == 0

            # Verify that architect agent was rendered even though it's not enabled
            assert Path('.claude/agents/architect.md').exists()
            assert Path('.claude/agents/engineer.md').exists()
            assert Path('.claude/agents/tester.md').exists()

            # Verify we rendered ALL available agents, not just enabled ones
            from agents import AgentRegistry
            registry = AgentRegistry(config)
            all_available = registry.list_agents()

            # Check that all available agents were rendered
            for agent_name in all_available:
                agent_file = Path(f'.claude/agents/{agent_name}.md')
                assert agent_file.exists(), f"Agent {agent_name} should be rendered but file doesn't exist"
