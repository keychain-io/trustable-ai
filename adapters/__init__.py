"""
Platform Adapters for TAID.

Provides integrations with various work tracking platforms:
- Azure DevOps (azure_devops)
- File-based local storage (file_based)
"""

from adapters.file_based import FileBasedAdapter

__all__ = ["FileBasedAdapter"]
