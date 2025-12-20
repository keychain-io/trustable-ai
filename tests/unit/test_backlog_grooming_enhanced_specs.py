"""
Unit tests for Task #1117: Enhanced backlog-grooming task specifications.

Tests verify that the backlog-grooming workflow template includes comprehensive
test requirements for Implementation and Testing tasks as specified in #1117.

This validates that task specifications explicitly list:
- Implementation Task: unit tests, integration tests, edge-case whitebox testing, acceptance tests
- Testing Task: validation of presence, completeness, and falsifiability
"""
import pytest
from pathlib import Path
from workflows.registry import WorkflowRegistry
from config.loader import load_config


@pytest.mark.unit
class TestBacklogGroomingEnhancedImplementationSpec:
    """Test suite for enhanced Implementation Task specification."""

    @pytest.fixture
    def config_yaml(self):
        """Sample configuration for testing."""
        return """
project:
  name: "Test Project"
  type: "web-application"
  tech_stack:
    languages: ["Python"]
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
    task: "Task"

quality_standards:
  test_coverage_min: 80
  critical_vulnerabilities_max: 0
  code_complexity_max: 10

agent_config:
  models:
    senior-engineer: "claude-sonnet-4.5"
  enabled_agents:
    - senior-engineer
"""

    def test_implementation_task_spec_includes_unit_tests(self, tmp_path, config_yaml):
        """Test that Implementation Task specification explicitly mentions unit tests."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)
        rendered = registry.render_workflow("backlog-grooming")

        # Find Implementation Task specification section
        assert "Exactly one task should request the complete implementation" in rendered, \
            "Implementation Task specification missing"

        # Verify unit tests mentioned
        assert "Unit tests" in rendered, \
            "Implementation Task should mention unit tests"
        assert "individual functions/methods in isolation" in rendered, \
            "Unit tests should be described as testing individual functions/methods"

    def test_implementation_task_spec_includes_integration_tests(self, tmp_path, config_yaml):
        """Test that Implementation Task specification explicitly mentions integration tests."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)
        rendered = registry.render_workflow("backlog-grooming")

        # Verify integration tests mentioned
        assert "Integration tests" in rendered, \
            "Implementation Task should mention integration tests"
        assert "component interactions" in rendered, \
            "Integration tests should mention component interactions"

    def test_implementation_task_spec_includes_edge_case_whitebox_testing(self, tmp_path, config_yaml):
        """Test that Implementation Task specification explicitly mentions edge-case whitebox testing."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)
        rendered = registry.render_workflow("backlog-grooming")

        # Verify edge-case whitebox testing mentioned
        assert "Edge-case whitebox testing" in rendered, \
            "Implementation Task should mention edge-case whitebox testing"
        assert "boundary conditions" in rendered, \
            "Edge-case testing should mention boundary conditions"
        assert "error handling" in rendered, \
            "Edge-case testing should mention error handling"

    def test_implementation_task_spec_includes_acceptance_tests(self, tmp_path, config_yaml):
        """Test that Implementation Task specification explicitly mentions acceptance tests."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)
        rendered = registry.render_workflow("backlog-grooming")

        # Verify acceptance tests mentioned
        assert "Acceptance tests" in rendered, \
            "Implementation Task should mention acceptance tests"
        assert "acceptance criteria listed in the Feature" in rendered, \
            "Acceptance tests should reference Feature acceptance criteria"

    def test_implementation_task_spec_includes_coverage_targets(self, tmp_path, config_yaml):
        """Test that Implementation Task specification includes code coverage targets."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)
        rendered = registry.render_workflow("backlog-grooming")

        # Verify coverage targets mentioned
        assert "code coverage targets" in rendered, \
            "Implementation Task should mention code coverage targets"
        # Verify quality standard is referenced (80% from config)
        assert "80% minimum" in rendered or "{{ quality_standards.test_coverage_min }}% minimum" in rendered, \
            "Implementation Task should reference quality standards coverage minimum"

    def test_implementation_task_spec_requires_falsifiable_tests(self, tmp_path, config_yaml):
        """Test that Implementation Task specification requires falsifiable tests."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)
        rendered = registry.render_workflow("backlog-grooming")

        # Verify falsifiability requirement
        assert "falsifiable" in rendered, \
            "Implementation Task should require falsifiable tests"
        assert "detect actual failures" in rendered or "able to detect" in rendered, \
            "Falsifiability should be explained"

    def test_implementation_task_spec_requires_comprehensive_tests(self, tmp_path, config_yaml):
        """Test that Implementation Task specification requires comprehensive tests."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)
        rendered = registry.render_workflow("backlog-grooming")

        # Verify comprehensive requirement
        assert "comprehensive" in rendered, \
            "Implementation Task should require comprehensive tests"


@pytest.mark.unit
class TestBacklogGroomingEnhancedTestingSpec:
    """Test suite for enhanced Testing Task specification."""

    @pytest.fixture
    def config_yaml(self):
        """Sample configuration for testing."""
        return """
