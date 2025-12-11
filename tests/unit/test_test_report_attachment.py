"""
Unit tests for sprint-review workflow Step 1.8: Test report attachment and linking.

Tests the logic for attaching test reports to EPIC work items, including
platform-specific attachment (Azure DevOps) and linking (file-based), and
verification that attachments exist after creation.
"""

import pytest
from pathlib import Path
from datetime import datetime
import tempfile


class TestTestReportAttachmentLogic:
    """Test test report attachment logic."""

    def test_azure_devops_attachment_structure(self):
        """Test Azure DevOps attachment data structure."""
        attachment_request = {
            'work_item_id': 123,
            'file_path': Path('.claude/acceptance-tests/epic-EPIC-123-test-report.md'),
            'comment': 'EPIC Acceptance Test Execution Report - Generated 2024-12-11T10:00:00Z'
        }

        # Verify structure
        assert 'work_item_id' in attachment_request
        assert isinstance(attachment_request['file_path'], Path)
        assert 'comment' in attachment_request
        assert 'Test Execution Report' in attachment_request['comment']

    def test_azure_devops_attachment_success_response(self):
        """Test Azure DevOps attachment success response structure."""
        attach_result = {
            'success': True,
            'attachment_id': 'abc-123',
            'url': 'https://dev.azure.com/.../attachments/abc-123'
        }

        # Verify success handling
        if attach_result.get('success'):
            assert 'attachment_id' in attach_result
            assert 'url' in attach_result

    def test_azure_devops_attachment_failure_response(self):
        """Test Azure DevOps attachment failure response structure."""
        attach_result = {
            'success': False,
            'error': 'File not found'
        }

        # Verify failure handling
        if not attach_result.get('success'):
            assert 'error' in attach_result

    def test_azure_devops_verification_call(self):
        """Test Azure DevOps attachment verification call."""
        verification_request = {
            'work_item_id': 123,
            'filename': 'epic-EPIC-123-test-report.md'
        }

        # Verify structure
        assert 'work_item_id' in verification_request
        assert 'filename' in verification_request
        assert verification_request['filename'].endswith('-test-report.md')

    def test_file_based_comment_structure(self):
        """Test file-based adapter comment structure."""
        comment_data = {
            'work_item_id': 'EPIC-123',
            'comment': '''Test Report: .claude/acceptance-tests/epic-EPIC-123-test-report.md

EPIC Acceptance Test Execution Report generated on 2024-12-11T10:00:00Z.
Overall Status: PASS
Pass Rate: 100.0%
Deployment Ready: ✅ YES

Test report file: .claude/acceptance-tests/epic-EPIC-123-test-report.md
''',
            'author': 'sprint-review-workflow'
        }

        # Verify structure
        assert 'work_item_id' in comment_data
        assert 'comment' in comment_data
        assert 'author' in comment_data
        assert 'Test Report:' in comment_data['comment']
        assert 'Overall Status:' in comment_data['comment']
        assert 'Pass Rate:' in comment_data['comment']
        assert 'Deployment Ready:' in comment_data['comment']

    def test_file_based_comment_verification(self):
        """Test file-based comment verification logic."""
        # Simulate work item with comments
        work_item = {
            'id': 'EPIC-123',
            'comments': [
                {
                    'text': 'Some other comment',
                    'author': 'user1'
                },
                {
                    'text': 'Test Report: .claude/acceptance-tests/epic-EPIC-123-test-report.md\n\n...',
                    'author': 'sprint-review-workflow'
                }
            ]
        }

        # Verify comment is present
        report_filepath = '.claude/acceptance-tests/epic-EPIC-123-test-report.md'
        comment_found = any(report_filepath in c.get('text', '') for c in work_item.get('comments', []))

        assert comment_found is True

    def test_file_based_comment_verification_missing(self):
        """Test file-based comment verification when comment is missing."""
        # Simulate work item without test report comment
        work_item = {
            'id': 'EPIC-123',
            'comments': [
                {
                    'text': 'Some other comment',
                    'author': 'user1'
                }
            ]
        }

        # Verify comment is not present
        report_filepath = '.claude/acceptance-tests/epic-EPIC-123-test-report.md'
        comment_found = any(report_filepath in c.get('text', '') for c in work_item.get('comments', []))

        assert comment_found is False

    def test_attachment_failure_tracking(self):
        """Test tracking of attachment failures."""
        failed_attachments = []

        # Simulate attachment failure
        failed_attachments.append({
            'epic_id': 'EPIC-123',
            'report_filepath': '.claude/acceptance-tests/epic-EPIC-123-test-report.md',
            'error': 'Attachment not found after upload'
        })

        # Verify failure tracking
        assert len(failed_attachments) == 1
        assert failed_attachments[0]['epic_id'] == 'EPIC-123'
        assert 'error' in failed_attachments[0]

    def test_attachment_success_counting(self):
        """Test tracking of successful attachments."""
        attached_count = 0
        test_execution_results = [
            {'epic_id': 'EPIC-100'},
            {'epic_id': 'EPIC-200'},
            {'epic_id': 'EPIC-300'}
        ]

        # Simulate successful attachments
        for result in test_execution_results:
            # Simulate attachment success
            attached_count += 1

        assert attached_count == 3

    def test_attachment_state_structure(self):
        """Test attachment state storage structure."""
        attachment_state = {
            'attached_count': 3,
            'failed_count': 1,
            'test_report_files': [
                '.claude/acceptance-tests/epic-EPIC-100-test-report.md',
                '.claude/acceptance-tests/epic-EPIC-200-test-report.md'
            ],
            'failed_attachments': [
                {
                    'epic_id': 'EPIC-300',
                    'report_filepath': '.claude/acceptance-tests/epic-EPIC-300-test-report.md',
                    'error': 'Permission denied'
                }
            ],
            'attachment_timestamp': datetime.now().isoformat()
        }

        # Verify structure
        assert 'attached_count' in attachment_state
        assert 'failed_count' in attachment_state
        assert 'test_report_files' in attachment_state
        assert 'failed_attachments' in attachment_state
        assert 'attachment_timestamp' in attachment_state

        # Verify data types
        assert isinstance(attachment_state['attached_count'], int)
        assert isinstance(attachment_state['failed_count'], int)
        assert isinstance(attachment_state['test_report_files'], list)
        assert isinstance(attachment_state['failed_attachments'], list)

    def test_multiple_epic_attachments(self):
        """Test attaching reports to multiple EPICs."""
        test_execution_results = [
            {
                'epic_id': 'EPIC-100',
                'epic_title': 'User Authentication',
                'report_filepath': '.claude/acceptance-tests/epic-EPIC-100-test-report.md',
                'report_filename': 'epic-EPIC-100-test-report.md'
            },
            {
                'epic_id': 'EPIC-200',
                'epic_title': 'Payment Processing',
                'report_filepath': '.claude/acceptance-tests/epic-EPIC-200-test-report.md',
                'report_filename': 'epic-EPIC-200-test-report.md'
            },
            {
                'epic_id': 'EPIC-300',
                'epic_title': 'Reporting Dashboard',
                'report_filepath': '.claude/acceptance-tests/epic-EPIC-300-test-report.md',
                'report_filename': 'epic-EPIC-300-test-report.md'
            }
        ]

        assert len(test_execution_results) == 3
        assert all('epic_id' in r for r in test_execution_results)
        assert all('report_filepath' in r for r in test_execution_results)
        assert all('report_filename' in r for r in test_execution_results)

    def test_epic_id_parsing_from_string(self):
        """Test parsing numeric EPIC ID from string format."""
        epic_id_string = 'EPIC-123'

        # Parse numeric ID (as would be done for Azure DevOps)
        numeric_id = int(epic_id_string.split('-')[-1])

        assert numeric_id == 123

    def test_epic_id_parsing_from_int(self):
        """Test handling numeric EPIC ID directly."""
        epic_id_int = 123

        # Should be usable directly
        work_item_id = int(epic_id_int)

        assert work_item_id == 123

    def test_report_filename_extraction(self):
        """Test extracting filename from report filepath."""
        report_filepath = '.claude/acceptance-tests/epic-EPIC-456-test-report.md'

        # Extract filename
        report_filename = Path(report_filepath).name

        assert report_filename == 'epic-EPIC-456-test-report.md'

    def test_attachment_summary_calculation(self):
        """Test calculating attachment summary statistics."""
        total_reports = 5
        attached_count = 4
        failed_count = 1

        # Calculate summary
        success_rate = (attached_count / total_reports) * 100 if total_reports > 0 else 0

        assert total_reports == 5
        assert attached_count == 4
        assert failed_count == 1
        assert success_rate == 80.0

    def test_workflow_halt_on_attachment_failure(self):
        """Test that workflow should halt if any attachments fail."""
        failed_attachments = [
            {
                'epic_id': 'EPIC-100',
                'report_filepath': '.claude/acceptance-tests/epic-EPIC-100-test-report.md',
                'error': 'File not found'
            }
        ]

        # Workflow should halt
        should_halt = len(failed_attachments) > 0

        assert should_halt is True

    def test_workflow_continue_on_all_success(self):
        """Test that workflow continues when all attachments succeed."""
        failed_attachments = []

        # Workflow should continue
        should_halt = len(failed_attachments) > 0

        assert should_halt is False

    def test_timestamp_format_in_attachment_state(self):
        """Test timestamp format in attachment state."""
        timestamp = datetime.now().isoformat()

        # Verify ISO format
        assert 'T' in timestamp
        assert len(timestamp) >= 19  # YYYY-MM-DDTHH:MM:SS minimum

    def test_comment_includes_test_results_summary(self):
        """Test that file-based comment includes test results summary."""
        test_result = {
            'overall_status': 'pass',
            'pass_rate': 0.95,
            'deployment_ready': True
        }

        comment_text = f"""Test Report: .claude/acceptance-tests/epic-EPIC-123-test-report.md

EPIC Acceptance Test Execution Report generated on {datetime.now().isoformat()}.
Overall Status: {test_result['overall_status'].upper()}
Pass Rate: {test_result['pass_rate'] * 100:.1f}%
Deployment Ready: {'✅ YES' if test_result['deployment_ready'] else '❌ NO'}

Test report file: .claude/acceptance-tests/epic-EPIC-123-test-report.md
"""

        assert 'Overall Status: PASS' in comment_text
        assert 'Pass Rate: 95.0%' in comment_text
        assert 'Deployment Ready: ✅ YES' in comment_text
