---
context:
  purpose: "Solves unverified AI work completion and workflow fragility through structured, checkpointed, multi-step processes"
  problem_solved: "AI agents routinely claim tasks are complete when they're not, skip verification steps, and lose progress when sessions crash. Without structured workflows with explicit verification gates and state checkpointing, multi-step development processes are unreliable and untrustworthy."
  keywords: [workflows, orchestration, verification, checkpoint, re-entrant, sprint, backlog, standup]
  task_types: [workflow, sprint-planning, backlog-grooming, daily-standup, retrospective]
  priority: medium
  max_tokens: 600
  children: [sprint-planning, sprint-execution, sprint-completion, sprint-retrospective, backlog-grooming, daily-standup, dependency-management, workflow-resume]
  dependencies: [core, agents, config]
---
# Workflows

## Purpose

Solves **tasks reported complete that were never done** (#1) and **workflow fragility** (#5) from VISION.md.

AI agents routinely claim success while delivering nothing:
- "I created the work items" → Work items don't exist in Azure DevOps
- "Tests are passing" → Tests assert nothing or weren't run
- "Feature is implemented" → Only placeholder code written

Workflows implement **Verifiable Workflows** (Pillar #2) and **State Persistence** (Pillar #4) to catch these failures:
- **Verification gates**: Check external source of truth (work tracking system) before marking complete
- **Explicit steps**: Break work into discrete, verifiable phases with checkpoints
- **Re-entrancy**: Save state after each step so failures don't erase progress
- **Human approval**: Block progression until human reviews and approves critical steps

## Key Workflows

### sprint-planning.md
**Problem Solved**: Unplanned sprints lead to scope creep, missed dependencies, and unaligned team capacity

Multi-step process: business analysis → architecture review → security review → estimation → human approval → work item creation. Each step verified before proceeding.

**Real Failure Prevented**: Sprint planning happens in conversation without structure. Tasks created without security review. Production vulnerability discovered in sprint review. With workflow: security specialist agent flags issue in planning phase, task adjusted before implementation.

### backlog-grooming.md
**Problem Solved**: Features entered as vague requirements get implemented incorrectly

Breaks Features into User Stories with acceptance criteria, estimates, and dependencies. Each story validated for completeness before backlog entry.

**Real Failure Prevented**: Feature "Add authentication" groomed without details. Engineer implements basic auth instead of OAuth. With workflow: backlog grooming clarifies auth method, API provider, token storage - engineer builds correct solution.

### sprint-execution.md
**Problem Solved**: Tasks claimed complete without implementation, tests, or commits. AI agents skip verification steps.

Primary purpose: Implements sprint-assigned tasks using /engineer agent for code + unit tests, /tester agent for validation and integration tests, automated test runs, and auto-commit on high-confidence pass. Secondary: Queries work tracking system (not AI memory) to monitor sprint status, identify blockers, and generate daily reports.

**Real Failure Prevented**: AI claims "implemented authentication" but no code written, no tests, no commit. With workflow: /engineer implements code + tests → unit tests run → /tester validates + integration tests → auto-commit only on high confidence pass → work item updated to "Done" with commit hash. Implementation verified at every step, not just claimed.

### daily-standup.md
**Problem Solved**: Progress tracking relies on AI assertions instead of verified work item state

Generates standup report by querying work tracking system. Compares claimed progress to actual work item state changes.

**Real Failure Prevented**: Developer says "completed authentication" in standup. Daily standup workflow queries Azure DevOps: auth task still "To Do", no commits in last 24 hours. Surface honesty gap immediately.

### sprint-retrospective.md
**Problem Solved**: Retrospectives become generic without specific data on what went wrong

Analyzes profiling data, state checkpoints, and work item history to generate evidence-based retrospective insights.

**Real Failure Prevented**: Team vaguely feels "sprint was slow". Retrospective workflow shows: architect agent called 12 times (should be 3), 40% of sprint on dependency resolution (should be 10%). Concrete actions: cache architect analysis, improve dependency mapping.

### workflow-resume.md
**Problem Solved**: Interrupted workflows lose all progress and must restart from scratch

Lists incomplete workflows with state checkpoints. Allows resume from last successful step.

**Real Failure Prevented**: Sprint planning interrupted at Step 5 (work item creation) due to Azure CLI auth expiry. Without resume: re-run business analysis, architecture review, estimation (3 hours). With resume: re-authenticate, continue from Step 5 (5 minutes).

## Architecture

Workflows orchestrate agents via fresh context windows:

```
Workflow (main conversation)
    ↓ spawn via Task tool
Agent 1: Business Analyst (fresh context)
    ↓ returns prioritized backlog
Workflow (receives result, saves checkpoint)
    ↓ spawn via Task tool
Agent 2: Project Architect (fresh context)
    ↓ returns architecture review
Workflow (receives result, saves checkpoint)
    ↓ ...
```

**Key Pattern**: Each agent gets fresh context (no overload), returns structured output, workflow saves checkpoint (re-entrancy).

## Verification Pattern

Every workflow step follows this pattern:

1. **Execute**: Agent or operation performs work
2. **Checkpoint**: Save state to `.claude/workflow-state/`
3. **Verify**: Query external source of truth (not AI claim)
4. **Gate**: Block if verification fails, continue if succeeds

**Example: Work Item Creation Verification**

```python
# Step: Create work items
for item in approved_items:
    # Execute
    result = azure_devops.create_work_item(title=item.title, ...)

    # Checkpoint
    state.save(step=7, created_items=[result.id])

    # Verify - query Azure DevOps (external truth)
    verify = azure_devops.get_work_item(result.id)
    if not verify.exists:
        raise VerificationError(f"Claimed {result.id} created but doesn't exist")

    # Gate - only proceed if verification passes
    if verify.state != "New":
        warn(f"Expected New state, got {verify.state}")
```

## State Management

Workflow state files stored in `.claude/workflow-state/`:

```json
{
  "workflow": "sprint-planning",
  "workflow_id": "sprint-1-planning",
  "current_step": 5,
  "completed_steps": [1, 2, 3, 4],
  "state": {
    "backlog_analysis": {...},
    "architecture_review": {...},
    "security_review": {...},
    "estimation": {...},
    "approved_items": [...]
  },
  "checkpoints": [
    {"step": 1, "timestamp": "2024-12-04T10:30:00Z"},
    {"step": 2, "timestamp": "2024-12-04T10:45:00Z"},
    ...
  ]
}
```

**Resume Process**:
1. User runs `/workflow-resume`
2. Workflow lists incomplete states
3. User selects workflow to resume
4. Workflow loads state, jumps to `current_step + 1`
5. Previous agent results available in `state` object

## Usage

Workflows are invoked via slash commands in Claude Code:

```
/sprint-planning           # Plan a new sprint
/backlog-grooming          # Groom features into user stories
/daily-standup             # Generate daily progress report
/sprint-execution          # Monitor sprint progress
/sprint-retrospective      # Analyze completed sprint
/workflow-resume           # Resume interrupted workflow
```

## Workflow Utilities

Production utility functions in `workflows/utilities.py` provide reusable functionality across workflows:

### analyze_sprint(adapter, sprint_name, config=None)
**Purpose**: Comprehensive sprint analysis and statistics

**Returns**: Dict with total items, state distribution, type distribution, assignee distribution, story points (total/completed/in_progress/not_started), completion rate, and velocity

**Example Usage**:
```python
from workflows.utilities import analyze_sprint
sprint_stats = analyze_sprint(adapter, "Sprint 6")
print(f"Completion: {sprint_stats['completion_rate']:.1f}%")
print(f"Velocity: {sprint_stats['velocity']} points")
```

### verify_work_item_states(adapter, work_items, terminal_states=None)
**Purpose**: External source of truth verification (VISION.md pattern)

Detects divergence between claimed work item states and actual states in the work tracking system. Critical for catching AI agents claiming work is complete when it isn't.

**Returns**: Dict with verified count, divergence count, divergences list (with severity ERROR/WARNING), and summary counts

**Example Usage**:
```python
from workflows.utilities import verify_work_item_states
verification = verify_work_item_states(adapter, recent_items)
if verification['divergence_count'] > 0:
    print(f"⚠️ {verification['divergence_count']} divergences detected")
```

### get_recent_activity(adapter, sprint_name, hours=24, config=None)
**Purpose**: Filter sprint items by recent updates (time window)

**Returns**: Dict with total items, recent items list, recent count

**Example Usage**:
```python
from workflows.utilities import get_recent_activity
activity = get_recent_activity(adapter, "Sprint 6", hours=24)
print(f"Found {activity['recent_count']} items updated in last 24h")
```

### identify_blockers(adapter, sprint_name, stale_threshold_days=3, config=None)
**Purpose**: Identify blocked work items through multiple signals

Detects blockers via: Blocked state, blocker tag, or stale (no updates in N+ days). Calculates impact (affected people, story points at risk).

**Returns**: Dict with total blockers, blocked items, tagged items, stale items, and impact analysis

**Example Usage**:
```python
from workflows.utilities import identify_blockers
blockers = identify_blockers(adapter, "Sprint 6", stale_threshold_days=3)
print(f"Total blockers: {blockers['total_blockers']}")
print(f"Story points at risk: {blockers['impact']['story_points_at_risk']}")
```

## Work Tracking: Adapter Required

**⚠️ CRITICAL: All workflows must use the work tracking adapter via Python. `az boards` CLI is deprecated.**

### Correct Pattern
```python
# ✅ ALWAYS use adapter
import sys
sys.path.insert(0, '.claude/skills')
from work_tracking import get_adapter
from workflows.utilities import analyze_sprint, verify_work_item_states

adapter = get_adapter()
items = adapter.query_sprint_work_items("Sprint 6")
sprint_stats = analyze_sprint(adapter, "Sprint 6")
```

### Deprecated Pattern
```bash
# ❌ NEVER use az boards CLI
az boards work-item show --id 1234  # DEPRECATED
az boards query                      # DEPRECATED
```

### Why Adapter is Mandatory for Workflows
- **External source of truth**: REST API calls, not subprocess output parsing
- **Platform abstraction**: Works with Azure DevOps, file-based, Jira, GitHub
- **Verification pattern**: Required for VISION.md verification gates
- **State persistence**: Adapter results serialize cleanly for checkpoints
- **Error recovery**: Unified error handling across all platforms

**All workflow templates use the adapter. Do not deviate from this pattern.**

## Important Notes

- **Workflows are re-entrant**: Always checkpoint after significant steps
- **Verify, don't trust**: Query external systems via adapter, don't trust AI claims
- **Use workflow utilities**: Instead of ad-hoc scripts, use production utilities in `workflows/utilities.py`
- **Use adapter, not CLI**: All work tracking operations must use Python adapter from `.claude/skills/work_tracking.py`
- **Human gates**: Critical steps (sprint approval, work item creation) require human confirmation
- **Fresh agent contexts**: Each agent spawns with clean context via Task tool
- **State cleanup**: Old workflow states accumulate in `.claude/workflow-state/` - clean periodically

## Real Failure Scenarios Prevented

### Scenario 1: AI Claims Work Items Created, They Don't Exist
**Without workflows**: "I created 10 work items for Sprint 1" → Sprint taskboard is empty → Discover issue 3 days into sprint

**With workflows**: Workflow verifies each work item after creation by querying Azure DevOps. If creation fails, workflow halts and reports error immediately.

### Scenario 2: Sprint Planning Session Crashes Mid-Process
**Without workflows**: 2 hours of agent analysis (backlog prioritization, architecture review, estimation) lost. Start over.

**With workflows**: State saved after each step. Resume from Step 4 (where crash happened), re-run only that step. 5 minutes to recover vs 2 hours to restart.

### Scenario 3: Security Review Skipped Due to Time Pressure
**Without workflows**: Team manually runs planning, skips security review to save time. Vulnerability shipped to production.

**With workflows**: Sprint planning workflow has mandatory security specialist agent step. Cannot proceed to approval without security review. Workflow enforces process discipline.

## Related

- **VISION.md**: Pillars #2 (Verifiable Workflows), #4 (State Persistence)
- **agents/CLAUDE.md**: Agents that workflows orchestrate
- **core/CLAUDE.md**: State management and profiling used by workflows
- **templates/workflows/**: Workflow template source files
- **workflows/utilities.py**: Production utility functions for sprint analysis and verification
- **workflows/validators.py**: Verification checklist validators for workflows
