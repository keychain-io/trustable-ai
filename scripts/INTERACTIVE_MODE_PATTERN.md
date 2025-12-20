# Interactive Mode Pattern - Reusable Template

This document shows the **interactive mode pattern** for workflows where user collaboration with Claude is essential.

## When To Use Interactive Mode

✅ **Use interactive mode for:**
- Sprint execution (implement tasks with Claude)
- Bug investigation (debug complex issues)
- Code review (discuss findings interactively)
- Architecture planning (iterate on designs)
- Refactoring (guided code improvements)
- Test writing (collaborate on test cases)

❌ **Don't use interactive mode for:**
- Sprint review (just need analysis + approval)
- Metrics collection (pure data gathering)
- Report generation (automated synthesis)
- Simple validation (pass/fail checks)

## The Pattern (Copy This)

```python
def _interactive_task_with_claude(self, task_id: str, context: Dict) -> bool:
    """
    Interactive Claude session pattern.

    This is the reusable template for spawning Claude interactively.
    Copy this method and adapt for your workflow.
    """

    # 1. WRITE CONTEXT FILE
    # Claude needs to know what to work on
    context_file = Path(f'.claude/tasks/{task_id}-context.md')
    context_file.parent.mkdir(parents=True, exist_ok=True)

    context_content = f"""# Task: {context['title']}

## Background
{context['description']}

## Your Mission
{context['instructions']}

## How To Exit
When done, type 'exit' or press Ctrl+D

## Output Expected
Write results to: .claude/tasks/{task_id}-results.md
"""

    with open(context_file, 'w', encoding='utf-8') as f:
        f.write(context_content)

    # 2. PREPARE OUTPUT FILE
    results_file = Path(f'.claude/tasks/{task_id}-results.md')
    if results_file.exists():
        results_file.unlink()  # Clean slate

    # 3. EXPLAIN TO USER
    print("=" * 70)
    print("🤖 OPENING INTERACTIVE CLAUDE SESSION")
    print("=" * 70)
    print(f"\nContext: {context_file}")
    print(f"Results: {results_file}")
    print("\nYou can now collaborate with Claude:")
    print("  - Ask questions")
    print("  - Guide implementation")
    print("  - Review work")
    print("  - Iterate until satisfied")
    print("\nClose Claude (Ctrl+D or 'exit') when done.")
    print("=" * 70)

    input("\nPress Enter to launch Claude...")

    # 4. SPAWN INTERACTIVE CLAUDE
    prompt = f"""Work on: {context['title']}

See context: {context_file}
Write results to: {results_file}
"""

    try:
        # This blocks until user closes Claude
        subprocess.run(['claude', prompt], check=False)
        print("\n✓ Claude session closed")

    except FileNotFoundError:
        print("⚠️  'claude' command not found")
        return False
    except Exception as e:
        print(f"⚠️  Error: {e}")
        return False

    # 5. VERIFY RESULTS
    if results_file.exists():
        with open(results_file, 'r', encoding='utf-8') as f:
            results = f.read()
        print(f"\n✓ Results received ({len(results)} chars)")
        return True
    else:
        print("\n⚠️  No results - task may be incomplete")
        return False
```

## Key Points

### 1. Context File Is Essential

Claude needs to know:
- What to work on (task description)
- What's expected (deliverables)
- How to exit (Ctrl+D or 'exit')
- Where to write results

**Template:**
```markdown
# Task: {title}

## Background
{context and requirements}

## Your Mission
{what Claude should do}

## Available Tools
- Read: Examine code
- Write: Create files
- Edit: Modify code
- Bash: Run tests, build, etc.

## How To Exit
Type 'exit' or press Ctrl+D when done

## Expected Output
Write summary to: {results_file}
Include:
- What you implemented
- Files changed
- Tests added
- Any blockers
```

### 2. User Sees Clear Instructions

Before spawning Claude, tell user:
```
═══════════════════════════════════════
🤖 OPENING INTERACTIVE CLAUDE SESSION
═══════════════════════════════════════

You can now collaborate with Claude:
  - Ask questions
  - Guide implementation
  - Review work
  - Iterate until satisfied

Close Claude (Ctrl+D) when done.
═══════════════════════════════════════
```

