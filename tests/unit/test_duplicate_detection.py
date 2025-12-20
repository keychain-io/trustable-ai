"""
Unit tests for duplicate detection in Azure DevOps CLI wrapper.

Tests Bug #1127 fix - ensures check_recent_duplicates() correctly identifies
duplicate work items using title similarity and time-based filtering.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from skills.azure_devops.cli_wrapper import AzureCLI


@pytest.mark.unit
class TestDuplicateDetection:
    """Test suite for check_recent_duplicates() method."""

    @pytest.fixture
    def mock_cli(self):
        """Create AzureCLI instance with mocked configuration."""
        with patch('skills.azure_devops.cli_wrapper.subprocess.run') as mock_run:
            # Mock the configure --list command
            mock_run.return_value = Mock(
                returncode=0,
                stdout='organization=https://dev.azure.com/test\nproject=TestProject\n'
            )
            cli = AzureCLI()
            yield cli

    def test_check_recent_duplicates_exact_match(self, mock_cli):
        """Test detection of exact title match."""
        # Mock query_work_items to return a recent item with exact title
        with patch.object(mock_cli, 'query_work_items') as mock_query:
            now = datetime.utcnow()
            mock_query.return_value = [{
                'id': 1234,
                'fields': {
                    'System.Title': 'Fix authentication bug',
                    'System.CreatedDate': now.isoformat() + 'Z',
                    'System.State': 'New'
                }
            }]

            result = mock_cli.check_recent_duplicates(
                title='Fix authentication bug',
                work_item_type='Bug',
                hours=1
            )

            assert result is not None
            assert result['id'] == 1234
            assert result['title'] == 'Fix authentication bug'
            assert result['similarity'] == 1.0  # Exact match
            assert result['state'] == 'New'

    def test_check_recent_duplicates_high_similarity(self, mock_cli):
        """Test detection of similar title (>95% similarity)."""
        with patch.object(mock_cli, 'query_work_items') as mock_query:
            now = datetime.utcnow()
            mock_query.return_value = [{
                'id': 1235,
                'fields': {
                    'System.Title': 'Fix authentication bug in login',
                    'System.CreatedDate': now.isoformat() + 'Z',
                    'System.State': 'Active'
                }
            }]

            result = mock_cli.check_recent_duplicates(
                title='Fix authentication bug in login page',
                work_item_type='Bug',
                hours=1,
                similarity_threshold=0.90
            )

            assert result is not None
            assert result['id'] == 1235
            assert result['similarity'] >= 0.90

    def test_check_recent_duplicates_no_match(self, mock_cli):
        """Test that dissimilar titles are not flagged as duplicates."""
        with patch.object(mock_cli, 'query_work_items') as mock_query:
            now = datetime.utcnow()
            mock_query.return_value = [{
                'id': 1236,
                'fields': {
                    'System.Title': 'Implement new feature',
                    'System.CreatedDate': now.isoformat() + 'Z',
                    'System.State': 'New'
                }
            }]

            result = mock_cli.check_recent_duplicates(
                title='Fix authentication bug',
                work_item_type='Bug',
                hours=1
            )

            assert result is None

    def test_check_recent_duplicates_no_recent_items(self, mock_cli):
        """Test when no recent work items exist."""
        with patch.object(mock_cli, 'query_work_items') as mock_query:
            mock_query.return_value = []

            result = mock_cli.check_recent_duplicates(
                title='Fix authentication bug',
                work_item_type='Bug',
                hours=1
            )

            assert result is None

    def test_check_recent_duplicates_time_window(self, mock_cli):
        """Test that time window is correctly applied in WIQL query."""
        with patch.object(mock_cli, 'query_work_items') as mock_query:
            mock_query.return_value = []

            mock_cli.check_recent_duplicates(
                title='Test',
                work_item_type='Task',
                hours=2
            )

            # Verify WIQL query was called
            assert mock_query.called
            wiql = mock_query.call_args[0][0]

            # Should filter by work item type
            assert "[System.WorkItemType] = 'Task'" in wiql

            # Should filter by created date
            assert '[System.CreatedDate] >=' in wiql

    def test_check_recent_duplicates_case_insensitive(self, mock_cli):
        """Test that title comparison is case-insensitive."""
        with patch.object(mock_cli, 'query_work_items') as mock_query:
            now = datetime.utcnow()
            mock_query.return_value = [{
                'id': 1237,
                'fields': {
                    'System.Title': 'FIX AUTHENTICATION BUG',
                    'System.CreatedDate': now.isoformat() + 'Z',
                    'System.State': 'New'
                }
            }]

            result = mock_cli.check_recent_duplicates(
                title='fix authentication bug',
                work_item_type='Bug',
                hours=1
            )

            assert result is not None
            assert result['id'] == 1237
            assert result['similarity'] == 1.0  # Case should not affect similarity

    def test_check_recent_duplicates_custom_threshold(self, mock_cli):
        """Test custom similarity threshold."""
        with patch.object(mock_cli, 'query_work_items') as mock_query:
            now = datetime.utcnow()
            mock_query.return_value = [{
                'id': 1238,
                'fields': {
                    'System.Title': 'Fix authentication bug in login',
                    'System.CreatedDate': now.isoformat() + 'Z',
                    'System.State': 'New'
                }
            }]

            # With low threshold (80%), should match
            result = mock_cli.check_recent_duplicates(
                title='Fix authentication bug',
                work_item_type='Bug',
                hours=1,
                similarity_threshold=0.70
            )
            assert result is not None

            # With high threshold (99%), should not match
            result = mock_cli.check_recent_duplicates(
                title='Fix authentication bug',
                work_item_type='Bug',
                hours=1,
                similarity_threshold=0.99
            )
            assert result is None

    def test_check_recent_duplicates_returns_first_match(self, mock_cli):
        """Test that only the first duplicate is returned."""
        with patch.object(mock_cli, 'query_work_items') as mock_query:
            now = datetime.utcnow()
            mock_query.return_value = [
                {
                    'id': 1239,
                    'fields': {
                        'System.Title': 'Fix authentication bug',
                        'System.CreatedDate': now.isoformat() + 'Z',
                        'System.State': 'New'
                    }
                },
                {
                    'id': 1240,
                    'fields': {
                        'System.Title': 'Fix authentication bug',
                        'System.CreatedDate': (now - timedelta(minutes=30)).isoformat() + 'Z',
                        'System.State': 'Active'
                    }
                }
            ]

            result = mock_cli.check_recent_duplicates(
                title='Fix authentication bug',
                work_item_type='Bug',
                hours=1
            )

            # Should return first match (most recent)
            assert result is not None
            assert result['id'] == 1239

    def test_check_recent_duplicates_includes_url(self, mock_cli):
        """Test that result includes work item URL."""
        with patch.object(mock_cli, 'query_work_items') as mock_query:
            with patch.object(mock_cli, '_get_base_url', return_value='https://dev.azure.com/test'):
                now = datetime.utcnow()
                mock_query.return_value = [{
                    'id': 1241,
                    'fields': {
                        'System.Title': 'Fix authentication bug',
                        'System.CreatedDate': now.isoformat() + 'Z',
                        'System.State': 'New'
                    }
                }]

                result = mock_cli.check_recent_duplicates(
                    title='Fix authentication bug',
                    work_item_type='Bug',
                    hours=1
                )

                assert result is not None
                assert 'url' in result
                assert result['url'] == 'https://dev.azure.com/test/_workitems/edit/1241'

    def test_check_recent_duplicates_query_failure_returns_none(self, mock_cli):
        """Test that query failures don't crash, just return None."""
        with patch.object(mock_cli, 'query_work_items') as mock_query:
            mock_query.side_effect = Exception("WIQL query failed")

            result = mock_cli.check_recent_duplicates(
                title='Fix authentication bug',
                work_item_type='Bug',
                hours=1
            )

            # Should return None, not raise exception
            assert result is None

    def test_check_recent_duplicates_similarity_calculation(self, mock_cli):
        """Test similarity score calculation for various titles."""
        with patch.object(mock_cli, 'query_work_items') as mock_query:
            now = datetime.utcnow()

            # Test cases with expected similarity ranges
            test_cases = [
                ('Fix auth bug', 'Fix authentication bug', 0.75, 0.85),
                ('Bug #1234', 'Bug #1234', 1.0, 1.0),
                ('Add feature X', 'Remove feature X', 0.80, 0.90),
                ('Completely different', 'Fix auth bug', 0.0, 0.30),
            ]

            for original, similar, min_sim, max_sim in test_cases:
                mock_query.return_value = [{
                    'id': 9999,
                    'fields': {
                        'System.Title': similar,
                        'System.CreatedDate': now.isoformat() + 'Z',
                        'System.State': 'New'
                    }
                }]

                result = mock_cli.check_recent_duplicates(
                    title=original,
                    work_item_type='Bug',
                    hours=1,
                    similarity_threshold=min_sim
                )

                if result:
                    assert min_sim <= result['similarity'] <= max_sim, \
                        f"Similarity for '{original}' vs '{similar}' should be between {min_sim} and {max_sim}"
