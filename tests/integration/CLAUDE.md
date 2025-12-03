# integration

## Purpose

Integration tests for TAID framework. These tests verify end-to-end functionality including CLI commands, external service integration, and complete workflows. May require external dependencies like Azure DevOps credentials.

## Key Components

- **test_cli_init.py**: Test `trustable-ai init` command for project initialization
- **test_cli_agent.py**: Test agent management CLI commands (list, enable, render)
- **test_cli_workflow.py**: Test workflow management CLI commands
- **test_cli_validate.py**: Test configuration validation command
- **test_context_generation.py**: Test context generation workflows
- **__init__.py**: Module initialization

## Test Structure

### CLI Command Tests

All CLI tests use Click's `CliRunner` for invoking commands:

```python
from click.testing import CliRunner
from cli.main import cli

@pytest.mark.integration
@pytest.mark.cli
def test_init_command(tmp_path, monkeypatch):
    """Test trustable-ai init command."""
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()

    result = runner.invoke(cli, ["init"], input="test\nweb-application\n")

    assert result.exit_code == 0
    assert (tmp_path / ".claude" / "config.yaml").exists()
```

### Test Categories

**test_cli_init.py**: Project initialization
- Create `.claude/` directory structure
- Generate default `config.yaml`
- Interactive prompts for project details
- Error handling for existing initialization

**test_cli_agent.py**: Agent management
- List available agents
- Enable/disable agents in configuration
- Render agent templates
- Render all agents to `.claude/agents/`
- Slash command generation

**test_cli_workflow.py**: Workflow management
- List available workflows
- Render workflow templates
- Render all workflows to `.claude/commands/`
- Workflow state management

**test_cli_validate.py**: Configuration validation
- Valid configuration passes validation
- Invalid configuration reports errors
- Missing required fields detected
- Platform-specific validation (Azure DevOps, etc.)

**test_context_generation.py**: Context generation
- Hierarchical CLAUDE.md loading
- Keyword-based context selection
- Token budget enforcement
- Context pruning and optimization

## Running Integration Tests

```bash
# Run all integration tests
pytest tests/integration/

# Run specific integration test file
pytest tests/integration/test_cli_init.py

# Run with markers
pytest -m integration
pytest -m cli

# Skip Azure DevOps tests (require credentials)
pytest -m "integration and not azure"
```

## Test Markers

Integration tests use these markers:

```python
@pytest.mark.integration   # All integration tests
@pytest.mark.cli           # CLI command tests
@pytest.mark.azure         # Requires Azure DevOps credentials
@pytest.mark.slow          # Long-running tests
```

## Test Fixtures

Common fixtures for integration tests:

### tmp_project
Creates a temporary project directory with `.claude/` structure:
```python
@pytest.fixture
def tmp_project(tmp_path):
    """Create temporary project with TAID initialization."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    (project_dir / ".claude").mkdir()
    return project_dir
```

### cli_runner
Provides Click CliRunner instance:
```python
@pytest.fixture
def cli_runner():
    """Provide Click CLI runner."""
    return CliRunner()
```

### mock_azure_config
Mock Azure DevOps configuration:
```python
@pytest.fixture
def mock_azure_config(tmp_path):
    """Provide mock Azure DevOps configuration."""
    config_path = tmp_path / ".claude" / "config.yaml"
    config_path.parent.mkdir()
    config_path.write_text("""
        work_tracking:
          platform: "azure-devops"
          organization: "https://dev.azure.com/test"
          project: "TestProject"
    """)
    return config_path
```

## Writing Integration Tests

### Testing CLI Commands

```python
import pytest
from click.testing import CliRunner
from cli.main import cli

@pytest.mark.integration
@pytest.mark.cli
def test_agent_list_command():
    """Test agent list command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["agent", "list"])

    assert result.exit_code == 0
    assert "business-analyst" in result.output
    assert "project-architect" in result.output
```

### Testing with Temporary Files

```python
@pytest.mark.integration
def test_agent_render_to_file(tmp_path):
    """Test rendering agent to file."""
    output_file = tmp_path / "business-analyst.md"
    runner = CliRunner()

    result = runner.invoke(cli, [
        "agent", "render", "business-analyst",
        "-o", str(output_file)
    ])

    assert result.exit_code == 0
    assert output_file.exists()
    content = output_file.read_text()
    assert "Business Analyst" in content
```

### Testing Interactive Commands

```python
@pytest.mark.integration
@pytest.mark.cli
def test_init_interactive(tmp_path, monkeypatch):
    """Test interactive initialization."""
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()

    # Provide input for prompts
    result = runner.invoke(cli, ["init"], input=(
        "my-project\n"           # Project name
        "web-application\n"      # Project type
        "Python,TypeScript\n"    # Languages
        "FastAPI,React\n"        # Frameworks
    ))

    assert result.exit_code == 0
    config_file = tmp_path / ".claude" / "config.yaml"
    assert config_file.exists()

    # Verify configuration
    import yaml
    config = yaml.safe_load(config_file.read_text())
    assert config["project"]["name"] == "my-project"
```

## Azure DevOps Integration Tests

Tests requiring Azure DevOps credentials:

```python
import pytest

@pytest.mark.integration
@pytest.mark.azure
def test_azure_work_item_creation(azure_config):
    """Test work item creation in Azure DevOps."""
    # Skip if Azure credentials not available
    if not has_azure_credentials():
        pytest.skip("Azure DevOps credentials not configured")

    from adapters.azure_devops import create_work_item

    work_item = create_work_item(
        work_item_type="Task",
        title="Integration Test Work Item",
        description="Created by integration test"
    )

    assert work_item["id"] > 0
    assert work_item["fields"]["System.Title"] == "Integration Test Work Item"
```

## Test Data

Integration tests use fixtures from `tests/fixtures/`:
- **sample_configs/**: Valid and invalid configuration files
- **sample_templates/**: Agent and workflow templates for testing
- **expected_outputs/**: Expected CLI output for comparison

## Conventions

- **Test Isolation**: Each test should clean up after itself
- **Temporary Files**: Use `tmp_path` fixture for file operations
- **Mock External Services**: Mock Azure DevOps unless explicitly testing integration
- **Error Cases**: Test both success and failure scenarios
- **CLI Testing**: Use `CliRunner` with `mix_stderr=False` for cleaner output
- **Markers**: Always mark tests with appropriate markers

## Debugging Integration Tests

```bash
# Run with verbose output
pytest tests/integration/ -v

# Run with output capture disabled (see print statements)
pytest tests/integration/ -s

# Run specific test with debugging
pytest tests/integration/test_cli_init.py::test_init_command -v -s

# Skip slow tests
pytest tests/integration/ -m "not slow"
```

## Common Issues

### Issue: Tests fail due to missing config
**Solution**: Use `tmp_path` fixture and create config files in tests

### Issue: Azure tests fail in CI
**Solution**: Mark Azure tests with `@pytest.mark.azure` and skip in CI

### Issue: CLI tests show unexpected output
**Solution**: Check Click's `mix_stderr=False` and use `result.output` carefully

### Issue: File permission errors
**Solution**: Use `tmp_path` fixture which handles cleanup automatically
