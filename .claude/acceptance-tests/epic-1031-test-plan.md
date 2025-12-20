# EPIC Acceptance Test Plan: Streamline User Workflow Experience

## EPIC Overview
- **EPIC ID**: 1031
- **EPIC Title**: Streamline User Workflow Experience: Implement To-Be Workflow Flow
- **EPIC Summary**: Implement the proposed to-be workflow flow that streamlines user experience by consolidating agents, clarifying workflow boundaries, and enhancing sprint execution based on successful Gateway project patterns. This EPIC represents a significant refactoring of the Trustable AI framework's agent model and workflow structure to reduce complexity and improve user experience.

## Test Scope

### In Scope
- End-to-end workflow execution from project initialization to sprint completion
- Consolidated agent model (7 agents vs. 12+ previously)
- Workflow boundary clarity and phase separation
- Sprint execution improvements (test integration, deployment readiness)
- Safe-action permissions configuration
- Credential management via Keychain Core
- Problem-focused documentation experience
- Architecture planning workflow (replacing roadmap planning)
- Sprint review workflow with acceptance and deployment readiness

### Out of Scope
- Individual feature-level unit testing (covered by feature acceptance tests)
- Performance benchmarking (covered by performance testing)
- Third-party integration testing beyond work tracking platforms
- Legacy workflow compatibility (deprecated workflows not tested)
- Internal framework implementation details (whitebox testing)

## Test Strategy

### Test Levels
- **Acceptance Testing (blackbox)**: End-to-end user workflows validating EPIC objectives
- **Integration Testing**: Agent-to-agent interactions, workflow-to-platform integrations
- **User Experience Testing**: Documentation clarity, workflow interruption reduction, configuration ease

### Test Approach

This test plan employs blackbox acceptance testing from an end-user perspective. Tests simulate real-world usage scenarios starting from project initialization through sprint completion. Each test scenario validates that the streamlined workflow experience achieves the EPIC's objectives:

1. **Agent Consolidation Testing**: Verify that 7 consolidated agents replace the previous 12+ agent model without loss of functionality
2. **Workflow Clarity Testing**: Ensure workflow boundaries are clear and phase transitions are logical
3. **Configuration Simplification Testing**: Validate that safe-action permissions and credential management reduce workflow interruptions
4. **Documentation Usability Testing**: Confirm problem-focused documentation guides users effectively
5. **Sprint Execution Enhancement Testing**: Verify enhanced sprint review with acceptance testing and deployment readiness

