---
context:
  purpose: "Provides external source of truth for work item verification, preventing AI from claiming work complete that doesn't exist"
  problem_solved: "AI agents routinely claim tasks complete when they're not - 'I created 10 work items' when none exist, 'Tests passing' when they weren't run. Without querying an external source of truth, there's no way to verify AI claims. This adapter makes Azure DevOps the authoritative system for work item state."
  keywords: [azure-devops, adapter, work-tracking, verification, source-of-truth, integration, ado]
  task_types: [integration, work-tracking, verification, implementation]
  priority: medium
  max_tokens: 600
  children: [cli_wrapper, field_mapper, type_mapper, bulk_operations]
  dependencies: [core, config]
---
# Azure DevOps Adapter

## Purpose

Solves **no external source of truth for work item verification** by making Azure DevOps the authoritative system for work item state (VISION.md Design Principle #2).

AI agents claim success while delivering nothing:
- "I created 10 work items for Sprint 1" → Query Azure DevOps → 0 work items exist
- "Task 1234 is complete" → Query Azure DevOps → Task 1234 still "To Do"
- "Sprint has 5 features" → Query Azure DevOps → Sprint has 2 features, 3 missing

**Without this adapter**, workflows have no way to verify AI claims. They'd have to trust AI assertions. That trust is misplaced - AI hallucinates completion routinely.

**With this adapter**, workflows query Azure DevOps directly. Work item 1234 either exists or it doesn't. Task state is "Done" or it isn't. External verification catches lies immediately.

## Key Components

### cli_wrapper.py
**Problem Solved**: Direct REST API calls need error handling, authentication, and markdown format support

Wraps Azure DevOps REST API v7.1 operations with proper error handling, PAT token authentication, markdown format support, and response parsing.

**Real Failure Prevented**: Workflow calls REST API to create work item but PAT token expired. API returns 401, workflow continues thinking item created. With cli_wrapper: authentication checked first via token validation, clear error if credentials invalid, workflow halts instead of proceeding with bad state.

### field_mapper.py
**Problem Solved**: Azure DevOps uses platform-specific field names that differ from generic framework fields

Maps generic framework fields (like `story_points`) to Azure DevOps-specific fields (like `Microsoft.VSTS.Scheduling.StoryPoints`).

**Real Failure Prevented**: Workflow tries to set `story_points: 5` on work item. Azure DevOps doesn't have `story_points` field, has `Microsoft.VSTS.Scheduling.StoryPoints`. Without mapper: field ignored silently, story points never set. With mapper: translates to correct field name, value set properly.

### type_mapper.py
**Problem Solved**: Azure DevOps work item types (Epic, Feature, Task) differ from generic types (epic, feature, story, task)

Maps framework work item types to Azure DevOps types based on project configuration.

**Real Failure Prevented**: Workflow tries to create "User Story" type work item. Azure DevOps project doesn't have "User Story" type (only has Task). Without mapper: creation fails with cryptic error "type doesn't exist". With mapper: consults config, maps "story" → "Task", creation succeeds.

### bulk_operations.py
**Problem Solved**: Creating many work items one-at-a-time is slow and prone to partial failures

Provides batch operations for creating/updating multiple work items efficiently, with rollback on failure.

**Real Failure Prevented**: Workflow creates 20 work items sequentially. Item #15 fails due to network error. Items 1-14 created, 15-20 missing. Partial state, hard to recover. With bulk operations: create all 20 in batch, if any fail, rollback all (or retry), maintain consistency.

## Verification Pattern

This adapter enables the core verification pattern:

```python
# Step 1: AI claims it did something
claimed_id = "1234"

# Step 2: Query external source of truth (Azure DevOps)
work_item = azure_devops.get_work_item(claimed_id)

# Step 3: Verify claim against reality
if not work_item.exists:
    raise VerificationError(f"AI claimed {claimed_id} created, but doesn't exist")

if work_item.state != expected_state:
    raise VerificationError(f"Expected state {expected_state}, got {work_item.state}")

# Step 4: Only proceed if verification passes
return work_item  # Verified to exist and be in correct state
```

**Why This Matters**: Without external verification, workflow trusts AI. AI says "task complete" → workflow marks complete → discover during sprint review that task was never done. With external verification: workflow queries Azure DevOps → sees task not in "Done" state → catches failure immediately.

## Supported Operations

### Work Item CRUD

**Create Work Item:**
```python
from adapters.azure_devops import AzureDevOpsAdapter

adapter = AzureDevOpsAdapter(config)

# Create work item
result = adapter.create_work_item(
    work_item_type="Task",
    title="Implement feature X",
    description="Details here",
    iteration_path="Project\\Sprint 1",
    story_points=5
)

# Verify creation
work_item = adapter.get_work_item(result.id)
assert work_item.exists, "Work item creation failed"
```

**Query Work Items:**
```python
# Query work items in sprint
items = adapter.query_work_items(
    wiql="SELECT [System.Id], [System.Title] FROM WorkItems WHERE [System.IterationPath] = 'Project\\Sprint 1'"
)

# Verify expected count
assert len(items) == expected_count, f"Expected {expected_count} items, found {len(items)}"
```

**Update Work Item:**
```python
# Update work item state
adapter.update_work_item(
    work_item_id=1234,
    state="Done",
    completed_work=8
)

# Verify update
work_item = adapter.get_work_item(1234)
assert work_item.state == "Done", "State update failed"
```

### Sprint Operations

**List Sprints:**
```python
# Get all sprints
sprints = adapter.list_iterations(team="Team Name")

# Verify sprint exists
sprint_1 = next((s for s in sprints if s.name == "Sprint 1"), None)
assert sprint_1 is not None, "Sprint 1 doesn't exist"
```

**Assign to Sprint:**
```python
# Assign work item to sprint (use TEAM iteration path, not project iteration path)
adapter.update_work_item(
    work_item_id=1234,
    iteration_path="Project\\Sprint 1"  # Team path, not "Project\\Iteration\\Sprint 1"
)

# Verify assignment
work_item = adapter.get_work_item(1234)
assert "Sprint 1" in work_item.iteration_path, "Sprint assignment failed"
```

## Field Mappings

Azure DevOps uses platform-specific field names. This adapter maps generic fields to Azure DevOps fields:

| Framework Field | Azure DevOps Field | Description |
|-----------------|-------------------|-------------|
| `story_points` | `Microsoft.VSTS.Scheduling.StoryPoints` | Story point estimate |
| `priority` | `Microsoft.VSTS.Common.Priority` | Priority (1-4) |
| `business_value` | `Microsoft.VSTS.Common.BusinessValue` | Business value score |
| `risk` | `Microsoft.VSTS.Common.Risk` | Risk level |
| `description` | `System.Description` | Work item description |
| `state` | `System.State` | Work item state |

**Custom Fields**: Configure custom field mappings in `.claude/config.yaml`:

```yaml
work_tracking:
  custom_fields:
    technical_risk: "Custom.TechnicalRiskScore"
    roi_estimate: "Custom.ROI"
```

## Authentication

This adapter uses Personal Access Token (PAT) authentication via Azure DevOps REST API v7.1:

```python
# PAT token retrieved from environment or Azure CLI credential cache
# Set via environment variable:
export AZURE_DEVOPS_EXT_PAT="your_pat_token_here"

# Or via Azure CLI credential cache (adapter auto-retrieves)
```

**Credential Source**: Configured in `.claude/config.yaml`:

```yaml
work_tracking:
  platform: "azure-devops"
  organization: "https://dev.azure.com/myorg"
  project: "My Project"
  credentials_source: "env:AZURE_DEVOPS_EXT_PAT"  # or "cli" for Azure CLI cache
```

**Verification**: Adapter checks authentication before operations:

```python
# Check auth status via REST API
if not adapter.is_authenticated():
    raise AuthenticationError("Azure DevOps PAT token not found or expired. Set AZURE_DEVOPS_EXT_PAT environment variable")
```

## Important Notes

- **This adapter is the source of truth**: Workflows query this adapter, not internal state, to verify claims
- **REST API v7.1**: Uses Azure DevOps REST API directly with HTTP requests (no CLI dependency)
- **Markdown format support**: Automatically sets HTML format for description fields
- **PAT token authentication**: Secure, programmatic authentication via Personal Access Tokens
- **Team iteration paths**: Work items must be assigned to team iteration paths (e.g., `Project\Sprint 1`), not project iteration paths (e.g., `Project\Iteration\Sprint 1`). See `skills/azure_devops/README.md` for details.
- **Field mappings configurable**: Custom fields can be mapped in config.yaml
- **Batch operations preferred**: Use bulk operations for creating/updating multiple items (faster, more reliable)
- **Error handling**: Adapter returns structured errors with HTTP status codes and JSON error details

## Real Failure Scenarios Prevented

### Scenario 1: AI Claims Work Items Created, They Don't Exist
**Without adapter**: Workflow says "✅ Created 10 work items". Sprint taskboard empty. Discover issue 3 days into sprint, scramble to create actual work items.

**With adapter**: After each claimed creation, adapter queries Azure DevOps. If work item doesn't exist, workflow halts with error: "Claimed work item 1234 created but Azure DevOps query returned not found". Fix immediately.

### Scenario 2: Wrong Iteration Path Format Breaks Taskboard
**Without adapter**: Work items assigned to `Project\Iteration\Sprint 1` (project iteration path). Items don't appear in taskboard. Mystery debugging for hours.

**With adapter**: Documentation clearly states team iteration path required. Adapter provides `list_iterations(team=...)` to get correct format. Work items show up in taskboard.

### Scenario 3: Custom Field Mapping Missing
**Without adapter**: Workflow sets `business_value: 85` on work item. Azure DevOps doesn't have `business_value` field, has `Custom.BusinessValueScore`. Field ignored, business value lost.

**With adapter**: field_mapper.py configured with mapping `business_value` → `Custom.BusinessValueScore`. Adapter translates field name, value set correctly in Azure DevOps.

## Related

- **VISION.md**: Design Principle #2 (External Source of Truth), Pillar #2 (Verifiable Workflows)
- **skills/azure_devops/README.md**: Platform-specific guidance (iteration paths, authentication)
- **config/CLAUDE.md**: WorkTrackingConfig for Azure DevOps settings
- **workflows/CLAUDE.md**: Workflows that use this adapter for verification
- **adapters/**: Adapter interface and base classes (for adding Jira, GitHub adapters)
