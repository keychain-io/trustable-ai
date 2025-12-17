"""
Integration tests for AzureCLI configuration loading (Task #1138).

Tests configuration loading from real .claude/config.yaml files
and environment variables in realistic scenarios.

Key scenarios tested:
1. Loading from actual config.yaml file
2. Loading from environment variables
3. Error handling with real file I/O
4. Integration with work item operations
"""
import pytest
import os
import yaml
from pathlib import Path
from unittest.mock import patch, Mock


@pytest.mark.integration
class TestConfigLoadingFromRealFiles:
    """Test configuration loading from real config.yaml files."""

    def test_load_from_real_config_yaml(self, tmp_path, monkeypatch):
        """Test loading configuration from actual .claude/config.yaml file."""
        # Change to temp directory
        monkeypatch.chdir(tmp_path)

        # Create .claude directory
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()

        # Create config.yaml
        config_content = {
            'project': {
                'name': 'Integration Test Project',
                'type': 'web-application',
                'tech_stack': {
                    'languages': ['Python']
                }
            },
            'work_tracking': {
                'platform': 'azure-devops',
                'organization': 'https://dev.azure.com/integrationtest',
                'project': 'IntegrationProject'
            }
        }

        config_path = claude_dir / "config.yaml"
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(config_content, f)

        # Import and create AzureCLI
        from skills.azure_devops.cli_wrapper import AzureCLI

        cli = AzureCLI()

        # Verify configuration loaded from file
        assert cli._config['organization'] == "https://dev.azure.com/integrationtest"
        assert cli._config['project'] == "IntegrationProject"

    def test_load_from_environment_variables_real(self, tmp_path, monkeypatch):
        """Test loading from environment variables when config.yaml doesn't exist."""
        # Change to temp directory (no .claude/config.yaml)
        monkeypatch.chdir(tmp_path)

        # Set environment variables
        monkeypatch.setenv('AZURE_DEVOPS_ORG', 'https://dev.azure.com/envtest')
        monkeypatch.setenv('AZURE_DEVOPS_PROJECT', 'EnvTestProject')

        # Import and create AzureCLI
        from skills.azure_devops.cli_wrapper import AzureCLI

        cli = AzureCLI()

        # Verify configuration loaded from env vars
        assert cli._config['organization'] == "https://dev.azure.com/envtest"
        assert cli._config['project'] == "EnvTestProject"

    def test_config_yaml_overrides_env_vars_real(self, tmp_path, monkeypatch):
        """Test that config.yaml takes precedence over environment variables."""
        # Change to temp directory
        monkeypatch.chdir(tmp_path)

        # Create .claude directory and config.yaml
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()

        config_content = {
            'project': {
                'name': 'Config Test',
                'type': 'api',
                'tech_stack': {'languages': ['Python']}
            },
            'work_tracking': {
                'platform': 'azure-devops',
                'organization': 'https://dev.azure.com/configtest',
                'project': 'ConfigProject'
            }
        }

        config_path = claude_dir / "config.yaml"
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(config_content, f)

        # Set different environment variables
        monkeypatch.setenv('AZURE_DEVOPS_ORG', 'https://dev.azure.com/envtest')
        monkeypatch.setenv('AZURE_DEVOPS_PROJECT', 'EnvProject')

        # Import and create AzureCLI
        from skills.azure_devops.cli_wrapper import AzureCLI

        cli = AzureCLI()

        # Verify config.yaml values used (not env vars)
        assert cli._config['organization'] == "https://dev.azure.com/configtest"
        assert cli._config['project'] == "ConfigProject"

    def test_invalid_yaml_falls_back_to_env_vars(self, tmp_path, monkeypatch):
        """Test that invalid YAML in config file allows fallback to env vars."""
        # Change to temp directory
        monkeypatch.chdir(tmp_path)

        # Create .claude directory with invalid YAML
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()

        config_path = claude_dir / "config.yaml"
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write("{ invalid yaml content !!")

        # Set environment variables
        monkeypatch.setenv('AZURE_DEVOPS_ORG', 'https://dev.azure.com/envtest')
        monkeypatch.setenv('AZURE_DEVOPS_PROJECT', 'EnvProject')

        # Import and create AzureCLI
        from skills.azure_devops.cli_wrapper import AzureCLI

        cli = AzureCLI()

        # Verify env vars used despite invalid config.yaml
        assert cli._config['organization'] == "https://dev.azure.com/envtest"
        assert cli._config['project'] == "EnvProject"

    def test_partial_config_with_env_var_fallback_real(self, tmp_path, monkeypatch):
        """Test partial config.yaml with environment variable fallback."""
        # Change to temp directory
        monkeypatch.chdir(tmp_path)

        # Create .claude directory
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()

        # Create config.yaml with only organization (no project)
        config_content = {
            'project': {
                'name': 'Partial Config Test',
                'type': 'api',
                'tech_stack': {'languages': ['Python']}
            },
            'work_tracking': {
                'platform': 'azure-devops',
                'organization': 'https://dev.azure.com/configtest',
                'project': None  # Explicitly set to None
            }
        }

        config_path = claude_dir / "config.yaml"
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(config_content, f)

        # Set project in environment variable
        monkeypatch.setenv('AZURE_DEVOPS_PROJECT', 'EnvProject')

        # Import and create AzureCLI
        from skills.azure_devops.cli_wrapper import AzureCLI

        cli = AzureCLI()

        # Verify config.yaml org + env var project
        assert cli._config['organization'] == "https://dev.azure.com/configtest"
        assert cli._config['project'] == "EnvProject"


