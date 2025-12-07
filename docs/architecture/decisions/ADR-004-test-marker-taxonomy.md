# ADR-004: Test Classification Taxonomy (Framework-Agnostic)

**Date**: 2025-12-07
**Status**: Proposed
**Deciders**: Project Architect Agent, Engineering Team
**Related Features**: #1030 (Implement Test Classification Tags for Workflow-Aware Test Execution)

---

## Context

Tests are created by multiple agents (QA Engineer, Software Developer, DevOps Engineer) across different projects using different languages and testing frameworks (Python/pytest, JavaScript/Jest, Java/JUnit, etc.). Without consistent classification:
- Can't run targeted test suites (only security tests, only unit tests)
- Can't execute workflow-specific test levels (sprint execution runs unit+integration, release runs all)
- Can't generate categorized test reports
- Can't skip slow tests during development
- Can't enforce quality gates (all security tests must pass)

We need to choose a **framework-agnostic** test classification system that:
1. **Universal**: Works across all testing frameworks and languages
2. **Simple**: Easy for agents and humans to apply
3. **Expressive**: Supports workflow-aware test execution
4. **Flexible**: Adapts to each project's native test tooling

---

## Decision

**Use a universal test taxonomy with framework-specific implementation guidance.**

The framework defines a **language/framework-agnostic taxonomy**:
1. **Test Level** (exactly one): `unit`, `integration`, `system`, `acceptance`, `validation`
2. **Test Type** (at least one): `functional`, `security`, `performance`, `usability`
3. **Optional modifiers**: `slow`, `requires-db`, `requires-network`, `flaky`

**Agent templates** provide instructions for applying this taxonomy in each framework:
- **Python/pytest**: Use `@pytest.mark.{level}` and `@pytest.mark.{type}`
- **JavaScript/Jest**: Use comments or test description patterns
- **Java/JUnit**: Use `@Tag("{level}")` and `@Tag("{type}")`
- **Other frameworks**: Use framework-native tagging or comment conventions

Example (Python/pytest):
```python
@pytest.mark.unit
@pytest.mark.functional
def test_user_login():
    pass
```

Example (JavaScript/Jest):
```javascript
// Test: unit, functional
test('user login with valid credentials', () => {
  // ...
});
```

Example (Java/JUnit):
```java
@Test
@Tag("unit")
@Tag("functional")
public void testUserLogin() {
    // ...
}
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

### Option 3: Universal Taxonomy with Framework-Specific Guidance - CHOSEN
**Description**: Define universal taxonomy (test levels + types), provide framework-specific implementation guidance in agent templates.

**Pros**:
- **Framework-agnostic**: Works across Python, JavaScript, Java, Go, etc.
- **Language-neutral**: Same taxonomy regardless of tech stack
- **Flexible implementation**: Uses each framework's native tagging mechanism
- **No framework lock-in**: Projects use their own test tooling
- **Agent-friendly**: Clear instructions for applying taxonomy in any framework

**Cons**:
- No single enforcement mechanism (each framework validates differently)
- Requires framework detection during `trustable-ai init`
- Agent templates need framework-specific examples

**Example (Universal Taxonomy)**:
```yaml
test_levels: [unit, integration, system, acceptance, validation]
test_types: [functional, security, performance, usability]
modifiers: [slow, requires-db, requires-network, flaky]
```

**Example (Framework-Specific Application)**:
- Python: `@pytest.mark.unit` / `@pytest.mark.functional`
- JavaScript: `// Test: unit, functional`
- Java: `@Tag("unit")` / `@Tag("functional")`

**Why chosen**: Only approach that works across all languages/frameworks. Framework provides taxonomy and agent instructions, projects use native tooling. Aligns with framework's goal of being language-agnostic.

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

- **Framework-agnostic**: Works across Python, JavaScript, Java, Go, C#, etc.
- **Language-neutral**: Same taxonomy for all projects
- **No vendor lock-in**: Uses native test framework tooling
- **Agent-friendly**: Clear, universal instructions in agent templates
- **Workflow-aware**: Consistent test classification enables workflow-specific execution
- **Extensible**: Can add new test types/levels as needed

### Negative

- **Framework detection required**: `trustable-ai init` must detect project language/framework
- **No universal enforcement**: Each framework validates differently (pytest has markers, Jest doesn't)
- **Agent template complexity**: Templates need framework-specific examples
- **Validation variation**: Enforcement varies by framework capabilities

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

### Universal Taxonomy Registry

```python
# config/test_taxonomy.py
TEST_TAXONOMY = {
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
```

### Framework Detection & Config Generation

```python
# cli/commands/init.py
def detect_test_framework(project_path: Path) -> str:
    """Detect testing framework based on project files."""
    if (project_path / "pytest.ini").exists() or (project_path / "setup.py").exists():
        return "pytest"
    elif (project_path / "package.json").exists():
        return "jest"
    elif (project_path / "pom.xml").exists():
        return "junit"
    # ... more framework detection
    return "generic"

def generate_test_config(framework: str, project_path: Path):
    """Generate framework-specific test configuration."""
    if framework == "pytest":
        generate_pytest_ini(project_path)
    elif framework == "jest":
        update_jest_config(project_path)
    elif framework == "junit":
        create_junit_guidance(project_path)
    else:
        create_generic_test_guidance(project_path)
```

### Agent Template Updates (Framework-Agnostic)

```jinja2
{# agents/templates/tester.j2 #}
## Test Classification Standards

Apply consistent test classifications to all tests using your project's test framework:

### Required Classifications

Every test MUST have:
1. **Test Level** (exactly one): unit | integration | system | acceptance | validation
2. **Test Type** (at least one): functional | security | performance | usability

### Framework-Specific Syntax

{% if project.tech_stack.languages contains "Python" %}
**Python (pytest)**:
```python
@pytest.mark.unit
@pytest.mark.functional
def test_user_login():
    pass
```
{% endif %}

{% if project.tech_stack.languages contains "JavaScript" %}
**JavaScript (Jest)**:
```javascript
// Test: unit, functional
test('user login', () => {
  // ...
});
```
{% endif %}

{% if project.tech_stack.languages contains "Java" %}
**Java (JUnit)**:
```java
@Test
@Tag("unit")
@Tag("functional")
public void testUserLogin() {
}
```
{% endif %}

### Workflow-Aware Execution

- **Sprint Execution**: unit + integration + functional
- **Release Validation**: ALL test levels and types
```

### Workflow Test Execution Guidance

```jinja2
{# workflows/templates/sprint-execution.j2 #}
## Run Tests with Classification Filters

{% if project.tech_stack.languages contains "Python" %}
```bash
pytest -m "(unit or integration) and functional"
```
{% endif %}

{% if project.tech_stack.languages contains "JavaScript" %}
```bash
npm test -- --testNamePattern="unit|integration"
```
{% endif %}

{% if project.tech_stack.languages contains "Java" %}
```bash
mvn test -Dgroups="unit | integration"
```
{% endif %}
```

### No Framework CLI Command

**Important**: The framework does NOT provide `trustable-ai test` because:
- Test execution is project-specific
- Projects use their native test runners
- Framework only provides taxonomy and agent instructions

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
