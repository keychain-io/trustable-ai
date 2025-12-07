# Sprint Execution Monitoring Workflow

**Project**: trusted-ai-development-workbench
**Workflow**: Sprint Execution Monitoring
**Purpose**: Monitor sprint progress, identify blockers, and generate daily reports

## Output Formatting Requirements

**IMPORTANT**: Use actual Unicode emojis in reports, NOT GitHub-style shortcodes.

---

## Workflow Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  SPRINT EXECUTION - Implementation & Monitoring                             │
│                                                                             │
│  IMPLEMENTATION CYCLE (for each task):                                     │
│    1. /engineer → Implement code + unit tests                              │
│    2. Run unit tests                                                       │
│    3. /tester → Evaluate tests, run integration tests                      │
│    4. If tests pass with high confidence → Auto-commit                     │
│    5. Update work item status                                              │
│                                                                             │
│  MONITORING CYCLE (daily):                                                 │
│    1. Collect sprint status data                                           │
│    2. /scrum-master → Daily standup report                                 │
│    3. /senior-engineer → Blocker analysis (if blocked items)               │
│    4. Quality health check                                                 │
│    5. /security-specialist → Weekly security review                        │
│    6. Generate status report                                               │
│                                                                             │
│  Each agent command spawns a FRESH CONTEXT WINDOW via Task tool            │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Initialize Workflow

```python
# Initialize work tracking adapter
import sys
sys.path.insert(0, ".claude/skills")
from work_tracking import get_adapter

adapter = get_adapter()
print(f"📋 Work Tracking: {adapter.platform}")

current_sprint = input("Sprint name (e.g., Sprint 1): ")

# Load sprint work items via adapter
try:
    sprint_items = adapter.query_work_items(
        filters={
            'System.IterationPath': f'Trusted AI Development Workbench\\{current_sprint}'
        }
    )
    print(f"📋 Found {len(sprint_items)} items in {current_sprint}")
except Exception as e:
    print(f"❌ Failed to load sprint items: {e}")
    sprint_items = []
```

---

## PART A: IMPLEMENTATION CYCLE

### Implementation Cycle Overview

For each task in the sprint, follow this cycle:

1. **Engineer implements** → Code + unit tests
2. **Run unit tests** → Validate basic functionality
3. **Tester validates** → Evaluate tests, run integration tests
4. **Auto-commit** → If tests pass with high confidence
5. **Update work item** → Mark as Done

---

### Step A1: Select Task to Implement

```python
# Get tasks that are ready to implement
ready_tasks = [
    item for item in sprint_items
    if item.get('state') in ['New', 'Approved', 'Ready']
    and item.get('type') == 'Task'
]

if not ready_tasks:
    print("✅ No tasks ready for implementation")
    # Skip to monitoring cycle
else:
    print(f"\n📋 Tasks ready for implementation: {len(ready_tasks)}")
    for i, task in enumerate(ready_tasks[:10], 1):  # Show first 10
        title = task.get('title', 'Untitled')
        task_id = task.get('id')
        points = get_story_points(task)
        print(f"  {i}. #{task_id}: {title} ({points} pts)")

    # User selects task
    selection = input("\nSelect task number (or 'skip' for monitoring only): ")
    if selection.lower() == 'skip':
        selected_task = None
    else:
        try:
            idx = int(selection) - 1
            selected_task = ready_tasks[idx]
            print(f"\n✅ Selected: #{selected_task['id']} - {selected_task['title']}")
        except (ValueError, IndexError):
            print("❌ Invalid selection, skipping implementation")
            selected_task = None
```

---

### Step A2: Engineer Implementation

**IF A TASK IS SELECTED**, call `/engineer` with the following task:

```
## YOUR TASK: Implement Feature

Implement the task according to specifications.

### Task Details
- ID: {selected_task['id']}
- Title: {selected_task['title']}
- Description: {selected_task['description']}
- Acceptance Criteria: {selected_task['acceptance_criteria']}

### Project Context
- Language: Python
- Frameworks: pytest
- Source directory: src
- Test directory: tests

### Requirements
1. Implement ALL functionality per acceptance criteria
2. Follow existing code patterns in the project
3. Write unit tests for all new code
4. Ensure 80% coverage minimum

### Output
- Implementation files in appropriate locations
- Unit test file with comprehensive coverage
- All tests passing
```

**After the agent completes:**
- Verify implementation files created
- Note the files changed for commit later

---

### Step A3: Run Unit Tests

Run the test suite to validate basic functionality:

```bash
python -m pytest tests -v
```

**If unit tests fail:**
- Do NOT proceed to integration testing
- Review failures and fix implementation
- Re-run until unit tests pass

