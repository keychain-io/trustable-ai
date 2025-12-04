# config

## Purpose

Configuration management system for TAID. Provides type-safe configuration schema using Pydantic and YAML-based configuration loading with environment variable expansion.

## Key Components

- **schema.py**: Pydantic models defining the complete configuration structure
- **loader.py**: `ConfigLoader` class for loading and validating YAML configuration
- **defaults/**: Default configuration templates for different project types
- **__init__.py**: Module exports (load_config, create_default_config, save_config)

## Architecture

### Configuration Schema (schema.py)

Pydantic models provide type-safe configuration with validation:

**FrameworkConfig** (root):
- `project`: ProjectConfig - Project metadata and tech stack
- `work_tracking`: WorkTrackingConfig - Work tracking platform settings
- `quality_standards`: QualityStandards - Quality thresholds and limits
- `agent_config`: AgentConfig - Agent models and enabled agents
- `workflow_config`: WorkflowConfig - State management and profiling
- `deployment_config`: DeploymentConfig - Deployment environments and tasks
- `custom`: Dict - Custom configuration values

**Key Models**:
- **ProjectConfig**: name, type, tech_stack, source_directory, test_directory
- **WorkTrackingConfig**: platform, organization, project, work_item_types, custom_fields, iteration_format
- **QualityStandards**: test_coverage_min, critical_vulnerabilities_max, code_complexity_max, etc.
- **AgentConfig**: models (map agent types to Claude models), enabled_agents list
- **WorkflowConfig**: state_directory, profiling_directory, checkpoint_enabled, max_retries
- **DeploymentConfig**: environments, default_environment, deployment_tasks_enabled

### Configuration Loader (loader.py)

**ConfigLoader** class:
- Loads YAML from `.claude/config.yaml`
- Expands environment variables (${VAR_NAME} or ${VAR_NAME:-default})
- Validates against Pydantic schema
- Provides save() method for persisting changes

### Environment Variable Expansion

Supports two formats:
- `${VAR_NAME}`: Use environment variable value
- `${VAR_NAME:-default}`: Use environment variable or default value

Example:
```yaml
work_tracking:
  organization: ${AZURE_ORG:-https://dev.azure.com/myorg}
  project: ${AZURE_PROJECT:-MyProject}
```

## Usage Examples

```python
from config import load_config, save_config, create_default_config

# Load existing configuration
config = load_config()  # Loads from .claude/config.yaml
print(config.project.name)
print(config.work_tracking.platform)

# Create default configuration
config = create_default_config(
    project_name="my-project",
    project_type="web-application",
    tech_stack={"languages": ["Python"], "frameworks": ["FastAPI"]},
    work_tracking_platform="azure-devops",
    organization="https://dev.azure.com/myorg",
    project="MyProject"
)

# Save configuration
save_config(config)  # Saves to .claude/config.yaml

# Access nested configuration
iteration_path = config.get_iteration_path("Sprint 10")
sprint_name = config.get_sprint_name(10)
is_enabled = config.is_agent_enabled("business-analyst")
model = config.get_agent_model("architect")  # Returns claude-opus-4
```

## Configuration File Structure

`.claude/config.yaml` structure:
```yaml
project:
  name: "project-name"
  type: "web-application"
  tech_stack:
    languages: ["Python", "TypeScript"]
    frameworks: ["FastAPI", "React"]
    platforms: ["Azure"]
    databases: ["PostgreSQL"]

work_tracking:
  platform: "azure-devops"
  organization: "https://dev.azure.com/org"
  project: "Project Name"
  credentials_source: "cli"
  work_item_types:
    epic: "Epic"
    feature: "Feature"
    task: "Task"
    bug: "Bug"
  custom_fields:
    business_value: "Custom.BusinessValue"

quality_standards:
  test_coverage_min: 80
  critical_vulnerabilities_max: 0
  code_complexity_max: 10

agent_config:
  models:
    architect: "claude-opus-4"
    engineer: "claude-sonnet-4.5"
  enabled_agents:
    - business-analyst
    - project-architect

workflow_config:
  checkpoint_enabled: true
  verification_enabled: true
```

## Validation

Pydantic provides automatic validation:
- **Type Checking**: Ensures values match declared types
- **Constraints**: Enforces min/max values, valid enums
- **Required Fields**: Raises error if required fields missing
- **Custom Validators**: field_validator for complex validation

Example validators:
- `project.type` must be one of: web-application, api, library, etc.
- `work_tracking.platform` must be: azure-devops, jira, github-projects, file-based
- `quality_standards.test_coverage_min` must be 0-100

## Conventions

- **File Location**: Always `.claude/config.yaml` in project root
- **Indentation**: Use 2 spaces for YAML
- **Comments**: Document non-obvious configuration values
- **Secrets**: Never commit secrets, use environment variables
- **Defaults**: Provide sensible defaults in schema

## Testing

```bash
pytest tests/unit/test_configuration.py  # Test config loading and validation
```
