"""
Skill Registry for TAID.

Manages discovery, loading, and access to skills.
"""

from pathlib import Path
from typing import Dict, List, Optional, Type, Any
import importlib
import pkgutil

from .base import BaseSkill


class SkillRegistry:
    """
    Registry for managing TAID skills.

    Provides discovery, loading, and access to skill implementations.
    """

    def __init__(self):
        """Initialize the skill registry."""
        self._skills: Dict[str, BaseSkill] = {}
        self._skill_classes: Dict[str, Type[BaseSkill]] = {}
        self._discovered = False

    def discover_skills(self) -> List[str]:
        """
        Discover available skills in the skills directory.

        Returns:
            List of discovered skill names
        """
        skills_dir = Path(__file__).parent
        discovered = []

        for item in skills_dir.iterdir():
            if item.is_dir() and not item.name.startswith("_"):
                # Check if it has an __init__.py
                init_file = item / "__init__.py"
                if init_file.exists():
                    # Verify it's actually a skill by checking if it can be loaded
                    try:
                        module_name = f"skills.{item.name}"
                        module = importlib.import_module(module_name)

                        # Check if module has skill pattern
                        has_skill = (
                            hasattr(module, "get_skill") or
                            hasattr(module, "Skill") or
                            any(
                                isinstance(getattr(module, attr_name), type) and
                                issubclass(getattr(module, attr_name), BaseSkill) and
                                getattr(module, attr_name) is not BaseSkill
                                for attr_name in dir(module)
                                if not attr_name.startswith("_")
                            )
                        )

                        if has_skill:
                            discovered.append(item.name)
                    except Exception:
                        # Skip modules that can't be imported or don't have skills
                        pass

        self._discovered = True
        return discovered

    def register_skill(self, name: str, skill_class: Type[BaseSkill]) -> None:
        """
        Register a skill class.

        Args:
            name: Skill name
            skill_class: Skill class (subclass of BaseSkill)
        """
        self._skill_classes[name] = skill_class

    def get_skill(
        self,
        name: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Optional[BaseSkill]:
        """
        Get a skill instance by name.

        Args:
            name: Skill name
            config: Optional configuration for the skill

        Returns:
            Skill instance or None if not found
        """
        # Return cached instance if available
        if name in self._skills:
            return self._skills[name]

        # Try to load the skill
        skill = self._load_skill(name, config)
        if skill:
            self._skills[name] = skill

        return skill

    def _load_skill(
        self,
        name: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Optional[BaseSkill]:
        """
        Load a skill by name.

        Args:
            name: Skill name (directory name under skills/)
            config: Optional configuration

        Returns:
            Skill instance or None
        """
        # Check if we have a registered class
        if name in self._skill_classes:
            return self._skill_classes[name](config)

        # Try to import from the skill module
        try:
            module_name = f"skills.{name}"
            module = importlib.import_module(module_name)

            # Look for a get_skill function or a default skill class
            if hasattr(module, "get_skill"):
                return module.get_skill(config)
            elif hasattr(module, "Skill"):
                return module.Skill(config)
            else:
                # Look for any BaseSkill subclass
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and
                        issubclass(attr, BaseSkill) and
                        attr is not BaseSkill):
                        return attr(config)

        except ImportError as e:
            print(f"Warning: Could not load skill '{name}': {e}")

        return None

    def list_skills(self) -> List[str]:
        """
        List all available skill names.

        Returns:
            List of skill names
        """
        if not self._discovered:
            self.discover_skills()

        return self.discover_skills()

    def get_skill_info(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a skill.

        Args:
            name: Skill name

        Returns:
            Dict with skill info (name, description, version, doc_path)
        """
        skill = self.get_skill(name)
        if not skill:
            return None

        return {
            "name": skill.name,
            "description": skill.description,
            "version": skill.version,
            "documentation_path": str(skill.get_documentation_path()) if skill.get_documentation_path() else None,
            "initialized": skill.is_initialized,
            "prerequisites": skill.verify_prerequisites()
        }

    def initialize_all(self) -> Dict[str, bool]:
        """
        Initialize all discovered skills.

        Returns:
            Dict mapping skill name to initialization success
        """
        results = {}
        for name in self.list_skills():
            skill = self.get_skill(name)
            if skill:
                results[name] = skill.initialize()
            else:
                results[name] = False
        return results


# Global registry instance
_registry: Optional[SkillRegistry] = None


def get_registry() -> SkillRegistry:
    """Get the global skill registry instance."""
    global _registry
    if _registry is None:
        _registry = SkillRegistry()
    return _registry


def get_skill(name: str, config: Optional[Dict[str, Any]] = None) -> Optional[BaseSkill]:
    """
    Convenience function to get a skill by name.

    Args:
        name: Skill name
        config: Optional configuration

    Returns:
        Skill instance or None
    """
    return get_registry().get_skill(name, config)


def list_skills() -> List[str]:
    """
    Convenience function to list all available skills.

    Returns:
        List of skill names
    """
    return get_registry().list_skills()