This avoids confusion about what to do.

### 3. subprocess.run() Blocks

```python
subprocess.run(['claude', prompt], check=False)
```

This **blocks the script** until Claude exits. User controls when by:
- Typing `exit`
- Pressing Ctrl+D
- Closing the session

Script resumes automatically after.

### 4. Verify Results

After Claude closes:
```python
if results_file.exists():
    # Read results
    # Continue workflow
else:
    # Handle incomplete work
```

This gives script proof that work was done.

## Complete Example Workflows

### Sprint Execution (Implemented)

See: `scripts/sprint_execution_interactive.py`

**Flow:**
1. Query tasks in progress
2. For each task:
   - Ask user: "Work on this task?"
   - If yes → Spawn Claude interactively
   - User + Claude implement together
   - User exits Claude when done
   - Script asks: "Mark as Done?"
3. Summary of completed tasks

### Bug Investigation (Template)

```python
class BugInvestigator:
    def investigate_with_claude(self, bug_id: int):
        # Get bug details
        bug = self.adapter.get_work_item(bug_id)

        # Write context
        context = {
            'title': f"Bug #{bug_id}",
            'description': bug['fields']['System.Description'],
            'instructions': """
1. Reproduce the bug
2. Identify root cause
3. Propose fix
4. Write tests to prevent regression
"""
        }

        # Launch interactive Claude
        completed = self._interactive_task_with_claude(
            task_id=f'bug-{bug_id}',
            context=context
        )

        if completed:
            print("Bug investigation complete")
            # Read results, create fix PR, etc.
```

### Architecture Planning (Template)

```python
class ArchitecturePlanner:
    def plan_with_claude(self, feature_name: str):
        context = {
            'title': f"Architecture: {feature_name}",
            'description': f"Design architecture for {feature_name}",
            'instructions': """
1. Review requirements
2. Propose architecture (diagrams, components)
3. Identify risks and trade-offs
4. Document decision rationale
5. Create implementation plan
"""
        }

        completed = self._interactive_task_with_claude(
            task_id=f'arch-{feature_name}',
            context=context
        )
```

### Code Review (Template)

```python
class CodeReviewer:
    def review_with_claude(self, pr_number: int):
        context = {
            'title': f"Code Review: PR #{pr_number}",
            'description': "Review pull request changes",
            'instructions': """
1. Read changed files
2. Check for issues (bugs, security, performance)
3. Suggest improvements
4. Write review comments
5. Recommend APPROVE/REQUEST_CHANGES
"""
        }

        completed = self._interactive_task_with_claude(
            task_id=f'pr-{pr_number}',
            context=context
        )
```

## Non-Interactive Alternative

For **automated** AI (no user collaboration needed):

```python
def _automated_claude_analysis(self, data: Dict) -> Dict:
    """Non-interactive Claude via CLI --print mode."""

    result = subprocess.run(
        [
            'claude',
            '--print',
            '--output-format', 'json',
            '--no-session-persistence',
            '--system-prompt', 'You are an expert analyst',
            f'Analyze: {json.dumps(data)}'
        ],
        capture_output=True,
        text=True,
        check=True,
        timeout=60
    )

    return json.loads(result.stdout)
```

**When to use:**
- Simple analysis (metrics, reports)
- Structured output needed (JSON)
- No iteration required
- Fast execution important

## Summary

### Interactive Mode = Collaboration

**Use when:**
- User needs to guide Claude
- Multiple iterations expected
- Complex problem requires back-and-forth
- User decides when "done"

**Pattern:**
1. Write context file
2. Explain to user what's happening
3. Spawn `claude` (blocks until user exits)
4. Verify results
5. Continue workflow

### Non-Interactive Mode = Automation

**Use when:**
- Simple analysis/synthesis
- One-shot prompt
- Structured output (JSON)
- No user guidance needed

**Pattern:**
1. Call `claude --print --output-format json`
2. Parse response
3. Continue workflow

## Files

- **`scripts/sprint_execution_interactive.py`** - Complete working example
- **`scripts/sprint_review_v2.py`** - Uses non-interactive mode (shows contrast)
- **This document** - Reusable pattern for any workflow

Copy the pattern and adapt for your specific workflow needs!
