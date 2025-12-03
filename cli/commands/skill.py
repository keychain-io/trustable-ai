"""
Skill command for TAID CLI.

Manage and interact with framework skills.
"""

import click
from pathlib import Path


@click.group()
def skill():
    """
    Manage framework skills.

    Skills are reusable capabilities that provide common
    functionality like Azure DevOps operations, context
    management, and more.
    """
    pass


@skill.command("list")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed information")
def list_skills(verbose: bool):
    """
    List available skills.

    Examples:
        trustable-ai skill list
        trustable-ai skill list -v
    """
    try:
        from skills import list_skills as get_skills
        from skills.registry import get_registry

        registry = get_registry()
        skill_names = get_skills()

        click.echo("Available Skills")
        click.echo("=" * 50)

        if not skill_names:
            click.echo("No skills found.")
            return

        for name in sorted(skill_names):
            if verbose:
                info = registry.get_skill_info(name)
                if info:
                    click.echo(f"\n{name}")
                    click.echo(f"  Description: {info.get('description', 'N/A')}")
                    click.echo(f"  Version: {info.get('version', 'N/A')}")

                    prereqs = info.get("prerequisites", {})
                    if prereqs.get("satisfied"):
                        click.echo("  Prerequisites: ✓ Satisfied")
                    else:
                        click.echo("  Prerequisites: ✗ Not satisfied")
                        for missing in prereqs.get("missing", []):
                            click.echo(f"    - Missing: {missing}")
                else:
                    click.echo(f"\n{name} (could not load)")
            else:
                click.echo(f"  - {name}")

    except ImportError as e:
        click.echo(f"Error loading skills: {e}")
        click.echo("Make sure the skills module is properly installed.")


@skill.command("info")
@click.argument("skill_name")
def skill_info(skill_name: str):
    """
    Show detailed information about a skill.

    Examples:
        trustable-ai skill info azure_devops
        trustable-ai skill info workflow
    """
    try:
        from skills.registry import get_registry

        registry = get_registry()
        info = registry.get_skill_info(skill_name)

        if not info:
            click.echo(f"Skill not found: {skill_name}")
            click.echo("Use 'trustable-ai skill list' to see available skills.")
            return

        click.echo(f"Skill: {info.get('name', skill_name)}")
        click.echo("=" * 50)
        click.echo(f"Description: {info.get('description', 'N/A')}")
        click.echo(f"Version: {info.get('version', 'N/A')}")
        click.echo(f"Initialized: {info.get('initialized', False)}")

        # Show documentation path
        doc_path = info.get("documentation_path")
        if doc_path:
            click.echo(f"Documentation: {doc_path}")

        # Show prerequisites
        prereqs = info.get("prerequisites", {})
        click.echo("\nPrerequisites:")
        if prereqs.get("satisfied"):
            click.echo("  ✓ All prerequisites satisfied")
        else:
            for missing in prereqs.get("missing", []):
                click.echo(f"  ✗ Missing: {missing}")

        for warning in prereqs.get("warnings", []):
            click.echo(f"  ! Warning: {warning}")

    except ImportError as e:
        click.echo(f"Error: {e}")


@skill.command("check")
@click.argument("skill_name")
def check_skill(skill_name: str):
    """
    Check if a skill's prerequisites are met.

    Examples:
        trustable-ai skill check azure_devops
    """
    try:
        from skills import get_skill

        skill_instance = get_skill(skill_name)

        if not skill_instance:
            click.echo(f"Skill not found: {skill_name}")
            return

        prereqs = skill_instance.verify_prerequisites()

        click.echo(f"Checking: {skill_name}")
        click.echo("-" * 30)

        if prereqs.get("satisfied"):
            click.echo("✓ All prerequisites satisfied")

            # Try to initialize
            click.echo("\nAttempting initialization...")
            if skill_instance.initialize():
                click.echo("✓ Skill initialized successfully")
            else:
                click.echo("✗ Initialization failed")
        else:
            click.echo("✗ Prerequisites not satisfied")

            for missing in prereqs.get("missing", []):
                click.echo(f"  Missing: {missing}")

        for warning in prereqs.get("warnings", []):
            click.echo(f"  Warning: {warning}")

    except ImportError as e:
        click.echo(f"Error: {e}")


@skill.command("doc")
@click.argument("skill_name")
def show_documentation(skill_name: str):
    """
    Show skill documentation.

    Examples:
        trustable-ai skill doc azure_devops
    """
    try:
        from skills import get_skill

        skill_instance = get_skill(skill_name)

        if not skill_instance:
            click.echo(f"Skill not found: {skill_name}")
            return

        doc = skill_instance.get_documentation()

        if doc:
            click.echo(doc)
        else:
            click.echo(f"No documentation found for: {skill_name}")
            click.echo("Create a SKILL.md file in the skill directory.")

    except ImportError as e:
        click.echo(f"Error: {e}")


@skill.command("init")
@click.argument("skill_name")
def initialize_skill(skill_name: str):
    """
    Initialize a skill.

    Examples:
        trustable-ai skill init azure_devops
    """
    try:
        from skills import get_skill

        click.echo(f"Initializing skill: {skill_name}")

        skill_instance = get_skill(skill_name)

        if not skill_instance:
            click.echo(f"✗ Skill not found: {skill_name}")
            return

        # Check prerequisites first
        prereqs = skill_instance.verify_prerequisites()
        if not prereqs.get("satisfied"):
            click.echo("✗ Prerequisites not satisfied:")
            for missing in prereqs.get("missing", []):
                click.echo(f"  - {missing}")
            return

        # Initialize
        if skill_instance.initialize():
            click.echo(f"✓ Skill '{skill_name}' initialized successfully")
        else:
            click.echo(f"✗ Failed to initialize skill: {skill_name}")
            if hasattr(skill_instance, "_last_error"):
                click.echo(f"  Error: {skill_instance._last_error}")

    except ImportError as e:
        click.echo(f"Error: {e}")


@skill.command("init-all")
def initialize_all():
    """
    Initialize all available skills.
    """
    try:
        from skills.registry import get_registry

        registry = get_registry()
        results = registry.initialize_all()

        click.echo("Initializing all skills")
        click.echo("-" * 30)

        success_count = 0
        for name, success in results.items():
            if success:
                click.echo(f"  ✓ {name}")
                success_count += 1
            else:
                click.echo(f"  ✗ {name}")

        click.echo(f"\n{success_count}/{len(results)} skills initialized")

    except ImportError as e:
        click.echo(f"Error: {e}")
