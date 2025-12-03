"""
Pytest configuration and fixtures for Trustable AI Workbench tests.

Provides reusable fixtures for testing components.
"""
import pytest
from pathlib import Path
import tempfile
import shutil
from typing import Dict, Any

from config.schema import (
    FrameworkConfig,
    ProjectConfig,
    WorkTrackingConfig,
    QualityStandards,
    AgentConfig,
    WorkflowConfig,
    DeploymentConfig,
)


@pytest.fixture
def sample_project_config() -> ProjectConfig:
    """Sample project configuration for testing."""
    return ProjectConfig(
        name="Test Project",
        type="web-application",
        tech_stack={
            "languages": ["Python", "TypeScript"],
            "frameworks": ["FastAPI", "React"],
            "platforms": ["Azure", "Docker"],
            "databases": ["PostgreSQL", "Redis"],
        },
        source_directory="src",
        test_directory="tests",
    )


@pytest.fixture
def sample_work_tracking_config() -> WorkTrackingConfig:
    """Sample work tracking configuration for testing."""
    return WorkTrackingConfig(
        platform="azure-devops",
        organization="https://dev.azure.com/test-org",
        project="Test Project",
        credentials_source="cli",
        work_item_types={
            "epic": "Epic",
            "feature": "Feature",
            "story": "User Story",
            "task": "Task",
            "bug": "Bug",
        },
        custom_fields={
            "business_value": "Custom.BusinessValueScore",
            "technical_risk": "Custom.TechnicalRisk",
            "roi_projection": "Custom.ROI",
        },
        iteration_format="{project}\\\\{sprint}",
        sprint_naming="Sprint {number}",
    )


@pytest.fixture
def sample_quality_standards() -> QualityStandards:
    """Sample quality standards for testing."""
    return QualityStandards(
        test_coverage_min=80,
        critical_vulnerabilities_max=0,
        high_vulnerabilities_max=0,
        medium_vulnerabilities_max=5,
        code_complexity_max=10,
        duplicate_code_max=3.0,
        build_time_max_minutes=10,
        test_time_max_minutes=5,
    )


@pytest.fixture
def sample_agent_config() -> AgentConfig:
    """Sample agent configuration for testing."""
    return AgentConfig(
        models={
            "architect": "claude-opus-4",
            "engineer": "claude-sonnet-4.5",
            "analyst": "claude-sonnet-4.5",
            "security": "claude-sonnet-4.5",
            "scrum-master": "claude-haiku-4",
        },
        enabled_agents=[
            "business-analyst",
            "senior-engineer",
            "scrum-master",
            "project-architect",
            "security-specialist",
        ],
    )


@pytest.fixture
def sample_workflow_config() -> WorkflowConfig:
    """Sample workflow configuration for testing."""
    return WorkflowConfig(
        state_directory=".claude/workflow-state",
        profiling_directory=".claude/profiling",
        checkpoint_enabled=True,
        verification_enabled=True,
        max_retries=3,
        timeout_minutes=30,
    )


@pytest.fixture
def sample_deployment_config() -> DeploymentConfig:
    """Sample deployment configuration for testing."""
    return DeploymentConfig(
        environments=["dev", "uat", "prod"],
        default_environment="dev",
        deployment_tasks_enabled=True,
        deployment_task_types=[
            "local_docker",
            "dev_deployment",
            "uat_deployment",
        ],
    )


@pytest.fixture
def sample_framework_config(
    sample_project_config,
    sample_work_tracking_config,
    sample_quality_standards,
    sample_agent_config,
    sample_workflow_config,
    sample_deployment_config,
) -> FrameworkConfig:
    """Complete sample framework configuration for testing."""
    return FrameworkConfig(
        project=sample_project_config,
        work_tracking=sample_work_tracking_config,
        quality_standards=sample_quality_standards,
        agent_config=sample_agent_config,
        workflow_config=sample_workflow_config,
        deployment_config=sample_deployment_config,
    )


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    # Cleanup
    if temp_path.exists():
        shutil.rmtree(temp_path)


@pytest.fixture
def mock_claude_dir(temp_dir):
    """Create a mock .claude directory structure for testing."""
    claude_dir = temp_dir / ".claude"
    claude_dir.mkdir()

    # Create subdirectories
    (claude_dir / "agents").mkdir()
    (claude_dir / "commands").mkdir()
    (claude_dir / "workflow-state").mkdir()
    (claude_dir / "profiling").mkdir()
    (claude_dir / "learnings").mkdir()

    return claude_dir


@pytest.fixture
def sample_config_yaml() -> str:
    """Sample configuration YAML for testing."""
    return """
project:
  name: "Test Project"
  type: "web-application"
  tech_stack:
    languages:
      - Python
      - TypeScript
    frameworks:
      - FastAPI
      - React
    platforms:
      - Azure
      - Docker

work_tracking:
  platform: "azure-devops"
  organization: "https://dev.azure.com/test-org"
  project: "Test Project"
  credentials_source: "cli"
  work_item_types:
    epic: "Epic"
    feature: "Feature"
    story: "User Story"
    task: "Task"
    bug: "Bug"
  custom_fields:
    business_value: "Custom.BusinessValueScore"
    technical_risk: "Custom.TechnicalRisk"
  iteration_format: "{project}\\\\{sprint}"
  sprint_naming: "Sprint {number}"

quality_standards:
  test_coverage_min: 80
  critical_vulnerabilities_max: 0
  high_vulnerabilities_max: 0

agent_config:
  models:
    architect: "claude-opus-4"
    engineer: "claude-sonnet-4.5"
    analyst: "claude-sonnet-4.5"
  enabled_agents:
    - business-analyst
    - senior-engineer
    - scrum-master
"""


@pytest.fixture
def config_file(temp_dir, sample_config_yaml):
    """Create a temporary config file for testing."""
    config_path = temp_dir / ".claude" / "config.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(sample_config_yaml)
    return config_path


@pytest.fixture
def minimal_framework_config() -> FrameworkConfig:
    """Minimal framework configuration for testing."""
    return FrameworkConfig(
        project=ProjectConfig(
            name="Minimal Test",
            type="api",
            tech_stack={"languages": ["Python"]},
        ),
        work_tracking=WorkTrackingConfig(
            organization="https://dev.azure.com/test",
            project="Test",
        ),
    )


# Marker helpers

def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test (fast, isolated)"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "azure: mark test as requiring Azure DevOps"
    )
    config.addinivalue_line(
        "markers", "cli: mark test as a CLI test"
    )
