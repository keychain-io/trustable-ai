# workflows

## Purpose

Workflow registry and template rendering system. This module manages multi-step workflow definitions (sprint planning, backlog grooming, etc.) and renders them as slash commands for Claude Code.

## Key Components

- **registry.py**: `WorkflowRegistry` class for loading, rendering, and managing workflow templates
- **templates/**: Jinja2 templates for workflows (sprint-planning.j2, sprint-execution.j2, etc.)
- **__init__.py**: Module exports for WorkflowRegistry and convenience functions

## Architecture

The workflow system uses template-based configuration to create executable workflows:

1. **Template Loading**: Jinja2 templates loaded from `templates/` directory
2. **Context Injection**: Project config (tech stack, quality standards, work tracking) injected into templates
3. **Workflow Rendering**: Templates rendered to Markdown slash commands for Claude Code
4. **State Management**: Workflows integrate with core.state_manager for checkpointing
5. **Profiling**: Workflows integrate with core.profiler for performance tracking

### WorkflowRegistry Methods

```python
registry = WorkflowRegistry(config)
registry.list_workflows()                    # List all available workflows
registry.render_workflow("sprint-planning")  # Render specific workflow
registry.save_rendered_workflow(name, dir)   # Save to file
```

## Available Workflows

Templates in `templates/` directory:
- **sprint-planning.j2**: Complete sprint planning automation (analyst, architect, engineer roles)
- **sprint-execution.j2**: Sprint progress monitoring and daily standups
- **sprint-completion.j2**: Sprint closure and retrospective data collection
- **sprint-retrospective.j2**: Retrospective analysis and action items
- **backlog-grooming.j2**: Backlog refinement and prioritization
- **daily-standup.j2**: Automated daily standup report generation
- **dependency-management.j2**: Dependency analysis and tracking
- **workflow-resume.j2**: Resume incomplete workflows from checkpoints
- **context-generation.j2**: Generate focused context for tasks

## Workflow Structure

Each workflow template typically includes:

1. **Workflow Metadata**: Name, description, inputs, outputs
2. **Agent Sequence**: Ordered list of agents to invoke (analyst → architect → engineer)
3. **State Checkpoints**: Save state after each step for re-entrancy
4. **Work Item Creation**: Use platform adapter to create work items
5. **Verification**: Verify work items were created successfully
6. **Profiling**: Track performance and cost estimates
7. **Output**: Final deliverables (work item IDs, sprint backlog, etc.)

Example workflow steps:
```markdown
1. Initialize state and profiler
2. Execute Business Analyst agent
3. Checkpoint state, save analyst output
4. Execute Project Architect agent
5. Checkpoint state, save architect output
6. Execute Senior Engineer agent
7. Create work items in Azure DevOps
8. Verify work items created
9. Complete workflow, save profiling report
```

## Template Context Variables

Templates have access to:
- `project`: name, type, tech_stack, directories
- `work_tracking`: platform, organization, work_item_types, custom_fields
- `quality_standards`: test coverage, vulnerability thresholds, complexity limits
- `agent_config`: models, enabled_agents
- `workflow_config`: state_directory, profiling_directory, checkpoint_enabled, max_retries
- `deployment_config`: environments, task types
- `config`: Full FrameworkConfig object for complex logic

## Usage Examples

```python
from workflows import WorkflowRegistry, load_workflow
from config import load_config

# Load and render workflow
config = load_config()
registry = WorkflowRegistry(config)
workflow_md = registry.render_workflow("sprint-planning")

# Save all workflows as slash commands
for workflow in registry.list_workflows():
    registry.save_rendered_workflow(workflow, Path(".claude/commands"))

# Use rendered workflow in Claude Code
# 1. Render workflows: trustable-ai workflow render-all
# 2. In Claude Code: /sprint-planning
```

## Workflow Re-entrancy

Workflows support checkpointing and resume:

1. **State Persistence**: Workflow state saved to `.claude/workflow-state/`
2. **Step Tracking**: Each step marked as completed after execution
3. **Resume**: On failure, workflow resumes from last checkpoint
4. **Work Item Tracking**: All created work items tracked for cleanup

Resume workflow using:
```bash
# In Claude Code
/workflow-resume  # Lists incomplete workflows and allows selection
```

## Creating New Workflows

To create a new workflow:

1. **Create Template**: Add `.j2` file to `workflows/templates/`
2. **Define Workflow**: Specify agent sequence, inputs, outputs
3. **Add State Management**: Use WorkflowState for checkpointing
4. **Add Profiling**: Use WorkflowProfiler for tracking
5. **Test**: Render and test the workflow
6. **Deploy**: Run `trustable-ai workflow render-all` to deploy

Example template structure:
```jinja2
# My Workflow

## Overview
Description of what this workflow does.

## Steps

### Step 1: Initialize
```python
from core.state_manager import WorkflowState
from core.profiler import WorkflowProfiler

state = WorkflowState("my-workflow", workflow_id)
profiler = WorkflowProfiler("my-workflow")
```

### Step 2: Execute Agent
Execute the business analyst agent...

### Step 3: Create Work Items
Create work items using platform adapter...
```

## Conventions

- **Template Naming**: Use kebab-case (sprint-planning.j2)
- **Slash Commands**: Workflows rendered to `.claude/commands/` as `{name}.md`
- **State Files**: Named `{workflow-name}-{workflow-id}.json`
- **Profiling Reports**: Named `{workflow-name}-{timestamp}.md`
- **Idempotency**: Always check step completion before executing
- **Error Handling**: Record errors in state for debugging

## Integration Points

- **State Manager**: Checkpoint after each step
- **Profiler**: Track agent execution time and costs
- **Platform Adapter**: Create/query work items
- **Context Loader**: Load relevant context for agents
- **Skills**: Invoke skills for specific capabilities

## Testing

```bash
pytest tests/unit/test_workflow_registry.py  # Test workflow rendering
pytest tests/integration/test_cli_workflow.py  # Test workflow commands
```
