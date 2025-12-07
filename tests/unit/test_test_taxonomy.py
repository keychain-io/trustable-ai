"""
Unit tests for Test Taxonomy.

Tests universal test classification taxonomy used across all testing frameworks.
Validates taxonomy structure, accessor functions, and validation logic.
"""

import pytest
from typing import List, Dict

from config.test_taxonomy import (
    TEST_TAXONOMY,
    get_test_levels,
    get_test_types,
    get_modifiers,
    get_test_level_description,
    get_test_type_description,
    get_modifier_description,
    is_valid_test_level,
    is_valid_test_type,
    is_valid_modifier,
    validate_test_classification,
    get_taxonomy_summary,
)


@pytest.mark.unit
class TestTaxonomyStructure:
    """Test that taxonomy structure is valid and complete."""

    def test_taxonomy_has_all_dimensions(self):
        """Test that taxonomy contains all required dimensions."""
        assert "test_levels" in TEST_TAXONOMY
        assert "test_types" in TEST_TAXONOMY
        assert "modifiers" in TEST_TAXONOMY

    def test_test_levels_not_empty(self):
        """Test that test_levels dimension is not empty."""
        assert len(TEST_TAXONOMY["test_levels"]) > 0

    def test_test_types_not_empty(self):
        """Test that test_types dimension is not empty."""
        assert len(TEST_TAXONOMY["test_types"]) > 0

    def test_modifiers_not_empty(self):
        """Test that modifiers dimension is not empty."""
        assert len(TEST_TAXONOMY["modifiers"]) > 0

    def test_test_levels_have_descriptions(self):
        """Test that all test levels have non-empty descriptions."""
        for level, description in TEST_TAXONOMY["test_levels"].items():
            assert isinstance(level, str)
            assert len(level) > 0
            assert isinstance(description, str)
            assert len(description) > 0

    def test_test_types_have_descriptions(self):
        """Test that all test types have non-empty descriptions."""
        for test_type, description in TEST_TAXONOMY["test_types"].items():
            assert isinstance(test_type, str)
            assert len(test_type) > 0
            assert isinstance(description, str)
            assert len(description) > 0

    def test_modifiers_have_descriptions(self):
        """Test that all modifiers have non-empty descriptions."""
        for modifier, description in TEST_TAXONOMY["modifiers"].items():
            assert isinstance(modifier, str)
            assert len(modifier) > 0
            assert isinstance(description, str)
            assert len(description) > 0


@pytest.mark.unit
class TestRequiredTestLevels:
    """Test that all required test levels are present."""

    def test_unit_level_exists(self):
        """Test that 'unit' test level exists."""
        assert "unit" in TEST_TAXONOMY["test_levels"]

    def test_integration_level_exists(self):
        """Test that 'integration' test level exists."""
        assert "integration" in TEST_TAXONOMY["test_levels"]

    def test_system_level_exists(self):
        """Test that 'system' test level exists."""
        assert "system" in TEST_TAXONOMY["test_levels"]

    def test_acceptance_level_exists(self):
        """Test that 'acceptance' test level exists."""
        assert "acceptance" in TEST_TAXONOMY["test_levels"]

    def test_validation_level_exists(self):
        """Test that 'validation' test level exists."""
        assert "validation" in TEST_TAXONOMY["test_levels"]


@pytest.mark.unit
class TestRequiredTestTypes:
    """Test that all required test types are present."""

    def test_functional_type_exists(self):
        """Test that 'functional' test type exists."""
        assert "functional" in TEST_TAXONOMY["test_types"]

    def test_security_type_exists(self):
        """Test that 'security' test type exists."""
        assert "security" in TEST_TAXONOMY["test_types"]

    def test_performance_type_exists(self):
        """Test that 'performance' test type exists."""
        assert "performance" in TEST_TAXONOMY["test_types"]

    def test_usability_type_exists(self):
        """Test that 'usability' test type exists."""
        assert "usability" in TEST_TAXONOMY["test_types"]


