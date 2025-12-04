---
context:
  purpose: "Ensures framework reliability by assuming failure and testing for it systematically"
  problem_solved: "Untested frameworks fail unpredictably in production. Without comprehensive testing organized by risk level, critical failures escape to users. Test categories (unit, integration, Azure) enable fast feedback during development while catching integration issues before deployment."
  keywords: [test, testing, pytest, coverage, fixture, tests, reliability, quality, validation]
  task_types: [testing, quality-assurance, debugging, validation]
  priority: medium
  max_tokens: 600
  children:
    - path: tests/integration/CLAUDE.md
      when: [module, feature]
    - path: tests/unit/CLAUDE.md
      when: [module, feature]
  dependencies: [core, config, agents, workflows, adapters]
---
# Tests

## Purpose

Embodies **Design Principle #1: Assume Failure** from VISION.md by systematically testing for all the ways the framework can fail.

The framework is designed to catch AI failures (skipped work, hallucinated completion, context overload). **But the framework itself can fail**:
- State manager fails to persist checkpoints → lost workflow progress
- Configuration validation misses invalid values → workflows crash mid-execution
- Agent rendering fails with wrong templates → agents unavailable
- Azure DevOps adapter uses wrong field names → work items corrupted

**Without comprehensive testing**, these framework failures escape to users. Users experience the very unreliability the framework is meant to prevent.

**With comprehensive testing**, framework failures are caught during development. Quality standards (80% coverage minimum) enforce reliability discipline.

## Test Strategy: Risk-Based Testing

Tests are organized by failure risk and execution speed:

### Unit Tests (tests/unit/)
**Risk**: Individual component logic failures
**Speed**: Fast (<1s each, ~50 tests run in 2-3 seconds)
**Coverage**: Pure functions, validation, mappers, state management

**Example Failures Caught**:
- Field mapper returns wrong Azure DevOps field name → work item fields not set
- Config loader accepts invalid enum value → runtime crash
- State manager overwrites checkpoint → progress lost

### Integration Tests (tests/integration/)
**Risk**: Component integration failures, system dependencies
**Speed**: Moderate (1-5s each, ~20 tests run in 30 seconds)
**Coverage**: CLI commands, file I/O, template rendering, end-to-end workflows

**Example Failures Caught**:
- CLI init creates malformed config.yaml → workflows can't start
- Agent render fails when template has syntax error → agents unavailable
- Workflow state file becomes corrupted → resume fails

### Azure DevOps Tests (tests/integration/ with @pytest.mark.azure)
**Risk**: External platform integration failures
**Speed**: Slow (5-30s each, requires Azure DevOps connection)
**Coverage**: Work item CRUD, sprint operations, field mappings

**Example Failures Caught**:
- Wrong iteration path format → work items don't appear in taskboard
- Custom field mapping incorrect → data loss
- Authentication expired → operations fail silently

## Test Organization by Failure Type

Tests map to specific failure modes the framework must prevent:

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
- **Descriptive Names**: Test names should explain what's being tested and what failure is being prevented
- **Fast Units**: Unit tests should complete in <1s
- **Isolated**: Tests should not depend on each other
- **Deterministic**: Tests should produce same results every time

## Design Principle: Assume Failure

Tests embody **Assume Failure** principle (VISION.md Design Principle #1):

**Assume framework components will fail:**
- State manager will corrupt checkpoints
- Config validation will miss invalid values
- Agent templates will have syntax errors
- Azure DevOps adapter will use wrong field names
- CLI commands will encounter missing dependencies

**Tests systematically verify these failures are caught:**

```python
# Test: State manager handles corrupted checkpoint
def test_load_corrupted_checkpoint():
    """Framework must not crash when checkpoint file corrupted."""
    with open(checkpoint_file, 'w') as f:
        f.write("{ invalid json !!")

    # Should raise clear error, not crash with JSON parse error
    with pytest.raises(CheckpointCorruptedError):
        WorkflowState.load(checkpoint_file)

# Test: Config validation catches invalid enum
def test_invalid_project_type():
    """Framework must reject invalid project types."""
    config = {"project": {"type": "invalid-type"}}

    # Should raise validation error, not proceed with invalid config
    with pytest.raises(ValidationError, match="Invalid project type"):
        load_config(config)
```

## Coverage as Reliability Metric

**Minimum 80% coverage** (enforced by quality_standards in config.yaml):
- Not arbitrary - 80% coverage catches ~90% of bugs in well-designed code
- Critical modules (core/, config/) target >90% coverage
- Integration tests add coverage that unit tests miss

**Coverage Reports Show Risk**:
- Red (uncovered): Code paths that could fail without detection
- Green (covered): Code paths with failure protection

**Coverage ≠ Quality** (tests can be bad), but **low coverage = high risk** (untested code fails unpredictably).

## Real Failure Scenarios Prevented by Tests

### Scenario 1: State Manager Checkpoint Overwrite
**Test**: `tests/unit/test_state_manager.py::test_checkpoint_preserves_previous_data`

**Without test**: State manager bug overwrites previous checkpoint data when saving new step. Sprint planning reaches Step 4, saves checkpoint, loses Step 1-3 data. Resume fails: "Step 1 data missing".

**With test**: Test verifies each checkpoint preserves previous data. Bug caught in CI, fixed before release.

### Scenario 2: Config Validation Misses Invalid Coverage Threshold
**Test**: `tests/unit/test_configuration.py::test_coverage_threshold_validation`

**Without test**: Validation accepts `test_coverage_min: 105` (>100). Workflows run with invalid config, crash when checking coverage.

**With test**: Test ensures validation rejects values >100. Invalid config caught at `trustable-ai validate`, never reaches workflows.

### Scenario 3: Azure DevOps Adapter Uses Wrong Iteration Path
**Test**: `tests/integration/test_azure_adapter.py::test_team_iteration_path`

**Without test**: Adapter uses project iteration path format instead of team format. Work items created but don't appear in taskboard. Mystery debugging.

**With test**: Test verifies adapter uses correct team iteration path format. Integration test catches issue before users encounter it.

## Related

- **VISION.md**: Design Principle #1 (Assume Failure), Quality Standards
- **config/CLAUDE.md**: QualityStandards configuration (test_coverage_min)
- **pytest.ini**: Test configuration and markers
- **conftest.py**: Shared test fixtures
