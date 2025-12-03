"""
Status command for TAID CLI.

Shows current framework status and active workflows.
"""

import click
from pathlib import Path
from datetime import datetime
import yaml


@click.command()
@click.option("--workflows", is_flag=True, help="Show active workflows")
@click.option("--sprints", is_flag=True, help="Show sprint status")
@click.option("--all", "show_all", is_flag=True, help="Show all status information")
def status(workflows: bool, sprints: bool, show_all: bool):
    """
    Show Trustable AI status and active workflows.

    Displays:
    - Configuration summary
    - Enabled agents
    - Active workflows
    - Sprint status (if configured)
    """
    if show_all:
        workflows = sprints = True

    click.echo("TAID Status")
    click.echo("=" * 50)

    # Load configuration
    config_path = Path(".claude/config.yaml")
    if not config_path.exists():
        click.echo("\n✗ Not initialized. Run 'trustable-ai init' first.")
        return

    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)
    except Exception as e:
        click.echo(f"\n✗ Error loading config: {e}")
        return

    # Project info
    project = config.get("project", {})
    click.echo(f"\nProject: {project.get('name', 'Unknown')}")
    click.echo(f"Type: {project.get('type', 'Unknown')}")

    tech_stack = project.get("tech_stack", {})
    if tech_stack:
        languages = tech_stack.get("languages", [])
        frameworks = tech_stack.get("frameworks", [])
        if languages:
            click.echo(f"Languages: {', '.join(languages)}")
        if frameworks:
            click.echo(f"Frameworks: {', '.join(frameworks)}")

    # Work tracking
    work_tracking = config.get("work_tracking", {})
    platform = work_tracking.get("platform", "file-based")
    click.echo(f"\nWork Tracking: {platform}")
    if platform == "azure-devops":
        org = work_tracking.get("organization", "Not set")
        project_name = work_tracking.get("project", "Not set")
        click.echo(f"  Organization: {org}")
        click.echo(f"  Project: {project_name}")

    # Enabled agents
    agent_config = config.get("agent_config", {})
    enabled_agents = agent_config.get("enabled_agents", [])
    click.echo(f"\nEnabled Agents: {len(enabled_agents)}")
    for agent in enabled_agents:
        click.echo(f"  - {agent}")

    # Quality standards
    quality = config.get("quality_standards", {})
    if quality:
        click.echo("\nQuality Standards:")
        click.echo(f"  Test Coverage: {quality.get('test_coverage_min', 80)}% min")
        click.echo(f"  Critical Vulns: {quality.get('critical_vulnerabilities_max', 0)} max")

    # Active workflows
    if workflows or show_all:
        click.echo("\n" + "-" * 50)
        click.echo("Active Workflows")
        click.echo("-" * 50)

        state_dir = Path(".claude/workflow-state")
        if state_dir.exists():
            active_count = 0
            for state_file in state_dir.glob("*.yaml"):
                try:
                    with open(state_file) as f:
                        state = yaml.safe_load(f)
                    if state and state.get("status") != "completed":
                        active_count += 1
                        click.echo(f"\n  {state.get('workflow_name', 'Unknown')}")
                        click.echo(f"    ID: {state.get('execution_id', 'Unknown')}")
                        click.echo(f"    Status: {state.get('status', 'Unknown')}")
                        click.echo(f"    Step: {state.get('current_step', 'Unknown')}")
                        started = state.get("started_at", "Unknown")
                        click.echo(f"    Started: {started}")
                except Exception:
                    pass

            if active_count == 0:
                click.echo("\n  No active workflows")
        else:
            click.echo("\n  No workflow state directory")

    # Sprint status
    if sprints or show_all:
        click.echo("\n" + "-" * 50)
        click.echo("Sprint Status")
        click.echo("-" * 50)

        # Check for file-based work items
        work_items_dir = Path(".claude/work-items")
        if work_items_dir.exists():
            sprints_dir = work_items_dir / "sprints"
            if sprints_dir.exists():
                sprint_files = list(sprints_dir.glob("*.yaml"))
                if sprint_files:
                    for sprint_file in sprint_files:
                        try:
                            with open(sprint_file) as f:
                                sprint = yaml.safe_load(f)
                            click.echo(f"\n  {sprint.get('name', sprint_file.stem)}")
                            if sprint.get("start_date"):
                                click.echo(f"    Start: {sprint['start_date']}")
                            if sprint.get("end_date"):
                                click.echo(f"    End: {sprint['end_date']}")

                            # Count work items in sprint
                            sprint_path = sprint.get("path", "")
                            item_count = 0
                            for type_dir in ["features", "tasks", "bugs"]:
                                for item_file in (work_items_dir / type_dir).glob("*.yaml"):
                                    try:
                                        with open(item_file) as f:
                                            item = yaml.safe_load(f)
                                        if item.get("iteration") == sprint_path:
                                            item_count += 1
                                    except Exception:
                                        pass
                            click.echo(f"    Work Items: {item_count}")
                        except Exception:
                            pass
                else:
                    click.echo("\n  No sprints defined")
            else:
                click.echo("\n  No sprints directory")
        else:
            # Azure DevOps or not configured
            if platform == "azure-devops":
                click.echo("\n  Use 'az boards iteration' to view sprints")
            else:
                click.echo("\n  No work items configured")

    # Profiling summary
    profiling_dir = Path(".claude/profiling")
    if profiling_dir.exists():
        profile_count = len(list(profiling_dir.glob("*.yaml")))
        if profile_count > 0:
            click.echo(f"\nProfiling: {profile_count} profile(s) recorded")

    click.echo("")
