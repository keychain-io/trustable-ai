"""
Learnings command for TAID CLI.

Manage institutional knowledge captured during development.
"""

import click
from pathlib import Path
import yaml
from datetime import datetime


@click.group()
def learnings():
    """
    Manage institutional knowledge and learnings.

    Capture patterns, gotchas, and insights discovered during
    AI-assisted development.
    """
    pass


@learnings.command("capture")
@click.argument("title")
@click.option("--category", "-c", required=True, help="Category (e.g., azure-devops, testing)")
@click.option("--content", "-m", required=True, help="Learning content/description")
@click.option("--tags", "-t", multiple=True, help="Tags for searchability")
@click.option("--source", "-s", help="Source (e.g., Sprint 4 planning)")
@click.option("--work-item", "-w", type=int, help="Related work item ID")
def capture(title: str, category: str, content: str, tags: tuple, source: str, work_item: int):
    """
    Capture a new learning.

    Examples:
        trustable-ai learnings capture "Iteration path format" -c azure-devops \\
            -m "Use simplified format: Project\\\\SprintName"

        trustable-ai learnings capture "Test isolation" -c testing \\
            -m "Always use separate database for tests" \\
            -t testing -t database -s "Sprint 3 retro"
    """
    learnings_dir = Path(".claude/learnings")
    learnings_dir.mkdir(parents=True, exist_ok=True)

    learning_id = f"{category}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    learning = {
        "id": learning_id,
        "title": title,
        "content": content,
        "category": category,
        "tags": list(tags) if tags else [],
        "source": source,
        "work_item_id": work_item,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }

    # Save learning
    learning_file = learnings_dir / f"{learning_id}.yaml"
    with open(learning_file, "w", encoding="utf-8") as f:
        yaml.dump(learning, f, default_flow_style=False)

    # Update index
    index_file = learnings_dir / "index.yaml"
    if index_file.exists():
        with open(index_file) as f:
            index = yaml.safe_load(f) or {"learnings": [], "categories": {}}
    else:
        index = {"learnings": [], "categories": {}}

    index["learnings"].append({
        "id": learning_id,
        "title": title,
        "category": category,
        "created_at": learning["created_at"]
    })
    index.setdefault("categories", {}).setdefault(category, []).append(learning_id)

    with open(index_file, "w", encoding="utf-8") as f:
        yaml.dump(index, f, default_flow_style=False)

    click.echo(f"✓ Learning captured: {learning_id}")
    click.echo(f"  Title: {title}")
    click.echo(f"  Category: {category}")


@learnings.command("list")
@click.option("--category", "-c", help="Filter by category")
@click.option("--tag", "-t", help="Filter by tag")
@click.option("--limit", "-n", type=int, default=10, help="Number of results")
def list_learnings(category: str, tag: str, limit: int):
    """
    List captured learnings.

    Examples:
        trustable-ai learnings list
        trustable-ai learnings list -c azure-devops
        trustable-ai learnings list -t security -n 5
    """
    learnings_dir = Path(".claude/learnings")
    index_file = learnings_dir / "index.yaml"

    if not index_file.exists():
        click.echo("No learnings captured yet.")
        click.echo("Use 'trustable-ai learnings capture' to add a learning.")
        return

    with open(index_file) as f:
        index = yaml.safe_load(f)

    entries = index.get("learnings", [])

    # Filter by category
    if category:
        entries = [e for e in entries if e.get("category") == category]

    # Sort by date (newest first)
    entries = sorted(entries, key=lambda x: x.get("created_at", ""), reverse=True)

    # Limit results
    entries = entries[:limit]

    if not entries:
        click.echo("No learnings found matching criteria.")
        return

    click.echo(f"Learnings ({len(entries)} of {len(index.get('learnings', []))})")
    click.echo("-" * 50)

    for entry in entries:
        learning_file = learnings_dir / f"{entry['id']}.yaml"
        if learning_file.exists():
            with open(learning_file) as f:
                learning = yaml.safe_load(f)

            # Filter by tag if specified
            if tag and tag not in learning.get("tags", []):
                continue

            click.echo(f"\n[{learning['category']}] {learning['title']}")
            click.echo(f"  ID: {learning['id']}")
            click.echo(f"  Content: {learning['content'][:100]}...")
            if learning.get("tags"):
                click.echo(f"  Tags: {', '.join(learning['tags'])}")


