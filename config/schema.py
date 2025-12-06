"""
Configuration schema for Trustable AI.

Defines Pydantic models for type-safe configuration validation.
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, field_validator
from pathlib import Path


class ProjectConfig(BaseModel):
    """Project-specific configuration."""

    name: str = Field(..., description="Project name")
    type: str = Field(
        ...,
        description="Project type (web-application, api, mobile-app, infrastructure, library, etc.)"
    )
    tech_stack: Dict[str, List[str]] = Field(
        ...,
        description="Technology stack grouped by category (languages, frameworks, platforms, databases, etc.)"
    )
    source_directory: str = Field(
        default="src",
        description="Primary source code directory"
    )
    test_directory: str = Field(
        default="tests",
        description="Test directory"
    )

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        """Validate project type."""
        valid_types = {
            "web-application", "api", "mobile-app", "desktop-app",
            "infrastructure", "library", "cli-tool", "data-pipeline",
            "microservice", "monolith"
        }
        if v not in valid_types:
            raise ValueError(f"Project type must be one of: {', '.join(valid_types)}")
        return v


class WorkTrackingConfig(BaseModel):
    """Work tracking platform configuration."""

    platform: str = Field(
        default="file-based",
        description="Work tracking platform (azure-devops, jira, github-projects, file-based)"
    )
    organization: Optional[str] = Field(
        default=None,
        description="Organization URL or name (required for cloud platforms)"
    )
    project: Optional[str] = Field(
        default=None,
        description="Project name"
    )
    credentials_source: str = Field(
        default="cli",
        description="Credentials source (cli, env:VAR_NAME, file:path)"
    )

    # File-based storage configuration
    work_items_directory: str = Field(
        default=".claude/work-items",
        description="Directory for file-based work items (file-based platform only)"
    )

    # Work item type mappings
    work_item_types: Dict[str, str] = Field(
        default_factory=lambda: {
            "epic": "Epic",
            "feature": "Feature",
            "story": "User Story",
            "task": "Task",
            "bug": "Bug",
        },
        description="Mapping from generic types to platform-specific types"
    )

    # Custom field mappings
    custom_fields: Dict[str, str] = Field(
        default_factory=dict,
        description="Mapping from generic field names to platform-specific field names"
    )

    # Sprint/iteration configuration
    iteration_format: str = Field(
        default="{project}\\\\{sprint}",
        description="Format for iteration paths"
    )
    sprint_naming: str = Field(
        default="Sprint {number}",
        description="Sprint naming pattern"
    )

    @field_validator("platform")
    @classmethod
    def validate_platform(cls, v: str) -> str:
        """Validate work tracking platform."""
        valid_platforms = {"azure-devops", "jira", "github-projects", "file-based"}
        if v not in valid_platforms:
            raise ValueError(f"Platform must be one of: {', '.join(valid_platforms)}")
        return v


class QualityStandards(BaseModel):
    """Quality and security standards configuration."""

    # Test coverage
    test_coverage_min: int = Field(
        default=80,
        ge=0,
        le=100,
        description="Minimum test coverage percentage"
    )

    # Vulnerability thresholds
    critical_vulnerabilities_max: int = Field(
        default=0,
        ge=0,
        description="Maximum allowed critical vulnerabilities"
    )
    high_vulnerabilities_max: int = Field(
        default=0,
        ge=0,
        description="Maximum allowed high vulnerabilities"
    )
    medium_vulnerabilities_max: int = Field(
        default=5,
        ge=0,
        description="Maximum allowed medium vulnerabilities"
    )

    # Code quality
    code_complexity_max: int = Field(
        default=10,
        ge=1,
        description="Maximum cyclomatic complexity"
    )
    duplicate_code_max: float = Field(
        default=3.0,
        ge=0.0,
        le=100.0,
        description="Maximum duplicate code percentage"
    )

    # Performance
    build_time_max_minutes: int = Field(
        default=10,
        ge=1,
        description="Maximum build time in minutes"
    )
    test_time_max_minutes: int = Field(
        default=5,
        ge=1,
        description="Maximum test execution time in minutes"
    )


class AgentConfig(BaseModel):
    """Agent configuration."""

    # Model selection for different agent types
    models: Dict[str, str] = Field(
        default_factory=lambda: {
            "architect": "claude-opus-4",
            "engineer": "claude-sonnet-4.5",
            "analyst": "claude-sonnet-4.5",
            "security": "claude-sonnet-4.5",
            "scrum-master": "claude-sonnet-4.5",
            "qa": "claude-sonnet-4.5",
            "devops": "claude-sonnet-4.5",
            "ux": "claude-sonnet-4.5",
            "writer": "claude-sonnet-4.5",
            "reviewer": "claude-sonnet-4.5",
            "release": "claude-sonnet-4.5",
            "performance": "claude-sonnet-4.5",
        },
        description="Claude model selection for each agent type"
    )

    # Enabled agents (default core team - 7 consolidated agents)
    enabled_agents: List[str] = Field(
        default_factory=lambda: [
            "business-analyst",
            "architect",
            "senior-engineer",
            "engineer",
            "tester",
            "security-specialist",
            "scrum-master",
        ],
        description="List of enabled agents"
    )

    # All available agents for reference
    available_agents: List[str] = Field(
        default_factory=lambda: [
            # Core agents (7)
            "business-analyst",
            "architect",
            "senior-engineer",
            "engineer",
            "tester",
            "security-specialist",
            "scrum-master",
            # Specialist agents
            "release-manager",
            "code-reviewer",
            "documentation-specialist",
            "technical-writer",
            "ux-designer",
        ],
        description="All available agent templates"
    )

    # Agent-specific configurations
    agent_specific: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Agent-specific configuration overrides"
    )


class WorkflowConfig(BaseModel):
    """Workflow execution configuration."""

    state_directory: str = Field(
        default=".claude/workflow-state",
        description="Directory for workflow state files"
    )
    profiling_directory: str = Field(
        default=".claude/profiling",
        description="Directory for profiling reports"
    )
    checkpoint_enabled: bool = Field(
        default=True,
        description="Enable workflow checkpointing"
    )
    verification_enabled: bool = Field(
        default=True,
        description="Enable verification of operations"
    )
    max_retries: int = Field(
        default=3,
        ge=0,
        description="Maximum retries for failed operations"
    )
    timeout_minutes: int = Field(
        default=30,
        ge=1,
        description="Workflow timeout in minutes"
    )


class DeploymentConfig(BaseModel):
    """Deployment configuration."""

    environments: List[str] = Field(
        default_factory=lambda: ["dev", "uat", "prod"],
        description="Available deployment environments"
    )
    default_environment: str = Field(
        default="dev",
        description="Default deployment environment"
    )
    deployment_tasks_enabled: bool = Field(
        default=True,
        description="Auto-create deployment tasks"
    )
    deployment_task_types: List[str] = Field(
        default_factory=lambda: [
            "local_docker",
            "dev_deployment",
            "uat_deployment",
            "terraform_infrastructure",
        ],
        description="Enabled deployment task types"
    )


class FrameworkConfig(BaseModel):
    """Complete framework configuration."""

    project: ProjectConfig
    work_tracking: WorkTrackingConfig
    quality_standards: QualityStandards = Field(default_factory=QualityStandards)
    agent_config: AgentConfig = Field(default_factory=AgentConfig)
    workflow_config: WorkflowConfig = Field(default_factory=WorkflowConfig)
    deployment_config: DeploymentConfig = Field(default_factory=DeploymentConfig)

    # Additional custom configuration
    custom: Dict[str, Any] = Field(
        default_factory=dict,
        description="Custom configuration values"
    )

    def get_iteration_path(self, sprint_name: str) -> str:
        """
        Get the iteration path for a sprint.

        Args:
            sprint_name: Sprint name (e.g., "Sprint 10")

        Returns:
            Formatted iteration path
        """
        return self.work_tracking.iteration_format.format(
            project=self.work_tracking.project,
            sprint=sprint_name
        )

    def get_sprint_name(self, number: int) -> str:
        """
        Get the sprint name for a sprint number.

        Args:
            number: Sprint number

        Returns:
            Formatted sprint name
        """
        return self.work_tracking.sprint_naming.format(number=number)

    def get_custom_field(self, field_name: str) -> Optional[str]:
        """
        Get a custom field name mapping.

        Args:
            field_name: Generic field name

        Returns:
            Platform-specific field name or None
        """
        return self.work_tracking.custom_fields.get(field_name)

    def get_work_item_type(self, generic_type: str) -> Optional[str]:
        """
        Get a work item type mapping.

        Args:
            generic_type: Generic work item type

        Returns:
            Platform-specific work item type or None
        """
        return self.work_tracking.work_item_types.get(generic_type)

    def is_agent_enabled(self, agent_name: str) -> bool:
        """
        Check if an agent is enabled.

        Args:
            agent_name: Agent name

        Returns:
            True if enabled
        """
        return agent_name in self.agent_config.enabled_agents

    def get_agent_model(self, agent_type: str) -> str:
        """
        Get the model for an agent type.

        Args:
            agent_type: Agent type (e.g., "architect", "engineer")

        Returns:
            Model name (defaults to sonnet if not configured)
        """
        return self.agent_config.models.get(agent_type, "claude-sonnet-4.5")

    class Config:
        """Pydantic model configuration."""
        extra = "allow"  # Allow additional fields
        validate_assignment = True  # Validate on assignment
