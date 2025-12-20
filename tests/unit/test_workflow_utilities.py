"""
Unit tests for workflow utilities.

Tests the utility functions for sprint analysis, work item state verification,
recent activity tracking, and blocker identification.
"""

import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime, timedelta
from workflows.utilities import (
    analyze_sprint,
    verify_work_item_states,
    get_recent_activity,
    identify_blockers
)


@pytest.mark.unit
class TestAnalyzeSprint:
    """Test suite for analyze_sprint utility function."""

    def test_analyze_sprint_returns_correct_structure(self):
        """Test analyze_sprint returns correct dict structure."""
        # Arrange
        mock_adapter = Mock()
        mock_adapter.query_sprint_work_items = Mock(return_value=[])
        sprint_name = "Sprint 6"

        # Act
        result = analyze_sprint(mock_adapter, sprint_name)

        # Assert
        assert "sprint_name" in result
        assert "total_items" in result
        assert "by_state" in result
        assert "by_type" in result
        assert "by_assignee" in result
        assert "story_points" in result
        assert "completion_rate" in result
        assert "velocity" in result
        assert "errors" in result
        assert result["sprint_name"] == sprint_name

    def test_analyze_sprint_counts_items_correctly(self):
        """Test analyze_sprint counts total items correctly."""
        # Arrange
        mock_adapter = Mock()
        sprint_items = [
            {"id": "1", "state": "Active", "type": "Task", "assigned_to": "Alice"},
            {"id": "2", "state": "Done", "type": "Task", "assigned_to": "Bob"},
            {"id": "3", "state": "In Progress", "type": "Bug", "assigned_to": "Alice"}
        ]
        mock_adapter.query_sprint_work_items = Mock(return_value=sprint_items)

        # Act
        result = analyze_sprint(mock_adapter, "Sprint 6")

        # Assert
        assert result["total_items"] == 3

    def test_analyze_sprint_groups_by_state(self):
        """Test analyze_sprint groups items by state."""
        # Arrange
        mock_adapter = Mock()
        sprint_items = [
            {"id": "1", "state": "Active"},
            {"id": "2", "state": "Done"},
            {"id": "3", "state": "Done"},
            {"id": "4", "state": "Active"}
        ]
        mock_adapter.query_sprint_work_items = Mock(return_value=sprint_items)

        # Act
        result = analyze_sprint(mock_adapter, "Sprint 6")

        # Assert
        assert result["by_state"]["Active"] == 2
        assert result["by_state"]["Done"] == 2

    def test_analyze_sprint_groups_by_type(self):
        """Test analyze_sprint groups items by type."""
        # Arrange
        mock_adapter = Mock()
        sprint_items = [
            {"id": "1", "type": "Task", "state": "Active"},
            {"id": "2", "type": "Bug", "state": "Done"},
            {"id": "3", "type": "Task", "state": "Active"}
        ]
        mock_adapter.query_sprint_work_items = Mock(return_value=sprint_items)

        # Act
        result = analyze_sprint(mock_adapter, "Sprint 6")

        # Assert
        assert result["by_type"]["Task"] == 2
        assert result["by_type"]["Bug"] == 1

    def test_analyze_sprint_groups_by_assignee(self):
        """Test analyze_sprint groups items by assignee."""
        # Arrange
        mock_adapter = Mock()
        sprint_items = [
            {"id": "1", "assigned_to": "Alice", "state": "Active"},
            {"id": "2", "assigned_to": "Bob", "state": "Done"},
            {"id": "3", "assigned_to": "Alice", "state": "Active"}
        ]
        mock_adapter.query_sprint_work_items = Mock(return_value=sprint_items)

        # Act
        result = analyze_sprint(mock_adapter, "Sprint 6")

        # Assert
        assert result["by_assignee"]["Alice"] == 2
        assert result["by_assignee"]["Bob"] == 1

    def test_analyze_sprint_calculates_story_points_with_config(self):
        """Test analyze_sprint calculates story points when config provided."""
        # Arrange
        mock_adapter = Mock()
        config = {
            "work_tracking": {
                "custom_fields": {
                    "story_points": "Microsoft.VSTS.Scheduling.StoryPoints"
                }
            }
        }
        sprint_items = [
            {
                "id": "1",
                "state": "Done",
                "fields": {"Microsoft.VSTS.Scheduling.StoryPoints": 5}
            },
            {
                "id": "2",
                "state": "Active",
                "fields": {"Microsoft.VSTS.Scheduling.StoryPoints": 3}
            },
            {
                "id": "3",
                "state": "New",
                "fields": {"Microsoft.VSTS.Scheduling.StoryPoints": 8}
            }
        ]
        mock_adapter.query_sprint_work_items = Mock(return_value=sprint_items)

        # Act
        result = analyze_sprint(mock_adapter, "Sprint 6", config)

        # Assert
        assert result["story_points"]["total"] == 16
        assert result["story_points"]["completed"] == 5
        assert result["story_points"]["in_progress"] == 3
        assert result["story_points"]["not_started"] == 8

    def test_analyze_sprint_calculates_completion_rate(self):
        """Test analyze_sprint calculates completion rate correctly."""
        # Arrange
        mock_adapter = Mock()
        sprint_items = [
            {"id": "1", "state": "Done"},
            {"id": "2", "state": "Closed"},
            {"id": "3", "state": "Active"},
            {"id": "4", "state": "Active"}
        ]
        mock_adapter.query_sprint_work_items = Mock(return_value=sprint_items)

        # Act
        result = analyze_sprint(mock_adapter, "Sprint 6")

        # Assert
        assert result["completion_rate"] == 50.0  # 2 out of 4 completed

    def test_analyze_sprint_calculates_velocity(self):
        """Test analyze_sprint calculates velocity (completed story points)."""
        # Arrange
        mock_adapter = Mock()
        config = {
            "work_tracking": {
                "custom_fields": {
                    "story_points": "Microsoft.VSTS.Scheduling.StoryPoints"
                }
            }
        }
        sprint_items = [
            {
                "id": "1",
                "state": "Done",
                "fields": {"Microsoft.VSTS.Scheduling.StoryPoints": 5}
            },
            {
                "id": "2",
                "state": "Closed",
                "fields": {"Microsoft.VSTS.Scheduling.StoryPoints": 3}
            },
            {
                "id": "3",
                "state": "Active",
                "fields": {"Microsoft.VSTS.Scheduling.StoryPoints": 8}
            }
        ]
        mock_adapter.query_sprint_work_items = Mock(return_value=sprint_items)

        # Act
        result = analyze_sprint(mock_adapter, "Sprint 6", config)

        # Assert
        assert result["velocity"] == 8  # 5 + 3 completed

    def test_analyze_sprint_handles_empty_sprint(self):
        """Test analyze_sprint handles empty sprint gracefully."""
        # Arrange
        mock_adapter = Mock()
        mock_adapter.query_sprint_work_items = Mock(return_value=[])

        # Act
        result = analyze_sprint(mock_adapter, "Sprint 6")

        # Assert
        assert result["total_items"] == 0
        assert result["completion_rate"] == 0.0
        assert result["velocity"] == 0.0
        assert len(result["errors"]) == 0

    def test_analyze_sprint_handles_adapter_exception(self):
        """Test analyze_sprint handles adapter exceptions gracefully."""
        # Arrange
        mock_adapter = Mock()
        mock_adapter.query_sprint_work_items = Mock(side_effect=Exception("Connection error"))

        # Act
        result = analyze_sprint(mock_adapter, "Sprint 6")

        # Assert
        assert len(result["errors"]) > 0
        assert "Connection error" in result["errors"][0]

    def test_analyze_sprint_handles_missing_story_points_field(self):
        """Test analyze_sprint handles missing story points gracefully."""
        # Arrange
        mock_adapter = Mock()
        config = {
            "work_tracking": {
                "custom_fields": {
                    "story_points": "Microsoft.VSTS.Scheduling.StoryPoints"
                }
            }
        }
        sprint_items = [
            {"id": "1", "state": "Done", "fields": {}},  # No story points
            {"id": "2", "state": "Active", "story_points": 5}  # Flat structure
        ]
        mock_adapter.query_sprint_work_items = Mock(return_value=sprint_items)

        # Act
        result = analyze_sprint(mock_adapter, "Sprint 6", config)

        # Assert
        assert result["story_points"]["total"] == 5  # Only second item counted
        assert result["story_points"]["in_progress"] == 5


