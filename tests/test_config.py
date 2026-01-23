"""Tests for the configuration module."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from src.config import Config, ConfigError, YnabSettings, load_config


class TestYnabSettings:
    """Tests for YnabSettings model."""

    def test_loads_api_token_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """API token should be loaded from YNAB_API_TOKEN env var."""
        monkeypatch.setenv("YNAB_API_TOKEN", "test-token-123")
        settings = YnabSettings()
        assert settings.api_token == "test-token-123"

    def test_default_base_url(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Base URL should default to YNAB API v1."""
        monkeypatch.setenv("YNAB_API_TOKEN", "test-token")
        settings = YnabSettings()
        assert settings.base_url == "https://api.ynab.com/v1"

    def test_default_budget_id(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Budget ID should default to 'last-used'."""
        monkeypatch.setenv("YNAB_API_TOKEN", "test-token")
        settings = YnabSettings()
        assert settings.budget_id == "last-used"

    def test_custom_base_url(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Base URL can be customized."""
        monkeypatch.setenv("YNAB_API_TOKEN", "test-token")
        settings = YnabSettings(base_url="https://custom.api.com")
        assert settings.base_url == "https://custom.api.com"

    def test_custom_budget_id(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Budget ID can be customized."""
        monkeypatch.setenv("YNAB_API_TOKEN", "test-token")
        settings = YnabSettings(budget_id="budget-123")
        assert settings.budget_id == "budget-123"

    def test_missing_api_token_raises_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Missing API token should raise ValidationError."""
        monkeypatch.delenv("YNAB_API_TOKEN", raising=False)
        with pytest.raises(ValidationError) as exc_info:
            YnabSettings()
        assert "api_token" in str(exc_info.value)


class TestConfig:
    """Tests for Config model."""

    def test_default_output_directory(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Output directory should default to './output'."""
        monkeypatch.setenv("YNAB_API_TOKEN", "test-token")
        config = Config()
        assert config.output_directory == Path("./output")

    def test_custom_output_directory_from_string(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Output directory can be set from string."""
        monkeypatch.setenv("YNAB_API_TOKEN", "test-token")
        config = Config(output_directory="/custom/path")
        assert config.output_directory == Path("/custom/path")

    def test_custom_output_directory_from_path(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Output directory can be set from Path object."""
        monkeypatch.setenv("YNAB_API_TOKEN", "test-token")
        config = Config(output_directory=Path("/another/path"))
        assert config.output_directory == Path("/another/path")

    def test_nested_ynab_settings(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Config should include nested YnabSettings."""
        monkeypatch.setenv("YNAB_API_TOKEN", "test-token")
        config = Config()
        assert isinstance(config.ynab, YnabSettings)
        assert config.ynab.api_token == "test-token"


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_config_from_yaml(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """Config should load from YAML file."""
        monkeypatch.setenv("YNAB_API_TOKEN", "test-token")
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            """
ynab:
  base_url: "https://custom.ynab.com/v1"
  budget_id: "my-budget-123"
output_directory: "/custom/output"
"""
        )

        config = load_config(config_file)

        assert config.ynab.base_url == "https://custom.ynab.com/v1"
        assert config.ynab.budget_id == "my-budget-123"
        assert config.output_directory == Path("/custom/output")

    def test_load_config_with_defaults(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """Config should use defaults for missing values."""
        monkeypatch.setenv("YNAB_API_TOKEN", "test-token")
        config_file = tmp_path / "config.yaml"
        config_file.write_text("# Empty config\n")

        config = load_config(config_file)

        assert config.ynab.base_url == "https://api.ynab.com/v1"
        assert config.ynab.budget_id == "last-used"
        assert config.output_directory == Path("./output")

    def test_load_config_nonexistent_file_uses_defaults(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """Non-existent config file should use defaults."""
        monkeypatch.setenv("YNAB_API_TOKEN", "test-token")
        config_file = tmp_path / "nonexistent.yaml"

        config = load_config(config_file)

        assert config.ynab.base_url == "https://api.ynab.com/v1"
        assert config.ynab.budget_id == "last-used"

    def test_load_config_invalid_yaml_raises_error(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """Invalid YAML should raise ConfigError."""
        monkeypatch.setenv("YNAB_API_TOKEN", "test-token")
        config_file = tmp_path / "invalid.yaml"
        config_file.write_text("invalid: yaml: content: [")

        with pytest.raises(ConfigError) as exc_info:
            load_config(config_file)
        assert "Failed to parse config file" in str(exc_info.value)

    def test_load_config_partial_ynab_settings(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """Config should handle partial YNAB settings."""
        monkeypatch.setenv("YNAB_API_TOKEN", "test-token")
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            """
ynab:
  budget_id: "partial-budget"
"""
        )

        config = load_config(config_file)

        assert config.ynab.budget_id == "partial-budget"
        assert config.ynab.base_url == "https://api.ynab.com/v1"  # default

    def test_load_config_default_path(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """load_config with no args should use default path."""
        monkeypatch.setenv("YNAB_API_TOKEN", "test-token")
        monkeypatch.chdir(tmp_path)

        # Create config directory and file
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        config_file = config_dir / "config.yaml"
        config_file.write_text(
            """
ynab:
  budget_id: "default-path-budget"
"""
        )

        config = load_config()

        assert config.ynab.budget_id == "default-path-budget"

    def test_load_config_string_path(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """load_config should accept string paths."""
        monkeypatch.setenv("YNAB_API_TOKEN", "test-token")
        config_file = tmp_path / "config.yaml"
        config_file.write_text("output_directory: /string/path/test\n")

        config = load_config(str(config_file))

        assert config.output_directory == Path("/string/path/test")

    def test_api_token_not_from_yaml(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """API token in YAML should be ignored (security)."""
        monkeypatch.setenv("YNAB_API_TOKEN", "env-token")
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            """
ynab:
  api_token: "yaml-token-should-be-ignored"
"""
        )

        config = load_config(config_file)

        # Token should come from env, not yaml
        assert config.ynab.api_token == "env-token"


class TestConfigError:
    """Tests for ConfigError exception."""

    def test_config_error_message(self) -> None:
        """ConfigError should preserve error message."""
        error = ConfigError("Test error message")
        assert str(error) == "Test error message"
