"""
Field name mapper for Azure DevOps.

Maps generic field names to platform-specific field names,
enabling support for custom fields and different Azure DevOps
configurations.
"""
from typing import Dict, Optional, Any


class FieldMapper:
    """Maps generic field names to platform-specific field names."""

    # Standard Azure DevOps fields (common across all process templates)
    STANDARD_FIELDS = {
        # Core fields
        "title": "System.Title",
        "description": "System.Description",
        "state": "System.State",
        "reason": "System.Reason",
        "assigned_to": "System.AssignedTo",
        "created_date": "System.CreatedDate",
        "created_by": "System.CreatedBy",
        "changed_date": "System.ChangedDate",
        "changed_by": "System.ChangedBy",
        "work_item_type": "System.WorkItemType",
        "tags": "System.Tags",
        "area_path": "System.AreaPath",
        "iteration_path": "System.IterationPath",

        # Scheduling fields
        "story_points": "Microsoft.VSTS.Scheduling.StoryPoints",
        "effort": "Microsoft.VSTS.Scheduling.Effort",
        "remaining_work": "Microsoft.VSTS.Scheduling.RemainingWork",
        "completed_work": "Microsoft.VSTS.Scheduling.CompletedWork",
        "original_estimate": "Microsoft.VSTS.Scheduling.OriginalEstimate",
        "start_date": "Microsoft.VSTS.Scheduling.StartDate",
        "finish_date": "Microsoft.VSTS.Scheduling.FinishDate",

        # Common VSTS fields
        "priority": "Microsoft.VSTS.Common.Priority",
        "severity": "Microsoft.VSTS.Common.Severity",
        "value_area": "Microsoft.VSTS.Common.ValueArea",
        "risk": "Microsoft.VSTS.Common.Risk",
        "activity": "Microsoft.VSTS.Common.Activity",

        # Acceptance criteria
        "acceptance_criteria": "Microsoft.VSTS.Common.AcceptanceCriteria",

        # Repro steps (for bugs)
        "repro_steps": "Microsoft.VSTS.TCM.ReproSteps",
        "system_info": "Microsoft.VSTS.TCM.SystemInfo",
    }

    def __init__(self, custom_fields: Optional[Dict[str, str]] = None):
        """
        Initialize the field mapper.

        Args:
            custom_fields: Dictionary mapping generic names to custom field names
                          e.g., {"business_value": "Custom.BusinessValueScore"}
        """
        self.custom_fields = custom_fields or {}

    def get_field_name(self, generic_name: str) -> str:
        """
        Get the platform-specific field name for a generic field.

        Args:
            generic_name: Generic field name (e.g., "story_points", "business_value")

        Returns:
            Platform-specific field name (e.g., "Microsoft.VSTS.Scheduling.StoryPoints")

        Raises:
            ValueError: If field name is not mapped
        """
        # Check custom fields first (takes precedence)
        if generic_name in self.custom_fields:
            return self.custom_fields[generic_name]

        # Check standard fields
        if generic_name in self.STANDARD_FIELDS:
            return self.STANDARD_FIELDS[generic_name]

        raise ValueError(
            f"Unknown field '{generic_name}'. "
            f"Available standard fields: {', '.join(self.STANDARD_FIELDS.keys())}. "
            f"Available custom fields: {', '.join(self.custom_fields.keys())}"
        )

    def map_fields(self, generic_fields: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map a dictionary of generic field names to platform-specific names.

        Args:
            generic_fields: Dictionary with generic field names as keys

        Returns:
            Dictionary with platform-specific field names as keys

        Example:
            >>> mapper = FieldMapper({"business_value": "Custom.BusinessValue"})
            >>> mapper.map_fields({"title": "Feature X", "business_value": 100})
            {"System.Title": "Feature X", "Custom.BusinessValue": 100}
        """
        mapped = {}
        for generic_name, value in generic_fields.items():
            try:
                platform_name = self.get_field_name(generic_name)
                mapped[platform_name] = value
            except ValueError:
                # If field is already in platform format, keep it as-is
                if "." in generic_name:
                    mapped[generic_name] = value
                else:
                    raise

        return mapped

    def reverse_map_fields(self, platform_fields: Dict[str, Any]) -> Dict[str, Any]:
        """
        Reverse map platform-specific field names to generic names.

        Args:
            platform_fields: Dictionary with platform-specific field names

        Returns:
            Dictionary with generic field names as keys
        """
        # Create reverse mapping
        reverse_standard = {v: k for k, v in self.STANDARD_FIELDS.items()}
        reverse_custom = {v: k for k, v in self.custom_fields.items()}

        generic = {}
        for platform_name, value in platform_fields.items():
            # Check custom fields first
            if platform_name in reverse_custom:
                generic[reverse_custom[platform_name]] = value
            # Then standard fields
            elif platform_name in reverse_standard:
                generic[reverse_standard[platform_name]] = value
            else:
                # Keep unmapped fields as-is
                generic[platform_name] = value

        return generic

    def is_custom_field(self, field_name: str) -> bool:
        """Check if a field name is a custom field."""
        return field_name in self.custom_fields or field_name.startswith("Custom.")

    def get_available_fields(self) -> Dict[str, str]:
        """Get all available field mappings (standard + custom)."""
        all_fields = self.STANDARD_FIELDS.copy()
        all_fields.update(self.custom_fields)
        return all_fields


class AzureDevOpsFieldBuilder:
    """
    Builder for constructing Azure DevOps field dictionaries.

    Provides a fluent interface for building work item field updates.
    """

    def __init__(self, field_mapper: Optional[FieldMapper] = None):
        """
        Initialize the field builder.

        Args:
            field_mapper: Optional FieldMapper instance (uses default if not provided)
        """
        self.field_mapper = field_mapper or FieldMapper()
        self.fields: Dict[str, Any] = {}

    def set(self, field_name: str, value: Any) -> "AzureDevOpsFieldBuilder":
        """
        Set a field value using generic field name.

        Args:
            field_name: Generic field name
            value: Field value

        Returns:
            Self for chaining
        """
        platform_name = self.field_mapper.get_field_name(field_name)
        self.fields[platform_name] = value
        return self

    def set_custom(self, custom_name: str, value: Any) -> "AzureDevOpsFieldBuilder":
        """
        Set a custom field value directly.

        Args:
            custom_name: Custom field name (e.g., "Custom.BusinessValue")
            value: Field value

        Returns:
            Self for chaining
        """
        self.fields[custom_name] = value
        return self

    def set_multiple(self, fields: Dict[str, Any]) -> "AzureDevOpsFieldBuilder":
        """
        Set multiple fields at once.

        Args:
            fields: Dictionary of generic field names and values

        Returns:
            Self for chaining
        """
        mapped = self.field_mapper.map_fields(fields)
        self.fields.update(mapped)
        return self

    def build(self) -> Dict[str, Any]:
        """
        Build and return the fields dictionary.

        Returns:
            Dictionary with platform-specific field names
        """
        return self.fields.copy()

    def clear(self) -> "AzureDevOpsFieldBuilder":
        """Clear all fields."""
        self.fields = {}
        return self


# Convenience functions
def map_fields(generic_fields: Dict[str, Any], custom_fields: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Quick helper to map generic fields to platform fields.

    Args:
        generic_fields: Dictionary with generic field names
        custom_fields: Optional custom field mappings

    Returns:
        Dictionary with platform-specific field names
    """
    mapper = FieldMapper(custom_fields)
    return mapper.map_fields(generic_fields)


def create_field_builder(custom_fields: Optional[Dict[str, str]] = None) -> AzureDevOpsFieldBuilder:
    """
    Create a new field builder.

    Args:
        custom_fields: Optional custom field mappings

    Returns:
        New AzureDevOpsFieldBuilder instance
    """
    mapper = FieldMapper(custom_fields)
    return AzureDevOpsFieldBuilder(mapper)