@pytest.mark.unit
class TestRequiredModifiers:
    """Test that all required modifiers are present."""

    def test_slow_modifier_exists(self):
        """Test that 'slow' modifier exists."""
        assert "slow" in TEST_TAXONOMY["modifiers"]

    def test_requires_db_modifier_exists(self):
        """Test that 'requires-db' modifier exists."""
        assert "requires-db" in TEST_TAXONOMY["modifiers"]

    def test_requires_network_modifier_exists(self):
        """Test that 'requires-network' modifier exists."""
        assert "requires-network" in TEST_TAXONOMY["modifiers"]

    def test_flaky_modifier_exists(self):
        """Test that 'flaky' modifier exists."""
        assert "flaky" in TEST_TAXONOMY["modifiers"]


@pytest.mark.unit
class TestGetTestLevels:
    """Test get_test_levels() function."""

    def test_returns_list(self):
        """Test that get_test_levels returns a list."""
        levels = get_test_levels()
        assert isinstance(levels, list)

    def test_returns_all_levels(self):
        """Test that get_test_levels returns all taxonomy levels."""
        levels = get_test_levels()
        expected = ["unit", "integration", "system", "acceptance", "validation"]
        assert set(levels) == set(expected)

    def test_returns_non_empty(self):
        """Test that get_test_levels returns non-empty list."""
        levels = get_test_levels()
        assert len(levels) > 0


@pytest.mark.unit
class TestGetTestTypes:
    """Test get_test_types() function."""

    def test_returns_list(self):
        """Test that get_test_types returns a list."""
        types = get_test_types()
        assert isinstance(types, list)

    def test_returns_all_types(self):
        """Test that get_test_types returns all taxonomy types."""
        types = get_test_types()
        expected = ["functional", "security", "performance", "usability"]
        assert set(types) == set(expected)

    def test_returns_non_empty(self):
        """Test that get_test_types returns non-empty list."""
        types = get_test_types()
        assert len(types) > 0


@pytest.mark.unit
class TestGetModifiers:
    """Test get_modifiers() function."""

    def test_returns_list(self):
        """Test that get_modifiers returns a list."""
        modifiers = get_modifiers()
        assert isinstance(modifiers, list)

    def test_returns_all_modifiers(self):
        """Test that get_modifiers returns all taxonomy modifiers."""
        modifiers = get_modifiers()
        expected = ["slow", "requires-db", "requires-network", "flaky"]
        assert set(modifiers) == set(expected)

    def test_returns_non_empty(self):
        """Test that get_modifiers returns non-empty list."""
        modifiers = get_modifiers()
        assert len(modifiers) > 0


@pytest.mark.unit
class TestGetTestLevelDescription:
    """Test get_test_level_description() function."""

    def test_returns_unit_description(self):
        """Test that unit level description is returned."""
        description = get_test_level_description("unit")
        assert description == "Isolated components/functions"

    def test_returns_integration_description(self):
        """Test that integration level description is returned."""
        description = get_test_level_description("integration")
        assert description == "Component interactions"

    def test_returns_system_description(self):
        """Test that system level description is returned."""
        description = get_test_level_description("system")
        assert description == "End-to-end workflows"

    def test_returns_acceptance_description(self):
        """Test that acceptance level description is returned."""
        description = get_test_level_description("acceptance")
        assert description == "User acceptance criteria"

    def test_returns_validation_description(self):
        """Test that validation level description is returned."""
        description = get_test_level_description("validation")
        assert description == "Release validation"

    def test_returns_none_for_invalid_level(self):
        """Test that None is returned for invalid test level."""
        description = get_test_level_description("invalid_level")
        assert description is None


@pytest.mark.unit
class TestGetTestTypeDescription:
    """Test get_test_type_description() function."""

    def test_returns_functional_description(self):
        """Test that functional type description is returned."""
        description = get_test_type_description("functional")
        assert description == "Business logic, features, functionality"

    def test_returns_security_description(self):
        """Test that security type description is returned."""
        description = get_test_type_description("security")
        assert description == "Authentication, authorization, vulnerabilities"

    def test_returns_performance_description(self):
        """Test that performance type description is returned."""
        description = get_test_type_description("performance")
        assert description == "Speed, throughput, resource usage"

    def test_returns_usability_description(self):
        """Test that usability type description is returned."""
        description = get_test_type_description("usability")
        assert description == "UI/UX, accessibility, user workflows"

    def test_returns_none_for_invalid_type(self):
        """Test that None is returned for invalid test type."""
        description = get_test_type_description("invalid_type")
        assert description is None


