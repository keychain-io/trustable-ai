"""
Initialize command - sets up Claude Workflow Framework in a project.
"""
import click
from pathlib import Path
from typing import Optional
import yaml

from config import create_default_config, save_config
from config.schema import FrameworkConfig


@click.command(name="init")
@click.option("--project-name", prompt="Project name", help="Name of your project")
@click.option(
    "--project-type",
    type=click.Choice([
        "web-application", "api", "mobile-app", "desktop-app",
        "infrastructure", "library", "cli-tool", "microservice"
    ]),
    prompt="Project type",
    help="Type of project"
)
@click.option("--interactive/--no-interactive", default=True, help="Interactive mode")
@click.option("--config-path", type=click.Path(), default=None, help="Custom config path")
def init_command(
    project_name: str,
    project_type: str,
    interactive: bool,
    config_path: Optional[str],
):
    """Initialize Claude Workflow Framework in your project."""

    click.echo("\n🚀 Initializing Claude Workflow Framework\n")

    # Determine config path
    if config_path:
        config_file = Path(config_path)
    else:
        config_file = Path.cwd() / ".claude" / "config.yaml"

    # Check if already initialized
    if config_file.exists():
        if not click.confirm(f"Configuration already exists at {config_file}. Overwrite?"):
            click.echo("Initialization cancelled.")
            return

    # Gather tech stack information
    click.echo("\n📦 Technology Stack")
    tech_stack = {}

    if interactive:
        # Languages
        languages_input = click.prompt(
            "Programming languages (comma-separated)",
            default="Python"
        )
        tech_stack["languages"] = [lang.strip() for lang in languages_input.split(",")]

        # Frameworks
        frameworks_input = click.prompt(
            "Frameworks (comma-separated)",
            default=""
        )
        if frameworks_input:
            tech_stack["frameworks"] = [fw.strip() for fw in frameworks_input.split(",")]

        # Platforms
        platforms_input = click.prompt(
            "Platforms (comma-separated, e.g., Azure, AWS, Docker)",
            default="Docker"
        )
        if platforms_input:
            tech_stack["platforms"] = [p.strip() for p in platforms_input.split(",")]

        # Databases
        databases_input = click.prompt(
            "Databases (comma-separated)",
            default=""
        )
        if databases_input:
            tech_stack["databases"] = [db.strip() for db in databases_input.split(",")]
    else:
        tech_stack = {"languages": ["Python"]}

    # Work tracking platform
    click.echo("\n🔧 Work Tracking Platform")

    platform = click.prompt(
        "Platform",
        type=click.Choice(["azure-devops", "jira", "github-projects"]),
        default="azure-devops"
    )

    organization = click.prompt("Organization URL or name")
    project = click.prompt("Project name")

    # Create configuration
    click.echo("\n⚙️  Creating configuration...")

    config = create_default_config(
        project_name=project_name,
        project_type=project_type,
        tech_stack=tech_stack,
        work_tracking_platform=platform,
        organization=organization,
        project=project,
    )

    # Create directory structure
    click.echo("\n📁 Creating directory structure...")

    claude_dir = config_file.parent
    directories = [
        claude_dir,
        claude_dir / "agents",
        claude_dir / "commands",
        claude_dir / "workflow-state",
        claude_dir / "profiling",
        claude_dir / "learnings",
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        click.echo(f"   ✓ {directory}")

    # Save configuration
    save_config(config, config_file)
    click.echo(f"\n   ✓ Configuration saved to {config_file}")

    # Create initial files
    _create_gitignore(claude_dir)
    _create_readme(claude_dir, project_name)

    # Summary
    click.echo("\n✅ Initialization complete!\n")
    click.echo("Next steps:")
    click.echo(f"  1. Review configuration: {config_file}")
    click.echo(f"  2. Configure work tracking: cwf configure {platform}")
    click.echo("  3. Enable agents: cwf agent enable business-analyst")
    click.echo("  4. Enable workflows: cwf workflow enable sprint-planning")
    click.echo("  5. Validate setup: cwf validate\n")


def _create_gitignore(claude_dir: Path) -> None:
    """Create .gitignore for .claude directory."""
    gitignore_file = claude_dir / ".gitignore"

    if not gitignore_file.exists():
        content = """# Workflow state files
workflow-state/*.json

# Profiling reports
profiling/*.json

# Session logs
*.log
"""
        gitignore_file.write_text(content)


def _create_readme(claude_dir: Path, project_name: str) -> None:
    """Create README in .claude directory."""
    readme_file = claude_dir / "README.md"

    if not readme_file.exists():
        content = f"""# Claude Workflow Automation

This directory contains workflow automation configuration for **{project_name}**.

## Directory Structure

- `config.yaml` - Main configuration file
- `agents/` - Rendered agent definitions
- `commands/` - Workflow command scripts
- `workflow-state/` - Workflow execution state
- `profiling/` - Workflow performance profiles
- `learnings/` - Session learnings and patterns

## Usage

See the main project README for usage instructions.

## Configuration

Edit `config.yaml` to customize:
- Work item type mappings
- Custom field mappings
- Quality standards
- Agent models and settings
"""
        readme_file.write_text(content)
