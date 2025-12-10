"""
Azure Bulk Operations

Provides batch operations for Azure DevOps to replace bash for-loop patterns.
Solves the issue of bash multi-line loops failing in Claude Code.

Usage:
    from azure_bulk_operations import AzureBulkOps

    bulk = AzureBulkOps()

    # Get multiple work items
    items = bulk.batch_get_work_items([771, 772, 773])

    # Update multiple work items
    results = bulk.batch_update_work_items([
        {"work_item_id": 771, "state": "Closed"},
        {"work_item_id": 772, "state": "Closed"},
    ])

    # Close multiple work items
    results = bulk.batch_close_work_items([771, 772, 773])
"""

from typing import Any, Dict, List, Optional

# Import from canonical skills implementation
from skills.azure_devops.cli_wrapper import AzureCLI


class AzureBulkOps:
    """Batch operations for Azure DevOps work items."""

    def __init__(self):
        """Initialize with Azure CLI wrapper."""
        self.azure = AzureCLI()

    def batch_get_work_items(
        self,
        work_item_ids: List[int],
        show_progress: bool = True
    ) -> Dict[int, Dict]:
        """
        Get multiple work items efficiently using WIQL query.

        Args:
            work_item_ids: List of work item IDs to fetch
            show_progress: Whether to print progress messages

        Returns:
            Dict mapping work item ID to work item data
        """
        if not work_item_ids:
            return {}

        if show_progress:
            print(f"Fetching {len(work_item_ids)} work items...")

        # Build WIQL query for batch fetch
        ids_str = ",".join(str(id) for id in work_item_ids)
        wiql = f"""
            SELECT [System.Id], [System.Title], [System.State],
                   [System.WorkItemType], [System.Description],
                   [System.Tags], [System.IterationPath]
            FROM WorkItems
            WHERE [System.Id] IN ({ids_str})
        """

        try:
            results = self.azure.query_work_items(wiql)

            # Convert list to dict keyed by ID
            work_items = {}
            for item in results:
                work_item_id = item.get('id') or item.get('System.Id')
                work_items[work_item_id] = item

            if show_progress:
                print(f"✓ Fetched {len(work_items)} work items")

            return work_items

        except Exception as e:
            print(f"✗ Error fetching work items: {e}")
            return {}

    def batch_update_work_items(
        self,
        updates: List[Dict[str, Any]],
        verify: bool = True,
        show_progress: bool = True
    ) -> List[Dict]:
        """
        Update multiple work items with verification.

        Args:
            updates: List of dicts with keys: work_item_id, state, fields, etc.
            verify: Whether to verify each update
            show_progress: Whether to print progress messages

        Example:
            updates = [
                {"work_item_id": 771, "state": "Closed"},
                {"work_item_id": 772, "state": "Active", "fields": {"System.Tags": "InProgress"}},
            ]

        Returns:
            List of result dicts with keys: work_item_id, success, result/error
        """
        if not updates:
            return []

        if show_progress:
            print(f"Updating {len(updates)} work items...")

        results = []
        success_count = 0
        fail_count = 0

        for i, update in enumerate(updates, 1):
            work_item_id = update["work_item_id"]

            if show_progress:
                print(f"  [{i}/{len(updates)}] Updating WI-{work_item_id}...", end=" ")

            try:
                # Extract parameters
                state = update.get("state")
                fields = update.get("fields", {})
                assigned_to = update.get("assigned_to")
                description = update.get("description")
                discussion = update.get("discussion")

                # Call Azure CLI wrapper
                result = self.azure.update_work_item(
                    work_item_id=work_item_id,
                    state=state,
                    fields=fields,
                    assigned_to=assigned_to,
                    description=description,
                    discussion=discussion,
                    verify=verify
                )

                results.append({
                    "work_item_id": work_item_id,
                    "success": True,
                    "result": result
                })
                success_count += 1

                if show_progress:
                    print("✓")

            except Exception as e:
                results.append({
                    "work_item_id": work_item_id,
                    "success": False,
                    "error": str(e)
                })
                fail_count += 1

                if show_progress:
                    print(f"✗ {e}")

        if show_progress:
            print(f"\n✓ Updated: {success_count}, ✗ Failed: {fail_count}")

        return results

    def batch_close_work_items(
        self,
        work_item_ids: List[int],
        verify: bool = True,
        show_progress: bool = True
    ) -> List[Dict]:
        """
        Close multiple work items.

        Args:
            work_item_ids: List of work item IDs to close
            verify: Whether to verify each closure
            show_progress: Whether to print progress messages

        Returns:
            List of result dicts
        """
        updates = [
            {"work_item_id": wi_id, "state": "Closed"}
            for wi_id in work_item_ids
        ]

        return self.batch_update_work_items(
            updates=updates,
            verify=verify,
            show_progress=show_progress
        )

    def batch_activate_work_items(
        self,
        work_item_ids: List[int],
        verify: bool = True,
        show_progress: bool = True
    ) -> List[Dict]:
        """
        Activate multiple work items.

        Args:
            work_item_ids: List of work item IDs to activate
            verify: Whether to verify each activation
            show_progress: Whether to print progress messages

        Returns:
            List of result dicts
        """
        updates = [
            {"work_item_id": wi_id, "state": "Active"}
            for wi_id in work_item_ids
        ]

        return self.batch_update_work_items(
            updates=updates,
            verify=verify,
            show_progress=show_progress
        )

    def batch_tag_work_items(
        self,
        work_item_ids: List[int],
        tags: str,
        verify: bool = True,
        show_progress: bool = True
    ) -> List[Dict]:
        """
        Add tags to multiple work items.

        Args:
            work_item_ids: List of work item IDs
            tags: Tags to add (semicolon-separated)
            verify: Whether to verify each update
            show_progress: Whether to print progress messages

        Returns:
            List of result dicts
        """
        updates = [
            {
                "work_item_id": wi_id,
                "fields": {"System.Tags": tags}
            }
            for wi_id in work_item_ids
        ]

        return self.batch_update_work_items(
            updates=updates,
            verify=verify,
            show_progress=show_progress
        )

    def batch_assign_work_items(
        self,
        work_item_ids: List[int],
        assigned_to: str,
        verify: bool = True,
        show_progress: bool = True
    ) -> List[Dict]:
        """
        Assign multiple work items to a user.

        Args:
            work_item_ids: List of work item IDs
            assigned_to: User email or display name
            verify: Whether to verify each assignment
            show_progress: Whether to print progress messages

        Returns:
            List of result dicts
        """
        updates = [
            {
                "work_item_id": wi_id,
                "assigned_to": assigned_to
            }
            for wi_id in work_item_ids
        ]

        return self.batch_update_work_items(
            updates=updates,
            verify=verify,
            show_progress=show_progress
        )

    def query_sprint_work_items(
        self,
        sprint_name: str,
        state: Optional[str] = None
    ) -> Dict[int, Dict]:
        """
        Query all work items in a sprint.

        Args:
            sprint_name: Sprint name (e.g., "Sprint 10")
            state: Optional state filter (e.g., "Active", "Closed")

        Returns:
            Dict mapping work item ID to work item data
        """
        # Get project name from config
        project = self.azure._config.get('defaults.project', 'Keychain Gateway')

        # Build WIQL query
        iteration_path = f"{project}\\\\{sprint_name}"
        wiql = f"""
            SELECT [System.Id], [System.Title], [System.State],
                   [System.WorkItemType], [System.Tags]
            FROM WorkItems
            WHERE [System.IterationPath] = '{iteration_path}'
        """

        if state:
            wiql += f" AND [System.State] = '{state}'"

        try:
            results = self.azure.query_work_items(wiql)

            # Convert to dict
            work_items = {}
            for item in results:
                work_item_id = item.get('id') or item.get('System.Id')
                work_items[work_item_id] = item

            print(f"✓ Found {len(work_items)} work items in {sprint_name}")
            return work_items

        except Exception as e:
            print(f"✗ Error querying sprint: {e}")
            return {}

    def print_work_items_table(
        self,
        work_items: Dict[int, Dict],
        show_description: bool = False
    ) -> None:
        """
        Print work items in a formatted table.

        Args:
            work_items: Dict of work item ID to work item data
            show_description: Whether to include description column
        """
        if not work_items:
            print("No work items to display")
            return

        # Calculate column widths
        id_width = max(len(str(wi_id)) for wi_id in work_items.keys())
        id_width = max(id_width, 2)  # Minimum width for "ID"

        # Extract fields from work items
        items_data = []
        for wi_id, wi_data in work_items.items():
            fields = wi_data.get('fields', wi_data)
            title = fields.get('System.Title', 'Unknown')
            state = fields.get('System.State', 'Unknown')
            wi_type = fields.get('System.WorkItemType', 'Unknown')

            items_data.append({
                'id': wi_id,
                'title': title,
                'state': state,
                'type': wi_type
            })

        # Calculate column widths
        title_width = max(len(item['title']) for item in items_data)
        title_width = min(title_width, 50)  # Cap at 50 chars

        state_width = max(len(item['state']) for item in items_data)
        state_width = max(state_width, 5)  # Minimum for "State"

        type_width = max(len(item['type']) for item in items_data)
        type_width = max(type_width, 4)  # Minimum for "Type"

        # Print header
        print()
        print(f"{'ID':<{id_width}} | {'Title':<{title_width}} | {'State':<{state_width}} | {'Type':<{type_width}}")
        print("-" * (id_width + title_width + state_width + type_width + 9))

        # Print rows
        for item in items_data:
            title = item['title'][:title_width]
            print(f"{item['id']:<{id_width}} | {title:<{title_width}} | {item['state']:<{state_width}} | {item['type']:<{type_width}}")

        print()


