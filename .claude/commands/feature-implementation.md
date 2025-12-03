# Feature Implementation Workflow (Adversarial Verification)

**Project**: Trusted AI Development Workbench
**Workflow**: Feature Implementation with Adversarial Verification
**Purpose**: Implement features with procedural safeguards against AI-generated bugs

## Output Formatting Requirements

**IMPORTANT**: Use actual Unicode emojis in reports, NOT GitHub-style shortcodes.

---

## The Problem This Workflow Solves

AI-generated code often contains subtle bugs. AI-generated tests often miss those same bugs because they share the same blind spots. This workflow uses **adversarial multi-agent verification** with **fresh context windows** for each specialized agent.

```
┌─────────────────────────────────────────────────────────────────────────┐
│  This Workflow (Adversarial Verification with Agent Slash Commands)     │
│                                                                         │
│  1. /senior-engineer → Creates API contract                            │
│  2. /software-developer → Implements feature                           │
│  3. /spec-driven-tester → Tests from SPEC ONLY (no code!)             │
│  4. /adversarial-tester → Tries to break code                         │
│  5. /falsifiability-prover → Verifies tests can fail                  │
│  6. /test-arbitrator → Resolves code/test/spec conflicts              │
│                                                                         │
│  Each agent command spawns a FRESH CONTEXT WINDOW via Task tool        │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

- Work item ID with clear acceptance criteria
- Specification file at `docs/specifications/` (from sprint-planning)
- Project codebase with existing test infrastructure

---

## Initialize Workflow

First, collect the work item information:

```python
work_item_id = input("Enter work item ID (e.g., FEATURE-001): ")
sprint_number = input("Enter sprint number: ")

# Load specification file
from pathlib import Path
spec_file = Path(f"docs/specifications/sprint-{sprint_number}/{work_item_id}-spec.md")
if spec_file.exists():
    specification = spec_file.read_text()
    print(f"✅ Loaded specification from {spec_file}")
else:
    print(f"❌ Specification file not found: {spec_file}")
    print("   Run /sprint-planning first to create specifications")
```

---

## Phase 1: API Contract Design

### Step 1.1: Create API Contract

**Call `/senior-engineer` with the following task:**

```
## YOUR TASK: Design API Contract

You are designing the API contract for a feature BEFORE implementation.
This contract will be given to an independent tester who will NEVER see the code.

### Work Item
- ID: {work_item_id}
- Specification:
{specification}

### Required Output

Create a precise API contract document with:

1. **Public Interface**
   - Function/method signatures with full type annotations
   - Parameter descriptions and constraints
   - Return type and guarantees
   - Exceptions that can be raised

2. **Input Constraints**
   - Valid ranges, formats, types for each parameter
   - What happens with null/empty/invalid inputs

3. **Output Guarantees**
   - What the caller can rely on
   - Invariants that are always true

4. **Error Conditions**
   - Every way this can fail
   - What exception/error for each condition

5. **State Changes**
   - Side effects (files, database, external calls)
   - Idempotency guarantees

**CRITICAL**: Be extremely precise. An independent tester will write tests
based ONLY on this contract without seeing your implementation.
Ambiguity here causes test failures later.

### Output Format

Save contract to: `.claude/contracts/{work_item_id}-contract.md`
```

**After the agent completes:**
- Verify the contract file was created
- The contract will be used in Phase 2 (given to spec-driven tester)

---

## Phase 2: Implementation

### Step 2.1: Implement Feature

**Call `/software-developer` with the following task:**

```
## YOUR TASK: Implement Feature

Implement the feature according to the API contract.

### API Contract
{contents of .claude/contracts/{work_item_id}-contract.md}

### Specification
{specification}

### Project Context
- Language: Python
- Frameworks: 
- Source directory: src
- Test directory: tests

### Requirements
1. Implement ALL functionality in the API contract
2. Follow existing code patterns in the project
3. Add inline comments for complex logic
4. Create ONLY basic happy-path tests (comprehensive tests come from spec-driven tester)

### Output
- Implementation files in appropriate locations
- Basic test file with 2-3 happy path tests

