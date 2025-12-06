"""
Integration tests for workflow adapter pattern usage.

Tests that workflows use the adapter pattern correctly for work tracking
instead of hardcoded Azure DevOps CLI commands. This ensures workflows
work with both Azure DevOps AND file-based adapters.

Addresses ticket #1018.
"""
import pytest
from pathlib import Path
from workflows.registry import WorkflowRegistry
from config.loader import load_config


@pytest.mark.integration
class TestWorkflowAdapterPatternUsage:
    """Test suite verifying workflows use adapter pattern."""

    @pytest.fixture
    def azure_config_yaml(self):
        """Sample configuration with Azure DevOps adapter."""
        return """
project:
  name: "Test Project"
  type: "web-application"
  tech_stack:
    languages: ["Python"]
    frameworks: []
    platforms: []

work_tracking:
  platform: "azure-devops"
  organization: "https://dev.azure.com/testorg"
  project: "TestProject"
  credentials_source: "cli"

  work_item_types:
    epic: "Epic"
    feature: "Feature"
    task: "Task"
    bug: "Bug"

  custom_fields:
    story_points: "Microsoft.VSTS.Scheduling.StoryPoints"
    business_value: "Microsoft.VSTS.Common.BusinessValue"

quality_standards:
  test_coverage_min: 80
  critical_vulnerabilities_max: 0
  high_vulnerabilities_max: 0
  code_complexity_max: 10

agent_config:
  models:
    architect: "claude-opus-4"
    engineer: "claude-sonnet-4.5"
  enabled_agents:
    - business-analyst
    - senior-engineer
"""

    @pytest.fixture
    def filebased_config_yaml(self):
        """Sample configuration with file-based adapter."""
        return """
project:
  name: "Test Project"
  type: "web-application"
  tech_stack:
    languages: ["Python"]

work_tracking:
  platform: "file-based"
  work_items_directory: ".claude/work-items"

  work_item_types:
    epic: "Epic"
    feature: "Feature"
    task: "Task"
    bug: "Bug"

quality_standards:
  test_coverage_min: 80
  critical_vulnerabilities_max: 0
  high_vulnerabilities_max: 0
  code_complexity_max: 10

agent_config:
  models:
    architect: "claude-opus-4"
    engineer: "claude-sonnet-4.5"
  enabled_agents:
    - business-analyst
    - senior-engineer
"""

    def test_epic_breakdown_uses_adapter_initialization(self, tmp_path, azure_config_yaml):
        """Test epic-breakdown workflow initializes adapter."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml)

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("epic-breakdown")

        # Should import and initialize adapter
        assert "from work_tracking import get_adapter" in rendered
        assert "adapter = get_adapter()" in rendered
        assert 'print(f"📋 Work Tracking: {adapter.platform}")' in rendered

    def test_epic_breakdown_uses_adapter_create_work_item(self, tmp_path, azure_config_yaml):
        """Test epic-breakdown uses adapter.create_work_item()."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml)

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("epic-breakdown")

        # Should use adapter pattern, not hardcoded az boards
        assert "adapter.create_work_item(" in rendered
        assert "adapter.link_work_items(" in rendered
        assert "az boards work-item create" not in rendered
        assert "az boards work-item link" not in rendered

    def test_sprint_planning_uses_adapter_query_work_items(self, tmp_path, azure_config_yaml):
        """Test sprint-planning uses adapter.query_work_items()."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml)

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        # Should use adapter for querying and creating
        assert "adapter.query_work_items(" in rendered
        assert "adapter.create_work_item(" in rendered
        assert "az boards work-item create" not in rendered
        assert "az boards query" not in rendered

    def test_sprint_execution_uses_adapter_query(self, tmp_path, azure_config_yaml):
        """Test sprint-execution uses adapter to query sprint items."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml)

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-execution")

        # Should use adapter, not manual file loading
        assert "from work_tracking import get_adapter" in rendered
        assert "adapter.query_work_items(" in rendered
        # Should NOT manually read YAML files
        assert "work_items_dir = Path(\".claude/work-items\")" not in rendered
        assert "yaml.safe_load" not in rendered

    def test_feature_implementation_uses_adapter_get_work_item(self, tmp_path, azure_config_yaml):
        """Test feature-implementation uses adapter to load work item."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml)

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("feature-implementation")

        # Should use adapter to load and update work items
        assert "from work_tracking import get_adapter" in rendered
        assert "adapter.get_work_item(" in rendered
        assert "adapter.update_work_item(" in rendered

    def test_workflows_work_with_filebased_adapter(self, tmp_path, filebased_config_yaml):
        """Test workflows render correctly with file-based adapter config."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(filebased_config_yaml)

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        # All refactored workflows should render without Azure-specific code
        for workflow_name in ["epic-breakdown", "sprint-planning", "sprint-execution", "feature-implementation"]:
            rendered = registry.render_workflow(workflow_name)

            # Should use generic adapter pattern
            assert "adapter = get_adapter()" in rendered

            # Should NOT have Azure DevOps hardcoded commands
            assert "az boards" not in rendered
            assert "--org" not in rendered  # Azure CLI flag
            assert "--project" not in rendered  # Azure CLI flag

    def test_all_refactored_workflows_use_adapter_pattern(self, tmp_path, azure_config_yaml):
        """Test that all 4 refactored workflows use adapter pattern consistently."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml)

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        refactored_workflows = [
            "epic-breakdown",
            "sprint-planning",
            "sprint-execution",
            "feature-implementation"
        ]

        for workflow_name in refactored_workflows:
            rendered = registry.render_workflow(workflow_name)

            # All should initialize adapter
            assert "from work_tracking import get_adapter" in rendered, \
                f"{workflow_name} missing adapter import"
            assert "adapter = get_adapter()" in rendered, \
                f"{workflow_name} missing adapter initialization"

            # None should use hardcoded Azure CLI commands
            assert "az boards work-item create" not in rendered, \
                f"{workflow_name} still using hardcoded az boards create"
            assert "az boards work-item update" not in rendered, \
                f"{workflow_name} still using hardcoded az boards update"
            assert "az boards work-item query" not in rendered, \
                f"{workflow_name} still using hardcoded az boards query"

    def test_workflows_inject_platform_specific_fields(self, tmp_path, azure_config_yaml):
        """Test workflows properly inject platform-specific field names."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml)

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        # Epic breakdown should use injected field names
        rendered = registry.render_workflow("epic-breakdown")

        # Should have Jinja2 template variables for custom fields
        # These get rendered as actual field names (e.g., Microsoft.VSTS.Scheduling.StoryPoints)
        assert "Microsoft.VSTS.Scheduling.StoryPoints" in rendered or \
               "'story_points'" in rendered.lower(), \
               "epic-breakdown should reference story_points field"


@pytest.mark.integration
class TestWorkflowAdapterErrorHandling:
    """Test suite for adapter error handling in workflows."""

    def test_workflows_handle_adapter_connection_failure(self, tmp_path, sample_config_yaml):
        """Test workflows have error handling for adapter failures."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(sample_config_yaml)

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        # Check that workflows have try/except blocks for adapter operations
        for workflow_name in ["epic-breakdown", "sprint-planning", "feature-implementation"]:
            rendered = registry.render_workflow(workflow_name)

            # Should have exception handling
            assert "try:" in rendered and "except Exception as e:" in rendered, \
                f"{workflow_name} missing error handling"

            # Should print user-friendly error messages
            assert "Failed to" in rendered or "❌" in rendered, \
                f"{workflow_name} missing user-friendly error messages"
