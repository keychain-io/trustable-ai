"""
Unit tests for iteration management REST API methods.

Tests create_iteration(), list_iterations(), and update_iteration() methods
with mocked REST API responses.
"""

import pytest
from unittest.mock import MagicMock, patch
from skills.azure_devops.cli_wrapper import AzureCLI, AuthenticationError


@pytest.fixture
def mock_cli():
    """Create AzureCLI instance with mocked configuration."""
    with patch.object(AzureCLI, '_load_configuration') as mock_config:
        mock_config.return_value = {
            'organization': 'https://dev.azure.com/testorg',
            'project': 'TestProject'
        }
        cli = AzureCLI()
        cli._cached_token = 'test-token-12345'
        return cli


class TestCreateIteration:
    """Tests for create_iteration() method."""

    def test_create_iteration_success(self, mock_cli):
        """Test successful iteration creation with dates."""
        mock_response = {
            'id': 12345,
            'identifier': 'abc-123',
            'name': 'Sprint 6',
            'structureType': 'iteration',
            'path': '\\TestProject\\Iteration\\Sprint 6',
            'attributes': {
                'startDate': '2025-01-01T00:00:00Z',
                'finishDate': '2025-01-14T00:00:00Z'
            }
        }

        with patch.object(mock_cli, '_make_request', return_value=mock_response):
            result = mock_cli.create_iteration(
                name='Sprint 6',
                start_date='2025-01-01',
                finish_date='2025-01-14'
            )

            assert result['id'] == 12345
            assert result['name'] == 'Sprint 6'
            assert result['attributes']['startDate'] == '2025-01-01T00:00:00Z'
            assert result['attributes']['finishDate'] == '2025-01-14T00:00:00Z'

    def test_create_iteration_without_dates(self, mock_cli):
        """Test iteration creation without dates."""
        mock_response = {
            'id': 12346,
            'name': 'Sprint 7',
            'structureType': 'iteration',
            'path': '\\TestProject\\Iteration\\Sprint 7'
        }

        with patch.object(mock_cli, '_make_request', return_value=mock_response):
            result = mock_cli.create_iteration(name='Sprint 7')

            assert result['id'] == 12346
            assert result['name'] == 'Sprint 7'

    def test_create_iteration_with_start_date_only(self, mock_cli):
        """Test iteration creation with only start date."""
        mock_response = {
            'id': 12347,
            'name': 'Sprint 8',
            'attributes': {
                'startDate': '2025-02-01T00:00:00Z'
            }
        }

        with patch.object(mock_cli, '_make_request', return_value=mock_response):
            result = mock_cli.create_iteration(
                name='Sprint 8',
                start_date='2025-02-01'
            )

            assert result['attributes']['startDate'] == '2025-02-01T00:00:00Z'
            assert 'finishDate' not in result['attributes']

    def test_create_iteration_with_finish_date_only(self, mock_cli):
        """Test iteration creation with only finish date."""
        mock_response = {
            'id': 12348,
            'name': 'Sprint 9',
            'attributes': {
                'finishDate': '2025-03-01T00:00:00Z'
            }
        }

        with patch.object(mock_cli, '_make_request', return_value=mock_response):
            result = mock_cli.create_iteration(
                name='Sprint 9',
                finish_date='2025-03-01'
            )

            assert result['attributes']['finishDate'] == '2025-03-01T00:00:00Z'
            assert 'startDate' not in result['attributes']

    def test_create_iteration_already_exists_400(self, mock_cli):
        """Test error when iteration already exists (400)."""
        with patch.object(mock_cli, '_make_request', side_effect=Exception('400 Bad Request')):
            with pytest.raises(Exception) as exc_info:
                mock_cli.create_iteration(name='Sprint 6')

            assert 'already exist' in str(exc_info.value)
            assert 'Sprint 6' in str(exc_info.value)

    def test_create_iteration_auth_failure_401(self, mock_cli):
        """Test authentication failure (401)."""
        with patch.object(mock_cli, '_make_request', side_effect=Exception('401 Unauthorized')):
            with pytest.raises(AuthenticationError) as exc_info:
                mock_cli.create_iteration(name='Sprint 6')

            assert 'Authentication failed' in str(exc_info.value)
            assert 'PAT token' in str(exc_info.value)

    def test_create_iteration_permission_denied_403(self, mock_cli):
        """Test permission denied (403)."""
        with patch.object(mock_cli, '_make_request', side_effect=Exception('403 Forbidden')):
            with pytest.raises(AuthenticationError) as exc_info:
                mock_cli.create_iteration(name='Sprint 6')

            assert 'Authentication failed' in str(exc_info.value)

    def test_create_iteration_project_not_found_404(self, mock_cli):
        """Test project not found (404)."""
        with patch.object(mock_cli, '_make_request', side_effect=Exception('404 Not Found')):
            with pytest.raises(Exception) as exc_info:
                mock_cli.create_iteration(name='Sprint 6')

            assert 'Project' in str(exc_info.value)
            assert 'not found' in str(exc_info.value)

    def test_create_iteration_server_error_500(self, mock_cli):
        """Test server error (500)."""
        with patch.object(mock_cli, '_make_request', side_effect=Exception('500 Internal Server Error')):
            with pytest.raises(Exception) as exc_info:
                mock_cli.create_iteration(name='Sprint 6')

            assert 'server error' in str(exc_info.value)
            assert 'temporarily unavailable' in str(exc_info.value)


