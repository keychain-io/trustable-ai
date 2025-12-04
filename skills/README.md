# skills

## Purpose

Reusable skill system for TAID. Skills are modular capabilities that can be used across workflows and agents, providing specialized functionality like Azure DevOps integration, context generation, workflow coordination, and learning capture.

## Key Components

- **base.py**: `BaseSkill` and `VerifiableSkill` abstract base classes
- **registry.py**: `SkillRegistry` for skill discovery, loading, and management
- **azure_devops/**: Azure DevOps platform integration skill
- **context/**: Context generation and management skills
- **coordination/**: Workflow coordination and orchestration skills
- **learnings/**: Learning capture and retrieval skills
- **workflow/**: Workflow execution and state management skills
- **__init__.py**: Module exports (get_skill, list_skills, get_registry)

## Architecture

The skill system provides a plugin-like architecture for reusable capabilities:

### BaseSkill Class

All skills inherit from `BaseSkill`:
```python
class BaseSkill(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Return skill name."""

    @property
    @abstractmethod
    def description(self) -> str:
        """Return skill description."""

    def initialize(self) -> bool:
        """Initialize skill (check prerequisites, load config)."""

    def verify_prerequisites(self) -> Dict[str, Any]:
        """Check if prerequisites are met."""

    def get_documentation(self) -> Optional[str]:
        """Load skill documentation (SKILL.md)."""
```

### VerifiableSkill Class

For skills that support operation verification:
```python
class VerifiableSkill(BaseSkill):
    def _verify_operation(
        self,
        operation: str,
        success: bool,
        result: Any,
        verification_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create standardized verification result."""
```

### SkillRegistry

Manages skill discovery and loading:
```python
registry = SkillRegistry()
registry.discover_skills()              # Discover available skills
registry.register_skill(name, class)    # Register skill class
skill = registry.get_skill(name)        # Get skill instance
skills = registry.list_skills()         # List all skills
info = registry.get_skill_info(name)    # Get skill metadata
```

## Available Skills

### azure_devops/
Azure DevOps platform integration:
- Work item CRUD operations
- Query work items with WIQL
- Create/manage sprints
- Batch operations
- File attachments

### context/
Context generation and management:
- Load hierarchical CLAUDE.md files
- Task-based context selection
- Token budget management
- Context pruning and optimization

### coordination/
Workflow coordination:
- Multi-agent orchestration
- Task delegation
- Dependency resolution
- Parallel execution

### learnings/
Learning capture and retrieval:
- Capture lessons learned
- Categorize learnings
- Search and retrieve learnings
- Export learning reports

### workflow/
Workflow execution support:
- State management helpers
- Profiling utilities
- Resume interrupted workflows
- Workflow templates

## Usage Examples

```python
from skills import get_skill, list_skills

# List available skills
skills = list_skills()
print(f"Available skills: {skills}")

# Get and initialize a skill
azure_skill = get_skill("azure_devops")
if azure_skill.initialize():
    print(f"Loaded: {azure_skill.name}")
    print(f"Description: {azure_skill.description}")

# Check prerequisites
prereqs = azure_skill.verify_prerequisites()
if not prereqs["satisfied"]:
    print(f"Missing: {prereqs['missing']}")

# Get documentation
docs = azure_skill.get_documentation()
if docs:
    print(docs)
```

## Creating New Skills

To create a new skill:

1. **Create Skill Directory**: Add directory under `skills/`
2. **Implement Skill Class**: Inherit from `BaseSkill` or `VerifiableSkill`
3. **Add Documentation**: Create `SKILL.md` with usage instructions
4. **Register Skill**: Implement `get_skill()` function or `Skill` class
5. **Test**: Write tests for skill functionality

Example skill implementation:
```python
# skills/my_skill/__init__.py
from skills.base import BaseSkill

class MySkill(BaseSkill):
    @property
    def name(self) -> str:
        return "my-skill"

    @property
    def description(self) -> str:
        return "Description of what this skill does"

    def initialize(self) -> bool:
        # Initialize skill
        self._initialized = True
        return True

    def do_something(self, param: str) -> Dict[str, Any]:
        # Implement skill functionality
        return {"result": f"Processed: {param}"}

def get_skill(config=None):
    return MySkill(config)
```

## Skill Documentation

Each skill should have a `SKILL.md` file:
```markdown
# Skill Name

## Purpose
What this skill does.

## Prerequisites
- Required tools/libraries
- Configuration requirements
- Credentials needed

## Usage
Example code showing how to use the skill.

## API Reference
Methods and their signatures.

## Examples
Common use cases.
```

## Skill Configuration

Skills receive optional configuration on initialization:
```python
skill = get_skill("azure_devops", config={
    "organization": "https://dev.azure.com/myorg",
    "project": "MyProject"
})
```

Configuration can come from:
- `.claude/config.yaml` (framework configuration)
- Direct parameters to `get_skill()`
- Environment variables
- Skill-specific config files

## Verification Pattern

Skills that modify external systems should implement verification:
```python
class MySkill(VerifiableSkill):
    def create_item(self, data, verify=False):
        # Create item
        result = self._create(data)

        # Verify if requested
        if verify:
            return self._verify_operation(
                operation="create_item",
                success=True,
                result=result,
                verification_data={"id": result["id"], "exists": True}
            )

        return result
```

## Conventions

- **Skill Names**: Use kebab-case (azure-devops, context-generation)
- **Directory Structure**: Each skill in its own directory with `__init__.py`
- **Documentation**: Always include `SKILL.md` in skill directory
- **Error Handling**: Handle errors gracefully, provide helpful messages
- **Initialization**: Check prerequisites in `initialize()`
- **Stateless**: Skills should be stateless when possible
- **Configuration**: Support optional configuration on initialization

## Integration with Workflows

Skills are invoked by workflows and agents:
```python
# In a workflow
from skills import get_skill

# Get Azure DevOps skill
azure = get_skill("azure_devops")

# Create work items
work_items = azure.create_sprint_work_items(
    sprint_name="Sprint 10",
    work_items=[
        {"type": "Task", "title": "Feature X", "description": "..."}
    ]
)
```

## Testing

```bash
pytest tests/unit/test_skills.py  # Test skill loading and registry
pytest tests/integration/  # Test skill functionality
```

## Skill CLI

Manage skills via CLI:
```bash
trustable-ai skill list        # List available skills
trustable-ai skill info <name> # Show skill information
```
