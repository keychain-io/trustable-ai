"""
Unit tests for Pytest Configuration Generator.

Tests pytest.ini generation with test taxonomy markers.
"""

import pytest
from pathlib import Path

from cli.config_generators.pytest_generator import PytestConfigGenerator
from config.test_taxonomy import get_test_levels, get_test_types, get_modifiers


@pytest.mark.unit
class TestPytestConfigGenerator:
    """Test pytest.ini generation."""

    def test_init(self):
        """Test PytestConfigGenerator initialization."""
        generator = PytestConfigGenerator()
        assert generator is not None

    def test_generate_pytest_ini_default(self, tmp_path):
        """Test generating pytest.ini with default settings."""
        generator = PytestConfigGenerator()
        content = generator.generate_pytest_ini(tmp_path)

        # Check basic structure
        assert content is not None
        assert isinstance(content, str)
        assert len(content) > 0

        # Check pytest section
        assert "[pytest]" in content

        # Check test discovery settings
        assert "testpaths = tests" in content
        assert "python_files = test_*.py" in content
        assert "python_classes = Test*" in content
        assert "python_functions = test_*" in content

        # Check markers section
        assert "markers =" in content

        # Check output settings
        assert "console_output_style = progress" in content
        assert "addopts = -v --strict-markers" in content

    def test_generate_pytest_ini_custom_testpaths(self, tmp_path):
        """Test generating pytest.ini with custom testpaths."""
        generator = PytestConfigGenerator()
        content = generator.generate_pytest_ini(
            tmp_path, testpaths="custom_tests"
        )

        assert "testpaths = custom_tests" in content

    def test_generate_pytest_ini_custom_addopts(self, tmp_path):
        """Test generating pytest.ini with custom addopts."""
        generator = PytestConfigGenerator()
        content = generator.generate_pytest_ini(
            tmp_path, addopts="-v -s --strict-markers --cov"
        )

        assert "addopts = -v -s --strict-markers --cov" in content

    def test_generate_pytest_ini_has_all_test_levels(self, tmp_path):
        """Test that generated pytest.ini includes all test level markers."""
        generator = PytestConfigGenerator()
        content = generator.generate_pytest_ini(tmp_path)

        test_levels = get_test_levels()
        for level in test_levels:
            # Check that each level appears as a marker
            assert f"{level}:" in content, f"Missing test level: {level}"

    def test_generate_pytest_ini_has_all_test_types(self, tmp_path):
        """Test that generated pytest.ini includes all test type markers."""
        generator = PytestConfigGenerator()
        content = generator.generate_pytest_ini(tmp_path)

        test_types = get_test_types()
        for test_type in test_types:
            # Check that each type appears as a marker
            assert f"{test_type}:" in content, f"Missing test type: {test_type}"

    def test_generate_pytest_ini_has_all_modifiers(self, tmp_path):
        """Test that generated pytest.ini includes all modifier markers."""
        generator = PytestConfigGenerator()
        content = generator.generate_pytest_ini(tmp_path)

        modifiers = get_modifiers()
        for modifier in modifiers:
            # Check that each modifier appears as a marker
            assert f"{modifier}:" in content, f"Missing modifier: {modifier}"

    def test_generate_pytest_ini_has_marker_descriptions(self, tmp_path):
        """Test that markers include helpful descriptions."""
        generator = PytestConfigGenerator()
        content = generator.generate_pytest_ini(tmp_path)

        # Check for specific marker descriptions
        assert "unit: Isolated components/functions" in content
        assert "integration: Component interactions" in content
        assert "functional: Business logic, features, functionality" in content
        assert "security: Authentication, authorization, vulnerabilities" in content
        assert "slow: Tests taking >10 seconds" in content
        assert "requires-db: Tests requiring database" in content

    def test_generate_pytest_ini_has_comments(self, tmp_path):
        """Test that generated file includes helpful comments."""
        generator = PytestConfigGenerator()
        content = generator.generate_pytest_ini(tmp_path)

        # Check for section comments
        assert "# Test Discovery" in content
        assert "# Test Classification Markers" in content
        assert "# Output Settings" in content
        assert "# Test Levels (exactly one required)" in content
        assert "# Test Types (at least one required)" in content
        assert "# Modifiers (optional)" in content

    def test_generate_pytest_ini_has_header_comment(self, tmp_path):
        """Test that generated file has header comment."""
        generator = PytestConfigGenerator()
        content = generator.generate_pytest_ini(tmp_path)

        assert "# pytest.ini" in content
        assert "# Generated by Trustable AI framework" in content
        assert "# See: docs/architecture/decisions/ADR-004-test-marker-taxonomy.md" in content

    def test_write_to_file(self, tmp_path):
        """Test writing pytest.ini to file."""
        generator = PytestConfigGenerator()
        content = generator.generate_pytest_ini(tmp_path)

        output_path = tmp_path / "pytest.ini"
        generator.write_to_file(content, output_path)

        # Check file was created
        assert output_path.exists()

        # Check file content
        written_content = output_path.read_text(encoding="utf-8")
        assert written_content == content

    def test_write_to_file_creates_parent_dir(self, tmp_path):
        """Test that write_to_file creates parent directory if needed."""
        generator = PytestConfigGenerator()
        content = generator.generate_pytest_ini(tmp_path)

        output_path = tmp_path / "subdir" / "pytest.ini"
        generator.write_to_file(content, output_path)

        # Check file was created
        assert output_path.exists()
        assert output_path.parent.exists()

    def test_write_to_file_empty_content_raises_error(self, tmp_path):
        """Test that writing empty content raises ValueError."""
        generator = PytestConfigGenerator()
        output_path = tmp_path / "pytest.ini"

        with pytest.raises(ValueError, match="Cannot write empty pytest.ini content"):
            generator.write_to_file("", output_path)

    def test_write_to_file_whitespace_only_raises_error(self, tmp_path):
        """Test that writing whitespace-only content raises ValueError."""
        generator = PytestConfigGenerator()
        output_path = tmp_path / "pytest.ini"

        with pytest.raises(ValueError, match="Cannot write empty pytest.ini content"):
            generator.write_to_file("   \n  \n  ", output_path)

    def test_validate_pytest_ini_valid_content(self, tmp_path):
        """Test validation of valid pytest.ini content."""
        generator = PytestConfigGenerator()
        content = generator.generate_pytest_ini(tmp_path)

        assert generator.validate_pytest_ini(content) is True

    def test_validate_pytest_ini_missing_pytest_section(self):
        """Test validation fails for missing [pytest] section."""
        generator = PytestConfigGenerator()
        content = """
        testpaths = tests
        markers =
            unit: Unit tests
        """

        assert generator.validate_pytest_ini(content) is False

    def test_validate_pytest_ini_missing_markers(self):
        """Test validation fails for missing markers section."""
        generator = PytestConfigGenerator()
        content = """
        [pytest]
        testpaths = tests
        python_files = test_*.py
        """

        assert generator.validate_pytest_ini(content) is False

    def test_validate_pytest_ini_missing_testpaths(self):
        """Test validation fails for missing testpaths."""
        generator = PytestConfigGenerator()
        content = """
        [pytest]
        python_files = test_*.py
        markers =
            unit: Unit tests
        """

        assert generator.validate_pytest_ini(content) is False

    def test_validate_pytest_ini_missing_python_files(self):
        """Test validation fails for missing python_files."""
        generator = PytestConfigGenerator()
        content = """
        [pytest]
        testpaths = tests
        markers =
            unit: Unit tests
        """

        assert generator.validate_pytest_ini(content) is False

    def test_validate_pytest_ini_missing_python_functions(self):
        """Test validation fails for missing python_functions."""
        generator = PytestConfigGenerator()
        content = """
        [pytest]
        testpaths = tests
        python_files = test_*.py
        markers =
            unit: Unit tests
        """

        assert generator.validate_pytest_ini(content) is False

    def test_validate_pytest_ini_empty_content(self):
        """Test validation fails for empty content."""
        generator = PytestConfigGenerator()

        assert generator.validate_pytest_ini("") is False
        assert generator.validate_pytest_ini("   \n  ") is False

    def test_validate_pytest_ini_none_content(self):
        """Test validation fails for None content."""
        generator = PytestConfigGenerator()

        assert generator.validate_pytest_ini(None) is False

    def test_generated_content_is_valid(self, tmp_path):
        """Test that generated content passes validation."""
        generator = PytestConfigGenerator()
        content = generator.generate_pytest_ini(tmp_path)

        assert generator.validate_pytest_ini(content) is True

    def test_generated_content_can_be_written_and_read(self, tmp_path):
        """Test full workflow: generate, write, read, validate."""
        generator = PytestConfigGenerator()

        # Generate content
        content = generator.generate_pytest_ini(tmp_path)

        # Write to file
        output_path = tmp_path / "pytest.ini"
        generator.write_to_file(content, output_path)

        # Read back
        written_content = output_path.read_text(encoding="utf-8")

        # Validate
        assert generator.validate_pytest_ini(written_content) is True
        assert written_content == content

    def test_marker_ordering_is_consistent(self, tmp_path):
        """Test that marker ordering is consistent across multiple generations."""
        generator = PytestConfigGenerator()

        content1 = generator.generate_pytest_ini(tmp_path)
        content2 = generator.generate_pytest_ini(tmp_path)

        # Content should be identical (deterministic)
        assert content1 == content2

    def test_taxonomy_changes_reflected_in_output(self, tmp_path):
        """Test that output reflects current taxonomy state."""
        generator = PytestConfigGenerator()
        content = generator.generate_pytest_ini(tmp_path)

        # All current test levels should be present
        for level in get_test_levels():
            assert f"{level}:" in content

        # All current test types should be present
        for test_type in get_test_types():
            assert f"{test_type}:" in content

        # All current modifiers should be present
        for modifier in get_modifiers():
            assert f"{modifier}:" in content
