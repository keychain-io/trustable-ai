---
context:
  purpose: "Individual CLI command modules that prevent user errors through validation and guided execution"
  problem_solved: "Users invoke commands with wrong parameters, in wrong order, or with invalid state. Without command-level validation and help, errors are cryptic and hard to recover from."
  keywords: [cli, commands, init, validate, agent, workflow, configure]
  task_types: [cli, implementation, tooling]
  priority: low
  max_tokens: 400
  children: []
  dependencies: [core, config, agents, workflows]
---
# CLI Commands

## Purpose

Solves **command invocation errors** through validation, helpful error messages, and guided execution.

Users invoke CLI commands incorrectly:
- Wrong parameters → cryptic error messages
- Missing prerequisites → silent failures
- Invalid order → partial state, hard to recover
- Typos → command not found, no suggestions

Each command module provides **validation before execution** and **actionable error messages**, catching mistakes before they cause problems.

## Commands

- **init.py**: Project initialization with prompts
- **validate.py**: Configuration and documentation validation
- **agent.py**: Agent management (list, enable, render)
- **workflow.py**: Workflow management (list, render)
- **configure.py**: Work tracking platform configuration
- **context.py**: Context generation and management

All commands validate inputs and provide clear error messages with suggested fixes.

## Related

- **cli/CLAUDE.md**: Parent CLI documentation
- **config/CLAUDE.md**: Configuration that commands validate
