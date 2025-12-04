# Epic Breakdown Workflow

**Project**: trusted-ai-development-workbench
**Workflow**: Epic Breakdown
**Purpose**: Decompose an Epic into 3-5 deliverable Features (large capabilities, 15-30 pts each)

## Output Formatting Requirements

**IMPORTANT**: Use actual Unicode emojis in reports, NOT GitHub-style shortcodes.

---

## Standard Scrum Hierarchy

```
Epic (months)
  └── Feature (weeks) ← THIS WORKFLOW CREATES THESE
       └── User Story (days) ← Created by /backlog-grooming
            └── Task (hours) ← Created by /sprint-planning
```

**What is a Feature?**
- A large, deliverable capability (not a technical task)
- Typically 15-30 story points
- Takes 1-2 sprints to complete
- Has clear business value
- Can be broken into 3-8 User Stories

**Examples:**
- ✅ GOOD: "Artifact Hygiene System" (capability spanning multiple stories)
- ❌ BAD: "Add cleanup command" (this is a User Story, not a Feature)

---

## Where This Fits

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  SOFTWARE LIFECYCLE - SCRUM PROCESS                                         │
│                                                                             │
│  /roadmap-planning                                                          │
│      │  Creates Epics (large business initiatives, months)                 │
│      ▼                                                                      │
│  ══════════════════                                                         │
│  YOU ARE HERE: /epic-breakdown                                              │
│  ══════════════════                                                         │
│      │  Input: Epic from Azure DevOps                                      │
│      │  Output: 3-5 Features (deliverable capabilities, weeks)             │
│      ▼                                                                      │
│  /backlog-grooming                                                          │
│      │  Breaks Features into User Stories (days)                           │
│      ▼                                                                      │
│  /sprint-planning                                                           │
│      │  Breaks User Stories into Tasks (hours)                             │
│      ▼                                                                      │
│  /feature-implementation                                                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

1. **Epic exists** with ID (e.g., EPIC-001)
2. **Epic has clear scope** (business justification, success metrics)

---

## Initialize Workflow

```python
# Get Epic to break down
epic_id = input("Epic ID to break down (e.g., EPIC-001): ")

# Load Epic details from work tracking
from pathlib import Path
epic_file = Path(f".claude/work-items/{epic_id}.yaml")
if epic_file.exists():
    import yaml
    with open(epic_file) as f:
        epic = yaml.safe_load(f)
    print(f"✅ Loaded Epic: {epic['title']}")
else:
    print(f"❌ Epic {epic_id} not found at {epic_file}")
```

---

## Phase 1: Epic Analysis

### Step 1.1: Analyze Scope and Identify Features

**Call `/business-analyst` with the following task:**

```
## YOUR TASK: Analyze Epic and Identify Features (NOT User Stories)

You are analyzing an Epic to identify 3-5 large, deliverable FEATURES (capabilities).

**CRITICAL**: Features are NOT individual user stories. A Feature is a large capability that will be broken down into multiple User Stories later.

### Examples of Proper Feature Granularity

✅ **GOOD Features** (large capabilities, 15-30 pts):
- "Problem-Focused Documentation System" (spans multiple documentation files)
- "Artifact Hygiene System" (includes scanning, detection, remediation)
- "Context Intelligence System" (includes loading, validation, verification)

❌ **BAD Features** (these are User Stories, not Features):
- "Update core/CLAUDE.md" (too small, this is a story)
- "Add cleanup command" (too small, this is a story)
- "Create schema" (too small, this is a story)

### Epic Information
- ID: {epic_id}
- Title: {epic['title']}
- Description: {epic.get('description', 'No description')}
- Business Justification: {epic.get('business_justification', 'Not provided')}
- Acceptance Criteria: {epic.get('acceptance_criteria', [])}

### Project Context
- Project: trusted-ai-development-workbench
- Type: cli-tool
- Tech Stack: Python

### Your Analysis Must Include:

1. **User Personas**
   - Who are the users affected by this Epic?
   - What are their goals?

2. **User Journeys**
   - What workflows does this Epic enable?
   - What's the user experience flow?

3. **Features** (3-5 large capabilities, NOT 8+ small stories)
   For each Feature, provide:
   - **Title**: Capability-focused system/feature name (e.g., "Artifact Hygiene System")
   - **Summary**: What large capability does this provide? (2-3 sentences)
   - **Business Value**: High / Medium / Low with rationale
   - **Estimated Story Points**: 15-30 (will span multiple User Stories)
   - **User Stories Preview**: List 3-6 stories this Feature will break down into
   - **Dependencies**: Other Features this depends on
   - **Sequence**: Suggested implementation order (1, 2, 3...)

4. **Scope Questions**
   - What needs Product Owner clarification?

### Output Format

Return your analysis as a JSON structure that can be parsed.
```

