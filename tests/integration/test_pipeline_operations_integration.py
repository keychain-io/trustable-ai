"""
Integration tests for Task #1144: Pipeline operations via REST API.

Tests verify that pipeline operations work with real Azure DevOps instance
(or skip gracefully when credentials not available).
"""
import pytest
import os
from skills.azure_devops.cli_wrapper import AzureCLI, AuthenticationError


# Skip all tests in this module if Azure DevOps credentials not available
pytestmark = pytest.mark.skipif(
    not os.environ.get('AZURE_DEVOPS_EXT_PAT'),
    reason="Azure DevOps PAT token not set (AZURE_DEVOPS_EXT_PAT)"
)


@pytest.mark.integration
@pytest.mark.azure
class TestPipelineOperationsIntegration:
    """Integration tests for pipeline operations with real Azure DevOps."""

    @pytest.fixture
    def cli(self):
        """Create AzureCLI instance with real configuration."""
        return AzureCLI()

    def test_get_pipeline_id_real_connection(self, cli):
        """
        Test pipeline ID resolution with real Azure DevOps connection.

        Note: This test will fail if no pipelines exist in the project.
        Consider it a configuration validation test.
        """
        try:
            # Try to list all pipelines
            project = cli._get_project()
            endpoint = f"{project}/_apis/pipelines"
            params = {"api-version": "7.1"}

            result = cli._make_request("GET", endpoint, params=params)
            pipelines = result.get("value", [])

            # If pipelines exist, test ID resolution
            if pipelines:
                first_pipeline = pipelines[0]
                pipeline_name = first_pipeline.get("name")
                pipeline_id = cli._get_pipeline_id(pipeline_name)

                assert pipeline_id == first_pipeline.get("id")
            else:
                pytest.skip("No pipelines configured in project")

        except AuthenticationError:
            pytest.fail("Authentication failed - verify PAT token has Build (Read) scope")
        except Exception as e:
            pytest.fail(f"Unexpected error: {e}")

    def test_trigger_pipeline_auth_required(self, cli):
        """
        Test that triggering pipeline requires proper authentication.

        This test verifies error handling without actually triggering a pipeline.
        """
        # Use a non-existent pipeline ID to avoid triggering real pipelines
        with pytest.raises(Exception) as exc_info:
            cli.trigger_pipeline(pipeline_id=999999, branch="main")

        # Should get either 404 (pipeline not found) or 401/403 (auth error)
        error_msg = str(exc_info.value)
        assert any(x in error_msg for x in ["not found", "Authentication failed", "Pipeline 999999"])

    def test_get_pipeline_run_auth_required(self, cli):
        """
        Test that getting pipeline run requires proper authentication.

        This test verifies error handling without accessing real pipeline runs.
        """
        # Use a non-existent pipeline/run ID combination
        with pytest.raises(Exception) as exc_info:
            cli.get_pipeline_run(pipeline_id=999999, run_id=999999)

        # Should get either 404 (not found) or 401/403 (auth error)
        error_msg = str(exc_info.value)
        assert any(x in error_msg for x in ["not found", "Authentication failed"])

    @pytest.mark.slow
    def test_pipeline_list_and_details(self, cli):
        """
        Test listing pipelines and getting details.

        This is a read-only test that verifies API connectivity.
        """
        try:
            project = cli._get_project()
            endpoint = f"{project}/_apis/pipelines"
            params = {"api-version": "7.1"}

            # List pipelines
            result = cli._make_request("GET", endpoint, params=params)
            pipelines = result.get("value", [])

            if not pipelines:
                pytest.skip("No pipelines configured in project")

            # Verify pipeline structure
            first_pipeline = pipelines[0]
            assert "id" in first_pipeline
            assert "name" in first_pipeline

            # Get pipeline details
            pipeline_id = first_pipeline["id"]
            pipeline_endpoint = f"{project}/_apis/pipelines/{pipeline_id}"
            pipeline_details = cli._make_request("GET", pipeline_endpoint, params=params)

            assert pipeline_details["id"] == pipeline_id
            assert "name" in pipeline_details

        except AuthenticationError:
            pytest.fail("Authentication failed - verify PAT token has Build (Read) scope")
        except Exception as e:
            pytest.fail(f"Unexpected error: {e}")

    @pytest.mark.slow
    def test_pipeline_runs_list(self, cli):
        """
        Test listing recent pipeline runs (read-only).

        This verifies the runs API is accessible without triggering new runs.
        """
        try:
            project = cli._get_project()

            # First, get a pipeline
            pipelines_endpoint = f"{project}/_apis/pipelines"
            params = {"api-version": "7.1"}
            pipelines_result = cli._make_request("GET", pipelines_endpoint, params=params)
            pipelines = pipelines_result.get("value", [])

            if not pipelines:
                pytest.skip("No pipelines configured in project")

            pipeline_id = pipelines[0]["id"]

            # Try to list runs for this pipeline
            runs_endpoint = f"{project}/_apis/pipelines/{pipeline_id}/runs"
            runs_result = cli._make_request("GET", runs_endpoint, params=params)

            # If runs exist, verify structure
            runs = runs_result.get("value", [])
            if runs:
                first_run = runs[0]
                assert "id" in first_run
                assert "state" in first_run

                # Test get_pipeline_run with a real run
                run_id = first_run["id"]
                run_details = cli.get_pipeline_run(pipeline_id=pipeline_id, run_id=run_id)

                assert run_details["id"] == run_id
                assert "state" in run_details
                assert run_details["state"] in ["inProgress", "completed", "canceling"]

        except AuthenticationError:
            pytest.fail("Authentication failed - verify PAT token has Build (Read) scope")
        except Exception as e:
            pytest.fail(f"Unexpected error: {e}")


@pytest.mark.integration
@pytest.mark.azure
class TestPipelineErrorHandling:
    """Integration tests for error handling scenarios."""

    @pytest.fixture
    def cli(self):
        """Create AzureCLI instance with real configuration."""
        return AzureCLI()

    def test_invalid_pipeline_id_404(self, cli):
        """Test that invalid pipeline ID returns clear 404 error."""
        with pytest.raises(Exception) as exc_info:
            cli.trigger_pipeline(pipeline_id=999999, branch="main")

        error_msg = str(exc_info.value)
        assert "Pipeline 999999 not found" in error_msg or "404" in error_msg

    def test_invalid_run_id_404(self, cli):
        """Test that invalid run ID returns clear 404 error."""
        with pytest.raises(Exception) as exc_info:
            cli.get_pipeline_run(pipeline_id=1, run_id=999999)

        error_msg = str(exc_info.value)
        assert "not found" in error_msg.lower() or "404" in error_msg

    def test_invalid_pipeline_name(self, cli):
        """Test that invalid pipeline name raises clear error."""
        with pytest.raises(Exception) as exc_info:
            cli._get_pipeline_id("NonExistentPipeline12345")

        error_msg = str(exc_info.value)
        assert "not found" in error_msg.lower()
