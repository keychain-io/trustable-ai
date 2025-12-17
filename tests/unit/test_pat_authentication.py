"""
Unit tests for PAT token authentication in Azure DevOps CLI wrapper.

Tests cover:
1. Token loading from environment variables
2. Token loading from config.yaml
3. Token validation
4. Token caching
5. Error handling and edge cases
"""
import pytest
import os
from unittest.mock import Mock, patch, mock_open
from pathlib import Path


@pytest.mark.unit
class TestPATTokenLoading:
    """Test PAT token loading from various sources."""

    def test_load_pat_from_env_success(self):
        """Test successful PAT loading from AZURE_DEVOPS_EXT_PAT environment variable."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        # Set environment variable
        test_token = "abcd1234efgh5678ijkl9012mnop3456qrst7890uvwx1234yzab"
        with patch.dict(os.environ, {
            'AZURE_DEVOPS_EXT_PAT': test_token,
            'AZURE_DEVOPS_ORG': 'https://dev.azure.com/test',
            'AZURE_DEVOPS_PROJECT': 'Test'
        }):
            cli = AzureCLI()
            token = cli._load_pat_from_env()

            assert token == test_token

    def test_load_pat_from_env_not_set(self):
        """Test PAT loading returns None when AZURE_DEVOPS_EXT_PAT not set."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        # Ensure environment variable is not set
        with patch.dict(os.environ, {
            'AZURE_DEVOPS_ORG': 'https://dev.azure.com/test',
            'AZURE_DEVOPS_PROJECT': 'Test'
        }, clear=True):
            cli = AzureCLI()
            token = cli._load_pat_from_env()

            assert token is None

    def test_load_pat_from_env_empty_string(self):
        """Test PAT loading returns None when AZURE_DEVOPS_EXT_PAT is empty."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        # Set to empty string
        with patch.dict(os.environ, {
            'AZURE_DEVOPS_EXT_PAT': '   ',
            'AZURE_DEVOPS_ORG': 'https://dev.azure.com/test',
            'AZURE_DEVOPS_PROJECT': 'Test'
        }):
            cli = AzureCLI()
            token = cli._load_pat_from_env()

            assert token is None

    @patch('builtins.open', new_callable=mock_open, read_data="""
work_tracking:
  credentials_source: env:CUSTOM_PAT_VAR
  organization: https://dev.azure.com/test
  project: Test
""")
    @patch('pathlib.Path.exists')
    def test_load_pat_from_config_env_format(self, mock_exists, mock_file):
        """Test PAT loading from config.yaml using env:VARIABLE_NAME format."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        mock_exists.return_value = True

        test_token = "custom1234token5678abcd9012efgh3456ijkl7890mnop"
        with patch.dict(os.environ, {
            'CUSTOM_PAT_VAR': test_token,
            'AZURE_DEVOPS_ORG': 'https://dev.azure.com/test',
            'AZURE_DEVOPS_PROJECT': 'Test'
        }):
            cli = AzureCLI()
            token = cli._load_pat_from_config()

            assert token == test_token

    @patch('builtins.open', new_callable=mock_open, read_data="""
work_tracking:
  credentials_source: direct1234token5678abcd9012efgh3456ijkl7890mnop12
  organization: https://dev.azure.com/test
  project: Test
""")
    @patch('pathlib.Path.exists')
    def test_load_pat_from_config_direct_token(self, mock_exists, mock_file):
        """Test PAT loading from config.yaml using direct token (discouraged)."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        mock_exists.return_value = True

        with patch.dict(os.environ, {
            'AZURE_DEVOPS_ORG': 'https://dev.azure.com/test',
            'AZURE_DEVOPS_PROJECT': 'Test'
        }):
            cli = AzureCLI()
            token = cli._load_pat_from_config()

            # Should return the direct token
            assert token == "direct1234token5678abcd9012efgh3456ijkl7890mnop12"

    @patch('builtins.open', new_callable=mock_open, read_data="""
