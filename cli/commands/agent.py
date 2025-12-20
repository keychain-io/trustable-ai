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
        click.echo("Run 'trustable-ai init' to initialize the framework.")


@agent_command.command(name="enable")
@click.argument("agent_name")
def enable_agent(agent_name: str):
    """Enable an agent (use 'all' to enable all agents)."""
    try:
        config = load_config()
        registry = AgentRegistry(config)

        # Handle "all" to enable all agents
        if agent_name.lower() == "all":
            all_agents = registry.list_agents()
            enabled_count = 0
            for agent in all_agents:
                if agent not in config.agent_config.enabled_agents:
                    config.agent_config.enabled_agents.append(agent)
                    enabled_count += 1
                    click.echo(f"  ✓ {agent}")
            save_config(config)
            click.echo(f"\n✅ Enabled {enabled_count} agents ({len(all_agents)} total).")
            return

        # Check if agent exists
        if agent_name not in registry.list_agents():
            click.echo(f"❌ Agent '{agent_name}' not found.")
            click.echo(f"Available agents: {', '.join(registry.list_agents())}")
            raise SystemExit(1)

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
@click.option("--output", "-o", type=click.Path(), help="Output file path (or directory if rendering all)")
@click.option("--show", is_flag=True, help="Show rendered output")
def render_agent(agent_name: str, output: Optional[str], show: bool):
    """Render an agent template (use 'all' to render all enabled agents)."""
    try:
        config = load_config()
        registry = AgentRegistry(config)

        # Handle "all" to render all enabled agents
        if agent_name.lower() == "all":
            output_path = Path(output) if output else Path(".claude/agents")
            enabled_agents = registry.get_enabled_agents()

            click.echo(f"\n📝 Rendering {len(enabled_agents)} agents to {output_path}\n")

            for agent in enabled_agents:
                output_file = registry.save_rendered_agent(agent, output_path)
                click.echo(f"  ✓ {agent} → {output_file}")

            click.echo(f"\n✅ All agents rendered successfully.\n")
            return

        # Render agent
        rendered = registry.render_agent(agent_name)

        # Save to file if requested
        if output:
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(rendered, encoding='utf-8')
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
        raise SystemExit(1)
    except FileNotFoundError as e:
        click.echo(f"❌ Error: {e}")
        raise SystemExit(1)


@agent_command.command(name="render-all")
@click.option("--output-dir", "-o", type=click.Path(), default=".claude/agents", help="Output directory")
@click.option("--with-commands", is_flag=True, help="Also render agent slash commands to .claude/commands")
def render_all_agents(output_dir: str, with_commands: bool):
    """Render all available agents (regardless of enabled status)."""
    try:
        config = load_config()
        registry = AgentRegistry(config)

        output_path = Path(output_dir)
        all_agents = registry.list_agents()

        click.echo(f"\n📝 Rendering {len(all_agents)} agents to {output_path}\n")

        for agent_name in all_agents:
            try:
                output_file = registry.save_rendered_agent(agent_name, output_path)
                click.echo(f"  ✓ {agent_name} → {output_file}")
            except Exception as e:
                click.echo(f"  ✗ {agent_name}: {type(e).__name__}: {e}")
                raise

        click.echo(f"\n✅ All agents rendered successfully.\n")

        # Also render slash commands if requested
        if with_commands:
            commands_dir = Path(".claude/commands")
            click.echo(f"📝 Rendering agent slash commands to {commands_dir}\n")

            for agent_name in all_agents:
                try:
                    output_file = registry.save_agent_slash_command(agent_name, commands_dir)
                    click.echo(f"  ✓ /{agent_name} → {output_file}")
                except Exception as e:
                    click.echo(f"  ✗ /{agent_name}: {type(e).__name__}: {e}")
                    raise

            click.echo(f"\n✅ Agent slash commands rendered successfully.\n")

    except FileNotFoundError as e:
        click.echo(f"❌ Error: {e}")
        raise SystemExit(1)
    except Exception as e:
        click.echo(f"❌ Error: {type(e).__name__}: {e}")
        raise SystemExit(1)


@agent_command.command(name="render-commands")
@click.option("--output-dir", "-o", type=click.Path(), default=".claude/commands", help="Output directory")
def render_agent_commands(output_dir: str):
    """Render slash commands for all enabled agents."""
    try:
        config = load_config()
        registry = AgentRegistry(config)

        output_path = Path(output_dir)
        enabled_agents = registry.get_enabled_agents()

        click.echo(f"\n📝 Rendering {len(enabled_agents)} agent slash commands to {output_path}\n")

        for agent_name in enabled_agents:
            output_file = registry.save_agent_slash_command(agent_name, output_path)
            click.echo(f"  ✓ /{agent_name} → {output_file}")

        click.echo(f"\n✅ Agent slash commands rendered successfully.\n")
        click.echo("Use these slash commands in Claude Code to spawn agents with fresh context:")
        for agent_name in enabled_agents[:5]:
            click.echo(f"  /{agent_name}")
        if len(enabled_agents) > 5:
            click.echo(f"  ... and {len(enabled_agents) - 5} more")

    except FileNotFoundError as e:
        click.echo(f"❌ Error: {e}")
