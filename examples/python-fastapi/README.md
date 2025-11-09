# Python FastAPI Example - Claude Workflow Framework

This example demonstrates how to use the Claude Workflow Framework with a Python FastAPI project.

## Project Overview

- **Project Type**: Web API
- **Language**: Python 3.10+
- **Framework**: FastAPI
- **Work Tracking**: Azure DevOps (Scrum template)
- **CI/CD**: GitHub Actions
- **Deployment**: Azure App Service

## Setup

### 1. Install Claude Workflow Framework

```bash
pip install claude-workflow-framework
```

### 2. Initialize in Your Project

```bash
cd your-fastapi-project
cwf init
```

Answer the prompts:
- Project name: `My FastAPI Project`
- Project type: `api` (choose from menu)
- Languages: `Python`
- Frameworks: `FastAPI,Pydantic`
- Platforms: `Azure,Docker`

### 3. Configure Azure DevOps

```bash
cwf configure azure-devops
```

Provide your Azure DevOps details:
- Organization: `https://dev.azure.com/your-org`
- Project: `Your Project Name`
- Process Template: `Scrum` (default)

### 4. Configure Quality Standards

```bash
cwf configure quality-standards
```

Set your quality thresholds:
- Test coverage minimum: `80%` (recommended for APIs)
- Critical vulnerabilities: `0`
- High vulnerabilities: `0`

## Configuration Example

The framework generates `.claude/config.yaml`:

```yaml
project:
  name: "My FastAPI Project"
  type: "api"
  description: "REST API built with FastAPI for customer management"
  source_directory: "src"
  test_directory: "tests"

  tech_stack:
    languages:
      - "Python"
    frameworks:
      - "FastAPI"
      - "Pydantic"
      - "SQLAlchemy"
    platforms:
      - "Azure"
      - "Docker"
    databases:
      - "PostgreSQL"
    tools:
      - "pytest"
      - "black"
      - "ruff"
      - "mypy"

work_tracking:
  platform: "azure-devops"
  organization: "https://dev.azure.com/your-org"
  project: "My FastAPI Project"
  process_template: "scrum"
  credentials_source: "env:AZURE_DEVOPS_PAT"

  work_item_types:
    epic: "Epic"
    feature: "Feature"
    story: "User Story"
    task: "Task"
    bug: "Bug"

  custom_fields:
    business_value: "Custom.BusinessValueScore"
    api_endpoint: "Custom.APIEndpoint"
    performance_sla: "Custom.PerformanceSLA"

  sprint_naming: "Sprint {number}"
  iteration_format: "{project}\\Sprint {sprint}"

quality_standards:
  test_coverage_min: 80
  critical_vulnerabilities_max: 0
  high_vulnerabilities_max: 0
  medium_vulnerabilities_max: 5
  code_complexity_max: 10
  duplicate_code_max: 3
  build_time_max_minutes: 5
  test_time_max_minutes: 10

agent_config:
  models:
    architect: "claude-opus-4"
    engineer: "claude-sonnet-4.5"
    analyst: "claude-sonnet-4.5"
    security: "claude-sonnet-4.5"
    scrum-master: "claude-sonnet-4.5"

  enabled_agents:
    - "business-analyst"
    - "project-architect"
    - "senior-engineer"
    - "security-specialist"
    - "scrum-master"

workflow_config:
  state_directory: ".claude/workflow-state"
  profiling_directory: ".claude/profiling"
  checkpoint_enabled: true
  verification_enabled: true
  max_retries: 3
  timeout_minutes: 60

deployment_config:
  environments:
    - "local"
    - "dev"
    - "uat"
    - "prod"
  default_environment: "dev"
  deployment_tasks_enabled: true
  deployment_task_types:
    - "deployment-task"
    - "infrastructure-task"
```

## Usage

### Enable Agents

```bash
# Enable all recommended agents for API projects
cwf agent enable business-analyst
cwf agent enable project-architect
cwf agent enable senior-engineer
cwf agent enable security-specialist
cwf agent enable scrum-master

# Or list available agents
cwf agent list
```

### Render Agent Definitions

```bash
# Render all enabled agents to .claude/agents/
cwf agent render-all -o .claude/agents

# Or render specific agent
cwf agent render senior-engineer -o .claude/agents/senior-engineer.md
```

### Render Workflows

```bash
# Render sprint planning workflow
cwf workflow render sprint-planning -o .claude/commands/sprint-planning.md

# Render backlog grooming workflow
cwf workflow render backlog-grooming -o .claude/commands/backlog-grooming.md

# Render sprint retrospective workflow
cwf workflow render sprint-retrospective -o .claude/commands/sprint-retrospective.md

# Render all workflows
cwf workflow render-all -o .claude/commands
```

### Run Workflows

#### Sprint Planning

```bash
# Dry run (see what would happen)
cwf workflow run sprint-planning --dry-run --sprint "Sprint 10" --capacity 40

# Actual execution
cwf workflow run sprint-planning --sprint "Sprint 10" --capacity 40
```

The sprint planning workflow will:
1. Analyze backlog items with Business Analyst
2. Review architecture implications with Project Architect
3. Perform security assessment with Security Specialist
4. Break down features into tasks with Senior Engineer
5. Create work items in Azure DevOps
6. Generate deployment tasks
7. Provide sprint commitment summary

#### Backlog Grooming

```bash
cwf workflow run backlog-grooming --limit 10
```

