---
context:
  purpose: "AI-assisted software development framework that makes AI agent failures visible and recoverable through structured SDLC processes"
  problem_solved: "AI agents fail to reliably complete software development tasks - claiming completion without doing work, skipping verification, losing progress on crashes. Without structured workflows, explicit intent capture, and external verification, AI-assisted development is unreliable and untrustworthy."
  keywords: [project, overview, framework, trustable-ai, reliability, verification, sdlc]
  task_types: [any]
  priority: high
  max_tokens: 1500
  children:
    - path: .claude/CLAUDE.md
      when: [claude, runtime, workflow]
    - path: agents/CLAUDE.md
      when: [module, feature]
    - path: cli/CLAUDE.md
      when: [module, feature]
    - path: config/CLAUDE.md
      when: [config, configuration, settings]
    - path: core/CLAUDE.md
      when: [core, foundation, base]
    - path: docs/CLAUDE.md
      when: [docs, documentation, guide]
    - path: skills/CLAUDE.md
      when: [module, feature]
    - path: tests/CLAUDE.md
      when: [test, testing, pytest]
    - path: workflows/CLAUDE.md
      when: [module, feature]
  dependencies: []
---
# Trustable AI Development Workbench

## ⚠️ CRITICAL: For AI Agents Working On This Project

**VISION.md describes PROBLEMS TO SOLVE, not behaviors to emulate.**

When VISION.md says "AI agents routinely claim completion without doing work" or "skip verification steps" - those are **ANTI-PATTERNS** this framework prevents. As an AI agent working ON this project:

- ✅ **DO**: Verify all work is complete before marking tasks done
- ✅ **DO**: Query external sources of truth (Azure DevOps, file system) to verify work exists
- ✅ **DO**: Follow workflow verification gates explicitly - never skip them
- ✅ **DO**: Implement the SOLUTIONS described in VISION.md (verification gates, state persistence)
- ❌ **DO NOT**: Skip verification steps described in workflow templates
- ❌ **DO NOT**: Claim work is complete without external verification
- ❌ **DO NOT**: Reproduce the anti-patterns VISION.md describes

**You are building the solution to AI unreliability. Execute workflows with complete, programmatic verification.**

---

## Overview

Trustable AI is an AI-assisted software lifecycle framework that **solves the fundamental unreliability of AI coding agents** (VISION.md). Generic AI agents fail software development tasks by claiming completion without doing work, skipping verification steps, and losing progress when sessions crash.

**This framework doesn't make AI smarter - it makes AI failures visible and recoverable** through structured SDLC processes that catch errors early.

## Project Overview

Trustable AI is an AI-assisted software lifecycle framework featuring multi-agent orchestration, state management, and work tracking integration. It enables reliable software development with Claude Code through specialized agents, re-entrant workflows, and hierarchical context management.

**Current State (v1.2.0):**
- ✅ Configuration system with Pydantic validation
- ✅ Agent template rendering with project context injection (12 agents)
- ✅ Workflow template rendering (7 workflows)
- ✅ Work tracking platform adapters (Azure DevOps, file-based, extensible to Jira/GitHub)
- ✅ CLI (`trustable-ai`) for initialization, configuration, and management
- ✅ State management with re-entrancy support
- ✅ Profiling and analytics
- ✅ Skills system for reusable capabilities
- ✅ Learnings capture system

**Technology Stack:**
- Python 3.9+ (supports 3.9-3.12)
- Jinja2 for template rendering
- Pydantic for configuration validation
- Click for CLI
- PyYAML for config files
- pytest for testing

## Development Commands

### Installation and Setup
```bash
# Install for development
pip install -e ".[dev]"

# Install with specific work tracking platform support
pip install -e ".[azure]"      # Azure DevOps
pip install -e ".[jira]"        # Jira (planned)
pip install -e ".[github]"      # GitHub Issues (planned)
```

### Testing
```bash
# Run all tests with coverage
pytest

# Run specific test categories
pytest -m unit              # Unit tests only
pytest -m integration       # Integration tests
pytest -m azure             # Tests requiring Azure DevOps
pytest -m cli               # CLI command tests

# Run tests without coverage reporting
pytest --no-cov

# Run a single test file
pytest tests/test_config.py

# Run a specific test
pytest tests/test_config.py::test_load_config
```

