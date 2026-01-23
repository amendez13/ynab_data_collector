"""Tests for the CLI module."""

from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from src.config import Config, ConfigError, YnabSettings
from src.exporters.json_exporter import ExportError
from src.main import Context, __version__, cli
from src.ynab.exceptions import YnabApiError, YnabAuthError, YnabNotFoundError
from src.ynab.models import BudgetSummary, MonthDetail


@pytest.fixture
def runner() -> CliRunner:
    """Create a Click test runner."""
    return CliRunner()


@pytest.fixture
def mock_config() -> Config:
    """Create a mock configuration."""
    with patch.dict("os.environ", {"YNAB_API_TOKEN": "test-token"}):
        ynab_settings = YnabSettings()
    return Config(ynab=ynab_settings, output_directory=Path("./output"))


@pytest.fixture
def mock_budgets() -> list[BudgetSummary]:
    """Create mock budget summaries."""
    return [
        BudgetSummary(
            id="budget-123",
            name="My Budget",
            last_modified_on="2024-01-15T10:30:00Z",
        ),
        BudgetSummary(
            id="budget-456",
            name="Another Budget",
            last_modified_on="2024-01-10T08:00:00Z",
        ),
    ]


@pytest.fixture
def mock_month_detail() -> MonthDetail:
    """Create mock month detail."""
    return MonthDetail(
        month=date(2024, 1, 1),
        income=500000,
        budgeted=400000,
        activity=-300000,
        to_be_budgeted=100000,
        categories=[],
    )


