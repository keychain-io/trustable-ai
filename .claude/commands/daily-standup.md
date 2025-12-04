# Daily Standup Report Workflow

**Project**: trusted-ai-development-workbench
**Workflow**: Daily Standup Report
**Purpose**: Generate automated daily standup reports for the active sprint

## Output Formatting Requirements

**IMPORTANT**: When generating reports, use actual Unicode emojis, NOT GitHub-style shortcodes:
- ✅ Correct: `⚠️ Warning` or `ℹ️ Info`
- ❌ Incorrect: `:warning:` or `:information_source:`

Status indicators to use:
- ✅ Completed / On track
- ⚠️ Warning / Below target
- ❌ Critical / Blocked
- ℹ️ Information
- 🔴 High priority
- 🟡 Medium priority
- 🟢 Low priority / Good

## Overview

This lightweight workflow generates daily standup reports showing what was completed yesterday, what's planned for today, and any blockers. Perfect for distributed teams or async standups.

## Prerequisites

- Active sprint in azure-devops
- Work items with recent activity

## Initialize Work Tracking

```python
# Initialize work tracking adapter (auto-selects Azure DevOps or file-based)
import sys
sys.path.insert(0, ".claude/skills")
from work_tracking import get_adapter
from datetime import datetime, timedelta

adapter = get_adapter()
print(f"📋 Work Tracking: {adapter.platform}")

# Get current sprint name (replace CURRENT_SPRINT with actual sprint)
current_sprint = "Sprint 1"  # Update this
```

## Workflow Steps

### Step 1: Gather Yesterday's Activity

1. **Query completed work (last 24 hours):**
   ```bash
   # Get work items completed or updated yesterday
   yesterday=$(date -d "yesterday" +%Y-%m-%d)
   az boards query --wiql "SELECT [System.Id], [System.Title], [System.State], [System.AssignedTo] FROM WorkItems WHERE [System.TeamProject] = 'Trusted AI Development Workbench' AND [System.IterationPath] UNDER 'Trusted AI Development Workbench\\CURRENT_SPRINT' AND [System.ChangedDate] >= '$yesterday'" --output json
   ```

2. **Categorize changes:**
   - ✅ Completed: Items moved to "Done"/"Closed"
   - ⚙️ In Progress: Items actively worked on
   - 🆕 Started: Items moved from "New" to "Active"
   - 🚫 Blocked: Items marked as blocked
   - 💬 Discussed: Items with new comments

### Step 2: Identify Today's Focus

1. **Query active work items:**
   ```bash
   # Get currently active work items
   az boards query --wiql "SELECT [System.Id], [System.Title], [System.State], [System.AssignedTo], [Microsoft.VSTS.Scheduling.StoryPoints] FROM WorkItems WHERE [System.TeamProject] = 'Trusted AI Development Workbench' AND [System.IterationPath] UNDER 'Trusted AI Development Workbench\\CURRENT_SPRINT' AND [System.State] IN ('Active', 'In Progress', 'Doing')" --output json
   ```

2. **Group by team member:**
   - List active items per person
   - Identify items without updates
   - Flag items at risk

### Step 3: Detect Blockers

1. **Find blocked items:**
   - Items with "Blocked" state
   - Items tagged with "blocker"
   - Items with no updates in 3+ days
   - Items mentioned in comments as blocked

2. **Analyze blocker impact:**
   - Number of people affected
   - Story points at risk
   - Sprint goal impact

### Step 4: Generate Standup Report

1. **Read agent definition:** `.claude/agents/scrum-master.md`
2. **Task:** "Generate a concise daily standup report:
   - Summarize yesterday's accomplishments
   - List today's planned work by team member
   - Highlight blockers requiring attention
   - Note sprint progress toward goal
   - Keep it brief and action-oriented"
3. **Spawn agent** using Task tool with model `claude-sonnet-4.5`
4. **Input:** Yesterday's activity, today's active items, blockers
5. **Display output** to user

### Step 5: Format and Distribute Report

Generate report in markdown format (template shown below with placeholder data that would be filled at runtime).

### Step 6: Distribute Report

1. **Save to file:**
   ```bash
   # Save to reports directory
   mkdir -p .claude/reports/daily
   echo "$report" > .claude/reports/daily/$(date +%Y-%m-%d)-standup.md
   ```

2. **Post to team channels** (configure webhook URLs in environment)

3. **Email to stakeholders** (optional)

## Automation Setup

### Run Automatically Every Morning

**GitHub Actions** (`.github/workflows/daily-standup.yml`):

```yaml
name: Daily Standup Report

on:
  schedule:
    - cron: '0 9 * * 1-5'  # Weekdays at 9 AM
  workflow_dispatch:  # Manual trigger

jobs:
  standup-report:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install framework
        run: pip install trustable-ai

      - name: Generate standup report
        env:
          AZURE_DEVOPS_PAT: ${{ secrets.AZURE_DEVOPS_PAT }}
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
        run: |
          cwf workflow run daily-standup

      - name: Commit report
        run: |
          git config user.name "Daily Standup Bot"
          git config user.email "bot@yourcompany.com"
          git add .claude/reports/daily/
          git commit -m "Daily standup report $(date +%Y-%m-%d)" || true
          git push
```

**Azure DevOps Pipeline** (`azure-daily-standup.yml`):

```yaml
schedules:
  - cron: "0 9 * * 1-5"
    displayName: Daily Standup Report
    branches:
      include:
        - main
    always: true

steps:
  - task: UsePythonVersion@0
    inputs:
      versionSpec: '3.10'

  - script: |
      pip install trustable-ai
      cwf workflow run daily-standup
    displayName: 'Generate Daily Standup'
    env:
      AZURE_DEVOPS_PAT: $(AZURE_DEVOPS_PAT)
      TEAMS_WEBHOOK_URL: $(TEAMS_WEBHOOK_URL)
```

### Manual Execution

```bash
# Generate today's standup report
cwf workflow run daily-standup

# Generate for specific date
cwf workflow run daily-standup --date 2025-01-15

# Dry run (preview without posting)
cwf workflow run daily-standup --dry-run
```

## Integration with Team Tools

### Slack Integration
Set environment variable:
```bash
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

### Microsoft Teams Integration
Set environment variable:
```bash
export TEAMS_WEBHOOK_URL="https://outlook.office.com/webhook/YOUR/WEBHOOK/URL"
```

## Success Criteria

- ✅ Report generated every weekday morning
- ✅ Delivered to team channels within 5 minutes
- ✅ Blockers clearly highlighted
- ✅ Team members know what others are working on
- ✅ Sprint progress visible at a glance

## Configuration

**Agents Used:**
- Scrum Master (report generation and formatting)
**Report Schedule:**
- **Daily**: Weekdays at 9 AM
- **Duration**: < 1 minute to generate
- **Distribution**: Slack/Teams/Email

**Work Item Types Tracked:**
- User Story
- Task
- Bug

---

*Generated by Trustable AI Workbench for trusted-ai-development-workbench*