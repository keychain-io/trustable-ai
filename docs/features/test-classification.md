# Framework-Agnostic Test Classification

## Overview

### What is Test Classification?

Test classification is a system for tagging tests with **level** (how isolated) and **type** (what aspect) metadata. This enables **workflow-aware test execution** where different workflows run different test subsets based on risk and phase in the SDLC.

**Example**: Sprint execution workflow runs only `unit` + `integration` + `functional` tests for fast feedback. Release validation workflow runs ALL test levels and types to verify production readiness.

### Why Framework-Agnostic?

The Trustable AI framework is language-agnostic - teams use Python, JavaScript, Java, Go, etc. Each language has different testing frameworks (pytest, Jest, JUnit, Go testing).

**Problem**: If the framework mandates pytest markers, JavaScript projects can't participate. If it requires Jest patterns, Python projects are excluded.

**Solution**: Define a **universal taxonomy** (test levels + types) that works across all frameworks. Each framework implements the taxonomy using its native mechanisms:

- **Python/pytest**: `@pytest.mark.unit` + `@pytest.mark.functional`
- **JavaScript/Jest**: `// Test: unit, functional` (comments)
- **Java/JUnit**: `@Tag("unit")` + `@Tag("functional")`
- **Go**: Build tags or test name conventions
- **Generic**: Comment-based fallback for any framework

### What Problems Does It Solve?

**Without test classification:**

1. **Can't run targeted test suites**
   - Need to run security tests only for audit? No way to filter.
   - Want to skip slow tests during development? Must maintain separate directories.

2. **Can't execute workflow-specific test levels**
   - Sprint execution should run unit + integration (fast feedback)
   - Release validation should run ALL tests (comprehensive check)
   - No way to express this requirement to agents or CI/CD

3. **Can't generate categorized test reports**
   - How many security tests exist? Unknown.
   - What's the coverage of performance tests? Can't measure.

4. **Can't enforce quality gates**
   - "All security tests must pass" - how do you select them?
   - "No flaky tests in CI" - which tests are flaky?

**With test classification:**

```bash
# Run only security tests
pytest -m security

# Run fast tests for development (exclude slow)
pytest -m "not slow"

# Sprint execution: unit + integration + functional
pytest -m "(unit or integration) and functional"

# Release validation: all tests
pytest
```

Every test is tagged with its **level** (unit/integration/system/acceptance/validation) and **type** (functional/security/performance/usability), enabling precise test selection.

---

## Universal Test Taxonomy

The framework defines three classification dimensions:

### Test Levels (exactly one required)

Test levels describe **how isolated** the test is - from single functions to full system workflows.

| Level | Description | Example | When to Use |
|-------|-------------|---------|-------------|
| `unit` | Isolated components/functions | Test a single function with mocked dependencies | Testing business logic, utility functions, pure functions |
| `integration` | Component interactions | Test database queries, API client, service integration | Testing component boundaries, external service adapters |
| `system` | End-to-end workflows | Test complete user flow from UI to database | Testing user journeys, critical paths, workflow orchestration |
| `acceptance` | User acceptance criteria | Test acceptance criteria from user story | Validating requirements, stakeholder acceptance |
| `validation` | Release validation | Test production deployment, smoke tests | Pre-release checks, deployment validation |

**Every test MUST have exactly ONE test level.**

### Test Types (at least one required)

Test types describe **what aspect** of the system is being tested - orthogonal to isolation level.

| Type | Description | Example | When to Use |
|------|-------------|---------|-------------|
| `functional` | Business logic, features, functionality | Login validates credentials, shopping cart calculates total | Testing feature behavior, business rules, workflows |
| `security` | Authentication, authorization, vulnerabilities | Password hashing, SQL injection prevention, RBAC | Testing security controls, vulnerability prevention |
| `performance` | Speed, throughput, resource usage | API responds in <200ms, handles 1000 req/s | Testing scalability, latency, resource limits |
| `usability` | UI/UX, accessibility, user workflows | Screen reader support, keyboard navigation | Testing user experience, accessibility compliance |

**Every test MUST have at least ONE test type** (can have multiple - e.g., a test can be both `functional` and `security`).

### Modifiers (optional)

Modifiers provide additional test metadata about execution characteristics or known issues.

| Modifier | Description | When to Use |
|----------|-------------|-------------|
| `slow` | Tests taking >10 seconds | Long-running integration tests, performance benchmarks |
| `requires-db` | Tests requiring database | Tests that need database connection (not mocked) |
| `requires-network` | Tests requiring network access | Tests calling external APIs, downloading resources |
| `flaky` | Tests with known intermittent failures | Tests with timing issues, race conditions (use sparingly - fix instead!) |

**Modifiers are optional.** Use them to help with test execution planning (e.g., skip `slow` tests during development, ensure `requires-db` tests have database available).

---

## Framework-Specific Implementation

### Python (pytest)

#### How to Apply Classifications

Use `@pytest.mark.<classification>` decorators:

