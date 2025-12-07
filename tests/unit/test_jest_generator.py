"""
Unit tests for Jest Configuration Generator.

Tests jest.config.js generation with test taxonomy patterns.
"""

import pytest
from pathlib import Path

from cli.config_generators.jest_generator import JestConfigGenerator
from config.test_taxonomy import get_test_levels, get_test_types, get_modifiers


@pytest.mark.unit
class TestJestConfigGenerator:
    """Test jest.config.js generation."""

    def test_init(self):
        """Test JestConfigGenerator initialization."""
        generator = JestConfigGenerator()
        assert generator is not None

    def test_generate_jest_config_default(self, tmp_path):
        """Test generating jest.config.js with default settings."""
        generator = JestConfigGenerator()
        content = generator.generate_jest_config(tmp_path)

        # Check basic structure
        assert content is not None
        assert isinstance(content, str)
        assert len(content) > 0

        # Check module.exports
        assert "module.exports" in content

        # Check test discovery settings
        assert "testMatch:" in content
        assert "**/__tests__/**/*.[jt]s?(x)" in content
        assert "**/?(*.)+(spec|test).[jt]s?(x)" in content

        # Check coverage configuration
        assert "collectCoverageFrom:" in content
        assert "coverageThreshold:" in content
        assert "branches: 80" in content
        assert "functions: 80" in content
        assert "lines: 80" in content
        assert "statements: 80" in content

        # Check environment
        assert 'testEnvironment: "node"' in content

        # Check verbose setting
        assert "verbose: true" in content

    def test_generate_jest_config_custom_test_match(self, tmp_path):
        """Test generating jest.config.js with custom testMatch."""
        generator = JestConfigGenerator()
        custom_patterns = ["**/*.test.js", "**/*.spec.ts"]
        content = generator.generate_jest_config(
            tmp_path, test_match=custom_patterns
        )

        assert "**/*.test.js" in content
        assert "**/*.spec.ts" in content

    def test_generate_jest_config_custom_coverage_threshold(self, tmp_path):
        """Test generating jest.config.js with custom coverage threshold."""
        generator = JestConfigGenerator()
        content = generator.generate_jest_config(
            tmp_path, coverage_threshold=90
        )

        assert "branches: 90" in content
        assert "functions: 90" in content
        assert "lines: 90" in content
        assert "statements: 90" in content

    def test_generate_jest_config_has_all_test_levels(self, tmp_path):
        """Test that generated jest.config.js includes all test level patterns."""
        generator = JestConfigGenerator()
        content = generator.generate_jest_config(tmp_path)

        test_levels = get_test_levels()
        for level in test_levels:
            # Check that each level appears in comments with pattern
            assert f"[{level}]" in content, f"Missing test level: {level}"

    def test_generate_jest_config_has_all_test_types(self, tmp_path):
        """Test that generated jest.config.js includes all test type patterns."""
        generator = JestConfigGenerator()
        content = generator.generate_jest_config(tmp_path)

        test_types = get_test_types()
        for test_type in test_types:
            # Check that each type appears in comments with pattern
            assert f"[{test_type}]" in content, f"Missing test type: {test_type}"

    def test_generate_jest_config_has_all_modifiers(self, tmp_path):
        """Test that generated jest.config.js includes all modifier patterns."""
        generator = JestConfigGenerator()
        content = generator.generate_jest_config(tmp_path)

        modifiers = get_modifiers()
        for modifier in modifiers:
            # Check that each modifier appears in comments with pattern
            assert f"[{modifier}]" in content, f"Missing modifier: {modifier}"

    def test_generate_jest_config_has_pattern_descriptions(self, tmp_path):
        """Test that patterns include helpful descriptions."""
        generator = JestConfigGenerator()
        content = generator.generate_jest_config(tmp_path)

        # Check for specific pattern descriptions from taxonomy
        assert "Isolated components/functions" in content
        assert "Component interactions" in content
        assert "Business logic, features, functionality" in content
        assert "Authentication, authorization, vulnerabilities" in content
        assert "Tests taking >10 seconds" in content
        assert "Tests requiring database" in content

    def test_generate_jest_config_has_comments(self, tmp_path):
        """Test that generated file includes helpful comments."""
        generator = JestConfigGenerator()
        content = generator.generate_jest_config(tmp_path)

        # Check for section comments
        assert "// Test Discovery" in content
        assert "// Test Classification Approaches" in content
        assert "// Test Levels (exactly one required):" in content
        assert "// Test Types (at least one required):" in content
        assert "// Modifiers (optional):" in content
        assert "// Coverage Configuration" in content
        assert "// Test Environment" in content
        assert "// Output Settings" in content

    def test_generate_jest_config_has_header_comment(self, tmp_path):
        """Test that generated file has header comment."""
        generator = JestConfigGenerator()
        content = generator.generate_jest_config(tmp_path)

        assert "// jest.config.js" in content
        assert "// Generated by Trustable AI framework" in content
        assert "// See: docs/architecture/decisions/ADR-004-test-marker-taxonomy.md" in content

    def test_generate_jest_config_has_classification_examples(self, tmp_path):
        """Test that generated file has classification approach examples."""
        generator = JestConfigGenerator()
        content = generator.generate_jest_config(tmp_path)

        # Check for name pattern examples
        assert "describe('[unit][functional]" in content
        assert "// @test-level: unit" in content
        assert "// @test-type: functional" in content

        # Check for usage examples
        assert "Example Test Classification:" in content

    def test_generate_jest_config_has_typescript_hints(self, tmp_path):
        """Test that generated file includes TypeScript support hints."""
        generator = JestConfigGenerator()
        content = generator.generate_jest_config(tmp_path)

        assert "TypeScript Support" in content
        assert "ts-jest" in content

    def test_generate_jest_config_has_test_filtering_examples(self, tmp_path):
        """Test that generated file includes test filtering examples."""
        generator = JestConfigGenerator()
        content = generator.generate_jest_config(tmp_path)

        assert "Running specific test types:" in content
        assert "--testNamePattern" in content

    def test_write_to_file(self, tmp_path):
        """Test writing jest.config.js to file."""
        generator = JestConfigGenerator()
        content = generator.generate_jest_config(tmp_path)

        output_path = tmp_path / "jest.config.js"
        generator.write_to_file(content, output_path)

        # Check file was created
        assert output_path.exists()

        # Check file content
        written_content = output_path.read_text(encoding="utf-8")
        assert written_content == content

    def test_write_to_file_creates_parent_dir(self, tmp_path):
        """Test that write_to_file creates parent directory if needed."""
        generator = JestConfigGenerator()
        content = generator.generate_jest_config(tmp_path)

        output_path = tmp_path / "subdir" / "jest.config.js"
        generator.write_to_file(content, output_path)

        # Check file was created
        assert output_path.exists()
        assert output_path.parent.exists()

    def test_write_to_file_empty_content_raises_error(self, tmp_path):
        """Test that writing empty content raises ValueError."""
        generator = JestConfigGenerator()
        output_path = tmp_path / "jest.config.js"

        with pytest.raises(ValueError, match="Cannot write empty jest.config.js content"):
            generator.write_to_file("", output_path)

    def test_write_to_file_whitespace_only_raises_error(self, tmp_path):
        """Test that writing whitespace-only content raises ValueError."""
        generator = JestConfigGenerator()
        output_path = tmp_path / "jest.config.js"

        with pytest.raises(ValueError, match="Cannot write empty jest.config.js content"):
            generator.write_to_file("   \n  \n  ", output_path)

    def test_validate_jest_config_valid_content(self, tmp_path):
        """Test validation of valid jest.config.js content."""
        generator = JestConfigGenerator()
        content = generator.generate_jest_config(tmp_path)

        assert generator.validate_jest_config(content) is True

    def test_validate_jest_config_missing_module_exports(self):
        """Test validation fails for missing module.exports."""
        generator = JestConfigGenerator()
        content = """
        testMatch: [
            "**/*.test.js"
        ]
        """

        assert generator.validate_jest_config(content) is False

    def test_validate_jest_config_missing_testmatch(self):
        """Test validation fails for missing testMatch."""
        generator = JestConfigGenerator()
        content = """
        module.exports = {
            verbose: true
        };
        """

        assert generator.validate_jest_config(content) is False

    def test_validate_jest_config_missing_classification_comments(self):
        """Test validation fails for missing classification comments."""
        generator = JestConfigGenerator()
        content = """
        module.exports = {
            testMatch: ["**/*.test.js"],
            coverageThreshold: {
                global: {
                    branches: 80
                }
            },
            testEnvironment: "node"
        };
        """

        assert generator.validate_jest_config(content) is False

    def test_validate_jest_config_missing_coverage(self):
        """Test validation fails for missing coverage configuration."""
        generator = JestConfigGenerator()
        content = """
        module.exports = {
            testMatch: ["**/*.test.js"],
            testEnvironment: "node"
        };
        // Test Classification
        """

        assert generator.validate_jest_config(content) is False

    def test_validate_jest_config_missing_test_environment(self):
        """Test validation fails for missing testEnvironment."""
        generator = JestConfigGenerator()
        content = """
        module.exports = {
            testMatch: ["**/*.test.js"],
            coverageThreshold: {
                global: {
                    branches: 80
                }
            }
        };
        // Test Classification
        """

        assert generator.validate_jest_config(content) is False

    def test_validate_jest_config_empty_content(self):
        """Test validation fails for empty content."""
        generator = JestConfigGenerator()

        assert generator.validate_jest_config("") is False
        assert generator.validate_jest_config("   \n  ") is False

    def test_validate_jest_config_none_content(self):
        """Test validation fails for None content."""
        generator = JestConfigGenerator()

        assert generator.validate_jest_config(None) is False

    def test_generated_content_is_valid(self, tmp_path):
        """Test that generated content passes validation."""
        generator = JestConfigGenerator()
        content = generator.generate_jest_config(tmp_path)

        assert generator.validate_jest_config(content) is True

    def test_generated_content_can_be_written_and_read(self, tmp_path):
        """Test full workflow: generate, write, read, validate."""
        generator = JestConfigGenerator()

        # Generate content
        content = generator.generate_jest_config(tmp_path)

        # Write to file
        output_path = tmp_path / "jest.config.js"
        generator.write_to_file(content, output_path)

        # Read back
        written_content = output_path.read_text(encoding="utf-8")

        # Validate
        assert generator.validate_jest_config(written_content) is True
        assert written_content == content

    def test_pattern_ordering_is_consistent(self, tmp_path):
        """Test that pattern ordering is consistent across multiple generations."""
        generator = JestConfigGenerator()

        content1 = generator.generate_jest_config(tmp_path)
        content2 = generator.generate_jest_config(tmp_path)

        # Content should be identical (deterministic)
        assert content1 == content2

    def test_taxonomy_changes_reflected_in_output(self, tmp_path):
        """Test that output reflects current taxonomy state."""
        generator = JestConfigGenerator()
        content = generator.generate_jest_config(tmp_path)

        # All current test levels should be present
        for level in get_test_levels():
            assert f"[{level}]" in content

        # All current test types should be present
        for test_type in get_test_types():
            assert f"[{test_type}]" in content

        # All current modifiers should be present
        for modifier in get_modifiers():
            assert f"[{modifier}]" in content

    def test_generated_file_is_valid_javascript(self, tmp_path):
        """Test that generated content is syntactically valid JavaScript."""
        generator = JestConfigGenerator()
        content = generator.generate_jest_config(tmp_path)

        # Basic JavaScript syntax checks
        assert content.count("{") == content.count("}")  # Balanced braces
        assert "module.exports = {" in content
        assert content.strip().endswith("};")

    def test_coverage_excludes_common_files(self, tmp_path):
        """Test that coverage configuration excludes common non-test files."""
        generator = JestConfigGenerator()
        content = generator.generate_jest_config(tmp_path)

        # Check coverage exclusions
        assert "!src/**/*.d.ts" in content
        assert "!src/**/*.stories.{js,jsx,ts,tsx}" in content
        assert "!src/**/__tests__/**" in content

    def test_generated_file_ends_with_newline(self, tmp_path):
        """Test that generated jest.config.js ends with newline."""
        generator = JestConfigGenerator()
        content = generator.generate_jest_config(tmp_path)

        assert content.endswith("\n")

    def test_all_classification_approaches_documented(self, tmp_path):
        """Test that all classification approaches are documented."""
        generator = JestConfigGenerator()
        content = generator.generate_jest_config(tmp_path)

        # Should document all three approaches
        assert "Test name patterns:" in content
        assert "Comment annotations:" in content
        assert "Test file organization:" in content

    def test_testmatch_supports_typescript(self, tmp_path):
        """Test that default testMatch patterns support TypeScript."""
        generator = JestConfigGenerator()
        content = generator.generate_jest_config(tmp_path)

        # Pattern should match .ts and .tsx files
        assert "[jt]s?(x)" in content
