# Trustable AI

An AI-assisted software lifecycle framework featuring multi-agent orchestration, state management, work tracking integration, and zero-trust tool integration. Build real software projects reliably with Claude Code.

## Overview

Trustable AI provides a sophisticated system for managing AI-assisted software development workflows. It coordinates specialized AI agents to handle complex development tasks while maintaining context, state, and integration with your work tracking platform.

**Key Capabilities:**
- Multi-agent orchestration with 7 context-driven agents
- Re-entrant workflows with state persistence
- Re-entrant initialization (update settings without re-entering everything)
- Hierarchical context management with auto-generated CLAUDE.md files
- Integration with Azure DevOps, file-based tracking (Jira/GitHub planned)
- Skills system for reusable capabilities
- Learnings capture for institutional knowledge

## Installation

```bash
pip install trustable-ai
```

With Azure DevOps support:
```bash
pip install trustable-ai[azure]
```

For development:
```bash
pip install -e ".[dev]"
```

## Quick Start

### Initialize in Your Project

```bash
cd your-project/
trustable-ai init
```

The interactive init wizard will:
1. Prompt for project information (name, type, tech stack)
2. Configure your work tracking platform
3. Create `.claude/` directory structure
4. Let you select which agents to enable (by number, 'all', or keep defaults)
5. Optionally render agents and workflows to `.claude/`
6. Optionally generate hierarchical CLAUDE.md context files

**Re-entrant:** Running `trustable-ai init` again loads existing values as defaults, so you can update individual settings without re-entering everything.

### Non-Interactive Mode

```bash
# Initialize with all defaults
trustable-ai init --no-interactive
```

### Agent and Workflow Management

```bash
# List available agents
trustable-ai agent list

# Enable agents (individually or all at once)
trustable-ai agent enable senior-engineer
trustable-ai agent enable all

# Render all enabled agents to .claude/agents/
trustable-ai agent render-all

# Also render agent slash commands to .claude/commands/
trustable-ai agent render-all --with-commands

# Or render commands separately
trustable-ai agent render-commands

# Render workflows to .claude/commands/
trustable-ai workflow render-all

# Validate your setup
trustable-ai validate
```

### Use with Claude Code

After rendering, use the slash commands in Claude Code:
- `/sprint-planning` - Plan your sprint with multi-agent orchestration
- `/daily-standup` - Generate daily standup reports
- `/backlog-grooming` - Review and prioritize backlog items
- `/senior-engineer` - Invoke the senior engineer agent with fresh context
- `/software-developer` - Invoke the developer agent with fresh context

## Features

### Multi-Agent System (7 Context-Driven Agents)

Trustable AI uses **context-driven agents** that adapt their behavior based on the task context, rather than having a separate agent for each specialized role.

| Agent | Core Responsibilities | Context-Driven Behaviors | Model |
|-------|----------------------|--------------------------|-------|
| **business-analyst** | Requirements analysis, business value scoring, prioritization | Sprint planning, roadmap analysis, feature assessment | sonnet |
| **architect** | Technical architecture, system design, technology decisions | Component design, risk assessment, ADR creation | opus |
| **senior-engineer** | Task breakdown, estimation, code review, epic decomposition | Feature decomposition, sprint planning, backlog grooming | sonnet |
| **engineer** | Feature implementation, DevOps, performance optimization | → DevOps tasks (CI/CD, infrastructure)<br>→ Performance tasks (optimization, profiling) | sonnet |
| **tester** | Test planning, test execution, adversarial testing | → Adversarial testing (find bugs)<br>→ Spec-driven testing (independent verification)<br>→ Falsifiability proving (test validation)<br>→ Test arbitration (fault attribution) | sonnet |
| **security-specialist** | Security review, vulnerability analysis, threat modeling | Code review, architecture review, deployment security | sonnet |
| **scrum-master** | Sprint coordination, workflow management, retrospectives | Sprint planning, daily standups, closure decisions | sonnet |