class TestCli:
    """Tests for the main CLI group."""

    def test_cli_help(self, runner: CliRunner) -> None:
        """Test CLI displays help text."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "YNAB Data Collector" in result.output
        assert "export" in result.output
        assert "budgets" in result.output
        assert "version" in result.output

    def test_cli_version_option(self, runner: CliRunner) -> None:
        """Test CLI --version option."""
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert __version__ in result.output
        assert "ynab-collector" in result.output


class TestVersionCommand:
    """Tests for the version command."""

    def test_version_command(self, runner: CliRunner) -> None:
        """Test version command shows version info."""
        result = runner.invoke(cli, ["version"])
        assert result.exit_code == 0
        assert f"ynab-collector version {__version__}" in result.output


class TestBudgetsCommand:
    """Tests for the budgets command."""

    def test_budgets_success(self, runner: CliRunner, mock_config: Config, mock_budgets: list[BudgetSummary]) -> None:
        """Test budgets command lists budgets successfully."""
        with (
            patch("src.main.load_config", return_value=mock_config),
            patch("src.main.YnabClient") as mock_client_class,
        ):
            mock_client = MagicMock()
            mock_client.get_budgets.return_value = mock_budgets
            mock_client_class.return_value = mock_client

            result = runner.invoke(cli, ["budgets"])

            assert result.exit_code == 0
            assert "My Budget" in result.output
            assert "budget-123" in result.output
            assert "Another Budget" in result.output

    def test_budgets_no_budgets_found(self, runner: CliRunner, mock_config: Config) -> None:
        """Test budgets command when no budgets exist."""
        with (
            patch("src.main.load_config", return_value=mock_config),
            patch("src.main.YnabClient") as mock_client_class,
        ):
            mock_client = MagicMock()
            mock_client.get_budgets.return_value = []
            mock_client_class.return_value = mock_client

            result = runner.invoke(cli, ["budgets"])

            assert result.exit_code == 0
            assert "No budgets found" in result.output

    def test_budgets_auth_error(self, runner: CliRunner, mock_config: Config) -> None:
        """Test budgets command with authentication failure."""
        with (
            patch("src.main.load_config", return_value=mock_config),
            patch("src.main.YnabClient") as mock_client_class,
        ):
            mock_client = MagicMock()
            mock_client.get_budgets.side_effect = YnabAuthError("Invalid API token.")
            mock_client_class.return_value = mock_client

            result = runner.invoke(cli, ["budgets"])

            assert result.exit_code == 1
            assert "Authentication failed" in result.output

    def test_budgets_api_error(self, runner: CliRunner, mock_config: Config) -> None:
        """Test budgets command with API error."""
        with (
            patch("src.main.load_config", return_value=mock_config),
            patch("src.main.YnabClient") as mock_client_class,
        ):
            mock_client = MagicMock()
            mock_client.get_budgets.side_effect = YnabApiError("API error")
            mock_client_class.return_value = mock_client

            result = runner.invoke(cli, ["budgets"])

            assert result.exit_code == 1
            assert "YNAB API error" in result.output

    def test_budgets_config_error(self, runner: CliRunner) -> None:
        """Test budgets command with config error."""
        with patch("src.main.load_config", side_effect=ConfigError("Config not found")):
            result = runner.invoke(cli, ["budgets"])

            assert result.exit_code == 1
            assert "Configuration error" in result.output


class TestExportCommand:
    """Tests for the export command."""

    def test_export_success(
        self,
        runner: CliRunner,
        mock_config: Config,
        mock_budgets: list[BudgetSummary],
        mock_month_detail: MonthDetail,
        tmp_path: Path,
    ) -> None:
        """Test export command succeeds."""
        output_file = tmp_path / "budget.json"

        with (
            patch("src.main.load_config", return_value=mock_config),
            patch("src.main.YnabClient") as mock_client_class,
            patch("src.main.JsonExporter") as mock_exporter_class,
        ):
            mock_client = MagicMock()
            mock_client.get_budgets.return_value = mock_budgets
            mock_client.get_current_month.return_value = mock_month_detail
            mock_client_class.return_value = mock_client

            mock_exporter = MagicMock()
            mock_exporter.export.return_value = output_file
            mock_exporter_class.return_value = mock_exporter

            result = runner.invoke(cli, ["export", "-o", str(output_file)])

            assert result.exit_code == 0
            assert "exported to" in result.output

    def test_export_with_custom_budget_id(
        self,
        runner: CliRunner,
        mock_config: Config,
        mock_budgets: list[BudgetSummary],
        mock_month_detail: MonthDetail,
        tmp_path: Path,
    ) -> None:
        """Test export command with custom budget ID."""
        output_file = tmp_path / "budget.json"

        with (
            patch("src.main.load_config", return_value=mock_config),
            patch("src.main.YnabClient") as mock_client_class,
            patch("src.main.JsonExporter") as mock_exporter_class,
        ):
            mock_client = MagicMock()
            mock_client.get_budgets.return_value = mock_budgets
            mock_client.get_current_month.return_value = mock_month_detail
            mock_client_class.return_value = mock_client

            mock_exporter = MagicMock()
            mock_exporter.export.return_value = output_file
            mock_exporter_class.return_value = mock_exporter

            result = runner.invoke(cli, ["export", "-b", "budget-456", "-o", str(output_file)])

            assert result.exit_code == 0
            mock_client.get_current_month.assert_called_once_with("budget-456")

    def test_export_auth_error(self, runner: CliRunner, mock_config: Config) -> None:
        """Test export command with authentication failure."""
        with (
            patch("src.main.load_config", return_value=mock_config),
            patch("src.main.YnabClient") as mock_client_class,
        ):
            mock_client = MagicMock()
            mock_client.get_budgets.side_effect = YnabAuthError("Invalid API token.")
            mock_client_class.return_value = mock_client

            result = runner.invoke(cli, ["export"])

            assert result.exit_code == 1
            assert "Authentication failed" in result.output

    def test_export_budget_not_found(
        self,
        runner: CliRunner,
        mock_config: Config,
        mock_budgets: list[BudgetSummary],
    ) -> None:
        """Test export command with budget not found."""
        with (
            patch("src.main.load_config", return_value=mock_config),
            patch("src.main.YnabClient") as mock_client_class,
        ):
            mock_client = MagicMock()
            mock_client.get_budgets.return_value = mock_budgets
            mock_client.get_current_month.side_effect = YnabNotFoundError("Budget not found")
            mock_client_class.return_value = mock_client

            result = runner.invoke(cli, ["export", "-b", "invalid-budget"])

            assert result.exit_code == 1
            assert "Budget not found" in result.output

    def test_export_api_error(
        self,
        runner: CliRunner,
        mock_config: Config,
        mock_budgets: list[BudgetSummary],
    ) -> None:
        """Test export command with API error."""
        with (
            patch("src.main.load_config", return_value=mock_config),
            patch("src.main.YnabClient") as mock_client_class,
        ):
            mock_client = MagicMock()
            mock_client.get_budgets.return_value = mock_budgets
            mock_client.get_current_month.side_effect = YnabApiError("API error")
            mock_client_class.return_value = mock_client

            result = runner.invoke(cli, ["export"])

            assert result.exit_code == 1
            assert "YNAB API error" in result.output

    def test_export_config_error(self, runner: CliRunner) -> None:
        """Test export command with config error."""
        with patch("src.main.load_config", side_effect=ConfigError("Config not found")):
            result = runner.invoke(cli, ["export"])

            assert result.exit_code == 1
            assert "Configuration error" in result.output

    def test_export_write_error(
        self,
        runner: CliRunner,
        mock_config: Config,
        mock_budgets: list[BudgetSummary],
        mock_month_detail: MonthDetail,
        tmp_path: Path,
    ) -> None:
        """Test export command with export error."""
        output_file = tmp_path / "budget.json"

        with (
            patch("src.main.load_config", return_value=mock_config),
            patch("src.main.YnabClient") as mock_client_class,
            patch("src.main.JsonExporter") as mock_exporter_class,
        ):
            mock_client = MagicMock()
            mock_client.get_budgets.return_value = mock_budgets
            mock_client.get_current_month.return_value = mock_month_detail
            mock_client_class.return_value = mock_client

            mock_exporter = MagicMock()
            mock_exporter.export.side_effect = ExportError("Write failed")
            mock_exporter_class.return_value = mock_exporter

            result = runner.invoke(cli, ["export", "-o", str(output_file)])

            assert result.exit_code == 1
            assert "Export failed" in result.output

    def test_export_help(self, runner: CliRunner) -> None:
        """Test export command help text."""
        result = runner.invoke(cli, ["export", "--help"])
        assert result.exit_code == 0
        assert "--output" in result.output
        assert "--budget-id" in result.output
        assert "--format" in result.output


class TestVerboseQuietFlags:
    """Tests for verbose and quiet flags."""

    def test_verbose_flag(self, runner: CliRunner, mock_config: Config, mock_budgets: list[BudgetSummary]) -> None:
        """Test verbose flag shows additional output."""
        with (
            patch("src.main.load_config", return_value=mock_config),
            patch("src.main.YnabClient") as mock_client_class,
        ):
            mock_client = MagicMock()
            mock_client.get_budgets.return_value = mock_budgets
            mock_client_class.return_value = mock_client

            result = runner.invoke(cli, ["-v", "budgets"])

            assert result.exit_code == 0
            assert "Loaded configuration from" in result.output

    def test_quiet_flag(self, runner: CliRunner, mock_config: Config, mock_budgets: list[BudgetSummary]) -> None:
        """Test quiet flag suppresses non-error output."""
        with (
            patch("src.main.load_config", return_value=mock_config),
            patch("src.main.YnabClient") as mock_client_class,
        ):
            mock_client = MagicMock()
            mock_client.get_budgets.return_value = mock_budgets
            mock_client_class.return_value = mock_client

            result = runner.invoke(cli, ["-q", "budgets"])

            assert result.exit_code == 0
            # Quiet mode still shows budget list via click.echo
            assert "My Budget" in result.output

    def test_no_color_flag(self, runner: CliRunner, mock_config: Config, mock_budgets: list[BudgetSummary]) -> None:
        """Test no-color flag disables colored output."""
        with (
            patch("src.main.load_config", return_value=mock_config),
            patch("src.main.YnabClient") as mock_client_class,
        ):
            mock_client = MagicMock()
            mock_client.get_budgets.return_value = mock_budgets
            mock_client_class.return_value = mock_client

            result = runner.invoke(cli, ["--no-color", "budgets"])

            assert result.exit_code == 0
            assert "My Budget" in result.output


class TestContext:
    """Tests for the Context class."""

    def test_context_echo_quiet(self) -> None:
        """Test echo does nothing in quiet mode."""
        ctx = Context(
            config_path="config/config.yaml",
            verbose=False,
            quiet=True,
            no_color=False,
        )
        # Should not raise and should not print
        ctx.echo("Test message")
        ctx.echo_success("Success")
        ctx.echo_info("Info")

    def test_context_echo_verbose_disabled(self) -> None:
        """Test verbose echo does nothing when verbose is disabled."""
        ctx = Context(
            config_path="config/config.yaml",
            verbose=False,
            quiet=False,
            no_color=False,
        )
        # Should not print verbose messages
        ctx.echo_verbose("Verbose message")

    def test_context_lazy_load_config(self, mock_config: Config) -> None:
        """Test config is lazy-loaded."""
        with patch("src.main.load_config", return_value=mock_config) as mock_load:
            ctx = Context(
                config_path="config/config.yaml",
                verbose=False,
                quiet=False,
                no_color=False,
            )

            # Config not loaded yet
            mock_load.assert_not_called()

            # Access config
            _ = ctx.config
            mock_load.assert_called_once_with("config/config.yaml")

            # Second access doesn't reload
            _ = ctx.config
            mock_load.assert_called_once()

    def test_context_lazy_load_client(self, mock_config: Config) -> None:
        """Test client is lazy-loaded."""
        with (
            patch("src.main.load_config", return_value=mock_config),
            patch("src.main.YnabClient") as mock_client_class,
        ):
            ctx = Context(
                config_path="config/config.yaml",
                verbose=False,
                quiet=False,
                no_color=False,
            )

            # Client not loaded yet
            mock_client_class.assert_not_called()

            # Access client
            _ = ctx.client
            mock_client_class.assert_called_once()

            # Second access doesn't recreate
            _ = ctx.client
            mock_client_class.assert_called_once()


class TestConfigOption:
    """Tests for the config option."""

    def test_custom_config_path(self, runner: CliRunner, mock_config: Config, mock_budgets: list[BudgetSummary]) -> None:
        """Test using a custom config path."""
        with (
            patch("src.main.load_config", return_value=mock_config) as mock_load,
            patch("src.main.YnabClient") as mock_client_class,
        ):
            mock_client = MagicMock()
            mock_client.get_budgets.return_value = mock_budgets
            mock_client_class.return_value = mock_client

            result = runner.invoke(cli, ["-c", "custom/config.yaml", "budgets"])

            assert result.exit_code == 0
            mock_load.assert_called_once_with("custom/config.yaml")
