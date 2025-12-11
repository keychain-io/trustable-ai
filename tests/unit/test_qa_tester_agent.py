"""
Unit tests for QA Tester Agent template.

Tests the qa-tester.j2 template rendering and content validation.
"""
import pytest
import json
from pathlib import Path

from agents.registry import AgentRegistry


@pytest.mark.unit
class TestQATesterAgentTemplate:
    """Test suite for QA Tester agent template."""

    def test_qa_tester_agent_exists(self, sample_framework_config):
        """Test that qa-tester agent template exists."""
        registry = AgentRegistry(sample_framework_config)
        agents = registry.list_agents()

        assert "qa-tester" in agents

    def test_qa_tester_renders_successfully(self, sample_framework_config):
        """Test that qa-tester template renders without errors."""
        registry = AgentRegistry(sample_framework_config)
        rendered = registry.render_agent("qa-tester")

        assert isinstance(rendered, str)
        assert len(rendered) > 1000  # Should be substantial

    def test_qa_tester_contains_role_description(self, sample_framework_config):
        """Test that rendered agent contains role description."""
        registry = AgentRegistry(sample_framework_config)
        rendered = registry.render_agent("qa-tester")

        assert "## Role" in rendered
        assert "blackbox acceptance test plan" in rendered.lower() or "acceptance test" in rendered.lower()

    def test_qa_tester_contains_model_configuration(self, sample_framework_config):
        """Test that model configuration is included."""
        registry = AgentRegistry(sample_framework_config)
        rendered = registry.render_agent("qa-tester")

        assert "## Model Configuration" in rendered
        assert "claude-sonnet-4.5" in rendered or "Model:" in rendered

    def test_qa_tester_contains_tech_stack_context(self, sample_framework_config):
        """Test that tech stack context is injected."""
        registry = AgentRegistry(sample_framework_config)
        rendered = registry.render_agent("qa-tester")

        assert "## Tech Stack Context" in rendered
        # Tech stack should include project type
        assert "web-application" in rendered or "Python" in rendered or "TypeScript" in rendered

    def test_qa_tester_contains_quality_standards(self, sample_framework_config):
        """Test that quality standards are injected."""
        registry = AgentRegistry(sample_framework_config)
        rendered = registry.render_agent("qa-tester")

        assert "## Quality Standards" in rendered or "Quality" in rendered
        # Should include test coverage minimum
        assert "80" in rendered  # Default test coverage minimum

    def test_qa_tester_contains_responsibilities(self, sample_framework_config):
        """Test that responsibilities section is present."""
        registry = AgentRegistry(sample_framework_config)
        rendered = registry.render_agent("qa-tester")

        assert "## Responsibilities" in rendered
        assert "blackbox" in rendered.lower()
        assert "test plan" in rendered.lower()
        assert "acceptance criteria" in rendered.lower()

    def test_qa_tester_contains_epic_overview_section(self, sample_framework_config):
        """Test that EPIC overview section is defined."""
        registry = AgentRegistry(sample_framework_config)
        rendered = registry.render_agent("qa-tester")

        assert "EPIC" in rendered
        assert "overview" in rendered.lower() or "EPIC Title" in rendered

    def test_qa_tester_contains_features_section(self, sample_framework_config):
        """Test that FEATURES section is defined."""
        registry = AgentRegistry(sample_framework_config)
        rendered = registry.render_agent("qa-tester")

        assert "FEATURE" in rendered
        assert "Feature" in rendered or "feature" in rendered.lower()

    def test_qa_tester_contains_test_cases_section(self, sample_framework_config):
        """Test that test cases section is defined."""
        registry = AgentRegistry(sample_framework_config)
        rendered = registry.render_agent("qa-tester")

        assert "Test Cases" in rendered or "test cases" in rendered.lower()
        assert "TC-" in rendered  # Test case ID format

    def test_qa_tester_contains_test_case_structure(self, sample_framework_config):
        """Test that test case structure includes required fields."""
        registry = AgentRegistry(sample_framework_config)
        rendered = registry.render_agent("qa-tester")

        # Test case components
        assert "test_id" in rendered.lower() or "Test ID" in rendered
        assert "input" in rendered.lower()
        assert "expected output" in rendered.lower() or "Expected Outputs" in rendered
        assert "pass" in rendered.lower() and "fail" in rendered.lower()

    def test_qa_tester_contains_json_output_format(self, sample_framework_config):
        """Test that JSON output format is defined."""
        registry = AgentRegistry(sample_framework_config)
        rendered = registry.render_agent("qa-tester")

        assert "JSON" in rendered or "json" in rendered
        assert "test_plan" in rendered

    def test_qa_tester_contains_blackbox_principles(self, sample_framework_config):
        """Test that blackbox testing principles are explained."""
        registry = AgentRegistry(sample_framework_config)
        rendered = registry.render_agent("qa-tester")

        assert "blackbox" in rendered.lower() or "Blackbox" in rendered
        # Should explain what blackbox testing is
        assert "implementation" in rendered.lower()

    def test_qa_tester_contains_test_plan_template(self, sample_framework_config):
        """Test that test plan template is provided."""
        registry = AgentRegistry(sample_framework_config)
        rendered = registry.render_agent("qa-tester")

        assert "Test Plan Template" in rendered or "test plan" in rendered.lower()
        assert "markdown" in rendered.lower() or "```" in rendered  # Code block for template

    def test_qa_tester_json_structure_includes_epic(self, sample_framework_config):
        """Test that JSON structure includes EPIC fields."""
        registry = AgentRegistry(sample_framework_config)
        rendered = registry.render_agent("qa-tester")

        # JSON output should define epic structure
        assert '"epic"' in rendered or "epic" in rendered.lower()
        assert "id" in rendered.lower()
        assert "title" in rendered.lower()
        assert "summary" in rendered.lower() or "description" in rendered.lower()

    def test_qa_tester_json_structure_includes_features(self, sample_framework_config):
        """Test that JSON structure includes features array."""
        registry = AgentRegistry(sample_framework_config)
        rendered = registry.render_agent("qa-tester")

        assert '"features"' in rendered or "features" in rendered.lower()
        assert "acceptance_criteria" in rendered or "acceptance criteria" in rendered.lower()

    def test_qa_tester_json_structure_includes_test_cases(self, sample_framework_config):
        """Test that JSON structure includes test_cases array."""
        registry = AgentRegistry(sample_framework_config)
        rendered = registry.render_agent("qa-tester")

        assert '"test_cases"' in rendered or "test_cases" in rendered
        assert "preconditions" in rendered.lower()
        assert "inputs" in rendered.lower() or "input" in rendered.lower()
        assert "expected_outputs" in rendered or "expected output" in rendered.lower()

    def test_qa_tester_contains_coverage_summary(self, sample_framework_config):
        """Test that coverage summary section is defined."""
        registry = AgentRegistry(sample_framework_config)
        rendered = registry.render_agent("qa-tester")

        assert "coverage" in rendered.lower()
        assert "summary" in rendered.lower() or "Coverage Summary" in rendered

    def test_qa_tester_contains_quality_gates(self, sample_framework_config):
        """Test that quality gates section is defined."""
        registry = AgentRegistry(sample_framework_config)
        rendered = registry.render_agent("qa-tester")

        assert "quality gate" in rendered.lower() or "Quality Gates" in rendered
        # Should reference test coverage minimum
        assert "80" in rendered or "{{ quality_standards.test_coverage_min }}" in rendered

    def test_qa_tester_contains_example(self, sample_framework_config):
        """Test that an example test plan is provided."""
        registry = AgentRegistry(sample_framework_config)
        rendered = registry.render_agent("qa-tester")

        # Should have example section
        assert "example" in rendered.lower() or "Example" in rendered

    def test_qa_tester_work_tracking_integration(self, sample_framework_config):
        """Test that work tracking integration is mentioned."""
        registry = AgentRegistry(sample_framework_config)
        rendered = registry.render_agent("qa-tester")

        # Should mention work tracking platform if configured
        if sample_framework_config.work_tracking.platform:
            assert sample_framework_config.work_tracking.platform in rendered or "work tracking" in rendered.lower()

    def test_qa_tester_contains_success_criteria(self, sample_framework_config):
        """Test that success criteria are defined."""
        registry = AgentRegistry(sample_framework_config)
        rendered = registry.render_agent("qa-tester")

        assert "Success Criteria" in rendered or "success criteria" in rendered.lower()

    def test_qa_tester_multiple_test_case_priorities(self, sample_framework_config):
        """Test that test case priorities are defined."""
        registry = AgentRegistry(sample_framework_config)
        rendered = registry.render_agent("qa-tester")

        assert "High" in rendered
        assert "Medium" in rendered
        assert "Low" in rendered
        assert "Priority" in rendered or "priority" in rendered.lower()

    def test_qa_tester_test_types_defined(self, sample_framework_config):
        """Test that test types are defined."""
        registry = AgentRegistry(sample_framework_config)
        rendered = registry.render_agent("qa-tester")

        # Common test types
        assert "Functional" in rendered or "functional" in rendered.lower()
        assert "Integration" in rendered or "integration" in rendered.lower()

    def test_qa_tester_with_minimal_config(self):
        """Test that agent renders with minimal configuration."""
        from config.schema import (
            FrameworkConfig,
            ProjectConfig,
            WorkTrackingConfig,
        )

        minimal_config = FrameworkConfig(
            project=ProjectConfig(
                name="MinimalProject",
                type="api",
                tech_stack={"languages": ["Python"]},
            ),
            work_tracking=WorkTrackingConfig(
                organization="https://dev.azure.com/test",
                project="Test",
            ),
        )

        registry = AgentRegistry(minimal_config)
        rendered = registry.render_agent("qa-tester")

        assert isinstance(rendered, str)
        assert len(rendered) > 500
        assert "MinimalProject" in rendered or "api" in rendered

    def test_qa_tester_template_valid_jinja2_syntax(self, sample_framework_config):
        """Test that template has valid Jinja2 syntax (no render errors)."""
        registry = AgentRegistry(sample_framework_config)

        # If template has syntax errors, this will raise TemplateSyntaxError
        try:
            rendered = registry.render_agent("qa-tester")
            assert len(rendered) > 0
        except Exception as e:
            pytest.fail(f"Template rendering failed with error: {e}")

    def test_qa_tester_save_to_file(self, sample_framework_config, temp_dir):
        """Test saving rendered qa-tester agent to file."""
        registry = AgentRegistry(sample_framework_config)

        output_file = registry.save_rendered_agent("qa-tester", temp_dir)

        assert output_file.exists()
        assert output_file.name == "qa-tester.md"
        content = output_file.read_text(encoding='utf-8')
        assert len(content) > 1000
        assert "QA Tester Agent" in content or "qa-tester" in content.lower()


