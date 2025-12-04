---
context:
  purpose: "Solves workflow fragility, memory limitations, and context overload that cause AI-assisted development failures"
  problem_solved: "Long-running AI workflows fail unpredictably when sessions timeout, token limits are hit, or context windows overflow - losing all progress. Without state persistence, checkpointing, and intelligent context loading, multi-step development tasks become unreliable and unrecoverable."
  keywords: [core, state, checkpoint, recovery, workflow, context, profiler, performance]
  task_types: [implementation, architecture, debugging, workflow]
  priority: high
  max_tokens: 800
  children: [state_manager, profiler, context_loader, directed_loader, optimized_loader]
  dependencies: [config]
---
# Core Framework

## Purpose

Solves **workflow fragility** (#5), **memory limitations** (#4), and **context overload** (#3) from VISION.md.

Long-running AI workflows fail unpredictably when:
- Sessions timeout mid-execution with no recovery path
- Token limits are hit, truncating critical context
- Context windows overflow, causing AI to forget instructions
- Multiple failures compound, making progress unverifiable

The core framework provides state persistence, checkpointing, and intelligent context loading to make multi-step workflows reliable and recoverable even when LLMs fail.

## Key Components

### state_manager.py
**Problem Solved**: Workflow fragility - sessions crash and lose all progress

Persists workflow state to `.claude/workflow-state/` after each step, enabling resume from last checkpoint. Without this, a session timeout 90% through sprint planning means starting over completely.

**Real Failure Prevented**: Sprint planning workflow reaches Step 6 (work item creation), Azure CLI authentication expires, session crashes. With state management: resume from checkpoint, re-authenticate, continue. Without: repeat all agent calls, lose business analysis, re-estimate everything.

### profiler.py
**Problem Solved**: Performance blindness - no visibility into AI agent costs or bottlenecks

Tracks execution time, token usage, and API calls for each workflow step and agent invocation. Generates reports in `.claude/profiling/` showing where time/money is spent.

**Real Failure Prevented**: Workflow takes 15 minutes to complete but you don't know why. Profiling reveals architect agent is called 3 times with same inputs (inefficiency). Fix: cache architect analysis. Without profiling: continue burning time and tokens unknowingly.

### context_loader.py
**Problem Solved**: Context overload - cramming irrelevant documentation overwhelms LLM context windows

Hierarchically loads CLAUDE.md files based on keywords and task types, respecting token budgets. Only loads relevant context for current task.

**Real Failure Prevented**: Task is "fix bug in state_manager.py". Without selective loading: load ALL module docs (15+ files, 50k tokens), hit context limit, truncate critical state_manager context. With context loader: load state_manager context (800 tokens) + dependencies (core, config), keep context under budget.

### directed_loader.py
**Problem Solved**: Scattered context - related context spread across multiple files

Follows dependency chains to load related context together. If loading `agents/`, also loads `core/` and `config/` that agents depend on.

**Real Failure Prevented**: Implementing new agent without core framework context. Agent implementation bypasses state management because AI didn't know it exists. Directed loader ensures dependent context is included.

### optimized_loader.py
**Problem Solved**: Repeated context loading - same files loaded on every operation

Caches loaded context and uses `.claude/context-index.yaml` for O(1) lookups instead of walking directory trees.

**Real Failure Prevented**: Every workflow step walks entire directory tree to find CLAUDE.md files (slow, expensive). Cache hits reduce context loading from 2s to 50ms per operation.

## Architecture

The core framework is the foundation layer that all other components depend on:

```
workflows/ (uses state_manager, profiler)
    ↓
agents/ (uses context_loader)
    ↓
skills/ (uses profiler)
    ↓
core/ ← YOU ARE HERE (provides state, profiling, context)
    ↓
config/ (provides configuration)
```

Core modules are **stateless between operations** - state is persisted to disk, not held in memory. This enables:
- Resumable workflows (read state from disk)
- Parallel execution (no shared memory conflicts)
- Process crashes don't lose data

## Usage

### State Management
```python
from core.state_manager import WorkflowState

# Initialize workflow state
state = WorkflowState(workflow_id="sprint-planning-001")

# Save checkpoint after each step
state.save_checkpoint(step=2, data={
    "backlog_analysis": {...},
    "architecture_review": {...}
})

# Resume from checkpoint
state = WorkflowState.load("sprint-planning-001")
print(f"Resuming from step {state.current_step}")
```

### Profiling
```python
from core.profiler import Profiler

profiler = Profiler(workflow="sprint-planning")
profiler.start_step("business-analysis")
# ... do work ...
profiler.end_step("business-analysis", tokens_used=1200)

# Generate report
profiler.save_report(".claude/profiling/sprint-planning-20241204.md")
```

### Context Loading
```python
from core.context_loader import load_context_for_task

# Load relevant context for a task
context = load_context_for_task(
    task_description="Implement state checkpointing in workflow",
    task_type="implementation",
    max_tokens=2000
)

# Returns only relevant CLAUDE.md content:
# - core/CLAUDE.md (contains state_manager)
# - workflows/CLAUDE.md (uses state management)
# - config/CLAUDE.md (state config)
```

## Important Notes

- **Core modules are high priority**: `priority: high` means context loads before other modules when token budget is limited
- **Token budget**: 800 tokens allocated for core context (larger than typical 600 because of importance)
- **State persistence enabled**: All core operations that modify state persist to `.claude/workflow-state/`
- **No circular dependencies**: Core depends only on config, nothing else, to prevent circular import issues
- **Checkpoint granularity**: State is saved after significant operations (after each workflow step, after agent completion), not on every function call

## Real Failure Scenarios Prevented

### Scenario 1: Session Timeout During Sprint Planning
**Without core framework**: Sprint planning reaches Step 5 (scrum master sprint assembly), user walks away, session times out after 30 minutes. All agent analysis lost. Start over.

**With core framework**: State saved after Steps 1-4. Resume from checkpoint, re-run only Step 5 onward.

### Scenario 2: Token Limit Truncates Critical Context
**Without core framework**: Loading all 15 CLAUDE.md files (60k tokens) to implement feature. Context truncated at 50k, cutting off state_manager docs. Implementation bypasses checkpointing.

**With core framework**: Context loader loads only relevant modules (core, workflows) totaling 3k tokens. Implementation has full state_manager context, uses checkpointing correctly.

### Scenario 3: Workflow Slowness Goes Undiagnosed
**Without core framework**: Daily standup workflow takes 8 minutes. Users frustrated but no data on why.

**With core framework**: Profiler shows business analyst agent taking 6 minutes due to loading full backlog (500 items). Fix: add pagination, runtime drops to 2 minutes.

## Related

- **VISION.md**: Pillars #3 (Agent Specialization), #4 (State Persistence), #5 (Fresh Contexts)
- **config/CLAUDE.md**: Configuration that core modules use
- **workflows/CLAUDE.md**: Workflows that depend on state management
- **agents/CLAUDE.md**: Agents that use context loading
