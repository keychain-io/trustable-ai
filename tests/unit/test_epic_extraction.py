"""
Unit tests for EPIC extraction logic in sprint-planning workflow.

Tests Task #1084 implementation at the unit level:
- EPIC filtering logic
- Child FEATURE extraction
- Metadata field mapping
- Workflow state data structure
"""
import pytest
from workflows.registry import WorkflowRegistry
from config.loader import load_config
from pathlib import Path


@pytest.mark.unit
class TestEpicExtractionLogic:
    """Unit tests for EPIC extraction logic."""

    @pytest.fixture
    def sample_config_yaml(self):
        """Minimal configuration for testing."""
        return """
project:
  name: "Test"
  type: "web-application"
  tech_stack:
    languages: ["Python"]

work_tracking:
  platform: "file-based"
  work_item_types:
    epic: "Epic"
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

    def test_epic_extraction_initializes_lists(self, tmp_path, sample_config_yaml):
        """Test that EPIC extraction initializes epic_ids and epic_data lists."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(sample_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)
        rendered = registry.render_workflow("sprint-planning")

        epic_section = rendered[rendered.find("## Step 1.5"):rendered.find("## Step 2")]

        # Should initialize epic_ids list
        assert "epic_ids = []" in epic_section, \
            "EPIC extraction should initialize epic_ids list"

        # Should initialize epic_data list
        assert "epic_data = []" in epic_section, \
            "EPIC extraction should initialize epic_data list"

    def test_epic_metadata_structure(self, tmp_path, sample_config_yaml):
        """Test that EPIC metadata has correct structure."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(sample_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)
        rendered = registry.render_workflow("sprint-planning")

        epic_section = rendered[rendered.find("## Step 1.5"):rendered.find("## Step 2")]

        # Should have epic_metadata dictionary
        assert "epic_metadata = {" in epic_section, \
            "EPIC extraction should create epic_metadata dictionary"

        # Required fields
        required_fields = ['id', 'title', 'description', 'acceptance_criteria', 'state', 'child_features']

        for field in required_fields:
            assert f"'{field}':" in epic_section, \
                f"EPIC metadata should include '{field}' field"

    def test_epic_extraction_state_structure(self, tmp_path, sample_config_yaml):
        """Test that epic_extraction_state has correct structure."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(sample_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)
        rendered = registry.render_workflow("sprint-planning")

        epic_section = rendered[rendered.find("## Step 1.5"):rendered.find("## Step 2")]

        # Should create epic_extraction_state
        assert "epic_extraction_state = {" in epic_section, \
            "EPIC extraction should create epic_extraction_state dictionary"

        # Required state fields
        required_state_fields = ['epic_ids', 'epic_data', 'extraction_timestamp']

        for field in required_state_fields:
            assert f"'{field}':" in epic_section, \
                f"EPIC extraction state should include '{field}' field"

    def test_filters_only_epic_work_items(self, tmp_path, sample_config_yaml):
        """Test that only Epic work item types are extracted."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(sample_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)
        rendered = registry.render_workflow("sprint-planning")

        epic_section = rendered[rendered.find("## Step 1.5"):rendered.find("## Step 2")]

        # Should check work_item_type against configured epic type
        assert "if work_item_type == 'Epic':" in epic_section, \
            "EPIC extraction should filter for Epic work item type"

        # Should only append to epic_ids when type matches
        epic_filter_section = epic_section[
            epic_section.find("if work_item_type == 'Epic':"):
            epic_section.find("except Exception as e:")
        ]

        assert "epic_ids.append(item_id)" in epic_filter_section, \
            "EPIC extraction should only append EPIC IDs when type matches"

    def test_filters_only_feature_child_work_items(self, tmp_path, sample_config_yaml):
        """Test that only Feature work item types are included in child_features."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(sample_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)
        rendered = registry.render_workflow("sprint-planning")

        epic_section = rendered[rendered.find("## Step 1.5"):rendered.find("## Step 2")]

        # Should check child_type against configured feature type
        assert "if child_type == 'Feature':" in epic_section, \
            "EPIC extraction should filter children for Feature work item type"

        # Should only append to child_features when type matches
        child_filter_section = epic_section[
            epic_section.find("if child_type == 'Feature':"):
            epic_section.find("except Exception as e:\n                print(f\"  ⚠️  Failed to query child")
        ]

        assert "epic_metadata['child_features'].append(" in child_filter_section, \
            "EPIC extraction should only append FEATUREs to child_features"

    def test_child_feature_metadata_structure(self, tmp_path, sample_config_yaml):
        """Test that child FEATURE metadata has correct structure."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(sample_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)
        rendered = registry.render_workflow("sprint-planning")

        epic_section = rendered[rendered.find("## Step 1.5"):rendered.find("## Step 2")]

        # Find child_features append section
        child_append = epic_section[
            epic_section.find("epic_metadata['child_features'].append({"):
            epic_section.find("print(f\"  ├─ FEATURE")
        ]

        # Required child feature fields
        assert "'id': child_id" in child_append, \
            "Child FEATURE should include id field"

        assert "'title': child_title" in child_append, \
            "Child FEATURE should include title field"

    def test_uses_configured_work_item_types(self, tmp_path):
        """Test that EPIC extraction uses work item types from configuration."""
        # Test with custom work item types
        custom_config = """
