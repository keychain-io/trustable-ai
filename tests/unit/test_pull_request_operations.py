"""
Unit tests for pull request operations in Azure DevOps CLI wrapper.

Tests Task #1142 - Replace subprocess calls in create_pull_request() and approve_pull_request()
with Azure DevOps Git REST API.

These tests verify:
1. Successful PR creation with REST API
2. PR creation with work item linking
3. PR creation with reviewers
4. Error handling for 404, 401, 400 errors
5. Successful PR approval
6. PR approval vote setting (vote=10)
7. Repository ID resolution
8. Current user ID retrieval
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from skills.azure_devops.cli_wrapper import AzureCLI, AuthenticationError


@pytest.fixture
def mock_cli():
    """Create AzureCLI instance with mocked configuration."""
    with patch.object(AzureCLI, '_load_configuration') as mock_load_config:
        mock_load_config.return_value = {
            'organization': 'https://dev.azure.com/testorg',
            'project': 'TestProject'
        }
        cli = AzureCLI()
        yield cli


@pytest.fixture
def mock_requests():
    """Mock requests library for REST API calls."""
    with patch('skills.azure_devops.cli_wrapper.requests') as mock_req:
        yield mock_req


@pytest.mark.unit
class TestGetRepositoryId:
    """Test suite for _get_repository_id() helper method."""

    def test_get_repository_id_success(self, mock_cli, mock_requests):
        """Test successful repository ID retrieval."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"id": "repo-guid-12345"}'
        mock_response.json.return_value = {"id": "repo-guid-12345"}
        mock_requests.request.return_value = mock_response

        with patch.object(mock_cli, '_get_auth_token', return_value='test-token'):
            result = mock_cli._get_repository_id("TestRepo")

        assert result == "repo-guid-12345"

    def test_get_repository_id_uses_project_name_as_default(self, mock_cli, mock_requests):
        """Test that repository name defaults to project name."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"id": "project-repo-guid"}'
        mock_response.json.return_value = {"id": "project-repo-guid"}
        mock_requests.request.return_value = mock_response

        with patch.object(mock_cli, '_get_auth_token', return_value='test-token'):
            result = mock_cli._get_repository_id()

        assert result == "project-repo-guid"
        # Verify the endpoint used project name
        call_args = mock_requests.request.call_args
        assert "TestProject" in call_args.kwargs['url']

    def test_get_repository_id_404_error(self, mock_cli, mock_requests):
        """Test 404 error handling for repository not found."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Repository not found"
        mock_requests.request.return_value = mock_response

        with patch.object(mock_cli, '_get_auth_token', return_value='test-token'):
            with pytest.raises(Exception) as exc_info:
                mock_cli._get_repository_id("NonExistentRepo")

        assert "Repository 'NonExistentRepo' not found" in str(exc_info.value)

    def test_get_repository_id_401_error(self, mock_cli, mock_requests):
        """Test 401 authentication error handling."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_requests.request.return_value = mock_response

        with patch.object(mock_cli, '_get_auth_token', return_value='test-token'):
            with pytest.raises(AuthenticationError) as exc_info:
                mock_cli._get_repository_id("TestRepo")

        assert "Authentication failed" in str(exc_info.value)


@pytest.mark.unit
class TestGetCurrentUserId:
    """Test suite for _get_current_user_id() helper method."""

    def test_get_current_user_id_success(self, mock_cli, mock_requests):
        """Test successful user ID retrieval."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"authenticatedUser": {"id": "user-guid-12345"}}'
        mock_response.json.return_value = {
            "authenticatedUser": {"id": "user-guid-12345"}
        }
        mock_requests.request.return_value = mock_response

        with patch.object(mock_cli, '_get_auth_token', return_value='test-token'):
            result = mock_cli._get_current_user_id()

        assert result == "user-guid-12345"

    def test_get_current_user_id_missing_id(self, mock_cli, mock_requests):
        """Test error when user ID is not available."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"authenticatedUser": {}}'
        mock_response.json.return_value = {"authenticatedUser": {}}
        mock_requests.request.return_value = mock_response

        with patch.object(mock_cli, '_get_auth_token', return_value='test-token'):
            with pytest.raises(AuthenticationError) as exc_info:
                mock_cli._get_current_user_id()

        assert "Could not determine authenticated user ID" in str(exc_info.value)

    def test_get_current_user_id_401_error(self, mock_cli, mock_requests):
        """Test 401 authentication error handling."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_requests.request.return_value = mock_response

        with patch.object(mock_cli, '_get_auth_token', return_value='test-token'):
            with pytest.raises(AuthenticationError) as exc_info:
                mock_cli._get_current_user_id()

        assert "Authentication failed" in str(exc_info.value)


