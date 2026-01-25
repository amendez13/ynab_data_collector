"""Utility helpers for date parsing and validation."""

from __future__ import annotations

from datetime import date, datetime


class DateRangeError(ValueError):
    """Raised when a date range is invalid."""


def parse_date(value: str) -> date:
    """Parse a YYYY-MM-DD date string into a date."""
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise DateRangeError("Invalid date format. Use YYYY-MM-DD.") from exc


def validate_date_range(start_date: date, end_date: date, max_days: int = 365) -> None:
    """Validate a date range is ordered and within max_days."""
    if start_date > end_date:
        raise DateRangeError("Start date must be on or before end date.")
    if (end_date - start_date).days > max_days:
        raise DateRangeError("Date range must not exceed 365 days.")
