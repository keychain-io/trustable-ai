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
