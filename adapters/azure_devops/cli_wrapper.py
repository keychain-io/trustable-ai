"""
Azure CLI Wrapper for Claude Code Agents
Simplifies Azure DevOps operations with battle-tested patterns

Key Learnings Applied:
1. Iteration paths use simplified format: "Project\\SprintName"
2. Work items need two-step creation (create then assign iteration)
3. Field names are case-sensitive
4. Project names with spaces must be quoted
5. WIQL queries need double backslashes for escaping
"""

import json
import subprocess
import base64
import requests
from pathlib import Path
from typing import Any, Dict, List, Optional


class AzureCLI:
    """Wrapper for Azure CLI DevOps operations"""

    def __init__(self):
        self._config = self._ensure_configured()

    def _ensure_configured(self) -> Dict[str, str]:
        """Verify Azure CLI is configured and return config"""
        result = subprocess.run(
            ['az', 'devops', 'configure', '--list'],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            raise Exception("Azure CLI not configured. Run setup first.")

        # Parse configuration
        config = {}
        for line in result.stdout.strip().split('\n'):
            if '=' in line:
                key, value = line.split('=', 1)
                config[key.strip()] = value.strip()
        return config

    def _run_command(self, cmd: List[str]) -> Dict[str, Any]:
        """Execute Azure CLI command and return JSON result"""
        if '--output' not in cmd and '-o' not in cmd:
            cmd.extend(['--output', 'json'])

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            return json.loads(result.stdout) if result.stdout else {}
        else:
            raise Exception(f"Command failed: {' '.join(cmd)}\nError: {result.stderr}")

    def _verify_operation(self, operation: str, success: bool, result: Any, verification_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Return standardized verification result for all Azure operations.

        Args:
            operation: Operation name (e.g., "create_work_item", "update_work_item")
            success: Whether the operation succeeded
            result: The operation result data
            verification_data: Additional verification details

        Returns:
            Dict with keys: success, operation, result, verification
        """
        return {
            "success": success,
            "operation": operation,
            "result": result,
            "verification": verification_data
        }

    # Work Items

    def query_work_items(self, wiql: str) -> List[Dict]:
        """Query work items using WIQL"""
        cmd = ['az', 'boards', 'query', '--wiql', wiql]
        return self._run_command(cmd)

    def get_work_item(self, work_item_id: int) -> Dict:
        """Get work item by ID"""
        cmd = ['az', 'boards', 'work-item', 'show', '--id', str(work_item_id)]
        return self._run_command(cmd)

    def verify_work_item_created(self, work_item_id: int, expected_title: Optional[str] = None) -> Dict[str, Any]:
        """
        Verify a work item was successfully created.

        Args:
            work_item_id: Work item ID to verify
            expected_title: Optional title to match

        Returns:
            Verification dict with success, operation, result, and verification data
        """
        try:
            work_item = self.get_work_item(work_item_id)

            verification_data = {
                "work_item_id": work_item_id,
                "exists": True,
                "title": work_item.get("fields", {}).get("System.Title"),
                "state": work_item.get("fields", {}).get("System.State"),
                "type": work_item.get("fields", {}).get("System.WorkItemType"),
            }

            # Check if title matches if expected
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

    def verify_work_item_updated(self, work_item_id: int, expected_fields: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify a work item was successfully updated with expected field values.

        Args:
            work_item_id: Work item ID to verify
            expected_fields: Dict of field names and expected values
                            Example: {"System.State": "Done", "System.IterationPath": "Project\\Sprint 1"}

        Returns:
            Verification dict with success, operation, result, and verification data
        """
        try:
            work_item = self.get_work_item(work_item_id)
            fields = work_item.get("fields", {})

            verification_data = {
                "work_item_id": work_item_id,
                "exists": True,
                "fields_verified": {},
                "all_fields_match": True
            }

            # Check each expected field
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
        verify: bool = False
    ) -> Dict:
        """
        Create a work item using two-step process for reliability.

        LEARNING: The --iteration parameter is unreliable in work-item create.
        Instead, we create the work item first, then update it with the iteration path.

        Iteration path format: "ProjectName\\SprintName" (simplified, no \\Iteration\\)
        Example: "Keychain Gateway\\Sprint 4"

        Args:
            work_item_type: Type of work item (Task, Bug, Feature, etc.)
            title: Work item title
            description: Work item description
            assigned_to: User to assign to
            area: Area path
            iteration: Iteration path (simplified format)
            fields: Additional fields as dict
            verify: If True, return verification dict instead of raw result

        Returns:
            If verify=False: Raw work item dict
            If verify=True: Verification dict with success, operation, result, verification
        """
        # Step 1: Create work item without iteration
        cmd = [
            'az', 'boards', 'work-item', 'create',
            '--type', work_item_type,
            '--title', title
        ]

        if description:
            cmd.extend(['--description', description])
        if assigned_to:
            cmd.extend(['--assigned-to', assigned_to])
        if area:
            cmd.extend(['--area', area])

        # Prepare fields - include markdown format if description provided
        all_fields = fields.copy() if fields else {}
        if description:
            # Set description format to Markdown for proper rendering
            all_fields['System.DescriptionFormat'] = 'Markdown'

        if all_fields:
            field_args = [f"{k}={v}" for k, v in all_fields.items()]
            cmd.extend(['--fields'] + field_args)

        result = self._run_command(cmd)

        # Step 2: If iteration specified, update the work item
        if iteration:
            work_item_id = result.get('id')
            if work_item_id:
                self.update_work_item(
                    work_item_id=work_item_id,
                    fields={"System.IterationPath": iteration}
                )
                # Refresh result to include iteration
                result = self.get_work_item(work_item_id)

        # Step 3: Verify if requested
        if verify:
            work_item_id = result.get('id')
            if work_item_id:
                expected_fields = {}
                if iteration:
                    expected_fields["System.IterationPath"] = iteration

                verification = self.verify_work_item_created(work_item_id, expected_title=title)

                # Also verify iteration if specified
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
        Update a work item.

        Args:
            work_item_id: Work item ID to update
            state: New state
            assigned_to: User to assign to
            fields: Additional fields to update
            verify: If True, return verification dict instead of raw result

        Returns:
            If verify=False: Raw work item dict
            If verify=True: Verification dict with success, operation, result, verification
        """
        cmd = ['az', 'boards', 'work-item', 'update', '--id', str(work_item_id)]

        if state:
            cmd.extend(['--state', state])
        if assigned_to:
            cmd.extend(['--assigned-to', assigned_to])
        if fields:
            field_args = [f"{k}={v}" for k, v in fields.items()]
            cmd.extend(['--fields'] + field_args)

        result = self._run_command(cmd)

        # Verify if requested
        if verify:
            expected_fields = {}
            if state:
                expected_fields["System.State"] = state
            if fields:
                expected_fields.update(fields)

            if expected_fields:
                return self.verify_work_item_updated(work_item_id, expected_fields)
            else:
                # No fields to verify, just confirm it exists
                return self.verify_work_item_created(work_item_id)

        return result

    def add_comment(self, work_item_id: int, comment: str) -> Dict:
        """Add comment to work item"""
        cmd = [
            'az', 'boards', 'work-item', 'comment', 'add',
            '--id', str(work_item_id),
            '--comment', comment
        ]
        return self._run_command(cmd)

    def link_work_items(self, source_id: int, target_id: int, relation_type: str) -> Dict:
        """Link two work items"""
        cmd = [
            'az', 'boards', 'work-item', 'relation', 'add',
            '--id', str(source_id),
            '--relation-type', relation_type,
            '--target-id', str(target_id)
        ]
        return self._run_command(cmd)

    def add_attachment(self, work_item_id: int, file_path: str, comment: Optional[str] = None) -> Dict:
        """
        Add an attachment to a work item.

        Args:
            work_item_id: Work item ID
            file_path: Path to file to attach
            comment: Optional comment for the attachment

        Returns:
            Attachment result dict
        """
        cmd = [
            'az', 'boards', 'work-item', 'relation', 'add',
            '--id', str(work_item_id),
            '--relation-type', 'AttachedFile',
            '--url', file_path
        ]

        if comment:
            cmd.extend(['--attributes', f'comment={comment}'])

        return self._run_command(cmd)

    # Pull Requests

    def create_pull_request(
        self,
        source_branch: str,
        title: str,
        description: str,
        work_item_ids: Optional[List[int]] = None,
        reviewers: Optional[List[str]] = None
    ) -> Dict:
        """Create a pull request"""
        cmd = [
            'az', 'repos', 'pr', 'create',
            '--source-branch', source_branch,
            '--target-branch', 'main',
            '--title', title,
            '--description', description
        ]

        if work_item_ids:
            cmd.extend(['--work-items'] + [str(wid) for wid in work_item_ids])
        if reviewers:
            cmd.extend(['--reviewers'] + reviewers)

        return self._run_command(cmd)

    def approve_pull_request(self, pr_id: int) -> Dict:
        """Approve a pull request"""
        cmd = [
            'az', 'repos', 'pr', 'set-vote',
            '--id', str(pr_id),
            '--vote', 'approve'
        ]
        return self._run_command(cmd)

    # Pipelines

    def trigger_pipeline(
        self,
        pipeline_id: int,
        branch: str,
        variables: Optional[Dict[str, str]] = None
    ) -> Dict:
        """Trigger a pipeline run"""
        cmd = [
            'az', 'pipelines', 'run',
            '--id', str(pipeline_id),
            '--branch', branch
        ]

        if variables:
            for key, value in variables.items():
                cmd.extend(['--variables', f"{key}={value}"])

        return self._run_command(cmd)

    def get_pipeline_run(self, run_id: int) -> Dict:
        """Get pipeline run details"""
        cmd = ['az', 'pipelines', 'runs', 'show', '--id', str(run_id)]
        return self._run_command(cmd)

    # Iterations (Sprints)

    def create_iteration(
        self,
        name: str,
        start_date: Optional[str] = None,
        finish_date: Optional[str] = None,
        project: Optional[str] = None
    ) -> Dict:
        """
        Create a new iteration/sprint.

        Args:
            name: Sprint name (e.g., "Sprint 9")
            start_date: Start date in YYYY-MM-DD format (optional)
            finish_date: Finish date in YYYY-MM-DD format (optional)
            project: Project name (optional if default configured)

        Returns:
            Created iteration details
        """
        if not project:
            project = self._config.get('project', '')

        # Build the iteration path
        path = f"{project}\\Iteration\\{name}"

        cmd = ['az', 'boards', 'iteration', 'project', 'create', '--name', name, '--path', path]

        if start_date:
            cmd.extend(['--start-date', start_date])
        if finish_date:
            cmd.extend(['--finish-date', finish_date])
        if project:
            cmd.extend(['--project', project])

        return self._run_command(cmd)

    def list_iterations(self, project: Optional[str] = None) -> List[Dict]:
        """
        List all iterations/sprints.

        Args:
            project: Project name (optional if default configured)
        """
        cmd = ['az', 'boards', 'iteration', 'project', 'list']
        if project:
            cmd.extend(['--project', project])
        return self._run_command(cmd)

    def update_iteration(
        self,
        path: str,
        start_date: Optional[str] = None,
        finish_date: Optional[str] = None,
        project: Optional[str] = None
    ) -> Dict:
        """
        Update iteration dates.

        LEARNING: Use --path parameter with FULL path including \\Iteration\\
        Example: "\\Keychain Gateway\\Iteration\\Sprint 4"

        Args:
            path: Full iteration path (e.g., "\\ProjectName\\Iteration\\SprintName")
            start_date: Start date in YYYY-MM-DD format
            finish_date: Finish date in YYYY-MM-DD format
            project: Project name (optional if default configured)
        """
        cmd = ['az', 'boards', 'iteration', 'project', 'update', '--path', path]
        if start_date:
            cmd.extend(['--start-date', start_date])
        if finish_date:
            cmd.extend(['--finish-date', finish_date])
        if project:
            cmd.extend(['--project', project])
        return self._run_command(cmd)

    def create_sprint_work_items_batch(
        self,
        sprint_name: str,
        work_items: List[Dict[str, Any]],
        project_name: Optional[str] = None
    ) -> List[Dict]:
        """
        Create multiple work items for a sprint efficiently.

        LEARNING: Batch creation is more reliable than individual calls.

        Args:
            sprint_name: Sprint name (e.g., "Sprint 4")
            work_items: List of work item dicts with keys: type, title, description, fields
            project_name: Project name for iteration path (uses config if not provided)

        Returns:
            List of created work item results

        Example:
            work_items = [
                {
                    "type": "Task",
                    "title": "WI-SEC-801: Fix Auth Bypass",
                    "description": "Fix auth middleware",
                    "fields": {"Microsoft.VSTS.Scheduling.StoryPoints": 3}
                }
            ]
            results = azure_cli.create_sprint_work_items_batch("Sprint 4", work_items)
        """
        if not project_name:
            project_name = self._config.get('project', '')

        # Build simplified iteration path for work items
        iteration_path = f"{project_name}\\{sprint_name}"

        results = []
        for item in work_items:
            result = self.create_work_item(
                work_item_type=item['type'],
                title=item['title'],
                description=item.get('description', ''),
                iteration=iteration_path,
                fields=item.get('fields')
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
        Format: "ProjectName\\\\SprintName" (simplified path in queries)

        Args:
            sprint_name: Sprint name (e.g., "Sprint 4")
            project_name: Project name (uses config if not provided)
            include_fields: Additional fields to include (default: Id, Title, State, StoryPoints)

        Returns:
            List of work items
        """
        if not project_name:
            project_name = self._config.get('project', '')

        # WIQL requires double backslashes for escaping
        iteration_path = f"{project_name}\\\\{sprint_name}"

        # Default fields
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

    def _get_auth_token(self) -> str:
        """
        Get Azure DevOps PAT token from az devops configure.

        Returns:
            Personal Access Token
        """
        # Try to get token from environment or az account
        result = subprocess.run(
            ['az', 'account', 'get-access-token', '--resource', '499b84ac-1321-427f-aa17-267ca6975798'],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            token_data = json.loads(result.stdout)
            return token_data.get('accessToken', '')

        # Fallback: Check environment variable
        import os
        return os.environ.get('AZURE_DEVOPS_EXT_PAT', '')

    def _get_rest_api_headers(self) -> Dict[str, str]:
        """Get headers for Azure DevOps REST API calls."""
        token = self._get_auth_token()
        if not token:
            raise Exception("No Azure DevOps authentication token found. Set AZURE_DEVOPS_EXT_PAT environment variable.")

        auth = base64.b64encode(f":{token}".encode()).decode()
        return {
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/json"
        }

    def attach_file_to_work_item(
        self,
        work_item_id: int,
        file_path: Path,
        comment: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Attach a file to a work item using Azure DevOps REST API.

        This solves the limitation that Azure CLI doesn't support file attachments.

        Args:
            work_item_id: Work item ID to attach file to
            file_path: Path to file to attach
            comment: Optional comment for the attachment

        Returns:
            Dict with attachment info

        Raises:
            Exception: If file doesn't exist or upload fails

        Example:
            result = azure_cli.attach_file_to_work_item(
                work_item_id=771,
                file_path=Path("docs/work_items/WI-771-spec.md"),
                comment="Specification document"
            )
        """
        if not isinstance(file_path, Path):
            file_path = Path(file_path)

        if not file_path.exists():
            raise Exception(f"File not found: {file_path}")

        # Get organization and project from config
        org_url = self._config.get('defaults.organization', '')
        project = self._config.get('defaults.project', '')

        if not org_url or not project:
            raise Exception("Azure DevOps organization and project must be configured")

        # Step 1: Upload file to attachments endpoint
        headers = self._get_rest_api_headers()
        headers["Content-Type"] = "application/octet-stream"

        upload_url = f"{org_url}/_apis/wit/attachments?fileName={file_path.name}&api-version=7.1"

        with open(file_path, 'rb') as f:
            file_content = f.read()

        print(f"📤 Uploading {file_path.name} ({len(file_content)} bytes)...")

        upload_response = requests.post(
            upload_url,
            data=file_content,
            headers=headers
        )

        if upload_response.status_code != 201:
            raise Exception(f"Failed to upload attachment: {upload_response.status_code} {upload_response.text}")

        attachment_data = upload_response.json()
        attachment_url = attachment_data.get('url')

        print(f"✓ Uploaded attachment: {attachment_url}")

        # Step 2: Link attachment to work item
        headers["Content-Type"] = "application/json-patch+json"

        patch_url = f"{org_url}/{project}/_apis/wit/workitems/{work_item_id}?api-version=7.1"

        patch_doc = [
            {
                "op": "add",
                "path": "/relations/-",
                "value": {
                    "rel": "AttachedFile",
                    "url": attachment_url,
                    "attributes": {
                        "comment": comment or f"Attached {file_path.name}"
                    }
                }
            }
        ]

        print(f"🔗 Linking attachment to WI-{work_item_id}...")

        link_response = requests.patch(
            patch_url,
            json=patch_doc,
            headers=headers
        )

        if link_response.status_code not in [200, 201]:
            raise Exception(f"Failed to link attachment: {link_response.status_code} {link_response.text}")

        print(f"✓ Attached {file_path.name} to WI-{work_item_id}")

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
            project = self._config.get('defaults.project', '')
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
            project = self._config.get('defaults.project', '')
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