@pytest.mark.integration
class TestConfigErrorHandlingReal:
    """Test error handling with real file I/O."""

    def test_missing_config_and_env_vars_error(self, tmp_path, monkeypatch):
        """Test clear error when both config and env vars are missing."""
        # Change to temp directory (no config.yaml)
        monkeypatch.chdir(tmp_path)

        # Ensure no environment variables set
        monkeypatch.delenv('AZURE_DEVOPS_ORG', raising=False)
        monkeypatch.delenv('AZURE_DEVOPS_PROJECT', raising=False)

        # Import and try to create AzureCLI
        from skills.azure_devops.cli_wrapper import AzureCLI

        with pytest.raises(Exception) as exc_info:
            AzureCLI()

        # Verify error message is clear and helpful
        error_msg = str(exc_info.value)
        assert "Azure DevOps organization not configured" in error_msg
        assert ".claude/config.yaml" in error_msg
        assert "AZURE_DEVOPS_ORG" in error_msg

    def test_invalid_organization_url_error(self, tmp_path, monkeypatch):
        """Test error message for invalid organization URL."""
        # Change to temp directory
        monkeypatch.chdir(tmp_path)

        # Set invalid URL in environment variable
        monkeypatch.setenv('AZURE_DEVOPS_ORG', 'https://github.com/testorg')
        monkeypatch.setenv('AZURE_DEVOPS_PROJECT', 'TestProject')

        # Import and try to create AzureCLI
        from skills.azure_devops.cli_wrapper import AzureCLI

        with pytest.raises(Exception) as exc_info:
            AzureCLI()

        # Verify error message explains the issue
        error_msg = str(exc_info.value)
        assert "Invalid Azure DevOps organization URL" in error_msg
        assert "Must start with 'https://dev.azure.com/'" in error_msg

    def test_missing_project_error(self, tmp_path, monkeypatch):
        """Test error message when project is missing."""
        # Change to temp directory
        monkeypatch.chdir(tmp_path)

        # Set only organization
        monkeypatch.setenv('AZURE_DEVOPS_ORG', 'https://dev.azure.com/testorg')
        monkeypatch.delenv('AZURE_DEVOPS_PROJECT', raising=False)

        # Import and try to create AzureCLI
        from skills.azure_devops.cli_wrapper import AzureCLI

        with pytest.raises(Exception) as exc_info:
            AzureCLI()

        # Verify error message is clear
        error_msg = str(exc_info.value)
        assert "Azure DevOps project not configured" in error_msg


@pytest.mark.integration
class TestWorkItemOperationsWithConfig:
    """Test that work item operations use configuration correctly."""

    @patch('skills.azure_devops.cli_wrapper.requests')
    def test_work_item_query_uses_config_organization(self, mock_requests, tmp_path, monkeypatch):
        """Test that work item queries use organization from config."""
        # Change to temp directory
        monkeypatch.chdir(tmp_path)

        # Create config.yaml
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()

        config_content = {
            'project': {
                'name': 'Test',
                'type': 'api',
                'tech_stack': {'languages': ['Python']}
            },
            'work_tracking': {
                'platform': 'azure-devops',
                'organization': 'https://dev.azure.com/testorg',
                'project': 'TestProject'
            }
        }

        config_path = claude_dir / "config.yaml"
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(config_content, f)

        # Mock requests response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'workItems': []}
        mock_requests.request.return_value = mock_response

        # Import and create AzureCLI
        from skills.azure_devops.cli_wrapper import AzureCLI

        cli = AzureCLI()

        # Mock _get_auth_token to avoid authentication
        with patch.object(cli, '_get_auth_token', return_value='fake-token'):
            # Query work items
            wiql = "SELECT [System.Id] FROM WorkItems"
            result = cli.query_work_items(wiql)

        # Verify request was made to correct organization URL
        call_args = mock_requests.request.call_args
        url = call_args[1]['url']
        assert 'https://dev.azure.com/testorg' in url
        assert 'TestProject' in url

    def test_get_project_returns_config_project(self, tmp_path, monkeypatch):
        """Test that _get_project() returns project from config."""
        # Change to temp directory
        monkeypatch.chdir(tmp_path)

        # Set environment variables
        monkeypatch.setenv('AZURE_DEVOPS_ORG', 'https://dev.azure.com/testorg')
        monkeypatch.setenv('AZURE_DEVOPS_PROJECT', 'TestProjectFromEnv')

        # Import and create AzureCLI
        from skills.azure_devops.cli_wrapper import AzureCLI

        cli = AzureCLI()

        # Verify _get_project() returns correct value
        project = cli._get_project()
        assert project == "TestProjectFromEnv"

    def test_get_base_url_returns_config_org(self, tmp_path, monkeypatch):
        """Test that _get_base_url() returns organization from config."""
        # Change to temp directory
        monkeypatch.chdir(tmp_path)

        # Set environment variables
        monkeypatch.setenv('AZURE_DEVOPS_ORG', 'https://dev.azure.com/testorg')
        monkeypatch.setenv('AZURE_DEVOPS_PROJECT', 'TestProject')

        # Import and create AzureCLI
        from skills.azure_devops.cli_wrapper import AzureCLI

        cli = AzureCLI()

        # Verify _get_base_url() returns correct value
        base_url = cli._get_base_url()
        assert base_url == "https://dev.azure.com/testorg"