class TestListIterations:
    """Tests for list_iterations() method."""

    def test_list_iterations_success(self, mock_cli):
        """Test successful iteration listing."""
        mock_response = {
            'id': 1,
            'name': 'Iteration',
            'structureType': 'iteration',
            'hasChildren': True,
            'children': [
                {
                    'id': 12345,
                    'name': 'Sprint 6',
                    'structureType': 'iteration',
                    'hasChildren': False,
                    'attributes': {
                        'startDate': '2025-01-01T00:00:00Z',
                        'finishDate': '2025-01-14T00:00:00Z'
                    }
                },
                {
                    'id': 12346,
                    'name': 'Sprint 7',
                    'structureType': 'iteration',
                    'hasChildren': False,
                    'attributes': {
                        'startDate': '2025-01-15T00:00:00Z',
                        'finishDate': '2025-01-28T00:00:00Z'
                    }
                }
            ]
        }

        with patch.object(mock_cli, '_make_request', return_value=mock_response):
            result = mock_cli.list_iterations()

            assert len(result) == 2
            assert result[0]['name'] == 'Sprint 6'
            assert result[1]['name'] == 'Sprint 7'
            assert result[0]['attributes']['startDate'] == '2025-01-01T00:00:00Z'

    def test_list_iterations_empty(self, mock_cli):
        """Test listing when no iterations exist."""
        mock_response = {
            'id': 1,
            'name': 'Iteration',
            'structureType': 'iteration',
            'hasChildren': False,
            'children': []
        }

        with patch.object(mock_cli, '_make_request', return_value=mock_response):
            result = mock_cli.list_iterations()

            assert len(result) == 0

    def test_list_iterations_nested_hierarchy(self, mock_cli):
        """Test listing with nested iteration hierarchy."""
        mock_response = {
            'id': 1,
            'name': 'Iteration',
            'structureType': 'iteration',
            'hasChildren': True,
            'children': [
                {
                    'id': 12345,
                    'name': 'Sprint 6',
                    'hasChildren': True,
                    'children': [
                        {
                            'id': 12346,
                            'name': 'Sub-Sprint 1',
                            'hasChildren': False
                        }
                    ]
                }
            ]
        }

        with patch.object(mock_cli, '_make_request', return_value=mock_response):
            result = mock_cli.list_iterations()

            # Should flatten hierarchy
            assert len(result) == 2
            assert result[0]['name'] == 'Sprint 6'
            assert result[1]['name'] == 'Sub-Sprint 1'

    def test_list_iterations_with_custom_depth(self, mock_cli):
        """Test listing with custom depth parameter."""
        mock_response = {
            'id': 1,
            'name': 'Iteration',
            'children': []
        }

        with patch.object(mock_cli, '_make_request', return_value=mock_response) as mock_request:
            mock_cli.list_iterations(depth=5)

            # Verify depth parameter passed to API
            call_args = mock_request.call_args
            assert call_args[1]['params']['$depth'] == '5'

    def test_list_iterations_project_not_found_404(self, mock_cli):
        """Test project not found (404)."""
        with patch.object(mock_cli, '_make_request', side_effect=Exception('404 Not Found')):
            with pytest.raises(Exception) as exc_info:
                mock_cli.list_iterations()

            assert 'Project' in str(exc_info.value)
            assert 'not found' in str(exc_info.value)

    def test_list_iterations_auth_failure_401(self, mock_cli):
        """Test authentication failure (401)."""
        with patch.object(mock_cli, '_make_request', side_effect=Exception('401 Unauthorized')):
            with pytest.raises(AuthenticationError) as exc_info:
                mock_cli.list_iterations()

            assert 'Authentication failed' in str(exc_info.value)

    def test_list_iterations_server_error_500(self, mock_cli):
        """Test server error (500)."""
        with patch.object(mock_cli, '_make_request', side_effect=Exception('500 Internal Server Error')):
            with pytest.raises(Exception) as exc_info:
                mock_cli.list_iterations()

            assert 'server error' in str(exc_info.value)


