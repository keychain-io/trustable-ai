"""
Directed Context Loader for CLAUDE.md Files

Loads context hierarchically based on directives embedded in each CLAUDE.md file.
Each file's front matter controls what child contexts are loaded, enabling
efficient, task-specific context loading with minimal token usage.

Usage:
    from core.directed_loader import DirectedContextLoader

    loader = DirectedContextLoader()
    result = loader.load_for_task(
        task_type="sprint-planning",
        keywords=["azure", "work-item"],
        max_tokens=8000
    )
    print(result["content"])
    print(f"Loaded {result['files_loaded']} files, ~{result['tokens_used']} tokens")
"""

import re
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field


@dataclass
class ContextDirective:
    """Parsed context directives from CLAUDE.md front matter."""
    keywords: List[str] = field(default_factory=list)
    task_types: List[str] = field(default_factory=list)
    priority: str = "medium"  # high, medium, low
    max_tokens: Optional[int] = None
    children: List[Dict[str, Any]] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContextDirective":
        """Create directive from parsed YAML dict."""
        context = data.get("context", {})
        return cls(
            keywords=context.get("keywords", []),
            task_types=context.get("task_types", []),
            priority=context.get("priority", "medium"),
            max_tokens=context.get("max_tokens"),
            children=context.get("children", []),
            dependencies=context.get("dependencies", []),
        )


@dataclass
class LoadedContext:
    """Result of loading a single CLAUDE.md file."""
    path: Path
    content: str
    directive: ContextDirective
    tokens_estimated: int
    priority: str


