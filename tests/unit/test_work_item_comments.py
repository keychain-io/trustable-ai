"""
Unit tests for work item comments REST API implementation (Task #1140).

Tests the add_comment() method in cli_wrapper.py that uses Azure DevOps
Work Item Comments REST API instead of subprocess calls.

Key scenarios tested:
1. Successful comment creation with mocked API response
2. Error handling for 404 (work item not found)
3. Error handling for 401 (authentication failure)
4. Markdown text preservation
5. Plain text comments
6. Error handling for API failures
7. Response structure validation
"""
import pytest
from unittest.mock import Mock, patch, MagicMock


@pytest.mark.unit
class TestAddCommentRestApi:
    """Test suite for add_comment() REST API implementation."""

    @patch('skills.azure_devops.cli_wrapper.load_config')
    @patch('skills.azure_devops.cli_wrapper.requests')
    def test_add_comment_success(self, mock_requests, mock_load_config):
        """Test successful comment creation with REST API."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        # Mock config loading
        mock_config = Mock()
        mock_config.work_tracking.organization = "https://dev.azure.com/test"
        mock_config.work_tracking.project = "TestProject"
        mock_load_config.return_value = mock_config

        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"id": 12345, "workItemId": 1234, "text": "Test comment"}'
        mock_response.json.return_value = {
            'id': 12345,
            'workItemId': 1234,
            'text': 'Test comment',
            'createdDate': '2024-01-15T10:30:00Z',
            'createdBy': {
                'displayName': 'Test User',
                'uniqueName': 'test@example.com'
            }
        }
        mock_requests.request.return_value = mock_response

        cli = AzureCLI()

        # Mock _get_auth_token to avoid authentication
        with patch.object(cli, '_get_auth_token', return_value='fake-token'):
            result = cli.add_comment(1234, "Test comment")

        assert result['id'] == 12345
        assert result['workItemId'] == 1234
        assert result['text'] == 'Test comment'
        assert 'createdDate' in result
        assert 'createdBy' in result

    @patch('skills.azure_devops.cli_wrapper.load_config')
    @patch('skills.azure_devops.cli_wrapper.requests')
    def test_add_comment_with_markdown(self, mock_requests, mock_load_config):
        """Test comment creation with markdown formatting preserved."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        # Mock config loading
        mock_config = Mock()
        mock_config.work_tracking.organization = "https://dev.azure.com/test"
        mock_config.work_tracking.project = "TestProject"
        mock_load_config.return_value = mock_config

        markdown_comment = """## Status Update

**Progress:**
- [x] Task 1 completed
- [ ] Task 2 in progress

```python
def example():
    return "code block"
```
"""

        # Mock successful API response with markdown preserved
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"id": 12346}'
        mock_response.json.return_value = {
            'id': 12346,
            'workItemId': 1234,
            'text': markdown_comment
        }
        mock_requests.request.return_value = mock_response

        cli = AzureCLI()

        with patch.object(cli, '_get_auth_token', return_value='fake-token'):
            result = cli.add_comment(1234, markdown_comment)

        assert result['text'] == markdown_comment
        assert '**Progress:**' in result['text']
        assert '```python' in result['text']

    @patch('skills.azure_devops.cli_wrapper.load_config')
    @patch('skills.azure_devops.cli_wrapper.requests')
    def test_add_comment_plain_text(self, mock_requests, mock_load_config):
        """Test comment creation with plain text."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        # Mock config loading
        mock_config = Mock()
        mock_config.work_tracking.organization = "https://dev.azure.com/test"
        mock_config.work_tracking.project = "TestProject"
        mock_load_config.return_value = mock_config

        plain_comment = "This is a plain text comment without any formatting."

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"id": 12347}'
        mock_response.json.return_value = {
            'id': 12347,
            'workItemId': 1234,
            'text': plain_comment
        }
        mock_requests.request.return_value = mock_response

        cli = AzureCLI()

        with patch.object(cli, '_get_auth_token', return_value='fake-token'):
            result = cli.add_comment(1234, plain_comment)

        assert result['text'] == plain_comment

    @patch('skills.azure_devops.cli_wrapper.load_config')
    @patch('skills.azure_devops.cli_wrapper.requests')
    def test_add_comment_404_work_item_not_found(self, mock_requests, mock_load_config):
        """Test error handling for 404 - work item not found."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        # Mock config loading
        mock_config = Mock()
        mock_config.work_tracking.organization = "https://dev.azure.com/test"
        mock_config.work_tracking.project = "TestProject"
        mock_load_config.return_value = mock_config

        # Mock 404 response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = '{"message": "Work item 9999 not found"}'
        mock_requests.request.return_value = mock_response

        cli = AzureCLI()

        with patch.object(cli, '_get_auth_token', return_value='fake-token'):
            with pytest.raises(Exception) as exc_info:
                cli.add_comment(9999, "Test comment")

        assert "9999" in str(exc_info.value)
        assert "not found" in str(exc_info.value).lower()

    @patch('skills.azure_devops.cli_wrapper.load_config')
    @patch('skills.azure_devops.cli_wrapper.requests')
    def test_add_comment_401_authentication_failure(self, mock_requests, mock_load_config):
        """Test error handling for 401 - authentication failure."""
        from skills.azure_devops.cli_wrapper import AzureCLI, AuthenticationError

        # Mock config loading
        mock_config = Mock()
        mock_config.work_tracking.organization = "https://dev.azure.com/test"
        mock_config.work_tracking.project = "TestProject"
        mock_load_config.return_value = mock_config

        # Mock 401 response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = '{"message": "Authentication required"}'
        mock_requests.request.return_value = mock_response

        cli = AzureCLI()

        with patch.object(cli, '_get_auth_token', return_value='fake-token'):
            with pytest.raises(AuthenticationError) as exc_info:
                cli.add_comment(1234, "Test comment")

        assert "Authentication failed" in str(exc_info.value)
        assert "1234" in str(exc_info.value)

    @patch('skills.azure_devops.cli_wrapper.load_config')
    @patch('skills.azure_devops.cli_wrapper.requests')
    def test_add_comment_403_forbidden(self, mock_requests, mock_load_config):
        """Test error handling for 403 - forbidden."""
        from skills.azure_devops.cli_wrapper import AzureCLI, AuthenticationError

        # Mock config loading
        mock_config = Mock()
        mock_config.work_tracking.organization = "https://dev.azure.com/test"
        mock_config.work_tracking.project = "TestProject"
        mock_load_config.return_value = mock_config

        # Mock 403 response
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.text = '{"message": "Access denied"}'
        mock_requests.request.return_value = mock_response

        cli = AzureCLI()

        with patch.object(cli, '_get_auth_token', return_value='fake-token'):
            with pytest.raises(AuthenticationError) as exc_info:
                cli.add_comment(1234, "Test comment")

        assert "Authentication failed" in str(exc_info.value)

    @patch('skills.azure_devops.cli_wrapper.load_config')
    @patch('skills.azure_devops.cli_wrapper.requests')
    def test_add_comment_500_server_error(self, mock_requests, mock_load_config):
        """Test error handling for 500 - server error."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        # Mock config loading
        mock_config = Mock()
        mock_config.work_tracking.organization = "https://dev.azure.com/test"
        mock_config.work_tracking.project = "TestProject"
        mock_load_config.return_value = mock_config

        # Mock 500 response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = '{"message": "Internal server error"}'
        mock_requests.request.return_value = mock_response

        cli = AzureCLI()

        with patch.object(cli, '_get_auth_token', return_value='fake-token'):
            with pytest.raises(Exception) as exc_info:
                cli.add_comment(1234, "Test comment")

        assert "Failed to add comment" in str(exc_info.value)
        assert "1234" in str(exc_info.value)

    @patch('skills.azure_devops.cli_wrapper.load_config')
    @patch('skills.azure_devops.cli_wrapper.requests')
    def test_add_comment_uses_correct_endpoint(self, mock_requests, mock_load_config):
        """Test that add_comment uses correct REST API endpoint."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        # Mock config loading
        mock_config = Mock()
        mock_config.work_tracking.organization = "https://dev.azure.com/test"
        mock_config.work_tracking.project = "TestProject"
        mock_load_config.return_value = mock_config

        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"id": 12345}'
        mock_response.json.return_value = {'id': 12345, 'workItemId': 1234, 'text': 'Test'}
        mock_requests.request.return_value = mock_response

        cli = AzureCLI()

        with patch.object(cli, '_get_auth_token', return_value='fake-token'):
            cli.add_comment(1234, "Test comment")

        # Verify API was called with correct parameters
        call_args = mock_requests.request.call_args
        assert call_args[1]['method'] == 'POST'
        assert 'TestProject/_apis/wit/workitems/1234/comments' in call_args[1]['url']
        assert 'api-version=7.1-preview' in call_args[1]['url'] or call_args[1]['params'].get('api-version') == '7.1-preview'

    @patch('skills.azure_devops.cli_wrapper.load_config')
    @patch('skills.azure_devops.cli_wrapper.requests')
    def test_add_comment_uses_correct_content_type(self, mock_requests, mock_load_config):
        """Test that add_comment uses application/json content type."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        # Mock config loading
        mock_config = Mock()
        mock_config.work_tracking.organization = "https://dev.azure.com/test"
        mock_config.work_tracking.project = "TestProject"
        mock_load_config.return_value = mock_config

        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"id": 12345}'
        mock_response.json.return_value = {'id': 12345}
        mock_requests.request.return_value = mock_response

        cli = AzureCLI()

        with patch.object(cli, '_get_auth_token', return_value='fake-token'):
            cli.add_comment(1234, "Test comment")

        # Verify Content-Type header
        call_args = mock_requests.request.call_args
        assert call_args[1]['headers']['Content-Type'] == 'application/json'

    @patch('skills.azure_devops.cli_wrapper.load_config')
    @patch('skills.azure_devops.cli_wrapper.requests')
    def test_add_comment_sends_correct_body(self, mock_requests, mock_load_config):
        """Test that add_comment sends correct JSON body."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        # Mock config loading
        mock_config = Mock()
        mock_config.work_tracking.organization = "https://dev.azure.com/test"
        mock_config.work_tracking.project = "TestProject"
        mock_load_config.return_value = mock_config

        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"id": 12345}'
        mock_response.json.return_value = {'id': 12345}
        mock_requests.request.return_value = mock_response

        cli = AzureCLI()

        with patch.object(cli, '_get_auth_token', return_value='fake-token'):
            cli.add_comment(1234, "My test comment")

        # Verify body
        call_args = mock_requests.request.call_args
        assert call_args[1]['json'] == {'text': 'My test comment'}

    @patch('skills.azure_devops.cli_wrapper.load_config')
    @patch('skills.azure_devops.cli_wrapper.requests')
    def test_add_comment_with_special_characters(self, mock_requests, mock_load_config):
        """Test comment creation with special characters."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        # Mock config loading
        mock_config = Mock()
        mock_config.work_tracking.organization = "https://dev.azure.com/test"
        mock_config.work_tracking.project = "TestProject"
        mock_load_config.return_value = mock_config

        special_comment = 'Comment with "quotes", <tags>, & ampersand'

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"id": 12348}'
        mock_response.json.return_value = {
            'id': 12348,
            'workItemId': 1234,
            'text': special_comment
        }
        mock_requests.request.return_value = mock_response

        cli = AzureCLI()

        with patch.object(cli, '_get_auth_token', return_value='fake-token'):
            result = cli.add_comment(1234, special_comment)

        assert result['text'] == special_comment

    @patch('skills.azure_devops.cli_wrapper.load_config')
    @patch('skills.azure_devops.cli_wrapper.requests')
    def test_add_comment_with_unicode(self, mock_requests, mock_load_config):
        """Test comment creation with unicode characters."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        # Mock config loading
        mock_config = Mock()
        mock_config.work_tracking.organization = "https://dev.azure.com/test"
        mock_config.work_tracking.project = "TestProject"
        mock_load_config.return_value = mock_config

        unicode_comment = 'Comment with emojis and unicode chars'

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"id": 12349}'
        mock_response.json.return_value = {
            'id': 12349,
            'workItemId': 1234,
            'text': unicode_comment
        }
        mock_requests.request.return_value = mock_response

        cli = AzureCLI()

        with patch.object(cli, '_get_auth_token', return_value='fake-token'):
            result = cli.add_comment(1234, unicode_comment)

        assert result['text'] == unicode_comment


