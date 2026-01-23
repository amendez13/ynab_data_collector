"""Tests for the YNAB API client."""

from datetime import date

import pytest
import requests
from requests_mock import Mocker

from src.ynab.client import YnabClient
from src.ynab.exceptions import (
    YnabApiError,
    YnabAuthError,
    YnabNetworkError,
    YnabNotFoundError,
    YnabRateLimitError,
    YnabResponseError,
)


def test_get_budgets_returns_models(requests_mock: Mocker) -> None:
    """Client should parse budgets into models."""
    url = "https://api.ynab.com/v1/budgets"
    requests_mock.get(
        url,
        json={
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

    client = YnabClient(api_token="test-token")
    budgets = client.get_budgets()

    assert len(budgets) == 1
    assert budgets[0].id == "budget-1"
    assert budgets[0].name == "Household"
    assert requests_mock.request_history[0].headers["Authorization"] == "Bearer test-token"
    assert requests_mock.request_history[0].headers["User-Agent"] == "ynab-data-collector/0.1.0"


def test_get_current_month_returns_model(requests_mock: Mocker) -> None:
    """Client should parse current month data into a model."""
    url = "https://api.ynab.com/v1/budgets/last-used/months/current"
    requests_mock.get(
        url,
        json={
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

    client = YnabClient(api_token="test-token")
    month = client.get_current_month()

    assert month.month == date(2024, 2, 1)
    assert month.income == 100000


def test_get_current_month_missing_payload_raises(requests_mock: Mocker) -> None:
    """Client should error when month data is missing."""
    url = "https://api.ynab.com/v1/budgets/last-used/months/current"
    requests_mock.get(url, json={"data": {}})

    client = YnabClient(api_token="test-token")

    with pytest.raises(YnabResponseError):
        client.get_current_month()


def test_auth_error_raises_custom_exception(requests_mock: Mocker) -> None:
    """401 responses should raise YnabAuthError."""
    url = "https://api.ynab.com/v1/budgets"
    requests_mock.get(url, status_code=401)

    client = YnabClient(api_token="bad-token")

    with pytest.raises(YnabAuthError):
        client.get_budgets()


def test_not_found_error_raises_custom_exception(requests_mock: Mocker) -> None:
    """404 responses should raise YnabNotFoundError."""
    url = "https://api.ynab.com/v1/budgets/bad/months/current"
    requests_mock.get(url, status_code=404)

    client = YnabClient(api_token="test-token")

    with pytest.raises(YnabNotFoundError):
        client.get_current_month("bad")


def test_rate_limit_error_raises_custom_exception(requests_mock: Mocker) -> None:
    """429 responses should raise YnabRateLimitError."""
    url = "https://api.ynab.com/v1/budgets"
    requests_mock.get(url, status_code=429)

    client = YnabClient(api_token="test-token")

    with pytest.raises(YnabRateLimitError):
        client.get_budgets()


def test_server_error_raises_generic_exception(requests_mock: Mocker) -> None:
    """Other HTTP errors should raise YnabApiError."""
    url = "https://api.ynab.com/v1/budgets"
    requests_mock.get(url, status_code=500)

    client = YnabClient(api_token="test-token")

    with pytest.raises(YnabApiError):
        client.get_budgets()


def test_network_error_raises_custom_exception(requests_mock: Mocker) -> None:
    """Network issues should raise YnabNetworkError."""
    url = "https://api.ynab.com/v1/budgets"
    requests_mock.get(url, exc=requests.exceptions.ConnectTimeout)

    client = YnabClient(api_token="test-token")

    with pytest.raises(YnabNetworkError):
        client.get_budgets()


def test_invalid_json_raises_custom_exception(requests_mock: Mocker) -> None:
    """Invalid JSON payloads should raise YnabResponseError."""
    url = "https://api.ynab.com/v1/budgets"
    requests_mock.get(url, text="not-json")

    client = YnabClient(api_token="test-token")

    with pytest.raises(YnabResponseError):
        client.get_budgets()
