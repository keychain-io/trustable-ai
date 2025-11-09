# Claude Workflow Framework - Quick Start Guide

Get up and running with Claude Workflow Framework in 15 minutes.

## Prerequisites

- Python 3.9 or higher
- pip package manager
- Azure CLI (for Azure DevOps integration)
- Git (optional, for version control)

## Installation

### Step 1: Install the Framework

```bash
# Install from source (during development)
cd /path/to/claude-workflow-framework
pip install -e .

# Or install with all optional dependencies
pip install -e ".[dev,azure]"
```

### Step 2: Verify Installation

```bash
# Check CLI is available
cwf --version

# Should output: Claude Workflow Framework 0.1.0
```

## Initial Setup

### Step 3: Navigate to Your Project

```bash
cd /path/to/your/project
```

### Step 4: Initialize Framework

```bash
cwf init
```

You'll be prompted for:
- **Project name**: e.g., "My Web App"
- **Project type**: Choose from web-application, api, mobile-app, etc.
- **Programming languages**: e.g., "Python, TypeScript"
- **Frameworks**: e.g., "FastAPI, React"
- **Platforms**: e.g., "Azure, Docker"
- **Databases**: e.g., "PostgreSQL"
- **Work tracking platform**: azure-devops, jira, or github-projects
- **Organization URL**: e.g., "https://dev.azure.com/your-org"
- **Project name**: Your project name in the work tracking system

This creates:
- `.claude/` directory
- `.claude/config.yaml` - Your configuration file
- `.claude/agents/` - Agent definitions directory
- `.claude/commands/` - Workflow scripts directory
- `.claude/workflow-state/` - Workflow state files
- `.claude/profiling/` - Performance profiles

### Step 5: Configure Azure DevOps (Optional)

If using Azure DevOps:

```bash
# Configure connection
cwf configure azure-devops

# Test connection (requires Azure CLI)
az login
az devops configure --defaults organization=https://dev.azure.com/your-org project="Your Project"
```

### Step 6: Enable Agents

```bash
# List available agents
cwf agent list

# Enable the agents you want
cwf agent enable business-analyst
cwf agent enable senior-engineer
cwf agent enable scrum-master
cwf agent enable project-architect
cwf agent enable security-specialist

# See which agents are enabled
cwf agent list --enabled-only
```

### Step 7: Render Agents

```bash
# Render all enabled agents
cwf agent render-all

# This creates:
# .claude/agents/business-analyst.md
# .claude/agents/senior-engineer.md
# .claude/agents/scrum-master.md
# etc.
```

### Step 8: Review Configuration

```bash
# Edit configuration if needed
vi .claude/config.yaml

# Configure quality standards
cwf configure quality-standards
```

### Step 9: Validate Setup

```bash
# Run validation
cwf validate

# Should show:
# ✓ Configuration file exists
# ✓ Required directories exist
# ✓ Agent templates available (5 agents)
# ✓ Work tracking configured
# ✓ Quality standards configured
# ✓ Agents enabled (5)
```

## Using the Framework

### Render Workflows

```bash
# List available workflows
cwf workflow list

# Render a specific workflow
cwf workflow render sprint-planning -o .claude/commands/sprint-planning.md

# Or render all workflows
cwf workflow render-all
```

### Customize for Your Project

#### 1. Edit Configuration

```yaml
# .claude/config.yaml

# Update work item type mappings for your process template
work_tracking:
  work_item_types:
    epic: "Epic"
    feature: "Feature"
    story: "User Story"  # or "Story" for some templates
    task: "Task"
    bug: "Bug"

  # Add your custom fields
  custom_fields:
    business_value: "Custom.BusinessValueScore"
    technical_risk: "Custom.TechnicalRisk"
    roi_projection: "Custom.ROI"

# Set quality standards
quality_standards:
  test_coverage_min: 80  # Your minimum test coverage
  critical_vulnerabilities_max: 0
  high_vulnerabilities_max: 0
```

#### 2. Customize Agent Models

