"""Tests for utility helpers."""

from datetime import date

import pytest

from src.utils import DateRangeError, parse_date, validate_date_range


def test_parse_date_valid() -> None:
    """parse_date should parse valid YYYY-MM-DD values."""
    parsed = parse_date("2024-01-15")

    assert parsed == date(2024, 1, 15)


def test_parse_date_invalid_format() -> None:
    """parse_date should raise for invalid date strings."""
    with pytest.raises(DateRangeError):
        parse_date("01-15-2024")


def test_validate_date_range_valid() -> None:
    """validate_date_range should accept ordered ranges within limit."""
    validate_date_range(date(2024, 1, 1), date(2024, 12, 31))


def test_validate_date_range_reversed() -> None:
    """validate_date_range should reject reversed ranges."""
    with pytest.raises(DateRangeError):
        validate_date_range(date(2024, 2, 1), date(2024, 1, 1))


def test_validate_date_range_too_long() -> None:
    """validate_date_range should reject ranges over 365 days."""
    with pytest.raises(DateRangeError):
        validate_date_range(date(2023, 1, 1), date(2024, 2, 1))
