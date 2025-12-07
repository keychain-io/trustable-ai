"""
Unit tests for test framework detection.

Tests the detect_test_framework() function in cli/commands/init.py to ensure
accurate detection of testing frameworks across different project types.
"""
import pytest
from pathlib import Path
import json

from cli.commands.init import detect_test_framework


@pytest.mark.unit
class TestFrameworkDetection:
    """Test framework detection logic."""

    def test_detect_pytest_with_pytest_ini(self, tmp_path):
        """Test detection of pytest via pytest.ini file."""
        # Arrange
        pytest_ini = tmp_path / "pytest.ini"
        pytest_ini.write_text("[pytest]\ntestpaths = tests\n")

        # Act
        framework = detect_test_framework(tmp_path)

        # Assert
        assert framework == "pytest"

    def test_detect_pytest_with_setup_py(self, tmp_path):
        """Test detection of pytest via setup.py file."""
        # Arrange
        setup_py = tmp_path / "setup.py"
        setup_py.write_text("from setuptools import setup\nsetup(name='test')\n")

        # Act
        framework = detect_test_framework(tmp_path)

        # Assert
        assert framework == "pytest"

    def test_detect_pytest_with_pyproject_toml(self, tmp_path):
        """Test detection of pytest via pyproject.toml with [tool.pytest] section."""
        # Arrange
        pyproject_toml = tmp_path / "pyproject.toml"
        pyproject_toml.write_text("""
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
""")

        # Act
        framework = detect_test_framework(tmp_path)

        # Assert
        assert framework == "pytest"

    def test_detect_pytest_with_setup_cfg(self, tmp_path):
        """Test detection of pytest via setup.cfg with [tool:pytest] section."""
        # Arrange
        setup_cfg = tmp_path / "setup.cfg"
        setup_cfg.write_text("""
[tool:pytest]
testpaths = tests
python_files = test_*.py
""")

        # Act
        framework = detect_test_framework(tmp_path)

        # Assert
        assert framework == "pytest"

    def test_detect_pytest_with_setup_cfg_pytest_section(self, tmp_path):
        """Test detection of pytest via setup.cfg with [pytest] section."""
        # Arrange
        setup_cfg = tmp_path / "setup.cfg"
        setup_cfg.write_text("""
[pytest]
testpaths = tests
""")

        # Act
        framework = detect_test_framework(tmp_path)

        # Assert
        assert framework == "pytest"

    def test_detect_jest_in_dev_dependencies(self, tmp_path):
        """Test detection of Jest via package.json devDependencies."""
        # Arrange
        package_json = tmp_path / "package.json"
        package_data = {
            "name": "test-project",
            "version": "1.0.0",
            "devDependencies": {
                "jest": "^29.0.0",
                "typescript": "^5.0.0"
            }
        }
        package_json.write_text(json.dumps(package_data))

        # Act
        framework = detect_test_framework(tmp_path)

        # Assert
        assert framework == "jest"

    def test_detect_jest_in_dependencies(self, tmp_path):
        """Test detection of Jest via package.json dependencies."""
        # Arrange
        package_json = tmp_path / "package.json"
        package_data = {
            "name": "test-project",
            "version": "1.0.0",
            "dependencies": {
                "jest": "^29.0.0",
                "react": "^18.0.0"
            }
        }
        package_json.write_text(json.dumps(package_data))

        # Act
        framework = detect_test_framework(tmp_path)

        # Assert
        assert framework == "jest"

    def test_detect_junit_with_pom_xml(self, tmp_path):
        """Test detection of JUnit via pom.xml (Maven)."""
        # Arrange
        pom_xml = tmp_path / "pom.xml"
        pom_xml.write_text("""
<project>
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.test</groupId>
    <artifactId>test-project</artifactId>
</project>
""")

        # Act
        framework = detect_test_framework(tmp_path)

        # Assert
        assert framework == "junit"

    def test_detect_junit_with_build_gradle(self, tmp_path):
        """Test detection of JUnit via build.gradle (Gradle)."""
        # Arrange
        build_gradle = tmp_path / "build.gradle"
        build_gradle.write_text("""
plugins {
    id 'java'
}
dependencies {
    testImplementation 'org.junit.jupiter:junit-jupiter:5.9.0'
}
""")

        # Act
        framework = detect_test_framework(tmp_path)

        # Assert
        assert framework == "junit"

    def test_detect_go_testing_with_go_mod(self, tmp_path):
        """Test detection of Go testing via go.mod file."""
        # Arrange
        go_mod = tmp_path / "go.mod"
        go_mod.write_text("""
module github.com/test/project

go 1.21
""")

        # Act
        framework = detect_test_framework(tmp_path)

        # Assert
        assert framework == "go-testing"

    def test_detect_generic_when_no_framework_files(self, tmp_path):
        """Test fallback to generic when no framework files are present."""
        # Arrange - empty directory

        # Act
        framework = detect_test_framework(tmp_path)

        # Assert
        assert framework == "generic"

    def test_detect_generic_with_unrelated_files(self, tmp_path):
        """Test fallback to generic when only unrelated files are present."""
        # Arrange
        readme = tmp_path / "README.md"
        readme.write_text("# Test Project")

        src_file = tmp_path / "main.py"
        src_file.write_text("print('hello')")

        # Act
        framework = detect_test_framework(tmp_path)

        # Assert
        assert framework == "generic"

    def test_pytest_priority_over_package_json(self, tmp_path):
        """Test that pytest.ini takes priority when both pytest and package.json exist."""
        # Arrange
        pytest_ini = tmp_path / "pytest.ini"
        pytest_ini.write_text("[pytest]\n")

        package_json = tmp_path / "package.json"
        package_data = {
            "name": "test-project",
            "devDependencies": {
                "jest": "^29.0.0"
            }
        }
        package_json.write_text(json.dumps(package_data))

        # Act
        framework = detect_test_framework(tmp_path)

        # Assert
        # pytest.ini is checked first, so pytest should win
        assert framework == "pytest"

    def test_pyproject_toml_without_pytest_section(self, tmp_path):
        """Test that pyproject.toml without pytest section doesn't trigger pytest detection."""
        # Arrange
        pyproject_toml = tmp_path / "pyproject.toml"
        pyproject_toml.write_text("""
[tool.black]
line-length = 88

[build-system]
requires = ["setuptools"]
""")

        # Act
        framework = detect_test_framework(tmp_path)

        # Assert
        assert framework == "generic"

    def test_package_json_without_jest(self, tmp_path):
        """Test that package.json without jest doesn't trigger Jest detection."""
        # Arrange
        package_json = tmp_path / "package.json"
        package_data = {
            "name": "test-project",
            "dependencies": {
                "react": "^18.0.0"
            },
            "devDependencies": {
                "typescript": "^5.0.0"
            }
        }
        package_json.write_text(json.dumps(package_data))

        # Act
        framework = detect_test_framework(tmp_path)

        # Assert
        assert framework == "generic"

    def test_malformed_pyproject_toml_continues_detection(self, tmp_path):
        """Test that malformed pyproject.toml doesn't crash detection."""
        # Arrange
        pyproject_toml = tmp_path / "pyproject.toml"
        pyproject_toml.write_text("invalid toml content {[}")

        setup_py = tmp_path / "setup.py"
        setup_py.write_text("from setuptools import setup\n")

        # Act
        framework = detect_test_framework(tmp_path)

        # Assert
        # Should continue to check setup.py and return pytest
        assert framework == "pytest"

    def test_malformed_package_json_continues_detection(self, tmp_path):
        """Test that malformed package.json doesn't crash detection."""
        # Arrange
        package_json = tmp_path / "package.json"
        package_json.write_text("{ invalid json }")

        go_mod = tmp_path / "go.mod"
        go_mod.write_text("module test\n")

        # Act
        framework = detect_test_framework(tmp_path)

        # Assert
        # Should continue to check go.mod and return go-testing
        assert framework == "go-testing"

    def test_malformed_setup_cfg_continues_detection(self, tmp_path):
        """Test that malformed setup.cfg doesn't crash detection."""
        # Arrange
        setup_cfg = tmp_path / "setup.cfg"
        # File exists but can't be read (permission issue simulation via empty)
        setup_cfg.write_text("")

        pom_xml = tmp_path / "pom.xml"
        pom_xml.write_text("<project></project>")

        # Act
        framework = detect_test_framework(tmp_path)

        # Assert
        # Should continue to check pom.xml and return junit
        assert framework == "junit"

    def test_nonexistent_directory_returns_generic(self, tmp_path):
        """Test that nonexistent directory returns generic."""
        # Arrange
        nonexistent_path = tmp_path / "nonexistent"

        # Act
        framework = detect_test_framework(nonexistent_path)

        # Assert
        assert framework == "generic"


