# tests

## Purpose

This directory contains the test suite for the project.

## Test Structure

- CLAUDE.md
- __init__.py
- conftest.py
+ fixtures
+ integration
+ unit

## Running Tests

```bash
# Run all tests
pytest                    # Python
npm test                  # Node.js
go test ./...             # Go

# Run specific test file
pytest tests/test_specific.py
npm test -- --grep "test name"

# Run with coverage
pytest --cov=src
npm run test:coverage
```

## Writing Tests

- Follow existing test patterns and naming conventions
- Name test files with `test_` prefix (Python) or `.test.` suffix (JS)
- Use fixtures and mocks for common setup
- Aim for meaningful test coverage (not just line coverage)
- Test edge cases and error conditions
