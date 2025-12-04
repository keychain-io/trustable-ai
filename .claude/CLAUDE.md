---
context:
  purpose: "Stores Claude Code configuration and runtime state, preventing workflow setup errors and state loss"
  problem_solved: "Without centralized runtime storage, workflows lose state on crashes, agents/workflows aren't available without manual rendering, and profiling/learnings data is scattered. This directory provides single location for all framework runtime artifacts, enabling recovery and analysis."
  keywords: [claude, runtime, workflow, agent, config, state, profiling, learnings]
  task_types: [workflow, agent-development, configuration]
  priority: medium
  max_tokens: 600
  children: []
  dependencies: []
---
# .claude Directory

## Purpose

Solves **runtime state management** and **workflow configuration errors** by centralizing all Claude Code operational artifacts in one location.

Without a dedicated runtime directory:
- Workflow state scattered across project → hard to find/resume after crashes
- Rendered agents/workflows mixed with templates → confusion about what's deployed
- Profiling data and learnings lost → no performance optimization or knowledge capture
- Configuration in multiple locations → unclear which config is active

**.claude/** provides the operational center for all AI-assisted workflows, enabling state recovery, performance analysis, and knowledge retention.

## Key Components

- **config.yaml**: Main framework configuration (project, work tracking, quality standards, agents)
- **agents/**: Rendered agent definitions in Markdown format for Claude Code
- **commands/**: Rendered workflow slash commands for Claude Code
- **learnings/**: Captured learnings from workflow executions
- **profiling/**: Performance profiling reports (timing, token usage, cost estimates)
- **workflow-state/**: Workflow execution state for re-entrancy and recovery
- **settings.local.json**: Local Claude Code settings

## Architecture

This directory bridges the Trustable AI framework with Claude Code:
1. **Configuration**: `config.yaml` defines project-specific settings
2. **Template Rendering**: Framework renders agents/workflows to `.claude/agents/` and `.claude/commands/`
3. **Runtime State**: Workflows persist state to `.claude/workflow-state/` for checkpointing
4. **Analytics**: Profiling data collected in `.claude/profiling/` for optimization
5. **Knowledge Capture**: Learnings stored in `.claude/learnings/` for continuous improvement

## Usage

Initialize this directory in your project:
```bash
trustable-ai init  # Creates .claude/ with default config.yaml
```

Render agents and workflows:
```bash
trustable-ai agent render-all     # Renders to .claude/agents/
trustable-ai workflow render-all  # Renders to .claude/commands/
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
