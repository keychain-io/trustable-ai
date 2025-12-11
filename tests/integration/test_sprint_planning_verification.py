"""
Integration tests for sprint-planning workflow work item existence verification.

Tests Task #1102 implementation: Add work item existence verification to sprint-planning.j2

This implements the "External Source of Truth" pattern from VISION.md Pillar #2:
- AI agents claim work items created when creation failed
- Verification queries adapter (external source of truth) to confirm existence
- Missing work items fail workflow with exit code 1
- Verification happens immediately after creation, not batched at end
"""
import pytest
from pathlib import Path
from workflows.registry import WorkflowRegistry
from config.loader import load_config


@pytest.mark.integration
class TestSprintPlanningWorkItemVerification:
    """Test suite for work item existence verification in sprint-planning workflow."""

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

    def test_verification_step_exists_after_step7(self, tmp_path, azure_config_yaml):
        """Test that Step 7.5 verification step is added after Step 7."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        # Step 7.5 should exist
        assert "Step 7.5: Verify Work Item Creation" in rendered, \
            "Step 7.5 verification step missing"

        # Step 7.5 should come after Step 7 and before Step 8
        step7_pos = rendered.find("Step 7: Work Item Creation")
        step75_pos = rendered.find("Step 7.5: Verify Work Item Creation")
        step8_pos = rendered.find("Step 8: Completion Summary")

        assert step7_pos < step75_pos < step8_pos, \
            "Step 7.5 not positioned correctly between Step 7 and Step 8"

    def test_verification_queries_adapter_get_work_item(self, tmp_path, azure_config_yaml):
        """Test that verification queries adapter.get_work_item() for each created item."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        # Should query adapter for each item
        assert "adapter.get_work_item(item_id)" in rendered, \
            "Verification should query adapter.get_work_item() for each created item"

        # Should iterate over created_items
        verification_section = rendered[rendered.find("Step 7.5"):rendered.find("Step 8")]
        assert "for item_id in created_items:" in verification_section, \
            "Verification should iterate over created_items list"

    def test_verification_collects_verified_and_missing_lists(self, tmp_path, azure_config_yaml):
        """Test that verification collects lists of verified IDs vs claimed IDs."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        verification_section = rendered[rendered.find("Step 7.5"):rendered.find("Step 8")]

        # Should maintain verified_items list
        assert "verified_items = []" in verification_section, \
            "Verification should initialize verified_items list"
        assert "verified_items.append(item_id)" in verification_section, \
            "Verification should append to verified_items when work item exists"

        # Should maintain missing_items list
        assert "missing_items = []" in verification_section, \
            "Verification should initialize missing_items list"
        assert "missing_items.append(item_id)" in verification_section, \
            "Verification should append to missing_items when work item doesn't exist"

    def test_verification_fails_with_exit_code_if_items_missing(self, tmp_path, azure_config_yaml):
        """Test that verification fails with exit code 1 if any claimed item doesn't exist."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        verification_section = rendered[rendered.find("Step 7.5"):rendered.find("Step 8")]

        # Should check if missing_items is non-empty
        assert "if missing_items:" in verification_section, \
            "Verification should check if missing_items list is non-empty"

        # Should import sys and exit with code 1
        assert "import sys" in verification_section, \
            "Verification should import sys module"
        assert "sys.exit(1)" in verification_section, \
            "Verification should call sys.exit(1) when items missing"

        # Should print VERIFICATION FAILED
        assert "VERIFICATION FAILED" in verification_section, \
            "Verification should print VERIFICATION FAILED when items missing"

    def test_verification_outputs_summary(self, tmp_path, azure_config_yaml):
        """Test that verification outputs verification summary showing verified count vs created count."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        verification_section = rendered[rendered.find("Step 7.5"):rendered.find("Step 8")]

        # Should output verification summary
        assert "Verification Summary" in verification_section, \
            "Verification should output summary section"

        # Should show created count
        assert "Created (claimed):" in verification_section or "len(created_items)" in verification_section, \
            "Verification summary should show created/claimed count"

        # Should show verified count
        assert "Verified (confirmed):" in verification_section or "len(verified_items)" in verification_section, \
            "Verification summary should show verified count"

        # Should show missing count
        assert "Missing:" in verification_section or "len(missing_items)" in verification_section, \
            "Verification summary should show missing count"

    def test_verification_checks_work_item_id_matches(self, tmp_path, azure_config_yaml):
        """Test that verification checks work_item.get('id') == item_id."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        verification_section = rendered[rendered.find("Step 7.5"):rendered.find("Step 8")]

        # Should check if work_item exists and ID matches
        assert "work_item.get('id') == item_id" in verification_section, \
            "Verification should check work_item.get('id') == item_id"

        # Should check work_item truthy (not None)
        assert "if work_item and" in verification_section, \
            "Verification should check work_item is not None before accessing id"

    def test_verification_handles_adapter_query_exceptions(self, tmp_path, azure_config_yaml):
        """Test that verification handles adapter query failures gracefully."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        verification_section = rendered[rendered.find("Step 7.5"):rendered.find("Step 8")]

        # Should wrap adapter.get_work_item() in try-except
        assert "try:" in verification_section, \
            "Verification should use try-except for adapter queries"
        assert "except Exception as e:" in verification_section, \
            "Verification should catch Exception for adapter query failures"

        # Should add to missing_items on exception
        exception_handling = verification_section[verification_section.find("except Exception"):verification_section.find("# Output verification summary")]
        assert "missing_items.append(item_id)" in exception_handling, \
            "Verification should add item to missing_items when adapter query throws exception"

    def test_verification_outputs_error_for_each_missing_item(self, tmp_path, azure_config_yaml):
        """Test that verification outputs error message for each missing work item."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        verification_section = rendered[rendered.find("Step 7.5"):rendered.find("Step 8")]

        # Should print error when work item doesn't exist
        assert "claimed created but doesn't exist" in verification_section, \
            "Verification should print error when work item doesn't exist"

        # Should reference adapter.platform
        assert "adapter.platform" in verification_section, \
            "Verification error should reference adapter.platform"

        # Should list missing items when failing
        failure_section = verification_section[verification_section.find("if missing_items:"):]
        assert "for item_id in missing_items:" in failure_section, \
            "Verification should loop through missing_items to display them"

    def test_verification_outputs_success_when_all_verified(self, tmp_path, azure_config_yaml):
        """Test that verification outputs success message when all items verified."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        verification_section = rendered[rendered.find("Step 7.5"):rendered.find("Step 8")]

        # Should have else block for success case
        assert "else:" in verification_section, \
            "Verification should have else block for success case"

        # Should print success message
        success_section = verification_section[verification_section.rfind("else:"):]
        assert "work items verified successfully" in success_section, \
            "Verification should print success message when all items verified"

    def test_verification_works_with_file_based_adapter(self, tmp_path, filebased_config_yaml):
        """Test that verification works with file-based adapter (not just Azure DevOps)."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(filebased_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        verification_section = rendered[rendered.find("Step 7.5"):rendered.find("Step 8")]

        # Should use generic adapter methods (not Azure-specific)
        assert "adapter.get_work_item(" in verification_section, \
            "Verification should use generic adapter.get_work_item()"

        # Should reference adapter.platform generically
        assert "adapter.platform" in verification_section, \
            "Verification should reference adapter.platform generically"

        # Should NOT have Azure DevOps-specific code
        assert "az boards" not in verification_section, \
            "Verification should not have Azure DevOps-specific commands"

    def test_verification_mentions_vision_pattern(self, tmp_path, azure_config_yaml):
        """Test that verification step references VISION.md External Source of Truth pattern."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        verification_section = rendered[rendered.find("Step 7.5"):rendered.find("Step 8")]

        # Should reference VISION.md pattern
        assert "External Source of Truth" in verification_section or "external source of truth" in verification_section, \
            "Verification step should reference External Source of Truth pattern"

        assert "VISION.md" in verification_section or "CRITICAL" in verification_section, \
            "Verification step should reference VISION.md or mark as CRITICAL"

    def test_verification_happens_immediately_after_creation(self, tmp_path, azure_config_yaml):
        """Test that verification happens immediately after Step 7, not batched at end."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        # Step 7.5 should be immediately after Step 7 work item creation
        step7_end = rendered.find('print(f"   Work Item IDs: {\', \'.join(map(str, created_items))}")')
        step75_start = rendered.find("Step 7.5: Verify Work Item Creation")
        step8_start = rendered.find("Step 8: Completion Summary")

        # Step 7.5 should be between Step 7 and Step 8
        assert step7_end < step75_start < step8_start, \
            "Step 7.5 verification should be immediately after Step 7 work item creation"

        # Should not be any other major steps between Step 7 and Step 7.5
        between_7_and_75 = rendered[step7_end:step75_start]
        # Allow for markdown separator but no other "Step" headers
        assert "## Step" not in between_7_and_75.replace("Step 7.5", ""), \
            "No other steps should be between Step 7 and Step 7.5"

    def test_verification_error_message_actionable(self, tmp_path, azure_config_yaml):
        """Test that verification error messages provide actionable guidance."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        verification_section = rendered[rendered.find("Step 7.5"):rendered.find("Step 8")]

        # Should provide actionable guidance on failure
        failure_section = verification_section[verification_section.find("if missing_items:"):]
        assert "indicates work item creation failed" in failure_section.lower() or \
               "creation failed silently" in failure_section.lower(), \
            "Verification should explain what the failure means"

        assert "Check adapter logs" in failure_section or "retry" in failure_section.lower(), \
            "Verification should provide actionable next steps"

    def test_verification_prints_verification_progress(self, tmp_path, azure_config_yaml):
        """Test that verification prints verification progress for each work item."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        verification_section = rendered[rendered.find("Step 7.5"):rendered.find("Step 8")]

        # Should print verification progress header
        assert "Verifying" in verification_section and "created work items exist" in verification_section, \
            "Verification should print header with count and platform"

        # Should print success for each verified item
        verified_output = verification_section[verification_section.find("verified_items.append"):verification_section.find("missing_items.append")]
        assert "Verified: Work Item" in verified_output or "✅" in verified_output, \
            "Verification should print success message for each verified item"

        # Should print error for each missing item
        missing_output = verification_section[verification_section.find("missing_items.append"):verification_section.find("# Output verification summary")]
        assert "ERROR: Work Item" in missing_output or "❌" in missing_output, \
            "Verification should print error message for each missing item"