@pytest.mark.unit
class TestFrameworkDetectionEdgeCases:
    """Test edge cases in framework detection."""

    def test_empty_package_json(self, tmp_path):
        """Test empty package.json returns generic."""
        # Arrange
        package_json = tmp_path / "package.json"
        package_json.write_text("{}")

        # Act
        framework = detect_test_framework(tmp_path)

        # Assert
        assert framework == "generic"

    def test_package_json_with_null_dependencies(self, tmp_path):
        """Test package.json with null dependencies doesn't crash."""
        # Arrange
        package_json = tmp_path / "package.json"
        package_data = {
            "name": "test-project",
            "dependencies": None,
            "devDependencies": None
        }
        package_json.write_text(json.dumps(package_data))

        # Act
        framework = detect_test_framework(tmp_path)

        # Assert
        assert framework == "generic"

    def test_multiple_framework_files_precedence(self, tmp_path):
        """Test precedence when multiple framework files exist."""
        # Arrange - create files in reverse priority order
        go_mod = tmp_path / "go.mod"
        go_mod.write_text("module test\n")

        pom_xml = tmp_path / "pom.xml"
        pom_xml.write_text("<project></project>")

        package_json = tmp_path / "package.json"
        package_data = {"devDependencies": {"jest": "^29.0.0"}}
        package_json.write_text(json.dumps(package_data))

        setup_py = tmp_path / "setup.py"
        setup_py.write_text("from setuptools import setup\n")

        pytest_ini = tmp_path / "pytest.ini"
        pytest_ini.write_text("[pytest]\n")

        # Act
        framework = detect_test_framework(tmp_path)

        # Assert
        # pytest.ini is checked first, should win
        assert framework == "pytest"

    def test_case_sensitivity_package_json(self, tmp_path):
        """Test that jest detection is case-sensitive in package.json."""
        # Arrange
        package_json = tmp_path / "package.json"
        package_data = {
            "devDependencies": {
                "Jest": "^29.0.0"  # Capital J
            }
        }
        package_json.write_text(json.dumps(package_data))

        # Act
        framework = detect_test_framework(tmp_path)

        # Assert
        # Should not match "Jest" (capital J)
        assert framework == "generic"

    def test_jest_in_package_name_not_dependency(self, tmp_path):
        """Test that jest in package name doesn't trigger detection."""
        # Arrange
        package_json = tmp_path / "package.json"
        package_data = {
            "name": "jest-utils",  # jest in name, not dependency
            "dependencies": {}
        }
        package_json.write_text(json.dumps(package_data))

        # Act
        framework = detect_test_framework(tmp_path)

        # Assert
        assert framework == "generic"
