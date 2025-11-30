# Sprint Planning Orchestration

Coordinate a complete sprint planning session across multiple specialized agents for Trusted AI Development Workbench.

**This workflow uses:**
- ✅ Workflow state management (re-entrant, idempotent)
- ✅ Workflow profiling (timing, tokens, costs)
- ✅ Comprehensive descriptions for ALL work items
- ✅ Deployment task automation
- ✅ Verified work item creation

## Prerequisites

```python
# Initialize workflow infrastructure
import sys
sys.path.insert(0, ".claude/skills")

from workflow_state import WorkflowState
from workflow_profiler import WorkflowProfiler
from azure_bulk_operations import AzureBulkOps
from azure_cli_wrapper import azure_cli
import json
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any
```

## Workflow Initialization

```python
# Get sprint information from user
sprint_number = input("Sprint number: ")
team_capacity = int(input("Team capacity (story points): "))

# Initialize state management
workflow_id = f"sprint-{sprint_number}"
state = WorkflowState("sprint-planning", workflow_id)
profiler = WorkflowProfiler(f"sprint-planning-{sprint_number}")

# Check for existing state
if state.state["status"] == "completed":
    print("⚠️  Sprint planning already completed for Sprint", sprint_number)
    state.print_summary()
    user_choice = input("Continue anyway? (yes/no): ")
    if user_choice.lower() != "yes":
        exit()
elif state.state["status"] == "in_progress":
    print("⚠️  Sprint planning in progress")
    print(f"Last step: {state.state.get('current_step', {}).get('name')}")
    print(f"Completed steps: {len(state.state['completed_steps'])}")
    user_choice = input("Resume from last checkpoint? (yes/no): ")
    if user_choice.lower() != "yes":
        exit()

# Store metadata
state.set_metadata("sprint_number", sprint_number)
state.set_metadata("team_capacity", team_capacity)
```

## Workflow Steps

Execute the following steps in sequence, spawning each agent with fresh context using the Task tool:

### Step 1: Business Analyst - Prioritized Backlog

```python
if not state.is_step_completed("business-analyst"):
    state.start_step("business-analyst", {"sprint": sprint_number})

    # Start profiling
    call_data = profiler.start_agent_call(
        agent_name="business-analyst",
        task_description=f"Prepare prioritized backlog for Sprint {sprint_number} with business value scores",
        model="claude-sonnet-4.5"
    )
```

1. **Read agent definition:** `.claude/workflow-state/../agents/business-analyst.md`
2. **Task:** "Prepare prioritized backlog for Sprint {sprint_number} with business value scores for Trusted AI Development Workbench"
3. **Spawn agent** using Task tool with model="claude-sonnet-4.5"
4. **Collect:** Prioritized backlog with business value scores

```python
    # After agent completes
    print("\n" + "=" * 80)
    print("📊 BUSINESS ANALYST OUTPUT")
    print("=" * 80)
    print(agent_output)
    print("=" * 80 + "\n")

    profiler.complete_agent_call(
        call_data,
        success=True,
        output_length=len(agent_output)
    )

    state.complete_step("business-analyst", result={
        "backlog": prioritized_backlog,
        "features": feature_list
    })
else:
    print("✓ Business analyst step already completed, loading cached result")
    prioritized_backlog = state.get_step_result("business-analyst")["backlog"]
    feature_list = state.get_step_result("business-analyst")["features"]
```

### Step 2: Project Architect - Architecture Review

```python
if not state.is_step_completed("project-architect"):
    state.start_step("project-architect")
    call_data = profiler.start_agent_call(
        "project-architect",
        f"Review architecture readiness for Sprint {sprint_number}",
        "claude-opus-4"
    )
```

1. **Read agent definition:** `.claude/workflow-state/../agents/project-architect.md`
2. **Task:** "Review architecture readiness for the planned features: {features from Step 1}

   **Tech Stack Context:**
   **Project Type**: library
**Languages**: Python
**Platforms**: Docker

   **Required Outputs:**
   - Architecture decisions
   - Technical risks
   - Infrastructure requirements
   - Deployment requirements checklist:
     ✓ Local Docker build/test needed?     ✓ Dev server deployment needed?     ✓ UAT server deployment needed?     ✓ Configuration changes needed?
     ✓ Database migrations required?
     ✓ Infrastructure provisioning needed?
   "