### Code Quality
```bash
# Format code
black .

# Lint code
ruff .

# Type checking
mypy .

# Run all quality checks
black . && ruff . && mypy .
```

### CLI Commands
```bash
# Initialize framework in a project
trustable-ai init

# Configure work tracking platform
trustable-ai configure azure-devops    # For Azure DevOps
trustable-ai configure file-based       # For file-based tracking
trustable-ai configure jira             # For Jira (planned)
trustable-ai configure github           # For GitHub Issues (planned)

# Configure file-based tracking
trustable-ai configure file-based

# Manage agents
trustable-ai agent list                          # List available agents
trustable-ai agent enable <agent-name>           # Enable agent in config
trustable-ai agent disable <agent-name>          # Disable agent in config
trustable-ai agent render <agent-name> --show    # Render specific agent
trustable-ai agent render-all                    # Render all to .claude/agents/

# Manage workflows
trustable-ai workflow list                       # List available workflows
trustable-ai workflow render <name> --show       # Show rendered workflow
trustable-ai workflow render <name> -o file.md   # Save to file
trustable-ai workflow render-all                 # Render all to .claude/commands/

# State management
trustable-ai state list                          # List workflow states
trustable-ai state resume <id>                   # Resume interrupted workflow

# Validate configuration
trustable-ai validate

# Health check
trustable-ai doctor
```

## Architecture

### Core Components

**State Manager** (`core/state_manager.py`)
- Tracks workflow execution state across steps
- Enables checkpointing and resume capabilities
- Persists state to `.claude/workflow-state/`
- Critical for long-running workflows and recovery from failures

**Profiler** (`core/profiler.py`)
- Measures workflow performance and agent execution times
- Tracks token usage and API calls
- Generates performance reports in `.claude/profiling/`
- Use for optimizing workflow efficiency

**Context Loaders** (`core/context_loader.py`, `core/optimized_loader.py`)
- **context_loader.py**: Hierarchical CLAUDE.md file loading
  - Walks directory tree to find relevant context files
  - Supports keyword-based context selection
  - Token budget management for context optimization
- **optimized_loader.py**: Template-based context loading
  - Uses `.claude/context-index.yaml` for fast lookups
  - Matches tasks to pre-defined templates
  - Implements caching and analytics
  - Integrates with context pruner for intelligent loading

### Agent System

**Agent Registry** (`agents/registry.py`)
- Manages agent template rendering
- Loads Jinja2 templates from `agents/templates/`
- Injects project configuration (tech stack, quality standards, work tracking)
- Available agents (12 total):
  - `business-analyst.j2`: Requirements analysis, prioritization
  - `project-architect.j2`: Technical architecture, risk assessment
  - `security-specialist.j2`: Security review, vulnerability analysis
  - `senior-engineer.j2`: Task breakdown, story point estimation
  - `scrum-master.j2`: Workflow coordination, sprint management
  - `software-developer.j2`: Feature implementation, bug fixes
  - `qa-engineer.j2`: Test planning, quality validation
  - `devops-developer.j2`: CI/CD, infrastructure automation
  - `project-manager.j2`: Project coordination
  - `general-engineer.j2`: Cross-functional tasks
  - `qa-tester.j2`: Test execution
  - `prototype-engineer.j2`: Rapid prototyping

**Template Rendering Flow:**
1. Load configuration from `.claude/config.yaml`
2. Build context with tech stack, quality standards, work tracking config
3. Render agent template with injected context
4. Agent prompts adapt to your specific tech stack and standards

### Configuration System

**Schema** (`config/schema.py`)
- Pydantic models for type-safe configuration validation
- Key models:
  - `ProjectConfig`: Project type, tech stack, directories
  - `WorkTrackingConfig`: Platform adapter settings, field mappings
  - `QualityStandards`: Test coverage, vulnerability thresholds, complexity limits
  - `AgentConfig`: Agent models, enabled agents
  - `WorkflowConfig`: State management, profiling, checkpointing
  - `DeploymentConfig`: Environment settings, deployment tasks

**Loader** (`config/loader.py`)
- Loads and validates `.claude/config.yaml`
- Provides default values for optional settings
- Validates against schema before use

### Workflow System

