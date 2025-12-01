"""
Doctor command for Trustable AI CLI.

Performs health checks on the framework installation and configuration.
"""

import click
import subprocess
from pathlib import Path


@click.command()
@click.option("--fix", is_flag=True, help="Attempt to fix issues automatically")
def doctor(fix: bool):
    """
    Run health checks on Trustable AI installation.

    Checks:
    - Python version and dependencies
    - Configuration file validity
    - Directory structure
    - Azure CLI (if configured)
    - Skills availability
    """
    click.echo("Trustable AI Health Check")
    click.echo("=" * 50)

    issues = []
    warnings = []

    # Check 1: Python version
    click.echo("\n[1/7] Checking Python version...")
    import sys
    py_version = sys.version_info
    if py_version >= (3, 9):
        click.echo(f"  ✓ Python {py_version.major}.{py_version.minor}.{py_version.micro}")
    else:
        issues.append(f"Python 3.9+ required, found {py_version.major}.{py_version.minor}")
        click.echo(f"  ✗ Python {py_version.major}.{py_version.minor} (3.9+ required)")

    # Check 2: Configuration file
    click.echo("\n[2/7] Checking configuration...")
    config_path = Path(".claude/config.yaml")
    if config_path.exists():
        click.echo(f"  ✓ Configuration file found: {config_path}")
        try:
            from config.loader import load_config
            config = load_config(config_path)
            click.echo("  ✓ Configuration is valid")
        except Exception as e:
            issues.append(f"Configuration error: {e}")
            click.echo(f"  ✗ Configuration error: {e}")
    else:
        issues.append("Configuration file not found")
        click.echo(f"  ✗ Configuration file not found at {config_path}")
        click.echo("    Run 'trustable-ai init' to create configuration")

    # Check 3: Directory structure
    click.echo("\n[3/7] Checking directory structure...")
    required_dirs = [
        ".claude",
        ".claude/agents",
        ".claude/commands",
        ".claude/workflow-state",
    ]
    for dir_path in required_dirs:
        path = Path(dir_path)
        if path.exists():
            click.echo(f"  ✓ {dir_path}/")
        else:
            if fix:
                path.mkdir(parents=True, exist_ok=True)
                click.echo(f"  ✓ {dir_path}/ (created)")
            else:
                warnings.append(f"Directory missing: {dir_path}")
                click.echo(f"  ! {dir_path}/ (missing)")

    # Check 4: Agent templates
    click.echo("\n[4/7] Checking agent templates...")
    try:
        from agents.registry import AgentRegistry
        from config.loader import load_config
        config = load_config()
        registry = AgentRegistry(config)
        agents = registry.list_agents()
        click.echo(f"  ✓ {len(agents)} agent templates available")
        for agent in agents[:5]:
            click.echo(f"    - {agent}")
        if len(agents) > 5:
            click.echo(f"    ... and {len(agents) - 5} more")
    except Exception as e:
        warnings.append(f"Agent registry error: {e}")
        click.echo(f"  ! Agent registry: {e}")

    # Check 5: Skills
    click.echo("\n[5/7] Checking skills...")
    try:
        from skills import list_skills
        skills = list_skills()
        click.echo(f"  ✓ {len(skills)} skills available")
        for skill in skills:
            click.echo(f"    - {skill}")
    except Exception as e:
        warnings.append(f"Skills registry error: {e}")
        click.echo(f"  ! Skills registry: {e}")

    # Check 6: Azure CLI (optional)
    click.echo("\n[6/7] Checking Azure CLI (optional)...")
    try:
        result = subprocess.run(
            ["az", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            # Extract version from output
            version_line = result.stdout.split("\n")[0]
            click.echo(f"  ✓ Azure CLI installed: {version_line}")

            # Check devops extension
            result = subprocess.run(
                ["az", "devops", "--help"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                click.echo("  ✓ Azure DevOps extension installed")
            else:
                warnings.append("Azure DevOps extension not installed")
                click.echo("  ! Azure DevOps extension not installed")
                click.echo("    Install with: az extension add --name azure-devops")
        else:
            warnings.append("Azure CLI not working properly")
            click.echo("  ! Azure CLI not working properly")
    except FileNotFoundError:
        click.echo("  - Azure CLI not installed (optional)")
        click.echo("    Install from: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli")
    except subprocess.TimeoutExpired:
        warnings.append("Azure CLI check timed out")
        click.echo("  ! Azure CLI check timed out")

    # Check 7: Dependencies
    click.echo("\n[7/7] Checking dependencies...")
    # Map package names to their import names
    required_packages = {
        "click": "click",
        "jinja2": "jinja2",
        "pydantic": "pydantic",
        "pyyaml": "yaml",  # pyyaml is imported as 'yaml'
    }
    for package_name, import_name in required_packages.items():
        try:
            __import__(import_name)
            click.echo(f"  ✓ {package_name}")
        except ImportError:
            issues.append(f"Missing package: {package_name}")
            click.echo(f"  ✗ {package_name} (missing)")

    # Summary
    click.echo("\n" + "=" * 50)
    click.echo("Summary")
    click.echo("=" * 50)

    if not issues and not warnings:
        click.echo("\n✓ All checks passed! Trustable AI is ready to use.")
    else:
        if issues:
            click.echo(f"\n✗ {len(issues)} issue(s) found:")
            for issue in issues:
                click.echo(f"  - {issue}")

        if warnings:
            click.echo(f"\n! {len(warnings)} warning(s):")
            for warning in warnings:
                click.echo(f"  - {warning}")

        if issues:
            click.echo("\nRun 'trustable-ai init' to set up the framework.")
        if fix:
            click.echo("\nSome issues were automatically fixed.")
        else:
            click.echo("\nRun 'trustable-ai doctor --fix' to attempt automatic fixes.")
