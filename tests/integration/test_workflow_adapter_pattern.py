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


@pytest.mark.integration
class TestBug1083WorkflowsUseAdapterNotAzBoards:
    """
    Test suite for Bug #1083 - Workflows use adapter pattern instead of direct az boards commands.

    Verifies that daily-standup, backlog-grooming, and sprint-retrospective workflows:
    1. Do NOT contain direct az boards CLI commands
    2. Do NOT have platform-specific conditional logic
    3. DO use the unified work tracking adapter for all operations
    4. Work consistently across all platforms (azure-devops, file-based, etc.)
    """

    @pytest.fixture
    def azure_config_yaml(self):
        """Sample configuration with Azure DevOps platform."""
        return """
project:
  name: "Test Project"
  type: "web-application"
  tech_stack:
    languages: ["Python"]
    frameworks: ["FastAPI"]
    platforms: ["Azure"]

work_tracking:
  platform: "azure-devops"
  organization: "https://dev.azure.com/testorg"
  project: "TestProject"
  credentials_source: "cli"

  work_item_types:
    epic: "Epic"
    feature: "Feature"
    story: "User Story"
    task: "Task"
    bug: "Bug"

  custom_fields:
    story_points: "Microsoft.VSTS.Scheduling.StoryPoints"
    business_value: "Microsoft.VSTS.Common.BusinessValue"
    technical_risk: "Custom.TechnicalRisk"

  iteration_format: "{project}\\\\{sprint}"
  sprint_naming: "Sprint {number}"

quality_standards:
  test_coverage_min: 80
  critical_vulnerabilities_max: 0
  high_vulnerabilities_max: 0
  code_complexity_max: 10

agent_config:
  models:
    architect: "claude-opus-4"
    engineer: "claude-sonnet-4.5"
    analyst: "claude-sonnet-4.5"
  enabled_agents:
    - business-analyst
    - senior-engineer
    - scrum-master
    - security-specialist
"""

    @pytest.fixture
    def filebased_config_yaml(self):
        """Sample configuration with file-based platform."""
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
    story: "User Story"
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

    def test_daily_standup_no_az_boards_commands(self, tmp_path, azure_config_yaml):
        """Test that daily-standup workflow does NOT contain az boards commands."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml)

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("daily-standup")

        # Should NOT have any az boards commands
        assert "az boards" not in rendered, \
            "daily-standup still contains direct az boards commands"
        assert "az boards query" not in rendered, \
            "daily-standup still contains az boards query commands"

    def test_daily_standup_uses_adapter_pattern(self, tmp_path, azure_config_yaml):
        """Test that daily-standup workflow uses adapter pattern."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml)

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("daily-standup")

        # Should initialize adapter
        assert "from work_tracking import get_adapter" in rendered, \
            "daily-standup missing adapter import"
        assert "adapter = get_adapter()" in rendered, \
            "daily-standup missing adapter initialization"

        # Should use adapter methods
        assert "adapter.query_sprint_work_items(" in rendered, \
            "daily-standup should use adapter.query_sprint_work_items()"

    def test_daily_standup_no_platform_conditionals(self, tmp_path, azure_config_yaml):
        """Test that daily-standup has NO platform-specific conditionals."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml)

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("daily-standup")

        # Should NOT have platform conditionals
        assert "{% if work_tracking.platform == 'azure-devops' %}" not in rendered, \
            "daily-standup still has Azure DevOps platform conditionals"
        assert "{% else %}" not in rendered or rendered.count("{% else %}") <= 2, \
            "daily-standup has suspicious conditional logic (possible platform branching)"

    def test_backlog_grooming_no_az_boards_commands(self, tmp_path, azure_config_yaml):
        """Test that backlog-grooming workflow does NOT contain az boards commands."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml)

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Should NOT have any az boards commands
        assert "az boards" not in rendered, \
            "backlog-grooming still contains direct az boards commands"
        assert "az boards query" not in rendered, \
            "backlog-grooming still contains az boards query commands"

    def test_backlog_grooming_uses_adapter_pattern(self, tmp_path, azure_config_yaml):
        """Test that backlog-grooming workflow uses adapter pattern."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml)

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Should initialize adapter
        assert "from work_tracking import get_adapter" in rendered, \
            "backlog-grooming missing adapter import"
        assert "adapter = get_adapter()" in rendered, \
            "backlog-grooming missing adapter initialization"

        # Should use adapter methods
        assert "adapter.query_work_items(" in rendered, \
            "backlog-grooming should use adapter.query_work_items()"
        assert "adapter.create_work_item(" in rendered, \
            "backlog-grooming should use adapter.create_work_item()"
        assert "adapter.update_work_item(" in rendered, \
            "backlog-grooming should use adapter.update_work_item()"

    def test_backlog_grooming_no_platform_conditionals(self, tmp_path, azure_config_yaml):
        """Test that backlog-grooming has NO platform-specific conditionals."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml)

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Should NOT have platform conditionals for work tracking operations
        assert "{% if work_tracking.platform == 'azure-devops' %}" not in rendered, \
            "backlog-grooming still has Azure DevOps platform conditionals"

    def test_sprint_retrospective_no_az_boards_commands(self, tmp_path, azure_config_yaml):
        """Test that sprint-retrospective workflow does NOT contain az boards commands."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml)

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-retrospective")

        # Should NOT have any az boards commands
        assert "az boards" not in rendered, \
            "sprint-retrospective still contains direct az boards commands"
        assert "az boards query" not in rendered, \
            "sprint-retrospective still contains az boards query commands"

    def test_sprint_retrospective_uses_adapter_pattern(self, tmp_path, azure_config_yaml):
        """Test that sprint-retrospective workflow uses adapter pattern."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml)

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-retrospective")

        # Should initialize adapter
        assert "from work_tracking import get_adapter" in rendered, \
            "sprint-retrospective missing adapter import"
        assert "adapter = get_adapter()" in rendered, \
            "sprint-retrospective missing adapter initialization"

        # Should use adapter methods
        assert "adapter.query_sprint_work_items(" in rendered, \
            "sprint-retrospective should use adapter.query_sprint_work_items()"
        assert "adapter.get_sprint_summary(" in rendered, \
            "sprint-retrospective should use adapter.get_sprint_summary()"
        assert "adapter.create_work_item_idempotent(" in rendered, \
            "sprint-retrospective should use adapter.create_work_item_idempotent()"

    def test_sprint_retrospective_no_platform_conditionals(self, tmp_path, azure_config_yaml):
        """Test that sprint-retrospective has NO platform-specific conditionals."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml)

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-retrospective")

        # Should NOT have platform conditionals for work tracking operations
        assert "{% if work_tracking.platform == 'azure-devops' %}" not in rendered, \
            "sprint-retrospective still has Azure DevOps platform conditionals"

    def test_all_three_workflows_work_with_file_based_adapter(self, tmp_path, filebased_config_yaml):
        """Test that all three fixed workflows work correctly with file-based adapter."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(filebased_config_yaml)

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        workflows_to_test = ["daily-standup", "backlog-grooming", "sprint-retrospective"]

        for workflow_name in workflows_to_test:
            rendered = registry.render_workflow(workflow_name)

            # Should use adapter pattern
            assert "adapter = get_adapter()" in rendered, \
                f"{workflow_name} missing adapter initialization for file-based platform"

            # Should NOT have Azure-specific commands
            assert "az boards" not in rendered, \
                f"{workflow_name} has az boards commands with file-based platform"

    def test_all_three_workflows_consistent_across_platforms(self, tmp_path, azure_config_yaml, filebased_config_yaml):
        """Test that all three workflows render consistently across platforms."""
        workflows_to_test = ["daily-standup", "backlog-grooming", "sprint-retrospective"]

        # Setup configs once before the loop
        config_path_azure = tmp_path / "azure" / ".claude" / "config.yaml"
        config_path_azure.parent.mkdir(parents=True, exist_ok=True)
        config_path_azure.write_text(azure_config_yaml)
        config_azure = load_config(config_path_azure)
        registry_azure = WorkflowRegistry(config_azure)

        config_path_file = tmp_path / "file" / ".claude" / "config.yaml"
        config_path_file.parent.mkdir(parents=True, exist_ok=True)
        config_path_file.write_text(filebased_config_yaml)
        config_file = load_config(config_path_file)
        registry_file = WorkflowRegistry(config_file)

        for workflow_name in workflows_to_test:
            # Render with Azure DevOps config
            rendered_azure = registry_azure.render_workflow(workflow_name)

            # Render with file-based config
            rendered_file = registry_file.render_workflow(workflow_name)

            # Both should use adapter pattern
            assert "adapter = get_adapter()" in rendered_azure, \
                f"{workflow_name} Azure config missing adapter"
            assert "adapter = get_adapter()" in rendered_file, \
                f"{workflow_name} file-based config missing adapter"

            # Neither should have platform-specific CLI commands
            assert "az boards" not in rendered_azure, \
                f"{workflow_name} Azure config has az boards commands"
            assert "az boards" not in rendered_file, \
                f"{workflow_name} file-based config has az boards commands"

            # Key adapter method calls should be present in both
            if workflow_name == "daily-standup":
                assert "adapter.query_sprint_work_items(" in rendered_azure
                assert "adapter.query_sprint_work_items(" in rendered_file
            elif workflow_name == "backlog-grooming":
                assert "adapter.query_work_items(" in rendered_azure
                assert "adapter.query_work_items(" in rendered_file
            elif workflow_name == "sprint-retrospective":
                assert "adapter.get_sprint_summary(" in rendered_azure
                assert "adapter.get_sprint_summary(" in rendered_file
