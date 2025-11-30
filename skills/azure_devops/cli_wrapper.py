"""
Azure CLI Wrapper for TAID.

Battle-tested patterns for Azure DevOps operations.

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
from pathlib import Path
from typing import Any, Dict, List, Optional

# Optional requests import for file attachments
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class AzureCLI:
    """Wrapper for Azure CLI DevOps operations."""

    def __init__(self):
        self._config = self._ensure_configured()

    def _ensure_configured(self) -> Dict[str, str]:
        """Verify Azure CLI is configured and return config."""
        result = subprocess.run(
            ['az', 'devops', 'configure', '--list'],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            raise Exception("Azure CLI not configured. Run: az devops configure --defaults organization=<url> project=<name>")

        config = {}
        for line in result.stdout.strip().split('\n'):
            if '=' in line:
                key, value = line.split('=', 1)
                config[key.strip()] = value.strip()
        return config

    def _run_command(self, cmd: List[str]) -> Dict[str, Any]:
        """Execute Azure CLI command and return JSON result."""
        if '--output' not in cmd and '-o' not in cmd:
            cmd.extend(['--output', 'json'])

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            return json.loads(result.stdout) if result.stdout else {}
        else:
            raise Exception(f"Command failed: {' '.join(cmd)}\nError: {result.stderr}")

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
        """Query work items using WIQL."""
        cmd = ['az', 'boards', 'query', '--wiql', wiql]
        return self._run_command(cmd)

    def get_work_item(self, work_item_id: int) -> Dict:
        """Get work item by ID."""
        cmd = ['az', 'boards', 'work-item', 'show', '--id', str(work_item_id)]
        return self._run_command(cmd)

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
        verify: bool = False
    ) -> Dict:
        """
        Create a work item using two-step process for reliability.

        LEARNING: The --iteration parameter is unreliable in work-item create.
        Instead, we create the work item first, then update it with the iteration path.

        Iteration path format: "ProjectName\\SprintName" (simplified, no \\Iteration\\)
        Example: "My Project\\Sprint 4"
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
        if fields:
            field_args = [f"{k}={v}" for k, v in fields.items()]
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
                result = self.get_work_item(work_item_id)

        # Step 3: Verify if requested
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
        """Update a work item."""
        cmd = ['az', 'boards', 'work-item', 'update', '--id', str(work_item_id)]

        if state:
            cmd.extend(['--state', state])
        if assigned_to:
            cmd.extend(['--assigned-to', assigned_to])
        if fields:
            field_args = [f"{k}={v}" for k, v in fields.items()]
            cmd.extend(['--fields'] + field_args)

        result = self._run_command(cmd)

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
        """Add comment to work item."""
        cmd = [
            'az', 'boards', 'work-item', 'comment', 'add',
            '--id', str(work_item_id),
            '--comment', comment
        ]
        return self._run_command(cmd)

    def link_work_items(self, source_id: int, target_id: int, relation_type: str) -> Dict:
        """Link two work items."""
        cmd = [
            'az', 'boards', 'work-item', 'relation', 'add',
            '--id', str(source_id),
            '--relation-type', relation_type,
            '--target-id', str(target_id)
        ]
        return self._run_command(cmd)

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
        """
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
                    work_item = self.get_work_item(work_item_id)
                    return {
                        "id": work_item_id,
                        "created": False,
                        "existing": True,
                        "work_item": work_item
                    }
            except Exception:
                pass  # Continue to create

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

    def create_pull_request(
        self,
        source_branch: str,
        title: str,
        description: str,
        work_item_ids: Optional[List[int]] = None,
        reviewers: Optional[List[str]] = None
    ) -> Dict:
        """Create a pull request."""
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
        """Approve a pull request."""
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
        """Trigger a pipeline run."""
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
        """Get pipeline run details."""
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
        """Create a new iteration/sprint."""
        if not project:
            project = self._config.get('project', '')

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
        """List all iterations/sprints."""
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

    # File Attachments (requires requests library)

    def _get_auth_token(self) -> str:
        """Get Azure DevOps access token."""
        import os

        result = subprocess.run(
            ['az', 'account', 'get-access-token', '--resource', '499b84ac-1321-427f-aa17-267ca6975798'],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            token_data = json.loads(result.stdout)
            return token_data.get('accessToken', '')

        return os.environ.get('AZURE_DEVOPS_EXT_PAT', '')

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
            "attachment_url": attachment_url,
            "success": True
        }