---

### Step A4: Tester Validation

**Call `/tester` with the following task:**

```
## YOUR TASK: Validate Implementation and Run Integration Tests

Evaluate the implementation, validate tests, and run integration tests.

### Task Being Validated
- ID: {selected_task['id']}
- Title: {selected_task['title']}
- Acceptance Criteria: {selected_task['acceptance_criteria']}

### Implementation Files
{List of files created/modified by engineer}

### Your Validation Steps

1. **Evaluate Unit Tests**
   - Do tests cover all acceptance criteria?
   - Are tests falsifiable (can they fail)?
   - Is coverage >= 80%?
   - Do tests check behavior, not implementation?

2. **Run Integration Tests**
   - Test feature in context of full system
   - Verify integration with existing components
   - Check for regressions
   - Validate error handling

3. **Quality Assessment**
   - Code complexity acceptable?
   - Security vulnerabilities?
   - Performance acceptable?

### Output Format

Return JSON with:
```json
{
  "validation_status": "pass|fail",
  "confidence": "high|medium|low",
  "test_results": {
    "unit_tests_pass": true|false,
    "integration_tests_pass": true|false,
    "coverage_percent": 85,
    "coverage_meets_standard": true|false
  },
  "issues_found": [
    "Description of any issues"
  ],
  "recommendation": "commit|fix_required"
}
```

**CRITICAL**: Set `confidence: "high"` ONLY if:
- All tests pass
- Coverage >= 80%
- No critical issues found
- Integration tests demonstrate feature works in full system

**Fault Attribution**: For each failed test, provide:
```json
{
  "test_name": "test_user_login_valid_credentials",
  "error": "AssertionError: Expected 200, got 401",
  "expected": "HTTP 200 with auth token",
  "actual": "HTTP 401 Unauthorized",
  "acceptance_criterion": "User can log in with valid email/password",
  "fault_attribution": "CODE|TEST|SPEC",
  "reasoning": "Spec requires login to work, test expects 200, code returns 401 - CODE is wrong"
}
```

**Fault Attribution Rules**:
- **CODE**: Test expectation matches spec, but code doesn't → Create bug ticket
- **TEST**: Test expectation doesn't match spec → Tester fixes test
- **SPEC**: Spec is ambiguous or contradictory → Escalate to human
```

**After the agent completes:**
- Parse validation result JSON
- Check confidence level
- Handle test failures with fault attribution and bug creation

---

### Step A4b: Handle Test Failures (Fault Attribution & Bug Creation)

**IF tests fail (`validation_status == "fail"`), perform fault attribution:**

```python
# Parse which tests failed
failed_tests = validation_result.get('failed_tests', [])

if failed_tests:
    print(f"\n⚠️  {len(failed_tests)} test(s) failed")

    # For each failed test, determine fault: CODE, TEST, or SPEC
    for failure in failed_tests:
        test_name = failure.get('test_name')
        error_message = failure.get('error')
        spec_reference = failure.get('acceptance_criterion')

        # Fault attribution logic:
        # - CODE fault: Test expects correct behavior per spec, code doesn't match
        # - TEST fault: Test expectation doesn't match spec
        # - SPEC fault: Spec is ambiguous or incorrect

        fault = "CODE"  # Default assumption: code is wrong

        # Tester agent should have provided fault attribution in validation result
        if 'fault_attribution' in failure:
            fault = failure['fault_attribution']  # CODE | TEST | SPEC

        print(f"\n  ❌ {test_name}")
        print(f"     Error: {error_message}")
        print(f"     Fault: {fault}")

        # Create bug ticket for CODE faults
        if fault == "CODE":
            try:
                bug_title = f"Test failure: {test_name}"
                bug_description = f"""## Test Failure

**Test**: {test_name}
**Task**: #{selected_task['id']} - {selected_task['title']}
**Error**: {error_message}

**Acceptance Criterion**: {spec_reference}

**Fault Attribution**: Code does not match spec expectation

**Expected Behavior**: {failure.get('expected', 'N/A')}
**Actual Behavior**: {failure.get('actual', 'N/A')}

**Fix Required**: Update implementation to match spec

---
*Auto-created by /sprint-execution*
"""

                bug = adapter.create_work_item(
                    work_item_type="Bug",
                    title=bug_title,
                    description=bug_description,
                    fields={
                        'System.IterationPath': f'Trusted AI Development Workbench\\{sprint_name}',
                        'System.Parent': selected_task['id'],  # Link to parent task
                        'System.Tags': 'auto-generated;test-failure',
                        'Microsoft.VSTS.Common.Priority': 1  # High priority
                    }
                )

                print(f"     🐛 Created bug #{bug['id']}: {bug_title}")

            except Exception as e:
                print(f"     ⚠️  Failed to create bug ticket: {e}")

        elif fault == "TEST":
            print(f"     ⚠️  TEST fault: Test expectation doesn't match spec")
            print(f"     Action: Tester should fix test expectations")

        elif fault == "SPEC":
            print(f"     ⚠️  SPEC fault: Specification is ambiguous or incorrect")
            print(f"     Action: Escalate to human for spec clarification")

    # Do NOT proceed to commit if tests failed
    print(f"\n❌ Cannot proceed to commit - {len(failed_tests)} test failure(s)")
    print(f"   Fix issues and re-run /sprint-execution")

    # Update task status to "Blocked" or "In Progress" (not Done)
    try:
        adapter.update_work_item(
            work_item_id=selected_task['id'],
            fields={
                'System.State': 'In Progress',
                'System.History': f"""
Test validation failed - {len(failed_tests)} test(s) failing

{len([f for f in failed_tests if f.get('fault_attribution') == 'CODE'])} CODE faults (bugs created)
{len([f for f in failed_tests if f.get('fault_attribution') == 'TEST'])} TEST faults (test fixes needed)
{len([f for f in failed_tests if f.get('fault_attribution') == 'SPEC'])} SPEC faults (clarification needed)

Review bug tickets and fix issues before re-running.
"""
            }
        )
    except Exception as e:
        print(f"⚠️  Failed to update work item: {e}")

    # Exit implementation cycle
    selected_task = None  # Clear selection to skip commit step
```

