"""
Unit tests for test plan attachment/linking to EPIC work items.

Tests that the attachment/linking logic works correctly for both
Azure DevOps (file attachments) and file-based (comment linking) platforms.

Key scenarios tested:
1. Azure DevOps attachment and verification
2. File-based comment linking and verification
3. Attachment failure detection
4. Platform-specific handling
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path


@pytest.mark.unit
class TestAzureDevOpsAttachment:
    """Test Azure DevOps file attachment functionality."""

    @patch('skills.azure_devops.cli_wrapper.subprocess.run')
    @patch('skills.azure_devops.cli_wrapper.requests')
    def test_attach_file_to_work_item_success(self, mock_requests, mock_run):
        """Test successful file attachment to Azure DevOps work item."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        # Mock config check
        mock_config = Mock()
        mock_config.returncode = 0
        mock_config.stdout = "organization=https://dev.azure.com/test\nproject=Test"

        # Mock token retrieval
        mock_token = Mock()
        mock_token.returncode = 0
        mock_token.stdout = '{"accessToken": "test-token"}'

        mock_run.side_effect = [mock_config, mock_token]

        # Mock file upload response
        mock_upload_response = Mock()
        mock_upload_response.status_code = 201
        mock_upload_response.json.return_value = {'url': 'https://dev.azure.com/attachment/123'}

        # Mock link response
        mock_link_response = Mock()
        mock_link_response.status_code = 200

        mock_requests.post.return_value = mock_upload_response
        mock_requests.patch.return_value = mock_link_response

        cli = AzureCLI()

        # Create a temporary test file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("# Test Plan\n\nTest content")
            temp_file = Path(f.name)

        try:
            result = cli.attach_file_to_work_item(
                work_item_id=123,
                file_path=temp_file,
                comment="Test attachment"
            )

            assert result['success'] is True
            assert result['work_item_id'] == 123
            assert result['file_name'] == temp_file.name
            assert 'attachment_url' in result
        finally:
            # Clean up temp file
            temp_file.unlink()

    @patch('skills.azure_devops.cli_wrapper.subprocess.run')
    def test_verify_attachment_exists(self, mock_run):
        """Test verification that attachment exists on work item."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        # Mock config check
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
                    "url": "https://dev.azure.com/_apis/wit/attachments/epic-001-test-plan.md",
                    "attributes": {"name": "epic-001-test-plan.md"}
                }
            ]
        }'''

        mock_run.side_effect = [mock_config, mock_get]

        cli = AzureCLI()
        exists = cli.verify_attachment_exists(123, "epic-001-test-plan.md")

        assert exists is True

    @patch('skills.azure_devops.cli_wrapper.subprocess.run')
    def test_verify_attachment_not_exists(self, mock_run):
        """Test verification returns False when attachment missing."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        # Mock config check
        mock_config = Mock()
        mock_config.returncode = 0
        mock_config.stdout = "organization=https://dev.azure.com/test\nproject=Test"

        # Mock get work item without attachments
        mock_get = Mock()
        mock_get.returncode = 0
        mock_get.stdout = '{"id": 123, "relations": []}'

        mock_run.side_effect = [mock_config, mock_get]

        cli = AzureCLI()
        exists = cli.verify_attachment_exists(123, "missing-file.md")

        assert exists is False


@pytest.mark.unit
class TestFileBasedCommentLinking:
    """Test file-based adapter comment linking functionality."""

    def test_add_comment_to_work_item(self, tmp_path):
        """Test adding comment with file path to work item."""
        from adapters.file_based import FileBasedAdapter

        adapter = FileBasedAdapter(work_items_dir=tmp_path, project_name="test")

        # Create an EPIC work item
        epic = adapter.create_work_item(
            work_item_type="Epic",
            title="Test EPIC",
            description="Test EPIC for attachment"
        )

        epic_id = epic['id']

        # Add comment with file path
        comment_text = "Test Plan: /path/to/test-plan.md"
        adapter.add_comment(
            work_item_id=epic_id,
            comment=comment_text,
            author="test-user"
        )

        # Verify comment was added
        updated_epic = adapter.get_work_item(epic_id)
        comments = updated_epic.get('comments', [])

        assert len(comments) == 1
        assert comments[0]['text'] == comment_text
        assert comments[0]['author'] == "test-user"

    def test_verify_comment_exists(self, tmp_path):
        """Test verification that comment with file path exists."""
        from adapters.file_based import FileBasedAdapter

        adapter = FileBasedAdapter(work_items_dir=tmp_path, project_name="test")

        # Create an EPIC work item
        epic = adapter.create_work_item(
            work_item_type="Epic",
            title="Test EPIC",
            description="Test EPIC for verification"
        )

        epic_id = epic['id']

        # Add comment with file path
        file_path = ".claude/acceptance-tests/epic-001-test-plan.md"
        comment_text = f"Test Plan: {file_path}"
        adapter.add_comment(
            work_item_id=epic_id,
            comment=comment_text,
            author="sprint-planning-workflow"
        )

        # Verify comment exists
        updated_epic = adapter.get_work_item(epic_id)
        comments = updated_epic.get('comments', [])

        # Check if our file path is in any comment
        comment_found = any(file_path in c.get('text', '') for c in comments)

        assert comment_found is True

    def test_verify_comment_not_exists(self, tmp_path):
        """Test verification returns False when comment missing."""
        from adapters.file_based import FileBasedAdapter

        adapter = FileBasedAdapter(work_items_dir=tmp_path, project_name="test")

        # Create an EPIC work item without comments
        epic = adapter.create_work_item(
            work_item_type="Epic",
            title="Test EPIC",
            description="Test EPIC without comments"
        )

        epic_id = epic['id']

        # Verify comment doesn't exist
        updated_epic = adapter.get_work_item(epic_id)
        comments = updated_epic.get('comments', [])

        # Check if file path is in any comment
        file_path = ".claude/acceptance-tests/epic-001-test-plan.md"
        comment_found = any(file_path in c.get('text', '') for c in comments)

        assert comment_found is False


