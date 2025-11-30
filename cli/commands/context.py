"""
Context command for TAID CLI.

Manage context index and context loading optimization.
"""

import click
from pathlib import Path
import yaml
from datetime import datetime


@click.group()
def context():
    """
    Manage context index and optimization.

    Build and manage the context index for optimized
    context loading during workflow execution.
    """
    pass


@context.command("index")
@click.option("--output", "-o", type=click.Path(), default=".claude/context-index.yaml")
@click.option("--root", "-r", type=click.Path(exists=True), default=".")
def build_index(output: str, root: str):
    """
    Build or rebuild the context index.

    Scans the project for CLAUDE.md files and other context sources,
    creating an index for fast context lookup.

    Examples:
        taid context index
        taid context index -o .claude/context-index.yaml
    """
    root_path = Path(root)
    output_path = Path(output)

    click.echo(f"Building context index from {root_path}...")

    # Find all CLAUDE.md files
    claude_files = list(root_path.rglob("CLAUDE.md"))
    claude_files.extend(root_path.rglob("claude.md"))

    # Find README files
    readme_files = list(root_path.rglob("README.md"))

    # Build index
    index = {
        "generated_at": datetime.now().isoformat(),
        "root": str(root_path.absolute()),
        "context_files": [],
        "templates": [],
        "keywords": {}
    }

    click.echo(f"Found {len(claude_files)} CLAUDE.md files")
    click.echo(f"Found {len(readme_files)} README.md files")

    # Index CLAUDE.md files
    for file_path in claude_files:
        relative_path = file_path.relative_to(root_path)
        try:
            content = file_path.read_text(encoding="utf-8")
            keywords = _extract_keywords(content)

            entry = {
                "path": str(relative_path),
                "type": "claude_md",
                "size": len(content),
                "keywords": keywords[:20]  # Top 20 keywords
            }
            index["context_files"].append(entry)

            # Build keyword index
            for keyword in keywords:
                index["keywords"].setdefault(keyword.lower(), []).append(str(relative_path))

            click.echo(f"  ✓ {relative_path}")
        except Exception as e:
            click.echo(f"  ✗ {relative_path}: {e}")

    # Index README files (lower priority)
    for file_path in readme_files:
        if file_path.name == "CLAUDE.md":
            continue

        relative_path = file_path.relative_to(root_path)
        # Skip node_modules, venv, etc.
        if any(part.startswith(".") or part in ["node_modules", "venv", "__pycache__"]
               for part in relative_path.parts):
            continue

        try:
            content = file_path.read_text(encoding="utf-8")
            keywords = _extract_keywords(content)

            entry = {
                "path": str(relative_path),
                "type": "readme",
                "size": len(content),
                "keywords": keywords[:10]
            }
            index["context_files"].append(entry)
        except Exception:
            pass

    # Create task templates
    index["templates"] = _generate_templates(index["context_files"])

    # Save index
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        yaml.dump(index, f, default_flow_style=False)

    click.echo(f"\n✓ Context index saved to {output_path}")
    click.echo(f"  Total files indexed: {len(index['context_files'])}")
    click.echo(f"  Unique keywords: {len(index['keywords'])}")
    click.echo(f"  Task templates: {len(index['templates'])}")


@context.command("show")
@click.option("--keywords", "-k", is_flag=True, help="Show keyword index")
@click.option("--templates", "-t", is_flag=True, help="Show task templates")
def show_index(keywords: bool, templates: bool):
    """
    Show context index contents.

    Examples:
        taid context show
        taid context show -k
        taid context show -t
    """
    index_path = Path(".claude/context-index.yaml")

    if not index_path.exists():
        click.echo("Context index not found.")
        click.echo("Run 'taid context index' to build it.")
        return

    with open(index_path) as f:
        index = yaml.safe_load(f)

    click.echo("Context Index")
    click.echo("=" * 50)
    click.echo(f"Generated: {index.get('generated_at', 'Unknown')}")
    click.echo(f"Root: {index.get('root', 'Unknown')}")
    click.echo(f"Files: {len(index.get('context_files', []))}")
    click.echo(f"Keywords: {len(index.get('keywords', {}))}")
    click.echo(f"Templates: {len(index.get('templates', []))}")

    # Show files
    click.echo("\nContext Files:")
    for entry in index.get("context_files", [])[:10]:
        click.echo(f"  - {entry['path']} ({entry['type']})")
    if len(index.get("context_files", [])) > 10:
        click.echo(f"  ... and {len(index['context_files']) - 10} more")

    # Show keywords
    if keywords:
        click.echo("\nTop Keywords:")
        sorted_keywords = sorted(
            index.get("keywords", {}).items(),
            key=lambda x: len(x[1]),
            reverse=True
        )[:20]
        for keyword, files in sorted_keywords:
            click.echo(f"  {keyword}: {len(files)} file(s)")

    # Show templates
    if templates:
        click.echo("\nTask Templates:")
        for template in index.get("templates", []):
            click.echo(f"\n  {template['name']}:")
            click.echo(f"    Pattern: {template.get('pattern', 'N/A')}")
            click.echo(f"    Context: {', '.join(template.get('context_files', [])[:3])}")


