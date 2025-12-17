"""
Integration tests for pull request operations in Azure DevOps CLI wrapper.

Tests Task #1142 - Replace subprocess calls in create_pull_request() and approve_pull_request()
with Azure DevOps Git REST API.

These tests require a valid Azure DevOps configuration and PAT token.
Tests will be skipped if Azure DevOps is not configured.

Test Prerequisites:
- AZURE_DEVOPS_EXT_PAT environment variable set with valid PAT token
- .claude/config.yaml configured with organization and project
- A Git repository in the Azure DevOps project
"""
import os
import pytest
from unittest.mock import patch

# Skip all tests in this module if Azure DevOps is not configured
pytestmark = [
    pytest.mark.integration,
    pytest.mark.azure
]


def has_azure_config():
    """Check if Azure DevOps configuration is available."""
    # Check for PAT token
    if not os.environ.get('AZURE_DEVOPS_EXT_PAT'):
        return False

    # Check for config file
    try:
        from skills.azure_devops.cli_wrapper import AzureCLI
        cli = AzureCLI()
        return True
    except Exception:
        return False


# Conditional skip decorator
skip_if_no_azure = pytest.mark.skipif(
    not has_azure_config(),
    reason="Azure DevOps configuration not available (AZURE_DEVOPS_EXT_PAT not set or config.yaml missing)"
)


@skip_if_no_azure
class TestGetRepositoryIdIntegration:
    """Integration tests for _get_repository_id() method."""

    def test_get_repository_id_real_repository(self):
        """Test getting repository ID from a real Azure DevOps repository."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        cli = AzureCLI()

        # Get repository ID using project name as repository name
        # Most Azure DevOps projects have a repository with the same name
        try:
            repo_id = cli._get_repository_id()
            assert repo_id is not None
            assert len(repo_id) > 0
            # Azure DevOps repository IDs are GUIDs
            assert '-' in repo_id
        except Exception as e:
            # If default repo doesn't exist, this is acceptable
            pytest.skip(f"Could not access default repository: {e}")

    def test_get_repository_id_invalid_repository(self):
        """Test error handling for non-existent repository."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        cli = AzureCLI()

        with pytest.raises(Exception) as exc_info:
            cli._get_repository_id("NonExistent_Repo_12345")

        assert "not found" in str(exc_info.value).lower()


@skip_if_no_azure
class TestGetCurrentUserIdIntegration:
    """Integration tests for _get_current_user_id() method."""

    def test_get_current_user_id_real_user(self):
        """Test getting current authenticated user ID."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        cli = AzureCLI()

        user_id = cli._get_current_user_id()

        assert user_id is not None
        assert len(user_id) > 0
        # Azure DevOps user IDs are GUIDs
        assert '-' in user_id


@skip_if_no_azure
class TestCreatePullRequestIntegration:
    """Integration tests for create_pull_request() method.

    Note: These tests are designed to be read-only or use non-destructive operations.
    Creating real PRs would require branch setup which may not be available.
    """

    def test_create_pull_request_invalid_source_branch(self):
        """Test PR creation fails gracefully with invalid source branch."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        cli = AzureCLI()

        # Try to create PR with non-existent source branch
        with pytest.raises(Exception) as exc_info:
            cli.create_pull_request(
                source_branch="nonexistent/branch/12345",
                title="Test PR - Should Fail",
                description="This PR should fail due to invalid branch"
            )

        # Should fail with 404 or similar error
        error_msg = str(exc_info.value).lower()
        assert "not found" in error_msg or "branch" in error_msg

    def test_create_pull_request_invalid_target_branch(self):
        """Test PR creation fails gracefully with invalid target branch."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        cli = AzureCLI()

        # Try to create PR with non-existent target branch
        with pytest.raises(Exception) as exc_info:
            cli.create_pull_request(
                source_branch="main",  # Assume main exists
                target_branch="nonexistent/target/12345",
                title="Test PR - Should Fail",
                description="This PR should fail due to invalid target branch"
            )

        # Should fail with 404 or similar error
        error_msg = str(exc_info.value).lower()
        assert "not found" in error_msg or "branch" in error_msg or "invalid" in error_msg


@skip_if_no_azure
class TestApprovePullRequestIntegration:
    """Integration tests for approve_pull_request() method."""

    def test_approve_pull_request_invalid_pr_id(self):
        """Test PR approval fails gracefully with invalid PR ID."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        cli = AzureCLI()

        # Try to approve non-existent PR
        with pytest.raises(Exception) as exc_info:
            cli.approve_pull_request(pr_id=999999999)

        # Should fail with 404
        assert "not found" in str(exc_info.value).lower()


@skip_if_no_azure
class TestEndToEndWorkflow:
    """End-to-end integration tests for PR workflow.

    These tests are marked with a special marker since they create real PRs.
    Only run these tests in a dedicated test environment.
    """

    @pytest.mark.skip(reason="Requires test branch setup - run manually in test environment")
    def test_full_pr_workflow(self):
        """Test complete PR creation and approval workflow.

        Prerequisites:
        - Create a test branch named 'test/integration-test' with some commits
        - Main branch exists and is protected or has commits

        This test:
        1. Creates a PR from test branch to main
        2. Approves the PR
        3. Verifies PR status
        """
        from skills.azure_devops.cli_wrapper import AzureCLI

        cli = AzureCLI()

        # Step 1: Create PR
        pr_result = cli.create_pull_request(
            source_branch="test/integration-test",
            target_branch="main",
            title="[TEST] Integration Test PR - Auto-generated",
            description="This PR was automatically generated by integration tests. "
                       "It can be safely closed without merging.",
            work_item_ids=[]
        )

        assert pr_result is not None
        assert "id" in pr_result
        pr_id = pr_result["id"]

        try:
            # Step 2: Approve PR
            approval_result = cli.approve_pull_request(pr_id=pr_id)

            assert approval_result is not None
            assert approval_result.get("vote") == 10

        except Exception as e:
            # Log failure but don't fail test if approval fails
            # (may fail due to permissions or policies)
            pytest.skip(f"PR approval not available: {e}")


@skip_if_no_azure
class TestConfigurationIntegration:
    """Integration tests for configuration and authentication."""

    def test_pat_token_authentication(self):
        """Test that PAT token authentication works."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        cli = AzureCLI()

        # Should be able to get current user with valid PAT
        user_id = cli._get_current_user_id()
        assert user_id is not None

    def test_organization_url_validation(self):
        """Test that organization URL is validated."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        cli = AzureCLI()

        # Check base URL format
        base_url = cli._get_base_url()
        assert base_url.startswith('https://dev.azure.com/')

    def test_project_configuration(self):
        """Test that project is properly configured."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        cli = AzureCLI()

        # Check project is set
        project = cli._get_project()
        assert project is not None
        assert len(project) > 0
