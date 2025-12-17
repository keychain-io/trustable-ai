"""
Integration tests for work item comments REST API implementation (Task #1140).

Tests the add_comment() method against real Azure DevOps API.

Key scenarios tested:
1. Creating comment on real work item
2. Retrieving comment via GET API
3. Markdown formatting preserved
4. Error handling with invalid work item ID
5. Comment persistence verification

Requirements:
- Azure DevOps organization and project configured
- Valid PAT token with Work Items (Read & Write) scope
- Environment variable AZURE_DEVOPS_EXT_PAT set
- Test work item ID available (set via TEST_WORK_ITEM_ID env var or fixture)

Usage:
    pytest tests/integration/test_work_item_comments_integration.py -m azure
"""
import os
import pytest
from datetime import datetime
from unittest.mock import patch


# Skip all tests in this module if Azure DevOps is not configured
pytestmark = [
    pytest.mark.integration,
    pytest.mark.azure,
    pytest.mark.skipif(
        not os.environ.get('AZURE_DEVOPS_EXT_PAT'),
        reason="AZURE_DEVOPS_EXT_PAT environment variable not set"
    )
]


def get_test_work_item_id():
    """
    Get a work item ID to use for testing.

    Tries in order:
    1. TEST_WORK_ITEM_ID environment variable
    2. Query for any existing work item in the project
    """
    # Try environment variable first
    test_id = os.environ.get('TEST_WORK_ITEM_ID')
    if test_id:
        return int(test_id)

    # Fall back to querying for any work item
    try:
        from skills.azure_devops.cli_wrapper import AzureCLI
        cli = AzureCLI()

        # Query for any recent work item
        wiql = """
            SELECT [System.Id]
            FROM WorkItems
            WHERE [System.ChangedDate] > @Today - 30
            ORDER BY [System.Id] DESC
        """
        items = cli.query_work_items(wiql)
        if items:
            return items[0].get('id')
    except Exception:
        pass

    return None


@pytest.fixture
def azure_cli():
    """Provide an AzureCLI instance for testing."""
    from skills.azure_devops.cli_wrapper import AzureCLI
    return AzureCLI()


@pytest.fixture
def test_work_item_id():
    """Provide a work item ID for testing."""
    work_item_id = get_test_work_item_id()
    if not work_item_id:
        pytest.skip("No test work item ID available. Set TEST_WORK_ITEM_ID environment variable.")
    return work_item_id


class TestAddCommentIntegration:
    """Integration tests for add_comment() against real Azure DevOps API."""

    def test_add_plain_text_comment(self, azure_cli, test_work_item_id):
        """Test creating a plain text comment on a real work item."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        comment_text = f"Integration test comment (plain text) - {timestamp}"

        result = azure_cli.add_comment(test_work_item_id, comment_text)

        # Verify response structure
        assert 'id' in result, "Response should contain comment ID"
        assert result['id'] is not None, "Comment ID should not be None"
        assert 'text' in result, "Response should contain comment text"
        assert comment_text in result['text'], "Comment text should be preserved"

    def test_add_markdown_comment(self, azure_cli, test_work_item_id):
        """Test creating a markdown-formatted comment on a real work item."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        markdown_comment = f"""## Integration Test Comment - {timestamp}

**Test Status:** Passed

### Checklist:
- [x] REST API call executed
- [x] Response validated
- [ ] Manual verification (optional)

```python
# Sample code block
def test():
    return "success"
```

