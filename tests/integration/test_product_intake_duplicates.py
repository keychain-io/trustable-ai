"""
Integration tests for product-intake workflow duplicate detection.

Tests Bug #1127 fix - ensures product-intake workflow prevents duplicate
work items when retried.
"""
import pytest
from pathlib import Path
from workflows.registry import WorkflowRegistry
from config.loader import load_config


@pytest.mark.integration
class TestProductIntakeDuplicateDetection:
    """Test suite for product-intake workflow duplicate detection integration."""

    @pytest.fixture
    def azure_config_yaml(self):
        """Sample configuration with Azure DevOps platform."""
        return """
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
    analyst: "claude-sonnet-4.5"
  enabled_agents:
    - business-analyst
    - senior-engineer
"""

    def test_product_intake_has_duplicate_detection(self, tmp_path, azure_config_yaml):
        """Test that product-intake workflow includes duplicate detection step."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding="utf-8")

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("product-intake")

        # Should have Step 4.0: Duplicate Detection
        assert "Step 4.0: Duplicate Detection" in rendered
        assert "check_recent_duplicates" in rendered

    def test_duplicate_detection_before_creation(self, tmp_path, azure_config_yaml):
        """Test that duplicate detection happens BEFORE work item creation."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding="utf-8")

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("product-intake")

        # Find positions
        dup_detection_pos = rendered.find("Step 4.0: Duplicate Detection")
        creation_pos = rendered.find("Step 4.1: Create Work Item")

        # Duplicate detection should come before creation
        assert dup_detection_pos > 0
        assert creation_pos > 0
        assert dup_detection_pos < creation_pos, \
            "Duplicate detection should happen before work item creation"

    def test_duplicate_detection_imports_check_function(self, tmp_path, azure_config_yaml):
        """Test that workflow imports check_recent_duplicates function."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding="utf-8")

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("product-intake")

        # Should import from CLI wrapper
        assert "from cli_wrapper import check_recent_duplicates" in rendered
        assert "sys.path.insert(0," in rendered

    def test_duplicate_detection_uses_correct_parameters(self, tmp_path, azure_config_yaml):
        """Test that duplicate detection uses correct parameters."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding="utf-8")

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("product-intake")

        # Should call with title and work_item_type
        assert "check_recent_duplicates(" in rendered
        assert "title=suggested_title or title" in rendered
        assert "work_item_type=work_item_type" in rendered

        # Should use default thresholds
        assert "hours=1" in rendered
        assert "similarity_threshold=0.95" in rendered

    def test_duplicate_detection_displays_results(self, tmp_path, azure_config_yaml):
        """Test that duplicate detection displays results to user."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding="utf-8")

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("product-intake")

        # Should display duplicate warning
        assert ":warning: DUPLICATE DETECTED!" in rendered

        # Should show duplicate details
        assert "duplicate['id']" in rendered
        assert "duplicate['title']" in rendered
        assert "duplicate['similarity']" in rendered
        assert "duplicate['created_date']" in rendered
        assert "duplicate['state']" in rendered
        assert "duplicate['url']" in rendered

    def test_duplicate_detection_offers_user_choice(self, tmp_path, azure_config_yaml):
        """Test that duplicate detection offers user choice of actions."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding="utf-8")

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("product-intake")

        # Should offer three options
        assert "[u] Use existing work item" in rendered
        assert "[c] Create new work item anyway" in rendered
        assert "[x] Cancel and exit" in rendered

        # Should capture user input
        assert "dup_action = input(" in rendered

    def test_duplicate_detection_handles_use_existing(self, tmp_path, azure_config_yaml):
        """Test that workflow handles 'use existing' action."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding="utf-8")

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("product-intake")

        # Should handle 'u' action
        assert "if dup_action == 'u':" in rendered
        assert "work_item_id = duplicate['id']" in rendered

        # Should skip creation
        assert "action = 'skip_creation'" in rendered

        # Should record in state
        assert "state.set_metadata" in rendered

    def test_duplicate_detection_handles_cancel(self, tmp_path, azure_config_yaml):
        """Test that workflow handles 'cancel' action."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding="utf-8")

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("product-intake")

        # Should handle 'x' action
        assert "if dup_action == 'x':" in rendered or "elif dup_action == 'x':" in rendered
        assert "state.complete_workflow()" in rendered
        assert "exit()" in rendered

    def test_duplicate_detection_handles_create_anyway(self, tmp_path, azure_config_yaml):
        """Test that workflow handles 'create anyway' action."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding="utf-8")

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("product-intake")

        # Should handle 'c' action
        assert "if dup_action == 'c':" in rendered or "elif dup_action == 'c':" in rendered

        # Should continue with creation
        assert "Continuing with work item creation" in rendered

    def test_duplicate_detection_no_duplicates_message(self, tmp_path, azure_config_yaml):
        """Test that workflow displays message when no duplicates found."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding="utf-8")

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("product-intake")

        # Should display success message
        assert ":white_check_mark: No duplicates found" in rendered

    def test_completion_phase_handles_skip_creation(self, tmp_path, azure_config_yaml):
        """Test that Phase 5 handles skip_creation action."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding="utf-8")

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("product-intake")

        # Should check for skip_creation action
        assert "if action == 'skip_creation':" in rendered

        # Should display appropriate message
        assert "Used existing work item" in rendered
        assert "No new work item created (duplicate avoided)" in rendered

    def test_duplicate_detection_only_in_create_actions(self, tmp_path, azure_config_yaml):
        """Test that duplicate detection only runs for create/escalate actions."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding="utf-8")

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("product-intake")

        # Duplicate detection should be inside 'if action in ['c', 'e']:' block
        lines = rendered.split('\n')
        dup_check_line = None
        for i, line in enumerate(lines):
            if "check_recent_duplicates(" in line:
                dup_check_line = i
                break

        assert dup_check_line is not None, "check_recent_duplicates call not found"

        # Look backwards to find the if statement
        found_if = False
        for i in range(dup_check_line, max(0, dup_check_line - 50), -1):
            if "if action in ['c', 'e']:" in lines[i]:
                found_if = True
                break

        assert found_if, "check_recent_duplicates should be within 'if action in [c, e]' block"

    def test_duplicate_detection_performance_threshold(self, tmp_path, azure_config_yaml):
        """Test that duplicate detection has acceptable performance threshold."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding="utf-8")

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("product-intake")

        # Should use 1 hour time window (fast query)
        assert "hours=1" in rendered

        # Should have high similarity threshold (95%) to reduce false positives
        assert "similarity_threshold=0.95" in rendered

    def test_duplicate_detection_error_handling(self, tmp_path, azure_config_yaml):
        """Test that duplicate detection failure doesn't block workflow."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding="utf-8")

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("product-intake")

        # check_recent_duplicates should handle errors internally
        # (returns None on failure, per implementation)
        # Workflow should check 'if duplicate:' which is safe with None
        assert "if duplicate:" in rendered
