# core

## Purpose

Core framework components for workflow execution, state management, context loading, and profiling. These modules provide the foundation for reliable, observable, and efficient AI-assisted workflows.

## Key Components

- **state_manager.py**: `WorkflowState` class for workflow checkpointing and re-entrancy
- **profiler.py**: `WorkflowProfiler` class for performance monitoring and cost analysis
- **context_loader.py**: Hierarchical CLAUDE.md file loading for context management
- **optimized_loader.py**: Template-based context loading with caching
- **__init__.py**: Module exports

## Architecture

### State Management (state_manager.py)

**WorkflowState** class provides re-entrant workflow execution:

**Key Features**:
- **Checkpointing**: Save workflow state after each step
- **Resume**: Resume from last checkpoint on failure
- **Work Item Tracking**: Track all created work items for cleanup/rollback
- **Error Logging**: Record errors with context for debugging
- **Idempotency**: Check if step already completed before re-running

**State File Structure**: `.claude/workflow-state/{workflow-name}-{workflow-id}.json`
```json
{
  "workflow_name": "sprint-planning",
  "workflow_id": "sprint-10",
  "status": "in_progress",
  "current_step": {"name": "architect", "started_at": "..."},
  "completed_steps": [{"name": "analyst", "completed_at": "...", "result": {...}}],
  "created_work_items": [{"id": 123, "created_at": "...", "data": {...}}],
  "errors": [],
  "metadata": {}
}
```

**Usage**:
```python
from core.state_manager import WorkflowState

state = WorkflowState("sprint-planning", "sprint-10")

if not state.is_step_completed("business-analyst"):
    state.start_step("business-analyst")
    # Execute step...
    state.complete_step("business-analyst", result={"features": [...]})

state.complete_workflow()
```

### Profiling (profiler.py)

**WorkflowProfiler** class tracks performance metrics:

**Metrics Tracked**:
- **Timing**: Duration of each agent call
- **Token Estimates**: Input/output token counts (estimated)
- **Cost Estimates**: API costs based on Claude pricing
- **Success Rate**: Track successful vs failed calls
- **Bottleneck Detection**: Identify slowest/most expensive operations

**Model Pricing** (as of 2025):
- Opus: $15/1M input, $75/1M output
- Sonnet: $3/1M input, $15/1M output
- Haiku: $0.25/1M input, $1.25/1M output

**Usage**:
```python
from core.profiler import WorkflowProfiler

profiler = WorkflowProfiler("sprint-planning")

call_data = profiler.start_agent_call("business-analyst", task_desc, model="sonnet")
# Execute agent...
profiler.complete_agent_call(call_data, success=True, output_length=5000)

profiler.save_report()  # Saves to .claude/profiling/
profiler.print_summary()
```

**Reports Generated**:
- Markdown report: `.claude/profiling/{workflow}-{timestamp}.md`
- JSON data: `.claude/profiling/{workflow}-{timestamp}.json`

### Context Loading (context_loader.py)

Hierarchical CLAUDE.md file loading for focused context:

**Key Functions**:
- `load_hierarchical_context(working_dir)`: Load all CLAUDE.md files from working directory to repo root
- `get_context_for_task(task_description)`: Load context based on keyword matching
- `get_focused_context(task_description, max_tokens)`: Load context with token budget
- `list_available_contexts()`: List all CLAUDE.md files in project
- `estimate_token_count(text)`: Estimate token usage (~4 chars per token)

**Context Hierarchy**:
```
repo_root/CLAUDE.md          # General project context
  src/CLAUDE.md              # Source code context
    module/CLAUDE.md         # Module-specific context
```

**Keyword Mapping**: Maps task keywords to relevant context files (e.g., "test" -> tests/CLAUDE.md)

**Usage**:
```python
from core.context_loader import get_context_for_task, get_focused_context

# Load context for task
context = get_context_for_task("Implement MCP tool for persona creation")

# Load with token budget
context = get_focused_context("Write integration tests", max_tokens=2000)
```

### Optimized Context Loading (optimized_loader.py)

Template-based context loading with caching and analytics:
- Uses `.claude/context-index.yaml` for fast lookups
- Matches tasks to pre-defined templates
- Implements caching for repeated loads
- Integrates with context pruner for intelligent loading

## Common Patterns

### Workflow with State and Profiling
```python
from core.state_manager import WorkflowState
from core.profiler import WorkflowProfiler

# Initialize state and profiler
state = WorkflowState("sprint-planning", "sprint-10")
profiler = WorkflowProfiler("sprint-planning")

# Execute steps with checkpointing
for step in ["analyst", "architect", "engineer"]:
    if not state.is_step_completed(step):
        state.start_step(step)

        # Profile the agent call
        call_data = profiler.start_agent_call(step, task, model="sonnet")
        try:
            result = execute_agent(step, task)
            profiler.complete_agent_call(call_data, success=True)
            state.complete_step(step, result=result)
        except Exception as e:
            profiler.complete_agent_call(call_data, success=False, error=str(e))
            state.record_error(str(e), context={"step": step})
            raise

# Finalize
state.complete_workflow()
profiler.save_report()
```

### Resume Interrupted Workflow
```python
from core.state_manager import list_incomplete_workflows, WorkflowState

# List incomplete workflows
incomplete = list_incomplete_workflows()
for wf in incomplete:
    print(f"{wf['workflow_name']}-{wf['workflow_id']}: {wf['status']}")

# Resume specific workflow
state = WorkflowState("sprint-planning", "sprint-10")
state.print_summary()  # Show current state

# Continue from last checkpoint
if not state.is_step_completed("architect"):
    # Resume architect step...
```

## Utilities

**State Management**:
- `list_workflow_states(workflow_name)`: List all state files
- `list_incomplete_workflows()`: List incomplete workflows with metadata
- `cleanup_old_states(days=30)`: Delete old completed state files

**Profiling**:
- `compare_workflow_runs(baseline, current)`: Compare performance between runs

**Context Loading**:
- `list_available_contexts()`: List all CLAUDE.md files
- `get_context_summary()`: Summary of available contexts
- `estimate_token_count(text)`: Estimate tokens for context text

## Conventions

- **State Files**: JSON format, human-readable for debugging
- **Profiling**: Always save both MD and JSON reports
- **Context**: Respect token budgets to avoid exceeding limits
- **Error Handling**: Record errors in state for post-mortem analysis
- **Idempotency**: Always check `is_step_completed()` before executing

## Testing

```bash
pytest tests/unit/test_state_manager.py  # State management tests
pytest tests/unit/test_profiler.py       # Profiling tests
pytest tests/unit/test_context_loader.py # Context loading tests
```