@pytest.mark.unit
class TestGetModifierDescription:
    """Test get_modifier_description() function."""

    def test_returns_slow_description(self):
        """Test that slow modifier description is returned."""
        description = get_modifier_description("slow")
        assert description == "Tests taking >10 seconds"

    def test_returns_requires_db_description(self):
        """Test that requires-db modifier description is returned."""
        description = get_modifier_description("requires-db")
        assert description == "Tests requiring database"

    def test_returns_requires_network_description(self):
        """Test that requires-network modifier description is returned."""
        description = get_modifier_description("requires-network")
        assert description == "Tests requiring network access"

    def test_returns_flaky_description(self):
        """Test that flaky modifier description is returned."""
        description = get_modifier_description("flaky")
        assert description == "Tests with known intermittent failures"

    def test_returns_none_for_invalid_modifier(self):
        """Test that None is returned for invalid modifier."""
        description = get_modifier_description("invalid_modifier")
        assert description is None


@pytest.mark.unit
class TestIsValidTestLevel:
    """Test is_valid_test_level() function."""

    def test_unit_is_valid(self):
        """Test that 'unit' is a valid test level."""
        assert is_valid_test_level("unit") is True

    def test_integration_is_valid(self):
        """Test that 'integration' is a valid test level."""
        assert is_valid_test_level("integration") is True

    def test_system_is_valid(self):
        """Test that 'system' is a valid test level."""
        assert is_valid_test_level("system") is True

    def test_acceptance_is_valid(self):
        """Test that 'acceptance' is a valid test level."""
        assert is_valid_test_level("acceptance") is True

    def test_validation_is_valid(self):
        """Test that 'validation' is a valid test level."""
        assert is_valid_test_level("validation") is True

    def test_invalid_level_is_not_valid(self):
        """Test that invalid level name is not valid."""
        assert is_valid_test_level("invalid") is False

    def test_empty_string_is_not_valid(self):
        """Test that empty string is not valid test level."""
        assert is_valid_test_level("") is False


@pytest.mark.unit
class TestIsValidTestType:
    """Test is_valid_test_type() function."""

    def test_functional_is_valid(self):
        """Test that 'functional' is a valid test type."""
        assert is_valid_test_type("functional") is True

    def test_security_is_valid(self):
        """Test that 'security' is a valid test type."""
        assert is_valid_test_type("security") is True

    def test_performance_is_valid(self):
        """Test that 'performance' is a valid test type."""
        assert is_valid_test_type("performance") is True

    def test_usability_is_valid(self):
        """Test that 'usability' is a valid test type."""
        assert is_valid_test_type("usability") is True

    def test_invalid_type_is_not_valid(self):
        """Test that invalid type name is not valid."""
        assert is_valid_test_type("invalid") is False

    def test_empty_string_is_not_valid(self):
        """Test that empty string is not valid test type."""
        assert is_valid_test_type("") is False


@pytest.mark.unit
class TestIsValidModifier:
    """Test is_valid_modifier() function."""

    def test_slow_is_valid(self):
        """Test that 'slow' is a valid modifier."""
        assert is_valid_modifier("slow") is True

    def test_requires_db_is_valid(self):
        """Test that 'requires-db' is a valid modifier."""
        assert is_valid_modifier("requires-db") is True

    def test_requires_network_is_valid(self):
        """Test that 'requires-network' is a valid modifier."""
        assert is_valid_modifier("requires-network") is True

    def test_flaky_is_valid(self):
        """Test that 'flaky' is a valid modifier."""
        assert is_valid_modifier("flaky") is True

    def test_invalid_modifier_is_not_valid(self):
        """Test that invalid modifier name is not valid."""
        assert is_valid_modifier("invalid") is False

    def test_empty_string_is_not_valid(self):
        """Test that empty string is not valid modifier."""
        assert is_valid_modifier("") is False