**Context-Driven Behavior:** Agents adapt based on task keywords. For example:
- `/engineer` analyzing a deployment task → Acts as DevOps engineer (CI/CD focus)
- `/engineer` analyzing a performance issue → Acts as Performance engineer (profiling focus)
- `/tester` in sprint planning → Test planning and strategy
- `/tester` with failing tests → Fault attribution and bug creation

**Deprecated Agents:** The framework maintains backward compatibility for old agent names (project-architect, software-developer, qa-engineer, etc.) by aliasing them to the new consolidated agents.

### Workflow Templates

- **sprint-planning** - Complete sprint planning automation
- **sprint-execution** - Sprint progress monitoring
- **sprint-completion** - Sprint closure and retrospectives
- **sprint-retrospective** - Retrospective analysis
- **backlog-grooming** - Backlog refinement
- **daily-standup** - Daily standup reports
- **dependency-management** - Dependency analysis and tracking
- **workflow-resume** - Resume incomplete workflows from within Claude Code
- **context-generation** - Guided CLAUDE.md hierarchy creation

### Hierarchical Context Generation

Trustable AI can automatically generate hierarchical CLAUDE.md files for your codebase:

```bash
# Preview what would be generated
trustable-ai context generate --dry-run

# Generate CLAUDE.md files (skips existing)
trustable-ai context generate

# Force overwrite existing files
trustable-ai context generate --force

# Limit depth of directory traversal
trustable-ai context generate --depth 2

# Build searchable context index
trustable-ai context index

# Look up relevant context for a task
trustable-ai context lookup "implement user authentication"
```

Context generation creates:
- Root `CLAUDE.md` with project overview and structure
- Directory-level `CLAUDE.md` for `src/`, `tests/`, `docs/`, etc.
- Module-level `CLAUDE.md` for significant subdirectories
- `.claude/context-index.yaml` for fast keyword-based lookups

### State Management

Workflows maintain state for re-entrancy:
- Resume from last checkpoint on failure
- Prevent duplicate work on retry
- Track created work items
- Persist errors with context

**Resume from within Claude Code:**
```
/workflow-resume
```

This will:
1. Scan for incomplete workflows
2. Show status, progress, and age of each
3. Let you select which to resume
4. Automatically continue from the last checkpoint

**Or use the CLI:**
```bash
# View workflow states
trustable-ai state list

# Resume interrupted workflow (outputs instructions)
trustable-ai state resume sprint-planning-sprint-10
```

### Skills System

Reusable capabilities for common tasks:
- Azure DevOps operations (enhanced CLI, bulk operations)
- Context loading and optimization
- Learnings capture
- Cross-repo coordination

### Learnings Capture

Capture institutional knowledge from development sessions:
```bash
trustable-ai learnings capture
trustable-ai learnings list
trustable-ai learnings archive
```

## Configuration

The `trustable-ai init` command creates `.claude/config.yaml` in your project. You can also create it manually:

```yaml
project:
  name: "your-project"
  type: "web-application"
  tech_stack:
    languages: ["Python", "TypeScript"]
    frameworks: ["FastAPI", "React"]
    platforms: ["Azure", "Docker"]
    databases: ["PostgreSQL"]

work_tracking:
  platform: "azure-devops"  # or "file-based"
  organization: "https://dev.azure.com/yourorg"
  project: "Your Project"
  credentials_source: "cli"  # uses 'az login'

  work_item_types:
    epic: "Epic"
    feature: "Feature"
    story: "User Story"
    task: "Task"
    bug: "Bug"

quality_standards:
  test_coverage_min: 80
  critical_vulnerabilities_max: 0
  high_vulnerabilities_max: 0
  code_complexity_max: 10

agent_config:
  models:
    architect: "claude-opus-4"
    engineer: "claude-sonnet-4.5"
    analyst: "claude-sonnet-4.5"

  enabled_agents:
    - senior-engineer
    - project-architect
    - software-developer

# Implementation tier affects quality expectations
# tier-0: Exploration/prototype
# tier-1: Intentful development (CI, tests)
# tier-2: Production ready
implementation_tier: "tier-0"
```