```yaml
# Choose which Claude model each agent uses
agent_config:
  models:
    architect: "claude-opus-4"      # Complex reasoning
    engineer: "claude-sonnet-4.5"   # General purpose
    analyst: "claude-sonnet-4.5"    # Business analysis
    security: "claude-sonnet-4.5"   # Security review
    scrum-master: "claude-haiku-4"  # Fast, lightweight
```

#### 3. Enable/Disable Features

```yaml
# Deployment automation
deployment_config:
  deployment_tasks_enabled: true  # Auto-create deployment tasks
  environments:
    - dev
    - uat
    - prod

# Workflow settings
workflow_config:
  checkpoint_enabled: true       # Enable workflow resume
  verification_enabled: true     # Verify all operations
  max_retries: 3                # Retry failed operations
```

## Example: Sprint Planning

### 1. Render Sprint Planning Workflow

```bash
cwf workflow render sprint-planning -o .claude/commands/sprint-planning.md
```

### 2. Review the Workflow

```bash
# The rendered workflow is customized for your project:
cat .claude/commands/sprint-planning.md
```

You'll see:
- Your project name
- Your work item types (Feature, Task, etc.)
- Your custom fields
- Your quality standards
- Only enabled agents included

### 3. Execute Workflow in Claude Code

Open Claude Code and run:
```
/sprint-planning
```

The workflow will:
1. Initialize state management
2. Run Business Analyst agent (if enabled)
3. Run Project Architect agent (if enabled)
4. Run Security Specialist agent (if enabled)
5. Run Senior Engineer agent for task breakdown
6. Run Scrum Master agent for sprint plan
7. Ask for human approval
8. Create work items in Azure DevOps
9. Track state for resume capability

## Daily Usage

### Rendering Agents

```bash
# When you update configuration
cwf agent render-all

# When you enable a new agent
cwf agent enable qa-engineer
cwf agent render qa-engineer -o .claude/agents/qa-engineer.md
```

### Rendering Workflows

```bash
# When you update configuration
cwf workflow render-all

# When you add custom fields or change work item types
cwf workflow render sprint-planning -o .claude/commands/sprint-planning.md
```

### Validation

```bash
# Before running workflows
cwf validate

# Check specific items
cwf agent list --enabled-only
cwf workflow list
```

## Troubleshooting

### Configuration Not Found

```bash
❌ Error: Configuration file not found
```

**Solution**: Run `cwf init` to initialize the framework.

### Agent Not Found

```bash
❌ Agent 'unknown-agent' not found
```

**Solution**: Run `cwf agent list` to see available agents.

### Azure DevOps Connection Failed

```bash
❌ Connection failed
```

**Solution**:
1. Run `az login` to authenticate
2. Run `az devops configure` to set defaults
3. Test with `cwf configure azure-devops`

### Work Item Type Mismatch

If work items fail to create, check your work item type mappings:

```bash
# Check your process template in Azure DevOps
# Update config.yaml to match

# For Scrum template
work_item_types:
  story: "User Story"

# For Agile template
work_item_types:
  story: "User Story"

# For Basic template
work_item_types:
  story: "Issue"
```

## Next Steps

- **Customize Agents**: Edit rendered agent files in `.claude/agents/`
- **Add Workflows**: Create custom workflows in `workflows/templates/`
- **Configure Custom Fields**: Add your Azure DevOps custom fields to `config.yaml`
- **Set Quality Standards**: Configure test coverage and vulnerability thresholds
- **Run Sprint Planning**: Use the rendered workflow in Claude Code

## Getting Help

- **Documentation**: See `docs/` directory
- **Configuration**: See `.claude/config.yaml`
- **Examples**: See `examples/` directory
- **Validation**: Run `cwf validate`

## Summary

You've successfully:
- ✅ Installed Claude Workflow Framework
- ✅ Initialized framework in your project
- ✅ Configured work tracking platform
- ✅ Enabled and rendered agents
- ✅ Validated setup
- ✅ Ready to run workflows!

Time to completion: ~15 minutes

Ready to automate your workflows! 🚀
