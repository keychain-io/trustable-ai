---
context:
  purpose: "Reusable operation bundles that prevent workflow code duplication and operation errors"
  problem_solved: "Workflows that reimplement common operations (work item creation, file operations, API calls) introduce bugs through inconsistent error handling, missing validation, and copy-paste mistakes. Skills provide battle-tested, reusable operations."
  keywords: [skills, reusable, operations, azure-devops, utilities]
  task_types: [implementation, integration]
  priority: medium
  max_tokens: 600
  children:
    - path: skills/azure_devops/CLAUDE.md
      when: [azure-devops, work-tracking]
  dependencies: [core]
---
# Skills

## Purpose

Solves **workflow code duplication** and **inconsistent operation implementation** by providing battle-tested, reusable operation bundles.

Without skills:
- Workflows reimplement work item creation → inconsistent error handling
- Same operations coded differently in each workflow → bugs from variations
- No verification patterns → workflows trust operations succeeded
- Copy-paste code → bug fixes don't propagate

Skills provide **one correct implementation** of common operations that all workflows can reuse with confidence.

## Available Skills

- **azure_devops**: Azure DevOps operations (work items, sprints, queries) with verification
- More skills can be added for other platforms and operations

## Usage Pattern

```python
from skills.azure_devops import AzureDevOpsSkill

skill = AzureDevOpsSkill()
result = skill.create_work_item(title="Task", type="Task")
# Skill handles: validation, error handling, verification, logging
```

Skills return structured results with success/failure indicators, making workflow verification straightforward.

## Related

- **workflows/CLAUDE.md**: Workflows that use skills
- **adapters/CLAUDE.md**: Platform adapters that skills wrap
