"""Tests for the YNAB API client."""

from datetime import date
from typing import Any

import pytest
import requests
from pytest_mock import MockerFixture

from src.ynab.client import YnabClient
from src.ynab.exceptions import (
    YnabApiError,
    YnabAuthError,
    YnabNetworkError,
    YnabNotFoundError,
    YnabRateLimitError,
    YnabResponseError,
)


class DummyResponse:
    """Minimal response stub for client tests."""

    def __init__(self, status_code: int, json_data: dict[str, Any] | None = None) -> None:
        self.status_code = status_code
        self._json_data = json_data

    def json(self) -> dict[str, Any]:
        if self._json_data is None:
            raise ValueError("Invalid JSON")
        return self._json_data


def test_get_budgets_returns_models(mocker: MockerFixture) -> None:
    """Client should parse budgets into models."""
    url = "https://api.ynab.com/v1/budgets"
    response = DummyResponse(
        200,
        {
            "data": {
                "budgets": [
                    {
                        "id": "budget-1",
                        "name": "Household",
                        "last_modified_on": "2024-02-10T12:00:00Z",
                        "currency_format": {"iso_code": "USD", "decimal_digits": 2},
                    }
                ]
            }
        },
    )
    get_mock = mocker.patch("requests.Session.get", return_value=response)

    client = YnabClient(api_token="test-token")
    budgets = client.get_budgets()

    assert len(budgets) == 1
    assert budgets[0].id == "budget-1"
    assert budgets[0].name == "Household"
    assert client._session.headers["Authorization"] == "Bearer test-token"
    assert client._session.headers["User-Agent"] == "ynab-data-collector/0.1.0"
    get_mock.assert_called_once_with(url, timeout=30.0, params=None)


def test_get_current_month_returns_model(mocker: MockerFixture) -> None:
    """Client should parse current month data into a model."""
    url = "https://api.ynab.com/v1/budgets/last-used/months/current"
    response = DummyResponse(
        200,
        {
            "data": {
                "month": {
                    "month": "2024-02-01",
                    "income": 100000,
                    "budgeted": 80000,
                    "activity": -20000,
                    "to_be_budgeted": 0,
                    "categories": [],
                }
            }
        },
    )
    get_mock = mocker.patch("requests.Session.get", return_value=response)

    client = YnabClient(api_token="test-token")
    month = client.get_current_month()

    assert month.month == date(2024, 2, 1)
    assert month.income == 100000
    get_mock.assert_called_once_with(url, timeout=30.0, params=None)


def test_get_accounts_returns_models(mocker: MockerFixture) -> None:
    """Client should parse accounts into models."""
    url = "https://api.ynab.com/v1/budgets/last-used/accounts"
    response = DummyResponse(
        200,
        {
            "data": {
                "accounts": [
                    {
                        "id": "acc-1",
                        "name": "Checking",
                        "type": "checking",
                        "on_budget": True,
                        "closed": False,
                    }
                ]
            }
        },
    )
    get_mock = mocker.patch("requests.Session.get", return_value=response)

    client = YnabClient(api_token="test-token")
    accounts = client.get_accounts()

    assert len(accounts) == 1
    assert accounts[0].id == "acc-1"
    assert accounts[0].account_type == "checking"
    get_mock.assert_called_once_with(url, timeout=30.0, params=None)


def test_get_transactions_returns_models(mocker: MockerFixture) -> None:
    """Client should parse transactions into models."""
    url = "https://api.ynab.com/v1/budgets/budget-123/accounts/account-456/transactions"
    response = DummyResponse(
        200,
        {
            "data": {
                "transactions": [
                    {
                        "id": "tx-1",
                        "date": "2024-02-01",
                        "amount": -12000,
                        "payee_name": "Coffee Shop",
                        "memo": "Latte",
                        "cleared": "cleared",
                        "approved": True,
                        "category_name": "Dining Out",
                        "account_id": "account-456",
                        "account_name": "Checking",
                    }
                ]
            }
        },
    )
    get_mock = mocker.patch("requests.Session.get", return_value=response)

    client = YnabClient(api_token="test-token")
    transactions = client.get_transactions("budget-123", "account-456", "2024-01-01")

    assert len(transactions) == 1
    assert transactions[0].id == "tx-1"
    assert transactions[0].amount == -12000
    get_mock.assert_called_once_with(url, timeout=30.0, params={"since_date": "2024-01-01"})


def test_get_current_month_missing_payload_raises(mocker: MockerFixture) -> None:
    """Client should error when month data is missing."""
    response = DummyResponse(200, {"data": {}})
    mocker.patch(
        "requests.Session.get",
        return_value=response,
    )

    client = YnabClient(api_token="test-token")

    with pytest.raises(YnabResponseError):
        client.get_current_month()


def test_auth_error_raises_custom_exception(mocker: MockerFixture) -> None:
    """401 responses should raise YnabAuthError."""
    response = DummyResponse(401, {"data": {}})
    mocker.patch("requests.Session.get", return_value=response)

    client = YnabClient(api_token="bad-token")

    with pytest.raises(YnabAuthError):
        client.get_budgets()


def test_not_found_error_raises_custom_exception(mocker: MockerFixture) -> None:
    """404 responses should raise YnabNotFoundError."""
    response = DummyResponse(404, {"data": {}})
    mocker.patch("requests.Session.get", return_value=response)

    client = YnabClient(api_token="test-token")

    with pytest.raises(YnabNotFoundError):
        client.get_current_month("bad")


def test_rate_limit_error_raises_custom_exception(mocker: MockerFixture) -> None:
    """429 responses should raise YnabRateLimitError."""
    response = DummyResponse(429, {"data": {}})
    mocker.patch("requests.Session.get", return_value=response)

    client = YnabClient(api_token="test-token")

    with pytest.raises(YnabRateLimitError):
        client.get_budgets()


def test_server_error_raises_generic_exception(mocker: MockerFixture) -> None:
    """Other HTTP errors should raise YnabApiError."""
    response = DummyResponse(500, {"data": {}})
    mocker.patch("requests.Session.get", return_value=response)

    client = YnabClient(api_token="test-token")

    with pytest.raises(YnabApiError):
        client.get_budgets()


def test_network_error_raises_custom_exception(mocker: MockerFixture) -> None:
    """Network issues should raise YnabNetworkError."""
    mocker.patch(
        "requests.Session.get",
        side_effect=requests.exceptions.ConnectTimeout,
    )

    client = YnabClient(api_token="test-token")

    with pytest.raises(YnabNetworkError):
        client.get_budgets()


def test_invalid_json_raises_custom_exception(mocker: MockerFixture) -> None:
    """Invalid JSON payloads should raise YnabResponseError."""
    response = DummyResponse(200, None)
    mocker.patch("requests.Session.get", return_value=response)

    client = YnabClient(api_token="test-token")

    with pytest.raises(YnabResponseError):
        client.get_budgets()
