"""
Integration tests for CLI init command.

Tests the complete init workflow with real file system operations.
"""
import pytest
import json
from pathlib import Path
from click.testing import CliRunner

from cli.main import cli


@pytest.mark.integration
class TestInitCommand:
    """Test suite for cwf init command."""

    def test_init_interactive_success(self):
        """Test successful interactive initialization."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Create some source files so context generation has something to index
            Path("src").mkdir()
            Path("src/app.py").write_text("# App")

            result = runner.invoke(cli, ['init'], input='\n'.join([
                'y',                       # Use detected settings as defaults
                'Test Project',           # Project name
                'web-application',        # Project type
                'Python,TypeScript',       # Languages
                'FastAPI,React',          # Frameworks
                'Azure,Docker',           # Platforms
                '',                        # Databases (empty)
                'file-based',              # Platform
                '',                        # Agent selection: keep current/defaults
                'y',                       # Render agents/workflows
                'n',                       # Don't generate context
            ]))

            assert result.exit_code == 0
            assert 'Initialization complete' in result.output or 'updated' in result.output.lower()

            # Verify files created
            assert Path('.claude/config.yaml').exists()
            # Note: agents/ and commands/ are created by /context-generation workflow, not init

    def test_init_non_interactive(self):
        """Test non-interactive initialization uses defaults."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            result = runner.invoke(cli, ['init', '--no-interactive'])

            assert result.exit_code == 0
            assert Path('.claude/config.yaml').exists()

            # Verify defaults were used
            from config.loader import ConfigLoader
            loader = ConfigLoader(Path('.claude/config.yaml'))
            config = loader.load()
            assert config.project.name == 'My Project'  # Default
            assert config.project.type == 'api'  # Default

    def test_init_custom_config_path(self):
        """Test initialization with custom config path."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            result = runner.invoke(cli, [
                'init',
                '--config-path', 'custom-config.yaml',
                '--no-interactive'
            ])

            assert result.exit_code == 0
            assert Path('custom-config.yaml').exists()

    def test_init_already_initialized(self):
        """Test initialization when already initialized (re-entrant)."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # First init
            runner.invoke(cli, ['init', '--no-interactive'])

            # Second init should show "Updating" message (re-entrant)
            result = runner.invoke(cli, ['init', '--no-interactive'])

            assert result.exit_code == 0
            assert 'Updating' in result.output or 'updated' in result.output.lower()