@pytest.mark.integration
class TestNoSubprocessCallsIntegration:
    """Integration tests verifying no subprocess calls are made."""

    @patch('skills.azure_devops.cli_wrapper.subprocess.run')
    def test_no_subprocess_calls_during_initialization(self, mock_subprocess, tmp_path, monkeypatch):
        """Test that no subprocess calls are made during AzureCLI initialization."""
        # Change to temp directory
        monkeypatch.chdir(tmp_path)

        # Set environment variables
        monkeypatch.setenv('AZURE_DEVOPS_ORG', 'https://dev.azure.com/testorg')
        monkeypatch.setenv('AZURE_DEVOPS_PROJECT', 'TestProject')

        # Import and create AzureCLI
        from skills.azure_devops.cli_wrapper import AzureCLI

        cli = AzureCLI()

        # Verify no subprocess calls were made
        mock_subprocess.assert_not_called()

        # Verify configuration loaded correctly
        assert cli._config['organization'] == "https://dev.azure.com/testorg"
        assert cli._config['project'] == "TestProject"

    @patch('skills.azure_devops.cli_wrapper.subprocess.run')
    def test_no_az_devops_configure_calls_anywhere(self, mock_subprocess, tmp_path, monkeypatch):
        """Test that 'az devops configure' is never called anywhere in the code."""
        # Change to temp directory
        monkeypatch.chdir(tmp_path)

        # Create config.yaml
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()

        config_content = {
            'project': {
                'name': 'Test',
                'type': 'api',
                'tech_stack': {'languages': ['Python']}
            },
            'work_tracking': {
                'platform': 'azure-devops',
                'organization': 'https://dev.azure.com/testorg',
                'project': 'TestProject'
            }
        }

        config_path = claude_dir / "config.yaml"
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(config_content, f)

        # Import and create AzureCLI
        from skills.azure_devops.cli_wrapper import AzureCLI

        cli = AzureCLI()

        # Verify no subprocess calls with 'az devops configure'
        for call in mock_subprocess.call_args_list:
            args = call[0][0] if call[0] else []
            assert 'configure' not in args, "Found subprocess call with 'configure' command"
            assert 'az' not in args or 'devops' not in args or 'configure' not in args


@pytest.mark.integration
class TestConfigLoadingEdgeCases:
    """Test edge cases in configuration loading."""

    def test_config_with_extra_whitespace(self, tmp_path, monkeypatch):
        """Test configuration loading handles whitespace correctly."""
        # Change to temp directory
        monkeypatch.chdir(tmp_path)

        # Set environment variables with extra whitespace
        monkeypatch.setenv('AZURE_DEVOPS_ORG', '  https://dev.azure.com/testorg  ')
        monkeypatch.setenv('AZURE_DEVOPS_PROJECT', '  TestProject  ')

        # Import and create AzureCLI
        from skills.azure_devops.cli_wrapper import AzureCLI

        cli = AzureCLI()

        # Verify whitespace was stripped
        assert cli._config['organization'] == "https://dev.azure.com/testorg"
        assert cli._config['project'] == "TestProject"

    def test_config_with_trailing_slash_in_url(self, tmp_path, monkeypatch):
        """Test that trailing slashes are removed from organization URLs."""
        # Change to temp directory
        monkeypatch.chdir(tmp_path)

        # Set environment variables with trailing slash
        monkeypatch.setenv('AZURE_DEVOPS_ORG', 'https://dev.azure.com/testorg/')
        monkeypatch.setenv('AZURE_DEVOPS_PROJECT', 'TestProject')

        # Import and create AzureCLI
        from skills.azure_devops.cli_wrapper import AzureCLI

        cli = AzureCLI()

        # Verify trailing slash removed
        assert cli._config['organization'] == "https://dev.azure.com/testorg"
        assert not cli._config['organization'].endswith('/')
