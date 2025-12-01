"""
Configure command - configure work tracking platforms and other settings.
"""
import click
from pathlib import Path

from config import load_config, save_config


@click.group(name="configure")
def configure_command():
    """Configure work tracking and other settings."""
    pass


@configure_command.command(name="azure-devops")
def configure_azure_devops():
    """Configure Azure DevOps integration."""
    try:
        config = load_config()

        click.echo("\n🔧 Azure DevOps Configuration\n")

        # Organization and project
        config.work_tracking.organization = click.prompt(
            "Organization URL",
            default=config.work_tracking.organization
        )

        config.work_tracking.project = click.prompt(
            "Project name",
            default=config.work_tracking.project
        )

        # Credentials source
        click.echo("\nCredentials options:")
        click.echo("  1. Azure CLI (default)")
        click.echo("  2. Environment variable")
        click.echo("  3. File")

        cred_choice = click.prompt("Credentials source", type=int, default=1)

        if cred_choice == 1:
            config.work_tracking.credentials_source = "cli"
        elif cred_choice == 2:
            var_name = click.prompt("Environment variable name", default="AZURE_DEVOPS_PAT")
            config.work_tracking.credentials_source = f"env:{var_name}"
        elif cred_choice == 3:
            file_path = click.prompt("File path")
            config.work_tracking.credentials_source = f"file:{file_path}"

        # Work item types
        if click.confirm("\nConfigure work item type mappings?", default=False):
            click.echo("\nWork item type mappings (leave blank to keep current):")

            for generic_type in ["epic", "feature", "story", "task", "bug"]:
                current = config.work_tracking.work_item_types.get(generic_type, "")
                new_value = click.prompt(
                    f"  {generic_type}",
                    default=current,
                    show_default=True
                )
                if new_value:
                    config.work_tracking.work_item_types[generic_type] = new_value

        # Custom fields
        if click.confirm("\nConfigure custom field mappings?", default=False):
            click.echo("\nAdd custom field mappings (enter blank line when done):")

            while True:
                generic_name = click.prompt(
                    "  Generic field name (or blank to finish)",
                    default="",
                    show_default=False
                )
                if not generic_name:
                    break

                platform_name = click.prompt(
                    f"  Platform field name for '{generic_name}'"
                )

                config.work_tracking.custom_fields[generic_name] = platform_name

        # Sprint/iteration configuration
        if click.confirm("\nConfigure sprint/iteration settings?", default=False):
            config.work_tracking.sprint_naming = click.prompt(
                "Sprint naming pattern (use {number} for sprint number)",
                default=config.work_tracking.sprint_naming
            )

            config.work_tracking.iteration_format = click.prompt(
                "Iteration path format (use {project} and {sprint})",
                default=config.work_tracking.iteration_format
            )

        # Save configuration
        save_config(config)

        click.echo("\n✅ Azure DevOps configuration saved.\n")

        # Test connection
        if click.confirm("Test connection now?", default=True):
            _test_azure_connection(config)

    except FileNotFoundError as e:
        click.echo(f"❌ Error: {e}")
        click.echo("Run 'trustable-ai init' to initialize the framework.")


