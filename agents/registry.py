"""
Agent registry and template rendering system.

Loads and renders agent templates with project-specific configuration.
"""
from pathlib import Path
from typing import Dict, Any, List, Optional
from jinja2 import Environment, FileSystemLoader, Template, TemplateNotFound

from config import FrameworkConfig


class AgentRegistry:
    """Registry for managing and rendering agent templates."""

    def __init__(self, config: FrameworkConfig, templates_dir: Optional[Path] = None):
        """
        Initialize the agent registry.

        Args:
            config: Framework configuration
            templates_dir: Directory containing agent templates (defaults to agents/templates)
        """
        self.config = config

        if templates_dir is None:
            # Default to package templates directory
            templates_dir = Path(__file__).parent / "templates"

        self.templates_dir = Path(templates_dir)

        # Setup Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def _build_context(self) -> Dict[str, Any]:
        """
        Build template context from configuration.

        Returns:
            Dictionary of context variables for template rendering
        """
        # Build tech stack context text
        tech_stack_parts = []
        tech_stack_parts.append(f"**Project Type**: {self.config.project.type}")

        if self.config.project.tech_stack.get("languages"):
            langs = ", ".join(self.config.project.tech_stack["languages"])
            tech_stack_parts.append(f"**Languages**: {langs}")

        if self.config.project.tech_stack.get("frameworks"):
            frameworks = ", ".join(self.config.project.tech_stack["frameworks"])
            tech_stack_parts.append(f"**Frameworks**: {frameworks}")

        if self.config.project.tech_stack.get("platforms"):
            platforms = ", ".join(self.config.project.tech_stack["platforms"])
            tech_stack_parts.append(f"**Platforms**: {platforms}")

        if self.config.project.tech_stack.get("databases"):
            databases = ", ".join(self.config.project.tech_stack["databases"])
            tech_stack_parts.append(f"**Databases**: {databases}")

        tech_stack_context = "\n".join(tech_stack_parts)

        # Build template context
        return {
            "project": {
                "name": self.config.project.name,
                "type": self.config.project.type,
                "tech_stack": self.config.project.tech_stack,
                "source_directory": self.config.project.source_directory,
                "test_directory": self.config.project.test_directory,
            },
            "work_tracking": {
                "platform": self.config.work_tracking.platform,
                "organization": self.config.work_tracking.organization,
                "project": self.config.work_tracking.project,
                "work_item_types": self.config.work_tracking.work_item_types,
                "sprint_naming": self.config.work_tracking.sprint_naming,
                "iteration_format": self.config.work_tracking.iteration_format,
            },
            "custom_fields": self.config.work_tracking.custom_fields,
            "quality_standards": {
                "test_coverage_min": self.config.quality_standards.test_coverage_min,
                "critical_vulnerabilities_max": self.config.quality_standards.critical_vulnerabilities_max,
                "high_vulnerabilities_max": self.config.quality_standards.high_vulnerabilities_max,
                "medium_vulnerabilities_max": self.config.quality_standards.medium_vulnerabilities_max,
                "code_complexity_max": self.config.quality_standards.code_complexity_max,
                "duplicate_code_max": self.config.quality_standards.duplicate_code_max,
                "build_time_max_minutes": self.config.quality_standards.build_time_max_minutes,
                "test_time_max_minutes": self.config.quality_standards.test_time_max_minutes,
            },
            "agent_config": {
                "models": self.config.agent_config.models,
                "enabled_agents": self.config.agent_config.enabled_agents,
            },
            "tech_stack_context": tech_stack_context,
        }

    def render_agent(self, agent_name: str, additional_context: Optional[Dict[str, Any]] = None) -> str:
        """
        Render an agent template.

        Args:
            agent_name: Agent name (without .j2 extension)
            additional_context: Additional context variables to merge

        Returns:
            Rendered agent definition

        Raises:
            TemplateNotFound: If agent template doesn't exist
        """
        # Load template
        template_name = f"{agent_name}.j2"
        try:
            template = self.env.get_template(template_name)
        except TemplateNotFound:
            raise ValueError(
                f"Agent template '{agent_name}' not found in {self.templates_dir}. "
                f"Available agents: {', '.join(self.list_agents())}"
            )

        # Build context
        context = self._build_context()

        # Merge additional context if provided
        if additional_context:
            context.update(additional_context)

        # Render template
        return template.render(**context)

    def list_agents(self) -> List[str]:
        """
        List available agent templates.

        Returns:
            List of agent names (without .j2 extension)
        """
        if not self.templates_dir.exists():
            return []

        agents = []
        for template_file in self.templates_dir.glob("*.j2"):
            agent_name = template_file.stem  # Remove .j2 extension
            agents.append(agent_name)

        return sorted(agents)

    def is_agent_enabled(self, agent_name: str) -> bool:
        """
        Check if an agent is enabled in configuration.

        Args:
            agent_name: Agent name

        Returns:
            True if agent is enabled
        """
        return agent_name in self.config.agent_config.enabled_agents

    def get_enabled_agents(self) -> List[str]:
        """
        Get list of enabled agents.

        Returns:
            List of enabled agent names
        """
        available = set(self.list_agents())
        enabled = [
            agent
            for agent in self.config.agent_config.enabled_agents
            if agent in available
        ]
        return enabled

    def save_rendered_agent(self, agent_name: str, output_dir: Path) -> Path:
        """
        Render and save an agent to a file.

        Args:
            agent_name: Agent name
            output_dir: Directory to save rendered agent

        Returns:
            Path to saved agent file
        """
        rendered = self.render_agent(agent_name)

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / f"{agent_name}.md"
        output_file.write_text(rendered)

        return output_file


# Convenience functions

def load_agent(agent_name: str, config: Optional[FrameworkConfig] = None) -> str:
    """
    Quick helper to render an agent.

    Args:
        agent_name: Agent name
        config: Framework configuration (loads from .claude/config.yaml if not provided)

    Returns:
        Rendered agent definition
    """
    if config is None:
        from config import load_config
        config = load_config()

    registry = AgentRegistry(config)
    return registry.render_agent(agent_name)


def list_agents(templates_dir: Optional[Path] = None) -> List[str]:
    """
    Quick helper to list available agents.

    Args:
        templates_dir: Templates directory (uses default if not provided)

    Returns:
        List of agent names
    """
    # Create minimal config for registry
    from config.schema import (
        FrameworkConfig,
        ProjectConfig,
        WorkTrackingConfig,
    )

    minimal_config = FrameworkConfig(
        project=ProjectConfig(
            name="temp",
            type="web-application",
            tech_stack={"languages": ["Python"]},
        ),
        work_tracking=WorkTrackingConfig(
            organization="https://dev.azure.com/org",
            project="Project",
        ),
    )

    registry = AgentRegistry(minimal_config, templates_dir)
    return registry.list_agents()


def render_agent(
    agent_name: str,
    config: Optional[FrameworkConfig] = None,
    output_file: Optional[Path] = None,
) -> str:
    """
    Render an agent and optionally save to file.

    Args:
        agent_name: Agent name
        config: Framework configuration
        output_file: Optional path to save rendered agent

    Returns:
        Rendered agent definition
    """
    if config is None:
        from config import load_config
        config = load_config()

    registry = AgentRegistry(config)
    rendered = registry.render_agent(agent_name)

    if output_file:
        output_file = Path(output_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(rendered)

    return rendered
