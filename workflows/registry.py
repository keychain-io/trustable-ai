"""
Workflow registry and template rendering system.

Loads and renders workflow templates with project-specific configuration.
"""
from pathlib import Path
from typing import Dict, Any, List, Optional
from jinja2 import Environment, FileSystemLoader, Template, TemplateNotFound

from config import FrameworkConfig


class WorkflowRegistry:
    """Registry for managing and rendering workflow templates."""

    def __init__(self, config: FrameworkConfig, templates_dir: Optional[Path] = None):
        """
        Initialize the workflow registry.

        Args:
            config: Framework configuration
            templates_dir: Directory containing workflow templates (defaults to workflows/templates)
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
        # Build tech stack context text (same as agents)
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
                "custom_fields": self.config.work_tracking.custom_fields,
            },
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
            "workflow_config": {
                "state_directory": self.config.workflow_config.state_directory,
                "profiling_directory": self.config.workflow_config.profiling_directory,
                "checkpoint_enabled": self.config.workflow_config.checkpoint_enabled,
                "verification_enabled": self.config.workflow_config.verification_enabled,
                "max_retries": self.config.workflow_config.max_retries,
                "timeout_minutes": self.config.workflow_config.timeout_minutes,
            },
            "deployment_config": {
                "environments": self.config.deployment_config.environments,
                "default_environment": self.config.deployment_config.default_environment,
                "deployment_tasks_enabled": self.config.deployment_config.deployment_tasks_enabled,
                "deployment_task_types": self.config.deployment_config.deployment_task_types,
            },
            "tech_stack_context": tech_stack_context,
            "config": self.config,  # Provide full config object for complex template logic
        }

    def render_workflow(self, workflow_name: str, additional_context: Optional[Dict[str, Any]] = None) -> str:
        """
        Render a workflow template.

        Args:
            workflow_name: Workflow name (without .j2 extension)
            additional_context: Additional context variables to merge

        Returns:
            Rendered workflow definition

        Raises:
            TemplateNotFound: If workflow template doesn't exist
        """
        # Load template
        template_name = f"{workflow_name}.j2"
        try:
            template = self.env.get_template(template_name)
        except TemplateNotFound:
            raise ValueError(
                f"Workflow template '{workflow_name}' not found in {self.templates_dir}. "
                f"Available workflows: {', '.join(self.list_workflows())}"
            )

        # Build context
        context = self._build_context()

        # Merge additional context if provided
        if additional_context:
            context.update(additional_context)

        # Render template
        return template.render(**context)

    def list_workflows(self) -> List[str]:
        """
        List available workflow templates.

        Returns:
            List of workflow names (without .j2 extension)
        """
        if not self.templates_dir.exists():
            return []

        workflows = []
        for template_file in self.templates_dir.glob("*.j2"):
            workflow_name = template_file.stem  # Remove .j2 extension
            workflows.append(workflow_name)

        return sorted(workflows)

    def save_rendered_workflow(self, workflow_name: str, output_dir: Path) -> Path:
        """
        Render and save a workflow to a file.

        Args:
            workflow_name: Workflow name
            output_dir: Directory to save rendered workflow

        Returns:
            Path to saved workflow file
        """
        rendered = self.render_workflow(workflow_name)

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / f"{workflow_name}.md"
        output_file.write_text(rendered, encoding='utf-8')

        return output_file


# Convenience functions

def load_workflow(workflow_name: str, config: Optional[FrameworkConfig] = None) -> str:
    """
    Quick helper to render a workflow.

    Args:
        workflow_name: Workflow name
        config: Framework configuration (loads from .claude/config.yaml if not provided)

    Returns:
        Rendered workflow definition
    """
    if config is None:
        from config import load_config
        config = load_config()

    registry = WorkflowRegistry(config)
    return registry.render_workflow(workflow_name)


def list_workflows(templates_dir: Optional[Path] = None) -> List[str]:
    """
    Quick helper to list available workflows.

    Args:
        templates_dir: Templates directory (uses default if not provided)

    Returns:
        List of workflow names
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

    registry = WorkflowRegistry(minimal_config, templates_dir)
    return registry.list_workflows()
