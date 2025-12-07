"""
Universal Test Taxonomy for Framework-Agnostic Test Classification.

Defines test classification dimensions (levels, types, modifiers) that work
across all testing frameworks and languages. Each project implements this
taxonomy using framework-native mechanisms (pytest markers, Jest comments,
JUnit tags, etc.).

This module solves the problem of **inconsistent test classification** across
multiple agents, languages, and frameworks. Without a universal taxonomy:
- Can't run targeted test suites (only security tests, only unit tests)
- Can't execute workflow-specific test levels (sprint execution runs unit+integration)
- Can't generate categorized test reports
- Can't enforce quality gates (all security tests must pass)

The taxonomy enables workflow-aware test execution by providing a common
classification language that agents and workflows understand, regardless
of the underlying test framework.

Architecture Decision:
    See docs/architecture/decisions/ADR-004-test-marker-taxonomy.md for
    detailed design rationale and framework-specific implementation guidance.

Example Usage:
    from config.test_taxonomy import TEST_TAXONOMY, get_test_level_description

    # Get all test levels
    levels = TEST_TAXONOMY["test_levels"]

    # Get description for a specific level
    description = get_test_level_description("unit")
    # Returns: "Isolated components/functions"

    # Validate a test level
    if is_valid_test_level("integration"):
        # Apply marker using framework-native mechanism
        pass

Framework-Specific Application:
    Python/pytest:
        @pytest.mark.unit
        @pytest.mark.functional
        def test_user_login():
            pass

    JavaScript/Jest:
        // Test: unit, functional
        test('user login', () => {
          // ...
        });

    Java/JUnit:
        @Test
        @Tag("unit")
        @Tag("functional")
        public void testUserLogin() {
            // ...
        }
"""

from typing import Dict, List, Optional


# Universal Test Taxonomy - Framework Agnostic
TEST_TAXONOMY: Dict[str, Dict[str, str]] = {
    "test_levels": {
        "unit": "Isolated components/functions",
        "integration": "Component interactions",
        "system": "End-to-end workflows",
        "acceptance": "User acceptance criteria",
        "validation": "Release validation"
    },
    "test_types": {
        "functional": "Business logic, features, functionality",
        "security": "Authentication, authorization, vulnerabilities",
        "performance": "Speed, throughput, resource usage",
        "usability": "UI/UX, accessibility, user workflows"
    },
    "modifiers": {
        "slow": "Tests taking >10 seconds",
        "requires-db": "Tests requiring database",
        "requires-network": "Tests requiring network access",
        "flaky": "Tests with known intermittent failures"
    }
}


def get_test_levels() -> List[str]:
    """
    Get all available test levels.

    Test levels form a hierarchy from most isolated (unit) to most comprehensive
    (validation). Every test must have exactly ONE test level.

    Returns:
        List of test level names (unit, integration, system, acceptance, validation)

    Example:
        >>> levels = get_test_levels()
        >>> print(levels)
        ['unit', 'integration', 'system', 'acceptance', 'validation']
    """
    return list(TEST_TAXONOMY["test_levels"].keys())


def get_test_types() -> List[str]:
    """
    Get all available test types.

    Test types categorize what aspect of the system is being tested.
    Every test must have at least ONE test type (can have multiple).

    Returns:
        List of test type names (functional, security, performance, usability)

    Example:
        >>> types = get_test_types()
        >>> print(types)
        ['functional', 'security', 'performance', 'usability']
    """
    return list(TEST_TAXONOMY["test_types"].keys())


def get_modifiers() -> List[str]:
    """
    Get all available test modifiers.

    Modifiers are optional tags that provide additional test metadata
    (execution characteristics, dependencies, known issues).

    Returns:
        List of modifier names (slow, requires-db, requires-network, flaky)

    Example:
        >>> modifiers = get_modifiers()
        >>> print(modifiers)
        ['slow', 'requires-db', 'requires-network', 'flaky']
    """
    return list(TEST_TAXONOMY["modifiers"].keys())


def get_test_level_description(level: str) -> Optional[str]:
    """
    Get the description for a test level.

    Args:
        level: Test level name (unit, integration, system, acceptance, validation)

    Returns:
        Description of the test level, or None if level not found

    Example:
        >>> desc = get_test_level_description("unit")
        >>> print(desc)
        'Isolated components/functions'

        >>> desc = get_test_level_description("integration")
        >>> print(desc)
        'Component interactions'
    """
    return TEST_TAXONOMY["test_levels"].get(level)


def get_test_type_description(test_type: str) -> Optional[str]:
    """
    Get the description for a test type.

    Args:
        test_type: Test type name (functional, security, performance, usability)

    Returns:
        Description of the test type, or None if type not found

    Example:
        >>> desc = get_test_type_description("functional")
        >>> print(desc)
        'Business logic, features, functionality'

        >>> desc = get_test_type_description("security")
        >>> print(desc)
        'Authentication, authorization, vulnerabilities'
    """
    return TEST_TAXONOMY["test_types"].get(test_type)


