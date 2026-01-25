"""CSV exporter for YNAB transaction data."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable

from src.ynab.models import TransactionDetail


class ExportError(Exception):
    """Raised when export fails."""


class CsvExporter:
    """Export YNAB transaction data to CSV files."""

    fieldnames = [
        "date",
        "account_id",
        "account_name",
        "payee",
        "memo",
        "category",
        "amount",
        "cleared",
        "approved",
        "transaction_id",
    ]

    def export(self, transactions: Iterable[TransactionDetail], output_path: str | Path) -> Path:
        """Export transactions to a CSV file.

        Args:
            transactions: Transactions to export.
            output_path: File path to write.

        Returns:
            Path to the written file.

        Raises:
            ExportError: If writing fails.
        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(path, "w", newline="", encoding="utf-8") as file_handle:
                writer = csv.DictWriter(file_handle, fieldnames=self.fieldnames)
                writer.writeheader()
                for transaction in transactions:
                    writer.writerow(
                        {
                            "date": transaction.date.isoformat(),
                            "account_id": transaction.account_id,
                            "account_name": transaction.account_name,
                            "payee": transaction.payee_name or "",
                            "memo": transaction.memo or "",
                            "category": transaction.category_name or "",
                            "amount": transaction.milliunit_to_unit(transaction.amount),
                            "cleared": transaction.cleared or "",
                            "approved": transaction.approved,
                            "transaction_id": transaction.id,
                        }
                    )
        except (OSError, ValueError, TypeError) as exc:
            raise ExportError(f"Failed to write CSV export file: {path}") from exc

        return path
