"""
Integration tests for QA Tester Agent rendering.

Tests the qa-tester agent can be rendered and saved correctly.
"""
import pytest
from pathlib import Path

from agents.registry import AgentRegistry


@pytest.mark.integration
class TestQATesterAgentRendering:
    """Integration tests for QA Tester agent rendering."""

    def test_qa_tester_renders_with_project_config(self, sample_framework_config, temp_dir):
        """Test that qa-tester renders with actual project configuration."""
        registry = AgentRegistry(sample_framework_config)

        # Render agent
        rendered = registry.render_agent("qa-tester")

        # Verify rendered content is substantial
        assert len(rendered) > 5000

        # Verify key sections are present
        assert "# QA Tester Agent" in rendered
        assert "## Role" in rendered
        assert "## Blackbox Testing Principles" in rendered
        assert "## Test Plan Template" in rendered
        assert "## JSON Output Format" in rendered

    def test_qa_tester_saves_to_file(self, sample_framework_config, temp_dir):
        """Test that qa-tester can be saved to file with UTF-8 encoding."""
        registry = AgentRegistry(sample_framework_config)

        # Save agent
        output_file = registry.save_rendered_agent("qa-tester", temp_dir)

        # Verify file exists and has correct name
        assert output_file.exists()
        assert output_file.name == "qa-tester.md"

        # Verify file can be read with UTF-8 encoding
        content = output_file.read_text(encoding='utf-8')
        assert len(content) > 5000

        # Verify Unicode emojis are preserved
        assert "✅" in content or "🧪" in content or "📋" in content

    def test_qa_tester_includes_all_required_sections(self, sample_framework_config):
        """Test that all required sections are present in rendered agent."""
        registry = AgentRegistry(sample_framework_config)
        rendered = registry.render_agent("qa-tester")

        required_sections = [
            "## Role",
            "## Model Configuration",
            "## Output Formatting",
            "## Tech Stack Context",
            "## Quality Standards",
            "## Responsibilities",
            "## Blackbox Testing Principles",
            "## Test Plan Template",
            "## JSON Output Format",
            "## Test Case Writing Guidelines",
            "## Example:",
            "## Work Tracking Integration",
            "## Success Criteria",
        ]

        for section in required_sections:
            assert section in rendered, f"Missing required section: {section}"

    def test_qa_tester_json_structure_valid(self, sample_framework_config):
        """Test that JSON structure in template is well-formed."""
        registry = AgentRegistry(sample_framework_config)
        rendered = registry.render_agent("qa-tester")

        # Verify JSON structure keys are present
        json_keys = [
            '"test_plan"',
            '"epic"',
            '"features"',
            '"test_cases"',
            '"coverage_summary"',
            '"quality_gates"',
            '"risks"',
            '"test_plan_markdown"'
        ]

        for key in json_keys:
            assert key in rendered, f"Missing JSON key: {key}"

    def test_qa_tester_example_includes_test_cases(self, sample_framework_config):
        """Test that example includes complete test case structure."""
        registry = AgentRegistry(sample_framework_config)
        rendered = registry.render_agent("qa-tester")

        # Example should include test case components
        # Check case-insensitive for most, case-sensitive for test IDs
        assert "TC-001" in rendered, "Example missing TC-001"

        case_insensitive_components = [
            "test_id",
            "preconditions",
            "inputs",
            "expected_outputs",
            "pass_conditions",
            "fail_conditions"
        ]

        for component in case_insensitive_components:
            assert component in rendered.lower(), f"Example missing component: {component}"

    def test_qa_tester_with_different_platforms(self):
        """Test that agent renders correctly with different work tracking platforms."""
        from config.schema import (
            FrameworkConfig,
            ProjectConfig,
            WorkTrackingConfig,
        )

        platforms = ["azure-devops", "file-based"]

        for platform in platforms:
            config = FrameworkConfig(
                project=ProjectConfig(
                    name="Test Project",
                    type="web-application",
                    tech_stack={"languages": ["Python"]},
                ),
                work_tracking=WorkTrackingConfig(
                    platform=platform,
                    organization="https://dev.azure.com/test",
                    project="Test",
                ),
            )

            registry = AgentRegistry(config)
            rendered = registry.render_agent("qa-tester")

            assert len(rendered) > 5000
            assert "QA Tester Agent" in rendered


@pytest.mark.integration
class TestQATesterAgentContent:
    """Integration tests for QA Tester agent content quality."""

    def test_qa_tester_blackbox_principles_comprehensive(self, sample_framework_config):
        """Test that blackbox principles are comprehensively explained."""
        registry = AgentRegistry(sample_framework_config)
        rendered = registry.render_agent("qa-tester")

        # Should explain what blackbox testing is
        assert "What is Blackbox Testing?" in rendered

        # Should explain blackbox vs whitebox
        assert "Blackbox vs Whitebox" in rendered or "blackbox" in rendered.lower()

        # Should provide examples
        assert "Good Blackbox Test Case" in rendered or "Bad Blackbox Test Case" in rendered

    def test_qa_tester_test_plan_template_complete(self, sample_framework_config):
        """Test that test plan template includes all required sections."""
        registry = AgentRegistry(sample_framework_config)
        rendered = registry.render_agent("qa-tester")

        template_sections = [
            "EPIC Overview",
            "FEATURES Covered",
            "Acceptance Criteria by FEATURE",
            "Blackbox Test Cases",
            "Test Coverage Summary",
            "Quality Gates",
            "Risk Assessment",
        ]

        for section in template_sections:
            assert section in rendered, f"Template missing section: {section}"

    def test_qa_tester_workflow_description_present(self, sample_framework_config):
        """Test that workflow description is present and clear."""
        registry = AgentRegistry(sample_framework_config)
        rendered = registry.render_agent("qa-tester")

        # Workflow should describe input, process, output
        workflow_elements = ["Workflow", "Input", "Process", "Output"]

        # At least some workflow elements should be present
        found = sum(1 for elem in workflow_elements if elem in rendered)
        assert found >= 2, "Workflow description not comprehensive enough"