@pytest.mark.unit
class TestMakeCommentRequest:
    """Test suite for _make_comment_request() helper method."""

    @patch('skills.azure_devops.cli_wrapper.load_config')
    @patch('skills.azure_devops.cli_wrapper.requests')
    def test_make_comment_request_uses_json_content_type(self, mock_requests, mock_load_config):
        """Test that _make_comment_request uses application/json content type."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        # Mock config loading
        mock_config = Mock()
        mock_config.work_tracking.organization = "https://dev.azure.com/test"
        mock_config.work_tracking.project = "TestProject"
        mock_load_config.return_value = mock_config

        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"id": 12345}'
        mock_response.json.return_value = {'id': 12345}
        mock_requests.request.return_value = mock_response

        cli = AzureCLI()

        with patch.object(cli, '_get_auth_token', return_value='fake-token'):
            cli._make_comment_request(
                'POST',
                'TestProject/_apis/wit/workitems/1234/comments',
                data={'text': 'Test'},
                params={'api-version': '7.1'}
            )

        # Verify Content-Type is application/json (not JSON Patch)
        call_args = mock_requests.request.call_args
        assert call_args[1]['headers']['Content-Type'] == 'application/json'

    @patch('skills.azure_devops.cli_wrapper.load_config')
    @patch('skills.azure_devops.cli_wrapper.requests')
    def test_make_comment_request_handles_empty_response(self, mock_requests, mock_load_config):
        """Test _make_comment_request handles empty response body."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        # Mock config loading
        mock_config = Mock()
        mock_config.work_tracking.organization = "https://dev.azure.com/test"
        mock_config.work_tracking.project = "TestProject"
        mock_load_config.return_value = mock_config

        # Mock response with empty body
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = ''
        mock_requests.request.return_value = mock_response

        cli = AzureCLI()

        with patch.object(cli, '_get_auth_token', return_value='fake-token'):
            result = cli._make_comment_request(
                'POST',
                'TestProject/_apis/wit/workitems/1234/comments',
                data={'text': 'Test'},
                params={'api-version': '7.1'}
            )

        assert result == {}

    @patch('skills.azure_devops.cli_wrapper.load_config')
    def test_make_comment_request_requires_requests_library(self, mock_load_config):
        """Test that _make_comment_request raises ImportError when requests unavailable."""
        from skills.azure_devops import cli_wrapper
        from skills.azure_devops.cli_wrapper import AzureCLI

        # Mock config loading
        mock_config = Mock()
        mock_config.work_tracking.organization = "https://dev.azure.com/test"
        mock_config.work_tracking.project = "TestProject"
        mock_load_config.return_value = mock_config

        cli = AzureCLI()

        # Temporarily set HAS_REQUESTS to False
        original_has_requests = cli_wrapper.HAS_REQUESTS
        cli_wrapper.HAS_REQUESTS = False

        try:
            with pytest.raises(ImportError) as exc_info:
                cli._make_comment_request('POST', 'endpoint', data={'text': 'test'})

            assert 'requests library required' in str(exc_info.value)
        finally:
            cli_wrapper.HAS_REQUESTS = original_has_requests


