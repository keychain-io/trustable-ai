---
context:
  keywords: [cli, command, taid, init, validate, doctor, render, agent, workflow]
  task_types: [cli-development, command-implementation]
  priority: medium
  max_tokens: 600
  children:
    - path: cli/commands/CLAUDE.md
      when: [command, subcommand, implementation]
  dependencies: []
---
# cli

## Purpose

Command-line interface for Trusted AI Development (TAID). Provides the `taid` command for initializing, configuring, and managing AI-assisted software development workflows.

## Key Components

- **main.py**: CLI entry point using Click framework, defines `taid` command group
- **commands/**: Subcommands organized by function (init, configure, agent, workflow, etc.)
- **__init__.py**: Module exports

## Architecture

The CLI uses Click's command group pattern:
```
taid (main group)
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
- **taid init**: Initialize TAID in a project (creates .claude/config.yaml)
- **taid configure**: Configure work tracking platforms (Azure DevOps, file-based)
- **taid validate**: Validate configuration against schema
- **taid doctor**: Health check for TAID setup

### Agent Management
- **taid agent list**: List available agents
- **taid agent enable/disable**: Enable/disable agents
- **taid agent render**: Render specific agent template
- **taid agent render-all**: Render all enabled agents to .claude/agents/

### Workflow Management
- **taid workflow list**: List available workflows
- **taid workflow render**: Render specific workflow template
- **taid workflow render-all**: Render all workflows to .claude/commands/

### Other Commands
- **taid status**: Show project status and configuration summary
- **taid learnings**: Manage captured learnings
- **taid context**: Generate context for specific tasks
- **taid skill**: Manage and list skills

## Usage Examples

```bash
# Initialize TAID in your project
cd my-project
taid init

# Configure Azure DevOps
taid configure azure-devops

# List and enable agents
taid agent list
taid agent enable business-analyst
taid agent render-all

# Render workflows as slash commands
taid workflow render-all

# Validate configuration
taid validate

# Check system health
taid doctor
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