## CLI Reference

```bash
# Initialization (re-entrant)
trustable-ai init              # Initialize or update Trustable AI configuration
trustable-ai init --no-interactive  # Use defaults without prompts
trustable-ai validate          # Validate configuration
trustable-ai doctor            # Health check and diagnostics
trustable-ai status            # Overall status

# Agent Management
trustable-ai agent list            # List available agents
trustable-ai agent enable <name>   # Enable an agent
trustable-ai agent enable all      # Enable all agents
trustable-ai agent disable <name>  # Disable an agent
trustable-ai agent render <name>   # Render specific agent
trustable-ai agent render all      # Render all enabled agents
trustable-ai agent render-all      # Render all enabled agents to .claude/agents/
trustable-ai agent render-all --with-commands  # Also render agent slash commands
trustable-ai agent render-commands # Render agent slash commands to .claude/commands/

# Workflow Management
trustable-ai workflow list             # List available workflows
trustable-ai workflow render <name>    # Render specific workflow
trustable-ai workflow render-all       # Render all workflows to .claude/commands/

# State Management
trustable-ai state list            # List workflow states
trustable-ai state show <id>       # Show specific state
trustable-ai state resume <id>     # Resume interrupted workflow
trustable-ai state cleanup         # Clean up old state files

# Context Management
trustable-ai context generate      # Generate hierarchical CLAUDE.md files
trustable-ai context generate --dry-run  # Preview without creating files
trustable-ai context generate --force    # Overwrite existing files
trustable-ai context generate -d 2       # Limit depth
trustable-ai context index         # Build context index
trustable-ai context show          # Show loaded contexts
trustable-ai context lookup <task> # Find relevant context for a task

# Configuration
trustable-ai configure azure-devops    # Configure Azure DevOps
trustable-ai configure file-based      # Configure file-based tracking
trustable-ai configure quality         # Configure quality standards
```

## Work Tracking Platforms

### Azure DevOps

```bash
# Configure Azure DevOps
trustable-ai configure azure-devops

# Ensure you've logged in
az login
```

### File-Based (Zero Dependency)

For projects without external work tracking:
```bash
trustable-ai configure file-based
```

Tasks are stored in `.claude/tasks/` as YAML files.

## Architecture

```
.claude/
  config.yaml           # Main configuration
  agents/               # Rendered agent definitions (.md files)
  commands/             # Workflow and agent slash commands
  workflow-state/       # Execution state (re-entrancy)
  profiling/            # Performance profiles
  learnings/            # Session learnings
  context-index.yaml    # Searchable context index
  tasks/                # File-based task tracking

project-root/
  CLAUDE.md             # Root context file
  src/
    CLAUDE.md           # Source code context
  tests/
    CLAUDE.md           # Test suite context
```

### Hierarchical Context

Trustable AI uses hierarchical CLAUDE.md files to provide maximal context with minimal tokens:
- Root CLAUDE.md for project overview
- Module-level CLAUDE.md for specific areas
- Auto-generated context index for smart loading
- Use `trustable-ai context generate` to create the hierarchy automatically

## Development

```bash
# Clone repository
git clone https://github.com/keychain-io/trustable-ai
cd trustable-ai

# Install for development
pip install -e ".[dev]"

# Run tests
pytest

# Run specific test categories
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests

# Code quality
black . && ruff . && mypy .
```

## Requirements

- Python 3.9+
- Claude Code account
- Azure CLI (for Azure DevOps integration)

## License

MIT License - see LICENSE file for details.

## Links

- GitHub: https://github.com/keychain-io/trustable-ai
- Documentation: https://github.com/keychain-io/trustable-ai/blob/main/README.md
- Issues: https://github.com/keychain-io/trustable-ai/issues
- PyPI: https://pypi.org/project/trustable-ai/