@pytest.mark.unit
class TestVerifyWorkItemStates:
    """Test suite for verify_work_item_states utility function."""

    def test_verify_work_item_states_returns_correct_structure(self):
        """Test verify_work_item_states returns correct dict structure."""
        # Arrange
        mock_adapter = Mock()
        mock_adapter.get_work_item = Mock(return_value={"id": "1", "state": "Active"})
        work_items = [{"id": "1", "state": "Active", "title": "Test"}]

        # Act
        result = verify_work_item_states(mock_adapter, work_items)

        # Assert
        assert "verified_count" in result
        assert "divergence_count" in result
        assert "divergences" in result
        assert "summary" in result
        assert "errors" in result
        assert "errors" in result["summary"]
        assert "warnings" in result["summary"]

    def test_verify_work_item_states_passes_when_states_match(self):
        """Test verification passes when claimed and actual states match."""
        # Arrange
        mock_adapter = Mock()
        mock_adapter.get_work_item = Mock(return_value={"id": "1", "state": "Active"})
        work_items = [{"id": "1", "state": "Active", "title": "Test Task"}]

        # Act
        result = verify_work_item_states(mock_adapter, work_items)

        # Assert
        assert result["verified_count"] == 1
        assert result["divergence_count"] == 0
        assert len(result["divergences"]) == 0

    def test_verify_work_item_states_detects_state_mismatch(self):
        """Test verification detects state mismatch."""
        # Arrange
        mock_adapter = Mock()
        mock_adapter.get_work_item = Mock(return_value={"id": "1", "state": "Active"})
        work_items = [{"id": "1", "state": "Done", "title": "Test Task"}]

        # Act
        result = verify_work_item_states(mock_adapter, work_items)

        # Assert
        assert result["divergence_count"] == 1
        assert len(result["divergences"]) == 1
        assert result["divergences"][0]["severity"] == "WARNING"
        assert result["divergences"][0]["claimed_state"] == "Done"
        assert result["divergences"][0]["actual_state"] == "Active"

    def test_verify_work_item_states_detects_claimed_terminal_but_not_terminal(self):
        """Test verification detects item claimed Done but actually Active."""
        # Arrange
        mock_adapter = Mock()
        mock_adapter.get_work_item = Mock(return_value={"id": "1", "state": "Active"})
        work_items = [{"id": "1", "state": "Done", "title": "Test Task"}]

        # Act
        result = verify_work_item_states(mock_adapter, work_items)

        # Assert
        assert result["divergence_count"] == 1
        assert result["divergences"][0]["severity"] == "WARNING"
        assert result["summary"]["warnings"] == 1

    def test_verify_work_item_states_detects_not_found(self):
        """Test verification detects work item not found in adapter."""
        # Arrange
        mock_adapter = Mock()
        mock_adapter.get_work_item = Mock(return_value=None)
        work_items = [{"id": "1", "state": "Done", "title": "Test Task"}]

        # Act
        result = verify_work_item_states(mock_adapter, work_items)

        # Assert
        assert result["divergence_count"] == 1
        assert result["divergences"][0]["severity"] == "ERROR"
        assert result["divergences"][0]["actual_state"] == "NOT_FOUND"
        assert result["summary"]["errors"] == 1

    def test_verify_work_item_states_handles_multiple_items(self):
        """Test verification handles multiple work items."""
        # Arrange
        mock_adapter = Mock()

        def mock_get_item(item_id):
            if item_id == "1":
                return {"id": "1", "state": "Done"}
            elif item_id == "2":
                return {"id": "2", "state": "Active"}
            elif item_id == "3":
                return None
            return None

        mock_adapter.get_work_item = Mock(side_effect=mock_get_item)
        work_items = [
            {"id": "1", "state": "Done", "title": "Task 1"},  # Match
            {"id": "2", "state": "Done", "title": "Task 2"},  # Mismatch
            {"id": "3", "state": "Active", "title": "Task 3"}  # Not found
        ]

        # Act
        result = verify_work_item_states(mock_adapter, work_items)

        # Assert
        assert result["verified_count"] == 2  # 1 and 2 found
        assert result["divergence_count"] == 2  # 2 and 3 diverge
        assert result["summary"]["errors"] == 1  # 3 not found
        assert result["summary"]["warnings"] == 1  # 2 state mismatch

    def test_verify_work_item_states_handles_adapter_exception(self):
        """Test verification handles adapter exceptions gracefully."""
        # Arrange
        mock_adapter = Mock()
        mock_adapter.get_work_item = Mock(side_effect=Exception("Connection error"))
        work_items = [{"id": "1", "state": "Done", "title": "Test"}]

        # Act
        result = verify_work_item_states(mock_adapter, work_items)

        # Assert
        assert len(result["errors"]) > 0
        assert "Connection error" in result["errors"][0]

    def test_verify_work_item_states_handles_custom_terminal_states(self):
        """Test verification respects custom terminal states."""
        # Arrange
        mock_adapter = Mock()
        mock_adapter.get_work_item = Mock(return_value={"id": "1", "state": "Active"})
        work_items = [{"id": "1", "state": "Complete", "title": "Test"}]
        custom_terminal = ["Complete", "Finished"]

        # Act
        result = verify_work_item_states(mock_adapter, work_items, custom_terminal)

        # Assert
        assert result["divergence_count"] == 1  # Complete is terminal but Active is not
        assert result["divergences"][0]["severity"] == "WARNING"

    def test_verify_work_item_states_handles_nested_state_field(self):
        """Test verification handles nested state field (Azure DevOps format)."""
        # Arrange
        mock_adapter = Mock()
        mock_adapter.get_work_item = Mock(return_value={
            "id": "1",
            "fields": {"System.State": "Done"}
        })
        work_items = [{"id": "1", "state": "Done", "title": "Test"}]

        # Act
        result = verify_work_item_states(mock_adapter, work_items)

        # Assert
        assert result["verified_count"] == 1
        assert result["divergence_count"] == 0

    def test_verify_work_item_states_handles_missing_id(self):
        """Test verification handles work items without id field."""
        # Arrange
        mock_adapter = Mock()
        work_items = [{"state": "Done", "title": "Test"}]  # No id

        # Act
        result = verify_work_item_states(mock_adapter, work_items)

        # Assert
        assert result["verified_count"] == 0
        assert len(result["errors"]) > 0


