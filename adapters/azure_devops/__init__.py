"""
Azure DevOps adapters for Claude Workflow Framework.

Provides type mapping, field mapping, and Azure CLI integration.
"""

__all__ = [
    "WorkItemTypeMapper",
    "FieldMapper",
    "get_platform_type",
    "map_fields",
]

# Avoid importing cli_wrapper by default (it requires azure CLI)
# These will be imported on demand
