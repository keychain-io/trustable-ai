"""
Unit tests for Bug #1113 - Work item type extraction fix.

Tests verify that work item type extraction correctly handles both flat and nested
field structures returned by Azure DevOps and other adapters.
"""

import pytest
from unittest.mock import Mock


@pytest.mark.unit
class TestWorkItemTypeExtraction:
    """Test suite for work item type extraction patterns."""

    def test_type_extraction_from_flat_structure(self):
        """Test type extraction when 'type' field is at root level."""
        # Arrange
        work_item = {
            'id': '1',
            'type': 'Task',
            'title': 'Test Task',
            'state': 'Active'
        }

        # Act
        item_type = work_item.get('type') or work_item.get('fields', {}).get('System.WorkItemType', 'Unknown')

        # Assert
        assert item_type == 'Task'

    def test_type_extraction_from_nested_structure(self):
        """Test type extraction when type is in fields.System.WorkItemType (Azure DevOps)."""
        # Arrange
        work_item = {
            'id': '1',
            'fields': {
                'System.WorkItemType': 'Bug',
                'System.Title': 'Test Bug',
                'System.State': 'Active'
            }
        }

        # Act
        item_type = work_item.get('type') or work_item.get('fields', {}).get('System.WorkItemType', 'Unknown')

        # Assert
        assert item_type == 'Bug'

    def test_type_extraction_missing_both_fields(self):
        """Test type extraction falls back to 'Unknown' when both fields missing."""
        # Arrange
        work_item = {
            'id': '1',
            'title': 'Test Item',
            'state': 'Active'
        }

        # Act
        item_type = work_item.get('type') or work_item.get('fields', {}).get('System.WorkItemType', 'Unknown')

        # Assert
        assert item_type == 'Unknown'

    def test_type_extraction_empty_fields_dict(self):
        """Test type extraction when fields dict exists but is empty."""
        # Arrange
        work_item = {
            'id': '1',
            'title': 'Test Item',
            'state': 'Active',
            'fields': {}
        }

        # Act
        item_type = work_item.get('type') or work_item.get('fields', {}).get('System.WorkItemType', 'Unknown')

        # Assert
        assert item_type == 'Unknown'

    def test_type_extraction_flat_takes_precedence(self):
        """Test that flat 'type' field takes precedence over nested field."""
        # Arrange
        work_item = {
            'id': '1',
            'type': 'Feature',
            'fields': {
                'System.WorkItemType': 'Epic'
            }
        }

        # Act
        item_type = work_item.get('type') or work_item.get('fields', {}).get('System.WorkItemType', 'Unknown')

        # Assert
        assert item_type == 'Feature'  # Flat structure takes precedence

    def test_type_extraction_none_type_uses_nested(self):
        """Test that None type falls back to nested field."""
        # Arrange
        work_item = {
            'id': '1',
            'type': None,
            'fields': {
                'System.WorkItemType': 'Task'
            }
        }

        # Act
        item_type = work_item.get('type') or work_item.get('fields', {}).get('System.WorkItemType', 'Unknown')

        # Assert
        assert item_type == 'Task'

    def test_type_extraction_empty_string_uses_nested(self):
        """Test that empty string type falls back to nested field."""
        # Arrange
        work_item = {
            'id': '1',
            'type': '',
            'fields': {
                'System.WorkItemType': 'Bug'
            }
        }

        # Act
        item_type = work_item.get('type') or work_item.get('fields', {}).get('System.WorkItemType', 'Unknown')

        # Assert
        assert item_type == 'Bug'

    def test_type_filtering_in_list_comprehension(self):
        """Test type-based filtering works with both flat and nested structures."""
        # Arrange
        work_items = [
            {'id': '1', 'type': 'Task', 'state': 'Active'},
            {'id': '2', 'fields': {'System.WorkItemType': 'Task', 'System.State': 'Active'}},
            {'id': '3', 'type': 'Bug', 'state': 'Active'},
            {'id': '4', 'fields': {'System.WorkItemType': 'Feature', 'System.State': 'Active'}}
        ]

        # Act
        tasks = [
            item for item in work_items
            if (item.get('type') or item.get('fields', {}).get('System.WorkItemType')) == 'Task'
        ]

        # Assert
        assert len(tasks) == 2
        assert tasks[0]['id'] == '1'
        assert tasks[1]['id'] == '2'

    def test_type_filtering_in_list_comprehension_multiple_types(self):
        """Test type-based filtering with multiple allowed types."""
        # Arrange
        work_items = [
            {'id': '1', 'type': 'User Story', 'state': 'New'},
            {'id': '2', 'fields': {'System.WorkItemType': 'Feature', 'System.State': 'New'}},
            {'id': '3', 'type': 'Task', 'state': 'New'},
            {'id': '4', 'fields': {'System.WorkItemType': 'Bug', 'System.State': 'New'}}
        ]

        # Act
        backlog_items = [
            item for item in work_items
            if (item.get('type') or item.get('fields', {}).get('System.WorkItemType'))
            in ['User Story', 'Feature']
        ]

        # Assert
        assert len(backlog_items) == 2
        assert backlog_items[0]['id'] == '1'
        assert backlog_items[1]['id'] == '2'

    def test_type_extraction_for_display(self):
        """Test type extraction for display in workflow output."""
        # Arrange
        epics = [
            {
                'id': '100',
                'title': 'Epic 1',
                'type': 'Epic'
            },
            {
                'id': '101',
                'title': 'Epic 2',
                'fields': {
                    'System.WorkItemType': 'Epic',
                    'System.Title': 'Epic 2'
                }
            },
            {
                'id': '102',
                'title': 'Epic 3',
                'fields': {}
            }
        ]

        # Act & Assert
        for epic in epics:
            epic_type = epic.get('type') or epic.get('fields', {}).get('System.WorkItemType', 'Unknown')
            if epic['id'] == '100':
                assert epic_type == 'Epic'
            elif epic['id'] == '101':
                assert epic_type == 'Epic'
            elif epic['id'] == '102':
                assert epic_type == 'Unknown'


