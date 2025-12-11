"""
File-Based Work Tracking Adapter for TAID.

Provides a local file-based alternative to Azure DevOps
for teams that want to use the framework without external dependencies.

Work items are stored as YAML files in a configurable directory.
"""

from typing import Any, Dict, List, Optional
from pathlib import Path
from datetime import datetime
import yaml
import re


class FileBasedAdapter:
    """
    File-based work item adapter.

    Stores work items as YAML files, providing the same interface
    as the Azure DevOps adapter.

    Work items use type-prefixed IDs for human readability:
    - EPIC-001, EPIC-002, ...
    - FEATURE-001, FEATURE-002, ...
    - STORY-001, STORY-002, ...
    - TASK-001, TASK-002, ...
    - BUG-001, BUG-002, ...
    """

    # Map work item types to ID prefixes
    TYPE_PREFIXES = {
        "Epic": "EPIC",
        "Feature": "FEATURE",
        "User Story": "STORY",
        "Task": "TASK",
        "Bug": "BUG",
    }

    # Reverse mapping for prefix to type
    PREFIX_TO_TYPE = {v: k for k, v in TYPE_PREFIXES.items()}

    def __init__(
        self,
        work_items_dir: Optional[Path] = None,
        project_name: str = "default"
    ):
        """
        Initialize the file-based adapter.

        Args:
            work_items_dir: Directory to store work items (default: .claude/work-items)
            project_name: Project name for work item paths
        """
        self.work_items_dir = work_items_dir or Path(".claude/work-items")
        self.project_name = project_name
        self.platform = "file-based"  # Platform identifier for workflow detection
        self._ensure_directories()
        # Track next ID per type prefix
        self._next_ids = self._get_next_ids()

    def _ensure_directories(self) -> None:
        """Create necessary directories."""
        self.work_items_dir.mkdir(parents=True, exist_ok=True)
        (self.work_items_dir / "epics").mkdir(exist_ok=True)
        (self.work_items_dir / "features").mkdir(exist_ok=True)
        (self.work_items_dir / "tasks").mkdir(exist_ok=True)
        (self.work_items_dir / "bugs").mkdir(exist_ok=True)
        (self.work_items_dir / "sprints").mkdir(exist_ok=True)

    def _get_next_ids(self) -> Dict[str, int]:
        """Get the next available work item ID for each type prefix."""
        next_ids = {prefix: 1 for prefix in self.TYPE_PREFIXES.values()}

        for work_item_type in ["epics", "features", "tasks", "bugs"]:
            type_dir = self.work_items_dir / work_item_type
            for file in type_dir.glob("*.yaml"):
                try:
                    # Try new format: PREFIX-NNN
                    for prefix in self.TYPE_PREFIXES.values():
                        pattern = rf"{prefix}-(\d+)"
                        id_match = re.search(pattern, file.stem)
                        if id_match:
                            current_id = int(id_match.group(1))
                            next_ids[prefix] = max(next_ids[prefix], current_id + 1)
                            break
                    else:
                        # Try legacy format: WI-NNN (for backward compatibility)
                        id_match = re.search(r"WI-(\d+)", file.stem)
                        if id_match:
                            # Legacy items get converted based on directory
                            legacy_prefix_map = {
                                "epics": "EPIC",
                                "features": "FEATURE",
                                "tasks": "TASK",
                                "bugs": "BUG",
                            }
                            prefix = legacy_prefix_map.get(work_item_type, "TASK")
                            current_id = int(id_match.group(1))
                            next_ids[prefix] = max(next_ids[prefix], current_id + 1)
                except ValueError:
                    pass
        return next_ids

    def _get_next_id_for_type(self, work_item_type: str) -> str:
        """Get the next ID string for a work item type (e.g., 'EPIC-001')."""
        prefix = self.TYPE_PREFIXES.get(work_item_type, "TASK")
        next_num = self._next_ids.get(prefix, 1)
        self._next_ids[prefix] = next_num + 1
        return f"{prefix}-{next_num:03d}"

    def _parse_work_item_id(self, work_item_id: str) -> tuple:
        """Parse a work item ID into (prefix, number). Returns (None, None) if invalid."""
        if isinstance(work_item_id, int):
            # Legacy numeric ID - search all directories
            return None, work_item_id

        # Try new format: PREFIX-NNN
        for prefix in self.TYPE_PREFIXES.values():
            pattern = rf"^({prefix})-(\d+)$"
            match = re.match(pattern, str(work_item_id))
            if match:
                return match.group(1), int(match.group(2))

        # Try legacy format: WI-NNN
        match = re.match(r"^WI-(\d+)$", str(work_item_id))
        if match:
            return "WI", int(match.group(1))

        return None, None

    def _type_to_dir(self, work_item_type: str) -> str:
        """Map work item type to directory name."""
        type_map = {
            "Epic": "epics",
            "Feature": "features",
            "User Story": "features",
            "Task": "tasks",
            "Bug": "bugs",
        }
        return type_map.get(work_item_type, "tasks")

    def create_work_item(
        self,
        work_item_type: str,
        title: str,
        description: str = "",
        assigned_to: Optional[str] = None,
        iteration: Optional[str] = None,
        fields: Optional[Dict[str, Any]] = None,
        parent_id: Optional[str] = None,
        verify: bool = False
    ) -> Dict[str, Any]:
        """
        Create a new work item.

        Args:
            work_item_type: Type (Epic, Feature, User Story, Task, Bug)
            title: Work item title
            description: Description
            assigned_to: Assignee
            iteration: Sprint/iteration name
            fields: Additional fields (story points, priority, etc.)
            parent_id: Parent work item ID (e.g., 'EPIC-001')
            verify: Whether to return verification dict

        Returns:
            Work item dict or verification result
        """
        # Generate type-prefixed ID (e.g., EPIC-001, TASK-002)
        work_item_id = self._get_next_id_for_type(work_item_type)

        work_item = {
            "id": work_item_id,
            "type": work_item_type,
            "title": title,
            "description": description,
            "state": "New",
            "assigned_to": assigned_to,
            "iteration": iteration or f"{self.project_name}\\Backlog",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "parent_id": parent_id,
            "child_ids": [],
            "fields": fields or {}
        }

        # Extract common fields
        if fields:
            if "Microsoft.VSTS.Scheduling.StoryPoints" in fields:
                work_item["story_points"] = fields["Microsoft.VSTS.Scheduling.StoryPoints"]
            if "Microsoft.VSTS.Common.Priority" in fields:
                work_item["priority"] = fields["Microsoft.VSTS.Common.Priority"]

        # Save work item with type-prefixed filename
        type_dir = self._type_to_dir(work_item_type)
        file_path = self.work_items_dir / type_dir / f"{work_item_id}.yaml"

        with open(file_path, "w", encoding="utf-8") as f:
            yaml.dump(work_item, f, default_flow_style=False, sort_keys=False)

        # Update parent's child list
        if parent_id:
            self._add_child_to_parent(parent_id, work_item_id)

        if verify:
            return self._verify_operation(
                operation="create_work_item",
                success=True,
                result=work_item,
                verification_data={
                    "work_item_id": work_item_id,
                    "exists": True,
                    "title": title,
                    "type": work_item_type
                }
            )

        return work_item

    def update_work_item(
        self,
        work_item_id: str,
        state: Optional[str] = None,
        assigned_to: Optional[str] = None,
        fields: Optional[Dict[str, Any]] = None,
        verify: bool = False
    ) -> Dict[str, Any]:
        """
        Update an existing work item.

        Args:
            work_item_id: Work item ID (e.g., 'EPIC-001' or legacy 'WI-1')
            state: New state
            assigned_to: New assignee
            fields: Fields to update
            verify: Whether to return verification dict

        Returns:
            Updated work item dict or verification result
        """
        work_item, file_path = self._get_work_item_with_path(work_item_id)
        if not work_item or not file_path:
            raise ValueError(f"Work item {work_item_id} not found")

        if state:
            work_item["state"] = state
        if assigned_to:
            work_item["assigned_to"] = assigned_to
        if fields:
            work_item["fields"].update(fields)
            # Update iteration if in fields
            if "System.IterationPath" in fields:
                work_item["iteration"] = fields["System.IterationPath"]

        work_item["updated_at"] = datetime.now().isoformat()

        # Save updated work item to its existing path
        with open(file_path, "w", encoding="utf-8") as f:
            yaml.dump(work_item, f, default_flow_style=False, sort_keys=False)

        if verify:
            return self._verify_operation(
                operation="update_work_item",
                success=True,
                result=work_item,
                verification_data={
                    "work_item_id": work_item_id,
                    "exists": True,
                    "state": work_item.get("state")
                }
            )

        return work_item

    def _get_work_item_with_path(self, work_item_id: str) -> tuple:
        """
        Get a work item and its file path by ID.

        Supports both new format (EPIC-001) and legacy format (WI-1).

        Returns:
            Tuple of (work_item_dict, file_path) or (None, None) if not found
        """
        work_item_id_str = str(work_item_id)

        for work_item_type in ["epics", "features", "tasks", "bugs"]:
            type_dir = self.work_items_dir / work_item_type

            # Try new format: PREFIX-NNN.yaml
            file_path = type_dir / f"{work_item_id_str}.yaml"
            if file_path.exists():
                with open(file_path) as f:
                    return yaml.safe_load(f), file_path

            # Try legacy format: WI-N.yaml
            if isinstance(work_item_id, int) or work_item_id_str.isdigit():
                legacy_path = type_dir / f"WI-{work_item_id}.yaml"
                if legacy_path.exists():
                    with open(legacy_path) as f:
                        return yaml.safe_load(f), legacy_path

        return None, None

    def get_work_item(self, work_item_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a work item by ID.

        Args:
            work_item_id: Work item ID (e.g., 'EPIC-001', 'TASK-002', or legacy 'WI-1')

        Returns:
            Work item dict or None if not found
        """
        work_item, _ = self._get_work_item_with_path(work_item_id)
        return work_item

    def query_work_items(
        self,
        iteration: Optional[str] = None,
        state: Optional[str] = None,
        work_item_type: Optional[str] = None,
        assigned_to: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Query work items with filters.

        Args:
            iteration: Filter by iteration/sprint
            state: Filter by state
            work_item_type: Filter by type
            assigned_to: Filter by assignee

        Returns:
            List of matching work items
        """
        results = []

        search_dirs = (
            [self._type_to_dir(work_item_type)]
            if work_item_type
            else ["epics", "features", "tasks", "bugs"]
        )

        for type_dir in search_dirs:
            dir_path = self.work_items_dir / type_dir
            for file_path in dir_path.glob("*.yaml"):
                with open(file_path) as f:
                    work_item = yaml.safe_load(f)

                # Apply filters
                if iteration and work_item.get("iteration") != iteration:
                    continue
                if state and work_item.get("state") != state:
                    continue
                if assigned_to and work_item.get("assigned_to") != assigned_to:
                    continue

                results.append(work_item)

        # Sort by ID - handle both new format (EPIC-001) and legacy (numeric)
        def sort_key(x):
            item_id = x.get("id", "")
            if isinstance(item_id, int):
                return ("", item_id)
            # Parse string ID like "EPIC-001" -> ("EPIC", 1)
            match = re.match(r"([A-Z]+)-(\d+)", str(item_id))
            if match:
                return (match.group(1), int(match.group(2)))
            return (str(item_id), 0)

        return sorted(results, key=sort_key)

    def add_comment(
        self,
        work_item_id: str,
        comment: str,
        author: Optional[str] = None
    ) -> Dict[str, Any]:
        """Add a comment to a work item."""
        work_item, file_path = self._get_work_item_with_path(work_item_id)
        if not work_item or not file_path:
            raise ValueError(f"Work item {work_item_id} not found")

        comment_entry = {
            "text": comment,
            "author": author or "system",
            "created_at": datetime.now().isoformat()
        }

        work_item.setdefault("comments", []).append(comment_entry)
        work_item["updated_at"] = datetime.now().isoformat()

        # Save updated work item
        with open(file_path, "w", encoding="utf-8") as f:
            yaml.dump(work_item, f, default_flow_style=False, sort_keys=False)

        return comment_entry

    def link_work_items(
        self,
        source_id: str,
        target_id: str,
        relation_type: str = "related"
    ) -> Dict[str, Any]:
        """Link two work items."""
        source, source_path = self._get_work_item_with_path(source_id)
        target = self.get_work_item(target_id)

        if not source or not target or not source_path:
            raise ValueError("One or both work items not found")

        link = {
            "target_id": target_id,
            "relation_type": relation_type,
            "created_at": datetime.now().isoformat()
        }

        source.setdefault("links", []).append(link)

        # Save updated source
        with open(source_path, "w", encoding="utf-8") as f:
            yaml.dump(source, f, default_flow_style=False, sort_keys=False)

        return link

    def _add_child_to_parent(self, parent_id: str, child_id: str) -> None:
        """Add a child reference to a parent work item."""
        parent, file_path = self._get_work_item_with_path(parent_id)
        if parent and file_path:
            parent.setdefault("child_ids", []).append(child_id)

            with open(file_path, "w", encoding="utf-8") as f:
                yaml.dump(parent, f, default_flow_style=False, sort_keys=False)

    # Sprint Management

    def create_sprint(
        self,
        name: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new sprint/iteration.

        Args:
            name: Sprint name (e.g., "Sprint 1")
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            Sprint dict
        """
        sprint = {
            "name": name,
            "path": f"{self.project_name}\\{name}",
            "start_date": start_date,
            "end_date": end_date,
            "created_at": datetime.now().isoformat()
        }

        file_path = self.work_items_dir / "sprints" / f"{name.replace(' ', '-')}.yaml"

        with open(file_path, "w", encoding="utf-8") as f:
            yaml.dump(sprint, f, default_flow_style=False)

        return sprint

    def list_sprints(self) -> List[Dict[str, Any]]:
        """List all sprints."""
        sprints = []
        sprints_dir = self.work_items_dir / "sprints"

        for file_path in sprints_dir.glob("*.yaml"):
            with open(file_path) as f:
                sprints.append(yaml.safe_load(f))

        return sorted(sprints, key=lambda x: x.get("start_date") or "")

    def query_sprint_work_items(
        self,
        sprint_name: str
    ) -> List[Dict[str, Any]]:
        """Get all work items in a sprint."""
        iteration = f"{self.project_name}\\{sprint_name}"
        return self.query_work_items(iteration=iteration)

    def create_sprint_work_items_batch(
        self,
        sprint_name: str,
        work_items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Create multiple work items for a sprint.

        Args:
            sprint_name: Sprint name
            work_items: List of work item dicts with type, title, description, fields

        Returns:
            List of created work items
        """
        iteration = f"{self.project_name}\\{sprint_name}"
        results = []

        for item in work_items:
            result = self.create_work_item(
                work_item_type=item["type"],
                title=item["title"],
                description=item.get("description", ""),
                iteration=iteration,
                fields=item.get("fields"),
                parent_id=item.get("parent_id")
            )
            results.append(result)

        return results

    # Verification helpers

    def _verify_operation(
        self,
        operation: str,
        success: bool,
        result: Any,
        verification_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Return standardized verification result."""
        return {
            "success": success,
            "operation": operation,
            "result": result,
            "verification": verification_data
        }

    def create_work_item_idempotent(
        self,
        title: str,
        work_item_type: str,
        description: str = "",
        sprint_name: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create work item only if it doesn't already exist.

        Args:
            title: Work item title
            work_item_type: Type
            description: Description
            sprint_name: Sprint name

        Returns:
            Dict with id, created, existing, work_item
        """
        # Search for existing
        iteration = f"{self.project_name}\\{sprint_name}" if sprint_name else None
        existing = self.query_work_items(
            iteration=iteration,
            work_item_type=work_item_type
        )

        for work_item in existing:
            if work_item.get("title") == title:
                return {
                    "id": work_item["id"],
                    "created": False,
                    "existing": True,
                    "work_item": work_item
                }

        # Create new
        work_item = self.create_work_item(
            work_item_type=work_item_type,
            title=title,
            description=description,
            iteration=iteration,
            **kwargs
        )

        return {
            "id": work_item["id"],
            "created": True,
            "existing": False,
            "work_item": work_item
        }

    # Reporting

    def get_sprint_summary(self, sprint_name: str) -> Dict[str, Any]:
        """
        Get summary statistics for a sprint.

        Returns:
            Dict with counts, points, and status breakdown
        """
        work_items = self.query_sprint_work_items(sprint_name)

        summary = {
            "sprint": sprint_name,
            "total_items": len(work_items),
            "by_type": {},
            "by_state": {},
            "total_points": 0,
            "completed_points": 0
        }

        for item in work_items:
            # By type
            item_type = item.get("type", "Unknown")
            summary["by_type"][item_type] = summary["by_type"].get(item_type, 0) + 1

            # By state
            state = item.get("state", "Unknown")
            summary["by_state"][state] = summary["by_state"].get(state, 0) + 1

            # Points
            points = item.get("story_points") or item.get("fields", {}).get(
                "Microsoft.VSTS.Scheduling.StoryPoints", 0
            )
            summary["total_points"] += points

            if state in ["Done", "Closed", "Completed"]:
                summary["completed_points"] += points

        return summary


# Factory function
def get_adapter(
    work_items_dir: Optional[Path] = None,
    project_name: str = "default"
) -> FileBasedAdapter:
    """Get a file-based adapter instance."""
    return FileBasedAdapter(work_items_dir, project_name)