def get_modifier_description(modifier: str) -> Optional[str]:
    """
    Get the description for a modifier.

    Args:
        modifier: Modifier name (slow, requires-db, requires-network, flaky)

    Returns:
        Description of the modifier, or None if modifier not found

    Example:
        >>> desc = get_modifier_description("slow")
        >>> print(desc)
        'Tests taking >10 seconds'

        >>> desc = get_modifier_description("requires-db")
        >>> print(desc)
        'Tests requiring database'
    """
    return TEST_TAXONOMY["modifiers"].get(modifier)


def is_valid_test_level(level: str) -> bool:
    """
    Check if a test level is valid.

    Args:
        level: Test level name to validate

    Returns:
        True if level exists in taxonomy, False otherwise

    Example:
        >>> is_valid_test_level("unit")
        True

        >>> is_valid_test_level("invalid")
        False
    """
    return level in TEST_TAXONOMY["test_levels"]


def is_valid_test_type(test_type: str) -> bool:
    """
    Check if a test type is valid.

    Args:
        test_type: Test type name to validate

    Returns:
        True if type exists in taxonomy, False otherwise

    Example:
        >>> is_valid_test_type("functional")
        True

        >>> is_valid_test_type("invalid")
        False
    """
    return test_type in TEST_TAXONOMY["test_types"]


def is_valid_modifier(modifier: str) -> bool:
    """
    Check if a modifier is valid.

    Args:
        modifier: Modifier name to validate

    Returns:
        True if modifier exists in taxonomy, False otherwise

    Example:
        >>> is_valid_modifier("slow")
        True

        >>> is_valid_modifier("invalid")
        False
    """
    return modifier in TEST_TAXONOMY["modifiers"]


def validate_test_classification(
    level: str,
    types: List[str],
    modifiers: Optional[List[str]] = None
) -> Dict[str, List[str]]:
    """
    Validate a complete test classification.

    Tests must have:
    1. Exactly ONE test level (unit, integration, system, acceptance, validation)
    2. At least ONE test type (functional, security, performance, usability)
    3. Zero or more optional modifiers (slow, requires-db, requires-network, flaky)

    Args:
        level: Test level (exactly one required)
        types: Test types (at least one required)
        modifiers: Optional modifiers

    Returns:
        Dictionary with validation errors (empty dict if valid)

    Raises:
        ValueError: If validation fails

    Example:
        >>> # Valid classification
        >>> errors = validate_test_classification("unit", ["functional"])
        >>> print(errors)
        {}

        >>> # Invalid level
        >>> errors = validate_test_classification("invalid", ["functional"])
        >>> print(errors)
        {'level': ['Invalid test level: invalid']}

        >>> # No types provided
        >>> errors = validate_test_classification("unit", [])
        >>> print(errors)
        {'types': ['At least one test type required']}
    """
    errors: Dict[str, List[str]] = {}

    # Validate test level
    if not level:
        errors.setdefault("level", []).append("Test level is required")
    elif not is_valid_test_level(level):
        errors.setdefault("level", []).append(f"Invalid test level: {level}")

    # Validate test types
    if not types:
        errors.setdefault("types", []).append("At least one test type required")
    else:
        invalid_types = [t for t in types if not is_valid_test_type(t)]
        if invalid_types:
            errors.setdefault("types", []).extend(
                [f"Invalid test type: {t}" for t in invalid_types]
            )

    # Validate modifiers (optional)
    if modifiers:
        invalid_modifiers = [m for m in modifiers if not is_valid_modifier(m)]
        if invalid_modifiers:
            errors.setdefault("modifiers", []).extend(
                [f"Invalid modifier: {m}" for m in invalid_modifiers]
            )

    return errors


def get_taxonomy_summary() -> str:
    """
    Get a formatted summary of the entire test taxonomy.

    Returns:
        Human-readable string describing all taxonomy dimensions

    Example:
        >>> summary = get_taxonomy_summary()
        >>> print(summary)
        Test Taxonomy Summary
        =====================

        Test Levels (exactly one required):
          - unit: Isolated components/functions
          - integration: Component interactions
          ...
    """
    lines = ["Test Taxonomy Summary", "=" * 21, ""]

    lines.append("Test Levels (exactly one required):")
    for level, description in TEST_TAXONOMY["test_levels"].items():
        lines.append(f"  - {level}: {description}")

    lines.append("")
    lines.append("Test Types (at least one required):")
    for test_type, description in TEST_TAXONOMY["test_types"].items():
        lines.append(f"  - {test_type}: {description}")

    lines.append("")
    lines.append("Modifiers (optional):")
    for modifier, description in TEST_TAXONOMY["modifiers"].items():
        lines.append(f"  - {modifier}: {description}")

    return "\n".join(lines)


# Example usage for documentation
if __name__ == "__main__":
    # Print taxonomy summary
    print(get_taxonomy_summary())
    print("\n")

    # Example validation
    print("Example: Valid classification")
    errors = validate_test_classification("unit", ["functional", "security"])
    print(f"Errors: {errors if errors else 'None'}")
    print("\n")

    print("Example: Invalid classification")
    errors = validate_test_classification("invalid_level", ["functional", "invalid_type"], ["invalid_mod"])
    print(f"Errors: {errors}")
