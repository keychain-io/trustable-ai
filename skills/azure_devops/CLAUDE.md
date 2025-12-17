---
context:
  purpose: "Battle-tested Azure DevOps REST API operations with markdown support and verification, preventing work item operation errors"
  problem_solved: "Direct REST API v7.1 operations with markdown format support, PAT token authentication, proper error handling, field mapping, and verification patterns for reliable Azure DevOps work item management."
  keywords: [azure-devops, skill, work-items, verification, ado, rest-api]
  task_types: [implementation, integration, work-tracking]
  priority: medium
  max_tokens: 600
  children: []
  dependencies: [core, adapters/azure_devops]
---
# Azure DevOps Skill

## Purpose

Solves **markdown format support**, **reliable authentication**, and **missing verification** by providing battle-tested Azure DevOps REST API v7.1 operations with built-in error handling and verification.

This skill provides:
- **REST API v7.1 Direct Access**: No CLI overhead, direct HTTP requests
- **Markdown Format Support**: Automatic markdown formatting for description fields
- **PAT Token Authentication**: Secure, programmatic authentication
- **Field Validation**: Proper field names and mappings
- **Error Handling**: Clear error messages and retry logic
- **External Verification**: All operations verify against Azure DevOps source of truth

This skill uses **Azure DevOps REST API v7.1** with **automatic markdown formatting, PAT token authentication, field mapping, and verification**, making Azure DevOps operations reliable and properly formatted.

## Features

- **Markdown Format Support**: Automatically sets markdown format for description fields (System.Description, Microsoft.VSTS.Common.AcceptanceCriteria, Microsoft.VSTS.TCM.ReproSteps)
- **Work Item CRUD**: Create, read, update, delete with verification via REST API
- **Single-Step Creation**: Sets all fields including iteration in one request (no two-step pattern)
- **Sprint Operations**: List sprints, assign work items (correct iteration path format)
- **Queries**: WIQL queries with batch fetching for large result sets
- **Field Mapping**: Generic fields → Azure DevOps-specific fields
- **Verification**: All operations verify results against external source of truth
- **REST API v7.1**: Uses Azure DevOps REST API for full feature support

## Usage

### Recommended: Use Work Tracking Adapter (Preferred)

**⚠️ IMPORTANT: For workflows, use the unified work tracking adapter instead of this skill directly.**

```python
# ✅ PREFERRED: Use unified adapter (works across all platforms)
import sys
sys.path.insert(0, '.claude/skills')
from work_tracking import get_adapter

adapter = get_adapter()  # Auto-selects Azure DevOps or file-based
items = adapter.query_sprint_work_items("Sprint 6")
```

### Alternative: Direct Skill Usage (For Azure DevOps-specific operations)

```python
# ⚠️ ONLY for Azure DevOps-specific operations
from skills.azure_devops import AzureDevOpsSkill

skill = AzureDevOpsSkill()

# Create and verify
result = skill.create_work_item(title="Task", type="Task")
if result.success:
    work_item = skill.get_work_item(result.id)
    assert work_item.exists  # Verification passed
```

## REST API Authentication

This skill uses **Personal Access Token (PAT)** authentication via Azure DevOps REST API v7.1:

```python
# Authentication handled automatically by the skill
# PAT token retrieved from environment or Azure CLI credential cache
skill = AzureDevOpsSkill()
# Skill authenticates using PAT token in HTTP Authorization header
```

**PAT Token Benefits:**
- Programmatic access without interactive login
- Scoped permissions (work items, repos, pipelines)
- Revocable and rotatable for security
- Works in CI/CD and automation scenarios
- No subprocess overhead

## Why REST API Instead of CLI

**Direct REST API v7.1 provides:**
- **Markdown Support**: Native HTML format parameter for work item fields
- **Performance**: Direct HTTP requests vs subprocess overhead
- **Reliability**: Structured JSON responses vs CLI output parsing
- **Testing**: Mockable HTTP requests vs subprocess mocking
- **Platform Agnostic**: Adapter pattern works with multiple platforms
- **Error Handling**: HTTP status codes and structured error responses

**Deprecated CLI approach had limitations:**
- No markdown format support → descriptions rendered as code blocks
- Subprocess overhead → slower execution
- Platform lock-in → couldn't switch to Jira/GitHub
- Output parsing complexity → brittle error handling
- Not testable/mockable → harder to unit test

## Related

- **adapters/azure_devops/CLAUDE.md**: Low-level Azure DevOps adapter
- **workflows/CLAUDE.md**: Workflows using this skill
- **skills/azure_devops/README.md**: Iteration path guidance