@pytest.mark.unit
class TestAddCommentConvenienceFunction:
    """Test suite for add_comment convenience function."""

    @patch('skills.azure_devops.cli_wrapper.load_config')
    @patch('skills.azure_devops.cli_wrapper.requests')
    def test_add_comment_convenience_function(self, mock_requests, mock_load_config):
        """Test the module-level add_comment convenience function."""
        from skills.azure_devops.cli_wrapper import add_comment

        # Mock config loading
        mock_config = Mock()
        mock_config.work_tracking.organization = "https://dev.azure.com/test"
        mock_config.work_tracking.project = "TestProject"
        mock_load_config.return_value = mock_config

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"id": 12350}'
        mock_response.json.return_value = {'id': 12350, 'text': 'Test comment'}
        mock_requests.request.return_value = mock_response

        # Patch the singleton's auth token
        from skills.azure_devops.cli_wrapper import azure_cli
        with patch.object(azure_cli, '_get_auth_token', return_value='fake-token'):
            result = add_comment(1234, "Test comment")

        assert result['id'] == 12350

    @patch('skills.azure_devops.cli_wrapper.load_config')
    @patch('skills.azure_devops.cli_wrapper.requests')
    def test_add_comment_with_agent_name(self, mock_requests, mock_load_config):
        """Test add_comment convenience function with agent_name prefix."""
        from skills.azure_devops.cli_wrapper import add_comment

        # Mock config loading
        mock_config = Mock()
        mock_config.work_tracking.organization = "https://dev.azure.com/test"
        mock_config.work_tracking.project = "TestProject"
        mock_load_config.return_value = mock_config

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"id": 12351}'
        mock_response.json.return_value = {
            'id': 12351,
            'text': '[engineer] Status update: task in progress'
        }
        mock_requests.request.return_value = mock_response

        from skills.azure_devops.cli_wrapper import azure_cli
        with patch.object(azure_cli, '_get_auth_token', return_value='fake-token'):
            result = add_comment(1234, "Status update: task in progress", agent_name="engineer")

        # Verify the comment was prefixed with agent name
        call_args = mock_requests.request.call_args
        assert call_args[1]['json']['text'] == '[engineer] Status update: task in progress'
