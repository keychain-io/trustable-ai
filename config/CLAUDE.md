---
context:
  purpose: "Solves AI misunderstanding human intent by capturing explicit project requirements, quality standards, and expectations"
  problem_solved: "AI agents make assumptions about what you want when requirements aren't explicit - guessing tech stack, quality thresholds, deployment targets, and development mode. Without explicit configuration, AI builds the wrong thing correctly instead of the right thing."
  keywords: [config, configuration, intent, quality, standards, pydantic, validation, yaml]
  task_types: [configuration, setup, initialization, validation]
  priority: medium
  max_tokens: 600
  children: [schema, loader]
  dependencies: []
---
# Configuration System

## Purpose

Solves **missing human intent** (#2) from VISION.md by implementing **Explicit Human Intent** (Pillar #1).

AI agents cannot read minds about what you actually want:
- Should this be a prototype or production-ready code?
- Fix every edge case or move fast?
- What's the tech stack? Python? TypeScript? Both?
- Quality thresholds: 80% test coverage or 95%?
- Deploy to AWS? Azure? Docker locally?

**Without explicit configuration**, AI makes assumptions. Those assumptions are often wrong. You get production-quality code when you needed a sketch, or throwaway code when you needed durability.

The configuration system captures human intent explicitly in `.claude/config.yaml` before any AI work begins. AI doesn't guess - it reads your requirements and builds accordingly.

## Key Components

### schema.py
**Problem Solved**: Invalid or incomplete configuration that breaks workflows

Defines Pydantic models for type-safe configuration validation. Catches missing required fields, invalid values, and incompatible combinations before workflows run.

**Real Failure Prevented**: User configures `test_coverage_min: "80"` (string instead of integer). Workflow tries to compare "80" > 75, crashes with type error. With schema validation: error caught at config load, clear message: "test_coverage_min must be integer, got string".

### loader.py
**Problem Solved**: Configuration scattered across multiple sources with unclear precedence

Loads and validates `.claude/config.yaml`, applies defaults for optional fields, provides single source of configuration truth.

**Real Failure Prevented**: Project has config in 3 places: .claude/config.yaml, environment variables, hardcoded defaults. Workflow uses wrong value (environment var overrides file). With loader: clear precedence order, single load function, predictable behavior.

## Configuration Models

### ProjectConfig
**What Intent It Captures**: What are you building and with what technologies?

```yaml
project:
  name: "trustable-ai"
  type: "cli-tool"  # or web-application, api, library
  tech_stack:
    languages: ["Python"]
    frameworks: ["pytest"]
    platforms: ["Docker"]
```

**Before/After Scenario**:
- **Without**: AI assumes Node.js project, generates package.json and Jest tests. Your project uses Python.
- **With**: AI reads Python in tech_stack, generates pytest tests and setup.py.

### QualityStandards
**What Intent It Captures**: What's acceptable quality for this project?

```yaml
quality_standards:
  test_coverage_min: 80        # Don't ship with <80% coverage
  critical_vulnerabilities_max: 0   # Zero critical vulns allowed
  code_complexity_max: 10      # Cyclomatic complexity threshold
```

**Before/After Scenario**:
- **Without**: AI implements feature with 40% test coverage. "Looks good!" Merge to main. Production breaks.
- **With**: AI checks quality_standards, sees 80% minimum, writes comprehensive tests. Coverage check passes.

### WorkTrackingConfig
**What Intent It Captures**: Where is the source of truth for work items?

```yaml
work_tracking:
  platform: "azure-devops"
  organization: "https://dev.azure.com/myorg"
  project: "My Project"
  work_item_types:
    epic: "Epic"
    feature: "Feature"
    task: "Task"
```

**Before/After Scenario**:
- **Without**: AI claims "created 10 work items" but has no integration. Work items don't exist. Discover 3 days later.
- **With**: AI uses work_tracking config to actually create items in Azure DevOps. Verification queries confirm existence.

### AgentConfig
**What Intent It Captures**: Which agents should run and with what models?

```yaml
agent_config:
  models:
    architect: "claude-opus-4"       # Complex reasoning
    engineer: "claude-sonnet-4.5"    # Balanced
  enabled_agents:
    - business-analyst
    - project-architect
    - senior-engineer
```

**Before/After Scenario**:
- **Without**: All agents use Sonnet. Architecture review misses complex system implications. Production bottleneck discovered.
- **With**: Architect uses Opus (better reasoning), catches scaling issue in planning. Fix before implementation.

## How Configuration Drives Behavior

### Example 1: Test Coverage Enforcement

**Config:**
```yaml
quality_standards:
  test_coverage_min: 80
```

**Agent Behavior:**
```python
# In senior-engineer agent
coverage_requirement = config.quality_standards.test_coverage_min

acceptance_criteria.append(
    f"Test coverage must be >= {coverage_requirement}%"
)

# In QA engineer agent
if measured_coverage < coverage_requirement:
    raise QualityGateFailure(
        f"Coverage {measured_coverage}% below minimum {coverage_requirement}%"
    )
```

### Example 2: Platform-Specific Deployment

**Config:**
```yaml
project:
  tech_stack:
    platforms: ["Azure", "Docker"]
```

**Agent Behavior:**
```python
# In devops-engineer agent
platforms = config.project.tech_stack.platforms

if "Azure" in platforms:
    deployment_steps.append("Create Azure App Service")
    deployment_steps.append("Configure Azure Key Vault")

if "Docker" in platforms:
    deployment_steps.append("Build Docker image")
    deployment_steps.append("Push to container registry")
```

### Example 3: Mode-Driven Development

**Config:**
```yaml
development:
  mode: "prototype"  # or "production"
```

**Agent Behavior:**
```python
# In senior-engineer agent
if config.development.mode == "prototype":
    # Fast iteration, skip edge cases
    story_points = base_estimate * 0.5  # Half the time
    acceptance_criteria = ["Happy path works"]

elif config.development.mode == "production":
    # Rigorous, handle all cases
    story_points = base_estimate * 1.5  # More thorough
    acceptance_criteria = [
        "Happy path works",
        "Error cases handled",
        "Edge cases covered",
        "Security review completed"
    ]
```

## Validation Rules

Schema validation enforces:

1. **Required Fields**: `project.name`, `project.type`, `work_tracking.platform`
2. **Valid Enums**: `project.type` must be one of: `web-application`, `api`, `library`, `cli-tool`, `mobile-app`
3. **Value Ranges**: `test_coverage_min` must be 0-100
4. **Dependency Checks**: If `work_tracking.platform == "azure-devops"`, then `organization` and `project` required
5. **Type Safety**: All fields have explicit types (int, str, list, etc.)

**Validation Example:**
```bash
$ trustable-ai validate

✅ Configuration valid
   - Project: trustable-ai (cli-tool)
   - Tech stack: Python, pytest, Docker
   - Work tracking: azure-devops
   - Quality: 80% coverage, 0 critical vulns
   - Agents: 7 enabled
```

## Usage

### Initialize Configuration

```bash
# Create default config
trustable-ai init

# Creates .claude/config.yaml with prompts for:
# - Project name and type
# - Tech stack
# - Work tracking platform
# - Quality standards
```

### Load Configuration in Code

```python
from config.loader import load_config

config = load_config(".claude/config.yaml")

# Access configuration
print(config.project.name)  # "trustable-ai"
print(config.quality_standards.test_coverage_min)  # 80
print(config.work_tracking.platform)  # "azure-devops"
```

### Validate Configuration

```bash
# Check configuration is valid
trustable-ai validate

# Returns exit code 0 if valid, non-zero if invalid
```

## Important Notes

- **Configuration is immutable during workflow execution**: Changes require re-rendering agents/workflows
- **Validation happens at load time**: Invalid config blocks execution (fail-fast principle)
- **Defaults provided for optional fields**: Don't need to specify everything
- **Type safety via Pydantic**: Catches type errors before runtime
- **Version controlled**: Commit `.claude/config.yaml` so team shares same standards

## Real Failure Scenarios Prevented

### Scenario 1: AI Guesses Wrong Development Mode
**Without config**: User wants quick prototype to demo to stakeholders. AI doesn't know this, builds production-ready code with comprehensive tests, error handling, edge cases. Takes 2 weeks. Demo window missed.

**With config**: `development.mode: "prototype"` in config. AI skips edge cases, builds happy path only. Demo ready in 3 days.

### Scenario 2: Quality Standards Unenforced
**Without config**: Team verbally agrees "80% test coverage required". AI doesn't know. Ships feature with 45% coverage. Production breaks.

**With config**: `test_coverage_min: 80` in config. AI writes tests to meet threshold. Coverage gate blocks merge if <80%.

### Scenario 3: Work Tracking Integration Broken
**Without config**: Workflow claims to create Azure DevOps work items, but organization URL wrong. Work items created in wrong org (or fail silently). Discover during sprint review.

**With config**: Schema validation requires correct organization URL format. Invalid URL caught at `trustable-ai validate`. Fix before workflows run.

## Related

- **VISION.md**: Pillar #1 (Explicit Human Intent), Design Principle #3 (Explicit Intent Before Work)
- **config/schema.py**: Pydantic validation models
- **config/loader.py**: Configuration loading implementation
- **.claude/config.yaml**: Project configuration file (created by `trustable-ai init`)
- **agents/**: Agents that read configuration to guide behavior
- **workflows/**: Workflows that use configuration for verification gates
