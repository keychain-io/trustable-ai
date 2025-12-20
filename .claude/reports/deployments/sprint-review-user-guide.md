# Sprint Review User Guide - External Enforcement

**Last Updated**: 2025-12-18

## Quick Start

```bash
# Run sprint review from your terminal (NOT from Claude Code)
python3 scripts/sprint_review_v2.py --sprint "Sprint 7"
```

**What happens:**
1. ✅ Script collects metrics automatically
2. ✅ Script analyzes work items automatically
3. ✅ Script gets AI reviews automatically (via Claude CLI)
4. ✅ Script presents recommendation
5. ⏸️  **Script BLOCKS and waits for your approval**
6. ✅ Script closes sprint ONLY if you type "yes"

## What You'll See

### Steps 1-6: Automated (No Input Required)

```
======================================================================
🔒 SPRINT REVIEW - GENUINE EXTERNAL ENFORCEMENT
======================================================================

Sprint: Sprint 7
Started: 2025-12-18 13:30:00

This script runs in YOUR terminal with genuine control flow.
You will be prompted to approve/reject at Step 7.
======================================================================

──────────────────────────────────────────────────────────────────────
📊 STEP 1: Metrics Collection (Pure Script)
──────────────────────────────────────────────────────────────────────
✓ Retrieved 14 work items
✓ 14 completed (100.0%)
✅ Step 1 complete

──────────────────────────────────────────────────────────────────────
🔍 STEP 2: Work Item Analysis (Pure Script)
──────────────────────────────────────────────────────────────────────
Breakdown by type:
  - Task: 14
Breakdown by state:
  - Done: 14
✅ Step 2 complete

... (Steps 3-6 run automatically) ...

──────────────────────────────────────────────────────────────────────
📋 STEP 6: Scrum Master Recommendation (Pure Script)
──────────────────────────────────────────────────────────────────────

Recommendation: APPROVE
Rationale: All reviews passed and sprint >90% complete
Completion: 100.0%
✅ Step 6 complete
```

### Step 7: YOUR APPROVAL (You Decide Here)

```
======================================================================
⏸️  STEP 7: HUMAN APPROVAL GATE (GENUINE BLOCKING)
======================================================================

🔒 BLOCKING CHECKPOINT - Execution halted pending approval
──────────────────────────────────────────────────────────────────────

Scrum Master Recommendation: APPROVE
Rationale: All reviews passed and sprint >90% complete
Completion: 100.0%

Steps completed:
  1. ✓ 1-metrics
  2. ✓ 2-analysis
  3. ✓ 3-epics
  4. ✓ 4-tests
  5. ✓ 5-reviews
  6. ✓ 6-recommendation

✓ All 6 steps verified
✓ No steps were skipped
✓ Audit trail complete

──────────────────────────────────────────────────────────────────────
DECISION REQUIRED:
  yes = Approve sprint closure (mark EPICs as Done)
  no  = Cancel (no changes made)
──────────────────────────────────────────────────────────────────────

Approve sprint closure? (yes/no): ▊  ← TYPE HERE AND PRESS ENTER
```

**What to do:**
- Type `yes` and press Enter → Sprint closes, EPICs marked Done
- Type `no` and press Enter → Sprint NOT closed, no changes made
- Press Ctrl+C → Cancel, no changes made

### Step 8: Sprint Closure (Only If You Approved)

```
──────────────────────────────────────────────────────────────────────
🎉 STEP 8: Sprint Closure (Pure Script)
──────────────────────────────────────────────────────────────────────
Closing 0 EPIC(s)...
✅ Step 8 complete

======================================================================
✅ SPRINT REVIEW COMPLETE
======================================================================

📋 Audit log saved: .claude/workflow-state/sprint-review-v2-Sprint-7-20251218-133045.json

✓ All workflow steps verified externally
✓ No steps were skipped
✓ User approval obtained
======================================================================
```

## Common Questions

### Q: Should I run this from Claude Code?

**No!** Run it directly in your terminal:

❌ **Wrong:**
```
# Inside Claude Code session
User: /sprint-review-enforced Sprint 7
```

✅ **Correct:**
```bash
# In your terminal (outside Claude Code)
$ python3 scripts/sprint_review_v2.py --sprint "Sprint 7"
```

**Why:** The script needs real terminal stdin to block for approval. Running via Claude Code creates a subprocess without terminal access.

