"""
Context Loader for Hierarchical CLAUDE.md Files

Loads relevant CLAUDE.md files based on working directory or task keywords,
reducing token usage by providing only relevant context.

Usage:
    from context_loader import load_hierarchical_context, get_context_for_task

    # Load context for current directory
    context = load_hierarchical_context(Path("src/keychain_gateway/mcp"))

    # Load context based on task description
    context = get_context_for_task("Implement MCP tool for persona creation")
"""

from pathlib import Path
from typing import List, Optional, Dict


def load_hierarchical_context(working_dir: Path) -> str:
    """
    Load all relevant CLAUDE.md files for a given working directory.

    Walks up the directory tree from working_dir to repo root,
    collecting all CLAUDE.md files along the way.

    Args:
        working_dir: Directory to start from

    Returns:
        Combined context from all CLAUDE.md files (root to specific)
    """
    context_files = []

    # Get repo root (assume it's where .git directory is)
    repo_root = Path.cwd()
    while not (repo_root / ".git").exists() and repo_root != repo_root.parent:
        repo_root = repo_root.parent

    # Walk up from working_dir to repo root
    current = working_dir.resolve()

    while current >= repo_root:
        claude_file = current / "CLAUDE.md"
        if claude_file.exists():
            context_files.append(claude_file)
        current = current.parent

    # Reverse to go from root to specific
    context_files.reverse()

    # Build combined context
    context = []
    context.append("# Combined Hierarchical Context\n")
    context.append(f"**Working Directory:** {working_dir}\n")
    context.append("")

    for i, file in enumerate(context_files):
        level = "Root" if i == 0 else f"Level {i}"
        relative_path = file.relative_to(repo_root) if file.is_relative_to(repo_root) else file

        context.append(f"## {level}: {relative_path}")
        context.append("")
        context.append(file.read_text())
        context.append("")
        context.append("---")
        context.append("")

    return "\n".join(context)


def get_context_for_task(task_description: str) -> str:
    """
    Determine which CLAUDE.md files are relevant for a task.

    Uses keyword matching to identify relevant directories and loads
    their CLAUDE.md files.

    Args:
        task_description: Description of the task

    Returns:
        Combined context from relevant CLAUDE.md files
    """
    # Keyword to path mapping
    keywords_to_paths = {
        # MCP-related keywords
        "mcp": "src/keychain_gateway/mcp/CLAUDE.md",
        "model context protocol": "src/keychain_gateway/mcp/CLAUDE.md",
        "sse": "src/keychain_gateway/mcp/CLAUDE.md",
        "server-sent events": "src/keychain_gateway/mcp/CLAUDE.md",
        "mcp tool": "src/keychain_gateway/mcp/CLAUDE.md",
        "mcp server": "src/keychain_gateway/mcp/CLAUDE.md",

        # Test-related keywords
        "test": "tests/CLAUDE.md",
        "testing": "tests/CLAUDE.md",
        "pytest": "tests/CLAUDE.md",
        "fixture": "tests/CLAUDE.md",
        "mock": "tests/CLAUDE.md",
        "integration test": "tests/CLAUDE.md",

        # Infrastructure keywords
        "terraform": "terraform/CLAUDE.md",
        "infrastructure": "terraform/CLAUDE.md",
        "azure resource": "terraform/CLAUDE.md",
        "provision": "terraform/CLAUDE.md",
        "deployment": "terraform/CLAUDE.md",

        # Workflow keywords
        "workflow": ".claude/CLAUDE.md",
        "agent": ".claude/CLAUDE.md",
        "sprint planning": ".claude/CLAUDE.md",
        "sprint execution": ".claude/CLAUDE.md",

        # Azure CLI keywords
        "azure": ".claude/skills/azure-cli-wrapper/CLAUDE.md",
        "azure devops": ".claude/skills/azure-cli-wrapper/CLAUDE.md",
        "work item": ".claude/skills/azure-cli-wrapper/CLAUDE.md",
        "wiql": ".claude/skills/azure-cli-wrapper/CLAUDE.md",
    }

    # Find matching keywords
    task_lower = task_description.lower()
    relevant_files = []

    # Always include root CLAUDE.md
    root_file = Path("CLAUDE.md")
    if root_file.exists():
        relevant_files.append(root_file)

    # Find keyword matches
    for keyword, path in keywords_to_paths.items():
        if keyword in task_lower:
            file_path = Path(path)
            if file_path.exists() and file_path not in relevant_files:
                relevant_files.append(file_path)

    # Build context
    context = []
    context.append("# Context for Task\n")
    context.append(f"**Task:** {task_description}\n")
    context.append(f"**Loaded {len(relevant_files)} context file(s)**\n")
    context.append("")

    for i, file in enumerate(relevant_files, 1):
        context.append(f"## Context {i}: {file}")
        context.append("")
        context.append(file.read_text())
        context.append("")

        if i < len(relevant_files):
            context.append("---")
            context.append("")

    return "\n".join(context)


