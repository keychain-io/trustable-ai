# External Enforcement - Correct Architecture

**Date**: 2025-12-18
**Status**: Design Complete - Ready for Implementation

## Critical Discovery

The initial "external enforcement" POC had a **fatal architectural flaw**:

**POC Design (BROKEN):**
```
User in Claude Code session
  → /sprint-review-enforced command
  → Spawns Python subprocess
  → subprocess tries input() for approval
  → ❌ No terminal stdin → EOF → fake cancellation
```

**Problems:**
- ✗ Approval gate didn't actually block (subprocess has no stdin)
- ✗ Script appeared to work but was broken
- ✗ Data parsing bugs made sprint look 0% done when it was 100% done
- ✗ User never saw approval prompt
- ✗ "External enforcement" was theater, not reality

## Correct Architecture

**User Suggestion (CORRECT):**
```
User runs script directly in terminal (not via Claude)
  → Script controls flow with genuine terminal I/O
  → Spawns Claude CLI when AI reasoning needed
  → Spawns interactive Claude when user collaboration needed
  → Approval gates work (real input() in real terminal)
```

## Architecture Details

### Three Execution Modes

#### Mode 1: Pure Script Control (No AI)
**For:** Data collection, validation, metrics

```bash
# User terminal
$ python3 scripts/sprint_review.py --sprint "Sprint 7"

# Script does:
- Query Azure DevOps API directly
- Calculate metrics (Python logic)
- Check file system for test reports
- Validate quality gates
- NO Claude needed
```

#### Mode 2: Non-Interactive AI Analysis
**For:** Reviews, recommendations, synthesis

```bash
# Script spawns Claude in --print mode
claude --print \
  --output-format json \
  --no-session-persistence \
  --system-prompt "You are a QA reviewer..." \
  "Analyze this sprint data and recommend APPROVE/BLOCK/CONDITIONAL: $(cat data.json)"

# Claude returns JSON:
{
  "recommendation": "APPROVE",
  "notes": "All tests passing, 100% completion",
  "concerns": []
}

# Script captures output and continues
```

**Benefits:**
- Fast (no interactive overhead)
- Structured output (JSON schema)
- Scriptable (deterministic)
- No session pollution

#### Mode 3: Interactive Claude Session
**For:** Sprint execution, complex debugging, user needs to guide Claude

```bash
# Script writes context
cat > .claude/tasks/current-task.md <<EOF
# Sprint Task: Implement Feature X

## Context
- Sprint: Sprint 7
- Feature: User Authentication
- Requirements: See Epic #1234

## Current State
- Database migration complete
- API endpoints 60% done
- Tests missing

## Your Task
Work with the user to complete this feature.
Check their questions and implement based on guidance.
EOF

# Script spawns interactive Claude
echo "═══════════════════════════════════════════"
echo "Opening Claude for interactive task work..."
echo "Work with Claude to complete the task."
echo "Close Claude when done (Ctrl+D or exit)."
echo "═══════════════════════════════════════════"

claude --session-id "sprint-7-task-1234" \
  "Review .claude/tasks/current-task.md and work with user to implement."

# Script waits for Claude to exit (user closes session)
# User can:
#   - Ask Claude questions
#   - Guide implementation
#   - Review Claude's work
#   - Iterate until satisfied
# When done, user exits Claude

# Script resumes
echo "Claude session closed. Checking results..."
```

**Benefits:**
- User can guide Claude interactively
- Claude has full tool access (Read, Write, Bash, etc.)
- Natural collaboration
- User decides when task is done

### Approval Gates (The Critical Fix)

```python
def approval_gate(self, recommendation: str) -> bool:
    """
    GENUINE blocking approval gate.

    Works because script runs in user's terminal with real stdin.
    """
    print("═" * 70)
    print("⏸️  APPROVAL REQUIRED")
    print("═" * 70)
    print(f"Recommendation: {recommendation}")
    print()
    print("Steps verified:")
    for step in self.completed_steps:
        print(f"  ✓ {step}")
    print()
    print("Approve sprint closure?")
    print("  yes = Continue with closure")
    print("  no  = Cancel (no changes)")
    print("═" * 70)

    # THIS WORKS because we're in a real terminal
    response = input("Your decision (yes/no): ").strip().lower()

    if response == "yes":
        print("✅ Approved - proceeding with closure")
        return True
    else:
        print("❌ Cancelled - no changes made")
        return False
```

**Why this works:**
- ✅ Script runs in terminal (not subprocess)
- ✅ stdin connected to user's keyboard
- ✅ input() genuinely blocks (waits for keypress)
- ✅ User sees prompt and types response
- ✅ Script cannot proceed without approval
- ✅ Audit log records actual user response

## Workflow Examples

### Sprint Review (Enforced)

```bash
#!/bin/bash
# scripts/sprint_review_enforced.sh

SPRINT="$1"

echo "Starting enforced sprint review for $SPRINT"

# Step 1-4: Pure script (no AI needed)
python3 -c "
from work_tracking import get_adapter
adapter = get_adapter()
items = adapter.query_sprint_work_items('$SPRINT')
print(f'Total: {len(items)}')
print(f'Done: {len([i for i in items if i.get(\"fields\",{}).get(\"System.State\")==\"Done\"])}')
" > metrics.txt

# Step 5: AI Reviews (non-interactive)
claude --print --output-format json \
  --system-prompt "You are a QA specialist. Review sprint completion." \
  "Sprint metrics: $(cat metrics.txt). Recommend APPROVE/BLOCK/CONDITIONAL." \
  > qa-review.json

claude --print --output-format json \
  --system-prompt "You are a security specialist." \
  "Review security for: $(cat metrics.txt)" \
  > security-review.json

# Step 6: Synthesize (script logic)
python3 synthesize_reviews.py qa-review.json security-review.json > recommendation.txt

# Step 7: APPROVAL GATE (genuine blocking)
echo "════════════════════════════════════════"
cat recommendation.txt
echo "════════════════════════════════════════"
read -p "Approve sprint closure? (yes/no): " approval

if [ "$approval" != "yes" ]; then
    echo "❌ Sprint review cancelled"
    exit 1
fi

# Step 8: Sprint closure (only if approved)
echo "✅ Closing sprint..."
python3 close_sprint.py "$SPRINT"

echo "✅ Sprint review complete"
```

