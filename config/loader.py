"""
Configuration loader for Trustable AI Workbench.

Loads configuration from YAML files with environment variable support.
"""
import os
import re
from pathlib import Path
from typing import Dict, Any, Optional
import yaml

from .schema import FrameworkConfig


class ConfigLoader:
    """Configuration loader with environment variable expansion."""

    ENV_VAR_PATTERN = re.compile(r'\${([^}]+)}')

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize configuration loader.

        Args:
            config_path: Path to config.yaml (defaults to .claude/config.yaml)
        """
        if config_path is None:
            config_path = Path.cwd() / ".claude" / "config.yaml"

        self.config_path = Path(config_path)

    def _expand_env_vars(self, value: Any) -> Any:
        """
        Recursively expand environment variables in configuration values.

        Supports ${VAR_NAME} and ${VAR_NAME:-default} syntax.

        Args:
            value: Configuration value (can be str, dict, list, etc.)

        Returns:
            Value with environment variables expanded
        """
        if isinstance(value, str):
            def replace_var(match: re.Match) -> str:
                var_expr = match.group(1)

                # Check for default value syntax: VAR_NAME:-default
                if ":-" in var_expr:
                    var_name, default = var_expr.split(":-", 1)
                    return os.environ.get(var_name.strip(), default.strip())
                else:
                    return os.environ.get(var_expr.strip(), match.group(0))

            return self.ENV_VAR_PATTERN.sub(replace_var, value)

        elif isinstance(value, dict):
            return {k: self._expand_env_vars(v) for k, v in value.items()}

        elif isinstance(value, list):
            return [self._expand_env_vars(item) for item in value]

        else:
            return value

    def load_raw(self) -> Dict[str, Any]:
        """
        Load raw configuration from YAML file.

        Returns:
            Raw configuration dictionary

        Raises:
            FileNotFoundError: If config file doesn't exist
            yaml.YAMLError: If YAML is invalid
        """
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {self.config_path}\n"
                f"Run 'cwf init' to create a configuration file."
            )

        with open(self.config_path, "r") as f:
            raw_config = yaml.safe_load(f)

        # Expand environment variables
        return self._expand_env_vars(raw_config)

    def load(self) -> FrameworkConfig:
        """
        Load and validate configuration.

        Returns:
            Validated FrameworkConfig instance

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValidationError: If configuration is invalid
        """
        raw_config = self.load_raw()
        return FrameworkConfig(**raw_config)

    def save(self, config: FrameworkConfig) -> None:
        """
        Save configuration to YAML file.

        Args:
            config: FrameworkConfig instance to save
        """
        # Ensure directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dict and save
        config_dict = config.model_dump(exclude_none=True)

        with open(self.config_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(
                config_dict,
                f,
                default_flow_style=False,
                sort_keys=False,
                indent=2
            )

    def merge_with_defaults(self, user_config: Dict[str, Any], defaults: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge user configuration with defaults.

        Args:
            user_config: User-provided configuration
            defaults: Default configuration

        Returns:
            Merged configuration
        """
        merged = defaults.copy()

        for key, value in user_config.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                # Recursively merge nested dicts
                merged[key] = self.merge_with_defaults(value, merged[key])
            else:
                # Override with user value
                merged[key] = value

        return merged


def load_config(config_path: Optional[Path] = None) -> FrameworkConfig:
    """
    Load framework configuration.

    Args:
        config_path: Path to config.yaml (defaults to .claude/config.yaml)

    Returns:
        Validated FrameworkConfig instance

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValidationError: If configuration is invalid
    """
    loader = ConfigLoader(config_path)
    return loader.load()


def create_default_config(
    project_name: str,
    project_type: str,
    tech_stack: Dict[str, list[str]],
    work_tracking_platform: str = "azure-devops",
    organization: str = "",
    project: str = "",
) -> FrameworkConfig:
    """
    Create a default configuration.

    Args:
        project_name: Project name
        project_type: Project type
        tech_stack: Technology stack
        work_tracking_platform: Work tracking platform
        organization: Organization URL/name
        project: Project name in work tracking system

    Returns:
        Default FrameworkConfig instance
    """
    from .schema import (
        ProjectConfig,
        WorkTrackingConfig,
        QualityStandards,
        AgentConfig,
        WorkflowConfig,
        DeploymentConfig,
    )

    return FrameworkConfig(
        project=ProjectConfig(
            name=project_name,
            type=project_type,
            tech_stack=tech_stack,
        ),
        work_tracking=WorkTrackingConfig(
            platform=work_tracking_platform,
            organization=organization,
            project=project,
        ),
        quality_standards=QualityStandards(),
        agent_config=AgentConfig(),
        workflow_config=WorkflowConfig(),
        deployment_config=DeploymentConfig(),
    )


def save_config(config: FrameworkConfig, config_path: Optional[Path] = None) -> None:
    """
    Save framework configuration.

    Args:
        config: FrameworkConfig instance
        config_path: Path to save config.yaml (defaults to .claude/config.yaml)
    """
    loader = ConfigLoader(config_path)
    loader.save(config)
