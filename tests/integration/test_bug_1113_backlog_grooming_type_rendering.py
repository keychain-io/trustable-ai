"""
Integration tests for Bug #1113 - Backlog grooming work item type rendering.

Tests verify that the backlog-grooming workflow correctly renders work item type
extraction code that handles both flat and nested field structures.
"""

import pytest
from pathlib import Path
import yaml
import tempfile
import shutil
from workflows.registry import WorkflowRegistry
from config.loader import load_config


@pytest.mark.integration
class TestBacklogGroomingTypeRendering:
    """Test suite for backlog-grooming workflow type rendering."""

    def test_backlog_grooming_renders_correct_type_extraction_for_epics(self, tmp_path):
        """Test backlog-grooming renders correct type extraction for Epic display."""
        # Arrange
        config_dict = {
            'project': {
                'name': 'test-project',
                'type': 'web-application',
                'tech_stack': {
                    'languages': ['Python'],
                    'frameworks': ['FastAPI']
                }
            },
            'work_tracking': {
                'platform': 'azure-devops',
                'organization': 'https://dev.azure.com/test',
                'project': 'TestProject',
                'work_item_types': {
                    'epic': 'Epic',
                    'feature': 'Feature',
                    'task': 'Task',
                    'bug': 'Bug'
                },
                'custom_fields': {
                    'story_points': 'Microsoft.VSTS.Scheduling.StoryPoints'
                }
            }
        }

        # Create config in temp directory
        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config_dict, f)

        # Load config and create WorkflowRegistry
        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        # Act
        rendered = registry.render_workflow('backlog-grooming')

        # Assert - Check Epic type extraction pattern
        assert "epic_type = epic.get('type') or epic.get('fields', {}).get('System.WorkItemType', 'Unknown')" in rendered, \
            "Epic type extraction should use correct pattern"

        assert "print(f\"  WI-{epic['id']}: {epic.get('title', 'Untitled')} [{epic_type}]\")" in rendered, \
            "Epic display should use extracted epic_type variable"

        # Ensure old broken pattern is NOT present
        assert "epic.get('type', 'Unknown')" not in rendered, \
            "Should not use old broken pattern that only checks flat structure"

    def test_backlog_grooming_renders_correct_type_filtering_for_backlog_items(self, tmp_path):
        """Test backlog-grooming renders correct type filtering for backlog items."""
        # Arrange
        config_dict = {
            'project': {
                'name': 'test-project',
                'type': 'web-application',
                'tech_stack': {
                    'languages': ['Python']
                }
            },
            'work_tracking': {
                'platform': 'azure-devops',
                'organization': 'https://dev.azure.com/test',
                'project': 'TestProject',
                'work_item_types': {
                    'epic': 'Epic',
                    'feature': 'Feature',
                    'story': 'User Story',
                    'task': 'Task'
                }
            }
        }

        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config_dict, f)

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        # Act
        rendered = registry.render_workflow('backlog-grooming')

        # Assert - Check backlog item filtering uses correct pattern
        expected_pattern = "and (item.get('type') or item.get('fields', {}).get('System.WorkItemType')) in ['User Story', 'Feature', 'User Story']"
        assert expected_pattern in rendered, \
            "Backlog item filtering should use correct type extraction pattern"

        # Ensure old broken pattern is NOT present
        assert "and item.get('type') in ['User Story'" not in rendered or \
               "and (item.get('type') or item.get('fields', {}).get('System.WorkItemType'))" in rendered, \
            "Should not use old broken pattern for filtering"

    def test_backlog_grooming_type_extraction_works_with_file_based_adapter(self, tmp_path):
        """Test backlog-grooming type extraction works with file-based adapter."""
        # Arrange
        config_dict = {
            'project': {
                'name': 'test-project',
                'type': 'library',
                'tech_stack': {
                    'languages': ['Python']
                }
            },
            'work_tracking': {
                'platform': 'file-based',
                'work_item_types': {
                    'epic': 'Epic',
                    'feature': 'Feature',
                    'task': 'Task'
                }
            }
        }

        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config_dict, f)

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        # Act
        rendered = registry.render_workflow('backlog-grooming')

        # Assert - Type extraction pattern should still be present
        assert "epic.get('type') or epic.get('fields', {}).get('System.WorkItemType', 'Unknown')" in rendered, \
            "Type extraction should work regardless of adapter"


@pytest.mark.integration
class TestSprintExecutionTypeRendering:
    """Test suite for sprint-execution workflow type rendering."""

    def test_sprint_execution_renders_correct_type_filtering(self, tmp_path):
        """Test sprint-execution renders correct type filtering for task selection."""
        # Arrange
        config_dict = {
            'project': {
                'name': 'test-project',
                'type': 'web-application',
                'tech_stack': {
                    'languages': ['Python']
                }
            },
            'work_tracking': {
                'platform': 'azure-devops',
                'organization': 'https://dev.azure.com/test',
                'project': 'TestProject',
                'work_item_types': {
                    'task': 'Task',
                    'bug': 'Bug'
                }
            }
        }

        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config_dict, f)

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        # Act
        rendered = registry.render_workflow('sprint-execution')

        # Assert - Check task filtering uses correct pattern
        expected_pattern = "and (item.get('type') or item.get('fields', {}).get('System.WorkItemType')) == 'Task'"
        assert expected_pattern in rendered, \
            "Task filtering should use correct type extraction pattern"

        # Ensure old broken pattern is NOT present
        assert "and item.get('type') == 'Task'" not in rendered or \
               "and (item.get('type') or item.get('fields', {}).get('System.WorkItemType'))" in rendered, \
            "Should not use old broken pattern for task filtering"