project:
  name: "Test Project"
  type: "web-application"
  tech_stack:
    languages: ["Python"]
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
    task: "Task"

quality_standards:
  test_coverage_min: 80
  critical_vulnerabilities_max: 0
  code_complexity_max: 10

agent_config:
  models:
    senior-engineer: "claude-sonnet-4.5"
  enabled_agents:
    - senior-engineer
"""

    def test_testing_task_spec_validates_presence(self, tmp_path, config_yaml):
        """Test that Testing Task specification includes validation of test presence."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)
        rendered = registry.render_workflow("backlog-grooming")

        # Find Testing Task specification section
        assert "Exactly one task should request validation of test quality" in rendered, \
            "Testing Task specification missing"

        # Verify presence validation mentioned
        assert "Validate presence" in rendered, \
            "Testing Task should validate presence of all test types"
        assert "unit, integration, edge-case, acceptance" in rendered, \
            "Testing Task should list all required test types"

    def test_testing_task_spec_validates_completeness(self, tmp_path, config_yaml):
        """Test that Testing Task specification includes validation of test completeness."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)
        rendered = registry.render_workflow("backlog-grooming")

        # Verify completeness validation mentioned
        assert "Validate completeness" in rendered, \
            "Testing Task should validate completeness of test coverage"
        assert "all acceptance criteria" in rendered, \
            "Completeness validation should reference all acceptance criteria"

    def test_testing_task_spec_validates_falsifiability(self, tmp_path, config_yaml):
        """Test that Testing Task specification includes validation of test falsifiability."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)
        rendered = registry.render_workflow("backlog-grooming")

        # Verify falsifiability validation mentioned
        assert "Validate falsifiability" in rendered, \
            "Testing Task should validate falsifiability of tests"
        assert "Introducing intentional bugs" in rendered or "intentional bugs/failures" in rendered, \
            "Falsifiability validation should mention introducing intentional bugs"
        assert "Confirming tests detect these failures" in rendered or "confirm tests detect" in rendered, \
            "Falsifiability validation should confirm tests detect failures"
        assert "Removing the intentional bugs" in rendered or "remove" in rendered.lower(), \
            "Falsifiability validation should mention removing bugs"

    def test_testing_task_spec_confirms_code_coverage(self, tmp_path, config_yaml):
        """Test that Testing Task specification includes code coverage confirmation."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)
        rendered = registry.render_workflow("backlog-grooming")

        # Verify code coverage confirmation
        assert "Confirm code coverage" in rendered, \
            "Testing Task should confirm code coverage"
        assert "meets or exceeds" in rendered or "minimum" in rendered, \
            "Code coverage should reference minimum threshold"

    def test_testing_task_spec_confirms_feature_coverage(self, tmp_path, config_yaml):
        """Test that Testing Task specification includes feature coverage confirmation."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)
        rendered = registry.render_workflow("backlog-grooming")

        # Verify feature coverage confirmation
        assert "Confirm feature coverage" in rendered or "feature coverage" in rendered, \
            "Testing Task should confirm feature coverage"
        assert "all acceptance criteria have corresponding" in rendered, \
            "Feature coverage should reference acceptance criteria"


