"""
Integration tests for skills installation during init.

Tests that skills are properly copied to .claude/skills/ and can be imported.
"""
import pytest
import sys
from pathlib import Path
from click.testing import CliRunner
from cli.main import cli


@pytest.mark.integration
class TestSkillsInit:
    """Test that skills are properly installed during init."""

    def test_skills_copied_during_init(self, tmp_path):
        """Test that skills are copied to .claude/skills/ during init."""
        runner = CliRunner()

        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            td_path = Path(td)

            # Run init with non-interactive mode
            result = runner.invoke(cli, [
                'init',
                '--no-interactive',
                '--config-path', str(td_path / '.claude' / 'config.yaml')
            ])

            assert result.exit_code == 0, f"Init failed: {result.output}"

            # Check that .claude/skills/ directory was created
            skills_dir = td_path / '.claude' / 'skills'
            assert skills_dir.exists(), f"Skills directory not created: {result.output}"
            assert skills_dir.is_dir()

            # Check that __init__.py exists
            assert (skills_dir / '__init__.py').exists()

            # Check that work_tracking skill exists
            work_tracking_dir = skills_dir / 'work_tracking'
            assert work_tracking_dir.exists()
            assert work_tracking_dir.is_dir()
            assert (work_tracking_dir / '__init__.py').exists()

            # Check that azure_devops skill exists
            azure_devops_dir = skills_dir / 'azure_devops'
            assert azure_devops_dir.exists()
            assert azure_devops_dir.is_dir()
            assert (azure_devops_dir / '__init__.py').exists()
            assert (azure_devops_dir / 'cli_wrapper.py').exists()

    def test_skills_can_be_imported_after_init(self, tmp_path):
        """Test that skills can be imported from .claude/skills/ after init."""
        runner = CliRunner()

        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            td_path = Path(td)

            # Run init
            result = runner.invoke(cli, [
                'init',
                '--no-interactive',
                '--config-path', str(td_path / '.claude' / 'config.yaml')
            ])

            assert result.exit_code == 0

            skills_dir = td_path / '.claude' / 'skills'

            # Test importing work_tracking skill
            original_path = sys.path.copy()
            try:
                sys.path.insert(0, str(skills_dir))

                # Import should not raise
                from work_tracking import get_adapter, UnifiedWorkTrackingAdapter
                assert get_adapter is not None
                assert UnifiedWorkTrackingAdapter is not None

                # Clean up the import
                if 'work_tracking' in sys.modules:
                    del sys.modules['work_tracking']
            finally:
                sys.path = original_path

    def test_skills_import_message_in_output(self, tmp_path):
        """Test that init command shows skills installation message."""
        runner = CliRunner()

        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            td_path = Path(td)

            result = runner.invoke(cli, [
                'init',
                '--no-interactive',
                '--config-path', str(td_path / '.claude' / 'config.yaml')
            ])

            assert result.exit_code == 0
            output = result.output

            # Should mention skills installation
            assert "Installing skills" in output or "skills" in output.lower()

    def test_skills_verification_runs(self, tmp_path):
        """Test that skills import verification runs during init."""
        runner = CliRunner()

        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            td_path = Path(td)

            result = runner.invoke(cli, [
                'init',
                '--no-interactive',
                '--config-path', str(td_path / '.claude' / 'config.yaml')
            ])

            assert result.exit_code == 0
            output = result.output

            # Should mention skills verification
            assert ("Skills import verified" in output or
                    "Installed" in output and "skills" in output.lower())

    def test_azure_cli_wrapper_has_parent_id(self, tmp_path):
        """Test that Azure CLI wrapper in .claude/skills has parent_id support."""
        runner = CliRunner()

        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            td_path = Path(td)

            # Run init
            result = runner.invoke(cli, [
                'init',
                '--no-interactive',
                '--config-path', str(td_path / '.claude' / 'config.yaml')
            ])

            assert result.exit_code == 0

            # Read the cli_wrapper.py file
            cli_wrapper_path = td_path / '.claude' / 'skills' / 'azure_devops' / 'cli_wrapper.py'
            assert cli_wrapper_path.exists()

            content = cli_wrapper_path.read_text(encoding='utf-8')

            # Check that create_work_item has parent_id parameter
            assert 'parent_id: Optional[int] = None' in content
            assert 'parent_id=item.get(\'parent_id\')' in content

    def test_work_tracking_adapter_passes_parent_id(self, tmp_path):
        """Test that work_tracking adapter in .claude/skills passes parent_id."""
        runner = CliRunner()

        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            td_path = Path(td)

            # Run init
            result = runner.invoke(cli, [
                'init',
                '--no-interactive',
                '--config-path', str(td_path / '.claude' / 'config.yaml')
            ])

            assert result.exit_code == 0

            # Read the work_tracking/__init__.py file
            work_tracking_path = td_path / '.claude' / 'skills' / 'work_tracking' / '__init__.py'
            assert work_tracking_path.exists()

            content = work_tracking_path.read_text(encoding='utf-8')

            # Check that protocol has parent_id
            assert 'parent_id: Optional[int] = None' in content

            # Check that AzureCLIAdapter passes parent_id
            assert 'parent_id=parent_id' in content


@pytest.mark.integration
class TestSkillsReInit:
    """Test that skills are properly updated during re-init."""

    def test_skills_updated_on_reinit(self, tmp_path):
        """Test that skills are refreshed when running init again."""
        runner = CliRunner()

        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            td_path = Path(td)

            # Run init first time
            result1 = runner.invoke(cli, [
                'init',
                '--no-interactive',
                '--config-path', str(td_path / '.claude' / 'config.yaml')
            ])
            assert result1.exit_code == 0

            skills_dir = td_path / '.claude' / 'skills'
            assert skills_dir.exists()

            # Modify a skill file to test it gets overwritten
            test_file = skills_dir / 'work_tracking' / '__init__.py'
            original_content = test_file.read_text(encoding='utf-8')
            test_file.write_text("# MODIFIED", encoding='utf-8')

            # Run init again
            result2 = runner.invoke(cli, [
                'init',
                '--no-interactive',
                '--config-path', str(td_path / '.claude' / 'config.yaml')
            ])
            assert result2.exit_code == 0

            # File should be restored to original content
            restored_content = test_file.read_text(encoding='utf-8')
            assert restored_content != "# MODIFIED"
            assert "UnifiedWorkTrackingAdapter" in restored_content
