# Workflow Boundaries and Agent Orchestration

## Overview

This guide shows how workflows orchestrate agents across the software development lifecycle (SDLC), with clear boundaries between planning, execution, and review phases.

## SDLC Workflow Flow

```mermaid
graph TD
    A[Product Intake] -->|Creates Epics/Features| B[Architecture Planning]
    B -->|Designs System| C[Backlog Grooming]
    C -->|Breaks into Tasks| D[Sprint Planning]
    D -->|Approves Sprint| E[Sprint Execution]
    E -->|Completes Work| F[Sprint Review]
    F -->|Deployment Ready| G[Production Deployment]
    F -->|Feedback| H[Sprint Retrospective]
    H -->|Learnings| D

    style A fill:#e1f5fe
    style B fill:#fff3e0
    style C fill:#f3e5f5
    style D fill:#e8f5e9
    style E fill:#fff9c4
    style F fill:#fce4ec
    style G fill:#e0f2f1
    style H fill:#f1f8e9
```

## Agent Roles by SDLC Phase

```mermaid
graph LR
    subgraph "Planning Phase"
        BA[Business Analyst]
        ARCH[Architect]
        SE[Senior Engineer]
    end

    subgraph "Execution Phase"
        ENG[Engineer]
        TEST[Tester]
        SEC[Security Specialist]
    end

    subgraph "Review Phase"
        SM[Scrum Master]
        TEST2[Tester]
        SEC2[Security Specialist]
    end

    BA -->|Requirements| ARCH
    ARCH -->|Architecture| SE
    SE -->|Task Breakdown| ENG
    ENG -->|Implementation| TEST
    TEST -->|Validation| SEC
    SEC -->|Approval| SM
    SM -->|Retrospective| BA

    style BA fill:#4fc3f7
    style ARCH fill:#ffb74d
    style SE fill:#ba68c8
    style ENG fill:#81c784
    style TEST fill:#fff176
    style SEC fill:#f06292
    style SM fill:#4db6ac
    style TEST2 fill:#fff176
    style SEC2 fill:#f06292
```

## Workflow Diagrams

### 1. Product Intake → Architecture Planning

**Purpose:** Transform business requirements into technical architecture

```mermaid
sequenceDiagram
    participant U as User
    participant BA as /business-analyst
    participant ARCH as /architect
    participant SEC as /security-specialist
    participant ADO as Azure DevOps

    U->>BA: Analyze product requirements
    BA->>U: Prioritized features + business value
    U->>ARCH: Design architecture for top features
    ARCH->>U: System design + ADRs
    U->>SEC: Security review of architecture
    SEC->>U: Security requirements + risks
    U->>ADO: Create Epic work items
    ADO->>U: Epic IDs created
```

**Agents Used:**
- `/business-analyst` - Analyze requirements, score business value
- `/architect` - Design system, create ADRs, assess risks
- `/security-specialist` - Review architecture security

**Output:**
- Epics created in work tracking system
- Architecture documentation in `docs/architecture/`

---

### 2. Backlog Grooming

**Purpose:** Decompose Epics into Features and Tasks

```mermaid
sequenceDiagram
    participant U as User
    participant SE as /senior-engineer
    participant BA as /business-analyst
    participant ARCH as /architect
    participant ADO as Azure DevOps

    U->>ADO: Query for Epics (>30 pts)
    ADO->>U: Epic list
    U->>SE: Decompose Epic into Features/Tasks
    SE->>U: Feature/Task hierarchy + estimates
    U->>ADO: Create Features + Tasks with parent links
    ADO->>U: Work items created
    U->>BA: Analyze Features for business value
    BA->>U: Business value scores
    U->>ARCH: Review Features for technical feasibility
    ARCH->>U: Technical risk + dependencies
    U->>ADO: Update Features with scores/risks
    ADO->>U: Features ready for sprint
```

**Agents Used:**
- `/senior-engineer` - Decompose Epics, estimate story points
- `/business-analyst` - Score business value
- `/architect` - Assess technical feasibility

**Output:**
- Features and Tasks created with parent-child links
- Business value and technical risk scores assigned

---

### 3. Sprint Planning

**Purpose:** Select and commit to work for the sprint

```mermaid
sequenceDiagram
    participant U as User
    participant BA as /business-analyst
    participant ARCH as /architect
    participant SE as /senior-engineer
    participant SEC as /security-specialist
    participant SM as /scrum-master
    participant ADO as Azure DevOps

    U->>ADO: Query backlog (Ready state)
    ADO->>U: Ready features
    U->>BA: Prioritize features for sprint
    BA->>U: Prioritized list
    U->>ARCH: Review architecture implications
    ARCH->>U: Architecture guidance
    U->>SEC: Security review of planned work
    SEC->>U: Security requirements
    U->>SE: Estimate effort for sprint
    SE->>U: Capacity vs. proposed work
    U->>SM: Sprint approval recommendation
    SM->>U: Approved sprint plan
    U->>ADO: Move items to Sprint iteration
    ADO->>U: Sprint configured
```

