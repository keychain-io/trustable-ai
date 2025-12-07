# Epic Breakdown Workflow

**Project**: trusted-ai-development-workbench
**Workflow**: Epic Breakdown
**Purpose**: Decompose an Epic into deliverable Features with clear scope

## Output Formatting Requirements

**IMPORTANT**: Use actual Unicode emojis in reports, NOT GitHub-style shortcodes.

---

## Where This Fits

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  SOFTWARE LIFECYCLE - UPSTREAM WORKFLOWS                                    │
│                                                                             │
│  /roadmap-planning                                                          │
│      │  Creates Epics from business strategy                               │
│      ▼                                                                      │
│  ══════════════════                                                         │
│  YOU ARE HERE: /epic-breakdown                                              │
│  ══════════════════                                                         │
│      │                                                                      │
│      │  Input: Epic from azure-devops                      │
│      │  Output: Features linked to Epic                                    │
│      ▼                                                                      │
│  /backlog-grooming → /sprint-planning → /feature-implementation            │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

1. **Epic exists** with ID (e.g., EPIC-001)
2. **Epic has clear scope** (business justification, success metrics)

---

## Initialize Workflow

```python
# Initialize work tracking adapter
import sys
sys.path.insert(0, ".claude/skills")
from work_tracking import get_adapter

adapter = get_adapter()
print(f"📋 Work Tracking: {adapter.platform}")

# Get Epic to break down
epic_id = input("Epic ID to break down (e.g., 1001): ")

# Load Epic details from work tracking system
try:
    epic = adapter.get_work_item(int(epic_id))
    print(f"✅ Loaded Epic #{epic_id}: {epic.get('title', 'Untitled')}")

    # Extract fields for workflow
    epic_title = epic.get('title', '')
    epic_description = epic.get('description', '')
    epic_tags = epic.get('tags', '')
except Exception as e:
    print(f"❌ Failed to load Epic #{epic_id}: {e}")
    print("   Make sure the Epic exists in azure-devops")
    exit(1)
```

---

## Phase 1: Epic Analysis

### Step 1.1: Analyze Scope and Identify Features

**Call `/business-analyst` with the following task:**

```
## YOUR TASK: Analyze Epic and Identify Features

You are analyzing an Epic to identify the user-facing deliverables (Features).

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

3. **Features** (3-8 distinct deliverables)
   For each Feature, provide:
   - **Title**: User-focused, with clear scope indication

     **IMPORTANT TITLE SCOPING RULES:**
     - Titles MUST indicate the specific aspect being delivered, not the entire concept
     - For multi-phase work, include phase qualifier: "- Strategy Design", "- Implementation", "- Testing"
     - Match titles to actual deliverables that will be completed

     ✅ GOOD Examples:
     - "Adversarial Testing - Strategy Design"
     - "API Authentication - OAuth Integration"
     - "Export Feature - JSON Format Support"
     - "User Dashboard - Read-Only View"

     ❌ BAD Examples (too broad for single Feature):
     - "Adversarial Testing" (is this strategy? implementation? both?)
     - "API Authentication" (which method? which components?)
     - "Export Feature" (which formats? which data?)
     - "User Dashboard" (view? edit? admin? all?)

     **Title Pattern**: "[Feature Area] - [Specific Scope]"

   - **User Story**: "As a [persona], I want [capability] so that [benefit]"
   - **Acceptance Criteria**: 3-5 specific, testable criteria
   - **Business Value**: High / Medium / Low
   - **Dependencies**: Other Features this depends on
   - **Sequence**: Suggested implementation order (1, 2, 3...)

   - **Completion Criteria**: For Features that produce code
     - Code must compile without errors
     - Developer-level unit tests must pass
     - Matches human concept of "complete" for that specific scope
     - Can be demonstrated to stakeholders as working

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

**Call `/architect` with the following task:**

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
**Frameworks**: pytest
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

### Step 2.2: Handle Large Features

If any Features are 13+ story points:

```
⚠️ FEATURES TOO LARGE

The following Features should be broken down further:

📦 [Feature Title] - 13 points
   Recommended: Split into 2-3 smaller Features

Options:
- [b] Break down now (call /business-analyst again)
- [k] Keep as-is (accept risk)
- [d] Defer to backlog grooming
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

📦 PROPOSED FEATURES ({count}):
   Total Story Points: {total}
   Estimated Sprints: {sprints}

  1. [Feature Title]
     Story Points: 5 | Complexity: M | Business Value: High
     User Story: As a..., I want..., so that...
     Dependencies: [Other Feature]

  2. [Feature Title]
     ...

🔧 TECHNICAL ENABLERS:
  - [Technical Feature] (prerequisite for: [Business Feature])

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

For each approved Feature:

```python
# Build Feature description
description = f"""## User Story
{feature['user_story']}

## Acceptance Criteria
{acceptance_criteria}

## Technical Components
{technical_components}

## Estimation
- Story Points: {estimate['story_points']}
- Confidence: {estimate['confidence']}

## Dependencies
{', '.join(feature['dependencies']) if feature['dependencies'] else 'None'}

---
*Created via /epic-breakdown workflow*
"""

# Create Feature work item via adapter
try:
    result = adapter.create_work_item(
        work_item_type='Feature',
        title=feature['title'],
        description=description,
        fields={
            'System.Tags': f"epic-breakdown; parent-epic-{epic_id}; business-value-{feature['business_value'].lower()}"
        }
    )

    feature_id = result['id']
    print(f"✅ Created Feature #{feature_id}: {feature['title']}")

    # Link to parent Epic
    try:
        adapter.link_work_items(feature_id, int(epic_id), "Parent")
        print(f"   🔗 Linked to Epic #{epic_id}")
    except Exception as e:
        print(f"   ⚠️ Failed to link to Epic: {e}")

    # Store for dependency linking
    feature_ids[feature['title']] = feature_id

except Exception as e:
    print(f"❌ Failed to create Feature '{feature['title']}': {e}")
    continue
```

### Step 4.2: Create Dependency Links

For Features with dependencies, create links:

```python
# Create dependency links between Features
for feature in approved_features:
    if feature['dependencies']:
        feature_id = feature_ids.get(feature['title'])
        if not feature_id:
            continue

        for dep_title in feature['dependencies']:
            dep_id = feature_ids.get(dep_title)
            if dep_id:
                try:
                    adapter.link_work_items(feature_id, dep_id, "Predecessor")
                    print(f"✅ Feature #{feature_id} depends on #{dep_id}")
                except Exception as e:
                    print(f"⚠️ Failed to link dependency: {e}")
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
1. Run `/backlog-grooming` to refine and prioritize
2. Run `/sprint-planning` to assign to sprints
```

### Step 5.3: Summary

```
════════════════════════════════════════════════════════════════════════════════
✅ EPIC BREAKDOWN COMPLETE
════════════════════════════════════════════════════════════════════════════════

📦 Created {count} Features from Epic {epic_id}
🔢 Total Story Points: {total}
📅 Estimated Sprints: {sprints}

➡️ Next: Run /backlog-grooming to refine Features
```

---

## Agent Commands Used

| Step | Agent Command | Purpose |
|------|---------------|---------|
| 1.1 | `/business-analyst` | Identify Features & user stories |
| 1.2 | `/architect` | Technical feasibility |
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