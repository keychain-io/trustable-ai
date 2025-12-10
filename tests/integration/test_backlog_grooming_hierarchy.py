"""
Integration tests for backlog-grooming workflow Feature-Task hierarchy verification.

Tests Task #1097 implementation: Add Feature-Task hierarchy verification to backlog-grooming.j2.

This implements the "External Source of Truth" verification pattern from VISION.md Pillar #2:
- AI agents claim Epic is decomposed when some Features have no Tasks
- Verification queries adapter (external source of truth) for each Feature's children
- Verification fails fast with descriptive error if any Feature has zero Tasks
- Exits with code 1 on verification failure
"""
import pytest
from pathlib import Path
from workflows.registry import WorkflowRegistry
from config.loader import load_config


@pytest.mark.integration
class TestBacklogGroomingHierarchyVerification:
    """Test suite for Feature-Task hierarchy verification in backlog-grooming workflow."""

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
  source_directory: "src"
  test_directory: "tests"

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

  iteration_format: "{project}\\\\{sprint}"
  sprint_naming: "Sprint {number}"

quality_standards:
  test_coverage_min: 80
  critical_vulnerabilities_max: 0
  high_vulnerabilities_max: 0
  code_complexity_max: 10

agent_config:
  models:
    senior-engineer: "claude-sonnet-4.5"
  enabled_agents:
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
  source_directory: "src"
  test_directory: "tests"

work_tracking:
  platform: "file-based"
  work_items_directory: ".claude/work-items"

  work_item_types:
    epic: "Epic"
    feature: "Feature"
    story: "User Story"
    task: "Task"
    bug: "Bug"

  custom_fields:
    story_points: "Microsoft.VSTS.Scheduling.StoryPoints"

quality_standards:
  test_coverage_min: 80
  critical_vulnerabilities_max: 0
  high_vulnerabilities_max: 0
  code_complexity_max: 10

agent_config:
  models:
    senior-engineer: "claude-sonnet-4.5"
  enabled_agents:
    - senior-engineer
