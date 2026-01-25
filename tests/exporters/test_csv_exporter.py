"""Tests for CSV exporter."""

from pathlib import Path

from src.exporters.csv_exporter import CsvExporter
from src.ynab.models import TransactionDetail


def test_csv_exporter_writes_transactions(tmp_path: Path) -> None:
    """CSV exporter should write header and rows."""
    exporter = CsvExporter()
    output_file = tmp_path / "transactions.csv"
    transactions = [
        TransactionDetail(
            id="tx-1",
            date="2024-01-01",
            amount=-2500,
            payee_name="Coffee",
            memo="Latte",
            cleared="cleared",
            approved=True,
            category_name="Dining",
            account_id="acc-1",
            account_name="Checking",
        )
    ]

    output_path = exporter.export(transactions, output_file)

    assert output_path == output_file
    contents = output_file.read_text(encoding="utf-8").splitlines()
    assert contents[0].startswith("date,account_id,account_name")
    assert "tx-1" in contents[1]
    assert "-2.5" in contents[1]