```python
import pytest

@pytest.mark.unit
@pytest.mark.functional
def test_calculate_total():
    """Test shopping cart total calculation."""
    cart = ShoppingCart()
    cart.add_item(price=10.00, quantity=2)
    assert cart.calculate_total() == 20.00

@pytest.mark.integration
@pytest.mark.functional
@pytest.mark.requires_db
def test_save_order_to_database():
    """Test order persistence to database."""
    order = Order(customer_id=123, total=50.00)
    order.save()

    # Verify saved to database
    saved_order = Order.get(order.id)
    assert saved_order.total == 50.00

@pytest.mark.system
@pytest.mark.security
def test_end_to_end_authentication():
    """Test complete authentication flow."""
    # Simulate user login
    response = client.post('/login', json={
        'username': 'test@example.com',
        'password': 'SecureP@ssw0rd'
    })

    assert response.status_code == 200
    assert 'access_token' in response.json()

    # Verify token works for protected endpoint
    token = response.json()['access_token']
    profile_response = client.get(
        '/profile',
        headers={'Authorization': f'Bearer {token}'}
    )
    assert profile_response.status_code == 200

@pytest.mark.integration
@pytest.mark.performance
@pytest.mark.slow
def test_api_response_time():
    """Test API response time under load."""
    import time

    start = time.time()
    responses = []
    for _ in range(100):
        response = client.get('/api/products')
        responses.append(response)
    duration = time.time() - start

    # All requests successful
    assert all(r.status_code == 200 for r in responses)

    # Average response time < 200ms
    avg_time = duration / 100
    assert avg_time < 0.2
```

#### How to Run Tests by Classification

```bash
# Run unit tests only
pytest -m unit

# Run integration tests only
pytest -m integration

# Run functional tests (any level)
pytest -m functional

# Run security tests (any level)
pytest -m security

# Sprint execution: unit OR integration, AND functional
pytest -m "(unit or integration) and functional"

# Exclude slow tests
pytest -m "not slow"

# Run tests that don't require database
pytest -m "not requires_db"

# Run only unit functional tests (most common during development)
pytest -m "unit and functional"

# Release validation: all tests (no marker filter)
pytest
```

#### Configuration (pytest.ini)

Register custom markers in `pytest.ini`:

```ini
[tool:pytest]
markers =
    # Test Levels (exactly one required)
    unit: Isolated components/functions
    integration: Component interactions
    system: End-to-end workflows
    acceptance: User acceptance criteria
    validation: Release validation

    # Test Types (at least one required)
    functional: Business logic, features, functionality
    security: Authentication, authorization, vulnerabilities
    performance: Speed, throughput, resource usage
    usability: UI/UX, accessibility, user workflows

    # Modifiers (optional)
    slow: Tests taking >10 seconds
    requires_db: Tests requiring database
    requires_network: Tests requiring network access
    flaky: Tests with known intermittent failures
```

#### Validation

Enforce marker usage with pytest plugin:

```python
# conftest.py
def pytest_collection_modifyitems(items):
    """Validate test classifications."""
    test_levels = {'unit', 'integration', 'system', 'acceptance', 'validation'}
    test_types = {'functional', 'security', 'performance', 'usability'}

    for item in items:
        markers = {mark.name for mark in item.iter_markers()}

        # Check for exactly one test level
        level_markers = markers & test_levels
        if len(level_markers) == 0:
            raise ValueError(
                f"Test {item.nodeid} missing test level marker "
                f"(must have one of: {test_levels})"
            )
        elif len(level_markers) > 1:
            raise ValueError(
                f"Test {item.nodeid} has multiple test level markers "
                f"({level_markers}). Only one allowed."
            )

        # Check for at least one test type
        type_markers = markers & test_types
        if len(type_markers) == 0:
            raise ValueError(
                f"Test {item.nodeid} missing test type marker "
                f"(must have at least one of: {test_types})"
            )
```

---

### JavaScript (Jest)

#### How to Apply Classifications

Jest doesn't have native marker support like pytest. Use **comment-based classification** at the test level:

```javascript
// Test: unit, functional
test('calculate shopping cart total', () => {
  const cart = new ShoppingCart();
  cart.addItem({ price: 10.00, quantity: 2 });
  expect(cart.calculateTotal()).toBe(20.00);
});

// Test: integration, functional, requires-db
test('save order to database', async () => {
  const order = new Order({ customerId: 123, total: 50.00 });
  await order.save();

  const savedOrder = await Order.findById(order.id);
  expect(savedOrder.total).toBe(50.00);
});

// Test: system, security
test('end-to-end authentication flow', async () => {
  // Login
  const loginResponse = await request(app)
    .post('/login')
    .send({
      username: 'test@example.com',
      password: 'SecureP@ssw0rd'
    });

  expect(loginResponse.status).toBe(200);
  expect(loginResponse.body.access_token).toBeDefined();

  // Use token
  const token = loginResponse.body.access_token;
  const profileResponse = await request(app)
    .get('/profile')
    .set('Authorization', `Bearer ${token}`);

  expect(profileResponse.status).toBe(200);
});

// Test: integration, performance, slow
test('API response time under load', async () => {
  const startTime = Date.now();
  const requests = [];

  for (let i = 0; i < 100; i++) {
    requests.push(request(app).get('/api/products'));
  }

  const responses = await Promise.all(requests);
  const duration = Date.now() - startTime;

  responses.forEach(response => {
    expect(response.status).toBe(200);
  });

  const avgTime = duration / 100;
  expect(avgTime).toBeLessThan(200);
}, 30000); // 30s timeout for slow test
```

