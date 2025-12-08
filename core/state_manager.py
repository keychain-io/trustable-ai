"""
Workflow State Management System

Provides re-entrant, idempotent workflow execution with state tracking.
Prevents orphaned work items and duplicate work during workflow failures.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
import json
from datetime import datetime


class WorkflowState:
    """
    Manages workflow execution state for re-entrancy and idempotency.

    This class implements a checkpoint system that allows workflows to:
    - Resume from failure points
    - Track all created Azure work items
    - Avoid duplicate work
    - Sync with Azure DevOps as source of truth

    Example:
        ```python
        state = WorkflowState("sprint-planning", "sprint-10")

        if not state.is_step_completed("business-analyst"):
            state.start_step("business-analyst")
            # ... do work ...
            state.complete_step("business-analyst", result=backlog)

        state.complete_workflow()
        ```
    """

    def __init__(self, workflow_name: str, workflow_id: str):
        """
        Initialize workflow state.

        Args:
            workflow_name: Name of workflow (e.g., "sprint-planning")
            workflow_id: Unique ID for this run (e.g., "sprint-10")
        """
        self.workflow_name = workflow_name
        self.workflow_id = workflow_id
        self.state_dir = Path(".claude/workflow-state")
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = self.state_dir / f"{workflow_name}-{workflow_id}.json"
        self.state = self._load_state()

    def _load_state(self) -> Dict[str, Any]:
        """Load existing state or create new state structure."""
        if self.state_file.exists():
            return json.loads(self.state_file.read_text())

        return {
            "workflow_name": self.workflow_name,
            "workflow_id": self.workflow_id,
            "started_at": datetime.now().isoformat(),
            "status": "in_progress",
            "current_step": None,
            "completed_steps": [],
            "created_work_items": [],
            "errors": [],
            "metadata": {}
        }

    def save(self) -> None:
        """Persist state to disk."""
        self.state["updated_at"] = datetime.now().isoformat()
        self.state_file.write_text(json.dumps(self.state, indent=2), encoding='utf-8')

    def start_step(self, step_name: str, step_data: Optional[Dict] = None) -> None:
        """
        Mark step as started.

        Args:
            step_name: Name of the step
            step_data: Optional metadata about the step
        """
        self.state["current_step"] = {
            "name": step_name,
            "started_at": datetime.now().isoformat(),
            "data": step_data or {}
        }
        self.save()
        print(f"📍 Started step: {step_name}")

    def complete_step(self, step_name: str, result: Optional[Dict] = None) -> None:
        """
        Mark step as completed.

        Args:
            step_name: Name of the step
            result: Optional result data to store
        """
        self.state["completed_steps"].append({
            "name": step_name,
            "completed_at": datetime.now().isoformat(),
            "result": result or {}
        })
        self.state["current_step"] = None
        self.save()
        print(f"✅ Completed step: {step_name}")

    def is_step_completed(self, step_name: str) -> bool:
        """
        Check if step was already completed.

        Args:
            step_name: Name of the step to check

        Returns:
            True if step is in completed_steps list
        """
        return any(s["name"] == step_name for s in self.state["completed_steps"])

    def get_step_result(self, step_name: str) -> Optional[Dict]:
        """
        Get result data from a completed step.

        Args:
            step_name: Name of the step

        Returns:
            Result dict if step completed, None otherwise
        """
        for step in self.state["completed_steps"]:
            if step["name"] == step_name:
                return step.get("result")
        return None

    def record_work_item_created(
        self,
        work_item_id: int,
        work_item_data: Dict[str, Any]
    ) -> None:
        """
        Track created work items for rollback/cleanup.

        Args:
            work_item_id: Azure DevOps work item ID
            work_item_data: Metadata about the work item
        """
        self.state["created_work_items"].append({
            "id": work_item_id,
            "created_at": datetime.now().isoformat(),
            "data": work_item_data
        })
        self.save()
        print(f"📝 Tracked work item: WI-{work_item_id}")

    def record_error(self, error: str, context: Optional[Dict] = None) -> None:
        """
        Log errors for debugging.

        Args:
            error: Error message
            context: Optional context about where error occurred
        """
        self.state["errors"].append({
            "error": error,
            "timestamp": datetime.now().isoformat(),
            "context": context or {}
        })
        self.save()
        print(f"❌ Error recorded: {error}")

    def complete_workflow(self) -> None:
        """Mark workflow as successfully completed."""
        self.state["status"] = "completed"
        self.state["completed_at"] = datetime.now().isoformat()
        self.save()
        print(f"✅ Workflow completed: {self.workflow_name} ({self.workflow_id})")

    def fail_workflow(self, reason: str) -> None:
        """
        Mark workflow as failed.

        Args:
            reason: Reason for failure
        """
        self.state["status"] = "failed"
        self.state["failed_at"] = datetime.now().isoformat()
        self.state["failure_reason"] = reason
        self.save()
        print(f"❌ Workflow failed: {reason}")

    def get_created_work_items(self) -> List[int]:
        """
        Get list of work item IDs created in this workflow.

        Returns:
            List of work item IDs
        """
        return [wi["id"] for wi in self.state["created_work_items"]]

    def set_metadata(self, key: str, value: Any) -> None:
        """
        Store arbitrary metadata in workflow state.

        Args:
            key: Metadata key
            value: Metadata value (must be JSON-serializable)
        """
        self.state["metadata"][key] = value
        self.save()

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """
        Retrieve metadata from workflow state.

        Args:
            key: Metadata key
            default: Default value if key not found

        Returns:
            Metadata value or default
        """
        return self.state["metadata"].get(key, default)

    def print_summary(self) -> None:
        """Print a human-readable summary of workflow state."""
        print("\n" + "=" * 80)
        print(f"Workflow State: {self.workflow_name} ({self.workflow_id})")
        print("=" * 80)
        print(f"Status: {self.state['status']}")
        print(f"Started: {self.state['started_at']}")

        if "completed_at" in self.state:
            print(f"Completed: {self.state['completed_at']}")

        if "failed_at" in self.state:
            print(f"Failed: {self.state['failed_at']}")
            print(f"Reason: {self.state.get('failure_reason', 'Unknown')}")

        print(f"\nCompleted Steps: {len(self.state['completed_steps'])}")
        for step in self.state["completed_steps"]:
            print(f"  ✓ {step['name']} ({step['completed_at']})")

        if self.state["current_step"]:
            print(f"\nCurrent Step: {self.state['current_step']['name']}")
            print(f"  Started: {self.state['current_step']['started_at']}")

        print(f"\nWork Items Created: {len(self.state['created_work_items'])}")
        for wi in self.state['created_work_items']:
            title = wi['data'].get('title', 'Unknown')
            print(f"  • WI-{wi['id']}: {title}")

        if self.state["errors"]:
            print(f"\nErrors: {len(self.state['errors'])}")
            for error in self.state["errors"][-5:]:  # Show last 5
                print(f"  ✗ {error['error']} ({error['timestamp']})")

        print("=" * 80 + "\n")


def list_workflow_states(workflow_name: Optional[str] = None) -> List[Path]:
    """
    List all workflow state files.

    Args:
        workflow_name: Optional filter by workflow name

    Returns:
        List of state file paths
    """
    state_dir = Path(".claude/workflow-state")
    if not state_dir.exists():
        return []

    if workflow_name:
        pattern = f"{workflow_name}-*.json"
    else:
        pattern = "*.json"

    return sorted(state_dir.glob(pattern))


def load_workflow_state(workflow_name: str, workflow_id: str) -> Optional[WorkflowState]:
    """
    Load an existing workflow state.

    Args:
        workflow_name: Name of workflow
        workflow_id: Workflow ID

    Returns:
        WorkflowState instance if exists, None otherwise
    """
    state_file = Path(f".claude/workflow-state/{workflow_name}-{workflow_id}.json")
    if state_file.exists():
        return WorkflowState(workflow_name, workflow_id)
    return None


def list_incomplete_workflows() -> List[Dict[str, Any]]:
    """
    List all incomplete (in_progress or failed) workflow states with metadata.

    Returns:
        List of workflow info dictionaries, sorted by most recently updated
    """
    state_dir = Path(".claude/workflow-state")
    if not state_dir.exists():
        return []

    incomplete = []

    for state_file in state_dir.glob("*.json"):
        try:
            state = json.loads(state_file.read_text())

            # Only include incomplete workflows
            if state.get("status") in ["in_progress", "failed"]:
                started_at = datetime.fromisoformat(state["started_at"])
                updated_at = datetime.fromisoformat(state.get("updated_at", state["started_at"]))

                # Calculate age
                age = datetime.now() - updated_at
                if age.days > 0:
                    age_str = f"{age.days} day(s) ago"
                elif age.seconds > 3600:
                    age_str = f"{age.seconds // 3600} hour(s) ago"
                else:
                    age_str = f"{age.seconds // 60} minute(s) ago"

                # Get current/last step
                current_step = state.get("current_step", {}).get("name") if state.get("current_step") else None
                completed_steps = [s["name"] for s in state.get("completed_steps", [])]

                incomplete.append({
                    "file": state_file.name,
                    "file_path": str(state_file),
                    "workflow_name": state.get("workflow_name"),
                    "workflow_id": state.get("workflow_id"),
                    "status": state.get("status"),
                    "current_step": current_step,
                    "completed_steps": completed_steps,
                    "completed_step_count": len(completed_steps),
                    "age": age_str,
                    "started_at": started_at.strftime("%Y-%m-%d %H:%M"),
                    "updated_at": updated_at.strftime("%Y-%m-%d %H:%M"),
                    "work_items_created": len(state.get("created_work_items", [])),
                    "error_count": len(state.get("errors", [])),
                    "metadata": state.get("metadata", {}),
                    "failure_reason": state.get("failure_reason"),
                })
        except Exception as e:
            # Skip files that can't be parsed
            continue

    # Sort by most recently updated
    incomplete.sort(key=lambda x: x["updated_at"], reverse=True)

    return incomplete


def cleanup_old_states(days: int = 30) -> int:
    """
    Clean up workflow state files older than specified days.

    Args:
        days: Age threshold in days

    Returns:
        Number of files deleted
    """
    from datetime import timedelta

    state_dir = Path(".claude/workflow-state")
    if not state_dir.exists():
        return 0

    cutoff = datetime.now() - timedelta(days=days)
    deleted = 0

    for state_file in state_dir.glob("*.json"):
        try:
            state = json.loads(state_file.read_text())
            started = datetime.fromisoformat(state["started_at"])

            if started < cutoff and state["status"] == "completed":
                state_file.unlink()
                deleted += 1
                print(f"Deleted old state: {state_file.name}")
        except Exception as e:
            print(f"Error processing {state_file}: {e}")

    return deleted


if __name__ == "__main__":
    # Example usage
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "list":
            states = list_workflow_states()
            print(f"Found {len(states)} workflow state files:")
            for state_file in states:
                print(f"  • {state_file.name}")

        elif command == "cleanup":
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
            deleted = cleanup_old_states(days)
            print(f"Deleted {deleted} old state files")

        elif command == "show" and len(sys.argv) > 3:
            workflow_name = sys.argv[2]
            workflow_id = sys.argv[3]
            state = load_workflow_state(workflow_name, workflow_id)
            if state:
                state.print_summary()
            else:
                print(f"State not found: {workflow_name}-{workflow_id}")
    else:
        print("Usage:")
        print("  python state_manager.py list")
        print("  python state_manager.py cleanup [days]")
        print("  python state_manager.py show <workflow_name> <workflow_id>")
