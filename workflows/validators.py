"""
Verification checklist validators for workflows.

Provides reusable validator functions that can be:
1. Called from workflows for verification
2. Used by CI/CD pipelines (trustable-ai workflow verify)
3. Tested independently as unit tests
4. Maintained in one place instead of duplicated across workflows
"""

from typing import Any, Dict, List, Optional


def verify_backlog_grooming(
    adapter,
    epic_id: str,
    created_features: List[Dict[str, Any]],
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Verify backlog grooming Epic decomposition quality.

    Validates:
    - Feature-Task hierarchy (all Features have Tasks)
    - Story point summation (Feature points = sum Task points, Epic points = sum Feature points)
    - Variance within 20% threshold

    Args:
        adapter: Work tracking adapter instance
        epic_id: Epic work item ID (e.g., 'EPIC-001' or 123)
        created_features: List of Feature metadata dicts with {'id', 'title', 'expected_tasks'}
        config: Configuration dict with work_tracking settings

    Returns:
        dict: {
            'passed': bool,  # Overall pass/fail
            'checks': {
                'feature_task_hierarchy': {'passed': bool, 'details': str},
                'story_point_variance': {'passed': bool, 'details': str}
            },
            'errors': list  # List of error messages
        }
    """
    errors = []
    checks = {}

    # Initialize overall pass state
    overall_passed = True

    # Extract configuration
    work_tracking_config = config.get('work_tracking', {})
    task_type = work_tracking_config.get('work_item_types', {}).get('task', 'Task')
    feature_type = work_tracking_config.get('work_item_types', {}).get('feature', 'Feature')
    story_points_field = work_tracking_config.get('custom_fields', {}).get('story_points')

    # Check 1: Feature-Task hierarchy
    childless_features = []
    hierarchy_details = []

    try:
        for feature_info in created_features:
            feature_id = feature_info.get('id')
            feature_title = feature_info.get('title', '')
            expected_tasks = feature_info.get('expected_tasks', 0)

            try:
                # Query Tasks under this Feature from adapter (external source of truth)
                feature_tasks = adapter.query_work_items(work_item_type=task_type)

                # Filter for Tasks with this Feature as parent
                # Handle different adapter formats (file-based vs Azure DevOps)
                feature_tasks = [
                    task for task in feature_tasks
                    if task.get('parent_id') == feature_id or
                       task.get('fields', {}).get('System.Parent') == feature_id
                ]

                task_count = len(feature_tasks)

                if task_count == 0:
                    childless_features.append({
                        'id': feature_id,
                        'title': feature_title
                    })
                    overall_passed = False
                    hierarchy_details.append(
                        f"Feature {feature_id} '{feature_title}' has no Tasks"
                    )
                else:
                    hierarchy_details.append(
                        f"Feature {feature_id} has {task_count} Task(s) (expected {expected_tasks})"
                    )

            except Exception as e:
                errors.append(f"Failed to query Tasks for Feature {feature_id}: {str(e)}")
                overall_passed = False

        # Check 2: Verify all Features are linked to parent Epic
        try:
            epic_features = adapter.query_work_items(work_item_type=feature_type)

            # Filter for Features with this Epic as parent
            epic_features = [
                feature for feature in epic_features
                if feature.get('parent_id') == epic_id or
                   feature.get('fields', {}).get('System.Parent') == epic_id
            ]

            expected_feature_count = len(created_features)
            actual_feature_count = len(epic_features)

            if actual_feature_count != expected_feature_count:
                hierarchy_details.append(
                    f"Epic has {actual_feature_count} Features, expected {expected_feature_count}"
                )
                overall_passed = False
            else:
                hierarchy_details.append(
                    f"All {expected_feature_count} Feature(s) linked to Epic"
                )

        except Exception as e:
            errors.append(f"Failed to query Features for Epic {epic_id}: {str(e)}")
            overall_passed = False

        hierarchy_passed = len(childless_features) == 0 and overall_passed
        checks['feature_task_hierarchy'] = {
            'passed': hierarchy_passed,
            'details': '\n'.join(hierarchy_details),
            'childless_features': childless_features
        }

    except Exception as e:
        errors.append(f"Feature-Task hierarchy check failed: {str(e)}")
        overall_passed = False
        checks['feature_task_hierarchy'] = {
            'passed': False,
            'details': f"Check failed with error: {str(e)}",
            'childless_features': []
        }

    # Check 3: Story point variance
    story_point_mismatches = []
    variance_details = []

    if story_points_field:
        try:
            # Verify story point summation within each Feature
            for feature_info in created_features:
                feature_id = feature_info.get('id')
                feature_title = feature_info.get('title', '')

                try:
                    # Get Feature story points from adapter (external source of truth)
                    feature_full = adapter.get_work_item(feature_id)
                    if not feature_full:
                        continue

                    feature_story_points = feature_full.get('fields', {}).get(story_points_field, 0)
                    if feature_story_points is None:
                        feature_story_points = feature_full.get('story_points', 0)
                    feature_story_points = feature_story_points or 0

                    # Query Tasks and sum their story points
                    feature_tasks = adapter.query_work_items(work_item_type=task_type)
                    feature_tasks = [
                        task for task in feature_tasks
                        if task.get('parent_id') == feature_id or
                           task.get('fields', {}).get('System.Parent') == feature_id
                    ]

                    # Sum Task story points
                    task_story_points_sum = 0
                    for task in feature_tasks:
                        task_points = task.get('fields', {}).get(story_points_field, 0)
                        if task_points is None:
                            task_points = task.get('story_points', 0)
                        task_story_points_sum += task_points or 0

                    # Calculate variance
                    if feature_story_points > 0:
                        variance_pct = abs(task_story_points_sum - feature_story_points) / feature_story_points * 100
                    else:
                        variance_pct = 100 if task_story_points_sum > 0 else 0

                    # Check if variance exceeds threshold
                    if variance_pct > 20:
                        story_point_mismatches.append({
                            'id': feature_id,
                            'title': feature_title,
                            'feature_points': feature_story_points,
                            'tasks_sum': task_story_points_sum,
                            'variance_pct': variance_pct
                        })
                        overall_passed = False
                        variance_details.append(
                            f"Feature {feature_id} story point mismatch (variance {variance_pct:.1f}%): "
                            f"Feature: {feature_story_points} pts, Tasks sum: {task_story_points_sum} pts"
                        )
                    else:
                        variance_details.append(
                            f"Feature {feature_id}: {feature_story_points} pts "
                            f"(Tasks sum: {task_story_points_sum} pts, variance: {variance_pct:.1f}%)"
                        )

                except Exception as e:
                    errors.append(f"Could not verify story points for Feature {feature_id}: {str(e)}")

            # Check 4: Verify Epic vs Features story point summation
            try:
                epic_full = adapter.get_work_item(epic_id)
                if epic_full:
                    epic_story_points = epic_full.get('fields', {}).get(story_points_field, 0)
                    if epic_story_points is None:
                        epic_story_points = epic_full.get('story_points', 0)
                    epic_story_points = epic_story_points or 0

                    # Sum Feature story points
                    features_story_points_sum = 0
                    for feature_info in created_features:
                        try:
                            feature_full = adapter.get_work_item(feature_info['id'])
                            if feature_full:
                                feature_points = feature_full.get('fields', {}).get(story_points_field, 0)
                                if feature_points is None:
                                    feature_points = feature_full.get('story_points', 0)
                                features_story_points_sum += feature_points or 0
                        except Exception as e:
                            errors.append(f"Could not get Feature {feature_info['id']} story points: {str(e)}")

                    # Calculate variance
                    if epic_story_points > 0:
                        epic_variance_pct = abs(features_story_points_sum - epic_story_points) / epic_story_points * 100
                    else:
                        epic_variance_pct = 100 if features_story_points_sum > 0 else 0

                    variance_details.append(
                        f"Epic {epic_id}: {epic_story_points} pts, "
                        f"Features sum: {features_story_points_sum} pts, "
                        f"Variance: {epic_variance_pct:.1f}%"
                    )

                    if epic_variance_pct > 20:
                        overall_passed = False
                        variance_details.append(f"Epic story point variance {epic_variance_pct:.1f}% exceeds 20% threshold")

            except Exception as e:
                errors.append(f"Could not verify Epic story points: {str(e)}")

            variance_passed = len(story_point_mismatches) == 0 and overall_passed
            checks['story_point_variance'] = {
                'passed': variance_passed,
                'details': '\n'.join(variance_details),
                'mismatches': story_point_mismatches
            }

        except Exception as e:
            errors.append(f"Story point variance check failed: {str(e)}")
            overall_passed = False
            checks['story_point_variance'] = {
                'passed': False,
                'details': f"Check failed with error: {str(e)}",
                'mismatches': []
            }
    else:
        # Story points field not configured
        checks['story_point_variance'] = {
            'passed': True,
            'details': 'Story points field not configured - skipping variance check',
            'mismatches': []
        }

    return {
        'passed': overall_passed and not errors,
        'checks': checks,
        'errors': errors
    }


def verify_sprint_planning(
    adapter,
    created_items: List[str],
    sprint_number: str,
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Verify sprint planning work item quality.

    Validates:
    - All work items exist in work tracking platform
    - Descriptions >= 500 characters
    - Acceptance criteria >= 3 items
    - Sprint assignments correct

    Args:
        adapter: Work tracking adapter instance
        created_items: List of work item IDs (e.g., ['EPIC-001', 'TASK-002'] or [123, 124])
        sprint_number: Sprint iteration number (e.g., "Sprint 5")
        config: Configuration dict with work_tracking settings

    Returns:
        dict: {
            'passed': bool,  # Overall pass/fail
            'checks': {
                'work_items_exist': {'passed': bool, 'details': str},
                'content_quality': {'passed': bool, 'details': str},
                'sprint_assignments': {'passed': bool, 'details': str}
            },
            'errors': list  # List of error messages
        }
    """
    errors = []
    checks = {}

    # Initialize overall pass state
    overall_passed = True

    # Extract configuration
    work_tracking_config = config.get('work_tracking', {})
    project_name = work_tracking_config.get('project', 'default')

    # Check 1: Work items exist
    verified_items = []
    missing_items = []
    existence_details = []

    try:
        for item_id in created_items:
            try:
                # Query adapter for external source of truth
                work_item = adapter.get_work_item(item_id)

                if work_item and work_item.get('id') == item_id:
                    verified_items.append(item_id)
                    existence_details.append(f"Work Item {item_id} exists")
                else:
                    missing_items.append(item_id)
                    existence_details.append(f"Work Item {item_id} claimed created but doesn't exist")
                    overall_passed = False

            except Exception as e:
                missing_items.append(item_id)
                errors.append(f"Work Item {item_id} verification failed: {str(e)}")
                overall_passed = False

        existence_passed = len(missing_items) == 0
        checks['work_items_exist'] = {
            'passed': existence_passed,
            'details': '\n'.join(existence_details),
            'verified_count': len(verified_items),
            'missing_count': len(missing_items),
            'missing_items': missing_items
        }

    except Exception as e:
        errors.append(f"Work items existence check failed: {str(e)}")
        overall_passed = False
        checks['work_items_exist'] = {
            'passed': False,
            'details': f"Check failed with error: {str(e)}",
            'verified_count': 0,
            'missing_count': len(created_items),
            'missing_items': created_items
        }

    # Check 2: Content quality (description and acceptance criteria)
    quality_issues = []
    quality_details = []

    try:
        import re

        for item_id in verified_items:
            try:
                # Query full work item details
                work_item = adapter.get_work_item(item_id)

                if not work_item:
                    continue  # Already failed in existence check

                fields = work_item.get('fields', {})
                title = fields.get('System.Title', work_item.get('title', f'Work Item {item_id}'))

                # Validate description length (>= 500 characters)
                description = fields.get('System.Description', work_item.get('description', ''))
                # Strip HTML tags for character count
                description_text = re.sub('<[^<]+?>', '', description)
                description_length = len(description_text.strip())

                # Validate acceptance criteria (>= 3 criteria)
                acceptance_criteria = fields.get('Microsoft.VSTS.Common.AcceptanceCriteria', '')
                # Count criteria (lines starting with "- [ ]" or numbered)
                criteria_lines = [
                    line for line in acceptance_criteria.split('\n')
                    if line.strip().startswith('- [ ]') or
                       line.strip().startswith('- [x]') or
                       re.match(r'^\d+\.', line.strip())
                ]
                criteria_count = len(criteria_lines)

                # Check quality thresholds
                item_issues = []
                if description_length < 500:
                    item_issues.append(f"description too short ({description_length} chars, need 500+)")
                if criteria_count < 3:
                    item_issues.append(f"insufficient acceptance criteria ({criteria_count} criteria, need 3+)")

                if item_issues:
                    quality_issues.append({
                        'id': item_id,
                        'title': title,
                        'issues': item_issues
                    })
                    overall_passed = False
                    quality_details.append(f"Work Item {item_id}: {', '.join(item_issues)}")
                else:
                    quality_details.append(
                        f"Work Item {item_id}: Sufficient detail "
                        f"(desc: {description_length} chars, AC: {criteria_count} criteria)"
                    )

            except Exception as e:
                errors.append(f"Work Item {item_id} content quality check failed: {str(e)}")
                overall_passed = False

        quality_passed = len(quality_issues) == 0
        checks['content_quality'] = {
            'passed': quality_passed,
            'details': '\n'.join(quality_details),
            'issues_count': len(quality_issues),
            'quality_issues': quality_issues
        }

    except Exception as e:
        errors.append(f"Content quality check failed: {str(e)}")
        overall_passed = False
        checks['content_quality'] = {
            'passed': False,
            'details': f"Check failed with error: {str(e)}",
            'issues_count': len(verified_items),
            'quality_issues': []
        }

    # Check 3: Sprint assignments
    assignment_issues = []
    assignment_details = []

    try:
        expected_iteration = f"{project_name}\\{sprint_number}"

        for item_id in verified_items:
            try:
                work_item = adapter.get_work_item(item_id)

                if not work_item:
                    continue

                # Get iteration path (handle both formats)
                iteration = work_item.get('fields', {}).get('System.IterationPath')
                if not iteration:
                    iteration = work_item.get('iteration')

                if iteration != expected_iteration:
                    assignment_issues.append({
                        'id': item_id,
                        'expected': expected_iteration,
                        'actual': iteration
                    })
                    overall_passed = False
                    assignment_details.append(
                        f"Work Item {item_id}: Wrong sprint (expected '{expected_iteration}', got '{iteration}')"
                    )
                else:
                    assignment_details.append(f"Work Item {item_id}: Assigned to {sprint_number}")

            except Exception as e:
                errors.append(f"Work Item {item_id} sprint assignment check failed: {str(e)}")
                overall_passed = False

        assignment_passed = len(assignment_issues) == 0
        checks['sprint_assignments'] = {
            'passed': assignment_passed,
            'details': '\n'.join(assignment_details),
            'issues_count': len(assignment_issues),
            'assignment_issues': assignment_issues
        }

    except Exception as e:
        errors.append(f"Sprint assignments check failed: {str(e)}")
        overall_passed = False
        checks['sprint_assignments'] = {
            'passed': False,
            'details': f"Check failed with error: {str(e)}",
            'issues_count': len(verified_items),
            'assignment_issues': []
        }

    return {
        'passed': overall_passed and not errors,
        'checks': checks,
        'errors': errors
    }