> This is a block quote for testing markdown preservation.
"""

        result = azure_cli.add_comment(test_work_item_id, markdown_comment)

        # Verify response structure
        assert 'id' in result, "Response should contain comment ID"
        assert 'text' in result, "Response should contain comment text"

        # Verify markdown elements are preserved
        returned_text = result['text']
        assert '##' in returned_text, "Markdown heading should be preserved"
        assert '**' in returned_text, "Bold markdown should be preserved"
        assert '```' in returned_text, "Code block should be preserved"

    def test_add_comment_returns_created_date(self, azure_cli, test_work_item_id):
        """Test that add_comment returns creation timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        comment_text = f"Integration test - timestamp check - {timestamp}"

        result = azure_cli.add_comment(test_work_item_id, comment_text)

        # Verify created date is present
        assert 'createdDate' in result, "Response should contain createdDate"
        assert result['createdDate'] is not None, "createdDate should not be None"

    def test_add_comment_returns_created_by(self, azure_cli, test_work_item_id):
        """Test that add_comment returns creator information."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        comment_text = f"Integration test - creator check - {timestamp}"

        result = azure_cli.add_comment(test_work_item_id, comment_text)

        # Verify created by information is present
        assert 'createdBy' in result, "Response should contain createdBy"
        assert result['createdBy'] is not None, "createdBy should not be None"

    def test_add_comment_invalid_work_item_id(self, azure_cli):
        """Test error handling when work item ID does not exist."""
        # Use an extremely high ID that's unlikely to exist
        invalid_id = 999999999

        with pytest.raises(Exception) as exc_info:
            azure_cli.add_comment(invalid_id, "This should fail")

        error_msg = str(exc_info.value).lower()
        assert "not found" in error_msg or "999999999" in str(exc_info.value), \
            "Error should indicate work item not found"


class TestCommentVerification:
    """Tests that verify comments can be retrieved after creation."""

    def test_comment_retrievable_via_get_request(self, azure_cli, test_work_item_id):
        """Test that a created comment can be retrieved via GET API."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        unique_marker = f"VERIFY-{timestamp}-{os.getpid()}"
        comment_text = f"Verification test comment - {unique_marker}"

        # Create comment
        create_result = azure_cli.add_comment(test_work_item_id, comment_text)
        comment_id = create_result['id']

        # Retrieve comment via GET request
        project = azure_cli._get_project()
        endpoint = f"{project}/_apis/wit/workitems/{test_work_item_id}/comments/{comment_id}"
        params = {"api-version": "7.1-preview"}

        get_result = azure_cli._make_comment_request("GET", endpoint, params=params)

        # Verify retrieved comment matches created comment
        assert get_result['id'] == comment_id, "Retrieved comment ID should match"
        assert unique_marker in get_result['text'], "Retrieved comment text should contain unique marker"


class TestCommentWithSpecialCharacters:
    """Tests for comments with special characters and edge cases."""

    def test_comment_with_html_entities(self, azure_cli, test_work_item_id):
        """Test comment creation with HTML-like content."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        comment_text = f"Test with <script>alert('test')</script> and &amp; entities - {timestamp}"

        result = azure_cli.add_comment(test_work_item_id, comment_text)

        # Should succeed without error
        assert 'id' in result, "Comment should be created successfully"

    def test_comment_with_newlines(self, azure_cli, test_work_item_id):
        """Test comment creation with multiple newlines."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        comment_text = f"Line 1\n\nLine 2\n\n\nLine 3 - {timestamp}"

        result = azure_cli.add_comment(test_work_item_id, comment_text)

        # Should succeed and preserve newlines
        assert 'id' in result, "Comment should be created successfully"
        assert '\n' in result['text'], "Newlines should be preserved"


class TestConvenienceFunctionIntegration:
    """Integration tests for the module-level add_comment convenience function."""

    def test_convenience_function_works(self, test_work_item_id):
        """Test that the module-level add_comment function works correctly."""
        from skills.azure_devops.cli_wrapper import add_comment

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        comment_text = f"Convenience function test - {timestamp}"

        result = add_comment(test_work_item_id, comment_text)

        assert 'id' in result, "Comment should be created successfully"
        assert comment_text in result['text'], "Comment text should be preserved"

    def test_convenience_function_with_agent_name(self, test_work_item_id):
        """Test add_comment convenience function with agent_name parameter."""
        from skills.azure_devops.cli_wrapper import add_comment

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        comment_text = f"Agent function test - {timestamp}"

        result = add_comment(test_work_item_id, comment_text, agent_name="test-agent")

        assert 'id' in result, "Comment should be created successfully"
        assert '[test-agent]' in result['text'], "Agent name prefix should be in comment"