3. **Spawn agent** using Task tool with model="claude-opus-4"
4. **Collect:** Architecture decisions, technical risks, infrastructure requirements, deployment checklist

```python
    print("\n" + "=" * 80)
    print("🏗️  PROJECT ARCHITECT OUTPUT")
    print("=" * 80)
    print(agent_output)
    print("=" * 80 + "\n")

    profiler.complete_agent_call(call_data, success=True, output_length=len(agent_output))
    state.complete_step("project-architect", result={
        "architecture": architecture_decisions,
        "risks": technical_risks,
        "infrastructure": infrastructure_requirements,
        "deployment_checklist": deployment_checklist
    })
else:
    print("✓ Project architect step already completed")
    architecture_result = state.get_step_result("project-architect")
```

### Step 3: Security Specialist - Security Review

```python
if not state.is_step_completed("security-specialist"):
    state.start_step("security-specialist")
    call_data = profiler.start_agent_call(
        "security-specialist",
        f"Review security implications for Sprint {sprint_number}",
        "claude-sonnet-4.5"
    )
```

1. **Read agent definition:** `.claude/workflow-state/../agents/security-specialist.md`
2. **Task:** "Review security implications for planned features: {features from Step 1}

   **Quality Standards:**
   - Critical Vulnerabilities: 0 allowed
   - High Vulnerabilities: 0 allowed
   - Medium Vulnerabilities: 5 allowed
   "

3. **Spawn agent** using Task tool with model="claude-sonnet-4.5"
4. **Collect:** Security risks, compliance requirements, security testing needs

```python
    print("\n" + "=" * 80)
    print("🔒 SECURITY SPECIALIST OUTPUT")
    print("=" * 80)
    print(agent_output)
    print("=" * 80 + "\n")

    profiler.complete_agent_call(call_data, success=True, output_length=len(agent_output))
    state.complete_step("security-specialist", result={
        "security_risks": security_risks,
        "compliance": compliance_requirements,
        "testing_needs": security_testing_needs
    })
else:
    print("✓ Security specialist step already completed")
    security_result = state.get_step_result("security-specialist")
```

### Step 4: Senior Engineer - Estimation & Breakdown

```python
if not state.is_step_completed("senior-engineer"):
    state.start_step("senior-engineer")
    call_data = profiler.start_agent_call(
        "senior-engineer",
        f"Estimate and break down features for Sprint {sprint_number}",
        "claude-sonnet-4.5"
    )

    # Check if Features already have child tasks from previous planning
    bulk_ops = AzureBulkOps()
    features_with_children = {}

    for feature in feature_list:
        if feature.get('work_item_id'):
            wi = azure_cli.get_work_item(feature['work_item_id'])
            relations = wi.get('relations', [])
            children = [r for r in relations if r.get('rel') == 'System.LinkTypes.Hierarchy-Forward']
            if children:
                features_with_children[feature['work_item_id']] = children
                print(f"ℹ️  Feature WI-{feature['work_item_id']} already has {len(children)} child tasks")

    task = f"""
    Estimate and break down top features from backlog: 

    **IMPORTANT - Existing Child Tasks:**
    Features with existing child tasks: {features_with_children}

    **If a Feature already has child tasks:**
    - Review existing child tasks to see if they cover requirements
    - Only create NEW tasks to fill gaps
    - DO NOT duplicate existing tasks

    **If a Feature has NO child tasks:**
    - Create comprehensive breakdown as normal

    **Project Context:**
    - Name: Trusted AI Development Workbench
    - Type: library
    - Tech Stack: **Project Type**: library
**Languages**: Python
**Platforms**: Docker

    **Work Item Types:**
    - Epic: Epic
    - Feature: Feature
    - Task: Task

    **CRITICAL: For EACH work item, you MUST provide:**
    1. **title**: Clear, specific title (max 100 chars)
    2. **type**: Feature or Task
    3. **description**: COMPREHENSIVE description (MINIMUM 500 characters)
    4. **acceptance_criteria**: Bullet list of specific, testable criteria
    5. **story_points**: Estimate (1, 2, 3, 5, 8, 13, 21)
    6. **priority**: 1 (Critical), 2 (High), 3 (Medium), 4 (Low)
    7. **tags**: Relevant tags
    8. **dependencies**: List of dependent work item titles (if any)

    **Quality Standards:**
    - Test Coverage: Minimum 80%
    - Code Complexity: Maximum 10

    Team capacity:  story points

    FORMAT YOUR OUTPUT AS JSON.
    """

    # Execute agent
    # ... agent execution ...

    # Parse and validate output
    senior_output = json.loads(agent_output)
    work_items = senior_output["work_items"]

    # Validate descriptions
    for item in work_items:
        if len(item.get("description", "")) < 500:
            print(f"⚠️  Warning: {item['title']} has insufficient description")

    profiler.complete_agent_call(call_data, success=True, output_length=len(agent_output))
    state.complete_step("senior-engineer", result={
        "work_items": work_items,
        "total_points": sum(item["story_points"] for item in work_items)
    })
else:
    print("✓ Senior engineer step already completed")
    work_items = state.get_step_result("senior-engineer")["work_items"]
```