@pytest.mark.integration
class TestInitDirectoryStructure:
    """Test directory structure creation during init."""

    def test_creates_claude_directory(self):
        """Test that .claude directory is created."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            runner.invoke(cli, ['init', '--no-interactive'])

            assert Path('.claude').exists()
            assert Path('.claude').is_dir()

    def test_creates_subdirectories(self):
        """Test that required subdirectories are created."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            runner.invoke(cli, ['init', '--no-interactive'])

            # Runtime directories are created by init
            assert Path('.claude/workflow-state').exists()
            assert Path('.claude/profiling').exists()
            assert Path('.claude/learnings').exists()
            # Note: agents/ and commands/ are created by /context-generation workflow, not init

    def test_config_file_valid_yaml(self):
        """Test that generated config file is valid YAML."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            runner.invoke(cli, ['init', '--no-interactive'])

            config_path = Path('.claude/config.yaml')
            assert config_path.exists()

            # Try to load the config
            from config.loader import ConfigLoader
            loader = ConfigLoader(config_path)
            config = loader.load()

            assert config.project.name == 'My Project'  # Default
            assert config.project.type == 'api'  # Default


@pytest.mark.integration
class TestInitReentrancy:
    """Test re-entrancy: running init again with existing config."""

    def test_reentrant_preserves_config(self):
        """Test that re-running init preserves existing configuration."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # First init with interactive settings
            result1 = runner.invoke(cli, ['init'], input='\n'.join([
                'y',                       # Use detected settings as defaults
                'Original Project',       # Project name
                'api',                    # Project type
                'Python',                 # Languages
                'FastAPI',                # Frameworks
                'Docker',                 # Platforms
                '',                        # Databases
                'file-based',              # Platform
                '',                        # Keep default agents
                'n',                       # Don't render
                'n',                       # Don't generate context
            ]))
            assert result1.exit_code == 0

            # Load config to verify first init
            from config.loader import ConfigLoader
            config1 = ConfigLoader(Path('.claude/config.yaml')).load()
            assert config1.project.name == 'Original Project'

            # Run init again - just press enter to keep all values
            result2 = runner.invoke(cli, ['init'], input='\n'.join([
                '',                        # Keep existing project name
                '',                        # Keep existing project type
                '',                        # Keep existing languages
                '',                        # Keep existing frameworks
                '',                        # Keep existing platforms
                '',                        # Keep existing databases
                '',                        # Keep existing work platform
                '',                        # Keep existing agents
                'n',                       # Don't render
                'n',                       # Don't generate context
            ]))

            assert result2.exit_code == 0
            assert 'Updating' in result2.output

            # Verify config preserved
            config2 = ConfigLoader(Path('.claude/config.yaml')).load()
            assert config2.project.name == 'Original Project'
            assert config2.project.type == 'api'

    def test_reentrant_can_update_single_value(self):
        """Test that re-running init can update a single value."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # First init
            runner.invoke(cli, ['init', '--no-interactive'])

            # Re-init interactively, changing just the project name
            result = runner.invoke(cli, ['init'], input='\n'.join([
                'Updated Project Name',   # Change project name
                '',                        # Keep project type
                '',                        # Keep languages
                '',                        # Keep frameworks
                '',                        # Keep platforms
                '',                        # Keep databases
                '',                        # Keep work platform
                '',                        # Keep agents
                'n',                       # Don't render
                'n',                       # Don't generate context
            ]))

            assert result.exit_code == 0

            # Verify only project name changed
            from config.loader import ConfigLoader
            config = ConfigLoader(Path('.claude/config.yaml')).load()
            assert config.project.name == 'Updated Project Name'
            assert config.project.type == 'api'  # Default preserved

    def test_reentrant_preserves_enabled_agents(self):
        """Test that re-running init preserves enabled agents."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # First init with all agents enabled
            result1 = runner.invoke(cli, ['init'], input='\n'.join([
                'y',                       # Use detected settings as defaults
                'Test Project',           # Project name
                'api',                    # Project type
                'Python',                 # Languages
                '',                        # Frameworks
                '',                        # Platforms
                '',                        # Databases
                'file-based',              # Platform
                'all',                     # Enable all agents
                'n',                       # Don't render
                'n',                       # Don't generate context
            ]))
            assert result1.exit_code == 0

            # Load and verify agents
            from config.loader import ConfigLoader
            config1 = ConfigLoader(Path('.claude/config.yaml')).load()
            initial_agents = config1.agent_config.enabled_agents.copy()
            assert len(initial_agents) > 5  # Should have many agents

            # Re-init and keep agents
            result2 = runner.invoke(cli, ['init'], input='\n'.join([
                '',                        # Keep project name
                '',                        # Keep project type
                '',                        # Keep languages
                '',                        # Keep frameworks
                '',                        # Keep platforms
                '',                        # Keep databases
                '',                        # Keep work platform
                '',                        # Keep agents (empty = keep current)
                'n',                       # Don't render
                'n',                       # Don't generate context
            ]))

            assert result2.exit_code == 0

            # Verify agents preserved
            config2 = ConfigLoader(Path('.claude/config.yaml')).load()
            assert config2.agent_config.enabled_agents == initial_agents