#### How to Run Tests by Classification

Use custom test runner script or `--testNamePattern`:

```bash
# Run tests matching pattern (basic filtering)
npm test -- --testNamePattern="unit"

# Custom test runner (recommended)
# Create scripts/run-tests.js:
```

```javascript
// scripts/run-tests.js
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

// Parse test files and extract classifications from comments
function parseTestClassifications(testDir) {
  const classifications = {};

  function parseFile(filePath) {
    const content = fs.readFileSync(filePath, 'utf8');
    const testPattern = /\/\/ Test: ([^\n]+)\s+test\(['"]([^'"]+)/g;

    let match;
    while ((match = testPattern.exec(content)) !== null) {
      const [_, tags, testName] = match;
      const testTags = tags.split(',').map(t => t.trim());
      classifications[testName] = testTags;
    }
  }

  // Walk test directory
  function walkDir(dir) {
    const files = fs.readdirSync(dir);
    files.forEach(file => {
      const filePath = path.join(dir, file);
      if (fs.statSync(filePath).isDirectory()) {
        walkDir(filePath);
      } else if (file.endsWith('.test.js') || file.endsWith('.spec.js')) {
        parseFile(filePath);
      }
    });
  }

  walkDir(testDir);
  return classifications;
}

// Filter tests by classification
function filterTests(classifications, filters) {
  const matching = [];

  for (const [testName, tags] of Object.entries(classifications)) {
    const tagSet = new Set(tags);

    // Check if test matches all filters
    if (filters.every(filter => tagSet.has(filter))) {
      matching.push(testName);
    }
  }

  return matching;
}

// Parse command line arguments
const args = process.argv.slice(2);
const filters = args.filter(arg => !arg.startsWith('-'));

// Get classifications
const testDir = path.join(__dirname, '../tests');
const classifications = parseTestClassifications(testDir);

// Filter tests
const matchingTests = filterTests(classifications, filters);

if (matchingTests.length === 0) {
  console.log(`No tests match filters: ${filters.join(', ')}`);
  process.exit(0);
}

// Build test name pattern
const pattern = matchingTests.join('|');

// Run Jest with filtered tests
const jestArgs = ['--testNamePattern', pattern];
const jest = spawn('jest', jestArgs, { stdio: 'inherit' });

jest.on('close', code => {
  process.exit(code);
});
```

```bash
# Usage
node scripts/run-tests.js unit functional     # Unit functional tests
node scripts/run-tests.js security            # All security tests
node scripts/run-tests.js integration         # All integration tests
```

#### Alternative: Test Suite Organization

Organize tests by classification using `describe` blocks:

```javascript
describe('Unit - Functional', () => {
  test('calculate shopping cart total', () => {
    // Test implementation
  });

  test('validate email format', () => {
    // Test implementation
  });
});

describe('Integration - Security', () => {
  test('SQL injection prevention', async () => {
    // Test implementation
  });

  test('password hashing', async () => {
    // Test implementation
  });
});
```

Then run specific suites:

```bash
npm test -- --testPathPattern="unit-functional"
npm test -- --testPathPattern="integration-security"
```

---

### Java (JUnit 5)

#### How to Apply Classifications

Use `@Tag` annotations:

```java
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

@Tag("unit")
@Tag("functional")
class ShoppingCartTest {

    @Test
    void testCalculateTotal() {
        ShoppingCart cart = new ShoppingCart();
        cart.addItem(new Item(10.00, 2));

        assertEquals(20.00, cart.calculateTotal());
    }
}

@Tag("integration")
@Tag("functional")
@Tag("requires-db")
class OrderRepositoryTest {

    @Test
    void testSaveOrder() {
        Order order = new Order(123L, 50.00);
        orderRepository.save(order);

        Order savedOrder = orderRepository.findById(order.getId());
        assertEquals(50.00, savedOrder.getTotal());
    }
}

@Tag("system")
@Tag("security")
class AuthenticationE2ETest {

    @Test
    void testEndToEndAuthentication() throws Exception {
        // Login
        String loginResponse = mockMvc.perform(
            post("/login")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"username\":\"test@example.com\",\"password\":\"SecureP@ssw0rd\"}")
        )
        .andExpect(status().isOk())
        .andReturn()
        .getResponse()
        .getContentAsString();

        String token = extractToken(loginResponse);

        // Use token
        mockMvc.perform(
            get("/profile")
                .header("Authorization", "Bearer " + token)
        )
        .andExpect(status().isOk());
    }
}

@Tag("integration")
@Tag("performance")
@Tag("slow")
class ApiPerformanceTest {

    @Test
    void testApiResponseTime() throws Exception {
        long startTime = System.currentTimeMillis();

        for (int i = 0; i < 100; i++) {
            mockMvc.perform(get("/api/products"))
                .andExpect(status().isOk());
        }

        long duration = System.currentTimeMillis() - startTime;
        double avgTime = duration / 100.0;

        assertTrue(avgTime < 200, "Average response time should be < 200ms");
    }
}
```

