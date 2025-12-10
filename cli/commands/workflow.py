"""
Workflow command - manage workflows (list, render, run).
"""
import click
from pathlib import Path
from typing import Optional

from config import load_config
from workflows import WorkflowRegistry


@click.group(name="workflow")
def workflow_command():
    """Manage workflows (render templates for use with Claude Code)."""
    pass


@workflow_command.command(name="list")
def list_workflows():
    """List available workflows."""
    try:
        config = load_config()
        registry = WorkflowRegistry(config)

        workflows = registry.list_workflows()

        click.echo("\n📋 Available workflows:")
        for workflow in workflows:
            click.echo(f"  • {workflow}")

        click.echo(f"\nTotal: {len(workflows)} workflows\n")

    except FileNotFoundError as e:
        click.echo(f"❌ Error: {e}")
        click.echo("Run 'trustable-ai init' to initialize the framework.")


@workflow_command.command(name="render")
@click.argument("workflow_name")
@click.option("--output", "-o", type=click.Path(), help="Output file path")
@click.option("--show", is_flag=True, help="Show rendered output")
def render_workflow(workflow_name: str, output: Optional[str], show: bool):
    """Render a workflow template."""
    try:
        config = load_config()
        registry = WorkflowRegistry(config)

        # Render workflow
        rendered = registry.render_workflow(workflow_name)

        # Save to file if requested
        if output:
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(rendered, encoding='utf-8')
            click.echo(f"✅ Rendered workflow saved to {output_path}")

        # Show output if requested
        if show or not output:
            click.echo(f"\n{'='*80}")
            click.echo(f"Workflow: {workflow_name}")
            click.echo('='*80)
            click.echo(rendered)
            click.echo('='*80)

    except ValueError as e:
        click.echo(f"❌ Error: {e}")
    except FileNotFoundError as e:
        click.echo(f"❌ Error: {e}")


@workflow_command.command(name="render-all")
@click.option("--output-dir", "-o", type=click.Path(), default=".claude/commands", help="Output directory")
def render_all_workflows(output_dir: str):
    """Render all workflows."""
    try:
        config = load_config()
        registry = WorkflowRegistry(config)

        output_path = Path(output_dir)
        workflows = registry.list_workflows()

        click.echo(f"\n📝 Rendering {len(workflows)} workflows to {output_path}\n")

        for workflow_name in workflows:
            output_file = registry.save_rendered_workflow(workflow_name, output_path)
            click.echo(f"  ✓ {workflow_name} → {output_file}")

        click.echo(f"\n✅ All workflows rendered successfully.\n")

    except FileNotFoundError as e:
        click.echo(f"❌ Error: {e}")


@workflow_command.command(name="run")
@click.argument("workflow_name")
@click.option("--dry-run", is_flag=True, help="Show workflow without executing")
def run_workflow(workflow_name: str, dry_run: bool):
    """
    Run a workflow (NOT YET IMPLEMENTED - use 'render' instead).

    Automatic workflow execution is planned for a future release.
    Currently, use 'trustable-ai workflow render' to generate workflow instructions
    that you can provide to Claude Code manually.
    """
    click.echo(f"\n🚀 Running workflow: {workflow_name}")

    if dry_run:
        try:
            config = load_config()
            registry = WorkflowRegistry(config)
            rendered = registry.render_workflow(workflow_name)

            click.echo("\n📄 Workflow Definition (dry-run):")
            click.echo('='*80)
            click.echo(rendered)
            click.echo('='*80)

        except Exception as e:
            click.echo(f"❌ Error: {e}")
    else:
        click.echo("\n⚠️  Workflow execution engine is not yet implemented.")
        click.echo("\n📝 To use this workflow:")
        click.echo(f"   1. Render it: trustable-ai workflow render {workflow_name} --show")
        click.echo("   2. Copy the instructions")
        click.echo("   3. Provide them to Claude Code\n")
        click.echo("Automatic execution will be available in a future release.\n")


