"""
Integration tests for jest.config.js generation in CLI init command.

Tests end-to-end jest.config.js generation including framework detection,
file creation, and validation.
"""

import pytest
import json
from pathlib import Path

from cli.commands.init import detect_test_framework, _generate_jest_config
from cli.config_generators.jest_generator import JestConfigGenerator


@pytest.mark.integration
class TestJestGenerationIntegration:
    """Integration tests for jest.config.js generation workflow."""

    def test_detect_test_framework_jest_in_dependencies(self, tmp_path):
        """Test framework detection when jest is in dependencies."""
        # Create package.json with jest in dependencies
        package_json = {
            "name": "test-project",
            "dependencies": {
                "jest": "^29.0.0"
            }
        }
        (tmp_path / "package.json").write_text(json.dumps(package_json))

        framework = detect_test_framework(tmp_path)
        assert framework == "jest"

    def test_detect_test_framework_jest_in_dev_dependencies(self, tmp_path):
        """Test framework detection when jest is in devDependencies."""
        # Create package.json with jest in devDependencies
        package_json = {
            "name": "test-project",
            "devDependencies": {
                "jest": "^29.0.0",
                "@types/jest": "^29.0.0"
            }
        }
        (tmp_path / "package.json").write_text(json.dumps(package_json))

        framework = detect_test_framework(tmp_path)
        assert framework == "jest"

    def test_generate_jest_config_creates_file(self, tmp_path):
        """Test that _generate_jest_config creates jest.config.js file."""
        # Create package.json to indicate Jest project
        package_json = {
            "name": "test-project",
            "devDependencies": {
                "jest": "^29.0.0"
            }
        }
        (tmp_path / "package.json").write_text(json.dumps(package_json))

        result = _generate_jest_config(tmp_path)

        assert result["generated"] is True
        assert result["path"] == tmp_path / "jest.config.js"
        assert result["reason"] is None
        assert (tmp_path / "jest.config.js").exists()

    def test_generate_jest_config_skips_if_exists(self, tmp_path):
        """Test that _generate_jest_config skips if jest.config.js exists."""
        # Create existing jest.config.js
        (tmp_path / "jest.config.js").write_text("module.exports = {};\n")

        result = _generate_jest_config(tmp_path)

        assert result["generated"] is False
        assert result["path"] == tmp_path / "jest.config.js"
        assert "already exists" in result["reason"]

    def test_generate_jest_config_skips_non_jest_projects(self, tmp_path):
        """Test that _generate_jest_config skips non-Jest projects."""
        # Create setup.py for pytest project
        (tmp_path / "setup.py").write_text("from setuptools import setup\n")

        result = _generate_jest_config(tmp_path)

        assert result["generated"] is False
        assert result["path"] is None
        assert "pytest" in result["reason"]

    def test_generate_jest_config_file_content_valid(self, tmp_path):
        """Test that generated jest.config.js has valid content."""
        # Create package.json to indicate Jest project
        package_json = {
            "name": "test-project",
            "devDependencies": {
                "jest": "^29.0.0"
            }
        }
        (tmp_path / "package.json").write_text(json.dumps(package_json))

        result = _generate_jest_config(tmp_path)

        assert result["generated"] is True

        # Read and validate generated file
        jest_config_path = tmp_path / "jest.config.js"
        content = jest_config_path.read_text(encoding="utf-8")

        # Validate using generator's validation method
        generator = JestConfigGenerator()
        assert generator.validate_jest_config(content) is True

    def test_generate_jest_config_includes_all_patterns(self, tmp_path):
        """Test that generated jest.config.js includes all taxonomy patterns."""
        from config.test_taxonomy import get_test_levels, get_test_types, get_modifiers

        # Create package.json to indicate Jest project
        package_json = {
            "name": "test-project",
            "devDependencies": {
                "jest": "^29.0.0"
            }
        }
        (tmp_path / "package.json").write_text(json.dumps(package_json))

        result = _generate_jest_config(tmp_path)
        assert result["generated"] is True

        # Read generated file
        content = (tmp_path / "jest.config.js").read_text(encoding="utf-8")

        # Check all test levels
        for level in get_test_levels():
            assert f"[{level}]" in content

        # Check all test types
        for test_type in get_test_types():
            assert f"[{test_type}]" in content

        # Check all modifiers
        for modifier in get_modifiers():
            assert f"[{modifier}]" in content

    def test_generated_jest_config_is_valid_javascript(self, tmp_path):
        """Test that generated jest.config.js is valid JavaScript syntax."""
        # Create package.json to indicate Jest project
        package_json = {
            "name": "test-project",
            "devDependencies": {
                "jest": "^29.0.0"
            }
        }
        (tmp_path / "package.json").write_text(json.dumps(package_json))

        result = _generate_jest_config(tmp_path)
        assert result["generated"] is True

        # Read generated file
        content = (tmp_path / "jest.config.js").read_text(encoding="utf-8")

        # Basic JavaScript syntax checks
        assert content.count("{") == content.count("}")  # Balanced braces
        assert "module.exports = {" in content
        assert content.strip().endswith("};")

    def test_multiple_framework_indicators_prefers_existing_config(self, tmp_path):
        """Test that existing config files take precedence in framework detection."""
        # Create both jest.config.js and setup.py
        (tmp_path / "jest.config.js").write_text("module.exports = {};\n")
        (tmp_path / "setup.py").write_text("from setuptools import setup\n")

        # Should still detect as Jest due to existing config
        # But generation should skip because config exists
        result = _generate_jest_config(tmp_path)

        assert result["generated"] is False
        assert "already exists" in result["reason"]

    def test_generate_jest_config_preserves_custom_content_if_exists(self, tmp_path):
        """Test that existing jest.config.js is not overwritten."""
        # Create existing jest.config.js with custom content
        custom_content = "module.exports = { custom: true };\n"
        (tmp_path / "jest.config.js").write_text(custom_content)

        result = _generate_jest_config(tmp_path)

        # Should skip generation
        assert result["generated"] is False

        # Original content should be preserved
        assert (tmp_path / "jest.config.js").read_text() == custom_content

    def test_generated_file_uses_utf8_encoding(self, tmp_path):
        """Test that generated jest.config.js uses UTF-8 encoding."""
        # Create package.json to indicate Jest project
        package_json = {
            "name": "test-project",
            "devDependencies": {
                "jest": "^29.0.0"
            }
        }
        (tmp_path / "package.json").write_text(json.dumps(package_json))

        result = _generate_jest_config(tmp_path)
        assert result["generated"] is True

        # Read file with explicit UTF-8 encoding
        jest_config_path = tmp_path / "jest.config.js"
        content = jest_config_path.read_text(encoding="utf-8")

        # Should not raise any encoding errors
        assert "module.exports" in content

    def test_generated_file_has_newline_at_end(self, tmp_path):
        """Test that generated jest.config.js ends with newline."""
        # Create package.json to indicate Jest project
        package_json = {
            "name": "test-project",
            "devDependencies": {
                "jest": "^29.0.0"
            }
        }
        (tmp_path / "package.json").write_text(json.dumps(package_json))

        result = _generate_jest_config(tmp_path)
        assert result["generated"] is True

        # Read file
        jest_config_path = tmp_path / "jest.config.js"
        content = jest_config_path.read_text(encoding="utf-8")

        # Should end with newline
        assert content.endswith("\n")

    def test_error_handling_for_permission_denied(self, tmp_path):
        """Test error handling when file cannot be written due to permissions."""
        import os
        import stat

        # Create package.json to indicate Jest project
        package_json = {
            "name": "test-project",
            "devDependencies": {
                "jest": "^29.0.0"
            }
        }
        (tmp_path / "package.json").write_text(json.dumps(package_json))

        # Make directory read-only (on Unix-like systems)
        if os.name != 'nt':  # Skip on Windows
            tmp_path.chmod(stat.S_IRUSR | stat.S_IXUSR)

            try:
                result = _generate_jest_config(tmp_path)

                # Should handle error gracefully
                assert result["generated"] is False
                assert result["reason"] is not None
                assert "Error writing jest.config.js" in result["reason"]
            finally:
                # Restore permissions
                tmp_path.chmod(stat.S_IRWXU)

    def test_detect_framework_with_typescript_jest(self, tmp_path):
        """Test framework detection for TypeScript projects using Jest."""
        # Create package.json with TypeScript and Jest
        package_json = {
            "name": "test-project",
            "devDependencies": {
                "jest": "^29.0.0",
                "ts-jest": "^29.0.0",
                "@types/jest": "^29.0.0",
                "typescript": "^5.0.0"
            }
        }
        (tmp_path / "package.json").write_text(json.dumps(package_json))

        framework = detect_test_framework(tmp_path)
        assert framework == "jest"

    def test_generated_config_includes_typescript_hints(self, tmp_path):
        """Test that generated config includes TypeScript configuration hints."""
        # Create package.json to indicate Jest project
        package_json = {
            "name": "test-project",
            "devDependencies": {
                "jest": "^29.0.0"
            }
        }
        (tmp_path / "package.json").write_text(json.dumps(package_json))

        result = _generate_jest_config(tmp_path)
        assert result["generated"] is True

        # Read generated file
        content = (tmp_path / "jest.config.js").read_text(encoding="utf-8")

        # Should include TypeScript hints
        assert "TypeScript Support" in content
        assert "ts-jest" in content

    def test_generated_config_includes_classification_examples(self, tmp_path):
        """Test that generated config includes test classification examples."""
        # Create package.json to indicate Jest project
        package_json = {
            "name": "test-project",
            "devDependencies": {
                "jest": "^29.0.0"
            }
        }
        (tmp_path / "package.json").write_text(json.dumps(package_json))

        result = _generate_jest_config(tmp_path)
        assert result["generated"] is True

        # Read generated file
        content = (tmp_path / "jest.config.js").read_text(encoding="utf-8")

        # Should include classification approach examples
        assert "Test name patterns:" in content
        assert "Comment annotations:" in content
        assert "Test file organization:" in content
        assert "describe('[unit][functional]" in content

    def test_generated_config_includes_filtering_examples(self, tmp_path):
        """Test that generated config includes test filtering examples."""
        # Create package.json to indicate Jest project
        package_json = {
            "name": "test-project",
            "devDependencies": {
                "jest": "^29.0.0"
            }
        }
        (tmp_path / "package.json").write_text(json.dumps(package_json))

        result = _generate_jest_config(tmp_path)
        assert result["generated"] is True

        # Read generated file
        content = (tmp_path / "jest.config.js").read_text(encoding="utf-8")

        # Should include filtering examples
        assert "Running specific test types:" in content
        assert "--testNamePattern" in content
        assert "[unit]" in content
        assert "[integration]" in content
        assert "[functional]" in content

    def test_generated_config_has_appropriate_coverage_exclusions(self, tmp_path):
        """Test that generated config excludes appropriate files from coverage."""
        # Create package.json to indicate Jest project
        package_json = {
            "name": "test-project",
            "devDependencies": {
                "jest": "^29.0.0"
            }
        }
        (tmp_path / "package.json").write_text(json.dumps(package_json))

        result = _generate_jest_config(tmp_path)
        assert result["generated"] is True

        # Read generated file
        content = (tmp_path / "jest.config.js").read_text(encoding="utf-8")

        # Should exclude common non-source files
        assert "!src/**/*.d.ts" in content
        assert "!src/**/*.stories.{js,jsx,ts,tsx}" in content
        assert "!src/**/__tests__/**" in content

    def test_package_json_without_jest_returns_generic(self, tmp_path):
        """Test that package.json without jest dependency returns generic framework."""
        # Create package.json without Jest
        package_json = {
            "name": "test-project",
            "dependencies": {
                "express": "^4.0.0"
            }
        }
        (tmp_path / "package.json").write_text(json.dumps(package_json))

        framework = detect_test_framework(tmp_path)
        assert framework == "generic"

    def test_malformed_package_json_returns_generic(self, tmp_path):
        """Test that malformed package.json returns generic framework."""
        # Create malformed package.json
        (tmp_path / "package.json").write_text("{ invalid json")

        framework = detect_test_framework(tmp_path)
        assert framework == "generic"

    def test_generated_config_default_coverage_threshold(self, tmp_path):
        """Test that generated config uses default 80% coverage threshold."""
        # Create package.json to indicate Jest project
        package_json = {
            "name": "test-project",
            "devDependencies": {
                "jest": "^29.0.0"
            }
        }
        (tmp_path / "package.json").write_text(json.dumps(package_json))

        result = _generate_jest_config(tmp_path)
        assert result["generated"] is True

        # Read generated file
        content = (tmp_path / "jest.config.js").read_text(encoding="utf-8")

        # Should have 80% thresholds
        assert "branches: 80" in content
        assert "functions: 80" in content
        assert "lines: 80" in content
        assert "statements: 80" in content
