# Sprint Execution Monitoring Workflow

**Project**: Trusted AI Development Workbench
**Workflow**: Sprint Execution Monitoring
**Purpose**: Monitor sprint progress, identify blockers, and generate daily/weekly reports

## Overview

This workflow monitors active sprint execution, tracks progress against sprint goals, identifies blockers, and provides regular status reports to stakeholders.

## Prerequisites

- Active sprint in azure-devops
- Work items assigned to current sprint
- Sprint goals defined

## Workflow Steps

### Step 1: Collect Sprint Status Data

1. **Query current sprint work items:**
   ```bash
   # Get all work items in current sprint
   az boards query --wiql "SELECT [System.Id], [System.Title], [System.State], [System.AssignedTo], [Microsoft.VSTS.Scheduling.StoryPoints] FROM WorkItems WHERE [System.TeamProject] = 'Trusted AI Development Workbench' AND [System.IterationPath] UNDER 'Trusted AI Development Workbench\\CURRENT_SPRINT'" --output json
   ```

2. **Calculate sprint metrics:**
   - **Total story points**: Planned vs. completed
   - **Burndown data**: Remaining work over time
   - **Work item status**: New / Active / Resolved / Closed
   - **Team capacity**: Available vs. allocated
   - **Velocity**: Story points per day
   - **Blockers**: Items tagged or flagged as blocked

3. **Identify issues:**
   - Work items not updated in 3+ days
   - Items without assignee
   - Items marked as blocked
   - Items exceeding estimated time
   - High-priority items not started

### Step 2: Daily Standup Report Generation

1. **Read agent definition:** `.claude/agents/scrum-master.md`
2. **Task:** "Generate daily standup report for the sprint:
   - Summarize yesterday's progress (story points completed)
   - Identify work planned for today
   - List current blockers and impediments
   - Flag items at risk of not completing
   - Provide recommendations for team focus
   - Track toward sprint goal"
3. **Spawn agent** using Task tool with model `claude-sonnet-4.5`
4. **Input:** Sprint status data from Step 1
5. **Display output** to user
6. **Collect:**
   - Daily progress summary
   - Blockers list
   - Items at risk
   - Team focus recommendations

### Step 3: Identify and Analyze Blockers

1. **Read agent definition:** `.claude/agents/senior-engineer.md`
2. **Task:** "Analyze blocked work items and suggest resolutions:
   - Review each blocked item's context
   - Identify root cause of blocker
   - Suggest technical solutions or workarounds
   - Recommend who should be involved
   - Estimate impact on sprint goal"
3. **Spawn agent** using Task tool with model `claude-sonnet-4.5`
4. **Input:** List of blocked items
5. **Display output** to user
6. **Collect:**
   - Blocker analysis
   - Suggested resolutions
   - Impact assessment

### Step 4: Quality Health Check

1. **Run automated quality checks:**
   ```bash
   # Test coverage check
   pytest --cov=src --cov-report=term

   # Security scan
   # (Run your security scanner here)

   # Code quality
   # (Run linters/analyzers here)
   ```

2. **Compare against standards:**
   - Test coverage: Current vs. 80%
   - Critical vulnerabilities: Current vs. 0
   - High vulnerabilities: Current vs. 0
   - Code complexity: Current vs. 10

3. **Flag quality regressions:**
   - Identify when metrics fall below standards
   - Link to specific work items causing regression
   - Recommend remediation actions

### Step 5: Security Status Review (Weekly)

1. **Read agent definition:** `.claude/agents/security-specialist.md`
2. **Task:** "Review sprint security status:
   - Analyze security scan results
   - Review vulnerability trends
   - Assess impact of security issues on sprint
   - Recommend security-focused tasks
   - Check compliance with security standards"
3. **Spawn agent** using Task tool with model `claude-sonnet-4.5`
4. **Input:** Security scan results and vulnerability data
5. **Display output** to user
6. **Collect:**
   - Security status summary
   - Critical issues requiring immediate attention
   - Recommended security tasks

### Step 6: Generate Status Report

Report includes:
- Sprint progress (story points, velocity, trend)
- Work item status breakdown
- Quality metrics vs. standards
- Blockers and risks
- Items at risk
- Sprint goal progress
- Recommendations

### Step 7: Update Stakeholders

1. **Daily standup report** (automated):
   - Save to `.claude/reports/daily/sprint-[NUMBER]-day-[DAY].md`
   - Post to team chat (Slack/Teams via webhook)
   - Update Azure DevOps dashboard

2. **Weekly status report** (for stakeholders):
   - Save to `.claude/reports/weekly/sprint-[NUMBER]-week-[WEEK].md`
   - Email to stakeholders
   - Update project wiki

3. **Real-time blockers alert**:
   - Create Task for each new blocker
   - Assign to appropriate resolver
   - Tag with "blocker" and "urgent"

### Step 8: Automated Actions (Optional)

Create work items for:
- Stale items (no update in 3+ days)
- Blocked items requiring resolution
- Quality regressions

## Execution Schedule

### Daily (Automated)
- **Every morning at 9 AM**:
  - Run Steps 1-3 (status collection, standup report, blocker analysis)
  - Generate daily standup report
  - Send to team channel

### Weekly (Automated)
- **Every Friday at 4 PM**:
  - Run full workflow (all steps)
  - Generate comprehensive weekly report
  - Send to stakeholders
  - Update project dashboard

### Ad-hoc (Manual)
- Run whenever sprint health check is needed
- Before sprint review preparation
- When major blockers emerge

## Setup for Automated Execution

### GitHub Actions


```yaml
# .github/workflows/sprint-monitoring.yml
name: Sprint Execution Monitoring

on:
  schedule:
    - cron: '0 9 * * 1-5'  # Weekdays at 9 AM
    - cron: '0 16 * * 5'   # Friday at 4 PM (weekly report)

jobs:
  monitor-sprint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install claude-workflow-framework
      - name: Generate Sprint Report
        env:
          AZURE_DEVOPS_PAT: ${{ secrets.AZURE_DEVOPS_PAT }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          cwf workflow run sprint-execution --report-type daily
```

### Azure DevOps Pipeline


```yaml
# azure-sprint-monitoring.yml
schedules:
  - cron: "0 9 * * 1-5"
    displayName: Daily Sprint Standup
    branches:
      include:
        - main
  - cron: "0 16 * * 5"
    displayName: Weekly Sprint Report
    branches:
      include:
        - main

steps:
  - script: |
      pip install claude-workflow-framework
      cwf workflow run sprint-execution
    env:
      AZURE_DEVOPS_PAT: $(AZURE_DEVOPS_PAT)
      ANTHROPIC_API_KEY: $(ANTHROPIC_API_KEY)
```

## Success Criteria

- ✅ Daily standup reports generated and shared
- ✅ Blockers identified and assigned for resolution
- ✅ Sprint progress visible to all stakeholders
- ✅ Quality metrics tracked against standards
- ✅ Risks flagged early for mitigation
- ✅ Team stays aligned on sprint goals

## Configuration

**Agents Used:**
- Scrum Master (daily reports)- Senior Engineer (blocker analysis)- Security Specialist (weekly security review)
**Quality Standards:**
- Test Coverage: ≥ 80%
- Critical Vulnerabilities: ≤ 0
- High Vulnerabilities: ≤ 0
- Code Complexity: ≤ 10

**Report Frequency:**
- Daily: Standup reports
- Weekly: Comprehensive status
- Ad-hoc: On-demand health checks

---

*Generated by Claude Workflow Framework for Trusted AI Development Workbench*