@configure_command.command(name="file-based")
def configure_file_based():
    """Configure file-based work item tracking."""
    try:
        config = load_config()

        click.echo("\n📁 File-Based Work Tracking Configuration\n")

        # Set platform to file-based
        config.work_tracking.platform = "file-based"

        # Work items directory
        config.work_tracking.work_items_directory = click.prompt(
            "Work items directory",
            default=config.work_tracking.work_items_directory or ".claude/work-items"
        )

        # Work item types
        if click.confirm("\nConfigure work item type names?", default=False):
            click.echo("\nWork item type names (leave blank to keep current):")

            for generic_type in ["epic", "feature", "story", "task", "bug"]:
                current = config.work_tracking.work_item_types.get(generic_type, generic_type.title())
                new_value = click.prompt(
                    f"  {generic_type}",
                    default=current,
                    show_default=True
                )
                if new_value:
                    config.work_tracking.work_item_types[generic_type] = new_value

        # Sprint configuration
        if click.confirm("\nConfigure sprint settings?", default=False):
            config.work_tracking.sprint_naming = click.prompt(
                "Sprint naming pattern (use {number} for sprint number)",
                default=config.work_tracking.sprint_naming or "Sprint {number}"
            )

        # Create work items directory
        work_items_path = Path(config.work_tracking.work_items_directory)
        if not work_items_path.exists():
            if click.confirm(f"\nCreate directory '{work_items_path}'?", default=True):
                work_items_path.mkdir(parents=True, exist_ok=True)
                click.echo(f"  ✓ Created {work_items_path}")

        # Save configuration
        save_config(config)

        click.echo("\n✅ File-based work tracking configured.\n")
        click.echo("Work items will be stored in: " + str(work_items_path))

    except FileNotFoundError as e:
        click.echo(f"❌ Error: {e}")
        click.echo("Run 'trustable-ai init' to initialize the framework.")


@configure_command.command(name="quality-standards")
def configure_quality_standards():
    """Configure quality and security standards."""
    try:
        config = load_config()

        click.echo("\n📊 Quality Standards Configuration\n")

        # Test coverage
        config.quality_standards.test_coverage_min = click.prompt(
            "Minimum test coverage (%)",
            type=int,
            default=config.quality_standards.test_coverage_min
        )

        # Vulnerabilities
        click.echo("\nMaximum allowed vulnerabilities:")
        config.quality_standards.critical_vulnerabilities_max = click.prompt(
            "  Critical",
            type=int,
            default=config.quality_standards.critical_vulnerabilities_max
        )

        config.quality_standards.high_vulnerabilities_max = click.prompt(
            "  High",
            type=int,
            default=config.quality_standards.high_vulnerabilities_max
        )

        config.quality_standards.medium_vulnerabilities_max = click.prompt(
            "  Medium",
            type=int,
            default=config.quality_standards.medium_vulnerabilities_max
        )

        # Code quality
        config.quality_standards.code_complexity_max = click.prompt(
            "\nMaximum cyclomatic complexity",
            type=int,
            default=config.quality_standards.code_complexity_max
        )

        config.quality_standards.duplicate_code_max = click.prompt(
            "Maximum duplicate code (%)",
            type=float,
            default=config.quality_standards.duplicate_code_max
        )

        # Performance
        click.echo("\nPerformance thresholds:")
        config.quality_standards.build_time_max_minutes = click.prompt(
            "  Maximum build time (minutes)",
            type=int,
            default=config.quality_standards.build_time_max_minutes
        )

        config.quality_standards.test_time_max_minutes = click.prompt(
            "  Maximum test time (minutes)",
            type=int,
            default=config.quality_standards.test_time_max_minutes
        )

        # Save configuration
        save_config(config)

        click.echo("\n✅ Quality standards configuration saved.\n")

    except FileNotFoundError as e:
        click.echo(f"❌ Error: {e}")


def _test_azure_connection(config):
    """Test Azure DevOps connection."""
    try:
        import subprocess

        click.echo("\n🧪 Testing Azure DevOps connection...")

        # Try to run az devops project show
        result = subprocess.run(
            [
                "az", "devops", "project", "show",
                "--project", config.work_tracking.project,
                "--organization", config.work_tracking.organization,
            ],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            click.echo("✅ Connection successful!")
        else:
            click.echo("❌ Connection failed:")
            click.echo(result.stderr)
            click.echo("\nMake sure you've run 'az login' and configured Azure DevOps extension.")

    except FileNotFoundError:
        click.echo("⚠️  Azure CLI not found. Install it to test connection.")
    except Exception as e:
        click.echo(f"❌ Error testing connection: {e}")
