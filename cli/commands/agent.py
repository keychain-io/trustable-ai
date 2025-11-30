"""
Agent command - manage agents (list, enable, disable, render).
"""
import click
from pathlib import Path
from typing import Optional

from config import load_config, save_config
from agents import AgentRegistry


@click.group(name="agent")
def agent_command():
    """Manage workflow agents (render templates for use with Claude Code)."""
    pass


@agent_command.command(name="list")
@click.option("--enabled-only", is_flag=True, help="Show only enabled agents")
def list_agents(enabled_only: bool):
    """List available agents."""
    try:
        config = load_config()
        registry = AgentRegistry(config)

        if enabled_only:
            agents = registry.get_enabled_agents()
            click.echo("\n✅ Enabled agents:")
        else:
            agents = registry.list_agents()
            enabled = set(registry.get_enabled_agents())
            click.echo("\n📋 Available agents:")

        for agent in agents:
            if enabled_only:
                click.echo(f"  • {agent}")
            else:
                status = "✓" if agent in enabled else " "
                click.echo(f"  [{status}] {agent}")

        click.echo()

    except FileNotFoundError as e:
        click.echo(f"❌ Error: {e}")
        click.echo("Run 'taid init' to initialize the framework.")


@agent_command.command(name="enable")
@click.argument("agent_name")
def enable_agent(agent_name: str):
    """Enable an agent."""
    try:
        config = load_config()
        registry = AgentRegistry(config)

        # Check if agent exists
        if agent_name not in registry.list_agents():
            click.echo(f"❌ Agent '{agent_name}' not found.")
            click.echo(f"Available agents: {', '.join(registry.list_agents())}")
            return

        # Check if already enabled
        if agent_name in config.agent_config.enabled_agents:
            click.echo(f"ℹ️  Agent '{agent_name}' is already enabled.")
            return

        # Enable agent
        config.agent_config.enabled_agents.append(agent_name)
        save_config(config)

        click.echo(f"✅ Agent '{agent_name}' enabled.")

    except FileNotFoundError as e:
        click.echo(f"❌ Error: {e}")


@agent_command.command(name="disable")
@click.argument("agent_name")
def disable_agent(agent_name: str):
    """Disable an agent."""
    try:
        config = load_config()

        # Check if agent is enabled
        if agent_name not in config.agent_config.enabled_agents:
            click.echo(f"ℹ️  Agent '{agent_name}' is not enabled.")
            return

        # Disable agent
        config.agent_config.enabled_agents.remove(agent_name)
        save_config(config)

        click.echo(f"✅ Agent '{agent_name}' disabled.")

    except FileNotFoundError as e:
        click.echo(f"❌ Error: {e}")


@agent_command.command(name="render")
@click.argument("agent_name")
@click.option("--output", "-o", type=click.Path(), help="Output file path")
@click.option("--show", is_flag=True, help="Show rendered output")
def render_agent(agent_name: str, output: Optional[str], show: bool):
    """Render an agent template."""
    try:
        config = load_config()
        registry = AgentRegistry(config)

        # Render agent
        rendered = registry.render_agent(agent_name)

        # Save to file if requested
        if output:
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(rendered)
            click.echo(f"✅ Rendered agent saved to {output_path}")

        # Show output if requested
        if show or not output:
            click.echo(f"\n{'='*80}")
            click.echo(f"Agent: {agent_name}")
            click.echo('='*80)
            click.echo(rendered)
            click.echo('='*80)

    except ValueError as e:
        click.echo(f"❌ Error: {e}")
    except FileNotFoundError as e:
        click.echo(f"❌ Error: {e}")


@agent_command.command(name="render-all")
@click.option("--output-dir", "-o", type=click.Path(), default=".claude/agents", help="Output directory")
def render_all_agents(output_dir: str):
    """Render all enabled agents."""
    try:
        config = load_config()
        registry = AgentRegistry(config)

        output_path = Path(output_dir)
        enabled_agents = registry.get_enabled_agents()

        click.echo(f"\n📝 Rendering {len(enabled_agents)} agents to {output_path}\n")

        for agent_name in enabled_agents:
            output_file = registry.save_rendered_agent(agent_name, output_path)
            click.echo(f"  ✓ {agent_name} → {output_file}")

        click.echo(f"\n✅ All agents rendered successfully.\n")

    except FileNotFoundError as e:
        click.echo(f"❌ Error: {e}")
