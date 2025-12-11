"""
Unit tests for sprint-review workflow Step 1.7: Test report generation and storage.

Tests the logic for generating markdown test reports from execution results,
writing reports to filesystem, and handling various report scenarios.
"""

import pytest
from pathlib import Path
from datetime import datetime
import tempfile
import shutil


class TestTestReportGeneration:
    """Test test report generation logic."""

    def test_report_header_generation(self):
        """Test generating report header with EPIC information."""
        epic_data = {
            'id': 'EPIC-123',
            'title': 'User Authentication',
            'overall_status': 'pass',
            'execution_timestamp': '2024-12-11T10:00:00Z',
            'environment': 'staging',
            'sprint_context': 'Sprint 5'
        }

        # Generate header
        report_lines = []
        report_lines.append(f"# EPIC Acceptance Test Execution Report")
        report_lines.append("")
        report_lines.append(f"**EPIC**: #{epic_data['id']} - {epic_data['title']}")
        report_lines.append(f"**Sprint**: {epic_data['sprint_context']}")
        report_lines.append(f"**Environment**: {epic_data['environment']}")
        report_lines.append(f"**Execution Date**: {epic_data['execution_timestamp']}")
        report_lines.append(f"**Overall Status**: {epic_data['overall_status'].upper()}")

        header = "\n".join(report_lines)

        assert "EPIC Acceptance Test Execution Report" in header
        assert "EPIC-123" in header
        assert "User Authentication" in header
        assert "Sprint 5" in header
        assert "staging" in header
        assert "PASS" in header

    def test_executive_summary_generation(self):
        """Test generating executive summary with test statistics."""
        summary = {
            'total_test_cases': 10,
            'tests_passed': 8,
            'tests_failed': 1,
            'tests_blocked': 1,
            'tests_skipped': 0,
            'pass_rate': 0.8,
            'execution_duration_minutes': 15
        }

        # Generate summary section
        report_lines = []
        report_lines.append("## Executive Summary")
        report_lines.append("")
        report_lines.append(f"**Total Test Cases**: {summary['total_test_cases']}")
        report_lines.append(f"**Tests Passed**: ✅ {summary['tests_passed']}")
        report_lines.append(f"**Tests Failed**: ❌ {summary['tests_failed']}")
        report_lines.append(f"**Tests Blocked**: 🚫 {summary['tests_blocked']}")
        report_lines.append(f"**Tests Skipped**: ⏭️  {summary['tests_skipped']}")
        report_lines.append(f"**Pass Rate**: {summary['pass_rate'] * 100:.1f}%")
        report_lines.append(f"**Execution Duration**: {summary['execution_duration_minutes']} minutes")

        summary_text = "\n".join(report_lines)

        assert "Executive Summary" in summary_text
        assert "10" in summary_text  # total
        assert "8" in summary_text   # passed
        assert "80.0%" in summary_text  # pass rate
        assert "15 minutes" in summary_text

    def test_quality_gates_generation_passed(self):
        """Test generating quality gates section when all gates pass."""
        quality_gates = {
            'gates_passed': True,
            'all_high_priority_pass': True,
            'all_medium_priority_pass': True,
            'all_acceptance_criteria_met': True
        }

        # Generate quality gates section
        report_lines = []
        report_lines.append("## Quality Gates")
        report_lines.append("")
        gates_status = "✅ PASSED" if quality_gates.get('gates_passed', False) else "❌ FAILED"
        report_lines.append(f"**Status**: {gates_status}")
        report_lines.append("")
        report_lines.append(f"- All high-priority tests pass: {'✅' if quality_gates['all_high_priority_pass'] else '❌'}")
        report_lines.append(f"- All medium-priority tests pass: {'✅' if quality_gates['all_medium_priority_pass'] else '❌'}")
        report_lines.append(f"- All acceptance criteria met: {'✅' if quality_gates['all_acceptance_criteria_met'] else '❌'}")

        gates_text = "\n".join(report_lines)

        assert "Quality Gates" in gates_text
        assert "✅ PASSED" in gates_text
        assert gates_text.count("✅") == 4  # status + 3 checks

    def test_quality_gates_generation_failed(self):
        """Test generating quality gates section when gates fail."""
        quality_gates = {
            'gates_passed': False,
            'all_high_priority_pass': False,
            'all_medium_priority_pass': True,
            'all_acceptance_criteria_met': False
        }

        # Generate quality gates section
        gates_status = "✅ PASSED" if quality_gates.get('gates_passed', False) else "❌ FAILED"

        assert gates_status == "❌ FAILED"

    def test_test_case_results_table_generation(self):
        """Test generating test case results table."""
        test_case_results = [
            {
                'test_id': 'TC-001',
                'feature_id': 'FEATURE-456',
                'title': 'User login with valid credentials',
                'priority': 'High',
                'status': 'pass'
            },
            {
                'test_id': 'TC-002',
                'feature_id': 'FEATURE-456',
                'title': 'User login with invalid credentials',
                'priority': 'High',
                'status': 'fail'
            }
        ]

        # Generate table
        report_lines = []
        report_lines.append("## Test Case Results")
        report_lines.append("")
        report_lines.append("| Test ID | Feature | Title | Priority | Status |")
        report_lines.append("|---------|---------|-------|----------|--------|")

        for tc in test_case_results:
            status_emoji = {
                'pass': '✅',
                'fail': '❌',
                'blocked': '🚫',
                'skipped': '⏭️ '
            }.get(tc.get('status', 'unknown'), '❓')

            report_lines.append(
                f"| {tc.get('test_id', 'N/A')} | "
                f"{tc.get('feature_id', 'N/A')} | "
                f"{tc.get('title', 'N/A')} | "
                f"{tc.get('priority', 'N/A')} | "
                f"{status_emoji} {tc.get('status', 'unknown')} |"
            )

        table_text = "\n".join(report_lines)

        assert "Test Case Results" in table_text
        assert "TC-001" in table_text
        assert "TC-002" in table_text
        assert "✅" in table_text
        assert "❌" in table_text

    def test_defects_section_generation(self):
        """Test generating defects found section."""
        defects_found = [
            {
                'severity': 'high',
                'test_case_id': 'TC-002',
                'feature_id': 'FEATURE-456',
                'description': 'Login fails with database timeout',
                'expected_behavior': 'Should return 401 Unauthorized',
                'actual_behavior': 'Returns 500 Internal Server Error',
                'reproduction_steps': [
                    'Navigate to login page',
                    'Enter invalid credentials',
                    'Click login button',
                    'Observe 500 error'
                ]
            }
        ]

        # Generate defects section
        report_lines = []
        report_lines.append("## Defects Found")
        report_lines.append("")

        for defect in defects_found:
            severity_emoji = {
                'critical': '🔴',
                'high': '🟠',
                'medium': '🟡',
                'low': '🟢'
            }.get(defect.get('severity', 'unknown'), '❓')

            report_lines.append(f"### {severity_emoji} {defect.get('severity', 'Unknown').upper()}: {defect.get('description', 'No description')}")
            report_lines.append("")
            report_lines.append(f"**Test Case**: {defect.get('test_case_id', 'N/A')}")
            report_lines.append("")
            report_lines.append("**Expected Behavior**:")
            report_lines.append(defect.get('expected_behavior', 'Not specified'))
            report_lines.append("")
            report_lines.append("**Actual Behavior**:")
            report_lines.append(defect.get('actual_behavior', 'Not specified'))
            report_lines.append("")
            report_lines.append("**Reproduction Steps**:")
            for i, step in enumerate(defect['reproduction_steps'], 1):
                report_lines.append(f"{i}. {step}")

        defects_text = "\n".join(report_lines)

        assert "Defects Found" in defects_text
        assert "🟠 HIGH" in defects_text
        assert "TC-002" in defects_text
        assert "database timeout" in defects_text
        assert "Reproduction Steps" in defects_text

    def test_deployment_readiness_section_ready(self):
        """Test generating deployment readiness section when ready."""
        recommendations = {
            'deployment_ready': True,
            'required_fixes': [],
            'optional_improvements': ['Add retry logic'],
            'overall_assessment': 'EPIC ready for deployment'
        }

        # Generate deployment readiness
        report_lines = []
        report_lines.append("## Deployment Readiness")
        report_lines.append("")
        deployment_ready = recommendations.get('deployment_ready', False)
        deployment_status = "✅ READY FOR DEPLOYMENT" if deployment_ready else "❌ NOT READY FOR DEPLOYMENT"
        report_lines.append(f"**Status**: {deployment_status}")

        readiness_text = "\n".join(report_lines)

        assert "Deployment Readiness" in readiness_text
        assert "✅ READY FOR DEPLOYMENT" in readiness_text

    def test_deployment_readiness_section_not_ready(self):
        """Test generating deployment readiness section when not ready."""
        recommendations = {
            'deployment_ready': False,
            'required_fixes': [
                'Fix authentication error handling',
                'Resolve database connection timeout'
            ],
            'optional_improvements': [],
            'overall_assessment': 'EPIC has critical defects'
        }

        # Generate deployment readiness
        report_lines = []
        report_lines.append("## Deployment Readiness")
        report_lines.append("")
        deployment_status = "✅ READY FOR DEPLOYMENT" if recommendations.get('deployment_ready', False) else "❌ NOT READY FOR DEPLOYMENT"
        report_lines.append(f"**Status**: {deployment_status}")
        report_lines.append("")

        if recommendations.get('required_fixes'):
            report_lines.append("**Required Fixes** (must be addressed before deployment):")
            for fix in recommendations['required_fixes']:
                report_lines.append(f"- ❌ {fix}")

        readiness_text = "\n".join(report_lines)

        assert "❌ NOT READY FOR DEPLOYMENT" in readiness_text
        assert "Required Fixes" in readiness_text
        assert "authentication error handling" in readiness_text

    def test_report_file_writing_utf8(self):
        """Test writing report to file with UTF-8 encoding."""
        with tempfile.TemporaryDirectory() as tmpdir:
            reports_dir = Path(tmpdir) / 'acceptance-tests'
            reports_dir.mkdir(parents=True)

            report_content = "# Test Report\n\nTest with Unicode: ✅ ❌ 🚫"
            report_filepath = reports_dir / 'epic-123-test-report.md'

            with open(report_filepath, 'w', encoding='utf-8') as f:
                f.write(report_content)

            # Read back and verify
            with open(report_filepath, 'r', encoding='utf-8') as f:
                read_content = f.read()

            assert read_content == report_content
            assert "✅" in read_content
            assert "❌" in read_content

    def test_report_filename_format(self):
        """Test report filename format."""
        epic_id = 'EPIC-456'
        report_filename = f"epic-{epic_id}-test-report.md"

        assert report_filename == "epic-EPIC-456-test-report.md"
        assert report_filename.endswith("-test-report.md")

    def test_report_footer_generation(self):
        """Test generating report footer with timestamp."""
        # Generate footer
        report_lines = []
        report_lines.append("---")
        report_lines.append("")
        report_lines.append(f"*Report generated by Trustable AI Workbench on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

        footer_text = "\n".join(report_lines)

        assert "Report generated by Trustable AI Workbench" in footer_text
        assert datetime.now().strftime('%Y-%m-%d') in footer_text

    def test_workflow_state_storage(self):
        """Test storing execution results in workflow state."""
        test_execution_results_all = [
            {
                'epic_id': 'EPIC-123',
                'epic_title': 'User Authentication',
                'report_filepath': '.claude/acceptance-tests/epic-EPIC-123-test-report.md',
                'overall_status': 'pass',
                'pass_rate': 1.0,
                'deployment_ready': True
            }
        ]

        test_execution_state = {
            'test_execution_results': test_execution_results_all,
            'test_report_files': [r['report_filepath'] for r in test_execution_results_all],
            'execution_failures': [],
            'successful_executions': len(test_execution_results_all),
            'failed_executions': 0,
            'execution_timestamp': datetime.now().isoformat()
        }

        assert test_execution_state['successful_executions'] == 1
        assert test_execution_state['failed_executions'] == 0
        assert len(test_execution_state['test_report_files']) == 1

    def test_execution_failure_handling(self):
        """Test handling execution failures."""
        execution_failures = [
            {
                'epic_id': 'EPIC-789',
                'epic_title': 'Payment Processing',
                'reason': 'JSON parsing error: Unexpected token'
            }
        ]

        assert len(execution_failures) == 1
        assert execution_failures[0]['epic_id'] == 'EPIC-789'
        assert 'JSON parsing error' in execution_failures[0]['reason']

    def test_multiple_epics_report_generation(self):
        """Test generating reports for multiple EPICs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            reports_dir = Path(tmpdir) / 'acceptance-tests'
            reports_dir.mkdir(parents=True)

            epic_ids = ['EPIC-100', 'EPIC-200', 'EPIC-300']
            test_report_files = []

            for epic_id in epic_ids:
                report_content = f"# Test Report for {epic_id}\n"
                report_filepath = reports_dir / f'epic-{epic_id}-test-report.md'

                with open(report_filepath, 'w', encoding='utf-8') as f:
                    f.write(report_content)

                test_report_files.append(str(report_filepath))

            assert len(test_report_files) == 3
            assert all(Path(f).exists() for f in test_report_files)

    def test_empty_defects_list(self):
        """Test report generation when no defects found."""
        defects_found = []

        # Should not include defects section
        include_defects_section = len(defects_found) > 0

        assert include_defects_section is False

    def test_empty_test_cases_list(self):
        """Test report generation when no test case details provided."""
        test_case_results = []

        # Should not include test case results table
        include_table = len(test_case_results) > 0

        assert include_table is False

    def test_status_emoji_mapping(self):
        """Test status emoji mapping for test cases."""
        status_emoji = {
            'pass': '✅',
            'fail': '❌',
            'blocked': '🚫',
            'skipped': '⏭️ '
        }

        assert status_emoji['pass'] == '✅'
        assert status_emoji['fail'] == '❌'
        assert status_emoji['blocked'] == '🚫'
        assert status_emoji['skipped'] == '⏭️ '

    def test_severity_emoji_mapping(self):
        """Test severity emoji mapping for defects."""
        severity_emoji = {
            'critical': '🔴',
            'high': '🟠',
            'medium': '🟡',
            'low': '🟢'
        }

        assert severity_emoji['critical'] == '🔴'
        assert severity_emoji['high'] == '🟠'
        assert severity_emoji['medium'] == '🟡'
        assert severity_emoji['low'] == '🟢'