#### How to Run Tests by Classification

**Maven:**

```bash
# Run unit tests
mvn test -Dgroups="unit"

# Run integration tests
mvn test -Dgroups="integration"

# Run functional tests (any level)
mvn test -Dgroups="functional"

# Run security tests
mvn test -Dgroups="security"

# Sprint execution: unit OR integration, AND functional
mvn test -Dgroups="(unit | integration) & functional"

# Exclude slow tests
mvn test -DexcludedGroups="slow"

# Release validation: all tests
mvn test
```

**Gradle:**

```bash
# Run unit tests
./gradlew test --tests "*" -Dgroups="unit"

# Run integration tests
./gradlew test --tests "*" -Dgroups="integration"

# Sprint execution
./gradlew test --tests "*" -Dgroups="(unit | integration) & functional"

# Exclude slow tests
./gradlew test -DexcludedGroups="slow"
```

#### Configuration

**Maven (pom.xml):**

```xml
<build>
  <plugins>
    <plugin>
      <groupId>org.apache.maven.plugins</groupId>
      <artifactId>maven-surefire-plugin</artifactId>
      <version>3.0.0</version>
      <configuration>
        <!-- Configure test groups -->
        <groups>${test.groups}</groups>
        <excludedGroups>${test.excludedGroups}</excludedGroups>
      </configuration>
    </plugin>
  </plugins>
</build>

<properties>
  <!-- Default: run all non-slow tests -->
  <test.groups></test.groups>
  <test.excludedGroups>slow</test.excludedGroups>
</properties>
```

**Gradle (build.gradle):**

```groovy
test {
    useJUnitPlatform {
        // Include/exclude tags
        if (project.hasProperty('groups')) {
            includeTags project.property('groups')
        }
        if (project.hasProperty('excludedGroups')) {
            excludeTags project.property('excludedGroups')
        }
    }
}
```

---

### Go (Go Testing)

#### How to Apply Classifications

Go testing doesn't have native tag support. Use **build tags** or **test naming conventions**:

**Option 1: Build Tags (Recommended)**

```go
// +build unit,functional

package cart_test

import "testing"

func TestCalculateTotal(t *testing.T) {
    cart := NewShoppingCart()
    cart.AddItem(10.00, 2)

    if total := cart.CalculateTotal(); total != 20.00 {
        t.Errorf("Expected 20.00, got %f", total)
    }
}
```

```go
// +build integration,functional,requires_db

package repository_test

import "testing"

func TestSaveOrder(t *testing.T) {
    order := &Order{CustomerID: 123, Total: 50.00}
    if err := orderRepo.Save(order); err != nil {
        t.Fatalf("Failed to save order: %v", err)
    }

    savedOrder, err := orderRepo.FindByID(order.ID)
    if err != nil {
        t.Fatalf("Failed to find order: %v", err)
    }

    if savedOrder.Total != 50.00 {
        t.Errorf("Expected 50.00, got %f", savedOrder.Total)
    }
}
```

**Option 2: Test Naming Convention**

```go
package cart_test

import "testing"

// Unit_Functional_CalculateTotal tests cart total calculation
func TestUnit_Functional_CalculateTotal(t *testing.T) {
    cart := NewShoppingCart()
    cart.AddItem(10.00, 2)

    if total := cart.CalculateTotal(); total != 20.00 {
        t.Errorf("Expected 20.00, got %f", total)
    }
}

// Integration_Functional_RequiresDB_SaveOrder tests order persistence
func TestIntegration_Functional_RequiresDB_SaveOrder(t *testing.T) {
    order := &Order{CustomerID: 123, Total: 50.00}
    if err := orderRepo.Save(order); err != nil {
        t.Fatalf("Failed to save order: %v", err)
    }

    savedOrder, err := orderRepo.FindByID(order.ID)
    if err != nil {
        t.Fatalf("Failed to find order: %v", err)
    }

    if savedOrder.Total != 50.00 {
        t.Errorf("Expected 50.00, got %f", savedOrder.Total)
    }
}
```

#### How to Run Tests by Classification

**Build Tags:**

```bash
# Run unit tests
go test -tags=unit ./...

# Run integration tests
go test -tags=integration ./...

# Run functional tests (any level)
go test -tags=functional ./...

# Run security tests
go test -tags=security ./...

# Run unit functional tests (comma = AND)
go test -tags=unit,functional ./...

# Exclude slow tests (use separate tags file)
go test -tags=!slow ./...
```

**Test Naming Convention:**