---

### Step A5: Auto-Commit (High Confidence Only)

**IF `validation_status == "pass"` AND `confidence == "high"`**, auto-commit:

```bash
# Stage all implementation files
git add src/ tests/

# Create commit with task reference
git commit -m "$(cat <<'EOF'
Implement #{selected_task['id']}: {selected_task['title']}

{Brief summary of changes}

Acceptance criteria met:
{List acceptance criteria from task}

Test results:
- Unit tests: ✅ Pass
- Integration tests: ✅ Pass
- Coverage: {coverage_percent}% (>= 80%)

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
EOF
)"

echo "✅ Changes committed successfully"
```

**IF `confidence != "high"`**, do NOT commit:

```
⚠️  Tests passed but confidence is {confidence}.

Issues that need attention:
{List issues from validation}

Recommendation: {recommendation}

Changes NOT committed. Review issues and re-run validation.
```

---

### Step A6: Update Work Item Status

```python
# Update task status to Done (only if committed)
if committed:
    try:
        adapter.update_work_item(
            work_item_id=selected_task['id'],
            fields={
                'System.State': 'Done',
                'System.History': f"""
Implementation complete and committed.

Test Results:
- Unit Tests: Pass
- Integration Tests: Pass
- Coverage: {coverage_percent}%

Commit: {git_commit_hash}
"""
            }
        )
        print(f"✅ Updated work item #{selected_task['id']} to Done")
    except Exception as e:
        print(f"⚠️ Failed to update work item: {e}")
        print(f"   Manual update required for #{selected_task['id']}")
```

---

## PART B: MONITORING CYCLE

### Step B1: Collect Sprint Status Data

Gather metrics from work items:

```python
# Calculate metrics from adapter work items
completed = [i for i in sprint_items if i.get('state') == 'Done']
in_progress = [i for i in sprint_items if i.get('state') == 'In Progress']
blocked = [i for i in sprint_items if i.get('state') == 'Blocked']
not_started = [i for i in sprint_items if i.get('state') == 'New']

# Get story points from work items
def get_story_points(item):
    return 0

total_points = sum(get_story_points(i) for i in sprint_items)
completed_points = sum(get_story_points(i) for i in completed)

print(f"📊 Sprint Status:")
print(f"  Total: {len(sprint_items)} items ({total_points} pts)")
print(f"  ✅ Done: {len(completed)} ({completed_points} pts)")
print(f"  🔄 In Progress: {len(in_progress)}")
print(f"  🔴 Blocked: {len(blocked)}")
print(f"  ⬜ Not Started: {len(not_started)}")
```

---

### Step B2: Generate Daily Standup Report

**Call `/scrum-master` with the following task:**

