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
        trustable-ai context index
        trustable-ai context index -o .claude/context-index.yaml
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
    with open(output_path, "w", encoding='utf-8') as f:
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
        trustable-ai context show
        trustable-ai context show -k
        trustable-ai context show -t
    """
    index_path = Path(".claude/context-index.yaml")

    if not index_path.exists():
        click.echo("Context index not found.")
        click.echo("Run 'trustable-ai context index' to build it.")
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
        trustable-ai context lookup "implement user authentication"
        trustable-ai context lookup "fix database connection issue" -t 8000
    """
    index_path = Path(".claude/context-index.yaml")

    if not index_path.exists():
        click.echo("Context index not found.")
        click.echo("Run 'trustable-ai context index' to build it.")
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
        trustable-ai context load "implement API endpoint"
        trustable-ai context load "fix authentication" -o context.md
    """
    index_path = Path(".claude/context-index.yaml")

    if not index_path.exists():
        click.echo("Context index not found. Run 'trustable-ai context index' first.")
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
        with open(output, "w", encoding='utf-8') as f:
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


@context.command("directed")
@click.argument("task_type", required=False)
@click.option("--keywords", "-k", multiple=True, help="Keywords to match (can specify multiple)")
@click.option("--max-tokens", "-t", type=int, default=8000, help="Maximum tokens to load")
@click.option("--tree", is_flag=True, help="Show the context tree structure")
@click.option("--content", is_flag=True, help="Show the loaded content")
def directed_load(task_type: str, keywords: tuple, max_tokens: int, tree: bool, content: bool):
    """
    Test directed context loading based on CLAUDE.md front matter.

    Uses the DirectedContextLoader to load context files based on
    keywords and task types specified in CLAUDE.md front matter.

    Examples:
        trustable-ai context directed sprint-planning
        trustable-ai context directed --keywords azure --keywords work-item
        trustable-ai context directed sprint-planning -k azure -k workflow --tree
        trustable-ai context directed --tree
    """
    try:
        from core.directed_loader import DirectedContextLoader
    except ImportError:
        click.echo("Error: core.directed_loader module not found")
        click.echo("Make sure you're in the TAID project directory")
        return

    loader = DirectedContextLoader()

    if tree:
        click.echo("Context Tree Structure")
        click.echo("=" * 50)
        tree_data = loader.get_context_tree()
        _print_tree(tree_data, indent=0)
        return

    # Load context
    keywords_list = list(keywords) if keywords else []

    click.echo(f"Loading context for:")
    click.echo(f"  Task Type: {task_type or '(none)'}")
    click.echo(f"  Keywords: {', '.join(keywords_list) if keywords_list else '(none)'}")
    click.echo(f"  Max Tokens: {max_tokens}")
    click.echo("")

    result = loader.load_for_task(
        task_type=task_type,
        keywords=keywords_list,
        max_tokens=max_tokens
    )

    click.echo("Results")
    click.echo("=" * 50)
    click.echo(f"Files Loaded: {len(result['files_loaded'])}")
    click.echo(f"Tokens Used: ~{result['tokens_used']}")
    click.echo("")

    click.echo("Files:")
    for ctx in result.get('contexts', []):
        priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(ctx.priority, "⚪")
        click.echo(f"  {priority_icon} {ctx.path} (~{ctx.tokens_estimated} tokens, {ctx.priority})")

    if content:
        click.echo("")
        click.echo("Content")
        click.echo("=" * 50)
        # Truncate if very long
        content_text = result['content']
        if len(content_text) > 5000:
            click.echo(content_text[:5000])
            click.echo(f"\n... (truncated, {len(content_text)} total chars)")
        else:
            click.echo(content_text)


def _print_tree(node: dict, indent: int = 0):
    """Print context tree recursively."""
    prefix = "  " * indent
    path = node.get("path", "unknown")
    tokens = node.get("tokens", 0)
    priority = node.get("priority", "medium")
    priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(priority, "⚪")

    if node.get("status") == "skipped":
        click.echo(f"{prefix}⏭ {path} (skipped)")
        return
    if node.get("status") == "failed":
        click.echo(f"{prefix}❌ {path} (failed to load)")
        return

    keywords = node.get("keywords", [])[:5]
    keywords_str = f" [{', '.join(keywords)}]" if keywords else ""

    click.echo(f"{prefix}{priority_icon} {path} (~{tokens} tokens){keywords_str}")

    for child in node.get("children", []):
        when = child.get("when", [])
        when_str = f" (when: {', '.join(when[:3])})" if when else ""
        click.echo(f"{prefix}  └─{when_str}")
        _print_tree(child, indent + 2)


def _merge_claude_md_content(existing_content: str, new_front_matter: str) -> str:
    """
    Merge new front matter with existing CLAUDE.md content.

    Preserves user customizations while updating the directed context configuration.
    """
    import re

    # Split existing content into front matter and body
    front_matter_pattern = r'^---\n(.*?)\n---\n'
    match = re.match(front_matter_pattern, existing_content, re.DOTALL)

    if match:
        # File has existing front matter - replace it
        existing_body = existing_content[match.end():]
    else:
        # File has no front matter - preserve entire content as body
        existing_body = existing_content

    # Combine new front matter with existing body
    return new_front_matter + existing_body


@context.command("verify")
@click.option("--root", "-r", type=click.Path(exists=True), default=".", help="Root directory to verify")
@click.option("--fix", "-f", is_flag=True, help="Automatically fix common issues")
def verify_context(root: str, fix: bool):
    """
    Verify generated CLAUDE.md files are accurate and non-stale.

    Checks front matter syntax, validates children references, detects stale
    content, and identifies common issues.

    Examples:
        trustable-ai context verify           # Verify all CLAUDE.md files
        trustable-ai context verify -r src/   # Verify specific directory
        trustable-ai context verify --fix     # Auto-fix common issues
    """
    root_path = Path(root).resolve()

    click.echo(f"\n🔍 Verifying CLAUDE.md files in: {root_path}\n")

    # Find all CLAUDE.md files
    claude_files = list(root_path.rglob("CLAUDE.md"))

    if not claude_files:
        click.echo("❌ No CLAUDE.md files found.")
        click.echo("Run 'trustable-ai context generate' first.")
        return

    click.echo(f"📋 Found {len(claude_files)} CLAUDE.md files to verify\n")

    issues = []
    warnings = []
    passed = 0

    for claude_file in claude_files:
        relative = claude_file.relative_to(root_path)

        try:
            content = claude_file.read_text(encoding="utf-8")

            # Check 1: Empty file
            if not content or not content.strip():
                issues.append(f"❌ {relative}: Empty file")
                continue

            # Check 2: Has front matter
            if not content.startswith("---"):
                warnings.append(f"⚠️  {relative}: Missing YAML front matter")
                continue

            # Check 3: Parse front matter
            import re
            match = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
            if not match:
                issues.append(f"❌ {relative}: Malformed front matter")
                continue

            front_matter_text = match.group(1)
            try:
                front_matter = yaml.safe_load(front_matter_text)
            except yaml.YAMLError as e:
                issues.append(f"❌ {relative}: Invalid YAML - {e}")
                continue

            # Check 4: Has context section
            if "context" not in front_matter:
                warnings.append(f"⚠️  {relative}: Missing 'context' section in front matter")
                continue

            ctx = front_matter["context"]

            # Check 5: Has required fields
            required = ["keywords", "task_types", "priority", "max_tokens"]
            missing = [f for f in required if f not in ctx]
            if missing:
                issues.append(f"❌ {relative}: Missing required fields: {', '.join(missing)}")
                continue

            # Check 6: Validate children paths exist
            children = ctx.get("children", [])
            if children:
                for child in children:
                    # Handle both dict format (with 'path' and 'when') and string format
                    if isinstance(child, dict):
                        child_path_str = child.get("path", "")
                    elif isinstance(child, str):
                        child_path_str = child
                    else:
                        continue

                    if child_path_str:
                        child_path = root_path / child_path_str
                        if not child_path.exists():
                            warnings.append(f"⚠️  {relative}: Child not found: {child_path_str}")

            # Check 7: Staleness (compare to source files)
            dir_path = claude_file.parent
            source_files = []
            for ext in ["*.py", "*.js", "*.ts", "*.tsx", "*.go", "*.rs"]:
                source_files.extend(dir_path.glob(ext))

            if source_files:
                newest_source = max(source_files, key=lambda p: p.stat().st_mtime)
                if newest_source.stat().st_mtime > claude_file.stat().st_mtime:
                    warnings.append(f"⚠️  {relative}: Stale (older than {newest_source.name})")

            # All checks passed
            passed += 1
            click.echo(f"  ✓ {relative}")

        except Exception as e:
            issues.append(f"❌ {relative}: Verification error - {e}")

    # Summary
    click.echo(f"\n{'='*60}")
    click.echo(f"Verification Summary")
    click.echo(f"{'='*60}")
    click.echo(f"  ✅ Passed: {passed}/{len(claude_files)}")
    click.echo(f"  ⚠️  Warnings: {len(warnings)}")
    click.echo(f"  ❌ Errors: {len(issues)}")

    if warnings:
        click.echo(f"\n⚠️  Warnings:\n")
        for warning in warnings:
            click.echo(f"  {warning}")

    if issues:
        click.echo(f"\n❌ Errors:\n")
        for issue in issues:
            click.echo(f"  {issue}")

        if fix:
            click.echo(f"\n🔧 Auto-fix is not yet implemented.")
            click.echo("  Manually regenerate files with: trustable-ai context generate")

    if not issues and not warnings:
        click.echo(f"\n🎉 All CLAUDE.md files are valid!")


@context.command("generate")
@click.option("--root", "-r", type=click.Path(exists=True), default=".", help="Root directory to analyze")
@click.option("--dry-run", is_flag=True, help="Show plan without creating files")
@click.option("--force", "-f", is_flag=True, help="Overwrite existing CLAUDE.md files completely (disables merge)")
@click.option("--no-merge", is_flag=True, help="Skip existing files instead of merging")
@click.option("--depth", "-d", type=int, default=3, help="Maximum directory depth to analyze")
def generate_context(root: str, dry_run: bool, force: bool, no_merge: bool, depth: int):
    """
    Generate hierarchical CLAUDE.md structure for a repository.

    Analyzes the repository structure and creates CLAUDE.md files at key
    directories to provide context for Claude Code.

    By default, existing files are MERGED (front matter updated, content preserved).

    Examples:
        trustable-ai context generate            # Generate/merge for current directory
        trustable-ai context generate --dry-run  # Show plan without creating
        trustable-ai context generate -d 2       # Only go 2 levels deep
        trustable-ai context generate -f         # Overwrite existing files completely
        trustable-ai context generate --no-merge # Skip existing files
    """
    # Merge is default unless --force or --no-merge is specified
    merge = not force and not no_merge

    if force and no_merge:
        click.echo("Error: Cannot use --force and --no-merge together.")
        click.echo("Use --force to completely overwrite, or --no-merge to skip existing files.")
        return
    root_path = Path(root).resolve()

    click.echo(f"\n🔍 Analyzing repository structure: {root_path}\n")

    # Analyze repository
    analysis = _analyze_repository(root_path, depth)

    if not analysis["directories"]:
        click.echo("❌ No significant directories found to document.")
        return

    # Show analysis results
    click.echo(f"📁 Found {len(analysis['directories'])} directories to document:\n")

    for dir_info in analysis["directories"]:
        existing = "✓ exists" if dir_info["has_claude_md"] else "○ needs creation"
        click.echo(f"  {dir_info['relative_path']}/")
        click.echo(f"     {existing} | {dir_info['file_count']} files | Type: {dir_info['type']}")

    if dry_run:
        click.echo("\n📋 Dry run - no files created.")
        click.echo("\nTo create files, run without --dry-run")
        return

    # Generate README.md and CLAUDE.md files
    mode_desc = "merging" if merge else "generating"
    click.echo(f"\n📝 Generating context files (README.md + CLAUDE.md)...\n")

    created_readme = 0
    created_claude = 0
    merged_claude = 0
    skipped = 0

    for dir_info in analysis["directories"]:
        dir_path = root_path / dir_info["relative_path"]
        readme_path = dir_path / "README.md"
        claude_path = dir_path / "CLAUDE.md"

        # Generate README.md (human-readable documentation)
        if readme_path.exists() and not force:
            click.echo(f"  ⏭ {dir_info['relative_path']}/README.md (exists)")
        else:
            readme_content = _generate_readme_content(dir_info, analysis)
            if readme_content and readme_content.strip():
                readme_path.write_text(readme_content, encoding='utf-8')
                click.echo(f"  ✓ {dir_info['relative_path']}/README.md")
                created_readme += 1
            else:
                click.echo(f"  ⚠ {dir_info['relative_path']}/README.md (skipped - empty content)")

        # Generate CLAUDE.md (Claude Code directives)
        if claude_path.exists():
            if merge:
                # Merge mode: update front matter, preserve custom content
                try:
                    existing_content = claude_path.read_text(encoding="utf-8")
                    new_front_matter = _generate_front_matter(dir_info, analysis)
                    merged_content = _merge_claude_md_content(existing_content, new_front_matter)

                    if merged_content and merged_content.strip():
                        claude_path.write_text(merged_content, encoding='utf-8')
                        click.echo(f"  🔄 {dir_info['relative_path']}/CLAUDE.md (merged)")
                        merged_claude += 1
                    else:
                        click.echo(f"  ⚠ {dir_info['relative_path']}/CLAUDE.md (merge failed - empty)")
                        skipped += 1
                except Exception as e:
                    click.echo(f"  ✗ {dir_info['relative_path']}/CLAUDE.md (merge error: {e})")
                    skipped += 1
                continue
            elif not force and not merge:
                click.echo(f"  ⏭ {dir_info['relative_path']}/CLAUDE.md (exists, use -f to overwrite)")
                skipped += 1
                continue

        # Generate new content
        content = _generate_claude_md_content(dir_info, analysis)

        # Validate content is not empty (empty CLAUDE.md files cause API Error 400)
        if not content or not content.strip():
            click.echo(f"  ⚠ {dir_info['relative_path']}/CLAUDE.md (skipped - empty content)")
            skipped += 1
            continue

        # Write file
        claude_path.write_text(content, encoding='utf-8')
        click.echo(f"  ✓ {dir_info['relative_path']}/CLAUDE.md")
        created_claude += 1

    click.echo(f"\n✅ Generation complete!")
    click.echo(f"   README.md created: {created_readme} files")
    click.echo(f"   CLAUDE.md created: {created_claude} files")
    if merged_claude > 0:
        click.echo(f"   CLAUDE.md merged: {merged_claude} files")
    click.echo(f"   Skipped: {skipped} files")

    click.echo("\n📌 Next steps:")
    click.echo("   1. Review generated CLAUDE.md files")
    click.echo("   2. Add project-specific details and guidelines")
    click.echo("   3. Run 'trustable-ai context index' to build the context index")


def _analyze_repository(root: Path, max_depth: int) -> dict:
    """Analyze repository structure to identify key directories."""
    analysis = {
        "root": str(root),
        "directories": [],
        "project_type": None,
        "languages": [],
        "frameworks": []
    }

    # Detect project type from files
    if (root / "package.json").exists():
        analysis["languages"].append("JavaScript/TypeScript")
        analysis["project_type"] = "node"
    if (root / "pyproject.toml").exists() or (root / "setup.py").exists():
        analysis["languages"].append("Python")
        analysis["project_type"] = "python"
    if (root / "go.mod").exists():
        analysis["languages"].append("Go")
        analysis["project_type"] = "go"
    if (root / "Cargo.toml").exists():
        analysis["languages"].append("Rust")
        analysis["project_type"] = "rust"
    if (root / "pom.xml").exists() or (root / "build.gradle").exists():
        analysis["languages"].append("Java")
        analysis["project_type"] = "java"

    # Directory patterns to look for
    important_patterns = {
        "src": "source",
        "lib": "source",
        "app": "source",
        "pkg": "source",
        "packages": "monorepo",
        "tests": "tests",
        "test": "tests",
        "spec": "tests",
        "__tests__": "tests",
        "docs": "documentation",
        "documentation": "documentation",
        "api": "api",
        "apis": "api",
        "services": "services",
        "components": "components",
        "modules": "modules",
        "core": "core",
        "utils": "utilities",
        "helpers": "utilities",
        "common": "shared",
        "shared": "shared",
        "config": "configuration",
        "configs": "configuration",
        "scripts": "scripts",
        "bin": "scripts",
        "terraform": "infrastructure",
        "infra": "infrastructure",
        "infrastructure": "infrastructure",
        "deploy": "deployment",
        "deployment": "deployment",
        ".claude": "claude_config",
        "models": "models",
        "schemas": "schemas",
        "types": "types",
        "interfaces": "interfaces",
        "routes": "routes",
        "controllers": "controllers",
        "handlers": "handlers",
        "middleware": "middleware",
        "plugins": "plugins",
        "extensions": "extensions",
    }

    # Directories to skip
    skip_patterns = {
        "node_modules", "venv", ".venv", "env", ".env",
        "__pycache__", ".git", ".svn", ".hg",
        "dist", "build", "out", "target", "bin", "obj",
        ".idea", ".vscode", ".vs",
        "coverage", ".coverage", "htmlcov",
        ".pytest_cache", ".mypy_cache", ".ruff_cache",
        "eggs", "*.egg-info", ".eggs",
    }

    # Always include root
    root_info = _analyze_directory(root, root, "root")
    analysis["directories"].append(root_info)

    # Walk directory tree
    for item in root.rglob("*"):
        if not item.is_dir():
            continue

        # Check depth
        relative = item.relative_to(root)
        if len(relative.parts) > max_depth:
            continue

        # Skip ignored directories
        if any(skip in relative.parts for skip in skip_patterns):
            continue

        # Check if it's an important directory
        dir_name = item.name.lower()
        dir_type = important_patterns.get(dir_name)

        if dir_type or _is_significant_directory(item):
            dir_info = _analyze_directory(item, root, dir_type or "module")
            analysis["directories"].append(dir_info)

    return analysis


def _analyze_directory(dir_path: Path, root: Path, dir_type: str) -> dict:
    """Analyze a single directory."""
    relative_path = dir_path.relative_to(root) if dir_path != root else Path(".")

    # Count files by type
    files = list(dir_path.glob("*"))
    file_count = len([f for f in files if f.is_file()])

    # Check for existing CLAUDE.md
    has_claude_md = (dir_path / "CLAUDE.md").exists()

    # Detect primary language/purpose
    py_files = len(list(dir_path.glob("*.py")))
    js_files = len(list(dir_path.glob("*.js"))) + len(list(dir_path.glob("*.ts")))
    go_files = len(list(dir_path.glob("*.go")))

    primary_lang = "mixed"
    if py_files > js_files and py_files > go_files:
        primary_lang = "python"
    elif js_files > py_files and js_files > go_files:
        primary_lang = "javascript"
    elif go_files > py_files and go_files > js_files:
        primary_lang = "go"

    # Get subdirectories
    subdirs = [d.name for d in dir_path.iterdir() if d.is_dir() and not d.name.startswith(".")]

    return {
        "path": str(dir_path),
        "relative_path": str(relative_path),
        "type": dir_type,
        "file_count": file_count,
        "has_claude_md": has_claude_md,
        "primary_language": primary_lang,
        "subdirectories": subdirs[:10],  # Limit to first 10
    }


def _is_significant_directory(dir_path: Path) -> bool:
    """Check if a directory is significant enough to document."""
    # Must have at least some code files
    code_extensions = {".py", ".js", ".ts", ".go", ".rs", ".java", ".cpp", ".c", ".rb"}

    code_files = 0
    for ext in code_extensions:
        code_files += len(list(dir_path.glob(f"*{ext}")))

    return code_files >= 2


def _generate_front_matter(dir_info: dict, analysis: dict) -> str:
    """Generate YAML front matter for directed context loading."""
    relative_path = dir_info["relative_path"]
    dir_type = dir_info["type"]

    # Keywords based on directory type
    type_keywords = {
        "root": ["project", "overview", "framework"],
        "source": ["source", "code", "implementation", "feature"],
        "tests": ["test", "testing", "pytest", "coverage", "fixture"],
        "api": ["api", "endpoint", "route", "handler", "rest"],
        "documentation": ["docs", "documentation", "guide", "readme"],
        "infrastructure": ["infrastructure", "terraform", "deploy", "devops"],
        "configuration": ["config", "configuration", "settings", "yaml"],
        "scripts": ["script", "automation", "build", "tool"],
        "services": ["service", "business-logic", "domain"],
        "components": ["component", "ui", "view", "widget"],
        "utilities": ["util", "helper", "common", "shared"],
        "models": ["model", "schema", "entity", "data"],
        "core": ["core", "foundation", "base"],
        "claude_config": ["claude", "runtime", "workflow", "agent"],
        "module": ["module", "feature"],
    }

    # Task types based on directory type
    type_task_types = {
        "root": ["any"],
        "source": ["implementation", "feature-development", "bug-fix"],
        "tests": ["testing", "quality-assurance"],
        "api": ["api-development", "endpoint-implementation"],
        "documentation": ["documentation"],
        "infrastructure": ["infrastructure", "deployment"],
        "configuration": ["configuration", "setup"],
        "scripts": ["scripting", "automation"],
        "services": ["implementation", "business-logic"],
        "core": ["implementation", "architecture"],
        "claude_config": ["workflow", "agent-development"],
    }

    # Priority based on directory type
    type_priority = {
        "root": "high",
        "source": "high",
        "core": "high",
        "tests": "medium",
        "api": "high",
        "infrastructure": "medium",
        "documentation": "low",
        "configuration": "medium",
        "claude_config": "medium",
    }

    # Max tokens based on directory type
    type_max_tokens = {
        "root": 1500,
        "source": 800,
        "tests": 600,
        "api": 800,
        "infrastructure": 600,
        "documentation": 400,
        "core": 800,
    }

    keywords = type_keywords.get(dir_type, ["module", dir_type])
    # Add directory name to keywords
    dir_name = Path(relative_path).name if relative_path != "." else ""
    if dir_name and dir_name not in keywords:
        keywords.append(dir_name.lower().replace("_", "-").replace(".", "-"))

    task_types = type_task_types.get(dir_type, ["implementation"])
    priority = type_priority.get(dir_type, "medium")
    max_tokens = type_max_tokens.get(dir_type, 600)

    # Build children list based on subdirectories in analysis
    children = []
    for d in analysis.get("directories", []):
        d_path = d["relative_path"]
        if d_path == relative_path or d_path == ".":
            continue
        # Check if this is a direct child
        if relative_path == ".":
            # Root: check if d_path has no slashes (direct child)
            if "/" not in d_path:
                child_keywords = type_keywords.get(d["type"], [d["type"]])[:3]
                children.append({
                    "path": f"{d_path}/CLAUDE.md",
                    "when": child_keywords
                })
        else:
            # Check if d_path starts with relative_path/ and has one more level
            prefix = relative_path + "/"
            if d_path.startswith(prefix):
                remainder = d_path[len(prefix):]
                if "/" not in remainder:
                    child_keywords = type_keywords.get(d["type"], [d["type"]])[:3]
                    children.append({
                        "path": f"{d_path}/CLAUDE.md",
                        "when": child_keywords
                    })

    # Build front matter
    lines = ["---", "context:"]
    lines.append(f"  keywords: [{', '.join(keywords[:8])}]")
    lines.append(f"  task_types: [{', '.join(task_types[:3])}]")
    lines.append(f"  priority: {priority}")
    lines.append(f"  max_tokens: {max_tokens}")

    if children:
        lines.append("  children:")
        for child in children[:10]:  # Limit to 10 children
            lines.append(f"    - path: {child['path']}")
            lines.append(f"      when: [{', '.join(child['when'])}]")
    else:
        lines.append("  children: []")

    lines.append("  dependencies: []")
    lines.append("---")

    return "\n".join(lines) + "\n"


def _generate_readme_content(dir_info: dict, analysis: dict) -> str:
    """Generate README.md content for a directory (human-readable documentation).

    README.md is the primary documentation file - what humans see in GitHub/Azure DevOps.
    It should contain real, useful content - never TODOs or placeholder text.
    """
    relative_path = dir_info["relative_path"]
    dir_type = dir_info["type"]
    dir_path = Path(dir_info["path"])

    # Get directory name
    dir_name = Path(relative_path).name if relative_path != "." else Path(analysis["root"]).name

    # Analyze directory contents to generate meaningful documentation
    files = []
    subdirs = []
    for item in sorted(dir_path.iterdir()):
        if item.name.startswith(".") and item.name != ".claude":
            continue
        if item.name in {"node_modules", "venv", "__pycache__", "dist", "build", ".git"}:
            continue
        if item.is_dir():
            subdirs.append(item.name)
        elif item.is_file():
            files.append(item.name)

    # Detect key files and their purposes
    key_components = []
    for f in files:
        if f.endswith(".py"):
            # Try to infer purpose from filename
            base = f.replace(".py", "").replace("_", " ").title()
            if f == "__init__.py":
                continue
            elif f.startswith("test_"):
                key_components.append(f"**{f}**: Tests for {base.replace('Test ', '')}")
            else:
                key_components.append(f"**{f}**: {base} implementation")
        elif f.endswith((".js", ".ts", ".tsx")):
            base = f.split(".")[0].replace("_", " ").replace("-", " ").title()
            key_components.append(f"**{f}**: {base} module")
        elif f in ["package.json", "pyproject.toml", "setup.py", "Cargo.toml", "go.mod"]:
            key_components.append(f"**{f}**: Package configuration")
        elif f in ["Dockerfile", "docker-compose.yml"]:
            key_components.append(f"**{f}**: Container configuration")
        elif f.endswith((".yaml", ".yml", ".json", ".toml")) and "config" in f.lower():
            key_components.append(f"**{f}**: Configuration file")

    # Generate structure listing
    structure_lines = []
    for d in subdirs[:10]:
        structure_lines.append(f"- **{d}/** - Subdirectory")
    for f in files[:15]:
        if f not in ["__init__.py", ".gitignore"]:
            structure_lines.append(f"- {f}")

    structure = "\n".join(structure_lines) if structure_lines else "*(empty)*"

    # Purpose descriptions based on directory type
    purposes = {
        "root": f"{dir_name} project root directory.",
        "source": "Contains the main source code implementation.",
        "tests": "Contains the test suite for quality assurance.",
        "api": "Contains API definitions, endpoints, and request handlers.",
        "documentation": "Contains project documentation and guides.",
        "infrastructure": "Contains infrastructure as code and deployment configurations.",
        "configuration": "Contains configuration files and settings.",
        "scripts": "Contains utility and automation scripts.",
        "services": "Contains service implementations and business logic.",
        "components": "Contains reusable UI or functional components.",
        "utilities": "Contains utility functions and helper modules.",
        "models": "Contains data models and entity definitions.",
        "schemas": "Contains data schemas and validation definitions.",
        "core": "Contains core framework functionality and base implementations.",
        "claude_config": "Contains Claude Code configuration and workflow state.",
        "module": f"Contains the {dir_name} module implementation.",
    }
    purpose = purposes.get(dir_type, f"Contains {dir_name} related code and resources.")

    # Build the README content
    content = f"# {dir_name}\n\n"
    content += f"## Purpose\n\n{purpose}\n\n"

    if key_components:
        content += "## Key Components\n\n"
        for comp in key_components[:10]:
            content += f"- {comp}\n"
        content += "\n"

    if subdirs:
        content += "## Subdirectories\n\n"
        for d in subdirs[:10]:
            content += f"- **{d}/**\n"
        content += "\n"

    content += "## Structure\n\n"
    content += f"```\n{structure}\n```\n"

    return content


def _generate_claude_md_content(dir_info: dict, analysis: dict) -> str:
    """Generate CLAUDE.md content for a directory (Claude Code directives only).

    CLAUDE.md should be lean - just front matter and a brief pointer to README.md.
    All real documentation belongs in README.md where humans expect to find it.
    """
    relative_path = dir_info["relative_path"]
    dir_type = dir_info["type"]

    # Generate front matter for directed context loading
    front_matter = _generate_front_matter(dir_info, analysis)

    # Get directory name
    dir_name = Path(relative_path).name if relative_path != "." else Path(analysis["root"]).name

    # CLAUDE.md should be minimal - just directives for Claude
    # Real documentation goes in README.md
    claude_content = f'''# {dir_name}

## Purpose

See [README.md](README.md) for full documentation.

'''

    return front_matter + claude_content
