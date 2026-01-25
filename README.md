# YNAB Data Collector

![CI](https://github.com/amendez13/ynab_data_collector/workflows/CI/badge.svg)
![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![Coverage](https://img.shields.io/badge/coverage-95%25-green.svg)

A CLI app that connects to YNAB and exports budget and transaction data to JSON/CSV.

## Features

- Export current month budget data to JSON
- Export account transactions to CSV for a date range (max 1 year)
- List available YNAB budgets and accounts
- Colored CLI output with verbose and quiet modes
- Configurable via YAML and environment variables

## Quick Start

1. Get a YNAB Personal Access Token:
   - Visit https://app.ynab.com/settings/developer

2. Clone the repo and install dependencies:

```bash
git clone https://github.com/amendez13/ynab_data_collector.git
cd ynab_data_collector
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
# venv\Scripts\activate   # On Windows
pip install -r requirements.txt
```

3. Configure the application:

```bash
cp config/config.example.yaml config/config.yaml
```

4. Set your YNAB API token:

```bash
export YNAB_API_TOKEN="your_token_here"
```

5. Export your current month budget:

```bash
python -m src.main export
# If installed as a script:
# ynab-collector export
```

The output file is written to `./output/<budget-name>-YYYY-MM-DD.json` by default.

## CLI Examples

If the package is installed, use `ynab-collector`. Otherwise, use `python -m src.main`.

```bash
# List budgets and IDs
ynab-collector budgets

# Export a specific budget
ynab-collector export --budget-id <budget-id>

# Export to a custom path
ynab-collector export --output ./my-budget.json

# List accounts and IDs
ynab-collector accounts

# Export transactions for an account (CSV)
ynab-collector transactions --account-id <account-id> --start-date 2024-01-01 --end-date 2024-01-31
```

For more examples, see `docs/USAGE.md`.

## Configuration

Configuration is stored in `config/config.yaml`. The YNAB API token is always loaded from the
`YNAB_API_TOKEN` environment variable.

```yaml
# config/config.yaml
ynab:
  base_url: "https://api.ynab.com/v1"
  budget_id: "last-used"  # or a specific budget ID

output_directory: "./output"
```

## Output Formats

Budget exports include metadata, summary totals, and categories.

```json
{
  "metadata": {
    "exported_at": "2024-01-15T12:00:00+00:00",
    "source": "YNAB API",
    "budget_name": "My Budget",
    "month": "2024-01"
  },
  "summary": {
    "total_budgeted": 2800.0,
    "total_spent": 2650.5,
    "total_available": 149.5
  },
  "categories": [
    {
      "group": "Monthly Bills",
      "name": "Rent",
      "budgeted": 1500.0,
      "spent": 1500.0,
      "available": 0.0
    }
  ]
}
```

Transaction exports are CSV with the following columns:

```
date,account_id,account_name,payee,memo,category,amount,cleared,approved,transaction_id
```

Default output path:
`./output/<account-name>-transactions-YYYY-MM-DD_to_YYYY-MM-DD.csv`

## Documentation

- `docs/INDEX.md` - Documentation index
- `docs/SETUP.md` - Setup and configuration
- `docs/USAGE.md` - CLI reference and examples
- `docs/ARCHITECTURE.md` - Architecture details

## Development

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run tests
pytest
```

## CI/CD

GitHub Actions runs:

1. Linting (Black, isort, flake8, mypy)
2. Tests (pytest across Python 3.10, 3.11, 3.12)
3. Coverage (95% minimum)
4. Security (bandit, pip-audit)

See `docs/CI.md` for details.
