---
context:
  purpose: "Solves context overload and agent focus issues through specialized, fresh-context agent invocations"
  problem_solved: "When AI agents operate in overloaded context windows with mixed responsibilities, they forget instructions, skip work, and conflate concerns. Without agent specialization and fresh contexts, complex workflows become unreliable as context pollution accumulates."
  keywords: [agents, specialization, fresh-context, orchestration, business-analyst, architect, engineer]
  task_types: [agent-development, workflow, architecture]
  priority: medium
  max_tokens: 600
  children: [business-analyst, project-architect, senior-engineer, scrum-master, security-specialist, qa-engineer, devops-engineer]
  dependencies: [core, config]
---
# Agents

## Purpose

Solves **context overload** (#3) and implements **Agent Specialization** (Pillar #3) from VISION.md.

When AI operates in overloaded context windows with mixed responsibilities:
- Instructions from early conversation get forgotten
- Constraints ignored due to context pollution
- Work skipped because agent lost track of requirements
- Hallucinations increase as context window fills

The agent system implements **fresh context per role** - each agent spawns in a clean context window with only the information needed for its specific responsibility. No conversation history, no accumulated cruft, just focused execution.

## Key Agents

### business-analyst
**Problem Solved**: Business value and priority decisions made without structured analysis

Analyzes backlog items for business value, revenue impact, customer benefit, and strategic alignment. Returns prioritized recommendations.

**Real Failure Prevented**: Feature prioritization happens in conversation. "Let's do the shiny feature first!" Ship feature with low ROI, delay high-value work. With business analyst: data-driven prioritization shows auth feature has 10x revenue impact vs UI polish. Build auth first.

### project-architect
**Problem Solved**: Technical decisions made without architecture review or risk analysis

Reviews proposed features for technical feasibility, architecture patterns, integration complexity, and risks.

**Real Failure Prevented**: Engineer implements real-time updates with WebSockets. Architect review reveals: existing infra can't handle WebSocket connections, requires $5k/month infrastructure upgrade. Alternative: SSE with existing infra, zero extra cost.

### senior-engineer
**Problem Solved**: Story point estimates made without task breakdown or historical data

Breaks features into granular tasks, estimates effort based on complexity, identifies unknowns.

**Real Failure Prevented**: Feature estimated at "3 points". Implementation reveals 8 integration points, 12 edge cases, security review needed. Actual: 13 points. With senior engineer breakdown: accurate 13-point estimate upfront, sprint capacity planned correctly.

### scrum-master
**Problem Solved**: Sprint planning lacks cohesion, dependencies missed, capacity overallocated

Assembles sprint plan from all agent inputs, validates dependencies, checks team capacity, identifies risks.

**Real Failure Prevented**: Sprint has 40 story points for 30-point capacity. No one catches overallocation. Sprint fails, team burns out. Scrum master validates capacity, flags overallocation, reduces scope to 28 points.

### security-specialist
**Problem Solved**: Security review happens after implementation (expensive to fix)

Reviews features for OWASP vulnerabilities, data exposure, auth weaknesses, compliance issues before implementation.

**Real Failure Prevented**: API endpoint ships without rate limiting. Production DDoS'd. With security review: rate limiting requirement identified in planning, built into implementation, no incident.

### qa-engineer
**Problem Solved**: Test planning happens after code written, missing critical scenarios

Designs test strategy, identifies edge cases, plans integration tests before implementation starts.

**Real Failure Prevented**: Feature implemented without considering offline scenario. Users report data loss. QA engineer identifies offline use case in planning, test plan includes offline-online sync, implementation handles it.

### devops-engineer
**Problem Solved**: Deployment and infrastructure considerations discovered during sprint (too late)

Reviews CI/CD impacts, infrastructure needs, monitoring requirements before sprint starts.

**Real Failure Prevented**: Feature requires new database table. Deploy fails because migration not included. With devops review: migration script planned, included in PR, deploy succeeds.

## Architecture: Fresh Context Pattern

Agents operate in isolated, fresh context windows:

```
Main Workflow (Context Window A - 50k tokens used, getting full)
    │
    ├─ spawn via Task tool ──→ Business Analyst (Context Window B - 0 tokens, fresh)
    │                          - Receives: backlog items, prioritization rules
    │                          - Returns: prioritized list with scores
    │                          - Context discarded after completion
    │
    ├─ spawn via Task tool ──→ Project Architect (Context Window C - 0 tokens, fresh)
    │                          - Receives: feature requirements, tech stack
    │                          - Returns: architecture review, risks
    │                          - Context discarded after completion
    │
    └─ spawn via Task tool ──→ Senior Engineer (Context Window D - 0 tokens, fresh)
                               - Receives: feature specs, estimates from others
                               - Returns: task breakdown, story points
                               - Context discarded after completion
```

**Why This Matters**: If all agents ran in Context Window A:
- 50k tokens + business analyst work (12k) + architect work (15k) = 77k tokens
- Exceeds context limit (70k), truncates early instructions
- Agents forget constraints, skip verification, hallucinate

With fresh contexts:
- Each agent operates in clean 0-token window
- Full instructions available, no truncation
- No cross-contamination between agent concerns

## Agent Invocation Pattern

Workflows spawn agents via the Task tool:

```python
# In workflow (main context)
business_analysis = Task(
    subagent_type="business-analyst",
    description="Prioritize backlog",
    prompt=f"""
    ## YOUR TASK: Prioritize Backlog Items

    Backlog items: {items}
    Prioritization rules: {rules}

    Return JSON with prioritized list.
    """
)

# Agent runs in fresh context, returns once
prioritized_items = parse_json(business_analysis.result)

# Agent context is destroyed, main workflow continues
```

**Key Points**:
- Agent spawned with Task tool (fresh context)
- Agent receives **only** what it needs (items, rules)
- Agent returns **once** (structured output)
- Agent context destroyed after return
- No back-and-forth, no clarification questions

## Agent Specialization Benefits

### 1. Focus
Each agent has one job. Business analyst doesn't do architecture. Architect doesn't estimate. Clean separation of concerns.

### 2. Expertise Modeling
Agent prompts optimized for role-specific decision-making. Business analyst prompt has ROI frameworks. Architect prompt has design patterns.

### 3. Context Efficiency
Agent receives only relevant inputs. Business analyst doesn't get tech stack details. Architect doesn't get business metrics.

### 4. Parallel Execution
Agents without dependencies can run in parallel. Business analysis + security review run simultaneously (2x faster than sequential).

### 5. Reusability
Same agent used across workflows. Business analyst agent works in sprint-planning, backlog-grooming, epic-breakdown - no duplication.

## Agent Configuration

Agents configured in `.claude/config.yaml`:

```yaml
agent_config:
  models:
    architect: "claude-opus-4"        # Complex reasoning
    engineer: "claude-sonnet-4.5"     # Balanced
    analyst: "claude-sonnet-4.5"      # Balanced

  enabled_agents:
    - business-analyst
    - project-architect
    - senior-engineer
    - scrum-master
```

Different agents can use different models based on task complexity:
- **Opus**: Architect (complex system design), Security Specialist (deep threat modeling)
- **Sonnet**: Engineer, Analyst, QA (balanced cost/performance)

## Important Notes

- **Agents are stateless**: No memory between invocations (by design)
- **One-shot execution**: Agent returns once, cannot be queried for clarification
- **Fresh context**: Agent sees NO main conversation history (prevents pollution)
- **Structured output**: Agents return JSON/YAML for parsing, not prose
- **Rendered from templates**: Agents generated from `agents/templates/*.j2` with project config injected

## Real Failure Scenarios Prevented

### Scenario 1: Context Overload Causes Skipped Work
**Without agent specialization**: Main workflow reaches 60k tokens. Add feature analysis (15k tokens), exceed limit, context truncated. Early instructions lost, agent skips verification steps.

**With agent specialization**: Feature analysis spawned in fresh context (0 tokens + 15k analysis = 15k total). All instructions present, verification completed.

### Scenario 2: Mixed Concerns Lead to Poor Decisions
**Without agent specialization**: Same agent does business analysis + architecture + estimation. Conflates concerns, optimizes for tech coolness over ROI.

**With agent specialization**: Business analyst focuses purely on ROI, recommends boring-but-valuable features. Architect focuses on feasibility. Engineer estimates effort. Clear separation leads to better decisions.

### Scenario 3: Sequential Execution Wastes Time
**Without agent specialization**: Business analysis (10 min) → wait → architecture review (12 min) → wait → estimation (8 min) = 30 minutes total.

**With agent specialization**: Business analysis + architecture review run in parallel (12 min max) → estimation (8 min) = 20 minutes total. 33% faster.

## Related

- **VISION.md**: Pillar #3 (Agent Specialization), Pillar #5 (Fresh Contexts Over Overloaded)
- **workflows/CLAUDE.md**: Workflows that orchestrate agents
- **core/CLAUDE.md**: Context loaders that prepare agent inputs
- **agents/templates/**: Agent template source files
- **agents/registry.py**: Agent rendering engine
