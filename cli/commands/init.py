"""
Initialize command - sets up Trustable AI in a project.

This command is re-entrant: running it again will load existing values as defaults,
allowing you to update individual settings without re-entering everything.
"""
import click
from pathlib import Path
from typing import Optional, List, Dict, Any
import yaml
import json
import shutil

from config import create_default_config, save_config, load_config
from config.schema import FrameworkConfig
from agents import AgentRegistry
from workflows import WorkflowRegistry
from cli.platform_detector import PlatformDetector
from cli.permissions_generator import PermissionsTemplateGenerator
from cli.config_generators.pytest_generator import PytestConfigGenerator
from cli.config_generators.jest_generator import JestConfigGenerator


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


def detect_test_framework(project_path: Path) -> str:
    """
    Detect testing framework based on project files.

    Analyzes the project directory structure and configuration files to determine
    which testing framework is being used. This enables framework-specific test
    configuration and agent instructions.

    Detection logic:
    - **pytest** (Python): Checks for pytest.ini, pyproject.toml with [tool.pytest],
      setup.py, or setup.cfg with pytest configuration
    - **jest** (JavaScript/TypeScript): Checks for package.json with "jest" in
      devDependencies or dependencies
    - **junit** (Java): Checks for pom.xml (Maven) or build.gradle (Gradle)
    - **go-testing** (Go): Checks for go.mod file
    - **generic**: Fallback when no specific framework is detected

    Args:
        project_path: Path to the project directory to analyze

    Returns:
        Framework name as string: 'pytest', 'jest', 'junit', 'go-testing', or 'generic'

    Example:
        >>> detect_test_framework(Path("/my/python/project"))
        'pytest'
        >>> detect_test_framework(Path("/my/js/project"))
        'jest'
    """
    # Detect pytest (Python)
    if (project_path / "pytest.ini").exists():
        return "pytest"

    # Check pyproject.toml for pytest configuration
    pyproject_path = project_path / "pyproject.toml"
    if pyproject_path.exists():
        try:
            # Try to parse TOML file for pytest configuration
            content = pyproject_path.read_text()
            # Simple check for pytest in tool section (works without toml library)
            if "[tool.pytest" in content:
                return "pytest"
        except Exception:
            # If reading fails, continue checking other files
            pass

    # Check setup.py for pytest
    if (project_path / "setup.py").exists():
        return "pytest"

    # Check setup.cfg for pytest configuration
    setup_cfg_path = project_path / "setup.cfg"
    if setup_cfg_path.exists():
        try:
            content = setup_cfg_path.read_text()
            if "[tool:pytest]" in content or "[pytest]" in content:
                return "pytest"
        except Exception:
            pass

    # Detect Jest (JavaScript/TypeScript)
    package_json_path = project_path / "package.json"
    if package_json_path.exists():
        try:
            package_data = json.loads(package_json_path.read_text())
            dependencies = package_data.get("dependencies", {})
            dev_dependencies = package_data.get("devDependencies", {})

            # Check if jest is in dependencies
            if "jest" in dependencies or "jest" in dev_dependencies:
                return "jest"
        except Exception:
            pass

    # Detect JUnit (Java)
    if (project_path / "pom.xml").exists():
        return "junit"

    if (project_path / "build.gradle").exists():
        return "junit"

    # Detect Go testing
    if (project_path / "go.mod").exists():
        return "go-testing"

    # Fallback to generic
    return "generic"


def _generate_permissions_config(claude_dir: Path) -> Dict[str, int]:
    """
    Generate permissions configuration for Claude Code.

    Detects platform and generates .claude/settings.local.json with safe-action
    permissions that auto-approve safe operations while requiring approval for
    destructive ones.

    Args:
        claude_dir: Path to .claude directory

    Returns:
        Dict with counts of permission types:
            - auto_approved: Number of auto-approved operations
            - requires_approval: Number of operations requiring approval
            - denied: Number of denied operations

    Example:
        >>> counts = _generate_permissions_config(Path(".claude"))
        >>> counts["auto_approved"]
        53
    """
    settings_path = claude_dir / "settings.local.json"

    # Detect platform
    detector = PlatformDetector()
    platform_info = detector.detect_platform()

    # Generate permissions
    generator = PermissionsTemplateGenerator()

    # Load existing settings if present
    existing_settings = {}
    if settings_path.exists():
        try:
            with settings_path.open("r") as f:
                existing_settings = json.load(f)
        except (json.JSONDecodeError, IOError):
            # If file is corrupt or unreadable, start fresh
            existing_settings = {}

    # Generate new permissions (development mode for local development)
    new_permissions = generator.generate_permissions(platform_info, mode="development")

    # Merge with existing settings (preserve user customizations)
    merged_settings = {**existing_settings, **new_permissions}

    # Write merged settings
    generator.write_to_file(merged_settings, settings_path)

    # Count permission types for summary
    counts = {
        "auto_approved": len(new_permissions["permissions"]["allow"]),
        "requires_approval": len(new_permissions["permissions"]["ask"]),
        "denied": len(new_permissions["permissions"]["deny"]),
    }

    return counts