### Sprint Execution (Interactive)

```bash
#!/bin/bash
# scripts/sprint_execution.sh

SPRINT="$1"

# Get tasks for sprint
TASKS=$(python3 -c "
from work_tracking import get_adapter
adapter = get_adapter()
items = adapter.query_sprint_work_items('$SPRINT')
in_progress = [i for i in items if i.get('fields',{}).get('System.State')=='In Progress']
for item in in_progress:
    print(f\"{item['id']}:{item['fields']['System.Title']}\")
")

echo "In Progress Tasks:"
echo "$TASKS"
echo

# For each task, offer interactive Claude session
echo "$TASKS" | while IFS=: read -r id title; do
    echo "════════════════════════════════════════"
    echo "Task #$id: $title"
    echo "════════════════════════════════════════"
    read -p "Work on this task? (yes/skip/quit): " choice

    case $choice in
        yes)
            # Write context for Claude
            cat > .claude/tasks/task-$id.md <<EOF
# Task #$id: $title

Work with the user to complete this task.
Use Read/Write/Bash tools as needed.
Ask questions if requirements are unclear.
EOF

            # Spawn interactive Claude
            echo "Opening Claude for task #$id..."
            claude "Work on task #$id. See .claude/tasks/task-$id.md"

            # After Claude closes
            read -p "Mark task as Done? (yes/no): " done
            if [ "$done" = "yes" ]; then
                python3 -c "
from work_tracking import get_adapter
adapter = get_adapter()
adapter.update_work_item($id, {'System.State': 'Done'})
print('✅ Task #$id marked Done')
"
            fi
            ;;
        quit)
            echo "Exiting sprint execution"
            exit 0
            ;;
        *)
            echo "Skipping task #$id"
            ;;
    esac
done
```

## Migration Plan

### Phase 1: Fix Current POC
- [x] Fix data parsing bugs (lines 193, 228, 234)
- [x] Test data collection works correctly
- [ ] Document limitations of subprocess approach

### Phase 2: Implement Correct Architecture
- [ ] Create `scripts/` directory for terminal-executable scripts
- [ ] Implement Mode 1: Pure script workflows (metrics, validation)
- [ ] Implement Mode 2: Non-interactive AI (reviews via `claude --print`)
- [ ] Implement Mode 3: Interactive AI (task work via `claude`)
- [ ] Test approval gates work in real terminal

### Phase 3: Update Documentation
- [ ] Update VISION.md with correct architecture
- [ ] Update workflow_executor/CLAUDE.md
- [ ] Create user guide for running scripts
- [ ] Document Mode 1/2/3 patterns

### Phase 4: Validate
- [ ] Run full sprint review from terminal
- [ ] Verify approval gate actually blocks
- [ ] Verify interactive Claude session works for sprint execution
- [ ] Create audit trail from real execution

## Benefits of New Architecture

### Reliability
- ✅ Approval gates genuinely block (real terminal I/O)
- ✅ Script controls flow (not AI)
- ✅ External verification at each step
- ✅ Audit trail proves compliance

### Flexibility
- ✅ Pure script when AI not needed (fast, cheap)
- ✅ Non-interactive AI for analysis (structured, scriptable)
- ✅ Interactive AI when user needs to collaborate (natural)
- ✅ User chooses level of automation vs. guidance

### User Experience
- ✅ User sees real approval prompts
- ✅ Can guide Claude interactively when needed
- ✅ Clear separation: script=control, Claude=reasoning
- ✅ Transparent execution (script output in terminal)

### Cost
- ✅ Mode 1: $0 (no AI calls)
- ✅ Mode 2: ~$0.10 per review (short prompts)
- ✅ Mode 3: Variable (user controls session length)
- ✅ Total: ~$1-5/month for typical sprint cadence

## Key Insights

1. **External enforcement requires external execution**
   - Running via Claude Code subprocess = not external
   - Running in user's terminal = genuinely external

2. **AI should assist, not control**
   - Script controls flow and verification
   - Claude provides reasoning and collaboration
   - User provides approval and guidance

3. **Three modes for three needs**
   - No AI: Data and validation
   - Automated AI: Reviews and analysis
   - Interactive AI: Complex tasks and collaboration

4. **Genuine blocking requires genuine terminals**
   - subprocess stdin = EOF = fake blocking
   - terminal stdin = keyboard = real blocking

## Next Steps

1. **Implement script templates** for common workflows
2. **Create user guide** for running enforced workflows
3. **Update documentation** to reflect correct architecture
4. **Validate with real sprint review** in terminal

## Conclusion

The original POC proved the **concept** was right (external enforcement), but the **implementation** was wrong (subprocess can't block).

The corrected architecture achieves the vision:
- **Script controls** = Reliability
- **Claude reasons** = Intelligence
- **User approves** = Trust

This is the breakthrough: **Trustable AI through genuine external enforcement.**
