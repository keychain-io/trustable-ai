# Trusted AI Development (TAID)

This directory contains AI-assisted workflow automation configuration for **Trusted AI Development Workbench**.

## Directory Structure

- `config.yaml` - Main configuration file
- `agents/` - Rendered agent definitions
- `commands/` - Workflow slash commands
- `workflow-state/` - Workflow execution state
- `profiling/` - Workflow performance profiles
- `learnings/` - Session learnings and patterns

## Quick Commands

```bash
taid agent list         # List available agents
taid agent render-all   # Render agents to .claude/agents/
taid workflow list      # List available workflows
taid workflow render-all # Render workflows to .claude/commands/
taid validate           # Validate configuration
```

## Configuration

Edit `config.yaml` to customize:
- Work item type mappings
- Custom field mappings
- Quality standards
- Agent models and settings
