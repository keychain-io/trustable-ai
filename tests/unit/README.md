# unit

## Purpose

Fast unit tests for TAID framework components. These tests have no external dependencies and focus on testing individual modules, classes, and functions in isolation. All unit tests should complete in under 1 second.

## Key Components

- **test_agent_registry.py**: Agent template rendering and registry operations
- **test_workflow_registry.py**: Workflow template rendering and registry operations
- **test_configuration.py**: Configuration loading, validation, and schema tests
- **test_mappers.py**: Field and type mapping for platform adapters
- **__init__.py**: Module initialization

## Test Structure

### test_agent_registry.py
Tests for agent template system:
- List available agents
- Render agent templates with configuration
- Inject project context into templates
- Validate rendered agent output
- Agent enablement/disablement
- Slash command generation

### test_workflow_registry.py
Tests for workflow template system:
- List available workflows
- Render workflow templates with configuration
- Inject project context into templates
- Validate rendered workflow output
- Workflow state management

### test_configuration.py
Tests for configuration system:
- Load configuration from YAML
- Validate configuration against schema
- Environment variable expansion
- Default value handling
- Configuration saving
- Error handling for invalid configs
- Pydantic model validation

### test_mappers.py
Tests for platform adapter field/type mapping:
- Generic field name to Azure DevOps field mapping
- Generic work item type to Azure DevOps type mapping
- Custom field mapping from configuration
- Case sensitivity handling

## Running Unit Tests

```bash
# Run all unit tests
pytest tests/unit/

# Run all unit tests (using marker)
pytest -m unit

# Run specific test file
pytest tests/unit/test_configuration.py

# Run specific test
pytest tests/unit/test_configuration.py::test_load_config_success

# Run with verbose output
pytest tests/unit/ -v

# Run without coverage
pytest tests/unit/ --no-cov
```

## Test Markers

All unit tests should be marked:

```python
import pytest

@pytest.mark.unit
def test_something():
    """Test description."""
    assert True
```

## Writing Unit Tests

### Test Structure - Arrange-Act-Assert

```python
import pytest
from config import load_config

@pytest.mark.unit
def test_load_config_success(tmp_path):
    """Test successful configuration loading."""
    # Arrange: Set up test data
    config_path = tmp_path / ".claude" / "config.yaml"
    config_path.parent.mkdir()
    config_path.write_text("""
        project:
          name: "test-project"
          type: "web-application"
          tech_stack:
            languages: ["Python"]
        work_tracking:
          organization: "https://dev.azure.com/test"
          project: "TestProject"
    """)

    # Act: Execute the function being tested
    config = load_config(config_path)

    # Assert: Verify expected behavior
    assert config.project.name == "test-project"
    assert config.project.type == "web-application"
    assert "Python" in config.project.tech_stack["languages"]
```

### Testing with Mock Data

```python
import pytest
from agents import AgentRegistry
from config.schema import FrameworkConfig, ProjectConfig, WorkTrackingConfig

@pytest.mark.unit
def test_render_agent_with_context():
    """Test agent rendering with project context."""
    # Arrange: Create mock configuration
    config = FrameworkConfig(
        project=ProjectConfig(
            name="test",
            type="web-application",
            tech_stack={"languages": ["Python"], "frameworks": ["FastAPI"]}
        ),
        work_tracking=WorkTrackingConfig(
            organization="https://dev.azure.com/test",
            project="Test"
        )
    )

    # Act: Render agent
    registry = AgentRegistry(config)
    rendered = registry.render_agent("business-analyst")

    # Assert: Verify context injection
    assert "test" in rendered
    assert "Python" in rendered
    assert "FastAPI" in rendered
```

### Testing Error Cases

```python
import pytest
from config import load_config
from pathlib import Path

@pytest.mark.unit
def test_load_config_missing_file():
    """Test error handling for missing config file."""
    # Act & Assert: Verify exception is raised
    with pytest.raises(FileNotFoundError):
        load_config(Path("nonexistent/config.yaml"))

@pytest.mark.unit
def test_load_config_invalid_yaml(tmp_path):
    """Test error handling for invalid YAML."""
    # Arrange: Create invalid YAML
    config_path = tmp_path / "config.yaml"
    config_path.write_text("invalid: yaml: : :")

    # Act & Assert: Verify exception is raised
    with pytest.raises(Exception):  # yaml.YAMLError or similar
        load_config(config_path)
```

### Testing Schema Validation

```python
import pytest
from pydantic import ValidationError
from config.schema import ProjectConfig

@pytest.mark.unit
def test_project_config_validation():
    """Test project configuration validation."""
    # Valid configuration
    config = ProjectConfig(
        name="test",
        type="web-application",
        tech_stack={"languages": ["Python"]}
    )
    assert config.name == "test"

    # Invalid project type
    with pytest.raises(ValidationError):
        ProjectConfig(
            name="test",
            type="invalid-type",  # Not in valid_types
            tech_stack={"languages": ["Python"]}
        )
```

### Testing Template Rendering

