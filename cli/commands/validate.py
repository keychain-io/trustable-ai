"""
Validate command - validate configuration and setup.
"""
import click
from pathlib import Path

from config import load_config
from agents import AgentRegistry


@click.command(name="validate")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def validate_command(verbose: bool):
    """Validate framework configuration and setup."""

    click.echo("\n🔍 Validating Trustable AI setup\n")

    errors = []
    warnings = []
    checks_passed = 0
    total_checks = 0

    # Check 1: Configuration file exists
    total_checks += 1
    config_file = Path.cwd() / ".claude" / "config.yaml"

    if config_file.exists():
        click.echo("✓ Configuration file exists")
        checks_passed += 1
    else:
        click.echo("✗ Configuration file not found")
        errors.append("Configuration file not found. Run 'trustable-ai init' to initialize.")
        click.echo("\n❌ Validation failed. Run 'trustable-ai init' to initialize the framework.\n")
        raise SystemExit(1)

    # Load configuration
    try:
        config = load_config()
    except Exception as e:
        click.echo(f"✗ Failed to load configuration: {e}")
        errors.append(f"Configuration validation failed: {e}")
        click.echo("\n❌ Validation failed.\n")
        raise SystemExit(1)

    # Check 2: Required directories exist
    total_checks += 1
    required_dirs = [
        ".claude/agents",
        ".claude/workflow-state",
        ".claude/profiling",
    ]

    all_dirs_exist = True
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            all_dirs_exist = False
            warnings.append(f"Directory missing: {dir_path}")

    if all_dirs_exist:
        click.echo("✓ Required directories exist")
        checks_passed += 1
    else:
        click.echo("⚠ Some directories missing (will be created as needed)")

    # Check 3: Agent templates available
    total_checks += 1
    try:
        registry = AgentRegistry(config)
        agents = registry.list_agents()

        if agents:
            click.echo(f"✓ Agent templates available ({len(agents)} agents)")
            checks_passed += 1

            if verbose:
                for agent in agents:
                    status = "enabled" if registry.is_agent_enabled(agent) else "disabled"
                    click.echo(f"    • {agent} ({status})")
        else:
            click.echo("✗ No agent templates found")
            errors.append("No agent templates found")

    except Exception as e:
        click.echo(f"✗ Agent registry error: {e}")
        errors.append(f"Agent registry error: {e}")

    # Check 4: Work tracking configuration
    total_checks += 1
    platform = config.work_tracking.platform

    if platform == "file-based":
        # File-based tracking doesn't require organization/project
        click.echo("✓ Work tracking configured (file-based)")
        checks_passed += 1

        if verbose:
            work_items_dir = config.work_tracking.work_items_directory or ".claude/work-items"
            click.echo(f"    Platform: {platform}")
            click.echo(f"    Work items directory: {work_items_dir}")
    elif config.work_tracking.organization and config.work_tracking.project:
        click.echo("✓ Work tracking configured")
        checks_passed += 1

        if verbose:
            click.echo(f"    Platform: {platform}")
            click.echo(f"    Organization: {config.work_tracking.organization}")
            click.echo(f"    Project: {config.work_tracking.project}")
    else:
        # Provide specific guidance on what's missing
        click.echo(f"⚠ Work tracking incomplete ({platform})")
        missing = []
        if not config.work_tracking.organization:
            missing.append("organization")
        if not config.work_tracking.project:
            missing.append("project")

        warning_msg = f"Work tracking missing: {', '.join(missing)}"
        if platform == "azure-devops":
            warning_msg += f"\n    Run: trustable-ai configure azure-devops"
        elif platform == "jira":
            warning_msg += f"\n    Run: trustable-ai configure jira"
        elif platform == "github-projects":
            warning_msg += f"\n    Run: trustable-ai configure github-projects"
        else:
            warning_msg += f"\n    Run: trustable-ai configure {platform}"

        warnings.append(warning_msg)

    # Check 5: Quality standards configured
    total_checks += 1
    if config.quality_standards:
        click.echo("✓ Quality standards configured")
        checks_passed += 1

        if verbose:
            click.echo(f"    Test coverage minimum: {config.quality_standards.test_coverage_min}%")
            click.echo(f"    Max critical vulnerabilities: {config.quality_standards.critical_vulnerabilities_max}")
    else:
        click.echo("⚠ Quality standards not configured")
        warnings.append("Quality standards not configured")

    # Check 6: At least one agent enabled
    total_checks += 1
    if config.agent_config.enabled_agents:
        click.echo(f"✓ Agents enabled ({len(config.agent_config.enabled_agents)})")
        checks_passed += 1

        if verbose:
            for agent in config.agent_config.enabled_agents:
                click.echo(f"    • {agent}")
    else:
        click.echo("⚠ No agents enabled")
        warnings.append("No agents enabled. Run 'trustable-ai agent enable <name>' to enable agents.")

    # Summary
    click.echo(f"\n{'='*80}")
    click.echo(f"Validation Summary: {checks_passed}/{total_checks} checks passed")
    click.echo('='*80)

    if errors:
        click.echo("\n❌ Errors:")
        for error in errors:
            click.echo(f"  • {error}")

    if warnings:
        click.echo("\n⚠️  Warnings:")
        for warning in warnings:
            click.echo(f"  • {warning}")

    if not errors:
        click.echo("\n✅ Validation successful!\n")
        click.echo("You can now:")
        click.echo("  • Render agents: trustable-ai agent render-all")
        click.echo("  • Render workflows: trustable-ai workflow render-all\n")
    else:
        click.echo("\n❌ Validation failed. Please fix the errors above.\n")
