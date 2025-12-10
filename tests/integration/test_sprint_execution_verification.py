"""
Integration tests for sprint-execution workflow verification checklist.

Tests Task #1110 implementation: Add verification checklist to sprint-execution monitoring cycle.

This implements the "External Source of Truth" pattern from VISION.md Pillar #2:
- AI agents claim work is complete when it isn't
- Verification queries adapter (external source of truth) to detect divergence
- Verification checklist provides daily audit trail
- Checklist included in status report (Step B6)
"""
import pytest
from pathlib import Path
from workflows.registry import WorkflowRegistry
from config.loader import load_config


@pytest.mark.integration
class TestSprintExecutionVerificationChecklist:
    """Test suite for verification checklist in sprint-execution workflow."""

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
    scrum-master: "claude-haiku-4"
    senior-engineer: "claude-sonnet-4.5"
  enabled_agents:
    - scrum-master
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
    def non_python_config_yaml(self):
        """Sample configuration with non-Python tech stack."""
        return """
project:
  name: "Test Project"
  type: "web-application"
  tech_stack:
    languages: ["TypeScript"]
    frameworks: ["React"]

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

    def test_verification_step_exists_in_monitoring_cycle(self, tmp_path, azure_config_yaml):
        """Test that Step B4.5 verification checklist is added in monitoring cycle."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-execution")

        # Step B4.5 should exist
        assert "Step B4.5: Verification Checklist" in rendered, \
            "Step B4.5 verification checklist step missing"

        # Step B4.5 should come after Step B4 and before Step B5
        step_b4_pos = rendered.find("Step B4: Quality Health Check")
        step_b45_pos = rendered.find("Step B4.5: Verification Checklist")
        step_b5_pos = rendered.find("Step B5: Weekly Security Review")

        assert step_b4_pos < step_b45_pos < step_b5_pos, \
            "Step B4.5 not positioned correctly between Step B4 and Step B5"

    def test_verification_checklist_has_four_items(self, tmp_path, azure_config_yaml):
        """Test that verification checklist has all 4 required items."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-execution")

        # Get Step B4.5 section
        step_b45_pos = rendered.find("Step B4.5: Verification Checklist")
        step_b5_pos = rendered.find("Step B5: Weekly Security Review")
        verification_section = rendered[step_b45_pos:step_b5_pos]

        # Should have all 4 checklist items
        assert "Work item states queried from adapter" in verification_section, \
            "Missing checklist item 1: Work item states queried from adapter"
        assert "Test results verified for Done items" in verification_section, \
            "Missing checklist item 2: Test results verified for Done items"
        assert "Blocked items have linked blocker work items" in verification_section, \
            "Missing checklist item 3: Blocked items have linked blockers"
        assert "Story points burndown validated" in verification_section, \
            "Missing checklist item 4: Story points burndown validated"

    def test_checklist_items_show_checkbox_format(self, tmp_path, azure_config_yaml):
        """Test that checklist items use markdown checkbox format [x] or [ ]."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-execution")

        # Get Step B4.5 section
        step_b45_pos = rendered.find("Step B4.5: Verification Checklist")
        step_b5_pos = rendered.find("Step B5: Weekly Security Review")
        verification_section = rendered[step_b45_pos:step_b5_pos]

        # Should use checkbox format with conditional [x] or [ ]
        assert "[{'x' if" in verification_section or "[x]" in verification_section, \
            "Checklist should use [x] for verified items"
        assert "' '}]" in verification_section or "[ ]" in verification_section, \
            "Checklist should use [ ] for unverified items"

    def test_work_items_verification_queries_adapter(self, tmp_path, azure_config_yaml):
        """Test that work items verification checks adapter query results."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-execution")

        # Get Step B4.5 section
        step_b45_pos = rendered.find("Step B4.5: Verification Checklist")
        step_b5_pos = rendered.find("Step B5: Weekly Security Review")
        verification_section = rendered[step_b45_pos:step_b5_pos]

        # Should verify work items were queried from adapter
        assert "work_items_verified" in verification_section, \
            "Should define work_items_verified variable"
        assert "len(sprint_items)" in verification_section, \
            "Should check sprint_items length"
        assert "'state' in item" in verification_section, \
            "Should verify items have 'state' field from adapter"

    def test_test_coverage_verification_for_python_projects(self, tmp_path, azure_config_yaml):
        """Test that test coverage verification runs for Python projects."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-execution")

        # Get Step B4.5 section
        step_b45_pos = rendered.find("Step B4.5: Verification Checklist")
        step_b5_pos = rendered.find("Step B5: Weekly Security Review")
        verification_section = rendered[step_b45_pos:step_b5_pos]

        # Should run pytest coverage for Python projects
        assert "python" in verification_section.lower() and "pytest" in verification_section.lower(), \
            "Should run pytest for Python projects"
        assert "--cov=" in verification_section, \
            "Should run pytest with coverage"
        assert "coverage_meets_standard" in verification_section, \
            "Should define coverage_meets_standard variable"

    def test_test_coverage_skipped_for_non_python_projects(self, tmp_path, non_python_config_yaml):
        """Test that test coverage verification is skipped for non-Python projects."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(non_python_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-execution")

        # Get Step B4.5 section
        step_b45_pos = rendered.find("Step B4.5: Verification Checklist")
        step_b5_pos = rendered.find("Step B5: Weekly Security Review")
        verification_section = rendered[step_b45_pos:step_b5_pos]

        # Should skip coverage check with N/A
        assert "Skip for non-Python projects" in verification_section or "N/A" in verification_section, \
            "Should skip or mark N/A for non-Python projects"

    def test_blocked_items_verification_queries_adapter(self, tmp_path, azure_config_yaml):
        """Test that blocked items verification queries adapter for work item details."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-execution")

        # Get Step B4.5 section
        step_b45_pos = rendered.find("Step B4.5: Verification Checklist")
        step_b5_pos = rendered.find("Step B5: Weekly Security Review")
        verification_section = rendered[step_b45_pos:step_b5_pos]

        # Should query adapter for work item details
        assert "adapter.get_work_item(" in verification_section, \
            "Should query adapter.get_work_item() for blocker links"
        assert "blocked_items" in verification_section, \
            "Should define blocked_items list"
        assert "relations" in verification_section, \
            "Should check work item relations for blocker links"

    def test_blocked_items_check_platform_agnostic(self, tmp_path, azure_config_yaml):
        """Test that blocked items check works with any platform adapter."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-execution")

        # Get Step B4.5 section
        step_b45_pos = rendered.find("Step B4.5: Verification Checklist")
        step_b5_pos = rendered.find("Step B5: Weekly Security Review")
        verification_section = rendered[step_b45_pos:step_b5_pos]

        # Should check relation types generically
        assert "'dependency'" in verification_section.lower() or "'blocks'" in verification_section.lower(), \
            "Should check for dependency or blocker relation types"
        assert "platform-agnostic" in verification_section.lower(), \
            "Should mention platform-agnostic approach"

    def test_story_points_verification_uses_adapter_data(self, tmp_path, azure_config_yaml):
        """Test that story points verification uses adapter-queried data."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-execution")

        # Get Step B4.5 section
        step_b45_pos = rendered.find("Step B4.5: Verification Checklist")
        step_b5_pos = rendered.find("Step B5: Weekly Security Review")
        verification_section = rendered[step_b45_pos:step_b5_pos]

        # Should validate story points from adapter data
        assert "story_points_validated" in verification_section, \
            "Should define story_points_validated variable"
        assert "total_points" in verification_section and "completed_points" in verification_section, \
            "Should use total_points and completed_points from adapter"

    def test_checklist_output_to_console(self, tmp_path, azure_config_yaml):
        """Test that checklist is output to console during execution."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-execution")

        # Get Step B4.5 section
        step_b45_pos = rendered.find("Step B4.5: Verification Checklist")
        step_b5_pos = rendered.find("Step B5: Weekly Security Review")
        verification_section = rendered[step_b45_pos:step_b5_pos]

        # Should print checklist to console
        assert "print(" in verification_section, \
            "Should print checklist output"
        assert "🔍" in verification_section or "Verification Checklist" in verification_section, \
            "Should print checklist header"
        assert "=" * 80 in verification_section or '="' in verification_section, \
            "Should print visual separator"

    def test_checklist_included_in_status_report(self, tmp_path, azure_config_yaml):
        """Test that checklist is included in Step B6 status report."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-execution")

        # Get Step B6 section
        step_b6_pos = rendered.find("Step B6: Generate Status Report")
        step_b6_section = rendered[step_b6_pos:]

        # Should include verification checklist in status report
        assert "🔍 Verification Checklist:" in step_b6_section, \
            "Status report should include Verification Checklist section"
        assert "verification_checklist_text" in step_b6_section, \
            "Status report should reference verification_checklist_text variable"

    def test_verification_results_stored_for_reporting(self, tmp_path, azure_config_yaml):
        """Test that verification results are stored in a dict for reporting."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-execution")

        # Get Step B4.5 section
        step_b45_pos = rendered.find("Step B4.5: Verification Checklist")
        step_b5_pos = rendered.find("Step B5: Weekly Security Review")
        verification_section = rendered[step_b45_pos:step_b5_pos]

        # Should store verification results
        assert "verification_results" in verification_section, \
            "Should define verification_results dict"
        assert "verification_checklist_text" in verification_section, \
            "Should define verification_checklist_text for reporting"

    def test_verification_works_with_file_based_adapter(self, tmp_path, filebased_config_yaml):
        """Test that verification works with file-based adapter (not just Azure DevOps)."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(filebased_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-execution")

        # Get Step B4.5 section
        step_b45_pos = rendered.find("Step B4.5: Verification Checklist")
        step_b5_pos = rendered.find("Step B5: Weekly Security Review")
        verification_section = rendered[step_b45_pos:step_b5_pos]

        # Should use generic adapter methods
        assert "adapter.get_work_item(" in verification_section, \
            "Should use generic adapter.get_work_item()"

        # Should NOT have Azure DevOps-specific code
        assert "az boards" not in verification_section, \
            "Should not have Azure DevOps-specific commands"

    def test_verification_mentions_vision_pattern(self, tmp_path, azure_config_yaml):
        """Test that verification step references VISION.md External Source of Truth pattern."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-execution")

        # Get Step B4.5 section
        step_b45_pos = rendered.find("Step B4.5: Verification Checklist")
        step_b5_pos = rendered.find("Step B5: Weekly Security Review")
        verification_section = rendered[step_b45_pos:step_b5_pos]

        # Should reference VISION.md pattern
        assert "External Source of Truth" in verification_section or "external source of truth" in verification_section, \
            "Should reference External Source of Truth pattern"
        assert "VISION.md" in verification_section or "CRITICAL" in verification_section, \
            "Should reference VISION.md or mark as CRITICAL"

    def test_workflow_overview_updated_with_verification_step(self, tmp_path, azure_config_yaml):
        """Test that workflow overview includes verification checklist step."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-execution")

        # Get workflow overview section
        overview_pos = rendered.find("MONITORING CYCLE (daily):")
        overview_section = rendered[overview_pos:overview_pos + 1000]

        # Should mention verification checklist in overview
        assert "Verification checklist" in overview_section or "verification" in overview_section.lower(), \
            "Workflow overview should mention verification checklist step"

    def test_error_handling_for_adapter_failures(self, tmp_path, azure_config_yaml):
        """Test that verification handles adapter query failures gracefully."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-execution")

        # Get Step B4.5 section
        step_b45_pos = rendered.find("Step B4.5: Verification Checklist")
        step_b5_pos = rendered.find("Step B5: Weekly Security Review")
        verification_section = rendered[step_b45_pos:step_b5_pos]

        # Should have try-except for adapter queries
        assert "try:" in verification_section and "except" in verification_section, \
            "Should handle adapter query failures with try-except"
        assert "Exception" in verification_section, \
            "Should catch exceptions from adapter queries"


@pytest.mark.integration
class TestSprintExecutionVerificationEdgeCases:
    """Test edge cases for sprint-execution verification checklist."""

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

    def test_verification_handles_empty_sprint_items(self, tmp_path, azure_config_yaml):
        """Test that verification handles case when sprint_items is empty."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-execution")

        # Get Step B4.5 section
        step_b45_pos = rendered.find("Step B4.5: Verification Checklist")
        step_b5_pos = rendered.find("Step B5: Weekly Security Review")
        verification_section = rendered[step_b45_pos:step_b5_pos]

        # Should check sprint_items length
        assert "len(sprint_items)" in verification_section, \
            "Should check sprint_items length (handles empty gracefully)"

    def test_verification_handles_no_blocked_items(self, tmp_path, azure_config_yaml):
        """Test that verification handles case when no items are blocked."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-execution")

        # Get Step B4.5 section
        step_b45_pos = rendered.find("Step B4.5: Verification Checklist")
        step_b5_pos = rendered.find("Step B5: Weekly Security Review")
        verification_section = rendered[step_b45_pos:step_b5_pos]

        # Should handle no blocked items (mark as pass/N/A)
        assert "len(blocked_items) == 0" in verification_section, \
            "Should handle case when no blocked items (mark as N/A)"

    def test_coverage_parse_failure_handling(self, tmp_path, azure_config_yaml):
        """Test that verification handles coverage parse failures gracefully."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-execution")

        # Get Step B4.5 section
        step_b45_pos = rendered.find("Step B4.5: Verification Checklist")
        step_b5_pos = rendered.find("Step B5: Weekly Security Review")
        verification_section = rendered[step_b45_pos:step_b5_pos]

        # Should handle coverage parsing failures
        assert "except Exception" in verification_section, \
            "Should catch exceptions from coverage parsing"
        # Should default to not failing verification
        assert "coverage_percent = 0" in verification_section, \
            "Should set default coverage_percent on failure"
