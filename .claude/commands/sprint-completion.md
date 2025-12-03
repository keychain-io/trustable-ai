# Sprint Completion Workflow

**Project**: Trusted AI Development Workbench
**Workflow**: Sprint Completion
**Purpose**: Close sprint, archive data, calculate metrics, and prepare for next sprint

## Output Formatting Requirements

**IMPORTANT**: Use actual Unicode emojis in reports, NOT GitHub-style shortcodes.

---

## Workflow Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  SPRINT COMPLETION                                                          │
│                                                                             │
│  Step 1: Collect final sprint metrics                                      │
│  Step 2: /scrum-master → Analyze incomplete work (if any)                  │
│  Step 3: Process incomplete items (carry over / backlog)                   │
│  Step 4: Calculate performance metrics                                     │
│  Step 5: Generate completion report                                        │
│  Step 6: Archive sprint data                                               │
│  Step 7: Prepare next sprint                                               │
│                                                                             │
│  Agent command spawns a FRESH CONTEXT WINDOW via Task tool                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Initialize Workflow

```python
current_sprint = input("Sprint to close (e.g., Sprint 1): ")
next_sprint = input("Next sprint name (e.g., Sprint 2): ")

# Load all sprint work items
from pathlib import Path
import yaml

sprint_items = []
work_items_dir = Path(".claude/work-items")
for f in work_items_dir.glob("*.yaml"):
    with open(f) as file:
        item = yaml.safe_load(file)
        if item.get('sprint') == current_sprint:
            sprint_items.append(item)

print(f"📋 Found {len(sprint_items)} items in {current_sprint}")
```

---

## Step 1: Collect Final Sprint Metrics

```python
# Categorize items
completed_states = ['Done', 'Closed', 'Resolved', 'Completed']
completed = [i for i in sprint_items if i['status'] in completed_states]
incomplete = [i for i in sprint_items if i['status'] not in completed_states]

# Calculate metrics
total_points = sum(i.get('story_points', 0) for i in sprint_items)
completed_points = sum(i.get('story_points', 0) for i in completed)
completion_rate = (completed_points / total_points * 100) if total_points > 0 else 0

print(f"📊 Final Sprint Metrics:")
print(f"  Total: {len(sprint_items)} items ({total_points} pts)")
print(f"  ✅ Completed: {len(completed)} ({completed_points} pts)")
print(f"  ⏳ Incomplete: {len(incomplete)}")
print(f"  📈 Completion Rate: {completion_rate:.1f}%")
print(f"  🚀 Velocity: {completed_points} story points")
```

---

## Step 2: Analyze Incomplete Work (If Any)

**IF THERE ARE INCOMPLETE ITEMS**, call `/scrum-master` with the following task:

```
## YOUR TASK: Analyze Incomplete Work Items

Review incomplete items and recommend disposition.

### Incomplete Items
{List incomplete items with details: title, status, story_points, progress}

### For Each Item, Determine:

1. **Reason for Incompletion**
   - Blocked by external dependency
   - Underestimated complexity
   - Scope creep
   - Started late
   - Not started (deprioritized)

2. **Progress Made**
   - Percentage complete
   - Work already done
   - Work remaining

3. **Recommendation**
   - **CARRY_OVER**: Move to next sprint (item has significant progress)
   - **BACKLOG**: Return to backlog (item not started or blocked indefinitely)
   - **ARCHIVE**: Close as won't do (item no longer relevant)

4. **Re-estimation**
   - Does the item need re-estimation?
   - Suggested new story points

5. **Next Sprint Impact**
   - How much capacity will carry-over items consume?

### Output Format

Return JSON with:
```json
{
  "items": [
    {
      "id": "FEATURE-001",
      "recommendation": "CARRY_OVER|BACKLOG|ARCHIVE",
      "reason": "...",
      "progress_pct": 60,
      "re_estimate": 3,
      "notes": "..."
    }
  ],
  "carry_over_points": 8,
  "capacity_impact": "15% of next sprint"
}
```
```

**After the agent completes:**
- Parse recommendations
- Present to user for approval

---

## Step 3: Process Incomplete Items

Based on recommendations (after user approval):

```python
for item in carry_over_items:
    # Update item to next sprint
    item['sprint'] = next_sprint
    item['carry_over_from'] = current_sprint
    item['carry_over_reason'] = recommendation['reason']

    # Save updated item
    # Add carry-over comment

    print(f"  ⏭️ {item['id']}: Carried over to {next_sprint}")

for item in backlog_items:
    # Remove sprint assignment
    item['sprint'] = None
    item['status'] = 'New'

    print(f"  ↩️ {item['id']}: Returned to backlog")

for item in archive_items:
    # Mark as won't do
    item['status'] = 'Closed'
    item['resolution'] = "Won't Do"

    print(f"  🗃️ {item['id']}: Archived")
```