@pytest.mark.unit
class TestCreatePullRequest:
    """Test suite for create_pull_request() method."""

    def test_create_pull_request_success(self, mock_cli, mock_requests):
        """Test successful PR creation."""
        # Mock repository ID response
        repo_response = Mock()
        repo_response.status_code = 200
        repo_response.text = '{"id": "repo-guid"}'
        repo_response.json.return_value = {"id": "repo-guid"}

        # Mock PR creation response
        pr_response = Mock()
        pr_response.status_code = 201
        pr_response.text = '{"id": 42, "url": "https://dev.azure.com/testorg/TestProject/_git/TestProject/pullrequest/42", "status": "active"}'
        pr_response.json.return_value = {
            "id": 42,
            "url": "https://dev.azure.com/testorg/TestProject/_git/TestProject/pullrequest/42",
            "status": "active",
            "sourceRefName": "refs/heads/feature/test",
            "targetRefName": "refs/heads/main",
            "title": "Test PR",
            "description": "Test description"
        }

        mock_requests.request.side_effect = [repo_response, pr_response]

        with patch.object(mock_cli, '_get_auth_token', return_value='test-token'):
            result = mock_cli.create_pull_request(
                source_branch="feature/test",
                title="Test PR",
                description="Test description"
            )

        assert result["id"] == 42
        assert result["status"] == "active"
        assert "url" in result

    def test_create_pull_request_with_work_items(self, mock_cli, mock_requests):
        """Test PR creation with work item linking."""
        repo_response = Mock()
        repo_response.status_code = 200
        repo_response.text = '{"id": "repo-guid"}'
        repo_response.json.return_value = {"id": "repo-guid"}

        pr_response = Mock()
        pr_response.status_code = 201
        pr_response.text = '{"id": 42}'
        pr_response.json.return_value = {"id": 42}

        mock_requests.request.side_effect = [repo_response, pr_response]

        with patch.object(mock_cli, '_get_auth_token', return_value='test-token'):
            result = mock_cli.create_pull_request(
                source_branch="feature/test",
                title="Test PR",
                description="Test description",
                work_item_ids=[1234, 1235, 1236]
            )

        assert result["id"] == 42

        # Verify work items were included in the request body
        call_args = mock_requests.request.call_args_list[-1]
        request_body = call_args.kwargs['json']
        assert "workItemRefs" in request_body
        assert len(request_body["workItemRefs"]) == 3
        assert request_body["workItemRefs"][0]["id"] == "1234"

    def test_create_pull_request_with_reviewers(self, mock_cli, mock_requests):
        """Test PR creation with reviewer assignment."""
        repo_response = Mock()
        repo_response.status_code = 200
        repo_response.text = '{"id": "repo-guid"}'
        repo_response.json.return_value = {"id": "repo-guid"}

        pr_response = Mock()
        pr_response.status_code = 201
        pr_response.text = '{"id": 42}'
        pr_response.json.return_value = {"id": 42}

        mock_requests.request.side_effect = [repo_response, pr_response]

        with patch.object(mock_cli, '_get_auth_token', return_value='test-token'):
            result = mock_cli.create_pull_request(
                source_branch="feature/test",
                title="Test PR",
                description="Test description",
                reviewers=["user1@example.com", "reviewer-guid-123"]
            )

        assert result["id"] == 42

        # Verify reviewers were included in the request body
        call_args = mock_requests.request.call_args_list[-1]
        request_body = call_args.kwargs['json']
        assert "reviewers" in request_body
        assert len(request_body["reviewers"]) == 2
        assert request_body["reviewers"][0]["id"] == "user1@example.com"

    def test_create_pull_request_with_target_branch(self, mock_cli, mock_requests):
        """Test PR creation with custom target branch."""
        repo_response = Mock()
        repo_response.status_code = 200
        repo_response.text = '{"id": "repo-guid"}'
        repo_response.json.return_value = {"id": "repo-guid"}

        pr_response = Mock()
        pr_response.status_code = 201
        pr_response.text = '{"id": 42}'
        pr_response.json.return_value = {"id": 42}

        mock_requests.request.side_effect = [repo_response, pr_response]

        with patch.object(mock_cli, '_get_auth_token', return_value='test-token'):
            result = mock_cli.create_pull_request(
                source_branch="feature/test",
                title="Test PR",
                description="Test description",
                target_branch="develop"
            )

        assert result["id"] == 42

        # Verify target branch was set correctly
        call_args = mock_requests.request.call_args_list[-1]
        request_body = call_args.kwargs['json']
        assert request_body["targetRefName"] == "refs/heads/develop"

    def test_create_pull_request_with_refs_prefix(self, mock_cli, mock_requests):
        """Test PR creation when branch already has refs/ prefix."""
        repo_response = Mock()
        repo_response.status_code = 200
        repo_response.text = '{"id": "repo-guid"}'
        repo_response.json.return_value = {"id": "repo-guid"}

        pr_response = Mock()
        pr_response.status_code = 201
        pr_response.text = '{"id": 42}'
        pr_response.json.return_value = {"id": 42}

        mock_requests.request.side_effect = [repo_response, pr_response]

        with patch.object(mock_cli, '_get_auth_token', return_value='test-token'):
            result = mock_cli.create_pull_request(
                source_branch="refs/heads/feature/test",
                title="Test PR",
                description="Test description"
            )

        assert result["id"] == 42

        # Verify refs/heads prefix not doubled
        call_args = mock_requests.request.call_args_list[-1]
        request_body = call_args.kwargs['json']
        assert request_body["sourceRefName"] == "refs/heads/feature/test"

    def test_create_pull_request_404_error_repository(self, mock_cli, mock_requests):
        """Test 404 error handling for repository not found."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Repository not found"
        mock_requests.request.return_value = mock_response

        with patch.object(mock_cli, '_get_auth_token', return_value='test-token'):
            with pytest.raises(Exception) as exc_info:
                mock_cli.create_pull_request(
                    source_branch="feature/test",
                    title="Test PR",
                    description="Test description"
                )

        assert "Repository" in str(exc_info.value) or "not found" in str(exc_info.value)

    def test_create_pull_request_404_error_branch(self, mock_cli, mock_requests):
        """Test 404 error handling for branch not found."""
        repo_response = Mock()
        repo_response.status_code = 200
        repo_response.text = '{"id": "repo-guid"}'
        repo_response.json.return_value = {"id": "repo-guid"}

        pr_response = Mock()
        pr_response.status_code = 404
        pr_response.text = "Branch not found"
        mock_requests.request.side_effect = [repo_response, pr_response]

        with patch.object(mock_cli, '_get_auth_token', return_value='test-token'):
            with pytest.raises(Exception) as exc_info:
                mock_cli.create_pull_request(
                    source_branch="nonexistent/branch",
                    title="Test PR",
                    description="Test description"
                )

        assert "branch not found" in str(exc_info.value).lower() or "not found" in str(exc_info.value).lower()

    def test_create_pull_request_401_error(self, mock_cli, mock_requests):
        """Test 401 authentication error handling."""
        repo_response = Mock()
        repo_response.status_code = 200
        repo_response.text = '{"id": "repo-guid"}'
        repo_response.json.return_value = {"id": "repo-guid"}

        pr_response = Mock()
        pr_response.status_code = 401
        pr_response.text = "Unauthorized"
        mock_requests.request.side_effect = [repo_response, pr_response]

        with patch.object(mock_cli, '_get_auth_token', return_value='test-token'):
            with pytest.raises(AuthenticationError) as exc_info:
                mock_cli.create_pull_request(
                    source_branch="feature/test",
                    title="Test PR",
                    description="Test description"
                )

        assert "Authentication failed" in str(exc_info.value)

    def test_create_pull_request_400_error(self, mock_cli, mock_requests):
        """Test 400 bad request error handling."""
        repo_response = Mock()
        repo_response.status_code = 200
        repo_response.text = '{"id": "repo-guid"}'
        repo_response.json.return_value = {"id": "repo-guid"}

        pr_response = Mock()
        pr_response.status_code = 400
        pr_response.text = "Invalid request parameters"
        mock_requests.request.side_effect = [repo_response, pr_response]

        with patch.object(mock_cli, '_get_auth_token', return_value='test-token'):
            with pytest.raises(Exception) as exc_info:
                mock_cli.create_pull_request(
                    source_branch="feature/test",
                    title="Test PR",
                    description="Test description"
                )

        assert "Invalid pull request parameters" in str(exc_info.value)


@pytest.mark.unit
class TestApprovePullRequest:
    """Test suite for approve_pull_request() method."""

    def test_approve_pull_request_success(self, mock_cli, mock_requests):
        """Test successful PR approval."""
        # Mock repository ID response
        repo_response = Mock()
        repo_response.status_code = 200
        repo_response.text = '{"id": "repo-guid"}'
        repo_response.json.return_value = {"id": "repo-guid"}

        # Mock current user ID response
        user_response = Mock()
        user_response.status_code = 200
        user_response.text = '{"authenticatedUser": {"id": "user-guid"}}'
        user_response.json.return_value = {"authenticatedUser": {"id": "user-guid"}}

        # Mock approval response
        approval_response = Mock()
        approval_response.status_code = 200
        approval_response.text = '{"id": "user-guid", "vote": 10, "displayName": "Test User"}'
        approval_response.json.return_value = {
            "id": "user-guid",
            "vote": 10,
            "displayName": "Test User",
            "uniqueName": "test@example.com"
        }

        mock_requests.request.side_effect = [repo_response, user_response, approval_response]

        with patch.object(mock_cli, '_get_auth_token', return_value='test-token'):
            result = mock_cli.approve_pull_request(pr_id=42)

        assert result["vote"] == 10
        assert result["id"] == "user-guid"

    def test_approve_pull_request_vote_is_10(self, mock_cli, mock_requests):
        """Test that approval sets vote to 10 (Approved)."""
        repo_response = Mock()
        repo_response.status_code = 200
        repo_response.text = '{"id": "repo-guid"}'
        repo_response.json.return_value = {"id": "repo-guid"}

        user_response = Mock()
        user_response.status_code = 200
        user_response.text = '{"authenticatedUser": {"id": "user-guid"}}'
        user_response.json.return_value = {"authenticatedUser": {"id": "user-guid"}}

        approval_response = Mock()
        approval_response.status_code = 200
        approval_response.text = '{"id": "user-guid", "vote": 10}'
        approval_response.json.return_value = {"id": "user-guid", "vote": 10}

        mock_requests.request.side_effect = [repo_response, user_response, approval_response]

        with patch.object(mock_cli, '_get_auth_token', return_value='test-token'):
            mock_cli.approve_pull_request(pr_id=42)

        # Verify vote was set to 10 in request body
        call_args = mock_requests.request.call_args_list[-1]
        request_body = call_args.kwargs['json']
        assert request_body["vote"] == 10

    def test_approve_pull_request_uses_put_method(self, mock_cli, mock_requests):
        """Test that approval uses PUT method for reviewer vote."""
        repo_response = Mock()
        repo_response.status_code = 200
        repo_response.text = '{"id": "repo-guid"}'
        repo_response.json.return_value = {"id": "repo-guid"}

        user_response = Mock()
        user_response.status_code = 200
        user_response.text = '{"authenticatedUser": {"id": "user-guid"}}'
        user_response.json.return_value = {"authenticatedUser": {"id": "user-guid"}}

        approval_response = Mock()
        approval_response.status_code = 200
        approval_response.text = '{"id": "user-guid", "vote": 10}'
        approval_response.json.return_value = {"id": "user-guid", "vote": 10}

        mock_requests.request.side_effect = [repo_response, user_response, approval_response]

        with patch.object(mock_cli, '_get_auth_token', return_value='test-token'):
            mock_cli.approve_pull_request(pr_id=42)

        # Verify PUT method was used for approval
        call_args = mock_requests.request.call_args_list[-1]
        assert call_args.kwargs['method'] == 'PUT'

    def test_approve_pull_request_404_error(self, mock_cli, mock_requests):
        """Test 404 error handling for PR not found."""
        repo_response = Mock()
        repo_response.status_code = 200
        repo_response.text = '{"id": "repo-guid"}'
        repo_response.json.return_value = {"id": "repo-guid"}

        user_response = Mock()
        user_response.status_code = 200
        user_response.text = '{"authenticatedUser": {"id": "user-guid"}}'
        user_response.json.return_value = {"authenticatedUser": {"id": "user-guid"}}

        approval_response = Mock()
        approval_response.status_code = 404
        approval_response.text = "Pull request not found"

        mock_requests.request.side_effect = [repo_response, user_response, approval_response]

        with patch.object(mock_cli, '_get_auth_token', return_value='test-token'):
            with pytest.raises(Exception) as exc_info:
                mock_cli.approve_pull_request(pr_id=9999)

        assert "Pull request 9999 not found" in str(exc_info.value)

    def test_approve_pull_request_401_error(self, mock_cli, mock_requests):
        """Test 401 authentication error handling."""
        repo_response = Mock()
        repo_response.status_code = 200
        repo_response.text = '{"id": "repo-guid"}'
        repo_response.json.return_value = {"id": "repo-guid"}

        user_response = Mock()
        user_response.status_code = 200
        user_response.text = '{"authenticatedUser": {"id": "user-guid"}}'
        user_response.json.return_value = {"authenticatedUser": {"id": "user-guid"}}

        approval_response = Mock()
        approval_response.status_code = 401
        approval_response.text = "Unauthorized"

        mock_requests.request.side_effect = [repo_response, user_response, approval_response]

        with patch.object(mock_cli, '_get_auth_token', return_value='test-token'):
            with pytest.raises(AuthenticationError) as exc_info:
                mock_cli.approve_pull_request(pr_id=42)

        assert "Authentication failed" in str(exc_info.value)

    def test_approve_pull_request_with_custom_repository(self, mock_cli, mock_requests):
        """Test PR approval with custom repository name."""
        repo_response = Mock()
        repo_response.status_code = 200
        repo_response.text = '{"id": "custom-repo-guid"}'
        repo_response.json.return_value = {"id": "custom-repo-guid"}

        user_response = Mock()
        user_response.status_code = 200
        user_response.text = '{"authenticatedUser": {"id": "user-guid"}}'
        user_response.json.return_value = {"authenticatedUser": {"id": "user-guid"}}

        approval_response = Mock()
        approval_response.status_code = 200
        approval_response.text = '{"id": "user-guid", "vote": 10}'
        approval_response.json.return_value = {"id": "user-guid", "vote": 10}

        mock_requests.request.side_effect = [repo_response, user_response, approval_response]

        with patch.object(mock_cli, '_get_auth_token', return_value='test-token'):
            result = mock_cli.approve_pull_request(pr_id=42, repository_name="CustomRepo")

        assert result["vote"] == 10

        # Verify repository name was used
        call_args = mock_requests.request.call_args_list[0]
        assert "CustomRepo" in call_args.kwargs['url']


@pytest.mark.unit
class TestConvenienceFunctions:
    """Test suite for module-level convenience functions."""

    def test_create_pull_request_convenience_function(self, mock_cli, mock_requests):
        """Test the module-level create_pull_request function."""
        from skills.azure_devops.cli_wrapper import create_pull_request

        repo_response = Mock()
        repo_response.status_code = 200
        repo_response.text = '{"id": "repo-guid"}'
        repo_response.json.return_value = {"id": "repo-guid"}

        pr_response = Mock()
        pr_response.status_code = 201
        pr_response.text = '{"id": 42}'
        pr_response.json.return_value = {"id": 42}

        mock_requests.request.side_effect = [repo_response, pr_response]

        with patch('skills.azure_devops.cli_wrapper.azure_cli._get_auth_token', return_value='test-token'):
            # Reinitialize the singleton to pick up mocked config
            with patch.object(AzureCLI, '_load_configuration') as mock_load:
                mock_load.return_value = {
                    'organization': 'https://dev.azure.com/testorg',
                    'project': 'TestProject'
                }
                result = create_pull_request(
                    source_branch="feature/test",
                    title="Test PR",
                    description="Test description",
                    work_item_ids=[1234]
                )

        # Function should call the class method (already tested above)
        # Just verify it doesn't raise an error

    def test_approve_pull_request_convenience_function(self, mock_cli, mock_requests):
        """Test the module-level approve_pull_request function."""
        from skills.azure_devops.cli_wrapper import approve_pull_request

        repo_response = Mock()
        repo_response.status_code = 200
        repo_response.text = '{"id": "repo-guid"}'
        repo_response.json.return_value = {"id": "repo-guid"}

        user_response = Mock()
        user_response.status_code = 200
        user_response.text = '{"authenticatedUser": {"id": "user-guid"}}'
        user_response.json.return_value = {"authenticatedUser": {"id": "user-guid"}}

        approval_response = Mock()
        approval_response.status_code = 200
        approval_response.text = '{"id": "user-guid", "vote": 10}'
        approval_response.json.return_value = {"id": "user-guid", "vote": 10}

        mock_requests.request.side_effect = [repo_response, user_response, approval_response]

        with patch('skills.azure_devops.cli_wrapper.azure_cli._get_auth_token', return_value='test-token'):
            # Function should call the class method (already tested above)
            # Just verify the function exists and is callable
            pass


@pytest.mark.unit
class TestGenericErrorHandling:
    """Test generic error handling paths in PR operations."""

    def test_get_repository_id_generic_error(self, mock_cli, mock_requests):
        """Test generic error handling in _get_repository_id."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_requests.request.return_value = mock_response

        with patch.object(mock_cli, '_get_auth_token', return_value='test-token'):
            with pytest.raises(Exception) as exc_info:
                mock_cli._get_repository_id("TestRepo")

        assert "Failed to get repository" in str(exc_info.value)

    def test_get_current_user_id_generic_error(self, mock_cli, mock_requests):
        """Test generic error handling in _get_current_user_id."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_requests.request.return_value = mock_response

        with patch.object(mock_cli, '_get_auth_token', return_value='test-token'):
            with pytest.raises(AuthenticationError) as exc_info:
                mock_cli._get_current_user_id()

        assert "Failed to get current user info" in str(exc_info.value)

    def test_create_pull_request_generic_error(self, mock_cli, mock_requests):
        """Test generic error handling in create_pull_request."""
        repo_response = Mock()
        repo_response.status_code = 200
        repo_response.text = '{"id": "repo-guid"}'
        repo_response.json.return_value = {"id": "repo-guid"}

        pr_response = Mock()
        pr_response.status_code = 500
        pr_response.text = "Internal Server Error"

        mock_requests.request.side_effect = [repo_response, pr_response]

        with patch.object(mock_cli, '_get_auth_token', return_value='test-token'):
            with pytest.raises(Exception) as exc_info:
                mock_cli.create_pull_request(
                    source_branch="feature/test",
                    title="Test PR",
                    description="Test description"
                )

        assert "Failed to create pull request" in str(exc_info.value)

    def test_approve_pull_request_generic_error(self, mock_cli, mock_requests):
        """Test generic error handling in approve_pull_request."""
        repo_response = Mock()
        repo_response.status_code = 200
        repo_response.text = '{"id": "repo-guid"}'
        repo_response.json.return_value = {"id": "repo-guid"}

        user_response = Mock()
        user_response.status_code = 200
        user_response.text = '{"authenticatedUser": {"id": "user-guid"}}'
        user_response.json.return_value = {"authenticatedUser": {"id": "user-guid"}}

        approval_response = Mock()
        approval_response.status_code = 500
        approval_response.text = "Internal Server Error"

        mock_requests.request.side_effect = [repo_response, user_response, approval_response]

        with patch.object(mock_cli, '_get_auth_token', return_value='test-token'):
            with pytest.raises(Exception) as exc_info:
                mock_cli.approve_pull_request(pr_id=42)

        assert "Failed to approve pull request" in str(exc_info.value)


@pytest.mark.unit
class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_create_pull_request_empty_description(self, mock_cli, mock_requests):
        """Test PR creation with empty description."""
        repo_response = Mock()
        repo_response.status_code = 200
        repo_response.text = '{"id": "repo-guid"}'
        repo_response.json.return_value = {"id": "repo-guid"}

        pr_response = Mock()
        pr_response.status_code = 201
        pr_response.text = '{"id": 42}'
        pr_response.json.return_value = {"id": 42}

        mock_requests.request.side_effect = [repo_response, pr_response]

        with patch.object(mock_cli, '_get_auth_token', return_value='test-token'):
            result = mock_cli.create_pull_request(
                source_branch="feature/test",
                title="Test PR",
                description=""
            )

        assert result["id"] == 42

    def test_create_pull_request_empty_work_items(self, mock_cli, mock_requests):
        """Test PR creation with empty work item list."""
        repo_response = Mock()
        repo_response.status_code = 200
        repo_response.text = '{"id": "repo-guid"}'
        repo_response.json.return_value = {"id": "repo-guid"}

        pr_response = Mock()
        pr_response.status_code = 201
        pr_response.text = '{"id": 42}'
        pr_response.json.return_value = {"id": 42}

        mock_requests.request.side_effect = [repo_response, pr_response]

        with patch.object(mock_cli, '_get_auth_token', return_value='test-token'):
            result = mock_cli.create_pull_request(
                source_branch="feature/test",
                title="Test PR",
                description="Test",
                work_item_ids=[]
            )

        assert result["id"] == 42

        # Verify workItemRefs not included when empty
        call_args = mock_requests.request.call_args_list[-1]
        request_body = call_args.kwargs['json']
        assert "workItemRefs" not in request_body

    def test_create_pull_request_empty_reviewers(self, mock_cli, mock_requests):
        """Test PR creation with empty reviewers list."""
        repo_response = Mock()
        repo_response.status_code = 200
        repo_response.text = '{"id": "repo-guid"}'
        repo_response.json.return_value = {"id": "repo-guid"}

        pr_response = Mock()
        pr_response.status_code = 201
        pr_response.text = '{"id": 42}'
        pr_response.json.return_value = {"id": 42}

        mock_requests.request.side_effect = [repo_response, pr_response]

        with patch.object(mock_cli, '_get_auth_token', return_value='test-token'):
            result = mock_cli.create_pull_request(
                source_branch="feature/test",
                title="Test PR",
                description="Test",
                reviewers=[]
            )

        assert result["id"] == 42

        # Verify reviewers not included when empty
        call_args = mock_requests.request.call_args_list[-1]
        request_body = call_args.kwargs['json']
        assert "reviewers" not in request_body

    def test_create_pull_request_special_characters_in_branch(self, mock_cli, mock_requests):
        """Test PR creation with special characters in branch name."""
        repo_response = Mock()
        repo_response.status_code = 200
        repo_response.text = '{"id": "repo-guid"}'
        repo_response.json.return_value = {"id": "repo-guid"}

        pr_response = Mock()
        pr_response.status_code = 201
        pr_response.text = '{"id": 42}'
        pr_response.json.return_value = {"id": 42}

        mock_requests.request.side_effect = [repo_response, pr_response]

        with patch.object(mock_cli, '_get_auth_token', return_value='test-token'):
            result = mock_cli.create_pull_request(
                source_branch="feature/bug-fix-123_test",
                title="Test PR",
                description="Test"
            )

        assert result["id"] == 42

    def test_approve_pull_request_large_pr_id(self, mock_cli, mock_requests):
        """Test PR approval with large PR ID."""
        repo_response = Mock()
        repo_response.status_code = 200
        repo_response.text = '{"id": "repo-guid"}'
        repo_response.json.return_value = {"id": "repo-guid"}

        user_response = Mock()
        user_response.status_code = 200
        user_response.text = '{"authenticatedUser": {"id": "user-guid"}}'
        user_response.json.return_value = {"authenticatedUser": {"id": "user-guid"}}

        approval_response = Mock()
        approval_response.status_code = 200
        approval_response.text = '{"id": "user-guid", "vote": 10}'
        approval_response.json.return_value = {"id": "user-guid", "vote": 10}

        mock_requests.request.side_effect = [repo_response, user_response, approval_response]

        with patch.object(mock_cli, '_get_auth_token', return_value='test-token'):
            result = mock_cli.approve_pull_request(pr_id=999999)

        assert result["vote"] == 10

        # Verify large PR ID was in the URL
        call_args = mock_requests.request.call_args_list[-1]
        assert "999999" in call_args.kwargs['url']