def _generate_pytest_config(project_path: Path) -> Dict[str, Any]:
    """
    Generate pytest.ini configuration file for Python projects.

    Detects if project uses pytest and generates pytest.ini with test taxonomy
    markers based on the universal test taxonomy (config/test_taxonomy.py).

    Args:
        project_path: Path to the project root directory

    Returns:
        Dict with generation results:
            - generated: True if pytest.ini was generated, False if skipped
            - path: Path to pytest.ini if generated, None otherwise
            - reason: Reason for skipping if not generated

    Example:
        >>> result = _generate_pytest_config(Path("/my/python/project"))
        >>> result["generated"]
        True
        >>> result["path"]
        PosixPath('/my/python/project/pytest.ini')
    """
    pytest_ini_path = project_path / "pytest.ini"

    # Skip if pytest.ini already exists
    if pytest_ini_path.exists():
        return {
            "generated": False,
            "path": pytest_ini_path,
            "reason": "pytest.ini already exists",
        }

    # Detect if project uses pytest
    framework = detect_test_framework(project_path)
    if framework != "pytest":
        return {
            "generated": False,
            "path": None,
            "reason": f"Project uses {framework}, not pytest",
        }

    # Generate pytest.ini
    generator = PytestConfigGenerator()
    content = generator.generate_pytest_ini(project_path)

    # Write to file
    try:
        generator.write_to_file(content, pytest_ini_path)
        return {
            "generated": True,
            "path": pytest_ini_path,
            "reason": None,
        }
    except Exception as e:
        return {
            "generated": False,
            "path": None,
            "reason": f"Error writing pytest.ini: {e}",
        }


def _generate_jest_config(project_path: Path) -> Dict[str, Any]:
    """
    Generate jest.config.js configuration file for JavaScript/TypeScript projects.

    Detects if project uses Jest and generates jest.config.js with test taxonomy
    patterns based on the universal test taxonomy (config/test_taxonomy.py).

    Args:
        project_path: Path to the project root directory

    Returns:
        Dict with generation results:
            - generated: True if jest.config.js was generated, False if skipped
            - path: Path to jest.config.js if generated, None otherwise
            - reason: Reason for skipping if not generated

    Example:
        >>> result = _generate_jest_config(Path("/my/js/project"))
        >>> result["generated"]
        True
        >>> result["path"]
        PosixPath('/my/js/project/jest.config.js')
    """
    jest_config_path = project_path / "jest.config.js"

    # Skip if jest.config.js already exists
    if jest_config_path.exists():
        return {
            "generated": False,
            "path": jest_config_path,
            "reason": "jest.config.js already exists",
        }

    # Detect if project uses Jest
    framework = detect_test_framework(project_path)
    if framework != "jest":
        return {
            "generated": False,
            "path": None,
            "reason": f"Project uses {framework}, not jest",
        }

    # Generate jest.config.js
    generator = JestConfigGenerator()
    content = generator.generate_jest_config(project_path)

    # Write to file
    try:
        generator.write_to_file(content, jest_config_path)
        return {
            "generated": True,
            "path": jest_config_path,
            "reason": None,
        }
    except Exception as e:
        return {
            "generated": False,
            "path": None,
            "reason": f"Error writing jest.config.js: {e}",
        }


