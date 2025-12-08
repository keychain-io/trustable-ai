"""
Configuration Generators for Testing Frameworks.

Generates framework-specific test configuration files based on the universal
test taxonomy defined in config/test_taxonomy.py.

This module solves **inconsistent test configuration** across projects by
providing standardized configuration generators that apply the universal test
taxonomy to each project's native test framework.

Available Generators:
    - PytestConfigGenerator: Generate pytest.ini for Python projects
    - (Future) JestConfigGenerator: Generate jest.config.js for JavaScript projects
    - (Future) JUnitConfigGenerator: Generate test config for Java projects

Example Usage:
    from cli.config_generators.pytest_generator import PytestConfigGenerator

    generator = PytestConfigGenerator()
    pytest_ini_content = generator.generate_pytest_ini(Path("/path/to/project"))

    # Write to file
    with open("pytest.ini", "w", encoding="utf-8") as f:
        f.write(pytest_ini_content)
"""

from cli.config_generators.pytest_generator import PytestConfigGenerator

__all__ = ["PytestConfigGenerator"]
