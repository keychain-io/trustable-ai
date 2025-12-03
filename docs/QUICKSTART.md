# Trusted AI Development (TAID) - Quick Start Guide

Get up and running with TAID in 15 minutes.

## Prerequisites

- Python 3.9 or higher
- pip package manager
- Azure CLI (for Azure DevOps integration)
- Git (optional, for version control)

## Installation

### Step 1: Install the Package

```bash
# Install from PyPI
pip install trusted-ai-dev

# Or install with Azure DevOps support
pip install trusted-ai-dev[azure]

# Or install from source (during development)
cd /path/to/trusted-ai-dev
pip install -e ".[dev,azure]"
```

### Step 2: Verify Installation

```bash
# Check CLI is available
trustable-ai --version

# Should output: trustable-ai, version 1.0.0
```

## Initial Setup

### Step 3: Navigate to Your Project

```bash
cd /path/to/your/project
```

### Step 4: Initialize Framework

```bash
trustable-ai init
```

You'll be prompted for:
- **Project name**: e.g., "My Web App"
- **Project type**: Choose from web-application, api, mobile-app, etc.
- **Programming languages**: e.g., "Python, TypeScript"
- **Frameworks**: e.g., "FastAPI, React"
- **Platforms**: e.g., "Azure, Docker"
- **Databases**: e.g., "PostgreSQL"
- **Work tracking platform**: azure-devops, or file-based
- **Organization URL**: e.g., "https://dev.azure.com/your-org"
- **Project name**: Your project name in the work tracking system

This creates:
- `.claude/` directory
- `.claude/config.yaml` - Your configuration file
- `.claude/agents/` - Agent definitions directory
- `.claude/commands/` - Workflow slash commands directory
- `.claude/workflow-state/` - Workflow state files
- `.claude/profiling/` - Performance profiles

### Step 5: Configure Azure DevOps (Optional)

If using Azure DevOps:

```bash
# Configure connection
trustable-ai configure azure-devops

# Test connection (requires Azure CLI)
az login
az devops configure --defaults organization=https://dev.azure.com/your-org project="Your Project"
```

Or use file-based tracking (no external dependencies):

```bash
trustable-ai configure file-based
```

### Step 6: Enable Agents

```bash
# List available agents
trustable-ai agent list

# Enable the agents you want
trustable-ai agent enable business-analyst
trustable-ai agent enable senior-engineer
trustable-ai agent enable scrum-master
trustable-ai agent enable project-architect
trustable-ai agent enable security-specialist

# See which agents are enabled
trustable-ai agent list --enabled-only
```

### Step 7: Render Agents

```bash
# Render all enabled agents
trustable-ai agent render-all

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
trustable-ai configure quality-standards
```

### Step 9: Validate Setup

```bash
# Run validation
trustable-ai validate

# Should show:
# ✓ Configuration file exists
# ✓ Required directories exist
# ✓ Agent templates available (12 agents)
# ✓ Work tracking configured
# ✓ Quality standards configured
# ✓ Agents enabled (5)
```

## Using the Framework

### Render Workflows

```bash
# List available workflows
trustable-ai workflow list

# Render a specific workflow
trustable-ai workflow render sprint-planning -o .claude/commands/sprint-planning.md

# Or render all workflows
trustable-ai workflow render-all
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
trustable-ai workflow render sprint-planning -o .claude/commands/sprint-planning.md
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
trustable-ai agent render-all

# When you enable a new agent
trustable-ai agent enable qa-engineer
trustable-ai agent render qa-engineer -o .claude/agents/qa-engineer.md
```

### Rendering Workflows

```bash
# When you update configuration
trustable-ai workflow render-all

# When you add custom fields or change work item types
trustable-ai workflow render sprint-planning -o .claude/commands/sprint-planning.md
```

### Validation

```bash
# Before running workflows
trustable-ai validate

# Check specific items
trustable-ai agent list --enabled-only
trustable-ai workflow list
```

## Troubleshooting

### Configuration Not Found

```bash
❌ Error: Configuration file not found
```

**Solution**: Run `trustable-ai init` to initialize the framework.

### Agent Not Found

```bash
❌ Agent 'unknown-agent' not found
```

**Solution**: Run `trustable-ai agent list` to see available agents.

### Azure DevOps Connection Failed

```bash
❌ Connection failed
```

**Solution**:
1. Run `az login` to authenticate
2. Run `az devops configure` to set defaults
3. Test with `trustable-ai configure azure-devops`

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
- **Validation**: Run `trustable-ai validate`
- **Health Check**: Run `trustable-ai doctor`

## Summary

You've successfully:
- ✅ Installed Trusted AI Development (TAID)
- ✅ Initialized framework in your project
- ✅ Configured work tracking platform
- ✅ Enabled and rendered agents
- ✅ Validated setup
- ✅ Ready to run workflows!

Time to completion: ~15 minutes

Ready to automate your workflows!
