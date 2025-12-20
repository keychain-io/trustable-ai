#!/usr/bin/env python3
"""
Sprint Execution - Interactive Mode Example

This demonstrates the INTERACTIVE MODE pattern for workflows where
user collaboration with Claude is essential.

Use cases for interactive mode:
- Sprint execution (implement tasks with Claude)
- Bug investigation (debug with Claude's help)
- Code review (discuss findings with Claude)
- Architecture planning (iterate designs with Claude)

Usage:
    python3 scripts/sprint_execution_interactive.py --sprint "Sprint 7"
"""

import os
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / '.claude' / 'skills'))

from work_tracking import get_adapter


class SprintExecutionInteractive:
    """
    Sprint execution with interactive Claude sessions.

    Demonstrates MODE 3: Interactive AI for collaborative work.
    """

    def __init__(self, sprint_name: str):
        self.sprint_name = sprint_name
        self.adapter = get_adapter()
        self.tasks_completed: List[int] = []
        self.start_time = datetime.now()

    def execute(self) -> bool:
        """Execute sprint tasks interactively with Claude."""
        print("=" * 70)
        print("🔄 SPRINT EXECUTION - INTERACTIVE MODE")
        print("=" * 70)
        print(f"\nSprint: {self.sprint_name}")
        print("Mode: Interactive collaboration with Claude")
        print("\nYou'll work with Claude on each task.")
        print("=" * 70)

        try:
            # Get tasks in progress
            items = self.adapter.query_sprint_work_items(self.sprint_name)
            in_progress = [
                i for i in items
                if i.get('fields', {}).get('System.State') == 'In Progress'
            ]

            if not in_progress:
                print("\n✓ No tasks in progress - sprint execution complete!")
                return True

            print(f"\nFound {len(in_progress)} task(s) in progress:")
            for item in in_progress:
                task_id = item['id']
                title = item.get('fields', {}).get('System.Title', 'Untitled')
                print(f"  - Task #{task_id}: {title}")

            print("\n" + "─" * 70)

            # Process each task interactively
            for item in in_progress:
                task_id = item['id']
                title = item.get('fields', {}).get('System.Title', 'Untitled')
                description = item.get('fields', {}).get('System.Description', '')

                # Ask if user wants to work on this task
                if not self._confirm_work_on_task(task_id, title):
                    continue

                # Interactive Claude session for the task
                completed = self._work_on_task_with_claude(task_id, title, description)

                if completed:
                    # Ask if task should be marked Done
                    if self._confirm_mark_done(task_id, title):
                        self._mark_task_done(task_id)
                        self.tasks_completed.append(task_id)

            # Summary
            print("\n" + "=" * 70)
            print("✅ SPRINT EXECUTION COMPLETE")
            print("=" * 70)
            print(f"\nTasks completed: {len(self.tasks_completed)}")
            for task_id in self.tasks_completed:
                print(f"  ✓ Task #{task_id}")
            print("=" * 70)

            return True

        except KeyboardInterrupt:
            print("\n\n❌ Interrupted by user")
            return False
        except Exception as e:
            print(f"\n\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _confirm_work_on_task(self, task_id: int, title: str) -> bool:
        """Ask user if they want to work on this task."""
        print("\n" + "=" * 70)
        print(f"Task #{task_id}: {title}")
        print("=" * 70)

        while True:
            response = input("\nWork on this task? (yes/skip/quit): ").strip().lower()
            if response == 'yes':
                return True
            elif response == 'skip':
                print("⏭️  Skipping task")
                return False
            elif response == 'quit':
                print("🛑 Quitting sprint execution")
                sys.exit(0)
            else:
                print("Please enter 'yes', 'skip', or 'quit'")

    def _work_on_task_with_claude(self, task_id: int, title: str, description: str) -> bool:
        """
        MODE 3: Interactive Claude session.

        This is where the interactive pattern shines:
        - Script writes context for Claude
        - Spawns interactive Claude session
        - User collaborates with Claude on implementation
        - User exits Claude when done (Ctrl+D or 'exit')
        - Script resumes and checks results
        """
        print("\n" + "─" * 70)
        print("🤖 OPENING INTERACTIVE CLAUDE SESSION")
        print("─" * 70)

        # Write context file for Claude
        context_file = Path(f'.claude/tasks/task-{task_id}-context.md')
        context_file.parent.mkdir(parents=True, exist_ok=True)

        context_content = f"""# Task #{task_id}: {title}

## Description
{description or 'No description provided'}

## Sprint
{self.sprint_name}

## Your Mission

Work with the user to complete this task. You have full access to:
- Read tool (examine code)
- Write tool (create/modify files)
- Edit tool (make precise changes)
- Bash tool (run tests, build, etc.)

## Instructions

1. **Understand the task**: Read the description carefully
2. **Ask questions**: If requirements are unclear, ask the user
3. **Plan approach**: Discuss implementation strategy
4. **Implement**: Write code, tests, documentation
5. **Verify**: Run tests, check quality
6. **Write summary**: When done, write results to task-{task_id}-results.md

## How To Exit

When task is complete (or you want to pause):
- Type `exit` or press Ctrl+D to close this Claude session
- The script will resume and ask if task should be marked Done

## Notes

- Take your time - quality over speed
- Ask user for guidance when needed
- Write tests for new functionality
- Document what you built

Good luck! 🚀
"""

        with open(context_file, 'w', encoding='utf-8') as f:
            f.write(context_content)

        # Prepare results file
        results_file = Path(f'.claude/tasks/task-{task_id}-results.md')
        if results_file.exists():
            results_file.unlink()

        print(f"\nContext written to: {context_file}")
        print(f"Results expected at: {results_file}")
        print("\n" + "─" * 70)
        print("Claude will now help you complete this task.")
        print("You can:")
        print("  - Ask Claude questions")
        print("  - Guide Claude's implementation")
        print("  - Review Claude's work")
        print("  - Iterate until satisfied")
        print("\nWhen done, type 'exit' or press Ctrl+D to return to this script.")
        print("─" * 70)

        input("\nPress Enter to open Claude session...")

        # Spawn interactive Claude
        prompt = f"""Work on Task #{task_id}: {title}

Read the full context and instructions:
  {context_file}

When complete, write a summary to:
  {results_file}

Include:
- What you implemented
- Files changed
- Tests added/run
- Any issues or blockers
"""

        try:
            # This opens an interactive session - user collaborates with Claude
            print("\n🚀 Launching Claude...\n")
            subprocess.run(['claude', prompt], check=False)
            print("\n✓ Claude session closed")

        except FileNotFoundError:
            print("⚠️  'claude' command not found")
            print("You'll need to work on this task manually.")
            return False
        except Exception as e:
            print(f"⚠️  Error launching Claude: {e}")
            return False

        # Check if results were written
        if results_file.exists():
            print(f"\n✓ Results found: {results_file}")
            with open(results_file, 'r', encoding='utf-8') as f:
                results = f.read()
            print("\n" + "─" * 70)
            print("RESULTS:")
            print("─" * 70)
            print(results[:500])  # Show first 500 chars
            if len(results) > 500:
                print(f"\n... ({len(results) - 500} more characters)")
            print("─" * 70)
            return True
        else:
            print("\n⚠️  No results file found - task may be incomplete")
            return False

    def _confirm_mark_done(self, task_id: int, title: str) -> bool:
        """Ask user if task should be marked Done."""
        print(f"\nMark Task #{task_id} as Done?")
        print(f"Title: {title}")

        while True:
            response = input("Mark as Done? (yes/no): ").strip().lower()
            if response == 'yes':
                return True
            elif response == 'no':
                print("Task will remain In Progress")
                return False
            else:
                print("Please enter 'yes' or 'no'")

    def _mark_task_done(self, task_id: int):
        """Mark task as Done in Azure DevOps."""
        try:
            self.adapter.update_work_item(task_id, {'System.State': 'Done'})
            print(f"✅ Task #{task_id} marked as Done")
        except Exception as e:
            print(f"❌ Error marking task Done: {e}")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Sprint Execution with Interactive Claude Sessions'
    )
    parser.add_argument('--sprint', required=True, help='Sprint name (e.g., "Sprint 7")')

    args = parser.parse_args()

    executor = SprintExecutionInteractive(args.sprint)
    success = executor.execute()

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