@learnings.command("show")
@click.argument("learning_id")
def show_learning(learning_id: str):
    """
    Show details of a specific learning.

    Example:
        trustable-ai learnings show azure-devops-20250101120000
    """
    learnings_dir = Path(".claude/learnings")
    learning_file = learnings_dir / f"{learning_id}.yaml"

    if not learning_file.exists():
        click.echo(f"Learning not found: {learning_id}")
        return

    with open(learning_file) as f:
        learning = yaml.safe_load(f)

    click.echo(f"Learning: {learning['title']}")
    click.echo("=" * 50)
    click.echo(f"ID: {learning['id']}")
    click.echo(f"Category: {learning['category']}")
    click.echo(f"Created: {learning['created_at']}")
    if learning.get("source"):
        click.echo(f"Source: {learning['source']}")
    if learning.get("work_item_id"):
        click.echo(f"Work Item: WI-{learning['work_item_id']}")
    if learning.get("tags"):
        click.echo(f"Tags: {', '.join(learning['tags'])}")
    click.echo("\nContent:")
    click.echo("-" * 50)
    click.echo(learning["content"])


@learnings.command("search")
@click.argument("query")
def search_learnings(query: str):
    """
    Search learnings by text.

    Example:
        trustable-ai learnings search "iteration path"
    """
    learnings_dir = Path(".claude/learnings")

    if not learnings_dir.exists():
        click.echo("No learnings captured yet.")
        return

    results = []
    query_lower = query.lower()

    for learning_file in learnings_dir.glob("*.yaml"):
        if learning_file.name == "index.yaml":
            continue

        with open(learning_file) as f:
            learning = yaml.safe_load(f)

        title = learning.get("title", "").lower()
        content = learning.get("content", "").lower()

        if query_lower in title or query_lower in content:
            results.append(learning)

    if not results:
        click.echo(f"No learnings found matching: {query}")
        return

    click.echo(f"Found {len(results)} learning(s) matching '{query}'")
    click.echo("-" * 50)

    for learning in results:
        click.echo(f"\n[{learning['category']}] {learning['title']}")
        click.echo(f"  ID: {learning['id']}")

        # Show snippet with match highlighted
        content = learning.get("content", "")
        if query_lower in content.lower():
            idx = content.lower().find(query_lower)
            start = max(0, idx - 30)
            end = min(len(content), idx + len(query) + 30)
            snippet = content[start:end]
            if start > 0:
                snippet = "..." + snippet
            if end < len(content):
                snippet = snippet + "..."
            click.echo(f"  ...{snippet}...")


@learnings.command("categories")
def list_categories():
    """
    List all learning categories.
    """
    learnings_dir = Path(".claude/learnings")
    index_file = learnings_dir / "index.yaml"

    if not index_file.exists():
        click.echo("No learnings captured yet.")
        return

    with open(index_file) as f:
        index = yaml.safe_load(f)

    categories = index.get("categories", {})

    if not categories:
        click.echo("No categories found.")
        return

    click.echo("Learning Categories")
    click.echo("-" * 30)

    for category, learning_ids in sorted(categories.items()):
        click.echo(f"  {category}: {len(learning_ids)} learning(s)")


@learnings.command("export")
@click.option("--format", "-f", type=click.Choice(["markdown", "json"]), default="markdown")
@click.option("--output", "-o", type=click.Path(), help="Output file")
def export_learnings(format: str, output: str):
    """
    Export learnings for documentation or context.

    Examples:
        trustable-ai learnings export -f markdown -o LEARNINGS.md
        trustable-ai learnings export -f json -o learnings.json
    """
    learnings_dir = Path(".claude/learnings")

    if not learnings_dir.exists():
        click.echo("No learnings to export.")
        return

    all_learnings = []
    for learning_file in learnings_dir.glob("*.yaml"):
        if learning_file.name == "index.yaml":
            continue
        with open(learning_file) as f:
            all_learnings.append(yaml.safe_load(f))

    if not all_learnings:
        click.echo("No learnings to export.")
        return

    # Sort by category, then date
    all_learnings.sort(key=lambda x: (x.get("category", ""), x.get("created_at", "")))

    if format == "markdown":
        content = _export_markdown(all_learnings)
    else:
        import json
        content = json.dumps(all_learnings, indent=2, default=str)

    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(content)
        click.echo(f"✓ Exported {len(all_learnings)} learnings to {output}")
    else:
        click.echo(content)


def _export_markdown(learnings: list) -> str:
    """Export learnings as markdown."""
    lines = ["# Institutional Knowledge\n"]
    lines.append(f"*{len(learnings)} learnings captured*\n")

    # Group by category
    by_category = {}
    for learning in learnings:
        cat = learning.get("category", "general")
        by_category.setdefault(cat, []).append(learning)

    for category in sorted(by_category.keys()):
        lines.append(f"\n## {category.replace('-', ' ').title()}\n")

        for learning in by_category[category]:
            lines.append(f"### {learning['title']}\n")
            lines.append(f"{learning['content']}\n")

            if learning.get("tags"):
                lines.append(f"*Tags: {', '.join(learning['tags'])}*\n")
            if learning.get("source"):
                lines.append(f"*Source: {learning['source']}*\n")

    return "\n".join(lines)