project:
  name: "Test"
  type: "web-application"
  tech_stack:
    languages: ["Python"]

work_tracking:
  platform: "file-based"
  work_item_types:
    epic: "CustomEpic"
    feature: "CustomFeature"
    task: "Task"

quality_standards:
  test_coverage_min: 80

agent_config:
  models:
    engineer: "claude-sonnet-4.5"
  enabled_agents:
    - senior-engineer
"""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(custom_config, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)
        rendered = registry.render_workflow("sprint-planning")

        epic_section = rendered[rendered.find("## Step 1.5"):rendered.find("## Step 2")]

        # Should use configured epic type
        assert "work_item_type == 'CustomEpic'" in epic_section, \
            "EPIC extraction should use configured epic type from work_tracking.work_item_types.epic"

        # Should use configured feature type
        assert "child_type == 'CustomFeature'" in epic_section, \
            "EPIC extraction should use configured feature type from work_tracking.work_item_types.feature"

    def test_appends_epic_to_epic_data_list(self, tmp_path, sample_config_yaml):
        """Test that extracted EPIC metadata is appended to epic_data list."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(sample_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)
        rendered = registry.render_workflow("sprint-planning")

        epic_section = rendered[rendered.find("## Step 1.5"):rendered.find("## Step 2")]

        # Should append epic_metadata to epic_data
        assert "epic_data.append(epic_metadata)" in epic_section, \
            "EPIC extraction should append epic_metadata to epic_data list"

    def test_handles_missing_fields_with_defaults(self, tmp_path, sample_config_yaml):
        """Test that EPIC extraction handles missing fields with appropriate defaults."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(sample_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)
        rendered = registry.render_workflow("sprint-planning")

        epic_section = rendered[rendered.find("## Step 1.5"):rendered.find("## Step 2")]

        # Should use get() with defaults for optional fields
        assert "fields.get('Microsoft.VSTS.Common.AcceptanceCriteria', '')" in epic_section, \
            "EPIC extraction should use get() with default empty string for acceptance_criteria"

        # Should handle fields in both root and nested 'fields' structure
        assert "epic.get('title') or fields.get('System.Title', '')" in epic_section, \
            "EPIC extraction should check both root and fields for title with default"

    def test_checks_for_both_child_ids_and_relations(self, tmp_path, sample_config_yaml):
        """Test that EPIC extraction checks both child_ids and relations for children."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(sample_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)
        rendered = registry.render_workflow("sprint-planning")

        epic_section = rendered[rendered.find("## Step 1.5"):rendered.find("## Step 2")]

        # Should first try child_ids (file-based pattern)
        assert "child_ids = epic.get('child_ids', [])" in epic_section, \
            "EPIC extraction should first check child_ids"

        # Should check relations if no child_ids (Azure DevOps pattern)
        assert "if not child_ids:" in epic_section, \
            "EPIC extraction should check if child_ids is empty"

        assert "relations = epic.get('relations', [])" in epic_section, \
            "EPIC extraction should check relations when no child_ids"

    def test_extracts_child_id_from_url(self, tmp_path, sample_config_yaml):
        """Test that EPIC extraction extracts child work item ID from URL."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(sample_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)
        rendered = registry.render_workflow("sprint-planning")

        epic_section = rendered[rendered.find("## Step 1.5"):rendered.find("## Step 2")]

        # Should extract work item ID from URL
        assert "child_id = target_url.split('/')[-1]" in epic_section, \
            "EPIC extraction should extract work item ID from last segment of URL"

    def test_checks_multiple_relation_types(self, tmp_path, sample_config_yaml):
        """Test that EPIC extraction checks for multiple relation type patterns."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(sample_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)
        rendered = registry.render_workflow("sprint-planning")

        epic_section = rendered[rendered.find("## Step 1.5"):rendered.find("## Step 2")]

        # Should check for Hierarchy-Forward (Azure DevOps)
        assert "'Hierarchy-Forward' in rel_type" in epic_section, \
            "EPIC extraction should check for Hierarchy-Forward relation type"

        # Should check for 'child' in relation type (file-based)
        assert "'child' in rel_type.lower()" in epic_section, \
            "EPIC extraction should check for 'child' in relation type (case-insensitive)"

    def test_handles_both_url_and_target_id_patterns(self, tmp_path, sample_config_yaml):
        """Test that EPIC extraction handles both URL and direct target_id patterns."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(sample_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)
        rendered = registry.render_workflow("sprint-planning")

        epic_section = rendered[rendered.find("## Step 1.5"):rendered.find("## Step 2")]

        # Should check for URL pattern
        assert "if target_url:" in epic_section, \
            "EPIC extraction should check if target_url exists"

        # Should check for direct target_id
        assert "elif 'target_id' in relation:" in epic_section, \
            "EPIC extraction should check for direct target_id in relation"


@pytest.mark.unit
class TestEpicExtractionOutputFormatting:
    """Unit tests for EPIC extraction output formatting."""

    @pytest.fixture
    def sample_config_yaml(self):
        """Minimal configuration for testing."""
        return """
