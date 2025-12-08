"""
Unit tests for Workflow Registry.

Tests the workflow template rendering system.
"""
import pytest
from pathlib import Path

from workflows.registry import WorkflowRegistry, load_workflow, list_workflows
from config.schema import FrameworkConfig


@pytest.mark.unit
class TestWorkflowRegistry:
    """Test suite for WorkflowRegistry class."""

    def test_init_with_config(self, sample_framework_config):
        """Test registry initialization with configuration."""
        registry = WorkflowRegistry(sample_framework_config)

        assert registry.config == sample_framework_config
        assert registry.templates_dir.exists()
        assert registry.env is not None

    def test_list_workflows(self, sample_framework_config):
        """Test listing available workflow templates."""
        registry = WorkflowRegistry(sample_framework_config)
        workflows = registry.list_workflows()

        assert isinstance(workflows, list)
        assert len(workflows) > 0
        assert "sprint-planning" in workflows

    def test_list_workflows_sorted(self, sample_framework_config):
        """Test that workflows are returned in sorted order."""
        registry = WorkflowRegistry(sample_framework_config)
        workflows = registry.list_workflows()

        assert workflows == sorted(workflows)

    def test_render_sprint_planning(self, sample_framework_config):
        """Test rendering sprint planning workflow."""
        registry = WorkflowRegistry(sample_framework_config)
        rendered = registry.render_workflow("sprint-planning")

        assert isinstance(rendered, str)
        assert len(rendered) > 1000  # Should be substantial

        # Check project name is substituted
        assert "Test Project" in rendered

        # Check work item types are substituted
        assert "Feature" in rendered or "Epic" in rendered

        # Check enabled agents are mentioned
        assert "business-analyst" in rendered or "Business Analyst" in rendered

    def test_render_workflow_includes_config(self, sample_framework_config):
        """Test that rendered workflow includes configuration details."""
        registry = WorkflowRegistry(sample_framework_config)
        rendered = registry.render_workflow("sprint-planning")

        # Check quality standards are included
        assert "80" in rendered  # test coverage

        # Check work tracking platform
        assert "azure-devops" in rendered

        # Check sprint naming pattern
        assert "Sprint" in rendered

    def test_render_workflow_with_enabled_agents_only(self, sample_framework_config):
        """Test that only enabled agents appear in workflow."""
        # Modify config to disable some agents
        sample_framework_config.agent_config.enabled_agents = ["senior-engineer"]

        registry = WorkflowRegistry(sample_framework_config)
        rendered = registry.render_workflow("sprint-planning")

        # Should still work with just one agent
        assert "senior-engineer" in rendered.lower()

    def test_render_nonexistent_workflow(self, sample_framework_config):
        """Test rendering a non-existent workflow raises ValueError."""
        registry = WorkflowRegistry(sample_framework_config)

        with pytest.raises(ValueError, match="not found"):
            registry.render_workflow("nonexistent-workflow")

    def test_save_rendered_workflow(self, sample_framework_config, temp_dir):
        """Test saving rendered workflow to file."""
        registry = WorkflowRegistry(sample_framework_config)

        output_file = registry.save_rendered_workflow("sprint-planning", temp_dir)

        assert output_file.exists()
        assert output_file.name == "sprint-planning.md"
        assert len(output_file.read_text()) > 1000

    def test_build_context(self, sample_framework_config):
        """Test building template context from configuration."""
        registry = WorkflowRegistry(sample_framework_config)
        context = registry._build_context()

        assert isinstance(context, dict)

        # Check all major sections are present
        assert "project" in context
        assert "work_tracking" in context
        assert "quality_standards" in context
        assert "agent_config" in context
        assert "workflow_config" in context
        assert "deployment_config" in context
        assert "tech_stack_context" in context

        # Check workflow config details
        assert context["workflow_config"]["checkpoint_enabled"] is True
        assert context["workflow_config"]["verification_enabled"] is True

        # Check deployment config details
        assert "dev" in context["deployment_config"]["environments"]

    def test_render_with_additional_context(self, sample_framework_config):
        """Test rendering with additional context variables."""
        registry = WorkflowRegistry(sample_framework_config)

        additional_context = {"custom_var": "custom_value"}
        rendered = registry.render_workflow("sprint-planning", additional_context)

        assert isinstance(rendered, str)
        assert len(rendered) > 0


@pytest.mark.unit
class TestWorkflowRegistryConvenienceFunctions:
    """Test convenience functions for workflow registry."""

    def test_list_workflows_function(self):
        """Test list_workflows convenience function."""
        workflows = list_workflows()

        assert isinstance(workflows, list)
        assert len(workflows) > 0

    def test_list_workflows_with_custom_dir(self, temp_dir):
        """Test list_workflows with custom templates directory."""
        # Create a dummy template
        (temp_dir / "test-workflow.j2").write_text("# Test Workflow")

        workflows = list_workflows(temp_dir)

        assert "test-workflow" in workflows


@pytest.mark.unit
class TestWorkflowRegistryEdgeCases:
    """Test edge cases and error handling."""

    def test_minimal_config(self, minimal_framework_config):
        """Test with minimal configuration."""
        registry = WorkflowRegistry(minimal_framework_config)
        workflows = registry.list_workflows()

        assert len(workflows) > 0

    def test_render_all_available_workflows(self, sample_framework_config):
        """Test that all available workflows can be rendered without errors."""
        registry = WorkflowRegistry(sample_framework_config)

        for workflow_name in registry.list_workflows():
            rendered = registry.render_workflow(workflow_name)
            assert isinstance(rendered, str)
            assert len(rendered) > 0

    def test_templates_directory_doesnt_exist(self, sample_framework_config, temp_dir):
        """Test behavior when templates directory doesn't exist."""
        nonexistent_dir = temp_dir / "nonexistent"

        registry = WorkflowRegistry(sample_framework_config, nonexistent_dir)
        workflows = registry.list_workflows()

        # Should return empty list, not crash
        assert workflows == []

    def test_workflow_includes_all_enabled_agents(self, sample_framework_config):
        """Test that workflow correctly reflects enabled agents configuration."""
        # Enable all agents
        sample_framework_config.agent_config.enabled_agents = [
            "business-analyst",
            "senior-engineer",
            "scrum-master",
            "architect",
            "security-specialist",
        ]

        registry = WorkflowRegistry(sample_framework_config)
        rendered = registry.render_workflow("sprint-planning")

        # All agents should be mentioned in workflow
        for agent in sample_framework_config.agent_config.enabled_agents:
            # Agent name should appear in the workflow
            assert agent in rendered.lower() or agent.replace("-", " ") in rendered.lower()