"""

    def test_verification_section_exists_after_feature_creation(self, tmp_path, azure_config_yaml):
        """Test that verification section is added after Feature/Task creation (line 268+)."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Verification section should exist after Feature creation
        assert "Verifying Epic Decomposition Hierarchy" in rendered, \
            "Verification section missing after Feature/Task creation"

        # Should be in Step 0 Epic Decomposition section
        assert "Step 0: Epic Detection and Decomposition" in rendered
        decomposition_pos = rendered.find("Step 0: Epic Detection and Decomposition")
        verification_pos = rendered.find("Verifying Epic Decomposition Hierarchy")

        assert decomposition_pos < verification_pos, \
            "Verification should be within Epic Decomposition step"

    def test_created_features_list_initialized(self, tmp_path, azure_config_yaml):
        """Test that created_features list is initialized before Feature creation loop."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Should initialize created_features list
        assert "created_features = []" in rendered, \
            "created_features list not initialized before Feature creation"

        # Should be before the Feature creation loop
        created_features_pos = rendered.find("created_features = []")
        feature_loop_pos = rendered.find("for feature_data in decomposition['features']:")

        assert created_features_pos < feature_loop_pos, \
            "created_features initialization should be before Feature creation loop"

    def test_feature_ids_stored_during_creation(self, tmp_path, azure_config_yaml):
        """Test that Feature IDs are stored during creation for later verification."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Should append to created_features list after each Feature creation
        assert "created_features.append({" in rendered, \
            "Feature info not appended to created_features list"

        # Should store id, title, and expected_tasks
        assert "'id': feature['id']" in rendered, \
            "Feature ID not stored"
        assert "'title': feature_data['title']" in rendered, \
            "Feature title not stored"
        assert "'expected_tasks': len(feature_data.get('tasks', []))" in rendered, \
            "Expected tasks count not stored"

    def test_verification_queries_adapter_for_each_feature(self, tmp_path, azure_config_yaml):
        """Test that verification queries adapter for children of each Feature."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Get verification section
        verification_pos = rendered.find("Verifying Epic Decomposition Hierarchy")
        verification_section = rendered[verification_pos:]

        # Should iterate over created_features
        assert "for feature_info in created_features:" in verification_section, \
            "Verification should iterate over created_features"

        # Should query adapter for Tasks
        assert "adapter.query_work_items(" in verification_section, \
            "Verification should query adapter for work items"

        # Should filter for Tasks with Feature as parent
        assert "parent_id" in verification_section, \
            "Verification should check parent_id"

    def test_verification_checks_each_feature_has_tasks(self, tmp_path, azure_config_yaml):
        """Test that verification checks each Feature has at least one Task."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Get verification section
        verification_pos = rendered.find("Verifying Epic Decomposition Hierarchy")
        verification_section = rendered[verification_pos:]

        # Should check if task_count is 0
        assert "if task_count == 0:" in verification_section, \
            "Verification should check if Feature has zero Tasks"

        # Should print error message with required format
        assert "ERROR: Feature" in verification_section, \
            "Error message should include 'ERROR: Feature'"
        assert "has no Tasks - workflow incomplete" in verification_section, \
            "Error message should include 'has no Tasks - workflow incomplete'"

    def test_verification_error_includes_feature_id_and_title(self, tmp_path, azure_config_yaml):
        """Test that error message includes Feature ID and title."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Get verification section
        verification_pos = rendered.find("Verifying Epic Decomposition Hierarchy")
        verification_section = rendered[verification_pos:]

        # Error message should include feature_id and feature_title
        assert "feature_id" in verification_section and "feature_title" in verification_section, \
            "Verification should use feature_id and feature_title variables"

        # Should include these in the error message
        error_msg_pos = verification_section.find("ERROR: Feature")
        error_msg_section = verification_section[error_msg_pos:error_msg_pos + 200]

        assert "{feature_id}" in error_msg_section or "feature_id" in error_msg_section, \
            "Error message should include feature_id"
        assert "{feature_title}" in error_msg_section or "feature_title" in error_msg_section, \
            "Error message should include feature_title"

    def test_verification_tracks_childless_features(self, tmp_path, azure_config_yaml):
        """Test that verification tracks all childless Features in a list."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Get verification section
        verification_pos = rendered.find("Verifying Epic Decomposition Hierarchy")
        verification_section = rendered[verification_pos:]

        # Should initialize childless_features list
        assert "childless_features = []" in verification_section, \
            "childless_features list should be initialized"

        # Should append to childless_features when Feature has no Tasks
        assert "childless_features.append({" in verification_section, \
            "Should append to childless_features when Feature has no Tasks"

    def test_verification_sets_failed_flag(self, tmp_path, azure_config_yaml):
        """Test that verification sets verification_failed flag when Feature has no Tasks."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Get verification section
        verification_pos = rendered.find("Verifying Epic Decomposition Hierarchy")
        verification_section = rendered[verification_pos:]

        # Should initialize verification_failed flag
        assert "verification_failed = False" in verification_section, \
            "verification_failed flag should be initialized to False"

        # Should set verification_failed = True when Feature has no Tasks
        assert "verification_failed = True" in verification_section, \
            "Should set verification_failed = True on failure"

    def test_verification_checks_features_linked_to_epic(self, tmp_path, azure_config_yaml):
        """Test that verification checks all Features are linked to parent Epic."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Get verification section
        verification_pos = rendered.find("Verifying Epic Decomposition Hierarchy")
        verification_section = rendered[verification_pos:]

        # Should verify Features linked to Epic
        assert "Verifying Features linked to Epic" in verification_section, \
            "Should have step to verify Features linked to Epic"

        # Should query adapter for Features under Epic
        assert "epic_features" in verification_section, \
            "Should query Features under Epic"

        # Should compare expected vs actual Feature count
        assert "expected_feature_count" in verification_section and "actual_feature_count" in verification_section, \
            "Should compare expected vs actual Feature count"

    def test_verification_exits_with_code_1_on_failure(self, tmp_path, azure_config_yaml):
        """Test that verification exits with code 1 if verification fails."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Get verification section
        verification_pos = rendered.find("Verifying Epic Decomposition Hierarchy")
        verification_section = rendered[verification_pos:]

        # Should exit with sys.exit(1) on failure
        assert "sys.exit(1)" in verification_section, \
            "Should exit with sys.exit(1) on verification failure"

        # Should be in the verification_failed block
        assert "if verification_failed:" in verification_section, \
            "Should check verification_failed flag"

        # sys.exit(1) should come after the verification_failed check
        failed_check_pos = verification_section.find("if verification_failed:")
        sys_exit_pos = verification_section.find("sys.exit(1)")

        assert failed_check_pos < sys_exit_pos, \
            "sys.exit(1) should be in the verification_failed block"

    def test_verification_imports_sys_module(self, tmp_path, azure_config_yaml):
        """Test that verification imports sys module for sys.exit()."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Get verification section - need to look before the print statements
        verification_start = rendered.find("4. Verify hierarchy created correctly:")
        verification_section = rendered[verification_start:verification_start + 1000]

        # Should import sys before using sys.exit()
        assert "import sys" in verification_section, \
            "Should import sys module before using sys.exit()"

    def test_verification_prints_summary_on_failure(self, tmp_path, azure_config_yaml):
        """Test that verification prints summary of childless Features on failure."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Get verification section
        verification_pos = rendered.find("Verifying Epic Decomposition Hierarchy")
        verification_section = rendered[verification_pos:]

        # Should print VERIFICATION FAILED message
        assert "VERIFICATION FAILED" in verification_section, \
            "Should print VERIFICATION FAILED message"

        # Should print list of childless Features
        assert "Feature(s) have no Tasks:" in verification_section, \
            "Should print list of childless Features"

        # Should iterate over childless_features to print them
        assert "for f in childless_features:" in verification_section, \
            "Should iterate over childless_features to print summary"

    def test_verification_prints_success_message(self, tmp_path, azure_config_yaml):
        """Test that verification prints success message when all checks pass."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Get verification section
        verification_pos = rendered.find("Verifying Epic Decomposition Hierarchy")
        verification_section = rendered[verification_pos:]

        # Should print VERIFICATION PASSED message
        assert "VERIFICATION PASSED" in verification_section, \
            "Should print VERIFICATION PASSED message"

        # Should be in the else block (when verification_failed is False)
        assert "else:" in verification_section, \
            "Should have else block for successful verification"

        # Should list what was verified
        assert "All Features have at least one Task" in verification_section, \
            "Success message should mention Features have Tasks"
        assert "All Features are linked to Epic" in verification_section, \
            "Success message should mention Features linked to Epic"

    def test_verification_handles_adapter_query_failures(self, tmp_path, azure_config_yaml):
        """Test that verification handles adapter query failures gracefully."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Get verification section
        verification_pos = rendered.find("Verifying Epic Decomposition Hierarchy")
        verification_section = rendered[verification_pos:]

        # Should use try-except for adapter queries
        assert "try:" in verification_section, \
            "Should use try-except for adapter queries"
        assert "except Exception as e:" in verification_section, \
            "Should catch exceptions from adapter queries"

        # Should print error message on adapter failure
        assert "Failed to query" in verification_section, \
            "Should print error message on adapter query failure"

    def test_verification_works_with_file_based_adapter(self, tmp_path, filebased_config_yaml):
        """Test that verification works with file-based adapter (not just Azure DevOps)."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(filebased_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Get verification section
        verification_pos = rendered.find("Verifying Epic Decomposition Hierarchy")
        verification_section = rendered[verification_pos:]

        # Should use generic adapter methods
        assert "adapter.query_work_items(" in verification_section, \
            "Should use generic adapter.query_work_items()"

        # Should NOT have Azure DevOps-specific code
        assert "az boards" not in verification_section, \
            "Should not have Azure DevOps-specific commands"

    def test_verification_checks_both_parent_id_formats(self, tmp_path, azure_config_yaml):
        """Test that verification checks both parent_id and fields.System.Parent for cross-platform compatibility."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Get verification section
        verification_pos = rendered.find("Verifying Epic Decomposition Hierarchy")
        verification_section = rendered[verification_pos:]

        # Should check both parent_id and System.Parent
        assert "parent_id" in verification_section, \
            "Should check parent_id field (file-based adapter format)"
        assert "System.Parent" in verification_section, \
            "Should check System.Parent field (Azure DevOps format)"

        # Should use OR logic to check both formats
        assert "or" in verification_section, \
            "Should use OR logic to check both parent formats"

    def test_verification_mentions_vision_pattern(self, tmp_path, azure_config_yaml):
        """Test that verification references VISION.md External Source of Truth pattern."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Get verification section
        verification_pos = rendered.find("Verifying Epic Decomposition Hierarchy")
        verification_section = rendered[verification_pos:verification_pos + 500]

        # Should reference External Source of Truth pattern
        assert "External Source of Truth" in verification_section or "external source of truth" in verification_section, \
            "Should reference External Source of Truth pattern"

        # Should reference VISION.md or mark as CRITICAL
        assert "VISION.md" in verification_section or "CRITICAL" in verification_section, \
            "Should reference VISION.md or mark as CRITICAL"

    def test_verification_verifies_task_parent_links(self, tmp_path, azure_config_yaml):
        """Test that verification checks each Task has correct parent Feature."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Get verification section
        verification_pos = rendered.find("Verifying Epic Decomposition Hierarchy")
        verification_section = rendered[verification_pos:]

        # Should iterate over Tasks to verify parent
        assert "for task in feature_tasks:" in verification_section, \
            "Should iterate over Tasks to verify parent"

        # Should check Task parent_id matches Feature
        assert "parent_id" in verification_section and "feature_id" in verification_section, \
            "Should check Task parent_id matches Feature ID"

        # Should warn on parent mismatch
        assert "WARNING" in verification_section and "parent mismatch" in verification_section.lower(), \
            "Should warn on Task parent mismatch"

    def test_verification_story_points_optional(self, tmp_path, azure_config_yaml):
        """Test that story points verification is optional (wrapped in Jinja if)."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Get verification section
        verification_pos = rendered.find("Verifying Epic Decomposition Hierarchy")
        verification_section = rendered[verification_pos:]

        # Should have story points verification
        assert "story points" in verification_section.lower(), \
            "Should have story points verification section"

        # Story points section should be wrapped in try-except (errors are warnings, not failures)
        story_points_pos = verification_section.find("story points")
        story_points_section = verification_section[story_points_pos:story_points_pos + 1000]

        assert "try:" in story_points_section or "WARNING" in story_points_section, \
            "Story points verification should be wrapped in try-except or treat as warnings"


