# Sprint Planning Workflow

**Project**: Trusted AI Development Workbench
**Workflow**: Sprint Planning
**Purpose**: Plan a sprint by analyzing backlog, reviewing architecture, and creating work items

## Output Formatting Requirements

**IMPORTANT**: Use actual Unicode emojis in reports, NOT GitHub-style shortcodes.

---

## Workflow Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  SPRINT PLANNING - Agent Orchestration                                      │
│                                                                             │
│  Step 1: /business-analyst → Prioritized backlog                           │
│  Step 2: /project-architect → Architecture review                          │
│  Step 3: /security-specialist → Security review                            │
│  Step 4: /senior-engineer → Estimation & breakdown                         │
│  Step 5: /scrum-master → Sprint plan assembly                              │
│  Step 6: Human Approval Gate                                               │
│  Step 7: Work Item Creation                                                │
│                                                                             │
│  Each agent command spawns a FRESH CONTEXT WINDOW via Task tool            │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Initialize Workflow

```python
# Get sprint information
sprint_number = input("Sprint number: ")
team_capacity = int(input("Team capacity (story points): "))

print(f"📋 Planning Sprint {sprint_number}")
print(f"👥 Team capacity: {team_capacity} points")
```

---

## Step 1: Prioritize Backlog

**Call `/business-analyst` with the following task:**

```
## YOUR TASK: Prepare Prioritized Backlog

Analyze the backlog and prepare a prioritized list for Sprint {sprint_number}.

### Project Context
- Project: Trusted AI Development Workbench
- Type: library
- Tech Stack: Python

### Available Backlog Items
{List Features from .claude/work-items/ with status=New or status=Ready}

### For Each Backlog Item, Analyze:

1. **Business Value**
   - Revenue impact (High/Medium/Low)
   - Customer impact (High/Medium/Low)
   - Strategic alignment (High/Medium/Low)
   - Overall Business Value Score (1-100)

2. **Priority Recommendation**
   - P0: Must have this sprint
   - P1: Should have this sprint
   - P2: Nice to have
   - P3: Can wait

3. **Dependencies**
   - What must be done before this?
   - What does this block?

### Output Format

Return as JSON:
```json
{
  "prioritized_backlog": [
    {
      "id": "FEATURE-001",
      "title": "...",
      "business_value_score": 85,
      "priority": "P0",
      "dependencies": [],
      "recommendation": "Include in sprint"
    }
  ],
  "recommended_for_sprint": ["FEATURE-001", "FEATURE-002"],
  "total_points_recommended": 25
}
```
```

**After the agent completes:**
- Parse the JSON output
- Store prioritized backlog
- Note recommended items for sprint

---

## Step 2: Architecture Review

**Call `/project-architect` with the following task:**

```
## YOUR TASK: Architecture Review for Sprint

Review the planned Features for architectural readiness.

### Planned Features
{prioritized_backlog from Step 1}

### Tech Stack
**Project Type**: library
**Languages**: Python
**Platforms**: Docker

### For Each Feature, Assess:

1. **Architecture Readiness**
   - Ready to implement
   - Needs design work first
   - Blocked by technical debt

2. **Technical Risks**
   - What could go wrong?
   - Mitigation strategies

3. **Infrastructure Needs**
   - New services required?
   - Database changes?
   - API changes?

4. **Deployment Considerations**
   - Configuration changes?
   - Migration scripts needed?
   - Feature flags?

### Output Format

Return as JSON with architecture decisions, risks, and deployment checklist.
```

**After the agent completes:**
- Store architecture analysis
- Note any blocking technical issues

---

## Step 3: Security Review

**Call `/security-specialist` with the following task:**

```
## YOUR TASK: Security Review

Review planned Features for security implications.

### Planned Features
{prioritized_backlog from Step 1}

### Quality Standards
- Critical Vulnerabilities: Max 0
- High Vulnerabilities: Max 0

### For Each Feature, Assess:

1. **Security Risks**
   - Authentication/authorization changes?
   - Data handling changes?
   - External integrations?

2. **Compliance Requirements**
   - Data privacy implications?
   - Audit logging needed?

3. **Security Testing Needs**
   - Penetration testing?
   - Security scanning?

### Output Format

Return as JSON with security risks, compliance items, and testing needs.
```

---

## Step 4: Estimation and Task Breakdown

This is the most critical step - creating detailed specifications and estimates.

**Call `/senior-engineer` with the following task:**