**After the agent completes:**
- Parse the JSON output
- Store in `business_analysis` variable
- Note any scope questions for Phase 2

---

### Step 1.2: Technical Architecture Review

**Call `/project-architect` with the following task:**

```
## YOUR TASK: Technical Architecture Review

Review the proposed Features for technical feasibility and architecture considerations.

### Epic
{epic['title']}

### Proposed Features from Business Analysis
{business_analysis['features']}

### Tech Stack
**Project Type**: cli-tool
**Languages**: Python
**Frameworks**: pytest, pytest
**Platforms**: Docker

### For Each Feature, Analyze:

1. **Technical Components**
   - APIs, UI components, database changes
   - New services or modules needed

2. **Architecture Patterns**
   - Patterns to apply (Repository, CQRS, etc.)
   - Integration approach

3. **Technical Risks**
   - What could go wrong?
   - Mitigation strategies

4. **Non-Functional Requirements**
   - Performance targets
   - Security considerations
   - Scalability needs

5. **Complexity Rating**: S / M / L / XL

### Additional Technical Features

Identify any technical enablers not in the business list:
- Infrastructure setup
- Database migrations
- Security implementations
- API versioning

### Recommended Sequence

Based on technical dependencies, what order should Features be implemented?

### Output Format

Return as JSON structure.
```

**After the agent completes:**
- Parse the JSON output
- Merge technical analysis with business analysis
- Store in `architecture_analysis` variable

---

### Step 1.3: Estimate Features

**Call `/senior-engineer` with the following task:**

```
## YOUR TASK: Estimate Features

Provide story point estimates for each Feature.

### Features to Estimate
{combined_features from steps 1.1 and 1.2}

### Technical Analysis
{architecture_analysis}

### Estimation Guidelines
- 1-2 points: Simple, well-understood, < 1 day
- 3-5 points: Moderate complexity, 1-3 days
- 8 points: Complex, needs design, 3-5 days
- 13+ points: Should be broken down further

### For Each Feature, Provide:

1. **Story Points**: 1, 2, 3, 5, 8, 13, or 21
2. **Confidence**: High / Medium / Low
3. **Assumptions**: What you're assuming
4. **Risks**: What could impact the estimate
5. **Needs Breakdown**: true if 13+ points

### Summary

- Total story points across all Features
- Recommended number of sprints (assuming 20-30 pts/sprint)
- Features that need further breakdown

### Output Format

Return as JSON structure.
```

**After the agent completes:**
- Parse the JSON output
- Flag any Features needing breakdown
- Calculate totals

---

## Phase 2: Scope Clarification (If Needed)

### Step 2.1: Address Scope Questions

If the Business Analyst identified scope questions:

```
⚠️ SCOPE QUESTIONS NEED CLARIFICATION

The following questions need answers before proceeding:

1. [Question from business_analysis]
2. [Question from business_analysis]

Options:
- Answer now: Provide clarification
- Skip: Defer to Product Owner
- Cancel: Stop workflow
```

### Step 2.2: Validate Feature Size

Check that Features are properly sized (15-30 story points):

```
✅ PROPER FEATURE SIZING

Features should be 15-30 story points:
- Too small (<15 pts): May actually be User Stories, consider consolidating
- Proper size (15-30 pts): Good Feature granularity
- Too large (>30 pts): Consider splitting into multiple Features

If Features are outside this range:
- [c] Consolidate small items into larger Features
- [s] Split large Features into multiple
- [k] Keep as-is and note for backlog grooming
```

---

## Phase 3: Human Review & Approval

### Step 3.1: Present Feature Breakdown

Display a summary for human review:

```
════════════════════════════════════════════════════════════════════════════════
📋 EPIC BREAKDOWN REVIEW - {epic['title']}
════════════════════════════════════════════════════════════════════════════════

👥 User Personas: {personas}
🚶 User Journeys: {count}

📦 PROPOSED FEATURES ({count} Features, target: 3-5):
   Total Story Points: {total}
   Estimated Sprints: {sprints}

  1. [Feature Title] - {points} pts (Business Value: High)
     Summary: Large deliverable capability description
     Will break down into: 5 User Stories
     Dependencies: [Other Feature]

     Preview User Stories:
     - Story 1 name
     - Story 2 name
     - ...

  2. [Feature Title] - {points} pts (Business Value: Medium)
     ...

════════════════════════════════════════════════════════════════════════════════
```

