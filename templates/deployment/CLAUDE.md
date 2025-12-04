---
context:
  purpose: "Deployment templates that prevent deployment configuration errors and environment inconsistencies"
  problem_solved: "Manual deployment configurations vary between environments, forget critical settings, and lack validation. Templates ensure consistent, validated deployment across all environments."
  keywords: [deployment, templates, docker, kubernetes, ci-cd]
  task_types: [deployment, devops, infrastructure]
  priority: low
  max_tokens: 400
  children: []
  dependencies: [config]
---
# Deployment Templates

## Purpose

Solves **deployment configuration inconsistencies** and **missing environment settings** through standardized, validated templates.

Manual deployment configurations lead to:
- Different settings in dev vs prod → works locally, fails in production
- Forgotten environment variables → runtime failures
- No validation → invalid configs deployed
- Copy-paste errors → credentials leak, ports conflict

Deployment templates provide **validated, environment-specific configurations** that ensure consistent deployment across all environments.

## Template Types

- **Docker**: Dockerfile templates with multi-stage builds
- **Docker Compose**: Local development environment setup
- **Kubernetes**: Production deployment manifests
- **CI/CD**: GitHub Actions / Azure Pipelines templates

All templates use configuration values from `.claude/config.yaml` to ensure deployment matches project configuration.

## Related

- **config/CLAUDE.md**: Configuration driving template rendering
- **VISION.md**: Deployment best practices