project:
  name: "Test"
  type: "web-application"
  tech_stack:
    languages: ["Python"]

work_tracking:
  platform: "file-based"
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

    def test_uses_tree_structure_for_child_features(self, tmp_path, sample_config_yaml):
        """Test that EPIC extraction uses tree structure (├─) for child FEATUREs."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(sample_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)
        rendered = registry.render_workflow("sprint-planning")

        epic_section = rendered[rendered.find("## Step 1.5"):rendered.find("## Step 2")]

        # Should use tree structure for child features
        assert "├─ FEATURE" in epic_section, \
            "EPIC extraction should use tree structure (├─) for child FEATUREs"

    def test_prints_child_feature_count_in_summary(self, tmp_path, sample_config_yaml):
        """Test that EPIC extraction prints child feature count in extracted EPIC summary."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(sample_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)
        rendered = registry.render_workflow("sprint-planning")

        epic_section = rendered[rendered.find("## Step 1.5"):rendered.find("## Step 2")]

        # Should print child feature count when EPIC extracted
        assert "len(epic_metadata['child_features'])" in epic_section, \
            "EPIC extraction should print child feature count"

        assert "child features" in epic_section, \
            "EPIC extraction summary should mention 'child features'"

    def test_prints_total_child_features_across_all_epics(self, tmp_path, sample_config_yaml):
        """Test that EPIC extraction prints total child FEATUREs across all EPICs."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(sample_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)
        rendered = registry.render_workflow("sprint-planning")

        epic_section = rendered[rendered.find("## Step 1.5"):rendered.find("## Step 2")]

        # Should calculate total child features using sum()
        assert "sum(len(e['child_features']) for e in epic_data)" in epic_section, \
            "EPIC extraction should calculate total child FEATUREs across all EPICs"

    def test_includes_checkpoint_comment(self, tmp_path, sample_config_yaml):
        """Test that EPIC extraction includes checkpoint comment."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(sample_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)
        rendered = registry.render_workflow("sprint-planning")

        epic_section = rendered[rendered.find("## Step 1.5"):rendered.find("## Step 2")]

        # Should include checkpoint comment
        assert "Checkpoint:" in epic_section or "checkpoint" in epic_section.lower(), \
            "EPIC extraction should include checkpoint comment"
