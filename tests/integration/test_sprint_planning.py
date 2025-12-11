"""
Integration tests for sprint-planning workflow verification checklist.

Tests Task #1104 implementation: Add sprint planning verification checklist and update tests

This tests the verification checklist added in Step 7.7 which shows:
1. Features created count
2. Tasks created count
3. All items exist in platform (from Step 7.5)
4. Descriptions validated (from Step 7.6)
5. Sprint assignments verified
6. Story points within capacity

The checklist provides visual confirmation of sprint planning verification results.
"""
import pytest
from pathlib import Path
from workflows.registry import WorkflowRegistry
from config.loader import load_config


@pytest.mark.integration
class TestSprintPlanningVerificationChecklist:
    """Test suite for sprint planning verification checklist in Step 7.7."""

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
        """Sample configuration with file-based adapter (no story points)."""
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

    def test_checklist_step_exists_after_step76(self, tmp_path, azure_config_yaml):
        """Test that Step 7.7 verification checklist is added after Step 7.6."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        # Step 7.7 should exist
        assert "Step 7.7: Verification Checklist" in rendered, \
            "Step 7.7 verification checklist missing"

        # Step 7.7 should come after Step 7.6 and before Step 8
        step76_pos = rendered.find("Step 7.6: Validate Work Item Content Quality")
        step77_pos = rendered.find("Step 7.7: Verification Checklist")
        step8_pos = rendered.find("Step 8: Completion Summary")

        assert step76_pos < step77_pos < step8_pos, \
            "Step 7.7 not positioned correctly between Step 7.6 and Step 8"

    def test_checklist_includes_all_six_items(self, tmp_path, azure_config_yaml):
        """Test that checklist includes all 6 verification items."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        checklist_section = rendered[rendered.find("Step 7.7"):rendered.find("Step 8")]

        # Item 1: Features created count
        assert "Features created:" in checklist_section, \
            "Checklist should show Features created count"

        # Item 2: Tasks created count
        assert "Tasks created:" in checklist_section, \
            "Checklist should show Tasks created count"

        # Item 3: All items exist in platform
        assert "All" in checklist_section and "work items exist in" in checklist_section, \
            "Checklist should verify all items exist in platform"

        # Item 4: Descriptions validated
        assert "descriptions validated" in checklist_section, \
            "Checklist should verify descriptions validated"

        # Item 5: Sprint assignments verified
        assert "Sprint assignments verified" in checklist_section, \
            "Checklist should verify sprint assignments"

        # Item 6: Story points within capacity
        assert "Story points within capacity" in checklist_section, \
            "Checklist should verify story points within capacity"

    def test_checklist_shows_features_created_count(self, tmp_path, azure_config_yaml):
        """Test that checklist displays Features created count."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        checklist_section = rendered[rendered.find("Step 7.7"):rendered.find("Step 8")]

        # Should count Features from approved_work_items
        assert "feature_count = sum(1 for item in approved_work_items if item['type'] == 'Feature')" in checklist_section, \
            "Checklist should count Features from approved_work_items"

        # Should display Features count
        assert 'print(f"- [x] Features created: {feature_count}")' in checklist_section, \
            "Checklist should display Features created count"

    def test_checklist_shows_tasks_created_count(self, tmp_path, azure_config_yaml):
        """Test that checklist displays Tasks created count."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        checklist_section = rendered[rendered.find("Step 7.7"):rendered.find("Step 8")]

        # Should count Tasks from approved_work_items
        assert "task_count = sum(1 for item in approved_work_items if item['type'] == 'Task')" in checklist_section, \
            "Checklist should count Tasks from approved_work_items"

        # Should display Tasks count
        assert 'print(f"- [x] Tasks created: {task_count}")' in checklist_section, \
            "Checklist should display Tasks created count"

    def test_checklist_shows_work_items_exist_checkbox(self, tmp_path, azure_config_yaml):
        """Test that checklist shows work items existence checkbox from Step 7.5."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        checklist_section = rendered[rendered.find("Step 7.7"):rendered.find("Step 8")]

        # Should check verified_items vs created_items
        assert "if len(verified_items) == len(created_items):" in checklist_section, \
            "Checklist should compare verified_items to created_items"

        # Should show [x] when all items verified
        assert 'print(f"- [x] All {len(created_items)} work items exist in {adapter.platform}")' in checklist_section, \
            "Checklist should show [x] when all items exist"

        # Should show [ ] with WARNING when items missing
        assert 'print(f"- [ ] All work items exist in {adapter.platform} (WARNING: {len(created_items) - len(verified_items)} missing)")' in checklist_section, \
            "Checklist should show [ ] with WARNING when items missing"

    def test_checklist_shows_descriptions_validated_checkbox(self, tmp_path, azure_config_yaml):
        """Test that checklist shows descriptions validated checkbox from Step 7.6."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        checklist_section = rendered[rendered.find("Step 7.7"):rendered.find("Step 8")]

        # Should check quality_issues list
        assert "if len(quality_issues) == 0:" in checklist_section, \
            "Checklist should check quality_issues list"

        # Should show [x] when no quality issues
        assert 'print(f"- [x] All descriptions validated (>= 500 characters)")' in checklist_section, \
            "Checklist should show [x] when descriptions validated"

        # Should show [ ] with WARNING when quality issues exist
        assert 'print(f"- [ ] All descriptions validated (WARNING: {len(quality_issues)} items have quality issues)")' in checklist_section, \
            "Checklist should show [ ] with WARNING when quality issues exist"

    def test_checklist_verifies_sprint_assignments(self, tmp_path, azure_config_yaml):
        """Test that checklist verifies sprint assignments."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        checklist_section = rendered[rendered.find("Step 7.7"):rendered.find("Step 8")]

        # Should iterate over verified_items to check sprint assignments
        assert "for item_id in verified_items:" in checklist_section, \
            "Checklist should iterate over verified_items"

        # Should query work item to get iteration path
        assert "iteration_path = work_item.get('fields', {}).get('System.IterationPath', '')" in checklist_section, \
            "Checklist should query iteration path from work item"

        # Should compare to expected path (rendered template has escaped backslashes)
        assert ("expected_path = f'TestProject\\\\{sprint_number}'" in checklist_section or
                "expected_path = f'TestProject\\{sprint_number}'" in checklist_section), \
            "Checklist should define expected iteration path"

        # Should count sprint assignment issues
        assert "sprint_assignment_issues = 0" in checklist_section, \
            "Checklist should track sprint assignment issues"

        # Should show [x] when all assignments correct
        assert 'print(f"- [x] Sprint assignments verified (all items in Sprint {sprint_number})")' in checklist_section, \
            "Checklist should show [x] when sprint assignments verified"

    def test_checklist_verifies_story_points_capacity(self, tmp_path, azure_config_yaml):
        """Test that checklist verifies story points within capacity."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        checklist_section = rendered[rendered.find("Step 7.7"):rendered.find("Step 8")]

        # Should calculate total story points
        assert "total_points = sum(item.get('story_points', 0) for item in approved_work_items)" in checklist_section, \
            "Checklist should calculate total story points"

        # Should compare to team_capacity
        assert "if total_points <= team_capacity:" in checklist_section, \
            "Checklist should compare total_points to team_capacity"

        # Should show [x] with utilization percentage when within capacity
        assert "utilization_pct = int((total_points / team_capacity) * 100) if team_capacity > 0 else 0" in checklist_section, \
            "Checklist should calculate utilization percentage"
        assert 'print(f"- [x] Story points within capacity ({total_points}/{team_capacity} points, {utilization_pct}% utilization)")' in checklist_section, \
            "Checklist should show [x] when within capacity"

        # Should show [ ] with WARNING when over capacity
        assert "over_pct = int(((total_points - team_capacity) / team_capacity) * 100) if team_capacity > 0 else 0" in checklist_section, \
            "Checklist should calculate over-capacity percentage"
        assert 'print(f"- [ ] Story points within capacity (WARNING: {total_points}/{team_capacity} points, {over_pct}% over capacity)")' in checklist_section, \
            "Checklist should show [ ] with WARNING when over capacity"

    def test_checklist_uses_checkbox_format_for_passed_items(self, tmp_path, azure_config_yaml):
        """Test that checklist uses [x] format for passed verification items."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        checklist_section = rendered[rendered.find("Step 7.7"):rendered.find("Step 8")]

        # Should use [x] for passed items
        assert '- [x]' in checklist_section, \
            "Checklist should use [x] checkbox format for passed items"

        # Count number of [x] checkboxes (should have 6 potential success paths)
        checkbox_count = checklist_section.count('- [x]')
        assert checkbox_count >= 6, \
            f"Checklist should have at least 6 [x] checkboxes, found {checkbox_count}"

    def test_checklist_uses_empty_checkbox_for_warnings(self, tmp_path, azure_config_yaml):
        """Test that checklist uses [ ] format for warnings and failures."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        checklist_section = rendered[rendered.find("Step 7.7"):rendered.find("Step 8")]

        # Should use [ ] for warnings
        assert '- [ ]' in checklist_section, \
            "Checklist should use [ ] checkbox format for warnings"

        # Should include WARNING keyword with [ ] checkboxes
        warning_checkboxes = checklist_section.count('- [ ]')
        assert warning_checkboxes >= 4, \
            f"Checklist should have at least 4 [ ] warning checkboxes, found {warning_checkboxes}"

    def test_checklist_handles_no_story_points_configured(self, tmp_path, filebased_config_yaml):
        """Test that checklist handles case when story points not configured."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(filebased_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        checklist_section = rendered[rendered.find("Step 7.7"):rendered.find("Step 8")]

        # Should show N/A when story points not configured
        assert 'print(f"- [ ] Story points within capacity (N/A - story points not configured)")' in checklist_section, \
            "Checklist should show N/A when story points not configured"

    def test_checklist_outputs_header_and_footer(self, tmp_path, azure_config_yaml):
        """Test that checklist outputs header and footer with proper formatting."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        checklist_section = rendered[rendered.find("Step 7.7"):rendered.find("Step 8")]

        # Should have header
        assert "Sprint Planning Verification Checklist" in checklist_section, \
            "Checklist should have header"

        # Should have separator lines
        assert "='*80" in checklist_section, \
            "Checklist should have 80-character separator lines"

        # Should have completion message
        assert "Sprint planning verification complete" in checklist_section, \
            "Checklist should have completion message"

    def test_work_item_existence_verification_failure_scenario(self, tmp_path, azure_config_yaml):
        """Integration test: Verify checklist shows failure when work items don't exist."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        # Verify Step 7.5 would catch missing items and populate missing_items list
        step75_section = rendered[rendered.find("Step 7.5"):rendered.find("Step 7.6")]
        assert "missing_items.append(item_id)" in step75_section, \
            "Step 7.5 should populate missing_items list when items don't exist"

        # Verify Step 7.7 checklist uses missing_items to show failure
        checklist_section = rendered[rendered.find("Step 7.7"):rendered.find("Step 8")]
        assert "len(created_items) - len(verified_items)" in checklist_section, \
            "Checklist should calculate missing items count"
        assert "WARNING:" in checklist_section and "missing" in checklist_section, \
            "Checklist should show WARNING when items missing"

    def test_description_length_verification_failure_scenario(self, tmp_path, azure_config_yaml):
        """Integration test: Verify checklist shows failure when descriptions too short."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        # Verify Step 7.6 would catch description issues and populate quality_issues list
        step76_section = rendered[rendered.find("Step 7.6"):rendered.find("Step 7.7")]
        assert "if description_length < 500:" in step76_section, \
            "Step 7.6 should check description length >= 500 characters"
        assert "quality_issues.append({" in step76_section, \
            "Step 7.6 should populate quality_issues list when descriptions too short"

        # Verify Step 7.7 checklist uses quality_issues to show failure
        checklist_section = rendered[rendered.find("Step 7.7"):rendered.find("Step 8")]
        assert "if len(quality_issues) == 0:" in checklist_section, \
            "Checklist should check quality_issues list"
        assert "len(quality_issues)" in checklist_section and "quality issues" in checklist_section, \
            "Checklist should show quality issues count when validation fails"

    def test_checklist_format_matches_requirements(self, tmp_path, azure_config_yaml):
        """Test that checklist format matches all requirements from Task #1104."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        checklist_section = rendered[rendered.find("Step 7.7"):rendered.find("Step 8")]

        # Requirement 1: Markdown checklist added after Step 7 completion (Step 7.7)
        assert "Step 7.7: Verification Checklist" in rendered, \
            "Requirement 1: Markdown checklist should be added as Step 7.7"

        # Requirement 2: Checklist shows all 6 verification items
        required_items = [
            "Features created:",
            "Tasks created:",
            "work items exist in",
            "descriptions validated",
            "Sprint assignments verified",
            "Story points within capacity"
        ]
        for item in required_items:
            assert item in checklist_section, \
                f"Requirement 2: Checklist missing required item: {item}"

        # Requirement 3: Uses [x] for passed items
        assert '- [x]' in checklist_section, \
            "Requirement 3: Checklist should use [x] for passed items"

        # Requirement 4: Uses [ ] for warnings
        assert '- [ ]' in checklist_section, \
            "Requirement 4: Checklist should use [ ] for warnings"

        # Visual confirmation feature
        assert "📋 Sprint Planning Verification Checklist" in checklist_section, \
            "Checklist should provide visual confirmation with emoji header"
