---
context:
  keywords: [claude, runtime, state, profiling, commands, agents, config, workflow-state]
  task_types: [any]
  priority: medium
  max_tokens: 400
  children: []
  dependencies: []
---
# .claude

## Purpose

Contains Claude Code configuration and runtime state for the Trusted AI Development (TAID) framework. This directory is the operational center for AI-assisted workflows, storing configuration, rendered agents/workflows, execution state, and analytics.

## Key Components

- **config.yaml**: Main framework configuration (project, work tracking, quality standards, agents)
- **agents/**: Rendered agent definitions in Markdown format for Claude Code
- **commands/**: Rendered workflow slash commands for Claude Code
- **learnings/**: Captured learnings from workflow executions
- **profiling/**: Performance profiling reports (timing, token usage, cost estimates)
- **workflow-state/**: Workflow execution state for re-entrancy and recovery
- **settings.local.json**: Local Claude Code settings

## Architecture

This directory bridges the TAID framework with Claude Code:
1. **Configuration**: `config.yaml` defines project-specific settings
2. **Template Rendering**: Framework renders agents/workflows to `.claude/agents/` and `.claude/commands/`
3. **Runtime State**: Workflows persist state to `.claude/workflow-state/` for checkpointing
4. **Analytics**: Profiling data collected in `.claude/profiling/` for optimization
5. **Knowledge Capture**: Learnings stored in `.claude/learnings/` for continuous improvement

## Usage

Initialize this directory in your project:
```bash
taid init  # Creates .claude/ with default config.yaml
```

Render agents and workflows:
```bash
taid agent render-all     # Renders to .claude/agents/
taid workflow render-all  # Renders to .claude/commands/
```

## File Conventions

- **agents/*.md**: Rendered agent definitions (e.g., business-analyst.md)
- **commands/*.md**: Workflow slash commands (e.g., sprint-planning.md)
- **workflow-state/*.json**: State files named `{workflow}-{id}.json`
- **profiling/*.md**: Reports named `{workflow}-{timestamp}.md`
- **learnings/*.md**: Categorized learning documents

## Important Notes

- **Version Control**: Commit `config.yaml` and templates, gitignore runtime state
- **State Persistence**: Workflow state enables resume after failures
- **Template Customization**: Copy templates here to customize for your project
- **Token Budget**: Context loading respects Claude's token limits