### Step 5: Scrum Master - Sprint Plan Creation

```python
if not state.is_step_completed("scrum-master"):
    state.start_step("scrum-master")
    call_data = profiler.start_agent_call(
        "scrum-master",
        f"Create sprint plan for Sprint {sprint_number}",
        "claude-sonnet-4.5"
    )
```

1. **Read agent definition:** `.claude/workflow-state/../agents/scrum-master.md`
2. **Task:** "Create sprint plan based on:
   - Backlog: {from Step 1}
   - Work Items: {from Step 4}
   - Team capacity: {capacity}
   - Architecture review: {from Step 2}
   - Security review: {from Step 3}

   **Sprint Configuration:**
   - Sprint naming: Sprint {number}
   - Iteration path: {project}\\{sprint}
   "

3. **Spawn agent** using Task tool
4. **Collect:** Final sprint plan with assigned work items

```python
    print("\n" + "=" * 80)
    print("📋 SCRUM MASTER OUTPUT - SPRINT PLAN")
    print("=" * 80)
    print(agent_output)
    print("=" * 80 + "\n")

    profiler.complete_agent_call(call_data, success=True, output_length=len(agent_output))
    state.complete_step("scrum-master", result={
        "sprint_plan": sprint_plan,
        "selected_work_items": selected_items
    })
else:
    print("✓ Scrum master step already completed")
    sprint_plan = state.get_step_result("scrum-master")["sprint_plan"]
```

### Step 6: Human Approval Gate

Present the complete sprint plan to the user:

```python
print("\n" + "=" * 80)
print("👤 HUMAN APPROVAL REQUIRED")
print("=" * 80)
print(f"Sprint: {sprint_name}")
print(f"Team Capacity: {team_capacity} story points")
print(f"Planned Work: {total_planned_points} story points")
print("\nFeatures:")
for item in selected_work_items:
    print(f"  • {item['title']} ({item['story_points']} points)")

print("\n⚠️  Architecture Decisions Requiring Approval:")
# ... display architecture decisions ...

print("\n🔒 Security Items Requiring Attention:")
# ... display security items ...

user_approval = input("\nApprove sprint plan? (yes/no): ")
if user_approval.lower() != "yes":
    print("❌ Sprint planning cancelled by user")
    state.fail_workflow("User declined sprint plan")
    exit()
```

**STOP and wait for user approval before proceeding.**

### Step 7: Sprint Iteration Setup

```python
if not state.is_step_completed("iteration-setup"):
    state.start_step("iteration-setup")

    sprint_name = "Sprint {number}".format(number=sprint_number)
    iteration_path = "{project}\\{sprint}".format(
        project="Trusted AI Development Workbench",
        sprint=sprint_name
    )

    # Create or verify sprint iteration exists
    # ... iteration setup code ...

    state.complete_step("iteration-setup", result={
        "sprint_name": sprint_name,
        "iteration_path": iteration_path
    })
```

### Step 8: Work Item Creation with Spec File Attachments

