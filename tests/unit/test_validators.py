"""
Unit tests for workflow validators.

Tests the verification checklist validators for backlog-grooming and sprint-planning workflows.
"""

import pytest
from unittest.mock import Mock, MagicMock
from workflows.validators import verify_backlog_grooming, verify_sprint_planning


@pytest.mark.unit
class TestVerifyBacklogGrooming:
    """Test suite for verify_backlog_grooming validator."""

    def test_feature_task_hierarchy_passes_when_all_features_have_tasks(self):
        """Test hierarchy check passes when all Features have Tasks."""
        # Arrange
        mock_adapter = Mock()
        epic_id = "EPIC-001"
        created_features = [
            {"id": "FEATURE-001", "title": "Feature 1", "expected_tasks": 2},
            {"id": "FEATURE-002", "title": "Feature 2", "expected_tasks": 3}
        ]
        config = {
            "work_tracking": {
                "work_item_types": {"task": "Task", "feature": "Feature"},
                "custom_fields": {"story_points": "Microsoft.VSTS.Scheduling.StoryPoints"}
            }
        }

        # Mock adapter to return Tasks for Features
        def mock_query(work_item_type=None):
            if work_item_type == "Task":
                return [
                    {"id": "TASK-001", "parent_id": "FEATURE-001"},
                    {"id": "TASK-002", "parent_id": "FEATURE-001"},
                    {"id": "TASK-003", "parent_id": "FEATURE-002"},
                    {"id": "TASK-004", "parent_id": "FEATURE-002"},
                    {"id": "TASK-005", "parent_id": "FEATURE-002"}
                ]
            elif work_item_type == "Feature":
                return [
                    {"id": "FEATURE-001", "parent_id": "EPIC-001"},
                    {"id": "FEATURE-002", "parent_id": "EPIC-001"}
                ]
            return []

        mock_adapter.query_work_items = Mock(side_effect=mock_query)
        mock_adapter.get_work_item = Mock(return_value={
            "id": "EPIC-001",
            "fields": {"Microsoft.VSTS.Scheduling.StoryPoints": 10}
        })

        # Act
        result = verify_backlog_grooming(mock_adapter, epic_id, created_features, config)

        # Assert
        assert result["checks"]["feature_task_hierarchy"]["passed"] is True
        assert len(result["checks"]["feature_task_hierarchy"]["childless_features"]) == 0

    def test_feature_task_hierarchy_fails_when_features_have_no_tasks(self):
        """Test hierarchy check fails when Features have no Tasks."""
        # Arrange
        mock_adapter = Mock()
        epic_id = "EPIC-001"
        created_features = [
            {"id": "FEATURE-001", "title": "Feature 1", "expected_tasks": 2},
            {"id": "FEATURE-002", "title": "Feature 2", "expected_tasks": 0}
        ]
        config = {
            "work_tracking": {
                "work_item_types": {"task": "Task", "feature": "Feature"},
                "custom_fields": {"story_points": "Microsoft.VSTS.Scheduling.StoryPoints"}
            }
        }

        # Mock adapter - FEATURE-002 has no tasks
        def mock_query(work_item_type=None):
            if work_item_type == "Task":
                return [
                    {"id": "TASK-001", "parent_id": "FEATURE-001"},
                    {"id": "TASK-002", "parent_id": "FEATURE-001"}
                ]
            elif work_item_type == "Feature":
                return [
                    {"id": "FEATURE-001", "parent_id": "EPIC-001"},
                    {"id": "FEATURE-002", "parent_id": "EPIC-001"}
                ]
            return []

        mock_adapter.query_work_items = Mock(side_effect=mock_query)
        mock_adapter.get_work_item = Mock(return_value={
            "id": "EPIC-001",
            "fields": {"Microsoft.VSTS.Scheduling.StoryPoints": 10}
        })

        # Act
        result = verify_backlog_grooming(mock_adapter, epic_id, created_features, config)

        # Assert
        assert result["checks"]["feature_task_hierarchy"]["passed"] is False
        assert len(result["checks"]["feature_task_hierarchy"]["childless_features"]) == 1
        assert result["checks"]["feature_task_hierarchy"]["childless_features"][0]["id"] == "FEATURE-002"
        assert result["passed"] is False

    def test_story_point_variance_passes_when_variance_within_threshold(self):
        """Test story point variance check passes when variance <= 20%."""
        # Arrange
        mock_adapter = Mock()
        epic_id = "EPIC-001"
        created_features = [
            {"id": "FEATURE-001", "title": "Feature 1", "expected_tasks": 2}
        ]
        config = {
            "work_tracking": {
                "work_item_types": {"task": "Task", "feature": "Feature"},
                "custom_fields": {"story_points": "Microsoft.VSTS.Scheduling.StoryPoints"}
            }
        }

        # Mock adapter - Feature has 10 points, Tasks sum to 9 points (10% variance)
        def mock_query(work_item_type=None):
            if work_item_type == "Task":
                return [
                    {"id": "TASK-001", "parent_id": "FEATURE-001", "fields": {"Microsoft.VSTS.Scheduling.StoryPoints": 5}},
                    {"id": "TASK-002", "parent_id": "FEATURE-001", "fields": {"Microsoft.VSTS.Scheduling.StoryPoints": 4}}
                ]
            elif work_item_type == "Feature":
                return [{"id": "FEATURE-001", "parent_id": "EPIC-001"}]
            return []

        def mock_get_item(item_id):
            if item_id == "FEATURE-001":
                return {"id": "FEATURE-001", "fields": {"Microsoft.VSTS.Scheduling.StoryPoints": 10}}
            elif item_id == "EPIC-001":
                return {"id": "EPIC-001", "fields": {"Microsoft.VSTS.Scheduling.StoryPoints": 10}}
            return None

        mock_adapter.query_work_items = Mock(side_effect=mock_query)
        mock_adapter.get_work_item = Mock(side_effect=mock_get_item)

        # Act
        result = verify_backlog_grooming(mock_adapter, epic_id, created_features, config)

        # Assert
        assert result["checks"]["story_point_variance"]["passed"] is True
        assert len(result["checks"]["story_point_variance"]["mismatches"]) == 0

    def test_story_point_variance_fails_when_variance_exceeds_threshold(self):
        """Test story point variance check fails when variance > 20%."""
        # Arrange
        mock_adapter = Mock()
        epic_id = "EPIC-001"
        created_features = [
            {"id": "FEATURE-001", "title": "Feature 1", "expected_tasks": 2}
        ]
        config = {
            "work_tracking": {
                "work_item_types": {"task": "Task", "feature": "Feature"},
                "custom_fields": {"story_points": "Microsoft.VSTS.Scheduling.StoryPoints"}
            }
        }

        # Mock adapter - Feature has 10 points, Tasks sum to 5 points (50% variance)
        def mock_query(work_item_type=None):
            if work_item_type == "Task":
                return [
                    {"id": "TASK-001", "parent_id": "FEATURE-001", "fields": {"Microsoft.VSTS.Scheduling.StoryPoints": 3}},
                    {"id": "TASK-002", "parent_id": "FEATURE-001", "fields": {"Microsoft.VSTS.Scheduling.StoryPoints": 2}}
                ]
            elif work_item_type == "Feature":
                return [{"id": "FEATURE-001", "parent_id": "EPIC-001"}]
            return []

        def mock_get_item(item_id):
            if item_id == "FEATURE-001":
                return {"id": "FEATURE-001", "fields": {"Microsoft.VSTS.Scheduling.StoryPoints": 10}}
            elif item_id == "EPIC-001":
                return {"id": "EPIC-001", "fields": {"Microsoft.VSTS.Scheduling.StoryPoints": 10}}
            return None

        mock_adapter.query_work_items = Mock(side_effect=mock_query)
        mock_adapter.get_work_item = Mock(side_effect=mock_get_item)

        # Act
        result = verify_backlog_grooming(mock_adapter, epic_id, created_features, config)

        # Assert
        assert result["checks"]["story_point_variance"]["passed"] is False
        assert len(result["checks"]["story_point_variance"]["mismatches"]) == 1
        assert result["checks"]["story_point_variance"]["mismatches"][0]["id"] == "FEATURE-001"
        assert result["passed"] is False

    def test_handles_missing_story_points_field_gracefully(self):
        """Test handles missing story points field gracefully."""
        # Arrange
        mock_adapter = Mock()
        epic_id = "EPIC-001"
        created_features = [
            {"id": "FEATURE-001", "title": "Feature 1", "expected_tasks": 2}
        ]
        config = {
            "work_tracking": {
                "work_item_types": {"task": "Task", "feature": "Feature"},
                "custom_fields": {}  # No story points field
            }
        }

        # Mock adapter
        def mock_query(work_item_type=None):
            if work_item_type == "Task":
                return [
                    {"id": "TASK-001", "parent_id": "FEATURE-001"},
                    {"id": "TASK-002", "parent_id": "FEATURE-001"}
                ]
            elif work_item_type == "Feature":
                return [{"id": "FEATURE-001", "parent_id": "EPIC-001"}]
            return []

        mock_adapter.query_work_items = Mock(side_effect=mock_query)
        mock_adapter.get_work_item = Mock(return_value={
            "id": "EPIC-001",
            "fields": {}
        })

        # Act
        result = verify_backlog_grooming(mock_adapter, epic_id, created_features, config)

        # Assert
        assert result["checks"]["story_point_variance"]["passed"] is True
        assert "not configured" in result["checks"]["story_point_variance"]["details"]

    def test_handles_adapter_query_exceptions(self):
        """Test handles adapter query exceptions gracefully."""
        # Arrange
        mock_adapter = Mock()
        epic_id = "EPIC-001"
        created_features = [
            {"id": "FEATURE-001", "title": "Feature 1", "expected_tasks": 2}
        ]
        config = {
            "work_tracking": {
                "work_item_types": {"task": "Task", "feature": "Feature"},
                "custom_fields": {"story_points": "Microsoft.VSTS.Scheduling.StoryPoints"}
            }
        }

        # Mock adapter to raise exception
        mock_adapter.query_work_items = Mock(side_effect=Exception("Connection error"))
        mock_adapter.get_work_item = Mock(return_value=None)

        # Act
        result = verify_backlog_grooming(mock_adapter, epic_id, created_features, config)

        # Assert
        assert result["passed"] is False
        assert len(result["errors"]) > 0
        assert "Connection error" in str(result["errors"])

    def test_returns_correct_dict_structure(self):
        """Test returns correct dict structure."""
        # Arrange
        mock_adapter = Mock()
        epic_id = "EPIC-001"
        created_features = []
        config = {
            "work_tracking": {
                "work_item_types": {"task": "Task", "feature": "Feature"},
                "custom_fields": {}
            }
        }

        mock_adapter.query_work_items = Mock(return_value=[])
        mock_adapter.get_work_item = Mock(return_value={
            "id": "EPIC-001",
            "fields": {}
        })

        # Act
        result = verify_backlog_grooming(mock_adapter, epic_id, created_features, config)

        # Assert
        assert "passed" in result
        assert "checks" in result
        assert "errors" in result
        assert "feature_task_hierarchy" in result["checks"]
        assert "story_point_variance" in result["checks"]
        assert "passed" in result["checks"]["feature_task_hierarchy"]
        assert "details" in result["checks"]["feature_task_hierarchy"]


