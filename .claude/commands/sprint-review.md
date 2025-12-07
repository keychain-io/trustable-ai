# Sprint Review Workflow

**Project**: trusted-ai-development-workbench
**Workflow**: Sprint Review (Acceptance & Deployment Readiness)
**Purpose**: Review sprint completion, run acceptance tests, assess deployment readiness, and close sprint

## Output Formatting Requirements

**IMPORTANT**: Use actual Unicode emojis in reports, NOT GitHub-style shortcodes.

---

## Workflow Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  SPRINT REVIEW - Acceptance & Deployment Readiness                          │
│                                                                             │
│  Step 1: Collect sprint completion metrics                                 │
│  Step 2: /tester → Run acceptance tests                                    │
│  Step 3: /security-specialist → Final security review                      │
│  Step 4: /engineer → Deployment readiness assessment                       │
│  Step 5: /scrum-master → Sprint closure decision                           │
│  Step 6: Human approval → Close sprint or extend                           │
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

sprint_name = input("Sprint name (e.g., Sprint 3): ")

# Load sprint work items
try:
    sprint_items = adapter.query_work_items(
        filters={
            'System.IterationPath': f'Trusted AI Development Workbench\\{sprint_name}'
        }
    )
    print(f"📋 Found {len(sprint_items)} items in {sprint_name}")
except Exception as e:
    print(f"❌ Failed to load sprint items: {e}")
    sprint_items = []
```

---

## Step 1: Collect Sprint Completion Metrics

```python
# Calculate completion metrics
completed = [i for i in sprint_items if i.get('state') == 'Done']
in_progress = [i for i in sprint_items if i.get('state') == 'In Progress']
not_done = [i for i in sprint_items if i.get('state') not in ['Done', 'Removed']]

# Get story points
def get_story_points(item):
    return 0

total_points = sum(get_story_points(i) for i in sprint_items)
completed_points = sum(get_story_points(i) for i in completed)
completion_rate = (completed_points / total_points * 100) if total_points > 0 else 0

print(f"\n📊 Sprint Completion Metrics:")
print(f"  Total Items: {len(sprint_items)} ({total_points} pts)")
print(f"  ✅ Completed: {len(completed)} ({completed_points} pts)")
print(f"  🔄 In Progress: {len(in_progress)}")
print(f"  ⬜ Not Done: {len(not_done)}")
print(f"  📈 Completion Rate: {completion_rate:.1f}%")
```

---

## Step 2: Run Acceptance Tests

**Call `/tester` with the following task:**

```
## YOUR TASK: Run Acceptance Tests for Sprint Completion

Execute acceptance tests for all completed features in the sprint.

### Sprint Details
- Sprint: {sprint_name}
- Completed Items: {len(completed)}
- Completed Story Points: {completed_points}

### Completed Work Items
{For each completed item:
  - ID: {item['id']}
  - Title: {item['title']}
  - Acceptance Criteria: {item['acceptance_criteria']}
}

### Acceptance Testing Requirements

1. **Functional Acceptance Tests**
   - Verify each completed feature meets its acceptance criteria
   - Test user workflows end-to-end
   - Validate integration with existing system
   - Check for regressions in existing functionality

2. **Non-Functional Acceptance Tests**
   - Performance: Response times within SLA
   - Scalability: Handles expected load
   - Usability: UI/UX meets standards
   - Compatibility: Works across supported platforms/browsers

3. **Data Validation**
   - Data migrations completed successfully
   - Data integrity maintained
   - No data loss or corruption

4. **Quality Gates**
   - Test coverage >= 80%
   - No critical or high priority bugs open
   - All tests passing
   - No security vulnerabilities

### Output Format

Return JSON with:
```json
{
  "acceptance_status": "pass|fail|partial",
  "tests_run": 50,
  "tests_passed": 48,
  "tests_failed": 2,
  "coverage_percent": 85,
  "failed_criteria": [
    {
      "work_item": "1234",
      "criterion": "User can reset password",
      "failure_reason": "Email not sent in dev environment"
    }
  ],
  "quality_gates": {
    "coverage_met": true,
    "no_critical_bugs": true,
    "all_tests_passing": false
  },
  "recommendation": "approve|fix_required|partial_approval"
}
```
```

**After the agent completes:**
- Parse acceptance test results
- Document any failures

---

## Step 3: Security Review

**Call `/security-specialist` with the following task:**

```
## YOUR TASK: Final Security Review Before Deployment

Perform final security review of all changes in the sprint.