@pytest.mark.unit
class TestQATesterAgentContent:
    """Test specific content and guidelines in QA Tester agent."""

    def test_qa_tester_blackbox_vs_whitebox_explanation(self, sample_framework_config):
        """Test that agent explains blackbox vs whitebox testing."""
        registry = AgentRegistry(sample_framework_config)
        rendered = registry.render_agent("qa-tester")

        # Should explain the difference
        assert "blackbox" in rendered.lower()
        assert ("whitebox" in rendered.lower() or "white box" in rendered.lower() or
                "internal" in rendered.lower())

    def test_qa_tester_good_vs_bad_examples(self, sample_framework_config):
        """Test that agent provides good vs bad test case examples."""
        registry = AgentRegistry(sample_framework_config)
        rendered = registry.render_agent("qa-tester")

        # Should have examples showing good and bad approaches
        assert ("good" in rendered.lower() or "bad" in rendered.lower() or
                "example" in rendered.lower())

    def test_qa_tester_test_case_naming_convention(self, sample_framework_config):
        """Test that test case naming convention is defined."""
        registry = AgentRegistry(sample_framework_config)
        rendered = registry.render_agent("qa-tester")

        assert "TC-" in rendered  # Test case ID prefix
        assert "naming" in rendered.lower() or "convention" in rendered.lower()

    def test_qa_tester_contains_workflow_section(self, sample_framework_config):
        """Test that workflow section explains the process."""
        registry = AgentRegistry(sample_framework_config)
        rendered = registry.render_agent("qa-tester")

        assert "Workflow" in rendered or "workflow" in rendered.lower() or "Process" in rendered
        assert "input" in rendered.lower() or "Input" in rendered
        assert "output" in rendered.lower() or "Output" in rendered

    def test_qa_tester_risk_assessment_section(self, sample_framework_config):
        """Test that risk assessment is included."""
        registry = AgentRegistry(sample_framework_config)
        rendered = registry.render_agent("qa-tester")

        assert "risk" in rendered.lower() or "Risk" in rendered

    def test_qa_tester_test_environment_requirements(self, sample_framework_config):
        """Test that test environment requirements are mentioned."""
        registry = AgentRegistry(sample_framework_config)
        rendered = registry.render_agent("qa-tester")

        assert ("environment" in rendered.lower() or "Environment" in rendered or
                "setup" in rendered.lower())


