# Usage Guide

This guide covers how to run YNAB Data Collector and how to use the current Python APIs.

## CLI Usage

After installation, the CLI is available as `ynab-collector` (if installed via pip) or `python -m src.main`.

### Installation

```bash
# Install in development mode
pip install -e .

# Or run directly
python -m src.main
```

### Commands

#### Export Budget Data

Export the current month's budget data to a JSON file:

```bash
# Export default budget to default location
ynab-collector export

# Export with custom output path
ynab-collector export --output ./my-budget.json

# Export specific budget
ynab-collector export --budget-id abc123-def456

# Combine options
ynab-collector export -b abc123 -o ./output/budget.json
```

#### List Available Budgets

View all budgets associated with your YNAB account:

```bash
ynab-collector budgets
```

#### Show Version

```bash
ynab-collector version
# or
ynab-collector --version
```

### Global Options

These options can be used with any command:

```bash
# Use custom config file
ynab-collector -c /path/to/config.yaml export

# Enable verbose output
ynab-collector -v export

# Suppress output (except errors)
ynab-collector -q export

# Disable colored output
ynab-collector --no-color budgets

# Show help
ynab-collector --help
ynab-collector export --help
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error (configuration, API, or export failure) |

## Configuration

The YNAB API token is loaded from the `YNAB_API_TOKEN` environment variable. Other settings live in `config/config.yaml`.

```bash
# macOS/Linux
export YNAB_API_TOKEN="your-token"

# Windows (PowerShell)
$env:YNAB_API_TOKEN="your-token"
```

```yaml
# config/config.yaml
ynab:
  base_url: "https://api.ynab.com/v1"
  budget_id: "last-used"

output_directory: "./output"
```

## Using the YNAB Client

```python
from src.config import load_config
from src.ynab import YnabClient

config = load_config()
client = YnabClient(
    api_token=config.ynab.api_token,
    base_url=config.ynab.base_url,
)

budgets = client.get_budgets()
current_month = client.get_current_month(config.ynab.budget_id)

print(budgets[0].name)
print(current_month.month)
```

## Using the JSON Exporter

```python
from src.config import load_config
from src.exporters import JsonExporter
from src.ynab import YnabClient

config = load_config()
client = YnabClient(
    api_token=config.ynab.api_token,
    base_url=config.ynab.base_url,
)

month_data = client.get_current_month()
budgets = client.get_budgets()
budget_name = budgets[0].name

exporter = JsonExporter(pretty=True)
output_path = exporter.export(month_data, budget_name, "output/budget.json")
print(f"Exported to: {output_path}")
```

## Error Handling

The client raises custom exceptions for common API failure cases.

```python
from src.ynab import (
    YnabAuthError,
    YnabNotFoundError,
    YnabRateLimitError,
    YnabNetworkError,
    YnabResponseError,
)

try:
    client.get_budgets()
except YnabAuthError:
    print("Invalid API token")
except YnabRateLimitError:
    print("Rate limit exceeded")
except YnabNotFoundError:
    print("Budget not found")
except YnabNetworkError:
    print("Network error")
except YnabResponseError:
    print("Invalid JSON payload")
```

## Next Steps

- Review `docs/ARCHITECTURE.md` for implementation details.
- See `docs/SETUP.md` if you need to configure your environment.
