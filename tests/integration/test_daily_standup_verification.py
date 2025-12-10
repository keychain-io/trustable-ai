"""
Integration tests for daily-standup workflow work item state verification.

Tests Task #1109 implementation: Add work item state verification to daily-standup.j2

This implements the "External Source of Truth" pattern from VISION.md Pillar #2:
- AI agents claim work is complete when it isn't
- Verification queries adapter (external source of truth) to detect divergence
- Divergences reported as warnings (don't fail workflow)
- Daily standup report includes divergence summary
"""
import pytest
from pathlib import Path
from workflows.registry import WorkflowRegistry
from config.loader import load_config


@pytest.mark.integration
class TestDailyStandupStateVerification:
    """Test suite for work item state verification in daily-standup workflow."""

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
    scrum-master: "claude-haiku-4"
  enabled_agents:
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
    scrum-master: "claude-haiku-4"
  enabled_agents:
    - scrum-master
"""

    def test_verification_step_exists_after_step1(self, tmp_path, azure_config_yaml):
        """Test that Step 1.5 verification step is added after Step 1."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml)

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("daily-standup")

        # Step 1.5 should exist
        assert "Step 1.5: Verify Work Item States Against External Source of Truth" in rendered, \
            "Step 1.5 verification step missing"

        # Step 1.5 should come after Step 1 and before Step 2
        step1_pos = rendered.find("Step 1: Gather Yesterday's Activity")
        step15_pos = rendered.find("Step 1.5: Verify Work Item States")
        step2_pos = rendered.find("Step 2: Identify Today's Focus")

        assert step1_pos < step15_pos < step2_pos, \
            "Step 1.5 not positioned correctly between Step 1 and Step 2"

    def test_verification_queries_adapter_for_current_states(self, tmp_path, azure_config_yaml):
        """Test that verification queries adapter to get current work item states."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml)

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("daily-standup")

        # Should query adapter for each item
        assert "adapter.get_work_item(" in rendered, \
            "Verification should query adapter.get_work_item() for current state"

        # Should build actual state map
        assert "actual_state_map" in rendered, \
            "Verification should build map of actual states from adapter"

        # Should handle items not found
        assert "NOT_FOUND" in rendered, \
            "Verification should handle work items not found in adapter"

    def test_verification_detects_state_divergence(self, tmp_path, azure_config_yaml):
        """Test that verification detects divergence between claimed and actual states."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml)

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("daily-standup")

        # Should define terminal states
        assert "terminal_states" in rendered, \
            "Verification should define terminal states list"
        assert "Done" in rendered and "Closed" in rendered, \
            "Terminal states should include 'Done' and 'Closed'"

        # Should check for divergence
        assert "divergences" in rendered, \
            "Verification should track divergences"

        # Should detect claimed terminal but actually not terminal
        assert "claimed_state in terminal_states and actual_state not in terminal_states" in rendered, \
            "Verification should detect claimed Done but actually In Progress"

    def test_verification_detects_missing_work_items(self, tmp_path, azure_config_yaml):
        """Test that verification detects work items that don't exist in adapter."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml)

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("daily-standup")

        # Should check if work item exists
        assert "actual_state == 'NOT_FOUND'" in rendered, \
            "Verification should check if work item not found in adapter"

        # Should flag as ERROR severity
        assert "'severity': 'ERROR'" in rendered, \
            "Missing work items should be flagged as ERROR severity"

    def test_verification_outputs_divergence_warnings(self, tmp_path, azure_config_yaml):
        """Test that verification outputs divergence warnings but doesn't fail workflow."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml)

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("daily-standup")

        # Should output divergence warnings
        assert "⚠️ DIVERGENCE DETECTED" in rendered, \
            "Verification should output divergence warning"

        # Should display errors and warnings differently
        assert "❌" in rendered, \
            "Errors should be displayed with error emoji"
        assert "⚠️" in rendered, \
            "Warnings should be displayed with warning emoji"

        # Should output divergence summary
        assert "Divergence Summary" in rendered, \
            "Verification should output divergence summary"

        # Should NOT have raise or sys.exit (informational only)
        verification_section = rendered[rendered.find("Step 1.5"):rendered.find("Step 2")]
        assert "raise" not in verification_section, \
            "Verification should not raise exceptions (informational only)"
        assert "sys.exit" not in verification_section, \
            "Verification should not exit workflow (informational only)"

    def test_verification_includes_success_message_when_no_divergence(self, tmp_path, azure_config_yaml):
        """Test that verification outputs success message when no divergence found."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml)

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("daily-standup")

        # Should output success message when no divergences
        assert "✅ No divergence detected" in rendered, \
            "Verification should output success message when no divergence"
        assert "all work item states match external source of truth" in rendered, \
            "Success message should confirm states match external source of truth"

    def test_divergence_summary_stored_for_report(self, tmp_path, azure_config_yaml):
        """Test that divergence summary is stored for inclusion in report."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml)

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("daily-standup")

        # Should store divergence summary
        assert "divergence_summary" in rendered, \
            "Verification should store divergence_summary variable"

        # Should include count, errors, and warnings
        assert "'count':" in rendered and "'errors':" in rendered and "'warnings':" in rendered, \
            "divergence_summary should include count, errors, and warnings"

    def test_divergence_section_added_to_report_template(self, tmp_path, azure_config_yaml):
        """Test that report template includes divergence summary section."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml)

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("daily-standup")

        # Report should have Work Item State Verification section
        assert "## Work Item State Verification" in rendered, \
            "Report template should include Work Item State Verification section"

        # Should conditionally show divergence details (Python code format)
        assert "if divergence_summary['count'] > 0:" in rendered, \
            "Report should conditionally show divergence details"

        # Should list errors and warnings
        assert "### Errors" in rendered and "### Warnings" in rendered, \
            "Report should list errors and warnings separately"

        # Should show success when no divergence
        assert "✅ **All work item states verified**" in rendered, \
            "Report should show success message when no divergence"

    def test_scrum_master_agent_receives_divergence_summary(self, tmp_path, azure_config_yaml):
        """Test that scrum-master agent receives divergence_summary as input."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml)

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("daily-standup")

        # Step 4 should mention including divergence results
        assert "Step 4: Generate Standup Report" in rendered, \
            "Step 4 should exist"

        step4_pos = rendered.find("Step 4: Generate Standup Report")
        step5_pos = rendered.find("Step 5: Format and Distribute Report")
        step4_section = rendered[step4_pos:step5_pos]

        assert "divergence" in step4_section.lower(), \
            "Step 4 should mention including divergence results"

        # Input should include divergence_summary
        assert "divergence_summary" in step4_section, \
            "Scrum-master agent input should include divergence_summary"

    def test_verification_works_with_file_based_adapter(self, tmp_path, filebased_config_yaml):
        """Test that verification works with file-based adapter (not just Azure DevOps)."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(filebased_config_yaml)

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("daily-standup")

        # Should use generic adapter methods (not Azure-specific)
        assert "adapter.get_work_item(" in rendered, \
            "Verification should use generic adapter.get_work_item()"

        # Should reference adapter.platform generically
        assert "adapter.platform" in rendered, \
            "Verification should reference adapter.platform generically"

        # Should NOT have Azure DevOps-specific code
        assert "az boards" not in rendered, \
            "Verification should not have Azure DevOps-specific commands"

    def test_terminal_states_correctly_identified(self, tmp_path, azure_config_yaml):
        """Test that terminal states list matches common completion states."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml)

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("daily-standup")

        # Find terminal states definition
        verification_section = rendered[rendered.find("Step 1.5"):rendered.find("Step 2")]

        # Should include common terminal states
        assert "Done" in verification_section, \
            "Terminal states should include 'Done'"
        assert "Closed" in verification_section, \
            "Terminal states should include 'Closed'"
        assert "Completed" in verification_section, \
            "Terminal states should include 'Completed'"
        assert "Resolved" in verification_section, \
            "Terminal states should include 'Resolved'"

    def test_divergence_output_formatting(self, tmp_path, azure_config_yaml):
        """Test that divergence output has clear, actionable formatting."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml)

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("daily-standup")

        # Get Step 1.5 section where divergence output formatting is defined
        step15_pos = rendered.find("Step 1.5: Verify Work Item States")
        step2_pos = rendered.find("Step 2: Identify Today's Focus")
        verification_section = rendered[step15_pos:step2_pos]

        # Should use clear visual separators in Step 1.5
        assert "=" * 80 in verification_section or '="' in verification_section, \
            "Divergence output should use visual separators"

        # Should show item ID and title (either dict access or f-string format)
        assert ("div['id']" in verification_section and "div['title']" in verification_section), \
            "Divergence output should show work item ID and title"

        # Should show claimed vs actual states
        assert "CLAIMED:" in verification_section or "claimed_state" in verification_section, \
            "Divergence output should show claimed state"
        assert "ACTUAL:" in verification_section or "actual_state" in verification_section, \
            "Divergence output should show actual state"

        # Should provide actionable guidance (check both Step 1.5 and Step 5)
        assert "Action" in rendered and ("Review" in rendered or "sync" in rendered), \
            "Divergence output should provide actionable guidance"

    def test_verification_mentions_vision_pattern(self, tmp_path, azure_config_yaml):
        """Test that verification step references VISION.md External Source of Truth pattern."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml)

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("daily-standup")

        # Should reference VISION.md pattern
        verification_section = rendered[rendered.find("Step 1.5"):rendered.find("Step 2")]

        assert "External Source of Truth" in verification_section or "external source of truth" in verification_section, \
            "Verification step should reference External Source of Truth pattern"

        assert "VISION.md" in verification_section or "CRITICAL" in verification_section, \
            "Verification step should reference VISION.md or mark as CRITICAL"

    def test_verification_counts_errors_and_warnings_separately(self, tmp_path, azure_config_yaml):
        """Test that verification counts errors and warnings separately in summary."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml)

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("daily-standup")

        # Should count errors separately
        assert "ERROR" in rendered and "'ERROR'" in rendered, \
            "Verification should have ERROR severity"

        # Should count warnings separately
        assert "WARNING" in rendered and "'WARNING'" in rendered, \
            "Verification should have WARNING severity"

        # Summary should show both counts
        summary_pattern = "len([d for d in divergences if d['severity'] == 'ERROR'])"
        assert summary_pattern in rendered or "ERROR" in rendered, \
            "Summary should count errors separately"

        warning_pattern = "len([d for d in divergences if d['severity'] == 'WARNING'])"
        assert warning_pattern in rendered or "WARNING" in rendered, \
            "Summary should count warnings separately"


@pytest.mark.integration
class TestDailyStandupVerificationEdgeCases:
    """Test edge cases for daily-standup state verification."""

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
    task: "Task"

quality_standards:
  test_coverage_min: 80
  critical_vulnerabilities_max: 0

agent_config:
  models:
    scrum-master: "claude-haiku-4"
  enabled_agents:
    - scrum-master
"""

    def test_verification_handles_empty_recent_items(self, tmp_path, azure_config_yaml):
        """Test that verification handles case when recent_items is empty."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml)

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("daily-standup")

        # Should iterate over recent_items (handles empty gracefully)
        assert "for item in recent_items:" in rendered, \
            "Verification should iterate over recent_items"

        # Python for loop handles empty list gracefully, no special handling needed

    def test_verification_handles_work_item_with_unknown_state(self, tmp_path, azure_config_yaml):
        """Test that verification handles work items with unknown or missing state."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml)

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("daily-standup")

        # Should use .get() with default for state
        assert "item.get('state'" in rendered or "current_item.get('state'" in rendered, \
            "Verification should use .get() for state field (handles missing gracefully)"

        # Should have default state values
        assert "'UNKNOWN'" in rendered or "'Unknown'" in rendered, \
            "Verification should have default state for missing values"

    def test_verification_message_format_consistency(self, tmp_path, azure_config_yaml):
        """Test that verification messages are consistent and informative."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml)

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("daily-standup")

        verification_section = rendered[rendered.find("Step 1.5"):rendered.find("Step 2")]

        # Should have consistent message field in divergence dict
        assert "'message'" in verification_section, \
            "Divergence dict should have message field"

        # Messages should reference platform generically
        assert "adapter.platform" in verification_section, \
            "Messages should reference adapter.platform generically"
