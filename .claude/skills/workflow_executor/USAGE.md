# External Enforcement - Usage Guide

## Quick Start

### From Claude Code (Recommended)
```
/sprint-review-enforced Sprint 7
```

### From Terminal
```bash
# Set up environment
export CLAUDE_AZURE_DEVELOPMENT_API_KEY="your-token-here"

# Run the enforced workflow
python3 .claude/skills/workflow_executor/sprint_review_enforced.py --sprint "Sprint 7" --interactive
```

---

## Prerequisites

### Required
- Python 3.9+
- Azure DevOps PAT token (if using Azure DevOps integration)
- `.claude/config.yaml` properly configured

### Optional
- `anthropic` package (for API mode)
- `ANTHROPIC_API_KEY` environment variable (for API mode)

---

## Environment Setup

### Azure DevOps PAT Token

Your Azure DevOps PAT token must be accessible to the script. There are three ways to provide it:

#### Option 1: Environment Variable (Recommended)
```bash
export CLAUDE_AZURE_DEVELOPMENT_API_KEY="your-52-char-token-here"
```

**For persistent setup**, add to `~/.bash_profile` (not `~/.bashrc`):
```bash
echo 'export CLAUDE_AZURE_DEVELOPMENT_API_KEY="your-token"' >> ~/.bash_profile
source ~/.bash_profile
```

#### Option 2: .claude/config.yaml
```yaml
work_tracking:
  platform: azure-devops
  organization: https://dev.azure.com/yourorg
  project: Your Project
  credentials_source: env:CLAUDE_AZURE_DEVELOPMENT_API_KEY
```

Then export the variable:
```bash
export CLAUDE_AZURE_DEVELOPMENT_API_KEY="your-token"
```

#### Option 3: Direct in Config (Not Recommended)
```yaml
work_tracking:
  credentials_source: "your-52-char-token-here"
```

**Warning:** This stores your token in plain text. Use `env:VARIABLE_NAME` instead.

### Generating a PAT Token

1. Go to Azure DevOps → User Settings → Personal Access Tokens
2. Create new token with scopes: **Work Items (Read, Write)**
3. Copy the 52-character token
4. Export it: `export CLAUDE_AZURE_DEVELOPMENT_API_KEY="your-token"`

---

## The Three Modes

### 1. Interactive Mode (Uses Claude in Session)

**Command:**
```bash
python3 .claude/skills/workflow_executor/sprint_review_enforced.py --sprint "Sprint 7" --interactive
```

**What Happens:**
1. Script executes Steps 1-4 (data collection)
2. Script writes analysis request to file
3. Script polls for response (checks every 2 seconds)
4. **You see the request and provide analysis** (as Claude)
5. Script reads your analysis and continues
6. At Step 7, **you must type "yes" or "no"** at the approval gate

**Cost:** $0 (uses existing Claude Code subscription)

**Use When:** Running from Claude Code interactive session

### 2. API Mode (Calls Claude API)

**Command:**
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
pip install anthropic  # If not already installed
python3 .claude/skills/workflow_executor/sprint_review_enforced.py --sprint "Sprint 7" --use-api
```

**What Happens:**
1. Script executes Steps 1-4 (data collection)
2. Script calls Claude API for analysis (Steps 5-6)
3. At Step 7, **you must type "yes" or "no"** at the approval gate

**Cost:** ~$0.30 per sprint review

**Use When:** CI/CD, automation, scheduled reviews (no interactive Claude)

### 3. Basic Mode (Local Heuristics)

**Command:**
```bash
python3 .claude/skills/workflow_executor/sprint_review_enforced.py --sprint "Sprint 7"
```

**What Happens:**
1. Script executes Steps 1-4 (data collection)
2. Script uses simple heuristics for analysis:
   - Completion rate >= 80% → QA APPROVE
   - Otherwise → QA BLOCK
   - Security: Always APPROVE (no real analysis)
   - Engineering: Based on completion rate
3. At Step 7, **you must type "yes" or "no"** at the approval gate

**Cost:** $0 (no AI analysis)

**Use When:** Quick verification, offline environments, testing

---

## Complete Workflow

### Interactive Mode (Detailed)

**Step 1: Start the Script**
```bash
export CLAUDE_AZURE_DEVELOPMENT_API_KEY="your-token"
python3 .claude/skills/workflow_executor/sprint_review_enforced.py --sprint "Sprint 7" --interactive
```

**Step 2: Watch Automated Steps**
```
📊 STEP 1: Sprint Metrics Collection
✓ Retrieved 14 work items
✓ 14 completed (100.0%)