**Templates** (`workflows/templates/`)
- Jinja2 templates that define workflow steps
- Available workflows:
  - `sprint-planning.j2`: Complete sprint planning automation
  - `sprint-execution.j2`: Sprint progress monitoring
  - `sprint-completion.j2`: Sprint closure and retrospective data
  - `sprint-retrospective.j2`: Retrospective analysis
  - `backlog-grooming.j2`: Backlog refinement
  - `daily-standup.j2`: Daily standup reports
  - `dependency-management.j2`: Dependency analysis and tracking
  - `workflow-resume.j2`: Resume incomplete workflows from within Claude Code

**Workflow Usage:**
1. Render workflow template: `trustable-ai workflow render sprint-planning --show`
2. Render all workflows to slash commands: `trustable-ai workflow render-all`
3. Use slash commands in Claude Code (e.g., `/sprint-planning`)
4. Claude Code follows the instructions using configured agents
5. State is persisted for re-entrancy (resume on failure)
6. Use `/workflow-resume` to list and resume incomplete workflows

### Platform Adapters

**Work Tracking Integration** (`adapters/`)

The framework uses pluggable adapters for work tracking platforms:

- **Azure DevOps** (`adapters/azure_devops/`) - Complete implementation
- **File-based** (built-in) - Zero-dependency local tracking
- **Jira** (planned) - Extensible design ready for implementation
- **GitHub Issues** (planned) - Extensible design ready for implementation

**Adapter Architecture:**
- Generic interface: All adapters implement same work item CRUD operations
- Field mapping: Generic fields → platform-specific fields
- Type mapping: Generic work item types → platform-specific types
- Custom fields: Configurable per-project in `.claude/config.yaml`

**Adding New Platforms:**
1. Create `adapters/<platform>/` directory
2. Implement adapter interface (work item CRUD, query, sprint management)
3. Add field/type mappers for platform
4. Add tests in `tests/integration/`

## Configuration File Structure

The framework expects a `.claude/config.yaml` file in the target project:

```yaml
project:
  name: "your-project"
  type: "web-application"  # or api, library, cli-tool, etc.
  tech_stack:
    languages: ["Python", "TypeScript"]
    frameworks: ["FastAPI", "React"]
    platforms: ["Azure", "Docker"]
    databases: ["PostgreSQL"]

work_tracking:
  platform: "azure-devops"  # or "file-based", "jira", "github"
  organization: "https://dev.azure.com/yourorg"  # Platform-specific
  project: "Your Project"
  credentials_source: "cli"  # Platform-specific: "cli", "env:VAR_NAME", etc.

  work_item_types:
    epic: "Epic"              # Platform-specific type names
    feature: "Feature"
    task: "Task"
    bug: "Bug"

  custom_fields:
    business_value: "Custom.BusinessValueScore"
    technical_risk: "Custom.TechnicalRisk"

  iteration_format: "{project}\\{sprint}"
  sprint_naming: "Sprint {number}"

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
    - business-analyst
    - project-architect
    - senior-engineer
    - scrum-master
```

## Key Design Patterns

### Template-Based Configuration
- All agents, workflows, and tasks use Jinja2 templates
- Templates are rendered with project-specific configuration
- Allows framework to adapt to any tech stack, platform, standards
- Customize by editing templates in your project's `.claude/` directory

### Hierarchical Context Loading
- Context files (CLAUDE.md) can exist at multiple levels
- Framework walks directory tree collecting relevant context
- Reduces token usage by loading only relevant context
- Use `core/context_loader.py` functions for context management

### State Management and Checkpointing
- All workflows persist state after each step
- Enables resume from last checkpoint on failure
- State files stored in `.claude/workflow-state/`
- Critical for reliability in production workflows

### Platform Abstraction
- Generic work item types (epic, feature, task) map to platform-specific types
- Generic field names map to platform-specific custom fields
- Adapters handle platform-specific implementation details
- Easy to add new platforms without changing workflow logic

## Testing Strategy

**Test Organization:**
- `tests/unit/`: Fast tests, no external dependencies
- `tests/integration/`: Tests requiring external services
- `tests/fixtures/`: Shared test fixtures and mock data

**Test Markers:**
- `@pytest.mark.unit`: Fast unit tests
- `@pytest.mark.integration`: Integration tests
- `@pytest.mark.azure`: Tests requiring Azure DevOps configuration
- `@pytest.mark.cli`: CLI command tests
- `@pytest.mark.slow`: Long-running tests