```python
if not state.is_step_completed("activation"):
    state.start_step("activation")

    created_work_items = []
    failed_items = []
    items_missing_attachments = []

    for item in work_items:
        try:
            # Create work item with verification
            result = azure_cli.create_work_item(
                work_item_type=item["type"],
                title=item["title"],
                description=item["description"],
                iteration=iteration_path,
                fields={
                    "Microsoft.VSTS.Scheduling.StoryPoints": item["story_points"],
                    "Microsoft.VSTS.Common.Priority": item["priority"],
                    "System.Tags": "; ".join(item["tags"]),
                },
                verify=True
            )

            work_item_id = result["id"]
            created_work_items.append(work_item_id)
            state.record_work_item_created(work_item_id, item)

            print(f"✓ Created WI-{work_item_id}: {item['title']}")

            # For Features/Epics with long descriptions, create and attach spec file
            if item["type"] in ["Feature",
                                "Epic"]:
                if len(item["description"]) > 300:
                    spec_dir = Path(f"docs/specifications/sprint-{sprint_number}")
                    spec_dir.mkdir(parents=True, exist_ok=True)

                    spec_file = spec_dir / f"WI-{work_item_id}-spec.md"
                    spec_content = f"""# {item['title']}

**Work Item:** WI-{work_item_id}
**Type:** {item['type']}
**Sprint:** Sprint {sprint_number}

## Description
{item['description']}

## Acceptance Criteria
{chr(10).join(f"- {c}" for c in item.get('acceptance_criteria', []))}

## Technical Notes
{item.get('technical_notes', 'See work item for details.')}

## Dependencies
{chr(10).join(f"- {d}" for d in item.get('dependencies', [])) if item.get('dependencies') else 'None'}
"""
                    spec_file.write_text(spec_content)
                    print(f"  📄 Created spec file: {spec_file}")

                    # Attach spec file using REST API
                    try:
                        attach_result = azure_cli.attach_file_to_work_item(
                            work_item_id=work_item_id,
                            file_path=spec_file,
                            comment=f"Technical specification for WI-{work_item_id}"
                        )

                        if attach_result and attach_result.get("success"):
                            print(f"  ✓ Attached spec file to WI-{work_item_id}")
                        else:
                            print(f"  ⚠️  Failed to attach spec file to WI-{work_item_id}")
                            items_missing_attachments.append(work_item_id)
                    except Exception as e:
                        print(f"  ⚠️  Attachment failed for WI-{work_item_id}: {e}")
                        items_missing_attachments.append(work_item_id)

        except Exception as e:
            print(f"✗ Failed to create: {item['title']}: {e}")
            failed_items.append(item)
            state.record_error(str(e), {"item": item})

    print(f"\n📊 Work Item Creation Summary:")
    print(f"  ✓ Created: {len(created_work_items)}")
    print(f"  ❌ Failed: {len(failed_items)}")
    if items_missing_attachments:
        print(f"  ⚠️  Missing attachments: {len(items_missing_attachments)}")
        print(f"     Work items: {', '.join(f'WI-{id}' for id in items_missing_attachments)}")

    state.complete_step("activation", result={
        "created": created_work_items,
        "failed": failed_items,
        "missing_attachments": items_missing_attachments,
        "total": len(work_items)
    })
```

### Step 9: Workflow Completion

```python
# Complete workflow
state.complete_workflow()

# Save profiling report
profiler.save_report()

# Display summary
print("\n" + "=" * 80)
print("✅ SPRINT PLANNING COMPLETE")
print("=" * 80)
state.print_summary()
profiler.print_summary()

print(f"\nCreated {len(created_work_items)} work items for Sprint {sprint_number}")
print(f"Total story points: {total_planned_points}")
print(f"Team capacity: {team_capacity}")
print(f"Capacity utilization: {(total_planned_points/team_capacity)*100:.1f}%")

if failed_items:
    print(f"\n⚠️  {len(failed_items)} items failed to create")
```

## Configuration

This workflow uses the following configuration:

- **Work Tracking**: azure-devops
- **Organization**: https://dev.azure.com/keychainio/
- **Project**: Trusted AI Development Workbench
- **Enabled Agents**: business-analyst, code-reviewer, devops-engineer, documentation-specialist, performance-engineer, project-architect, qa-engineer, release-manager, scrum-master, security-specialist, senior-engineer, technical-writer, ux-designer
- **State Directory**: .claude/workflow-state
- **Profiling Directory**: .claude/profiling
- **Verification**: Enabled

## Success Criteria

- All enabled agents complete successfully
- Work items created with comprehensive descriptions (500+ chars)
- Human approval obtained
- Sprint capacity not exceeded
- All work items verified in azure-devops