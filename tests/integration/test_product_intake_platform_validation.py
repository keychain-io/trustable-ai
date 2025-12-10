"""
Integration tests for product-intake workflow platform validation.

Tests Bug #1078 fix - ensures product-intake workflow validates
platform configuration early and fails with clear error messages.
"""
import pytest
from pathlib import Path
from workflows.registry import WorkflowRegistry
from config.loader import load_config


@pytest.mark.integration
class TestProductIntakePlatformValidation:
    """Test suite for product-intake workflow platform validation."""

    @pytest.fixture
    def azure_config_yaml(self):
        """Sample configuration with Azure DevOps platform."""
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
    analyst: "claude-sonnet-4.5"
  enabled_agents:
    - business-analyst
    - senior-engineer
"""

    @pytest.fixture
    def filebased_config_yaml(self):
        """Sample configuration with file-based platform."""
        return """
project:
  name: "Test Project"
  type: "web-application"
  tech_stack:
    languages: ["Python"]

work_tracking:
  platform: "file-based"
  work_items_directory: ".claude/work-items"
  project: "TestProject"

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
    - senior-engineer
"""

    def test_product_intake_has_platform_validation(self, tmp_path, azure_config_yaml):
        """Test that product-intake workflow includes platform validation."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding="utf-8")

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("product-intake")

        # Should have try/except for adapter initialization
        assert "try:" in rendered
        assert "adapter = get_adapter()" in rendered
        assert "except ValueError as e:" in rendered

        # Should have helpful error message
        assert ":x: ERROR:" in rendered
        assert ".claude/config.yaml" in rendered

    def test_product_intake_validates_platform_match(self, tmp_path, azure_config_yaml):
        """Test that product-intake validates adapter platform matches config."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding="utf-8")

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("product-intake")

        # Should validate platform matches
        assert 'configured_platform = "' in rendered or "configured_platform =" in rendered
        assert "adapter.platform != configured_platform" in rendered
        assert ":warning: WARNING: Adapter platform mismatch!" in rendered

    def test_product_intake_exits_on_platform_error(self, tmp_path, azure_config_yaml):
        """Test that product-intake exits on platform validation failure."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding="utf-8")

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("product-intake")

        # Should exit on error
        assert "sys.exit(1)" in rendered

    def test_product_intake_renders_with_azure_devops(self, tmp_path, azure_config_yaml):
        """Test that product-intake renders correctly with Azure DevOps config."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding="utf-8")

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("product-intake")

        # Should have Azure DevOps as configured platform
        assert 'configured_platform = "azure-devops"' in rendered

        # Should use adapter pattern, not direct az boards
        assert "adapter.create_work_item(" in rendered
        assert "az boards" not in rendered

    def test_product_intake_renders_with_file_based(self, tmp_path, filebased_config_yaml):
        """Test that product-intake renders correctly with file-based config."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(filebased_config_yaml, encoding="utf-8")

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("product-intake")

        # Should have file-based as configured platform
        assert 'configured_platform = "file-based"' in rendered

        # Should use adapter pattern
        assert "adapter.create_work_item(" in rendered
        assert "az boards" not in rendered

    def test_product_intake_validation_before_workflow_logic(self, tmp_path, azure_config_yaml):
        """Test that platform validation happens BEFORE workflow logic."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding="utf-8")

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("product-intake")

        # Find position of validation and workflow logic
        validation_pos = rendered.find("try:\n    adapter = get_adapter()")
        workflow_logic_pos = rendered.find("## Phase 1: Capture Intake Item")

        # Validation should come before workflow logic
        assert validation_pos > 0
        assert workflow_logic_pos > 0
        assert validation_pos < workflow_logic_pos, \
            "Platform validation should happen before workflow logic starts"

    def test_product_intake_error_message_actionable(self, tmp_path, azure_config_yaml):
        """Test that error messages tell user exactly what to do."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding="utf-8")

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("product-intake")

        # Error message should be actionable
        assert ":arrow_right: Fix:" in rendered
        assert "work_tracking:" in rendered
        assert "platform:" in rendered
        # Should show example
        assert "Example:" in rendered or "example:" in rendered


