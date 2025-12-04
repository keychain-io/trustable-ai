# Documentation Templates

## Purpose

This directory contains Jinja2 templates for generating problem-focused CLAUDE.md documentation files throughout the Trustable AI Workbench codebase.

## Problem Solved

AI agents fail to grasp project intent when documentation is feature-focused ("what it does") instead of problem-focused ("why it exists"). These templates enforce a problem-first narrative that references VISION.md problem pillars, helping AI understand both what components do AND why they matter.

## Available Templates

### 1. core-module.j2
For core framework modules like `state_manager.py`, `profiler.py`, `context_loader.py`

**Use when**: Documenting foundational modules that other components depend on

**Key variables**:
- `module_name`: Python module name
- `display_name`: Human-readable name
- `vision_problems`: VISION.md problems this solves
- `problem_statement`: What problem this solves
- `solution_approach`: How it solves it
- `keywords`: Context loading keywords
- `components`: Key classes/functions

### 2. agent.j2
For agent definitions like Business Analyst, Project Architect, etc.

**Use when**: Documenting specialized agents used in workflows

**Key variables**:
- `agent_name`: Agent identifier (e.g., "business-analyst")
- `problem_statement`: What problem this agent solves
- `capabilities`: List of agent capabilities
- `workflow_integration`: How agent fits into workflows
- `context_inputs`: What context the agent receives
- `outputs`: What the agent returns

### 3. workflow.j2
For workflow definitions like Sprint Planning, Backlog Grooming, etc.

**Use when**: Documenting multi-step workflows with agent orchestration

**Key variables**:
- `workflow_name`: Workflow identifier
- `problem_statement`: What workflow problem this solves
- `phases`: Workflow phases with steps
- `agents_used`: Agents orchestrated
- `verification_points`: Where verification happens
- `state_items`: What's persisted in state

### 4. adapter.j2
For platform adapters like Azure DevOps, Jira, etc.

**Use when**: Documenting platform integrations

**Key variables**:
- `adapter_name`: Adapter identifier
- `platform_name`: Platform being integrated
- `operations`: Supported operations
- `authentication_description`: How auth works
- `field_mappings`: Generic to platform field mappings

### 5. config.j2
For configuration modules like `schema.py`, `loader.py`

**Use when**: Documenting configuration validation and loading

**Key variables**:
- `module_name`: Config module name
- `configuration_models`: Pydantic models
- `validation_rules`: Validation rules enforced
- `usage_example`: YAML config example

### 6. skill.j2
For reusable skills like the Azure DevOps skill

**Use when**: Documenting reusable operation bundles

**Key variables**:
- `skill_name`: Skill identifier
- `capabilities`: What the skill can do
- `usage_patterns`: Common usage patterns
- `verification_patterns`: Verification support

### 7. cli.j2
For CLI command modules

**Use when**: Documenting CLI commands

**Key variables**:
- `command_name`: Command name
- `subcommands`: List of subcommands
- `usage_examples`: Common usage examples
- `error_cases`: Common errors and solutions

## Usage

### Manual Rendering

```python
from jinja2 import Environment, FileSystemLoader
import yaml

# Load template
env = Environment(loader=FileSystemLoader('templates/documentation'))
template = env.get_template('core-module.j2')

# Prepare context
context = {
    'module_name': 'state_manager',
    'display_name': 'State Manager',
    'vision_problems': ['workflow fragility', 'memory limitations'],
    'problem_statement': 'Long-running workflows fail unpredictably when sessions timeout...',
    'solution_approach': 'State manager persists workflow progress to disk...',
    'keywords': ['state', 'checkpoint', 'recovery', 'workflow'],
    'task_types': ['implementation', 'debugging', 'workflow'],
    'components': [
        {'name': 'WorkflowState', 'description': 'Tracks workflow execution state'},
        {'name': 'save_checkpoint', 'description': 'Persists state to disk'}
    ],
    'usage_example': '''from core.state_manager import WorkflowState
state = WorkflowState(workflow_id="sprint-planning-001")
state.save_checkpoint(step=2, data={"backlog": [...]})'''
}

# Render
output = template.render(context)

# Save
with open('core/CLAUDE.md', 'w') as f:
    f.write(output)
```

### CLI Integration (Planned)

```bash
# Render documentation for a module
trustable-ai docs render core/state_manager.py --template core-module

# Validate existing documentation
trustable-ai docs validate core/CLAUDE.md

# Scan for missing or stale documentation
trustable-ai docs scan
```

## Schema Reference

All templates produce CLAUDE.md files conforming to the schema defined in `SCHEMA.md`.

**Required front matter fields:**
- `purpose`: Problem-focused summary (auto-generated from problem_statement)
- `problem_solved`: Detailed problem explanation
- `keywords`: Context loading keywords
- `task_types`: Task types this helps with

**Document sections:**
- **Purpose**: Problem statement → Solution approach → VISION.md references
- **Key Components**: Components/classes/functions
- **Architecture**: How it fits in the system
- **Usage**: Code examples
- **Important Notes**: Gotchas, best practices
- **Related**: Links to related docs and VISION.md

## Template Design Principles

### 1. Problem-First Narrative
Every template starts with the problem being solved, not the features being provided.

❌ **Feature-focused**: "Provides state management for workflows"
✅ **Problem-focused**: "Solves workflow fragility - workflows fail when sessions timeout"

### 2. VISION.md References
Templates explicitly link to VISION.md problem pillars so AI understands why components exist.

### 3. Verification Guidance
Templates emphasize verification points - how to verify claimed functionality actually works.

### 4. Fresh Context Pattern
Agent and workflow templates explain the fresh context pattern and why it matters.

### 5. External Source of Truth
Adapter templates emphasize that external systems (not AI claims) are the source of truth.

## Validation

Generated documentation should be validated with:

```bash
trustable-ai validate documentation
```

Validation checks:
- Required front matter fields present
- Problem-focused language (not feature-focused)
- VISION.md references where applicable
- Sections not empty or just "See README.md"

## Related

- **SCHEMA.md**: Front matter schema and structure requirements
- **VISION.md**: Problem pillars that documentation references
- **Task 1005**: Use these templates to enhance core module documentation
- **Task 1008**: Build validation tooling based on this schema