def list_available_contexts() -> Dict[str, Path]:
    """
    List all available CLAUDE.md files in the project.

    Returns:
        Dict mapping relative path to absolute Path
    """
    repo_root = Path.cwd()
    contexts = {}

    # Find all CLAUDE.md files
    for claude_file in repo_root.rglob("CLAUDE.md"):
        # Skip .git directory
        if ".git" in claude_file.parts:
            continue

        relative_path = claude_file.relative_to(repo_root)
        contexts[str(relative_path)] = claude_file

    return contexts


def get_context_summary() -> str:
    """
    Get a summary of all available context files.

    Returns:
        Markdown formatted summary
    """
    contexts = list_available_contexts()

    summary = []
    summary.append("# Available Context Files\n")
    summary.append(f"Found {len(contexts)} CLAUDE.md files:\n")

    for relative_path, abs_path in sorted(contexts.items()):
        file_size = abs_path.stat().st_size
        line_count = len(abs_path.read_text().splitlines())

        summary.append(f"- **{relative_path}**")
        summary.append(f"  - Size: {file_size:,} bytes")
        summary.append(f"  - Lines: {line_count:,}")
        summary.append("")

    return "\n".join(summary)


def estimate_token_count(text: str) -> int:
    """
    Estimate token count for context text.

    Uses ~4.0 characters per token as average.

    Args:
        text: Text to estimate

    Returns:
        Estimated token count
    """
    return int(len(text) / 4.0)


def get_focused_context(
    task_description: str,
    max_tokens: Optional[int] = None
) -> str:
    """
    Get focused context for task, optionally limiting to token budget.

    Args:
        task_description: Description of task
        max_tokens: Optional maximum token budget

    Returns:
        Context text, potentially truncated to fit budget
    """
    # Get full context
    context = get_context_for_task(task_description)

    # If no token limit, return full context
    if max_tokens is None:
        return context

    # Estimate current token count
    current_tokens = estimate_token_count(context)

    # If under budget, return as-is
    if current_tokens <= max_tokens:
        return context

    # Truncate to fit budget
    # Target 90% of budget to leave room for variance
    target_chars = int(max_tokens * 4.0 * 0.9)

    if len(context) > target_chars:
        context = context[:target_chars]
        context += "\n\n[... Context truncated to fit token budget ...]"

    return context


if __name__ == "__main__":
    # Example usage and CLI interface
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "list":
            print(get_context_summary())

        elif command == "load" and len(sys.argv) > 2:
            path = Path(sys.argv[2])
            context = load_hierarchical_context(path)
            print(context)

        elif command == "task" and len(sys.argv) > 2:
            task = " ".join(sys.argv[2:])
            context = get_context_for_task(task)
            print(context)
            print(f"\n\nEstimated tokens: {estimate_token_count(context):,}")

        elif command == "focused" and len(sys.argv) > 3:
            task = " ".join(sys.argv[2:-1])
            max_tokens = int(sys.argv[-1])
            context = get_focused_context(task, max_tokens)
            print(context)
            print(f"\n\nEstimated tokens: {estimate_token_count(context):,}")

        else:
            print("Unknown command")
            print("Usage:")
            print("  python loader.py list")
            print("  python loader.py load <path>")
            print("  python loader.py task <task description>")
            print("  python loader.py focused <task description> <max_tokens>")

    else:
        print("Usage:")
        print("  python loader.py list")
        print("  python loader.py load <path>")
        print("  python loader.py task <task description>")
        print("  python loader.py focused <task description> <max_tokens>")
        print("\nExamples:")
        print("  python loader.py list")
        print("  python loader.py load src/keychain_gateway/mcp")
        print("  python loader.py task 'Implement MCP tool for persona creation'")
        print("  python loader.py focused 'Write integration tests for MCP' 2000")
