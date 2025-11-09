"""
Work item type mapper for Azure DevOps.

Maps generic work item types to platform-specific types,
enabling configuration flexibility across different Azure DevOps
process templates (Agile, Scrum, CMMI, Basic).
"""
from typing import Dict, Optional


class WorkItemTypeMapper:
    """Maps generic work item types to platform-specific types."""

    # Default mappings for Scrum process template
    DEFAULT_MAPPINGS = {
        "epic": "Epic",
        "feature": "Feature",
        "story": "User Story",
        "task": "Task",
        "bug": "Bug",
        "impediment": "Impediment",
    }

    # Alternative mappings for other process templates
    AGILE_MAPPINGS = {
        "epic": "Epic",
        "feature": "Feature",
        "story": "User Story",  # Same as Scrum
        "task": "Task",
        "bug": "Bug",
        "issue": "Issue",  # Agile-specific
    }

    CMMI_MAPPINGS = {
        "epic": "Epic",
        "feature": "Feature",
        "story": "Requirement",  # Different from Scrum
        "task": "Task",
        "bug": "Bug",
        "issue": "Issue",
        "risk": "Risk",  # CMMI-specific
        "review": "Review",  # CMMI-specific
    }

    BASIC_MAPPINGS = {
        "epic": "Epic",
        "story": "Issue",  # Basic only has Issue type
        "task": "Issue",
        "bug": "Issue",
    }

    def __init__(self, config: Optional[Dict[str, str]] = None, process_template: str = "scrum"):
        """
        Initialize the work item type mapper.

        Args:
            config: Custom mapping dictionary (overrides defaults)
            process_template: Azure DevOps process template ("scrum", "agile", "cmmi", "basic")
        """
        # Select base mappings based on process template
        if process_template.lower() == "agile":
            base_mappings = self.AGILE_MAPPINGS.copy()
        elif process_template.lower() == "cmmi":
            base_mappings = self.CMMI_MAPPINGS.copy()
        elif process_template.lower() == "basic":
            base_mappings = self.BASIC_MAPPINGS.copy()
        else:
            base_mappings = self.DEFAULT_MAPPINGS.copy()

        # Override with custom mappings if provided
        if config:
            base_mappings.update(config)

        self.mappings = base_mappings

    def to_platform_type(self, generic_type: str) -> str:
        """
        Convert generic type to platform-specific type.

        Args:
            generic_type: Generic type name (e.g., "story", "task")

        Returns:
            Platform-specific type name (e.g., "User Story", "Task")

        Raises:
            ValueError: If generic type is not mapped
        """
        generic_type_lower = generic_type.lower()
        if generic_type_lower not in self.mappings:
            raise ValueError(
                f"Unknown generic type '{generic_type}'. "
                f"Available types: {', '.join(self.mappings.keys())}"
            )
        return self.mappings[generic_type_lower]

    def to_generic_type(self, platform_type: str) -> str:
        """
        Convert platform-specific type to generic type.

        Args:
            platform_type: Platform type name (e.g., "User Story")

        Returns:
            Generic type name (e.g., "story")

        Raises:
            ValueError: If platform type is not mapped
        """
        # Reverse lookup
        for generic, platform in self.mappings.items():
            if platform == platform_type:
                return generic

        raise ValueError(
            f"Unknown platform type '{platform_type}'. "
            f"Available types: {', '.join(self.mappings.values())}"
        )

    def is_valid_generic_type(self, generic_type: str) -> bool:
        """Check if a generic type is valid."""
        return generic_type.lower() in self.mappings

    def is_valid_platform_type(self, platform_type: str) -> bool:
        """Check if a platform type is valid."""
        return platform_type in self.mappings.values()

    def get_available_types(self) -> Dict[str, str]:
        """Get all available type mappings."""
        return self.mappings.copy()


# Convenience function for simple usage
def get_platform_type(generic_type: str, config: Optional[Dict[str, str]] = None) -> str:
    """
    Quick helper to map a generic type to platform type.

    Args:
        generic_type: Generic type name
        config: Optional custom mappings

    Returns:
        Platform-specific type name
    """
    mapper = WorkItemTypeMapper(config)
    return mapper.to_platform_type(generic_type)
