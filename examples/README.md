# Trusted AI Development (TAID) - Examples

This directory contains complete example projects demonstrating how to use TAID with different tech stacks and work tracking platforms.

## Available Examples

### [Python FastAPI](./python-fastapi/)

Complete example for Python FastAPI projects:
- **Language**: Python 3.10+
- **Framework**: FastAPI, Pydantic, SQLAlchemy
- **Work Tracking**: Azure DevOps (Scrum template)
- **Deployment**: Azure App Service
- **CI/CD**: GitHub Actions

**Best for**: REST APIs, microservices, data platforms

[View Example →](./python-fastapi/README.md)

### [.NET Web API](./dotnet-webapi/)

Complete example for .NET Web API projects:
- **Language**: C# / .NET 8
- **Framework**: ASP.NET Core, Entity Framework Core
- **Work Tracking**: Azure DevOps (Agile template)
- **Deployment**: Azure App Service
- **CI/CD**: Azure DevOps Pipelines

**Best for**: Enterprise APIs, corporate applications, Azure-first projects

[View Example →](./dotnet-webapi/README.md)

## Quick Start

### 1. Choose Your Example

Pick the example that matches your tech stack:

```bash
# For Python projects
cd examples/python-fastapi

# For .NET projects
cd examples/dotnet-webapi
```

### 2. Follow the README

Each example includes:
- Complete setup instructions
- Configuration examples
- Usage guide with real commands
- Integration patterns (CI/CD, quality gates)
- Customization best practices
- Troubleshooting guide

### 3. Adapt for Your Project

Copy the patterns to your own project:

```bash
# Install TAID
pip install trusted-ai-dev

# Initialize in your project
cd your-project
trustable-ai init

# Copy example config as starting point
cp examples/python-fastapi/.claude/config.yaml .claude/config.yaml

# Customize for your project
vi .claude/config.yaml
```

## Example Comparison

| Feature | Python FastAPI | .NET Web API |
|---------|----------------|--------------|
| **Language** | Python 3.10+ | C# / .NET 8 |
| **Framework** | FastAPI | ASP.NET Core |
| **ORM** | SQLAlchemy | Entity Framework Core |
| **Testing** | pytest | xUnit |
| **Process Template** | Scrum | Agile |
| **Work Item Types** | Epic, Feature, User Story, Task, Bug | Epic, Feature, User Story, Task, Bug |
| **CI/CD** | GitHub Actions | Azure DevOps Pipelines |
| **Custom Fields** | API Endpoint, Performance SLA | API Contract, Breaking Change, EF Migration |
| **Quality Tools** | black, ruff, mypy, pytest-cov | StyleCop, Coverlet, dotnet-format |
| **Best For** | Startups, ML/AI projects, APIs | Enterprise, corporate, Azure-first |

## Common Patterns

### Agent Customization

Both examples show how to customize agents for your domain:

**Generic Agent:**
```markdown
# Senior Engineer

Break down features into tasks and estimate story points.
```

**Domain-Specific Agent (Python FastAPI):**
```markdown
# Senior Engineer - FastAPI Specialist

## Task Breakdown for FastAPI
- API endpoint with Pydantic model: 2-3 SP
- Database model with SQLAlchemy: 1-2 SP
- Async background task: 3-5 SP
- pytest test suite: 2-3 SP
```

### Workflow Integration

Both examples demonstrate:
- Sprint planning automation
- Backlog grooming workflows
- Sprint retrospectives
- CI/CD integration
- Quality gates

### Configuration Patterns

Learn how to configure:
- Work item type mapping (different process templates)
- Custom fields for your domain
- Quality standards for your stack
- Agent model selection (opus vs sonnet)
- Deployment environments

## Creating Your Own Example

Want to contribute an example for another stack? Here's the structure:

```
examples/your-stack/
├── README.md                   # Complete guide (see existing examples)
├── .claude/
│   └── config.yaml            # Example configuration
├── sample-project/            # (Optional) Sample code
│   ├── src/
│   └── tests/
└── docs/                      # (Optional) Additional docs
    ├── customization.md
    └── advanced-patterns.md
```

### Requirements for New Examples

1. **Comprehensive README** with:
   - Project overview
   - Complete setup instructions
   - Configuration example
   - Usage guide with actual commands
   - Integration patterns
   - Best practices
   - Troubleshooting

2. **Working Configuration**:
   - `.claude/config.yaml` tailored for the stack
   - Custom fields relevant to the domain
   - Appropriate quality standards
   - Correct work item type mappings

3. **Customized Agents** (optional):
   - Show how to customize for the stack
   - Include code examples in the agent's language
   - Reference stack-specific patterns

4. **CI/CD Integration**:
   - Example pipeline configuration
   - Quality gate implementation
   - Automated workflow execution

## Tech Stacks We'd Love to See

Community contributions welcome for:

- **Java Spring Boot**: Enterprise Java projects with Azure DevOps
- **Node.js/Express**: JavaScript APIs with GitHub Projects
- **Ruby on Rails**: Rails projects with Jira
- **Go**: Go microservices with Azure DevOps
- **React/Vue/Angular**: Frontend projects with different work tracking
- **Mobile (Flutter/React Native)**: Mobile app development workflows
- **Data Engineering (Databricks/Airflow)**: Data pipeline projects

## Support

- Framework Documentation: [Main README](../README.md)
- Issues: https://github.com/trusted-ai-dev/trusted-ai-dev/issues

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines on contributing examples.

---

*Examples for Trusted AI Development (TAID)*