```bash
# Run unit tests
go test -run Unit ./...

# Run integration tests
go test -run Integration ./...

# Run functional tests
go test -run Functional ./...

# Run unit functional tests
go test -run "Unit.*Functional" ./...

# Exclude slow tests
go test -run "^((?!Slow).)*$" ./...
```

#### Configuration

Create build tag combinations in separate files:

```go
// test_tags_unit.go
// +build unit

package tests

// Empty file to enable unit tag
```

```go
// test_tags_integration.go
// +build integration

package tests

// Empty file to enable integration tag
```

---

### Generic (Fallback for Any Framework)

For frameworks without native tagging support, use **comment-based classification**:

```python
# Ruby (RSpec)
# Test: unit, functional
it "calculates shopping cart total" do
  cart = ShoppingCart.new
  cart.add_item(price: 10.00, quantity: 2)
  expect(cart.calculate_total).to eq(20.00)
end

# Test: integration, functional, requires-db
it "saves order to database" do
  order = Order.new(customer_id: 123, total: 50.00)
  order.save

  saved_order = Order.find(order.id)
  expect(saved_order.total).to eq(50.00)
end
```

```csharp
// C# (NUnit)
// Test: unit, functional
[Test]
public void TestCalculateTotal()
{
    var cart = new ShoppingCart();
    cart.AddItem(10.00, 2);
    Assert.AreEqual(20.00, cart.CalculateTotal());
}

// Test: integration, functional, requires-db
[Test]
public void TestSaveOrder()
{
    var order = new Order { CustomerId = 123, Total = 50.00 };
    orderRepository.Save(order);

    var savedOrder = orderRepository.FindById(order.Id);
    Assert.AreEqual(50.00, savedOrder.Total);
}
```

Parse comments with custom test runner or CI/CD script to filter tests.

---

## Workflow-Aware Test Execution

Different SDLC workflows require different test subsets:

### Sprint Execution Workflow

**Goal**: Fast feedback during development

**Test Selection**: Unit + Integration + Functional (skip slow, skip validation)

**Rationale**: Developers need quick feedback on code changes. Run tests that execute fast (<5 minutes) and catch most bugs (80/20 rule).

```bash
# Python/pytest
pytest -m "(unit or integration) and functional and not slow"

# JavaScript/Jest
npm test -- --testNamePattern="unit|integration"

# Java/Maven
mvn test -Dgroups="(unit | integration) & functional" -DexcludedGroups="slow"

# Go
go test -tags=unit,functional ./...
go test -tags=integration,functional ./...
```

### Release Validation Workflow

**Goal**: Comprehensive pre-release verification

**Test Selection**: ALL test levels and types

**Rationale**: Before releasing to production, run every test to catch edge cases, performance regressions, security issues.

```bash
# Python/pytest
pytest  # No filters = run all

# JavaScript/Jest
npm test

# Java/Maven
mvn test  # No -Dgroups = run all

# Go
go test ./...
```

### Security Audit Workflow

**Goal**: Verify security controls

**Test Selection**: All security tests (any level)

**Rationale**: During security audits or compliance reviews, demonstrate security test coverage.

```bash
# Python/pytest
pytest -m security

# JavaScript/Jest
node scripts/run-tests.js security

# Java/Maven
mvn test -Dgroups="security"

# Go
go test -tags=security ./...
```

### Performance Baseline Workflow

**Goal**: Establish performance benchmarks

**Test Selection**: All performance tests

**Rationale**: Before deploying changes, ensure performance hasn't regressed.

```bash
# Python/pytest
pytest -m performance

# JavaScript/Jest
node scripts/run-tests.js performance

# Java/Maven
mvn test -Dgroups="performance"

# Go
go test -tags=performance -bench=. ./...
```

### Development Workflow (Fast Iteration)

**Goal**: Ultra-fast feedback during TDD

**Test Selection**: Unit + Functional (exclude slow, exclude requires-db, exclude requires-network)

**Rationale**: Developers practicing TDD need sub-second test runs. Run only fast, isolated tests.

```bash
# Python/pytest
pytest -m "unit and functional and not slow and not requires_db and not requires_network"

# JavaScript/Jest
npm test -- --testNamePattern="unit" --testPathPattern="functional"

# Java/Maven
mvn test -Dgroups="unit & functional" -DexcludedGroups="slow,requires-db,requires-network"

# Go
go test -tags=unit,functional -short ./...
```

### CI/CD Pipeline Integration

Configure different test suites for different CI stages:

```yaml
# .github/workflows/ci.yml (GitHub Actions)
name: CI

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run unit tests
        run: pytest -m "unit and functional"

  integration-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    steps:
      - uses: actions/checkout@v2
      - name: Setup database
        run: docker-compose up -d postgres
      - name: Run integration tests
        run: pytest -m "integration"

  security-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    steps:
      - uses: actions/checkout@v2
      - name: Run security tests
        run: pytest -m "security"

  release-validation:
    runs-on: ubuntu-latest
    needs: [unit-tests, integration-tests, security-tests]
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v2
      - name: Run all tests
        run: pytest
```

---

## Best Practices

### 1. Always Classify Tests with Level + Type

**DO:**

