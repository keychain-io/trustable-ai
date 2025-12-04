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

1. **Read agent definition:** `.claude/agents/project-architect.md`
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