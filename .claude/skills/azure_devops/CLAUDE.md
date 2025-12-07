---
context:
  purpose: "Battle-tested Azure DevOps operations with verification, preventing work item operation errors"
  problem_solved: "Raw Azure CLI commands are error-prone - wrong parameters, auth failures, malformed responses. This skill wraps Azure CLI with proper error handling, field mapping, and verification patterns."
  keywords: [azure-devops, skill, work-items, verification, ado]
  task_types: [implementation, integration, work-tracking]
  priority: medium
  max_tokens: 600
  children: []
  dependencies: [core, adapters/azure_devops]
---
# Azure DevOps Skill

## Purpose

Solves **Azure CLI operation errors** and **missing verification** by providing battle-tested Azure DevOps operations with built-in error handling and verification.

Raw Azure CLI commands fail silently or cryptically:
- Wrong field names → data loss (field ignored)
- Authentication expired → operation fails, unclear why
- Malformed WIQL → cryptic parse errors
- No verification → claim success but operation failed

This skill wraps Azure CLI with **validation, error handling, field mapping, and verification**, making Azure DevOps operations reliable.

## Features

- **Work Item CRUD**: Create, read, update, delete with verification
- **Sprint Operations**: List sprints, assign work items (correct iteration path format)
- **Queries**: WIQL queries with result parsing
- **Field Mapping**: Generic fields → Azure DevOps-specific fields
- **Verification**: All operations verify results against external source of truth

## Usage

```python
from skills.azure_devops import AzureDevOpsSkill

skill = AzureDevOpsSkill()

# Create and verify
result = skill.create_work_item(title="Task", type="Task")
if result.success:
    work_item = skill.get_work_item(result.id)
    assert work_item.exists  # Verification passed
```

## Related

- **adapters/azure_devops/CLAUDE.md**: Low-level Azure DevOps adapter
- **workflows/CLAUDE.md**: Workflows using this skill
- **skills/azure_devops/README.md**: Iteration path guidance