@pytest.mark.unit
class TestVerifySprintPlanning:
    """Test suite for verify_sprint_planning validator."""

    def test_work_items_exist_check_passes_when_all_items_found(self):
        """Test work items exist check passes when all items found."""
        # Arrange
        mock_adapter = Mock()
        created_items = ["TASK-001", "TASK-002", "TASK-003"]
        sprint_number = "Sprint 5"
        config = {
            "work_tracking": {
                "project": "TestProject"
            }
        }

        # Mock adapter - all items exist
        def mock_get_item(item_id):
            return {"id": item_id, "fields": {
                "System.Title": f"Task {item_id}",
                "System.Description": "A" * 600,
                "Microsoft.VSTS.Common.AcceptanceCriteria": "- [ ] AC 1\n- [ ] AC 2\n- [ ] AC 3\n",
                "System.IterationPath": f"TestProject\\{sprint_number}"
            }}

        mock_adapter.get_work_item = Mock(side_effect=mock_get_item)

        # Act
        result = verify_sprint_planning(mock_adapter, created_items, sprint_number, config)

        # Assert
        assert result["checks"]["work_items_exist"]["passed"] is True
        assert result["checks"]["work_items_exist"]["verified_count"] == 3
        assert result["checks"]["work_items_exist"]["missing_count"] == 0

    def test_work_items_exist_check_fails_when_items_missing(self):
        """Test work items exist check fails when items missing."""
        # Arrange
        mock_adapter = Mock()
        created_items = ["TASK-001", "TASK-002", "TASK-003"]
        sprint_number = "Sprint 5"
        config = {
            "work_tracking": {
                "project": "TestProject"
            }
        }

        # Mock adapter - TASK-002 doesn't exist
        def mock_get_item(item_id):
            if item_id == "TASK-002":
                return None
            return {"id": item_id, "fields": {
                "System.Title": f"Task {item_id}",
                "System.Description": "A" * 600,
                "Microsoft.VSTS.Common.AcceptanceCriteria": "- [ ] AC 1\n- [ ] AC 2\n- [ ] AC 3\n",
                "System.IterationPath": f"TestProject\\{sprint_number}"
            }}

        mock_adapter.get_work_item = Mock(side_effect=mock_get_item)

        # Act
        result = verify_sprint_planning(mock_adapter, created_items, sprint_number, config)

        # Assert
        assert result["checks"]["work_items_exist"]["passed"] is False
        assert result["checks"]["work_items_exist"]["verified_count"] == 2
        assert result["checks"]["work_items_exist"]["missing_count"] == 1
        assert "TASK-002" in result["checks"]["work_items_exist"]["missing_items"]
        assert result["passed"] is False

    def test_content_quality_check_passes_when_descriptions_sufficient(self):
        """Test content quality check passes when descriptions >= 500 chars and AC >= 3."""
        # Arrange
        mock_adapter = Mock()
        created_items = ["TASK-001"]
        sprint_number = "Sprint 5"
        config = {
            "work_tracking": {
                "project": "TestProject"
            }
        }

        # Mock adapter - sufficient content
        mock_adapter.get_work_item = Mock(return_value={
            "id": "TASK-001",
            "fields": {
                "System.Title": "Task 1",
                "System.Description": "A" * 600,  # 600 characters
                "Microsoft.VSTS.Common.AcceptanceCriteria": "- [ ] AC 1\n- [ ] AC 2\n- [ ] AC 3\n",
                "System.IterationPath": f"TestProject\\{sprint_number}"
            }
        })

        # Act
        result = verify_sprint_planning(mock_adapter, created_items, sprint_number, config)

        # Assert
        assert result["checks"]["content_quality"]["passed"] is True
        assert result["checks"]["content_quality"]["issues_count"] == 0

    def test_content_quality_check_fails_when_descriptions_too_short(self):
        """Test content quality check fails when descriptions too short."""
        # Arrange
        mock_adapter = Mock()
        created_items = ["TASK-001"]
        sprint_number = "Sprint 5"
        config = {
            "work_tracking": {
                "project": "TestProject"
            }
        }

        # Mock adapter - description too short (100 chars)
        mock_adapter.get_work_item = Mock(return_value={
            "id": "TASK-001",
            "fields": {
                "System.Title": "Task 1",
                "System.Description": "A" * 100,
                "Microsoft.VSTS.Common.AcceptanceCriteria": "- [ ] AC 1\n- [ ] AC 2\n- [ ] AC 3\n",
                "System.IterationPath": f"TestProject\\{sprint_number}"
            }
        })

        # Act
        result = verify_sprint_planning(mock_adapter, created_items, sprint_number, config)

        # Assert
        assert result["checks"]["content_quality"]["passed"] is False
        assert result["checks"]["content_quality"]["issues_count"] == 1
        assert "description too short" in result["checks"]["content_quality"]["quality_issues"][0]["issues"][0]
        assert result["passed"] is False

    def test_content_quality_check_fails_when_ac_insufficient(self):
        """Test content quality check fails when AC insufficient."""
        # Arrange
        mock_adapter = Mock()
        created_items = ["TASK-001"]
        sprint_number = "Sprint 5"
        config = {
            "work_tracking": {
                "project": "TestProject"
            }
        }

        # Mock adapter - only 2 AC (need 3)
        mock_adapter.get_work_item = Mock(return_value={
            "id": "TASK-001",
            "fields": {
                "System.Title": "Task 1",
                "System.Description": "A" * 600,
                "Microsoft.VSTS.Common.AcceptanceCriteria": "- [ ] AC 1\n- [ ] AC 2\n",
                "System.IterationPath": f"TestProject\\{sprint_number}"
            }
        })

        # Act
        result = verify_sprint_planning(mock_adapter, created_items, sprint_number, config)

        # Assert
        assert result["checks"]["content_quality"]["passed"] is False
        assert result["checks"]["content_quality"]["issues_count"] == 1
        assert "insufficient acceptance criteria" in result["checks"]["content_quality"]["quality_issues"][0]["issues"][0]
        assert result["passed"] is False

    def test_sprint_assignments_check_passes_when_items_in_correct_sprint(self):
        """Test sprint assignments check passes when all items in correct sprint."""
        # Arrange
        mock_adapter = Mock()
        created_items = ["TASK-001", "TASK-002"]
        sprint_number = "Sprint 5"
        config = {
            "work_tracking": {
                "project": "TestProject"
            }
        }

        # Mock adapter - correct sprint
        def mock_get_item(item_id):
            return {
                "id": item_id,
                "fields": {
                    "System.Title": f"Task {item_id}",
                    "System.Description": "A" * 600,
                    "Microsoft.VSTS.Common.AcceptanceCriteria": "- [ ] AC 1\n- [ ] AC 2\n- [ ] AC 3\n",
                    "System.IterationPath": "TestProject\\Sprint 5"
                }
            }

        mock_adapter.get_work_item = Mock(side_effect=mock_get_item)

        # Act
        result = verify_sprint_planning(mock_adapter, created_items, sprint_number, config)

        # Assert
        assert result["checks"]["sprint_assignments"]["passed"] is True
        assert result["checks"]["sprint_assignments"]["issues_count"] == 0

    def test_sprint_assignments_check_fails_when_items_in_wrong_sprint(self):
        """Test sprint assignments check fails when items in wrong sprint."""
        # Arrange
        mock_adapter = Mock()
        created_items = ["TASK-001"]
        sprint_number = "Sprint 5"
        config = {
            "work_tracking": {
                "project": "TestProject"
            }
        }

        # Mock adapter - wrong sprint
        mock_adapter.get_work_item = Mock(return_value={
            "id": "TASK-001",
            "fields": {
                "System.Title": "Task 1",
                "System.Description": "A" * 600,
                "Microsoft.VSTS.Common.AcceptanceCriteria": "- [ ] AC 1\n- [ ] AC 2\n- [ ] AC 3\n",
                "System.IterationPath": "TestProject\\Sprint 4"  # Wrong sprint
            }
        })

        # Act
        result = verify_sprint_planning(mock_adapter, created_items, sprint_number, config)

        # Assert
        assert result["checks"]["sprint_assignments"]["passed"] is False
        assert result["checks"]["sprint_assignments"]["issues_count"] == 1
        assert result["checks"]["sprint_assignments"]["assignment_issues"][0]["expected"] == "TestProject\\Sprint 5"
        assert result["checks"]["sprint_assignments"]["assignment_issues"][0]["actual"] == "TestProject\\Sprint 4"
        assert result["passed"] is False

    def test_handles_adapter_query_exceptions(self):
        """Test handles adapter query exceptions gracefully."""
        # Arrange
        mock_adapter = Mock()
        created_items = ["TASK-001"]
        sprint_number = "Sprint 5"
        config = {
            "work_tracking": {
                "project": "TestProject"
            }
        }

        # Mock adapter to raise exception
        mock_adapter.get_work_item = Mock(side_effect=Exception("Connection error"))

        # Act
        result = verify_sprint_planning(mock_adapter, created_items, sprint_number, config)

        # Assert
        assert result["passed"] is False
        assert len(result["errors"]) > 0
        assert "Connection error" in str(result["errors"])

    def test_returns_correct_dict_structure(self):
        """Test returns correct dict structure."""
        # Arrange
        mock_adapter = Mock()
        created_items = []
        sprint_number = "Sprint 5"
        config = {
            "work_tracking": {
                "project": "TestProject"
            }
        }

        mock_adapter.get_work_item = Mock(return_value=None)

        # Act
        result = verify_sprint_planning(mock_adapter, created_items, sprint_number, config)

        # Assert
        assert "passed" in result
        assert "checks" in result
        assert "errors" in result
        assert "work_items_exist" in result["checks"]
        assert "content_quality" in result["checks"]
        assert "sprint_assignments" in result["checks"]
        assert "passed" in result["checks"]["work_items_exist"]
        assert "details" in result["checks"]["work_items_exist"]

    def test_handles_file_based_adapter_format(self):
        """Test handles file-based adapter work item format (without System.* fields)."""
        # Arrange
        mock_adapter = Mock()
        created_items = ["TASK-001"]
        sprint_number = "Sprint 5"
        config = {
            "work_tracking": {
                "project": "TestProject"
            }
        }

        # Mock file-based adapter format (flat structure)
        mock_adapter.get_work_item = Mock(return_value={
            "id": "TASK-001",
            "title": "Task 1",
            "description": "A" * 600,
            "iteration": "TestProject\\Sprint 5",
            "fields": {}
        })

        # Act
        result = verify_sprint_planning(mock_adapter, created_items, sprint_number, config)

        # Assert
        # Should handle missing fields gracefully (AC check might fail, but shouldn't crash)
        assert "passed" in result
        assert "checks" in result
        assert result["checks"]["work_items_exist"]["passed"] is True
        assert result["checks"]["sprint_assignments"]["passed"] is True