### Sprint Changes
- Completed Features: {list of completed features}
- Code Changes: {git diff statistics}
- New Dependencies: {any new packages/libraries added}

### Security Review Checklist

1. **Vulnerability Scan Results**
   - Run dependency scanner (e.g., pip-audit, npm audit)
   - Check for known vulnerabilities in dependencies
   - Verify 0 critical vulns max
   - Verify 0 high vulns max

2. **Code Security Review**
   - OWASP Top 10 compliance
   - Authentication/authorization changes reviewed
   - Input validation and sanitization
   - SQL injection prevention
   - XSS prevention
   - CSRF protection

3. **Configuration Security**
   - No secrets in code or config files
   - Proper environment variable usage
   - Secure default configurations
   - HTTPS enforced where required

4. **Deployment Security**
   - Container image vulnerabilities scanned
   - Infrastructure as code reviewed
   - Network security rules validated
   - Access controls configured correctly

### Output Format

Return security review report:
```markdown
## Security Review Report - {sprint_name}

### Summary
- ✅ Critical Vulnerabilities: {count} (Max: 0)
- ✅ High Vulnerabilities: {count} (Max: 0)
- Overall Status: APPROVED | CONDITIONAL | REJECTED

### Vulnerabilities Found
{List with severity, component, fix required}

### Security Requirements for Deployment
{List any security controls that must be in place}

### Recommendations
{Security improvements for future sprints}
```
```

**After the agent completes:**
- Review security findings
- Address critical/high vulnerabilities if any

---

## Step 4: Deployment Readiness Assessment

**Call `/engineer` with the following task:**

```
## YOUR TASK: Assess Deployment Readiness

Evaluate whether the sprint changes are ready for deployment to production.

### Sprint Changes
{List completed features and code changes}

### Deployment Readiness Checklist

1. **Build & Package**
   - ✅ Build succeeds without errors
   - ✅ All tests pass
   - ✅ Artifacts generated correctly
   - ✅ Version incremented appropriately

2. **Database Migrations**
   - Migration scripts tested
   - Rollback scripts prepared
   - Data backup plan in place
   - Migration tested in staging

3. **Infrastructure**
   - Required infrastructure provisioned
   - Environment variables configured
   - Secrets management configured
   - Monitoring/alerting configured

4. **Documentation**
   - Release notes prepared
   - Deployment guide updated
   - API documentation updated (if applicable)
   - User documentation updated (if applicable)

5. **Rollback Plan**
   - Rollback procedure documented
   - Rollback tested in staging
   - Rollback decision criteria defined

### Deployment Environment
**Environments**: dev, uat, prod

### Output Format

Return deployment readiness assessment:
```json
{
  "ready_for_deployment": true|false,
  "environment": "staging|production",
  "blockers": [
    "Description of any deployment blockers"
  ],
  "deployment_tasks": [
    {
      "task": "Run database migration",
      "owner": "DevOps",
      "estimated_time": "10 minutes"
    }
  ],
  "rollback_ready": true|false,
  "recommendation": "deploy|fix_blockers|deploy_to_staging_first"
}
```
```

**After the agent completes:**
- Review deployment readiness
- Address any blockers

---

## Step 5: Sprint Closure Decision

**Call `/scrum-master` with the following task:**

```
## YOUR TASK: Recommend Sprint Closure Decision

Based on sprint metrics, acceptance tests, security review, and deployment readiness, recommend whether to close the sprint.

### Sprint Metrics
- Completion Rate: {completion_rate}%
- Completed: {completed_points}/{total_points} story points
- Items Not Done: {len(not_done)}

### Acceptance Test Results
{acceptance test summary from Step 2}

### Security Review
{security review summary from Step 3}

### Deployment Readiness
{deployment readiness summary from Step 4}

### Decision Criteria

**Close Sprint (Recommended if):**
- Completion rate >= 80%
- All acceptance tests pass OR failures are minor/acceptable
- No critical/high security vulnerabilities
- Deployment readiness confirmed OR sprint work not deployment-bound

**Extend Sprint (Recommended if):**
- Completion rate < 80% with critical items incomplete
- Acceptance test failures block deployment
- Critical security vulnerabilities need fixing

**Partial Closure (Recommended if):**
- Completion rate 60-80% with some items ready to deploy
- Some features deployable, others need more work

### Output Format

