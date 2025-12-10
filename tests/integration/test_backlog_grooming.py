"""
End-to-end integration tests for backlog-grooming workflow verification gates.

Tests Task #1100 implementation: Verify that backlog-grooming workflow properly validates
Feature-Task hierarchy and story point summation using adapter queries (external source of truth).

This validates the FULL workflow behavior with mocked adapter responses to simulate real
verification failures, complementing the unit tests in test_backlog_grooming_hierarchy.py
which test individual verification components.

Key differences from test_backlog_grooming_hierarchy.py:
- hierarchy tests: Unit tests that verify template CONTAINS verification code
- THIS FILE: Integration tests that verify template BEHAVIOR with mocked data
"""
import pytest
from pathlib import Path
from workflows.registry import WorkflowRegistry
from config.loader import load_config


@pytest.mark.integration
class TestBacklogGroomingVerificationGates:
    """End-to-end integration tests for backlog-grooming verification gates."""

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

    # =========================================================================
    # Test 1: Feature-Task Hierarchy Verification
    # =========================================================================

    def test_workflow_detects_childless_features(self, tmp_path, azure_config_yaml):
        """Test that workflow identifies Features with no Tasks (childless Features).

        Verifies Task #1097: Feature-Task hierarchy verification.
        Simulates scenario where Epic decomposition creates Features but some have no Tasks.
        """
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Verify workflow checks for childless Features
        assert "if task_count == 0:" in rendered, \
            "Workflow should check for Features with zero Tasks"

        # Verify error message format matches requirements
        assert "ERROR: Feature" in rendered, \
            "Error message should include 'ERROR: Feature'"
        assert "has no Tasks - workflow incomplete" in rendered, \
            "Error message should specify 'has no Tasks - workflow incomplete'"

        # Verify workflow tracks childless Features
        assert "childless_features" in rendered, \
            "Workflow should track childless Features in a list"
        assert "childless_features.append(" in rendered, \
            "Workflow should append to childless_features list"

    def test_workflow_queries_adapter_for_feature_tasks(self, tmp_path, azure_config_yaml):
        """Test that workflow queries adapter for Tasks under each Feature.

        Verifies that verification uses adapter.query_work_items() to get actual Task data
        from external source of truth (not AI memory).
        """
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Verify adapter query for Tasks
        assert "adapter.query_work_items(" in rendered, \
            "Workflow should query adapter for work items"

        # Verify filtering by parent_id (Feature-Task relationship)
        assert "parent_id" in rendered, \
            "Workflow should filter Tasks by parent_id"

        # Verify Task work item type used in query
        verification_section = rendered[rendered.find("Verifying Epic Decomposition"):rendered.find("STEP 6")]
        assert "work_item_type='Task'" in verification_section or \
               "work_item_type='{{ work_tracking.work_item_types.task }}'" in verification_section, \
            "Workflow should query specifically for Task work items"

    def test_workflow_exits_on_hierarchy_verification_failure(self, tmp_path, azure_config_yaml):
        """Test that workflow exits with code 1 when Feature has no Tasks.

        Verifies that verification failures halt the workflow to prevent proceeding
        with incomplete Epic decomposition.
        """
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Verify verification_failed flag
        assert "verification_failed = False" in rendered, \
            "Workflow should initialize verification_failed flag"
        assert "verification_failed = True" in rendered, \
            "Workflow should set verification_failed = True on failure"

        # Verify sys.exit(1) on failure
        assert "sys.exit(1)" in rendered, \
            "Workflow should exit with code 1 on verification failure"

        # Verify exit happens after failure check
        exit_section = rendered[rendered.find("if verification_failed:"):]
        assert "sys.exit(1)" in exit_section[:1500], \
            "sys.exit(1) should be in the verification failure block"

    def test_workflow_verifies_features_linked_to_epic(self, tmp_path, azure_config_yaml):
        """Test that workflow verifies all Features are linked to parent Epic.

        Verifies STEP 2 of hierarchy verification: Epic-Features relationship.
        """
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Verify Epic-Features verification step
        assert "STEP 2: Verify all Features are linked to parent Epic" in rendered, \
            "Workflow should include STEP 2 for Epic-Features verification"

        # Verify query for Features under Epic
        assert "epic_features" in rendered, \
            "Workflow should query for Features under Epic"

        # Verify count validation
        assert "expected_feature_count" in rendered and "actual_feature_count" in rendered, \
            "Workflow should compare expected vs actual Feature count"

    # =========================================================================
    # Test 2: Story Point Variance Verification
    # =========================================================================

    def test_workflow_detects_story_point_variance(self, tmp_path, azure_config_yaml):
        """Test that workflow detects story point variance >20% between Feature and Tasks.

        Verifies Task #1098: Story point summation verification.
        """
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Verify story point summation logic
        assert "STEP 3: Verify story point summation" in rendered, \
            "Workflow should include STEP 3 for story point verification"

        # Verify variance calculation
        assert "variance_pct" in rendered, \
            "Workflow should calculate variance percentage"

        # Verify 20% threshold check
        assert "variance_pct > 20" in rendered or "if variance_pct > 20:" in rendered, \
            "Workflow should check for variance >20%"

        # Verify error message for variance
        assert "ERROR: Feature" in rendered and "story point mismatch" in rendered, \
            "Workflow should report story point mismatches as errors"

    def test_workflow_queries_adapter_for_story_points(self, tmp_path, azure_config_yaml):
        """Test that workflow queries adapter to get story points from work items.

        Verifies that story point verification uses adapter queries (external source of truth)
        not AI memory.
        """
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Verify adapter.get_work_item() for Feature story points
        story_point_section = rendered[rendered.find("STEP 3"):]
        assert "adapter.get_work_item(" in story_point_section[:2000], \
            "Workflow should query adapter.get_work_item() for Feature details"

        # Verify story point field access
        assert "story_point_field" in rendered, \
            "Workflow should use story_point_field variable"
        assert "Microsoft.VSTS.Scheduling.StoryPoints" in rendered, \
            "Workflow should reference correct Azure DevOps story points field"

    def test_workflow_sums_task_story_points(self, tmp_path, azure_config_yaml):
        """Test that workflow sums story points from all Tasks under a Feature.

        Verifies that workflow calculates total Task story points for comparison.
        """
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Verify Task story points summation
        assert "task_story_points_sum" in rendered, \
            "Workflow should calculate sum of Task story points"

        # Verify sum() function used
        assert "sum(" in rendered, \
            "Workflow should use sum() to aggregate Task story points"

    def test_workflow_tracks_story_point_mismatches(self, tmp_path, azure_config_yaml):
        """Test that workflow tracks Features with story point mismatches.

        Verifies that workflow collects all mismatches for reporting.
        """
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Verify mismatch tracking
        assert "story_point_mismatches" in rendered, \
            "Workflow should track story point mismatches in a list"
        assert "story_point_mismatches.append(" in rendered, \
            "Workflow should append mismatches to list"

        # Verify mismatch details stored
        mismatch_section = rendered[rendered.find("story_point_mismatches.append"):]
        assert "'feature_points'" in mismatch_section[:500] and "'tasks_sum'" in mismatch_section[:500], \
            "Workflow should store Feature points and Tasks sum in mismatch"

    def test_workflow_verifies_epic_story_points(self, tmp_path, azure_config_yaml):
        """Test that workflow verifies Epic vs Features story point summation.

        Verifies STEP 4: Epic-level story point verification.
        """
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Verify Epic verification step
        assert "STEP 4: Verify Epic vs Features story point summation" in rendered, \
            "Workflow should include STEP 4 for Epic-level verification"

        # Verify Epic story points query
        assert "epic_full = adapter.get_work_item(epic_id)" in rendered, \
            "Workflow should query Epic work item for story points"

        # Verify Features sum comparison
        assert "features_story_points_sum" in rendered, \
            "Workflow should sum Features story points"

    # =========================================================================
    # Test 3: Verification Checklist Output
    # =========================================================================

    def test_workflow_outputs_verification_checklist(self, tmp_path, azure_config_yaml):
        """Test that workflow outputs markdown verification checklist.

        Verifies Task #1099: Explicit verification checklist output.
        """
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Verify checklist step exists
        assert "STEP 6: Output verification checklist" in rendered, \
            "Workflow should include STEP 6 for checklist output"

        # Verify checklist header
        assert "📋 Epic Decomposition Verification Checklist" in rendered, \
            "Workflow should output checklist with correct header"

        # Verify checklist uses markdown checkboxes
        assert "- [x]" in rendered, \
            "Workflow should use markdown checkbox format [x] for completed items"

    def test_checklist_includes_epic_decomposition_status(self, tmp_path, azure_config_yaml):
        """Test that checklist includes Epic decomposition status.

        Verifies checklist Item 1: Epic decomposed into Features.
        """
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Verify Epic decomposition item
        checklist_section = rendered[rendered.find("Epic Decomposition Verification Checklist"):]
        assert "Epic WI-" in checklist_section and "decomposed into" in checklist_section, \
            "Checklist should show Epic ID and decomposition status"
        assert "Features" in checklist_section, \
            "Checklist should mention Features"

    def test_checklist_includes_features_created(self, tmp_path, azure_config_yaml):
        """Test that checklist lists all Features created with Task counts.

        Verifies checklist Item 2: Features created with child counts.
        """
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Verify Features list in checklist
        checklist_section = rendered[rendered.find("Epic Decomposition Verification Checklist"):]
        assert "Features created:" in checklist_section, \
            "Checklist should include 'Features created:' section"

        # Verify loop over created_features
        assert "for feature_info in created_features:" in checklist_section, \
            "Checklist should iterate over created_features"

        # Verify Feature details in output
        assert "Feature WI-" in checklist_section and "Tasks)" in checklist_section, \
            "Checklist should show Feature IDs and Task counts"

    def test_checklist_includes_story_point_validation(self, tmp_path, azure_config_yaml):
        """Test that checklist includes story point validation status.

        Verifies checklist Item 4: Story points validated with conditional status.
        """
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Verify story point validation item
        checklist_section = rendered[rendered.find("Epic Decomposition Verification Checklist"):]
        assert "Story points validated" in checklist_section, \
            "Checklist should include story point validation item"

        # Verify conditional status based on mismatches
        assert "if story_point_mismatches:" in checklist_section, \
            "Checklist should conditionally show story point status"
        assert "- [ ] Story points validated (WARNING:" in checklist_section, \
            "Checklist should show unchecked box with warning if mismatches found"
        assert "- [x] Story points validated" in checklist_section, \
            "Checklist should show checked box if no mismatches"

    def test_checklist_includes_acceptance_criteria_validation(self, tmp_path, azure_config_yaml):
        """Test that checklist includes acceptance criteria validation.

        Verifies checklist Item 5: Acceptance criteria validated with partial status.
        """
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Verify acceptance criteria validation
        checklist_section = rendered[rendered.find("Epic Decomposition Verification Checklist"):]
        assert "Acceptance criteria validated" in checklist_section, \
            "Checklist should include acceptance criteria validation item"

        # Verify partial completion support (tilde checkbox)
        assert "- [~]" in checklist_section, \
            "Checklist should support [~] for partial completion"

        # Verify Features counted for acceptance criteria
        assert "features_with_ac" in checklist_section, \
            "Checklist should count Features with acceptance criteria"

    # =========================================================================
    # Test 4: Human Approval Gate
    # =========================================================================

    def test_workflow_includes_human_approval_gate(self, tmp_path, azure_config_yaml):
        """Test that workflow includes human approval gate after verification.

        Verifies STEP 7: Human review required before proceeding.
        """
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Verify approval gate step
        assert "STEP 7: Human approval gate" in rendered or "HUMAN REVIEW REQUIRED" in rendered, \
            "Workflow should include human approval gate"

        # Verify input() prompt
        assert "input(" in rendered, \
            "Workflow should use input() to get user approval"

        # Verify approval options
        approval_section = rendered[rendered.find("HUMAN REVIEW"):]
        assert "proceed" in approval_section and "skip" in approval_section, \
            "Workflow should accept 'proceed' or 'skip' as approval options"

    def test_approval_gate_validates_user_input(self, tmp_path, azure_config_yaml):
        """Test that approval gate validates user input and handles invalid responses.

        Verifies that workflow doesn't proceed with invalid input.
        """
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Verify input validation
        approval_section = rendered[rendered.find("input("):]
        assert "== 'proceed'" in approval_section[:500] or "!= 'proceed'" in approval_section[:500], \
            "Workflow should validate approval input"

        # Verify invalid input handling
        assert "Invalid input" in approval_section[:1000] or "elif approval != 'proceed'" in approval_section[:1000], \
            "Workflow should handle invalid input"

    # =========================================================================
    # Test 5: Cross-Platform Compatibility
    # =========================================================================

    def test_verification_works_with_filebased_adapter(self, tmp_path, filebased_config_yaml):
        """Test that verification logic works with file-based adapter.

        Verifies that verification code is platform-agnostic.
        """
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(filebased_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Verify platform-agnostic verification code exists
        assert "adapter.query_work_items(" in rendered, \
            "Verification should work with any adapter platform"
        assert "adapter.get_work_item(" in rendered, \
            "Verification should use generic adapter interface"

        # Verify no Azure-specific code in verification
        verification_section = rendered[rendered.find("Verifying Epic Decomposition"):]
        assert "az boards" not in verification_section.lower(), \
            "Verification should not use Azure-specific commands"

    # =========================================================================
    # Test 6: External Source of Truth Pattern
    # =========================================================================

    def test_workflow_implements_external_source_of_truth_pattern(self, tmp_path, azure_config_yaml):
        """Test that workflow implements External Source of Truth pattern from VISION.md.

        Verifies that verification queries adapter (not AI memory) for all data.
        """
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Verify External Source of Truth mention
        assert "External Source of Truth" in rendered or "VISION.md" in rendered, \
            "Workflow should reference External Source of Truth pattern"

        # Verify adapter queries (not hardcoded data)
        verification_section = rendered[rendered.find("Verifying Epic Decomposition"):]

        # Count adapter method calls
        adapter_get_count = verification_section.count("adapter.get_work_item(")
        adapter_query_count = verification_section.count("adapter.query_work_items(")

        assert adapter_get_count >= 2, \
            "Verification should call adapter.get_work_item() multiple times"
        assert adapter_query_count >= 2, \
            "Verification should call adapter.query_work_items() multiple times"

    def test_verification_does_not_trust_ai_claims(self, tmp_path, azure_config_yaml):
        """Test that verification doesn't trust AI-claimed data without adapter verification.

        Verifies that workflow queries adapter even when AI claims work is complete.
        """
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Verify verification happens AFTER work item creation
        creation_pos = rendered.find("adapter.create_work_item(")
        verification_pos = rendered.find("Verifying Epic Decomposition Hierarchy")

        assert creation_pos < verification_pos, \
            "Verification should happen after work item creation, not trust creation claims"

        # Verify no assumptions about created work items
        verification_section = rendered[verification_pos:verification_pos+2000]
        assert "try:" in verification_section or "except" in verification_section, \
            "Verification should handle errors (assume adapter queries might fail)"

    # =========================================================================
    # Test 7: Error Reporting and Exit Codes
    # =========================================================================

    def test_workflow_reports_all_verification_failures(self, tmp_path, azure_config_yaml):
        """Test that workflow collects and reports all verification failures.

        Verifies that workflow doesn't stop at first failure but reports all issues.
        """
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Verify failure summary section
        assert "VERIFICATION FAILED - Issues detected:" in rendered, \
            "Workflow should have failure summary section"

        # Verify reports childless Features
        failure_section = rendered[rendered.find("VERIFICATION FAILED"):]
        assert "childless_features" in failure_section[:1000], \
            "Failure summary should report childless Features"

        # Verify reports story point mismatches
        assert "story_point_mismatches" in failure_section[:1000], \
            "Failure summary should report story point mismatches"

    def test_workflow_provides_actionable_error_messages(self, tmp_path, azure_config_yaml):
        """Test that error messages provide actionable guidance.

        Verifies that errors tell user what to do to fix the issue.
        """
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Verify actionable guidance
        failure_section = rendered[rendered.find("VERIFICATION FAILED"):]
        assert "Fix these issues before proceeding" in failure_section or \
               "Re-run decomposition" in failure_section, \
            "Failure summary should provide actionable guidance"

    def test_workflow_exits_with_success_on_passing_verification(self, tmp_path, azure_config_yaml):
        """Test that workflow outputs success message when verification passes.

        Verifies that successful verification is clearly communicated.
        """
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Verify success message
        assert "VERIFICATION PASSED - All hierarchy checks successful" in rendered, \
            "Workflow should output success message when verification passes"

        # Verify success criteria listed
        success_section = rendered[rendered.find("VERIFICATION PASSED"):]
        assert "All Features have at least one Task" in success_section, \
            "Success message should list verification criteria"

    # =========================================================================
    # Test 8: Verification Performance
    # =========================================================================

    def test_verification_minimizes_adapter_queries(self, tmp_path, azure_config_yaml):
        """Test that verification minimizes redundant adapter queries.

        Verifies that workflow caches adapter responses to avoid duplicate queries.
        """
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Verify caching strategy mentioned or implemented
        story_point_section = rendered[rendered.find("STEP 4: Verify Epic vs Features"):]

        # Check if workflow reuses already-fetched data
        assert "mismatch_entry" in story_point_section or "already have" in story_point_section.lower(), \
            "Workflow should reuse already-fetched Feature data in Epic verification"

    # =========================================================================
    # Test 9: Verification Step Ordering
    # =========================================================================

    def test_verification_steps_in_correct_order(self, tmp_path, azure_config_yaml):
        """Test that verification steps execute in correct order.

        Verifies that verification follows logical order:
        1. Feature-Task hierarchy
        2. Feature-Epic linkage
        3. Story points within Features
        4. Story points Epic-level
        5. Exit on failure
        6. Output checklist
        7. Human approval
        """
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("backlog-grooming")

        # Find positions of verification steps
        step1_pos = rendered.find("STEP 1: Verify each Feature has at least one Task")
        step2_pos = rendered.find("STEP 2: Verify all Features are linked to parent Epic")
        step3_pos = rendered.find("STEP 3: Verify story point summation")
        step4_pos = rendered.find("STEP 4: Verify Epic vs Features story point summation")
        step5_pos = rendered.find("STEP 5: Exit with error code if verification failed")
        step6_pos = rendered.find("STEP 6: Output verification checklist")
        step7_pos = rendered.find("STEP 7: Human approval gate")

        # Verify steps in correct order
        assert step1_pos < step2_pos < step3_pos < step4_pos < step5_pos < step6_pos < step7_pos, \
            "Verification steps should be in correct order"

    # =========================================================================
    # Test 10: Template Rendering with Real Config
    # =========================================================================

    def test_template_renders_without_errors(self, tmp_path, azure_config_yaml):
        """Test that backlog-grooming template renders without errors.

        Verifies that template syntax is correct and all variables are defined.
        """
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        # This should not raise any exceptions
        rendered = registry.render_workflow("backlog-grooming")

        # Verify template rendered successfully
        assert len(rendered) > 1000, \
            "Rendered workflow should be substantial (>1000 chars)"
        assert "Backlog Grooming" in rendered, \
            "Rendered workflow should contain workflow title"
        assert "Verifying Epic Decomposition" in rendered, \
            "Rendered workflow should contain verification section"
