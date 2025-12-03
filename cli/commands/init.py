"""
Initialize command - sets up Trustable AI in a project.

This command is re-entrant: running it again will load existing values as defaults,
allowing you to update individual settings without re-entering everything.
"""
import click
from pathlib import Path
from typing import Optional, List, Dict, Any
import yaml

from config import create_default_config, save_config, load_config
from config.schema import FrameworkConfig
from agents import AgentRegistry
from workflows import WorkflowRegistry


def _load_existing_config(config_file: Path) -> Optional[FrameworkConfig]:
    """Load existing configuration if it exists."""
    if config_file.exists():
        try:
            return load_config(config_file)
        except Exception:
            return None
    return None


def _get_existing_value(config: Optional[FrameworkConfig], path: str, default: Any) -> Any:
    """Get a value from existing config or return default."""
    if config is None:
        return default

    try:
        parts = path.split(".")
        value = config
        for part in parts:
            if hasattr(value, part):
                value = getattr(value, part)
            elif isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return default
        return value if value is not None else default
    except Exception:
        return default


@click.command(name="init")
@click.option("--interactive/--no-interactive", default=True, help="Interactive mode")
@click.option("--config-path", type=click.Path(), default=None, help="Custom config path")
def init_command(
    interactive: bool,
    config_path: Optional[str],
):
    """
    Initialize Trustable AI in your project.

    This command is re-entrant: running it again will load existing values as defaults,
    allowing you to update individual settings without re-entering everything.
    """
    # Determine config path
    if config_path:
        config_file = Path(config_path)
    else:
        config_file = Path.cwd() / ".claude" / "config.yaml"

    # Load existing config if present
    existing_config = _load_existing_config(config_file)

    if existing_config:
        click.echo("\n🔄 Updating Trustable AI configuration")
        click.echo("   (Press Enter to keep existing values)\n")
    else:
        click.echo("\n🚀 Initializing Trustable AI\n")

    # Get project name
    existing_name = _get_existing_value(existing_config, "project.name", "My Project")
    if interactive:
        project_name = click.prompt(
            "Project name (for display/documentation)",
            default=existing_name
        )
    else:
        project_name = existing_name

    # Get project type
    project_types = [
        "web-application", "api", "mobile-app", "desktop-app",
        "infrastructure", "library", "cli-tool", "microservice"
    ]
    existing_type = _get_existing_value(existing_config, "project.type", "api")

    if interactive:
        click.echo(f"\nProject types: {', '.join(project_types)}")
        project_type = click.prompt(
            "Project type",
            default=existing_type,
            type=click.Choice(project_types, case_sensitive=False)
        )
    else:
        project_type = existing_type

    # Gather tech stack information
    tech_stack = {}

    if interactive:
        click.echo("\n📦 Technology Stack")

        # Languages
        existing_langs = _get_existing_value(existing_config, "project.tech_stack.languages", ["Python"])
        languages_input = click.prompt(
            "Programming languages (comma-separated)",
            default=", ".join(existing_langs) if existing_langs else "Python"
        )
        tech_stack["languages"] = [lang.strip() for lang in languages_input.split(",") if lang.strip()]

        # Frameworks
        existing_frameworks = _get_existing_value(existing_config, "project.tech_stack.frameworks", [])
        frameworks_input = click.prompt(
            "Frameworks (comma-separated)",
            default=", ".join(existing_frameworks) if existing_frameworks else ""
        )
        if frameworks_input.strip():
            tech_stack["frameworks"] = [fw.strip() for fw in frameworks_input.split(",") if fw.strip()]

        # Platforms
        existing_platforms = _get_existing_value(existing_config, "project.tech_stack.platforms", ["Docker"])
        platforms_input = click.prompt(
            "Platforms (comma-separated, e.g., Azure, AWS, Docker)",
            default=", ".join(existing_platforms) if existing_platforms else "Docker"
        )
        if platforms_input.strip():
            tech_stack["platforms"] = [p.strip() for p in platforms_input.split(",") if p.strip()]

        # Databases
        existing_dbs = _get_existing_value(existing_config, "project.tech_stack.databases", [])
        databases_input = click.prompt(
            "Databases (comma-separated)",
            default=", ".join(existing_dbs) if existing_dbs else ""
        )
        if databases_input.strip():
            tech_stack["databases"] = [db.strip() for db in databases_input.split(",") if db.strip()]
    else:
        # Non-interactive: use existing or defaults
        tech_stack = _get_existing_value(existing_config, "project.tech_stack", {"languages": ["Python"]})

    # Work tracking platform
    if interactive:
        click.echo("\n🔧 Work Tracking Platform")

        existing_platform = _get_existing_value(existing_config, "work_tracking.platform", "file-based")
        platform = click.prompt(
            "Platform",
            type=click.Choice(["azure-devops", "jira", "github-projects", "file-based"]),
            default=existing_platform
        )

        if platform != "file-based":
            existing_org = _get_existing_value(existing_config, "work_tracking.organization", "")
            existing_project = _get_existing_value(existing_config, "work_tracking.project", "")

            organization = click.prompt(
                "Organization URL or name",
                default=existing_org if existing_org else ""
            )
            project = click.prompt(
                f"Work tracking project name (your {platform} project)",
                default=existing_project if existing_project else ""
            )
        else:
            organization = _get_existing_value(existing_config, "work_tracking.organization", None)
            project = _get_existing_value(existing_config, "work_tracking.project", None)
    else:
        # Non-interactive defaults
        platform = _get_existing_value(existing_config, "work_tracking.platform", "file-based")
        organization = _get_existing_value(existing_config, "work_tracking.organization", None)
        project = _get_existing_value(existing_config, "work_tracking.project", None)

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

    # Preserve existing enabled agents if updating
    if existing_config:
        config.agent_config.enabled_agents = existing_config.agent_config.enabled_agents

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
        if not existing_config:
            click.echo(f"   ✓ {directory}")

    if existing_config:
        click.echo("   ✓ Directories verified")

    # Save configuration
    save_config(config, config_file)
    click.echo(f"\n   ✓ Configuration saved to {config_file}")

    # Create initial files (only if new)
    if not existing_config:
        _create_gitignore(claude_dir)
        _create_readme(claude_dir, project_name)

    # Check if work tracking configuration is incomplete and offer to complete it
    if interactive and platform != "file-based" and (not organization or not project):
        click.echo(f"\n⚠️  Work tracking ({platform}) is not fully configured.")
        click.echo(f"   Missing: {'organization, ' if not organization else ''}{'project' if not project else ''}")

        if click.confirm(f"\nWould you like to complete {platform} configuration now?", default=True):
            # Import and run the configure command inline
            from cli.commands.configure import configure_azure_devops, configure_file_based

            if platform == "azure-devops":
                # Run Azure DevOps configuration
                ctx = click.Context(configure_azure_devops)
                ctx.invoke(configure_azure_devops)
                # Reload config after configuration
                try:
                    config = load_config(config_file)
                except Exception:
                    pass
            else:
                click.echo(f"\n   Run 'trustable-ai configure {platform}' to complete configuration.")
        else:
            click.echo(f"\n   Run 'trustable-ai configure {platform}' later to complete configuration.")

    # Agent selection
    if interactive:
        click.echo("\n🤖 Agent Selection")

        registry = AgentRegistry(config)
        available_agents = registry.list_agents()

        click.echo("Available agents:")
        for i, agent in enumerate(available_agents, 1):
            enabled = "✓" if agent in config.agent_config.enabled_agents else " "
            click.echo(f"  [{enabled}] {i:2}. {agent}")

        current_count = len(config.agent_config.enabled_agents)
        click.echo(f"\nCurrently enabled: {current_count} agents")
        click.echo("Enter agent numbers (comma-separated), 'all', or press Enter to keep current")

        selection = click.prompt("Selection", default="")

        if selection.strip() == "":
            click.echo(f"   ✓ Keeping current agents ({current_count} enabled)")
        elif selection.lower() == "all":
            config.agent_config.enabled_agents = available_agents
            click.echo(f"   ✓ Enabled all {len(available_agents)} agents")
        else:
            # Parse comma-separated numbers
            try:
                indices = [int(x.strip()) for x in selection.split(",")]
                selected_agents = [available_agents[i - 1] for i in indices if 1 <= i <= len(available_agents)]
                if selected_agents:
                    config.agent_config.enabled_agents = selected_agents
                    click.echo(f"   ✓ Enabled {len(selected_agents)} agents: {', '.join(selected_agents)}")
                else:
                    click.echo("   ⚠ No valid agents selected, keeping current")
            except (ValueError, IndexError):
                click.echo("   ⚠ Invalid selection, keeping current")

        # Save updated config with selected agents
        save_config(config, config_file)

        # Ask about rendering
        if click.confirm("\nRender agents and workflows now?", default=True):
            click.echo("\n📝 Rendering agent definitions...")
            agents_dir = claude_dir / "agents"
            for agent_name in config.agent_config.enabled_agents:
                try:
                    output_file = registry.save_rendered_agent(agent_name, agents_dir)
                    click.echo(f"   ✓ {agent_name}")
                except Exception as e:
                    click.echo(f"   ✗ {agent_name}: {e}")

            click.echo("\n📝 Rendering agent slash commands...")
            commands_dir = claude_dir / "commands"
            for agent_name in config.agent_config.enabled_agents:
                try:
                    output_file = registry.save_agent_slash_command(agent_name, commands_dir)
                    click.echo(f"   ✓ /{agent_name}")
                except Exception as e:
                    click.echo(f"   ✗ /{agent_name}: {e}")

            click.echo("\n📝 Rendering workflow slash commands...")
            workflow_registry = WorkflowRegistry(config)
            for workflow_name in workflow_registry.list_workflows():
                try:
                    output_file = workflow_registry.save_rendered_workflow(workflow_name, commands_dir)
                    click.echo(f"   ✓ /{workflow_name}")
                except Exception as e:
                    click.echo(f"   ✗ /{workflow_name}: {e}")

        # Ask about context generation
        if click.confirm("\nGenerate hierarchical context files (README.md + CLAUDE.md)?", default=not existing_config):
            from cli.commands.context import _analyze_repository, _generate_claude_md_content, _generate_readme_content

            click.echo("\n📝 Generating context file hierarchy (README.md + CLAUDE.md)...")

            root_path = Path.cwd()
            analysis = _analyze_repository(root_path, max_depth=3)

            created_readme = 0
            created_claude = 0
            skipped = 0

            for dir_info in analysis["directories"]:
                dir_path = root_path / dir_info["relative_path"]
                readme_path = dir_path / "README.md"
                claude_path = dir_path / "CLAUDE.md"

                # Generate README.md if it doesn't exist
                if not readme_path.exists():
                    try:
                        readme_content = _generate_readme_content(dir_info, analysis)
                        if readme_content and readme_content.strip():
                            readme_path.write_text(readme_content)
                            click.echo(f"   ✓ {dir_info['relative_path']}/README.md")
                            created_readme += 1
                    except Exception as e:
                        click.echo(f"   ✗ {dir_info['relative_path']}/README.md: {e}")

                # Generate CLAUDE.md
                if claude_path.exists():
                    click.echo(f"   ⏭ {dir_info['relative_path']}/CLAUDE.md (exists)")
                    skipped += 1
                    continue

                try:
                    content = _generate_claude_md_content(dir_info, analysis)

                    # Validate content is not empty (empty CLAUDE.md files cause API Error 400)
                    if not content or not content.strip():
                        click.echo(f"   ⚠ {dir_info['relative_path']}/CLAUDE.md (skipped - empty content)")
                        skipped += 1
                        continue

                    claude_path.write_text(content)
                    click.echo(f"   ✓ {dir_info['relative_path']}/CLAUDE.md")
                    created_claude += 1
                except Exception as e:
                    click.echo(f"   ✗ {dir_info['relative_path']}/CLAUDE.md: {e}")

            click.echo(f"\n   Created {created_readme} README.md, {created_claude} CLAUDE.md files, skipped {skipped} existing")

            # Build context index
            click.echo("\n📝 Building context index...")
            from cli.commands.context import _extract_keywords
            import yaml as yaml_lib
            from datetime import datetime

            index = {
                "generated_at": datetime.now().isoformat(),
                "root": str(root_path.absolute()),
                "context_files": [],
                "keywords": {}
            }

            for claude_file in root_path.rglob("CLAUDE.md"):
                if ".git" in claude_file.parts:
                    continue
                try:
                    relative_path = claude_file.relative_to(root_path)
                    content = claude_file.read_text(encoding="utf-8")
                    keywords = _extract_keywords(content)

                    entry = {
                        "path": str(relative_path),
                        "type": "claude_md",
                        "size": len(content),
                        "keywords": keywords[:20]
                    }
                    index["context_files"].append(entry)

                    for keyword in keywords:
                        index["keywords"].setdefault(keyword.lower(), []).append(str(relative_path))
                except Exception:
                    pass

            index_path = claude_dir / "context-index.yaml"
            with open(index_path, "w") as f:
                yaml_lib.dump(index, f, default_flow_style=False)

            click.echo(f"   ✓ Indexed {len(index['context_files'])} context files")
            click.echo(f"   ✓ Context index saved to {index_path}")

    # Summary
    action = "updated" if existing_config else "complete"
    click.echo(f"\n✅ Initialization {action}!\n")

    if not existing_config:
        click.echo("Next steps:")
        click.echo(f"  1. Review configuration: {config_file}")
        click.echo(f"  2. Review and enhance CLAUDE.md files with project-specific details")
        click.echo(f"  3. Configure work tracking: trustable-ai configure {platform}")
        click.echo("  4. Validate setup: trustable-ai validate")
        click.echo("  5. Start using workflows in Claude Code (e.g., /sprint-planning)\n")
    else:
        click.echo("Configuration updated. Run 'trustable-ai validate' to verify settings.\n")


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
        content = f"""# Trustable AI

This directory contains AI-assisted workflow automation configuration for **{project_name}**.

## Directory Structure

- `config.yaml` - Main configuration file
- `agents/` - Rendered agent definitions
- `commands/` - Workflow slash commands
- `workflow-state/` - Workflow execution state
- `profiling/` - Workflow performance profiles
- `learnings/` - Session learnings and patterns

## Quick Commands

```bash
trustable-ai agent list         # List available agents
trustable-ai agent render-all   # Render agents to .claude/agents/
trustable-ai workflow list      # List available workflows
trustable-ai workflow render-all # Render workflows to .claude/commands/
trustable-ai validate           # Validate configuration
```

## Configuration

Edit `config.yaml` to customize:
- Work item type mappings
- Custom field mappings
- Quality standards
- Agent models and settings
"""
        readme_file.write_text(content)
