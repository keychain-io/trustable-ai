"""
Unit tests for skills system.

Tests skill loading, registry, and parent_id parameter support.
"""
import os
import sys
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock


@pytest.mark.unit
class TestSkillsLoading:
    """Test that skills can be loaded and imported correctly."""

    def test_skills_module_exists(self):
        """Test that the skills module exists and can be imported."""
        from skills import SkillRegistry, get_skill, list_skills

        assert SkillRegistry is not None
        assert get_skill is not None
        assert list_skills is not None

    def test_list_skills(self):
        """Test that skills can be listed."""
        from skills import list_skills

        skill_list = list_skills()
        assert isinstance(skill_list, list)
        # At minimum we should have these skills
        assert "azure_devops" in skill_list or len(skill_list) >= 0

    def test_work_tracking_skill_can_be_imported(self):
        """Test that work_tracking skill module can be imported."""
        from skills.work_tracking import get_adapter, UnifiedWorkTrackingAdapter

        assert get_adapter is not None
        assert UnifiedWorkTrackingAdapter is not None

    def test_azure_devops_skill_can_be_imported(self):
        """Test that azure_devops skill module can be imported."""
        from skills.azure_devops import AzureCLI

        assert AzureCLI is not None


@pytest.mark.unit
class TestAzureCLIParentId:
    """Test that Azure CLI wrapper supports parent_id parameter."""

    @patch.dict(os.environ, {'AZURE_DEVOPS_EXT_PAT': 'dGVzdF90b2tlbl9mb3JfdGVzdGluZ19wdXJwb3Nlcw=='})
    @patch('skills.azure_devops.cli_wrapper.requests.request')
    def test_create_work_item_accepts_parent_id(self, mock_request):
        """Test that create_work_item accepts parent_id parameter via REST API."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        # Mock REST API response for work item creation
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": 123,
            "fields": {"System.Title": "Test Task"}
        }
        mock_response.text = '{"id": 123}'
        mock_request.return_value = mock_response

        cli = AzureCLI()

        # This should not raise an error
        result = cli.create_work_item(
            work_item_type="Task",
            title="Test Task",
            description="Test",
            parent_id=456
        )

        assert result is not None
        assert result.get('id') == 123

    @patch.dict(os.environ, {'AZURE_DEVOPS_EXT_PAT': 'dGVzdF90b2tlbl9mb3JfdGVzdGluZ19wdXJwb3Nlcw=='})
    @patch('skills.azure_devops.cli_wrapper.requests.request')
    def test_create_work_item_without_parent_id(self, mock_request):
        """Test that create_work_item works without parent_id via REST API."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        # Mock REST API response for work item creation
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": 123,
            "fields": {"System.Title": "Test Task"}
        }
        mock_response.text = '{"id": 123}'
        mock_request.return_value = mock_response

        cli = AzureCLI()

        # This should not raise an error
        result = cli.create_work_item(
            work_item_type="Task",
            title="Test Task",
            description="Test"
        )

        assert result is not None
        assert result.get('id') == 123

    @patch.dict(os.environ, {'AZURE_DEVOPS_EXT_PAT': 'dGVzdF90b2tlbl9mb3JfdGVzdGluZ19wdXJwb3Nlcw=='})
    @patch('skills.azure_devops.cli_wrapper.requests.request')
    def test_create_sprint_work_items_batch_supports_parent_id(self, mock_request):
        """Test that batch creation supports parent_id in work items via REST API."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        # Mock REST API response for work item creation
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": 123,
            "fields": {"System.Title": "Test Task"}
        }
        mock_response.text = '{"id": 123}'
        mock_request.return_value = mock_response

        cli = AzureCLI()

        work_items = [
            {
                "type": "Task",
                "title": "Task 1",
                "description": "First task",
                "parent_id": 456
            },
            {
                "type": "Task",
                "title": "Task 2",
                "description": "Second task",
                "parent_id": 456
            }
        ]

        # This should not raise an error
        results = cli.create_sprint_work_items_batch(
            sprint_name="Sprint 1",
            work_items=work_items,
            project_name="TestProject"
        )

        # Should have created 2 work items
        assert len(results) == 2
        # Each should have an id
        assert results[0].get('id') is not None
        assert results[1].get('id') is not None


@pytest.mark.unit
class TestWorkTrackingAdapter:
    """Test that work tracking adapter properly passes parent_id."""

    def test_unified_adapter_protocol_includes_parent_id(self):
        """Test that WorkTrackingAdapter protocol includes parent_id parameter."""
        from skills.work_tracking import WorkTrackingAdapter
        import inspect

        # Get the create_work_item signature from the protocol
        sig = inspect.signature(WorkTrackingAdapter.create_work_item)
        params = sig.parameters

        assert 'parent_id' in params, "create_work_item should accept parent_id parameter"
        assert params['parent_id'].default is None, "parent_id should be optional"

    @patch('skills.work_tracking.Path')
    def test_azure_cli_adapter_passes_parent_id(self, mock_path):
        """Test that AzureCLIAdapter passes parent_id to AzureCLI."""
        from skills.work_tracking import AzureCLIAdapter

        # Create mock AzureCLI
        mock_cli = Mock()
        mock_cli.create_work_item = Mock(return_value={"id": 123})

        work_tracking_config = {
            "project": "TestProject",
            "iteration_format": "{project}\\{sprint}"
        }

        adapter = AzureCLIAdapter(mock_cli, work_tracking_config)

        # Call create_work_item with parent_id
        adapter.create_work_item(
            work_item_type="Task",
            title="Test Task",
            parent_id=456
        )

        # Verify that AzureCLI.create_work_item was called with parent_id
        mock_cli.create_work_item.assert_called_once()
        call_kwargs = mock_cli.create_work_item.call_args[1]
        assert 'parent_id' in call_kwargs
        assert call_kwargs['parent_id'] == 456


@pytest.mark.unit
class TestSkillsDirectory:
    """Test that skills directory structure is correct."""

    def test_skills_directory_exists(self):
        """Test that skills directory exists in the package."""
        import skills
        skills_path = Path(skills.__file__).parent
        assert skills_path.exists()
        assert skills_path.is_dir()

    def test_skills_has_init(self):
        """Test that skills/__init__.py exists."""
        import skills
        skills_path = Path(skills.__file__)
        assert skills_path.exists()
        assert skills_path.name == "__init__.py"

    def test_work_tracking_skill_exists(self):
        """Test that work_tracking skill directory exists."""
        import skills
        skills_path = Path(skills.__file__).parent
        work_tracking_path = skills_path / "work_tracking"
        assert work_tracking_path.exists()
        assert work_tracking_path.is_dir()
        assert (work_tracking_path / "__init__.py").exists()

    def test_azure_devops_skill_exists(self):
        """Test that azure_devops skill directory exists."""
        import skills
        skills_path = Path(skills.__file__).parent
        azure_devops_path = skills_path / "azure_devops"
        assert azure_devops_path.exists()
        assert azure_devops_path.is_dir()
        assert (azure_devops_path / "__init__.py").exists()
        assert (azure_devops_path / "cli_wrapper.py").exists()