@pytest.mark.integration
class TestSprintPlanningVerificationEdgeCases:
    """Test edge cases for sprint-planning work item verification."""

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
    feature: "Feature"
    task: "Task"

quality_standards:
  test_coverage_min: 80

agent_config:
  models:
    engineer: "claude-sonnet-4.5"
  enabled_agents:
    - senior-engineer
"""

    def test_verification_handles_empty_created_items(self, tmp_path, azure_config_yaml):
        """Test that verification handles case when created_items is empty."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        verification_section = rendered[rendered.find("Step 7.5"):rendered.find("Step 8")]

        # Should iterate over created_items (handles empty gracefully)
        assert "for item_id in created_items:" in verification_section, \
            "Verification should iterate over created_items"

        # Should print verification header with count (even if 0)
        assert "len(created_items)" in verification_section, \
            "Verification should use len(created_items) in header"

        # Python for loop handles empty list gracefully, no special handling needed

    def test_verification_section_formatting(self, tmp_path, azure_config_yaml):
        """Test that verification section has clear visual formatting."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        verification_section = rendered[rendered.find("Step 7.5"):rendered.find("Step 8")]

        # Should use visual separators
        assert "=" * 80 in verification_section or '="' in verification_section, \
            "Verification should use visual separators for clarity"

        # Should use emojis for visual scanning
        assert "🔍" in verification_section, \
            "Verification should use emoji for verification actions"
        assert "✅" in verification_section, \
            "Verification should use emoji for success"
        assert "❌" in verification_section, \
            "Verification should use emoji for errors"
