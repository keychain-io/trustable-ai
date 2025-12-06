# Migration Guide: v1.x → v2.0 (12-Agent → 7-Agent Model)

## Overview

Trustable AI v2.0 introduces a **context-driven agent model** that consolidates 12 specialized agents into 7 adaptive agents. This simplifies the mental model while improving agent capability through context-aware behavior.

## What Changed

### Agent Consolidation

**v1.x (12 Agents):**
- `business-analyst`
- `project-architect`
- `senior-engineer`
- `software-developer`
- `qa-engineer`
- `devops-engineer`
- `performance-engineer`
- `security-specialist`
- `scrum-master`
- `adversarial-tester`
- `spec-driven-tester`
- `test-arbitrator`

**v2.0 (7 Agents):**
- `business-analyst` (unchanged)
- `architect` (renamed from `project-architect`)
- `senior-engineer` (unchanged)
- `engineer` (consolidates: `software-developer`, `devops-engineer`, `performance-engineer`)
- `tester` (consolidates: `qa-engineer`, `adversarial-tester`, `spec-driven-tester`, `test-arbitrator`)
- `security-specialist` (unchanged)
- `scrum-master` (unchanged)

### How Agents Now Work: Context-Driven Behavior

Instead of having separate agents for each role, consolidated agents **adapt based on task context**:

#### Example 1: Engineer Agent

**Old model (v1.x):**
- `/software-developer` → Implement features
- `/devops-engineer` → CI/CD and infrastructure
- `/performance-engineer` → Performance optimization

**New model (v2.0):**
- `/engineer` with deployment task → Acts as DevOps engineer
- `/engineer` with performance task → Acts as Performance engineer
- `/engineer` with feature task → Acts as Software developer

**How it works:** The agent prompt includes conditional sections that activate based on task keywords:
```
## Responsibilities (Context-Driven)

### Core Engineering (All Tasks)
1. Break down features into implementable tasks
2. Estimate complexity and effort
...

### DevOps & Infrastructure (When task involves deployment/infrastructure)
6. Design and implement CI/CD pipelines
7. Manage infrastructure as code (IaC)
...

### Performance Engineering (When task involves performance/optimization)
11. Analyze application performance and identify bottlenecks
12. Design and execute load tests
...
```

#### Example 2: Tester Agent

**Old model (v1.x):**
- `/qa-engineer` → Test planning
- `/adversarial-tester` → Find bugs
- `/spec-driven-tester` → Independent verification
- `/test-arbitrator` → Determine fault attribution

**New model (v2.0):**
- `/tester` in sprint planning → Test planning and strategy
- `/tester` with failing tests → Adversarial testing to find root cause
- `/tester` with spec → Spec-driven test generation
- `/tester` with test failures → Fault attribution (CODE | TEST | SPEC)

## Migration Steps

### Step 1: Upgrade Trustable AI

```bash
pip install --upgrade trustable-ai
```

### Step 2: Update Configuration

**Option A: Automatic Update (Recommended)**

Run `trustable-ai init` to update your `.claude/config.yaml`:

```bash
trustable-ai init
```

The init wizard will:
1. Detect your v1.x configuration
2. Show current enabled agents
3. Prompt: "Migrate to v2.0 7-agent model? (Y/n)"
4. Update `enabled_agents` list automatically
5. Preserve custom settings

**Option B: Manual Update**

Edit `.claude/config.yaml`:

```yaml
agent_config:
  enabled_agents:
    # Old (v1.x) - commented out
    # - business-analyst
    # - project-architect
    # - senior-engineer
    # - software-developer
    # - devops-engineer
    # - performance-engineer
    # - qa-engineer
    # - adversarial-tester
    # - spec-driven-tester
    # - test-arbitrator
    # - security-specialist
    # - scrum-master

    # New (v2.0)
    - business-analyst
    - architect
    - senior-engineer
    - engineer
    - tester
    - security-specialist
    - scrum-master
```

### Step 3: Re-render Agents

```bash
# Render new agent definitions
trustable-ai agent render-all

# Re-render workflows (updated to use new agent names)
trustable-ai workflow render-all
```

### Step 4: Update Custom Workflows (If Any)

If you have custom workflows in `.claude/commands/`, update agent references:

**Old:**
```markdown
Call `/software-developer` to implement the feature.
Call `/qa-engineer` to create test plan.
```

**New:**
```markdown
Call `/engineer` to implement the feature.
Call `/tester` to create test plan.
```

