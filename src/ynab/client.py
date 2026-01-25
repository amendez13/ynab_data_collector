"""YNAB API client implementation."""

from __future__ import annotations

from typing import Any, cast

import requests

from src.ynab.exceptions import (
    YnabApiError,
    YnabAuthError,
    YnabNetworkError,
    YnabNotFoundError,
    YnabRateLimitError,
    YnabResponseError,
)
from src.ynab.models import AccountSummary, BudgetSummary, MonthDetail


class YnabClient:
    """YNAB API client."""

    def __init__(
        self,
        api_token: str,
        base_url: str = "https://api.ynab.com/v1",
        user_agent: str = "ynab-data-collector/0.1.0",
        timeout: float = 30.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {api_token}",
                "User-Agent": user_agent,
                "Accept": "application/json",
            }
        )

    def get_budgets(self) -> list[BudgetSummary]:
        """List available budgets for the user."""
        payload = self._get("/budgets")
        budgets = payload.get("data", {}).get("budgets", [])
        return [BudgetSummary(**budget) for budget in budgets]

    def get_accounts(self, budget_id: str = "last-used") -> list[AccountSummary]:
        """List accounts for a budget."""
        payload = self._get(f"/budgets/{budget_id}/accounts")
        accounts = payload.get("data", {}).get("accounts", [])
        return [AccountSummary(**account) for account in accounts]

    def get_current_month(self, budget_id: str = "last-used") -> MonthDetail:
        """Retrieve current month data for a budget."""
        payload = self._get(f"/budgets/{budget_id}/months/current")
        month = payload.get("data", {}).get("month")
        if month is None:
            raise YnabResponseError("Missing month data in YNAB response.")
        return MonthDetail(**month)

    def _get(self, endpoint: str) -> dict[str, Any]:
        """Make a GET request to the YNAB API with error handling."""
        url = f"{self.base_url}{endpoint}"
        try:
            response = self._session.get(url, timeout=self.timeout)
        except requests.RequestException as exc:
            raise YnabNetworkError("Network error while calling YNAB API.") from exc

        self._handle_response(response)

        try:
            return cast(dict[str, Any], response.json())
        except ValueError as exc:
            raise YnabResponseError("Invalid JSON response from YNAB API.") from exc

    def _handle_response(self, response: requests.Response) -> None:
        """Translate HTTP errors into custom exceptions."""
        status = response.status_code
        if status == 401:
            raise YnabAuthError("Invalid API token.")
        if status == 404:
            raise YnabNotFoundError("Requested resource was not found.")
        if status == 429:
            raise YnabRateLimitError("YNAB API rate limit exceeded.")
        if status >= 400:
            raise YnabApiError(f"YNAB API request failed with status {status}.")
