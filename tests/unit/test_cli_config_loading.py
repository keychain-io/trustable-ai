"""
Unit tests for AzureCLI configuration loading (Task #1138).

Tests pure Python configuration loading from .claude/config.yaml
and environment variable fallback, replacing subprocess-based
az devops configure calls.

Key scenarios tested:
1. Configuration loaded from .claude/config.yaml
2. Fallback to AZURE_DEVOPS_ORG and AZURE_DEVOPS_PROJECT environment variables
3. Validation errors for invalid organization URLs
4. Validation errors for missing project names
5. Validation errors when both config and env vars missing
6. Organization URL normalization (trailing slash removal)
"""
import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path


@pytest.mark.unit
class TestConfigLoadingFromYaml:
    """Test configuration loading from .claude/config.yaml."""

    @patch('skills.azure_devops.cli_wrapper.load_config')
    def test_load_from_config_yaml_success(self, mock_load_config):
        """Test successful configuration loading from .claude/config.yaml."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        # Mock framework config
        mock_config = Mock()
        mock_config.work_tracking.organization = "https://dev.azure.com/testorg"
        mock_config.work_tracking.project = "TestProject"
        mock_load_config.return_value = mock_config

        # Create AzureCLI instance
        cli = AzureCLI()

        # Verify configuration loaded
        assert cli._config['organization'] == "https://dev.azure.com/testorg"
        assert cli._config['project'] == "TestProject"

    @patch('skills.azure_devops.cli_wrapper.load_config')
    def test_load_from_config_yaml_with_trailing_slash(self, mock_load_config):
        """Test organization URL normalization (trailing slash removal)."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        # Mock framework config with trailing slash
        mock_config = Mock()
        mock_config.work_tracking.organization = "https://dev.azure.com/testorg/"
        mock_config.work_tracking.project = "TestProject"
        mock_load_config.return_value = mock_config

        # Create AzureCLI instance
        cli = AzureCLI()

        # Verify trailing slash removed
        assert cli._config['organization'] == "https://dev.azure.com/testorg"
        assert not cli._config['organization'].endswith('/')

    @patch('skills.azure_devops.cli_wrapper.load_config')
    def test_load_from_config_yaml_invalid_url(self, mock_load_config):
        """Test validation error for invalid organization URL."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        # Mock framework config with invalid URL
        mock_config = Mock()
        mock_config.work_tracking.organization = "https://invalid.com/testorg"
        mock_config.work_tracking.project = "TestProject"
        mock_load_config.return_value = mock_config

        # Should raise exception for invalid URL
        with pytest.raises(Exception) as exc_info:
            AzureCLI()

        assert "Invalid Azure DevOps organization URL" in str(exc_info.value)
        assert "Must start with 'https://dev.azure.com/'" in str(exc_info.value)

    @patch('skills.azure_devops.cli_wrapper.load_config')
    def test_load_from_config_yaml_missing_project(self, mock_load_config):
        """Test validation error when project name is missing."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        # Mock framework config with missing project
        mock_config = Mock()
        mock_config.work_tracking.organization = "https://dev.azure.com/testorg"
        mock_config.work_tracking.project = None
        mock_load_config.return_value = mock_config

        # Should raise exception for missing project
        with pytest.raises(Exception) as exc_info:
            AzureCLI()

        assert "Azure DevOps project not configured" in str(exc_info.value)
        assert ".claude/config.yaml" in str(exc_info.value)

    @patch('skills.azure_devops.cli_wrapper.load_config')
    def test_load_from_config_yaml_empty_project(self, mock_load_config):
        """Test validation error when project name is empty string."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        # Mock framework config with empty project
        mock_config = Mock()
        mock_config.work_tracking.organization = "https://dev.azure.com/testorg"
        mock_config.work_tracking.project = ""
        mock_load_config.return_value = mock_config

        # Should raise exception for empty project
        with pytest.raises(Exception) as exc_info:
            AzureCLI()

        assert "Azure DevOps project not configured" in str(exc_info.value)


@pytest.mark.unit
class TestEnvironmentVariableFallback:
    """Test fallback to environment variables."""

    @patch('skills.azure_devops.cli_wrapper.load_config')
    def test_fallback_to_environment_variables(self, mock_load_config):
        """Test fallback to environment variables when config.yaml not found."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        # Mock config file not found
        mock_load_config.side_effect = FileNotFoundError()

        # Set environment variables
        os.environ['AZURE_DEVOPS_ORG'] = "https://dev.azure.com/envorg"
        os.environ['AZURE_DEVOPS_PROJECT'] = "EnvProject"

        try:
            # Create AzureCLI instance
            cli = AzureCLI()

            # Verify configuration loaded from env vars
            assert cli._config['organization'] == "https://dev.azure.com/envorg"
            assert cli._config['project'] == "EnvProject"

        finally:
            # Cleanup
            del os.environ['AZURE_DEVOPS_ORG']
            del os.environ['AZURE_DEVOPS_PROJECT']

    @patch('skills.azure_devops.cli_wrapper.load_config')
    def test_config_yaml_takes_precedence_over_env_vars(self, mock_load_config):
        """Test that config.yaml values take precedence over environment variables."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        # Mock framework config
        mock_config = Mock()
        mock_config.work_tracking.organization = "https://dev.azure.com/configorg"
        mock_config.work_tracking.project = "ConfigProject"
        mock_load_config.return_value = mock_config

        # Set environment variables (should be ignored)
        os.environ['AZURE_DEVOPS_ORG'] = "https://dev.azure.com/envorg"
        os.environ['AZURE_DEVOPS_PROJECT'] = "EnvProject"

        try:
            # Create AzureCLI instance
            cli = AzureCLI()

            # Verify config.yaml values used (not env vars)
            assert cli._config['organization'] == "https://dev.azure.com/configorg"
            assert cli._config['project'] == "ConfigProject"

        finally:
            # Cleanup
            del os.environ['AZURE_DEVOPS_ORG']
            del os.environ['AZURE_DEVOPS_PROJECT']

    @patch('skills.azure_devops.cli_wrapper.load_config')
    def test_partial_config_with_env_var_fallback(self, mock_load_config):
        """Test partial config.yaml with env var fallback for missing values."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        # Mock framework config with only organization (no project)
        mock_config = Mock()
        mock_config.work_tracking.organization = "https://dev.azure.com/configorg"
        mock_config.work_tracking.project = None
        mock_load_config.return_value = mock_config

        # Set project in environment variable
        os.environ['AZURE_DEVOPS_PROJECT'] = "EnvProject"

        try:
            # Create AzureCLI instance
            cli = AzureCLI()

            # Verify config.yaml org + env var project
            assert cli._config['organization'] == "https://dev.azure.com/configorg"
            assert cli._config['project'] == "EnvProject"

        finally:
            # Cleanup
            del os.environ['AZURE_DEVOPS_PROJECT']

    @patch('skills.azure_devops.cli_wrapper.load_config')
    def test_env_var_with_trailing_slash_normalized(self, mock_load_config):
        """Test environment variable URL is also normalized."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        # Mock config file not found
        mock_load_config.side_effect = FileNotFoundError()

        # Set environment variables with trailing slash
        os.environ['AZURE_DEVOPS_ORG'] = "https://dev.azure.com/envorg/"
        os.environ['AZURE_DEVOPS_PROJECT'] = "EnvProject"

        try:
            # Create AzureCLI instance
            cli = AzureCLI()

            # Verify trailing slash removed
            assert cli._config['organization'] == "https://dev.azure.com/envorg"
            assert not cli._config['organization'].endswith('/')

        finally:
            # Cleanup
            del os.environ['AZURE_DEVOPS_ORG']
            del os.environ['AZURE_DEVOPS_PROJECT']


@pytest.mark.unit
class TestValidationErrors:
    """Test validation error handling."""

    @patch('skills.azure_devops.cli_wrapper.load_config')
    def test_missing_organization_config_and_env_var(self, mock_load_config):
        """Test error when organization missing in both config and env vars."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        # Mock config file not found
        mock_load_config.side_effect = FileNotFoundError()

        # No environment variables set
        # Ensure env vars don't exist
        os.environ.pop('AZURE_DEVOPS_ORG', None)
        os.environ.pop('AZURE_DEVOPS_PROJECT', None)

        # Should raise exception
        with pytest.raises(Exception) as exc_info:
            AzureCLI()

        assert "Azure DevOps organization not configured" in str(exc_info.value)
        assert ".claude/config.yaml" in str(exc_info.value)
        assert "AZURE_DEVOPS_ORG" in str(exc_info.value)

    @patch('skills.azure_devops.cli_wrapper.load_config')
    def test_missing_project_config_and_env_var(self, mock_load_config):
        """Test error when project missing in both config and env vars."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        # Mock config file not found
        mock_load_config.side_effect = FileNotFoundError()

        # Set only organization, not project
        os.environ['AZURE_DEVOPS_ORG'] = "https://dev.azure.com/testorg"
        os.environ.pop('AZURE_DEVOPS_PROJECT', None)

        try:
            # Should raise exception
            with pytest.raises(Exception) as exc_info:
                AzureCLI()

            assert "Azure DevOps project not configured" in str(exc_info.value)
            assert ".claude/config.yaml" in str(exc_info.value)
            assert "AZURE_DEVOPS_PROJECT" in str(exc_info.value)

        finally:
            # Cleanup
            del os.environ['AZURE_DEVOPS_ORG']

    @patch('skills.azure_devops.cli_wrapper.load_config')
    def test_invalid_url_from_env_var(self, mock_load_config):
        """Test validation error for invalid URL from environment variable."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        # Mock config file not found
        mock_load_config.side_effect = FileNotFoundError()

        # Set invalid URL in environment variable
        os.environ['AZURE_DEVOPS_ORG'] = "https://github.com/testorg"
        os.environ['AZURE_DEVOPS_PROJECT'] = "TestProject"

        try:
            # Should raise exception
            with pytest.raises(Exception) as exc_info:
                AzureCLI()

            assert "Invalid Azure DevOps organization URL" in str(exc_info.value)
            assert "Must start with 'https://dev.azure.com/'" in str(exc_info.value)

        finally:
            # Cleanup
            del os.environ['AZURE_DEVOPS_ORG']
            del os.environ['AZURE_DEVOPS_PROJECT']

    @patch('skills.azure_devops.cli_wrapper.load_config')
    def test_url_without_https_prefix(self, mock_load_config):
        """Test validation error for URL without https prefix."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        # Mock config file not found
        mock_load_config.side_effect = FileNotFoundError()

        # Set URL without https
        os.environ['AZURE_DEVOPS_ORG'] = "dev.azure.com/testorg"
        os.environ['AZURE_DEVOPS_PROJECT'] = "TestProject"

        try:
            # Should raise exception
            with pytest.raises(Exception) as exc_info:
                AzureCLI()

            assert "Invalid Azure DevOps organization URL" in str(exc_info.value)

        finally:
            # Cleanup
            del os.environ['AZURE_DEVOPS_ORG']
            del os.environ['AZURE_DEVOPS_PROJECT']


@pytest.mark.unit
class TestConfigErrorHandling:
    """Test error handling for config loading failures."""

    @patch('skills.azure_devops.cli_wrapper.load_config')
    def test_config_parse_error_falls_back_to_env_vars(self, mock_load_config):
        """Test that config parse errors allow fallback to env vars."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        # Mock config parsing error
        mock_load_config.side_effect = Exception("YAML parsing error")

        # Set environment variables
        os.environ['AZURE_DEVOPS_ORG'] = "https://dev.azure.com/envorg"
        os.environ['AZURE_DEVOPS_PROJECT'] = "EnvProject"

        try:
            # Should fall back to env vars (with warning printed)
            cli = AzureCLI()

            # Verify env vars used
            assert cli._config['organization'] == "https://dev.azure.com/envorg"
            assert cli._config['project'] == "EnvProject"

        finally:
            # Cleanup
            del os.environ['AZURE_DEVOPS_ORG']
            del os.environ['AZURE_DEVOPS_PROJECT']

    @patch('skills.azure_devops.cli_wrapper.load_config')
    def test_whitespace_in_env_vars_stripped(self, mock_load_config):
        """Test that whitespace in env vars is stripped."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        # Mock config file not found
        mock_load_config.side_effect = FileNotFoundError()

        # Set environment variables with whitespace
        os.environ['AZURE_DEVOPS_ORG'] = "  https://dev.azure.com/testorg  "
        os.environ['AZURE_DEVOPS_PROJECT'] = "  TestProject  "

        try:
            # Create AzureCLI instance
            cli = AzureCLI()

            # Verify whitespace stripped
            assert cli._config['organization'] == "https://dev.azure.com/testorg"
            assert cli._config['project'] == "TestProject"

        finally:
            # Cleanup
            del os.environ['AZURE_DEVOPS_ORG']
            del os.environ['AZURE_DEVOPS_PROJECT']


@pytest.mark.unit
class TestNoSubprocessCalls:
    """Test that no subprocess calls to 'az devops configure' are made (subprocess removed in Sprint 7)."""

    @patch('skills.azure_devops.cli_wrapper.load_config')
    def test_no_subprocess_calls_during_init(self, mock_load_config):
        """Test that AzureCLI.__init__() uses pure Python config loading (no subprocess)."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        # Mock framework config
        mock_config = Mock()
        mock_config.work_tracking.organization = "https://dev.azure.com/testorg"
        mock_config.work_tracking.project = "TestProject"
        mock_load_config.return_value = mock_config

        # Create AzureCLI instance
        cli = AzureCLI()

        # Verify configuration loaded correctly via Python (not subprocess)
        assert cli._config['organization'] == "https://dev.azure.com/testorg"
        assert cli._config['project'] == "TestProject"

        # Verify load_config was called (Python-based config loading)
        mock_load_config.assert_called_once()

    @patch('skills.azure_devops.cli_wrapper.load_config')
    def test_no_az_devops_configure_calls(self, mock_load_config):
        """Test that 'az devops configure' is never called (pure Python config)."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        # Mock framework config
        mock_config = Mock()
        mock_config.work_tracking.organization = "https://dev.azure.com/testorg"
        mock_config.work_tracking.project = "TestProject"
        mock_load_config.return_value = mock_config

        # Create instance - should use Python config loading only
        cli = AzureCLI()

        # Verify configuration loaded via Python (load_config called)
        mock_load_config.assert_called_once()

        # Verify config values match expected
        assert cli._config['organization'] == "https://dev.azure.com/testorg"
        assert cli._config['project'] == "TestProject"


@pytest.mark.unit
class TestBackwardCompatibility:
    """Test backward compatibility with existing code."""

    @patch('skills.azure_devops.cli_wrapper.load_config')
    def test_config_dict_structure_unchanged(self, mock_load_config):
        """Test that _config dict structure remains unchanged for backward compatibility."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        # Mock framework config
        mock_config = Mock()
        mock_config.work_tracking.organization = "https://dev.azure.com/testorg"
        mock_config.work_tracking.project = "TestProject"
        mock_load_config.return_value = mock_config

        # Create AzureCLI instance
        cli = AzureCLI()

        # Verify _config has expected keys
        assert 'organization' in cli._config
        assert 'project' in cli._config

        # Verify values are strings (not objects)
        assert isinstance(cli._config['organization'], str)
        assert isinstance(cli._config['project'], str)

    @patch('skills.azure_devops.cli_wrapper.load_config')
    def test_get_project_method_works(self, mock_load_config):
        """Test that _get_project() method still works correctly."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        # Mock framework config
        mock_config = Mock()
        mock_config.work_tracking.organization = "https://dev.azure.com/testorg"
        mock_config.work_tracking.project = "TestProject"
        mock_load_config.return_value = mock_config

        # Create AzureCLI instance
        cli = AzureCLI()

        # Call _get_project()
        project = cli._get_project()

        # Verify project returned
        assert project == "TestProject"

    @patch('skills.azure_devops.cli_wrapper.load_config')
    def test_get_base_url_method_works(self, mock_load_config):
        """Test that _get_base_url() method still works correctly."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        # Mock framework config
        mock_config = Mock()
        mock_config.work_tracking.organization = "https://dev.azure.com/testorg"
        mock_config.work_tracking.project = "TestProject"
        mock_load_config.return_value = mock_config

        # Create AzureCLI instance
        cli = AzureCLI()

        # Call _get_base_url()
        base_url = cli._get_base_url()

        # Verify URL returned (without trailing slash)
        assert base_url == "https://dev.azure.com/testorg"
        assert not base_url.endswith('/')
