"""
Main CLI entry point for Trustable AI.

Provides commands for initializing, configuring, and managing AI-assisted
software development workflows.
"""
import click
from pathlib import Path
try:
    from importlib.metadata import version
except ImportError:
    from importlib_metadata import version  # Python 3.7 compatibility


@click.group()
@click.version_option(version=version("trustable-ai"), prog_name="trustable-ai")
def cli():
    """
    Trustable AI - AI-assisted software lifecycle automation.

    Initialize, configure, and manage multi-agent workflows for software development
    with Claude Code integration.

    Get started:

      trustable-ai init              Initialize Trustable AI in your project

      trustable-ai agent list        List available agents

      trustable-ai workflow list     List available workflows

      trustable-ai doctor            Check configuration health
    """
    pass


# Import commands
from .commands import init, configure, agent, workflow, validate
from .commands import doctor, status, learnings, context, skill, permissions

# Register core commands
cli.add_command(init.init_command)
cli.add_command(configure.configure_command)
cli.add_command(agent.agent_command)
cli.add_command(workflow.workflow_command)
cli.add_command(validate.validate_command)

# Register new commands
cli.add_command(doctor.doctor)
cli.add_command(status.status)
cli.add_command(learnings.learnings)
cli.add_command(context.context)
cli.add_command(skill.skill)
cli.add_command(permissions.permissions_command)


if __name__ == "__main__":
    cli()