Return sprint closure recommendation:
```markdown
## Sprint Closure Recommendation - {sprint_name}

### Recommendation: CLOSE | EXTEND | PARTIAL_CLOSE

### Rationale
{Explain reasoning based on metrics and reviews}

### Items to Close
{List items that can be closed}

### Items to Carry Over
{List items that should move to next sprint}

### Action Items
1. {Required action 1}
2. {Required action 2}

### Sprint Goal Achievement
- Sprint Goal: {sprint_goal if available}
- Achieved: YES | NO | PARTIAL
```
```

**After the agent completes:**
- Review recommendation
- Prepare for human approval

---

## Step 6: Human Approval Gate

**Present to sprint stakeholders:**

```
════════════════════════════════════════════════════════════════════════════════
📊 SPRINT REVIEW SUMMARY - {sprint_name}
════════════════════════════════════════════════════════════════════════════════

📈 Completion: {completed_points}/{total_points} pts ({completion_rate:.1f}%)

🧪 Acceptance Tests: {acceptance_status}
  - Tests Run: {tests_run}
  - Passed: {tests_passed}
  - Failed: {tests_failed}

🔒 Security: {security_status}
  - Critical Vulns: {critical_count} (Max: 0)
  - High Vulns: {high_count} (Max: 0)

🚀 Deployment: {deployment_ready}

📋 Scrum Master Recommendation: {recommendation}

════════════════════════════════════════════════════════════════════════════════

Choose action:
1. ✅ Close Sprint - Mark sprint complete, deploy changes
2. ⏸️  Extend Sprint - Continue work for X more days
3. 🔀 Partial Close - Deploy completed work, carry over rest
4. ❌ Cancel - Review and re-plan

```

**Based on user decision:**

### Option 1: Close Sprint

```python
# Update sprint status
try:
    # Close completed items
    for item in completed:
        adapter.update_work_item(
            work_item_id=item['id'],
            fields={'System.State': 'Done'}
        )

    # Move incomplete items to next sprint
    next_sprint = input("Next sprint name (or 'backlog'): ")
    for item in not_done:
        new_iteration = f'Trusted AI Development Workbench\\{next_sprint}' if next_sprint != 'backlog' else ''
        adapter.update_work_item(
            work_item_id=item['id'],
            fields={'System.IterationPath': new_iteration}
        )

    print(f"✅ Sprint {sprint_name} closed successfully")
    print(f"   Completed: {len(completed)} items")
    print(f"   Moved to {next_sprint}: {len(not_done)} items")

except Exception as e:
    print(f"❌ Failed to close sprint: {e}")
```

### Option 2: Extend Sprint

```python
extension_days = input("Extend by how many days: ")
print(f"⏸️  Sprint {sprint_name} extended by {extension_days} days")
print(f"   Focus on completing: {[i['title'] for i in not_done[:5]]}")
```

### Option 3: Partial Close

```python
# User selects which items to deploy
print("Select items to deploy (comma-separated IDs):")
deploy_ids = input("Item IDs: ")
deploy_items = [int(x.strip()) for x in deploy_ids.split(',')]

# Close selected items
# Move others to next sprint
```

---

## Step 7: Generate Sprint Review Report

Save comprehensive report to `.claude/reports/sprint-reviews/`:

```markdown
# Sprint Review Report - {sprint_name}

**Date**: {current_date}
**Decision**: {user_decision}

## Sprint Metrics
- Total Items: {len(sprint_items)} ({total_points} pts)
- Completed: {len(completed)} ({completed_points} pts)
- Completion Rate: {completion_rate:.1f}%

## Acceptance Testing
{acceptance test summary}

## Security Review
{security review summary}

## Deployment Readiness
{deployment readiness summary}

## Sprint Closure
{closure details}

## Lessons Learned
{optional: what went well, what to improve}

## Next Sprint Planning
{items carried over, priorities}
```

---

## Agent Commands Used

| Step | Agent Command | Purpose |
|------|---------------|---------|
| 2 | `/tester` | Run acceptance tests |
| 3 | `/security-specialist` | Final security review |
| 4 | `/engineer` | Deployment readiness |
| 5 | `/scrum-master` | Sprint closure recommendation |

**Key**: Each agent command spawns a **fresh context window** via the Task tool.

---

## Configuration

**Work Tracking Platform:** azure-devops

**Quality Standards:**
- Test Coverage: >= 80%
- Critical Vulnerabilities: <= 0
- High Vulnerabilities: <= 0

---

*Generated by Trustable AI Workbench for trusted-ai-development-workbench*
*Replaces /sprint-completion (v1.x) with focus on acceptance testing and deployment readiness*