"""
Integration tests for iteration management REST API methods.

These tests use real Azure DevOps REST API calls if AZURE_DEVOPS_EXT_PAT is set.
Tests are skipped gracefully if PAT not available.
"""

import pytest
import os
from datetime import datetime, timedelta
from skills.azure_devops.cli_wrapper import AzureCLI, AuthenticationError


# Skip all tests if PAT not available
pytestmark = pytest.mark.skipif(
    not os.environ.get('AZURE_DEVOPS_EXT_PAT'),
    reason="AZURE_DEVOPS_EXT_PAT not set - skipping integration tests"
)


@pytest.fixture
def cli():
    """Create real AzureCLI instance for integration tests."""
    return AzureCLI()


@pytest.fixture
def test_iteration_name():
    """Generate unique iteration name for testing."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"TestIteration-{timestamp}"


class TestIterationManagementIntegration:
    """Integration tests for iteration management."""

    def test_create_and_list_iteration(self, cli, test_iteration_name):
        """Test creating an iteration and verifying it appears in list."""
        # Calculate dates for iteration
        start_date = datetime.now().strftime("%Y-%m-%d")
        finish_date = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")

        # Create iteration
        created = cli.create_iteration(
            name=test_iteration_name,
            start_date=start_date,
            finish_date=finish_date
        )

        assert created['name'] == test_iteration_name
        assert 'id' in created
        assert 'attributes' in created

        # List iterations and verify new one appears
        iterations = cli.list_iterations()
        assert len(iterations) > 0

        # Find our test iteration
        found = False
        for iteration in iterations:
            if iteration['name'] == test_iteration_name:
                found = True
                assert 'startDate' in iteration.get('attributes', {})
                assert 'finishDate' in iteration.get('attributes', {})
                break

        assert found, f"Created iteration '{test_iteration_name}' not found in list"

    def test_create_iteration_without_dates(self, cli, test_iteration_name):
        """Test creating iteration without dates."""
        name = f"{test_iteration_name}-NoDates"

        created = cli.create_iteration(name=name)

        assert created['name'] == name
        assert 'id' in created
        assert created['structureType'] == 'iteration'

    def test_update_iteration_dates(self, cli, test_iteration_name):
        """Test creating an iteration and updating its dates."""
        # Create iteration
        start_date = datetime.now().strftime("%Y-%m-%d")
        finish_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")

        created = cli.create_iteration(
            name=test_iteration_name,
            start_date=start_date,
            finish_date=finish_date
        )

        iteration_id = created['id']

        # Update dates
        new_start = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        new_finish = (datetime.now() + timedelta(days=8)).strftime("%Y-%m-%d")

        updated = cli.update_iteration(
            path=test_iteration_name,
            start_date=new_start,
            finish_date=new_finish
        )

        assert updated['id'] == iteration_id
        assert 'attributes' in updated
        # Note: API returns ISO 8601 format, so we verify dates were updated
        assert 'startDate' in updated['attributes']
        assert 'finishDate' in updated['attributes']

    def test_list_iterations_returns_hierarchy(self, cli):
        """Test that list_iterations returns iteration hierarchy."""
        iterations = cli.list_iterations(depth=5)

        # Should return at least some iterations (project should have iterations)
        assert isinstance(iterations, list)

        # Each iteration should have expected fields
        for iteration in iterations:
            assert 'id' in iteration
            assert 'name' in iteration
            assert 'structureType' in iteration

    def test_create_duplicate_iteration_fails(self, cli, test_iteration_name):
        """Test that creating duplicate iteration raises error."""
        # Create first iteration
        cli.create_iteration(name=test_iteration_name)

        # Try to create duplicate
        with pytest.raises(Exception) as exc_info:
            cli.create_iteration(name=test_iteration_name)

        # Should get 400 error about duplicate
        error_msg = str(exc_info.value)
        assert '400' in error_msg or 'already exist' in error_msg.lower()

    def test_update_nonexistent_iteration_fails(self, cli):
        """Test that updating non-existent iteration raises error."""
        fake_name = f"NonExistent-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        with pytest.raises(Exception) as exc_info:
            cli.update_iteration(
                path=fake_name,
                start_date=datetime.now().strftime("%Y-%m-%d")
            )

        # Should get 404 error
        error_msg = str(exc_info.value)
        assert '404' in error_msg or 'not found' in error_msg.lower()


class TestIterationPathNormalization:
    """Integration tests for path normalization in real API calls."""

    def test_update_with_simple_name(self, cli, test_iteration_name):
        """Test updating iteration using simple name."""
        # Create iteration
        start_date = datetime.now().strftime("%Y-%m-%d")
        cli.create_iteration(name=test_iteration_name, start_date=start_date)

        # Update using simple name
        new_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        updated = cli.update_iteration(
            path=test_iteration_name,
            start_date=new_date
        )

        assert updated['name'] == test_iteration_name

    def test_update_with_full_path(self, cli, test_iteration_name):
        """Test updating iteration using full path."""
        # Create iteration
        start_date = datetime.now().strftime("%Y-%m-%d")
        created = cli.create_iteration(name=test_iteration_name, start_date=start_date)

        # Get full path from created iteration
        full_path = created.get('path', '')

        # Update using full path
        new_date = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
        updated = cli.update_iteration(
            path=full_path,
            start_date=new_date
        )

        assert updated['name'] == test_iteration_name
