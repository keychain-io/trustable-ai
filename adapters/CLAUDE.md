---
context:
  purpose: "Solves work tracking platform lock-in through pluggable adapters for external source of truth"
  problem_solved: "AI agents claim work items are created when they're not. Without external verification against a real work tracking system, AI assertions are untrustworthy. Platform-specific implementations would lock projects into a single tool."
  keywords: [adapters, work-tracking, azure-devops, jira, github, verification, external-truth]
  task_types: [implementation, integration, adapter-development]
  priority: high
  max_tokens: 800
  children:
    - path: adapters/azure_devops/CLAUDE.md
      when: [azure-devops, azure, work-items]
    - path: adapters/file_based/CLAUDE.md
      when: [file-based, local, testing]
  dependencies: [config]
---
# Adapters

## Purpose

Solves **unverified work completion** (#1) from VISION.md by implementing **External Source of Truth** verification.

AI agents routinely claim tasks are complete when they're not:
- "I created 10 work items for the sprint" → Work items don't exist in Azure DevOps
- "Feature is marked as Done" → Still shows "In Progress" in tracking system
- "All bugs are closed" → Bug tracker shows 5 open critical issues

The adapter system provides **pluggable integrations** with work tracking platforms (Azure DevOps, Jira, GitHub Issues, file-based) that serve as the **external source of truth**. Workflows verify AI claims by querying these systems, catching false completion reports immediately.

## Key Adapters

### azure_devops/
**Problem Solved**: Azure DevOps-specific work item creation, queries, and verification

Implements full Azure DevOps API integration using Azure CLI credentials. Supports:
- Work item creation (Epic, Feature, Task, Bug with proper types)
- Query execution (WIQL for complex filtering)
- Sprint/iteration management
- Field mapping (generic → Azure DevOps custom fields)
- Verification queries (confirm work items exist after creation)

**Real Failure Prevented**: Workflow claims "created WI-1001 Feature". Verification query to Azure DevOps API returns 404. Workflow halts immediately with error: "Claimed work item doesn't exist". Without adapter verification: discover missing work items 3 days later at sprint review.

### file_based/ (planned)
**Problem Solved**: Zero-dependency local work tracking for testing and offline development

Uses YAML files in `.claude/work-items/` to simulate work tracking system. Enables:
- Workflow testing without Azure DevOps credentials
- Offline development and demos
- CI/CD pipeline testing
- Quick prototyping

**When to Use**: Development mode, testing, demos, projects without work tracking platform.

## Adapter Pattern

All adapters implement a common interface:

```python
class WorkTrackingAdapter:
    """Base interface for all work tracking platform adapters."""

    def create_work_item(self, item_type, title, description, **fields):
        """Create a work item and return its ID."""
        raise NotImplementedError

    def get_work_item(self, item_id):
        """Retrieve work item by ID."""
        raise NotImplementedError

    def update_work_item(self, item_id, **fields):
        """Update work item fields."""
        raise NotImplementedError

    def query_work_items(self, query):
        """Execute platform-specific query."""
        raise NotImplementedError

    def verify_work_item_exists(self, item_id):
        """Verify work item exists (external source of truth check)."""
        work_item = self.get_work_item(item_id)
        return work_item is not None
```

Workflows use adapters generically:

```python
# Load adapter from config (Azure DevOps, Jira, file-based, etc.)
adapter = get_adapter()

# Create work item
item_id = adapter.create_work_item(
    item_type="Feature",
    title="Add authentication",
    description="Implement OAuth2 authentication"
)

# CRITICAL: Verify work item exists (external truth check)
if not adapter.verify_work_item_exists(item_id):
    raise VerificationError(f"AI claimed work item {item_id} created but doesn't exist")

# Work item verified - safe to continue
```

## Field Mapping

Adapters map generic field names to platform-specific fields:

**Generic Field → Platform Field**
- `item_type` → Azure: `System.WorkItemType`, Jira: `issuetype`
- `title` → Azure: `System.Title`, Jira: `summary`
- `description` → Azure: `System.Description`, Jira: `description`
- `state` → Azure: `System.State`, Jira: `status`
- `assigned_to` → Azure: `System.AssignedTo`, Jira: `assignee`
- `story_points` → Azure: `Microsoft.VSTS.Scheduling.StoryPoints`, Jira: `customfield_10016`

Configuration in `.claude/config.yaml`:

```yaml
work_tracking:
  platform: "azure-devops"  # or "jira", "github", "file-based"

  # Custom field mappings
  custom_fields:
    business_value: "Custom.BusinessValueScore"
    technical_risk: "Custom.TechnicalRisk"
    acceptance_criteria: "Microsoft.VSTS.Common.AcceptanceCriteria"
```

## Verification Pattern

Every workflow operation that creates or modifies work items follows this pattern:

1. **Execute Operation**: Call adapter to create/update work item
2. **Get Claimed Result**: Adapter returns work item ID or status
3. **Verify External Truth**: Query platform API to confirm
4. **Gate Progression**: Block if verification fails, continue if succeeds

**Example: Sprint Planning Work Item Creation**

```python
# Step 1: Execute - create work items via adapter
created_ids = []
for item in approved_sprint_items:
    result = adapter.create_work_item(
        item_type=item.type,
        title=item.title,
        description=item.description,
        story_points=item.story_points
    )
    created_ids.append(result.id)

# Step 2: Verify - query external system
verified_ids = []
for item_id in created_ids:
    work_item = adapter.get_work_item(item_id)

    if work_item is None:
        raise VerificationError(
            f"Work item {item_id} claimed created but doesn't exist in {adapter.platform}"
        )

    if work_item.state != "New":
        warnings.append(f"Expected state 'New' for {item_id}, got '{work_item.state}'")

    verified_ids.append(item_id)

# Step 3: Gate - only proceed if all verified
if len(verified_ids) != len(created_ids):
    raise VerificationError(
        f"Created {len(created_ids)} work items but only {len(verified_ids)} verified"
    )

print(f"✅ Verified {len(verified_ids)} work items in {adapter.platform}")
```

## Adding New Platform Adapters

To add support for a new platform (e.g., Jira, GitHub Issues):

1. **Create adapter directory**: `adapters/jira/`
2. **Implement adapter interface**: `adapters/jira/adapter.py`
3. **Implement field mappers**: `adapters/jira/field_mapper.py`
4. **Add to adapter registry**: `adapters/__init__.py`
5. **Add configuration schema**: `config/schema.py`
6. **Add tests**: `tests/integration/test_jira_adapter.py`

**Example: Jira Adapter Structure**

```
adapters/jira/
├── __init__.py
├── adapter.py          # JiraAdapter(WorkTrackingAdapter)
├── field_mapper.py     # Generic → Jira field mapping
├── auth.py             # Jira authentication (API token, OAuth)
└── CLAUDE.md           # Adapter-specific documentation
```

## Important Notes

- **Adapters are the source of truth**: Workflow verification always queries adapter, never trusts AI claims
- **Authentication is platform-specific**: Azure uses Azure CLI, Jira uses API tokens, GitHub uses PATs
- **Field mapping is configurable**: Projects can define custom field mappings in config.yaml
- **Verification is mandatory**: All work item creation/update must verify via external query
- **Error handling**: Failed verification halts workflow immediately (fail-fast principle)

## Real Failure Scenarios Prevented

### Scenario 1: AI Claims Work Items Created, They Don't Exist
**Without adapters**: "I created 10 work items for Sprint 1" → Sprint taskboard is empty → Discover issue 3 days into sprint

**With adapters**: After each create_work_item() call, adapter.verify_work_item_exists() queries Azure DevOps API. If item doesn't exist, workflow throws VerificationError immediately.

### Scenario 2: Work Item States Diverge from AI Claims
**Without adapters**: AI says "All features are Done". Reality: 3 features still "In Progress". Team discovers at sprint review.

**With adapters**: Daily standup workflow queries adapter.query_work_items(state='Done') and compares to AI assertions. Divergence detected immediately, surfaced in daily report.

### Scenario 3: Platform Lock-In
**Without adapters**: Workflow hardcoded for Azure DevOps. Company switches to Jira. Rewrite entire workflow layer.

**With adapters**: Change `.claude/config.yaml` from `platform: azure-devops` to `platform: jira`. Workflows use same adapter interface, no code changes needed.

## Related

- **VISION.md**: Pillar #2 (Verifiable Workflows - External Source of Truth)
- **workflows/CLAUDE.md**: Workflows that use adapters for verification
- **config/CLAUDE.md**: Work tracking configuration (platform, credentials, field mappings)
- **adapters/azure_devops/CLAUDE.md**: Azure DevOps adapter implementation
- **skills/work_tracking.py**: Skill that provides adapter access to workflows