@pytest.mark.unit
class TestBacklogGroomingExampleTasksUpdated:
    """Test suite to verify example tasks reflect enhanced specifications."""

    @pytest.fixture
    def config_yaml(self):
        """Sample configuration for testing."""
        return """
project:
  name: "Test Project"
  type: "web-application"
  tech_stack:
    languages: ["Python"]
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
    task: "Task"

quality_standards:
  test_coverage_min: 80
  critical_vulnerabilities_max: 0
  code_complexity_max: 10

agent_config:
  models:
    senior-engineer: "claude-sonnet-4.5"
  enabled_agents:
    - senior-engineer
"""

    def test_example_implementation_task_includes_test_types(self, tmp_path, config_yaml):
        """Test that example Implementation Task lists all test types."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)
        rendered = registry.render_workflow("backlog-grooming")

        # Find example Implementation Task
        impl_task_start = rendered.find('"title": "Implement OAuth2 integration')
        assert impl_task_start != -1, "Example Implementation Task not found"

        impl_task_section = rendered[impl_task_start:impl_task_start + 2000]

        # Verify test types in example
        assert "**Unit tests**" in impl_task_section, \
            "Example should include unit tests"
        assert "**Integration tests**" in impl_task_section, \
            "Example should include integration tests"
        assert "**Edge-case whitebox testing**" in impl_task_section, \
            "Example should include edge-case whitebox testing"
        assert "**Acceptance tests**" in impl_task_section, \
            "Example should include acceptance tests"

    def test_example_testing_task_includes_validation_types(self, tmp_path, config_yaml):
        """Test that example Testing Task lists all validation types."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)
        rendered = registry.render_workflow("backlog-grooming")

        # Find example Testing Task
        test_task_start = rendered.find('"title": "Validate authentication test quality')
        assert test_task_start != -1, "Example Testing Task not found"

        test_task_section = rendered[test_task_start:test_task_start + 2000]

        # Verify validation types in example
        assert "**Validate presence**" in test_task_section, \
            "Example should include presence validation"
        assert "**Validate completeness**" in test_task_section, \
            "Example should include completeness validation"
        assert "**Validate falsifiability**" in test_task_section, \
            "Example should include falsifiability validation"
        assert "**Confirm code coverage**" in test_task_section, \
            "Example should include code coverage confirmation"
        assert "**Confirm feature coverage**" in test_task_section, \
            "Example should include feature coverage confirmation"

    def test_example_implementation_task_acceptance_criteria_updated(self, tmp_path, config_yaml):
        """Test that example Implementation Task acceptance criteria include test types."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)
        rendered = registry.render_workflow("backlog-grooming")

        # Find example Implementation Task acceptance criteria
        impl_task_start = rendered.find('"title": "Implement OAuth2 integration')
        impl_task_section = rendered[impl_task_start:impl_task_start + 2000]

        # Verify acceptance criteria updated
        assert "Unit tests achieve" in impl_task_section, \
            "Implementation Task acceptance criteria should include unit tests"
        assert "Integration tests verify" in impl_task_section, \
            "Implementation Task acceptance criteria should include integration tests"
        assert "Edge-case tests" in impl_task_section, \
            "Implementation Task acceptance criteria should include edge-case tests"
        assert "Acceptance tests verify" in impl_task_section, \
            "Implementation Task acceptance criteria should include acceptance tests"

    def test_example_testing_task_acceptance_criteria_updated(self, tmp_path, config_yaml):
        """Test that example Testing Task acceptance criteria include validation steps."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)
        rendered = registry.render_workflow("backlog-grooming")

        # Find example Testing Task acceptance criteria
        test_task_start = rendered.find('"title": "Validate authentication test quality')
        test_task_section = rendered[test_task_start:test_task_start + 2000]

        # Verify acceptance criteria updated
        assert "All required test types present" in test_task_section, \
            "Testing Task acceptance criteria should verify presence"
        assert "All Feature acceptance criteria have corresponding tests" in test_task_section, \
            "Testing Task acceptance criteria should verify completeness"
        assert "Falsifiability verified" in test_task_section, \
            "Testing Task acceptance criteria should verify falsifiability"
        assert "Code coverage meets" in test_task_section, \
            "Testing Task acceptance criteria should verify code coverage"
        assert "Feature coverage" in test_task_section, \
            "Testing Task acceptance criteria should verify feature coverage"


@pytest.mark.unit
class TestBacklogGroomingTemplateRendersSuccessfully:
    """Test suite to verify template renders without errors after enhancements."""

    @pytest.fixture
    def config_yaml(self):
        """Sample configuration for testing."""
        return """
project:
  name: "Test Project"
  type: "web-application"
  tech_stack:
    languages: ["Python"]
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
    task: "Task"

quality_standards:
  test_coverage_min: 80
  critical_vulnerabilities_max: 0
  code_complexity_max: 10

agent_config:
  models:
    senior-engineer: "claude-sonnet-4.5"
  enabled_agents:
    - senior-engineer
"""

    def test_template_renders_without_errors(self, tmp_path, config_yaml):
        """Test that enhanced template renders without Jinja2 errors."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        # This should not raise any exceptions
        rendered = registry.render_workflow("backlog-grooming")

        # Verify template rendered successfully
        assert len(rendered) > 1000, \
            "Rendered workflow should be substantial (>1000 chars)"
        assert "Backlog Grooming" in rendered, \
            "Rendered workflow should contain workflow title"

    def test_template_quality_standards_interpolated(self, tmp_path, config_yaml):
        """Test that quality_standards.test_coverage_min is properly interpolated."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)
        rendered = registry.render_workflow("backlog-grooming")

        # Verify quality standard is interpolated (not left as Jinja variable)
        assert "80% minimum" in rendered, \
            "quality_standards.test_coverage_min should be interpolated to 80%"
        assert "{{ quality_standards.test_coverage_min }}" not in rendered, \
            "Jinja variables should be interpolated, not left as-is"

    def test_template_preserves_existing_functionality(self, tmp_path, config_yaml):
        """Test that enhanced template preserves existing Epic decomposition functionality."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(config_yaml, encoding='utf-8')

        config = load_config(config_path)
        registry = WorkflowRegistry(config)
        rendered = registry.render_workflow("backlog-grooming")

        # Verify existing sections still present
        assert "Epic Detection and Decomposition" in rendered, \
            "Epic decomposition section should be preserved"
        assert "Feature Extraction" in rendered, \
            "Feature extraction section should be preserved"
        assert "Verification" in rendered, \
            "Verification section should be preserved"
        assert "Verifying Epic Decomposition Hierarchy" in rendered, \
            "Verification gates should be preserved"