work_tracking:
  credentials_source: cli
  organization: https://dev.azure.com/test
  project: Test
""")
    @patch('pathlib.Path.exists')
    def test_load_pat_from_config_cli_source(self, mock_exists, mock_file):
        """Test PAT loading returns None when credentials_source is 'cli'."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        mock_exists.return_value = True

        with patch.dict(os.environ, {
            'AZURE_DEVOPS_ORG': 'https://dev.azure.com/test',
            'AZURE_DEVOPS_PROJECT': 'Test'
        }):
            cli = AzureCLI()
            token = cli._load_pat_from_config()

            assert token is None

    @patch('pathlib.Path.exists')
    def test_load_pat_from_config_missing_file(self, mock_exists):
        """Test PAT loading returns None when config.yaml doesn't exist."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        mock_exists.return_value = False

        with patch.dict(os.environ, {
            'AZURE_DEVOPS_ORG': 'https://dev.azure.com/test',
            'AZURE_DEVOPS_PROJECT': 'Test'
        }):
            cli = AzureCLI()
            token = cli._load_pat_from_config()

            assert token is None


@pytest.mark.unit
class TestPATTokenValidation:
    """Test PAT token validation logic."""

    def test_validate_pat_token_valid_52_chars(self):
        """Test validation accepts valid 52-character PAT token."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        with patch.dict(os.environ, {
            'AZURE_DEVOPS_ORG': 'https://dev.azure.com/test',
            'AZURE_DEVOPS_PROJECT': 'Test'
        }):
            cli = AzureCLI()
            token = "abcd1234efgh5678ijkl9012mnop3456qrst7890uvwx1234yzab"

            assert cli._validate_pat_token(token) is True

    def test_validate_pat_token_valid_with_base64_chars(self):
        """Test validation accepts token with valid base64 characters."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        with patch.dict(os.environ, {
            'AZURE_DEVOPS_ORG': 'https://dev.azure.com/test',
            'AZURE_DEVOPS_PROJECT': 'Test'
        }):
            cli = AzureCLI()
            token = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=="

            assert cli._validate_pat_token(token) is True

    def test_validate_pat_token_too_short(self):
        """Test validation rejects token shorter than 20 characters."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        with patch.dict(os.environ, {
            'AZURE_DEVOPS_ORG': 'https://dev.azure.com/test',
            'AZURE_DEVOPS_PROJECT': 'Test'
        }):
            cli = AzureCLI()
            token = "tooshort"

            assert cli._validate_pat_token(token) is False

    def test_validate_pat_token_empty_string(self):
        """Test validation rejects empty string."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        with patch.dict(os.environ, {
            'AZURE_DEVOPS_ORG': 'https://dev.azure.com/test',
            'AZURE_DEVOPS_PROJECT': 'Test'
        }):
            cli = AzureCLI()

            assert cli._validate_pat_token("") is False

    def test_validate_pat_token_none(self):
        """Test validation rejects None."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        with patch.dict(os.environ, {
            'AZURE_DEVOPS_ORG': 'https://dev.azure.com/test',
            'AZURE_DEVOPS_PROJECT': 'Test'
        }):
            cli = AzureCLI()

            assert cli._validate_pat_token(None) is False

    def test_validate_pat_token_invalid_characters(self):
        """Test validation rejects token with invalid characters."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        with patch.dict(os.environ, {
            'AZURE_DEVOPS_ORG': 'https://dev.azure.com/test',
            'AZURE_DEVOPS_PROJECT': 'Test'
        }):
            cli = AzureCLI()
            token = "invalid@token#with$special%chars&"

            assert cli._validate_pat_token(token) is False


@pytest.mark.unit
class TestTokenCaching:
    """Test token caching behavior."""

    def test_cached_token_reused(self):
        """Test that cached token is reused instead of reloading."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        test_token = "abcd1234efgh5678ijkl9012mnop3456qrst7890uvwx1234yzab"

        with patch.dict(os.environ, {
            'AZURE_DEVOPS_EXT_PAT': test_token,
            'AZURE_DEVOPS_ORG': 'https://dev.azure.com/test',
            'AZURE_DEVOPS_PROJECT': 'Test'
        }):
            cli = AzureCLI()

            # First call - should load from env
            token1 = cli._get_cached_or_load_token()

            # Verify token is cached
            assert cli._cached_token == test_token

            # Clear environment variable
            with patch.dict(os.environ, {
                'AZURE_DEVOPS_ORG': 'https://dev.azure.com/test',
                'AZURE_DEVOPS_PROJECT': 'Test'
            }, clear=True):
                # Second call - should use cache even though env var is gone
                token2 = cli._get_cached_or_load_token()

                assert token1 == token2
                assert token2 == test_token

    def test_cached_token_validated_on_reuse(self):
        """Test that cached token is validated before reuse."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        test_token = "abcd1234efgh5678ijkl9012mnop3456qrst7890uvwx1234yzab"
        invalid_token = "short"

        with patch.dict(os.environ, {
            'AZURE_DEVOPS_EXT_PAT': test_token,
            'AZURE_DEVOPS_ORG': 'https://dev.azure.com/test',
            'AZURE_DEVOPS_PROJECT': 'Test'
        }):
            cli = AzureCLI()

            # First call - should cache valid token
            token1 = cli._get_cached_or_load_token()
            assert token1 == test_token

            # Manually corrupt cached token
            cli._cached_token = invalid_token

            # Next call should reject invalid cache and reload
            token2 = cli._get_cached_or_load_token()
            assert token2 == test_token  # Should reload from env


@pytest.mark.unit
class TestAuthenticationError:
    """Test AuthenticationError exception handling."""

    def test_authentication_error_raised_no_token(self):
        """Test AuthenticationError raised when no token found."""
        from skills.azure_devops.cli_wrapper import AzureCLI, AuthenticationError

        # Ensure no token available
        with patch.dict(os.environ, {
            'AZURE_DEVOPS_ORG': 'https://dev.azure.com/test',
            'AZURE_DEVOPS_PROJECT': 'Test'
        }, clear=True):
            with patch('pathlib.Path.exists', return_value=False):
                cli = AzureCLI()

                with pytest.raises(AuthenticationError) as excinfo:
                    cli._get_cached_or_load_token()

                assert "PAT token not found" in str(excinfo.value)
                assert "AZURE_DEVOPS_EXT_PAT" in str(excinfo.value)
                assert "_usersSettings/tokens" in str(excinfo.value)

    def test_authentication_error_includes_org_url(self):
        """Test AuthenticationError includes organization URL in message."""
        from skills.azure_devops.cli_wrapper import AzureCLI, AuthenticationError

        # Ensure no token available
        with patch.dict(os.environ, {
            'AZURE_DEVOPS_ORG': 'https://dev.azure.com/mycompany',
            'AZURE_DEVOPS_PROJECT': 'Test'
        }, clear=True):
            with patch('pathlib.Path.exists', return_value=False):
                cli = AzureCLI()

                with pytest.raises(AuthenticationError) as excinfo:
                    cli._get_cached_or_load_token()

                assert "https://dev.azure.com/mycompany/_usersSettings/tokens" in str(excinfo.value)


@pytest.mark.unit
class TestGetAuthToken:
    """Test _get_auth_token method."""

    def test_get_auth_token_returns_pat(self):
        """Test _get_auth_token returns PAT token."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        test_token = "abcd1234efgh5678ijkl9012mnop3456qrst7890uvwx1234yzab"

        with patch.dict(os.environ, {
            'AZURE_DEVOPS_EXT_PAT': test_token,
            'AZURE_DEVOPS_ORG': 'https://dev.azure.com/test',
            'AZURE_DEVOPS_PROJECT': 'Test'
        }):
            cli = AzureCLI()
            token = cli._get_auth_token()

            assert token == test_token

    def test_get_auth_token_uses_caching(self):
        """Test _get_auth_token uses cached token."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        test_token = "abcd1234efgh5678ijkl9012mnop3456qrst7890uvwx1234yzab"

        with patch.dict(os.environ, {
            'AZURE_DEVOPS_EXT_PAT': test_token,
            'AZURE_DEVOPS_ORG': 'https://dev.azure.com/test',
            'AZURE_DEVOPS_PROJECT': 'Test'
        }):
            cli = AzureCLI()

            # First call
            token1 = cli._get_auth_token()

            # Clear environment
            with patch.dict(os.environ, {
                'AZURE_DEVOPS_ORG': 'https://dev.azure.com/test',
                'AZURE_DEVOPS_PROJECT': 'Test'
            }, clear=True):
                # Should use cache
                token2 = cli._get_auth_token()

                assert token1 == token2


@pytest.mark.unit
class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_token_with_whitespace_stripped(self):
        """Test token with leading/trailing whitespace is stripped."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        test_token = "abcd1234efgh5678ijkl9012mnop3456qrst7890uvwx1234yzab"
        token_with_whitespace = f"  {test_token}  "

        with patch.dict(os.environ, {
            'AZURE_DEVOPS_EXT_PAT': token_with_whitespace,
            'AZURE_DEVOPS_ORG': 'https://dev.azure.com/test',
            'AZURE_DEVOPS_PROJECT': 'Test'
        }):
            cli = AzureCLI()
            token = cli._load_pat_from_env()

            assert token == test_token
            assert token.strip() == token

    @patch('builtins.open', side_effect=IOError("File read error"))
    @patch('pathlib.Path.exists')
    def test_config_file_read_error_handled_gracefully(self, mock_exists, mock_file):
        """Test that config file read errors are handled gracefully."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        mock_exists.return_value = True

        with patch.dict(os.environ, {
            'AZURE_DEVOPS_ORG': 'https://dev.azure.com/test',
            'AZURE_DEVOPS_PROJECT': 'Test'
        }):
            cli = AzureCLI()
            token = cli._load_pat_from_config()

            # Should return None instead of crashing
            assert token is None

    @patch('builtins.open', new_callable=mock_open, read_data="{ invalid yaml !!")
    @patch('pathlib.Path.exists')
    def test_invalid_yaml_handled_gracefully(self, mock_exists, mock_file):
        """Test that invalid YAML is handled gracefully."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        mock_exists.return_value = True

        with patch.dict(os.environ, {
            'AZURE_DEVOPS_ORG': 'https://dev.azure.com/test',
            'AZURE_DEVOPS_PROJECT': 'Test'
        }):
            cli = AzureCLI()
            token = cli._load_pat_from_config()

            # Should return None instead of crashing
            assert token is None

    def test_token_exactly_20_chars_valid(self):
        """Test token with exactly 20 characters (minimum) is valid."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        with patch.dict(os.environ, {
            'AZURE_DEVOPS_ORG': 'https://dev.azure.com/test',
            'AZURE_DEVOPS_PROJECT': 'Test'
        }):
            cli = AzureCLI()
            token = "abcd1234efgh5678ijkl"  # Exactly 20 chars

            assert len(token) == 20
            assert cli._validate_pat_token(token) is True

    def test_token_19_chars_invalid(self):
        """Test token with 19 characters (below minimum) is invalid."""
        from skills.azure_devops.cli_wrapper import AzureCLI

        with patch.dict(os.environ, {
            'AZURE_DEVOPS_ORG': 'https://dev.azure.com/test',
            'AZURE_DEVOPS_PROJECT': 'Test'
        }):
            cli = AzureCLI()
            token = "abcd1234efgh5678ijk"  # 19 chars

            assert len(token) == 19
            assert cli._validate_pat_token(token) is False
