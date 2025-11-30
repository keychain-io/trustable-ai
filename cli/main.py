"""
Main CLI entry point for Trusted AI Development (TAID).

Provides commands for initializing, configuring, and managing AI-assisted
software development workflows.
"""
import click
from pathlib import Path


@click.group()
@click.version_option(version="1.0.0", prog_name="taid")
def cli():
    """
    Trusted AI Development (taid) - AI-assisted software lifecycle automation.

    Initialize, configure, and manage multi-agent workflows for software development
    with Claude Code integration.

    Get started:

      taid init              Initialize TAID in your project

      taid agent list        List available agents

      taid workflow list     List available workflows

      taid doctor            Check configuration health
    """
    pass


# Import commands
from .commands import init, configure, agent, workflow, validate
from .commands import doctor, status, learnings, context, skill

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


if __name__ == "__main__":
    cli()
