"""
Base class for TAID skills.

Skills are reusable capabilities that can be used across workflows and agents.
Each skill should:
1. Implement a clear interface for its functionality
2. Include documentation (SKILL.md)
3. Handle errors gracefully
4. Support verification where applicable
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pathlib import Path


class BaseSkill(ABC):
    """Abstract base class for TAID skills."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the skill with optional configuration.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self._initialized = False

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the skill name."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Return a brief description of the skill."""
        pass

    @property
    def version(self) -> str:
        """Return the skill version."""
        return "1.0.0"

    def initialize(self) -> bool:
        """
        Initialize the skill (e.g., check prerequisites, load config).

        Returns:
            True if initialization successful, False otherwise
        """
        self._initialized = True
        return True

    @property
    def is_initialized(self) -> bool:
        """Check if skill is initialized."""
        return self._initialized

    def get_documentation_path(self) -> Optional[Path]:
        """
        Get the path to this skill's documentation (SKILL.md).

        Returns:
            Path to SKILL.md if it exists, None otherwise
        """
        # Try to find SKILL.md in the skill's directory
        skill_dir = Path(__file__).parent / self.name.replace("-", "_")
        skill_md = skill_dir / "SKILL.md"

        if skill_md.exists():
            return skill_md
        return None

    def get_documentation(self) -> Optional[str]:
        """
        Load and return the skill's documentation.

        Returns:
            Documentation content or None
        """
        doc_path = self.get_documentation_path()
        if doc_path and doc_path.exists():
            return doc_path.read_text()
        return None

    def verify_prerequisites(self) -> Dict[str, Any]:
        """
        Check if prerequisites for this skill are met.

        Returns:
            Dict with keys: satisfied (bool), missing (list), warnings (list)
        """
        return {
            "satisfied": True,
            "missing": [],
            "warnings": []
        }

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.name}, version={self.version})>"


class VerifiableSkill(BaseSkill):
    """
    Base class for skills that support operation verification.

    Verification ensures that operations complete successfully by
    re-checking the result after execution.
    """

    def _verify_operation(
        self,
        operation: str,
        success: bool,
        result: Any,
        verification_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a standardized verification result.

        Args:
            operation: Name of the operation
            success: Whether operation succeeded
            result: The operation result
            verification_data: Additional verification details

        Returns:
            Verification dict with: success, operation, result, verification
        """
        return {
            "success": success,
            "operation": operation,
            "result": result,
            "verification": verification_data
        }
