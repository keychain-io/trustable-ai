# azure_devops

## Purpose

Azure DevOps platform adapter for TAID. Provides a comprehensive wrapper around Azure CLI for work item management, sprint operations, and DevOps workflows. Includes battle-tested patterns, verification support, and idempotent operations.

## Key Components

- **cli_wrapper.py**: `AzureCLI` class wrapping Azure CLI commands with verification and error handling
- **field_mapper.py**: Maps generic field names to Azure DevOps-specific field names
- **type_mapper.py**: Maps generic work item types to Azure DevOps work item types
- **bulk_operations.py**: Efficient bulk work item creation and updates
- **__init__.py**: Module exports

## Architecture

The adapter provides a platform-agnostic interface for work item management:

### AzureCLI Class

Main wrapper for Azure DevOps operations:

**Work Item Operations**:
- `create_work_item()`: Create work item with two-step iteration assignment
- `update_work_item()`: Update work item fields
- `get_work_item()`: Retrieve work item by ID
- `query_work_items()`: Query using WIQL
- `add_comment()`: Add comment to work item
- `link_work_items()`: Link work items with relationships
- `attach_file_to_work_item()`: Attach files using REST API

**Sprint/Iteration Operations**:
- `create_iteration()`: Create new sprint/iteration
- `list_iterations()`: List all sprints
- `update_iteration()`: Update sprint dates
- `create_sprint_work_items_batch()`: Efficiently create multiple work items for a sprint
- `query_sprint_work_items()`: Query all work items in a sprint

**Pull Request Operations**:
- `create_pull_request()`: Create PR with work item linking
- `approve_pull_request()`: Approve PR

**Pipeline Operations**:
- `trigger_pipeline()`: Trigger pipeline run
- `get_pipeline_run()`: Get pipeline status

**Verification Operations**:
- `verify_work_item_created()`: Verify work item exists with expected title
- `verify_work_item_updated()`: Verify fields updated correctly
- `verify_attachment_exists()`: Check if file attached

**Idempotent Operations**:
- `create_work_item_idempotent()`: Create only if doesn't exist (checks by title in sprint)

## Key Learnings Implemented

Based on battle-tested Azure DevOps integration:

### 1. Two-Step Work Item Creation
**Learning**: The `--iteration` parameter in `az boards work-item create` is unreliable.

**Solution**: Create work item first, then update with iteration path:
```python
# Step 1: Create without iteration
result = create_work_item(type, title, description)

# Step 2: Update with iteration
update_work_item(work_item_id, fields={"System.IterationPath": iteration})
```

### 2. Iteration Path Formats
**Learning**: Different operations use different iteration path formats.

**Formats**:
- **Work Items**: `"ProjectName\\SprintName"` (simplified)
- **WIQL Queries**: `"ProjectName\\\\SprintName"` (double backslash for escaping)
- **Iteration Updates**: `"\\ProjectName\\Iteration\\SprintName"` (full path with leading backslash)

### 3. Case-Sensitive Field Names
**Learning**: Azure DevOps field names are case-sensitive.

**Examples**:
- `System.Title` (correct)
- `system.title` (incorrect)
- `Microsoft.VSTS.Scheduling.StoryPoints` (correct)

### 4. Project Names with Spaces
**Learning**: Project names with spaces must be quoted in CLI commands.

**Solution**: CLI wrapper handles quoting automatically.

### 5. File Attachments
**Learning**: Azure CLI doesn't support file attachments directly.

**Solution**: Use Azure DevOps REST API via `attach_file_to_work_item()`:
1. Upload file to attachments endpoint
2. Link attachment to work item via PATCH operation

## Usage Examples

### Basic Work Item Operations
```python
from adapters.azure_devops import create_work_item, update_work_item, query_work_items

# Create work item
work_item = create_work_item(
    work_item_type="Task",
    title="Implement feature X",
    description="Details...",
    iteration="MyProject\\Sprint 10",
    fields={"Microsoft.VSTS.Scheduling.StoryPoints": 5}
)
print(f"Created WI-{work_item['id']}")

# Update work item
update_work_item(
    work_item_id=123,
    state="Done",
    fields={"System.AssignedTo": "user@example.com"}
)

# Query work items
wiql = """
    SELECT [System.Id], [System.Title], [System.State]
    FROM WorkItems
    WHERE [System.IterationPath] = 'MyProject\\\\Sprint 10'
"""
results = query_work_items(wiql)
```