```
## YOUR TASK: Estimation and Task Breakdown

Estimate the planned Features and break them into Tasks.

### Features to Estimate
{prioritized_backlog from Step 1}

### Architecture Analysis
{architecture review from Step 2}

### Security Analysis
{security review from Step 3}

### Team Capacity
{team_capacity} story points

### For Each Feature, Provide:

1. **Story Point Estimate** (1, 2, 3, 5, 8, 13, 21)
2. **Confidence Level** (High/Medium/Low)
3. **Task Breakdown**
   - Each task should be 1-3 points
   - Include implementation, testing, documentation tasks
4. **Acceptance Criteria**
   - 3-5 specific, testable criteria per Feature
5. **Technical Notes**
   - Implementation approach
   - Key decisions made

### Work Item Format

For each work item (Feature or Task), provide:
```json
{
  "type": "Feature|Task",
  "title": "Clear, specific title",
  "description": "COMPREHENSIVE description (min 500 chars)",
  "acceptance_criteria": ["Criterion 1", "Criterion 2"],
  "story_points": 5,
  "priority": 2,
  "tags": ["tag1", "tag2"],
  "dependencies": ["Other item title"],
  "technical_notes": "Implementation approach..."
}
```

### CRITICAL Requirements

- Description must be MINIMUM 500 characters
- Include all acceptance criteria
- Story points must fit within team capacity ({team_capacity})

### Output Format

Return as JSON with work_items array and total_points.
```

**After the agent completes:**
- Validate all descriptions are 500+ characters
- Verify total points <= team capacity
- Store work items for creation

---

## Step 5: Assemble Sprint Plan

**Call `/scrum-master` with the following task:**

```
## YOUR TASK: Assemble Sprint Plan

Create the final sprint plan from all agent outputs.

### Inputs
- Prioritized Backlog: {from Step 1}
- Architecture Review: {from Step 2}
- Security Review: {from Step 3}
- Work Items & Estimates: {from Step 4}

### Team Capacity
{team_capacity} story points

### Create Sprint Plan Including:

1. **Sprint Goal**
   - Clear, measurable objective

2. **Selected Work Items**
   - Features and Tasks for this sprint
   - Total story points

3. **Risk Summary**
   - Top 3 technical risks
   - Top 3 security risks
   - Mitigation plans

4. **Dependencies**
   - External dependencies
   - Internal dependencies (order of work)

5. **Definition of Done**
   - What must be true for sprint success

### Output Format

Return as JSON with sprint_plan object.
```

---

## Step 6: Human Approval Gate

**STOP and display the sprint plan for human approval.**

```
════════════════════════════════════════════════════════════════════════════════
👤 HUMAN APPROVAL REQUIRED
════════════════════════════════════════════════════════════════════════════════

Sprint: {sprint_number}
Team Capacity: {team_capacity} points
Planned Work: {total_points} points
Utilization: {percentage}%

📋 FEATURES:
  1. [FEATURE-001] Feature Title (5 pts)
  2. [FEATURE-002] Another Feature (8 pts)
  ...

⚠️ ARCHITECTURE DECISIONS:
  - Decision 1
  - Decision 2

🔒 SECURITY ITEMS:
  - Security consideration 1
  - Security consideration 2

════════════════════════════════════════════════════════════════════════════════
Approve sprint plan? [yes/no/modify]:
```

**Do NOT proceed without user approval.**

---

## Step 7: Work Item Creation

After approval, create work items:

```python
for item in approved_work_items:
    # Create work item in .claude/work-items/
    work_item = {
        'id': f"{item['type'].upper()}-{next_id}",
        'type': item['type'],
        'title': item['title'],
        'status': 'New',
        'sprint': sprint_number,
        'description': item['description'],
        'acceptance_criteria': item['acceptance_criteria'],
        'story_points': item['story_points'],
        'priority': item['priority'],
        'tags': item['tags'],
        'dependencies': item['dependencies']
    }

    # Save to .claude/work-items/{id}.yaml
    # Create spec file for Features at docs/specifications/sprint-{n}/

print(f"✅ Created {count} work items")
print(f"📄 Created {spec_count} specification files")
```

---

## Step 8: Completion Summary

```
════════════════════════════════════════════════════════════════════════════════
✅ SPRINT PLANNING COMPLETE
════════════════════════════════════════════════════════════════════════════════

Sprint {sprint_number} is ready!

📊 Summary:
  - Features: {feature_count}
  - Tasks: {task_count}
  - Total Points: {total_points}
  - Capacity: {team_capacity}
  - Utilization: {percentage}%

📁 Files Created:
  - Work items in .claude/work-items/
  - Specifications in docs/specifications/sprint-{sprint_number}/

➡️ Next Steps:
  1. Run /feature-implementation for each Feature
  2. Run /daily-standup during sprint
  3. Run /sprint-completion at end

════════════════════════════════════════════════════════════════════════════════
```

---

## Agent Commands Used

| Step | Agent Command | Purpose |
|------|---------------|---------|
| 1 | `/business-analyst` | Prioritize backlog |
| 2 | `/project-architect` | Architecture review |
| 3 | `/security-specialist` | Security review |
| 4 | `/senior-engineer` | Estimation & breakdown |
| 5 | `/scrum-master` | Sprint plan assembly |

**Key**: Each agent command spawns a **fresh context window** via the Task tool.

---

## Configuration

**Work Tracking Platform:** file-based

**Work Item Types:**
- Epic: Epic
- Feature: Feature
- Task: Task

**Quality Standards:**
- Test Coverage: >= 80%
- Code Complexity: <= 10

---

*Generated by Trustable AI Workbench for Trusted AI Development Workbench*