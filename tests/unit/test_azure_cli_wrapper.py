"""
Unit tests for Azure CLI wrapper refactoring (Bug #1041).

Tests that the refactored cli_wrapper maintains all functionality
from both the adapter and skills versions, with no regressions.

Key scenarios tested:
1. Single source of truth - skills/azure_devops/cli_wrapper.py
2. Adapters properly re-export from skills
3. Parent_id parameter support (Bug #1073 fix)
4. All convenience functions work
5. Verification functions work
6. File attachment functions work
"""
import pytest
from unittest.mock import Mock, patch, MagicMock


@pytest.mark.unit
class TestCliWrapperRefactoring:
    """Test that cli_wrapper refactoring maintains all functionality."""

    def test_skills_cli_wrapper_is_canonical_source(self):
        """Test that skills/azure_devops/cli_wrapper.py exists and is importable."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        assert AzureCLI is not None

    def test_adapters_cli_wrapper_imports_from_skills(self):
        """Test that adapters/azure_devops/cli_wrapper.py imports from skills."""
        from adapters.azure_devops import cli_wrapper as adapter_cli
        from skills.azure_devops import cli_wrapper as skills_cli

        # Should be the same class
        assert adapter_cli.AzureCLI is skills_cli.AzureCLI

    def test_deployed_skills_cli_wrapper_matches_source(self):
        """Test that .claude/skills/azure_devops/cli_wrapper.py matches source."""
        from pathlib import Path

        source_path = Path(__file__).parent.parent.parent / "skills" / "azure_devops" / "cli_wrapper.py"
        deployed_path = Path(__file__).parent.parent.parent / ".claude" / "skills" / "azure_devops" / "cli_wrapper.py"

        # Both should exist
        assert source_path.exists(), "Source cli_wrapper.py should exist"
        assert deployed_path.exists(), "Deployed cli_wrapper.py should exist"

        # Should have same size (indicating same content)
        source_size = source_path.stat().st_size
        deployed_size = deployed_path.stat().st_size

        assert source_size == deployed_size, (
            f"Deployed cli_wrapper ({deployed_size} bytes) should match source ({source_size} bytes). "
            f"Run 'cp skills/azure_devops/cli_wrapper.py .claude/skills/azure_devops/cli_wrapper.py'"
        )


@pytest.mark.unit
class TestParentIdSupport:
    """Test that parent_id parameter works correctly (Bug #1073)."""

    @patch('skills.azure_devops.cli_wrapper.subprocess.run')
    def test_create_work_item_with_parent_id(self, mock_run):
        """Test create_work_item with parent_id links to parent."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        # Mock config check
        mock_config = Mock()
        mock_config.returncode = 0
        mock_config.stdout = "organization=https://dev.azure.com/test\nproject=Test"

        # Mock create
        mock_create = Mock()
        mock_create.returncode = 0
        mock_create.stdout = '{"id": 123, "fields": {"System.Title": "Child Task"}}'

        # Mock link
        mock_link = Mock()
        mock_link.returncode = 0
        mock_link.stdout = '{"success": true}'

        # Mock get (after link)
        mock_get = Mock()
        mock_get.returncode = 0
        mock_get.stdout = '{"id": 123, "fields": {"System.Title": "Child Task"}, "relations": [{"rel": "System.LinkTypes.Hierarchy-Reverse", "url": "parent/456"}]}'

        mock_run.side_effect = [mock_config, mock_create, mock_link, mock_get]

        cli = AzureCLI()
        result = cli.create_work_item(
            work_item_type="Task",
            title="Child Task",
            parent_id=456
        )

        assert result['id'] == 123
        # Verify link was called
        assert mock_run.call_count >= 3  # config, create, link

    @patch('skills.azure_devops.cli_wrapper.subprocess.run')
    def test_create_work_item_without_parent_id(self, mock_run):
        """Test create_work_item without parent_id skips linking."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        # Mock config check
        mock_config = Mock()
        mock_config.returncode = 0
        mock_config.stdout = "organization=https://dev.azure.com/test\nproject=Test"

        # Mock create
        mock_create = Mock()
        mock_create.returncode = 0
        mock_create.stdout = '{"id": 123, "fields": {"System.Title": "Standalone Task"}}'

        mock_run.side_effect = [mock_config, mock_create]

        cli = AzureCLI()
        result = cli.create_work_item(
            work_item_type="Task",
            title="Standalone Task"
        )

        assert result['id'] == 123
        # Should not call link
        assert mock_run.call_count == 2  # config, create only

    @patch('skills.azure_devops.cli_wrapper.subprocess.run')
    def test_batch_creation_with_parent_ids(self, mock_run):
        """Test batch creation supports parent_id in work items."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        def mock_subprocess(*args, **kwargs):
            cmd = args[0] if args else kwargs.get('cmd', [])

            if 'configure' in cmd:
                result = Mock()
                result.returncode = 0
                result.stdout = "organization=https://dev.azure.com/test\nproject=Test"
                return result

            if 'create' in cmd:
                result = Mock()
                result.returncode = 0
                result.stdout = '{"id": 100, "fields": {"System.Title": "Task"}}'
                return result

            if 'relation' in cmd:
                result = Mock()
                result.returncode = 0
                result.stdout = '{"success": true}'
                return result

            if 'show' in cmd:
                result = Mock()
                result.returncode = 0
                result.stdout = '{"id": 100, "fields": {"System.Title": "Task"}}'
                return result

            result = Mock()
            result.returncode = 0
            result.stdout = '{}'
            return result

        mock_run.side_effect = mock_subprocess

        cli = AzureCLI()
        work_items = [
            {"type": "Task", "title": "Task 1", "parent_id": 456},
            {"type": "Task", "title": "Task 2", "parent_id": 456}
        ]

        results = cli.create_sprint_work_items_batch(
            sprint_name="Sprint 1",
            work_items=work_items
        )

        assert len(results) == 2


@pytest.mark.unit
class TestConvenienceFunctions:
    """Test that all convenience functions are available and importable."""

    def test_convenience_functions_exist(self):
        """Test that all convenience functions exist and are importable."""
        from skills.azure_devops import cli_wrapper

        # Check all convenience functions exist
        assert hasattr(cli_wrapper, 'query_work_items')
        assert hasattr(cli_wrapper, 'create_work_item')
        assert hasattr(cli_wrapper, 'update_work_item')
        assert hasattr(cli_wrapper, 'add_comment')
        assert hasattr(cli_wrapper, 'create_pull_request')
        assert hasattr(cli_wrapper, 'approve_pull_request')
        assert hasattr(cli_wrapper, 'create_sprint')
        assert hasattr(cli_wrapper, 'list_sprints')
        assert hasattr(cli_wrapper, 'update_sprint_dates')
        assert hasattr(cli_wrapper, 'create_sprint_work_items')
        assert hasattr(cli_wrapper, 'query_sprint_work_items')

    def test_convenience_functions_are_callable(self):
        """Test that all convenience functions are callable."""
        from skills.azure_devops import cli_wrapper

        # All should be callable
        assert callable(cli_wrapper.query_work_items)
        assert callable(cli_wrapper.create_work_item)
        assert callable(cli_wrapper.update_work_item)
        assert callable(cli_wrapper.add_comment)
        assert callable(cli_wrapper.create_pull_request)
        assert callable(cli_wrapper.approve_pull_request)
        assert callable(cli_wrapper.create_sprint)
        assert callable(cli_wrapper.list_sprints)
        assert callable(cli_wrapper.update_sprint_dates)
        assert callable(cli_wrapper.create_sprint_work_items)
        assert callable(cli_wrapper.query_sprint_work_items)

    def test_singleton_instance_exists(self):
        """Test that azure_cli singleton instance exists."""
        from skills.azure_devops import cli_wrapper

        assert hasattr(cli_wrapper, 'azure_cli')
        assert cli_wrapper.azure_cli is not None


@pytest.mark.unit
class TestVerificationFunctions:
    """Test that verification functions work correctly."""

    @patch('skills.azure_devops.cli_wrapper.subprocess.run')
    def test_verify_work_item_created(self, mock_run):
        """Test verify_work_item_created returns correct verification data."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        # Mock config
        mock_config = Mock()
        mock_config.returncode = 0
        mock_config.stdout = "organization=https://dev.azure.com/test\nproject=Test"

        # Mock get work item
        mock_get = Mock()
        mock_get.returncode = 0
        mock_get.stdout = '{"id": 123, "fields": {"System.Title": "Test Task", "System.State": "New", "System.WorkItemType": "Task"}}'

        mock_run.side_effect = [mock_config, mock_get]

        cli = AzureCLI()
        verification = cli.verify_work_item_created(123, expected_title="Test Task")

        assert verification['success'] is True
        assert verification['operation'] == "verify_work_item_created"
        assert verification['verification']['exists'] is True
        assert verification['verification']['title'] == "Test Task"

    @patch('skills.azure_devops.cli_wrapper.subprocess.run')
    def test_verify_work_item_updated(self, mock_run):
        """Test verify_work_item_updated checks field values."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        # Mock config
        mock_config = Mock()
        mock_config.returncode = 0
        mock_config.stdout = "organization=https://dev.azure.com/test\nproject=Test"

        # Mock get work item
        mock_get = Mock()
        mock_get.returncode = 0
        mock_get.stdout = '{"id": 123, "fields": {"System.State": "Done", "System.IterationPath": "Project\\\\Sprint 1"}}'

        mock_run.side_effect = [mock_config, mock_get]

        cli = AzureCLI()
        verification = cli.verify_work_item_updated(
            123,
            expected_fields={"System.State": "Done", "System.IterationPath": "Project\\Sprint 1"}
        )

        assert verification['success'] is True
        assert verification['verification']['all_fields_match'] is True

    @patch('skills.azure_devops.cli_wrapper.subprocess.run')
    def test_create_with_verify_flag(self, mock_run):
        """Test create_work_item with verify=True returns verification result."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        # Mock config
        mock_config = Mock()
        mock_config.returncode = 0
        mock_config.stdout = "organization=https://dev.azure.com/test\nproject=Test"

        # Mock create
        mock_create = Mock()
        mock_create.returncode = 0
        mock_create.stdout = '{"id": 123, "fields": {"System.Title": "Test"}}'

        # Mock get (for verification)
        mock_get = Mock()
        mock_get.returncode = 0
        mock_get.stdout = '{"id": 123, "fields": {"System.Title": "Test", "System.State": "New"}}'

        mock_run.side_effect = [mock_config, mock_create, mock_get]

        cli = AzureCLI()
        result = cli.create_work_item(
            work_item_type="Task",
            title="Test",
            verify=True
        )

        # Should return verification result, not raw work item
        assert 'success' in result
        assert 'operation' in result
        assert 'verification' in result


@pytest.mark.unit
class TestFileAttachments:
    """Test file attachment functionality."""

    @patch('skills.azure_devops.cli_wrapper.subprocess.run')
    def test_verify_attachment_exists(self, mock_run):
        """Test verify_attachment_exists checks work item relations."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        # Mock config
        mock_config = Mock()
        mock_config.returncode = 0
        mock_config.stdout = "organization=https://dev.azure.com/test\nproject=Test"

        # Mock get work item with attachment
        mock_get = Mock()
        mock_get.returncode = 0
        mock_get.stdout = '''{
            "id": 123,
            "relations": [
                {
                    "rel": "AttachedFile",
                    "url": "https://dev.azure.com/test/_apis/wit/attachments/test.pdf",
                    "attributes": {"name": "test.pdf"}
                }
            ]
        }'''

        mock_run.side_effect = [mock_config, mock_get]

        cli = AzureCLI()
        exists = cli.verify_attachment_exists(123, "test.pdf")

        assert exists is True

    @patch('skills.azure_devops.cli_wrapper.subprocess.run')
    def test_verify_attachment_not_exists(self, mock_run):
        """Test verify_attachment_exists returns False when attachment missing."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        # Mock config
        mock_config = Mock()
        mock_config.returncode = 0
        mock_config.stdout = "organization=https://dev.azure.com/test\nproject=Test"

        # Mock get work item without attachments
        mock_get = Mock()
        mock_get.returncode = 0
        mock_get.stdout = '{"id": 123, "relations": []}'

        mock_run.side_effect = [mock_config, mock_get]

        cli = AzureCLI()
        exists = cli.verify_attachment_exists(123, "missing.pdf")

        assert exists is False


@pytest.mark.unit
class TestIdempotentCreation:
    """Test idempotent work item creation."""

    @patch('skills.azure_devops.cli_wrapper.subprocess.run')
    def test_idempotent_creation_finds_existing(self, mock_run):
        """Test create_work_item_idempotent returns existing item if found."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        # Mock config
        mock_config = Mock()
        mock_config.returncode = 0
        mock_config.stdout = "organization=https://dev.azure.com/test\nproject=Test"

        # Mock query that finds existing item
        mock_query = Mock()
        mock_query.returncode = 0
        mock_query.stdout = '[{"id": 456, "fields": {"System.Title": "Existing Task"}}]'

        # Mock get work item
        mock_get = Mock()
        mock_get.returncode = 0
        mock_get.stdout = '{"id": 456, "fields": {"System.Title": "Existing Task"}}'

        mock_run.side_effect = [mock_config, mock_query, mock_get]

        cli = AzureCLI()
        result = cli.create_work_item_idempotent(
            title="Existing Task",
            work_item_type="Task",
            sprint_name="Sprint 1"
        )

        assert result['id'] == 456
        assert result['existing'] is True
        assert result['created'] is False

    @patch('skills.azure_devops.cli_wrapper.subprocess.run')
    def test_idempotent_creation_creates_new(self, mock_run):
        """Test create_work_item_idempotent creates new item if not found."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        # Mock config
        mock_config = Mock()
        mock_config.returncode = 0
        mock_config.stdout = "organization=https://dev.azure.com/test\nproject=Test"

        # Mock query that finds nothing
        mock_query = Mock()
        mock_query.returncode = 0
        mock_query.stdout = '[]'

        # Mock create
        mock_create = Mock()
        mock_create.returncode = 0
        mock_create.stdout = '{"id": 789, "fields": {"System.Title": "New Task"}}'

        # Mock update (for iteration)
        mock_update = Mock()
        mock_update.returncode = 0
        mock_update.stdout = '{}'

        # Mock get (after update)
        mock_get = Mock()
        mock_get.returncode = 0
        mock_get.stdout = '{"id": 789, "fields": {"System.Title": "New Task"}}'

        mock_run.side_effect = [mock_config, mock_query, mock_create, mock_update, mock_get]

        cli = AzureCLI()
        result = cli.create_work_item_idempotent(
            title="New Task",
            work_item_type="Task",
            sprint_name="Sprint 1"
        )

        assert result['id'] == 789
        assert result['created'] is True
        assert result['existing'] is False


@pytest.mark.unit
class TestAdapterCompatibility:
    """Test that adapter re-exports work correctly."""

    def test_adapter_exports_all_functions(self):
        """Test that adapter cli_wrapper exports all expected functions."""
        from adapters.azure_devops import cli_wrapper

        # Check all expected exports exist
        assert hasattr(cli_wrapper, 'AzureCLI')
        assert hasattr(cli_wrapper, 'azure_cli')
        assert hasattr(cli_wrapper, 'query_work_items')
        assert hasattr(cli_wrapper, 'create_work_item')
        assert hasattr(cli_wrapper, 'update_work_item')
        assert hasattr(cli_wrapper, 'add_comment')
        assert hasattr(cli_wrapper, 'create_pull_request')
        assert hasattr(cli_wrapper, 'approve_pull_request')
        assert hasattr(cli_wrapper, 'create_sprint')
        assert hasattr(cli_wrapper, 'list_sprints')
        assert hasattr(cli_wrapper, 'update_sprint_dates')
        assert hasattr(cli_wrapper, 'create_sprint_work_items')
        assert hasattr(cli_wrapper, 'query_sprint_work_items')

    def test_adapter_imports_match_skills(self):
        """Test that adapter exports are the same objects as skills exports."""
        from adapters.azure_devops.cli_wrapper import (
            AzureCLI as AdapterCLI,
            query_work_items as adapter_query,
            create_work_item as adapter_create
        )
        from skills.azure_devops.cli_wrapper import (
            AzureCLI as SkillsCLI,
            query_work_items as skills_query,
            create_work_item as skills_create
        )

        # Should be the exact same objects
        assert AdapterCLI is SkillsCLI
        assert adapter_query is skills_query
        assert adapter_create is skills_create