def _detect_project_settings(root: Path) -> Dict[str, Any]:
    """Auto-detect project settings from repository structure."""
    settings = {
        "name": root.name,
        "type": "api",  # default
        "tech_stack": {
            "languages": [],
            "frameworks": [],
            "platforms": [],
            "databases": [],
        }
    }

    # Detect languages and project type
    if (root / "pyproject.toml").exists() or (root / "setup.py").exists():
        settings["tech_stack"]["languages"].append("Python")
        # Try to detect Python frameworks
        for req_file in ["requirements.txt", "pyproject.toml", "setup.py"]:
            req_path = root / req_file
            if req_path.exists():
                try:
                    content = req_path.read_text().lower()
                    if "fastapi" in content:
                        settings["tech_stack"]["frameworks"].append("FastAPI")
                        settings["type"] = "api"
                    if "flask" in content:
                        settings["tech_stack"]["frameworks"].append("Flask")
                        settings["type"] = "api"
                    if "django" in content:
                        settings["tech_stack"]["frameworks"].append("Django")
                        settings["type"] = "web-application"
                    if "click" in content:
                        settings["type"] = "cli-tool"
                    if "pytest" in content:
                        settings["tech_stack"]["frameworks"].append("pytest")
                except Exception:
                    pass

    if (root / "package.json").exists():
        settings["tech_stack"]["languages"].append("JavaScript")
        try:
            import json
            pkg = json.loads((root / "package.json").read_text())
            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
            if "typescript" in deps:
                settings["tech_stack"]["languages"].append("TypeScript")
            if "react" in deps or "@types/react" in deps:
                settings["tech_stack"]["frameworks"].append("React")
                settings["type"] = "web-application"
            if "vue" in deps:
                settings["tech_stack"]["frameworks"].append("Vue")
                settings["type"] = "web-application"
            if "express" in deps:
                settings["tech_stack"]["frameworks"].append("Express")
                settings["type"] = "api"
            if "next" in deps:
                settings["tech_stack"]["frameworks"].append("Next.js")
                settings["type"] = "web-application"
        except Exception:
            pass

    if (root / "go.mod").exists():
        settings["tech_stack"]["languages"].append("Go")
        settings["type"] = "api"

    if (root / "Cargo.toml").exists():
        settings["tech_stack"]["languages"].append("Rust")
        settings["type"] = "cli-tool"

    if (root / "pom.xml").exists() or (root / "build.gradle").exists():
        settings["tech_stack"]["languages"].append("Java")
        settings["type"] = "api"

    # Detect platforms
    if (root / "Dockerfile").exists() or (root / "docker-compose.yml").exists():
        settings["tech_stack"]["platforms"].append("Docker")
    if (root / "terraform").is_dir() or list(root.glob("*.tf")):
        settings["tech_stack"]["platforms"].append("Terraform")
    if (root / ".github" / "workflows").is_dir():
        settings["tech_stack"]["platforms"].append("GitHub Actions")
    if (root / "azure-pipelines.yml").exists():
        settings["tech_stack"]["platforms"].append("Azure DevOps")

    # Detect project type from directory structure
    if (root / "src" / "lib").is_dir() or (root / "lib").is_dir():
        settings["type"] = "library"
    if (root / "cli").is_dir() or (root / "cmd").is_dir():
        settings["type"] = "cli-tool"

    # Default to Python if nothing detected
    if not settings["tech_stack"]["languages"]:
        settings["tech_stack"]["languages"] = ["Python"]

    return settings