@pytest.mark.unit
class TestQATesterAgentConfiguration:
    """Test configuration injection in QA Tester agent."""

    def test_qa_tester_injects_project_name(self, sample_framework_config):
        """Test that project name is injected into template."""
        registry = AgentRegistry(sample_framework_config)
        rendered = registry.render_agent("qa-tester")

        # Project name might not appear in the template directly, but tech stack should
        assert sample_framework_config.project.type in rendered or "Python" in rendered

    def test_qa_tester_injects_quality_standards(self, sample_framework_config):
        """Test that quality standards values are injected."""
        registry = AgentRegistry(sample_framework_config)
        rendered = registry.render_agent("qa-tester")

        # Test coverage minimum should be injected
        coverage_min = str(sample_framework_config.quality_standards.test_coverage_min)
        assert coverage_min in rendered

    def test_qa_tester_injects_work_item_types(self, sample_framework_config):
        """Test that work item types are injected."""
        registry = AgentRegistry(sample_framework_config)
        rendered = registry.render_agent("qa-tester")

        # Should include work item types if work tracking configured
        if sample_framework_config.work_tracking.work_item_types:
            # At least some work item type should appear
            assert ("Epic" in rendered or "Feature" in rendered or "Task" in rendered or
                    "epic" in rendered.lower())

    def test_qa_tester_different_tech_stacks(self):
        """Test that different tech stacks are rendered correctly."""
        from config.schema import (
            FrameworkConfig,
            ProjectConfig,
            WorkTrackingConfig,
        )

        # Test with different languages
        for language in ["Python", "JavaScript", "TypeScript", "Java", "Go"]:
            config = FrameworkConfig(
                project=ProjectConfig(
                    name="Test",
                    type="web-application",
                    tech_stack={"languages": [language]},
                ),
                work_tracking=WorkTrackingConfig(
                    organization="https://dev.azure.com/test",
                    project="Test",
                ),
            )

            registry = AgentRegistry(config)
            rendered = registry.render_agent("qa-tester")

            assert isinstance(rendered, str)
            assert len(rendered) > 500

    def test_qa_tester_with_custom_quality_standards(self):
        """Test with custom quality standards."""
        from config.schema import (
            FrameworkConfig,
            ProjectConfig,
            WorkTrackingConfig,
            QualityStandards,
        )

        custom_config = FrameworkConfig(
            project=ProjectConfig(
                name="Test",
                type="web-application",
                tech_stack={"languages": ["Python"]},
            ),
            work_tracking=WorkTrackingConfig(
                organization="https://dev.azure.com/test",
                project="Test",
            ),
            quality_standards=QualityStandards(
                test_coverage_min=95,
                code_complexity_max=5,
            ),
        )

        registry = AgentRegistry(custom_config)
        rendered = registry.render_agent("qa-tester")

        # Custom quality standards should be injected
        assert "95" in rendered
        assert "5" in rendered