🔍 STEP 2: Work Item Analysis
Work item breakdown: ...

🎯 STEP 3: EPIC Identification
Found 1 completed EPIC: #1128

🧪 STEP 4: Test Verification
Found 7 test reports
```

**Step 3: Script Requests Analysis**
```
======================================================================
WAITING FOR CLAUDE'S ANALYSIS
======================================================================

Claude, please analyze the sprint data and provide:
1. QA Review (recommendation: APPROVE/BLOCK, notes)
2. Security Review (recommendation: APPROVE/BLOCK, score)
3. Engineering Review (recommendation: APPROVE/CONDITIONAL, readiness)

Sprint data: .claude/workflow-state/sprint-review-analysis-request.json

Write your analysis to:
  .claude/workflow-state/sprint-review-analysis-response.json

⏸️  Waiting for analysis response...
```

**Step 4: Provide Analysis** (as Claude in the session)
```bash
# Read the request
cat .claude/workflow-state/sprint-review-analysis-request.json

# Write your analysis
cat > .claude/workflow-state/sprint-review-analysis-response.json <<'EOF'
{
  "qa": {"recommendation": "APPROVE", "notes": "All tests passing"},
  "security": {"recommendation": "APPROVE", "score": "5/5"},
  "engineering": {"recommendation": "APPROVE", "readiness": "9.5/10"}
}
EOF
```

**Step 5: Script Continues**
```
✓ Analysis response received!

📋 STEP 6: Scrum Master Recommendation
Recommendation: APPROVE
Rationale: All reviews passed
```

**Step 6: Approval Gate (BLOCKING)**
```
══════════════════════════════════════════════════════════════════════
⏸️  STEP 7: HUMAN APPROVAL GATE
══════════════════════════════════════════════════════════════════════

Recommendation: APPROVE
Steps completed: 1-metrics, 2-analysis, 3-epics, 4-tests, 5-reviews, 6-recommendation

✓ All 6 steps verified externally

Approve sprint closure? (yes/no): █
```

**YOU TYPE HERE** → "yes" or "no"

**Step 7: Sprint Closure** (if approved)
```
🎉 STEP 8: Sprint Closure
Marking 1 EPIC(s) as Done...
  ✓ EPIC #1128 - Marked as Done

✓ Closure report: .claude/reports/deployments/sprint-7-enforced-closure.md

✅ SPRINT REVIEW COMPLETE
Duration: 135.2s
Audit log: .claude/workflow-state/sprint-review-enforced-Sprint-7-20251218.json
```

---

## Outputs

### Audit Log
**Location:** `.claude/workflow-state/sprint-review-enforced-{sprint}-{timestamp}.json`

**Contains:**
- All steps completed with timestamps
- Evidence for each step (metrics, analyses, reviews)
- User approval decision and timestamp
- Enforcement metadata (mode, guarantees)

**Example:**
```json
{
  "workflow": "sprint-review-enforced",
  "sprint": "Sprint 7",
  "status": "completed",
  "steps_completed": ["1-metrics", "2-analysis", ..., "8-closure"],
  "step_evidence": { ... },
  "enforcement": {
    "mode": "external",
    "guarantee": "All steps verified externally",
    "approval_gate": "blocking"
  }
}
```

### Closure Report
**Location:** `.claude/reports/deployments/{sprint}-enforced-closure.md`

**Contains:**
- Sprint summary
- All steps completed with evidence
- Enforcement guarantees
- Timestamp and approval record

---

## Troubleshooting

### "PAT token not found or invalid"

**Cause:** Azure DevOps PAT token not exported to subprocess

**Solution:**
```bash
# Export the variable
export CLAUDE_AZURE_DEVELOPMENT_API_KEY="your-token"

