"""Integration tests for the complete export workflow.

These tests verify the full workflow from CLI to JSON export using mocked YNAB API responses.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Generator

import pytest
import requests_mock as rm
from click.testing import CliRunner
from pydantic_settings import SettingsConfigDict

from src.config import YnabSettings
from src.main import cli

# Path to test fixtures
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def runner() -> CliRunner:
    """Provide a Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def budgets_response() -> dict[str, Any]:
    """Load mock budgets API response."""
    with open(FIXTURES_DIR / "budgets_response.json") as f:
        return json.load(f)


@pytest.fixture
def current_month_response() -> dict[str, Any]:
    """Load mock current month API response."""
    with open(FIXTURES_DIR / "current_month_response.json") as f:
        return json.load(f)


@pytest.fixture
def mock_ynab_api(
    requests_mock: rm.Mocker,
    budgets_response: dict[str, Any],
    current_month_response: dict[str, Any],
) -> Generator[rm.Mocker, None, None]:
    """Set up mocked YNAB API responses for happy path."""
    requests_mock.get(
        "https://api.ynab.com/v1/budgets",
        json=budgets_response,
    )
    requests_mock.get(
        "https://api.ynab.com/v1/budgets/last-used/months/current",
        json=current_month_response,
    )
    requests_mock.get(
        "https://api.ynab.com/v1/budgets/budget-123/months/current",
        json=current_month_response,
    )
    requests_mock.get(
        "https://api.ynab.com/v1/budgets/budget-456/months/current",
        json=current_month_response,
    )
    yield requests_mock


