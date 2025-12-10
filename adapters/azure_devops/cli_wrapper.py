"""
Azure CLI Wrapper - Adapter Layer

This module re-exports the canonical AzureCLI implementation from skills.

IMPORTANT: This is a compatibility layer only. The single source of truth
for AzureCLI is in skills/azure_devops/cli_wrapper.py.

All Azure CLI operations should use the skills implementation to ensure
consistency and prevent code duplication (Bug #1041).
"""

# Re-export everything from the canonical skills implementation
from skills.azure_devops.cli_wrapper import (
    AzureCLI,
    azure_cli,
    query_work_items,
    create_work_item,
    update_work_item,
    add_comment,
    create_pull_request,
    approve_pull_request,
    create_sprint,
    list_sprints,
    update_sprint_dates,
    create_sprint_work_items,
    query_sprint_work_items,
)

__all__ = [
    "AzureCLI",
    "azure_cli",
    "query_work_items",
    "create_work_item",
    "update_work_item",
    "add_comment",
    "create_pull_request",
    "approve_pull_request",
    "create_sprint",
    "list_sprints",
    "update_sprint_dates",
    "create_sprint_work_items",
    "query_sprint_work_items",
]