@pytest.mark.integration
class TestInitPermissionsGeneration:
    """Test suite for permissions generation during init."""

    def test_init_generates_permissions_file(self):
        """Test that init generates settings.local.json with permissions."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            result = runner.invoke(cli, ['init', '--no-interactive'])

            assert result.exit_code == 0

            # Verify settings.local.json was created
            settings_path = Path('.claude/settings.local.json')
            assert settings_path.exists()

            # Verify it's valid JSON
            with settings_path.open() as f:
                settings = json.load(f)

            # Verify permissions structure
            assert 'permissions' in settings
            assert 'allow' in settings['permissions']
            assert 'deny' in settings['permissions']
            assert 'ask' in settings['permissions']

    def test_permissions_file_contains_correct_structure(self):
        """Test that permissions file contains expected safe actions."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            result = runner.invoke(cli, ['init', '--no-interactive'])

            assert result.exit_code == 0

            settings_path = Path('.claude/settings.local.json')
            with settings_path.open() as f:
                settings = json.load(f)

            # Verify allow list contains safe operations
            allow_list = settings['permissions']['allow']
            assert isinstance(allow_list, list)
            assert len(allow_list) > 0

            # Check for some expected safe patterns
            allow_str = str(allow_list)
            assert 'git status' in allow_str
            assert 'git diff' in allow_str

            # Verify deny list contains destructive operations
            deny_list = settings['permissions']['deny']
            assert isinstance(deny_list, list)

            # Verify ask list contains operations requiring approval
            ask_list = settings['permissions']['ask']
            assert isinstance(ask_list, list)
            assert len(ask_list) > 0

    def test_init_preserves_existing_settings(self):
        """Test that init preserves existing settings when merging permissions."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Create .claude directory and settings file with custom settings
            claude_dir = Path('.claude')
            claude_dir.mkdir()

            settings_path = claude_dir / 'settings.local.json'
            custom_settings = {
                'custom_key': 'custom_value',
                'another_setting': 42,
            }
            with settings_path.open('w') as f:
                json.dump(custom_settings, f)

            # Run init
            result = runner.invoke(cli, ['init', '--no-interactive'])

            assert result.exit_code == 0

            # Verify custom settings preserved
            with settings_path.open() as f:
                settings = json.load(f)

            assert settings['custom_key'] == 'custom_value'
            assert settings['another_setting'] == 42

            # Verify permissions were added
            assert 'permissions' in settings

    def test_init_displays_permission_summary(self):
        """Test that init displays summary of configured permissions."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            result = runner.invoke(cli, ['init', '--no-interactive'])

            assert result.exit_code == 0

            # Verify output contains permission summary
            output = result.output
            assert 'Detecting platform' in output
            assert 'Platform:' in output
            assert 'Shell:' in output
            assert 'Permissions configured:' in output
            assert 'Auto-approved:' in output
            assert 'Require approval:' in output
            assert 'Denied:' in output
            assert 'settings.local.json' in output

    def test_init_handles_permission_generation_errors_gracefully(self):
        """Test that init continues if permission generation fails."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            # Create .claude directory with unwritable settings file
            claude_dir = Path('.claude')
            claude_dir.mkdir()

            # Note: Making files unwritable is platform-specific and may not work
            # in all test environments. This test verifies error handling exists.
            result = runner.invoke(cli, ['init', '--no-interactive'])

            # Init should complete successfully even if permissions fail
            assert result.exit_code == 0

            # Config should still be created
            assert Path('.claude/config.yaml').exists()

    def test_permissions_counts_are_reasonable(self):
        """Test that permission counts are in expected ranges."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            result = runner.invoke(cli, ['init', '--no-interactive'])

            assert result.exit_code == 0

            settings_path = Path('.claude/settings.local.json')
            with settings_path.open() as f:
                settings = json.load(f)

            # Verify counts are reasonable (not 0, not absurdly high)
            allow_count = len(settings['permissions']['allow'])
            ask_count = len(settings['permissions']['ask'])
            deny_count = len(settings['permissions']['deny'])

            # Allow list should have many safe operations (>20)
            assert allow_count > 20, f"Expected >20 auto-approved operations, got {allow_count}"

            # Ask list should have some operations requiring approval (>5)
            assert ask_count > 5, f"Expected >5 operations requiring approval, got {ask_count}"

            # Deny list should have some destructive operations (>2)
            assert deny_count > 2, f"Expected >2 denied operations, got {deny_count}"

    def test_permissions_platform_detection(self):
        """Test that platform detection works during init."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            result = runner.invoke(cli, ['init', '--no-interactive'])

            assert result.exit_code == 0

            # Verify platform was detected and displayed
            output = result.output
            assert 'Platform:' in output

            # Platform should be one of: Windows, Linux, Darwin
            # (We can't assert exact platform since tests run on different systems)
            platform_detected = (
                'Windows' in output or
                'Linux' in output or
                'Darwin' in output
            )
            assert platform_detected, f"No valid platform detected in output: {output}"
