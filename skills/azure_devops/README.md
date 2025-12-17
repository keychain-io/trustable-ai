# azure_devops

## Purpose

Azure DevOps skill for Trustable AI. Provides battle-tested Azure DevOps operations via REST API v7.1, including work item management, sprint operations, PR creation, and pipeline triggers with verification support.

## Key Components

- **__init__.py**: `AzureDevOpsSkill` class - main skill implementation with verification patterns
- **cli_wrapper.py**: REST API wrapper for Azure DevOps operations (uses HTTP requests, not CLI)

## Features

- **Work Item Operations**: Create, update, query, and link work items via REST API
- **Markdown Format Support**: Automatic markdown formatting for description fields
- **Sprint Management**: Manage iterations and sprint assignments
- **Pull Requests**: Create and manage PRs with reviewers
- **Pipeline Triggers**: Trigger and monitor CI/CD pipelines
- **Verification**: Built-in verification patterns for all operations
- **PAT Token Authentication**: Secure, programmatic authentication

## Usage

```python
from skills.azure_devops import AzureDevOpsSkill

skill = AzureDevOpsSkill()
if skill.initialize():
    # Create a work item with markdown description
    result = skill.create_work_item(
        work_item_type="Task",
        title="Implement feature X",
        description="# Details\n\nMarkdown formatted description"
    )
```

## Prerequisites

- Azure DevOps Personal Access Token (PAT) configured
- Appropriate permissions in the Azure DevOps project
- PAT token available via environment variable or credential cache

## Important Notes

### Sprint/Iteration Path Management

Azure DevOps has two types of iteration paths that serve different purposes:

1. **Project Iteration Paths** (classification nodes):
   - Format: `\Project Name\Iteration\Sprint 1`
   - These are the classification structure nodes visible in Project Settings
   - Used for organizing the iteration hierarchy
   - NOT used for work item assignment

2. **Team Iteration Paths** (for work items):
   - Format: `Project Name\Sprint 1`
   - These are the paths that work items must be assigned to
   - These are what appear in sprint taskboards and backlogs
   - Retrieved via REST API team iteration endpoints

**CRITICAL**: When assigning work items to sprints, always use the **team iteration path** format, not the project iteration path format. Work items assigned to project iteration paths will not appear in sprint taskboards.

**Example:**
```python
# ✅ CORRECT - Use team iteration path via skill
skill.update_work_item(
    work_item_id=1004,
    iteration_path="Project Name\\Sprint 1"
)

# ❌ INCORRECT - Project iteration path won't show in taskboard
skill.update_work_item(
    work_item_id=1004,
    iteration_path="Project Name\\Iteration\\Sprint 1"  # Wrong format
)
```

**How to find the correct team iteration path:**
```python
# List team iterations via skill to see the correct path format
iterations = skill.list_team_iterations(team_name="Team Name")
for iteration in iterations:
    print(f"Path: {iteration['path']}")
```
