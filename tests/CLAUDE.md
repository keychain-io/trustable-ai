---
context:
  keywords: [test, testing, pytest, coverage, fixture, mock, unit, integration]
  task_types: [testing, quality-assurance]
  priority: medium
  max_tokens: 800
  children:
    - path: tests/unit/CLAUDE.md
      when: [unit, fast]
    - path: tests/integration/CLAUDE.md
      when: [integration, cli, e2e]
  dependencies: []
---
# tests

## Purpose

Comprehensive test suite for TAID framework. Includes unit tests for individual components and integration tests for end-to-end workflows. Uses pytest with markers for test categorization.

## Key Components

- **conftest.py**: Shared pytest fixtures and configuration
- **fixtures/**: Test data, mock configurations, and sample files
- **unit/**: Fast unit tests for individual modules (no external dependencies)
- **integration/**: Integration tests requiring external services or CLI commands
- **__init__.py**: Module initialization

## Test Organization

### Unit Tests (unit/)
Fast tests with no external dependencies:
- **test_agent_registry.py**: Agent template rendering and management
- **test_workflow_registry.py**: Workflow template rendering
- **test_configuration.py**: Configuration loading and validation
- **test_mappers.py**: Field and type mapping for Azure DevOps
- **test_state_manager.py**: Workflow state management
- **test_profiler.py**: Performance profiling
- **test_context_loader.py**: Context loading and hierarchy

### Integration Tests (integration/)
Tests requiring external services or system dependencies:
- **test_cli_init.py**: CLI initialization command
- **test_cli_agent.py**: CLI agent management commands
- **test_cli_workflow.py**: CLI workflow commands
- **test_cli_validate.py**: CLI validation command
- **test_context_generation.py**: End-to-end context generation

## Test Markers

Tests are marked for selective execution:

```python
@pytest.mark.unit          # Fast unit tests (no external deps)
@pytest.mark.integration   # Integration tests
@pytest.mark.azure         # Requires Azure DevOps configuration
@pytest.mark.cli           # CLI command tests
@pytest.mark.slow          # Long-running tests
```

## Running Tests

### Run All Tests
```bash
pytest                     # Run all tests with coverage
pytest --no-cov           # Run without coverage
```

### Run by Marker
```bash
pytest -m unit             # Unit tests only (fast)
pytest -m integration      # Integration tests
pytest -m azure            # Azure DevOps tests
pytest -m cli              # CLI tests
pytest -m "not slow"       # Exclude slow tests
```

### Run Specific Tests
```bash
pytest tests/unit/                    # All unit tests
pytest tests/integration/             # All integration tests
pytest tests/unit/test_config.py      # Specific file
pytest tests/unit/test_config.py::test_load_config  # Specific test
```

### Coverage Reports
```bash
pytest --cov                          # Terminal coverage report
pytest --cov --cov-report=html       # HTML report in htmlcov/
pytest --cov --cov-report=term-missing  # Show missing lines
```

## Writing Tests

### Test Naming Conventions
- **Files**: `test_<module>.py`
- **Functions**: `test_<functionality>()`
- **Classes**: `Test<Module>` (for grouping related tests)

### Using Fixtures

Common fixtures defined in `conftest.py`:
```python
def test_with_temp_config(tmp_path):
    """tmp_path is a pytest fixture for temporary directories."""
    config_file = tmp_path / "config.yaml"
    # Test with temporary config

def test_with_mock_azure(mock_azure_cli):
    """Use mock_azure_cli fixture for Azure DevOps tests."""
    result = mock_azure_cli.create_work_item(...)
    assert result["id"] == 123
```

### Test Structure

```python
import pytest
from config import load_config

@pytest.mark.unit
def test_load_config_success(tmp_path):
    """Test successful configuration loading."""
    # Arrange
    config_path = tmp_path / ".claude" / "config.yaml"
    config_path.parent.mkdir()
    config_path.write_text("""
        project:
          name: "test"
          type: "web-application"
    """)

    # Act
    config = load_config(config_path)

    # Assert
    assert config.project.name == "test"
    assert config.project.type == "web-application"

@pytest.mark.unit
def test_load_config_missing_file():
    """Test error handling for missing config."""
    with pytest.raises(FileNotFoundError):
        load_config(Path("nonexistent/config.yaml"))
```

### Integration Test Example

```python
import pytest
from click.testing import CliRunner
from cli.main import cli

@pytest.mark.integration
@pytest.mark.cli
def test_init_command(tmp_path, monkeypatch):
    """Test trustable-ai init command."""
    # Arrange
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()

    # Act
    result = runner.invoke(cli, ["init"], input="test\nweb-application\n")

    # Assert
    assert result.exit_code == 0
    assert (tmp_path / ".claude" / "config.yaml").exists()
```

## Test Fixtures

### Common Fixtures (conftest.py)
- **tmp_path**: Pytest built-in for temporary directories
- **mock_config**: Mock FrameworkConfig instance
- **mock_azure_cli**: Mock AzureCLI for testing without Azure DevOps
- **sample_work_items**: Sample work item data
- **sample_sprint_data**: Sample sprint configuration

### Creating Custom Fixtures

```python
# In conftest.py
import pytest
from config.schema import FrameworkConfig, ProjectConfig

@pytest.fixture
def sample_config():
    """Provide a sample configuration for testing."""
    return FrameworkConfig(
        project=ProjectConfig(
            name="test-project",
            type="web-application",
            tech_stack={"languages": ["Python"]}
        ),
        # ... other config
    )
```

## Coverage Requirements

- **Minimum Coverage**: 80% (enforced by quality standards)
- **Critical Modules**: Aim for >90% coverage
  - config/
  - core/
  - agents/registry.py
  - workflows/registry.py
- **Reports**: HTML coverage report in `htmlcov/index.html`

## Continuous Integration

Tests run automatically in CI/CD:
```yaml
# Example CI configuration
test:
  script:
    - pip install -e ".[dev]"
    - pytest --cov --cov-report=xml
    - pytest -m "not azure"  # Skip Azure tests in CI
```

## Mocking Strategies

### Mock External Services
```python
from unittest.mock import Mock, patch

@patch('adapters.azure_devops.cli_wrapper.subprocess.run')
def test_create_work_item(mock_run):
    """Test work item creation with mocked subprocess."""
    mock_run.return_value = Mock(
        returncode=0,
        stdout='{"id": 123, "fields": {"System.Title": "Test"}}'
    )

    result = create_work_item("Task", "Test")
    assert result["id"] == 123
```

### Mock File System
```python
def test_save_config(tmp_path):
    """Test config saving with temporary directory."""
    config = create_default_config(...)
    save_config(config, tmp_path / "config.yaml")
    assert (tmp_path / "config.yaml").exists()
```

## Debugging Tests

```bash
# Run with verbose output
pytest -v

# Run with print statements
pytest -s

# Drop into debugger on failure
pytest --pdb

# Run last failed tests
pytest --lf

# Run tests matching keyword
pytest -k "config"
```

## Test Data

Test data located in `tests/fixtures/`:
- **sample_configs/**: Sample configuration files
- **sample_work_items/**: Sample work item JSON
- **mock_responses/**: Mock API responses

## Conventions

- **Arrange-Act-Assert**: Use AAA pattern in tests
- **One Assert Per Test**: Focus tests on single behaviors
- **Descriptive Names**: Test names should explain what's being tested
- **Fast Units**: Unit tests should complete in <1s
- **Isolated**: Tests should not depend on each other
- **Deterministic**: Tests should produce same results every time
