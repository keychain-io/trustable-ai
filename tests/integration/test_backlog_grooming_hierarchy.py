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


@pytest.mark.integration
class TestBacklogGroomingStoryPointVerification:
    """Test suite for story point summation verification in backlog-grooming workflow."""

    @pytest.fixture
    def azure_config_yaml(self):
        """Sample configuration with Azure DevOps adapter and story points."""
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
        """Sample configuration with file-based adapter and story points."""
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

    def test_story_point_verification_section_exists(self, tmp_path, azure_config_yaml):
        """Test that story point verification section is added in verification."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Get verification section
        verification_pos = rendered.find("Verifying Epic Decomposition Hierarchy")
        verification_section = rendered[verification_pos:]

        # Should have story point verification
        assert "Verifying story point summation" in verification_section, \
            "Story point verification section missing"

    def test_story_point_field_variable_initialized(self, tmp_path, azure_config_yaml):
        """Test that story_point_field variable is initialized from config."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Get verification section
        verification_pos = rendered.find("Verifying Epic Decomposition Hierarchy")
        verification_section = rendered[verification_pos:]

        # Should initialize story_point_field from config
        assert "story_point_field = 'Microsoft.VSTS.Scheduling.StoryPoints'" in verification_section, \
            "story_point_field should be initialized from config"

    def test_story_point_mismatches_list_initialized(self, tmp_path, azure_config_yaml):
        """Test that story_point_mismatches list is initialized."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Get verification section
        verification_pos = rendered.find("Verifying Epic Decomposition Hierarchy")
        verification_section = rendered[verification_pos:]

        # Should initialize story_point_mismatches list
        assert "story_point_mismatches = []" in verification_section, \
            "story_point_mismatches list should be initialized"

    def test_calculates_sum_of_task_story_points(self, tmp_path, azure_config_yaml):
        """Test that verification calculates sum of Task story points within each Feature."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Get verification section
        verification_pos = rendered.find("Verifying Epic Decomposition Hierarchy")
        verification_section = rendered[verification_pos:]

        # Should sum Task story points
        assert "task_story_points_sum = sum(" in verification_section, \
            "Should calculate sum of Task story points"

        # Should use story_point_field from config
        assert "task.get('fields', {}).get(story_point_field, 0)" in verification_section, \
            "Should use story_point_field to get Task story points"

    def test_compares_feature_story_points_to_task_sum(self, tmp_path, azure_config_yaml):
        """Test that verification compares Feature story points to sum of child Tasks."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Get verification section
        verification_pos = rendered.find("Verifying Epic Decomposition Hierarchy")
        verification_section = rendered[verification_pos:]

        # Should get Feature story points
        assert "feature_story_points = feature_full.get('fields', {}).get(story_point_field, 0)" in verification_section, \
            "Should get Feature story points from adapter"

        # Should compare Feature points to Task sum
        assert "task_story_points_sum" in verification_section and "feature_story_points" in verification_section, \
            "Should compare Feature story points to Task sum"

    def test_calculates_variance_percentage(self, tmp_path, azure_config_yaml):
        """Test that verification calculates variance percentage correctly."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Get verification section
        verification_pos = rendered.find("Verifying Epic Decomposition Hierarchy")
        verification_section = rendered[verification_pos:]

        # Should calculate variance percentage
        assert "variance_pct" in verification_section, \
            "Should calculate variance percentage"

        # Should use formula: abs(actual - expected) / expected * 100
        assert "abs(task_story_points_sum - feature_story_points)" in verification_section, \
            "Variance calculation should use abs(actual - expected)"
        assert "/ feature_story_points * 100" in verification_section, \
            "Variance calculation should divide by expected and multiply by 100"

    def test_handles_division_by_zero_in_variance_calculation(self, tmp_path, azure_config_yaml):
        """Test that variance calculation handles division by zero when Feature has 0 points."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Get verification section
        verification_pos = rendered.find("Verifying Epic Decomposition Hierarchy")
        verification_section = rendered[verification_pos:]

        # Should handle division by zero
        assert "if feature_story_points > 0:" in verification_section, \
            "Should check for zero before division"

        # Should have else case for zero points
        assert "else:" in verification_section, \
            "Should have else case for zero story points"

    def test_outputs_variance_percentage_to_user(self, tmp_path, azure_config_yaml):
        """Test that verification outputs variance percentage to user."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Get verification section
        verification_pos = rendered.find("Verifying Epic Decomposition Hierarchy")
        verification_section = rendered[verification_pos:]

        # Should print variance percentage
        assert "variance: {variance_pct:.1f}%" in verification_section, \
            "Should output variance percentage to user"

    def test_fails_when_variance_exceeds_20_percent(self, tmp_path, azure_config_yaml):
        """Test that verification fails with exit code 1 if variance >20%."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Get verification section
        verification_pos = rendered.find("Verifying Epic Decomposition Hierarchy")
        verification_section = rendered[verification_pos:]

        # Should check if variance exceeds 20%
        assert "if variance_pct > 20:" in verification_section, \
            "Should check if variance exceeds 20% threshold"

        # Should set verification_failed flag
        assert "verification_failed = True" in verification_section, \
            "Should set verification_failed = True when variance >20%"

    def test_prints_error_message_on_variance_failure(self, tmp_path, azure_config_yaml):
        """Test that verification prints error message when variance exceeds threshold."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Get verification section
        verification_pos = rendered.find("Verifying Epic Decomposition Hierarchy")
        verification_section = rendered[verification_pos:]

        # Should print error message
        assert "ERROR: Feature" in verification_section and "story point mismatch" in verification_section, \
            "Should print error message for story point mismatch"

        # Should include variance percentage in error
        assert "variance {variance_pct:.1f}%" in verification_section, \
            "Error message should include variance percentage"

    def test_tracks_story_point_mismatches_in_list(self, tmp_path, azure_config_yaml):
        """Test that verification tracks all story point mismatches in a list."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Get verification section
        verification_pos = rendered.find("Verifying Epic Decomposition Hierarchy")
        verification_section = rendered[verification_pos:]

        # Should append to story_point_mismatches list
        assert "story_point_mismatches.append({" in verification_section, \
            "Should append to story_point_mismatches list"

        # Should store mismatch details
        assert "'id': feature_id" in verification_section, \
            "Should store feature_id in mismatch"
        assert "'title': feature_title" in verification_section, \
            "Should store feature_title in mismatch"
        assert "'feature_points': feature_story_points" in verification_section, \
            "Should store feature_points in mismatch"
        assert "'tasks_sum': task_story_points_sum" in verification_section, \
            "Should store tasks_sum in mismatch"
        assert "'variance_pct': variance_pct" in verification_section, \
            "Should store variance_pct in mismatch"

    def test_verifies_epic_story_points_vs_features_sum(self, tmp_path, azure_config_yaml):
        """Test that verification checks Epic story points vs sum of Features."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Get verification section
        verification_pos = rendered.find("Verifying Epic Decomposition Hierarchy")
        verification_section = rendered[verification_pos:]

        # Should verify Epic story points
        assert "Verifying Epic story point summation" in verification_section, \
            "Should have Epic story point verification step"

        # Should get Epic story points
        assert "epic_story_points = epic_full.get('fields', {}).get(story_point_field, 0)" in verification_section, \
            "Should get Epic story points from adapter"

        # Should sum Feature story points
        assert "features_story_points_sum" in verification_section, \
            "Should calculate sum of Feature story points"

    def test_epic_variance_calculation(self, tmp_path, azure_config_yaml):
        """Test that Epic variance is calculated correctly."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Get verification section
        verification_pos = rendered.find("Verifying Epic Decomposition Hierarchy")
        verification_section = rendered[verification_pos:]

        # Should calculate Epic variance
        assert "epic_variance_pct" in verification_section, \
            "Should calculate Epic variance percentage"

        # Should use correct formula
        assert "abs(features_story_points_sum - epic_story_points)" in verification_section, \
            "Epic variance should use abs(actual - expected)"

    def test_epic_variance_failure_sets_verification_failed(self, tmp_path, azure_config_yaml):
        """Test that Epic variance >20% sets verification_failed flag."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Get verification section
        verification_pos = rendered.find("Verifying Epic Decomposition Hierarchy")
        verification_section = rendered[verification_pos:]

        # Should check Epic variance threshold
        assert "if epic_variance_pct > 20:" in verification_section, \
            "Should check if Epic variance exceeds 20%"

        # Should print error for Epic variance
        assert "ERROR: Epic story point variance" in verification_section, \
            "Should print error for Epic variance failure"

    def test_story_point_mismatches_included_in_failure_summary(self, tmp_path, azure_config_yaml):
        """Test that story point mismatches are included in failure summary."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Get verification section
        verification_pos = rendered.find("Verifying Epic Decomposition Hierarchy")
        verification_section = rendered[verification_pos:]

        # Should include story point mismatches in failure summary
        assert "if story_point_mismatches:" in verification_section, \
            "Should check if there are story point mismatches"

        # Should print mismatch count
        assert "Feature(s) have story point mismatches" in verification_section, \
            "Should print count of Features with story point mismatches"

        # Should iterate over mismatches to print details
        assert "for m in story_point_mismatches:" in verification_section, \
            "Should iterate over story_point_mismatches to print details"

    def test_story_point_mismatch_details_in_summary(self, tmp_path, azure_config_yaml):
        """Test that story point mismatch details are printed in failure summary."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Get verification section
        verification_pos = rendered.find("Verifying Epic Decomposition Hierarchy")
        verification_section = rendered[verification_pos:]

        # Should print Feature ID and title
        assert "WI-{m['id']}: {m['title']}" in verification_section, \
            "Should print Feature ID and title in mismatch summary"

        # Should print Feature points, Tasks sum, and variance
        assert "Feature: {m['feature_points']} pts" in verification_section, \
            "Should print Feature story points"
        assert "Tasks sum: {m['tasks_sum']} pts" in verification_section, \
            "Should print Tasks sum"
        assert "Variance: {m['variance_pct']:.1f}%" in verification_section, \
            "Should print variance percentage"

    def test_success_message_includes_story_points(self, tmp_path, azure_config_yaml):
        """Test that success message includes story points verification."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Get verification section
        verification_pos = rendered.find("Verifying Epic Decomposition Hierarchy")
        verification_section = rendered[verification_pos:]

        # Success message should mention story points
        assert "Story points sum correctly across hierarchy" in verification_section, \
            "Success message should mention story points verification"

    def test_story_point_verification_handles_missing_fields(self, tmp_path, azure_config_yaml):
        """Test that story point verification handles missing story point fields gracefully."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Get verification section
        verification_pos = rendered.find("Verifying Epic Decomposition Hierarchy")
        verification_section = rendered[verification_pos:]

        # Should use .get() with default 0
        assert ".get(story_point_field, 0) or 0" in verification_section, \
            "Should use .get() with default 0 for missing story point fields"

    def test_story_point_verification_uses_try_except(self, tmp_path, azure_config_yaml):
        """Test that story point verification uses try-except for adapter queries."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Get verification section
        verification_pos = rendered.find("Verifying Epic Decomposition Hierarchy")
        verification_section = rendered[verification_pos:]
        story_points_pos = verification_section.find("Verifying story point summation")
        story_points_section = verification_section[story_points_pos:story_points_pos + 3000]

        # Should use try-except for adapter queries
        assert "try:" in story_points_section, \
            "Story point verification should use try-except"
        assert "except Exception as e:" in story_points_section, \
            "Should catch exceptions in story point verification"

    def test_story_point_verification_works_with_file_based_adapter(self, tmp_path, filebased_config_yaml):
        """Test that story point verification works with file-based adapter."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(filebased_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Get verification section
        verification_pos = rendered.find("Verifying Epic Decomposition Hierarchy")
        verification_section = rendered[verification_pos:]

        # Should have story point verification (even for file-based)
        assert "Verifying story point summation" in verification_section, \
            "Should have story point verification for file-based adapter"

        # Should use generic adapter methods
        assert "adapter.get_work_item(" in verification_section, \
            "Should use generic adapter.get_work_item()"

    def test_story_point_verification_wrapped_in_jinja_if(self, tmp_path, azure_config_yaml):
        """Test that story point verification is wrapped in Jinja if statement."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        # Read template source (not rendered)
        template_path = Path(__file__).parent.parent.parent / "workflows" / "templates" / "backlog-grooming.j2"
        template_source = template_path.read_text(encoding='utf-8')

        # Get verification section from template
        verification_pos = template_source.find("Verifying Epic Decomposition Hierarchy")
        verification_section = template_source[verification_pos:verification_pos + 5000]

        # Story point verification should be wrapped in Jinja if
        assert "{% if work_tracking.custom_fields.story_points %}" in verification_section, \
            "Story point verification should be wrapped in Jinja if statement"


@pytest.mark.integration
class TestBacklogGroomingChecklistOutput:
    """Test suite for verification checklist output in backlog-grooming workflow."""

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
    def no_story_points_config_yaml(self):
        """Sample configuration without story points."""
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

    def test_checklist_section_exists_after_verification(self, tmp_path, azure_config_yaml):
        """Test that checklist section exists after verification completes."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Should have checklist section
        assert "Epic Decomposition Verification Checklist" in rendered, \
            "Checklist section missing"

        # Should be after verification section
        verification_pos = rendered.find("Verifying Epic Decomposition Hierarchy")
        checklist_pos = rendered.find("Epic Decomposition Verification Checklist")

        assert verification_pos < checklist_pos, \
            "Checklist should be after verification section"

    def test_checklist_includes_epic_decomposition_item(self, tmp_path, azure_config_yaml):
        """Test that checklist includes Epic decomposition item with format: '- [x] Epic WI-{id} decomposed into {n} Features'."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Get checklist section
        checklist_pos = rendered.find("Epic Decomposition Verification Checklist")
        checklist_section = rendered[checklist_pos:checklist_pos + 2000]

        # Should have Epic decomposition item with correct format
        assert "- [x] Epic WI-{epic_id} decomposed into {len(created_features)} Features" in checklist_section, \
            "Checklist missing Epic decomposition item with correct format"

    def test_checklist_includes_features_created_with_child_count(self, tmp_path, azure_config_yaml):
        """Test that checklist includes Features created item with child count."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Get checklist section
        checklist_pos = rendered.find("Epic Decomposition Verification Checklist")
        checklist_section = rendered[checklist_pos:checklist_pos + 2000]

        # Should have Features created header
        assert "- [x] Features created:" in checklist_section, \
            "Checklist missing Features created item"

        # Should iterate over Features and show child count
        assert "for feature_info in created_features:" in checklist_section, \
            "Checklist should iterate over created_features"

        # Should show Feature ID, title, and task count
        assert "Feature WI-{feature_info['id']}" in checklist_section, \
            "Should show Feature ID"
        assert "{feature_info['title']}" in checklist_section, \
            "Should show Feature title"
        assert "({task_count} Tasks)" in checklist_section, \
            "Should show Task count"

    def test_checklist_includes_tasks_created_per_feature(self, tmp_path, azure_config_yaml):
        """Test that checklist includes Tasks created per Feature."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Get checklist section
        checklist_pos = rendered.find("Epic Decomposition Verification Checklist")
        checklist_section = rendered[checklist_pos:checklist_pos + 2000]

        # Should calculate total tasks
        assert "total_tasks = sum(f.get('expected_tasks', 0) for f in created_features)" in checklist_section, \
            "Should calculate total tasks"

        # Should show total tasks created
        assert "- [x] {total_tasks} Tasks created across {len(created_features)} Features" in checklist_section, \
            "Should show total Tasks created"

    def test_checklist_includes_story_points_validation(self, tmp_path, azure_config_yaml):
        """Test that checklist includes story points validation item."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Get checklist section
        checklist_pos = rendered.find("Epic Decomposition Verification Checklist")
        checklist_section = rendered[checklist_pos:checklist_pos + 2000]

        # Should have story points validation item
        assert "Story points validated" in checklist_section, \
            "Checklist should include story points validation"

        # Should check for mismatches
        assert "if story_point_mismatches:" in checklist_section, \
            "Should check story_point_mismatches"

        # Should show [x] if no mismatches, [ ] if mismatches found
        assert "- [x] Story points validated (all variances within 20% threshold)" in checklist_section, \
            "Should show [x] for successful validation"
        assert "- [ ] Story points validated (WARNING: {len(story_point_mismatches)} mismatches found)" in checklist_section, \
            "Should show [ ] for failed validation"

    def test_checklist_includes_acceptance_criteria_validation(self, tmp_path, azure_config_yaml):
        """Test that checklist includes acceptance criteria validation item."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Get checklist section
        checklist_pos = rendered.find("Epic Decomposition Verification Checklist")
        checklist_section = rendered[checklist_pos:checklist_pos + 2000]

        # Should have acceptance criteria validation
        assert "Acceptance criteria validated" in checklist_section, \
            "Checklist should include acceptance criteria validation"

        # Should query Features for acceptance criteria
        assert "features_with_ac = 0" in checklist_section, \
            "Should initialize acceptance criteria counter"

        # Should query each Feature
        assert "adapter.get_work_item(feature_info['id'])" in checklist_section, \
            "Should query each Feature for acceptance criteria"

        # Should check Microsoft.VSTS.Common.AcceptanceCriteria field
        assert "Microsoft.VSTS.Common.AcceptanceCriteria" in checklist_section, \
            "Should check AcceptanceCriteria field"

    def test_checklist_uses_checkmark_for_completed_items(self, tmp_path, azure_config_yaml):
        """Test that checklist uses [x] for completed items."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Get checklist section
        checklist_pos = rendered.find("Epic Decomposition Verification Checklist")
        checklist_section = rendered[checklist_pos:checklist_pos + 2000]

        # Should use [x] for completed items
        assert "- [x] Epic WI-" in checklist_section, \
            "Should use [x] for Epic decomposition"
        assert "- [x] Features created:" in checklist_section, \
            "Should use [x] for Features created"
        assert "- [x] {total_tasks} Tasks created" in checklist_section, \
            "Should use [x] for Tasks created"

    def test_checklist_uses_empty_checkbox_for_incomplete_items(self, tmp_path, azure_config_yaml):
        """Test that checklist uses [ ] for incomplete/skipped items."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Get checklist section
        checklist_pos = rendered.find("Epic Decomposition Verification Checklist")
        checklist_section = rendered[checklist_pos:checklist_pos + 2000]

        # Should use [ ] for incomplete items
        assert "- [ ] Story points validated (WARNING:" in checklist_section, \
            "Should use [ ] for failed story points validation"
        assert "- [ ] Acceptance criteria validated (0/" in checklist_section, \
            "Should use [ ] for missing acceptance criteria"

    def test_checklist_uses_partial_checkbox_for_partially_complete(self, tmp_path, azure_config_yaml):
        """Test that checklist uses [~] for partially complete items."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Get checklist section
        checklist_pos = rendered.find("Epic Decomposition Verification Checklist")
        checklist_section = rendered[checklist_pos:checklist_pos + 2000]

        # Should use [~] for partially complete acceptance criteria
        assert "- [~] Acceptance criteria partially validated" in checklist_section, \
            "Should use [~] for partially validated acceptance criteria"

    def test_checklist_shows_na_for_story_points_when_not_configured(self, tmp_path, no_story_points_config_yaml):
        """Test that checklist shows N/A for story points when not configured."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(no_story_points_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Get checklist section
        checklist_pos = rendered.find("Epic Decomposition Verification Checklist")
        checklist_section = rendered[checklist_pos:checklist_pos + 2000]

        # Should show N/A when story points not configured
        assert "- [ ] Story points validated (N/A - story points not configured)" in checklist_section, \
            "Should show N/A for story points when not configured"

    def test_checklist_format_matches_epic_requirements(self, tmp_path, azure_config_yaml):
        """Test that checklist format matches example in Epic requirements."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Get checklist section
        checklist_pos = rendered.find("Epic Decomposition Verification Checklist")
        checklist_section = rendered[checklist_pos:checklist_pos + 2000]

        # Should match format: "- [x] Epic WI-{id} decomposed into {count} Features"
        assert "- [x] Epic WI-{epic_id} decomposed into {len(created_features)} Features" in checklist_section, \
            "Format should match Epic requirements"

    def test_human_approval_gate_exists(self, tmp_path, azure_config_yaml):
        """Test that human approval gate is added after checklist."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Get section after checklist
        checklist_pos = rendered.find("Epic Decomposition Verification Checklist")
        approval_section = rendered[checklist_pos:checklist_pos + 3000]

        # Should have human approval gate
        assert "HUMAN REVIEW REQUIRED" in approval_section, \
            "Human approval gate missing"

    def test_approval_gate_prompts_for_proceed_input(self, tmp_path, azure_config_yaml):
        """Test that approval gate prompts for 'proceed' input."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Get approval gate section
        checklist_pos = rendered.find("Epic Decomposition Verification Checklist")
        approval_section = rendered[checklist_pos:checklist_pos + 3000]

        # Should prompt for input
        assert "input(" in approval_section, \
            "Should prompt for user input"

        # Should mention 'proceed'
        assert "Type 'proceed' to continue" in approval_section, \
            "Should mention 'proceed' in prompt"

        # Should mention 'skip'
        assert "or 'skip' to end grooming" in approval_section, \
            "Should mention 'skip' in prompt"

    def test_approval_gate_handles_proceed_input(self, tmp_path, azure_config_yaml):
        """Test that approval gate handles 'proceed' input."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Get approval gate section
        checklist_pos = rendered.find("Epic Decomposition Verification Checklist")
        approval_section = rendered[checklist_pos:checklist_pos + 3000]

        # Should check for 'proceed'
        assert "approval = input(" in approval_section, \
            "Should capture user input"
        # Check logic: if skip, elif not proceed (invalid), else (proceed)
        assert "elif approval != 'proceed':" in approval_section, \
            "Should check for non-'proceed' input"

        # Should continue on 'proceed'
        assert "Continuing to next Epic" in approval_section, \
            "Should continue on 'proceed'"

    def test_approval_gate_handles_skip_input(self, tmp_path, azure_config_yaml):
        """Test that approval gate handles 'skip' input."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Get approval gate section
        checklist_pos = rendered.find("Epic Decomposition Verification Checklist")
        approval_section = rendered[checklist_pos:checklist_pos + 3000]

        # Should check for 'skip'
        assert "approval == 'skip'" in approval_section, \
            "Should check for 'skip' input"

        # Should end grooming on 'skip'
        assert "Backlog grooming ended by user" in approval_section, \
            "Should end grooming on 'skip'"

        # Should break out of Epic loop
        assert "break" in approval_section, \
            "Should break out of Epic loop on 'skip'"

    def test_approval_gate_handles_invalid_input(self, tmp_path, azure_config_yaml):
        """Test that approval gate handles invalid input."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Get approval gate section
        checklist_pos = rendered.find("Epic Decomposition Verification Checklist")
        approval_section = rendered[checklist_pos:checklist_pos + 3000]

        # Should handle invalid input
        assert "elif approval != 'proceed':" in approval_section, \
            "Should check for invalid input"

        # Should end with error on invalid input
        assert "Invalid input. Backlog grooming ended." in approval_section, \
            "Should end with error on invalid input"

    def test_checklist_and_approval_gate_order(self, tmp_path, azure_config_yaml):
        """Test that checklist comes before approval gate."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Find positions
        checklist_pos = rendered.find("Epic Decomposition Verification Checklist")
        approval_pos = rendered.find("HUMAN REVIEW REQUIRED")

        # Checklist should come before approval gate
        assert checklist_pos < approval_pos, \
            "Checklist should come before approval gate"

    def test_acceptance_criteria_validation_handles_errors(self, tmp_path, azure_config_yaml):
        """Test that acceptance criteria validation handles errors gracefully."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Get checklist section
        checklist_pos = rendered.find("Epic Decomposition Verification Checklist")
        checklist_section = rendered[checklist_pos:checklist_pos + 2000]

        # Should use try-except for acceptance criteria queries
        assert "try:" in checklist_section, \
            "Should use try-except for acceptance criteria queries"
        assert "except:" in checklist_section, \
            "Should catch exceptions gracefully"
        assert "pass" in checklist_section, \
            "Should pass on exception (don't fail verification)"