```python
@pytest.mark.unit
@pytest.mark.functional
def test_calculate_total():
    pass
```

**DON'T:**

```python
# Missing classification - which workflow should run this?
def test_calculate_total():
    pass
```

**Rationale**: Tests without classification can't be selected by workflows. They run in all workflows (slow) or none (untested).

### 2. Use Modifiers for Slow/Flaky/Resource-Dependent Tests

**DO:**

```python
@pytest.mark.integration
@pytest.mark.performance
@pytest.mark.slow
@pytest.mark.requires_db
def test_bulk_import_performance():
    pass
```

**DON'T:**

```python
@pytest.mark.integration
@pytest.mark.performance
# Missing slow + requires_db modifiers
# Test runs in fast dev workflow, slows down TDD cycle
def test_bulk_import_performance():
    pass
```

**Rationale**: Modifiers let developers skip slow/resource-dependent tests during fast iteration, then include them in CI/CD.

### 3. Keep Test Classifications Accurate

**DO:** Update classifications when test scope changes

```python
# Originally unit test
@pytest.mark.unit
@pytest.mark.functional
def test_user_login():
    # Was mocked, now hits real database
    user = User.query.filter_by(username='test').first()
    assert user.authenticate('password')

# Update to integration + requires_db
@pytest.mark.integration  # Changed from unit
@pytest.mark.functional
@pytest.mark.requires_db  # Added modifier
def test_user_login():
    user = User.query.filter_by(username='test').first()
    assert user.authenticate('password')
```

**DON'T:** Leave stale classifications

**Rationale**: Inaccurate classifications cause tests to run in wrong workflows (unit tests hitting databases, integration tests in fast dev suite).

### 4. Update Classifications When Test Scope Changes

**Example**: Test starts as unit test with mocks, evolves to integration test

```python
# Version 1: Unit test (mocked)
@pytest.mark.unit
@pytest.mark.functional
def test_send_email():
    with mock.patch('email.client.send') as mock_send:
        send_welcome_email('user@example.com')
        mock_send.assert_called_once()

# Version 2: Integration test (real email service)
@pytest.mark.integration  # Changed from unit
@pytest.mark.functional
@pytest.mark.requires_network  # Added modifier
def test_send_email():
    # Now sends real email to test SMTP server
    send_welcome_email('user@example.com')
    # Verify email in test inbox
    assert check_test_inbox('user@example.com')
```

**Action**: Update markers when test changes from mocked to real dependencies.

### 5. Prefer Fixing Flaky Tests Over Marking Them

**DO:**

```python
# Fix the race condition
@pytest.mark.integration
@pytest.mark.functional
def test_concurrent_updates():
    # Add proper locking/synchronization
    with db.transaction():
        account.withdraw(50)
```

**DON'T:**

```python
# Just mark as flaky and ignore
@pytest.mark.integration
@pytest.mark.functional
@pytest.mark.flaky  # AVOID - fix the test instead!
def test_concurrent_updates():
    # Race condition exists
    account.withdraw(50)
```

**Rationale**: Flaky tests erode confidence. Fix timing issues, race conditions, improper cleanup. Use `flaky` marker only as temporary measure while debugging.

### 6. Use Multiple Test Types When Appropriate

**DO:**

```python
@pytest.mark.integration
@pytest.mark.functional
@pytest.mark.security  # Test is both functional AND security
def test_password_reset_flow():
    """Test password reset (functional) and token security (security)."""
    token = request_password_reset('user@example.com')

    # Functional: can reset password
    response = reset_password(token, 'NewP@ssw0rd')
    assert response.status_code == 200

    # Security: token expires
    time.sleep(EXPIRATION_TIME + 1)
    expired_response = reset_password(token, 'AnotherP@ssw0rd')
    assert expired_response.status_code == 401
```

**Rationale**: Some tests validate multiple aspects. Classify with all applicable types so test runs in both functional and security workflows.

### 7. Document Classification Rationale for Edge Cases

**DO:**

```python
@pytest.mark.system  # NOT acceptance - no user story acceptance criteria
@pytest.mark.functional
def test_end_to_end_checkout():
    """
    Test complete checkout flow (system test).

    Classified as 'system' (not 'acceptance') because this tests
    the technical implementation of checkout, not acceptance criteria
    from a user story. Acceptance tests would reference specific
    user story requirements.
    """
    pass
```

**Rationale**: When classification isn't obvious, document reasoning to help maintainers.

### 8. Validate Classification Coverage in CI

Add CI check to ensure all tests are classified:

```python
# conftest.py
def pytest_collection_modifyitems(items):
    """Ensure all tests have required classifications."""
    test_levels = {'unit', 'integration', 'system', 'acceptance', 'validation'}
    test_types = {'functional', 'security', 'performance', 'usability'}

    errors = []
    for item in items:
        markers = {mark.name for mark in item.iter_markers()}

        level_markers = markers & test_levels
        type_markers = markers & test_types

        if len(level_markers) == 0:
            errors.append(f"{item.nodeid}: Missing test level marker")
        elif len(level_markers) > 1:
            errors.append(f"{item.nodeid}: Multiple test level markers: {level_markers}")

        if len(type_markers) == 0:
            errors.append(f"{item.nodeid}: Missing test type marker")

    if errors:
        raise ValueError("Test classification errors:\n" + "\n".join(errors))
```