class TestUpdateIteration:
    """Tests for update_iteration() method."""

    def test_update_iteration_both_dates(self, mock_cli):
        """Test updating iteration with both dates."""
        mock_response = {
            'id': 12345,
            'name': 'Sprint 6',
            'attributes': {
                'startDate': '2025-01-02T00:00:00Z',
                'finishDate': '2025-01-16T00:00:00Z'
            }
        }

        with patch.object(mock_cli, '_make_request', return_value=mock_response):
            result = mock_cli.update_iteration(
                path='Sprint 6',
                start_date='2025-01-02',
                finish_date='2025-01-16'
            )

            assert result['attributes']['startDate'] == '2025-01-02T00:00:00Z'
            assert result['attributes']['finishDate'] == '2025-01-16T00:00:00Z'

    def test_update_iteration_start_date_only(self, mock_cli):
        """Test updating only start date."""
        mock_response = {
            'id': 12345,
            'name': 'Sprint 6',
            'attributes': {
                'startDate': '2025-01-03T00:00:00Z',
                'finishDate': '2025-01-14T00:00:00Z'
            }
        }

        with patch.object(mock_cli, '_make_request', return_value=mock_response):
            result = mock_cli.update_iteration(
                path='Sprint 6',
                start_date='2025-01-03'
            )

            assert result['attributes']['startDate'] == '2025-01-03T00:00:00Z'

    def test_update_iteration_finish_date_only(self, mock_cli):
        """Test updating only finish date."""
        mock_response = {
            'id': 12345,
            'name': 'Sprint 6',
            'attributes': {
                'startDate': '2025-01-01T00:00:00Z',
                'finishDate': '2025-01-20T00:00:00Z'
            }
        }

        with patch.object(mock_cli, '_make_request', return_value=mock_response):
            result = mock_cli.update_iteration(
                path='Sprint 6',
                finish_date='2025-01-20'
            )

            assert result['attributes']['finishDate'] == '2025-01-20T00:00:00Z'

    def test_update_iteration_no_dates_raises_error(self, mock_cli):
        """Test that updating without dates raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            mock_cli.update_iteration(path='Sprint 6')

        assert 'At least one' in str(exc_info.value)
        assert 'start_date or finish_date' in str(exc_info.value)

    def test_update_iteration_full_path(self, mock_cli):
        """Test updating with full iteration path."""
        mock_response = {
            'id': 12345,
            'name': 'Sprint 6',
            'attributes': {
                'startDate': '2025-01-01T00:00:00Z',
                'finishDate': '2025-01-14T00:00:00Z'
            }
        }

        with patch.object(mock_cli, '_make_request', return_value=mock_response) as mock_request:
            mock_cli.update_iteration(
                path='\\TestProject\\Iteration\\Sprint 6',
                start_date='2025-01-01'
            )

            # Verify path was normalized
            call_args = mock_request.call_args
            endpoint = call_args[0][1]
            assert 'Sprint 6' in endpoint

    def test_update_iteration_not_found_404(self, mock_cli):
        """Test iteration not found (404)."""
        with patch.object(mock_cli, '_make_request', side_effect=Exception('404 Not Found')):
            with pytest.raises(Exception) as exc_info:
                mock_cli.update_iteration(path='Sprint 6', start_date='2025-01-01')

            assert 'not found' in str(exc_info.value)
            assert 'Sprint 6' in str(exc_info.value)

    def test_update_iteration_auth_failure_401(self, mock_cli):
        """Test authentication failure (401)."""
        with patch.object(mock_cli, '_make_request', side_effect=Exception('401 Unauthorized')):
            with pytest.raises(AuthenticationError) as exc_info:
                mock_cli.update_iteration(path='Sprint 6', start_date='2025-01-01')

            assert 'Authentication failed' in str(exc_info.value)

    def test_update_iteration_invalid_params_400(self, mock_cli):
        """Test invalid parameters (400)."""
        with patch.object(mock_cli, '_make_request', side_effect=Exception('400 Bad Request')):
            with pytest.raises(Exception) as exc_info:
                mock_cli.update_iteration(path='Sprint 6', start_date='2025-01-01')

            assert 'Invalid parameters' in str(exc_info.value)

    def test_update_iteration_server_error_500(self, mock_cli):
        """Test server error (500)."""
        with patch.object(mock_cli, '_make_request', side_effect=Exception('500 Internal Server Error')):
            with pytest.raises(Exception) as exc_info:
                mock_cli.update_iteration(path='Sprint 6', start_date='2025-01-01')

            assert 'server error' in str(exc_info.value)


class TestHelperMethods:
    """Tests for helper methods used by iteration management."""

    def test_format_date_iso8601(self, mock_cli):
        """Test date formatting to ISO 8601."""
        result = mock_cli._format_date_iso8601('2025-01-15')
        assert result == '2025-01-15T00:00:00Z'

    def test_format_date_iso8601_invalid_format(self, mock_cli):
        """Test date formatting with invalid format."""
        with pytest.raises(ValueError) as exc_info:
            mock_cli._format_date_iso8601('01/15/2025')

        assert 'Invalid date format' in str(exc_info.value)
        assert 'YYYY-MM-DD' in str(exc_info.value)

    def test_normalize_iteration_path_simple_name(self, mock_cli):
        """Test path normalization with simple name."""
        result = mock_cli._normalize_iteration_path('Sprint 6', 'TestProject')
        assert result == 'Sprint 6'

    def test_normalize_iteration_path_full_path(self, mock_cli):
        """Test path normalization with full path."""
        result = mock_cli._normalize_iteration_path(
            '\\TestProject\\Iteration\\Sprint 6',
            'TestProject'
        )
        assert result == 'Sprint 6'

    def test_normalize_iteration_path_without_leading_backslash(self, mock_cli):
        """Test path normalization without leading backslash."""
        result = mock_cli._normalize_iteration_path(
            'TestProject\\Iteration\\Sprint 6',
            'TestProject'
        )
        assert result == 'Sprint 6'

    def test_flatten_iteration_hierarchy_single_level(self, mock_cli):
        """Test flattening single-level hierarchy."""
        nodes = [
            {'id': 1, 'name': 'Sprint 1', 'hasChildren': False},
            {'id': 2, 'name': 'Sprint 2', 'hasChildren': False}
        ]
        result = mock_cli._flatten_iteration_hierarchy(nodes)
        assert len(result) == 2
        assert result[0]['name'] == 'Sprint 1'
        assert result[1]['name'] == 'Sprint 2'

    def test_flatten_iteration_hierarchy_nested(self, mock_cli):
        """Test flattening nested hierarchy."""
        nodes = [
            {
                'id': 1,
                'name': 'Sprint 1',
                'hasChildren': True,
                'children': [
                    {'id': 2, 'name': 'Sub-Sprint 1', 'hasChildren': False}
                ]
            }
        ]
        result = mock_cli._flatten_iteration_hierarchy(nodes)
        assert len(result) == 2
        assert result[0]['name'] == 'Sprint 1'
        assert result[1]['name'] == 'Sub-Sprint 1'

    def test_flatten_iteration_hierarchy_empty(self, mock_cli):
        """Test flattening empty hierarchy."""
        result = mock_cli._flatten_iteration_hierarchy([])
        assert len(result) == 0