**Agents Used:**
- `/business-analyst` - Prioritize features
- `/architect` - Provide architecture guidance
- `/security-specialist` - Security review
- `/senior-engineer` - Estimate effort vs. capacity
- `/scrum-master` - Sprint approval decision

**Output:**
- Sprint backlog configured in work tracking
- Work items assigned to sprint iteration

---

### 4. Sprint Execution (Implementation Cycle)

**Purpose:** Implement and test features iteratively

```mermaid
sequenceDiagram
    participant U as User
    participant ENG as /engineer
    participant TEST as /tester
    participant ADO as Azure DevOps
    participant GIT as Git

    loop For each task in sprint
        U->>ENG: Implement Task #{task_id}
        ENG->>U: Implementation complete
        U->>GIT: Run unit tests
        GIT->>U: Test results
        U->>TEST: Validate implementation
        alt Tests Pass & High Confidence
            TEST->>U: Validation: PASS (confidence: high)
            U->>GIT: Auto-commit implementation
            GIT->>U: Commit created
            U->>ADO: Update task state to Done
            ADO->>U: Task marked Done
        else Tests Fail
            TEST->>U: Fault attribution (CODE/TEST/SPEC)
            alt CODE fault
                U->>ADO: Create bug ticket (linked to task)
                ADO->>U: Bug created
            else TEST fault
                U->>TEST: Fix test implementation
            else SPEC fault
                U->>U: Escalate to product owner
            end
        end
    end
```

**Agents Used:**
- `/engineer` - Implement features/fixes
- `/tester` - Validate implementation, fault attribution

**Automated Steps:**
- Auto-commit on PASS + high confidence
- Auto-create bug tickets for CODE faults

**Output:**
- Implemented features committed to git
- Tasks marked Done in work tracking
- Bug tickets created for failures

---

### 5. Sprint Review

**Purpose:** Validate sprint deliverables ready for deployment

```mermaid
sequenceDiagram
    participant U as User
    participant TEST as /tester
    participant SEC as /security-specialist
    participant ENG as /engineer
    participant SM as /scrum-master
    participant ADO as Azure DevOps

    U->>ADO: Query sprint completion metrics
    ADO->>U: Completion stats
    U->>TEST: Run acceptance tests
    TEST->>U: Test results (pass/fail)
    U->>SEC: Final security review
    SEC->>U: Security status (vuln count)
    U->>ENG: Deployment readiness assessment
    ENG->>U: Deployment plan + blockers
    U->>SM: Sprint closure recommendation
    SM->>U: Close/Extend/Partial decision
    U->>U: Human approval gate
    alt Approve Close
        U->>ADO: Close sprint, move incomplete to next
        ADO->>U: Sprint closed
    else Extend Sprint
        U->>ADO: Extend sprint by X days
    else Partial Close
        U->>ADO: Deploy subset, carry over rest
    end
```

**Agents Used:**
- `/tester` - Run acceptance tests
- `/security-specialist` - Final security review
- `/engineer` - Deployment readiness
- `/scrum-master` - Closure recommendation

**Output:**
- Acceptance test report
- Security review report
- Deployment readiness assessment
- Sprint closure decision

---

## Agent Boundaries

### Business Analyst
- **Input:** Requirements, features, backlog items
- **Output:** Business value scores, prioritized lists
- **Used In:** Product intake, backlog grooming, sprint planning

### Architect
- **Input:** Features, system requirements, constraints
- **Output:** System design, ADRs, technical risk assessment
- **Used In:** Architecture planning, backlog grooming, sprint planning

### Senior Engineer
- **Input:** Epics, features, estimation requests
- **Output:** Task breakdown, story point estimates, capacity analysis
- **Used In:** Backlog grooming, sprint planning

### Engineer (Context-Driven)
- **Input:** Tasks, bugs, performance issues, deployment needs
- **Output:** Implemented code, CI/CD pipelines, optimized systems
- **Used In:** Sprint execution, deployment
- **Contexts:** Software dev, DevOps, Performance

### Tester (Context-Driven)
- **Input:** Implementations, test plans, failing tests
- **Output:** Test plans, validation results, fault attribution
- **Used In:** Sprint planning, sprint execution, sprint review
- **Contexts:** Test planning, adversarial testing, fault attribution

### Security Specialist
- **Input:** Architecture, code changes, deployment plans
- **Output:** Security requirements, vulnerability reports, approval
- **Used In:** Architecture planning, sprint planning, sprint review

### Scrum Master
- **Input:** Sprint metrics, completion status, blockers
- **Output:** Sprint recommendations, retrospective insights
- **Used In:** Sprint planning, sprint review, retrospectives