@pytest.mark.integration
class TestProductIntakeNoSilentFallback:
    """
    Critical tests: Verify product-intake workflow NEVER silently
    falls back to file-based adapter when Azure DevOps configured.

    This is the core of Bug #1078.
    """

    @pytest.fixture
    def azure_config_yaml(self):
        """Azure DevOps configuration."""
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
    bug: "Bug"
    task: "Task"

quality_standards:
  test_coverage_min: 80

agent_config:
  models:
    analyst: "claude-sonnet-4.5"
  enabled_agents:
    - business-analyst
"""

    def test_no_file_based_fallback_logic_in_workflow(self, tmp_path, azure_config_yaml):
        """
        Critical: Verify workflow has NO fallback logic to file-based adapter.

        The bug was that workflows would silently switch to file-based
        when Azure DevOps failed. This MUST NOT happen.
        """
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding="utf-8")

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("product-intake")

        # Should NOT have conditional fallback logic like:
        # if adapter.platform != 'azure-devops': use_file_based()
        # Or: except: adapter = FileBasedAdapter()

        # Check for suspicious patterns
        assert "FileBasedAdapter" not in rendered, \
            "Workflow should not directly reference FileBasedAdapter"

        # Should not have platform-specific branching for adapter selection
        assert "if adapter.platform ==" not in rendered or \
               "configured_platform" in rendered, \
            "Platform checks should only be for validation, not fallback"

    def test_workflow_uses_single_adapter_instance(self, tmp_path, azure_config_yaml):
        """Test that workflow uses single adapter instance throughout."""
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config_yaml, encoding="utf-8")

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("product-intake")

        # Should call get_adapter() only once
        adapter_init_count = rendered.count("adapter = get_adapter()")
        assert adapter_init_count == 1, \
            f"Workflow should initialize adapter once, found {adapter_init_count} times"

        # Should not reinitialize adapter later
        assert rendered.count("adapter =") == 1, \
            "Adapter should not be reassigned after initialization"

    def test_workflow_enforces_configured_platform_only(self, tmp_path):
        """
        Test that workflow strictly uses configured platform with no alternatives.

        This verifies the single source of truth principle.
        """
        # Test with Azure DevOps config
        azure_config = """
project:
  name: "Test"
  type: "cli-tool"
  tech_stack:
    languages: ["Python"]

work_tracking:
  platform: "azure-devops"
  organization: "https://dev.azure.com/test"
  project: "Test"

quality_standards:
  test_coverage_min: 80

agent_config:
  enabled_agents: []
"""
        config_path = tmp_path / "azure" / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(azure_config, encoding="utf-8")

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        rendered = registry.render_workflow("product-intake")

        # Should reference azure-devops as the configured platform
        assert 'configured_platform = "azure-devops"' in rendered

        # Test with file-based config
        filebased_config = """
project:
  name: "Test"
  type: "cli-tool"
  tech_stack:
    languages: ["Python"]

work_tracking:
  platform: "file-based"

quality_standards:
  test_coverage_min: 80

agent_config:
  enabled_agents: []
"""
        config_path2 = tmp_path / "file" / ".claude" / "config.yaml"
        config_path2.parent.mkdir(parents=True)
        config_path2.write_text(filebased_config, encoding="utf-8")

        config2 = load_config(config_path2)
        registry2 = WorkflowRegistry(config2)

        rendered2 = registry2.render_workflow("product-intake")

        # Should reference file-based as the configured platform
        assert 'configured_platform = "file-based"' in rendered2

        # The two renderings should differ in configured_platform only
        # Both should use the same adapter pattern code
        assert "adapter.create_work_item(" in rendered
        assert "adapter.create_work_item(" in rendered2
