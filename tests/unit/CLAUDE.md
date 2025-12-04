---
context:
  purpose: "Fast unit tests that catch component logic errors without external dependencies"
  problem_solved: "Without fast unit tests, logic errors go undetected until integration testing or production. Unit tests provide immediate feedback on component correctness, catching bugs seconds after they're introduced."
  keywords: [unit, tests, fast, isolated, logic]
  task_types: [testing, unit, validation]
  priority: medium
  max_tokens: 600
  children: []
  dependencies: [core, config, agents, workflows, adapters]
---
# Unit Tests

## Purpose

Solves **slow feedback on logic errors** by providing fast (<1s), isolated tests that catch bugs immediately after introduction.

Without fast unit tests:
- Logic errors discovered hours/days later in integration testing
- Debugging harder (many changes since bug introduced)
- Test suite slow → developers skip running tests
- Coverage gaps → untested code paths fail in production

Unit tests provide **immediate feedback** - run in seconds, catch errors right away, pinpoint exact failure.

## Test Coverage

- **Configuration**: Config loading, validation, schema enforcement
- **State Management**: Checkpoint save/load, state corruption handling
- **Profiling**: Performance tracking, report generation
- **Context Loading**: Hierarchical loading, keyword matching, token budgets
- **Field/Type Mapping**: Azure DevOps field and type translation
- **Agent/Workflow Registry**: Template rendering, config injection

## Running Unit Tests

```bash
# All unit tests (fast - 2-3 seconds)
pytest -m unit

# Specific unit test file
pytest tests/unit/test_config.py

# Specific test function
pytest tests/unit/test_config.py::test_load_config_success
```

## Test Characteristics

- **Fast**: <1s per test, entire suite runs in 2-3 seconds
- **Isolated**: No external dependencies (files, network, databases)
- **Deterministic**: Same input → same output every time
- **Focused**: One behavior per test

## Important Notes

- Use `tmp_path` fixture for file operations (pytest built-in)
- Mock external services with `unittest.mock`
- One assert per test (focus on single behavior)
- Descriptive test names explain what's being validated

## Related

- **tests/CLAUDE.md**: Parent testing documentation
- **tests/integration/CLAUDE.md**: Integration tests for component interactions
