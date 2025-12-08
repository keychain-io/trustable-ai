"""
Unit tests for Agent Registry.

Tests the agent template rendering system.
"""
import pytest
from pathlib import Path

from agents.registry import AgentRegistry, load_agent, list_agents
from config.schema import FrameworkConfig


@pytest.mark.unit
class TestAgentRegistry:
    """Test suite for AgentRegistry class."""

    def test_init_with_config(self, sample_framework_config):
        """Test registry initialization with configuration."""
        registry = AgentRegistry(sample_framework_config)

        assert registry.config == sample_framework_config
        assert registry.templates_dir.exists()
        assert registry.env is not None

    def test_list_agents(self, sample_framework_config):
        """Test listing available agent templates."""
        registry = AgentRegistry(sample_framework_config)
        agents = registry.list_agents()

        assert isinstance(agents, list)
        assert len(agents) > 0
        assert "business-analyst" in agents
        assert "senior-engineer" in agents
        assert "scrum-master" in agents
        assert "architect" in agents
        assert "security-specialist" in agents

    def test_list_agents_sorted(self, sample_framework_config):
        """Test that agents are returned in sorted order."""
        registry = AgentRegistry(sample_framework_config)
        agents = registry.list_agents()

        assert agents == sorted(agents)

    def test_render_agent_business_analyst(self, sample_framework_config):
        """Test rendering business analyst agent."""
        registry = AgentRegistry(sample_framework_config)
        rendered = registry.render_agent("business-analyst")

        assert isinstance(rendered, str)
        assert len(rendered) > 0

        # Check project name is substituted
        assert "Test Project" in rendered

        # Check model configuration is substituted
        assert "claude-sonnet-4.5" in rendered or "sonnet" in rendered.lower()

        # Check work item types are substituted
        assert "Epic" in rendered
        assert "Feature" in rendered
        assert "User Story" in rendered

    def test_render_agent_senior_engineer(self, sample_framework_config):
        """Test rendering senior engineer agent."""
        registry = AgentRegistry(sample_framework_config)
        rendered = registry.render_agent("senior-engineer")

        assert isinstance(rendered, str)
        assert len(rendered) > 500  # Should be substantial

        # Check tech stack context is included
        assert "Python" in rendered or "TypeScript" in rendered

        # Check quality standards are substituted
        assert "80" in rendered  # test coverage minimum

        # Check work item types
        assert "Feature" in rendered
        assert "Task" in rendered

    def test_render_agent_with_custom_fields(self, sample_framework_config):
        """Test that custom fields are included in rendered agents."""
        registry = AgentRegistry(sample_framework_config)
        rendered = registry.render_agent("business-analyst")

        # Custom fields should be in the output
        assert "Custom.BusinessValueScore" in rendered or "business_value" in rendered

    def test_render_nonexistent_agent(self, sample_framework_config):
        """Test rendering a non-existent agent raises ValueError."""
        registry = AgentRegistry(sample_framework_config)

        with pytest.raises(ValueError, match="not found"):
            registry.render_agent("nonexistent-agent")

    def test_is_agent_enabled(self, sample_framework_config):
        """Test checking if agent is enabled."""
        registry = AgentRegistry(sample_framework_config)

        assert registry.is_agent_enabled("business-analyst") is True
        assert registry.is_agent_enabled("senior-engineer") is True
        assert registry.is_agent_enabled("nonexistent-agent") is False

    def test_get_enabled_agents(self, sample_framework_config):
        """Test getting list of enabled agents."""
        registry = AgentRegistry(sample_framework_config)
        enabled = registry.get_enabled_agents()

        assert isinstance(enabled, list)
        assert "business-analyst" in enabled
        assert "senior-engineer" in enabled

    def test_save_rendered_agent(self, sample_framework_config, temp_dir):
        """Test saving rendered agent to file."""
        registry = AgentRegistry(sample_framework_config)

        output_file = registry.save_rendered_agent("business-analyst", temp_dir)

        assert output_file.exists()
        assert output_file.name == "business-analyst.md"
        assert output_file.read_text()  # File has content

    def test_build_context(self, sample_framework_config):
        """Test building template context from configuration."""
        registry = AgentRegistry(sample_framework_config)
        context = registry._build_context()

        assert isinstance(context, dict)

        # Check project context
        assert context["project"]["name"] == "Test Project"
        assert context["project"]["type"] == "web-application"
        assert "Python" in context["project"]["tech_stack"]["languages"]

        # Check work tracking context
        assert context["work_tracking"]["platform"] == "azure-devops"
        assert context["work_tracking"]["work_item_types"]["epic"] == "Epic"

        # Check quality standards
        assert context["quality_standards"]["test_coverage_min"] == 80

        # Check tech stack context text
        assert "tech_stack_context" in context
        assert "Python" in context["tech_stack_context"]

    def test_render_with_additional_context(self, sample_framework_config):
        """Test rendering with additional context variables."""
        registry = AgentRegistry(sample_framework_config)

        additional_context = {"custom_var": "custom_value"}
        rendered = registry.render_agent("business-analyst", additional_context)

        assert isinstance(rendered, str)
        assert len(rendered) > 0


@pytest.mark.unit
class TestAgentRegistryConvenienceFunctions:
    """Test convenience functions for agent registry."""

    def test_list_agents_function(self):
        """Test list_agents convenience function."""
        agents = list_agents()

        assert isinstance(agents, list)
        assert len(agents) > 0

    def test_list_agents_with_custom_dir(self, temp_dir):
        """Test list_agents with custom templates directory."""
        # Create a dummy template
        (temp_dir / "test-agent.j2").write_text("# Test Agent")

        agents = list_agents(temp_dir)

        assert "test-agent" in agents


@pytest.mark.unit
class TestAgentRegistryEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_config(self):
        """Test with minimal configuration."""
        from config.schema import ProjectConfig, WorkTrackingConfig

        minimal_config = FrameworkConfig(
            project=ProjectConfig(
                name="Minimal",
                type="api",
                tech_stack={"languages": ["Python"]},
            ),
            work_tracking=WorkTrackingConfig(
                organization="https://dev.azure.com/test",
                project="Test",
            ),
        )

        registry = AgentRegistry(minimal_config)
        agents = registry.list_agents()

        assert len(agents) > 0

    def test_render_all_available_agents(self, sample_framework_config):
        """Test that all available agents can be rendered without errors."""
        registry = AgentRegistry(sample_framework_config)

        for agent_name in registry.list_agents():
            rendered = registry.render_agent(agent_name)
            assert isinstance(rendered, str)
            assert len(rendered) > 0
            # Verify configuration values appear in rendered output
            assert ("80" in rendered or "claude" in rendered.lower() or "Feature" in rendered or "Epic" in rendered)

    def test_templates_directory_doesnt_exist(self, sample_framework_config, temp_dir):
        """Test behavior when templates directory doesn't exist."""
        nonexistent_dir = temp_dir / "nonexistent"

        registry = AgentRegistry(sample_framework_config, nonexistent_dir)
        agents = registry.list_agents()

        # Should return empty list, not crash
        assert agents == []