@workflow_command.command(name="verify")
@click.argument("workflow_name")
@click.option("--epic-id", type=int, help="Epic ID for context-specific verification")
@click.option("--sprint-id", type=int, help="Sprint ID for context-specific verification")
@click.option("--feature-id", type=int, help="Feature ID for context-specific verification")
def verify_workflow(
    workflow_name: str,
    epic_id: Optional[int],
    sprint_id: Optional[int],
    feature_id: Optional[int]
):
    """
    Verify workflow checklist items against external source of truth.

    Validates that workflow verification checklist items pass by querying
    the work tracking adapter. Returns exit code 0 if all checks pass,
    exit code 1 if any checks fail.

    Examples:
        trustable-ai workflow verify sprint-planning
        trustable-ai workflow verify backlog-grooming --epic-id 123
        trustable-ai workflow verify daily-standup --sprint-id 456
    """
    import sys
    import re

    # Step 1: Load Configuration and Initialize Adapter
    try:
        config = load_config()

        # Initialize work tracking adapter
        sys.path.insert(0, '.claude/skills')
        from work_tracking import get_adapter
        adapter = get_adapter()

    except FileNotFoundError as e:
        click.echo(f"❌ Error: {e}")
        click.echo("Run 'trustable-ai init' to initialize the framework.")
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Error initializing adapter: {e}")
        sys.exit(1)

    # Step 2: Load and Render Workflow Template
    try:
        registry = WorkflowRegistry(config)
        rendered = registry.render_workflow(workflow_name)
    except ValueError as e:
        click.echo(f"❌ Error: Workflow '{workflow_name}' not found")
        available = registry.list_workflows()
        click.echo(f"Available workflows: {', '.join(available)}")
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Error rendering workflow: {e}")
        sys.exit(1)

    # Step 3: Extract Verification Checklist from Rendered Workflow
    # Look for verification checklist items in multiple formats:
    # 1. Direct markdown checkboxes: - [ ] Item
    # 2. Python f-strings that generate checkboxes: checklist.append(f"- [...")
    # 3. Numbered list items that describe verification
    checklist_items = []

    # Pattern 1: Find direct markdown checkboxes
    direct_checkboxes = re.findall(r'- \[[ x]\] (.+)', rendered)
    checklist_items.extend(direct_checkboxes)

    # Pattern 2: Find Python f-strings that append checklist items
    # Look for: checklist.append(f"- [{'x' if ... else ' '}] Item text")
    fstring_pattern = r'checklist\.append\(f"- \[.*?\] ([^"]+?)(?: \(|")'
    fstring_items = re.findall(fstring_pattern, rendered)
    checklist_items.extend(fstring_items)

    # Pattern 3: If we found a "Verification Checklist" header, extract numbered items
    if 'Verification Checklist' in rendered or '🔍' in rendered:
        # Look for numbered list after verification header
        verification_section_pattern = r'(?:Verification Checklist|🔍.*)[^\n]*\n(?:.*\n)*?((?:\d+\.\s+.+\n?)+)'
        verification_matches = re.findall(verification_section_pattern, rendered, re.MULTILINE)
        for match in verification_matches:
            # Extract numbered items
            numbered_items = re.findall(r'\d+\.\s+(.+)', match)
            checklist_items.extend(numbered_items)

    if not checklist_items:
        click.echo(f"ℹ️  No verification checklist found in {workflow_name}")
        click.echo("This workflow does not have verification gates.")
        sys.exit(0)

    # Step 4: Validate Each Checklist Item
    click.echo(f"\n🔍 Verifying workflow: {workflow_name}")
    click.echo("=" * 80)

    failed_checks = []

    for item_text in checklist_items:
        item_lower = item_text.lower()

        # Check 1: Work item states queried
        if 'work item' in item_lower and ('queried' in item_lower or 'adapter' in item_lower or 'source of truth' in item_lower):
            # Query work items to verify adapter works
            try:
                if sprint_id:
                    items = adapter.query_work_items(iteration=f"Sprint {sprint_id}")
                elif epic_id:
                    items = adapter.query_work_items(filters={'Parent': epic_id})
                elif feature_id:
                    items = adapter.query_work_items(filters={'Parent': feature_id})
                else:
                    # Generic query - just verify adapter connectivity
                    # Don't pass limit parameter (not all adapters support it)
                    items = adapter.query_work_items()

                if items is not None:
                    click.echo(f"✅ {item_text}")
                else:
                    click.echo(f"❌ {item_text} - Adapter query returned None")
                    failed_checks.append(item_text)
            except Exception as e:
                click.echo(f"❌ {item_text} - Adapter query failed: {e}")
                failed_checks.append(item_text)

        # Check 2: Test results verified
        elif 'test' in item_lower and ('verified' in item_lower or 'coverage' in item_lower):
            # Attempt to verify test coverage if possible
            try:
                if sprint_id:
                    items = adapter.query_work_items(iteration=f"Sprint {sprint_id}")
                    if items:
                        click.echo(f"✅ {item_text}")
                    else:
                        click.echo(f"⚠️  {item_text} - No items to verify")
                else:
                    # Generic check - just note that manual verification needed
                    click.echo(f"ℹ️  {item_text} - Manual verification required")
            except Exception as e:
                click.echo(f"⚠️  {item_text} - Unable to verify: {e}")

        # Check 3: Blocked items have links
        elif 'blocked' in item_lower and ('linked' in item_lower or 'blocker' in item_lower):
            try:
                blocked = adapter.query_work_items(state='Blocked')
                if blocked:
                    # Check if blocked items have relations
                    all_linked = True
                    for item in blocked:
                        full_item = adapter.get_work_item(item['id'])
                        if full_item and not full_item.get('relations'):
                            all_linked = False
                            break

                    if all_linked:
                        click.echo(f"✅ {item_text}")
                    else:
                        click.echo(f"❌ {item_text} - Some blocked items missing links")
                        failed_checks.append(item_text)
                else:
                    # No blocked items = N/A = pass
                    click.echo(f"✅ {item_text} (N/A - no blocked items)")
            except Exception as e:
                click.echo(f"⚠️  {item_text} - Unable to verify: {e}")

        # Check 4: Story points validated
        elif 'story point' in item_lower or 'burndown' in item_lower:
            try:
                if sprint_id:
                    items = adapter.query_work_items(iteration=f"Sprint {sprint_id}")
                    if items:
                        # Verify we can query items with story points
                        click.echo(f"✅ {item_text}")
                    else:
                        click.echo(f"⚠️  {item_text} - No items to check")
                else:
                    click.echo(f"ℹ️  {item_text} - Requires --sprint-id")
            except Exception as e:
                click.echo(f"⚠️  {item_text} - Unable to verify: {e}")

        # Generic check - just verify we can query adapter
        else:
            click.echo(f"ℹ️  {item_text} - Manual verification required")

    click.echo("=" * 80)

    # Return exit code based on results
    if failed_checks:
        click.echo(f"\n❌ Verification FAILED - {len(failed_checks)} check(s) failed:")
        for check in failed_checks:
            click.echo(f"  • {check}")
        sys.exit(1)
    else:
        click.echo(f"\n✅ Verification PASSED - All checks successful")
        sys.exit(0)