This will:
1. Fetch top 10 backlog items from Azure DevOps
2. Assign business value scores
3. Identify technical risks
4. Update work items with findings
5. Mark items as "Ready" for sprint planning

#### Sprint Retrospective

```bash
cwf workflow run sprint-retrospective --sprint "Sprint 9"
```

This will:
1. Collect sprint metrics from Azure DevOps
2. Analyze what went well and what needs improvement
3. Generate technical and security insights
4. Create improvement work items
5. Generate retrospective report

### Validate Setup

```bash
cwf validate
```

This checks:
- Configuration file validity
- Directory structure
- Agent templates availability
- Work tracking connectivity
- Quality standards configuration

## Integration with FastAPI Development

### Pre-commit Hooks

Add to `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: cwf-validate
        name: Validate Claude Workflow Framework
        entry: cwf validate
        language: system
        pass_filenames: false
```

### CI/CD Integration (GitHub Actions)

Add to `.github/workflows/sprint-planning.yml`:

```yaml
name: Sprint Planning Automation

on:
  schedule:
    - cron: '0 9 * * 1'  # Every Monday at 9 AM
  workflow_dispatch:

jobs:
  sprint-planning:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install claude-workflow-framework

      - name: Run Sprint Planning
        env:
          AZURE_DEVOPS_PAT: ${{ secrets.AZURE_DEVOPS_PAT }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          cwf workflow run sprint-planning --sprint "Sprint ${{ github.run_number }}"
```

### Environment Variables

Set these in your environment or `.env` file:

```bash
# Azure DevOps
export AZURE_DEVOPS_PAT="your-personal-access-token"

# Anthropic API (for Claude)
export ANTHROPIC_API_KEY="your-api-key"

# Optional: Custom config path
export CWF_CONFIG_PATH=".claude/config.yaml"
```

## Project Structure

After initialization, your project will have:

```
your-fastapi-project/
├── .claude/
│   ├── config.yaml                    # Framework configuration
│   ├── agents/                         # Rendered agent definitions
│   │   ├── business-analyst.md
│   │   ├── senior-engineer.md
│   │   ├── scrum-master.md
│   │   ├── project-architect.md
│   │   └── security-specialist.md
│   ├── commands/                       # Rendered workflow commands
│   │   ├── sprint-planning.md
│   │   ├── backlog-grooming.md
│   │   └── sprint-retrospective.md
│   ├── workflow-state/                 # Workflow execution state
│   ├── profiling/                      # Performance profiles
│   └── retrospectives/                 # Sprint retrospective reports
├── src/                                # Your FastAPI code
├── tests/                              # Your tests
├── requirements.txt
└── pyproject.toml
```

## Best Practices

### 1. Customize Agent Templates

Edit `.claude/agents/*.md` to include FastAPI-specific guidance:

```markdown
# Senior Engineer - FastAPI Specialist

## Tech Stack Context
- Python 3.10+ with FastAPI
- Async/await patterns
- Pydantic models for validation
- SQLAlchemy ORM
- pytest for testing

## Task Breakdown Guidelines
- Each API endpoint = 1 task (2-3 story points)
- Database migration = 1 task (1-2 story points)
- Integration test suite = 1 task (2-3 story points)
- API documentation = 1 task (1 story point)
```

### 2. Custom Fields for API Projects

Add API-specific custom fields in Azure DevOps:

- `Custom.APIEndpoint`: Which endpoint this story relates to
- `Custom.PerformanceSLA`: Expected response time (e.g., "< 200ms")
- `Custom.DataModel`: Pydantic models involved

Update `.claude/config.yaml`:

```yaml
work_tracking:
  custom_fields:
    api_endpoint: "Custom.APIEndpoint"
    performance_sla: "Custom.PerformanceSLA"
    data_model: "Custom.DataModel"
```

### 3. Quality Gates

Integrate with your CI/CD:

```yaml
# In your .github/workflows/ci.yml
- name: Check Quality Standards
  run: |
    coverage_pct=$(pytest --cov=src --cov-report=term | grep "TOTAL" | awk '{print $4}' | sed 's/%//')
    if [ $coverage_pct -lt 80 ]; then
      echo "Test coverage $coverage_pct% is below minimum 80%"
      exit 1
    fi
```

## Troubleshooting

### Issue: Azure DevOps connection fails

**Solution**:
```bash
# Verify PAT is set
echo $AZURE_DEVOPS_PAT

# Test Azure CLI
az login
az devops configure --defaults organization=https://dev.azure.com/your-org project="Your Project"
```

### Issue: Workflow state conflicts

**Solution**:
```bash
# List workflow states
ls .claude/workflow-state/

# Remove old state to start fresh
rm .claude/workflow-state/sprint-planning-*.json
```

### Issue: Agent renders with wrong tech stack

**Solution**:
```bash
# Verify configuration
cwf validate

# Re-render agents
cwf agent render-all -o .claude/agents --force
```

## Next Steps

1. **Run your first sprint planning**:
   ```bash
   cwf workflow run sprint-planning --sprint "Sprint 1" --capacity 40
   ```

2. **Customize agents** for your domain (e-commerce, healthcare, etc.)

3. **Create custom workflows** for your specific needs

4. **Integrate with CI/CD** for automated workflow execution

5. **Train your team** on using the rendered agents and workflows

## Support

- Framework Documentation: https://github.com/keychain/claude-workflow-framework
- Issues: https://github.com/keychain/claude-workflow-framework/issues
- Discussions: https://github.com/keychain/claude-workflow-framework/discussions

---

*Example project for Claude Workflow Framework*
