# ADR-004: Test Marker Taxonomy

**Date**: 2025-12-07
**Status**: Proposed
**Deciders**: Project Architect Agent, Engineering Team
**Related Features**: #1030 (Implement Test Classification Tags for Workflow-Aware Test Execution)

---

## Context

Tests are created by multiple agents (QA Engineer, Software Developer, DevOps Engineer) without consistent classification. This makes it impossible to:
- Run targeted test suites (only security tests, only unit tests)
- Execute workflow-specific test levels (sprint execution runs unit+integration, release runs all)
- Generate categorized test reports
- Skip slow tests during development
- Enforce quality gates (all security tests must pass)

We need to choose a test classification system that is:
1. **Standard**: Uses widely-adopted tooling
2. **Simple**: Easy for agents and humans to apply
3. **Expressive**: Supports workflow-aware test execution
4. **Enforceable**: Can validate marker correctness

---

## Decision

**Use pytest.mark.* markers with a standardized registry.**

All tests will be tagged with:
1. **Test Level** (exactly one): `unit`, `integration`, `system`, `acceptance`, `validation`
2. **Test Type** (at least one): `functional`, `security`, `performance`, `usability`
3. **Optional modifiers**: `slow`, `requires_db`, `requires_network`, `flaky`

Example:
```python
@pytest.mark.unit
@pytest.mark.functional
def test_user_login():
    pass

@pytest.mark.integration
@pytest.mark.security
@pytest.mark.requires_db
def test_password_hashing():
    pass
```

---

## Options Considered

### Option 1: pytest built-in markers only
**Description**: Use only pytest's built-in markers (`skip`, `skipif`, `xfail`, `parametrize`).

**Pros**:
- No setup required
- Standard pytest

**Cons**:
- Insufficient for test classification
- No test level or type markers
- Can't express functional vs security tests

**Why not chosen**: Built-in markers don't support our classification needs.

---

### Option 2: Custom marker framework
**Description**: Build a custom test marker system separate from pytest.

**Pros**:
- Full control over syntax and semantics
- Can add domain-specific features

**Cons**:
- Reinventing the wheel
- Compatibility issues with pytest ecosystem
- Extra dependency
- Learning curve for developers

**Why not chosen**: Unnecessary complexity. pytest markers solve the problem without custom tooling.

---

### Option 3: pytest.mark.* with registry - CHOSEN
**Description**: Use pytest's marker system with a standardized marker registry defined in `pytest.ini`.

**Pros**:
- **Standard pytest mechanism** (no custom framework)
- **IDE support** (PyCharm, VS Code recognize markers)
- **Extensible taxonomy** (can add markers as needed)
- **Workflow integration** (`pytest -m "unit and functional"`)
- **Validation** (pytest warns about unknown markers)

**Cons**:
- Requires `pytest.ini` configuration
- All projects need marker definitions
- Marker enforcement requires custom plugin (optional)

**Example**:
```ini
# pytest.ini
[pytest]
markers =
    unit: Unit tests for isolated components
    integration: Integration tests for component interactions
    functional: Functional tests verifying business requirements
    security: Security tests (OWASP, auth, vulnerabilities)
```

**Why chosen**: Standard pytest mechanism with broad ecosystem support. Registry provides documentation and validation. Workflow presets simplify common cases.

---

### Option 4: Attribute-based (in docstrings)
**Description**: Embed test classification in docstrings, parse at runtime.

**Pros**:
- No marker syntax
- Human-readable

**Cons**:
- Non-standard approach
- Parsing complexity
- No IDE support
- Poor pytest integration

**Example**:
```python
def test_user_login():
    """
    Test: unit, functional
    Description: Test user login with valid credentials
    """
    pass
```

**Why not chosen**: Non-standard, poor tooling support, parsing overhead.

---

## Consequences

### Positive

- **Standard pytest compatibility**: Works with all pytest tooling
- **IDE support**: PyCharm, VS Code, etc. recognize and autocomplete markers
- **Workflow integration**: `pytest -m "unit and functional"` for targeted execution
- **Extensible taxonomy**: Can add markers (e.g., `smoke`, `regression`) as needed
- **Documentation**: Marker registry in `pytest.ini` documents each marker
- **Validation**: pytest warns about unknown markers (typo detection)

### Negative

