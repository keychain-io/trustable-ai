"""
Integration tests for PAT token authentication with REST API.

Tests actual REST API calls using PAT authentication to verify:
1. Authentication headers are correctly formatted
2. REST API endpoints accept PAT authentication
3. Work item operations succeed with PAT tokens
"""
import pytest
import os
from unittest.mock import Mock, patch, MagicMock
import base64


@pytest.mark.integration
class TestPATAuthenticationRESTAPI:
    """Test REST API calls with PAT authentication."""

    @patch('skills.azure_devops.cli_wrapper.requests.request')
    def test_make_request_uses_pat_authentication(self, mock_request):
        """Test that _make_request uses PAT token in Basic authentication header."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"id": 123}'
        mock_response.json.return_value = {"id": 123}
        mock_request.return_value = mock_response

        test_token = "abcd1234efgh5678ijkl9012mnop3456qrst7890uvwx1234yzab"

        with patch.dict(os.environ, {'AZURE_DEVOPS_EXT_PAT': test_token}):
            cli = AzureCLI()
            result = cli._make_request("GET", "Test/_apis/wit/workitems/123")

            # Verify request was called
            assert mock_request.called

            # Verify authorization header format
            call_kwargs = mock_request.call_args[1]
            headers = call_kwargs['headers']

            # Verify Basic auth header is present
            assert 'Authorization' in headers

            # Verify header format: Basic {base64(':' + PAT)}
            auth_header = headers['Authorization']
            assert auth_header.startswith('Basic ')

            # Decode and verify
            encoded_auth = auth_header.split(' ')[1]
            decoded_auth = base64.b64decode(encoded_auth).decode()
            assert decoded_auth == f":{test_token}"

    @patch('skills.azure_devops.cli_wrapper.requests.request')
    def test_get_work_item_with_pat_auth(self, mock_request):
        """Test get_work_item uses PAT authentication."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        # Mock work item response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"id": 123, "fields": {"System.Title": "Test Task"}}'
        mock_response.json.return_value = {
            "id": 123,
            "fields": {"System.Title": "Test Task"}
        }
        mock_request.return_value = mock_response

        test_token = "abcd1234efgh5678ijkl9012mnop3456qrst7890uvwx1234yzab"

        with patch.dict(os.environ, {'AZURE_DEVOPS_EXT_PAT': test_token}):
            cli = AzureCLI()
            work_item = cli.get_work_item(123)

            assert work_item['id'] == 123
            assert work_item['fields']['System.Title'] == "Test Task"

            # Verify PAT was used in auth header
            call_kwargs = mock_request.call_args[1]
            auth_header = call_kwargs['headers']['Authorization']
            assert auth_header.startswith('Basic ')

    @patch('skills.azure_devops.cli_wrapper.requests.request')
    def test_create_work_item_with_pat_auth(self, mock_request):
        """Test create_work_item uses PAT authentication."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        # Mock create response
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.text = '{"id": 456, "fields": {"System.Title": "New Task"}}'
        mock_response.json.return_value = {
            "id": 456,
            "fields": {"System.Title": "New Task"}
        }
        mock_request.return_value = mock_response

        test_token = "abcd1234efgh5678ijkl9012mnop3456qrst7890uvwx1234yzab"

        with patch.dict(os.environ, {'AZURE_DEVOPS_EXT_PAT': test_token}):
            cli = AzureCLI()
            work_item = cli.create_work_item(
                work_item_type="Task",
                title="New Task",
                description="Test description"
            )

            assert work_item['id'] == 456

            # Verify PAT was used
            call_kwargs = mock_request.call_args[1]
            auth_header = call_kwargs['headers']['Authorization']
            assert auth_header.startswith('Basic ')

            # Verify correct content type
            assert call_kwargs['headers']['Content-Type'] == 'application/json-patch+json'

    @patch('skills.azure_devops.cli_wrapper.requests.request')
    def test_query_work_items_with_pat_auth(self, mock_request):
        """Test query_work_items uses PAT authentication."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        # Mock query response (returns IDs)
        mock_query_response = Mock()
        mock_query_response.status_code = 200
        mock_query_response.text = '{"workItems": [{"id": 123}, {"id": 456}]}'
        mock_query_response.json.return_value = {
            "workItems": [{"id": 123}, {"id": 456}]
        }

        # Mock batch get response (returns full items)
        mock_batch_response = Mock()
        mock_batch_response.status_code = 200
        mock_batch_response.text = '{"value": [{"id": 123}, {"id": 456}]}'
        mock_batch_response.json.return_value = {
            "value": [{"id": 123}, {"id": 456}]
        }

        # Return different responses for POST (query) and GET (batch)
        def request_side_effect(method, *args, **kwargs):
            if method == "POST":
                return mock_query_response
            else:
                return mock_batch_response

        mock_request.side_effect = request_side_effect

        test_token = "abcd1234efgh5678ijkl9012mnop3456qrst7890uvwx1234yzab"

        with patch.dict(os.environ, {'AZURE_DEVOPS_EXT_PAT': test_token}):
            cli = AzureCLI()
            items = cli.query_work_items("SELECT [System.Id] FROM WorkItems")

            assert len(items) == 2

            # Verify both calls used PAT auth
            assert mock_request.call_count == 2
            for call in mock_request.call_args_list:
                auth_header = call[1]['headers']['Authorization']
                assert auth_header.startswith('Basic ')