**DO NOT write comprehensive tests.** That's the spec-driven tester's job.
Your tests would share your blind spots.
```

**After the agent completes:**
- Verify implementation compiles/parses
- Verify basic tests pass
- Note the files created for Phase 3

---

## Phase 3: Specification-Driven Testing (Information Asymmetry)

### Step 3.1: Create Spec-Driven Tests (NO CODE ACCESS)

**CRITICAL - Information Asymmetry:**
```
┌──────────────────────────────────────────────────────────────┐
│  The Spec-Driven Tester receives:                            │
│  ✅ Work item specification                                  │
│  ✅ API contract                                             │
│  ❌ NOT the implementation code                              │
│  ❌ NOT the developer's tests                                │
│                                                              │
│  This agent gets a FRESH CONTEXT with only spec materials.  │
│  It literally CANNOT see the code.                          │
└──────────────────────────────────────────────────────────────┘
```

**Call `/spec-driven-tester` with the following task:**

```
## YOUR TASK: Generate Tests from Specification ONLY

You are writing tests based ONLY on the specification and API contract.
You have NOT been given the implementation code. This is intentional.

### Why You Don't See The Code
By not seeing the implementation, you cannot share the developer's blind spots.
You test what SHOULD happen (per spec), not what DOES happen (per code).

### Specification
{specification}

### API Contract
{contents of .claude/contracts/{work_item_id}-contract.md}

### Test Framework
- Framework: pytest
- Location: tests/spec_driven/test_{work_item_id}.py

### Required Test Categories

1. **Acceptance Criteria Tests**
   - One or more tests for each acceptance criterion
   - Clear traceability to requirements

2. **Input Validation Tests** (from API contract)
   - Valid inputs at boundaries
   - Invalid inputs (null, empty, wrong type, out of range)
   - Edge cases from input constraints

3. **Output Guarantee Tests** (from API contract)
   - Verify all output guarantees hold
   - Test return value invariants

4. **Error Condition Tests** (from API contract)
   - Every error condition from contract
   - Verify correct exception type and message

5. **State Change Tests** (from API contract)
   - Verify side effects occur correctly
   - Test idempotency if specified

### Output Format
- Test file with clear docstrings referencing spec/contract
- Minimum 15-25 tests for typical feature
- Each test must be specific and falsifiable
```

**After the agent completes:**
- Save the spec-driven tests
- DO NOT show the tests to the developer yet
- These tests will be run in Phase 5

---

## Phase 4: Adversarial Testing (Red Team)

### Step 4.1: Find Bugs (FULL ACCESS)

This agent gets EVERYTHING and tries to break the code.

**Call `/adversarial-tester` with the following task:**

```
## YOUR TASK: Find Bugs That Tests Miss

Your job is to BREAK this code. Find bugs that existing tests don't catch.
Your success is measured by bugs FOUND, not by tests PASSED.

### You Have Access To Everything

**Specification:**
{specification}

**API Contract:**
{contents of .claude/contracts/{work_item_id}-contract.md}

**Implementation Code:**
{read the implementation files from Phase 2}

