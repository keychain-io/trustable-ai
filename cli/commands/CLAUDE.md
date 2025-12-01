# commands

## Purpose

CLI command implementations for the `trustable-ai` command-line tool. Each file implements a specific command or command group using Click framework.

## Key Components

- **init.py**: `trustable-ai init` - Initialize Trustable AI framework in a project
- **configure.py**: `trustable-ai configure` - Configure work tracking platforms
- **agent.py**: `trustable-ai agent` - Agent management commands (list, enable, disable, render)
- **workflow.py**: `trustable-ai workflow` - Workflow management commands (list, render)
- **validate.py**: `trustable-ai validate` - Validate configuration against schema
- **doctor.py**: `trustable-ai doctor` - System health check and diagnostics
- **status.py**: `trustable-ai status` - Show project status and configuration
- **learnings.py**: `trustable-ai learnings` - Manage captured learnings
- **context.py**: `trustable-ai context` - Generate context for tasks
- **skill.py**: `trustable-ai skill` - Manage skills
- **__init__.py**: Module exports for command registration

## Command Patterns

### Standard Command Structure
```python
import click
from config import load_config

@click.command(name="command-name")
@click.option("--option", help="Option description")
def command_name(option):
    """Command description."""
    try:
        # Load config if needed
        config = load_config()

        # Execute command logic
        # ...

        click.echo("Success message")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()
```

### Command Groups
```python
@click.group()
def agent_command():
    """Agent management commands."""
    pass

@agent_command.command(name="list")
def list_agents():
    """List available agents."""
    # ...

@agent_command.command(name="render")
@click.argument("agent_name")
def render_agent(agent_name):
    """Render specific agent."""
    # ...
```

## Command Descriptions

### init.py - Project Initialization
- Prompts for project details (name, type, tech stack)
- Creates `.claude/` directory structure
- Generates default `config.yaml`
- Optionally configures work tracking

### configure.py - Work Tracking Configuration
- **azure-devops**: Configure Azure DevOps integration
- **file-based**: Configure file-based work tracking
- Updates config.yaml with platform settings
- Validates credentials and connectivity

### agent.py - Agent Management
- **list**: List all available agent templates
- **enable**: Enable agent in configuration
- **disable**: Disable agent in configuration
- **render**: Render specific agent to stdout or file
- **render-all**: Render all enabled agents to .claude/agents/

### workflow.py - Workflow Management
- **list**: List all available workflow templates
- **render**: Render specific workflow to stdout or file
- **render-all**: Render all workflows to .claude/commands/

### validate.py - Configuration Validation
- Loads config.yaml and validates against Pydantic schema
- Checks for missing required fields
- Validates work tracking platform configuration
- Verifies agent and workflow references

### doctor.py - System Health Check
- Verifies .claude/ directory structure
- Checks config.yaml validity
- Tests work tracking connectivity (if configured)
- Validates agent and workflow templates
- Reports missing dependencies

### status.py - Project Status
- Shows current configuration summary
- Lists enabled agents and workflows
- Displays work tracking platform status
- Shows recent workflow executions

### learnings.py - Learning Management
- **list**: List captured learnings
- **add**: Add new learning
- **export**: Export learnings to markdown

### context.py - Context Generation
- **generate**: Generate context for specific task
- Uses hierarchical CLAUDE.md loading
- Supports token budget limits

### skill.py - Skill Management
- **list**: List available skills
- **info**: Show skill details
- **init**: Initialize skills

## Conventions

- **Error Handling**: Use try/except with click.Abort() for clean exits
- **Output**: Use click.echo() for output, click.secho() for colored output
- **Prompts**: Use click.prompt() for interactive input
- **Options**: Use --option format (kebab-case)
- **Arguments**: Use UPPER_CASE for required positional arguments
- **Help Text**: Provide clear, concise help text for all commands and options

## Testing

```bash
pytest tests/integration/test_cli_*.py  # Test all CLI commands
pytest tests/integration/test_cli_agent.py  # Test agent commands
pytest tests/integration/test_cli_init.py   # Test init command
```