### Sprint Operations
```python
from adapters.azure_devops import create_sprint, create_sprint_work_items

# Create sprint
sprint = create_sprint(
    sprint_name="Sprint 10",
    start_date="2025-11-07",
    finish_date="2025-11-20"
)

# Create multiple work items for sprint
work_items = [
    {
        "type": "Task",
        "title": "Task 1",
        "description": "Details...",
        "fields": {"Microsoft.VSTS.Scheduling.StoryPoints": 3}
    },
    {
        "type": "Bug",
        "title": "Fix bug",
        "description": "Bug details...",
        "fields": {"Microsoft.VSTS.Scheduling.StoryPoints": 2}
    }
]
results = create_sprint_work_items("Sprint 10", work_items)
```

### Verification
```python
from adapters.azure_devops.cli_wrapper import AzureCLI

azure = AzureCLI()

# Create with verification
result = azure.create_work_item(
    work_item_type="Task",
    title="Feature X",
    iteration="MyProject\\Sprint 10",
    verify=True
)

if result["success"]:
    print(f"Verified: WI-{result['result']['id']}")
    print(f"Iteration: {result['verification']['iteration_verified']}")
else:
    print(f"Verification failed: {result['verification']}")

# Verify specific fields
verification = azure.verify_work_item_updated(
    work_item_id=123,
    expected_fields={
        "System.State": "Done",
        "System.IterationPath": "MyProject\\Sprint 10"
    }
)

if verification["success"]:
    print("All fields match!")
else:
    for field, data in verification["verification"]["fields_verified"].items():
        if not data["matches"]:
            print(f"{field}: expected {data['expected']}, got {data['actual']}")
```

### Idempotent Operations
```python
from adapters.azure_devops.cli_wrapper import AzureCLI

azure = AzureCLI()

# Create only if doesn't exist
result = azure.create_work_item_idempotent(
    title="Feature X",
    work_item_type="Task",
    description="Details...",
    sprint_name="Sprint 10"
)

if result["created"]:
    print(f"Created new work item: WI-{result['id']}")
else:
    print(f"Work item already exists: WI-{result['id']}")
```

### File Attachments
```python
from pathlib import Path
from adapters.azure_devops.cli_wrapper import AzureCLI

azure = AzureCLI()

# Attach file to work item
result = azure.attach_file_to_work_item(
    work_item_id=123,
    file_path=Path("docs/spec.md"),
    comment="Technical specification"
)

if result["success"]:
    print(f"Attached {result['file_name']} to WI-{result['work_item_id']}")
```

## Field Mapping

Generic field names map to Azure DevOps fields:
- `title` → `System.Title`
- `description` → `System.Description`
- `state` → `System.State`
- `assigned_to` → `System.AssignedTo`
- `iteration_path` → `System.IterationPath`
- `area_path` → `System.AreaPath`
- `story_points` → `Microsoft.VSTS.Scheduling.StoryPoints`

Custom fields defined in `.claude/config.yaml`:
```yaml
work_tracking:
  custom_fields:
    business_value: "Custom.BusinessValue"
    technical_risk: "Custom.TechnicalRisk"
```

## Type Mapping

Generic work item types map to Azure DevOps types:
- `epic` → `Epic`
- `feature` → `Feature`
- `story` → `User Story`
- `task` → `Task`
- `bug` → `Bug`

## Conventions

- **Iteration Paths**: Use simplified format in create/update (`ProjectName\\SprintName`)
- **WIQL Queries**: Use double backslash for escaping (`ProjectName\\\\SprintName`)
- **Field Names**: Always use exact case (`System.Title`, not `system.title`)
- **Verification**: Use `verify=True` for critical operations
- **Idempotency**: Use `create_work_item_idempotent()` to avoid duplicates
- **Error Handling**: All methods raise exceptions with helpful error messages

## Authentication

Uses Azure CLI credentials:
```bash
# Login to Azure
az login

# Configure Azure DevOps
az devops configure --defaults organization=https://dev.azure.com/myorg project=MyProject
```

Or set environment variable:
```bash
export AZURE_DEVOPS_EXT_PAT=your_personal_access_token
```

## Testing

```bash
pytest tests/unit/test_mappers.py  # Test field/type mapping
pytest tests/integration/  # Test Azure DevOps operations (requires credentials)
```
