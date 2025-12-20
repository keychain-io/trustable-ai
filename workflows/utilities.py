"""
Workflow utility functions for sprint analysis and verification.

Provides reusable utility functions that can be:
1. Called from workflows for analysis and verification
2. Used by CI/CD pipelines for monitoring
3. Tested independently as unit tests
4. Maintained in one place instead of duplicated across workflows

This module extracts functionality previously implemented as ad-hoc /tmp scripts,
providing production-quality implementations with proper error handling and testing.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta


def analyze_sprint(
    adapter,
    sprint_name: str,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Analyze sprint work items and generate statistics.

    This function provides comprehensive sprint analysis including work item counts,
    state distributions, story point tracking, and team member assignments.

    Args:
        adapter: Work tracking adapter instance
        sprint_name: Sprint iteration name (e.g., "Sprint 5")
        config: Optional configuration dict with work_tracking settings

    Returns:
        dict: {
            'sprint_name': str,
            'total_items': int,
            'by_state': {state: count},
            'by_type': {type: count},
            'by_assignee': {assignee: count},
            'story_points': {
                'total': int,
                'completed': int,
                'in_progress': int,
                'not_started': int
            },
            'completion_rate': float,  # Percentage of items in terminal states
            'velocity': float,  # Story points completed
            'errors': list  # List of error messages if any
        }

    Example:
        >>> adapter = get_adapter()
        >>> stats = analyze_sprint(adapter, "Sprint 6")
        >>> print(f"Completion: {stats['completion_rate']:.1f}%")
        >>> print(f"Velocity: {stats['velocity']} points")
    """
    errors = []
    config = config or {}
    work_tracking_config = config.get('work_tracking', {})

    # Initialize result structure
    result = {
        'sprint_name': sprint_name,
        'total_items': 0,
        'by_state': {},
        'by_type': {},
        'by_assignee': {},
        'story_points': {
            'total': 0,
            'completed': 0,
            'in_progress': 0,
            'not_started': 0
        },
        'completion_rate': 0.0,
        'velocity': 0.0,
        'errors': errors
    }

    try:
        # Query all work items in the sprint
        sprint_items = adapter.query_sprint_work_items(sprint_name)
        result['total_items'] = len(sprint_items)

        if result['total_items'] == 0:
            return result

        # Get story points field name from config
        story_points_field = work_tracking_config.get('custom_fields', {}).get('story_points')

        # Define terminal states (completed/closed)
        terminal_states = ['Done', 'Closed', 'Completed', 'Resolved']
        in_progress_states = ['Active', 'In Progress', 'Doing', 'Committed']

        # Analyze each work item
        for item in sprint_items:
            item_state = item.get('state', 'Unknown')
            item_type = item.get('type', item.get('fields', {}).get('System.WorkItemType', 'Unknown'))
            assignee = item.get('assigned_to', 'Unassigned')

            # Track by state
            result['by_state'][item_state] = result['by_state'].get(item_state, 0) + 1

            # Track by type
            result['by_type'][item_type] = result['by_type'].get(item_type, 0) + 1

            # Track by assignee
            result['by_assignee'][assignee] = result['by_assignee'].get(assignee, 0) + 1

            # Track story points
            if story_points_field:
                # Get story points from item
                points = item.get('fields', {}).get(story_points_field)
                if points is None:
                    points = item.get('story_points', 0)
                points = points or 0

                result['story_points']['total'] += points

                # Categorize points by state
                if item_state in terminal_states:
                    result['story_points']['completed'] += points
                elif item_state in in_progress_states:
                    result['story_points']['in_progress'] += points
                else:
                    result['story_points']['not_started'] += points

        # Calculate completion rate
        completed_count = sum(
            result['by_state'].get(state, 0)
            for state in terminal_states
        )
        if result['total_items'] > 0:
            result['completion_rate'] = (completed_count / result['total_items']) * 100

        # Calculate velocity (completed story points)
        result['velocity'] = result['story_points']['completed']

    except Exception as e:
        errors.append(f"Sprint analysis failed: {str(e)}")

    return result


