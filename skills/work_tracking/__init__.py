"""
Unified Work Tracking Adapter for TAID.

Provides a platform-agnostic interface for work item operations,
automatically selecting the right backend (Azure DevOps or file-based)
based on configuration.

Usage in workflows:
    from work_tracking import get_adapter

    adapter = get_adapter()  # Auto-selects based on config
    adapter.create_work_item(type="Task", title="My task", ...)
    adapter.query_work_items(iteration="Sprint 1")
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable
import yaml


@runtime_checkable
class WorkTrackingAdapter(Protocol):
    """Protocol defining the work tracking adapter interface."""

    def create_work_item(
        self,
        work_item_type: str,
        title: str,
        description: str = "",
        assigned_to: Optional[str] = None,
        iteration: Optional[str] = None,
        fields: Optional[Dict[str, Any]] = None,
        parent_id: Optional[int] = None,
        verify: bool = False
    ) -> Dict[str, Any]: ...

    def update_work_item(
        self,
        work_item_id: int,
        state: Optional[str] = None,
        assigned_to: Optional[str] = None,
        fields: Optional[Dict[str, Any]] = None,
        verify: bool = False
    ) -> Dict[str, Any]: ...

    def get_work_item(self, work_item_id: int) -> Optional[Dict[str, Any]]: ...

    def query_work_items(
        self,
        iteration: Optional[str] = None,
        state: Optional[str] = None,
        work_item_type: Optional[str] = None,
        assigned_to: Optional[str] = None
    ) -> List[Dict[str, Any]]: ...

    def add_comment(
        self,
        work_item_id: int,
        comment: str,
        author: Optional[str] = None
    ) -> Dict[str, Any]: ...

    def create_work_item_idempotent(
        self,
        title: str,
        work_item_type: str,
        description: str = "",
        sprint_name: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]: ...

    def get_sprint_summary(self, sprint_name: str) -> Dict[str, Any]: ...


class UnifiedWorkTrackingAdapter:
    """
    Unified adapter that delegates to the appropriate backend.

    Automatically selects Azure DevOps or file-based adapter
    based on the work_tracking.platform configuration.
    """

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the unified adapter.

        Args:
            config_path: Path to config.yaml (default: .claude/config.yaml)
        """
        self.config_path = config_path or Path(".claude/config.yaml")
        self.config = self._load_config()
        # Don't default to file-based - let _create_adapter validate
        self.platform = self.config.get("work_tracking", {}).get("platform")
        self._adapter = self._create_adapter()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            return {"work_tracking": {"platform": "file-based"}}

        with open(self.config_path) as f:
            return yaml.safe_load(f) or {}

    def _create_adapter(self):
        """Create the appropriate backend adapter."""
        work_tracking = self.config.get("work_tracking", {})

        # Validate platform is explicitly configured
        if not self.platform:
            raise ValueError(
                "Work tracking platform not configured. "
                "Set 'work_tracking.platform' in .claude/config.yaml to 'azure-devops' or 'file-based'"
            )

        # Strict platform matching - NO silent fallback
        if self.platform == "azure-devops":
            return self._create_azure_adapter(work_tracking)
        elif self.platform == "file-based":
            return self._create_file_adapter(work_tracking)
        else:
            raise ValueError(
                f"Invalid work tracking platform: '{self.platform}'. "
                f"Valid options: 'azure-devops', 'file-based'. "
                f"Check 'work_tracking.platform' in .claude/config.yaml"
            )

    def _create_azure_adapter(self, work_tracking: Dict[str, Any]):
        """Create Azure DevOps adapter."""
        try:
            from skills.azure_devops.cli_wrapper import AzureCLI
            return AzureCLIAdapter(AzureCLI(), work_tracking)
        except ImportError:
            raise ImportError(
                "Azure DevOps adapter requires azure-cli. "
                "Install with: pip install trusted-ai-dev[azure]"
            )

    def _create_file_adapter(self, work_tracking: Dict[str, Any]):
        """Create file-based adapter."""
        from adapters.file_based import FileBasedAdapter

        work_items_dir = Path(
            work_tracking.get("work_items_directory", ".claude/work-items")
        )
        project_name = work_tracking.get("project", "default")

        return FileBasedAdapter(work_items_dir, project_name)

    # Delegate all methods to the underlying adapter

    def create_work_item(self, **kwargs) -> Dict[str, Any]:
        """Create a new work item."""
        return self._adapter.create_work_item(**kwargs)

    def update_work_item(self, work_item_id: int, **kwargs) -> Dict[str, Any]:
        """Update an existing work item."""
        return self._adapter.update_work_item(work_item_id, **kwargs)

    def get_work_item(self, work_item_id: int) -> Optional[Dict[str, Any]]:
        """Get a work item by ID."""
        return self._adapter.get_work_item(work_item_id)

    def query_work_items(self, **kwargs) -> List[Dict[str, Any]]:
        """Query work items with filters."""
        return self._adapter.query_work_items(**kwargs)

    def add_comment(self, work_item_id: int, comment: str, **kwargs) -> Dict[str, Any]:
        """Add a comment to a work item."""
        return self._adapter.add_comment(work_item_id, comment, **kwargs)

    def create_work_item_idempotent(self, **kwargs) -> Dict[str, Any]:
        """Create work item only if it doesn't exist."""
        return self._adapter.create_work_item_idempotent(**kwargs)

    def get_sprint_summary(self, sprint_name: str) -> Dict[str, Any]:
        """Get sprint summary statistics."""
        return self._adapter.get_sprint_summary(sprint_name)

    def link_work_items(self, source_id: int, target_id: int, relation_type: str = "related") -> Dict[str, Any]:
        """Link two work items."""
        return self._adapter.link_work_items(source_id, target_id, relation_type)

    def create_sprint(self, name: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """Create a new sprint."""
        return self._adapter.create_sprint(name, start_date, end_date)

    def list_sprints(self) -> List[Dict[str, Any]]:
        """List all sprints."""
        return self._adapter.list_sprints()

    def query_sprint_work_items(self, sprint_name: str) -> List[Dict[str, Any]]:
        """Get all work items in a sprint."""
        return self._adapter.query_sprint_work_items(sprint_name)

    @property
    def is_file_based(self) -> bool:
        """Check if using file-based adapter."""
        return self.platform == "file-based"

    @property
    def is_azure_devops(self) -> bool:
        """Check if using Azure DevOps adapter."""
        return self.platform == "azure-devops"


class AzureCLIAdapter:
    """
    Wrapper to make AzureCLI conform to the unified interface.

    Translates between the unified interface and Azure CLI specifics.
    """

    def __init__(self, azure_cli, work_tracking: Dict[str, Any]):
        self.cli = azure_cli
        self.work_tracking = work_tracking
        self.project = work_tracking.get("project", "")
        self.iteration_format = work_tracking.get("iteration_format", "{project}\\{sprint}")

    def create_work_item(
        self,
        work_item_type: str,
        title: str,
        description: str = "",
        assigned_to: Optional[str] = None,
        iteration: Optional[str] = None,
        fields: Optional[Dict[str, Any]] = None,
        parent_id: Optional[int] = None,
        verify: bool = False
    ) -> Dict[str, Any]:
        """Create work item via Azure CLI."""
        return self.cli.create_work_item(
            work_item_type=work_item_type,
            title=title,
            description=description,
            assigned_to=assigned_to,
            iteration=iteration,
            fields=fields,
            parent_id=parent_id,
            verify=verify
        )

    def update_work_item(
        self,
        work_item_id: int,
        state: Optional[str] = None,
        assigned_to: Optional[str] = None,
        fields: Optional[Dict[str, Any]] = None,
        verify: bool = False
    ) -> Dict[str, Any]:
        """Update work item via Azure CLI."""
        return self.cli.update_work_item(
            work_item_id=work_item_id,
            state=state,
            fields=fields,
            verify=verify
        )

    def get_work_item(self, work_item_id: int) -> Optional[Dict[str, Any]]:
        """Get work item via Azure CLI."""
        try:
            return self.cli.get_work_item(work_item_id)
        except Exception:
            return None

    def query_work_items(
        self,
        iteration: Optional[str] = None,
        state: Optional[str] = None,
        work_item_type: Optional[str] = None,
        assigned_to: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Query work items via WIQL."""
        conditions = [f"[System.TeamProject] = '{self.project}'"]

        if iteration:
            conditions.append(f"[System.IterationPath] = '{iteration}'")
        if state:
            conditions.append(f"[System.State] = '{state}'")
        if work_item_type:
            conditions.append(f"[System.WorkItemType] = '{work_item_type}'")
        if assigned_to:
            conditions.append(f"[System.AssignedTo] = '{assigned_to}'")

        wiql = f"SELECT [System.Id], [System.Title], [System.State] FROM WorkItems WHERE {' AND '.join(conditions)}"
        return self.cli.query_work_items(wiql)

    def add_comment(
        self,
        work_item_id: int,
        comment: str,
        author: Optional[str] = None
    ) -> Dict[str, Any]:
        """Add comment via Azure CLI."""
        return self.cli.add_work_item_comment(work_item_id, comment)

    def create_work_item_idempotent(
        self,
        title: str,
        work_item_type: str,
        description: str = "",
        sprint_name: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create work item idempotently."""
        return self.cli.create_work_item_idempotent(
            title=title,
            work_item_type=work_item_type,
            description=description,
            sprint_name=sprint_name,
            **kwargs
        )

    def get_sprint_summary(self, sprint_name: str) -> Dict[str, Any]:
        """Get sprint summary via Azure CLI queries."""
        iteration = self.iteration_format.format(project=self.project, sprint=sprint_name)
        work_items = self.query_work_items(iteration=iteration)

        summary = {
            "sprint": sprint_name,
            "total_items": len(work_items),
            "by_type": {},
            "by_state": {},
            "total_points": 0,
            "completed_points": 0
        }

        for item in work_items:
            fields = item.get("fields", {})
            item_type = fields.get("System.WorkItemType", "Unknown")
            state = fields.get("System.State", "Unknown")
            points = fields.get("Microsoft.VSTS.Scheduling.StoryPoints", 0) or 0

            summary["by_type"][item_type] = summary["by_type"].get(item_type, 0) + 1
            summary["by_state"][state] = summary["by_state"].get(state, 0) + 1
            summary["total_points"] += points

            if state in ["Done", "Closed", "Completed"]:
                summary["completed_points"] += points

        return summary

    def link_work_items(self, source_id: int, target_id: int, relation_type: str = "related") -> Dict[str, Any]:
        """Link work items via Azure CLI."""
        return self.cli.link_work_items(source_id, target_id, relation_type)

    def create_sprint(self, name: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """Create sprint via Azure CLI."""
        return self.cli.create_iteration(name, start_date, end_date)

    def list_sprints(self) -> List[Dict[str, Any]]:
        """List sprints via Azure CLI."""
        return self.cli.list_iterations()

    def query_sprint_work_items(self, sprint_name: str) -> List[Dict[str, Any]]:
        """Get sprint work items."""
        iteration = self.iteration_format.format(project=self.project, sprint=sprint_name)
        return self.query_work_items(iteration=iteration)


# Factory function for easy access
def get_adapter(config_path: Optional[Path] = None) -> UnifiedWorkTrackingAdapter:
    """
    Get a work tracking adapter based on configuration.

    Args:
        config_path: Optional path to config.yaml

    Returns:
        UnifiedWorkTrackingAdapter configured for the right platform

    Example:
        from work_tracking import get_adapter

        adapter = get_adapter()

        # Create a task
        task = adapter.create_work_item(
            work_item_type="Task",
            title="Implement feature X",
            description="Details...",
            iteration="Sprint 1"
        )

        # Query sprint items
        items = adapter.query_sprint_work_items("Sprint 1")

        # Get sprint stats
        summary = adapter.get_sprint_summary("Sprint 1")
    """
    return UnifiedWorkTrackingAdapter(config_path)


# Convenience alias
work_tracking = get_adapter
