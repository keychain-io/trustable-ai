"""
Azure DevOps Skill for TAID.

Provides battle-tested Azure DevOps operations via CLI wrapper.
"""

from typing import Any, Dict, List, Optional

from ..base import VerifiableSkill
from .cli_wrapper import AzureCLI


class AzureDevOpsSkill(VerifiableSkill):
    """
    Azure DevOps integration skill.

    Provides work item operations, sprint management, PR creation,
    and pipeline triggers with verification support.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._cli: Optional[AzureCLI] = None

    @property
    def name(self) -> str:
        return "azure_devops"

    @property
    def description(self) -> str:
        return "Azure DevOps operations with verification patterns"

    @property
    def version(self) -> str:
        return "1.0.0"

    def initialize(self) -> bool:
        """Initialize Azure CLI connection."""
        try:
            self._cli = AzureCLI()
            self._initialized = True
            return True
        except Exception as e:
            self._last_error = str(e)
            return False

    def verify_prerequisites(self) -> Dict[str, Any]:
        """Check if Azure CLI is configured."""
        import subprocess

        missing = []
        warnings = []

        # Check az command exists
        try:
            result = subprocess.run(
                ['az', '--version'],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                missing.append("Azure CLI not installed")
        except FileNotFoundError:
            missing.append("Azure CLI not installed")

        # Check devops extension
        try:
            result = subprocess.run(
                ['az', 'devops', '--help'],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                missing.append("Azure DevOps extension not installed (run: az extension add --name azure-devops)")
        except Exception:
            missing.append("Azure DevOps extension not installed")

        # Check login status
        try:
            result = subprocess.run(
                ['az', 'account', 'show'],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                warnings.append("Not logged in to Azure (run: az login)")
        except Exception:
            warnings.append("Could not check Azure login status")

        return {
            "satisfied": len(missing) == 0,
            "missing": missing,
            "warnings": warnings
        }

    @property
    def cli(self) -> AzureCLI:
        """Get the CLI wrapper instance."""
        if not self._cli:
            raise RuntimeError("Skill not initialized. Call initialize() first.")
        return self._cli

    # Work Item Operations

    def create_work_item(
        self,
        work_item_type: str,
        title: str,
        description: str = "",
        assigned_to: Optional[str] = None,
        area: Optional[str] = None,
        iteration: Optional[str] = None,
        fields: Optional[Dict[str, Any]] = None,
        parent_id: Optional[int] = None,
        verify: bool = True
    ) -> Dict[str, Any]:
        """
        Create a work item with optional verification.

        Uses two-step creation for reliability (create then assign iteration).

        Args:
            work_item_type: Type (Task, Bug, Feature, etc.)
            title: Work item title
            description: Description
            assigned_to: User to assign the work item to
            area: Area path
            iteration: Iteration path (e.g., "Project\\Sprint 1")
            fields: Additional fields
            parent_id: ID of parent work item to link to
            verify: Whether to verify creation

        Returns:
            Work item dict or verification result
        """
        return self.cli.create_work_item(
            work_item_type=work_item_type,
            title=title,
            description=description,
            assigned_to=assigned_to,
            area=area,
            iteration=iteration,
            fields=fields,
            parent_id=parent_id,
            verify=verify
        )

    def update_work_item(
        self,
        work_item_id: int,
        state: Optional[str] = None,
        fields: Optional[Dict[str, Any]] = None,
        verify: bool = True
    ) -> Dict[str, Any]:
        """Update a work item with optional verification."""
        return self.cli.update_work_item(
            work_item_id=work_item_id,
            state=state,
            fields=fields,
            verify=verify
        )

    def get_work_item(self, work_item_id: int) -> Dict[str, Any]:
        """Get work item by ID."""
        return self.cli.get_work_item(work_item_id)

    def query_work_items(self, wiql: str) -> List[Dict]:
        """Query work items using WIQL."""
        return self.cli.query_work_items(wiql)

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

        Prevents duplicate work items during re-runs.
        """
        return self.cli.create_work_item_idempotent(
            title=title,
            work_item_type=work_item_type,
            description=description,
            sprint_name=sprint_name,
            **kwargs
        )

    # Sprint Operations

    def create_sprint(
        self,
        name: str,
        start_date: Optional[str] = None,
        finish_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new sprint/iteration."""
        return self.cli.create_iteration(name, start_date, finish_date)

    def list_sprints(self) -> List[Dict]:
        """List all sprints/iterations."""
        return self.cli.list_iterations()

    def query_sprint_work_items(
        self,
        sprint_name: str,
        project_name: Optional[str] = None
    ) -> List[Dict]:
        """Query all work items in a sprint."""
        return self.cli.query_sprint_work_items(sprint_name, project_name)

    def create_sprint_work_items_batch(
        self,
        sprint_name: str,
        work_items: List[Dict[str, Any]]
    ) -> List[Dict]:
        """Create multiple work items for a sprint efficiently."""
        return self.cli.create_sprint_work_items_batch(sprint_name, work_items)

    # PR Operations

    def create_pull_request(
        self,
        source_branch: str,
        title: str,
        description: str,
        work_item_ids: Optional[List[int]] = None,
        reviewers: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a pull request linked to work items."""
        return self.cli.create_pull_request(
            source_branch=source_branch,
            title=title,
            description=description,
            work_item_ids=work_item_ids,
            reviewers=reviewers
        )

    # Pipeline Operations

    def trigger_pipeline(
        self,
        pipeline_id: int,
        branch: str,
        variables: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Trigger a pipeline run."""
        return self.cli.trigger_pipeline(pipeline_id, branch, variables)

    def get_pipeline_run(self, run_id: int) -> Dict[str, Any]:
        """Get pipeline run status."""
        return self.cli.get_pipeline_run(run_id)


# Factory function for registry
def get_skill(config: Optional[Dict[str, Any]] = None) -> AzureDevOpsSkill:
    """Get an instance of the Azure DevOps skill."""
    return AzureDevOpsSkill(config)


# Convenience exports
Skill = AzureDevOpsSkill
