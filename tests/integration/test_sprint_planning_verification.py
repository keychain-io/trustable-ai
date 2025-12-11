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

        # Get only Step 7.5 section (not Step 7.6)
        step75_start = rendered.find("Step 7.5: Verify Work Item Creation")
        step76_start = rendered.find("Step 7.6: Validate Work Item Content Quality")
        verification_section = rendered[step75_start:step76_start]

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


@pytest.mark.integration
class TestSprintPlanningContentQualityValidation:
    """Test suite for content quality validation in sprint-planning workflow."""

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

    def test_content_quality_step_exists_after_verification(self, tmp_path, azure_config_yaml):
        """Test that Step 7.6 content quality validation exists after Step 7.5."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        # Step 7.6 should exist
        assert "Step 7.6: Validate Work Item Content Quality" in rendered, \
            "Step 7.6 content quality validation step missing"

        # Step 7.6 should come after Step 7.5 and before Step 8
        step75_pos = rendered.find("Step 7.5: Verify Work Item Creation")
        step76_pos = rendered.find("Step 7.6: Validate Work Item Content Quality")
        step8_pos = rendered.find("Step 8: Completion Summary")

        assert step75_pos < step76_pos < step8_pos, \
            "Step 7.6 not positioned correctly between Step 7.5 and Step 8"

    def test_queries_adapter_for_each_verified_work_item(self, tmp_path, azure_config_yaml):
        """Test that content quality validation queries adapter for each verified work item."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        quality_section = rendered[rendered.find("Step 7.6"):rendered.find("Step 8")]

        # Should iterate over verified_items (from Step 7.5)
        assert "for item_id in verified_items:" in quality_section, \
            "Content quality validation should iterate over verified_items"

        # Should query adapter for full work item details
        assert "adapter.get_work_item(item_id)" in quality_section, \
            "Content quality validation should query adapter.get_work_item()"

    def test_validates_description_length_500_chars(self, tmp_path, azure_config_yaml):
        """Test that validation checks description >= 500 characters."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        quality_section = rendered[rendered.find("Step 7.6"):rendered.find("Step 8")]

        # Should get description field
        assert "fields.get('System.Description'" in quality_section, \
            "Validation should get System.Description field"

        # Should check description length >= 500
        assert "description_length < 500" in quality_section, \
            "Validation should check description length < 500"

        # Should track this as a quality issue
        assert "description too short" in quality_section, \
            "Validation should record 'description too short' issue"

    def test_validates_acceptance_criteria_count_3(self, tmp_path, azure_config_yaml):
        """Test that validation checks acceptance criteria >= 3."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        quality_section = rendered[rendered.find("Step 7.6"):rendered.find("Step 8")]

        # Should get acceptance criteria field
        assert "fields.get('Microsoft.VSTS.Common.AcceptanceCriteria'" in quality_section, \
            "Validation should get Microsoft.VSTS.Common.AcceptanceCriteria field"

        # Should check criteria count >= 3
        assert "criteria_count < 3" in quality_section, \
            "Validation should check criteria_count < 3"

        # Should track this as a quality issue
        assert "insufficient acceptance criteria" in quality_section, \
            "Validation should record 'insufficient acceptance criteria' issue"

    def test_strips_html_from_description_before_counting(self, tmp_path, azure_config_yaml):
        """Test that validation strips HTML tags from description before counting characters."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        quality_section = rendered[rendered.find("Step 7.6"):rendered.find("Step 8")]

        # Should import re module
        assert "import re" in quality_section, \
            "Validation should import re module for HTML stripping"

        # Should strip HTML tags using regex
        assert "re.sub('<[^<]+?>', '', description)" in quality_section, \
            "Validation should strip HTML tags using re.sub()"

        # Should count stripped text length
        assert "description_text = re.sub" in quality_section, \
            "Validation should assign stripped text to variable"
        assert "len(description_text.strip())" in quality_section, \
            "Validation should count length of stripped text"

    def test_counts_acceptance_criteria_lines_correctly(self, tmp_path, azure_config_yaml):
        """Test that validation counts acceptance criteria lines (checkboxes and numbered)."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        quality_section = rendered[rendered.find("Step 7.6"):rendered.find("Step 8")]

        # Should count lines starting with "- [ ]"
        assert "startswith('- [ ]')" in quality_section, \
            "Validation should count lines starting with '- [ ]'"

        # Should count lines starting with "- [x]"
        assert "startswith('- [x]')" in quality_section, \
            "Validation should count lines starting with '- [x]'"

        # Should count numbered lines (1., 2., etc.)
        assert r"re.match(r'^\d+\.'" in quality_section, \
            "Validation should count numbered lines using re.match()"

        # Should count criteria lines
        assert "criteria_count = len(criteria_lines)" in quality_section, \
            "Validation should count number of criteria lines"

    def test_detects_description_too_short(self, tmp_path, azure_config_yaml):
        """Test that validation detects when description < 500 characters."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        quality_section = rendered[rendered.find("Step 7.6"):rendered.find("Step 8")]

        # Should append to issues list when description too short
        assert "if description_length < 500:" in quality_section, \
            "Validation should check if description_length < 500"

        # Should record issue with character count
        assert "description too short" in quality_section and "{description_length}" in quality_section, \
            "Validation should record description too short with character count"

    def test_detects_insufficient_acceptance_criteria(self, tmp_path, azure_config_yaml):
        """Test that validation detects when acceptance criteria < 3."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        quality_section = rendered[rendered.find("Step 7.6"):rendered.find("Step 8")]

        # Should append to issues list when criteria count < 3
        assert "if criteria_count < 3:" in quality_section, \
            "Validation should check if criteria_count < 3"

        # Should record issue with criteria count
        assert "insufficient acceptance criteria" in quality_section and "{criteria_count}" in quality_section, \
            "Validation should record insufficient criteria with count"

    def test_detects_multiple_issues_per_work_item(self, tmp_path, azure_config_yaml):
        """Test that validation can detect both description and AC issues for same work item."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        quality_section = rendered[rendered.find("Step 7.6"):rendered.find("Step 8")]

        # Should use issues list to collect multiple issues
        assert "issues = []" in quality_section, \
            "Validation should initialize issues list"

        # Should append both types of issues to same list
        assert "issues.append(" in quality_section, \
            "Validation should append issues to issues list"

        # Should check if issues list is non-empty before adding to quality_issues
        assert "if issues:" in quality_section, \
            "Validation should check if issues list has items"

    def test_fails_with_exit_code_1_when_quality_issues_found(self, tmp_path, azure_config_yaml):
        """Test that validation fails with exit code 1 when any quality issues found."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        quality_section = rendered[rendered.find("Step 7.6"):rendered.find("Step 8")]

        # Should check if quality_issues is non-empty
        assert "if quality_issues:" in quality_section, \
            "Validation should check if quality_issues list is non-empty"

        # Should import sys and exit with code 1
        assert "import sys" in quality_section, \
            "Validation should import sys module"
        assert "sys.exit(1)" in quality_section, \
            "Validation should call sys.exit(1) when quality issues found"

        # Should print CONTENT QUALITY VALIDATION FAILED
        assert "CONTENT QUALITY VALIDATION FAILED" in quality_section, \
            "Validation should print CONTENT QUALITY VALIDATION FAILED"

    def test_outputs_quality_summary(self, tmp_path, azure_config_yaml):
        """Test that validation outputs quality validation summary."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        quality_section = rendered[rendered.find("Step 7.6"):rendered.find("Step 8")]

        # Should output quality summary
        assert "Content Quality Summary" in quality_section, \
            "Validation should output Content Quality Summary section"

        # Should show validated count
        assert "Validated:" in quality_section and "len(verified_items)" in quality_section, \
            "Validation summary should show validated count"

        # Should show sufficient quality count
        assert "Sufficient Quality:" in quality_section, \
            "Validation summary should show sufficient quality count"

        # Should show quality issues count
        assert "Quality Issues:" in quality_section and "len(quality_issues)" in quality_section, \
            "Validation summary should show quality issues count"

    def test_outputs_error_for_each_work_item_with_issues(self, tmp_path, azure_config_yaml):
        """Test that validation outputs detailed error for each work item with quality issues."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        quality_section = rendered[rendered.find("Step 7.6"):rendered.find("Step 8")]

        # Should track quality_issues list with id, title, issues
        assert "quality_issues = []" in quality_section, \
            "Validation should initialize quality_issues list"

        assert "'id': item_id" in quality_section, \
            "Validation should store work item ID in quality_issues"

        assert "'title': title" in quality_section, \
            "Validation should store work item title in quality_issues"

        assert "'issues': issues" in quality_section, \
            "Validation should store issues list in quality_issues"

        # Should loop through quality_issues to display them
        failure_section = quality_section[quality_section.find("if quality_issues:"):]
        assert "for issue in quality_issues:" in failure_section, \
            "Validation should loop through quality_issues to display them"

        # Should print each issue's problems
        assert "for problem in issue['issues']:" in failure_section, \
            "Validation should loop through each issue's problems"

    def test_handles_adapter_query_exceptions(self, tmp_path, azure_config_yaml):
        """Test that validation handles adapter query failures gracefully."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        quality_section = rendered[rendered.find("Step 7.6"):rendered.find("Step 8")]

        # Should wrap adapter.get_work_item() in try-except
        assert "try:" in quality_section, \
            "Validation should use try-except for adapter queries"
        assert "except Exception as e:" in quality_section, \
            "Validation should catch Exception for adapter query failures"

        # Should add to quality_issues on exception
        exception_handling = quality_section[quality_section.find("except Exception"):quality_section.find("# Output quality validation summary")]
        assert "quality_issues.append" in exception_handling, \
            "Validation should add item to quality_issues when adapter query throws exception"

        assert "validation error" in exception_handling, \
            "Validation should record 'validation error' when exception occurs"

    def test_continues_to_step8_when_all_pass(self, tmp_path, azure_config_yaml):
        """Test that workflow continues to Step 8 when all work items pass quality validation."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        # Step 7.6 now ends at Step 7.7 (not Step 8)
        quality_section = rendered[rendered.find("Step 7.6"):rendered.find("Step 7.7")]

        # Should have else block for success case
        assert "else:" in quality_section, \
            "Validation should have else block for success case"

        # Should print success message
        success_section = quality_section[quality_section.rfind("else:"):]
        assert "work items have sufficient detail" in success_section, \
            "Validation should print success message when all items pass"

        # Step 8 should exist after Step 7.6 (now after Step 7.7)
        assert "Step 8: Completion Summary" in rendered, \
            "Step 8 should exist after Step 7.7"

    def test_specifies_quality_thresholds_in_error_message(self, tmp_path, azure_config_yaml):
        """Test that validation error message specifies quality thresholds."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        quality_section = rendered[rendered.find("Step 7.6"):rendered.find("Step 8")]

        failure_section = quality_section[quality_section.find("if quality_issues:"):]

        # Should specify description threshold
        assert "500 characters" in failure_section, \
            "Error message should specify 500 character description threshold"

        # Should specify acceptance criteria threshold
        assert "3 criteria" in failure_section, \
            "Error message should specify 3 criteria threshold"

        # Should mention HTML tags are excluded
        assert "excluding HTML tags" in failure_section, \
            "Error message should mention HTML tags are excluded from description count"

    def test_prints_validation_progress_for_each_item(self, tmp_path, azure_config_yaml):
        """Test that validation prints progress for each work item validated."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        quality_section = rendered[rendered.find("Step 7.6"):rendered.find("Step 8")]

        # Should print validation progress header
        assert "Validating content quality" in quality_section, \
            "Validation should print header with count"

        # Should print success for each item that passes
        assert "Sufficient detail (desc:" in quality_section, \
            "Validation should print success message with details for each passing item"

        # Should print error for each item with issues
        assert "print(f\"❌ Work Item #{item_id}: {', '.join(issues)}\")" in quality_section, \
            "Validation should print error message for each item with issues"
