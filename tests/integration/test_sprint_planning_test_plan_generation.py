"""
Integration tests for sprint-planning workflow test plan generation.

Tests Task #1086 implementation: Add workflow step to generate and store test plans for EPICs

This implements test plan generation after EPIC extraction (Step 1.6):
- Creates .claude/acceptance-tests/ directory if missing
- Spawns qa-tester agent for each EPIC to generate test plan
- Writes test plan markdown to epic-{id}-test-plan.md with UTF-8 encoding
- Stores test plan file paths in workflow state
- Handles errors gracefully (directory creation, file write, agent failure)
"""
import pytest
from pathlib import Path
from workflows.registry import WorkflowRegistry
from config.loader import load_config


@pytest.mark.integration
class TestSprintPlanningTestPlanGeneration:
    """Test suite for test plan generation in sprint-planning workflow."""

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
    qa: "claude-sonnet-4.5"
  enabled_agents:
    - business-analyst
    - project-architect
    - senior-engineer
    - scrum-master
    - qa-tester
"""

    def test_test_plan_generation_step_exists_after_step15(self, tmp_path, azure_config_yaml):
        """Test that Step 1.6 test plan generation step exists after Step 1.5."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        # Step 1.6 should exist
        assert "Step 1.6: Generate Test Plans for EPICs" in rendered, \
            "Step 1.6 test plan generation step missing"

        # Step 1.6 should come after Step 1.5 and before Step 2
        step15_pos = rendered.find("Step 1.5: Extract EPICs from Sprint Scope")
        step16_pos = rendered.find("Step 1.6: Generate Test Plans for EPICs")
        step2_pos = rendered.find("Step 2: Architecture Review")

        assert step15_pos < step16_pos < step2_pos, \
            "Step 1.6 not positioned correctly between Step 1.5 and Step 2"

    def test_creates_acceptance_tests_directory(self, tmp_path, azure_config_yaml):
        """Test that Step 1.6 creates .claude/acceptance-tests/ directory."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        step16_section = rendered[rendered.find("## Step 1.6"):rendered.find("## Step 2")]

        # Should define test_plans_dir variable
        assert 'test_plans_dir = ".claude/acceptance-tests"' in step16_section, \
            "Step 1.6 should define test_plans_dir as .claude/acceptance-tests"

        # Should check if directory exists
        assert "os.path.exists(test_plans_dir)" in step16_section, \
            "Step 1.6 should check if directory exists"

        # Should create directory if it doesn't exist
        assert "os.makedirs(test_plans_dir, exist_ok=True)" in step16_section, \
            "Step 1.6 should create directory with os.makedirs()"

    def test_handles_directory_creation_failure(self, tmp_path, azure_config_yaml):
        """Test that Step 1.6 handles directory creation failure gracefully."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        step16_section = rendered[rendered.find("## Step 1.6"):rendered.find("## Step 2")]

        # Should wrap directory creation in try-except
        assert "try:" in step16_section and "os.makedirs" in step16_section, \
            "Step 1.6 should wrap directory creation in try block"

        assert "except Exception as e:" in step16_section, \
            "Step 1.6 should catch Exception for directory creation failures"

        # Should print error and exit on directory creation failure
        assert "Failed to create directory" in step16_section or "ERROR" in step16_section, \
            "Step 1.6 should print error when directory creation fails"

        assert "sys.exit(1)" in step16_section, \
            "Step 1.6 should exit with error code when directory creation fails"

    def test_iterates_over_epic_data(self, tmp_path, azure_config_yaml):
        """Test that Step 1.6 iterates over epic_data from Step 1.5."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        step16_section = rendered[rendered.find("## Step 1.6"):rendered.find("## Step 2")]

        # Should iterate over epic_data from Step 1.5
        assert "for epic in epic_data:" in step16_section, \
            "Step 1.6 should iterate over epic_data from Step 1.5"

        # Should extract epic ID and title
        assert "epic_id = epic.get('id')" in step16_section, \
            "Step 1.6 should extract epic ID"

        assert "epic_title = epic.get('title'" in step16_section, \
            "Step 1.6 should extract epic title"

    def test_prepares_epic_input_for_qa_tester(self, tmp_path, azure_config_yaml):
        """Test that Step 1.6 prepares EPIC data for qa-tester agent."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        step16_section = rendered[rendered.find("## Step 1.6"):rendered.find("## Step 2")]

        # Should prepare epic_input dictionary
        assert "epic_input = {" in step16_section, \
            "Step 1.6 should prepare epic_input dictionary"

        # Should include epic metadata
        assert "'epic': {" in step16_section, \
            "Step 1.6 should include epic metadata"

        assert "'id': epic_id" in step16_section, \
            "Step 1.6 should include epic ID in input"

        assert "'title': epic_title" in step16_section, \
            "Step 1.6 should include epic title in input"

        assert "'summary':" in step16_section and "epic.get('description'" in step16_section, \
            "Step 1.6 should include epic description/summary in input"

        assert "'acceptance_criteria':" in step16_section, \
            "Step 1.6 should include acceptance criteria in input"

        # Should include child features
        assert "'features':" in step16_section and "epic.get('child_features'" in step16_section, \
            "Step 1.6 should include child features in input"

    def test_spawns_qa_tester_agent(self, tmp_path, azure_config_yaml):
        """Test that Step 1.6 spawns qa-tester agent via Task tool."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        step16_section = rendered[rendered.find("## Step 1.6"):rendered.find("## Step 2")]

        # Should spawn qa-tester agent
        assert "/qa-tester" in step16_section, \
            "Step 1.6 should spawn /qa-tester agent"

        # Should show Task tool invocation pattern (commented for template)
        assert "Task(" in step16_section or "Spawn /qa-tester agent" in step16_section, \
            "Step 1.6 should show Task tool invocation pattern"

        # Should pass EPIC data to agent
        assert "json.dumps(epic_input" in step16_section or "EPIC Details" in step16_section, \
            "Step 1.6 should pass EPIC data to qa-tester agent"

    def test_handles_agent_json_parsing_errors(self, tmp_path, azure_config_yaml):
        """Test that Step 1.6 handles JSON parsing errors from agent response."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        step16_section = rendered[rendered.find("## Step 1.6"):rendered.find("## Step 2")]

        # Should handle JSONDecodeError
        assert "json.JSONDecodeError" in step16_section or "parse JSON" in step16_section, \
            "Step 1.6 should handle JSON parsing errors from agent"

        # Should print error message
        assert "Failed to parse JSON" in step16_section or "invalid JSON" in step16_section, \
            "Step 1.6 should print error when JSON parsing fails"

        # Should continue to next EPIC on error
        assert "continue" in step16_section, \
            "Step 1.6 should continue to next EPIC on agent error"

    def test_writes_test_plan_to_file(self, tmp_path, azure_config_yaml):
        """Test that Step 1.6 writes test plan to markdown file."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        step16_section = rendered[rendered.find("## Step 1.6"):rendered.find("## Step 2")]

        # Should construct filename from epic_id
        assert 'test_plan_filename = f"epic-{epic_id}-test-plan.md"' in step16_section, \
            "Step 1.6 should construct filename as epic-{id}-test-plan.md"

        # Should construct full file path
        assert "test_plan_filepath = os.path.join(test_plans_dir, test_plan_filename)" in step16_section, \
            "Step 1.6 should construct full file path"

        # Should open file for writing with UTF-8 encoding
        assert "open(test_plan_filepath, 'w', encoding='utf-8')" in step16_section, \
            "Step 1.6 should open file with UTF-8 encoding for cross-platform compatibility"

        # Should write test plan markdown
        assert "f.write(test_plan_markdown)" in step16_section, \
            "Step 1.6 should write test plan markdown to file"

    def test_uses_utf8_encoding_for_file_write(self, tmp_path, azure_config_yaml):
        """Test that Step 1.6 uses UTF-8 encoding for file write (cross-platform)."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        step16_section = rendered[rendered.find("## Step 1.6"):rendered.find("## Step 2")]

        # Should explicitly specify UTF-8 encoding
        assert "encoding='utf-8'" in step16_section, \
            "Step 1.6 should use explicit UTF-8 encoding for Windows/Linux/macOS compatibility"

    def test_handles_file_write_errors(self, tmp_path, azure_config_yaml):
        """Test that Step 1.6 handles file write errors gracefully."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        step16_section = rendered[rendered.find("## Step 1.6"):rendered.find("## Step 2")]

        # Should wrap file write in try-except
        assert "try:" in step16_section, \
            "Step 1.6 should wrap file write in try block"

        # Should catch IOError
        assert "except IOError as e:" in step16_section, \
            "Step 1.6 should catch IOError for file write failures"

        # Should print error message
        assert "Failed to write test plan file" in step16_section, \
            "Step 1.6 should print error when file write fails"

        # Should mention checking permissions
        assert "permissions" in step16_section.lower() or "disk space" in step16_section.lower(), \
            "Step 1.6 should mention checking file permissions and disk space"

        # Should continue to next EPIC on error
        assert "continue" in step16_section, \
            "Step 1.6 should continue to next EPIC on file write error"

    def test_stores_file_path_in_workflow_state(self, tmp_path, azure_config_yaml):
        """Test that Step 1.6 stores test plan file path in workflow state."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        step16_section = rendered[rendered.find("## Step 1.6"):rendered.find("## Step 2")]

        # Should append file path to test_plan_files list
        assert "test_plan_files.append({" in step16_section, \
            "Step 1.6 should append test plan file metadata to list"

        # Should store epic_id
        assert "'epic_id': epic_id" in step16_section, \
            "Step 1.6 should store epic_id in file metadata"

        # Should store epic_title
        assert "'epic_title': epic_title" in step16_section, \
            "Step 1.6 should store epic_title in file metadata"

        # Should store file_path
        assert "'file_path': test_plan_filepath" in step16_section, \
            "Step 1.6 should store file_path in file metadata"

        # Should store generation timestamp
        assert "'generated_at':" in step16_section and "datetime.now().isoformat()" in step16_section, \
            "Step 1.6 should store generation timestamp"

    def test_creates_test_plan_state_for_workflow(self, tmp_path, azure_config_yaml):
        """Test that Step 1.6 creates test_plan_state for workflow state."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        step16_section = rendered[rendered.find("## Step 1.6"):rendered.find("## Step 2")]

        # Should create test_plan_state dictionary
        assert "test_plan_state = {" in step16_section, \
            "Step 1.6 should create test_plan_state dictionary"

        # Should store test_plan_files
        assert "'test_plan_files': test_plan_files" in step16_section, \
            "Step 1.6 test_plan_state should include test_plan_files"

        # Should store test_plans_directory
        assert "'test_plans_directory': test_plans_dir" in step16_section, \
            "Step 1.6 test_plan_state should include test_plans_directory"

        # Should store generation_timestamp
        assert "'generation_timestamp':" in step16_section and "datetime.now().isoformat()" in step16_section, \
            "Step 1.6 test_plan_state should include generation_timestamp"

    def test_outputs_test_plan_generation_summary(self, tmp_path, azure_config_yaml):
        """Test that Step 1.6 outputs summary of test plan generation."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        step16_section = rendered[rendered.find("## Step 1.6"):rendered.find("## Step 2")]

        # Should output test plan generation summary
        assert "Test Plan Generation Summary" in step16_section, \
            "Step 1.6 should output Test Plan Generation Summary"

        # Should show EPICs processed count
        assert "EPICs processed:" in step16_section and "len(epic_data)" in step16_section, \
            "Step 1.6 summary should show EPICs processed count"

        # Should show test plans generated count
        assert "Test plans generated:" in step16_section and "len(test_plan_files)" in step16_section, \
            "Step 1.6 summary should show test plans generated count"

        # Should show test plans directory
        assert "Test plans directory:" in step16_section and "test_plans_dir" in step16_section, \
            "Step 1.6 summary should show test plans directory"

    def test_mentions_workflow_state_storage(self, tmp_path, azure_config_yaml):
        """Test that Step 1.6 mentions storing file paths in workflow state."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        step16_section = rendered[rendered.find("## Step 1.6"):rendered.find("## Step 2")]

        # Should mention workflow state storage
        assert "workflow state" in step16_section.lower(), \
            "Step 1.6 should mention storing data in workflow state"

        # Should mention attachment/linking in Step 7
        assert "attachment" in step16_section.lower() or "linking" in step16_section.lower(), \
            "Step 1.6 should mention attachment/linking to work items"

    def test_imports_required_modules(self, tmp_path, azure_config_yaml):
        """Test that Step 1.6 imports required Python modules."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        step16_section = rendered[rendered.find("## Step 1.6"):rendered.find("## Step 2")]

        # Should import os for directory operations
        assert "import os" in step16_section, \
            "Step 1.6 should import os module"

        # Should import json for parsing agent response
        assert "import json" in step16_section, \
            "Step 1.6 should import json module"

        # Should import datetime for timestamps
        assert "from datetime import datetime" in step16_section, \
            "Step 1.6 should import datetime module"

    def test_section_has_visual_formatting(self, tmp_path, azure_config_yaml):
        """Test that Step 1.6 has clear visual formatting."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        step16_section = rendered[rendered.find("## Step 1.6"):rendered.find("## Step 2")]

        # Should use visual separators
        assert "=" * 80 in step16_section or '="' in step16_section, \
            "Step 1.6 should use visual separators for clarity"

        # Should use emojis for visual scanning
        assert "🧪" in step16_section, \
            "Step 1.6 should use emoji for test-related actions"

        assert "📋" in step16_section, \
            "Step 1.6 should use emoji for EPIC items"

        assert "🤖" in step16_section, \
            "Step 1.6 should use emoji for agent spawning"

        assert "✅" in step16_section, \
            "Step 1.6 should use emoji for success"

        assert "❌" in step16_section, \
            "Step 1.6 should use emoji for errors"

        assert "📊" in step16_section, \
            "Step 1.6 should use emoji for summary"

        assert "💾" in step16_section, \
            "Step 1.6 should use emoji for state storage"

    def test_references_critical_importance(self, tmp_path, azure_config_yaml):
        """Test that Step 1.6 references critical importance of test plan generation."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        step16_section = rendered[rendered.find("## Step 1.6"):rendered.find("## Step 2")]

        # Should mention CRITICAL
        assert "CRITICAL" in step16_section, \
            "Step 1.6 should reference critical importance"

    def test_workflow_overview_includes_step16(self, tmp_path, azure_config_yaml):
        """Test that workflow overview includes Step 1.6."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        overview = rendered[rendered.find("## Workflow Overview"):rendered.find("## Initialize Workflow")]

        # Should list Step 1.6 in overview
        assert "Step 1.6:" in overview or "1.6" in overview, \
            "Workflow overview should include Step 1.6"

        # Should mention qa-tester agent
        assert "qa-tester" in overview.lower(), \
            "Workflow overview should mention qa-tester agent for Step 1.6"

    def test_agent_commands_table_includes_qa_tester(self, tmp_path, azure_config_yaml):
        """Test that Agent Commands table includes qa-tester for Step 1.6."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        # Find Agent Commands table
        table_start = rendered.find("## Agent Commands Used")
        table_section = rendered[table_start:table_start + 1000]

        # Should include Step 1.6 in table
        assert "1.6" in table_section, \
            "Agent Commands table should include Step 1.6"

        # Should list qa-tester agent
        assert "qa-tester" in table_section, \
            "Agent Commands table should list /qa-tester agent for Step 1.6"


