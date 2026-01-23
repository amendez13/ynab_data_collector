"""Configuration module for YNAB Data Collector.

This module provides configuration management using Pydantic models.
Configuration is loaded from YAML files, with sensitive values (API tokens)
loaded from environment variables for security.

Example usage:
    from src.config import load_config

    config = load_config()  # Uses default path: config/config.yaml
    print(config.ynab.base_url)

    # Or with custom path
    config = load_config("path/to/config.yaml")
"""

from pathlib import Path
from typing import Any, Optional, Union

import yaml
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class YnabSettings(BaseSettings):
    """YNAB API configuration settings.

    The API token is loaded from the YNAB_API_TOKEN environment variable
    for security. Other settings can be specified in the config file.
    """

    model_config = SettingsConfigDict(
        env_prefix="YNAB_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    api_token: str = Field(
        default=...,
        description="YNAB Personal Access Token (from YNAB_API_TOKEN env var)",
    )
    base_url: str = Field(
        default="https://api.ynab.com/v1",
        description="YNAB API base URL",
    )
    budget_id: str = Field(
        default="last-used",
        description="Budget ID to use, or 'last-used' for default budget",
    )


class Config(BaseModel):
    """Main application configuration.

    Combines YNAB settings with general application settings.
    """

    ynab: YnabSettings = Field(default_factory=YnabSettings)
    output_directory: Path = Field(
        default=Path("./output"),
        description="Directory for exported files",
    )

    @field_validator("output_directory", mode="before")
    @classmethod
    def parse_output_directory(cls, v: Union[str, Path]) -> Path:
        """Convert string paths to Path objects."""
        if isinstance(v, str):
            return Path(v)
        return v


class ConfigError(Exception):
    """Raised when configuration loading fails."""

    pass


def load_config(config_path: Optional[str | Path] = None) -> Config:
    """Load configuration from a YAML file.

    Loads configuration from the specified YAML file. YNAB API token
    is always loaded from the YNAB_API_TOKEN environment variable.

    Args:
        config_path: Path to the YAML config file. Defaults to 'config/config.yaml'.

    Returns:
        Config object with all settings loaded.

    Raises:
        ConfigError: If the config file cannot be read or parsed.
        ValidationError: If required settings are missing or invalid.
    """
    if config_path is None:
        config_path = Path("config/config.yaml")
    else:
        config_path = Path(config_path)

    # Load YAML config if file exists
    yaml_config: dict[str, Any] = {}
    if config_path.exists():
        try:
            with open(config_path, encoding="utf-8") as f:
                yaml_config = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise ConfigError(f"Failed to parse config file: {e}") from e
        except OSError as e:
            raise ConfigError(f"Failed to read config file: {e}") from e

    # Extract YNAB settings from YAML (excluding api_token which comes from env)
    ynab_yaml = yaml_config.get("ynab", {})
    ynab_settings_kwargs = {}
    if "base_url" in ynab_yaml:
        ynab_settings_kwargs["base_url"] = ynab_yaml["base_url"]
    if "budget_id" in ynab_yaml:
        ynab_settings_kwargs["budget_id"] = ynab_yaml["budget_id"]

    # Create YnabSettings (api_token loaded from environment)
    ynab_settings = YnabSettings(**ynab_settings_kwargs)

    # Build config kwargs
    config_kwargs: dict[str, Any] = {"ynab": ynab_settings}
    if "output_directory" in yaml_config:
        config_kwargs["output_directory"] = yaml_config["output_directory"]

    return Config(**config_kwargs)