```
## YOUR TASK: Generate Daily Standup Report

Create a daily standup report for the team.

### Sprint Data
- Sprint: {current_sprint}
- Total Items: {len(sprint_items)}
- Completed: {len(completed)} ({completed_points} pts)
- In Progress: {len(in_progress)}
- Blocked: {len(blocked)}
- Not Started: {len(not_started)}

### Work Items
{List of all work items with status}

### Generate Report Including:

1. **Yesterday's Progress**
   - What was completed
   - Story points delivered

2. **Today's Focus**
   - What should be worked on
   - Priority items

3. **Blockers & Impediments**
   - Current blockers
   - Who needs to resolve them

4. **Sprint Health**
   - On track / At risk / Behind
   - Days remaining
   - Burndown status

5. **Recommendations**
   - Team focus areas
   - Risk mitigations

### Output Format

Return a formatted standup report in markdown.
```

**After the agent completes:**
- Display standup report to user
- Save to `.claude/reports/daily/`

---

### Step B3: Analyze Blockers (If Any)

**IF THERE ARE BLOCKED ITEMS**, call `/senior-engineer` with the following task:

```
## YOUR TASK: Analyze Blocked Work Items

Review blocked items and suggest resolutions.

### Blocked Items
{List of blocked work items with details}

### For Each Blocker, Analyze:

1. **Root Cause**
   - Why is this blocked?
   - Technical vs. organizational blocker

2. **Impact Assessment**
   - How many items depend on this?
   - Sprint goal impact

3. **Resolution Options**
   - Technical solutions or workarounds
   - Who needs to be involved
   - Estimated time to resolve

4. **Priority Ranking**
   - Which blockers to resolve first
   - Critical path analysis

### Output Format

Return JSON with blocker analysis and recommendations.
```

**After the agent completes:**
- Display blocker analysis
- Recommend actions to unblock items

---

### Step B4: Quality Health Check

Run automated quality checks:

```bash
# Run tests with coverage
python -m pytest --cov=src --cov-report=term

# Check coverage against standard
# Target: 80%
```

Compare results against quality standards:
- Test Coverage: Current vs. 80%
- Critical Vulnerabilities: Current vs. 0
- Code Complexity: Current vs. 10

---

### Step B5: Weekly Security Review (Fridays Only)

**FOR WEEKLY REPORTS ONLY**, call `/security-specialist` with the following task:

```
## YOUR TASK: Weekly Security Status Review

Review sprint security status.

### Quality Standards
- Critical Vulnerabilities: Max 0
- High Vulnerabilities: Max 0

### Security Scan Results
{Include any security scan output}

### Analyze:

1. **Vulnerability Status**
   - New vulnerabilities this sprint
   - Resolved vulnerabilities
   - Outstanding issues

2. **Security Impact of Changes**
   - Features with security implications
   - Authentication/authorization changes

3. **Recommendations**
   - Critical issues requiring immediate attention
   - Security tasks for next sprint

### Output Format

Return security review report in markdown.
```

---

### Step B6: Generate Status Report

Compile comprehensive report:

```
════════════════════════════════════════════════════════════════════════════════
📊 SPRINT STATUS REPORT - {current_sprint}
════════════════════════════════════════════════════════════════════════════════

📈 Progress: {completed_points}/{total_points} points ({percentage}%)

📋 Work Items:
  ✅ Done: {done_count}
  🔄 In Progress: {in_progress_count}
  🔴 Blocked: {blocked_count}
  ⬜ Not Started: {not_started_count}

⚠️ Blockers:
  {blocker_list}

🔒 Quality:
  - Test Coverage: {coverage}% (target: 80%)
  - Vulnerabilities: {vuln_count}

🎯 Sprint Health: {On Track / At Risk / Behind}

════════════════════════════════════════════════════════════════════════════════
```

---

## Agent Commands Used

| Cycle | Step | Agent Command | Purpose |
|-------|------|---------------|---------|
| **Implementation** | A2 | `/engineer` | Implement code + unit tests |
| **Implementation** | A4 | `/tester` | Validate tests, run integration tests |
| **Monitoring** | B2 | `/scrum-master` | Daily standup report |
| **Monitoring** | B3 | `/senior-engineer` | Blocker analysis (when blocked) |
| **Monitoring** | B5 | `/security-specialist` | Weekly security review |

**Key**: Each agent command spawns a **fresh context window** via the Task tool.

**Auto-Commit**: Executes at step A5 when `validation_status == "pass"` AND `confidence == "high"`

---

## Execution Schedule

- **Daily (9 AM)**: Steps 1-4 (status, standup, blockers, quality)
- **Weekly (Friday 4 PM)**: Full workflow including security review
- **Ad-hoc**: Run manually when needed

---

## Configuration

**Work Tracking Platform:** azure-devops

**Quality Standards:**
- Test Coverage: >= 80%
- Critical Vulnerabilities: <= 0
- Code Complexity: <= 10

---

*Generated by Trustable AI Workbench for trusted-ai-development-workbench*