@pytest.mark.unit
class TestWorkflowUtilitiesTypeExtraction:
    """Test that workflow utilities correctly extract work item types."""

    def test_analyze_sprint_extracts_type_from_nested_structure(self):
        """Test analyze_sprint correctly extracts type from nested fields."""
        # This is tested in test_workflow_utilities.py
        # Just verify the pattern matches what we use in utilities.py
        work_item = {
            'id': '1',
            'state': 'Active',
            'fields': {
                'System.WorkItemType': 'Task'
            }
        }

        # The pattern used in workflows/utilities.py line 98
        item_type = work_item.get('type', work_item.get('fields', {}).get('System.WorkItemType', 'Unknown'))

        assert item_type == 'Task'

    def test_get_recent_activity_extracts_type_from_nested_structure(self):
        """Test get_recent_activity correctly extracts type from nested fields."""
        # This is tested in test_workflow_utilities.py
        # Just verify the pattern matches what we use in utilities.py
        work_item = {
            'id': '1',
            'title': 'Test',
            'state': 'Active',
            'fields': {
                'System.WorkItemType': 'Bug',
                'System.Title': 'Test Bug'
            }
        }

        # The pattern used in workflows/utilities.py line 384
        item_type = work_item.get('type', work_item.get('fields', {}).get('System.WorkItemType', 'Unknown'))

        assert item_type == 'Bug'

    def test_type_extraction_pattern_consistency(self):
        """Test that type extraction pattern is consistent across codebase."""
        # Pattern 1: Using 'or' (used in templates)
        work_item_1 = {'fields': {'System.WorkItemType': 'Task'}}
        type_1 = work_item_1.get('type') or work_item_1.get('fields', {}).get('System.WorkItemType', 'Unknown')

        # Pattern 2: Using default parameter (used in utilities)
        work_item_2 = {'fields': {'System.WorkItemType': 'Task'}}
        type_2 = work_item_2.get('type', work_item_2.get('fields', {}).get('System.WorkItemType', 'Unknown'))

        # Both patterns should produce same result
        assert type_1 == 'Task'
        assert type_2 == 'Task'
        assert type_1 == type_2
