# Context-Driven Agent Behavior

## Principle

**Context-driven agents adapt their behavior based on the task context**, rather than having fixed, specialized roles.

Traditional approach (v1.x): 12 specialized agents, each with narrow focus
```
/software-developer → Only implements features
/devops-engineer → Only does infrastructure
/performance-engineer → Only optimizes performance
```

Context-driven approach (v2.0): 7 adaptive agents, behavior determined by task
```
/engineer + feature task → Implements features
/engineer + deployment task → Configures infrastructure
/engineer + performance task → Optimizes performance
```

## Why Context-Driven?

### Problem with Specialized Agents

1. **Cognitive Overload:** Remembering which of 12 agents to use for each task
2. **Artificial Boundaries:** Real tasks don't map cleanly to single roles
3. **Agent Proliferation:** More agents = more maintenance, more complexity
4. **Workflow Fragility:** Hard-coding specific agent names in workflows

### Benefits of Context-Driven

1. **Simpler Mental Model:** 7 agents vs 12 agents
2. **Natural Task Mapping:** Pick agent by SDLC phase, not implementation detail
3. **Flexible Behavior:** Agent adapts to task nuances automatically
4. **Future-Proof Workflows:** Workflows don't break when agent capabilities evolve

## How It Works

### Agent Prompt Structure

Context-driven agents have **conditional sections** in their prompts:

```markdown
# Engineer Agent

## Responsibilities (Context-Driven)

### Core Engineering (All Tasks)
1. Break down features into implementable tasks
2. Estimate complexity and effort
3. Implement features with clean, tested code
4. Review code for quality
5. Manage technical debt

### DevOps & Infrastructure (When task involves deployment/infrastructure)
6. Design and implement CI/CD pipelines
7. Manage infrastructure as code (IaC)
8. Configure monitoring and alerting
9. Implement deployment automation
10. Manage secrets and configuration

### Performance Engineering (When task involves performance/optimization)
11. Analyze application performance
12. Identify and fix bottlenecks
13. Design and execute load tests
14. Optimize database queries
15. Implement caching strategies
```

### Context Detection

The agent's behavior is determined by **keywords in the task description**:

| Keywords | Activated Section | Agent Behavior |
|----------|-------------------|----------------|
| deploy, CI/CD, infrastructure, docker, kubernetes | DevOps & Infrastructure | Acts as DevOps engineer |
| performance, optimize, slow, latency, throughput | Performance Engineering | Acts as Performance engineer |
| feature, implement, bug, fix, refactor | Core Engineering | Acts as Software developer |

**Example Task Analysis:**

**Task:** "Implement user authentication API endpoint"
- Keywords detected: `implement`, `API`, `endpoint`
- Activated sections: Core Engineering
- Agent behavior: Software developer mode

**Task:** "Optimize slow database queries in checkout flow"
- Keywords detected: `optimize`, `slow`, `database`, `queries`
- Activated sections: Core Engineering + Performance Engineering
- Agent behavior: Performance engineer mode (with core engineering baseline)

**Task:** "Set up CI/CD pipeline for deployment to production"
- Keywords detected: `CI/CD`, `pipeline`, `deployment`, `production`
- Activated sections: Core Engineering + DevOps & Infrastructure
- Agent behavior: DevOps engineer mode

### Implementation in Templates

Agent templates use Jinja2 conditionals to render context-specific content:

```jinja2
## Responsibilities

### Core (Always Active)
{# This section is always included #}
1. Task breakdown and estimation
2. Code implementation
3. Code review

{% if 'devops' in task_keywords or 'deployment' in task_keywords %}
### DevOps (Active for deployment tasks)
4. CI/CD pipeline configuration
5. Infrastructure as code
6. Secrets management
{% endif %}

{% if 'performance' in task_keywords or 'optimize' in task_keywords %}
### Performance (Active for optimization tasks)
7. Performance profiling
8. Bottleneck identification
9. Load testing
{% endif %}
```

## Detailed Examples

### Example 1: Engineer Agent

**Scenario A: Feature Implementation**

**Task:**
> "Implement the password reset feature for user accounts"

**Keywords Detected:** `implement`, `feature`, `password`, `user`