### Step 5: Test Workflows

Run a test workflow to verify migration:

```bash
# In Claude Code
/daily-standup
```

If you see errors like "Agent 'software-developer' not found", check:
1. Did you re-render agents? (`trustable-ai agent render-all`)
2. Is your config updated? (`cat .claude/config.yaml | grep enabled_agents -A 10`)

## Backward Compatibility

v2.0 maintains **deprecated aliases** for old agent names:

```python
# In agents/registry.py
agent_model_map = {
    # New agents
    "engineer": "engineer",
    "tester": "qa",

    # Deprecated aliases (still work, but logged warnings)
    "software-developer": "engineer",   # → engineer
    "devops-engineer": "engineer",       # → engineer
    "qa-engineer": "qa",                 # → tester
    "adversarial-tester": "qa",          # → tester
}
```

**What this means:**
- Old workflows using `/software-developer` will still work (routes to `/engineer`)
- Deprecated agent names log warnings in profiling reports
- You should update workflows to new names for clarity

## Breaking Changes

1. **Agent Template Structure:**
   - Agent templates now include conditional sections (context-driven behavior)
   - Old agent templates (v1.x) are not compatible with v2.0

2. **Workflow References:**
   - Workflows generated in v2.0 use new agent names (`/architect` not `/project-architect`)
   - Old workflow files will still work via deprecated aliases

3. **Initialization Behavior:**
   - `trustable-ai init` no longer creates `.claude/agents/` and `.claude/commands/` directories
   - Instead, instructs users to run `/context-generation` in Claude Code
   - Agents/workflows are generated on-demand via workflows, not upfront via CLI

## Benefits of v2.0

1. **Simpler Mental Model:** 7 agents vs 12 agents → easier to remember and use
2. **More Capable Agents:** Context-driven behavior → agents have broader skillsets
3. **Better Adaptability:** Agents adjust to task context → no need to pick "right" agent
4. **Clearer Boundaries:** 7 agents map to distinct SDLC roles, not implementation details

## Common Issues

### Issue 1: "Agent not found" error

**Symptom:**
```
Error: Agent 'software-developer' not found in .claude/agents/
```

**Solution:**
Re-render agents:
```bash
trustable-ai agent render-all
```

### Issue 2: Old agent names in workflows

**Symptom:**
Workflow uses `/software-developer` but you want `/engineer`

**Solution:**
Re-render workflows:
```bash
trustable-ai workflow render-all
```

### Issue 3: Custom workflows broken

**Symptom:**
Custom workflows reference old agent names

**Solution:**
Update manually:
```bash
find .claude/commands -name "*.md" -exec sed -i 's|/software-developer|/engineer|g' {} +
find .claude/commands -name "*.md" -exec sed -i 's|/qa-engineer|/tester|g' {} +
find .claude/commands -name "*.md" -exec sed -i 's|/project-architect|/architect|g' {} +
```

## FAQ

### Q: Will my old workflows break?

**A:** No, deprecated aliases ensure old workflows continue working. However, you should update to new agent names for clarity.

### Q: Can I still use the old 12-agent model?

**A:** No, v2.0 only supports the 7-agent model. If you need the old model, stay on v1.x.

### Q: How do I know which agent to use now?

**A:** Use this mapping:
- **Implementation/DevOps/Performance** → `/engineer`
- **All testing scenarios** → `/tester`
- **Architecture/Design** → `/architect`
- **Estimation/Breakdown** → `/senior-engineer`
- **Requirements/Business** → `/business-analyst`
- **Security** → `/security-specialist`
- **Sprint Management** → `/scrum-master`

### Q: Does context-driven behavior work automatically?

**A:** Yes! The agent prompts include conditional sections that activate based on task keywords. You don't need to do anything special.

### Q: What if the agent doesn't adapt correctly?

**A:** Be more explicit in your task description:
- Bad: "Fix this" → Agent doesn't know what role to take
- Good: "Optimize performance of database queries" → Agent knows to use performance engineering skills

## Support

If you encounter issues during migration:

1. Check the [GitHub Issues](https://github.com/anthropics/claude-code/issues)
2. Run `trustable-ai doctor` to diagnose common problems
3. Open a new issue with:
   - Your `.claude/config.yaml` (redact sensitive info)
   - Output of `trustable-ai --version`
   - Error messages or unexpected behavior

## Version History

- **v1.x:** 12 specialized agents (deprecated)
- **v2.0:** 7 context-driven agents (current)