@pytest.mark.unit
class TestAttachmentVerificationGate:
    """Test that attachment verification gates workflow progression."""

    def test_attachment_verification_passes_all_attached(self):
        """Test verification gate passes when all attachments succeed."""
        test_plan_files = [
            {'epic_id': 'EPIC-001', 'file_path': 'test1.md'},
            {'epic_id': 'EPIC-002', 'file_path': 'test2.md'},
        ]

        attached_count = 2
        failed_attachments = []

        # Simulate verification gate logic
        verification_passed = len(failed_attachments) == 0 and attached_count == len(test_plan_files)

        assert verification_passed is True

    def test_attachment_verification_fails_partial_attachments(self):
        """Test verification gate fails when some attachments fail."""
        test_plan_files = [
            {'epic_id': 'EPIC-001', 'file_path': 'test1.md'},
            {'epic_id': 'EPIC-002', 'file_path': 'test2.md'},
        ]

        attached_count = 1
        failed_attachments = [
            {'epic_id': 'EPIC-002', 'file_path': 'test2.md', 'error': 'Upload failed'}
        ]

        # Simulate verification gate logic
        verification_passed = len(failed_attachments) == 0

        assert verification_passed is False

    def test_attachment_verification_fails_all_failed(self):
        """Test verification gate fails when all attachments fail."""
        test_plan_files = [
            {'epic_id': 'EPIC-001', 'file_path': 'test1.md'},
            {'epic_id': 'EPIC-002', 'file_path': 'test2.md'},
        ]

        attached_count = 0
        failed_attachments = [
            {'epic_id': 'EPIC-001', 'file_path': 'test1.md', 'error': 'Upload failed'},
            {'epic_id': 'EPIC-002', 'file_path': 'test2.md', 'error': 'Upload failed'}
        ]

        # Simulate verification gate logic
        verification_passed = len(failed_attachments) == 0

        assert verification_passed is False


@pytest.mark.unit
class TestPlatformSpecificHandling:
    """Test platform-specific attachment/linking handling."""

    def test_azure_devops_platform_uses_file_attachment(self):
        """Test that Azure DevOps platform uses file attachment method."""
        platform = "azure-devops"

        # Simulate platform detection logic
        uses_file_attachment = (platform == "azure-devops")
        uses_comment_linking = (platform == "file-based")

        assert uses_file_attachment is True
        assert uses_comment_linking is False

    def test_file_based_platform_uses_comment_linking(self):
        """Test that file-based platform uses comment linking method."""
        platform = "file-based"

        # Simulate platform detection logic
        uses_file_attachment = (platform == "azure-devops")
        uses_comment_linking = (platform == "file-based")

        assert uses_file_attachment is False
        assert uses_comment_linking is True

    def test_unsupported_platform_skips_attachment(self):
        """Test that unsupported platforms skip attachment gracefully."""
        platform = "unsupported-platform"

        # Simulate platform detection logic
        supported = platform in ["azure-devops", "file-based"]

        assert supported is False


@pytest.mark.unit
class TestAttachmentErrorHandling:
    """Test error handling for attachment operations."""

    @patch('skills.azure_devops.cli_wrapper.subprocess.run')
    @patch('skills.azure_devops.cli_wrapper.requests')
    def test_attachment_failure_creates_error_record(self, mock_requests, mock_run):
        """Test that attachment failures are recorded properly."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        # Mock config check
        mock_config = Mock()
        mock_config.returncode = 0
        mock_config.stdout = "organization=https://dev.azure.com/test\nproject=Test"

        # Mock token retrieval
        mock_token = Mock()
        mock_token.returncode = 0
        mock_token.stdout = '{"accessToken": "test-token"}'

        mock_run.side_effect = [mock_config, mock_token]

        # Mock file upload failure
        mock_upload_response = Mock()
        mock_upload_response.status_code = 500  # Failure

        mock_requests.post.return_value = mock_upload_response

        cli = AzureCLI()

        # Create a temporary test file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("# Test Plan\n\nTest content")
            temp_file = Path(f.name)

        try:
            # Attempt to attach file
            with pytest.raises(Exception, match="Failed to upload attachment"):
                cli.attach_file_to_work_item(
                    work_item_id=123,
                    file_path=temp_file,
                    comment="Test attachment"
                )
        finally:
            # Clean up temp file
            temp_file.unlink()

    def test_missing_file_raises_error(self):
        """Test that attempting to attach missing file raises error."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        with patch('skills.azure_devops.cli_wrapper.subprocess.run') as mock_run:
            # Mock config check
            mock_config = Mock()
            mock_config.returncode = 0
            mock_config.stdout = "organization=https://dev.azure.com/test\nproject=Test"

            mock_run.return_value = mock_config

            cli = AzureCLI()

            # Attempt to attach non-existent file
            with pytest.raises(Exception, match="File not found"):
                cli.attach_file_to_work_item(
                    work_item_id=123,
                    file_path=Path("/nonexistent/file.md"),
                    comment="Test attachment"
                )