@pytest.mark.integration
class TestBacklogGroomingHierarchyEdgeCases:
    """Test edge cases for backlog-grooming hierarchy verification."""

    @pytest.fixture
    def azure_config_yaml(self):
        """Sample configuration with Azure DevOps adapter."""
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
    task: "Task"

quality_standards:
  test_coverage_min: 80

agent_config:
  models:
    senior-engineer: "claude-sonnet-4.5"
  enabled_agents:
    - senior-engineer
"""

    def test_verification_handles_empty_created_features(self, tmp_path, azure_config_yaml):
        """Test that verification handles case when created_features is empty."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Get verification section
        verification_pos = rendered.find("Verifying Epic Decomposition Hierarchy")
        verification_section = rendered[verification_pos:]

        # Should iterate over created_features (handles empty gracefully)
        assert "for feature_info in created_features:" in verification_section, \
            "Should iterate over created_features (handles empty gracefully)"

    def test_verification_handles_missing_parent_id_field(self, tmp_path, azure_config_yaml):
        """Test that verification handles case when work item has no parent_id field."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Get verification section
        verification_pos = rendered.find("Verifying Epic Decomposition Hierarchy")
        verification_section = rendered[verification_pos:]

        # Should use .get() to safely access parent_id
        assert ".get('parent_id')" in verification_section or "get('parent_id')" in verification_section, \
            "Should use .get() to safely access parent_id"

    def test_verification_printed_with_visual_separators(self, tmp_path, azure_config_yaml):
        """Test that verification output includes visual separators for readability."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Get verification section
        verification_pos = rendered.find("Verifying Epic Decomposition Hierarchy")
        verification_section = rendered[verification_pos:verification_pos + 500]

        # Should have visual separators (=== or ---)
        assert "=" * 80 in verification_section or "print(\"=\" * 80)" in verification_section, \
            "Should have visual separators for readability"