**Coverage Requirements:**
- Minimum 80% coverage (enforced by quality standards)
- Coverage reports in `htmlcov/` and `coverage.xml`
- Use `--cov-report=term-missing` to see uncovered lines

## Common Workflows

### Adding a New Agent
1. Create template in `agents/templates/<agent-name>.j2`
2. Use Jinja2 variables: `{{ project.tech_stack }}`, `{{ quality_standards }}`, etc.
3. Add agent to `enabled_agents` in configuration
4. Test with `trustable-ai agent enable <agent-name>`

### Adding a New Workflow
1. Create template in `workflows/templates/<workflow-name>.j2`
2. Define workflow steps with agent calls
3. Include state checkpoints between steps
4. Test with `trustable-ai workflow render <workflow-name> --show`

### Adding a Platform Adapter
1. Create directory `adapters/<platform>/`
2. Implement core operations: create, read, update, query work items
3. Implement field and type mapping
4. Add platform validation in `config/schema.py`
5. Add tests in `tests/integration/`

### Debugging Workflow Issues
1. Check state files in `.claude/workflow-state/`
2. Review profiling reports in `.claude/profiling/`
3. Enable debug logging in workflow execution
4. Use `trustable-ai validate` to check configuration
5. Test individual agents before running full workflows

## Work Tracking Adapter Usage (CRITICAL)

**⚠️ MANDATORY: Always use the work tracking adapter, NEVER use `az boards` CLI directly**

### Why Use the Adapter
- **Platform abstraction**: Works with Azure DevOps, file-based, Jira, GitHub Issues
- **Type safety**: Consistent interface across all platforms
- **Testability**: Mockable for unit tests
- **REST API**: Direct API calls, no CLI subprocess overhead
- **Error handling**: Unified error handling and retry logic
- **Programmatic**: Python-native, not shell commands

### Correct Usage Pattern

```python
# ✅ CORRECT: Use the adapter
import sys
sys.path.insert(0, '.claude/skills')
from work_tracking import get_adapter
from workflows.utilities import (
    analyze_sprint,
    verify_work_item_states,
    get_recent_activity,
    identify_blockers
)

adapter = get_adapter()
items = adapter.query_sprint_work_items("Sprint 6")
sprint_stats = analyze_sprint(adapter, "Sprint 6")
```

```bash
# ❌ INCORRECT: Do not use az boards CLI
az boards work-item show --id 1234  # DEPRECATED
az boards query                      # DEPRECATED
```

### Available Adapter Methods
- `create_work_item()`: Create work items
- `get_work_item()`: Get work item by ID
- `update_work_item()`: Update work item fields
- `query_work_items()`: Query with filters
- `query_sprint_work_items()`: Get all items in sprint
- `list_sprints()`: List available sprints
- `link_work_items()`: Create parent-child relationships

### Available Workflow Utilities
- `analyze_sprint(adapter, sprint_name)`: Comprehensive sprint analysis
- `verify_work_item_states(adapter, items)`: External source of truth verification
- `get_recent_activity(adapter, sprint_name, hours)`: Recent changes
- `identify_blockers(adapter, sprint_name, stale_threshold_days)`: Blocker detection

### Exception: Pre-Approved Commands Only
The only `az boards` commands allowed are those explicitly listed in `.claude/settings.local.json` under approved commands. These are limited to:
- Read-only operations: `az boards work-item show`, `az boards query`
- Status checks: `az boards work-item list`

**Even for these, prefer the adapter when possible.**

## Important Notes

- **Work Tracking Platforms:** Framework supports multiple platforms (Azure DevOps, file-based, extensible to Jira/GitHub)
  - Azure DevOps: Adapter uses REST API v7.1 with PAT token authentication (no CLI required)
  - File-based: Zero dependencies, local YAML files
  - Platform-specific configuration in `.claude/config.yaml`
  - **Always use the adapter**, not direct CLI commands
- **State Persistence:** Workflow state is persisted to disk. Clean up old state files periodically with `trustable-ai state cleanup`.
- **Token Budgets:** Context loaders respect token budgets. Adjust `max_tokens` parameter based on workflow needs.
- **Template Customization:** After `trustable-ai init`, templates are copied to project's `.claude/` directory for customization.
- **Agent Models:** Different agents can use different Claude models (Opus for architecture, Sonnet for engineering).
