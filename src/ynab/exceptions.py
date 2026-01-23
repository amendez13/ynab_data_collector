"""Custom exceptions for YNAB API client errors."""


class YnabApiError(Exception):
    """Base YNAB API exception."""


class YnabAuthError(YnabApiError):
    """Authentication failed with the YNAB API."""


class YnabNotFoundError(YnabApiError):
    """Requested resource not found."""


class YnabRateLimitError(YnabApiError):
    """Rate limit exceeded for the YNAB API."""


class YnabNetworkError(YnabApiError):
    """Network error while communicating with the YNAB API."""


class YnabResponseError(YnabApiError):
    """Invalid response payload received from the YNAB API."""
