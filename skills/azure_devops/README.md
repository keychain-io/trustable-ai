# azure_devops

## Purpose

Azure DevOps skill for Trustable AI. Provides battle-tested Azure DevOps operations via CLI wrapper, including work item management, sprint operations, PR creation, and pipeline triggers with verification support.

## Key Components

- **__init__.py**: `AzureDevOpsSkill` class - main skill implementation with verification patterns
- **cli_wrapper.py**: `AzureCLI` class - low-level wrapper around Azure CLI commands

## Features

- **Work Item Operations**: Create, update, query, and link work items
- **Sprint Management**: Manage iterations and sprint assignments
- **Pull Requests**: Create and manage PRs with reviewers
- **Pipeline Triggers**: Trigger and monitor CI/CD pipelines
- **Verification**: Built-in verification patterns for all operations

## Usage

```python
from skills.azure_devops import AzureDevOpsSkill

skill = AzureDevOpsSkill()
if skill.initialize():
    # Create a work item
    result = skill.create_work_item(
        work_item_type="Task",
        title="Implement feature X",
        description="Details here"
    )
```

## Prerequisites

- Azure CLI installed and configured (`az login`)
- Azure DevOps extension (`az extension add --name azure-devops`)
- Appropriate permissions in the Azure DevOps project

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
   - Retrieved via: `az boards iteration team list`

**CRITICAL**: When assigning work items to sprints, always use the **team iteration path** format, not the project iteration path format. Work items assigned to project iteration paths will not appear in sprint taskboards.

**Example:**
```bash
# ✅ CORRECT - Use team iteration path
az boards work-item update \
  --id 1004 \
  --iteration "Project Name\\Sprint 1" \
  --org "https://dev.azure.com/org/"

# ❌ INCORRECT - Project iteration path won't show in taskboard
az boards work-item update \
  --id 1004 \
  --iteration "Project Name\\Iteration\\Sprint 1" \
  --org "https://dev.azure.com/org/"
```

**How to find the correct team iteration path:**
```bash
# List team iterations to see the correct path format
az boards iteration team list \
  --team "Team Name" \
  --org "https://dev.azure.com/org/" \
  --project "Project Name" \
  -o table
```