**Rationale**: Prevent tests without classifications from reaching production. CI fails if tests missing markers.

---

## Migration Guide

### Gradual Adoption Strategy

**Don't try to classify all tests at once.** Gradual adoption reduces risk and allows learning.

#### Phase 1: New Tests Only (Week 1-2)

1. **Add marker registration** to `pytest.ini` (or equivalent for your framework)
2. **Update test templates** to include classification examples
3. **Require classifications for new tests** (PR review checklist)
4. **Run existing tests as before** (no filtering)

**Outcome**: New tests have classifications, old tests work as before.

#### Phase 2: Critical Path Tests (Week 3-4)

1. **Identify critical user flows** (login, checkout, payment, etc.)
2. **Add classifications to critical tests** (highest ROI)
3. **Create workflow-specific test commands** for critical paths

```bash
# Run critical path tests
pytest -m "system and functional"
```

**Outcome**: Critical tests can be run selectively, faster feedback on key workflows.

#### Phase 3: All Tests (Week 5+)

1. **Classify remaining tests** (batch by module/feature)
2. **Enable classification validation** (CI fails on missing markers)
3. **Update CI/CD pipeline** to use workflow-specific test commands
4. **Document classification standards** for team

**Outcome**: All tests classified, workflow-aware test execution enabled.

### Handling Legacy Tests Without Classifications

**Option 1: Legacy Marker (Temporary)**

Mark unclassified tests with `legacy` marker, run them in all workflows until classified:

```python
@pytest.mark.legacy  # Temporary marker for unclassified tests
def test_old_feature():
    pass
```

```bash
# Sprint execution: unit + integration + functional + legacy
pytest -m "(unit or integration) and functional or legacy"
```

**Remove legacy marker** as tests are classified.

**Option 2: Gradual Enforcement**

Start with warnings, escalate to errors:

```python
# conftest.py
def pytest_collection_modifyitems(items):
    """Warn about unclassified tests, error after deadline."""
    import datetime

    ENFORCEMENT_DATE = datetime.date(2025, 2, 1)  # Hard enforcement starts Feb 1
    today = datetime.date.today()

    errors = []
    for item in items:
        markers = {mark.name for mark in item.iter_markers()}

        if not (markers & test_levels) or not (markers & test_types):
            if today >= ENFORCEMENT_DATE:
                errors.append(f"{item.nodeid}: Missing classification")
            else:
                warnings.warn(f"{item.nodeid}: Missing classification (required by {ENFORCEMENT_DATE})")

    if errors:
        raise ValueError("Test classification errors:\n" + "\n".join(errors))
```

**Option 3: Default Classification**

Assign default classifications to unclassified tests based on file path:

```python
# conftest.py
def pytest_collection_modifyitems(items):
    """Apply default classifications based on file path."""
    for item in items:
        markers = {mark.name for mark in item.iter_markers()}

        # If no level marker, guess from file path
        if not (markers & test_levels):
            if '/unit/' in item.nodeid:
                item.add_marker(pytest.mark.unit)
            elif '/integration/' in item.nodeid:
                item.add_marker(pytest.mark.integration)
            else:
                item.add_marker(pytest.mark.unit)  # Default

        # If no type marker, default to functional
        if not (markers & test_types):
            item.add_marker(pytest.mark.functional)
```

**Use with caution**: Defaults may be wrong. Better to explicitly classify.

### Validation Tools to Check Classification Coverage

#### Coverage Report Script

