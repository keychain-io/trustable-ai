---
context:
  keywords: [trustable-ai, framework, project, overview]
  task_types: [any]
  priority: high
  max_tokens: 1500
  children:
    - path: agents/CLAUDE.md
      when: [agent, analyst, architect, engineer, scrum, qa, devops, security]
    - path: workflows/CLAUDE.md
      when: [workflow, sprint, planning, execution, standup, retrospective, backlog]
    - path: adapters/azure_devops/CLAUDE.md
      when: [azure, devops, work-item, wiql, iteration, sprint]
    - path: core/CLAUDE.md
      when: [state, profiler, context, loader, checkpoint, resume]
    - path: config/CLAUDE.md
      when: [config, configuration, schema, yaml, settings]
    - path: cli/CLAUDE.md
      when: [cli, command, trustable-ai, init, validate, doctor]
    - path: skills/CLAUDE.md
      when: [skill, capability, plugin]
    - path: tests/CLAUDE.md
      when: [test, testing, pytest, coverage, fixture]
    - path: .claude/CLAUDE.md
      when: [claude, runtime, state, profiling, commands]
---
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Trustable AI is an AI-assisted software lifecycle framework featuring multi-agent orchestration, state management, and work tracking integration. It enables reliable software development with Claude Code through specialized agents, re-entrant workflows, and hierarchical context management.

**Current State (v1.1.0):**
- ✅ Configuration system with Pydantic validation
- ✅ Agent template rendering with project context injection (12 agents)
- ✅ Workflow template rendering (7 workflows)
- ✅ Azure DevOps adapter for work item operations
- ✅ File-based task tracking adapter
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

# Install with Azure DevOps support
pip install -e ".[azure]"
```

### Testing
```bash
# Run all tests with coverage
pytest

# Run specific test categories
pytest -m unit              # Unit tests only
pytest -m integration       # Integration tests
pytest -m azure             # Azure DevOps tests
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

# Configure Azure DevOps
trustable-ai configure azure-devops

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

**Azure DevOps** (`adapters/azure_devops/`)
- Complete integration with Azure DevOps work items
- Components:
  - `cli_wrapper.py`: Wraps Azure CLI for work item operations
  - `field_mapper.py`: Maps generic fields to Azure DevOps fields
  - `type_mapper.py`: Maps generic work item types to Azure DevOps types
  - `bulk_operations.py`: Efficient bulk work item operations
- Uses Azure CLI credentials (requires `az login`)
- Supports custom fields via configuration

**Extensibility:**
- Create adapters for Jira, GitHub Projects by implementing same interface
- Place in `adapters/<platform>/` directory
- Implement work item CRUD, query, sprint management

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
  platform: "azure-devops"
  organization: "https://dev.azure.com/yourorg"
  project: "Your Project"
  credentials_source: "cli"  # or "env:VAR_NAME"

  work_item_types:
    epic: "Epic"
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

## Important Notes

- **Credentials:** Azure DevOps adapter uses Azure CLI credentials. Ensure `az login` is completed before running workflows.
- **Organization URL Format:** The organization URL must be the full Azure DevOps URL (e.g., `https://dev.azure.com/yourorg`), not just the organization name.
- **State Persistence:** Workflow state is persisted to disk. Clean up old state files periodically with `trustable-ai state cleanup`.
- **Token Budgets:** Context loaders respect token budgets. Adjust `max_tokens` parameter based on workflow needs.
- **Template Customization:** After `trustable-ai init`, templates are copied to project's `.claude/` directory for customization.
- **Agent Models:** Different agents can use different Claude models (Opus for architecture, Sonnet for engineering).
- **File-Based Tracking:** Use `trustable-ai configure file-based` for zero-dependency task management.
