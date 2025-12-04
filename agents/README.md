# agents

## Purpose

Agent registry and template rendering system. This module manages specialized AI agent definitions (Business Analyst, Project Architect, etc.) and renders them with project-specific configuration.

## Key Components

- **registry.py**: `AgentRegistry` class for loading, rendering, and managing agent templates
- **templates/**: Jinja2 templates for 12+ specialized agents (business-analyst.j2, project-architect.j2, etc.)
- **__init__.py**: Module exports for AgentRegistry and convenience functions

## Architecture

The agent system uses template-based configuration to adapt agents to your project:

1. **Template Loading**: Jinja2 templates loaded from `templates/` directory
2. **Context Injection**: Project config (tech stack, quality standards, work tracking) injected into templates
3. **Agent Rendering**: Templates rendered to Markdown for Claude Code consumption
4. **Model Assignment**: Different agents can use different Claude models (Opus for architects, Sonnet for engineers)

### AgentRegistry Methods

```python
registry = AgentRegistry(config)
registry.list_agents()                    # List all available agents
registry.render_agent("business-analyst") # Render specific agent
registry.save_rendered_agent(name, dir)   # Save to file
registry.is_agent_enabled(name)           # Check if enabled in config
```

## Available Agents

Templates in `templates/` directory:
- **business-analyst.j2**: Requirements analysis, prioritization
- **project-architect.j2**: Technical architecture, risk assessment
- **senior-engineer.j2**: Task breakdown, story point estimation
- **security-specialist.j2**: Security review, vulnerability analysis
- **scrum-master.j2**: Workflow coordination, sprint management
- **software-developer.j2**: Feature implementation
- **qa-engineer.j2**: Test planning, quality validation
- **devops-engineer.j2**: CI/CD, infrastructure
- **slash-command.j2**: Template for creating agent slash commands

## Usage Examples

```python
from agents import AgentRegistry, load_agent
from config import load_config

# Load and render agent
config = load_config()
registry = AgentRegistry(config)
agent_md = registry.render_agent("business-analyst")

# Save all enabled agents
for agent in registry.get_enabled_agents():
    registry.save_rendered_agent(agent, Path(".claude/agents"))

# Create slash command for agent
slash_cmd = registry.render_agent_slash_command("business-analyst")
```

## Template Context Variables

Templates have access to:
- `project`: name, type, tech_stack, directories
- `work_tracking`: platform, organization, work_item_types
- `quality_standards`: test coverage, vulnerability thresholds, complexity limits
- `agent_config`: models, enabled_agents
- `deployment_config`: environments, task types
- `tech_stack_context`: Formatted tech stack description

## Conventions

- **Template Naming**: Use kebab-case (business-analyst.j2)
- **Agent Enablement**: Configure in `.claude/config.yaml` under `agent_config.enabled_agents`
- **Model Selection**: Map agents to models in `agent_config.models` (architect -> opus, engineer -> sonnet)
- **Slash Commands**: Use `slash-command.j2` template for creating Claude Code commands

## Testing

Test agent rendering:
```bash
pytest tests/unit/test_agent_registry.py
```
