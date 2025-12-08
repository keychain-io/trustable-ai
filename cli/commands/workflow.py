"""
Workflow command - manage workflows (list, render, run).
"""
import click
from pathlib import Path
from typing import Optional

from config import load_config
from workflows import WorkflowRegistry


@click.group(name="workflow")
def workflow_command():
    """Manage workflows (render templates for use with Claude Code)."""
    pass


@workflow_command.command(name="list")
def list_workflows():
    """List available workflows."""
    try:
        config = load_config()
        registry = WorkflowRegistry(config)

        workflows = registry.list_workflows()

        click.echo("\n📋 Available workflows:")
        for workflow in workflows:
            click.echo(f"  • {workflow}")

        click.echo(f"\nTotal: {len(workflows)} workflows\n")

    except FileNotFoundError as e:
        click.echo(f"❌ Error: {e}")
        click.echo("Run 'trustable-ai init' to initialize the framework.")


@workflow_command.command(name="render")
@click.argument("workflow_name")
@click.option("--output", "-o", type=click.Path(), help="Output file path")
@click.option("--show", is_flag=True, help="Show rendered output")
def render_workflow(workflow_name: str, output: Optional[str], show: bool):
    """Render a workflow template."""
    try:
        config = load_config()
        registry = WorkflowRegistry(config)

        # Render workflow
        rendered = registry.render_workflow(workflow_name)

        # Save to file if requested
        if output:
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(rendered, encoding='utf-8')
            click.echo(f"✅ Rendered workflow saved to {output_path}")

        # Show output if requested
        if show or not output:
            click.echo(f"\n{'='*80}")
            click.echo(f"Workflow: {workflow_name}")
            click.echo('='*80)
            click.echo(rendered)
            click.echo('='*80)

    except ValueError as e:
        click.echo(f"❌ Error: {e}")
    except FileNotFoundError as e:
        click.echo(f"❌ Error: {e}")


@workflow_command.command(name="render-all")
@click.option("--output-dir", "-o", type=click.Path(), default=".claude/commands", help="Output directory")
def render_all_workflows(output_dir: str):
    """Render all workflows."""
    try:
        config = load_config()
        registry = WorkflowRegistry(config)

        output_path = Path(output_dir)
        workflows = registry.list_workflows()

        click.echo(f"\n📝 Rendering {len(workflows)} workflows to {output_path}\n")

        for workflow_name in workflows:
            output_file = registry.save_rendered_workflow(workflow_name, output_path)
            click.echo(f"  ✓ {workflow_name} → {output_file}")

        click.echo(f"\n✅ All workflows rendered successfully.\n")

    except FileNotFoundError as e:
        click.echo(f"❌ Error: {e}")


@workflow_command.command(name="run")
@click.argument("workflow_name")
@click.option("--dry-run", is_flag=True, help="Show workflow without executing")
def run_workflow(workflow_name: str, dry_run: bool):
    """
    Run a workflow (NOT YET IMPLEMENTED - use 'render' instead).

    Automatic workflow execution is planned for a future release.
    Currently, use 'trustable-ai workflow render' to generate workflow instructions
    that you can provide to Claude Code manually.
    """
    click.echo(f"\n🚀 Running workflow: {workflow_name}")

    if dry_run:
        try:
            config = load_config()
            registry = WorkflowRegistry(config)
            rendered = registry.render_workflow(workflow_name)

            click.echo("\n📄 Workflow Definition (dry-run):")
            click.echo('='*80)
            click.echo(rendered)
            click.echo('='*80)

        except Exception as e:
            click.echo(f"❌ Error: {e}")
    else:
        click.echo("\n⚠️  Workflow execution engine is not yet implemented.")
        click.echo("\n📝 To use this workflow:")
        click.echo(f"   1. Render it: trustable-ai workflow render {workflow_name} --show")
        click.echo("   2. Copy the instructions")
        click.echo("   3. Provide them to Claude Code\n")
        click.echo("Automatic execution will be available in a future release.\n")
