"""
Main CLI entry point for Claude Workflow Framework.

Provides commands for initializing, configuring, and managing workflows.
"""
import click
from pathlib import Path


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Claude Workflow Framework - AI-powered workflow automation."""
    pass


# Import commands
from .commands import init, configure, agent, workflow, validate

# Register commands
cli.add_command(init.init_command)
cli.add_command(configure.configure_command)
cli.add_command(agent.agent_command)
cli.add_command(workflow.workflow_command)
cli.add_command(validate.validate_command)


if __name__ == "__main__":
    cli()