class DirectedContextLoader:
    """
    Loads CLAUDE.md files based on embedded directives.

    Each CLAUDE.md can have YAML front matter that specifies:
    - keywords: What keywords make this context relevant
    - task_types: What task types this context applies to
    - priority: How important this context is (affects token allocation)
    - max_tokens: Maximum tokens to use from this file
    - children: Child contexts to potentially load
    - dependencies: Other contexts that must be loaded first

    Example front matter:
    ```yaml
    ---
    context:
      keywords: [sprint, planning, backlog, workflow]
      task_types: [sprint-planning, backlog-grooming]
      priority: high
      max_tokens: 800
      children:
        - path: agents/CLAUDE.md
          when: [agent, analyst, architect, engineer]
        - path: workflows/CLAUDE.md
          when: [workflow, sprint, planning]
        - path: adapters/azure_devops/CLAUDE.md
          when: [azure, devops, work-item]
      dependencies: []
    ---
    # Directory Name
    ...
    ```
    """

    FRONT_MATTER_PATTERN = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)
    CHARS_PER_TOKEN = 4.0

    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize the directed context loader.

        Args:
            project_root: Root directory of the project. Defaults to cwd.
        """
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self._cache: Dict[str, LoadedContext] = {}

    def load_for_task(
        self,
        task_type: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        max_tokens: int = 8000,
        include_all_high_priority: bool = True
    ) -> Dict[str, Any]:
        """
        Load relevant context for a task.

        Starts from root CLAUDE.md and follows children directives
        based on task_type and keywords.

        Args:
            task_type: Type of task (e.g., "sprint-planning", "implementation")
            keywords: Keywords describing the task
            max_tokens: Maximum total tokens to load
            include_all_high_priority: Always include high-priority contexts

        Returns:
            Dict containing:
                - content: Combined context content
                - files_loaded: List of files that were loaded
                - tokens_used: Estimated token count
                - contexts: List of LoadedContext objects
        """
        keywords = keywords or []
        keywords_lower = {k.lower() for k in keywords}
        if task_type:
            keywords_lower.add(task_type.lower())

        # Track what we've loaded
        loaded_contexts: List[LoadedContext] = []
        loaded_paths: Set[Path] = set()
        tokens_remaining = max_tokens

        # Start from root CLAUDE.md
        root_claude = self.project_root / "CLAUDE.md"
        if root_claude.exists():
            self._load_recursive(
                root_claude,
                keywords_lower,
                task_type,
                loaded_contexts,
                loaded_paths,
                tokens_remaining,
                include_all_high_priority
            )

        # Also check .claude/CLAUDE.md (common location)
        claude_dir = self.project_root / ".claude" / "CLAUDE.md"
        if claude_dir.exists() and claude_dir not in loaded_paths:
            self._load_recursive(
                claude_dir,
                keywords_lower,
                task_type,
                loaded_contexts,
                loaded_paths,
                tokens_remaining - sum(c.tokens_estimated for c in loaded_contexts),
                include_all_high_priority
            )

        # Sort by priority: high first, then medium, then low
        priority_order = {"high": 0, "medium": 1, "low": 2}
        loaded_contexts.sort(key=lambda c: priority_order.get(c.priority, 1))

        # Build combined content within token budget
        combined_parts = []
        total_tokens = 0
        final_files = []

        for ctx in loaded_contexts:
            if total_tokens + ctx.tokens_estimated <= max_tokens:
                combined_parts.append(f"<!-- Context: {ctx.path} -->\n{ctx.content}")
                total_tokens += ctx.tokens_estimated
                final_files.append(str(ctx.path))
            elif include_all_high_priority and ctx.priority == "high":
                # Always include high priority, even if over budget
                combined_parts.append(f"<!-- Context: {ctx.path} (high priority) -->\n{ctx.content}")
                total_tokens += ctx.tokens_estimated
                final_files.append(str(ctx.path))

        return {
            "content": "\n\n---\n\n".join(combined_parts),
            "files_loaded": final_files,
            "tokens_used": total_tokens,
            "contexts": loaded_contexts,
        }

    def _load_recursive(
        self,
        file_path: Path,
        keywords: Set[str],
        task_type: Optional[str],
        loaded_contexts: List[LoadedContext],
        loaded_paths: Set[Path],
        tokens_remaining: int,
        include_all_high_priority: bool
    ) -> None:
        """
        Recursively load a CLAUDE.md file and its children.

        Args:
            file_path: Path to CLAUDE.md file
            keywords: Set of keywords to match
            task_type: Task type to match
            loaded_contexts: List to append loaded contexts to
            loaded_paths: Set of already loaded paths (avoid duplicates)
            tokens_remaining: Token budget remaining
            include_all_high_priority: Include high priority regardless of match
        """
        # Avoid duplicates
        abs_path = file_path.resolve()
        if abs_path in loaded_paths:
            return

        if not file_path.exists():
            return

        # Load and parse file
        loaded = self._load_file(file_path)
        if not loaded:
            return

        # Check if this context is relevant
        is_relevant = self._is_relevant(loaded.directive, keywords, task_type)
        is_high_priority = loaded.directive.priority == "high"

        if is_relevant or (include_all_high_priority and is_high_priority):
            loaded_paths.add(abs_path)
            loaded_contexts.append(loaded)
            tokens_remaining -= loaded.tokens_estimated

        # Follow children directives
        for child in loaded.directive.children:
            child_path = child.get("path", "")
            when_keywords = {k.lower() for k in child.get("when", [])}

            # Check if any of the child's "when" keywords match
            if not when_keywords or keywords & when_keywords:
                full_child_path = self.project_root / child_path
                if full_child_path.exists():
                    self._load_recursive(
                        full_child_path,
                        keywords,
                        task_type,
                        loaded_contexts,
                        loaded_paths,
                        tokens_remaining,
                        include_all_high_priority
                    )

    def _load_file(self, file_path: Path) -> Optional[LoadedContext]:
        """
        Load a single CLAUDE.md file.

        Args:
            file_path: Path to the file

        Returns:
            LoadedContext or None if file can't be loaded
        """
        # Check cache
        cache_key = str(file_path.resolve())
        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception:
            return None

        # Parse front matter
        directive = self._parse_front_matter(content)

        # Remove front matter from content for output
        content_without_front_matter = self.FRONT_MATTER_PATTERN.sub("", content)

        # Apply max_tokens limit if specified
        if directive.max_tokens:
            max_chars = int(directive.max_tokens * self.CHARS_PER_TOKEN)
            if len(content_without_front_matter) > max_chars:
                content_without_front_matter = content_without_front_matter[:max_chars]
                content_without_front_matter += "\n\n<!-- Content truncated to fit token budget -->"

        # Estimate tokens
        tokens_estimated = int(len(content_without_front_matter) / self.CHARS_PER_TOKEN)

        loaded = LoadedContext(
            path=file_path,
            content=content_without_front_matter,
            directive=directive,
            tokens_estimated=tokens_estimated,
            priority=directive.priority,
        )

        self._cache[cache_key] = loaded
        return loaded

    def _parse_front_matter(self, content: str) -> ContextDirective:
        """
        Parse YAML front matter from content.

        Args:
            content: File content potentially containing front matter

        Returns:
            ContextDirective with parsed values or defaults
        """
        match = self.FRONT_MATTER_PATTERN.match(content)
        if not match:
            return ContextDirective()

        try:
            front_matter = yaml.safe_load(match.group(1))
            if isinstance(front_matter, dict):
                return ContextDirective.from_dict(front_matter)
        except yaml.YAMLError:
            pass

        return ContextDirective()

    def _is_relevant(
        self,
        directive: ContextDirective,
        keywords: Set[str],
        task_type: Optional[str]
    ) -> bool:
        """
        Check if a context is relevant based on keywords and task type.

        Args:
            directive: The context's directive
            keywords: Keywords to match
            task_type: Task type to match

        Returns:
            True if the context is relevant
        """
        # If no keywords or task_types specified, always include
        if not directive.keywords and not directive.task_types:
            return True

        # Check task type match
        if task_type and directive.task_types:
            if task_type.lower() in [t.lower() for t in directive.task_types]:
                return True

        # Check keyword match
        if keywords and directive.keywords:
            directive_keywords = {k.lower() for k in directive.keywords}
            if keywords & directive_keywords:
                return True

        return False

    def clear_cache(self) -> None:
        """Clear the file cache."""
        self._cache.clear()

    def get_context_tree(self) -> Dict[str, Any]:
        """
        Get the full context tree starting from root.

        Returns:
            Dict representing the context tree structure
        """
        root_claude = self.project_root / "CLAUDE.md"
        if not root_claude.exists():
            return {"error": "No root CLAUDE.md found"}

        return self._build_tree(root_claude, set())

    def _build_tree(self, file_path: Path, visited: Set[Path]) -> Dict[str, Any]:
        """Build context tree recursively."""
        abs_path = file_path.resolve()
        if abs_path in visited or not file_path.exists():
            return {"path": str(file_path), "status": "skipped"}

        visited.add(abs_path)
        loaded = self._load_file(file_path)

        if not loaded:
            return {"path": str(file_path), "status": "failed"}

        children_tree = []
        for child in loaded.directive.children:
            child_path = self.project_root / child.get("path", "")
            child_tree = self._build_tree(child_path, visited)
            child_tree["when"] = child.get("when", [])
            children_tree.append(child_tree)

        return {
            "path": str(file_path),
            "keywords": loaded.directive.keywords,
            "task_types": loaded.directive.task_types,
            "priority": loaded.directive.priority,
            "tokens": loaded.tokens_estimated,
            "children": children_tree,
        }


# Convenience functions

def load_context_for_task(
    task_type: Optional[str] = None,
    keywords: Optional[List[str]] = None,
    max_tokens: int = 8000,
    project_root: Optional[Path] = None
) -> str:
    """
    Load context for a task (convenience function).

    Args:
        task_type: Type of task
        keywords: Keywords describing the task
        max_tokens: Maximum tokens to load
        project_root: Project root directory

    Returns:
        Combined context content
    """
    loader = DirectedContextLoader(project_root)
    result = loader.load_for_task(task_type, keywords, max_tokens)
    return result["content"]


def load_context_with_metadata(
    task_type: Optional[str] = None,
    keywords: Optional[List[str]] = None,
    max_tokens: int = 8000,
    project_root: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Load context with full metadata.

    Args:
        task_type: Type of task
        keywords: Keywords describing the task
        max_tokens: Maximum tokens to load
        project_root: Project root directory

    Returns:
        Dict with content, files_loaded, tokens_used, contexts
    """
    loader = DirectedContextLoader(project_root)
    return loader.load_for_task(task_type, keywords, max_tokens)


if __name__ == "__main__":
    import sys
    import json

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python directed_loader.py tree")
        print("  python directed_loader.py load <task_type> [keywords...]")
        print("")
        print("Examples:")
        print("  python directed_loader.py tree")
        print("  python directed_loader.py load sprint-planning azure work-item")
        sys.exit(1)

    command = sys.argv[1]
    loader = DirectedContextLoader()

    if command == "tree":
        tree = loader.get_context_tree()
        print(json.dumps(tree, indent=2))

    elif command == "load":
        task_type = sys.argv[2] if len(sys.argv) > 2 else None
        keywords = sys.argv[3:] if len(sys.argv) > 3 else []

        result = loader.load_for_task(task_type, keywords)

        print(f"Task Type: {task_type}")
        print(f"Keywords: {keywords}")
        print(f"Files Loaded: {len(result['files_loaded'])}")
        print(f"Tokens Used: {result['tokens_used']}")
        print("")
        print("Files:")
        for f in result["files_loaded"]:
            print(f"  - {f}")
        print("")
        print("--- CONTENT ---")
        print(result["content"][:2000] + "..." if len(result["content"]) > 2000 else result["content"])

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
