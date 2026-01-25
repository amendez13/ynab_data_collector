"""Integration tests for transaction export workflow."""

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

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def runner() -> CliRunner:
    """Provide a Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def accounts_response() -> dict[str, Any]:
    """Load mock accounts API response."""
    with open(FIXTURES_DIR / "accounts_response.json") as f:
        return json.load(f)


@pytest.fixture
def transactions_response() -> dict[str, Any]:
    """Load mock transactions API response."""
    with open(FIXTURES_DIR / "transactions_response.json") as f:
        return json.load(f)


@pytest.fixture
def mock_env_token(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set up mock API token in environment."""
    monkeypatch.setenv("YNAB_API_TOKEN", "test-token-abc123")


@pytest.fixture
def mock_transactions_api(
    requests_mock: rm.Mocker,
    accounts_response: dict[str, Any],
    transactions_response: dict[str, Any],
) -> Generator[rm.Mocker, None, None]:
    """Set up mocked YNAB API responses for transactions."""
    requests_mock.get(
        "https://api.ynab.com/v1/budgets/last-used/accounts",
        json=accounts_response,
    )
    requests_mock.get(
        "https://api.ynab.com/v1/budgets/last-used/accounts/account-123/transactions",
        json=transactions_response,
    )
    yield requests_mock


class TestTransactionsWorkflow:
    """Integration tests for transactions export."""

    def test_export_transactions_csv(
        self,
        runner: CliRunner,
        mock_transactions_api: rm.Mocker,
        mock_env_token: None,
        tmp_path: Path,
    ) -> None:
        """Export transactions to CSV and verify contents."""
        output_file = tmp_path / "transactions.csv"

        result = runner.invoke(
            cli,
            [
                "transactions",
                "--account-id",
                "account-123",
                "--start-date",
                "2024-01-01",
                "--end-date",
                "2024-01-31",
                "--output",
                str(output_file),
            ],
        )

        assert result.exit_code == 0
        assert output_file.exists()
        contents = output_file.read_text(encoding="utf-8")
        assert "transaction_id" in contents.splitlines()[0]
        assert "tx-1" in contents
        assert "tx-2" not in contents

    def test_invalid_date_range(
        self,
        runner: CliRunner,
        mock_env_token: None,
    ) -> None:
        """Invalid date ranges should be rejected."""
        result = runner.invoke(
            cli,
            [
                "transactions",
                "--account-id",
                "account-123",
                "--start-date",
                "2024-02-01",
                "--end-date",
                "2024-01-01",
            ],
        )

        assert result.exit_code == 1
        assert "Start date must be on or before end date" in result.output

    def test_account_not_found(
        self,
        runner: CliRunner,
        requests_mock: rm.Mocker,
        accounts_response: dict[str, Any],
        mock_env_token: None,
    ) -> None:
        """Invalid account ID should fail before export."""
        requests_mock.get(
            "https://api.ynab.com/v1/budgets/last-used/accounts",
            json=accounts_response,
        )

        result = runner.invoke(
            cli,
            [
                "transactions",
                "--account-id",
                "missing",
                "--start-date",
                "2024-01-01",
                "--end-date",
                "2024-01-31",
            ],
        )

        assert result.exit_code == 1
        assert "Account not found" in result.output

    def test_api_error_handling(
        self,
        runner: CliRunner,
        requests_mock: rm.Mocker,
        accounts_response: dict[str, Any],
        mock_env_token: None,
    ) -> None:
        """API errors should surface with clear messaging."""
        requests_mock.get(
            "https://api.ynab.com/v1/budgets/last-used/accounts",
            json=accounts_response,
        )
        requests_mock.get(
            "https://api.ynab.com/v1/budgets/last-used/accounts/account-123/transactions",
            status_code=500,
            json={"error": {"id": "500", "name": "server_error"}},
        )

        result = runner.invoke(
            cli,
            [
                "transactions",
                "--account-id",
                "account-123",
                "--start-date",
                "2024-01-01",
                "--end-date",
                "2024-01-31",
            ],
        )

        assert result.exit_code == 1
        assert "YNAB API error" in result.output

    def test_missing_environment_variable(
        self,
        runner: CliRunner,
        requests_mock: rm.Mocker,
        accounts_response: dict[str, Any],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Missing API token should exit with error."""

        class NoEnvFileYnabSettings(YnabSettings):
            model_config = SettingsConfigDict(
                env_prefix="YNAB_",
                env_file=None,
                env_file_encoding="utf-8",
                extra="ignore",
            )

        monkeypatch.setattr("src.config.YnabSettings", NoEnvFileYnabSettings)
        monkeypatch.delenv("YNAB_API_TOKEN", raising=False)

        requests_mock.get(
            "https://api.ynab.com/v1/budgets/last-used/accounts",
            json=accounts_response,
        )

        result = runner.invoke(
            cli,
            [
                "transactions",
                "--account-id",
                "account-123",
                "--start-date",
                "2024-01-01",
                "--end-date",
                "2024-01-31",
            ],
        )

        assert result.exit_code == 1