@pytest.mark.integration
class TestPATAuthenticationErrorHandling:
    """Test error handling with PAT authentication."""

    @patch('skills.azure_devops.cli_wrapper.requests.request')
    def test_authentication_failure_401_response(self, mock_request):
        """Test that 401 response indicates authentication failure."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        # Mock 401 unauthorized response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = 'Unauthorized'
        mock_request.return_value = mock_response

        test_token = "invalidtoken1234567890abcdefghijklmnop"

        with patch.dict(os.environ, {'AZURE_DEVOPS_EXT_PAT': test_token}):
            cli = AzureCLI()

            with pytest.raises(Exception) as excinfo:
                cli.get_work_item(123)

            assert "401" in str(excinfo.value)

    def test_no_token_raises_authentication_error(self):
        """Test that missing token raises AuthenticationError."""
        from skills.azure_devops.cli_wrapper import AzureCLI, AuthenticationError

        # Provide organization/project config but no PAT token
        with patch.dict(os.environ, {
            'AZURE_DEVOPS_ORG': 'https://dev.azure.com/test',
            'AZURE_DEVOPS_PROJECT': 'TestProject'
        }, clear=True):
            with patch('pathlib.Path.exists', return_value=False):
                cli = AzureCLI()

                with pytest.raises(AuthenticationError):
                    cli._get_auth_token()


@pytest.mark.integration
class TestPATAuthenticationMultipleSources:
    """Test PAT authentication from multiple sources with priority."""

    def test_env_var_takes_priority_over_config(self):
        """Test that AZURE_DEVOPS_EXT_PAT env var takes priority over config."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        env_token = "envtoken1234567890abcdefghijklmnopqrstuvwxyz1234"
        config_token = "configtoken1234567890abcdefghijklmnopqrstuv1234"

        # Set environment variable
        with patch.dict(os.environ, {'AZURE_DEVOPS_EXT_PAT': env_token}):
            # Mock config file with different token
            with patch('builtins.open', create=True) as mock_file:
                mock_file.return_value.__enter__.return_value.read.return_value = f"""
work_tracking:
  credentials_source: {config_token}
"""
                with patch('pathlib.Path.exists', return_value=True):
                    cli = AzureCLI()
                    token = cli._get_cached_or_load_token()

                    # Should use env var, not config
                    assert token == env_token

    @patch('builtins.open', create=True)
    @patch('pathlib.Path.exists')
    def test_config_used_when_env_not_set(self, mock_exists, mock_file):
        """Test that config is used when AZURE_DEVOPS_EXT_PAT not set."""
        from skills.azure_devops.cli_wrapper import AzureCLI
        from unittest.mock import mock_open

        mock_exists.return_value = True

        config_token = "configtoken1234567890abcdefghijklmnopqrstuv1234"

        # Mock config file
        config_content = f"""
work_tracking:
  credentials_source: env:CUSTOM_TOKEN
  organization: https://dev.azure.com/test
  project: Test
"""
        mock_file.return_value = mock_open(read_data=config_content).return_value

        # Environment variable for CUSTOM_TOKEN
        with patch.dict(os.environ, {'CUSTOM_TOKEN': config_token}, clear=True):
            cli = AzureCLI()
            token = cli._get_cached_or_load_token()

            # Should use config token
            assert token == config_token


@pytest.mark.integration
class TestPATAuthenticationAttachments:
    """Test PAT authentication with file attachment operations."""

    @patch('skills.azure_devops.cli_wrapper.requests.post')
    @patch('skills.azure_devops.cli_wrapper.requests.patch')
    @patch('builtins.open', create=True)
    def test_attach_file_uses_pat_auth(self, mock_file, mock_patch, mock_post):
        """Test that attach_file_to_work_item uses PAT authentication."""
        from skills.azure_devops.cli_wrapper import AzureCLI
        from pathlib import Path
        from unittest.mock import mock_open

        # Mock file upload response
        upload_response = Mock()
        upload_response.status_code = 201
        upload_response.json.return_value = {"url": "https://dev.azure.com/test/_apis/wit/attachments/123"}
        mock_post.return_value = upload_response

        # Mock link response
        link_response = Mock()
        link_response.status_code = 200
        link_response.json.return_value = {"id": 456}
        mock_patch.return_value = link_response

        test_token = "abcd1234efgh5678ijkl9012mnop3456qrst7890uvwx1234yzab"

        # Mock file exists
        with patch('pathlib.Path.exists', return_value=True):
            with patch.dict(os.environ, {'AZURE_DEVOPS_EXT_PAT': test_token}):
                # Mock file read
                mock_file.return_value = mock_open(read_data=b"file content").return_value

                cli = AzureCLI()
                result = cli.attach_file_to_work_item(456, Path("test.pdf"))

                assert result['success'] is True

                # Verify both upload and link used PAT auth
                upload_headers = mock_post.call_args[1]['headers']
                assert 'Authorization' in upload_headers
                assert upload_headers['Authorization'].startswith('Basic ')

                link_headers = mock_patch.call_args[1]['headers']
                assert 'Authorization' in link_headers
                assert link_headers['Authorization'].startswith('Basic ')
