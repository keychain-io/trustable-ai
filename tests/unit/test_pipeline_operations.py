"""
Unit tests for Task #1144: Pipeline operations via REST API.

Tests verify that trigger_pipeline() and get_pipeline_run() use REST API
instead of subprocess calls, with comprehensive error handling and parameter support.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from skills.azure_devops.cli_wrapper import AzureCLI, AuthenticationError


@pytest.mark.unit
class TestGetPipelineId:
    """Test suite for _get_pipeline_id() helper method."""

    @pytest.fixture
    def mock_cli(self):
        """Create AzureCLI instance with mocked config."""
        with patch.object(AzureCLI, '_load_configuration') as mock_config:
            mock_config.return_value = {
                'organization': 'https://dev.azure.com/testorg',
                'project': 'TestProject'
            }
            cli = AzureCLI()
            cli._cached_token = 'test-token'
            return cli

    def test_get_pipeline_id_success(self, mock_cli):
        """Test successful pipeline ID resolution by name."""
        mock_response = {
            "value": [
                {"id": 1, "name": "CI-Pipeline"},
                {"id": 2, "name": "CD-Pipeline"},
                {"id": 3, "name": "Test-Pipeline"}
            ]
        }

        with patch.object(mock_cli, '_make_request', return_value=mock_response):
            pipeline_id = mock_cli._get_pipeline_id("CD-Pipeline")

            assert pipeline_id == 2
            mock_cli._make_request.assert_called_once_with(
                "GET",
                "TestProject/_apis/pipelines",
                params={"api-version": "7.1"}
            )

    def test_get_pipeline_id_not_found(self, mock_cli):
        """Test pipeline not found error."""
        mock_response = {
            "value": [
                {"id": 1, "name": "CI-Pipeline"},
                {"id": 2, "name": "CD-Pipeline"}
            ]
        }

        with patch.object(mock_cli, '_make_request', return_value=mock_response):
            with pytest.raises(Exception, match="Pipeline 'Missing-Pipeline' not found"):
                mock_cli._get_pipeline_id("Missing-Pipeline")

    def test_get_pipeline_id_empty_list(self, mock_cli):
        """Test pipeline resolution with no pipelines in project."""
        mock_response = {"value": []}

        with patch.object(mock_cli, '_make_request', return_value=mock_response):
            with pytest.raises(Exception, match="Pipeline 'Test' not found"):
                mock_cli._get_pipeline_id("Test")

    def test_get_pipeline_id_404_error(self, mock_cli):
        """Test 404 error when pipelines API not accessible."""
        with patch.object(mock_cli, '_make_request', side_effect=Exception("404 Not Found")):
            with pytest.raises(Exception, match="Pipelines API not accessible"):
                mock_cli._get_pipeline_id("Test")

    def test_get_pipeline_id_auth_error(self, mock_cli):
        """Test authentication error when getting pipeline ID."""
        with patch.object(mock_cli, '_make_request', side_effect=Exception("401 Unauthorized")):
            with pytest.raises(AuthenticationError, match="Authentication failed"):
                mock_cli._get_pipeline_id("Test")


@pytest.mark.unit
class TestTriggerPipeline:
    """Test suite for trigger_pipeline() method."""

    @pytest.fixture
    def mock_cli(self):
        """Create AzureCLI instance with mocked config."""
        with patch.object(AzureCLI, '_load_configuration') as mock_config:
            mock_config.return_value = {
                'organization': 'https://dev.azure.com/testorg',
                'project': 'TestProject'
            }
            cli = AzureCLI()
            cli._cached_token = 'test-token'
            return cli

    def test_trigger_pipeline_success_no_variables(self, mock_cli):
        """Test successful pipeline trigger without variables."""
        mock_response = {
            "id": 123,
            "state": "inProgress",
            "result": None,
            "url": "https://dev.azure.com/testorg/TestProject/_build/results?buildId=123",
            "createdDate": "2025-12-17T10:00:00Z",
            "pipeline": {"id": 42, "name": "CI-Pipeline"}
        }

        with patch.object(mock_cli, '_make_request', return_value=mock_response):
            result = mock_cli.trigger_pipeline(pipeline_id=42, branch="main")

            assert result["id"] == 123
            assert result["state"] == "inProgress"
            assert result["url"] == "https://dev.azure.com/testorg/TestProject/_build/results?buildId=123"

            # Verify API call
            mock_cli._make_request.assert_called_once()
            call_args = mock_cli._make_request.call_args
            assert call_args[0][0] == "POST"
            assert call_args[0][1] == "TestProject/_apis/pipelines/42/runs"
            assert call_args[1]["data"]["resources"]["repositories"]["self"]["refName"] == "refs/heads/main"
            assert call_args[1]["params"] == {"api-version": "7.1"}

    def test_trigger_pipeline_success_with_variables(self, mock_cli):
        """Test successful pipeline trigger with variables."""
        mock_response = {
            "id": 124,
            "state": "inProgress",
            "result": None,
            "url": "https://dev.azure.com/testorg/TestProject/_build/results?buildId=124"
        }

        variables = {"environment": "production", "version": "2.0.0"}

        with patch.object(mock_cli, '_make_request', return_value=mock_response):
            result = mock_cli.trigger_pipeline(pipeline_id=42, branch="main", variables=variables)

            assert result["id"] == 124

            # Verify variables in request body
            call_args = mock_cli._make_request.call_args
            request_body = call_args[1]["data"]
            assert "variables" in request_body
            assert request_body["variables"]["environment"]["value"] == "production"
            assert request_body["variables"]["version"]["value"] == "2.0.0"

    def test_trigger_pipeline_branch_normalization(self, mock_cli):
        """Test branch name normalization to refs/heads/ format."""
        mock_response = {"id": 125, "state": "inProgress"}

        with patch.object(mock_cli, '_make_request', return_value=mock_response):
            # Test with simple branch name
            mock_cli.trigger_pipeline(pipeline_id=42, branch="feature-branch")

            call_args = mock_cli._make_request.call_args
            assert call_args[1]["data"]["resources"]["repositories"]["self"]["refName"] == "refs/heads/feature-branch"

            # Test with already-normalized branch ref
            mock_cli.trigger_pipeline(pipeline_id=42, branch="refs/heads/another-branch")

            call_args = mock_cli._make_request.call_args
            assert call_args[1]["data"]["resources"]["repositories"]["self"]["refName"] == "refs/heads/another-branch"

    def test_trigger_pipeline_404_error(self, mock_cli):
        """Test 404 error when pipeline not found."""
        with patch.object(mock_cli, '_make_request', side_effect=Exception("404 Not Found")):
            with pytest.raises(Exception, match="Pipeline 42 not found"):
                mock_cli.trigger_pipeline(pipeline_id=42, branch="main")

    def test_trigger_pipeline_auth_error(self, mock_cli):
        """Test authentication error when triggering pipeline."""
        with patch.object(mock_cli, '_make_request', side_effect=Exception("401 Unauthorized")):
            with pytest.raises(AuthenticationError, match="Authentication failed"):
                mock_cli.trigger_pipeline(pipeline_id=42, branch="main")

    def test_trigger_pipeline_403_error(self, mock_cli):
        """Test 403 forbidden error when triggering pipeline."""
        with patch.object(mock_cli, '_make_request', side_effect=Exception("403 Forbidden")):
            with pytest.raises(AuthenticationError, match="Authentication failed"):
                mock_cli.trigger_pipeline(pipeline_id=42, branch="main")

    def test_trigger_pipeline_400_error(self, mock_cli):
        """Test 400 bad request error with invalid parameters."""
        with patch.object(mock_cli, '_make_request', side_effect=Exception("400 Bad Request")):
            with pytest.raises(Exception, match="Invalid pipeline run parameters"):
                mock_cli.trigger_pipeline(pipeline_id=42, branch="invalid-branch")

    def test_trigger_pipeline_500_error(self, mock_cli):
        """Test 500 server error when triggering pipeline."""
        with patch.object(mock_cli, '_make_request', side_effect=Exception("500 Internal Server Error")):
            with pytest.raises(Exception, match="Azure DevOps server error"):
                mock_cli.trigger_pipeline(pipeline_id=42, branch="main")


@pytest.mark.unit
class TestGetPipelineRun:
    """Test suite for get_pipeline_run() method."""

    @pytest.fixture
    def mock_cli(self):
        """Create AzureCLI instance with mocked config."""
        with patch.object(AzureCLI, '_load_configuration') as mock_config:
            mock_config.return_value = {
                'organization': 'https://dev.azure.com/testorg',
                'project': 'TestProject'
            }
            cli = AzureCLI()
            cli._cached_token = 'test-token'
            return cli

    def test_get_pipeline_run_success_in_progress(self, mock_cli):
        """Test successful retrieval of in-progress pipeline run."""
        mock_response = {
            "id": 123,
            "state": "inProgress",
            "result": None,
            "finishedDate": None,
            "url": "https://dev.azure.com/testorg/TestProject/_build/results?buildId=123",
            "createdDate": "2025-12-17T10:00:00Z",
            "pipeline": {"id": 42, "name": "CI-Pipeline"}
        }

        with patch.object(mock_cli, '_make_request', return_value=mock_response):
            result = mock_cli.get_pipeline_run(pipeline_id=42, run_id=123)

            assert result["id"] == 123
            assert result["state"] == "inProgress"
            assert result["result"] is None
            assert result["finishedDate"] is None

            # Verify API call
            mock_cli._make_request.assert_called_once_with(
                "GET",
                "TestProject/_apis/pipelines/42/runs/123",
                params={"api-version": "7.1"}
            )

    def test_get_pipeline_run_success_completed(self, mock_cli):
        """Test successful retrieval of completed pipeline run."""
        mock_response = {
            "id": 124,
            "state": "completed",
            "result": "succeeded",
            "finishedDate": "2025-12-17T10:30:00Z",
            "url": "https://dev.azure.com/testorg/TestProject/_build/results?buildId=124",
            "createdDate": "2025-12-17T10:00:00Z",
            "pipeline": {"id": 42, "name": "CI-Pipeline"}
        }

        with patch.object(mock_cli, '_make_request', return_value=mock_response):
            result = mock_cli.get_pipeline_run(pipeline_id=42, run_id=124)

            assert result["id"] == 124
            assert result["state"] == "completed"
            assert result["result"] == "succeeded"
            assert result["finishedDate"] == "2025-12-17T10:30:00Z"

    def test_get_pipeline_run_failed(self, mock_cli):
        """Test retrieval of failed pipeline run."""
        mock_response = {
            "id": 125,
            "state": "completed",
            "result": "failed",
            "finishedDate": "2025-12-17T10:15:00Z",
            "url": "https://dev.azure.com/testorg/TestProject/_build/results?buildId=125"
        }

        with patch.object(mock_cli, '_make_request', return_value=mock_response):
            result = mock_cli.get_pipeline_run(pipeline_id=42, run_id=125)

            assert result["result"] == "failed"
            assert result["state"] == "completed"

    def test_get_pipeline_run_canceled(self, mock_cli):
        """Test retrieval of canceled pipeline run."""
        mock_response = {
            "id": 126,
            "state": "completed",
            "result": "canceled",
            "finishedDate": "2025-12-17T10:05:00Z"
        }

        with patch.object(mock_cli, '_make_request', return_value=mock_response):
            result = mock_cli.get_pipeline_run(pipeline_id=42, run_id=126)

            assert result["result"] == "canceled"

    def test_get_pipeline_run_404_error(self, mock_cli):
        """Test 404 error when pipeline run not found."""
        with patch.object(mock_cli, '_make_request', side_effect=Exception("404 Not Found")):
            with pytest.raises(Exception, match="Pipeline run 999 not found"):
                mock_cli.get_pipeline_run(pipeline_id=42, run_id=999)

    def test_get_pipeline_run_auth_error(self, mock_cli):
        """Test authentication error when getting pipeline run."""
        with patch.object(mock_cli, '_make_request', side_effect=Exception("401 Unauthorized")):
            with pytest.raises(AuthenticationError, match="Authentication failed"):
                mock_cli.get_pipeline_run(pipeline_id=42, run_id=123)

    def test_get_pipeline_run_403_error(self, mock_cli):
        """Test 403 forbidden error when getting pipeline run."""
        with patch.object(mock_cli, '_make_request', side_effect=Exception("403 Forbidden")):
            with pytest.raises(AuthenticationError, match="Authentication failed"):
                mock_cli.get_pipeline_run(pipeline_id=42, run_id=123)

    def test_get_pipeline_run_500_error(self, mock_cli):
        """Test 500 server error when getting pipeline run."""
        with patch.object(mock_cli, '_make_request', side_effect=Exception("500 Internal Server Error")):
            with pytest.raises(Exception, match="Azure DevOps server error"):
                mock_cli.get_pipeline_run(pipeline_id=42, run_id=123)


@pytest.mark.unit
class TestPipelineOperationsIntegration:
    """Integration tests for pipeline trigger and status workflow."""

    @pytest.fixture
    def mock_cli(self):
        """Create AzureCLI instance with mocked config."""
        with patch.object(AzureCLI, '_load_configuration') as mock_config:
            mock_config.return_value = {
                'organization': 'https://dev.azure.com/testorg',
                'project': 'TestProject'
            }
            cli = AzureCLI()
            cli._cached_token = 'test-token'
            return cli

    def test_trigger_and_monitor_pipeline_workflow(self, mock_cli):
        """Test complete workflow: trigger pipeline and monitor status."""
        # Mock trigger response
        trigger_response = {
            "id": 123,
            "state": "inProgress",
            "result": None,
            "pipeline": {"id": 42}
        }

        # Mock status responses (simulating progression)
        status_response_in_progress = {
            "id": 123,
            "state": "inProgress",
            "result": None,
            "finishedDate": None
        }

        status_response_completed = {
            "id": 123,
            "state": "completed",
            "result": "succeeded",
            "finishedDate": "2025-12-17T10:30:00Z"
        }

        with patch.object(mock_cli, '_make_request') as mock_request:
            # First call: trigger pipeline
            mock_request.return_value = trigger_response
            trigger_result = mock_cli.trigger_pipeline(pipeline_id=42, branch="main")
            assert trigger_result["id"] == 123

            # Second call: check status (in progress)
            mock_request.return_value = status_response_in_progress
            status = mock_cli.get_pipeline_run(pipeline_id=42, run_id=123)
            assert status["state"] == "inProgress"

            # Third call: check status (completed)
            mock_request.return_value = status_response_completed
            status = mock_cli.get_pipeline_run(pipeline_id=42, run_id=123)
            assert status["state"] == "completed"
            assert status["result"] == "succeeded"

            # Verify call count
            assert mock_request.call_count == 3
