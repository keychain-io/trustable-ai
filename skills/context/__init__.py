"""
Context Management Skill for TAID.

Provides intelligent context loading and optimization.
"""

from typing import Any, Dict, List, Optional
from pathlib import Path

from ..base import BaseSkill


class ContextSkill(BaseSkill):
    """
    Context management skill.

    Provides context loading, indexing, and optimization for workflows.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._context_loader = None
        self._optimized_loader = None

    @property
    def name(self) -> str:
        return "context"

    @property
    def description(self) -> str:
        return "Context loading and optimization for token efficiency"

    @property
    def version(self) -> str:
        return "1.0.0"

    def initialize(self) -> bool:
        """Initialize context loaders."""
        try:
            # Import functions and classes that actually exist
            from core import context_loader
            from core import OptimizedContextLoader

            self._context_loader = context_loader
            self._optimized_loader = OptimizedContextLoader()
            self._initialized = True
            return True
        except ImportError as e:
            self._last_error = f"Context loader modules not available: {e}"
            return False

    def verify_prerequisites(self) -> Dict[str, Any]:
        """Check if context loader modules are available."""
        missing = []
        warnings = []

        try:
            from core import context_loader
        except ImportError:
            missing.append("core.context_loader module")

        try:
            from core import OptimizedContextLoader
        except ImportError:
            warnings.append("core.optimized_loader module (optional)")

        index_path = Path('.claude/context-index.yaml')
        if not index_path.exists():
            warnings.append("Context index not found - run 'trustable-ai context index' to generate")

        return {
            "satisfied": len(missing) == 0,
            "missing": missing,
            "warnings": warnings
        }

    def load_context(
        self,
        keywords: Optional[List[str]] = None,
        path: Optional[Path] = None,
        max_tokens: int = 4000
    ) -> Dict[str, Any]:
        """
        Load context from CLAUDE.md files.

        Args:
            keywords: Keywords to filter relevant context
            path: Starting path for context search
            max_tokens: Maximum tokens to include

        Returns:
            Dict with context content and metadata
        """
        if not self._context_loader:
            raise RuntimeError("Skill not initialized")

        return self._context_loader.load(
            keywords=keywords or [],
            path=path,
            max_tokens=max_tokens
        )

    def load_optimized_context(
        self,
        task_description: str,
        max_tokens: int = 4000
    ) -> Dict[str, Any]:
        """
        Load optimized context based on task description.

        Uses context index for fast template matching.

        Args:
            task_description: Description of the task
            max_tokens: Maximum tokens to include

        Returns:
            Dict with matched templates and context
        """
        if not self._optimized_loader:
            raise RuntimeError("Skill not initialized or optimized loader unavailable")

        return self._optimized_loader.load_for_task(
            task_description,
            max_tokens=max_tokens
        )

    def build_index(
        self,
        root_path: Optional[Path] = None,
        output_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Build or rebuild the context index.

        Args:
            root_path: Root directory to index
            output_path: Path to save index

        Returns:
            Dict with indexing stats
        """
        if not self._optimized_loader:
            raise RuntimeError("Skill not initialized")

        return self._optimized_loader.build_index(
            root_path=root_path or Path('.'),
            output_path=output_path or Path('.claude/context-index.yaml')
        )

    def get_context_for_agent(
        self,
        agent_name: str,
        additional_keywords: Optional[List[str]] = None
    ) -> str:
        """
        Get context optimized for a specific agent.

        Args:
            agent_name: Name of the agent
            additional_keywords: Extra keywords to include

        Returns:
            Context string for the agent
        """
        if not self._context_loader:
            raise RuntimeError("Skill not initialized")

        # Agent-specific keyword mapping
        agent_keywords = {
            "business-analyst": ["requirements", "user stories", "acceptance criteria"],
            "project-architect": ["architecture", "design", "patterns", "security"],
            "senior-engineer": ["implementation", "code", "testing", "api"],
            "security-specialist": ["security", "vulnerabilities", "authentication"],
            "scrum-master": ["sprint", "planning", "workflow", "process"],
        }

        keywords = agent_keywords.get(agent_name, [])
        if additional_keywords:
            keywords.extend(additional_keywords)

        result = self.load_context(keywords=keywords)
        return result.get('content', '')


# Factory function
def get_skill(config: Optional[Dict[str, Any]] = None) -> ContextSkill:
    """Get an instance of the context skill."""
    return ContextSkill(config)


Skill = ContextSkill
