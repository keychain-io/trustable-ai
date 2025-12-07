# ADR-001: Learnings Injection Strategy

**Date**: 2025-12-07
**Status**: Proposed
**Deciders**: Project Architect Agent, Engineering Team
**Related Features**: #1025 (Integrate active learnings feedback loop)

---

## Context

Tool failures (Azure CLI JMESPath errors, incorrect arguments, etc.) recur across sessions because learnings aren't automatically injected into agent context. The framework has learnings capture infrastructure but it's not integrated into workflow execution.

We need to decide **how and when** to inject learnings into agent contexts to prevent recurring errors without degrading performance or overwhelming agents with irrelevant information.

---

## Decision

**Per-agent injection with category filtering and caching.**

Each agent invocation will receive learnings filtered by:
1. **Agent type** (engineer, tester, architect, etc.)
2. **Category** (azure-devops, git, pytest, etc.)
3. **Token budget** (maximum 1000 tokens per agent)
4. **Recency** (most recent/impactful learnings prioritized)

Learnings will be **cached per category** with a 5-minute TTL to avoid repeated file system reads.

---

## Options Considered

### Option 1: Per-workflow injection
**Description**: Load learnings once per workflow, all agents get the same set.

**Pros**:
- Simple implementation
- Single load operation per workflow
- Consistent context across all agents

**Cons**:
- Not agent-specific (tester gets architect learnings)
- May include irrelevant learnings
- Wastes token budget on non-applicable context
- No granular control

**Why not chosen**: Different agents need different learnings. Engineer needs Azure CLI learnings, security specialist needs vulnerability learnings. One-size-fits-all wastes tokens and dilutes relevance.

---

### Option 2: Per-agent injection (no caching)
**Description**: Each agent invocation loads fresh learnings filtered by agent type.

**Pros**:
- Relevant learnings per agent
- Category-filtered, focused context
- Token budget managed per agent

**Cons**:
- High file I/O overhead (repeated loads)
- Performance degradation with many agents
- No deduplication across similar agents

**Why not chosen**: Performance overhead too high for workflows with many agent invocations (sprint planning, backlog grooming). Repeated file reads for same categories wasteful.

---

### Option 3: Per-agent injection with caching (CHOSEN)
**Description**: Category-filtered learnings loaded on-demand, cached for 5 minutes.

**Pros**:
- Relevant learnings per agent
- Token budget managed per agent
- Caching mitigates performance overhead
- Category mapping in config allows customization
- Filtering reduces context token usage

**Cons**:
- More complex implementation
- Cache invalidation needed when learnings updated
- TTL tuning required for optimal performance

**Why chosen**: Best balance of relevance, performance, and flexibility. Caching eliminates repeated I/O, category filtering ensures relevance, per-agent injection allows token budget management.

---

## Consequences

### Positive

- **Relevant learnings**: Each agent receives only applicable learnings for its domain
- **Token efficiency**: Filtered learnings fit within budget (1000 tokens max)
- **Performance**: Caching prevents repeated file reads
- **Customizable**: Agent-category mapping in config allows per-project tuning
- **Measurable impact**: Efficiency metrics track learnings application and error prevention

### Negative

- **Implementation complexity**: Requires caching layer, category filtering logic, TTL management
- **Cache invalidation**: New learnings won't appear immediately (5-minute delay)
- **Configuration overhead**: Requires agent-category mapping in `.claude/config.yaml`
- **Debugging difficulty**: Cached learnings may obscure when new learnings are captured

### Risks

- **Risk**: Cache TTL too long → new learnings not applied quickly
  - **Mitigation**: 5-minute TTL balances freshness vs performance, configurable via config

- **Risk**: Category mapping incorrect → agent misses relevant learnings
  - **Mitigation**: Default mapping for all agent types, validation during `trustable-ai init`

- **Risk**: Token budget exceeded → learnings truncated
  - **Mitigation**: Hard limit enforcement, prioritization by recency and impact

---

## Implementation Notes

### Agent-Category Mapping

```yaml
# .claude/config.yaml
learnings_config:
  agent_category_mapping:
    engineer: ["azure-devops", "git", "pytest", "general"]
    tester: ["pytest", "testing", "general"]
    architect: ["architecture", "infrastructure", "general"]
    security-specialist: ["security", "vulnerabilities", "general"]
  max_learnings_per_category: 5
  max_total_tokens: 1000
  cache_ttl_seconds: 300  # 5 minutes
```

### Caching Strategy

```python
# core/learnings_injector.py
class LearningsCache:
    def __init__(self, ttl_seconds: int = 300):
        self.cache: Dict[str, Tuple[List[Learning], float]] = {}
        self.ttl = ttl_seconds

    def get(self, category: str) -> Optional[List[Learning]]:
        if category in self.cache:
            learnings, timestamp = self.cache[category]
            if time.time() - timestamp < self.ttl:
                return learnings
        return None

    def set(self, category: str, learnings: List[Learning]):
        self.cache[category] = (learnings, time.time())
```

### Rendering Integration

```python
# agents/registry.py
class AgentRegistry:
    def render_agent(
        self,
        agent_name: str,
        additional_context: Optional[Dict[str, Any]] = None,
        inject_learnings: bool = True
    ) -> str:
        context = self._build_context()

        if inject_learnings:
            injector = LearningsContextInjector()
            categories = injector.get_categories_for_agent(agent_name)
            learnings_context = injector.fetch_learnings(categories)
            context["learnings"] = learnings_context

        if additional_context:
            context.update(additional_context)

        return template.render(**context)
```

---

## Related Decisions

- **ADR-004**: Test Marker Taxonomy (affects testing of learnings injection)
- Future: Learnings prioritization algorithm (by impact, recency, error frequency)

---

## Approval

- [ ] Engineering Team Review
- [ ] Performance Testing (measure overhead with 100+ learnings)
- [ ] Security Review (ensure no sensitive data in learnings cache)