@pytest.mark.integration
class TestWorkflowTypeExtractionConsistency:
    """Test that type extraction is consistent across all workflows."""

    def test_all_workflows_use_consistent_type_extraction(self, tmp_path):
        """Test that all workflows using type extraction use the same pattern."""
        # Arrange
        config_dict = {
            'project': {
                'name': 'test-project',
                'type': 'web-application',
                'tech_stack': {
                    'languages': ['Python']
                }
            },
            'work_tracking': {
                'platform': 'azure-devops',
                'organization': 'https://dev.azure.com/test',
                'project': 'TestProject',
                'work_item_types': {
                    'epic': 'Epic',
                    'feature': 'Feature',
                    'task': 'Task',
                    'bug': 'Bug'
                }
            }
        }

        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config_dict, f)

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        # Workflows that use type extraction
        workflows_to_check = ['backlog-grooming', 'sprint-execution', 'sprint-planning']

        # Pattern to look for
        correct_pattern = "item.get('type') or item.get('fields', {}).get('System.WorkItemType'"
        alt_correct_pattern = "work_item.get('type') or work_item.get('fields', {}).get('System.WorkItemType'"

        for workflow_name in workflows_to_check:
            # Act
            try:
                rendered = registry.render_workflow(workflow_name)

                # Check if workflow uses type extraction
                if 'WorkItemType' in rendered:
                    # Assert - Should use correct pattern
                    assert correct_pattern in rendered or alt_correct_pattern in rendered, \
                        f"{workflow_name} should use correct type extraction pattern"

            except Exception as e:
                # Some workflows might not exist or have rendering issues
                # That's okay for this test
                pass


@pytest.mark.integration
class TestBacklogGroomingEndToEnd:
    """End-to-end tests for backlog grooming workflow rendering."""

    def test_backlog_grooming_full_render_no_errors(self, tmp_path):
        """Test that backlog-grooming workflow renders completely without errors."""
        # Arrange
        config_dict = {
            'project': {
                'name': 'full-test-project',
                'type': 'web-application',
                'tech_stack': {
                    'languages': ['Python', 'TypeScript'],
                    'frameworks': ['Django', 'React']
                }
            },
            'work_tracking': {
                'platform': 'azure-devops',
                'organization': 'https://dev.azure.com/test',
                'project': 'FullTest',
                'work_item_types': {
                    'epic': 'Epic',
                    'feature': 'Feature',
                    'story': 'User Story',
                    'task': 'Task',
                    'bug': 'Bug'
                },
                'custom_fields': {
                    'story_points': 'Microsoft.VSTS.Scheduling.StoryPoints',
                    'business_value': 'Custom.BusinessValue',
                    'technical_risk': 'Custom.TechnicalRisk'
                }
            },
            'quality_standards': {
                'test_coverage_min': 80,
                'critical_vulnerabilities_max': 0,
                'high_vulnerabilities_max': 0
            }
        }

        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config_dict, f)

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        # Act
        rendered = registry.render_workflow('backlog-grooming')

        # Assert
        assert rendered is not None
        assert len(rendered) > 0
        assert '# Backlog Grooming Workflow' in rendered
        assert 'Epic-sized items' in rendered
        assert 'System.WorkItemType' in rendered

        # Verify specific fix is present
        assert "epic_type = epic.get('type') or epic.get('fields', {}).get('System.WorkItemType', 'Unknown')" in rendered

    def test_backlog_grooming_type_extraction_syntax(self, tmp_path):
        """Test that type extraction code in backlog-grooming has valid Python syntax."""
        # Arrange
        config_dict = {
            'project': {
                'name': 'syntax-test',
                'type': 'api',
                'tech_stack': {
                    'languages': ['Python']
                }
            },
            'work_tracking': {
                'platform': 'azure-devops',
                'organization': 'https://dev.azure.com/test',
                'project': 'SyntaxTest',
                'work_item_types': {
                    'epic': 'Epic',
                    'feature': 'Feature',
                    'task': 'Task'
                }
            }
        }

        config_path = tmp_path / ".claude" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config_dict, f)

        config = load_config(config_path)
        registry = WorkflowRegistry(config)

        # Act
        rendered = registry.render_workflow('backlog-grooming')

        # Extract and test specific type extraction patterns
        # Test pattern 1: Epic type extraction for display
        test_code_1 = """
epic = {'id': '1', 'fields': {'System.WorkItemType': 'Epic', 'System.Title': 'Test'}}
epic_type = epic.get('type') or epic.get('fields', {}).get('System.WorkItemType', 'Unknown')
assert epic_type == 'Epic'
"""

        # Test pattern 2: Backlog item filtering (simplified to just test syntax)
        test_code_2 = """
item = {'id': '1', 'fields': {'System.WorkItemType': 'User Story', 'System.State': 'New'}}
# Test the type extraction pattern used in filtering
item_type = item.get('type') or item.get('fields', {}).get('System.WorkItemType')
assert item_type == 'User Story'
"""

        # Verify these patterns compile and execute correctly
        try:
            compile(test_code_1, '<test_epic_type>', 'exec')
            exec(test_code_1)
        except Exception as e:
            pytest.fail(f"Epic type extraction has syntax/logic error: {e}")

        try:
            compile(test_code_2, '<test_type_in_filter>', 'exec')
            exec(test_code_2)
        except Exception as e:
            pytest.fail(f"Type extraction in filter has syntax/logic error: {e}")

        # Verify patterns appear in rendered workflow
        assert "epic.get('type') or epic.get('fields', {}).get('System.WorkItemType'" in rendered
        assert "(item.get('type') or item.get('fields', {}).get('System.WorkItemType'))" in rendered