---

## Workflow Handoffs

### Epic → Features (Backlog Grooming)

```
┌─────────────────────────────────────────┐
│ INPUT: Epic (50 story points)           │
│ - Epic WI-1050: User Management         │
│ - Description: User CRUD + Auth         │
└─────────────────────────────────────────┘
                   ↓
          /senior-engineer
          (decomposition)
                   ↓
┌─────────────────────────────────────────┐
│ OUTPUT: Features + Tasks                │
│ - Feature WI-1051: User CRUD (15 pts)   │
│   - Task WI-1052: Create user (5 pts)   │
│   - Task WI-1053: Update user (5 pts)   │
│   - Task WI-1054: Delete user (5 pts)   │
│ - Feature WI-1055: Auth (20 pts)        │
│   - Task WI-1056: OAuth2 (8 pts)        │
│   - Task WI-1057: JWT (7 pts)           │
│   - Task WI-1058: Refresh (5 pts)       │
│ - Feature WI-1059: Permissions (15 pts) │
│   - Task WI-1060: RBAC (8 pts)          │
│   - Task WI-1061: ACLs (7 pts)          │
└─────────────────────────────────────────┘
```

### Task → Implementation (Sprint Execution)

```
┌─────────────────────────────────────────┐
│ INPUT: Task WI-1052: Create user (5pts) │
│ - Acceptance Criteria:                  │
│   - POST /api/users endpoint            │
│   - Validate email format               │
│   - Return 201 Created                  │
└─────────────────────────────────────────┘
                   ↓
           /engineer
        (implementation)
                   ↓
┌─────────────────────────────────────────┐
│ OUTPUT: Implementation                  │
│ - Code: src/api/users.py                │
│ - Tests: tests/test_users.py            │
│ - Commit: "Implement user creation"     │
└─────────────────────────────────────────┘
                   ↓
            /tester
         (validation)
                   ↓
┌─────────────────────────────────────────┐
│ OUTPUT: Validation                      │
│ - Status: PASS                          │
│ - Confidence: high                      │
│ - Coverage: 95%                         │
│ → Auto-commit triggered                 │
│ → Task marked Done in ADO               │
└─────────────────────────────────────────┘
```

---

## Key Principles

### 1. Fresh Context Per Agent

Each agent spawned via Task tool gets **fresh context window**:
- No context pollution from previous agents
- Explicit handoff of data between agents
- Workflow orchestrates agent sequence

### 2. External Verification

Workflows verify via **external source of truth** (Azure DevOps), not AI claims:
- After creating work items, query ADO to verify they exist
- After updating tasks, query ADO to verify state changed
- After commits, git log to verify commit created

### 3. Human Approval Gates

Critical decisions require **human approval**:
- Sprint planning → Human approves work items
- Sprint closure → Human approves deployment
- Architecture decisions → Human approves ADRs

### 4. State Checkpointing

Workflows save state after each step for **re-entrancy**:
- Checkpoint after Epic decomposition
- Checkpoint after Feature creation
- Checkpoint after Task implementation
- Resume from last checkpoint on failure

---

## Visual Summary

```
┌──────────────────────────────────────────────────────────────────────┐
│                        TRUSTABLE AI WORKFLOW                         │
│                                                                      │
│  Product Intake → Architecture → Backlog → Sprint → Execution       │
│       │               │           │         │         │             │
│       ↓               ↓           ↓         ↓         ↓             │
│   business-     architect    senior-     scrum-    engineer         │
│   analyst                   engineer    master     tester           │
│                                                   security           │
│                                                                      │
│  ┌────────┐   ┌────────┐   ┌────────┐   ┌────────┐   ┌────────┐  │
│  │ Epics  │ → │ Design │ → │Features│ → │ Sprint │ → │  Code  │  │
│  │        │   │  Docs  │   │ Tasks  │   │ Backlog│   │ Commits│  │
│  └────────┘   └────────┘   └────────┘   └────────┘   └────────┘  │
│                                                                      │
│       ↓                                                    ↓         │
│  Sprint Review ← Retrospective ← Deployment ← Validation            │
│       │                                          │                   │
│       ↓                                          ↓                   │
│   scrum-master                                tester                │
│   security-specialist                         security              │
│   engineer                                                          │
└──────────────────────────────────────────────────────────────────────┘
```

Each box represents a workflow phase, with agents working within that phase's boundaries.

---

## Conclusion

Workflows orchestrate agents through the SDLC with:
- **Clear boundaries** between planning, execution, and review
- **Fresh agent contexts** via Task tool
- **External verification** via work tracking system
- **Human approval** for critical decisions
- **State checkpointing** for re-entrancy

This architecture makes AI failures **visible and recoverable** through structured processes.