```python
# scripts/check_test_classification_coverage.py
import pytest
from pathlib import Path

def analyze_test_classifications(test_dir):
    """Analyze test classification coverage."""
    # Collect all tests
    items = []
    pytest.main(['--collect-only', '-q', str(test_dir)], plugins=[
        CollectionPlugin(items)
    ])

    test_levels = {'unit', 'integration', 'system', 'acceptance', 'validation'}
    test_types = {'functional', 'security', 'performance', 'usability'}

    stats = {
        'total': len(items),
        'with_level': 0,
        'with_type': 0,
        'fully_classified': 0,
        'missing_level': [],
        'missing_type': [],
        'level_distribution': {},
        'type_distribution': {}
    }

    for item in items:
        markers = {mark.name for mark in item.iter_markers()}
        level_markers = markers & test_levels
        type_markers = markers & test_types

        if level_markers:
            stats['with_level'] += 1
            for level in level_markers:
                stats['level_distribution'][level] = stats['level_distribution'].get(level, 0) + 1
        else:
            stats['missing_level'].append(item.nodeid)

        if type_markers:
            stats['with_type'] += 1
            for test_type in type_markers:
                stats['type_distribution'][test_type] = stats['type_distribution'].get(test_type, 0) + 1
        else:
            stats['missing_type'].append(item.nodeid)

        if level_markers and type_markers:
            stats['fully_classified'] += 1

    return stats

def print_report(stats):
    """Print classification coverage report."""
    total = stats['total']
    print(f"Test Classification Coverage Report")
    print(f"=" * 50)
    print(f"Total tests: {total}")
    print(f"")
    print(f"Classification coverage:")
    print(f"  With level marker: {stats['with_level']}/{total} ({stats['with_level']/total*100:.1f}%)")
    print(f"  With type marker: {stats['with_type']}/{total} ({stats['with_type']/total*100:.1f}%)")
    print(f"  Fully classified: {stats['fully_classified']}/{total} ({stats['fully_classified']/total*100:.1f}%)")
    print(f"")
    print(f"Level distribution:")
    for level, count in sorted(stats['level_distribution'].items()):
        print(f"  {level}: {count} ({count/total*100:.1f}%)")
    print(f"")
    print(f"Type distribution:")
    for test_type, count in sorted(stats['type_distribution'].items()):
        print(f"  {test_type}: {count} ({count/total*100:.1f}%)")

    if stats['missing_level']:
        print(f"\nTests missing level marker ({len(stats['missing_level'])}):")
        for nodeid in stats['missing_level'][:10]:  # Show first 10
            print(f"  - {nodeid}")
        if len(stats['missing_level']) > 10:
            print(f"  ... and {len(stats['missing_level']) - 10} more")

    if stats['missing_type']:
        print(f"\nTests missing type marker ({len(stats['missing_type'])}):")
        for nodeid in stats['missing_type'][:10]:  # Show first 10
            print(f"  - {nodeid}")
        if len(stats['missing_type']) > 10:
            print(f"  ... and {len(stats['missing_type']) - 10} more")

if __name__ == '__main__':
    test_dir = Path('tests')
    stats = analyze_test_classifications(test_dir)
    print_report(stats)
```

Run regularly to track progress:

```bash
python scripts/check_test_classification_coverage.py

# Output:
# Test Classification Coverage Report
# ==================================================
# Total tests: 150
#
# Classification coverage:
#   With level marker: 120/150 (80.0%)
#   With type marker: 110/150 (73.3%)
#   Fully classified: 100/150 (66.7%)
#
# Level distribution:
#   unit: 80 (53.3%)
#   integration: 35 (23.3%)
#   system: 5 (3.3%)
#
# Type distribution:
#   functional: 90 (60.0%)
#   security: 15 (10.0%)
#   performance: 5 (3.3%)
```

---

## Architecture Reference

This test classification system implements the architecture defined in:

- **[ADR-004: Test Classification Taxonomy (Framework-Agnostic)](/mnt/c/Users/sundance/workspace/keychain/products/trusted-ai-development-workbench/docs/architecture/decisions/ADR-004-test-marker-taxonomy.md)**
  - Design rationale and alternatives considered
  - Framework-agnostic taxonomy definition
  - Implementation strategy

- **[config/test_taxonomy.py](/mnt/c/Users/sundance/workspace/keychain/products/trusted-ai-development-workbench/config/test_taxonomy.py)**
  - Universal taxonomy implementation
  - Validation functions
  - Helper utilities

- **[cli/commands/init.py](/mnt/c/Users/sundance/workspace/keychain/products/trusted-ai-development-workbench/cli/commands/init.py)**
  - Framework detection logic
  - Test configuration generation
  - Auto-detection of test frameworks

---

## Related Documentation

- **[Architecture Decision Records](/mnt/c/Users/sundance/workspace/keychain/products/trusted-ai-development-workbench/docs/architecture/decisions/)**: Design decisions and rationale
- **[Quick Start Guide](/mnt/c/Users/sundance/workspace/keychain/products/trusted-ai-development-workbench/docs/QUICKSTART.md)**: Getting started with the framework
- **[Workflow Boundaries](/mnt/c/Users/sundance/workspace/keychain/products/trusted-ai-development-workbench/docs/WORKFLOW-BOUNDARIES.md)**: Workflow execution patterns

---

## Summary

Test classification enables **workflow-aware test execution** by tagging tests with:

1. **Test Level** (exactly one): unit, integration, system, acceptance, validation
2. **Test Type** (at least one): functional, security, performance, usability
3. **Modifiers** (optional): slow, requires-db, requires-network, flaky

This universal taxonomy works across all testing frameworks through framework-native mechanisms:

- **Python/pytest**: `@pytest.mark.<tag>`
- **JavaScript/Jest**: Comment-based or test suite organization
- **Java/JUnit**: `@Tag("<tag>")`
- **Go**: Build tags or test naming
- **Generic**: Comment-based fallback

Different workflows run different test subsets:

- **Sprint execution**: Fast tests (unit + integration + functional)
- **Release validation**: All tests (comprehensive)
- **Security audit**: Security tests only
- **Performance baseline**: Performance tests only

Adopt gradually using the migration guide, validate coverage with tooling, and keep classifications accurate as tests evolve.

**Result**: Faster feedback loops, better test organization, workflow-specific quality gates, and framework-agnostic test execution.
