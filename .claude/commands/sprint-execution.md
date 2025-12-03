# Sprint Execution Monitoring Workflow

**Project**: Trusted AI Development Workbench
**Workflow**: Sprint Execution Monitoring
**Purpose**: Monitor sprint progress, identify blockers, and generate daily reports

## Output Formatting Requirements

**IMPORTANT**: Use actual Unicode emojis in reports, NOT GitHub-style shortcodes.

---

## Workflow Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  SPRINT EXECUTION MONITORING                                                │
│                                                                             │
│  Step 1: Collect sprint status data                                        │
│  Step 2: /scrum-master → Daily standup report                              │
│  Step 3: /senior-engineer → Blocker analysis (if blocked items)            │
│  Step 4: Quality health check                                              │
│  Step 5: /security-specialist → Weekly security review                     │
│  Step 6: Generate status report                                            │
│                                                                             │
│  Each agent command spawns a FRESH CONTEXT WINDOW via Task tool            │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Initialize Workflow

```python
current_sprint = input("Sprint name (e.g., Sprint 1): ")

# Load sprint work items from .claude/work-items/
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

## Step 1: Collect Sprint Status Data

Gather metrics from work items:

```python
# Calculate metrics
completed = [i for i in sprint_items if i['status'] == 'Done']
in_progress = [i for i in sprint_items if i['status'] == 'In Progress']
blocked = [i for i in sprint_items if i['status'] == 'Blocked']
not_started = [i for i in sprint_items if i['status'] == 'New']

total_points = sum(i.get('story_points', 0) for i in sprint_items)
completed_points = sum(i.get('story_points', 0) for i in completed)

print(f"📊 Sprint Status:")
print(f"  Total: {len(sprint_items)} items ({total_points} pts)")
print(f"  ✅ Done: {len(completed)} ({completed_points} pts)")
print(f"  🔄 In Progress: {len(in_progress)}")
print(f"  🔴 Blocked: {len(blocked)}")
print(f"  ⬜ Not Started: {len(not_started)}")
```

---

## Step 2: Generate Daily Standup Report

**Call `/scrum-master` with the following task:**

```
## YOUR TASK: Generate Daily Standup Report

Create a daily standup report for the team.

### Sprint Data
- Sprint: {current_sprint}
- Total Items: {len(sprint_items)}
- Completed: {len(completed)} ({completed_points} pts)
- In Progress: {len(in_progress)}
- Blocked: {len(blocked)}
- Not Started: {len(not_started)}

### Work Items
{List of all work items with status}

### Generate Report Including:

1. **Yesterday's Progress**
   - What was completed
   - Story points delivered

2. **Today's Focus**
   - What should be worked on
   - Priority items

3. **Blockers & Impediments**
   - Current blockers
   - Who needs to resolve them

4. **Sprint Health**
   - On track / At risk / Behind
   - Days remaining
   - Burndown status

5. **Recommendations**
   - Team focus areas
   - Risk mitigations

### Output Format

Return a formatted standup report in markdown.
```

**After the agent completes:**
- Display standup report to user
- Save to `.claude/reports/daily/`

---

## Step 3: Analyze Blockers (If Any)

**IF THERE ARE BLOCKED ITEMS**, call `/senior-engineer` with the following task:

```
## YOUR TASK: Analyze Blocked Work Items

Review blocked items and suggest resolutions.

### Blocked Items
{List of blocked work items with details}

### For Each Blocker, Analyze:

1. **Root Cause**
   - Why is this blocked?
   - Technical vs. organizational blocker

2. **Impact Assessment**
   - How many items depend on this?
   - Sprint goal impact

3. **Resolution Options**
   - Technical solutions or workarounds
   - Who needs to be involved
   - Estimated time to resolve

4. **Priority Ranking**
   - Which blockers to resolve first
   - Critical path analysis

### Output Format

Return JSON with blocker analysis and recommendations.
```

**After the agent completes:**
- Display blocker analysis
- Recommend actions to unblock items

---

## Step 4: Quality Health Check

Run automated quality checks:

```bash
# Run tests with coverage
python -m pytest --cov=src --cov-report=term

# Check coverage against standard
# Target: 80%
```

Compare results against quality standards:
- Test Coverage: Current vs. 80%
- Critical Vulnerabilities: Current vs. 0
- Code Complexity: Current vs. 10

---

## Step 5: Weekly Security Review (Fridays Only)

**FOR WEEKLY REPORTS ONLY**, call `/security-specialist` with the following task:

```
## YOUR TASK: Weekly Security Status Review

Review sprint security status.

### Quality Standards
- Critical Vulnerabilities: Max 0
- High Vulnerabilities: Max 0

### Security Scan Results
{Include any security scan output}

### Analyze:

1. **Vulnerability Status**
   - New vulnerabilities this sprint
   - Resolved vulnerabilities
   - Outstanding issues

2. **Security Impact of Changes**
   - Features with security implications
   - Authentication/authorization changes

3. **Recommendations**
   - Critical issues requiring immediate attention
   - Security tasks for next sprint

### Output Format

Return security review report in markdown.
```

---

## Step 6: Generate Status Report

Compile comprehensive report:

```
════════════════════════════════════════════════════════════════════════════════
📊 SPRINT STATUS REPORT - {current_sprint}
════════════════════════════════════════════════════════════════════════════════

📈 Progress: {completed_points}/{total_points} points ({percentage}%)

📋 Work Items:
  ✅ Done: {done_count}
  🔄 In Progress: {in_progress_count}
  🔴 Blocked: {blocked_count}
  ⬜ Not Started: {not_started_count}

⚠️ Blockers:
  {blocker_list}

🔒 Quality:
  - Test Coverage: {coverage}% (target: 80%)
  - Vulnerabilities: {vuln_count}

🎯 Sprint Health: {On Track / At Risk / Behind}

════════════════════════════════════════════════════════════════════════════════
```

---

## Agent Commands Used

| Step | Agent Command | When | Purpose |
|------|---------------|------|---------|
| 2 | `/scrum-master` | Daily | Standup report |
| 3 | `/senior-engineer` | When blocked | Blocker analysis |
| 5 | `/security-specialist` | Weekly | Security review |

**Key**: Each agent command spawns a **fresh context window** via the Task tool.

---

## Execution Schedule

- **Daily (9 AM)**: Steps 1-4 (status, standup, blockers, quality)
- **Weekly (Friday 4 PM)**: Full workflow including security review
- **Ad-hoc**: Run manually when needed

---

## Configuration

**Work Tracking Platform:** file-based

**Quality Standards:**
- Test Coverage: >= 80%
- Critical Vulnerabilities: <= 0
- Code Complexity: <= 10

---

*Generated by Trustable AI Workbench for Trusted AI Development Workbench*