- **Configuration required**: Every project needs `pytest.ini` with marker definitions
- **Enforcement complexity**: Requires custom validation for marker correctness
- **Learning curve**: Developers must learn marker taxonomy

### Risks

- **Risk**: Developers forget to apply markers → unmarked tests
  - **Mitigation**: Agent templates enforce markers, linter warns about unmarked tests

- **Risk**: Inconsistent marker application → test classification inaccurate
  - **Mitigation**: Agent templates standardize marker usage, validation tool checks consistency

- **Risk**: Marker taxonomy too complex → adoption friction
  - **Mitigation**: Start simple (2 dimensions: level + type), add modifiers as needed

- **Risk**: Legacy tests without markers → broken workflows
  - **Mitigation**: Escape hatch (`@pytest.mark.legacy`), gradual enforcement (new tests only)

---

## Implementation Notes

### Marker Registry

```python
# testing/markers.py
from enum import Enum

class TestLevel(Enum):
    """Test levels per testing pyramid."""
    UNIT = "unit"
    INTEGRATION = "integration"
    SYSTEM = "system"
    ACCEPTANCE = "acceptance"
    VALIDATION = "validation"

class TestType(Enum):
    """Test types for classification."""
    FUNCTIONAL = "functional"
    SECURITY = "security"
    PERFORMANCE = "performance"
    USABILITY = "usability"
```

### pytest.ini Configuration

```ini
[pytest]
markers =
    # Test Levels
    unit: Unit tests for isolated components
    integration: Integration tests for component interactions
    system: System-level end-to-end tests
    acceptance: User acceptance criteria tests
    validation: Release validation tests

    # Test Types
    functional: Functional tests verifying business requirements
    security: Security tests (OWASP, auth, vulnerabilities)
    performance: Performance and load tests
    usability: UI/UX and accessibility tests

    # Modifiers
    slow: Tests that take >10 seconds
    requires_db: Tests requiring database access
    requires_network: Tests requiring network access
    flaky: Tests with known intermittent failures
```

### Agent Template Updates

```jinja2
{# agents/templates/tester.j2 #}
## Test Marker Standards

Every test MUST have:
1. **Test Level** (exactly one): `@pytest.mark.unit`, `@pytest.mark.integration`, etc.
2. **Test Type** (at least one): `@pytest.mark.functional`, `@pytest.mark.security`, etc.

Example:
```python
@pytest.mark.unit
@pytest.mark.functional
def test_user_login_valid_credentials():
    """Test successful login with valid credentials."""
    pass
```
```

### Workflow Presets

```python
# testing/markers.py
WORKFLOW_MARKER_PRESETS = {
    "sprint-execution": {"unit", "integration", "functional"},
    "sprint-completion": {"unit", "integration", "functional", "acceptance"},
    "release-validation": {"unit", "integration", "system", "acceptance", "security", "validation"},
    "security-review": {"security"},
    "performance-test": {"performance"},
}
```

### CLI Integration

```bash
# Run tests for sprint execution (unit + integration + functional)
trustable-ai test --workflow=sprint-execution

# Run only security tests at unit level
trustable-ai test --type=security --level=unit

# Run all tests except slow ones
pytest -m "not slow"

# Run unit and integration functional tests
pytest -m "(unit or integration) and functional"
```

### Validation Tool

```python
# cli/commands/validate.py
def validate_test_markers(test_directory: str):
    """Validate all tests have required markers."""
    tests = discover_tests(test_directory)
    issues = []

    for test in tests:
        markers = get_markers(test)

        # Check for test level
        level_markers = markers & {"unit", "integration", "system", "acceptance", "validation"}
        if len(level_markers) == 0:
            issues.append(f"{test}: Missing test level marker")
        elif len(level_markers) > 1:
            issues.append(f"{test}: Multiple test level markers: {level_markers}")

        # Check for test type
        type_markers = markers & {"functional", "security", "performance", "usability"}
        if len(type_markers) == 0:
            issues.append(f"{test}: Missing test type marker")

    return issues
```

---

## Related Decisions

- Future: Test marker enforcement strictness (warning vs error)
- Future: Automated marker suggestion based on test name/path

---

## Approval

- [ ] Engineering Team Review
- [ ] QA Team Review (validate marker taxonomy covers all test types)
- [ ] Update agent templates with marker standards
- [ ] Add validation to CI/CD pipeline