@pytest.mark.unit
class TestGetRecentActivity:
    """Test suite for get_recent_activity utility function."""

    def test_get_recent_activity_returns_correct_structure(self):
        """Test get_recent_activity returns correct dict structure."""
        # Arrange
        mock_adapter = Mock()
        mock_adapter.query_sprint_work_items = Mock(return_value=[])

        # Act
        result = get_recent_activity(mock_adapter, "Sprint 6", hours=24)

        # Assert
        assert "sprint_name" in result
        assert "hours" in result
        assert "total_items" in result
        assert "recent_items" in result
        assert "recent_count" in result
        assert "errors" in result

    def test_get_recent_activity_filters_by_time_window(self):
        """Test get_recent_activity filters items by time window."""
        # Arrange
        mock_adapter = Mock()
        now = datetime.now()
        yesterday = now - timedelta(hours=12)
        two_days_ago = now - timedelta(hours=48)

        sprint_items = [
            {
                "id": "1",
                "title": "Recent Task",
                "state": "Active",
                "updated_at": yesterday.isoformat()
            },
            {
                "id": "2",
                "title": "Old Task",
                "state": "Done",
                "updated_at": two_days_ago.isoformat()
            }
        ]
        mock_adapter.query_sprint_work_items = Mock(return_value=sprint_items)

        # Act
        result = get_recent_activity(mock_adapter, "Sprint 6", hours=24)

        # Assert
        assert result["total_items"] == 2
        assert result["recent_count"] == 1
        assert result["recent_items"][0]["id"] == "1"

    def test_get_recent_activity_handles_empty_sprint(self):
        """Test get_recent_activity handles empty sprint."""
        # Arrange
        mock_adapter = Mock()
        mock_adapter.query_sprint_work_items = Mock(return_value=[])

        # Act
        result = get_recent_activity(mock_adapter, "Sprint 6", hours=24)

        # Assert
        assert result["total_items"] == 0
        assert result["recent_count"] == 0
        assert len(result["recent_items"]) == 0

    def test_get_recent_activity_handles_nested_updated_at_field(self):
        """Test get_recent_activity handles nested updated_at field."""
        # Arrange
        mock_adapter = Mock()
        now = datetime.now()
        yesterday = now - timedelta(hours=12)

        sprint_items = [
            {
                "id": "1",
                "fields": {"System.ChangedDate": yesterday.isoformat()}
            }
        ]
        mock_adapter.query_sprint_work_items = Mock(return_value=sprint_items)

        # Act
        result = get_recent_activity(mock_adapter, "Sprint 6", hours=24)

        # Assert
        assert result["recent_count"] == 1

    def test_get_recent_activity_handles_missing_timestamp(self):
        """Test get_recent_activity handles items without timestamp."""
        # Arrange
        mock_adapter = Mock()
        sprint_items = [
            {"id": "1", "title": "No Timestamp"}
        ]
        mock_adapter.query_sprint_work_items = Mock(return_value=sprint_items)

        # Act
        result = get_recent_activity(mock_adapter, "Sprint 6", hours=24)

        # Assert
        assert result["total_items"] == 1
        assert result["recent_count"] == 0  # Skipped due to missing timestamp

    def test_get_recent_activity_handles_adapter_exception(self):
        """Test get_recent_activity handles adapter exceptions."""
        # Arrange
        mock_adapter = Mock()
        mock_adapter.query_sprint_work_items = Mock(side_effect=Exception("Connection error"))

        # Act
        result = get_recent_activity(mock_adapter, "Sprint 6", hours=24)

        # Assert
        assert len(result["errors"]) > 0
        assert "Connection error" in result["errors"][0]

    def test_get_recent_activity_handles_invalid_timestamp(self):
        """Test get_recent_activity handles invalid timestamp format."""
        # Arrange
        mock_adapter = Mock()
        sprint_items = [
            {"id": "1", "updated_at": "invalid-date"}
        ]
        mock_adapter.query_sprint_work_items = Mock(return_value=sprint_items)

        # Act
        result = get_recent_activity(mock_adapter, "Sprint 6", hours=24)

        # Assert
        assert result["recent_count"] == 0
        assert len(result["errors"]) > 0


