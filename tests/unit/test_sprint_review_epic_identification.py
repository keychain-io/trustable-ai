"""
Unit tests for sprint-review workflow EPIC identification.

Tests Task #1089 implementation: Extend sprint-review workflow to identify EPICs for testing

This implements EPIC identification from sprint scope in Step 1.5:
- Query adapter for Epic work items from sprint scope
- Extract EPIC metadata (ID, title, description, state)
- Verify each EPIC has attached/linked acceptance test plan
- Store testable EPICs (those with test plans) in workflow state with checkpoint
- Works with both Azure DevOps and file-based adapters
"""
import pytest
from pathlib import Path
from workflows.registry import WorkflowRegistry
from config.loader import load_config


@pytest.mark.unit
class TestSprintReviewEpicIdentification:
    """Test suite for EPIC identification in sprint-review workflow."""

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

    def test_epic_identification_step_exists_after_step1(self, tmp_path, azure_config_yaml):
        """Test that Step 1.5 EPIC identification step is added after Step 1."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-review")

        # Step 1.5 should exist
        assert "Step 1.5: Identify EPICs for Testing" in rendered, \
            "Step 1.5 EPIC identification step missing"

        # Step 1.5 should come after Step 1 and before Step 2
        step1_pos = rendered.find("Step 1: Collect Sprint Completion Metrics")
        step15_pos = rendered.find("Step 1.5: Identify EPICs for Testing")
        step2_pos = rendered.find("Step 2: Run Acceptance Tests")

        assert step1_pos < step15_pos < step2_pos, \
            "Step 1.5 not positioned correctly between Step 1 and Step 2"

    def test_workflow_overview_includes_step15(self, tmp_path, azure_config_yaml):
        """Test that workflow overview includes Step 1.5."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-review")

        overview_section = rendered[rendered.find("## Workflow Overview"):rendered.find("## Initialize Workflow")]

        # Overview should list Step 1.5
        assert "Step 1.5: Identify EPICs for testing" in overview_section, \
            "Workflow overview should include Step 1.5"

    def test_queries_adapter_for_epic_work_items(self, tmp_path, azure_config_yaml):
        """Test that EPIC identification queries adapter for Epic work items in sprint scope."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-review")

        epic_section = rendered[rendered.find("## Step 1.5"):rendered.find("## Step 2")]

        # Should query adapter for Epic work items
        assert "adapter.query_work_items(" in epic_section, \
            "EPIC identification should query adapter for work items"

        # Should filter by work item type (Epic)
        assert "'System.WorkItemType': 'Epic'" in epic_section, \
            "EPIC identification should filter for Epic work item type"

        # Should filter by iteration path (sprint scope)
        assert "'System.IterationPath':" in epic_section, \
            "EPIC identification should filter by sprint iteration path"

    def test_extracts_epic_metadata_fields(self, tmp_path, azure_config_yaml):
        """Test that EPIC identification extracts required metadata fields."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-review")

        epic_section = rendered[rendered.find("## Step 1.5"):rendered.find("## Step 2")]

        # Should extract epic metadata with required fields
        assert "'id': epic_id" in epic_section, \
            "EPIC identification should extract ID"

        assert "'title':" in epic_section, \
            "EPIC identification should extract title"

        assert "'state':" in epic_section, \
            "EPIC identification should extract state"

        assert "'description':" in epic_section, \
            "EPIC identification should extract description"

    def test_checks_azure_devops_attachments_for_test_plan(self, tmp_path, azure_config_yaml):
        """Test that EPIC identification checks Azure DevOps attachments for test plan file."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-review")

        epic_section = rendered[rendered.find("## Step 1.5"):rendered.find("## Step 2")]

        # Should check for Azure DevOps platform
        assert "if adapter.platform == 'azure-devops':" in epic_section, \
            "EPIC identification should check for Azure DevOps platform"

        # Should check work item relations for attachments
        assert "relations = work_item.get('relations', [])" in epic_section, \
            "EPIC identification should get work item relations"

        assert "for relation in relations:" in epic_section, \
            "EPIC identification should iterate over relations"

        # Should check for AttachedFile relation type
        assert "'AttachedFile' in rel_type" in epic_section, \
            "EPIC identification should check for AttachedFile relation type"

        # Should check attachment URL for test plan pattern
        assert "'test-plan' in attachment_url.lower()" in epic_section, \
            "EPIC identification should check for test-plan in attachment URL"

    def test_verifies_attachment_by_filename(self, tmp_path, azure_config_yaml):
        """Test that EPIC identification verifies attachment exists by expected filename."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-review")

        epic_section = rendered[rendered.find("## Step 1.5"):rendered.find("## Step 2")]

        # Should verify attachment by expected filename pattern
        assert "expected_filename = f\"epic-{epic_id}-test-plan.md\"" in epic_section, \
            "EPIC identification should construct expected test plan filename"

        assert "azure_cli.verify_attachment_exists(" in epic_section, \
            "EPIC identification should verify attachment exists using azure_cli"

    def test_checks_file_based_comments_for_test_plan(self, tmp_path, filebased_config_yaml):
        """Test that EPIC identification checks file-based comments for test plan reference."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(filebased_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-review")

        epic_section = rendered[rendered.find("## Step 1.5"):rendered.find("## Step 2")]

        # Should check for file-based platform
        assert "elif adapter.platform == 'file-based':" in epic_section, \
            "EPIC identification should check for file-based platform"

        # Should check work item comments
        assert "comments = work_item.get('comments', [])" in epic_section, \
            "EPIC identification should get work item comments"

        assert "for comment in comments:" in epic_section, \
            "EPIC identification should iterate over comments"

        # Should check comment text for test plan pattern
        assert "'Test Plan:' in comment_text" in epic_section, \
            "EPIC identification should check for 'Test Plan:' in comment text"

        assert "'test-plan' in comment_text.lower()" in epic_section, \
            "EPIC identification should check for 'test-plan' in comment text"

    def test_checks_local_filesystem_for_test_plan(self, tmp_path, filebased_config_yaml):
        """Test that EPIC identification checks local filesystem for test plan file."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(filebased_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-review")

        epic_section = rendered[rendered.find("## Step 1.5"):rendered.find("## Step 2")]

        # Should check if test plan file exists at expected location
        assert "test_plan_path = Path(f\".claude/acceptance-tests/epic-{epic_id}-test-plan.md\")" in epic_section, \
            "EPIC identification should construct test plan file path"

        assert "if test_plan_path.exists():" in epic_section, \
            "EPIC identification should check if test plan file exists"

    def test_separates_testable_and_untestable_epics(self, tmp_path, azure_config_yaml):
        """Test that EPIC identification separates EPICs with and without test plans."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-review")

        epic_section = rendered[rendered.find("## Step 1.5"):rendered.find("## Step 2")]

        # Should maintain separate lists
        assert "testable_epics = []" in epic_section, \
            "EPIC identification should initialize testable_epics list"

        assert "epics_without_test_plans = []" in epic_section, \
            "EPIC identification should initialize epics_without_test_plans list"

        # Should append to testable_epics when test plan found
        assert "testable_epics.append(epic)" in epic_section, \
            "EPIC identification should append to testable_epics when test plan found"

        # Should append to epics_without_test_plans when test plan not found
        assert "epics_without_test_plans.append(epic)" in epic_section, \
            "EPIC identification should append to epics_without_test_plans when test plan not found"

    def test_logs_warnings_for_epics_without_test_plans(self, tmp_path, azure_config_yaml):
        """Test that EPIC identification logs warnings for EPICs without test plans."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-review")

        epic_section = rendered[rendered.find("## Step 1.5"):rendered.find("## Step 2")]

        # Should log warning when EPIC has no test plan
        assert "⚠️  WARNING: EPIC #{epic_id} has no test plan - excluded from acceptance testing" in epic_section, \
            "EPIC identification should log warning for EPICs without test plans"

        # Should display summary of EPICs without test plans
        assert "if epics_without_test_plans:" in epic_section, \
            "EPIC identification should check for EPICs without test plans"

        assert "EPIC(s) excluded from acceptance testing due to missing test plans:" in epic_section, \
            "EPIC identification should display summary of excluded EPICs"

    def test_stores_testable_epics_in_workflow_state(self, tmp_path, azure_config_yaml):
        """Test that EPIC identification stores testable EPICs in workflow state."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-review")

        epic_section = rendered[rendered.find("## Step 1.5"):rendered.find("## Step 2")]

        # Should create testable_epics_state dictionary
        assert "testable_epics_state = {" in epic_section, \
            "EPIC identification should create testable_epics_state dictionary"

        # Should store testable_epics
        assert "'testable_epics': testable_epics" in epic_section, \
            "EPIC identification state should include testable_epics"

        # Should store epics_without_test_plans
        assert "'epics_without_test_plans': epics_without_test_plans" in epic_section, \
            "EPIC identification state should include epics_without_test_plans"

        # Should store total_epics_found
        assert "'total_epics_found': len(epic_data)" in epic_section, \
            "EPIC identification state should include total_epics_found"

        # Should store testable_count
        assert "'testable_count': len(testable_epics)" in epic_section, \
            "EPIC identification state should include testable_count"

        # Should store identification timestamp
        assert "'identification_timestamp':" in epic_section and "datetime.now().isoformat()" in epic_section, \
            "EPIC identification state should include identification timestamp"

    def test_outputs_epic_identification_summary(self, tmp_path, azure_config_yaml):
        """Test that EPIC identification outputs summary of identified EPICs."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-review")

        epic_section = rendered[rendered.find("## Step 1.5"):rendered.find("## Step 2")]

        # Should output EPIC identification summary
        assert "EPIC Identification Summary" in epic_section, \
            "EPIC identification should output EPIC Identification Summary"

        # Should show total EPICs found
        assert "Total EPICs found:" in epic_section, \
            "EPIC identification summary should show total EPICs found"

        # Should show EPICs with test plans count
        assert "EPICs with test plans:" in epic_section, \
            "EPIC identification summary should show EPICs with test plans count"

        # Should show EPICs without test plans count
        assert "EPICs without test plans:" in epic_section, \
            "EPIC identification summary should show EPICs without test plans count"

    def test_handles_exceptions_when_querying_work_items(self, tmp_path, azure_config_yaml):
        """Test that EPIC identification handles exceptions when querying work items."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-review")

        epic_section = rendered[rendered.find("## Step 1.5"):rendered.find("## Step 2")]

        # Should wrap adapter queries in try-except
        assert "try:" in epic_section, \
            "EPIC identification should use try-except for adapter queries"

        assert "except Exception as e:" in epic_section, \
            "EPIC identification should catch Exception for adapter query failures"

        # Should print warning on query failure
        assert "Failed to query Epic work items" in epic_section or "⚠️" in epic_section, \
            "EPIC identification should print warning when Epic query fails"

    def test_references_vision_pattern(self, tmp_path, azure_config_yaml):
        """Test that EPIC identification references VISION.md External Source of Truth pattern."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-review")

        epic_section = rendered[rendered.find("## Step 1.5"):rendered.find("## Step 2")]

        # Should reference VISION.md pattern
        assert "VISION.md" in epic_section and "External Source of Truth" in epic_section or \
               "CRITICAL" in epic_section, \
            "EPIC identification should reference VISION.md External Source of Truth pattern"

    def test_imports_datetime_module(self, tmp_path, azure_config_yaml):
        """Test that workflow imports datetime module for timestamp generation."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-review")

        init_section = rendered[rendered.find("## Initialize Workflow"):rendered.find("## Step 1")]

        # Should import datetime
        assert "from datetime import datetime" in init_section, \
            "Workflow should import datetime module in initialization"

    def test_section_has_visual_formatting(self, tmp_path, azure_config_yaml):
        """Test that EPIC identification section has clear visual formatting."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-review")

        epic_section = rendered[rendered.find("## Step 1.5"):rendered.find("## Step 2")]

        # Should use visual separators
        assert "=" * 80 in epic_section or '="' in epic_section, \
            "EPIC identification should use visual separators for clarity"

        # Should use emojis for visual scanning
        assert "🔍" in epic_section, \
            "EPIC identification should use emoji for identification actions"

        assert "✅" in epic_section, \
            "EPIC identification should use emoji for success"

        assert "📋" in epic_section or "📊" in epic_section, \
            "EPIC identification should use emoji for metadata/summary"

        assert "💾" in epic_section, \
            "EPIC identification should use emoji for state storage"

        assert "⚠️" in epic_section, \
            "EPIC identification should use emoji for warnings"

    def test_handles_both_root_level_and_nested_fields(self, tmp_path, azure_config_yaml):
        """Test that EPIC identification handles both root-level and nested 'fields' structure."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-review")

        epic_section = rendered[rendered.find("## Step 1.5"):rendered.find("## Step 2")]

        # Should extract from both root level and fields
        # Example: item.get('title') or fields.get('System.Title')
        assert "item.get('title') or fields.get('System.Title'" in epic_section, \
            "EPIC identification should handle both root-level and nested 'fields' for title"

        assert "item.get('state') or fields.get('System.State'" in epic_section, \
            "EPIC identification should handle both root-level and nested 'fields' for state"

        assert "item.get('description') or fields.get('System.Description'" in epic_section, \
            "EPIC identification should handle both root-level and nested 'fields' for description"


@pytest.mark.unit
class TestSprintReviewEpicIdentificationEdgeCases:
    """Test edge cases for sprint-review EPIC identification."""

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

quality_standards:
  test_coverage_min: 80

agent_config:
  models:
    engineer: "claude-sonnet-4.5"
  enabled_agents:
    - senior-engineer
"""

    def test_handles_empty_epic_query_result(self, tmp_path, azure_config_yaml):
        """Test that EPIC identification handles case when no EPICs found in sprint."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-review")

        epic_section = rendered[rendered.find("## Step 1.5"):rendered.find("## Step 2")]

        # Should handle empty result gracefully
        # Python for loop handles empty list, no special handling needed
        assert "for item in epic_items:" in epic_section, \
            "EPIC identification should iterate over epic_items (handles empty gracefully)"

    def test_handles_work_item_not_found(self, tmp_path, azure_config_yaml):
        """Test that EPIC identification handles case when work item not found in adapter."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-review")

        epic_section = rendered[rendered.find("## Step 1.5"):rendered.find("## Step 2")]

        # Should check if work_item is truthy
        assert "if work_item:" in epic_section, \
            "EPIC identification should check if work_item exists"

    def test_handles_query_failure_gracefully(self, tmp_path, azure_config_yaml):
        """Test that EPIC identification handles query failure gracefully."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-review")

        epic_section = rendered[rendered.find("## Step 1.5"):rendered.find("## Step 2")]

        # Should set epic_items to empty list on failure
        assert "epic_items = []" in epic_section, \
            "EPIC identification should set epic_items to empty list on query failure"
