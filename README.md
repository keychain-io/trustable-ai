# Trusted AI Development (TAID)

An AI-assisted software lifecycle framework featuring multi-agent orchestration, state management, and work tracking integration. Build real software projects reliably with Claude Code.

## Overview

Trusted AI Development (TAID) provides a sophisticated system for managing AI-assisted software development workflows. It coordinates specialized AI agents to handle complex development tasks while maintaining context, state, and integration with your work tracking platform.

**Key Capabilities:**
- Multi-agent orchestration with 13 specialized agents
- Re-entrant workflows with state persistence
- Re-entrant initialization (update settings without re-entering everything)
- Hierarchical context management with auto-generated CLAUDE.md files
- Integration with Azure DevOps, file-based tracking (Jira/GitHub planned)
- Skills system for reusable capabilities
- Learnings capture for institutional knowledge

## Installation

```bash
pip install trusted-ai-dev
```

With Azure DevOps support:
```bash
pip install trusted-ai-dev[azure]
```

For development:
```bash
pip install -e ".[dev]"
```

## Quick Start

### Initialize in Your Project

```bash
cd your-project/
taid init
```

The interactive init wizard will:
1. Prompt for project information (name, type, tech stack)
2. Configure your work tracking platform
3. Create `.claude/` directory structure
4. Let you select which agents to enable (by number, 'all', or keep defaults)
5. Optionally render agents and workflows to `.claude/`
6. Optionally generate hierarchical CLAUDE.md context files

**Re-entrant:** Running `taid init` again loads existing values as defaults, so you can update individual settings without re-entering everything.

### Non-Interactive Mode

```bash
# Initialize with all defaults
taid init --no-interactive
```

### Agent and Workflow Management

```bash
# List available agents
taid agent list

# Enable agents (individually or all at once)
taid agent enable senior-engineer
taid agent enable all

# Render all enabled agents to .claude/agents/
taid agent render-all

# Also render agent slash commands to .claude/commands/
taid agent render-all --with-commands

# Or render commands separately
taid agent render-commands

# Render workflows to .claude/commands/
taid workflow render-all

# Validate your setup
taid validate
```

### Use with Claude Code

After rendering, use the slash commands in Claude Code:
- `/sprint-planning` - Plan your sprint with multi-agent orchestration
- `/daily-standup` - Generate daily standup reports
- `/backlog-grooming` - Review and prioritize backlog items
- `/senior-engineer` - Invoke the senior engineer agent with fresh context
- `/software-developer` - Invoke the developer agent with fresh context

## Features

### Multi-Agent System (13 Agents)

| Agent | Description | Model |
|-------|-------------|-------|
| **business-analyst** | Requirements analysis, business value scoring | sonnet |
| **project-architect** | Technical architecture, risk assessment | opus |
| **security-specialist** | Security review, vulnerability analysis | sonnet |
| **senior-engineer** | Task breakdown, estimation, code review | sonnet |
| **software-developer** | Feature implementation, bug fixes | sonnet |
| **qa-engineer** | Test planning, quality validation | sonnet |
| **devops-developer** | CI/CD, infrastructure automation | sonnet |
| **scrum-master** | Sprint coordination, workflow management | sonnet |
| **project-manager** | Project planning, stakeholder communication | sonnet |
| **general-engineer** | Cross-functional development tasks | sonnet |
| **qa-tester** | Test execution, defect tracking | haiku |
| **prototype-engineer** | Rapid prototyping, exploration | sonnet |
| **documentation-specialist** | CLAUDE.md generation, code documentation | sonnet |

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

TAID can automatically generate hierarchical CLAUDE.md files for your codebase:

```bash
# Preview what would be generated
taid context generate --dry-run

# Generate CLAUDE.md files (skips existing)
taid context generate

# Force overwrite existing files
taid context generate --force

# Limit depth of directory traversal
taid context generate --depth 2

# Build searchable context index
taid context index

# Look up relevant context for a task
taid context lookup "implement user authentication"
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
taid state list

# Resume interrupted workflow (outputs instructions)
taid state resume sprint-planning-sprint-10
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
taid learnings capture
taid learnings list
taid learnings archive
```

## Configuration

The `taid init` command creates `.claude/config.yaml` in your project. You can also create it manually:

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
taid init              # Initialize or update TAID configuration
taid init --no-interactive  # Use defaults without prompts
taid validate          # Validate configuration
taid doctor            # Health check and diagnostics
taid status            # Overall status

# Agent Management
taid agent list            # List available agents
taid agent enable <name>   # Enable an agent
taid agent enable all      # Enable all agents
taid agent disable <name>  # Disable an agent
taid agent render <name>   # Render specific agent
taid agent render all      # Render all enabled agents
taid agent render-all      # Render all enabled agents to .claude/agents/
taid agent render-all --with-commands  # Also render agent slash commands
taid agent render-commands # Render agent slash commands to .claude/commands/

# Workflow Management
taid workflow list             # List available workflows
taid workflow render <name>    # Render specific workflow
taid workflow render-all       # Render all workflows to .claude/commands/

# State Management
taid state list            # List workflow states
taid state show <id>       # Show specific state
taid state resume <id>     # Resume interrupted workflow
taid state cleanup         # Clean up old state files

# Context Management
taid context generate      # Generate hierarchical CLAUDE.md files
taid context generate --dry-run  # Preview without creating files
taid context generate --force    # Overwrite existing files
taid context generate -d 2       # Limit depth
taid context index         # Build context index
taid context show          # Show loaded contexts
taid context lookup <task> # Find relevant context for a task

# Configuration
taid configure azure-devops    # Configure Azure DevOps
taid configure file-based      # Configure file-based tracking
taid configure quality         # Configure quality standards
```

## Work Tracking Platforms

### Azure DevOps

```bash
# Configure Azure DevOps
taid configure azure-devops

# Ensure you've logged in
az login
```

### File-Based (Zero Dependency)

For projects without external work tracking:
```bash
taid configure file-based
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

TAID uses hierarchical CLAUDE.md files to provide maximal context with minimal tokens:
- Root CLAUDE.md for project overview
- Module-level CLAUDE.md for specific areas
- Auto-generated context index for smart loading
- Use `taid context generate` to create the hierarchy automatically

## Development

```bash
# Clone repository
git clone https://github.com/trusted-ai-dev/trusted-ai-dev
cd trusted-ai-dev

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

- Documentation: https://trusted-ai-dev.github.io
- Issues: https://github.com/trusted-ai-dev/trusted-ai-dev/issues
- PyPI: https://pypi.org/project/trusted-ai-dev/
