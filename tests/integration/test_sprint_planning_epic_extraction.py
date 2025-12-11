"""
Integration tests for sprint-planning workflow EPIC extraction.

Tests Task #1084 implementation: Extend sprint-planning workflow to identify and extract EPICs

This implements EPIC extraction from sprint scope after Step 1:
- Query adapter for Epic work items from prioritized backlog
- Extract EPIC metadata (ID, title, description, acceptance criteria, child features)
- Store EPIC data in workflow state with checkpoint
- Works with both Azure DevOps and file-based adapters
"""
import pytest
from pathlib import Path
from workflows.registry import WorkflowRegistry
from config.loader import load_config


@pytest.mark.integration
class TestSprintPlanningEpicExtraction:
    """Test suite for EPIC extraction in sprint-planning workflow."""

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

    def test_epic_extraction_step_exists_after_step1(self, tmp_path, azure_config_yaml):
        """Test that Step 1.5 EPIC extraction step is added after Step 1."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        # Step 1.5 should exist
        assert "Step 1.5: Extract EPICs from Sprint Scope" in rendered, \
            "Step 1.5 EPIC extraction step missing"

        # Step 1.5 should come after Step 1 and before Step 2
        step1_pos = rendered.find("Step 1: Prioritize Backlog")
        step15_pos = rendered.find("Step 1.5: Extract EPICs from Sprint Scope")
        step2_pos = rendered.find("Step 2: Architecture Review")

        assert step1_pos < step15_pos < step2_pos, \
            "Step 1.5 not positioned correctly between Step 1 and Step 2"

    def test_queries_adapter_for_work_item_type(self, tmp_path, azure_config_yaml):
        """Test that EPIC extraction queries adapter.get_work_item() to check work item type."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        epic_section = rendered[rendered.find("## Step 1.5"):rendered.find("## Step 2")]

        # Should query adapter for each prioritized backlog item
        assert "adapter.get_work_item(item_id)" in epic_section, \
            "EPIC extraction should query adapter.get_work_item() for each backlog item"

        # Should iterate over prioritized_backlog
        assert "for item in prioritized_backlog.get('prioritized_backlog', []):" in epic_section, \
            "EPIC extraction should iterate over prioritized_backlog"

        # Should check work item type
        assert "work_item_type ==" in epic_section, \
            "EPIC extraction should check work item type"

    def test_filters_for_epic_work_item_type(self, tmp_path, azure_config_yaml):
        """Test that EPIC extraction filters for Epic work item type."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        epic_section = rendered[rendered.find("## Step 1.5"):rendered.find("## Step 2")]

        # Should check for configured epic type from work_tracking.work_item_types.epic
        assert "work_item_type == 'Epic'" in epic_section, \
            "EPIC extraction should filter for Epic work item type from config"

        # Should append to epic_ids list when EPIC found
        assert "epic_ids.append(item_id)" in epic_section, \
            "EPIC extraction should append EPIC IDs to epic_ids list"

    def test_extracts_epic_metadata_fields(self, tmp_path, azure_config_yaml):
        """Test that EPIC extraction extracts all required metadata fields."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        epic_section = rendered[rendered.find("## Step 1.5"):rendered.find("## Step 2")]

        # Should extract epic metadata with required fields
        assert "'id': epic_id" in epic_section, \
            "EPIC extraction should extract ID"

        assert "'title':" in epic_section, \
            "EPIC extraction should extract title"

        assert "'description':" in epic_section, \
            "EPIC extraction should extract description"

        assert "'acceptance_criteria':" in epic_section, \
            "EPIC extraction should extract acceptance criteria"

        assert "'state':" in epic_section, \
            "EPIC extraction should extract state"

        assert "'child_features': []" in epic_section, \
            "EPIC extraction should initialize child_features list"

    def test_queries_for_child_features(self, tmp_path, azure_config_yaml):
        """Test that EPIC extraction queries for child FEATURE work items."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        epic_section = rendered[rendered.find("## Step 1.5"):rendered.find("## Step 2")]

        # Should get child_ids from EPIC
        assert "child_ids = epic.get('child_ids', [])" in epic_section, \
            "EPIC extraction should get child_ids from EPIC"

        # Should iterate over child_ids
        assert "for child_id in child_ids:" in epic_section, \
            "EPIC extraction should iterate over child_ids"

        # Should query adapter for each child
        assert "child = adapter.get_work_item(child_id)" in epic_section, \
            "EPIC extraction should query adapter for each child work item"

    def test_filters_child_features_by_type(self, tmp_path, azure_config_yaml):
        """Test that EPIC extraction filters child work items to only include FEATUREs."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        epic_section = rendered[rendered.find("## Step 1.5"):rendered.find("## Step 2")]

        # Should check child type
        assert "child_type = child.get('type') or child.get('fields', {}).get('System.WorkItemType')" in epic_section, \
            "EPIC extraction should get child work item type"

        # Should filter for FEATURE type
        assert "child_type == 'Feature'" in epic_section, \
            "EPIC extraction should filter children to only FEATUREs"

        # Should append to child_features list
        assert "epic_metadata['child_features'].append({" in epic_section, \
            "EPIC extraction should append FEATUREs to child_features list"

    def test_stores_child_feature_id_and_title(self, tmp_path, azure_config_yaml):
        """Test that EPIC extraction stores child FEATURE ID and title."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        epic_section = rendered[rendered.find("## Step 1.5"):rendered.find("## Step 2")]

        # Should store child FEATURE metadata
        child_feature_append = epic_section[epic_section.find("epic_metadata['child_features'].append"):epic_section.find("print(f\"  ├─ FEATURE")]

        assert "'id': child_id" in child_feature_append, \
            "EPIC extraction should store child FEATURE ID"

        assert "'title': child_title" in child_feature_append, \
            "EPIC extraction should store child FEATURE title"

    def test_handles_azure_devops_relations(self, tmp_path, azure_config_yaml):
        """Test that EPIC extraction handles Azure DevOps relations for child work items."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        epic_section = rendered[rendered.find("## Step 1.5"):rendered.find("## Step 2")]

        # Should check relations if no child_ids
        assert "relations = epic.get('relations', [])" in epic_section, \
            "EPIC extraction should get relations from EPIC"

        assert "for relation in relations:" in epic_section, \
            "EPIC extraction should iterate over relations"

        # Should check for Hierarchy-Forward relation type (Azure DevOps)
        assert "'Hierarchy-Forward' in rel_type" in epic_section, \
            "EPIC extraction should check for Hierarchy-Forward relation type"

        # Should extract work item ID from URL
        assert "child_id = target_url.split('/')[-1]" in epic_section, \
            "EPIC extraction should extract work item ID from URL"

    def test_stores_epic_data_in_workflow_state(self, tmp_path, azure_config_yaml):
        """Test that EPIC extraction stores EPIC data in workflow state."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        epic_section = rendered[rendered.find("## Step 1.5"):rendered.find("## Step 2")]

        # Should create epic_extraction_state dictionary
        assert "epic_extraction_state = {" in epic_section, \
            "EPIC extraction should create epic_extraction_state dictionary"

        # Should store epic_ids
        assert "'epic_ids': epic_ids" in epic_section, \
            "EPIC extraction state should include epic_ids"

        # Should store epic_data
        assert "'epic_data': epic_data" in epic_section, \
            "EPIC extraction state should include epic_data"

        # Should store extraction timestamp
        assert "'extraction_timestamp':" in epic_section and "datetime.now().isoformat()" in epic_section, \
            "EPIC extraction state should include extraction timestamp"

    def test_outputs_epic_extraction_summary(self, tmp_path, azure_config_yaml):
        """Test that EPIC extraction outputs summary of extracted EPICs."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        epic_section = rendered[rendered.find("## Step 1.5"):rendered.find("## Step 2")]

        # Should output EPIC extraction summary
        assert "EPIC Extraction Summary" in epic_section, \
            "EPIC extraction should output EPIC Extraction Summary"

        # Should show EPICs found count
        assert "EPICs found:" in epic_section and "len(epic_data)" in epic_section, \
            "EPIC extraction summary should show EPICs found count"

        # Should show total child FEATUREs count
        assert "Total child FEATUREs:" in epic_section, \
            "EPIC extraction summary should show total child FEATUREs count"

        assert "sum(len(e['child_features']) for e in epic_data)" in epic_section, \
            "EPIC extraction summary should calculate total child FEATUREs"

    def test_handles_exceptions_when_querying_work_items(self, tmp_path, azure_config_yaml):
        """Test that EPIC extraction handles exceptions when querying work items."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        epic_section = rendered[rendered.find("## Step 1.5"):rendered.find("## Step 2")]

        # Should wrap adapter queries in try-except
        assert "try:" in epic_section, \
            "EPIC extraction should use try-except for adapter queries"

        assert "except Exception as e:" in epic_section, \
            "EPIC extraction should catch Exception for adapter query failures"

        # Should print warning on query failure
        assert "Failed to query work item" in epic_section or "⚠️" in epic_section, \
            "EPIC extraction should print warning when work item query fails"

    def test_references_vision_pattern(self, tmp_path, azure_config_yaml):
        """Test that EPIC extraction references VISION.md External Source of Truth pattern."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        epic_section = rendered[rendered.find("## Step 1.5"):rendered.find("## Step 2")]

        # Should reference VISION.md pattern
        assert "VISION.md" in epic_section and "External Source of Truth" in epic_section or \
               "CRITICAL" in epic_section, \
            "EPIC extraction should reference VISION.md External Source of Truth pattern"

    def test_works_with_file_based_adapter(self, tmp_path, filebased_config_yaml):
        """Test that EPIC extraction works with file-based adapter (not just Azure DevOps)."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(filebased_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        epic_section = rendered[rendered.find("## Step 1.5"):rendered.find("## Step 2")]

        # Should use generic adapter methods
        assert "adapter.get_work_item(" in epic_section, \
            "EPIC extraction should use generic adapter.get_work_item()"

        # Should handle both Azure DevOps and file-based patterns
        assert "child_ids = epic.get('child_ids', [])" in epic_section, \
            "EPIC extraction should check child_ids (file-based pattern)"

        assert "relations = epic.get('relations', [])" in epic_section, \
            "EPIC extraction should check relations (Azure DevOps pattern)"

    def test_prints_extraction_progress(self, tmp_path, azure_config_yaml):
        """Test that EPIC extraction prints progress messages."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        epic_section = rendered[rendered.find("## Step 1.5"):rendered.find("## Step 2")]

        # Should print extraction header
        assert "Extracting EPICs from sprint scope" in epic_section, \
            "EPIC extraction should print extraction header"

        # Should print when EPIC found
        assert "Found EPIC:" in epic_section, \
            "EPIC extraction should print when EPIC found"

        # Should print when querying for EPIC metadata
        assert "Querying adapter for EPIC metadata" in epic_section, \
            "EPIC extraction should print when querying for EPIC metadata"

        # Should print success for each extracted EPIC
        assert "Extracted EPIC" in epic_section, \
            "EPIC extraction should print success for each extracted EPIC"

        # Should print child FEATUREs
        assert "FEATURE #" in epic_section, \
            "EPIC extraction should print child FEATURE details"

    def test_section_has_visual_formatting(self, tmp_path, azure_config_yaml):
        """Test that EPIC extraction section has clear visual formatting."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        epic_section = rendered[rendered.find("## Step 1.5"):rendered.find("## Step 2")]

        # Should use visual separators
        assert "=" * 80 in epic_section or '="' in epic_section, \
            "EPIC extraction should use visual separators for clarity"

        # Should use emojis for visual scanning
        assert "🔍" in epic_section, \
            "EPIC extraction should use emoji for extraction actions"

        assert "✅" in epic_section, \
            "EPIC extraction should use emoji for success"

        assert "📋" in epic_section or "📊" in epic_section, \
            "EPIC extraction should use emoji for metadata/summary"

        assert "💾" in epic_section, \
            "EPIC extraction should use emoji for state storage"

    def test_mentions_test_plan_generation_use_case(self, tmp_path, azure_config_yaml):
        """Test that EPIC extraction mentions test plan generation as the use case."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        epic_section = rendered[rendered.find("## Step 1.5"):rendered.find("## Step 2")]

        # Should mention test plan generation
        assert "test plan generation" in epic_section.lower(), \
            "EPIC extraction should mention test plan generation as use case"

    def test_extracts_both_root_level_and_nested_fields(self, tmp_path, azure_config_yaml):
        """Test that EPIC extraction handles both root-level and nested 'fields' structure."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        epic_section = rendered[rendered.find("## Step 1.5"):rendered.find("## Step 2")]

        # Should extract from both root level and fields
        # Example: epic.get('title') or fields.get('System.Title')
        assert "epic.get('title') or fields.get('System.Title'" in epic_section, \
            "EPIC extraction should handle both root-level and nested 'fields' for title"

        assert "epic.get('description') or fields.get('System.Description'" in epic_section, \
            "EPIC extraction should handle both root-level and nested 'fields' for description"

        assert "epic.get('state') or fields.get('System.State'" in epic_section, \
            "EPIC extraction should handle both root-level and nested 'fields' for state"


@pytest.mark.integration
class TestSprintPlanningEpicExtractionEdgeCases:
    """Test edge cases for sprint-planning EPIC extraction."""

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

    def test_handles_empty_prioritized_backlog(self, tmp_path, azure_config_yaml):
        """Test that EPIC extraction handles case when prioritized_backlog is empty."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        epic_section = rendered[rendered.find("## Step 1.5"):rendered.find("## Step 2")]

        # Should iterate over prioritized_backlog (handles empty gracefully)
        assert "for item in prioritized_backlog.get('prioritized_backlog', []):" in epic_section, \
            "EPIC extraction should iterate over prioritized_backlog with default empty list"

        # Python for loop handles empty list gracefully, no special handling needed

    def test_handles_epic_with_no_children(self, tmp_path, azure_config_yaml):
        """Test that EPIC extraction handles EPICs with no child work items."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        epic_section = rendered[rendered.find("## Step 1.5"):rendered.find("## Step 2")]

        # Should initialize child_features as empty list
        assert "'child_features': []" in epic_section, \
            "EPIC extraction should initialize child_features as empty list"

        # Should use get() with default empty list for child_ids
        assert "child_ids = epic.get('child_ids', [])" in epic_section, \
            "EPIC extraction should use get() with default empty list for child_ids"

    def test_handles_work_item_not_found(self, tmp_path, azure_config_yaml):
        """Test that EPIC extraction handles case when work item not found in adapter."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        epic_section = rendered[rendered.find("## Step 1.5"):rendered.find("## Step 2")]

        # Should check if work_item is truthy
        assert "if work_item:" in epic_section, \
            "EPIC extraction should check if work_item exists"

        # Should check if epic is truthy
        assert "if not epic:" in epic_section, \
            "EPIC extraction should check if epic exists"

        # Should continue or print warning when not found
        assert "continue" in epic_section, \
            "EPIC extraction should continue when EPIC not found"