def verify_work_item_states(
    adapter,
    work_items: List[Dict[str, Any]],
    terminal_states: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Verify work item states against external source of truth.

    Implements the "External Source of Truth" pattern from VISION.md. AI agents
    often claim work is complete when it isn't. This verification function catches
    divergence immediately by querying the work tracking adapter directly.

    Args:
        adapter: Work tracking adapter instance (external source of truth)
        work_items: List of work item dicts with 'id', 'state', 'title' keys
        terminal_states: Optional list of states considered "complete"
                        (default: ['Done', 'Closed', 'Completed', 'Resolved'])

    Returns:
        dict: {
            'verified_count': int,  # Number of items successfully verified
            'divergence_count': int,  # Number of divergences detected
            'divergences': [  # List of detected divergences
                {
                    'id': str,
                    'title': str,
                    'claimed_state': str,
                    'actual_state': str,
                    'severity': str,  # 'ERROR' or 'WARNING'
                    'message': str
                }
            ],
            'summary': {
                'errors': int,  # Count of ERROR divergences
                'warnings': int  # Count of WARNING divergences
            },
            'errors': list  # List of error messages if verification fails
        }

    Example:
        >>> recent_items = [
        ...     {'id': 'TASK-001', 'state': 'Done', 'title': 'Implement auth'},
        ...     {'id': 'TASK-002', 'state': 'Active', 'title': 'Add tests'}
        ... ]
        >>> result = verify_work_item_states(adapter, recent_items)
        >>> if result['divergence_count'] > 0:
        ...     print(f"⚠️ {result['divergence_count']} divergence(s) detected")
    """
    errors = []
    terminal_states = terminal_states or ['Done', 'Closed', 'Completed', 'Resolved']

    # Initialize result structure
    result = {
        'verified_count': 0,
        'divergence_count': 0,
        'divergences': [],
        'summary': {
            'errors': 0,
            'warnings': 0
        },
        'errors': errors
    }

    try:
        # Build map of actual current states from adapter (external truth)
        actual_state_map = {}

        for item in work_items:
            item_id = item.get('id')
            if not item_id:
                errors.append("Work item missing 'id' field")
                continue

            try:
                # Query adapter for current state (external source of truth)
                current_item = adapter.get_work_item(item_id)

                if current_item:
                    # Extract state from either flat or nested structure
                    actual_state = current_item.get('state')
                    if not actual_state:
                        actual_state = current_item.get('fields', {}).get('System.State')
                    actual_state_map[item_id] = actual_state or 'UNKNOWN'
                    result['verified_count'] += 1
                else:
                    actual_state_map[item_id] = 'NOT_FOUND'

            except Exception as e:
                errors.append(f"Failed to verify work item {item_id}: {str(e)}")
                actual_state_map[item_id] = 'ERROR'

        # Detect state divergences
        for item in work_items:
            item_id = item.get('id')
            if not item_id:
                continue

            item_title = item.get('title', 'Unknown')
            claimed_state = item.get('state', 'Unknown')
            actual_state = actual_state_map.get(item_id, 'NOT_FOUND')

            # Skip if verification failed
            if actual_state == 'ERROR':
                continue

            # Divergence Type 1: Work item doesn't exist in adapter
            if actual_state == 'NOT_FOUND':
                result['divergences'].append({
                    'id': item_id,
                    'title': item_title,
                    'claimed_state': claimed_state,
                    'actual_state': actual_state,
                    'severity': 'ERROR',
                    'message': f"Work item not found in {adapter.platform}"
                })
                result['divergence_count'] += 1
                result['summary']['errors'] += 1
                continue

            # Divergence Type 2: Claimed terminal but actually not terminal
            if claimed_state in terminal_states and actual_state not in terminal_states:
                result['divergences'].append({
                    'id': item_id,
                    'title': item_title,
                    'claimed_state': claimed_state,
                    'actual_state': actual_state,
                    'severity': 'WARNING',
                    'message': f"State mismatch: claimed '{claimed_state}' but adapter shows '{actual_state}'"
                })
                result['divergence_count'] += 1
                result['summary']['warnings'] += 1

            # Divergence Type 3: State mismatch (any difference)
            elif claimed_state != actual_state:
                result['divergences'].append({
                    'id': item_id,
                    'title': item_title,
                    'claimed_state': claimed_state,
                    'actual_state': actual_state,
                    'severity': 'WARNING',
                    'message': f"State mismatch: claimed '{claimed_state}' but adapter shows '{actual_state}'"
                })
                result['divergence_count'] += 1
                result['summary']['warnings'] += 1

    except Exception as e:
        errors.append(f"Work item state verification failed: {str(e)}")

    return result


def get_recent_activity(
    adapter,
    sprint_name: str,
    hours: int = 24,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Get work items with recent activity in a sprint.

    Filters sprint work items to those updated within the specified time window.
    Useful for daily standup reports and activity tracking.

    Args:
        adapter: Work tracking adapter instance
        sprint_name: Sprint iteration name (e.g., "Sprint 5")
        hours: Number of hours to look back (default: 24)
        config: Optional configuration dict

    Returns:
        dict: {
            'sprint_name': str,
            'hours': int,
            'total_items': int,  # Total items in sprint
            'recent_items': [  # Items updated in time window
                {
                    'id': str,
                    'title': str,
                    'state': str,
                    'type': str,
                    'updated_at': str,
                    'assigned_to': str
                }
            ],
            'recent_count': int,
            'errors': list
        }

    Example:
        >>> activity = get_recent_activity(adapter, "Sprint 6", hours=24)
        >>> print(f"Found {activity['recent_count']} items updated in last 24h")
    """
    errors = []
    config = config or {}

    result = {
        'sprint_name': sprint_name,
        'hours': hours,
        'total_items': 0,
        'recent_items': [],
        'recent_count': 0,
        'errors': errors
    }

    try:
        # Get all work items from the sprint
        sprint_items = adapter.query_sprint_work_items(sprint_name)
        result['total_items'] = len(sprint_items)

        # Calculate cutoff time
        cutoff_time = datetime.now() - timedelta(hours=hours)

        # Filter for items updated since cutoff
        for item in sprint_items:
            # Get updated_at timestamp
            updated_at_str = item.get('updated_at')
            if not updated_at_str:
                updated_at_str = item.get('fields', {}).get('System.ChangedDate')

            if not updated_at_str:
                # Skip items without timestamp
                continue

            try:
                # Parse timestamp (handle ISO format)
                if updated_at_str.endswith('Z'):
                    updated_at_str = updated_at_str[:-1] + '+00:00'
                updated_at = datetime.fromisoformat(updated_at_str.replace('Z', '+00:00'))

                # Remove timezone info for comparison if present
                if updated_at.tzinfo:
                    updated_at = updated_at.replace(tzinfo=None)

                # Check if updated recently
                if updated_at >= cutoff_time:
                    result['recent_items'].append({
                        'id': item.get('id'),
                        'title': item.get('title', item.get('fields', {}).get('System.Title', 'Unknown')),
                        'state': item.get('state', item.get('fields', {}).get('System.State', 'Unknown')),
                        'type': item.get('type', item.get('fields', {}).get('System.WorkItemType', 'Unknown')),
                        'updated_at': updated_at_str,
                        'assigned_to': item.get('assigned_to', 'Unassigned')
                    })

            except (ValueError, AttributeError) as e:
                errors.append(f"Failed to parse timestamp for item {item.get('id')}: {str(e)}")

        result['recent_count'] = len(result['recent_items'])

    except Exception as e:
        errors.append(f"Failed to get recent activity: {str(e)}")

    return result


def identify_blockers(
    adapter,
    sprint_name: str,
    stale_threshold_days: int = 3,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Identify blocked work items in a sprint.

    Detects blockers through multiple signals:
    - Items with "Blocked" state
    - Items with "blocker" tag
    - Items with no updates in N+ days (stale)

    Args:
        adapter: Work tracking adapter instance
        sprint_name: Sprint iteration name (e.g., "Sprint 5")
        stale_threshold_days: Days without updates to consider stale (default: 3)
        config: Optional configuration dict

    Returns:
        dict: {
            'sprint_name': str,
            'total_blockers': int,
            'blocked_items': [  # Items in Blocked state
                {'id': str, 'title': str, 'reason': str}
            ],
            'tagged_items': [  # Items tagged as blocker
                {'id': str, 'title': str, 'tags': list}
            ],
            'stale_items': [  # Items with no updates in N+ days
                {'id': str, 'title': str, 'days_stale': int, 'last_update': str}
            ],
            'impact': {
                'affected_people': int,
                'story_points_at_risk': int
            },
            'errors': list
        }

    Example:
        >>> blockers = identify_blockers(adapter, "Sprint 6", stale_threshold_days=3)
        >>> if blockers['total_blockers'] > 0:
        ...     print(f"⚠️ {blockers['total_blockers']} blocker(s) detected")
        ...     print(f"Story points at risk: {blockers['impact']['story_points_at_risk']}")
    """
    errors = []
    config = config or {}
    work_tracking_config = config.get('work_tracking', {})

    result = {
        'sprint_name': sprint_name,
        'total_blockers': 0,
        'blocked_items': [],
        'tagged_items': [],
        'stale_items': [],
        'impact': {
            'affected_people': 0,
            'story_points_at_risk': 0
        },
        'errors': errors
    }

    try:
        # Get all work items from the sprint
        sprint_items = adapter.query_sprint_work_items(sprint_name)

        # Get story points field name from config
        story_points_field = work_tracking_config.get('custom_fields', {}).get('story_points')

        # Calculate stale cutoff time
        stale_cutoff = datetime.now() - timedelta(days=stale_threshold_days)

        # Track affected assignees for impact calculation
        affected_assignees = set()

        # Analyze each work item for blocker signals
        for item in sprint_items:
            item_id = item.get('id')
            item_title = item.get('title', item.get('fields', {}).get('System.Title', 'Unknown'))
            item_state = item.get('state', item.get('fields', {}).get('System.State', 'Unknown'))
            assignee = item.get('assigned_to', 'Unassigned')

            # Get story points
            points = 0
            if story_points_field:
                points = item.get('fields', {}).get(story_points_field)
                if points is None:
                    points = item.get('story_points', 0)
                points = points or 0

            # Signal 1: Blocked state
            if item_state == 'Blocked':
                result['blocked_items'].append({
                    'id': item_id,
                    'title': item_title,
                    'reason': 'State is Blocked',
                    'assigned_to': assignee,
                    'story_points': points
                })
                result['total_blockers'] += 1
                result['impact']['story_points_at_risk'] += points
                if assignee != 'Unassigned':
                    affected_assignees.add(assignee)

            # Signal 2: Tagged as blocker
            tags = item.get('tags', item.get('fields', {}).get('System.Tags', ''))
            if isinstance(tags, str):
                tags = [t.strip() for t in tags.split(';') if t.strip()]
            if 'blocker' in [t.lower() for t in tags]:
                result['tagged_items'].append({
                    'id': item_id,
                    'title': item_title,
                    'tags': tags,
                    'assigned_to': assignee,
                    'story_points': points
                })
                if item_state != 'Blocked':  # Don't double-count
                    result['total_blockers'] += 1
                    result['impact']['story_points_at_risk'] += points
                    if assignee != 'Unassigned':
                        affected_assignees.add(assignee)

            # Signal 3: Stale (no updates in N+ days)
            updated_at_str = item.get('updated_at')
            if not updated_at_str:
                updated_at_str = item.get('fields', {}).get('System.ChangedDate')

            if updated_at_str:
                try:
                    # Parse timestamp
                    if updated_at_str.endswith('Z'):
                        updated_at_str = updated_at_str[:-1] + '+00:00'
                    updated_at = datetime.fromisoformat(updated_at_str.replace('Z', '+00:00'))

                    # Remove timezone info for comparison
                    if updated_at.tzinfo:
                        updated_at = updated_at.replace(tzinfo=None)

                    # Check if stale
                    if updated_at < stale_cutoff and item_state not in ['Done', 'Closed', 'Completed', 'Resolved']:
                        days_stale = (datetime.now() - updated_at).days
                        result['stale_items'].append({
                            'id': item_id,
                            'title': item_title,
                            'days_stale': days_stale,
                            'last_update': updated_at_str,
                            'assigned_to': assignee,
                            'story_points': points
                        })
                        # Only count as blocker if not already counted
                        if item_state != 'Blocked' and 'blocker' not in [t.lower() for t in tags]:
                            result['total_blockers'] += 1
                            result['impact']['story_points_at_risk'] += points
                            if assignee != 'Unassigned':
                                affected_assignees.add(assignee)

                except (ValueError, AttributeError) as e:
                    errors.append(f"Failed to parse timestamp for item {item_id}: {str(e)}")

        # Calculate people impact
        result['impact']['affected_people'] = len(affected_assignees)

    except Exception as e:
        errors.append(f"Failed to identify blockers: {str(e)}")

    return result