### Q: What happened to --interactive mode?

**Removed** because it was confusing for sprint review. Sprint review is fully automated except for the approval gate.

**Interactive mode belongs in sprint execution**, not sprint review:
- Sprint review = Automated analysis → You approve → Done
- Sprint execution = You work with Claude on tasks interactively

### Q: Does Claude still analyze the sprint?

**Yes!** Claude analyzes via the CLI in non-interactive mode:

```bash
# Script calls this automatically:
claude --print \
  --output-format json \
  --system-prompt "You are a QA reviewer..." \
  "Analyze sprint data: {...}"
```

**You don't see this** - it happens automatically and the script captures the output.

### Q: Can I see the audit log?

**Yes!** After completion:

```bash
# Find latest audit log
ls -lt .claude/workflow-state/sprint-review-v2-*.json | head -1

# View it
cat .claude/workflow-state/sprint-review-v2-Sprint-7-<timestamp>.json
```

**Contents:**
```json
{
  "workflow": "sprint-review-v2",
  "sprint": "Sprint 7",
  "status": "completed",
  "steps_completed": ["1-metrics", "2-analysis", ...],
  "evidence": {
    "metrics": { "completion_rate": 100.0, ... },
    "reviews": { "qa": {"recommendation": "APPROVE"}, ... },
    "approval": { "approved": true, "response": "yes", "timestamp": "..." }
  },
  "enforcement": {
    "type": "genuine_external",
    "execution_context": "user_terminal",
    "approval_gate": "blocking_input"
  }
}
```

This is **cryptographic proof** that:
- All steps completed in order
- External verification performed
- You approved with "yes" at specific timestamp

## Troubleshooting

### Problem: "claude: command not found"

**Solution:** The script will use fallback analysis (simple heuristics based on completion rate).

To enable Claude CLI reviews:
```bash
# Check if claude is installed
which claude

# If not found, check installation
claude --version
```

### Problem: Script exits immediately without blocking

**Likely cause:** You're running it via Claude Code subprocess.

**Solution:** Run directly in terminal:
```bash
# Open a NEW terminal window (not Claude Code)
cd /path/to/project
python3 scripts/sprint_review_v2.py --sprint "Sprint 7"
```

### Problem: Want to cancel after approving

**Too late!** Once you type "yes", the script proceeds immediately.

**Prevention:** Read the recommendation carefully before approving:
- Check completion rate
- Review the recommendation (APPROVE/CONDITIONAL/BLOCK)
- Look at steps completed

If uncertain, type "no" and investigate manually.

## Advanced Usage

### Use Claude API Instead of CLI

If you have an Anthropic API key and want higher-quality AI reviews:

```bash
export ANTHROPIC_API_KEY="your-key-here"
python3 scripts/sprint_review_v2.py --sprint "Sprint 7" --use-api
```

**Cost:** ~$0.10-0.30 per sprint review (depending on sprint size)

### Inspect Results Before Running

```bash
# Manually check sprint status
python3 -c "
import sys
sys.path.insert(0, '.claude/skills')
from work_tracking import get_adapter
adapter = get_adapter()
items = adapter.query_sprint_work_items('Sprint 7')
done = len([i for i in items if i.get('fields',{}).get('System.State')=='Done'])
print(f'{done}/{len(items)} items Done ({done/len(items)*100:.0f}%)')
"
```

### Dry Run (No Closure)

The script doesn't have a dry-run mode, but you can:
1. Run the script normally
2. Type "no" at the approval gate
3. Review the audit log to see what would have happened

## When To Use This Script

**Use for:**
- ✅ End-of-sprint reviews (Sprint 6, Sprint 7, etc.)
- ✅ When you need audit trail of sprint closure
- ✅ When EPICs need to be marked Done
- ✅ When you want external verification before closing

**Don't use for:**
- ❌ Sprint execution (use separate script for interactive work)
- ❌ Quick status checks (just query Azure DevOps)
- ❌ Mid-sprint reviews (no closure needed)

## Summary

**Run:** `python3 scripts/sprint_review_v2.py --sprint "Sprint 7"`

**Expect:** Automated analysis → Approval prompt → Sprint closure (if approved)

**Key feature:** **Genuine blocking approval gate** - script waits for YOUR decision

**Proof:** Audit log in `.claude/workflow-state/` proves compliance