@pytest.mark.integration
class TestSprintPlanningTestPlanGenerationEdgeCases:
    """Test edge cases for sprint-planning test plan generation."""

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
    qa: "claude-sonnet-4.5"
  enabled_agents:
    - qa-tester
"""

    def test_handles_empty_epic_data(self, tmp_path, azure_config_yaml):
        """Test that Step 1.6 handles case when epic_data is empty."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        step16_section = rendered[rendered.find("## Step 1.6"):rendered.find("## Step 2")]

        # Should iterate over epic_data (handles empty gracefully)
        assert "for epic in epic_data:" in step16_section, \
            "Step 1.6 should iterate over epic_data with for loop (handles empty gracefully)"

        # Python for loop handles empty list gracefully, no special handling needed

    def test_handles_epic_with_no_child_features(self, tmp_path, azure_config_yaml):
        """Test that Step 1.6 handles EPICs with no child features."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        step16_section = rendered[rendered.find("## Step 1.6"):rendered.find("## Step 2")]

        # Should use get() with default empty list for child_features
        assert "epic.get('child_features', [])" in step16_section or \
               "epic.get('child_features')" in step16_section, \
            "Step 1.6 should use get() for child_features (handles missing gracefully)"

    def test_handles_missing_epic_fields(self, tmp_path, azure_config_yaml):
        """Test that Step 1.6 handles missing EPIC fields gracefully."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("sprint-planning")

        step16_section = rendered[rendered.find("## Step 1.6"):rendered.find("## Step 2")]

        # Should use get() with defaults for optional fields
        assert "epic.get('title', " in step16_section, \
            "Step 1.6 should use get() with default for title"

        assert "epic.get('description'" in step16_section, \
            "Step 1.6 should use get() for description"

        assert "epic.get('acceptance_criteria'" in step16_section, \
            "Step 1.6 should use get() for acceptance_criteria"