**Agent Behavior:**
- **Active Sections:** Core Engineering
- **Focus:** Feature implementation, clean code, testing
- **Deliverables:**
  - Implemented password reset endpoint
  - Unit tests for password reset flow
  - Integration tests for email delivery
  - Updated API documentation

**Agent Reasoning:**
```
Task is feature implementation → Use core engineering skills
No deployment or performance keywords → Skip DevOps/Performance sections
Follow standard feature development workflow:
1. Design API endpoint
2. Implement business logic
3. Add validation and error handling
4. Write unit tests
5. Write integration tests
6. Update documentation
```

**Scenario B: CI/CD Pipeline Setup**

**Task:**
> "Set up automated deployment pipeline for staging environment with Docker"

**Keywords Detected:** `deployment`, `pipeline`, `staging`, `docker`

**Agent Behavior:**
- **Active Sections:** Core Engineering + DevOps & Infrastructure
- **Focus:** CI/CD, containerization, infrastructure automation
- **Deliverables:**
  - Dockerfile for application
  - docker-compose.yml for local development
  - GitHub Actions workflow for CI/CD
  - Deployment script for staging
  - Infrastructure as code (Terraform/CloudFormation)

**Agent Reasoning:**
```
Task is deployment infrastructure → Activate DevOps section
Keywords: pipeline, docker, deployment → Use CI/CD skills
Apply DevOps best practices:
1. Containerize application (Dockerfile)
2. Create CI pipeline (build, test, lint)
3. Create CD pipeline (deploy to staging)
4. Add health checks and monitoring
5. Document deployment process
```

**Scenario C: Performance Optimization**

**Task:**
> "Application is slow during peak traffic. Optimize API response times."

**Keywords Detected:** `slow`, `optimize`, `API`, `response times`, `peak traffic`

**Agent Behavior:**
- **Active Sections:** Core Engineering + Performance Engineering
- **Focus:** Performance analysis, bottleneck identification, optimization
- **Deliverables:**
  - Performance profiling report
  - Identified bottlenecks (N+1 queries, missing indexes)
  - Optimized database queries
  - Implemented caching layer (Redis)
  - Load test results showing improvement

**Agent Reasoning:**
```
Task is performance optimization → Activate Performance section
Keywords: slow, optimize, response times → Use profiling skills
Performance engineering workflow:
1. Profile application under load
2. Identify bottlenecks (CPU, memory, I/O, network)
3. Analyze database query performance
4. Implement optimizations (caching, indexing, query optimization)
5. Re-test and measure improvement
6. Document changes and performance gains
```

### Example 2: Tester Agent

**Scenario A: Test Planning (Sprint Planning Phase)**

**Task:**
> "Create test plan for user authentication feature"

**Keywords Detected:** `test plan`, `user authentication`, `feature`

**Agent Behavior:**
- **Active Sections:** Core Testing
- **Focus:** Test strategy, test case design, coverage analysis
- **Deliverables:**
  - Test strategy document
  - Test cases (positive, negative, edge cases)
  - Test data requirements
  - Coverage plan (unit, integration, E2E)

**Scenario B: Adversarial Testing (Bug Hunt)**

**Task:**
> "Find bugs in the checkout flow that our tests are missing"

**Keywords Detected:** `find bugs`, `checkout flow`, `tests missing`

**Agent Behavior:**
- **Active Sections:** Core Testing + Adversarial Testing
- **Focus:** Finding bugs, edge cases, unexpected behaviors
- **Approach:**
  - Red team mindset: "How can I break this?"
  - Test unusual inputs, race conditions, boundary values
  - Look for assumptions in code that could be violated

**Scenario C: Fault Attribution (Test Failure Analysis)**

**Task:**
> "Tests are failing. Determine if the CODE, TEST, or SPEC is wrong."

**Keywords Detected:** `tests failing`, `determine`, `wrong`

**Agent Behavior:**
- **Active Sections:** Core Testing + Test Arbitration
- **Focus:** Fault attribution (CODE | TEST | SPEC)
- **Deliverables:**
  - Fault analysis for each failure
  - `CODE` fault → Create bug ticket
  - `TEST` fault → Fix test implementation
  - `SPEC` fault → Escalate to product owner