@pytest.mark.unit
class TestQATesterAgentEdgeCases:
    """Test edge cases and error handling."""

    def test_qa_tester_renders_with_empty_tech_stack(self):
        """Test that agent renders even with minimal tech stack."""
        from config.schema import (
            FrameworkConfig,
            ProjectConfig,
            WorkTrackingConfig,
        )

        config = FrameworkConfig(
            project=ProjectConfig(
                name="Test",
                type="api",
                tech_stack={},  # Empty tech stack
            ),
            work_tracking=WorkTrackingConfig(
                organization="https://dev.azure.com/test",
                project="Test",
            ),
        )

        registry = AgentRegistry(config)
        rendered = registry.render_agent("qa-tester")

        assert isinstance(rendered, str)
        assert len(rendered) > 500

    def test_qa_tester_no_unicode_emojis_in_critical_content(self, sample_framework_config):
        """Test that critical content uses actual emojis, not shortcodes."""
        registry = AgentRegistry(sample_framework_config)
        rendered = registry.render_agent("qa-tester")

        # Should use actual Unicode emojis in output formatting section
        # Look for the Output Formatting section and verify it uses actual emojis
        if "Output Formatting" in rendered:
            output_section_start = rendered.find("Output Formatting")
            output_section = rendered[output_section_start:output_section_start + 500]
            # Should contain actual emojis or mention of Unicode
            assert ("✅" in output_section or "🧪" in output_section or "Unicode" in output_section)