@click.command(name="init")
@click.option("--interactive/--no-interactive", default=True, help="Interactive mode")
@click.option("--config-path", type=click.Path(), default=None, help="Custom config path")
@click.option("--auto-detect/--no-auto-detect", default=False, help="Auto-detect project settings from repository")
def init_command(
    interactive: bool,
    config_path: Optional[str],
    auto_detect: bool,
):
    """
    Initialize Trustable AI in your project.

    This command is re-entrant: running it again will load existing values as defaults,
    allowing you to update individual settings without re-entering everything.

    Use --auto-detect to automatically detect project settings from the repository
    structure (languages, frameworks, platforms).
    """
    # Determine config path
    if config_path:
        config_file = Path(config_path)
    else:
        config_file = Path.cwd() / ".claude" / "config.yaml"

    # Load existing config if present
    existing_config = _load_existing_config(config_file)

    # Auto-detect settings (always run to provide smart defaults)
    detected_settings = _detect_project_settings(Path.cwd())

    if existing_config:
        click.echo("\n🔄 Updating Trustable AI configuration")
        click.echo("   (Press Enter to keep existing values)\n")
    else:
        click.echo("\n🚀 Initializing Trustable AI\n")

    # If auto-detect flag and not interactive, use detected settings directly
    if auto_detect and not interactive:
        project_name = detected_settings["name"]
        project_type = detected_settings["type"]
        tech_stack = detected_settings["tech_stack"]
    elif interactive:
        # Show auto-detection results
        click.echo("📡 Auto-detected project settings:")
        click.echo(f"   Name: {detected_settings['name']}")
        click.echo(f"   Type: {detected_settings['type']}")
        click.echo(f"   Languages: {', '.join(detected_settings['tech_stack']['languages']) or 'none detected'}")
        click.echo(f"   Frameworks: {', '.join(detected_settings['tech_stack']['frameworks']) or 'none detected'}")
        click.echo(f"   Platforms: {', '.join(detected_settings['tech_stack']['platforms']) or 'none detected'}")

        if existing_config:
            click.echo("\n   Current config values will be shown as defaults.")
            click.echo("   Detected values shown above for reference.\n")
        else:
            click.echo("")
            if not click.confirm("Use detected settings as defaults?", default=True):
                detected_settings = None

        # Get project name
        click.echo("\n📋 Project name")
        click.echo("   Used for display in logs, documentation, and work item references.\n")
        existing_name = _get_existing_value(existing_config, "project.name", None)
        default_name = existing_name or (detected_settings["name"] if detected_settings else "My Project")
        project_name = click.prompt(
            "Project name",
            default=default_name
        )

        # Get project type with explanation
        project_types = [
            "web-application", "api", "mobile-app", "desktop-app",
            "infrastructure", "library", "cli-tool", "microservice"
        ]
        existing_type = _get_existing_value(existing_config, "project.type", None)
        default_type = existing_type or (detected_settings["type"] if detected_settings else "api")

        click.echo("\n📦 Project type")
        click.echo("   Affects which agent prompts and best practices are emphasized:\n")
        click.echo("   web-application  - Frontend focus, UI/UX, browser compatibility")
        click.echo("   api              - REST/GraphQL patterns, auth, request validation")
        click.echo("   library          - API design, docs, backwards compatibility, packaging")
        click.echo("   cli-tool         - Argument parsing, user feedback, cross-platform")
        click.echo("   microservice     - Service boundaries, messaging, resilience patterns")
        click.echo("   infrastructure   - IaC patterns, security, cost optimization")
        click.echo("   mobile-app       - Mobile platform guidelines (iOS/Android)")
        click.echo("   desktop-app      - Desktop platform guidelines (Electron, etc.)\n")

        project_type = click.prompt(
            "Project type",
            default=default_type,
            type=click.Choice(project_types, case_sensitive=False)
        )

        # Gather tech stack information with explanations
        tech_stack = {}

        click.echo("\n🔧 Technology Stack")
        click.echo("   These settings help agents provide language/framework-specific advice.")
        click.echo("   Leave empty if unsure - you can update config.yaml later.\n")

        # Languages
        existing_langs = _get_existing_value(existing_config, "project.tech_stack.languages", None)
        default_langs = existing_langs or (detected_settings["tech_stack"]["languages"] if detected_settings else ["Python"])
        languages_input = click.prompt(
            "Programming languages (comma-separated)",
            default=", ".join(default_langs) if default_langs else ""
        )
        tech_stack["languages"] = [lang.strip() for lang in languages_input.split(",") if lang.strip()]

        # Frameworks
        existing_frameworks = _get_existing_value(existing_config, "project.tech_stack.frameworks", None)
        default_frameworks = existing_frameworks or (detected_settings["tech_stack"]["frameworks"] if detected_settings else [])
        click.echo("\n   Frameworks (e.g., FastAPI, Django, React, Express, Spring Boot)")
        click.echo("   Helps agents suggest framework-specific patterns and avoid anti-patterns.\n")
        frameworks_input = click.prompt(
            "Frameworks (comma-separated, or leave empty)",
            default=", ".join(default_frameworks) if default_frameworks else ""
        )
        if frameworks_input.strip():
            tech_stack["frameworks"] = [fw.strip() for fw in frameworks_input.split(",") if fw.strip()]

        # Platforms
        existing_platforms = _get_existing_value(existing_config, "project.tech_stack.platforms", None)
        default_platforms = existing_platforms or (detected_settings["tech_stack"]["platforms"] if detected_settings else [])
        click.echo("\n   Platforms (e.g., Docker, AWS, Azure, GCP, Kubernetes)")
        click.echo("   Deployment targets - helps with infrastructure and DevOps guidance.\n")
        platforms_input = click.prompt(
            "Platforms (comma-separated, or leave empty)",
            default=", ".join(default_platforms) if default_platforms else ""
        )
        if platforms_input.strip():
            tech_stack["platforms"] = [p.strip() for p in platforms_input.split(",") if p.strip()]

        # Databases
        existing_dbs = _get_existing_value(existing_config, "project.tech_stack.databases", None)
        default_dbs = existing_dbs or (detected_settings["tech_stack"]["databases"] if detected_settings else [])
        click.echo("\n   Databases (e.g., PostgreSQL, MongoDB, Redis, Elasticsearch)\n")
        databases_input = click.prompt(
            "Databases (comma-separated, or leave empty)",
            default=", ".join(default_dbs) if default_dbs else ""
        )
        if databases_input.strip():
            tech_stack["databases"] = [db.strip() for db in databases_input.split(",") if db.strip()]
    else:
        # Non-interactive without auto-detect: use existing or defaults
        project_name = _get_existing_value(existing_config, "project.name", "My Project")
        project_type = _get_existing_value(existing_config, "project.type", "api")
        tech_stack = _get_existing_value(existing_config, "project.tech_stack", {"languages": ["Python"]})

    # Work tracking platform
    if interactive:
        click.echo("\n🔧 Work Tracking Platform")
        click.echo("Work tracking integrates agents with your task management system:")
        click.echo("  - azure-devops: Full integration with Azure Boards (requires az login)")
        click.echo("  - jira: Jira Cloud/Server integration (coming soon)")
        click.echo("  - github-projects: GitHub Projects integration (coming soon)")
        click.echo("  - file-based: Local markdown files in .claude/work-items/ (no setup required)\n")

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

    # Create directory structure (runtime directories only)
    click.echo("\n📁 Creating directory structure...")

    claude_dir = config_file.parent
    directories = [
        claude_dir,
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

    # Generate permissions configuration
    click.echo("\n🔍 Detecting platform...")
    try:
        detector = PlatformDetector()
        platform_info = detector.detect_platform()
        platform_desc = platform_info["os"]
        if platform_info.get("is_wsl"):
            platform_desc += " (WSL2)"
        click.echo(f"   Platform: {platform_desc}")
        click.echo(f"   Shell: {platform_info['shell']}")

        click.echo("\n🔒 Configuring permissions...")
        counts = _generate_permissions_config(claude_dir)

        click.echo("\n✅ Permissions configured:")
        click.echo(f"   - Auto-approved: {counts['auto_approved']} safe operations (git status, pytest, etc.)")
        click.echo(f"   - Require approval: {counts['requires_approval']} operations (git push, network access, etc.)")
        click.echo(f"   - Denied: {counts['denied']} destructive operations (--force, rm -rf, etc.)")
        click.echo(f"\n   Settings saved to {claude_dir / 'settings.local.json'}")
    except Exception as e:
        # Permissions generation is non-critical, warn but continue
        click.echo(f"\n⚠️  Warning: Could not generate permissions: {e}")
        click.echo("   You can configure permissions manually in .claude/settings.local.json")

    # Generate test framework configuration
    click.echo("\n🧪 Detecting test framework...")
    try:
        project_root = Path.cwd()
        framework = detect_test_framework(project_root)
        click.echo(f"   Test framework: {framework}")

        if framework == "pytest":
            click.echo("\n📝 Generating pytest.ini...")
            result = _generate_pytest_config(project_root)

            if result["generated"]:
                click.echo(f"   ✓ pytest.ini created at {result['path']}")
                click.echo("   - Test discovery configured (testpaths, python_files)")
                click.echo("   - Test taxonomy markers defined (unit, integration, functional, etc.)")
                click.echo("   - Marker descriptions for IDE support")
            else:
                if result["reason"]:
                    click.echo(f"   ⏭ {result['reason']}")
        elif framework == "jest":
            click.echo("\n📝 Generating jest.config.js...")
            result = _generate_jest_config(project_root)

            if result["generated"]:
                click.echo(f"   ✓ jest.config.js created at {result['path']}")
                click.echo("   - Test discovery configured (testMatch patterns)")
                click.echo("   - Test taxonomy patterns documented (unit, integration, functional, etc.)")
                click.echo("   - Classification approaches explained (name patterns, comments)")
                click.echo("   - Coverage thresholds configured")
            else:
                if result["reason"]:
                    click.echo(f"   ⏭ {result['reason']}")
        else:
            click.echo(f"   ⏭ Test config not generated (project uses {framework})")
    except Exception as e:
        # Test framework config generation is non-critical, warn but continue
        click.echo(f"\n⚠️  Warning: Could not generate test configuration: {e}")
        click.echo("   You can create test configuration manually if needed")

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

        # Ask about context generation
        if click.confirm("\nGenerate hierarchical context files (README.md + CLAUDE.md)?", default=not existing_config):
            from cli.commands.context import (
                _analyze_repository, _generate_claude_md_content, _generate_readme_content,
                _generate_front_matter, _merge_claude_md_content
            )

            click.echo("\n📝 Generating context file hierarchy (README.md + CLAUDE.md)...")

            root_path = Path.cwd()
            analysis = _analyze_repository(root_path, max_depth=3)

            # Check if there are existing CLAUDE.md files
            existing_claude_files = [
                d for d in analysis["directories"]
                if (root_path / d["relative_path"] / "CLAUDE.md").exists()
            ]

            merge_existing = False
            if existing_claude_files:
                click.echo(f"\n   Found {len(existing_claude_files)} existing CLAUDE.md file(s).")
                click.echo("   Options:")
                click.echo("     - Merge: Update front matter while preserving your custom content")
                click.echo("     - Skip: Leave existing files unchanged")
                merge_existing = click.confirm("   Merge existing CLAUDE.md files?", default=True)

            created_readme = 0
            created_claude = 0
            merged_claude = 0
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
                            readme_path.write_text(readme_content, encoding='utf-8')
                            click.echo(f"   ✓ {dir_info['relative_path']}/README.md")
                            created_readme += 1
                    except Exception as e:
                        click.echo(f"   ✗ {dir_info['relative_path']}/README.md: {e}")

                # Generate or merge CLAUDE.md
                if claude_path.exists():
                    if merge_existing:
                        # Merge: update front matter, preserve content
                        try:
                            existing_content = claude_path.read_text(encoding="utf-8")
                            new_front_matter = _generate_front_matter(dir_info, analysis)
                            merged_content = _merge_claude_md_content(existing_content, new_front_matter)

                            if merged_content and merged_content.strip():
                                claude_path.write_text(merged_content, encoding='utf-8')
                                click.echo(f"   🔄 {dir_info['relative_path']}/CLAUDE.md (merged)")
                                merged_claude += 1
                            else:
                                click.echo(f"   ⚠ {dir_info['relative_path']}/CLAUDE.md (merge failed)")
                                skipped += 1
                        except Exception as e:
                            click.echo(f"   ✗ {dir_info['relative_path']}/CLAUDE.md (merge error: {e})")
                            skipped += 1
                    else:
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

                    claude_path.write_text(content, encoding='utf-8')
                    click.echo(f"   ✓ {dir_info['relative_path']}/CLAUDE.md")
                    created_claude += 1
                except Exception as e:
                    click.echo(f"   ✗ {dir_info['relative_path']}/CLAUDE.md: {e}")

            summary_parts = [f"Created {created_readme} README.md, {created_claude} CLAUDE.md"]
            if merged_claude > 0:
                summary_parts.append(f"merged {merged_claude}")
            summary_parts.append(f"skipped {skipped}")
            click.echo(f"\n   {', '.join(summary_parts)}")

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
            with open(index_path, "w", encoding='utf-8') as f:
                yaml_lib.dump(index, f, default_flow_style=False)

            click.echo(f"   ✓ Indexed {len(index['context_files'])} context files")
            click.echo(f"   ✓ Context index saved to {index_path}")

    # Render agents and workflows so they're immediately usable
    # This happens in both interactive and non-interactive modes
    if config.agent_config.enabled_agents:
        click.echo("\n📝 Rendering agents and workflows...")

        try:
            # Create AgentRegistry if not already created
            if 'registry' not in locals():
                registry = AgentRegistry(config)

            # Render enabled agents
            agents_dir = claude_dir / "agents"
            agents_dir.mkdir(parents=True, exist_ok=True)

            for agent_name in config.agent_config.enabled_agents:
                try:
                    output_file = registry.save_rendered_agent(agent_name, agents_dir)
                    click.echo(f"   ✓ {agent_name} → {output_file.relative_to(Path.cwd())}")
                except Exception as e:
                    click.echo(f"   ✗ {agent_name}: {e}")

            # Render ALL workflows (no enable/disable for workflows)
            workflow_registry = WorkflowRegistry(config)
            workflows_dir = claude_dir / "commands"
            workflows_dir.mkdir(parents=True, exist_ok=True)

            for workflow_name in workflow_registry.list_workflows():
                try:
                    output_file = workflow_registry.save_rendered_workflow(workflow_name, workflows_dir)
                    click.echo(f"   ✓ /{workflow_name} → {output_file.relative_to(Path.cwd())}")
                except Exception as e:
                    click.echo(f"   ✗ /{workflow_name}: {e}")

            click.echo(f"\n   ✅ Agents and workflows ready to use in Claude Code")
        except Exception as e:
            click.echo(f"   ⚠️  Error rendering: {e}")
            click.echo(f"   You can render manually with:")
            click.echo(f"      trustable-ai agent render-all")
            click.echo(f"      trustable-ai workflow render-all")

    # Copy skills directory to .claude/skills/
    # Done at the end to avoid interfering with context generation
    click.echo("\n📦 Installing skills...")
    try:
        skills_src = Path(__file__).parent.parent.parent / "skills"
        skills_dest = claude_dir / "skills"

        if not skills_src.exists() or not skills_src.is_dir():
            click.echo(f"   ⚠️  Warning: Skills source directory not found at {skills_src}")
        else:
            if skills_dest.exists():
                shutil.rmtree(skills_dest)
            shutil.copytree(skills_src, skills_dest)

            # Count skills installed
            skill_dirs = [d for d in skills_dest.iterdir() if d.is_dir() and not d.name.startswith('__')]
            click.echo(f"   ✓ Installed {len(skill_dirs)} skills to {skills_dest.relative_to(Path.cwd())}")

            # Verify skills can be imported
            test_import_cmd = f'python -c "import sys; sys.path.insert(0, \\"{skills_dest}\\"); from work_tracking import get_adapter"'
            import subprocess
            test_result = subprocess.run(test_import_cmd, shell=True, capture_output=True, text=True)
            if test_result.returncode != 0:
                click.echo(f"   ⚠️  Warning: Skills import test failed: {test_result.stderr}")
            else:
                click.echo(f"   ✓ Skills import verified")
    except Exception as e:
        # Skills copying is important but not critical enough to fail init
        click.echo(f"   ⚠️  Warning: Could not install skills: {e}")
        click.echo("   Skills can be manually copied from the skills/ directory if needed")

    # Summary
    action = "updated" if existing_config else "complete"
    click.echo(f"\n✅ Initialization {action}!\n")

    if not existing_config:
        # Determine correct command based on platform
        import platform as platform_module
        if platform_module.system() == 'Windows':
            claude_cmd = "claude.cmd"
        else:
            claude_cmd = "claude"

        click.echo("📋 Next steps:")
        click.echo(f"")
        click.echo(f"  1. Start Claude Code in this directory:")
        click.echo(f"     $ {claude_cmd}")
        click.echo(f"")
        click.echo(f"  2. Use the rendered workflows (slash commands):")
        click.echo(f"     /sprint-planning      - Plan your sprint")
        click.echo(f"     /backlog-grooming     - Refine your backlog")
        click.echo(f"     /context-generation   - Update CLAUDE.md files")
        click.echo(f"")
        click.echo(f"  3. Or spawn agents directly:")
        click.echo(f"     /architect            - Architecture decisions")
        click.echo(f"     /business-analyst     - Business value analysis")
        click.echo(f"     /engineer             - Implementation tasks")
        click.echo(f"")
        click.echo(f"  4. Commit the generated files to git:")
        click.echo(f"     $ git add .claude/")
        click.echo(f"     $ git commit -m \"Add Trustable AI configuration\"")
        click.echo(f"")
        click.echo(f"For more information: https://docs.trustable.ai/getting-started\n")
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
        gitignore_file.write_text(content, encoding='utf-8')


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
        readme_file.write_text(content, encoding='utf-8')