**Agent Reasoning:**
```
Task is test failure analysis → Activate Test Arbitration section
For each failing test:
1. Read test implementation
2. Read code under test
3. Read specification/acceptance criteria
4. Determine fault:
   - CODE: Implementation doesn't match spec
   - TEST: Test assertion is incorrect
   - SPEC: Specification is ambiguous/wrong
5. Take appropriate action based on fault type
```

## Context Keywords Reference

### Engineer Agent

| Context | Keywords | Activated Behavior |
|---------|----------|-------------------|
| **Core Engineering** | implement, feature, bug, fix, refactor, code | Software development |
| **DevOps** | deploy, deployment, CI/CD, pipeline, docker, kubernetes, infrastructure, IaC | Infrastructure automation |
| **Performance** | optimize, slow, latency, performance, throughput, bottleneck, cache | Performance engineering |

### Tester Agent

| Context | Keywords | Activated Behavior |
|---------|----------|-------------------|
| **Core Testing** | test, testing, test plan, coverage, quality | Test planning and strategy |
| **Adversarial** | find bugs, break, edge case, security test, fuzz | Adversarial testing |
| **Spec-Driven** | specification, requirements, acceptance criteria | Spec-driven test generation |
| **Fault Attribution** | test failure, failing test, determine fault | Fault attribution (CODE/TEST/SPEC) |

## Best Practices

### 1. Be Explicit in Task Descriptions

**Bad:**
> "Fix the database issue"

**Good:**
> "Optimize slow database queries causing checkout timeout"

**Why:** Explicit keywords (`optimize`, `slow`, `queries`) trigger Performance section.

### 2. Use Natural Language

Don't overthink keywords - write tasks as you would for a human:

**Good:**
> "The API is slow during peak hours. Profile and optimize response times."

**Bad:**
> "PERFORMANCE OPTIMIZATION TASK: API LATENCY REDUCTION"

### 3. Combine Contexts When Needed

Some tasks naturally span multiple contexts:

> "Implement user login feature with OAuth2 and deploy to staging with CI/CD"

**Keywords Detected:** `implement`, `feature`, `OAuth2`, `deploy`, `staging`, `CI/CD`

**Activated Sections:** Core Engineering + DevOps

**Agent Behavior:** Implements feature AND sets up deployment pipeline

### 4. Trust the Agent's Judgment

Context-driven agents are designed to infer the right behavior from your task description. You don't need to explicitly say "act as a DevOps engineer" - the keywords will trigger it.

## Limitations

### 1. Ambiguous Tasks

If task description is too vague, agent may not activate the right sections:

**Vague:**
> "Do something with the API"

**Clear:**
> "Optimize API response times for the /users endpoint"

### 2. Conflicting Contexts

If task has conflicting keywords, agent may activate multiple sections:

**Conflicting:**
> "Write tests for the performance optimization"

**Keywords:** `tests` (Testing) + `performance optimization` (Performance)

**Resolution:** Agent will use both Testing and Performance skills, which is usually correct (test the optimization).

### 3. Rare Contexts

For very specialized tasks, context-driven agents may not have the exact specialized knowledge:

**Example:**
> "Perform quantum cryptography analysis on the encryption module"

**Resolution:** Agent will use Security Specialist skills but may lack domain-specific quantum crypto expertise. For highly specialized domains, consider custom agent templates.

## Migration from Specialized Agents

If you're used to the old specialized agent model, here's how to think in the new model:

| Old Thinking (v1.x) | New Thinking (v2.0) |
|---------------------|---------------------|
| "This is a DevOps task, use `/devops-engineer`" | "This is an engineering task involving deployment, use `/engineer`" |
| "This needs adversarial testing, use `/adversarial-tester`" | "This needs testing with a red team mindset, use `/tester` and mention finding bugs" |
| "Which agent handles X?" | "Which SDLC phase is this? Use that agent with clear task description" |

## Summary

Context-driven agents **simplify the framework while increasing capability**:

- **Fewer agents** → Easier to remember and use
- **Adaptive behavior** → Agent fits the task, not the other way around
- **Natural language** → Write tasks as you would for a human
- **Future-proof** → New capabilities added without new agents

The key is **explicit, clear task descriptions** that include relevant keywords. The agent will handle the rest.
