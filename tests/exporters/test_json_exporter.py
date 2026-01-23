"""Tests for JsonExporter."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.exporters.json_exporter import ExportError, JsonExporter
from src.ynab.models import Category, MonthDetail


def _sample_month(categories: list[Category]) -> MonthDetail:
    return MonthDetail(
        month="2024-01-01",
        income=200000,
        budgeted=150000,
        activity=-50000,
        to_be_budgeted=50000,
        categories=categories,
    )


def test_export_creates_output_file(tmp_path: Path) -> None:
    """Exporter should write JSON output."""
    exporter = JsonExporter(pretty=True)
    month = _sample_month(
        [
            Category(
                id="cat-1",
                category_group_id="group-1",
                category_group_name="Monthly Bills",
                name="Rent",
                budgeted=150000,
                activity=-150000,
                balance=0,
            )
        ]
    )
    output_path = tmp_path / "exports" / "budget.json"

    result = exporter.export(month, "My Budget", output_path)

    assert result.exists()
    payload = json.loads(result.read_text(encoding="utf-8"))
    assert payload["metadata"]["budget_name"] == "My Budget"
    assert payload["metadata"]["month"] == "2024-01"
    assert payload["summary"]["total_budgeted"] == 150.0
    assert payload["categories"][0]["group"] == "Monthly Bills"


def test_export_uses_compact_format(tmp_path: Path) -> None:
    """Compact format should omit indentation."""
    exporter = JsonExporter(pretty=False)
    month = _sample_month([])
    output_path = tmp_path / "budget.json"

    exporter.export(month, "My Budget", output_path)
    content = output_path.read_text(encoding="utf-8")

    assert "\n" not in content


def test_export_handles_empty_categories(tmp_path: Path) -> None:
    """Exporter should handle empty categories list."""
    exporter = JsonExporter()
    month = _sample_month([])
    output_path = tmp_path / "budget.json"

    exporter.export(month, "My Budget", output_path)
    payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert payload["categories"] == []
    assert payload["summary"]["total_budgeted"] == 0.0


def test_export_raises_on_write_error(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Exporter should raise ExportError on IO issues."""
    exporter = JsonExporter()
    month = _sample_month([])
    output_path = tmp_path / "budget.json"

    def _fail_open(*_args: object, **_kwargs: object) -> None:
        raise OSError("boom")

    monkeypatch.setattr("builtins.open", _fail_open)

    with pytest.raises(ExportError):
        exporter.export(month, "My Budget", output_path)
