"""
Integration tests for pytest.ini generation in CLI init command.

Tests end-to-end pytest.ini generation including framework detection,
file creation, and validation.
"""

import pytest
from pathlib import Path
from click.testing import CliRunner

from cli.commands.init import detect_test_framework, _generate_pytest_config
from cli.config_generators.pytest_generator import PytestConfigGenerator


@pytest.mark.integration
class TestPytestGenerationIntegration:
    """Integration tests for pytest.ini generation workflow."""

    def test_detect_test_framework_pytest_with_pytest_ini(self, tmp_path):
        """Test framework detection when pytest.ini exists."""
        # Create pytest.ini file
        (tmp_path / "pytest.ini").write_text("[pytest]\n")

        framework = detect_test_framework(tmp_path)
        assert framework == "pytest"

    def test_detect_test_framework_pytest_with_setup_py(self, tmp_path):
        """Test framework detection when setup.py exists."""
        # Create setup.py file
        (tmp_path / "setup.py").write_text("from setuptools import setup\n")

        framework = detect_test_framework(tmp_path)
        assert framework == "pytest"

    def test_detect_test_framework_pytest_with_pyproject_toml(self, tmp_path):
        """Test framework detection with pyproject.toml containing pytest config."""
        # Create pyproject.toml with pytest section
        (tmp_path / "pyproject.toml").write_text(
            "[tool.pytest.ini_options]\ntestpaths = ['tests']\n"
        )

        framework = detect_test_framework(tmp_path)
        assert framework == "pytest"

    def test_detect_test_framework_pytest_with_setup_cfg(self, tmp_path):
        """Test framework detection with setup.cfg containing pytest config."""
        # Create setup.cfg with pytest section
        (tmp_path / "setup.cfg").write_text("[tool:pytest]\ntestpaths = tests\n")

        framework = detect_test_framework(tmp_path)
        assert framework == "pytest"

    def test_detect_test_framework_jest(self, tmp_path):
        """Test framework detection for Jest projects."""
        # Create package.json with jest dependency
        (tmp_path / "package.json").write_text(
            '{"devDependencies": {"jest": "^29.0.0"}}'
        )

        framework = detect_test_framework(tmp_path)
        assert framework == "jest"

    def test_detect_test_framework_junit_maven(self, tmp_path):
        """Test framework detection for JUnit with Maven."""
        # Create pom.xml
        (tmp_path / "pom.xml").write_text("<project></project>")

        framework = detect_test_framework(tmp_path)
        assert framework == "junit"

    def test_detect_test_framework_junit_gradle(self, tmp_path):
        """Test framework detection for JUnit with Gradle."""
        # Create build.gradle
        (tmp_path / "build.gradle").write_text("")

        framework = detect_test_framework(tmp_path)
        assert framework == "junit"

    def test_detect_test_framework_go(self, tmp_path):
        """Test framework detection for Go projects."""
        # Create go.mod
        (tmp_path / "go.mod").write_text("module example.com/myproject\n")

        framework = detect_test_framework(tmp_path)
        assert framework == "go-testing"

    def test_detect_test_framework_generic(self, tmp_path):
        """Test framework detection returns generic for unknown projects."""
        # Empty directory with no test framework indicators
        framework = detect_test_framework(tmp_path)
        assert framework == "generic"

    def test_generate_pytest_config_creates_file(self, tmp_path):
        """Test that _generate_pytest_config creates pytest.ini file."""
        # Create setup.py to indicate pytest project
        (tmp_path / "setup.py").write_text("from setuptools import setup\n")

        result = _generate_pytest_config(tmp_path)

        assert result["generated"] is True
        assert result["path"] == tmp_path / "pytest.ini"
        assert result["reason"] is None
        assert (tmp_path / "pytest.ini").exists()

    def test_generate_pytest_config_skips_if_exists(self, tmp_path):
        """Test that _generate_pytest_config skips if pytest.ini exists."""
        # Create existing pytest.ini
        (tmp_path / "pytest.ini").write_text("[pytest]\n")

        result = _generate_pytest_config(tmp_path)

        assert result["generated"] is False
        assert result["path"] == tmp_path / "pytest.ini"
        assert "already exists" in result["reason"]

    def test_generate_pytest_config_skips_non_pytest_projects(self, tmp_path):
        """Test that _generate_pytest_config skips non-pytest projects."""
        # Create package.json for Jest project
        (tmp_path / "package.json").write_text(
            '{"devDependencies": {"jest": "^29.0.0"}}'
        )

        result = _generate_pytest_config(tmp_path)

        assert result["generated"] is False
        assert result["path"] is None
        assert "jest" in result["reason"]

    def test_generate_pytest_config_file_content_valid(self, tmp_path):
        """Test that generated pytest.ini has valid content."""
        # Create setup.py to indicate pytest project
        (tmp_path / "setup.py").write_text("from setuptools import setup\n")

        result = _generate_pytest_config(tmp_path)

        assert result["generated"] is True

        # Read and validate generated file
        pytest_ini_path = tmp_path / "pytest.ini"
        content = pytest_ini_path.read_text(encoding="utf-8")

        # Validate using generator's validation method
        generator = PytestConfigGenerator()
        assert generator.validate_pytest_ini(content) is True

    def test_generate_pytest_config_includes_all_markers(self, tmp_path):
        """Test that generated pytest.ini includes all taxonomy markers."""
        from config.test_taxonomy import get_test_levels, get_test_types, get_modifiers

        # Create setup.py to indicate pytest project
        (tmp_path / "setup.py").write_text("from setuptools import setup\n")

        result = _generate_pytest_config(tmp_path)
        assert result["generated"] is True

        # Read generated file
        content = (tmp_path / "pytest.ini").read_text(encoding="utf-8")

        # Check all test levels
        for level in get_test_levels():
            assert f"{level}:" in content

        # Check all test types
        for test_type in get_test_types():
            assert f"{test_type}:" in content

        # Check all modifiers
        for modifier in get_modifiers():
            assert f"{modifier}:" in content

    def test_generated_pytest_ini_can_be_parsed(self, tmp_path):
        """Test that generated pytest.ini can be parsed by configparser."""
        import configparser

        # Create setup.py to indicate pytest project
        (tmp_path / "setup.py").write_text("from setuptools import setup\n")

        result = _generate_pytest_config(tmp_path)
        assert result["generated"] is True

        # Try to parse the generated file
        config = configparser.ConfigParser()
        pytest_ini_path = tmp_path / "pytest.ini"
        config.read(pytest_ini_path)

        # Check that pytest section exists
        assert "pytest" in config.sections()

        # Check key settings
        assert config.get("pytest", "testpaths") == "tests"
        assert config.get("pytest", "python_files") == "test_*.py"
        assert config.get("pytest", "console_output_style") == "progress"

    def test_multiple_framework_indicators_prefers_pytest_ini(self, tmp_path):
        """Test that pytest.ini takes precedence in framework detection."""
        # Create both pytest.ini and package.json
        (tmp_path / "pytest.ini").write_text("[pytest]\n")
        (tmp_path / "package.json").write_text(
            '{"devDependencies": {"jest": "^29.0.0"}}'
        )

        framework = detect_test_framework(tmp_path)
        assert framework == "pytest"

    def test_generate_pytest_config_preserves_custom_content_if_exists(self, tmp_path):
        """Test that existing pytest.ini is not overwritten."""
        # Create existing pytest.ini with custom content
        custom_content = "[pytest]\ncustom_option = custom_value\n"
        (tmp_path / "pytest.ini").write_text(custom_content)

        result = _generate_pytest_config(tmp_path)

        # Should skip generation
        assert result["generated"] is False

        # Original content should be preserved
        assert (tmp_path / "pytest.ini").read_text() == custom_content

    def test_generated_file_uses_utf8_encoding(self, tmp_path):
        """Test that generated pytest.ini uses UTF-8 encoding."""
        # Create setup.py to indicate pytest project
        (tmp_path / "setup.py").write_text("from setuptools import setup\n")

        result = _generate_pytest_config(tmp_path)
        assert result["generated"] is True

        # Read file with explicit UTF-8 encoding
        pytest_ini_path = tmp_path / "pytest.ini"
        content = pytest_ini_path.read_text(encoding="utf-8")

        # Should not raise any encoding errors
        assert "[pytest]" in content

    def test_generated_file_has_newline_at_end(self, tmp_path):
        """Test that generated pytest.ini ends with newline."""
        # Create setup.py to indicate pytest project
        (tmp_path / "setup.py").write_text("from setuptools import setup\n")

        result = _generate_pytest_config(tmp_path)
        assert result["generated"] is True

        # Read file
        pytest_ini_path = tmp_path / "pytest.ini"
        content = pytest_ini_path.read_text(encoding="utf-8")

        # Should end with newline
        assert content.endswith("\n")

    def test_error_handling_for_permission_denied(self, tmp_path):
        """Test error handling when file cannot be written due to permissions."""
        import os
        import stat

        # Create setup.py to indicate pytest project
        (tmp_path / "setup.py").write_text("from setuptools import setup\n")

        # Make directory read-only (on Unix-like systems)
        if os.name != 'nt':  # Skip on Windows
            tmp_path.chmod(stat.S_IRUSR | stat.S_IXUSR)

            try:
                result = _generate_pytest_config(tmp_path)

                # Should handle error gracefully
                assert result["generated"] is False
                assert result["reason"] is not None
                assert "Error writing pytest.ini" in result["reason"]
            finally:
                # Restore permissions
                tmp_path.chmod(stat.S_IRWXU)
