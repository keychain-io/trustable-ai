# deployment

## Purpose

Deployment templates for Trustable AI workflows. Contains Jinja2 templates for generating deployment configurations, scripts, and CI/CD pipeline definitions.

## Template Types

This directory is intended to contain:

- **Docker**: Dockerfile and docker-compose templates
- **Kubernetes**: K8s manifest templates (deployments, services, configmaps)
- **CI/CD**: Pipeline templates for GitHub Actions, Azure Pipelines, etc.
- **Infrastructure**: Terraform/CloudFormation templates

## Usage

Templates are rendered by the workflow system with project-specific configuration:

```python
from workflows import WorkflowRegistry

registry = WorkflowRegistry(config)
rendered = registry.render_template("deployment/docker.j2", context)
```

## Adding Templates

1. Create a `.j2` file in the appropriate subdirectory
2. Use Jinja2 syntax with project context variables
3. Available context: `{{ project }}`, `{{ deployment_config }}`, `{{ environment }}`
