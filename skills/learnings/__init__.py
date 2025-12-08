"""
Learnings Capture Skill for TAID.

Captures and manages institutional knowledge from AI-assisted development.
"""

from typing import Any, Dict, List, Optional
from pathlib import Path
from datetime import datetime
import json
import yaml


from ..base import BaseSkill


class LearningsSkill(BaseSkill):
    """
    Learnings capture and management skill.

    Captures patterns, gotchas, and institutional knowledge
    discovered during AI-assisted development.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._learnings_dir: Optional[Path] = None
        self._index: Dict[str, List[Dict[str, Any]]] = {}

    @property
    def name(self) -> str:
        return "learnings"

    @property
    def description(self) -> str:
        return "Institutional knowledge capture and management"

    @property
    def version(self) -> str:
        return "1.0.0"

    def initialize(self) -> bool:
        """Initialize learnings directory and load index."""
        try:
            self._learnings_dir = Path(
                self.config.get('learnings_dir', '.claude/learnings')
            )
            self._learnings_dir.mkdir(parents=True, exist_ok=True)

            # Load or create index
            index_path = self._learnings_dir / 'index.yaml'
            if index_path.exists():
                with open(index_path) as f:
                    self._index = yaml.safe_load(f) or {}
            else:
                self._index = {"learnings": [], "categories": {}}

            self._initialized = True
            return True
        except Exception as e:
            self._last_error = str(e)
            return False

    def verify_prerequisites(self) -> Dict[str, Any]:
        """Check prerequisites."""
        return {
            "satisfied": True,
            "missing": [],
            "warnings": []
        }

    def capture(
        self,
        title: str,
        content: str,
        category: str,
        tags: Optional[List[str]] = None,
        source: Optional[str] = None,
        work_item_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Capture a new learning.

        Args:
            title: Short title for the learning
            content: Detailed description of the learning
            category: Category (e.g., "azure-devops", "testing", "architecture")
            tags: Optional tags for searchability
            source: Where this was learned (e.g., "Sprint 4 planning")
            work_item_id: Related work item ID

        Returns:
            Created learning entry
        """
        if not self._initialized:
            raise RuntimeError("Skill not initialized")

        learning_id = f"{category}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        learning = {
            "id": learning_id,
            "title": title,
            "content": content,
            "category": category,
            "tags": tags or [],
            "source": source,
            "work_item_id": work_item_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

        # Save individual learning file
        learning_file = self._learnings_dir / f"{learning_id}.yaml"
        with open(learning_file, 'w', encoding='utf-8') as f:
            yaml.dump(learning, f, default_flow_style=False)

        # Update index
        self._index.setdefault("learnings", []).append({
            "id": learning_id,
            "title": title,
            "category": category,
            "created_at": learning["created_at"]
        })

        self._index.setdefault("categories", {}).setdefault(category, []).append(learning_id)

        self._save_index()

        return learning

    def get(self, learning_id: str) -> Optional[Dict[str, Any]]:
        """Get a learning by ID."""
        if not self._initialized:
            raise RuntimeError("Skill not initialized")

        learning_file = self._learnings_dir / f"{learning_id}.yaml"
        if learning_file.exists():
            with open(learning_file) as f:
                return yaml.safe_load(f)
        return None

    def search(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search learnings.

        Args:
            query: Text to search in title and content
            category: Filter by category
            tags: Filter by tags (any match)

        Returns:
            List of matching learnings
        """
        if not self._initialized:
            raise RuntimeError("Skill not initialized")

        results = []

        for entry in self._index.get("learnings", []):
            learning = self.get(entry["id"])
            if not learning:
                continue

            # Category filter
            if category and learning.get("category") != category:
                continue

            # Tags filter
            if tags:
                learning_tags = learning.get("tags", [])
                if not any(t in learning_tags for t in tags):
                    continue

            # Query filter
            if query:
                query_lower = query.lower()
                title = learning.get("title", "").lower()
                content = learning.get("content", "").lower()
                if query_lower not in title and query_lower not in content:
                    continue

            results.append(learning)

        return results

    def list_categories(self) -> List[str]:
        """List all learning categories."""
        if not self._initialized:
            raise RuntimeError("Skill not initialized")
        return list(self._index.get("categories", {}).keys())

    def get_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get all learnings in a category."""
        return self.search(category=category)

    def get_recent(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most recent learnings."""
        if not self._initialized:
            raise RuntimeError("Skill not initialized")

        entries = sorted(
            self._index.get("learnings", []),
            key=lambda x: x.get("created_at", ""),
            reverse=True
        )[:limit]

        return [self.get(e["id"]) for e in entries if self.get(e["id"])]

    def export_for_context(
        self,
        categories: Optional[List[str]] = None,
        max_entries: int = 20
    ) -> str:
        """
        Export learnings as context for agents.

        Args:
            categories: Categories to include (all if None)
            max_entries: Maximum entries to include

        Returns:
            Formatted learnings for agent context
        """
        if not self._initialized:
            raise RuntimeError("Skill not initialized")

        learnings = []
        if categories:
            for cat in categories:
                learnings.extend(self.get_by_category(cat))
        else:
            learnings = self.get_recent(max_entries)

        # Format for context
        lines = ["## Institutional Knowledge\n"]

        by_category: Dict[str, List[Dict]] = {}
        for learning in learnings[:max_entries]:
            cat = learning.get("category", "general")
            by_category.setdefault(cat, []).append(learning)

        for category, items in by_category.items():
            lines.append(f"\n### {category.replace('-', ' ').title()}\n")
            for item in items:
                lines.append(f"- **{item['title']}**: {item['content'][:200]}...")

        return "\n".join(lines)

    def _save_index(self) -> None:
        """Save the learnings index."""
        index_path = self._learnings_dir / 'index.yaml'
        with open(index_path, 'w', encoding='utf-8') as f:
            yaml.dump(self._index, f, default_flow_style=False)


# Factory function
def get_skill(config: Optional[Dict[str, Any]] = None) -> LearningsSkill:
    """Get an instance of the learnings skill."""
    return LearningsSkill(config)


Skill = LearningsSkill
