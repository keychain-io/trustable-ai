"""
Workflow Management Skill for TAID.

Re-exports state management and profiling capabilities from core.
"""

from typing import Any, Dict, List, Optional
from pathlib import Path

from ..base import BaseSkill


class WorkflowSkill(BaseSkill):
    """
    Workflow management skill.

    Provides state management, checkpointing, and profiling for workflows.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._state_manager = None
        self._profiler = None

    @property
    def name(self) -> str:
        return "workflow"

    @property
    def description(self) -> str:
        return "Workflow state management, checkpointing, and profiling"

    @property
    def version(self) -> str:
        return "1.0.0"

    def initialize(self) -> bool:
        """Initialize state manager and profiler."""
        try:
            # Import the actual classes and functions that exist
            from core import WorkflowState, WorkflowProfiler

            # Store the classes for later use
            self._state_class = WorkflowState
            self._profiler_class = WorkflowProfiler
            self._initialized = True
            return True
        except ImportError as e:
            self._last_error = f"Core modules not available: {e}"
            return False

    def verify_prerequisites(self) -> Dict[str, Any]:
        """Check if core modules are available."""
        missing = []
        warnings = []

        try:
            from core import WorkflowState
        except ImportError:
            missing.append("core.WorkflowState class")

        try:
            from core import WorkflowProfiler
        except ImportError:
            missing.append("core.WorkflowProfiler class")

        state_dir = Path(self.config.get('state_dir', '.claude/workflow-state'))
        if not state_dir.exists():
            warnings.append(f"State directory does not exist: {state_dir}")

        return {
            "satisfied": len(missing) == 0,
            "missing": missing,
            "warnings": warnings
        }

    # State Management

    def start_workflow(
        self,
        workflow_name: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Start a new workflow execution.

        Args:
            workflow_name: Name of the workflow
            context: Initial context data

        Returns:
            Workflow execution ID
        """
        if not self._state_manager:
            raise RuntimeError("Skill not initialized")
        return self._state_manager.start_workflow(workflow_name, context or {})

    def checkpoint(
        self,
        execution_id: str,
        step_name: str,
        data: Dict[str, Any]
    ) -> None:
        """
        Save a checkpoint in the workflow.

        Args:
            execution_id: Workflow execution ID
            step_name: Name of the step being checkpointed
            data: Data to save at this checkpoint
        """
        if not self._state_manager:
            raise RuntimeError("Skill not initialized")
        self._state_manager.checkpoint(execution_id, step_name, data)

    def get_state(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get current workflow state."""
        if not self._state_manager:
            raise RuntimeError("Skill not initialized")
        return self._state_manager.get_state(execution_id)

    def resume_workflow(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """
        Resume a workflow from its last checkpoint.

        Returns:
            Last checkpoint data or None if not found
        """
        if not self._state_manager:
            raise RuntimeError("Skill not initialized")
        return self._state_manager.resume(execution_id)

    def complete_workflow(self, execution_id: str, result: Dict[str, Any]) -> None:
        """Mark workflow as completed."""
        if not self._state_manager:
            raise RuntimeError("Skill not initialized")
        self._state_manager.complete(execution_id, result)

    def fail_workflow(self, execution_id: str, error: str) -> None:
        """Mark workflow as failed."""
        if not self._state_manager:
            raise RuntimeError("Skill not initialized")
        self._state_manager.fail(execution_id, error)

    def list_active_workflows(self) -> List[Dict[str, Any]]:
        """List all active (non-completed) workflows."""
        if not self._state_manager:
            raise RuntimeError("Skill not initialized")
        return self._state_manager.list_active()

    # Profiling

    def start_profiling(self, workflow_name: str) -> str:
        """
        Start profiling a workflow execution.

        Returns:
            Profile ID
        """
        if not self._profiler:
            raise RuntimeError("Skill not initialized")
        return self._profiler.start(workflow_name)

    def record_step(
        self,
        profile_id: str,
        step_name: str,
        duration_ms: float,
        tokens_used: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record metrics for a workflow step."""
        if not self._profiler:
            raise RuntimeError("Skill not initialized")
        self._profiler.record_step(
            profile_id,
            step_name,
            duration_ms,
            tokens_used,
            metadata or {}
        )

    def stop_profiling(self, profile_id: str) -> Dict[str, Any]:
        """
        Stop profiling and get report.

        Returns:
            Profiling report with timing and token usage
        """
        if not self._profiler:
            raise RuntimeError("Skill not initialized")
        return self._profiler.stop(profile_id)

    def get_profile_report(self, profile_id: str) -> Optional[Dict[str, Any]]:
        """Get a previously saved profile report."""
        if not self._profiler:
            raise RuntimeError("Skill not initialized")
        return self._profiler.get_report(profile_id)


# Factory function
def get_skill(config: Optional[Dict[str, Any]] = None) -> WorkflowSkill:
    """Get an instance of the workflow skill."""
    return WorkflowSkill(config)


Skill = WorkflowSkill