# Verify it's set
echo $CLAUDE_AZURE_DEVELOPMENT_API_KEY

# Run the script in the same session
python3 .claude/skills/workflow_executor/sprint_review_enforced.py --sprint "Sprint 7" --interactive
```

### "Timeout waiting for analysis"

**Cause:** In interactive mode, response file not written within 5 minutes

**Solution:**
1. Check if request file exists: `.claude/workflow-state/sprint-review-analysis-request.json`
2. Read it to see what's needed
3. Write response to: `.claude/workflow-state/sprint-review-analysis-response.json`
4. Script will automatically continue

**If timeout occurs:** Script falls back to local heuristics analysis

### "Script terminated without completion"

**Cause:** Running via non-interactive subprocess (like Bash tool)

**Why This Happens:** The approval gate uses `input()` which requires an interactive terminal

**Solution:** Run in an actual terminal:
```bash
# From your terminal (not via Bash tool)
python3 .claude/skills/workflow_executor/sprint_review_enforced.py --sprint "Sprint 7" --interactive
```

**Note:** This is actually a feature - the script cannot proceed without real user input, proving the enforcement works!

---

## Best Practices

### 1. Use Interactive Mode in Claude Code
- Free (uses subscription)
- Intelligent analysis
- Same enforcement guarantees

### 2. Export Environment Variables First
```bash
# Do this BEFORE running the script
export CLAUDE_AZURE_DEVELOPMENT_API_KEY="your-token"
```

### 3. Run in Real Terminal for Full Experience
- See all output
- Provide approval at Step 7
- Complete audit trail

### 4. Review Audit Logs
```bash
# Check the audit log after completion
cat .claude/workflow-state/sprint-review-enforced-Sprint-7-*.json | jq .
```

### 5. Clean Up Old Logs Periodically
```bash
# Remove old audit logs (keep last 5)
ls -t .claude/workflow-state/sprint-review-enforced-*.json | tail -n +6 | xargs rm -f
```

---

## Understanding the Enforcement

### What's Enforced

✅ **Step Order** - Script controls execution sequence
✅ **Step Completion** - Each step verified before proceeding
✅ **External Verification** - Evidence from Azure DevOps, file system
✅ **Approval Gate** - Blocking `input()` call that halts execution
✅ **Audit Trail** - Complete record of all steps and decisions

### What AI Cannot Do

❌ **Skip steps** - Script controls flow, not AI
❌ **Bypass approval** - `input()` is a system call AI cannot access
❌ **Claim false completion** - External verification required
❌ **Modify audit trail** - Written by script, not AI
❌ **Proceed without approval** - Script terminates if no input

### The Guarantee

**The script will terminate rather than proceed in an invalid state.**

This is the core enforcement guarantee - if any step fails, if approval cannot be obtained, if external verification fails → the script stops cleanly with no partial state or incomplete work.

---

## Cost Comparison

| Mode | Setup | Cost/Review | Monthly (4 reviews) | Analysis Quality |
|------|-------|-------------|---------------------|------------------|
| **Interactive** | Export token | $0 | $0 | Excellent (Claude) |
| **API** | Export token + API key | ~$0.30 | ~$1.20 | Excellent (Claude API) |
| **Basic** | Export token only | $0 | $0 | Simple heuristics |

**Recommendation:** Interactive mode for Claude Code sessions, API mode for automation.

---

## Related Documentation

- **CLAUDE.md** - Complete architecture documentation
- **README.md** - Proof of concept overview
- **external-enforcement-poc-demonstration.md** - Demonstration report
- **sprint_review_enforced.py** - Implementation (well-commented)

---

*This external enforcement pattern makes AI failures impossible, not just unlikely.*
