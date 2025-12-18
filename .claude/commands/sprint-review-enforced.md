---
description: "Sprint review with EXTERNAL ENFORCEMENT - Guarantees workflow compliance"
---

# Sprint Review - External Enforcement Mode

I will execute the sprint review workflow with **external enforcement** to guarantee compliance.

## What This Means

**The Problem**: AI agents (including me) are unreliable when given workflow instructions:
- I skip steps to optimize for goals
- I bypass approval gates
- I claim completion without verification
- More explicit instructions don't help (I optimize for outcomes, not procedures)

**The Solution**: External enforcement script that:
- ✅ Controls execution flow (not AI)
- ✅ Verifies each step externally before proceeding
- ✅ Blocks on approval gates (Python `input()` halts until you respond)
- ✅ Creates comprehensive audit trail
- ✅ Makes it **impossible** for AI to skip steps or bypass gates

## Execution

I'm now executing the external enforcement script. You'll see:
1. Each workflow step executed in order
2. External verification of each step
3. **Blocking approval gate** where you must type "yes" or "no"
4. Complete audit trail saved to `.claude/workflow-state/`

**IMPORTANT**: When you see the approval prompt, you must type your response directly in the terminal. The script will wait for your input - this is a genuine blocking gate that I cannot bypass.

```bash
python3 .claude/skills/workflow_executor/sprint_review_enforced.py --sprint "{{sprint_name}}"
```

This demonstrates the breakthrough design: **Combining Claude's reasoning with external enforcement creates reliable, trustworthy AI-assisted development.**