if __name__ == "__main__":
    # Example usage and CLI interface
    import argparse

    parser = argparse.ArgumentParser(description="Azure DevOps Bulk Operations")
    parser.add_argument("operation", choices=["get", "close", "activate", "tag", "sprint"])
    parser.add_argument("--ids", type=str, help="Comma-separated work item IDs")
    parser.add_argument("--sprint", type=str, help="Sprint name")
    parser.add_argument("--tags", type=str, help="Tags to add (semicolon-separated)")
    parser.add_argument("--state", type=str, help="State filter for sprint query")
    parser.add_argument("--no-verify", action="store_true", help="Skip verification")

    args = parser.parse_args()

    bulk = AzureBulkOps()

    if args.operation == "get":
        if not args.ids:
            print("Error: --ids required for get operation")
            sys.exit(1)

        ids = [int(id.strip()) for id in args.ids.split(",")]
        items = bulk.batch_get_work_items(ids)
        bulk.print_work_items_table(items)

    elif args.operation == "close":
        if not args.ids:
            print("Error: --ids required for close operation")
            sys.exit(1)

        ids = [int(id.strip()) for id in args.ids.split(",")]
        results = bulk.batch_close_work_items(ids, verify=not args.no_verify)

        success = sum(1 for r in results if r["success"])
        print(f"\nClosed {success}/{len(ids)} work items")

    elif args.operation == "activate":
        if not args.ids:
            print("Error: --ids required for activate operation")
            sys.exit(1)

        ids = [int(id.strip()) for id in args.ids.split(",")]
        results = bulk.batch_activate_work_items(ids, verify=not args.no_verify)

        success = sum(1 for r in results if r["success"])
        print(f"\nActivated {success}/{len(ids)} work items")

    elif args.operation == "tag":
        if not args.ids or not args.tags:
            print("Error: --ids and --tags required for tag operation")
            sys.exit(1)

        ids = [int(id.strip()) for id in args.ids.split(",")]
        results = bulk.batch_tag_work_items(ids, args.tags, verify=not args.no_verify)

        success = sum(1 for r in results if r["success"])
        print(f"\nTagged {success}/{len(ids)} work items")

    elif args.operation == "sprint":
        if not args.sprint:
            print("Error: --sprint required for sprint operation")
            sys.exit(1)

        items = bulk.query_sprint_work_items(args.sprint, state=args.state)
        bulk.print_work_items_table(items)