---

## Step 4: Calculate Performance Metrics

```python
metrics = {
    'sprint': current_sprint,
    'planned_points': total_points,
    'completed_points': completed_points,
    'velocity': completed_points,
    'completion_rate': completion_rate,
    'items_completed': len(completed),
    'items_carried_over': len(carry_over_items),
    'items_to_backlog': len(backlog_items),
}

# Quality metrics
metrics['quality'] = {
    'test_coverage': get_test_coverage(),  # From test runner
    'bugs_created': count_bugs_created(),
    'bugs_fixed': count_bugs_fixed(),
}

print(f"📈 Performance Summary:")
print(f"  Velocity: {metrics['velocity']} pts")
print(f"  Completion: {metrics['completion_rate']:.1f}%")
print(f"  Quality: {metrics['quality']['test_coverage']}% coverage")
```

---

## Step 5: Generate Completion Report

```markdown
# Sprint Completion Report

**Sprint**: {current_sprint}
**Duration**: {start_date} - {end_date}

---

## 📊 Summary

| Metric | Value |
|--------|-------|
| Planned Points | {total_points} |
| Completed Points | {completed_points} |
| Velocity | {velocity} pts |
| Completion Rate | {completion_rate}% |

---

## 📋 Work Breakdown

### ✅ Completed ({completed_count})
{List completed items}

### ⏭️ Carried Over ({carry_over_count})
{List carried over items with reasons}

### ↩️ Returned to Backlog ({backlog_count})
{List items returned to backlog}

---

## 📈 Quality Metrics

- Test Coverage: {coverage}% (target: 80%)
- Bugs Created: {bugs_created}
- Bugs Fixed: {bugs_fixed}

---

## 🎯 Sprint Goal

**Goal**: {sprint_goal}
**Status**: {Achieved / Partially Achieved / Not Achieved}

---

## 📝 Lessons Learned

{Include retrospective notes if available}

---

## 📅 Next Sprint

**Name**: {next_sprint}
**Carry-over Impact**: {carry_over_points} pts
**Recommended Capacity**: {recommended_capacity} pts

---

*Generated by Trustable AI Workbench*
```

Save to `.claude/reports/sprint-completion/sprint-{N}-completion.md`

---

## Step 6: Archive Sprint Data

```python
import json
from datetime import datetime

# Archive sprint data
archive_data = {
    'sprint': current_sprint,
    'completion_date': datetime.now().isoformat(),
    'metrics': metrics,
    'completed_items': [i['id'] for i in completed],
    'carried_over': [i['id'] for i in carry_over_items],
}

# Save to archive
archive_path = Path(f".claude/data/sprint-{sprint_number}.json")
archive_path.parent.mkdir(parents=True, exist_ok=True)
with open(archive_path, 'w') as f:
    json.dump(archive_data, f, indent=2)

print(f"📁 Archived sprint data to {archive_path}")
```

---

## Step 7: Prepare Next Sprint

```python
# Calculate recommended capacity for next sprint
carry_over_points = sum(i.get('story_points', 0) for i in carry_over_items)
available_capacity = team_capacity - carry_over_points

print(f"📅 Next Sprint Preparation:")
print(f"  Team Capacity: {team_capacity} pts")
print(f"  Carry-over: -{carry_over_points} pts")
print(f"  Available: {available_capacity} pts")
print(f"")
print(f"➡️ Next: Run /sprint-planning for {next_sprint}")
```

---

## Completion Summary

```
════════════════════════════════════════════════════════════════════════════════
✅ SPRINT COMPLETION FINISHED
════════════════════════════════════════════════════════════════════════════════

Sprint: {current_sprint}

📊 Final Results:
  - Velocity: {velocity} story points
  - Completion: {completion_rate}%
  - Items Done: {completed_count}
  - Carried Over: {carry_over_count}

📁 Artifacts:
  - Completion Report: .claude/reports/sprint-completion/
  - Sprint Archive: .claude/data/

➡️ Next Steps:
  1. Share completion report with stakeholders
  2. Run /sprint-planning for {next_sprint}

════════════════════════════════════════════════════════════════════════════════
```

---

## Agent Commands Used

| Step | Agent Command | When | Purpose |
|------|---------------|------|---------|
| 2 | `/scrum-master` | If incomplete items | Analyze incomplete work |

**Key**: Agent command spawns a **fresh context window** via the Task tool.

---

## Configuration

**Work Tracking Platform:** file-based

**Work Item Types:**
- Feature: Feature
- Task: Task
- Bug: Bug

**Quality Standards:**
- Test Coverage: >= 80%

---

*Generated by Trustable AI Workbench for Trusted AI Development Workbench*