@pytest.mark.unit
class TestIdentifyBlockers:
    """Test suite for identify_blockers utility function."""

    def test_identify_blockers_returns_correct_structure(self):
        """Test identify_blockers returns correct dict structure."""
        # Arrange
        mock_adapter = Mock()
        mock_adapter.query_sprint_work_items = Mock(return_value=[])

        # Act
        result = identify_blockers(mock_adapter, "Sprint 6")

        # Assert
        assert "sprint_name" in result
        assert "total_blockers" in result
        assert "blocked_items" in result
        assert "tagged_items" in result
        assert "stale_items" in result
        assert "impact" in result
        assert "errors" in result
        assert "affected_people" in result["impact"]
        assert "story_points_at_risk" in result["impact"]

    def test_identify_blockers_detects_blocked_state(self):
        """Test identify_blockers detects items in Blocked state."""
        # Arrange
        mock_adapter = Mock()
        sprint_items = [
            {
                "id": "1",
                "title": "Blocked Task",
                "state": "Blocked",
                "assigned_to": "Alice"
            }
        ]
        mock_adapter.query_sprint_work_items = Mock(return_value=sprint_items)

        # Act
        result = identify_blockers(mock_adapter, "Sprint 6")

        # Assert
        assert result["total_blockers"] == 1
        assert len(result["blocked_items"]) == 1
        assert result["blocked_items"][0]["id"] == "1"
        assert result["impact"]["affected_people"] == 1

    def test_identify_blockers_detects_blocker_tag(self):
        """Test identify_blockers detects items tagged as blocker."""
        # Arrange
        mock_adapter = Mock()
        sprint_items = [
            {
                "id": "1",
                "title": "Tagged Task",
                "state": "Active",
                "tags": ["blocker", "urgent"]
            }
        ]
        mock_adapter.query_sprint_work_items = Mock(return_value=sprint_items)

        # Act
        result = identify_blockers(mock_adapter, "Sprint 6")

        # Assert
        assert result["total_blockers"] == 1
        assert len(result["tagged_items"]) == 1

    def test_identify_blockers_detects_stale_items(self):
        """Test identify_blockers detects stale items (no updates in N+ days)."""
        # Arrange
        mock_adapter = Mock()
        old_date = datetime.now() - timedelta(days=5)

        sprint_items = [
            {
                "id": "1",
                "title": "Stale Task",
                "state": "Active",
                "updated_at": old_date.isoformat()
            }
        ]
        mock_adapter.query_sprint_work_items = Mock(return_value=sprint_items)

        # Act
        result = identify_blockers(mock_adapter, "Sprint 6", stale_threshold_days=3)

        # Assert
        assert result["total_blockers"] == 1
        assert len(result["stale_items"]) == 1
        assert result["stale_items"][0]["days_stale"] == 5

    def test_identify_blockers_does_not_count_done_items_as_stale(self):
        """Test identify_blockers ignores stale items in terminal states."""
        # Arrange
        mock_adapter = Mock()
        old_date = datetime.now() - timedelta(days=5)

        sprint_items = [
            {
                "id": "1",
                "title": "Done Task",
                "state": "Done",
                "updated_at": old_date.isoformat()
            }
        ]
        mock_adapter.query_sprint_work_items = Mock(return_value=sprint_items)

        # Act
        result = identify_blockers(mock_adapter, "Sprint 6", stale_threshold_days=3)

        # Assert
        assert result["total_blockers"] == 0
        assert len(result["stale_items"]) == 0

    def test_identify_blockers_calculates_story_points_at_risk(self):
        """Test identify_blockers calculates story points at risk."""
        # Arrange
        mock_adapter = Mock()
        config = {
            "work_tracking": {
                "custom_fields": {
                    "story_points": "Microsoft.VSTS.Scheduling.StoryPoints"
                }
            }
        }
        sprint_items = [
            {
                "id": "1",
                "state": "Blocked",
                "fields": {"Microsoft.VSTS.Scheduling.StoryPoints": 5}
            },
            {
                "id": "2",
                "state": "Active",
                "tags": ["blocker"],
                "fields": {"Microsoft.VSTS.Scheduling.StoryPoints": 3}
            }
        ]
        mock_adapter.query_sprint_work_items = Mock(return_value=sprint_items)

        # Act
        result = identify_blockers(mock_adapter, "Sprint 6", config=config)

        # Assert
        assert result["impact"]["story_points_at_risk"] == 8

    def test_identify_blockers_does_not_double_count(self):
        """Test identify_blockers does not double-count items with multiple blocker signals."""
        # Arrange
        mock_adapter = Mock()
        old_date = datetime.now() - timedelta(days=5)

        sprint_items = [
            {
                "id": "1",
                "title": "Multi-blocked",
                "state": "Blocked",
                "tags": ["blocker"],
                "updated_at": old_date.isoformat()
            }
        ]
        mock_adapter.query_sprint_work_items = Mock(return_value=sprint_items)

        # Act
        result = identify_blockers(mock_adapter, "Sprint 6", stale_threshold_days=3)

        # Assert
        # Should appear in all 3 lists but only counted once in total
        assert result["total_blockers"] == 1
        assert len(result["blocked_items"]) == 1
        assert len(result["tagged_items"]) == 1
        assert len(result["stale_items"]) == 1

    def test_identify_blockers_handles_empty_sprint(self):
        """Test identify_blockers handles empty sprint."""
        # Arrange
        mock_adapter = Mock()
        mock_adapter.query_sprint_work_items = Mock(return_value=[])

        # Act
        result = identify_blockers(mock_adapter, "Sprint 6")

        # Assert
        assert result["total_blockers"] == 0
        assert len(result["blocked_items"]) == 0
        assert len(result["tagged_items"]) == 0
        assert len(result["stale_items"]) == 0
        assert result["impact"]["affected_people"] == 0
        assert result["impact"]["story_points_at_risk"] == 0

    def test_identify_blockers_handles_adapter_exception(self):
        """Test identify_blockers handles adapter exceptions."""
        # Arrange
        mock_adapter = Mock()
        mock_adapter.query_sprint_work_items = Mock(side_effect=Exception("Connection error"))

        # Act
        result = identify_blockers(mock_adapter, "Sprint 6")

        # Assert
        assert len(result["errors"]) > 0
        assert "Connection error" in result["errors"][0]

    def test_identify_blockers_handles_string_tags(self):
        """Test identify_blockers handles tags as semicolon-separated string."""
        # Arrange
        mock_adapter = Mock()
        sprint_items = [
            {
                "id": "1",
                "state": "Active",
                "fields": {"System.Tags": "blocker; urgent; critical"}
            }
        ]
        mock_adapter.query_sprint_work_items = Mock(return_value=sprint_items)

        # Act
        result = identify_blockers(mock_adapter, "Sprint 6")

        # Assert
        assert result["total_blockers"] == 1
        assert len(result["tagged_items"]) == 1

    def test_identify_blockers_counts_affected_people(self):
        """Test identify_blockers counts unique affected assignees."""
        # Arrange
        mock_adapter = Mock()
        sprint_items = [
            {"id": "1", "state": "Blocked", "assigned_to": "Alice"},
            {"id": "2", "state": "Blocked", "assigned_to": "Bob"},
            {"id": "3", "state": "Blocked", "assigned_to": "Alice"}
        ]
        mock_adapter.query_sprint_work_items = Mock(return_value=sprint_items)

        # Act
        result = identify_blockers(mock_adapter, "Sprint 6")

        # Assert
        assert result["total_blockers"] == 3
        assert result["impact"]["affected_people"] == 2  # Alice and Bob

    def test_identify_blockers_ignores_unassigned_in_people_count(self):
        """Test identify_blockers does not count Unassigned in affected people."""
        # Arrange
        mock_adapter = Mock()
        sprint_items = [
            {"id": "1", "state": "Blocked", "assigned_to": "Alice"},
            {"id": "2", "state": "Blocked", "assigned_to": "Unassigned"}
        ]
        mock_adapter.query_sprint_work_items = Mock(return_value=sprint_items)

        # Act
        result = identify_blockers(mock_adapter, "Sprint 6")

        # Assert
        assert result["total_blockers"] == 2
        assert result["impact"]["affected_people"] == 1  # Only Alice
