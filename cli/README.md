# cli

## Purpose

Command-line interface for Trustable AI. Provides the `trustable-ai` command for initializing, configuring, and managing AI-assisted software development workflows.

## Key Components

- **main.py**: CLI entry point using Click framework, defines `trustable-ai` command group
- **commands/**: Subcommands organized by function (init, configure, agent, workflow, etc.)
- **__init__.py**: Module exports

## Architecture

The CLI uses Click's command group pattern:
```
trustable-ai (main group)
├── init              (commands/init.py)
├── configure         (commands/configure.py)
├── agent             (commands/agent.py)
├── workflow          (commands/workflow.py)
├── validate          (commands/validate.py)
├── doctor            (commands/doctor.py)
├── status            (commands/status.py)
├── learnings         (commands/learnings.py)
├── context           (commands/context.py)
└── skill             (commands/skill.py)
```

## Command Overview

### Core Commands
- **trustable-ai init**: Initialize Trustable AI in a project (creates .claude/config.yaml)
- **trustable-ai configure**: Configure work tracking platforms (Azure DevOps, file-based)
- **trustable-ai validate**: Validate configuration against schema
- **trustable-ai doctor**: Health check for Trustable AI setup

### Agent Management
- **trustable-ai agent list**: List available agents
- **trustable-ai agent enable/disable**: Enable/disable agents
- **trustable-ai agent render**: Render specific agent template
- **trustable-ai agent render-all**: Render all enabled agents to .claude/agents/

### Workflow Management
- **trustable-ai workflow list**: List available workflows
- **trustable-ai workflow render**: Render specific workflow template
- **trustable-ai workflow render-all**: Render all workflows to .claude/commands/

### Other Commands
- **trustable-ai status**: Show project status and configuration summary
- **trustable-ai learnings**: Manage captured learnings
- **trustable-ai context**: Generate context for specific tasks
- **trustable-ai skill**: Manage and list skills

## Usage Examples

```bash
# Initialize Trustable AI in your project
cd my-project
trustable-ai init

# Configure Azure DevOps
trustable-ai configure azure-devops

# List and enable agents
trustable-ai agent list
trustable-ai agent enable business-analyst
trustable-ai agent render-all

# Render workflows as slash commands
trustable-ai workflow render-all

# Validate configuration
trustable-ai validate

# Check system health
trustable-ai doctor
```

## Conventions

- **Command Naming**: Use kebab-case (agent-render-all)
- **Interactive Prompts**: Use Click's prompt() for required inputs
- **Error Handling**: Provide helpful error messages with next steps
- **Output Format**: Support JSON output with --output-format flag where applicable
- **Project Detection**: Commands assume .claude/config.yaml exists in current directory

## Dependencies

- **Click**: Command-line framework
- **config**: Load and validate configuration
- **agents**: Agent registry for rendering
- **workflows**: Workflow registry for rendering
- **core**: State management and profiling

## Testing

```bash
pytest tests/integration/test_cli_*.py  # Integration tests for CLI commands
```