```python
import pytest
from agents import AgentRegistry

@pytest.mark.unit
def test_list_agents():
    """Test listing available agents."""
    # Arrange: Create registry with minimal config
    from config.schema import FrameworkConfig, ProjectConfig, WorkTrackingConfig

    config = FrameworkConfig(
        project=ProjectConfig(
            name="test",
            type="web-application",
            tech_stack={"languages": ["Python"]}
        ),
        work_tracking=WorkTrackingConfig(
            organization="https://dev.azure.com/test",
            project="Test"
        )
    )

    # Act: List agents
    registry = AgentRegistry(config)
    agents = registry.list_agents()

    # Assert: Verify expected agents
    assert "business-analyst" in agents
    assert "project-architect" in agents
    assert "senior-engineer" in agents
    assert len(agents) > 0
```

## Common Fixtures

Unit tests use these common fixtures from `conftest.py`:

### sample_config
Provides a sample FrameworkConfig:
```python
@pytest.fixture
def sample_config():
    """Provide sample configuration for testing."""
    return FrameworkConfig(
        project=ProjectConfig(
            name="test-project",
            type="web-application",
            tech_stack={"languages": ["Python"]}
        ),
        work_tracking=WorkTrackingConfig(
            organization="https://dev.azure.com/test",
            project="Test"
        )
    )
```

### tmp_config_file
Creates a temporary config file:
```python
@pytest.fixture
def tmp_config_file(tmp_path):
    """Create temporary config file."""
    config_dir = tmp_path / ".claude"
    config_dir.mkdir()
    config_file = config_dir / "config.yaml"
    return config_file
```

## Conventions

### Test Naming
- **Files**: `test_<module>.py`
- **Functions**: `test_<what_is_tested>()`
- **Classes**: `Test<Module>` for grouping

### Test Organization
- **One Test Per Behavior**: Each test should verify one specific behavior
- **Fast Execution**: All unit tests must complete in <1s
- **No External Deps**: No network, databases, file system (except tmp_path)
- **Deterministic**: Tests must produce same results every time
- **Isolated**: Tests should not depend on each other

### Assertions
- **Specific Assertions**: Use specific assertions (assert x == 5, not assert x)
- **Clear Messages**: Provide clear assertion messages when helpful
- **Multiple Assertions**: OK if testing same logical unit

### Mocking
Unit tests should mock external dependencies:
```python
from unittest.mock import Mock, patch

@pytest.mark.unit
@patch('adapters.azure_devops.cli_wrapper.subprocess.run')
def test_with_mock(mock_run):
    """Test with mocked subprocess."""
    mock_run.return_value = Mock(returncode=0, stdout='{"id": 123}')
    # Test code here
```

## Test Coverage

Unit tests should provide high coverage:
- **Target**: >90% coverage for core modules
- **Minimum**: 80% coverage overall
- **Focus Areas**:
  - `config/` - Configuration loading and validation
  - `core/` - State management, profiling, context loading
  - `agents/registry.py` - Agent rendering
  - `workflows/registry.py` - Workflow rendering

## Debugging Unit Tests

```bash
# Run with verbose output
pytest tests/unit/ -v

# Run with print statements visible
pytest tests/unit/ -s

# Run specific test with debugging
pytest tests/unit/test_config.py::test_load_config -v -s

# Drop into debugger on failure
pytest tests/unit/ --pdb

# Run last failed tests
pytest tests/unit/ --lf

# Run tests matching keyword
pytest tests/unit/ -k "config"
```

## Performance

Unit tests should be fast:
- **Individual Test**: <100ms
- **Full Suite**: <10s
- **Use tmp_path**: Avoid creating files in actual filesystem
- **Mock I/O**: Mock file/network operations
- **Minimal Setup**: Keep fixtures lightweight

## Common Patterns

### Testing Pydantic Models
```python
@pytest.mark.unit
def test_pydantic_model():
    """Test Pydantic model validation."""
    from config.schema import QualityStandards

    # Valid data
    standards = QualityStandards(
        test_coverage_min=80,
        critical_vulnerabilities_max=0
    )
    assert standards.test_coverage_min == 80

    # Invalid data
    with pytest.raises(ValidationError):
        QualityStandards(test_coverage_min=150)  # Must be <= 100
```

### Testing Template Rendering
```python
@pytest.mark.unit
def test_template_rendering(sample_config):
    """Test Jinja2 template rendering."""
    from agents import AgentRegistry

    registry = AgentRegistry(sample_config)
    rendered = registry.render_agent("business-analyst")

    # Verify context injection
    assert sample_config.project.name in rendered
    assert "Python" in rendered
```

### Parametrized Tests
```python
@pytest.mark.unit
@pytest.mark.parametrize("project_type,expected", [
    ("web-application", True),
    ("api", True),
    ("invalid-type", False),
])
def test_validate_project_type(project_type, expected):
    """Test project type validation."""
    from config.schema import ProjectConfig

    if expected:
        config = ProjectConfig(
            name="test",
            type=project_type,
            tech_stack={"languages": ["Python"]}
        )
        assert config.type == project_type
    else:
        with pytest.raises(ValidationError):
            ProjectConfig(
                name="test",
                type=project_type,
                tech_stack={"languages": ["Python"]}
            )
```