### Step 3.2: Approval Gate

```
Review and approve Features to create:
[yes] Approve all Features
[no] Cancel
[select] Choose which to approve
```

---

## Phase 4: Feature Creation

### Step 4.1: Create Features in Work Tracking

For each approved Feature, create a Feature work item (NOT User Stories yet - those come in /backlog-grooming):

```python
# Create Feature work item (large capability)
feature_data = {
    'id': f"FEATURE-{next_id}",
    'type': 'Feature',
    'title': feature['title'],  # e.g., "Artifact Hygiene System"
    'status': 'New',
    'parent': epic_id,
    'description': f"""## Summary
{feature['summary']}

## Business Value
{feature['business_value']}: {feature['business_value_rationale']}

## Scope
{feature['scope_description']}

## User Stories
Will be broken down into {len(feature['user_stories_preview'])} User Stories during backlog grooming:
{feature['user_stories_preview']}

## Success Criteria
{success_criteria}

## Estimated Effort
{story_points} story points total

---
*Created via /epic-breakdown workflow*
""",
    'story_points': feature['story_points'],  # 15-30 for Feature
    'business_value': feature['business_value'],
    'dependencies': feature['dependencies']
}

# Create in Azure DevOps
az boards work-item create \
  --type "Feature" \
  --title "{title}" \
  --description "{description}" \
  --org "{org}" \
  --project "{project}"

# Link to Epic
az boards work-item relation add \
  --id {feature_id} \
  --relation-type "parent" \
  --target-id {epic_id}
```

**IMPORTANT**: Do NOT create User Stories at this stage. Features will be broken down into User Stories during `/backlog-grooming`.

### Step 4.2: Create Dependency Links

For Features with dependencies, create links:

```
✅ Feature 1002 depends on Feature 1001
✅ Feature 1003 depends on Feature 1001
```

---

## Phase 5: Completion

### Step 5.1: Update Epic

Add comment to Epic summarizing breakdown:

```markdown
## Epic Breakdown Complete

**Features Created**: 5
**Total Story Points**: 34

### Features:
- [FEATURE-001] User can save tasks to JSON (5 pts)
- [FEATURE-002] User can load tasks from JSON (5 pts)
- ...
```

### Step 5.2: Generate Breakdown Document

Save to `docs/epics/epic-{epic_id}-breakdown.md`:

```markdown
# Epic Breakdown: {epic['title']}

**Epic ID**: {epic_id}
**Date**: {date}
**Total Features**: {count}
**Total Story Points**: {total}

## Features

| ID | Feature | Points | Value | Dependencies |
|----|---------|--------|-------|--------------|
| FEATURE-001 | ... | 5 | High | None |

## Implementation Order
1. FEATURE-001 (no dependencies)
2. FEATURE-002 (depends on 001)
...

## Next Steps
1. Run `/backlog-grooming` to break Features into User Stories
2. Run `/sprint-planning` to break User Stories into Tasks and assign to sprint
```

### Step 5.3: Summary

```
════════════════════════════════════════════════════════════════════════════════
✅ EPIC BREAKDOWN COMPLETE
════════════════════════════════════════════════════════════════════════════════

📦 Created {count} Features (target: 3-5) from Epic {epic_id}
🔢 Total Story Points: {total}
📅 Estimated Sprints: {sprints}

**Standard Scrum Process:**
Epic (months) → [Features (weeks)] ← YOU ARE HERE
                     ↓
                User Stories (days) ← Next: /backlog-grooming
                     ↓
                Tasks (hours) ← Then: /sprint-planning

➡️ Next: Run /backlog-grooming to break Features into User Stories
```

---

## Agent Commands Used

| Step | Agent Command | Purpose |
|------|---------------|---------|
| 1.1 | `/business-analyst` | Identify Features & user stories |
| 1.2 | `/project-architect` | Technical feasibility |
| 1.3 | `/senior-engineer` | Story point estimates |

**Key**: Each agent command spawns a **fresh context window** via the Task tool.

---

## Configuration

**Work Tracking Platform:** azure-devops

**Work Item Types:**
- Epic: Epic (input)
- Feature: Feature (output)

**Quality Standards:**
- Test Coverage: >= 80%
- Code Complexity: <= 10

---

*Generated by Trustable AI Workbench for trusted-ai-development-workbench*