@context.command("lookup")
@click.argument("task_description")
@click.option("--max-tokens", "-t", type=int, default=4000, help="Max tokens to return")
def lookup_context(task_description: str, max_tokens: int):
    """
    Look up relevant context for a task.

    Examples:
        taid context lookup "implement user authentication"
        taid context lookup "fix database connection issue" -t 8000
    """
    index_path = Path(".claude/context-index.yaml")

    if not index_path.exists():
        click.echo("Context index not found.")
        click.echo("Run 'taid context index' to build it.")
        return

    with open(index_path) as f:
        index = yaml.safe_load(f)

    # Extract keywords from task description
    task_keywords = _extract_keywords(task_description)

    # Find matching files
    matches = {}
    for keyword in task_keywords:
        keyword_lower = keyword.lower()
        if keyword_lower in index.get("keywords", {}):
            for file_path in index["keywords"][keyword_lower]:
                matches[file_path] = matches.get(file_path, 0) + 1

    if not matches:
        click.echo("No relevant context found.")
        click.echo("Try different keywords or rebuild the index.")
        return

    # Sort by relevance
    sorted_matches = sorted(matches.items(), key=lambda x: x[1], reverse=True)

    click.echo(f"Context for: {task_description}")
    click.echo("=" * 50)
    click.echo(f"Keywords extracted: {', '.join(task_keywords[:10])}")
    click.echo(f"\nRelevant files (by match count):")

    total_tokens = 0
    selected_files = []

    for file_path, count in sorted_matches:
        # Estimate tokens (rough: 4 chars per token)
        path = Path(file_path)
        if path.exists():
            size = path.stat().st_size
            estimated_tokens = size // 4

            if total_tokens + estimated_tokens <= max_tokens:
                selected_files.append(file_path)
                total_tokens += estimated_tokens
                click.echo(f"  ✓ {file_path} ({count} matches, ~{estimated_tokens} tokens)")
            else:
                click.echo(f"  - {file_path} ({count} matches, skipped - token limit)")
        else:
            click.echo(f"  - {file_path} ({count} matches, file not found)")

    click.echo(f"\nSelected {len(selected_files)} files (~{total_tokens} tokens)")


@context.command("load")
@click.argument("task_description")
@click.option("--output", "-o", type=click.Path(), help="Output file")
def load_context(task_description: str, output: str):
    """
    Load and combine context for a task.

    Examples:
        taid context load "implement API endpoint"
        taid context load "fix authentication" -o context.md
    """
    index_path = Path(".claude/context-index.yaml")

    if not index_path.exists():
        click.echo("Context index not found. Run 'taid context index' first.")
        return

    with open(index_path) as f:
        index = yaml.safe_load(f)

    # Find relevant files
    task_keywords = _extract_keywords(task_description)
    matches = {}

    for keyword in task_keywords:
        keyword_lower = keyword.lower()
        if keyword_lower in index.get("keywords", {}):
            for file_path in index["keywords"][keyword_lower]:
                matches[file_path] = matches.get(file_path, 0) + 1

    sorted_matches = sorted(matches.items(), key=lambda x: x[1], reverse=True)[:5]

    # Load and combine content
    combined = [f"# Context for: {task_description}\n"]
    combined.append(f"*Generated: {datetime.now().isoformat()}*\n")

    for file_path, count in sorted_matches:
        path = Path(file_path)
        if path.exists():
            try:
                content = path.read_text(encoding="utf-8")
                combined.append(f"\n---\n## From: {file_path}\n")
                combined.append(content)
            except Exception as e:
                combined.append(f"\n*Error loading {file_path}: {e}*\n")

    result = "\n".join(combined)

    if output:
        with open(output, "w") as f:
            f.write(result)
        click.echo(f"✓ Context saved to {output}")
    else:
        click.echo(result)


def _extract_keywords(text: str) -> list:
    """Extract keywords from text."""
    import re

    # Common stop words to exclude
    stop_words = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "must", "shall", "can", "need", "dare",
        "ought", "used", "to", "of", "in", "for", "on", "with", "at", "by",
        "from", "as", "into", "through", "during", "before", "after",
        "above", "below", "between", "under", "again", "further", "then",
        "once", "here", "there", "when", "where", "why", "how", "all",
        "each", "few", "more", "most", "other", "some", "such", "no", "nor",
        "not", "only", "own", "same", "so", "than", "too", "very", "just",
        "and", "but", "if", "or", "because", "until", "while", "this",
        "that", "these", "those", "it", "its", "you", "your", "we", "our"
    }

    # Extract words
    words = re.findall(r'\b[a-zA-Z][a-zA-Z0-9_-]{2,}\b', text.lower())

    # Filter and count
    word_counts = {}
    for word in words:
        if word not in stop_words and len(word) > 2:
            word_counts[word] = word_counts.get(word, 0) + 1

    # Sort by frequency
    sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)

    return [word for word, count in sorted_words]


def _generate_templates(context_files: list) -> list:
    """Generate task templates based on context files."""
    templates = []

    # Group files by directory
    by_dir = {}
    for entry in context_files:
        path = Path(entry["path"])
        dir_name = str(path.parent)
        by_dir.setdefault(dir_name, []).append(entry)

    # Generate templates for each directory group
    for dir_name, files in by_dir.items():
        if dir_name == ".":
            continue

        # Combine keywords
        all_keywords = []
        for f in files:
            all_keywords.extend(f.get("keywords", []))

        unique_keywords = list(set(all_keywords))[:5]

        if unique_keywords:
            templates.append({
                "name": f"{dir_name} context",
                "pattern": f".*({'|'.join(unique_keywords[:3])}).*",
                "context_files": [f["path"] for f in files],
                "keywords": unique_keywords
            })

    return templates