**Developer's Tests:**
{read the developer's test file}

**Spec-Driven Tests:**
{read the spec-driven test file from Phase 3}

### Your Attack Approach

1. **Gap Analysis**
   - What does the spec require that tests don't verify?
   - What edge cases did both developer and spec-tester miss?

2. **Boundary Attacks**
   - Test just inside and outside every boundary
   - Test at MAX_INT, MIN_INT, zero, negative
   - Test empty strings, null bytes, unicode edge cases

3. **State Corruption**
   - Can you put the system in an invalid state?
   - Race conditions? Resource exhaustion?

4. **Security Probes**
   - Injection attacks (SQL, command, path traversal)
   - Authentication/authorization bypasses
   - Information leakage

5. **Mutation Escapes**
   - For each test, what code mutation would it NOT catch?
   - Prove the gap with a test that catches the mutation

### Required Output

1. **Gap Report**: List of test coverage gaps
2. **Adversarial Tests**: Tests that expose the gaps
3. **Severity Ranking**: Critical/High/Medium/Low for each finding

Save to: tests/adversarial/test_{work_item_id}_adversarial.py
```

---

## Phase 5: Falsifiability Verification

### Step 5.1: Verify Tests Can Fail

**Call `/falsifiability-prover` with the following task:**

```
## YOUR TASK: Prove Every Test Can Fail

A test that cannot fail is worthless. For each test, prove it CAN fail
by describing a minimal code mutation that would break it.

### Tests to Verify

**Spec-Driven Tests:**
{contents of spec-driven test file}

**Adversarial Tests:**
{contents of adversarial test file}

### For Each Test, Provide:

1. **Test Name**: `test_xyz`
2. **What It Claims to Verify**: "Verifies that X happens when Y"
3. **Mutation That Breaks It**: "Change line N from A to B"
4. **Expected Failure**: "AssertionError: expected X, got Z"
5. **Verdict**: FALSIFIABLE / NOT_FALSIFIABLE

### Non-Falsifiable Tests Must Be Fixed

If a test passes with broken code, it's not testing what it claims.
Flag these for revision.

### Output Format

```markdown
## Falsifiability Report

### Summary
- Tests analyzed: N
- Falsifiable: M
- NOT falsifiable (needs fix): O

### Details
[For each test, the analysis above]
```

Save to: `.claude/reports/{work_item_id}-falsifiability.md`
```

---

## Phase 6: Run Tests and Remediation

### Step 6.1: Run All Tests

Now run all the tests:

```bash
python -m pytest tests/ -v --tb=short
```

### Step 6.2: If Tests Fail - Arbitrate

When a test fails, there's three-way ambiguity:
- CODE is wrong (doesn't match spec)
- TEST is wrong (doesn't match spec)
- SPEC is wrong (doesn't match reality)

**Call `/test-arbitrator` with the following task:**

```
## YOUR TASK: Determine Who Is Wrong

Tests are failing. Your job is to determine whether the CODE, TEST, or SPEC is wrong.

### Failing Tests
{list of failing tests with error messages}

### Evidence Package

**Specification:**
{specification}

**API Contract:**
{contents of API contract}

**Implementation Code:**
{relevant code sections}

**Failing Test Code:**
{the test code that failed}

### For Each Failing Test, Determine:

| Verdict | Meaning | Action |
|---------|---------|--------|
| CODE_WRONG | Implementation doesn't match spec | Developer fixes code |
| TEST_WRONG | Test doesn't match spec | Tester fixes test |
| SPEC_WRONG | Spec doesn't match reality | Update spec, then code & test |
| SPEC_AMBIGUOUS | Spec is unclear | Escalate to human |

### Output Format

For each failing test:
```markdown
## Ruling: test_xyz

**Verdict**: CODE_WRONG | TEST_WRONG | SPEC_WRONG | SPEC_AMBIGUOUS

**Evidence**: [What you examined]

**Reasoning**: [Step-by-step logic]

**Required Action**: [Specific fix needed]

**Confidence**: HIGH | MEDIUM | LOW
```
```

**After arbitration:**
- Apply the fixes based on verdicts
- Re-run tests
- Repeat until all tests pass or maximum iterations (3) reached

---

## Phase 7: Quality Gates

### Step 7.1: Verify All Gates Pass

| Gate | Requirement | Check |
|------|-------------|-------|
| All Tests Pass | 100% | `pytest` exits 0 |
| Coverage | >= 80% | `pytest --cov` |
| Complexity | <= 10 | Radon/ESLint |
| Falsifiability | 100% | All tests proven falsifiable |
| Adversary Clean | No unaddressed gaps | Adversarial report |

### Step 7.2: If Gates Fail

- Coverage too low → Call `/spec-driven-tester` to add more tests
- Complexity too high → Call `/software-developer` to refactor
- Adversary found gaps → Address gaps and re-verify

---

## Phase 8: Completion

### Step 8.1: Update Work Item Status

```python
# Update work item to Done
# Add verification summary as comment
```

### Step 8.2: Generate Verification Report

Save comprehensive report to `.claude/reports/{work_item_id}-verification.md`

---

## Agent Commands Used

| Phase | Agent Command | Purpose |
|-------|---------------|---------|
| 1 | `/senior-engineer` | Design API contract |
| 2 | `/software-developer` | Implement feature |
| 3 | `/spec-driven-tester` | Tests from spec (no code access) |
| 4 | `/adversarial-tester` | Find gaps and bugs |
| 5 | `/falsifiability-prover` | Verify tests work |
| 6 | `/test-arbitrator` | Resolve conflicts |

**Key**: Each agent command spawns a **fresh context window** via the Task tool.

---

*Generated by Trustable AI Workbench for Trusted AI Development Workbench*