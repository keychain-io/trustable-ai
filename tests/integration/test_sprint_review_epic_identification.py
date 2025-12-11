"""
Integration tests for sprint-review workflow EPIC identification.

Tests Task #1089 implementation: Extend sprint-review workflow to identify EPICs for testing

This implements end-to-end testing of EPIC identification in sprint-review workflow:
- Query adapter for Epic work items from sprint scope
- Verify each EPIC has attached/linked acceptance test plan
- Store testable EPICs in workflow state
- Works with both Azure DevOps and file-based adapters
"""
import pytest
from pathlib import Path
from workflows.registry import WorkflowRegistry
from config.loader import load_config


@pytest.mark.integration
class TestSprintReviewEpicIdentificationIntegration:
    """Integration test suite for EPIC identification in sprint-review workflow."""

    @pytest.fixture
    def azure_config_yaml(self):
        """Sample configuration with Azure DevOps adapter."""
        return """
project:
  name: "Test Project"
  type: "web-application"
  tech_stack:
    languages: ["Python"]
    frameworks: ["FastAPI"]

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
  enabled_agents:
    - business-analyst
    - project-architect
    - senior-engineer
    - scrum-master
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
    - project-architect
    - senior-engineer
    - scrum-master
"""

    def test_sprint_review_workflow_renders_with_epic_identification(self, tmp_path, azure_config_yaml):
        """Test that sprint-review workflow renders successfully with EPIC identification step."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        # Render workflow - should not raise exception
        rendered = registry.render_workflow("sprint-review")

        # Verify workflow structure
        assert "Sprint Review Workflow" in rendered
        assert "Step 1: Collect Sprint Completion Metrics" in rendered
        assert "Step 1.5: Identify EPICs for Testing" in rendered
        assert "Step 2: Run Acceptance Tests" in rendered

    def test_epic_identification_uses_correct_adapter_query_format(self, tmp_path, azure_config_yaml):
        """Test that EPIC identification uses correct query format for Azure DevOps."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-review")

        epic_section = rendered[rendered.find("## Step 1.5"):rendered.find("## Step 2")]

        # Should use correct filter format for Azure DevOps
        assert "'System.WorkItemType': 'Epic'" in epic_section, \
            "Should filter by System.WorkItemType field"

        assert "'System.IterationPath':" in epic_section, \
            "Should filter by System.IterationPath field"

        # Should use project name from config
        assert "TestProject" in epic_section, \
            "Should use project name from configuration"

    def test_file_based_adapter_epic_identification(self, tmp_path, filebased_config_yaml):
        """Test that EPIC identification works with file-based adapter."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(filebased_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-review")

        epic_section = rendered[rendered.find("## Step 1.5"):rendered.find("## Step 2")]

        # Should check for file-based platform
        assert "elif adapter.platform == 'file-based':" in epic_section, \
            "Should check for file-based platform"

        # Should check comments for test plan path
        assert "comments = work_item.get('comments', [])" in epic_section, \
            "Should check work item comments for test plan path"

    def test_epic_identification_integrates_with_workflow_state(self, tmp_path, azure_config_yaml):
        """Test that EPIC identification integrates with workflow state management."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-review")

        epic_section = rendered[rendered.find("## Step 1.5"):rendered.find("## Step 2")]

        # Should create workflow state dictionary
        assert "testable_epics_state = {" in epic_section, \
            "Should create workflow state dictionary"

        # Should include checkpoint comment
        assert "Checkpoint:" in epic_section or "💾" in epic_section, \
            "Should include checkpoint indication"

    def test_workflow_uses_azure_cli_wrapper_correctly(self, tmp_path, azure_config_yaml):
        """Test that workflow imports and uses Azure CLI wrapper correctly."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-review")

        epic_section = rendered[rendered.find("## Step 1.5"):rendered.find("## Step 2")]

        # Should import from canonical location
        assert 'sys.path.insert(0, ".claude/skills")' in epic_section, \
            "Should add .claude/skills to sys.path"

        assert "from azure_devops.cli_wrapper import azure_cli" in epic_section, \
            "Should import azure_cli from canonical location"

        # Should use azure_cli methods
        assert "azure_cli.verify_attachment_exists(" in epic_section, \
            "Should use azure_cli.verify_attachment_exists method"

    def test_complete_workflow_flow_with_epic_identification(self, tmp_path, azure_config_yaml):
        """Test complete workflow flow from Step 1 through Step 1.5 to Step 2."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-review")

        # Verify complete flow
        assert "## Initialize Workflow" in rendered
        assert "## Step 1: Collect Sprint Completion Metrics" in rendered
        assert "## Step 1.5: Identify EPICs for Testing" in rendered
        assert "## Step 2: Run Acceptance Tests" in rendered

        # Verify steps are in correct order
        init_pos = rendered.find("## Initialize Workflow")
        step1_pos = rendered.find("## Step 1: Collect Sprint Completion Metrics")
        step15_pos = rendered.find("## Step 1.5: Identify EPICs for Testing")
        step2_pos = rendered.find("## Step 2: Run Acceptance Tests")

        assert init_pos < step1_pos < step15_pos < step2_pos, \
            "Steps should be in correct order"

    def test_workflow_handles_platform_specific_differences(self, tmp_path):
        """Test that workflow handles differences between Azure DevOps and file-based platforms."""
        # Test Azure DevOps configuration
        azure_config = """
project:
  name: "Test Project"
  type: "web-application"
  tech_stack:
    languages: ["Python"]

work_tracking:
  platform: "azure-devops"
  organization: "https://dev.azure.com/testorg"
  project: "TestProject"
  credentials_source: "cli"
  work_item_types:
    epic: "Epic"

quality_standards:
  test_coverage_min: 80

agent_config:
  models:
    engineer: "claude-sonnet-4.5"
  enabled_agents:
    - senior-engineer
"""

        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        azure_rendered = registry.render_workflow("sprint-review")

        # Should contain Azure DevOps specific logic
        assert "if adapter.platform == 'azure-devops':" in azure_rendered
        assert "'AttachedFile' in rel_type" in azure_rendered

        # Test file-based configuration
        filebased_config = """
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

quality_standards:
  test_coverage_min: 80

agent_config:
  models:
    engineer: "claude-sonnet-4.5"
  enabled_agents:
    - senior-engineer
"""

        config_path.write_text(filebased_config, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        filebased_rendered = registry.render_workflow("sprint-review")

        # Should contain file-based specific logic
        assert "elif adapter.platform == 'file-based':" in filebased_rendered
        assert "comments = work_item.get('comments', [])" in filebased_rendered

    def test_workflow_error_handling_and_logging(self, tmp_path, azure_config_yaml):
        """Test that workflow includes proper error handling and logging."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-review")

        epic_section = rendered[rendered.find("## Step 1.5"):rendered.find("## Step 2")]

        # Should include try-except blocks
        assert "try:" in epic_section
        assert "except Exception as e:" in epic_section

        # Should include logging statements
        assert "print(f\"" in epic_section
        assert "🔍" in epic_section  # Emoji for visual clarity
        assert "✅" in epic_section  # Success indicator
        assert "⚠️" in epic_section  # Warning indicator
        assert "❌" in epic_section  # Error indicator

        # Should log summary information
        assert "EPIC Identification Summary" in epic_section

    def test_workflow_produces_actionable_output(self, tmp_path, azure_config_yaml):
        """Test that workflow produces actionable output for users."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-review")

        epic_section = rendered[rendered.find("## Step 1.5"):rendered.find("## Step 2")]

        # Should provide clear instructions for missing test plans
        assert "To include them, attach/link test plans to the EPIC work items" in epic_section, \
            "Should provide actionable guidance for missing test plans"

        # Should indicate which EPICs are testable
        assert "eligible for acceptance testing" in epic_section, \
            "Should indicate which EPICs are eligible for testing"

        # Should indicate which EPICs are excluded
        assert "excluded from acceptance testing" in epic_section, \
            "Should indicate which EPICs are excluded from testing"