Tests will be executed in a clean test environment with Azure DevOps and file-based work tracking adapters. Each scenario includes preconditions, step-by-step procedures, expected results, and pass criteria with external verification gates (VISION.md Pillar #2: External Source of Truth).

## Test Scenarios

### Scenario 1: Complete Workflow Flow - New Project Initialization to Sprint Completion

**Objective**: Validate the complete end-to-end workflow using consolidated agents and streamlined workflows.

**Preconditions**:
- Clean test environment with no existing .claude/ directory
- Trustable AI framework installed (pip install -e .)
- Azure DevOps organization accessible with valid credentials (az login)
- Sample vision/requirements document prepared

**Test Steps**:

1. **Framework Setup**
   ```bash
   mkdir test-project-workflow
   cd test-project-workflow
   trustable-ai init
   ```
   - Verify .claude/ directory created with default config.yaml
   - Verify prompted for project details (name, type, tech stack)

2. **Work Tracking Configuration**
   ```bash
   trustable-ai configure azure-devops
   ```
   - Provide organization URL and project name
   - Verify connection validation succeeds
   - Verify field mappings configured

3. **Agent and Workflow Rendering**
   ```bash
   trustable-ai agent render-all
   trustable-ai workflow render-all
   ```
   - Verify exactly 7 agents rendered to .claude/agents/: business-analyst, architect, senior-engineer, engineer, tester, security-specialist, scrum-master
   - Verify workflows rendered to .claude/commands/: context-generation, product-intake, architecture-planning, epic-breakdown, backlog-grooming, sprint-planning, daily-standup, sprint-execution, sprint-review, sprint-retrospective, update-context, workflow-resume

4. **Context Generation** (in Claude Code)
   ```
   /context-generation
   ```
   - Verify hierarchical CLAUDE.md files created
   - Verify README.md files populated with project context

5. **Product Intake** (in Claude Code)
   ```
   /product-intake
   ```
   - Provide sample vision document
   - Verify Business Analyst agent analyzes requirements
   - Verify Epic/Feature hierarchy created in Azure DevOps
   - Query Azure DevOps: Verify Epic and Feature work items exist with correct fields

6. **Architecture Planning** (in Claude Code)
   ```
   /architecture-planning
   ```
   - Select features from product intake
   - Verify Architect agent designs architecture
   - Verify Security Specialist reviews architecture
   - Verify docs/architecture/ directory contains design.md and ADRs
   - Verify features tagged with 'architecture-reviewed' in Azure DevOps

7. **Backlog Grooming** (in Claude Code)
   ```
   /backlog-grooming
   ```
   - Verify Senior Engineer breaks down features into tasks
   - Verify task work items created with story points in Azure DevOps
   - Verify acceptance criteria refined

8. **Sprint Planning** (in Claude Code)
   ```
   /sprint-planning
   ```
   - Verify Scrum Master facilitates planning
   - Verify sprint iteration created in Azure DevOps
   - Verify work items assigned to sprint
   - Verify sprint plan document generated in .claude/reports/

9. **Sprint Execution** (in Claude Code)
   ```
   /sprint-execution
   ```
   - Verify Engineer implements tasks
   - Verify Tester evaluates tests for completeness
   - Verify work item status updated to "In Progress" → "Completed" in Azure DevOps
   - Verify code changes committed

10. **Sprint Review** (in Claude Code)
    ```
    /sprint-review
    ```
    - Verify Tester runs acceptance tests
    - Verify Security Specialist performs vulnerability review
    - Verify Engineer assesses deployment readiness
    - Verify Scrum Master generates sprint closure recommendation
    - Verify test reports attached to EPIC work items in Azure DevOps
    - Verify sprint review report saved to .claude/reports/sprint-reviews/

11. **Sprint Retrospective** (in Claude Code)
    ```
    /sprint-retrospective
    ```
    - Verify retrospective metrics generated
    - Verify learnings captured in .claude/learnings/
    - Verify retrospective report saved

**Expected Results**:
- Complete workflow executes without errors
- All artifacts created in expected locations (work tracking platform, file system)
- Work items created, updated, and closed correctly in Azure DevOps
- Reports generated in .claude/reports/ directories
- Learnings captured in .claude/learnings/
- State checkpoints saved in .claude/workflow-state/

**Pass Criteria**:
- [ ] Framework initialization completes successfully with config.yaml
- [ ] Azure DevOps connection validated and configured
- [ ] Exactly 7 agents rendered (no more, no less)
- [ ] All 12 workflows rendered to .claude/commands/
- [ ] Product intake creates Epic/Feature work items verified in Azure DevOps
- [ ] Architecture planning creates docs/architecture/ artifacts and tags features
- [ ] Backlog grooming creates task work items with story points in Azure DevOps
- [ ] Sprint planning creates sprint iteration and assigns work items in Azure DevOps
- [ ] Sprint execution updates work item states to "Completed" in Azure DevOps
- [ ] Sprint review generates and attaches test reports to EPICs in Azure DevOps
- [ ] Sprint retrospective generates report and captures learnings
- [ ] No workflow interruptions due to missing permissions or credentials

---

### Scenario 2: Agent Consolidation Validation

**Objective**: Verify that the consolidated 7-agent model provides equivalent functionality to the previous 12+ agent model.

**Preconditions**:
- Trustable AI framework installed
- Project initialized with .claude/config.yaml
- Agents and workflows rendered

**Test Steps**:

1. **Verify Agent Count**
   ```bash
   ls .claude/agents/ | wc -l
   ```
   - Count agent .md files in .claude/agents/

2. **Verify Agent Names**
   ```bash
   ls .claude/agents/
   ```
   - List all agent files and confirm names match to-be agent list

3. **Verify Agent Role Coverage**
   - Open each agent .md file and verify role description matches to-be specification:
     - business-analyst.md: Requirements analysis, prioritization
     - architect.md: Technical architecture, risk assessment (replaces project-architect)
     - senior-engineer.md: Task breakdown, story point estimation
     - engineer.md: Implementation, unit/integration testing (replaces software-developer, devops-engineer, performance-engineer)
     - tester.md: Test planning, acceptance testing, falsifiability (replaces adversarial-tester, falsifiability-prover, spec-driven-tester, test-arbitrator)
     - security-specialist.md: Security review, vulnerability analysis
     - scrum-master.md: Workflow coordination, sprint management

4. **Test Agent Functionality**
   - Execute each workflow that uses consolidated agents
   - Verify workflows complete successfully with consolidated agents
   - Verify no missing functionality from deprecated agents

5. **Verify Config Alignment**
   - Open .claude/config.yaml
   - Verify enabled_agents list contains exactly 7 agents:
     ```yaml
     enabled_agents:
       - business-analyst
       - architect
       - senior-engineer
       - engineer
       - tester
       - security-specialist
       - scrum-master
     ```

**Expected Results**:
- Exactly 7 agent files in .claude/agents/
- Agent names match to-be specification
- Each agent's role description covers responsibilities from deprecated agents
- All workflows execute successfully with consolidated agents
- No functionality gaps identified

**Pass Criteria**:
- [ ] Agent count equals 7 (verified by file count)
- [ ] Agent names match: business-analyst, architect, senior-engineer, engineer, tester, security-specialist, scrum-master
- [ ] Architect agent replaces project-architect functionality
- [ ] Engineer agent covers software-developer, devops-engineer, performance-engineer responsibilities
- [ ] Tester agent covers adversarial-tester, falsifiability-prover, spec-driven-tester, test-arbitrator responsibilities
- [ ] All workflows from Scenario 1 execute without errors
- [ ] Config.yaml enabled_agents contains exactly 7 agents

---

### Scenario 3: Workflow Boundary Clarity

**Objective**: Verify that workflow boundaries are clear, phases are distinct, and transitions are logical.

**Preconditions**:
- Trustable AI framework installed
- Project initialized with workflows rendered

**Test Steps**:

1. **Verify Workflow Naming and Purpose**
   - List all workflows in .claude/commands/
   - For each workflow, verify:
     - Name clearly indicates purpose
     - Workflow markdown file contains "Workflow Overview" section
     - "Where This Fits" section showing workflow position in lifecycle

2. **Test Phase Separation**
   - Execute workflows in sequence:
     - Phase 1: /context-generation
     - Phase 2: /product-intake
     - Phase 3: /architecture-planning, /epic-breakdown, /backlog-grooming
     - Phase 4: /sprint-planning, /daily-standup, /sprint-execution
     - Phase 5: /sprint-review, /sprint-retrospective
   - Verify each phase produces artifacts consumed by next phase
   - Verify no circular dependencies between workflows

3. **Verify Architecture Planning Replaces Roadmap Planning**
   - Verify /architecture-planning workflow exists
   - Verify /roadmap-planning workflow deprecated or removed
   - Execute /architecture-planning
   - Verify output focuses on technical architecture (not business roadmap)
   - Verify architecture artifacts saved to docs/architecture/

4. **Verify Sprint Review Focus**
   - Execute /sprint-review workflow
   - Verify workflow includes:
     - Step 1.5: Identify EPICs for testing
     - Step 1.6: Retrieve test plans from work items
     - Step 1.7: Execute tests and generate reports
     - Step 1.8: Attach test reports to EPIC work items
     - Acceptance testing (Step 2)
     - Security review (Step 3)
     - Deployment readiness assessment (Step 4)
   - Verify workflow does NOT include business roadmap planning

5. **Test Workflow Resume**
   - Simulate workflow interruption during /sprint-planning
   - Execute /workflow-resume
   - Verify list of incomplete workflows displayed
   - Resume interrupted workflow
   - Verify workflow continues from last checkpoint

**Expected Results**:
- All workflows have clear names and purpose statements
- "Where This Fits" diagrams show workflow position in lifecycle
- Workflows execute in logical sequence without circular dependencies
- Architecture planning produces technical architecture docs
- Sprint review includes acceptance testing and deployment readiness
- Workflow resume successfully recovers interrupted workflows

**Pass Criteria**:
- [ ] All 12 workflows present in .claude/commands/
- [ ] Each workflow has "Workflow Overview" and "Where This Fits" sections
- [ ] Workflows execute in phase order: context → product → architecture → sprint
- [ ] /architecture-planning exists and /roadmap-planning deprecated
- [ ] /architecture-planning produces docs/architecture/ artifacts
- [ ] /sprint-review includes Steps 1.5-1.8 (EPIC test plan integration)
- [ ] /workflow-resume successfully lists and resumes interrupted workflows
- [ ] No circular dependencies detected between workflows

---

### Scenario 4: Safe-Action Permissions Configuration

**Objective**: Verify that default safe-action permissions reduce workflow interruptions.

**Preconditions**:
- Trustable AI framework installed
- Project initialized

**Test Steps**:

1. **Verify Permissions Generated**
   ```bash
   trustable-ai init
   ```
   - Verify .claude/settings.local.json created
   - Verify safeActions section present
   - Verify safeActionPatterns section present

2. **Verify Permission Patterns**
   - Open .claude/settings.local.json
   - Verify safe-action patterns include:
     - File read operations (cat, head, tail)
     - Directory listing (ls, find)
     - Git read operations (git status, git diff, git log)
     - Python script execution with project-specific paths
     - Work tracking CLI operations (az boards, etc.)
   - Verify patterns use wildcards for flexibility

3. **Test Workflow Execution Without Interruptions**
   - Execute /product-intake workflow
   - Monitor for permission prompts
   - Verify no prompts for safe operations (reading work items, listing files, etc.)
   - Verify workflow completes without manual approvals

4. **Test Permission Scoping**
   - Verify permissions scoped to project directory (not global)
   - Verify dangerous operations (rm -rf, etc.) NOT in safe-action list
   - Verify write operations require approval unless explicitly safe

5. **Test Credential Management Integration**
   - Verify .claude/config.yaml contains credentials_source configuration
   - Execute workflow requiring Azure DevOps access
   - Verify credentials sourced from CLI (az login) without prompts
   - Verify no credential exposure in logs or state files

**Expected Results**:
- .claude/settings.local.json generated with safeActions and safeActionPatterns
- Safe-action patterns cover common read and query operations
- Workflows execute without interruption for safe operations
- Permissions scoped to project directory
- Dangerous operations NOT marked as safe
- Credentials sourced securely without prompts

**Pass Criteria**:
- [ ] .claude/settings.local.json exists after init
- [ ] safeActions section contains file read, git read, work tracking read operations
- [ ] safeActionPatterns section contains wildcarded patterns for project paths
- [ ] /product-intake executes without permission prompts for work tracking queries
- [ ] /sprint-planning executes without permission prompts for work item creation
- [ ] Dangerous operations (rm, dd, etc.) NOT in safeActions
- [ ] credentials_source in config.yaml uses CLI authentication
- [ ] No credentials exposed in .claude/workflow-state/ or .claude/reports/

---

### Scenario 5: Problem-Focused Documentation Experience

**Objective**: Verify that documentation is problem-focused and guides users effectively.

**Preconditions**:
- Trustable AI framework installed
- Documentation files accessible

**Test Steps**:

1. **Verify VISION.md Clarity**
   - Read VISION.md
   - Verify document structure:
     - "The Problem We Solve" section clearly describes AI unreliability
     - "Our Solution" section explains SDLC-driven approach
     - Warning at top for AI agents (anti-patterns vs. solutions)
   - Verify problem descriptions are concrete with examples
   - Verify solutions reference specific framework features

2. **Verify CLAUDE.md Clarity**
   - Read CLAUDE.md (project root)
   - Verify structure:
     - "Overview" section with current state and tech stack
     - "Development Commands" section with categorized examples
     - "Architecture" section explaining core components
     - "Common Workflows" section with practical examples
   - Verify commands use actual syntax (not placeholders)
   - Verify examples reference real project paths

3. **Verify .claude/CLAUDE.md Clarity**
   - Read .claude/CLAUDE.md
   - Verify purpose statement explains runtime state management
   - Verify "Key Components" section lists actual directories
   - Verify "Important Notes" section highlights common pitfalls

4. **Verify Workflow Documentation**
   - Open any workflow .md file (e.g., .claude/commands/sprint-planning.md)
   - Verify workflow includes:
     - Clear purpose statement
     - "Where This Fits" lifecycle diagram
     - Step-by-step instructions with code examples
     - Agent commands with expected outputs
     - Success criteria checklist
   - Verify code examples are executable (not pseudocode)

5. **Test Documentation Usability**
   - Follow CLAUDE.md instructions to install and initialize project
   - Follow workflow documentation to execute /product-intake
   - Verify documentation accuracy (no broken references, outdated commands)
   - Verify problem-focused sections help diagnose issues

**Expected Results**:
- VISION.md clearly describes problems and solutions
- CLAUDE.md provides practical commands and workflows
- .claude/CLAUDE.md explains runtime directory purpose
- Workflow documentation includes lifecycle context and executable examples
- Documentation accurate and up-to-date with no broken references

**Pass Criteria**:
- [ ] VISION.md contains "⚠️ IMPORTANT: For AI Agents" warning section
- [ ] VISION.md "The Problem We Solve" lists 5+ concrete problems with examples
- [ ] VISION.md "Our Solution" references specific framework features (state management, verification gates, etc.)
- [ ] CLAUDE.md "Development Commands" section uses executable syntax
- [ ] CLAUDE.md examples reference actual project paths (not placeholders)
- [ ] .claude/CLAUDE.md purpose statement explains runtime state management problem
- [ ] Workflow .md files include "Where This Fits" lifecycle diagram
- [ ] Workflow code examples are executable (copy-paste-run)
- [ ] Following CLAUDE.md instructions successfully initializes project
- [ ] Following workflow docs successfully executes /product-intake

---

### Scenario 6: Sprint Review Enhanced Workflow

**Objective**: Verify enhanced sprint review workflow integrates acceptance testing and deployment readiness.

**Preconditions**:
- Project initialized with work tracking configured
- Sprint executed with completed EPICs
- Test plans attached to EPIC work items

**Test Steps**:

1. **Prepare Test Environment**
   - Create test EPIC work item in Azure DevOps
   - Generate acceptance test plan for EPIC
   - Attach test plan to EPIC work item
   - Mark EPIC as part of current sprint

2. **Execute Sprint Review - EPIC Identification**
   ```
   /sprint-review
   ```
   - Verify Step 1.5 executes: "Identify EPICs for Testing"
   - Verify query to Azure DevOps for Epic work items in sprint
   - Verify EPICs with attached test plans identified
   - Verify EPICs without test plans excluded with warning

3. **Execute Sprint Review - Test Plan Retrieval**
   - Verify Step 1.6 executes: "Retrieve Test Plans from Work Items"
   - For Azure DevOps: Verify test plan downloaded from attachment
   - For file-based: Verify test plan read from local filesystem
   - Verify test plan content validated (required sections present)
   - Verify retrieval failures logged with reasons

4. **Execute Sprint Review - Test Execution**
   - Verify Step 1.7 executes: "Execute Tests and Generate Reports"
   - Verify qa-tester agent spawned in execution mode
   - Verify test execution results returned (JSON structure)
   - Verify test report generated in markdown format
   - Verify test report written to .claude/acceptance-tests/epic-{id}-test-report.md

5. **Execute Sprint Review - Report Attachment**
   - Verify Step 1.8 executes: "Attach Test Reports to EPIC Work Items"
   - For Azure DevOps: Verify test report attached to EPIC work item
   - Verify attachment existence verified using Azure CLI
   - Verify attachment failures halt workflow with error message

6. **Execute Sprint Review - Acceptance Testing**
   - Verify Step 2 executes: Tester runs acceptance tests
   - Verify acceptance test results returned (JSON format)
   - Verify quality gates evaluated (coverage, vulnerabilities, etc.)

7. **Execute Sprint Review - Security Review**
   - Verify Step 3 executes: Security Specialist performs final review
   - Verify vulnerability scan results included
   - Verify security report generated

8. **Execute Sprint Review - Deployment Readiness**
   - Verify Step 4 executes: Engineer assesses deployment readiness
   - Verify deployment readiness checklist evaluated
   - Verify deployment blockers identified

9. **Execute Sprint Review - Sprint Closure**
   - Verify Step 5 executes: Scrum Master recommends closure decision
   - Verify recommendation includes EPIC test results
   - Verify recommendation considers deployment readiness

10. **Execute Sprint Review - Human Approval**
    - Verify Step 6 presents summary to user
    - Verify summary includes EPIC test report counts
    - Verify summary includes deployment readiness status

**Expected Results**:
- Sprint review workflow completes all steps without errors
- EPICs identified from work tracking platform
- Test plans retrieved from EPIC attachments
- Tests executed and reports generated
- Reports attached to EPICs in work tracking platform
- Attachment verified before proceeding
- Sprint closure recommendation includes EPIC test results and deployment readiness

**Pass Criteria**:
- [ ] Step 1.5 queries Azure DevOps for Epic work items in sprint
- [ ] EPICs with test plans identified correctly
- [ ] EPICs without test plans excluded with warning
- [ ] Step 1.6 retrieves test plans from EPIC attachments
- [ ] Test plan content validated (EPIC, FEATURE, Test Case sections present)
- [ ] Step 1.7 generates test reports for all EPICs with test plans
- [ ] Test reports written to .claude/acceptance-tests/
- [ ] Step 1.8 attaches test reports to EPIC work items in Azure DevOps
- [ ] Attachment verified using Azure CLI before workflow proceeds
- [ ] Attachment failures halt workflow with error (VISION.md Pillar #2: External Source of Truth)
- [ ] Sprint closure recommendation includes EPIC test execution results
- [ ] Sprint summary displays EPIC test report counts and attachment status

---

### Scenario 7: State Recovery and Re-entrancy

**Objective**: Verify workflow state persistence and recovery from interruptions.

**Preconditions**:
- Project initialized with workflows rendered
- Work tracking configured

**Test Steps**:

1. **Simulate Workflow Interruption**
   - Start /sprint-planning workflow
   - Manually interrupt workflow mid-execution (Ctrl+C or session timeout simulation)
   - Verify workflow state saved to .claude/workflow-state/

2. **List Incomplete Workflows**
   ```
   /workflow-resume
   ```
   - Verify incomplete workflow listed with ID, workflow name, current step
   - Verify last checkpoint timestamp displayed

3. **Resume Workflow**
   - Select workflow to resume from list
   - Verify workflow continues from last checkpoint (not from beginning)
   - Verify state data loaded correctly (work items, decisions, etc.)
   - Verify workflow completes successfully

4. **Verify State File Structure**
   - Open .claude/workflow-state/{workflow}-{id}.json
   - Verify structure contains:
     - workflow: workflow name
     - current_step: step number
     - completed_steps: array of completed step numbers
     - workflow-specific state (work_items_created, decisions_made, etc.)

5. **Test Multiple Workflow Interruptions**
   - Interrupt /product-intake workflow
   - Interrupt /backlog-grooming workflow
   - Execute /workflow-resume
   - Verify both workflows listed
   - Resume each workflow individually
   - Verify both complete successfully

**Expected Results**:
- Workflow state saved to .claude/workflow-state/ after each step
- /workflow-resume lists all incomplete workflows
- Resuming workflow continues from last checkpoint
- State data loaded correctly
- Multiple interrupted workflows can be resumed independently

**Pass Criteria**:
- [ ] Interrupted workflow state saved to .claude/workflow-state/
- [ ] State file contains workflow, current_step, completed_steps fields
- [ ] /workflow-resume lists interrupted workflows with IDs and timestamps
- [ ] Resuming workflow continues from current_step (not step 1)
- [ ] Workflow completes successfully after resume
- [ ] Multiple interrupted workflows listed and resumable independently
- [ ] State cleanup command available (trustable-ai state cleanup)

---

## Quality Gates

All test scenarios must pass the following quality gates before EPIC acceptance:

### Functional Quality Gates
- [ ] All 7 consolidated agents render correctly and cover full functionality
- [ ] All 12 workflows execute successfully in correct phase order
- [ ] Work items created, updated, and verified in Azure DevOps (external source of truth)
- [ ] Architecture planning produces docs/architecture/ artifacts
- [ ] Sprint review integrates EPIC acceptance testing (Steps 1.5-1.8)
- [ ] Test reports attached and verified in work tracking platform
- [ ] State persistence enables workflow resume from interruptions

### Configuration Quality Gates
- [ ] Safe-action permissions reduce workflow interruptions (no prompts for safe operations)
- [ ] Credential management uses secure sources (CLI authentication)
- [ ] No credentials exposed in state files or reports

### Documentation Quality Gates
- [ ] VISION.md clearly describes problems and solutions
- [ ] CLAUDE.md provides executable commands and examples
- [ ] Workflow documentation includes lifecycle context diagrams
- [ ] Code examples in docs are executable (not pseudocode)

### User Experience Quality Gates
- [ ] Complete workflow (init to sprint completion) executes without errors
- [ ] Workflow boundaries clear with distinct phases
- [ ] No functionality gaps from agent consolidation
- [ ] Documentation guides users effectively through workflows

## Test Environment

### Hardware Requirements
- Workstation with 8GB+ RAM
- 20GB+ available disk space
- Internet connectivity for work tracking platform access

### Software Requirements
- Python 3.9+ installed
- Git installed
- Azure CLI installed and authenticated (az login)
- Claude Code CLI installed
- Trustable AI framework installed (pip install -e .)

### Work Tracking Platform
- Azure DevOps organization with project access
- File-based work tracking (for offline testing)

### Test Data
- Sample vision/requirements document (500-1000 words)
- Sample tech stack configuration (Python, pytest, Docker)
- Sample EPIC with attached test plan
- Sample sprint with 5-10 work items

## Test Data

### Sample Vision Document
```
# Project Vision: User Authentication System

## Overview
Build a secure user authentication system with registration, login, password reset, and MFA support.

## Features
1. User Registration: Email/password with email verification
2. User Login: Secure authentication with session management
3. Password Reset: Email-based password recovery
4. Multi-Factor Authentication: SMS and authenticator app support

## Acceptance Criteria
- Registration: User receives verification email within 30 seconds
- Login: Session created with JWT token, 15-minute expiration
- Password Reset: Reset link expires after 1 hour
- MFA: Supports TOTP authenticator apps
```

### Sample EPIC Test Plan
```
# EPIC Acceptance Test Plan: User Authentication System

## Test Cases
- TC-001: User can register with valid email/password
- TC-002: User receives verification email
- TC-003: User can login with verified credentials
- TC-004: User can reset password via email
- TC-005: User can enable MFA
```

### Sample Configuration
```yaml
project:
  name: test-authentication-system
  type: web-application
  tech_stack:
    languages: ["Python"]
    frameworks: ["FastAPI", "pytest"]
    platforms: ["Docker"]

work_tracking:
  platform: azure-devops
  organization: https://dev.azure.com/test-org
  project: Test Project
  credentials_source: cli
```

## Risks and Mitigation

### Risk 1: Azure DevOps Connection Failures
**Impact**: High - Blocks work tracking integration tests
**Likelihood**: Medium - Depends on network and authentication
**Mitigation**:
- Verify az login before test execution
- Provide file-based work tracking fallback
- Include connection validation in test preconditions
- Document Azure DevOps setup in test environment section

### Risk 2: Agent Consolidation Functionality Gaps
**Impact**: High - Violates EPIC objective
**Likelihood**: Low - Design reviewed and approved
**Mitigation**:
- Comprehensive agent role coverage testing (Scenario 2)
- Map deprecated agent responsibilities to consolidated agents
- Execute all workflows to verify no missing functionality
- Document agent capability matrix for verification

### Risk 3: Test Plan Attachment/Retrieval Failures
**Impact**: Medium - Sprint review workflow incomplete
**Likelihood**: Medium - Platform-specific attachment handling
**Mitigation**:
- Test both Azure DevOps and file-based attachment flows
- Verify attachment existence after upload (external verification)
- Implement clear error messages for attachment failures
- Provide manual attachment fallback instructions

### Risk 4: Documentation Drift
**Impact**: Medium - Reduces documentation usability
**Likelihood**: Medium - Documentation updated during EPIC
**Mitigation**:
- Test documentation by following instructions exactly
- Verify code examples are executable
- Check for broken references and outdated commands
- Update documentation as part of test execution

### Risk 5: State File Corruption
**Impact**: Medium - Workflow resume failures
**Likelihood**: Low - JSON serialization well-tested
**Mitigation**:
- Validate state file JSON structure in tests
- Test multiple interrupt/resume cycles
- Implement state file validation in framework
- Provide state cleanup command for corrupted files

### Risk 6: Permission Configuration Complexity
**Impact**: Low - Users may need to adjust permissions
**Likelihood**: Medium - Environment-specific variations
**Mitigation**:
- Test with default safe-action configuration
- Document permission customization in docs
- Provide permission troubleshooting guide
- Test both permissive and restrictive permission scenarios