@pytest.mark.unit
class TestValidateTestClassification:
    """Test validate_test_classification() function."""

    def test_valid_classification_unit_functional(self):
        """Test validation of valid classification: unit + functional."""
        errors = validate_test_classification("unit", ["functional"])
        assert errors == {}

    def test_valid_classification_integration_security(self):
        """Test validation of valid classification: integration + security."""
        errors = validate_test_classification("integration", ["security"])
        assert errors == {}

    def test_valid_classification_multiple_types(self):
        """Test validation with multiple test types."""
        errors = validate_test_classification(
            "unit",
            ["functional", "security", "performance"]
        )
        assert errors == {}

    def test_valid_classification_with_modifiers(self):
        """Test validation with optional modifiers."""
        errors = validate_test_classification(
            "integration",
            ["functional"],
            ["slow", "requires-db"]
        )
        assert errors == {}

    def test_invalid_level_returns_error(self):
        """Test that invalid test level returns error."""
        errors = validate_test_classification("invalid_level", ["functional"])
        assert "level" in errors
        assert any("Invalid test level" in err for err in errors["level"])

    def test_missing_level_returns_error(self):
        """Test that missing test level returns error."""
        errors = validate_test_classification("", ["functional"])
        assert "level" in errors
        assert any("Test level is required" in err for err in errors["level"])

    def test_empty_types_returns_error(self):
        """Test that empty test types list returns error."""
        errors = validate_test_classification("unit", [])
        assert "types" in errors
        assert any("At least one test type required" in err for err in errors["types"])

    def test_invalid_type_returns_error(self):
        """Test that invalid test type returns error."""
        errors = validate_test_classification("unit", ["invalid_type"])
        assert "types" in errors
        assert any("Invalid test type" in err for err in errors["types"])

    def test_mixed_valid_invalid_types_returns_error(self):
        """Test that mix of valid and invalid types returns errors for invalid ones."""
        errors = validate_test_classification(
            "unit",
            ["functional", "invalid_type", "security"]
        )
        assert "types" in errors
        assert any("Invalid test type: invalid_type" in err for err in errors["types"])

    def test_invalid_modifier_returns_error(self):
        """Test that invalid modifier returns error."""
        errors = validate_test_classification(
            "unit",
            ["functional"],
            ["invalid_modifier"]
        )
        assert "modifiers" in errors
        assert any("Invalid modifier" in err for err in errors["modifiers"])

    def test_mixed_valid_invalid_modifiers_returns_error(self):
        """Test that mix of valid and invalid modifiers returns errors for invalid ones."""
        errors = validate_test_classification(
            "unit",
            ["functional"],
            ["slow", "invalid_mod", "requires-db"]
        )
        assert "modifiers" in errors
        assert any("Invalid modifier: invalid_mod" in err for err in errors["modifiers"])

    def test_multiple_validation_errors(self):
        """Test that multiple validation errors are all returned."""
        errors = validate_test_classification(
            "invalid_level",
            ["invalid_type"],
            ["invalid_modifier"]
        )
        assert "level" in errors
        assert "types" in errors
        assert "modifiers" in errors

    def test_none_modifiers_is_valid(self):
        """Test that None modifiers is valid (modifiers are optional)."""
        errors = validate_test_classification("unit", ["functional"], None)
        assert errors == {}


