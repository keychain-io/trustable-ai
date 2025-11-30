"""
Doctor command for TAID CLI.

Performs health checks on the framework installation and configuration.
"""

import click
import subprocess
from pathlib import Path


@click.command()
@click.option("--fix", is_flag=True, help="Attempt to fix issues automatically")
def doctor(fix: bool):
    """
    Run health checks on TAID installation.

    Checks:
    - Python version and dependencies
    - Configuration file validity
    - Directory structure
    - Azure CLI (if configured)
    - Skills availability
    """
    click.echo("TAID Health Check")
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
        click.echo("    Run 'taid init' to create configuration")

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
        registry = AgentRegistry()
        templates = registry.list_templates()
        click.echo(f"  ✓ {len(templates)} agent templates available")
        for template in templates[:5]:
            click.echo(f"    - {template}")
        if len(templates) > 5:
            click.echo(f"    ... and {len(templates) - 5} more")
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
    required_packages = ["click", "jinja2", "pydantic", "pyyaml"]
    for package in required_packages:
        try:
            __import__(package)
            click.echo(f"  ✓ {package}")
        except ImportError:
            issues.append(f"Missing package: {package}")
            click.echo(f"  ✗ {package} (missing)")

    # Summary
    click.echo("\n" + "=" * 50)
    click.echo("Summary")
    click.echo("=" * 50)

    if not issues and not warnings:
        click.echo("\n✓ All checks passed! TAID is ready to use.")
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
            click.echo("\nRun 'taid init' to set up the framework.")
        if fix:
            click.echo("\nSome issues were automatically fixed.")
        else:
            click.echo("\nRun 'taid doctor --fix' to attempt automatic fixes.")
