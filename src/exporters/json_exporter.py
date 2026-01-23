"""JSON exporter for YNAB budget data."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.ynab.models import Category, MonthDetail


class ExportError(Exception):
    """Raised when export fails."""


class JsonExporter:
    """Export YNAB budget data to JSON files."""

    def __init__(self, pretty: bool = True) -> None:
        self.pretty = pretty

    def export(self, month_data: MonthDetail, budget_name: str, output_path: str | Path) -> Path:
        """Export budget data to a JSON file.

        Args:
            month_data: Month detail data to export.
            budget_name: Name of the budget for metadata.
            output_path: File path to write.

        Returns:
            Path to the written file.

        Raises:
            ExportError: If writing fails.
        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        export_data = self._build_export_data(month_data, budget_name)

        try:
            with open(path, "w", encoding="utf-8") as file_handle:
                json.dump(
                    export_data,
                    file_handle,
                    indent=2 if self.pretty else None,
                    default=str,
                )
        except (OSError, ValueError, TypeError) as exc:
            raise ExportError(f"Failed to write export file: {path}") from exc

        return path

    def _build_export_data(self, month_data: MonthDetail, budget_name: str) -> dict[str, Any]:
        """Build the export payload."""
        return {
            "metadata": {
                "exported_at": datetime.now(timezone.utc).isoformat(),
                "source": "YNAB API",
                "budget_name": budget_name,
                "month": month_data.month.strftime("%Y-%m"),
            },
            "summary": self._build_summary(month_data.categories),
            "categories": self._build_categories(month_data.categories),
        }

    def _build_summary(self, categories: list[Category]) -> dict[str, float]:
        """Aggregate totals in human-readable units."""
        total_budgeted = sum(category.budgeted for category in categories)
        total_spent = sum(abs(category.activity) for category in categories)
        total_available = sum(category.balance for category in categories)

        return {
            "total_budgeted": Category.milliunit_to_unit(total_budgeted),
            "total_spent": Category.milliunit_to_unit(total_spent),
            "total_available": Category.milliunit_to_unit(total_available),
        }

    def _build_categories(self, categories: list[Category]) -> list[dict[str, Any]]:
        """Build category entries with group names and amounts."""
        output: list[dict[str, Any]] = []
        for category in categories:
            output.append(
                {
                    "group": category.category_group_name or "",
                    "name": category.name,
                    "budgeted": category.budgeted_amount,
                    "spent": category.spent_amount,
                    "available": category.balance_amount,
                }
            )
        return output
