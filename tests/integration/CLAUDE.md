---
context:
  purpose: "Integration tests that catch component interaction failures and system dependency issues"
  problem_solved: "Unit tests validate components in isolation but miss integration failures - file I/O errors, CLI command issues, template rendering failures. Integration tests catch failures that occur when components interact or depend on system resources."
  keywords: [integration, tests, cli, file-io, end-to-end]
  task_types: [testing, integration, validation]
  priority: medium
  max_tokens: 600
  children: []
  dependencies: [core, config, cli, agents, workflows]
---
# Integration Tests

## Purpose

Solves **component interaction failures** that unit tests miss by testing components working together with real system dependencies.

Unit tests validate isolated logic but miss:
- File I/O failures (permissions, paths)
- CLI command failures (subprocess errors, output parsing)
- Template rendering failures (Jinja2 errors with real data)
- End-to-end workflow failures (step interactions)

Integration tests catch these failures by running components against real (or realistic) system resources.

## Test Coverage

- **CLI Commands**: `trustable-ai init`, `validate`, `agent render`, etc.
- **File Operations**: Config loading, state persistence, template rendering
- **Template Rendering**: Agents and workflows with project config
- **Azure DevOps**: Work item operations (requires Azure DevOps setup)

## Running Integration Tests

```bash
# All integration tests
pytest -m integration

# Excluding Azure tests (require Azure DevOps)
pytest -m "integration and not azure"

# Specific integration test
pytest tests/integration/test_cli_init.py
```

## Important Notes

- Integration tests slower than unit tests (1-5s each vs <1s)
- Azure tests require Azure DevOps configuration and authentication
- Tests use temporary directories to avoid polluting project
- Some tests require network access

## Related

- **tests/CLAUDE.md**: Parent testing documentation
- **tests/unit/CLAUDE.md**: Unit tests for isolated logic