@pytest.mark.unit
class TestGetTaxonomySummary:
    """Test get_taxonomy_summary() function."""

    def test_returns_string(self):
        """Test that get_taxonomy_summary returns a string."""
        summary = get_taxonomy_summary()
        assert isinstance(summary, str)

    def test_contains_title(self):
        """Test that summary contains title."""
        summary = get_taxonomy_summary()
        assert "Test Taxonomy Summary" in summary

    def test_contains_test_levels_section(self):
        """Test that summary contains test levels section."""
        summary = get_taxonomy_summary()
        assert "Test Levels" in summary
        assert "unit" in summary
        assert "integration" in summary

    def test_contains_test_types_section(self):
        """Test that summary contains test types section."""
        summary = get_taxonomy_summary()
        assert "Test Types" in summary
        assert "functional" in summary
        assert "security" in summary

    def test_contains_modifiers_section(self):
        """Test that summary contains modifiers section."""
        summary = get_taxonomy_summary()
        assert "Modifiers" in summary
        assert "slow" in summary
        assert "requires-db" in summary

    def test_contains_all_descriptions(self):
        """Test that summary contains all descriptions."""
        summary = get_taxonomy_summary()
        # Test level descriptions
        assert "Isolated components/functions" in summary
        assert "Component interactions" in summary
        # Test type descriptions
        assert "Business logic, features, functionality" in summary
        assert "Authentication, authorization, vulnerabilities" in summary
        # Modifier descriptions
        assert "Tests taking >10 seconds" in summary
        assert "Tests requiring database" in summary

    def test_not_empty(self):
        """Test that summary is not empty."""
        summary = get_taxonomy_summary()
        assert len(summary) > 0


@pytest.mark.unit
class TestTaxonomyEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_case_sensitive_level_validation(self):
        """Test that level validation is case-sensitive."""
        assert is_valid_test_level("unit") is True
        assert is_valid_test_level("Unit") is False
        assert is_valid_test_level("UNIT") is False

    def test_case_sensitive_type_validation(self):
        """Test that type validation is case-sensitive."""
        assert is_valid_test_type("functional") is True
        assert is_valid_test_type("Functional") is False
        assert is_valid_test_type("FUNCTIONAL") is False

    def test_case_sensitive_modifier_validation(self):
        """Test that modifier validation is case-sensitive."""
        assert is_valid_modifier("slow") is True
        assert is_valid_modifier("Slow") is False
        assert is_valid_modifier("SLOW") is False

    def test_whitespace_level_not_valid(self):
        """Test that whitespace-only level is not valid."""
        assert is_valid_test_level("   ") is False

    def test_whitespace_type_not_valid(self):
        """Test that whitespace-only type is not valid."""
        assert is_valid_test_type("   ") is False

    def test_whitespace_modifier_not_valid(self):
        """Test that whitespace-only modifier is not valid."""
        assert is_valid_modifier("   ") is False


@pytest.mark.unit
class TestTaxonomyUsageExamples:
    """Test real-world usage examples from documentation."""

    def test_example_unit_functional_test(self):
        """Test classification for unit functional test."""
        # Example: Testing a pure function
        errors = validate_test_classification("unit", ["functional"])
        assert errors == {}

    def test_example_integration_security_test(self):
        """Test classification for integration security test."""
        # Example: Testing authentication flow
        errors = validate_test_classification("integration", ["security"])
        assert errors == {}

    def test_example_system_performance_test(self):
        """Test classification for system performance test."""
        # Example: Load testing end-to-end workflow
        errors = validate_test_classification(
            "system",
            ["performance"],
            ["slow"]
        )
        assert errors == {}

    def test_example_acceptance_usability_test(self):
        """Test classification for acceptance usability test."""
        # Example: User acceptance testing for UI
        errors = validate_test_classification("acceptance", ["usability"])
        assert errors == {}

    def test_example_integration_functional_with_database(self):
        """Test classification for integration test requiring database."""
        # Example: Testing database repository layer
        errors = validate_test_classification(
            "integration",
            ["functional"],
            ["requires-db"]
        )
        assert errors == {}

    def test_example_system_functional_with_network(self):
        """Test classification for system test requiring network."""
        # Example: Testing external API integration
        errors = validate_test_classification(
            "system",
            ["functional"],
            ["requires-network", "slow"]
        )
        assert errors == {}

    def test_example_unit_functional_security(self):
        """Test classification for unit test covering both functional and security."""
        # Example: Testing input validation (functionality + security)
        errors = validate_test_classification(
            "unit",
            ["functional", "security"]
        )
        assert errors == {}
