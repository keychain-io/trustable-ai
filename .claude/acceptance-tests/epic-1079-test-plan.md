# EPIC Acceptance Test Plan: Add Blackbox Acceptance Testing

## EPIC Overview
- **EPIC ID**: 1079
- **EPIC Title**: Add blackbox acceptance testing to sprint workflows
- **EPIC Summary**: Integrate blackbox acceptance testing into sprint planning and execution workflows to ensure EPICs have comprehensive acceptance test plans and tests are executed during sprint review.
- **State**: Removed

## Test Scope

### In Scope
- Test plan generation during sprint planning workflow
- Test plan attachment/linking to EPIC work items
- Test execution during sprint review workflow
- Test report generation and attachment
- Verification gates in workflows
- Tester agent review of test plan quality

### Out of Scope
- Unit testing (covered by engineer/tester agents)
- Performance testing (separate EPIC)
- Security testing (handled by security-specialist agent)
- Test infrastructure setup (prerequisite)

## Test Strategy

### Test Levels
- **Acceptance Testing (blackbox)**: End-to-end EPIC validation
- **Integration Testing**: Workflow-to-platform integration (Azure DevOps)
- **Workflow Testing**: Verification gate execution

### Test Approach

This test plan validates that acceptance testing is properly integrated into sprint workflows. Tests verify that:
1. EPICs receive comprehensive test plans during sprint planning
2. Test plans are stored and linked to work items
3. Tests execute during sprint review
4. Test reports are attached to EPICs
5. Verification gates prevent progression without test confirmation

## Test Scenarios

### Scenario 1: Sprint Planning Test Plan Generation

**Objective**: Verify test plans are generated for EPICs during sprint planning.

**Preconditions**:
- Sprint 6 initialized
- EPICs identified in sprint scope (#1031, #1079)
- QA-tester agent available

**Test Steps**:
1. Execute /sprint-planning workflow
2. Verify Step 1.5 executes: Extract EPICs from sprint scope
3. Verify Step 1.6 spawns qa-tester agent for each EPIC
4. Verify test plans generated in markdown format
5. Verify test plans written to .claude/acceptance-tests/ directory
6. Verify Step 1.7 attaches test plans to EPIC work items

**Expected Results**:
- Test plans generated for all EPICs in sprint
- Files created: epic-{id}-test-plan.md
- Test plans attached to EPIC work items in Azure DevOps
- Attachment verified via Azure CLI

**Pass Criteria**:
- [ ] EPICs extracted correctly from prioritized backlog
- [ ] QA-tester agent spawned for each EPIC
- [ ] Test plans written to .claude/acceptance-tests/
- [ ] Test plans attached to Azure DevOps work items
- [ ] Attachment verified (external source of truth)

### Scenario 2: Sprint Review Test Execution

**Objective**: Verify tests execute during sprint review and reports are attached.

**Preconditions**:
- Sprint with completed EPICs
- Test plans attached to EPIC work items
- Acceptance test environment ready

**Test Steps**:
1. Execute /sprint-review workflow
2. Verify Step 1.5 identifies EPICs for testing
3. Verify Step 1.6 retrieves test plans from work items
4. Verify Step 1.7 executes tests and generates reports
5. Verify Step 1.8 attaches test reports to EPICs
6. Verify attachment verified before workflow proceeds

**Expected Results**:
- EPICs identified from work tracking platform
- Test plans retrieved successfully
- Tests executed by tester agent
- Test reports generated and attached
- Attachment verified

**Pass Criteria**:
- [ ] EPICs identified via Azure DevOps query
- [ ] Test plans downloaded from attachments
- [ ] Tests executed without errors
- [ ] Test reports written to .claude/acceptance-tests/epic-{id}-test-report.md
- [ ] Reports attached to EPIC work items
- [ ] Attachment verified (halt on failure)

### Scenario 3: Verification Gates

**Objective**: Verify workflow verification gates prevent progression without test confirmation.

**Preconditions**:
- Sprint execution workflow active
- Tasks with pending test validation

**Test Steps**:
1. Execute /sprint-execution workflow
2. Implement a task (Step A2)
3. Verify tester validation required before marking Done (Step A4)
4. Simulate test failure
5. Verify task NOT marked Done without tester confirmation
6. Fix issues and get tester confirmation
7. Verify task marked Done only after confirmation

**Expected Results**:
- Tasks remain "In Progress" until tester confirms
- Test failures prevent task completion
- Tester confirmation required to mark Done

**Pass Criteria**:
- [ ] Task implementation proceeds normally
- [ ] Test validation step executes before marking Done
- [ ] Failed tests prevent task completion
- [ ] Tester confirmation gates task completion
- [ ] Task state updated only after confirmation

### Scenario 4: Tester Agent Test Plan Review

**Objective**: Verify tester agent reviews test plans for quality and creates deficiency bugs.

**Preconditions**:
- Test plans generated for EPICs
- QA-tester agent configured

**Test Steps**:
1. Generate test plan with intentional deficiencies:
   - Missing acceptance criteria
   - Non-falsifiable tests
   - Incomplete coverage
2. Execute test plan review workflow
3. Verify tester agent identifies deficiencies
4. Verify BUG work items created for each deficiency
5. Verify bugs linked to parent EPIC

**Expected Results**:
- Tester identifies missing/deficient test criteria
- BUG work items created in Azure DevOps
- Bugs linked to parent EPIC
- Deficiency descriptions clear and actionable

**Pass Criteria**:
- [ ] Tester agent reviews test plan structure
- [ ] Missing acceptance criteria identified
- [ ] Non-falsifiable tests flagged
- [ ] BUG work items created for deficiencies
- [ ] Bugs linked to parent EPIC in Azure DevOps

## Quality Gates

- [ ] Test plans generated during sprint planning
- [ ] Test plans attached to EPIC work items
- [ ] Test execution integrated into sprint review
- [ ] Test reports attached to EPICs
- [ ] Verification gates prevent progression without tests
- [ ] Tester agent reviews test plan quality
- [ ] All attachments verified (external source of truth)

## Test Environment

- Trustable AI framework installed
- Azure DevOps access configured
- QA-tester agent available
- Sprint workflows rendered

## Test Data

- 2 EPICs for testing (#1031, #1079)
- Sample acceptance criteria
- Test environment configuration

## Risks and Mitigation

**Risk**: Azure DevOps attachment API failures
**Mitigation**: Implement retry logic, verify after upload, provide file-based fallback

**Risk**: Test plan quality varies
**Mitigation**: Tester agent review step, deficiency tracking, quality guidelines

**Risk**: Test execution timeouts
**Mitigation**: Timeout configuration, parallel execution, partial results handling
