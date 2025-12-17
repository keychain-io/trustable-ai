"""
Azure DevOps REST API Wrapper for TAID.

Uses Azure DevOps REST API for work item operations with automatic markdown formatting support.

Key Features:
1. Markdown format support: Automatically sets multilineFieldsFormat for description fields
2. Single-step work item creation: Sets all fields including iteration in one API call
3. Batch operations: Query work items efficiently with batch fetching
4. Field mapping: Generic field names to Azure DevOps-specific fields

Key Learnings Applied:
1. Iteration paths use simplified format: "Project\\SprintName"
2. Single-step creation with REST API (no longer two-step)
3. Field names are case-sensitive
4. WIQL queries need double backslashes for escaping
5. Markdown fields require multilineFieldsFormat=Markdown parameter

REST API Operations:
- create_work_item: POST with JSON Patch, supports markdown
- update_work_item: PATCH with JSON Patch, supports markdown
- query_work_items: POST WIQL + batch GET for full items
- link_work_items: PATCH with relation additions
- get_work_item: GET with full expansion
"""

import json
import base64
import os
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import config loader for pure Python config loading
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config.loader import load_config

# Optional requests import for file attachments
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class AuthenticationError(Exception):
    """Raised when Azure DevOps authentication fails."""
    pass


class AzureCLI:
    """Wrapper for Azure CLI DevOps operations."""

    def __init__(self):
        self._config = self._load_configuration()
        self._cached_token: Optional[str] = None

    def _load_configuration(self) -> Dict[str, str]:
        """
        Load Azure DevOps configuration from .claude/config.yaml or environment variables.

        Configuration sources (in order of precedence):
        1. .claude/config.yaml (work_tracking.organization and work_tracking.project)
        2. Environment variables (AZURE_DEVOPS_ORG and AZURE_DEVOPS_PROJECT)

        Returns:
            Dict with 'organization' and 'project' keys

        Raises:
            Exception: If configuration is missing or invalid
        """
        config = {}

        # Try loading from .claude/config.yaml
        try:
            framework_config = load_config()

            # Extract work tracking configuration
            if framework_config.work_tracking.organization:
                config['organization'] = framework_config.work_tracking.organization
            if framework_config.work_tracking.project:
                config['project'] = framework_config.work_tracking.project

        except FileNotFoundError:
            # Config file doesn't exist, will fall back to environment variables
            pass
        except Exception as e:
            # Config file exists but has errors - log warning but continue
            print(f"Warning: Could not load configuration from .claude/config.yaml: {e}")

        # Fall back to environment variables if not in config
        if 'organization' not in config:
            org = os.environ.get('AZURE_DEVOPS_ORG', '').strip()
            if org:
                config['organization'] = org

        if 'project' not in config:
            project = os.environ.get('AZURE_DEVOPS_PROJECT', '').strip()
            if project:
                config['project'] = project

        # Validate configuration
        if 'organization' not in config or not config['organization']:
            raise Exception(
                "Azure DevOps organization not configured. "
                "Set in .claude/config.yaml (work_tracking.organization) "
                "or environment variable AZURE_DEVOPS_ORG"
            )

        if 'project' not in config or not config['project']:
            raise Exception(
                "Azure DevOps project not configured. "
                "Set in .claude/config.yaml (work_tracking.project) "
                "or environment variable AZURE_DEVOPS_PROJECT"
            )

        # Validate organization URL format
        org_url = config['organization']
        if not org_url.startswith('https://dev.azure.com/'):
            raise Exception(
                f"Invalid Azure DevOps organization URL: {org_url}. "
                f"Must start with 'https://dev.azure.com/'. "
                f"Update in .claude/config.yaml or AZURE_DEVOPS_ORG environment variable."
            )

        # Normalize organization URL (remove trailing slash)
        config['organization'] = org_url.rstrip('/')

        return config

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

    # Work Items

    def query_work_items(self, wiql: str) -> List[Dict]:
        """
        Query work items using WIQL via REST API.

        Args:
            wiql: WIQL query string

        Returns:
            List of full work item dicts (not just IDs)

        Note:
            REST API query returns only IDs; this method automatically
            fetches full work items in batches for compatibility.
        """
        project = self._get_project()

        # POST WIQL query
        endpoint = f"{project}/_apis/wit/wiql"
        params = {"api-version": "7.1"}
        data = {"query": wiql}

        result = self._make_request("POST", endpoint, data=data, params=params)

        # Extract work item IDs
        work_item_ids = [item["id"] for item in result.get("workItems", [])]

        if not work_item_ids:
            return []

        # Batch fetch full work items (up to 200 at a time per API limits)
        all_items = []
        batch_size = 200

        for i in range(0, len(work_item_ids), batch_size):
            batch_ids = work_item_ids[i:i+batch_size]
            ids_param = ",".join(str(id) for id in batch_ids)

            endpoint = "_apis/wit/workitems"
            params = {
                "api-version": "7.1",
                "ids": ids_param,
                "$expand": "All"
            }

            batch_result = self._make_request("GET", endpoint, params=params)
            all_items.extend(batch_result.get("value", []))

        return all_items

    def get_work_item(self, work_item_id: int) -> Dict:
        """
        Get work item by ID using REST API.

        Args:
            work_item_id: ID of work item to retrieve

        Returns:
            Work item dict with fields, relations, etc.
        """
        endpoint = f"_apis/wit/workitems/{work_item_id}"
        params = {
            "api-version": "7.1",
            "$expand": "All"
        }

        return self._make_request("GET", endpoint, params=params)

    def verify_work_item_created(
        self,
        work_item_id: int,
        expected_title: Optional[str] = None
    ) -> Dict[str, Any]:
        """Verify a work item was successfully created."""
        try:
            work_item = self.get_work_item(work_item_id)

            verification_data = {
                "work_item_id": work_item_id,
                "exists": True,
                "title": work_item.get("fields", {}).get("System.Title"),
                "state": work_item.get("fields", {}).get("System.State"),
                "type": work_item.get("fields", {}).get("System.WorkItemType"),
            }

            title_matches = True
            if expected_title:
                title_matches = verification_data["title"] == expected_title
                verification_data["title_matches"] = title_matches

            success = verification_data["exists"] and title_matches

            return self._verify_operation(
                operation="verify_work_item_created",
                success=success,
                result=work_item,
                verification_data=verification_data
            )
        except Exception as e:
            return self._verify_operation(
                operation="verify_work_item_created",
                success=False,
                result=None,
                verification_data={
                    "work_item_id": work_item_id,
                    "exists": False,
                    "error": str(e)
                }
            )

    def verify_work_item_updated(
        self,
        work_item_id: int,
        expected_fields: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Verify a work item was successfully updated with expected field values."""
        try:
            work_item = self.get_work_item(work_item_id)
            fields = work_item.get("fields", {})

            verification_data = {
                "work_item_id": work_item_id,
                "exists": True,
                "fields_verified": {},
                "all_fields_match": True
            }

            for field_name, expected_value in expected_fields.items():
                actual_value = fields.get(field_name)
                matches = actual_value == expected_value

                verification_data["fields_verified"][field_name] = {
                    "expected": expected_value,
                    "actual": actual_value,
                    "matches": matches
                }

                if not matches:
                    verification_data["all_fields_match"] = False

            success = verification_data["exists"] and verification_data["all_fields_match"]

            return self._verify_operation(
                operation="verify_work_item_updated",
                success=success,
                result=work_item,
                verification_data=verification_data
            )
        except Exception as e:
            return self._verify_operation(
                operation="verify_work_item_updated",
                success=False,
                result=None,
                verification_data={
                    "work_item_id": work_item_id,
                    "exists": False,
                    "error": str(e)
                }
            )

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
        verify: bool = False
    ) -> Dict:
        """
        Create a work item using REST API with markdown support.

        Single-step creation that sets all fields including iteration in one API call.
        Automatically sets multilineFieldsFormat=Markdown for description fields.

        Iteration path format: "ProjectName\\SprintName" (simplified, no \\Iteration\\)
        Example: "My Project\\Sprint 4"

        Args:
            work_item_type: Type of work item (Task, Bug, User Story, etc.)
            title: Work item title
            description: Work item description (supports markdown)
            assigned_to: User to assign the work item to
            area: Area path
            iteration: Iteration path (set in single call, not two-step)
            fields: Additional fields to set
            parent_id: ID of parent work item (will create Parent link)
            verify: Whether to verify the work item was created correctly
        """
        project = self._get_project()

        # Build field updates
        all_fields = {"System.Title": title}

        if description:
            all_fields["System.Description"] = description
        if assigned_to:
            all_fields["System.AssignedTo"] = assigned_to
        if area:
            all_fields["System.AreaPath"] = area
        if iteration:
            all_fields["System.IterationPath"] = iteration  # Single-step!
        if fields:
            all_fields.update(fields)

        # Build JSON Patch
        patch = self._build_json_patch(all_fields)

        # Add markdown format operations for eligible fields
        markdown_fields = [
            "System.Description",
            "Microsoft.VSTS.Common.AcceptanceCriteria",
            "Microsoft.VSTS.TCM.ReproSteps"
        ]
        for field in markdown_fields:
            if field in all_fields:
                patch.append({
                    "op": "add",
                    "path": f"/multilineFieldsFormat/{field}",
                    "value": "Markdown"
                })

        # Add parent link if specified
        if parent_id:
            base_url = self._get_base_url()
            patch.append({
                "op": "add",
                "path": "/relations/-",
                "value": {
                    "rel": "System.LinkTypes.Hierarchy-Reverse",
                    "url": f"{base_url}/_apis/wit/workitems/{parent_id}"
                }
            })

        # API version parameter
        params = {"api-version": "7.1"}

        # Create via REST API
        endpoint = f"{project}/_apis/wit/workitems/${work_item_type}"
        result = self._make_request("POST", endpoint, data=patch, params=params)

        # Verification if requested
        if verify:
            work_item_id = result.get('id')
            if work_item_id:
                expected_fields = {}
                if iteration:
                    expected_fields["System.IterationPath"] = iteration

                verification = self.verify_work_item_created(work_item_id, expected_title=title)

                if iteration and verification["success"]:
                    iter_verification = self.verify_work_item_updated(work_item_id, expected_fields)
                    verification["verification"]["iteration_verified"] = iter_verification["verification"]
                    verification["success"] = verification["success"] and iter_verification["success"]

                return verification
            else:
                return self._verify_operation(
                    operation="create_work_item",
                    success=False,
                    result=result,
                    verification_data={"error": "No work item ID in result"}
                )

        return result

    def update_work_item(
        self,
        work_item_id: int,
        state: Optional[str] = None,
        assigned_to: Optional[str] = None,
        fields: Optional[Dict[str, Any]] = None,
        verify: bool = False
    ) -> Dict:
        """
        Update a work item using REST API with markdown support.

        Args:
            work_item_id: ID of work item to update
            state: New state (e.g., "Done", "In Progress")
            assigned_to: User to assign to
            fields: Additional fields to update
            verify: Whether to verify the update

        Returns:
            Updated work item dict
        """
        project = self._get_project()

        # Build field updates
        all_fields = {}

        if state:
            all_fields["System.State"] = state
        if assigned_to:
            all_fields["System.AssignedTo"] = assigned_to
        if fields:
            all_fields.update(fields)

        if not all_fields:
            raise ValueError("No fields specified for update")

        # Build JSON Patch
        patch = self._build_json_patch(all_fields)

        # Add markdown format operations for eligible fields
        markdown_fields = [
            "System.Description",
            "Microsoft.VSTS.Common.AcceptanceCriteria",
            "Microsoft.VSTS.TCM.ReproSteps"
        ]
        for field in markdown_fields:
            if field in all_fields:
                patch.append({
                    "op": "add",
                    "path": f"/multilineFieldsFormat/{field}",
                    "value": "Markdown"
                })

        # API version parameter
        params = {"api-version": "7.1"}

        # Update via REST API
        endpoint = f"{project}/_apis/wit/workitems/{work_item_id}"
        result = self._make_request("PATCH", endpoint, data=patch, params=params)

        # Verification if requested
        if verify:
            expected_fields = {}
            if state:
                expected_fields["System.State"] = state
            if fields:
                expected_fields.update(fields)

            if expected_fields:
                return self.verify_work_item_updated(work_item_id, expected_fields)
            else:
                return self.verify_work_item_created(work_item_id)

        return result

    def add_comment(self, work_item_id: int, comment: str) -> Dict:
        """
        Add comment to work item using REST API.

        Supports both plain text and markdown formatting. Markdown formatting
        is preserved in the comment text.

        Args:
            work_item_id: ID of work item to add comment to
            comment: Comment text (supports markdown formatting)

        Returns:
            Dict containing comment details:
            - id: Comment ID
            - workItemId: Work item ID
            - text: Comment text
            - createdDate: Creation timestamp
            - createdBy: User who created the comment

        Raises:
            Exception: If work item not found (404), authentication fails (401),
                      or other API errors occur

        Example:
            >>> cli.add_comment(1234, "This is a **markdown** comment")
            {'id': 5678, 'workItemId': 1234, 'text': 'This is a **markdown** comment', ...}
        """
        project = self._get_project()

        # Build REST API endpoint for comments
        endpoint = f"{project}/_apis/wit/workitems/{work_item_id}/comments"
        params = {"api-version": "7.1-preview"}

        # Comment body - text field supports markdown
        data = {"text": comment}

        try:
            return self._make_comment_request("POST", endpoint, data=data, params=params)
        except Exception as e:
            error_msg = str(e)
            # Provide clearer error messages for common failures
            if "404" in error_msg:
                raise Exception(
                    f"Work item {work_item_id} not found. "
                    f"Verify the work item ID exists in Azure DevOps."
                ) from e
            elif "401" in error_msg or "403" in error_msg:
                raise AuthenticationError(
                    f"Authentication failed when adding comment to work item {work_item_id}. "
                    f"Verify your Azure DevOps PAT token is valid and has Work Items (Read & Write) scope."
                ) from e
            else:
                raise Exception(
                    f"Failed to add comment to work item {work_item_id}: {error_msg}"
                ) from e

    def _make_comment_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Make authenticated REST API request for work item comments.

        This is a specialized version of _make_request() for the Comments API,
        which uses application/json Content-Type (not JSON Patch).

        Args:
            method: HTTP method (GET, POST)
            endpoint: API endpoint (e.g., "Project/_apis/wit/workitems/1234/comments")
            data: Request body as dict
            params: Query parameters (e.g., {"api-version": "7.1"})

        Returns:
            Response JSON as dict

        Raises:
            ImportError: If requests library not available
            Exception: If request fails with status code and error details
        """
        if not HAS_REQUESTS:
            raise ImportError("requests library required for REST API operations. Install with: pip install requests")

        url = f"{self._get_base_url()}/{endpoint}"
        token = self._get_auth_token()
        auth = base64.b64encode(f":{token}".encode()).decode()

        # Comments API uses standard application/json (not JSON Patch)
        headers = {
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/json"
        }

        response = requests.request(
            method=method,
            url=url,
            json=data,
            params=params,
            headers=headers
        )

        if response.status_code not in [200, 201]:
            raise Exception(
                f"Azure DevOps REST API request failed:\n"
                f"  Method: {method}\n"
                f"  URL: {url}\n"
                f"  Status: {response.status_code}\n"
                f"  Error: {response.text}"
            )

        return response.json() if response.text else {}

    def link_work_items(self, source_id: int, target_id: int, relation_type: str) -> Dict:
        """
        Link two work items using REST API.

        Args:
            source_id: Source work item ID
            target_id: Target work item ID
            relation_type: Relation type (e.g., "System.LinkTypes.Hierarchy-Reverse")

        Returns:
            Updated source work item dict
        """
        project = self._get_project()
        base_url = self._get_base_url()

        # Build relation patch
        patch = [{
            "op": "add",
            "path": "/relations/-",
            "value": {
                "rel": relation_type,
                "url": f"{base_url}/_apis/wit/workitems/{target_id}"
            }
        }]

        # Update source work item with relation
        endpoint = f"{project}/_apis/wit/workitems/{source_id}"
        params = {"api-version": "7.1"}

        return self._make_request("PATCH", endpoint, data=patch, params=params)

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

        Checks for existing work item with same title in current sprint.
        If found, returns existing item. If not found, creates new item.

        Args:
            title: Work item title
            work_item_type: Type (Task, Bug, Feature, etc.)
            description: Description
            sprint_name: Optional sprint name to check
            **kwargs: Additional arguments for create_work_item

        Returns:
            Dict with keys: id, created (bool), existing (bool), work_item
        """
        # Search for existing work item
        if sprint_name:
            project = self._config.get('project', '')
            iteration_path = f"{project}\\\\{sprint_name}"

            wiql = f"""
                SELECT [System.Id], [System.Title]
                FROM WorkItems
                WHERE [System.IterationPath] = '{iteration_path}'
                AND [System.Title] = '{title.replace("'", "''")}'
            """

            try:
                results = self.query_work_items(wiql)
                if results:
                    work_item_id = results[0].get('id') or results[0].get('System.Id')
                    print(f"ℹ️  Work item already exists: WI-{work_item_id} - {title}")
                    work_item = self.get_work_item(work_item_id)
                    return {
                        "id": work_item_id,
                        "created": False,
                        "existing": True,
                        "work_item": work_item
                    }
            except Exception as e:
                print(f"Warning: Could not check for existing work item: {e}")

        # Create new work item
        if sprint_name:
            project = self._config.get('project', '')
            kwargs['iteration'] = f"{project}\\{sprint_name}"

        work_item = self.create_work_item(
            work_item_type=work_item_type,
            title=title,
            description=description,
            **kwargs
        )

        return {
            "id": work_item.get('id'),
            "created": True,
            "existing": False,
            "work_item": work_item
        }

    # Pull Requests

    def _get_repository_id(self, repository_name: Optional[str] = None) -> str:
        """
        Get repository ID by name using REST API.

        Args:
            repository_name: Repository name. If not provided, uses project name.

        Returns:
            Repository ID (GUID)

        Raises:
            Exception: If repository not found (404) or request fails
        """
        project = self._get_project()
        repo_name = repository_name or project

        endpoint = f"{project}/_apis/git/repositories/{repo_name}"
        params = {"api-version": "7.1"}

        try:
            result = self._make_request("GET", endpoint, params=params)
            return result.get("id")
        except Exception as e:
            error_msg = str(e)
            if "404" in error_msg:
                raise Exception(
                    f"Repository '{repo_name}' not found in project '{project}'. "
                    f"Verify the repository name exists in Azure DevOps."
                ) from e
            elif "401" in error_msg or "403" in error_msg:
                raise AuthenticationError(
                    f"Authentication failed when getting repository '{repo_name}'. "
                    f"Verify your Azure DevOps PAT token is valid and has Code (Read) scope."
                ) from e
            else:
                raise Exception(
                    f"Failed to get repository '{repo_name}': {error_msg}"
                ) from e

    def _get_current_user_id(self) -> str:
        """
        Get the current authenticated user's ID for use as reviewer.

        Returns:
            User ID (GUID) of the authenticated user

        Raises:
            AuthenticationError: If authentication fails or user info unavailable
        """
        # Use the Connection Data API to get current user info
        # This endpoint returns information about the authenticated user
        endpoint = "_apis/connectionData"
        params = {"api-version": "7.1-preview"}

        try:
            result = self._make_request("GET", endpoint, params=params)
            authenticated_user = result.get("authenticatedUser", {})
            user_id = authenticated_user.get("id")

            if not user_id:
                raise AuthenticationError(
                    "Could not determine authenticated user ID. "
                    "Verify your Azure DevOps PAT token is valid."
                )

            return user_id
        except Exception as e:
            if isinstance(e, AuthenticationError):
                raise
            error_msg = str(e)
            if "401" in error_msg or "403" in error_msg:
                raise AuthenticationError(
                    "Authentication failed when getting current user info. "
                    "Verify your Azure DevOps PAT token is valid."
                ) from e
            else:
                raise AuthenticationError(
                    f"Failed to get current user info: {error_msg}"
                ) from e

    def create_pull_request(
        self,
        source_branch: str,
        title: str,
        description: str,
        work_item_ids: Optional[List[int]] = None,
        reviewers: Optional[List[str]] = None,
        target_branch: str = "main",
        repository_name: Optional[str] = None
    ) -> Dict:
        """
        Create a pull request using Azure DevOps REST API.

        Args:
            source_branch: Source branch name (e.g., "feature/my-feature")
            title: Pull request title
            description: Pull request description (supports markdown)
            work_item_ids: List of work item IDs to link to the PR
            reviewers: List of reviewer IDs (GUIDs) or email addresses
            target_branch: Target branch name (default: "main")
            repository_name: Repository name. If not provided, uses project name.

        Returns:
            Dict containing:
            - id: Pull request ID
            - url: Pull request URL
            - status: PR status (e.g., "active")
            - sourceRefName: Source branch ref
            - targetRefName: Target branch ref
            - title: PR title
            - description: PR description
            - createdBy: User who created the PR
            - creationDate: Creation timestamp

        Raises:
            Exception: If repository or branch not found (404)
            AuthenticationError: If authentication fails (401/403)
            Exception: For other API errors (400, etc.)

        Example:
            >>> cli.create_pull_request(
            ...     source_branch="feature/new-feature",
            ...     title="Add new feature",
            ...     description="This PR adds...",
            ...     work_item_ids=[1234, 1235],
            ...     reviewers=["user@example.com"]
            ... )
            {'id': 42, 'url': 'https://dev.azure.com/org/project/_git/repo/pullrequest/42', ...}
        """
        project = self._get_project()

        # Get repository ID
        repository_id = self._get_repository_id(repository_name)

        # Build PR creation body
        # Branch refs must be in format "refs/heads/{branch_name}"
        source_ref = source_branch if source_branch.startswith("refs/") else f"refs/heads/{source_branch}"
        target_ref = target_branch if target_branch.startswith("refs/") else f"refs/heads/{target_branch}"

        pr_body: Dict[str, Any] = {
            "sourceRefName": source_ref,
            "targetRefName": target_ref,
            "title": title,
            "description": description
        }

        # Add work item references if provided
        if work_item_ids:
            pr_body["workItemRefs"] = [{"id": str(wid)} for wid in work_item_ids]

        # Add reviewers if provided
        if reviewers:
            pr_body["reviewers"] = [{"id": reviewer} for reviewer in reviewers]

        # REST API endpoint for PR creation
        endpoint = f"{project}/_apis/git/repositories/{repository_id}/pullrequests"
        params = {"api-version": "7.1"}

        try:
            result = self._make_request("POST", endpoint, data=pr_body, params=params)
            return result
        except Exception as e:
            error_msg = str(e)
            if "404" in error_msg:
                raise Exception(
                    f"Repository or branch not found. "
                    f"Verify repository '{repository_name or project}' exists and "
                    f"branches '{source_branch}' and '{target_branch}' are valid."
                ) from e
            elif "401" in error_msg or "403" in error_msg:
                raise AuthenticationError(
                    f"Authentication failed when creating pull request. "
                    f"Verify your Azure DevOps PAT token is valid and has Code (Read & Write) scope."
                ) from e
            elif "400" in error_msg:
                raise Exception(
                    f"Invalid pull request parameters. "
                    f"Check source branch '{source_branch}', target branch '{target_branch}', "
                    f"and reviewer IDs. Error: {error_msg}"
                ) from e
            else:
                raise Exception(
                    f"Failed to create pull request: {error_msg}"
                ) from e

    def approve_pull_request(
        self,
        pr_id: int,
        repository_name: Optional[str] = None
    ) -> Dict:
        """
        Approve a pull request using Azure DevOps REST API.

        Sets the current authenticated user's vote to 10 (Approved).

        Vote values:
        - 10: Approved
        - 5: Approved with suggestions
        - 0: No vote
        - -5: Waiting for author
        - -10: Rejected

        Args:
            pr_id: Pull request ID
            repository_name: Repository name. If not provided, uses project name.

        Returns:
            Dict containing reviewer vote details:
            - id: Reviewer ID
            - vote: Vote value (10 for Approved)
            - displayName: Reviewer display name
            - uniqueName: Reviewer unique name

        Raises:
            Exception: If PR not found (404)
            AuthenticationError: If authentication fails (401/403)
            Exception: For other API errors

        Example:
            >>> cli.approve_pull_request(pr_id=42)
            {'id': 'user-guid', 'vote': 10, 'displayName': 'User Name', ...}
        """
        project = self._get_project()

        # Get repository ID
        repository_id = self._get_repository_id(repository_name)

        # Get current user ID for reviewer
        reviewer_id = self._get_current_user_id()

        # Build approval body - vote 10 = Approved
        vote_body = {"vote": 10}

        # REST API endpoint for setting reviewer vote
        endpoint = f"{project}/_apis/git/repositories/{repository_id}/pullrequests/{pr_id}/reviewers/{reviewer_id}"
        params = {"api-version": "7.1"}

        try:
            result = self._make_request("PUT", endpoint, data=vote_body, params=params)
            return result
        except Exception as e:
            error_msg = str(e)
            if "404" in error_msg:
                raise Exception(
                    f"Pull request {pr_id} not found in repository '{repository_name or project}'. "
                    f"Verify the pull request ID exists."
                ) from e
            elif "401" in error_msg or "403" in error_msg:
                raise AuthenticationError(
                    f"Authentication failed when approving pull request {pr_id}. "
                    f"Verify your Azure DevOps PAT token is valid and has Code (Read & Write) scope."
                ) from e
            else:
                raise Exception(
                    f"Failed to approve pull request {pr_id}: {error_msg}"
                ) from e

    # Pipelines

    def _get_pipeline_id(self, pipeline_name: str) -> int:
        """
        Get pipeline ID by name using REST API.

        Args:
            pipeline_name: Pipeline name

        Returns:
            Pipeline ID

        Raises:
            Exception: If pipeline not found (404) or request fails
        """
        project = self._get_project()

        endpoint = f"{project}/_apis/pipelines"
        params = {"api-version": "7.1"}

        try:
            result = self._make_request("GET", endpoint, params=params)
            pipelines = result.get("value", [])

            for pipeline in pipelines:
                if pipeline.get("name") == pipeline_name:
                    return pipeline.get("id")

            raise Exception(
                f"Pipeline '{pipeline_name}' not found in project '{project}'. "
                f"Available pipelines: {[p.get('name') for p in pipelines]}"
            )
        except Exception as e:
            error_msg = str(e)
            if "404" in error_msg:
                raise Exception(
                    f"Pipelines API not accessible in project '{project}'. "
                    f"Verify the project name is correct."
                ) from e
            elif "401" in error_msg or "403" in error_msg:
                raise AuthenticationError(
                    f"Authentication failed when getting pipeline '{pipeline_name}'. "
                    f"Verify your Azure DevOps PAT token is valid and has Build (Read) scope."
                ) from e
            else:
                raise

    def trigger_pipeline(
        self,
        pipeline_id: int,
        branch: str,
        variables: Optional[Dict[str, str]] = None
    ) -> Dict:
        """
        Trigger a pipeline run using Azure DevOps REST API.

        Args:
            pipeline_id: Pipeline ID (use _get_pipeline_id to resolve from name)
            branch: Branch to build (e.g., "main", "refs/heads/feature-branch")
            variables: Optional dictionary of pipeline variables/parameters

        Returns:
            Dict containing:
            - id: Run ID
            - state: Run state (e.g., "inProgress", "completed")
            - result: Run result (e.g., "succeeded", "failed", "canceled")
            - url: Run URL
            - pipeline: Pipeline details
            - createdDate: Creation timestamp

        Raises:
            Exception: If pipeline not found (404)
            AuthenticationError: If authentication fails (401/403)
            Exception: For other API errors (400, 500)

        Example:
            >>> cli.trigger_pipeline(
            ...     pipeline_id=42,
            ...     branch="main",
            ...     variables={"environment": "production"}
            ... )
            {'id': 123, 'state': 'inProgress', 'url': 'https://...', ...}
        """
        project = self._get_project()

        # Build run request body
        # Branch refs must be in format "refs/heads/{branch_name}"
        if not branch.startswith("refs/"):
            branch = f"refs/heads/{branch}"

        run_body: Dict[str, Any] = {
            "resources": {
                "repositories": {
                    "self": {
                        "refName": branch
                    }
                }
            }
        }

        # Add variables/parameters if provided
        if variables:
            run_body["variables"] = {
                key: {"value": value}
                for key, value in variables.items()
            }

        # REST API endpoint for pipeline run
        endpoint = f"{project}/_apis/pipelines/{pipeline_id}/runs"
        params = {"api-version": "7.1"}

        try:
            result = self._make_request("POST", endpoint, data=run_body, params=params)
            return result
        except Exception as e:
            error_msg = str(e)
            if "404" in error_msg:
                raise Exception(
                    f"Pipeline {pipeline_id} not found in project '{project}'. "
                    f"Verify the pipeline ID is correct."
                ) from e
            elif "401" in error_msg or "403" in error_msg:
                raise AuthenticationError(
                    f"Authentication failed when triggering pipeline {pipeline_id}. "
                    f"Verify your Azure DevOps PAT token is valid and has Build (Read & Execute) scope."
                ) from e
            elif "400" in error_msg:
                raise Exception(
                    f"Invalid pipeline run parameters for pipeline {pipeline_id}. "
                    f"Check branch '{branch}' and variables. Error: {error_msg}"
                ) from e
            elif "500" in error_msg:
                raise Exception(
                    f"Azure DevOps server error when triggering pipeline {pipeline_id}. "
                    f"The service may be temporarily unavailable. Error: {error_msg}"
                ) from e
            else:
                raise Exception(
                    f"Failed to trigger pipeline {pipeline_id}: {error_msg}"
                ) from e

    def get_pipeline_run(self, pipeline_id: int, run_id: int) -> Dict:
        """
        Get pipeline run details using Azure DevOps REST API.

        Args:
            pipeline_id: Pipeline ID
            run_id: Run ID

        Returns:
            Dict containing:
            - id: Run ID
            - state: Run state (e.g., "inProgress", "completed")
            - result: Run result (e.g., "succeeded", "failed", "canceled", None if in progress)
            - finishedDate: Completion timestamp (None if in progress)
            - url: Run URL
            - pipeline: Pipeline details
            - createdDate: Creation timestamp

        Raises:
            Exception: If pipeline or run not found (404)
            AuthenticationError: If authentication fails (401/403)
            Exception: For other API errors (500)

        Example:
            >>> cli.get_pipeline_run(pipeline_id=42, run_id=123)
            {'id': 123, 'state': 'completed', 'result': 'succeeded', ...}
        """
        project = self._get_project()

        # REST API endpoint for pipeline run
        endpoint = f"{project}/_apis/pipelines/{pipeline_id}/runs/{run_id}"
        params = {"api-version": "7.1"}

        try:
            result = self._make_request("GET", endpoint, params=params)
            return result
        except Exception as e:
            error_msg = str(e)
            if "404" in error_msg:
                raise Exception(
                    f"Pipeline run {run_id} not found for pipeline {pipeline_id} in project '{project}'. "
                    f"Verify the pipeline ID and run ID are correct."
                ) from e
            elif "401" in error_msg or "403" in error_msg:
                raise AuthenticationError(
                    f"Authentication failed when getting pipeline run {run_id}. "
                    f"Verify your Azure DevOps PAT token is valid and has Build (Read) scope."
                ) from e
            elif "500" in error_msg:
                raise Exception(
                    f"Azure DevOps server error when getting pipeline run {run_id}. "
                    f"The service may be temporarily unavailable. Error: {error_msg}"
                ) from e
            else:
                raise Exception(
                    f"Failed to get pipeline run {run_id}: {error_msg}"
                ) from e

    # Iterations (Sprints)

    def create_iteration(
        self,
        name: str,
        start_date: Optional[str] = None,
        finish_date: Optional[str] = None,
        project: Optional[str] = None
    ) -> Dict:
        """
        Create a new iteration/sprint using REST API.

        Args:
            name: Iteration name (e.g., "Sprint 6")
            start_date: Start date in YYYY-MM-DD format (converted to ISO 8601)
            finish_date: Finish date in YYYY-MM-DD format (converted to ISO 8601)
            project: Project name (optional, uses config if not provided)

        Returns:
            Dict containing:
            - id: Iteration ID
            - identifier: GUID identifier
            - name: Iteration name
            - structureType: "iteration"
            - path: Full iteration path
            - attributes: Dict with startDate and finishDate if provided

        Raises:
            Exception: If iteration already exists (400), authentication fails (401/403),
                      project not found (404), or other API errors (500)

        Example:
            >>> cli.create_iteration("Sprint 6", "2025-01-01", "2025-01-14")
            {'id': 12345, 'name': 'Sprint 6', 'attributes': {'startDate': '2025-01-01T00:00:00Z', ...}}
        """
        if not project:
            project = self._get_project()

        # Build request body
        body: Dict[str, Any] = {"name": name}

        # Add attributes if dates provided
        if start_date or finish_date:
            attributes = {}
            if start_date:
                # Convert YYYY-MM-DD to ISO 8601 format
                attributes["startDate"] = self._format_date_iso8601(start_date)
            if finish_date:
                attributes["finishDate"] = self._format_date_iso8601(finish_date)
            body["attributes"] = attributes

        # REST API endpoint for iteration creation
        endpoint = f"{project}/_apis/wit/classificationnodes/Iterations"
        params = {"api-version": "7.1"}

        try:
            result = self._make_request("POST", endpoint, data=body, params=params)
            return result
        except Exception as e:
            error_msg = str(e)
            if "400" in error_msg:
                raise Exception(
                    f"Failed to create iteration '{name}'. "
                    f"The iteration may already exist or the request is invalid. "
                    f"Error: {error_msg}"
                ) from e
            elif "401" in error_msg or "403" in error_msg:
                raise AuthenticationError(
                    f"Authentication failed when creating iteration '{name}'. "
                    f"Verify your Azure DevOps PAT token is valid and has Work Items (Read & Write) scope."
                ) from e
            elif "404" in error_msg:
                raise Exception(
                    f"Project '{project}' not found when creating iteration '{name}'. "
                    f"Verify the project name is correct."
                ) from e
            elif "500" in error_msg:
                raise Exception(
                    f"Azure DevOps server error when creating iteration '{name}'. "
                    f"The service may be temporarily unavailable. Error: {error_msg}"
                ) from e
            else:
                raise Exception(
                    f"Failed to create iteration '{name}': {error_msg}"
                ) from e

    def list_iterations(
        self,
        project: Optional[str] = None,
        depth: int = 10
    ) -> List[Dict]:
        """
        List all iterations/sprints using REST API.

        Args:
            project: Project name (optional, uses config if not provided)
            depth: Depth of iteration hierarchy to fetch (default: 10)

        Returns:
            List of iteration dicts, each containing:
            - id: Iteration ID
            - identifier: GUID identifier
            - name: Iteration name
            - structureType: "iteration"
            - path: Full iteration path
            - attributes: Dict with startDate and finishDate if set
            - hasChildren: Boolean indicating if iteration has children
            - children: List of child iterations (if depth > 0)

        Raises:
            Exception: If project not found (404), authentication fails (401/403),
                      or other API errors (500)

        Example:
            >>> cli.list_iterations()
            [
                {
                    'id': 12345,
                    'name': 'Sprint 6',
                    'path': '\\\\Project\\\\Iteration\\\\Sprint 6',
                    'attributes': {'startDate': '2025-01-01T00:00:00Z', ...}
                }
            ]
        """
        if not project:
            project = self._get_project()

        # REST API endpoint for listing iterations
        endpoint = f"{project}/_apis/wit/classificationnodes/Iterations"
        params = {
            "api-version": "7.1",
            "$depth": str(depth)
        }

        try:
            result = self._make_request("GET", endpoint, params=params)

            # Extract children (iterations) from the root node
            # The API returns a single root node with children representing actual iterations
            children = result.get("children", [])

            # Flatten the hierarchy into a list for backward compatibility
            iterations = self._flatten_iteration_hierarchy(children)

            return iterations
        except Exception as e:
            error_msg = str(e)
            if "404" in error_msg:
                raise Exception(
                    f"Project '{project}' not found when listing iterations. "
                    f"Verify the project name is correct."
                ) from e
            elif "401" in error_msg or "403" in error_msg:
                raise AuthenticationError(
                    f"Authentication failed when listing iterations for project '{project}'. "
                    f"Verify your Azure DevOps PAT token is valid and has Work Items (Read) scope."
                ) from e
            elif "500" in error_msg:
                raise Exception(
                    f"Azure DevOps server error when listing iterations. "
                    f"The service may be temporarily unavailable. Error: {error_msg}"
                ) from e
            else:
                raise Exception(
                    f"Failed to list iterations for project '{project}': {error_msg}"
                ) from e

    def update_iteration(
        self,
        path: str,
        start_date: Optional[str] = None,
        finish_date: Optional[str] = None,
        project: Optional[str] = None
    ) -> Dict:
        """
        Update iteration dates using REST API.

        Args:
            path: Iteration path. Can be:
                  - Simple name: "Sprint 6" (will construct full path)
                  - Full path: "\\Project\\Iteration\\Sprint 6"
            start_date: New start date in YYYY-MM-DD format (converted to ISO 8601)
            finish_date: New finish date in YYYY-MM-DD format (converted to ISO 8601)
            project: Project name (optional, uses config if not provided)

        Returns:
            Dict containing updated iteration:
            - id: Iteration ID
            - identifier: GUID identifier
            - name: Iteration name
            - structureType: "iteration"
            - path: Full iteration path
            - attributes: Dict with updated startDate and finishDate

        Raises:
            Exception: If iteration not found (404), authentication fails (401/403),
                      invalid parameters (400), or other API errors (500)

        Example:
            >>> cli.update_iteration("Sprint 6", "2025-01-01", "2025-01-14")
            {'id': 12345, 'name': 'Sprint 6', 'attributes': {'startDate': '2025-01-01T00:00:00Z', ...}}

        Note:
            At least one of start_date or finish_date must be provided.
        """
        if not start_date and not finish_date:
            raise ValueError("At least one of start_date or finish_date must be provided")

        if not project:
            project = self._get_project()

        # Normalize path - remove leading/trailing backslashes and "Iteration" if present
        normalized_path = self._normalize_iteration_path(path, project)

        # Build request body with attributes
        attributes = {}
        if start_date:
            attributes["startDate"] = self._format_date_iso8601(start_date)
        if finish_date:
            attributes["finishDate"] = self._format_date_iso8601(finish_date)

        body = {"attributes": attributes}

        # REST API endpoint for iteration update
        endpoint = f"{project}/_apis/wit/classificationnodes/Iterations/{normalized_path}"
        params = {"api-version": "7.1"}

        try:
            result = self._make_request("PATCH", endpoint, data=body, params=params)
            return result
        except Exception as e:
            error_msg = str(e)
            if "404" in error_msg:
                raise Exception(
                    f"Iteration not found at path '{path}'. "
                    f"Verify the iteration exists in Azure DevOps. "
                    f"Use list_iterations() to see available iterations."
                ) from e
            elif "401" in error_msg or "403" in error_msg:
                raise AuthenticationError(
                    f"Authentication failed when updating iteration '{path}'. "
                    f"Verify your Azure DevOps PAT token is valid and has Work Items (Read & Write) scope."
                ) from e
            elif "400" in error_msg:
                raise Exception(
                    f"Invalid parameters when updating iteration '{path}'. "
                    f"Check date formats and iteration path. Error: {error_msg}"
                ) from e
            elif "500" in error_msg:
                raise Exception(
                    f"Azure DevOps server error when updating iteration '{path}'. "
                    f"The service may be temporarily unavailable. Error: {error_msg}"
                ) from e
            else:
                raise Exception(
                    f"Failed to update iteration '{path}': {error_msg}"
                ) from e

    def create_sprint_work_items_batch(
        self,
        sprint_name: str,
        work_items: List[Dict[str, Any]],
        project_name: Optional[str] = None
    ) -> List[Dict]:
        """
        Create multiple work items for a sprint efficiently.

        LEARNING: Batch creation is more reliable than individual calls.
        """
        if not project_name:
            project_name = self._config.get('project', '')

        iteration_path = f"{project_name}\\{sprint_name}"

        results = []
        for item in work_items:
            result = self.create_work_item(
                work_item_type=item['type'],
                title=item['title'],
                description=item.get('description', ''),
                iteration=iteration_path,
                fields=item.get('fields'),
                parent_id=item.get('parent_id')
            )
            results.append(result)

        return results

    def query_sprint_work_items(
        self,
        sprint_name: str,
        project_name: Optional[str] = None,
        include_fields: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Query all work items in a sprint.

        LEARNING: WIQL iteration paths use double backslashes for escaping.
        """
        if not project_name:
            project_name = self._config.get('project', '')

        iteration_path = f"{project_name}\\\\{sprint_name}"

        fields = ["System.Id", "System.Title", "System.State", "Microsoft.VSTS.Scheduling.StoryPoints"]
        if include_fields:
            fields.extend(include_fields)

        field_list = ", ".join(f"[{field}]" for field in fields)

        wiql = f"""
            SELECT {field_list}
            FROM WorkItems
            WHERE [System.IterationPath] = '{iteration_path}'
            ORDER BY [System.Id]
        """

        return self.query_work_items(wiql)

    def check_recent_duplicates(
        self,
        title: str,
        work_item_type: str,
        hours: int = 1,
        similarity_threshold: float = 0.95
    ) -> Optional[Dict[str, Any]]:
        """
        Check for recently created work items with similar titles.

        Queries work items of the same type created in the last N hours
        and calculates title similarity using difflib.SequenceMatcher.

        Args:
            title: Title to check for duplicates
            work_item_type: Type of work item (Task, Bug, Feature, etc.)
            hours: Time window to check (default: 1 hour)
            similarity_threshold: Similarity threshold (0.0-1.0, default: 0.95)

        Returns:
            Dict with duplicate work item details if found, None otherwise
            Format: {
                'id': work_item_id,
                'title': work_item_title,
                'similarity': similarity_score,
                'created_date': created_date,
                'state': current_state,
                'url': work_item_url
            }

        Example:
            duplicate = cli.check_recent_duplicates(
                "Fix authentication bug",
                "Bug",
                hours=1
            )
            if duplicate:
                print(f"Duplicate found: #{duplicate['id']} - {duplicate['title']}")
        """
        from difflib import SequenceMatcher
        from datetime import datetime, timedelta

        # Calculate time threshold
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        cutoff_str = cutoff_time.strftime("%Y-%m-%dT%H:%M:%SZ")

        # Query recent work items of same type
        # WIQL uses single quotes for string literals
        wiql = f"""
            SELECT [System.Id], [System.Title], [System.CreatedDate], [System.State]
            FROM WorkItems
            WHERE [System.WorkItemType] = '{work_item_type}'
            AND [System.CreatedDate] >= '{cutoff_str}'
            ORDER BY [System.CreatedDate] DESC
        """

        try:
            recent_items = self.query_work_items(wiql)
        except Exception as e:
            # If query fails, log warning but don't block workflow
            print(f"Warning: Could not check for duplicates: {e}")
            return None

        # Check each recent item for title similarity
        for item in recent_items:
            fields = item.get('fields', {})
            item_title = fields.get('System.Title', '')

            # Calculate similarity using SequenceMatcher
            # SequenceMatcher.ratio() returns value between 0.0 and 1.0
            similarity = SequenceMatcher(None, title.lower(), item_title.lower()).ratio()

            if similarity >= similarity_threshold:
                # Found a duplicate
                item_id = item.get('id')
                created_date = fields.get('System.CreatedDate', '')
                state = fields.get('System.State', '')

                # Build work item URL
                base_url = self._get_base_url()
                work_item_url = f"{base_url}/_workitems/edit/{item_id}"

                return {
                    'id': item_id,
                    'title': item_title,
                    'similarity': similarity,
                    'created_date': created_date,
                    'state': state,
                    'url': work_item_url
                }

        # No duplicates found
        return None

    # REST API Helper Methods

    def _get_base_url(self) -> str:
        """Get Azure DevOps organization URL from config."""
        org_url = self._config.get('organization', '')
        if not org_url:
            raise Exception("Azure DevOps organization not configured")
        return org_url.rstrip('/')

    def _get_project(self) -> str:
        """Get project name from config."""
        project = self._config.get('project', '')
        if not project:
            raise Exception("Azure DevOps project not configured")
        return project

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Any] = None,
        params: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Make authenticated REST API request to Azure DevOps.

        Args:
            method: HTTP method (GET, POST, PATCH)
            endpoint: API endpoint (e.g., "Project/_apis/wit/workitems/1234")
            data: Request body (list for JSON Patch, dict for JSON)
            params: Query parameters (e.g., {"api-version": "7.1"})

        Returns:
            Response JSON as dict

        Raises:
            ImportError: If requests library not available
            Exception: If request fails with status code and error details
        """
        if not HAS_REQUESTS:
            raise ImportError("requests library required for REST API operations. Install with: pip install requests")

        url = f"{self._get_base_url()}/{endpoint}"
        token = self._get_auth_token()
        auth = base64.b64encode(f":{token}".encode()).decode()

        # Use correct Content-Type based on data type
        # JSON Patch operations use application/json-patch+json
        # Regular JSON operations use application/json
        if isinstance(data, list):
            content_type = "application/json-patch+json"
        else:
            content_type = "application/json"

        headers = {
            "Authorization": f"Basic {auth}",
            "Content-Type": content_type
        }

        response = requests.request(
            method=method,
            url=url,
            json=data,
            params=params,
            headers=headers
        )

        if response.status_code not in [200, 201]:
            raise Exception(
                f"Azure DevOps REST API request failed:\n"
                f"  Method: {method}\n"
                f"  URL: {url}\n"
                f"  Status: {response.status_code}\n"
                f"  Error: {response.text}"
            )

        return response.json() if response.text else {}

    def _build_json_patch(self, fields: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Build JSON Patch operations from field dict.

        Args:
            fields: Dictionary of field names to values
                   (e.g., {"System.Title": "Task", "System.State": "Done"})

        Returns:
            JSON Patch array for PATCH request (RFC 6902 format)

        Example:
            >>> _build_json_patch({"System.Title": "Task", "System.State": "Done"})
            [
                {"op": "add", "path": "/fields/System.Title", "value": "Task"},
                {"op": "add", "path": "/fields/System.State", "value": "Done"}
            ]
        """
        return [
            {"op": "add", "path": f"/fields/{name}", "value": value}
            for name, value in fields.items()
            if value is not None
        ]

    def _needs_markdown_format(self, fields: Dict[str, Any]) -> bool:
        """
        Check if fields contain markdown-eligible fields.

        Args:
            fields: Dictionary of field names to values

        Returns:
            True if any field should use markdown formatting
        """
        markdown_fields = [
            "System.Description",
            "Microsoft.VSTS.Common.AcceptanceCriteria",
            "Microsoft.VSTS.TCM.ReproSteps"
        ]
        return any(field in fields for field in markdown_fields)

    def _format_date_iso8601(self, date_str: str) -> str:
        """
        Convert date string to ISO 8601 format for Azure DevOps API.

        Args:
            date_str: Date in YYYY-MM-DD format

        Returns:
            ISO 8601 formatted string (YYYY-MM-DDTHH:MM:SSZ)

        Example:
            >>> _format_date_iso8601("2025-01-01")
            "2025-01-01T00:00:00Z"
        """
        from datetime import datetime

        # Parse YYYY-MM-DD format
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            # Return ISO 8601 format with UTC timezone
            return date_obj.strftime("%Y-%m-%dT%H:%M:%SZ")
        except ValueError as e:
            raise ValueError(
                f"Invalid date format: '{date_str}'. Expected YYYY-MM-DD format."
            ) from e

    def _normalize_iteration_path(self, path: str, project: str) -> str:
        """
        Normalize iteration path for Azure DevOps REST API.

        Handles various path formats and converts them to the format expected
        by the classification nodes API (just the iteration name without project prefix).

        Args:
            path: Iteration path in various formats:
                  - "Sprint 6"
                  - "\\Project\\Iteration\\Sprint 6"
                  - "Project\\Iteration\\Sprint 6"
            project: Project name

        Returns:
            Normalized path for REST API (e.g., "Sprint 6")

        Example:
            >>> _normalize_iteration_path("Sprint 6", "MyProject")
            "Sprint 6"
            >>> _normalize_iteration_path("\\MyProject\\Iteration\\Sprint 6", "MyProject")
            "Sprint 6"
        """
        # Remove leading/trailing backslashes
        normalized = path.strip("\\")

        # Remove project prefix if present (case-insensitive)
        if normalized.lower().startswith(project.lower() + "\\"):
            normalized = normalized[len(project) + 1:]

        # Remove "Iteration\\" prefix if present (case-insensitive)
        if normalized.lower().startswith("iteration\\"):
            normalized = normalized[10:]  # len("iteration\\") = 10

        return normalized

    def _flatten_iteration_hierarchy(self, nodes: List[Dict]) -> List[Dict]:
        """
        Flatten nested iteration hierarchy into a flat list.

        Args:
            nodes: List of iteration nodes with potential children

        Returns:
            Flat list of all iterations (including nested children)

        Example:
            Input: [{'name': 'Sprint 1', 'children': [{'name': 'Sub-Sprint'}]}]
            Output: [{'name': 'Sprint 1', ...}, {'name': 'Sub-Sprint', ...}]
        """
        result = []

        for node in nodes:
            # Add current node
            result.append(node)

            # Recursively add children
            if node.get("hasChildren") and node.get("children"):
                result.extend(self._flatten_iteration_hierarchy(node["children"]))

        return result

    # File Attachments (requires requests library)

    def _load_pat_from_env(self) -> Optional[str]:
        """
        Load PAT token from AZURE_DEVOPS_EXT_PAT environment variable.

        Returns:
            PAT token if found, None otherwise
        """
        token = os.environ.get('AZURE_DEVOPS_EXT_PAT', '').strip()
        return token if token else None

    def _load_pat_from_config(self) -> Optional[str]:
        """
        Load PAT token from .claude/config.yaml credentials_source field.

        Supports:
        - env:VARIABLE_NAME format to load from alternate env vars
        - Direct PAT token string (discouraged, warns in logs)

        Returns:
            PAT token if found, None otherwise
        """
        try:
            config_path = Path.cwd() / ".claude" / "config.yaml"
            if not config_path.exists():
                return None

            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            if not config or 'work_tracking' not in config:
                return None

            credentials_source = config['work_tracking'].get('credentials_source', '')

            if not credentials_source or credentials_source == 'cli':
                return None

            # Handle env:VARIABLE_NAME format
            if credentials_source.startswith('env:'):
                var_name = credentials_source[4:].strip()
                token = os.environ.get(var_name, '').strip()
                return token if token else None

            # Handle direct PAT token (discouraged)
            # If it looks like a base64 PAT token, use it
            # Azure DevOps PATs can be various lengths but typically 52 chars
            import re
            if len(credentials_source) >= 20 and re.match(r'^[A-Za-z0-9+/=]+$', credentials_source):
                print("WARNING: Direct PAT token in config.yaml is discouraged. Use env:VARIABLE_NAME instead.")
                return credentials_source.strip()

            return None

        except (yaml.YAMLError, IOError, KeyError) as e:
            # If config parsing fails, log but don't raise - allow fallback to other methods
            print(f"Warning: Could not load PAT from config: {e}")
            return None

    def _validate_pat_token(self, token: str) -> bool:
        """
        Validate PAT token format.

        Args:
            token: PAT token to validate

        Returns:
            True if valid, False otherwise
        """
        if not token or not isinstance(token, str):
            return False

        token = token.strip()

        # Check minimum length (Azure DevOps PATs are typically 52 characters)
        if len(token) < 20:
            return False

        # Check if token contains only base64-compatible characters
        # Base64 uses: A-Z, a-z, 0-9, +, /, and = for padding
        import re
        if not re.match(r'^[A-Za-z0-9+/=]+$', token):
            return False

        return True

    def _get_cached_or_load_token(self) -> str:
        """
        Get cached PAT token or load from available sources.

        Attempts to load from:
        1. AZURE_DEVOPS_EXT_PAT environment variable
        2. credentials_source in .claude/config.yaml

        Returns:
            PAT token

        Raises:
            AuthenticationError: If no valid token found
        """
        # Return cached token if available and valid
        if self._cached_token and self._validate_pat_token(self._cached_token):
            return self._cached_token

        # Try loading from environment variable
        token = self._load_pat_from_env()

        # If not found, try loading from config
        if not token:
            token = self._load_pat_from_config()

        # Validate token
        if not token or not self._validate_pat_token(token):
            org_url = self._config.get('organization', 'https://dev.azure.com/{organization}')
            raise AuthenticationError(
                f"Azure DevOps PAT token not found or invalid. "
                f"Set AZURE_DEVOPS_EXT_PAT environment variable or configure credentials_source in .claude/config.yaml. "
                f"Generate a PAT at: {org_url}/_usersSettings/tokens"
            )

        # Cache valid token
        self._cached_token = token
        return token

    def _get_auth_token(self) -> str:
        """
        Get Azure DevOps access token using PAT authentication.

        Returns:
            PAT token for Basic authentication

        Raises:
            AuthenticationError: If no valid PAT token found
        """
        return self._get_cached_or_load_token()

    def attach_file_to_work_item(
        self,
        work_item_id: int,
        file_path: Path,
        comment: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Attach a file to a work item using Azure DevOps REST API.

        Requires the requests library.
        """
        if not HAS_REQUESTS:
            raise ImportError("requests library required for file attachments. Install with: pip install requests")

        if not isinstance(file_path, Path):
            file_path = Path(file_path)

        if not file_path.exists():
            raise Exception(f"File not found: {file_path}")

        org_url = self._config.get('organization', '')
        project = self._config.get('project', '')

        if not org_url or not project:
            raise Exception("Azure DevOps organization and project must be configured")

        token = self._get_auth_token()
        if not token:
            raise Exception("No Azure DevOps authentication token found")

        auth = base64.b64encode(f":{token}".encode()).decode()

        # Step 1: Upload file
        upload_url = f"{org_url}/_apis/wit/attachments?fileName={file_path.name}&api-version=7.1"

        with open(file_path, 'rb') as f:
            file_content = f.read()

        upload_response = requests.post(
            upload_url,
            data=file_content,
            headers={
                "Authorization": f"Basic {auth}",
                "Content-Type": "application/octet-stream"
            }
        )

        if upload_response.status_code != 201:
            raise Exception(f"Failed to upload attachment: {upload_response.status_code}")

        attachment_url = upload_response.json().get('url')

        # Step 2: Link to work item
        patch_url = f"{org_url}/{project}/_apis/wit/workitems/{work_item_id}?api-version=7.1"

        patch_doc = [{
            "op": "add",
            "path": "/relations/-",
            "value": {
                "rel": "AttachedFile",
                "url": attachment_url,
                "attributes": {"comment": comment or f"Attached {file_path.name}"}
            }
        }]

        link_response = requests.patch(
            patch_url,
            json=patch_doc,
            headers={
                "Authorization": f"Basic {auth}",
                "Content-Type": "application/json-patch+json"
            }
        )

        if link_response.status_code not in [200, 201]:
            raise Exception(f"Failed to link attachment: {link_response.status_code}")

        return {
            "work_item_id": work_item_id,
            "file_name": file_path.name,
            "file_path": str(file_path),
            "attachment_url": attachment_url,
            "comment": comment,
            "success": True
        }

    def verify_attachment_exists(
        self,
        work_item_id: int,
        filename: str
    ) -> bool:
        """
        Check if a file is attached to a work item.

        Args:
            work_item_id: Work item ID
            filename: Name of file to check for

        Returns:
            True if attachment exists, False otherwise
        """
        try:
            work_item = self.get_work_item(work_item_id)
            relations = work_item.get('relations', [])

            for relation in relations:
                if relation.get('rel') == 'AttachedFile':
                    # Extract filename from URL
                    url = relation.get('url', '')
                    if filename in url or relation.get('attributes', {}).get('name') == filename:
                        return True

            return False

        except Exception as e:
            print(f"Error checking attachment: {e}")
            return False


# Singleton instance
azure_cli = AzureCLI()

# Convenience functions for work items
def query_work_items(wiql: str) -> List[Dict]:
    """Query work items using WIQL"""
    return azure_cli.query_work_items(wiql)

def create_work_item(work_item_type: str, title: str, description: str = "", **kwargs) -> Dict:
    """Create a work item with automatic iteration assignment"""
    return azure_cli.create_work_item(work_item_type, title, description, **kwargs)

def update_work_item(work_item_id: int, **kwargs) -> Dict:
    """Update a work item"""
    return azure_cli.update_work_item(work_item_id, **kwargs)

def add_comment(work_item_id: int, comment: str, agent_name: str = None) -> Dict:
    """Add a comment to a work item (optionally prefixed with agent name)"""
    if agent_name:
        comment = f"[{agent_name}] {comment}"
    return azure_cli.add_comment(work_item_id, comment)

# Convenience functions for pull requests
def create_pull_request(source_branch: str, title: str, description: str, work_item_ids: List[int]) -> Dict:
    """Create a pull request"""
    return azure_cli.create_pull_request(source_branch, title, description, work_item_ids)

def approve_pull_request(pr_id: int) -> Dict:
    """Approve a pull request"""
    return azure_cli.approve_pull_request(pr_id)

# Convenience functions for iterations (NEW)
def create_sprint(
    sprint_name: str,
    start_date: Optional[str] = None,
    finish_date: Optional[str] = None,
    project: Optional[str] = None
) -> Dict:
    """
    Create a new sprint/iteration.

    Args:
        sprint_name: Sprint name (e.g., "Sprint 9")
        start_date: Start date in YYYY-MM-DD format (optional)
        finish_date: Finish date in YYYY-MM-DD format (optional)
        project: Project name (optional)

    Returns:
        Created iteration details

    Example:
        create_sprint("Sprint 9", "2025-11-07", "2025-11-20")
    """
    return azure_cli.create_iteration(sprint_name, start_date, finish_date, project)

def list_sprints(project: Optional[str] = None) -> List[Dict]:
    """List all sprints/iterations"""
    return azure_cli.list_iterations(project)

def update_sprint_dates(
    sprint_name: str,
    start_date: str,
    finish_date: str,
    project: Optional[str] = None
) -> Dict:
    """
    Update sprint dates using correct path format.

    Args:
        sprint_name: Sprint name (e.g., "Sprint 4")
        start_date: Start date in YYYY-MM-DD format
        finish_date: Finish date in YYYY-MM-DD format
        project: Project name (optional)

    Example:
        update_sprint_dates("Sprint 4", "2025-11-07", "2025-11-20")
    """
    if not project:
        project = azure_cli._config.get('project', '')

    # Build full path for iteration update
    path = f"\\{project}\\Iteration\\{sprint_name}"

    return azure_cli.update_iteration(path, start_date, finish_date, project)

def create_sprint_work_items(
    sprint_name: str,
    work_items: List[Dict[str, Any]],
    project: Optional[str] = None
) -> List[Dict]:
    """
    Create multiple work items for a sprint in batch.

    Args:
        sprint_name: Sprint name (e.g., "Sprint 4")
        work_items: List of dicts with keys: type, title, description, fields
        project: Project name (optional)

    Example:
        work_items = [
            {
                "type": "Task",
                "title": "Implement feature X",
                "description": "Details...",
                "fields": {"Microsoft.VSTS.Scheduling.StoryPoints": 5}
            }
        ]
        results = create_sprint_work_items("Sprint 4", work_items)
    """
    return azure_cli.create_sprint_work_items_batch(sprint_name, work_items, project)

def query_sprint_work_items(
    sprint_name: str,
    project: Optional[str] = None
) -> List[Dict]:
    """
    Query all work items in a sprint.

    Args:
        sprint_name: Sprint name (e.g., "Sprint 4")
        project: Project name (optional)

    Returns:
        List of work items with Id, Title, State, and Story Points
    """
    return azure_cli.query_sprint_work_items(sprint_name, project)

def check_recent_duplicates(
    title: str,
    work_item_type: str,
    hours: int = 1,
    similarity_threshold: float = 0.95
) -> Optional[Dict[str, Any]]:
    """
    Check for recently created work items with similar titles.

    Args:
        title: Title to check for duplicates
        work_item_type: Type of work item (Task, Bug, Feature, etc.)
        hours: Time window to check (default: 1 hour)
        similarity_threshold: Similarity threshold (0.0-1.0, default: 0.95)

    Returns:
        Dict with duplicate work item details if found, None otherwise

    Example:
        duplicate = check_recent_duplicates("Fix auth bug", "Bug")
        if duplicate:
            print(f"Found duplicate: #{duplicate['id']}")
    """
    return azure_cli.check_recent_duplicates(title, work_item_type, hours, similarity_threshold)
