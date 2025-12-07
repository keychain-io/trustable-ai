# Backlog Grooming Workflow

**Project**: trusted-ai-development-workbench
**Workflow**: Backlog Grooming
**Purpose**: Refine and prioritize backlog items for upcoming sprints

## Output Formatting Requirements

**IMPORTANT**: Use actual Unicode emojis in reports, NOT GitHub-style shortcodes:
- ✅ Ready for sprint | ⚠️ Needs refinement | ❌ Not ready
- 🔴 High priority | 🟡 Medium | 🟢 Low
- 📋 User story | 🐛 Bug | 🔧 Technical debt

## Overview

This workflow analyzes unrefined backlog items, assigns business value scores, identifies missing requirements, and prepares items for sprint planning.

## Prerequisites

- Access to azure-devops (https://dev.azure.com/keychainio/)
- Backlog items in "New" or "Proposed" state
- Understanding of project priorities and business goals

## Initialize Work Tracking

```python
# Initialize work tracking adapter (auto-selects Azure DevOps or file-based)
import sys
sys.path.insert(0, ".claude/skills")
from work_tracking import get_adapter

adapter = get_adapter()
print(f"📋 Work Tracking: {adapter.platform}")
```

## Workflow Steps

### Step 0: Epic Detection and Decomposition

**Detect Epic-sized items in backlog:**

```python
# Query for Epics and large items
epics = adapter.query_work_items(
    filters={
        'System.State': ['New', 'Proposed'],
        'System.WorkItemType': ['Epic']
    }
)

# Also find items with large story point estimates (>30 pts)

print(f"📦 Found {len(epics)} Epic-sized items requiring decomposition")
for epic in epics:
    print(f"  WI-{epic['id']}: {epic.get('title', 'Untitled')} [{epic.get('type', 'Unknown')}]")
```

**For each Epic, decompose into Features and Tasks:**

**Call `/senior-engineer` agent for each Epic:**

```
## YOUR TASK: Decompose Epic into Features and Tasks

Analyze the following Epic and break it down into a hierarchy of Features and Tasks.

### Epic Details
- ID: {epic['id']}
- Title: {epic['title']}
- Description: {epic['description']}
- Business Value: {epic.get('business_value', 'Not specified')}

### Decomposition Requirements

1. **Feature Extraction**: Identify 3-7 Features that comprise this Epic
   - Each Feature should represent a cohesive capability that is measurable, testable, and valuable
   - Features should be independently deliverable
   - Estimate story points for each Feature (5-20 pts ideal)

2. **Task Breakdown**: For each Feature, identify 2-5 Tasks that implement the Feature and, if applicable, deploy it
   - Exactly one task should request the complete implementation of the Feature code and unit and integration tests, and it should contain enough context for an engineer to implement both the code and the tests solely based on the Task description and if any attachments. The Task should include detailed function specification of each testable technical task for an engineer to implement. The tests should be falsifiable and comprehensive relative to the scope and goals of the Feature. The test type and requirements should be project-stage aware, be labelled according to the project's test classification taxonomy, and be designed to provide evidence that the feature was implemented completely.
   - Exactly one tasks should request the running of the tests created in the implementation task, collecting results, verifying falsifiable of the tests, confirming code coverage, and confirming feature coverage of the tests.
   - Deployment tasks should be included if the Feature requires deployment to a dev, staging, or production environment.
   - All tasks should be actionable and specific and not overlap
   - Each Task should be completable within 7 days
   - Include acceptance criteria for each Task

3. **Dependency Analysis**: Identify dependencies between Features/Tasks
   - Which Features must be completed before others?
   - Are there external dependencies (APIs, data, infrastructure)?

4. **Verification**: Ensure decomposition is complete
   - Sum of Feature story points should approximate Epic estimate
   - All Epic acceptance criteria covered by Feature/Task breakdown
   - No orphaned requirements (everything has a Feature/Task)

### Output Format

Return JSON with Epic decomposition:
```json
{
  "epic_id": {epic['id']},
  "epic_title": "{epic['title']}",
  "features": [
    {
      "title": "Feature 1: User Authentication",
      "description": "Implement secure user authentication with OAuth2",
      "story_points": 13,
      "acceptance_criteria": [
        "Users can log in with Google/GitHub OAuth",
        "JWT tokens issued on successful auth",
        "Token refresh mechanism implemented"
      ],
      "tasks": [
        {
          "title": "Task 1: Implement OAuth2 integration",
          "description": "Integrate Google/GitHub OAuth providers",
          "story_points": 5,
          "acceptance_criteria": [
            "OAuth callback endpoints created",
            "Provider SDK configured",
            "User profile data fetched"
          ]
        },
        {
          "title": "Task 2: Implement JWT token service",
          "description": "Create service for JWT generation and validation",
          "story_points": 3,
          "acceptance_criteria": [
            "JWT library configured",
            "Token generation tested",
            "Token validation tested"
          ]
        }
      ],
      "dependencies": []
    }
  ],
  "total_story_points": 65,
  "verification": {
    "epic_estimate": {epic.get('story_points', 'N/A')},
    "decomposed_total": 65,
    "variance_percent": 8,
    "all_acceptance_criteria_covered": true,
    "missing_requirements": []
  }
}
```
```

**After agent completes:**

1. Parse Epic decomposition JSON
2. Verify decomposition quality (story points sum, acceptance criteria coverage)
3. Create work item hierarchy:

```python
epic_id = epic['id']
decomposition = agent_result  # JSON from agent

# Create Features under Epic
for feature_data in decomposition['features']:
    # Create Feature work item
    feature = adapter.create_work_item(
        work_item_type="Feature",
        title=feature_data['title'],
        description=f"""{feature_data['description']}

## Acceptance Criteria
{chr(10).join(f"- {ac}" for ac in feature_data['acceptance_criteria'])}

## Parent Epic
WI-{epic_id}: {epic['title']}
""",
        fields={
            'System.Parent': epic_id,  # Link to parent Epic
            'System.Tags': 'epic-decomposed'
        }
    )

    print(f"  ✓ Created Feature WI-{feature['id']}: {feature_data['title']}")

    # Create Tasks under Feature
    for task_data in feature_data.get('tasks', []):
        task = adapter.create_work_item(
            work_item_type="Task",
            title=task_data['title'],
            description=f"""{task_data['description']}

## Acceptance Criteria
{chr(10).join(f"- {ac}" for ac in task_data['acceptance_criteria'])}

## Parent Feature
WI-{feature['id']}: {feature_data['title']}
""",
            fields={
                'System.Parent': feature['id'],  # Link to parent Feature
                'System.Tags': 'epic-decomposed'
            }
        )

        print(f"    ✓ Created Task WI-{task['id']}: {task_data['title']}")

# Update Epic state
adapter.update_work_item(
    work_item_id=epic_id,
    state='Proposed',  # Mark as decomposed but not yet approved
    fields={'System.Tags': epic.get('tags', '') + ';decomposed'}
)

print(f"✅ Epic WI-{epic_id} decomposed into {len(decomposition['features'])} Features")
```

4. Verify hierarchy created correctly:

```python
# Query children of Epic
children = adapter.query_work_items(
    filters={'System.Parent': epic_id}
)

expected_count = len(decomposition['features'])
actual_count = len(children)

if actual_count != expected_count:
    print(f"⚠️  Verification failed: Expected {expected_count} Features, got {actual_count}")
else:
    print(f"✅ Verification passed: All {expected_count} Features created")

# Verify story points sum
```


**If no Epics found, skip to Step 1.**

### Step 1: Business Analyst - Backlog Analysis

1. **Read agent definition:** `.claude/agents/business-analyst.md`
2. **Task:** "Analyze the following backlog items and perform business value assessment:
   - Review each item for clarity and completeness
   - Assign business value scores (1-100)
   - Identify items that align with strategic goals
   - Flag items with missing acceptance criteria
   - Recommend prioritization"
3. **Spawn agent** using Task tool with model `claude-sonnet-4.5`
4. **Query backlog items:**
   ```bash
   # Get backlog items in New/Proposed state
   az boards query --wiql "SELECT [System.Id], [System.Title], [System.State] FROM WorkItems WHERE [System.TeamProject] = 'Trusted AI Development Workbench' AND [System.State] IN ('New', 'Proposed') AND [System.WorkItemType] = 'User Story' ORDER BY [System.ChangedDate] DESC" --output json
   ```
5. **Display output** to user:
   - Read task result
   - Format business value assessments
   - Display recommendations
6. **Collect:**
   - Business value scores for each item
   - Priority recommendations
   - Gaps and missing information

### Step 2: Project Architect - Technical Feasibility Review

1. **Read agent definition:** `.claude/agents/architect.md`
2. **Task:** "Review backlog items for technical feasibility and architecture implications:
   - Identify technical dependencies
   - Assess complexity and risk
   - Flag items requiring architecture decisions
   - Recommend technical spikes if needed
   - Estimate relative effort (T-shirt sizing)"
3. **Spawn agent** using Task tool with model `claude-opus-4`
4. **Input:** Backlog items from Step 1
5. **Display output** to user
6. **Collect:**
   - Technical risk assessments
   - Dependency mappings
   - Spike recommendations
   - Effort estimates (S/M/L/XL)

### Step 3: Human Review & Approval Gate

**Instructions for User:**
1. Review the business value assessments and technical evaluations
2. Adjust priorities based on your knowledge
3. Confirm which items should be refined further
4. Type "proceed" to continue with updates

**Wait for user confirmation before proceeding.**

### Step 4: Update Work Items with Findings

1. **For each backlog item to update:**
   - Update Business Value field
   - Update Technical Risk field
   - Add refinement notes to description
   - Update state to "Ready" if complete

2. **Update work items with refinement data:**
   ```python
   # Update each refined item
   for item in refined_items:
       result = adapter.update_work_item(
           work_item_id=item['id'],
           state='Ready' if item.get('is_complete') else 'Proposed',
           fields={
               'Custom.BusinessValue': item.get('business_value'),
               'Custom.TechnicalRisk': item.get('technical_risk'),
           },
           verify=True
       )

       # Add grooming notes as comment
       if item.get('notes'):
           adapter.add_comment(
               work_item_id=item['id'],
               comment=f"Grooming notes: {item['notes']}"
           )

       print(f"  ✓ Updated WI-{item['id']}: {item.get('title', 'Unknown')}")
   ```

3. **Track progress:**
   ```python
   state.record_work_item_updated(item_id, {'action': 'refined'})
   ```

### Step 5: Generate Grooming Summary

Create summary report with:
- Total items reviewed
- Items moved to "Ready" state
- Items requiring more information
- Recommended items for next sprint
- Outstanding technical questions

## Success Criteria

- ✅ All backlog items have business value scores
- ✅ Technical risks identified and documented
- ✅ Items ready for sprint planning are in "Ready" state
- ✅ Missing information clearly flagged
- ✅ Priorities aligned with business goals

## Post-Workflow

1. Share grooming summary with stakeholders
2. Schedule follow-up meetings for unclear items
3. Update product roadmap based on priorities
4. Prepare refined backlog for sprint planning

## Configuration

**Agents Used:**
- Business Analyst- Project Architect
**Quality Standards:**
- Business value scoring: 1-100 scale
- Technical risk: Low/Medium/High
- Minimum acceptance criteria: Yes/No

**Work Item Types:**
- User Story
- Feature

---

*Generated by Trustable AI Workbench for trusted-ai-development-workbench*