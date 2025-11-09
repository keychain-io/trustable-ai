# Claude Workflow Framework

A reusable workflow automation framework for Claude Code featuring multi-agent orchestration, state management, and work tracking platform integration.

## Overview

The Claude Workflow Framework provides a sophisticated system for automating software development workflows using AI agents. Originally developed for the Keychain Gateway project, this framework has been extracted and generalized to work with any project, tech stack, and work tracking platform.

## Key Features

- **Multi-Agent Orchestration**: Coordinate specialized AI agents (Business Analyst, Project Architect, Security Specialist, Senior Engineer, Scrum Master)
- **State Management**: Robust workflow state tracking with checkpoint and resume capabilities
- **Performance Profiling**: Track workflow execution time, agent calls, and performance metrics
- **Work Tracking Integration**: Adapters for Azure DevOps (extensible to Jira, GitHub Projects, etc.)
- **Hierarchical Context Loading**: Intelligent context management to minimize token usage
- **Template System**: Customizable Jinja2 templates for agents, workflows, and tasks
- **CLI Tool**: Command-line interface for setup, configuration, and workflow execution

## Quick Start

### Installation

```bash
pip install claude-workflow-framework
```

### Initialize in Your Project

```bash
cd your-project/
cwf init
```

This will:
1. Prompt you for project information (name, tech stack, etc.)
2. Configure your work tracking platform (Azure DevOps, Jira, etc.)
3. Create `.claude/` directory structure
4. Generate configuration files
5. Set up agents and workflows

### Configure Azure DevOps

```bash
cwf configure azure-devops
```

Provide your organization, project, and credentials when prompted.

### Enable Agents and Workflows

```bash
# Enable specific agents
cwf agent enable business-analyst
cwf agent enable senior-engineer
cwf agent enable scrum-master

# Enable workflows
cwf workflow enable sprint-planning
cwf workflow enable backlog-grooming
```

### Run Your First Workflow

```bash
cwf run sprint-planning --sprint "Sprint 1" --capacity 40
```

## Architecture

### Core Components

- **State Manager**: Tracks workflow execution state, enables checkpointing and resume
- **Profiler**: Measures workflow performance and agent execution times
- **Context Loader**: Intelligently loads relevant context to minimize token usage
- **Orchestrator**: Coordinates agent execution and workflow steps

### Adapters

Platform-specific integrations:
- **Azure DevOps**: Complete integration with work items, sprints, queries
- **Jira** (planned): Issue tracking and sprint management
- **GitHub Projects** (planned): Project boards and issues

### Agent System

Specialized AI agents with customizable prompts:
- **Business Analyst**: Requirements analysis, prioritization, business value scoring
- **Project Architect**: Technical architecture, risk assessment, technology decisions
- **Security Specialist**: Security review, vulnerability analysis, threat modeling
- **Senior Engineer**: Task breakdown, story point estimation, implementation planning
- **Scrum Master**: Workflow coordination, sprint management, team facilitation

### Template System

All agents, workflows, and tasks use Jinja2 templates that can be customized for your:
- Tech stack (Python, C#, Java, TypeScript, etc.)
- Frameworks (FastAPI, .NET, Spring Boot, React, etc.)
- Quality standards (test coverage, vulnerability thresholds, etc.)
- Work item types and custom fields

## Configuration

Create `.claude/config.yaml` in your project:

```yaml
project:
  name: "your-project"
  type: "web-application"
  tech_stack:
    languages: ["Python", "TypeScript"]
    frameworks: ["FastAPI", "React"]
    platforms: ["Azure", "Docker"]

work_tracking:
  platform: "azure-devops"
  organization: "https://dev.azure.com/yourorg"
  project: "Your Project"
  credentials_source: "env:AZURE_DEVOPS_PAT"

  work_item_types:
    epic: "Epic"
    feature: "Feature"
    task: "Task"
    bug: "Bug"

  custom_fields:
    business_value: "Custom.BusinessValueScore"
    technical_risk: "Custom.TechnicalRisk"

  sprint_naming: "Sprint {number}"

quality_standards:
  test_coverage_min: 80
  critical_vulnerabilities_max: 0
  high_vulnerabilities_max: 0

agent_config:
  models:
    architect: "claude-opus-4"
    engineer: "claude-sonnet-4.5"
    analyst: "claude-sonnet-4.5"

  enabled_agents:
    - business-analyst
    - project-architect
    - senior-engineer
    - scrum-master
```

## Available Workflows

### Sprint Planning

Automates the entire sprint planning process:
1. Backlog analysis and prioritization
2. Architecture review
3. Security assessment
4. Task breakdown and estimation
5. Work item creation in Azure DevOps
6. Sprint commitment and capacity planning

```bash
cwf run sprint-planning --sprint "Sprint 10" --capacity 40
```

### Backlog Grooming

Reviews and refines backlog items:
1. Analyzes unrefined backlog items
2. Assigns business value scores
3. Identifies missing requirements
4. Updates work items with findings

```bash
cwf run backlog-grooming --limit 10
```

### Sprint Execution

Monitors sprint progress and creates daily reports:
1. Checks work item status
2. Identifies blockers
3. Tracks velocity
4. Generates burndown data

```bash
cwf run sprint-execution --sprint "Sprint 10"
```

## Customization

### Custom Agents

Create your own agent by adding a Jinja2 template:

```bash
cwf agent create my-custom-agent
```

Edit `.claude/agents/templates/my-custom-agent.j2`:

```jinja2
# My Custom Agent

## Role
{{ role_description }}

## Tech Stack Context
{{ tech_stack_context }}

## Responsibilities
- {{ responsibility_1 }}
- {{ responsibility_2 }}

## Output Format
{{ output_format }}
```

### Custom Workflows

Create custom workflow templates:

```bash
cwf workflow create my-workflow
```

Edit `.claude/workflows/templates/my-workflow.j2` following the workflow DSL.

## Examples

See `examples/` directory for complete projects:
- **python-fastapi**: FastAPI web application with Azure DevOps
- **dotnet-webapi**: .NET Web API with Azure DevOps
- **java-spring**: Spring Boot application with Jira

## Documentation

- [Getting Started](docs/getting-started.md)
- [Configuration Reference](docs/configuration.md)
- [Agent Customization](docs/agent-customization.md)
- [Workflow Creation](docs/workflow-creation.md)
- [Best Practices](docs/best-practices.md)

## Development

```bash
# Clone repository
git clone https://github.com/keychain/claude-workflow-framework
cd claude-workflow-framework

# Install for development
pip install -e ".[dev]"

# Run tests
pytest

# Code quality
black .
ruff .
mypy .
```

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions welcome! Please see CONTRIBUTING.md for guidelines.

## Support

- Issues: https://github.com/keychain/claude-workflow-framework/issues
- Discussions: https://github.com/keychain/claude-workflow-framework/discussions