@pytest.fixture
def mock_env_token(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set up mock API token in environment."""
    monkeypatch.setenv("YNAB_API_TOKEN", "test-token-abc123")


class TestExportWorkflowHappyPath:
    """Tests for successful export workflows."""

    def test_export_default_budget_current_month(
        self,
        runner: CliRunner,
        mock_ynab_api: rm.Mocker,
        mock_env_token: None,
        tmp_path: Path,
    ) -> None:
        """Test exporting the default (last-used) budget for current month."""
        output_file = tmp_path / "budget.json"

        result = runner.invoke(cli, ["export", "-o", str(output_file)])

        assert result.exit_code == 0
        assert output_file.exists()
        assert "Budget exported to:" in result.output

        with open(output_file) as f:
            data = json.load(f)

        assert "metadata" in data
        assert "summary" in data
        assert "categories" in data
        assert data["metadata"]["budget_name"] == "My Budget"
        assert data["metadata"]["source"] == "YNAB API"
        assert len(data["categories"]) == 8

    def test_export_specific_budget_by_id(
        self,
        runner: CliRunner,
        mock_ynab_api: rm.Mocker,
        mock_env_token: None,
        tmp_path: Path,
    ) -> None:
        """Test exporting a specific budget by ID."""
        output_file = tmp_path / "budget.json"

        result = runner.invoke(cli, ["export", "-b", "budget-123", "-o", str(output_file)])

        assert result.exit_code == 0
        assert output_file.exists()

        with open(output_file) as f:
            data = json.load(f)

        assert data["metadata"]["budget_name"] == "My Budget"

    def test_export_to_custom_output_path(
        self,
        runner: CliRunner,
        mock_ynab_api: rm.Mocker,
        mock_env_token: None,
        tmp_path: Path,
    ) -> None:
        """Test exporting to a custom nested output path."""
        output_file = tmp_path / "nested" / "dir" / "my-export.json"

        result = runner.invoke(cli, ["export", "-o", str(output_file)])

        assert result.exit_code == 0
        assert output_file.exists()
        assert output_file.parent.name == "dir"

    def test_export_creates_output_directory(
        self,
        runner: CliRunner,
        mock_ynab_api: rm.Mocker,
        mock_env_token: None,
        tmp_path: Path,
    ) -> None:
        """Test that parent directories are created for output file."""
        output_file = tmp_path / "new" / "nested" / "output" / "budget.json"

        result = runner.invoke(cli, ["export", "-o", str(output_file)])

        assert result.exit_code == 0
        assert output_file.exists()
        assert output_file.parent.exists()

    def test_export_data_integrity(
        self,
        runner: CliRunner,
        mock_ynab_api: rm.Mocker,
        mock_env_token: None,
        tmp_path: Path,
    ) -> None:
        """Test that exported data maintains correct values."""
        output_file = tmp_path / "budget.json"

        result = runner.invoke(cli, ["export", "-o", str(output_file)])

        assert result.exit_code == 0

        with open(output_file) as f:
            data = json.load(f)

        summary = data["summary"]
        assert summary["total_budgeted"] == 2800.0
        assert summary["total_spent"] == 2650.5
        assert summary["total_available"] == 149.5

        rent_category = next(c for c in data["categories"] if c["name"] == "Rent")
        assert rent_category["group"] == "Monthly Bills"
        assert rent_category["budgeted"] == 1500.0
        assert rent_category["spent"] == 1500.0
        assert rent_category["available"] == 0.0


class TestBudgetsCommand:
    """Tests for the budgets list command."""

    def test_list_budgets_successfully(
        self,
        runner: CliRunner,
        mock_ynab_api: rm.Mocker,
        mock_env_token: None,
    ) -> None:
        """Test listing available budgets."""
        result = runner.invoke(cli, ["budgets"])

        assert result.exit_code == 0
        assert "My Budget" in result.output
        assert "budget-123" in result.output
        assert "Second Budget" in result.output
        assert "budget-456" in result.output
        assert "Found 2 budget(s)" in result.output

    def test_list_budgets_with_no_color(
        self,
        runner: CliRunner,
        mock_ynab_api: rm.Mocker,
        mock_env_token: None,
    ) -> None:
        """Test listing budgets with color disabled."""
        result = runner.invoke(cli, ["--no-color", "budgets"])

        assert result.exit_code == 0
        assert "My Budget" in result.output


class TestErrorScenarios:
    """Tests for error handling in the export workflow."""

    def test_invalid_api_token_401(
        self,
        runner: CliRunner,
        requests_mock: rm.Mocker,
        mock_env_token: None,
        tmp_path: Path,
    ) -> None:
        """Test handling of invalid API token (401 error)."""
        requests_mock.get(
            "https://api.ynab.com/v1/budgets",
            status_code=401,
            json={"error": {"id": "401", "name": "unauthorized"}},
        )
        output_file = tmp_path / "budget.json"

        result = runner.invoke(cli, ["export", "-o", str(output_file)])

        assert result.exit_code == 1
        assert "Authentication failed" in result.output
        assert not output_file.exists()

    def test_budget_not_found_404(
        self,
        runner: CliRunner,
        requests_mock: rm.Mocker,
        budgets_response: dict[str, Any],
        mock_env_token: None,
        tmp_path: Path,
    ) -> None:
        """Test handling of budget not found (404 error)."""
        requests_mock.get(
            "https://api.ynab.com/v1/budgets",
            json=budgets_response,
        )
        requests_mock.get(
            "https://api.ynab.com/v1/budgets/nonexistent-budget/months/current",
            status_code=404,
            json={"error": {"id": "404", "name": "not_found"}},
        )
        output_file = tmp_path / "budget.json"

        result = runner.invoke(cli, ["export", "-b", "nonexistent-budget", "-o", str(output_file)])

        assert result.exit_code == 1
        assert "Budget not found" in result.output
        assert not output_file.exists()

    def test_rate_limited_429(
        self,
        runner: CliRunner,
        requests_mock: rm.Mocker,
        mock_env_token: None,
        tmp_path: Path,
    ) -> None:
        """Test handling of rate limit exceeded (429 error)."""
        requests_mock.get(
            "https://api.ynab.com/v1/budgets",
            status_code=429,
            json={"error": {"id": "429", "name": "rate_limit_exceeded"}},
        )
        output_file = tmp_path / "budget.json"

        result = runner.invoke(cli, ["export", "-o", str(output_file)])

        assert result.exit_code == 1
        assert "YNAB API error" in result.output
        assert not output_file.exists()

    def test_network_error(
        self,
        runner: CliRunner,
        requests_mock: rm.Mocker,
        mock_env_token: None,
        tmp_path: Path,
    ) -> None:
        """Test handling of network errors."""
        import requests

        requests_mock.get(
            "https://api.ynab.com/v1/budgets",
            exc=requests.exceptions.ConnectionError("Network unreachable"),
        )
        output_file = tmp_path / "budget.json"

        result = runner.invoke(cli, ["export", "-o", str(output_file)])

        assert result.exit_code == 1
        assert "YNAB API error" in result.output
        assert not output_file.exists()

    def test_invalid_yaml_config_file(
        self,
        runner: CliRunner,
        mock_env_token: None,
        tmp_path: Path,
    ) -> None:
        """Test handling of invalid YAML configuration file."""
        config_file = tmp_path / "invalid.yaml"
        config_file.write_text("ynab:\n  budget_id: [invalid yaml structure")
        output_file = tmp_path / "budget.json"

        result = runner.invoke(cli, ["-c", str(config_file), "export", "-o", str(output_file)])

        assert result.exit_code == 1
        assert "Configuration error" in result.output

    def test_missing_environment_variable(
        self,
        runner: CliRunner,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """Test handling of missing YNAB_API_TOKEN environment variable."""

        class NoEnvFileYnabSettings(YnabSettings):
            model_config = SettingsConfigDict(
                env_prefix="YNAB_",
                env_file=None,
                env_file_encoding="utf-8",
                extra="ignore",
            )

        monkeypatch.setattr("src.config.YnabSettings", NoEnvFileYnabSettings)
        monkeypatch.delenv("YNAB_API_TOKEN", raising=False)
        output_file = tmp_path / "budget.json"

        result = runner.invoke(cli, ["export", "-o", str(output_file)])

        assert result.exit_code == 1
        assert not output_file.exists()


class TestEdgeCases:
    """Tests for edge cases in the export workflow."""

    def test_empty_budget_no_categories(
        self,
        runner: CliRunner,
        requests_mock: rm.Mocker,
        budgets_response: dict[str, Any],
        mock_env_token: None,
        tmp_path: Path,
    ) -> None:
        """Test handling of a budget with no categories."""
        empty_month_response = {
            "data": {
                "month": {
                    "month": "2024-01-01",
                    "income": 0,
                    "budgeted": 0,
                    "activity": 0,
                    "to_be_budgeted": 0,
                    "categories": [],
                }
            }
        }
        requests_mock.get(
            "https://api.ynab.com/v1/budgets",
            json=budgets_response,
        )
        requests_mock.get(
            "https://api.ynab.com/v1/budgets/last-used/months/current",
            json=empty_month_response,
        )
        output_file = tmp_path / "budget.json"

        result = runner.invoke(cli, ["export", "-o", str(output_file)])

        assert result.exit_code == 0
        assert output_file.exists()

        with open(output_file) as f:
            data = json.load(f)

        assert data["categories"] == []
        assert data["summary"]["total_budgeted"] == 0.0
        assert data["summary"]["total_spent"] == 0.0

    def test_budget_with_zero_activity(
        self,
        runner: CliRunner,
        requests_mock: rm.Mocker,
        budgets_response: dict[str, Any],
        mock_env_token: None,
        tmp_path: Path,
    ) -> None:
        """Test handling of a budget where all categories have zero activity."""
        zero_activity_response = {
            "data": {
                "month": {
                    "month": "2024-01-01",
                    "income": 5000000,
                    "budgeted": 2000000,
                    "activity": 0,
                    "to_be_budgeted": 3000000,
                    "categories": [
                        {
                            "id": "cat-1",
                            "category_group_id": "group-1",
                            "category_group_name": "Monthly Bills",
                            "name": "Rent",
                            "budgeted": 1500000,
                            "activity": 0,
                            "balance": 1500000,
                        },
                        {
                            "id": "cat-2",
                            "category_group_id": "group-1",
                            "category_group_name": "Monthly Bills",
                            "name": "Utilities",
                            "budgeted": 500000,
                            "activity": 0,
                            "balance": 500000,
                        },
                    ],
                }
            }
        }
        requests_mock.get(
            "https://api.ynab.com/v1/budgets",
            json=budgets_response,
        )
        requests_mock.get(
            "https://api.ynab.com/v1/budgets/last-used/months/current",
            json=zero_activity_response,
        )
        output_file = tmp_path / "budget.json"

        result = runner.invoke(cli, ["export", "-o", str(output_file)])

        assert result.exit_code == 0

        with open(output_file) as f:
            data = json.load(f)

        assert data["summary"]["total_spent"] == 0.0
        assert data["summary"]["total_budgeted"] == 2000.0
        assert data["summary"]["total_available"] == 2000.0

    def test_second_budget_selection(
        self,
        runner: CliRunner,
        mock_ynab_api: rm.Mocker,
        mock_env_token: None,
        tmp_path: Path,
    ) -> None:
        """Test selecting the second budget by ID."""
        output_file = tmp_path / "budget.json"

        result = runner.invoke(cli, ["export", "-b", "budget-456", "-o", str(output_file)])

        assert result.exit_code == 0
        assert output_file.exists()

        with open(output_file) as f:
            data = json.load(f)

        assert data["metadata"]["budget_name"] == "Second Budget"


class TestCLIOptions:
    """Tests for CLI option interactions."""

    def test_verbose_flag_shows_debug_info(
        self,
        runner: CliRunner,
        mock_ynab_api: rm.Mocker,
        mock_env_token: None,
        tmp_path: Path,
    ) -> None:
        """Test that verbose flag enables debug output."""
        output_file = tmp_path / "budget.json"

        result = runner.invoke(cli, ["-v", "export", "-o", str(output_file)])

        assert result.exit_code == 0
        assert "Fetching budgets from YNAB API" in result.output
        assert "Found" in result.output and "budget" in result.output

    def test_quiet_flag_suppresses_output(
        self,
        runner: CliRunner,
        mock_ynab_api: rm.Mocker,
        mock_env_token: None,
        tmp_path: Path,
    ) -> None:
        """Test that quiet flag suppresses non-error output."""
        output_file = tmp_path / "budget.json"

        result = runner.invoke(cli, ["-q", "export", "-o", str(output_file)])

        assert result.exit_code == 0
        assert result.output == ""
        assert output_file.exists()

    def test_no_color_flag_removes_ansi(
        self,
        runner: CliRunner,
        mock_ynab_api: rm.Mocker,
        mock_env_token: None,
        tmp_path: Path,
    ) -> None:
        """Test that no-color flag removes ANSI escape codes."""
        output_file = tmp_path / "budget.json"

        result = runner.invoke(cli, ["--no-color", "export", "-o", str(output_file)])

        assert result.exit_code == 0
        assert "\x1b[" not in result.output

    def test_custom_config_path(
        self,
        runner: CliRunner,
        requests_mock: rm.Mocker,
        budgets_response: dict[str, Any],
        current_month_response: dict[str, Any],
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """Test using a custom configuration file path."""
        monkeypatch.setenv("YNAB_API_TOKEN", "test-token-abc123")

        config_content = """
ynab:
  budget_id: budget-123
output_directory: ./custom-output
"""
        config_file = tmp_path / "custom-config.yaml"
        config_file.write_text(config_content)

        requests_mock.get(
            "https://api.ynab.com/v1/budgets",
            json=budgets_response,
        )
        requests_mock.get(
            "https://api.ynab.com/v1/budgets/budget-123/months/current",
            json=current_month_response,
        )

        output_file = tmp_path / "budget.json"
        result = runner.invoke(cli, ["-c", str(config_file), "export", "-o", str(output_file)])

        assert result.exit_code == 0
        assert output_file.exists()

    def test_version_command(
        self,
        runner: CliRunner,
    ) -> None:
        """Test the version command."""
        result = runner.invoke(cli, ["version"])

        assert result.exit_code == 0
        assert "ynab-collector version" in result.output


class TestAPIResponseHandling:
    """Tests for API response parsing and handling."""

    def test_handles_extra_api_fields(
        self,
        runner: CliRunner,
        requests_mock: rm.Mocker,
        mock_env_token: None,
        tmp_path: Path,
    ) -> None:
        """Test that extra fields in API response are ignored gracefully."""
        budgets_with_extra = {
            "data": {
                "budgets": [
                    {
                        "id": "budget-123",
                        "name": "My Budget",
                        "last_modified_on": "2024-01-15T10:00:00+00:00",
                        "currency_format": {"iso_code": "USD"},
                        "extra_field": "should be ignored",
                        "another_unknown": 12345,
                    }
                ],
                "server_knowledge": 12345,
            }
        }
        month_with_extra = {
            "data": {
                "month": {
                    "month": "2024-01-01",
                    "income": 5000000,
                    "budgeted": 4500000,
                    "activity": -3250500,
                    "to_be_budgeted": 500000,
                    "categories": [
                        {
                            "id": "cat-1",
                            "category_group_id": "group-1",
                            "category_group_name": "Monthly Bills",
                            "name": "Rent",
                            "budgeted": 1500000,
                            "activity": -1500000,
                            "balance": 0,
                            "hidden": False,
                            "deleted": False,
                        }
                    ],
                    "deleted": False,
                }
            }
        }
        requests_mock.get(
            "https://api.ynab.com/v1/budgets",
            json=budgets_with_extra,
        )
        requests_mock.get(
            "https://api.ynab.com/v1/budgets/last-used/months/current",
            json=month_with_extra,
        )
        output_file = tmp_path / "budget.json"

        result = runner.invoke(cli, ["export", "-o", str(output_file)])

        assert result.exit_code == 0
        assert output_file.exists()

    def test_handles_null_optional_fields(
        self,
        runner: CliRunner,
        requests_mock: rm.Mocker,
        mock_env_token: None,
        tmp_path: Path,
    ) -> None:
        """Test that null optional fields are handled correctly."""
        budgets_with_nulls = {
            "data": {
                "budgets": [
                    {
                        "id": "budget-123",
                        "name": "My Budget",
                        "last_modified_on": None,
                        "currency_format": None,
                    }
                ]
            }
        }
        month_with_nulls = {
            "data": {
                "month": {
                    "month": "2024-01-01",
                    "income": 1000000,
                    "budgeted": 500000,
                    "activity": -250000,
                    "to_be_budgeted": 500000,
                    "categories": [
                        {
                            "id": "cat-1",
                            "category_group_id": "group-1",
                            "category_group_name": None,
                            "name": "Uncategorized",
                            "budgeted": 500000,
                            "activity": -250000,
                            "balance": 250000,
                        }
                    ],
                }
            }
        }
        requests_mock.get(
            "https://api.ynab.com/v1/budgets",
            json=budgets_with_nulls,
        )
        requests_mock.get(
            "https://api.ynab.com/v1/budgets/last-used/months/current",
            json=month_with_nulls,
        )
        output_file = tmp_path / "budget.json"

        result = runner.invoke(cli, ["export", "-o", str(output_file)])

        assert result.exit_code == 0
        assert output_file.exists()

        with open(output_file) as f:
            data = json.load(f)

        category = data["categories"][0]
        assert category["group"] == ""


class TestEmptyBudgetsList:
    """Tests for handling when no budgets are available."""

    def test_list_budgets_empty(
        self,
        runner: CliRunner,
        requests_mock: rm.Mocker,
        mock_env_token: None,
    ) -> None:
        """Test listing budgets when account has no budgets."""
        requests_mock.get(
            "https://api.ynab.com/v1/budgets",
            json={"data": {"budgets": []}},
        )

        result = runner.invoke(cli, ["budgets"])

        assert result.exit_code == 0
        assert "No budgets found" in result.output
